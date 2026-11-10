# Playground Optimizer / Recommender

**One-liner:** stop guessing agent settings — systematically try what Playground already supports, score with Eval Hub, recommend the next tries from those scores, and let users save the winner as an agent.

![Find better settings — animated overview](ux_mockups/playground_optimize.gif)

---

## Why this matters

| Today | With Optimize |
|-------|----------------|
| Manual tweak → chat → “feels right” → save | Describe the goal → ranked configs with scores → save |
| Hard for non-experts; no shared definition of “better” | Comparable quality scores; baseline vs improved always visible |
| Good settings stay tribal knowledge | Repeatable path from Playground → evaluated agent |

**Product fit:** meets users where they already build agents (Playground), instead of sending them to a separate optimization lab. Differentiates Gen AI Studio with a guided “make it better” path that still ends in **Save as agent**.

**Platform fit:** reuses **Responses API** (how Playground runs today) and **Eval Hub** (evaluation), rather than inventing a parallel runtime or scoring stack. Same optimization pattern as **AutoML** and **AutoRAG** (search configs → score → recommend next → leaderboard), applied to Playground agent settings.

---

## Problem

Playground agent creation is a manual loop:

1. Choose model, instructions, creativity, tools / document search, and related settings  
2. Validate by chatting  
3. **Save as agent** when it feels good enough  

Gaps:

- No systematic comparison across settings  
- No shared score for quality  
- High cost of exploration (time, tokens, cognitive load)  
- Non-experts don’t know which knobs matter  

---

## Proposed solution

Add **Find better settings** beside the existing Playground flow:

1. User states what the agent should be good at  
2. Eval data: auto-generated practice questions / Eval Hub collections or user upload 
3. Optimizer explores combinations of **Playground-supported settings**  
4. **Eval Hub** scores each candidate; leaderboard shows ranking (always includes current settings as baseline)  
5. User picks a winner → optional chat smoke-test → **Save as agent**

```text
Playground settings  →  Optimizer proposes configs  →  Eval Hub scores  →  Ranked results  →  Save agent
         ↑                            │
         └──── next configs recommended from scores ─┘
```

Chat remains for quick validation. Batch evaluation drives the ranking.

---

## Technical approach (summary)

| Piece | Role |
|-------|------|
| **Search space** | Only settings Playground already exposes (model, prompt/instructions, temperature/creativity, RAG, MCP/tools, …) |
| **Execution** | **Responses API** — same path Playground uses for model + tools (no separate agent runtime) |
| **Scoring** | **Eval Hub** runs each config on the eval set and returns the quality score used on the leaderboard |
| **Optimization loop** | Not only a fixed grid: use Eval Hub scores so far to **recommend the next** configs (focus on promising regions, skip poor ones) |
| **Output** | Ranked agent configs → apply into Playground → save as agent |

---

## Suggested MVP

**In scope (MVP)**

- Optimize entry from Playground Settings  
- Eval data: use predefined Eval Hub collections/benchmarks (upload examples next)
- Search over core Playground settings via Responses API  
- Eval Hub scoring + leaderboard with baseline  
- Apply winner + Save as agent  
- Simple budget (“quick” limited number of tries)

**Out of scope / later**

- Full AutoRAG-scale search or unrelated pipeline knobs  
- Deep multi-objective cost/latency Pareto UI (show simple proxies first if available)  
- Non-black box optimization (deep agentic optimization)

---

## Success criteria (how we know it worked)

- Users can go from Playground → ranked results → saved agent without leaving Gen AI Studio  
- Leaderboard always shows baseline vs best; lift is understandable to non-experts  
- Scoring is attributable to Eval Hub (not a opaque side path)  
- Runs use Responses API with the same setting surface as Playground  
- Qualitative: PMs/design can walk the UX sketches and get the idea in &lt;2 minutes  

---

## Dependencies & risks

| Item | Note |
|------|------|
| **Eval Hub** | Must support scoring Playground/Responses-style agent configs on an eval set |
| **Responses API** | Must cover the Playground setting surface we put in the search space |
| **Cost / time** | Multi-config eval uses tokens; MVP needs clear budgets and progress UX |
| **Eval data quality** | Weak examples → weak rankings; offer upload + sensible defaults |
| **UX clarity** | Keep language non-technical (“Find better settings”, quality %) |

---

