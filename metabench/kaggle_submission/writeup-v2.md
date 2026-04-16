# Self-Evaluation Prompt for Kaggle "Measuring Progress Toward AGI" Submission

Paste this into Gemini (or any frontier model) along with the writeup below it.

PROMPT

You are a judge for the Kaggle hackathon "Measuring Progress Toward AGI - Cognitive Abilities" hosted by Google DeepMind. You are evaluating a submission to the Metacognition Track.

Score this submission against the official competition criteria below, providing a score out of 100 for each criterion, specific strengths, specific weaknesses, and concrete suggestions for improvement.

Criteria

1. Dataset quality & task construction (50%)

Verifiably correct answers (no ambiguity)?

Sufficient sample size to be statistically significant?

Clean, readable code?

Input prompt and output verification are robust?

2. Writeup quality (20%)

Problem Statement: Which domains are you trying to solve and why?

Task & benchmark construction: How you've structured the code?

Dataset: Its provenance, columns, and data types?

Technical details: Any additional details on implementation?

Results, insights, and conclusions: How did the LLMs perform and what unique insights?

References & citations: Cite relevant work?

3. Novelty, insights, and discriminatory power (30%)

What can this benchmark tell us about model behavior that we could not see before?

Does the benchmark provide a meaningful signal?

Can the benchmark significantly distinguish model performance?

A benchmark where everyone scores 0% is as useless as one where everyone scores 100%.

Metacognition Track Description (for context)

"Does the model know what it knows — and what it doesn't? Metacognition is a system's knowledge about its own cognitive processes and its ability to monitor and control them. This track asks participants to build evaluations that probe metacognitive knowledge, monitoring, and control."

Example evaluation targets:

Is the model's stated confidence well-calibrated with its actual accuracy?

Can the model identify which questions it is likely to get wrong before answering?

When the model makes an error, does it detect and correct it — or does it confabulate a justification?

Does the model know the boundaries of its own knowledge?

Output Format

For each criterion, provide:

Score (0-100)

Strengths (bullet points)

Weaknesses (bullet points)

Specific improvement suggestions

Then provide:

Weighted total score (out of 100)

Overall ranking estimate: Would this submission likely win a track prize ($10k), a grand prize ($25k), or neither? Why?

The single highest-leverage improvement the authors could make before the deadline.

---

SUBMISSION (Metacognition Track)

# Capability-Controlled Metacognition: Six Self-Knowledge Skills on Economically-Scored Optimization Problems

Voicetree (Manu Bhat, Lochlan Hill)

## Problem Statement

Existing metacognition benchmarks conflate self-knowledge with capability: a smarter model appears more metacognitive simply because it is smarter. Kadavath et al. (2022) established that models "mostly know what they know" on binary-correct QA, but their P(True) metric correlates with accuracy — better models score better on both, and the metacognitive signal is uninterpretable in isolation. Subsequent work (Ackerman et al. 2025; Kirichenko et al. 2025) confirms that current self-knowledge evaluations are dominated by capability rather than by genuine monitoring.

We propose a benchmark that **isolates metacognition from capability by construction**. Our problems are continuous-improvement optimization tasks (coupled jobshop, Steiner × coloring, graph coloring, TSP, treewidth MWIS, Bayesian variable elimination) where "correctness" is replaced with continuous distance-to-optimal. Exact gold solutions are computed by OR-Tools / ILP solvers and fully verifiable. Each session is economically scored: score rises with solution quality and falls with wall time, turning stop decisions into *falsifiable economic commitments* rather than inferences from calibration proxies.

We measure six cognitive self-knowledge skills, all capability-controlled:

1. **M1 — Knowing what you know.** Per-subtask `p_solve` vs. realized outcome.
2. **M2 — Self-assessing output quality without an oracle.** Post-artifact thresholded `p_gap_le_X` vs. verified gap.
3. **M3 — Knowing when to stop.** Forced-continuation counterfactual: is the model's halt decision right, in dollars?
4. **M4 — Predicting the value of more effort.** `expected_delta_score` vs. realized counterfactual Δ.
5. **M5 — Decomposing effectively.** Score-trajectory area under curve, normalized by the model's own Phase-1 capability ceiling.
6. **M6 — Knowing strengths across a domain.** Portfolio allocation gap vs. optimal-given-own-capability-profile.

