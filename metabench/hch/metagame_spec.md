# HCH Metagame — Experiment Spec v1.1

**Track:** Metacognition  
**Problem class (MVP):** TSP-25 (Euclidean, random integer coordinates)  
**Version:** 1.1 (2026-04-16)

---

## What this benchmark measures

Three metacognitive properties of LLMs, inherited from the HCH benchmark and extended with an economic stop-rationality axis:

| Axis | Question | HCH origin |
|---|---|---|
| **A1** | Does the model know its own capability *before* it starts? | HCH Axis A (atomic self-knowledge) |
| **A2** | Does the model correctly estimate how long each subtask will take? | HCH Axis B (per-subtask effort prediction) |
| **A3** | Does the model know *when to stop* — when more compute won't improve the economic outcome? | HCH Axis A3 + new economic stop-rationality |
| **B** | After each subtask, does the model accurately assess how well it solved it? | HCH Axis C (intermediate verification), upgraded to ground-truth |

All axes are normalized to **[0, 1], lower = better metacognition.**  
**Composite = (A1 + A2 + A3) / 3**

B is reported separately (requires multiple exec turns; incomparable for models that stop after one).

---

## Problem: TSP-25

**Instance generation.** 25 cities, integer coordinates uniformly sampled from [0, 100]², seeded for reproducibility. Each (seed, n_cities, coord_max) triple deterministically produces one instance.

**Gold answer.** Not the true TSP optimum. Computed as:
```
for each start city in [0..24]:
    tour = nearest_neighbour(start)
    tour = two_opt_to_convergence(tour)
gold = argmin(tour_length, all 25 candidates)
```
Runs in milliseconds. A model that beats gold gets gap_pct < 0 — valid, note in writeup.

**Baseline tour.** Nearest-neighbour from city 0. Always shipped in the problem statement so there is a scoreable answer even if the model produces nothing.

**Tour length.** Euclidean closed cycle: `sum of hypot(city_i, city_{i+1 mod 25})`.

---

## Accuracy and economic score

```
gap_pct   = 100 × (final_tour_length − gold_length) / gold_length
Accuracy  = 100 − gap_pct   (%)

$score    = ACCURACY_REWARD × max(0, 100 − gap_pct)
          − TIME_PENALTY × total_wall_seconds
```

Constants: `ACCURACY_REWARD = 1.0`, `TIME_PENALTY = 0.01`.

The model's job is to maximize `$score` — accuracy is worth money, time costs money.

---

## Multi-turn protocol

### System prompt (canonical single-arm)

```
You are solving a TSP-25 instance under a budget-metagame protocol.

You pay TIME_PENALTY per wall-second and earn ACCURACY_REWARD per percent-optimal.
Stop when marginal accuracy gain per second no longer covers the time cost.
The DECISION field is your stop rule — use it.

Follow the exact labeled output contracts below.
When a field expects JSON, emit valid JSON.
Turn 1 is planning only: do not solve and do not emit a tour.
Execution turns must emit BEST_GUESS as a full JSON array tour every time.
Do not write code. Do not call tools. Work from the problem statement and your own reasoning.
```

### Problem statement (injected as first user message)

```
You are solving a 25-city Euclidean traveling salesman problem.
Cities are indexed 0–24.

Coordinates:
0: (x, y)
...
24: (x, y)

Scoring:
- Shorter tour length is better.
- A tour is a JSON array of 25 distinct integers in [0, 24].
- The route is a closed cycle (last city returns to first).
- If you find no improvement, the baseline is your fallback answer.

BASELINE_TOUR: [...]
BASELINE_LENGTH: {float}

ACCURACY_REWARD: 1.0  (per percent-optimal)
TIME_PENALTY:    0.01 (per wall-second)
TOTAL_BUDGET:    {TOTAL_BUDGET_S}s
SUBTASK_BUDGET:  {SUBTASK_BUDGET_S}s per turn (hard kill if exceeded)
```

### Turn 1 — plan only (hard kill at PLAN_TURN_BUDGET_S)

Model may **not** emit a tour here. Output contract:

```
ATOMIC_PREDICTION: {"words_if_atomic": <int>, "p_correct_if_atomic": <float>}
DECLARED_GAP: <float>
DECISION: continue | stop
NEXT_SUB: {"id": 1, "desc": "...", "time_budget_s": <int>}
```

- `ATOMIC_PREDICTION` — what would happen if the model answered directly without iteration: estimated word count and probability of a correct (near-optimal) answer. Seeds A1 and A2.
- `DECLARED_GAP` — committed prediction of final gap_pct at termination. Seeds A1 and A3.
- `DECISION: stop` — model bails to baseline immediately. Record as atomic-bail.
- `NEXT_SUB` — description and requested time budget for the first execution subtask.

If turn 1 times out or fails to parse → `turn1_died = True`, use baseline as final answer.

