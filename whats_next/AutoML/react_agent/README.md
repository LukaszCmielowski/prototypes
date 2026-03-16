# AutoGluon ReAct agent (UI/UX mocks)

Mock UI for a **ReAct-style agent** that uses **AutoGluon models as predictor tools**: **select model(s)** from experiments → **configure** LLM and predictor tools → **chat**. Optional: Tools (MCP) and Run & trace.

## What it showcases

- **Select model:** Choose one or more AutoGluon model(s) from experiments; each becomes a predictor tool (e.g. predict_demand, predict_churn) in the next step.
- **Agent config:** LLM connection (endpoint, model) for reasoning and tool selection; **predictor tools table** (tool name, description, model/experiment); max reasoning steps; Back + Start chat.
- **Chat:** Conversation with the agent; it calls predictor tools when needed. Link to “View trace” for ReAct steps.
- **Tools (MCP):** Registered tools (predict_demand, predict_churn, get_leaderboard) with descriptions and input schema; AutoMCP option.
- **Run & trace:** ReAct trace (thought → action → observation); final answer. Linked from Chat.

## Screens

| Screen        | File                         | Description |
|---------------|------------------------------|-------------|
| Overview      | [index.html](index.html)     | Intro and links to all screens. |
| Select model  | [01_select_model.html](01_select_model.html) | Pick AutoGluon model(s) from experiments. |
| Agent config  | [02_agent_config.html](02_agent_config.html) | LLM connection, predictor tools table, max steps, Start chat. |
| Chat          | [03_chat.html](03_chat.html) | Ask questions; agent calls tools; View trace. |
| Tools (MCP)   | [04_tools_mcp.html](04_tools_mcp.html) | Tool list, descriptions, input schema; AutoMCP. |
| Run & trace   | [05_run_trace.html](05_run_trace.html) | Thought → tool → observation; final answer. |

## How to view

Open any HTML file in a browser (e.g. `index.html`). No build step. For design reference only.

## Context

- **ReAct:** Reasoning + Acting — the agent alternates “thought” and “action” (tool call), then receives an “observation” and continues until it can answer.
- **Predictor tools:** Each selected AutoGluon model is exposed as a named tool (e.g. predict_churn); the agent chooses which tool to call based on the user’s question.
- **MCP:** Model Context Protocol standardizes tool discovery and invocation; optional AutoMCP to improve tool metadata for agent selection.

Part of Red Hat OpenShift AI / AutoML. Aligns with roadmap item **ReAct agent + MCP for ML models**.
