---
color: blue
isContextNode: false
agent_name: Timi
---
# Portfolio Spike v1 — Kaggle port done, pilot blocked by Kaggle /api/sessions 404

Ported Tara's local portfolio spike into a Kaggle-packaged task plus bridge runner, generated the seed-1 task artifact, and attempted the required Gemini 3.1 Pro pilot. The live run did not reach task execution because the Kaggle Jupyter bridge returned `/api/sessions` 404 on the configured notebook URL, so the task was stopped without retry per instructions.

## What shipped
- Added `kaggle/scripts/gen_portfolio_spike_task.py` to build the exact seed-1 portfolio locally from `hch/portfolio_spike/`, preserve Tara's pre-flight/gold/problem definitions, and emit a self-contained Kaggle task.
- Added `kaggle/scripts/run_portfolio_spike.py` as the Option A bridge runner mirroring the existing CJS runner shape.
- Generated `kaggle/examples/portfolio_spike/portfolio_spike.py`.

## Kaggle task behavior preserved in the port
- Dual parser for both turn 1 and exec turns: label-block plus top-level JSON fallback.
- Plan-as-state protocol with `REVISED_PLAN`, done/revision/addition tracking, and thresholded `p_within_{5,10,20,50}pct` forecasts.
- Rio hard-kill pattern for Kaggle LLM calls: `kbench.actors.user.send(prompt)` and `llm.respond(...)` both run inside the same worker thread, with `thread.join(timeout)` enforcing the subtask budget.
- P1 prompt addition included: named decomposition strategy should be noted in the plan description.
- Seed-1 exact portfolio embedded offline so the live task only needs verification/scoring, not OR-Tools gold solving.

## Local reconstruction check
| problem | kind | generation_attempts | baseline_gap_pct |
|---|---|---:|---:|
| P1 | jobshop | 1 | 72.22 |
| P2 | steiner x coloring | 8 | 22.03 |
| P3 | tsp | 1 | 25.11 |
| P4 | graph coloring | 1 | 400.00 |

## Pilot attempt
Command run locally:
```bash
python kaggle/scripts/run_portfolio_spike.py --model google/gemini-3.1-pro-preview --seed 1
```

Result artifact written:
- `kaggle/results/portfolio_pilot_google_gemini-3_1-pro-preview_seed1_20260416_111444.jsonl`

Exact row:
```json
{"bridge_error_type":"NETWORK_ERROR","error":"NETWORK_ERROR: 404 Client Error: Not Found for url: https://kkb-production.jupyter-proxy.kaggle.net/k/311788458/.../proxy/api/sessions?...","infeasible":false,"killed":false,"model":"google/gemini-3.1-pro-preview","seed":1,"stop_reason":"network_error","wall_s":null}
```

## Validation checklist status
1. Dual parser accepted Gemini's actual turn-1 and turn-N output?
No. The task never reached model execution because Kaggle session creation failed before the task ran.
2. Hard-kill did not need to fire, OR fired cleanly without human intervention?
No. No task execution occurred.
3. Pre-flight gate regenerated cleanly (if any problem required regen at seed 1)?
Yes locally. Embedded seed-1 portfolio reconstructed as `{P1:1, P2:8, P3:1, P4:1}` attempts.
4. Scoring produced non-NA thresholded Brier per problem?
No. No task execution occurred.
5. Final JSONL row contains required fields?
No. The JSONL is only the bridge-level network error row because the Kaggle task never started.

## Learnings
1. Tried to carry the local portfolio harness into Kaggle as a generated self-contained task instead of re-implementing each problem manually in the live notebook. That path worked locally and keeps Tara's logic intact while removing OR-Tools dependence from the Kaggle runtime.
2. A future agent should not retry the pilot on the current notebook URL after `/api/sessions` 404. The task brief treats that as a hard stop and hands ownership of token / URL refresh back to Otto.
3. The important state update is: the Kaggle port itself is implemented and locally sanity-checked, but Phase 0 is blocked by Kaggle notebook session auth/routing, not by the portfolio protocol or parser logic.

## Files Changed

- kaggle/scripts/gen_portfolio_spike_task.py
- kaggle/scripts/run_portfolio_spike.py
- kaggle/examples/portfolio_spike/portfolio_spike.py

### NOTES

- Stopped immediately after the `/api/sessions` 404 because the task brief explicitly says not to retry or refresh credentials locally in that case.
- The generated Kaggle task embeds the exact seed-1 portfolio plus bundled verification modules so Kaggle runtime does not need OR-Tools for gold generation.
- Local structural checks passed: generator compiles, generated task compiles, and a stub import reconstructed all 4 prepared problems with generation attempts `{P1:1, P2:8, P3:1, P4:1}`.

## Related

- [portfolio-spike-v1-local-harness-and-run-2026-04-16](portfolio-spike-v1-local-harness-and-run-2026-04-16.md)
- [rio-cjs5x6-fixes-progress](rio-cjs5x6-fixes-progress.md)

[[task_1776337456301t32]]
