---
color: green
isContextNode: false
agent_name: Ama
---
# Kaggle 503 Diagnosis — Provider Availability, Not Wrong Slug

Answered: the Claude/GPT 503 fast-fails were Kaggle-side LLM-proxy availability rejections, not a wrong model slug. Same slugs passed 1-row smoke immediately before the full sweeps; error is provider 503 'model currently unavailable', not 404; Gemini on the same bridge passed — so bridge/config was healthy. Distinct from the earlier runtime-default drift (blocker #2), which was already fixed before these sweeps.

# Kaggle 503 Diagnosis

**Question asked:** "do we know why we were getting 503? using wrong model name?"

**Answer:** No, not a wrong model name. The 503s were Kaggle-side LLM-proxy availability rejections for Claude and GPT at the time of the full sweeps.

## Evidence

### 1. Same slug passed smoke immediately before the full sweep
From `kaggle-production-blockers-and-workarounds.md` §3:
> both Claude and GPT succeeded on 1-row smoke probes before the full sweeps

If the slug were wrong, the 1-row smoke would have failed with the same error. It didn't.

### 2. Error shape = provider availability, not model-not-found
Every row in `kaggle_submission/kaggle/output/kaggle-production-full-claude-sonnet-4.6-20260416T202925Z/bridge_stdout.txt` logs:
```
InternalServerError: Error code: 503 - {'message': 'The requested model is currently unavailable.', 'type': 'invalid_request_error'}
```
This is a **503** with `invalid_request_error` type carrying an *availability* message — upstream provider rejection. A wrong slug would surface as a 404 / `model_not_found` at the SDK boundary, not a 503 from the provider.

### 3. Fast-fail timing is consistent with upstream rejection
All rows failed at **1.3–1.5s**, which is network round-trip plus a provider-side 503, not inference timing and not timeout-on-our-side. Uniform fast-fail across every (class, difficulty, seed) is a classic provider-throttle/availability signature.

### 4. Gemini on the same bridge worked
`kaggle-production-full-google_gemini-3-flash-preview-20260416T173202Z` was a clean pass on the same kernel/bridge concurrently — so the bridge, verifier bundle, task.py, and `.evaluate()` path were healthy. Only the Claude and GPT provider routes were rejecting.

## Distinction vs. blocker #2 (runtime-default drift)
There were actually **two different problems** in this run. Don't conflate them:

| Blocker | Cause | Fix |
|---|---|---|
| #2 runtime-default drift | Live Jupyter kernel persisted `kbench.llm.model` across bridge calls — a nominal runtime-default run inherited an earlier GPT override. A *slug-shape* bug (wrong model picked up implicitly). | Stopped trusting `runtime-default`; passed explicit slugs on every full launch. |
| #3 503 availability | Kaggle LLM proxy rejected explicit Claude + GPT slugs with 503 during the full sweeps. A *provider-side availability* issue, unrelated to what slug we sent. | None applied; Gemini carried the canonical pass. |

**Blocker #3 happened AFTER blocker #2 was fixed**, with known-good explicit slugs. So it's not slug drift either.

## Net conclusion
The 503 is **not** explained by a wrong model name. The signal points to Kaggle's LLM proxy being unable to serve Claude and GPT during that window. The right follow-up is retry-with-backoff in the bridge (and/or a later re-run), not a slug change.

## Residual uncertainty
- We don't have a Kaggle-side status / log from that exact window to *prove* proxy-level throttle vs. an upstream provider outage — only the shape and timing of the error plus the smoke-vs-sweep asymmetry. Both possibilities reduce to 'not our slug'.
- If a follow-up retry also 503s on the same slugs, worth opening a Kaggle forum thread / contacting support with the request timestamps.

### NOTES

- Do not change the Claude or GPT slugs based on this event. Slugs were validated by smoke on the same kernel minutes before the sweep.
- Consider adding per-row retry-with-exponential-backoff to the bridge before re-running — a single 503 killed each row's plan turn with no retry.
- Keep blocker #2 (runtime-default drift) and blocker #3 (503 availability) separate in any writeup — conflating them hides the real provider-availability risk from the Kaggle side.

## Related

- [kaggle-production-run-complete](kaggle-production-run-complete.md)
- [kaggle-production-blockers-and-workarounds](kaggle-production-blockers-and-workarounds.md)

[[kaggle-production-run-complete_1]]
