---
color: blue
isContextNode: false
agent_name: Ari
status: claimed
---
# 1B: Dependency and Environment Drift Audit

Inspect dependency manifests, environment files, and version-management clues to identify the active runtime/tooling assumptions and any mismatch between repository documentation and the current local workspace.

Audit focus:
- Dependency manifests and lockfiles.
- Package managers and environment managers.
- Version assumptions expressed in config files or scripts.
- Workspace-local drift versus README/setup guidance where directly observable.

Deliverable:
- File-referenced findings only.
- No implementation changes.

[[forecastbench-layout-docs-deps-implementation-plan]]

## Findings

- No ForecastBench dependency manifests, lockfiles, or version-manager files are present in this workspace. The only root-level config files visible under `ForecastBench/` are [.mcp.json](/Users/lochlan/voicetree-evals/ForecastBench/.mcp.json) and [.codex/config.toml](/Users/lochlan/voicetree-evals/ForecastBench/.codex/config.toml); the only other version-like marker surfaced locally is [.voicetree/.version](/Users/lochlan/voicetree-evals/ForecastBench/.voicetree/.version). A workspace scan found no `package.json`, `pyproject.toml`, `requirements*.txt`, `environment*.yml`, `.python-version`, `.tool-versions`, `.nvmrc`, `.node-version`, or `.env*` files.
- The only explicit runtime/tooling assumptions expressed in local files are for Voicetree/Codex orchestration. [.mcp.json](/Users/lochlan/voicetree-evals/ForecastBench/.mcp.json) configures an MCP server at `http://127.0.0.1:3001/mcp`, [.codex/config.toml](/Users/lochlan/voicetree-evals/ForecastBench/.codex/config.toml) points Codex at `http://localhost:3001/mcp`, and [.voicetree/.version](/Users/lochlan/voicetree-evals/ForecastBench/.voicetree/.version) records Voicetree `2.9.16`.
- No benchmark-specific environment templates or setup docs are present locally. The only instruction-style document in the workspace is [run_me.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/run_me.md), and it describes generating a codebase graph rather than installing dependencies, setting environment variables, or running ForecastBench.
- The directly observable workspace drift is that this folder is not a checkout of the ForecastBench source repository. [1775618897236Woz.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/1775618897236Woz.md) assumes "python code and scripts" are available in `ForecastBench/`, but the visible local files are Voicetree/Codex artifacts and markdown nodes instead. The surrounding git repository is rooted at `/Users/lochlan/voicetree-evals`, and `ForecastBench/` is currently an untracked subdirectory there, so repo-relative install assumptions from the upstream project would not apply cleanly to this local layout.

## Practical Conclusion

As of 2026-04-08, the current `ForecastBench/` workspace does not expose a runnable ForecastBench environment. The only observable environment is the local Voicetree/Codex orchestration stack on MCP port `3001`; a real dependency or environment drift audit for ForecastBench itself is blocked until the actual upstream source checkout and its manifests are present locally.

## Blocking Gap

- To audit benchmark dependencies and env drift beyond the orchestration scaffolding above, the upstream ForecastBench repository referenced in [1775618897236Woz.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/1775618897236Woz.md) needs to be cloned or mounted into this workspace.
