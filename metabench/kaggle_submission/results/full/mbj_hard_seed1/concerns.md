# Concerns for `mbj_hard_seed1`

## parse
- `gemini-flash-latest`: `strict_protocol_cf`; stop=`decision_stop`; 1 exec turn; wall=`396.1s`.
- `claude-sonnet-4.6`: `strict_protocol_cf`; stop=`decision_stop`; 1 exec turn; wall=`92.9s`.
- `gpt-5.4-mini`: `strict_protocol_cf`; stop=`decision_stop`; 1 exec turn; wall=`15.4s`.

## feasibility
- `gemini-flash-latest`: feasible=`False`; source=`cf_parsed`; verifier rejected the schedule with `precedence failed for J3: M4 starts at 25 before predecessor finished at 28`; gap_pct=`100.0%`.
- `claude-sonnet-4.6`: feasible=`True`; source=`cf_parsed`; verified_objective=`6560`; gap_pct=`2.18%`.
- `gpt-5.4-mini`: feasible=`True`; source=`cf_parsed`; verified_objective=`7700`; gap_pct=`19.94%`.

## score-vs-baseline
- `gemini-flash-latest`: score=`0.00`; hard MBJ collapsed on a precedence violation.
- `claude-sonnet-4.6`: strong improvement over baseline (`7700 -> 6560`); score=`96.89`.
- `gpt-5.4-mini`: feasible but baseline-level (`7700 -> 7700`); score=`79.91`.

## transcript coherence
- `gemini-flash-latest`: parse path stayed clean, but the actual schedule violated precedence.
- `claude-sonnet-4.6`: this is the best MBJ result in the sweep; hard MBJ elicited real search rather than baseline recovery.
- `gpt-5.4-mini`: coherent and fast, but still baseline echo on the hard seed.

## suggested fixes
- Keep `mbj_hard_seed1` in future smokes: it sharply separates Sonnet's optimization ability from GPT's baseline echo and Gemini's schedule-validity failures.
- Add a precedence checker or repair step to the MBJ prompt loop; Gemini's failure was not parsing but invalid schedule construction.
- If GPT is meant to show optimization headroom, this row is a good canary because it stays feasible while revealing no improvement.
