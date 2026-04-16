---
color: blue
isContextNode: false
agent_name: Ivan
---
# Parity architecture — LocalLLM adapter, 1-line divergence from Kaggle

`harness/runner.py` already supports parity: `_prompt_once` only needs `.prompt(text, temperature=0)` → str. System prompt is the only gap (Kaggle injects via `kbench.chats.new(system_instructions=...)`; local path needs constructor-bound system). Documented, no runner.py changes.

## What runner.py already gives us

```python
# harness/runner.py:_prompt_once
if hasattr(llm, "prompt"):
    try: return llm.prompt(prompt_text, temperature=0)
    except TypeError: return llm.prompt(prompt_text)
```

Any object with `.prompt(text, temperature=0) → str | obj.content` works. `_chat_session` guards the kbench import with try/except, falling back to `nullcontext()`.

## The one real gap

On Kaggle: `kbench.chats.new(name, system_instructions=system_prompt)` context manager pushes system into the active chat so `kbench.llm.prompt(user_text)` includes it. **Locally:** `nullcontext()` drops the system prompt silently.

## Fix: bind system at LocalLLM construction

```python
# metabench/kaggle_submission/eval_harness/local_llm.py
import subprocess
class LocalLLM:
    def __init__(self, model: str, system_prompt: str):
        self.model = model          # e.g. "gemini-flash-latest"
        self.system = system_prompt
    def prompt(self, text: str, *, temperature: float = 0.0) -> str:
        cmd = ["llm", "-m", self.model, "-s", self.system,
               "--option", "temperature", str(temperature), text]
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=_TIMEOUT_CAP)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip() or "llm CLI failed")
        return r.stdout.strip()
```

Each `run_instance()` call constructs a fresh `LocalLLM(model, build_system_prompt())`. No changes to `harness/runner.py`.

## Why shell the CLI (not import llm)
- Ian already configured CLI + keys + plugins
- Token logs automatic via `llm logs`
- Matches Ian's smoke-test invocation exactly
- Swappable if subprocess overhead bites (see open Q5 on parent)

## Parity audit

| Layer | Kaggle | Local |
|---|---|---|
| `run_instance()` signature | same | same |
| `harness/{prompt,protocol,render_nl,scoring,runner}.py` | byte-identical | byte-identical |
| Verifiers/generators | same | same |
| System prompt | `kbench.chats.new(system_instructions=...)` | `LocalLLM(system_prompt=...)` constructor |
| `.prompt(text, temperature)` contract | `kbench.llm` ModelProxy | `LocalLLM` subprocess wrapper |
| Wall 1800s, CF fork, exec turns | same | same |

**Divergence = 1 attribute set path.** Minimum physically possible given we can't spin up Kaggle's model proxy locally.

## Cannot-meet-parity escape hatch

If user rejects constructor-bound system → alternative is a `local_chats` shim module matching `kbench.chats.new()` API exactly with a thread-local that LocalLLM reads on `.prompt()`. More code, identical call-site shape. Flagging as option but recommending constructor path (simpler + equally verifiable).


parity [[factory-a-eval-plan-v1]]
