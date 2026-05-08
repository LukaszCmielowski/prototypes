create # Deploying the AutoRAG Patterns

## The Big Picture (What we're trying to do)

We want a slick, end-to-end flow: from running RAG experiments in AutoRAG right through to deploying the optimized RAG Pattern. The flow should also support the Gen AI Studio integration for try me out capabilities.

Note that each RAG Pattern consists of:
- **Index building stage** (batch job)
- **Retrieval & generation** (request)

**See also:** [Unified RAG Pattern contract (KFP, ai4rag, LightRAG): envelopes, S3 layout, mock artifacts](./unified_rag_pattern_contract_and_kfp_mocks.md) — versioned `pattern.json`, `run_manifest.json`, typed recipes, and orchestration-only KFP role when multiple engines emit patterns in one run.

## Where we are (current state)

AutoRAG results (optimization outputs) are mostly Data Science Pipelines/KFP artifacts on S3 (like `documents-rag-optimization-pipeline/<run_id>/...`).

Each optimized RAG pattern has its own folder (`rag_patterns/`):
- `pattern.json`: The main config and scores.
- `indexing_notebook.ipynb`: For building/updating the index.
- `inference_notebook.ipynb`: For querying the RAG.
- `v1_responses_body.json`: The specific API request body for the Llama Stack's `/v1/responses` endpoint.

### Example responses JSON body

```json
{
  "model": "vllm-inference-qwen/qwen25-7b-instruct",
  "stream": false,
  "store": true,
  "input": [
    {
      "type": "message",
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "What information is available in the indexed knowledge base?"
        }
      ]
    }
  ],
  "metadata": {
    "rag_pattern_name": "Pattern1",
    "rag_pattern_iteration": "0",
    "vector_datasource_type": "ls_milvus",
    "embedding_model_id": "vllm-embedding/bge-m3"
  },
  "instructions": "Please answer the question I provide in the user question below, using only information found in file_search results. If the question is unanswerable, please say you cannot answer. Respond in the same language as the user question.",
  "tools": [
    {
      "type": "file_search",
      "vector_store_ids": [
        "vs_14e9616f-9d65-40ce-be80-9e04c6657736"
      ],
      "max_num_results": 3,
      "ranking_options": {
        "ranker": "rrf",
        "alpha": 0.6,
        "impact_factor": 2.0
      }
    }
  ],
  "tool_choice": { "type": "file_search" },
  "include": [ "file_search_call.results" ]
}
```

## What's Happening Soon (3.4 Demo)

For quick demos, we're basically doing manual workarounds:
1. Added the vector store created by AutoRAG in the remote milvus instance as an AI Asset in Gen AI Studio.
2. Using custom endpoints, added the embedding model as an AI Asset
3. Using custom endpoints, added the chat model as an AI Asset
4. Add all three to playground

## The short-term vision (3.5)

### Retrieval & generation

**Immediate Goal**: Get the properties from the Llama Stack responses API (`v1/responses`) saved and exposed (RHAIRFE-912, aimed at 3.5).

#### KFP artifact for Storing AutoRAG Responses ("Recipes")

It is already in place for 3.4 but not integrated yet with AutoRAG UI (see Where we are … section). 

The integration scenario:
1. AutoRAG UI reads the responses api assets from the completed AutoRAG 
2. Push those to GenAI Studio as "try me out" parameters (! here we have an integration gap)
3. UI exposes the code snippets for the REST API calls (to be consumed by end user)

---

**TODO** - to make solution portable (another LLS) in addition to requests object:

**Option A: AutoRAG generates config maps**
- Llama-stack config: Eder Ignatowicz to share the exact spec required
  - models (name + url) 
  - vector_store_provider id + details

Example vector store config (mirrors LLS configmap):
```yaml
config:
  uri: http://milvus.milvus.svc.cluster.local:19530
  persistence:
    backend: kv_default
    namespace: vector_io::milvus-provider
  custom_gen_ai:
    credentials:
      secretRefs:
        - name: milvus-api-token
          key: token
```

