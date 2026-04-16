# HANDOVER

## Goal of the next step

Run two cheap pilot spikes with this author-kit: two HCH questions and two MetaCoach questions. The purpose is not benchmark completeness. It is to validate the full Kaggle toolchain on both benchmark families with minimal quota burn: task authoring, execution, `.task.json`, `.run.json`, and the final "Save Task" UI step. Option A works today for this. Option B is still useful as packaging scaffolding, but fresh CLI-created slugs still have an unresolved `.run.json` gap.

## Where the specs live

- `../hch/`: `spec.md`, `explanation.md`, and runner/scorer scripts. This is the architectural metacognition benchmark: decomposition decision, per-sub `p_solve`, token-budget MAPE, intermediate verification, integration, and optional Bayesian update.
- `../metacoach/`: `spec.md`, `explanation.md`, and runner/scorer scripts. This is the prompt-level metacognition benchmark: accuracy, Brier, answer-redirection, correct-redirection, and failure-mode tracking.

## Concrete next actions

```bash
cd ~/repos/voicetree-evals/metabench/kaggle
source .venv/bin/activate
mkdir -p examples/hch_spike examples/metacog_spike pilots

# Author two HCH tasks, then run them through the live-kernel bridge.
python option_a_bridge/submit_task.py examples/hch_spike/q1.py
python option_a_bridge/submit_task.py examples/hch_spike/q2.py

# Author two MetaCoach tasks, then run them the same way.
python option_a_bridge/submit_task.py examples/metacog_spike/q1.py
python option_a_bridge/submit_task.py examples/metacog_spike/q2.py
```

Record each run in:

- `pilots/hch-spike-YYYYMMDD.md`
- `pilots/metacog-spike-YYYYMMDD.md`

Attach the generated `.task.json` and `.run.json` facts, not raw dumps.

## Open questions the pilot should answer

- Does `.run.json` expose per-call token breakdown or only aggregates?
- Can HCH recursion fit cleanly inside one `@kbench.task`, or does it need multi-task packaging?
- Does Kaggle's "Save Task" flow work cleanly for each pilot, and is the resulting leaderboard view useful?

## Known gotchas

See README section 7. Do not duplicate that list in pilot notes; just add any new pilot-specific failures.

## Estimated cost

Rough order of magnitude: about `$0.002` total for four tiny tasks, assuming the metacog seed cost remains representative.

## Provenance

Written by Ari orchestration session on 2026-04-15, post-consolidation. Kaggle hackathon deadline: April 16 2026 EOD. Treat this pilot as the go/no-go check before any larger submission push.
