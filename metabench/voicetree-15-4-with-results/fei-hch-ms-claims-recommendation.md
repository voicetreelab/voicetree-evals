---
color: blue
isContextNode: false
agent_name: Fei
---
# Q5/Q6 — Metacog claim analysis + final recommendation

Multi-session is only load-bearing for the architectural isolation claim, not the accuracy/calibration claim. Recommendation: don't switch for the next re-run. Fix v1 bugs → v2 clean baseline → THEN a 2-question multi-session spike (~$0.015) to decide if isolation matters.

## Q5 — Is multi-session load-bearing for the metacog claim?

### Claims that REQUIRE multi-session
- **Architectural isolation claim**: 'Does the model correctly predict per-subtask token cost when its sub-execution context is genuinely isolated from sibling work?' — word-count proxy in single-session doesn't capture this.
- **Factored cognition claim**: 'Can the planner correctly assess that splitting into independent sub-problems will beat atomic?' — in single-session, sub-solvers benefit from full in-context reasoning of prior steps, which conflates planning quality with execution quality.

### Claims equally testable in single-session
- **Accuracy gap** (HCH > vanilla?): testable in single-session with paired vanilla arm. No change.
- **Axis A1/A2/A3** (decompose-decision calibration): ATOMIC_PREDICTION + vanilla arm give all needed ground truths.
- **Axis D** (overconfidence): P_CORRECT vs gold judge — identical regardless of session structure.
- **Decomposition never paid off** (0/7 in v1): this conclusion holds in either mode.

### Is single-session a valid approximation?
**For the calibration/accuracy claim** (axes A1/A2/A3/D): YES — single-session is a valid, complete test.

**For the architectural isolation claim**: NO — single-session measures 'stylistic decomposition with shared context', which is a real capability but different from the Factored Cognition HCH.

The current benchmark primarily tests calibration + accuracy claims. Multi-session is only needed if the architectural isolation claim becomes part of the benchmark's scope.

## Q6 — Recommendation

**VERDICT: Stay with single-session for Gemini 3 / Claude / ChatGPT re-run.**

### Why not now
1. **LaTeX bugs, not architecture bugs, caused v1 measurement failures.** Eva's 5 patches (LLM judge for answer correctness, anti-LaTeX prompt + parser fallback, INTEGRATE output constraint, external correctly_solved judge) address all 4 v1 bugs in single-session. These must land first.
2. **No clean single-session baseline exists yet.** Multi-session vs single-session comparison is only interpretable once single-session produces valid axis scores. Currently v1 data is partially contaminated.
3. **3× engineering overhead** on top of 5 open bugs is poor sequencing.

### When to do multi-session
After Eva's 5 patches are applied and a v2 12-question re-run validates clean axis scores.

### Minimum viable spike (to de-risk the switch)
**2 questions × 2 arms = 4 task files** — e.g. Q44 (hard, n_subtasks likely 3–4) and Q41 (medium, 2 subtasks):
- `q44_hch_ms.py` + `q41_hch_ms.py` (multi-session variants)
- Run against the same model as v2 re-run
- Compare: does isolation change accuracy, n_subtasks, Axis B MAPE?
- If no change: multi-session not worth the overhead. Flag as confirmed.
- If change: launch as HCH v3, run full 12-Q set.

**Cost of spike: ~$0.015 total** (10 API calls × $0.0003/call at gemini-2.5-flash rates). Negligible.

### Summary judgment
Multi-session HCH is a principled scientific upgrade for the architectural isolation claim. It is NOT a prerequisite for the current benchmark signal (calibration + accuracy). Sequence: fix bugs → clean baseline → then decide based on evidence from the 2-Q spike.

### NOTES

- The 2-Q spike should include one question where HCH chose to decompose (multiple subtasks) and one where it went atomic. This tests whether isolation matters both in decomposed and atomic paths.
- If launching the multi-session spike, keep the single-session HCH arm running in parallel for the same questions — direct comparison requires paired runs.

[[fei-hch-multisession-research-overview]]
