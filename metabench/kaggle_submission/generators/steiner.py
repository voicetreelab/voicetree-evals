from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from random import Random
from typing import Any

from ortools.sat.python import cp_model

FREQ_PENALTY = 15
ANSWER_CONTRACT = 'Object with "edges": [["Port", "Bay"], ...] and "frequencies": {"Port": 1, ...}.'
NAME_POOL = (
    "Port",
    "Bay",
    "Cliff",
    "Pine",
    "Rock",
    "Dune",
    "Mill",
    "Cape",
    "Harbor",
    "Grove",
    "Ridge",
    "Cove",
)
DIFFICULTY_CONFIGS = {
    "medium": {
        "n": 8,
        "k": 4,
        "n_terminals": 3,
        "min_baseline_gap_pct": 15.0,
        "require_coupling": True,
        "max_generation_attempts": 80,
    },
    "hard": {
        "n": 12,
        "k": 4,
        "n_terminals": 3,
        "min_baseline_gap_pct": 15.0,
        "require_coupling": True,
        "max_generation_attempts": 120,
    },
}


@dataclass(frozen=True)
class EdgeSpec:
    u: str
    v: str
    cost: int

    @property
    def key(self) -> tuple[str, str]:
        return canonical_edge(self.u, self.v)


def generate(seed: int, difficulty: str) -> dict[str, Any]:
    if difficulty not in DIFFICULTY_CONFIGS:
        allowed = ", ".join(sorted(DIFFICULTY_CONFIGS))
        raise ValueError(f"unknown difficulty {difficulty!r}; expected one of: {allowed}")
    return _build_instance(seed=seed, difficulty=difficulty, **DIFFICULTY_CONFIGS[difficulty])


def canonical_edge(u: str, v: str) -> tuple[str, str]:
    if u == v:
        raise ValueError(f"self loops are not allowed: {u}")
    return (u, v) if u < v else (v, u)


def ordered_edges(
    edge_keys: set[tuple[str, str]] | tuple[tuple[str, str], ...] | list[tuple[str, str]],
    villages: tuple[str, ...],
) -> list[tuple[str, str]]:
    order = {village: index for index, village in enumerate(villages)}
    return sorted(edge_keys, key=lambda item: (order[item[0]], order[item[1]]))


def ordered_edge_specs(edges: tuple[EdgeSpec, ...], villages: tuple[str, ...]) -> list[EdgeSpec]:
    order = {village: index for index, village in enumerate(villages)}
    return sorted(edges, key=lambda edge: (order[edge.u], order[edge.v]))


def active_villages_for_edges(
    terminals: tuple[str, ...],
    edge_keys: set[tuple[str, str]] | tuple[tuple[str, str], ...] | list[tuple[str, str]],
    villages: tuple[str, ...],
) -> tuple[str, ...]:
    active = set(terminals)
    for u, v in edge_keys:
        active.add(u)
        active.add(v)
    return tuple(village for village in villages if village in active)


def interference_graph(
    active_villages: tuple[str, ...] | list[str],
    interference_pairs: tuple[tuple[str, str], ...],
) -> dict[str, set[str]]:
    active = set(active_villages)
    graph = {village: set() for village in active}
    for u, v in interference_pairs:
        if u in active and v in active:
            graph[u].add(v)
            graph[v].add(u)
    return graph


def greedy_color_active(
    active_villages: tuple[str, ...],
    villages: tuple[str, ...],
    interference_pairs: tuple[tuple[str, str], ...],
) -> dict[str, int]:
    graph = interference_graph(active_villages, interference_pairs)
    order = {village: index for index, village in enumerate(villages)}
    assignment: dict[str, int] = {}
    nodes = sorted(active_villages, key=lambda village: (-len(graph[village]), order[village]))
    for village in nodes:
        blocked = {assignment[neighbor] for neighbor in graph[village] if neighbor in assignment}
        color = 1
        while color in blocked:
            color += 1
        assignment[village] = color
    return {village: assignment[village] for village in villages if village in assignment}


