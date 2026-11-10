# Playground Optimizer / Recommender

**Proposal:** help users discover the best Playground agent settings automatically, instead of guessing by hand.

![Find better settings — animated overview](ux_mockups/playground_optimize.gif)

Today’s Playground → **Find better settings** → combinations tried and scored → ranked winners vs the old setup → save the best as an agent.

---

## Problem

In OpenShift AI **Playground**, building an agent is a manual loop:

1. Choose model, instructions, creativity, tools / document search, and related settings  
2. Validate by chatting  
3. **Save as agent** when it “feels right”

That process is slow and hard to compare. Users rarely know which knobs matter, cannot systematically try alternatives, and have no shared score for “better.” Non-experts especially get stuck in trial-and-error.

---

## Solution

Add an **Optimize** step (**Find better settings**) next to the existing Playground flow:

1. User describes what the agent should be good at  
2. Practice questions come from auto-generation or a user upload  
3. The optimizer explores combinations of Playground settings  
4. Each candidate is scored; results appear as a simple ranking  
5. User picks a winner, optionally smoke-tests in chat, and saves it as an agent

Chat stays the smoke-test surface. Offline evaluation drives the ranking.

```text
Playground settings  →  Optimizer explores configs  →  Eval Hub scores  →  Ranked results  →  Save agent
         ↑                         │
         └──── next configs recommended from scores ──┘
```

---

## How it works (tech)

### Search space = Playground settings

The optimizer only searches what Playground already exposes (model, system instructions / prompt, creativity/temperature, streaming-related options, RAG, MCP servers & tools, and similar). Under the hood those runs go through the **Responses API** (same path Playground uses to talk to models and tools) — not a separate agent runtime.

### Scoring with Eval Hub

**Eval Hub** is the evaluation backend:

- Runs each candidate config against the practice / eval set  
- Produces the quality score (and related metrics) used on the leaderboard  

### Recommend next from scores

The optimizer is not only a grid of fixed trials. It uses Eval Hub scores for configs tried so far to **recommend what to try next** in the search space (e.g. focus on promising models, prompts, or tool setups; skip poor regions). The leaderboard always includes the user’s current Playground settings as a baseline so lift is visible.

### User-facing outcome

A ranked list of agent configs → **Use this** applies settings back into Playground → **Save as agent**.

---

## UX sketches

Clickable plain-language screens: [`ux_mockups/index.html`](ux_mockups/index.html)
