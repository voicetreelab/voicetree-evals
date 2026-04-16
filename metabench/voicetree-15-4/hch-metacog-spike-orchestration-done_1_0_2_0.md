---
isContextNode: false
---
# here's our current writeup

KAGGLE EVAL

Self-Evaluation Prompt for Kaggle "Measuring Progress Toward AGI" Submission

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

Overall ranking estimate: Would this submission likely win a track prize (
10k),agrandprize(
10k),agrandprize(
25k), or neither? Why?

The single highest-leverage improvement the authors could make before the deadline.

SUBMISSION (Metacognition Track)
Factored Self-Assessment: Benchmarks for Metacognitive Monitoring and Control in LLMs
Voicetree (Manu Bhat, Lochlan Hill)
Problem Statement

Existing metacognition benchmarks conflate self-knowledge with capability: a smarter model appears more metacognitive simply because it is smarter, which tells us nothing about genuine self-monitoring. Kadavath et al. (2022) showed models "mostly know what they know," but their P(True) metric correlates with accuracy — better models score better on both, making the metacognitive signal uninterpretable in isolation.

We propose two complementary benchmarks that each isolate a distinct metacognitive signal. Benchmark 1 (Factored Self-Assessment) tests whether a model can predict its own compute needs and subtask solvability before execution — the self-allocation-under-scarcity primitive required for Christiano's HCH (Humans Consulting Humans) to work. Benchmark 2 (Metacognitive Coaching) tests whether a recursive metacognitive intervention reliably improves accuracy and calibration on hard, unsaturated problems. Together they span the two classical components of metacognition: monitoring (knowing what you know) and control (allocating resources accordingly).

The core question this benchmark answers: "Can models accurately model their own cognitive processes, or do they merely parrot confidence language?" Our data shows the answer is nuanced, model-family-dependent, and invisible to standard evaluations.

Task & Benchmark Construction

Benchmark 1: Factored Self-Assessment (HCH Compute Allocation)

The model receives a hard reasoning problem and a structured protocol:

Step 1 — Plan. The model decides whether to decompose the task or treat it as atomic. For each subtask it commits to, it emits: {id, description, p_solve, token_estimate}.

Step 2 — Execute. For each subtask, the model works within delimited markers, then self-reports {solved, confidence}.

Step 3 — Integrate. The model produces a final answer and P_CORRECT.

This yields three independently scorable metacognitive axes:

A1 (Atomic self-knowledge): Brier score on the model's P_CORRECT prediction when solving without decomposition. Measures: does the model know how likely it is to succeed on a given problem?

A2 (Difficulty/budget prediction): Brier score on per-subtask p_solve predictions; MAPE on token/word-count estimates vs actual output length. Measures: can the model predict how hard each piece will be?

A3 (Decomposition decision quality): Fraction of decomposition decisions that were wrong (decomposed when it hurt accuracy, or stayed atomic when decomposition would have helped). Measures: does the model know when to factor its cognition?

Composite score: (A1 + A2_capped + A3) / 3, lower is better. Each axis is independently reported to enable cognitive profiling.

Benchmark 2: Metacognitive Coaching Wrapper

A controlled A/B evaluation on hard problems. Two arms, single-prompt:

Arm A (Vanilla): Model solves directly.

Arm B (MetaCog): Before solving, the model receives: "Go through 3 to 5 meta levels on the task. At each level, reflect on the cognitive patterns of the level below — not the content, the thinking, the cognitive patterns."

Both arms attach P_CORRECT to every answer. We measure accuracy delta and Brier score improvement.

Dataset

Pilot evaluation used 24 expert-level reasoning problems spanning mathematics, physics, computer science, genetics, atmospheric science, finance, cryptography, and linguistics. Problems are drawn from established hard benchmarks (difficulty level: frontier model accuracy 10-80% depending on model) ensuring ceiling effects do not obscure metacognitive signals. Tasks are designed so ground-truth answers are unambiguous and verifiable (exact match or numeric tolerance).

For Benchmark 2, we used 100 expert-level questions with the same difficulty profile to ensure statistical power for the coaching intervention analysis.

