# Kaggle Community Benchmark Author Kit

2026-04-15: initial consolidation, pre-deadline. Fresh Option B slugs still have a `.run.json` gap, so use Option A for live pilot runs today.

This folder packages the working Kaggle Community Benchmark tooling into one standalone kit. It is for the Kaggle "Measuring Progress Toward AGI" hackathon and is designed to help a new agent or human go from local task authoring to Kaggle execution without re-deriving the workflow from old VoiceTree nodes.

## 1. What this is

This kit consolidates the working scripts, example tasks, and operational notes needed to author Kaggle Community Benchmark tasks without depending on the old `voicetree-13-4/kaggle-benchmark/` workspace. It includes one development path that runs against a live Kaggle kernel, one packaging path that builds notebook tasks for `kaggle kernels push`, a local smoke test, and example artifacts for both styles.

## 2. Two ways to run tasks

There are two ways to run tasks:

| Path | Best for | Iteration speed | Auth model | Parallelism | Submission-ready | Known status |
|------|----------|-----------------|------------|-------------|------------------|--------------|
| Option A: `option_a_bridge/` | Development and pilot spikes | Seconds | Live Kaggle notebook token + model proxy env | Low, one live kernel | No | Works end-to-end today, emits `.task.json` and `.run.json` |
| Option B: `option_b_push/` | Packaging one notebook per task | Minutes | Kaggle CLI token | Higher, one notebook per task | Yes in principle | Fresh CLI-created slugs emit `.task.json`; `.run.json` still missing |

Recommendation: use Option A to iterate on task logic and validate the benchmark signal. Use Option B when you need the final Kaggle notebook packaging, ideally against a benchmark slug created once from Kaggle's "Create New Benchmark Task" UI.

## 3. Prerequisites

- Kaggle account joined to the hackathon competition.
- `KAGGLE_API_TOKEN` set to a new-format `KGAT_...` token from Kaggle settings.
- `KAGGLE_USERNAME` set.
- For Option A only: `KAGGLE_JUPYTER_URL` and `KAGGLE_JUPYTER_TOKEN` from a live notebook session.
- For Option A only: `MODEL_PROXY_URL` and `MODEL_PROXY_API_KEY`. These are IP-locked to Kaggle's network, which is fine because execution happens on Kaggle's kernel.
- Python 3.11+.

## 4. Setup

```bash
cd ~/repos/voicetree-evals/metabench/kaggle
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`smoke_test.py` is a local non-LLM check that verifies the SDK import and task registration path:

```bash
python smoke_test.py
```

## 5. Option A workflow

Write exactly one `@kbench.task` in a local file under `examples/` or any other path. Then run:

```bash
python option_a_bridge/submit_task.py examples/example_hle_metacog.py
```

Expected output:

- task name, status, pass/fail
- any newly generated `.task.json`
- any newly generated `.run.json`
- judge notes and wrapper tracebacks if execution failed

This path is fast because it does not push notebook edits. The bridge injects your task source into an already-running Kaggle kernel over Jupyter channels and executes it there. The tradeoff is that the kernel is shared state: runs serialize, the token expires after a few hours, and stale imports can leak between iterations.

## 6. Option B workflow

```bash
python option_b_push/new_task.py my-task-slug
# edit option_b_push/tasks/my-task-slug/kernel.py
python option_b_push/push_and_wait.py my-task-slug
```

This scaffolds a notebook task directory, regenerates `kernel.ipynb`, pushes it with `kaggle kernels push`, polls status, downloads output, and prints any `.task.json` or `.run.json` artifacts.

Current caveat as of 2026-04-15: fresh slugs created only through the CLI still produce `.task.json` but may miss `.run.json`. The current diagnosis is that CLI-created kernels land on the standard Python image instead of Kaggle's benchmark runtime, so the model proxy env is missing even though the task registration path works. If you already have a benchmark task slug created from Kaggle's UI, this push workflow is still the right update path to test next.

## 7. Known gotchas

- In Option B notebooks, install `kaggle-benchmarks` and `protobuf>=5.29.6` before the first import. Kaggle's default runtime is one patch version behind.
- `@kbench.task` only registers a task. Execution still requires an explicit `Task.run()` call.
- `MODEL_PROXY_API_KEY` is IP-locked to Kaggle's network. Local laptops cannot use it directly.
- Option A runs through one live kernel, so task executions serialize and can leak state.
- Option B maps better to Kaggle's publishing model because each task is one notebook and one eventual "Save Task" entry.

## 8. Writing a new task

The easiest starting points are:

- `examples/example_hle_metacog.py` for a single-file bridge task.
- `examples/metacog_format_recall_v1/` for a notebook-packaged task.

`@kbench.task` functions can take either `() -> bool` or `(llm) -> bool`. Use `kbench.assertions.assert_true(...)` for hard checks and `kbench.assertions.assess_response_with_judge(...)` when you need an LLM judge.

## 9. Submission

There is no confirmed CLI path for the final "Save Task" action. After a pushed notebook finishes on Kaggle, open its notebook URL and click **Save Task** in the Kaggle UI.

## 10. Provenance

Option A originated from Ben's live-kernel bridge. Option B originated from Cho and Emi's `kaggle kernels push` flow, with Eva's follow-up diagnosis on the missing `.run.json` issue. This folder is the cleaned consolidation point for those threads.
