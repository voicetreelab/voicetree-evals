# Codex MetaGame v2 - Local Gemini Spike Spec

## Goal

Replace the TSP-based local metagame spike with a **single-prompt, multi-turn, natural-language coupled job-shop** spike that better measures the metacognitive signals we actually care about:

- initial self-calibration before solving
- whether the model decomposes the problem sensibly
- whether it estimates subtask effort realistically
- whether it updates confidence after intermediate work
- whether it stops when more compute is no longer worth it

This is a **local Gemini API spike**, not the final Kaggle packaging.

## Core design choice

Use **one canonical objective-optimizing prompt**, not `greedy` / `exhaustive` / `smart` arms.

The TSP run showed that arm design became unnecessary complexity. The main benchmark signal should come from the **problem class + protocol**, not from prompt ablations.

Counterfactual arms can be added later as analysis-only experiments, but they are out of scope for this v2 local spike.

## Problem family

### Main task

Procedurally generated **coupled two-factory job-shop scheduling**.

- Factory A and Factory B each have their own machines.
- Every job must complete all of its Factory A operations before that same job can start in Factory B.
- Each factory is itself a small job shop: machine exclusivity, job-order precedence, no preemption.
- Output is a full feasible schedule plus a claimed makespan.

### Why this family

- Unlike TSP, it is not a memorized "known algorithm" benchmark.
- It has natural staged decomposition: solve / approximate Factory A first, then reason about Factory B under release times.
- It supports **progressive improvement**: a model can start from a feasible baseline schedule and improve it.
- Exact gold is computable offline with OR-Tools CP-SAT for MVP sizes.
- It can be rendered in natural language to reduce direct solver-template behavior.

## Deliberate non-duplication vs Meg

Another agent, Meg, is already exploring a **simpler Johnson-style two-stage flowshop** where:

- every job visits Department A then Department B
- the order is shared across both departments
- the model's answer is a **single permutation**

This v2 spike must stay distinct. It should test the **harder coupled job-shop** setting where:

- each factory is a real job shop with its own machine routing
- Factory B is released by Factory A per job
- the model must emit a **full schedule**, not just a permutation

The point of this v2 spike is to learn whether the richer coupled structure creates stronger metacognitive signal than Meg's simpler flowshop formulation, or whether it merely creates output/parsing overhead.

## Benchmark shape for the spike

### Canonical evaluation unit

One `(model, seed)` trial on one generated coupled job-shop instance.

### Sizes

- **Smoke size:** `3x4`
  Meaning: 3 jobs per factory, 4 machines per factory.
  Purpose: validate generator, solver, parser, verifier, and protocol end-to-end.
- **Spike size:** `6x7`
  Purpose: main comparison tier for `gemini-2.5-pro`, `gemini-2.5-flash`, and `gemini-3.1-pro-preview`.

### Planned runs

1. **Smoke run**
   - 1 model: `gemini-2.5-pro`
   - 1 seed
   - size `3x4`
   - objective: confirm end-to-end correctness before spending API budget

2. **Full local spike**
   - models:
     - `gemini-2.5-pro`
     - `gemini-2.5-flash`
     - `gemini-3.1-pro-preview`
   - seeds: `1 2 3`
   - size `6x7`
   - total rows: `9`

If `6x7` is obviously too easy or too hard during smoke, it is acceptable to switch the main spike one notch at a time, for example to `6x6`, `6x8`, or `7x7`, but only if the change is documented in the results node and JSONL metadata.

## Required directory layout

Implement under:

`/Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2`

Expected files:

- `EXPERIMENT_SPEC.md`
- `gemini_client.py`
- `jobshop_instance.py`
- `protocol.py`
- `run_spike.py`
- `analyze.py`
- `requirements.txt`
- `results/` for JSONL outputs

Reusing code from `hch/metagame/` is encouraged where it still fits. This v2 folder should be self-contained enough to run independently.

## Instance generation

Create deterministic seeded instance generation:

`build_instance(seed: int, n_jobs: int, n_machines: int) -> CoupledJobShopInstance`

Each instance should include:

- Factory A routing and durations
- Factory B routing and durations
- a natural-language problem statement
- an exact gold solution from OR-Tools CP-SAT
- a cheap feasible baseline schedule
- a verifier for arbitrary model-proposed schedules

### Generation rules

- Integer durations only.
- Keep routing non-trivial: do not make every job use machines in the same order.
- Preserve coupling by job id: B-job `j` is released only after A-job `j` fully completes.
- Prefer instances where a locally good Factory A order is not obviously globally best.
- Deterministic from seed.

### Natural-language rendering

The benchmark-facing prompt should be natural language, not raw solver input.

It should still be fully precise:

- describe the factories as a supply chain
- give machine names and ordered steps per job
- state non-preemption and one-job-per-machine constraints explicitly
- state the coupling rule explicitly
- include a baseline feasible schedule summary and its makespan

Light narrative wrapping is good. Hidden ambiguity is not. The prompt must remain exactly verifiable.

## Baseline and exact gold

### Baseline

Every instance must ship with a deterministic feasible baseline, for example:

- greedy dispatch in Factory A
- then greedy dispatch in Factory B subject to release times

If the model produces no parseable schedule, the baseline is the scored fallback.

### Gold

Gold must be exact, not heuristic.

Use OR-Tools CP-SAT to compute:

- optimal makespan
- one optimal full schedule

Never rely on hand-computed gold.

## Output contract

The model must emit structured text that the runner can parse.

### Turn 1: planning only

Turn 1 is **not allowed** to emit a full schedule.

Required fields:

