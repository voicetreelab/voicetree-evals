from __future__ import annotations

from math import hypot
from typing import Any

INVALID_GAP_PCT = 100.0


def verify(instance: dict[str, Any], submission: dict[str, Any] | list[int] | tuple[int, ...]) -> tuple[float, bool, dict[str, Any]]:
    """BEST_GUESS JSON schema: {"tour": [0, 7, 3, ...]} with every city index exactly once."""

    try:
        coords = _parse_coords(instance.get("coords"))
        optimal_length = _read_positive_float(instance, "optimal_length")
    except (TypeError, ValueError) as exc:
        details = {"failure_reason": f"invalid instance: {exc}"}
        return INVALID_GAP_PCT, False, details

    baseline_length = _read_optional_float(instance, "baseline_length")
    raw_tour = submission.get("tour") if isinstance(submission, dict) else submission
    normalized_tour, failure_reason = _normalize_submission(coords, raw_tour)
    if failure_reason is not None:
        details = {
            "failure_reason": failure_reason,
            "baseline_length": baseline_length,
            "optimal_length": optimal_length,
        }
        return INVALID_GAP_PCT, False, details

    computed_length = _tour_length(coords, normalized_tour)
    gap_pct = 100.0 * max(0.0, computed_length - optimal_length) / optimal_length
    details = {
        "computed_length": computed_length,
        "baseline_length": baseline_length,
        "optimal_length": optimal_length,
        "normalized_tour": list(normalized_tour),
    }
    return gap_pct, True, details


def _parse_coords(raw_coords: Any) -> tuple[tuple[int, int], ...]:
    if not isinstance(raw_coords, list):
        raise TypeError("coords must be a list")
    coords: list[tuple[int, int]] = []
    for item in raw_coords:
        if not isinstance(item, list | tuple) or len(item) != 2:
            raise TypeError("each coordinate must be a two-item list")
        x = int(item[0])
        y = int(item[1])
        coords.append((x, y))
    if not coords:
        raise ValueError("coords must not be empty")
    return tuple(coords)


def _normalize_submission(
    coords: tuple[tuple[int, int], ...],
    raw_tour: Any,
) -> tuple[tuple[int, ...], str | None]:
    if not isinstance(raw_tour, list | tuple):
        return tuple(), "submission must provide tour as a list of city indices"

    n = len(coords)
    if len(raw_tour) != n:
        return tuple(), f"tour must contain exactly {n} cities"

    normalized: list[int] = []
    seen: set[int] = set()
    for item in raw_tour:
        try:
            city = int(item)
        except Exception:
            return tuple(), "tour items must be integers"
        if not 0 <= city < n:
            return tuple(), f"city index {city} is out of range"
        if city in seen:
            return tuple(), f"city {city} appears more than once"
        normalized.append(city)
        seen.add(city)

    return _normalize_tour(normalized), None


def _normalize_tour(tour: list[int] | tuple[int, ...]) -> tuple[int, ...]:
    start_index = tour.index(0)
    rotated = list(tour[start_index:]) + list(tour[:start_index])
    reversed_rotated = [rotated[0]] + list(reversed(rotated[1:]))
    return tuple(rotated) if tuple(rotated) <= tuple(reversed_rotated) else tuple(reversed_rotated)


def _tour_length(coords: tuple[tuple[int, int], ...], tour: tuple[int, ...]) -> float:
    total = 0.0
    for idx, city in enumerate(tour):
        nxt = tour[(idx + 1) % len(tour)]
        total += _distance(coords, city, nxt)
    return total


def _distance(coords: tuple[tuple[int, int], ...], a: int, b: int) -> float:
    ax, ay = coords[a]
    bx, by = coords[b]
    return hypot(ax - bx, ay - by)


def _read_positive_float(instance: dict[str, Any], key: str) -> float:
    value = float(instance[key])
    if value <= 0.0:
        raise ValueError(f"{key} must be positive")
    return value


def _read_optional_float(instance: dict[str, Any], key: str) -> float | None:
    value = instance.get(key)
    if value is None:
        return None
    return float(value)
