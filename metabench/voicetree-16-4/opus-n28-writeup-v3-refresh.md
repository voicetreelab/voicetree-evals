---
color: green
isContextNode: false
agent_name: Iris
---
# Fresh Opus N=28 refresh: writeup-v3 patched (7 cells)

Opus N=14→N=28: M2-BSS +0.05→+0.18 (monitoring strengthens), feas 93%→82% (crosses <85% threshold), M4-MAE 1.20→1.82 (+52%). Three Ian-thresholds fired → patched. 7 edits landed, word count holds at 1424/1500. Verdict direction unchanged: anthropic-monitoring CONFIRMED.

# Fresh Opus N=28 refresh — writeup-v3 patched

## Diff table: N=14 snapshot (in writeup) vs N=28 (fresh run)

Re-ran `python3 kaggle_submission/scripts/analyze_metacog.py` (344 model-row records, up from ~192). Extracted §3 family-consistency row for `claude-opus-4.6`.

| metric | N=14 (writeup) | N=28 (fresh) | Δ | trigger fired? |
|---|---:|---:|---:|:---:|
| M1 BSS | −0.06 | **−0.01** | +0.05 | no (borderline) |
| M2 BSS | +0.05 | **+0.18** | **+0.13** | YES (>0.10) |
| M2 resolution | 0.05 | 0.07 | +0.02 | no |
| M4 MAE | 1.20 | **1.82** | **+52%** | YES (>30%) |
| Feasibility | 93% | **82%** | −11pp | YES (<85%) |

## Decision: PATCH

Three of Ian's thresholds crossed. Direction is mixed:
- M2-BSS shifts favourably (monitoring axis STRENGTHENS: +0.05 → +0.18). Sonnet+Opus now both clearly positive; anthropic-monitoring CONFIRMED verdict holds and is more robust.
- Feasibility + M4-MAE shift unfavourably (execution story weakens slightly: 93%→82%, MAE 1.20→1.82). The "Opus patches Sonnet" narrative survives — 32%→82% is still a +50pp jump — just less dramatic than the N=14 snapshot.

Verdict direction unchanged. Patch is a numeric refresh, not a reframe.

## Source row from fresh §3 table

```
| anthropic | small    | claude-sonnet-4.6 | 68 | 0.187 | +0.194 | 0.090 | 0.098 | +0.528 | 0.123 | 1.85 | 32% |
| anthropic | frontier | claude-opus-4.6   | 28 | 0.241 | -0.014 | 0.023 | 0.202 | +0.182 | 0.066 | 1.82 | 82% |
```

Sonnet row unchanged vs. N=14 writeup (table cites 33% feas; fresh says 32% — rounding, left alone).

Other frontier rows (Gemini-3-Pro N=56, GPT-5.4 N=56) unchanged from N=23/N=18 snapshot — writeup cells for those families not touched.

## Edits landed (7 cells, 1 file)

File: `kaggle_submission/writeup-v3.md`

Table (6-model sweep, lines 47–51):
- M1 BSS anthropic frontier: `−0.06` → `−0.01`
- M2 BSS anthropic frontier: `+0.05` → `+0.18`
- M2 resolution anthropic frontier: `0.05` → `0.07`
- M4 MAE anthropic frontier: `1.20` → `1.82`
- Feasibility anthropic frontier: `93%` → `82%`

Family-consistency verdict prose (line 59):
- `(+0.53 / +0.05)` → `(+0.53 / +0.18)`
- `~1.2–1.9` → `~1.8`
- `33% → 93% feasibility` → `33% → 82% feasibility`

## Judge ask #2 — plain-English BSS gloss

Not added. Line 53 already contains a plain-English gloss: *"Negative BSS = the model's confidence is strictly worse than ignoring it and quoting the class base rate (e.g., Gemini Flash's M1 BSS of −0.79 means the model is actively deceiving itself compared to just guessing the average)."* Adding another gloss would be redundant and risk the 1500-word cap.

## Budget

```
Before: 1424 words
After:  1424 words
Limit:  1500 words
```

