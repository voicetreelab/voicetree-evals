---
color: green
isContextNode: false
agent_name: Eva
---
# Fix recommendations for HCH HLE-12 re-run — ordered by ROI

3 ordered fixes: (1) anti-LaTeX format + parser extension — unlocks all 12 vanilla ground truths; (2) strengthen INTEGRATE output constraint — fixes 25% HCH parse-fail rate; (3) external correctly_solved judge — makes Axis C meaningful.

## Fix 1 (Highest ROI): Anti-LaTeX format instruction + parser extension
**Fixes:** Bug 1 (all 12 vanilla parse failures) + HCH parse failures Q43/Q49/Q68

**Prompt addition** (both arms):
> "Output your final answer as `ANSWER: <your answer>` — plain text only, no LaTeX notation, no \\boxed{}, no $...$ math mode."

**Parser fix**: Also accept `$\\boxed{X}$` as fallback extraction.

**Impact**: Unlocks valid A1/A3 ground truth for all 12 Qs. Turns A1 from partially-valid-but-inflated into fully valid. Currently 2/12 Qs latex-recoverable; this fixes root cause.

---

## Fix 2 (High ROI): Strengthen INTEGRATE step output constraint
**Fixes:** Bug 2 protocol drift (Q43,Q49,Q55,Q68 — 25% of HCH arm)

**Prompt addition** (STEP 3 INTEGRATE):
> "The FINAL line of your entire response MUST be exactly `ANSWER: <concise answer>` (plain text, no LaTeX). If you do not emit this line, your response is invalid."

**Also consider**: max_tokens=1500 cap to prevent essay-mode on long Qs (Q49: 2158 out tokens, Q43: 3163 out tokens caused drift).

**Impact**: Recovers A3/B/C validity for 4 Qs. Reduces HCH parse-fail rate from ~25% (3/12) to ~0%. Combined with Fix 1, brings N valid to 12/12 for most axes.

---

## Fix 3 (Medium ROI): Add external correctly_solved judge
**Fixes:** Axis C design gap (self-report ≠ calibration)

**Approach A**: After final answer judged, backfill correctly_solved = (final_answer_correct).
**Approach B**: Judge each subtask's answer fragment independently against gold.

**Impact**: Makes Axis C a genuine calibration measurement. Currently C Brier≈0 is meaningless (model says "solved" = wrote text). With external judge, C can distinguish between good and bad subtask reasoning.

recommendations [[eva-hch-analysis-overview]]
