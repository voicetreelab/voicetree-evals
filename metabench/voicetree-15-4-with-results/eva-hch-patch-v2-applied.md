---
color: green
isContextNode: false
agent_name: Eve
---
# HCH HLE-12 patch v2 applied — 5 fixes, smoke-green

Applied all 5 bug-fix patches to gen_hch_hle12_tasks.py and regenerated all 24 task files. Smoke test green: no syntax errors, no f-string NameError on Q44, judge code path callable with mock.

## Patches Applied

### PATCH 1 — LLM-as-judge for ANSWER correctness (Bug 1: LaTeX boxing)
Added `_judge_answer(llm, gold, full_response)` to `SHARED_CODE`. Both HCH and Vanilla task functions now call the judge after getting the model response. `correct = judge_pass` (primary signal). `official_pass` (regex) still recorded as diagnostic. Judge prompt: `Gold answer: "<gold>"\nModel response: "<full>"\nDid the model correctly state the gold answer? Reply YES or NO only.`

### PATCH 2 — max_output_tokens=32768 (Bug 2: truncation)
All `llm.prompt(PROMPT)` calls changed to `llm.prompt(PROMPT, max_output_tokens=32768)` in both HCH and Vanilla task templates. 32768 is the minimum acceptable per spec; Gemini 2.5 Flash supports up to 65536 but 32768 is a safe, documented value.

### PATCH 3 — Strengthen STEP 3 INTEGRATE instruction (Bug 2: format drift)
Added to `HCH_PROMPT_BODY` STEP 3 section:
```
The FINAL line of your response MUST be exactly:
  ANSWER: <your answer>
  P_CORRECT: <float between 0 and 1>
Do NOT use LaTeX, \boxed{}, or markdown for these two lines — plain text only.
```

### PATCH 4 — Fix f-string gold-answer brace NameError (Bug 3: generalized)
In `make_hch_task` and `make_vanilla_task`, added:
```python
gold_esc = repr(gold).replace('{', '{{').replace('}', '}}')
```
Used `gold_esc` (no `!r`) instead of `{gold!r}` in expectation f-string contexts. Plain assignment `GOLD_ANSWER = {gold!r}` left unchanged (no f-string there). Only Q44 has braces in gold (`flag{no_zeros}`); all others unaffected but protected.

### PATCH 5 — P_CORRECT plain-float instruction (no-op verification)
PATCH 3 already covers this — the two-line format requirement mandates `P_CORRECT: <float between 0 and 1>` in plain text. No additional work needed. Verified present in generated files.

## Smoke Test Output
```
All 24 files parse clean
judge_answer: OK
compare_answer Q44: OK
hch_hle12_q44_hch returned: True
hch_hle12_q44_vanilla returned: True
ALL SMOKE TESTS PASSED

PATCH 3 (STEP 3 instruction): present in q44_hch.py
PATCH 2 (max_output_tokens): present
PATCH 1 (judge call): present
PATCH 4 (brace escape in gold): present in q44_hch.py
PATCH 2+1 in vanilla: present
ALL PATCH VERIFICATION CHECKS PASSED
```

## Key Diff — gen_hch_hle12_tasks.py

**HCH_PROMPT_BODY** — STEP 3 strengthened:
```diff
-    "STEP 3 — INTEGRATE. Produce the final answer.\n"
-    "  ANSWER: <answer>\n"
-    "  P_CORRECT: <float>"
+    "STEP 3 — INTEGRATE. Produce the final answer.\n"
+    "The FINAL line of your response MUST be exactly:\n"
+    "  ANSWER: <your answer>\n"
+    "  P_CORRECT: <float between 0 and 1>\n"
+    "Do NOT use LaTeX, \\boxed{}, or markdown for these two lines — plain text only."
```

