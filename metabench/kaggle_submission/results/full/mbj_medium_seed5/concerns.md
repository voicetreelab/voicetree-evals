# Concerns for `mbj_medium_seed5`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`; 1 exec turn; wall=`362.0s`.
- `claude-sonnet-4.6`: `baseline_only`; stop=`wall_budget`; 3 attempts all hit `exec turn 2 timed out after 300s`.
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`; 1 exec turn; wall=`15.3s`.

## feasibility
- `gemini-flash-latest`: feasible=`False`; source=`cf_parsed`; verifier rejected the schedule with `duration mismatch for J8 on M7: expected 36, got 24`; gap_pct=`100.0%`.
- `claude-sonnet-4.6`: feasible=`True`; source=`baseline`; verified_objective=`7440`; gap_pct=`24.0%`.
- `gpt-5.4-mini`: feasible=`True`; source=`cf_parsed`; verified_objective=`7440`; gap_pct=`24.0%`.

## score-vs-baseline
- `gemini-flash-latest`: score=`0.00`; parse succeeded but the emitted MBJ schedule failed basic duration consistency.
- `claude-sonnet-4.6`: recovered only baseline after retries; score=`72.90`.
- `gpt-5.4-mini`: also stayed at baseline; score=`75.85`.

## transcript coherence
- `gemini-flash-latest`: structurally coherent output, but schedule correctness broke on a machine-duration invariant.
- `claude-sonnet-4.6`: same timeout pattern as `mbj_medium_seed1`; medium MBJ remains unstable locally.
- `gpt-5.4-mini`: coherent and fast, but again defaulted to baseline echo.

## suggested fixes
- Add an MBJ self-check before emitting `decision_stop`: duration mismatches should be catchable without the external verifier.
- Treat `mbj_medium_seed5` as a harder discriminator than seed 1; it separates Gemini's schedule-validity issue from GPT/Sonnet baseline fallback.
- Sonnet likely needs the same output-budget / shorter-turn intervention as on `mbj_medium_seed1`; retries alone are not fixing medium MBJ.
