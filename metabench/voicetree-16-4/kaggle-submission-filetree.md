---
color: blue
isContextNode: false
agent_name: Ari
---
# Filetree — metabench/kaggle_submission/ (v2)

v2 collapse: single task file driven by evaluation_data DataFrame, no per-instance generation, no clients, no extractor, inline CF fork. Structure below reflects the `.evaluate()` + EMBEDDED_MODULES pattern.

# Filetree — `metabench/kaggle_submission/` (v2)

```
metabench/kaggle_submission/
├── README.md                        # entry point, run instructions
├── pyproject.toml                   # pinned deps (kaggle-benchmarks, ortools, pandas)
├── schema-freeze.md                 # B-lead Hr 0–1 — field contract, SHA-pinned
├── predictions.md                   # C-lead Hr 1 — frozen pre-registration
├── .coordination/                   # factory status (not shipped)
│   ├── factory-a.md
│   ├── factory-b.md
│   ├── factory-c.md
│   └── handoffs.md
│
├── questions.jsonl                  # SINGLE source of truth, 210 rows; class ∈
│                                    #   {cjs, steiner, graphcol, tsp, mwis, ve, portfolio}
│                                    # Row fields: {id, class, difficulty, seed, instance,
│                                    #   gold_objective, baseline_objective, value_cap,
│                                    #   wall_budget_s, components?}  # components only for portfolio
├── questions/                       # fragment staging (GITIGNORED after Hr 6 freeze)
│   ├── cjs_{medium,hard}.jsonl
│   ├── steiner_{medium,hard}.jsonl
│   ├── graphcol_{medium,hard}.jsonl
│   ├── tsp_{medium,hard}.jsonl
│   ├── mwis_{medium,hard}.jsonl
│   ├── ve_{medium,hard}.jsonl
│   └── portfolios.jsonl
│
├── generators/{class}.py            # regen/reproducibility, NOT shipped in task
├── verifiers/{class}.py             # verify(instance, submission) → (score, feasible, details)
│                                    # EMBEDDED into task.py at build time
├── verifiers/__init__.py            # CLASS_TO_VERIFIER registry
├── gold/gold.jsonl                  # {id, gold_objective, baseline_objective, value_cap}
│
├── harness/                         # pure logic, EMBEDDED into task.py via base64
│   ├── protocol.py                  # PLAN_STATE / UPDATED_PLAN_STATE / forecasts + regex parsers
│   ├── prompt.py                    # system prompt + Turn 1 / Turn N / force-continue contracts
│   ├── runner.py                    # raw-string loop using injected `llm`
│   │                                # returns row w/ score_at_stop, score_after_cf, cf_delta INLINE
│   ├── scoring.py                   # solo: max(0, 100 − gap_pct) − 0.01·wall_s
│   │                                # portfolio: Σ value_cap·headroom − 0.05·wall_s
│   └── render_nl.py                 # per-class instance → NL dispatch
│
├── kaggle/
│   ├── task.py                      # THE single task file — @kbench.task + EMBEDDED_MODULES
│   │                                # Signature:
│   │                                #   @kbench.task(name="metacog_optim_v1", ...)
│   │                                #   def run_instance(
│   │                                #       llm, instance_json: str, cls: str, difficulty: str,
│   │                                #       seed: int, gold_objective: float,
│   │                                #       baseline_objective: float, value_cap: float
│   │                                #   ) -> float: ...
│   ├── build_task.py                # concatenates harness/ + verifiers/ → task.py EMBEDDED_MODULES
│   ├── kernel-metadata.json         # single notebook metadata
│   ├── notebook.ipynb               # loads questions.jsonl as df, calls task.evaluate(df)
│   ├── writeup.md                   # ≤1500 words, Metacognition track
│   └── media/cover.png              # mandatory cover image
│
├── analyzer/                        # LOCAL post-hoc, consumes fetched run outputs
│   ├── extract_metrics.py           # M1/M4/M5/M6/M7/M10 from JSONL rows
│   ├── aggregate.py                 # cross-(seed, model, class) rollup
│   ├── cf_table.py                  # per-stop CF table from cf_delta field
│   ├── plots.py                     # paper figures
│   └── tables.py                    # paper tables
│
├── paper/                           # Factory C — source for writeup.md
│   ├── main.md                      # full draft
│   ├── figures/ , tables/
│   └── critic_log.md
│
├── results/                         # runtime, partitioned, append-only
│   ├── runs/{model}/{run_id}.jsonl  # one row per evaluation_data row
│   └── reference/gemini-3-pro.jsonl
│
├── scripts/
│   ├── run_local_fixture.py         # fixture check with stub llm (no Kaggle)
│   ├── build_questions.py           # fragments → questions.jsonl (one-shot, Hr 6)
│   ├── build_and_upload.py          # build_task.py → upload notebook via kaggle API
│   └── fetch_results.py             # pull .evaluate() run outputs for analyzer
│
└── tests/
    ├── test_protocol.py             # regex parsers against frozen transcripts
    ├── test_verifiers.py            # per class: feasibility + gold sanity
    ├── test_harness_fixture.py      # end-to-end on stub llm + CJS-5×6 seed-1
    └── fixtures/                    # frozen raw transcripts — all 3 model shapes
```

## What disappeared from v1

- `kaggle/tasks/solo_task.py` + `kaggle/tasks/portfolio_task.py` → merged into one `task.py`
- `kaggle/generated/` (210 per-instance files) → **gone**, `.evaluate(evaluation_data=df)` handles fan-out
- `kaggle/benchmark.py` → **gone**, not a kbench concept; DataFrame IS the benchmark
- `harness/clients/{gemini,gpt,anthropic,base}.py` → **gone**, Kaggle injects `llm`
- `harness/extractor.py` → **gone**, regex parsing inline; `kbench.judge_llm` is the fallback
- `harness/cf_fork.py` → **gone**, inline CF in `runner.py` on same transcript
- `benchmark/` wrapper dir → flattened to top-level (questions.jsonl, verifiers/, generators/, gold/)
- `results/phase1/`, `results/phase2/`, `results/cf/` split → flat `results/runs/{model}/` since CF and portfolio are part of each row

## Why the EMBEDDED_MODULES pattern is load-bearing

`task.py` must be a single uploadable file, but it imports OR-Tools-using verifiers + harness logic. The spike's approach (`portfolio_spike.py`, 216KB):
```python
EMBEDDED_MODULES = {"verifiers/cjs.py": "<base64 source>", ...}
def _ensure_bundle():
    bundle_dir = Path(tempfile.gettempdir()) / "metacog_v1_bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    for filename, encoded in EMBEDDED_MODULES.items():
        (bundle_dir / filename).write_text(base64.b64decode(encoded).decode())
    sys.path.insert(0, str(bundle_dir))
_ensure_bundle()
from verifiers import CLASS_TO_VERIFIER  # now importable
```
`build_task.py` reads every `.py` in `harness/` and `verifiers/`, base64s them into the `EMBEDDED_MODULES` dict literal, then concatenates the task-defining suffix. One re-run per harness change.

### NOTES

- `task.py` expected ~150–300KB after bundling (portfolio_spike is 216KB with 5 modules).
- `kernel-metadata.json` ID format: `username/metacog-optim-v1` — see `kaggle_experiments/examples/metacog_format_recall_v1/`.
- `notebook.ipynb` can be minimal: import task.py, load questions.jsonl into df, call `.evaluate(llm=[kbench.llm], evaluation_data=df)`, save runs.
