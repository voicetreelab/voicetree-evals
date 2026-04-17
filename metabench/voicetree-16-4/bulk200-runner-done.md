---
color: green
agent_name: Gia
---

# Bulk200 runner done

## Summary

Appended 12 rows to `kaggle_submission/questions.jsonl` without regenerating the canonical file, taking it from 188 to 200 rows. New rows: `mbj_medium_seed1..7`, `mbj_hard_seed1..3`, `portfolio_medium_seed50`, `portfolio_medium_seed51`. Portfolio component sets landed as `tsp/graphcol/ve` for seed 50 and `steiner/ve/mbj` for seed 51. Round-trip and duplicate-id checks passed.

Ran the 4-row x 3-model sweep on `mbj_medium_seed1`, `mbj_medium_seed5`, `mbj_hard_seed1`, `portfolio_medium_seed50`. I could not use `mcp__voicetree__spawn_agent` / `wait_for_agents` because those tools were unavailable in this environment, so I executed the runner phase directly and wrote the expected artifacts under `kaggle_submission/results/full/{question_id}/`.

## Eval rollup

| model | strict_protocol_cf rows | feasible rows | rows with error | headline |
|---|---:|---:|---:|---|
| `gemini-flash-latest` | 4/4 | 2/4 | 0/4 | Best `mbj_medium_seed1` improvement, but invalid MBJ schedules on `mbj_medium_seed5` and `mbj_hard_seed1`; safe-pool portfolio feasible but slow and low-value |
| `claude-sonnet-4.6` | 1/4 | 3/4 | 3/4 | Medium MBJ repeatedly timed out to baseline; hard MBJ was excellent; portfolio row failed all 3 parse retries |
| `gpt-5.4-mini` | 4/4 | 4/4 | 0/4 | Fastest and most stable, but baseline-echoed every MBJ row; safe-pool portfolio feasible in one turn |

## Row findings

- `mbj_medium_seed1`: Gemini improved baseline `7167 -> 6000` (gap `5.26%`, score `90.72`). Sonnet timed out 3 times and fell back to baseline (`7167`, score `71.20`). GPT was clean but baseline-only (`7167`, score `74.10`).
- `mbj_medium_seed5`: Gemini emitted an infeasible schedule (`duration mismatch for J8 on M7`, score `0.0`). Sonnet again timed out 3 times and recovered baseline (`7440`, score `72.90`). GPT again baseline-echoed (`7440`, score `75.85`).
- `mbj_hard_seed1`: Sonnet found the best solution of the sweep (`7700 -> 6560`, gap `2.18%`, score `96.89`). GPT stayed at baseline (`7700`, score `79.91`). Gemini emitted an infeasible schedule (`precedence failed for J3`, score `0.0`).
- `portfolio_medium_seed50`: GPT feasible in one turn (score `42.14`) but left large headroom in all 3 components. Gemini also became feasible, with strong `tsp` and decent `ve`, but needed `1099.9s` and still left `graphcol` weak (score `7.20`). Sonnet failed all 3 retries with schema-level parse errors (`portfolio submission must be an object` / no usable `BEST_GUESS`).

## Baseline-echo check

- GPT baseline-echoed all 3 MBJ rows: `mbj_medium_seed1`, `mbj_medium_seed5`, `mbj_hard_seed1`.
- Sonnet baseline-echoed both MBJ medium rows but broke the pattern on `mbj_hard_seed1` with a real improvement.
- Gemini broke the baseline-echo pattern too, but in a mixed way: one real improvement (`mbj_medium_seed1`) and two infeasible schedules (`mbj_medium_seed5`, `mbj_hard_seed1`).

## Prediction claims

- MBJ is a useful discriminator, not just a feasibility smoke. It separated GPT's baseline-echo behavior from Sonnet's hard-seed optimization and Gemini's schedule-validity failures.
- The MWIS-safe portfolio pool helped. `portfolio_medium_seed50` was technically feasible for GPT and Gemini, so the prior total portfolio collapse was not solely a generation-pool issue. But quality remained weak and Sonnet still failed at the schema layer.
- GPT's MBJ behavior still matches Emi's baseline-echo concern. On this 3-row MBJ slice it improved `0/3` times despite being fully feasible and very fast.

## Verdict

`kaggle_submission/questions.jsonl` is now at 200 rows and remains uncommitted for user review. I would treat the dataset append as ready for review, but not treat the eval slice as a clean green light: Sonnet is still unstable on medium MBJ and portfolio parsing, Gemini still emits invalid MBJ schedules on some seeds, and GPT's MBJ optimization signal is mostly baseline recovery.

## Learnings

- Tried to follow the task's parent/child orchestration literally, then switched to a single-agent local runner because the Voicetree spawn/wait MCP tools were not exposed here.
- Do not run `python scripts/build_questions.py` in place. The safe path is append-only generation plus `_sanity_check_round_trip`, or you will clobber the 188-row benchmark file.
- The safe portfolio pool removes the MWIS generation blocker, but it does not solve portfolio quality or parser brittleness by itself. MBJ also has three distinct model behaviors now: GPT baseline echo, Sonnet timeout-or-win, Gemini improve-or-break.

## Files Changed

- `kaggle_submission/questions.jsonl`
- `kaggle_submission/results/full/bulk200-gemini-flash-latest-summary.json`, `kaggle_submission/results/full/bulk200-claude-sonnet-4.6-summary.json`, `kaggle_submission/results/full/bulk200-gpt-5.4-mini-summary.json`
- `kaggle_submission/results/full/mbj_medium_seed1/question.json`, `kaggle_submission/results/full/mbj_medium_seed1/gemini-flash-latest.json`, `kaggle_submission/results/full/mbj_medium_seed1/claude-sonnet-4.6.json`, `kaggle_submission/results/full/mbj_medium_seed1/gpt-5.4-mini.json`, `kaggle_submission/results/full/mbj_medium_seed1/concerns.md`
- `kaggle_submission/results/full/mbj_medium_seed5/question.json`, `kaggle_submission/results/full/mbj_medium_seed5/gemini-flash-latest.json`, `kaggle_submission/results/full/mbj_medium_seed5/claude-sonnet-4.6.json`, `kaggle_submission/results/full/mbj_medium_seed5/gpt-5.4-mini.json`, `kaggle_submission/results/full/mbj_medium_seed5/concerns.md`
- `kaggle_submission/results/full/mbj_hard_seed1/question.json`, `kaggle_submission/results/full/mbj_hard_seed1/gemini-flash-latest.json`, `kaggle_submission/results/full/mbj_hard_seed1/claude-sonnet-4.6.json`, `kaggle_submission/results/full/mbj_hard_seed1/gpt-5.4-mini.json`, `kaggle_submission/results/full/mbj_hard_seed1/concerns.md`
- `kaggle_submission/results/full/portfolio_medium_seed50/question.json`, `kaggle_submission/results/full/portfolio_medium_seed50/gemini-flash-latest.json`, `kaggle_submission/results/full/portfolio_medium_seed50/claude-sonnet-4.6.json`, `kaggle_submission/results/full/portfolio_medium_seed50/gpt-5.4-mini.json`, `kaggle_submission/results/full/portfolio_medium_seed50/concerns.md`
- `voicetree-16-4/bulk200-runner-done.md`

- parent [[task_1776379549388fz5.md]]
