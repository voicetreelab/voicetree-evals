---
color: blue
isContextNode: false
agent_name: Ivan
---
# Eval harness + prompt hardening — new subtree, no collisions

New `eval_harness/` subtree with LocalLLM + run_local CLI. Amend `harness/prompt.py` with few-shot + end-of-user-prompt format reminder. 3-model smoke on 1 question gates the 45-run eval.

## New subtree

`metabench/kaggle_submission/eval_harness/`

| File | Purpose |
|---|---|
| `local_llm.py` | `LocalLLM` class (see parity sub-node) |
| `run_local.py` | `python -m eval_harness.run_local --model <m> --ids <csv|@file> --out results/runs/<m>/` |
| `README.md` | Documents parity gap + replay instructions |
| `__init__.py` | package marker |

`run_local.py` loads `questions.jsonl`, filters by `--ids`, builds a fresh `LocalLLM(model, build_system_prompt())` per row, calls `run_instance(llm, instance, cls, difficulty, seed, gold_objective, baseline_objective, value_cap, components=row.get("components"))`, writes one JSON per row under `results/runs/{model}/{id}.json`.

## Prompt hardening (Ayu constraint #2)

Land BEFORE the 3-model smoke:
1. **Few-shot exemplar** in `build_turn1_prompt()` + `build_exec_prompt()` showing one canonical `BEST_GUESS: {...}` line
2. **End-of-user-prompt format reminder:** "Your reply MUST end with a line starting `BEST_GUESS: ` followed by JSON matching the schema. No code fences."
3. **temperature=0** — already wired in `runner.py:_prompt_once`

**NO fallback JSON parser added.** `harness/protocol.parse_best_guess` stays strict. Gia's `_fallback_last_json_object` stays confined to `scripts/verify_pipeline.py` (dev-time tool).

## Gating smoke

A-harness Codex runs the 3-model smoke on ONE question (e.g. `cjs_medium_seed1`) before returning. Prints per-model `parse_method` + `feasible` + `score`.

**Gate criteria:** all 3 models emit labelled `BEST_GUESS:` AND produce `feasible=True` AND `score >= 0`.

- **If PASS:** Ivan spawns 3 eval workers.
- **If FAIL on 1 model:** user decision — retry with tweaked prompt, or accept n=1 on 2 models.
- **If FAIL on ≥2 models:** regress, consider fallback parser, surface to user.

## Eval subset (answer to open Q2)

```
solo:      6 classes × 2 difficulties × seed=1   = 12
portfolio: seeds 1, 2, 3                         =  3
                                         total  = 15
```

Stratification: every (class, difficulty) cell gets n=1; portfolios get n=3 to give some within-class signal.

## Writer & outputs

- **Codex:** 1 (A-harness), leaf
- **Writes:** `eval_harness/*.py` (new), `harness/prompt.py` (amend), 3 smoke result files under `results/runs/{model}/cjs_medium_seed1.json`
- **Budget:** ~45-60 min incl. smoke run


phase 2 [[factory-a-eval-plan-v1]]
