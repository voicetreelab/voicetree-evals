---
color: green
isContextNode: false
agent_name: Ama
---
# Round 2 Worker 3 Runner — 4 IDs × 3 Models

Executed the existing Round 2 worker 3 runner against `tsp_hard_seed7`, `tsp_hard_seed10`, `ve_hard_seed4`, and `ve_hard_seed7`. Produced all per-row artifacts plus `runner-log.md` and `runner-summary.json`; no timeouts, with only Sonnet failing the two VE-hard rows.

## Feasibility Headline
10 of 12 row-model evaluations finished feasible. No timeouts were recorded. `claude-sonnet-4.6` failed on `ve_hard_seed4` and `ve_hard_seed7`; all other row-model pairs completed with usable outputs.

## Parse And Feasibility By Model
| Model | Usable parse | Strict protocol | Partial rescue | Strict parse failed | Feasible rows | Avg score | Avg wall s |
| --- | --- | --- | --- | --- | --- | ---: | ---: |
| `gemini-flash-latest` | 4/4 (100%) | 2/4 | 2/4 | 0/4 | 4/4 (100%) | 92.90 | 420.25 |
| `claude-sonnet-4.6` | 2/4 (50%) | 2/4 | 0/4 | 2/4 | 2/4 (50%) | 46.65 | 230.35 |
| `gpt-5.4-mini` | 4/4 (100%) | 2/4 | 2/4 | 0/4 | 4/4 (100%) | 88.84 | 12.39 |

## Per-Question Outcomes
- `tsp_hard_seed7`: all 3 models feasible, all 3 parsed via `strict_protocol_cf`.
- `tsp_hard_seed10`: all 3 models feasible, all 3 parsed via `strict_protocol_cf`.
- `ve_hard_seed4`: Gemini and GPT feasible via `partial_rescue`; Sonnet stopped with `strict_parse_failed` and `error`.
- `ve_hard_seed7`: Gemini and GPT feasible via `partial_rescue`; Sonnet stopped with `strict_parse_failed` and `error`.

## Notable Failures And Timeouts
- No timeouts in `runner-summary.json`.
- `claude-sonnet-4.6` error rows: `ve_hard_seed4`, `ve_hard_seed7`.
- `gemini-flash-latest` and `gpt-5.4-mini` rescued both VE-hard rows through `partial_rescue`.
- `concerns.md` artifacts exist under all 4 result directories.

## Learnings
1. Tried the existing runner exactly as assigned and kept it unchanged because it completed successfully end to end.
2. Do not infer failure from quiet stdout: the runner can sit silent for minutes, then re-plan the same row multiple times with changing budgets before settling on the recorded artifact.
3. For this batch, VE-hard rows were the stress case: Gemini and GPT recovered with `partial_rescue`, while Sonnet produced artifacts but still ended with unusable strict parses and `error` stop reasons.

## Files Changed

- kaggle_submission/scratch/round2/worker3/runner-log.md
- kaggle_submission/scratch/round2/worker3/runner-summary.json
- kaggle_submission/results/full/tsp_hard_seed7/question.json
- kaggle_submission/results/full/tsp_hard_seed7/gemini-flash-latest.json
- kaggle_submission/results/full/tsp_hard_seed7/claude-sonnet-4.6.json
- kaggle_submission/results/full/tsp_hard_seed7/gpt-5.4-mini.json
- kaggle_submission/results/full/tsp_hard_seed7/concerns.md
- kaggle_submission/results/full/tsp_hard_seed10/question.json
- kaggle_submission/results/full/tsp_hard_seed10/gemini-flash-latest.json
- kaggle_submission/results/full/tsp_hard_seed10/claude-sonnet-4.6.json
- kaggle_submission/results/full/tsp_hard_seed10/gpt-5.4-mini.json
- kaggle_submission/results/full/tsp_hard_seed10/concerns.md
- kaggle_submission/results/full/ve_hard_seed4/question.json
- kaggle_submission/results/full/ve_hard_seed4/gemini-flash-latest.json
- kaggle_submission/results/full/ve_hard_seed4/claude-sonnet-4.6.json
- kaggle_submission/results/full/ve_hard_seed4/gpt-5.4-mini.json
- kaggle_submission/results/full/ve_hard_seed4/concerns.md
- kaggle_submission/results/full/ve_hard_seed7/question.json
- kaggle_submission/results/full/ve_hard_seed7/gemini-flash-latest.json
- kaggle_submission/results/full/ve_hard_seed7/claude-sonnet-4.6.json
- kaggle_submission/results/full/ve_hard_seed7/gpt-5.4-mini.json
- kaggle_submission/results/full/ve_hard_seed7/concerns.md

### NOTES

- No code changes were required; the existing runner script succeeded as-is.
- The observed stdout budgets varied across repeated passes even though the parent brief described a 600s target budget.

## Related

- [task_1776364655703zxg](task_1776364655703zxg.md)
- [task_1776364360597w06](task_1776364360597w06.md)
- [round2-partition](round2-partition.md)

[[task_1776364655703zxg]]
