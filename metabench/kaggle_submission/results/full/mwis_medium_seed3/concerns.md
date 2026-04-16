# Concerns for mwis_medium_seed3

- class: `mwis`
- difficulty: `medium`
- baseline_gap_pct: `100.0`

## Parse
- `gemini-flash-latest`: parse_path=`strict_protocol`, parse_events=2, modes=['strict', 'cf_strict_parse_failed'], error=`counterfactual turn parse failed`
- `claude-sonnet-4.6`: parse_path=`baseline_only`, parse_events=0, modes=['-'], error=`RuntimeError: llm CLI timed out after 120s`
- `gpt-5.4-mini`: parse_path=`strict_protocol_cf`, parse_events=2, modes=['strict', 'cf_strict'], error=`-`

## Feasibility
- `gemini-flash-latest`: feasible=`True`, failure_reason=`counterfactual turn parse failed`
- `claude-sonnet-4.6`: feasible=`False`, failure_reason=`submission must be an object`
- `gpt-5.4-mini`: feasible=`False`, failure_reason=`claimed total_weight 381 does not match computed 377`

## Score vs Baseline
- `gemini-flash-latest`: score=86.78485100402135, gap_pct=10.88888888888889, baseline_gap_pct=100.0, improved_vs_baseline_gap=True, final_submission_source=`parsed`
- `claude-sonnet-4.6`: score=0.0, gap_pct=100.0, baseline_gap_pct=100.0, improved_vs_baseline_gap=False, final_submission_source=`baseline`
- `gpt-5.4-mini`: score=0.0, gap_pct=100.0, baseline_gap_pct=100.0, improved_vs_baseline_gap=False, final_submission_source=`cf_parsed`

## Transcript Coherence
- `gemini-flash-latest`: stop_reason=`decision_stop`, n_exec_turns=1, transcript_messages=3, wall_s=374.180419833865, retries=0
- `claude-sonnet-4.6`: stop_reason=`skipped_after_timeouts`, n_exec_turns=0, transcript_messages=1, wall_s=127.78376637492329, retries=2
- `gpt-5.4-mini`: stop_reason=`decision_stop`, n_exec_turns=1, transcript_messages=3, wall_s=12.018665791954845, retries=0

## Suggested Fixes
`claude-sonnet-4.6` needs prompt/protocol attention for `mwis_medium_seed3` because parse_path was `baseline_only`.
`claude-sonnet-4.6` produced an infeasible or missing final answer for `mwis_medium_seed3`; inspect verifier failure `submission must be an object`.
`claude-sonnet-4.6` did not beat the baseline gap on `mwis_medium_seed3`.
`claude-sonnet-4.6` ended with stop_reason `skipped_after_timeouts` on `mwis_medium_seed3`.
`gpt-5.4-mini` produced an infeasible or missing final answer for `mwis_medium_seed3`; inspect verifier failure `claimed total_weight 381 does not match computed 377`.
`gpt-5.4-mini` did not beat the baseline gap on `mwis_medium_seed3`.
