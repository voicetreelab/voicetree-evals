---
color: green
isContextNode: false
agent_name: Kate
---
# Local TSP spike implementation

Implemented the local Gemini TSP-25 budget-metagame spike in `metabench/hch/metagame`: TSP instance generation, arm prompts, Gemini wrapper, locked-protocol harness, runner, analyzer, requirements, and explicit `.env` ignore entry.

## Deliverable
A runnable local spike now exists in `metabench/hch/metagame/` with this layout:

```text
requirements.txt
tsp_instance.py
arms.py
gemini_client.py
protocol.py
run_spike.py
analyze.py
kaggle-budget-metagame-design.md
.env   # written locally, gitignored
results/
```

## Implementation notes
- `tsp_instance.py` generates deterministic 25-city integer-coordinate TSP instances, a nearest-neighbor baseline, and a stronger near-gold tour via multi-start nearest-neighbor plus 2-opt to convergence.
- `arms.py` keeps the three benchmark arms as system-prompt variants only: `greedy`, `exhaustive`, and `smart`.
- `gemini_client.py` uses `google-genai` native chat history and exposes per-turn text plus `prompt_token_count`, `candidates_token_count`, `total_token_count`, and `thoughts_token_count` when available.
- `protocol.py` implements the locked multi-turn protocol with constants `TOTAL_BUDGET_S=300`, `SUBTASK_BUDGET_S=120`, `PLAN_TURN_BUDGET_S=30`, regex parsing, timeout wrappers, fallback-to-baseline semantics, and post-hoc scoring.
- `run_spike.py` iterates `models × arms × seeds`, writes JSONL incrementally, and prints the grouped summary table.
- `analyze.py` groups rows by `(model, arm)` and prints mean gap, wall time, score, Brier, and protocol-flag counts.

## Learnings
- Tried to stay close to the task node’s “native chat” requirement instead of switching to raw `generate_content`; that kept history handling simple enough and matched the intended protocol shape.
- The non-obvious pitfall is timeout behavior: `future.result(timeout=...)` stops the harness from waiting, but it does not truly kill the underlying HTTP request thread. For this spike that is acceptable, but for larger sweeps a subprocess-based kill boundary would be cleaner.
- Local direct Gemini calls expose token counts but not Kaggle-style cost/latency fields, so the local harness injects wall-clock plus tokens between turns rather than exact dollar cost.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/.gitignore
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/requirements.txt
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/tsp_instance.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/arms.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/gemini_client.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/protocol.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/run_spike.py
- /Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/analyze.py

### NOTES

- Root `.gitignore` already ignored `.env`, but the task explicitly asked for `metabench/hch/metagame/.env`, so that path was added explicitly.
- No Kaggle or kbench dependency was added; this is pure local Python plus `google-genai`.
- The local `.env` was written from the task node without committing it.

## Related

- [task_1776316393902b98](task_1776316393902b98.md)

[[task_1776316393902b98]]
