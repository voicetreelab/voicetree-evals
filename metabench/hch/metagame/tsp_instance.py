from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from random import Random

Coord = tuple[int, int]
Tour = list[int]


@dataclass(frozen=True)
class TSPInstance:
    seed: int
    coords: tuple[Coord, ...]
    baseline_tour: tuple[int, ...]
    baseline_length: float
    gold_tour: tuple[int, ...]
    gold_length: float

    def problem_statement(self) -> str:
        coord_lines = "\n".join(
            f"{idx}: ({x}, {y})" for idx, (x, y) in enumerate(self.coords)
        )
        return f"""You are solving a 25-city Euclidean traveling salesman problem.
Cities are indexed from 0 to 24.

Coordinates:
{coord_lines}

Scoring target:
- Shorter tour length is better.
- A tour is a JSON array of 25 distinct integers in [0, 24].
- The route is a closed cycle: after the last city, return to the first city.
- If you do not find an improvement, the baseline remains a valid answer.

BASELINE_TOUR: {list(self.baseline_tour)}
BASELINE_LENGTH: {self.baseline_length:.3f}

When you emit BEST_GUESS, output a full JSON array tour on the same line or directly after the label.
Do not use placeholders or partial tours.
"""


def build_instance(seed: int, n_cities: int = 25, coord_max: int = 100) -> TSPInstance:
    rng = Random(seed)
    coords: list[Coord] = []
    seen: set[Coord] = set()
    while len(coords) < n_cities:
        coord = (rng.randint(0, coord_max), rng.randint(0, coord_max))
        if coord in seen:
            continue
        seen.add(coord)
        coords.append(coord)

    baseline_tour = nearest_neighbor_tour(coords, start=0)
    baseline_length = tour_length(coords, baseline_tour)

    gold_tour = best_nn_plus_two_opt(coords)
    gold_length = tour_length(coords, gold_tour)

    return TSPInstance(
        seed=seed,
        coords=tuple(coords),
        baseline_tour=tuple(baseline_tour),
        baseline_length=baseline_length,
        gold_tour=tuple(gold_tour),
        gold_length=gold_length,
    )


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


def nearest_neighbor_tour(coords: list[Coord] | tuple[Coord, ...], start: int = 0) -> Tour:
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


def two_opt_to_convergence(
    coords: list[Coord] | tuple[Coord, ...],
    initial_tour: list[int] | tuple[int, ...],
) -> Tour:
    best = list(initial_tour)
    best_length = tour_length(coords, best)
    n = len(best)
    improved = True

    while improved:
        improved = False
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                if j - i == 1:
                    continue
                candidate = best[:i] + list(reversed(best[i:j])) + best[j:]
                candidate_length = tour_length(coords, candidate)
                if candidate_length + 1e-9 < best_length:
                    best = candidate
                    best_length = candidate_length
                    improved = True
                    break
            if improved:
                break
    return best


def best_nn_plus_two_opt(coords: list[Coord] | tuple[Coord, ...]) -> Tour:
    best_tour: Tour | None = None
    best_length: float | None = None
    for start in range(len(coords)):
        candidate = nearest_neighbor_tour(coords, start=start)
        candidate = two_opt_to_convergence(coords, candidate)
        candidate_length = tour_length(coords, candidate)
        if best_length is None or candidate_length < best_length:
            best_tour = candidate
            best_length = candidate_length
    if best_tour is None:
        raise ValueError("failed to generate a gold tour")
    return best_tour
