---
color: green
isContextNode: false
agent_name: Ivan
---
# ForecastBench Tool And Source Policy

Mapped the tool budget and source-specific tactics onto the tiered workflow so the expensive research paths stay focused on the most valuable questions.

Tool policy by tier:
- Full-workflow bucket uses the full packet: provided question metadata, source-specific structured data, official / authoritative sources, EXA or broad web search, related market context, and X / social signals when the question is event-driven.
- Baseline bucket gets zero bespoke research after the baseline pass.

Source-specific fast path:
- `acled`: baseline time-series forecast plus news / escalation checks for the relevant country and event type.
- `dbnomics` / `fred` / `yfinance`: baseline time-series forecast unless a known scheduled catalyst exists within 30 days.
- `wikipedia`: baseline structural forecast plus official schedule / incumbent / record-holder checks.
- Market questions: baseline only; use current market probability when available, otherwise `0.5`.

Adaptation from the root probability skill:
- Reuse the orchestration pattern and Phase 2 LR-budgeting logic.
- Do not reuse the generic-question path as-is because downstream workers still expect a parsed-contract style intake.
- Replace Polymarket-specific parsing with a ForecastBench intake packet and question-level grouping before any fan-out.
- Skip the direct-estimation shortcut for the targeted first-month preliminary bucket; those questions always get the full workflow.
- Keep `HUMAN_REVIEW = no` on benchmark day.

Practical consequence:
- The existing `scratch/gameplan.md` remains the operational shell runbook.
- This policy fills in the forecasting black box with a baseline-first, first-month-preliminary-overwrite algorithm instead of trying to fully bespoke every row.

details [[forecastbench-workflow-synthesis]]
