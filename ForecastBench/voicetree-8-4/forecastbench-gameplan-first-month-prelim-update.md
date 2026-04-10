---
color: green
isContextNode: false
agent_name: Ivan
---
# ForecastBench Gameplan Update: First-Month Preliminary Policy

Updated the operational runbook in `scratch/gameplan.md` to match the amended strategy: baseline-first coverage, strong workflow only for first-month preliminary rows, and baseline-only handling for everything else.

Updated the day-of runbook to remove the old black-box framing and replace it with the explicit new policy.

What changed in the runbook:
- The intro now states the actual forecasting policy instead of treating forecasting as unspecified.
- The core idea now includes building a full baseline submission first and selectively overwriting only first-month preliminary rows.
- Step 2 now highlights that the main high-effort bucket is the `within_1_month` count in the preliminary view.
- Step 4 now spells out the intended forecasting process:
  - baseline submission for all rows
  - target only preliminary rows within 1 month
  - group those targets by dataset question
  - run the strong workflow only there
  - overwrite only those targeted rows
  - leave everything else on baseline
- Validation now explicitly checks that the overwrite scope stayed narrow.
- The one-command section now echoes the new policy instead of referring to an unspecified forecast algorithm.
- Future improvements now describe a deterministic baseline-first targeted-overwrite script.

Learnings
- The key documentation risk was leaving the forecasting section as a black box after the strategy had already become explicit elsewhere in the graph.
- The most important operational boundary is not just which questions get analyzed, but which rows are allowed to be overwritten afterward.
- The runbook is now aligned with the amended policy: full workflow only for first-month preliminary rows, no-compute baseline for everything else.

## Files Changed

- /Users/lochlan/voicetree-evals/forecastbench-src/scratch/gameplan.md

### NOTES

- This was a documentation-only update; no scripts or runtime code were changed.
- The runbook still intentionally avoids inventing commands for the targeted workflow that have not yet been implemented.

[[1775712512821qMj]]
