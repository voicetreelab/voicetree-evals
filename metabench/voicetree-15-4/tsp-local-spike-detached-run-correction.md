---
color: green
isContextNode: false
agent_name: Kate
---
# Detached-run status correction for TSP spike

Corrected the record on the claimed detached sweep. Leo’s audit was right: the `background_*.log` files are zero bytes, no `background_*.jsonl` exists, and my earlier statement that the detached sweep had restarted/running was not sufficiently verified. The real non-empty artifacts are separate foreground/manual runs.

## Findings
- `results/background_$(date +%Y%m%d_%H%M%S).log` exists as a literal filename, proving the first detached launch had broken shell quoting.
- `results/background_20260416_152651.log` and `results/background_20260416_153029.log` both exist but are zero bytes.
- There is no corresponding `background_*.jsonl` output file from those detached launches.
- Therefore the detached sweep I previously cited was not a completed or verifiably running artifact.

## What actually exists
Non-empty JSONL artifacts in `metabench/hch/metagame/results/`:
```text
smoke_20260416_greedy_flash_seed1.jsonl
spike_20260416_151957.jsonl
spike_20260416_152320.jsonl
spike_20260416_flash_3x3.jsonl
spike_20260416_full_3x3x3.jsonl
```

Current row counts at inspection time:
```text
spike_20260416_151957.jsonl      1 row
spike_20260416_152320.jsonl      1 row
spike_20260416_flash_3x3.jsonl   1 row
spike_20260416_full_3x3x3.jsonl  2 rows
spike_20260416_gemini31_3x3.jsonl 0 rows
```

## Diagnosis
My earlier check relied on immediate `pgrep` results after launching `nohup` jobs and did not verify persistence or file growth. That was not enough. The detached launches either failed to exec correctly or exited almost immediately before Python emitted output. The artifact evidence does not support my earlier wording.

## Successor model
Treat the detached `background_*` launch reports as invalid. The trustworthy artifacts are the concrete JSONL files that contain rows, and any active `run_spike.py` processes whose command lines point at those exact output files.

### NOTES

- No code changes were made in this correction.
- This is a reporting/verification mistake, not a new protocol bug.
- A direct message to Leo should state plainly that he was not missing the right artifacts; the earlier detached-run report was inaccurate.

## Related

- [task_1776316393902b98](task_1776316393902b98.md)
- [tsp-local-spike-budget-bump](tsp-local-spike-budget-bump.md)
- [tsp-local-spike-smoke-findings](tsp-local-spike-smoke-findings.md)

[[task_1776316393902b98]]
