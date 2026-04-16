---
color: green
isContextNode: false
agent_name: Dan
---
# S0 CJS Port

Ported the coupled-job-shop generator, verifier, and frozen smoke fixture into `kaggle_submission/`. The required smoke command passes, and the exact solver path was made deterministic so repeated same-seed generation is stable.

## Sources Read
- `hch/portfolio_spike/jobshop_instance.py`
- `hch/portfolio_spike/portfolio_problem.py`
- `hch/portfolio_spike/EXPERIMENT_SPEC.md`
- `hch/masked_block_jobshop/jobshop_instance.py`
- `voicetree-16-4/kaggle-submission-filetree.md`
- `voicetree-16-4/kaggle-submission-design.md`
- `voicetree-16-4/factory-plan.md`
- `voicetree-16-4/task_17763492705484kf.md`

## Files Written
- `kaggle_submission/generators/cjs.py`
- `kaggle_submission/verifiers/cjs.py`
- `kaggle_submission/tests/fixtures/cjs_smoke.json`

## Smoke Result
Command:
`cd kaggle_submission && python -c "from generators.cjs import generate; from verifiers.cjs import verify; inst = generate(seed=1, difficulty='medium'); import json; fixture = json.load(open('tests/fixtures/cjs_smoke.json')); s, f, d = verify(fixture['instance'], fixture['gold_submission']); assert f and s == 0.0, (s, f, d); print('OK')"`
Result:
`OK`

Hard sanity:
`generate(seed=1, difficulty='hard') -> {'difficulty': 'hard', 'n_jobs': 6, 'n_machines': 7, 'gold_objective': 106, 'baseline_objective': 216}`

## BEST_GUESS Schema
```json
{
  "factory_a": {"MA1": [["J1", 0, 3]]},
  "factory_b": {"MB1": [["J1", 3, 5]]},
  "makespan": 42
}
```

## Decisions
- Treated `cjs` as the coupled job-shop class from `portfolio_spike/jobshop_instance.py`; `masked_block_jobshop` only informed prompt/contract context and harder-instance background.
- Mapped `medium -> 5x6` to preserve the documented smoke path and `hard -> 6x7` from the portfolio spike spec.
- Kept `verifiers/cjs.py` self-contained because `verifiers/` is embedded into `task.py` but `generators/` is not.
- Forced exact solve determinism with `num_search_workers=1` and `random_seed=0` after same-seed multithreaded solves produced different optimal schedules.

## Learnings
1. Tried a direct multi-worker port from the source, switched to a deterministic single-worker exact solve because repeated `generate(seed=1, difficulty='medium')` calls returned different optimal schedules.
2. Do not regenerate the smoke fixture from two separate generator calls unless the exact solver is deterministic; the instance can stay the same while the optimal schedule changes across alternate optima.
3. The portable contract here is: generator returns JSON with jobs plus baseline/gold metadata, verifier computes gap from `gold_objective`, and the LLM output schema stays the simple `{factory_a, factory_b, makespan}` schedule object.


## Files Changed

- kaggle_submission/generators/cjs.py
- kaggle_submission/verifiers/cjs.py
- kaggle_submission/tests/fixtures/cjs_smoke.json

### NOTES

- All three authored files are currently untracked in git.
- The verifier returns `100.0` gap for infeasible submissions so downstream economic scoring clips to zero reward instead of producing NaN/inf.

[[task_17763492705484kf]]
