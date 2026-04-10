---
color: green
isContextNode: false
agent_name: Aki
---
# ForecastBench Follow-up: Day-Of Game Plan Markdown

Added `scratch/gameplan.md`, a step-by-step runbook for the day a new ForecastBench question set drops. It covers fetching the round, inspecting workload, generating the submission skeleton, plugging in the forecast algorithm as a black box, validating the final file, uploading to GCP, and handling fallback email submission.

Created file:
- `/Users/lochlan/voicetree-evals/forecastbench-src/scratch/gameplan.md`

What the runbook covers:
- shell prep and environment activation
- fetching `latest-llm.json`
- inspecting tournament and preliminary workload via `resolution_checker.py`
- generating the submission skeleton with `make_submission_skeleton.py`
- keeping forecast generation as a black box while documenting the required output shape
- validating metadata, row counts, market/dataset split, forecast value ranges, and duplicate rows
- uploading the final artifact to the ForecastBench-provided GCP path
- fallback email procedure if upload fails
- local archiving of the submitted file

Why this matters:
- It converts the ad hoc exploration we did in-session into a repeatable day-of checklist.
- It keeps the user focused on the operational workflow without prematurely locking in a forecasting algorithm.
- It makes the distinction between planning views and the single required submission artifact explicit.

Learnings
- The most important operational subtlety is that the preliminary view is a planning lens, not a separate upload format.
- The safest workflow is to always fetch `latest-llm.json` fresh on round day instead of assuming the date from cadence alone.
- Validation steps are worth writing down explicitly because the real workload is row-based and much larger than the visible 500-question count.

## Files Changed

- /Users/lochlan/voicetree-evals/forecastbench-src/scratch/gameplan.md

## Related

- [forecastbench-followup-step-2-question-set-inspection](forecastbench-followup-step-2-question-set-inspection.md)
- [forecastbench-followup-step-3-submission-skeleton-helper](forecastbench-followup-step-3-submission-skeleton-helper.md)
- [forecastbench-followup-resolution-checker-v3-tournament-preliminary](forecastbench-followup-resolution-checker-v3-tournament-preliminary.md)

[[1775618897236Woz]]
