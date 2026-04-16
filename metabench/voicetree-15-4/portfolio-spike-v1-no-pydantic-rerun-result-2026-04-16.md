---
color: green
isContextNode: false
agent_name: Uma
---
# Portfolio spike v1 no-Pydantic rerun result

Ran the portfolio spike again on April 16, 2026 with the no-Pydantic structured-output implementation and `models/gemini-3-pro-preview`. The run succeeded through three completed exec turns, solved P4 and P2 optimally, got P1 to 4.44% gap, then timed out on the fourth subtask (TSP), finishing with net score 178.88.

## Per-problem Result Table
| id | baseline | gold | model_final | value_captured | subtasks_executed |
|---|---:|---:|---:|---:|---:|
| P1 | 155 | 90 | 94 | 46.92 | 1 |
| P2 | 72 | 59 | 59 | 60.00 | 1 |
| P3 | 588.221 | 470.146 | 588.221 | 0.00 | 0 |
| P4 | 20 | 4 | 4 | 100.00 | 1 |

## Plan Evolution Trace
| turn | phase | plan_size | additions | revisions | status_flips | per-turn wall | cumulative wall | note |
|---|---|---:|---|---|---|---:|---:|---|
| 1 | plan | 4 | n/a | n/a | n/a | 13.37 | 13.37 | next_sub=1 |
| 2 | exec | 4 | [] | [] | [1] | 94.27 | 107.64 | problem=P4 next_sub=2 |
| 3 | exec | 4 | [] | [] | [2] | 85.93 | 193.57 | problem=P2 next_sub=3 |
| 4 | exec | 4 | [] | [] | [3] | 167.19 | 360.76 | problem=P1 next_sub=4 |
| 5 | exec | N/A | n/a | n/a | n/a | 200.01 | 560.77 | timeout before response |

## Thresholded Brier Per Problem
| id | p_within_5pct | p_within_10pct | p_within_20pct | p_within_50pct |
|---|---:|---:|---:|---:|
| P1 | 0.04 | 0.01 | 0.00 | 0.00 |
| P2 | 0.00 | 0.00 | 0.00 | 0.00 |
| P3 | N/A | N/A | N/A | N/A |
| P4 | 0.00 | 0.00 | 0.00 | 0.00 |

## Session Score Breakdown
| metric | value |
|---|---:|
| Σ V_i | 206.923 |
| cost | 28.044 |
| net | 178.879 |
| stop_reason | subtask_timeout |
| wall_time_s | 560.887 |
| turn1_wall_s | 13.373 |

## Timeout Diagnostics
Last API call was exec turn 5 on subtask 4 (`P3`, `Optimize TSP-20 tour to capture up to 20 value.`). The call timed out after 200.005s with no returned text:
```json
{
  "attempt_index": 1,
  "input_tokens": null,
  "output_tokens": null,
  "parsed": null,
  "text": "",
  "thinking_tokens": null,
  "timed_out": true,
  "total_tokens": null,
  "wall_seconds": 200.00525712501258
}
```

## Interpretation
This rerun shows the architecture fix worked: the session got past turn 1 and maintained structured plan state across multiple exec turns. Plan-as-state did unlock real multi-subtask behavior, but it did not unlock plan revision in the stronger sense; the model simply executed the original 4-item plan in order, with only status flips and no additions or rewrites. Allocation was partly rational: it captured the two largest caps first (P4 then P2), then recovered most of P1, but left P3 untouched because the final TSP subtask timed out. The model did not stop economically; it continued into TSP instead of halting after capturing 206.92 gross value, and the run ended only because the final subtask consumed its full 200s budget. Calibration on the solved problems was strong: P2 and P4 were perfect, and P1's 0.8/0.9/1.0/1.0 forecast was directionally correct for a 4.44% final gap.

## Learnings
1. Tried the no-Pydantic manual-schema path specifically to eliminate the prior request-level schema rejection, and it worked: the session progressed through live model turns without any schema-construction failure.
2. A future agent might over-credit "plan as state" here. The state machinery worked, but the model still behaved like a fixed-plan executor rather than dynamically revising or adding subtasks.
3. The current belief to carry forward is: structured output plus downstream verification is now robust enough for this harness, and the next performance bottleneck is subtask budgeting/timeout behavior on harder problems like TSP rather than parser fragility.

## Files Changed

- hch/portfolio_spike/results/portfolio_spike_structured_nopydantic_seed1_20260416.json

### NOTES

- This was a user-explicit rerun after the earlier April 16, 2026 Pydantic-based failure; it should be read as superseding that failed attempt for protocol validation.
- Initial plan order was P4 -> P2 -> P1 -> P3, and the first three subtasks all completed with parse_ok=true and feasible verified answers.

## Related

- [portfolio-spike-v1-local-harness-and-run-2026-04-16](portfolio-spike-v1-local-harness-and-run-2026-04-16.md)
- [portfolio-spike-v1-structured-output-upgrade-and-rerun-2026-04-16](portfolio-spike-v1-structured-output-upgrade-and-rerun-2026-04-16.md)

validated by [[portfolio-spike-v1-no-pydantic-structured-output-refactor-2026-04-16]]
