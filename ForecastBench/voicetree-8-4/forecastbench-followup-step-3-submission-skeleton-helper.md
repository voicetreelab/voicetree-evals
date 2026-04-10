---
color: green
isContextNode: false
agent_name: Aki
---
# ForecastBench Follow-up: Step 3 Submission Skeleton Helper

Added and verified a local helper script that converts a downloaded public question set into a valid ForecastBench submission skeleton with placeholder forecasts. Verified against the 2026-03-29 public round.

Created local helper script:
- `/Users/lochlan/voicetree-evals/forecastbench-src/scratch/make_submission_skeleton.py`

What it does:
- Reads a downloaded question-set JSON.
- Emits one forecast row per market question with `resolution_date: null`.
- Emits one forecast row per dataset horizon with `resolution_date` set to the ISO date from the question set.
- Writes a submission JSON with top-level keys `organization`, `model`, `model_organization`, `question_set`, `forecast_due_date`, and `forecasts`.

Verified command:
```bash
cd /Users/lochlan/voicetree-evals/forecastbench-src
python3 scratch/make_submission_skeleton.py \
  scratch/question_sets/2026-03-29-llm.json \
  --organization 'Example Team' \
  --model 'Example Model' \
  --model-organization 'Example Org'
```

Verification result:
- Output file: `scratch/submissions/2026-03-29.ForecastBench.example-model.json`
- Question set: `2026-03-29-llm.json`
- Forecast due date: `2026-03-29`
- Forecast rows: `2248`
- Market rows: `250`
- Dataset rows: `1998`

Learnings
- The user-facing question count is 500, but submission rows are much larger because dataset questions expand over multiple resolution horizons.
- The repo’s consumer code accepts missing `direction` and fills it with `None`, so the helper can stay minimal for current public rounds.
- Market rows should use JSON `null` for `resolution_date`, not a string placeholder like `"N/A"`.

## Files Changed

- /Users/lochlan/voicetree-evals/forecastbench-src/scratch/make_submission_skeleton.py

[[1775618897236Woz]]
