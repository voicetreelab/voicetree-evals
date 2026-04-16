---
color: blue
isContextNode: false
agent_name: Fei
---
# Multi-session HCH design research — feasibility + experiment design + recommendation

Research into whether true child-agent HCH (one llm.prompt() per subtask, context-isolated) is feasible on Kaggle Option A bridge and worth switching to for the next re-run. Verdict: feasible yes, worthwhile no — not yet. Fix v1 bugs first.

## Architecture Contrast

**Current (single-session):** ONE `llm.prompt()` call per question. All of STEP 0/1/2/3 in one shared context. Decomposition is stylistic markup — sub-solvers see siblings' reasoning.

**Multi-session (Factored Cognition HCH):** N+2 `llm.prompt()` calls per question. Each subtask executes in a fresh isolated context with no sibling work visible. True architectural separation.

## Research Summary

| Question | Verdict |
|---|---|
| Q1: Possible on bridge? | ✅ YES — multiple `llm.prompt()` per `@kbench.task` supported; `.run.json` captures per-call metrics |
| Q2: Protocol shape? | PLAN call → N isolated EXECUTE calls → INTEGRATE call (N+2 total) |
| Q3: Main pro? | Real per-subtask token accounting (Axis B upgrade) + true context isolation |
| Q3: Main con? | ~5× latency, integration drift risk, 3× task authoring complexity |
| Q4: Axis that gains? | **Axis B** (words → real tokens). A/C/D unchanged. |
| Q5: Load-bearing? | Only for architectural isolation claim; accuracy/calibration claims work in single-session |
| Q6: Recommendation? | ❌ Don't switch yet — fix 5 v1 bugs first, establish clean baseline, then 2-Q spike |

## Key Insight

The v1 pilot failures were LaTeX format bugs, not single-session architecture bugs. Multi-session on top of broken parsing is premature. Priority: Eva's 5 fixes → v2 re-run → THEN multi-session spike as HCH v3.

### NOTES

- The spec_corrected.md §Post-hoc actuals already anticipates multi-call HCH explicitly — it's not a new idea, just unimplemented.
- Future agent: don't conflate 'context isolation' (multi-session) with 'no context leakage between questions' (already true in single-session). The isolation in question is between SUB 1 and SUB 2 within the same question.

[[task_17762430353779gg]]
