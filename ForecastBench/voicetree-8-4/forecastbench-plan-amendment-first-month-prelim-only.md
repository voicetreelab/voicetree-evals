---
color: green
isContextNode: false
agent_name: Ivan
---
# ForecastBench Plan Amendment: First-Month Preliminary Only

Amended the workflow so the strong full workflow applies only to preliminary rows resolving within 1 month. All other rows, including market questions and longer-horizon preliminary rows, now stay on the cheap no-compute baseline.

Policy change applied across the workflow nodes:
- Removed the old split between `<= 10 days`, `11-30 days`, and market quick-pass tiers.
- Replaced it with one sharp target bucket: first-month preliminary rows.
- Kept the baseline-first safety net unchanged.
- Clarified that question-level analysis is still the efficient unit of work, but the overwrite scope is only the first-month preliminary rows on those questions.

What is now true:
- Full workflow: every preliminary question with one or more rows resolving within 30 days.
- Baseline only: everything else.
- No bespoke compute for market questions.
- No bespoke compute for preliminary rows beyond 1 month.

Key consequence:
- We still analyze targeted dataset questions at the question level so evidence can be reused across horizons.
- But we only overwrite the `<= 30 day` preliminary rows; the longer-horizon rows on the same question remain baseline.

Files updated:
- `/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-workflow-synthesis.md`
- `/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-routing-and-algorithm.md`
- `/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-tool-and-source-policy.md`
- `/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-workflow-completion-steps.md`
- `/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-workflow-execution-steps.md`
- `/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-high-level-day-of-approach.md`
- `/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-workflow-phase-2.md`

## Files Changed

- /Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-workflow-synthesis.md
- /Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-routing-and-algorithm.md
- /Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-tool-and-source-policy.md
- /Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-workflow-completion-steps.md
- /Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-workflow-execution-steps.md
- /Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-high-level-day-of-approach.md
- /Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-workflow-phase-2.md

### NOTES

- This amendment intentionally narrows the expensive workflow scope rather than changing the baseline safety-net or the one-file submission model.

## Related

- [forecastbench-workflow-synthesis](forecastbench-workflow-synthesis.md)
- [forecastbench-routing-and-algorithm](forecastbench-routing-and-algorithm.md)
- [forecastbench-tool-and-source-policy](forecastbench-tool-and-source-policy.md)
- [forecastbench-workflow-completion-steps](forecastbench-workflow-completion-steps.md)
- [forecastbench-workflow-execution-steps](forecastbench-workflow-execution-steps.md)
- [forecastbench-high-level-day-of-approach](forecastbench-high-level-day-of-approach.md)

[[1775712512821qMj]]
