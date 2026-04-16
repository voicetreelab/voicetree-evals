---
color: blue
isContextNode: false
agent_name: Ari
---
# Kaggle Submission — Codebase Design (Answer)

Design for metabench/kaggle_submission/: write-path-isolated subtrees per factory, SDK-facing kaggle/ layer for submission artifacts, internal harness/benchmark/analyzer split. Detailed in two child nodes.

# Kaggle Submission — Codebase Design

## Binding constraints
**Deadline: 2026-04-17 09:59 AM GMT+10 (~14h).** Metacognition track ($20k).

Kaggle-facing must-haves (from [[factory-plan_1_0]]):
- Kaggle Benchmark (via `kaggle-benchmarks` SDK) = mandatory project link
- Kaggle Tasks — all authored by us, private until deadline
- Writeup ≤1500 words, 3 pages, with fixed template sections
- Cover image (mandatory), optional public notebook

Internal must-haves (from [[experiment-spec]]):
- ~210 frozen questions, 6 classes × 2 difficulties × 10 seeds + 90 portfolios
- Per-class verifiers with exact OR-Tools gold
- Raw-string loop + Gemini Flash post-hoc extractor
- CF-fork pass for M5/M6 headline metric

## Core design principle — write-path isolation
Three factories work in parallel for 14h. Merge conflicts in the last hour = shipped-broken. Solution: **each factory owns disjoint subtrees**; shared contracts are one-writer-only and frozen-by-SHA.

| Path prefix | Owner | Writers |
|---|---|---|
| `schema-freeze.md` | B-lead | B-lead only, Hr 0–1, then frozen |
| `predictions.md` | C-lead | C-lead only, Hr 0–1, then frozen |
| `benchmark/questions/*.jsonl` | Factory A | one A-Codex per file (class×diff) |
| `benchmark/{verifiers,generators}/{class}.py` | Factory A | one A-Codex per class |
| `benchmark/questions.jsonl` | Factory A | **A-lead ONLY**, serialized, Hr 6 |
| `harness/*`, `kaggle/*` | Factory B | B-Codex by file |
| `analyzer/*`, `paper/*` | Factory C | C-agents only |
| `results/*` | runtime | append-only, partitioned by (model, phase, seed) |

## Key architectural choices
1. **Two-layer kaggle interface**: internal `harness/` stays SDK-agnostic and testable locally; `kaggle/` is a thin adapter that wraps harness functions in `kaggle-benchmarks` Task objects. Lets us iterate without kernel round-trips.
2. **Fragments → consolidated**: A-Codex writes per-class fragments (`questions/{class}_{diff}.jsonl`); A-lead concatenates once, late. Prevents 6 agents racing on one file.
3. **`results/` partitioned by (model, phase, seed)**: append-only, no locks needed. Analyzer reads whatever's landed.
4. **`tests/fixtures/` with frozen raw transcripts** from all 3 model shapes: B-extractor validated against these in Hr 0–2, before any Phase 1 fires. Specific mitigation for risk #3 in the factory plan.

## Node split
- [[kaggle-submission-filetree]] — concrete directory layout with per-file purpose
- [[factory-orchestration-hourly]] — Hr-by-Hr spawn/gate/commit sequence using voicetree MCP

## PREDICTION CLAIMS
- **Claim:** Write-path isolation plus single-writer consolidation (A-lead for `questions.jsonl`) eliminates merge conflicts across all 3 factories. *Falsifiable by:* any Hr 6–14 commit that modifies files owned by another factory.
- **Claim:** The `harness/` ↔ `kaggle/` two-layer split means Kaggle SDK changes never require touching generator/verifier code. *Falsifiable by:* any diff in `benchmark/verifiers/` driven by SDK-shape churn.


### NOTES

- Treat Hr 6 questions.jsonl commit as immutable; any post-freeze change = v2 not v1.
- Extractor fixture validation in Hr 0–2 is the single biggest cost-of-skipping — it catches model-shape divergence before 360 runs.

## Related

- [factory-plan](factory-plan.md)
- [experiment-spec](experiment-spec.md)
- [factory-plan_1_0](factory-plan_1_0.md)
- [llmpromptflowanswer](llmpromptflowanswer.md)

[[factory-plan_1]]
