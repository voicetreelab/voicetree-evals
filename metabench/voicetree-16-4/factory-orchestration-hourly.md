---
color: blue
isContextNode: false
agent_name: Ari
---
# Factory Orchestration — Hr-by-Hr (v2)

14h sequencing, v2-collapsed: Factory B now builds ONE `task.py` + notebook, not 210 task files. Factory A merges portfolios into `questions.jsonl` directly. Phase 1+2+CF run in a single `.evaluate()` pass per model (CF is inline).

# Factory Orchestration — Hr-by-Hr

## Mechanism (voicetree MCP)
- Each factory **lead** runs in its own voicetree terminal.
- `spawn_agent` creates Codex subagents; brief includes pinned `schema-freeze.md` commit SHA + explicit write-path whitelist.
- Leads gate with `wait_for_agents` on two events: schema freeze (Hr 1), questions.jsonl freeze (Hr 6).
- Each lead drops one hourly progress node per the factory-plan coordination requirement.

## Hr 0–1 — Schema freeze + spawn (SEQUENTIAL, blocks everything)
1. **B-lead** writes `schema-freeze.md` + skeleton `harness/protocol.py` (regex parsers + field types). `git commit`, record SHA.
2. **C-lead** writes `predictions.md` seeded from [[experiment-theory]]; commits.
3. **A-lead** reads frozen SHA, writes `.coordination/factory-a.md` with per-class Codex briefs.
4. All Codex spawned in parallel.

**Gate:** no Factory A or C work reads protocol fields before this commits.

## Hr 1–3 — Parallel implementation
- **A-Codex × 6** (CJS, Steiner, GraphCol, TSP, MWIS, VE) — each owns `generators/{class}.py`, `verifiers/{class}.py`, `questions/{class}_{medium,hard}.jsonl`.
  - A-Portfolio (1 extra Codex OR A-lead directly) owns `questions/portfolios.jsonl` sampling from other classes.
- **B-Codex × 3** (was 4, shrunk):
  - `harness/runner.py` — raw-string loop + **inline CF fork on DECISION: stop**
  - `harness/prompt.py` + `harness/render_nl.py`
  - `kaggle/build_task.py` + `kaggle/task.py` skeleton w/ EMBEDDED_MODULES stub
- **C-analyzer (Codex)** — `analyzer/extract_metrics.py` stubs against schema fields (reads `cf_delta` directly; no CF-join logic).
- **C-writer (Opus)** — drafts `paper/main.md` methodology + pre-reg sections.

## Hr 2–3 — First end-to-end fixture (BLOCKING CHECK)
B-lead runs `scripts/run_local_fixture.py` on CJS-5×6 medium seed-1 **the moment A-CJS commits its first row**. Stub `llm` replays a canned Gemini transcript from `tests/fixtures/`. Exercises: prompt → loop → regex parser → verifier → scoring → inline CF. Any contract drift fails fast.

**Critical check at this stage:** regex parsers against raw transcripts from all 3 model shapes (Gemini, GPT, Sonnet) in `tests/fixtures/`. If regex is clean across shapes → ship without `kbench.judge_llm`. If not → inline `judge_llm` extraction as fallback.

## Hr 3–6 — Consolidate + spot-check + build task
- A-lead runs 1 Gemini 3 Pro session per (class × difficulty) via harness → verifier passes. Bugs → ping respective A-Codex.
- A-lead runs `scripts/build_questions.py`: concatenates `questions/*.jsonl` → `questions.jsonl` + runs `scripts/recompute_gold.py` via OR-Tools. **A-lead sole writer.**
- B-Codex runs `kaggle/build_task.py` once verifiers are in; produces `task.py` (~200KB) with EMBEDDED_MODULES.
- C-critic red-teams `predictions.md`; C-writer iterates to final.

## Hr 6 — FREEZE GATE
`questions.jsonl` commit SHA is immutable. `questions/*.jsonl` fragments deleted or added to `.gitignore`.
`scripts/validate_schema.py` run as pre-Phase-1 gate.

## Hr 6–10 — Single-model reference pass + Kaggle task creation
- **Critical v2 change:** there is no "Phase 1" fan-out from our side. We upload ONE Kaggle task with `evaluation_data=questions_df` and let Kaggle's runner fan it out.
- `scripts/build_and_upload.py`:
  1. `kaggle kernels push` the notebook (which imports task.py + loads questions.jsonl into df + calls `.evaluate`)
  2. Verify task page renders
  3. Click "Evaluate More Models" for the 3 target models (Gemini 3 Pro, GPT-5.4, Sonnet 4.6) — this is UI/API driven, not code
- Reference run: Gemini 3 Pro is the first model triggered.
- `scripts/fetch_results.py` pulls run outputs as they complete → `results/runs/{model}/`.
- **C-analyzer pipelined** on fetched rows: each row already carries `cf_delta`, so M5/M6 extractable the moment the row lands.

## Hr 10–14 — Full model suite + writeup package
- All 3 models running via Kaggle. 210 rows × 3 models = 630 evaluations, but fan-out is Kaggle-side, not our compute.
- C-writer finalizes results section consuming `analyzer/tables.py` output.
- C-critic final red-team pass on `paper/main.md` + `kaggle/writeup.md` (≤1500 words, template-compliant).
- B-lead assembles submission:
  - `kaggle/notebook.ipynb` ← exported from reference run
  - `kaggle/writeup.md` ← compressed from `paper/main.md`
  - `kaggle/media/cover.png` ← added
  - `kernel-metadata.json` validated
  - Kaggle Benchmark project link created → attached to writeup
- Submit writeup before 09:59 AM GMT+10.

## What got simpler in v2 vs v1

| v1 | v2 | Hrs saved |
|---|---|---|
| B-Codex × 4 (incl. extractor) | B-Codex × 3 | ~2h |
| 210 task file generation in build_tasks.py | 1 task.py with build_task.py embed step | ~3h |
| Separate CF pass after Phase 1 | CF inline in same evaluation | ~2h |
| Per-model clients in harness | Drop entirely | ~1h |
| Kaggle Benchmark collection wiring | Single task page + "Evaluate More Models" | ~1h |

v2 reclaims ~9h — lets us harden fixtures, tighten writeup, re-run any flaky models.

## Fallback shedding (if compute tight)
- Drop seeds 10 → 5 per cell: 60 solo + 45 portfolio = 105 rows. Preserves 6-class coverage.
- Drop 1 model: keep Gemini 3 Pro + Sonnet 4.6 (Gemini is reference, Sonnet best-documented from `hch/portfolio_spike` pilot notes).

## Hand-offs (what blocks what)
See diagram.

### NOTES

- Hr 2–3 fixture check is still the load-bearing risk mitigation — don't skip to save time, it saves time downstream.
- `build_task.py` must be idempotent: re-run after any harness or verifier change regenerates EMBEDDED_MODULES cleanly.
- C-writer starts BEFORE any results — methodology + pre-reg write against the schema alone.
- Inline CF means the task wall budget needs +300s reserve; set `TOTAL_BUDGET_S=1800` with `CF_RESERVE_S=300` → main loop max wall 1500s.
