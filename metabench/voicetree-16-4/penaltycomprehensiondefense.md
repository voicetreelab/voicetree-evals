---
color: blue
isContextNode: false
agent_name: Amy
---
# Bulletproofing M5: Penalty Comprehension Defense

Three-layer response to judge feedback: prove models understand 0.01$/sec penalty so M5 (CF-$) can't be dismissed as arithmetic-comprehension failure. L1 internal-consistency audit (free), L2 arithmetic probe appendix ($5), L3 optional worked-example ablation. Plus M1-M10 numbering fix.

# Bulletproofing M5 Against “Arithmetic Confound” Critique

## Judge feedback
Weighted score **96.3/100**, grand-prize track. Single highest-leverage pre-deadline improvement:
> Prove that models understand the economic scoring penalty (0.01 × wall_seconds). A skeptic could argue: “Gemini didn’t stop early because of poor metacognition; it stopped early because it failed to grasp the reward/cost ratio.” Also fix the M1–M10 numbering jump.

## Threat model
If the model can’t do `reward = gap_reduction`, `cost = 0.01 × extra_wall`, `continue iff reward > cost`, then every stop decision is attributable to arithmetic failure, not stop-rationality. M5 (CF-$) collapses as a metacog metric under that framing.

## Three-layer defense (cheapest first)

### L1 — Internal consistency audit (zero extra runs)
`CONTINUE_FORECAST.expected_delta_score` is literally the model’s own arithmetic output. From existing transcripts:
- **Sign-agreement rate:** `sign(expected_delta_score)` vs `DECISION ∈ {continue, stop}`. ≥95% agreement → decisions follow the model’s own math; arithmetic is not the confound.
- **Stop-threshold fit:** logistic fit of P(stop) against `expected_delta_score`. Rational agent crosses 0.5 at 0. Any skew is a **pricing bias** to *report* — not a metacog failure. e.g. “Gemini stops at threshold +2.3, indicating risk-aversion in $ forecasting, but stops follow internal math.”
- **Output:** one table, one paragraph in paper body. Kills ≈80% of the critique for free.

### L2 — Arithmetic probe appendix (≈$5, 90 calls)
One-shot, independent of main run. 30 probes × 3 models:
- *“Elapsed 847s, gap 7%. Expect 200s to reduce gap to 4%. Net score change?”* gold = `+3 − 2.0 = +1.0`
- *“Minimum gap reduction for 400s to be worth it?”* gold = `4 pp`
- *“At what `expected_delta_score` should you stop?”* gold = `0`
- *“You’ve used 1600s / 1800s. Remaining budget in points?”* gold = `2.0`
- Mix trivial, moderate, trap variants (e.g. score already at 0 floor).

Report pass rate. >95% → “penalty comprehension established as background fact” → M5 stands. Ship as 1-page appendix titled **“Penalty Comprehension Probe.”**

### L3 — Worked-example ablation (optional, defense-in-depth)
Re-run a 60-question subset with one extra line added to system prompt:
> *Example: 200s of wall time costs 2.0 points; only worth spending if you expect >2 pp of gap closure.*

Two outcomes, both good:
- **No behavior shift** → original prompt was already understood; M5 fully bulletproofed.
- **Behavior shifts** → publish the sensitivity honestly. M5 still stands but is now conditional on framing, which is a cleaner scientific claim.

## Recommended pre-deadline package
| Layer | Action | Cost | Where |
|---|---|---|---|
| L1 | Sign-agreement + threshold fit | 0 | Paper body, headline table |
| L2 | 90 arithmetic probes | ≈$5, <1h | Appendix A |
| L3 | Worked-example ablation | 60 runs | Only if time permits |

## M1–M10 numbering fix
Current table jumps M1/M4/M5/M6/M7/M10 — M2/M3/M8/M9 were scoped out during planning.
- **Renumber contiguously M1–M6** in the final paper.
- **Footnote** with old→new mapping for reviewers who saw earlier drafts.
- Update all internal refs in `experiment-theory.md`, `experiment-spec.md`, analyzer code, and CF-pass tables.

## PREDICTION CLAIMS
- **Claim:** L1 sign-agreement will exceed 95% across all three models. *Falsifiable by:* running the audit on existing Phase-1+CF transcripts.
- **Claim:** L2 probe pass rate will exceed 95% for Gemini 3 Pro, GPT-5, Claude; if any model fails <90%, M5 for that model needs an asterisk. *Falsifiable by:* 90-call probe run.
- **Claim:** L3 ablation will show <10% shift in stop rate — i.e. worked example won’t change behavior because arithmetic was already understood. *Falsifiable by:* 60-question A/B.
- **Claim:** M1–M6 contiguous renumbering is safe — no downstream analyzer code depends on the literal integer "M10". *Falsifiable by:* grep `\bM1[0-9]?\b` across repo.

### NOTES

- If L1 sign-agreement comes in <90%, the critique is real and the paper needs a more careful framing of M5 — not 'stop-rationality' but 'math-compliant stopping.'
- L2 probes must include at least one trap where score is already floored at 0 (further work is literally impossible to net positive) — that's the cleanest discriminator between models.
- Numbering fix is a pure paper-doc change but touches analyzer code that reads metric names from config; audit before renaming.

## Related

- [experiment-spec](experiment-spec.md)
- [experiment-theory](experiment-theory.md)
- [llmpromptflowanswer](llmpromptflowanswer.md)

[[experiment-spec_1]]
