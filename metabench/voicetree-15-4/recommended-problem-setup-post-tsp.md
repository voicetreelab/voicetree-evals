---
color: green
isContextNode: false
agent_name: Max
---
# Recommended setup: NL-wrapped coupled job shop with economic stop scoring

Recommended one main benchmark family that fits the graph constraints: procedurally generated coupled two-factory job-shop instances with exact offline gold, a natural-language surface, visible wall-clock budgeting, and a single canonical objective-optimizing prompt.

## Recommended problem setup
Use procedurally generated **coupled two-factory job-shop** instances as the main benchmark family.

## Why this best fits the graph
- It keeps the strongest part of the budget-metagame idea: agents can improve a baseline answer progressively, and stopping early or late is economically meaningful.
- It avoids the main TSP failure mode: there is no single memorized NN+2-opt-style recipe that frontier models can reliably recall and execute.
- It exposes the metacognitive signals the graph cares about: upfront uncertainty, decomposition choice, per-subtask effort prediction, intermediate self-checking, and stop-decision quality.
- It stays fully automatable: generate from seed, compute exact gold offline with OR-Tools, verify any proposed schedule mechanically.
- It can be rendered in natural language, which helps avoid turning the task into 'just emit a solver template.'

## Concrete MVP
- Problem family: two coupled factories where each job's work in Factory B depends on completion times from Factory A.
- Difficulty tier: `4x5` for MVP, `5x6` for frontier tier.
- Generation: deterministic seeded generator producing `(problem_data, gold_answer, verify_fn)`.
- Surface form: natural-language renderer for benchmark use, math renderer retained for debugging and paired analysis.
- Baseline: ship a trivial feasible schedule in the prompt so there is always a scoreable fallback answer.
- Turn 1: planning only — atomic prediction, declared gap, continue/stop, next subtask.
- Turn N>=2: execute one subtask, emit updated best schedule, confidence, continue/stop, and next subtask.
- Budget primitive: wall-clock time, not thinking-token cost.
- Primary leaderboard mode: one canonical objective-optimizing prompt.
- Counterfactual arms: forced-atomic / forced-decomposed / free-choice only as diagnostics or ablations, not the core benchmark definition.

## Safeguards required by the graph
- Never rely on hand-computed gold. Exact solver-backed gold is mandatory.
- Add mild NL wrapping, distractors, or ambiguity-with-resolution so the task measures interpretation plus planning, not just formal scheduling memory.
- Do not let the benchmark's main signal depend on hidden thinking-token accounting.
- Keep coding-resistant classes such as compression or infeasibility as separate companion benchmarks if needed. They solve a different problem: coding resistance, not progressive improvement under a stop decision.

## Bottom line
If the goal is one problem setup that best satisfies the graph's accumulated constraints and lets answers improve with more time and effort, the cleanest answer is: **NL-wrapped coupled job shop with exact offline gold and wall-clock-budgeted stop scoring.**

### NOTES

- Compression-gap and working-memory classes remain valuable, but they fit better as companion benchmarks than as the single main benchmark requested here.
- This recommendation preserves the economic-stop idea while dropping the unnecessary multi-arm complexity as the primary benchmark structure.
- Natural-language wrapping is important because otherwise even a good problem class drifts back toward formal-solver imitation.

## Related

- [benchmark-class-bench-summary](benchmark-class-bench-summary.md)
- [compression-gap-benchmark-design](compression-gap-benchmark-design.md)
- [working-memory-chunk-scaling-benchmark](working-memory-chunk-scaling-benchmark.md)
- [benchmark-question-generation-pipeline](benchmark-question-generation-pipeline.md)
- [jobshop-spike-evidence-and-sizing](jobshop-spike-evidence-and-sizing.md)
- [kaggle-metrics-support-verified](kaggle-metrics-support-verified.md)

implies [[trajectory-post-tsp-synthesis]]

[[/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp_1.md]]
[[/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp_2.md]]