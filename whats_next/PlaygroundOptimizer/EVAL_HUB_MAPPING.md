# Eval Hub reference note

Supporting detail for the [product story](README.md), reviewed **2026-11-10**. This was an upstream source review; no live deployment or benchmark runs were checked.

Snapshots: [Eval Hub server `d67e9c7`](https://github.com/eval-hub/eval-hub/tree/d67e9c7d9fbe7d1afac380ee488a5e753e07943f) and [community adapters `879914d`](https://github.com/eval-hub/eval-hub-contrib/tree/879914de8c1ffa7cb38399d1d77540ad309045e5).

## Reuse map

These are proposed mappings, subject to verifying the deployed runtime. Collections bundle benchmarks and scoring policies; they do not supply examples for an arbitrary user task.

| Goal | Existing collection / provider | Reuse boundary |
|------|--------------------------------|----------------|
| Follow instructions | [`instruction-following-v1`](https://github.com/eval-hub/eval-hub/blob/d67e9c7d9fbe7d1afac380ee488a5e753e07943f/config/collections/instruction-following-v1.yaml): Harness `ifeval` | Good starter candidate. Strict instruction-level accuracy; verify chat-template and candidate-setting support |
| Follow compound constraints / return JSON | [`instruction-output-v1`](https://github.com/eval-hub/eval-hub/blob/d67e9c7d9fbe7d1afac380ee488a5e753e07943f/config/collections/instruction-output-v1.yaml): IFBench, JSONSchemaBench Easy, FollowBench | Tests unconstrained output. Valid JSON does not establish correct values; some benchmark parameters fix temperature |
| Construct function calls | [`tool-use-v1`](https://github.com/eval-hub/eval-hub/blob/d67e9c7d9fbe7d1afac380ee488a5e753e07943f/config/collections/tool-use-v1.yaml): two Inspect `inspect/bfcl` category selections | Call construction and relevance/no-call decisions; excludes tool execution and multi-turn workflows |
| Understand long documents | [`document-understanding-v1`](https://github.com/eval-hub/eval-hub/blob/d67e9c7d9fbe7d1afac380ee488a5e753e07943f/config/collections/document-understanding-v1.yaml): six RULER tasks | Model screening; does not evaluate the user's retrieval pipeline, citations, or faithfulness |
| Answer from retrieved documents | [`ragas` / `ragas_rag_default`](https://github.com/eval-hub/eval-hub/blob/d67e9c7d9fbe7d1afac380ee488a5e753e07943f/config/providers/ragas.yaml) | Closest task-specific fit. Default metrics: faithfulness, answer relevancy, context precision/recall; primary score is faithfulness |
| Compare answers with references / evaluate conversations | [DeepEval adapter](https://github.com/eval-hub/eval-hub-contrib/blob/879914de8c1ffa7cb38399d1d77540ad309045e5/adapters/deepeval/README.md) | Reuses correctness, grounding, summarization, and conversation scoring; requires completed outputs and metric-specific fields. Resolve registry mismatch below |
| Reason over difficult questions | [`knowledge-reasoning-v1`](https://github.com/eval-hub/eval-hub/blob/d67e9c7d9fbe7d1afac380ee488a5e753e07943f/config/collections/knowledge-reasoning-v1.yaml): GPQA Diamond, HLE, MATH-500 | Closed-book model screening; does not validate a custom domain assistant |
| Check selected trustworthiness dimensions | [`trustworthiness-v1`](https://github.com/eval-hub/eval-hub/blob/d67e9c7d9fbe7d1afac380ee488a5e753e07943f/config/collections/trustworthiness-v1.yaml): CyberSecEval prompt injection + TruthfulQA MC1 | Supplemental diagnostics; not comprehensive agent safety coverage |

The [collection catalog](https://eval-hub.github.io/collections/catalog/) also covers coding, multimodal, and general model suites. For a quick Playground comparison, prefer the smallest relevant task over a broad model leaderboard suite.

## Integration contract

**Recommended design:** Playground executes each candidate through Responses API; Eval Hub scores its captured outputs. Direct benchmark calls to a model endpoint are also possible, but must preserve the candidate configuration and benchmark protocol. Completion API compatibility alone does not establish Responses API or full agent support.

For RAGAS, capture `user_input`, `response`, `retrieved_contexts`, and references where required. The [adapter contract](https://github.com/eval-hub/eval-hub-contrib/blob/879914de8c1ffa7cb38399d1d77540ad309045e5/adapters/ragas/README.md) supports column mapping, a separate judge, and an embedding connection. Default-suite metrics need embeddings; a chat-only endpoint is insufficient. Keep measuring models fixed across candidates and pair grounding with a relevance requirement.

Do not assume a universal recorded-output flag. The [custom-data guide](https://eval-hub.github.io/guides/custom-data/) limits tested `pre_recorded_data` support to IBM CLEAR, while the inspected [RAGAS implementation](https://github.com/eval-hub/eval-hub-contrib/blob/879914de8c1ffa7cb38399d1d77540ad309045e5/adapters/ragas/main.py) and [DeepEval implementation](https://github.com/eval-hub/eval-hub-contrib/blob/879914de8c1ffa7cb38399d1d77540ad309045e5/adapters/deepeval/main.py) consume completed output records. Verify the deployed data-staging contract before promising reuse.

## Findings to resolve before implementation

- **Catalog drift:** the website catalog reports an October 17 sync and includes LongBench v2 in Document Understanding; the reviewed server definition contains six RULER tasks. Discover installed collections rather than hard-coding website contents.
- **DeepEval mismatch:** the [server definition](https://github.com/eval-hub/eval-hub/blob/d67e9c7d9fbe7d1afac380ee488a5e753e07943f/config/providers/deepeval.yaml) declares five prefixed IDs such as `deepeval-correctness`; the [community provider](https://github.com/eval-hub/eval-hub-contrib/blob/879914de8c1ffa7cb38399d1d77540ad309045e5/adapters/deepeval/provider.yaml) and implementation use unprefixed IDs plus conversation benchmarks. Align registry and adapter image; do not assume aliases.
- **Score interpretation:** verify emitted metric keys, units, direction, and completed sample counts. A collection aggregate can hide weaker dimensions; incomplete results must not win. Public diagnostic thresholds are not acceptance criteria for the user's task.

Discover providers and collections through the [server API](https://github.com/eval-hub/eval-hub/blob/d67e9c7d9fbe7d1afac380ee488a5e753e07943f/docs/src/openapi.yaml):

```text
GET /api/v1/evaluations/providers
GET /api/v1/evaluations/providers/{id}
GET /api/v1/evaluations/collections?scope=system
GET /api/v1/evaluations/collections/{id}
```

**First proof:** baseline + one alternative on a small document-QA dataset, executed through Playground and scored through RAGAS. Verify that settings survive execution and save, scores come from actual captured answers, and results remain comparable. Then add bounded search, fresh confirmation examples, and the instruction-following starter.
