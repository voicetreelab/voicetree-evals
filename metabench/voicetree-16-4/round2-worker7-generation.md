---
color: green
isContextNode: false
agent_name: Yan
---
# Round 2 Worker 7 Generation — Portfolio Mixed Rows

Generated all 12 assigned round-2 portfolio rows for worker 7 in scratch space and resolved the concrete runner ids after whole-row seed fallback. The original template ids drifted to medium `33/36` and hard `30/34`, so `runner_ids.txt` is now the source of truth for stage 2.

## Actual rows
| id | difficulty | components |
|---|---|---|
| `portfolio_medium_seed33` | `medium` | `mwis_medium_seed33`, `steiner_medium_seed33`, `ve_medium_seed33` |
| `portfolio_medium_seed34` | `medium` | `mwis_medium_seed34`, `graphcol_medium_seed34`, `cjs_medium_seed34` |
| `portfolio_medium_seed35` | `medium` | `mwis_medium_seed35`, `graphcol_medium_seed35`, `steiner_medium_seed35` |
| `portfolio_medium_seed36` | `medium` | `graphcol_medium_seed36`, `cjs_medium_seed36`, `mwis_medium_seed36` |
| `portfolio_medium_seed37` | `medium` | `ve_medium_seed37`, `mwis_medium_seed37`, `cjs_medium_seed37` |
| `portfolio_medium_seed38` | `medium` | `ve_medium_seed38`, `tsp_medium_seed38`, `mwis_medium_seed38` |
| `portfolio_hard_seed30` | `hard` | `mwis_hard_seed30`, `graphcol_hard_seed30`, `cjs_hard_seed30` |
| `portfolio_hard_seed31` | `hard` | `cjs_hard_seed31`, `tsp_hard_seed31`, `ve_hard_seed31` |
| `portfolio_hard_seed33` | `hard` | `mwis_hard_seed33`, `steiner_hard_seed33`, `ve_hard_seed33` |
| `portfolio_hard_seed34` | `hard` | `mwis_hard_seed34`, `graphcol_hard_seed34`, `cjs_hard_seed34` |
| `portfolio_hard_seed35` | `hard` | `mwis_hard_seed35`, `graphcol_hard_seed35`, `steiner_hard_seed35` |
| `portfolio_hard_seed36` | `hard` | `graphcol_hard_seed36`, `cjs_hard_seed36`, `mwis_hard_seed36` |

## Runner ids
- `portfolio_medium_seed33`
- `portfolio_medium_seed36`
- `portfolio_hard_seed30`
- `portfolio_hard_seed34`

## Generation model
- Deterministic `random.Random(actual_seed).sample(['cjs','steiner','graphcol','tsp','mwis','ve'], 3)` class selection.
- Whole-row seed fallback over `requested_seed..requested_seed+4` with duplicate-actual-seed avoidance per portfolio difficulty.
- Hard MWIS-backed components reuse the existing `n_nodes=120` size fallback at a fixed actual seed.

## Learnings
1. Tried to treat the task-node anchor ids as authoritative, switched to generated `runner_ids.txt` because portfolio whole-row fallback shifted the actual ids immediately.
2. The easy mistake is using `_build_hard_row_with_fallback(...)` for portfolio components. That is wrong here because it can change per-component seeds; the portfolio rows need all three components on the row's actual seed.
3. The stable mental model is row-local generation: each portfolio row is a self-contained wrapper over three freshly built solo sub-instances, and duplicate avoidance only needs to track existing/generated portfolio actual seeds per difficulty.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker7/generate_rows.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker7/run_partial_eval.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker7/questions.partial.jsonl
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker7/runner_ids.txt
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker7/gen-notes.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker7/generation-manifest.json

### NOTES

- No skips were required; all 12 requested row slots produced concrete portfolio ids after whole-row fallback.
- Medium requested seeds `32..37` shifted upward because seed `32` hit an MWIS pre-flight failure and subsequent requests had to avoid already-consumed actual seeds.
- Stage 2 runner was spawned against the concrete ids above rather than the stale template ids from the original worker brief.

[[task_1776364403624wbv]]
