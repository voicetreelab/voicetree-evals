# STATUS — Read this first

**Goal:** let agents easily run experiments on Kaggle's official Community Benchmarks platform.

**State (2026-04-15):** ✅ We have it. Use **Option A** (`option_a_bridge/`).

## What works today
- Agent writes `tasks/foo.py` containing a `@kbench.task` function.
- Runs `python option_a_bridge/submit_task.py tasks/foo.py`.
- Code executes on Kaggle's infrastructure via the live notebook kernel.
- Produces real `.task.json` + `.run.json` with token counts, cost, and model output.
- Verified: ~1–5s per run, ~$0.0004/call against `gemini-2.5-flash`.

That is the entire "agents run experiments on Kaggle" loop. **Done.**

## What's still half-built
**Option B** (`kaggle kernels push`) is for *leaderboard submission* — each entry needs its own notebook URL. Currently produces `.task.json` but not `.run.json` (docker-image issue diagnosed in `~/brain/voicetree-13-4/option-b-rootcause-two-layer-bug.md`). **Not on the critical path** — you can publish manually by clicking "Save Task" once per task in the Kaggle UI.

## Next step
See `HANDOVER.md` — pilot spikes for HCH + metacog benches.
