---
color: green
isContextNode: false
agent_name: Ivan
---
# ForecastBench Routing And Algorithm

Specified the benchmark-day routing policy and the end-to-end algorithm for filling the submission file.

Routing policy:
- Full-workflow bucket: preliminary dataset questions that have one or more resolution rows within `<= 30 days` -> strong adapted map->quantify workflow.
- Baseline bucket: everything else -> keep the cheap no-compute baseline.

End-to-end algorithm:
1. On round day, fetch `latest-llm.json`, expand all rows, and compute horizon buckets relative to `forecast_due_date`.
2. Build a guaranteed-coverage baseline submission first.
   - Dataset rows use the repo's source-aware naive forecaster as the default prior.
   - Market rows use current market probability when available, else `0.5`.
3. Convert only the preliminary dataset rows into question-level work items.
   - One work item per dataset `id`, carrying all resolution dates.
   - Mark which of that question's rows fall within the first month.
4. Build an intake packet for each targeted work item using all provided fields: question text, background, `source_intro`, resolution criteria, URL, freeze time, source, close info, and attached horizons.
5. Select the full-workflow bucket.
   - If a preliminary dataset question has one or more `<= 30 day` resolution rows, it enters the strong workflow.
   - Everything else stays untouched on baseline.
6. For every targeted question, run the full adapted evidence workflow.
   - Mapping phase: identify drivers, catalysts, disconfirmers, and data gaps.
   - Quantification phase: start from the baseline prior, apply LR-style adjustments, and spend deeper analysis where value-of-information is high.
   - There is no early-stop shortcut for this bucket; these are the questions we explicitly care about.
7. Convert the result into horizon-specific probabilities only for the first-month preliminary rows on that question.
   - The analysis can be shared across the question's horizon ladder.
   - But only the `<= 30 day` preliminary rows get overwritten.
   - Longer-horizon rows remain on baseline.
8. Overwrite only the targeted first-month preliminary rows in the baseline artifact.
9. Run the existing validation flow, then upload one unified submission JSON.

Pseudocode:
```text
rows = expand(question_set)
submission = baseline_forecast(rows)
work_items = group_preliminary_dataset_questions(rows)
for item in work_items:
    if not has_first_month_rows(item):
        continue
    packet = build_intake_packet(item)
    evidence = full_map_phase(packet)
    probs = full_quantify_from_baseline(packet, evidence, submission)
    submission = overwrite_first_month_prelim_rows(submission, item, probs)
validate(submission)
upload(submission)
```

details [[forecastbench-workflow-synthesis]]
