# AutoMCP — MCP tools optimization

This folder captures **ideas and open-source options for MCP (Model Context Protocol) tools optimization**: better tool descriptions, schema improvement, LLM parameter tuning, and related work. It supports the platform direction **AutoMCP** (optimization of tools metadata under MCP server) and pairs with [MCP registry + tool health](../red_hat_openshift_ai_optimization_building_ideas.md#7-mcp-registry-discovery-and-tool-health-beyond-metadata-optimization).

## Contents

| Document | Description |
|----------|-------------|
| [MCP optimization ideas](mcp_optimization_ideas.md) | Open-source projects and research for tool descriptions, schema optimization, prompt optimization, and inference tuning. |
| [UX/UI mockups](ux_mockups/) | Static HTML mockups exploring possible UX scenarios: connect MCP, tool list, metadata, run optimization, before/after. Open [ux_mockups/index.html](ux_mockups/index.html) in a browser. |
| [POC notebook](notebooks/mcp_tool_optimization_poc.ipynb) | Sample notebook: LLM-based rewrite of MCP tool descriptions and parameter schema; eval with (query, expected tool) for tool selection accuracy. Uses OpenAI-compatible API and open-source patterns. |

## Relationship to platform docs

- **[Optimization & building ideas](../red_hat_openshift_ai_optimization_building_ideas.md)** — AutoMCP is listed under existing directions; MCP registry + tool health is a recommended feature.
- **[User needs vs. ideas](../user_needs_vs_ideas_and_missing_solutions.md)** — Tooling (MCP): “which tools exist, are reliable, well-described” is addressed by AutoMCP and MCP registry.
