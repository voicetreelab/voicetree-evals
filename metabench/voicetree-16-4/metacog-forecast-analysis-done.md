---
color: green
isContextNode: false
agent_name: Anna
---
# Metacog Forecast Analysis — done (headline + findings)

Built kaggle_submission/scripts/analyze_metacog.py. 192 model-rows (64 row_ids × 3 models) parsed; 164 with ≥1 QUALITY_FORECAST, 163 with ≥1 CONTINUE_FORECAST, 1182 forecast-turns scored. Overall Quality Brier = 0.197 (Sonnet 0.097 / GPT 0.172 / Gemini 0.322). Continue-forecast is uninformative beyond base-rate; `p_improve` mean 0.11 vs. observed CF-improve 0.06.

# Metacog Forecast Analysis — overnight 64-row set × 3 models

**Headline:** Overall Quality Brier = **0.197** (0 = oracle, 0.25 = uniform random). Model spread is wide — Sonnet 0.097 / GPT 0.172 / Gemini 0.322. Continue-forecast Brier = **0.065** vs. empirical base-rate floor 0.052; all three models sit within ±0.03 of their own base-rate floor on `p_improve`, so CONTINUE_FORECAST adds ~no resolution over just quoting the base rate.

## Model-level rollup

| model | rows | quality_brier | continue_brier | base_floor | Δvs_base | mean_p_improve | observed_rate |
|---|---|---|---|---|---|---|---|
| claude-sonnet-4.6 | 64 | **0.097** | 0.040 | 0.040 | -0.000 | 0.08 | 0.04 |
| gpt-5.4-mini | 64 | 0.172 | 0.031 | 0.000 | +0.031 | 0.12 | 0.00 |
| gemini-flash-latest | 64 | 0.322 | 0.131 | 0.118 | +0.013 | 0.12 | 0.14 |

## Findings

1. **Quality forecasts beat uniform-random but mostly by staying pessimistic.** Biggest contributors to Brier are over-confident cells: Sonnet × cjs_medium (0.883 over 6 turns, predicting gap≤2 for cjs it couldn't solve); Gemini × portfolio_hard (0.548) and mwis_hard (0.362); GPT × graphcol_medium (0.492) and steiner (0.486–0.505). Conversely, many 0.000 cells are trivial — models emit 1.0 on solved runs (Sonnet graphcol) or 0.0 on clearly-failed portfolio rows.
2. **Model ordering: Sonnet ≫ GPT > Gemini on quality calibration** (0.097 / 0.172 / 0.322 overall Brier). Drift supports this: Sonnet moves toward truth 32× / away 5×; Gemini moves away 23× / toward 11×; GPT is flat on 53/64 runs — it emits the same forecast turn-after-turn.
3. **GPT-5.4-mini's `p_improve` is the clearest miscalibration.** GPT CF branches improved 0/42 times — the optimal constant predictor is 0.00 with Brier=0. GPT instead emits mean p_improve=0.12 → Brier 0.031 (all of it attributable to predicting improvement that never materialized).
4. **Portfolio's low Brier (0.166) is a trivial win, not calibration.** 97% of portfolio rows end infeasible → realized I[gap≤k]=0 everywhere; models emit correspondingly low probabilities so squared error stays small for the wrong reason. Solo-class Brier (0.223) is the honest calibration metric.
5. **`expected_delta_score` regression is weak.** MSE = 32.49 across 163 final-turn predictions vs cf_delta. Models are treating CONTINUE_FORECAST as a cursory emission — not grounded in an actual cost model for their own turn.

## Coverage

- 192 rows (64 row_ids × 3 models) analyzed from `kaggle_submission/results/full/{row_id}/{model}.json`.
- 164/192 with ≥1 QUALITY_FORECAST (85%), 163/192 with ≥1 CONTINUE_FORECAST. Sonnet missing on 16/64 rows (25%), Gemini 12/64 (19%), GPT 0/64 — Sonnet + Gemini drop forecasts when a turn errors or times out.

## Actionable follow-ups

1. **Fix VE prompting.** Every VE transcript emits `p_gap_le_2/5/10` instead of the VE-specific `p_gap_le_0_01/0_1/0_5` → strict-parse fails for all VE rows. Either update the prompt or collapse VE onto solo thresholds permanently.
2. **Store per-turn best_guess scores** so mid-run QUALITY_FORECAST can be scored against per-turn realized gap instead of only the final gap.
3. **Mine GPT's flat-forecast pattern.** 53/64 rows emit identical forecasts across all turns. Either GPT is deterministic in its calibration output regardless of new information, or the turn content isn't being integrated. Worth a diff-check over transcript turns.

## Deliverables

- Script: `kaggle_submission/scripts/analyze_metacog.py` (684 lines, stdlib-only, reuses `harness.protocol.parse_exec_turn_partial`).
- Markdown report: `kaggle_submission/results/metacog_analysis.md` (full per-class × per-difficulty tables, drift, caveats).
- CSV rollup: `kaggle_submission/results/metacog_rollup.csv`.

## Caveats

- Per-turn ground truth unavailable — mid-run forecasts scored against *final* gap only.
- Infeasible rows treated as realized=0 across all thresholds (natural reading but penalizes models that forecast non-zero probability before feasibility layer rejects the submission).
- `cf_delta` is noisy — a legitimate 0.6 p_improve can still see cf_delta≤0 on a single CF trajectory.
- Portfolio forecasts use solo-style 2/5/10 thresholds (confirmed from `cf_parsed`).
- VE rows re-scored with solo fallback because all emit solo keys.
- '206-row' headline from wake-up brief refers to artifact count; the `results/full/` set here is 192 = 64 row_ids × 3 models.

## Files Changed

- kaggle_submission/scripts/analyze_metacog.py
- kaggle_submission/results/metacog_analysis.md
- kaggle_submission/results/metacog_rollup.csv

### NOTES

- Score model: per-turn `p_gap_le_k` scored against final `final_evaluation.gap_pct` with infeasible→0. Per-turn realized gap not stored, so mid-run forecasts inherit the final-turn label.
- Continue-forecast calibrated via final-turn `p_improve` vs I[cf_delta>0]. `cf_delta` is a noisy single-sample estimate but is the only forward-looking signal we have per row.
- VE parse fix: fallback from `parse_quality_forecast(cls='ve')` → solo-style keys. All VE forecasts in the overnight set are strict-parse-invalid against the declared VE threshold schema — real prompting bug, not a tool artifact.

## Related

- [metacog_analysis](metacog_analysis.md)
- [metacog_rollup.csv](metacog_rollup.csv.md)

[[task_17763740598480xi]]
