---
color: green
isContextNode: false
agent_name: Hana
---
# S2 Smoke Questions Complete

Built `kaggle_submission/scripts/build_smoke_questions.py`, generated the 7-row smoke `questions.jsonl` and `gold/gold.jsonl`, and validated JSON round-trip plus infeasible-path checks for all six solo verifiers. The portfolio row samples CJS, Steiner, and TSP and carries prompt-ready metadata plus full component sub-instances for later integration.

## Row Table

| id | class | seed | gold_objective | baseline_objective | value_cap | notes |
|---|---|---:|---:|---:|---:|---|
| `cjs_medium_seed1` | `cjs` | 1 | 90.0 | 155.0 | 100.0 | exact CP-SAT makespan rechecked from parsed jobs via `solve_exact_schedule(...)` |
| `steiner_medium_seed1` | `steiner` | 1 | 59.0 | 72.0 | 100.0 | exact joint CP-SAT optimum rechecked via `_solve_joint_optimum(instance, seed=1)` |
| `graphcol_medium_seed1` | `graphcol` | 1 | 4.0 | 20.0 | 100.0 | exact coloring rechecked via `_solve_exact_coloring(...)`; zero conflicts at optimum |
| `tsp_medium_seed1` | `tsp` | 1 | 470.14629428718786 | 588.2206603869462 | 100.0 | exact tour rechecked via `solve_exact_tour(coords)` |
| `mwis_medium_seed1` | `mwis` | 1 | 542.0 | 480.0 | 100.0 | exact MWIS rechecked via `solve_exact_mwis(...)`; `n_nodes=120` |
| `ve_medium_seed1` | `ve` | 1 | 0.49014481565752194 | 0.5 | 100.0 | exact posterior rechecked via `evaluate_exact_probability(...)`; baseline kept as trivial `0.5` heuristic TODO |
| `portfolio_medium_seed1` | `portfolio` | 1 | 100.0 | 0.0 | 100.0 | components = `cjs_medium_seed1`, `steiner_medium_seed1`, `tsp_medium_seed1`; value caps `33/33/34` |

## Gold Recompute Method

- `cjs`: reconstructed `JobSpec` / `OperationSpec` from the generated JSON payload and reran `generators.cjs.solve_exact_schedule(jobs, n_machines)`.
- `steiner`: reran `generators.steiner._solve_joint_optimum(instance, seed)` on the generated instance dict.
- `graphcol`: rebuilt `GraphColoringInstance` from the JSON payload and reran `generators.graphcol._solve_exact_coloring(instance)`.
- `tsp`: converted `coords` back to tuples and reran `generators.tsp.solve_exact_tour(coords)`.
- `mwis`: rebuilt `vertices`, `weights`, and `edges` from the JSON payload and reran `generators.mwis.solve_exact_mwis(...)`; required `is_optimal=True`.
- `ve`: parsed the generated payload back into `BayesianVEInstance` with `verifiers.ve._instance_from_payload(...)` and reran `evaluate_exact_probability(instance, instance.gold_ordering)` to recheck `exact_posterior`.

## Portfolio Row

Top-level row:

```json
{
  "id": "portfolio_medium_seed1",
  "class": "portfolio",
  "difficulty": "medium",
  "seed": 1,
  "gold_objective": 100.0,
  "baseline_objective": 0.0,
  "value_cap": 100.0,
  "wall_budget_s": 1800,
  "components": [
    {"problem_id": "cjs_medium_seed1", "class": "cjs", "value_cap": 33.0, "sub_instance": "<full cjs instance>"},
    {"problem_id": "steiner_medium_seed1", "class": "steiner", "value_cap": 33.0, "sub_instance": "<full steiner instance>"},
    {"problem_id": "tsp_medium_seed1", "class": "tsp", "value_cap": 34.0, "sub_instance": "<full tsp instance>"}
  ]
}
```

Portfolio `instance` is a prompt-bearing summary object with `problem_statement`, `seed`, `difficulty`, and `n_components`. I used `gold_objective=100.0` and `baseline_objective=0.0` as the economic ceiling/floor for the value-capture scoring path because no portfolio verifier or runner exists yet in the checkout.

## Validation

Commands run:

```bash
cd kaggle_submission
python -m py_compile scripts/build_smoke_questions.py
python scripts/build_smoke_questions.py
wc -l questions.jsonl gold/gold.jsonl
```

Observed output:

```text
Wrote 7 rows to questions.jsonl; 7 rows to gold/gold.jsonl. Verified schema round-trip.
       7 questions.jsonl
       7 gold/gold.jsonl
      14 total
```

Schema round-trip verdict:
- Every row round-tripped through `json.dumps`/`json.loads` cleanly.
- For the six solo rows, passing a trivial wrong submission (`{}` or `[]` for TSP) to the registered verifier produced `feasible=False`, confirming the row payloads can be consumed by the existing verifier registry.
- Portfolio row validation is structural only for now: `components` length is 3 and component `value_cap` sums to 100.0.

## Learnings

1. Tried to rely on the sibling smoke fixture files as the sole seed contract, then switched to the live generators and S0 notes because the MWIS fixture in `tests/fixtures/mwis_smoke.json` is a tiny `seed=0`, `difficulty=smoke` fixture, while the real smoke-safe row for this task is `seed=1`, `difficulty=medium`.
2. Do not assume VE’s top-level `gold_objective` / `baseline_objective` is already settled by the current codebase. The verifier scores posterior error against `exact_posterior`, while the payload also exposes ordering-peak metadata. For smoke I used `gold_objective=exact_posterior` and `baseline_objective=0.5` as a trivial heuristic, and I left the richer ordering metadata inside `instance` for later refinement.
3. The portfolio schema is ahead of the live implementation: there is no portfolio verifier or runner in `kaggle_submission/` yet. The safest dataset shape is therefore one that keeps prompt-ready summary text plus full `sub_instance` payloads, so Ben can integrate against it without losing information.


## Files Changed

- kaggle_submission/scripts/build_smoke_questions.py
- kaggle_submission/questions.jsonl
- kaggle_submission/gold/gold.jsonl

### NOTES

- The task brief’s write path still says `metabench/kaggle_submission/...`, but the live checkout path is `kaggle_submission/...` at repo root; writes were made there.
- VE baseline metadata is the only row still carrying a semantic TODO. It does not block smoke because current solo verifiers score directly from `instance`, not from the top-level row metadata.
- `mwis_medium_seed2` is not stable in the current generator (`bridge nodes did not separate the graph`), so the hand-picked `seed=1` choice is materially safer than assuming all nearby seeds work.

## Related

- [task_17763501122159u5](task_17763501122159u5.md)
- [s0-mwis-port](s0-mwis-port.md)
- [s0-ve-port](s0-ve-port.md)

[[task_17763501122159u5]]
