---
color: green
isContextNode: false
agent_name: Ama
---
# Official Sources Audit: ForecastBench Current Benchmark Facts

Audited forecastbench.org, the linked ForecastBench wiki, and the datasets repo to extract the current benchmark structure, submission workflow, and post-paper changes. Identified that the live submission docs and changelog supersede some older paper-era details, especially question-count and leaderboard rules.

## Sources consulted
- https://www.forecastbench.org/
- https://forecastbench.org/about/
- https://www.forecastbench.org/leaderboards/
- https://www.forecastbench.org/docs/
- https://www.forecastbench.org/datasets/
- https://github.com/forecastingresearch/forecastbench/wiki/How-to-submit-to-ForecastBench
- https://github.com/forecastingresearch/forecastbench/wiki/Changelog
- https://github.com/forecastingresearch/forecastbench/wiki/How-does-ForecastBench-work%3F
- https://github.com/forecastingresearch/forecastbench
- https://github.com/forecastingresearch/forecastbench-datasets/tree/main/datasets/question_sets

## Current fact base
- ForecastBench describes itself as a dynamic, contamination-free benchmark of LLM forecasting accuracy with human comparison groups.
- The benchmark currently uses two question families: dataset questions generated from real-world time series and market questions drawn from prediction platforms.
- The public About page says new forecasting rounds occur every two weeks and each round now generates 500 questions split evenly between market and dataset questions.
- Leaderboards are updated nightly, and the datasets page says leaderboards, resolution values, and released question sets are stored in the public `forecastbench-datasets` repository.
- The tournament leaderboard is the public-submission track; teams may use tools, context, fine-tuning, ensembling, etc. The baseline leaderboard is ForecastBench-run only and measures out-of-the-box performance.
- Public participation is open. The operational submission instructions live in the ForecastBench wiki page "How to submit to ForecastBench," edited Jan 9, 2026.
- Current submission flow: email `forecastbench@forecastingresearch.org` with uploader email addresses; ForecastBench replies with a GCP Cloud Storage upload folder and the next forecast due date. Anonymous submission is supported.
- On the forecast due date at 00:00 UTC, participants download the latest `YYYY-MM-DD-llm.json` question set from `forecastbench-datasets/datasets/question_sets`; the docs warn publication may lag by up to 5 minutes.
- Participants then have until 23:59:59 UTC on that same due date to upload a forecast-set JSON to their assigned GCP bucket. If bucket upload fails, the wiki allows emailing the forecast file before the same deadline.
- To appear on the leaderboard, a model must forecast at least 95% of market questions and at least 95% of dataset questions; missing forecasts are imputed to 0.5.
- Current question-set shape for submissions is 500 questions total: 250 market and 250 dataset.
- Market questions require 1 forecast each. Dataset questions require one forecast per listed resolution date, typically up to 8 horizons.
- The current rules no longer score unresolved market questions; market performance updates once those questions resolve.
- Teams may submit at most 3 forecast sets per round.
- Leaderboard inclusion is delayed by 50 days after forecast submission for stability. The changelog later adds a minimum of 50 resolved market questions per round for models to be included on the leaderboard.
- As of 2026-04-08, the public `latest-llm.json` symlink in the datasets repo points to `2026-03-29-llm.json`. Inference: under the documented biweekly cadence, the next nominal due date would be 2026-04-12.

## Divergences and freshness notes
- The docs landing page says the latest paper was updated 2025-02-28 and labels the changelog as "Last updated: 6 Oct 2025," but the linked changelog page itself was edited 2026-03-05 and contains newer benchmark-rule changes.
- The architecture wiki page still describes 1,000-question LLM rounds and combination-question handling. The newer submission wiki and changelog supersede that: combination questions were removed starting 2025-10-26 and current submission rounds use 500-question LLM sets.
- The public About page already reflects the newer 500-question setup, so the highest-confidence current view is: About/Leaderboards for public framing, Submit wiki for mechanics, Changelog for post-paper rule changes.

## Learnings
- Tried the high-level website first, then switched to the linked GitHub wiki because the site points there for authoritative submission mechanics and the landing docs lag the live changelog.
- Main pitfall: older paper-era docs still mention 1,000-question rounds and combination questions. Current live submissions use 500-question sets without combo questions for rounds starting 2025-10-26.
- The reliable mental model is split across three official surfaces: website pages for benchmark framing, wiki pages for operational details, and the datasets repo for current release cadence evidence.

### NOTES

- No workspace files were modified; this node captures the research output for Phase 1A.
- Key risk for follow-on planning: do not rely on the paper or older architecture wiki alone when implementing the live submission pipeline.

[[forecastbench-1a-official-sources]]
