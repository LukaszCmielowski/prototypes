"""
Shared helpers for ai4rag baseline vs PR #75 William benchmark experiments.

Used by:
  - ai4rag_baseline_experiment.ipynb
  - ai4rag_pr75_experiment.ipynb
"""

from __future__ import annotations

import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd

# --- experiment constants (keep identical across baseline / PR #75 runs) ---

FOUNDATION_MODEL = "vllm-inference-gpu-llama/redhataillama-31-8b-instruct"
EMBEDDING_MODEL = "vllm-embedding/bge-m3"
GAM_MAX_EVALS = 10
GAM_RANDOM_NODES = 4
OPTIMIZATION_METRIC = "faithfulness"
VECTOR_STORE_TYPE = "chroma"

RESULTS_DIR = Path(__file__).parent / "results"
BASELINE_SUMMARY_LATEST = RESULTS_DIR / "ai4rag_baseline_summary_latest.json"
PR75_SUMMARY_LATEST = RESULTS_DIR / "ai4rag_pr75_summary_latest.json"

NOTEBOOK_PROFILES: dict[str, dict[str, Any]] = {
    "baseline": {
        "VARIANT": "baseline",
        "BRANCH": "move-autorag-components-code-to-ai4rag",
        "PR_URL": "https://github.com/IBM/ai4rag/tree/move-autorag-components-code-to-ai4rag",
        "EXPECT_PR75": False,
    },
    "pr75": {
        "VARIANT": "pr75",
        "BRANCH": "fix-prompts",
        "PR_URL": "https://github.com/IBM/ai4rag/pull/75",
        "EXPECT_PR75": True,
    },
}


