# Portfolio Spike — Pilot Note (2026-04-16)

## Configuration

- Problem family: 4-problem portfolio metagame with plan-as-state and thresholded per-problem forecasts.
- Problems:
  - `P1`: coupled jobshop `5x6`, `value_cap=50`
  - `P2`: Steiner x coloring `N=8, K=4`, `value_cap=60`
  - `P3`: Euclidean `TSP-20`, `value_cap=20`
  - `P4`: slack graph coloring `30 nodes`, `value_cap=100`
- Seed: `1`
- Budgets: `TOTAL_BUDGET_S=1800`, `SUBTASK_BUDGET_S=600`, `PLAN_TURN_BUDGET_S=300`
- Economic objective: `sum(value_cap_i * headroom_fraction_i) - 0.05 * wall_s_total`
- Live Kaggle access:
  - Working form: root host URL with query token, passed via `--notebook-url`
  - Failing form: `.env` proxied `/k/{run}/{jwt}/proxy` URL, which returned `/api/sessions` `404`

## Result Artifacts

- Gemini 3.1 Pro:
  - `kaggle/results/portfolio_pilot_google_gemini-3_1-pro-preview_seed1_20260416_112855.jsonl`
- Claude Sonnet 4.6 (retry after harness fix — **canonical**):
  - `kaggle/results/portfolio_pilot_anthropic_claude-sonnet-4-6_seed1_20260416_retry.jsonl`
- GPT-5.4:
  - `kaggle/results/portfolio_pilot_openai_gpt-5_4_seed1_20260416_120142.jsonl`
- Claude Sonnet 4.6 (original — non-canonical harness-gate failure, retained for traceability):
  - `kaggle/results/portfolio_pilot_anthropic_claude-sonnet-4-6_seed1_20260416_114146.jsonl`

## Per-Model Summary

| model | P1 headroom | P2 headroom | P3 headroom | P4 headroom | exec subtasks | stop_reason | net_score | wall_s | declared_axis_p1 |
|---|---:|---:|---:|---:|---:|---|---:|---:|---|
| Gemini 3.1 Pro | 0.00 | 1.00 | 0.00 | 1.00 | 2 | `subtask_timeout` | 129.48 | 610.49 | — |
| Claude Sonnet 4.6 (retry, canonical) | 0.00 | 1.00 | 0.67 | 0.00 | 4 | `subtask_timeout` | 56.11 | 346.59 | — |
| GPT-5.4 | 0.00 | 1.00 | 0.40 | 0.00 | 8 | `max_exec_turns` | 59.62 | 167.24 | `bottleneck-first` |

## Per-Problem Final Rows

### Gemini 3.1 Pro

| problem | baseline | gold | final | headroom_fraction_captured | value_captured | realized_bucket |
|---|---:|---:|---:|---:|---:|---|
| P1 | 155.0 | 90.0 | 155.0 | 0.00 | 0.0 | `miss` |
| P2 | 72.0 | 59.0 | 59.0 | 1.00 | 60.0 | `within_5pct` |
| P3 | 588.2207 | 470.1463 | 588.2207 | 0.00 | 0.0 | `within_50pct` |
| P4 | 20.0 | 4.0 | 4.0 | 1.00 | 100.0 | `within_5pct` |

### Claude Sonnet 4.6 (retry — canonical, harness fix applied)

| problem | baseline | gold | final | headroom_fraction_captured | value_captured | realized_bucket |
|---|---:|---:|---:|---:|---:|---|
| P1 | 155.0 | 90.0 | 155.0 | 0.00 | 0.0 | `miss` (P1 subtask timed out) |
| P2 | 72.0 | 59.0 | 59.0 | 1.00 | 60.0 | `within_5pct` (OPTIMAL) |
| P3 | 588.2207 | 470.1463 | 508.9051 | 0.67 | 13.43 | `within_10pct` |
| P4 | 20.0 | 4.0 | 20.0 | 0.00 | 0.0 | `miss` |

### GPT-5.4

| problem | baseline | gold | final | headroom_fraction_captured | value_captured | realized_bucket |
|---|---:|---:|---:|---:|---:|---|
| P1 | 155.0 | 90.0 | 155.0 | 0.00 | 0.0 | `miss` |
| P2 | 72.0 | 59.0 | 59.0 | 1.00 | 60.0 | `within_5pct` (OPTIMAL) |
| P3 | 588.2207 | 470.1463 | 541.1092 | 0.40 | 7.98 | `within_20pct` |
| P4 | 20.0 | 4.0 | 20.0 | 0.00 | 0.0 | `miss` |

## GPT-5.4 Validation Checklist

1. Dual parser accepted the live run: `parse_fail=false`, `turn_count=9`, no malformed turn triggered the hard stop.
2. Hard-kill path was not needed: `subtask_killed_count=0`, stop came from `max_exec_turns`, not timeout or SSL hang.
3. Pre-flight remained clean on the embedded seed-1 portfolio: same portfolio/task build, no regeneration drift surfaced during the live run.
4. Thresholded Brier is populated for all four problems in `thresholded_brier_by_problem`, because GPT touched `P1-P4`.
5. Final JSONL row includes the expected pilot fields: `stop_reason`, `economic_net_score`, `wall_s`, `declared_axis_p1`, `plan_evolution`, per-problem summaries, forecast histories, and Brier outputs.

## Cross-Model Comparison (final)

