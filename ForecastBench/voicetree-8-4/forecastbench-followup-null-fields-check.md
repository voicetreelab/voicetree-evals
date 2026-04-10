---
color: green
isContextNode: false
agent_name: Aki
---
# ForecastBench Follow-up: Null Fields Check

Checked the generated submission skeleton and confirmed the `null` fields are expected: market rows legitimately use `resolution_date: null`, and `reasoning` is optional and currently blank by design.

Verified generated file: `2026-03-29.ForecastBench.example-model.json`

Observed counts:
- `n_forecasts`: `2248`
- `n_null_resolution_dates`: `250`
- `n_null_reasoning`: `2248`

Interpretation:
- `250` null `resolution_date` values correspond to the `250` market questions in the round.
- Dataset rows carry explicit ISO `resolution_date` values, one row per horizon.
- `reasoning` is not required for acceptance in the current repo consumer path and is explicitly dropped before resolution/scoring.

Repo evidence:
- `src/helpers/model_eval.py` emits market forecasts with `"resolution_date": None` and zero-shot forecasts with `"reasoning": None`.
- `src/resolve_forecasts/main.py` drops the `reasoning` column during validation, so it is not used for scoring.

Sample rows:
```json
{
  "id": "hiqwmkt2f5MbEtmVdkv6",
  "source": "manifold",
  "forecast": 0.5,
  "resolution_date": null,
  "reasoning": null
}
```

```json
{
  "id": "d13164a14ead5bbbeebceb2c273af666cdfcf8d8c769d57fab9f7afbf13c6d8f",
  "source": "acled",
  "forecast": 0.5,
  "resolution_date": "2026-04-05",
  "reasoning": null
}
```

## Related

- [forecastbench-followup-step-3-submission-skeleton-helper](forecastbench-followup-step-3-submission-skeleton-helper.md)

[[1775618897236Woz]]
