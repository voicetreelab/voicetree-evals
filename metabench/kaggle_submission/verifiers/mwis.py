from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InstanceView:
    node_order: dict[str, int]
    weights: dict[str, int]
    edges: tuple[tuple[str, str], ...]
    optimal_objective: int
    baseline_objective: int | None
    baseline_gap_pct: float | None


def verify(instance: dict[str, Any], submission: dict[str, Any] | None) -> tuple[float, bool, dict[str, Any]]:
    """BEST_GUESS schema: {"selected_vertices": ["V001", ...], "total_weight": 123}."""

    parsed_instance, instance_error = _parse_instance(instance)
    if parsed_instance is None:
        return 100.0, False, {"failure_reason": instance_error}

    normalized_submission, failure_reason = _normalize_submission(parsed_instance, submission)
    if normalized_submission is None:
        return 100.0, False, {
            "failure_reason": failure_reason,
            "optimal_objective": parsed_instance.optimal_objective,
            "baseline_objective": parsed_instance.baseline_objective,
            "baseline_gap_pct": parsed_instance.baseline_gap_pct,
        }

    submitted_objective = normalized_submission["total_weight"]
    optimal_objective = parsed_instance.optimal_objective
    if optimal_objective <= 0:
        return 100.0, False, {
            "failure_reason": "optimal_objective must be a positive integer",
            "submitted_objective": submitted_objective,
        }

    gap_pct = max(0.0, 100.0 * (optimal_objective - submitted_objective) / optimal_objective)
    details: dict[str, Any] = {
        "submitted_objective": submitted_objective,
        "optimal_objective": optimal_objective,
        "baseline_objective": parsed_instance.baseline_objective,
        "baseline_gap_pct": parsed_instance.baseline_gap_pct,
        "selected_count": len(normalized_submission["selected_vertices"]),
        "normalized_submission": normalized_submission,
    }
    if parsed_instance.baseline_objective is not None:
        details["improves_on_baseline"] = submitted_objective > parsed_instance.baseline_objective
    return gap_pct, True, details


def _parse_instance(instance: dict[str, Any]) -> tuple[InstanceView | None, str | None]:
    if not isinstance(instance, dict):
        return None, "instance must be an object"

    weights, node_order, weight_error = _parse_vertices(instance.get("vertices"))
    if weights is None or node_order is None:
        return None, weight_error

    edges, edge_error = _parse_edges(instance.get("edges"), weights)
    if edges is None:
        return None, edge_error

    optimal_objective, error = _parse_int_field(
        instance.get("optimal_objective"),
        field_name="optimal_objective",
    )
    if error and isinstance(instance.get("optimal_answer"), dict):
        optimal_objective, error = _parse_int_field(
            instance["optimal_answer"].get("total_weight"),
            field_name="optimal_answer.total_weight",
        )
    if error:
        return None, error

    baseline_objective: int | None = None
    baseline_error: str | None = None
    if "baseline_objective" in instance:
        baseline_objective, baseline_error = _parse_int_field(
            instance.get("baseline_objective"),
            field_name="baseline_objective",
        )
    elif isinstance(instance.get("baseline_answer"), dict):
        baseline_objective, baseline_error = _parse_int_field(
            instance["baseline_answer"].get("total_weight"),
            field_name="baseline_answer.total_weight",
        )
    if baseline_error:
        return None, baseline_error

    baseline_gap_pct: float | None = None
    raw_baseline_gap = instance.get("baseline_gap_pct")
    if raw_baseline_gap is not None:
        try:
            baseline_gap_pct = float(raw_baseline_gap)
        except Exception:
            return None, "baseline_gap_pct must be numeric"

    return (
        InstanceView(
            node_order=node_order,
            weights=weights,
            edges=edges,
            optimal_objective=optimal_objective,
            baseline_objective=baseline_objective,
            baseline_gap_pct=baseline_gap_pct,
        ),
        None,
    )


def _parse_vertices(
    raw_vertices: Any,
) -> tuple[dict[str, int] | None, dict[str, int] | None, str | None]:
    if not isinstance(raw_vertices, list):
        return None, None, "instance.vertices must be a list"

    weights: dict[str, int] = {}
    node_order: dict[str, int] = {}
    for index, item in enumerate(raw_vertices):
        if not isinstance(item, dict):
            return None, None, "each instance.vertices entry must be an object"
        raw_vertex = item.get("vertex_id")
        if not isinstance(raw_vertex, str) or not raw_vertex.strip():
            return None, None, "each vertex must have a non-empty string vertex_id"
        vertex = raw_vertex.strip()
        if vertex in weights:
            return None, None, f"duplicate vertex_id {vertex}"
        try:
            weight = int(item.get("weight"))
        except Exception:
            return None, None, f"weight for {vertex} must be an integer"
        weights[vertex] = weight
        node_order[vertex] = index
    if not weights:
        return None, None, "instance must contain at least one vertex"
    return weights, node_order, None


def _parse_edges(
    raw_edges: Any,
    weights: dict[str, int],
) -> tuple[tuple[tuple[str, str], ...] | None, str | None]:
    if not isinstance(raw_edges, list):
        return None, "instance.edges must be a list"

    edge_set: set[tuple[str, str]] = set()
    for item in raw_edges:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            return None, "each edge must be a two-item list"
        left_raw, right_raw = item
        if not isinstance(left_raw, str) or not isinstance(right_raw, str):
            return None, "edge endpoints must be strings"
        left = left_raw.strip()
        right = right_raw.strip()
        if left not in weights or right not in weights:
            return None, f"unknown edge endpoint in {item!r}"
        if left == right:
            return None, f"self-loop {left} is not allowed"
        edge_set.add(_edge(left, right))
    return tuple(sorted(edge_set)), None


def _parse_int_field(raw_value: Any, *, field_name: str) -> tuple[int, str | None]:
    try:
        return int(raw_value), None
    except Exception:
        return 0, f"{field_name} must be an integer"


def _normalize_submission(
    instance: InstanceView,
    submission: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(submission, dict):
        return None, "submission must be an object"

    raw_vertices = submission.get("selected_vertices")
    if not isinstance(raw_vertices, list):
        return None, "selected_vertices must be a list"

    raw_total_weight = submission.get("total_weight")
    try:
        claimed_total_weight = int(raw_total_weight)
    except Exception:
        return None, "total_weight must be an integer"

    seen: set[str] = set()
    normalized_vertices: list[str] = []
    for raw_vertex in raw_vertices:
        if not isinstance(raw_vertex, str):
            return None, "selected_vertices entries must be strings"
        vertex = raw_vertex.strip()
        if vertex not in instance.weights:
            return None, f"unknown vertex {raw_vertex!r}"
        if vertex in seen:
            return None, f"duplicate vertex {vertex}"
        seen.add(vertex)
        normalized_vertices.append(vertex)

    selected_set = set(normalized_vertices)
    for left, right in instance.edges:
        if left in selected_set and right in selected_set:
            return None, f"selected set is not independent: edge {left}-{right} is internal"

    verified_total_weight = sum(instance.weights[vertex] for vertex in normalized_vertices)
    if verified_total_weight != claimed_total_weight:
        return None, (
            f"claimed total_weight {claimed_total_weight} does not match computed {verified_total_weight}"
        )

    ordered_vertices = sorted(normalized_vertices, key=instance.node_order.__getitem__)
    return {
        "selected_vertices": ordered_vertices,
        "total_weight": verified_total_weight,
    }, None


def _edge(left: str, right: str) -> tuple[str, str]:
    return (left, right) if left < right else (right, left)
