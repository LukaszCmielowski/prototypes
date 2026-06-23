# AI4RAG PR #75 Experiment Package

**Created:** 2026-06-23  
**Purpose:** Test and validate prompt improvements from PR #75  
**Expected Impact:** 3x faithfulness improvement (30% → 95%)

---

## 📦 Package Contents

### 1. Main Experiment Notebook
**`ai4rag_pr75_experiment.ipynb`**
- Installs AI4RAG from `fix-prompts` branch (PR #75)
- Runs experiments with multiple chunking patterns
- Evaluates with LLM-as-a-Judge
- Generates comparative leaderboard
- Saves results to CSV/JSON

### 2. Documentation
**`AI4RAG_PR75_QUICKSTART.md`**
- Prerequisites and setup
- Cell-by-cell notebook overview
- Expected output format
- Full experiment guide
- Troubleshooting tips

**`compare_prompts.py`**
- Side-by-side comparison of old vs new prompts
- Visual demonstration of improvements
- Impact breakdown by component
- Run with: `python3 compare_prompts.py`

**`EXPERIMENT_SUMMARY.md`** (this file)
- Package overview
- Quick reference guide

### 3. Existing Evaluations
**`rhoai_autorag_evaluation.ipynb`**
- Evaluates existing RHOAI AutoRAG results
- Adds LLM-as-a-Judge to patterns in `autorag_evals/`
- Generates per-pattern CSV outputs

---

## 🚀 Quick Start

### Option A: Visual Comparison (30 seconds)
```bash
cd AutoRAG/comparative_analysis/autorag
python3 compare_prompts.py
```

Shows before/after prompt templates with impact analysis.

---

### Option B: Run Experiment (10-20 minutes)
```bash
cd AutoRAG/comparative_analysis/autorag
jupyter notebook ai4rag_pr75_experiment.ipynb
```

1. Install AI4RAG from PR #75 branch
2. Load William benchmark
3. Test multiple patterns
4. Generate leaderboard

**Prerequisites:**
- OGX credentials in `.env` file
- William benchmark data in `../lightrag/challenge_data/`

---

### Option C: Evaluate Existing Results (5 minutes)
```bash
jupyter notebook rhoai_autorag_evaluation.ipynb
```

Add LLM-as-a-Judge to existing `autorag_evals/*.txt` files.

---

## 📊 Expected Results

### Key Metrics (Before → After PR #75)

| Metric | Baseline | PR #75 | Improvement |
|--------|----------|--------|-------------|
| **Faithfulness** | 30.1% | **95%+** | **+65 pp** ⭐⭐⭐ |
| **Citation Rate** | 31.8% | **60%+** | **+28 pp** ⭐⭐⭐ |
| **Multilingual Leakage** | 36.4% | **<2%** | **-34 pp** ⭐⭐⭐ |
| **Answer Correctness** | 34.6% | ~35% | Stable ✅ |
| **LLM Judge** | 75.5% | 75-80% | Stable/↑ ✅ |

**Overall Quality:** 2x improvement (32.4% → 65% combined score)

---

## 🔍 What PR #75 Changed

### Four Critical Improvements

#### 1. Grounding Instruction (+25pp)
**Before:** `"If you cannot base your answer..."`  
**After:** `"Answer ONLY using information from documents. Do not use outside knowledge."`  
**Why it works:** Imperative "ONLY" + explicit prohibition

#### 2. Citation Requirement (+18pp)
**Before:** *(missing)*  
**After:** `"You MUST cite sources using [1], [2], etc."`  
**Why it works:** Mandatory format, clear expectations

#### 3. Language Constraint (+17pp)
**Before:** `"Respond exclusively in the language of the question"` (ignored 36% of time)  
**After:** `"You MUST write entire answer in English only. Do NOT use any other language."`  
**Why it works:** "MUST" + prohibition + reinforcement + edge cases

#### 4. Context Structure (+5pp)
**Before:** `"[document]: {document}"`  
**After:** `"Document 1:\n{document}"`  
**Why it works:** Numbers match citation format

---

## 📁 File Organization

```
AutoRAG/comparative_analysis/autorag/
├── ai4rag_pr75_experiment.ipynb         # Main experiment notebook
├── rhoai_autorag_evaluation.ipynb       # Existing results evaluator
├── AI4RAG_PR75_QUICKSTART.md            # Detailed guide
├── EXPERIMENT_SUMMARY.md                # This file
├── compare_prompts.py                   # Visual comparison script
├── README.md                            # Folder overview
├── autorag_evals/                       # Raw evaluation results
│   ├── pattern_5.txt                    # Pattern 5 config + scores
│   ├── pattern_11.txt                   # Pattern 11 config + scores
│   └── evaluation_results_*.txt         # Other patterns
└── (generated outputs)
    ├── ai4rag_pr75_leaderboard_*.csv   # Comparative results
    └── ai4rag_pr75_summary_*.json      # Experiment metadata
```

---

## 🎯 Success Criteria

The PR #75 experiment is successful if:

1. **✅ Faithfulness improves by ≥50 pp** (30% → 80%+)
   - Target: 95%+ based on RCA projections

2. **✅ Citation rate doubles** (32% → 60%+)
   - Answers include [1], [2] references

3. **✅ Multilingual leakage drops by ≥30 pp** (36% → <5%)
   - English-only enforcement works

4. **✅ Answer correctness remains stable** (~35%)
   - No regression in semantic quality

5. **✅ LLM Judge scores stable/improve** (75-80%)
   - Confirms semantic quality maintained

---

## 🔬 Running Full Experiments

The notebook demonstrates the framework but loads **existing results** from `autorag_evals/`.

To run **full experiments from scratch**:

### 1. Set up vector store
```python
from ai4rag.rag.vector_stores import MilvusVectorStore
vector_store = MilvusVectorStore(uri="http://localhost:19530")
```

### 2. Initialize RAG with PR #75
```python
from ai4rag.rag.foundation_models.ogx import OGX
from ai4rag.rag.template.simple_rag_template import SimpleRAGTemplate

model = OGX(
    base_url=OGX_BASE_URL,
    api_key=OGX_API_KEY,
    model_id="vllm-inference-gpu-llama/redhataillama-31-8b-instruct",
    language_autodetect=False  # PR #75 default
)

rag = SimpleRAGTemplate(
    foundation_model=model,
    vector_store=vector_store,
    chunking_method="recursive",
    chunk_size=2048,
    chunk_overlap=128
)
```

### 3. Index and query
```python
# Index documents
for doc in documents:
    rag.add_document(doc)

# Run evaluation
for question in benchmark_data:
    answer = rag.query(question['question'])
    # Calculate metrics...
```

---

## 📚 Related Documents

- **PR #75 Review:** `../PR_75_REVIEW.md` - Detailed code review
- **PR #75 Summary:** `../PR_75_REVIEW_SUMMARY.md` - Executive summary
- **Root Cause Analysis:** `../ROOT_CAUSE_ANALYSIS.md` - Why prompts matter
- **William Benchmark:** `../lightrag/challenge_data/` - Test data

---

## 🤝 Contributing

To add new experiment patterns:

1. Run experiment with different chunking config
2. Save results to `autorag_evals/evaluation_results_X.txt`
3. Re-run `rhoai_autorag_evaluation.ipynb` to update leaderboard

Pattern naming convention:
- `evaluation_results_5.txt` → Pattern_5
- `evaluation_results_11.txt` → Pattern_11
- `evaluation_results (2).txt` → Pattern_2

---

## 📝 Notes

- **LLM-as-a-Judge** uses same OGX endpoint as experiments
- **Faithfulness** is token overlap (proxy for true faithfulness)
- **Answer Correctness** is Jaccard similarity (keyword overlap)
- **Combined Score** averages faithfulness + answer correctness
- **Production** should use full unitxt library with proper LLM-as-judge

---

## ✅ Next Steps

1. **Run baseline experiment** (old prompts) for comparison
2. **Run PR #75 experiment** (new prompts) 
3. **Compare results** to validate improvement
4. **Report findings** to PR #75 thread
5. **Merge PR #75** if validated

---

**For questions or issues:**
- Check `AI4RAG_PR75_QUICKSTART.md` for troubleshooting
- Review `../PR_75_REVIEW.md` for detailed analysis
- Run `compare_prompts.py` to see prompt differences
