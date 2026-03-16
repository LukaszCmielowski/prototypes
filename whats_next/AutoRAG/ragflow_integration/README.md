# AutoRAG + open-source RAG backends — UI/UX mocks

Static HTML mockups for **integrating AutoRAG with popular open-source RAG engines**: [RAGFlow](https://github.com/infiniflow/ragflow), [LightRAG](https://github.com/HKUDS/LightRAG), and [OpenRAG](https://github.com/langflow-ai/openrag). The flow is: connect a backend → see how the AutoRAG pipeline maps to it → run optimization → try queries in the backend → deploy or export the best config → **open the result in the RAGFlow UI and customize further**.

## Why integrate?

- **AutoRAG** (Red Hat OpenShift AI): optimizes document loading, text extraction, chunking, and RAG templates via pipelines (e.g. Kubeflow); produces optimized chunks and retrieval/generation config.
- **RAGFlow / LightRAG / OpenRAG**: production RAG engines with large communities. Users can run AutoRAG once, then **sync or export** the best setup into the engine they already use.

## Screens

| Screen | File | Description |
|--------|------|-------------|
| Overview | [index.html](index.html) | Intro and links to Connect, Pipeline mapping, Run & compare, Deploy, Open in RAGFlow. |
| Connect backend | [01_connect_backend.html](01_connect_backend.html) | Choose RAGFlow, LightRAG, or OpenRAG; URL + API key; optional project/dataset. |
| Pipeline → backend | [02_pipeline_to_backend.html](02_pipeline_to_backend.html) | How AutoRAG components (document-loader → … → rag-templates-optimization) map to the backend; mapping table. |
| Run & compare | [03_run_compare.html](03_run_compare.html) | Run AutoRAG pipeline; results table (runs, chunk strategy, score); "Try query in backend" (e.g. RAGFlow). |
| Deploy | [04_deploy.html](04_deploy.html) | Select run; deploy to RAGFlow (project, overwrite option) or export for LightRAG / OpenRAG; "Open in RAGFlow UI" link. |
| Open in RAGFlow | [05_open_in_ragflow.html](05_open_in_ragflow.html) | Open the synced dataset in RAGFlow UI; mock of RAGFlow with "From AutoRAG" dataset and customization (chunk method, parser config, embedding model, documents, retrieval). |
| Edit flow (nodes) | [06_edit_flow_in_ragflow.html](06_edit_flow_in_ragflow.html) | RAGFlow node-based flow editor: palette of nodes, canvas with ingestion (Document → Parser → Chunker → Embedding → Vector store) and retrieval (Query → Retrieval → LLM → Response); nodes from AutoRAG highlighted; properties panel to edit selected node. |

## Detailed integration: AutoRAG → RAGFlow

See **[INTEGRATION_RAGFLOW.md](INTEGRATION_RAGFLOW.md)** for:

- AutoRAG pipeline outputs (pattern.json, chunking/retrieval/generation settings, artifacts).
- RAGFlow concepts (dataset, chunk_method, parser_config, documents, Add chunk API, chat API).
- Mapping: AutoRAG chunk_size/chunk_method → RAGFlow parser_config and embedding_model; retrieval number_of_chunks → chat/retrieval config.
- Two paths: **config-only sync** (create/update RAGFlow dataset; user uploads same docs in RAGFlow) and **pre-chunked sync** (push chunks via Add chunk API).
- Concrete API steps (create/update dataset, list datasets, chat completions).

## Integration ideas per backend

- **RAGFlow:** Sync optimized chunks + retrieval/generation config to a RAGFlow dataset via API; run test queries via RAGFlow chat/agent API. See INTEGRATION_RAGFLOW.md.
- **LightRAG:** Export chunk/parsing config and document corpus so users can run LightRAG ingest locally or in their stack; optional API if LightRAG exposes one.
- **OpenRAG:** Export Langflow/Opensearch-compatible config (YAML or API) so the optimized pipeline can be loaded into OpenRAG.

## How to view

Open any HTML file in a browser (e.g. `index.html`). No build step. For design reference and screenshots only.

Part of Red Hat OpenShift AI / AutoRAG prototypes.
