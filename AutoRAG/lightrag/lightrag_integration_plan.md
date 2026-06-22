# LightRAG integration plan — Documents Graph RAG Pipeline

**Status:** Design (pre-implementation)  
**Pipeline name (proposed):** extend [`documents_rag_optimization_pipeline`](../documents_rag_optimization_pipeline/README.md) (preferred) or `documents-graph-rag-pipeline` (fallback)  
**Location:** `pipelines/training/autorag/documents_graph_rag_pipeline/` (design docs); implementation primarily in **ai4rag** + thin KFP changes  
**Related pipeline:** chunk RAG + ai4rag GAMOpt + OGX (today)

---

## 0. Strategic decisions

### 0.1 ai4rag-first (team-owned engine)

**ai4rag is owned and extended by the same team** that maintains this repository. That removes the main reason for a standalone LightRAG pipeline (waiting on upstream APIs, fork risk, duplicate HPO).

**Preferred approach:** implement graph RAG as a new **ai4rag RAG template** (LightRAG-backed) and extend **`AI4RAGExperiment`** to select template type and graph search-space parameters. Keep **one** Kubeflow optimization pipeline, **one** `rag_templates_optimization` component (extended), and **one** pattern / leaderboard model.

| Approach | When to use |
|----------|-------------|
| **A. ai4rag template + extend existing pipeline** (recommended) | Team can ship ai4rag changes on your cadence; want GAMOpt, same artifacts, OGX-only ops |
| **B. Standalone graph pipeline + KFP components** (fallback) | Need a demo before ai4rag merges; or want zero `lightrag-hku` dependency inside the engine |

The rest of this document describes **both** paths; **§9 phases assume path A** unless noted.

### 0.2 Simplest-first storage strategy (Updated 2026-06-22)

**Target:** Minimize new infrastructure and code for Phase 1 MVP.

**Decision:** Start with **PostgreSQL All-in-One** instead of multi-database approach.

| Storage Layer | Phase 1 MVP (Simplest) | Phase 2+ (Performance) |
|---------------|------------------------|------------------------|
| **Vectors** | OGX → pgvector (existing) | OGX → Milvus (existing) |
| **Graph** | PostgreSQL AGE (new extension) | Neo4j (new service) |
| **KV** | PostgreSQL tables (new tables) | Redis (new service) |
| **Status** | PostgreSQL tables (new tables) | Redis (new service) |
| **Total DBs** | **1** (PostgreSQL) | **2-3** (Milvus/pgvector + Neo4j + Redis) |

**Why PostgreSQL All-in-One for MVP:**
- ✅ Reuses existing ai4rag OGX pgvector integration (zero new vector code)
- ✅ Single database to provision (PostgreSQL 16.6+ with extensions)
- ✅ Single secret for all storage (simpler KFP configuration)
- ✅ Lower ops complexity (one connection, one backup, one monitoring target)
- ✅ Sufficient performance for evaluation workloads
- ⚠️ Graph queries slower than Neo4j (acceptable for MVP metrics)

**Migration path:** If graph performance becomes a bottleneck (measured in Phase 1), migrate to Neo4j in Phase 2 while keeping OGX pgvector for vectors. This is a **storage backend swap**, not a re-architecture.

**Is Neo4j a must-have?**  
- **Phase 1 (MVP evaluation):** ❌ No — PostgreSQL AGE sufficient  
- **Phase 2 (production scale):** ⚠️ Recommended — if graph latency <100ms required  
- **Phase 3 (large deployments >10M docs):** ✅ Yes — Neo4j cluster needed

See `STORAGE_BACKENDS.md` for detailed performance comparison and migration guide.

---

## 1. Purpose

