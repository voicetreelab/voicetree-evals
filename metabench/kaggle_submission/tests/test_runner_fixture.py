from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.runner import run_instance


class ReplayLLM:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.prompts: list[str] = []

    def prompt(self, message: str, temperature: float = 0) -> str:
        del temperature
        self.prompts.append(message)
        if not self._responses:
            raise AssertionError("ReplayLLM exhausted scripted responses")
        return self._responses.pop(0)


def test_runner_fixture_decision_stop_triggers_counterfactual() -> None:
    fixture_path = ROOT / "tests" / "fixtures" / "cjs_smoke.json"
    fixture = json.loads(fixture_path.read_text())
    instance = fixture["instance"]
    gold_submission = fixture["gold_submission"]
    gold_json = json.dumps(gold_submission, indent=2, sort_keys=True)

    llm = ReplayLLM(
        [
            "\n".join(
                [
                    "PLAN_STATE: Start from the baseline schedule, then repair machine conflicts only if they buy real makespan.",
                    'NEXT_SUB: {"id": 1, "desc": "Emit the best complete schedule you can verify mentally.", "p_solve": 0.82, "time_budget_s": 600}',
                ]
            ),
            "\n".join(
                [
                    "SUB_1: I verified that the gold schedule satisfies the contract, so I will emit it directly as my current best artifact.",
                    f"BEST_GUESS: {gold_json}",
                    "UPDATED_PLAN_STATE: Keep the verified gold schedule unless a forced extra turn reveals a better normalization.",
                    'QUALITY_FORECAST: {"p_gap_le_2": 0.92, "p_gap_le_5": 0.97, "p_gap_le_10": 0.99}',
                    'CONTINUE_FORECAST: {"p_improve": 0.08, "expected_delta_score": -0.4, "expected_gap_reduction": 0.0}',
                    "DECISION: stop",
                ]
            ),
            "\n".join(
                [
                    "SUB_2: Forced continuation confirms the same verified schedule remains optimal for this fixture.",
                    f"BEST_GUESS: {gold_json}",
                    "UPDATED_PLAN_STATE: No revision; the gold schedule is still the best artifact.",
                    'QUALITY_FORECAST: {"p_gap_le_2": 0.93, "p_gap_le_5": 0.98, "p_gap_le_10": 0.99}',
                    'CONTINUE_FORECAST: {"p_improve": 0.02, "expected_delta_score": -0.6, "expected_gap_reduction": 0.0}',
                ]
            ),
        ]
    )

    row = run_instance(
        llm=llm,
        instance=instance,
        cls="cjs",
        difficulty=str(instance["difficulty"]),
        seed=int(instance["seed"]),
        gold_objective=float(instance["gold_objective"]),
        baseline_objective=float(instance["baseline_objective"]),
        value_cap=100.0,
    )

    assert row["score_at_stop"] > 0
    assert row["score_after_cf"] > 0
    assert row["cf_delta"] == pytest.approx(row["score_after_cf"] - row["score_at_stop"])
    assert row["stop_reason"] == "decision_stop"
    assert row["n_exec_turns"] == 1
    assert len(row["transcript"]) == 3
    assert row["parsed"]["decision"] == "stop"
    assert "decision" not in row["cf_parsed"] or row["cf_parsed"]["decision"] is None
    assert row["error"] is None
    assert not llm._responses
