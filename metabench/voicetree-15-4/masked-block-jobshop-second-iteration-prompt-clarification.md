---
color: green
isContextNode: false
agent_name: Siti
---
# Masked Block Jobshop — second-iteration prompt clarification

Clarified that the second call does not reuse the exact turn-1 decomposition prompt. It reuses the problem statement and continuation/value framing, but switches to an execution prompt that carries `CURRENT_PLAN_STATE`, `NEXT_SUB_TO_EXECUTE`, and `CURRENT_BEST_*`.

## Clarification
Turn 2 is **not** the same prompt as turn 1.

Turn 1 asks the model to:
- choose a decomposition axis
- describe a boundary cut
- emit an initial `PLAN_STATE`
- forecast atomic quality and whether one more subtask is worth it
- pick `NEXT_SUB`

Turn 2 instead gives the model:
- the same underlying problem statement
- `CURRENT_PLAN_STATE`
- `NEXT_SUB_TO_EXECUTE`
- `CURRENT_BEST_*` schedule/objective context
- the same continuation/value question via `CONTINUE_FORECAST`

So the decomposition framing persists indirectly through the carried plan state, but the explicit "choose a decomposition axis / boundary cut" instruction is only in turn 1.

## Related

- [masked-block-jobshop-planstate-rerun](masked-block-jobshop-planstate-rerun.md)

[[task_1776334440474z0n]]
