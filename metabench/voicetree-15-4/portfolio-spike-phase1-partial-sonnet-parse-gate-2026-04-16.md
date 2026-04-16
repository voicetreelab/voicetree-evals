---
color: blue
isContextNode: false
agent_name: Timi
---
# Portfolio Spike Phase 1 — Sonnet partial result triggers parser-fail stop gate

Ran Phase 1 serially on the working root-form Kaggle URL. Sonnet completed a real seed-1 portfolio run and showed multi-subtask plan-state behavior, but the final row reported `subtask_parse_fail`, so GPT-5.4 was not launched and the phase was escalated as instructed.

## Command run
```bash
python kaggle/scripts/run_portfolio_spike.py \
  --model anthropic/claude-sonnet-4-6 \
  --seed 1 \
  --notebook-url 'https://kkb-production.jupyter-proxy.kaggle.net?token=...FL0vlYmD...'
```

## Sonnet headline row
- model: `anthropic/claude-sonnet-4-6`
- seed: `1`
- stop_reason: `subtask_parse_fail`
- economic_net_score: `6.92`
- wall_s: `113.41`
- declared_axis_p1: `null`
- total exec subtasks: `4`

## Per-problem headroom captured
- `P1`: `0.00`
- `P2`: `0.00`
- `P3`: `0.6294`
- `P4`: `0.00`

## What Sonnet actually did before the stop
- Executed repeated `P4` subtasks and dynamically added follow-up work.
- Executed `P2` once, but did not beat baseline.
- Executed `P3` once and improved tour length from `588.2207` to `513.9034`.
- Added new plan items over time (`5`, `6`, `7`, `8`), which is genuine plan-state behavior.

Stored `plan_evolution`:
```json
[
  {
    "additions": [5],
    "executed_sub_id": 1,
    "next_sub_id_out": 2,
    "plan_size": 5,
    "problem": "P4",
    "revisions": [2, 3, 4],
    "status_flips": [1],
    "turn_index": 2
  },
  {
    "additions": [6],
    "executed_sub_id": 2,
    "next_sub_id_out": 3,
    "plan_size": 6,
    "problem": "P4",
    "revisions": [],
    "status_flips": [2],
    "turn_index": 3
  },
  {
    "additions": [7],
    "executed_sub_id": 3,
    "next_sub_id_out": 4,
    "plan_size": 7,
    "problem": "P2",
    "revisions": [],
    "status_flips": [3],
    "turn_index": 4
  },
  {
    "additions": [8],
    "executed_sub_id": 4,
    "next_sub_id_out": 6,
    "plan_size": 8,
    "problem": "P3",
    "revisions": [],
    "status_flips": [4],
    "turn_index": 5
  }
]
```

## Why Phase 1 stopped here
Otto's stop rule says to stop and ping if a model produces an output shape neither parser form handles.

The Sonnet row reports:
```json
{
  "stop_reason": "subtask_parse_fail",
  "parse_fail": true,
  "turn_count": 6
}
```

But the stored turns through `turn_index=6` all have `parse_ok=true`. That means the practical blocker is now one of:
1. an unrecorded failing transition after the last stored parsed turn, or
2. a harness state inconsistency where `parse_fail` / `stop_reason` is being set despite the captured turns parsing.

Either way, this is a gated Sonnet fix-pass issue, so GPT-5.4 was not run.

## Additional artifact
Created partial cross-model pilot note:
- `kaggle/pilots/portfolio-spike-2026-04-16.md`

That note currently includes:
- Gemini Phase 0 result
- Sonnet partial Phase 1 result
- root-URL access fix
- explicit blocker for GPT

## Learnings
1. Tried Sonnet serially on the exact host-root URL override instead of the `.env` proxy URL. That was correct: the run executed normally on Kaggle and returned a real result row.
2. A future agent might misread `subtask_parse_fail` as 'Sonnet never executed'. That would be wrong. Sonnet completed four execution subtasks and the interesting issue is the mismatch between the final row's parse-fail status and the stored parsed turns.
3. The updated belief is that portfolio Phase 1 is now in a model-protocol debugging regime, not a Kaggle connectivity regime. The next highest-leverage action is a targeted Sonnet parser/harness review before spending the GPT slot.

## Files Changed

- kaggle/results/portfolio_pilot_anthropic_claude-sonnet-4-6_seed1_20260416_114146.jsonl
- kaggle/pilots/portfolio-spike-2026-04-16.md

### NOTES

- The working Kaggle access path is now confirmed: host-root `https://kkb-production.jupyter-proxy.kaggle.net?token=...` passed via `--notebook-url`.
- Sonnet did not hit auth/404 or SSL-hang; the kernel went busy then idle normally and the local wrapper returned a real row.
- The blocker is specifically the parser-fail gate on Sonnet's completed run, not connectivity.

## Related

- [portfolio-spike-v1-kaggle-root-url-pilot-2026-04-16](portfolio-spike-v1-kaggle-root-url-pilot-2026-04-16.md)
- [portfolio-spike-kaggle-url-form-diagnosis-2026-04-16](portfolio-spike-kaggle-url-form-diagnosis-2026-04-16.md)

[[task_1776337456301t32]]
