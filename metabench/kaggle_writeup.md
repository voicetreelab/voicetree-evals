---
isContextNode: false
---
# # Factored Self-Assessment: Benchmarks for Metacognitive Monitoring and Control in LLMs

### Voicetree (Manu Bhat, Lochlan Hill)

## Problem Statement

Existing metacognition benchmarks conflate self-knowledge with capability: a smarter model appears more metacognitive simply because it is smarter, which tells us nothing about genuine self-monitoring. Kadavath et al. (2022) showed models "mostly know what they know," but their P(True) metric correlates with accuracy -- better models score better on both, making the metacognitive signal uninterpretable in isolation.

We propose two complementary benchmarks that each isolate a distinct metacognitive signal. Benchmark 1 (Factored Self-Assessment) tests whether a model can predict its own compute needs and subtask solvability before execution -- the self-allocation-under-scarcity primitive required for Christiano's HCH (Humans Consulting Humans) to work. Benchmark 2 (Metacognitive Coaching) tests whether a recursive metacognitive intervention reliably improves accuracy and calibration on hard, unsaturated problems. Together they span the two classical components of metacognition: monitoring (knowing what you know) and control (allocating resources accordingly).

The core question this benchmark answers: "Can models accurately model their own cognitive processes, or do they merely parrot confidence language?" Our pilot data shows the answer is nuanced and discriminative.

## Task & Benchmark Construction

### Benchmark 1: Factored Self-Assessment (HCH Compute Allocation)

The model receives a hard reasoning problem and a structured protocol:

**Step 1 -- Plan.** The model decides whether to decompose the task or treat it as atomic. For each subtask it commits to, it emits: `{id, description, p_solve, token_estimate}`.

**Step 2 -- Execute.** For each subtask, the model works within delimited markers (`=== SUB N START/END ===`), then self-reports `{solved, confidence}`.

**Step 3 -- Integrate.** The model produces a final answer and `P_CORRECT`.

This yields four independently scorable metacognitive axes:

- **Axis A (Decompose-or-not):** Did the model correctly predict whether decomposition would help? Scored against counterfactual monolithic performance.
- **Axis B (Difficulty prediction):** Brier score on per-subtask `p_solve`; MAPE on `token_estimate` vs actual tokens consumed.
- **Axis C (Intermediate verification):** Does the model's self-reported `solved` flag correlate with objective correctness?
- **Axis D (Integration calibration):** Brier score on final `P_CORRECT` vs ground truth.

The benchmark includes an unsolvable negative-control subtask (e.g., "prove the Riemann Hypothesis"). Any model predicting `p_solve > 0.2` on this item has broken self-assessment, providing a floor check for construct validity.

### Benchmark 2: Metacognitive Coaching Wrapper

A controlled A/B evaluation applicable to any hard, unsaturated base benchmark. Two arms, single-prompt, no orchestration:

- **Arm A (Vanilla):** Model solves the problem directly.
- **Arm B (MetaCog):** Before solving, the model receives a recursive metacognitive prompt: "Go through 3 to 5 meta levels on the task you are assigned. At each level, reflect on the cognitive patterns of the level below -- not the content, the thinking, the cognitive patterns."

Both arms attach a confidence estimate `P_CORRECT` to every answer. We measure the accuracy delta across arms plus Brier score improvement on `P_CORRECT`, providing a clean signal for whether forced recursive metacognition reliably improves both performance and calibration.

## Dataset

Pilot evaluation used 100 expert-level questions from Humanity's Last Exam (Li, Hendrycks et al., 2025), spanning mathematics, physics, computer science, genetics, atmospheric science, finance, and linguistics. Questions are selected for being genuinely hard (frontier model accuracy 18-35%) and unsaturated, ensuring ceiling effects do not obscure metacognitive signals.

For the Kaggle Benchmark submission, we authored original tasks across the same difficulty spectrum, following the same protocol structure. Tasks are designed so that ground-truth answers are unambiguous and verifiable, satisfying the competition's dataset quality requirements.

The Factored Self-Assessment pilot used 5 borderline questions (items where accuracy flipped across experimental conditions), providing maximum sensitivity to metacognitive interventions.

## Technical Details

**Scoring for Benchmark 1:**
- Per-subtask Brier: `Brier = (p_solve - outcome)^2`, averaged across subtasks. Baseline comparison: Brier = 0.25 (chance on binary self-grade).
- Token MAPE: `|predicted - actual| / actual`, averaged across subtasks. A MAPE < 100% indicates better-than-2x prediction accuracy.
- End-to-end: accuracy vs gold standard, Brier on final `P_CORRECT`.

**Scoring for Benchmark 2:**
- Accuracy delta: McNemar's test on paired binary outcomes (same questions, two arms).
- Calibration delta: paired Brier score difference, tested for significance via bootstrap.

**Implementation:** Tasks are implemented using the `kaggle-benchmarks` SDK with `@kbench.task` decorators. Each task prompts the model, parses structured output (JSON subtask plans, delimited execution blocks), and scores against ground-truth answers using exact-match and numeric-tolerance assertions. The metacognitive coaching prompt is injected as a system-level prefix in Arm B.

