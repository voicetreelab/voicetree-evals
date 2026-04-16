# MetaCoach Kaggle Pilot — Spike Note 2026-04-15

**Status:** COMPLETE — both tasks ran, real results recorded below.

---

## Run summary

| Q | Task name | Model | passed | vanilla | metacoach | redirected | artifacts |
|---|-----------|-------|--------|---------|-----------|------------|-----------|
| Q1 | `metacoach_pilot_q1_grid_independence` | gemini-2.5-flash | ❌ False | answer=None, p=None | answer=None, p=0.99 | False | `.run.json` only |
| Q2 | `metacoach_pilot_q2_last_digit_sum` | gemini-2.5-flash | ✅ True | answer=None, p=None | answer='B', p=0.99 | True* | `.task.json` + `.run.json` |

*See format-compliance section — `redirected=True` on Q2 is confounded by vanilla format failure.

---

## What was done (full timeline)

| Step | Result |
|------|--------|
| Author `q1.py` | ✅ `examples/metacog_spike/q1.py` |
| Author `q2.py` | ✅ `examples/metacog_spike/q2.py` |
| `python smoke_test.py` | ✅ `kaggle_benchmarks=0.3.0`, `status=SUCCESS`, `passed=True` |
| `.env` credentials written | ✅ all 4 Option A creds present |
| Increase bridge timeout to 300s | ✅ (default 30s timed out; 2 LLM calls per task need ~50-90s) |
| `submit_task.py examples/metacog_spike/q1.py` | ✅ ran (exit 1 = passed=False); `.run.json` emitted |
| `submit_task.py examples/metacog_spike/q2.py` | ✅ ran (exit 0 = passed=True); `.task.json` + `.run.json` emitted |

---

## Q1 — `metacoach_pilot_q1_grid_independence` (gold: A = 63/512)

**Run:** 2026-04-15T06:23:20Z → 06:24:48Z (88s total, model latency 87991ms)

**Results:**
- `status=SUCCESS`, `passed=False`
- `vanilla_answer=None`, `vanilla_correct=False`, `vanilla_p=None`
- `metacoach_answer=None`, `metacoach_correct=False`, `metacoach_p=0.99`
- `redirected=False`

**Failure mode:** Format non-compliance. The model (gemini-2.5-flash) correctly computed the answer (63/512 = A via row-DP) but ended responses with `$\boxed{\text{A}}$.` instead of the required `ANSWER: A` line. The ANSWER regex matched nothing in either arm. The vanilla response also lacked `P_CORRECT:`, hence `vanilla_p=None`. The metacoach response emitted `P_CORRECT: 0.99` (parsed) but no `ANSWER:` line.

**Artifacts:**
- `.run.json`: `metacoach_pilot_q1_grid_independence-run_id_Run_1_google_gemini-2.5-flash.run.json`
- `.task.json`: NOT emitted (assertion failed — kbench only emits .task.json on pass)

**Token breakdown from .run.json (conversation level):**
- Total input: 2526 tokens, total output: 4158 tokens
- Per-call breakdown: only ONE request shown in run.json (request indexing gap — see open questions)

---

## Q2 — `metacoach_pilot_q2_last_digit_sum` (gold: B = 2)

**Run:** 2026-04-15T06:26:11Z → 06:27:00Z (49s total)

**Results:**
- `status=SUCCESS`, `passed=True`
- `vanilla_answer=None`, `vanilla_correct=False`, `vanilla_p=None`
- `metacoach_answer='B'`, `metacoach_correct=True`, `metacoach_p=0.99`
- `redirected=True` ← see format-compliance section

**Vanilla run** (req-1): Model correctly computed 5050 − 2208 = 2842, last digit = 2, stated "The final answer is $\boxed{B}$" — but did NOT emit `ANSWER: B`. Format non-compliance → answer=None.

**MetaCoach run** (req-2): Model performed 3-level metacognitive reflection pre/post, correctly computed the answer, and correctly emitted `ANSWER: B\nP_CORRECT: 0.99`. Parsed successfully.

**Per-call token breakdown (Q2 run.json shows both requests):**