def _build_instance(
    *,
    seed: int,
    difficulty: str,
    n: int,
    k: int,
    n_terminals: int,
    min_baseline_gap_pct: float,
    require_coupling: bool,
    max_generation_attempts: int,
) -> dict[str, Any]:
    last_reason = "no attempt made"

    for attempt in range(max_generation_attempts):
        attempt_seed = seed if attempt == 0 else seed * 10_000 + attempt
        villages, terminals, edges, interference_pairs = _generate_candidate(
            seed=attempt_seed,
            n=n,
            k=k,
            n_terminals=n_terminals,
        )

        candidate = {
            "villages": list(villages),
            "terminals": list(terminals),
            "edges": [{"u": edge.u, "v": edge.v, "cost": edge.cost} for edge in ordered_edge_specs(edges, villages)],
            "interference_pairs": [list(pair) for pair in ordered_edges(interference_pairs, villages)],
        }

        baseline_submission = build_baseline_answer(villages, terminals, edges, interference_pairs)
        baseline_check = _evaluate_submission(candidate, baseline_submission)
        if not baseline_check["feasible"]:
            raise RuntimeError(f"internal error: baseline answer is infeasible: {baseline_check['failure_reason']}")
        baseline_cost = int(baseline_check["computed_cost"])

        cable_only_submission, cable_only_cost = _solve_edge_only_then_color(candidate, seed=attempt_seed)
        cable_only_check = _evaluate_submission(candidate, cable_only_submission)
        if not cable_only_check["feasible"] or cable_only_check["computed_cost"] != cable_only_cost:
            raise RuntimeError(
                "internal error: cable-only exact solution failed verification: "
                f"{cable_only_check['failure_reason']}"
            )

        gold_submission, gold_cost = _solve_joint_optimum(candidate, seed=attempt_seed)
        gold_check = _evaluate_submission(candidate, gold_submission)
        if not gold_check["feasible"] or gold_check["computed_cost"] != gold_cost:
            raise RuntimeError(
                "internal error: optimal exact solution failed verification: "
                f"{gold_check['failure_reason']}"
            )

        baseline_gap_pct = 100.0 * (baseline_cost - gold_cost) / gold_cost
        coupling_gap = cable_only_cost - gold_cost
        accepted = baseline_gap_pct >= min_baseline_gap_pct
        if require_coupling:
            accepted = accepted and coupling_gap > 0
        if not accepted:
            last_reason = f"baseline_gap_pct={baseline_gap_pct:.2f}, coupling_gap={coupling_gap}"
            continue

        instance = {
            "class": "steiner",
            "difficulty": difficulty,
            "seed": seed,
            "n": n,
            "k": k,
            "n_terminals": n_terminals,
            "freq_penalty": FREQ_PENALTY,
            "villages": list(villages),
            "terminals": list(terminals),
            "edges": candidate["edges"],
            "interference_pairs": candidate["interference_pairs"],
            "baseline_submission": baseline_check["normalized_submission"],
            "baseline_cost": baseline_cost,
            "baseline_gap_pct": baseline_gap_pct,
            "cable_only_submission": cable_only_check["normalized_submission"],
            "cable_only_cost": cable_only_cost,
            "gold_submission": gold_check["normalized_submission"],
            "gold_cost": gold_cost,
            "answer_contract": ANSWER_CONTRACT,
        }
        instance["problem_statement"] = render_problem(instance)
        return instance

    raise RuntimeError(
        "failed to generate a Steiner instance with enough headroom after "
        f"{max_generation_attempts} attempts; last rejection was {last_reason}"
    )


def build_baseline_answer(
    villages: tuple[str, ...],
    terminals: tuple[str, ...],
    edges: tuple[EdgeSpec, ...],
    interference_pairs: tuple[tuple[str, str], ...],
) -> dict[str, Any]:
    root = terminals[0]
    edge_lookup = {edge.key: edge.cost for edge in edges}
    selected: set[tuple[str, str]] = set()
    for terminal in terminals[1:]:
        selected.update(shortest_path_edges(root, terminal, edge_lookup))
    spanning = _kruskal_spanning_tree(selected, edge_lookup)
    pruned = _prune_nonterminal_leaves(spanning, terminals)
    active = active_villages_for_edges(terminals, pruned, villages)
    frequencies = greedy_color_active(active, villages, interference_pairs)
    return {
        "edges": [list(edge) for edge in ordered_edges(pruned, villages)],
        "frequencies": frequencies,
    }


