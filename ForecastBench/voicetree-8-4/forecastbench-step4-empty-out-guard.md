---
color: green
isContextNode: false
agent_name: Ivan
---
# ForecastBench Step 4 Empty OUT Guard

Added a clearer validation error to `prepare_baseline_and_targets.py` so an empty or unset submission path fails fast with a helpful message instead of raising `IsADirectoryError` on the repo root.

Problem:
- Running `python3 scratch/prepare_baseline_and_targets.py ... "$OUT"` with `OUT` unset or empty caused `Path("").resolve()` to become the current repo directory.
- The script then tried to open that directory as JSON and raised `IsADirectoryError`.

Fix:
- Added an explicit empty-string guard in `main()`.
- Added a directory-path guard in `load_submission()`.

Verified behavior:
```bash
cd /Users/lochlan/voicetree-evals/forecastbench-src && python3 scratch/prepare_baseline_and_targets.py scratch/question_sets/2026-03-29-llm.json ''
```
Now raises:
```text
ValueError: Submission path is empty. Recompute OUT first, for example:
OUT=$(ls -t scratch/submissions/*.json | head -n 1)
```


## Files Changed

- /Users/lochlan/voicetree-evals/forecastbench-src/scratch/prepare_baseline_and_targets.py

### NOTES

- This was a usability fix only; the actual Step 4 behavior is unchanged.

[[1775712512821qMj]]
