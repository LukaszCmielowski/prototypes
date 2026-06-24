#!/usr/bin/env python3
"""Regenerate cleaned ai4rag experiment notebooks."""

from __future__ import annotations

import json
from pathlib import Path

NOTEBOOK_DIR = Path(__file__).parent


def md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source}


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": source,
    }


def notebook(cells: list[dict]) -> dict:
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
        "cells": cells,
    }


def build_cells(*, variant: str, branch: str, pr_url: str, expect_pr75: bool) -> list[dict]:
    title = "PR #75 (fix-prompts)" if variant == "pr75" else "Baseline (pre–PR #75)"
    run_label = "PR #75" if variant == "pr75" else "baseline"

    ensure = (
        "import importlib\n"
        "import sys\n"
        "from pathlib import Path\n"
        "\n"
        "import pandas as pd\n"
        "\n"
        "sys.path.insert(0, str(Path('.').resolve()))\n"
        "import experiment_utils as eu\n"
        "eu = importlib.reload(eu)\n"
        f'eu.ensure_notebook_context("{variant}")\n'
        "\n"
    )

    cells = [
        md(
            f"# AI4RAG William benchmark — {title}\n\n"
            "Compare prompt templates on the **same** GAM search space and William benchmark (22 questions).\n\n"
            "**Run order:** `ai4rag_baseline_experiment.ipynb` → `ai4rag_pr75_experiment.ipynb`.\n\n"
            "**Inspect without re-run:** set `RUN_EXPERIMENT = False` in section 2 and run from section 4 onward "
            "(loads `results/{variant}/runs/<latest>/`).\n\n"
            "**Prerequisites:** OGX `.env`, William data in `../lightrag/POC/challenge_data/`, ~10–20 min if running GAM.\n\n"
            f"**Branch:** `{branch}`"
        ),
        md("## 1. Install ai4rag\n\nSkip if inspecting a saved run only (`RUN_EXPERIMENT = False`)."),
        code(
            f"# Install ai4rag from: {branch}\n"
            f"!pip install --force-reinstall git+https://github.com/IBM/ai4rag.git@{branch} --quiet\n"
            f"!pip install python-dotenv openai pandas docling docling-core --quiet\n\n"
            f'print("Installed ai4rag @ {branch}")'
        ),
        md("## 2. Configuration"),
        code(
            "import importlib\n"
            "import json\n"
            "import sys\n"
            "from pathlib import Path\n"
            "\n"
            "import pandas as pd\n"
            "\n"
            "sys.path.insert(0, str(Path('.').resolve()))\n"
            "import experiment_utils as eu\n"
            "eu = importlib.reload(eu)\n"
            "\n"
            f'VARIANT = "{variant}"\n'
            f'BRANCH = "{branch}"\n'
            f'PR_URL = "{pr_url}"\n'
            f"EXPECT_PR75 = {expect_pr75}\n"
            "\n"
            "# --- execution controls ---\n"
            "RUN_EXPERIMENT = True   # False = load latest saved run (no GAM / no OGX experiment)\n"
            "RUN_ID = None           # e.g. '20260623_163137' or None for latest\n"
            "RUN_LLM_JUDGE = True    # 220 API calls; set False to skip or when reloading saved run\n"
            "\n"
            "eu.print_saved_run_index(VARIANT)\n"
            "\n"
            "if RUN_EXPERIMENT:\n"
            "    env_path = eu.load_dotenv_from_standard_paths()\n"
            "    print(f'Env: {env_path or \"environment variables\"}')\n"
            "    OGX_BASE_URL, OGX_API_KEY = eu.require_ogx_credentials()\n"
            "    print(f'OGX: {OGX_BASE_URL}')\n"
            "    try:\n"
            "        import ai4rag\n"
            "        print(f'ai4rag version: {getattr(ai4rag, \"__version__\", \"unknown\")}')\n"
            "    except ImportError as exc:\n"
            "        raise ImportError('Run the install cell first') from exc\n"
            "else:\n"
            "    print('RUN_EXPERIMENT=False — will load persisted results in section 4')"
        ),
        md("## 3. Load William benchmark\n\nSkipped when `RUN_EXPERIMENT = False`."),
        code(
            ensure
            + "if RUN_EXPERIMENT:\n"
            "    benchmark_data, documents = eu.load_william_benchmark()\n"
            "    benchmark_df = pd.DataFrame(benchmark_data)\n"
            "    print(f'Questions: {len(benchmark_data)}, documents: {len(documents)}')\n"
            "else:\n"
            "    benchmark_data, documents, benchmark_df = [], [], pd.DataFrame()\n"
            "    print('Skipped (loading saved run)')"
        ),
        md(
            "## 4. Run experiment or load saved run\n\n"
            "Fresh run: GAM explores retrieval/chunking from ai4rag defaults. "
            "Reload: reads `results/{variant}/runs/<run_id>/` (summary, leaderboard, answers, patterns, prompts)."
        ),
        code(
            ensure
            + "prompt_info = None\n"
            "\n"
            "if RUN_EXPERIMENT:\n"
            "    from ai4rag.rag.foundation_models.ogx import OgxClient\n"
            "\n"
            "    ogx_client = OgxClient(base_url=OGX_BASE_URL, api_key=OGX_API_KEY)\n"
            "    docling_documents = eu.documents_to_docling(documents)\n"
            "    print(f'Converted {len(docling_documents)} documents')\n"
            "\n"
            f'    experiment = eu.run_gam_experiment(\n'
            f"        docling_documents, benchmark_df, ogx_client, label='{run_label}',\n"
            f"    )\n"
            "    experiment_results, all_answers = eu.extract_experiment_results(experiment, benchmark_data)\n"
            "    eu.enrich_results_with_answer_quality(experiment_results, all_answers)\n"
            "    if experiment.results:\n"
            "        top = experiment.results.get_best_evaluations(k=1)[0]\n"
            "        prompt_info = eu.print_prompt_verification(top, expect_pr75=EXPECT_PR75)\n"
            "    print('Experiment complete')\n"
            "else:\n"
            "    bundle = eu.load_saved_run(VARIANT, run_id=RUN_ID)\n"
            "    experiment_results = bundle['experiment_results']\n"
            "    all_answers = bundle['all_answers']\n"
            "    leaderboard_df = bundle['leaderboard_df']\n"
            "    prompt_info = bundle.get('prompts')\n"
            "    run_dir = bundle['run_dir']\n"
            "    print(f'Loaded saved run: {run_dir}')\n"
            "    eu.print_run_inspection(bundle)"
        ),
        md("## 5. LLM-as-a-Judge\n\nSkipped if answers already include `llm_judge` from a saved run."),
        code(
            ensure
            + "has_judge = all_answers and all('llm_judge' in a for a in all_answers)\n"
            "\n"
            "if RUN_LLM_JUDGE and all_answers and not has_judge:\n"
            "    if not RUN_EXPERIMENT:\n"
            "        raise RuntimeError('LLM judge needs OGX — set RUN_EXPERIMENT=True or use a saved run that already has llm_judge')\n"
            "    judge_fn = eu.create_llm_judge_fn(OGX_BASE_URL, OGX_API_KEY)\n"
            "    eu.run_llm_judge_on_answers(all_answers, judge_fn)\n"
            "    eu.attach_llm_judge_averages(experiment_results, all_answers)\n"
            "    print('LLM-as-a-Judge complete')\n"
            "elif has_judge:\n"
            "    eu.attach_llm_judge_averages(experiment_results, all_answers)\n"
            "    print('Using llm_judge scores from saved run')\n"
            "else:\n"
            "    print('Skipped LLM-as-a-Judge')"
        ),
        md("## 6. Leaderboard"),
        code(
            ensure
            + "if experiment_results:\n"
            "    leaderboard_df = eu.build_leaderboard_df(experiment_results)\n"
            "elif 'leaderboard_df' not in globals() or leaderboard_df is None or getattr(leaderboard_df, 'empty', True):\n"
            "    raise RuntimeError('Run section 4 first (no experiment_results or leaderboard_df)')\n"
            "else:\n"
            "    leaderboard_df = eu.coerce_leaderboard_df(leaderboard_df)\n"
            "\n"
            "display_df = eu.format_leaderboard_for_display(leaderboard_df)\n"
            f'print("AI4RAG {run_label.upper()} LEADERBOARD")\n'
            "print('=' * 100)\n"
            "print(display_df.to_string(index=False))\n"
            "\n"
            "if not leaderboard_df.empty:\n"
            "    run_summary = eu.summarize_run(experiment_results, all_answers)\n"
            "    print('\\nRun summary:')\n"
            "    for k, v in run_summary.items():\n"
            "        print(f'  {k}: {v:.1%}')"
        ),
        md(
            "## 7. Save artifacts\n\n"
            "Writes a full run folder:\n"
            f"`results/{variant}/runs/<timestamp>/` with `summary.json`, `leaderboard.csv`, "
            "`answers.csv`, `patterns.json`, `prompts.json`.\n\n"
            "Skipped when reloading (`RUN_EXPERIMENT = False`)."
        ),
        code(
            ensure
            + "if RUN_EXPERIMENT and experiment_results:\n"
            "    run_dir = eu.save_experiment_artifacts(\n"
            "        VARIANT,\n"
            "        branch=BRANCH,\n"
            "        pr_url=PR_URL,\n"
            "        benchmark_data=benchmark_data,\n"
            "        experiment_results=experiment_results,\n"
            "        all_answers=all_answers,\n"
            "        leaderboard_df=leaderboard_df,\n"
            "        prompt_info=prompt_info if isinstance(prompt_info, dict) else None,\n"
            "    )\n"
            "    print(f'Saved run: {run_dir}')\n"
            "    print('Files: summary.json, leaderboard.csv, answers.csv, patterns.json, prompts.json')\n"
            "else:\n"
            "    print('Skipped save (no new experiment run)')"
        ),
        md(
            "## 8. Inspect saved runs (offline)\n\n"
            "Browse all runs or load a specific `RUN_ID` without re-running GAM."
        ),
        code(
            ensure
            + "eu.print_saved_run_index(VARIANT)\n"
            "\n"
            "# Uncomment to inspect a specific run:\n"
            "# inspect = eu.load_saved_run(VARIANT, run_id='20260623_163137')\n"
            "# eu.print_run_inspection(inspect)\n"
            "# inspect['answers_df'].head(10)"
        ),
    ]

    if variant == "pr75":
        cells.extend(
            [
                md("## 9. Compare with baseline"),
                code(
                    ensure
                    + "baseline_summary = eu.load_summary(eu.BASELINE_SUMMARY_LATEST)\n"
                    "pr75_summary = eu.load_summary(eu.PR75_SUMMARY_LATEST)\n"
                    "\n"
                    "if baseline_summary and pr75_summary:\n"
                    "    eu.print_baseline_comparison(pr75_summary, baseline_summary)\n"
                    "else:\n"
                    "    print('Run baseline notebook first (section 7) to enable comparison.')\n"
                    "    if not baseline_summary:\n"
                    "        print(f'  Missing: {eu.BASELINE_SUMMARY_LATEST}')"
                ),
            ]
        )

    return cells


def main() -> None:
    specs = [
        {
            "filename": "ai4rag_baseline_experiment.ipynb",
            "variant": "baseline",
            "branch": "move-autorag-components-code-to-ai4rag",
            "pr_url": "https://github.com/IBM/ai4rag/tree/move-autorag-components-code-to-ai4rag",
            "expect_pr75": False,
        },
        {
            "filename": "ai4rag_pr75_experiment.ipynb",
            "variant": "pr75",
            "branch": "fix-prompts",
            "pr_url": "https://github.com/IBM/ai4rag/pull/75",
            "expect_pr75": True,
        },
    ]

    for spec in specs:
        cells = build_cells(
            variant=spec["variant"],
            branch=spec["branch"],
            pr_url=spec["pr_url"],
            expect_pr75=spec["expect_pr75"],
        )
        path = NOTEBOOK_DIR / spec["filename"]
        path.write_text(json.dumps(notebook(cells), indent=1) + "\n", encoding="utf-8")
        print(f"Wrote {path} ({len(cells)} cells)")


if __name__ == "__main__":
    main()