Add **graph-augmented RAG** under the AutoRAG umbrella by extending **team-owned [ai4rag](https://github.com/IBM/ai4rag)** with a [LightRAG](https://github.com/HKUDS/LightRAG) (`lightrag-hku`) template, complementing the existing **`SimpleRAG`** chunk path.

| Lane | ai4rag template | Retrieval paradigm |
|------|-----------------|-------------------|
| Existing | `SimpleRAG` | Dense / hybrid ranker on OGX chunk index |
| New | `LightRAGTemplate` (proposed) | KG + vector (local / global / hybrid / mix / naive) |

Shared across lanes: docling extraction, benchmark data, **GAMOpt**, leaderboard metrics, OGX embed/LLM, and (target) unified `rag_patterns` layout with `pattern_type` discriminator.

---

## 2. Goals and non-goals

### Goals

- Reuse **docling** extraction and AutoRAG **test data** / **leaderboard** components.
- Run LightRAG **indexing** (`insert`) on the same `extracted_text` artifact (markdown per document).
- Support **query modes** relevant to graph RAG: at minimum `naive`, `local`, `global`, `hybrid`, `mix` (LightRAG `QueryParam.mode`).
- Emit **graph-RAG patterns** (manifest + eval results) comparable on the leaderboard with ai4rag patterns.
- Prefer **OGX** for LLM and embeddings (same secret model as today: `ogx_secret_name`).
- Extend **ai4rag** first; keep KFP changes minimal (pipeline param + search space + pattern export).
- Use **durable storage** for indexes (OGX/Milvus for vectors; graph DB or managed KV) — **not** task PVC as the system of record (PVC is ephemeral after the run completes).
- Document a phased path: **durable MVP (OGX vectors + graph DB)** → **GAMOpt over graph params** → deployment hardening.

### Non-goals (initial phases)

- Reusing existing **ai4rag / OGX chunk collections** as LightRAG indexes without re-indexing.
- Replacing ai4rag GAMOpt for chunk RAG (graph lane uses the **same** optimizer).
- Duplicate HPO in pipelines-components (no standalone Optuna loop if path A).
- MiniRAG fork integration (evaluate only if LightRAG MVP fails SLM/cost targets).
- LightRAG Server / WebUI as a managed product surface in v1 (Core-in-component only).
- Multimodal RAG-Anything / MinerU in v1 (docling path remains canonical).

---

## 3. Architecture overview

### 3.1 Path A — Extend existing Kubeflow DAG (recommended)

```text
test_data_loader
       │
documents_discovery ──► text_extraction ──► search_space_preparation
       │                                              │
       │                                              ▼
       └──────────────────────────────► rag_templates_optimization
                                              (ai4rag: SimpleRAG | LightRAGTemplate)
                                                      │
                              ┌────────────────────────┴────────────────────────┐
                              ▼                                                 ▼
              prepare_responses_api_requests (chunk patterns)    leaderboard_evaluation
                                                                 (chunk + graph patterns)
```

**pipelines-components changes (thin):**

| Asset | Change |
|-------|--------|
| `documents_rag_optimization_pipeline` | Add `rag_template_type` (e.g. `simple` \| `lightrag` \| `both`); optional graph-specific search space inputs |
| `search_space_preparation` | Include graph parameters when `lightrag` selected (or separate MPS report file) |
| `rag_templates_optimization` | Pass `template_type` / graph settings into `AI4RAGExperiment`; bump `ai4rag` pin |
| `leaderboard_evaluation` | Columns for `pattern_type`, LightRAG `query.mode`, storage profile |
| `prepare_responses_api_requests` | Chunk patterns only in v1; graph serving in phase 3 |

**ai4rag changes (primary engineering):**

| Module | Change |
|--------|--------|
| `ai4rag/rag/template/lightrag_template.py` | `LightRAGTemplate(BaseRAGTemplate)`: `build_index`, `generate`, `generate_stream` delegating to LightRAG Core |
| `ai4rag/rag/template/` | Register template; optional `get_template(name)` factory |
| `ai4rag/core/experiment/experiment.py` | `rag_template_type: Literal["simple", "lightrag"]`; branch indexing/eval; stop hardcoding `SimpleRAG` only |
| `ai4rag/search_space/` | Parameters: `query_mode`, `top_k`, `chunk_top_k`, LightRAG chunk sizes, `storage_profile`, etc. |
| `ai4rag/rag/vector_store/` (phase 3) | Optional `OGXLightRAGVectorStorage` adapter if not using LightRAG built-in Milvus |
| `pyproject.toml` | Optional extra: `ai4rag[lightrag]` → `lightrag-hku` pin |

### 3.2 Path B — Standalone graph pipeline (fallback)

Use only if ai4rag work is blocked. Same DAG as originally drafted:

```text
… ──► lightrag_indexing ──► lightrag_evaluation ──► leaderboard_evaluation
```

See §13 for component list. Avoid running path A and B in production simultaneously.

### 3.2 LightRAG runtime model

LightRAG requires **four storage roles** (see [Programming with LightRAG Core](https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md)):

| Role | Purpose | Ephemeral (dev only) | **Durable (pipeline default)** |
|------|---------|----------------------|--------------------------------|
| `kv_storage` | Chunks, full docs, LLM cache | `JsonKVStorage` on task PVC | `PGKVStorage`, `RedisKVStorage`, or `MongoKVStorage` |
| `vector_storage` | Embeddings for **entities**, **relationships**, **chunks** | `NanoVectorDBStorage` on PVC | **`OGXVectorDBStorage`** in ai4rag (wrappers → OGX/Milvus) |
| `graph_storage` | Entity–relation graph | `NetworkXStorage` on PVC | **`Neo4JStorage`**, **`PGGraphStorage` (AGE)**, or `MongoGraphStorage` |
| `doc_status_storage` | Indexing progress | `JsonDocStatusStorage` | Same tier as KV (e.g. `PGDocStatusStorage`) |

**PVC vs durable storage (OpenShift AI / KFP):**

- Task-mounted **PVC is tied to the run** and is **not** a reliable long-term index after the pipeline completes (same constraint as AutoML workspace PVC used for progress, not for serving).
- Chunk RAG today already persists retrieval state in **OGX** via `collection_name` in `pattern.json` — not on the pod filesystem.
- Graph RAG must follow the same rule: **patterns reference external store IDs** (OGX collection/workspace prefix, Neo4j label prefix, etc.), not paths under `/tmp` or a run-scoped PVC.

**Optional PVC uses (non-authoritative):**

- Scratch `working_dir` during `insert` (cache, export) if LightRAG requires a local directory.
- Packaging **artifacts** for Kubeflow (notebooks, `pattern.json`, tarball backup) — these are copies for humans/CI, not the live index.

**Workspace isolation:** stable `workspace` / `collection_prefix` per pattern (e.g. derived from pattern name or user-supplied index id), not only KFP run id, so re-runs and serving can find the same stores.

---

## 4. Storage and OGX strategy

### 4.1 Cannot share ai4rag Milvus collections

- ai4rag `OGXVectorStore`: **chunk-only** schema, OGX-managed collection names.
- LightRAG Milvus: **three** collections per workspace (`*_entities`, `*_relationships`, `*_chunks`) with distinct fields and graph build via LLM extraction on `insert`.

**Conclusion:** Same corpus, **separate index**; compare via leaderboard, not shared collection.

### 4.2 OGX integration options — SIMPLEST FIRST

**Updated 2026-06-22:** Prioritizing simplest viable integration.

| Profile | Vector + embed | Graph + KV | Infrastructure Needed | Complexity |
|---------|----------------|------------|----------------------|------------|
| **PostgreSQL All-in-One** (Phase 1 MVP) | **OGX → pgvector** (existing ai4rag) | **PostgreSQL AGE** (same DB) | 1 database (PostgreSQL 16.6+) | ⭐ Simplest |
| **Durable OGX + Neo4j** (Phase 2) | **OGX → Milvus** (existing ai4rag) | **Neo4j** (separate) | 2 services (Milvus + Neo4j) | ⭐⭐ Recommended long-term |
| **Dev / CI only** | `NanoVectorDBStorage` (local) | `NetworkXStorage` (local) | 0 (local files) | ⭐ Dev only |

**Phase 1 MVP Decision: PostgreSQL All-in-One**

**Why simplest:**
- ✅ **Single database** (PostgreSQL with pgvector + AGE extensions)
- ✅ **Reuses existing ai4rag OGX pgvector** integration (no new code)
- ✅ **Same connection for all 4 storage layers** (vector, graph, kv, status)
- ✅ **Lower ops burden** than multi-database setup
- ❌ **Graph performance lower than Neo4j** (acceptable for MVP)

**Phase 2 upgrade path:** Migrate graph to Neo4j when performance requirements demand it (keep OGX vectors).

**Is Neo4j a must-have?** 
- Phase 1 MVP: ❌ **No** — PostgreSQL AGE sufficient
- Production scale: ✅ **Yes** — Neo4j recommended for performance
- See `STORAGE_BACKENDS.md` for detailed comparison

**Recommendation:** Start with PostgreSQL All-in-One (Phase 1), measure performance, upgrade to Neo4j only if graph query latency becomes a bottleneck.

**GAMOpt note:** Each trial needs a distinct durable `workspace` / collection prefix (or explicit cleanup after failed trials). Winning patterns retain references in `pattern.json`; failed trials may schedule async cleanup jobs.

### 4.3 Embedding lock-in

- Fix `embedding_model_id` (and params) at index time; use the same model at query time.
- Changing embedder dimension forces LightRAG storage recreate (document in pattern metadata).

---

## 5. Query modes and search space

### 5.1 LightRAG vs ai4rag “hybrid”

| Term | Meaning |
|------|---------|
| ai4rag `search_mode: hybrid` | Dense retrieval + hybrid **ranker** (BM25-style fusion) |
| LightRAG `mode: hybrid` | **Local + global** graph retrieval |
| LightRAG `mode: mix` | Knowledge graph + **vector chunk** search (often default when reranker enabled) |

Document this in pattern READMEs to avoid operator confusion.

### 5.2 Phase 1 (fixed config)

Single pattern per run:

- `QueryParam.mode`: `mix` (or `hybrid` if no reranker)
- `top_k`, `chunk_top_k`, token budgets: conservative defaults from LightRAG env docs
- LLM: OGX-backed completion for entity extraction and query

### 5.3 Phase 2 (search space + optimization)

Candidate parameters (YAML consumed by `graph_search_space_preparation`):

```yaml
# Illustrative — finalize during implementation
indexing:
  chunk_token_size: [512, 1200]
  chunk_overlap_token_size: [50, 100]
  entity_extract_max_gleaning: [1, 2]
query:
  mode: [naive, local, global, hybrid, mix]
  top_k: [20, 40, 60]
  chunk_top_k: [10, 20]
  enable_rerank: [true, false]
embedding_model_id: [<from OGX catalog>]
generation_model_id: [<from OGX catalog>]
workspace: <derived from run>
storage_profile: [mvp_local, milvus_neo4j, ogx_milvus]
```

**Optimizer choices (pick one in design review):**

1. **Optuna** in `lightrag_optimization` (parallel to ai4rag, not integrated with GAMOpt).
2. **Grid / random** for MVP HPO (smaller scope).
3. **Future:** extend ai4rag experiment type for graph templates (larger lift).

**Optimization metric:** reuse `faithfulness`, `answer_correctness`, `context_correctness` (same as chunk pipeline).

---

## 6. Pattern artifact schema (proposed)

Extend leaderboard-compatible **graph RAG pattern** JSON (versioned):

```json
{
  "pattern_version": "1.0",
  "pattern_type": "lightrag",
  "workspace": "<run-scoped-id>",
  "storage": {
    "kv_storage": "PGKVStorage",
    "vector_storage": "OGXVectorDBStorage",
    "graph_storage": "Neo4JStorage",
    "workspace": "<stable-index-id>",
    "ogx_collection_prefix": "<workspace-derived>",
    "neo4j_workspace_label": "<optional-isolation>"
  },
  "indexing": {
    "chunk_token_size": 1200,
    "chunk_overlap_token_size": 100,
    "embedding_model_id": "<ogx-model-id>",
    "embedding_params": {}
  },
  "query_defaults": {
    "mode": "mix",
    "top_k": 40,
    "chunk_top_k": 20
  },
  "generation": {
    "model_id": "<ogx-model-id>",
    "params": {}
  },
  "ogx": {
    "vector_io_provider_id": "<optional — production B>",
    "collection_prefix": "<workspace-derived>"
  },
  "metrics": {
    "faithfulness": 0.0,
    "answer_correctness": 0.0,
    "context_correctness": 0.0
  }
}
```

**Artifacts per pattern:**

- `pattern.json` (manifest above)
- `lightrag_working_dir/` (or object-store URI in later phase)
- `evaluation_results.json` (per-question scores, retrieved contexts for RAGAS-style audit)
- `inference_notebook.ipynb` (generated from template, analogous to `ogx_inference_template.ipynb`)

**Not in v1:** OGX `/v1/responses` request bodies for graph RAG (chunk pipeline’s `prepare_responses_api_requests` assumes ai4rag chunk retrieval). Phase 3: new deployment component or extend existing with `pattern_type` branch.

---

## 7. OGX and LLM wiring

### 7.1 Embeddings

Wrap OGX in LightRAG `EmbeddingFunc`:

```python
# Pseudocode — implement in lightrag_indexing shared module
async def ogx_embed(texts: list[str]) -> np.ndarray:
    return await ogx_embedding_model.aembed_documents(texts)

embedding_func = EmbeddingFunc(
    embedding_dim=<from model>,
    max_token_size=<from model>,
    func=ogx_embed,
    model_name=embedding_model_id,
)
```

Use the same `OgxClient` creation / SSL retry pattern as `documents_indexing` and `search_space_preparation`.

### 7.2 LLM (extraction + query)

- Entity/relation extraction during `insert` needs a capable model (LightRAG recommends ≥32B class for indexing; platform may use best available OGX model).
- Query-stage model may differ (stronger model at query time per LightRAG guidance).
- Route via OGX OpenAI-compatible or documented LightRAG provider hooks; avoid hardcoding vendor SDKs in components.

### 7.3 Kubernetes secrets

| Task | Secrets |
|------|---------|
| Data path | `test_data_secret_name`, `input_data_secret_name` (unchanged) |
| LightRAG indexing / eval | `ogx_secret_name` → `OGX_CLIENT_BASE_URL`, `OGX_CLIENT_API_KEY` |
| Milvus direct (production A only) | New optional `milvus_secret_name` or platform-supplied env |
| Neo4j (optional) | `neo4j_secret_name` |

Pipeline parameter **`vector_io_provider_id`**: required when `storage_profile=ogx_milvus` (production B); optional/disabled for MVP PVC profile.

---

## 8. Pipeline parameters (proposed)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rag_template_type` | str | `simple` | `simple` \| `lightrag` \| `both` — selects ai4rag template(s); **path A** |
| `test_data_secret_name` | str | — | Same as chunk pipeline |
| `test_data_bucket_name` | str | — | Same as chunk pipeline |
| `test_data_key` | str | — | Same as chunk pipeline |
| `input_data_secret_name` | str | — | Same as chunk pipeline |
| `input_data_bucket_name` | str | — | Same as chunk pipeline |
| `input_data_key` | str | `""` | Same as chunk pipeline |
| `ogx_secret_name` | str | — | OGX API credentials |
| `vector_io_provider_id` | str | `""` | OGX vector provider (production B); empty for MVP |
| `embedding_model_id` | str | — | OGX embedding model (fixed for run in v1) |
| `generation_model_id` | str | — | OGX LLM for extract + answer |
| `extraction_model_id` | str | optional | Override for indexing-only LLM |
| `optimization_metric` | str | `faithfulness` | Leaderboard primary metric |
| `storage_profile` | str | `ogx_neo4j` | `ogx_neo4j` \| `ogx_postgres_age` \| `dev_local` (non-prod) |
| `index_workspace` | str | `""` | Stable id for OGX collections + graph isolation; empty → generated once per pattern |
| `graph_secret_name` | str | optional | Neo4j or Postgres credentials when not in platform env |
| `query_mode` | str | `mix` | LightRAG QueryParam.mode (v1 fixed) |

---

## 9. Implementation phases (path A — ai4rag-first)

### Phase 0 — Design sign-off (current)

- [x] Integration plan (this document)
- [ ] ai4rag ADR: `LightRAGTemplate` API, `pattern_type`, optional dep `ai4rag[lightrag]`
- [ ] Pipelines Working Group issue for KFP / component changes ([`GOVERNANCE.md`](../../../../docs/GOVERNANCE.md))

### Phase 1 — Simplest MVP: PostgreSQL All-in-One (Tech Preview)

**Updated 2026-06-22:** Targeting simplest viable integration first.

**Prerequisite:** PostgreSQL 16.6+ with **pgvector** + **AGE** extensions in target cluster.

**Infrastructure:**
- ✅ PostgreSQL 16.6+ (single database)
  - pgvector extension (already used by ai4rag OGX)
  - AGE extension (graph support - new)
- ✅ OGX with `pgvector-provider` configured (reuses existing ai4rag setup)
- ❌ **No Neo4j needed** for MVP
- ❌ **No Redis needed** for MVP (use PostgreSQL tables for KV/status)

**ai4rag deliverables:**

- `OGXVectorDBStorage` wrapper — delegates to existing OGX pgvector for 3 collections
- `LightRAGTemplate` wired to **PostgreSQL AGE** (graph) + **PostgreSQL** (KV/status)
- OGX wrappers for `EmbeddingFunc` and LLM (reuse existing `OGXEmbeddingModel` / `OGXFoundationModel`)
- `AI4RAGExperiment(rag_template_type="lightrag")` — fixed `QueryParam.mode="mix"`
- Pattern JSON: `"pattern_type": "lightrag"`, `"storage_profile": "postgres_all_in_one"`
- Unit tests: mock OGX + PostgreSQL; integration test against shared dev PostgreSQL

**pipelines-components deliverables:**

- Bump `ai4rag` version in `rag_templates_optimization` requirements
- Pipeline params: `rag_template_type`, `postgres_secret_name` (reuse existing)
- Extend `leaderboard_evaluation` for `pattern_type` column
- Integration test: pattern queryable after pod exits (PostgreSQL connection only)

**Acceptance:** 
- One LightRAG pattern from `documents_rag_optimization_pipeline`
- Stores vectors in OGX pgvector, graph in PostgreSQL AGE, KV/status in PostgreSQL
- Inference notebook reconnects with **single PostgreSQL connection** (no Neo4j/Redis)

**Why this is simplest:**
1. **No new databases** — reuses PostgreSQL already deployed for ai4rag
2. **No new OGX code** — pgvector integration already exists
3. **Single secret** — one PostgreSQL connection for all storage layers
4. **Minimal ai4rag changes** — just LightRAG template wrapper + storage config

**Performance note:** PostgreSQL AGE has lower graph query performance than Neo4j. This is acceptable for MVP evaluation. Phase 2 can migrate to Neo4j if needed.

### Phase 2 — GAMOpt over graph search space

**ai4rag:**

- Search space parameters: `query.mode`, `top_k`, `chunk_top_k`, indexing chunk tokens, `enable_rerank`, etc.
- Reuse **GAMOpt**; ensure experiment reuses collections/workspaces where safe (separate workspace per graph index)

**pipelines-components:**

- `search_space_preparation` emits graph dimensions when requested
- Optional pipeline mode `rag_template_type=both` → two template families in one run (larger budget) or two pipeline runs

### Phase 3 — Deployment + lifecycle

- Trial cleanup policy for orphaned OGX collections / graph workspaces
- Notebooks: `ogx_lightrag_indexing_template.ipynb`, `ogx_lightrag_inference_template.ipynb` (connect via pattern refs only)
- `prepare_responses_api_requests` or successor for graph serving (if OGX API fits; else document notebook-only)
- Optional: S3 artifact **backup** of index metadata (not primary store)

### Phase 4 — Optional enhancements

- `rag_template_type=both` leaderboard comparison in one HTML artifact
- RAGAS / Langfuse via LightRAG hooks inside template
- Fusion template: `SimpleRAG` retriever + `LightRAGTemplate` query (advanced `BaseRAGTemplate`)

### Path B phases (fallback only)

If path A slips: implement §3.2 standalone `lightrag_indexing` / `lightrag_evaluation` components as originally specified; merge into path A when ai4rag template lands.

---

## 10. ai4rag `LightRAGTemplate` design (path A)

### 10.1 `BaseRAGTemplate` contract

Implement in **ai4rag** (not pipelines-components):

```python
class LightRAGTemplate(BaseRAGTemplate):
    """Graph RAG via LightRAG Core; OGX for embed + LLM."""

    def build_index(self, documents, indexing_params: dict) -> None:
        # Map documents → LightRAG insert (markdown/text)
        # Persist working_dir / workspace from indexing_params
        ...

    def generate(self, question: str, rag_params: dict) -> str:
        # LightRAG aquery(question, QueryParam(mode=rag_params["query_mode"], ...))
        ...

    def generate_stream(self, question: str, rag_params: dict):
        ...
```

- **Do not** implement graph RAG only via `BaseVectorStore` — chunk vector store is insufficient.
- Reuse **`OGXFoundationModel`** / **`OGXEmbeddingModel`** inside LightRAG `EmbeddingFunc` and LLM callbacks (same credentials as `SimpleRAG`).

### 10.2 `AI4RAGExperiment` changes

- Add `rag_template_type: str = "simple"`.
- In the evaluation loop: instantiate `SimpleRAG` or `LightRAGTemplate` per trial.
- Indexing: graph template runs LightRAG `insert` (separate workspace per trial); chunk template keeps current `vector_store.add_documents` path.
- `output.json` / pattern payload: add top-level `"pattern_type": "simple" | "lightrag"`.

### 10.3 Optional dependency

```toml
# ai4rag pyproject.toml
[project.optional-dependencies]
lightrag = ["lightrag-hku>=<pinned>"]
```

KFP component installs `ai4rag[lightrag]` when `rag_template_type != "simple"`.

---

## 11. Component design notes (path B fallback)

### 11.1 `lightrag_indexing`

**Inputs:** `extracted_text` (Dataset), `embedding_model_id`, `generation_model_id`, `storage_profile`, `lightrag_workspace`, OGX env  
**Outputs:** `lightrag_manifest` (JSON), `lightrag_storage` (Directory artifact — PVC snapshot or tarball)

**Logic:**

1. List `*.md` from extracted_text (same as `documents_indexing`).
2. `await rag.initialize_storages()` then `insert` per file or batched.
3. `await rag.finalize_storages()` / `index_done_callback` as required by LightRAG.
4. Write manifest with storage paths and model ids.

**Resource hints:** Higher than chunk indexing (LLM extraction per chunk batch); start `cpu_request=4`, `memory_request=16Gi`, tune from integration runs.

### 11.2 `lightrag_evaluation`

**Inputs:** `test_data`, `lightrag_manifest`, `lightrag_storage`, `query_mode`, OGX env  
**Outputs:** `evaluation_results`, `rag_patterns` (compatible structure for leaderboard)

**Logic:**

1. Reload LightRAG from manifest `working_dir` + storage config.
2. For each benchmark question: `aquery(question, QueryParam(mode=...))`.
3. Score with same eval stack as ai4rag (import from ai4rag eval utilities or duplicate thin wrapper).
4. Assemble pattern dict with metrics.

### 11.3 Shared module (path B or ai4rag internal)

Prefer **`ai4rag/rag/lightrag/ogx_bridge.py`** for OGX helpers; use `components/training/autorag/shared/lightrag_ogx.py` only in path B.

---

## 12. Testing strategy

| Level | Scope |
|-------|--------|
| Unit | Mock LightRAG storages; test manifest I/O, OGX client retry |
| Component local | `setup_and_teardown_subprocess_runner` with tiny corpus |
| Pipeline unit | Compile DAG; parameter wiring; secret annotations |
| Integration | S3 + OGX + small doc set; assert pattern + leaderboard artifacts |

**Fixtures:** Reuse `documents_rag_optimization_pipeline/tests/integration_config.py` patterns; add `storage_profile=mvp_local` profile.

**CI:** Register pipeline in component-pipeline-tests workflow when `pipeline.py` exists; pin `lightrag-hku` in lockfile policy per [`CONTRIBUTING.md`](../../../../docs/CONTRIBUTING.md).

---

## 13. Risks and mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Indexing cost (LLM entity extraction) | High $/run | Batch inserts; cache via `enable_llm_cache`; cap corpus size in MVP |
| SLM quality on extraction | Poor graph | Document minimum model; use `extraction_model_id` ≥ recommended tier |
| Ephemeral PVC assumed durable | Index lost after run | **No catalog MVP on PVC**; pattern.json references OGX + graph DB only |
| GAMOpt trial sprawl | Orphaned Milvus/Neo4j data | Per-trial `workspace` prefix + cleanup job / TTL policy |
| LightRAG API drift | Breakage | Pin package version; contract tests on `QueryParam` |
| OGX adapter complexity | Blocks phase 1 | Prioritize three-namespace vector wrapper in ai4rag before GAMOpt |
| Graph DB ops | New secret / capacity | Align with platform Neo4j or Postgres AGE; document sizing |
| Leaderboard schema mismatch | UI errors | Version `pattern_type`; extend `leaderboard_evaluation` with tests |
| No `/v1/responses` path v1 | Deployment gap | Document manual notebook serving until phase 3 |

---

## 14. Repository layout (target)

**Path A (primary):**

```text
# ai4rag repository (team-owned)
ai4rag/
  rag/template/lightrag_template.py
  rag/lightrag/ogx_bridge.py          # EmbeddingFunc + LLM adapters
  core/experiment/experiment.py       # rag_template_type
  tests/unit/template/test_lightrag_template.py

# pipelines-components
pipelines/training/autorag/documents_graph_rag_pipeline/
  LIGHT_RAG_INTEGRATION_PLAN.md
  README.md
components/training/autorag/
  rag_templates_optimization/         # extend, don't duplicate
  search_space_preparation/           # graph search space
  leaderboard_evaluation/             # pattern_type columns
```

**Path B (fallback):** add `lightrag_indexing/`, `lightrag_evaluation/` under `components/training/autorag/` and optional `documents_graph_rag_pipeline/pipeline.py`.

---

## 15. Governance and documentation

- Open **component submission issue** (`.github/ISSUE_TEMPLATE/component_submission.md`) for new catalog components.
- Link issue from PR; obtain Pipelines Working Group approval per [`GOVERNANCE.md`](../../../../docs/GOVERNANCE.md).
- After implementation: `make readme TYPE=pipeline CATEGORY=training SUBCATEGORY=autorag NAME=documents_graph_rag_pipeline`.
- Update [`pipelines/training/autorag/README.md`](../README.md) with link to graph RAG pipeline.

---

## 16. Open questions

1. **Minimum OGX LLM tier** for graph indexing — align with LightRAG guidance vs cost caps?
2. ~~**Production graph DB**~~ — ✅ **RESOLVED (2026-06-22):** Phase 1 uses PostgreSQL AGE (simplest). Neo4j deferred to Phase 2 if performance metrics require it.
3. **Single run vs two runs** — `rag_template_type=both` in one GAMOpt budget vs separate pipeline runs for chunk vs graph?
4. **Pattern serving** — extend `prepare_responses_api_requests` or graph-only notebooks in v1?
5. **Base image** — `ai4rag[lightrag]` in existing AutoRAG image vs separate image tag?
6. **Multilingual** — defer until chunk pipeline exits English MVP?
7. **ai4rag repo location** — confirm canonical remote/branch strategy for template development (IBM fork vs team fork).

---

## 17. Performance Optimization Recommendations

Based on LightRAG documentation and William benchmark testing, these optimizations can improve accuracy by +15-25%.

### High-Impact Optimizations (Phase 1)

**1. Use "mix" Mode** (Expected: +5-10% accuracy)
```python
retrieval_modes = ["naive", "hybrid", "mix"]  # mix = best results
```
Why: Combines local graph + global graph + naive vector retrieval for comprehensive results.

**2. Enable Reranking** (Expected: +8-12% accuracy) - if OGX provides reranker
```python
param=QueryParam(mode="mix", top_k=20, enable_rerank=True)
```
Why: LightRAG docs state this "significantly improves query quality" (+1-2s latency).  
Recommended models: `BAAI/bge-reranker-v2-m3`, Jina, Cohere

**3. Increase top_k to 20** (Expected: +3-7% accuracy)
```python
param=QueryParam(mode="mix", top_k=20)  # vs default 5
```
Why: Multi-hop questions need more context. Caveat: higher latency.

### Medium-Impact Optimizations (Phase 2)

**4. Optimize Chunk Size** (Expected: +2-5% accuracy)
```python
rag = LightRAG(
    addon_params={
        "chunk_token_size": 1200,  # vs default ~512
        "chunk_overlap_token_size": 100
    }
)
```
Why: Larger chunks capture more context for entity/relationship extraction.

**5. Lower LLM Temperature** (Expected: +5-10% faithfulness)
```python
temperature=kwargs.get("temperature", 0.2)  # vs default 0.7
```
Why: Reduces hallucination, improves factual consistency for multi-hop reasoning.

**6. Increase max_tokens** (Expected: better completeness)
```python
max_tokens=kwargs.get("max_tokens", 4096)  # vs default 2048
```
Why: Allows detailed answers for complex questions.

### Advanced Optimizations (Phase 3)

**7. Role-Specific LLMs** (if OGX supports)
- Stronger model (≥70B) for entity extraction during indexing
- Lighter model (31B) acceptable for query generation

**8. Enable LLM Caching**
```python
addon_params={"enable_llm_cache": True}
```
Why: Cost/time savings, minimal accuracy impact.

**9. Test All Query Modes**
```python
retrieval_modes = ["naive", "local", "global", "hybrid", "mix"]
```
Use cases:
- `naive`: Simple fact lookup (baseline)
- `local`: Entity-specific ("Who is X?")
- `global`: Cross-document patterns
- `hybrid`: Local + global
- `mix`: All strategies (recommended default)

### Expected Combined Impact

| Optimization | Δ Accuracy | Δ Faithfulness |
|-------------|-----------|----------------|
| mix mode | +5-10% | +3-5% |
| Reranking | +8-12% | +5-8% |
| top_k 5→20 | +3-7% | +2-4% |
| Chunk 512→1200 | +2-5% | +1-3% |
| Temp 0.7→0.2 | +1-3% | +5-10% |
| **Total** | **+15-25%** | **+12-20%** |

### Quick-Start Template

```python
# Optimized initialization
rag = LightRAG(
    working_dir=WORKING_DIR,
    llm_model_func=ogx_llm_func,
    embedding_func=embedding_func,
    addon_params={
        "enable_rerank": True,  # If available
        "chunk_token_size": 1200,
        "chunk_overlap_token_size": 100,
        "enable_llm_cache": True
    }
)

# Optimized query
response = await rag.aquery(
    question,
    param=QueryParam(
        mode="mix",  # Best results
        top_k=20,    # More context
        enable_rerank=True
    )
)
```

**References:**
- [LightRAG Docs](https://github.com/HKUDS/LightRAG/blob/main/docs/LightRAG-API-Server.md)
- [Programming Guide](https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md)

---

## 18. Storage Backend Details

### Supported Backends Summary

LightRAG supports these production backends:

| Storage Type | Phase 1 (Simplest) | Phase 2+ (Performance) | Also Supported |
|--------------|-------------------|----------------------|----------------|
| **Graph** | PostgreSQL AGE | Neo4j | Memgraph, OpenSearch, MongoDB |
| **Vector** | OGX → pgvector | OGX → Milvus | Qdrant, OpenSearch, Faiss |
| **KV** | PostgreSQL tables | Redis | MongoDB, OpenSearch |
| **Status** | PostgreSQL tables | Redis | MongoDB, OpenSearch |

### PostgreSQL Requirements (Phase 1)

**Version:** PostgreSQL 16.6+

**Required Extensions:**
```sql
CREATE EXTENSION IF NOT EXISTS vector;  -- pgvector (already enabled for ai4rag)
CREATE EXTENSION IF NOT EXISTS age;     -- Apache AGE for graph (new)
```

**Performance Characteristics:**
- Vector queries (pgvector): <50ms p95
- Graph queries (AGE): 50-200ms p95 (simple), 100-500ms (complex)
- KV operations: <10ms p95

**Good for:** MVP evaluation, <1M entities, non-latency-critical queries

### Neo4j Migration (Phase 2 - If Needed)

**When to upgrade:**
- Graph query p95 >100ms sustained
- Complex traversals (3+ hops) needed frequently
- >1M entities in knowledge graph
- Production SLAs require <50ms graph latency

**Migration Steps:**
1. Export graph from PostgreSQL AGE (LightRAG built-in export)
2. Provision Neo4j instance
3. Change `graph_storage="Neo4JStorage"` in ai4rag template
4. Import graph data
5. Validate query results match
6. Update pattern JSON with Neo4j connection info

**Impact:** Configuration change only - no ai4rag template code changes needed.

---

## 19. References

- [LightRAG](https://github.com/HKUDS/LightRAG) — Core, storage matrix, `QueryParam`
- [LightRAG — Programming with Core](https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md)
- [PostgreSQL AGE](https://age.apache.org/) — Apache AGE graph extension
- [ai4rag](https://github.com/IBM/ai4rag)
- Existing: `components/data_processing/autorag/documents_indexing`, `components/training/autorag/rag_templates_optimization`

---

## 20. Revision history

| Date | Author | Change |
|------|--------|--------|
| 2026-05-20 | AutoRAG design | Initial integration plan |
| 2026-05-20 | AutoRAG design | ai4rag-first strategy (team-owned engine) |
| 2026-05-20 | AutoRAG design | Durable storage requirement (OGX + graph DB); PVC not system of record |
| 2026-06-22 | AutoRAG design | **Simplified to PostgreSQL All-in-One** for Phase 1 MVP; deferred Neo4j to Phase 2 based on metrics |
| 2026-06-22 | AutoRAG design | Consolidated storage backend documentation into integration plan |
