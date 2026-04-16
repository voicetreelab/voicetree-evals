---
color: green
isContextNode: false
agent_name: Zoe
---
# Round 2 Worker 8 Runner — 4 Portfolio Rows × 3 Models

Ran 12 local evals for the 4 assigned worker-8 portfolio IDs. Parse success was Gemini 3/4, Sonnet 4/4, GPT-5.4-mini 4/4; feasibility was 0/12 across the sample, with one Gemini strict-parse failure on `portfolio_hard_seed36`.

## Runner Summary
```json
{
  "models": {
    "claude-sonnet-4.6": {"avg_score": 5.90096221928446, "feasible_runs": 0, "parsed_runs": 4, "runs": 4},
    "gemini-flash-latest": {"avg_score": -25.45229340522783, "feasible_runs": 0, "parsed_runs": 3, "runs": 4},
    "gpt-5.4-mini": {"avg_score": 1.6762782218662329, "feasible_runs": 0, "parsed_runs": 4, "runs": 4}
  },
  "question_ids": [
    "portfolio_medium_seed38",
    "portfolio_medium_seed41",
    "portfolio_hard_seed36",
    "portfolio_hard_seed39"
  ]
}
```

## Per-Run Outcomes
| id | model | parse | feasible | score | stop | wall_s |
|---|---|---|---|---:|---|---:|
| portfolio_medium_seed38 | gemini-flash-latest | partial_rescue | false | -26.25 | decision_stop | 525.1 |
| portfolio_medium_seed38 | claude-sonnet-4.6 | strict_protocol_cf | false | -1.74 | decision_stop | 34.8 |
| portfolio_medium_seed38 | gpt-5.4-mini | strict_protocol_cf | false | -0.47 | decision_stop | 9.4 |
| portfolio_medium_seed41 | gemini-flash-latest | strict_protocol_cf | false | -39.25 | decision_stop | 785.0 |
| portfolio_medium_seed41 | claude-sonnet-4.6 | strict_protocol_cf | false | 19.63 | decision_stop | 46.5 |
| portfolio_medium_seed41 | gpt-5.4-mini | strict_protocol_cf | false | -0.80 | decision_stop | 15.9 |
| portfolio_hard_seed36 | gemini-flash-latest | strict_parse_failed | false | -14.54 | error | 290.8 |
| portfolio_hard_seed36 | claude-sonnet-4.6 | strict_protocol_cf | false | -2.43 | decision_stop | 48.7 |
| portfolio_hard_seed36 | gpt-5.4-mini | strict_protocol_cf | false | -1.13 | decision_stop | 22.6 |
| portfolio_hard_seed39 | gemini-flash-latest | strict_protocol_cf | false | -21.77 | decision_stop | 435.4 |
| portfolio_hard_seed39 | claude-sonnet-4.6 | strict_protocol_cf | false | 8.15 | decision_stop | 35.0 |
| portfolio_hard_seed39 | gpt-5.4-mini | strict_protocol_cf | false | 9.10 | decision_stop | 16.0 |

## Learnings
- Tried to leave the shared harness untouched; a worker-local runner was enough to emit the required `results/full/<id>/` artifacts.
- Do not equate parse success with useful solve behavior here: Sonnet and GPT parsed every run, but all 12 executions still ended infeasible.
- Gemini is the unstable leg on this sample: it was much slower on three rows and produced the only strict parse failure on `portfolio_hard_seed36`.

## Files Changed

- kaggle_submission/scratch/round2/worker8/run_partial_eval.py
- kaggle_submission/scratch/round2/worker8/runner-log.md
- kaggle_submission/scratch/round2/worker8/runner-summary.json
- kaggle_submission/results/full/portfolio_medium_seed38/question.json
- kaggle_submission/results/full/portfolio_medium_seed38/gemini-flash-latest.json
- kaggle_submission/results/full/portfolio_medium_seed38/claude-sonnet-4.6.json
- kaggle_submission/results/full/portfolio_medium_seed38/gpt-5.4-mini.json
- kaggle_submission/results/full/portfolio_medium_seed38/concerns.md
- kaggle_submission/results/full/portfolio_medium_seed41/question.json
- kaggle_submission/results/full/portfolio_medium_seed41/gemini-flash-latest.json
- kaggle_submission/results/full/portfolio_medium_seed41/claude-sonnet-4.6.json
- kaggle_submission/results/full/portfolio_medium_seed41/gpt-5.4-mini.json
- kaggle_submission/results/full/portfolio_medium_seed41/concerns.md
- kaggle_submission/results/full/portfolio_hard_seed36/question.json
- kaggle_submission/results/full/portfolio_hard_seed36/gemini-flash-latest.json
- kaggle_submission/results/full/portfolio_hard_seed36/claude-sonnet-4.6.json
- kaggle_submission/results/full/portfolio_hard_seed36/gpt-5.4-mini.json
- kaggle_submission/results/full/portfolio_hard_seed36/concerns.md
- kaggle_submission/results/full/portfolio_hard_seed39/question.json
- kaggle_submission/results/full/portfolio_hard_seed39/gemini-flash-latest.json
- kaggle_submission/results/full/portfolio_hard_seed39/claude-sonnet-4.6.json
- kaggle_submission/results/full/portfolio_hard_seed39/gpt-5.4-mini.json
- kaggle_submission/results/full/portfolio_hard_seed39/concerns.md

### NOTES

- Broad `git add kaggle_submission/results/full/` would be unsafe here because other round-2 workers are writing nearby; stage only the four owned result directories.
- Every emitted result dir includes `question.json`, three model payloads, and `concerns.md`.

includes eval sample [[round2-worker8-done]]
