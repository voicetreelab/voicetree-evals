---
color: green
isContextNode: false
agent_name: Ivan
---
# Kaggle budget-metagame: concrete design + multi-turn mechanics

Read the kbench API and existing HCH HLE-12 tasks. Surfaced three Kaggle-specific constraints that change the MVP shape: (1) `thinking_tokens` is NOT exposed in the public `Usage` surface, so "charge for reasoning" from budget-metagame-benchmark-analysis.md is partially broken for thinking models; (2) multi-turn is already a solved pattern — history-string accumulation via `llm.prompt()`, no native chat state; (3) kbench has no native budget enforcement, so budgets are either soft (declared, scored post-hoc) or hand-rolled inside the task function.

## What kbench actually gives us

From `kaggle/examples/` and `kaggle/option_a_bridge/`:
- `@kbench.task` registers one task. Body is a python function with `llm` as arg.
- `llm.prompt(text, max_output_tokens=N)` → returns response string. Stateless from harness POV. `max_output_tokens` kwarg is supported on some proxies, not all (see `run_deepseek.py` comment).
- `kbench.assertions.assert_true(bool, expectation=str)` = pass/fail + a free-form diag string that lands in `.run.json`.
- Per-request and aggregated `Usage`: `input_tokens`, `output_tokens`, `*_cost_nanodollars`, `total_backend_latency_ms`. **No** `thinking_tokens` in public SDK.
- `.run.json` also has `startTime`/`endTime` for wall-clock.

So the primitive is: **one task function = one "trial"**, it can call `llm.prompt` many times in a row, and Kaggle aggregates Usage across all those calls into one conversation. Scoring happens post-hoc by reading `.run.json`.

## Multi-turn concretely

`examples/metacog_format_recall_v1/kernel.py` is the pattern:
```python
history = [f"RULE: {RULE}"]
for q, opts in FILLERS:
    history.append(f"Q: {q}")
    resp = llm.prompt("\n".join(history))
    history.append(f"A: {resp.strip()}")
history.append(f"Q: {TARGET}")
final = llm.prompt("\n".join(history)).strip()
```
That is multi-turn. For budget-metagame that becomes:
```python
history = [SCORING_PROMPT, PROBLEM]
while True:
    resp = llm.prompt("\n".join(history), max_output_tokens=CAP_PER_TURN)
    history.append(resp)
    if _contains_final_answer(resp):
        break
    if _exceeded_budget(history):
        break  # harness-enforced hard cut
    history.append(NEXT_TURN_PROMPT)  # "continue, or emit ANSWER"
```
Budget enforcement is hand-rolled inside the task body (count words/chars locally) because the kbench `Usage` object is only surfaced post-run, not between turns.

## The three Kaggle-specific design forks

### Fork 1 — thinking-token blindness
`budget-metagame-benchmark-analysis.md` depends on charging for ALL tokens incl. reasoning. Kaggle's public `Usage` doesn't expose `thinking_tokens`. **Options:**
- (a) Restrict to non-thinking models (Haiku, Flash, plain Sonnet w/ thinking off). Clean, but kills the most interesting axis.
- (b) Force scratchpad into visible output via prompt framing ("show all work in-band; final ANSWER on last line"). Then reasoning counts as `output_tokens`. Mostly works for non-thinking models; thinking models still burn hidden tokens we can't see or charge.
- (c) Accept the blindness; score only observable tokens and note in writeup that thinking-model comparisons are incomplete.

Recommendation: **(b) for MVP**, caveat in writeup. Re-evaluate if `thinking_tokens` becomes exposed.

### Fork 2 — budget enforcement mechanism
`four-budget-benchmark-proposals.md` proposes four budgets: `total_{tokens,time}`, `subtask_{tokens,time}`. Kaggle has no native way to kill a task mid-flight on a token count. **Options:**
- (a) **Soft budgets**: declare them in the prompt, score violations post-hoc from `.run.json`. Agent can "cheat" by ignoring caps — that's a feature, it surfaces bad metacog.
- (b) **Hand-rolled hard caps**: track turn count + char count in the python loop, break on overflow. `max_output_tokens=CAP` on each `llm.prompt` gives per-subtask output cap for free.
- (c) Hybrid: hard cap on turns + per-turn `max_output_tokens`; soft cap on total token $ cost scored post-hoc.

