# DSPy prototype — Mock UI/UX scenarios for end users

This document proposes **user-facing scenarios and mock UI/UX** that could be built on top of the DSPy POC (prompt generation, optimization, leaderboards, export to chat API). It is intended to guide product and design discussions for an eventual UI (e.g. inside Red Hat OpenShift AI).

**Mock screens (HTML):** Open the static mockups in a browser to see how each screen could look, or capture screenshots for docs/presentations.  
→ **[ux_mockups/](ux_mockups/index.html)** — Connection, Task type, Data & metric, Leaderboard, Export, Try it; **Building from blocks:** Pipeline builder (07), ReAct agent (08), ProgramOfThought (09), Compile pipeline (10).

---

## Alignment with DSPy concepts (real use cases)

To keep scenarios and mocks aligned with how DSPy is actually used in tutorials and docs:

| DSPy concept | UX equivalent | Notes |
|--------------|----------------|--------|
| **Signature** | Task type / preset or custom "inputs → outputs" | e.g. `question -> answer`, `context, question -> answer`. Power users may define custom field names. |
| **Program** | Single block (Predict, ChainOfThought) or pipeline from builder | Program has a `forward()` that calls one or more modules. |
| **Compile** | "Run optimization" / "Compile & optimize" | Optimizer (BootstrapFewShot, MIPRO, etc.) runs on **trainset** and produces an optimized program. |
| **Trainset** | Training set (for optimization) | Used by the optimizer to learn prompts/few-shots. DSPy recommends ~20% of data for training (min ~30 examples; 300+ for best results). |
| **Dev set** | Dev / evaluation set | Used to **evaluate** the compiled program (leaderboard, metrics). DSPy recommends ~80% for dev to get stable eval and avoid overfitting. |
| **Metric** | Metric (e.g. exact match, LLM-as-judge) | Function `(example, pred, trace=None) -> score`. Guides optimization; revisit after initial runs. |
| **Optimizer** | Optimizer choice (BootstrapFewShot, MIPRO, etc.) | BootstrapFewShot = few-shot demos; MIPRO = instructions + demos; others for finetuning or comparison. |
| **Save / load** | Save compiled program, Export messages | DSPy: `program.save(path)` (JSON state or full program), `dspy.load(path)`. UI can offer "Save for Python" and "Export chat messages for API". |

**Recommendation:** In the UI, distinguish **training set** (for compile) and **dev set** (for leaderboard/eval). For POC or small data, "use same set" is allowed; for production, support split (e.g. 20% train / 80% dev) and show both counts.

---

## 1. User personas

| Persona | Goal | Key actions |
|--------|------|-------------|
| **ML engineer / data scientist** | Improve prompt quality and reproducibility for a model on RHOAI. | Configure connection, upload/paste eval data, run optimization, compare baseline vs optimized, export prompts. |
| **App developer** | Get a ready-to-use prompt (chat messages) to plug into their app or API. | Pick a task type (QA or RAG), run optimization once, export messages JSON or copy into code. |
| **Evaluator / reviewer** | See how well different prompt configs perform before rollout. | View leaderboards, drill into scores, inspect which examples passed/failed. |

---

## 2. High-level user journeys

1. **Connect & run once** — Set RHOAI endpoint and token → run a simple question → see answer (no optimization).
2. **Optimize and rank** — Provide a small trainset and metric → run baseline + optimized → view leaderboard ranked by score.
3. **RAG flow** — Same as above for context+question→answer; view RAG-specific leaderboard.
4. **Export and reuse** — After optimization, export the winning prompt as chat completion messages (JSON) and optionally call the API from the UI.
5. **Compare and iterate** — Change trainset or metric, re-run, compare new leaderboard with previous run.
6. **Build from blocks** — Compose a pipeline from modules (Retrieve, Predict, ChainOfThought, ReAct, ProgramOfThought, etc.), wire inputs/outputs, then compile and optimize the whole pipeline; view leaderboard and export.
7. **Agent or code-reasoning app** — Add tools (ReAct) or use ProgramOfThought; optimize and rank as above.

---

## 3. Mock UI/UX scenarios (by screen or step)

### 3.1 Connection / project setup

