# User Needs vs. Ideas — and Missing Solutions on the Market

This document compares **what users are looking for** and **what problems they are solving** to the [current optimization & building ideas](red_hat_openshift_ai_optimization_building_ideas.md), then proposes **missing solutions on the market** as additional feature ideas for Red Hat OpenShift AI.

---

## User needs & problems vs. current ideas

**✓** = well covered by current/recommended ideas; **△** = partially covered; **✗** = gap.

| User need / problem | Current ideas coverage | Notes |
|---------------------|------------------------|--------|
| **RAG: 72% of enterprise RAG fails in year one** — monolithic index, context bleeding, scattered evidence, over-retrieval, stale knowledge | AutoRAG (optimization engine, hybrid retrieval); Graph RAG; multi-modal RAG | △ Ingestion, versioning, and governance are not yet first-class. |
| **RAG: Document lifecycle** — ingestion, versioning, metadata, refresh, access control, audit | — | ✗ No dedicated "governed ingestion" or version-aware RAG in the list. |
| **RAG: Observability & debugging** — where did it fail (query vs retrieval vs LLM), tracing, release gates | Unified RAG + agent evaluation | △ Eval exists; continuous monitoring, drift, and release gates are not explicit. |
| **AutoML: Only automates a narrow slice** — data prep and feature engineering are the real bottleneck (e.g. 50%+ of effort) | AutoML + Gen AI; assistant-based AutoML | ✗ Data prep / feature engineering automation is not in scope. |
| **AutoML: Black box & compliance** — explainability, audit trails, EU AI Act, GDPR | — | ✗ Explainable AutoML / model cards not in the list. |
| **AutoML: Training–serving skew, feature reusability** — feature stores, versioning | — | ✗ Feature store or "features as code" not in the list. |
| **Agents: Production readiness** — security boundaries, state, policy enforcement, audit trails | AutoAgent; agent composer; MCP registry | △ Governance and "why did the agent do that?" observability are partial. |
| **Agents: Drift & continuous eval** — retrieval drift, prompt drift, safety drift, golden sets | Unified evaluation | △ One-time/periodic evals; continuous drift detection and release gates are not explicit. |
| **Cost & latency** — LLM inference cost, latency, right-sizing (e.g. small vs large model) | — | ✗ No dedicated "inference optimization" or "cost vs quality" tuning. |
| **Tooling (MCP)** — which tools exist, are reliable, well-described | AutoMCP; MCP registry + tool health | ✓ Addressed by metadata optimization and registry. |

**Summary of gaps:** Governed RAG (ingestion, versioning, access control); data prep / feature engineering for AutoML; explainable AutoML and compliance; feature store or feature lifecycle; continuous evaluation, drift monitoring, and release gates; LLM inference and cost optimization.

---

## Missing solutions on the market → additional ideas

These ideas address user problems and market gaps that are **not** fully covered by the existing list. They can be used as yet another set of directions for RHOAI.

### 9. Governed RAG: ingestion, versioning, and access control