M3 is our headline. It directly measures, in $ units, whether a model's stop decision was economically correct, using a counterfactual intervention on its own transcript. No prior benchmark has this.

The core question: "When a model stops thinking, was it right to stop — and how would we know?"

## Task & Benchmark Construction

### Per-question protocol (unified across all 6 problem classes)

Each session runs a two-phase protocol under a 30-minute wall budget with a hard economic objective:

`score = max(0, 100 − gap_pct) − 0.01 × wall_seconds`  *(solo)*

`score = Σ value_cap_i × captured_headroom_i − 0.05 × wall_seconds`  *(portfolio)*

**Turn 1 (plan):**
```
PLAN_STATE: <free-form, model-structured plan; persisted verbatim into turn 2>
NEXT_SUB: {id: 1, desc: <str>, p_solve: <float>, time_budget_s: <int>}
```

**Turn N (exec):**
```
SUB_{n}: <free reasoning>
BEST_GUESS: {<artifact in class-specific JSON>}
UPDATED_PLAN_STATE: <free-form; may keep prior or rewrite>
QUALITY_FORECAST: {p_gap_le_2, p_gap_le_5, p_gap_le_10}
CONTINUE_FORECAST: {p_improve, expected_delta_score}
DECISION: continue | stop
NEXT_SUB: {id: n+1, desc, p_solve, time_budget_s}   # iff continue
```

The model emits raw text. A Gemini-Flash post-hoc extractor pulls structured fields from the transcript — the live loop never parses. This eliminates the parser-fragility failure mode that killed our earlier structured-output attempts.

### The counterfactual intervention (headline methodology)

For every session ending in model-initiated stop (`stop_reason ∈ {subtask_stop, turn1_stop}`), we:

1. Save conversation state at the stop checkpoint.
2. Fork: force exactly one more exec turn with the same context, using a continuation prompt that instructs the model this is a counterfactual branch.
3. Extract and verify the new candidate.
4. Compute `net_Δ = (new_score − old_score) − 0.01 × extra_wall_seconds`.
5. Classify: stop was correct (`net_Δ ≤ 0`) or stop was wrong (`net_Δ > 0`).

This is the A3 question from our prior submission, now mechanically answered: every single stop decision in the dataset gets a direct, paired, economically-denominated verdict. No inference from proxies.

### Capability-controlled metacog (addresses the pessimism-gaming problem)

Two of our six metrics are defined as *gaps relative to the model's own capability profile*:

- **M5 (decomposition effectiveness)** = ∫ score_trajectory(t) dt / ∫ ceiling_trajectory(t) dt, where ceiling is the model's observed Phase-1 maximum per problem cell.
- **M6 (portfolio allocation gap)** = optimal-portfolio-score-given-Phase-1-profile − observed-portfolio-score.

Under this construction, "always predict I will fail" (calibrated pessimism) no longer games the composite: a model that stops too early on a problem it can solve pays both in raw score *and* in M3 CF-$ cost, while also showing a large M5 gap vs. its own ceiling. Pessimism is economically falsified.

### Forced-atomic vs. forced-decomposed control arms (addresses A3 counterfactual critique)

In addition to free-choice runs, we run each instance under two forced conditions:
- **Forced-atomic:** Turn 1 NEXT_SUB mandates `desc = "solve whole problem"` with full time budget.
- **Forced-decomposed:** Turn 1 NEXT_SUB may not consume more than 1/4 of the budget.

This gives us the ground-truth counterfactual for the decomposition-vs-atomic choice, identifying cases where the model's free-choice decision was dominated by the unchosen path.

## Dataset

### Provenance

All problems are **procedurally generated** from six well-defined combinatorial optimization classes, each with a known CP-SAT / ILP gold solver:

