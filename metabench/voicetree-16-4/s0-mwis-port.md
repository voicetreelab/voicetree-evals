---
color: green
isContextNode: false
agent_name: Eve
---
# S0 MWIS Port

Ported the MWIS generator and verifier into `kaggle_submission/`, added a smoke fixture, and validated the port locally. The only non-mechanical choice was the inferred difficulty split: `medium=120` nodes and `hard=140` nodes, because the source generator's `150/180` tiers failed their own separator pre-checks.

## Sources read
- `voicetree-16-4/task_1776349270575e4n.md`
- `voicetree-16-4/kaggle-submission-design.md`
- `voicetree-16-4/kaggle-submission-filetree.md`
- `hch/treewidth_mwis/graph_instance.py`
- `hch/treewidth_mwis/analyze.py`
- `hch/treewidth_mwis/run_spike.py`
- `hch/portfolio_spike/verify.py`

## Files written
- `kaggle_submission/generators/mwis.py`
- `kaggle_submission/verifiers/mwis.py`
- `kaggle_submission/tests/fixtures/mwis_smoke.json`

## BEST_GUESS schema
```json
{
  "selected_vertices": ["V001", "V014", "V077"],
  "total_weight": 123
}
```

## Smoke result
Required smoke command from `kaggle_submission/`:
```sh
python -c "from generators.mwis import generate; from verifiers.mwis import verify; inst = generate(seed=1, difficulty='medium'); import json; fixture = json.load(open('tests/fixtures/mwis_smoke.json')); s, f, d = verify(fixture['instance'], fixture['gold_submission']); assert f and s == 0.0, (s, f, d); print('OK')"
```
Output:
```text
OK
```

Additional sanity checks:
```sh
python -m py_compile generators/mwis.py verifiers/mwis.py
python -c "from generators.mwis import generate; from verifiers.mwis import verify; inst = generate(seed=1, difficulty='medium'); s, f, d = verify(inst, inst['optimal_answer']); assert f and s == 0.0, (s, f, d); print(inst['n_nodes'], inst['optimal_objective'], inst['baseline_objective'])"
python -c "from generators.mwis import generate; inst = generate(seed=1, difficulty='hard'); print(inst['n_nodes'], inst['optimal_objective'], inst['baseline_objective'])"
```
Outputs:
```text
120 542 480
140 436 387
```

## Non-mechanical decisions
- Difficulty mapping had to be inferred because `hch/treewidth_mwis/graph_instance.py` exposes a size knob, not explicit `medium`/`hard` tiers.
- Final mapping is `medium=120` and `hard=140`.
- Rejected `hard=150` and `hard=180` because they repeatedly failed the source generator's own bridge/separator pre-flight check for seed 1.
- Rejected a gap-only hardening strategy on `120` because `build_instance()` falls through to the unstable `150/180` sizes when the tighter gap threshold is not met.
- The verifier returns `gap_pct=100.0` on infeasible submissions so invalid `BEST_GUESS` payloads cleanly map to zero downstream score.

## Learnings
1. Tried a size-based hard tier at `180`, then `150`; switched to `140` because the larger sizes were not deterministic under the source generator's separator constraint.
2. Do not assume the original `size_queue` is a usable difficulty ladder. In the source code it is a fallback path for `120`, not evidence that `150` or `180` are stable standalone tiers.
3. The safe mental model is: keep the MWIS verifier fully self-contained, preserve the source generation logic closely, and treat difficulty as an adapter layer on top of a generator that was originally built for a single canonical size.

## Files Changed

- kaggle_submission/generators/mwis.py
- kaggle_submission/verifiers/mwis.py
- kaggle_submission/tests/fixtures/mwis_smoke.json

[[task_1776349270575e4n]]
