# Local parity harness

`eval_harness/` runs the production `harness.runner.run_instance()` loop against local models exposed through the `llm` CLI.

## Purpose

- Keep the Kaggle-vs-local divergence minimal.
- Reuse the real production prompt, parser, verifier, scoring, and stop/counterfactual logic.
- Swap only the model provider seam: Kaggle uses `kaggle_benchmarks`; local runs use `LocalLLM`.

## Files

- `local_llm.py`: duck-typed adapter exposing `.prompt(text, temperature=0) -> str`
- `run_local.py`: CLI for replaying rows from `questions.jsonl`
- `__init__.py`: package export

## Usage

Run from `kaggle_submission/` so imports resolve:

```bash
/Users/bobbobby/repos/voicetree-public/.venv/bin/python -m eval_harness.run_local --model gemini-flash-latest --ids all
```

You can also target a subset:

```bash
/Users/bobbobby/repos/voicetree-public/.venv/bin/python -m eval_harness.run_local --model gemini-flash-latest --ids cjs_medium_seed1,graphcol_medium_seed1
/Users/bobbobby/repos/voicetree-public/.venv/bin/python -m eval_harness.run_local --model gemini-flash-latest --ids @ids.txt
```

Results are written to `results/runs/{model_slug}/{id}.json`, where `model_slug` only replaces `/` with `_`.

## Notes

- `LocalLLM` shells to `llm -m <model> -s <system> --option temperature <t> <user>`.
- Non-zero CLI exits surface as `RuntimeError` text in the saved result JSON.
- `run_local.py` stops a model early only on obvious billing/quota errors. Per-row wall is governed by the production harness (`TOTAL_BUDGET_S=1800`).
