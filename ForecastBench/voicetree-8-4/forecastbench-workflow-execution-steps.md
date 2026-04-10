---
color: green
isContextNode: false
agent_name: Ivan
---
# ForecastBench Workflow Execution Steps

Specified the higher-tier workflows, horizon projection, validation, and recommended implementation order once the baseline shell exists.

Execution-path steps:
7. Implement the strong first-month preliminary workflow.
- Run the fullest map -> quantify path.
- Use provided metadata, source-specific structured data, official sources, EXA / web search, related market context, and X/social when useful.
- Start from the baseline prior, then apply evidence-based adjustments.

8. Implement the first-month-only overwrite rule.
- Produce one analysis per targeted dataset question.
- Apply that analysis only to the preliminary rows on that question that resolve within 1 month.
- Leave longer-horizon preliminary rows on baseline.

9. Keep all non-target rows on baseline.
- Market questions stay baseline-only.
- Preliminary rows beyond 1 month stay baseline-only.
- No bespoke compute should be spent outside the first-month preliminary bucket.

10. Implement the overwrite step and validation.
- Overwrite only the targeted first-month preliminary rows.
- Leave every other row untouched.
- Check row count, metadata, market-vs-dataset coverage, forecast bounds, and duplicate keys.
- Confirm the final artifact is still one unified submission JSON.

11. Run the benchmark-day operational flow.
- Fetch fresh `latest-llm.json` on round day.
- Generate the submission skeleton.
- Apply the first-month-preliminary forecasting workflow.
- Validate.
- Upload.

Recommended implementation order:
- First finish Steps 1-6 so the routing shell exists.
- Then add the strong workflow for targeted first-month preliminary questions.
- Finally add the targeted overwrite and validation refinements.

Learnings
- The reusable part of the root probability skill is the decision structure and quantification logic, not the original Polymarket intake plumbing.
- Question-level grouping is the key optimization because the same evidence feeds multiple horizons, even when only the first-month rows get overwritten.

continues [[forecastbench-workflow-completion-steps]]
