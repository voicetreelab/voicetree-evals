---
color: green
isContextNode: false
agent_name: Aki
---
# Round 2 Worker 2 Runner Complete After 600s Resume Split

Completed the Worker 2 Round 2 probe matrix for 4 IDs × 3 models. Mid-run, patched the runner to enforce a 600s total cap per (row, model) via resume-safe subprocesses, then split execution by model with Timi to finish Gemini and Claude without overlapping writes.

## Execution
- Started from the original mixed-model worker2 runner.
- Patched `kaggle_submission/scratch/round2/worker2/run_partial_eval.py` to add resume-safe `--single-run` subprocess execution with a 600s total timeout per `(row, model)` attempt.
- Preserved existing GPT artifacts and resumed rather than recomputing them.
- Split the remaining work by model with Timi: local lane finished Gemini-only remainder, Timi finished Claude-only remainder.
- Wrote the final human-facing summary to `voicetree-16-4/round2-worker2-runner-done.md`.

## Per-model parse rates
| model | completed | strict | rescue | failed_or_baseline | feasible | errors | avg_wall_s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gemini-flash-latest | 4 | 4 | 0 | 0 | 4 | 0 | 468.8 |
| claude-sonnet-4.6 | 4 | 4 | 0 | 0 | 4 | 0 | 151.9 |
| gpt-5.4-mini | 4 | 4 | 0 | 0 | 4 | 0 | 20.9 |

## Per-question headlines
- `graphcol_hard_seed4`: Gemini `strict_protocol_cf`, feasible=True, score=94.9550, wall_s=504.5; Claude `strict_protocol_cf`, feasible=True, score=97.8526, wall_s=214.7; GPT `strict_protocol_cf`, feasible=True, score=-0.1793, wall_s=17.9.
- `graphcol_hard_seed7`: Gemini `strict_protocol_cf`, feasible=True, score=94.6949, wall_s=530.5; Claude `strict_protocol_cf`, feasible=True, score=98.0873, wall_s=191.3; GPT `strict_protocol_cf`, feasible=True, score=-0.4210, wall_s=42.1.
- `graphcol_hard_seed10`: Gemini `strict_protocol_cf`, feasible=True, score=95.9092, wall_s=409.1; Claude `strict_protocol_cf`, feasible=True, score=99.3487, wall_s=65.1; GPT `strict_protocol_cf`, feasible=True, score=-0.1206, wall_s=12.1.
- `tsp_hard_seed4`: Gemini `strict_protocol_cf`, feasible=True, score=95.6894, wall_s=431.1; Claude `strict_protocol_cf`, feasible=True, score=98.4661, wall_s=136.4; GPT `strict_protocol_cf`, feasible=True, score=97.9990, wall_s=11.6.

## Learnings
1. Tried letting the original mixed-model runner continue, then switched to a subprocess-based resume wrapper because the stage-2 policy required a 600s total cap per `(row, model)`, not the harness default 1800s budget.
2. The non-obvious cutover pitfall is killing the outer runner after the child exits but before it writes `{model}.json`; waiting for the file boundary is the reliable handoff signal.
3. Model-disjoint concurrent lanes are safe on the same row directories because each lane writes a distinct `{model}.json`; that let Gemini and Claude finish in parallel without file conflicts once the wrapper became resume-safe.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker2/run_partial_eval.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker2/runner_ids.txt
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker2/runner-log.md
- /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/round2-worker2-runner-done.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_hard_seed4/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_hard_seed4/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_hard_seed4/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_hard_seed4/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_hard_seed4/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_hard_seed7/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_hard_seed7/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_hard_seed7/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_hard_seed7/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_hard_seed7/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_hard_seed10/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_hard_seed10/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_hard_seed10/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_hard_seed10/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/graphcol_hard_seed10/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_hard_seed4/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_hard_seed4/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_hard_seed4/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_hard_seed4/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/tsp_hard_seed4/concerns.md

### NOTES

- Mixed-model execution was interrupted after the stage-2 policy clarification; the replacement wrapper enforced 600s total wall time per subprocess rather than relying on the 1800s harness budget.
- Safe cutover depended on waiting for the model JSON write boundary, not just child-process exit, otherwise the outer runner could be killed before persisting the just-finished payload.
- A stray duplicate Claude-only outer runner appeared during monitoring and had to be terminated to restore single ownership of the local lane.

## Related

- [round2-worker2-runner-done](round2-worker2-runner-done.md)

[[task_1776364420829pea]]
