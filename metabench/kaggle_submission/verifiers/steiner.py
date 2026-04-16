from __future__ import annotations

from typing import Any

FREQ_PENALTY = 15


def verify(instance: dict[str, Any], submission: dict[str, Any] | None) -> tuple[float, bool, dict[str, Any]]:
    """BEST_GUESS schema: {"edges": [["VillageA", "VillageB"], ...], "frequencies": {"VillageA": 1, ...}}."""

    villages = tuple(_require_list_of_strings(instance, "villages"))
    terminals = tuple(_require_list_of_strings(instance, "terminals"))
    edges = _require_edges(instance)
    interference_pairs = tuple(tuple(pair) for pair in _require_string_pairs(instance, "interference_pairs"))
    baseline_cost = int(instance["baseline_cost"])
    gold_cost = int(instance["gold_cost"])
    freq_penalty = int(instance.get("freq_penalty", FREQ_PENALTY))
    village_order = {village: index for index, village in enumerate(villages)}
    edge_lookup = {canonical_edge(edge["u"], edge["v"]): int(edge["cost"]) for edge in edges}

    check = _evaluate_submission(
        villages=villages,
        terminals=terminals,
        interference_pairs=interference_pairs,
        village_order=village_order,
        edge_lookup=edge_lookup,
        submission=submission,
        freq_penalty=freq_penalty,
    )

    if check["feasible"]:
        scored_cost = int(check["computed_cost"])
        feasible = True
        used_baseline_fallback = False
    else:
        scored_cost = baseline_cost
        feasible = False
        used_baseline_fallback = True

    gap_pct = 100.0 * (scored_cost - gold_cost) / gold_cost
    details = {
        "failure_reason": check["failure_reason"],
        "computed_cost": check["computed_cost"],
        "scored_cost": scored_cost,
        "edge_cost": check["edge_cost"],
        "num_frequencies_used": check["num_frequencies_used"],
        "normalized_submission": check["normalized_submission"],
        "baseline_cost": baseline_cost,
        "gold_cost": gold_cost,
        "used_baseline_fallback": used_baseline_fallback,
    }
    return gap_pct, feasible, details


def canonical_edge(u: str, v: str) -> tuple[str, str]:
    if u == v:
        raise ValueError(f"self loops are not allowed: {u}")
    return (u, v) if u < v else (v, u)


def ordered_edges(
    edge_keys: set[tuple[str, str]] | tuple[tuple[str, str], ...],
    villages: tuple[str, ...],
) -> list[tuple[str, str]]:
    order = {village: index for index, village in enumerate(villages)}
    return sorted(edge_keys, key=lambda item: (order[item[0]], order[item[1]]))


def active_villages_for_edges(
    terminals: tuple[str, ...],
    edge_keys: set[tuple[str, str]],
    villages: tuple[str, ...],
) -> tuple[str, ...]:
    active = set(terminals)
    for u, v in edge_keys:
        active.add(u)
        active.add(v)
    return tuple(village for village in villages if village in active)


def _require_list_of_strings(instance: dict[str, Any], key: str) -> list[str]:
    value = instance.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"instance[{key!r}] must be a list of strings")
    return value


def _require_string_pairs(instance: dict[str, Any], key: str) -> list[list[str]]:
    value = instance.get(key)
    if not isinstance(value, list):
        raise ValueError(f"instance[{key!r}] must be a list")
    normalized: list[list[str]] = []
    for item in value:
        if not isinstance(item, list | tuple) or len(item) != 2:
            raise ValueError(f"instance[{key!r}] must contain two-item pairs")
        left, right = item
        if not isinstance(left, str) or not isinstance(right, str):
            raise ValueError(f"instance[{key!r}] must contain string pairs")
        normalized.append([left, right])
    return normalized


def _require_edges(instance: dict[str, Any]) -> list[dict[str, Any]]:
    value = instance.get("edges")
    if not isinstance(value, list):
        raise ValueError("instance['edges'] must be a list")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("instance['edges'] entries must be objects")
        u = item.get("u")
        v = item.get("v")
        cost = item.get("cost")
        if not isinstance(u, str) or not isinstance(v, str):
            raise ValueError("instance['edges'] entries must contain string u/v fields")
        normalized.append({"u": u, "v": v, "cost": int(cost)})
    return normalized


def _evaluate_submission(
    *,
    villages: tuple[str, ...],
    terminals: tuple[str, ...],
    interference_pairs: tuple[tuple[str, str], ...],
    village_order: dict[str, int],
    edge_lookup: dict[tuple[str, str], int],
    submission: dict[str, Any] | None,
    freq_penalty: int,
) -> dict[str, Any]:
    if not isinstance(submission, dict):
        return _failure("submission must be an object")

    raw_edges = submission.get("edges")
    canonical_edges = _normalize_edges(edge_lookup, raw_edges)
    if isinstance(canonical_edges, str):
        return _failure(canonical_edges)

    active = active_villages_for_edges(terminals, canonical_edges, villages)
    if len(canonical_edges) != len(active) - 1:
        return _failure("chosen cable links do not form a tree on the active villages")
    if not _is_connected(active, canonical_edges):
        return _failure("chosen cable links do not connect the active villages")
    if not set(terminals).issubset(active):
        return _failure("all required terminals must be active")

    frequencies = _normalize_frequencies(submission.get("frequencies"))
    if isinstance(frequencies, str):
        return _failure(frequencies)

    missing = [village for village in active if village not in frequencies]
    if missing:
        return _failure(f"missing frequencies for active villages: {missing}")

    active_set = set(active)
    for u, v in interference_pairs:
        if u in active_set and v in active_set and frequencies[u] == frequencies[v]:
            return _failure(f"interference violation between {u} and {v}")

    edge_cost = sum(edge_lookup[edge] for edge in canonical_edges)
    num_frequencies_used = len({frequencies[village] for village in active})
    computed_cost = edge_cost + freq_penalty * num_frequencies_used
    normalized_submission = {
        "edges": [list(edge) for edge in ordered_edges(canonical_edges, villages)],
        "frequencies": {
            village: frequencies[village]
            for village in sorted(active, key=lambda name: village_order[name])
        },
    }
    return {
        "feasible": True,
        "failure_reason": None,
        "computed_cost": computed_cost,
        "edge_cost": edge_cost,
        "num_frequencies_used": num_frequencies_used,
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


def _failure(reason: str) -> dict[str, Any]:
    return {
        "feasible": False,
        "failure_reason": reason,
        "computed_cost": None,
        "edge_cost": None,
        "num_frequencies_used": None,
        "normalized_submission": None,
    }
