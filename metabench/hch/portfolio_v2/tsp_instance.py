from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from random import Random
from typing import Any

try:
    from ortools.sat.python import cp_model
except ImportError:  # pragma: no cover - exercised in dependency-blocked environments
    cp_model = None

Coord = tuple[int, int]
Tour = tuple[int, ...]


def _require_ortools() -> Any:
    if cp_model is None:
        raise RuntimeError(
            "ortools is not installed. Install hch/portfolio_spike/requirements.txt before building TSP instances."
        )
    return cp_model


@dataclass(frozen=True)
class VerificationResult:
    feasible: bool
    computed_length: float | None
    failure_reason: str | None
    normalized_tour: Tour | None


@dataclass(frozen=True)
class TSPInstance:
    seed: int
    coords: tuple[Coord, ...]
    baseline_tour: Tour
    baseline_length: float
    optimal_tour: Tour
    optimal_length: float
    problem_statement: str


def build_instance(
    seed: int,
    n_cities: int = 20,
    coord_max: int = 100,
    min_baseline_gap_pct: float | None = None,
    max_generation_attempts: int = 60,
) -> TSPInstance:
    last_gap_pct: float | None = None
    for attempt in range(max_generation_attempts):
        attempt_seed = seed if attempt == 0 else seed * 10_000 + attempt
        coords = _draw_coords(attempt_seed, n_cities=n_cities, coord_max=coord_max)
        baseline_tour = tuple(nearest_neighbor_tour(coords, start=0))
        baseline_length = tour_length(coords, baseline_tour)
        optimal_tour, optimal_length = solve_exact_tour(coords)
        last_gap_pct = 100.0 * (baseline_length - optimal_length) / optimal_length
        if min_baseline_gap_pct is not None and last_gap_pct < min_baseline_gap_pct:
            continue
        stub = TSPInstance(
            seed=seed,
            coords=coords,
            baseline_tour=baseline_tour,
            baseline_length=baseline_length,
            optimal_tour=optimal_tour,
            optimal_length=optimal_length,
            problem_statement="",
        )
        return TSPInstance(
            seed=seed,
            coords=coords,
            baseline_tour=baseline_tour,
            baseline_length=baseline_length,
            optimal_tour=optimal_tour,
            optimal_length=optimal_length,
            problem_statement=render_problem(stub),
        )

    raise RuntimeError(
        "failed to generate a TSP-20 instance meeting minimum baseline gap "
        f"{min_baseline_gap_pct} after {max_generation_attempts} attempts; last gap was {last_gap_pct}"
    )


def _draw_coords(seed: int, *, n_cities: int, coord_max: int) -> tuple[Coord, ...]:
    rng = Random(seed)
    coords: list[Coord] = []
    seen: set[Coord] = set()
    while len(coords) < n_cities:
        coord = (rng.randint(0, coord_max), rng.randint(0, coord_max))
        if coord in seen:
            continue
        seen.add(coord)
        coords.append(coord)
    return tuple(coords)


def distance(coords: list[Coord] | tuple[Coord, ...], a: int, b: int) -> float:
    ax, ay = coords[a]
    bx, by = coords[b]
    return hypot(ax - bx, ay - by)


def tour_length(coords: list[Coord] | tuple[Coord, ...], tour: list[int] | tuple[int, ...]) -> float:
    if not tour:
        raise ValueError("tour must not be empty")
    total = 0.0
    for idx, city in enumerate(tour):
        nxt = tour[(idx + 1) % len(tour)]
        total += distance(coords, city, nxt)
    return total


def nearest_neighbor_tour(coords: list[Coord] | tuple[Coord, ...], start: int = 0) -> list[int]:
    n = len(coords)
    if n == 0:
        return []
    remaining = set(range(n))
    remaining.remove(start)
    tour = [start]
    current = start
    while remaining:
        next_city = min(remaining, key=lambda city: (distance(coords, current, city), city))
        tour.append(next_city)
        remaining.remove(next_city)
        current = next_city
    return tour


