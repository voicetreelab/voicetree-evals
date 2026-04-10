---
color: green
isContextNode: false
agent_name: Ivan
---
# ForecastBench Targeted Updates Interface

Implemented a clean two-step interface after Step 4: build an isolated updates template containing only targeted first-month preliminary rows, then merge a filled updates file back onto the baseline submission. Verified the contract end-to-end with a synthetic merge test.

Implemented files:
- `scratch/make_target_updates_template.py`
- `scratch/apply_target_updates.py`
- updated `scratch/gameplan.md`

What the new interface does:
- `make_target_updates_template.py` reads the Step 4 baseline submission plus the first-month preliminary row manifest and writes a clean updates template containing only targeted rows.
- Each update row includes `id`, `source`, `resolution_date`, `baseline_forecast`, `forecast`, and `reasoning`.
- `apply_target_updates.py` reads a baseline submission plus a filled updates file and overwrites only the listed rows.

End-to-end verification:
- Built a target updates template from the real Step 4 test artifacts in `/private/tmp`.
- Filled that template synthetically by copying baseline forecasts into all rows and changing the first targeted row to `0.61` with reasoning `synthetic merge test`.
- Merged the filled updates file back onto the baseline submission.
- Verified that:
  - the targeted first-month row changed from `0.5` to `0.61`
  - a longer-horizon non-target row on the same question stayed at `0.5`
  - a market row stayed at its original market-based baseline value `0.215119014138537`

Why this matters:
- The future strong workflow no longer needs to touch the full baseline submission directly.
- It can operate on a small isolated updates file containing only the targeted rows, then hand that file to the merge script.
- This cleanly separates expensive reasoning from the safe baseline artifact.

Learnings
- The right contract boundary is row-level updates keyed by `(id, source, resolution_date)`.
- The grouped manifest remains the best orchestration input for question-level reasoning, while the updates file is the best merge/output contract.
- The narrow-overwrite rule is now enforced by structure, not just by convention.

## Files Changed

- /Users/lochlan/voicetree-evals/forecastbench-src/scratch/make_target_updates_template.py
- /Users/lochlan/voicetree-evals/forecastbench-src/scratch/apply_target_updates.py
- /Users/lochlan/voicetree-evals/forecastbench-src/scratch/gameplan.md

### NOTES

- The synthetic merge test used `/private/tmp` artifacts to avoid sandbox write restrictions in the sibling repo checkout.
- The next implementation step should target the grouped manifest and emit a filled updates file, leaving the merge contract unchanged.

[[1775712512821qMj]]
