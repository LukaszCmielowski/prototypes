# AI4RAG comparative analysis (William benchmark)

Prompt A/B and evaluation for ai4rag baseline vs [PR #75](https://github.com/IBM/ai4rag/pull/75).

Analysis conclusions: [`../FINDINGS.md`](../FINDINGS.md)

## Quick start

```bash
cd AutoRAG/comparative_analysis/autorag
python3 compare_prompts.py                         # prompt diff only (optional)
jupyter notebook ai4rag_baseline_experiment.ipynb  # run first
jupyter notebook ai4rag_pr75_experiment.ipynb      # then compare (section 9)
```

Set `RUN_EXPERIMENT = False` in section 2 to reload the latest saved run without re-running GAM.

## Notebook sections (baseline + PR #75)

| # | Section |
|---|---------|
| 1 | Install ai4rag |
| 2 | Configuration (`RUN_EXPERIMENT`, `RUN_ID`, `RUN_LLM_JUDGE`) |
| 3 | Load William benchmark |
| 4 | Run GAM or load saved run |
| 5 | LLM-as-a-Judge |
| 6 | Leaderboard |
| 7 | Save artifacts |
| 8 | Inspect saved runs |
| 9 | Compare with baseline *(PR #75 only)* |

**Run order:** baseline → PR #75.

## Files

### Notebooks

| File | Purpose |
|------|---------|
| `ai4rag_baseline_experiment.ipynb` | GAM experiment, baseline branch (`move-autorag-components-code-to-ai4rag`) |
| `ai4rag_pr75_experiment.ipynb` | GAM experiment, PR #75 branch (`fix-prompts`) + baseline comparison |
| `rhoai_autorag_evaluation.ipynb` | Legacy: LLM-as-a-Judge on RHOAI `autorag_evals/` exports |

### Code

| File | Purpose |
|------|---------|
| `experiment_utils.py` | GAM config, extract/save/load runs, leaderboard, LLM judge |
| `build_experiment_notebooks.py` | Regenerate experiment notebooks |
| `compare_prompts.py` | Print PR #75 vs baseline prompt diff |

### Data

| Path | Purpose |
|------|---------|
| `autorag_evals/evaluation_results_*.txt` | RHOAI per-question eval JSON (legacy notebook) |
| `results/` | Persisted baseline / PR #75 runs (see `results/README.md`) |

## Results layout

```
results/{baseline|pr75}/
  latest_run.txt
  runs/<YYYYMMDD_HHMMSS>/
    summary.json, leaderboard.csv, answers.csv, patterns.json, prompts.json
  ai4rag_{variant}_summary_latest.json      # PR #75 section 9 comparison
  ai4rag_{variant}_leaderboard_latest.csv
```

## Latest measured impact (saved runs, June 2026)

| Metric | Baseline | PR #75 |
|--------|----------|--------|
| Best LLM judge | 78% | 84% |
| Mean LLM judge | 74% | 82% |
| Citation rate | 0% | 82% |
| Multilingual leakage | 56% | 8% |

GAM explores different retrieval configs each run; pattern labels are not comparable across runs unless `random_state` / fixed replay is wired in ai4rag.

## Navigation

| Goal | Go to |
|------|-------|
| Run prompt A/B | baseline notebook → PR #75 notebook |
| Reload saved run | `RUN_EXPERIMENT = False`, run from section 4 |
| See prompt changes | `python3 compare_prompts.py` |
| Legacy RHOAI LLMaJ | `rhoai_autorag_evaluation.ipynb` |
| Analysis / conclusions | `../FINDINGS.md` |

## Prerequisites

- OGX credentials: `../lightrag/POC/.env`
- William benchmark: `../lightrag/POC/challenge_data/william_benchmark.json`, `william.md`
- Packages: `ai4rag`, `python-dotenv`, `openai`, `pandas`, `docling`

## Related folders

- `../lightrag/POC/` — William data and LightRAG notebook
- `../korean_autorag/` — Korean AutoRAG William benchmark
