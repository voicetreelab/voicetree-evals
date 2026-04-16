---
color: green
isContextNode: false
agent_name: Luis
---
# TSP spike partial results: research assessment + arm-design critique

Research assessment of 9 committed (model, arm, seed) rows from the local TSP-25 budget-metagame spike. Key findings: gemini-3.1-pro achieves near-optimal solutions (0.24% gap) but with catastrophically wrong calibration (Brier=9953, declared gap=100%). Multi-arm prompting has zero effect on gemini-3.1 (identical solutions across all arms). Design critique: multi-arm prompting may be unnecessary complexity if the true goal is simply comparing realized $score across models.

## Data source

All rows from four active campaign files as of 2026-04-16:
- `results/spike_20260416_full_3x3x3.jsonl`
- `results/spike_20260416_pro_seeds23.jsonl`
- `results/spike_20260416_flash_3x3.jsonl`
- `results/spike_20260416_gemini31_3x3.jsonl`

---

## Complete per-row table (9 rows)

| model | arm | seed | gap_pct | score | brier | wall_s | turns | stop_reason |
|---|---|---:|---:|---:|---:|---:|---:|---|
| gemini-2.5-flash | greedy | 1 | 22.4% | 76.81 | 57.98 | 80s | 2 | subtask_parse_fail |
| gemini-2.5-flash | exhaustive | 1 | 14.0% | 81.70 | 257.14 | 434s | 2 | subtask_stop |
| gemini-2.5-pro | greedy | 1 | 13.5% | 85.94 | 978.84 | 55s | 2 | subtask_stop |
| gemini-2.5-pro | greedy | 2 | 11.9% | 86.87 | 2.98 | 121s | 2 | subtask_stop |
| gemini-2.5-pro | exhaustive | 1 | 11.3% | 82.05 | 822.81 | 663s | 6 | subtask_stop |
| gemini-2.5-pro | smart | 1 | 4.4% | 92.62 | 2435.24 | 302s | 4 | subtask_stop |
| gemini-3.1-pro-preview | greedy | 1 | 0.24% | 97.39 | 9953.03 | 237s | 2 | subtask_stop |
| gemini-3.1-pro-preview | exhaustive | 1 | 0.24% | 97.20 | 9953.03 | 256s | 2 | subtask_stop |
| gemini-3.1-pro-preview | smart | 1 | 0.24% | 97.22 | 9953.03 | 254s | 2 | subtask_stop |

*Brier = (declared_gap − actual_gap_pct)² — lower = better calibrated. turn1_died=0, killed=0, revised_best_guess_downward=0 for all rows.*

---

## Aggregated by model × arm

| model | arm | n | mean_gap_pct | mean_score | mean_brier | mean_wall_s |
|---|---|---:|---:|---:|---:|---:|
| gemini-2.5-flash | exhaustive | 1 | 14.0% | 81.70 | 257 | 434s |
| gemini-2.5-flash | greedy | 1 | 22.4% | 76.81 | 58 | 80s |
| gemini-2.5-pro | exhaustive | 1 | 11.3% | 82.05 | 823 | 663s |
| gemini-2.5-pro | greedy | 2 | 12.7% | 86.40 | 491 | 88s |
| gemini-2.5-pro | smart | 1 | 4.4% | 92.62 | 2435 | 302s |
| gemini-3.1-pro-preview | all 3 arms | 3 | 0.24% | 97.27 | 9953 | 249s |

---

## Gap-to-optimal chart (lower = better)

```
Gap to optimal (%) — each █ ≈ 2ppt

gemini-3.1 greedy    ▏ 0.2%
gemini-3.1 exhaustive▏ 0.2%
gemini-3.1 smart     ▏ 0.2%
gemini-2.5-pro smart ██ 4.4%
gemini-2.5-pro exh   █████ 11.3%
gemini-2.5-pro grdy* ██████ 12.7% (avg 2 seeds)
gemini-2.5-flash exh ███████ 14.0%
gemini-2.5-flash grd ███████████ 22.4%
                     |----5----|----10----|----15----|----20----|--25
```

## Objective $score chart (higher = better)

