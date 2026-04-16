---
color: orange
isContextNode: false
agent_name: Eli
---
# HCH HLE-12 worker — 24 task files authored, blocked on Kaggle token expiry

Authored all 24 task files (12 HCH v2 + 12 Vanilla arms) for the HCH HLE-12 spike. All syntax-check and smoke-test pass. Bridge connection timed out — Kaggle notebook session expired. Awaiting token refresh from user to run.

## Task Files Authored

24 task files generated via `scripts/gen_hch_hle12_tasks.py`:
- 12 HCH v2 arm files (`q{NN}_hch.py`) — full STEP 0/1/2/3 protocol with ATOMIC_PREDICTION
- 12 Vanilla arm files (`q{NN}_vanilla.py`) — one-shot ANSWER + P_CORRECT

For Q = {41, 43, 44, 48, 49, 52, 53, 55, 57, 65, 68, 99}

## HCH v2 Prompt Differences from v1
| Field | v1 | v2 |
|-------|-----|----|
| New STEP 0 | absent | ATOMIC_PREDICTION: {words_if_atomic, p_correct_if_atomic} |
| STEP 1 field | token_estimate | words_to_produce_solution |
| STEP 2 field | solved | correctly_solved |
| New axis | absent | A1 (atomic p_correct calibration), A2 (atomic word calibration) |

## Metacog Axes to Score
| Axis | Inputs | Formula |
|------|--------|--------|
| A1 | p_correct_if_atomic, vanilla_correct | Brier(p_correct_if_atomic, vanilla_correct) |
| A2 | words_if_atomic, vanilla_word_count | \|diff\| / max(1, van_wc) |
| A3 | chose_decomp, hch_correct, van_correct | tabulate decomp decisions |
| B  | words_to_produce vs actual_words | MAPE per subtask |
| C  | p_solve/confidence vs correctly_solved | Brier per subtask |
| D  | P_CORRECT vs correct (both arms) | Brier |

## Blocker
Bridge connection timed out at `resolve_kernel()` → `list_sessions()`. The Kaggle notebook session at `kkb-production.jupyter-proxy.kaggle.net` is no longer active.

**To unblock:**
1. Open https://www.kaggle.com/code/manumasson/new-benchmark-task-87295/edit
2. Start kernel → get fresh `KAGGLE_JUPYTER_URL` + `KAGGLE_JUPYTER_TOKEN`
3. Update `kaggle/.env`
4. Run: `python scripts/run_hch_hle12.py`
5. After: `python scripts/analyze_hch_hle12.py results/hch_hle12_run_*.jsonl`

## Ready-to-Run Scripts
- `scripts/run_hch_hle12.py` — runs all 24 tasks with 25s idle_wait, 180s timeout, 20s sleep between
- `scripts/analyze_hch_hle12.py` — parses judge notes, computes all 6 axes, prints per-Q table
- `pilots/hch-hle12-2026-04-15.md` — pilot note shell (ready for fill-in post-run)

## Files Changed

- kaggle/examples/hch_hle12/q41_hch.py
- kaggle/examples/hch_hle12/q41_vanilla.py
- kaggle/examples/hch_hle12/q43_hch.py
- kaggle/examples/hch_hle12/q43_vanilla.py
- kaggle/examples/hch_hle12/q44_hch.py
- kaggle/examples/hch_hle12/q44_vanilla.py
- kaggle/examples/hch_hle12/q48_hch.py
- kaggle/examples/hch_hle12/q48_vanilla.py
- kaggle/examples/hch_hle12/q49_hch.py
- kaggle/examples/hch_hle12/q49_vanilla.py
- kaggle/examples/hch_hle12/q52_hch.py
- kaggle/examples/hch_hle12/q52_vanilla.py
- kaggle/examples/hch_hle12/q53_hch.py
- kaggle/examples/hch_hle12/q53_vanilla.py
- kaggle/examples/hch_hle12/q55_hch.py
- kaggle/examples/hch_hle12/q55_vanilla.py
- kaggle/examples/hch_hle12/q57_hch.py
- kaggle/examples/hch_hle12/q57_vanilla.py
- kaggle/examples/hch_hle12/q65_hch.py
- kaggle/examples/hch_hle12/q65_vanilla.py
- kaggle/examples/hch_hle12/q68_hch.py
- kaggle/examples/hch_hle12/q68_vanilla.py
- kaggle/examples/hch_hle12/q99_hch.py
- kaggle/examples/hch_hle12/q99_vanilla.py
- kaggle/scripts/gen_hch_hle12_tasks.py
- kaggle/scripts/run_hch_hle12.py
- kaggle/scripts/analyze_hch_hle12.py
- kaggle/pilots/hch-hle12-2026-04-15.md

### NOTES

- NO from __future__ import annotations in any generated file (PEP 563 breaks @kbench.task — Dan's confirmed bug)
- HCH v2 prompt uses actual em-dashes (\u2014) — verified in generated PROMPT strings
- Generator uses repr() for PROMPT embedding — handles Q44's code block with backticks and quotes safely
- Comparison function handles: float ±0.01 (Q41), TC⁰/TC^0/TC0 variants (Q55), dodecagon with 'A ' prefix (Q99), case-insensitive default
- Q99 dataset answer is 'A dodecagon' but task spec gold is 'dodecagon' — comparison accepts both via substring check
- Bridge timeout (not 401/403): Kaggle notebook session has expired, not just token. User needs to start a fresh notebook session at the URL, then update .env
- Runner uses idle_wait_seconds=25.0 (vs default 10.0) and timeout_seconds=180.0 — both Dan's gotchas applied
- All 24 files pass ast.parse() and importlib smoke test (task name + GOLD_ANSWER verified)

[[task_1776236551225qja]]
