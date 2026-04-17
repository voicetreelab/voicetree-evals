#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse, urlunparse

ROOT = Path(__file__).resolve().parents[2]
KAGGLE_SUBMISSION_ROOT = ROOT / "kaggle_submission"
KAGGLE_DIR = KAGGLE_SUBMISSION_ROOT / "kaggle"
QUESTIONS_PATH = KAGGLE_SUBMISSION_ROOT / "questions.jsonl"
TASK_PATH = KAGGLE_DIR / "task.py"
OUTPUT_ROOT = KAGGLE_DIR / "output"
RESULTS_ROOT = KAGGLE_SUBMISSION_ROOT / "results" / "runs" / "kaggle_production"
BRIDGE_DIR = ROOT / "kaggle_experiments" / "option_a_bridge"

if str(BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(BRIDGE_DIR))

from kernel_bridge import (  # noqa: E402
    ExecutionTimeoutError,
    JupyterKernelBridge,
    KernelBridgeError,
    KernelBusyError,
    TokenRejectedError,
)

RESULT_START = "__KAGGLE_PROD_RESULT_START__"
RESULT_END = "__KAGGLE_PROD_RESULT_END__"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Kaggle production bridge against a live Jupyter proxy.")
    parser.add_argument(
        "command",
        choices=("probe", "run"),
        help="`probe` inspects the live Kaggle runtime; `run` executes an evaluation.",
    )
    parser.add_argument(
        "--proxy-url",
        required=True,
        help="Full Kaggle Jupyter proxy URL including the `?token=...` query parameter.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Requested Kaggle model slug override. If omitted, uses the runtime default.",
    )
    parser.add_argument(
        "--ids",
        nargs="*",
        default=None,
        help="Optional row ids to run. Defaults to all rows in questions.jsonl.",
    )
    parser.add_argument(
        "--label",
        default=None,
        help="Optional local output label. Defaults to a UTC timestamped label.",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=14400.0,
        help="Bridge timeout in seconds for the remote execution. Default: 14400s (4h).",
    )
    return parser.parse_args()


def parse_proxy_url(proxy_url: str) -> tuple[str, str]:
    parsed = urlparse(proxy_url)
    token = parse_qs(parsed.query).get("token", [None])[0]
    if not token:
        raise ValueError("Proxy URL is missing a `token` query parameter.")
    base_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))
    return base_url, token


