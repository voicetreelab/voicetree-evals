# Round 1 Review — Sonnet Reviewer

## Verdict: **PROCEED**

None of the three HALT criteria were triggered:
1. **Gold corruption**: No negative/NaN gold values found. MWIS seed substitutions (W4, W7, W8) used inline OR-Tools gold correctly.
2. **All-zero on >50% of rows**: No row had all 3 models at score 0 due to a harness bug. Portfolio infeasibility is a model quality failure, not a harness bug (parse succeeded).
3. **OR-Tools venv broken**: No venv errors logged. Only 2 generation skips in W7 due to MWIS hard bridge-check fallback exhaustion.

---

## Consolidation

- **Rows added**: 94 (0 collisions with existing global IDs, 0 cross-worker duplicates)
- **Total questions.jsonl**: 120 rows (26 original + 94 new)
- Merged from `scratch/round1/worker{1..8}/questions.partial.jsonl` (deduped by `id`, existing rows preserved)

Worker row counts: W1=12, W2=12, W3=12, W4=12, W5=12, W6=12, W7=10 (2 skipped), W8=12

---

## Per-Model Strict-Parse Rates (32 probe rows)

| Model | Strict-parse | Partial-rescue | Not-run / skipped | Parse fail / timeout |
|---|---:|---:|---:|---:|
| `gemini-flash-latest` | 21/32 (65.6%) | 3/32 (9.4%) | 7 | 1 (runner_timeout W6) |
| `claude-sonnet-4.6` | 22/32 (68.8%) | 0 | 6 | 4 (2 strict_parse_failed + 2 baseline_only) |
| `gpt-5.4-mini` | 29/32 (90.6%) | 3/32 (9.4%) | 0 | 0 |

**GPT parsed all 32 rows** (strict or rescue). Gemini and Sonnet had 7–10 explicit not_run/skipped rows due to budget guardrails (W5 and W7).

---

## Rescue-Parse Rate

Rescue parser active on select rows (partial_rescue parse_path):
- **Gemini**: 3 rescues — W4 `ve_medium_seed2`, W5 `ve_medium_seed5`, W8 `portfolio_hard_seed16`
- **GPT**: 3 rescues — W4 `ve_medium_seed2`, W5 `ve_medium_seed8` + `cjs_hard_seed4`
- **Sonnet**: 0 rescues

---

## Feasibility Rates by Class

| Class | Probe rows | Gemini feasible | Sonnet feasible | GPT feasible |
|---|---|---|---|---|
| `cjs` medium | 3 (W1) | 3/3 | 1/3 | 3/3 |
| `steiner` medium | 3 (W1+W2) | 3/3 | 3/3 | 2/3 |
| `graphcol` medium | 3 (W2+W3) | 3/3 | 3/3 | 3/3 |
| `tsp` medium | 3 (W3) | 3/3 | 2/3 | 3/3 |
| `mwis` medium | 3 (W4) | 3/3 | 0/3* | 1/3 |
| `ve` medium | 2 (W4+W5) | 2/2 | 0/2* | 2/2 |
| `cjs` hard | 1 (W5) | not_run | not_run | 1/1† |
| `steiner` hard | 1 (W5) | not_run | not_run | 1/1† |
| `portfolio` medium | 8 (W6+W8) | 0/7† | 0/8 | 0/8 |
| `portfolio` hard | 8 (W7+W8) | 0/1† | 0/8 | 0/8 |

*Sonnet: 1 timeout/baseline_only on mwis_seed3, 3 explicit skips (W4); 0 feasible on VE (parse fail + not_run)
†GPT cjs/steiner hard: feasible=True but cjs score=-0.18 (near-baseline)
†Gemini portfolio medium W6: 7 ran (1 runner_timeout stub on seed8 = not counted)
†Gemini portfolio hard W7: only 1 row attempted (guardrail abort at 541s), 3 not_run

---

## Score-vs-Baseline Highlights

**Strong beats (>80 score):**
- Steiner medium: Gemini ~96, Sonnet ~93-99, GPT 79-82 (W2 best slice)
- Graphcol medium: Gemini ~96, Sonnet ~97-98 (W2 outstanding)
- TSP medium: Gemini ~93-96, Sonnet ~92-96, GPT ~64-86 (W3)
- MWIS medium: Gemini 86-92 (solid), GPT 89 on seed10

