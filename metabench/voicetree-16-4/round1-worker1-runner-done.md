---
color: green
isContextNode: false
agent_name: Rex
---
# Round 1 Worker 1 Runner — 12 Eval Artifacts

Completed the assigned 4 question IDs across 3 models and wrote `question.json`, model JSONs, and `concerns.md` under `kaggle_submission/results/full/`. The scratch runner had to be patched and resumed after an incomplete first pass; final numbers below are recomputed from the saved per-question JSON artifacts.

## Model totals
| Model | Strict-like | Strict parse failed | Baseline only | Feasible |
| --- | ---: | ---: | ---: | ---: |
| `gemini-flash-latest` | 4/4 | 0/4 | 0/4 | 4/4 |
| `claude-sonnet-4.6` | 2/4 | 1/4 | 1/4 | 2/4 |
| `gpt-5.4-mini` | 4/4 | 0/4 | 0/4 | 4/4 |

## Per-question outcomes
| Question | Gemini | Claude | GPT |
| --- | --- | --- | --- |
| `cjs_medium_seed2` | `strict_protocol_cf`, feasible, gap `11.1`, score `84.79` | `strict_protocol_cf`, infeasible, gap `100.0`, score `0.00` | `strict_protocol_cf`, feasible, gap `113.3`, score `-0.16` |
| `cjs_medium_seed5` | `strict_protocol_cf`, feasible, gap `34.2`, score `60.51` | `strict_parse_failed`, infeasible, gap `100.0`, score `-4.91` | `strict_protocol_cf`, feasible, gap `115.8`, score `-0.19` |
| `cjs_medium_seed8` | `strict_protocol_cf`, feasible, gap `3.9`, score `90.12` | `baseline_only`, feasible, gap `103.9`, score `-4.23` | `strict_protocol_cf`, feasible, gap `103.9`, score `-0.16` |
| `steiner_medium_seed2` | `strict_protocol_cf`, feasible, gap `0.0`, score `96.19` | `strict_protocol_cf`, feasible, gap `0.0`, score `99.24` | `strict_protocol_cf`, feasible, gap `18.3`, score `81.58` |

## Operational notes
- Gemini was slow but strongest on the three CJS rows and also solved the Steiner row to gold.
- Claude was the unstable model in this slice: one infeasible stop, one strict parse failure, and one wall-budget timeout that fell back to the baseline.
- GPT parsed all four rows cleanly and stayed feasible, but its CJS solutions were consistently baseline-or-worse on score.
- `runner-summary.json` was regenerated from the saved result artifacts after the resumed run because the intermediate summary had stale values.

## Files Changed

- kaggle_submission/scratch/round1/worker1/run_worker1_evals.py
- kaggle_submission/scratch/round1/worker1/runner-summary.json
- kaggle_submission/results/full/cjs_medium_seed2/question.json
- kaggle_submission/results/full/cjs_medium_seed2/gemini-flash-latest.json
- kaggle_submission/results/full/cjs_medium_seed2/claude-sonnet-4.6.json
- kaggle_submission/results/full/cjs_medium_seed2/gpt-5.4-mini.json
- kaggle_submission/results/full/cjs_medium_seed2/concerns.md
- kaggle_submission/results/full/cjs_medium_seed5/question.json
- kaggle_submission/results/full/cjs_medium_seed5/gemini-flash-latest.json
- kaggle_submission/results/full/cjs_medium_seed5/claude-sonnet-4.6.json
- kaggle_submission/results/full/cjs_medium_seed5/gpt-5.4-mini.json
- kaggle_submission/results/full/cjs_medium_seed5/concerns.md
- kaggle_submission/results/full/cjs_medium_seed8/question.json
- kaggle_submission/results/full/cjs_medium_seed8/gemini-flash-latest.json
- kaggle_submission/results/full/cjs_medium_seed8/claude-sonnet-4.6.json
- kaggle_submission/results/full/cjs_medium_seed8/gpt-5.4-mini.json
- kaggle_submission/results/full/cjs_medium_seed8/concerns.md
- kaggle_submission/results/full/steiner_medium_seed2/question.json
- kaggle_submission/results/full/steiner_medium_seed2/gemini-flash-latest.json
- kaggle_submission/results/full/steiner_medium_seed2/claude-sonnet-4.6.json
- kaggle_submission/results/full/steiner_medium_seed2/gpt-5.4-mini.json
- kaggle_submission/results/full/steiner_medium_seed2/concerns.md

### NOTES

- Do not blindly `git add kaggle_submission/results/full/` in this repo state; other workers are concurrently writing sibling directories there.
- The repaired scratch runner resumes from existing per-model JSONs, so reruns of this worker should not recompute rows that already have saved artifacts.
- For this worker slice, the authoritative artifacts are the per-question JSON files and `concerns.md`; `runner-summary.json` is derived from them.
