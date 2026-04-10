---
color: green
isContextNode: false
agent_name: Aki
---
# ForecastBench Follow-up: Resolution Checker v1

Added a first-pass `resolution_checker.py` helper under `scratch/` that buckets questions by inferred resolution horizon using `resolution_dates`, `market_info_close_datetime`, then question-text parsing, with `unknown` as fallback. Verified it on the 2026-03-29 public question set.

Implemented file:
- `/Users/lochlan/voicetree-evals/forecastbench-src/scratch/resolution_checker.py`

Current behavior:
- Reads a question-set JSON.
- Uses the earliest date from `resolution_dates` for dataset questions.
- Uses `market_info_close_datetime` for market questions.
- Falls back to lightweight question-text parsing for explicit dates.
- Buckets into `within_10_days`, `within_1_month`, `within_3_months`, `within_1_year`, `over_1_year`, and `unknown`.
- Prints which date source was used.

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

Buckets by earliest inferred resolution date:
  within_10_days: 278
  within_1_month: 29
  within_3_months: 64
  within_1_year: 127
  over_1_year: 2
  unknown: 0

Date source used:
  resolution_dates: 250
  market_info_close_datetime: 250
  question_text: 0
  unknown: 0
```

Key assumption in v1:
- For multi-horizon dataset questions, the script classifies by the earliest listed `resolution_date`, not by every horizon separately.

Learnings
- On the current public round, the explicit structured fields were sufficient for all questions; the text parser was not needed.
- The main thing we may want to iterate on is whether the counts should stay question-level or switch to resolution-target-level for dataset questions.
- Keeping the script in `scratch/` preserves a clear boundary between our local workflow helpers and the upstream repo codebase.

## Files Changed

- /Users/lochlan/voicetree-evals/forecastbench-src/scratch/resolution_checker.py

## Related

- [forecastbench-followup-step-2-question-set-inspection](forecastbench-followup-step-2-question-set-inspection.md)

[[1775618897236Woz]]
