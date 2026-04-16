#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import sys
import textwrap
from dataclasses import is_dataclass
from pathlib import Path
from random import Random
from string import Template
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PORTFOLIO_DIR = REPO_ROOT / "hch" / "portfolio_spike"
if str(PORTFOLIO_DIR) not in sys.path:
    sys.path.insert(0, str(PORTFOLIO_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from graph_coloring_instance import _generate_candidate as generate_graph_candidate  # noqa: E402
from jobshop_instance import _build_jobs  # noqa: E402
from portfolio_problem import build_portfolio  # noqa: E402
from prompt import CANONICAL_SYSTEM_PROMPT  # noqa: E402
from steiner_coloring_instance import _canonical_spec, _generate_candidate as generate_steiner_candidate  # noqa: E402
from tsp_instance import _draw_coords  # noqa: E402


SEEDS = (1,)
OUTPUT_PATH = REPO_ROOT / "kaggle" / "examples" / "portfolio_spike" / "portfolio_spike.py"
MODULE_FILES = (
    "graph_coloring_instance.py",
    "jobshop_instance.py",
    "steiner_coloring_instance.py",
    "tsp_instance.py",
    "verify.py",
)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if is_dataclass(value):
        return {field: _json_safe(getattr(value, field)) for field in value.__dataclass_fields__}
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    raise TypeError(f"Unsupported value for serialization: {type(value).__name__}")


def _jobshop_signature(problem: Any) -> list[dict[str, Any]]:
    return _json_safe(problem.instance.jobs)


def _jobshop_attempts(problem: Any) -> int:
    target = _jobshop_signature(problem)
    for attempt in range(20):
        attempt_seed = problem.instance.seed if attempt == 0 else problem.instance.seed * 10_000 + attempt
        jobs = _build_jobs(
            Random(attempt_seed),
            n_jobs=problem.instance.n_jobs,
            n_machines=problem.instance.n_machines,
            duration_low=1,
            duration_high=9,
        )
        if _json_safe(jobs) == target:
            return attempt + 1
    raise RuntimeError(f"Unable to recover accepted jobshop attempt for seed={problem.instance.seed}")


def _tsp_attempts(problem: Any) -> int:
    target = _json_safe(problem.instance.coords)
    for attempt in range(60):
        attempt_seed = problem.instance.seed if attempt == 0 else problem.instance.seed * 10_000 + attempt
        coords = _draw_coords(
            attempt_seed,
            n_cities=len(problem.instance.coords),
            coord_max=100,
        )
        if _json_safe(coords) == target:
            return attempt + 1
    raise RuntimeError(f"Unable to recover accepted TSP attempt for seed={problem.instance.seed}")


def _graph_attempts(problem: Any) -> int:
    target = {
        "nodes": _json_safe(problem.instance.nodes),
        "edges": _json_safe(problem.instance.edges),
        "planted_assignment": _json_safe(problem.instance.planted_assignment),
    }
    for attempt in range(80):
        attempt_seed = problem.instance.seed if attempt == 0 else problem.instance.seed * 10_000 + attempt
        nodes, planted_assignment, edges = generate_graph_candidate(
            seed=attempt_seed,
            n_nodes=problem.instance.n_nodes,
            num_colors=problem.instance.num_colors,
        )
        candidate = {
            "nodes": _json_safe(nodes),
            "edges": _json_safe(edges),
            "planted_assignment": _json_safe(planted_assignment),
        }
        if candidate == target:
            return attempt + 1
    raise RuntimeError(f"Unable to recover accepted graph-coloring attempt for seed={problem.instance.seed}")


def _steiner_attempts(problem: Any) -> int:
    target = {
        "villages": _json_safe(problem.instance.villages),
        "terminals": _json_safe(problem.instance.terminals),
        "edges": _json_safe(problem.instance.edges),
        "interference_pairs": _json_safe(problem.instance.interference_pairs),
    }
    for attempt in range(80):
        if (
            problem.instance.seed == 1
            and problem.instance.n == 8
            and problem.instance.k == 3
            and len(problem.instance.terminals) == 3
            and attempt == 0
        ):
            villages, terminals, edges, interference_pairs = _canonical_spec()
        else:
            attempt_seed = problem.instance.seed if attempt == 0 else problem.instance.seed * 10_000 + attempt
            villages, terminals, edges, interference_pairs = generate_steiner_candidate(
                seed=attempt_seed,
                n=problem.instance.n,
                k=problem.instance.k,
                n_terminals=len(problem.instance.terminals),
            )
        candidate = {
            "villages": _json_safe(villages),
            "terminals": _json_safe(terminals),
            "edges": _json_safe(edges),
            "interference_pairs": _json_safe(interference_pairs),
        }
        if candidate == target:
            return attempt + 1
    raise RuntimeError(f"Unable to recover accepted steiner attempt for seed={problem.instance.seed}")


def _problem_kind(problem_id: str) -> str:
    return {
        "P1": "jobshop",
        "P2": "steiner",
        "P3": "tsp",
        "P4": "graph_coloring",
    }[problem_id]


def _generation_attempts(problem: Any) -> int:
    if problem.problem_id == "P1":
        return _jobshop_attempts(problem)
    if problem.problem_id == "P2":
        return _steiner_attempts(problem)
    if problem.problem_id == "P3":
        return _tsp_attempts(problem)
    if problem.problem_id == "P4":
        return _graph_attempts(problem)
    raise ValueError(f"Unknown problem id: {problem.problem_id}")


def _serialize_problem(problem: Any) -> dict[str, Any]:
    return {
        "problem_id": problem.problem_id,
        "kind": _problem_kind(problem.problem_id),
        "label": problem.label,
        "short_label": problem.short_label,
        "value_cap": problem.value_cap,
        "metric_name": problem.metric_name,
        "baseline_score": problem.baseline_score,
        "gold_score": problem.gold_score,
        "baseline_answer": _json_safe(problem.baseline_answer),
        "gold_answer": _json_safe(problem.gold_answer),
        "problem_statement": problem.problem_statement,
        "answer_contract": problem.answer_contract,
        "gold_method": problem.gold_method,
        "gold_wall_seconds": problem.gold_wall_seconds,
        "baseline_gap_pct": problem.baseline_gap_pct,
        "generation_attempts": _generation_attempts(problem),
        "instance": _json_safe(problem.instance),
    }


def _build_embedded_portfolio() -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for seed in SEEDS:
        problems = build_portfolio(seed=seed, min_baseline_gap_pct=15.0)
        payload[str(seed)] = {
            "seed": seed,
            "problems": [_serialize_problem(problem) for problem in problems],
        }
    return payload


def _bundle_modules() -> dict[str, str]:
    payload: dict[str, str] = {}
    for filename in MODULE_FILES:
        source = (PORTFOLIO_DIR / filename).read_text(encoding="utf-8")
        payload[filename] = base64.b64encode(source.encode("utf-8")).decode("ascii")
    return payload


TASK_TEMPLATE = Template(
    textwrap.dedent(
        """\
        from __future__ import annotations

        import ast
        import base64
        import json
        import os
        import re
        import sys
        import tempfile
        import threading
        import time
        from dataclasses import dataclass
        from pathlib import Path
        from typing import Any, Callable

        import kaggle_benchmarks as kbench

        SEED = int(globals().get("PORTFOLIO_TARGET_SEED", 1))
        TOTAL_BUDGET_S = 1800
        PLAN_TURN_BUDGET_S = 300
        MAX_SUBTASK_BUDGET_S = 600
        MAX_EXEC_TURNS = 8
        COST_PER_SECOND = 0.05
        FORECAST_KEYS = ("p_within_5pct", "p_within_10pct", "p_within_20pct", "p_within_50pct")
        STOP_TOKENS = {"stop_economic", "stop_budget"}

        CANONICAL_SYSTEM_PROMPT = $SYSTEM_PROMPT_JSON
        EMBEDDED_MODULES = $MODULE_BUNDLE_JSON
        PORTFOLIO_DATA_BY_SEED = $PORTFOLIO_JSON

        _SUB_RE = re.compile(
            r"^\\s*\\**\\s*SUB_(\\d+)_RESULT\\**\\s*:\\s*(.*?)(?=^\\s*\\**\\s*[A-Z][A-Z0-9_]*\\**\\s*:|\\Z)",
            re.DOTALL | re.MULTILINE,
        )


        def _ensure_bundle() -> None:
            bundle_dir = Path(tempfile.gettempdir()) / "voicetree_portfolio_spike_bundle"
            bundle_dir.mkdir(parents=True, exist_ok=True)
            for filename, encoded in EMBEDDED_MODULES.items():
                path = bundle_dir / filename
                source = base64.b64decode(encoded).decode("utf-8")
                if not path.exists() or path.read_text(encoding="utf-8") != source:
                    path.write_text(source, encoding="utf-8")
            if str(bundle_dir) not in sys.path:
                sys.path.insert(0, str(bundle_dir))


        _ensure_bundle()

        from graph_coloring_instance import (  # noqa: E402
            GraphColoringInstance,
            solution_summary as graph_coloring_summary,
            verify_answer as verify_graph_coloring_answer,
        )
        from jobshop_instance import (  # noqa: E402
            CoupledJobShopInstance,
            JobSpec,
            OperationSpec,
            schedule_summary,
            verify_schedule,
        )
        from steiner_coloring_instance import (  # noqa: E402
            EdgeSpec,
            SteinerColoringInstance,
            solution_summary as steiner_solution_summary,
        )
        from tsp_instance import TSPInstance, tour_summary, verify_tour  # noqa: E402
        from verify import verify_answer as verify_steiner_answer  # noqa: E402


        @dataclass(frozen=True)
        class VerificationOutcome:
            feasible: bool
            score: float | None
            failure_reason: str | None
            normalized_answer: Any | None
            details: dict[str, Any]


        @dataclass(frozen=True)
        class PreparedProblem:
            kind: str
            problem_id: str
            label: str
            short_label: str
            value_cap: int
            metric_name: str
            baseline_score: float
            gold_score: float
            baseline_answer: Any
            gold_answer: Any
            problem_statement: str
            answer_contract: str
            instance: Any
            gold_method: str
            gold_wall_seconds: float
            generation_attempts: int
            verify_answer: Callable[[Any], VerificationOutcome]
            summarize_answer: Callable[[Any, float | None], str]

            @property
            def baseline_gap_pct(self) -> float:
                return 100.0 * (self.baseline_score - self.gold_score) / self.gold_score

            def gap_pct_for_score(self, score: float) -> float:
                return 100.0 * (score - self.gold_score) / self.gold_score

            def headroom_fraction(self, score: float) -> float:
                denom = self.baseline_score - self.gold_score
                if denom <= 0:
                    return 0.0
                ratio = (self.baseline_score - score) / denom
                return max(0.0, min(1.0, ratio))

            def value_captured(self, score: float) -> float:
                return self.value_cap * self.headroom_fraction(score)

            def realized_bucket(self, score: float) -> str:
                gap_pct = self.gap_pct_for_score(score)
                if gap_pct <= 5.0:
                    return "within_5pct"
                if gap_pct <= 10.0:
                    return "within_10pct"
                if gap_pct <= 20.0:
                    return "within_20pct"
                if gap_pct <= 50.0:
                    return "within_50pct"
                return "miss"


        def _clone_jsonish(value: Any) -> Any:
            return json.loads(json.dumps(value))


        def _safe_float(value: Any) -> float | None:
            try:
                return float(value)
            except Exception:
                return None


        def forecast_event_map(problem: PreparedProblem, score: float) -> dict[str, float]:
            gap_pct = problem.gap_pct_for_score(score)
            return {
                "p_within_5pct": float(gap_pct <= 5.0),
                "p_within_10pct": float(gap_pct <= 10.0),
                "p_within_20pct": float(gap_pct <= 20.0),
                "p_within_50pct": float(gap_pct <= 50.0),
            }


        def _deserialize_jobshop_instance(data: dict[str, Any]) -> CoupledJobShopInstance:
            def _op(raw: dict[str, Any]) -> OperationSpec:
                return OperationSpec(
                    machine_name=str(raw["machine_name"]),
                    duration=int(raw["duration"]),
                )

            def _job(raw: dict[str, Any]) -> JobSpec:
                return JobSpec(
                    job_id=int(raw["job_id"]),
                    factory_a=tuple(_op(item) for item in raw["factory_a"]),
                    factory_b=tuple(_op(item) for item in raw["factory_b"]),
                )

            return CoupledJobShopInstance(
                seed=int(data["seed"]),
                n_jobs=int(data["n_jobs"]),
                n_machines=int(data["n_machines"]),
                jobs=tuple(_job(item) for item in data["jobs"]),
                baseline_schedule=_clone_jsonish(data["baseline_schedule"]),
                baseline_makespan=int(data["baseline_makespan"]),
                optimal_schedule=_clone_jsonish(data["optimal_schedule"]),
                optimal_makespan=int(data["optimal_makespan"]),
                problem_statement=str(data["problem_statement"]),
            )


        def _deserialize_steiner_instance(data: dict[str, Any]) -> SteinerColoringInstance:
            return SteinerColoringInstance(
                seed=int(data["seed"]),
                n=int(data["n"]),
                k=int(data["k"]),
                villages=tuple(str(item) for item in data["villages"]),
                terminals=tuple(str(item) for item in data["terminals"]),
                edges=tuple(
                    EdgeSpec(
                        u=str(item["u"]),
                        v=str(item["v"]),
                        cost=int(item["cost"]),
                    )
                    for item in data["edges"]
                ),
                interference_pairs=tuple((str(left), str(right)) for left, right in data["interference_pairs"]),
                baseline_answer=_clone_jsonish(data["baseline_answer"]),
                baseline_cost=int(data["baseline_cost"]),
                cable_only_answer=_clone_jsonish(data["cable_only_answer"]),
                cable_only_cost=(None if data["cable_only_cost"] is None else int(data["cable_only_cost"])),
                optimal_answer=_clone_jsonish(data["optimal_answer"]),
                optimal_cost=(None if data["optimal_cost"] is None else int(data["optimal_cost"])),
                problem_statement=str(data["problem_statement"]),
            )


        def _deserialize_tsp_instance(data: dict[str, Any]) -> TSPInstance:
            return TSPInstance(
                seed=int(data["seed"]),
                coords=tuple((int(x), int(y)) for x, y in data["coords"]),
                baseline_tour=tuple(int(item) for item in data["baseline_tour"]),
                baseline_length=float(data["baseline_length"]),
                optimal_tour=tuple(int(item) for item in data["optimal_tour"]),
                optimal_length=float(data["optimal_length"]),
                problem_statement=str(data["problem_statement"]),
            )


        def _deserialize_graph_instance(data: dict[str, Any]) -> GraphColoringInstance:
            return GraphColoringInstance(
                seed=int(data["seed"]),
                n_nodes=int(data["n_nodes"]),
                num_colors=int(data["num_colors"]),
                nodes=tuple(str(item) for item in data["nodes"]),
                edges=tuple((str(left), str(right)) for left, right in data["edges"]),
                planted_assignment={str(key): int(value) for key, value in data["planted_assignment"].items()},
                baseline_answer=_clone_jsonish(data["baseline_answer"]),
                baseline_conflicts=int(data["baseline_conflicts"]),
                optimal_answer=_clone_jsonish(data["optimal_answer"]),
                optimal_conflicts=int(data["optimal_conflicts"]),
                problem_statement=str(data["problem_statement"]),
            )


        def _build_problem(problem_data: dict[str, Any]) -> PreparedProblem:
            kind = str(problem_data["kind"])
            if kind == "jobshop":
                instance = _deserialize_jobshop_instance(problem_data["instance"])

                def verify(answer: Any) -> VerificationOutcome:
                    result = verify_schedule(
                        jobs=instance.jobs,
                        n_machines=instance.n_machines,
                        schedule=answer,
                    )
                    return VerificationOutcome(
                        feasible=result.is_feasible,
                        score=(float(result.verified_makespan) if result.verified_makespan is not None else None),
                        failure_reason=result.failure_reason,
                        normalized_answer=answer if result.is_feasible else None,
                        details={"verified_makespan": result.verified_makespan},
                    )

                summarize = lambda answer, score: schedule_summary(answer)
            elif kind == "steiner":
                instance = _deserialize_steiner_instance(problem_data["instance"])

                def verify(answer: Any) -> VerificationOutcome:
                    result = verify_steiner_answer(instance, answer)
                    return VerificationOutcome(
                        feasible=result.feasible,
                        score=(float(result.computed_cost) if result.computed_cost is not None else None),
                        failure_reason=result.failure_reason,
                        normalized_answer=result.normalized_answer,
                        details={
                            "edge_cost": result.edge_cost,
                            "num_frequencies_used": result.num_frequencies_used,
                            "computed_cost": result.computed_cost,
                        },
                    )

                summarize = lambda answer, score: steiner_solution_summary(
                    instance,
                    answer,
                    None if score is None else int(round(score)),
                )
            elif kind == "tsp":
                instance = _deserialize_tsp_instance(problem_data["instance"])

                def verify(answer: Any) -> VerificationOutcome:
                    result = verify_tour(instance, answer)
                    return VerificationOutcome(
                        feasible=result.feasible,
                        score=result.computed_length,
                        failure_reason=result.failure_reason,
                        normalized_answer=(list(result.normalized_tour) if result.normalized_tour is not None else None),
                        details={"computed_length": result.computed_length},
                    )

                summarize = lambda answer, score: tour_summary(instance, answer, score)
            elif kind == "graph_coloring":
                instance = _deserialize_graph_instance(problem_data["instance"])

                def verify(answer: Any) -> VerificationOutcome:
                    result = verify_graph_coloring_answer(instance, answer)
                    return VerificationOutcome(
                        feasible=result.feasible,
                        score=(float(result.computed_cost) if result.computed_cost is not None else None),
                        failure_reason=result.failure_reason,
                        normalized_answer=result.normalized_answer,
                        details={
                            "conflict_count": result.conflict_count,
                            "computed_cost": result.computed_cost,
                        },
                    )

                summarize = lambda answer, score: graph_coloring_summary(
                    instance,
                    answer,
                    None if score is None else int(round(score - 4)),
                )
            else:
                raise RuntimeError(f"Unknown problem kind: {kind}")

            return PreparedProblem(
                kind=kind,
                problem_id=str(problem_data["problem_id"]),
                label=str(problem_data["label"]),
                short_label=str(problem_data["short_label"]),
                value_cap=int(problem_data["value_cap"]),
                metric_name=str(problem_data["metric_name"]),
                baseline_score=float(problem_data["baseline_score"]),
                gold_score=float(problem_data["gold_score"]),
                baseline_answer=_clone_jsonish(problem_data["baseline_answer"]),
                gold_answer=_clone_jsonish(problem_data["gold_answer"]),
                problem_statement=str(problem_data["problem_statement"]),
                answer_contract=str(problem_data["answer_contract"]),
                instance=instance,
                gold_method=str(problem_data["gold_method"]),
                gold_wall_seconds=float(problem_data["gold_wall_seconds"]),
                generation_attempts=int(problem_data["generation_attempts"]),
                verify_answer=verify,
                summarize_answer=summarize,
            )


        def _portfolio_for_seed(seed: int) -> list[PreparedProblem]:
            payload = PORTFOLIO_DATA_BY_SEED.get(str(seed))
            if payload is None:
                raise RuntimeError(f"Unsupported seed {seed}. Expected one of {sorted(PORTFOLIO_DATA_BY_SEED)}.")
            return [_build_problem(problem_data) for problem_data in payload["problems"]]


        def _extract_label_block(text: str, label: str) -> str | None:
            pattern = re.compile(
                rf"^\\s*\\**\\s*{re.escape(label)}\\**\\s*:\\s*(.*?)(?=^\\s*\\**\\s*[A-Z][A-Z0-9_]*\\**\\s*:|\\Z)",
                re.DOTALL | re.MULTILINE,
            )
            match = pattern.search(text)
            if not match:
                return None
            return match.group(1).strip()


        def _extract_forecast(text: str) -> tuple[str, dict[str, float]] | None:
            pattern = re.compile(
                r"^\\s*\\**\\s*FORECAST_(P\\d+)\\**\\s*:\\s*(.*?)(?=^\\s*\\**\\s*[A-Z][A-Z0-9_]*\\**\\s*:|\\Z)",
                re.DOTALL | re.MULTILINE | re.IGNORECASE,
            )
            match = pattern.search(text)
            if not match:
                return None
            problem_id = match.group(1).upper()
            parsed = _parse_value_loose(match.group(2).strip())
            if not isinstance(parsed, dict):
                return None
            normalized = _normalize_forecast(parsed)
            if normalized is None:
                return None
            return problem_id, normalized


        def _strip_code_fences(text: str) -> str:
            stripped = text.strip()
            if stripped.startswith("```") and stripped.endswith("```"):
                lines = stripped.splitlines()
                if len(lines) >= 2:
                    return "\\n".join(lines[1:-1]).strip()
            return stripped


        def _parse_value_loose(text: str | None) -> Any:
            if text is None:
                return None
            stripped = _strip_code_fences(text.strip())
            if not stripped:
                return None
            for parser in (json.loads, ast.literal_eval):
                try:
                    return parser(stripped)
                except Exception:
                    continue
            if re.fullmatch(r"-?\\d+", stripped):
                try:
                    return int(stripped)
                except Exception:
                    return stripped
            return stripped


        def _lookup_key(mapping: dict[str, Any], *names: str) -> Any:
            upper_map = {str(key).strip().upper(): value for key, value in mapping.items()}
            for name in names:
                if name.upper() in upper_map:
                    return upper_map[name.upper()]
            return None


        def _normalize_forecast(raw: dict[str, Any]) -> dict[str, float] | None:
            lower_map = {str(key).strip().lower(): value for key, value in raw.items()}
            normalized: dict[str, float] = {}
            for key in FORECAST_KEYS:
                value = _safe_float(lower_map.get(key.lower()))
                if value is None or not 0.0 <= value <= 1.0:
                    return None
                normalized[key] = value
            ordered = [normalized[key] for key in FORECAST_KEYS]
            if ordered != sorted(ordered):
                return None
            return normalized


        def _normalize_next_sub_id(raw: Any) -> int | str | None:
            if isinstance(raw, int):
                return raw
            if isinstance(raw, str):
                stripped = raw.strip()
                if stripped in STOP_TOKENS:
                    return stripped
                if re.fullmatch(r"\\d+", stripped):
                    return int(stripped)
            return None


        def _normalize_plan_item(
            raw: dict[str, Any],
            *,
            prior: dict[str, Any] | None,
            require_status: bool,
            allowed_problem_ids: set[str],
        ) -> dict[str, Any] | None:
            try:
                item_id = int(raw.get("id"))
            except Exception:
                return None

            raw_status = raw.get("status", prior.get("status") if prior else None)
            if raw_status is None and not require_status:
                status = "pending"
            else:
                status_text = str(raw_status).strip().lower() if raw_status is not None else ""
                status_map = {
                    "pending": "pending",
                    "done": "done",
                    "skip": "skipped",
                    "skipped": "skipped",
                }
                status = status_map.get(status_text)
                if status is None:
                    return None

            problem_id = raw.get("problem", prior.get("problem") if prior else None)
            if problem_id is None:
                return None
            problem_id = str(problem_id).strip().upper()
            if problem_id not in allowed_problem_ids:
                return None

            desc = str(raw.get("desc", prior.get("desc") if prior else "")).strip()
            if not desc:
                return None

            raw_budget = raw.get("budget_s", prior.get("budget_s") if prior else None)
            if raw_budget is None:
                return None
            try:
                budget_s = int(raw_budget)
            except Exception:
                return None
            if budget_s <= 0:
                return None
            budget_s = min(budget_s, MAX_SUBTASK_BUDGET_S)

            realized_bucket = raw.get("realized_bucket", prior.get("realized_bucket") if prior else None)
            if realized_bucket is not None:
                realized_bucket = str(realized_bucket).strip().lower()
                if realized_bucket not in {"within_5pct", "within_10pct", "within_20pct", "within_50pct", "miss"}:
                    realized_bucket = None

            item = {
                "id": item_id,
                "problem": problem_id,
                "desc": desc,
                "budget_s": budget_s,
                "status": status,
            }
            if realized_bucket is not None:
                item["realized_bucket"] = realized_bucket
            return item


        def _normalize_plan(
            raw_plan: Any,
            *,
            prior_plan: list[dict[str, Any]] | None,
            require_status: bool,
            allowed_problem_ids: set[str],
        ) -> list[dict[str, Any]] | None:
            if not isinstance(raw_plan, list):
                return None
            prior_by_id = {item["id"]: item for item in prior_plan or []}
            normalized: list[dict[str, Any]] = []
            seen: set[int] = set()
            for raw_item in raw_plan:
                if not isinstance(raw_item, dict):
                    return None
                raw_item_id = raw_item.get("id")
                try:
                    prior_key = int(raw_item_id)
                except Exception:
                    prior_key = -1
                item = _normalize_plan_item(
                    raw_item,
                    prior=prior_by_id.get(prior_key),
                    require_status=require_status,
                    allowed_problem_ids=allowed_problem_ids,
                )
                if item is None or item["id"] in seen:
                    return None
                normalized.append(item)
                seen.add(item["id"])
            return normalized


        def _parse_plan_turn(text: str, problem_ids: set[str]) -> dict[str, Any] | None:
            plan_value = _parse_value_loose(_extract_label_block(text, "PLAN"))
            next_sub_value = _parse_value_loose(_extract_label_block(text, "NEXT_SUB_ID"))
            if plan_value is None or next_sub_value is None:
                top_level = _parse_value_loose(text)
                if isinstance(top_level, dict):
                    plan_value = plan_value or _lookup_key(top_level, "PLAN")
                    next_sub_value = next_sub_value or _lookup_key(top_level, "NEXT_SUB_ID")

            plan = _normalize_plan(
                plan_value,
                prior_plan=None,
                require_status=False,
                allowed_problem_ids=problem_ids,
            )
            next_sub_id = _normalize_next_sub_id(next_sub_value)
            if plan is None or not isinstance(next_sub_id, int):
                return None
            if next_sub_id not in {item["id"] for item in plan}:
                return None
            return {"plan": plan, "next_sub_id": next_sub_id}


        def _parse_exec_turn(
            text: str,
            *,
            prior_plan: list[dict[str, Any]],
            expected_problem_id: str,
            problem_ids: set[str],
        ) -> dict[str, Any] | None:
            candidate_value = _parse_value_loose(_extract_label_block(text, "CANDIDATE"))
            revised_plan_value = _parse_value_loose(_extract_label_block(text, "REVISED_PLAN"))
            next_sub_value = _parse_value_loose(_extract_label_block(text, "NEXT_SUB_ID"))
            forecast = _extract_forecast(text)
            sub_match = _SUB_RE.search(text)

            if candidate_value is None or revised_plan_value is None or next_sub_value is None or forecast is None or sub_match is None:
                top_level = _parse_value_loose(text)
                if isinstance(top_level, dict):
                    candidate_value = candidate_value or _lookup_key(top_level, "CANDIDATE")
                    revised_plan_value = revised_plan_value or _lookup_key(top_level, "REVISED_PLAN")
                    next_sub_value = next_sub_value or _lookup_key(top_level, "NEXT_SUB_ID")
                    if forecast is None:
                        for key, value in top_level.items():
                            match = re.match(r"^FORECAST_(P\\d+)$$", str(key).strip(), re.IGNORECASE)
                            if match:
                                normalized = _normalize_forecast(value) if isinstance(value, dict) else None
                                if normalized is not None:
                                    forecast = (match.group(1).upper(), normalized)
                                    break
                    if sub_match is None:
                        for key in top_level:
                            sub_key_match = re.match(r"^SUB_(\\d+)_RESULT$$", str(key).strip(), re.IGNORECASE)
                            if sub_key_match:
                                sub_match = sub_key_match
                                break

            revised_plan = _normalize_plan(
                revised_plan_value,
                prior_plan=prior_plan,
                require_status=True,
                allowed_problem_ids=problem_ids,
            )
            next_sub_id = _normalize_next_sub_id(next_sub_value)
            if (
                not isinstance(candidate_value, dict)
                or revised_plan is None
                or next_sub_id is None
                or forecast is None
                or sub_match is None
            ):
                return None
            problem_id = str(candidate_value.get("problem", "")).strip().upper()
            answer = candidate_value.get("answer")
            if problem_id != expected_problem_id or forecast[0] != expected_problem_id:
                return None
            return {
                "subtask_id": int(sub_match.group(1)),
                "candidate": {"problem": problem_id, "answer": answer},
                "forecast": forecast[1],
                "revised_plan": revised_plan,
                "next_sub_id": next_sub_id,
            }


        def _merge_revised_plan(
            proposed_plan: list[dict[str, Any]],
            *,
            prior_plan: list[dict[str, Any]],
            executed_item: dict[str, Any],
            realized_bucket: str,
        ) -> list[dict[str, Any]]:
            by_id = {item["id"]: dict(item) for item in proposed_plan}
            if executed_item["id"] not in by_id:
                by_id[executed_item["id"]] = dict(executed_item)
            executed = by_id[executed_item["id"]]
            executed["status"] = "done"
            executed["problem"] = executed_item["problem"]
            executed["desc"] = executed_item["desc"]
            executed["budget_s"] = executed_item["budget_s"]
            executed["realized_bucket"] = realized_bucket

            for item in prior_plan:
                if item["id"] not in by_id and item.get("status") == "done":
                    by_id[item["id"]] = dict(item)

            return [by_id[item_id] for item_id in sorted(by_id)]


        def _plan_delta(previous: list[dict[str, Any]], current: list[dict[str, Any]]) -> dict[str, Any]:
            previous_by_id = {item["id"]: item for item in previous}
            current_by_id = {item["id"]: item for item in current}
            additions = sorted(item_id for item_id in current_by_id if item_id not in previous_by_id)
            revisions = sorted(
                item_id
                for item_id in current_by_id
                if item_id in previous_by_id
                and any(
                    current_by_id[item_id].get(field) != previous_by_id[item_id].get(field)
                    for field in ("problem", "desc", "budget_s")
                )
            )
            status_flips = sorted(
                item_id
                for item_id in current_by_id
                if item_id in previous_by_id
                and current_by_id[item_id].get("status") != previous_by_id[item_id].get("status")
            )
            return {
                "plan_size": len(current),
                "additions": additions,
                "revisions": revisions,
                "status_flips": status_flips,
            }


        def _fmt_token(value: Any) -> str:
            return "NA" if value is None else str(value)


        def _fmt_metric(value: float) -> str:
            if abs(value - round(value)) < 1e-9:
                return str(int(round(value)))
            return f"{value:.3f}"


        def _call_model(llm: Any, prompt: str, timeout_s: int) -> dict[str, Any]:
            start = time.monotonic()
            _result: list[Any] = [None]
            _error: list[BaseException | None] = [None]

            def _respond() -> None:
                try:
                    kbench.actors.user.send(prompt)
                    _result[0] = llm.respond(system=CANONICAL_SYSTEM_PROMPT, temperature=0)
                except BaseException as exc:  # noqa: BLE001
                    _error[0] = exc

            thread = threading.Thread(target=_respond, daemon=True)
            thread.start()
            thread.join(timeout=timeout_s)
            wall_seconds = time.monotonic() - start

            if thread.is_alive():
                return {
                    "text": "",
                    "wall_seconds": wall_seconds,
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "thinking_tokens": None,
                    "timed_out": True,
                }

            if _error[0] is not None:
                raise _error[0]

            response = _result[0]
            meta = getattr(response, "_meta", {}) or {}
            return {
                "text": str(response.content or "").strip(),
                "wall_seconds": wall_seconds,
                "input_tokens": meta.get("input_tokens"),
                "output_tokens": meta.get("output_tokens"),
                "total_tokens": meta.get("total_tokens"),
                "thinking_tokens": meta.get("thinking_tokens"),
                "timed_out": wall_seconds > timeout_s,
            }


        def format_turn1_prompt(problems: list[PreparedProblem]) -> str:
            lines = [
                f"TOTAL_WALL_BUDGET_S: {TOTAL_BUDGET_S}",
                f"COST_PER_SECOND: {COST_PER_SECOND:.2f}",
                f"SUBTASK_BUDGET_CAP_S: {MAX_SUBTASK_BUDGET_S}",
                "Session score = sum(value captured per problem) - COST_PER_SECOND * total_wall_seconds.",
                "Value captured per problem is clipped to [0, value_cap].",
                "Turn 1 is planning only: do not emit any candidate artifact yet.",
                "Build a short portfolio allocation plan over these four problems.",
                "",
                "Portfolio baseline state:",
            ]
            for problem in problems:
                lines.append(
                    f"- {problem.problem_id} | {problem.label} | value_cap={problem.value_cap} | "
                    f"baseline_{problem.metric_name}={_fmt_metric(problem.baseline_score)}"
                )
            lines.append("")
            for problem in problems:
                lines.extend(
                    [
                        f"=== {problem.problem_id}: {problem.label} ===",
                        problem.problem_statement,
                        f"When you touch {problem.problem_id}, emit CANDIDATE.answer in this shape:",
                        problem.answer_contract,
                    ]
                )
                if problem.problem_id == "P1":
                    lines.append(
                        "If your approach corresponds to a named decomposition strategy "
                        "(e.g. bottleneck-first, family-first, outlier-first, due-date-first, composite), "
                        "note it in the plan description."
                    )
                lines.append("")
            lines.extend(
                [
                    "Use this exact output contract:",
                    'PLAN: [{"id": 1, "problem": "P1", "desc": "...", "budget_s": 240}, ...]',
                    "NEXT_SUB_ID: 1",
                    "Requirements:",
                    "- PLAN can include any subset of P1..P4 and may contain multiple subtasks for the same problem.",
                    "- desc should be short and should not restate the problem text.",
                    f"- budget_s must be a positive integer no larger than {MAX_SUBTASK_BUDGET_S}.",
                    "- NEXT_SUB_ID must point to one plan item in PLAN.",
                ]
            )
            return "\\n".join(lines)


        def format_exec_prompt(
            *,
            turn_number: int,
            previous_turn: dict[str, Any],
            elapsed_s: float,
            problems_by_id: dict[str, PreparedProblem],
            current_answers: dict[str, Any],
            current_scores: dict[str, float],
            plan_state: list[dict[str, Any]],
            next_sub: dict[str, Any],
        ) -> str:
            remaining_s = max(0.0, TOTAL_BUDGET_S - elapsed_s)
            prev_wall = previous_turn.get("wall_seconds")
            prev_input = previous_turn.get("input_tokens")
            prev_output = previous_turn.get("output_tokens")
            prev_total = previous_turn.get("total_tokens")

            status_lines = []
            for problem_id in sorted(problems_by_id):
                problem = problems_by_id[problem_id]
                current_score = current_scores[problem_id]
                gap_pct = problem.gap_pct_for_score(current_score)
                value = problem.value_captured(current_score)
                status_lines.append(
                    f"- {problem_id} {problem.short_label}: current_{problem.metric_name}={_fmt_metric(current_score)}, "
                    f"baseline={_fmt_metric(problem.baseline_score)}, gap_pct={gap_pct:.2f}, "
                    f"value={value:.2f}/{problem.value_cap}"
                )

            target_problem = problems_by_id[next_sub["problem"]]
            target_answer = current_answers[next_sub["problem"]]
            target_score = current_scores[next_sub["problem"]]
            target_answer_json = json.dumps(target_answer, indent=2, sort_keys=True)
            plan_json = json.dumps(plan_state, indent=2, sort_keys=True)
            axis_note = ""
            if target_problem.problem_id == "P1":
                axis_note = (
                    "If you add or revise a P1 subtask and it corresponds to a named decomposition strategy "
                    "(e.g. bottleneck-first, family-first, outlier-first, due-date-first, composite), "
                    "note it in the plan description.\\n"
                )

            return (
                f"TURN_{turn_number - 1} STATS: wall={prev_wall:.1f}s, input_tok={_fmt_token(prev_input)}, "
                f"output_tok={_fmt_token(prev_output)}, total_tok={_fmt_token(prev_total)}\\n"
                f"CUMULATIVE: wall={elapsed_s:.1f}s / {TOTAL_BUDGET_S}s, remaining={remaining_s:.1f}s\\n"
                f"CURRENT_SUBTASK: id={next_sub['id']} problem={next_sub['problem']} budget_s={next_sub['budget_s']}\\n"
                f"SUBTASK_DESC: {next_sub['desc']}\\n"
                "PORTFOLIO_STATUS:\\n"
                f"{chr(10).join(status_lines)}\\n"
                "CURRENT_PLAN_JSON:\\n"
                f"{plan_json}\\n"
                f"TARGET_PROBLEM_SPEC ({target_problem.problem_id}):\\n"
                f"{target_problem.problem_statement}\\n"
                f"CURRENT_BEST_{target_problem.metric_name.upper()}: {_fmt_metric(target_score)}\\n"
                "CURRENT_BEST_SUMMARY:\\n"
                f"{target_problem.summarize_answer(target_answer, target_score)}\\n"
                "CURRENT_BEST_JSON:\\n"
                f"{target_answer_json}\\n"
                "CANDIDATE_ANSWER_SHAPE:\\n"
                f"{target_problem.answer_contract}\\n"
                "Now execute the current subtask, then revise the plan state.\\n"
                "REVISED_PLAN must be the full revised plan state, not just the delta.\\n"
                "FORECAST for the touched problem means the probability that the current best answer for that problem "
                "is within the stated gap threshold relative to that problem's offline gold.\\n"
                f"{axis_note}"
                "Use this exact output contract:\\n"
                f"SUB_{turn_number - 1}_RESULT: <work + candidate artifact summary>\\n"
                f'CANDIDATE: {{"problem": "{target_problem.problem_id}", "answer": <full valid answer for {target_problem.problem_id}>}}\\n'
                f'FORECAST_{target_problem.problem_id}: {{"p_within_5pct": <float>, "p_within_10pct": <float>, '
                '"p_within_20pct": <float>, "p_within_50pct": <float>}}\\n'
                'REVISED_PLAN: [{"id": 1, "status": "done", "realized_bucket": "within_20pct"}, ...]\\n'
                "NEXT_SUB_ID: <int> | stop_economic | stop_budget\\n"
                "Rules:\\n"
                "- If you touch a problem, emit a full candidate artifact for that problem.\\n"
                "- Forecast probabilities must be between 0 and 1 and monotone non-decreasing across thresholds.\\n"
                "- If the executed subtask is finished, mark it done and put any follow-up as a new id.\\n"
                "- If you want to stop because further work is not worth its cost, use stop_economic.\\n"
            )


        def _extract_declared_axis(plan_items: list[dict[str, Any]] | None) -> str | None:
            if not plan_items:
                return None
            axis_map = {
                "bottleneck-first": "bottleneck-first",
                "bottleneck first": "bottleneck-first",
                "family-first": "family-first",
                "family first": "family-first",
                "outlier-first": "outlier-first",
                "outlier first": "outlier-first",
                "due-date-first": "due-date-first",
                "due date first": "due-date-first",
                "composite": "composite",
            }
            for item in plan_items:
                if str(item.get("problem", "")).upper() != "P1":
                    continue
                desc = str(item.get("desc", "")).strip().lower()
                for token, canonical in axis_map.items():
                    if token in desc:
                        return canonical
            return None


        def run_protocol(llm: Any, problems: list[PreparedProblem], model_name: str) -> dict[str, Any]:
            run_start = time.monotonic()
            problems_by_id = {problem.problem_id: problem for problem in problems}
            problem_ids = set(problems_by_id)
            turns: list[dict[str, Any]] = []
            current_answers = {problem.problem_id: _clone_jsonish(problem.baseline_answer) for problem in problems}
            current_scores = {problem.problem_id: float(problem.baseline_score) for problem in problems}
            current_sources = {problem.problem_id: "baseline" for problem in problems}
            forecast_history = {problem.problem_id: [] for problem in problems}
            per_problem_turns = {problem.problem_id: [] for problem in problems}
            plan_evolution: list[dict[str, Any]] = []
            initial_plan: list[dict[str, Any]] | None = None
            plan_state: list[dict[str, Any]] = []
            next_sub_id: int | str | None = None
            turn1_died = False
            parse_fail = False
            subtask_killed_count = 0
            revised_best_guess_downward = False
            feasibility_failures = 0
            stop_reason = "unknown"
            error_message: str | None = None

            try:
                plan_response = _call_model(llm, format_turn1_prompt(problems), PLAN_TURN_BUDGET_S)
            except Exception as exc:
                plan_response = {
                    "text": "",
                    "wall_seconds": time.monotonic() - run_start,
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "thinking_tokens": None,
                    "timed_out": False,
                }
                error_message = f"{type(exc).__name__}: {exc}"
                turn1_died = True
                stop_reason = "plan_error"

            plan_parsed = None if plan_response["timed_out"] or error_message else _parse_plan_turn(plan_response["text"], problem_ids)
            plan_turn = {
                "turn_index": 1,
                "phase": "plan",
                "raw_text": plan_response["text"],
                "wall_seconds": plan_response["wall_seconds"],
                "input_tokens": plan_response["input_tokens"],
                "output_tokens": plan_response["output_tokens"],
                "total_tokens": plan_response["total_tokens"],
                "thinking_tokens": plan_response["thinking_tokens"],
                "timed_out": plan_response["timed_out"],
                "parse_ok": plan_parsed is not None,
                "parsed": plan_parsed,
            }
            turns.append(plan_turn)

            if stop_reason == "unknown":
                if plan_response["timed_out"] or plan_parsed is None:
                    turn1_died = True
                    if not plan_response["timed_out"]:
                        parse_fail = True
                    stop_reason = "turn1_died" if plan_response["timed_out"] else "plan_parse_fail"
                else:
                    initial_plan = plan_parsed["plan"]
                    plan_state = plan_parsed["plan"]
                    next_sub_id = plan_parsed["next_sub_id"]

            turn_number = 2
            while (
                isinstance(next_sub_id, int)
                and stop_reason == "unknown"
                and (time.monotonic() - run_start) < TOTAL_BUDGET_S
                and turn_number <= MAX_EXEC_TURNS + 1
            ):
                plan_lookup = {item["id"]: item for item in plan_state}
                next_sub = plan_lookup.get(next_sub_id)
                if next_sub is None or next_sub.get("status") != "pending":
                    parse_fail = True
                    stop_reason = "invalid_next_sub"
                    break

                elapsed_s = time.monotonic() - run_start
                remaining_s = max(1, int(TOTAL_BUDGET_S - elapsed_s))
                next_sub = dict(next_sub)
                next_sub["budget_s"] = max(1, min(int(next_sub["budget_s"]), MAX_SUBTASK_BUDGET_S, remaining_s))

                try:
                    exec_response = _call_model(
                        llm,
                        format_exec_prompt(
                            turn_number=turn_number,
                            previous_turn=turns[-1],
                            elapsed_s=elapsed_s,
                            problems_by_id=problems_by_id,
                            current_answers=current_answers,
                            current_scores=current_scores,
                            plan_state=plan_state,
                            next_sub=next_sub,
                        ),
                        next_sub["budget_s"],
                    )
                except Exception as exc:
                    exec_response = {
                        "text": "",
                        "wall_seconds": time.monotonic() - run_start,
                        "input_tokens": None,
                        "output_tokens": None,
                        "total_tokens": None,
                        "thinking_tokens": None,
                        "timed_out": False,
                    }
                    error_message = f"{type(exc).__name__}: {exc}"
                    stop_reason = "subtask_error"

                if stop_reason != "unknown":
                    break

                exec_parsed = None
                if not exec_response["timed_out"]:
                    exec_parsed = _parse_exec_turn(
                        exec_response["text"],
                        prior_plan=plan_state,
                        expected_problem_id=next_sub["problem"],
                        problem_ids=problem_ids,
                    )

                exec_turn: dict[str, Any] = {
                    "turn_index": turn_number,
                    "phase": "exec",
                    "next_sub_in": next_sub,
                    "raw_text": exec_response["text"],
                    "wall_seconds": exec_response["wall_seconds"],
                    "input_tokens": exec_response["input_tokens"],
                    "output_tokens": exec_response["output_tokens"],
                    "total_tokens": exec_response["total_tokens"],
                    "thinking_tokens": exec_response["thinking_tokens"],
                    "timed_out": exec_response["timed_out"],
                    "parse_ok": exec_parsed is not None,
                    "parsed": exec_parsed,
                }

                if exec_response["timed_out"]:
                    turns.append(exec_turn)
                    subtask_killed_count += 1
                    stop_reason = "subtask_timeout"
                    break

                if exec_parsed is None:
                    turns.append(exec_turn)
                    parse_fail = True
                    stop_reason = "subtask_parse_fail"
                    break

                if exec_parsed["subtask_id"] != next_sub["id"]:
                    # Model labelled its response SUB_N_RESULT with the wrong counter
                    # (happens when the harness skips to a non-sequential plan sub_id).
                    # The semantic content is still valid: problem_id and forecast are
                    # already validated in _parse_exec_turn. Override the declared
                    # subtask_id so downstream accounting stays correct.
                    exec_parsed = dict(exec_parsed)
                    exec_parsed["subtask_id"] = next_sub["id"]

                touched_problem = problems_by_id[next_sub["problem"]]
                verification = touched_problem.verify_answer(exec_parsed["candidate"]["answer"])
                exec_turn["verification"] = {
                    "feasible": verification.feasible,
                    "score": verification.score,
                    "failure_reason": verification.failure_reason,
                    "details": verification.details,
                }

                if verification.feasible and verification.score is not None:
                    previous_score = current_scores[touched_problem.problem_id]
                    if verification.score <= previous_score + 1e-9 and verification.normalized_answer is not None:
                        current_answers[touched_problem.problem_id] = _clone_jsonish(verification.normalized_answer)
                        current_scores[touched_problem.problem_id] = verification.score
                        current_sources[touched_problem.problem_id] = "model"
                    elif verification.score > previous_score + 1e-9:
                        revised_best_guess_downward = True
                else:
                    feasibility_failures += 1

                realized_score = current_scores[touched_problem.problem_id]
                realized_bucket = touched_problem.realized_bucket(realized_score)
                forecast_history[touched_problem.problem_id].append(
                    {
                        "turn_index": turn_number,
                        "forecast": exec_parsed["forecast"],
                        "realized_score": realized_score,
                    }
                )
                per_problem_turns[touched_problem.problem_id].append(turn_number)

                merged_plan = _merge_revised_plan(
                    exec_parsed["revised_plan"],
                    prior_plan=plan_state,
                    executed_item=next_sub,
                    realized_bucket=realized_bucket,
                )
                delta = _plan_delta(plan_state, merged_plan)
                exec_turn["plan_delta"] = delta
                exec_turn["plan_state_out"] = merged_plan
                turns.append(exec_turn)
                plan_evolution.append(
                    {
                        "turn_index": turn_number,
                        "problem": touched_problem.problem_id,
                        "executed_sub_id": next_sub["id"],
                        "plan_size": delta["plan_size"],
                        "additions": delta["additions"],
                        "revisions": delta["revisions"],
                        "status_flips": delta["status_flips"],
                        "next_sub_id_out": exec_parsed["next_sub_id"],
                    }
                )
                plan_state = merged_plan

                if exec_parsed["next_sub_id"] in STOP_TOKENS:
                    stop_reason = str(exec_parsed["next_sub_id"])
                    break

                next_sub_id = exec_parsed["next_sub_id"]
                turn_number += 1

            if stop_reason == "unknown":
                if turn_number > MAX_EXEC_TURNS + 1 and isinstance(next_sub_id, int):
                    stop_reason = "max_exec_turns"
                else:
                    stop_reason = "stop_budget"

            total_wall_seconds = time.monotonic() - run_start
            per_problem_results: dict[str, dict[str, Any]] = {}
            brier_by_problem: dict[str, dict[str, float | None]] = {}
            latest_forecast_by_problem: dict[str, dict[str, float] | None] = {}
            realized_bucket_by_problem: dict[str, str] = {}
            final_value_sum = 0.0
            for problem in problems:
                final_score = current_scores[problem.problem_id]
                headroom_fraction = problem.headroom_fraction(final_score)
                value_captured = problem.value_captured(final_score)
                final_value_sum += value_captured
                entries = forecast_history[problem.problem_id]
                latest_forecast = entries[-1]["forecast"] if entries else None
                realized_bucket = problem.realized_bucket(final_score)
                latest_forecast_by_problem[problem.problem_id] = latest_forecast
                realized_bucket_by_problem[problem.problem_id] = realized_bucket
                per_problem_results[problem.problem_id] = {
                    "label": problem.label,
                    "kind": problem.kind,
                    "value_cap": problem.value_cap,
                    "metric_name": problem.metric_name,
                    "baseline_score": problem.baseline_score,
                    "gold_score": problem.gold_score,
                    "final_score": final_score,
                    "final_gap_pct": problem.gap_pct_for_score(final_score),
                    "headroom_fraction_captured": headroom_fraction,
                    "value_captured": value_captured,
                    "subtasks_executed": len(per_problem_turns[problem.problem_id]),
                    "final_answer": current_answers[problem.problem_id],
                    "final_source": current_sources[problem.problem_id],
                    "final_thresholded_forecast": latest_forecast,
                    "realized_bucket": realized_bucket,
                }
                brier_by_problem[problem.problem_id] = {
                    key: (
                        sum(
                            (
                                entry["forecast"][key]
                                - forecast_event_map(problem, entry["realized_score"])[key]
                            )
                            ** 2
                            for entry in entries
                        )
                        / len(entries)
                    )
                    if entries
                    else None
                    for key in FORECAST_KEYS
                }

            time_cost = COST_PER_SECOND * total_wall_seconds
            net_score = final_value_sum - time_cost
            initial_allocation = {
                problem.problem_id: sum(item["budget_s"] for item in (initial_plan or []) if item["problem"] == problem.problem_id)
                for problem in problems
            }
            abandoned_problems = sorted(
                problem.problem_id
                for problem in problems
                if initial_allocation[problem.problem_id] > 0 and not per_problem_turns[problem.problem_id]
            )

            declared_axis_p1 = _extract_declared_axis(plan_state or initial_plan)
            return {
                "model": model_name,
                "seed": problems[0].instance.seed if problems else None,
                "cost_per_second": COST_PER_SECOND,
                "total_wall_budget_s": TOTAL_BUDGET_S,
                "max_exec_turns": MAX_EXEC_TURNS,
                "problems": per_problem_results,
                "preflight": {
                    problem.problem_id: {
                        "baseline_score": problem.baseline_score,
                        "gold_score": problem.gold_score,
                        "gap_pct": problem.baseline_gap_pct,
                        "gold_method": problem.gold_method,
                        "gold_wall_seconds": problem.gold_wall_seconds,
                        "generation_attempts": problem.generation_attempts,
                        "regenerated": problem.generation_attempts > 1,
                    }
                    for problem in problems
                },
                "turns": turns,
                "initial_plan": initial_plan,
                "final_plan": plan_state,
                "plan_evolution": plan_evolution,
                "plan_trace": plan_evolution,
                "initial_allocation": initial_allocation,
                "forecast_history": forecast_history,
                "thresholded_forecast_history_by_problem": forecast_history,
                "latest_forecast_by_problem": latest_forecast_by_problem,
                "thresholded_brier_by_problem": brier_by_problem,
                "forecast_brier_by_problem": brier_by_problem,
                "forecast_event_by_problem": {
                    problem.problem_id: forecast_event_map(problem, current_scores[problem.problem_id])
                    for problem in problems
                },
                "realized_bucket_by_problem": realized_bucket_by_problem,
                "per_problem_turns": per_problem_turns,
                "session_value_sum": final_value_sum,
                "session_time_cost": time_cost,
                "session_net_score": net_score,
                "economic_net_score": net_score,
                "turn_count": len(turns),
                "turn1_wall_seconds": turns[0]["wall_seconds"],
                "stop_reason": stop_reason,
                "turn1_died": turn1_died,
                "parse_fail": parse_fail,
                "subtask_killed_count": subtask_killed_count,
                "revised_best_guess_downward": revised_best_guess_downward,
                "feasibility_failure_count": feasibility_failures,
                "abandoned_problems": abandoned_problems,
                "total_wall_seconds": total_wall_seconds,
                "wall_s": total_wall_seconds,
                "declared_axis_p1": declared_axis_p1,
                "error": error_message,
            }


        @kbench.task(
            name=f"portfolio_spike_seed{SEED}",
            description=(
                f"Portfolio spike metagame pilot for seed {SEED}. "
                "Four problems, plan-as-state, thresholded forecasts, 30-minute total budget."
            ),
        )
        def portfolio_spike(llm):
            problems = _portfolio_for_seed(SEED)
            row = run_protocol(llm, problems, os.environ.get("LLM_DEFAULT", "unknown"))
            kbench.assertions.assert_true(
                True,
                expectation=(
                    f"PORTFOLIO seed={row['seed']} model={row['model']} stop_reason={row['stop_reason']} "
                    f"net={row['session_net_score']:.2f} turns={row['turn_count']} "
                    f"axis_p1={row['declared_axis_p1']} error={row['error']}"
                ),
            )
            return row
        """
    )
)


def build_task_source() -> str:
    portfolio_json = json.dumps(_build_embedded_portfolio(), indent=2, sort_keys=True)
    module_bundle_json = json.dumps(_bundle_modules(), indent=2, sort_keys=True)
    return TASK_TEMPLATE.substitute(
        SYSTEM_PROMPT_JSON=json.dumps(CANONICAL_SYSTEM_PROMPT),
        MODULE_BUNDLE_JSON=module_bundle_json,
        PORTFOLIO_JSON=portfolio_json,
    )


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_task_source(), encoding="utf-8")
    print(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
