---
color: cyan
isContextNode: false
agent_name: Eli
---
# §9 — Per-class Brier decomposition (embedded)

21-row per-(model,class) Murphy decomposition table. Portfolio skipped for M1; included for M2.

# §9 — Per-class Brier decomposition (M1 and M2)

Per-(model, class) Murphy decomposition. M1 (p_solve → kept_as_best) skips portfolio; M2 includes portfolio.

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
| gpt-5.4-mini | portfolio | — | — | — | — | 192 | 0.059 | 0.059 | 0.000 |

**Reading the table.** Test Sonnet's M1 resolution by class: high on graphcol/steiner (feasibility-succeeding) → low on mwis/cjs (feasibility-failing) would show M1 self-knowledge directly predicts execution — Finding 3's underlying mechanism.

**Observed patterns.** Sonnet: highest M1 res on tsp (0.052) and steiner (0.051); M2 res best on tsp (0.075) and ve (0.000). GPT: M1 res peaks on graphcol (0.245) and ve (0.148) — its M1 resolution advantage is class-concentrated, not uniform. Gemini M1: cjs dominates (0.109); elsewhere near-zero — explains flat-forecaster M1 BSS.

artifact [[cora-metacog-writereport-extension-done]]
