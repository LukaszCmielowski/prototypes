# Korean AutoRAG - William Challenge Evaluation

Evaluation of **Korean AutoRAG** (Marker-Inc-Korea) on the William benchmark dataset.

## Overview

This folder contains a Jupyter notebook that evaluates Korean AutoRAG using the same William benchmark and metrics as the LightRAG evaluation, enabling direct comparison between the two frameworks.

**Korean AutoRAG** is an open-source framework for automatically optimizing RAG pipelines through AutoML-style automation.

## Contents

- `autorag_william_challenge.ipynb` - Main evaluation notebook
- `data/` - Generated parquet files (corpus and QA data)
- `autorag_leaderboard.csv` - Results leaderboard
- `autorag_evaluation_results.csv` - Detailed per-question results

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install AutoRAG rank-bm25 scikit-learn python-dotenv
   ```

2. **Configure OGX endpoint:**
   ```bash
   # Use the same .env file as LightRAG
   cp ../lightrag/POC/.env.example ../lightrag/POC/.env
   # Edit .env and set OGX_BASE_URL
   ```

3. **Run the notebook:**
   ```bash
   jupyter notebook korea_autorag_william_challenge.ipynb
   ```

## Evaluation Setup

### Data
- **Source**: William benchmark from `../lightrag/POC/challenge_data/`
  - `william.md` - 10 interconnected documents about Millbrook city
  - `william_benchmark.json` - 22 multi-hop reasoning questions

### Retrieval Methods Tested
1. **BM25** - Lexical/keyword-based retrieval
2. **Vector** - Semantic embedding-based retrieval (using OGX embeddings)
3. **Hybrid** - RRF (Reciprocal Rank Fusion) combination of BM25 + Vector

### Metrics (Same as LightRAG)
- **answer_correctness**: Keyword overlap (Jaccard similarity) between prediction and ground truth
- **faithfulness**: Content overlap between answer and retrieved documents

## Comparison: LightRAG vs Korean AutoRAG

| Feature | LightRAG | Korean AutoRAG |
|---------|----------|----------------|
| **Retrieval Modes** | naive, hybrid, mix | bm25, vector, hybrid |
| **Graph Integration** | Yes (local/global graph) | No (traditional retrieval) |
| **Optimization** | Manual configuration | AutoML-style auto-optimization |
| **Storage** | NetworkX, PostgreSQL AGE, Neo4j | Standard vector DB |
| **Best For** | Multi-hop reasoning, graph queries | AutoML pipeline optimization |

## Expected Results

The notebook generates a leaderboard table comparing the three retrieval methods:

```
Rank  Retrieval Mode  Answer Correctness  Faithfulness  Combined Score  Num Queries
----  --------------  ------------------  ------------  --------------  -----------
1     HYBRID          0.XXXX              0.XXXX        0.XXXX          22
2     VECTOR          0.XXXX              0.XXXX        0.XXXX          22
3     BM25            0.XXXX              0.XXXX        0.XXXX          22
```

## Resources

- **Tutorial**: https://marker-inc-korea.github.io/AutoRAG/tutorial.html
- **GitHub**: https://github.com/Marker-Inc-Korea/AutoRAG
- **Documentation**: https://marker-inc-korea.github.io/AutoRAG/

## Notes

- The notebook implements manual evaluation with the same metrics as LightRAG for direct comparison
- Full AutoRAG optimization pipeline (with AutoML) requires additional setup and can be expensive
- This implementation uses OGX for both LLM inference and embeddings (same as LightRAG)
