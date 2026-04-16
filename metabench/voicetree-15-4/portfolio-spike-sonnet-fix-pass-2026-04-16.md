---
color: green
isContextNode: false
agent_name: Zoe
---
# Portfolio Spike Phase 1 — Sonnet fix-pass: harness gate bug diagnosed + fixed, re-run clean

Diagnosed and fixed a false subtask_parse_fail stop gate in portfolio_spike.py. Root cause: harness stopped when Sonnet's SUB_N_RESULT label count diverged from plan sub_id after a non-sequential jump. Fix: removed secondary subtask_id mismatch check. Re-run Sonnet seed 1 confirmed clean (net=56.11, parse_fail=false). GPT-5.4 greenlit.

## Root Cause Diagnosis

**Category: (d) Other — harness secondary validation over-fires on non-sequential plan sub_id jumps**

### The bug

`_parse_exec_turn` extracts `subtask_id = int(sub_match.group(1))` from the `SUB_N_RESULT:` label the model writes in its output. The main loop then checks:

```python
if exec_parsed is None or exec_parsed["subtask_id"] != next_sub["id"]:
    parse_fail = True
    stop_reason = "subtask_parse_fail"
```

### What happened in turn 6 (original run)

| | value |
|---|---|
| `next_sub["id"]` (harness expected) | `6` |
| `exec_parsed["subtask_id"]` (Sonnet wrote) | `5` |
| Gate fired? | YES — 5 ≠ 6 |

Sonnet's plan jumped from sub_id 4 → sub_id 5 (added by Sonnet) → sub_id 2 (P2) → sub_id 3 (P3) → sub_id 6 (P4 deep). When executing sub_id 6, it was Sonnet's 5th exec call, so it wrote `SUB_5_RESULT`. The harness expected `SUB_6_RESULT`.

### Why the response was actually valid

The parser already validates semantic correctness in `_parse_exec_turn`:
- `problem_id == expected_problem_id` ✓ (P4 == P4)
- `forecast[0] == expected_problem_id` ✓
- All required fields (CANDIDATE, REVISED_PLAN, NEXT_SUB_ID, FORECAST) present ✓

The `SUB_N_RESULT` label is just a formatting convention the model follows — not a semantic field.

## Fix Applied

Split the combined gate into two separate checks:
1. Keep `exec_parsed is None` → hard stop (real parse failure)
2. `exec_parsed["subtask_id"] != next_sub["id"]` → soft override: replace declared sub_id with harness's tracked `next_sub["id"]` and continue

This is surgical and safe: the harness controls which subtask prompt was sent, so it always knows the right sub_id regardless of what the model wrote.

## Re-run Results (canonical Sonnet seed 1)

| metric | original (buggy) | retry (fixed) |
|---|---|---|
| stop_reason | `subtask_parse_fail` | `subtask_timeout` |
| parse_fail | true | false |
| exec subtasks | 4 | 5 |
| net_score | 6.92 | **56.11** |
| wall_s | 113.4 | 346.6 |
| P2 headroom | 0.00 | **1.00 (OPTIMAL)** |
| P3 headroom | 0.63 | **0.67** |
| P4 headroom | 0.00 | 0.00 |
| P1 | not reached | timed out at 240s |

### Retry plan evolution
```
Turn 2: P4 (sub 1) → add sub 5 → next=5
Turn 3: P4 (sub 5) → add sub 6 → next=2
Turn 4: P2 (sub 2, OPTIMAL 59/59) → add sub 7 → next=3
Turn 5: P3 (sub 3, tour 508.9) → add sub 8 → next=4
Turn 6: P1 (sub 4) → TIMEOUT at 240s
```

## Token Status
Token (FL0vlYmD prefix, run 311788458) confirmed valid — ping test returned 42 successfully.

## DIFF

```
--- kaggle/examples/portfolio_spike/portfolio_spike.py
@@ -3997,6 +3997,13 @@
-        if exec_parsed is None or exec_parsed["subtask_id"] != next_sub["id"]:
+        if exec_parsed is None:
             turns.append(exec_turn)
             parse_fail = True
             stop_reason = "subtask_parse_fail"
             break
+
+        if exec_parsed["subtask_id"] != next_sub["id"]:
+            # Model labelled its response SUB_N_RESULT with wrong counter
+            # (happens when harness skips to a non-sequential plan sub_id).
+            # Semantic content is still valid: problem_id and forecast are
+            # already validated in _parse_exec_turn.  Override the declared
+            # subtask_id so downstream accounting stays correct.
+            exec_parsed = dict(exec_parsed)
+            exec_parsed["subtask_id"] = next_sub["id"]
```

## Complexity: medium

Harness loop logic in portfolio_spike.py; needed to understand _parse_exec_turn interaction and secondary validation semantics before knowing where to split the check

## Files Changed

- kaggle/examples/portfolio_spike/portfolio_spike.py
- kaggle/pilots/portfolio-spike-2026-04-16.md
- kaggle/results/portfolio_pilot_anthropic_claude-sonnet-4-6_seed1_20260416_retry.jsonl

### NOTES

- The SUB_N_RESULT counter diverges from plan sub_id whenever the harness visits sub_ids non-sequentially (e.g. model adds sub_id=5, harness skips back to execute sub_id=2). This is a structural property of plan-state protocol with dynamic additions — any model that reorders its queue will trigger this.
- The fix should also be applied to the gen_portfolio_spike_task.py source if portfolio_spike.py is ever regenerated from it.
- P4 (30-node dense coloring, gold=4, baseline=20, value_cap=100) is proving very hard for frontier models to solve manually. Gemini solved it (exact) while Sonnet could not after 2 attempts. This is a strong discriminator.
- Harness note: per_problem_turns does not include turns where subtask_id was overridden (original run). Retry run is clean.

## Related

- [portfolio-spike-phase1-partial-sonnet-parse-gate-2026-04-16](portfolio-spike-phase1-partial-sonnet-parse-gate-2026-04-16.md)

[[task_1776340014216ob3]]
