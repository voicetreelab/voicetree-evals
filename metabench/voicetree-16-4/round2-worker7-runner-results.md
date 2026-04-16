---
color: green
isContextNode: false
agent_name: Amit
---
# Round 2 Worker 7 Runner Results

Executed the worker7 round-2 portfolio mixed probe set from `scratch/round2/worker7/runner_ids.txt` across 3 models and wrote complete result bundles for 4 ids. Resolved a stale parent-template id mismatch by following the concrete scratch artifact and confirmed all 12 saved payloads were infeasible.

## Probe IDs
- `portfolio_medium_seed33`
- `portfolio_medium_seed36`
- `portfolio_hard_seed30`
- `portfolio_hard_seed34`

## Model Summary
| model | feasible | avg wall_s | avg score | parse paths |
| --- | --- | ---: | ---: | --- |
| `gemini-flash-latest` | `0/4` | `367.6` | `-17.37` | `strict_protocol_cf: 3`, `partial_rescue: 1` |
| `claude-sonnet-4.6` | `0/4` | `52.1` | `3.16` | `strict_protocol_cf: 4` |
| `gpt-5.4-mini` | `0/4` | `21.3` | `4.70` | `strict_protocol_cf: 4` |

## Per-Question Headlines
- `portfolio_medium_seed33`: Gemini `-17.59`; Claude `15.38`; GPT `16.72`; all infeasible.
- `portfolio_medium_seed36`: Gemini `-26.79`; Claude `2.16`; GPT `4.91`; all infeasible.
- `portfolio_hard_seed30`: Gemini `partial_rescue`, stop=`error`, score `-8.37`; Claude `-2.50`; GPT `-0.87`; all infeasible.
- `portfolio_hard_seed34`: Gemini `-16.72`; Claude `-2.39`; GPT `-1.96`; all infeasible.

## Learnings
1. Tried to trust the parent worker template first, then switched to the concrete child task plus `runner_ids.txt` because the parent template was stale and named a different probe set.
2. A successor could easily misread the positive Claude/GPT scores on the medium rows as success; do not do that, because every saved payload here is still infeasible.
3. The real shape of this slice is: the worker-local runner is correct as-is, the authoritative ids live in scratch artifacts, and portfolio rows can produce parseable counterfactual outputs with non-trivial scores while still failing final feasibility.

## Artifacts
- Every row now has `question.json`, `gemini-flash-latest.json`, `claude-sonnet-4.6.json`, `gpt-5.4-mini.json`, and `concerns.md`.
- Scratch log written to `kaggle_submission/scratch/round2/worker7/runner-log.md`.
- Human-readable run report written to `voicetree-16-4/round2-worker7-runner-done.md`.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker7/runner-log.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed33/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed33/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed33/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed33/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed33/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed36/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed36/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed36/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed36/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed36/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed30/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed30/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed30/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed30/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed30/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed34/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed34/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed34/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed34/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_hard_seed34/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/round2-worker7-runner-done.md

### NOTES

- The parent worker brief's child template listed ids `32,35,30,33`, but the concrete task plus `runner_ids.txt` listed `33,36,30,34`; the scratch artifact was treated as the authoritative source.
- All four result directories contain the expected five-file bundle shape.
- Gemini consumed most of the wall time on this slice and produced the only non-strict parse path (`partial_rescue` on `portfolio_hard_seed30`).

## Related

- [round2-worker7-runner-done](round2-worker7-runner-done.md)

[[task_17763647178163f9]]
