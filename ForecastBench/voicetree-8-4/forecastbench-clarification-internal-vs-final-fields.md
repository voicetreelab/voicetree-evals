---
color: green
isContextNode: false
agent_name: Ivan
---
# ForecastBench Clarification: Internal Versus Final Fields

Clarified that helper artifacts may carry extra internal fields like `days_until_resolution`, but the final submission JSON must stay on the strict ForecastBench schema.

Clarification:
- Extra fields such as `days_until_resolution`, `baseline_forecast`, or helper metadata are acceptable in internal pipeline artifacts like target manifests and updates templates.
- They should not appear in the final uploaded submission JSON.

Why the current setup is safe:
- `prepare_baseline_and_targets.py` writes those extra fields only into the manifest files.
- `make_target_updates_template.py` writes them only into the isolated updates file.
- `apply_target_updates.py` only copies `forecast` and optionally `reasoning` back into the submission rows.
- So the final submission file keeps the normal row shape: `id`, `source`, `forecast`, `resolution_date`, `reasoning`.

Rule of thumb:
- Internal files can be rich.
- Final submission file must stay strict.

[[1775712512821qMj]]
