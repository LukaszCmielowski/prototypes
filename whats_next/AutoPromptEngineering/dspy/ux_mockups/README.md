# Mock UI screens — DSPy prompt optimization

Static HTML mockups of how the UX could look. Use them for design reference or to **capture screenshots**.

## How to view

1. Open **`index.html`** in a browser (double-click or `open index.html`).
2. Use the sidebar or the grid to open each screen.
3. To capture screenshots: use your OS screenshot tool or browser DevTools (e.g. responsive mode) and save each screen.

## Screens

### Prompt optimization

| File | Screen |
|------|--------|
| `01_connection.html` | Model connection (RHOAI URL + token) |
| `02_task_type.html` | Task type (Simple QA, RAG, Summarization, Sentiment, Custom signature) |
| `03_data_metric.html` | Training data table + metric choice |
| `04_leaderboard.html` | Leaderboard (baseline vs optimized, ranked by score) |
| `05_export.html` | Inspect prompt + export chat messages JSON |
| `06_try_it.html` | Try it (question → answer) |

### Building from blocks

| File | Screen |
|------|--------|
| `07_pipeline_builder.html` | Pipeline builder — block palette + canvas (e.g. Retrieve → ChainOfThought) |
| `08_react_agent.html` | ReAct agent — tools list, max_iters, eval set |
| `09_program_of_thought.html` | ProgramOfThought — interpreter, max retries, generated code / result |
| `10_compile_pipeline.html` | Compile pipeline — optimize full pipeline, pipeline leaderboard |

Scenarios are described in [../UX_SCENARIOS.md](../UX_SCENARIOS.md) (sections 3 and 4).