def ensure_notebook_context(variant: str, g: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Apply notebook defaults so cells can run out-of-order after a partial kernel session.

    Call at the top of any cell that depends on section 2 globals.
    """
    if variant not in NOTEBOOK_PROFILES:
        raise ValueError(f"Unknown variant {variant!r}; expected baseline or pr75")

    ctx = g if g is not None else globals()
    profile = NOTEBOOK_PROFILES[variant]

    ctx.setdefault("VARIANT", profile["VARIANT"])
    ctx.setdefault("BRANCH", profile["BRANCH"])
    ctx.setdefault("PR_URL", profile["PR_URL"])
    ctx.setdefault("EXPECT_PR75", profile["EXPECT_PR75"])
    ctx.setdefault("RUN_EXPERIMENT", True)
    ctx.setdefault("RUN_ID", None)
    ctx.setdefault("RUN_LLM_JUDGE", True)
    ctx.setdefault("experiment_results", [])
    ctx.setdefault("all_answers", [])
    ctx.setdefault("prompt_info", None)
    ctx.setdefault("benchmark_data", [])
    ctx.setdefault("documents", [])

    if not ctx.get("benchmark_data"):
        try:
            ctx["benchmark_data"], ctx["documents"] = load_william_benchmark()
        except OSError:
            pass

    lb = ctx.get("leaderboard_df")
    if ctx.get("experiment_results"):
        ctx["leaderboard_df"] = build_leaderboard_df(ctx["experiment_results"])
    elif lb is None or (hasattr(lb, "empty") and lb.empty):
        pass
    elif lb is not None:
        ctx["leaderboard_df"] = coerce_leaderboard_df(lb)

    return ctx


def variant_results_dir(variant: str) -> Path:
    return RESULTS_DIR / variant


def list_saved_runs(variant: str) -> list[str]:
    runs_dir = variant_results_dir(variant) / "runs"
    if not runs_dir.exists():
        return []
    return sorted((p.name for p in runs_dir.iterdir() if p.is_dir()), reverse=True)


def latest_run_id(variant: str) -> str | None:
    pointer = variant_results_dir(variant) / "latest_run.txt"
    if pointer.exists():
        run_id = pointer.read_text(encoding="utf-8").strip()
        if run_id and (variant_results_dir(variant) / "runs" / run_id).exists():
            return run_id
    runs = list_saved_runs(variant)
    return runs[0] if runs else None


def run_dir_for(variant: str, run_id: str) -> Path:
    return variant_results_dir(variant) / "runs" / run_id


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def serialize_experiment_results(experiment_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in experiment_results:
        settings = dict(result.get("settings") or {})
        rag_params = result.get("rag_params") or settings.pop("rag_params", None)
        rows.append(
            {
                "pattern_id": result["pattern_id"],
                "scores": result["scores"],
                "settings": settings,
                "final_score": result.get("final_score"),
                "num_answers": result.get("num_answers"),
                "rag_params": _json_safe(rag_params) if rag_params else {},
            }
        )
    return rows


def answers_to_dataframe(all_answers: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for row in all_answers:
        rows.append(
            {
                "pattern_id": row["pattern_id"],
                "question_idx": row["question_idx"],
                "question": row["question"],
                "answer": row["answer"],
                "ground_truth": " | ".join(row["ground_truth"]),
                "llm_judge": row.get("llm_judge"),
                "has_citations": bool(count_citations(row["answer"])),
                "is_multilingual": is_multilingual(row["answer"]),
            }
        )
    return pd.DataFrame(rows)


def extract_prompts_from_results(experiment_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not experiment_results:
        return {}
    best = max(
        experiment_results,
        key=lambda r: (
            r["scores"].get("faithfulness", 0.0),
            r["scores"].get("answer_correctness", 0.0),
        ),
    )
    rag_params = best.get("rag_params") or {}
    if not isinstance(rag_params, dict):
        rag_params = {}
    generation = rag_params.get("generation", {}) or {}
    return {
        "best_pattern_id": best["pattern_id"],
        "system_message_text": generation.get("system_message_text", ""),
        "user_message_text": generation.get("user_message_text", ""),
        "context_template_text": generation.get("context_template_text", ""),
        "pr75_features": check_pr75_features(
            generation.get("user_message_text", ""),
            generation.get("context_template_text", ""),
        ),
    }

PR75_FEATURE_CHECKS = {
    "strong_grounding": "Answer ONLY",
    "mandatory_citations": "You MUST cite",
    "english_enforcement": ("MUST write in English", "MUST write your entire answer in English"),
    "numbered_documents": ("Document {doc_number}", "Document 1:"),
}


def load_dotenv_from_standard_paths() -> Path | None:
    from dotenv import load_dotenv

    for env_path in (Path(".env"), Path("../lightrag/POC/.env"), Path("../.env")):
        if env_path.exists():
            load_dotenv(env_path)
            return env_path
    return None


def require_ogx_credentials() -> tuple[str, str]:
    import os

    base_url = os.getenv("OGX_BASE_URL")
    api_key = os.getenv("OGX_API_KEY")
    if not base_url or not api_key:
        raise ValueError(
            "Missing OGX_BASE_URL or OGX_API_KEY. "
            "Create .env (see ../lightrag/POC/.env.example)."
        )
    return base_url, api_key


def load_william_benchmark(
    benchmark_path: Path | None = None,
    documents_path: Path | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    benchmark_path = benchmark_path or Path("../lightrag/POC/challenge_data/william_benchmark.json")
    documents_path = documents_path or Path("../lightrag/POC/challenge_data/william.md")

    with open(benchmark_path, encoding="utf-8") as f:
        benchmark_data = json.load(f)

    documents_text = documents_path.read_text(encoding="utf-8")
    documents: list[str] = []
    current_doc: list[str] = []
    for line in documents_text.split("\n"):
        if line.startswith("---") and current_doc:
            documents.append("\n".join(current_doc))
            current_doc = []
        elif not line.startswith("---"):
            current_doc.append(line)
    if current_doc:
        documents.append("\n".join(current_doc))

    return benchmark_data, documents


def documents_to_docling(documents: list[str]) -> list[Any]:
    import tempfile

    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    docling_documents: list[Any] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        for i, doc_text in enumerate(documents, 1):
            path = tmp / f"william_doc_{i}.md"
            path.write_text(doc_text, encoding="utf-8")
            docling_documents.append(converter.convert(path).document)
    return docling_documents


def extract_metric_mean(scores: Any, metric_name: str) -> float:
    if not scores:
        return 0.0
    data = scores.get("scores", scores) if isinstance(scores, dict) else scores
    if not isinstance(data, dict) or metric_name not in data:
        return 0.0
    metric = data[metric_name]
    if isinstance(metric, dict) and "mean" in metric:
        return float(metric["mean"])
    if isinstance(metric, (int, float)):
        return float(metric)
    return 0.0


def flatten_rag_settings(rag_params: dict[str, Any] | None) -> dict[str, Any]:
    if not rag_params:
        return {}
    retrieval = rag_params.get("retrieval", {}) or {}
    generation = rag_params.get("generation", {}) or {}
    chunking = rag_params.get("chunking", {}) or {}
    return {
        "retrieval_method": retrieval.get("retrieval_method", "N/A"),
        "window_size": retrieval.get("window_size", "N/A"),
        "number_of_chunks": retrieval.get("number_of_chunks", "N/A"),
        "search_mode": retrieval.get("search_mode", "N/A"),
        "chunking_method": chunking.get("chunking_method", "N/A"),
        "chunk_size": chunking.get("chunk_size", "N/A"),
        "chunk_overlap": chunking.get("chunk_overlap", "N/A"),
        "model_id": generation.get("model_id", "N/A"),
        "rag_params": rag_params,
    }


def extract_experiment_results(
    experiment: Any,
    benchmark_data: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (experiment_results, all_answers)."""
    experiment_results: list[dict[str, Any]] = []
    all_answers: list[dict[str, Any]] = []

    if not getattr(experiment, "results", None):
        return experiment_results, all_answers

    all_evals = experiment.results.get_best_evaluations(k=None)
    evaluation_data_lists = getattr(experiment.results, "evaluation_data", []) or []

    for j, eval_result in enumerate(all_evals):
        faithfulness = extract_metric_mean(eval_result.scores, "faithfulness")
        answer_correctness = extract_metric_mean(eval_result.scores, "answer_correctness")
        settings = flatten_rag_settings(eval_result.rag_params)

        pattern_answers: list[str] = []
        if j < len(evaluation_data_lists):
            for idx, eval_data in enumerate(evaluation_data_lists[j]):
                if not (hasattr(eval_data, "answer") and hasattr(eval_data, "question")):
                    continue
                pattern_answers.append(eval_data.answer)
                if idx < len(benchmark_data):
                    all_answers.append(
                        {
                            "pattern_id": eval_result.pattern_name,
                            "question": eval_data.question,
                            "answer": eval_data.answer,
                            "ground_truth": benchmark_data[idx]["correct_answers"],
                            "question_idx": idx,
                        }
                    )

        experiment_results.append(
            {
                "pattern_id": eval_result.pattern_name,
                "scores": {
                    "faithfulness": faithfulness,
                    "answer_correctness": answer_correctness,
                },
                "settings": settings,
                "final_score": getattr(eval_result, "final_score", None),
                "num_answers": len(pattern_answers),
                "rag_params": eval_result.rag_params,
            }
        )

    return experiment_results, all_answers


def check_pr75_features(user_msg: str, context_template: str) -> dict[str, bool]:
    return {
        "strong_grounding": PR75_FEATURE_CHECKS["strong_grounding"] in user_msg,
        "mandatory_citations": PR75_FEATURE_CHECKS["mandatory_citations"] in user_msg,
        "english_enforcement": any(
            s in user_msg for s in PR75_FEATURE_CHECKS["english_enforcement"]
        ),
        "numbered_documents": any(
            s in context_template for s in PR75_FEATURE_CHECKS["numbered_documents"]
        ),
    }


def print_prompt_verification(eval_result: Any, *, expect_pr75: bool) -> dict[str, Any]:
    generation = (eval_result.rag_params or {}).get("generation", {}) or {}
    user_msg = generation.get("user_message_text", "")
    context_template = generation.get("context_template_text", "")
    system_msg = generation.get("system_message_text", "")

    features = check_pr75_features(user_msg, context_template)
    feature_count = sum(features.values())

    print("System message (first 200 chars):")
    print(system_msg[:200] + ("..." if len(system_msg) > 200 else ""))
    print("\nUser template (first 300 chars):")
    print(user_msg[:300] + ("..." if len(user_msg) > 300 else ""))
    print("\nContext template:")
    print(context_template)
    print("\nPR #75 feature checklist:")
    for name, present in features.items():
        print(f"  {'✅' if present else '❌'} {name.replace('_', ' ')}")

    if expect_pr75 and feature_count < 4:
        print(f"\n⚠️  Expected PR #75 prompts but only {feature_count}/4 features found.")
    elif not expect_pr75 and feature_count > 0:
        print(f"\n⚠️  Baseline run has {feature_count}/4 PR #75 features — wrong branch installed?")
    else:
        label = "PR #75" if expect_pr75 else "baseline"
        print(f"\n✅ Prompt verification OK for {label} ({feature_count}/4 PR features).")

    return {
        "best_pattern_id": eval_result.pattern_name,
        "system_message_text": system_msg,
        "user_message_text": user_msg,
        "context_template_text": context_template,
        "pr75_features": features,
        "pr75_feature_count": feature_count,
    }


def count_citations(answer: str) -> int:
    return len(re.findall(r"\[\d+\]", answer))


def is_multilingual(answer: str) -> bool:
    return bool(re.search(r"[^\x00-\x7F]", answer))


def compute_answer_quality_stats(all_answers: list[dict[str, Any]]) -> dict[str, Any]:
    if not all_answers:
        return {"citation_rate": 0.0, "multilingual_rate": 0.0, "total": 0}

    with_citations = sum(1 for a in all_answers if count_citations(a["answer"]))
    multilingual = sum(1 for a in all_answers if is_multilingual(a["answer"]))
    total = len(all_answers)
    return {
        "total": total,
        "citation_rate": with_citations / total,
        "multilingual_rate": multilingual / total,
        "answers_with_citations": with_citations,
        "multilingual_answers": multilingual,
    }


def enrich_results_with_answer_quality(
    experiment_results: list[dict[str, Any]],
    all_answers: list[dict[str, Any]],
) -> None:
    by_pattern: dict[str, list[dict[str, Any]]] = {}
    for row in all_answers:
        by_pattern.setdefault(row["pattern_id"], []).append(row)

    for result in experiment_results:
        rows = by_pattern.get(result["pattern_id"], [])
        if not rows:
            result["scores"]["citation_rate"] = 0.0
            result["scores"]["multilingual_rate"] = 0.0
            continue
        cited = sum(1 for r in rows if count_citations(r["answer"]))
        multi = sum(1 for r in rows if is_multilingual(r["answer"]))
        n = len(rows)
        result["scores"]["citation_rate"] = cited / n
        result["scores"]["multilingual_rate"] = multi / n


def create_llm_judge_fn(
    ogx_base_url: str,
    ogx_api_key: str,
    model_id: str = FOUNDATION_MODEL,
) -> Callable[[str, str, list[str]], float]:
    from openai import OpenAI

    client = OpenAI(base_url=f"{ogx_base_url.rstrip('/')}/v1", api_key=ogx_api_key)

    def llm_as_judge(question: str, predicted_answer: str, ground_truth_answers: list[str]) -> float:
        if not predicted_answer or predicted_answer.startswith("Error:"):
            return 0.2

        gt_text = " OR ".join(ground_truth_answers)
        judge_prompt = f"""You are an expert evaluator. Rate the quality of the predicted answer compared to the ground truth.

Question: {question}

Ground Truth Answer(s): {gt_text}

Predicted Answer: {predicted_answer}

Rate the predicted answer on a scale of 1-5:
- 5: Perfect answer, matches ground truth completely
- 4: Very good answer, captures main points with minor gaps
- 3: Adequate answer, partially correct but missing key information
- 2: Poor answer, mostly incorrect or incomplete
- 1: Wrong or irrelevant answer

Respond with ONLY a number from 1 to 5."""

        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": judge_prompt}],
                temperature=0.1,
                max_tokens=10,
            )
            score_text = response.choices[0].message.content.strip()
            match = re.search(r"[1-5]", score_text)
            return int(match.group()) / 5.0 if match else 0.5
        except Exception as exc:
            print(f"  ⚠️  LLM Judge error: {exc}")
            return 0.5

    return llm_as_judge


