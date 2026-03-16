# Red Hat OpenShift AI — Optimization & Building: Feature Ideas

Ideas for new features in the area of optimization and building, including existing directions and recommendations based on widely published / used open source communities.

**See also:** [User needs vs. ideas — and missing solutions on the market](user_needs_vs_ideas_and_missing_solutions.md) for a comparison to what users are looking for and additional ideas (governed RAG, data prep for AutoML, explainability, continuous eval, inference optimization, health dashboard).

---

## Existing directions (current list)

| Area | Ideas |
|------|--------|
| **AutoML** | Joining the AutoML with Gen AI for time-series, classification and regression tasks (leaderboard of the mixed types models optimized and evaluated); assistant-based approach for AutoML (e.g. AutoGluon assistant); build and deploy React agent for working with ML model (MCP tool registration as yet another direction). |
| **AutoRAG** | Combining optimization engine with other frameworks available; Agentic RAG; Graph RAG; Multi-modal RAG. |
| **AutoMCP** | Optimization of tools metadata under MCP server (e.g. ask from Ben on Slack channel). |
| **AutoAgent** | Deck from Shila to analyze. |

---

## Recommended additional features (open source / community basis)

### 1. AutoPrompt / prompt optimization pipeline (DSPy-style)

- **Idea:** A pipeline or workbench flow that **automatically optimizes prompts** (and optionally light fine-tuning) for RAG, agents, or custom LLM apps — not just hand-tuned prompts.
- **Why it fits:** [DSPy](https://github.com/stanfordnlp/dspy) and similar (e.g. MIPROv2, BootstrapRS, GEPA) are widely cited; “optimize instructions + few-shot examples” is a standard pattern. Fits “building and optimization” and pairs with AutoRAG (better prompts → better RAG).
- **RHOAI angle:** Run prompt-optimization as a pipeline (or workbench template) with your LLM stack; output optimized prompts/configs as artifacts; optional integration with your RAG optimization engine.

### 2. Unified evaluation and benchmarking for RAG and agents

- **Idea:** A **standardized evaluation stack** for RAG and agents (faithfulness/groundedness, context relevance, answer relevance, tool use, etc.) with pipelines and leaderboards.
- **Why it fits:** [TruLens](https://www.trulens.org/) (RAG triad, agents, OpenTelemetry), [RAGAS](https://github.com/explodinggradients/ragas), and “LLM-as-judge” evals are standard. People need one place to run and compare evals across RAG/agent configs.
- **RHOAI angle:** Reuse/extend your AutoRAG evaluation (e.g. faithfulness, answer_correctness) into a general **eval service**: run evals from pipelines or workbench, store results, and feed them into AutoRAG/AutoAgent leaderboards. Align with TruLens/RAGAS-style metrics and optionally OTel.

### 3. Time-series + Gen AI foundation models in the platform

- **Idea:** Support **time-series forecasting** with open foundation models (e.g. Lag-Llama, TimesFM, Chronos) and optional “agentic” orchestration (e.g. TimeCopilot-style) for model selection and explanation.
- **Why it fits:** [Lag-Llama](https://github.com/time-series-foundation-models/lag-llama), [TimesFM](https://github.com/google-research/timesfm), [TimeCopilot](https://arxiv.org/pdf/2509.00616) are visible in papers and repos. “Time-series + LLM” is a clear extension of “AutoML + Gen AI” for temporal data.
- **RHOAI angle:** Add time-series as a first-class task next to tabular AutoML: pre-packaged runtimes/templates for Lag-Llama/TimesFM (and later TimeCopilot-style orchestration), with leaderboards and evaluation comparable to your current AutoML.

### 4. Agent framework interoperability and “agent composer”

- **Idea:** Support **multiple agent frameworks** (LangGraph, AutoGen, CrewAI, etc.) with a common abstraction: define workflows (state machines, roles, tools), run them on RHOAI, and optionally optimize tool use and prompts.
- **Why it fits:** [LangGraph](https://docs.langchain.com/langgraph-platform/autogen-integration), [AutoGen](https://github.com/microsoft/autogen), [CrewAI](https://github.com/joaomdmoura/crewAI) are widely adopted; comparisons and “which framework” are common. Demand for observability, durability, and human-in-the-loop is high.
- **RHOAI angle:** “Agent composer” or “agent runtime” on RHOAI: choose framework (LangGraph vs AutoGen vs CrewAI), attach MCP/connections, run with your LLMs and observability. Feeds into AutoAgent (e.g. Shila’s deck) and AutoMCP (tools as first-class).

### 5. Graph RAG and knowledge-graph RAG as a first-class path

- **Idea:** **Graph-native RAG**: build and query knowledge graphs (e.g. Neo4j, or graph stores in your stack) for complex, multi-hop QA and combine with your existing RAG optimization.
- **Why it fits:** [LlamaIndex Graph RAG](https://docs.llamaindex.ai/en/stable/examples/cookbooks/GraphRAG_v2/), [Neo4j + LlamaIndex](https://neo4j.com/labs/genai-ecosystem/llamaindex/), and “GraphRAG” are standard in talks and blogs. Complements vector-only RAG.
- **RHOAI angle:** “Graph RAG” track next to “vector RAG”: graph extraction (e.g. triples + optional LLM enrichment), graph store, and query engine. Optimize chunking + graph schema + retrieval strategy in the same way you optimize vector RAG (e.g. in AutoRAG).

### 6. Multi-modal and document-vision RAG

- **Idea:** RAG over **documents as images** (PDFs, scans, figures) without full OCR-first pipelines: vision encoders + retrieval + LLM, with optimization of model and retrieval choices.
- **Why it fits:** [VDocRAG](https://vdocrag.github.io/) (e.g. CVPR 2025), ColPali-based [VisionRAG](https://github.com/grapepicker1016/visionrag), and [Hugging Face multimodal RAG](https://huggingface.co/learn/cookbook/en/multimodal_rag_using_document_retrieval_and_vlms) are visible. “Tables, diagrams, handwriting” is a frequent ask.
- **RHOAI angle:** “Multi-modal RAG” in AutoRAG: support vision-backed retrieval and optional VLM answers; optimize embedding model, chunking (e.g. by page/region), and retrieval strategy. Fits your “multi-modal RAG” item with a concrete implementation path.

### 7. MCP registry, discovery, and “tool health” (beyond metadata optimization)

- **Idea:** Beyond AutoMCP (optimizing tool metadata): **registry of MCP servers/tools**, discovery, versioning, and “tool health” (latency, errors, usage) so agents and pipelines pick reliable tools.
- **Why it fits:** [MCP](https://modelcontextprotocol.io/) has a large ecosystem; [MCP Registry](https://github.com/modelcontextprotocol) and Inspector are reference implementations. Teams need “which tools exist, which are reliable, and how to describe them well.”
- **RHOAI angle:** RHOAI as a place to **register and curate MCP servers** (and their metadata). AutoMCP optimizes metadata; the registry + health gives discovery, governance, and feedback into that optimization (e.g. “these tools are used and stable”).

### 8. Hybrid retrieval and RAG pipeline optimization

- **Idea:** Explicit support for **hybrid retrieval** (vector + keyword + optional graph) and **reranking**, with pipeline tuning (chunking, retrieval, reranking) and evaluation.
- **Why it fits:** Production RAG often uses [hybrid retrieval and reranking](https://latestfromtechguy.com/article/rag-best-practices-2026); [RAG-Stack](https://arxiv.org/pdf/2510.20296)-style “quality + performance” tuning is discussed in papers and blogs.
- **RHOAI angle:** In AutoRAG, add “hybrid retrieval” and “reranker” as tunable components; optimize chunking, retrieval mix, and reranker in one search space. Complements “combining optimization engine with other frameworks.”

---

## Suggested shortlist to prioritize

If you want a small set of “next steps” that are well grounded in open source and fit RHOAI:

1. **AutoPrompt / prompt optimization** (DSPy-style) — builds on existing LLM/RAG usage; clear “optimization” story.
2. **Unified RAG + agent evaluation** — extends current AutoRAG evals and supports AutoAgent; TruLens/RAGAS-style.
3. **Graph RAG** — first-class path alongside vector RAG; LlamaIndex/Neo4j ecosystem.
4. **Multi-modal / document-vision RAG** — VDocRAG/ColPali-style; differentiates from text-only RAG.
5. **MCP registry + tool health** — pairs with AutoMCP (metadata optimization) and supports “build and deploy React agent + MCP.”

---

## References (open source / community)

| Topic | Links |
|-------|--------|
| Agent frameworks | [LangGraph](https://docs.langchain.com/langgraph-platform/autogen-integration), [AutoGen](https://github.com/microsoft/autogen), [CrewAI](https://github.com/joaomdmoura/crewAI) |
| RAG optimization | [RAG best practices](https://latestfromtechguy.com/article/rag-best-practices-2026), [RAG-Stack](https://arxiv.org/pdf/2510.20296), [FlexRAG](https://arxiv.org/pdf/2506.12494) |
| MCP | [Model Context Protocol](https://modelcontextprotocol.io/), [MCP GitHub](https://github.com/modelcontextprotocol) |
| Time-series + Gen AI | [Lag-Llama](https://github.com/time-series-foundation-models/lag-llama), [TimesFM](https://github.com/google-research/timesfm), [TimeCopilot](https://arxiv.org/pdf/2509.00616) |
| Graph RAG | [LlamaIndex GraphRAG v2](https://docs.llamaindex.ai/en/stable/examples/cookbooks/GraphRAG_v2/), [Neo4j LlamaIndex](https://neo4j.com/labs/genai-ecosystem/llamaindex/) |
| Multimodal RAG | [VDocRAG](https://vdocrag.github.io/), [VisionRAG](https://github.com/grapepicker1016/visionrag), [Hugging Face cookbook](https://huggingface.co/learn/cookbook/en/multimodal_rag_using_document_retrieval_and_vlms) |
| Prompt optimization | [DSPy](https://github.com/stanfordnlp/dspy), [dspy.ai](https://dspy.ai) |
| Evaluation | [TruLens](https://www.trulens.org/), [RAGAS](https://github.com/explodinggradients/ragas) |
