from __future__ import annotations

from typing import Any


def score_solo(gap_pct: float, feasible: bool, wall_s: float) -> float:
    if not feasible:
        return 0.0
    return max(0.0, 100.0 - float(gap_pct)) - 0.01 * float(wall_s)


def score_portfolio(components: list[dict[str, Any]], wall_s: float) -> float:
    value_sum = 0.0
    for component in components:
        value_cap = float(component.get("value_cap", 0.0))
        feasible = bool(component.get("feasible", True))
        gap_pct = float(component.get("gap_pct", 100.0))
        if not feasible:
            headroom = 0.0
        else:
            headroom = min(1.0, max(0.0, 1.0 - gap_pct / 100.0))
        value_sum += value_cap * headroom
    return value_sum - 0.05 * float(wall_s)
