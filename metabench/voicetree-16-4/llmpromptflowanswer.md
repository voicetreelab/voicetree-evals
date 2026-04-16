---
color: green
isContextNode: false
agent_name: Amy
---
# LLM Prompt Design + Flow (Answer)

Walkthrough of what the harness prepends to each question: constant system prompt + phase-specific output contract (Turn 1 plan / Turn N exec / CF fork). Raw-string loop, post-hoc Gemini Flash extractor.

# LLM Prompt Design + Flow

Question asked: *when an LLM gets given a question, what's the additional prompt we add on? how does it change per phase?*

## Layer 1 — System prompt (constant, injected every turn)
> You are solving an optimization problem under a 30-minute wall budget. Objective is economic: score = max(0, 100 − gap_pct) − 0.01 × wall_seconds. You may decompose the problem into subtasks, revise your plan each turn, and stop when you judge no more subtasks are worth their time cost. Raw text output; the harness extracts structured fields post-hoc.

Establishes economic scoring, decomposition license, stop-rationality framing, and raw-string I/O contract.

## Layer 2 — User message (varies by phase)

### Turn 1 (plan phase)
`<instance JSON>` + the plan output contract:
```
PLAN_STATE: <free-form, model-structured plan; persisted verbatim into turn 2 prompt>
NEXT_SUB: {id: 1, desc: <str>, p_solve: <float>, time_budget_s: <int>}
```
No `BEST_GUESS` yet. Turn-1 budget 300s.

### Turn N (exec phase, n ≥ 2)
Full prior transcript (PLAN_STATE carried verbatim) + exec contract:
```
SUB_{n}: <free reasoning>
BEST_GUESS: {<artifact in class-specific JSON>}
UPDATED_PLAN_STATE: <free-form; may keep prior or rewrite>
QUALITY_FORECAST: {p_gap_le_2, p_gap_le_5, p_gap_le_10}
CONTINUE_FORECAST: {p_improve, expected_delta_score}
DECISION: continue | stop
NEXT_SUB: {id: n+1, desc, p_solve, time_budget_s}   # iff continue
```
Per-subtask budget ≤600s, max 10 exec turns, hard wall 1800s.

### Counterfactual fork (post-hoc synthetic phase)
Fires on every clean stop (`stop_reason ∈ {subtask_stop, turn1_stop}`). Transcript forked at stop state, one more exec turn forced — same exec contract but DECISION effectively disabled. Measures net Δ(score − 0.01·extra_wall) → feeds M5 (CF-$) and M6 (expected vs realized Δ error).

## Phase-delta table
| Aspect | Turn 1 | Turn N | CF fork |
|---|---|---|---|
| System prompt | same | same | same |
| Output contract | PLAN_STATE + NEXT_SUB | SUB/BEST_GUESS/UPDATED_PLAN/QUALITY/CONTINUE/DECISION/NEXT_SUB | exec contract, forced continue |
| Prior context | instance only | instance + full transcript | transcript up to stop |
| Budget | 300s | ≤600s per subtask | +1 turn |
| BEST_GUESS required | no | yes | yes |

## Key design choices
- **Raw-string loop** — harness never live-parses. It only appends turns to history. Gemini Flash extracts structured fields post-hoc into analyzer-friendly JSON.
- **Phase shifts live in the output contract**, not in different system prompts. The economic framing stays constant so the model's stop/continue decision is always scored against the same objective.
- **PLAN_STATE is model-owned scratch** — persisted verbatim, model may rewrite. This is the substrate metacog metrics read from (M1 from NEXT_SUB.p_solve; M4 from QUALITY_FORECAST; M6 from CONTINUE_FORECAST.expected_delta_score).

## PREDICTION CLAIMS
- **Claim:** The constant-system-prompt + phase-specific-output-contract split is the whole prompt design; no hidden reformatter exists between turns. *Falsifiable by:* grepping the harness code for any turn-indexed system prompt variants.
- **Claim:** The CF fork reuses the Turn-N contract verbatim (no special CF prompt). *Falsifiable by:* inspecting the CF branch implementation — if it strips/adds fields, this claim is wrong.

---

## Revision after user pushback

User flagged three issues with the walkthrough above. All three land.

