# ForecastBench: Evaluation Plan for Voicetree

## What is ForecastBench?

ForecastBench is a dynamic benchmark that measures how well AI systems predict real future events. Published at ICLR 2025, it is run by the Forecasting Research Institute.

Every two weeks, 500 questions are released. Each question asks for a probability (0-1) that some event will occur. Questions resolve against reality — there is no subjective judging. Scoring uses a difficulty-adjusted Brier score converted to a "Brier Index" (0-100, higher = better).

The benchmark is contamination-proof by design: all questions concern future events with no known answer at submission time.

### Two types of questions

**Market questions (250 per round):** Sourced from prediction markets (Metaculus, Polymarket, Manifold, Infer). Free-form questions about world events.

Examples:
- "Will the US and China reach a trade deal by 2026?"
- "Will GPT-5 be released before July 2026?"
- Each requires 1 probability forecast

**Dataset questions (250 per round):** Sourced from structured data (FRED, ACLED, Wikipedia, YFinance, DBnomics). Binary questions about whether a metric will be higher or lower than a reference value.

Examples:
- "Will the 10-Year Treasury yield have increased by {resolution_date} relative to the value on {forecast_due_date}?" (FRED)
- "Will there be more protests in France in the 30 days before {resolution_date} relative to the 360-day average?" (ACLED)
- "Will AAPL close price be higher on {resolution_date} than on {forecast_due_date}?" (YFinance)
- Each requires **8 probability forecasts** at different time horizons (7d, 30d, 90d, 180d, 1yr, 3yr, 5yr, 10yr)

**Total forecasts per round: ~2,250** (250 market x 1 + 250 dataset x 8)

---

## Current Leaderboard (as of April 2026)

### Tournament Track (tools, scaffolding, crowd data allowed)

| Rank | System | Score | Notes |
|------|--------|-------|-------|
| 1 | Superforecasters (human) | 70.9 | The ceiling to beat |
| 2 | Cassi-AI (ensemble + crowd) | 67.9 | Model ensemble + market price adjustment |
| 3 | Gemini-3-Pro (w/ crowd) | 67.8 | Raw model + market price in prompt |
| 3 | Grok 4.20 | 67.8 | xAI direct submission |
| 5 | Foresight-32B | 67.3 | RL fine-tuned on Brier score (open source) |
| 8 | Claude 3.7 Sonnet (w/ crowd) | 67.0 | Raw model + market price in prompt |

### Baseline Track (no tools, no crowd data)

| Rank | Model | Score |
|------|-------|-------|
| 1 | Superforecasters | 70.9 |
| 2 | Public median | 65.2 |
| 3 | o3 (scratchpad) | 65.1 |
| 4 | Claude 3.7 Sonnet (scratchpad) | 64.8 |

### Dataset-Only Track (preliminary — results in ~10 days)

| Rank | System | Dataset Score |
|------|--------|--------------|
| 1 | Google DeepMind (green tree) | 66.2 |
| 2 | Superforecasters | 63.8 |
| 3 | Google DeepMind (yellow mouse) | 63.7 |

### Key observation

**Nobody is using multi-agent orchestration, web search, tool use, or sophisticated scaffolding.** ~80% of the leaderboard is ForecastBench running raw model API calls. The only differentiated entries are Cassi-AI (ensemble), Foresight-32B (RL fine-tuned), and DeepMind's mystery entries. This is an open field.

---

## Why ForecastBench is the right benchmark for Voicetree

1. **Multi-agent naturally helps.** Forecasting decomposes into research, analysis, and synthesis — exactly what Voicetree's graph-based orchestration enables. No other competitor is doing this.

2. **No cheating concerns.** All information is public. No hidden state. The graph can't leak anything that isn't already available.

3. **Clear gap to close.** Superforecasters at 70.9, best system at 67.9, best raw model at 65.1. Every point of improvement is meaningful and demonstrable.

4. **Credible venue.** ICLR 2025 paper. Used by OpenAI, Anthropic, Google, xAI. A strong showing here is a legitimate marketing artifact.

5. **Untapped approach.** Zero competitors are using multi-agent workflows. If Voicetree scores competitively, it demonstrates a novel capability.

---

## Submission mechanics

- **Registration:** Email forecastbench@forecastingresearch.org to get a GCP upload bucket.
- **Schedule:** Questions drop every 2 weeks on Sundays at 00:00 UTC. Next window: **April 12, 2026**.
- **Deadline:** 24 hours from question release (23:59:59 UTC same day).
- **Coverage:** Must forecast >= 95% of market questions AND >= 95% of dataset questions.
- **Max submissions:** 3 per round.
- **Anonymity:** Can request anonymous submission (assigned "Anonymous N").
- **Results:** Dataset scores appear on preliminary leaderboard in ~10 days. Full tournament scores in ~50 days.

### Submission format

