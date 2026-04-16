---
color: green
isContextNode: false
agent_name: Jose
---
# HCH HLE-12 Brier decomposition — calibration vs resolution across 5 arms

Murphy (1973) Brier decomposition across 5 HCH HLE-12 arms reveals near-zero resolution in all models. Haiku 'flat-prediction' hypothesis refuted: std(p_atomic)=0.199 (variable), but AUC=0.409 (anti-discriminating). Ranking reshuffles completely under resolution-only metric. Root cause of low resolution: extreme base rates (0-87.5% accuracy) suppress the uncertainty ceiling for resolution.

## Full Comparison Table

| Model | VanAcc | A1 Brier | A1 Rel | A1 Res | A1 AUC | D Brier | D Rel | D Res | D AUC | std_pAtomic | std_pD | Old Comp | Res Comp |
|-------|--------|---------|--------|--------|--------|---------|-------|-------|-------|------------|--------|---------|----------|
| v1 Gemini 2.5 Flash | 0/12 (0%) | 0.537 | 0.532 | 0.000 | N/A | 0.934 | 0.933 | 0.000 | N/A | 0.285 | 0.039 | 0.736 | 1.000 |
| Gemini 3.1 Pro | 7/8 (87.5%) | 0.004 | 0.004 | 0.000 | N/A† | 0.335 | 0.094 | 0.000 | 0.000 | 0.020 | 0.024 | 0.169 | 1.000 |
| GPT-5.4 base | 0/4 (0%) | 0.427‡ | N/A | N/A | N/A | 0.297‡ | N/A | N/A | N/A | 0.070 | 0.095 | 0.362 | N/A |
| GPT-5.4 Nano | 1/12 (8.3%) | 0.144 | 0.063 | 0.014 | 0.545 | 0.455 | 0.449 | 0.000 | N/A | 0.177 | 0.245 | 0.300 | 0.993 |
| Claude Haiku 4.5 | 1/12 (8.3%) | 0.253 | 0.188 | 0.010 | 0.409 | 0.393 | 0.260 | 0.031 | 0.556 | 0.199 | 0.279 | 0.323 | 0.980 |

† Gemini31Pro A1: N=5 pairs, all vanilla outcomes=1 (no negative class) → AUC undefined, Resolution forced to 0.  
‡ GPT-5.4 base: N=2 paired questions, Brier computed but decomposition requires N≥3.

Definitions:
- **Old Comp** = mean(A1_Brier, D_Brier) — lower is better
- **Res Comp** = 1 − mean(A1_Res, D_Res) — lower is better, rewards discrimination
- **Bins used:** 4 bins (n_bins=4), valid for N≥3. GPT54base skipped (N=2).

---

## Rankings — Old vs Resolution-Only

**OLD COMPOSITE (mean A1+D Brier) — lower is better:**
1. Gemini 3.1 Pro — 0.169  
2. GPT-5.4 Nano — 0.300  
3. Claude Haiku 4.5 — 0.323  
4. GPT-5.4 base — 0.362 (N too small)  
5. v1 Gemini 2.5 Flash — 0.736  

**RESOLUTION-ONLY COMPOSITE (1 − mean resolution) — lower is better:**
1. Claude Haiku 4.5 — 0.980 (combined resolution=0.020)  
2. GPT-5.4 Nano — 0.993 (combined resolution=0.007)  
3–4. v1 Gemini 2.5 Flash & Gemini 3.1 Pro — 1.000 (resolution=0, degenerate)  

**Key ranking flip:** Gemini 3.1 Pro drops from #1 (old composite) to last-place tie (res-only). Haiku rises from #3 to #1. This is NOT because Haiku has better discrimination — it's because both Gemini31Pro (#1→last) and Haiku (#3→1st) are degenerate in different directions: Gemini31Pro hits near-100% accuracy (all outcomes=1, resolution=0 by construction), while Haiku barely ekes out non-zero resolution from its 8.3% / 16.7% split. The 0.020 combined resolution for Haiku vs 0.000 for Gemini31Pro is statistical noise, not real signal.

---

## Haiku Flat-Prediction Hypothesis: REFUTED (but nuanced)

**Hypothesis (task spec):** Haiku uses "uniform pessimism" — predicts low confidence on everything, gets good Brier for free on a hard dataset.

**Finding: Prediction variance is NOT near-zero**
- std(p_correct_if_atomic) = **0.199** — Haiku actively varies its A1 predictions (range 0.15–0.75)
- std(P_CORRECT_HCH) = **0.279** — even more spread on Axis D
- So uniform pessimism as a prediction strategy is NOT occurring

**But resolution is still near-zero:**
- A1 Resolution = 0.010, AUC = **0.409** (below chance)
- D Resolution = 0.031, AUC = 0.556

**Mechanism (corrected):** Haiku's predictions are variable but *anti-correlated* with outcomes on A1 (AUC < 0.5 means it assigns higher p_correct_if_atomic to questions the vanilla arm gets wrong). The near-zero resolution is not from flat predictions — it's from poor discrimination regardless of spread. The better Brier vs v1 Flash arises from moderate overconfidence (0.25–0.75 range) vs v1's extreme overconfidence (0.5–1.0 range) on a dataset where accuracy = 0–8%.

---

## One-Paragraph Insight for HCH Spec v3

The Brier decomposition exposes a deeper structural problem than reward-hacking: **all five arms show near-zero resolution regardless of model quality**, because the HLE-12 question set has extreme base rates (0% or 8% for most arms; 87.5% for Gemini31Pro which only completed 8 questions). Resolution = Σ(nₖ/N)(ōₖ − ō)² is bounded above by ō(1−ō) (the uncertainty term), so at 8% accuracy, the maximum achievable resolution is 0.074 — even perfect AUC would yield resolution < 0.074. None of the models come close. The practical implication for spec v3: **(1)** include a difficulty-stratified question set targeting 30–60% aggregate baseline accuracy to open the resolution ceiling; **(2)** replace or supplement the total Brier score with AUC as the primary discrimination metric (it is base-rate-invariant and more robust at small N); **(3)** always report all three Murphy components (Reliability, Resolution, Uncertainty) in the metacog scorecard — total Brier alone conceals whether a model is well-calibrated because it's accurate vs. because the questions are all hard.

### NOTES

- v1 Gemini25Flash data is degenerate for decomposition: 0% accuracy means all outcomes=0, uncertainty=0, resolution=0 always. A1 Brier=0.537 = pure Reliability (systematic overconfidence).
- Gemini31Pro A1 analysis limited to N=5 (7 missing p_correct_if_atomic). With 5/5 vanilla correct, outcome distribution has no negative class — AUC undefined, resolution=0 forced. This is a data quality gap, not a model property.
- GPT-5.4 base: only 4 questions (2 paired), N too small for decomposition. Excluded from ranking.
- The 'composite Brier 0.55' referenced in the task spec for Haiku did not match computed values (0.323 for mean A1+D). This may refer to a different composite formulation from an interim analysis before all pilot notes were complete.
- Bins=4 for Murphy decomposition. With N=10-12 per arm, some bins have nₖ=1-3, making bin-level statistics noisy. AUC is more robust at this N.
- D AUC for GPT54Nano = N/A because 0/12 HCH tasks correct → no positive class for AUC computation.

## Related

- [ivan-haiku-hle12-complete](ivan-haiku-hle12-complete.md)
- [jay-gptnano-hle12-complete](jay-gptnano-hle12-complete.md)
- [gus-gemini3pro-hle12-complete](gus-gemini3pro-hle12-complete.md)

[[task_1776257126742r2s]]
