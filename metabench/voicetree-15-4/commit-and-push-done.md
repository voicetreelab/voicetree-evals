---
color: green
isContextNode: false
agent_name: Tao
---
# Repo committed in groups and pushed

Grouped all pending changes into 10 logical commits and pushed to origin/main.

## Commit Groups

| # | Commit | Concern |
|---|--------|---------|
| 1 | `8aab7c1` | Root config: `.gitignore`, `forecastbench-src`, `.mcp.json`, `.codex/` |
| 2 | `4326ff8` | HCH metagame: full `hch/` directory (spec, TSP/jobshop/Steiner/Kolmogorov spikes, results) |
| 3 | `52f16ed` | Kaggle HLE-12 examples: modified `q41–q99` hch + vanilla solutions |
| 4 | `7fb53de` | Kaggle CJS spike: `examples/coupled_jobshop_spike/` |
| 5 | `38a0524` | Kaggle scripts, option-A bridge, `.env.flashlite`, `.env.gptnano` |
| 6 | `8ce1029` | Kaggle pilots (11 models) + results (CJS 5x6, HLE-12 v2 multi-model) |
| 7 | `79c8a39` | VoiceTree vault `voicetree-15-4/`: new task nodes, spike nodes, chromadb state |
| 8 | `872fd32` | CSU: `csu/generate_csu.py` |
| 9 | `1d57c05` | Vault export: `voicetree-15-4-with-results/` + `voicetree-15-4.zip` |
| 10 | `56c45ae` | Straggler: `hch/masked_block_jobshop/jobshop_instance.py` |

Pushed: `fd8dd9a..56c45ae → main`

### NOTES

- `forecastbench-src` shows `m` (dirty submodule working tree) — not actionable from parent repo; committed pointer is correct.
- `.env.flashlite` and `.env.gptnano` were committed as they were already tracked per repo policy (not in .gitignore).

[[1776334837979iYE]]
