# Option B: `kaggle kernels push`

Use this path to scaffold and update one notebook per benchmark task. It is the right packaging model for Kaggle submission, but fresh CLI-created slugs still have a known `.run.json` gap.

## Workflow

From the repo root:

```bash
source .venv/bin/activate
python option_b_push/new_task.py my-task-slug
$EDITOR option_b_push/tasks/my-task-slug/kernel.py
python option_b_push/push_and_wait.py my-task-slug
```

`new_task.py` creates:

- `option_b_push/tasks/<slug>/kernel.py`
- `option_b_push/tasks/<slug>/kernel-metadata.json`
- `option_b_push/tasks/<slug>/kernel.ipynb`

`push_and_wait.py` regenerates the notebook, runs `kaggle kernels push`, polls kernel status, downloads output, and prints any `.task.json` or `.run.json` artifacts it finds.

## Current status

- `KAGGLE_API_TOKEN` is the correct env var for new-format `KGAT_...` tokens.
- The notebook must install `protobuf>=5.29.6` before importing `kaggle_benchmarks`.
- The run cell explicitly calls the registered task. `@kbench.task` only registers; it does not auto-run.
- Fresh slugs created only through `kaggle kernels push` currently produce `.task.json` but may miss `.run.json` because the benchmark runtime is not provisioned.

## Practical recommendation

If you already have a benchmark task slug created from Kaggle's "Create New Benchmark Task" UI, use this folder to push code updates to that slug. If you need a working end-to-end run today, use Option A.

## Example

See `examples/metacog_format_recall_v1/` for a real task and matching metadata.
