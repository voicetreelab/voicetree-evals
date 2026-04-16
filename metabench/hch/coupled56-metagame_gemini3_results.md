# Coupled MetaGame Gemini 3 Results

This file summarizes the current Gemini 3 results for the coupled two-factory job-shop metagame spike under `hch/codex_metagame_v2`.

Note: despite the filename `coupled56`, the main live run summarized here is the current `6x7` variant, because that is the latest calibrated spike configuration.

## Main live run

Artifact:
- `hch/codex_metagame_v2/results/gemini31_6x7_20260416_run.jsonl`

Config:
- model: `gemini-3.1-pro-preview`
- seeds: `1 2 3`
- size: `6 jobs x 7 machines` in each factory
- budgets:
  - `TOTAL_BUDGET_S = 1800`
  - `SUBTASK_BUDGET_S = 600`
  - `PLAN_TURN_BUDGET_S = 300`
- old forecast contract:
  - `ATOMIC_PREDICTION`
  - `DECLARED_GAP`
  - `P_CORRECT`

### Aggregate summary

| metric | value |
|---|---:|
| mean gap_pct | 4.43 |
| mean wall_s | 211.64 |
| mean score | 93.46 |
| mean brier | 13270.09 |
| mean turn_count | 2.00 |
| mean execution subtasks used | 1.00 |
| turn1_died | 0 |
| killed | 0 |
| infeasible | 0 |
| errors | 0 |

### Per-seed results

| seed | baseline | optimal | final | gap_pct | score | stop_reason | turns | source |
|---|---:|---:|---:|---:|---:|---|---:|---|
| 1 | 216 | 106 | 115 | 8.49 | 89.68 | `subtask_stop` | 2 | `model` |
| 2 | 255 | 114 | 116 | 1.75 | 96.01 | `subtask_stop` | 2 | `model` |
| 3 | 239 | 99 | 102 | 3.03 | 94.68 | `subtask_stop` | 2 | `model` |

### Behavioral takeaway

- This run was **not saturated** in the Johnson-rule / exact-algorithm-collapse sense.
- Gemini 3 did **not** die on turn 1 once the planning budget was restored to 300 seconds.
- All three runs used exactly one execution subtask:
  - one planning turn
  - one execution turn
  - then stop
- So the benchmark now exposes meaningful optimization headroom, but the metacognitive behavior is still shallow.

### Calibration takeaway

The old forecast contract was poor for optimization:
- `atomic_p_correct` collapsed to `0.0`
- `declared_gap` was wildly miscalibrated (`100`, `135`, `120`)
- realized gaps were much smaller (`8.49`, `1.75`, `3.03`)

That means the optimization behavior was decent, but the self-estimates were not.

## Forecast-contract rerun

Artifact:
- `hch/codex_metagame_v2/results/gemini31_6x7_newforecast_seed1_20260416.jsonl`

Config:
- model: `gemini-3.1-pro-preview`
- seed: `1`
- size: `6x7`
- same budgets as above
- new forecast contract:
  - `ATOMIC_FORECAST: {p_gap_le_2, p_gap_le_5, p_gap_le_10}`
  - `CONTINUE_FORECAST: {p_improve_if_one_more_subtask, expected_gap_reduction, expected_delta_score}`
  - execution-turn `QUALITY_FORECAST` with the same thresholded gap structure

### Result

| metric | value |
|---|---:|
| baseline_makespan | 216 |
| optimal_makespan | 106 |
| final_makespan | 109 |
| gap_pct | 2.83 |
| score | 94.62 |
| brier (atomic thresholded forecast) | 0.405 |
| continue_brier | 0.0025 |
| expected_delta_score_error | 54.76 |
| turn_count | 2 |
| stop_reason | `subtask_stop` |

### Forecasts emitted

Turn 1:

```json
{
  "atomic_forecast": {
    "p_gap_le_2": 0.05,
    "p_gap_le_5": 0.15,
    "p_gap_le_10": 0.30
  },
  "continue_forecast": {
    "p_improve_if_one_more_subtask": 0.95,
    "expected_gap_reduction": 50.0,
    "expected_delta_score": 40.0
  }
}
```

Turn 2:

```json
{
  "final_quality_forecast": {
    "p_gap_le_2": 0.85,
    "p_gap_le_5": 0.95,
    "p_gap_le_10": 0.99
  },
  "continue_forecast": {
    "p_improve_if_one_more_subtask": 0.05,
    "expected_gap_reduction": 0.5,
    "expected_delta_score": -10.0
  }
}
```

### Rerun takeaway

- The new forecast contract is clearly better than the old one.
- Gemini 3 now gives coherent thresholded distance-to-optimal beliefs instead of degenerate “probability exactly correct” style answers.
- The quality forecast after execution is reasonably sensible for the realized `2.83%` gap.
- The continuation forecast is directionally useful, but still not well calibrated in magnitude:
  - continuing really was worth it
  - but the predicted `expected_delta_score = 40.0` was much smaller than the realized delta score of about `94.76`

## Current overall verdict

1. The coupled multi-machine benchmark direction is viable.
2. Restoring a 5-minute planning budget was necessary.
3. The benchmark is no longer suffering from immediate timeout pathology.
4. It is also not obviously saturated.
5. The remaining weakness is shallow search depth:
   - Gemini 3 still tends to do one good execution subtask and then stop.
6. The new forecast contract is a real improvement and should probably replace the old one for further runs.
