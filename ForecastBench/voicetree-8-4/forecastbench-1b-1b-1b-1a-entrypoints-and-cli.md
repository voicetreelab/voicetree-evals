---
color: blue
isContextNode: false
agent_name: Bob
status: claimed
---
# 1A: Forecast Entrypoints and CLI Audit

Audit status: blocked by a missing ForecastBench source checkout.

The local `ForecastBench/` folder currently contains Voicetree/Codex orchestration files rather than benchmark source code, so there are no forecast-generation entrypoints or CLI surfaces to trace from this workspace.

## Evidence

- Root-level files observed under `/Users/lochlan/voicetree-evals/ForecastBench`: `.codex/`, `.mcp.json`, `.voicetree/`, and `voicetree-8-4/`.
- [.mcp.json](/Users/lochlan/voicetree-evals/ForecastBench/.mcp.json) only configures a local Voicetree MCP server at `http://127.0.0.1:3001`.
- [.codex/config.toml](/Users/lochlan/voicetree-evals/ForecastBench/.codex/config.toml) only points Codex at `http://localhost:3001/mcp`.
- [run_me.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/run_me.md) is a graph-orchestration note about spawning agents to map a codebase, not a forecast runner or wrapper.
- `git -C /Users/lochlan/voicetree-evals/ForecastBench rev-parse --show-toplevel` resolves to `/Users/lochlan/voicetree-evals`, and `git -C /Users/lochlan/voicetree-evals/ForecastBench status --short` shows `?? ./`, which means this folder is an untracked workspace directory inside the parent repo instead of a checked-out ForecastBench codebase.
- A workspace-wide search found no Python modules, package manifests, benchmark CLI definitions, or forecast scripts under the local `ForecastBench/` path.

## Audit Findings

- Forecast script entrypoints and wrapper scripts: none present locally.
- Required positional or flag arguments: not discoverable without the missing source files.
- Model, dataset, and task selection controls: not discoverable without the missing source files.
- Runtime assumptions such as checkpoints, config files, API keys, or working-directory expectations: not discoverable without the missing source files.

## Blocker

To complete the requested entrypoint and CLI audit, the actual ForecastBench repository contents need to be mounted into this workspace or the correct local path needs to be provided.
[[forecastbench-1b-1b-1b-phase-1]]

[[forecastbench-1b-1b-1b-phase-1]]
