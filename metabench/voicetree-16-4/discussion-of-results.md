---
isContextNode: false
agent_name: Ben
---
# Discussion of Overnight Results

## Headline

The overnight autopilot (~03:57–05:46 AEST, 2026-04-17) ran two full rounds of question-generation + LLM evaluation. Eight Codex workers per round, each spawning a child runner. The benchmark grew from **26 → 120 → 206 rows** across 6 problem classes × 2 difficulties × up to 12 seeds, plus 43 portfolio-medium and 31 portfolio-hard seeds. A total of **~192 LLM probe runs** were executed (64 probe rows × 3 models, minus a handful of R1 budget skips). Both rounds produced PROCEED verdicts. The dominant overnight signal: **all three frontier models cleanly parse and solve solo problems but fail entirely on portfolio rows** — 1 / 72 portfolio model-runs returned a feasible joint solution.

---

## Per-Model Strict-Parse Rate (R1 + R2 combined, 64 probe rows × 3 models)

| Model | Strict | Rescue | Failed / Skipped | Total | Strict + Rescue % |
|---|---:|---:|---:|---:|---:|
| `gemini-flash-latest` | 43 | 11 | 10 | 64 | **84.4 %** |
| `claude-sonnet-4.6` | 47 | 1 | 16 | 64 | **75.0 %** |
| `gpt-5.4-mini` | 58 | 6 | 0 | 64 | **100 %** |

GPT-5.4-mini parsed every single probe. Sonnet's 25 % failure tail is concentrated in MWIS-hard (3/3 stop=error), VE-hard seeds 4+7 (stop=error), and W5/W6 budget skips. Gemini's rescue rate jumped from 3 (R1) to 8 (R2) — the partial-rescue parser is doing real work.

---

## Per-Class Feasibility Rate (R1 + R2 combined; G/S/GPT)

| Class | Difficulty | Probes | Gemini feasible | Sonnet feasible | GPT feasible | Notes |
|---|---|---:|---:|---:|---:|---|
| CJS | medium | 3 | 3/3 | 1/3 | 3/3 | Sonnet parse-fails on seeds 5+8 |
| CJS | hard | 2 (R2) | 1/2 | 0/2 | 2/2 | + R1: GPT-only seed4 (-0.18 score) |
| Steiner | medium | 3 | 3/3 | 3/3 | 2/3 | Strongest medium class |
| Steiner | hard | 2 (R2) | 2/2 | 2/2 | 2/2 | All gap_pct = 0.0 |
| Graphcol | medium | 3 | 3/3 | 3/3 | 3/3 | Clean across the board |
| Graphcol | hard | 3 | 3/3 | 3/3 | 3/3 | GPT feasible but score ~−0.2 |
| TSP | medium | 3 | 3/3 | 2/3 | 3/3 | Strong |
| TSP | hard | 3 | 3/3 | 3/3 | 3/3 | Strongest hard class |
| MWIS | medium | 3 | 3/3 | 0/3 | 1/3 | Sonnet timeout-then-skip; GPT gives up early |
| MWIS | hard | 3 | 3/3 | 0/3 | 3/3 | Sonnet stop=error every probe |
| VE | medium | 2 | 2/2 | 0/2 | 2/2 | Sonnet parse-fail + skip |
| VE | hard | 3 | 3/3 | 1/3 | 3/3 | Sonnet stop=error on seeds 4+7; OK on seed 10 |
| **Portfolio** | medium | 12 | 0/12 (1 timeout) | 0/12 | 0/12 | 0/36 feasible — total failure |
| **Portfolio** | hard | 12 | 0/12 | 1/12 (seed25) | 0/12 | 1/36 feasible; that 1 had poor gaps |

Solo difficulty discriminates the models well. Portfolio is currently a discriminator only of the *generator pipeline*, not of model quality.

---

## Headline Findings

1. **Portfolio is broken at the model layer, not the harness layer.** 0/36 portfolio-medium runs and 1/36 portfolio-hard runs returned a jointly-feasible answer across all three models. Parse rates on portfolio rows are ~90 %, so the harness sees a structured artifact every time — the artifact just doesn't satisfy all three sub-components simultaneously. From W6 generation notes (replicated in concerns.md spot-checks): the dominant failure is TSP sub-component output-format violations, with VE and graphcol schema non-compliance close behind. Portfolio scoring is currently a uniform near-zero floor across the leaderboard — useless as a benchmark signal until the model-side joint-feasibility behaviour is fixed.

