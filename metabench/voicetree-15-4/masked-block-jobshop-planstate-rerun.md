---
color: green
isContextNode: false
agent_name: Siti
---
# Masked Block Jobshop — explicit plan-state rerun

Redid the masked-block Gemini 3 Pro seed-1 run with an explicit free-form `PLAN_STATE` string on turn 1 and `UPDATED_PLAN_STATE` on exec turns, threaded through every call. The rerun stayed on 25x15 and improved the final objective from 12282 to 11369, reducing gap from 44.78% to 34.02%.

## Protocol change
Persistent free-form plan state is now part of the contract:
- Turn 1 must emit `PLAN_STATE`.
- Every exec turn receives `CURRENT_PLAN_STATE`.
- Every exec turn must emit `UPDATED_PLAN_STATE`, which becomes the next turn's carried state.

## Comparison
| Variant | Baseline | Gold | Final | Gap % | Axis | Exec turns | Stop reason | Wall s |
| --- | ---: | ---: | ---: | ---: | --- | ---: | --- | ---: |
| No explicit plan-state string | 13615 | 8483 | 12282 | 44.78% | `due_date_first` | 1 | `subtask_stop` | 275.76 |
| Explicit plan-state string repassed every call | 13615 | 8483 | 11369 | 34.02% | `composite` | 1 | `subtask_stop` | 574.25 |

## New result row
| Model | Size | Baseline | Gold | Final | Gap % | Declared axis | Exec turns | Subtask p_solve | Stop reason | Wall s |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | ---: |
| `models/gemini-3-pro-preview` | 25x15 | 13615 | 8483 | 11369 | 34.02% | `composite` | 1 | 0.95 | `subtask_stop` | 574.25 |

Final details: makespan 543, weighted tardiness 509.
Objective improvement versus baseline: **2246**.
Objective improvement versus prior no-plan-state rerun: **913**.

## Plan state strings
Initial `PLAN_STATE`:

```text
Phase 1: Schedule M2-Front jobs (J23, J1, J11, J8, J16, J25, J24, J7) prioritizing J23 and J1 on M2 to start at 0 and 48, followed by the early due-date jobs. Phase 2: Schedule J18, J17, J13 on M2 from 153 to 270. Phase 3: Schedule remaining jobs (J19, J2, J22, J12, J10, J6, J3, J4, J14, J20, J5, J21) on M2 from 270 to 421, ordered by effective due date to minimize tardiness, achieving makespan 421.
```

Final `UPDATED_PLAN_STATE`:

```text
Phase 1: Scheduled M2-Front jobs prioritizing J23 and J1, followed by early due-date jobs. Phase 2: Scheduled J18, J17, J13 on M2. Phase 3: Scheduled remaining jobs on M2. Post-M2 operations were strictly prioritized by due date, resulting in zero tardiness for most jobs and a highly optimized objective of 11369. Stopping as further improvements are likely marginal.
```

## Interpretation
Adding explicit plan state changed the model's framing from `due_date_first` to a more `composite` bottleneck-plus-deadline strategy centered on machine `M2`. That improved quality substantially on the same one-seed setup, even though behavior was still effectively one-shot: one plan turn, one exec turn, then stop.

The plan-state version cost much more wall time, so the gain came from better reasoning rather than better stop behavior. The model still failed to iterate across multiple exec turns, but the carried state appears to have helped it hold onto a richer multi-phase bottleneck plan.

## Learnings
1. Tried the free-form state as an additive protocol field rather than replacing the existing axis/cut metadata, because the benchmark row still needed comparable declared-axis outputs.
2. Future agents should keep the plan state plain text. The user was right here: the useful part was persistence, not designing a schema.
3. In this harness, persistent state alone can move the model into a better decomposition regime without changing the underlying instance or verifier. The bigger remaining bottleneck is still control flow: the model improved, but it still stopped after one exec turn.

## Files Changed

- hch/masked_block_jobshop/prompt.py
- hch/masked_block_jobshop/protocol.py
- hch/masked_block_jobshop/results/masked_block_jobshop_gemini3pro_seed1_planstate_20260416.jsonl

### NOTES

- The rerun used the same requested size and stayed at 25x15 again; gold remained OPTIMAL with the same baseline/gold row, so the delta is attributable to protocol change rather than instance fallback.
- The child-process timeout wrapper remained unchanged and the revised run completed normally.
- Plan-turn forecast remained overconfident: it predicted near-gold atomic quality and very large continuation benefit, but the realized gap stayed 34.02%.

## Related

- [masked-block-jobshop-v1-gemini3pro-seed1-result](masked-block-jobshop-v1-gemini3pro-seed1-result.md)
- [masked-block-jobshop-plan-state-clarification](masked-block-jobshop-plan-state-clarification.md)

[[task_1776334440474z0n]]
