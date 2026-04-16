from __future__ import annotations

from typing import Iterable

from portfolio_problem import PreparedProblem

COST_PER_SECOND = 0.05


def build_system_prompt(problems: Iterable[PreparedProblem]) -> str:
    lines = [
        "You are optimizing a four-problem portfolio across multiple turns.",
        "Your objective is economic, not symbolic: improve verified answers toward gold while minimizing wall-clock time.",
        (
            "Session objective = sum over problems of value_cap * captured_headroom"
            f" - {COST_PER_SECOND:.2f} * wall_seconds."
        ),
        "Do not call tools.",
        "Do not write solver code, Python, or pseudocode.",
        "Work only from the problem statements, prior conversation state, and your own reasoning.",
        "You may revise your plan freely across turns and shift effort when you learn something useful.",
        "When you update a problem, emit your full current best candidate answer on its own line using labels like P1_ANSWER: {...}.",
        "Free-form reasoning is allowed before or after those answer lines.",
        "At the end of each turn, if helpful, you may state your estimate of how much more value one additional turn would add; this is a forecast the harness measures.",
        "",
        "Portfolio summary:",
    ]

    for problem in problems:
        lines.append(
            (
                f"- {problem.problem_id} | {problem.label} | value_cap={problem.value_cap} | "
                f"baseline_{problem.metric_name}={_fmt_metric(problem.baseline_score)} | "
                f"gold_{problem.metric_name}={_fmt_metric(problem.gold_score)}"
            )
        )

    for problem in problems:
        lines.extend(
            [
                "",
                f"=== {problem.problem_id}: {problem.label} ===",
                problem.problem_statement,
                f"Answer contract hint: {problem.answer_contract}",
            ]
        )

    return "\n".join(lines)


def _fmt_metric(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:.3f}"
