---
color: green
agent_name: Gia
---

# Bulk200 progress verified

## Summary

Verified the bulk200 task is documented in the graph and the workspace state matches the handoff. `kaggle_submission/questions.jsonl` is at 200 rows with 200 unique ids. The append-only additions are present: `mbj_medium_seed1..7`, `mbj_hard_seed1..3`, `portfolio_medium_seed50`, `portfolio_medium_seed51`.

The representative 4-row x 3-model eval sweep is complete and artifacts exist under `kaggle_submission/results/full/{question_id}/` for `mbj_medium_seed1`, `mbj_medium_seed5`, `mbj_hard_seed1`, and `portfolio_medium_seed50`, including `question.json`, per-model JSON outputs, and `concerns.md`. Summary rollups also exist at `kaggle_submission/results/full/bulk200-*.json`.

The key result pattern is stable:
- `gpt-5.4-mini`: 4/4 feasible, fastest, but baseline-echoed all 3 MBJ rows.
- `claude-sonnet-4.6`: medium MBJ timed out to baseline, hard MBJ improved strongly, portfolio row failed parsing on all 3 retries.
- `gemini-flash-latest`: improved `mbj_medium_seed1`, produced infeasible schedules on `mbj_medium_seed5` and `mbj_hard_seed1`, and eventually reached a technically feasible but low-value safe-pool portfolio row.

The canonical task node for this work is `voicetree-16-4/bulk200-runner-done.md`. This follow-up node exists only to make the final state explicit after the wait monitor asked for progress-node confirmation.

## Files Changed

- `voicetree-16-4/bulk200-progress-verified.md`

## Learnings

- Tried to rely on the already-written progress node, then added this explicit follow-up because the wait monitor asked for progress-node creation after the fact.
- A future agent could incorrectly assume the task is undocumented because the orchestration MCP tools were unavailable. In this environment, manual `.md` progress nodes are the correct fallback.
- The important belief to carry forward is that the task is complete but not green across models: the dataset append succeeded cleanly, while the eval slice still shows distinct MBJ/pathology modes by model.

- parent [[task_1776379549388fz5.md]]
