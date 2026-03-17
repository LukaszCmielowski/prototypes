# AutoMCP — UX/UI mockups

Static HTML mockups that explore **possible UX scenarios** for **AutoMCP**: connecting to MCP servers, listing tools, viewing/editing tool metadata, running optimization (descriptions and schema), and comparing before/after.

## Scenarios

| Screen | File | Description |
|--------|------|-------------|
| Overview | [index.html](index.html) | Intro and flow: Connect → Tool list → Metadata → Optimize → Before/after. |
| Connect MCP | [01_connect_mcp.html](01_connect_mcp.html) | Connect to MCP server (URL, auth); list discovered tools. |
| Tool list | [02_tool_list.html](02_tool_list.html) | All tools with name, description, optional health/usage; select for optimization. |
| Tool metadata | [03_tool_metadata.html](03_tool_metadata.html) | View or edit one tool: name, description, inputSchema (JSON). |
| Run optimization | [04_optimize.html](04_optimize.html) | Run AutoMCP: choose scope (descriptions, schema), select tools, trigger run. |
| Before / after | [05_before_after.html](05_before_after.html) | Compare original vs optimized tool metadata (description and schema). |

## How to view

Open [index.html](index.html) in a browser. No build step. For design reference only.

## Context

- **AutoMCP** = optimization of tool metadata under MCP server (descriptions, parameter schema) so agents select and use tools more reliably.
- See [../mcp_optimization_ideas.md](../mcp_optimization_ideas.md) for open-source and research backing (Trace-Free+, PARSE, DSPy+MCP, etc.).
