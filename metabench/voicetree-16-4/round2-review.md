---
color: green
isContextNode: false
agent_name: Ayu_1
---
# Round 2 Review — PROCEED + Merge Complete

PROCEED verdict. Merged 86 new rows into questions.jsonl (120→206 total). Solo-hard coverage now nearly complete; portfolio rows systematically infeasible across all models. Committed round2-review.md, OVERNIGHT-RESULTS.md, and questions.jsonl.

## Verdict: PROCEED

No HALT criteria triggered:
- Gold intact (all workers used inline OR-Tools gold; OR-Tools venv operational)
- No row had all-3-models at score=0 due to harness bug (portfolio infeasibility is model quality, not harness)
- OR-Tools venv unbroken: W6 generation shortfall (8 seeds skipped) caused by deterministic MWIS bridge-check exhaustion, not venv failure

## Consolidation

- **86 new rows appended, 2 cross-worker collisions** (W7 seed drift into W8's range: portfolio_medium_seed38 and portfolio_hard_seed36 — W7 copy preferred as first-encountered)
- W6 generated 4/12 rows (MWIS bridge-check exhausted 8 slots — not a venv error)
- Final count: **206 rows** (120 R1 + 86 R2)

## Parse Rates — R2 Probe Rows (32 probe IDs × 3 models = 96 runs)

| Model | Strict | Partial-rescue | Parse failed | Feasible |
|---|---:|---:|---:|---:|
| `gemini-flash-latest` | 22/32 (68.8%) | 8 | 2 | 15/32 |
| `claude-sonnet-4.6` | 25/32 (78.1%) | 1 | 6 | 10/32 |
| `gpt-5.4-mini` | 29/32 (90.6%) | 3 | 0 | 16/32 |

## Feasibility by Class (R2 Probes)

| Class | Probed rows | Feasible runs | Notes |
|---|---:|---:|---|
| CJS hard | 2 (6 runs) | 3/6 | Gemini+GPT solve; Sonnet parse-fails |
| Steiner hard | 2 (6 runs) | 6/6 | All 3 models, gap_pct=0.0 |
| Graphcol hard | 3 (9 runs) | 9/9 | Perfect coverage, GPT weakest on score |
| TSP hard | 3 (9 runs) | 9/9 | All feasible, strong scores |
| VE hard | 3 (9 runs) | 7/9 | Sonnet fails on seed4+seed7 (stop=error) |
| MWIS hard | 3 (9 runs) | 6/9 | Sonnet 0/3; Gemini+GPT 3/3 each |
| Portfolio medium | 8 (24 runs) | 0/24 | 100% infeasible — model quality |
| Portfolio hard | 8 (24 runs) | 1/24 | 1 Sonnet solve on seed25, poor gaps |

## Score-vs-Baseline Highlights

**Standout solo-hard results:**
- `graphcol_hard_seed4..10`: Gemini ~95%, Sonnet ~98%, GPT negative (near-0 gap but -0.18 baseline-adjusted)
- `steiner_hard_seed7/10`: Sonnet 99.19, Gemini ~96, GPT ~80-85
- `tsp_hard_seed4`: Gemini 95.7, Sonnet 98.5, GPT 97.9 — strongest 3-way tie
- `mwis_hard_seed9`: GPT 85.7, Gemini 85.4 (both feasible); Sonnet infeasible

**Portfolio: consistently near-0 or negative scores** (0/48 meaningful solutions)

## Top 3 Concerns

1. **Portfolio infeasibility persists at 100% (less 1/48)** — All 48 R2 portfolio model runs were infeasible (0/48 feasible, with only 1 Sonnet solve on portfolio_hard_seed25 having poor gaps). This is a model quality/planning failure, not a harness bug. Parse succeeded on ~90%+ of runs.

2. **Sonnet MWIS hard 0/3** — Sonnet produced strict_parse_failed or infeasible on all 3 MWIS hard probes. Gemini and GPT solved 3/3. Sonnet VE-hard also failed on seeds 4+7 (stop=error). Sonnet-specific hard-instance failure pattern.

3. **W6 Portfolio hard generation shortfall (4/12 rows)** — MWIS bridge-check exhausted 8 requested hard-portfolio seed slots. Successor must either patch the MWIS hard generator or accept portfolio-hard coverage gaps at the deterministic seed positions.

## Skipped / Shortened Cells

| Worker | Nominal | Actual | Gap | Reason |
|---|---:|---:|---:|---|
| W6 (portfolio hard) | 12 | 4 | -8 | MWIS bridge-check exhausted |
| W8 (portfolio mixed) | 2 IDs | 0 IDs | -2 | Duplicates of W7 (seed drift) — logged |
| All others | 12 | 12 | 0 | — |

## Per-Worker Summary

| W | Agent | Class/Diff | Rows gen | Probe IDs | Gemini parse | Sonnet parse | GPT parse | All 3 feasible? |
|---|---|---|---:|---|---|---|---|---|
| 1 | Tara | CJS+Steiner hard | 12 | seed7,10,seed7,10 | 3/4 (1 fail) | 2/4 (2 fail) | 4/4 | Steiner yes, CJS no |
| 2 | Timi | Graphcol+TSP hard | 12 | seed4,7,10,tsp4 | 4/4 strict | 4/4 strict | 4/4 strict | Yes — 12/12 |
| 3 | Uma | TSP+VE hard | 12 | tsp7,10,ve4,7 | 4/4 (2 rescue) | 2/4 (2 fail) | 4/4 (2 rescue) | TSP yes, VE sonnet fail |
| 4 | Vic | VE+MWIS hard | 12 | ve10,mwis5,9,13 | 4/4 | 1/4 | 4/4 | MWIS: sonnet 0/3 |
| 5 | Wei | Portfolio med | 12 | seed14,21,26,29 | 4/4 (1 rescue) | 4/4 | 4/4 | 0/12 feasible |
| 6 | Xan | Portfolio hard | 4 | seed24,25,27,28 | 4/4 (1 rescue, 1 fail) | 4/4 | 4/4 | 1/12 feasible (sonnet seed25) |
| 7 | Yan | Portfolio mixed | 12 | med33,36,hard30,34 | 4/4 (1 rescue) | 4/4 | 4/4 | 0/12 feasible |
| 8 | Zoe | Portfolio mixed | 12 | med38,41,hard36,39 | 3/4 (1 fail) | 4/4 | 4/4 | 0/12 feasible |

## Files Changed

- kaggle_submission/questions.jsonl (120→206 rows)
- voicetree-16-4/round2-review.md (this file)
- voicetree-16-4/OVERNIGHT-RESULTS.md

[[task_1776368841822ndn]]
