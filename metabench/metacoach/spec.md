# MetaCoach — benchmark spec

**Version:** 0.1 (pre-Kaggle)
**Track:** Metacognition
**License:** CC0

## What this measures

Whether wrapping a language model in a structured metacognitive reflection protocol changes (a) its accuracy on hard questions, (b) its calibration, or (c) its failure modes — compared to a plain "just solve it" control arm.

Specifically: does meta-reflection make the model **redirect** its answers, or only **modulate** its confidence?

## Protocol

For each question in a task set, run two fresh agent sessions (one per arm), fully isolated from each other and from any other question.

### Arm 1 — Vanilla (control)

Prompt:
```
Solve the following question directly. Show whatever reasoning you need,
then emit your final answer.

Question type: {multipleChoice | exactMatch}
Subject: {domain label}

QUESTION:
{question_text}

OUTPUT FORMAT — strict. Your response must END with exactly two lines:
ANSWER: <your answer>
P_CORRECT: <float in [0,1]>

If the question is multipleChoice, ANSWER is a single capital letter.
If the question is exactMatch, ANSWER is the literal numeric/symbolic/phrase answer (no letter).
```

### Arm 2 — MetaCoach

Same as Vanilla, plus a pre-prompt instruction inserted before the question:

```
Address the following metacognitive reflection prompt at BOTH the start
and the end of this task:

"Go through at least 2-3 levels on your reasoning towards the task/prompt
you are assigned. At each level, reflect on the cognitive patterns of the
level below — not the content, the thinking, the cognitive patterns. For
example in level 1, identify what cognitive pattern you are using to solve
this problem. In level 2, identify what meta-pattern you used to notice &
identify that, biases/uncertainties, etc. Finally, after going to 2-3
meta-levels recursively, circle back to the task — has this reflection
actually improved my confidence in how to solve this problem & whether
it is correct? Provide a prediction probability claim for that question."

Do this reflection BEFORE attempting the question, then solve the question,
then do the reflection AGAIN after your candidate answer, and let your final
P_CORRECT incorporate both passes.
```

### Isolation contract (critical)

- **One fresh session per (question, arm)**. No context sharing across questions within an arm.
- **No access to other questions' prompts or answers.** The agent cannot amortize reasoning across questions.
- **Answer keys never visible to the agent or to the agent's filesystem.** Enforced by keeping keys encrypted or on a separate host until scoring time.

Prior work (Sonnet, HLE Q41-100, batch architecture) showed that a single agent handling 60 questions in one session produced "format-inversion" failures at final synthesis — the agent knew the answer internally but emitted the wrong format after context saturation. Per-question isolation eliminates this class of failure.

## Measurement axes

| Axis | Metric | What it isolates |
|------|--------|------------------|
| 1. Accuracy | correct / total | Raw task ability |
| 2. Calibration | Brier score on P_CORRECT vs binary correctness | Confidence quality |
| 3. Answer-redirection rate | % of questions where MetaCoach's final answer differs from Vanilla's | Does reflection change the answer, or only confidence? |
| 4. Correct-redirection rate | among redirected answers, % where MetaCoach's new answer is correct and Vanilla's was wrong | Is redirection actually useful? |
| 5. Failure-mode inventory | qualitative — coded per wrong answer | Which cognitive patterns fail; how metacog interacts with each |

Axis 3 is the load-bearing novelty. Prior metacog benchmarks report (1) and (2); the redirect-vs-modulate distinction is what separates "reflection theater" from functional metacognition.

## Task authoring requirements

For Kaggle submission (and for general validity), tasks must satisfy:

1. **Borderline difficulty.** Pilot data should show Vanilla answering correctly ≥20% and ≤80% of the time. Too easy → no room for redirection; too hard → both arms collapse to noise.
2. **Auto-gradable.** Numeric, short-string, or multiple-choice answer. No free-form essays.
3. **Ambiguity-containing.** A significant fraction of tasks should admit multiple plausible readings where only one is correct — so axis 3 has something to measure.
4. **Computation-requiring.** At least half the tasks should require non-trivial computation, not retrieval of a known fact. Retrieval questions are dominated by model knowledge; metacog has no value-add.
5. **Original-authored.** No derived-from-public-benchmark text. Tasks may mirror the *shape* of existing benchmark items but must be independently authored.

Recommended task count for Kaggle submission: **20-30 tasks.** Enough for Brier and redirection-rate to be stable, small enough to fit the compute budget (~$10-15 at Sonnet rates for both arms).

## Scoring procedure

1. Run Arm 1 and Arm 2 on all tasks. Append one JSONL row per (qnum, arm) with: `qnum`, `qid`, `arm`, `answer`, `p_correct`, `reasoning`, `duration_s`, `returncode`, `stdout`.
2. Grade each row against the held-out answer key. MCQ: letter match. exactMatch: normalized-string equality with numeric-equivalence fallback.
3. Compute accuracy and Brier per arm.
4. Compute answer-redirection rate: `|{q : metacog_answer(q) != vanilla_answer(q)}| / n`.
5. Compute correct-redirection rate: `|{q : metacog_correct(q) AND NOT vanilla_correct(q)}| / |{q : metacog_answer(q) != vanilla_answer(q)}|`.
6. For each wrong answer in Arm 2, code the failure mode (computation error, format error, knowledge gap, ambiguity misresolution, other).

## Output format

Submission includes:
- `tasks.json` — authored task set (questions, types, subjects)
- `answers.json` — answer key (encrypted or held separately during run)
- `vanilla_results.jsonl` — Arm 1 outputs
- `metacoach_results.jsonl` — Arm 2 outputs
- `summary.json` — computed axis values
- `failure_modes.csv` — coded failure modes per wrong answer

## Pre-registered predictions (from HLE pilot, n=60)

- MetaCoach redirection rate: ~30% of answers differ from Vanilla
- Correct-redirection rate: ~15% — most redirections are from right to wrong or wrong to differently-wrong, not wrong to right
- MetaCoach Brier improvement vs Vanilla: marginal (≤0.05) on clean per-question isolation

If these hold on an original task set, the headline is: **metacog-as-prompt-wrapper is a confidence modulator, not an answer redirector.** That is itself a useful negative result, and it implies the path to useful metacog is *architectural* (decomposition, fresh-session sub-agents, adversarial verification) rather than *prompt-level* (reflection scaffolds).

## Scripts

- `scripts/hle_per_question.py` — runner. Headless `claude -p` per (question, arm), parallel, resumable via JSONL.
- `scripts/hle_score.py` — grader. Produces accuracy + Brier per arm + REVIEW-flagged ambiguous rows for human audit.

Both scripts were developed against HLE Q41-100. To use with an authored task set, replace the dataset path constant at the top of `hle_per_question.py` and provide a matching `answer_key.json` for the scorer.

## Known limitations

- Single-model (Sonnet) pilot data. Cross-model replication (Haiku, Opus, GPT, Gemini) recommended before publication claims.
- P_CORRECT in the vanilla prompt is itself a reflective probe. A stricter no-metacog control would strip it and forgo calibration measurement.
- Axis 5 (failure-mode coding) is currently manual. For scale, a second-pass grader agent could auto-code with a fixed taxonomy.
