---
color: green
isContextNode: false
agent_name: Mei
---
# Round 1 Worker 4 Runner — 4 IDs × 3 Models

Materialized the 4 Worker 4 probe ids into complete `results/full/{id}/` bundles.
Gemini and GPT completed all 4 rows; Sonnet timed out on the first MWIS row and the remaining 3 Sonnet rows were written as explicit skips.

Probe ids:

- `mwis_medium_seed3`
- `mwis_medium_seed7`
- `mwis_medium_seed10`
- `ve_medium_seed2`

Per-model outcomes:

- `gemini-flash-latest`: feasible `4/4`; parse paths = `strict_protocol: 3`, `partial_rescue: 1`; avg score `87.78`
- `claude-sonnet-4.6`: feasible `0/4`; parse paths = `baseline_only: 1`, `not_run: 3`; avg score `0.00`
- `gpt-5.4-mini`: feasible `2/4`; parse paths = `strict_protocol_cf: 3`, `partial_rescue: 1`; avg score `45.40`

Per-question headlines:

- `mwis_medium_seed3`: Gemini `86.78`; Sonnet timeout / baseline-only `0.00`; GPT infeasible `0.00`
- `mwis_medium_seed7`: Gemini `85.77` with timeout-carry forward from a usable feasible turn; Sonnet skipped; GPT infeasible `0.00`
- `mwis_medium_seed10`: Gemini `91.78` from a feasible turn-2 state after a later timeout; Sonnet skipped; GPT `89.45`
- `ve_medium_seed2`: Gemini `86.80` via `partial_rescue`; Sonnet skipped; GPT `92.16` via `partial_rescue`

Execution notes:

1. Resumed from on-disk state instead of restarting, preserving completed `mwis_medium_seed3` and `mwis_medium_seed7` payloads.
2. Applied tighter timeouts (`gemini-flash-latest=180s`, `gpt-5.4-mini=90s`) and an explicit Sonnet skip policy after `mwis_medium_seed3` exhausted retries at `120s`.
3. The wrapper preserved usable feasible Gemini payloads when later turns timed out on `mwis_medium_seed7` and `mwis_medium_seed10`.
4. `ve_medium_seed2` completed a forced counterfactual branch before the final Gemini payload was written; the saved result remained the usable `partial_rescue` answer.

Artifact inventory per row:

- `question.json`
- `gemini-flash-latest.json`
- `claude-sonnet-4.6.json`
- `gpt-5.4-mini.json`
- `concerns.md`


## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_medium_seed3/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_medium_seed3/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_medium_seed3/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_medium_seed3/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_medium_seed3/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_medium_seed7/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_medium_seed7/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_medium_seed7/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_medium_seed7/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_medium_seed7/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_medium_seed10/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_medium_seed10/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_medium_seed10/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_medium_seed10/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/mwis_medium_seed10/concerns.md
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/ve_medium_seed2/question.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/ve_medium_seed2/gemini-flash-latest.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/ve_medium_seed2/claude-sonnet-4.6.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/ve_medium_seed2/gpt-5.4-mini.json
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full/ve_medium_seed2/concerns.md

### NOTES

- `claude-sonnet-4.6` hit repeated timeouts on `mwis_medium_seed3`; the remaining Sonnet rows were written as truthful `skipped_model` artifacts instead of pretending they were evaluated.
- The resumed wrapper preserved usable feasible Gemini payloads when later turns timed out on `mwis_medium_seed7` and `mwis_medium_seed10`.
- `ve_medium_seed2` only wrote its final Gemini artifact after a forced counterfactual branch completed, which explains the temporary delay where only `question.json` existed on disk.

## Related

- [round1-worker4-generation](round1-worker4-generation.md)
- [round1-worker4-runner-stand-down](round1-worker4-runner-stand-down.md)

[[task_17763596432192c5]]
