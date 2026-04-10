---
color: green
isContextNode: false
agent_name: Ivan
---
# ForecastBench Workflow Completion Steps

Converted the workflow into a concrete ordered checklist, split into build-path steps and execution-path steps so the implementation sequence stays clear.

This checklist is meant to be completed in order.

Build-path first:
1. Lock the baseline path.
- Confirm the dataset baseline comes from the existing source-aware naive forecaster.
- Confirm the market baseline rule is `market price if available, else 0.5`.
- Treat this as the guaranteed-coverage fallback for every required row.

2. Build the row-expansion and grouping layer.
- Read the round question set.
- Expand dataset `resolution_dates` into submission rows.
- Group dataset rows back into one work item per question `id`.
- Keep market questions as one work item each.

3. Build the intake packet for each work item.
- Include question text, background, source intro, resolution criteria, URL, freeze time, source, close info, and attached horizons.
- This replaces the Polymarket-style parsed-contract intake from the root skill.

4. Implement the target selector.
- A dataset question enters the strong workflow if it is part of prelim and has one or more resolution rows within 1 month.
- Everything else is assigned to baseline-only handling.

5. Remove early-stop logic for the target bucket.
- Every first-month preliminary target should go through the strong full workflow.
- Do not shortcut these questions back to baseline just because the baseline looks plausible.

6. Build the overwrite-ready baseline artifact.
- Generate the full submission from the cheap baseline first.
- This guarantees a valid file even if higher-tier workflows are still incomplete.

Learnings
- The biggest execution trap is thinking in submission rows instead of question-level work items.
- The safest delivery strategy is baseline-first, because it guarantees a valid artifact before any expensive logic is added.
- The key scope guard is to overwrite only the first-month preliminary rows, not the whole horizon ladder for a targeted question.

## Related

- [forecastbench-workflow-synthesis](forecastbench-workflow-synthesis.md)
- [forecastbench-routing-and-algorithm](forecastbench-routing-and-algorithm.md)
- [forecastbench-tool-and-source-policy](forecastbench-tool-and-source-policy.md)

[[1775712512821qMj]]
