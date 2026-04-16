---
color: green
isContextNode: false
agent_name: Rex
---
# Review: metacog benchmark findings + next-step recommendation

Synthesized the TSP, jobshop, and Steiner spikes into one empirical ledger. Main result: every tested substrate still one-shots on Gemini 3.1 Pro; the primary next step should be a plan-as-state protocol experiment on coupled 6x7 jobshop before paying for a new problem class.

## Source key
- `TSP` = `voicetree-15-4/tsp-spike-runner-complete.md`
- `TSPL` = `voicetree-15-4/tsp-structural-limits-problem-class-decision.md`
- `J1` = `voicetree-15-4/jobshop-local-spike-ceiling.md`
- `J2` = `voicetree-15-4/jobshop-v2-gemini3-rerun.md`
- `J3` = `voicetree-15-4/codex-metagame-v2-coupled-jobshop-findings.md`
- `S1` = `voicetree-15-4/steiner-coloring-minimal-plan-turn-adjustment.md`
- `S2` = `voicetree-15-4/steiner-coloring-n12k4-exploratory-run.md`
- `SE` = `voicetree-15-4/steiner-coloring-n12k4-exact-solve-verdict.md`
- `SBT` = `voicetree-15-4/steiner-coloring-n12k4-bruteforce-timeouts.md`
- `LIT` = `voicetree-15-4/np-hard-instance-specific-heuristics-literature-survey.md`
- `SPEC` = `hch/metagame_spec.md`
## 1. Empirical findings table
| problem class | size | model | n_seeds | mean_gap | turn_count | A1 signal | coupling-fires | key observation |
|---|---|---|---:|---:|---|---|---|---|
| TSP-25 | 25 cities | 2.5-flash/pro, 3.1 | 27 | 8.35% overall | ~2 | pathological; 3.1 best accuracy, worst A1; A2 flat | no | Near-ceiling and arm effects are secondary to recipe recall. `[TSP][TSPL][SPEC]` |
| Flowshop v1 | `F2||Cmax`, `n=12` | 2.5-flash/pro, 3.1 | 9 | 0.00% | 2 | weak | no | Full ceiling via explicit Johnson's rule. `[J1]` |
| Jobshop v2 | `5x6` single-factory | 3.1 | 3 | 0.60% | 2 | thin | yes | Named-rule collapse disappeared, but control flow stayed one-shot. `[J2]` |
| Coupled jobshop v2 | `3x4` locked-plan | 2.5-flash/pro, 3.1 | 3 | 69.64% | 1 | none | untested | All three died in planning and fell back to baseline. `[J3]` |
| Coupled jobshop v2 | `3x4` relaxed-plan diagnostic | 2.5-pro | 1 | 3.57% | 2 | present, but 1 seed only | yes | Full schedule path works once the plan bottleneck is loosened. `[J3]` |
| Coupled jobshop v2 | `6x7` | 3.1 | 3 | 4.43% | 2 | strong, clean miscalibration | yes | Best current metacog signal: declared `100/135/120%` gap, realized `8.49/1.75/3.03%`. `[J3]` |
| Coupled jobshop v2 | `6x7` + forecast contract | 3.1 | 1 | 2.83% | 2 | improved | yes | Thresholded forecasts fixed the worst A1 pathology, but continuation value was still overconfident and behavior stayed one-shot. `[J3]` |
| Steiner x coloring | `n=8,k=3` minimal-plan | 3.1 | 1 | 0.00% | 2 | removed to unblock plan | yes | Composite coupling clearly fired: triangle avoidance cut coloring cost, then the model stopped immediately. `[S1]` |
| Steiner x coloring | `n=12,k=4` exploratory | 3.1 | 3 | NA | 2 | removed + no gold | partial | Harder but still one-shot: seed 1 improved `68->48`, seeds 2-3 did not improve baseline; exact gold is blocked. `[S2][SE][SBT]` |
## 2. Cross-cutting findings
- One-shot is universal under the current protocol: every live spike that reached execution used exactly one execution turn, then stopped; increasing difficulty changed quality, not control flow. `[J2][J3][S1][S2]`
- Problem-class upgrades mattered for capability but not for iteration: TSP and flowshop collapsed to memorized recipes, while coupled jobshop and Steiner composite removed the cheap named rule yet still did not produce multi-turn search. `[TSPL][J1][J2][J3][S1]`
- The cleanest measured metacog signal is A1 calibration, especially on coupled `6x7` jobshop; A2 is effectively dead in TSP and B mostly disappears because there is only one execution turn. `[J3][SPEC]`
- Rich planning contracts are themselves a failure mode: Steiner burned the full `300s` plan budget until turn 1 was stripped down, and the tighter coupled-jobshop spec died in planning until the budget/contract was loosened. `[S1][J3]`
- The current protocol gives the model one `NEXT_SUB` but no persistent multi-step plan-state to return to after finishing it; this is now the strongest untested mechanistic explanation for the universal one-shot pattern.
## 3. Confirmed vs hypothetical
Confirmed
- Frontier Gemini behavior on every tested substrate is `plan once, execute once, stop`. `[TSP][J1][J2][J3][S1][S2]`
- Coupled structures can force real joint reasoning and still leave optimization headroom; they just have not unlocked iteration. `[J2][J3][S1]`
- The current exact-gold path for Steiner does not scale past roughly `n=8` without a new algorithmic approach. `[SE][SBT]`
Still hypothetical
- Whether explicit plan-state plus plan revision can create genuine second-turn improvement on the same substrate.
- Whether a new class like WPMS breaks the one-shot pattern, or whether the pattern is model-level. `[LIT]`
- Whether the forecast-contract improvement on coupled `6x7` generalizes beyond one seed/model and can replace the old A1 fields. `[J3]`
## 4. Three concrete next-step options
- `A. Plan-as-state protocol experiment on coupled 6x7 jobshop.` Turn 1 emits a variable-length `PLAN`; each exec turn revises that plan, marks completed steps, updates budgets, and chooses `NEXT_SUB_ID`. This directly tests the strongest current hypothesis for one-shot behavior, and may also restore usable A1/A2 signal. Cost: `3-5h dev + 2-4h compute`; waste risk: `low`.
- `B. WPMS pilot.` Build a minimal NL-wrapped weighted partial Max-SAT spike plus a 1-turn recipe-recall check on Gemini 3, following Mia's top-ranked candidate. This tests whether a new anytime substrate with competition-backed per-instance heuristic variation breaks the one-shot pattern. Cost: `8-12h dev + 1-3h compute`; waste risk: `medium`.
- `C. Accept an A1-first benchmark.` Standardize the improved forecast contract on coupled `6x7` and score calibration plus continuation claims rather than waiting for multi-turn behavior that never arrives. This tests whether we already have a stable benchmark if we drop the iteration requirement. Cost: `2-4h analysis + 0-1h compute`; waste risk: `low`, but it abandons the original multi-turn ambition.
## 5. Recommendation
Pick `A` first, specifically the explicit plan-as-state variant rather than a generic min-turn hack. It is the most targeted explanation for the observed failure mode, it rides on top of Mei's or Nia's existing harness with about half a day of protocol work, and it could improve three things at once: control-flow richness, A1 via upfront decomposition, and A2 via differentiated per-step budgets. We already know scaling alone does not buy iteration, and Steiner scaling is blocked by exact-gold cost; a brand-new class like WPMS is worth paying for only after we know whether this protocol-state fix works on a substrate that already has clean gold, headroom, and the clearest A1 signal. If `A` still produces zero second-turn gains, I would stop expecting natural multi-turn behavior under this benchmark style and then choose between `B` and `C` explicitly.
## 6. Open questions the user should answer before committing
- Is explicit plan-state plus plan revision acceptable as benchmark behavior, or do you consider that too interventionist relative to the metacognition you want to measure?
- Should the first protocol test be `plan-as-state only`, or should we pair it with a softer forcing device like `min_exec_turns=2` for a cleaner ablation?
- If the plan-state experiment is null, do you want to pay for a new substrate (`WPMS`) or collapse scope to A1 / continuation calibration?

