---
color: green
isContextNode: false
agent_name: Max
---
# Cofounder summary: metagame experiment pivot after TSP

Prepared a concise cofounder-facing summary of the experiment trajectory, why TSP was rejected, what problem family now looks best, and what the current implementation split is between Meg's simpler flowshop spike and the new harder coupled job-shop branch.

## Sendable summary draft
We started from the HCH-style metacognition idea rather than from a fixed problem class. The target signal was: can a model predict whether decomposition will help, estimate subtask difficulty/effort, verify intermediate work, and stop when more compute is no longer worth it?

Our first concrete local benchmark was a multi-turn budget-metagame on TSP-25 via the Gemini API. The harness itself worked: planning-only turn 1, iterative exec turns, declared-gap calibration, live stats injection, hard per-turn timeouts, and economic scoring. We ran the full 3-model x 3-arm x 3-seed sweep successfully.

The main result was that TSP looks like the wrong problem class, not just an underscaled instance. Gemini 3 was already near-ceiling across prompt arms, the time-budget field was basically ignored, multi-turn behavior was weak, and the dominant pattern looked more like 'recall and execute a known heuristic' than metacognitive self-modelling. So the wrapper idea survived, but TSP as the substrate did not.

The design conclusion is to pivot to natural-language coupled job-shop scheduling. This better matches the benchmark requirements because it has genuine upfront uncertainty, natural forced decomposition (Factory A -> release times -> Factory B), non-obvious globally optimal moves, exact offline gold via OR-Tools, and a real progressive-improvement story where extra reasoning can improve a baseline schedule.

We also simplified the protocol. The old `greedy/exhaustive/smart` arm split now looks like unnecessary benchmark complexity. The cleaner version is one canonical objective-optimizing prompt with a planning turn, a few execution turns, wall-clock budget pressure, and stop-decision scoring.

Current implementation status is intentionally split into two non-duplicating spikes. Meg is testing a simpler two-stage flowshop variant where the answer is just a job permutation; that is useful because it is easier to run and may already produce some signal. In parallel, I wrote a new spec for a harder branch (`hch/codex_metagame_v2`) that keeps the full coupled two-factory job-shop structure and requires the model to emit a full schedule that we can verify. The key question is whether the richer coupled structure gives meaningfully stronger metacognitive signal than the simpler flowshop, or whether it mostly adds parsing/output overhead.

If I had to summarize the current belief in one line: the core contribution is no longer 'TSP with a clever wrapper'; it is 'a budgeted metacognition protocol needs a problem family whose structure actually elicits uncertainty, decomposition, and stop-rationality, and coupled job-shop currently looks like the best fit.'

### NOTES

- The summary is tuned for a smart AI researcher: high signal, minimal background, and explicit distinction between harness validity and problem-class validity.
- At the time of writing, both Meg's simpler flowshop spike and the child Codex coupled-job-shop implementation are still running, so the implementation-status lines are intentionally provisional rather than final.

## Related

- [trajectory-post-tsp-synthesis](trajectory-post-tsp-synthesis.md)
- [recommended-problem-setup-post-tsp](recommended-problem-setup-post-tsp.md)
- [codex-metagame-v2-spec-and-handoff](codex-metagame-v2-spec-and-handoff.md)

[[task_1776319758322uan_1]]
