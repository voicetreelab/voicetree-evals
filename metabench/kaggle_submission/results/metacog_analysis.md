# Metacog Forecast Analysis — overnight 64-row set × 3 models

**Coverage:** 201 rows (192 expected = 64 unique row_ids × 3 models), 171 with ≥1 QUALITY_FORECAST (85%), 170 with ≥1 CONTINUE_FORECAST, 1224 forecast-turns scored against final realized gap.

**Headline:** Overall Quality Brier = 0.198 (lower is better; 0.25 = uniform-random floor) — but the model spread is large (Sonnet 0.096 / GPT 0.147 / Gemini 0.315) and much of the apparent calibration comes from correctly-low confidence on runs that end infeasible. **M1 (subtask p_solve Brier):** Claude Brier=0.186/res=0.101; Gemini Brier=0.221/res=0.037; Gpt Brier=0.287/res=0.101. GPT has the highest resolution (informativeness) on M1 despite the highest Brier — it moves `p_solve` around more, even though its calibration is worse than Sonnet's. Continue-forecast Brier = 0.067; models are mildly overconfident on `p_improve` (mean 0.11 vs. observed CF-improve rate 0.06) and essentially uninformative beyond 'stopping was the right call'.

## 1. Quality Brier by model × class × difficulty (mean over thresholds)

| model | class | diff | rows | turns | p_gap_le_2 | p_gap_le_5 | p_gap_le_10 | mean_brier |
|---|---|---|---|---|---|---|---|---|
| claude-sonnet-4.6 | cjs | medium | 3 | 6 | 0.748 | 0.922 | 0.980 | 0.883 |
| claude-sonnet-4.6 | cjs | hard | 3 | 0 | — | — | — | — |
| claude-sonnet-4.6 | graphcol | medium | 3 | 18 | 0.000 | 0.000 | 0.000 | 0.000 |
| claude-sonnet-4.6 | graphcol | hard | 3 | 18 | 0.000 | 0.000 | 0.000 | 0.000 |
| claude-sonnet-4.6 | mwis | medium | 3 | 0 | — | — | — | — |
| claude-sonnet-4.6 | mwis | hard | 3 | 6 | 0.076 | 0.331 | 0.681 | 0.363 |
| claude-sonnet-4.6 | steiner | medium | 3 | 21 | 0.203 | 0.203 | 0.008 | 0.138 |
| claude-sonnet-4.6 | steiner | hard | 3 | 15 | 0.238 | 0.077 | 0.011 | 0.109 |
| claude-sonnet-4.6 | tsp | medium | 3 | 30 | 0.167 | 0.231 | 0.373 | 0.257 |
| claude-sonnet-4.6 | tsp | hard | 3 | 42 | 0.279 | 0.154 | 0.141 | 0.191 |
| claude-sonnet-4.6 | ve | medium | 3 | 0 | — | — | — | — |
| claude-sonnet-4.6 | ve | hard | 3 | 3 | 0.062 | 0.203 | 0.423 | 0.229 |
| claude-sonnet-4.6 | portfolio | medium | 14 | 102 | 0.009 | 0.033 | 0.096 | 0.046 |
| claude-sonnet-4.6 | portfolio | hard | 14 | 99 | 0.003 | 0.012 | 0.044 | 0.020 |
| gemini-flash-latest | cjs | medium | 3 | 24 | 0.151 | 0.227 | 0.449 | 0.276 |
| gemini-flash-latest | cjs | hard | 3 | 12 | 0.045 | 0.237 | 0.688 | 0.323 |
| gemini-flash-latest | graphcol | medium | 3 | 18 | 0.000 | 0.000 | 0.000 | 0.000 |
| gemini-flash-latest | graphcol | hard | 3 | 24 | 0.203 | 0.106 | 0.021 | 0.110 |
| gemini-flash-latest | mwis | medium | 3 | 9 | 0.010 | 0.223 | 0.313 | 0.182 |
| gemini-flash-latest | mwis | hard | 3 | 24 | 0.210 | 0.394 | 0.481 | 0.362 |
| gemini-flash-latest | steiner | medium | 3 | 18 | 0.005 | 0.001 | 0.000 | 0.002 |
| gemini-flash-latest | steiner | hard | 3 | 12 | 0.004 | 0.001 | 0.000 | 0.002 |
| gemini-flash-latest | tsp | medium | 3 | 30 | 0.583 | 0.211 | 0.020 | 0.271 |
| gemini-flash-latest | tsp | hard | 3 | 21 | 0.403 | 0.249 | 0.023 | 0.225 |
| gemini-flash-latest | ve | medium | 3 | 12 | 0.448 | 0.716 | 0.003 | 0.389 |
| gemini-flash-latest | ve | hard | 3 | 18 | 0.540 | 0.654 | 0.002 | 0.399 |
| gemini-flash-latest | portfolio | medium | 14 | 111 | 0.304 | 0.420 | 0.612 | 0.445 |
| gemini-flash-latest | portfolio | hard | 14 | 42 | 0.411 | 0.559 | 0.675 | 0.548 |
| gpt-5.4-mini | cjs | medium | 3 | 18 | 0.000 | 0.003 | 0.032 | 0.012 |
| gpt-5.4-mini | cjs | hard | 3 | 18 | 0.000 | 0.004 | 0.027 | 0.010 |
| gpt-5.4-mini | graphcol | medium | 3 | 21 | 0.385 | 0.462 | 0.628 | 0.492 |
| gpt-5.4-mini | graphcol | hard | 3 | 39 | 0.118 | 0.181 | 0.414 | 0.238 |
| gpt-5.4-mini | mwis | medium | 3 | 18 | 0.003 | 0.022 | 0.122 | 0.049 |
| gpt-5.4-mini | mwis | hard | 3 | 21 | 0.001 | 0.011 | 0.064 | 0.025 |
| gpt-5.4-mini | steiner | medium | 3 | 18 | 0.342 | 0.492 | 0.624 | 0.486 |
| gpt-5.4-mini | steiner | hard | 3 | 18 | 0.348 | 0.504 | 0.661 | 0.505 |
| gpt-5.4-mini | tsp | medium | 3 | 21 | 0.006 | 0.068 | 0.359 | 0.145 |
| gpt-5.4-mini | tsp | hard | 3 | 18 | 0.288 | 0.381 | 0.236 | 0.301 |
| gpt-5.4-mini | ve | medium | 3 | 27 | 0.015 | 0.580 | 0.579 | 0.391 |
| gpt-5.4-mini | ve | hard | 3 | 18 | 0.427 | 0.610 | 0.165 | 0.401 |
| gpt-5.4-mini | portfolio | medium | 15 | 99 | 0.002 | 0.023 | 0.136 | 0.054 |
| gpt-5.4-mini | portfolio | hard | 14 | 99 | 0.004 | 0.032 | 0.163 | 0.066 |