**Purpose:** User configures the RHOAI model endpoint and auth so all later steps use the same model.

| Element | Description |
|---------|-------------|
| **Screen / section** | “Model connection” or “RHOAI setup” |
| **Inputs** | Base URL (e.g. inference URL), optional API base override, Bearer token (masked). Option: pick from existing RHOAI “connections” if the platform supports it. |
| **Actions** | “Save”, “Test connection” (optional: send a minimal request and show success/failure). |
| **UX note** | Support loading from env or .env so notebook users can keep using current flow; UI can prefill from project/default connection. |
---

### 3.2 Signature / task type

**Purpose:** User chooses the **signature** (inputs → outputs) that defines the program. In DSPy this is the declarative spec (e.g. `question -> answer`) used by Predict or ChainOfThought.

| Element | Description |
|---------|-------------|
| **Screen / section** | “Prompt task” or “New optimization” |
| **Options** | **Simple QA** — question → answer (with optional chain-of-thought). **RAG** — context + question → answer (retrieved passages + question). See *Signatures in DSPy docs* below for more. |
| **Actions** | “Continue” → go to data/metric step. |
| **UX note** | Could be a stepper: Connection → Task type → Data & metric → Run → Leaderboard → Export. |

**Signatures in DSPy docs** — The mocks currently emphasize Simple QA and RAG; the [DSPy Signatures](https://dspy.ai/learn/programming/signatures/) and [Modules](https://dspy.ai/learn/programming/modules/) docs include additional task types that could be offered as presets or custom:

| Signature / task type | Inline form (examples) | Notes |
|-----------------------|------------------------|--------|
| **Question answering** | `question -> answer` | Default Simple QA. |
| **RAG** | `context: list[str], question: str -> answer: str` | Retrieved context + question. |
| **Sentiment / classification** | `sentence -> sentiment: bool` or `Literal['positive','negative','neutral']` | Boolean or enum output. |
| **Summarization** | `document -> summary` | Single long input → short summary. |
| **Multiple-choice with reasoning** | `question, choices: list[str] -> reasoning: str, selection: int` | CoT + selection. |
| **Toxicity / binary** | `comment -> toxic: bool` | Optional `instructions` for criteria. |
| **Math** | `question -> answer: float` | Numeric output. |
| **Information extraction** | `text -> title, headings: list[str], entities_and_metadata: list[dict]` | Structured extraction. |
| **Citation / faithfulness** | `context, text -> faithfulness: bool, evidence: dict` | Class-based; evaluator-oriented. |
| **Multi-modal** | `image -> answer` (e.g. `dspy.Image`) | Vision inputs. |
| **Custom** | Any `inputs -> outputs` with types | Power users; custom field names. |

These can be exposed as extra task-type presets in the UI or via a "Custom signature" option that accepts an inline string (e.g. `document -> summary`).

---

### 3.3 Data, metric, and optimizer

**Purpose:** User provides **training set** (for compile) and **dev set** (for evaluation), defines the **metric**, and chooses the **optimizer**. Aligns with DSPy: compile uses trainset; leaderboard uses devset.

| Element | Description |
|---------|-------------|
| **Screen / section** | “Training & dev data”, “Metric”, “Optimizer” |
| **Inputs** | **Training set:** for optimizer (~20% recommended, min ~30). **Dev set:** for leaderboard (~80%). Option: “Use same set” for POC. Fields: QA = `question`, `answer`; RAG = `context`, `question`, `answer`. Upload or paste. Row counts + preview. |
| **Metric** | (example, pred) → score. “Exact match”, “Contains gold answer”, “LLM-as-judge” (future). Refine after initial runs. |
| **Optimizer** | **BootstrapFewShot**, **MIPRO**, etc. Optional: max_bootstrapped_demos, max_labeled_demos. |
| **Actions** | “Validate data”, “Save”, “Next” → Run optimization. |
| **UX note** | Train vs dev matches DSPy; truncate long context in preview. |
---

### 3.4 Run optimization and view leaderboard

**Purpose:** User runs **compile** (optimizer on trainset) and evaluates **baseline** vs **optimized** on the **dev set**. Leaderboard shows dev-set scores.

| Element | Description |
|---------|-------------|
| **Screen / section** | “Run optimization” then “Leaderboard” |
| **Inputs** | Optimizer/settings from previous step. Trainset for compile; devset for scores. |
| **Actions** | “Compile” → “Evaluate on dev set”. Progress: “Compiling…”, “Evaluating baseline…”, “Evaluating optimized…”. |
| **Output** | **Leaderboard:** Rank, Config (Baseline vs Optimized), **Score on dev set**, Description. Sorted by score. |
| **UX note** | Baseline = uncompiled; optimized = compiled. Eval on dev set for stable comparison. “Run again”, “Download CSV”. |

---

### 3.5 Inspect prompt, save program, and export for API

**Purpose:** User inspects the compiled program, **saves it** for Python (DSPy save/load), and/or **exports chat messages** for an API.

| Element | Description |
|---------|-------------|
| **Screen / section** | “Inspect prompt”, “Save program”, “Export for API” |
| **Inspect** | System message, few-shot pairs, final placeholder. Collapsible “Signature”. |
| **Save program** | DSPy-style: save state (JSON) for `program.load(path)` in Python. Option: “Save full program”. **Actions:** “Save as JSON”, “Save full program”. |
| **Export for API** | Chat completion messages (JSON). **Actions:** “Copy JSON”, “Download JSON”, “Try in API” (3.6). Optional: template `{question}`. |
| **UX note** | Two paths: (1) Python save/load; (2) Export messages for API. Aligns with DSPy and POC. |

---

### 3.6 Try it (run a query with exported prompt)

**Purpose:** User types a question (and for RAG, pastes context) and sees the model answer using the selected config (baseline or optimized).

| Element | Description |
|---------|-------------|
| **Screen / section** | “Try it” or “Test prompt” |
| **Inputs** | **Simple QA:** One text field: “Question”. **RAG:** Two fields: “Context” (e.g. retrieved passage), “Question”. Optional: “Use config” dropdown: Baseline vs Optimized. |
| **Actions** | “Get answer”. Optional: “Use in export” — append this example to the exported messages as the final user (and assistant) turn. |
| **Output** | Answer text; optional “Reasoning” (if ChainOfThought). Optional: “View messages sent” (show the exact messages list used for this call). |
| **UX note** | For RAG, “Context” could be populated from a “Retrieve” step in a future version (e.g. call a retrieval API and paste result). |

---

### 3.7 RAG-specific flows

**Purpose:** Same as above but with RAG task type; leaderboard and export are RAG-specific.

| Element | Description |
|---------|-------------|
| **Data** | Table: `context`, `question`, `answer`. User can upload or paste. |
| **Leaderboard** | Same structure as 3.4: “RAG baseline”, “RAG optimized”, ranked by score. Option: separate “RAG leaderboard” tab or section so QA and RAG leaderboards don’t mix. |
| **Export** | Same as 3.5 but messages include context (e.g. system or user message containing context + question). |
| **Try it** | As in 3.6 with Context + Question fields. |

---

## 4. Building AI applications from blocks (and other DSPy scenarios)

DSPy supports **modular programs**: you compose **blocks** (modules) with different signatures and behaviors, then **compile** the whole pipeline so prompts and few-shot examples are optimized end-to-end. Below are scenarios a UI could support beyond single-signature QA/RAG.

### 4.1 DSPy building blocks (module types)

| Block | Role | Typical signature / behavior |
|-------|------|------------------------------|
| **Predict** | Single LM call, no extra structure. | Any `inputs -> outputs` (e.g. `question -> answer`). |
| **ChainOfThought** | Adds step-by-step reasoning before the answer. | Same as Predict but model outputs `reasoning` then `answer`. |
| **ReAct** | Agent loop: reason → optionally call tools → repeat until done. | Inputs + `tools` list; output includes actions and final answer. |
| **ProgramOfThought** | Generate Python code → run it → return answer (or regenerate on error). | e.g. `question -> code`, then `code_output -> answer`. |
| **Retrieve** | Fetch top-k passages from a corpus (needs a retriever / RM configured). | `query -> passages` (no LM; uses retrieval model). |
| **MultiChainComparison** | Generate multiple candidate answers and compare/select. | Multiple chains, then selection. |

**Composition:** A program’s `forward()` calls several modules and passes one block’s outputs as the next block’s inputs (e.g. Retrieve → ChainOfThought).

### 4.2 Scenario: Pipeline builder (visual or form-based)

**Purpose:** User builds an AI app by choosing and connecting blocks instead of writing code.

| Element | Description |
|---------|-------------|
| **Screen / section** | “Pipeline builder” or “Build from blocks” |
| **Palette** | List or grid of blocks: **Retrieve**, **Predict**, **ChainOfThought**, **ReAct**, **ProgramOfThought**, **MultiChainComparison**. Each shows name, short description, and main signature shape (inputs → outputs). |
| **Canvas / flow** | User drags blocks onto a canvas and connects outputs of one block to inputs of the next. Or: form-based “Add step” with dropdown “Step 1: Retrieve (query → passages)”, “Step 2: ChainOfThought (context, question → answer)” and auto-wiring (e.g. “context” = Step 1’s passages). |
| **Signatures** | Per block, user can pick a preset (e.g. “context, question -> answer”) or define custom input/output field names. UI validates that connected ports match (e.g. “passages” → “context”). |
| **Actions** | “Validate pipeline”, “Run on sample input”, “Compile & optimize” (runs teleprompter on the full pipeline). |
| **UX note** | Advanced users might see generated Python (DSPy code); others only see the graph/form. |

### 4.3 Scenario: Full RAG pipeline (Retrieve + Generate)

**Purpose:** End-to-end RAG: user provides a corpus/retriever and question; system retrieves then generates answer. Different from “RAG prompt only” (section 3.7) where context is pre-supplied.

| Element | Description |
|---------|-------------|
| **Blocks** | **Retrieve** (query → passages) → **ChainOfThought** or **Predict** (passages + question → answer). |
| **Config** | User connects to a retriever (e.g. ColBERTv2, FAISS, Chroma, or “RHOAI retrieval API” if available). LM = RHOAI as today. |
| **Data** | Eval set: (question, gold_answer) or (question, gold_context, gold_answer). Metric: answer match and/or context relevance. |
| **Run & leaderboard** | “Run baseline pipeline” vs “Run optimized pipeline” (compile with BootstrapFewShot or similar). Leaderboard: baseline vs optimized, ranked by score. |
| **Export** | Export the **generation** block’s prompt as chat messages (retrieval step is separate; app would call retrieve then inject context into messages). |

### 4.4 Scenario: Agent with tools (ReAct)

**Purpose:** User defines a list of tools (e.g. search, calculator, API call); the model repeatedly reasons and calls tools until it returns a final answer.

| Element | Description |
|---------|-------------|
| **Block** | **ReAct** with signature (e.g. `task -> answer`) and a **tools** list. |
| **UI** | “Tools” section: add tool (name, description, parameters). Optional: register from MCP server or OpenAPI spec. |
| **Config** | Max iterations (e.g. 5–20). Model = RHOAI. |
| **Data & metric** | Eval set: (task, gold_answer). Metric: final answer match or LLM-as-judge. |
| **Run & leaderboard** | Baseline (ReAct with default prompt) vs optimized (compiled ReAct). Leaderboard as before. |
| **Export** | Harder to “export as chat messages” because of the loop; UI could export “ReAct config” (signature + tools + optimized instructions) for use in code or an agent runtime. |

### 4.5 Scenario: Code reasoning (ProgramOfThought)

**Purpose:** Model writes and runs Python code to answer a question (math, data, etc.), with optional retries on error.

| Element | Description |
|---------|-------------|
| **Block** | **ProgramOfThought**: internal steps (generate code → execute → optionally regenerate on error → answer). |
| **Config** | Interpreter (e.g. sandboxed Python), max_iters. Model = RHOAI. |
| **Data & metric** | Eval set: (question, gold_answer). Metric: answer match (and optionally code correctness). |
| **Run & leaderboard** | Baseline vs optimized ProgramOfThought. Leaderboard ranked by score. |
| **UX note** | Safety: code runs in a sandbox; UI may show “generated code” and “execution result” for transparency. |

### 4.6 Scenario: Compile & optimize entire pipeline

**Purpose:** User has built a multi-block pipeline; they want one “Optimize” action that improves prompts (and optionally few-shots) for **all** blocks to maximize the end-to-end metric.

| Element | Description |
|---------|-------------|
| **Screen / section** | “Compile pipeline” or “Optimize full pipeline” |
| **Input** | Pipeline (from builder or code). Trainset with inputs and gold outputs for the **final** block. Metric that evaluates the pipeline’s final output. |
| **Action** | “Compile” runs a DSPy compiler (e.g. BootstrapFewShot, MIPRO) over the **whole** pipeline so every module’s prompts/demos are tuned together. |
| **Output** | Optimized pipeline (saved or exported). Optional: per-block “before/after” prompt diff or leaderboard (baseline pipeline vs optimized pipeline). |
| **UX note** | This is the main differentiator of “building from blocks”: optimization is pipeline-wide, not single-block. |

### 4.7 Summary: blocks vs current POC

| Scenario | Blocks used | In current POC? |
|----------|-------------|------------------|
| Simple QA | Predict or ChainOfThought | Yes (single signature) |
| RAG (context given) | ChainOfThought(context, question → answer) | Yes |
| Full RAG (retrieve + generate) | Retrieve → ChainOfThought | No (no Retrieve block in notebook) |
| Agent with tools | ReAct | No |
| Code reasoning | ProgramOfThought | No |
| Pipeline builder | Any combination | No (conceptual for UI) |
| Compile full pipeline | N/A (compiler over graph) | Partially (we optimize one module) |

---

## 5. Suggested wireframe order (single flow)

1. **Connection** — URL + token (or pick connection).
2. **Task** — QA vs RAG.
3. **Data & metric** — Upload/paste trainset (+ optional eval set), choose metric.
4. **Run** — One button: “Run baseline and optimized”.
5. **Leaderboard** — Table ranked by score; optionally “Inspect” per row.
6. **Inspect & export** — For the top-ranked config: show prompt, “Copy messages JSON”, “Download”.
7. **Try it** — Input question (and context for RAG), “Get answer”, show answer and optional “View messages”.

---

## 6. Out-of-scope for initial mock (backlog)

- **Multiple optimizers** — MIPRO, COPRO, etc.; UI could later offer “Optimizer” dropdown.
- **LLM-as-judge metric** — Configurable judge model and prompt.
- **Versioning / history** — Save runs, name experiments, compare leaderboards across runs.
- **Retrieval integration** — “Retrieve context” button that calls a RAG retrieval API and fills the context field.
- **A/B test** — Deploy baseline vs optimized to two endpoints and compare live traffic (product decision).

---

## 7. Summary table: scenarios → UI elements

| Scenario | Main UI elements |
|----------|-------------------|
| Connect & run once | Connection form, Task = QA, “Try it” only (no trainset). |
| Optimize and rank (QA) | Connection, Task = QA, Data & metric, Run, Leaderboard, Export, Try it. |
| RAG flow | Same with Task = RAG, RAG data (context, question, answer), RAG leaderboard. |
| Export and reuse | Leaderboard → “Inspect & export” for best config → Copy/download messages JSON. |
| Compare and iterate | Change data or metric → Run again → New leaderboard (optional: side-by-side with previous). |
| **Build from blocks** | Palette (Predict, CoT, ReAct, Retrieve, ProgramOfThought, etc.), canvas/form to connect blocks, validate, run sample, compile pipeline. |
| **Full RAG pipeline** | Retrieve block + Generate block, retriever config, eval set (question, answer), pipeline leaderboard, export generation prompt. |
| **Agent with tools** | ReAct block, tools list (or MCP), max_iters, eval set, baseline vs optimized leaderboard, export agent config. |
| **Code reasoning** | ProgramOfThought block, sandbox config, eval set, leaderboard, show generated code & execution. |
| **Compile full pipeline** | Multi-block pipeline from builder, trainset for final output, one “Compile” action, optimized pipeline + optional per-block diff. |

This gives a concrete set of mock UI/UX scenarios that map to the current DSPy POC and to **building AI applications from blocks** (section 4), for wireframes, user testing, or implementation in OpenShift AI.
