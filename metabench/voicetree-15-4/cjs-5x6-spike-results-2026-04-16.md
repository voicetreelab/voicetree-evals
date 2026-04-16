---
color: green
isContextNode: false
agent_name: Raj
---
# CJS 5x6 Spike Results

Completed the full `3 models x 3 seeds` live Kaggle spike and wrote the pilot note. Gemini had the best mean score, Sonnet searched deepest but hit a timeout on one seed, and GPT-5.4 never converted its turns into a scored improving schedule.

## Aggregate
| model | mean gap_pct | mean score | mean wall_s | mean turns | mean exec subtasks |
|---|---:|---:|---:|---:|---:|
| Gemini 3.1 Pro | 37.04 | 60.64 | 232.11 | 1.67 | 0.67 |
| Claude Sonnet 4.6 | 42.35 | 50.67 | 698.16 | 3.00 | 2.00 |
| GPT-5.4 | 95.19 | 8.87 | 39.33 | 3.67 | 2.67 |

## Per-seed rows
| model | seed | baseline | optimal | final | gap_pct | stop_reason | wall_s |
|---|---:|---:|---:|---:|---:|---|---:|
| Gemini 3.1 Pro | 1 | 155 | 90 | 100 | 11.11 | `subtask_stop` | 224.30 |
| Gemini 3.1 Pro | 2 | 192 | 90 | 90 | 0.00 | `subtask_stop` | 460.85 |
| Gemini 3.1 Pro | 3 | 170 | 85 | 170 | 100.00 | `plan_parse_fail` | 11.18 |
| Claude Sonnet 4.6 | 1 | 155 | 90 | 103 | 14.44 | `subtask_stop` | 138.90 |
| Claude Sonnet 4.6 | 2 | 192 | 90 | 167 | 85.56 | `subtask_stop` | 371.83 |
| Claude Sonnet 4.6 | 3 | 170 | 85 | 108 | 27.06 | `subtask_timeout` | 1583.75 |
| GPT-5.4 | 1 | 155 | 90 | 155 | 72.22 | `subtask_stop` | 41.99 |
| GPT-5.4 | 2 | 192 | 90 | 192 | 113.33 | `subtask_stop` | 45.37 |
| GPT-5.4 | 3 | 170 | 85 | 170 | 100.00 | `subtask_stop` | 30.64 |

## Key findings
- Gemini won on mean score because seeds `1` and `2` were strong one-subtask improvements, including one exact solve. Its weakness was robustness: seed `3` failed at plan parse.
- Sonnet was the only model showing sustained deeper search with multiple valid improving execution turns, but it was far more expensive in wall time and one seed had to be converted to `subtask_timeout` after a manual kernel interrupt.
- GPT-5.4 used the most execution turns on average but produced `0` valid scored improving schedules. All three runs fell back to baseline after repeated infeasible proposals.

## Calibration / behavior
- Gemini had the best plan-stage continuation calibration (`mean continue brier 0.0013`) on the seeds where the plan parsed.
- Sonnet had the best final-quality calibration (`mean final_quality_brier 0.1981`) and the best evidence of non-trivial search depth.
- GPT’s continuation calibration was worst (`0.6297`) because it kept decomposing even when continuation never paid off in the scored result.

## Pilot note
- Wrote `kaggle/pilots/cjs-5x6-spike-2026-04-16.md` with the aggregate table, full per-seed table, calibration notes, one-shot vs multi-turn comparison, and blockers.

## Files Changed

- kaggle/results/cjs_5x6_google_gemini-3_1-pro-preview_20260416_091133.jsonl
- kaggle/results/cjs_5x6_google_gemini-3_1-pro-preview_20260416_091155.jsonl
- kaggle/results/cjs_5x6_google_gemini-3_1-pro-preview_20260416_091215.jsonl
- kaggle/results/cjs_5x6_google_gemini-3_1-pro-preview_20260416_091732.jsonl
- kaggle/results/cjs_5x6_google_gemini-3_1-pro-preview_20260416_full.jsonl
- kaggle/results/cjs_5x6_anthropic_claude-sonnet-4-6_20260416_092551.jsonl
- kaggle/results/cjs_5x6_openai_gpt-5_4_20260416_100133.jsonl
- kaggle/pilots/cjs-5x6-spike-2026-04-16.md

### NOTES

- Claude Sonnet seed 3 exceeded the intended `600s` execution-turn budget; the row was finalized as `subtask_timeout` by manually interrupting the kernel because the current port lacks true hard-turn kill.
- The Gemini final artifact was normalized into a clean 3-row file because the initial smoke run wrote a literal `\\n` suffix.
- GPT completed after the local controlling turn had been interrupted; the background process still wrote the full 3-row result file successfully.

validated by [[cjs-5x6-kaggle-port]]
