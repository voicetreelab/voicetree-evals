---
color: green
isContextNode: false
agent_name: Meg
---
# Round 1 Worker 3 Runner — 4 IDs × 3 Models

Ran the worker3 eval slice against the worker-local partial dataset and wrote full per-question artifacts under `results/full/`. Gemini was slow but strongest, Sonnet recovered from two timeout retries but failed feasibility on `tsp_medium_seed8`, and GPT was very fast but materially weaker on graph coloring.

## Per-model summary
| model | strict-protocol parses | feasible | avg score | avg wall_s | notable issue |
| --- | ---: | ---: | ---: | ---: | --- |
| `gemini-flash-latest` | 4/4 | 4/4 | 94.42 | 537.8 | Very slow; `tsp_medium_seed5` took `695.6s` |
| `claude-sonnet-4.6` | 4/4 | 3/4 | 71.78 | 169.0 | `tsp_medium_seed8` infeasible, score `0.00` |
| `gpt-5.4-mini` | 4/4 | 4/4 | 58.05 | 14.6 | `graphcol_medium_seed8` feasible but score `-0.20` |

## Row-by-row outcomes
| id | gemini | sonnet | gpt |
| --- | --- | --- | --- |
| `graphcol_medium_seed8` | feasible, `96.29`, `370.5s` | feasible, `97.99`, `201.1s` after timeout retry | feasible, `-0.20`, `19.7s` |
| `tsp_medium_seed2` | feasible, `94.09`, `510.7s` | feasible, `96.23`, `310.8s` after timeout retry | feasible, `64.74`, `11.1s` |
| `tsp_medium_seed5` | feasible, `93.04`, `695.6s` | feasible, `92.92`, `69.4s` | feasible, `82.03`, `11.8s` |
| `tsp_medium_seed8` | feasible, `94.26`, `574.3s` | infeasible, `0.00`, `94.9s` | feasible, `85.61`, `15.9s` |

## Headline findings
- Gemini delivered the strongest and most consistent scores, but at a very high latency cost.
- Sonnet's parser held up after the earlier harness fixes, but answer quality is still brittle on at least one TSP row.
- GPT stayed extremely fast and always feasible on this slice, but its graph-coloring quality was far behind Gemini and Sonnet.


## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round1/worker3/run_partial_eval.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round1/worker3/runner-log.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_medium_seed8/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_medium_seed8/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_medium_seed8/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_medium_seed8/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_medium_seed8/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_medium_seed2/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_medium_seed2/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_medium_seed2/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_medium_seed2/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_medium_seed2/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_medium_seed5/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_medium_seed5/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_medium_seed5/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_medium_seed5/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_medium_seed5/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_medium_seed8/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_medium_seed8/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_medium_seed8/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_medium_seed8/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_medium_seed8/concerns.md

### NOTES

- Sonnet needed one timeout retry on `graphcol_medium_seed8` and one timeout retry on `tsp_medium_seed2`, but both reruns completed successfully.
- All 12 payloads ended with `parse_path=strict_protocol_cf`; there were no final parse failures in this slice.
- `tsp_medium_seed8` is the only row with a clear model-specific failure: Sonnet stopped with an infeasible answer and score `0.00` while Gemini and GPT remained feasible.

[[task_1776359643077snj]]