def shortest_path_edges(
    start: str,
    goal: str,
    edge_lookup: dict[tuple[str, str], int],
) -> list[tuple[str, str]]:
    adjacency: dict[str, list[tuple[str, int]]] = {}
    for (u, v), cost in edge_lookup.items():
        adjacency.setdefault(u, []).append((v, cost))
        adjacency.setdefault(v, []).append((u, cost))

    queue: list[tuple[int, str]] = [(0, start)]
    dist = {start: 0}
    prev: dict[str, str] = {}
    while queue:
        best_dist, node = heapq.heappop(queue)
        if node == goal:
            break
        if best_dist != dist.get(node):
            continue
        for neighbor, cost in adjacency.get(node, []):
            candidate = best_dist + cost
            if candidate < dist.get(neighbor, math.inf):
                dist[neighbor] = candidate
                prev[neighbor] = node
                heapq.heappush(queue, (candidate, neighbor))

    if goal not in dist:
        raise RuntimeError(f"no path between {start} and {goal}")

    path_edges: list[tuple[str, str]] = []
    cursor = goal
    while cursor != start:
        parent = prev[cursor]
        path_edges.append(canonical_edge(cursor, parent))
        cursor = parent
    path_edges.reverse()
    return path_edges


def render_problem(instance: dict[str, Any]) -> str:
    villages = tuple(instance["villages"])
    edges = tuple(EdgeSpec(edge["u"], edge["v"], int(edge["cost"])) for edge in instance["edges"])
    interference_pairs = tuple(tuple(pair) for pair in instance["interference_pairs"])
    edge_lines = [f"- {edge.u}-{edge.v}: cost {edge.cost}" for edge in ordered_edge_specs(edges, villages)]
    interference_lines = [f"- {u} / {v}" for u, v in ordered_edges(interference_pairs, villages)]
    baseline_summary = solution_summary(instance, instance["baseline_submission"], int(instance["baseline_cost"]))
    return f"""Coastal Emergency scenario:
Storm season is coming. You need to wire a resilient emergency communication network across coastal villages.

You may choose any subset of the available cable links, but the chosen cable network must be a single connected tree that includes every required terminal village.
Every village that lies in your chosen network is active and must be assigned a radio frequency.
If an interference pair is active on both ends, those two villages must use different frequencies.

Objective:
total_cost = sum(cable costs used) + {FREQ_PENALTY} * num_frequencies_used

Villages:
- {", ".join(instance["villages"])}

Required terminals:
- {", ".join(instance["terminals"])}

Available cable links:
{chr(10).join(edge_lines)}

Interference pairs:
{chr(10).join(interference_lines)}

Rules:
- Your cable choice must be a tree, not a cyclic network.
- All required terminals must lie in one connected component.
- Frequencies matter only for active villages in the chosen network.
- If you stop immediately or fail to produce a valid answer, the baseline below is what gets scored.

Baseline total cost: {instance["baseline_cost"]}
Baseline answer summary:
{baseline_summary}

Answer contract hint: {instance["answer_contract"]}
"""


def solution_summary(
    instance: dict[str, Any],
    answer: dict[str, Any],
    total_cost: int | None = None,
) -> str:
    villages = tuple(instance["villages"])
    terminals = tuple(instance["terminals"])
    edge_lookup = {
        canonical_edge(edge["u"], edge["v"]): int(edge["cost"])
        for edge in instance["edges"]
    }
    raw_edges = {
        canonical_edge(*edge)
        for edge in answer.get("edges", [])
        if isinstance(edge, list | tuple) and len(edge) == 2
    }
    ordered = ordered_edges(raw_edges, villages)
    edge_cost = sum(edge_lookup[edge] for edge in ordered if edge in edge_lookup)
    active = active_villages_for_edges(terminals, raw_edges, villages)
    frequencies = answer.get("frequencies", {})
    active_freqs = {village: frequencies[village] for village in active if village in frequencies}
    used_colors = sorted(set(active_freqs.values()))
    total = total_cost if total_cost is not None else edge_cost + FREQ_PENALTY * len(used_colors)
    edge_bits = ", ".join(f"{u}-{v}({edge_lookup[(u, v)]})" for u, v in ordered)
    freq_bits = ", ".join(f"{village}={active_freqs.get(village, '?')}" for village in active)
    return (
        f"Edges: {edge_bits}\n"
        f"Active villages: {', '.join(active)}\n"
        f"Frequencies: {freq_bits}\n"
        f"Edge cost: {edge_cost}\n"
        f"Frequencies used: {len(used_colors)}\n"
        f"Total cost: {total}"
    )


