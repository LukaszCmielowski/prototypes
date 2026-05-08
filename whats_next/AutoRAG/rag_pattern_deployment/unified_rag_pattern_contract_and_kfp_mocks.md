# Unified RAG Pattern contract: KFP orchestration, ai4rag, and LightRAG

This document specifies a **versioned platform envelope** so multiple RAG engines (e.g. **ai4rag** and **LightRAG**) can each emit a **RAG Pattern** next to one another, with **Kubeflow Pipelines (KFP)** acting as **orchestration and unification** for integration with the AutoRAG UI and Gen AI Studio.

**Related:** [Deploying the AutoRAG Patterns](./deploying_autorag_patterns.md) (current artifact layout, Llama Stack `v1/responses`, indexing pipeline notes).

---

## 1. Design principles

1. **One run, many engines** — A parent KFP `run_id` is the anchor. Each engine writes a **sibling subtree** under the same object-storage prefix so the UI can list all patterns produced in that run.
2. **One envelope per pattern** — Engines emit the **same top-level files** where possible. Engine-specific details live in **`pattern.json`** (nested under an `engine` or `engines` object) or in **explicitly typed** recipe files so parsers do not break.
3. **Recipes are not forced to be identical HTTP** — Llama Stack `file_search` and LightRAG Server query APIs are different surfaces. The bundle carries **one canonical `pattern.json`** plus **typed recipe** files (see §5).
4. **Secrets never in JSON** — Only **references** (`secretRef`, `configMapRef`, vault key identifiers). Runtimes resolve them.

---

## 2. Object storage layout (mock)

Extend the existing style (`documents-rag-optimization-pipeline/<run_id>/...`) without breaking current consumers:

```text
s3://bucket/documents-rag-optimization-pipeline/
└── <run_id>/
    ├── run_manifest.json              # Run-level index for UI (discover engines + patterns)
    ├── eval/
    │   ├── golden_set.json            # Optional: pointer + hash to eval set
    │   └── eval_report.json           # Cross-engine comparison (shared metric schema)
    └── rag_patterns/
        ├── ai4rag/
        │   └── <pattern_slug>/
        │       ├── pattern.json
        │       ├── recipe_llama_stack_responses.json
        │       ├── indexing_notebook.ipynb
        │       ├── inference_notebook.ipynb
        │       └── scores.json
        └── lightrag/
            └── <pattern_slug>/
                ├── pattern.json
                ├── recipe_lightrag_query.json
                ├── indexing_notebook.ipynb
                ├── inference_notebook.ipynb
                └── scores.json
```

**Notes:**

- **`run_manifest.json`** — First file the UI loads to discover engines, patterns, and status.
- **`rag_patterns/<engine>/<slug>/`** — Slugs are unique **per engine** path; avoids collisions when both engines emit a pattern named similarly.

---

## 3. `run_manifest.json` (mock)

Orchestration handoff to the UI / API:

```json
{
  "schema": "https://redhat.com/schemas/ai/rag-run-manifest/v1",
  "run_id": "run-2026-04-21-8f3a2c",
  "pipeline_name": "rag-pattern-orchestrator",
  "pipeline_version": "1.4.2",
  "status": "succeeded",
  "created_at": "2026-04-21T14:02:11Z",
  "finished_at": "2026-04-21T15:47:03Z",
  "inputs": {
    "corpus_uri": "s3://bucket/corpora/finance-faq/v3/",
    "eval_uri": "s3://bucket/evalsets/finance-rag-v1.jsonl",
    "engines_requested": ["ai4rag", "lightrag"]
  },
  "engines": {
    "ai4rag": {
      "status": "succeeded",
      "kfp_task_id": "ai4rag-optimize-abc",
      "patterns": [
        {
          "slug": "milvus-rrf-bge-m3",
          "path": "rag_patterns/ai4rag/milvus-rrf-bge-m3/",
          "primary_score": 0.81,
          "score_metric": "ragas_answer_relevancy"
        }
      ]
    },
    "lightrag": {
      "status": "succeeded",
      "kfp_task_id": "lightrag-index-xyz",
      "patterns": [
        {
          "slug": "pg-mix-bge-m3",
          "path": "rag_patterns/lightrag/pg-mix-bge-m3/",
          "primary_score": 0.84,
          "score_metric": "ragas_answer_relevancy"
        }
      ]
    }
  },
  "eval": {
    "path": "eval/eval_report.json",
    "comparable": true,
    "notes": "Same golden set and same generation LLM endpoint for both engines."
  }
}
```

**Partial failure** (UI still useful):

