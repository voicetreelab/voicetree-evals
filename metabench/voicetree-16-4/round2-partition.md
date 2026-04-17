---
color: blue
isContextNode: false
agent_name: Noam
---
# Round 2 Partition — 8 Workers × 4 Cells × 3 Seeds = 96 Rows

Noam's Round 2 partition after Tao's PROCEED (round1-review.md). Focus: finish solo-hard coverage (4 workers), extend portfolio volume (4 workers). Target total after R2: ~216 rows (within 210 overshoot tolerance).

## Current coverage (120 rows post-R1)

Solo medium: ALL 10 seeds for cjs, steiner, graphcol, tsp, mwis, ve (mwis has gaps at 2/6/11, but total=10).
Solo hard: cjs/steiner=seeds 1-6, graphcol/tsp/ve=seeds 1-3, mwis=seeds 1,2,4.
Portfolio medium: 19 seeds scattered. Portfolio hard: 17 seeds scattered.

## Round 2 assignment

| W | Cells (class, diff, seed_range) | Rows | Child runner seed=1-of-cell IDs |
|---|---|---:|---|
| 1 | (cjs, hard, 7-9), (cjs, hard, 10-12), (steiner, hard, 7-9), (steiner, hard, 10-12) | 12 | cjs_hard_seed7, cjs_hard_seed10, steiner_hard_seed7, steiner_hard_seed10 |
| 2 | (graphcol, hard, 4-6), (graphcol, hard, 7-9), (graphcol, hard, 10-12), (tsp, hard, 4-6) | 12 | graphcol_hard_seed4, graphcol_hard_seed7, graphcol_hard_seed10, tsp_hard_seed4 |
| 3 | (tsp, hard, 7-9), (tsp, hard, 10-12), (ve, hard, 4-6), (ve, hard, 7-9) | 12 | tsp_hard_seed7, tsp_hard_seed10, ve_hard_seed4, ve_hard_seed7 |
| 4 | (ve, hard, 10-12), (mwis, hard, 5-7), (mwis, hard, 8-10), (mwis, hard, 11-13) | 12 | ve_hard_seed10, mwis_hard_seed5, mwis_hard_seed8, mwis_hard_seed11 |
| 5 | (portfolio, medium, gap-fill 14/15/17), (portfolio, medium, 21/24/25), (portfolio, medium, 26-28), (portfolio, medium, 29-31) | 12 | portfolio_medium_seed14, portfolio_medium_seed21, portfolio_medium_seed26, portfolio_medium_seed29 |
| 6 | (portfolio, hard, gap-fill 6/11/14), (portfolio, hard, 15/17/21), (portfolio, hard, 24-26), (portfolio, hard, 27-29) | 12 | portfolio_hard_seed6, portfolio_hard_seed15, portfolio_hard_seed24, portfolio_hard_seed27 |
| 7 | (portfolio, medium, 32-34), (portfolio, medium, 35-37), (portfolio, hard, 30-32), (portfolio, hard, 33-35) | 12 | portfolio_medium_seed32, portfolio_medium_seed35, portfolio_hard_seed30, portfolio_hard_seed33 |
| 8 | (portfolio, medium, 38-40), (portfolio, medium, 41-43), (portfolio, hard, 36-38), (portfolio, hard, 39-41) | 12 | portfolio_medium_seed38, portfolio_medium_seed41, portfolio_hard_seed36, portfolio_hard_seed39 |

## Learnings applied from Round 1

1. **W5 budget guardrail killed Gemini+Sonnet on hard rows.** Round 2 workers: DO NOT pre-emptively kill slower models. Allow 600s per model per row. Only skip a (row, model) if 2 retries fail.
2. **Portfolio infeasibility 0/36 in R1.** Sonnet reviewer classified as model-quality failure, not harness bug. Collect more data in R2; don't tune harness.
3. **MWIS hard seed 3 bridge-fail is deterministic.** W4 skips mwis_hard_seed3, uses seed fallback to +4 equivalents.
4. **Mary/Rex late divergence**: when a child runner produces improved artifacts post-parent commit, accept them (strictly better = commit the diff).

## Known gotchas
- mwis hard seed 3 bridge-check always fails — workers using mwis hard seeds should seed-fallback past any seeds that repeat this.
- Lou is running Kaggle production in parallel (writes to `kaggle_submission/kaggle/output/`) — DO NOT touch that path.
- Jun's rescue parser is active — `parse_path: partial_rescue` is a valid result.

## Scratch dir
`kaggle_submission/scratch/round2/worker[W]/`
