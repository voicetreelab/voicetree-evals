---
color: blue
isContextNode: false
agent_name: Ayu
---
# Factory Plan v2 Staleness Audit + Open Gaps

factory-plan.md is stale v1; canonical v2 lives in kaggle-submission-design + factory-orchestration-hourly. 7 concrete drift rows + 6 un-addressed gaps surfaced for user decision.

# Factory Plan v2 Staleness Audit + Open Gaps

## Where v2 ground truth lives
- `kaggle-submission-design.md` — v2 architecture (single task.py, inline CF, EMBEDDED_MODULES, `.evaluate()`)
- `factory-orchestration-hourly.md` — v2 Hr-by-Hr sequencing
- `kaggle-submission-filetree.md` — v2 directory layout
- `factory-plan.md` — **stale v1** (pre-kbench-docs)

## Drift in factory-plan.md vs v2

| factory-plan.md (v1) | v2 reality |
|---|---|
| B-Codex × 4 incl. B-extractor | B-Codex × 3, no extractor — regex inline; `kbench.judge_llm` as fallback |
| B-runner does post-hoc CF | Inline CF fork on `DECISION: stop`, same transcript |
| B-kaggle: 210 task files + per-model clients + grader | ONE `task.py` + EMBEDDED_MODULES + `.evaluate(evaluation_data=df)`; Kaggle injects `llm` |
| Sequencing: Phase 1 (360) + Phase 2 (270) + CF pass | ONE `.evaluate()` per model × 3 models via "Evaluate More Models"; Kaggle-side fan-out |
| Risk #3: raw-string extractor fails 10% | obsolete — no extractor |
| Risk #5: parallel-5 Kaggle kernels overrun | obsolete — failure mode is now per-row timeout in `.evaluate()` |
| Prediction claim on extractor failure rate | obsolete |

## Gaps even v2 docs don't address

1. **"Evaluate More Models" trigger** — v2 treats this as UI-driven. Need Hr 0–1 check for `kaggle` CLI/API equivalent; if none, write explicit checklist into `.coordination/handoffs.md` so Hr 10–14 deadline pressure doesn't drop it.
2. **`kbench.evaluate()` per-row timeout** (LOAD-BEARING) — we assume `TOTAL_BUDGET_S=1800` + `CF_RESERVE_S=300`. If Kaggle enforces shorter per-row ceiling, inline CF breaks. Must verify in `kaggle-benchmarks/user_guide.md` before harness code commits to 1800s. Add to B-lead Hr 0–1.
3. **Schema freeze scope** — v2 `@kbench.task` signature `(llm, instance_json, cls, difficulty, seed, gold_objective, baseline_objective, value_cap) → float` IS a public contract. `schema-freeze.md` must pin the signature, not only internal protocol fields, else Factory A may emit rows Factory B can't unpack.
4. **Hr 2–3 fixture must exercise `DECISION: stop`** — inline CF is the load-bearing new behavior; fixture that never stops doesn't validate it. State explicitly in fixture spec.
5. **A-Portfolio ambiguity** — factory-orchestration-hourly says "1 extra Codex OR A-lead directly". Recommend A-lead direct: portfolio sampling depends on other fragments being committed = natural serial step.
6. **Fallback register missing "drop 1 class"** — MWIS/VE have the flakiest difficulty-knob story (per v1 prediction claim, still valid). If either blocks Hr 6 freeze, drop > slip.

## Options presented to user
- (a) Rewrite `factory-plan.md` as canonical v2 plan.
- (b) Mark `factory-plan.md` superseded; patch delta list only.
- (c) Drill into 1–2 gaps now. Default pick: gap #2 (kbench timeout) — cheapest verify, most load-bearing.

## Working assumption if no reply
Option (c), starting with gap #2 via Explore agent on `kaggle-benchmarks/user_guide.md`.

## PREDICTION CLAIMS
- **Claim:** If `kbench.evaluate()` has a per-row timeout <1800s, inline-CF design fails and harness must restructure CF as a second `.evaluate()` over a derived DataFrame. *Falsifiable by:* Hr 0–1 docs check — grep user_guide.md for `timeout`, `wall`, `max_seconds`.
- **Claim:** "Evaluate More Models" has NO CLI/API equivalent (UI-only), making Hr 10–14 the highest manual-error surface in v2. *Falsifiable by:* finding a `kaggle benchmarks evaluate --model ...` subcommand.
- **Claim:** Rewriting `factory-plan.md` in-place is strictly better than leaving a stale-with-stub, because the stub creates two-source-of-truth confusion when a Codex agent onboards via `factory-plan.md` first. *Falsifiable by:* user prefers preserving v1 history as an artifact.

### NOTES

- factory-plan.md header says v1; kaggle-submission-design.md header says v2 — naming convention already implies superseded.
- Gap #2 is the one that could break the whole v2 simplification; worth verifying before any B-Codex writes wall-budget constants.
- No code changes this turn — pure thinking-partner analysis.

## Related

- [factory-plan](factory-plan.md)
- [kaggle-submission-design](kaggle-submission-design.md)
- [factory-orchestration-hourly](factory-orchestration-hourly.md)
- [kaggle-submission-filetree](kaggle-submission-filetree.md)

[[factory-plan_2]]
