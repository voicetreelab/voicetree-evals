---
color: blue
isContextNode: false
agent_name: Ivan
---
# Factory A Eval Plan v1 — questions × local LLMs (parity w/ Kaggle)

Proposed plan: 48 questions, 15 eval rows, 3 models via `llm` CLI, 5 Codex (1 q-gen + 1 harness + 3 eval). Parity via `LocalLLM` binding system prompt at construction (1-line divergence from Kaggle path). Incorporates Ayu's two constraints: `gemini-flash-latest` (verified working in CLI) + no default fallback parser (prompt-tune first).

# Factory A — Eval Orchestration Plan v1 (DRAFT, awaiting sign-off)

**Will NOT spawn Codex until user/Ayu approves.**

## Objective recap
1. `questions.jsonl` — 36 solo (6 cls × 2 diff × 3 seeds) + 12 portfolios = **48 rows**
2. `results/runs/{model}/*.jsonl` — 15 rows × 3 models = **45 real runs**
3. Max code-parity with Kaggle: same `run_instance()` serves both paths; only the LLM provider differs.

## Ayu's two constraints absorbed this turn
- **Model:** `gemini-flash-latest` (full Flash, NOT lite). **Verified:** `llm -m gemini-flash-latest "test"` returns `OK` in this env. llm-gemini plugin already knows the alias.
- **No default fallback JSON parser.** Fix label-drop via prompting first (few-shot + stronger CONTRACT + temp 0). Only add fallback if ≥2 of 3 models keep dropping labels after the 3-model smoke.

## Node split (tree below)
- Parity architecture → `factory-a-eval-plan-parity.md`
- Question generation (48 rows) → `factory-a-eval-plan-questions.md`
- Eval harness + prompt hardening → `factory-a-eval-plan-harness.md`
- Codex fan-out, budget, collisions → `factory-a-eval-plan-execution.md`

## Open questions for user (please answer before spawn)

1. **Question count confirmation** — 36 solo + 12 portfolio = 48 rows. OK, or trim/expand?
2. **Eval subset shape** — 12 solo (6 cls × 2 diff × seed=1) + 3 portfolios (seeds 1,2,3) = 15. OK, or different slice?
3. **Portfolio caps** — keep (33,33,34)→100 from smoke, or propose variable per-problem caps?
4. **Prompt hardening location** — amend `harness/prompt.py` (consistent Kaggle + local) vs layer few-shot in `eval_harness/` only (keeps Ben's prompt frozen). Recommend: amend production.
5. **CLI vs Python lib** — shell to `llm` CLI (simpler, logs to sqlite) vs `import llm` (faster, no subprocess overhead × up to 450 calls). Recommend: start with CLI, swap if subprocess cost bites.

## Total wall estimate
- Phase 1 (q-gen + harness in parallel): **~60 min**
- Gate: 3-model smoke on 1 question
- Phase 2 (3 eval workers parallel): **~25 min**
- **End-to-end: ~90-120 min** from go.
- **Total spend: <$10** (Sonnet output dominates).

## Related
- [kaggle-submission-design](kaggle-submission-design.md)
- [factory-a-validator-pipeline-built](factory-a-validator-pipeline-built.md)
- [llm-cli-setup-complete](llm-cli-setup-complete.md)


### NOTES

- Blocks: user sign-off on 5 open questions before Codex spawn.
- Parity constraint met with 1-line documented divergence.
- Write-path collision flagged on `harness/prompt.py` — mitigation in execution sub-node.

[[task_17763511977396df]]