def slugify(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_") or "default"


def utc_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def load_rows(selected_ids: list[str] | None) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in QUESTIONS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not selected_ids:
        return rows
    wanted = set(selected_ids)
    filtered = [row for row in rows if row["id"] in wanted]
    found = {row["id"] for row in filtered}
    missing = sorted(wanted - found)
    if missing:
        raise ValueError(f"Unknown row ids: {missing}")
    return filtered


def build_probe_code() -> str:
    return f"""
import inspect
import json
import pathlib
import traceback

RESULT_START = {RESULT_START!r}
RESULT_END = {RESULT_END!r}
payload = {{}}

try:
    import kaggle_benchmarks as kbench
    from kaggle_benchmarks import kaggle as _kbk

    registry = getattr(getattr(kbench, "client", None), "registry", {{}})
    payload.update({{
        "status": "ok",
        "cwd": str(pathlib.Path.cwd()),
        "is_configured": bool(_kbk.is_configured()),
        "llm_type": type(kbench.llm).__name__,
        "llm_model": getattr(kbench.llm, "model", None),
        "llm_name": getattr(kbench.llm, "name", None),
        "llm_attrs": sorted(name for name in dir(kbench.llm) if not name.startswith("_")),
        "registry_size": len(registry),
        "registry_names": sorted(getattr(task, "name", "<unnamed>") for task in registry.values()),
    }})
except Exception as exc:
    payload["status"] = "error"
    payload["wrapper_error"] = {{
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": traceback.format_exc(),
    }}

print(RESULT_START)
print(json.dumps(payload))
print(RESULT_END)
""".strip()


def build_eval_code(*, task_source: str, rows: list[dict[str, Any]], task_name: str, requested_model: str | None) -> str:
    encoded_task = base64.b64encode(task_source.encode("utf-8")).decode("ascii")
    encoded_rows = base64.b64encode(json.dumps(rows, separators=(",", ":"), sort_keys=True).encode("utf-8")).decode("ascii")

    model_swap = ""
    if requested_model:
        model_swap = f"""
import kaggle_benchmarks as _kbench_swap
_kbench_swap.llm.model = {requested_model!r}
_kbench_swap.llm.name = {requested_model!r}
del _kbench_swap
""".strip()

    return f"""
{model_swap}

import base64
import inspect
import json
import pathlib
import re
import sys
import traceback
import types

import pandas as pd
import kaggle_benchmarks as kbench

RESULT_START = {RESULT_START!r}
RESULT_END = {RESULT_END!r}
TASK_SOURCE = base64.b64decode({encoded_task!r}).decode("utf-8")
ROWS = json.loads(base64.b64decode({encoded_rows!r}).decode("utf-8"))
TASK_PATH = {str(TASK_PATH)!r}
MODULE_NAME = "__voicetree_kaggle_prod_task__"
TASK_NAME = {task_name!r}

detail_rows = []
payload = {{
    "status": "ok",
    "task_name": TASK_NAME,
    "requested_model": {requested_model!r},
    "effective_model": getattr(kbench.llm, "model", None),
    "effective_name": getattr(kbench.llm, "name", None),
}}


def json_safe(value):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {{str(key): json_safe(item) for key, item in value.items()}}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return repr(value)


def snapshot(pattern):
    output = {{}}
    for path in pathlib.Path(".").glob(pattern):
        if path.is_file():
            output[path.name] = path.read_text()
    return output


def parse_param_id(filename):
    match = re.search(r"run_param_id_(\\d+)_", filename)
    if not match:
        return None
    return int(match.group(1))


def select_submission_source(result, *, instance, cls, components):
    if result.get("cf_parsed"):
        return "cf_parsed", result["cf_parsed"].get("best_guess")
    if result.get("parsed"):
        return "parsed", result["parsed"].get("best_guess")
    return "baseline", module._initial_best_guess(instance, cls=cls, components=components)


def evaluate_final_submission(result, *, instance, cls, components):
    submission_source, submission = select_submission_source(
        result,
        instance=instance,
        cls=cls,
        components=components,
    )
    evaluation = module._evaluate_submission(
        cls=cls,
        instance=instance,
        submission=submission,
        components=components,
    )
    return submission_source, evaluation


def infer_feasible(evaluation):
    if evaluation.get("mode") == "portfolio":
        return bool(evaluation.get("components")) and all(
            bool(component.get("feasible")) for component in evaluation["components"]
        )
    return bool(evaluation.get("feasible"))


def infer_parse_path(result):
    parse_events = result.get("parse_events") or []
    modes = [str(event.get("mode")) for event in parse_events]
    if any(mode == "judge_rescue" for mode in modes):
        return "judge_rescue"
    if any(mode == "partial_rescue" for mode in modes):
        return "partial_rescue"
    if any(mode == "strict_parse_failed" for mode in modes):
        return "strict_parse_failed"
    if result.get("cf_parsed"):
        return "strict_protocol_cf"
    if result.get("parsed"):
        return "strict_protocol"
    return "baseline_only"


before_task_files = snapshot("*.task.json")
before_run_files = snapshot("*.run.json")

try:
    module = types.ModuleType(MODULE_NAME)
    module.__file__ = TASK_PATH
    module.__dict__["__name__"] = MODULE_NAME
    sys.modules[MODULE_NAME] = module
    exec(compile(TASK_SOURCE, TASK_PATH, "exec"), module.__dict__, module.__dict__)

    @kbench.task(name=TASK_NAME)
    def detailed_run(
        llm,
        id,
        class_,
        difficulty,
        seed,
        instance,
        gold_objective,
        baseline_objective,
        value_cap,
        wall_budget_s=1800,
        components=None,
    ):
        del wall_budget_s
        inst = module._coerce_json(instance, default=None)
        if not isinstance(inst, dict):
            raise TypeError("instance must be a dict or JSON object string")
        normalized_components = module._normalize_components(components)

        row = module.run_instance(
            llm=llm,
            instance=inst,
            cls=str(class_),
            difficulty=str(difficulty),
            seed=int(seed),
            gold_objective=float(gold_objective),
            baseline_objective=float(baseline_objective),
            value_cap=float(value_cap),
            components=normalized_components,
        )
        final_submission_source, final_evaluation = evaluate_final_submission(
            row,
            instance=inst,
            cls=str(class_),
            components=normalized_components,
        )
        gap_pct = final_evaluation.get("gap_pct")
        if gap_pct is None:
            gap_pct = final_evaluation.get("details", {{}}).get("gap_pct")
        detail = {{
            "id": str(id),
            "class": str(class_),
            "difficulty": str(difficulty),
            "seed": int(seed),
            "score": float(row["score"]),
            "score_at_stop": float(row["score_at_stop"]),
            "score_after_cf": float(row["score_after_cf"]),
            "cf_delta": float(row["cf_delta"]),
            "stop_reason": row["stop_reason"],
            "wall_s": float(row["wall_s"]),
            "n_exec_turns": int(row["n_exec_turns"]),
            "error": row["error"],
            "parsed": row["parsed"],
            "cf_parsed": row["cf_parsed"],
            "transcript": row["transcript"],
            "parse_path": infer_parse_path(row),
            "parse_events": row.get("parse_events"),
            "feasible": infer_feasible(final_evaluation),
            "final_submission_source": final_submission_source,
            "final_evaluation": final_evaluation,
            "gap_pct": gap_pct,
        }}
        detail_rows.append(detail)
        return float(row["score"])

    dataframe = pd.DataFrame(ROWS).rename(columns={{"class": "class_"}}).reset_index(drop=True)
    evaluate_signature = str(inspect.signature(detailed_run.evaluate))
    payload["evaluate_signature"] = evaluate_signature
    payload["row_count"] = len(dataframe)
    payload["row_ids"] = [str(row["id"]) for row in ROWS]

    eval_result = detailed_run.evaluate(llm=[kbench.llm], evaluation_data=dataframe)
    payload["eval_result"] = json_safe(eval_result)
    payload["detail_rows"] = detail_rows
    payload["eval_summary"] = [
        {{
            "id": row["id"],
            "class": row["class"],
            "difficulty": row["difficulty"],
            "seed": row["seed"],
            "result": row["score"],
        }}
        for row in detail_rows
    ]
    payload["missing_ids"] = sorted(set(payload["row_ids"]) - {{row["id"] for row in detail_rows}})
except Exception as exc:
    payload["status"] = "error"
    payload["detail_rows"] = detail_rows
    payload["wrapper_error"] = {{
        "type": type(exc).__name__,
        "message": str(exc),
        "traceback": traceback.format_exc(),
    }}
finally:
    after_task_files = snapshot("*.task.json")
    after_run_files = snapshot("*.run.json")
    changed_task_files = {{
        name: contents
        for name, contents in after_task_files.items()
        if before_task_files.get(name) != contents
    }}
    changed_run_files = {{
        name: contents
        for name, contents in after_run_files.items()
        if before_run_files.get(name) != contents
    }}
    payload["task_files"] = changed_task_files
    payload["run_files"] = changed_run_files

    rows_by_param_id = {{
        index: row
        for index, row in enumerate(ROWS)
    }}
    run_files_by_row = {{}}
    for name, contents in changed_run_files.items():
        param_id = parse_param_id(name)
        row = rows_by_param_id.get(param_id)
        if row is None:
            continue
        run_files_by_row[row["id"]] = {{
            "filename": name,
            "contents": contents,
            "param_id": param_id,
        }}
    payload["run_files_by_row"] = run_files_by_row

    print(RESULT_START)
    print(json.dumps(payload))
    print(RESULT_END)
""".strip()


def extract_payload(stdout: str) -> dict[str, Any]:
    start = stdout.find(RESULT_START)
    end = stdout.find(RESULT_END)
    if start == -1 or end == -1 or end <= start:
        raise RuntimeError("Bridge output did not contain the expected payload markers.")
    body = stdout[start + len(RESULT_START) : end].strip()
    return json.loads(body)


def write_text(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def run_remote(bridge: JupyterKernelBridge, code: str, *, timeout_s: float) -> tuple[dict[str, Any], str, str]:
    execution = bridge.run(code, timeout_seconds=timeout_s)
    payload = extract_payload(execution.stdout)
    return payload, execution.stdout, execution.stderr


def save_payload_bundle(
    *,
    label: str,
    payload: dict[str, Any],
    stdout: str,
    stderr: str,
) -> Path:
    out_dir = OUTPUT_ROOT / label
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "payload.json", payload)
    write_text(out_dir / "bridge_stdout.txt", stdout)
    write_text(out_dir / "bridge_stderr.txt", stderr)
    if payload.get("eval_summary") is not None:
        write_json(out_dir / "eval_summary.json", payload["eval_summary"])
    if payload.get("detail_rows") is not None:
        write_json(out_dir / "detail_rows.json", payload["detail_rows"])
    return out_dir


def persist_model_results(payload: dict[str, Any], *, requested_model: str | None) -> Path:
    effective_model = str(payload.get("effective_model") or payload.get("effective_name") or requested_model or "runtime-default")
    model_dir = RESULTS_ROOT / slugify(effective_model)
    model_dir.mkdir(parents=True, exist_ok=True)

    detail_rows = {
        row["id"]: row
        for row in payload.get("detail_rows") or []
    }
    run_files_by_row = payload.get("run_files_by_row") or {}

    for row_id, detail in detail_rows.items():
        combined = {
            "requested_model": requested_model,
            "effective_model": effective_model,
            "detail_row": detail,
        }
        run_file_meta = run_files_by_row.get(row_id)
        if run_file_meta:
            combined["run_file"] = {
                "filename": run_file_meta["filename"],
                "param_id": run_file_meta["param_id"],
            }
            try:
                run_json = json.loads(run_file_meta["contents"])
            except json.JSONDecodeError:
                run_json = run_file_meta["contents"]
            combined["run_json"] = run_json
            write_json(model_dir / f"{row_id}.run.json", run_json)
        write_json(model_dir / f"{row_id}.json", combined)

    return model_dir


def main() -> int:
    args = parse_args()
    base_url, token = parse_proxy_url(args.proxy_url)
    bridge = JupyterKernelBridge(base_url=base_url, token=token, idle_wait_seconds=60.0)

    label = args.label
    if not label:
        if args.command == "probe":
            label = f"kaggle-production-probe-{utc_stamp()}"
        else:
            model_label = slugify(args.model or "runtime-default")
            scope = "smoke" if args.ids else "full"
            label = f"kaggle-production-{scope}-{model_label}-{utc_stamp()}"

    try:
        if args.command == "probe":
            payload, stdout, stderr = run_remote(bridge, build_probe_code(), timeout_s=args.timeout_s)
            out_dir = save_payload_bundle(label=label, payload=payload, stdout=stdout, stderr=stderr)
            print(f"[probe] status={payload.get('status')} out_dir={out_dir}")
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0 if payload.get("status") == "ok" else 1

        rows = load_rows(args.ids)
        task_source = TASK_PATH.read_text(encoding="utf-8")
        task_name = f"meta_hch_prod_{slugify(args.model or 'runtime-default')}_{utc_stamp().lower()}"
        remote_code = build_eval_code(
            task_source=task_source,
            rows=rows,
            task_name=task_name,
            requested_model=args.model,
        )
        payload, stdout, stderr = run_remote(bridge, remote_code, timeout_s=args.timeout_s)
        out_dir = save_payload_bundle(label=label, payload=payload, stdout=stdout, stderr=stderr)
        model_dir = persist_model_results(payload, requested_model=args.model)

        print(
            "[run] "
            f"status={payload.get('status')} "
            f"requested_model={args.model or 'runtime-default'} "
            f"effective_model={payload.get('effective_model')} "
            f"rows={payload.get('row_count')} "
            f"detail_rows={len(payload.get('detail_rows') or [])} "
            f"missing_ids={len(payload.get('missing_ids') or [])} "
            f"out_dir={out_dir} "
            f"model_dir={model_dir}"
        )
        if payload.get("wrapper_error"):
            print(json.dumps(payload["wrapper_error"], indent=2, sort_keys=True))
        return 0 if payload.get("status") == "ok" else 1
    except TokenRejectedError as exc:
        print(f"[bridge] token rejected: {exc}", file=sys.stderr)
        return 3
    except KernelBusyError as exc:
        print(f"[bridge] kernel busy: {exc}", file=sys.stderr)
        return 4
    except ExecutionTimeoutError as exc:
        print(f"[bridge] execution timeout: {exc}", file=sys.stderr)
        return 5
    except KernelBridgeError as exc:
        print(f"[bridge] bridge error: {exc}", file=sys.stderr)
        return 6
    except Exception as exc:
        print(f"[bridge] unexpected error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
