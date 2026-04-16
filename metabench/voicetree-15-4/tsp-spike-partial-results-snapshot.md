---
color: green
isContextNode: false
agent_name: Lou
---
# TSP spike partial results snapshot

Snapshot of currently committed local TSP spike rows across the active run files. Eight `(model, arm, seed)` rows are available so far; remaining cells are still running in the background.

## Scope
This snapshot uses only the active campaign files:
- `results/spike_20260416_full_3x3x3.jsonl`
- `results/spike_20260416_pro_seeds23.jsonl`
- `results/spike_20260416_flash_3x3.jsonl`
- `results/spike_20260416_gemini31_3x3.jsonl`

Older smoke / exploratory files were excluded because they are superseded by these newer run artifacts.

## Per-row snapshot
| model | arm | seed | acc_pct | gap_pct | score | brier | wall_s | stop_reason | turn1_died | killed | downward |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|
| gemini-2.5-flash | exhaustive | 1 | 86.036 | 13.964 | 81.699 | 257.142 | 433.6 | subtask_stop | 0 | 0 | 0 |
| gemini-2.5-flash | greedy | 1 | 77.615 | 22.385 | 76.813 | 57.983 | 80.2 | subtask_parse_fail | 0 | 0 | 0 |
| gemini-2.5-pro | exhaustive | 1 | 88.685 | 11.315 | 82.053 | 822.808 | 663.2 | subtask_stop | 0 | 0 | 0 |
| gemini-2.5-pro | greedy | 1 | 86.486 | 13.514 | 85.939 | 978.840 | 54.8 | subtask_stop | 0 | 0 | 0 |
| gemini-2.5-pro | greedy | 2 | 88.076 | 11.924 | 86.868 | 2.978 | 120.8 | subtask_stop | 0 | 0 | 0 |
| gemini-2.5-pro | smart | 1 | 95.646 | 4.354 | 92.622 | 2435.242 | 302.4 | subtask_stop | 0 | 0 | 0 |
| gemini-3.1-pro-preview | exhaustive | 1 | 99.765 | 0.235 | 97.202 | 9953.034 | 256.3 | subtask_stop | 0 | 0 | 0 |
| gemini-3.1-pro-preview | greedy | 1 | 99.765 | 0.235 | 97.393 | 9953.034 | 237.2 | subtask_stop | 0 | 0 | 0 |

## Aggregated by model x arm
| model | arm | n | mean_acc_pct | mean_gap_pct | mean_score | mean_brier | mean_wall_s | turn1_died | killed | downward |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gemini-2.5-flash | exhaustive | 1 | 86.036 | 13.964 | 81.699 | 257.142 | 433.6 | 0 | 0 | 0 |
| gemini-2.5-flash | greedy | 1 | 77.615 | 22.385 | 76.813 | 57.983 | 80.2 | 0 | 0 | 0 |
| gemini-2.5-pro | exhaustive | 1 | 88.685 | 11.315 | 82.053 | 822.808 | 663.2 | 0 | 0 | 0 |
| gemini-2.5-pro | greedy | 2 | 87.281 | 12.719 | 86.403 | 490.909 | 87.8 | 0 | 0 | 0 |
| gemini-2.5-pro | smart | 1 | 95.646 | 4.354 | 92.622 | 2435.242 | 302.4 | 0 | 0 | 0 |
| gemini-3.1-pro-preview | exhaustive | 1 | 99.765 | 0.235 | 97.202 | 9953.034 | 256.3 | 0 | 0 | 0 |
| gemini-3.1-pro-preview | greedy | 1 | 99.765 | 0.235 | 97.393 | 9953.034 | 237.2 | 0 | 0 | 0 |

## Interpretation notes
- `acc_pct` here is `100 - gap_pct`.
- `score` is the harness objective score (`accuracy reward - time penalty`), not a separate pure metacognition scalar.
- The metacog-relevant signals currently exposed are `brier`, `turn1_died`, `subtask_killed_count`, and `revised_best_guess_downward`.
- No committed row so far has `turn1_died = true`, `subtask_killed_count > 0`, or `revised_best_guess_downward = true` in the active campaign files.
- One current failure mode is `gemini-2.5-flash` greedy seed 1 stopping on `subtask_parse_fail` after omitting the required `NEXT_SUB` while still saying `DECISION: continue`.
- Background runs are still active, so this is a partial snapshot rather than a final benchmark table.

### NOTES

- Current active background processes are still writing `results/spike_20260416_pro_seeds23.jsonl`, `results/spike_20260416_flash_3x3.jsonl`, and `results/spike_20260416_gemini31_3x3.jsonl`.
- The biggest operational cost remains long execution turns, especially in the exhaustive arm, but the currently committed rows are valid enough to summarize.

## Related

- [task_1776317933629sza](task_1776317933629sza.md)
- [review-kate-tsp-spike-protocol-execution](review-kate-tsp-spike-protocol-execution.md)
- [tsp-local-spike-implementation](tsp-local-spike-implementation.md)

[[task_1776317933629sza]]
