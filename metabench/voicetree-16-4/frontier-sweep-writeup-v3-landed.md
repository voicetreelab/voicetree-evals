---
color: green
isContextNode: false
agent_name: Hana
---
# Frontier sweep integrated + writeup-v3 updated (6-model family-consistency)

Per-family verdict: anthropic-monitoring CONFIRMED, openai-sharp-and-wrong-M2 CONFIRMED, google-flat-forecaster REJECTED (Gemini 3 Pro inverts at frontier). writeup-v3.md at 1348/1500 words, ready for judge re-scoring. Opus N=13 flagged as small-sample caveat.

# Frontier-sweep integration + writeup-v3 update — landed

**Per-family verdict (headline):**
- **anthropic — monitoring axis CONFIRMED.** Sonnet M2-BSS +0.528 / Opus M2-BSS +0.035 (both positive); Opus *patches* Sonnet's execution failure (feas 33% → 92%). Opus N=13 caveat.
- **google — flat-forecaster axis REJECTED.** Flash M2-BSS −0.436 (res 0.026) vs Gemini-3-Pro M2-BSS +0.506 (res 0.116, feas 100%). Frontier inverts the Flash failure profile; flat-forecasting is a Flash-tier artifact, not a family specialization.
- **openai — sharp-and-wrong-M2 axis CONFIRMED.** GPT-5.4-mini M2-BSS −2.138 / GPT-5.4 M2-BSS −2.658 (both catastrophic, resolution ~0). M4 MAE worsens at frontier (2.08 → 8.62).

## Final 6-model metacog profile (fresh from `results/metacog_rollup.csv` at writeup time)

| family | tier | model | n_rows | M1-Brier | M1-BSS | M1-res | M2-Brier | M2-BSS | M2-res | M4-MAE | feas |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| anthropic | small    | claude-sonnet-4.6     | 67 | 0.187 | +0.194 | 0.090 | 0.098 | +0.528 | 0.123 | 1.85 | 33%  |
| anthropic | frontier | claude-opus-4.6       | 13 | 0.250 | −0.055 | 0.020 | 0.233 | +0.035 | 0.054 | 1.11 | 92%  |
| google    | small    | gemini-flash-latest   | 67 | 0.221 | −0.788 | 0.037 | 0.331 | −0.436 | 0.026 | 5.94 | 49%  |
| google    | frontier | gemini-3-pro-preview  | 53 | 0.119 |   —    | 0.000 | 0.093 | +0.506 | 0.116 | 0.35 | 100% |
| openai    | small    | gpt-5.4-mini          | 68 | 0.287 | −0.353 | 0.101 | 0.165 | −2.138 | 0.002 | 2.08 | 54%  |
| openai    | frontier | gpt-5.4               | 51 | 0.210 | +0.136 | 0.071 | 0.322 | −2.658 | 0.008 | 8.62 | 86%  |

*(M1-BSS for Gemini 3 Pro is undefined: all 46-row kept_as_best outcomes were 1 → uncertainty=0 → BSS mathematically undefined. That itself is a clean finding: the feasibility-ceiling the frontier Gemini reaches collapses the M1 base-rate Bernoulli.)*

## What landed in code

1. **`kaggle_submission/scripts/analyze_metacog.py`** — added frontier loader:
   - New constants: `FRONTIER_MODELS`, `SMALL_MODELS`, `MODELS` (6-model tuple), `FAMILY`/`TIER` maps, `FRONTIER_RUNS_DIR`.
   - Added `mbj` to `SOLO_CLASSES` (latest class graduation).
   - Refactored `_collect_per_row(path, question_row_dir=None)` — frontier rows resolve `question.json` from canonical `results/full/<row_id>/` rather than the path's parent.
   - Extended `aggregate()` to walk `results/runs/<model>/<row_id>.json` (inverted layout) as a second pass.
   - Added §3 family-consistency table + per-family verdict lines in `write_report`, then renamed old §3 → §3b.
   - §3b header now spans all 6 models (was hard-coded to the 3 small-tier models).

2. **`kaggle_submission/writeup-v3.md`** — at **1348 / 1500 words** after update:
   - Collapsed M1–M6 bulleted list into one inline sentence (saved ~50 words).
   - Replaced 3-model 10-row table with compact 6-model 6-row family-pair table (small · frontier per family).
   - Replaced the Sonnet/GPT/Gemini prose triptych with a per-family verdict paragraph explicitly naming CONFIRMED/REJECTED.
   - Updated pre-registered-predictions bullet with the frontier refinement.
   - Updated Limitations to cite Opus N=13 small-sample caveat and the still-running sweep.

3. **Re-rendered outputs:**
   - `kaggle_submission/results/metacog_analysis.md` — now includes §3 family-consistency table with verdicts.
   - `kaggle_submission/results/metacog_rollup.csv` — now has rows for all 6 models × all cells.

## Judge-critique closure pointer

> **Gemini 3.1 Pro Preview (90.5/100):** "The specialization claim isn't fully supported by the limited pilot data (which only tested one model per family)."

**Now empirically addressed** with N={67 Sonnet, 13 Opus, 67 Flash, 53 Gemini-3-Pro, 68 GPT-5.4-mini, 51 GPT-5.4} = 319 model-rows across 3 families × 2 tiers. Two of three family-level specialization axes are REPLICATED within-family across tiers; the third (google-flat) is honestly reported as REJECTED. The writeup no longer relies on single-model-per-family inference.

