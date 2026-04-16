---
color: green
isContextNode: false
agent_name: Bob
---
# Pre-S0 kbench SDK Verification — All 6 Questions

Read-only inspection of kaggle_benchmarks SDK source at /opt/homebrew/lib/python3.14/site-packages/kaggle_benchmarks/. All 6 load-bearing questions answered. Q1 (timeout) is CLEAR — no SDK ceiling. Q4 (Evaluate More Models) is YELLOW/UI-only as predicted.

## Verdicts

### Q1 — Per-row timeout: **OK, 1800s safe**
`tasks.py:137` → `.evaluate(timeout: float|None)` passes directly to `joblib.Parallel(timeout=timeout)`. **No hardcoded SDK ceiling.** Pass `timeout=1800` in our call.
Caveat: threading backend does NOT kill timed-out threads (`tasks.py:169`: "timed-out threads are not killed and will run to completion"). They are marked FAILED for retry, but keep running. Irrelevant for us — our LLM calls self-terminate via token budget, not wall-kill.

### Q2 — @kbench.task signature: **GREEN**
`scheduling.py:78-83` merges `{**grid_params, **row.to_dict()}` → `func(**call_params)`. Any DataFrame column becomes a kwarg automatically. Return `float` auto-infers to `Score` result type (`results.py:93: class Score(Result[float])`). Our planned signature `(llm, instance_json, cls, difficulty, seed, gold_objective, baseline_objective, value_cap) -> float` works verbatim.

### Q3 — .evaluate() shape: **GREEN**
`evaluate(grid=None, evaluation_data=pd.DataFrame, ...)`. Call `task.evaluate(llm=[kbench.llm], evaluation_data=df)` is correct — `llm` goes into `**kwargs` → grid `{'llm': [kbench.llm]}`. `kbench.llm` is a `ModelProxy` (OpenAI-compatible LLMChat) injected at Kaggle runtime from `MODEL_PROXY_URL + LLM_DEFAULT` env vars.

### Q4 — "Evaluate More Models": **YELLOW — UI-only confirmed**
No CLI/API equivalent in SDK. Our scripts use `kaggle kernels push/status`. Kaggle presumably re-runs the notebook with a different `LLM_DEFAULT` env var per model. `kbench.llms` exists (`load_available_models()` reads `LLMS_AVAILABLE` env var) but that's Kaggle-injected at evaluation time. **Biggest manual-error surface at deadline — flagging to Ben.**

### Q5 — kbench.judge_llm: **GREEN (exists), YELLOW (not a structured extractor)**
`__init__.py:39: judge_llm = kaggle.load_judge_model()` — exists when Kaggle is configured. Falls back: `LLM_DEFAULT_JUDGE` → `LLM_DEFAULT_EVAL` → `LLM_DEFAULT`. It's a plain `LLMChat` (ModelProxy), NOT a built-in structured extractor. We must write our own extraction prompt and call `kbench.judge_llm.prompt(...)` ourselves.

### Q6 — EMBEDDED_MODULES lifecycle: **GREEN — once per notebook**
`portfolio_spike.py:3023: _ensure_bundle()` called at **module top-level**, not inside task function. Module imports once per notebook session → `_ensure_bundle()` runs once (~300ms). Has idempotency guard: skips writes if file exists and matches. `.evaluate()` calls the decorated function N times, but module-level code doesn't re-execute. 210-row scaling: ~300ms once, not 63s.

### NOTES

- Threading timeout does NOT kill threads — marks FAILED for retry logic only. Our LLM calls must self-terminate (token budget / stop sequences), not rely on OS kill.
- judge_llm is just another LLM instance — we write our own extraction prompt. It is NOT a magic structured extractor.
- Q4 (Evaluate More Models) remains UI-only — no programmatic trigger found. This is the highest manual-error risk at deadline.

## Related

- [task_1776348744160b4e](task_1776348744160b4e.md)
- [kaggle-submission-design](kaggle-submission-design.md)
- [kaggle-submission-filetree](kaggle-submission-filetree.md)

[[task_1776349026039ga4]]
