---
color: green
isContextNode: false
agent_name: Ayu_1
---
# OVERNIGHT-RESULTS — Morning Wake-Up Brief

**Start reading here.** The overnight autopilot ran 2 full rounds of question generation + LLM evaluation. Both rounds PROCEEDED. Dataset is ready for review.

---

## Headline

Rounds 1 and 2 completed. The benchmark grew from 26 → 120 → **206 rows** across 8 workers × 2 rounds. A total of **~192 LLM model runs** were executed across 64 probe rows × 3 models (with some skips/timeouts in R1). Solo-hard questions are now well-covered for all 6 classes (cjs/steiner/graphcol/tsp/ve/mwis) with 3–12 seeds each. Portfolio rows exist in volume (medium + hard, seeds 1–43 medium, 1–41 hard) but **every portfolio row remained infeasible** — models failed to simultaneously solve all 3 sub-components of any portfolio question. This is the dominant signal from the overnight run.

---

## Per-Model Overall Parse Rate (Combined R1 + R2, 64 probe rows)

| Model | Strict parse | Partial rescue | Parse failed / skipped | Combined parse % |
|---|---:|---:|---:|---:|
| `gemini-flash-latest` | 43/64 | 11 | 10 | **84.4%** |
| `claude-sonnet-4.6` | 47/64 | 1 | 16 | **75.0%** |
| `gpt-5.4-mini` | 58/64 | 6 | 0 | **100%** |

**GPT is the most reliable parser.** Sonnet's 25% failure rate is driven by VE-hard + MWIS-hard stop=error events and some CJS hard failures. Gemini's rescue rate jumped from 3 (R1) to 8 (R2) — partial-rescue is working.

---

## Per-Class Feasibility Rate (Combined R1 + R2 Probes)

_Solo-class rows only. Portfolio excluded (treated separately below)._

| Class | Difficulty | Rows probed | Feasible runs | Feasibility % | Notes |
|---|---|---:|---:|---:|---|
| CJS | medium | 3 | ~7/9 | ~78% | Strong, some R1 Sonnet parse fails |
| CJS | hard | 2 | 3/6 | 50% | Sonnet 0/2, Gemini 1/2, GPT 2/2 |
| Steiner | medium | 2 | ~8/9 | ~89% | Very strong |
| Steiner | hard | 2 | 6/6 | 100% | All 3 models, gap_pct=0.0 |
| Graphcol | medium | 2 | ~8/9 | ~89% | Strong |
| Graphcol | hard | 3 | 9/9 | 100% | Perfect — GPT weak on score |
| TSP | medium | 2 | ~8/9 | ~89% | Strong |
| TSP | hard | 3 | 9/9 | 100% | Strong across all models |
| MWIS | medium | 2 | ~5/9 | ~56% | Sonnet timeouts in R1 |
| MWIS | hard | 3 | 6/9 | 67% | Sonnet 0/3 on hard |
| VE | medium | 2 | ~8/9 | ~89% | Strong |
| VE | hard | 3 | 7/9 | 78% | Sonnet fails seed4+seed7 |
| **Portfolio medium** | medium | 12 | 0/36 | **0%** | Model quality failure |
| **Portfolio hard** | hard | 12 | 1/36 | **2.8%** | 1 Sonnet solve with poor gaps |

**Solo hard questions discriminate models well.** Portfolio questions are currently unsolvable by all models.

---

## Top 5 Bugs / Concerns Surfaced

1. **Portfolio infeasibility is total and systematic** — 0/36 medium portfolio runs feasible, 1/36 hard (near-zero). Models parse portfolio questions correctly (~90%+) but fail to simultaneously satisfy all 3 sub-components. The harness is working; model planning/portfolio reasoning is failing. Diagnosis needed: is this a prompt engineering issue, an impossible difficulty level, or a fundamental multi-objective limitation?

