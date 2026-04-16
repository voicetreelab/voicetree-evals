---
color: blue
isContextNode: false
agent_name: Amit
---
# Factory Plan — 3 Parallel Factories to Build v1 in ~14h

Three parallel factories with Opus orchestrators coordinating Codex implementers: Content (dataset+verifiers), Platform (harness+kaggle), Research (analysis+paper). Ships in ~14h with all 210 questions, Phase 1+2 data, CF pass, paper draft through results.

# Factory Plan — Building v1

Three parallel factories, each with **Opus orchestrator** coordinating **Codex implementers**.

## Factory A — Content (dataset + verifiers)
**A-lead (Opus):** schema freeze review, per-class task definition, PR review, consolidate fragments to `questions.jsonl`.

**A-Codex (one per problem class):**
- A-CJS: CJS-5×6 generator + verifier (baseline: `hch/codex_metagame_v2/`)
- A-Steiner: Steiner×coloring (baseline: `hch/portfolio_spike/steiner_coloring_*.py`)
- A-GraphCol: graph coloring slack (baseline: `hch/portfolio_spike/graph_coloring_instance.py`)
- A-TSP: TSP (baseline: `hch/portfolio_spike/tsp_instance.py`)
- A-MWIS: treewidth MWIS (baseline: `hch/treewidth_mwis/`)
- A-VE: Bayesian VE (baseline: `hch/bayesnet_ve/`)

**Each A-Codex deliverable:**
- `verifiers/{class}.py` — `verify(instance, submission) → (score, feasibility, details)`
- `generators/{class}.py` — `generate(difficulty, seed) → instance` with 2 difficulty knobs (medium, hard)
- Fragment `questions/{class}_{difficulty}.jsonl` — 10 rows/difficulty with embedded gold + baseline
- Spot-check: 1 Gemini 3 Pro run per (class × difficulty) confirming contract parses + verifier works

A-lead consolidates fragments → `benchmark/questions.jsonl` once all 6 agents commit.

## Factory B — Platform (harness + runner + Kaggle port)
**B-lead (Opus):** unified protocol contract, Kaggle kernel shape, end-to-end validation.

**B-Codex:**
- B-protocol: extract `codex_metagame_v2/protocol.py` → `benchmark/protocol.py`; ADD `PLAN_STATE`, `UPDATED_PLAN_STATE`, continuous forecast fields per spec; switch to raw-string loop (no live parsing)
- B-extractor: post-hoc LLM extractor (Gemini Flash) pulling structured fields from raw transcripts; validated on all 3 model output shapes
- B-runner: `run_session.py` — preflight → loop → extract → verify → score → CF. Output matches `kaggle/results/` JSONL format
- B-kaggle: Kaggle kernel scaffolding — leaderboard submission shape, grader script

**B-lead runs one end-to-end session** on CJS-5×6 medium seed-1 as soon as schema freezes — catches contract drift before Factory A scales.

## Factory C — Research (analysis + paper)
**C-lead (Opus):** pre-registration freeze, analyzer design, writer/critic split.

**C-agents:**
- C-analyzer (Codex): per-session metric extraction (M1/M4/M5/M6/M7/M10) → per-run JSONL; cross-seed/cross-model aggregation
- C-cf (Codex): batch CF runner on JSONL result files → per-stop CF table
- C-writer (Opus): paper draft; starts methodology + pre-registration NOW, before any Phase 2 data
- C-critic (Opus, *separate agent*): red-teams writer's draft for n-size weakness, post-hoc framing, missing confounds. Writer iterates until critic passes.

**Pre-registration freeze:** C-lead commits `predictions.md` (from theory node) before any Phase 1 fires.

## Sequencing

| hour | Factory A | Factory B | Factory C |
|---|---|---|---|
| 0–1 | spawn all 6 Codex | schema-freeze.md | pre-reg draft |
| 1–3 | generators in parallel | E2E fixture validation | pre-reg critic review |
| 3–6 | consolidate fragments | harness harden | methodology writing |
| 6–10 | gold recompute + freeze | Phase 1 runs (360, parallel-5) | analyzer processes stream |
| 10–14 | — | Phase 2 (270) + CF pass | results section + critic |

## Coordination artifacts
- **schema-freeze.md** (B-lead, Hour 0–1) — single markdown as field-name source of truth. A and C pin to its commit SHA.
- **predictions.md** (C-lead, Hour 1) — blocks Phase 1 firing.
- **questions.jsonl** (A-lead, Hour 6) — blocks Phase 1 firing.
- **Hourly voicetree progress nodes** — each factory drops one per hour of active work.

## Risk register
1. **Schema drift across factories.** → single frozen markdown pinned by commit SHA, not by copy-paste.
2. **Verifier bugs surface late.** → A-lead spot-checks every (class × difficulty) with 1 Gemini run before scaling seeds.
3. **Raw-string extractor fails on some model's output shape.** → B-extractor validated on all 3 target models in Hour 0–2.
4. **CF reveals family-dependent stop-calibration variance.** → not a risk, that's a finding. Writer/critic prepared for either direction.
5. **Phase 1 compute overruns.** → parallel-5 on Kaggle kernels; can shed seeds 10→5 per cell if budget tight.

## End-of-hour-14 commit
- Frozen ~210-question benchmark dataset
- Phase 1 + Phase 2 + CF data across 3 frontier models
- Analyzer tables for all 5 primary metacog skills (M1/M4/M5/M6/M7) + M10 portfolio
- Pre-registered predictions evaluated against outcomes
- Paper draft through results section
- Kaggle leaderboard reference run (Gemini 3 Pro × seed 1 × 210)

## Prediction claims
- Factory-A dominant risk: generator difficulty knobs for MWIS/VE may not exist at 2 distinct levels; could collapse to 1 difficulty for those 2 classes → 180 solo instead of 120 ... wait actually 180 is more than 120, correcting: could collapse 2 difficulties to 1 for those 2 classes, yielding 6×2×10 − 2×1×10 = 100 solo.
- Factory-B dominant risk: raw-string extraction has ~10% failure rate on long transcripts; plan for retry + manual spot-check of extractor failures.
- Factory-C dominant risk: Phase 1 seed n=10 per cell may be insufficient for M10 capability-ceiling estimation if variance is high; mitigation is to ship n=10 in v1 and widen to n=20 post-pilot.


builds [[experiment-spec]]

[[/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan_1.md]]
[[/Users/bobbobby/repos/voicetree-evals/metabench/voicetree-16-4/factory-plan_2.md]]