**SHARED_CODE** — `_judge_answer` added (new function at end of block):
```python
def _judge_answer(llm, gold, full_response):
    judge_prompt = (
        f'Gold answer: "{gold}"\n'
        f'Model response: "{full_response}"\n'
        'Did the model correctly state the gold answer? Reply YES or NO only.'
    )
    try:
        judge_raw = llm.prompt(judge_prompt, max_output_tokens=16)
        judge_pass = judge_raw.strip().upper().startswith("YES")
    except Exception as _e:
        judge_raw = f"JUDGE_ERROR: {_e}"
        judge_pass = False
    return judge_pass, judge_raw
```

**make_hch_task / make_vanilla_task** — new `gold_esc` local + changed task body:
```diff
+    gold_esc = repr(gold).replace('{', '{{').replace('}', '}}')
 ...
-    f'    raw = llm.prompt(PROMPT)\n'
-    f'    correct = _compare_answer(traj["answer"], GOLD_ANSWER, QNUM)\n'
+    f'    raw = llm.prompt(PROMPT, max_output_tokens=32768)\n'
+    f'    official_pass = _compare_answer(traj["answer"], GOLD_ANSWER, QNUM)\n'
+    f'    judge_pass, judge_raw = _judge_answer(llm, GOLD_ANSWER, raw)\n'
+    f'    correct = judge_pass  # primary correctness signal is the judge\n'
```

## Files Changed

- kaggle/scripts/gen_hch_hle12_tasks.py
- kaggle/examples/hch_hle12/q41_hch.py
- kaggle/examples/hch_hle12/q41_vanilla.py
- kaggle/examples/hch_hle12/q43_hch.py
- kaggle/examples/hch_hle12/q43_vanilla.py
- kaggle/examples/hch_hle12/q44_hch.py
- kaggle/examples/hch_hle12/q44_vanilla.py
- kaggle/examples/hch_hle12/q48_hch.py
- kaggle/examples/hch_hle12/q48_vanilla.py
- kaggle/examples/hch_hle12/q49_hch.py
- kaggle/examples/hch_hle12/q49_vanilla.py
- kaggle/examples/hch_hle12/q52_hch.py
- kaggle/examples/hch_hle12/q52_vanilla.py
- kaggle/examples/hch_hle12/q53_hch.py
- kaggle/examples/hch_hle12/q53_vanilla.py
- kaggle/examples/hch_hle12/q55_hch.py
- kaggle/examples/hch_hle12/q55_vanilla.py
- kaggle/examples/hch_hle12/q57_hch.py
- kaggle/examples/hch_hle12/q57_vanilla.py
- kaggle/examples/hch_hle12/q65_hch.py
- kaggle/examples/hch_hle12/q65_vanilla.py
- kaggle/examples/hch_hle12/q68_hch.py
- kaggle/examples/hch_hle12/q68_vanilla.py
- kaggle/examples/hch_hle12/q99_hch.py
- kaggle/examples/hch_hle12/q99_vanilla.py

### NOTES

- PATCH 2: max_output_tokens=32768 set in task call. kbench.llm.prompt() is assumed to accept this kwarg (can't verify without live kernel). If it doesn't, judge_answer itself also uses max_output_tokens=16 — same assumption. Worst case: kwarg is silently ignored.
- PATCH 1: judge uses same model as task (no separate model kwarg). The task spec says 'call a cheap judge model (e.g. google/gemini-2.5-flash)' — since the llm object is already configured for that model via MODEL_PROXY_URL env, this is equivalent.
- PATCH 4: Only Q44 has braces in gold. The gold_esc approach is robust for any future questions with braces in answers.
- PATCH 5 is a no-op: Patch 3 already adds the explicit P_CORRECT format line. Vanilla prompt body did NOT get the STEP 3 instruction (it's HCH-specific) — Vanilla still has its own 'Output exactly: ANSWER: / P_CORRECT:' format which is sufficient.
- All 24 task files regenerated from scratch via the fixed generator. No manual edits to individual task files needed.

[[task_17762428944860ah]]