2. **Sonnet has a class-specific failure mode on MWIS and VE hard.** Sonnet returned `strict_parse_failed` with `stop=error` on every MWIS-hard probe (0/3 in R2; 0/3 medium in R1 via timeout), and on VE-hard seeds 4 + 7. Same probe IDs ran cleanly on Gemini and GPT. This rules out instance-difficulty as the cause and points at a Sonnet-specific protocol-emission failure on iterative branch-and-bound reasoning — most likely max-token exhaustion mid-exec-turn-2, even *after* Juan's earlier max_tokens fix. Sonnet on these classes is the only "model dies on a class" pattern in the dataset.

3. **GPT-5.4-mini parses perfectly but optimises poorly on graph problems.** GPT hit 100 % parse coverage and is by far the fastest (often 10–20 s vs. Gemini's 200–500 s), but its solution quality on graphcol-hard and steiner-hard is weak. Concerns.md spot-check on `graphcol_hard_seed7`: Sonnet 99.19 score / gap 0 vs. GPT 84.86 / gap 15 (and on other graphcol-hard seeds GPT scored −0.12 to −0.42). Reliability and quality are decoupled here — leaderboard ranking by parse rate will mislead.

4. **W5 budget guardrail produced GPT-only data on 3 hard rows.** Worker 5's runner saw row-1 wall times of 417.9 s (Gemini) and 367.2 s (Sonnet) on `ve_medium_seed5`, and pre-emptively skipped Gemini + Sonnet on `ve_medium_seed8`, `cjs_hard_seed4`, and `steiner_hard_seed4`. Net effect: those rows have no multi-model comparison, and the only data point for `cjs_hard_seed4` is GPT scoring −0.18 (baseline-equivalent). The guardrail behaviour is correct given the budget contract, but it leaves a coverage hole in the dataset.

5. **Mary/Rex late divergence on W1 (silently improved 2 cells).** W1 had two artifacts: Mary's child-runner output (committed at hash `6470942`) and a later Rex resumed-runner output (uncommitted at consolidation time). Rex's run upgraded `steiner_medium_seed2/gemini` from baseline_only (80.1) to strict (96.2, gap 0.0), and `cjs_medium_seed8/gemini` from 34.8 to 90.1. The Round 1 reviewer accepted Rex's strictly-better artifacts. Lesson: parallel-runner reconciliation needs an explicit "later run wins iff strictly better on parse-path × score" rule — currently this was a manual judgement.

6. **Cross-worker seed drift (W7 → W8).** R2 W7 generated portfolio seeds up to 38 (med) and 36 (hard) after seed-fallback chains, consuming IDs that the partition had assigned to W8. The reviewer kept W7's copies and dropped W8's duplicates. Artifacts-only issue — but it shows the partition design lacks fallback-window bounds. Two seeds is small; eight workers in a ring with no backstop is the kind of design that breaks at 16.

7. **Generator weakness: MWIS-hard bridge-check is deterministic.** R2 W6 was assigned 12 portfolio-hard rows and produced only 4 — eight requested seeds failed because the underlying MWIS-hard generator's bridge-check pre-flight is deterministically infeasible at those seed positions. This is a *generator* limit, not a model limit. The pipeline correctly logged + skipped, but ~67 % of the requested R2 portfolio-hard cells are simply unproducible without patching `mwis_hard.py` or excluding MWIS from the portfolio-hard class pool.

8. **R1 vs R2 review agreement.** Both reviewers (Tao for R1, Ayu_1 for R2) issued PROCEED verdicts and converged on the same three top concerns (portfolio infeasibility, Sonnet MWIS pattern, generator/budget shortfalls). No contradictions between the rounds. The R2 reviewer's parse-rate numbers (Gemini 22/32 strict + 8 rescue, Sonnet 25/32, GPT 29/32) match the OVERNIGHT-RESULTS aggregation within rounding.

---

## Top Bugs Surfaced

1. **Portfolio joint-feasibility failure (BLOCKER).** 0 / 36 medium and 1 / 36 hard portfolio runs feasible. Root-cause hypothesis: the per-sub-component output contract in the portfolio prompt is implicitly requiring the model to re-derive the TSP / VE / graphcol artifact schemas on every turn. Models output something parseable but structurally non-compliant on at least one of the three components, so joint-feasibility falls through. Severity: blocker for any portfolio-driven leaderboard signal.

2. **Sonnet stop=error on MWIS-hard / VE-hard (BLOCKER for Sonnet on those classes).** 0/6 MWIS hard runs feasible across both rounds. Root-cause hypothesis: max-token truncation mid-exec-turn-2 even after Juan's max-token fix; or Sonnet-specific failure when emitting long iterative DP traces. Severity: blocker — Sonnet contributes zero signal on those cells.

3. **W6 portfolio-hard generation shortfall, MWIS bridge-check (WARNING).** 8/12 R2 portfolio-hard cells unproducible. Root-cause: `mwis_hard.py` bridge-check pre-flight is deterministic; the same seed always fails. Severity: warning — caps portfolio-hard coverage at the deterministic-feasible seed positions.

4. **W5 budget-guardrail coverage hole (WARNING).** 3 hard rows have only GPT data because Gemini + Sonnet were guardrail-skipped after a single slow row-1. Root-cause: per-row wall-time guardrail uses observed-row-1-time × remaining-rows extrapolation, which over-penalises models with high variance. Severity: warning — fixable by switching to a per-row budget instead of a per-worker rolling extrapolation.

5. **Cross-worker seed drift (NUISANCE).** W7 ate 2 seeds from W8's partition range. Root-cause: seed-fallback (3→4→5→6→7) per worker has no upper bound that respects neighbour partitions. Severity: nuisance — caught by the reviewer's dedup, but design-fragile at higher fan-out.

6. **Late-runner divergence requires manual reconciliation (NUISANCE).** Mary/Rex W1 produced two valid artifact sets; the reviewer manually accepted Rex's strictly-better one. No automated rule. Severity: nuisance — cheap fix is `later_wins_iff_score_gte AND parse_path_at_least_as_strict`.

---

## Suggested Next Experiments (ordered by impact)

1. **Trace one portfolio-medium row end-to-end and isolate the joint-feasibility failure mode.** Pick `portfolio_medium_seed14` (concerns.md confirms all three models parsed cleanly and all three returned `feasible=False`). Read each model's full transcript, identify which sub-component's artifact violates which schema rule. Then tighten the portfolio prompt's per-component CONTRACT block — likely an explicit per-class JSON template inline, not "produce an answer for each of TSP / VE / graphcol". Dominant overnight signal; biggest leverage. **Tied to: finding 1, bug 1.**

2. **Patch the MWIS-hard bridge-check or exclude MWIS from portfolio-hard.** Two surgical options: (a) detect the deterministic bridge-check failure pre-flight and lower `n_nodes` (n=100 worked for some seeds where the default failed); (b) add a `class_exclude` flag for portfolio-hard so the seed lottery skips MWIS. Option (b) is one-line; option (a) needs ~30 min of generator work. Either unblocks the next ~8 portfolio-hard slots. **Tied to: finding 7, bug 3.**

3. **Diagnose Sonnet's MWIS/VE-hard stop=error.** Read 2–3 raw transcripts (`results/full/mwis_hard_seed{5,9,13}/claude-sonnet-4.6.json`) and check: was max-tokens hit, was an unparseable mid-turn token emitted, was the BEST_GUESS schema violated? Juan's prior max_tokens fix raised Sonnet R1 scores generally but did not save MWIS hard — there is a residual model-specific failure to characterise. **Tied to: finding 2, bug 2.**

4. **Score-quality scorecard for GPT-5.4-mini on graph problems.** GPT parses 100 % but produces low-quality solutions on graphcol-hard and steiner-hard. Build a per-class score table (gold gap, baseline-relative score, wall time) for GPT-only across all 64 probes; if the pattern is "GPT submits the first feasible solution and stops" then this is a stop-policy issue, not a capability issue, and is fixable via a per-class prompt nudge. Cheap diagnostic. **Tied to: finding 3.**

5. **Ship Kaggle v2 with current solo-hard data; defer portfolio rows to a v3 once bug 1 is resolved.** 206 rows is plenty of solo-hard signal for a meaningful leaderboard, GPT vs Gemini vs Sonnet differentiate cleanly on the solo cells. Gating v2 on portfolio-fix risks missing the deadline window for no leaderboard gain. **Tied to: dataset state in OVERNIGHT-RESULTS.**

---

## Methodology Notes

- Source documents: `OVERNIGHT-RESULTS.md` (consolidator's wake-up brief), `round1-review.md` (Tao), `round2-review.md` (Ayu_1), and per-row `concerns.md` files spot-checked across cjs/steiner/graphcol/tsp/mwis/ve and 2 portfolio rows.
- Per-class feasibility numbers are aggregated from R1 + R2 review tables; minor count discrepancies exist between the round-level tables and the OVERNIGHT-RESULTS summary (e.g., portfolio probe counts reported as 12 vs 16) — I trust the OVERNIGHT-RESULTS aggregations as the consolidator's final view but note that per-cell breakdowns are R1 + R2 sums.
- All findings cross-checked against at least one concrete `concerns.md` artifact.
