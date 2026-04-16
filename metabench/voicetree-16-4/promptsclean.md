---
color: green
isContextNode: false
agent_name: Amy
---
# Updated Prompts (Clean Prose Form)

Standalone, copy-pasteable prose prompts: System + Turn 1 (plan) + Turn N (exec, with timing block) + CF fork. Primitives-based scoring framing; no formula to decode.

# Updated Prompts — Prose Form

Standalone, copy-pasteable. Replaces the formula-encoded + schema-stub version in `experiment-spec.md`.

---

## System prompt (constant, every turn)

> You are solving an optimization problem.
>
> **Value.** Each problem is worth up to **100 points**. Your gap to the optimum reduces value linearly — 1 point per percentage-point of gap, floored at 0.
>
> **Cost.** Wall time costs **0.01 points per second**.
>
> **Budgets.** Total wall budget **1800s**. Per-subtask budget up to **600s**. Turn-1 planning budget **300s**. Max **10 exec turns**.
>
> **Task structure.** You may decompose the problem into subtasks, revise your plan between turns, and stop whenever further work is not worth its time cost. Your raw text output is saved verbatim; a post-hoc extractor pulls structured fields. Each turn we will tell you the exact fields to emit.

---

## Turn 1 user message (plan phase)

> ```
> [problem instance JSON]
> ```
>
> **Turn 1 — planning.** No answer yet. Emit these fields, in order:
>
> - `PLAN_STATE`: your free-form plan for tackling this problem. We quote it back to you verbatim on every subsequent turn — it is your persistent scratchpad.
> - `NEXT_SUB`: `{id: 1, desc: <str>, p_solve: <float in [0,1]>, time_budget_s: <int ≤ 600>}`. `p_solve` is your probability that your final answer lands within the target gap **after this subtask completes**. `time_budget_s` is how many seconds you want to spend on this subtask.
>
> Planning budget: **300s**.

---

## Turn N user message (exec phase, n ≥ 2)

> ```
> [full prior transcript — system prompt + every prior turn, verbatim]
> ```
>
> **Timing block:**
> - Global: **elapsed 847s / 1800s** (remaining 953s)
> - Last subtask: budgeted 300s, actual 412s
> - Subtask history: `[(s1: budgeted 200s, actual 180s), (s2: budgeted 300s, actual 412s)]`
>
> **Exec turn N.** Emit these fields, in order:
>
> - `SUB_{n}`: your reasoning and work for this subtask.
> - `BEST_GUESS`: your current best answer as a class-specific JSON artifact. Include this every turn, even if unchanged.
> - `UPDATED_PLAN_STATE`: your revised plan. Keep the prior verbatim if no change, or rewrite freely.
> - `QUALITY_FORECAST`: `{p_gap_le_2, p_gap_le_5, p_gap_le_10}` — your probability that BEST_GUESS is within each gap threshold.
> - `CONTINUE_FORECAST`: `{p_improve, expected_delta_score}` — probability another exec turn improves BEST_GUESS, and expected net Δ in points (after subtracting 0.01 × extra_wall_seconds).
> - `DECISION`: `continue` | `stop`.
> - `NEXT_SUB`: `{id: n+1, desc, p_solve, time_budget_s}` — **only if** `DECISION = continue`.

---

## Counterfactual fork message (post-hoc, on every clean stop)

> ```
> [full transcript up through the stop turn, verbatim]
> ```
>
> **Timing block at stop:**
> - Global: elapsed 1247s / 1800s (remaining 553s)
> - Final subtask: budgeted 300s, actual 284s
> - Subtask history: [...]
>
> You previously emitted `DECISION: stop`. This is a **counterfactual branch**: your transcript has been forked at the stop state and you are required to produce exactly one more exec turn. Emit the standard exec fields (`SUB_{n+1}`, `BEST_GUESS`, `UPDATED_PLAN_STATE`, `QUALITY_FORECAST`). Do not emit `DECISION` or `NEXT_SUB` — the branch terminates after this turn.

---

## Design notes (for anyone adapting these)

1. **Scoring is stated as primitives, not a formula.** Value / cost / budgets in natural language. Lets the model reason from economic primitives; avoids "decode the equation" tax.
2. **Timing block is mandatory in Turn N and CF fork.** `CONTINUE_FORECAST.expected_delta_score` and `DECISION` are meaningless without wall-time accounting. Without this, M6 MAE measures "model reasoning under hidden state" rather than stop-rationality.
3. **PLAN_STATE is model-owned scratch, carried verbatim.** Not a spec-owned field — the harness must never rewrite or summarize it.
4. **Raw-string loop.** No live parsing. Gemini Flash extracts structured fields post-hoc into analyzer JSON. Format-failures here are extractor bugs, not model failures.
5. **CF fork reuses the exec contract** minus `DECISION`/`NEXT_SUB`. No special CF prompt — the differentiator is the framing sentence and the transcript fork-point.

## Related

- [experiment-spec](experiment-spec.md)
- [llmpromptflowanswer](llmpromptflowanswer.md)

[[experiment-spec_1]]