### (1) Scoring formula is over-encoded
`max(0, 100 − gap_pct) − 0.01 × wall_seconds` hides its own semantics inside an equation. Cleaner: state the primitives in natural language and let the LLM do the arithmetic.

**Proposed replacement:**
> Each problem is worth up to **100 points** of value. Your gap to the optimum reduces value linearly (1 point per % gap, floored at 0). Wall time costs **0.01 points/sec**. Total wall budget **1800s**, per-subtask budget up to **600s**.

Same function; transparent primitives; removes the "decode the formula" tax.

### (2) The contract stubs aren't the actual prompts — they're schemas
Spec shorthand like `PLAN_STATE: <free-form plan>` is a field schema, not a user message. Actual prose prompts below.

**Turn 1 user message (plan):**
> [problem instance]
>
> Turn 1 — planning. Emit, in order:
> - `PLAN_STATE`: free-form plan. We quote this back to you verbatim on every subsequent turn.
> - `NEXT_SUB`: `{id: 1, desc, p_solve, time_budget_s}`. `p_solve` is your probability the final answer lands within the target gap after this subtask. `time_budget_s` ≤ 600.
>
> Planning budget: 300s.

**Turn N user message (exec):**
> [full prior transcript, PLAN_STATE carried verbatim]
>
> **Timing:** global elapsed 847s / 1800s (remaining 953s). Last subtask: budgeted 300s, actual 412s. Subtask history: [s1 180/200s, s2 412/300s].
>
> Exec turn N. Emit, in order:
> - `SUB_{n}`: reasoning/work for this subtask
> - `BEST_GUESS`: class-specific JSON artifact (your current best answer)
> - `UPDATED_PLAN_STATE`: revised plan, or keep prior verbatim
> - `QUALITY_FORECAST`: `{p_gap_le_2, p_gap_le_5, p_gap_le_10}` — probability your BEST_GUESS is within each gap
> - `CONTINUE_FORECAST`: `{p_improve, expected_delta_score}` — probability another exec turn improves BEST_GUESS, and expected Δ in points after subtracting time cost
> - `DECISION`: `continue` | `stop`
> - `NEXT_SUB`: `{id: n+1, desc, p_solve, time_budget_s}` — only if continue

### (3) Missing timing metadata in Turn N — spec gap
As originally written, Turn N gives the model the transcript but no wall-time accounting. `CONTINUE_FORECAST.expected_delta_score` and the `DECISION` to continue/stop are the whole point of the benchmark — asking the model to forecast value-per-time without telling it how much time it has or has burned is under-specified.

**Required additions to Turn N prompt:**
- `elapsed_s` (global) and `remaining_s`
- last subtask: `budgeted_s` vs `actual_s`
- subtask history: list of (budgeted_s, actual_s) for every prior subtask

**Why it matters for the metrics:** M6 (expected_delta_score vs realized CF Δ MAE) is only meaningful if the model was pricing time against a known remaining budget. Without the timing block, M6 measures "model is bad at forecasting under hidden state" rather than "model is bad at forecasting its own improvement."

### Corrected phase-delta table
| Aspect | Turn 1 | Turn N | CF fork |
|---|---|---|---|
| System prompt | same (prose, primitives not formula) | same | same |
| Prior context | instance | instance + transcript + **timing block** | transcript up to stop + timing block |
| Emit schema | PLAN_STATE, NEXT_SUB | SUB/BEST_GUESS/UPDATED_PLAN/QUALITY/CONTINUE/DECISION/NEXT_SUB | same as Turn N, DECISION stripped |
| Budget | 300s | ≤600s per subtask | 1 forced extra turn |

## Updated PREDICTION CLAIMS
- **Claim:** Replacing the formula with prose primitives leaves M1/M4 Briers unchanged (±noise) but reduces format-confusion failures at turn 1. *Falsifiable by:* A/B the two system prompts on 20 questions, compare parse-failure rates and score.
- **Claim:** Adding the timing block to Turn N materially improves M6 MAE on CONTINUE_FORECAST. *Falsifiable by:* ablation run — with vs without timing block, compare |expected_delta_score − realized CF Δ|.
- **Claim:** Current spec does not pass timing metadata into Turn N. *Falsifiable by:* reading the harness source; if `build_turn_n_prompt()` already injects elapsed/remaining, I'm wrong.

[[experiment-spec_1]]
