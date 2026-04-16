from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from steiner_coloring_instance import (
    FREQ_PENALTY,
    SteinerColoringInstance,
    active_villages_for_edges,
    canonical_edge,
    ordered_edges,
)


@dataclass(frozen=True)
class VerificationResult:
    feasible: bool
    computed_cost: int | None
    failure_reason: str | None
    edge_cost: int | None
    num_frequencies_used: int | None
    normalized_answer: dict[str, Any] | None


def verify_answer(instance: SteinerColoringInstance, answer: dict[str, Any] | None) -> VerificationResult:
    if not isinstance(answer, dict):
        return VerificationResult(False, None, "answer must be an object", None, None, None)

    raw_edges = answer.get("edges")
    raw_frequencies = answer.get("frequencies")
    canonical_edges = _normalize_edges(instance, raw_edges)
    if isinstance(canonical_edges, str):
        return VerificationResult(False, None, canonical_edges, None, None, None)

    active = active_villages_for_edges(instance.terminals, canonical_edges)
    if len(canonical_edges) != len(active) - 1:
        return VerificationResult(False, None, "chosen cable links do not form a tree on the active villages", None, None, None)
    if not _is_connected(active, canonical_edges):
        return VerificationResult(False, None, "chosen cable links do not connect the active villages", None, None, None)
    if not set(instance.terminals).issubset(active):
        return VerificationResult(False, None, "all required terminals must be active", None, None, None)

    frequencies = _normalize_frequencies(raw_frequencies)
    if isinstance(frequencies, str):
        return VerificationResult(False, None, frequencies, None, None, None)

    missing = [village for village in active if village not in frequencies]
    if missing:
        return VerificationResult(False, None, f"missing frequencies for active villages: {missing}", None, None, None)

    for u, v in instance.interference_pairs:
        if u in active and v in active and frequencies[u] == frequencies[v]:
            return VerificationResult(False, None, f"interference violation between {u} and {v}", None, None, None)

    edge_cost = sum(instance.edge_lookup[edge] for edge in canonical_edges)
    freq_values = {frequencies[village] for village in active}
    total_cost = edge_cost + FREQ_PENALTY * len(freq_values)
    normalized_answer = {
        "edges": [list(edge) for edge in ordered_edges(canonical_edges, instance.villages)],
        "frequencies": {
            village: frequencies[village]
            for village in sorted(active, key=lambda name: instance.village_order[name])
        },
    }
    return VerificationResult(True, total_cost, None, edge_cost, len(freq_values), normalized_answer)


def _normalize_edges(
    instance: SteinerColoringInstance,
    raw_edges: Any,
) -> set[tuple[str, str]] | str:
    if not isinstance(raw_edges, list):
        return "EDGES must be a list"
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
        if edge not in instance.edge_lookup:
            return f"unknown cable edge: {edge[0]}-{edge[1]}"
        canonical.add(edge)
    return canonical


def _normalize_frequencies(raw_frequencies: Any) -> dict[str, int] | str:
    if not isinstance(raw_frequencies, dict):
        return "FREQUENCIES must be an object"
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