No commit per task spec — changes staged only.

## Handoff to caller

**RE-RUN GEMINI JUDGE.** Patched numbers strengthen the monitoring verdict (+0.13 M2-BSS) while softening the execution story (feas 93%→82%). Net impact on judge score is ambiguous — the judge's 96.5 praised the family-consistency claim, which now rests on firmer M2 ground but slightly weaker feasibility. Prior scoring was at N=14 Opus; the N=28 patch is material enough to re-score.

## PREDICTION CLAIMS

1. **Judge will keep anthropic-monitoring CONFIRMED verdict** — M2-BSS direction preserved and strengthened. Confidence 0.85.
2. **Judge score stays within ±1.5 of 96.5** — prose-level reframe is zero; numbers moved but verdict text remains tight. Confidence 0.60.
3. **Feasibility drop (93→82) does NOT trigger a new criticism** — the 'Opus patches Sonnet' claim still holds at 32%→82% (+50pp). Confidence 0.70.
4. **If judge flags anything new, it will be M4-MAE parity (1.85 vs 1.82)** — used to read as Opus improving on Sonnet's MAE; now they're identical, which muddies the 'frontier monitoring improvement' sub-claim. Confidence 0.45.

## DIFF

```
--- table (lines 47-51) ---
- | M1 BSS ↑ | +0.19 · −0.06 | −0.79 · — | −0.35 · +0.14 |
- | M2 BSS ↑ | **+0.53** · **+0.05** | −0.44 · **+0.50** | −2.14 · −3.17 |
- | M2 resolution ↑ | 0.12 · 0.05 | 0.03 · **0.11** | 0.00 · 0.01 |
- | M4 MAE ↓ | **1.85** · **1.20** | 5.94 · **0.35** | 2.08 · 7.99 |
- | Feasibility ↑ | 33% · **93%** | 49% · **100%** | 54% · **86%** |
+ | M1 BSS ↑ | +0.19 · −0.01 | −0.79 · — | −0.35 · +0.14 |
+ | M2 BSS ↑ | **+0.53** · **+0.18** | −0.44 · **+0.50** | −2.14 · −3.17 |
+ | M2 resolution ↑ | 0.12 · 0.07 | 0.03 · **0.11** | 0.00 · 0.01 |
+ | M4 MAE ↓ | **1.85** · **1.82** | 5.94 · **0.35** | 2.08 · 7.99 |
+ | Feasibility ↑ | 33% · **82%** | 49% · **100%** | 54% · **86%** |

--- verdict prose (line 59) ---
- **Anthropic — monitoring axis CONFIRMED.** Both Sonnet and Opus post positive M2 BSS (+0.53 / +0.05) and low M4 MAE (~1.2–1.9); Opus *patches* Sonnet's execution collapse (33% → 93% feasibility) while preserving its monitoring advantage.
+ **Anthropic — monitoring axis CONFIRMED.** Both Sonnet and Opus post positive M2 BSS (+0.53 / +0.18) and low M4 MAE (~1.8); Opus *patches* Sonnet's execution collapse (33% → 82% feasibility) while preserving its monitoring advantage.
```

## Complexity: low

7 numeric edits in 2 adjacent regions of one markdown file. No logic/code touched. Risk is entirely in the narrative coherence check, which I verified by re-reading the verdict prose end-to-end.

## Files Changed

- kaggle_submission/writeup-v3.md

### NOTES

- Opus N=28 is mid-sweep (56/2=28, so exactly half the cells complete). If sweep continues overnight to N=56, expect another refresh and possibly further feasibility movement.
- Sonnet feas in fresh table is 32% vs. writeup's 33% — rounding difference, left alone to avoid churn.
- M1 BSS Opus moved from −0.06 to −0.01 — essentially 0 now (no monitoring signal at subtask-solvability level, consistent with small subtask n=? sample). Not load-bearing; writeup doesn't cite this number in prose.
- Did NOT add judge ask #2 (plain-English BSS gloss) — line 53 already contains one.

[[task_1776383046038ror]]
