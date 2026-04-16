---
color: green
isContextNode: false
agent_name: Ren
---
# SCIP-Jack blockers for the composite spike

Checked the official SCIP-Jack source path and the solver/problem fit. Two blockers emerged immediately: the official site no longer offers a direct public download, and SCIP-Jack's supported problem classes do not match the spike's full Steiner-plus-coloring objective.

## Official source checked
`https://scipjack.zib.de/`

## Local command used
```bash
curl -L https://scipjack.zib.de/ | rg -n "Download|INSTALL|\.tar|\.tgz|\.zip|Daniel Rehfeldt|request"
```

Observed output excerpt:
```text
169: <h1 id="download">Download</h1>
170: ... SCIP-Jack is no longer distributed as part of the SCIP Optimization Suite. It can still be obtained on request ...
175: <p> See the INSTALL file in the SCIP-Jack directory.</p>
```

## Why this blocks quick setup
- The official page does not expose a public tarball/zip link that I can fetch directly in this automated turn.
- The stated acquisition path is to obtain SCIP-Jack "on request" by contacting Daniel Rehfeldt.
- Because the distribution is request-gated, there is no concrete installable artifact to build from here.

## Why SCIP-Jack is not a direct exact solver for this spike anyway
The spike objective is:
```text
total_cost = cable_cost + 15 * chromatic_number(active interference graph)
```

SCIP-Jack's documented problem classes are Steiner-tree-family variants. That matches the cable-connection part, but not the exact graph-coloring term over the active induced interference graph.

Practical implication:
- SCIP-Jack could maybe solve a cable-only relaxation.
- It is not a direct drop-in exact solver for the full composite optimum used by `steiner_coloring_gold.py` without a new formulation layer or decomposition strategy.

## Conclusion
The SCIP-Jack route is blocked on both access and problem mismatch, so it is not the quick exact-solve path for this task.

supports [[steiner-coloring-n12k4-exact-solve-verdict]]
