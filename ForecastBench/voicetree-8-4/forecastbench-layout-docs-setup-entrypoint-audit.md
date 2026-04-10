---
color: blue
isContextNode: false
agent_name: Emi
status: claimed
---
# 1B: Setup Workflow and Entrypoint Audit

Audit status: blocked by a missing ForecastBench source checkout.

The local `ForecastBench/` folder exposes a Voicetree/Codex orchestration workspace rather than the benchmark repository itself, so there are no benchmark setup instructions, package-manager clues, or runnable entrypoints to trace from local files.

## Evidence

- The root of [ForecastBench](/Users/lochlan/voicetree-evals/ForecastBench) contains only [.codex](/Users/lochlan/voicetree-evals/ForecastBench/.codex), [.mcp.json](/Users/lochlan/voicetree-evals/ForecastBench/.mcp.json), [.voicetree](/Users/lochlan/voicetree-evals/ForecastBench/.voicetree), and [voicetree-8-4](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4). No top-level source packages, runner folders, data folders, or install docs are present.
- A workspace-wide scan found no local benchmark manifests or runner files under [ForecastBench](/Users/lochlan/voicetree-evals/ForecastBench): no `README*`, `pyproject.toml`, `requirements*.txt`, `environment*.yml`, `setup.py`, `setup.cfg`, `package.json`, `Makefile`, `*.py`, `*.sh`, `*.R`, `*.ipynb`, or `*.jl`.
- The only executable-style instruction note surfaced locally is [run_me.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/run_me.md), which describes spawning Voicetree agents to graph a codebase rather than installing or running ForecastBench.
- The only concrete environment configuration files are [.mcp.json](/Users/lochlan/voicetree-evals/ForecastBench/.mcp.json) and [.codex/config.toml](/Users/lochlan/voicetree-evals/ForecastBench/.codex/config.toml). Both point to a local MCP server on `127.0.0.1:3001` / `localhost:3001`, so the observable runtime assumptions are for Voicetree orchestration rather than ForecastBench execution.
- The intent note [1775618897236Woz.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/1775618897236Woz.md) references `forecastbench.org` and `github.com/forecastingresearch/forecastbench`, which is the clearest local clue that the real benchmark materials are expected from upstream sources rather than being checked into this workspace.
- `git -C /Users/lochlan/voicetree-evals/ForecastBench rev-parse --show-toplevel` resolves to `/Users/lochlan/voicetree-evals`, so [ForecastBench](/Users/lochlan/voicetree-evals/ForecastBench) is currently an untracked subdirectory inside a different parent repository rather than its own ForecastBench checkout.

## Audit Findings

- Setup instructions and documented commands: none exist locally for ForecastBench itself. The only instruction-like files are Voicetree notes under [voicetree-8-4](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4).
- Script entrypoints, package manager clues, and runnable folders: none are present locally. There is no repo-grounded way to infer command order, CLI flags, environment variables, or working-directory assumptions for the benchmark.
- Documentation ambiguity: the folder name `ForecastBench` and the upstream references in [1775618897236Woz.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/1775618897236Woz.md) suggest benchmark work, but the visible local files are only orchestration artifacts. Treating this folder as a runnable benchmark checkout would be a false assumption.
- Stale or incomplete local workflow surface: because the source tree is absent, any setup or execution guidance derived from this workspace alone would be speculative.

## Blocker

To complete a real setup-workflow and entrypoint audit, the upstream ForecastBench repository referenced in [1775618897236Woz.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/1775618897236Woz.md) needs to be cloned or mounted into this workspace first.

[[forecastbench-layout-docs-phase-1]]