def _generate_candidate(
    *,
    seed: int,
    n: int,
    k: int,
    n_terminals: int,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[EdgeSpec, ...], tuple[tuple[str, str], ...]]:
    rng = Random(seed)
    villages = tuple(NAME_POOL[:n])
    points = {village: (rng.randint(0, 30), rng.randint(0, 30)) for village in villages}
    complete_edges: list[tuple[int, tuple[str, str]]] = []
    for index, u in enumerate(villages):
        for v in villages[index + 1 :]:
            x1, y1 = points[u]
            x2, y2 = points[v]
            cost = max(2, int(round(math.hypot(x1 - x2, y1 - y2))))
            complete_edges.append((cost, canonical_edge(u, v)))

    mst_edges = _minimum_spanning_tree(villages, complete_edges)
    selected = set(mst_edges)
    neighbors: dict[str, list[tuple[int, str]]] = {village: [] for village in villages}
    for cost, (u, v) in complete_edges:
        neighbors[u].append((cost, v))
        neighbors[v].append((cost, u))
    for village in villages:
        for _, other in sorted(neighbors[village], key=lambda item: (item[0], item[1]))[:k]:
            selected.add(canonical_edge(village, other))

    edge_costs = {edge: cost for cost, edge in complete_edges}
    edges = tuple(
        EdgeSpec(u=edge[0], v=edge[1], cost=edge_costs[edge])
        for edge in ordered_edges(selected, villages)
    )
    terminals = tuple(sorted(rng.sample(list(villages), n_terminals), key=lambda item: villages.index(item)))
    interference_pairs = _build_interference_pairs(rng, villages, terminals, edge_costs)
    return villages, terminals, edges, interference_pairs


def _minimum_spanning_tree(
    villages: tuple[str, ...],
    complete_edges: list[tuple[int, tuple[str, str]]],
) -> set[tuple[str, str]]:
    parent = {village: village for village in villages}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(left: str, right: str) -> bool:
        root_left = find(left)
        root_right = find(right)
        if root_left == root_right:
            return False
        parent[root_right] = root_left
        return True

    selected: set[tuple[str, str]] = set()
    for _, (u, v) in sorted(complete_edges, key=lambda item: (item[0], item[1][0], item[1][1])):
        if union(u, v):
            selected.add(canonical_edge(u, v))
        if len(selected) == len(villages) - 1:
            break
    return selected


def _build_interference_pairs(
    rng: Random,
    villages: tuple[str, ...],
    terminals: tuple[str, ...],
    edge_costs: dict[tuple[str, str], int],
) -> tuple[tuple[str, str], ...]:
    root = terminals[0]
    seed_edges: set[tuple[str, str]] = set()
    for terminal in terminals[1:]:
        seed_edges.update(shortest_path_edges(root, terminal, edge_costs))
    active = list(active_villages_for_edges(terminals, seed_edges, villages))
    if len(active) < 3:
        active = list(villages)

    interference: set[tuple[str, str]] = set()
    triangle_count = 2 if len(villages) >= 7 else 1
    rng.shuffle(active)
    used: set[str] = set()
    for _ in range(triangle_count):
        pool = [village for village in active if village not in used]
        if len(pool) < 3:
            pool = list(villages)
        anchor = pool[0]
        near = sorted(
            [village for village in villages if village != anchor],
            key=lambda village: (edge_costs.get(canonical_edge(anchor, village), 10_000), village),
        )
        trio = [anchor]
        for village in near:
            if village not in trio:
                trio.append(village)
            if len(trio) == 3:
                break
        if len(trio) == 3:
            used.update(trio)
            for index, u in enumerate(trio):
                for v in trio[index + 1 :]:
                    interference.add(canonical_edge(u, v))

    extras = sorted(edge_costs, key=lambda item: (edge_costs[item], item[0], item[1]))
    rng.shuffle(extras)
    for edge in extras:
        if len(interference) >= triangle_count * 3 + 2:
            break
        interference.add(edge)
    return tuple(ordered_edges(interference, villages))