2. **Sonnet MWIS hard: 0/3 feasible, stop=error** — Sonnet produced strict_parse_failed on all 3 MWIS hard probes (seeds 5, 9, 13). This extends the pattern from R1 where Sonnet failed all 3 MWIS medium probes via timeout. Sonnet+MWIS is a consistent failure mode. Gemini and GPT both solve MWIS hard 3/3.

3. **W6 portfolio hard generation shortfall (4/12)** — The MWIS hard bridge-check failure is deterministic and exhausted 8 of 12 requested hard-portfolio seeds. The current MWIS hard generator cannot reliably populate portfolio-hard rows when the seed's 3-class draw includes MWIS. Fix: either patch the bridge-check pre-flight or set an exclusion list for MWIS-containing portfolio-hard seeds.

4. **Cross-worker seed drift (W7 → W8)** — Worker 7 started from seed 33 (seed 32 failed) and generated up to seed 38 (inclusive), eating 2 IDs meant for Worker 8. This is an artifacts-only issue (W7's copy was kept, W8's duplicate was discarded), but the partition design should include explicit seed handover points with fallback bounds per worker.

5. **GPT score quality on graphcol/steiner** — GPT parses perfectly (100%) and is fastest, but scores near 0 or negative on graphcol hard (−0.12 to −0.42) and below Gemini/Sonnet on steiner hard. GPT's feasibility comes from sub-optimal solutions that don't improve over baseline. This matters for leaderboard ranking: GPT appears reliable but is a weak optimizer on graph problems.

---

## Rounds Completed + Approximate Time

| Round | Started | Commits finished | Duration |
|---|---|---|---|
| Round 1 (gen + eval) | ~03:57 AEST | 04:30 AEST (R1 consolidation) | ~33 min |
| Round 2 (gen + eval) | ~04:30 AEST | 05:46 AEST (W4 final commit) | ~76 min |
| **Total overnight** | ~03:57 AEST | 05:46 AEST | **~1h 49min** |

(Timestamps from git log; R2 workers ran in parallel so elapsed ≠ sum of worker times)

---

## Recommended Next Steps for Morning-Ivan

**Priority 1: Investigate portfolio infeasibility.** Run a manual trace on 1 portfolio-medium row (e.g. `portfolio_medium_seed14`) to understand why no model produces a feasible joint solution. Hypotheses to test: (a) prompt is not communicating the joint-feasibility requirement clearly enough, (b) value_caps=33/33/34 are too tight for the LLM's greedy sub-problem solving, (c) the baseline=0 assumption inflates the difficulty. Fix before treating portfolio scores as a benchmark signal.

**Priority 2: Patch MWIS hard generator** (or exclude MWIS from portfolio-hard class pool). The bridge-check failure is deterministic at most seed positions. This is blocking ~60% of portfolio-hard generation. Either lower n_nodes earlier (n_nodes=100 worked for some) or add a class exclusion flag for portfolio-hard.

**Priority 3: Ship dataset to Kaggle for v2 submission.** The solo-hard coverage is now strong: 206 rows, 6 classes × 2 difficulties, up to 12 seeds each. GPT and Gemini show differentiated quality. This is enough for a meaningful leaderboard signal even without portfolio rows. Run `kaggle_submission/scripts/run_kaggle_production.py` to build the v2 submission artifact.

**Priority 4 (optional): Investigate Sonnet MWIS hard.** Sonnet's stop=error pattern on MWIS hard is reproducible (0/6 across R1+R2). Root cause likely max_tokens exhaustion or a model-specific failure in iterative branch-and-bound reasoning. Juan's max_tokens fix improved Sonnet R1 scores generally but didn't help MWIS hard.

---

## Dataset State

| Metric | Value |
|---|---|
| Total rows | **206** |
| Solo medium | 60 (all 6 classes × seeds 1-10) |
| Solo hard | 72 (all 6 classes × 3-12 seeds) |
| Portfolio medium | 43 seeds (1-31 + sparse 33-43) |
| Portfolio hard | 31 seeds (1-28 + sparse 30-41) |
| Total LLM probe runs | ~192 (64 probe rows × 3 models, minus R1 skips) |
| Committed? | Pending this commit |
