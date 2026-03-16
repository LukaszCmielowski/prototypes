# AutoGluon + LLM — Gen AI joint experience (UI/UX mocks)

Mocked UX/UI for a **single experience** that combines **predictive AI** (AutoGluon: classification, regression, time-series) and **generative AI** (LLMs). Includes a **configuration pane** and a **common leaderboard** where both types of AI are ranked together.

## What it showcases

- **Task types:** Classification, regression, time-series (tabs in config).
- **Predictive (AutoGluon):** Select experiment/run and model from leaderboard; include in run.
- **LLM:** Select endpoint and model (e.g. few-shot for same task); include in run.
- **Combined options:** Compare on same metric, LLM explains predictive, or ensemble/fallback — so predictive and LLM are combined in one workflow.
- **Common leaderboard:** One table with **Type** (Predictive | LLM | Combined), **Task**, **Model**, **Score**, **Notes**. Same eval set, same metric; rank AutoGluon and LLM together.

## Screens

| Screen         | File                         | Description |
|----------------|------------------------------|-------------|
| Overview       | [index.html](index.html)     | Intro and links to Configuration and Leaderboard. |
| Configuration  | [01_configuration.html](01_configuration.html) | Task type (classification / regression / time-series), AutoGluon + LLM side-by-side panes, combined experience mode, data & metric, Run. |
| Leaderboard    | [02_leaderboard.html](02_leaderboard.html) | Single table: Predictive and LLM (and Combined) rows, same score column; optional filters by type. |

## How to view

Open any HTML file in a browser (e.g. `index.html`). No build step. For design reference and screenshots only.

## Context

- **Predictive:** AutoGluon models for tabular classification, regression, time-series from AutoML experiments.
- **LLM:** Generative models (e.g. RHOAI) used on the same task (e.g. few-shot classification) so they can be compared fairly.
- **Combined:** One experience — configure both, run both, view both on the same leaderboard (and optional combined modes: explain, ensemble).

Part of Red Hat OpenShift AI / AutoML.

---

## Research & related work

Recent work aligns with this "joint experience" of classical ML and LLMs:

- **Hybrid predictive systems** — Combining LLMs with traditional ML for accuracy, explainability, and scalability; orchestration and self-correcting feedback between components. *e.g. DeepKnit AI whitepaper: "Hybrid Predictive Models: LLMs + Traditional ML".*
- **LLM for AutoML** — Using LLMs to guide model selection or search space (pre-hoc) from dataset descriptions and meta-features, reducing compute; or LLMs inside Bayesian optimization (LLAMBO, LLM-AutoOpt). *e.g. "Pre-Hoc Predictions in AutoML: Leveraging LLMs…" (tabular); NNGPT (LLM-based AutoML for vision).*
- **LLM explains ML** — Turning classical ML explanations (e.g. SHAP, feature importance) into natural-language narratives via an LLM, instead of the LLM explaining from scratch (limits hallucination). *e.g. Explingo / MIT work: SHAP → Narrator + Grader; FaithLM for faithfulness of explanations.*
- **Ensemble / weighting** — Combining LLM and classical ML scores with fixed weights, confidence-based weighting (use LLM more when ML confidence is low), or calibrated schemes. *e.g. DataComp-LM classifier (frozen LLM + classical ML, no fine-tuning).*

These suggest concrete enrichments (see below).

---

## Enrichment ideas (from research)

Ideas already reflected in the mocks or that could be added:

| Idea | Where it appears / could go |
|------|-----------------------------|
| **Ensemble weighting** | Config: "Ensemble with weighting" — fixed / confidence-based / calibrated. |
| **SHAP → LLM narrative** | Config: "LLM explains predictive" with SHAP option; leaderboard "Explain" column; explanation preview card. |
| **Latency & cost** | Leaderboard: optional Latency (ms) column; later Cost per 1k predictions. |
| **Explanation quality** | Leaderboard: "Explain" column for combined rows (e.g. Good / Fair); link to Grader or faithfulness metrics. |
| **Orchestration / self-correct** | Config: "LLM orchestrates predictive" — LLM delegates to ML, refines with feedback (future). |
| **Distribution-shift robustness** | Leaderboard or run options: eval on out-of-distribution holdout; report robustness. |

### Further research (2024–25)

Additional directions from recent work that could inform the joint experience:

- **Data-aware recommendation** — Suggest predictive vs LLM (or both) from dataset size, semantic column headers, and task. *e.g. LLM-Boost / PFN-Boost: LLMs help most on small/medium tabular data; GBDTs dominate on large; meaningful headers improve LLM value.*
- **Uncertainty / borderline** — LLM-enhanced classifiers show LLMs often more reliable on borderline cases. Surface uncertainty in leaderboard or combined view; optionally weight or route low-confidence rows toward LLM.
- **Natural language config** — LLM-driven AutoML improves success rates and cuts setup time (human-centered studies). Consider "Describe your task" → suggest task type, metric, predictive/LLM/both.
- **Risks & transparency** — AutoML+LLM survey notes synergies and risks (interpretability, cost, over-reliance). Design for cost visibility and clear guidance on when to prefer classical ML.
- **Synthetic tabular data** — Future: LLM-augmented or suggested synthetic data for training classical ML in low-data regimes (e.g. AutoSynth-style workflows, with quality safeguards).

### References (representative)

- DeepKnit AI: [Hybrid Predictive Models: LLMs + Traditional ML](https://www.deepknit.ai/whitepapers/hybrid-predictive-models-combining-llms-with-traditional-machine-learning/) (whitepaper).
- arXiv: Pre-Hoc Predictions in AutoML (LLMs for model selection on tabular); NNGPT (LLM-based AutoML); LLAMBO / LLM-AutoOpt (LLM in Bayesian optimization).
- Explingo / MIT: explaining AI predictions using LLMs (SHAP → narrative); FaithLM (faithful explanations).
- DataComp-LM: combining frozen LLM with classical ML via weighting/calibration.
- OpenReview: [LLMs Boost the Performance of Decision Trees on Tabular Data](https://openreview.net/forum?id=gp5tRHkz9B) (LLM-Boost / PFN-Boost; dataset-size and header-aware hybrid).
- OpenReview: [AutoML in the Age of Large Language Models](https://openreview.net/forum?id=cAthubStyG): current challenges, opportunities, and risks.
- Frontiers in AI / arXiv: Evaluation of LLM-driven AutoML in data and model management from human-centered perspective (success rates, implementation time, error resolution).
