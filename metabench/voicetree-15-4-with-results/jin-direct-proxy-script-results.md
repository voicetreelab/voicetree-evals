---
color: blue
isContextNode: false
agent_name: Jin
---
# Spike script (76 LOC) + test run results

Script loads task files correctly (kbench stub works). Model listing confirmed 200. Inference call confirmed 403 from local IP. End-to-end q41 test blocked by IP restriction; timing comparison not possible from dev machine.

## Script: direct_runner_spike.py (key sections)

```python
# Load task file with kbench stubbed out
def load_task(path):
    stub = types.ModuleType("kaggle_benchmarks")
    stub.task = lambda **_: (lambda fn: fn)  # @kbench.task becomes no-op
    stub.assertions = types.SimpleNamespace(assert_true=lambda *a, **kw: None)
    sys.modules["kaggle_benchmarks"] = stub
    spec = importlib.util.spec_from_file_location("_task", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod  # mod.PROMPT, mod.GOLD_ANSWER, mod._parse_hch_trajectory etc. all available

# Direct proxy call (OpenAI-compat)
def chat(model, prompt, max_tokens=32768):
    r = requests.post(f"{PROXY_BASE}/v1/chat/completions", headers=HEADERS,
        json={"model":model,"messages":[{"role":"user","content":prompt}],"max_tokens":max_tokens})
    data = r.json()
    return data["choices"][0]["message"]["content"], data.get("usage",{}), elapsed

# JSONL output shape
{"question_id":41,"arm":"hch","model":"google/gemini-2.5-flash",
 "answer":"46.24","gold":"46.24","judge_pass":true,"p_correct":0.95,
 "input_tokens":1234,"output_tokens":567,"elapsed_s":14.2,"raw_response":"..."}
```

## Test Results

| Test | Result |
|------|--------|
| `load_task('q41_hch.py')` | PASS — GOLD=46.24, PROMPT loaded, parsers accessible |
| `--list-models` | PASS — 200, 47 models, ~0.26s latency |
| `chat()` q41 (local) | BLOCKED — 403 "token can’t be used from this IP" |
| Timing estimate | Bridge ~15-20s; direct ~same (model latency dominates; bridge adds ~2-5s) |

## Files Changed

- kaggle/scripts/direct_runner_spike.py

### NOTES

- kbench stub approach is clean: task module fully imports, all helpers available. No mock patching needed.
- PROXY_BASE must be MODEL_PROXY_URL (https://mp-staging.kaggle.net/models/openapi). The /v1/models discovery URL is the base without /openapi.

[[jin-direct-proxy-spike-overview]]