Recommendation: **(c) hybrid**. Hard total-turns limit (say 6), `max_output_tokens=subtask_cap` per turn, everything else soft + post-hoc.

### Fork 3 — task-per-arm vs arm-inside-task
We have 3 budget arms (B1 greedy, B2 exhaustive, B3 smart-metacog from the analysis node). Two shapes:
- (a) **One task file per (instance × arm)** — matches existing `hch_hle12/q41_hch.py` + `q41_vanilla.py` pattern. 10 instances × 3 arms = 30 files. Generator script like `gen_hch_hle12_tasks.py` already exists as template.
- (b) **One task file per instance, arm chosen by env var** — fewer files, but breaks the "one task = one Kaggle submission" model.

Recommendation: **(a)** — reuses the Option A bridge flow verbatim and reuses the `run_hch_hle12.py` analysis script shape.

## Proposed MVP (concrete)

**Scope**: Bounded TSP-25 × 10 instances × 3 arms = 30 kbench tasks.

**File layout** (mirrors `examples/hch_hle12/`):
```
examples/budget_tsp25/
  i01_greedy.py     i01_exhaustive.py     i01_smart.py
  i02_greedy.py     ...
  ... × 10 instances
scripts/
  gen_budget_tsp25.py   # Concorde gold, generator+prompt assembly
  run_budget_tsp25.py   # drives Option A bridge per file
  analyze_budget_tsp25.py  # reads .run.json, computes $-score
```

**Task body (pseudocode, shared across arms)**:
```python
@kbench.task(name=f"tsp25_i{i:02}_{arm}", ...)
def task(llm):
    history = [SCORING_RULE, TSP_INSTANCE, ARM_PROMPT[arm]]
    turns = 0
    while turns < 6:
        resp = llm.prompt("\n".join(history), max_output_tokens=8000)
        history.append(resp)
        tour = _parse_tour(resp)
        if tour is not None:
            break
        history.append("Continue, or emit ANSWER: <tour>")
        turns += 1
    tour_len = _length(tour) if tour else None
    gap_pct = _gap(tour_len, GOLD_LEN)
    declared = _parse_declared_gap(history[0])  # Brier signal
    kbench.assertions.assert_true(
        tour is not None,
        expectation=f"TSP25 i{i:02} arm={arm}: tour={tour!r}, len={tour_len}, "
                    f"gap_pct={gap_pct}, declared_gap={declared}, turns={turns}",
    )
    return tour is not None
```

**Scoring (post-hoc, in `analyze_budget_tsp25.py`)**:
```
$score = A * max(0, 100 - gap_pct) * convex(gap_pct)
       - K_in * input_tokens
       - K_out * output_tokens
       - T * backend_latency_ms / 1000
hard_reject if turns >= 6 and no answer
brier(declared_gap, actual_gap) for calibration axis
```
A, K_in, K_out, T tuned so B1/B2/B3 land on different points on the Pareto frontier for the reference model.

**Arm prompt deltas**:
- `greedy`: "answer in one turn using nearest-neighbour. No iteration."
- `exhaustive`: "iterate 2-opt to convergence. Budget is generous."
- `smart`: "you pay $K per token and $A per %-optimal. Stop when marginal < cost. Declare your expected gap% first."

## LOCKED PROTOCOL (2026-04-16 user-converged)

### Budget primitive: wall-clock time (not tokens)
Sidesteps `thinking_tokens` blindness — thinking models bill time identically to non-thinking. Kaggle already exposes `msg.usage.total_backend_latency_ms` per message and `chat.usage.total_backend_latency_ms` aggregated.

