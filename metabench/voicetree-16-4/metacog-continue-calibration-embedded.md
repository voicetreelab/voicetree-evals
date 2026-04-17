---
color: green
isContextNode: false
agent_name: Anna
---
# Continue-forecast calibration table (final-turn p_improve vs cf_delta>0)

Final-turn `p_improve` scored against I[cf_delta>0] per (model, class, difficulty). GPT 0/42 observed improve rate — Brier=0.031 is all over-prediction. Gemini has the only cells where p_improve is under-confident (cjs_medium: emits 0.17, 100% improved → Brier 0.705).

Continue-forecast calibration per (model, class, difficulty). `rows_scored` = rows where a final-turn p_improve was parseable AND cf_delta was present. `vs_base` = Brier minus the empirical base-rate floor `p(1-p)` using that cell's observed rate.

| model | class | diff | rows | mean_p_improve | observed_rate | brier | vs_base | delta_mse |
|---|---|---|---|---|---|---|---|---|
| claude-sonnet-4.6 | cjs | medium | 1 | 0.10 | 0.00 | 0.010 | +0.010 | 0.04 |
| claude-sonnet-4.6 | graphcol | medium | 3 | 0.00 | 0.00 | 0.000 | +0.000 | 0.01 |
| claude-sonnet-4.6 | graphcol | hard | 3 | 0.00 | 0.00 | 0.000 | +0.000 | 0.00 |
| claude-sonnet-4.6 | mwis | hard | 1 | 0.20 | 0.00 | 0.040 | +0.040 | 1.00 |
| claude-sonnet-4.6 | steiner | medium | 3 | 0.08 | 0.33 | 0.242 | +0.020 | 18.68 |
| claude-sonnet-4.6 | steiner | hard | 2 | 0.08 | 0.00 | 0.006 | +0.006 | 0.24 |
| claude-sonnet-4.6 | tsp | medium | 3 | 0.20 | 0.33 | 0.208 | -0.014 | 0.38 |
| claude-sonnet-4.6 | tsp | hard | 3 | 0.20 | 0.00 | 0.040 | +0.040 | 0.73 |
| claude-sonnet-4.6 | ve | hard | 1 | 0.55 | 0.00 | 0.303 | +0.303 | 64.00 |
| claude-sonnet-4.6 | portfolio | medium | 14 | 0.04 | 0.00 | 0.002 | +0.002 | 1.02 |
| claude-sonnet-4.6 | portfolio | hard | 14 | 0.05 | 0.00 | 0.003 | +0.003 | 1.28 |
| gemini-flash-latest | cjs | medium | 3 | 0.17 | 1.00 | **0.705** | +0.705 | 100.88 |
| gemini-flash-latest | cjs | hard | 2 | 0.30 | 0.50 | 0.400 | +0.150 | 16.52 |
| gemini-flash-latest | graphcol | medium | 3 | 0.00 | 0.00 | 0.000 | +0.000 | 1.62 |
| gemini-flash-latest | graphcol | hard | 3 | 0.00 | 0.00 | 0.000 | +0.000 | 1.43 |
| gemini-flash-latest | mwis | medium | 3 | 0.32 | 0.00 | 0.114 | +0.114 | 16.75 |
| gemini-flash-latest | mwis | hard | 3 | 0.08 | 0.67 | 0.574 | +0.352 | 19.25 |
| gemini-flash-latest | steiner | medium | 3 | 0.07 | 0.00 | 0.005 | +0.005 | 2.25 |
| gemini-flash-latest | steiner | hard | 2 | 0.05 | 0.00 | 0.003 | +0.003 | 2.26 |
| gemini-flash-latest | tsp | medium | 3 | 0.17 | 0.00 | 0.037 | +0.037 | 4.07 |
| gemini-flash-latest | tsp | hard | 3 | 0.30 | 0.00 | 0.110 | +0.110 | 9.41 |
| gemini-flash-latest | ve | medium | 2 | 0.15 | 0.50 | 0.425 | +0.175 | 197.03 |
| gemini-flash-latest | ve | hard | 3 | 0.17 | 0.00 | 0.037 | +0.037 | 27.09 |
| gemini-flash-latest | portfolio | medium | 13 | 0.07 | 0.00 | 0.015 | +0.015 | 145.00 |
| gemini-flash-latest | portfolio | hard | 5 | 0.09 | 0.00 | 0.020 | +0.020 | 24.03 |
| gpt-5.4-mini | cjs | medium | 3 | 0.06 | 0.00 | 0.005 | +0.005 | 0.05 |
| gpt-5.4-mini | cjs | hard | 3 | 0.09 | 0.00 | 0.009 | +0.009 | 0.12 |
| gpt-5.4-mini | graphcol | medium | 3 | 0.25 | 0.00 | 0.125 | +0.125 | 7.01 |
| gpt-5.4-mini | graphcol | hard | 3 | 0.14 | 0.00 | 0.035 | +0.035 | 0.86 |
| gpt-5.4-mini | mwis | medium | 3 | 0.18 | 0.00 | 0.035 | +0.035 | 0.59 |
| gpt-5.4-mini | mwis | hard | 3 | 0.11 | 0.00 | 0.015 | +0.015 | 0.38 |
| gpt-5.4-mini | steiner | medium | 3 | 0.09 | 0.00 | 0.012 | +0.012 | 0.14 |
| gpt-5.4-mini | steiner | hard | 3 | 0.10 | 0.00 | 0.014 | +0.014 | 0.22 |
| gpt-5.4-mini | tsp | medium | 3 | 0.16 | 0.00 | 0.029 | +0.029 | 0.58 |
| gpt-5.4-mini | tsp | hard | 3 | 0.16 | 0.00 | 0.026 | +0.026 | 0.89 |
| gpt-5.4-mini | ve | medium | 3 | 0.35 | 0.00 | 0.206 | +0.206 | 21.92 |
| gpt-5.4-mini | ve | hard | 3 | 0.06 | 0.00 | 0.005 | +0.005 | 0.09 |
| gpt-5.4-mini | portfolio | medium | 14 | 0.09 | 0.00 | 0.013 | +0.013 | 146.09 |
| gpt-5.4-mini | portfolio | hard | 14 | 0.10 | 0.00 | 0.017 | +0.017 | 0.66 |

## Pattern read-out

- **Under-confidence cells (rare):** Gemini × cjs_medium (p=0.17 but 100% improved) — Gemini gave up too early. Gemini × cjs_hard (p=0.30 vs 50%), Sonnet × tsp_medium (p=0.20 vs 33%).
- **Over-confidence cells (dominant):** GPT × graphcol_medium (p=0.25 vs 0%), GPT × ve_medium (p=0.35 vs 0%), Sonnet × ve_hard (p=0.55 vs 0%), Gemini × mwis_medium (p=0.32 vs 0%).
- **`delta_mse` is large wherever expected_delta_score is on an unbounded scale** — portfolio and VE have MSE up to 197 (Gemini ve_medium) and 145 (Gemini portfolio_medium). Models emit plausibly-sized expected deltas but don't track the counterfactual's true magnitude.

detail [[metacog-forecast-analysis-done]]
