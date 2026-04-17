from __future__ import annotations

import subprocess

from harness.protocol import PLAN_TURN_BUDGET_S, SUBTASK_BUDGET_S

_TIMEOUT_CAP_S = max(PLAN_TURN_BUDGET_S, SUBTASK_BUDGET_S) + 30
MODEL_MAX_TOKENS_FLAGS: dict[str, list[str]] = {
    "claude-sonnet-4.6": ["--option", "max_tokens", "40000"],
    "gemini-flash-latest": ["--option", "max_output_tokens", "40000"],
    "gpt-5.4-mini": [],
    "claude-opus-4.6": ["--option", "max_tokens", "40000"],
    "gemini-3-pro-preview": ["--option", "max_output_tokens", "40000", "--option", "thinking_level", "low"],
    "gpt-5.4": [],
}
MODELS_WITHOUT_TEMPERATURE: set[str] = {"gpt-5.4"}


class LocalLLM:
    def __init__(self, model: str, system_prompt: str, *, timeout_s: int = _TIMEOUT_CAP_S):
        self.model = model
        self.system_prompt = system_prompt
        self.timeout_s = timeout_s

    def prompt(self, text: str, *, temperature: float = 0.0) -> str:
        cmd = [
            "llm",
            "-m",
            self.model,
            "-s",
            self.system_prompt,
        ]
        if self.model not in MODELS_WITHOUT_TEMPERATURE:
            cmd.extend(["--option", "temperature", format(float(temperature), "g")])
        cmd.extend(MODEL_MAX_TOKENS_FLAGS.get(self.model, []))
        cmd.append(text)
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("llm CLI not found in PATH") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"llm CLI timed out after {self.timeout_s}s") from exc

        if completed.returncode != 0:
            message = completed.stderr.strip() or completed.stdout.strip() or "llm CLI failed"
            raise RuntimeError(message)

        return completed.stdout.strip()