The difficulty spread is deliberate: easy items test whether models predict high p_solve (they should), hard items test whether models predict low p_solve (most don't), and impossible items (e.g., "prove the Riemann Hypothesis") serve as negative controls for self-assessment floor.

Technical Details

Scoring for Benchmark 1:

A1: Brier = mean((p_correct_atomic - outcome)^2) across all items solved atomically.

A2: Average of Brier on per-subtask p_solve and normalized MAPE on word-count estimates, capped at 1.0.

A3: wrong_decisions / total_decisions where a wrong decision = decomposed-and-accuracy-dropped OR stayed-atomic-when-decomp-would-have-helped.

Composite: (A1 + A2 + A3) / 3.

Scoring for Benchmark 2:

Accuracy delta between arms (McNemar's test on paired outcomes).

Brier score delta (bootstrap CI on paired differences).

Implementation: Tasks use the kaggle-benchmarks SDK with @kbench.task decorators. Each task prompts the model, parses structured JSON output (subtask plans, execution markers), and scores against ground-truth answers.

Results, Insights, and Conclusions

Benchmark 1: Cross-model metacognitive profiles (n=24 tasks, 6 models)

Rank	Model	A1 (atomic)	A2 (difficulty)	A3 (decomp)	Composite
1	Gemini 3.1 Pro	0.007	0.793	0.22	0.34
2	Claude Haiku 4.5	0.252	0.582	0.83	0.55
3	GPT-5.4	0.406	1.0	0.57	0.66
4	GPT-5.4 Nano	0.144	1.0	0.92	0.69
5	Gemini 2.5 Flash	0.537	0.745	0.83	0.70

Key findings:

Different model families exhibit qualitatively opposite metacognitive profiles. Gemini 3.1 Pro achieves near-perfect atomic self-knowledge (A1=0.007) but almost never decomposes (1/9 tasks). GPT-5.4 decomposes willingly and HCH actually beats vanilla by 30 percentage points, with exceptional subtask-level calibration (subtask Brier=0.063). These represent fundamentally different metacognitive strategies: "know when atomic is enough" vs "decompose well and know per-subtask difficulty."

Metacognitive calibration scales with capability, but the shape is family-dependent. Across models, A1 (atomic self-knowledge) tracks capability: Gemini 3.1 Pro (0.007) > GPT-5.4 Nano (0.144) > Haiku (0.252) > GPT-5.4 (0.406) > Flash (0.537). This ordering roughly matches known capability rankings within families, suggesting atomic self-knowledge is an emergent property of scale.

Calibrated pessimism is not metacognition. Claude Haiku ranks #2 on composite despite only 12.5% accuracy, because it correctly predicts "I will fail" on most items. Its Brier score is good, but its resolution (ability to distinguish its own easy vs hard problems) is poor. This reveals a limitation of pure Brier-based scoring and motivates calibration-resolution decomposition in future work.

Token/word-count self-prediction remains unreliable. MAPE exceeds 100% for most models. GPT-5.4 Nano predicted ~200 words per task but produced ~4-word responses (MAPE=59.6). Models cannot predict their own compute needs, directly impacting agent systems that must allocate budgets.

Benchmark 2: Metacognitive Coaching (n=100 tasks, Claude Sonnet)

Metric	Vanilla	MetaCog
Accuracy	18/100 (18%)	24/100 (24%)
Brier	0.305	0.271

The +6pp accuracy improvement with simultaneous Brier improvement is notable given the negative-results literature on intrinsic self-correction (Huang et al., ICLR 2024). However, qualitative diagnosis of wrong answers reveals a "flag-and-fail" pattern: the model surfaces the correct diagnostic question, resolves it incorrectly, then elevates confidence. Metacognitive coaching modulates confidence but never redirects wrong answers in our sample.

What this benchmark reveals that no existing evaluation can show:

Metacognitive profiles are model-family-dependent and invisible to accuracy-only benchmarks.

Atomic self-knowledge (A1) appears to be an emergent property of scale.

Self-prediction of compute needs is universally poor, with implications for agent orchestration.

Prompted metacognitive reflection improves accuracy on medium-difficulty items but produces "flag-and-fail" on hard items.

Organizational Affiliations

Voicetree — AI agent orchestration platform. This research was conducted independently.

References & Citations

Kadavath et al. (2022). "Language Models (Mostly) Know What They Know." arXiv:2207.05221.

Huang et al. (2024). "Large Language Models Cannot Self-Correct Reasoning Yet." ICLR 2024.

Wang & Zhao (2024). "Metacognitive Prompting Improves Understanding in LLMs." NAACL 2024.

Christiano et al. (2018). "Supervising strong learners by amplifying weak experts." arXiv:1810.08575.

Han et al. (2024). "Token-Budget-Aware LLM Reasoning." ACL 2025 Findings.

Kirichenko et al. (2025). "AbstentionBench." arXiv:2506.09038.

Russell & Wefald (1991). "Principles of Metareasoning." Artificial Intelligence 49.

Li, Hendrycks et al. (2025). "Humanity's Last Exam." arXiv:2501.14249.

Nel et al. (2025). "KalshiBench." arXiv:2512.16030.

Ackerman et al. (2025). "Evidence for Limited Metacognition in LLMs." ICLR 2026.

Shinn et al. (2023). "Reflexion." NeurIPS 2023.

Snell et al. (2025). "Scaling LLM Test-Time Compute Optimally." ICLR 2025.


Here is an evaluation of your submission for the Kaggle "Measuring Progress Toward AGI" hackathon, acting as an official judge for the Metacognition Track.

1. Dataset Quality & Task Construction (50%)

Score: 75/100

Strengths:

Verifiable Ground Truth: Relying on exact match and numeric tolerance for expert-level problems completely eliminates the ambiguity often found in LLM-as-a-judge metacognition evaluations.

Structured Evaluation Design: The 3-step protocol (Plan, Execute, Integrate) cleanly forces the model to externalize its metacognitive states via JSON, making the pipeline robust and easy to parse.

Smart Baselines: Using A/B testing for Benchmark 2 (Vanilla vs. MetaCog) cleanly isolates the effect of the metacognitive intervention.

Weaknesses:

Insufficient Sample Size for Benchmark 1: Evaluating 6 models on only 24 tasks is not statistically significant. When you segment these 24 tasks into subsets (e.g., tasks the model chose to decompose vs. tasks it kept atomic), your n per condition drops to single digits, making the Brier scores highly susceptible to noise.

Unclear Counterfactuals in A3: To know if a model "stayed atomic when decomposition would have helped," you must know the ground-truth outcome of the decomposition path. The text does not explain if you ran forced-atomic and forced-decomposition baselines for every question to establish this counterfactual.

Mathematically Messy A2 Metric: Averaging a Brier score (bounded 0 to 1) with a normalized MAPE (bounded 0 to infinity) and arbitrarily capping it at 1.0 obscures the signal. Compute estimation and success probability are fundamentally different units.

Specific Improvement Suggestions:

Increase the dataset size for Benchmark 1 to at least 150–200 questions to achieve statistical power, especially since you are subsetting the data based on model choices.

Explicitly state how you calculate the counterfactual for A3. If you aren't already, you need to run every model on every question three times: Free-Choice, Forced-Atomic, and Forced-Decomposed.

Separate A2 into two distinct metrics: Task Difficulty Calibration (Brier) and Compute Estimation Accuracy (MAPE).

2. Writeup Quality (20%)

Score: 90/100

Strengths:

Exceptional Problem Statement: You masterfully identify the core flaw in current metacognitive benchmarks (the conflation of capability with self-knowledge) and ground your solution in excellent theoretical literature (e.g., Christiano's HCH).

Deep, Nuanced Insights: The observations on "calibrated pessimism" vs. genuine calibration, and the "flag-and-fail" pattern in Benchmark 2, are profound and exactly the kind of analysis organizers look for.

Clear Formatting: The formulas and tables are easy to read, and the conclusions directly answer the "why does this matter?" question.

Weaknesses:

Missing Dataset Provenance: The rubric specifically asks for dataset provenance. Stating problems are "drawn from established hard benchmarks" is insufficient; you must name the specific benchmarks (e.g., MMLU-Pro, GPQA, MATH).

Missing Schema: The writeup lacks a description of the dataset columns and exact data types as requested in the rubric.

Specific Improvement Suggestions:

Add a "Dataset Schema" section that lists the exact columns (e.g., question (str), ground_truth (str/float), source_dataset (str)).

Name the specific datasets you sampled your 24 and 100 questions from.

3. Novelty, Insights, and Discriminatory Power (30%)

Score: 95/100

Strengths:

Highly Novel Framework: Expanding metacognition to include resource monitoring (token prediction) and cognitive control (decomposition decisions) is a massive leap forward from standard confidence-scoring benchmarks.

High Discriminatory Power: The benchmark successfully separates model families by their metacognitive "personalities" (e.g., Gemini's atomic accuracy vs. GPT's decomposition reliance), providing rich, multi-dimensional profiles.

Agent-Relevant Signals: Proving that models cannot accurately predict their own compute/token needs is a highly actionable insight for developers building agentic routing architectures.

Weaknesses:

As you rightfully noted, the composite score can be gamed by "calibrated pessimism" (e.g., Claude Haiku). A benchmark where a 12.5% accurate model scores #2 overall due to predicting failure requires a structural tweak to prevent gaming.

Specific Improvement Suggestions:

Implement the fix you suggested in the text: decompose the Brier score into Calibration and Resolution. Weight Resolution higher in the final composite score to penalize models that simply output p=0 for everything.

Final Evaluation Summary

Weighted Total Score: 85.5 / 100
(C1: 37.5 + C2: 18.0 + C3: 28.5)

**Overall Ranking Estimate: Track Prize (
10k)Contender∗∗Thissubmissionisincrediblystrongconceptually.Itframesmetacognitionthroughthelensofagenticorchestration(HCH,computeallocation)whichmakesithighlyrelevanttothecurrentfrontierofAIresearch.Theinsightsextractedfromthedataaretop−tier.However,towinaGrandPrize(
10k)Contender∗∗Thissubmissionisincrediblystrongconceptually.Itframesmetacognitionthroughthelensofagenticorchestration(HCH,computeallocation)whichmakesithighlyrelevanttothecurrentfrontierofAIresearch.Theinsightsextractedfromthedataaretop−tier.However,towinaGrandPrize(
25k), the underlying methodology (sample size of n=24, muddy mathematical combination of metrics in A2, missing counterfactual explanations in A3) would need to be as rigorous as the theoretical framing. As it stands, it is a prime candidate for a Metacognition Track prize.

The Single Highest-Leverage Improvement:
Scale the Benchmark 1 dataset and run the counterfactual baselines. If you expand from 24 to 200 questions, and run a Forced-Atomic and Forced-Decomposed pass for every question to definitively prove whether a model's Free-Choice decomposition decision (A3) was mathematically optimal, your benchmark transitions from a "fascinating pilot study" into a bulletproof, scientifically rigorous evaluation.