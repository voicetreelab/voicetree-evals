---
color: blue
isContextNode: false
agent_name: Emi
---
# MBJ graduated to SOLO_CLASSES + hard seeds 1/2/3 optimal + single-seed gpt smoke passed

Landed Bob's 3 pre-flight fixups for MBJ (SOLO_CLASSES, HARD_SIZE_FALLBACKS, CP-SAT require_optimal). build_questions.py now emits 30 rows including 4 MBJ (1 medium + 3 hard). mbj_hard_seed{1,2,3} all proved OPTIMAL in CP-SAT at 300s, no size fallback triggered. Single gpt-5.4-mini run on mbj_medium_seed1: parse clean (strict_protocol_cf), feasible=True, but gap=25.7% (baseline-only submission, no improvement). Ready for Codex bulk-generate.

# MBJ graduation — pre-flight fixups + single-seed LLM smoke

Bob's MBJ spike landed a one-row port. This node graduates MBJ to a first-class citizen: wires into `SOLO_CLASSES`, adds a HARD_SIZE_FALLBACKS entry, tightens CP-SAT optimality policy, and proves the full local harness path end-to-end with one real gpt-5.4-mini call.

## Part 1 — Fixup diffs

### 1a + 1b in `kaggle_submission/scripts/build_questions.py`

```python
SOLO_CLASSES = ("cjs", "steiner", "graphcol", "tsp", "mwis", "ve", "mbj")  # was 6-tuple

HARD_SIZE_FALLBACKS: dict[str, tuple[tuple[str, int], ...]] = {
    "mwis": (...),
    "steiner": (...),
    "ve": (...),
    "mbj": (
        ("n_jobs", mbj.DIFFICULTY_CONFIGS["medium"]["n_jobs"]),
        ("n_machines", mbj.DIFFICULTY_CONFIGS["medium"]["n_machines"]),
    ),
}
```

Added a full `_generate_mbj_instance()` helper that merges `config_override` into `mbj.DIFFICULTY_CONFIGS[difficulty]` (same pattern as mwis/ve). Replaced the old `_build_mbj_row` that raised when config_override was provided — it now delegates to `_generate_mbj_instance` so the size-fallback path is live.

Wired into `builders` dict and removed the ad-hoc medium-row append in `_build_rows`. MBJ now flows through `MEDIUM_SOLO_SPECS`/`HARD_SOLO_SPECS` like every other class.

**Intentionally NOT touched:** `HARD_PORTFOLIO_COMPONENT_CLASSES` and `MEDIUM_PORTFOLIO_COMPONENT_IDS` stay `('cjs','steiner','tsp')` and the cjs/steiner/tsp medium-seed1 triple respectively. Portfolio integration is an explicit follow-up decision, per task scope.

### 1c in `kaggle_submission/generators/mbj.py`

```python
# DIFFICULTY_CONFIGS["hard"]["cp_time_limit_s"]: 120.0 → 300.0

def build_instance(
    ...
    cp_time_limit_s: float = 60.0,
    require_optimal: bool = True,   # NEW — default True prevents silent FEASIBLE-only rot
) -> MaskedBlockJobShopInstance:
    ...
    for attempt_index in range(max_generation_attempts):
        ...
        solve_result = solve_exact_schedule(...)
        if require_optimal and not solve_result.is_optimal:
            last_failure = (
                f"attempt {attempt_index} CP-SAT returned {solve_result.status_name} "
                f"(not OPTIMAL) within {cp_time_limit_s}s"
            )
            continue
        ...
```

`generate()` now passes `require_optimal=True` explicitly. Pilot's silent-accept-FEASIBLE behaviour (which rotted `gold_objective` math per Bob's Claim 2) is gone.

Picked 300s as the per-call CP-SAT budget — 5 min is comfortable for 12×10 MBJ, and the attempt loop caps worst case at 300s × 24 = 2h per seed (observed actual ≪ that).

## Part 1d — Hard-gen verification

Stashed the committed 188-row `questions.jsonl` to `/tmp/questions.jsonl.emi_backup`, ran `python scripts/build_questions.py`, observed output, restored. **188-row committed file is intact.**

```
Wrote 30 rows to questions.jsonl. Deleted gold/. Verified schema round-trip.
```

30 rows = 7 medium solo + 1 medium portfolio + 7 hard × 3 seeds + 1 hard portfolio. MBJ rows:

| id | n_jobs | n_machines | gold_obj | baseline_obj | baseline_gap |
|---|---|---|---|---|---|
| mbj_medium_seed1 | 8 | 8 | 5700 | 7167 | 25.7% |
| mbj_hard_seed1 | 12 | 10 | 6420 | 7700 | 19.9% |
| mbj_hard_seed2 | 12 | 10 | 6340 | 9394 | 48.2% |
| mbj_hard_seed3 | 12 | 10 | 5380 | 7040 | 30.9% |