def _kruskal_spanning_tree(
    edge_keys: set[tuple[str, str]],
    edge_lookup: dict[tuple[str, str], int],
) -> set[tuple[str, str]]:
    nodes = {node for edge in edge_keys for node in edge}
    parent = {node: node for node in nodes}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(left: str, right: str) -> bool:
        root_left = find(left)
        root_right = find(right)
        if root_left == root_right:
            return False
        parent[root_right] = root_left
        return True

    chosen: set[tuple[str, str]] = set()
    for edge in sorted(edge_keys, key=lambda item: (edge_lookup[item], item[0], item[1])):
        if union(edge[0], edge[1]):
            chosen.add(edge)
    return chosen


def _prune_nonterminal_leaves(
    edge_keys: set[tuple[str, str]],
    terminals: tuple[str, ...],
) -> set[tuple[str, str]]:
    adjacency: dict[str, set[str]] = {}
    for u, v in edge_keys:
        adjacency.setdefault(u, set()).add(v)
        adjacency.setdefault(v, set()).add(u)

    terminals_set = set(terminals)
    changed = True
    while changed:
        changed = False
        for village in list(adjacency):
            neighbors = adjacency.get(village, set())
            if village not in terminals_set and len(neighbors) == 1:
                neighbor = next(iter(neighbors))
                adjacency[neighbor].remove(village)
                if not adjacency[neighbor]:
                    adjacency.pop(neighbor)
                adjacency.pop(village)
                changed = True
    pruned: set[tuple[str, str]] = set()
    for u, neighbors in adjacency.items():
        for v in neighbors:
            if u < v:
                pruned.add((u, v))
    return pruned


def _evaluate_submission(instance: dict[str, Any], submission: dict[str, Any] | None) -> dict[str, Any]:
    villages = tuple(instance["villages"])
    terminals = tuple(instance["terminals"])
    interference_pairs = tuple(tuple(pair) for pair in instance["interference_pairs"])
    edge_lookup = {
        canonical_edge(edge["u"], edge["v"]): int(edge["cost"])
        for edge in instance["edges"]
    }
    village_order = {village: index for index, village in enumerate(villages)}

    if not isinstance(submission, dict):
        return {
            "feasible": False,
            "computed_cost": None,
            "failure_reason": "submission must be an object",
            "edge_cost": None,
            "num_frequencies_used": None,
            "normalized_submission": None,
        }

    raw_edges = submission.get("edges")
    canonical_edges = _normalize_edges(edge_lookup, raw_edges)
    if isinstance(canonical_edges, str):
        return {
            "feasible": False,
            "computed_cost": None,
            "failure_reason": canonical_edges,
            "edge_cost": None,
            "num_frequencies_used": None,
            "normalized_submission": None,
        }

    active = active_villages_for_edges(terminals, canonical_edges, villages)
    if len(canonical_edges) != len(active) - 1:
        return {
            "feasible": False,
            "computed_cost": None,
            "failure_reason": "chosen cable links do not form a tree on the active villages",
            "edge_cost": None,
            "num_frequencies_used": None,
            "normalized_submission": None,
        }
    if not _is_connected(active, canonical_edges):
        return {
            "feasible": False,
            "computed_cost": None,
            "failure_reason": "chosen cable links do not connect the active villages",
            "edge_cost": None,
            "num_frequencies_used": None,
            "normalized_submission": None,
        }
    if not set(terminals).issubset(active):
        return {
            "feasible": False,
            "computed_cost": None,
            "failure_reason": "all required terminals must be active",
            "edge_cost": None,
            "num_frequencies_used": None,
            "normalized_submission": None,
        }

    frequencies = _normalize_frequencies(submission.get("frequencies"))
    if isinstance(frequencies, str):
        return {
            "feasible": False,
            "computed_cost": None,
            "failure_reason": frequencies,
            "edge_cost": None,
            "num_frequencies_used": None,
            "normalized_submission": None,
        }

    missing = [village for village in active if village not in frequencies]
    if missing:
        return {
            "feasible": False,
            "computed_cost": None,
            "failure_reason": f"missing frequencies for active villages: {missing}",
            "edge_cost": None,
            "num_frequencies_used": None,
            "normalized_submission": None,
        }

    active_set = set(active)
    for u, v in interference_pairs:
        if u in active_set and v in active_set and frequencies[u] == frequencies[v]:
            return {
                "feasible": False,
                "computed_cost": None,
                "failure_reason": f"interference violation between {u} and {v}",
                "edge_cost": None,
                "num_frequencies_used": None,
                "normalized_submission": None,
            }

    edge_cost = sum(edge_lookup[edge] for edge in canonical_edges)
    freq_values = {frequencies[village] for village in active}
    total_cost = edge_cost + FREQ_PENALTY * len(freq_values)
    normalized_submission = {
        "edges": [list(edge) for edge in ordered_edges(canonical_edges, villages)],
        "frequencies": {
            village: frequencies[village]
            for village in sorted(active, key=lambda name: village_order[name])
        },
    }
    return {
        "feasible": True,
        "computed_cost": total_cost,
        "failure_reason": None,
        "edge_cost": edge_cost,
        "num_frequencies_used": len(freq_values),
        "normalized_submission": normalized_submission,
    }