### NOTES

- Tried to look for a single 'winning problem class'; the evidence instead points first to protocol/state representation.
- Do not spend the next spike on larger Steiner instances before replacing the exact-gold path; evaluator cost is already the blocker at `n=12,k=4`.
- What is true now: coupled `6x7` jobshop is the best-controlled substrate for a plan-as-state test because it has clean gold, visible headroom, and the clearest A1 signal.

## Related

- [tsp-spike-runner-complete](tsp-spike-runner-complete.md)
- [tsp-structural-limits-problem-class-decision](tsp-structural-limits-problem-class-decision.md)
- [jobshop-local-spike-ceiling](jobshop-local-spike-ceiling.md)
- [jobshop-v2-gemini3-rerun](jobshop-v2-gemini3-rerun.md)
- [codex-metagame-v2-coupled-jobshop-findings](codex-metagame-v2-coupled-jobshop-findings.md)
- [steiner-coloring-minimal-plan-turn-adjustment](steiner-coloring-minimal-plan-turn-adjustment.md)
- [steiner-coloring-n12k4-exploratory-run](steiner-coloring-n12k4-exploratory-run.md)
- [steiner-coloring-n12k4-exact-solve-verdict](steiner-coloring-n12k4-exact-solve-verdict.md)
- [np-hard-instance-specific-heuristics-literature-survey](np-hard-instance-specific-heuristics-literature-survey.md)

[[task_1776319758322uan_1]]
