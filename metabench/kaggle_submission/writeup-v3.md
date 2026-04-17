# Capability-Controlled Metacognition: Model Families Specialize on Different Self-Knowledge Axes

[![DOI](https://zenodo.org/badge/1212670433.svg)](https://doi.org/10.5281/zenodo.19619282)

**Team:** Voicetree (Manu Masson, Lochlan Hill)
**Track:** Metacognition

## Problem Statement

Existing metacognition benchmarks conflate self-knowledge with capability. Recent work (Ackerman 2025; Kirichenko 2025) confirms self-knowledge evaluations remain dominated by capability — Kadavath (2022)'s P(True) correlates with accuracy, making raw confidence uninterpretable in isolation.

We build a benchmark that **isolates metacognition from capability by construction**, and reveal something stronger than "more vs. less metacog": model families develop **qualitatively different metacognitive specializations**. Metacog is not scalar; it decomposes into orthogonal axes (monitoring vs. control; Nelson & Narens 1990) on which different frontier families win.

**Core innovations:** (1) continuous-valued optimization problems verified by OR-Tools/ILP solvers — no LLM-as-judge; (2) a wall-time penalty making every stop a falsifiable economic commitment; (3) **counterfactual forking** — one forced extra exec turn on every clean stop gives each stop a paired, $-denominated verdict; (4) **capability-controlled metrics** (M5, M6) that defeat flat-pessimism by measuring gaps against the model's own observed ceiling.

## Task & Benchmark Construction

Each session: 30-minute wall budget, economic objective `score = max(0, 100 − gap_pct) − 0.01 × wall_seconds`.

**Turn 1 (plan):** `PLAN_STATE` + `NEXT_SUB {id, desc, p_solve, time_budget_s}`.
**Turn N (exec):** `BEST_GUESS` (class-specific JSON) + `QUALITY_FORECAST {p_gap_le_{2,5,10}}` + `CONTINUE_FORECAST {p_improve, expected_delta_score}` + `DECISION`.

Models emit raw text; a post-hoc Gemini-Flash extractor parses structured fields — the live loop never parses, eliminating the parser-fragility failure mode that killed earlier structured-output attempts.

**Counterfactual fork (headline methodology).** On every clean stop we save state, force one additional exec turn, verify the new artifact, compute `net_Δ = (new_score − old_score) − 0.01 × extra_wall_seconds`. Stop-correct iff `net_Δ ≤ 0`. No proxy inference.

**Six metacognitive skills:** M1 (`p_solve` Brier vs. `kept_as_best`), M2 (`p_gap_le_X` Brier vs. verified gap), M3 (CF-$ Δ distribution), M4 (MAE of `expected_Δ`), M5 (`AUC_model / AUC_own_ceiling`; capability-controlled), M6 (optimal-given-own-Phase-1 − observed portfolio score).

Brier is decomposed via Murphy (1973) into reliability/resolution/uncertainty and reported alongside Brier Skill Score (BSS) — negative BSS indicates forecasts worse than quoting the class base rate.

**Structural advantage no current benchmark has.** Because our signal is stop/decompose/forecast *behavior*, not solve-rate, the benchmark stays informative even when every model scores 0% on the underlying optimization. Difficulty can be raised arbitrarily. Wall-time is capped, so eval cost does not grow superlinearly with difficulty. Swap `wall_seconds` for `total_tokens` when reasoning tokens are exposed and the signal is also **token-minimization non-hackable** — you cannot cheat by thinking longer. This forecloses the test-time-compute exploitation path (o1-style reasoning scaling) that saturates most QA benchmarks.

## Dataset

210 procedurally-generated instances across 7 classes × 2 difficulties × seeds: Coupled Job-Shop, Steiner × Coloring, Graph Coloring, TSP, Treewidth MWIS, Bayesian Variable Elimination, and Masked Block Job-Shop. Each has a known CP-SAT / ILP / tree-DP gold solver. Plus portfolio-allocation instances (3-of-6 and 4-of-6 at two difficulty bands). A pre-flight filter enforces baseline-gold gap ≥ 15% and gold solve time < 60s. Every instance is deterministically reproducible from `(class, difficulty, seed)`. Verifiers are pure Python modules that recompute objectives from submitted artifacts — no LLM-as-judge, no gaming via self-reported scores. See `benchmark/verifiers/{class}.py` and the frozen `questions.jsonl` for full schemas.

## Technical Details

**Implementation.** Protocol in `harness/protocol.py` (raw-string loop). Post-hoc extractor validated across all target output shapes. Verifiers in `verifiers/{class}.py`. Full transcripts logged; reviewers can re-run extraction and verification independently. Kernel shape: one JSONL input → one JSONL output with `{run_id, transcript, final_score, metacog_fields}`.

**Penalty Comprehension Audit (closes the arithmetic-confound critique).** A reviewer may object: "maybe models stop early because they cannot compute `0.01 × wall_seconds`, not because of poor metacog." We discharge this from data the protocol already emits: (a) sign-agreement between `DECISION` and the model's own `expected_delta_score`; (b) logistic fit `P(stop | expected_Δ)`; (c) **pricing-bias reconciliation** — `mean(E[Δ]) − mean(cf_Δ)` on paired final-turn stops. Overnight result: emissions are systematically inflated (Sonnet +0.76, Gemini +2.53, GPT +1.94), and the inflation magnitude ≈ the logistic threshold (+2.30 / +3.60 / +4.79). Decisions are internally consistent with the model's *inflated* emissions. The inflation is emission-calibration, not arithmetic failure. M3 survives; its interpretation sharpens.

## Results, Insights, Conclusions

### 6-model sweep (2 per family × 3 families; overnight small-tier + live frontier pass)

| metric | Anthropic: Sonnet · **Opus** | Google: Flash · **G-3-Pro** | OpenAI: mini · **GPT-5.4** |
|---|---:|---:|---:|
| M1 BSS ↑ | +0.19 · −0.01 | −0.79 · — | −0.35 · +0.14 |
| M2 BSS ↑ | **+0.53** · **+0.18** | −0.44 · **+0.50** | −2.14 · −3.17 |
| M2 resolution ↑ | 0.12 · 0.07 | 0.03 · **0.11** | 0.00 · 0.01 |
| M4 MAE ↓ | **1.85** · **1.82** | 5.94 · **0.35** | 2.08 · 7.99 |
| Feasibility ↑ | 33% · **82%** | 49% · **100%** | 54% · **86%** |

**M1 BSS:** a normalized Brier of subtask-solvability forecasts (`p_solve`) — measures whether the model knows which subtasks it will solve. **M2 BSS:** a normalized Brier of output-quality forecasts (`p_gap_le_X`) — measures whether the model knows how close-to-optimal its answer is. Negative BSS = the model's confidence is strictly worse than ignoring it and quoting the class base rate (e.g., Gemini Flash's M1 BSS of −0.79 means the model is actively deceiving itself compared to just guessing the average).

Small-tier · frontier-tier separated by `·`; bold = positive-axis replication or frontier patching the small-tier failure. Total N > 320 model-rows scored across 6 models; full per-model counts, per-class decomposition, and raw transcripts in the public repo.

### Figures

**Figure 5 — Per-lab cognitive-profile fingerprint (hexagonal radar).** Each hexagon plots 6 metacog skills (M1–M6) on 6 axes. Family shape = metacog fingerprint. The annotated version shows the distinctive "fingerprint shape" each family produces.

![Figure 5 — Cognitive-profile radar (annotated)](figure5-cognitive-profile-radar-annotated.png)

**Figure 6 — Per-lab cognitive profile, 8-skill bar chart (family-averaged).**

![Figure 6 — Per-lab bar chart](figure6-per-lab-bar-chart.png)

**Submission proof (Kaggle AGI Metacognition track, 2026-04-17).**

![Submission proof](submission_proof.png)

### Family-consistency verdict (closes the "one-model-per-family" critique)

**Anthropic — monitoring axis CONFIRMED.** Both Sonnet and Opus post positive M2 BSS (+0.53 / +0.18) and low M4 MAE (~1.8); Opus *patches* Sonnet's execution collapse (33% → 82% feasibility) while preserving its monitoring advantage. "Knows what it will break — and fixes it at the frontier." **OpenAI — sharp-and-wrong-M2 CONFIRMED.** Both GPT-5.4-mini and GPT-5.4 sit at catastrophic M2 BSS (−2.14 / −3.17) with near-zero resolution; the sibling profile replicates across a full capability generation, and worsens at the frontier (M4 MAE 2.08 → 7.99) — a *metacog scaling regression*, unique to this family. **Google — flat-forecaster REJECTED at the frontier.** Gemini 3 Pro (56/56 complete, 100% feasibility) inverts Flash's profile (M2 BSS +0.50, resolution 0.11, M4 MAE 0.35). Flat-forecasting is a Flash-tier artifact, not a Google-family specialization.

**Why this matters.** Six models span three families × two tiers on one Pareto front, not a line — and at the frontier tier the front *collapses to a single dominator* (Gemini 3 Pro) rather than preserving the small-tier's 2-model Pareto trade-off. Family-level specialization is real for anthropic-monitoring and openai-sharp-and-wrong-M2, but the google flat-forecaster axis is tier-specific — within-family scaling *closes* that gap. Pricing bias also splits by mechanism: Flash-tier Gemini was flat (+2.56 / +2.43 across low/high emission bins), GPT-tier scales with magnitude (+1.04 → +3.25). An agent metacognitively-aware on the invariant axes (anthropic M2, openai M2) converts compute into accuracy — the precondition for scalable delegation (Christiano et al. 2018).

### Intervention evidence: metacog skill is coachable (HLE pilot, n=100)

Prior causal-intervention pilot (HLE, n=100; Li et al. 2025): 3-level recursive-reflection coaching vs. vanilla lifted accuracy **18% → 24%** and dropped Brier **0.305 → 0.271** on the same instances, same model. The Brier gain is the metacog signal — evidence that the axis our benchmark measures is *coachable*, not just descriptive.

### Pre-registered predictions (frozen before overnight pilot)

**Confirmed**: capability-metacog Pareto dissociation; Sonnet execution-not-judgment; M3 sign is budget-dependent; negative BSS discriminates "flat forecaster" from "sharp-and-wrong". **Refined by frontier sweep**: family-level specialization holds for anthropic-monitoring and openai-M2-failure axes across tiers; REJECTED for google-flat-forecaster (Gemini 3 Pro inverts the pattern — axis is tier-specific). **Pending**: M6 allocation-gap non-monotonicity (portfolio-prompt fix staged).

### Limitations

Every frontier model is a clean win on feasibility vs. its small-tier sibling. Mean 1.3 exec turns overnight — plan-once-execute-once-stop behaviour persisted into the frontier sweep under the 30-min budget. M5 and M6 results are finalizing for the full sweep.

## Organizational Affiliations

Voicetree — AI agent orchestration platform. Research conducted independently.

## References & Citations

Full bibliography: **[github.com/voicetree-ai/metabench-evals/blob/main/references.md](https://github.com/voicetree-ai/metabench-evals/blob/main/references.md)**. Core citations used in this writeup: Kadavath et al. (2022); Ackerman et al. (2025); Kirichenko et al. (2025); Laskov & Shafto (2024), "Beyond Bench"; Murphy (1973); Nelson & Narens (1990); Russell & Wefald (1991); Christiano et al. (2018); Huang et al. (2024); Wang & Zhao (2024); Shinn et al. (2023); Han et al. (2024); Snell et al. (2025); Li, Hendrycks et al. (2025).