- **User problem:** ~72% of enterprise RAG implementations fail or underperform; common causes include single "monolithic" index (context bleeding), no document versioning, stale knowledge, and missing access control. Users need policy-driven retrieval, audit trails, and lifecycle management.
- **Market gap:** "Governed RAG" and "VersionRAG"-style version-aware retrieval are discussed (e.g. [Governed RAG](https://www.infiligence.com/post/governed-rag-secure-policy-driven-ai-retrieval-for-enterprises), [VersionRAG](https://arxiv.org/html/2510.08109v1)) but rarely delivered as a single platform capability.
- **Idea:** **Governed RAG** as a first-class track: document classification (e.g. Public / Internal / Confidential), RBAC/ABAC at retrieval time, permission-aware retrieval, optional PII/PHI redaction, immutable audit logs, and **version-aware retrieval** for evolving documents (e.g. APIs, legal, policies). Integrate with AutoRAG so optimization respects governance (e.g. only optimize over authorized content).
- **RHOAI angle:** Extend RAG pipelines with a "governance layer": ingestion pipeline with metadata and versioning, version-aware index (or graph), and retrieval filters that enforce project/connection-level access. Position as "enterprise RAG that doesn't bleed context and stays in compliance."

### 10. Data prep and feature engineering automation (pre-AutoML)

- **User problem:** Data scientists spend 50%+ of time on data prep and feature engineering; AutoML assumes clean, prepared data. Training–serving skew and lack of feature reusability cause production failures.
- **Market gap:** Feature stores (Feast, Tecton, Hopsworks) and "features as code" exist but are often separate from AutoML. Few platforms tightly integrate "automated feature engineering + AutoML + feature serving" in one flow.
- **Idea:** **AutoFeatures** or **data-prep-for-AutoML**: pipelines for data validation (e.g. Great Expectations–style), automated feature generation (e.g. time-series lags, aggregations, domain-specific transforms), and optional **feature store** integration so the same features are used in training and serving. Output: a "model-ready" dataset and feature manifest that feeds into AutoML.
- **RHOAI angle:** Workbench templates or pipelines: "Prepare data for AutoML" (validate → transform → optional feature store write). For time-series + Gen AI, add temporal feature automation. Connects to existing AutoML so users get "data prep → AutoML → leaderboard" in one story.

### 11. Explainable AutoML and compliance-ready model cards

- **User problem:** AutoML is seen as a black box; regulated industries (healthcare, finance) need explainability, audit trails, and compliance documentation (EU AI Act, GDPR Art. 22).
- **Market gap:** Some vendors (e.g. Oracle AutoMLx, iTuring) offer explainable AutoML; open source (SHAP, LIME) is used ad hoc. Few platforms bundle "AutoML + explainability + model card + audit trail" for governance.
- **Idea:** **Explainable AutoML**: built-in SHAP/LIME-style explanations, global and local feature importance, optional counterfactuals, and **model cards** (intended use, limitations, metrics, training data summary). Export artifacts (explanations, model card) for compliance and risk review.
- **RHOAI angle:** Add an "explainability and model card" step to the AutoML pipeline: after leaderboard, generate explanations and a model card for the selected model(s). Store as run artifacts and optionally feed into Model Registry with governance metadata. Differentiator for regulated industries.

### 12. Continuous evaluation, drift detection, and release gates

- **User problem:** RAG and agents degrade in production (retrieval drift, prompt drift, data drift); teams lack "golden sets," continuous evals, and release gates so bad versions don't ship.
- **Market gap:** Langfuse, DeepEval, Statsig, and TruLens support evals and tracing; "continuous eval + drift + release gates" as a single product story is still emerging.
- **Idea:** **Continuous Eval & Release Gates**: define golden sets and quality rubrics (e.g. groundedness, relevance, safety); run evals on a schedule or on every candidate release; **drift detection** (e.g. metric regression vs baseline); **release gates** (e.g. block deploy if quality drops > X%). Works for both RAG and agents.
- **RHOAI angle:** Extend the unified RAG/agent evaluation stack with "continuous" mode: pipeline or cron that runs evals, compares to baseline, and exposes a "gate" (pass/fail) for promotion. Integrate with existing AutoRAG evals and with pipeline run artifacts. Positions RHOAI as "production-grade AI with guardrails."

### 13. LLM inference and cost optimization

- **User problem:** Inference cost and latency are top concerns; GPU utilization is often low; teams need right-sizing (e.g. small model for simple tasks, large for hard ones) and techniques like quantization, batching, caching.
- **Market gap:** vLLM, TensorRT-LLM, and cloud cost tools exist; "optimize for cost vs quality vs latency" as a platform capability (e.g. automatic model selection or routing by task) is underexplored in open source platforms.
- **Idea:** **Inference optimization** (or **AutoInference**): pipelines or runtimes that support quantization, batching, semantic caching, and optional **model routing** (e.g. by query complexity or confidence) to reduce cost while preserving quality. Surface "cost vs accuracy vs latency" tradeoffs in a dashboard or report.
- **RHOAI angle:** Offer "inference tuning" for RAG and agents: recommend or apply quantization/caching for deployed models; optional A/B or routing by model size. Complements AutoRAG (optimize retrieval + generation) and helps users control spend without leaving the platform.

### 14. RAG and agent "health" dashboard (single pane of glass)

- **User problem:** Production RAG/agents involve many components (ingestion, retrieval, reranker, LLM, tools); failures can be in any layer. Users want one place to see health, traces, and regressions.
- **Market gap:** Observability tools (Langfuse, LangSmith, TruLens) provide tracing and evals; few integrate deeply with pipeline platforms and model registries to give "health + artifacts + gates" in one place.
- **Idea:** **RAG/Agent health dashboard**: single view over pipelines and runs — ingestion freshness, retrieval metrics (e.g. precision@k), generation quality (from evals), tool success rate, latency and cost. Drill-down to traces and failed runs. Optional alerts and release gate status.
- **RHOAI angle:** Build on existing pipelines and eval service: aggregate run and eval results into a project-level "AI health" view. Link to workbenches, pipeline runs, and (later) governed RAG and continuous eval. Reduces "where do I look?" for platform users.

---

## Summary: ideas by theme

| Theme | Existing + recommended (1–8) | Missing solutions (9–14) |
|-------|------------------------------|---------------------------|
| **RAG** | AutoRAG, Graph RAG, multi-modal, hybrid retrieval, unified eval | Governed RAG (ingestion, versioning, access); RAG/agent health dashboard |
| **AutoML** | Gen AI + time-series, assistant, React agent + MCP | Data prep/feature automation; explainable AutoML & model cards |
| **Agents & tools** | AutoAgent, agent composer, AutoMCP, MCP registry | Continuous eval & release gates; health dashboard |
| **Platform / ops** | — | Continuous eval, drift, gates; inference/cost optimization; health dashboard |

---

## References (user & market research)

| Topic | Sources |
|-------|--------|
| Enterprise RAG failure modes | [72% RAG failures](https://ragaboutit.com/why-72-of-enterprise-rag-implementations-fail-in-the-first-year-and-how-to-avoid-the-same-fate/), [RAG failure modes](https://www.faktion.com/post/common-failure-modes-of-rag-how-to-fix-them-for-enterprise-use-cases), [RAG at scale](https://www.infoworld.com/article/4108159/how-to-build-rag-at-scale.html) |
| Governed RAG & versioning | [Governed RAG](https://www.infiligence.com/post/governed-rag-secure-policy-driven-ai-retrieval-for-enterprises), [VersionRAG](https://arxiv.org/html/2510.08109v1), [RAG pipeline governance](https://aws.amazon.com/blogs/security/securing-the-rag-ingestion-pipeline-filtering-mechanisms/) |
| AutoML adoption barriers | [Why AutoML failed to live up to the hype](https://delphinaai.substack.com/p/why-automl-failed-to-live-up-to-the), [Limitations of AutoML](https://milvus.io/ai-quick-reference/what-are-the-limitations-of-automl), [Shadow side of AutoML](https://towardsdatascience.com/the-shadow-side-of-automl-when-no-code-tools-hurt-more-than-help/) |
| Data prep & feature engineering | [Feature stores](https://uplatz.com/blog/feature-stores-the-missing-link-in-scalable-mlops-pipelines/), [Features as code](https://tecton.ai/blog/features-as-code), [MLOps data prep](https://www.responsibleaiops.com/post/how-can-mlops-revolutionize-data-preparation) |
| Explainable AutoML | [AutoMLx](https://docs.public.oneportal.content.oci.oraclecloud.com/iaas/tools/automlx/latest/latest/index.html), [iTuring AutoML](https://ituring.ai/ituring-automl/), [Explainable AI enterprise](https://www.trantorinc.com/blog/explainable-ai-enterprise-guide) |
| Agent production & observability | [Governed agentic AI](https://medium.com/@yagmur.sahin/governed-agentic-ai-how-enterprises-can-take-ai-agents-into-production-systems-52003af5031c), [Agentic AI observability](https://www.datarobot.com/blog/agentic-ai-observability/), [Production-ready agentic AI](https://www.datarobot.com/blog/production-ready-agentic-ai-evaluation-monitoring-governance/) |
| RAG/agent drift & continuous eval | [Evaluation-first AI](https://medium.com/@falvarezpinto/evaluation-first-ai-product-engineering-golden-sets-drift-monitoring-and-release-gates-for-llm-2c3bfb3f1e7b), [Managing agent drift](https://dev.to/kuldeep_paul/managing-ai-agent-drift-over-time-a-practical-framework-for-reliability-evals-and-observability-1fk8), [Langfuse RAG evals](https://langfuse.com/blog/2025-10-28-rag-observability-and-evals) |
| LLM inference & cost | [LLM inference optimization](https://seenos.ai/llm-optimization/llm-inference-optimization), [LLM cost optimization](https://calmops.com/ai/llm-cost-optimization-reducing-inference-costs/), [Inference at enterprise scale](https://techcommunity.microsoft.com/blog/appsonazureblog/inference-at-enterprise-scale-why-llm-inference-is-a-capital-allocation-problem/4498754) |
