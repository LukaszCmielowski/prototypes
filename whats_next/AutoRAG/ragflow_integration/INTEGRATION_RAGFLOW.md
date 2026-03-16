# AutoRAG (ai4rag) → RAGFlow integration — detailed design

This document describes **how the AutoRAG pipeline can be integrated with [RAGFlow](https://github.com/infiniflow/ragflow)** so that optimized RAG config (chunking, retrieval, generation) and optionally pre-chunked content are synced to a RAGFlow dataset and used for chat/retrieval.

---

## 1. High-level flow

```
AutoRAG (Kubeflow pipeline)                    RAGFlow
────────────────────────────                  ───────
document-loader        ──┐
text-extraction        ──┼──► artifacts (S3)   ──►  Dataset (create/update)
search-space-prep      ──┤       pattern.json  ──►  parser_config + chunk_method
rag-templates-optim    ──┘       chunks (opt)  ──►  Documents + chunks (Add chunk API)
test-data-loader       ──►  eval Q&A            ──►  Optional: eval in RAGFlow
```

- **Config path:** AutoRAG run produces `pattern.json` (and leaderboard). An integration service reads it and **creates or updates a RAGFlow dataset** with matching `chunk_method` and `parser_config`. Same documents can then be (re-)uploaded in RAGFlow and parsed with that config, or pre-chunked content can be pushed via the **Add chunk** API.
- **Query path:** After sync, users run queries via RAGFlow’s **OpenAI-compatible chat API** (`/api/v1/chats_openai/{chat_id}/chat/completions`) or **agent API**, so the “Try in RAGFlow” UX calls RAGFlow with the chosen chat/agent tied to that dataset.

---

## 2. AutoRAG pipeline outputs (what we have)

From the **documents-rag-optimization-pipeline** (Kubeflow) and the AutoRAG experiment notebook:

| Component | Role | Typical outputs (e.g. S3) |
|-----------|------|----------------------------|
| **document-loader** | Load raw documents | Document list / paths for downstream steps |
| **text-extraction** | Extract text from docs | Extracted text per document |
| **search-space-preparation** | Define search space for optimization | Search space config |
| **rag-templates-optimization** | Run RAG patterns, evaluate | Per-pattern artifacts and leaderboard |
| **test-data-loader** | Load Q&A eval set | Benchmark questions/answers for scoring |

**rag-templates-optimization** writes, per pattern (e.g. `pattern0`, `pattern1`, `pattern2`):

- **`pattern.json`** — Full RAG config for that pattern, e.g.:
  - `chunking`: `method` (e.g. `recursive`), `chunk_size`, `chunk_overlap`
  - `retrieval`: `method` (e.g. `window`), `number_of_chunks`
  - `embeddings`: `model_id`
  - `generation`: `model_id`
- **`evaluation_result.json`** — Scores (e.g. answer_correctness, faithfulness, context_correctness) and optional per-question breakdown; can include `answer_contexts` (retrieved chunk text + `document_id`).
- **`indexing_notebook.ipynb` / `inference_notebook.ipynb`** — Indexing and inference logic (for reference or re-use).

Leaderboard (e.g. HTML artifact) ranks patterns by a chosen metric; the **best pattern** is the one to sync to RAGFlow.

So the integration has:

1. **Config:** `pattern.json` (chunking + retrieval + model ids).
2. **Optional chunk payload:** If the pipeline or a post-step exports **chunk text + document_id** (e.g. from evaluation or a dedicated chunk export), that can be pushed to RAGFlow via the Add chunk API.
3. **Eval set:** test-data-loader / benchmark Q&A can be reused in RAGFlow for evals or “Try in RAGFlow” demos.

---

## 3. RAGFlow concepts (what we target)

- **Dataset** — Knowledge base: has a name, `chunk_method`, `parser_config`, `embedding_model`, and holds documents and chunks.
- **chunk_method** — How RAGFlow parses/chunks documents. Examples: `naive` (General), `qa`, `paper`, `book`, `laws`, `manual`, `one`, etc.
- **parser_config** — Depends on `chunk_method`. For **naive** (most aligned with AutoRAG’s generic chunking):
  - `chunk_token_num` (1–2048; RAGFlow uses tokens, AutoRAG often uses characters — needs a conversion or convention).
  - `delimiter` (e.g. `"\n"`, `"\n!?;。；！？"`).
  - Optional: `layout_recognize`, `raptor`, `graphrag`, etc.
- **Documents** — Files (PDF, DOCX, TXT, etc.) uploaded to a dataset; RAGFlow can parse them with the dataset’s `chunk_method` + `parser_config`, or you can push **pre-chunked** content via the **Add chunk** API (document must exist; then mark as parsed so chunks are searchable).
- **Chat / Agent** — RAGFlow exposes **chats** (tied to a dataset) and **agents**; both support OpenAI-like chat completions. Chat/completion APIs use `chat_id` or `agent_id` and return answers plus optional `reference` (retrieved chunks).

RAGFlow HTTP API (high level):

- **Auth:** `Authorization: Bearer <RAGFLOW_API_KEY>`.
- **Dataset:** `POST /api/v1/datasets` (create), `PUT /api/v1/datasets/{dataset_id}` (update), `GET /api/v1/datasets` (list).
- **Documents:** Upload docs to a dataset (RAGFlow then parses with dataset config); or create a document and then call **Add chunk** to push pre-computed chunks.
- **Chat:** `POST /api/v1/chats_openai/{chat_id}/chat/completions` (stream or non-stream) with `reference: true` to get retrieved chunks in the response.

---

## 4. Mapping: AutoRAG → RAGFlow

| AutoRAG (pattern.json / behavior) | RAGFlow |
|-----------------------------------|--------|
| **chunking.method** (e.g. `recursive`) | **chunk_method**: use `naive` for generic semantic/token-based chunking; RAGFlow does not have a 1:1 “recursive” name — map to `naive` and drive behavior via `parser_config`. |
| **chunking.chunk_size** (e.g. 256 chars) | **parser_config.chunk_token_num**: convert to tokens (e.g. ~chars/4) and clamp to [1, 2048]. Prefer a single convention (e.g. “AutoRAG chunk_size in chars, divide by 4 for RAGFlow tokens”). |
| **chunking.chunk_overlap** | RAGFlow’s naive parser does not expose overlap in the same way; document the limitation or map to the closest RAGFlow option if available in future. |
| **retrieval.number_of_chunks** (e.g. 5) | Not stored on the dataset in the same form; RAGFlow controls retrieval at **chat/agent** level (e.g. top_k in retrieval config). Store in app config or pass when creating/updating the chat so the “Try in RAGFlow” UX uses the same top_k. |
| **embeddings.model_id** | **embedding_model** on dataset: map to RAGFlow’s model name format (e.g. `model_name@model_factory`). If the ID does not exist in RAGFlow, pick a fallback or document supported models. |
| **generation.model_id** | Used when **creating a chat** or agent in RAGFlow (LLM selection). Not part of dataset; sync as “preferred LLM” in integration metadata or in the chat creation step. |
| **Optimized chunk text + document_id** (if exported) | **Add chunk** API: create/ensure document in RAGFlow, then POST chunks for that document so RAGFlow indexes them; set document status so chunks are included in search. |

Summary:

- **Dataset:** Create or update with `chunk_method=naive`, `parser_config.chunk_token_num` (and optionally `delimiter`) from AutoRAG chunking; `embedding_model` from `embeddings.model_id`.
- **Retrieval (top_k):** Apply when creating/updating the chat or agent used for “Try in RAGFlow”, not on the dataset itself.
- **Chunks:** Either (A) user re-uploads same files in RAGFlow and RAGFlow re-parses with the synced config, or (B) integration pushes pre-computed chunks via Add chunk API.

---

## 5. Integration paths

### Path A: Config-only sync (recommended first step)

1. After an AutoRAG run, read the **best pattern** (e.g. from leaderboard or by score).
2. Download that pattern’s **pattern.json** from S3 (or artifact store).
3. **Create or update a RAGFlow dataset:**
   - `POST /api/v1/datasets` with `name` (e.g. `autorag-{run_id}-best`) or reuse existing dataset.
   - Set `chunk_method`: `naive`.
   - Set `parser_config`: `chunk_token_num` from AutoRAG `chunk_size` (with token conversion), `delimiter` if needed.
   - Set `embedding_model` from `embeddings.model_id` (with mapping if required).
4. **Documents:** User uploads the **same** source documents in RAGFlow UI or via document upload API; RAGFlow parses them with the new config.
5. **Chat:** Create or select a RAGFlow chat linked to this dataset; when calling the chat API, use retrieval settings (e.g. top_k = `number_of_chunks`) in the chat config so “Try in RAGFlow” matches AutoRAG behavior.

**Pros:** No custom chunk format; reuses RAGFlow’s parser. **Cons:** User must upload docs in RAGFlow; chunk boundaries may differ slightly (token vs character, delimiter handling).

### Path B: Pre-chunked sync (Add chunk API)

1. AutoRAG (or a post-processing job) exports **chunks** with at least: `document_id` (or doc name), `content` (text), and optionally order/index.
2. In RAGFlow, for each logical document:
   - Create a document in the dataset (or use existing).
   - Call the **Add chunk** API to attach chunks to that document.
   - Ensure the document is marked as parsed so chunks are searchable (see RAGFlow docs / issue #7059 for “add chunk” and parsed status).
3. Dataset config can still be synced from pattern.json (embedding_model, etc.); chunking is then “already done” so RAGFlow does not re-parse the file content.

**Pros:** Chunk boundaries and content are exactly those optimized by AutoRAG. **Cons:** Requires chunk export from AutoRAG and handling of RAGFlow’s Add chunk API and parsed state.

---

## 6. API steps (concrete)

- **Auth:** All requests: `Authorization: Bearer <RAGFLOW_API_KEY>`.
- **Create dataset (config-only):**
  - `POST /api/v1/datasets`
  - Body: `name`, `chunk_method`: `"naive"`, `parser_config`: `{ "chunk_token_num": <from AutoRAG>, "delimiter": "\n" }`, `embedding_model`: `"<model>@<factory>"`.
- **Update dataset (e.g. after new best pattern):**
  - `PUT /api/v1/datasets/{dataset_id}`
  - Body: same `chunk_method` and `parser_config` (and optionally `embedding_model` if no chunks yet).
- **List datasets:** `GET /api/v1/datasets` to show “Target project” in the UI and to resolve `dataset_id` for deploy.
- **Upload documents:** Use RAGFlow’s document upload for the dataset (path depends on RAGFlow version; see [RAGFlow HTTP API](https://ragflow.io/docs/http_api_reference)).
- **Chat (try query):** `POST /api/v1/chats_openai/{chat_id}/chat/completions` with `messages` and optional `extra_body.reference: true` to get citations; `chat_id` is the one bound to the synced dataset.

---

## 7. UI/UX (from mocks)

- **Connect backend:** User selects RAGFlow and sets URL + API key; “Test connection” and optional “Project/dataset” selector (from `GET /api/v1/datasets`).
- **Pipeline → backend:** Diagram shows AutoRAG components → RAGFlow; table summarizes “Optimized chunks/config” → “RAGFlow dataset + parser_config”; “Eval Q&A” → “Optional RAGFlow eval”.
- **Run & compare:** User runs the pipeline; results table shows runs and scores; “Try query in RAGFlow” sends the question to `chats_openai/{chat_id}/chat/completions` with the selected dataset/chat.
- **Deploy:** User picks an AutoRAG run (best or chosen pattern); “Deploy to RAGFlow” creates/updates the dataset (Path A) and optionally triggers document upload or chunk push (Path B); “Export for LightRAG/OpenRAG” remains for other backends.

---

## 8. References

- [RAGFlow HTTP API](https://ragflow.io/docs/http_api_reference) — datasets, parser_config, chat completions.
- [RAGFlow Python API](https://ragflow.io/docs/python_api_reference) — e.g. `create_dataset()`, document upload.
- [Configure dataset (RAGFlow)](https://ragflow.io/docs/configure_knowledge_base) — chunk methods and parser_config.
- RAGFlow issue [#7059](https://github.com/infiniflow/ragflow/issues/7059) — Add chunk usage; [#10097](https://github.com/infiniflow/ragflow/issues/10097) — chunks endpoint pagination limit.
- AutoRAG experiment notebook: pipeline components, S3 artifact layout, `pattern.json` and `evaluation_result.json` schema.