Filename: `{date}.{organization}.{N}.json`

```json
{
  "organization": "Voicetree",
  "model": "Voicetree Multi-Agent Forecaster v1",
  "question_set": "2026-04-12-llm.json",
  "forecasts": [
    {
      "id": "14364",
      "source": "metaculus",
      "forecast": 0.32,
      "resolution_date": null,
      "reasoning": null
    },
    {
      "id": "WFC",
      "source": "yfinance",
      "forecast": 0.53,
      "resolution_date": "2026-04-19",
      "reasoning": null
    }
  ]
}
```

---

## Options

### Option A: Dataset-only focus (recommended start)

**Scope:** Focus effort on the 250 dataset questions. Submit 0.5 for all market questions.

**Why:**
- Dataset questions are more structured and tractable (binary: will X be higher/lower?)
- Google DeepMind is #1 on dataset track at 66.2 — a clear, prestigious target
- Beating superforecasters (63.8) on dataset questions is achievable
- Results visible in ~10 days (vs 50 days for full tournament)
- Lower compute: 250 questions x 8 horizons = 2,000 forecasts
- Sources are data-driven (FRED, YFinance, ACLED, Wikipedia, DBnomics) — well-suited to research agents

**Voicetree workflow per question:**
1. **Data Agent** — Fetch recent data for the metric (trend, volatility, seasonality)
2. **Analysis Agent** — Compute base rates, historical hit rates for similar moves at each horizon
3. **Calibration Agent** — Adjust probabilities for known biases, ensure coherence across horizons
4. **Output:** 8 calibrated probabilities per question

**Compute estimate (2x Claude Max):**
- 2,000 forecasts / 24 hours = ~1.4 per minute average
- With a 3-agent workflow at ~2 min per question: ~8 hours for all 250 questions
- Comfortably within budget with parallel execution across 2 accounts

**Target:** Beat superforecasters on dataset track (>63.8). Stretch: beat DeepMind's green tree (>66.2).

### Option B: Full tournament entry

**Scope:** Full 500-question submission with multi-agent workflows for both market and dataset questions.

**Why:**
- Appears on the main tournament leaderboard (higher visibility)
- Market questions are where multi-agent orchestration adds the most value (research, reasoning)
- Competing directly against Cassi-AI (67.9) and frontier models

**Additional complexity:**
- Market questions require current event knowledge, web search, news analysis
- 250 additional market forecasts on top of 2,000 dataset forecasts
- Tighter compute budget (2,250 total forecasts in 24 hours)
- Results take 50 days to appear

**Voicetree workflow for market questions:**
1. **Research Agent** — Web search for recent news, expert opinions, relevant data
2. **Base Rate Agent** — Historical reference class forecasting
3. **Reasoning Agent** — Weigh evidence, consider scenarios
4. **Calibration Agent** — Adjust for LLM biases (tendency toward 0.5, overconfidence)
5. **Output:** 1 calibrated probability

**Target:** Top 10 on tournament track (>66.0). Stretch: beat Cassi-AI (>67.9).

### Option C: Progressive approach (recommended)

**Round 1 (April 12):** Option A — dataset-only focus. Validate the pipeline, get preliminary results in ~10 days.

**Round 2 (April 26):** Based on Round 1 results, either:
- Iterate on dataset approach if scores are promising
- Expand to full tournament entry (Option B) if compute is manageable
- Adjust workflow based on which question types benefited most from orchestration

**Round 3+:** Optimize based on data. Identify which sources (FRED vs ACLED vs YFinance) and which horizons benefit most from multi-agent treatment. Focus compute where it matters.

---

## What makes this a compelling marketing story

**Narrative:** "Voicetree's multi-agent orchestration outperforms every raw LLM on real-world forecasting — a benchmark where no other AI system uses agent workflows."

**Key proof points:**
- First multi-agent system to compete on ForecastBench
- Outperforms single-model baselines (Claude, GPT, Gemini) without fine-tuning
- Demonstrates that graph-based orchestration adds measurable value to decision-making
- Competes on a benchmark used by OpenAI, Anthropic, Google, and xAI
- Published at ICLR 2025 — not a toy benchmark

**Even a modest result is interesting:** If Voicetree scores 64-65 on dataset questions (matching raw frontier models), the story is "multi-agent orchestration on a smaller model matches frontier model performance." If it scores >66, it's beating DeepMind.

---

## Next steps

1. **Register** — Email forecastbench@forecastingresearch.org for GCP bucket access
2. **Dry run** — Download the March 29 question set, run Voicetree workflows on 10-20 dataset questions, measure quality and throughput
3. **Build pipeline** — Script that reads question JSON, spawns Voicetree workflows, collects probabilities, outputs submission JSON
4. **Submit April 12** — First real round (Option A: dataset-focused)
5. **Iterate** — Review preliminary results (~April 22), adjust for Round 2
