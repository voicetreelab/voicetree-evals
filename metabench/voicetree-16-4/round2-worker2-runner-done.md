# Round 2 Worker 2 Runner Done

Completed the assigned Round 2 probe matrix for `graphcol_hard_seed4`, `graphcol_hard_seed7`, `graphcol_hard_seed10`, and `tsp_hard_seed4` across `gemini-flash-latest`, `claude-sonnet-4.6`, and `gpt-5.4-mini`.

Execution note:
- The run started under the original mixed-model wrapper.
- Mid-run, the wrapper was patched to enforce a **600s total wall cap per `(row, model)`** via resume-safe `--single-run` subprocesses.
- After `graphcol_hard_seed7` Gemini landed, execution was split by model to avoid overlap: this runner finished the remaining **Gemini-only** lane while Timi finished the remaining **Claude-only** lane.
- Existing GPT artifacts were preserved and resumed rather than recomputed.

## Scope
- question_ids: `graphcol_hard_seed4`, `graphcol_hard_seed7`, `graphcol_hard_seed10`, `tsp_hard_seed4`
- models: `gemini-flash-latest`, `claude-sonnet-4.6`, `gpt-5.4-mini`

## Per-model parse rates
| model | completed | strict | rescue | failed_or_baseline | feasible | errors | avg_wall_s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gemini-flash-latest | 4 | 4 | 0 | 0 | 4 | 0 | 468.8 |
| claude-sonnet-4.6 | 4 | 4 | 0 | 0 | 4 | 0 | 151.9 |
| gpt-5.4-mini | 4 | 4 | 0 | 0 | 4 | 0 | 20.9 |

## Per-question headlines
- `graphcol_hard_seed4`: Gemini `strict_protocol_cf`, feasible=True, score=94.9550, wall_s=504.5, stop=`decision_stop`; Claude `strict_protocol_cf`, feasible=True, score=97.8526, wall_s=214.7, stop=`decision_stop`; GPT `strict_protocol_cf`, feasible=True, score=-0.1793, wall_s=17.9, stop=`decision_stop`.
- `graphcol_hard_seed7`: Gemini `strict_protocol_cf`, feasible=True, score=94.6949, wall_s=530.5, stop=`decision_stop`; Claude `strict_protocol_cf`, feasible=True, score=98.0873, wall_s=191.3, stop=`decision_stop`; GPT `strict_protocol_cf`, feasible=True, score=-0.4210, wall_s=42.1, stop=`decision_stop`.
- `graphcol_hard_seed10`: Gemini `strict_protocol_cf`, feasible=True, score=95.9092, wall_s=409.1, stop=`decision_stop`; Claude `strict_protocol_cf`, feasible=True, score=99.3487, wall_s=65.1, stop=`decision_stop`; GPT `strict_protocol_cf`, feasible=True, score=-0.1206, wall_s=12.1, stop=`decision_stop`.
- `tsp_hard_seed4`: Gemini `strict_protocol_cf`, feasible=True, score=95.6894, wall_s=431.1, stop=`decision_stop`; Claude `strict_protocol_cf`, feasible=True, score=98.4661, wall_s=136.4, stop=`decision_stop`; GPT `strict_protocol_cf`, feasible=True, score=97.9990, wall_s=11.6, stop=`decision_stop`.

## Headline findings
- All 12 runs completed with strict protocol parses; there were **no rescue parses, no baseline fallbacks, and no runtime errors**.
- `claude-sonnet-4.6` was the strongest row-for-row scorer on all four probes.
- `gemini-flash-latest` remained feasible and accurate, but it was materially slower than the other two models even after the 600s-total wrapper change.
- `gpt-5.4-mini` was by far the fastest path. It solved all four probes feasibly, but its graph-coloring scores were much weaker than Gemini/Sonnet because wall-time was tiny but solution quality stayed comparatively poor.

## Skips / Failures
- None.
