---
color: blue
isContextNode: false
agent_name: Uma
---
# Portfolio spike structured-output simplification decision

Evaluated the lighter-weight protocol option after the structured-output rerun task was questioned. Recommendation: schema the control/state envelope, but keep candidate artifacts and long-form reasoning as strings or loosely typed JSON payloads to preserve scoring while avoiding brittle per-problem schemas.

## Decision
Use structured output for the protocol state machine, not for every artifact field.

## Recommended minimal contract
Plan turn should stay schema-constrained for:
- `PLAN`
- `NEXT_SUB_ID`

Exec turn should stay schema-constrained for:
- `SUB_N_RESULT`
- `FORECAST`
- `REVISED_PLAN`
- `NEXT_SUB_ID`
- one candidate field carrying the proposed answer payload

## Why not make plan state a raw string?
A free-form plan string is viable only if the harness stops depending on plan semantics. The current portfolio spike does depend on those semantics:
- it needs to know which subtask is next
- it needs to know whether a subtask is still pending or done
- it needs to record additions, revisions, and status flips turn by turn
- it needs a stable plan-evolution trace for the deliverable

If `REVISED_PLAN` becomes an opaque string, those metrics disappear or become post-hoc heuristic parsing again.

## Better compromise
Keep the plan as explicit structured state, but allow the model to choose the natural-language content inside it:
- `desc` remains free text
- `SUB_N_RESULT` remains free text
- candidate artifacts can be kept as a raw JSON string or a loosely typed `answer` field

This preserves the revisable multi-step plan requirement while avoiding brittle regex parsing and avoiding a large problem-specific schema explosion.

## Learnings
- The real fragility is in the control envelope, not in the model's descriptive text.
- If the benchmark wants plan evolution, the plan cannot be an uninterpreted blob; at minimum the harness must retain item ids, statuses, and next-step selection.
- The lightest reliable architecture is: strict schema for control state, permissive payloads for artifact content.

### NOTES

- This narrows the implementation from 'fully typed structured output everywhere' to 'typed control envelope plus permissive artifact payloads'.
- If the user approves this simplification, protocol changes become smaller and less risky while still eliminating the regex label-block failure class.

## Related

- [portfolio-spike-v1-local-harness-and-run-2026-04-16](portfolio-spike-v1-local-harness-and-run-2026-04-16.md)
- [task_1776337535298wih](task_1776337535298wih.md)

[[task_1776337535298wih]]