def solve_exact_tour(coords: tuple[Coord, ...]) -> tuple[Tour, float]:
    cp = _require_ortools()
    n = len(coords)
    if n <= 2:
        tour = tuple(range(n))
        return tour, tour_length(coords, tour)

    scaled = [
        [0 if i == j else int(round(distance(coords, i, j) * 1_000_000)) for j in range(n)]
        for i in range(n)
    ]

    model = cp.CpModel()
    arc_vars: dict[tuple[int, int], Any] = {}
    arcs: list[tuple[int, int, Any]] = []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            var = model.NewBoolVar(f"a_{i}_{j}")
            arc_vars[(i, j)] = var
            arcs.append((i, j, var))
    model.AddCircuit(arcs)
    model.Minimize(sum(scaled[i][j] * var for (i, j), var in arc_vars.items()))

    solver = cp.CpSolver()
    solver.parameters.max_time_in_seconds = 60.0
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)
    if status != cp.OPTIMAL:
        status_name = solver.StatusName(status)
        raise RuntimeError(f"failed to obtain exact optimum for TSP-20 instance: {status_name}")

    successor: dict[int, int] = {}
    for (i, j), var in arc_vars.items():
        if solver.Value(var):
            successor[i] = j

    tour = [0]
    seen = {0}
    while len(tour) < n:
        nxt = successor.get(tour[-1])
        if nxt is None or nxt in seen:
            raise RuntimeError("exact TSP solver returned an invalid circuit")
        tour.append(nxt)
        seen.add(nxt)
    if successor.get(tour[-1]) != 0:
        raise RuntimeError("exact TSP solver did not return a closed tour")

    normalized = normalize_tour(tour)
    return normalized, tour_length(coords, normalized)


def verify_tour(instance: TSPInstance, answer: list[int] | tuple[int, ...] | None) -> VerificationResult:
    if not isinstance(answer, list | tuple):
        return VerificationResult(False, None, "tour must be a list of city indices", None)
    n = len(instance.coords)
    if len(answer) != n:
        return VerificationResult(False, None, f"tour must contain exactly {n} cities", None)
    normalized: list[int] = []
    seen: set[int] = set()
    for item in answer:
        try:
            city = int(item)
        except Exception:
            return VerificationResult(False, None, "tour items must be integers", None)
        if not 0 <= city < n:
            return VerificationResult(False, None, f"city index {city} is out of range", None)
        if city in seen:
            return VerificationResult(False, None, f"city {city} appears more than once", None)
        normalized.append(city)
        seen.add(city)
    normalized_tour = normalize_tour(normalized)
    return VerificationResult(True, tour_length(instance.coords, normalized_tour), None, normalized_tour)


def normalize_tour(tour: list[int] | tuple[int, ...]) -> Tour:
    if not tour:
        return tuple()
    n = len(tour)
    start_index = tour.index(0)
    rotated = list(tour[start_index:]) + list(tour[:start_index])
    reversed_rotated = [rotated[0]] + list(reversed(rotated[1:]))
    return tuple(rotated) if tuple(rotated) <= tuple(reversed_rotated) else tuple(reversed_rotated)


def render_problem(instance: TSPInstance) -> str:
    coord_lines = "\n".join(f"- {idx}: ({x}, {y})" for idx, (x, y) in enumerate(instance.coords))
    return f"""Euclidean TSP-20:
You need a short closed tour through all 20 cities.

Coordinates:
{coord_lines}

Rules:
- Output one full tour containing every city exactly once.
- The route is a closed cycle: after the last city, return to the first city.
- Shorter total Euclidean length is better.
- If you stop immediately or fail to produce a valid answer, the baseline below is what gets scored.

Baseline length: {instance.baseline_length:.3f}
Baseline tour: {list(instance.baseline_tour)}
"""


def tour_summary(instance: TSPInstance, tour: list[int] | tuple[int, ...], length: float | None = None) -> str:
    total = length if length is not None else tour_length(instance.coords, tour)
    return f"Tour: {list(normalize_tour(tour))}\nLength: {total:.3f}"
