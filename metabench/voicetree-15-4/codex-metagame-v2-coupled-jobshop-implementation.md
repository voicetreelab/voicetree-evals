---
color: green
isContextNode: false
agent_name: Mei
---
# Codex MetaGame v2: coupled job-shop spike implementation

Implemented a self-contained local Gemini spike under `hch/codex_metagame_v2` for the full coupled two-factory multi-machine job-shop setting. The new subtree includes exact CP-SAT gold solving, deterministic baseline generation, schedule verification, NL rendering, a multi-turn canonical-prompt protocol, a JSONL runner, and a grouped analyzer.

## What changed
- Added a new self-contained subtree for the full coupled job-shop benchmark candidate rather than mutating the older TSP harness.
- `jobshop_instance.py` now owns deterministic instance generation, a serial baseline scheduler, exact OR-Tools CP-SAT solving, strict schedule verification, NL rendering, and optional baseline-gap prefiltering.
- `protocol.py` implements the canonical multi-turn plan/execute loop with labeled parsing, hard per-turn timeouts, last-good-schedule retention, and row-level metrics.
- `run_spike.py` supports the spec smoke preset (`--smoke` = 3x4, pro, seed 1) plus arbitrary `--n-jobs/--n-machines` sweeps and `--min-baseline-gap-pct` prefiltering.
- `analyze.py` prints grouped summaries by model for gap, wall time, score, Brier, turn count, timeouts, infeasibility failures, and errors.
- Follow-up config change: restored the larger benchmark-style budget trio (`TOTAL=1800`, `SUBTASK=600`, `PLAN=300`) and changed the main default spike size from `4x5` to `6x7`.
- Follow-up contract change: replaced `p_correct_if_atomic` / `DECLARED_GAP` style fields with thresholded gap forecasts plus explicit one-more-subtask value forecasts, and updated the analyzer to report the new forecast metrics.

## Commands run
```sh
python -m py_compile /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/*.py
uv pip install --python /Users/bobbobby/repos/voicetree-public/.venv/bin/python -r /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/requirements.txt
python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path('/Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2')))
from jobshop_instance import build_instance, verify_schedule
inst = build_instance(seed=1, n_jobs=3, n_machines=4)
print('baseline', inst.baseline_makespan)
print('optimal', inst.optimal_makespan)
print('baseline_verify', verify_schedule(jobs=inst.jobs, n_machines=inst.n_machines, schedule=inst.baseline_schedule))
print('optimal_verify', verify_schedule(jobs=inst.jobs, n_machines=inst.n_machines, schedule=inst.optimal_schedule))
PY
python - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, str(Path('/Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2')))
from jobshop_instance import build_instance
inst = build_instance(seed=2, n_jobs=4, n_machines=5, min_baseline_gap_pct=70)
print('baseline', inst.baseline_makespan)
print('optimal', inst.optimal_makespan)
print('gap_pct', round(100*(inst.baseline_makespan-inst.optimal_makespan)/inst.optimal_makespan,2))
PY
python - <<'PY'
from pathlib import Path
import sys, time
sys.path.insert(0, str(Path('/Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2')))
from jobshop_instance import build_instance
start = time.monotonic()
inst = build_instance(seed=1, n_jobs=6, n_machines=7, min_baseline_gap_pct=10)
wall = time.monotonic() - start
print({'baseline': inst.baseline_makespan, 'optimal': inst.optimal_makespan, 'gap_pct': round(100*(inst.baseline_makespan-inst.optimal_makespan)/inst.optimal_makespan,2), 'build_wall_s': round(wall,2), 'problem_len': len(inst.problem_statement)})
PY
python /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/run_spike.py --models gemini-3.1-pro-preview --seeds 1 --n-jobs 6 --n-machines 7 --output /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/results/gemini31_6x7_newforecast_seed1_20260416.jsonl
```

## Learnings
- Tried carrying a full baseline JSON schedule in the turn-1 prompt, then reduced it to a summary when all models still timed out under the locked 30s planning budget. The bottleneck is the plan-time budget on the coupled task, not prompt bloat alone.
- Do not conflate Meg's simpler Johnson-rule flowshop ceiling with this task. The full coupled multi-machine job-shop variant does not show that collapse in local checks.
- A successor should treat offline exact solving as solved engineering. The open question is protocol economics: what plan budget / size regime reveals metacog rather than immediate timeout.
- The benchmark-facing prompt is already natural language, but it does **not** currently include explicit distraction context beyond the manufacturing cover story and baseline summary. That is a separate lever, not yet implemented.
- The new forecast contract parses cleanly with Gemini 3 and is more informative: thresholded gap probabilities and one-more-subtask value forecasts exposed much better calibration structure than `p_correct_if_atomic`.


## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/__init__.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/requirements.txt
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/gemini_client.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/prompt.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/jobshop_instance.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/render_nl.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/protocol.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/analyze.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/prompt.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/run_spike.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/results/.gitkeep
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/EXPERIMENT_SPEC.md
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/results/gemini31_6x7_newforecast_seed1_20260416.jsonl

### NOTES

- `gemini_client.py` now falls back to `hch/metagame/.env`, per task guidance and Max's confirmation.
- `build_instance(..., min_baseline_gap_pct=...)` can deterministically retry generation to enforce baseline headroom without hardcoding one size.
- Exact solving was not the blocker: CP-SAT solved sampled `4x5`, `5x6`, and `6x7` instances essentially instantly in local checks.

## Related

- [jobshop-local-spike-ceiling](jobshop-local-spike-ceiling.md)

[[task_1776322276544vcx]]
