---
color: green
isContextNode: false
agent_name: Xan
---
# Round 2 Worker 6 Runner — 4 Portfolio-Hard IDs × 3 Models

Evaluated `portfolio_hard_seed24`, `portfolio_hard_seed25`, `portfolio_hard_seed27`, and `portfolio_hard_seed28` across Gemini Flash, Claude Sonnet 4.6, and GPT-5.4 Mini.
Only 1/12 runs produced a fully feasible portfolio (`portfolio_hard_seed25` on Sonnet), but its component gaps remained poor; Gemini was slowest and produced both `partial_rescue` and `strict_parse_failed` outcomes.

## Model Summary

| model | runs | fully feasible | avg wall_s | parse mix |
|---|---:|---:|---:|---|
| `gemini-flash-latest` | 4 | 0 | 288.8 | `strict_protocol_cf`×2, `partial_rescue`×1, `strict_parse_failed`×1 |
| `claude-sonnet-4.6` | 4 | 1 | 53.5 | `strict_protocol_cf`×4 |
| `gpt-5.4-mini` | 4 | 0 | 14.0 | `strict_protocol_cf`×4 |

## Per-Row Headlines

- `portfolio_hard_seed24`: all 3 models were infeasible; Sonnet had the highest score (`18.18`) but only 1/3 components was feasible.
- `portfolio_hard_seed25`: Sonnet produced the only fully feasible portfolio of the run, but the component gaps were still poor (`185.57`, `123.71`, `80.39`), so feasibility did not mean quality.
- `portfolio_hard_seed27`: all 3 models were infeasible; Gemini and Sonnet both completed strict parses but still failed portfolio validity.
- `portfolio_hard_seed28`: Gemini ended in `strict_parse_failed` with no recovered `BEST_GUESS`; Sonnet reached the best score of the run (`24.53`) but still only solved 2/3 components feasibly.

## Learnings

- Tried to preserve the original 4-probe intent by selecting one ID per chunk, then switched to evaluating all 4 generated rows because only two chunks produced any rows at all. That kept the run at the intended 12 model executions without pretending the missing chunks existed.
- The easy mistake is reading positive portfolio scores as success. That is wrong here: almost every run remained infeasible, and even the sole feasible Sonnet run on seed 25 still had very poor objective gaps.
- A successor should believe the harness is behaving correctly on these rows. The failure mode is still portfolio solving quality, not packaging: every evaluated row produced the expected `question.json`, per-model payloads, and `concerns.md`, and the parse-path variation mostly tracks model behavior rather than file/schema problems.

## Files Changed

- kaggle_submission/scratch/round2/worker6/run_partial_eval.py
- kaggle_submission/scratch/round2/worker6/runner-log.md
- kaggle_submission/results/full/portfolio_hard_seed24/question.json
- kaggle_submission/results/full/portfolio_hard_seed24/gemini-flash-latest.json
- kaggle_submission/results/full/portfolio_hard_seed24/claude-sonnet-4.6.json
- kaggle_submission/results/full/portfolio_hard_seed24/gpt-5.4-mini.json
- kaggle_submission/results/full/portfolio_hard_seed24/concerns.md
- kaggle_submission/results/full/portfolio_hard_seed25/question.json
- kaggle_submission/results/full/portfolio_hard_seed25/gemini-flash-latest.json
- kaggle_submission/results/full/portfolio_hard_seed25/claude-sonnet-4.6.json
- kaggle_submission/results/full/portfolio_hard_seed25/gpt-5.4-mini.json
- kaggle_submission/results/full/portfolio_hard_seed25/concerns.md
- kaggle_submission/results/full/portfolio_hard_seed27/question.json
- kaggle_submission/results/full/portfolio_hard_seed27/gemini-flash-latest.json
- kaggle_submission/results/full/portfolio_hard_seed27/claude-sonnet-4.6.json
- kaggle_submission/results/full/portfolio_hard_seed27/gpt-5.4-mini.json
- kaggle_submission/results/full/portfolio_hard_seed27/concerns.md
- kaggle_submission/results/full/portfolio_hard_seed28/question.json
- kaggle_submission/results/full/portfolio_hard_seed28/gemini-flash-latest.json
- kaggle_submission/results/full/portfolio_hard_seed28/claude-sonnet-4.6.json
- kaggle_submission/results/full/portfolio_hard_seed28/gpt-5.4-mini.json
- kaggle_submission/results/full/portfolio_hard_seed28/concerns.md

### NOTES

- Gemini was by far the slowest path: 494.6s on `portfolio_hard_seed24` and 290.3s on `portfolio_hard_seed28`.
- `portfolio_hard_seed25` on Gemini hit `partial_rescue` and then exited with missing control fields; `portfolio_hard_seed28` on Gemini hit `strict_parse_failed`.
- GPT was operationally stable and fastest, but it never produced a fully feasible portfolio on this worker's sample.

evaluates [[round2-worker6-done]]