- `TOTAL_BUDGET_S = 1800` (30 min), tune after first run
- `SUBTASK_BUDGET_S = 600` (10 min per turn, hard kill)
- `PLAN_TURN_BUDGET_S = 60` (turn 1 kill-short)

### SDK corrections from the user guide
- Multi-turn = `with kbench.chats.new(name):` — SDK tracks history natively. Do NOT concat history strings.
- `llm.prompt()` has no `timeout=` or `max_output_tokens=` kwarg. Use `concurrent.futures.ThreadPoolExecutor().submit(llm.prompt, ...).result(timeout=N)` to get a real hard kill.
- `kbench.user.send(text)` injects a user message into the chat without triggering a response — used to feed timing stats between turns.
- `.evaluate(llm, evaluation_data=df)` runs one task over a DataFrame → 10 instances × 3 arms = 3 task files (one per arm), not 30.

### Turn protocol (adaptive, one subtask at a time, sequential deps OK)

Problem statement ships with a trivial baseline (e.g., nearest-neighbor tour) so there is always a scoreable answer even if everything after turn 1 dies.

**Turn 1 (planning only — NO solving, 60s hard cap)**
Output contract:
```
ATOMIC_PREDICTION: {"words_if_atomic": int, "p_correct_if_atomic": float}
DECLARED_GAP: <float>               # committed at T=0; Brier signal
DECISION: continue | stop            # stop = atomic-bail, commit baseline as final
NEXT_SUB: {"id": 1, "desc": "...", "time_budget_s": <int>}   # if continue
```
Prompt explicitly forbids solving. If Turn 1 dies (timeout or parse fail) → use baseline as final answer, record protocol violation.

**Turn N≥2 (one subtask per turn, 600s hard cap)**
Before the turn, we inject stats via `kbench.user.send()`:
```
TURN_{N-1} STATS: wall={s:.1f}s, input_tok={int}, output_tok={int}, cost=${usd:.4f}
CUMULATIVE: wall={s:.1f}s / {TOTAL_BUDGET_S}s, cost=${usd:.4f}
SUBTASK BUDGET: {SUBTASK_BUDGET_S}s per turn (hard kill).
Now execute NEXT_SUB.
```
Source for stats: `chat.messages[-1].usage` after each `llm.prompt`.

Turn N output contract:
```
SUB_{n}: <work>
BEST_GUESS: <current-best answer>
P_CORRECT: <float>                   # per-turn self-calibration
DECISION: continue | stop
NEXT_SUB: {"id": n+1, "desc": "...", "time_budget_s": <int>}   # if continue
```

**Termination** (any of):
- `DECISION: stop` emitted
- `time.monotonic() - start >= TOTAL_BUDGET_S`
- `concurrent.futures.TimeoutError` from the subtask timeout (last good BEST_GUESS retained; if none yet, baseline stays)

### Scoring (post-hoc, in analyze_*.py)

```
final_answer = best_guess_last_emitted or baseline
gap_pct      = 100 * (length(final_answer) - length(gold)) / length(gold)
brier_gap    = (declared_gap - gap_pct)**2
$score       = A * convex(100 - gap_pct)          # accuracy reward
             - T_total * chat.usage.total_backend_latency_ms/1000
protocol_flags:
  - turn1_died (bool)
  - subtask_killed_count (int)
  - revised_best_guess_downward (bool)
```

### Metacog axes exposed
1. **Calibration**: `DECLARED_GAP` (turn 1) vs. actual `gap_pct` — Brier.
2. **Per-turn confidence trajectory**: `P_CORRECT` sequence — should rise toward truth.
3. **Stop-decision quality**: $score of agent's chosen stop point vs. counterfactual (would one more turn have helped?).
4. **Adaptive planning**: fraction of `NEXT_SUB.desc` that references the prior `BEST_GUESS` (textual overlap) = "is the agent actually reacting to its own output?"
5. **Atomic-bail accuracy**: agents that stop on turn 1 with `DECISION: stop` — was the baseline actually the rational choice for this instance?

