---
color: blue
isContextNode: false
agent_name: Emi
---
# HCH HLE-12 v2 — 9-arm synthesis + cross-cutting findings (mid-run)

9 model arms completed (2 in progress). Gemini 3.1 Pro is strict Pareto dominator. Haiku reward-hack hypothesis refuted — real failure is anti-correlated predictions, not flat. OSS gap from top closed-tier is large. Resolution-weighted composite has its own reward hack.

## 9-arm comparison table

| # | Model | Accuracy | A1 Brier | A2 MAPE (cap 1) | A3 wrong-dec | D_hch | D_van | Composite |
|---|-------|----------|----------|------------------|--------------|-------|-------|-----------|
| 1 | **Gemini 3.1 Pro** (Gus) | **79%** (15/19) | **0.007** 🎯 | 0.793 | 0.22 | 0.332 | **0.100** 🎯 | **0.34** 🥇 |
| 2 | Claude Sonnet 4.6 (Hana) | 35% (8/23) | 0.353 | **0.524** | ~0.73 | **0.410** | 0.307 | 0.54 |
| 3 | Claude Haiku 4.5 (Ivan₀) | 12.5% (3/24) | 0.252 | 0.582 | 0.83 | 0.393 | 0.522 | 0.55 |
| 4 | GPT-5.4 base (Ian) | 27% (4/15) | 0.406 | 1.000† | 0.57 | 0.474 | 0.769 | 0.66 |
| 5 | GPT-5.4 Nano (Jay₀) | 4% (1/24) | 0.144 | 1.000‡ | 0.92 | 0.455 | 0.394 | 0.69 |
| 6 | Qwen3-235B Instruct (Jay₁) | 17% (4/24) | 0.282 | 1.000§ | 0.79 | 0.581 | 0.899 | 0.69 |
| 7 | v1 Gemini 2.5 Flash | 8% (2/24) | 0.537 | 0.745 | 0.83 | 0.934 | N/A | 0.70 |
| 8 | Qwen3-235B Thinking (Ivan₁) | 8% (2/24) | 0.269 | 1.000§ | 0.92 | 0.639 | 0.786 | 0.73 |
| 9 | Gemini 2.5 Flash-Lite (Ivy₀) | 8% (2/24) | 0.679 | 1.000§ | 0.92 | — | — | 0.87 |

† GPT-base raw A2 = 1.069   ‡ Nano raw A2 = 59.61 (pathological terse vanilla — 4-word outputs)   § A2 > 1 (bimodal or extreme verbosity, e.g. Qwen3 "thinking mode" produces 6k–11k word outputs)

## Pareto chart — accuracy vs metacog composite

```
 Accuracy (%)
  100│
   80│  ● Gemini 3.1 Pro          ← strict Pareto dominator
      │   (0.34, 79%)
   60│
   40│      ● Sonnet 4.6
      │        (0.54, 35%)
      │        ● GPT-5.4 base (0.66, 27%)
   20│              ● Qwen-Instruct (0.69, 17%)
      │                ● Haiku (0.55, 12.5%)
      │                     ● Qwen-Think, v1 Flash, Flash-Lite
   10│                     ● Nano
    0│_________________________________________
      0.3  0.4  0.5  0.6  0.7  0.8  0.9   Composite (lower=better)
```

## 6 headline findings

**1. Gemini 3.1 Pro is a strict dominator.** Best accuracy AND best composite. This isn't a tradeoff win — it's a regime change.

**2. Haiku's "calibrated pessimism" hypothesis was REFUTED by Jose's decomposition.** std(p_atomic)=0.199 (predictions do vary), but AUC=0.409 < 0.5 (below chance) — Haiku's confidence is *anti-correlated* with correctness. Confident on wrong answers, uncertain on the 3 it gets right. Different (worse) failure mode than flat predictions.

**3. Resolution-weighted composite has its OWN reward hack.** Gemini 3 Pro drops from #1 to last on pure resolution because 87% accuracy makes outcome-variance ≈ 0 — resolution ceiling caps at p×(1-p). At our N=12 with base rates 4%–87%, neither pure Brier nor resolution-only is robust. Needs stratified-difficulty questions (target 30–60% baseline accuracy) to open the measurement ceiling.

