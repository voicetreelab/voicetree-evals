---
color: green
isContextNode: false
agent_name: Kate
---
# Local TSP spike budget bump to 30m / 10m / 5m

Updated the local spike to the larger benchmark budgets the user requested: total budget 1800s, subtask budget 600s, and planning-turn budget 300s. Restarted the detached full sweep so the live run uses the new values.

## Outcome
The local spike now uses:
- `TOTAL_BUDGET_S = 1800`
- `SUBTASK_BUDGET_S = 600`
- `PLAN_TURN_BUDGET_S = 300`

Both the actual timeout constants and the `NEXT_SUB.time_budget_s` examples shown to the model were updated so the prompt is no longer inconsistent with the harness.

## Live run
A fresh detached sweep was started after the patch.

Artifacts:
```text
/Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/results/background_20260416_153029.log
/Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/results/background_20260416_153029.jsonl
```

## Coordination
Per user request, a status message was sent to parent agent `Ivan` summarizing the budget change and the restarted run.

## Learnings
- The prior discrepancy was not a bug in the timeout wrapper; it came from following the task node's spike override rather than the earlier design-doc defaults.
- When changing runtime budgets, the user-facing contract examples need to be updated too, otherwise the model is told `120` while the harness enforces `600`.
- The safest way to apply a budget change mid-run is to restart the detached process rather than assume the existing background job will pick up new constants.

## DIFF

```
diff --git a/metabench/hch/metagame/protocol.py b/metabench/hch/metagame/protocol.py
@@
-TOTAL_BUDGET_S = 300
-SUBTASK_BUDGET_S = 120
-PLAN_TURN_BUDGET_S = 30
+TOTAL_BUDGET_S = 1800
+SUBTASK_BUDGET_S = 600
+PLAN_TURN_BUDGET_S = 300
@@
-        'NEXT_SUB: {"id": 1, "desc": "...", "time_budget_s": 120}\n'
+        f'NEXT_SUB: {{"id": 1, "desc": "...", "time_budget_s": {SUBTASK_BUDGET_S}}}\n'
@@
-        f'NEXT_SUB: {{"id": {turn_number}, "desc": "...", "time_budget_s": 120}}\n'
+        f'NEXT_SUB: {{"id": {turn_number}, "desc": "...", "time_budget_s": {SUBTASK_BUDGET_S}}}\n'
```

## Complexity: low

Small constant update plus keeping the prompt examples aligned with the enforced runtime budget.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/protocol.py

### NOTES

- `python3 -m py_compile metabench/hch/metagame/*.py` passed after the patch.
- The earlier background PID had already exited before restart, so there was no live stale process left to kill at patch time.

## Related

- [task_1776316393902b98](task_1776316393902b98.md)
- [tsp-local-spike-implementation](tsp-local-spike-implementation.md)
- [tsp-local-spike-budget-clarification](tsp-local-spike-budget-clarification.md)

[[task_1776316393902b98]]