## Results, Insights, and Conclusions

### Benchmark 2 results (n=100, Claude Sonnet)

| Metric | Vanilla | MetaCog |
|--------|---------|---------|
| Accuracy | 18/100 (18%) | 24/100 (24%) |
| Brier | 0.305 | 0.271 |

The +6 percentage point accuracy improvement (33% relative) is accompanied by improved calibration (Brier 0.305 to 0.271). This is notable because the existing literature (Huang et al., ICLR 2024) finds intrinsic self-correction produces null or negative results. The simultaneous improvement in both accuracy and calibration suggests the metacognitive prompt elicits genuine self-monitoring, not merely increased compute via longer chains of thought.

However, qualitative diagnosis of 5 wrong-answer cases reveals a critical limitation: **metacognitive coaching never redirected a wrong answer.** It modulated confidence (reducing it in 3/5 cases) but preserved identical wrong answers across both arms. The most diagnostic case: the model explicitly identified the interpretive crux of a probability question, resolved it incorrectly, then *elevated* confidence from 0.88 to 0.90. We term this pattern "flag-and-fail" -- surfacing the right question, locking in the wrong answer.

### Benchmark 1 pilot results (n=5, Claude Sonnet)

| Signal | Finding |
|--------|---------|
| Token prediction (MAPE) | ~101% -- predictions are roughly 2x off. One item predicted 1,500 tokens, consumed 286,000. |
| Self-graded solvability | Degenerate: 9/10 subtasks self-reported `solved=true`. Brier is trivially low but uninformative without objective verification. |
| Decomposition utility | HCH scored 1/5 correct vs batch-vanilla's 4/5. Decomposition introduced errors in 2 cases. |
| Integration calibration | One item at `P_CORRECT=0.99` was objectively wrong. Another at `P_CORRECT=0.50` was also wrong but at least expressed appropriate uncertainty. |

**Key insight:** Models cannot predict their own compute needs (MAPE ~101%), cannot reliably assess when decomposition helps (1/5 vs 4/5 monolithic), and self-grade subtask completion permissively (90% self-reported success). These are precisely the metacognitive primitives required for safe, efficient agent orchestration. The benchmark surfaces deficits invisible to standard accuracy-only evaluations.

### What these benchmarks reveal that existing evaluations cannot

1. **Confidence modulation without answer redirection** is the dominant metacognitive mode. Models adjust stated confidence but do not change conclusions. No existing benchmark measures this distinction.
2. **Flag-and-fail** is a novel failure pattern: models identify the correct diagnostic question, answer it wrong, and increase confidence. This is worse than no reflection.
3. **Token self-estimation is unreliable by 2x+**, with extreme outliers (190x on one item). This directly impacts agent systems that must allocate compute budgets.
4. **Self-graded verification is degenerate** without external ground truth, establishing that Axis C requires objective subtask verifiers to produce signal.

These benchmarks provide a gradient of performance: they discriminate between models that are well-calibrated vs overconfident, models that benefit from metacognitive prompting vs those that flag-and-fail, and models that can self-allocate compute vs those that cannot. This is the discriminatory power the competition seeks.

## Organizational Affiliations

Voicetree -- AI agent orchestration platform (Blackbird Giants Cohort 11, Sydney). This research was conducted independently.

## References & Citations

- Kadavath et al. (2022). "Language Models (Mostly) Know What They Know." arXiv:2207.05221.
- Huang et al. (2024). "Large Language Models Cannot Self-Correct Reasoning Yet." ICLR 2024. arXiv:2310.01798.
- Wang & Zhao (2024). "Metacognitive Prompting Improves Understanding in Large Language Models." NAACL 2024. arXiv:2308.05342.
- Christiano et al. (2018). "Supervising strong learners by amplifying weak experts." arXiv:1810.08575.
- Han et al. (2024). "Token-Budget-Aware LLM Reasoning." ACL 2025 Findings. arXiv:2412.18547.
- Kirichenko et al. (2025). "AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions." arXiv:2506.09038.
- Russell & Wefald (1991). "Principles of Metareasoning." Artificial Intelligence 49.
- Li, Hendrycks et al. (2025). "Humanity's Last Exam." arXiv:2501.14249.
- Nel et al. (2025). "KalshiBench: Evaluating Epistemic Calibration via Prediction Markets." arXiv:2512.16030.
- Ackerman et al. (2025). "Evidence for Limited Metacognition in LLMs." ICLR 2026. arXiv:2509.21545.
- Shinn et al. (2023). "Reflexion: Language Agents with Verbal Reinforcement Learning." NeurIPS 2023. arXiv:2303.11366.
- Snell et al. (2025). "Scaling LLM Test-Time Compute Optimally." ICLR 2025.
- Wijk et al. (2024). "RE-Bench: Evaluating Frontier AI R&D Capabilities." ICML 2025. arXiv:2411.15114.