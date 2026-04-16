---
color: green
isContextNode: false
agent_name: Aki
---
# Benchmark class bench — results summary + ranking

6 of 7 classes returned results (Class 1 hung). Tier 1 (ship): Classes 7 (Kolmogorov) and 4 (infeasibility proof) — shortest output, insight-required, clean metacog. Tier 2 (tune): Classes 2, 3. Tier 3 (fix): Classes 5, 6. Key strategic findings: difficulty-up/tokens-down inversion is real for Classes 6+7; insight-based classes beat enumeration-based on time and signal; Class 5 validated budget-pressure need (19min ceiling); OR-Tools gold verification needed at scale (Class 5 designer computed wrong gold).

## Results table

| Class | Problem type | Time | Output words | Correct? | Brier_D | Metacog signal | Verdict |
|---|---|---|---|---|---|---|---|
| **7** | Kolmogorov string compression | 349s | 238 | ✅ (beat ref) | 0.0049 | Strong: atomic 0.45 → decomp 0.93 | **BEST** |
| **4** | Infeasibility proof (NO) | 266s | 345 | ✅ partial proof | 0.0004 | Partial-proof gap is itself useful signal | **Very strong** |
| **3** | Graph coloring (W5 trap) | 292s | 450 | ✅ | 0.0009 | Clean decomposition, atomic 0.70 | **Strong** |
| **2** | Decision/comparison (3 schedules) | 385s | 590 | ✅ | 0.0081 | Dispatcher trap fires | **Good** |
| **5** | 12-constraint chunk scaling | 1156s | 550 | ✅ (designer was wrong!) | 0.014 | 0/12 dropped — no overload | **Marginal** (hit 19min ceiling) |
| **6** | Proof compression (M=5) | 227s | 280 | ✅ trivially | 0.0009 | No insight required — trimmed induction | **Design flaw — fixable** |
| **1** | Adversarial 3x2 job shop | — | — | Ari hung | — | — | No data |

## Ranked by promise for the benchmark

### Tier 1 — ship these
**Class 7 (Kolmogorov)** and **Class 4 (infeasibility proofs)**. Both hit the sweet spot: short output (<350 words), insight-required difficulty, clean metacog gaps, strong Brier calibration. Class 7 has the cleanest "difficulty up, tokens down" inversion we have. Class 4's partial-proof outcome is itself a publishable signal — the model finds the obvious case but misses the adversarial one, which is exactly the metacog failure mode the benchmark is designed to catch.

### Tier 2 — promising but need tuning
**Class 3 (graph coloring)** works well but edge cases around ω(G)=3 vs odd-wheel need more instances to characterize. **Class 2 (decision/comparison)** works but the dispatcher trap might be too domain-specific — need variants.

### Tier 3 — blocked on design fixes
**Class 5 (constraint scaling)** revealed two problems: (1) hit the 19-min ceiling meaning difficulty can't scale further without budget enforcement, (2) designer computed wrong gold — we need OR-Tools verification in the pipeline, not hand calculation. **Class 6 (proof compression)** was trivially solved by induction-trimming — M=3 with "no induction" constraint would force the telescoping insight.

### Tier 4 — unknown
**Class 1 (adversarial 3x2 job shop)** — need to rerun, Ari hung.

## Key strategic takeaways

1. **The "difficulty up, tokens down" inversion is real** — Classes 7 and 6 both produce shorter outputs for harder versions. This is the most valuable property for a benchmark that must stay in-context.

2. **Insight-based classes (4, 7) beat enumeration-based classes (5)** on both time and signal clarity. The model either finds the key argument (<400 words) or it doesn't — binary, fast, clean.

3. **Class 5 proved the budget-pressure intuition right** — without budget enforcement, we hit the time ceiling before getting a discriminating signal. The 19-min run with 0 dropped constraints means we'd need to scale up further, but there's no room to. Budget-as-constraint is the only principled way out.

4. **The designer-gold problem is real infrastructure work.** Cho anchored on one optimal A-schedule and got the gold wrong. At scale (210 problems), we cannot trust hand-computed gold — every problem needs a verified solver (OR-Tools or brute force).

### NOTES

- Ari (Class 1 designer) hung without producing output — rerun needed
- 4 solver children exited with no nodes (Emi, Eli, Eva, Eve, Fei partially) — but output was captured via designer parents' reads in most cases
- Class 5 designer made gold error but solver found correct answer via variant A-schedule — pipeline needs OR-Tools gold verification, not hand calc
- Budget-enforcement protocol modification (enforce max_tokens = predicted_words) is the clear next experiment given Class 5's 19-min ceiling hit

[[benchmark-class-bench]]