```json
{
  "schema": "https://redhat.com/schemas/ai/rag-run-manifest/v1",
  "run_id": "run-2026-04-21-9c1d00",
  "pipeline_name": "rag-pattern-orchestrator",
  "pipeline_version": "1.4.2",
  "status": "partial",
  "engines": {
    "ai4rag": {
      "status": "succeeded",
      "patterns": [
        { "slug": "p1", "path": "rag_patterns/ai4rag/p1/", "primary_score": 0.79, "score_metric": "ragas_answer_relevancy" }
      ]
    },
    "lightrag": {
      "status": "failed",
      "error_code": "LIGHTRAG_INDEX_OOM",
      "patterns": []
    }
  },
  "eval": { "path": "eval/eval_report.json", "comparable": false, "notes": "LightRAG branch failed before eval." }
}
```

---

## 4. Shared `pattern.json` schema (concept)

### 4.1 Stable top-level fields (all engines)

| Field | Purpose |
|--------|--------|
| `schema` | Versioned JSON Schema URI for this document |
| `pattern_id` | UUID for this pattern instance |
| `slug` | Directory name under `rag_patterns/<engine>/` |
| `display_name` | Human-readable title |
| `engine.type` | `"ai4rag"` \| `"lightrag"` (extensible) |
| `engine.version` | Package or image digest for reproducibility |
| `index` | Abstract index / store descriptor + rebuild pointer |
| `query` | Default recipe file + typed recipe registry |
| `models` | Logical ids for chat / embedding / rerank (org catalog) |
| `lineage` | Parent run, corpus hash, eval hash, upstream artifact pointers |
| `ui` | Tags, try-me prefill, marketing strings |

### 4.2 Mock — ai4rag pattern

```json
{
  "schema": "https://redhat.com/schemas/ai/rag-pattern/v1",
  "pattern_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "slug": "milvus-rrf-bge-m3",
  "display_name": "Finance FAQ — Milvus hybrid RRF",
  "engine": {
    "type": "ai4rag",
    "version": "ai4rag-0.3.8+digest:sha256:deadbeef…",
    "capabilities": ["vector", "hybrid_rrf", "llama_stack_file_search"]
  },
  "index": {
    "kind": "vector_store",
    "provider": "milvus",
    "collection": "finance_faq_v3_milvus_rrf_bge_m3",
    "embedding_model_id": "vllm-embedding/bge-m3",
    "embedding_dim": 1024,
    "rebuild": {
      "type": "kfp_task",
      "template_ref": "rag-pattern-orchestrator/reindex-ai4rag@v1",
      "parameters": {
        "corpus_uri": "${input.corpus_uri}",
        "pattern_slug": "milvus-rrf-bge-m3"
      }
    }
  },
  "query": {
    "default_recipe": "recipe_llama_stack_responses.json",
    "recipes": {
      "recipe_llama_stack_responses.json": {
        "type": "llama_stack_v1_responses",
        "description": "Gen AI Studio / Llama Stack compatible"
      }
    }
  },
  "models": {
    "chat": {
      "id": "vllm-inference-qwen/qwen25-7b-instruct",
      "endpoint_ref": "secretRef/genai/endpoints/qwen"
    },
    "embedding": {
      "id": "vllm-embedding/bge-m3",
      "endpoint_ref": "secretRef/genai/endpoints/bge-m3"
    },
    "rerank": null
  },
  "lineage": {
    "parent_run_id": "run-2026-04-21-8f3a2c",
    "corpus_etag": "s3:…:v3",
    "eval_set_hash": "sha256:…",
    "optimization_run_artifact": "s3://bucket/…/ai4rag/leaderboard.json"
  },
  "ui": {
    "tags": ["finance", "hybrid", "milvus"],
    "try_me": { "prefill_question": "What changed in the fee policy in Q3?" }
  }
}
```

### 4.3 Mock — LightRAG pattern

