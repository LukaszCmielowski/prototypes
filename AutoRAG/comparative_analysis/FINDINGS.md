# William benchmark — comparative findings

Single reference for conclusions from the `comparative_analysis` work. Operational how-to lives in `autorag/README.md`.

## Background

Three RAG stacks were compared on the William benchmark (22 questions, 10 documents):

| Track | Folder | Notes |
|-------|--------|-------|
| Korean AutoRAG (BM25) | `korean_autorag/` | High faithfulness (~93%); simple “answer from context” prompts |
| RHOAI AutoRAG (legacy) | `autorag/rhoai_autorag_evaluation.ipynb` | Low token-overlap faithfulness (~30%); LLM judge ~76% |
| IBM ai4rag (GAM) | `autorag/ai4rag_*_experiment.ipynb` | Prompt A/B baseline vs PR #75 |

**Main insight:** RHOAI’s low faithfulness was largely **weak prompt templates** (conditional grounding, no citations, ambiguous language rules), not a broken model. LLM-as-a-Judge scores were already ~75–80% while keyword faithfulness was ~30%.

## PR #75 prompt changes (ai4rag)

| Change | Baseline | PR #75 |
|--------|----------|--------|
| Grounding | “If you cannot base your answer…” | “Answer ONLY… Do not use outside knowledge.” |
| Citations | None | “MUST cite [1], [2]…” |
| Language | Match question language | English only, explicit prohibition |
| Documents | `[document]:` | `Document {n}:` |

Validated with paired notebooks (`experiment_utils.py`, shared GAM settings). Latest saved runs:

| Metric | Baseline | PR #75 | Delta |
|--------|----------|--------|-------|
| Best LLM judge | 78% | 84% | +6 pp |
| Mean LLM judge | 74% | 82% | +8 pp |
| Best faithfulness | 43% | 55% | +12 pp |
| Mean answer correctness | 29% | 62% | +33 pp |
| Citation rate | 0% | 82% | +82 pp |
| Multilingual leakage | 56% | 8% | −48 pp |

**Prompt-area closure:** PR #75 addresses foundational prompt hygiene. Further LLMaJ gains on multi-hop / transcript questions need retrieval or task-format prompt follow-up (optional), not more work on the four features above.

## Caveats

1. **GAM is non-deterministic** — `random_state` is unused in ai4rag; each run explores different retrieval configs. Pattern labels are not comparable across runs.
2. **Faithfulness metric** — Unitxt/token overlap understates semantic quality; trust LLM judge + manual answer review for prompt validation.
3. **Early projections** (+65 pp faithfulness, 95%+) were theoretical; measured best faithfulness on William is ~55% (PR #75).

## Where things live

| Need | Location |
|------|----------|
| Run experiments | `autorag/ai4rag_baseline_experiment.ipynb`, `ai4rag_pr75_experiment.ipynb` |
| Saved run data | `autorag/results/baseline/runs/` and `autorag/results/pr75/runs/` |
| Prompt before/after | `python3 autorag/compare_prompts.py` |
| Legacy RHOAI LLMaJ | `autorag/rhoai_autorag_evaluation.ipynb` |

**Last updated:** 2026-06-24
