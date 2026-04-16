from __future__ import annotations

import importlib
import inspect
import re
from typing import Any, Callable

KNOWN_CLASSES = ("cjs", "graphcol", "mbj", "mwis", "steiner", "tsp", "ve")
_SCHEMA_RE = re.compile(r"BEST_GUESS(?: JSON)? schema:\s*(.*)", re.IGNORECASE | re.DOTALL)

CLASS_TO_VERIFIER: dict[str, Callable[[dict[str, Any], dict[str, Any] | None], tuple[float, bool, dict[str, Any]]]] = {}
CLASS_TO_BEST_GUESS_SCHEMA: dict[str, str] = {}

for cls in KNOWN_CLASSES:
    try:
        module = importlib.import_module(f"verifiers.{cls}")
    except ModuleNotFoundError:
        continue
    verify = getattr(module, "verify", None)
    if not callable(verify):
        continue

    CLASS_TO_VERIFIER[cls] = verify
    doc = inspect.getdoc(verify) or inspect.getdoc(module) or ""
    match = _SCHEMA_RE.search(doc)
    if match:
        schema = match.group(1).strip()
        if schema:
            CLASS_TO_BEST_GUESS_SCHEMA[cls] = schema
