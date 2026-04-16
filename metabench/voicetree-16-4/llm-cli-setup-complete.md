---
color: green
isContextNode: false
agent_name: Ian
---
# Unified LLM CLI Setup — llm + plugins

Installed llm-anthropic + llm-gemini plugins. All three model IDs confirmed. Keys stored in llm keychain + metabench/.env. Gemini working; Claude + GPT need billing top-up.

## Setup

`llm` v0.30 was already installed. Installed two plugins:
```bash
llm install llm-anthropic llm-gemini
```

## Confirmed model IDs

| Alias (use this) | Full ID | Status |
|---|---|---|
| `claude-sonnet-4.6` | `anthropic/claude-sonnet-4-6` | ❌ needs credits |
| `gpt-5.4-mini` | `gpt-5.4-mini` | ❌ needs quota |
| `gemini-2.5-flash-lite` | `gemini/gemini-2.5-flash-lite` | ✅ working |

Note: "Gemini 3 Lite" doesn't exist as a model ID — `gemini-2.5-flash-lite` is the current stable lite-class model.

## API keys

Stored in `metabench/.env` and in llm's keychain:
```
GEMINI_API_KEY=...    (from hch/metagame/.env)
ANTHROPIC_API_KEY=... (new)
OPENAI_API_KEY=...    (new)
```

To re-set a key: `llm keys set <openai|anthropic|gemini>`

## Test commands (ready to run once billing fixed)

```bash
llm -m claude-sonnet-4.6 -s "You are a terse assistant." "Reply with exactly: OK"
llm -m gpt-5.4-mini -s "You are a terse assistant." "Reply with exactly: OK"
llm -m gemini-2.5-flash-lite -s "You are a terse assistant." "Reply with exactly: OK"
```

## Benchmark invocation shape

```bash
llm -m <model> -s "<system_prompt>" "<user_prompt>" --option temperature 0.0
```

- Output → stdout
- Token usage → logged to llm's sqlite DB (`llm logs` to view)
- Exit code 0 on success, non-zero on error

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/.env

### NOTES

- Claude + GPT keys are valid (auth succeeds) but billing is exhausted — not a config issue.
- llm logs token usage to a local sqlite DB, not stderr. Use `llm logs` or `llm logs --json` to inspect cost/usage post-run.
- Scope lock-in: 6 classes × 2 diff × 3 seeds = 36 solo + ~12 portfolios ≈ 50 questions, 3 models = ~150 evals, ~$75 budget.

[[task_1776350178296ze8]]
