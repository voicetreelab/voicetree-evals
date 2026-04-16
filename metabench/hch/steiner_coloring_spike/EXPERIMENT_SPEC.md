# Steiner x Coloring Composite Local Spike

## Goal

Run a minimal local Gemini spike on a composite optimization task where the model must jointly choose:

- a cheapest cable tree that connects required coastal villages
- a frequency assignment for all villages touched by that network

The objective is:

`total_cost = cable_cost + 15 * num_frequencies_used`

This is intentionally small-scale and exact. The point is to test whether the composite structure creates real joint-reasoning pressure or whether Gemini still compresses the task into one planning turn plus one execution turn.

## Problem shape

- Villages are coastal sites connected by weighted cable edges.
- A required subset of villages must all lie in one connected tree.
- Every active village in that tree needs a radio frequency.
- Some village pairs interfere and must use different frequencies if both are active.

## Exact gold

For this spike, exact gold uses a small-instance brute-force fallback:

- enumerate all cable trees that connect the required terminals
- solve the induced coloring problem exactly
- take the minimum joint objective

This is exact for the canonical `n=8` tier and keeps the implementation smaller than a CP-SAT encoding.

## Protocol

Reuse the existing locked budget-metagame loop:

- `TOTAL_BUDGET_S = 1800`
- `SUBTASK_BUDGET_S = 600`
- `PLAN_TURN_BUDGET_S = 300`
- one planning turn, up to four execution turns
- hard timeout wrapping around each Gemini call
- JSONL logging per `(model, seed)` run

## Canonical run

- model: `gemini-3.1-pro-preview`
- seeds: `1 2 3`
- size: `n=8`, `k=3`

Seed 1 is the hand-authored canonical coastal instance from the task handoff. Seeds 2 and 3 are deterministic generated variants filtered to keep non-trivial baseline headroom and a non-zero gap between cable-only reasoning and the joint optimum.
