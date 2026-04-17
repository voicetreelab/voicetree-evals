---
color: blue
isContextNode: false
agent_name: Amit
---
# Evidence — seeds 14, 5, 25 × 3 models

Row-by-row evidence table: each portfolio row breaks on a different sub-component (MWIS for seed14, TSP for seed5/25), and the three models fail in three different ways on the SAME row. Pattern is schema non-compliance, not optimisation quality.

## portfolio_medium_seed14 (cjs + mwis + steiner)

| Model | CJS | MWIS | Steiner | Overall |
|---|---|---|---|---|
| claude-sonnet-4.6 | feasible (baseline echo) | **feasible=False** — `{"selected": []}` emitted; verifier wants `selected_vertices` list | feasible (baseline echo) | **False** |
| gpt-5.4-mini | feasible (baseline echo) | **feasible=False** — submitted `mwis_medium_seed14: null` | feasible (baseline echo) | **False** |
| gemini-flash-latest | feasible (baseline echo) | **feasible=False** — submitted bare list `["Cape","Dune","Mill","Peak","Reef","Vale"]` (Steiner location names, not MWIS vertex IDs, not wrapped in object) | **feasible=False** — deleted required `frequencies` field (`failure_reason: "frequencies must be an object"`); subtask_body says "I removed the extraneous `frequencies` field from the Steiner tree output to adhere to the standard format" | **False** |

Verbatim submission excerpts (line numbers in `kaggle_submission/results/full/portfolio_medium_seed14/`):
- Sonnet `claude-sonnet-4.6.json:859-861` — `"mwis_medium_seed14": {"selected": []}`
- GPT `gpt-5.4-mini.json:338` — `"mwis_medium_seed14": null`
- Gemini `gemini-flash-latest.json:338-345` — `"mwis_medium_seed14": ["Cape","Dune","Mill","Peak","Reef","Vale"]`
- Gemini subtask_body at `gemini-flash-latest.json:375`

## portfolio_medium_seed5 (cjs + steiner + tsp)

| Model | TSP submission | Failure |
|---|---|---|
| claude-sonnet-4.6 | `{"tour": [0,1,2,…,19,0]}` (21 items, closed with 0) | `tour must contain exactly 20 cities` |
| gemini-flash-latest | same shape as Sonnet | `tour must contain exactly 20 cities` |
| gpt-5.4-mini | not a list | `submission must provide tour as a list of city indices` |

Source: `results/full/portfolio_medium_seed5/concerns.md:9-11` and `claude-sonnet-4.6.json:906-930`.

## portfolio_hard_seed25 (cjs + steiner + tsp) — the 1-of-36 success

| Model | TSP submission | Result |
|---|---|---|
| claude-sonnet-4.6 | `{"tour": [0,1,2,…,19]}` (20 items, no closing 0) | **feasible=True** (coincidence — picked right length) |
| gpt-5.4-mini | CJS feasible, Steiner feasible, TSP string keys | **overall False** |
| gemini-flash-latest | TSP tour = `["Bay","Port","Grove","Pine","Cove"]` (5 Steiner-terminal names); `steiner_hard_seed25: null` | **False** |

Source: `results/full/portfolio_hard_seed25/claude-sonnet-4.6.json:488-510`, `gemini-flash-latest.json:566-574`.

Sonnet's single success on seed25 is a lucky guess at N=20 with no closing-0 convention. The same model produced `[0..19,0]` on seed5 — proving schema compliance is random, not learned.

## What it is NOT

- NOT a parse bug: Sonnet seed14 is `parse_path=strict_protocol_cf` — BEST_GUESS parsed cleanly as JSON. The schema mismatch is downstream of parsing.
- NOT a model-capability bug: all three models produce correct baseline-echo CJS and Steiner submissions in the same prompt. The failure is isolated to sub-components whose baseline is not seeded into CURRENT_BEST.
- NOT instance-difficulty: seed25 hard succeeded for Sonnet; seed14 medium failed. Pattern tracks sub-component key mismatch, not intrinsic difficulty.

evidence [[portfolio-infeasibility-root]]
