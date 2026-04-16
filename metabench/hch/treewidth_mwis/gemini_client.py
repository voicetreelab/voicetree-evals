from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

MODULE_DIR = Path(__file__).resolve().parent
ENV_PATH = MODULE_DIR / ".env"
FALLBACK_ENV_PATH = MODULE_DIR.parent / "metagame" / ".env"
DEFAULT_MODELS = [
    "models/gemini-3-pro-preview",
]


def load_local_env() -> None:
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)
    elif FALLBACK_ENV_PATH.exists():
        load_dotenv(FALLBACK_ENV_PATH)


def get_api_key() -> str:
    load_local_env()
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            f"Missing GOOGLE_API_KEY or GEMINI_API_KEY. Expected {ENV_PATH} or {FALLBACK_ENV_PATH}."
        )
    return api_key


class GeminiChatSession:
    def __init__(
        self,
        model_name: str,
        system_instruction: str,
        *,
        temperature: float = 0.0,
        thinking_budget: int | None = None,
    ) -> None:
        self.api_key = get_api_key()
        self.model_name = model_name
        self.temperature = temperature
        self.history: list[Any] = []

        config_kwargs: dict[str, Any] = {
            "system_instruction": system_instruction,
            "temperature": temperature,
        }
        if thinking_budget is not None:
            config_kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_budget=thinking_budget
            )
        self.base_config = types.GenerateContentConfig(**config_kwargs)

    def send_message(self, message: str, timeout_s: int | float | None = None) -> dict[str, Any]:
        http_options = None
        if timeout_s is not None:
            http_options = types.HttpOptions.model_construct(
                timeout=int((float(timeout_s) + 5.0) * 1000)
            )

        client = genai.Client(api_key=self.api_key, http_options=http_options)
        chat = client.chats.create(
            model=self.model_name,
            config=self.base_config,
            history=self.history,
        )

        start = time.monotonic()
        response = chat.send_message(message)
        wall_seconds = time.monotonic() - start
        self.history = chat.get_history()

        usage = getattr(response, "usage_metadata", None)
        return {
            "text": (response.text or "").strip(),
            "wall_seconds": wall_seconds,
            "input_tokens": getattr(usage, "prompt_token_count", None),
            "output_tokens": getattr(usage, "candidates_token_count", None),
            "total_tokens": getattr(usage, "total_token_count", None),
            "thinking_tokens": getattr(usage, "thoughts_token_count", None),
        }


def list_live_models() -> list[str]:
    client = genai.Client(api_key=get_api_key())
    return [getattr(model, "name", "") for model in client.models.list()]
