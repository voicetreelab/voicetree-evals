---
color: green
isContextNode: false
agent_name: Timi
---
# Portfolio Spike Phase 1 GPT-5.4 Complete

Ran the GPT-5.4 seed-1 Kaggle pilot with the root-form notebook URL, captured the canonical result row, updated the cross-model pilot note, and aligned the generator with the softened non-sequential subtask-id gate.

## GPT-5.4 Headline

- Model: `openai/gpt-5.4`
- Seed: `1`
- Stop reason: `max_exec_turns`
- Net score: `59.61794438560163`
- Wall time: `167.240478318`
- Declared axis P1: `bottleneck-first`
- Completed exec subtasks: `8`
- Parse fail: `false`
- Subtask killed count: `0`

## Per-Problem Headroom

| problem | headroom_fraction_captured | final_score | realized_bucket | subtasks_executed |
|---|---:|---:|---|---:|
| P1 | 0.0 | 155.0 | `miss` | 2 |
| P2 | 1.0 | 59.0 | `within_5pct` | 2 |
| P3 | 0.3989984150750811 | 541.1091754521477 | `within_20pct` | 2 |
| P4 | 0.0 | 20.0 | `miss` | 2 |

## GPT Validation Checklist

1. Dual parser accepted the live run: `parse_fail=false`, `turn_count=9`.
2. Hard-kill path was not needed: stop came from `max_exec_turns`, not timeout.
3. Pre-flight remained clean on the embedded seed-1 portfolio.
4. `thresholded_brier_by_problem` is populated for `P1-P4` because GPT touched all four problems.
5. Final JSONL row contains the expected pilot fields, including plan evolution, forecast history, and per-problem summaries.

## Cross-Model Canonical Table

| model | P1 | P2 | P3 | P4 | exec_subtasks | stop_reason | net_score | wall_s | declared_axis_p1 |
|---|---:|---:|---:|---:|---:|---|---:|---:|---|
| Gemini 3.1 Pro | 0.00 | 1.00 | 0.00 | 1.00 | 2 | `subtask_timeout` | 129.48 | 610.49 | — |
| Claude Sonnet 4.6 (retry) | 0.00 | 1.00 | 0.67 | 0.00 | 4 | `subtask_timeout` | 56.11 | 346.59 | — |
| GPT-5.4 | 0.00 | 1.00 | 0.40 | 0.00 | 8 | `max_exec_turns` | 59.62 | 167.24 | `bottleneck-first` |

## Harness Follow-Up

The generated task already had Zoe's soft override for non-sequential `subtask_id` mismatches, but the source generator still contained the old hard gate. I updated `kaggle/scripts/gen_portfolio_spike_task.py` so future regenerations preserve the same behavior:

- hard stop only when `exec_parsed is None`
- soft override when the model's `SUB_N_RESULT` label counter diverges from the harness-selected plan subtask id

## Artifacts

- `kaggle/results/portfolio_pilot_openai_gpt-5_4_seed1_20260416_120142.jsonl`
- `kaggle/pilots/portfolio-spike-2026-04-16.md`
- `kaggle/scripts/gen_portfolio_spike_task.py`


## Files Changed

- kaggle/scripts/gen_portfolio_spike_task.py
- kaggle/pilots/portfolio-spike-2026-04-16.md
- kaggle/results/portfolio_pilot_openai_gpt-5_4_seed1_20260416_120142.jsonl

### NOTES

- Root-form Kaggle notebook URL remains mandatory; the `.env` proxied `/k/{run}/{jwt}/proxy` form still returns `/api/sessions` 404 for this kernel.
- Gemini remains the net leader because it alone solved `P4` exactly.
- GPT is the first canonical run with full thresholded-Brier coverage across all four problems.

[[task_1776337456301t32]]
