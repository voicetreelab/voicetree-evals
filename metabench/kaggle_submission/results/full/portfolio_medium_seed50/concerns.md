# Concerns for `portfolio_medium_seed50`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`; 4 exec turns; wall=`1099.9s`.
- `claude-sonnet-4.6`: `strict_parse_failed`; stop=`error`; 3 attempts all failed on exec-turn parsing; final error=`exec turn 2 parse failed`.
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`; 1 exec turn; wall=`12.6s`.

## feasibility
- `gemini-flash-latest`: feasible=`True`; source=`cf_parsed`; component gaps: `tsp=0.88%`, `graphcol=175.0%`, `ve=13.29%`.
- `claude-sonnet-4.6`: feasible=`False`; source=`parsed`; failure_reason=`portfolio submission must be an object`.
- `gpt-5.4-mini`: feasible=`True`; source=`cf_parsed`; component gaps: `tsp=25.11%`, `graphcol=400.0%`, `ve=46.90%`.

## score-vs-baseline
- `gemini-flash-latest`: score=`7.20`; technically feasible portfolio, but the gain came mostly from `tsp`/`ve` while `graphcol` remained very weak and the run consumed ~18 minutes.
- `claude-sonnet-4.6`: score=`0.57`; never produced a usable portfolio object despite 3 retries.
- `gpt-5.4-mini`: score=`42.14`; feasible safe-pool portfolio in one turn, but quality stayed close to baseline on all three components.

## transcript coherence
- `gemini-flash-latest`: coherent but very long; multiple exec turns were needed before it converged on a feasible portfolio object.
- `claude-sonnet-4.6`: unstable at the schema layer; one attempt returned a non-object portfolio payload and another produced partial output without a usable `BEST_GUESS`.
- `gpt-5.4-mini`: coherent and concise; this row shows that safe-pool portfolio is no longer an automatic feasibility collapse.

## suggested fixes
- Keep using safe-pool portfolio sampling: removing the MWIS generation blocker did help GPT and Gemini reach feasible portfolio submissions.
- Portfolio prompt/schema handling is still brittle for `claude-sonnet-4.6`; the top-level object contract needs stronger enforcement and probably a tighter in-context example.
- If portfolio quality matters, add more guidance for `graphcol`: both feasible models left the largest headroom there.