```text
ATOMIC_FORECAST: {"p_gap_le_2": <float>, "p_gap_le_5": <float>, "p_gap_le_10": <float>}
CONTINUE_FORECAST: {"p_improve_if_one_more_subtask": <float>, "expected_gap_reduction": <float>, "expected_delta_score": <float>}
DECISION: continue | stop
NEXT_SUB: {"id": 1, "desc": "...", "time_budget_s": <int>}
```

If `DECISION: stop`, `NEXT_SUB` is omitted and the baseline becomes final.

Interpretation:
- `ATOMIC_FORECAST` is your calibrated forecast for the gap if you answered now without decomposition.
- `CONTINUE_FORECAST` is your forecast for taking exactly one more subtask instead of stopping now.
- Do not emit a probability of exact correctness; optimization tasks should be forecast in terms of distance-to-optimal thresholds.

### Turn N >= 2: execute one subtask

Required fields:

```text
SUB_<n>: <work>
BEST_GUESS: {
  "factory_a": {
    "<machine_name>": [["J<id>", <start>, <end>], ...]
  },
  "factory_b": {
    "<machine_name>": [["J<id>", <start>, <end>], ...]
  },
  "makespan": <int>
}
QUALITY_FORECAST: {"p_gap_le_2": <float>, "p_gap_le_5": <float>, "p_gap_le_10": <float>}
CONTINUE_FORECAST: {"p_improve_if_one_more_subtask": <float>, "expected_gap_reduction": <float>, "expected_delta_score": <float>}
DECISION: continue | stop
NEXT_SUB: {"id": <n+1>, "desc": "...", "time_budget_s": <int>}
```

If `DECISION: stop`, `NEXT_SUB` is omitted.

### Parser tolerance

Be somewhat tolerant to markdown noise around labels, as in the existing TSP parser, but require:

- parseable `BEST_GUESS`
- all operations present exactly once
- valid integer start/end times
- claimed makespan matching the verified schedule makespan

If a turn's schedule is infeasible or unparsable, retain the last good schedule.

## Schedule verification

The verifier must check:

1. every required operation appears exactly once
2. operation duration matches the instance definition
3. job order is respected inside each factory
4. no machine overlap
5. Factory B release times respect Factory A completion times for the same job
6. reported makespan equals the max end time

The verifier should return:

- `is_feasible`
- `verified_makespan` if feasible
- a short failure reason if infeasible

## Protocol

This stays multi-turn, but simpler than the TSP branch:

- one system prompt
- one planning turn
- up to `MAX_EXEC_TURNS = 4`
- after each execution turn, inject usage + elapsed time stats
- retain last valid schedule as the current best guess

### Budget constants for the local spike

- `TOTAL_BUDGET_S = 1800`
- `SUBTASK_BUDGET_S = 600`
- `PLAN_TURN_BUDGET_S = 300`

Use hard timeout wrapping around each Gemini call, as in the current local runner.

### Stop rule framing

The model should be told:

- it earns score for lower makespan / lower gap to optimal
- it pays score for wall-clock time
- it should stop when expected gain is not worth more time

But do not over-coach beyond that. The prompt should not bake in a specific decomposition strategy or teach the answer.

## Scoring

Use the same high-level shape as the TSP spike, adapted to makespan:

```text
gap_pct  = 100 * (verified_makespan - optimal_makespan) / optimal_makespan
accuracy = 100 - gap_pct
score    = max(0, accuracy) - TIME_PENALTY * total_wall_seconds
```

Constants:

- `TIME_PENALTY = 0.01`

If the final schedule is infeasible or missing, score the baseline schedule instead.

## Metrics to log per row

Each JSONL row should include at least:

- `model`
- `seed`
- `n_jobs`
- `n_machines`
- `optimal_makespan`
- `baseline_makespan`
- `final_makespan`
- `gap_pct`
- `score`
- `atomic_forecast`
- `plan_continue_forecast`
- `brier`
- `plan_continue_brier`
- `plan_expected_delta_score_error`
- `final_quality_forecast`
- `total_wall_seconds`
- `turn_count`
- `turn1_died`
- `subtask_killed_count`
- `stop_reason`
- `revised_best_guess_downward`
- `final_schedule_feasible`
- `final_schedule_source` (`model`, `baseline`, `last_good_turn`)
- `error` if the run failed

Also retain enough turn-level detail to debug:

- each turn's raw text
- parse status
- wall time
- token counts if available

## Analyzer requirements

`analyze.py` should print grouped summaries by model, including:

- mean gap
- mean wall time
- mean score
- mean Brier on the thresholded atomic forecast
- turn-1 deaths
- timeout kills
- feasibility failures
- mean turn count

Simple terminal summary is sufficient for the spike.

## Reuse guidance

The new implementation should copy or adapt the good parts of `hch/metagame/`:

- Gemini client wrapper
- timeout pattern
- JSONL runner shape
- summary analyzer shape

But it should **not** carry over:

- multi-arm prompt logic
- TSP-specific parsers
- TSP instance or tour utilities

## Non-goals

Out of scope for this spike:

- Kaggle packaging
- thinking-token billing as a core metric
- forced-atomic / forced-decomposed ablation arms
- multiple problem families
- a polished dataset generator for hundreds of instances

## Child-agent implementation target

The child Codex agent should implement a runnable local spike under this directory with this minimum bar:

1. smoke run works on one seeded `3x4` instance
2. full spike command exists for the 3 target Gemini models on `4x5`
3. JSONL results and analyzer work
4. progress nodes document what was built and what still failed, if anything

If exact `6x7` solving via OR-Tools is too slow or fragile in the first pass, it is acceptable to land `3x4` end-to-end first and explicitly document the blocker before extending.
