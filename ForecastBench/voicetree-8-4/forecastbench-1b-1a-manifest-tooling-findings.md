---
color: green
isContextNode: false
agent_name: Gia
---
# Manifest and Tooling Audit Findings

Audited the local `ForecastBench` workspace for manifests, lockfiles, package managers, and version pins. The directory contains only Voicetree/Codex orchestration files, so the only directly evidenced tooling assumptions are the local MCP/Voicetree endpoints rather than a runnable ForecastBench stack.

## Findings
- No dependency manifests or lockfiles are present anywhere under `/Users/lochlan/voicetree-evals/ForecastBench`: recursive scans returned no `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `pyproject.toml`, `requirements*.txt`, `poetry.lock`, `Pipfile*`, `Dockerfile`, `Makefile`, `.python-version`, `.nvmrc`, `.node-version`, `.tool-versions`, or `mise.toml`.
- No application or benchmark source files are present either: recursive scans returned no `*.py`, `*.R`, `*.ipynb`, `*.sh`, `*.jl`, `*.js`, or `*.ts` files under the local workspace.
- The workspace root contains only [.codex](/Users/lochlan/voicetree-evals/ForecastBench/.codex), [.voicetree](/Users/lochlan/voicetree-evals/ForecastBench/.voicetree), [.mcp.json](/Users/lochlan/voicetree-evals/ForecastBench/.mcp.json), and [voicetree-8-4](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4), which matches an orchestration workspace rather than a populated benchmark repository.
- The only concrete tooling configuration visible locally is the Voicetree MCP wiring: [.mcp.json](/Users/lochlan/voicetree-evals/ForecastBench/.mcp.json) points to `http://127.0.0.1:3001/mcp`, and [.codex/config.toml](/Users/lochlan/voicetree-evals/ForecastBench/.codex/config.toml) points to `http://localhost:3001/mcp`.
- [.voicetree/.version](/Users/lochlan/voicetree-evals/ForecastBench/.voicetree/.version) is `2.9.16`, which is the only explicit version pin discoverable in the local workspace.
- [run_me.md](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/run_me.md) documents a Voicetree graph-generation workflow, not ForecastBench runtime/setup steps.
- `git rev-parse --show-toplevel` from this directory resolves to `/Users/lochlan/voicetree-evals`, so `ForecastBench/` is not its own checked-out git repository in the current workspace.

## Conclusion
The local path does not expose any direct evidence for ForecastBench runtime, package-manager, or version-management assumptions because the source repository itself is not present here. The only active tooling assumptions that can be stated from local evidence are the surrounding Voicetree/Codex orchestration settings.

## Learnings
- Tried standard manifest discovery first and kept the task as a single audit because the workspace never branched into independent code areas.
- The main pitfall is assuming the folder name `ForecastBench` means the benchmark source tree is actually checked out here.
- A successor should treat this workspace as graph/orchestration state; a real manifest audit for ForecastBench itself requires the source checkout to be mounted or cloned into the directory.

## Files Changed

- /Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-1b-1a-manifest-tooling-findings.md

### NOTES

- No code or repo files were changed; the audit result is constrained by the absence of an actual ForecastBench source checkout in this workspace.

[[forecastbench-1b-1a-manifest-tooling-assumptions-audit]]
