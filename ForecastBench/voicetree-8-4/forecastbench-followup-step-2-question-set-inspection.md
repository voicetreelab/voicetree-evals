---
color: green
isContextNode: false
agent_name: Aki
---
# ForecastBench Follow-up: Step 2 Question Set Inspection

Prepared the next step after cloning: download the current public question set into the real repo checkout, verify the latest pointer, and inspect the exact market/dataset structure that a submission must cover.

Step 2 goal
- Pull down the current public LLM question set.
- Verify the forecast due date and question count.
- Inspect how market and dataset questions differ in `resolution_dates`.

Commands to run
```bash
cd /Users/lochlan/voicetree-evals/forecastbench-src
mkdir -p scratch/question_sets scratch/submissions
LATEST=$(curl -sS https://raw.githubusercontent.com/forecastingresearch/forecastbench-datasets/main/datasets/question_sets/latest-llm.json)
echo "$LATEST"
curl -sS "https://raw.githubusercontent.com/forecastingresearch/forecastbench-datasets/main/datasets/question_sets/$LATEST" -o "scratch/question_sets/$LATEST"
```

Inspect the file:
```bash
jq '{forecast_due_date, question_set, n_questions:(.questions|length)}' "scratch/question_sets/$LATEST"
jq '[.questions[] | select(.resolution_dates == "N/A")] | length' "scratch/question_sets/$LATEST"
jq '[.questions[] | select(.resolution_dates != "N/A")] | length' "scratch/question_sets/$LATEST"
```

Inspect example rows:
```bash
jq '.questions[0] | {id, source, resolution_dates, question}' "scratch/question_sets/$LATEST"
jq 'first(.questions[] | select(.resolution_dates != "N/A") | {id, source, resolution_dates, question})' "scratch/question_sets/$LATEST"
```

Expected result
- On 2026-04-08, `LATEST` should print `2026-03-29-llm.json`.
- The total question count should be `500`.
- Market questions should have `resolution_dates == "N/A"`.
- Dataset questions should have `resolution_dates` as an array of ISO dates.

Why this matters
- We want our local generator to match the live public input format, not just the repo code in the abstract.
- This is the cleanest way to see how many forecast rows we will eventually need to emit in the submission JSON.

Learnings
- The live pointer file is simple and public, so the safest workflow is to resolve `latest-llm.json` first instead of hardcoding a date.
- The key structural distinction is not source name alone; it is whether `resolution_dates` is `"N/A"` or a list.
- After this step, the next natural move is generating a starter submission skeleton from this question-set file.

## Related

- [forecastbench-followup-step-1-setup-commands](forecastbench-followup-step-1-setup-commands.md)
- [forecastbench-execution-submission-plan-apr-2026](forecastbench-execution-submission-plan-apr-2026.md)

[[1775618897236Woz]]
