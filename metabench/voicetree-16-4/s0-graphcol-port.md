---
color: green
isContextNode: false
agent_name: Emi
---
# S0 GraphCol Port

Ported the GraphCol generator, verifier, and smoke fixture into `kaggle_submission/`. Smoke passed from `kaggle_submission/` using the required command; non-mechanical choice was tightening the difficulty thresholds to keep `hard` distinct under the source generator’s native 200–400% headroom.

## Sources Read
- `voicetree-16-4/ctx-nodes/task_1776349270562npb_context_1776349270564.md`
- `.voicetree/prompts/addProgressTree.md`
- `voicetree-16-4/kaggle-submission-design.md`
- `voicetree-16-4/kaggle-submission-filetree.md`
- `voicetree-16-4/task_17763490260491fj.md`
- `hch/portfolio_spike/graph_coloring_instance.py`
- `hch/portfolio_spike/portfolio_problem.py`
- `voicetree-16-4/factory-plan.md`
- `voicetree-16-4/1776343402673uBv.md`

## Files Written
- `kaggle_submission/generators/graphcol.py`
- `kaggle_submission/verifiers/graphcol.py`
- `kaggle_submission/tests/fixtures/graphcol_smoke.json`

## BEST_GUESS Schema
```json
{"assignment": {"N01": 1, "N02": 3, "...": 4}}
```
Every node listed in `instance["nodes"]` must appear exactly once. Colors must be integers in `1..instance["num_colors"]`.

## Smoke
Command run from `kaggle_submission/`:
```bash
python -c "from generators.graphcol import generate; from verifiers.graphcol import verify; inst = generate(seed=1, difficulty='medium'); import json; fixture = json.load(open('tests/fixtures/graphcol_smoke.json')); s, f, d = verify(fixture['instance'], fixture['gold_submission']); assert f and s == 0.0, (s, f, d); print('OK')"
```
Result:
```text
OK
```

## Decisions
- Kept the port mechanical: generator logic is copied from `graph_coloring_instance.py` with the same 30-node construction, greedy baseline, and CP-SAT exact solve.
- Made the verifier standalone instead of importing generator internals so it can be embedded later without depending on `generators/`.
- Difficulty remains source-native and headroom-based. After sampling seeds 1–10, native baseline gaps were `200%` to `400%`, so the initial `15/30` thresholds were not meaningful. Final mapping is `medium=200.0`, `hard=300.0`.

## Learnings
- Tried `medium=15.0` / `hard=30.0` first, then switched to `200.0` / `300.0` because the source graph-color generator already produces very large baseline gaps and the lower thresholds made both tiers effectively identical.
- Future agents should not mark conflicting assignments infeasible for this class. Feasibility here is schema-valid assignment; the objective is `4 + conflicts`, and `gap_pct` is measured against `gold_scored_cost`.
- The meaningful mental model is: GraphCol difficulty is not yet a size ladder in the source tree; it is a filtered sample from a fixed 30-node family, using baseline headroom as the only native control.

## Files Changed

- kaggle_submission/generators/graphcol.py
- kaggle_submission/verifiers/graphcol.py
- kaggle_submission/tests/fixtures/graphcol_smoke.json

### NOTES

- Verifier treats any complete integer assignment as feasible; conflicts contribute to objective rather than invalidating the submission.
- GraphCol source generator has fixed 30-node structure; the only native difficulty knob is minimum baseline-gap headroom, so difficulty remains headroom-based rather than size-based.
- Initial `15/30` thresholds collapsed medium and hard because sampled native gaps were 200–400%; tightened to `200/300` after local sampling so `hard` forces higher-headroom retries on several seeds.

## Related

- [task_1776349270562npb](task_1776349270562npb.md)
- [kaggle-submission-design](kaggle-submission-design.md)
- [kaggle-submission-filetree](kaggle-submission-filetree.md)

[[task_1776349270562npb]]
