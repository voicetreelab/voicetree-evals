---
color: green
isContextNode: false
agent_name: Omar
---
# Round 1 Worker 8 Generation — 12 High-Seed Portfolio Rows

Generated Worker 8’s full 12-row scratch set for portfolio medium+hard high seeds. Actual row ids shifted via seed fallback, and two hard MWIS-backed rows required the existing hard->medium `n_nodes=120` fallback to avoid skips.

## Actual rows

| id | difficulty | components |
|---|---|---|
| `portfolio_medium_seed16` | `medium` | `graphcol_medium_seed16`, `tsp_medium_seed16`, `mwis_medium_seed16` |
| `portfolio_medium_seed18` | `medium` | `steiner_medium_seed18`, `cjs_medium_seed18`, `tsp_medium_seed18` |
| `portfolio_medium_seed19` | `medium` | `ve_medium_seed19`, `cjs_medium_seed19`, `mwis_medium_seed19` |
| `portfolio_medium_seed20` | `medium` | `ve_medium_seed20`, `steiner_medium_seed20`, `graphcol_medium_seed20` |
| `portfolio_medium_seed22` | `medium` | `steiner_medium_seed22`, `ve_medium_seed22`, `cjs_medium_seed22` |
| `portfolio_medium_seed23` | `medium` | `graphcol_medium_seed23`, `cjs_medium_seed23`, `mwis_medium_seed23` |
| `portfolio_hard_seed16` | `hard` | `graphcol_hard_seed16`, `tsp_hard_seed16`, `mwis_hard_seed16` |
| `portfolio_hard_seed18` | `hard` | `steiner_hard_seed18`, `cjs_hard_seed18`, `tsp_hard_seed18` |
| `portfolio_hard_seed19` | `hard` | `ve_hard_seed19`, `cjs_hard_seed19`, `mwis_hard_seed19` |
| `portfolio_hard_seed20` | `hard` | `ve_hard_seed20`, `steiner_hard_seed20`, `graphcol_hard_seed20` |
| `portfolio_hard_seed22` | `hard` | `steiner_hard_seed22`, `ve_hard_seed22`, `cjs_hard_seed22` |
| `portfolio_hard_seed23` | `hard` | `graphcol_hard_seed23`, `cjs_hard_seed23`, `mwis_hard_seed23` |

## Runner ids

`portfolio_medium_seed16`, `portfolio_medium_seed20`, `portfolio_hard_seed16`, `portfolio_hard_seed20`

## Generation model

- Deterministic 3-of-6 class sampling by numeric seed.
- All three portfolio components use the portfolio row’s difficulty and actual seed.
- Whole-row seed fallback used `requested_seed..requested_seed+4` with duplicate actual-seed avoidance inside each difficulty band.
- Hard MWIS components additionally used the existing hard-row size fallback pattern (`n_nodes=120`) when default hard generation failed.

## Learnings

- Tried pure seed fallback first, switched to seed fallback plus hard MWIS size fallback because two hard requested slots were still skipping on repeated bridge-check failures.
- The main pitfall is assuming portfolio workers can depend on other workers’ solo rows; they cannot. The rows have to be self-contained via embedded `components[].sub_instance` payloads.
- The stable mental model is: portfolio rows are schema-only wrappers over freshly generated solo sub-instances, so the correctness boundary is row-local and reproducible from the seed/fallback notes.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round1/worker8/questions.partial.jsonl
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round1/worker8/gen-notes.md

### NOTES

- Medium high seeds repeatedly hit MWIS bridge-check failures on seeds 14, 15, 17, and 21 but still yielded 6 rows after whole-row fallback.
- Hard high seeds only reached the full 6 rows after enabling the same `n_nodes=120` MWIS fallback pattern already used elsewhere for hard-row salvage.
- The evaluator child should use the fallback runner ids above, not the original requested ids from the task brief.

## Related

- [round1-partition](round1-partition.md)
- [task_1776359686816yeg](task_1776359686816yeg.md)

[[task_1776359686816yeg]]
