# AutoRAG → OpenRAG integration — mocked UX

Use **AutoRAG (ai4rag)** to find **optimal settings for OpenRAG pipeline steps**: embedding model, language model, chunk size/overlap, and retrieval (top_k, similarity threshold). The mocked experience shows connect → map steps → run optimization → recommended settings → apply to OpenRAG.

## Integration approach

- **OpenRAG** ([langflow-ai/openrag](https://github.com/langflow-ai/openrag)): Langflow + Docling + Opensearch — a fixed pipeline (parse → chunk → embed → index → retrieve → LLM).
- **AutoRAG**: Runs many RAG configs (different embeddings, LLMs, chunk/retrieval params) and scores them on your eval set.
- **Integration**: Map each **OpenRAG step** to an **AutoRAG search dimension**. AutoRAG searches over those dimensions; the winning combination is a valid OpenRAG config that you **apply** (push to OpenRAG or export as YAML).

Optimized dimensions:

- **Embedding model** — which model for the embed step in OpenRAG.
- **Language model** — which LLM for generation.
- **Chunk size / overlap** — chunking step (post-Docling).
- **Retrieval** — top_k, similarity threshold for the retrieval step.

## Screens

| Screen | File | Description |
|--------|------|-------------|
| Overview | [index.html](index.html) | Integration approach; flow links. |
| Connect OpenRAG | [01_connect_openrag.html](01_connect_openrag.html) | OpenRAG/Langflow URL, API key, Opensearch URL; select pipeline to optimize for. |
| Map steps | [02_map_steps.html](02_map_steps.html) | Table: OpenRAG step ↔ AutoRAG dimension (embedding, LLM, chunk, retrieval); include/exclude toggles. |
| Run optimization | [03_run_optimization.html](03_run_optimization.html) | Search space summary; "Run optimization"; link to recommended settings. |
| Recommended settings | [04_recommended_settings.html](04_recommended_settings.html) | Leaderboard of OpenRAG-compatible configs (embedding, LLM, chunk, retrieval, score); "Apply best to OpenRAG". |
| Apply to OpenRAG | [05_apply_to_openrag.html](05_apply_to_openrag.html) | Config to apply; target OpenRAG; "Apply to OpenRAG", "Export as YAML", optional re-index; download OpenRAG-compatible YAML. |

## How to view

Open any HTML file in a browser (e.g. `index.html`). No build step. For design reference only.

Part of Red Hat OpenShift AI / AutoRAG prototypes.