```json
{
  "schema": "https://redhat.com/schemas/ai/rag-pattern/v1",
  "pattern_id": "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
  "slug": "pg-mix-bge-m3",
  "display_name": "Finance FAQ — LightRAG (PostgreSQL + mix + rerank)",
  "engine": {
    "type": "lightrag",
    "version": "lightrag-hku-1.4.15+digest:sha256:cafebabe…",
    "capabilities": ["knowledge_graph", "dual_level_retrieval", "mix_query_mode", "reranker"]
  },
  "index": {
    "kind": "lightrag_store",
    "storage": {
      "backend": "postgres",
      "namespace": "finance_faq_v3",
      "tables_prefix": "lr_finance_faq_v3_",
      "dsn_ref": "secretRef/rag/lightrag/pg-finance-faq"
    },
    "graph": { "enabled": true, "export_supported": true },
    "rebuild": {
      "type": "kfp_task",
      "template_ref": "rag-pattern-orchestrator/reindex-lightrag@v1",
      "parameters": {
        "corpus_uri": "${input.corpus_uri}",
        "pattern_slug": "pg-mix-bge-m3"
      }
    }
  },
  "query": {
    "default_recipe": "recipe_lightrag_query.json",
    "recipes": {
      "recipe_lightrag_query.json": {
        "type": "lightrag_server_query_v1",
        "description": "Calls LightRAG Server query API (not Llama Stack file_search)"
      }
    },
    "defaults": {
      "mode": "mix",
      "top_k": 10,
      "include_references": true
    }
  },
  "models": {
    "chat": {
      "id": "vllm-inference-qwen/qwen25-7b-instruct",
      "endpoint_ref": "secretRef/genai/endpoints/qwen"
    },
    "embedding": {
      "id": "vllm-embedding/bge-m3",
      "endpoint_ref": "secretRef/genai/endpoints/bge-m3"
    },
    "rerank": {
      "id": "vllm-reranker/bge-reranker-v2-m3",
      "endpoint_ref": "secretRef/genai/endpoints/rerank"
    }
  },
  "serving": {
    "lightrag_server_base_url_ref": "secretRef/rag/lightrag/server-base-url",
    "auth": { "mode": "bearer", "token_ref": "secretRef/rag/lightrag/query-token" }
  },
  "lineage": {
    "parent_run_id": "run-2026-04-21-8f3a2c",
    "corpus_etag": "s3:…:v3",
    "eval_set_hash": "sha256:…",
    "index_job_id": "kfp:task/lightrag-index-xyz"
  },
  "ui": {
    "tags": ["finance", "graph", "lightrag"],
    "try_me": {
      "prefill_question": "Summarize cross-document relationships about fee caps."
    }
  }
}
```

**Implementation note:** LightRAG requires **embedding model and vector dimension** to stay aligned with existing tables. Changing embedding without a controlled migration should produce a **new** `pattern_id` / slug (or explicit `supersedes` lineage), not silent overwrites.

---

## 5. Recipe mocks (different HTTP surfaces)

### 5.1 `recipe_llama_stack_responses.json` (ai4rag / Studio)

Aligned with the Llama Stack `/v1/responses` style described in [deploying_autorag_patterns.md](./deploying_autorag_patterns.md):

```json
{
  "schema": "https://redhat.com/schemas/ai/rag-recipe/llama-stack-v1-responses/v1",
  "body": {
    "model": "vllm-inference-qwen/qwen25-7b-instruct",
    "stream": false,
    "store": true,
    "input": [
      {
        "type": "message",
        "role": "user",
        "content": [{ "type": "input_text", "text": "{{ user_question }}" }]
      }
    ],
    "metadata": {
      "rag_pattern_name": "milvus-rrf-bge-m3",
      "rag_pattern_iteration": "0",
      "vector_datasource_type": "ls_milvus",
      "embedding_model_id": "vllm-embedding/bge-m3"
    },
    "instructions": "Answer using only file_search results. If unknown, say you cannot answer. Match user language.",
    "tools": [
      {
        "type": "file_search",
        "vector_store_ids": ["vs_14e9616f-9d65-40ce-be80-9e04c6657736"],
        "max_num_results": 3,
        "ranking_options": { "ranker": "rrf", "alpha": 0.6, "impact_factor": 2.0 }
      }
    ],
    "tool_choice": { "type": "file_search" },
    "include": ["file_search_call.results"]
  },
  "placeholders": {
    "user_question": { "source": "ui_try_me", "required": true }
  }
}
```

### 5.2 `recipe_lightrag_query.json` (LightRAG — separate contract)

Do **not** pretend this is `file_search` unless a gateway translates it. Mock:

```json
{
  "schema": "https://redhat.com/schemas/ai/rag-recipe/lightrag-server-query/v1",
  "http": {
    "method": "POST",
    "path": "/query",
    "base_url_ref": "secretRef/rag/lightrag/server-base-url",
    "headers": {
      "Authorization": "Bearer ${secretRef:rag/lightrag/query-token}",
      "Content-Type": "application/json"
    }
  },
  "body_template": {
    "query": "{{ user_question }}",
    "mode": "mix",
    "include_references": true,
    "top_k": 10
  },
  "response_mapping": {
    "answer_path": "$.answer",
    "sources_path": "$.references"
  },
  "placeholders": {
    "user_question": { "source": "ui_try_me", "required": true }
  }
}
```

**UI implication:** The “Try me” renderer branches on `recipe.*.type` — one path for Llama Stack JSON, one for LightRAG (or a server-side proxy that normalizes responses for the playground).

---

## 6. `scores.json` (shared leaderboard shape — mock)

