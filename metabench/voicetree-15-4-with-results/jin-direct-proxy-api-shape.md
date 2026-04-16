---
color: blue
isContextNode: false
agent_name: Jin
---
# Proxy API shape + kbench feature delta

Proxy is fully OpenAI-compatible. Model listing 200 from anywhere. Inference 403 (IP-locked). kbench only adds ~30 LOC of scaffolding — all parsers already embedded in task files.

## Proxy Endpoints

| Endpoint | Method | IP restriction | Status |
|----------|--------|----------------|--------|
| `https://mp-staging.kaggle.net/models` | GET | None | 200 ✓ |
| `https://mp-staging.kaggle.net/models/openapi/v1/chat/completions` | POST | Kaggle-only | 403 from local |

Auth: `Authorization: Bearer <MODEL_PROXY_API_KEY>` for both.  
Body: `{"model":"<id>","messages":[...],"max_tokens":32768}` (OpenAI format).  
47 models available: Claude family, Gemini family (incl. 3 Pro), GPT-5.4 family, DeepSeek, Gemma.

## kbench Feature Delta

| Feature | kbench | Direct runner | Impact |
|---------|--------|---------------|--------|
| Task registration | `@kbench.task` | No-op (stub) | Negligible |
| Metacog data storage | `assert_true(expectation=...)` | Extract from trajectory directly | Medium — explicit extraction |
| `.run.json` format | Built-in | ~10 LOC replication | Low |
| Retry on error | Built-in | Add if needed | Low |
| Token tracking | Bridge overhead | `usage` field from API response | Already in script |

**Key:** All parsers (`_parse_hch_trajectory`, `_parse_vanilla`, `_judge_answer`) are embedded in every task file and load cleanly with kbench stubbed out.

[[jin-direct-proxy-spike-overview]]
