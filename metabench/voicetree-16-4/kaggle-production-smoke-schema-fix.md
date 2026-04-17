---
color: green
isContextNode: false
agent_name: Lou
---
# Kaggle Production Smoke + Schema Fix

Stabilized the live Kaggle bridge path: isolated verifier namespaces in the generated task bundle, then re-ran the live one-row smoke until the payload exposed final feasibility, parse provenance, and final evaluation details needed for the production report.

## Decisions
- Accepted Ayu's clarification that the canonical production dataset is the existing 26-row `kaggle_submission/questions.jsonl`.
- Kept `scripts/build_questions.py` untouched.
- Continued from Step 2 onward, using the live Kaggle Jupyter proxy path only.

## Fixes Applied
### Verifier namespace isolation
`kaggle_submission/kaggle/build_task.py` was updated so each verifier source file is executed in its own globals dict and only its public `verify` function is re-exported into the generated task bundle.

Reason:
- The previous flat-merge approach let private helper names collide across verifier files.
- This broke the first Kaggle smoke with a `ValueError: not enough values to unpack (expected 4, got 2)` inside `cjs_verify()` because it ended up calling another verifier's `_parse_instance()` helper.

Result:
- Rebuilt `kaggle_submission/kaggle/task.py` now contains isolated blocks such as `# verifiers/cjs.py (isolated namespace)` and binds `cjs_verify = _CJS_VERIFIER_GLOBALS['verify']`.

### Bridge result schema parity
`kaggle_submission/scripts/run_kaggle_production.py` was updated so the remote Kaggle wrapper computes the same final-row semantics as the local runner:
- `final_submission_source`
- `final_evaluation`
- `feasible`
- `gap_pct`
- `parse_path`

This is computed from the bundled `task.py` using `_initial_best_guess()` and `_evaluate_submission()` instead of relying on `run_instance()` alone.

## Live Kaggle Smoke
Command shape:
- `python kaggle_submission/scripts/run_kaggle_production.py run --proxy-url '<live tokenized URL>' --ids cjs_medium_seed1`

Successful smoke bundle:
- `/Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/kaggle/output/kaggle-production-smoke-runtime-default-20260416T172413Z/payload.json`

Persisted local row artifact:
- `/Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/runs/kaggle_production/google_gemini-3-flash-preview/cjs_medium_seed1.json`

Observed smoke facts:
- `status=ok`
- `requested_model=runtime-default`
- `effective_model=google/gemini-3-flash-preview`
- `rows=1`
- `detail_rows=1`
- `missing_ids=0`

Observed row facts for `cjs_medium_seed1`:
- `parse_path=strict_protocol_cf`
- `final_submission_source=cf_parsed`
- `feasible=True`
- `gap_pct=10.0`
- `stop_reason=decision_stop`
- `score=87.22296294626`
- `score_at_stop=0.0`
- `score_after_cf=87.22296294626`
- `verified_makespan=99`

## Next Step At This Checkpoint
- Probe `claude-sonnet-4.6` and `gpt-5.4-mini` on a faster row (`steiner_medium_seed1`) to confirm model availability in the Kaggle runtime.
- If available, launch the 26-row production run sequentially per model and pull all row artifacts into `results/runs/kaggle_production/`.


## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/kaggle/build_task.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/kaggle/task.py
- /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scripts/run_kaggle_production.py

### NOTES

- `build_task.py` now emits each verifier in an isolated exec namespace to avoid helper-function collisions after flat-merging verifiers into `kaggle/task.py`.
- The Kaggle bridge wrapper now mirrors the local `eval_harness/run_local.py` semantics by computing `final_submission_source`, `final_evaluation`, `feasible`, `gap_pct`, and `parse_path` inside the remote task wrapper.
- The live smoke used the runtime default model because model-override probes for Claude/GPT were still pending at this checkpoint.

[[task_177635921351608r]]
