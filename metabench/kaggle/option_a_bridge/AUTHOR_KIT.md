# Option A: live-kernel bridge

Use this path for fast development. `submit_task.py` sends one local task file to an already-running Kaggle notebook kernel, executes it there, and prints any newly generated `.task.json` and `.run.json`.

## Run a task

1. Keep a Kaggle benchmark notebook open so you have fresh `KAGGLE_JUPYTER_URL` and `KAGGLE_JUPYTER_TOKEN` values.
2. From the repo root:

```bash
source .venv/bin/activate
python option_a_bridge/submit_task.py examples/example_hle_metacog.py
```

The bridge prints:

- `status` / `passed`
- the registered task name and run id
- any generated `.task.json`
- any generated `.run.json`
- judge notes or wrapper tracebacks

## Caveats

- This path does not publish notebooks. It is for iteration, not final submission.
- `KAGGLE_JUPYTER_TOKEN` expires. Refresh it from the live notebook page if the bridge reports a rejected token.
- Runs serialize through one live kernel. If the kernel is busy, wait rather than forcing it.
- State can leak between runs because the same kernel stays alive. `submit_task.py` mitigates this, but fresh notebook restarts are still the cleanest reset.
