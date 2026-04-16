---
color: green
isContextNode: false
agent_name: Mary
---
# Round 1 Worker 1 Runner — 12 Eval Artifacts

Completed the 4 selected question IDs across 3 models and wrote per-question `question.json`, 3 model JSONs, and `concerns.md` under `results/full/`. The runner summary shows Gemini strongest on CJS, Sonnet brittle on CJS parsing but perfect on Steiner, and GPT-5.4-mini consistently feasible but low-value on CJS.

## Model totals
| Model | Strict-like | Strict parse failed | Baseline only | Feasible |
| --- | ---: | ---: | ---: | ---: |
| `gemini-flash-latest` | 3/4 | 0/4 | 1/4 | 4/4 |
| `claude-sonnet-4.6` | 2/4 | 2/4 | 0/4 | 2/4 |
| `gpt-5.4-mini` | 4/4 | 0/4 | 0/4 | 4/4 |

## Per-question outcomes
| Question | Gemini | Claude | GPT |
| --- | --- | --- | --- |
| `cjs_medium_seed2` | `strict_protocol_cf`, gap `11.1`, score `84.79` | `strict_protocol_cf`, infeasible, score `0.00` | `strict_protocol_cf`, gap `113.3`, score `-0.16` |
| `cjs_medium_seed5` | `strict_protocol_cf`, gap `34.2`, score `60.51` | `strict_parse_failed`, infeasible, score `-4.91` | `strict_protocol_cf`, gap `115.8`, score `-0.19` |
| `cjs_medium_seed8` | `strict_protocol_cf`, gap `61.0`, score `34.82` | `strict_parse_failed`, feasible, gap `103.9`, score `-4.25` | `strict_protocol_cf`, gap `103.9`, score `-0.16` |
| `steiner_medium_seed2` | `baseline_only`, feasible, gap `18.3`, score `80.06` | `strict_protocol_cf`, gap `0.0`, score `99.24` | `strict_protocol_cf`, gap `18.3`, score `81.58` |

## Operational notes
- The first spawned child runner never reached model execution, so the parent completed the runner stage locally.
- The local helper was patched to resume from existing per-model JSON files and to avoid replaying whole rows after harness wall-budget stops.
- `concerns.md` was written for each question directory with parse, feasibility, score-vs-baseline, and transcript-coherence buckets.


## Files Changed

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
- Claude Sonnet 4.6's failures are concentrated on the CJS rows and show up as `exec turn 2 parse failed`, not transport-level API errors.
- Gemini's only parser miss in this slice was a Steiner plan-turn parse failure; the saved artifact is still feasible because the harness fell back to the baseline submission.

evaluated by [[round1-worker1-done]]
