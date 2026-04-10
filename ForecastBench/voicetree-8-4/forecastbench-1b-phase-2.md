---
color: green
isContextNode: false
agent_name: Amit
---
# Phase 2: Execution Outline Synthesis

Local blocker first: the current workspace at [ForecastBench](/Users/lochlan/voicetree-evals/ForecastBench) is not a checkout of the upstream source repo. The runnable benchmark code lives in the public GitHub repository, while this local folder only contains Voicetree/Codex artifacts documented in [forecastbench-1b-1a-layout-and-environment-audit.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-1b-1a-layout-and-environment-audit.md) and [forecastbench-1b-1b-data-and-results-pipeline-audit.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-1b-1b-data-and-results-pipeline-audit.md).

## Upstream Repo Shape

- Root orchestration is centered on [`Makefile`](https://github.com/forecastingresearch/forecastbench/blob/main/Makefile), which fans out into source-specific jobs under [`src/questions`](https://github.com/forecastingresearch/forecastbench/tree/main/src/questions), metadata jobs under [`src/metadata`](https://github.com/forecastingresearch/forecastbench/tree/main/src/metadata), question-set curation under [`src/curate_questions`](https://github.com/forecastingresearch/forecastbench/tree/main/src/curate_questions), baseline forecasters under [`src/base_eval`](https://github.com/forecastingresearch/forecastbench/tree/main/src/base_eval), resolution under [`src/resolve_forecasts`](https://github.com/forecastingresearch/forecastbench/tree/main/src/resolve_forecasts), leaderboard generation under [`src/leaderboard`](https://github.com/forecastingresearch/forecastbench/tree/main/src/leaderboard), and deployment orchestration under [`src/nightly_update_workflow`](https://github.com/forecastingresearch/forecastbench/tree/main/src/nightly_update_workflow).
- The repo expects submodules from [`.gitmodules`](https://github.com/forecastingresearch/forecastbench/blob/main/.gitmodules): `utils`, `experiments/stability-analysis`, and `experiments/ranking-simulation`.
- The public dev setup in [`README.md`](https://github.com/forecastingresearch/forecastbench/blob/main/README.md) is: `git clone --recurse-submodules`, `cp variables.example.mk variables.mk`, `make setup-python-env`, and `source .venv/bin/activate`.

## Setup Prerequisites Inferred From Code

1. Clone the real repo with submodules, not just this Voicetree workspace.
2. Create `variables.mk` from [`variables.example.mk`](https://github.com/forecastingresearch/forecastbench/blob/main/variables.example.mk). The public example leaves every important bucket/project/service-account value blank, so real deployment values are private.
3. Run root environment bootstrap from [`Makefile`](https://github.com/forecastingresearch/forecastbench/blob/main/Makefile): `make setup-python-env` and `make install-requirements`. Root `requirements.txt` only installs lint tooling; runnable components also have per-directory `requirements.txt` files.
4. Provide GCP access used across the codebase: Cloud Run, Cloud Storage, Secret Manager, and service-account permissions referenced in [`src/helpers/env.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/helpers/env.py) and [`src/helpers/keys.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/helpers/keys.py).
5. Provide secrets that are not public in the repo: model API keys, source API keys, `API_GITHUB_DATASET_REPO_URL`, and optionally `API_GITHUB_SSH_ID_RSA` for publishing question sets and public-release artifacts.
6. For local function-style execution, the README’s pattern is `eval $(cat path/to/variables.mk | xargs) python main.py`, but several jobs also require Cloud Run env vars such as `CLOUD_RUN_TASK_INDEX`, `FORECAST_DUE_DATE`, and `TEST_OR_PROD`.

## Ordered Execution Outline

1. Refresh the question bank.
   Files: [`Makefile`](https://github.com/forecastingresearch/forecastbench/blob/main/Makefile), [`src/questions/manifold/fetch/main.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/questions/manifold/fetch/main.py), [`src/questions/manifold/update_questions/main.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/questions/manifold/update_questions/main.py), [`src/helpers/data_utils.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/helpers/data_utils.py).
   Flow: `make questions` or per-source targets such as `make manifold`, `make metaculus`, `make fred`.
   Artifacts: source fetch/update jobs write `{source}_fetch.jsonl`, `{source}_questions.jsonl`, and `{source}_resolutions.jsonl` into `QUESTION_BANK_BUCKET`.

2. Tag and validate questions.
   Files: [`src/metadata/tag_questions/main.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/metadata/tag_questions/main.py), [`src/metadata/validate_questions/main.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/metadata/validate_questions/main.py).
   Flow: `make metadata`.
   Artifacts: `question_metadata.jsonl` in `QUESTION_BANK_BUCKET`, populated partly by LLM classification/validation calls.

3. Create and publish the current question set.
   Files: [`src/curate_questions/create_question_set/main.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/curate_questions/create_question_set/main.py), [`src/curate_questions/publish_question_set/main.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/curate_questions/publish_question_set/main.py), [`src/helpers/question_curation.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/helpers/question_curation.py).
   Flow: `make curate-questions`.
   Artifacts: the curated `YYYY-MM-DD-llm.json` is written to `QUESTION_SETS_BUCKET`, then published to the separate `forecastbench-datasets` repo as `datasets/question_sets/{date}-llm.json` plus `latest-llm.json`.

4. Generate ForecastBench-owned baselines.
   Naive/dummy path:
   Files: [`src/base_eval/naive_and_dummy_forecasters/main.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/base_eval/naive_and_dummy_forecasters/main.py), [`src/helpers/data_utils.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/helpers/data_utils.py).
   Flow: `make naive-and-dummy-forecasters`.
   Artifacts: writes forecast-set JSONs like `{date}.ForecastBench.naive-forecaster.json` to `/tmp`, then uploads to `FORECAST_SETS_BUCKET/{date}/...`.
   LLM baseline path:
   Files: [`src/base_eval/llm_baselines/manager/main.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/base_eval/llm_baselines/manager/main.py), [`src/base_eval/llm_baselines/worker/main.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/base_eval/llm_baselines/worker/main.py), [`src/helpers/model_eval.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/helpers/model_eval.py), [`src/helpers/question_sets.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/helpers/question_sets.py).
   Flow: `make llm-baselines`. The manager reads the latest published question set and triggers the worker Cloud Run job. The worker creates intermediate JSONL files under `/tmp/{prompt_type}/...`, merges them into `/tmp/{prompt_type}/final_submit[_test]/`, and uploads final forecast JSONs to `FORECAST_SETS_BUCKET/{forecast_due_date}/...`.

5. Resolve and normalize forecast files for scoring.
   Files: [`src/resolve_forecasts/main.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/resolve_forecasts/main.py), [`src/helpers/resolution.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/helpers/resolution.py).
   Flow: `make resolve`.
   Artifacts: reads raw forecast-set JSONs from `FORECAST_SETS_BUCKET/{date}/...`, validates schema, expands/imputes missing forecasts, joins question resolutions, and uploads processed forecast files to `PROCESSED_FORECAST_SETS_BUCKET/{date}/...`. It also writes resolution sets to `PUBLIC_RELEASE_BUCKET/datasets/resolution_sets`.

6. Build leaderboards and site outputs.
   Files: [`src/leaderboard/main.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/leaderboard/main.py), [`src/www.forecastbench.org`](https://github.com/forecastingresearch/forecastbench/tree/main/src/www.forecastbench.org), [`src/nightly_update_workflow/manager/main.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/nightly_update_workflow/manager/main.py).
   Flow: `make leaderboards` and `make website`, or the full orchestrated nightly path.
   Artifacts: leaderboard HTML/CSV files and site assets written to public-release buckets and published website content.

## What An External Participant Can Realistically Use

- The public repo exposes the forecast file schema and ForecastBench’s internal baseline pipeline, but it does not provide a turnkey external submission CLI.
- The public submission path is documented in the wiki page [How-to-submit-to-ForecastBench](https://github.com/forecastingresearch/forecastbench/wiki/How-to-submit-to-ForecastBench): download the released question set from `forecastbench-datasets`, generate a forecast-set JSON locally, and upload it to the GCP folder assigned by ForecastBench before the deadline.
- Repo code that consumes forecast files starts at [`read_forecast_file()`](https://github.com/forecastingresearch/forecastbench/blob/main/src/helpers/resolution.py) and expects top-level keys `organization`, `model`, `model_organization`, `question_set`, and `forecasts`, with forecast rows containing `id`, `source`, `forecast`, `resolution_date`, and optional `reasoning`.

## Unresolved Gaps

- This local workspace cannot run any of the above until the actual upstream repo is checked out here.
- The public repo does not disclose real `variables.mk` values, bucket names, uploader folders, or service-account bindings.
- Publishing question sets and public artifacts depends on private GitHub/GCP secrets in [`src/helpers/keys.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/helpers/keys.py).
- The LLM baseline manager is not a purely local entrypoint; it dispatches Cloud Run workers through [`src/helpers/cloud_run.py`](https://github.com/forecastingresearch/forecastbench/blob/main/src/helpers/cloud_run.py).
- The bridge from an external participant’s assigned upload folder to internal `FORECAST_SETS_BUCKET` processing is not fully documented in the public repo, so that handoff remains an operational black box.

[[forecastbench-1b-phase-1]]
