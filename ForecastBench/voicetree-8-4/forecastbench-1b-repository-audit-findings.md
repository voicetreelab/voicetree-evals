---
color: green
isContextNode: false
agent_name: Amit
---
# Repository Audit Findings

Completed the repository audit by combining the local-workspace blocker with a direct upstream GitHub audit. The resulting execution outline now distinguishes the public maintainer pipeline from the narrower public participant submission path and calls out the private GCP/secret dependencies that block a full local run.

Key findings:
- The local folder `/Users/lochlan/voicetree-evals/ForecastBench` is not a checkout of the ForecastBench source repository; it only contains Voicetree/Codex orchestration files.
- The real public implementation surface is the upstream GitHub repo, where the root `Makefile` orchestrates question ingestion, metadata tagging, question-set curation, baseline forecast generation, forecast resolution, leaderboard generation, and website publication.
- The public repo is primarily maintainers' infrastructure. It exposes forecast schemas and baseline generation code, but it does not expose the private `variables.mk` values, Secret Manager contents, bucket allocations, or the full handoff from participant upload folders into the internal scoring buckets.
- The updated node `/Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-1b-phase-2.md` now contains the ordered execution outline, file references, and unresolved gaps.

Learnings:
- Tried to audit the local workspace first, then switched to direct upstream GitHub inspection because the local folder never contained the benchmark source tree.
- The main pitfall is assuming ForecastBench is a normal public benchmark runner. The public repo mostly codifies ForecastBench's own GCP operations and baseline jobs, while live external submission is documented separately in the wiki.
- The durable mental model is: question bank refresh -> metadata -> question-set publish -> baseline forecast generation -> resolution -> processed forecast files -> leaderboard/site publication, with several steps gated by private cloud configuration.

## Files Changed

- /Users/lochlan/voicetree-evals/ForecastBench/voicetree-8-4/forecastbench-1b-phase-2.md

## Related

- [forecastbench-1a-official-sources-audit-apr-2026](forecastbench-1a-official-sources-audit-apr-2026.md)

[[forecastbench-1b-repository-audit]]
