---
color: green
isContextNode: false
agent_name: Cho
---
# Carla — notable metacog findings for writeup (un-clipped BSS, refinement, Sonnet-only dominance)

Only Sonnet has positive BSS on both M1 and M2 (+0.21, +0.52). Gemini M1 BSS = −1.09 (flat forecaster), GPT M2 BSS = −2.13 (sharp + anti-informative). Un-clipping BSS + reporting Refinement=Res/(Res+Rel) differentiate the failure axes that writeup-v2's clipped 0 framing erases.

# Carla — notable metacog findings for writeup (un-clipped, unabridged)

User interjected mid-work: flagged that the negative BSS numbers are the fascinating finding. Stop clipping them. This node captures the cleanest framings worth landing in writeup-v2.

## TL;DR

**Only Sonnet has positive Brier Skill Score on both M1 and M2.** The other two models' emitted metacog forecasts are *worse than just quoting the base rate* — they hurt predictions vs the trivial constant predictor. Clipping BSS to 0 hides this.

## Un-clipped BSS — M1 and M2, derived from existing Murphy numbers

`BSS = 1 − Brier / Uncertainty`. Negative = forecast hurts vs the constant base-rate predictor.

| model | M1 Brier | M1 Uncert | **M1 BSS (raw)** | M2 Brier | M2 Uncert | **M2 BSS (raw)** |
|---|---|---|---|---|---|---|
| claude-sonnet-4.6 | 0.186 | 0.236 | **+0.212** | 0.097 | 0.204 | **+0.525** |
| gemini-flash-latest | 0.207 | 0.099 | **−1.091** | 0.322 | 0.237 | **−0.359** |
| gpt-5.4-mini | 0.275 | 0.220 | **−0.250** | 0.172 | 0.055 | **−2.127** |

(Anna's finding 3 cited −1.11 / −0.25 / −0.38 / −2.11 — same numbers to rounding noise.)

## Refinement = Resolution / (Resolution + Reliability)

The axis that survives BSS-clipping. Bounded [0,1]: 0 = pure miscalibration, 1 = pure calibration. Already in the Murphy ingredients.

| model | M1 res | M1 rel | **M1 Refinement** | M2 res | M2 rel | **M2 Refinement** |
|---|---|---|---|---|---|---|
| claude-sonnet-4.6 | 0.101 | 0.051 | **0.664** | 0.120 | 0.013 | **0.902** |
| gemini-flash-latest | 0.022 | 0.132 | **0.143** | 0.028 | 0.117 | **0.193** |
| gpt-5.4-mini | 0.121 | 0.176 | **0.407** | 0.002 | 0.118 | **0.017** |

## Why the signs matter

- **Gemini M1 BSS = −1.09** — emits `p_solve` in a narrow, base-rate-like band (variance of predictions ≪ variance of outcomes). Resolution 0.022 vs uncertainty 0.099: flat forecaster. Emit-side reliability gap (0.132) swamps lift. Classic 'flat and wrong'.
- **GPT M2 BSS = −2.13** — opposite failure. Quality forecasts spread (not flat) but don't track realized outcomes: Res = 0.002. Brier 3× base-rate floor. Classic 'sharp and wrong'.
- **Sonnet M1/M2 both positive** — narrow but real. Refinement 0.66 / 0.90. Emissions genuinely track truth, especially M2.
- **The two failure directions are NOT interchangeable.** A composite that collapses them loses that Gemini and GPT are making *different* mistakes.

## The M1↔M2 flip is structural, not noise

GPT is 2/3 on M1 Refinement (0.407) and 3/3 on M2 Refinement (0.017). On p_solve (subtask-kicking-off forecast), GPT discriminates well — it knows which subtasks it's about to succeed at. On p_gap_le_k (quality forecast after the output exists), it can't tell which of its own outputs are close to target. Writeup axis: **'knowing what you know' (M1) and 'knowing what you made' (M2) dissociate within-model**, not just across models.

## Writeup implications

1. **Delete the BSS-clipping convention.** Report raw BSS. 'All clipped to 0' is informationally dead; raw differentiates flat (Gemini) from sharp-wrong (GPT).
2. **Replace Finding 7.** Writeup currently says 'GPT has highest resolution' as a virtue. True on M1 (res 0.121); INVERTS on M2 (res 0.002). Correct finding: **resolution is metric-dependent; GPT's M2 resolution is floor-level; pure Brier hides both.**
3. **New finding: Sonnet's monopoly on positive BSS.** Only Sonnet's metacog adds skill over base-rate. Headline-grade.
4. **Refinement column** is an acceptable single-number summary: bounded, negative-BSS-proof, matches Murphy's original framing.

## Handover state — what's done, what's pending

**Done (in analyze_metacog.py, lines 792–975):**
- `_collect_m1_pairs`, `_collect_m2_pairs` — per (model, class) pair extractors
- `_calibration_bins` — uniform 1/n-wide binning
- `_render_calibration_plot` — ASCII reliability diagram
- `_per_class_rollup` — per-(model, class) Murphy decomp for M1 + M2
- `_pricing_bias` — per-model mean E[Δ] vs realized cf_Δ with low/high median split

**Pending:**
- Insert `write_report` extension to emit §8 (6 calibration plots), §9 (per-class Brier), §10 (pricing-bias reconciliation) + `results/metacog_calibration_bins.csv`. Full code ready-to-paste in sibling node `carla-handover-writereport-extension.md`.
- Draft `kaggle_submission/writeup-v2-overnight-patches.md` with BEFORE/AFTER for: (a) Metacognitive profile table (drop clipped BSS, add raw BSS + Refinement columns), (b) Seven primary findings (replace Finding 7, add Sonnet-BSS-monopoly finding), (c) Penalty Comprehension Audit (reframe via §10 pricing-bias math).
- Re-run `python3 kaggle_submission/scripts/analyze_metacog.py` after pasting extension to produce the concrete numbers for the pricing-bias paragraph.

### NOTES
- User steer (standing preference for this writeup pass): *'the negative numbers are fascinating!!! btw let's not clip these to zero.'*
- Depth budget 0 on Cho — handover agent is spawned as peer under Anna, not child of Cho.


[[task_17763772282376sh]]
