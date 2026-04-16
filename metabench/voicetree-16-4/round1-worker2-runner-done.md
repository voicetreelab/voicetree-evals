# Round 1 Worker 2 Runner Done

Recovered locally after the spawned child runner stalled in analysis and was stopped without producing model outputs.

## Scope
- question_ids: steiner_medium_seed5, steiner_medium_seed8, graphcol_medium_seed2, graphcol_medium_seed5
- models: gemini-flash-latest, claude-sonnet-4.6, gpt-5.4-mini

## Per-model parse rates
| model | completed | strict | rescue | failed_or_baseline | feasible | errors | skipped |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gemini-flash-latest | 4 | 4 | 0 | 0 | 4 | 0 | 0 |
| claude-sonnet-4.6 | 4 | 4 | 0 | 0 | 4 | 0 | 0 |
| gpt-5.4-mini | 4 | 4 | 0 | 0 | 3 | 0 | 0 |

## Per-question headlines
- steiner_medium_seed5: gemini-flash-latest: parse=strict_protocol_cf, feasible=True, score=96.1164, stop=decision_stop; claude-sonnet-4.6: parse=strict_protocol_cf, feasible=True, score=93.9696, stop=decision_stop; gpt-5.4-mini: parse=strict_protocol_cf, feasible=False, score=0.0000, stop=decision_stop
- steiner_medium_seed8: gemini-flash-latest: parse=strict_protocol_cf, feasible=True, score=96.1617, stop=decision_stop; claude-sonnet-4.6: parse=strict_protocol_cf, feasible=True, score=99.3023, stop=decision_stop; gpt-5.4-mini: parse=strict_protocol_cf, feasible=True, score=79.1360, stop=decision_stop
- graphcol_medium_seed2: gemini-flash-latest: parse=strict_protocol_cf, feasible=True, score=96.7340, stop=decision_stop; claude-sonnet-4.6: parse=strict_protocol_cf, feasible=True, score=98.0628, stop=decision_stop; gpt-5.4-mini: parse=strict_protocol_cf, feasible=True, score=-0.1530, stop=decision_stop
- graphcol_medium_seed5: gemini-flash-latest: parse=strict_protocol_cf, feasible=True, score=96.5242, stop=decision_stop; claude-sonnet-4.6: parse=strict_protocol_cf, feasible=True, score=97.2423, stop=decision_stop; gpt-5.4-mini: parse=strict_protocol_cf, feasible=True, score=-0.1363, stop=decision_stop
