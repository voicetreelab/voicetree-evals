---
color: blue
isContextNode: false
agent_name: Jin
---
# Direct-proxy runner spike — findings + recommendation

Spike complete. Proxy is OpenAI-compatible and reachable. Chat/inference is IP-locked (403 from dev machine). Direct runner is 76 LOC and correct. Viable migration: Kaggle batch kernel submission via Kaggle API — resolves live-session dependency permanently.

## Verdict: Viable-with-Caveats

Direct proxy works; IP restriction means it must run FROM Kaggle's network (not dev laptop).

**Migration path (~1 day):**
1. Use `direct_runner_spike.py` as standalone Kaggle notebook script (no kbench)
2. Submit via `kaggle.api.kernels_push()` as batch kernel — runs inside Kaggle network, hits proxy directly
3. Fetch results via `kaggle.api.kernels_output()` when done

**Solves:** no live Jupyter session, no arm contention, no token expiry  
**Doesn't solve:** still Kaggle-dependent; batch cold-start ~60-120s (vs 0s live)

**Alternative (fully Kaggle-free):** Request proxy IP-unlock from Kaggle benchmark team.

### NOTES

- Model listing (GET /models) is accessible from any IP with auth. Only inference is IP-locked.
- Script is NOT committed to git — at kaggle/scripts/direct_runner_spike.py for user review.

[[task_17762550915227eo]]
