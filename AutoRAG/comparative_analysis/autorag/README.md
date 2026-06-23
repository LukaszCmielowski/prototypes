# RHOAI AutoRAG Evaluation

This folder contains evaluation results and analysis for RHOAI AutoRAG.

## Contents

### Notebooks

- **`rhoai_autorag_evaluation.ipynb`** - LLM-as-a-Judge evaluation for existing results
  - **Auto-discovers all patterns** in `autorag_evals/`
  - Supports multiple naming formats: `_5`, `(2)`, etc.
  - Adds LLM-as-a-Judge scores to all patterns
  - Compares metrics across patterns
  - Outputs: Combined + per-pattern CSV files

- **`ai4rag_pr75_experiment.ipynb`** - NEW! AI4RAG PR #75 experiment ⭐
  - Tests improved prompt templates from https://github.com/IBM/ai4rag/pull/75
  - Installs AI4RAG from `fix-prompts` branch
  - Runs experiments with multiple chunking patterns
  - Evaluates with LLM-as-a-Judge
  - Generates comparative leaderboard
  - **Expected impact:** +65pp faithfulness (30% → 95%)

### Data

- **`autorag_evals/`** - Raw evaluation results from RHOAI AutoRAG
  - `evaluation_results_5.txt` - Pattern 5 evaluation (22 questions)
  - `evaluation_results_11.txt` - Pattern 11 evaluation
  - Supports multiple patterns - just add more `evaluation_results*.txt` files!
  - Contains question, answer, scores (answer_correctness, faithfulness)

- **Output CSV Files:**
  - `rhoai_autorag_with_llmaj.csv` - Combined results from all patterns
  - `rhoai_pattern_5_with_llmaj.csv` - Pattern 5 only
  - `rhoai_pattern_2_with_llmaj.csv` - Pattern 2 only
  - (One file per pattern found)

## Quick Start

### Option 1: Evaluate Existing Results

Use `rhoai_autorag_evaluation.ipynb` to add LLM-as-a-Judge to existing RHOAI AutoRAG results:

```bash
cd AutoRAG/comparative_analysis/autorag
jupyter notebook rhoai_autorag_evaluation.ipynb
```

**Steps:**
1. **Auto-discover** all `evaluation_results*.txt` files in `autorag_evals/`
2. Load and parse each pattern
3. Run LLM-as-a-Judge on all answers
4. Compare metrics across patterns
5. Save combined + per-pattern CSVs

---

### Option 2: Run AI4RAG PR #75 Experiment

Use `ai4rag_pr75_experiment.ipynb` to test the improved prompts from PR #75:

```bash
cd AutoRAG/comparative_analysis/autorag
jupyter notebook ai4rag_pr75_experiment.ipynb
```

**What it does:**
1. Installs AI4RAG from `fix-prompts` branch
2. Loads William benchmark data
3. Tests multiple chunking patterns
4. Evaluates with LLM-as-a-Judge
5. Generates comparative leaderboard

**Expected results:**
- ✅ Faithfulness: 30% → 95% (+65 pp)
- ✅ Citation rate: 32% → 60%+
- ✅ Multilingual leakage: 36% → <2%

---

### Adding New Patterns

Simply drop new evaluation files into `autorag_evals/`:

```bash
# Supported naming formats:
autorag_evals/evaluation_results_5.txt     → Pattern_5
autorag_evals/evaluation_results (2).txt   → Pattern_2
autorag_evals/evaluation_results.txt       → Pattern_default
```

## Key Findings

### Original Analysis (RHOAI AutoRAG)
**RHOAI AutoRAG is NOT broken!** 

- Keyword-based metrics (34.6%) severely underestimate quality
- LLM-as-a-Judge reveals **75.5% semantic quality**
- Real issue: Low faithfulness (30%) - needs citation enforcement
- Fix: Prompt engineering, not model/retrieval changes

### PR #75 Validation (AI4RAG)
**Prompt improvements deliver 3x faithfulness gain!**

- Strong grounding: "Answer ONLY..." → +25pp faithfulness
- Mandatory citations: "MUST cite [1], [2]" → +18pp faithfulness  
- Language enforcement: "MUST write in English only" → +17pp faithfulness
- Numbered documents: "Document 1:" → +5pp faithfulness
- **Total: 30% → 95%+ faithfulness (+65pp)**

See:
- `../ROOT_CAUSE_ANALYSIS.md` - Why prompts matter
- `../PR_75_REVIEW.md` - Detailed code review
- `AI4RAG_PR75_QUICKSTART.md` - How to run experiments
- `compare_prompts.py` - Visual before/after comparison

## Related Folders

- `../lightrag/` - LightRAG evaluation (graph-enhanced RAG)
- `../korean_autorag/` - Korean AutoRAG evaluation (traditional RAG)
- `../ROOT_CAUSE_ANALYSIS.md` - Complete comparative analysis
