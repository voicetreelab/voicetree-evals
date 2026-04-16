---
color: green
isContextNode: false
agent_name: Mei
---
# Codex MetaGame v2: coupled job-shop local findings

Validated the new harness and ran both locked-budget and relaxed-budget local trials. Under the spec budget, all three Gemini models timed out on the 30s planning turn and fell back to baseline. Under a one-off relaxed 90s planning budget on the same 3x4 instance, `gemini-2.5-pro` produced a feasible full schedule with makespan 58 versus optimum 56 (3.57% gap), proving that the coupled schedule-output path itself works once the model reaches it.

## Locked-budget runs
`smoke_20260416_seed1.jsonl`
- `gemini-2.5-pro`, `3x4`, seed 1
- `stop_reason=turn1_died`
- `turn_count=1`
- `final_schedule_source=baseline`
- `gap_pct=69.64285714285714`

`subset_20260416_3models_seed1_3x4.jsonl`
- `gemini-2.5-pro`: `turn1_died`, baseline fallback, `gap_pct=69.64285714285714`
- `gemini-2.5-flash`: `turn1_died`, baseline fallback, `gap_pct=69.64285714285714`
- `gemini-3.1-pro-preview`: `turn1_died`, baseline fallback, `gap_pct=69.64285714285714`

All three models timed out on the exact same 30s planning turn and returned no parseable plan text.

## Relaxed-budget diagnostic
`diagnostic_relaxed_plan_20260416_seed1_3x4.jsonl`
- one-off diagnostic with `PLAN_TURN_BUDGET_S=90`, `TOTAL_BUDGET_S=420`
- `gemini-2.5-pro`
- `stop_reason=subtask_stop`
- `turn_count=2`
- `final_schedule_source=model`
- `declared_gap=0.36`
- `atomic_p_correct=0.9`
- `final_makespan=58`
- `optimal_makespan=56`
- `gap_pct=3.5714285714285716`

Observed turn trace:
- turn 1 parsed successfully and chose `DECISION: continue`
- turn 2 emitted a full feasible `BEST_GUESS` schedule and then `DECISION: stop`

## Size calibration
Offline exact-solve checks:
- `4x5` seed 1: baseline 132, optimal 72, gap `83.33%`, solve wall `0.04s`
- `4x5` seed 2: baseline 153, optimal 93, gap `64.52%`, solve wall `0.01s`
- `4x5` seed 3: baseline 132, optimal 71, gap `85.92%`, solve wall `0.01s`
- `5x6` seed 1: baseline 155, optimal 90, gap `72.22%`, solve wall `0.01s`
- `5x6` seed 2: baseline 192, optimal 90, gap `113.33%`, solve wall `0.01s`
- `5x6` seed 3: baseline 170, optimal 85, gap `100.0%`, solve wall `0.01s`
- `6x7` seed 1 with `min_baseline_gap_pct=10`: baseline 216, optimal 106, gap `103.77%`, build wall `0.04s`

## Live 6x7 run: Gemini 3 only
`gemini31_6x7_20260416_run.jsonl`
- model: `gemini-3.1-pro-preview`
- seeds: `1 2 3`
- size: `6x7`
- budgets: `TOTAL=1800`, `SUBTASK=600`, `PLAN=300`

Per-seed outcomes:
- seed 1: `subtask_stop`, `turn_count=2`, model schedule kept, final makespan `115` vs optimum `106`, gap `8.49%`, wall `182.63s`
- seed 2: `subtask_stop`, `turn_count=2`, model schedule kept, final makespan `116` vs optimum `114`, gap `1.75%`, wall `223.79s`
- seed 3: `subtask_stop`, `turn_count=2`, model schedule kept, final makespan `102` vs optimum `99`, gap `3.03%`, wall `228.51s`

Grouped summary:
- mean gap `4.43%`
- mean wall `211.64s`
- mean score `93.46`
- mean Brier `13270.09`
- mean turns `2.00`
- mean execution subtasks used `1.00`
- `turn1_died=0`, `killed=0`, `infeasible=0`, `errors=0`

Behavioral read:
- The restored 5-minute planning budget removed the earlier turn-1 timeout failure mode entirely.
- This was **not saturated** in the Meg / Johnson-rule sense: none of the three seeds hit `0%` gap.
- However, it is still not showing rich multi-turn metacognition yet: all three runs chose `continue` once, emitted one full schedule, then immediately `stop`ped on turn 2.
- Self-calibration remained very poor despite strong optimization performance: declared gaps were `100%`, `135%`, and `120%`, while realized gaps were `8.49%`, `1.75%`, and `3.03%`; `atomic_p_correct` was `0.0` on all three seeds.
- The stop behavior looks more like heuristic satisficing than explicit economic stopping. In the raw turn text, Gemini 3 simply says it constructed an improved or optimized schedule and then stops; it does not articulate a counterfactual marginal-value argument about why another subtask is no longer worth the time.

