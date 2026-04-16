# portfolio_medium_seed8

## Parse
- `gemini-flash-latest`: parse_path=`runner_error`; stop_reason=`runner_timeout`; turns=0; attempts=3; error=Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/eval_harness/run_local.py", line 215, in <module>
    raise SystemExit(main())
                     ~~~~^^
  File "/Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/eval_harness/run_local.py", line 175, in main
    result = run_instance(
        llm,
    ...<7 lines>...
        components=row.get("components"),
    )
  File "/Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/harness/runner.py", line 141, in run_instance
    exec_response = _call_model(
        llm=llm,
        prompt_text=exec_prompt,
        timeout_s=expected_turn_s,
    )
  File "/Users/bobbobby/repos/voicetree-evals/metabench/kaggle_submission/harness/runner.py", line 437, in _call_model
    thread.join(timeout=timeout_s)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.13/3.13.12_1/Frameworks/Python.framework/Versions/3.13/lib/python3.13/threading.py", line 1095, in join
    self._handle.join(timeout)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^
KeyboardInterrupt
- `claude-sonnet-4.6`: parse_path=`strict_protocol_cf`; stop_reason=`decision_stop`; turns=1; attempts=1; error=-
- `gpt-5.4-mini`: parse_path=`strict_protocol_cf`; stop_reason=`decision_stop`; turns=2; attempts=1; error=-

## Feasibility
- `gemini-flash-latest`: feasible=False; failures=-
- `claude-sonnet-4.6`: feasible=False; failures=tsp_medium_seed8: submission must provide tour as a list of city indices
- `gpt-5.4-mini`: feasible=False; failures=tsp_medium_seed8: submission must provide tour as a list of city indices

## Score vs Baseline
- baseline_objective=0.0; gold_objective=100.0
- `gemini-flash-latest`: score=0.0; gap_pct=n/a; component_gaps=-
- `claude-sonnet-4.6`: score=24.026728114972272; gap_pct=n/a; component_gaps=cjs_medium_seed8=103.90%, steiner_medium_seed8=20.75%, tsp_medium_seed8=100.00%
- `gpt-5.4-mini`: score=25.083117571226236; gap_pct=n/a; component_gaps=cjs_medium_seed8=103.90%, steiner_medium_seed8=20.75%, tsp_medium_seed8=100.00%

## Transcript Coherence
- `gemini-flash-latest`: transcript_entries=0; wall_s=240.0s; stop_reason=`runner_timeout`
- `claude-sonnet-4.6`: transcript_entries=3; wall_s=42.5s; stop_reason=`decision_stop`
- `gpt-5.4-mini`: transcript_entries=4; wall_s=21.4s; stop_reason=`decision_stop`

## Suggested Fixes
- Tighten protocol adherence for portfolio outputs; parse failures fell back to baseline or runner stubs.
- Add stronger contract/schema reminders for sub-problem answers inside the portfolio response.
- Timeouts hit the runner budget; consider shorter outputs or a more decisive planning policy.