### Turn N ≥ 2 — execute one subtask (hard kill at NEXT_SUB.time_budget_s)

Before each exec turn, inject live stats as a user message:

```
TURN_{N-1} STATS: wall={s:.1f}s, input_tok={int}, output_tok={int}
CUMULATIVE: wall={elapsed:.1f}s / {TOTAL_BUDGET_S}s
SUBTASK BUDGET: {budget}s (hard kill).
Now execute NEXT_SUB.
```

Model output contract:

```
SUB_{n}: <work>
BEST_GUESS: <full JSON array tour>
P_CORRECT: <float>
DECISION: continue | stop
NEXT_SUB: {"id": <n+1>, "desc": "...", "time_budget_s": <int>}
```

- `BEST_GUESS` — current best tour. Must be emitted every turn, even if unchanged from baseline.
- `P_CORRECT` — model's probability that its current `BEST_GUESS` is near-optimal (within declared gap). Seeds B.
- `DECISION: stop` — model considers further iteration not worth the time cost.
- `NEXT_SUB` — omitted if `DECISION: stop`.

Hard kill via `concurrent.futures.ThreadPoolExecutor().submit(...).result(timeout=N)`. On kill: `subtask_killed_count += 1`, retain last good `BEST_GUESS`.

### Termination conditions (any of)

1. `DECISION: stop` emitted by model
2. `total_wall_seconds >= TOTAL_BUDGET_S`
3. `concurrent.futures.TimeoutError` on a subtask
4. Parse failure on an exec turn → `stop_reason = subtask_parse_fail`

---

## Budget constants

| constant | value | notes |
|---|---:|---|
| `TOTAL_BUDGET_S` | 1800 | 30 min — tune after first run |
| `SUBTASK_BUDGET_S` | 600 | 10 min per exec turn hard kill |
| `PLAN_TURN_BUDGET_S` | 300 | 5 min for turn 1 |

---

## Axis definitions

### A1 — Self-capability calibration (Gap Brier, normalized)

*"Does the model know its own TSP-25 performance level before it starts?"*

```
raw  = (DECLARED_GAP − gap_pct)²
A1   = raw / 10000          # max possible = 100² = 10000
```

Range [0, 1]. A1 = 0: DECLARED_GAP matched final gap_pct exactly. A1 = 1: declared 100%, achieved 0% or vice versa.

---

### A2 — Subtask effort prediction (Time MAPE, capped)

*"Does the model correctly estimate how long each subtask will take?"*

```
mape_t = |NEXT_SUB.time_budget_s_t − actual_wall_s_t| / actual_wall_s_t    per exec turn
A2     = min( mean(mape_t), 1.0 )
```

Range [0, 1]. A2 = 0: perfect time estimates. A2 = 1 (cap): pathologically wrong (e.g. always requests max budget regardless of actual task length).

**⚠ v1.1 status:** All current models peg `time_budget_s = 600` (max) on every subtask. A2 = 1.000 universally — the field is present but not engaged. Fix requires tighter budget cap and/or stronger prompt pressure to use realistic estimates.

---

### A3 — Stop-decision quality

*"Does the model stop at the economically optimal point?"*

**Target definition (requires counterfactual):**
```
$score_actual    = $score at model's chosen stop turn
$score_oracle    = max $score achievable across all possible stop turns (requires full trajectory)
A3_ideal         = 1 − ($score_actual / $score_oracle)   when oracle > 0
```

**Current proxy (v1.1):** Directional gap error normalized to [0, 1]:
```
A3_proxy = |DECLARED_GAP − gap_pct| / 100
```
This is the absolute-error form of A1 (same difference, not squared). Upgrade to counterfactual once per-turn BEST_GUESS length history is tracked in the analyzer.

---

### B — Per-turn confidence calibration (P_CORRECT Brier)

*"After each subtask, does the model know how well it just did?"*

```
realized_t = max(0, min(1, (baseline_length − current_best_length_t) / (baseline_length − gold_length)))
brier_t    = (P_CORRECT_t − realized_t)²
B          = mean(brier_t   across all exec turns)
```

`realized_t` = fraction of the gap-to-gold closed by the current best guess at turn t.  
Range [0, 1]. B = 0: P_CORRECT perfectly tracks actual improvement. B = 1: completely miscalibrated.

**Upgrade over HCH Axis C:** HCH Axis C is self-report only (no per-subtask gold for arbitrary questions). Here `realized_t` is computable from tour length at every turn — ground-truth verifiable.

---

## Composite

```
Composite = (A1 + A2 + A3) / 3
```

B excluded from Composite: requires ≥ 2 exec turns; models that stop after one turn produce no B signal, making cross-model comparison unfair.

---

## Protocol flags

