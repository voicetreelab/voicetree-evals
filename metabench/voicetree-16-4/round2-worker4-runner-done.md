# Round 2 Worker 4 Runner Done

Completed the worker-local probe eval run for:
- `ve_hard_seed10`
- `mwis_hard_seed5`
- `mwis_hard_seed9`
- `mwis_hard_seed13`

Artifacts were written under `kaggle_submission/results/full/{question_id}/`, with worker-local summaries in:
- `kaggle_submission/scratch/round2/worker4/runner-log.md`
- `kaggle_submission/scratch/round2/worker4/runner-summary.json`

No model was globally skipped. No API/billing/rate-limit failures occurred. The run finished cleanly.

## Per-model summary

| model | completed | feasible | avg score | parse paths |
|---|---:|---:|---:|---|
| `gemini-flash-latest` | 4 | 4 | 81.51 | `partial_rescue`=1, `strict_protocol_cf`=3 |
| `claude-sonnet-4.6` | 4 | 1 | 20.20 | `partial_rescue`=1, `strict_parse_failed`=2, `strict_protocol_cf`=1 |
| `gpt-5.4-mini` | 4 | 4 | 81.82 | `partial_rescue`=1, `strict_protocol_cf`=3 |

## Per-question headlines

- `ve_hard_seed10`: all 3 models were feasible. Best score was `gpt-5.4-mini` at `89.43`; `gemini-flash-latest` scored `87.61`; `claude-sonnet-4.6` scored `80.80` but ended with `error` after an exec-turn parse failure, rescued via `partial_rescue`.
- `mwis_hard_seed5`: `gemini-flash-latest` and `gpt-5.4-mini` were feasible at `75.76` and `71.47`. `claude-sonnet-4.6` hit `strict_parse_failed`, was infeasible, and scored `0.00`.
- `mwis_hard_seed9`: strongest row overall. `gpt-5.4-mini` scored `85.69`, narrowly above `gemini-flash-latest` at `85.40`; both were feasible. `claude-sonnet-4.6` produced `strict_protocol_cf` output but remained infeasible and scored `0.00`.
- `mwis_hard_seed13`: `gpt-5.4-mini` scored `80.71` and `gemini-flash-latest` scored `77.27`, both feasible. `claude-sonnet-4.6` hit another `strict_parse_failed` result and scored `0.00`.

## Notable patterns

- `claude-sonnet-4.6` was the clear weak point on MWIS hard: `0/3` feasible, with two parse failures and one infeasible strict-protocol completion.
- `gemini-flash-latest` was reliable but slow on MWIS hard, especially `mwis_hard_seed9` (`808.6s` wall time).
- `gpt-5.4-mini` was the most balanced model here: `4/4` feasible, best row score on `ve_hard_seed10` and `mwis_hard_seed9`, and very short wall times on all four rows.
