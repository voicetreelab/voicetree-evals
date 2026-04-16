---
color: green
isContextNode: false
agent_name: Eli
---
# S0 Steiner Port

Ported the Steiner generator, verifier, and smoke fixture into `kaggle_submission/`. Medium seed-1 smoke passed, and the hard config also generated successfully on a spot check.

## Sources Read
- `hch/portfolio_spike/steiner_coloring_instance.py`
- `hch/portfolio_spike/steiner_coloring_gold.py`
- `hch/portfolio_spike/verify.py`
- `voicetree-16-4/task_1776349270555qg2.md`
- `voicetree-16-4/kaggle-submission-design.md`
- `voicetree-16-4/kaggle-submission-filetree.md`

## Deliverable
- `kaggle_submission/generators/steiner.py` now exposes `generate(seed: int, difficulty: str) -> dict`.
  It reuses the source graph-generation / baseline-construction logic and embeds exact solving for both `medium` (`n=8, k=4`) and `hard` (`n=12, k=4`).
- `kaggle_submission/verifiers/steiner.py` now exposes `verify(instance, submission) -> (gap_pct, feasible, details)`.
  It recomputes submission cost structurally, normalizes the artifact, and uses baseline fallback scoring when the answer is invalid.
- `kaggle_submission/tests/fixtures/steiner_smoke.json` freezes the generated `medium`, `seed=1` instance plus its gold submission.

## Smoke
Command:
```bash
python -c "from generators.steiner import generate; from verifiers.steiner import verify; inst = generate(seed=1, difficulty='medium'); import json; fixture = json.load(open('tests/fixtures/steiner_smoke.json')); s, f, d = verify(fixture['instance'], fixture['gold_submission']); assert f and s == 0.0, (s, f, d); print('OK')"
```
Output:
```text
OK
```
Extra hard-config spot check:
```python
{'difficulty': 'hard', 'seed': 2, 'n': 12, 'baseline_cost': 66, 'gold_cost': 48, 'baseline_gap_pct': 37.5}
```

## BEST_GUESS Schema
```json
{
  "edges": [["VillageA", "VillageB"], ["VillageB", "VillageC"]],
  "frequencies": {"VillageA": 1, "VillageB": 2, "VillageC": 1}
}
```

## Non-Mechanical Decisions
- Used CP-SAT inside the generator for the exact joint gold solve and the edge-only Steiner solve so the `hard` size remains tractable without relying on brute-force edge-subset enumeration.
- Kept the verifier lightweight by trusting `gold_cost` / `baseline_cost` embedded in the generated instance instead of rerunning the exact solver during verification.
- Returned baseline-based `gap_pct` when submissions are infeasible while still marking `feasible=False`, matching the prompt contract that invalid answers fall back to the baseline for scoring.

## Learnings
1. Tried to match the spike's brute-force gold path directly, then switched to CP-SAT because the `n=12` hard setting would make subset enumeration too expensive.
2. A future agent should not make the verifier recompute exact gold; the expensive work belongs in generation, not in per-answer scoring.
3. The useful mental model is: generator owns reproducibility plus exact gold, verifier owns cheap structural validation plus cost normalization plus baseline fallback.

## Files Changed

- kaggle_submission/generators/steiner.py
- kaggle_submission/verifiers/steiner.py
- kaggle_submission/tests/fixtures/steiner_smoke.json

### NOTES

- There are other untracked `kaggle_submission/` files from sibling work in the tree; this task only added the Steiner generator, verifier, and fixture.
- The medium seed-1 instance reproduces the expected portfolio-style costs: baseline `72`, gold `59`.

[[task_1776349270555qg2]]
