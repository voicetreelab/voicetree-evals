---
color: blue
isContextNode: false
agent_name: Bob
---
# MBJ spike — files changed + load-bearing excerpts

One new generator (~700 LOC), one new verifier (~270 LOC), four small wiring edits. Protocol.py and runner.py untouched — the class-agnostic machinery carries MBJ without modification.

# Files changed

| File | Change | LOC |
|---|---|---|
| `kaggle_submission/generators/mbj.py` | **NEW**. Port of pilot generator + `generate(seed, difficulty)` façade + `DIFFICULTY_CONFIGS` + `_job_to_dict`. | ~700 |
| `kaggle_submission/verifiers/mbj.py` | **NEW**. `verify(instance, submission)`; docstring-extracted BEST_GUESS schema; independent of generator module (no cross-import). | ~270 |
| `kaggle_submission/verifiers/__init__.py` | Added `"mbj"` to `KNOWN_CLASSES`. | +1 |
| `kaggle_submission/harness/prompt.py` | Added `"mbj": "Masked Block Job-Shop"` to `CLASS_DISPLAY_NAMES`. | +1 |
| `kaggle_submission/harness/render_nl.py` | Added `_render_mbj` fallback + registry entry (unused in practice because `problem_statement` is embedded, but matches the pattern). | +9 |
| `kaggle_submission/scripts/build_questions.py` | Imported `mbj`, added `_build_mbj_row`, appended one row in `_build_rows()`. | +15 |

**Deliberately not touched:** `SOLO_CLASSES`, portfolio wiring, `HARD_PORTFOLIO_COMPONENT_CLASSES`, `harness/runner.py`, `harness/protocol.py`. Protocol is class-agnostic (parses BEST_GUESS as generic JSON object) — no per-class branching needed.

## `generators/mbj.py` — size-specialised configs

```python
DIFFICULTY_CONFIGS = {
    "medium": {
        "n_jobs": 8, "n_machines": 8,
        "min_baseline_gap_pct": 10.0,
        "min_heuristic_spread_pct": 3.0,
        "max_heuristic_spread_pct": 60.0,
        "cp_time_limit_s": 60.0,
        "max_generation_attempts": 24,
    },
    "hard": {"n_jobs": 12, "n_machines": 10, "cp_time_limit_s": 120.0, ...},
}
```

Pilot defaults were 25×15 with 600s CP-SAT budget — overkill for a spike. At 8×8 seed 1, generation + CP-SAT complete in ~30ms. Pilot assumed `n_machines >= 7`; I tightened to `>= 8` because `peripheral_machines[(2*family_id) % len(...)]` mod-indexes on a potentially empty list for n=7.

## `generators/mbj.py` — `generate()` matches the cjs exemplar shape

```python
def generate(seed: int, difficulty: str) -> dict[str, Any]:
    instance = build_instance(seed=seed, ...)
    return {
        "class": "mbj", "difficulty": difficulty, "seed": seed,
        "n_jobs": instance.n_jobs, "n_machines": instance.n_machines,
        "metric_name": "objective",
        "answer_contract": 'Object with "machines", "makespan", "weighted_tardiness", and "objective". ...',
        "jobs": [_job_to_dict(job) for job in instance.jobs],
        "baseline_submission": instance.baseline_schedule,
        "gold_submission": instance.optimal_schedule,
        "baseline_objective": 7167,  # seed 1
        "gold_objective": 5700,      # seed 1
        "baseline_gap_pct": 25.74,
        "problem_statement": instance.problem_statement,
    }
```

## `verifiers/mbj.py` — docstring drives registry schema extraction

```python
def verify(instance, submission) -> tuple[float, bool, dict]:
    """BEST_GUESS schema: {\"machines\": {\"M1\": [[\"J1\", 0, 3], ...], ...}, \"makespan\": 42, \"weighted_tardiness\": 18, \"objective\": 858}."""
    ...
```

`verifiers/__init__.py` auto-extracts this via the existing `_SCHEMA_RE` regex — no registry changes. Confirmed reachable: `CLASS_TO_BEST_GUESS_SCHEMA['mbj']` returns the dict-shape example used in `build_exec_prompt`.

## `scripts/build_questions.py` — one row, without touching SOLO_CLASSES

```python
rows = list(medium_rows)
# MBJ port spike: one medium row, kept out of SOLO_CLASSES so it does not
# contaminate portfolio assembly or hard-seed fallback loops.
rows.append(_annotate_row(_build_timed_row(_build_mbj_row, 1, "medium"), requested_seed=1))
rows.append(_build_portfolio_row(...))
```

## DIFF

```
# verifiers/__init__.py
-KNOWN_CLASSES = ("cjs", "graphcol", "mwis", "steiner", "tsp", "ve")
+KNOWN_CLASSES = ("cjs", "graphcol", "mbj", "mwis", "steiner", "tsp", "ve")
```

```
# harness/prompt.py
 CLASS_DISPLAY_NAMES = {
     "cjs": "Coupled Job-Shop",
     "graphcol": "Graph Coloring",
+    "mbj": "Masked Block Job-Shop",
     "mwis": "Maximum Weighted Independent Set",
     ...
 }
```

```
# scripts/build_questions.py
-from generators import cjs, graphcol, mwis, steiner, tsp, ve
+from generators import cjs, graphcol, mbj, mwis, steiner, tsp, ve

+def _build_mbj_row(seed, difficulty, *, config_override=None):
+    if config_override is not None:
+        raise RuntimeError("mbj does not expose a size override path from build_questions.py")
+    instance = mbj.generate(seed=seed, difficulty=difficulty)
+    row = _solo_row(cls="mbj", difficulty=difficulty, seed=seed, instance=instance,
+                    gold_objective=float(instance["gold_objective"]),
+                    baseline_objective=float(instance["baseline_objective"]))
+    return SmokeRow(row=row, notes="MBJ port spike — one row only, not yet in SOLO_CLASSES.")

# in _build_rows():
     rows = list(medium_rows)
+    rows.append(_annotate_row(_build_timed_row(_build_mbj_row, 1, "medium"), requested_seed=1))
     rows.append(_build_portfolio_row(...))
```

## Complexity: medium

New generator/verifier modules total ~970 LOC but are mostly a mechanical port with thin wrappers. The non-trivial judgement calls were (a) the CJS-vs-MBJ distinctness check, (b) keeping MBJ out of SOLO_CLASSES for the spike, and (c) shrinking DIFFICULTY_CONFIGS from the pilot's 25×15 to a fast 8×8.

### NOTES

- Protocol and runner untouched — class-agnostic infrastructure carries MBJ without modification. This is the biggest signal that the port path works: only generators/ + verifiers/ + the class registry needed changes.

implementation [[mbj-spike-landed]]
