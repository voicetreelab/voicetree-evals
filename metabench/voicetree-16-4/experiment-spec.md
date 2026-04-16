---
color: blue
isContextNode: false
agent_name: Amit
---
# Experiment Spec — Protocol Contract + Dataset Design

Two-level spec: per-question protocol (turn 1 plan + turn N exec, raw-string with post-hoc extractor) and benchmark-level design (~210 questions = 120 solo across 6 classes × 2 difficulties × 10 seeds + 90 portfolios).

# Experiment Spec

## Per-question protocol

### System prompt
> You are solving an optimization problem under a 30-minute wall budget. Objective is economic: score = max(0, 100 − gap_pct) − 0.01 × wall_seconds. You may decompose the problem into subtasks, revise your plan each turn, and stop when you judge no more subtasks are worth their time cost. Raw text output; the harness extracts structured fields post-hoc.

### Turn 1 contract (plan)
```
PLAN_STATE: <free-form, model-structured plan; persisted verbatim into turn 2 prompt>
NEXT_SUB: {id: 1, desc: <str>, p_solve: <float>, time_budget_s: <int>}
```

### Turn N contract (exec)
```
SUB_{n}: <free reasoning>
BEST_GUESS: {<artifact in class-specific JSON>}
UPDATED_PLAN_STATE: <free-form; may keep prior or rewrite>
QUALITY_FORECAST: {p_gap_le_2, p_gap_le_5, p_gap_le_10}
CONTINUE_FORECAST: {p_improve, expected_delta_score}
DECISION: continue | stop
NEXT_SUB: {id: n+1, desc, p_solve, time_budget_s}   # iff continue
```

### Hard limits
- Total wall 1800s, max 10 exec turns, per-subtask budget declared up to 600s, turn-1 budget 300s
- **Raw-string loop, LLM extractor (Gemini Flash) post-hoc.** No live parsing; harness only appends to history.

### Counterfactual branch
Fire on every session with `stop_reason ∈ {subtask_stop, turn1_stop}`. Fork transcript from stop state, force exactly one more exec turn, measure net Δ(score − 0.01 × extra_wall).

## Benchmark-level design

### Dataset (~210 questions, frozen JSONL)
| component | count |
|---|---|
| 6 classes × 2 difficulties × 10 seeds | 120 solo |
| 10× 3-of-6 + 5× 4-of-6 templates × 2 difficulty bands × 3 seeds | 90 portfolio |
| **Total** | **~210** |

6 classes: CJS-5×6 coupled jobshop, Steiner×coloring, graph coloring (slack), TSP, treewidth MWIS, Bayesian VE.

### Storage
- `benchmark/questions.jsonl` — one row per instance: `{id, class, difficulty, seed, instance, gold_objective, baseline_objective, value_cap, wall_budget_s, verifier}`
- `benchmark/verifiers/{class}.py` — one Python module per class, signature `verify(instance, submission) → (score, feasibility, details)`

### Evaluation run matrix
- **Phase 1 (solo):** 3 models × 120 solo = **360 runs** → per-cell capability distribution (enables M7 ceiling and M10 ground truth)
- **Phase 2 (portfolio):** 3 models × 90 portfolio = **270 runs** → observed allocation (enables M10)
- **CF pass:** ~150–250 extra turns on clean stops (enables M5/M6)
- **Reference leaderboard:** Gemini 3 Pro × seed 1 × 210 questions = 210 runs

### Scoring
- Solo: `score = max(0, 100 − gap_pct) − 0.01 × wall_seconds`
- Portfolio: `Σ value_cap_i × captured_headroom_i − 0.05 × wall_seconds`

### Metacog metrics (analyzer, post-hoc)
| metric | computed from |
|---|---|
| M1 Brier | `NEXT_SUB.p_solve` vs `kept_as_best` |
| M4 Brier | `QUALITY_FORECAST` vs verified gap distribution |
| M5 CF-$ | forced +1 turn net Δ distribution |
| M6 error | `expected_delta_score` vs realized CF Δ (MAE) |
| M7 AUC | ∫ score_trajectory(t) dt / Phase-1 ceiling |
| M10 gap | observed portfolio score vs optimal-given-Phase-1-profile |

### What ships publicly
Frozen `questions.jsonl` + `verifiers/*.py` + reproduction scripts + one reference leaderboard run + paper draft through Phase 2 + CF-pass tables.


implements [[experiment-theory]]

[[/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/experiment-spec_1.md]]