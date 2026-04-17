---
color: blue
isContextNode: false
agent_name: Amit
---
# Mechanism — the 4 code paths that drop sub-component data

Four upstream defects compose: (1) render_nl only emits top-level problem_statement; (2) schema block is empty for portfolio; (3) initial best-guess seeding only reads baseline_submission; (4) infer_feasible ANDs across components. Details + citations inside.

## 1. `render_nl` returns only the portfolio `problem_statement`

`kaggle_submission/harness/render_nl.py:7-16`:
```python
def render_nl(instance: dict[str, Any], cls: str) -> str:
    if not isinstance(instance, dict):
        raise TypeError("instance must be a dict")
    problem_statement = instance.get("problem_statement")
    if isinstance(problem_statement, str) and problem_statement.strip():
        return problem_statement
    renderer = _FALLBACK_RENDERERS.get(cls, _render_generic)
    return renderer(instance)
```

For `cls="portfolio"` the `portfolio_instance` (see `build_questions.py:371-377`) has `problem_statement` = the short bullet list built by `_portfolio_problem_statement(components)` (lines 329-348):

```
You are allocating effort across a three-problem optimization portfolio.
...
Portfolio components:
- cjs_medium_seed14 | class=cjs | value_cap=33.0
- mwis_medium_seed14 | class=mwis | value_cap=33.0
- steiner_medium_seed14 | class=steiner | value_cap=34.0

Return answers for the listed sub-problems using the component-specific answer contracts.
```

No graph edges, no jobs data, no coords, no per-class answer_contract. The phrase "the component-specific answer contracts" is a dangling reference — the model is never shown them.

## 2. `_best_guess_schema_block(cls="portfolio")` is a no-op

`kaggle_submission/harness/prompt.py:206-215`:
```python
def _best_guess_schema_block(cls: str) -> str:
    try:
        from verifiers import CLASS_TO_BEST_GUESS_SCHEMA
    except Exception:
        return "- BEST_GUESS schema example unavailable until verifier registries are in place."
    schema = CLASS_TO_BEST_GUESS_SCHEMA.get(cls)
    if not schema:
        return f"- BEST_GUESS schema example unavailable for `{cls}`."
    return f"- BEST_GUESS schema example for `{cls}`:\n```json\n{schema}\n```"
```

`CLASS_TO_BEST_GUESS_SCHEMA` is populated from `verifiers/{cjs,graphcol,mwis,steiner,tsp,ve}.py` docstrings (`verifiers/__init__.py:14-29`). There is no `verifiers/portfolio.py`, so `CLASS_TO_BEST_GUESS_SCHEMA["portfolio"]` is missing — the exec prompt literally tells the model the schema is unavailable.

## 3. `_initial_best_guess` silently drops MWIS and TSP baselines

`kaggle_submission/harness/runner.py:472-495`:
```python
for component in components:
    ...
    baseline_submission = sub_instance.get("baseline_submission")
    if baseline_submission is not None:
        answers[problem_id] = baseline_submission
```

Key-name audit in `question.json` for seed14/seed5:
- `cjs.*` sub_instance has `baseline_submission` ✓
- `steiner.*` sub_instance has `baseline_submission` ✓
- `graphcol.*` sub_instance has `baseline_submission` ✓ (inferred; not audited here)
- `mwis.*` sub_instance has `baseline_answer` (see `question.json:967`) — **skipped**
- `tsp.*` sub_instance has `baseline_tour` (see `question.json:1208`) — **skipped**
- `ve.*` — not audited, likely also divergent

Net: CURRENT_BEST_JSON is missing MWIS and TSP entries entirely. Combined with (1)+(2), the model has zero evidence of what keys MWIS or TSP expect.

## 4. `infer_feasible` is AND across components

`kaggle_submission/scripts/run_kaggle_production.py:241-246`:
```python
def infer_feasible(evaluation):
    if evaluation.get("mode") == "portfolio":
        return bool(evaluation.get("components")) and all(
            bool(component.get("feasible")) for component in evaluation["components"]
        )
    return bool(evaluation.get("feasible"))
```

One broken sub-component ⇒ the row's `feasible` flag is False. Partial-credit score is still awarded by `score_portfolio` per-component (`harness/scoring.py:12-23`), but the boolean leaderboard metric collapses.

mechanism [[portfolio-infeasibility-root]]
