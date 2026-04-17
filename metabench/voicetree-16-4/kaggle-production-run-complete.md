---
color: green
isContextNode: false
agent_name: Lou
---
# Kaggle Production Run Complete

Completed the Kaggle production sweep against the canonical 26-row scope with 78 canonical `.run.json` artifacts present across Gemini, Claude, and GPT. Gemini produced the only clean full pass; Claude and GPT both fast-failed on the canonical rows with Kaggle-side 503 model-unavailable errors.

## Outcome
Canonical 26-row production status:
- `78/78` canonical row JSON files present
- `78/78` canonical `.run.json` files present
- `26/78` canonical rows completed without a row-level error

Canonical parse-method distribution:
- `strict_protocol_cf`: `22`
- `partial_rescue`: `4`
- `baseline_only`: `52`

Success-tier interpretation:
- Gold by canonical artifact count: `78` canonical `.run.json` files exist.
- Quality caveat: only Gemini produced a clean parsed full pass; Claude and GPT fast-failed on all canonical rows.

Bottom line:
- Gemini: full clean canonical pass
- Claude: canonical coverage present, but every canonical row fast-failed with Kaggle-side `503 model unavailable`
- GPT: same canonical full-sweep `503 model unavailable` failure mode

The production pull is complete at the artifact level for the agreed 26-row scope, but only one of the three model families yielded usable canonical evaluation signal.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/kaggle/build_task.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/kaggle/task.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scripts/run_kaggle_production.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/runs/kaggle_production
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/kaggle/output

### NOTES

- Canonical reporting is filtered to the original 26 ids agreed with Ayu.
- `runtime-default` on the live Kaggle kernel was not safe because `kbench.llm.model` persisted across cells.
- A concurrent upstream mutation expanded `questions.jsonl` from 26 rows to 206 rows before the Claude full sweep.

[[task_177635921351608r]]

[[/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/kaggle-production-run-complete_1.md]]