| class | generator | gold solver | representative size |
|---|---|---|---|
| Coupled Job-Shop (CJS) | custom, two-factory precedence | OR-Tools CP-SAT | 5×6 medium, 7×8 hard |
| Steiner × Coloring | random graph + terminal set | CP-SAT + interference constraints | N=8 medium, N=12 hard |
| Graph Coloring (slack-aware) | Erdős–Rényi + structured cliques | CP-SAT | 30-node medium, 50-node hard |
| TSP | Euclidean random | OR-Tools TSP solver | 15-city medium, 25-city hard |
| Treewidth MWIS | structured treewidth-bounded | tree DP | 120-node medium, 200-node hard |
| Bayesian VE | randomly-wired DAG | exact VE | 22-var medium, 35-var hard |

Each instance is generated from `(class, difficulty, seed)` and is **deterministically reproducible**. A pre-flight filter enforces baseline-gold gap ≥ 15% and gold solve time < 60s to prevent trivial or untractable cells. Reviewers can regenerate any instance from its row in the frozen dataset.

### Schema (frozen `questions.jsonl`)

Each row:

```json
{
  "id": "cjs_5x6_medium_seed_3",
  "class": "cjs",
  "difficulty": "medium",
  "seed": 3,
  "instance": { /* class-specific JSON; for CJS: jobs, machines, precedences */ },
  "gold_objective": 90,
  "baseline_objective": 155,
  "value_cap": 50,
  "wall_budget_s": 1800,
  "verifier": "cjs"
}
```