### Three arms via prompt injection

- **greedy arm**: system prompt includes *"You have a very small time budget. Commit after one execution subtask. Do not iterate."*
- **exhaustive arm**: *"Maximise accuracy. Use the full 30-minute budget. Ignore the cost term."*
- **smart arm**: *"You pay $T per wall-second and score $A per percent-optimal. Stop when marginal accuracy gain per second < $T/$A. The DECISION field is your stop rule."*

All three arms use the same protocol and same `.evaluate()` DataFrame — only the system-prompt string differs.

## Open questions for the user

1. Live-stats injection between turns — keep as MVP, or A/B it against a no-counter variant? Analysis Claim 4 said counter *might worsen* decisions by anchoring. *Assumption: include for MVP, A/B later.*
2. TSP-25 as the single problem class for MVP, or also include one coding-resistant class (compression, infeasibility) alongside? *Assumption: TSP-25 only for MVP — coding-resistant arm is Benchmark-3 from four-budget-benchmark-proposals.md, stays out of scope until TSP-25 produces signal.*
3. Hard turn cap of 6 feel right? Lower forces decomposition pressure, higher lets exhaustive arm breathe. *Assumption: 6 turns, revisit after first run.*
4. Do we need B3 prompt to include a live `get_tokens_used()` tool-call, or is decision-rule framing alone the MVP? `budget-metagame-benchmark-analysis.md` flagged this as an open question. *Assumption: rule-framing only for MVP — tool-call variant is a follow-up experiment (matches Claim 4 in that node).*
5. Reuse Option A bridge for iteration (recommended), or go straight to Option B packaging? *Assumption: Option A for the first 30-task pilot run, Option B only for final Kaggle submission.*

## PREDICTION CLAIMS

- **Claim 1 (p=0.75):** History-accumulating multi-turn works out-of-the-box on the Kaggle Model Proxy for non-thinking models; no kbench changes needed.
- **Claim 2 (p=0.65):** On TSP-25, a smart-metacog prompt arm beats both greedy and exhaustive arms on post-hoc $-score for Sonnet on ≥6/10 instances.
- **Claim 3 (p=0.85):** Not exposing `thinking_tokens` through the public `Usage` API materially biases the MVP against thinking models — they will appear cheaper than they are. Writeup must flag this.
- **Claim 4 (p=0.50):** Declared-vs-actual gap Brier score correlates positively with $-score across models. (Metacog and calibration align.) If it doesn't, that's a very interesting negative result.

## Related

- [budget-metagame-benchmark-analysis](budget-metagame-benchmark-analysis.md) — original analysis
- [four-budget-benchmark-proposals](four-budget-benchmark-proposals.md) — 3 MVP designs
- [kaggle-metrics-support-verified](kaggle-metrics-support-verified.md) — what Kaggle exposes
- [benchmark-v2-plan](benchmark-v2-plan.md) — 5-phase v2 plan, complementary
- `kaggle/examples/hch_hle12/` — file layout + kbench.task template to reuse
- `kaggle/examples/metacog_format_recall_v1/kernel.py` — multi-turn pattern to copy
- `kaggle/scripts/gen_hch_hle12_tasks.py` — generator template
- `kaggle/option_a_bridge/submit_task.py` — per-file runner

### NOTES

- Multi-turn is NOT a kbench feature — it's a python-loop pattern around a stateless `llm.prompt`. Kaggle aggregates Usage across the loop into one conversation for us.
- `thinking_tokens` gap is the single biggest design constraint that was not obvious before reading the SDK. Every downstream decision (non-thinking MVP, show-work framing, caveat in writeup) flows from it.
- Budget enforcement is NOT native. Harder caps must be hand-rolled inside the task function body. Soft budgets + post-hoc scoring is the path of least resistance.
- The existing `hch_hle12` generator and runner scripts are a near-perfect template — budget-metagame adds 3 arm variants but does not need new harness infrastructure.

[[budget-metagame-benchmark-analysis_1_0]]
