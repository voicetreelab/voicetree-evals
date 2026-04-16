from __future__ import annotations

from typing import Any

from verifiers.ve import build_instance_payload


def generate(seed: int, difficulty: str) -> dict[str, Any]:
    return build_instance_payload(seed=seed, difficulty=difficulty)


__all__ = ["generate"]
