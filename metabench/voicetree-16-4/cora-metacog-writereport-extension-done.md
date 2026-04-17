---
color: green
isContextNode: false
agent_name: Eli
---
# Cora — §8/§9/§10 landed + writeup-v2 overnight patches drafted

Pasted Carla's write_report extension into analyze_metacog.py; §8 (6 ASCII calibration plots), §9 (per-class Brier), §10 (pricing-bias reconciliation) now render. metacog_calibration_bins.csv emitted (60 rows). §3 raw-BSS verified: Sonnet +0.21/+0.53, Gemini -1.11/-0.38, GPT -0.25/-2.12. Patches A/B/C drafted to writeup-v2-overnight-patches.md.

# Cora — §8/§9/§10 landed + writeup-v2 overnight patches drafted

## 4 MUSTs landed

- **MUST 1 ✓** — §8/§9/§10 write_report extension pasted verbatim into `kaggle_submission/scripts/analyze_metacog.py` between the §7 caveats and the `Script:` footer.
- **MUST 2 ✓** — §3 profile table raw-BSS + Refinement rows already present from Carla's earlier pass (fields `m1_bss`, `m1_refinement`, `m2_bss`, `m2_refinement` computed unclipped in `model_level_stats`; `_row` calls at lines 1117/1118/1125/1126). Verified magnitudes on re-render: Sonnet +0.211/+0.525, Gemini −1.112/−0.377, GPT −0.251/−2.122 on M1/M2 (within rounding of Carla's expected +0.21 / −1.09 / −0.36 / +0.53 / −0.25 / −2.13). Existing `_row` labels retained; no rows deleted.
- **MUST 3 ✓** — Re-ran `python3 kaggle_submission/scripts/analyze_metacog.py`. metacog_analysis.md now has §8 (6 reliability diagrams), §9 (21-row per-class Brier), §10 (pricing-bias). `results/metacog_calibration_bins.csv` exists, 61 lines = 60 rows + header.
- **MUST 4 ✓** — `kaggle_submission/writeup-v2-overnight-patches.md` created with BEFORE/AFTER blocks for:
  - Patch A: §Metacognitive profile table → 3-model overnight table, raw BSS + Refinement, Sonnet-only-positive headline in caption.
  - Patch B: Findings 1 (CF-$ flip flagged as budget-dependent), 3 (Sonnet exec-not-judgment CONFIRMED; 30%/0% mwis/17% cjs feasibility), 7 (resolution M1↔M2 flip reframed).
  - Patch C: Penalty Comprehension Audit reconciled via §10 pricing-bias math; audit role preserved, magnitude reading shifts from 'risk-averse pricing' to 'emission-inflation bias'.

## Link to patches draft

[writeup-v2-overnight-patches.md](../kaggle_submission/writeup-v2-overnight-patches.md) — BEFORE/AFTER for Patch A (profile table), Patch B (findings 1/3/7), Patch C (penalty audit).

## Ranked strongest→weakest writeup findings (overnight numbers)

1. **STRONGEST — Sonnet monopoly on positive BSS.** Only Sonnet raw BSS > 0 on M1 + M2 (+0.21 / +0.53); Gemini M1 −1.11 (flat), GPT M2 −2.12 (sharp-wrong). Un-clipping reveals two distinct failure modes the clipped-0 framing erased. 2. **Pareto dissociation of capability × metacog (pre-registered ✓).** Sonnet wins metacog; GPT wins feasibility 52% + clean-stop 100%; Gemini Pareto-dominated. 3. **Sonnet execution-not-judgment CONFIRMED.** 30% feasibility, 0% mwis, 17% cjs, yet best metacog. 4. **Resolution is metric-dependent (M1↔M2 flip within GPT).** M1 res 0.121 vs M2 res 0.002. 5. **Sign-agreement 24–39% + logistic +2.3/+3.6/+4.8 reconcile via pricing bias +0.76/+2.53/+1.94 ≈ thresholds** — penalty audit closes arithmetic-confound critique; magnitude reading shifts to emission inflation. 6. **WEAKEST (budget-dependent) — CF-$ direction flip.** Mean cf_Δ negative for all three overnight models, but mean exec turns only 1.3. Needs full-budget re-check before finding-1 rewrite locks in.

See child nodes for the embedded §8 / §9 / §10 artifacts.

## Complexity: medium

Pure append — no restructuring of existing compute paths. Carla's helper functions were already wired; this was 140 lines of report-rendering + CSV emission composing existing pair collectors, Murphy decomposition, and calibration binning. Subtle dependency: `csv`, `ROOT`, `MODELS` already in scope at insertion point (verified imports). Cross-check vs Carla's expected magnitudes ±0.01.

## Files Changed

- kaggle_submission/scripts/analyze_metacog.py
- kaggle_submission/writeup-v2-overnight-patches.md
- kaggle_submission/results/metacog_analysis.md
- kaggle_submission/results/metacog_calibration_bins.csv

### NOTES

- MUST 2 (raw-BSS + Refinement rows) was already landed by Carla — verified numbers match expectations before moving on.
- One surface bug noted but OUT OF SCOPE: §4 header appears twice in metacog_analysis.md (line 148 '## 4. Model-level rollup (raw)' and line 156 '## 4. Forecast drift...'). Pre-existing, not introduced by this pass.
- Depth budget 0 respected. No sub-agents. Post-hoc analysis only — no LLM calls, no harness runs, no commits.

[[task_17763772282376sh]]