**4. Two distinct A3 (decomp-decision) profiles emerged:**
   - **Selective decomposers** (Gemini Pro 1/9, Sonnet 5/11): decompose rarely, atomic default works. First decomp payoffs ever observed (Sonnet Q41, Gemini Pro Q55+others).
   - **Compulsive decomposers** (Haiku 12/12, Qwen-Think 12/12, Flash-Lite 6/6 of HCH Qs, Nano 3/12 but still frequent): always decompose, 0–17% payoff rate.
   Selective > compulsive on composite.

**5. OSS top-tier tracks *weak* closed tier, not strong.** Qwen3-235B (largest non-coder OSS on proxy) = 8–17% accuracy, comparable to Haiku/Flash-Lite/Nano. Significant capability gap from Sonnet/GPT base, massive gap from Gemini 3 Pro. No Llama or Mistral on proxy.

**6. Calibration improves with capability, within family.**
   - Gemini family: Flash (0.537) → Flash-Lite (0.679) → 3.1 Pro (0.007). Pro is outlier.
   - OpenAI family: Nano (0.144 — suspiciously good at this accuracy level) → GPT base (0.406). Inversion hints at selection / training artifact.
   - Anthropic family: Haiku (0.252) → Sonnet (0.353). Calibration gets WORSE going Haiku→Sonnet, counter to expectation. Sonnet's failure is high-confidence wrong, Haiku's is anti-correlation.

## v3 spec implications

- **Stratified difficulty per model** — auto-select question set targeting 30–60% baseline accuracy so resolution stays measurable
- **Report all 3 Brier components** (Reliability, Resolution, Uncertainty) in every scorecard — total Brier alone hides the failure mode (Jose)
- **AUC as primary discrimination metric** — rank-based, not affected by base-rate cliffs. Haiku's AUC<0.5 would have been caught instantly
- **Axis C upgrade** — per-subtask gold answers to convert self-consistency → actual calibration (the self-report interpretation remains valid but is weaker)
- **Final leaderboard metric** — keep raw Brier composite (standard, defensible) but surface the decomposition as the insightful finding

## What's still pending

- Ivy: DeepSeek arm (OSS, dedicated kernel, running)
- Ivan: GPT-OSS-120B arm (OSS, dedicated kernel, queued next after Qwen done)
- Cross-model final report node (after all 11 arms land)

### NOTES

- Haiku AUC=0.409 (below chance) is the single most interesting per-model finding — refutes my initial hypothesis that composite Brier was being hacked by uniform pessimism. Real mechanism is anti-correlation.
- Gemini 3.1 Pro's resolution = 0 (degenerate) is a measurement-ceiling artifact at N=12, not a real score — flag this in any v3 design
- No Llama/Mistral on proxy — available OSS families: deepseek-r1/v3, gemma-3/4 (1b–31b), gpt-oss-20b/120b, qwen3-235b/480b-coder
- Two Qwen3-235B variants (Instruct vs Thinking) differ dramatically in output style (Instruct ~terse, Thinking 6k–11k words) — replication signal useful for spec robustness
- Ivy discovered: kbench module eviction on fresh kernel re-inits the IP-locked static API key → PermissionDenied. Fix: swap kbench.llm.model in-place without eviction.
- Hana discovered: LLMChat.prompt() doesn't accept max_output_tokens kwarg — proxy-side fix needed for runaway Q43/Q49 on Sonnet (11.6k / 10k words)

## Related

- [jose-brier-decomp-analysis](jose-brier-decomp-analysis.md)
- [gus-gemini3pro-hle12-complete](gus-gemini3pro-hle12-complete.md)
- [hana-sonnet-arm-complete](hana-sonnet-arm-complete.md)
- [ian-hch-chatgpt-arm-complete](ian-hch-chatgpt-arm-complete.md)
- [ivan-haiku-hle12-complete](ivan-haiku-hle12-complete.md)
- [jay-gptnano-hle12-complete](jay-gptnano-hle12-complete.md)
- [ivy-flashlite-hle12-complete](ivy-flashlite-hle12-complete.md)
- [jay-qwen235b-hle12-complete](jay-qwen235b-hle12-complete.md)
- [ivan-qwen-hle12-complete](ivan-qwen-hle12-complete.md)

[[task_1776238764431kq6]]