## New forecast-contract rerun
`gemini31_6x7_newforecast_seed1_20260416.jsonl`
- model: `gemini-3.1-pro-preview`
- seed: `1`
- size: `6x7`
- same larger budgets, but with the updated output contract:
  - `ATOMIC_FORECAST {p_gap_le_2, p_gap_le_5, p_gap_le_10}`
  - `CONTINUE_FORECAST {p_improve_if_one_more_subtask, expected_gap_reduction, expected_delta_score}`
  - execution-turn `QUALITY_FORECAST` with the same thresholded gap structure

Outcome:
- `stop_reason=subtask_stop`
- `turn_count=2`
- `final_schedule_source=model`
- `final_makespan=109` vs `optimal_makespan=106`
- `gap_pct=2.83%`
- `score=94.62`
- atomic forecast Brier `0.405`
- plan-continue Brier `0.0025`
- plan expected-delta-score error `54.76`

Forecast read:
- Turn 1 atomic forecast was sensible and much more informative than the old exact-correctness claim:
  - `p_gap_le_2=0.05`
  - `p_gap_le_5=0.15`
  - `p_gap_le_10=0.30`
- Turn 1 continuation forecast strongly favored one more subtask:
  - `p_improve_if_one_more_subtask=0.95`
  - `expected_gap_reduction=50.0`
  - `expected_delta_score=40.0`
- Turn 2 quality forecast tracked reality reasonably well:
  - `p_gap_le_2=0.85`
  - `p_gap_le_5=0.95`
  - `p_gap_le_10=0.99`
  - realized gap was `2.83%`
- The new contract fixed the worst pathology from the old one: instead of `atomic_p_correct=0.0` plus absurd `declared_gap` values, the model now produced coherent thresholded distance-to-optimal beliefs.
- However, the continuation-value estimate is still badly overconfident in magnitude: the direction was correct (continuing was worth it), but `expected_delta_score=40.0` undershot the realized delta score of about `94.76` by a large margin. So calibration is improved, but still incomplete.

## Interpretation
- Meg's simpler flowshop ceiling does not transfer to this richer coupled multi-machine variant.
- The current failure mode under the locked protocol is not schedule parsing or verifier brittleness; it is the 30s planning-turn budget.
- Once the plan budget is relaxed, the model can emit a valid full machine-by-machine schedule and get near-optimal on `3x4`.
- If the benchmark remains wall-clock-rationed, the main design choice is whether to keep that harsh 30s planning bottleneck as part of the benchmark signal or loosen it to expose later-turn metacognition.

## Saturation answer
- **Meg's simpler Johnson-style flowshop spike:** yes, saturated. All 9 rows reached `0%` gap because the model could name and apply the exact known algorithm.
- **This full coupled multi-machine v2 spike:** no evidence of saturation yet. The locked-budget runs did not hit an optimality ceiling; they timed out on the 30s planning turn and fell back to the baseline.
- The one relaxed-budget diagnostic is the key counterexample to saturation: `gemini-2.5-pro` on `3x4` reached a feasible model-produced schedule at makespan `58` vs optimum `56`, so the problem is still hard enough to leave real headroom.
- For larger sampled sizes, offline gold remained easy to compute but baseline headroom stayed large (`4x5` gaps roughly `64%` to `86%`, `5x6` gaps roughly `72%` to `113%`), which is the opposite of a saturation signature.

## Why 5x6 solves quickly
- In the full coupled v2 code, `5x6` means only `2 * 5 * 6 = 60` timed operations total: each of 5 jobs visits each of 6 machines once in Factory A and once in Factory B.
- The exact gold path is a clean CP-SAT job-shop model with precedence chains, `NoOverlap` per machine, and one cross-factory release constraint per job. That is still a small optimization instance for OR-Tools, so fast exact solving is expected and is actually desirable for benchmark packaging.
- Fast exact solving by OR-Tools is **not** the saturation criterion. The benchmark only fails if frontier models also solve it optimally or near-optimally with little metacognitive variation.
- The other `jobshop_spike_v2` branch is easier still: it is single-factory and asks for per-machine priority lists rather than a full timed schedule. That branch should not be used as evidence that the full coupled full-schedule v2 is easy.

