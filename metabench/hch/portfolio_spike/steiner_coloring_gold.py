from __future__ import annotations

from typing import Any

from steiner_coloring_instance import (
    FREQ_PENALTY,
    SteinerColoringInstance,
    active_villages_for_edges,
    interference_graph,
    ordered_edges,
)


def solve_joint_optimum(instance: SteinerColoringInstance) -> tuple[dict[str, Any], int]:
    return _solve_exact(instance, objective="joint")


def solve_cable_only_then_color(instance: SteinerColoringInstance) -> tuple[dict[str, Any], int]:
    return _solve_exact(instance, objective="edge_only")


def _solve_exact(instance: SteinerColoringInstance, objective: str) -> tuple[dict[str, Any], int]:
    edges = list(instance.edges)
    terminals = set(instance.terminals)
    villages = instance.villages
    order = instance.village_order
    color_cache: dict[tuple[str, ...], tuple[int, dict[str, int]]] = {}
    best_key: tuple[Any, ...] | None = None
    best_answer: dict[str, Any] | None = None
    best_total_cost: int | None = None

    for mask in range(1, 1 << len(edges)):
        edge_count = mask.bit_count()
        if edge_count < len(terminals) - 1 or edge_count >= len(villages):
            continue

        chosen = [edges[index] for index in range(len(edges)) if mask & (1 << index)]
        active = set(terminals)
        for edge in chosen:
            active.add(edge.u)
            active.add(edge.v)
        if edge_count != len(active) - 1:
            continue
        if not _is_connected_tree(active, chosen):
            continue

        edge_cost = sum(edge.cost for edge in chosen)
        active_key = tuple(sorted(active, key=lambda village: order[village]))
        if active_key not in color_cache:
            color_cache[active_key] = _solve_exact_coloring(instance, active_key)
        num_colors, frequencies = color_cache[active_key]
        total_cost = edge_cost + FREQ_PENALTY * num_colors

        edge_keys = {(edge.u, edge.v) if edge.u < edge.v else (edge.v, edge.u) for edge in chosen}
        ordered_edge_keys = tuple(ordered_edges(edge_keys, villages))
        freq_items = tuple((village, frequencies[village]) for village in sorted(frequencies, key=lambda name: order[name]))
        if objective == "joint":
            key = (total_cost, edge_cost, len(active), ordered_edge_keys, freq_items)
        else:
            key = (edge_cost, len(active), ordered_edge_keys, freq_items)
        if best_key is None or key < best_key:
            best_key = key
            best_total_cost = total_cost
            best_answer = {
                "edges": [list(edge) for edge in ordered_edge_keys],
                "frequencies": {village: frequencies[village] for village, _ in freq_items},
            }

    if best_answer is None or best_total_cost is None:
        raise RuntimeError("failed to find any terminal-connecting tree")
    return best_answer, best_total_cost


def _is_connected_tree(active: set[str], chosen_edges: list[Any]) -> bool:
    if not active:
        return False
    adjacency = {node: set() for node in active}
    for edge in chosen_edges:
        adjacency[edge.u].add(edge.v)
        adjacency[edge.v].add(edge.u)
    stack = [next(iter(active))]
    seen: set[str] = set()
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(adjacency[node] - seen)
    return seen == active


def _solve_exact_coloring(
    instance: SteinerColoringInstance,
    active_villages: tuple[str, ...],
) -> tuple[int, dict[str, int]]:
    order = instance.village_order
    graph = interference_graph(active_villages, instance.interference_pairs)
    nodes = sorted(active_villages, key=lambda village: (-len(graph[village]), order[village]))
    assignment: dict[str, int] = {}
    best_assignment: dict[str, int] = {}
    best_used = len(nodes) + 1

    def backtrack(index: int, used_colors: int) -> None:
        nonlocal best_used, best_assignment
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
    return best_used, {village: best_assignment[village] for village in sorted(best_assignment, key=lambda name: order[name])}
