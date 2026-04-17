# Instructions — reproducing the benchmark

The writeup (repo [README.md](README.md)) describes the benchmark's design and findings. This doc covers how to run it.

## Layout

```
metabench/kaggle_submission/
├── questions.jsonl          # frozen 210-instance benchmark (7 classes × 2 difficulties + portfolios)
├── harness/                 # protocol + plan/exec loop
├── verifiers/               # pure-Python CP-SAT/ILP verifiers per class — no LLM-as-judge
├── generators/              # procedural instance generation
├── scripts/
│   ├── build_questions.py   # regenerate questions.jsonl (WARNING: clobbers the frozen set)
│   ├── run_kaggle_production.py
│   └── analyze_metacog.py   # score M1–M5 + Murphy + BSS + pricing-bias
├── results/
│   ├── full/<row_id>/<model>.json      # small-tier overnight rows
│   └── runs/<model>/<row_id>.json       # frontier-tier sweep rows
└── writeup-v3.md            # Kaggle submission writeup (same as repo README)
```

## Install

```bash
cd metabench/kaggle_submission
pip install -e .
```

Requires Python ≥ 3.11 and OR-Tools. Provider API keys (Anthropic / OpenAI / Google) must be set in your environment if you plan to run live models.

## Reproduce the analysis

The per-row transcripts are already committed under `results/`. To regenerate the metacog report and rollup CSV from the existing transcripts:

```bash
python metabench/kaggle_submission/scripts/analyze_metacog.py
```

Outputs:

- `results/metacog_analysis.md` — full report (§3 is the 6-model family-consistency table)
- `results/metacog_rollup.csv` — per `(model, class, difficulty)` rollup
- `results/metacog_calibration_bins.csv`

## Re-run the sweep

Frontier-tier sweep runner:

```bash
python metabench/kaggle_submission/scripts/run_kaggle_production.py --model <model-slug>
```

Each row produces `results/runs/<model>/<row_id>.json` with the transcript, final score, and extracted metacog fields. The `analyze_metacog.py` script picks up new rows automatically on next run.

## Verifier contract

Every verifier in `verifiers/{class}.py` takes a submitted artifact (JSON) and returns `{feasible: bool, score: float, gap_pct: float}`. Verifiers are pure Python — no LLM — so results are deterministic and independently auditable.

## Submission proof

See [submission_proof.png](metabench/kaggle_submission/submission_proof.png) for the Kaggle submission attempt timestamp.
