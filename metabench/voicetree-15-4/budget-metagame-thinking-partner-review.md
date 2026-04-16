---
color: green
isContextNode: false
agent_name: Ivy
---
# Budget-metagame review: reframe as B1v2, not as a third benchmark

Reviewed Ivan's kaggle-budget-metagame-design.md against Gus's analysis and the existing judged writeup (85.5/100). Core recommendation: promote budget-metagame into a Benchmark 1 scoring upgrade — it structurally resolves all three judge-flagged weaknesses (n, messy A2 units, missing A3 counterfactuals) plus the calibrated-pessimism gaming. Flagged four concrete MVP concerns: TSP-25 is code-solvable by memory (coding-resistance unaddressed), thinking-token blindness is submission-level risk not just a caveat, B3 prompt leaks the metacog it tries to measure, and the 6-turn multi-turn scaffold likely won't fire on TSP.

# Thinking-partner review of Ivan's kaggle-budget-metagame-design.md

Task: user asked Ivy to read `kaggle-budget-metagame-design.md` and review the approach vs the existing writeup at `hch-metacog-spike-orchestration-done_1_0_2_0.md` (the judged submission draft, 85.5/100).

## Strategic reframe (highest-leverage point)

Neither Ivan's design doc nor Gus's earlier analysis positions budget-metagame against the existing submission. The judge gave the current writeup **one** highest-leverage improvement: scale B1 to n=200 + run Forced-Atomic/Forced-Decomposed counterfactuals. Ivan's B1/B2/B3 arm structure **is exactly those counterfactuals with an economic scoring layer on top**. Reframe budget-metagame as **"Benchmark 1 v2"** — same HCH Plan/Execute/Integrate protocol, but replace the A1+A2+A3 composite with `$score = convex(acc%) · A − tokens · K` — and a single move resolves all three judge weaknesses (sample size, messy A2 units mixing Brier with MAPE, missing A3 counterfactuals) and the calibrated-pessimism gaming.

Positioning this as a third benchmark dilutes; positioning as a B1 upgrade strengthens.

## Four concrete concerns with Ivan's TSP-25 MVP

### 1. TSP-25 is code-solvable by memory
Ivan's design has no coding-resistance. `four-budget-benchmark-proposals.md` already flagged this: "clean-decomposition problems (TSP, coloring) tempt agents to write solver code." In a `llm.prompt` setting with no execution, a frontier model mentally runs nearest-neighbour + 2-opt and lands at ~95%. You'd measure arithmetic accuracy, not metacog. Options:
- (a) Natural-language-wrap the instance (Specification Gap idea from the mindmap) to force interpretation before solving.
- (b) Switch to a coding-resistant class (compression-gap, infeasibility proofs) that Gus's analysis recommended.
- (c) Accept TSP only as a baseline calibration instrument, not the main signal.

### 2. Thinking-token blindness is a submission risk, not just a caveat
Ivan's Claim 3 (p=0.85) says bias is material. If Sonnet-with-thinking wins $-score because 20K hidden thinking tokens aren't billed, a Kaggle judge *will* catch it — and the existing submission already has one gaming concern (calibrated-pessimism via Haiku). Compounding is dangerous. Honest MVP framing: restrict to non-thinking models and **sell it as a feature**: "we measure the agentic regime where every reasoning token is billable and observable."

### 3. B3 prompt leaks the metacog it tries to measure
Ivan's B3 arm: "you pay $K per token and $A per %-optimal. Stop when marginal < cost. Declare your expected gap% first." That's not measuring emergent metacog — it's teaching it. Good science: **hand the same full scoring info (rates + convex payoff) to all three arms**, only vary the *instruction on what to do with it*. Otherwise B3 wins trivially because it was told to, and Claim 2 generalizes to nothing.

### 4. Multi-turn scaffold likely won't fire on TSP
For TSP-25, models dump full answers in turn 1. The 6-turn `while turns < 6` loop copied from `metacog_format_recall_v1` was designed for interleaved-fillers recall, not one-shot optimization. Expect most instances to terminate in turn 1 with the multi-turn machinery as dead code. Either simplify to single-turn, or pick a problem class where iterative refinement is natural (online adversarial job-shop with reveal schedule, budget-constrained multi-step planning).