| Call | Input tokens | Output tokens | Latency |
|------|-------------|---------------|---------|
| Vanilla (req-1) | 137 | 966 | 25095ms |
| MetaCoach (req-2) | 1436 | 2193 | 23811ms |
| **Total** | **1573** | **3159** | **48906ms** |

**Artifacts:**
- `.task.json`: `metacoach_pilot_q2_last_digit_sum.task.json` ✅
- `.run.json`: `metacoach_pilot_q2_last_digit_sum-run_id_Run_1_google_gemini-2.5-flash.run.json` ✅

---

## Format compliance issue (critical finding)

The vanilla arm **consistently** fails to emit `ANSWER: X` on its own line. Gemini 2.5 Flash defaults to LaTeX box notation (`$\boxed{A}$` or `$\boxed{B}$`) rather than the plain-text format required by the parser. This affects both Q1 and Q2 vanilla arms.

The metacoach arm **partially** fixes this: Q1 metacoach still failed (no `ANSWER:` line), Q2 metacoach succeeded (correctly emitted `ANSWER: B`). The metacoach instruction's scaffolding appears to encourage more structured output on Q2 but not reliably.

**Impact on benchmark signal:**
- `vanilla_answer=None` makes Brier-delta computation impossible for vanilla.
- `redirected=True` on Q2 is a **false positive**: the model reasoned correctly in both arms, but vanilla's format failure made `vanilla_answer=None ≠ metacoach_answer='B'`, triggering `redirected=True`. No genuine Axis-3 ambiguity resolution observed.
- Genuine redirection signal will require fixing format compliance first (see next steps).

---

## HANDOVER.md open questions — answered

**Does `.run.json` expose per-call token breakdown?**
YES — Q2's run.json shows per-request metrics (req-1 and req-2 each have separate `inputTokens`, `outputTokens`, `totalBackendLatencyMs`). Q1's run.json shows only one request despite two LLM calls — possibly a kbench behavior when the first request fails to parse correctly. The per-call breakdown is available and useful for Brier-delta accounting.

**Does Kaggle's "Save Task" flow work cleanly?**
PARTIAL — `.task.json` was emitted for Q2 (passed=True) but NOT for Q1 (passed=False). The kbench framework appears to only emit `.task.json` when `assert_true` passes. The "Save Task" UI step was not tested (would require opening the Kaggle notebook UI and clicking the button).

**Can HCH recursion fit inside one `@kbench.task`?** (HCH question)
Not applicable — see `hch-spike-2026-04-15.md`.

---

## Isolation contract violation (spike note, unchanged)

Both arms run in one shared kernel session (Option A). Per-arm and per-question isolation violated. Acceptable for toolchain-validation spike only. Production runs need per-(question, arm) fresh sessions.

---

## Bridge timeout finding

Default `timeout_seconds=30.0` in `submit_task.py` is insufficient for tasks with 2 LLM calls (each 23-31s). **Changed to 300s** in `option_a_bridge/submit_task.py:228`. This change is load-bearing for multi-call tasks.

---

## Next steps after this spike

1. **Fix format compliance before any real benchmark run.** Add `ANSWER: X` enforcement to the prompt or use a post-processing regex fallback. Alternatively switch to a model that reliably follows strict output format instructions.
2. **Re-run Q1 with format fix** to get real vanilla vs metacoach comparison signal.
3. **Test "Save Task" UI** on Q2 (which did emit `.task.json`) — open the Kaggle notebook and click Save Task to validate the submission flow end-to-end.
4. **Genuine Axis-3 test** requires vanilla to also parse correctly — then compare `vanilla_answer != metacoach_answer` without format noise.

---

## Provenance

Task files authored by Amy (agent) on 2026-04-15.  
Suborchestrator: Amit → re-run suborchestrator: Cho → worker: Dae.  
SDK version at smoke test: `kaggle_benchmarks=0.3.0`.  
Bridge runs executed by Dae (worker) on 2026-04-15.  
Model: `google/gemini-2.5-flash` (set via `LLM_DEFAULT` in `.env`).
