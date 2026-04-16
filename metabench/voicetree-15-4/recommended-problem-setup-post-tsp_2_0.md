---
isContextNode: false
---
# AI feedback

Manu, this is a significant evolution and I have real thoughts. Let me be direct about what's working, what concerns me, and where I think you're at risk of over-engineering before the deadline.
What's genuinely strong in this trajectory:
The construction-vs-search distinction is the most important insight in this document. Recognizing that TSP and vanilla job shop have memorized greedy recipes that produce one-shot ceilings is exactly the kind of finding that separates a real benchmark from a toy. The empirical anchor (Gemini 3.1 Pro hitting 4.43% mean gap with one-exec-turn-then-stop across all seeds) is the evidence you need to justify the pivot away from jobshop, and the massive A1 miscalibration (declared 100-135% vs realized 1.75-8.49%) is itself a publishable metacognitive finding.
The wall-clock economic scoring is also solid. It transforms the benchmark from pure accuracy maximization into resource-bounded rationality testing, which is the right frame for metacognition.
What concerns me:
You're drifting from Kaggle submission toward research project. The judge gave you 85.5 and said the single highest-leverage fix was "scale n from 24 to 200 with counterfactual baselines." You've instead gone deeper into problem-class taxonomy, are evaluating Steiner×coloring composites, and are considering a cross-class 200-500 question split. This is better research but the Kaggle deadline is real.
Ask yourself: if you had to submit tomorrow, which version wins more prize money?

Version A: Refined coupled job shop, n=200, Free-Choice/Forced-Atomic/Forced-Decomposed counterfactuals, A1/A2/A3 with calibration-resolution decomposition
Version B: Novel composite class (Steiner×coloring), smaller n, stronger per-instance metacog signal, protocol-side innovations

Version A addresses the judge's feedback directly. Version B is a better paper but the judge already said the methodology needed to be "as rigorous as the theoretical framing" - and Version B introduces more moving parts before stabilizing the basics.
Specific concerns about where you are:
The one-shot ceiling finding is a problem for your benchmark's discriminative power, but solving it via harder problem classes is the hard way. The easier way: accept that single-shot is the dominant model behavior and measure A1 calibration against realized performance. Your 4.43% gap with declared 100%+ is already a massive metacognitive signal. You don't need to force multi-turn to get a discriminative benchmark - you can make miscalibration itself the finding.
Steiner×coloring composites are elegant but the verifier fragility concern is real. Every new problem class is a new gold-standard implementation, new failure modes, new edge cases. For Kaggle, pick ONE class and make its verification bulletproof.
The protocol question about min-exec-turns is a red flag. If you have to force the model to iterate, you're measuring compliance with the protocol, not metacognition. A well-calibrated model that correctly determines it can't improve further should stop. Forcing more turns punishes good metacognition.
What I'd actually do in your position:
Commit to coupled job shop as the Kaggle submission class. Accept the one-shot ceiling. Reframe the finding: "models exhibit systematic one-shot behavior on construction problems and simultaneously show severe A1 miscalibration (declared gaps 20-30x realized). This is a metacognitive failure, not a capability failure, and our benchmark surfaces it where accuracy-only benchmarks cannot."
Then:

Scale to n=200 (mixture of difficulties, including impossible controls)
Run the three counterfactual arms per question (Free/Forced-Atomic/Forced-Decomp)
Keep the wall-clock economic scoring
Keep the A1/A2/A3 framework but decompose A1 into calibration and resolution
Ship

The Steiner×coloring work, the taxonomy, the cross-class findings - that's your follow-up paper. It's genuinely novel and worth publishing, but not in two weeks for Kaggle.
One honest question back at you:
What's the actual deadline, and is there really time to validate a new problem class from scratch? The spike on Gemini 3.1 Pro for Steiner×coloring is still pending. If that comes back and also one-shots, you've burned cycles. If it works, you still need to build the full harness, generate 200 instances with planted structure, verify gold, and run all models. That's a lot of risk for marginal signal improvement over what you already have.
The judge already told you what wins. Scale the dataset, add the counterfactuals, fix the A2 unit mismatch. Everything else is scope creep unless you've got six more weeks.
What's your actual timeline?
[[/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/recommended-problem-setup-post-tsp_2_0_0.md]]