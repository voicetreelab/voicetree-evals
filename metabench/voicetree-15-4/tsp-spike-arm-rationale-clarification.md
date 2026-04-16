---
color: green
isContextNode: false
agent_name: Lou
---
# TSP spike arm rationale clarification

Clarified that the current `greedy` / `exhaustive` / `smart` split exists because the locked spike spec requested policy-counterfactual arms, not because a production benchmark necessarily needs multi-arm prompting.

## Core clarification
The user's objection is substantively valid: if the benchmark goal is simply **"which model best maximizes the economic objective?"**, then a single canonical prompt that tells the model to optimize `$score = value - cost/time` is the cleaner benchmark.

## Why the current spike has multiple arms
The current local TSP spike distinguishes `greedy`, `exhaustive`, and `smart` only because the locked protocol spec explicitly required **three arms via system-prompt variants only**. In that framing, the arms are **ablations / counterfactual policies**:
- `greedy` = cheap / early-stop policy
- `exhaustive` = maximize accuracy, ignore cost term
- `smart` = explicitly optimize the benchmark objective

This is useful if the research question is:
- does prompting a different stop policy change behavior for the same model?
- how much of performance comes from model capability vs instructed policy?

## Why the user's simplification is reasonable
If the actual benchmark question is just:
- *Which model produces the highest realized economic value under the benchmark objective?*

then multiple prompt arms are unnecessary complexity and add prompt-sensitivity noise. In that regime the cleaner design is:
1. one canonical objective-optimizing prompt
2. one leaderboard ranked by realized objective score
3. keep gap, wall-clock, Brier, stop flags as diagnostics rather than separate benchmark arms

## Practical consequence for this task
For the current task, Lou should still execute the existing spike as written because the task node treats the three-arm protocol as authoritative. But for the design discussion, multi-arm should be framed as **optional ablation machinery**, not as obviously required benchmark structure.

### NOTES

- This clarification does not change the current runner task; it changes how the benchmark design should be interpreted.
- Recommended framing: single-arm benchmark for leaderboard, multi-arm only for analysis / ablation.

[[task_1776317933629sza]]
