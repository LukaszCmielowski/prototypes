# MCP tools optimization — open-source and research

Ideas and open-source projects that can support **MCP (Model Context Protocol) tools optimization**: better descriptions, schema improvement, LLM parameter adjustment, and related work. Use this to inform AutoMCP (optimization of tool metadata) and tool-health/registry efforts.

---

## 1. Tool descriptions and schema optimization

| Project / paper | What it does | Use for MCP |
|-----------------|--------------|-------------|
| **Microsoft Trace** ([github.com/microsoft/Trace](https://github.com/microsoft/Trace)) | End-to-end generative optimization for AI agents. The **Trace-Free+** line (e.g. [Learning to Rewrite Tool Descriptions for Reliable LLM-Agent Tool Use](https://arxiv.org/html/2602.20426)) rewrites **tool descriptions and parameter schemas** so agents use tools more reliably. | Direct fit: improve MCP tool `name` / `description` and `inputSchema` (and parameter descriptions) so the LLM selects and calls tools better. |
| **PARSE** (paper: [arXiv:2510.08623](https://arxiv.org/html/2510.08623)) | **ARCHITECT** optimizes JSON schemas for LLM consumption (clearer fields, types, constraints) while keeping backward compatibility. Focus: entity extraction; the idea applies to any tool schema. | Use the ideas (or reimplement) to refine MCP tools’ `inputSchema` and per-parameter descriptions. No public repo found; concept-only. |
| **PA-Tool** (paper) | Aligns tool schemas with model pretraining (e.g. naming, structure) to reduce “schema misalignment” errors. | Informs how you name and structure MCP tool and parameter names and descriptions. |

---

## 2. Prompt optimization (apply to “how tools are presented”)

| Project | What it does | Use for MCP |
|---------|----------------|-------------|
| **GreaterPrompt** ([psunlpgroup/GreaterPrompt](https://github.com/psunlpgroup/GreaterPrompt)) | Unified prompt optimization (multiple methods, Web UI). Optimizes the text prompt given to the model. | Optimize the **system/user text that describes or lists MCP tools** (e.g. “here are the tools…”) or the instructions that wrap tool results. |
| **PromptPerfect** ([Beagle-AI-automation/promptperfect](https://github.com/Beagle-AI-automation/promptperfect)) | Improves prompts (e.g. “Make it Better”, “Add Chain-of-Thought”). | Same idea: improve the prose that explains when/how to use tools. |
| **promptolution** (paper: [arXiv:2512.02840](https://arxiv.org/html/2512.02840)) | Modular prompt optimization over a dataset with token budgets. | Optimize the “tool-use instructions” or tool-summary prompt under token limits. |

These don’t edit MCP JSON directly but improve the **prompt layer** the model sees around your MCP tools.

---

## 3. DSPy + MCP (tool-usage optimization)

| Resource | What it does | Use for MCP |
|----------|----------------|-------------|
| **DSPy MCP** ([dspy.ai/learn/programming/mcp](https://dspy.ai/learn/programming/mcp), [tutorial](https://dspy.ai/tutorials/mcp/)) | Converts MCP tools to DSPy tools (`dspy.Tool.from_mcp_tool()`), then **compiles** programs (e.g. ReAct) with optimizers (BootstrapFewShot, MIPRO) so the model learns **when and how** to call tools from examples. | Optimize **usage** of existing MCP tools (prompts, few-shot, routing) rather than rewriting tool definitions. Complements description/schema work. |

So: **description/schema** = better tool definitions; **DSPy+MCP** = better use of those definitions.

---

## 4. LLM parameter and inference tuning

| Project | What it does | Use for MCP |
|---------|----------------|-------------|
| **BentoML llm-optimizer** ([bentoml/llm-optimizer](https://github.com/bentoml/llm-optimizer)) | Benchmarks and tunes **inference** (e.g. vLLM, SGLang): batch size, SLO, hardware. | Tune **serving/LLM parameters** for the model that calls MCP tools (throughput, latency), not tool text. |

Use this for “LLM parameters adjustment” at the **inference** side, not for tool descriptions.

---

## 5. MCP-specific and guidance (no automation)

- **context-optimizer-mcp-server** ([malaksedarous/context-optimizer-mcp-server](https://github.com/malaksedarous/context-optimizer-mcp-server)): Reduces context (e.g. file/terminal output) before sending to the model. Helps with **context budget**, not description quality.
- **Writing great tool schemas for MCP** (e.g. [MCP Bundles](https://www.mcpbundles.com/blog/2025/05/06/writing-great-tool-schemas), [Grizzly Peak patterns](https://www.grizzlypeaksoftware.com/library/mcp-tool-creation-patterns-and-best-practices-sgph5f29)): Best practices (one clear sentence, enums, required vs optional, examples). Useful as **target format** for any generator or rewriter.

---

## Summary

- **Better descriptions / schema for MCP tools:** **Microsoft Trace** (and Trace-Free+ style tool-description rewriting) is the main open-source direction; **PARSE/ARCHITECT** and **PA-Tool** are research ideas you can reuse or reimplement for MCP `inputSchema` and descriptions.
- **“Prompt” optimization around tools:** **GreaterPrompt**, **PromptPerfect**, **promptolution** optimize the text the model sees; apply them to the prompt that describes or frames your MCP tools.
- **Tool-use behavior (which tool, when):** **DSPy + MCP** for compile-time optimization of tool-calling behavior.
- **LLM parameters (inference):** **BentoML llm-optimizer** for runtime/inference tuning.

---

## References (representative)

| Topic | Links |
|-------|--------|
| Tool description rewriting | [Microsoft Trace](https://github.com/microsoft/Trace), [Trace-Free+ (arXiv:2602.20426)](https://arxiv.org/html/2602.20426) |
| Schema optimization | [PARSE (arXiv:2510.08623)](https://arxiv.org/html/2510.08623) |
| Prompt optimization | [GreaterPrompt](https://github.com/psunlpgroup/GreaterPrompt), [PromptPerfect](https://github.com/Beagle-AI-automation/promptperfect) |
| DSPy + MCP | [DSPy MCP](https://dspy.ai/learn/programming/mcp), [DSPy MCP tutorial](https://dspy.ai/tutorials/mcp/) |
| Inference tuning | [BentoML llm-optimizer](https://github.com/bentoml/llm-optimizer) |
| MCP protocol and best practices | [Model Context Protocol](https://modelcontextprotocol.io/), [MCP GitHub](https://github.com/modelcontextprotocol) |
