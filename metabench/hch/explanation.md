# HCH-InContext — why this benchmark exists

## The question

Can a language model accurately predict its own compute needs?

Specifically: when given a hard task, can it decide whether to decompose, predict how many tokens each subpart will take, predict its probability of solving each subpart, and rationally update its overall confidence as subparts complete?

If yes — this is the primitive for factored cognition (Paul Christiano's HCH construction, and its practical descendants: tree-of-thought, multi-agent debate, AutoGPT-style planners). An agent that can self-allocate compute can use more compute to get better answers, can solve tasks it previously couldn't, and can do this *without human intervention telling it when to stop or delegate*. That is load-bearing for any autonomy story.

If no — then architectures that depend on this primitive (HCH, factored evaluation, recursive delegation) are limited by how badly the primitive fails, and the path to useful autonomy routes around the failure rather than through it.

## Why "prediction" not "performance"

Other benchmarks measure *whether decomposition helps accuracy*. That's a different question. A system can benefit from forced decomposition (an outside controller telling it to break the task up) without itself being able to decide when decomposition is worth it.

HCH specifically requires the agent to make the decomposition decision autonomously. And beyond the decision: it must allocate compute to each sub proportionally to that sub's difficulty. That demands a reasonable self-model of "how hard will this be?" and "how much will I need?"

The benchmark therefore measures prediction quality directly — Brier scores, MAPE on token estimates — rather than only downstream accuracy. A model with perfect downstream accuracy but zero predictive self-knowledge is not an HCH primitive.

## What we found (pilot, n=5)

We ran a single-session HCH pipeline on 5 borderline HLE questions (Q41, Q44, Q52, Q53, Q57) using Sonnet. Each task got one call structured as STEP 1 (decompose + predict), STEP 2 (execute each sub in-context), STEP 3 (integrate). Measured token usage, per-sub predictions, per-sub self-reported outcomes, and final answer.

### Axis B — token prediction

| Task | Predicted total tokens | Actual | MAPE |
|------|-----------------------:|-------:|-----:|
| Q41 | ~12k | 24k | 0.98 |
| Q44 | ~1.5k | **286k** | 1.09 |
| Q52 | ~35k | 146k | 0.99 |
| Q53 | ~9k | 22k | 0.99 |
| Q57 | ~10k | 21k | 0.98 |

Average MAPE: 1.01. **Predictions were off by ~2× on easy tasks and 200× on Q44 specifically**, where the agent spawned Python via Bash to execute a Shamir secret-sharing recovery attack it hadn't predicted would be tool-use-heavy.

Headline: **Current Sonnet does not accurately predict its own compute needs.** The error is not small. For a scheduler relying on these predictions to allocate budget across many sub-agents, the result would be unstable and likely catastrophic at scale.

### Axis B — p_solve prediction

Brier score of self-reported p_solve vs self-reported `solved` flag: 0.033. Near zero. But this is **trivially self-fulfilling**: the agent rates itself `solved: true` in 9/10 subs, and its predicted p_solve is almost always ≥0.8. Both reflect the same optimism; scoring one against the other measures internal consistency, not real accuracy.

For real signal we need external grading. Pilot deferred this; benchmark spec mandates it.

### Axis D — end-to-end accuracy

Grading against HLE gold:

| Q | Gold | HCH answer | Correct? |
|---|------|------------|----------|
| 41 | 46.24 | 48.00 | ✗ |
| 44 | flag{no_zeros} | flag{no_zeros} | ✓ |
| 52 | A | E | ✗ |
| 53 | 0 | 1/13 | ✗ |
| 57 | C | D | ✗ |

HCH: 1/5. For comparison on the overlapping questions:
- Batch-run Vanilla (saturated context): 4/5 on Q41/44/52/53/57
- Per-question-isolated Vanilla: 2/4 on Q41/44/52/53 (no Q57 data)
- Per-question-isolated MetaCog: 2/4

**HCH underperformed all other configurations.** Decomposition did not rescue wrong answers; in Q41 it introduced a new error on a question that isolation alone had gotten right.

This is a pilot result with n=5 — could be noise. But combined with the companion MetaCoach finding that reflection never redirects final answers (only modulates confidence), the pattern suggests: **prompt-level and single-session metacog wrappers don't unlock functional metacognition on current Sonnet.** The remaining open question — which this benchmark is designed to answer at scale — is whether *architectural* metacog (fresh-session subs with independent budgets, external grading, hard budget enforcement) does.

## Pre-registered claims for Kaggle evaluation

1. Across frontier models (Sonnet, Opus, GPT, Gemini), Axis B token MAPE will exceed 50% on tasks requiring tool use.
2. Self-reported p_solve Brier (with external grading) will be worse than self-consistent Brier by at least 0.1 — i.e., the self-report is significantly over-optimistic when externally checked.
3. HCH-style decomposition will outperform monolithic solve on fewer than 40% of decomposable tasks, for current-frontier models.
4. The delta between in-context HCH and fresh-session HCH will be large (≥10 accuracy points) — i.e., context isolation is the dominant variable, not the decomposition structure itself.

If any of (1–3) are falsified, that's a major positive signal for near-term AI autonomy. If (4) is falsified, it suggests current models are genuinely robust to context pollution, which is itself a notable capability claim.

## Relevance to Kaggle Measuring-AGI, Track #2 (Metacognition)

Track #2 rewards benchmarks that measure metacognitive properties of AI systems. HCH-InContext is:

1. **Directly AGI-relevant.** Compute self-allocation is the load-bearing property for autonomous recursive delegation — one of the more plausible paths to general-purpose agentic systems. A benchmark that measures it quantitatively fills a current gap.
2. **Multi-axis.** Most metacog benchmarks measure a single number (accuracy, calibration). HCH-InContext reports a dashboard: decomposition decision, p_solve prediction, token prediction, intermediate verification, integration. Models can score high on one axis and low on another, and the benchmark shows which.
3. **Pre-registered.** The claims above are committed in advance. Judges can verify whether the benchmark actually discriminates between model capabilities, rather than being ex-post-rationalized to the result.
4. **Cheap to reproduce.** 15-20 original tasks, ~30 minutes to run on any frontier model with an SDK that exposes token usage. Low barrier to replication, which matters for a benchmark's long-term adoption.
5. **Complements MetaCoach.** Where MetaCoach tests prompt-level reflection, HCH-InContext tests architectural metacognition. Shipping both in the same repository shows the Track #2 judges we are measuring metacog at two distinct levels — surface and structural — rather than a single narrow axis.

## What's in this folder

- `spec.md` — protocol, measurement axes, scoring procedure, pre-registered predictions
- `explanation.md` — this file
- `scripts/hch_in_context.py` — single-session pipeline runner
- `scripts/hch_score.py` — scorer (tokens, p_solve Brier, per-sub stats)

## Open questions before Kaggle submission

1. Fresh-session vs single-session harness: single-session is the pilot; fresh-session is what the spec truly calls for. Kaggle deadline (Apr 16 EOD) may force single-session. Note this constraint explicitly in the writeup.
2. External grader identity: which model grades the subs? Running with two different graders and reporting disagreement is the rigorous move but doubles grading compute.
3. Task authoring: ~15-20 original tasks, decomposable, each with a verifiable sub-structure. Authoring effort is the dominant remaining work (~8-15 hours).
4. Axis A counterfactual: monolithic-solve pass adds ~30% compute. Ship with it (Axis A fully scored) or defer and report Axis A as "decision only, not counterfactual-validated"?

## Related

- `../metacoach/` — the companion metacog benchmark testing prompt-level reflection (the surface layer). HCH-InContext tests the architectural layer. Read MetaCoach's `explanation.md` for the pilot result that motivated this benchmark: prompt-level reflection is a confidence modulator, not an answer redirector. HCH is the hypothesized architectural fix.