- All three frontier models exhibited real portfolio behavior rather than a single-shot answer dump.
- Gemini executed `2` subtasks total and solved `P2` and `P4` exactly before timing out. That remains the net-score winner at `129.48`, because `P4` carries `value_cap=100`.
- Sonnet (retry, canonical) completed `4` subtasks, handled non-sequential plan traversal cleanly after the harness fix, solved `P2` exactly, and improved `P3` to within 10% before a timed-out `P1` attempt.
- GPT-5.4 completed `8` subtasks across all four problems, expanded the plan from `6` to `17` items, solved `P2` exactly, improved `P3` to within 20%, and reached `max_exec_turns` without needing the hard-kill path.
- Multi-subtask execution is therefore confirmed for both Sonnet and GPT, not just Gemini.
- GPT is the only model that explicitly named a `P1` decomposition axis: `bottleneck-first`. It still failed to beat the `P1` baseline, so the axis is interesting signal rather than a winning strategy.

## Sonnet Plan-State Trace (retry — canonical)

Stored `plan_evolution` from the Sonnet retry row (4 completed exec subtasks, then P1 timed out at turn 6):

```json
[
  {"turn_index": 2, "problem": "P4", "executed_sub_id": 1, "next_sub_id_out": 5, "plan_size": 5, "additions": [5], "revisions": [], "status_flips": [1]},
  {"turn_index": 3, "problem": "P4", "executed_sub_id": 5, "next_sub_id_out": 2, "plan_size": 6, "additions": [6], "revisions": [], "status_flips": [5]},
  {"turn_index": 4, "problem": "P2", "executed_sub_id": 2, "next_sub_id_out": 3, "plan_size": 7, "additions": [7], "revisions": [], "status_flips": [2]},
  {"turn_index": 5, "problem": "P3", "executed_sub_id": 3, "next_sub_id_out": 4, "plan_size": 8, "additions": [8], "revisions": [], "status_flips": [3]}
]
```

Turn 6 (P1 jobshop, sub_id 4): timed_out=true at 240s — P1 abandoned, stop_reason=subtask_timeout.

## GPT Plan-State Trace

Stored `plan_evolution` from the GPT row (8 completed exec subtasks, no hard kill):

```json
[
  {"turn_index": 2, "problem": "P4", "executed_sub_id": 1, "next_sub_id_out": 2, "plan_size": 7, "additions": [7], "revisions": [], "status_flips": [1, 5]},
  {"turn_index": 3, "problem": "P2", "executed_sub_id": 2, "next_sub_id_out": 8, "plan_size": 8, "additions": [8], "revisions": [], "status_flips": [2]},
  {"turn_index": 4, "problem": "P2", "executed_sub_id": 8, "next_sub_id_out": 9, "plan_size": 10, "additions": [9, 10], "revisions": [], "status_flips": [7, 8]},
  {"turn_index": 5, "problem": "P4", "executed_sub_id": 9, "next_sub_id_out": 3, "plan_size": 12, "additions": [11, 12], "revisions": [], "status_flips": [9]},
  {"turn_index": 6, "problem": "P3", "executed_sub_id": 3, "next_sub_id_out": 13, "plan_size": 13, "additions": [13], "revisions": [], "status_flips": [3]},
  {"turn_index": 7, "problem": "P3", "executed_sub_id": 13, "next_sub_id_out": 14, "plan_size": 14, "additions": [14], "revisions": [], "status_flips": [13]},
  {"turn_index": 8, "problem": "P1", "executed_sub_id": 14, "next_sub_id_out": 15, "plan_size": 15, "additions": [15], "revisions": [], "status_flips": [14]},
  {"turn_index": 9, "problem": "P1", "executed_sub_id": 15, "next_sub_id_out": 16, "plan_size": 17, "additions": [16, 17], "revisions": [], "status_flips": [15]}
]
```

## Blockers / Notes

1. Root-URL override is still required for Kaggle access. The working invocation shape is:
   - `python kaggle/scripts/run_portfolio_spike.py --model <model> --seed 1 --notebook-url 'https://kkb-production.jupyter-proxy.kaggle.net?token=...'`
   - Do not trust the `.env` `/k/{run}/{jwt}/proxy` construction for this notebook.
2. The harness gate bug is resolved in the generated task and now aligned in the generator source:
   - Hard stop remains `exec_parsed is None`.
   - Non-sequential `subtask_id` mismatches are now soft-overridden to the harness-selected `next_sub["id"]`.
3. Forecast coverage remains protocol-dependent:
   - untouched problems retain `null` thresholded Brier entries.
   - GPT touched all four problems, so it is the first run with full thresholded-Brier coverage across the portfolio.

## Interim Takeaways

1. The portfolio protocol now has clean live evidence from three frontier models, with two distinct multi-subtask styles:
   - Gemini: sparse but high-value hits (`P2`, `P4`).
   - Sonnet/GPT: broader dynamic-plan traversal with multiple pivots and additions.
2. `P2` looks like the consistent easy win: all canonical models solved it exactly.
3. `P4` remains the swing problem: only Gemini solved it, and that single hit is what keeps Gemini far ahead on net value.
4. `P1` remains the hardest planner-facing problem in this seed:
   - Sonnet timed out on its first real `P1` attempt.
   - GPT explored `P1` twice, named a bottleneck-first axis, but produced no improvement.
