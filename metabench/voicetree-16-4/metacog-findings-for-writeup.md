---
color: green
isContextNode: false
agent_name: Anna
---
# Metacog findings & analysis threads for writeup (Anna)

Overnight 192-row metacog analysis produced 10 findings, several of which diverge from writeup-v2's predictions. Headline: capability ↔ metacog dissociate (pre-registered ✓), but sign-agreement, CF-$ direction, and Murphy-BSS clipping need re-framing before the writeup can cite overnight numbers.

# Metacog overnight pilot — findings + open analysis threads

## The 10 findings worth putting in the writeup

1. **Pareto dissociation of capability and metacog (pre-registered prediction ✓).** None of the 3 models strictly dominates: Sonnet wins composite metacog (0.37, ↓ better) but has worst feasibility (30%); GPT wins feasibility (52%) and has perfect M3 (0/64 wrong) but near-zero M2 resolution; Gemini is Pareto-dominated by GPT on both axes.

2. **M1 resolution preserves writeup finding 7 in its original direction.** GPT has *highest* M1 resolution (0.121 > Sonnet 0.101 > Gemini 0.022). Re-grounding finding 7 on M2 would *invert* the claim (GPT M2 res = 0.002). So the "resolution reveals what Brier hides" story lives specifically on M1.

3. **Composite Brier Skill Score clips to 0 for two of three models on both M1 and M2.** Raw BSS: Gemini M1 −1.11, GPT M1 −0.25, Gemini M2 −0.38, GPT M2 −2.11. Clipping hides the meaningful distinction between "flat forecast" (Gemini) and "sharp + miscalibrated" (GPT). **Report Reliability + Resolution separately in the writeup** (or use Refinement = Res/(Res+Rel)), not BSS alone.

4. **Sign agreement 24–39% (not 93–98% as in writeup).** Models overwhelmingly emit `decision=stop` WITH `expected_delta_score > 0` (Sonnet 70/80 stops, Gemini 53/59, GPT 113/126). This is **pricing bias, not arithmetic error** — confirmed by the logistic thresholds at +2.30 / +3.60 / +4.79, all deeply risk-averse.

5. **CF-$ direction is flipped vs. writeup.** Our mean cf_delta is *negative* across all 3 models (Sonnet −0.26, Gemini −1.64, GPT −1.31). Writeup expected positive (Gemini +3.14). Likely cause: short overnight runs (mean 1.3 exec turns) leave little slack for a forced-continue turn to recover. **The writeup's "models stop too early" frame may invert on the full-budget sweep** — needs re-check when 30-min runs land.

6. **GPT Continue AUC is DEGEN** because 0/64 CF-branches improved. No positive class to rank. Consistent with GPT's clean-stop-rate = 100% and M3 fraction-wrong = 0: GPT stops when it truly can't improve further, but does so overconfidently per its own emit (mean p_improve = 0.12).

7. **Sonnet's weakness is execution, not judgment** (writeup finding 3 ✓). Metacog composite leader but feasibility drops to 0% on mwis_hard, 17% on cjs_medium, 17% on ve_hard. M2 forecasts are good; the *artifact* breaks.

8. **Gemini drifts AWAY from truth** (11 toward, 23 away, 13 flat across 47 multi-turn rows). Sonnet is the opposite (32 toward, 5 away). GPT is flat (53/64). Drift coherence is a real discriminator.

9. **VE protocol bug:** all 18 VE transcripts emit solo-style keys (`p_gap_le_{2,5,10}`) instead of VE-specific (`p_gap_le_{0_01,0_1,0_5}`). Strict parse fails 100% on VE. Either collapse VE to solo thresholds or rework the prompt.

10. **Portfolio M1 remains unmeasured.** Ben skipped portfolio M1 because per-sub-component verifier routing wasn't implemented. Blocked on Amit's portfolio-infeasibility fix (0/36 medium, 1/36 hard feasible).

## Most promising analysis threads to continue

