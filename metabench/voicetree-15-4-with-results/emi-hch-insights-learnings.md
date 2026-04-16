---
color: purple
isContextNode: false
agent_name: Emi
---
# HCH HLE-12 — cross-cutting insights + methodology learnings

Consolidated insights from v1 pilot + discussion: LLM-as-judge beats regex, LaTeX isn't the bug (rigid parser is), max_tokens must be near API ceiling, Axis C self-report is the measurement (not a gap), JSON-ification is overkill. For future metacog benchmark runs.

## Key insights for future metacog benchmarks

### 1. LLM-as-judge > regex parsing for answer correctness
**Why:** Regex parsers are brittle against real model output: LaTeX boxing (`$\boxed{X}$`), markdown, verbose essays, semantic equivalents (`dodecagon` vs `12-sided polygon`). A cheap-model judge handles all of these uniformly with trivial prompt: *"Gold: X. Response: Y. Did the model correctly state the gold? YES/NO."*
**Cost at n=12–24:** ~$0.002 extra per run — negligible.
**Keep regex only for:** `P_CORRECT` float extraction (needs parseable float for Axis D scoring). Answer field goes through judge.
**Pitfall avoided:** simple `response.contains(gold)` breaks on short answers — gold="C" matches almost every response. Use judge, not substring.

### 2. LaTeX is not the bug — the rigid parser is
**Original framing was wrong:** banning LaTeX in prompt is over-constrained. Let the model write naturally. The fix is parser-side (accept `$\boxed{X}$` as equivalent to `ANSWER: X`) or judge-side (LLM judge handles it transparently). Only keep plain-text constraint on the ONE field that genuinely needs it: `P_CORRECT` float.

### 3. max_output_tokens must be near API ceiling, not a conservative 8192
**Why:** HCH v2 structured response (ATOMIC_PREDICTION + SUBTASKS + N SUB blocks + ANSWER + P_CORRECT) easily hits 30k+ tokens on hard reasoning Qs. Q43 in v1 used 3,163 output tokens and still truncated mid-structure. Cap output tokens too low → the model runs out before emitting `ANSWER:` → looks like "protocol drift" but is actually truncation.
**Rule:** set to the model's documented API max (65k for Gemini 2.5/3 Pro, etc.). You only pay for tokens actually emitted — no cost downside to high ceiling.

### 4. Axis C (self-report `correctly_solved`) IS the metacog claim — not a design gap
**Original mischaracterization:** I called it a "design gap" because `correctly_solved` can't be verified against ground truth.
**Correction:** the self-report IS the measurement. The metacog claim is *"the model thinks this subtask is solved with confidence X"*. That's a valid thing to measure. The finding from v1 — model uniformly says `True` on every subtask regardless of final correctness — is a REAL signal of metacog failure, not a methodology flaw.
**Future upgrade (optional):** per-subtask gold answers would let you verify self-report vs ground truth, but the current self-consistency measurement is still valid.

### 5. JSON-ifying subtask output is overkill
**What JSON would solve:** format drift on `=== SUB N END === {...}` lines (but this didn't actually fail in v1).
**What JSON would NOT solve:** truncation (partial JSON is worse than partial markers), protocol skip (brackets just as easy to ignore), LaTeX boxing (same regex problem).
**What JSON might HURT:** reasoning quality (models often reason worse in JSON mode), escape pain (multi-line work with quotes/backslashes is ugly as JSON string), cross-model comparison (native structured-output modes differ across Gemini/Claude/GPT).
**Verdict:** keep free-text work between markers; JSON-ify only what's already structured (ATOMIC_PREDICTION + SUBTASKS array + END-marker dict).

### 6. f-string gold embedding is a generalizable footgun
**Specific bug:** Q44 gold `flag{no_zeros}` triggered NameError because task generator used `f"gold = '{gold_val}'"`, and Python tried to evaluate `{no_zeros}` as a variable.
**Generalized fix:** never embed gold answers in f-strings — use `repr()` or plain string concatenation. Affects any question with `{...}` in the gold (flags, LaTeX, JSON-shaped answers, dict literals).

### 7. Noise-contaminated axis scores need per-axis validity framing
**Template for metacog reports:** `Axis | Raw | Clean | N valid | Bias direction | Valid?`
- Raw: as-is aggregate
- Clean: after excluding bug-contaminated Qs OR using post-hoc correction (e.g. LaTeX-aware extraction)
- N valid: count of questions where the axis can actually be scored
- Bias direction: does the bug inflate or deflate?
- Validity: valid / partially valid / invalid as calibration

**Example from v1:** Axis C raw Brier = 0.026 looks great but is INVALID as calibration (model marks everything solved). Axis D raw Brier = 0.934 is REAL and ROBUST. Reporting raw-only would hide both truths.

### 8. Test matrix for "does capability → metacog?"
HCH HLE-12 v1 ran on Gemini 2.5 Flash (cheap baseline). v2 should run in parallel on:
- Gemini 3 Pro (or latest available) — stronger same-family
- Claude Sonnet 4.6 — different architecture, RLHF-heavy
- ChatGPT (GPT-5 or latest) — different training regime
**Hypothesis to test explicitly:** stronger model → lower D Brier (better calibration) + decomposes more selectively + A2 word MAPE drops. If a stronger model shows no metacog improvement, the finding upgrades from "Flash is bad" to "metacog doesn't improve with capability" — a much bigger result.

### 9. Orchestrator discipline pays off in long-horizon sessions
**Pattern:** Bob → Eli (runner) → Emi (handover suborch) → Eva (analysis) → Eve (patch). Each level did its job; my context stayed clean enough to compose the final MC-properties table and run the retry loop. Attempting this single-agent would have blown the context window on any of the intermediate steps.

## Open design question (delegated to research agent)

**Should HCH run as single-session (current) or multi-session with real child agents?**

Current implementation: single `llm.prompt()` call per question. Model does ATOMIC_PREDICTION, SUBTASKS planning, EXECUTE of each sub, and INTEGRATE all in one context. The "decomposition" is stylistic, not architectural — there are no independent sub-contexts.

Alternative: true HCH where the parent session spawns real child sessions, each with an isolated context that only sees its assigned subtask. Parent INTEGRATES from child outputs.

**Open questions for research agent:**
- Is multi-session HCH *possible* on the Kaggle Option A bridge? What mechanism?
- What does the experiment design look like (protocol, task-file shape, data capture)?
- Pros/cons vs single-session
- Does it change which axes are measurable (esp. Axis B: real per-subtask token accounting becomes possible)?
- Cost implications (N+1 API calls per question)
- Load-bearing for the metacog claim? Or is the current single-session shape already sufficient?

**Status:** Delegated to Sonnet research agent. Left open for user review — Emi does NOT synthesize the answer, user reads raw research output.

## Related
- `kaggle/pilots/hch-hle12-2026-04-15.md` (v1 full results)
- `hch/spec_corrected.md` (v0.2 spec — protocol locked)
- `eva-hch-analysis-overview.md` (noise-corrected axis detail)
- `eva-hch-fixes.md` (fix recommendations)
- `emi-hch-hle12-spike-complete.md` (v1 end-to-end)

[[task_1776238764431kq6]]
