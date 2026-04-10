---
color: green
isContextNode: false
agent_name: Aki
---
# ForecastBench Follow-up: Question Schema Clarification

Verified that the downloaded live question set includes richer question metadata such as `url`, `freeze_datetime`, and `background`. The earlier `jq` commands only displayed a small selected subset for readability.

Verified local question object keys from the downloaded public question set:

```json
[
  "background",
  "freeze_datetime",
  "freeze_datetime_value",
  "freeze_datetime_value_explanation",
  "id",
  "market_info_close_datetime",
  "market_info_open_datetime",
  "market_info_resolution_criteria",
  "question",
  "resolution_criteria",
  "resolution_dates",
  "source",
  "source_intro",
  "url"
]
```

Why the user only saw a few fields earlier:
- The prior commands used filters like `{id, source, resolution_dates, question}`.
- `jq` returns only the explicitly selected fields in that object constructor.
- The underlying JSON still contains the full question record.

Useful inspection commands:
```bash
jq '.questions[0]' "scratch/question_sets/$LATEST"
jq '.questions[0] | keys' "scratch/question_sets/$LATEST"
```

## Related

- [forecastbench-followup-step-2-question-set-inspection](forecastbench-followup-step-2-question-set-inspection.md)

[[1775618897236Woz]]
