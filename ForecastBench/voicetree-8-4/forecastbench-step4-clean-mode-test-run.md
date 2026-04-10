---
color: green
isContextNode: false
agent_name: Ivan
---
# ForecastBench Step 4 Clean Mode Test Run

Ran the simplified Step 4 helper end-to-end on the downloaded `2026-03-29-llm.json` round and verified that it produced the baseline artifact plus the two first-month preliminary target manifests.

Test run performed:
1. Created a fresh skeleton in `/private/tmp/2026-03-29.ForecastBench.step4-simple-test.json` from the downloaded round file.
2. Ran:
```bash
cd /Users/lochlan/voicetree-evals/forecastbench-src && python3 scratch/prepare_baseline_and_targets.py scratch/question_sets/2026-03-29-llm.json /private/tmp/2026-03-29.ForecastBench.step4-simple-test.json
```
3. Observed output:
```text
Wrote baseline submission: /private/tmp/2026-03-29.ForecastBench.step4-simple-test.json
Wrote safety-net baseline copy: /private/tmp/2026-03-29.ForecastBench.step4-simple-test.baseline.json
Wrote target-row manifest: /private/tmp/2026-03-29.ForecastBench.step4-simple-test.first-month-preliminary-rows.json
Wrote grouped target manifest: /private/tmp/2026-03-29.ForecastBench.step4-simple-test.first-month-preliminary-groups.json
Dataset baseline mode: simple
Forecast rows: 2248
Market rows: 250
Dataset rows: 1998
First-month preliminary target rows: 498
First-month preliminary target questions: 250
```

Output spot checks:
- Sample market row used the round file's market probability: `0.215119014138537` for the first `manifold` question.
- Sample dataset row used the simple dataset baseline: `0.5` for the first `acled` row.
- The grouped target manifest correctly split one dataset question into two first-month target dates and six longer-horizon non-target dates.

Learnings
- The test confirms the exact targeting shape for the current round: 498 first-month preliminary rows across all 250 dataset questions.
- Writing the temporary test artifacts to `/private/tmp` avoided sandbox issues with creating new files in the sibling repo checkout.

verified by [[forecastbench-clean-step4-mode]]
