---
color: green
isContextNode: false
agent_name: Vic
---
# Round 2 Worker 4 — VE + MWIS Hard Complete

Completed Worker 4 end-to-end: generated all 12 assigned rows, resolved 4 probe ids, and materialized 12 model artifacts across 4 result bundles.
MWIS hard required repeated seed and size fallback; Gemini and GPT were 4/4 feasible while Sonnet failed on all 3 MWIS-hard probes.

All 4 probe ids now have the full `question.json + 3 model JSONs + concerns.md` shape.

Generated rows:

- `mwis_hard_seed5`
- `mwis_hard_seed7`
- `mwis_hard_seed8`
- `mwis_hard_seed9`
- `mwis_hard_seed10`
- `mwis_hard_seed12`
- `mwis_hard_seed13`
- `mwis_hard_seed16`
- `mwis_hard_seed14`
- `ve_hard_seed10`
- `ve_hard_seed11`
- `ve_hard_seed12`

Probe ids resolved from the first actual row in each assigned cell:

- `ve_hard_seed10`
- `mwis_hard_seed5`
- `mwis_hard_seed9`
- `mwis_hard_seed13`

Generation facts:

- VE hard `10-12` generated directly with exact posterior as `gold_objective` and `0.5` as the trivial uninformed baseline.
- MWIS hard requested seeds `5-13` could not be satisfied directly at the default size; repeated bridge-separation pre-flight failures forced fall-through to later seeds and then size fallback.
- Actual MWIS hard rows landed as `5,7,8,9,10,12,13,16,14`.
- Size fallback was required on every MWIS hard cell, using `n_nodes=120` for most rows and `n_nodes=100` for the final requested `mwis_hard_seed13` slot.
- Worker-local generation was required because the shared `build_questions.py` hard-seed fallback is capped by `MAX_GENERATED_SEED=7`, which does not cover the Round 2 high-seed brief.
- `gen-notes.md` records the per-requested-seed substitution trail, duplicate-actual-seed skips, fallback attempts, and gold solve times.

Runner headline:

- `gemini-flash-latest` completed `4/4` rows and was feasible on `4/4`.
- `gpt-5.4-mini` completed `4/4` rows and was feasible on `4/4`.
- `claude-sonnet-4.6` completed `4/4` rows but was feasible on only `1/4`; it failed or remained infeasible on all `3` MWIS-hard probes.
- Full artifact bundles were written for all `4` probe ids.

Truthful completion accounting:

- Generation: `12` rows written.
- Model artifacts: `12` JSON artifacts written across `4` rows × `3` models.
- Result bundles: `4` full directories written.
- Feasibility mix: `9/12` model runs feasible, `3/12` infeasible.

Per-question headlines:

- `ve_hard_seed10`: all 3 models were feasible. Best score was `gpt-5.4-mini` at `89.43`; `gemini-flash-latest` scored `87.61`; `claude-sonnet-4.6` scored `80.80` via `partial_rescue` but ended with `error`.
- `mwis_hard_seed5`: `gemini-flash-latest` and `gpt-5.4-mini` were feasible at `75.76` and `71.47`. `claude-sonnet-4.6` hit `strict_parse_failed`, was infeasible, and scored `0.00`.
- `mwis_hard_seed9`: strongest MWIS row overall. `gpt-5.4-mini` scored `85.69`, narrowly above `gemini-flash-latest` at `85.40`; both were feasible. `claude-sonnet-4.6` produced `strict_protocol_cf` output but remained infeasible and scored `0.00`.
- `mwis_hard_seed13`: `gpt-5.4-mini` scored `80.71` and `gemini-flash-latest` scored `77.27`, both feasible. `claude-sonnet-4.6` hit another `strict_parse_failed` result and scored `0.00`.


## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker4/build_partial.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker4/run_partial_eval.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker4/questions.partial.jsonl
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker4/child-question-ids.txt
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker4/gen-notes.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker4/runner-log.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round2/worker4/runner-summary.json
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
- /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/round2-worker4-runner-done.md
- /Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/round2-worker4-runner-progress.md

### NOTES

- MWIS hard generation required more aggressive local fallback than the shared builder supports for high seeds.
- The child runner outputs were verified from on-disk result bundles rather than relying on terminal logs alone.
- This worker stayed within the 12-row / 12-model-run brief and produced no skipped-model placeholders.

## Related

- [round2-worker4-runner-progress](round2-worker4-runner-progress.md)
- [round2-worker4-runner-done](round2-worker4-runner-done.md)

[[task_1776364360774od1]]