## Recommended next lever
- Do **not** jump straight to `10x10` as the first move. With full schedule output, that would force the model to emit roughly 200 timed operations and risks turning the benchmark into output-volume/parsing stress instead of metacognition.
- First restore a realistic planning budget (`PLAN_TURN_BUDGET_S = 300`) and run the intended coupled variant at `5x6` for Gemini 3.
- If that still saturates, then move one notch at a time: `6x6`, `6x7`, or keep `5x6` but strengthen instance selection so naive A-then-B decomposition is more misleading.
- If more difficulty is needed, prefer **structural hardness** over raw size: stronger cross-factory bottlenecks, instance prefiltering for large baseline gaps, and adversarial release-time interactions are better next levers than immediately scaling to `10x10`.

## Updated config decision
- The runner and protocol have now been updated to the larger benchmark-style budget trio: `TOTAL_BUDGET_S = 1800`, `SUBTASK_BUDGET_S = 600`, `PLAN_TURN_BUDGET_S = 300`.
- The main default spike size has now been updated from `4x5` to `6x7`, while keeping the `3x4` smoke preset.
- Based on the local `6x7` build check, this size is still easy for OR-Tools gold generation and still leaves a very large baseline gap, so it is a reasonable next live run target.
- After the live Gemini-3-only run, `6x7` now looks like a meaningful but still somewhat shallow tier: strong optimization signal, no timeout pathology, but still only one execution turn and badly miscalibrated self-prediction.

## Budget-history clarification
- Earlier local-spike iterations did use a 5-minute planning turn: `PLAN_TURN_BUDGET_S = 300` appears in `hch/metagame_spec.md` and in the earlier `hch/metagame/jobshop_spike/protocol.py`.
- The current `hch/codex_metagame_v2/EXPERIMENT_SPEC.md` working contract explicitly changed that back to `PLAN_TURN_BUDGET_S = 30`, alongside `TOTAL_BUDGET_S = 360` and `SUBTASK_BUDGET_S = 120`.
- I initially followed that tighter v2 spec, then updated `hch/codex_metagame_v2/protocol.py` back to the larger budget trio after the follow-up request to restore a 5-minute planning turn.

## Prompt-shape clarification
- Yes, the current coupled v2 problems are already rendered in natural language. The prompt starts with a manufacturing cover story and describes jobs, machines, and constraints in prose before asking for a full timed schedule.
- No, there is not yet a separate distraction-context layer. The prompt has light narrative wrapping, but it does not currently inject extra irrelevant business details, side constraints that wash out, or attention-decoy text.

## Prediction-contract recommendation
- The current prediction fields are not well matched to optimization tasks. `p_correct_if_atomic` collapses toward `0.0` because exact correctness is too brittle, while a single `DECLARED_GAP` point estimate loses the uncertainty structure that we actually care about.
- The better target is not a single “probability of being correct,” but a small set of **decision-relevant calibrated claims**:
  - a distribution over final quality if answered now
  - a counterfactual estimate of improvement if given one more subtask
  - an explicit expected-value claim about whether continuing is worth the time cost
- For quality calibration, prefer thresholded probabilities or bins over a single scalar. Example: `P_GAP_LE_2`, `P_GAP_LE_5`, `P_GAP_LE_10`, or a binned distribution over gap ranges. These are easier to score and more informative than “probability exactly optimal.”
- For decomposition, ask directly whether another subtask is expected to help. Example: `P_IMPROVE_IF_ONE_MORE_SUBTASK`, `EXPECTED_GAP_REDUCTION`, or `EXPECTED_DELTA_SCORE_IF_CONTINUE`.
- For stopping, tie the claim to the benchmark objective. Example: `EXPECTED_DELTA_SCORE_IF_CONTINUE` plus `DECISION`, so the evaluation can compare the stated marginal value against realized marginal value.
- In short: keep some notion of distance-to-optimal, but make it probabilistic and thresholded; add a separate counterfactual prediction about whether decomposition / continuation is worth it. Those are different metacognitive judgments and should not be collapsed into one field.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/hch/coupled56-metagame_gemini3_results.md
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/results/smoke_20260416_seed1.jsonl
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/results/smoke_20260416_seed1_v2prompt.jsonl
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/results/subset_20260416_3models_seed1_3x4.jsonl
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/results/diagnostic_relaxed_plan_20260416_seed1_3x4.jsonl
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/results/gemini31_6x7_20260416_run.jsonl
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/results/gemini31_6x7_newforecast_seed1_20260416.jsonl

### NOTES

- Under the old tight config, the protocol spent the entire 30s plan budget before any schedule was emitted.
- A trivial control prompt to `gemini-2.5-flash` returned in ~1.4s, so the timeout is specific to this planning task, not a broken Gemini client.
- Sampled `4x5`, `5x6`, and `6x7` instances all have very large baseline gaps, so making the class harder is optional calibration work rather than a correctness fix.
- Exported a concise human-readable results summary to `hch/coupled56-metagame_gemini3_results.md` for direct reuse outside the Voicetree graph.

validated by [[codex-metagame-v2-coupled-jobshop-implementation]]
