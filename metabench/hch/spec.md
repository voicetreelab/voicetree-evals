# HCH-InContext — benchmark spec

**Version:** 0.1 (pre-Kaggle)
**Track:** Metacognition (primary) / Executive function (secondary)
**License:** CC0

## What this measures

Whether a language model can accurately **predict its own compute needs** — the primitive required for factored cognition / HCH (Humans Consulting HCH) to be a useful architecture for agentic AI.

Four independent metacognitive axes, each separately Brier-scorable:

| Axis | Question the agent answers | Metric |
|------|----------------------------|--------|
| A. Decompose-or-not | "Is decomposing this problem worth more than solving it monolithically?" | Binary decision, scored vs counterfactual monolithic run |
| B. Difficulty prediction | "Per subtask: probability I solve it; tokens I will need." | Brier on p_solve; MAPE on token_estimate |
| C. Intermediate verification | "Did sub_i actually come out correct?" | Brier vs objective verification (not self-report) |
| D. Integration | "Given sub outputs, what is the final answer and my confidence?" | End-to-end accuracy; Brier on P_CORRECT |

Optional axis E: Bayesian update — does the agent rationally revise P_CORRECT after each sub's outcome? Measurable as Brier on pre-integration vs post-integration end-to-end confidence.

The benchmark is deliberately multi-signal. A frontier model can score high on A and D but fail B; or score well on B for tokens but poorly for p_solve. Aggregating these would mask the structure. The dashboard is the deliverable.

## Why token prediction is load-bearing

An agent that cannot predict its own compute needs cannot allocate compute rationally, cannot halt when it exceeds budget, and cannot tell a scheduler "give me more time on this sub, less on that one." Useful-HCH requires all three. Current frontier models are known to be bad at self-estimation (MAPE > 100% in pilot); the benchmark makes this measurable and comparable across models.

## Protocol — single-session version (spike implementation)

One `claude -p` (or equivalent) call per task. The agent does decomposition, prediction, execution, and integration in one context.

Prompt structure:
```
Solve the following question.

STEP 1 — PLAN. Decide how to tackle this. If the task is atomic, one
subtask is fine; if it benefits from decomposition, break it up however
you see fit. For each subtask you commit to, emit a JSON object with
at minimum:
  {"id": <n>, "desc": "...", "p_solve": <float>, "token_estimate": <int>}
Emit all subtasks as a single JSON array under the heading `SUBTASKS:`.

STEP 2 — EXECUTE. For each subtask, wrap your work in markers:
  === SUB <id> START ===
  <your work>
  === SUB <id> END === {"solved": true|false, "confidence": <float>}

STEP 3 — INTEGRATE. Produce the final answer.
  ANSWER: <answer>
  P_CORRECT: <float>
```

Parse: the SUBTASKS JSON array, per-sub work text between markers, per-sub end-of-block JSON, final answer and confidence.

## Protocol — fresh-session version (follow-up)

For each task:
1. **Phase 1 — Planner session.** Fresh session. Agent decomposes and emits predictions. No execution.
2. **Phase 2 — Executor sessions.** N fresh sessions, parallel. Each given only its own sub-prompt. Solves. Token count captured per session.
3. **Phase 3 — Integrator session.** Fresh session. Given original question + each executor's output (not the planner's predictions). Produces final answer + P_CORRECT.

This version gives clean per-subtask token accounting and eliminates in-context contamination between plan, execution, and integration. It is the "real" HCH test. The single-session version is the cheap pilot that tells us whether to invest in the fresh-session harness.

## Measurement details

### Axis A — Decompose-or-not

The agent's STEP 1 output implicitly answers this (subtasks: 1 → atomic; subtasks: N>1 → decomposed). For each task, run a monolithic counterfactual (no STEP 1/2/3 scaffolding, just solve it) and compare end-to-end accuracy. The correct decomposition decision is the one that produces higher accuracy at lower token cost. Brier the agent's decision against the counterfactual-optimal decision across tasks.

### Axis B — Difficulty prediction

Per subtask: predicted p_solve vs actual "was it solved correctly" (ground truth from integration correctness or from objective sub-grader — see Axis C for verification). Predicted token_estimate vs actual tokens.

**Caveat on per-sub token attribution** in single-session version: total tokens for the call are measurable (from the API usage block); per-sub attribution is a proxy (e.g., character count between START/END markers, scaled to total). Tool-use tokens are invisible at sub granularity. Fresh-session version resolves this.

MAPE = `mean(|predicted - actual| / actual)`.

### Axis C — Intermediate verification

