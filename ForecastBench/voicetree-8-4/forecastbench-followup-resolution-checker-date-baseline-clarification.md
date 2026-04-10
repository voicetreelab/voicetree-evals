---
color: green
isContextNode: false
agent_name: Aki
---
# ForecastBench Follow-up: Resolution Checker Date Baseline Clarification

Clarified that the checker’s horizon buckets are measured relative to the question set’s `forecast_due_date`, which is effectively the submission date for that round. Confirmed the script can be rerun on future question sets with the same schema.

Clarification:
- `within_10_days`, `within_1_month`, and the other buckets are computed relative to the question set's `forecast_due_date` field.
- In the public submission workflow, that `forecast_due_date` is the round's submission date / due date.
- So for the current file `2026-03-29-llm.json`, `within_10_days` means within 10 days of `2026-03-29`.

Reusability:
- The script can be rerun on a new downloaded question set as-is.
- It will read the new file's own `forecast_due_date` and bucket against that date automatically.
- If a future set changes schema or omits structured dates, some rows may fall into `question_text` or `unknown`, but the script will still run.

## Related

- [forecastbench-followup-resolution-checker-v3-tournament-preliminary](forecastbench-followup-resolution-checker-v3-tournament-preliminary.md)

[[1775618897236Woz]]
