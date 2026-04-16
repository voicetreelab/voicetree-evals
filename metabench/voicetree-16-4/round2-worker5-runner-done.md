---
color: green
isContextNode: false
agent_name: Wei
---
# Round 2 Worker 5 Runner — 4 Portfolio Medium IDs × 3 Models

Completed the worker5 runner locally after reclaiming the stalled child lane. All 12 planned model runs completed against the worker-local partial file, every final portfolio remained infeasible, and no wrapper retries or timeouts were needed.

## Probe IDs

- `portfolio_medium_seed14`
- `portfolio_medium_seed21`
- `portfolio_medium_seed26`
- `portfolio_medium_seed29`

## Model Summary

| model | parse profile | feasible | avg wall_s | avg score |
|---|---|---:|---:|---:|
| `gemini-flash-latest` | `strict_protocol_cf` 3/4, `partial_rescue` 1/4 | 0/4 | 381.6 | -19.08 |
| `claude-sonnet-4.6` | `strict_protocol_cf` 4/4 | 0/4 | 44.9 | 12.42 |
| `gpt-5.4-mini` | `strict_protocol_cf` 4/4 | 0/4 | 14.0 | 7.47 |

## Per-row Headlines

- `portfolio_medium_seed14`: Gemini `partial_rescue` score `-11.03`; Sonnet `11.72`; GPT `13.25`; all infeasible.
- `portfolio_medium_seed21`: Gemini `strict_protocol_cf` score `-27.70`; Sonnet `14.86`; GPT `15.99`; all infeasible.
- `portfolio_medium_seed26`: Gemini `strict_protocol_cf` score `-10.81`; Sonnet `23.73`; GPT `-0.45`; all infeasible.
- `portfolio_medium_seed29`: Gemini `strict_protocol_cf` score `-26.78`; Sonnet `-0.65`; GPT `1.09`; all infeasible.

## Interpretation

- This reproduces the round-1 portfolio pattern: parsing is mostly fine, but end-to-end portfolio validity still fails on every run.
- Gemini remained the slowest path by a large margin, especially on seeds `21` and `29`, but still stayed within the worker-local 600s attempt budget.
- The useful failure signal is portfolio invalidity, not harness instability. The runner wrapper completed all 12 executions without retries, crashes, or budget aborts.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker5/run_partial_eval.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker5/runner-log.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed14/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed14/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed14/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed14/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed14/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed21/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed21/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed21/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed21/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed21/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed26/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed26/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed26/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed26/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed26/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed29/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed29/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed29/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed29/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/portfolio_medium_seed29/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/round2-worker5-runner-done.md

### NOTES

- The Ari child created only a stand-down receipt and never touched worker5 runner artifacts.
- The worker-local runner uses subprocess-scoped execution so the 600s per-attempt budget is real rather than inherited from the shared 1800s harness total.
- `portfolio_medium_seed14` was the only probe row that required `partial_rescue`; every other payload parsed through `strict_protocol_cf`.

[[task_1776364403193gei]]
