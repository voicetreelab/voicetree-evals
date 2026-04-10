---
color: green
isContextNode: false
agent_name: Aki
---
# ForecastBench Execution and Submission Plan

Synthesized the official-site audit and repository audit into a practical April 2026 plan. The result separates the public participant workflow, which is feasible from public docs, from the internal maintainer pipeline, which depends on private GCP configuration and is not fully runnable from this workspace.

As of 2026-04-08, there are two distinct ways to "run ForecastBench":

1. External participant workflow (publicly runnable enough to submit)
- Email `forecastbench@forecastingresearch.org` with the uploader email addresses you want authorized.
- Wait for ForecastBench to reply with your GCP upload folder and the next forecast due date.
- On the due date at 00:00 UTC, download `latest-llm.json` from `forecastbench-datasets/datasets/question_sets/`. Public docs say publication can lag by up to 5 minutes.
- Generate one forecast JSON for that question set. Current live rounds use 500 questions total: 250 market + 250 dataset.
- Use the repo-consistent schema: top-level keys `organization`, `model_organization`, `model`, `question_set`, and `forecasts`; each forecast row needs `id`, `source`, `forecast`, `resolution_date`, and optional `reasoning`.
- Market questions get one forecast each. Dataset questions need one forecast per listed `resolution_date`.
- Cover at least 95% of market questions and 95% of dataset questions; missing forecasts are imputed to `0.5`.
- Upload the JSON to the assigned GCP folder by 23:59:59 UTC the same day. If bucket upload fails, the official fallback is emailing the file before the same deadline.
- Teams may submit up to 3 forecast sets per round.

2. Internal maintainer pipeline (not fully public)
- Clone `forecastingresearch/forecastbench` with submodules.
- Create `variables.mk` from `variables.example.mk`.
- Run `make setup-python-env`.
- The operational flow is `make questions`, `make metadata`, `make curate-questions`, `make baselines`, `make resolve`, `make leaderboards`, and optionally `make website`.
- This path is blocked publicly by missing bucket names, service accounts, Secret Manager values, and internal handoff details.

Concrete next-step plan for this workspace
- Clone the real repo into a separate local directory; this folder is only a Voicetree planning workspace.
- Build a small local generator/validator around the published question-set JSON rather than trying to run ForecastBench's full private GCP pipeline.
- Dry-run against the current public `latest-llm.json` target, which pointed to `2026-03-29-llm.json` on 2026-04-08.
- After ForecastBench grants an upload folder, submit that validated JSON through the participant workflow above.

Learnings
- Tried treating the public repo as a turnkey local benchmark runner, then switched to a two-track model because the repo is mostly maintainer infrastructure while the real public submission flow lives in the wiki.
- The main pitfall is relying on older paper-era docs. Current rounds use 500 questions, unresolved market questions are not scored immediately, and leaderboard inclusion is delayed by 50 days.
- The durable mental model is: public participants only need the released question set plus the upload contract; maintainers run a larger private GCP pipeline behind that public interface.

## Related

- [forecastbench-1a-official-sources-audit-apr-2026](forecastbench-1a-official-sources-audit-apr-2026.md)
- [forecastbench-1b-repository-audit-findings](forecastbench-1b-repository-audit-findings.md)
- [forecastbench-1b-phase-2](forecastbench-1b-phase-2.md)

[[1775618897236Woz]]
