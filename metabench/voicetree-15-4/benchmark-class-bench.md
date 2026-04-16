---
color: blue
isContextNode: false
agent_name: Aki
---
# Benchmark problem-class bench — 7 classes, HCH-solved, timed

Spawn 7 Sonnet designers (one per class 1-7). Each designs an example question with expected_tokens < 3x3 coupled job shop, difficulty >= 3x3. Each spawns a Sonnet solver child running HCH v2 protocol. Parents measure time, accuracy, Brier, metacog signals. Goal: find which classes deliver short-token + high-difficulty + clean metacog signal.

## Bench protocol

**Context:** 3x3 natural-language coupled job shop took Amit >20 min — hitting the token ceiling. We need problem classes where reasoning is short but difficulty is equal-or-greater.

**7 classes under test (from prior turn):**
1. Coupled job shop — adversarial structure (fixed 3x2)
2. Decision/comparison job shop (pre-computed options)
3. Graph coloring on fixed-size graphs (8-12 nodes)
4. Lower-bound / infeasibility proofs
5. Working memory chunk scaling
6. Proof compression
7. Kolmogorov-style string compression

**Each designer agent's 3 phases:**
- PHASE 1: Design question (< 3x3 tokens, >= 3x3 difficulty), compute gold
- PHASE 2: Spawn Sonnet solver child with HCH v2 protocol wrapper, record start time
- PHASE 3: Wait, measure time/accuracy/Brier, create progress node

**Output per class:** one progress node with question, gold, child trace, all metrics, one-sentence assessment.

### NOTES

- Each parent gets depthBudget=1 so they can spawn one solver child with depth 0
- If child exceeds ~15 min, parent should note timeout — that's the finding for that class
- Success criteria: time_to_solve < Amit's 20min AND accuracy achievable AND p_correct calibration legible

[[hch-metacog-spike-orchestration-done_1_0_2_1_1_0_1]]