```
Objective $score — each █ ≈ 2 units, scaled from 60

gemini-3.1 greedy    ████████████████████ 97.4
gemini-3.1 smart     ████████████████████ 97.2
gemini-3.1 exhaustive████████████████████ 97.2
gemini-2.5-pro smart ██████████████████  92.6
gemini-2.5-pro grdy* █████████████████   86.4
gemini-2.5-pro exh   ████████████████    82.1
gemini-2.5-flash exh ████████████████    81.7
gemini-2.5-flash grd ███████████████     76.8
                      60----70----80----90----100
```

---

## Interpretation

### 1. Accuracy and raw optimization

Model ranking on gap-to-optimal is clear and consistent:
- **gemini-3.1-pro**: 0.24% gap — essentially solved TSP-25 to near-optimality in every run
- **gemini-2.5-pro**: 4–13% gap range depending on arm and seed
- **gemini-2.5-flash**: 14–22% gap range

The spread is large enough to be benchmark-useful for 2.5-gen models. For gemini-3.1, TSP-25 is too easy — the ceiling effect renders arms and seeds irrelevant.

### 2. Arm invariance in gemini-3.1 (critical anomaly)

All three arms for gemini-3.1 produce **byte-identical final solutions** (final_length=506.724487, gap_pct=0.235107, brier=9953). The model achieved near-optimal TSP in a 2-turn sequence (plan → exec → stop) regardless of whether it was told to be greedy, exhaustive, or metacognitively smart. The arm prompts have zero observable effect. This is either:
- The model's TSP-solving capability saturates the problem class (most likely for a near-optimal result)
- The system prompt variants are too subtle to overcome the model's prior strategy

Consequence: the arm structure is providing no information for the strongest model.

### 3. Calibration (Brier) — a noisy but revealing signal

Brier = (declared_gap − realized_gap)². All rows over-declared their gap (models underestimated their own capability).

| model | arm | declared_gap | actual_gap | over-estimate |
|---|---|---:|---:|---:|
| gemini-3.1 | all | 100.0% | 0.24% | +99.8pp |
| gemini-2.5-pro | smart | 53.7% | 4.4% | +49.3pp |
| gemini-2.5-pro | greedy s1 | 44.8% | 13.5% | +31.3pp |
| gemini-2.5-pro | greedy s2 | 13.7% | 11.9% | +1.7pp |
| gemini-2.5-flash | exhaustive | 30.0% | 14.0% | +16.0pp |

**gemini-3.1 calibration failure is structurally important**: the model achieves near-perfect TSP solutions but declares maximum uncertainty (gap=100%). This is metacognitive failure in the literal sense — the model does not know what it knows. However, it may also be a prompt-level artifact: the model might be interpreting the declared_gap field as a worst-case bound rather than a calibrated estimate.

**gemini-2.5-pro seed2 is the sole well-calibrated row** (declared 13.7%, actual 11.9%, Brier=3). But this is one seed; the same arm at seed1 had Brier=979. Calibration is too noisy at n=1 to be interpretable.

### 4. Stop behavior — no metacog signals fired

Zero rows with: turn1_died, subtask_killed, revised_best_guess_downward. The protocol's metacog-forcing conditions (budget pressure triggering early stop or downward revision) have not been observed yet. This may be because:
- 9 rows is too few, and the remaining 18 seeds will show more variation
- The 30-min total budget is large enough that no model felt genuine time pressure
- The declared_gap field is the only live calibration signal and it's already shown to be noisy

### 5. Turn count and economic efficiency

| arm | model | turns | wall_s | score |
|---|---:|---:|---:|---:|
| greedy | 2.5-pro | 2 | 55–121s | 86.4 |
| exhaustive | 2.5-pro | 6 | 663s | 82.1 |
| smart | 2.5-pro | 4 | 302s | 92.6 |
| any | 3.1-pro | 2 | ~250s | 97.3 |

The exhaustive arm uses 5× more time than greedy but scores *lower* for 2.5-pro. The smart arm is both faster than exhaustive and 10+ points higher. This is not a contradiction — it may reflect that the exhaustive prompt encourages inefficient iterative search while smart prompts encourage targeted improvement.

---

## Design critique: are multi-arm prompts necessary?