def _normalize_edges(
    edge_lookup: dict[tuple[str, str], int],
    raw_edges: Any,
) -> set[tuple[str, str]] | str:
    if not isinstance(raw_edges, list):
        return "edges must be a list"
    canonical: set[tuple[str, str]] = set()
    for item in raw_edges:
        if not isinstance(item, list | tuple) or len(item) != 2:
            return "each edge must be a two-item list"
        try:
            u = str(item[0]).strip()
            v = str(item[1]).strip()
        except Exception:
            return "edges must contain village names"
        edge = canonical_edge(u, v)
        if edge not in edge_lookup:
            return f"unknown cable edge: {edge[0]}-{edge[1]}"
        canonical.add(edge)
    return canonical


def _normalize_frequencies(raw_frequencies: Any) -> dict[str, int] | str:
    if not isinstance(raw_frequencies, dict):
        return "frequencies must be an object"
    normalized: dict[str, int] = {}
    for village, value in raw_frequencies.items():
        try:
            freq = int(value)
        except Exception:
            return f"frequency for {village} is not an integer"
        if freq <= 0:
            return f"frequency for {village} must be positive"
        normalized[str(village).strip()] = freq
    return normalized


def _is_connected(active: tuple[str, ...], edges: set[tuple[str, str]]) -> bool:
    if not active:
        return False
    adjacency = {village: set() for village in active}
    for u, v in edges:
        adjacency[u].add(v)
        adjacency[v].add(u)
    stack = [active[0]]
    seen: set[str] = set()
    while stack:
        village = stack.pop()
        if village in seen:
            continue
        seen.add(village)
        stack.extend(adjacency[village] - seen)
    return seen == set(active)


def _solve_edge_only_then_color(instance: dict[str, Any], seed: int) -> tuple[dict[str, Any], int]:
    min_edge_cost, chosen_edges = _solve_edge_only_tree(instance, seed)
    villages = tuple(instance["villages"])
    terminals = tuple(instance["terminals"])
    interference_pairs = tuple(tuple(pair) for pair in instance["interference_pairs"])
    active = active_villages_for_edges(terminals, chosen_edges, villages)
    num_colors, frequencies = _solve_exact_coloring(active, villages, interference_pairs)
    total_cost = min_edge_cost + FREQ_PENALTY * num_colors
    submission = {
        "edges": [list(edge) for edge in ordered_edges(chosen_edges, villages)],
        "frequencies": frequencies,
    }
    return submission, total_cost


