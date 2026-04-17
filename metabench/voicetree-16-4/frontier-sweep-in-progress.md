---
color: blue
isContextNode: false
agent_name: Eve
---
# Frontier-model sweep — in-progress (10 parallel batches live)

Sweeping 3 frontier models (claude-opus-4.6, gemini-3-pro-preview, gpt-5.4) across the 56-row intersection of results/full × questions.jsonl. Pilots + settings tuning done; full sweep running as 10 parallel batches of 15 rows. Results land per-row at results/runs/<model>/<id>.json as they finish. Partial data already shows frontier models hitting higher feasibility than non-frontier baselines.

## Scope

Compare frontier vs non-frontier LLMs on identical rows. Intersection of `kaggle_submission/results/full/` ids and current `kaggle_submission/questions.jsonl` = **56 rows** (20 portfolio + 36 solo). ID list saved to `/tmp/frontier-sweep/ids.txt`.

## Frontier model slugs + settings (final, after tuning)

| Model | llm slug | Flags | Non-frontier baseline |
|---|---|---|---|
| Claude Opus 4.6 | `claude-opus-4.6` | `--option max_tokens 40000` | claude-sonnet-4.6 |
| Gemini 3 Pro | `gemini-3-pro-preview` | `--option max_output_tokens 40000 --option thinking_level low` | gemini-flash-latest |
| GPT-5.4 | `gpt-5.4` | no temperature flag (reasoning model rejects it), no reasoning_effort | gpt-5.4-mini |

Wired into `kaggle_submission/eval_harness/local_llm.py` via `MODEL_MAX_TOKENS_FLAGS` + new `MODELS_WITHOUT_TEMPERATURE` set.

## Why `thinking_level=low` for Gemini 3 Pro

Pilots at default thinking and `thinking_level=high` both blew the 1800s wall budget: plan turn alone took 178s, and the model then emits `time_budget_s=60` for exec turns which it cannot meet with deep thinking → exec timeout → stop_reason=`wall_budget` after 1 exec turn. `thinking_level=low` brings plan to ~7s and lets the model actually progress. See `/tmp/frontier-sweep/logs/pilot-gemini3*.log`.

## Why GPT-5.4 without reasoning_effort

Pilot with `reasoning_effort=high`: plan 294s + exec 420s timeout → 1 exec turn, wall_budget blown, score -7.15. At default reasoning runs in ~40s/row with decision_stop=True. Non-frontier `gpt-5.4-mini` also uses default reasoning, so apples-to-apples.

## Why Opus 4.6 has no thinking flag

The `llm` CLI's Anthropic plugin does not expose extended thinking. Default mode runs fine — Opus pushes through all 10 exec turns at ~30s per turn, ~350-400s total per row.

## Parallelization — 10 batches live

After user direction to parallelize: killed the 3 serial sweeps, partitioned remaining ids into **batches of 15**, relaunched as 10 concurrent workers at 09:14 AEST.

| Model | Remaining at kill | Batches |
|---|---|---|
| claude-opus-4.6 | 54 | 4 (15+15+15+9) |
| gemini-3-pro-preview | 33 | 3 (15+15+3) |
| gpt-5.4 | 38 | 3 (15+15+8) |

Batch id files: `/tmp/frontier-sweep/{model}_batch{i}.txt`. Logs: `/tmp/frontier-sweep/logs/sweep-{model}_batch{i}.log`.

## Live counts as of 09:14 AEST

- opus: 2/56
- gemini3: 23/56
- gpt-5.4: 18/56

## Partial aggregation (from completed rows only)

From `/tmp/frontier-sweep/aggregate.py`:

```
FRONTIER  claude-opus-4.6       present=1/56   feasible=1/56   mean_score=72.33 (n=1)
FRONTIER  gemini-3-pro-preview  present=8/56   feasible=8/56   mean_score=36.46
FRONTIER  gpt-5.4               present=8/56   feasible=8/56   mean_score=33.68
NON-FRONT claude-sonnet-4.6     present=56/56  feasible=19/56  mean_score=35.55
NON-FRONT gemini-flash-latest   present=56/56  feasible=32/56  mean_score=48.70
NON-FRONT gpt-5.4-mini          present=56/56  feasible=33/56  mean_score=34.93
```

Too early to draw conclusions: frontier numbers are over solo classes only (all 8 completed rows are solo, no portfolio yet). But early signal is **100% feasibility on completed solo rows** for all 3 frontier models, which is a strong contrast to ~55% feasibility for non-frontier baselines.

## Notable paths

