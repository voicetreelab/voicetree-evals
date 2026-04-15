# HCH-InContext — benchmark spec (CORRECTED v2)

**Version:** 0.2
**Supersedes:** `spec.md` v0.1 for the prompt body and per-subtask field names.
**Track:** Metacognition (primary) / Executive function (secondary)
**License:** CC0

## What changed vs spec.md v0.1

Three corrections came out of the 2026-04-15 design pass with the user. Each is load-bearing for honest scoring:

1. **`solved` → `correctly_solved`** (per-subtask END marker).
   `solved` was ambiguous: a model could mark a subtask "solved" meaning "I produced output" rather than "the output is correct." `correctly_solved` forces the metacog claim to be about correctness, not completion. Pairs naturally with `confidence` as the calibrated probability that the just-emitted subtask result is right.

2. **`token_estimate` → `words_to_produce_solution`** (per-subtask PLAN entry).
   Tokens are a model-internal abstraction the LLM has weaker grounding on than words. Words are model-agnostic, trivially counted post-hoc (`len(text.split())`), and the per-subtask actuals are recoverable from the text between START/END markers in single-call HCH — no multi-call shape required. The estimate is explicitly scoped: "output words for THIS subtask's work between markers."

3. **New STEP 0 — ATOMIC BASELINE PREDICTION.**
   Without an explicit atomic-baseline claim, Axis A (decompose-or-not metacog) is unscorable: we can only see whether HCH got the answer, not whether the model correctly judged that decomposition was *worth it*. Forcing the model to commit to `{words_if_atomic, p_correct_if_atomic}` *before* the decomposition decision turns Axis A into a real, comparable claim — comparable to a paired vanilla one-shot arm on the same question.

The four metacognitive axes from v0.1 remain the same conceptually, but A is now decomposed (A1 atomic-self-knowledge, A2 atomic-word self-knowledge, A3 decompose-decision quality) because the new STEP 0 makes the sub-claims separable.

## Axes (corrected)

| Axis | Predicted | Ground truth | Metric |
|------|-----------|--------------|--------|
| **A1. Atomic-self-knowledge (correctness)** | `p_correct_if_atomic` | Vanilla-arm actual correctness on same Q | Brier |
| **A2. Atomic-self-knowledge (effort)** | `words_if_atomic` | Vanilla-arm actual word count | MAPE |
| **A3. Decompose-decision quality** | Implicit (chose to decompose iff `p_correct_decomp_plan > p_correct_if_atomic` or shorter) | Did HCH actually beat vanilla on correctness when it chose to decompose? | Decision-rate confusion table; conditional accuracy lift |
| **B. Per-subtask effort** | `words_to_produce_solution` | `len(text_between_markers.split())` | MAPE |
| **C. Per-subtask self-consistency** | `p_solve`, `confidence` | `correctly_solved` (self-report — see honesty note below) | Brier |
| **D. Final answer calibration** | `P_CORRECT` | Judge match vs gold | Brier |

**Honesty note on Axis C.** Without per-subtask gold answers, "correctness" of an intermediate subtask is only the model's self-report (`correctly_solved`). Brier on `p_solve` vs `correctly_solved` measures *internal consistency* between PLAN-time prediction and EXECUTE-time judgment — not ground truth. To upgrade C to true intermediate verification, subtasks would need independently judgeable gold (out of scope for this spec; possible follow-up via stricter task templates).

The vanilla one-shot arm becomes **load-bearing**, not optional: A1, A2, A3 are unscorable without it.

## Protocol — single-session corrected prompt body (verbatim)

One `llm.prompt()` call per question. The agent does atomic prediction, decomposition decision, execution, and integration in one context.

```
Solve the following question.

STEP 0 — ATOMIC BASELINE PREDICTION. Before deciding whether to decompose, predict what would happen if you just answered this question directly with no decomposition. Emit:
  ATOMIC_PREDICTION: {"words_if_atomic": <int>, "p_correct_if_atomic": <float>}

STEP 1 — PLAN. Now decide whether to decompose. If atomic is best, emit one subtask. If decomposition will help (higher p_correct, fewer total words, or both), break it up however you see fit. For each subtask, emit:
  {"id": <n>, "desc": "...", "p_solve": <float>, "words_to_produce_solution": <int>}
Emit all subtasks as a single JSON array under the heading `SUBTASKS:`.

STEP 2 — EXECUTE. For each subtask, wrap your work in markers:
  === SUB <id> START ===
  <your work>
  === SUB <id> END === {"correctly_solved": true|false, "confidence": <float>}

STEP 3 — INTEGRATE. Produce the final answer.
  ANSWER: <answer>
  P_CORRECT: <float>
```

Em-dashes (`—`) are intentional and load-bearing — do not normalize to hyphens (the v1 spike found that hyphen substitution silently changed model behavior).

## Per-question wrapper (unchanged from v0.1)

```
Question type: {answer_type}
Subject: {raw_subject}

QUESTION:
{question}

{body}
```

## Vanilla baseline arm (new — required for Axis A scoring)

Same per-question wrapper, but the `{body}`:

```
Solve the following question. Output exactly:
  ANSWER: <answer>
  P_CORRECT: <float>
```

## Post-hoc actuals

In single-call mode, all per-subtask actuals are recoverable from the captured response text:

- `actual_words_per_subtask = len(text_between_SUB_START_and_SUB_END.split())`
- Per-subtask input tokens are **not meaningfully defined** in single-call mode (all subtasks share the same input context); only OUTPUT-side estimates are scored against actuals.
- For per-subtask token actuals (not words), a multi-call HCH variant is required (one `llm.prompt()` per subtask). The Kaggle Option A bridge `.run.json` exposes per-call `inputTokens`/`outputTokens` for that case.

## Honest scope of this spec

- The single-call corrected prompt is sufficient for Axes A1/A2/A3 (paired with vanilla arm), B (via word count), C (as self-consistency only), D (vs gold judge).
- "Multi-call HCH" remains an unimplemented variant for stricter Axis B (real token actuals) and possible future Axis E (Bayesian update of P_CORRECT after each sub).
- All axes assume a competent judge against a gold answer for the final answer; the per-subtask "intermediate verification" axis does not require per-subtask gold under this spec (see honesty note above).

## Provenance

Designed in conversation between user (manummasson8@gmail.com) and Bob (suborchestrator) on 2026-04-15. Driven by:
1. The toy 2-Q spike (`kaggle/pilots/hch-spike-2026-04-15.md`) showing `solved` was ambiguous and that single-call HCH gives only aggregate token counts.
2. The user's metacog notes restating Axes A/B/C as the load-bearing capabilities (decide-to-decompose, predict-difficulty, intermediate-verification).
3. Recognition that without an explicit atomic baseline, Axis A is observed-only, not predicted — therefore unscorable as a calibrated metacog claim.

## Related

- `spec.md` — original v0.1 spec (still authoritative for the four-axis framing; v0.2 corrects only the prompt body and field names)
- `scripts/hch_in_context.py` — reference implementation; needs minor patches to match v0.2 field names if rerun
- `kaggle/pilots/hch-hle12-2026-04-15.md` — first pilot using v0.2 (12 HLE Qs, two-arm: HCH v2 + vanilla)
