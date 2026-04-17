---
color: blue
isContextNode: false
agent_name: Amit
---
# Open questions + non-applicable fallbacks

VE + graphcol sub-components not traced end-to-end; judge-rescue is not the right layer for schema mismatches; a few validation steps remain before shipping fixes.

1. **VE sub-component behaviour.** Not sampled here — only portfolios containing CJS/MWIS/Steiner/TSP were traced. VE has its own schema nuances; confirm by auditing a portfolio row with a VE component. Scan: `grep '"class": "ve"' results/full/portfolio_*/question.json`.
2. **Graphcol sub-component in portfolios.** Generator audit suggests Graphcol has `baseline_submission` (Steiner-style), so seeding should work — but contract absence (Fix 4) may still bite. Not traced end-to-end here.
3. **Is the TSP sub_instance `problem_statement` field reliable across seeds?** seed5 TSP embedded a useful `problem_statement`; untested on portfolio-hard with the TSP hard generator (variables may differ).
4. **Does `answer_contract` already propagate through `build_questions.py` for non-CJS/Steiner classes?** The raw generator output may differ from what lands in `sub_instance` — re-check after Fix 4.
5. **Judge-rescue cannot recover MWIS key-mismatches.** Sonnet's seed14 run passed strict parse (`parse_path=strict_protocol_cf`) — rescue never triggered because BEST_GUESS parsed as valid JSON; the schema mismatch is downstream of parsing. Do NOT try to fix this in the rescue layer.

## Validation plan for shipping Fix 1+2+3

- Dry-run on `portfolio_medium_seed14` with the 3 models. Success criterion: all 3 models return `feasible=True` for all 3 sub-components (even if gaps are large). Expected: MWIS `selected_vertices` key used, TSP `tour` length matches N, Steiner `frequencies` present.
- Dry-run on `portfolio_medium_seed5` (TSP-bearing). Success: no 21-item tours, no string-name tours.
- Dry-run on `portfolio_hard_seed25` (the 1-of-36 success) to confirm no regression.

open questions [[portfolio-infeasibility-root]]
