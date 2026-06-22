# LightRAG William Challenge Evaluation

This directory contains a Jupyter notebook for evaluating LightRAG on the William benchmark - a complex multi-document dataset testing multi-hop reasoning, temporal relationships, and entity disambiguation.

## Quick Start

### 1. Setup Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and set your OGX credentials
# Required:
#   OGX_BASE_URL=https://your-ogx-endpoint.com
#   OGX_API_KEY=your_api_key_here
```

### 2. Install Dependencies

```bash
pip install lightrag-hku python-dotenv pandas numpy
```

### 3. Run the Notebook

```bash
jupyter lab lightrag_william_challenge.ipynb
```

## Files

```
.
├── README.md                          # This file
├── .env.example                       # Environment template
├── .env                               # Your credentials (gitignored)
├── lightrag_william_challenge.ipynb   # Main evaluation notebook
├── RECOMMENDATIONS.md                 # Performance optimization guide
├── lightrag_integration_plan.md       # Production deployment plan
├── challenge_data/
│   ├── william.md                     # 10 interconnected documents
│   └── william_benchmark.json         # 22 evaluation questions
└── lightrag_cache_ogx/               # Generated index (after running)
```

## What This Notebook Does

1. **Connects to OGX**: Uses your llama-stack endpoint for LLM and embeddings
2. **Ingests Documents**: Builds knowledge graph from William benchmark data
3. **Tests 3 Query Modes**:
   - **naive**: Vector similarity only (baseline)
   - **hybrid**: Local + global graph retrieval
   - **mix**: Combines all strategies (recommended)
4. **Evaluates Performance**: Calculates answer_correctness and faithfulness for all 22 questions
5. **Generates Leaderboard**: Compares modes with quantitative metrics
6. **Saves Results**: Exports to `lightrag_evaluation_results.csv`

## Expected Runtime

- **Document Ingestion**: ~10-15 minutes (builds knowledge graph)
- **Evaluation (22 questions × 3 modes)**: ~20-30 minutes
- **Total**: ~30-45 minutes

## Results

After running, you'll get:

- **Leaderboard table** showing which mode performs best
- **Per-question breakdown** of scores by mode
- **CSV file** with detailed results for analysis
- **Best mode per question** analysis
- **Win count summary** across all questions

## Optimization Recommendations

See `RECOMMENDATIONS.md` for guidance on:
- Improving answer accuracy (+15-25% possible)
- Enabling reranking
- Tuning chunk sizes and top_k
- Adjusting temperature for better faithfulness
- Using mix mode for best results

## Known Issues

- **OGX Timeouts**: The endpoint may timeout during indexing (504 errors). This is expected - the index still builds successfully.
- **None Responses**: Evaluation handles query failures gracefully and continues.
- **Memory**: Large knowledge graphs require ~4GB RAM minimum.

## Production Deployment

### Current Notebook: Local Storage (Development)

This notebook uses **local filesystem storage**:
- **Graph**: `NetworkXStorage` (stores as `.graphml` files)
- **Vectors**: `NanoVectorDBStorage` (stores as `.json` files)
- **KV/Status**: `JsonKVStorage` (stores as `.json` files)

This is sufficient for:
- ✅ Development and testing
- ✅ Single-machine deployments
- ✅ Proof-of-concept evaluations

### Production Options

For production deployment with durable storage, LightRAG supports:

**Graph Storage:**
- ✅ **Neo4j** (recommended - best performance)
- ✅ **PostgreSQL + AGE** (unified database option)
- ✅ Memgraph, OpenSearch, MongoDB

**Vector Storage (via ai4rag OGX):**
- ✅ **Milvus** (ai4rag current standard)
- ✅ **pgvector** (PostgreSQL extension)
- ⚠️ Qdrant, OpenSearch (check OGX deployment)

**Key Difference from ai4rag SimpleRAG:**
- ai4rag: 1 vector collection (chunks)
- LightRAG: **3 vector collections** (entities, relationships, chunks) + **graph database**

**See `STORAGE_BACKENDS.md` for:**
- Complete list of supported databases
- Configuration examples for each backend
- Migration path from dev to production
- Integration with ai4rag OGX
- Recommended architectures by scale

**See `lightrag_integration_plan.md` for:**
- ai4rag integration strategy (Phases 1-4)
- OGX vector wrapper implementation
- Kubeflow pipeline integration

## Configuration Options

### Environment Variables (.env)

```bash
# Required
OGX_BASE_URL=https://your-ogx-endpoint.com
OGX_API_KEY=your_api_key

# Optional (defaults shown)
# CHUNK_TOKEN_SIZE=1200
# CHUNK_OVERLAP=100
# TEMPERATURE=0.7
# TOP_K=5
```

### LightRAG Parameters

Edit the notebook cells to customize:

```python
# Cell 9: Chunk sizes
rag_openai = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=ogx_llm_func,
    embedding_func=embedding_func,
    addon_params={
        "enable_rerank": False,
        "chunk_token_size": 1200,      # Adjust this
        "chunk_overlap_token_size": 100 # And this
    }
)

# Cell 9: LLM temperature
temperature = kwargs.get("temperature", 0.7)  # Lower = more factual

# Cell 19: Retrieval top_k
param=QueryParam(mode="mix", top_k=5)  # Increase for more context
```

## Support

- **LightRAG Issues**: https://github.com/HKUDS/LightRAG/issues
- **OGX Documentation**: Contact your OGX admin
- **William Benchmark**: See `challenge_data/william_benchmark.json` for question format

## References

- [LightRAG Repository](https://github.com/HKUDS/LightRAG)
- [LightRAG API Docs](https://github.com/HKUDS/LightRAG/blob/main/docs/LightRAG-API-Server.md)
- [Programming Guide](https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md)
