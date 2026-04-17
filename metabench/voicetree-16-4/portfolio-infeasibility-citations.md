---
color: blue
isContextNode: false
agent_name: Amit
---
# Citations — file:line map

Authoritative pointers for every code path referenced in mechanism and fix.

| Concern | File | Lines |
|---|---|---|
| Portfolio NL rendering | `kaggle_submission/harness/render_nl.py` | 7-16 |
| Portfolio problem_statement construction | `kaggle_submission/scripts/build_questions.py` | 329-348 |
| Per-class BEST_GUESS schema block | `kaggle_submission/harness/prompt.py` | 206-215 |
| Schema registry build | `kaggle_submission/verifiers/__init__.py` | 14-29 |
| Initial current_best seeding | `kaggle_submission/harness/runner.py` | 472-495 |
| Portfolio evaluation | `kaggle_submission/harness/runner.py` | 529-591 |
| Portfolio `feasible` inference (AND) | `kaggle_submission/scripts/run_kaggle_production.py` | 241-246 |
| Portfolio partial-credit score | `kaggle_submission/harness/scoring.py` | 12-23 |
| MWIS verifier (wants `selected_vertices`) | `kaggle_submission/verifiers/mwis.py` | 17, 181-183 |
| TSP verifier (wants tour length == N) | `kaggle_submission/verifiers/tsp.py` | 63-65 |

Also: the exec prompt assembly `kaggle_submission/harness/prompt.py:85-144` shows that `instance_nl`, `current_best_block`, and `schema_block` are the three channels by which per-class content reaches the model — all three drop portfolio sub-component detail.

citations [[portfolio-infeasibility-root]]