def run_llm_judge_on_answers(
    all_answers: list[dict[str, Any]],
    judge_fn: Callable[[str, str, list[str]], float],
    *,
    verbose: bool = True,
) -> None:
    for i, row in enumerate(all_answers, 1):
        if verbose:
            print(
                f"  [{i}/{len(all_answers)}] {row['pattern_id']} Q{row['question_idx']}: ",
                end="",
            )
        row["llm_judge"] = judge_fn(row["question"], row["answer"], row["ground_truth"])
        if verbose:
            print(f"{row['llm_judge']:.2f}")


def attach_llm_judge_averages(
    experiment_results: list[dict[str, Any]],
    all_answers: list[dict[str, Any]],
) -> None:
    by_pattern: dict[str, list[float]] = {}
    for row in all_answers:
        if "llm_judge" in row:
            by_pattern.setdefault(row["pattern_id"], []).append(row["llm_judge"])

    for result in experiment_results:
        scores = by_pattern.get(result["pattern_id"], [])
        result["scores"]["llm_judge"] = sum(scores) / len(scores) if scores else 0.0


PCT_COLUMNS = (
    "Faithfulness",
    "Answer Correctness",
    "LLM Judge",
    "Citation Rate",
    "Multilingual %",
    "Combined",
)


def _parse_fraction(value: Any) -> float | None:
    """Parse metric cell to a 0–1 float (handles CSV reloads and pre-formatted strings)."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip()
        if not s or s.upper() == "N/A":
            return None
        if s.endswith("%"):
            return float(s[:-1].strip()) / 100.0
        return float(s)
    return None


def coerce_leaderboard_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure percentage metric columns are numeric fractions."""
    if df.empty:
        return df
    out = df.copy()
    for col in PCT_COLUMNS:
        if col in out.columns:
            out[col] = out[col].apply(_parse_fraction)
    return out


