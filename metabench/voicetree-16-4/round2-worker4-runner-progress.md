---
color: green
isContextNode: false
agent_name: Anna
---
# Round 2 Worker 4 Runner Complete

Executed the worker-local `4 × 3` probe eval set for `ve_hard_seed10`, `mwis_hard_seed5`, `mwis_hard_seed9`, and `mwis_hard_seed13`. All 12 result artifacts, the worker-local log/summary, and `round2-worker4-runner-done.md` were written successfully.

## Final metrics

| model | completed | feasible | avg score | parse paths |
|---|---:|---:|---:|---|
| `gemini-flash-latest` | 4 | 4 | 81.51 | `partial_rescue`=1, `strict_protocol_cf`=3 |
| `claude-sonnet-4.6` | 4 | 1 | 20.20 | `partial_rescue`=1, `strict_parse_failed`=2, `strict_protocol_cf`=1 |
| `gpt-5.4-mini` | 4 | 4 | 81.82 | `partial_rescue`=1, `strict_protocol_cf`=3 |

## Per-question headlines

- `ve_hard_seed10`: all 3 models feasible. `gpt-5.4-mini` scored `89.43`, `gemini-flash-latest` `87.61`, `claude-sonnet-4.6` `80.80` with `partial_rescue` after an exec-turn parse failure.
- `mwis_hard_seed5`: `gemini-flash-latest` `75.76` and `gpt-5.4-mini` `71.47` were feasible. `claude-sonnet-4.6` hit `strict_parse_failed` and scored `0.00`.
- `mwis_hard_seed9`: `gpt-5.4-mini` scored `85.69`, narrowly above `gemini-flash-latest` at `85.40`; both were feasible. `claude-sonnet-4.6` remained infeasible and scored `0.00` despite `strict_protocol_cf` output.
- `mwis_hard_seed13`: `gpt-5.4-mini` scored `80.71`, `gemini-flash-latest` `77.27`, both feasible. `claude-sonnet-4.6` hit another `strict_parse_failed` result and scored `0.00`.

## Deliverable note

`voicetree-16-4/round2-worker4-runner-done.md` contents:

```md
# Round 2 Worker 4 Runner Done

Completed the worker-local probe eval run for:
- `ve_hard_seed10`
- `mwis_hard_seed5`
- `mwis_hard_seed9`
- `mwis_hard_seed13`

Artifacts were written under `kaggle_submission/results/full/{question_id}/`, with worker-local summaries in:
- `kaggle_submission/scratch/round2/worker4/runner-log.md`
- `kaggle_submission/scratch/round2/worker4/runner-summary.json`

No model was globally skipped. No API/billing/rate-limit failures occurred. The run finished cleanly.

## Per-model summary

| model | completed | feasible | avg score | parse paths |
|---|---:|---:|---:|---|
| `gemini-flash-latest` | 4 | 4 | 81.51 | `partial_rescue`=1, `strict_protocol_cf`=3 |
| `claude-sonnet-4.6` | 4 | 1 | 20.20 | `partial_rescue`=1, `strict_parse_failed`=2, `strict_protocol_cf`=1 |
| `gpt-5.4-mini` | 4 | 4 | 81.82 | `partial_rescue`=1, `strict_protocol_cf`=3 |

## Per-question headlines

- `ve_hard_seed10`: all 3 models were feasible. Best score was `gpt-5.4-mini` at `89.43`; `gemini-flash-latest` scored `87.61`; `claude-sonnet-4.6` scored `80.80` but ended with `error` after an exec-turn parse failure, rescued via `partial_rescue`.
- `mwis_hard_seed5`: `gemini-flash-latest` and `gpt-5.4-mini` were feasible at `75.76` and `71.47`. `claude-sonnet-4.6` hit `strict_parse_failed`, was infeasible, and scored `0.00`.
- `mwis_hard_seed9`: strongest row overall. `gpt-5.4-mini` scored `85.69`, narrowly above `gemini-flash-latest` at `85.40`; both were feasible. `claude-sonnet-4.6` produced `strict_protocol_cf` output but remained infeasible and scored `0.00`.
- `mwis_hard_seed13`: `gpt-5.4-mini` scored `80.71` and `gemini-flash-latest` scored `77.27`, both feasible. `claude-sonnet-4.6` hit another `strict_parse_failed` result and scored `0.00`.

## Notable patterns

- `claude-sonnet-4.6` was the clear weak point on MWIS hard: `0/3` feasible, with two parse failures and one infeasible strict-protocol completion.
- `gemini-flash-latest` was reliable but slow on MWIS hard, especially `mwis_hard_seed9` (`808.6s` wall time).
- `gpt-5.4-mini` was the most balanced model here: `4/4` feasible, best row score on `ve_hard_seed10` and `mwis_hard_seed9`, and very short wall times on all four rows.
```

## Learnings

1. Tried the prepared worker-local runner directly and kept that path; the tooling was already correct for this task.
2. Do not read too much into live stdout lines like `exec 2 ✓` or `exec 3 ✓`: those are turn-level events inside a single provider run, not proof that a model JSON artifact has been written.
3. A successor should assume MWIS hard is the stress case: `claude-sonnet-4.6` is brittle there, `gemini-flash-latest` is usually reliable but slow, and `gpt-5.4-mini` currently offers the best speed/quality tradeoff on this slice.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/ve_hard_seed10/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/ve_hard_seed10/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/ve_hard_seed10/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/ve_hard_seed10/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/ve_hard_seed10/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_hard_seed5/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_hard_seed5/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_hard_seed5/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_hard_seed5/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_hard_seed5/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_hard_seed9/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_hard_seed9/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_hard_seed9/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_hard_seed9/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_hard_seed9/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_hard_seed13/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_hard_seed13/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_hard_seed13/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_hard_seed13/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_hard_seed13/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker4/runner-log.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker4/runner-summary.json
- /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/round2-worker4-runner-done.md

### NOTES

- Stdout lines during the run reflect intra-model planning/execution turns, not completed model artifacts; use the per-row JSON files or `runner-summary.json` for authoritative outcomes.
- `claude-sonnet-4.6` was stable enough on `ve_hard_seed10` only via `partial_rescue`, but it failed or remained infeasible on all three MWIS hard rows.
- `gemini-flash-latest` was reliable across all four rows but materially slower on MWIS hard, including an `808.6s` run on `mwis_hard_seed9`.
- `gpt-5.4-mini` delivered the best balance here: `4/4` feasible with the top score on two rows and very short wall times.

## Related

- [task_1776364735111j3k](task_1776364735111j3k.md)
- [round2-worker4-runner-done](round2-worker4-runner-done.md)

[[task_1776364735111j3k]]
