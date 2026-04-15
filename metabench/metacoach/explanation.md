# MetaCoach — why this benchmark exists

## The question

When we wrap a language model in a "reflect before you answer" protocol, what actually changes?

Most metacognition benchmarks report accuracy and Brier score. Both improved? Metacog works. Neither improved? It doesn't. This dichotomy misses the most interesting question: **is the model redirecting its answers based on reflection, or just modulating its confidence around the same answer it would have given anyway?**

These are very different capabilities.
- A **confidence modulator** makes the model say "I am 0.7 confident" instead of "I am 0.9 confident" on the same wrong answer. Useful for calibration, but not for accuracy.
- An **answer redirector** makes the model change its answer from wrong to right (or wrong to less-wrong) because reflection surfaced a crux it would otherwise have missed.

Only the second is load-bearing for agentic systems. An AI research assistant that reflects and still gives the wrong answer with appropriately low confidence is only marginally more useful than one that doesn't reflect at all — it still needs human review to catch the error. The redirector is what unlocks autonomous work.

## What we found (pilot)

We ran Sonnet on HLE (Humanity's Last Exam) Q41-100 with and without the metacog wrapper, under two architectures:

### Architecture 1 — Batch (one agent per 60-question block)

- Vanilla: 9/60 correct, Brier 0.382
- MetaCog: 5/60 correct, Brier 0.302

MetaCog *underperformed* on accuracy despite better calibration. Trace analysis revealed this was an architecture artifact: the metacog agent used 68 tool calls vs vanilla's 37 (reflection correctly triggered more exploration on hard questions), saturating context. At final synthesis — where the agent emits all 60 answers in one block — MetaCoach's saturated context produced "format inversion": the agent knew the answer (visible in its own trace) but emitted a wrong-format value at synthesis time. MCQ questions got exact-match-style answers; exact-match questions got MCQ letters.

### Architecture 2 — Per-question isolation (one agent per question)

We rebuilt the harness to give each question a fresh session. On a n=15 mini rerun:
- Vanilla recovered previously-wrong answers (Q41, Q48 flipped from wrong to right)
- MetaCoach recovered the cybersecurity Q44 (batch: got "3" because it failed to retrieve an answer that was literally stated in the problem; isolated: emitted `flag{no_zeros}` correctly)
- Format-inversion errors disappeared entirely

The architecture bug was real. Isolation fixes it. But isolation alone accounts for most of the gains — metacog's marginal contribution remains unclear.

### The decisive finding

On 5 questions where both isolated arms emitted wrong answers (Q42, Q46, Q47, Q52, Q53), we read the full reasoning traces. The finding was stark:

> **MetaCoach never changed a final answer across all 5 wrong questions.** It only modulated confidence — down in 3 cases, up in 1 case (wrongly), neutral in 1. Zero net answer-redirection value.

On Q53, MetaCoach asked exactly the right crux question during its pre-reflection ("does 0 count as even?"), resolved it mathematically correct but linguistically wrong, and *elevated* its confidence from baseline to 0.90 on the wrong answer. "Flag and fail" — worse than no reflection, because the conviction-of-having-examined-it locks the error in.

On Q46, MetaCoach explicitly computed the correction term that would have led to the right answer, then formally discarded it via a (wrong) regime check. The reflection built the tool and dropped it.

## Why this is a benchmark

The pilot suggests a real, measurable phenomenon:

> Prompt-level metacog wrappers around current frontier models act as confidence modulators, not answer redirectors.

If this holds at scale and across models, it's a significant result — it implies the path to functional metacognition is architectural (sub-agent decomposition, adversarial verification, fresh-session sub-reasoning) rather than prompt-level (reflection scaffolds at the surface). It also implies that a lot of what's called "chain-of-thought metacognition" in the literature is confidence theater.

But prior benchmarks can't tell us this, because they only report accuracy and calibration as aggregate scores. They conflate:
- "MetaCog got 5 right that Vanilla got wrong, and 5 wrong that Vanilla got right" (high redirection, zero net)
- "MetaCog got the same 5 right and Vanilla got the same 5 right, but with better confidence values" (zero redirection, same net)

Both show as +0 accuracy. The first means the protocol is chaotically redirecting; the second means it's doing nothing structural. These have very different implications and demand different follow-up work.

MetaCoach instruments the difference directly by running paired Vanilla and MetaCog arms on the same isolated questions and measuring **answer-level divergence** — not just aggregate metrics.

## Relevance to Kaggle Measuring-AGI, Track #2 (Metacognition)

Track #2 rewards benchmarks that measure metacognitive properties of AI systems. The redirect-vs-modulate axis is:

1. **Novel.** No existing public benchmark reports answer-redirection rate between reflected and unreflected arms of the same model.
2. **Diagnostic.** A model that scores high on accuracy improvement via metacog must show redirection; a model that shows only calibration improvement cannot falsely claim "metacog works" on this benchmark.
3. **Implementation-agnostic.** Any wrapper protocol (chain-of-thought, tree-of-thought, reflection, constitutional AI, debate) can be run as an Arm 2 against the same Vanilla control. Apples-to-apples across metacog families.
4. **AGI-forward.** If current systems fail the redirect axis, that's load-bearing evidence for the claim that pre-AGI systems need architectural interventions (factored cognition, HCH, multi-agent debate) rather than prompt-level refinement. This directly motivates the companion HCH benchmark in the same repository.

## What's in this folder

- `spec.md` — protocol, measurement axes, scoring procedure, pre-registered predictions
- `explanation.md` — this file
- `scripts/hle_per_question.py` — headless parallel runner, resumable
- `scripts/hle_score.py` — grader with REVIEW flagging

## Open questions before Kaggle submission

1. Do we ship one Arm (MetaCoach alone) or a comparator structure (Vanilla + MetaCoach)? Comparator is stronger scientifically but doubles compute.
2. How do we weight a benchmark where the "correct" result is that the intervention doesn't work? Judges may read "MetaCoach doesn't redirect" as failure of the benchmark rather than a valid finding about current models. Needs clear framing in the submission writeup.
3. Original task authoring: we need 20-30 borderline tasks, independently authored, not HLE-derived. Authoring is ~30-45 min/task for a hard probe. That's the main remaining work.

## Related

- `../hch/` — the companion HCH in-context benchmark, testing architectural metacog (decomposition + per-sub budget prediction) as the hypothesized fix for the redirect failure documented here.
