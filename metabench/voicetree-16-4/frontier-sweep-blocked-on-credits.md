---
color: red
isContextNode: false
agent_name: Eve
---
# Frontier sweep — Opus halted on Anthropic credits (34/56); Gemini 3 Pro + GPT-5.4 done (56/56 each)

Frontier sweep ran as 10 parallel batches across 56 rows × 3 models. Gemini 3 Pro and GPT-5.4 completed all 56 rows with 100% and 47/56 feasibility respectively. Claude Opus 4.6 halted at 34 real completions + 4 billing-error stubs when the Anthropic API credit balance ran out; 22 rows remain. All committed per-row JSONs are under results/runs/<model>/<id>.json and are already on origin/main.

## Final tally (as of 12:02 AEST)

| Model | Present | Real completions | Billing-error stubs | Missing | Feasible (of real) | Mean score (of real) |
|---|---|---|---|---|---|---|
| claude-opus-4.6 | 38/56 | 34 | 4 | 18 | 24/34 | ~64 |
| gemini-3-pro-preview | 56/56 | 56 | 0 | 0 | 56/56 | 61.9 |
| gpt-5.4 | 56/56 | 56 | 0 | 0 | 47/56 | 48.1 |

Non-frontier baselines for the same 56 rows:
- claude-sonnet-4.6: 19/56 feasible, mean 35.6
- gemini-flash-latest: 32/56 feasible, mean 48.7
- gpt-5.4-mini: 33/56 feasible, mean 34.9

## Why opus stopped

All 4 opus batch workers hit:

```
400 {'type': 'error', 'error': {'type': 'invalid_request_error',
 'message': 'Your credit balance is too low to access the Anthropic API.
  Please go to Plans & Billing to upgrade or purchase credits.'}}
```

`eval_harness.run_local.main` breaks the row loop on `looks_like_billing_error` — so each worker wrote one error-stub JSON and exited. That left 4 stub files that need to be rerun in addition to the 18 never-attempted rows.

## 22 rows that need rerun once credits land

Saved at `/tmp/frontier-sweep/opus-rerun-ids.txt`:

```
cjs_hard_seed10
cjs_hard_seed7
graphcol_hard_seed10
graphcol_hard_seed4
graphcol_hard_seed7
mwis_hard_seed13
mwis_hard_seed5
mwis_hard_seed9
portfolio_hard_seed20
portfolio_hard_seed24
portfolio_hard_seed25
portfolio_hard_seed27
portfolio_hard_seed39
portfolio_medium_seed14
portfolio_medium_seed20
portfolio_medium_seed21
portfolio_medium_seed26
portfolio_medium_seed29
portfolio_medium_seed38
portfolio_medium_seed41
ve_hard_seed10
ve_hard_seed7
```

Stubs among these (must be overwritten, not skipped): `cjs_hard_seed7`, `portfolio_medium_seed20`, `portfolio_medium_seed38`, `ve_hard_seed7`. `run_local` writes `<id>.json` unconditionally so a bare rerun will overwrite them.

## Relaunch command once credits land

```bash
cd /Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission
nohup python -m eval_harness.run_local \
  --model claude-opus-4.6 \
  --ids @/tmp/frontier-sweep/opus-rerun-ids.txt \
  > /tmp/frontier-sweep/logs/sweep-opus-rerun.log 2>&1 &
```

Or split into 2-3 parallel batches of ~8 rows each by re-chunking that id file — same pattern as the original batches under `/tmp/frontier-sweep/*_batch*.txt`.

## Per-row data is on origin

An auto-commit at 10:27 AEST (`a261318`) and subsequent commits swept up every completed frontier result. `git rev-list origin/main..HEAD = 0`. Nothing of the frontier sweep is left only in the working tree — all 38 opus + 56 gemini-3-pro + 56 gpt-5.4 result JSONs are on origin. Also committed:
- `kaggle_submission/eval_harness/local_llm.py` (frontier model slugs + MODELS_WITHOUT_TEMPERATURE)
- `voicetree-16-4/frontier-sweep-in-progress.md`

## Notable paths

- Frontier per-row results: `kaggle_submission/results/runs/{claude-opus-4.6,gemini-3-pro-preview,gpt-5.4}/<id>.json`
- Non-frontier baselines: `kaggle_submission/results/full/<id>/<model>.json`
- ID intersection: `/tmp/frontier-sweep/ids.txt` (56 rows)
- Opus rerun list: `/tmp/frontier-sweep/opus-rerun-ids.txt` (22 rows)
- Sweep logs: `/tmp/frontier-sweep/logs/sweep-*.log`
- Aggregation script: `/tmp/frontier-sweep/aggregate.py`
- Parent in-progress node: `voicetree-16-4/frontier-sweep-in-progress.md`

### NOTES

- Opus credit exhaustion happened mid-sweep — the 38 files on disk include both real completions and 4 error stubs. Aggregation must treat the stubs as missing, not present, or mean_score gets dragged toward 0.
- Gemini 3 Pro at thinking_level=low and GPT-5.4 at default reasoning both use decision_stop after 1-2 turns — mean scores are a floor, not a ceiling, for those models.
- Anthropic billing portal: https://console.anthropic.com — look for the key labeled 'anthropic' in `llm keys list`.
- Do NOT commit metabench/kaggle.json (secrets) or the PNG files at metabench root when committing — they're unrelated and may contain credentials.

[[task_1776378788819ik5]]