- All 3 hard seeds succeeded on **attempt 0** — no size fallback triggered, no seed fallback triggered.
- All 3 were OPTIMAL (would have raised otherwise given `require_optimal=True`).
- `_sanity_check_round_trip` passed for all 30 rows.
- Verifier sanity check: `CLASS_TO_VERIFIER['mbj'](inst, inst['gold_submission'])` → feasible=True for all 4 MBJ rows.
- Portfolios unchanged: `portfolio_medium_seed1` = cjs/steiner/tsp medium, `portfolio_hard_seed2` = cjs/steiner/tsp hard.

## Part 2 — Single-seed LLM smoke (gpt-5.4-mini × mbj_medium_seed1)

Built a temp `/tmp/mbj_smoke.jsonl` with just the MBJ row, ran `python -m eval_harness.run_local --model gpt-5.4-mini --ids mbj_medium_seed1 --questions-file /tmp/mbj_smoke.jsonl --output-dir /tmp/mbj_run`, moved outputs to `kaggle_submission/results/full/mbj_medium_seed1/`.

| metric | value |
|---|---|
| parse_path | strict_protocol_cf |
| cf_parsed | True |
| feasible | **True** |
| verified_objective | 7167 |
| gap_pct | 25.7% |
| score | 74.08 |
| cf_delta | -0.054 |
| stop_reason | decision_stop |
| n_exec_turns | 1 |
| wall_s | 17.9s |
| error | - |

Qualitative: plan turn identified bottleneck on M1/M2/M7 + J6 tardiness. Exec turn stated "did not find a clearly superior local swap" and emitted the baseline verbatim. CF branch re-confirmed baseline. **Model produced structurally perfect JSON but punted on improvement.**

Full artefacts in `kaggle_submission/results/full/mbj_medium_seed1/{gpt-5.4-mini.json, question.jsonl, concerns.md}`.

## Part 3 — PREDICTION CLAIMS update

Against Bob's four claims from `mbj-spike-prediction-claims.md`:

- **Claim 1** (porting 11 medium seeds will work): not tested this round — deferred to bulk-generate.
- **Claim 2** (porting 12 hard seeds will work): **supported for seeds 1–3 at 300s CP-SAT budget with require_optimal=True**. All 3 proved OPTIMAL on attempt 0, no fallback triggered. Confidence bumps from 55% → 80% for seeds 1–3; unchanged for seeds 4–12 until tested.
- **Claim 3** (LLMs emit feasible MBJ at first run): **supported for gpt-5.4-mini × seed 1** — feasible=True, strict parse, no rescue. Confidence now 85% for GPT; Sonnet + Gemini still untested. Caveat: "feasible" here = baseline echo, not genuine optimization. Headroom capture is a separate claim.
- **Claim 4** (adding to SOLO_CLASSES is non-trivial): **refuted for the in-scope subset.** One-line SOLO_CLASSES change + one HARD_SIZE_FALLBACKS entry + the `require_optimal` path was sufficient. Worker-script sampling not re-tested.

New claims:

1. **All 3 frontier models will produce feasible mbj_medium_seed1 at first run — 75% confident.** Basis: GPT landed clean, the baseline-echo escape hatch is generous. Falsifier: any model emits a schedule that fails `verify_schedule`.
2. **CP-SAT at 300s is enough for mbj_hard seeds 1–6 — 75% confident.** Basis: seeds 1–3 all proved OPTIMAL well under 300s; 12×10 MBJ is small enough that OR-Tools rarely times out. Falsifier: any seed in 4–6 returns FEASIBLE-not-OPTIMAL (will now raise and trigger fallback).
3. **Baseline-echo is the dominant feasibility strategy for MBJ — 70% confident.** Basis: GPT explicitly said "did not find a clearly superior local swap" and echoed baseline; MBJ's dense precedence chains make local improvement hard. Falsifier: >30% of bulk runs show `verified_objective < baseline_objective`.

## Verdict

**Ready for Codex bulk-generate.** No structural blockers uncovered; the 3 hard seeds generate optimal gold under 300s CP-SAT with require_optimal=True, and at least GPT clears the full local harness path cleanly. Remaining risk: (a) Sonnet/Gemini may have different parse behaviour than GPT, (b) higher hard seeds (4+) may need the new size-fallback path, (c) portfolio integration is an explicit follow-up.

## DIFF