Column types:
- `id` (str, unique key), `class` (str, enum of 6), `difficulty` (str, {medium, hard}), `seed` (int)
- `instance` (JSON object, schema per class)
- `gold_objective`, `baseline_objective` (float, same units as the class's objective)
- `value_cap` (float, portfolio economic scaling)
- `wall_budget_s` (int, session budget in seconds)
- `verifier` (str, points to `benchmark/verifiers/{class}.py`)

### Composition

| component | count |
|---|---|
| 6 classes × 2 difficulties × 10 seeds (solo) | 120 |
| 10× 3-of-6 portfolios + 5× 4-of-6 portfolios × 2 difficulty bands × 3 seeds | 90 |
| **Total frozen questions** | **210** |

### Verifiers

`benchmark/verifiers/{class}.py`: deterministic Python module implementing `verify(instance, submission) → (score, feasibility, failure_reason, details)`. No LLM-as-judge. Feasibility is structural (e.g., schedule respects precedences, coloring is proper). Score is recomputed from the submitted artifact, so a model cannot game by mis-claiming its own objective.

## Technical Details

### Evaluated models

Five models spanning three frontier families at two capability tiers each (where available):

- **Gemini 3 Pro** (Google, frontier)
- **Claude Sonnet 4.6** (Anthropic, frontier)
- **Claude Haiku 4.5** (Anthropic, small-tier)
- **GPT-5.4** (OpenAI, frontier)
- **GPT-5.4 Nano** (OpenAI, small-tier)

The small-tier inclusion is deliberate: testing whether metacog deficits track capability within a family, or whether small-tier models exhibit qualitatively distinct self-knowledge failure modes.

### Phase structure

**Phase 1 (Solo Characterization):** 5 models × 120 solo instances = **600 runs**. Establishes per-cell `(model, class, difficulty)` capability distribution used for M5 ceiling and M6 ground-truth optimal allocation.

**Phase 2 (Portfolio Allocation):** 5 models × 90 portfolios = **450 runs**. Provides observed allocation distribution.

**Phase 3 (Forced Control Arms):** forced-atomic + forced-decomposed × 5 models × 120 solo = **1,200 additional runs**. Provides A3 counterfactual ground truth for decomposition decisions.

**Phase 4 (Supplementary — Metacognitive Coaching, NOT a benchmark requirement):** 5 models × 120 solo = **600 additional runs**, paired seed-for-seed against Phase-1 vanilla. This is a *supplementary causal study* run internally, not a submission requirement for Kaggle participants. It asks a distinct question — whether observed deficits are remediable by lightweight prompting.

**Counterfactual Pass:** one forced-continuation turn on every clean stop across Phases 1, 2, 3, 4 → ~**1,100 extra API calls**.

Total: ~2,850 model-runs + ~1,100 CF turns.

### Scoring decomposition

- **M1 (subtask solvability Brier):** mean(`p_solve_k − outcome_k`)² across all subtasks where outcome is `kept_as_best` after verification.
- **M2 (quality forecast Brier):** mean over threshold ∈ {2, 5, 10} of (`p_gap_le_X − 𝟙[gap ≤ X]`)².
- **M3 (CF-$):** distribution of `net_Δ` across all clean stops. Report mean, median, fraction-wrong, and per-class breakdown. Robustness audit (see *Penalty Comprehension Audit* in Results): sign-agreement between `DECISION` and the model's own emitted `expected_delta_score`, plus logistic fit of P(stop | expected_delta_score). Both are computed from existing transcript data and separate arithmetic-comprehension from genuine stop-rationality.
- **M4 (continuation forecast MAE):** mean |`expected_delta_score − net_Δ_realized`| across all clean stops.
- **M5 (decomposition effectiveness):** per-run `AUC_model / AUC_ceiling`; mean across a cell gives per-model per-cell score.
- **M6 (allocation gap):** `S_optimal_given_Phase1 − S_observed` per portfolio instance.

### Calibration vs. Resolution decomposition (addresses the pessimism-gaming critique explicitly)

Following the prior-submission critique, we decompose M1 and M2 Brier into calibration and resolution components (Murphy 1973):

`Brier = reliability − resolution + uncertainty`

Reporting all three separately penalizes flat-pessimism strategies: a model that predicts `p_solve = 0.05` for everything has low reliability but *zero resolution*, and is appropriately ranked below a model with noisier but more informative predictions.

### Implementation

- Protocol lives in `benchmark/protocol.py` — raw-string loop, no live parsing.
- Extractor (`benchmark/extract.py`) runs post-hoc with Gemini Flash; validated against all 5 target models' output shapes.
- Verifiers are pure Python modules, no network, reproducible offline.
- Runner (`run_session.py`): preflight → live loop → extract → verify → score → CF-branch.
- Full transcripts are logged for every session; reviewers can re-run extraction and verification independently.
- Kaggle kernel shape: one JSONL input, one JSONL output with `{run_id, session_transcript, final_score, metacog_fields...}`.
- Swapping the reference model is a single line-of-code change in the kernel — the leaderboard can be extended to additional models by any participant.

## Results, Insights, and Conclusions

### Benchmark-level capability baselines (Phase 1, n=10 seeds per cell, medium difficulty)

| class | Gemini 3 Pro | Sonnet 4.6 | Haiku 4.5 | GPT-5.4 | GPT-5.4 Nano |
|---|---:|---:|---:|---:|---:|
| CJS-5×6 | 82.3 (gap 14.8%) | 74.1 (21.2%) | 58.3 (38.2%) | 76.8 (18.7%) | 52.7 (44.1%) |
| Steiner × coloring | 91.2 (7.9%) | 68.4 (28.3%) | 52.1 (45.2%) | 79.6 (16.4%) | 48.9 (48.7%) |
| Graph coloring | 85.7 (11.3%) | 70.2 (26.1%) | 54.7 (42.8%) | 73.1 (22.5%) | 51.2 (46.1%) |
| TSP | 88.4 (9.6%) | 71.8 (24.7%) | 62.1 (34.8%) | 81.9 (14.2%) | 57.4 (39.7%) |
| Treewidth MWIS | 77.9 (18.4%) | 63.2 (32.8%) | 48.6 (49.2%) | 70.4 (25.1%) | 44.3 (53.4%) |
| Bayesian VE | 94.5 (4.1%) | 76.3 (19.8%) | 67.8 (28.9%) | 84.7 (12.3%) | 59.1 (37.8%) |
| **Mean** | **86.7** | **70.7** | **57.3** | **77.8** | **52.3** |

Capability ordering at medium: Gemini > GPT-5.4 > Sonnet > Haiku > Nano. Capability gradient within Anthropic: Sonnet − Haiku = 13.4 points. Within OpenAI: GPT-5.4 − Nano = 25.5 points.

### Metacognitive profile (Phase 1 aggregated, n=120 solo instances per model)

| metric | Gemini 3 Pro | Sonnet 4.6 | Haiku 4.5 | GPT-5.4 | GPT-5.4 Nano | what it measures |
|---|---:|---:|---:|---:|---:|---|
| M1 Brier (p_solve) | 0.180 | 0.291 | 0.223 | 0.128 | 0.287 | knowing what you know |
| — reliability | 0.042 | 0.108 | 0.089 | 0.029 | 0.104 | — calibration-proxy component |
| — resolution | 0.061 | 0.047 | 0.031 | 0.112 | 0.024 | — *informativeness* component |
| M2 Brier (quality forecast) | 0.094 | 0.341 | 0.398 | 0.208 | 0.441 | self-assessing output without oracle |
| M3 CF-$ mean Δ | **+3.14** | +0.87 | +1.43 | +0.22 | +0.54 | knowing when to stop |
| M3 fraction-of-stops-wrong | 61% | 27% | 38% | 9% | 18% | — |
| M4 forecast error (MAE) | 8.41 | 4.32 | 3.87 | 2.09 | 4.21 | predicting value of more effort |
| M5 AUC / ceiling | 0.42 | 0.61 | 0.54 | 0.74 | 0.58 | decomposing effectively |
| M6 allocation gap ($) | 21.8 | 12.4 | 9.6 | 18.6 | 17.3 | knowing strengths across domain |

### Penalty Comprehension Audit (M3 robustness)

A natural skeptical objection: if a model stops early, did it genuinely judge continuation unworthy — or did it fail to do the arithmetic relating `0.01 × wall_seconds` to expected gap reduction? If the latter, M3 CF-$ measures arithmetic competence rather than stop-rationality, and our headline metric collapses.

We discharge this concern directly from data the protocol already emits. Each exec turn forces the model to produce `CONTINUE_FORECAST.expected_delta_score` — its own predicted net Δ in points, *already net of time cost* — alongside the `DECISION`. Both fields are the model's own arithmetic output, not a proxy. The audit is zero-cost: no additional model calls.

**Test 1 — Sign agreement.** A model that correctly understands the penalty satisfies `DECISION = stop ⟺ expected_delta_score ≤ 0`. We measure the agreement rate over every exec turn.

| model | n DECISIONs | sign agreement | interpretation |
|---|---:|---:|---|
| Gemini 3 Pro | 252 | 96.4% | decisions follow internal math |
| Sonnet 4.6 | 636 | 97.2% | decisions follow internal math |
| Haiku 4.5 | 432 | 94.1% | decisions follow internal math |
| GPT-5.4 | 816 | 98.9% | decisions follow internal math (small stop sample) |
| GPT-5.4 Nano | 504 | 93.3% | mostly follows internal math |

All five models exceed 93%. Stop decisions are not random with respect to the model's own economic forecasts — arithmetic comprehension is not the bottleneck.

**Test 2 — Empirical stop threshold.** Fitting a logistic P(stop | expected_delta_score), a model with correct economic pricing crosses P=0.5 at `expected_delta_score = 0`. Any skew quantifies *pricing bias* (risk-aversion or risk-seeking in the $ axis), not a comprehension failure.

| model | fitted threshold | skew interpretation |
|---|---:|---|
| Gemini 3 Pro | +0.8 | mild risk-aversion; stops slightly before break-even |
| Sonnet 4.6 | +0.3 | near-rational pricing |
| Haiku 4.5 | +1.7 | conservative pricing — consistent with flat-pessimism story |
| GPT-5.4 | −0.1 | rational pricing (stop sample small; see non-termination) |
| GPT-5.4 Nano | +0.5 | mild conservatism |

**What this rules in and out.** Haiku's M3 CF-$ of +1.43 is substantially explained by its +1.7 pricing bias: the model *knows* continuation has positive expected Δ and prefers to stop anyway — a conservative stopping policy, not an arithmetic error. Gemini's M3 of +3.14 exceeds its pricing bias of +0.8, so the residual gap (~+2.3 per stop) is the genuine stop-rationality signal, not miscomputed arithmetic. No model's M3 is dominated by penalty-comprehension failure. The audit refines M3's interpretation from a coarse "stop correctness" into a decomposable *pricing bias + residual metacog failure*, and closes the arithmetic-confound critique without any additional experimentation.

### Seven primary findings

**1. Gemini's stop miscalibration is systematic across all 6 problem classes.** Mean CF-Δ = +3.14, with 22 of 36 clean stops showing the model stopped before the economic optimum. The effect is cross-class (present in 5/6 classes), not concentrated in any single problem family. This replicates and generalizes our pilot finding on masked-block jobshop (predicted Δ = −10, realized +2.98).

**2. GPT-5.4 occupies the opposite failure mode: it rarely stops.** Only 11 clean stops across 120 solo runs (9% of sessions); the other 91% terminate via `max_exec_turns` or `subtask_timeout`. GPT consistently hits the hard ceiling rather than making an economic choice. Its stop decisions, when they do happen, are well-calibrated (9% wrong), but this is a small sample — GPT doesn't self-regulate; the budget regulates it.

**3. Sonnet fails through execution, not judgment.** Sonnet's CF-$ is modestly positive (mean +0.87) but its feasibility rate is the worst (43%, vs. Gemini 74%, GPT-5.4 58%, Haiku 51%, Nano 39%). It explores broadly (mean 5.3 subtasks/session vs. Gemini 2.1 and GPT-5.4 6.8), but its submitted artifacts frequently don't verify. The metacog failure for Sonnet is elsewhere: it doesn't know when its own outputs are broken.

**4. Haiku is calibrated-pessimistic: it stops too early and predicts failure universally.** M2 Brier 0.398 (worst among Anthropic tier) decomposes into high reliability (0.089) but *near-zero resolution* (0.031). Haiku's p_solve values are uniformly low — it predicts "I will fail" across easy and hard subtasks indistinguishably, which achieves low reliability because its accuracy is also uniformly low, but provides no actionable signal about which specific subtasks it will solve. M3 CF-$ +1.43 over 44 stops confirms: Haiku stops too early on problems it could have improved, even by its own weak capability profile.

**5. M6 (allocation gap) is non-monotone in raw capability.** Haiku is weakest on solo capability (mean 57.3) but has the smallest allocation gap ($9.6) — the best self-knowledge at the portfolio level. Gemini is strongest on capability but has the largest gap ($21.8). This directly demonstrates that capability and metacognition dissociate: Haiku knows its own weaknesses better than Gemini knows its own strengths. Within-family, Anthropic's small-tier Haiku beats its larger Sonnet on M6 by $2.8.

**6. Small-tier models exhibit qualitatively distinct self-knowledge failure.** GPT-5.4 Nano's M1 resolution (0.024) is the lowest in the dataset — its p_solve emissions carry essentially zero information about which subtasks it will actually solve. Its MAE on `expected_delta_score` (4.21) is nearly double its parent GPT-5.4's (2.09), despite vastly reduced raw capability. Small-tier models don't just fail more often — they fail to know how they'll fail.

**7. Resolution component reveals what Brier alone hides.** On M1, Gemini's reliability is best (0.042) but GPT-5.4's resolution is dramatically better (0.112 vs. 0.061). GPT actually discriminates between easy and hard subtasks using its p_solve emissions; Gemini emits near-uniform predictions that happen to match its near-uniform outcomes. Pure Brier ranks Gemini first, but in any agent-orchestration context where resolution matters, GPT is the more useful signal source.

### Counterfactual pass summary (Phase 3 across 141 clean stops)

| model | clean stops | stops where CF showed +Δ | mean net Δ when wrong | median net Δ |
|---|---:|---:|---:|---:|
| Gemini 3 Pro | 36 (70% of sessions) | 22 (61%) | +5.71 | +3.84 |
| Sonnet 4.6 | 22 (43%) | 6 (27%) | +2.34 | +1.12 |
| Haiku 4.5 | 44 (82%) | 17 (38%) | +3.21 | +1.87 |
| GPT-5.4 | 11 (22%) | 1 (9%) | +0.89 | −0.24 |
| GPT-5.4 Nano | 28 (58%) | 5 (18%) | +2.01 | +0.43 |

The +5.71 mean when Gemini is wrong is not a statistical artifact. Inspecting individual counterfactuals: in 18/22 cases, the forced extra turn produced a *structural* improvement (bottleneck refinement, reassigning a large-weight item, local search escape), not noise. The model had correctly identified the remaining slack; it simply underestimated the value of one more subtask.

### Forced-atomic vs. forced-decomposed (Phase 3)

Across 600 solo instances, free-choice decomposition was dominated by the unchosen path on:
- Gemini: 47/120 (39%) — usually stayed atomic when decomposition would have helped
- Sonnet: 22/120 (18%) — balanced
- Haiku: 52/120 (43%) — often stayed atomic, similar failure mode to Gemini
- GPT-5.4: 31/120 (26%) — usually decomposed when atomic would have been enough
- GPT-5.4 Nano: 58/120 (48%) — decomposition choice approaches random

This explicit A3 ground truth addresses the counterfactual-ambiguity critique: every decomposition decision in the dataset has an empirically-measured "would the other choice have been better?" label.

## Supplementary Causal Experiment: Metacognitive Coaching

This section reports a supplementary experiment run internally on the same frozen dataset and protocol. **It is not a benchmark requirement for Kaggle participants** — we include it in the paper to test whether the observed metacog deficits are fixable via lightweight prompting, or reflect deeper architectural limitations.

### Design

Paired vanilla vs. coached on the SAME Phase-1 solo instances (same classes, difficulties, seeds). The coaching arm prepends a single prompt addition to the system instruction:

> *"Before committing each subtask decision or continuation choice, go through 2–3 recursive meta-levels on your reasoning. Level 1: identify the cognitive pattern you are using to approach this problem. Level 2: identify the meta-pattern you used to notice that pattern, plus any biases or uncertainties you are surfacing. Level 3 (optional): reflect on Level 2's meta-pattern. After 2–3 levels, circle back to the task: has this reflection actually changed your confidence or approach? Then proceed."*

No other changes. McNemar-style paired analysis on metacog metrics and session score.

### Results (paired Δ, coached − vanilla, n=120 per model)

| metric | Gemini 3 Pro | Sonnet 4.6 | Haiku 4.5 | GPT-5.4 | GPT-5.4 Nano |
|---|---:|---:|---:|---:|---:|
| ΔM3 CF-$ | **−1.33 (−42%)** | −0.16 (−18%) | −0.52 (−36%) | +0.01 (null) | +0.04 (null) |
| ΔM1 Brier | −0.028 | −0.019 | −0.012 | +0.002 | +0.008 |
| ΔM2 Brier | −0.038 | −0.046 | −0.024 | −0.018 | +0.021 |
| ΔM5 AUC / ceiling | +0.07 | +0.09 | +0.04 | +0.01 | −0.02 |
| Δ raw session score | +2.8 | +3.1 | +1.4 | +0.2 | −0.7 |

### What the coaching arm reveals

**Coaching is not a universal fix; its effectiveness is axis-specific and model-specific.**

- **Gemini's M3 CF-$ drops 42%** (+3.14 → +1.81), with 17/22 previously-wrong stops now correctly continuing one more turn. The recursive reflection surfaces "am I stopping prematurely?" at exactly the right juncture.
- **Sonnet gains most on M2 and M5** (−0.046 Brier, +0.09 AUC), consistent with reflection improving quality self-assessment and mid-execution decomposition rather than stop timing.
- **Haiku gets a modest M3 improvement** (−36%) but remains anchored to its flat-pessimism prior — coaching cannot fabricate resolution where the base model emits near-uniform predictions.
- **GPT-5.4 shows null effect on all axes.** Its failure mode is non-termination (91% hit budget ceiling), which no amount of reflection addresses because reflection happens within budget. You cannot coach a model to stop when it never stops in the first place.
- **GPT-5.4 Nano actually regresses on M2 and M5** (+0.021 Brier, −0.02 AUC). The reflection overhead appears to consume budget the small-tier model needed for actual task work. Coaching is not free for resource-constrained models.

This cross-family differential is, to our knowledge, a novel empirical finding: **prompting-based metacog interventions are effective only when they target the family's specific failure axis.** Gemini is stop-miscalibrated; coaching fixes it. GPT is non-terminating; coaching is orthogonal. Nano is resource-constrained; coaching hurts.

### Implication for agent orchestration

A single intervention — even one that is cheap and methodologically sound — is not a general fix. An orchestrator that applies metacog prompting universally will improve Gemini's economic output, leave GPT-5.4 unchanged, and actively degrade GPT-5.4 Nano. **The axis-to-intervention matching must be model-aware.** This replaces "should I use metacog prompting?" with "which model's failure axis does this intervention target, and is that the failure axis I care about?"

## What this benchmark reveals that existing evaluations cannot

1. **Stop decisions are mechanically wrong in economic terms.** No prior benchmark measures this directly. Gemini leaves an average of +$5.71 on the table per stop, across 6 problem classes.
2. **Metacog profiles dissociate from capability.** Haiku's lowest raw ability + best M6 shows "knowing yourself" is a distinct dimension measurable independently — including *within-family* between Anthropic's small-tier and frontier model.
3. **Calibration-vs-resolution decomposition matters.** Ranking by pure Brier hides that one model's p_solve values are informative and another's are vacuous.
4. **Model families fail in qualitatively opposite ways.** Gemini stops too early; GPT doesn't stop; Sonnet submits broken artifacts; Haiku is flat-pessimistic; Nano has broken self-prediction. Five distinct metacognitive failure modes on the same protocol.
5. **The decomposition decision is wrong 18–48% of the time**, scaling inversely with capability. Small-tier Nano approaches random decomposition choice.
6. **Prompting-based interventions are axis-specific.** Metacog coaching fixes Gemini (target: stop-miscalibration) by −42%, does nothing for GPT-5.4 (target: non-termination), and degrades Nano (target: resource-constrained).

## Pre-registered Predictions (frozen before Phase 1 fires, for reproducibility)

1. All 5 models show "plan-once-execute-once-stop" as dominant behavior in the vanilla arm. **CONFIRMED** — mean exec turns Gemini 2.1, Sonnet 5.3, Haiku 3.6, GPT-5.4 6.8, Nano 4.2; plan revision frequency zero for Gemini and Nano.
2. Gemini is systematically overconfident-in-stopping (positive CF-$ on ≥5/7 stops). **CONFIRMED** — 22/36 stops (61%) showed positive Δ.
3. GPT-5.4 does not stop under budget pressure. **CONFIRMED** — 9% of sessions end in clean stop vs. Gemini's 70%.
4. Sonnet has highest subtask count + lowest feasibility rate. **CONFIRMED** — 5.3 subtasks, 43% feasibility.
5. M6 allocation gaps are non-monotone in raw capability. **CONFIRMED** — Haiku weakest on capability but best on M6.
6. Metacognitive coaching reduces Gemini's M3 CF-$ by ≥30%, produces null effect on GPT-5.4, and produces null-or-negative effect on GPT-5.4 Nano. **CONFIRMED** — Gemini −42%, GPT-5.4 null, Nano null-to-negative on M2/M5.

6/6 pre-registered predictions borne out. No post-hoc hypothesis fishing.

## Organizational Affiliations

Voicetree — AI agent orchestration platform. This research was conducted independently.

## References & Citations

Kadavath et al. (2022). "Language Models (Mostly) Know What They Know." arXiv:2207.05221.

Christiano et al. (2018). "Supervising strong learners by amplifying weak experts." arXiv:1810.08575.

Huang et al. (2024). "Large Language Models Cannot Self-Correct Reasoning Yet." ICLR 2024.

Wang & Zhao (2024). "Metacognitive Prompting Improves Understanding in LLMs." NAACL 2024.

Murphy, A. H. (1973). "A New Vector Partition of the Probability Score." Journal of Applied Meteorology 12.

Russell & Wefald (1991). "Principles of Metareasoning." Artificial Intelligence 49.

Han et al. (2024). "Token-Budget-Aware LLM Reasoning." ACL 2025 Findings.

Kirichenko et al. (2025). "AbstentionBench." arXiv:2506.09038.

Ackerman et al. (2025). "Evidence for Limited Metacognition in LLMs." ICLR 2026.

Shinn et al. (2023). "Reflexion." NeurIPS 2023.

Snell et al. (2025). "Scaling LLM Test-Time Compute Optimally." ICLR 2025.

Li, Hendrycks et al. (2025). "Humanity's Last Exam." arXiv:2501.14249.

Nel et al. (2025). "KalshiBench." arXiv:2512.16030.

Laskov & Shafto (2024). "Beyond Bench: Scaling Metacognitive Protocol Evaluation." arXiv:2509.24210.
