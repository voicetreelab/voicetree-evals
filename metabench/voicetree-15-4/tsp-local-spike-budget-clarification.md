---
color: green
isContextNode: false
agent_name: Kate
---
# TSP local spike budget clarification

Clarified why the live local spike is timing out at 120s instead of 600s: the locked design doc uses 10-minute subtasks, but the concrete task node for this local spike explicitly overrides that to a 2-minute subtask budget, and `protocol.py` matches the override.

## Evidence
- Design doc default: `SUBTASK_BUDGET_S = 600` (10 min per turn) in `kaggle-budget-metagame-design.md`.
- Local spike task override: `TOTAL_BUDGET_S=300`, `SUBTASK_BUDGET_S=120`, `PLAN_TURN_BUDGET_S=30` in `task_1776316393902b98.md`.
- Implemented constants: `TOTAL_BUDGET_S = 300`, `SUBTASK_BUDGET_S = 120`, `PLAN_TURN_BUDGET_S = 30` in `hch/metagame/protocol.py`.

## Practical meaning
The current local spike is intentionally running with a much smaller budget than the original benchmark sketch. The background process that is still running is therefore timing out execution turns at 120 seconds, not 600 seconds.

## Learning
The important distinction is “design default” versus “task-specific spike override.” The code followed the task node, not the earlier design doc defaults.

### NOTES

- No code changes made in this clarification.
- If the user wants the local spike to match the original design doc, `protocol.py` should be bumped from 120 to 600 and the background run restarted.

## Related

- [task_1776316393902b98](task_1776316393902b98.md)
- [tsp-local-spike-implementation](tsp-local-spike-implementation.md)
- [tsp-local-spike-smoke-findings](tsp-local-spike-smoke-findings.md)

[[task_1776316393902b98]]
