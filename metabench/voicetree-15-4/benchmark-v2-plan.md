---
color: blue
isContextNode: false
agent_name: Aki
---
# Benchmark v2 question set — build plan (5 phases)

Proposed plan to scale from n=24 hand-picked HLE questions to n=210 procedurally generated NP-hard problems with 3-arm counterfactual protocol. Awaiting user input on problem mix, NL wrapping, calibration budget, and timeline.

## Plan overview

Address the two judge-flagged weaknesses: sample size (n=24→200+) and missing A3 counterfactuals.

## Phase 1: Build 3 generators
Each: `generate(seed, difficulty) → (question_text, gold_answer, verify_fn, metadata)`

| Generator | Count | Difficulty knob | Verification |
|-----------|-------|-----------------|-------------|
| 3-SAT | ~150 | n_vars, clause_ratio (phase transition ~4.27) | DPLL/backtracking verifier |
| Graph Coloring | ~30 | n_vertices, n_edges, chromatic_number | Adjacent color check + minimality |
| Coupled Job Shop | ~30 | n_jobs × n_machines per factory + coupling | No overlaps, precedence, coupling check |

## Phase 2: Difficulty calibration
- Generate ~500 candidates
- Run cheap model (Haiku/Flash) to find 20-80% accuracy zone
- Select 210: ~60 easy, ~90 medium, ~40 hard, ~20 impossible/very-hard

## Phase 3: Three-arm protocol
| Arm | Prompt | Measures |
|-----|--------|----------|
| Free Choice | Full HCH v2 | A1+A2+A3 combined |
| Forced Atomic | No decomposition allowed | A1 baseline + A3 counterfactual |
| Forced Decomposed | Must decompose ≥2 subtasks | A2 + A3 counterfactual |

A3_wrong = (chose atomic AND forced_decomp better) OR (chose decomp AND forced_atomic better)

## Phase 4: Integration
New `gen_benchmark_v2.py` using existing kbench + parsing infrastructure.

## Phase 5: Writeup fixes
- Dataset provenance, schema, separate A2 into Brier/MAPE, calibration-resolution decomposition

## Open questions for user
1. Problem mix weighting (more coupled job shop for novelty vs. SAT for power?)
2. Natural language wrapping (scenario framing with verifiable core?)
3. Calibration run budget feasibility
4. Kaggle deadline → compressed vs. full plan

### NOTES

- Judge score 85.5/100 — novelty is strong (95), dataset quality is the weak point (75)
- Previous conversation already concluded: coupled job shop > Kolmogorov for Kaggle
- Existing parsing infra (_parse_hch_trajectory, _parse_vanilla) works unchanged for all 3 arms

[[hch-metacog-spike-orchestration-done_1_0_2_1_1_0_1]]
