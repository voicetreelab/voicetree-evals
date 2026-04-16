---
color: green
isContextNode: false
agent_name: Timi
---
# Portfolio Spike v1 — root URL Kaggle pilot succeeded, execution stopped on subtask timeout

Re-ran the Gemini seed-1 Phase 0 pilot using the user's exact host-root Kaggle URL form (`https://kkb-production.jupyter-proxy.kaggle.net?token=...`) via `--notebook-url`. That bypassed the previous `/k/.../proxy` 404 issue, executed the portfolio task on Kaggle, solved P2 and P4 exactly, and then stopped cleanly on a subtask timeout with economic net score `129.48`.

## Command used
```bash
python kaggle/scripts/run_portfolio_spike.py \
  --model google/gemini-3.1-pro-preview \
  --seed 1 \
  --notebook-url 'https://kkb-production.jupyter-proxy.kaggle.net?token=...FL0vlYmD...'
```

## Headline row
- model: `google/gemini-3.1-pro-preview`
- seed: `1`
- stop_reason: `subtask_timeout`
- wall_s: `610.49`
- economic_net_score: `129.48`
- declared_axis_p1: `null`
- subtask_killed_count: `1`

Per-problem headroom captured:
- `P1`: `0.00`
- `P2`: `1.00`
- `P3`: `0.00`
- `P4`: `1.00`

## Result artifact
- `kaggle/results/portfolio_pilot_google_gemini-3_1-pro-preview_seed1_20260416_112855.jsonl`

## What happened
Turn 1 parsed successfully and produced this initial plan:
```json
[
  {
    "budget_s": 300,
    "desc": "Find optimal Steiner tree for the 3 terminals and valid frequency assignment",
    "id": 1,
    "problem": "P2",
    "status": "pending"
  },
  {
    "budget_s": 400,
    "desc": "Construct a 4-coloring for the 30-node graph to minimize conflicting edges",
    "id": 2,
    "problem": "P4",
    "status": "pending"
  },
  {
    "budget_s": 300,
    "desc": "Optimize TSP-20 tour using geometric heuristics and 2-opt",
    "id": 3,
    "problem": "P3",
    "status": "pending"
  },
  {
    "budget_s": 400,
    "desc": "Compress the coupled jobshop schedule using greedy active scheduling",
    "id": 4,
    "problem": "P1",
    "status": "pending"
  }
]
```

Exec turn 1 (`P2`) parsed and verified feasible at exact gold `59` with perfect thresholded forecast `1.0` across all bins.

Exec turn 2 (`P4`) parsed and verified feasible at exact gold `4` with perfect thresholded forecast `1.0` across all bins.

Exec turn 3 timed out cleanly before parse, so the run stopped with `subtask_timeout`.

Plan evolution captured in the row:
```json
[
  {
    "additions": [],
    "executed_sub_id": 1,
    "next_sub_id_out": 2,
    "plan_size": 4,
    "problem": "P2",
    "revisions": [],
    "status_flips": [1],
    "turn_index": 2
  },
  {
    "additions": [],
    "executed_sub_id": 2,
    "next_sub_id_out": 3,
    "plan_size": 4,
    "problem": "P4",
    "revisions": [],
    "status_flips": [2],
    "turn_index": 3
  }
]
```

## Per-problem row summary
| problem | baseline | gold | final | headroom_fraction_captured | value_captured | realized_bucket | final_thresholded_forecast |
|---|---:|---:|---:|---:|---:|---|---|
| P1 | 155.0 | 90.0 | 155.0 | 0.00 | 0.0 | miss | null |
| P2 | 72.0 | 59.0 | 59.0 | 1.00 | 60.0 | within_5pct | all 1.0 |
| P3 | 588.2206603869462 | 470.14629428718786 | 588.2206603869462 | 0.00 | 0.0 | within_50pct | null |
| P4 | 20.0 | 4.0 | 4.0 | 1.00 | 100.0 | within_5pct | all 1.0 |

## Validation checklist
1. Dual parser accepted Gemini's actual turn-1 and turn-N output?
Yes. Turn 1 and exec turns 2/3 parsed successfully. In this run Gemini used label-block output, so top-level JSON fallback was preserved but not exercised.
2. Hard-kill did not need to fire, OR fired cleanly without human intervention?
Yes. It fired cleanly on the next subtask and stopped the run with `subtask_timeout`.
3. Pre-flight gate regenerated cleanly (if any problem required regen at seed 1)?
Yes. Embedded preflight shows `P2` regenerated to attempt `8`; others accepted on attempt `1`.
4. Scoring produced non-NA thresholded Brier per problem?
No. `P2` and `P4` have `0.0`, but untouched `P1` and `P3` remain `null` because the current protocol only emits forecasts for executed problems.
5. Final JSONL row contains: seed, per-problem baseline/gold/final/headroom_captured, plan_trace, declared axis on P1 if model named one, stop_reason, wall_s, economic_net_score, thresholded forecasts + realized bucket.
Yes. All fields exist in the row. `declared_axis_p1` is `null` because Gemini did not name one.

## Learnings
1. Tried the user's exact host-root `?token=` URL without touching the ported task code. That was the right move: it immediately bypassed the repeated `/api/sessions` 404 failure mode from the proxied `.env` URL.
2. A future agent could wrongly conclude the harness is still broken because the run ended on timeout. The important distinction is that the bridge and Kaggle packaging are now working; the remaining issue is portfolio execution behavior and spec-level scoring coverage for untouched problems.
3. The current mental model is: root-host Jupyter access is correct, the Kaggle task code runs end-to-end, Gemini can solve `P2` and `P4` exactly under this protocol, and the next design question is whether untouched problems should receive mandatory forecasts so Brier is never `NA`.

## Files Changed

- kaggle/results/portfolio_pilot_google_gemini-3_1-pro-preview_seed1_20260416_112855.jsonl

### NOTES

- This run confirms the connection issue was URL-form related: the exact bare `?token=` host URL worked, while the `.env` proxied `/k/.../proxy` URL repeatedly returned `/api/sessions` 404.
- Hard-kill behavior worked as intended: the third exec turn timed out cleanly without manual intervention.
- One checklist item remains a spec gap: untouched problems do not get forecasts, so `thresholded_brier_by_problem` is `null` for P1 and P3.

## Related

- [portfolio-spike-kaggle-url-form-diagnosis-2026-04-16](portfolio-spike-kaggle-url-form-diagnosis-2026-04-16.md)
- [portfolio-spike-v1-kaggle-pilot-retry-still-404-2026-04-16](portfolio-spike-v1-kaggle-pilot-retry-still-404-2026-04-16.md)

[[task_1776337456301t32]]
