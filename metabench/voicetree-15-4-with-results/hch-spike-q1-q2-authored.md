---
color: green
isContextNode: false
agent_name: Anna
---
# HCH spike: q1.py + q2.py authored, bridge blocked on .env tokens

Authored both HCH pilot task files. Bridge runs blocked (missing .env tokens). SDK imports verified. Pilot note written.

## What was done

### q1.py (updated from Ama's draft)
- Fixed `HCH_PROMPT_BODY` from dashes (`-`) to em-dashes (`—`) to match verbatim `hch/scripts/hch_in_context.py`
- Question: sum a_n = n^2+3n for n=1..10, find mod 17. **Gold = 6** (550 mod 17 = 6, verified)
- Decomposition character: borderline atomic (1-3 natural subtasks), good for seeing whether model over-decomposes
- Axes B/C/D covered via assert_true judge notes

### q2.py (new)
- Question: a+b+c=30, ab+bc+ca=281, abc=780, a<b<c — compute a+b^2+c^3. **Gold = 2346** (verified: a=5, b=12, c=13 via Vieta's cubic roots)
- Decomposition character: 3 natural subtasks (form cubic → factor → evaluate). Genuinely rewards decomposition → Axis A has real signal
- Emits Axis A judge note (expected 2-3 subtasks), per-subtask Axis B/C notes, Axis D correctness assertion

## Smoke test output
```
kaggle_benchmarks=0.3.0
model_proxy_configured=False
task=Addition Smoke Test
status=SUCCESS
passed=True
note=LLM-backed benchmark tasks will require MODEL_PROXY_URL and MODEL_PROXY_API_KEY.
```

## Bridge run results
Both exits with: `Bridge failed: KAGGLE_JUPYTER_URL and KAGGLE_JUPYTER_TOKEN must be set.`

.env missing — only .env.example present. Live tokens needed to proceed.

## Files Changed

- metabench/kaggle/examples/hch_spike/q1.py
- metabench/kaggle/examples/hch_spike/q2.py
- metabench/kaggle/pilots/hch-spike-2026-04-15.md

### NOTES

- BLOCKER: .env does not exist. User must open a live Kaggle benchmark notebook, grab KAGGLE_JUPYTER_URL + KAGGLE_JUPYTER_TOKEN + MODEL_PROXY_URL + MODEL_PROXY_API_KEY, paste into metabench/kaggle/.env, then re-run both submit_task.py calls.
- .venv also did not exist — created it and installed requirements.txt as part of smoke test verification.
- q1 HCH_PROMPT_BODY fix: Ama's draft had ASCII dashes; verbatim spec uses em-dashes. Both regexes and parse_trajectory logic were already correct.
- q2 Vieta's problem was chosen because it has 3 independent computation steps, making Axis A (decompose-or-not) non-trivial vs q1 which is more borderline.
- HANDOVER.md open questions (per-call token breakdown, Save Task flow) cannot be answered until live tokens are available.

## Related

- [hch-spike-2026-04-15](hch-spike-2026-04-15.md)

[[task_1776232463790kty]]
