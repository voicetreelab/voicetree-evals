---
color: green
isContextNode: false
agent_name: Anna
---
# Metacog Brier table — per model × class × difficulty

Full Quality Brier table (1104 turn-thresholds scored). Highest-Brier cells: Sonnet cjs_medium 0.883, Gemini portfolio_hard 0.548, Gemini cjs_hard 0.323, GPT steiner_hard 0.505. Lowest (trivial): Sonnet graphcol × both difficulties 0.000, GPT cjs × both 0.010/0.012.

Quality Brier by (model, class, difficulty). Columns `p_gap_le_k` show Brier at threshold k (lower = better; 0.0 = perfect, 0.25 = uniform-random on a 50/50 event). `turns` = count of turn × threshold scorings (one row contributes up to 3 × n_exec_turns entries).

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
| gpt-5.4-mini | portfolio | medium | 14 | 93 | 0.002 | 0.022 | 0.133 | 0.052 |
| gpt-5.4-mini | portfolio | hard | 14 | 99 | 0.004 | 0.032 | 0.163 | 0.066 |

VE rows re-scored against solo-style 2/5/10 thresholds (models emit solo keys on VE instead of the canonical 0.01/0.1/0.5; strict-parse fails for every VE row without this fallback).

## Drift (first-turn vs last-turn forecast on middle threshold)

| model | toward_truth | away_from_truth | flat | eligible (n_exec_turns≥2) |
|---|---|---|---|---|
| claude-sonnet-4.6 | 32 | 5 | 10 | 47 |
| gemini-flash-latest | 11 | 23 | 13 | 47 |
| gpt-5.4-mini | 6 | 5 | 53 | 64 |

Sonnet updates forecasts coherently (32 toward vs 5 away). Gemini updates incoherently (11 vs 23 — drifts *away* more often than toward). GPT largely doesn't update at all (53/64 runs have identical first and last forecast) — raises the question of whether GPT is integrating turn-level evidence at all when emitting forecasts.

detail [[metacog-forecast-analysis-done]]