> **Gemini 3 Pro Preview (93.4/100):** "sample size + single-model-per-family are the key weaknesses".

Sample size per cell is still small (≤3 seeds × 6 classes × 2 difficulties), but the per-family replication argument is now a two-tier within-family comparison — the judge's single-highest-leverage criticism is closed.

## Snapshot refresh (sweep in-progress)

Latest data refresh — analyzer re-run over 328 model-rows:

| model | done | feasible | N scored |
|---|---|---|---|
| gemini-3-pro-preview | **56/56 ✅** | 56/56 (100%) | 56 |
| gpt-5.4 | 55/56 parsed | 47/56 (86%) | 56 |
| claude-opus-4.6 | 14/56 | 13/14 (93%) | 14 |

**Every frontier model beats every small-tier baseline on feasibility** — small-tier caps at 33/56. Verdicts unchanged with fresher N: anthropic M2-BSS (Sonnet +0.528 / Opus +0.052) both positive; openai catastrophic M2 *sharpened* at frontier (−2.138 → −3.169); google flat-forecaster cleanly REJECTED (Gemini-3-Pro +0.504 with 56/56 complete). Writeup table + verdict paragraph updated to latest numbers (now 1373/1500 words).

## Handoff

Writeup is **staged, not committed** — the caller asked to leave changes for human review. Next action for the caller: run the Gemini judge CLI on the updated `writeup-v3.md` to re-score. Expected direction: up from 90.5–93.4 — the single largest open criticism is now empirically addressed.

Sweep is still running (Opus was 4 rows at spawn, 7 mid-pass, 13 at writeup snapshot). A follow-up agent could re-run `python3 kaggle_submission/scripts/analyze_metacog.py` when the sweep completes (all three frontier counters should stabilize at 56 per target overlap list) and refresh the writeup numbers one more time; the verdict structure should not change because the direction of all three family axes is already decisive at current N.

## Files changed

- `kaggle_submission/scripts/analyze_metacog.py`
- `kaggle_submission/writeup-v3.md`
- `kaggle_submission/results/metacog_analysis.md` (regenerated)
- `kaggle_submission/results/metacog_rollup.csv` (regenerated)
- `kaggle_submission/results/metacog_calibration_bins.csv` (regenerated)

## PREDICTION CLAIMS

1. The Gemini-judge re-score on the updated `writeup-v3.md` will come in **at or above 93** (probability 0.65). Mechanism: single-highest-leverage criticism is now empirically closed; no new weaknesses introduced; word budget still at 1348/1500.
2. When the sweep completes (Opus settles at ~56 rows), the **three per-family verdicts will not flip** (probability 0.80). Mechanism: the direction of each axis is already decisive at current N — Opus M2-BSS is small but positive; Gemini-3-Pro M2-BSS at +0.51 is large enough that only a catastrophic drift could flip it; GPT-5.4 M2-BSS at −2.66 is way below the CONFIRMED threshold.
3. The caller will ship **writeup-v3 as-is** (probability 0.55); the alternative is one trimming pass to remove the M4-MAE row from the table in favor of restoring the M3 fraction-wrong line. I left M4 in because it is where the openai-family frontier regression is most visible (2.08 → 8.62).


## DIFF

```
# analyze_metacog.py — new constants + frontier loader walk

+FRONTIER_RUNS_DIR = ROOT / "results" / "runs"
 ...
-SOLO_CLASSES = ("cjs", "graphcol", "mwis", "steiner", "tsp", "ve")
+SOLO_CLASSES = ("cjs", "graphcol", "mwis", "steiner", "tsp", "ve", "mbj")
-MODELS = ("claude-sonnet-4.6", "gemini-flash-latest", "gpt-5.4-mini")
+SMALL_MODELS = ("claude-sonnet-4.6", "gemini-flash-latest", "gpt-5.4-mini")
+FRONTIER_MODELS = ("claude-opus-4.6", "gemini-3-pro-preview", "gpt-5.4")
+MODELS = SMALL_MODELS + FRONTIER_MODELS
+FAMILY = {"claude-sonnet-4.6":"anthropic", "claude-opus-4.6":"anthropic",
+          "gemini-flash-latest":"google", "gemini-3-pro-preview":"google",
+          "gpt-5.4-mini":"openai", "gpt-5.4":"openai"}
+TIER = {"claude-sonnet-4.6":"small", "claude-opus-4.6":"frontier", ...}

# aggregate() — second pass over inverted-layout frontier runs
+    if FRONTIER_RUNS_DIR.exists():
+        for model_dir in sorted(FRONTIER_RUNS_DIR.iterdir()):
+            if model_dir.name not in FRONTIER_MODELS: continue
+            for row_json in sorted(model_dir.glob("*.json")):
+                row_id = row_json.stem
+                q_dir = RESULTS_DIR / row_id
+                rec = _collect_per_row(row_json, question_row_dir=q_dir)
+                if rec: rows.append(rec)

# write_report() — new §3 family-consistency table with verdicts
+    lines.append("## 3. Family-consistency table — 6 models, 2 per family")
+    ... (renders the small·frontier pair per family + per-family CONFIRMED/REJECTED verdicts)
```

## Complexity: medium

Loader refactor + 6-model family-consistency section + writeup overhaul under 1500-word ceiling; code additive on an existing 1850-line script, writeup prose replacement.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scripts/analyze_metacog.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/writeup-v3.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/metacog_analysis.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/metacog_rollup.csv

[[task_1776381391711euy]]
