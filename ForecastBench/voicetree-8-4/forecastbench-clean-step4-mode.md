---
color: green
isContextNode: false
agent_name: Ivan
---
# ForecastBench Clean Step 4 Mode

Simplified Step 4 so it runs from the latest question set alone by default, while keeping the source-aware dataset baseline as an optional enhanced mode.

Implementation change:
- `scratch/prepare_baseline_and_targets.py` now defaults to `--dataset-baseline-mode simple`.
- In simple mode, dataset rows use a constant fallback probability (`0.5` by default).
- Market rows still use `freeze_datetime_value` when available, else `0.5`.
- The heavier source-aware dataset baseline is still available via `--dataset-baseline-mode source-aware --question-bank-dir ...`.
- `scratch/gameplan.md` now documents the clean default command and the optional enhanced mode.

Why this change helps:
- The public round file is now sufficient for the standard Step 4 path.
- The source-aware dataset baseline remains available, but it is no longer a required operational dependency.
- This keeps the day-of path aligned with the actual benchmark priority: spend real effort only on first-month preliminary rows.

Learnings
- The clean operational boundary is now much better: Step 1 provides enough input for the standard Step 4 run.
- The source-aware baseline is still useful, but it belongs in an opt-in enhanced path rather than the default day-of path.

[[1775712512821qMj]]