(VE rows: re-scored against solo-style 2/5/10 thresholds. VE's canonical strict-parse contract requires 0.01/0.1/0.5, but every model in this set emits solo-style keys — flagged in caveats.)

## 2. Continue-forecast calibration (final-turn p_improve vs cf_delta>0)

| model | class | diff | rows_scored | mean_p_improve | observed_improve_rate | brier | vs_base | delta_mae |
|---|---|---|---|---|---|---|---|---|
| claude-sonnet-4.6 | cjs | medium | 1 | 0.10 | 0.00 | 0.010 | +0.010 | 0.20 |
| claude-sonnet-4.6 | graphcol | medium | 3 | 0.00 | 0.00 | 0.000 | +0.000 | 0.07 |
| claude-sonnet-4.6 | graphcol | hard | 3 | 0.00 | 0.00 | 0.000 | +0.000 | 0.07 |
| claude-sonnet-4.6 | mwis | hard | 1 | 0.20 | 0.00 | 0.040 | +0.040 | 1.00 |
| claude-sonnet-4.6 | steiner | medium | 3 | 0.08 | 0.33 | 0.242 | +0.020 | 2.72 |
| claude-sonnet-4.6 | steiner | hard | 2 | 0.08 | 0.00 | 0.006 | +0.006 | 0.46 |
| claude-sonnet-4.6 | tsp | medium | 3 | 0.20 | 0.33 | 0.208 | -0.014 | 0.51 |
| claude-sonnet-4.6 | tsp | hard | 3 | 0.20 | 0.00 | 0.040 | +0.040 | 0.85 |
| claude-sonnet-4.6 | ve | hard | 1 | 0.55 | 0.00 | 0.303 | +0.303 | 8.00 |
| claude-sonnet-4.6 | portfolio | medium | 14 | 0.04 | 0.00 | 0.002 | +0.002 | 0.98 |
| claude-sonnet-4.6 | portfolio | hard | 14 | 0.05 | 0.00 | 0.003 | +0.003 | 1.07 |
| gemini-flash-latest | cjs | medium | 3 | 0.17 | 1.00 | 0.705 | +0.705 | 8.13 |
| gemini-flash-latest | cjs | hard | 2 | 0.30 | 0.50 | 0.400 | +0.150 | 3.92 |
| gemini-flash-latest | graphcol | medium | 3 | 0.00 | 0.00 | 0.000 | +0.000 | 1.26 |
| gemini-flash-latest | graphcol | hard | 3 | 0.00 | 0.00 | 0.000 | +0.000 | 1.16 |
| gemini-flash-latest | mwis | medium | 3 | 0.32 | 0.00 | 0.114 | +0.114 | 3.50 |
| gemini-flash-latest | mwis | hard | 3 | 0.08 | 0.67 | 0.574 | +0.352 | 3.39 |
| gemini-flash-latest | steiner | medium | 3 | 0.07 | 0.00 | 0.005 | +0.005 | 1.48 |
| gemini-flash-latest | steiner | hard | 2 | 0.05 | 0.00 | 0.003 | +0.003 | 1.50 |
| gemini-flash-latest | tsp | medium | 3 | 0.17 | 0.00 | 0.037 | +0.037 | 1.99 |
| gemini-flash-latest | tsp | hard | 3 | 0.30 | 0.00 | 0.110 | +0.110 | 3.00 |
| gemini-flash-latest | ve | medium | 2 | 0.15 | 0.50 | 0.425 | +0.175 | 11.92 |
| gemini-flash-latest | ve | hard | 3 | 0.17 | 0.00 | 0.037 | +0.037 | 5.16 |
| gemini-flash-latest | portfolio | medium | 13 | 0.07 | 0.00 | 0.015 | +0.015 | 7.27 |
| gemini-flash-latest | portfolio | hard | 5 | 0.09 | 0.00 | 0.020 | +0.020 | 4.32 |
| gpt-5.4-mini | cjs | medium | 3 | 0.06 | 0.00 | 0.005 | +0.005 | 0.23 |
| gpt-5.4-mini | cjs | hard | 3 | 0.09 | 0.00 | 0.009 | +0.009 | 0.34 |
| gpt-5.4-mini | graphcol | medium | 3 | 0.25 | 0.00 | 0.125 | +0.125 | 1.67 |
| gpt-5.4-mini | graphcol | hard | 3 | 0.14 | 0.00 | 0.035 | +0.035 | 0.68 |
| gpt-5.4-mini | mwis | medium | 3 | 0.18 | 0.00 | 0.035 | +0.035 | 0.75 |
| gpt-5.4-mini | mwis | hard | 3 | 0.11 | 0.00 | 0.015 | +0.015 | 0.58 |
| gpt-5.4-mini | steiner | medium | 3 | 0.09 | 0.00 | 0.012 | +0.012 | 0.32 |
| gpt-5.4-mini | steiner | hard | 3 | 0.10 | 0.00 | 0.014 | +0.014 | 0.44 |
| gpt-5.4-mini | tsp | medium | 3 | 0.16 | 0.00 | 0.029 | +0.029 | 0.67 |
| gpt-5.4-mini | tsp | hard | 3 | 0.16 | 0.00 | 0.026 | +0.026 | 0.91 |
| gpt-5.4-mini | ve | medium | 3 | 0.35 | 0.00 | 0.206 | +0.206 | 3.14 |
| gpt-5.4-mini | ve | hard | 3 | 0.06 | 0.00 | 0.005 | +0.005 | 0.26 |
| gpt-5.4-mini | portfolio | medium | 15 | 0.09 | 0.00 | 0.013 | +0.013 | 6.69 |
| gpt-5.4-mini | portfolio | hard | 14 | 0.10 | 0.00 | 0.017 | +0.017 | 0.70 |

## 3. Metacognitive profile (writeup-v2 layout)

Model-level metacog metrics as framed in `kaggle_submission/writeup-v2.md`.  M1 (p_solve Brier) is computed over solo-class subtasks only — portfolio rows are skipped because we do not re-score per-sub-component best_guess payloads in this pass. M5 and M6 require additional runs.

| metric | claude-sonnet-4.6 | gemini-flash-latest | gpt-5.4-mini | what it measures |
|---|---|---|---|---|
| M1 Brier (p_solve) | 0.186 | 0.221 | 0.287 | knowing what you know — Brier on subtask-kept-as-best outcomes |
| — M1 reliability | 0.051 | 0.135 | 0.177 | Murphy: calibration component (lower=better) |
| — M1 resolution | 0.101 | 0.037 | 0.101 | Murphy: informativeness component (higher=better) |
| — M1 uncertainty | 0.236 | 0.125 | 0.213 | Murphy: base-rate entropy (not model-dependent) |
| — **M1 BSS** (unclipped) | +0.211 | -0.788 | -0.353 | skill score; NEGATIVE = worse than quoting base rate |
| — M1 refinement Res/(Res+Rel) | 0.663 | 0.216 | 0.365 | bounded [0,1] alternative to BSS |
| — M1 n (subtasks) | 34 | 48 | 52 | denominator — solo-class subtasks with parseable p_solve + best_guess |
| M2 Brier (quality forecast) | 0.097 | 0.331 | 0.165 | self-assessing output without oracle |
| — M2 reliability | 0.013 | 0.128 | 0.113 | Murphy: calibration component (lower=better) |
| — M2 resolution | 0.120 | 0.026 | 0.002 | Murphy: informativeness component (higher=better) |
| — M2 uncertainty | 0.204 | 0.233 | 0.052 | Murphy: base-rate entropy (not model-dependent) |
| — **M2 BSS** (unclipped) | +0.525 | -0.436 | -2.138 | skill score; NEGATIVE = worse than quoting base rate |
| — M2 refinement Res/(Res+Rel) | 0.902 | 0.170 | 0.017 | bounded [0,1] alternative to BSS |
| M3 CF-\$ mean Δ | -0.264 | -1.411 | -1.462 | knowing when to stop (clean stops only) |
| M3 CF-\$ median | -0.426 | -1.389 | -0.064 | clean-stop-restricted |
| M3 fraction-of-stops-wrong | 4% | 15% | 0% | % of clean stops where CF improved |
| M3 clean-stops n | 47 | 52 | 68 | denominator for M3 |
| M4 forecast error (MAE) | 1.07 | 5.94 | 2.08 | predicting value of more effort |
| Continue Brier | 0.040 | 0.139 | 0.030 | raw Brier on final-turn p_improve |
| Continue BSS | +0.01 | -0.10 | — | skill score vs. base-rate floor (>0 beats base rate; None=DEGEN) |
| Continue AUC | 0.92 | 0.64 | — | discrimination (None=one-class) |
| Sign agreement (DECISION↔Δ≤0) | 34% | 37% | 23% | penalty-comprehension audit Test 1 |
| Sign audit n (turns) | 106 | 92 | 157 |  |
| Logistic threshold | +2.30 | +106.71 | +4.79 | P(stop)=0.5 crossing over expected_delta_score; >0 = risk-averse pricing |
| Feasibility rate | 32% | 49% | 54% | % rows where final submission verifies feasible |
| Clean-stop rate | 71% | 78% | 100% | % rows ending via subtask_stop / turn1_stop |
| Non-termination rate | 29% | 22% | 0% | % rows hitting budget / timeout / error |
| Mean exec turns | 1.29 | 1.33 | 1.31 | n_exec_turns across rows |

**Logistic fit P(stop | expected_delta_score):**
- `claude-sonnet-4.6`: β₀ = +6.48, β₁ = -2.820, threshold = +2.30 (n = 106).  Interpretation: P(stop)=0.5 crosses when expected_delta_score = +2.30 — risk-averse (stops before break-even).
- `gemini-flash-latest`: β₀ = +0.87, β₁ = -0.008, threshold = +106.71 (n = 92).  Interpretation: P(stop)=0.5 crosses when expected_delta_score = +106.71 — risk-averse (stops before break-even).
- `gpt-5.4-mini`: β₀ = +2.32, β₁ = -0.484, threshold = +4.79 (n = 157).  Interpretation: P(stop)=0.5 crosses when expected_delta_score = +4.79 — risk-averse (stops before break-even).

**Feasibility rate per (model × class):**

| model | cjs | graphcol | mwis | steiner | tsp | ve | portfolio |
|---|---|---|---|---|---|---|---|
| claude-sonnet-4.6 | 17% | 100% | 0% | 83% | 83% | 17% | 4% |
| gemini-flash-latest | 67% | 100% | 100% | 83% | 100% | 83% | 0% |
| gpt-5.4-mini | 100% | 100% | 67% | 83% | 100% | 100% | 3% |

## 3a. M5 — Decomposition effectiveness (AUC / ceiling)

**M5 headline:** Claude M5=0.776 (n_eligible=8, ≥1 frac=12%); Gemini M5=0.825 (n_eligible=11, ≥1 frac=9%); Gpt M5=0.945 (n_eligible=3, ≥1 frac=67%). Per-row M5 = AUC(score trajectory) / (cell ceiling × (n_turns−1)). Ceilings are max final_score across the (model, class, difficulty) seeds in the overnight pilot; infeasible rows contribute 0 to ceilings. Rows with n_exec_turns < 2 are M5-undefined (no interval to integrate) and reported separately; cells where the ceiling is 0 fall back to the per-class ceiling across difficulties, or are excluded if that is also 0. M5 > 1 is possible and NOT clipped — it indicates the row's trajectory area beats the cell's ceiling rectangle.

### M5 per-model rollup

| model | mean M5 | frac M5 ≥ 1 | n eligible | n trivial (n_turns<2) | n zero-ceiling | total rows |
|---|---|---|---|---|---|---|
| claude-sonnet-4.6 | 0.776 | 12% | 8 | 30 | 0 | 38 |
| gemini-flash-latest | 0.825 | 9% | 11 | 28 | 0 | 39 |
| gpt-5.4-mini | 0.945 | 67% | 3 | 33 | 3 | 39 |

### M5 per-(model, class) breakdown (aggregated across difficulties)

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

**Interpretation.** A model that reaches its own cell ceiling fast and holds it earns high M5; a model that leaves score on the table by stopping early, oscillating, or failing to recover after a bad intermediate turn earns low M5. M5 is capability-controlled by design (the denominator is the model's OWN ceiling in the cell), so a lower-capability model with a low ceiling can still score high M5 if it uses its turns efficiently. Caveat: mean n_exec_turns overnight is ~1.3, so many rows are trivially excluded; M5 is informative only where a model took ≥2 exec turns in a cell.

## 4. Model-level rollup (raw)

| model | rows | mean_quality_brier | mean_continue_brier | base_floor | Δvs_base | mean_p_improve | observed_rate |
|---|---|---|---|---|---|---|---|
| claude-sonnet-4.6 | 66 | 0.097 | 0.040 | 0.040 | -0.000 | 0.08 | 0.04 |
| gemini-flash-latest | 67 | 0.331 | 0.139 | 0.126 | +0.013 | 0.13 | 0.15 |
| gpt-5.4-mini | 68 | 0.165 | 0.030 | 0.000 | +0.030 | 0.12 | 0.00 |

## 4. Forecast drift (first vs last turn, middle threshold)

| model | toward_truth | away_from_truth | flat | eligible_rows (n_exec_turns≥2) |
|---|---|---|---|---|
| claude-sonnet-4.6 | 32 | 5 | 10 | 47 |
| gemini-flash-latest | 11 | 25 | 14 | 50 |
| gpt-5.4-mini | 6 | 6 | 56 | 68 |

## 5. Missing / malformed forecasts

- **claude-sonnet-4.6**: 66 rows, 18 rows with no QF (27%), 18 with no CF, 18 with no parsed turns at all.
- **gemini-flash-latest**: 67 rows, 12 rows with no QF (18%), 13 with no CF, 12 with no parsed turns at all.
- **gpt-5.4-mini**: 68 rows, 0 rows with no QF (0%), 0 with no CF, 0 with no parsed turns at all.

## 6. Findings

1. **Quality forecasts beat uniform-random but mostly by staying pessimistic.** Overall mean Brier = 0.198. For context: 0.000 = oracle, 0.250 = uniform random. The biggest Brier contributions are from individual model×class cells where forecasts swing high but realized `I[gap≤k]` is 0 — e.g. Sonnet on **cjs_medium** (0.883 Brier, 6 turns, over-predicting gap ≤ 2) and Gemini on **portfolio_hard** (0.548) / **mwis_hard** (0.362). Conversely, the many 0.000 cells are trivial: the model emits 1.0 for a feasible, low-gap run (e.g. Sonnet graphcol × both difficulties) or 0.0 for a clearly-failed portfolio row.
2. **Quality-Brier ranking across models:** claude-sonnet-4.6 = 0.097, gpt-5.4-mini = 0.165, gemini-flash-latest = 0.331 (lower is better; gap = 0.234).
3. **GPT-5.4-mini is the clearest case of miscalibrated `p_improve`.** GPT's CF branches improved 0/42 times (observed rate = 0.00), so the optimal constant predictor would say 0.00 and score Brier = 0.00. GPT instead emits mean p_improve = 0.12, yielding Brier = 0.030 — i.e. all of its Brier comes from over-predicting improvement that never materialized. Sonnet's 4% / Gemini's 14% base rate leave a small informative margin; all three sit within ±0.03 of their own base-rate floors, so the forecast adds almost no resolution over just quoting the base rate.
4. **Portfolio Brier is numerically *lower* than solo — but this is a trivial win, not a calibration signal.** Portfolio Brier = 0.165 (n=552 turn-thresholds), solo Brier = 0.226 (n=672). On portfolio, ~97% of rows are infeasible (realized `I[gap≤k] = 0`), and models emit correspondingly low p_gap_le_k values — so squared error stays small for the wrong reason. **Solo-class Brier is the honest calibration metric** because feasibility ≈ 100% there, so realized labels actually vary across turns.
5. **`expected_delta_score` regression fit is weak.** MAE = 3.02 across 170 final-turn predictions against cf_delta. This is consistent with models treating CONTINUE_FORECAST as a cursory emission rather than an estimate grounded in a cost model for their own turn.

## 7. Open questions / caveats

- **M1 skips portfolio rows.** Portfolio BEST_GUESS is a nested dict keyed by sub-component problem_id and would need per-sub-component verifier routing. M1 is therefore computed on solo-class subtasks only (n = 34–49 subtasks per model; 28–36 rows per model contribute). Subtasks without a parseable `best_guess` are also skipped (no outcome to label).
- **M1 outcome is `kept_as_best`, not `feasible`.** Subtask 1 is kept_as_best=1 iff feasible (no prior to beat); subtask k≥2 is kept_as_best=1 iff its verified gap_pct is strictly lower than every prior subtask's gap_pct. This is the writeup-v2 framing; using `feasible` alone would make kept_as_best monotone-decreasing across turns and hide subtasks that improve on a feasible baseline.
- **Per-turn ground truth is unavailable.** We only have the final realized gap (from `final_evaluation.gap_pct`) and the counterfactual-continue delta (`cf_delta`). For multi-turn runs, intermediate best_guess scores are not stored, so mid-run quality forecasts are scored against the *final* gap — biasing calibration for models whose final turn improved over mid-run state.
- **Infeasible rows are treated as realized=0 for all thresholds.** This is the natural reading (quality target was not met) but does penalize models that forecast some probability of hitting a gap target before their submission is rejected by the feasibility layer.
- **`cf_delta` is a noisy signal for continue-forecast calibration.** The CF branch runs a single additional turn from the same state, but with a different random draw. A model's p_improve could legitimately be 0.6 and still see cf_delta ≤ 0 due to the specific CF trajectory.
- **Portfolio uses solo-style thresholds (2/5/10).** Confirmed from `cf_parsed` entries in `portfolio_*_seedN.json`. If the intent was a portfolio-specific threshold set, the forecasts-as-emitted can't reflect that.
- **VE protocol drift: models emit solo keys for VE.** `harness/protocol.py` defines `VE_GAP_THRESHOLDS = (0.01, 0.1, 0.5)` and the emit-spec says 'or the VE-specific thresholds if this is `ve`', but *every* VE transcript in the overnight set emits `p_gap_le_2 / 5 / 10`. This analysis falls back to solo-style parsing for VE so we can score them; the strict-parse path in `parse_quality_forecast(text, cls='ve')` returns None for all of them. That is a real bug in the VE exec-turn prompting — either rephrase the prompt so models actually emit VE keys, or collapse VE onto the solo threshold schema permanently.
- **64-row set, not 206.** The overnight pilot that fed this analysis contains 64 unique row_ids (7 classes × 2 difficulties × 3 seeds, plus 28 extra portfolio seeds). Each is scored × 3 models = 192 row-model pairs. The 206 headline from the wake-up brief includes some runs/ top-level files and other artifacts.

## 8. Calibration plots (M1 and M2)

Binned reliability diagrams per model. Each row is one 0.1-wide bin of the forecast. Position `.` marks the bin's mean forecast p̄; position `o` marks the bin's observed frequency ȳ; `X` means they coincide. The horizontal displacement between `.` and `o` is the bin's reliability residual. Vertical spread of ȳ across bins = resolution.

```text
M1 calibration — claude-sonnet-4.6
Brier=0.186  reliability=0.051  resolution=0.101  uncertainty=0.236  n=34
bin            n     p̄      ȳ   |0.0-------0.25-------0.5-------0.75-------1.0|
[0.0,0.1)      0      —      —   |                                        |
[0.1,0.2)      0      —      —   |                                        |
[0.2,0.3)      0      —      —   |                                        |
[0.3,0.4)      0      —      —   |                                        |
[0.4,0.5)      1   0.45   0.00   |o                 .                     |
[0.5,0.6)      7   0.51   0.29   |           o        .                   |
[0.6,0.7)      7   0.63   0.29   |           o             .              |
[0.7,0.8)     15   0.75   0.87   |                             .    o     |
[0.8,0.9)      4   0.81   1.00   |                                .      o|
[0.9,1.0)      0      —      —   |                                        |
Legend: '.' = forecast p̄ for bin | 'o' = observed ȳ | 'X' = same position (perfect calibration in that bin)
```

```text
M1 calibration — gemini-flash-latest
Brier=0.221  reliability=0.135  resolution=0.037  uncertainty=0.125  n=48
bin            n     p̄      ȳ   |0.0-------0.25-------0.5-------0.75-------1.0|
[0.0,0.1)      0      —      —   |                                        |
[0.1,0.2)      1   0.10   1.00   |    .                                  o|
[0.2,0.3)      2   0.20   1.00   |        .                              o|
[0.3,0.4)      2   0.32   0.50   |             .      o                   |
[0.4,0.5)      5   0.40   1.00   |                .                      o|
[0.5,0.6)     13   0.50   0.85   |                    .            o      |
[0.6,0.7)      2   0.60   0.50   |                    o  .                |
[0.7,0.8)      4   0.71   1.00   |                            .          o|
[0.8,0.9)      6   0.81   0.50   |                    o           .       |
[0.9,1.0)     13   0.93   1.00   |                                    .  o|
Legend: '.' = forecast p̄ for bin | 'o' = observed ȳ | 'X' = same position (perfect calibration in that bin)
```

```text
M1 calibration — gpt-5.4-mini
Brier=0.287  reliability=0.177  resolution=0.101  uncertainty=0.213  n=52
bin            n     p̄      ȳ   |0.0-------0.25-------0.5-------0.75-------1.0|
[0.0,0.1)      0      —      —   |                                        |
[0.1,0.2)      0      —      —   |                                        |
[0.2,0.3)     10   0.23   0.10   |    o    .                              |
[0.3,0.4)     17   0.34   0.82   |             .                  o       |
[0.4,0.5)     17   0.42   0.88   |                .                 o     |
[0.5,0.6)      0      —      —   |                                        |
[0.6,0.7)      0      —      —   |                                        |
[0.7,0.8)      5   0.76   1.00   |                             .         o|
[0.8,0.9)      0      —      —   |                                        |
[0.9,1.0)      3   0.96   0.33   |             o                       .  |
Legend: '.' = forecast p̄ for bin | 'o' = observed ȳ | 'X' = same position (perfect calibration in that bin)
```

```text
M2 calibration — claude-sonnet-4.6
Brier=0.097  reliability=0.013  resolution=0.120  uncertainty=0.204  n=360
bin            n     p̄      ȳ   |0.0-------0.25-------0.5-------0.75-------1.0|
[0.0,0.1)     86   0.05   0.00   |o .                                     |
[0.1,0.2)     74   0.12   0.04   |  o  .                                  |
[0.2,0.3)     48   0.21   0.10   |    o   .                               |
[0.3,0.4)     20   0.33   0.05   |  o          .                          |
[0.4,0.5)     17   0.43   0.41   |                o.                      |
[0.5,0.6)     18   0.52   0.56   |                    . o                 |
[0.6,0.7)      8   0.63   0.50   |                    o    .              |
[0.7,0.8)     18   0.73   0.83   |                            .   o       |
[0.8,0.9)     21   0.83   0.57   |                      o         .       |
[0.9,1.0)     50   0.98   0.92   |                                    o . |
Legend: '.' = forecast p̄ for bin | 'o' = observed ȳ | 'X' = same position (perfect calibration in that bin)
```

```text
M2 calibration — gemini-flash-latest
Brier=0.331  reliability=0.128  resolution=0.026  uncertainty=0.233  n=393
bin            n     p̄      ȳ   |0.0-------0.25-------0.5-------0.75-------1.0|
[0.0,0.1)     19   0.02   0.00   |o.                                      |
[0.1,0.2)     31   0.10   0.16   |    . o                                 |
[0.2,0.3)     23   0.20   0.26   |        . o                             |
[0.3,0.4)     32   0.30   0.25   |          o .                           |
[0.4,0.5)     11   0.40   0.36   |              o .                       |
[0.5,0.6)     25   0.50   0.28   |           o        .                   |
[0.6,0.7)     24   0.60   0.29   |           o           .                |
[0.7,0.8)     13   0.70   0.46   |                  o        .            |
[0.8,0.9)     35   0.80   0.23   |         o                     .        |
[0.9,1.0)    180   0.96   0.53   |                     o                . |
Legend: '.' = forecast p̄ for bin | 'o' = observed ȳ | 'X' = same position (perfect calibration in that bin)
```

```text
M2 calibration — gpt-5.4-mini
Brier=0.165  reliability=0.113  resolution=0.002  uncertainty=0.052  n=471
bin            n     p̄      ȳ   |0.0-------0.25-------0.5-------0.75-------1.0|
[0.0,0.1)    207   0.04   0.03   | o.                                     |
[0.1,0.2)     48   0.15   0.10   |    o .                                 |
[0.2,0.3)     74   0.23   0.04   |  o      .                              |
[0.3,0.4)     25   0.35   0.04   |  o           .                         |
[0.4,0.5)     10   0.42   0.00   |o               .                       |
[0.5,0.6)     31   0.52   0.00   |o                   .                   |
[0.6,0.7)     21   0.62   0.19   |       o                .               |
[0.7,0.8)     15   0.70   0.13   |     o                     .            |
[0.8,0.9)      2   0.82   0.00   |o                               .       |
[0.9,1.0)     38   0.97   0.11   |    o                                 . |
Legend: '.' = forecast p̄ for bin | 'o' = observed ȳ | 'X' = same position (perfect calibration in that bin)
```

## 9. Per-class Brier decomposition (M1 and M2)

Per-(model, class) Murphy decomposition. M1 (p_solve → kept_as_best) skips portfolio. M2 includes portfolio.

| model | class | M1 n | M1 Brier | M1 rel | M1 res | M2 n | M2 Brier | M2 rel | M2 res |
|---|---|---|---|---|---|---|---|---|---|
| claude-sonnet-4.6 | cjs | 1 | 0.303 | 0.303 | 0.000 | 6 | 0.883 | 0.883 | 0.000 |
| claude-sonnet-4.6 | graphcol | 6 | 0.055 | 0.055 | 0.000 | 36 | 0.000 | 0.000 | 0.000 |
| claude-sonnet-4.6 | mwis | 1 | 0.423 | 0.423 | 0.000 | 6 | 0.363 | 0.363 | 0.000 |
| claude-sonnet-4.6 | steiner | 7 | 0.107 | 0.036 | 0.051 | 36 | 0.126 | 0.034 | 0.007 |
| claude-sonnet-4.6 | tsp | 18 | 0.248 | 0.055 | 0.052 | 72 | 0.219 | 0.041 | 0.075 |
| claude-sonnet-4.6 | ve | 1 | 0.062 | 0.062 | 0.000 | 3 | 0.229 | 0.229 | 0.000 |
| claude-sonnet-4.6 | portfolio | — | — | — | — | 201 | 0.033 | 0.033 | 0.000 |
| gemini-flash-latest | cjs | 8 | 0.235 | 0.235 | 0.109 | 36 | 0.292 | 0.183 | 0.023 |
| gemini-flash-latest | graphcol | 8 | 0.074 | 0.074 | 0.000 | 42 | 0.063 | 0.063 | 0.000 |
| gemini-flash-latest | mwis | 8 | 0.237 | 0.133 | 0.005 | 33 | 0.313 | 0.198 | 0.017 |
| gemini-flash-latest | steiner | 5 | 0.004 | 0.004 | 0.000 | 30 | 0.002 | 0.001 | 0.000 |
| gemini-flash-latest | tsp | 11 | 0.231 | 0.077 | 0.039 | 51 | 0.252 | 0.220 | 0.006 |
| gemini-flash-latest | ve | 5 | 0.476 | 0.476 | 0.000 | 30 | 0.395 | 0.200 | 0.039 |
| gemini-flash-latest | portfolio | — | — | — | — | 153 | 0.474 | 0.473 | 0.000 |
| gpt-5.4-mini | cjs | 6 | 0.445 | 0.444 | 0.000 | 36 | 0.011 | 0.010 | 0.000 |
| gpt-5.4-mini | graphcol | 14 | 0.175 | 0.175 | 0.245 | 60 | 0.327 | 0.326 | 0.000 |
| gpt-5.4-mini | mwis | 7 | 0.255 | 0.114 | 0.102 | 39 | 0.036 | 0.036 | 0.000 |
| gpt-5.4-mini | steiner | 6 | 0.324 | 0.191 | 0.006 | 36 | 0.495 | 0.495 | 0.000 |
| gpt-5.4-mini | tsp | 7 | 0.323 | 0.323 | 0.122 | 39 | 0.217 | 0.043 | 0.018 |
| gpt-5.4-mini | ve | 9 | 0.265 | 0.182 | 0.148 | 45 | 0.395 | 0.198 | 0.039 |
| gpt-5.4-mini | portfolio | — | — | — | — | 198 | 0.060 | 0.059 | 0.000 |

**Reading the table.** Test Sonnet's M1 resolution by class: high on graphcol/steiner (feasibility-succeeding) → low on mwis/cjs (feasibility-failing) would show M1 self-knowledge directly predicts execution — Finding 3's underlying mechanism.

## 10. Pricing bias vs. stop-rationality reconciliation

Reconciles logistic thresholds (+2.3/+3.6/+4.8) with CF-$ means (−0.26/−1.64/−1.31). If mean(E[Δ]) − mean(cf_Δ) is large positive, the signals reconcile as pricing bias.

| model | n turns | mean E[Δ] (all) | n paired | mean E[Δ] (final) | mean cf_Δ | pricing bias |
|---|---|---|---|---|---|---|
| claude-sonnet-4.6 | 120 | +1.33 | 48 | +0.50 | -0.26 | +0.76 |
| gemini-flash-latest | 130 | +4.10 | 54 | +2.56 | -1.36 | +3.92 |
| gpt-5.4-mini | 157 | +1.02 | 68 | +0.62 | -1.46 | +2.08 |

**Uniform shift or resolution-dependent?** Split each model's paired final-turn population at its own median E[Δ]. Flat bias ⇒ bias_low ≈ bias_high. Scaling bias (emission growing with forecast) ⇒ bias_high > bias_low.

| model | median E[Δ] | n_low | low E[Δ] | low cf_Δ | low bias | n_high | high E[Δ] | high cf_Δ | high bias |
|---|---|---|---|---|---|---|---|---|---|
| claude-sonnet-4.6 | +0.30 | 26 | +0.14 | -0.42 | +0.56 | 22 | +0.93 | -0.06 | +0.99 |
| gemini-flash-latest | +0.50 | 37 | +0.23 | -2.34 | +2.56 | 17 | +7.65 | +0.77 | +6.88 |
| gpt-5.4-mini | +0.40 | 40 | +0.22 | -0.79 | +1.01 | 28 | +1.19 | -2.42 | +3.61 |

**Interpretation.** Paired pricing biases are claude +0.76, gemini +3.92, gpt +2.08. Across low/high split, bias changes by claude Δ=+0.43, gemini Δ=+4.32, gpt Δ=+2.60. Positive paired bias + bias ≈ logistic threshold ⇒ thresholds are inflated break-evens, not risk-aversion: models stop when emit-inflated forecast hits ~0, landing realized cf_Δ at ≈ −bias. Penalty-Audit direction preserved; magnitude reading shifts from 'risk-averse pricing' to 'emissions need de-biasing before being read as break-even'.

Script: `kaggle_submission/scripts/analyze_metacog.py`
CSV rollup: `kaggle_submission/results/metacog_rollup.csv`
Calibration bins CSV: `kaggle_submission/results/metacog_calibration_bins.csv`
