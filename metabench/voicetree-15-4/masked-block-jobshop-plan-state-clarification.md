---
color: green
isContextNode: false
agent_name: Siti
---
# Masked Block Jobshop v1 — plan-state clarification

Clarified that the implemented masked-block harness does not use a persistent, revisable multi-step PLAN object. It uses a single plan turn with axis/cut plus a rolling `NEXT_SUB`, while persistence lives in runner-side `CURRENT_BEST_*` state.

## Clarification
This implementation is **not** the stronger "explicit multi-step plan, revisable at each turn" design.

What it does have:
- Turn 1 requires `DECLARED_DECOMPOSITION_AXIS`, `DECLARED_AXIS_RATIONALE`, `DECLARED_BOUNDARY_CUT`, and one `NEXT_SUB` payload.
- Each exec turn receives `CURRENT_BEST_*` plus one `NEXT_SUB_TO_EXECUTE`, and may emit another `NEXT_SUB`.

What it does **not** have:
- No persistent `PLAN` object.
- No structured list of steps that is carried forward and revised each turn.
- No explicit done/in-progress/revised bookkeeping inside model-visible state.

So the implemented protocol is "single planning turn + rolling next subtask + persistent best schedule state," not Option-A-style plan-as-state.

## Related

- [masked-block-jobshop-v1-gemini3pro-seed1-result](masked-block-jobshop-v1-gemini3pro-seed1-result.md)

[[task_1776334440474z0n]]