```
# kaggle_submission/scripts/build_questions.py

-SOLO_CLASSES = ("cjs", "steiner", "graphcol", "tsp", "mwis", "ve")
+SOLO_CLASSES = ("cjs", "steiner", "graphcol", "tsp", "mwis", "ve", "mbj")

 HARD_SIZE_FALLBACKS: dict[str, tuple[tuple[str, int], ...]] = {
     "mwis": (...),
     "steiner": (...),
     "ve": (...),
+    "mbj": (
+        ("n_jobs", mbj.DIFFICULTY_CONFIGS["medium"]["n_jobs"]),
+        ("n_machines", mbj.DIFFICULTY_CONFIGS["medium"]["n_machines"]),
+    ),
 }

+def _generate_mbj_instance(seed, difficulty, config_override=None):
+    if config_override is None:
+        return mbj.generate(seed=seed, difficulty=difficulty)
+    config = dict(mbj.DIFFICULTY_CONFIGS[difficulty])
+    config.update(config_override)
+    instance = mbj.build_instance(
+        seed=seed,
+        n_jobs=int(config["n_jobs"]),
+        n_machines=int(config["n_machines"]),
+        ...
+        require_optimal=bool(config.get("require_optimal", True)),
+    )
+    # ... build full instance dict (same shape as mbj.generate) ...

-def _build_mbj_row(seed, difficulty, *, config_override=None):
-    if config_override is not None:
-        raise RuntimeError("mbj does not expose a size override path from build_questions.py")
-    instance = mbj.generate(seed=seed, difficulty=difficulty)
-    ...
-    return SmokeRow(row=row, notes="MBJ port spike — one row only, not yet in SOLO_CLASSES.")
+def _build_mbj_row(seed, difficulty, *, config_override=None):
+    instance = _generate_mbj_instance(seed=seed, difficulty=difficulty, config_override=config_override)
+    ...
+    return SmokeRow(row=row)

 builders = {
     "cjs": ..., "steiner": ..., "graphcol": ..., "tsp": ..., "mwis": ..., "ve": ...,
+    "mbj": _build_mbj_row,
 }

-rows = list(medium_rows)
-# MBJ port spike: one medium row, kept out of SOLO_CLASSES ...
-rows.append(_annotate_row(_build_timed_row(_build_mbj_row, 1, "medium"), requested_seed=1))
+rows = list(medium_rows)  # mbj_medium_seed1 now included via MEDIUM_SOLO_SPECS
```

```
# kaggle_submission/generators/mbj.py

 DIFFICULTY_CONFIGS = {
     "medium": {..., "cp_time_limit_s": 60.0, ...},
-    "hard":   {..., "cp_time_limit_s": 120.0, ...},
+    "hard":   {..., "cp_time_limit_s": 300.0, ...},
 }

 def build_instance(
     seed, n_jobs, n_machines, *,
     min_baseline_gap_pct=10.0, ...,
     cp_time_limit_s=60.0,
+    require_optimal: bool = True,
 ) -> MaskedBlockJobShopInstance:
     for attempt_index in range(max_generation_attempts):
         ...
         solve_result = solve_exact_schedule(...)
+        if require_optimal and not solve_result.is_optimal:
+            last_failure = (
+                f"attempt {attempt_index} CP-SAT returned {solve_result.status_name} "
+                f"(not OPTIMAL) within {cp_time_limit_s}s"
+            )
+            continue
         baseline = _heuristic_by_name(heuristic_results, "baseline")
         ...

 def generate(seed, difficulty):
     ...
     instance = build_instance(
         ...
         cp_time_limit_s=float(config["cp_time_limit_s"]),
+        require_optimal=True,
     )
```

## Complexity: medium

Three touchpoints across two files — SOLO_CLASSES list, HARD_SIZE_FALLBACKS dict, and a new `require_optimal` kwarg that intercepts the attempt loop. Each change is small but load-bearing (silent CP-SAT FEASIBLE acceptance would rot gold math; missing HARD_SIZE_FALLBACKS would crash hard-seed gen). Plus pilot helper `_generate_mbj_instance` refactor so config_override plumbs through.

## Files Changed

- kaggle_submission/scripts/build_questions.py
- kaggle_submission/generators/mbj.py
- kaggle_submission/results/full/mbj_medium_seed1/gpt-5.4-mini.json
- kaggle_submission/results/full/mbj_medium_seed1/question.jsonl
- kaggle_submission/results/full/mbj_medium_seed1/concerns.md

### NOTES

- Committed 188-row questions.jsonl stashed to /tmp/questions.jsonl.emi_backup before build, restored after — the committed file is byte-identical to HEAD post-run.
- Per task instructions: no commits made. User decides commit scope after review.
- Observed MBJ hard CP-SAT solve times: all 3 seeds finished well under 300s per attempt 0 on this box; 300s is a defensive ceiling, not a measured need. Pilot's 120s was likely also enough but risked silent-accept-FEASIBLE.
- Gold_submission verifier returns objective=0.0 feasible=True for optimal gold rows — cosmetic; other classes behave the same (verifier returns gap-from-best, not raw objective).

[[task_1776378000394y8q]]
