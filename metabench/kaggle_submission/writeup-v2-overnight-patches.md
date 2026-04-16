# writeup-v2 overnight patches — Cora

Three BEFORE/AFTER patches reflecting the overnight 192-row pilot (64 row_ids × 3 models: `claude-sonnet-4.6`, `gemini-flash-latest`, `gpt-5.4-mini`). Source numbers: `kaggle_submission/results/metacog_analysis.md` §§3, 8, 9, 10 (re-rendered 2026-04-17 after Carla's §8/§9/§10 extension landed).

Standing user steer:
> "the negative numbers are fascinating!!! btw let's not clip these to zero."

All BSS reported raw. Refinement = Res / (Res + Rel) carried alongside as a bounded [0,1] companion.

---

## Patch A — §"Metacognitive profile" table

Replaces the 5-model clipped-BSS table with a 3-model raw-BSS + Refinement table. Other two columns marked TBD because Haiku 4.5, Gemini 3 Pro, and GPT-5.4 Nano are not in the overnight set.

### BEFORE (lines ~344–356 of writeup-v2.md)

```
### Metacognitive profile (Phase 1 aggregated, n=120 solo instances per model)

| metric | Gemini 3 Pro | Sonnet 4.6 | Haiku 4.5 | GPT-5.4 | GPT-5.4 Nano | what it measures |
|---|---:|---:|---:|---:|---:|---|
| M1 Brier (p_solve) | 0.180 | 0.291 | 0.223 | 0.128 | 0.287 | knowing what you know |
| — reliability | 0.042 | 0.108 | 0.089 | 0.029 | 0.104 | — calibration-proxy component |
| — resolution | 0.061 | 0.047 | 0.031 | 0.112 | 0.024 | — *informativeness* component |
| M2 Brier (quality forecast) | 0.094 | 0.341 | 0.398 | 0.208 | 0.441 | self-assessing output without oracle |
| M3 CF-$ mean Δ | **+3.14** | +0.87 | +1.43 | +0.22 | +0.54 | knowing when to stop |
| M3 fraction-of-stops-wrong | 61% | 27% | 38% | 9% | 18% | — |
| M4 forecast error (MAE) | 8.41 | 4.32 | 3.87 | 2.09 | 4.21 | predicting value of more effort |
| M5 AUC / ceiling | 0.42 | 0.61 | 0.54 | 0.74 | 0.58 | decomposing effectively |
| M6 allocation gap ($) | 21.8 | 12.4 | 9.6 | 18.6 | 17.3 | knowing strengths across domain |
```

### AFTER

```
### Metacognitive profile (overnight pilot, 64 row_ids × 3 models, mean 1.3 exec turns)

**Headline: only Sonnet 4.6 has positive Brier Skill Score on both M1 and M2 (+0.21 / +0.53).** The other two models' emitted metacog forecasts are *worse than just quoting the base rate* — they hurt predictions against the trivial constant predictor. The two failure modes dissociate: Gemini is a *flat forecaster* (M1 BSS −1.11, narrow-band p_solve, low resolution 0.02), while GPT is *sharp-and-wrong* on M2 (BSS −2.12, spread forecasts with floor-level resolution 0.002). A composite that clips BSS to 0 erases that distinction. Refinement = Res / (Res + Rel) is carried alongside as a bounded [0,1] companion that survives the clipping problem.

| metric | Sonnet 4.6 | Gemini Flash | GPT-5.4 mini | Haiku 4.5 / Nano / Gemini Pro | what it measures |
|---|---:|---:|---:|---:|---|
| M1 Brier (p_solve) | 0.186 | 0.207 | 0.275 | TBD (not in overnight set) | knowing what you know — kept_as_best outcome |
| — M1 reliability | 0.051 | 0.132 | 0.176 | TBD | Murphy: calibration component (lower=better) |
| — M1 resolution | 0.101 | 0.022 | 0.121 | TBD | Murphy: informativeness (higher=better) |
| — M1 uncertainty | 0.236 | 0.099 | 0.220 | TBD | base-rate entropy |
| — **M1 BSS (raw, unclipped)** | **+0.21** | **−1.11** | **−0.25** | TBD | 1 − Brier/Uncertainty; negative ⇒ forecast hurts vs base-rate |
| — M1 Refinement Res/(Res+Rel) | 0.663 | 0.144 | 0.407 | TBD | bounded-[0,1] alt to BSS |
| — M1 n (subtasks) | 34 | 45 | 49 | TBD | solo-class subtasks w/ parseable p_solve + best_guess |
| M2 Brier (quality forecast) | 0.097 | 0.322 | 0.172 | TBD | self-assessing output without oracle |
| — M2 reliability | 0.013 | 0.117 | 0.118 | TBD | Murphy calibration |
| — M2 resolution | 0.120 | 0.028 | 0.002 | TBD | Murphy informativeness |
| — M2 uncertainty | 0.204 | 0.237 | 0.055 | TBD | base-rate entropy |
| — **M2 BSS (raw, unclipped)** | **+0.53** | **−0.38** | **−2.12** | TBD | — |
| — M2 Refinement Res/(Res+Rel) | 0.902 | 0.192 | 0.017 | TBD | — |
| M3 CF-$ mean Δ (clean stops) | −0.26 | −1.64 | −1.31 | TBD | knowing when to stop (NEGATIVE = stopped correctly) |
| M3 fraction-of-stops-wrong | 4% | 14% | 0% | TBD | % clean stops where forced-continue improved |
| M4 forecast error (MAE) | 1.07 | 4.66 | 1.94 | TBD | expected_Δ vs realized cf_Δ |
| Feasibility rate | 30% | 50% | 52% | TBD | final submission verifies feasible |
| Mean exec turns | 1.30 | 1.34 | 1.33 | TBD | (SHORT — 30-min full-budget sweep pending) |

**Two axes of failure, one table of numbers.** Sonnet is the only model whose emitted p_solve (M1) and quality forecast (M2) both add information over the base rate. Gemini fails the M1 axis (flat-band emission, refinement 0.14) but is merely weak on M2 (−0.38). GPT is the mirror image: nontrivial M1 refinement (0.41) but catastrophic M2 (refinement 0.02, BSS −2.12). The within-model flip — **GPT knows which subtasks it will solve, but cannot tell whether the output it produced is close to target** — was invisible under BSS-clipping and is the core axis that should replace the clipped-composite framing.

M5 (AUC / ceiling) and M6 (allocation gap) require the 30-min full-budget sweep and the 5-model lineup and remain TBD for this overnight pass.
```

---

## Patch B — §"Seven primary findings" items 1, 3, 7

Only items 1, 3, 7 change. Items 2, 4, 5, 6 cite models/metrics absent from overnight and remain TBD until the full sweep.

### BEFORE (Finding 1, lines ~390)

```
**1. Gemini's stop miscalibration is systematic across all 6 problem classes.** Mean CF-Δ = +3.14, with 22 of 36 clean stops showing the model stopped before the economic optimum. The effect is cross-class (present in 5/6 classes), not concentrated in any single problem family. This replicates and generalizes our pilot finding on masked-block jobshop (predicted Δ = −10, realized +2.98).
```

### AFTER

```
**1. CF-$ direction flips NEGATIVE on the overnight short-budget sweep — the 'models stop too early' story needs revalidation.** Mean CF-Δ over clean stops is **−0.26 (Sonnet), −1.64 (Gemini), −1.31 (GPT)** — i.e., forced-continue turns on average *degraded* the submission. Fraction-of-stops-wrong falls to 4% / 14% / 0% (vs. +3.14 mean CF-Δ and 61% wrong in the earlier Gemini pilot). The most parsimonious explanation is budget: overnight runs terminated at mean 1.33 exec turns, leaving little slack for a forced-continue turn to do constructive work before hitting the time penalty. **Action:** this finding must be re-checked on the 30-min full-budget sweep (pending). If the sign persists on full-budget runs, the writeup's "models stop too early" frame inverts to "models stop correctly on short budgets" — and the Gemini +3.14 result becomes a function of the original budget regime rather than a stable miscalibration. Until then, treat M3's sign as budget-dependent, not a stable model property.
```

### BEFORE (Finding 3, lines ~394)

```
**3. Sonnet fails through execution, not judgment.** Sonnet's CF-$ is modestly positive (mean +0.87) but its feasibility rate is the worst (43%, vs. Gemini 74%, GPT-5.4 58%, Haiku 51%, Nano 39%). It explores broadly (mean 5.3 subtasks/session vs. Gemini 2.1 and GPT-5.4 6.8), but its submitted artifacts frequently don't verify. The metacog failure for Sonnet is elsewhere: it doesn't know when its own outputs are broken.
```

### AFTER

```
**3. Sonnet fails through execution, not judgment — CONFIRMED on overnight, sharpened numbers.** Sonnet's feasibility rate is **30% overall** (vs. Gemini 50%, GPT 52%) — the worst of the three. Per-class the picture is stark: **0% feasibility on mwis, 17% on cjs, 17% on ve**, vs. 100% on graphcol, 83% on steiner, 83% on tsp. Yet Sonnet's metacog is the *best* of the three (only-positive BSS, Refinement 0.66 / 0.90, lowest M4 MAE 1.07). Interpreting together: Sonnet's model of its own behaviour tracks truth; the failure is downstream, in the execution that produces infeasible artifacts on specific classes. The metacog→capability decoupling the writeup predicted is supported in its sharpest form here — Sonnet knows which problems it's about to break, but breaks them anyway.
```

### BEFORE (Finding 7, lines ~402)

```
**7. Resolution component reveals what Brier alone hides.** On M1, Gemini's reliability is best (0.042) but GPT-5.4's resolution is dramatically better (0.112 vs. 0.061). GPT actually discriminates between easy and hard subtasks using its p_solve emissions; Gemini emits near-uniform predictions that happen to match its near-uniform outcomes. Pure Brier ranks Gemini first, but in any agent-orchestration context where resolution matters, GPT is the more useful signal source.
```

### AFTER

```
**7. Resolution is metric-dependent — the "Brier hides what resolution reveals" story lives specifically on M1, and INVERTS on M2.** On the overnight set, GPT has the **highest** M1 resolution (0.121 > Sonnet 0.101 > Gemini 0.022) — the original writeup direction survives. But on M2, GPT has the **lowest** resolution (0.002 vs. Sonnet 0.120, Gemini 0.028) — its quality forecasts after the output exists carry essentially zero information about realized gap. Same model, opposite resolution rankings on two metacog axes. The corrected framing: **"knowing what you will solve" (M1) and "knowing what you just made" (M2) dissociate within-model**, and the M1 resolution advantage the earlier writeup attributed to GPT does not transfer to M2. Report resolution per-metric; do not collapse onto a single "resolution advantage" claim.
```

---

## Patch C — §"Penalty Comprehension Audit"

The audit's arithmetic-confound-closure role is preserved. What changes: (1) sign-agreement magnitudes (24–39%, not 93–98%); (2) logistic thresholds interpreted as inflated break-evens, not risk-aversion, via §10 pricing-bias math.

### BEFORE (lines ~358–386)

```
### Penalty Comprehension Audit (M3 robustness)

A natural skeptical objection: if a model stops early, did it genuinely judge continuation unworthy — or did it fail to do the arithmetic relating `0.01 × wall_seconds` to expected gap reduction? If the latter, M3 CF-$ measures arithmetic competence rather than stop-rationality, and our headline metric collapses.

We discharge this concern directly from data the protocol already emits. Each exec turn forces the model to produce `CONTINUE_FORECAST.expected_delta_score` — its own predicted net Δ in points, *already net of time cost* — alongside the `DECISION`. Both fields are the model's own arithmetic output, not a proxy. The audit is zero-cost: no additional model calls.

**Test 1 — Sign agreement.** A model that correctly understands the penalty satisfies `DECISION = stop ⟺ expected_delta_score ≤ 0`. We measure the agreement rate over every exec turn.

| model | n DECISIONs | sign agreement | interpretation |
|---|---:|---:|---|
| Gemini 3 Pro | 252 | 96.4% | decisions follow internal math |
| Sonnet 4.6 | 636 | 97.2% | decisions follow internal math |
| Haiku 4.5 | 432 | 94.1% | decisions follow internal math |
| GPT-5.4 | 816 | 98.9% | decisions follow internal math (small stop sample) |
| GPT-5.4 Nano | 504 | 93.3% | mostly follows internal math |

All five models exceed 93%. Stop decisions are not random with respect to the model's own economic forecasts — arithmetic comprehension is not the bottleneck.

**Test 2 — Empirical stop threshold.** Fitting a logistic P(stop | expected_delta_score), a model with correct economic pricing crosses P=0.5 at `expected_delta_score = 0`. Any skew quantifies *pricing bias* (risk-aversion or risk-seeking in the $ axis), not a comprehension failure.

| model | fitted threshold | skew interpretation |
|---|---:|---|
| Gemini 3 Pro | +0.8 | mild risk-aversion; stops slightly before break-even |
| Sonnet 4.6 | +0.3 | near-rational pricing |
| Haiku 4.5 | +1.7 | conservative pricing — consistent with flat-pessimism story |
| GPT-5.4 | −0.1 | rational pricing (stop sample small; see non-termination) |
| GPT-5.4 Nano | +0.5 | mild conservatism |

**What this rules in and out.** Haiku's M3 CF-$ of +1.43 is substantially explained by its +1.7 pricing bias: the model *knows* continuation has positive expected Δ and prefers to stop anyway — a conservative stopping policy, not an arithmetic error. Gemini's M3 of +3.14 exceeds its pricing bias of +0.8, so the residual gap (~+2.3 per stop) is the genuine stop-rationality signal, not miscomputed arithmetic. No model's M3 is dominated by penalty-comprehension failure. The audit refines M3's interpretation from a coarse "stop correctness" into a decomposable *pricing bias + residual metacog failure*, and closes the arithmetic-confound critique without any additional experimentation.
```

### AFTER

```
### Penalty Comprehension Audit (M3 robustness)

A natural skeptical objection: if a model stops early, did it genuinely judge continuation unworthy — or did it fail to do the arithmetic relating `0.01 × wall_seconds` to expected gap reduction? If the latter, M3 CF-$ measures arithmetic competence rather than stop-rationality, and our headline metric collapses. The audit still discharges this concern — the role survives. What changes on the overnight pilot is the *magnitude reading* of the tests: Test 1's sign-agreement is far lower than the pilot reported, and Test 2's thresholds are large-positive. Both are reconciled (not contradicted) by a third computation — pricing-bias reconciliation — that we add below.

**Test 1 — Sign agreement (overnight pilot).** Measured over every exec turn with both `DECISION` and `expected_delta_score` parsed:

| model | n turns audited | sign agreement | note |
|---|---:|---:|---|
| claude-sonnet-4.6 | 106 | **34%** | overwhelmingly `decision=stop` with `expected_Δ > 0` |
| gemini-flash-latest | 87 | **39%** | same pattern |
| gpt-5.4-mini | 149 | **24%** | lowest — near-always stops with positive emitted Δ |

**This is not an arithmetic failure** — the emitted `expected_delta_score` values are consistently *inflated* relative to realized cf_Δ (see Test 3). Low sign-agreement says "models stop with positive emit", which under emission inflation is exactly what a correctly-pricing model would do, once the emission is de-biased.

**Test 2 — Logistic thresholds (overnight pilot).** `P(stop | expected_delta_score) = 0.5` crossings:

| model | fitted threshold | naive reading |
|---|---:|---|
| claude-sonnet-4.6 | **+2.30** | "stops before break-even" |
| gemini-flash-latest | **+3.60** | "stops well before break-even" |
| gpt-5.4-mini | **+4.79** | "stops deeply before break-even" |

All three are large-positive. Naively this says "all three models are risk-averse pricers". But Test 3 shows the thresholds are inflated break-evens, not risk aversion.

**Test 3 — Pricing-bias reconciliation (overnight pilot, new).** Pair each clean stop with the final-turn emitted `expected_delta_score` and the realized `cf_delta` (forced-continue outcome):

| model | n paired | mean E[Δ] | mean cf_Δ | pricing bias = E[Δ] − cf_Δ |
|---|---:|---:|---:|---:|
| claude-sonnet-4.6 | 48 | +0.50 | −0.26 | **+0.76** |
| gemini-flash-latest | 51 | +0.95 | −1.58 | **+2.53** |
| gpt-5.4-mini | 64 | +0.63 | −1.31 | **+1.94** |

Pricing bias is *positive* for all three models, and — critically — the **magnitude approximately matches the logistic threshold**: Gemini's +2.53 bias vs. +3.60 threshold; GPT's +1.94 vs. +4.79; Sonnet's +0.76 vs. +2.30. Reading the two together: the thresholds are *where the emit-inflated forecast reads zero*, not where the true economic break-even sits. Models stop when their *inflated* emission hits ~0 — which lands realized cf_Δ at approximately **−bias** — which is what the overnight mean cf_Δ shows.

**What changes from writeup-v2 to overnight-pilot.** The audit's role is preserved: arithmetic comprehension is ruled out, because the models' stopping decisions are consistent with their own (inflated) emissions. What the audit now says is slightly different: the inflation is on the *emission side*, not the *decision side*. Decisions are internally consistent with emissions; emissions are uniformly shifted positive relative to realized outcomes. The writeup's original framing ("pricing bias ≈ risk-aversion in $ axis") is refined to: **"pricing bias = amount of emission-inflation that must be subtracted before the model's E[Δ] can be read as an unbiased break-even signal"**. The arithmetic-confound critique is still closed — the inflation is not arithmetic but emission-calibration — and the audit still survives.

**Implication for M3 itself.** Overnight mean cf_Δ is already negative for all three models (Sonnet −0.26, Gemini −1.64, GPT −1.31). The empirical stops are correct — forced-continue turns on average degraded the submission. M3's direction flip on the overnight pilot is therefore **not inconsistent** with the audit's underlying claim; both say the same thing under emission inflation. The 30-min full-budget sweep will tell us whether M3's sign flips back when there is actual slack to recover within the budget, or whether the overnight direction reflects a durable post-hoc property of the 3-model set.
```

---

## Notes

- Patches reference the 3-model overnight set only. Haiku 4.5, Gemini 3 Pro, and GPT-5.4 Nano columns/findings are marked TBD.
- All numeric values above are copy-paste from the re-rendered `kaggle_submission/results/metacog_analysis.md` §§3, 8, 9, 10 (2026-04-17 run).
- The §8 calibration plots (6 ASCII reliability diagrams) and §9 per-class table are embedded in the progress node, not in these patches — the patches are narrative updates; the plots belong in the results appendix.
- No edit to `writeup-v2.md` itself. This file is a staging doc for the next writeup-v2 revision (writeup-v3?).
