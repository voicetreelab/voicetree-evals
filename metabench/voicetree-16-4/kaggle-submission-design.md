---
color: blue
isContextNode: false
agent_name: Ari
---
# Kaggle Submission — Codebase Design (v2, post-kbench-docs)

Final design: ONE `@kbench.task` function + `questions.jsonl` DataFrame driven by `.evaluate()`. No per-instance task files, no model clients, no extractor, no separate CF runner. All 210 instances are rows in evaluation_data; all 3 models via Kaggle's "Evaluate More Models" UI.

# Kaggle Submission — Codebase Design

## Binding constraints
**Deadline: 2026-04-17 09:59 AM GMT+10 (~14h).** Metacognition track ($20k).

Kaggle-facing must-haves (from [[factory-plan_1_0]]):
- Kaggle Benchmark via `kaggle-benchmarks` SDK = mandatory project link
- Private until deadline, auto-publicized after
- Writeup ≤1500 words, 3 pages, fixed template
- Cover image (mandatory), optional public notebook

Internal must-haves (from [[experiment-spec]]):
- ~210 frozen questions: 6 classes × 2 difficulties × 10 seeds + 90 portfolios
- Per-class verifiers with exact OR-Tools gold
- CF-fork pass for M5/M6 headline metric (**now inline in task**)
- ~~Raw-string loop + Gemini Flash post-hoc extractor~~ → regex parsing inline

## v2 collapses from docs findings

Reading `kaggle-benchmarks/user_guide.md` (ci branch) changed the shape substantially:

| v1 assumption | v2 reality | Source |
|---|---|---|
| 210 task files, one per instance | ONE task function + `evaluation_data: pd.DataFrame` | `@kbench.task` + `.evaluate(evaluation_data=df)` |
| Per-model task variants (3×210=630 files) | "Evaluate More Models" button on task page | §4 of guide |
| Gemini Flash extractor in harness | Regex parsing inline (spike already does this); `kbench.judge_llm` available if needed | §3 `assess_response_with_judge` |
| `harness/clients/{gemini,gpt,anthropic}.py` | `llm` injected by Kaggle; no clients | §1 Task Function Parameters |
| Post-hoc CF runner | Inline CF fork in the same session (transcript is live state) | user's point |
| `kaggle/benchmark.py` listing tasks | Not needed; the Task + evaluation_data IS the benchmark | — |

## Core design principle — write-path isolation (unchanged)

Three factories, parallel, 14h. Each owns disjoint subtrees; shared contracts are single-writer frozen-by-SHA.

| Path prefix | Owner | Writers |
|---|---|---|
| `schema-freeze.md` | B-lead | B-lead only, Hr 0–1, then frozen |
| `predictions.md` | C-lead | C-lead only, Hr 0–1, then frozen |
| `questions/*.jsonl` | Factory A | one A-Codex per file (class×diff) — scaffolding, deleted after Hr 6 |
| `{verifiers,generators}/{class}.py` | Factory A | one A-Codex per class |
| `questions.jsonl` | Factory A | **A-lead ONLY**, serialized at Hr 6 — single source of truth |
| `harness/*`, `kaggle/*` | Factory B | B-Codex by file |
| `analyzer/*`, `paper/*` | Factory C | C-agents only |
| `results/*` | runtime | append-only partitioned by (model, seed) |

## Key architectural choices (v2)

1. **One task file** `kaggle/task.py` with `@kbench.task(...)` signature `(llm, instance_json, class, difficulty, seed, gold_objective, baseline_objective, value_cap) -> float`. Uses `.evaluate(llm=[kbench.llm], evaluation_data=questions_df)` to fan out across 210 rows.
2. **EMBEDDED_MODULES pattern** (from `portfolio_spike.py`): `build_task.py` base64-inlines `harness/*.py` + `verifiers/*.py` into `task.py`. Materialized at runtime via `_ensure_bundle()` + `sys.path.insert`.
3. **Merged `questions.jsonl`** (per user): one file, 210 rows, `class ∈ {cjs, steiner, graphcol, tsp, mwis, ve, portfolio}`. Portfolio rows carry `components: [{problem_id, class, value_cap, sub_instance}]`. Fragments are staging only, gitignored after freeze.
4. **Inline CF fork** (per user): when model emits `DECISION: stop`, harness records `score_at_stop`, forces one more turn on the same transcript, records `score_after_cf`, emits `cf_delta`. Zero state-reconstruction drift. Budget reserves +300s within the 1800s wall.
5. **Return type `-> float`** → per-row economic score; Kaggle leaderboard aggregates automatically across 210 rows × N models.

## Node split
- [[kaggle-submission-filetree]] — concrete directory layout (v2)
- [[factory-orchestration-hourly]] — Hr-by-Hr spawn/gate/commit sequence

## PREDICTION CLAIMS
- **Claim:** Single-task-plus-evaluation_data shape ships in under half the B-Codex hours vs 210-file generation, because the harness-embedding step runs once. *Falsifiable by:* if build_task.py takes >30min end-to-end once harness is settled.
- **Claim:** Inline CF produces identical-or-cleaner M5/M6 signal than post-hoc reconstruction. *Falsifiable by:* comparing inline-CF deltas on CJS-5×6 seed-1 against existing `force_one_more_turn.py` outputs in `hch/masked_block_jobshop/results/`.
- **Claim:** `kbench.judge_llm` can serve as the structured-field extractor if regex parsing misses anything. *Falsifiable by:* ship decision — if regex is clean on all 3 model shapes in `tests/fixtures/`, judge_llm stays unused.

### NOTES

- Hr 6 questions.jsonl commit is immutable; any post-freeze change = v2 not v1.
- `tests/fixtures/` raw transcripts from all 3 model shapes validate regex parsers Hr 0–2 — the single biggest cost-of-skipping.
- `kbench.chats.new()` is how harness scopes a session; we do NOT call it for CF fork (want to continue the same chat).

## Related

- [factory-plan](factory-plan.md)
- [experiment-spec](experiment-spec.md)
- [factory-plan_1_0](factory-plan_1_0.md)
- [llmpromptflowanswer](llmpromptflowanswer.md)

[[factory-plan_1]]
