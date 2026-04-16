from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ParsedInstance:
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    num_colors: int
    gold_scored_cost: float
    baseline_scored_cost: float | None


def verify(instance: dict[str, Any], submission: dict[str, Any] | None) -> tuple[float, bool, dict[str, Any]]:
    """BEST_GUESS schema: {"assignment": {"N01": 1, ..., "N30": 4}}."""
    try:
        parsed = _parse_instance(instance)
    except ValueError as exc:
        return math.inf, False, {"error": str(exc)}

    raw_assignment = submission.get("assignment", submission) if isinstance(submission, dict) else submission
    if not isinstance(raw_assignment, dict):
        return math.inf, False, _failure_details(parsed, "submission must be an object with an assignment mapping")

    normalized: dict[str, int] = {}
    for node in parsed.nodes:
        if node not in raw_assignment:
            return math.inf, False, _failure_details(parsed, f"missing color for {node}")
        try:
            color = int(raw_assignment[node])
        except Exception:
            return math.inf, False, _failure_details(parsed, f"color for {node} is not an integer")
        if not 1 <= color <= parsed.num_colors:
            return math.inf, False, _failure_details(
                parsed,
                f"color for {node} must be between 1 and {parsed.num_colors}",
            )
        normalized[node] = color

    conflict_count = sum(1 for left, right in parsed.edges if normalized[left] == normalized[right])
    scored_cost = float(parsed.num_colors + conflict_count)
    gap_pct = 100.0 * (scored_cost - parsed.gold_scored_cost) / parsed.gold_scored_cost
    details = {
        "conflict_count": conflict_count,
        "scored_cost": scored_cost,
        "gold_scored_cost": parsed.gold_scored_cost,
        "baseline_scored_cost": parsed.baseline_scored_cost,
        "normalized_submission": {
            "assignment": {node: normalized[node] for node in parsed.nodes},
        },
    }
    return gap_pct, True, details


def _parse_instance(instance: dict[str, Any]) -> ParsedInstance:
    if not isinstance(instance, dict):
        raise ValueError("instance must be an object")

    raw_nodes = instance.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes or not all(isinstance(node, str) for node in raw_nodes):
        raise ValueError("instance.nodes must be a non-empty list of node ids")
    nodes = tuple(raw_nodes)
    node_set = set(nodes)
    if len(node_set) != len(nodes):
        raise ValueError("instance.nodes contains duplicates")

    raw_edges = instance.get("edges")
    if not isinstance(raw_edges, list):
        raise ValueError("instance.edges must be a list")
    edges: list[tuple[str, str]] = []
    for raw_edge in raw_edges:
        if not isinstance(raw_edge, (list, tuple)) or len(raw_edge) != 2:
            raise ValueError("each edge must be a two-item list")
        left, right = raw_edge
        if not isinstance(left, str) or not isinstance(right, str):
            raise ValueError("edge endpoints must be strings")
        if left not in node_set or right not in node_set:
            raise ValueError("edge endpoint missing from instance.nodes")
        if left == right:
            raise ValueError("self-loops are not allowed")
        edges.append((left, right) if left < right else (right, left))

    num_colors = instance.get("num_colors")
    if not isinstance(num_colors, int) or num_colors <= 0:
        raise ValueError("instance.num_colors must be a positive integer")

    gold_scored_cost = instance.get("gold_scored_cost")
    if gold_scored_cost is None:
        gold_conflicts = instance.get("gold_conflicts")
        if not isinstance(gold_conflicts, int) or gold_conflicts < 0:
            raise ValueError("instance must provide gold_scored_cost or a non-negative gold_conflicts")
        gold_scored_cost = float(num_colors + gold_conflicts)
    else:
        gold_scored_cost = float(gold_scored_cost)

    baseline_scored_cost = instance.get("baseline_scored_cost")
    if baseline_scored_cost is None:
        baseline_conflicts = instance.get("baseline_conflicts")
        baseline_scored_cost = (
            float(num_colors + baseline_conflicts)
            if isinstance(baseline_conflicts, int) and baseline_conflicts >= 0
            else None
        )
    else:
        baseline_scored_cost = float(baseline_scored_cost)

    return ParsedInstance(
        nodes=nodes,
        edges=tuple(edges),
        num_colors=num_colors,
        gold_scored_cost=gold_scored_cost,
        baseline_scored_cost=baseline_scored_cost,
    )


def _failure_details(parsed: ParsedInstance, error: str) -> dict[str, Any]:
    return {
        "error": error,
        "gold_scored_cost": parsed.gold_scored_cost,
        "baseline_scored_cost": parsed.baseline_scored_cost,
    }