## Concrete recommendation (what I'd actually do next)

**Fold budget-metagame into a Benchmark 1 v2 design doc:**
1. Keep HCH Plan/Execute/Integrate protocol (judge praised it).
2. Run every instance on **three arms**: forced-atomic / forced-decomposed / free-choice-with-cost-rule. These arms *are* Ivan's B1/B2/B3 AND the judge's requested counterfactuals.
3. Primary metric: `$score = convex(acc%) · A − tokens · K` (Ivan's idea).
4. Secondary metric: Brier on P_CORRECT (keep for calibration axis, drop composite).
5. Problem class: **not TSP** — pick one coding-resistant class from Gus's list (compression-gap or NL-wrapped scheduling).
6. Hard-exclude thinking models for MVP; frame as scope choice.
7. n ≥ 150 (judge's minimum for stat power).

## Open questions for the user

1. **Positioning**: third benchmark, replacement for B1, or upgrade-in-place to B1? (*My vote: upgrade-in-place — directly answers judge's highest-leverage improvement.*)
2. **Problem class**: TSP (code-solvable risk) or coding-resistant class? (*My vote: coding-resistant.*)
3. **Thinking models**: hard-exclude for MVP or include with caveat? (*My vote: hard-exclude + sell as feature.*)
4. **"Budget-metagame" scope**: is it the *scoring function* ($/acc tradeoff), the *protocol* (3 arms), or the *problem class* (NP-hard approximable)? Clarifying prevents Ivan's MVP from doing one well and the other two by accident.

## PREDICTION CLAIMS

- **Claim 1 (p=0.80):** If TSP-25 is used as-is with a frontier model via `llm.prompt`, greedy and exhaustive arm accuracy will be within 5pp of each other — no Pareto spread to measure metacog.
- **Claim 2 (p=0.70):** Reframing budget-metagame as B1 v2 (same protocol, new scoring + counterfactual arms) raises the judge score more than adding a third benchmark would.
- **Claim 3 (p=0.75):** If B3 prompt is stripped of its stopping-rule coaching and given the same framing as B1/B2 plus only the $/accuracy rates, at least one model family will *still* underperform greedy — that would be a cleaner metacog signal than Ivan's current design would produce.
- **Claim 4 (p=0.60):** The thinking-token blindness gap will be called out by at least one reviewer if not pre-emptively framed; silent caveat is insufficient.

## Related

- [kaggle-budget-metagame-design](kaggle-budget-metagame-design.md) — Ivan's concrete kbench mechanics
- [budget-metagame-benchmark-analysis](budget-metagame-benchmark-analysis.md) — Gus's core analysis + 4 design issues
- [four-budget-benchmark-proposals](four-budget-benchmark-proposals.md) — coding-resistance tradeoff
- [hch-metacog-spike-orchestration-done_1_0_2_0](hch-metacog-spike-orchestration-done_1_0_2_0.md) — existing writeup + judge score 85.5/100
- [kaggle-metrics-support-verified](kaggle-metrics-support-verified.md) — thinking_tokens gap evidence

### NOTES

- Single-agent thinking-partner task — no decomposition, DEPTH_BUDGET preserved.
- The key insight Ivan missed: his B1/B2/B3 arm structure is a direct answer to the judge's highest-leverage improvement ask (Forced-Atomic/Forced-Decomposed counterfactuals). Selling it as a third benchmark undersells it.
- Coding-resistance is still the unresolved crux across all three design docs — was raised in `four-budget-benchmark-proposals.md` and in the mindmap (Specification Gap idea) but no design has addressed it concretely.

## Related

- [kaggle-budget-metagame-design](kaggle-budget-metagame-design.md)
- [budget-metagame-benchmark-analysis](budget-metagame-benchmark-analysis.md)
- [four-budget-benchmark-proposals](four-budget-benchmark-proposals.md)
- [hch-metacog-spike-orchestration-done_1_0_2_0](hch-metacog-spike-orchestration-done_1_0_2_0.md)

[[budget-metagame-benchmark-analysis_1_0_0]]
