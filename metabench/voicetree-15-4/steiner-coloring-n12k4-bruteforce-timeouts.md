---
color: green
isContextNode: false
agent_name: Ren
---
# Direct timeouts from the unmodified exact solver

Ran the unmodified exact solver and the no-retry `build_instance()` path under hard 120-second alarms. Both timed out cleanly, matching the runtime estimate and ruling out a sub-30-minute solve on the current seed-1 graph.

## Direct timeout: `solve_joint_optimum(instance)`
This run used the unmodified code on the generated `seed=1, n=12, k=4` instance with a hard `120s` alarm.

Observed output:
```text
status timeout
elapsed_s 120.00213000003714
```

## Direct timeout: `build_instance()` with retries disabled
This run used:
```bash
build_instance(seed=1, n=12, k=4, min_baseline_gap_pct=0.0, require_coupling=False, max_generation_attempts=1)
```
with a hard `120s` alarm.

Observed output:
```text
status timeout
elapsed_s 120.00452491699252
```

## Interpretation
- The issue is not retry churn; even the no-retry build path fails to complete inside two minutes.
- Because `build_instance()` performs two exact passes (`cable_only` and `joint`), the empirical timeout result is consistent with the separate `~1 hour` per-pass estimate.

## Conclusion
The current brute-force exact solver does not satisfy the `under 30 minutes` requirement for the current generated `seed=1, n=12, k=4` case.

supports [[steiner-coloring-n12k4-exact-solve-verdict]]
