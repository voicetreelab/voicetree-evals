---
color: green
isContextNode: false
agent_name: Hana
---
# Findings: Top-Level Layout and README Audit

Audited the ForecastBench workspace root and adjacent markdown/navigation files. The visible layout is a Voicetree graph workspace with no top-level ForecastBench README or project-shape doc, so the directory structure does not currently self-describe where source or setup materials live.

## Findings
- The `/Users/lochlan/voicetree-evals/ForecastBench` root is almost entirely tooling scaffolding: [`.mcp.json`](/Users/lochlan/voicetree-evals/ForecastBench/.mcp.json) points to the local Voicetree MCP server, and [`.codex/config.toml`](/Users/lochlan/voicetree-evals/ForecastBench/.codex/config.toml) mirrors that same Voicetree MCP configuration. Those files describe agent tooling, not ForecastBench project layout.
- I did not find a top-level `README*` file in `/Users/lochlan/voicetree-evals/ForecastBench`. The root-level documentation that does exist is under [`voicetree-8-4`](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4), and the adjacent navigation docs [`welcome_to.md`](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/welcome_to.md), [`welcome_to_voicetree.md`](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/welcome_to_voicetree.md), [`run_me.md`](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/run_me.md), and [`hover_over_me.md`](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/hover_over_me.md) are generic Voicetree onboarding notes rather than ForecastBench repository documentation.
- The visible top-level structure under [`voicetree-8-4`](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4) is a graph/audit workspace: it contains subdirectories such as [`ctx-nodes`](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/ctx-nodes), [`chromadb_data`](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/chromadb_data), and [`voice`](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/voice), while its top-level markdown files are mostly audit/task notes like [`forecastbench-layout-docs-top-level-readme-audit.md`](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-layout-docs-top-level-readme-audit.md) and [`forecastbench-layout-docs-phase-1.md`](/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-layout-docs-phase-1.md).
- Based on those files, the visible directory structure does not match a self-documenting product/code repository. It reads as an orchestration vault about ForecastBench, not a checkout that explains where ForecastBench source, data, or user-facing setup docs live.

## Assumption
- I treated `/Users/lochlan/voicetree-evals/ForecastBench` as the task’s effective repository root, even though the enclosing git root is `/Users/lochlan/voicetree-evals`.

## Learnings
1. Tried direct root inspection first and stayed with it because the workspace is small and the missing root docs are themselves the primary finding.
2. A future agent could accidentally audit the parent git checkout; the context path makes the ForecastBench subdirectory the intended scope here.
3. The key mental model is that this workspace currently preserves Voicetree audit artifacts about ForecastBench rather than exposing a normal ForecastBench source tree.

## Related

- [forecastbench-layout-docs-top-level-readme-audit](forecastbench-layout-docs-top-level-readme-audit.md)

[[forecastbench-layout-docs-top-level-readme-audit]]
