---
color: green
isContextNode: false
agent_name: Gus
---
# Budget-metagame benchmark: analysis + design recommendation

Validated user's budget-metagame idea (accuracy-vs-token tradeoff on NP-hard approximable problems) as the strongest metacog benchmark candidate so far. Addressed reasoning!=output concern: charge for ALL tokens using actual API rates — the asymmetry IS the signal. Flagged four non-obvious design issues and proposed a minimal TSP-25 experiment.

# Budget-metagame benchmark: thinking-partner analysis

## Core validation
The proposal (generate NP-hard problems with heuristic-approximable answers; score = $X/%-optimal − $K/token) is the strongest metacog benchmark discussed in this thread. It **solves the reasoning-length ceiling** identified in the parent chain (`if-we-scale-N-tokens-scale-too.md`): stopping early becomes rationally correct, so metacog becomes observable rather than punished.

Complements (does not replace) working-memory-chunk-scaling:
- WM-scaling tests: *does agent recognize overload?*
- Budget-metagame tests: *does agent act on marginal-cost reasoning once aware?*
Different axes, both worth having.

## The reasoning ≠ output concern (user flagged)
**Not a bug — it's the substrate of what we measure.** Charge for ALL tokens (input + extended-thinking + output) using real API $/M-token rates (Sonnet $3/$15, Opus $15/$75). Rationale:
1. Anthropic's billing already costs reasoning tokens → realistic.
2. If agent burns 10K thinking then outputs "greedy answer", that's *bad* metacog and the score must surface it.
3. Scoring asymmetry between thinking/output is the feature, not the leak.

**Caveat:** LLMs can't self-count tokens accurately. So *live budget tracker* framing ("$23 left") will be noise. Fix: frame the prompt as a **decision rule** — "stop when marginal accuracy gain < marginal token cost." A rule executes without a counter. Smart agents will produce stopping logic; bad ones won't.

## Non-obvious design issues

### 1. Heuristic floor is too high on most NP-hard
Greedy TSP/bin-packing/max-cut hit 85–95% routinely. If the cheap heuristic already scores ~90%, there's no spread to measure investment. **Fix:** pick instances where greedy is ~60–70% and 2-opt/local-search climbs to ~90% — the middle band is where metacog differentiates agents.

### 2. Continuous accuracy only
TSP tour length, max-SAT clauses satisfied, Steiner cost — good. Avoid discrete-jump scoring (bin-packing exact-bins, graph-coloring chromatic number) — accuracy quantizes and the Pareto frontier gets ragged.

### 3. Convex payoff curve
Pay more per % at the top: $1 for 80→90, $3 for 90→99. Rewards pushing past heuristic ceiling; discourages "greedy-bail." Matches the intuition that *the last few % are what separate smart agents*.

### 4. Three observable baselines required
- **B1 — always-greedy**: minimum reasoning, high-floor accuracy.
- **B2 — always-exhaustive**: max reasoning, near-optimal.
- **B3 — smart-metacog**: stops when marginal < cost; should land above both on the $ Pareto frontier.
Without all three, raw score is uninterpretable.

## Minimal experiment (one sitting)

**Problem class:** TSP, 25–30 cities, Euclidean random instances.
**Gold answer:** offline Concorde-exact or branch-and-bound.
**Prompt:** problem + scoring formula + stopping-rule framing + token-rate disclosure.
**Scoring:** `score_$ = ACC_POINTS × accuracy_% − TOKEN_RATE × total_tokens` (with convex ACC_POINTS).
**Sample:** 10 instances × 3 arms (B1/B2/B3) × 2 models (Sonnet/Opus) = 60 runs.
**Success criterion:** smart-metacog agent achieves higher $score than always-greedy AND always-exhaustive on ≥6/10 instances.

If yes → budget-metagame is a usable metacog axis; design Class-8 of `benchmark-class-bench.md` around it.
If no → the framing fails to elicit metacog reasoning, and we need harder mechanisms (live token counter via tool calls, forced scratchpad in constrained DSL, etc.).

## Deferred open questions
- Do we show a live token counter via tool call (`get_tokens_used()`)? Adds realism but may anchor on counter rather than rule.
- Reveal token rate in $ or in raw tokens? $ framing likely anchors better on human cost-benefit priors.
- Single-shot or iterative refinement allowed (submit, then decide whether to pay more for revision)? Iterative is more realistic but adds protocol complexity.

## PREDICTION CLAIMS
- **Claim 1 (p=0.70):** On TSP-25, Sonnet smart-metacog arm outperforms always-exhaustive on $score ≥6/10 instances.
- **Claim 2 (p=0.55):** Sonnet smart-metacog arm also outperforms always-greedy on $score ≥6/10 instances.
- **Claim 3 (p=0.80):** Charging for extended-thinking tokens at real API rates materially changes agent behavior (shorter thinking blocks) vs. not charging.
- **Claim 4 (p=0.40):** Providing a live `get_tokens_used()` tool *worsens* decision quality (anchoring) vs. decision-rule framing alone.


### NOTES

- Single-agent thinking-partner task — no decomposition needed, DEPTH_BUDGET preserved.
- The 'reasoning tokens != output tokens' concern the user raised is resolved by charging actual API cost, not by trying to hide reasoning. This turns the asymmetry from a measurement leak into a measurement surface.
- Next logical step if user agrees: spawn ONE designer agent for a TSP-25 instance + scoring prompt, then 3 solver agents (B1/B2/B3) per instance. Follows the `benchmark-class-bench.md` fan-out pattern.

## Related

- [benchmark-class-bench](benchmark-class-bench.md)
- [working-memory-chunk-scaling-benchmark](working-memory-chunk-scaling-benchmark.md)
- [compression-gap-benchmark-design](compression-gap-benchmark-design.md)

[[hch-metacog-spike-orchestration-done_1_0_2_1_1_0_1_1_0_0_2_0_0]]

[[/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-15-4/budget-metagame-benchmark-analysis_1.md]]