---
color: blue
isContextNode: false
agent_name: Noam
---
# Round 1 Partition — 8 Workers × 4 Cells × 3 Seeds = 96 Rows

Noam's Round 1 partition for overnight auto-pilot. Deterministic assignment — no overlap. Each cell = (class, difficulty, 3 consecutive seeds). Workers generate rows to `kaggle_submission/scratch/round1/worker[W]/questions.partial.jsonl` (never touch global questions.jsonl — Sonnet reviewer merges after round).

## Existing dataset (26 rows after Leo)
- All 6 solo classes: medium seed 1 ✓
- All 6 solo classes: hard seeds 1,2,3 ✓ (mwis hard uses seed 4 in place of 3)
- portfolio: medium seed 1 ✓, hard seed 2 ✓

## Round 1 assignment (solo workers 1-5, portfolio workers 6-8)

| W | Cells (class, diff, seed_range) | Rows | Child runner: seed=1-of-each-cell (4 rows × 3 models = 12 runs) |
|---|---|---:|---|
| 1 | (cjs, medium, 2-4), (cjs, medium, 5-7), (cjs, medium, 8-10), (steiner, medium, 2-4) | 12 | cjs_medium_seed2, cjs_medium_seed5, cjs_medium_seed8, steiner_medium_seed2 |
| 2 | (steiner, medium, 5-7), (steiner, medium, 8-10), (graphcol, medium, 2-4), (graphcol, medium, 5-7) | 12 | steiner_medium_seed5, steiner_medium_seed8, graphcol_medium_seed2, graphcol_medium_seed5 |
| 3 | (graphcol, medium, 8-10), (tsp, medium, 2-4), (tsp, medium, 5-7), (tsp, medium, 8-10) | 12 | graphcol_medium_seed8, tsp_medium_seed2, tsp_medium_seed5, tsp_medium_seed8 |
| 4 | (mwis, medium, 2-4), (mwis, medium, 5-7), (mwis, medium, 8-10), (ve, medium, 2-4) | 12 | mwis_medium_seed2, mwis_medium_seed5, mwis_medium_seed8, ve_medium_seed2 |
| 5 | (ve, medium, 5-7), (ve, medium, 8-10), (cjs, hard, 4-6), (steiner, hard, 4-6) | 12 | ve_medium_seed5, ve_medium_seed8, cjs_hard_seed4, steiner_hard_seed4 |
| 6 | (portfolio, medium, 2-4), (portfolio, medium, 5-7), (portfolio, medium, 8-10), (portfolio, medium, 11-13) | 12 | portfolio_medium_seed2, portfolio_medium_seed5, portfolio_medium_seed8, portfolio_medium_seed11 |
| 7 | (portfolio, hard, chunk{1,3,4}), (portfolio, hard, 5-7), (portfolio, hard, 8-10), (portfolio, hard, 11-13) | 12 | portfolio_hard_seed1, portfolio_hard_seed5, portfolio_hard_seed8, portfolio_hard_seed11 |
| 8 | (portfolio, medium, 14-16), (portfolio, medium, 17-19), (portfolio, hard, 14-16), (portfolio, hard, 17-19) | 12 | portfolio_medium_seed14, portfolio_medium_seed17, portfolio_hard_seed14, portfolio_hard_seed17 |

## Fallback policy (for workers)
- Seed fail: try +1, up to seed+4 (e.g., if seed=3 fails, try 4,5,6,7)
- Generator fail: drop difficulty-config n param (n-20, n-40)
- Still fail: SKIP cell, log in gen-notes.md

## Known gotcha
- `mwis_hard_seed3` fails bridge-check — Leo used seed=4. Worker 7 uses chunk{1,3,4} strategy (seed 2 already exists). Worker 5 skips cell if mwis hard.

## Next steps after Round 1
Sonnet review → merge scratch into questions.jsonl → Round 2 (similar shape, 96 more rows).
