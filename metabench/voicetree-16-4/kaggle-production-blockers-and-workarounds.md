---
color: green
isContextNode: false
agent_name: Lou
---
# Kaggle Production Blockers And Workarounds

Documents the concrete problems encountered during the production run and the exact workarounds used: verifier namespace collisions, live-kernel model persistence, Kaggle-side 503 availability failures, and the mid-run global dataset expansion from 26 to 206 rows.

## Blockers And Workarounds
### 1. Verifier namespace collision in generated `kaggle/task.py`
Observed during early smoke:
- `cjs_verify()` called the wrong helper after flat-merging verifier files into one namespace.

Workaround used:
- updated `kaggle_submission/kaggle/build_task.py` to execute each verifier in an isolated namespace and re-export only its `verify` symbol
- rebuilt `kaggle_submission/kaggle/task.py`

### 2. `runtime-default` model drift on the Kaggle kernel
Observed during the first full launch:
- the live notebook persisted `kbench.llm.model` across bridge calls
- a nominal runtime-default full run inherited the previous GPT override

Workaround used:
- treated `runtime-default` as unsafe after detection
- used explicit model slugs for all subsequent full launches

### 3. Full-sweep model availability failures
Observed on canonical full sweeps:
- Claude full sweep: every canonical row errored with `InternalServerError: Error code: 503 - {'message': 'The requested model is currently unavailable.', 'type': 'invalid_request_error'}`
- GPT full sweep: the same canonical row-level `503` failure on every row

Evidence this was load/availability-related rather than a total configuration miss:
- both Claude and GPT succeeded on 1-row smoke probes before the full sweeps

### 4. Upstream `questions.jsonl` scope drift during the run
Observed after the long Gemini pass:
- global `kaggle_submission/questions.jsonl` expanded from `26` rows to `206` rows while this task was in flight
- the subsequent Claude full sweep therefore loaded `206` rows instead of the agreed `26`

Workaround used:
- final reporting filtered strictly to the original canonical 26 ids
- extra Claude artifacts were left on disk but treated as out-of-scope noise for this task

### 5. MWIS workaround status
- none used in this task
- Ayu's clarified 26-row dataset already excluded the blocked MWIS hard seed 3 path, so no rebuild or fallback ladder was needed here

## Key Artifact Paths
Initial smoke proof with fixed schema:
- `/Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/kaggle/output/kaggle-production-smoke-runtime-default-20260416T172413Z/payload.json`

GPT canonical full sweep (fast-fail availability blocker):
- `/Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/kaggle/output/kaggle-production-full-runtime-default-20260416T173040Z/payload.json`

Gemini canonical full sweep (clean pass):
- `/Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/kaggle/output/kaggle-production-full-google_gemini-3-flash-preview-20260416T173202Z/payload.json`

Claude full sweep (206-row drifted input, canonical subset still present):
- `/Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/kaggle/output/kaggle-production-full-claude-sonnet-4.6-20260416T202925Z/payload.json`

Canonical per-model results root:
- `/Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/runs/kaggle_production`

explains [[kaggle-production-run-complete]]
