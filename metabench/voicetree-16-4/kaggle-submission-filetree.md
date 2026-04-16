---
color: blue
isContextNode: false
agent_name: Ari
---
# Filetree — metabench/kaggle_submission/

Concrete directory layout: benchmark/ (Factory A), harness/ (Factory B internal), kaggle/ (Factory B SDK-facing), analyzer/+paper/ (Factory C), results/ (runtime), scripts/, tests/, plus coordination markers.

# Filetree — `metabench/kaggle_submission/`

```
metabench/kaggle_submission/
├── README.md                        # entry point, run instructions
├── pyproject.toml                   # pinned deps (kaggle-benchmarks, ortools, google-genai, openai, anthropic)
├── schema-freeze.md                 # B-lead Hr 0–1 — field contract, SHA-pinned source of truth
├── predictions.md                   # C-lead Hr 1 — frozen pre-registration
├── .coordination/                   # factory status (not shipped)
│   ├── factory-a.md
│   ├── factory-b.md
│   ├── factory-c.md
│   └── handoffs.md                  # cross-factory blocking events
│
├── benchmark/                       # FACTORY A OUTPUT (dataset + verifiers)
│   ├── questions.jsonl              # A-lead consolidates — SINGLE WRITER at Hr 6
│   ├── questions/                   # per-(class,diff) fragments
│   │   ├── cjs_{medium,hard}.jsonl
│   │   ├── steiner_{medium,hard}.jsonl
│   │   ├── graphcol_{medium,hard}.jsonl
│   │   ├── tsp_{medium,hard}.jsonl
│   │   ├── mwis_{medium,hard}.jsonl
│   │   └── ve_{medium,hard}.jsonl
│   ├── portfolios.jsonl             # 90 portfolio Qs (10×3-of-6 + 5×4-of-6) × 2 bands × 3 seeds
│   ├── generators/{class}.py        # generate(difficulty, seed) → instance dict; 2 difficulty knobs
│   ├── verifiers/{class}.py         # verify(instance, submission) → (score, feasibility, details)
│   ├── verifiers/__init__.py        # CLASS_TO_VERIFIER registry
│   └── gold/gold.jsonl              # {id, gold_objective, baseline_objective, value_cap} via OR-Tools
│
├── harness/                         # FACTORY B OUTPUT (internal, SDK-agnostic)
│   ├── protocol.py                  # PLAN_STATE / UPDATED_PLAN_STATE / QUALITY_FORECAST / CONTINUE_FORECAST
│   ├── prompt.py                    # Layer 1 system (constant) + Layer 2 phase-specific contracts
│   ├── runner.py                    # preflight → raw-string loop → extract → verify → score → CF
│   ├── extractor.py                 # Gemini Flash post-hoc field extraction
│   ├── cf_fork.py                   # force +1 exec turn on clean stops; net Δ score computation
│   ├── scoring.py                   # solo: max(0,100−gap)−0.01·s ; portfolio: Σ value_cap·headroom−0.05·s
│   ├── render_nl.py                 # per-class instance → NL dispatch
│   └── clients/{gemini,gpt,anthropic,base}.py
│
├── kaggle/                          # FACTORY B OUTPUT (SDK-facing, thin adapter)
│   ├── tasks/solo_task.py           # kaggle_benchmarks.Task wrapping harness.runner for solo Qs
│   ├── tasks/portfolio_task.py      # Task wrapping runner for portfolio Qs
│   ├── benchmark.py                 # Benchmark(tasks=[...210]) — the mandatory Kaggle attachment
│   ├── kernel-metadata.json         # kernel config
│   ├── notebook.ipynb               # public notebook — reference Gemini 3 Pro × seed 1 × 210
│   ├── writeup.md                   # ≤1500 words, Metacognition track
│   └── media/cover.png              # mandatory cover image
│
├── analyzer/                        # FACTORY C OUTPUT
│   ├── extract_metrics.py           # per-session M1/M4/M5/M6/M7/M10
│   ├── aggregate.py                 # cross-(seed,model,class) rollup
│   ├── cf_table.py                  # per-stop CF table builder
│   ├── plots.py                     # paper figures
│   └── tables.py                    # paper tables
│
├── paper/                           # FACTORY C OUTPUT (source for writeup.md)
│   ├── main.md                      # full draft: methodology → results
│   ├── figures/ , tables/
│   └── critic_log.md                # C-critic red-team exchanges
│
├── results/                         # RUNTIME OUTPUT, append-only partitioned
│   ├── phase1/{model}/{class}_{diff}_{seed}.json
│   ├── phase2/{model}/{portfolio_id}.json
│   ├── cf/{model}/{class}_{diff}_{seed}__cf.json
│   └── reference/gemini-3-pro__seed-1.jsonl
│
├── scripts/                         # CLI wrappers, deterministic
│   ├── run_session.py               # one (model, question) → JSON
│   ├── run_phase1.py                # 360 runs, parallel-5 on Kaggle kernels
│   ├── run_phase2.py                # 270 portfolio runs
│   ├── run_cf_pass.py               # iterate clean stops, force +1 turn
│   ├── build_questions.py           # A-lead: fragments → questions.jsonl
│   ├── recompute_gold.py            # OR-Tools regeneration
│   └── validate_schema.py           # JSONL rows against schema-freeze.md
│
└── tests/
    ├── test_protocol.py
    ├── test_verifiers.py            # per class: feasibility + gold sanity
    ├── test_extractor.py            # fixtures from all 3 model shapes
    └── fixtures/                    # frozen raw transcripts (risk #3 mitigation)
```


### NOTES

- `kaggle/` is a thin adapter, not a parallel implementation — Task objects delegate to harness.runner.
- `benchmark/questions/*.jsonl` fragment naming is load-bearing — build_questions.py globs this pattern.

structure [[kaggle-submission-design]]
