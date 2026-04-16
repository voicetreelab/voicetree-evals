---
color: green
isContextNode: false
agent_name: Sam
---
# Round 1 Worker 8 Runner Done

Ran Worker 8's 4 fallback portfolio rows (`portfolio_{medium,hard}_seed{16,20}`) across `gemini-flash-latest`, `claude-sonnet-4.6`, and `gpt-5.4-mini` using a worker-local wrapper against `scratch/round1/worker8/questions.partial.jsonl`. All 12 runs wrote `question.json`, per-model JSON, and `concerns.md`; every final portfolio remained infeasible, with Gemini showing one timeout-retry and one `partial_rescue` parse on `portfolio_hard_seed16`.

- Question source: `/Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round1/worker8/questions.partial.jsonl`
- Questions: `portfolio_medium_seed16`, `portfolio_medium_seed20`, `portfolio_hard_seed16`, `portfolio_hard_seed20`
- Models: `gemini-flash-latest`, `claude-sonnet-4.6`, `gpt-5.4-mini`
- Artifacts: `/Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full`

## Parse Rates

| model | parsed outputs | feasible | avg wall_s | notes |
|---|---:|---:|---:|---|
| `gemini-flash-latest` | 4/4 | 0/4 | 319.1 | `strict_protocol_cf`=3, `partial_rescue`=1 |
| `claude-sonnet-4.6` | 4/4 | 0/4 | 43.0 | `strict_protocol_cf`=4 |
| `gpt-5.4-mini` | 4/4 | 0/4 | 9.5 | `strict_protocol_cf`=4 |

## Question Headlines

- `portfolio_medium_seed16`: Gemini `strict_protocol_cf` score=-11.03 feasible=False; Sonnet `strict_protocol_cf` score=-2.43 feasible=False; GPT `strict_protocol_cf` score=-0.51 feasible=False.
- `portfolio_medium_seed20`: Gemini `strict_protocol_cf` score=-19.33 feasible=False; Sonnet `strict_protocol_cf` score=20.80 feasible=False; GPT `strict_protocol_cf` score=-0.46 feasible=False.
- `portfolio_hard_seed16`: Gemini `partial_rescue` score=-8.71 feasible=False stop=`error`; Sonnet `strict_protocol_cf` score=-2.89 feasible=False; GPT `strict_protocol_cf` score=-0.43 feasible=False.
- `portfolio_hard_seed20`: Gemini `strict_protocol_cf` score=-24.75 feasible=False; Sonnet `strict_protocol_cf` score=15.58 feasible=False; GPT `strict_protocol_cf` score=16.89 feasible=False.

## Headline Findings

- All 12 final portfolio submissions were infeasible even when the protocol parse succeeded.
- Gemini was by far the slowest path and the noisiest one: one hard-row timeout retry, one `partial_rescue`, and consistently negative net scores from time cost plus zero recovered value.
- Sonnet and GPT were much faster and sometimes positive on score, but those positives still came from partially successful portfolios rather than valid end-to-end solves.
- In the positive-score samples, `steiner` was feasible while sibling `ve` or `graphcol` components failed schema/answer-contract checks, so the overall portfolio stayed invalid.

## Learnings

1. Tried the existing `eval_harness.run_local` CLI first, then switched to a worker-local wrapper because this task had to read `scratch/round1/worker8/questions.partial.jsonl` rather than the shared dataset.
2. A follow-up agent could easily misread positive Sonnet/GPT scores as success; do not do that, because every final portfolio here was still infeasible.
3. The reliable mental model is: protocol compliance is mostly okay on these portfolio rows, but portfolio answer-schema validity is not. The current prompts/models can emit structured portfolio JSON while still violating component-specific contracts (`ve` object shape, `graphcol` assignment mapping, MWIS/TSP field names), and Gemini hard rows additionally strain timeout/parse robustness.

## Files Changed

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

### NOTES

- The worker-local wrapper was necessary because the shared `eval_harness.run_local` flow must not read the global `questions.jsonl` for this task.
- Gemini required one timeout retry on `portfolio_hard_seed16` and still only recovered a `partial_rescue` parse ending in `stop=error`.
- Positive Sonnet/GPT scores on some rows did not indicate full portfolio success; they came from one feasible component, typically `steiner`, while other components remained invalid.

## Related

- [round1-worker8-generation](round1-worker8-generation.md)

[[task_17763600821684bs]]
