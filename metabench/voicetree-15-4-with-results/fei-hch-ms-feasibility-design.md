---
color: blue
isContextNode: false
agent_name: Fei
---
# Q1/Q2 — Bridge feasibility + multi-session experiment design + pseudocode

Multi-session HCH is confirmed possible on Option A bridge. Each llm.prompt() call creates an independent request with isolated context. .run.json captures per-call inputTokens/outputTokens. Concrete pseudocode provided.

## Q1 — Bridge feasibility

**YES — confirmed from source.**

`submit_task.py:121-125` calls `task_fn.run(kbench.llm)` — the task receives a live `llm` object. Multiple `llm.prompt()` calls are supported; each is an independent API request with a fresh context window.

The `.run.json` records all calls in `conversations[].requests[].metrics` with:
- `inputTokens`, `outputTokens` (real per-call counts)
- `inputTokensCostNanodollars`, `outputTokensCostNanodollars`
- `totalBackendLatencyMs`

The spec itself documents this (spec_corrected.md §Post-hoc actuals):
> "For per-subtask token actuals, a multi-call HCH variant is required. The Kaggle
> Option A bridge .run.json exposes per-call inputTokens/outputTokens for that case."

**Parallelism:** NOT supported — one live kernel, sequential calls only.
**Timeout constraint:** submit_task.py default = 300s. At 5 calls × ~50s avg = 250s. Tight for high-subtask questions.

## Q2 — Experiment design

Protocol: `PLAN call → N isolated EXECUTE calls → INTEGRATE call`

Each EXECUTE sees only `{question} + {this subtask desc}` — no sibling context.

```python
@kbench.task(name='hch_ms_q44')
def hch_ms_q44(llm) -> bool:
    # CALL 1: PLAN — STEP 0 (atomic prediction) + STEP 1 (decompose decision)
    plan_raw = llm.prompt(PLAN_PROMPT)        # context: question only
    atomic   = _parse_atomic(plan_raw)
    subtasks = _parse_subtasks(plan_raw)

    # CALLS 2..N+1: EXECUTE each subtask in full isolation
    sub_results = []
    for sub in subtasks:
        exec_raw = llm.prompt(EXECUTE_TEMPLATE.format(
            question=QUESTION_TEXT,
            subtask_id=sub['id'],
            subtask_desc=sub['desc'],         # only this sub — no siblings
        ))
        sub_results.append({
            'id':              sub['id'],
            'p_solve':         sub['p_solve'],
            'words_predicted': sub['words_to_produce_solution'],
            'correctly_solved':_parse_correctly_solved(exec_raw),
            'confidence':      _parse_confidence(exec_raw),
            'actual_words':    len(exec_raw.split()),
        })

    # CALL N+2: INTEGRATE — question + all sub outputs concatenated
    sub_text = '\n\n'.join(f'SUB {r["id"]}:\n{r["raw"]}' for r in sub_results)
    int_raw  = llm.prompt(INTEGRATE_TEMPLATE.format(
        question=QUESTION_TEXT, sub_outputs=sub_text,
    ))
    answer  = _parse_answer(int_raw)
    correct = _compare_answer(answer, GOLD_ANSWER, QNUM)
    kbench.assertions.assert_true(correct, expectation=f"Axis D: ...")
    return correct
```

| Aspect | Single-call | Multi-session |
|--------|------------|---------------|
| API calls/question | 1 | N+2 (avg ~5) |
| Sub context | Full shared context | Isolated: question + one subtask |
| Axis B actual | word count (text parse) | outputTokens (`.run.json`) |
| Sibling leakage | YES | NO |
| Task authoring complexity | 1 prompt template | 3 prompt templates + error handling |

### NOTES

- Verified from Q41 .run.json: conversations[0].requests[0].metrics has inputTokens=724, outputTokens=733 for single-call. Multi-session would show requests[0..N+1] each with independent metrics.
- EXECUTE_TEMPLATE needs careful design: sub-solver must not see parent's PLAN or siblings. Injecting only question + subtask desc is the minimal correct approach.
- No @kbench.task can take more than 1 parameter (kbench.llm). Multi-session does not require any change to the task registration signature.

[[fei-hch-multisession-research-overview]]
