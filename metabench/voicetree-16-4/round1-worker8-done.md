---
color: green
isContextNode: false
agent_name: Omar
---
# Round 1 Worker 8 Done

Completed Worker 8 end to end: generated 12 portfolio medium+hard high-seed rows, ran the 4 designated fallback rows across 3 models, and confirmed that all 12 evaluated portfolios remained infeasible. Gemini was materially slower/noisier than Sonnet and GPT, including one timeout retry and one `partial_rescue` parse on a hard row.

# Worker 8 End-to-End Outcome

## Generation

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

Runner ids used for evaluation:

- `portfolio_medium_seed16`
- `portfolio_medium_seed20`
- `portfolio_hard_seed16`
- `portfolio_hard_seed20`

Generation notes:

- Deterministic 3-of-6 class sampling by numeric seed.
- Whole-row fallback used `requested_seed..requested_seed+4` with duplicate actual-seed avoidance inside each difficulty.
- Two hard MWIS-backed rows required the existing hard->medium `n_nodes=120` fallback to avoid skips.
- Net result: full 12-row worker scratch set with no skipped cells.

## Runner Summary

| model | parsed outputs | feasible | avg wall_s | notes |
|---|---:|---:|---:|---|
| `gemini-flash-latest` | 4/4 | 0/4 | 319.1 | `strict_protocol_cf`=3, `partial_rescue`=1 |
| `claude-sonnet-4.6` | 4/4 | 0/4 | 43.0 | `strict_protocol_cf`=4 |
| `gpt-5.4-mini` | 4/4 | 0/4 | 9.5 | `strict_protocol_cf`=4 |

Per-row headlines:

- `portfolio_medium_seed16`: Gemini `strict_protocol_cf` score=-11.03 feasible=False; Sonnet `strict_protocol_cf` score=-2.43 feasible=False; GPT `strict_protocol_cf` score=-0.51 feasible=False.
- `portfolio_medium_seed20`: Gemini `strict_protocol_cf` score=-19.33 feasible=False; Sonnet `strict_protocol_cf` score=20.80 feasible=False; GPT `strict_protocol_cf` score=-0.46 feasible=False.
- `portfolio_hard_seed16`: Gemini `partial_rescue` score=-8.71 feasible=False stop=`error`; Sonnet `strict_protocol_cf` score=-2.89 feasible=False; GPT `strict_protocol_cf` score=-0.43 feasible=False.
- `portfolio_hard_seed20`: Gemini `strict_protocol_cf` score=-24.75 feasible=False; Sonnet `strict_protocol_cf` score=15.58 feasible=False; GPT `strict_protocol_cf` score=16.89 feasible=False.

## Interpretation

- All 12 evaluated model-row runs produced infeasible final portfolios.
- Positive Sonnet/GPT scores on `portfolio_medium_seed20` and `portfolio_hard_seed20` were not end-to-end solves; they came from partial value capture while sibling portfolio components still violated answer contracts.
- Gemini was the weakest operational path on these rows: far slower, one timeout retry, and one hard-row `partial_rescue` parse ending in `stop=error`.
- The right readout is not parse failure in general; it is persistent portfolio-level invalidity even when the outer JSON/protocol shape is mostly acceptable.

## Deliverables

- Scratch generation set in `kaggle_submission/scratch/round1/worker8/`
- Four evaluated result directories in `kaggle_submission/results/full/portfolio_{medium,hard}_seed{16,20}/`
- Supporting graph nodes: `round1-worker8-generation.md`, `round1-worker8-runner-done.md`


## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round1/worker8/questions.partial.jsonl
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round1/worker8/gen-notes.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round1/worker8/child-question-ids.txt
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round1/worker8/run_partial_eval.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round1/worker8/runner-log.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed16/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed16/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed16/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed16/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed16/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed20/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed20/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed20/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed20/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed20/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed16/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed16/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed16/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed16/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed16/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed20/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed20/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed20/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed20/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed20/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/round1-worker8-done.md

### NOTES

- All four designated runner ids completed and wrote full result directories with `question.json`, three per-model JSON payloads, and `concerns.md`.
- The worker-local wrapper was the correct containment boundary because this task had to read `scratch/round1/worker8/questions.partial.jsonl` instead of the shared `questions.jsonl`.
- The important interpretive trap is treating positive scores as success. That is wrong for this worker: every final portfolio remained infeasible.

## Related

- [round1-worker8-generation](round1-worker8-generation.md)
- [round1-worker8-runner-done](round1-worker8-runner-done.md)

[[task_1776359686816yeg]]
