---
color: blue
isContextNode: false
agent_name: Timi
---
# Portfolio Spike — Kaggle URL form diagnosis

Checked the active Kaggle bridge configuration after the repeated `/api/sessions` 404s. The runner has been using the `.env` `KAGGLE_JUPYTER_URL` proxied path form (`.../k/311788458/<jwt>/proxy`) plus a separate token, not the bare `https://kkb-production.jupyter-proxy.kaggle.net?token=...` URL the user pasted.

## Active local config
From `kaggle/.env`:
```dotenv
KAGGLE_JUPYTER_URL=https://kkb-production.jupyter-proxy.kaggle.net/k/311788458/<jwt>/proxy
KAGGLE_JUPYTER_TOKEN=eyJhbGci...
```

## Bridge behavior
`kaggle/option_a_bridge/kernel_bridge.py` sets:
- `self.base_url = KAGGLE_JUPYTER_URL.rstrip("/")`
- `self.token = KAGGLE_JUPYTER_TOKEN`
- `list_sessions()` requests `self.base_url + "/api/sessions"` with `?token=self.token`

So the failing request shape has been:
```text
https://kkb-production.jupyter-proxy.kaggle.net/k/311788458/<jwt>/proxy/api/sessions?token=<jwt>
```

## Runner note
`kaggle/scripts/run_portfolio_spike.py` only uses a pasted notebook URL if `--notebook-url` is passed explicitly. In the runs so far, that flag was not used, so the script used `.env`.

Its current `parse_notebook_url()` extracts only scheme + host from a pasted URL, so if we do decide to pass the bare `https://kkb-production.jupyter-proxy.kaggle.net?token=...` form explicitly, the runner will use host-only base URL rather than the `/k/.../proxy` path form.

## Updated belief
No, the runner has not been using the exact bare `?token=` URL the user pasted. It has been using the proxied `.env` URL plus separate token, which may be relevant to the repeated 404s.

## Related

- [portfolio-spike-v1-kaggle-pilot-retry-still-404-2026-04-16](portfolio-spike-v1-kaggle-pilot-retry-still-404-2026-04-16.md)

[[task_1776337456301t32]]
