---
color: green
isContextNode: false
agent_name: Aki
---
# ForecastBench Follow-up: Resolution Checker v2 Row-Level Counts

Updated `resolution_checker.py` to bucket every required forecast row rather than each unique question. Verified that the current public round totals 2,248 required forecast rows, matching the generated submission skeleton.

Updated behavior:
- Dataset questions now contribute one bucketed count per `resolution_date`.
- Market questions still contribute one row each from `market_info_close_datetime`.
- Text parsing remains a single-date fallback when structured fields are missing.

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
Total required forecast rows: 2248

Buckets by required forecast row:
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
```

Interpretation:
- The current round needs `2248` forecast rows, not just `500` question-level classifications.
- That matches the submission skeleton row count exactly.
- The script is now aligned with the actual unit of work needed for submission preparation.

Learnings
- The biggest conceptual trap was counting question objects instead of required forecast rows.
- Current public rounds can differ a lot from a rough "~2500" estimate; the exact row total depends on how many dataset horizons are present in that round.
- The next likely iteration is a per-source or per-horizon breakdown now that the script is counting the right unit.

## Files Changed

- /Users/lochlan/voicetree-evals/forecastbench-src/scratch/resolution_checker.py

## Related

- [forecastbench-followup-resolution-checker-v1](forecastbench-followup-resolution-checker-v1.md)
- [forecastbench-followup-step-3-submission-skeleton-helper](forecastbench-followup-step-3-submission-skeleton-helper.md)

[[1775618897236Woz]]
