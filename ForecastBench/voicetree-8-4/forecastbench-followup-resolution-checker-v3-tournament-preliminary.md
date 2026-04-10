---
color: green
isContextNode: false
agent_name: Aki
---
# ForecastBench Follow-up: Resolution Checker v3 Tournament vs Preliminary

Updated `resolution_checker.py` to print both tournament and preliminary views. Tournament counts all required forecast rows; preliminary counts dataset-only rows, matching the dataset-only nature of the preliminary leaderboard.

Updated behavior:
- `Tournament view` counts all required forecast rows.
- `Preliminary view` counts only dataset forecast rows.
- Both views use the same horizon buckets.

Verified command:
```bash
cd /Users/lochlan/voicetree-evals/forecastbench-src
python3 scratch/resolution_checker.py scratch/question_sets/2026-03-29-llm.json
```

Observed output:
```text
Question set: 2026-03-29-llm.json
Forecast due date: 2026-03-29
Total questions: 500

Tournament view (all required forecast rows):
  Total required forecast rows: 2248
  Buckets:
    within_10_days: 278
    within_1_month: 277
    within_3_months: 314
    within_1_year: 627
    over_1_year: 752
    unknown: 0
  Date source used:
    resolution_dates: 1998
    market_info_close_datetime: 250
    question_text: 0
    unknown: 0

Preliminary view (dataset-only forecast rows):
  Total required forecast rows: 1998
  Buckets:
    within_10_days: 248
    within_1_month: 250
    within_3_months: 250
    within_1_year: 500
    over_1_year: 750
    unknown: 0
  Date source used:
    resolution_dates: 1998
    market_info_close_datetime: 0
    question_text: 0
    unknown: 0
```

Clarification:
- This preliminary section is dataset-only, which matches the dataset-only leaderboard concept.
- It does not yet mean "already resolved as of today"; it is a horizon breakdown of dataset rows by their scheduled resolution dates.

Learnings
- The word "preliminary" can mean two different things in practice: dataset-only versus already-resolved-to-date. This version implements the first meaning.
- The next likely refinement is an `--as-of YYYY-MM-DD` mode to report only rows that should already be resolved by a given date.
- The separation is now useful for planning effort because tournament work includes market rows while preliminary work does not.

## Files Changed

- /Users/lochlan/voicetree-evals/forecastbench-src/scratch/resolution_checker.py

## Related

- [forecastbench-followup-resolution-checker-v2-row-level](forecastbench-followup-resolution-checker-v2-row-level.md)

[[1775618897236Woz]]
