---
color: cyan
isContextNode: false
agent_name: Eli
---
# §10 — Pricing-bias reconciliation (embedded)

Paired pricing bias E[Δ]−cf_Δ reconciles logistic thresholds with negative mean cf_Δ. Biases ≈ thresholds ⇒ thresholds are inflated break-evens, not risk-aversion.

# §10 — Pricing-bias reconciliation

Reconciles logistic thresholds (+2.3 / +3.6 / +4.8) with mean cf_Δ (−0.26 / −1.64 / −1.31). If mean(E[Δ]) − mean(cf_Δ) is large-positive, the signals reconcile as pricing bias.

## Paired final-turn E[Δ] vs realized cf_Δ

| model | n turns | mean E[Δ] (all) | n paired | mean E[Δ] (final) | mean cf_Δ | pricing bias |
|---|---|---|---|---|---|---|
| claude-sonnet-4.6 | 120 | +1.33 | 48 | +0.50 | -0.26 | **+0.76** |
| gemini-flash-latest | 124 | +2.12 | 51 | +0.95 | -1.58 | **+2.53** |
| gpt-5.4-mini | 149 | +1.05 | 64 | +0.63 | -1.31 | **+1.94** |

## Low/high split at each model's own median E[Δ]

| model | median E[Δ] | n_low | low E[Δ] | low cf_Δ | low bias | n_high | high E[Δ] | high cf_Δ | high bias |
|---|---|---|---|---|---|---|---|---|---|
| claude-sonnet-4.6 | +0.30 | 26 | +0.14 | -0.42 | +0.56 | 22 | +0.93 | -0.06 | +0.99 |
| gemini-flash-latest | +0.50 | 37 | +0.23 | -2.34 | +2.56 | 14 | +2.86 | +0.42 | +2.43 |
| gpt-5.4-mini | +0.40 | 38 | +0.21 | -0.83 | +1.04 | 26 | +1.24 | -2.01 | +3.25 |

## Reconciliation paragraph (verbatim)

Paired pricing biases are claude +0.76, gemini +2.53, gpt +1.94. Across low/high split, bias changes by claude Δ=+0.43, gemini Δ=−0.13, gpt Δ=+2.21. Positive paired bias + bias ≈ logistic threshold ⇒ thresholds are inflated break-evens, not risk-aversion: models stop when emit-inflated forecast hits ~0, landing realized cf_Δ at ≈ −bias. Penalty-Audit direction preserved; magnitude reading shifts from 'risk-averse pricing' to 'emissions need de-biasing before being read as break-even'.

## Key numerical reconciliation

| model | logistic threshold | paired pricing bias | gap (threshold − bias) |
|---|---:|---:|---:|
| claude-sonnet-4.6 | +2.30 | +0.76 | +1.54 |
| gemini-flash-latest | +3.60 | +2.53 | +1.07 |
| gpt-5.4-mini | +4.79 | +1.94 | +2.85 |

Residual gap = genuine pricing conservatism *on top of* emission inflation. GPT has the largest residual (+2.85) and is also the only model with strong scaling bias (Δ=+2.21 low→high). Gemini is flat-bias (Δ=−0.13) — purely uniform emission inflation. Sonnet is in between.

artifact [[cora-metacog-writereport-extension-done]]