def _solve_edge_only_tree(instance: dict[str, Any], seed: int) -> tuple[int, set[tuple[str, str]]]:
    base_model, active_vars, edge_vars, flow_vars, edges = _build_tree_model(instance)
    edge_cost_expr = sum(edge.cost * edge_vars[index] for index, edge in enumerate(edges))
    base_model.Minimize(edge_cost_expr)
    base_solver = _new_solver(seed)
    base_status = base_solver.Solve(base_model)
    if base_status != cp_model.OPTIMAL:
        raise RuntimeError(f"failed to solve exact edge-only Steiner tree (status={base_status})")
    min_edge_cost = int(base_solver.Value(edge_cost_expr))

    tie_model, tie_active_vars, tie_edge_vars, tie_flow_vars, tie_edges = _build_tree_model(instance)
    del tie_flow_vars
    tie_edge_cost_expr = sum(edge.cost * tie_edge_vars[index] for index, edge in enumerate(tie_edges))
    tie_model.Add(tie_edge_cost_expr == min_edge_cost)
    active_count_expr = sum(tie_active_vars.values())
    tie_model.Minimize(active_count_expr)
    tie_solver = _new_solver(seed + 1)
    tie_status = tie_solver.Solve(tie_model)
    if tie_status != cp_model.OPTIMAL:
        raise RuntimeError(f"failed to break edge-only tie (status={tie_status})")

    chosen_edges = {
        edge.key
        for index, edge in enumerate(tie_edges)
        if tie_solver.Value(tie_edge_vars[index])
    }
    return min_edge_cost, chosen_edges


def _solve_joint_optimum(instance: dict[str, Any], seed: int) -> tuple[dict[str, Any], int]:
    villages = tuple(instance["villages"])
    root = instance["terminals"][0]
    model, active_vars, edge_vars, flow_vars, edges = _build_tree_model(instance)
    del flow_vars

    max_colors = len(villages)
    color_vars: dict[tuple[str, int], cp_model.IntVar] = {}
    used_color_vars: dict[int, cp_model.IntVar] = {}
    for color in range(1, max_colors + 1):
        used_color_vars[color] = model.NewBoolVar(f"used_color_{color}")

    for village in villages:
        vars_for_village = []
        for color in range(1, max_colors + 1):
            var = model.NewBoolVar(f"{village}_color_{color}")
            color_vars[(village, color)] = var
            vars_for_village.append(var)
            model.Add(var <= used_color_vars[color])
        model.Add(sum(vars_for_village) == active_vars[village])

    model.Add(color_vars[(root, 1)] == 1)
    for color in range(2, max_colors + 1):
        model.Add(color_vars[(root, color)] == 0)

    for color in range(1, max_colors):
        model.Add(used_color_vars[color + 1] <= used_color_vars[color])

    active_villages_by_color: dict[int, list[cp_model.IntVar]] = {color: [] for color in range(1, max_colors + 1)}
    for village in villages:
        for color in range(1, max_colors + 1):
            active_villages_by_color[color].append(color_vars[(village, color)])
    for color in range(1, max_colors + 1):
        model.Add(sum(active_villages_by_color[color]) >= used_color_vars[color])

    for u, v in (tuple(pair) for pair in instance["interference_pairs"]):
        for color in range(1, max_colors + 1):
            model.Add(color_vars[(u, color)] + color_vars[(v, color)] <= 1)

    objective = (
        sum(edge.cost * edge_vars[index] for index, edge in enumerate(edges))
        + FREQ_PENALTY * sum(used_color_vars.values())
    )
    model.Minimize(objective)

    solver = _new_solver(seed)
    status = solver.Solve(model)
    if status != cp_model.OPTIMAL:
        raise RuntimeError(f"failed to solve exact joint Steiner-coloring optimum (status={status})")

    chosen_edges = {
        edge.key
        for index, edge in enumerate(edges)
        if solver.Value(edge_vars[index])
    }
    active = active_villages_for_edges(tuple(instance["terminals"]), chosen_edges, villages)
    frequencies: dict[str, int] = {}
    for village in active:
        for color in range(1, max_colors + 1):
            if solver.Value(color_vars[(village, color)]):
                frequencies[village] = color
                break
    submission = {
        "edges": [list(edge) for edge in ordered_edges(chosen_edges, villages)],
        "frequencies": frequencies,
    }
    total_cost = int(solver.ObjectiveValue())
    return submission, total_cost


