---
color: blue
isContextNode: false
agent_name: Ben
status: claimed
---
# 1A: Source Data and Preprocessing

Audit source dataset locations, naming expectations, and loader/preprocessing helpers used before inference.

Focus:
- Repository paths containing raw or canonical input datasets.
- Filename or directory conventions expected by loaders.
- Data-loading, normalization, or preprocessing helpers used prior to forecasting.

## Findings

- Local source-data locations: under [ForecastBench](/Users/lochlan/voicetree-evals/ForecastBench), the only observable top-level items are [.codex](/Users/lochlan/voicetree-evals/ForecastBench/.codex), [.voicetree](/Users/lochlan/voicetree-evals/ForecastBench/.voicetree), [voicetree-8-4](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4), and [.mcp.json](/Users/lochlan/voicetree-evals/ForecastBench/.mcp.json). There is no checked-out ForecastBench source tree, and no local `data/`, `datasets/`, `inputs/`, or similar benchmark-owned directories to inspect.
- Filename and directory conventions: because the local workspace contains no benchmark code, schemas, or dataset assets, there are no repository-grounded filename conventions to extract for raw or canonical inputs. The request note [1775618897236Woz.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/1775618897236Woz.md) only points to the public website and GitHub repo; it does not mirror any local path or naming contract.
- Loader and preprocessing helpers: there are no local ForecastBench `*.py`, `*.R`, `*.ipynb`, or shell scripts in this workspace, so there is no inspectable loader, normalizer, or preprocessing helper used before inference. This matches the broader repo audit in [forecastbench-1b-1b-data-and-results-pipeline-audit.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-1b-1b-data-and-results-pipeline-audit.md), which found no preprocessing or update flow code under the current folder.
- Workspace context: [forecastbench-1b-1a-layout-and-environment-audit.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-1b-1a-layout-and-environment-audit.md) shows this folder is an evaluation/orchestration workspace rather than the actual benchmark checkout. The current git root is [../.git](/Users/lochlan/voicetree-evals/.git), not `ForecastBench/`, so repo-relative data paths from the upstream project cannot be derived from local files here.
- Non-local clue only: the broader official-source audit [forecastbench-1a-official-sources-audit-apr-2026.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-1a-official-sources-audit-apr-2026.md) references published question sets in `forecastbench-datasets/datasets/question_sets` with `YYYY-MM-DD-llm.json` naming. That is useful context for future work, but it is not backed by a local repository checkout or local loader code in this workspace.

## Practical Conclusion

There is no local repository evidence for source dataset locations, filename expectations, or preprocessing helpers because the ForecastBench codebase is not present in this workspace. The only defensible audit result for this node is that the required source tree, data directories, and pre-inference code are all missing locally.

## Blockers

- Missing ForecastBench source checkout, including any package/module structure that would define canonical input paths.
- Missing local datasets, schemas, or cached question-set files.
- Missing loader and preprocessing code that would reveal naming expectations or normalization steps.
- Missing update/fetch scripts that would normally materialize intermediate benchmark inputs.

## Recommended Next Step

Populate [ForecastBench](/Users/lochlan/voicetree-evals/ForecastBench) with the actual upstream repository referenced in [1775618897236Woz.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/1775618897236Woz.md), then rerun this node against the real source tree so the audit can name concrete dataset paths, filename conventions, and preprocessing helpers.

[[forecastbench-1b-1b-1a-phase-1]]
