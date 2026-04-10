---
color: green
isContextNode: false
agent_name: Ivan
---
# ForecastBench Clarification: Question Set Versus Question Bank

Clarified that Step 1's latest question set is the correct round input, but it is not sufficient by itself for the current Step 4 implementation because the source-aware dataset baseline also needs historical question-bank data.

Key clarification:
- Yes, Step 1 is the correct way to get the latest round input.
- The file fetched in Step 1 (`latest-llm.json` -> a concrete `YYYY-MM-DD-llm.json`) is the public question set for the round.
- We should absolutely use that file as the main round input.

Why that was not enough for the Step 4 test:
- The current Step 4 implementation intentionally uses the repo's source-aware cheap baseline forecaster for dataset rows.
- That forecaster does not run from the question-set JSON alone.
- It also needs the historical question-bank / resolution data for the dataset sources (`acled`, `dbnomics`, `fred`, `wikipedia`, `yfinance`).
- Market rows are easy from the question set because they can use `freeze_datetime_value`, but dataset rows need more than the round file.

Resulting mental model:
- Step 1 input = the round definition.
- Question bank data = supporting historical data needed by the current dataset baseline implementation.

Consequence:
- If we want to keep the requirement "dataset rows use the cheap source-aware baseline forecaster," then a real Step 4 run needs both the latest question set and the local question-bank data.
- If we want Step 4 to run from the question set alone, we would need to relax that requirement and use a simpler dataset baseline.

[[1775712512821qMj]]