**The critique:** If the benchmark goal is simply *"how well does each model optimize the economic objective?"*, then the right experimental design is a single arm with the objective function stated plainly: *"You will be scored on accuracy - token_cost; maximize your $score."* Comparing realized $scores across models gives a clean capability ranking without the confound of arm-specific prompt engineering.

The three-arm split (greedy/exhaustive/smart) was motivated by wanting to measure whether models respond to different metacognitive framing. But the current data suggests:
1. **For strong models (gemini-3.1)**: arm makes no difference — capability dominates framing
2. **For weaker models (2.5-pro/flash)**: the smart arm outperforms, but this could be because it injects implicit algorithmic hints, not because it elicits better metacognition

**Verdict:** The arm split is currently more of an ablation study on prompt engineering than a metacognition benchmark. It adds complexity (3× more runs, harder to interpret) without proportional signal.

**Design recommendation:** For the Kaggle submission, prefer a **single-arm design** where the economic objective is stated directly and models are compared on realized $score. Retain the arm split only as an optional ablation appendix, not as the primary benchmark structure. This also avoids the arms-confound problem in model comparisons: with multi-arm data, it's ambiguous whether model X > model Y because of capability or because arm assignment interacted with model priors.

If arm variants are retained, they should be: (a) run at higher n to distinguish arm effects from seed noise, and (b) pre-registered with a specific hypothesis (e.g., *"smart arm will improve 2.5-pro score by ≥5 points"*) to avoid HARKing.

---

## What these numbers imply about metacognition vs raw optimization

| signal | finding | metacog implication |
|---|---|---|
| gap-to-optimal | 3.1-pro near-perfect, clear model hierarchy | raw optimization; TSP-25 too easy for 3.1-pro |
| Brier (calibration) | all models over-declared gap; 3.1-pro most extreme | models don't know what they know; especially bad for strongest model |
| arm invariance (3.1-pro) | identical solutions regardless of framing | capability saturates problem; arm design not stress-testing metacog for this model |
| turn count | exhaustive uses 6 turns, scores worse than 2-turn greedy | more compute doesn't help; models not stopping optimally |
| stop/kill signals | zero triggered | budget pressure not yet reaching metacog threshold in current runs |

**Core tension:** The benchmark is designed to measure whether models make rational stop/continue decisions. But all current rows stop naturally (subtask_stop), no one is getting killed or making downward revisions. The metacog signal the benchmark was designed to surface has not appeared in 9 rows. This may change with more seeds and models — or it may indicate the budget parameters need tightening.

---

## Caveats

- **n=9 is very small**: all arm×model cells have n=1 except pro/greedy (n=2). No statistical claims are supported.
- Background runs for seeds 2/3 on flash and gemini-3.1 are still in progress; this assessment will need to be updated.
- The gemini-3.1 declared_gap=100% pattern may be a prompt artifact (models treating declared_gap as a worst-case bound) rather than a true calibration failure — needs investigation.
- All runs used seed=1 for the same TSP-25 instance (coordinates), so model × arm comparisons are within-instance, not across instances.

### NOTES

- PARTIAL DATA: 9 rows out of a planned 27 (3 models × 3 arms × 3 seeds). Background runs for seeds 2/3 on flash and gemini-3.1 are still active. All conclusions are provisional.
- gemini-3.1 identical-solution anomaly: all three arms produce final_length=506.724487... to 6 decimal places, same gap_pct=0.235107, same brier=9953. The arm prompts have zero observable effect on this model.
- Brier calibration is extremely noisy at n=1: same pro/greedy/seed1 vs seed2 gives Brier 979 vs 3. Don't over-interpret single-seed calibration numbers.
- One protocol failure: flash greedy seed1 emitted DECISION:continue but omitted NEXT_SUB, triggering subtask_parse_fail. The model stopped at baseline tour (gap=22.4%) rather than its declared gap target.
- The exhaustive arm is both the slowest (663s for 2.5-pro) AND lower-scoring than smart (82 vs 93) and sometimes greedy (82 vs 86). More turns ≠ better outcomes.

## Related

- [tsp-spike-partial-results-snapshot](tsp-spike-partial-results-snapshot.md)
- [review-kate-tsp-spike-protocol-execution](review-kate-tsp-spike-protocol-execution.md)
- [kaggle-metrics-support-verified](kaggle-metrics-support-verified.md)

[[task_1776319758322uan]]
