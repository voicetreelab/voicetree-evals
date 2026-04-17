# Concerns for `mbj_medium_seed1`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`; 1 exec turn; wall=`402.0s`.
- `claude-sonnet-4.6`: `baseline_only`; stop=`wall_budget`; 3 attempts all hit `exec turn 2 timed out after 300s`.
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`; 1 exec turn; wall=`16.8s`.

## feasibility
- `gemini-flash-latest`: feasible=`True`; source=`cf_parsed`; verified_objective=`6000`; gap_pct=`5.26%`.
- `claude-sonnet-4.6`: feasible=`True`; source=`baseline`; verified_objective=`7167`; gap_pct=`25.74%`.
- `gpt-5.4-mini`: feasible=`True`; source=`cf_parsed`; verified_objective=`7167`; gap_pct=`25.74%`.

## score-vs-baseline
- `gemini-flash-latest`: real improvement over baseline (`7167 -> 6000`); score=`90.72`.
- `claude-sonnet-4.6`: recovered only the baseline schedule (`7167 -> 7167`); score=`71.20`.
- `gpt-5.4-mini`: also stayed at the baseline schedule (`7167 -> 7167`); score=`74.10`.

## transcript coherence
- `gemini-flash-latest`: coherent plan/exec/CF flow, but very slow for a single-turn MBJ improvement.
- `claude-sonnet-4.6`: not stable enough to complete the first exec turn on medium MBJ; timeout behavior dominates.
- `gpt-5.4-mini`: concise and structurally clean, but the run still defaulted to baseline echo.

## suggested fixes
- Keep this row in the representative set: it discriminates `gemini-flash-latest` from the baseline-echo pattern shown by GPT and timeout-limited Sonnet.
- Tighten MBJ exec formatting for `claude-sonnet-4.6` or cap verbosity earlier; 3 retries on the same 300s timeout did not recover a usable improved schedule.
- If the goal is optimization signal rather than mere feasibility, add a guardrail against MBJ baseline echo before accepting `decision_stop`.
