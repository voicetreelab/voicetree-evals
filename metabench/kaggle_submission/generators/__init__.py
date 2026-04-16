from __future__ import annotations

import importlib
from typing import Any, Callable

KNOWN_CLASSES = ("cjs", "graphcol", "mwis", "steiner", "tsp", "ve")

CLASS_TO_GENERATOR: dict[str, Callable[[int, str], dict[str, Any]]] = {}

for cls in KNOWN_CLASSES:
    try:
        module = importlib.import_module(f"generators.{cls}")
    except ModuleNotFoundError:
        continue
    generate = getattr(module, "generate", None)
    if callable(generate):
        CLASS_TO_GENERATOR[cls] = generate