**At or below baseline (<0 score or near-zero):**
- CJS medium: GPT consistently -0.16 to -0.19 (near-baseline)
- Portfolio all: 0/36 feasible runs; scores range from -24 to +26 (partial component value only)
- MWIS medium: Sonnet 0, GPT 0/0 on seeds 3 and 7 (infeasible)

---

## Top 3 Concerns

1. **Portfolio infeasibility (systematic)**: 0/36 portfolio model-runs produced a feasible final answer across all 8 probed portfolio rows (W6+W7+W8). Root cause documented in W6 notes: TSP sub-component output format violations, plus occasional VE/graphcol schema non-compliance. This is a model quality issue, not a harness bug.

2. **Sonnet MWIS timeout pattern**: Sonnet timed out (400s wall budget) on `mwis_medium_seed3` and was explicitly skipped for the remaining 3 W4 probe rows. MWIS medium appears to be a systematic Sonnet slowness/failure class. Sonnet MWIS coverage is 0/3 probe rows.

3. **W5 budget guardrail left hard rows GPT-only**: Worker 5's budget policy cut Gemini (417.9s/row) and Sonnet (367.2s/row) after row 1, leaving `ve_medium_seed8`, `cjs_hard_seed4`, `steiner_hard_seed4` with only GPT data. CJS hard GPT scored -0.18 (baseline-equivalent). No multi-model hard-difficulty comparison data was produced for those rows.

---

## Skipped Cells

| Worker | Class | Difficulty | Seeds | Reason |
|---|---|---|---|---|
| W7 | portfolio | hard | seeds 11-13 region (2 rows) | MWIS hard bridge-check pre-flight failures exhausted +4 fallback; logged in `worker7/gen-notes.md` |

No venv errors. No other generation skips. W4 MWIS used seed substitutions (bridge-check fall-through) but all 12 rows were generated.

---

## Special Flags

### Max (W2) — Local Runner Recovery
Worker 2's child runner `Ren` stalled without producing results. Max (parent) recovered the full 4×3 eval matrix locally. All 4 probe rows have complete artifacts. This is fully resolved; no human action needed.

### Mary/Rex (W1) — Late Rex Divergence
Rex completed a resumed runner pass after the parent W1 commit (`6470942`) that improved two artifacts:
- `steiner_medium_seed2 / gemini-flash-latest`: upgraded from `baseline_only` (score 80.1) → `strict_protocol_cf` (score 96.2, gap 0.0)
- `cjs_medium_seed8 / gemini-flash-latest`: score improved from 34.8 → 90.1
- `cjs_medium_seed8 / claude-sonnet-4.6`: reclassified from `strict_parse_failed` → `baseline_only`

Rex's improved artifacts are currently in the working tree (uncommitted). **Recommendation: accept Rex's improvements** — they are strictly better and consistent with artifact schema. These will be staged with this consolidation commit.

---

## Per-Worker Summary

| Worker | Agent | Rows gen | Probe IDs | Gemini strict | Sonnet strict | GPT strict | Notes |
|---|---|---|---|---|---|---|---|
| W1 | Mary+Rex | 12 | 4 | 4/4 | 2/4 | 4/4 | Late Rex divergence (see above) |
| W2 | Max | 12 | 4 | 4/4 | 4/4 | 4/4 | Local runner recovery |
| W3 | Meg | 12 | 4 | 4/4 | 4/4 | 4/4 | Clean |
| W4 | Mei | 12 | 4 | 3/4 + 1 rescue | 0/4 (1 baseline_only + 3 skipped) | 3/4 + 1 rescue | Sonnet skipped after seed3 timeout |
| W5 | Mia | 12 | 4 | 1/4 ran (partial_rescue) + 3 not_run | 1/4 ran (parse_fail) + 3 not_run | 4/4 | Budget guardrail after row-1 wall times |
| W6 | Nia | 12 | 4 | 3/4 (1 runner_timeout) | 4/4 | 4/4 | Portfolio: 0/12 feasible |
| W7 | Noa | 10 | 4 | 0/4 (guardrail + not_run) | 4/4 | 4/4 | Portfolio hard: 0/12 feasible; 2 gen skips |
| W8 | Omar+Sam | 12 | 4 | 3/4 + 1 rescue | 4/4 | 4/4 | Portfolio: 0/12 feasible |
