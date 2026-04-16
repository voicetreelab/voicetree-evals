---
color: green
isContextNode: false
agent_name: Max
---
# Codex MetaGame v2 spec + non-duplicating child handoff

Wrote the new `hch/codex_metagame_v2/EXPERIMENT_SPEC.md`, clarified that this branch must not duplicate Meg's simpler flowshop spike, and spawned a `Codex` child agent (`Mei`) to implement the harder full coupled job-shop local Gemini spike.

## What was done
- Created `/Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/EXPERIMENT_SPEC.md`.
- Scoped the new branch to a **full coupled two-factory job-shop** benchmark with full schedule output and verification.
- Explicitly separated this from Meg's already-running task, which is a **simpler Johnson-style two-stage flowshop** with permutation output.
- Spawned child agent `Mei` (`Codex`) to implement the local Gemini spike under `hch/codex_metagame_v2`.

## Key spec decisions
- One canonical prompt only; no `greedy/exhaustive/smart` arm split.
- Smoke tier `3x4`, main spike tier `4x5`.
- Exact offline gold required via OR-Tools CP-SAT.
- Full schedule output required for verification; this is the main distinction from Meg's flowshop permutation task.
- Local Gemini API spike only; Kaggle packaging is explicitly out of scope.

## Handoff boundary for the child agent
- Owned write scope: `/Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/**`
- Reuse allowed from `hch/metagame/` for Gemini client / timeout / analyzer patterns.
- Avoid mutating the older TSP code unless necessary.
- Deliver new experiment insight relative to Meg's simpler flowshop: does the richer coupled structure create stronger metacog signal, or mostly parser/output overhead?

## Early blocker guidance sent to the child
- Confirmed parent env file exists at `/Users/bobbobby/repos/voicetree-evals/metabench/hch/metagame/.env`; child was told it may safely fall back to that path instead of requiring a copied secret.
- Confirmed `ortools` is not currently installed; child was told to treat that explicitly as a dependency / run blocker and document it if it prevents the first smoke run.

## Current status at node creation
- Spec is written.
- Child `Mei` is running and has begun reading the spec plus existing harness code.
- No implementation files beyond the spec have landed yet at this point.

## DIFF

```
diff --git a/hch/codex_metagame_v2/EXPERIMENT_SPEC.md b/hch/codex_metagame_v2/EXPERIMENT_SPEC.md
new file mode 100644
--- /dev/null
+++ b/hch/codex_metagame_v2/EXPERIMENT_SPEC.md
@@
+# Codex MetaGame v2 - Local Gemini Spike Spec
+...
+## Deliberate non-duplication vs Meg
+Another agent, Meg, is already exploring a simpler Johnson-style two-stage flowshop.
+This v2 spike stays on the harder coupled two-factory job-shop with full schedule output.
+...
+## Child-agent implementation target
+Implement a runnable local Gemini spike under `hch/codex_metagame_v2` with smoke run first, then the largest safe fuller spike.
```

## Complexity: medium

This is a new benchmark-spec artifact plus a cross-agent handoff boundary. The implementation complexity is deferred, but the design constraints and non-duplication requirements needed careful coordination.

## Files Changed

- /Users/bobbobby/repos/voicetree-evals/metabench/hch/codex_metagame_v2/EXPERIMENT_SPEC.md

### NOTES

- The non-duplication constraint is substantive, not cosmetic: Meg's task is a two-stage flowshop with permutation output, while this branch is the harder coupled job-shop with full schedule verification.
- This branch may end up revealing whether the added coupled-structure signal is worth the much heavier parsing / verification burden.
- If `ortools` becomes the gating issue, a documented `3x4` exact fallback is preferable to silently downgrading the benchmark definition.

## Related

- [trajectory-post-tsp-synthesis](trajectory-post-tsp-synthesis.md)
- [recommended-problem-setup-post-tsp](recommended-problem-setup-post-tsp.md)

[[task_1776319758322uan_1]]
