---
isContextNode: false
---
# Problem classes exhibiting genuine decomposition uncertainty
Summary of what I dug up. Ranked by how sharply each matches your property (subproblems exist, boundaries are non-obvious, decomposition choice is load-bearing), with notes on gold-scalability and harness fit.
Tier 1: structurally decomposable but decomposition is NP-hard itself
These are the sharpest hits. The problem decomposes, but how you decompose determines solution quality, and finding the optimal decomposition is a known hard problem.
1. Tree-decomposition-dependent graph problems (vertex cover, independent set, dominating set, q-coloring, weighted coloring on dense graphs)
The core property is spelled out cleanly: it is NP-complete to determine whether a given graph G has treewidth at most a given variable k Wikipedia, and there is no known polynomial-time constant-factor approximation algorithm for treewidth — it is an open problem whether one exists Ethz. You solve the original problem via dynamic programming on the tree decomposition, but the quality of a tree decomposition is measured by its width; finding the smallest-width decomposition is hard, and using a non-optimal tree-decomposition affects the running time of downstream DP ScienceDirect. The standard approach is repeated balanced separator search, which is the foundation of all treewidth approximation algorithms arXiv — and those separators are exactly the "subproblem boundaries" a solver must pick.
Why this fits your property precisely:

Genuine subproblems exist (the bags after you cut on a separator)
Where to cut is non-obvious (NP-hard to find optimally)
Choice is load-bearing (bad cuts → exponentially larger DP)
Gold scales (you can use a known-good tree decomposition from a solver to establish ground truth)

Concrete benchmark shape: give a 100-200 node graph, ask for max independent set or min vertex cover. Good decomposition (finding a small separator, solving two halves, reconciling) gets close to optimal quickly. Naive decomposition blows up. Model must reason about which vertex set separates the graph well — that's the metacog.
2. Bayesian network inference via variable elimination
Same core issue, different skin: choosing the optimal VE ordering is an NP-hard problem Ermongroup, and heuristics (min-neighbors, min-weight, min-fill) give meaningfully different runtimes and memory blowups. Unfortunately, the problem of finding the treewidth of a graph is NP-hard and therefore in practice we have to resort to various heuristic alternatives University of Texas at Dallas.
This is really the same math as #1, but cast as a probabilistic reasoning task rather than a graph problem — which is a better surface for metacog testing because the model has to reason about "which variables are most entangled, eliminate the peripheral ones first." That IS the decomposition choice.


cool. I think let's make two spikes for these questions as well.

let's use the evolved local harness, single gemini multi turn spike structure 

where the todo list / subtask plan state is just saved as a string 
