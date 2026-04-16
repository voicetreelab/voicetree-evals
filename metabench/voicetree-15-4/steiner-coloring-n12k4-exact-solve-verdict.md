---
color: green
isContextNode: false
agent_name: Ren
---
# Steiner-coloring n=12,k=4 exact-solve verdict

Evaluated exact-solve feasibility for the current generated `hch/steiner_coloring_spike` case at `seed=1, n=12, k=4`. Result: SCIP-Jack is not a quick drop-in path for this turn, and the current brute-force gold solver is not feasible under 30 minutes on the current graph.

## Outcome
The task split into two checks:
1. Can SCIP-Jack be downloaded and used quickly for this exact case?
2. If not, can the repo's current brute-force exact solver handle the generated `n=12, k=4` case within 30 minutes?

Verdict:
- `SCIP-Jack`: no quick path in this turn. The official site now distributes it only on request, and it does not directly solve the full Steiner-plus-coloring objective used by this spike.
- Current brute-force exact solver: not feasible under 30 minutes for the current generated `seed=1, n=12, k=4` instance. The measured projection is about `1.0 hour` for one `solve_joint_optimum()` pass and `2+ hours` for the `build_instance()` path that runs two exact passes.

## Environment
- macOS `15.7.3` on `arm64`
- Python `3.13.12`

## Learnings
- Tried the SCIP-Jack route first because it is the obvious exact Steiner candidate, then switched because both distribution and formulation were blockers.
- The dominant variable here is not just `n`; it is graph edge count `m`. At `m=32`, the current exhaustive edge-subset solver is already beyond the 30-minute target.
- A successor should treat this as an algorithm-class problem, not a minor optimization problem: either sparsify the generated graph substantially or replace the exact method entirely.

### NOTES

- No files changed.
- This work stayed within exact-solve feasibility and avoided the main agent's protocol/prompt edits.

## Related

- [task_1776331013767452](task_1776331013767452.md)
- [steiner-coloring-minimal-plan-turn-adjustment](steiner-coloring-minimal-plan-turn-adjustment.md)

[[task_1776331013767452]]