Full ConfigMap example for reference:
```yaml
kind: ConfigMap
apiVersion: v1
metadata:
  name: gen-ai-aa-vector-stores
  namespace: autorag-playground-testing
data:
  config.yaml: |
    providers:
      vector_io:
      - provider_id: milvus-provider
        provider_type: remote::milvus
        config:
          uri: http://milvus.milvus.svc.cluster.local:19530
          persistence:
            backend: kv_default
            namespace: vector_io::milvus-provider
          custom_gen_ai:
            credentials:
              secretRefs:
                - name: milvus-api-token
                  key: token
    registered_resources:
      vector_stores:
      - provider_id: milvus-provider
        vector_store_id: vs_240aa55e-5f2d-4f94-8586-c9ad8f7a5ab2
        vector_store_name: "AutoRAG vector store"
        embedding_model: ibm-granite/granite-embedding-english-r2
        embedding_dimension: 768
        metadata:
          description: "Collection created from AutoRAG pipeline"
```

**Option B: Gen AI Studio extracts config automatically using llama-stack API**
- AutoRAG provides pointer to the llama-stack instance used (already part of run details)
- Gen AI Studio calls the llama-stack API endpoint to GET the required configuration information (e.g., `/v1/providers/:provider_id`)
- This avoids AutoRAG having to generate config maps for each RAG Pattern
- **Trade-offs**:
  - Pro: Eliminates duplication and manual config map creation
  - Con: Need to materialize/serialize the config in a CR for async "load it later" scenarios (in case the AutoRAG LLS instance doesn't exist anymore)
  - Open question: Should we auto-register the vector db provider in another LLS instance, or keep it as read-only "try me out" on top of the provided LLS instance?

### Index building

#### AutoRAG Indexing Pipeline Generation for Kubeflow Pipelines

AutoRAG is designed to automate the creation of an index-building pipeline for Kubeflow Pipelines (KFP). This generated pipeline is based on the existing AutoRAG Documents Indexing pipeline component graph found in pipelines-components (`pipelines/data_processing/autorag/documents_indexing_pipeline`), which follows the flow: documents_discovery → text_extraction → documents_indexing into Llama Stack vector I/O.

##### Key Features and Benefits

- **Optimized Configuration**: The generated KFP pipeline maintains the original component graph and interfaces. Default parameters and run-time settings (e.g., `embedding_model_id`, `chunking_method`, `chunk_size`, `chunk_overlap`, `distance_metric`, `batch_size`, `collection_name`, `llama_stack_vector_io_provider_id`, `embedding_params`) are automatically set using values from the optimized `pattern.json`.
- **Seamless Pattern Matching**: This automatic configuration ensures the indexing process precisely matches the winning RAG pattern without the need for manual parameter copy-pasting.
- **Artifact Management**: The compiled pipeline (e.g., `pipeline.yaml`) is stored in S3 (or equivalent object storage), versioned, and linked to the specific pattern/run that created it.
- **Deployment and Execution**: Teams can then upload or import this pipeline specification into their Data Science Pipelines / Kubeflow Pipelines server. After attaching necessary secrets (for S3 input data and Llama Stack), they execute the run to build or refresh the vector index. This resulting index is then referenced by the RAG pattern's response body (`v1_responses_body.json` under `file_search / vector_store_ids`).

##### Conceptual Flow

```
pattern.json → Generate KFP Pipeline → Store in S3 → Upload to Pipelines Server → Execute Run
```

The optimized `pattern.json` serves as the input to generate the KFP pipeline (the index building pipeline). This compiled pipeline is then stored in S3. From S3, it is uploaded/imported into the Pipelines Server, where it is then executed as a run.

## The Future Vision (Long-Term / 3.6+)

AutoRAG will support agentic RAG with custom RAG Templates. As a result it will generate agentic app source code / image definition that could be further customized by the end user. The agentic app source ball to be stored under run results reference.

We need to differentiate "try me out" from "production deployment" use cases. The second may require source code customization and hardening; therefore both approaches should co-exist.

The section outlines two primary, simplified paths for deploying an agent within the Kagenti GenAI Studio environment.

### Simplified Agent Deployment Options

#### 1. Fastest Deployment (Using a Pre-built Image)

This is the quickest way to get an agent running without needing to build an image yourself.

**Method A: Kagenti UI Import**
1. In the Kagenti UI, select **Import New Agent**.
2. Choose **Deploy from existing image**.
3. Provide the image reference (e.g., `kagenti/agent-examples`) and optionally any environment variables. For non-main branches, a raw GitHub URL trick can be used for the `.env` file.

**Method B: kubectl Application**
- Apply a Kubernetes Deployment and Service that includes the annotation `kagenti.io/type: agent`. This is demonstrated in the kagenti-operator quick start and allows the AgentCard machinery to automatically pick up the agent.
- No Git cloning or in-cluster image build is required for this path.

#### 2. Simplest Full Platform Flow (Building from Git Source)

This option uses the platform's complete build-and-deploy workflow for an agent written in Python and sourced from a Git repository.

**Prerequisites:**
- The repository must be hosted on GitHub and accessible using the GitHub credentials configured during the Kagenti installation.
- The agent code must reside in a subdirectory of the repository (not the root).
- A Dockerfile must be present at the root of that subdirectory.

**Deployment Steps via UI:**
1. Navigate to **Import New Agent** in the UI.
2. Select the target namespace.
3. Define optional environment variables/.env (supports `valueFrom` for Secrets).
4. Select **Build from source**.
5. Input the Agent Source Repository URL, Git branch or tag, and Source subfolder path.
6. Specify the A2A protocol.
7. Click **Build New Agent**.

**Post-Build Automation:**
Upon a successful build, Kagenti automatically:
- Creates the Deployment and Service using the newly built image.
- Can create an HTTPRoute for external access if enabled.
- Redirects the user to the agent detail page. The Agent Catalog is the recommended place for a quick chat-based smoke test.

### Summary of Source-Based Build and Deploy

The UI's "Build from source" path fully automates the process: it clones the repository from GitHub, builds the image, and then deploys the resulting workload.

**Key Caveats:**
- **GitHub Focus**: The import flow is primarily designed around GitHub (relying on the install-time GitHub authentication), and "any Git URL" is not presented as a first-class option in the guide.
- **Repository Structure**: The agent code must be in a subfolder with its own Dockerfile, not solely in the monorepo root.
- **Branch/Env**: The UI defaults to assumptions around the main branch. A raw GitHub URL workaround is documented for non-standard `.env` paths.
- **Alternative**: The first path (pre-built image) is available as an alternative that skips Git + build entirely.

### Summary

- **Short-term fix**: Create that externalized "agent configuration" format for clean serialization, GenAI Studio integration (no deployment required if based on responses API).
- **Long-term fix (3.5+)**: Create that externalized "agent asset" format for clean serialization, GenAI Studio integration, and deployment (Kagenti, Kubernetes native).
- Long-term vision should be also aligned with agentic starter-kits vision.

## Integration Components and Associated RFEs

| Component | Role | RFE/Context |
|-----------|------|-------------|
| Agent Configuration | Externalized config holding references (e.g., vector store IDs, prompt IDs from MLflow). | RHAIRFE-912 (3.5) |
| MLflow | Logical store for prompts and experimental artifacts. | RHAIRFE-1450 (MLflow integration) |
| AutoRAG (deployment flow) | AutoRAG → Serialization Format → Open in Playground → Deploy Agent. | RHAIRFE-1449 (RAG pattern deployment) |
| Deployment / kagenti | Playground config deployed as executable code ("Agent Deployment"). | RHAIRFE-727 |
