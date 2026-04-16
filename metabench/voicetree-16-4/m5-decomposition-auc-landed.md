---
color: green
isContextNode: false
agent_name: Gus
---
# M5 (decomposition AUC/ceiling) landed in analyze_metacog.py

Per-model M5 mean: Sonnet=0.776 (n=8 eligible), Gemini=0.825 (n=11), GPT=0.945 (n=3). Low eligible counts because overnight mean n_exec_turns ≈ 1.3 — 91 of 116 solo rows are M5-undefined (n_turns<2). writeup-v3.md §Core innovations + §Abstract already name M5 as capability-controlled; numbers can now be cited.

# M5 (decomposition AUC/ceiling) landed

**Per-model mean M5 (overnight 3-model pilot, solo classes only):**

| model | mean M5 | frac M5 ≥ 1 | n eligible | n trivial (n_turns<2) | n zero-ceiling | total solo rows |
|---|---|---|---|---|---|---|
| claude-sonnet-4.6  | 0.776 | 12% | 8  | 30 | 0 | 38 |
| gemini-flash-latest | 0.825 | 9%  | 11 | 28 | 0 | 39 |
| gpt-5.4-mini        | **0.945** | **67%** | 3  | 33 | 3 | 39 |

## Headline reading

GPT edges the mean (0.945) and the M5 ≥ 1 fraction (67% of its 3 eligible rows — two tsp/ve cells where GPT's own ceiling happens to be low and it nails it on one turn-pair), but the eligible-n is so small (3) that the mean is fragile. Gemini leads on eligible-n (11) because Gemini is the model that actually takes multi-turn runs overnight; its 0.825 is the highest-confidence cell. Sonnet's 0.776 across 8 eligible rows is the middle estimate.

**Dominant caveat: mean n_exec_turns ≈ 1.3 overnight.** 91 of 116 solo row-model records hit n_turns<2 (M5 undefined — no turn-interval to integrate). M5 is structurally informative only where a model chose to take ≥2 exec turns in a cell. Overnight's plan-once-execute-once-stop behaviour means M5 is mostly a sparse signal until the 30-min budget sweep lands.

## What got computed

- **AUC_model** = trapezoidal area under per-turn `score_t = max(0, 100 − gap_pct_t)` with uniform unit turn spacing.
- **cell_ceiling** = `max(final_score)` across the (model, class, difficulty) cell's 3 seeds; infeasible rows contribute 0 to ceilings.
- **AUC_ceiling** = `cell_ceiling × (n_turns − 1)` (flat rectangle).
- Per-row M5 = `AUC_model / AUC_ceiling`. Not clipped — values > 1 are possible when a row's intermediate turns score above the cell's own final ceiling.
- **Cell-ceiling fallback:** when a cell's ceiling is 0 (every seed infeasible) we fall back to per-class ceiling across difficulties; if still 0 the row is excluded (n_zero_ceiling).

## Per-(model, class) breakdown

| model | class | mean M5 | frac M5 ≥ 1 | n eligible | n trivial | ceiling |
|---|---|---|---|---|---|---|
| claude-sonnet-4.6 | cjs | — | — | 0 | 6 | 0.0 |
| claude-sonnet-4.6 | graphcol | — | — | 0 | 6 | 100.0 |
| claude-sonnet-4.6 | mwis | — | — | 0 | 6 | 0.0 |
| claude-sonnet-4.6 | steiner | 0.951 | 50% | 2 | 4 | 100.0 |
| claude-sonnet-4.6 | tsp | 0.761 | 0% | 5 | 1 | 99.8 |
| claude-sonnet-4.6 | ve | 0.500 | 0% | 1 | 5 | 84.5 |
| gemini-flash-latest | cjs | 0.753 | 0% | 3 | 3 | 96.1 |
| gemini-flash-latest | graphcol | 0.500 | 0% | 2 | 4 | 100.0 |
| gemini-flash-latest | mwis | 0.923 | 0% | 2 | 4 | 96.1 |
| gemini-flash-latest | steiner | — | — | 0 | 6 | 100.0 |
| gemini-flash-latest | tsp | 0.994 | 25% | 4 | 2 | 100.0 |
| gemini-flash-latest | ve | — | — | 0 | 6 | 97.1 |
| gpt-5.4-mini | cjs | — | — | 0 | 6 | 0.0 |
| gpt-5.4-mini | graphcol | — | — | 0 | 3 | 0.0 |
| gpt-5.4-mini | mwis | 0.835 | 0% | 1 | 5 | 89.6 |
| gpt-5.4-mini | steiner | — | — | 0 | 6 | 85.0 |
| gpt-5.4-mini | tsp | 1.000 | 100% | 1 | 5 | 98.1 |
| gpt-5.4-mini | ve | 1.000 | 100% | 1 | 5 | 96.5 |

## Writeup-v3 hook

- `kaggle_submission/writeup-v3.md:12` — §Abstract already lists M5 as a capability-controlled metric. Numbers can now be inserted into the Results section.
- `kaggle_submission/writeup-v3.md:30` — §Methods bullet names M5 with its formula; no math change needed.
- `kaggle_submission/writeup-v3.md:88` — §Limitations currently says `M5 results landing separately` — replace with the headline line above (or cite `kaggle_submission/results/metacog_analysis.md` §3a).

## Verification

Script runs clean:
```
$ python3 kaggle_submission/scripts/analyze_metacog.py
Analyzed 201 model-row records.
Wrote report: kaggle_submission/results/metacog_analysis.md
Wrote CSV:    kaggle_submission/results/metacog_rollup.csv
```

`metacog_analysis.md` now contains §3a. M5 — Decomposition effectiveness (AUC / ceiling) with the two tables above, placed between §3 (profile) and §4 (rollup) per the brief. `metacog_rollup.csv` gains five new columns: `m5_mean`, `m5_ge1_frac`, `m5_n_eligible`, `m5_n_trivial`, `m5_ceiling`.

## Design decisions

1. **Why a new `_extract_turn_scores` instead of reusing `_extract_subtasks`.** `_extract_subtasks` breaks out of the per-turn loop when the NEXT_SUB p_solve chain terminates (line 225). That is correct for M1 (subtasks require a preceding p_solve to score) but wrong for M5 (we want the score trajectory across all main-run exec turns). I added a sibling helper that scores every main-run exec turn's BEST_GUESS via the existing `_score_subtask_submission`. No re-verification outside the solo path — portfolio/no-instance rows return [].

2. **Uniform turn spacing, not wall-seconds.** The brief permitted either; I took the uniform fallback because per-turn wall_seconds isn't stored in the transcript entries (only a total `wall_s` on the record). Time-weighted AUC is a nice-to-have follow-up.

3. **Ceiling source transparency.** Each M5 row records `ceiling_source = 'cell' | 'class' | 'none'` so downstream analysis can filter out fallback rows if cell-level attribution matters.

4. **No clipping.** The brief explicitly asked for raw M5 and M5 ≥ 1 fraction. GPT tsp_medium and ve_medium each have one eligible row at M5 = 1.000 exactly — those are cases where the eligible row IS the ceiling row AND its intermediate turn score equals the final score (flat trajectory at ceiling). Not noise.

## Files changed

- `kaggle_submission/scripts/analyze_metacog.py` (+~170 lines additive)
  - New: `_extract_turn_scores(...)`, `_final_score(...)`, `_m5_decomposition(...)`
  - `_collect_per_row` now stores `turn_scores` alongside `subtasks`
  - `write_report(...)` takes an `m5` kwarg and renders §3a after §3
  - `main()` computes M5 and threads it into the report
  - CSV rollup gains 5 M5 columns
- `kaggle_submission/results/metacog_analysis.md` (regenerated)
- `kaggle_submission/results/metacog_rollup.csv` (regenerated)

## What was skipped / flagged

- **Portfolio excluded** from M5 (same rule as M1 — no per-sub-component verifier routing).
- **n_zero_ceiling = 3 for GPT.** Three solo rows where GPT's own cell had no feasible seed. Falls back to per-class ceiling; remaining 3 excluded where per-class also zero (all-infeasible cells like cjs × both difficulties).
- **Mean n_exec_turns ≈ 1.3 is the headline limitation.** The cheap-to-compute M5 number will become much more informative once the 30-min budget sweep lands and models actually chain multiple turns.

## DIFF

```
--- a/kaggle_submission/scripts/analyze_metacog.py
+++ b/kaggle_submission/scripts/analyze_metacog.py
@@ (near _extract_subtasks)
+def _extract_turn_scores(transcript, cls, n_exec_turns, instance):
+    """Per-main-run-exec-turn BEST_GUESS verified score trajectory (for M5).
+    Scores every main-run exec turn regardless of p_solve chain continuity.
+    """
+    if cls == 'portfolio' or instance is None: return []
+    if not transcript or n_exec_turns <= 0: return []
+    exec_msgs = [m for m in transcript[1:1+n_exec_turns] if m.get('role') == 'assistant']
+    out = []
+    for idx, msg in enumerate(exec_msgs):
+        parsed = parse_exec_turn_partial(msg.get('content') or '', cls=cls, require_decision=False)
+        bg = parsed.get('best_guess')
+        if bg is None:
+            gap_pct, feasible, had_bg = INFEASIBLE_GAP_PCT, False, False
+        else:
+            gap_pct, feasible = _score_subtask_submission(cls, instance, bg); had_bg = True
+        out.append({'turn_idx': idx+1, 'gap_pct': gap_pct, 'feasible': feasible,
+                    'had_best_guess': had_bg, 'score': max(0.0, 100.0 - float(gap_pct))})
+    return out

@@ (in _collect_per_row)
     subtasks = _extract_subtasks(transcript, cls, n_exec_turns, instance)
+    turn_scores = _extract_turn_scores(transcript, cls, n_exec_turns, instance)
     return {..., 'subtasks': subtasks, 'turn_scores': turn_scores}

@@ (before write_report)
+def _final_score(r):
+    if r.get('feasible') and r.get('final_gap') is not None:
+        return max(0.0, 100.0 - float(r['final_gap']))
+    return 0.0
+
+def _m5_decomposition(rows):
+    cell_ceiling, class_ceiling = {}, {}
+    for r in rows:
+        if r['class'] == 'portfolio': continue
+        fs = _final_score(r)
+        cell_ceiling[(r['model'], r['class'], r['difficulty'])] = max(fs, cell_ceiling.get((r['model'], r['class'], r['difficulty']), -1.0))
+        class_ceiling[(r['model'], r['class'])] = max(fs, class_ceiling.get((r['model'], r['class']), -1.0))
+    per_row = []
+    for r in rows:
+        if r['class'] == 'portfolio': continue
+        ts = r.get('turn_scores') or []
+        n = len(ts)
+        ceiling = cell_ceiling.get((r['model'], r['class'], r['difficulty']), 0.0)
+        if ceiling <= 0.0: ceiling = class_ceiling.get((r['model'], r['class']), 0.0)
+        if n < 2: per_row.append({..., 'm5': None, 'reason': 'n_turns<2'}); continue
+        if ceiling <= 0.0: per_row.append({..., 'm5': None, 'reason': 'ceiling<=0'}); continue
+        auc_model = sum((ts[i]['score']+ts[i+1]['score'])/2 for i in range(n-1))
+        auc_ceiling = ceiling * (n-1)
+        per_row.append({..., 'm5': auc_model/auc_ceiling})
+    # per-model / per-class aggregation: mean M5, frac M5 ≥ 1, n eligible/trivial/zero
+    ...
+    return {'per_row': per_row, 'per_model': ..., 'per_cell': ..., 'per_class': ...}

@@ (in main)
-    write_report(rows, agg, all_agg, mstats)
+    m5 = _m5_decomposition(rows)
+    write_report(rows, agg, all_agg, mstats, m5)

@@ (in write_report, after §3 profile table, before §4 rollup)
+    if m5:
+        lines.append('## 3a. M5 — Decomposition effectiveness (AUC / ceiling)')
+        # headline, per-model rollup table, per-class breakdown table, interpretation paragraph

@@ (CSV writer — added columns)
     w.writerow([..., bucket['drift_flat'],
-                 ])
+                 m5_mean, m5_ge1_frac, m5_n_eligible, m5_n_trivial, m5_ceiling])

```

## Complexity: medium

Additive — no changes to existing M1/M2/M3/M4 pipelines. Three load-bearing concerns: (1) write a turn-score extractor that covers ALL main-run exec turns (not just those in the p_solve chain, which is why reusing _extract_subtasks directly wouldn't work); (2) compute cell ceilings with the infeasible→0 rule and a per-class fallback for all-infeasible cells; (3) thread m5 through main → write_report → CSV writer without breaking the existing signatures. No verifier re-runs: all gap_pct comes from _score_subtask_submission which is already exercised by M1.

## Files Changed

- kaggle_submission/scripts/analyze_metacog.py
- kaggle_submission/results/metacog_analysis.md
- kaggle_submission/results/metacog_rollup.csv

### NOTES

- M5 is cheap to run but structurally under-powered at overnight n_exec_turns ≈ 1.3 — eligible n = 8/11/3 per model. The 30-min budget sweep is the next unlock; rerunning this script after that sweep should lift eligible-n into the dozens.
- Two rows land at M5 = 1.000 exactly (GPT tsp_medium and GPT ve_medium). In both cases the single eligible row IS the cell's ceiling row, with a flat trajectory (intermediate turn score = final turn score = ceiling). Not a numerical artifact.
- n_zero_ceiling > 0 (GPT: 3 rows) reflects the 0/36 feasibility failures that landed the portfolio infeasibility investigation. For solo classes, GPT has 3 rows in cells where every seed is infeasible (cjs × both difficulties accounts for most of it).
- Did NOT commit — per brief, leave changes staged for human review. Script is idempotent; running it again regenerates both outputs cleanly.
- writeup-v3.md already names M5 in §Abstract and §Methods; the only writeup patch needed is to replace the `M5 results landing separately` placeholder at line 88 with the per-model headline.

[[task_1776380869255odv]]
