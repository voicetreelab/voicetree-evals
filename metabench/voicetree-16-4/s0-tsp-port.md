---
color: green
isContextNode: false
agent_name: Eva
---
# S0 TSP Port

Ported the TSP generator, verifier, and smoke fixture into `kaggle_submission/`. Smoke check passed with `OK`; TSP BEST_GUESS is now documented as `{"tour": [...]}` while the verifier remains backward-compatible with a raw list.

## Sources Read
- `voicetree-16-4/task_1776349270569uld.md`
- `voicetree-16-4/kaggle-submission-design.md`
- `voicetree-16-4/kaggle-submission-filetree.md`
- `hch/portfolio_spike/tsp_instance.py`
- `hch/portfolio_spike/portfolio_problem.py`
- `.voicetree/prompts/addProgressTree.md`

## Outcome
- Added `kaggle_submission/generators/tsp.py` by porting the Euclidean TSP-20 instance builder, nearest-neighbor baseline, exact CP-SAT solver, and NL rendering from the spike.
- Added `kaggle_submission/verifiers/tsp.py` with feasibility checks, tour normalization, gap computation, and the required BEST_GUESS schema docstring.
- Added `kaggle_submission/tests/fixtures/tsp_smoke.json` for one medium seed-1 instance with the gold tour and expected zero gap.

## Smoke Result
```text
$ python -c "from generators.tsp import generate; from verifiers.tsp import verify; inst = generate(seed=1, difficulty='medium'); import json; fixture = json.load(open('tests/fixtures/tsp_smoke.json')); s, f, d = verify(fixture['instance'], fixture['gold_submission']); assert f and s == 0.0, (s, f, d); print('OK')"
OK

$ python -m py_compile generators/tsp.py verifiers/tsp.py
# exit 0
```

## BEST_GUESS Schema
```json
{"tour": [0, 7, 3, 10, 17, 5, 19, 13, 6, 1, 14, 12, 15, 2, 16, 18, 8, 11, 9, 4]}
```

## Decisions
- The repo’s real write path is `kaggle_submission/` at the root, even though the task note still says `metabench/kaggle_submission/`.
- The TSP verifier logic actually lives in `hch/portfolio_spike/tsp_instance.py`; `verify.py` was stale for this class.
- `generate()` exposes `optimal_length` but deliberately omits `optimal_tour` from the public instance payload so the instance JSON does not leak the gold tour; the smoke fixture carries the gold submission separately.
- The verifier documents the object contract but still accepts a raw tour list to avoid breaking older prompt shapes.

## Learnings
- Tried to find the TSP verifier in `hch/portfolio_spike/verify.py`, then switched to `tsp_instance.py` after confirming the task note’s source pointer was stale.
- A successor should not assume the path prefix in the leaf task note is current; check the repo root first because the actual submission tree here is `kaggle_submission/`.
- The stable mental model is: generator owns the expensive exact solve once per instance build, verifier trusts `optimal_length` from the generated instance and only checks feasibility plus realized tour length.

## DIFF

```
diff --git a/kaggle_submission/generators/tsp.py b/kaggle_submission/generators/tsp.py
new file mode 100644
--- /dev/null
+++ b/kaggle_submission/generators/tsp.py
@@ -0,0 +16,21 @@
+DIFFICULTY_TO_MIN_GAP_PCT = {
+    "medium": 15.0,
+    "hard": 25.0,
+}
+
+
+def generate(seed: int, difficulty: str) -> dict[str, Any]:
+    instance = _build_instance(seed=seed, difficulty=difficulty)
+    return {
+        "seed": instance.seed,
+        "difficulty": instance.difficulty,
+        "coords": [[x, y] for x, y in instance.coords],
+        "baseline_tour": list(instance.baseline_tour),
+        "baseline_length": instance.baseline_length,
+        "optimal_length": instance.optimal_length,
+        "problem_statement": instance.problem_statement,
+    }

```

```
diff --git a/kaggle_submission/verifiers/tsp.py b/kaggle_submission/verifiers/tsp.py
new file mode 100644
--- /dev/null
+++ b/kaggle_submission/verifiers/tsp.py
@@ -0,0 +8,31 @@
+def verify(instance: dict[str, Any], submission: dict[str, Any] | list[int] | tuple[int, ...]) -> tuple[float, bool, dict[str, Any]]:
+    """BEST_GUESS JSON schema: {"tour": [0, 7, 3, ...]} with every city index exactly once."""
+
+    try:
+        coords = _parse_coords(instance.get("coords"))
+        optimal_length = _read_positive_float(instance, "optimal_length")
+    except (TypeError, ValueError) as exc:
+        details = {"failure_reason": f"invalid instance: {exc}"}
+        return INVALID_GAP_PCT, False, details
+
+    baseline_length = _read_optional_float(instance, "baseline_length")
+    raw_tour = submission.get("tour") if isinstance(submission, dict) else submission
+    normalized_tour, failure_reason = _normalize_submission(coords, raw_tour)
+    if failure_reason is not None:
+        details = {
+            "failure_reason": failure_reason,
+            "baseline_length": baseline_length,
+            "optimal_length": optimal_length,
+        }
+        return INVALID_GAP_PCT, False, details
+
+    computed_length = _tour_length(coords, normalized_tour)
+    gap_pct = 100.0 * max(0.0, computed_length - optimal_length) / optimal_length
+    details = {
+        "computed_length": computed_length,
+        "baseline_length": baseline_length,
+        "optimal_length": optimal_length,
+        "normalized_tour": list(normalized_tour),
+    }
+    return gap_pct, True, details

```

## Complexity: medium

Mechanical port with one contract decision: expose an object-shaped BEST_GUESS while preserving backward compatibility for raw list submissions.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/generators/tsp.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/verifiers/tsp.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/tests/fixtures/tsp_smoke.json

### NOTES

- No files outside the TSP leaf write scope were modified.
- `hard` is implemented as a stricter minimum baseline-gap requirement (25%) rather than a different city count, keeping the instance family aligned with the source spike’s TSP-20 formulation.

## Related

- [task_1776349270569uld](task_1776349270569uld.md)
- [kaggle-submission-design](kaggle-submission-design.md)
- [kaggle-submission-filetree](kaggle-submission-filetree.md)

[[task_1776349270569uld]]
