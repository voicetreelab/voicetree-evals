# Round 1 Worker 6 Runner Done

- Question source: `/Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/scratch/round1/worker6/questions.partial.jsonl`
- Questions: portfolio_medium_seed2, portfolio_medium_seed5, portfolio_medium_seed8, portfolio_medium_seed11
- Models: gemini-flash-latest, claude-sonnet-4.6, gpt-5.4-mini
- Artifacts: `/Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/results/full`
- Recovery mode: Gemini rerun used outer timeout `240s` per attempt.

## Parse Rates

| model | parse_success | feasible | failures | notes |
|---|---:|---:|---:|---|
| `gemini-flash-latest` | 3/4 | 0/4 | 1 | runner_error=1, strict_protocol_cf=3 |
| `claude-sonnet-4.6` | 4/4 | 0/4 | 0 | strict_protocol_cf=4 |
| `gpt-5.4-mini` | 4/4 | 0/4 | 0 | strict_protocol_cf=4 |

## Question Headlines

- `portfolio_medium_seed2`: `gemini-flash-latest` parse=strict_protocol_cf score=-8.137342787499074 feasible=False; `claude-sonnet-4.6` parse=strict_protocol_cf score=24.47608921012602 feasible=False; `gpt-5.4-mini` parse=strict_protocol_cf score=-0.8710435979417526 feasible=False
- `portfolio_medium_seed5`: `gemini-flash-latest` parse=strict_protocol_cf score=5.798483044876928 feasible=False; `claude-sonnet-4.6` parse=strict_protocol_cf score=23.15700085140034 feasible=False; `gpt-5.4-mini` parse=strict_protocol_cf score=25.356836218097857 feasible=False
- `portfolio_medium_seed8`: `gemini-flash-latest` parse=runner_error score=0.0 feasible=False; `claude-sonnet-4.6` parse=strict_protocol_cf score=24.026728114972272 feasible=False; `gpt-5.4-mini` parse=strict_protocol_cf score=25.083117571226236 feasible=False
- `portfolio_medium_seed11`: `gemini-flash-latest` parse=strict_protocol_cf score=-9.4541372642869 feasible=False; `claude-sonnet-4.6` parse=strict_protocol_cf score=24.78922595742578 feasible=False; `gpt-5.4-mini` parse=strict_protocol_cf score=26.142143461573408 feasible=False

## Notes

- `concerns.md` was written for each question directory even when runs produced partial or timeout/error results.
- Existing Sonnet and GPT artifacts were preserved; only missing Gemini rows were rerun in recovery mode.