### A. Per-class Brier breakdown (high-value, low-cost)
Current M1/M2 numbers are model-level. Breaking them down by class would reveal **where** each model's self-model fails. Hypothesis: Sonnet's M1 resolution is class-dependent — high on graphcol/steiner (where it succeeds) and low on mwis/cjs (where it fails feasibility). This would link M1 self-knowledge to downstream execution, which strengthens the pitch.

### B. Cross-model per-row forecast comparison (high-value, medium-cost)
Pick the ~15 rows where exactly 2 of 3 models succeed. For each, compare forecasts at the subtask level: did the failing model emit lower p_solve / lower p_gap_le_2 / higher p_improve-then-give-up? If forecasts *predict* the feasibility split, that's a strong story. If they don't, the models' self-model is blind to the very executions they're about to fail.

### C. Correlation of p_solve with kept_as_best probability per p_solve bin (high-value, medium-cost)
Current M1 Brier aggregates. A calibration plot (expected vs. observed frequency per 0.1-wide p_solve bin) makes Murphy reliability/resolution *visible* in one image and lands directly into the writeup. Ben computed the ingredients; this is ~50 lines.

### D. M5 score-trajectory AUC (medium-value, medium-cost)
Ben's `_extract_subtasks` infrastructure already scores every turn's best_guess. Trivially extend to emit per-turn `gap_pct` sequences → compute AUC / ceiling for each row. One of the six skills from writeup. **This is the cheapest missing piece in the writeup framework.**

### E. Logistic threshold vs. base-rate check (medium-value, low-cost)
The logistic thresholds (+2.3 / +3.6 / +4.8) all say "risk-averse", but the CF-$ data says the models' stops are EMPIRICALLY CORRECT (mean cf_delta < 0 everywhere). These two are in tension — models are "risk-averse" by their own declared arithmetic but "empirically well-calibrated" by realized outcomes. Resolve: is `expected_delta_score` systematically upward-biased by a constant (e.g., +2)? If so, subtracting the bias would close the gap. Easy to check.

### F. Refactor writeup's Penalty-Comprehension Audit using our numbers (low-cost, writeup-direct)
The audit section in writeup-v2 §M3 robustness cites sign-agreement 93–98% and threshold range [−0.1, +1.7]. Our overnight numbers are 24–39% and [+2.3, +4.8]. The *methodology* is identical; the *numbers* differ. A careful pass through the writeup paragraph to either flag "overnight vs. full-sweep" difference or replace with overnight numbers would be high-signal for the reviewer.

## What NOT to chase

- Computing M6 without portfolio feasibility. 0/36 feasibility means every model scores 0, leaving no signal. Wait for Amit.
- Adding more normalization / composite variants. We already showed the composite hides detail (finding 3). The honest answer is to stop hiding.
- Sign-agreement beyond the logistic fit. We have the data; the insight is in the magnitude mismatch with writeup, not in more fits.

## Where the numbers live

- Script: `kaggle_submission/scripts/analyze_metacog.py` (1030 lines, includes M1+M2 Brier + Murphy + M3 CF-$ + M4 MAE + audit + AUC + BSS + drift + feasibility per class)
- Report: `kaggle_submission/results/metacog_analysis.md`
- CSV: `kaggle_submission/results/metacog_rollup.csv`
- Upstream prior nodes: `metacog-forecast-analysis-done`, `m1-brier-landed`
- Writeup to update: `kaggle_submission/writeup-v2.md` (specifically §Findings 1–7, §Penalty Comprehension Audit, §Metacognitive profile table)

### NOTES

- BSS clipping is a scoring choice, not a data limitation. Reporting Reliability + Resolution as two axes (like Murphy's original paper does) preserves the GPT "sharp but miscalibrated" vs. Gemini "flat and wrong" distinction that the composite throws away.
- CF-$ direction flip is the single biggest divergence from writeup-v2. Worth flagging in the writeup as a known-scale-dependent result: the direction may recover on full 30-min runs where there's more slack for forced-continue to exploit.
- The sign-agreement story reframes the Penalty-Comprehension Audit: models here aren't failing arithmetic, they're emitting optimistically-biased `expected_delta_score` that their decision layer correctly dismisses.

[[task_17763740598480xi]]