```json
{
  "schema": "https://redhat.com/schemas/ai/rag-pattern-scores/v1",
  "primary_metric": "ragas_answer_relevancy",
  "metrics": {
    "ragas_answer_relevancy": 0.84,
    "ragas_context_precision": 0.78,
    "ragas_faithfulness": 0.81,
    "latency_p50_ms": 920,
    "cost_usd_estimate": 1.42
  },
  "eval": {
    "eval_set_hash": "sha256:…",
    "generation_model_id": "vllm-inference-qwen/qwen25-7b-instruct",
    "notes": "Generation model held constant for cross-engine compare."
  },
  "engine": { "type": "lightrag", "version": "lightrag-hku-1.4.15" }
}
```

Swap `engine` and `metrics` for ai4rag rows; keep **metric names** stable for UI sorting.

---

## 7. `eval/eval_report.json` (run-level — mock)

```json
{
  "schema": "https://redhat.com/schemas/ai/rag-eval-report/v1",
  "run_id": "run-2026-04-21-8f3a2c",
  "comparable": true,
  "rows": [
    {
      "engine": "ai4rag",
      "pattern_slug": "milvus-rrf-bge-m3",
      "primary_metric": "ragas_answer_relevancy",
      "value": 0.81,
      "pattern_path": "rag_patterns/ai4rag/milvus-rrf-bge-m3/"
    },
    {
      "engine": "lightrag",
      "pattern_slug": "pg-mix-bge-m3",
      "primary_metric": "ragas_answer_relevancy",
      "value": 0.84,
      "pattern_path": "rag_patterns/lightrag/pg-mix-bge-m3/"
    }
  ],
  "warnings": []
}
```

If generation model or eval subset differed, set `"comparable": false` and document reasons in `warnings`.

---

## 8. KFP orchestration-only DAG (conceptual YAML sketch)

KFP encodes **graph, retries, timeouts, artifact paths, and manifest writing** — not RAG science inside generic nodes:

```yaml
# rag-pattern-orchestrator (conceptual — not a committed pipeline compile artifact)
components:
  validate_inputs:
    outputs: [corpus_uri, eval_uri, engines]
  eval_shared_prep:
    inputs: [eval_uri]
    outputs: [golden_set_manifest]
  branch_ai4rag:
    when: "'ai4rag' in engines"
    graph: ai4rag_optimize_and_emit_pattern
  branch_lightrag:
    when: "'lightrag' in engines"
    graph: lightrag_index_and_emit_pattern
  eval_score_all:
    inputs: [golden_set_manifest, patterns_from_branches]
    outputs: [eval/eval_report.json]
  write_run_manifest:
    inputs: [eval/eval_report.json, pattern_manifests]
    outputs: [run_manifest.json]
```

Each **`emit_pattern`** subgraph should end with a **normalizer** component (small shared image) that:

- Validates JSON against `rag-pattern/v1` (and recipe schemas),
- Writes `rag_patterns/<engine>/<slug>/`,
- Returns structured outputs to KFP for `run_manifest.json`.

---

## 9. Notebooks

Keep **`indexing_notebook.ipynb`** and **`inference_notebook.ipynb`** as **human escape hatches** and support tooling. Suggested shared context (first cell or metadata):

```json
{
  "pattern_uri": "s3://bucket/.../rag_patterns/lightrag/pg-mix-bge-m3/pattern.json",
  "run_id": "run-2026-04-21-8f3a2c"
}
```

---

## 10. Edge cases to encode in the contract

| Case | Behavior |
|------|-----------|
| LightRAG index OK, eval failed | `scores.json` missing or partial; `run_manifest.status` may be `partial` |
| Embedding / schema change | New `pattern_id`; optional `lineage.supersedes` |
| Same logical name from two engines | Allowed — paths differ by `rag_patterns/<engine>/` |
| Studio only supports Llama Stack today | LightRAG “Try me” uses **typed** recipe + curl/proxy; no silent cast to `file_search` |

---

## 11. Schema URIs (placeholder)

The `https://redhat.com/schemas/ai/...` values in mocks are **placeholder** identifiers. Replace with your org’s real schema registry or OpenShift AI documentation URLs when formalizing JSON Schema artifacts.

---

## 12. Summary

| Layer | Role |
|-------|------|
| **KFP** | Orchestration: branches per engine, shared eval, artifact layout, `run_manifest.json` |
| **ai4rag / LightRAG** | Pattern producers: fill `pattern.json`, typed recipes, `scores.json`, notebooks |
| **UI / Studio** | Load `run_manifest.json`, drill into `rag_patterns/<engine>/<slug>/`, render Try me by **recipe type** |

This keeps LightRAG as a **peer** pattern source to ai4rag without forcing LightRAG into ai4rag’s internal optimization search loop.