def _build_tree_model(
    instance: dict[str, Any],
) -> tuple[
    cp_model.CpModel,
    dict[str, cp_model.IntVar],
    dict[int, cp_model.IntVar],
    dict[tuple[int, str], cp_model.IntVar],
    list[EdgeSpec],
]:
    villages = tuple(instance["villages"])
    terminals = tuple(instance["terminals"])
    edges = [EdgeSpec(edge["u"], edge["v"], int(edge["cost"])) for edge in instance["edges"]]
    root = terminals[0]
    node_count = len(villages)

    model = cp_model.CpModel()
    active_vars = {village: model.NewBoolVar(f"active_{village}") for village in villages}
    for terminal in terminals:
        model.Add(active_vars[terminal] == 1)

    edge_vars = {index: model.NewBoolVar(f"edge_{edge.u}_{edge.v}") for index, edge in enumerate(edges)}
    incidence: dict[str, list[cp_model.IntVar]] = {village: [] for village in villages}
    for index, edge in enumerate(edges):
        edge_var = edge_vars[index]
        incidence[edge.u].append(edge_var)
        incidence[edge.v].append(edge_var)
        model.Add(edge_var <= active_vars[edge.u])
        model.Add(edge_var <= active_vars[edge.v])

    for village in villages:
        model.Add(sum(incidence[village]) >= active_vars[village])

    model.Add(sum(edge_vars.values()) == sum(active_vars.values()) - 1)

    flow_vars: dict[tuple[int, str], cp_model.IntVar] = {}
    for index, edge in enumerate(edges):
        flow_vars[(index, "uv")] = model.NewIntVar(0, node_count, f"flow_{edge.u}_{edge.v}")
        flow_vars[(index, "vu")] = model.NewIntVar(0, node_count, f"flow_{edge.v}_{edge.u}")
        model.Add(flow_vars[(index, "uv")] <= node_count * edge_vars[index])
        model.Add(flow_vars[(index, "vu")] <= node_count * edge_vars[index])

    total_active = sum(active_vars.values())
    for village in villages:
        incoming: list[cp_model.IntVar] = []
        outgoing: list[cp_model.IntVar] = []
        for index, edge in enumerate(edges):
            if edge.u == village:
                outgoing.append(flow_vars[(index, "uv")])
                incoming.append(flow_vars[(index, "vu")])
            elif edge.v == village:
                outgoing.append(flow_vars[(index, "vu")])
                incoming.append(flow_vars[(index, "uv")])
        if village == root:
            model.Add(sum(outgoing) - sum(incoming) == total_active - 1)
        else:
            model.Add(sum(incoming) - sum(outgoing) == active_vars[village])

    return model, active_vars, edge_vars, flow_vars, edges


def _solve_exact_coloring(
    active_villages: tuple[str, ...],
    villages: tuple[str, ...],
    interference_pairs: tuple[tuple[str, str], ...],
) -> tuple[int, dict[str, int]]:
    order = {village: index for index, village in enumerate(villages)}
    graph = interference_graph(active_villages, interference_pairs)
    nodes = sorted(active_villages, key=lambda village: (-len(graph[village]), order[village]))
    assignment: dict[str, int] = {}
    best_assignment: dict[str, int] = {}
    best_used = len(nodes) + 1

    def backtrack(index: int, used_colors: int) -> None:
        nonlocal best_assignment, best_used
        if used_colors >= best_used:
            return
        if index == len(nodes):
            best_used = used_colors
            best_assignment = assignment.copy()
            return

        node = nodes[index]
        blocked = {assignment[neighbor] for neighbor in graph[node] if neighbor in assignment}
        for color in range(1, used_colors + 1):
            if color in blocked:
                continue
            assignment[node] = color
            backtrack(index + 1, used_colors)
            assignment.pop(node, None)

        new_color = used_colors + 1
        if new_color <= best_used:
            assignment[node] = new_color
            backtrack(index + 1, new_color)
            assignment.pop(node, None)

    backtrack(0, 0)
    if not best_assignment:
        best_assignment = {node: 1 for node in nodes}
        best_used = 1
    return best_used, {village: best_assignment[village] for village in villages if village in best_assignment}


def _new_solver(seed: int) -> cp_model.CpSolver:
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.max_time_in_seconds = 30.0
    solver.parameters.random_seed = seed
    return solver
