# Playground Optimizer — simple UX mocks

Plain-language mocks for non-technical viewers.

## The idea in one line

**Stop guessing agent settings — press a button, get a ranked list of what works best, save the winner.**

## How to view

```bash
open whats_next/PlaygroundOptimizer/ux_mockups/index.html
```

## Screens (demo order)

| # | File | Say this out loud |
|---|------|-------------------|
| — | `index.html` | Today vs Optimize story |
| 1 | `01_playground_entry.html` | “Here’s the Playground. New button: Find better settings.” |
| 2 | `02_optimize_setup.html` | “What for? Create examples for me. Start.” |
| 3 | `03_running.html` | “We’re trying combinations. Best so far is climbing.” |
| 4 | `04_leaderboard.html` | “Gold / silver / bronze. +21 points vs before.” |
| 5 | `05_apply_save.html` | “Settings filled in. Name it. Save agent.” |

## Language choices (intentional)

| Avoid | Prefer |
|-------|--------|
| Optimize / search space / trials | Find better settings / what we can change / tries |
| SDG / JSONL / holdout | Create examples for me / upload my own |
| Temperature / MCP / RAG | Creativity / extra tools / document search |
| LLM-as-judge / metric | Quality score (%) |
| Config / leaderboard row | Ranked results / Use this |

## Flow

```text
Try & tweak → Find better settings → Waiting → See the winners → Save agent
```