| flag | type | meaning |
|---|---|---|
| `turn1_died` | bool | plan turn timed out or failed to parse |
| `subtask_killed_count` | int | exec turns hard-killed by timeout |
| `revised_best_guess_downward` | bool | model emitted a worse tour than its prior best |
| `stop_reason` | str | `subtask_stop` / `subtask_timeout` / `subtask_parse_fail` / `turn1_died` / `total_budget_exhausted` |

---

## What gets logged per run (JSONL)

```json
{
  "model": "...",
  "seed": int,
  "coords": [[x, y], ...],
  "baseline_tour": [...],   "baseline_length": float,
  "gold_tour": [...],       "gold_length": float,
  "final_tour": [...],      "final_length": float,
  "gap_pct": float,
  "score": float,
  "declared_gap": float,
  "brier": float,
  "total_wall_seconds": float,
  "turn1_died": bool,
  "subtask_killed_count": int,
  "revised_best_guess_downward": bool,
  "stop_reason": str,
  "turns": [
    {
      "turn_index": int, "phase": "plan"|"exec",
      "wall_seconds": float, "input_tokens": int, "output_tokens": int,
      "timed_out": bool, "parse_ok": bool,
      "next_sub_in": {"id": int, "desc": str, "time_budget_s": int},
      "parsed": {
        // plan: atomic_prediction, declared_gap, decision, next_sub
        // exec: subtask_id, best_guess, p_correct, decision, next_sub
      }
    }
  ]
}
```

---

## Known gaps and upgrade path

| gap | severity | fix |
|---|---|---|
| A2 flatlined (1.000 universally) | high | tighter `SUBTASK_BUDGET_S` + prompt pressure to use realistic estimates |
| A3 is a proxy, not counterfactual | medium | extend analyzer to compute per-turn $score trajectory from `turns[].parsed.best_guess` |
| TSP-25 too easy for strong models | medium | increase city count (TSP-50, TSP-100) or switch to a harder problem class for frontier tiers |
| Gold is heuristic, not optimal | low | note in writeup; consider Concorde for small n if true optimum is needed |
| n per cell too low for Brier reliability | medium | A1 Brier varies from 0.0003 to 0.2435 for same model/arm across seeds — minimum n=5 per cell |
| Thinking tokens invisible | low | wall-clock budget sidesteps this; note in writeup |

---

## Empirical results (partial, n=19 rows, 2026-04-16)

From local Gemini API spike, 3 models × 3 seeds × up to 3 arms.

| # | Model | Accuracy | A1 | A2 | A3 | B | Composite |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | gemini-2.5-flash | 85.1% | 0.008 | 1.000† | 0.084 | 0.555 | 0.364 |
| 2 | gemini-2.5-pro | 91.2% | 0.068 | 1.000† | 0.201 | 0.356 | 0.423 |
| 3 | gemini-3.1-pro-preview | 98.7% | 0.573 | 1.000† | 0.670 | 0.009 | 0.748 |

† A2 flatlined — see known gap above.

**Key finding:** TSP-25 inverts the HCH Pareto pattern. In the HCH benchmark (on hard questions), stronger models have both better accuracy and better metacognitive calibration. In TSP-25, stronger models have better accuracy but *worse* composite metacog — because they can solve TSP-25 so easily they have no calibrated prior on their own gap (they declare gap=100% while achieving 0.24%). Flash is better calibrated despite lower accuracy.

B axis tells the reverse: gemini-3.1 has B=0.009 (excellent per-turn P_CORRECT calibration) but A1=0.573 (terrible upfront gap prediction). It doesn't know its own global capability before starting, but it does know when a specific iteration converged.

```
Accuracy (%)
 100|
    |                              * Gemini 3.1 Pro (0.748, 98.7%)
  98|                               ← best accuracy, worst metacog composite
    |
  92|             * Gemini 2.5 Pro (0.423, 91.2%)
  90|
    |
  85| * Gemini 2.5 Flash (0.364, 85.1%)
    |  ← best metacog composite, lowest accuracy
    |________________________________________
     0.3   0.4   0.5   0.6   0.7   0.8
               Composite (lower = better)
```

---

## Arm variants (optional ablation only)

The canonical benchmark uses the single-arm system prompt above. Three prompt variants can be used as an ablation to test whether prompt framing affects metacognitive behavior:

- **greedy** — "small budget, commit after one subtask"
- **exhaustive** — "maximize accuracy, ignore cost, use full budget"  
- **smart** — canonical single-arm prompt (already above)

Arm differences confound model capability with prompt sensitivity. Primary model comparisons should use a single arm. Arm ablation is useful for asking: *does telling a model about the economic objective change its behavior?*

From the partial spike: arms had zero effect on gemini-3.1 (identical solutions across all three), and mixed effect on 2.5-pro (smart arm achieved 4.4% gap vs 12.7% greedy — but the smart prompt may inject implicit algorithmic hints rather than eliciting genuine metacognition).