- Frontier per-row results: `kaggle_submission/results/runs/{claude-opus-4.6,gemini-3-pro-preview,gpt-5.4}/<id>.json`
- Non-frontier baselines: `kaggle_submission/results/full/<id>/<model>.json`
- ID intersection list: `/tmp/frontier-sweep/ids.txt` (56 rows)
- Batch id files: `/tmp/frontier-sweep/<model>_batch<i>.txt`
- Logs: `/tmp/frontier-sweep/logs/`
- Aggregation script: `/tmp/frontier-sweep/aggregate.py`

## Learnings for next agent

**1. What did you try first, and why did you change approach?**
First attempt used `reasoning_effort=high` (gpt-5.4) and `thinking_level=high` (gemini-3-pro-preview) to give frontier models their best shot. Both blew the 1800s wall budget on the pilot row — plan turn alone ate 180-300s, then the model self-assigned tight `time_budget_s=60` exec budgets it could not meet with deep thinking. Dropped both to default/low for apples-to-apples with non-frontier baselines.

**2. What will a future agent get wrong?**
(a) `gpt-5.4` is a reasoning model: it rejects any `--option temperature <x>` even when <x>=0.0. Harness error: `'temperature' does not support 0.0 with this model. Only the default (1) value is supported.` Fix: add model to `MODELS_WITHOUT_TEMPERATURE` so the temperature flag is skipped. (b) `gemini-3-pro-preview` with `thinking_level` omitted defaults to deep thinking — NOT off. You must explicitly pass `thinking_level=low` to get fast behavior. (c) The harness emits `time_budget_s` in the model's plan; thinking models under-budget themselves and blow their own timers, so wall_budget stops dominate rather than decision_stop.

**3. What should a successor believe without repeating reasoning?**
At the current wall budget (1800s total, 300s plan budget, 600s exec cap, 10 exec turn limit), frontier models with high reasoning cannot fit a useful number of turns and collapse to wall_budget stops with 1 exec turn. To get meaningful frontier data inside the existing harness, reasoning depth must be capped. Frontier-vs-non-frontier comparison is therefore implicitly `default-reasoning-frontier` vs `default-reasoning-non-frontier`. A harness-level extension to multiply the wall budget for frontier models would be needed to compare at high reasoning.

## Status

In progress — expected completion ~10:30-11:00 AEST (Opus is long pole; each batch handles 9-15 rows sequentially at ~6 min/row, so longest batch = ~90 min).

## DIFF

```
--- a/kaggle_submission/eval_harness/local_llm.py
+++ b/kaggle_submission/eval_harness/local_llm.py
@@ -5,11 +5,15 @@ import subprocess
 from harness.protocol import PLAN_TURN_BUDGET_S, SUBTASK_BUDGET_S
 
 _TIMEOUT_CAP_S = max(PLAN_TURN_BUDGET_S, SUBTASK_BUDGET_S) + 30
 MODEL_MAX_TOKENS_FLAGS: dict[str, list[str]] = {
     "claude-sonnet-4.6": ["--option", "max_tokens", "40000"],
     "gemini-flash-latest": ["--option", "max_output_tokens", "40000"],
     "gpt-5.4-mini": [],
+    "claude-opus-4.6": ["--option", "max_tokens", "40000"],
+    "gemini-3-pro-preview": ["--option", "max_output_tokens", "40000", "--option", "thinking_level", "low"],
+    "gpt-5.4": [],
 }
+MODELS_WITHOUT_TEMPERATURE: set[str] = {"gpt-5.4"}
 
 
 class LocalLLM:
@@ -21,15 +25,15 @@ class LocalLLM:
     def prompt(self, text: str, *, temperature: float = 0.0) -> str:
         cmd = [
             "llm",
             "-m",
             self.model,
             "-s",
             self.system_prompt,
-            "--option",
-            "temperature",
-            format(float(temperature), "g"),
         ]
+        if self.model not in MODELS_WITHOUT_TEMPERATURE:
+            cmd.extend(["--option", "temperature", format(float(temperature), "g")])
         cmd.extend(MODEL_MAX_TOKENS_FLAGS.get(self.model, []))
         cmd.append(text)
         try:
```

## Complexity: low

Three small additions to an existing flag registry + one conditional in prompt() — all contained within local_llm.py.

## Files Changed

- kaggle_submission/eval_harness/local_llm.py

### NOTES

- 10 parallel workers writing to shared results/runs/<model>/<id>.json. Partition is disjoint (each batch file has a unique id subset), so no write races.
- Gemini 3 Pro's non-frontier baseline is gemini-flash-latest — a much smaller sibling. Gemini 3 Pro at thinking_level=low may still significantly outperform flash; watch for that signal.
- Aggregation script works off whatever is present at run-time; safe to execute mid-sweep for intermediate headlines.
- stranded-llm-cli-processes visible in ps -ef that aren't mine belong to Eva's concurrent Portfolio fix sweep. Do not kill them.

[[task_1776378788819ik5]]