The agent self-reports `solved: true|false` at each sub's END marker. This is *not* ground truth. Real ground truth requires one of:
1. Objective verifier per sub (unit test, type check, domain-specific validator)
2. External grader agent (separate session, no access to predictor's output)
3. Adversarial sub injection (insert a known-unsolvable sub; agent's `solved: true` on it is the error signal)

For Kaggle submission, use option 2 (external grader) as default; option 3 as a bonus axis on a subset of tasks.

### Axis D — Integration

Standard: final answer vs gold; Brier on final P_CORRECT.

### Axis E (optional) — Bayesian update

Capture the agent's P_CORRECT both (1) at end of STEP 1 (decomposition phase, before any sub executes) and (2) at end of STEP 3 (after all subs). A rational agent updates both directions based on sub outcomes. Scored as Brier improvement: Brier(P_CORRECT_pre) - Brier(P_CORRECT_post). Positive = updated in the right direction.

## Task authoring requirements

1. **Decomposable.** At least half the tasks must genuinely benefit from breaking into 2-5 subparts (e.g., multi-step computation, multi-constraint reasoning). Otherwise Axis A has no signal.
2. **Executable sub-verifiability.** For at least a subset of tasks, each subtask's correctness should be independently checkable (numeric output matching, constraint satisfaction). Enables Axis C option 1.
3. **Tool-use mixed.** Include tasks where Python/Bash execution is legitimately useful and tasks where it isn't. Tests whether the agent predicts tool-tokens correctly (pilot shows big blind spots here).
4. **Borderline end-to-end difficulty.** Same criterion as metacoach/spec.md — Vanilla monolithic accuracy in [20%, 80%] range.
5. **Original-authored.** No derived benchmark text (CC0-compatible, Kaggle-rule-compatible).

Recommended task count for Kaggle submission: **15-20 tasks.** HCH runs are compute-heavier than metacoach (3+ sessions per task in fresh-session version), so fewer tasks is the right tradeoff.

## Scoring procedure

1. Run the full pipeline on each task. Collect: SUBTASKS JSON, per-sub execution blocks, final answer, final P_CORRECT, total tokens.
2. For each sub: grade `solved` against external grader or objective verifier. This is the Axis C ground truth.
3. For each task: grade final answer against gold.
4. Compute:
   - Axis A: `#{tasks where agent's decompose decision matched counterfactual-optimal} / n`
   - Axis B-p_solve: `mean Brier` across all (task × sub) pairs
   - Axis B-tokens: `mean MAPE` across all (task × sub) pairs
   - Axis C: `mean Brier` of self-reported `solved` vs external grader
   - Axis D-accuracy: `#correct / n`
   - Axis D-Brier: `mean Brier` of final P_CORRECT vs binary correctness
   - Axis E (optional): `mean(Brier_pre - Brier_post)` per task

Report per-task values and aggregate values. No single composite score — the dashboard is the artifact.

## Pre-registered predictions (from n=5 pilot on HLE-borderline)

- Axis B (tokens, MAPE): will exceed 100%. *Result: 101% on pilot — just barely met.*
- Axis B (p_solve Brier): will be < 0.25. *Result: 0.033 on pilot — but self-fulfilling; real signal requires external grading.*
- Axis D (end-to-end accuracy vs isolated monolithic): HCH will **underperform** isolated monolithic by at least 1 point on borderline tasks. *Result on n=5: HCH 1/5 vs isolated vanilla 2/4 — directionally confirmed but small n.*
- Axis A: agent will over-decompose (choose N>1 subtasks when monolithic would be better) more often than under-decompose.

## Output format

Submission includes:
- `tasks.json` — authored task set
- `answers.json` — answer keys (held-out)
- `results.jsonl` — one row per task with: qnum, subtasks_plan, sub_executions, final_answer, final_p_correct, total_tokens, per_sub_tokens
- `counterfactual_monolithic_results.jsonl` — single-shot solve for Axis A
- `external_grader_results.jsonl` — separate agent's grading per sub for Axis C
- `summary.json` — computed per-axis values

## Scripts

- `scripts/hch_in_context.py` — single-session pipeline runner, resumable JSONL output
- `scripts/hch_score.py` — parses results, computes Axis B/C/D metrics, produces per-task table

For Kaggle submission, a fresh-session harness extending these to 3 sessions per task is the recommended next step; single-session version suffices for a pilot-grade submission.

## Known limitations

- Single-session version conflates planning, execution, and integration in one context. A perfect-metacog agent would not benefit from fresh-session isolation; a context-polluting agent would. The delta between single-session and fresh-session HCH results is itself a metacog measurement — whichever value is larger tells us how much agents depend on isolation.
- Counterfactual for Axis A requires running a second pass. Doubles compute but is necessary.
- External grader for Axis C introduces grader-model dependency. Run with two different grader models and report disagreement rate.