def build_leaderboard_df(experiment_results: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for result in experiment_results:
        scores = result["scores"]
        settings = result["settings"]
        faith = scores.get("faithfulness", 0.0)
        ac = scores.get("answer_correctness", 0.0)
        llm = scores.get("llm_judge", 0.0)
        cite = scores.get("citation_rate", 0.0)
        multi = scores.get("multilingual_rate", 0.0)
        rows.append(
            {
                "Pattern": result["pattern_id"],
                "Retrieval": settings.get("retrieval_method", "N/A"),
                "Window": settings.get("window_size", "N/A"),
                "Chunks": settings.get("number_of_chunks", "N/A"),
                "Chunking": settings.get("chunking_method", "N/A"),
                "Chunk Size": settings.get("chunk_size", "N/A"),
                "Faithfulness": faith,
                "Answer Correctness": ac,
                "LLM Judge": llm,
                "Citation Rate": cite,
                "Multilingual %": multi,
                "Combined": (faith + ac) / 2,
                "Final Score": result.get("final_score"),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["Faithfulness", "Combined"], ascending=False).reset_index(drop=True)


def format_leaderboard_for_display(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    display = coerce_leaderboard_df(df)
    for col in PCT_COLUMNS:
        if col in display.columns:
            display[col] = display[col].map(
                lambda x: "N/A"
                if x is None or (isinstance(x, float) and pd.isna(x))
                else f"{x:.1%}"
            )
    return display


def summarize_run(experiment_results: list[dict[str, Any]], all_answers: list[dict[str, Any]]) -> dict[str, float]:
    faiths = [r["scores"]["faithfulness"] for r in experiment_results]
    acs = [r["scores"]["answer_correctness"] for r in experiment_results]
    quality = compute_answer_quality_stats(all_answers)
    summary: dict[str, float] = {
        "best_faithfulness": max(faiths) if faiths else 0.0,
        "mean_faithfulness": statistics.mean(faiths) if faiths else 0.0,
        "best_answer_correctness": max(acs) if acs else 0.0,
        "mean_answer_correctness": statistics.mean(acs) if acs else 0.0,
        "citation_rate": quality["citation_rate"],
        "multilingual_rate": quality["multilingual_rate"],
    }
    if any("llm_judge" in a for a in all_answers):
        llm_scores = [
            r["scores"]["llm_judge"]
            for r in experiment_results
            if "llm_judge" in r.get("scores", {})
        ]
        if llm_scores:
            summary["best_llm_judge"] = max(llm_scores)
            summary["mean_llm_judge"] = statistics.mean(llm_scores)
    return summary


def save_experiment_artifacts(
    variant: str,
    *,
    branch: str,
    pr_url: str,
    benchmark_data: list[dict[str, Any]],
    experiment_results: list[dict[str, Any]],
    all_answers: list[dict[str, Any]],
    leaderboard_df: pd.DataFrame,
    prompt_info: dict[str, Any] | None = None,
) -> Path:
    """Persist a full run under results/{variant}/runs/{run_id}/ for offline inspection."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    summary_stats = summarize_run(experiment_results, all_answers)
    best_row = leaderboard_df.iloc[0].to_dict() if not leaderboard_df.empty else {}

    prompts = prompt_info or extract_prompts_from_results(experiment_results)
    patterns = serialize_experiment_results(experiment_results)
    answers_df = answers_to_dataframe(all_answers)

    payload: dict[str, Any] = {
        "experiment_date": timestamp,
        "variant": variant,
        "branch": branch,
        "pr_url": pr_url,
        "benchmark": "william",
        "num_questions": len(benchmark_data),
        "num_patterns": len(experiment_results),
        "num_answers": len(all_answers),
        "gam_max_evals": GAM_MAX_EVALS,
        "gam_random_nodes": GAM_RANDOM_NODES,
        "foundation_model": FOUNDATION_MODEL,
        "embedding_model": EMBEDDING_MODEL,
        "summary": summary_stats,
        "best_pattern": best_row.get("Pattern"),
        "patterns_leaderboard": leaderboard_df.to_dict(orient="records"),
        "artifacts": {
            "summary": "summary.json",
            "leaderboard": "leaderboard.csv",
            "answers": "answers.csv",
            "patterns": "patterns.json",
            "prompts": "prompts.json",
        },
    }

    run_dir = run_dir_for(variant, timestamp)
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    leaderboard_df.to_csv(run_dir / "leaderboard.csv", index=False)
    answers_df.to_csv(run_dir / "answers.csv", index=False)
    (run_dir / "patterns.json").write_text(json.dumps(patterns, indent=2) + "\n", encoding="utf-8")
    (run_dir / "prompts.json").write_text(json.dumps(_json_safe(prompts), indent=2) + "\n", encoding="utf-8")

    # Pointer to latest run for this variant
    (variant_results_dir(variant) / "latest_run.txt").write_text(timestamp + "\n", encoding="utf-8")

    # Flat latest files (backward compatible with comparison helpers)
    latest_summary = BASELINE_SUMMARY_LATEST if variant == "baseline" else PR75_SUMMARY_LATEST
    latest_leaderboard = RESULTS_DIR / f"ai4rag_{variant}_leaderboard_latest.csv"
    latest_summary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    leaderboard_df.to_csv(latest_leaderboard, index=False)

    # Timestamped copies at results/ root (legacy paths)
    (RESULTS_DIR / f"ai4rag_{variant}_summary_{timestamp}.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    leaderboard_df.to_csv(RESULTS_DIR / f"ai4rag_{variant}_leaderboard_{timestamp}.csv", index=False)

    return run_dir


def load_saved_run(
    variant: str,
    *,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Load a persisted run bundle from results/{variant}/runs/{run_id}/."""
    run_id = run_id or latest_run_id(variant)
    if not run_id:
        raise FileNotFoundError(f"No saved runs for variant={variant!r} under {variant_results_dir(variant)}")

    run_dir = run_dir_for(variant, run_id)
    if not run_dir.exists():
        raise FileNotFoundError(f"Run not found: {run_dir}")

    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    leaderboard_df = coerce_leaderboard_df(pd.read_csv(run_dir / "leaderboard.csv"))
    answers_df = pd.read_csv(run_dir / "answers.csv")
    patterns = json.loads((run_dir / "patterns.json").read_text(encoding="utf-8"))
    prompts_path = run_dir / "prompts.json"
    prompts = json.loads(prompts_path.read_text(encoding="utf-8")) if prompts_path.exists() else {}

    experiment_results: list[dict[str, Any]] = []
    for row in patterns:
        settings = dict(row.get("settings") or {})
        rag_params = row.get("rag_params") or {}
        settings["rag_params"] = rag_params
        experiment_results.append(
            {
                "pattern_id": row["pattern_id"],
                "scores": row["scores"],
                "settings": settings,
                "final_score": row.get("final_score"),
                "num_answers": row.get("num_answers"),
                "rag_params": rag_params,
            }
        )

    all_answers: list[dict[str, Any]] = []
    for _, row in answers_df.iterrows():
        gt = row["ground_truth"]
        all_answers.append(
            {
                "pattern_id": row["pattern_id"],
                "question_idx": int(row["question_idx"]),
                "question": row["question"],
                "answer": row["answer"],
                "ground_truth": [s.strip() for s in str(gt).split(" | ") if s.strip()],
                **({"llm_judge": float(row["llm_judge"])} if pd.notna(row.get("llm_judge")) else {}),
            }
        )

    return {
        "run_id": run_id,
        "run_dir": run_dir,
        "summary": summary,
        "experiment_results": experiment_results,
        "all_answers": all_answers,
        "leaderboard_df": leaderboard_df,
        "answers_df": answers_df,
        "prompts": prompts,
    }


def print_saved_run_index(variant: str | None = None) -> None:
    variants = [variant] if variant else ["baseline", "pr75"]
    print("Saved experiment runs")
    print("=" * 60)
    for v in variants:
        runs = list_saved_runs(v)
        latest = latest_run_id(v)
        print(f"\n{v}/ ({len(runs)} runs, latest={latest})")
        for run_id in runs[:5]:
            marker = " ← latest" if run_id == latest else ""
            summary_path = run_dir_for(v, run_id) / "summary.json"
            if summary_path.exists():
                s = json.loads(summary_path.read_text(encoding="utf-8"))
                faith = s.get("summary", {}).get("best_faithfulness", 0)
                print(f"  {run_id}  best_faith={faith:.1%}{marker}")
            else:
                print(f"  {run_id}{marker}")
        if len(runs) > 5:
            print(f"  ... and {len(runs) - 5} more")


def print_run_inspection(bundle: dict[str, Any], *, sample_questions: int = 3) -> None:
    print(f"\nRun: {bundle['run_id']}  ({bundle['run_dir']})")
    print(f"Patterns: {len(bundle['experiment_results'])}, answers: {len(bundle['all_answers'])}")
    print("\nLeaderboard (top 5):")
    print(bundle["leaderboard_df"].head().to_string(index=False))

    prompts = bundle.get("prompts") or {}
    if prompts:
        print(f"\nBest pattern prompts: {prompts.get('best_pattern_id')}")
        features = prompts.get("pr75_features") or {}
        if features:
            print("PR #75 features:", ", ".join(f"{k}={'yes' if v else 'no'}" for k, v in features.items()))

    if bundle["all_answers"]:
        best_pattern = bundle["experiment_results"][0]["pattern_id"] if bundle["experiment_results"] else None
        if best_pattern:
            samples = [a for a in bundle["all_answers"] if a["pattern_id"] == best_pattern][:sample_questions]
            print(f"\nSample answers from {best_pattern}:")
            for i, row in enumerate(samples, 1):
                print(f"\n--- Q{i} ---")
                print(row["question"][:200])
                print(f"Answer: {row['answer'][:400]}...")


def load_summary(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def print_baseline_comparison(pr75_summary: dict[str, Any], baseline_summary: dict[str, Any]) -> None:
    b = baseline_summary["summary"]
    p = pr75_summary["summary"]

    def _fmt(value: float | None) -> str:
        return f"{value:>9.1%}" if value is not None else "      N/A"

    def _delta(bv: float | None, pv: float | None) -> str:
        if bv is None or pv is None:
            return "     N/A"
        return f"{(pv - bv) * 100:+6.1f} pp"

    metrics = [
        ("Best faithfulness", "best_faithfulness"),
        ("Mean faithfulness", "mean_faithfulness"),
        ("Best answer corr.", "best_answer_correctness"),
        ("Mean answer corr.", "mean_answer_correctness"),
        ("Best LLM judge", "best_llm_judge"),
        ("Mean LLM judge", "mean_llm_judge"),
        ("Citation rate", "citation_rate"),
        ("Multilingual rate", "multilingual_rate"),
    ]

    print("\n📈 PAIRED COMPARISON (baseline notebook vs PR #75 notebook)")
    print("-" * 80)
    print(f"{'Metric':<22} | {'Baseline':>10} | {'PR #75':>10} | {'Delta':>8}")
    print("-" * 80)
    for label, key in metrics:
        bv = b.get(key)
        pv = p.get(key)
        if key in ("best_llm_judge", "mean_llm_judge") and bv is None and pv is None:
            continue
        print(f"{label:<22} | {_fmt(bv)} | {_fmt(pv)} | {_delta(bv, pv)}")
    print("-" * 80)
    if "best_llm_judge" not in b or "best_llm_judge" not in p:
        print(
            "LLM-as-a-Judge: missing from one or both summaries — re-run section 5 "
            "and section 7 in each notebook to persist judge scores."
        )
    print(
        "\nNote: GAM explores different retrieval configs each run. "
        "For strict prompt-only A/B, fix rag_params and re-run both branches."
    )


def run_gam_experiment(
    docling_documents: list[Any],
    benchmark_df: pd.DataFrame,
    ogx_client: Any,
    *,
    label: str,
) -> Any:
    from ai4rag.core.experiment.experiment import AI4RAGExperiment
    from ai4rag.core.hpo.gam_opt import GAMOptSettings
    from ai4rag.search_space.prepare.prepare_search_space import prepare_search_space_with_ogx
    from ai4rag.utils.event_handler.base_event_handler import BaseEventHandler

    payload = {
        "foundation_models": [{"model_id": FOUNDATION_MODEL}],
        "embedding_models": [{"model_id": EMBEDDING_MODEL}],
    }
    search_space = prepare_search_space_with_ogx(
        payload=payload,
        client=ogx_client,
        vector_store_type=VECTOR_STORE_TYPE,
    )

    optimizer_settings = GAMOptSettings(
        max_evals=GAM_MAX_EVALS,
        n_random_nodes=GAM_RANDOM_NODES,
    )

    class SimpleEventHandler(BaseEventHandler):
        def on_status_change(self, level, message: str, step: str | None = None, **kwargs):
            if step:
                print(f"   [{level}] {step}: {message}")

        def on_pattern_creation(self, payload, evaluation_results: list, **kwargs):
            pattern_id = (
                payload.get("pattern_id", "unknown")
                if isinstance(payload, dict)
                else getattr(payload, "pattern_id", "unknown")
            )
            print(f"   🔧 Pattern {pattern_id} created")

    print(f"\n🚀 Running GAM experiment ({label})")
    print(f"   max_evals={GAM_MAX_EVALS}, n_random_nodes={GAM_RANDOM_NODES}")
    print(f"   metric={OPTIMIZATION_METRIC}, models={FOUNDATION_MODEL}")

    experiment = AI4RAGExperiment(
        documents=docling_documents,
        benchmark_data=benchmark_df,
        search_space=search_space,
        vector_store_type=VECTOR_STORE_TYPE,
        optimizer_settings=optimizer_settings,
        event_handler=SimpleEventHandler(),
        client=ogx_client,
        optimization_metric=OPTIMIZATION_METRIC,
    )
    experiment.search()
    return experiment
