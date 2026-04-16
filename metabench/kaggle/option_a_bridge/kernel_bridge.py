from __future__ import annotations

import dataclasses
import json
import os
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse, urlunparse

import requests
import websocket
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class KernelBridgeError(RuntimeError):
    """Base error for Jupyter bridge failures."""


class TokenRejectedError(KernelBridgeError):
    """Raised when the Jupyter token is rejected or expired."""


class KernelBusyError(KernelBridgeError):
    """Raised when the target kernel does not become idle in time."""


class ExecutionTimeoutError(KernelBridgeError):
    """Raised when cell execution exceeds the configured timeout."""


@dataclasses.dataclass(slots=True)
class KernelTarget:
    kernel_id: str
    notebook_session_id: str | None
    notebook_path: str | None


@dataclasses.dataclass(slots=True)
class ExecutionError:
    ename: str
    evalue: str
    traceback: list[str]


@dataclasses.dataclass(slots=True)
class RichOutput:
    output_type: str
    data: dict[str, Any]
    metadata: dict[str, Any]
    execution_count: int | None = None


@dataclasses.dataclass(slots=True)
class ExecutionResult:
    kernel_id: str
    client_session_id: str
    msg_id: str
    status: str
    stdout: str = ""
    stderr: str = ""
    display_outputs: list[RichOutput] = dataclasses.field(default_factory=list)
    execute_results: list[RichOutput] = dataclasses.field(default_factory=list)
    error: ExecutionError | None = None
    execution_count: int | None = None
    reply_content: dict[str, Any] = dataclasses.field(default_factory=dict)


class JupyterKernelBridge:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        token: str | None = None,
        request_timeout_seconds: float = 10.0,
        idle_wait_seconds: float = 10.0,
    ) -> None:
        load_dotenv(PROJECT_ROOT / ".env", override=False)

        self.base_url = (base_url or os.environ.get("KAGGLE_JUPYTER_URL", "")).rstrip("/")
        self.token = token or os.environ.get("KAGGLE_JUPYTER_TOKEN", "")
        self.request_timeout_seconds = request_timeout_seconds
        self.idle_wait_seconds = idle_wait_seconds

        if not self.base_url or not self.token:
            raise KernelBridgeError(
                "KAGGLE_JUPYTER_URL and KAGGLE_JUPYTER_TOKEN must be set."
            )

        self._http = requests.Session()
        self._http.headers.update(
            {
                "Authorization": f"token {self.token}",
                "Accept": "application/json",
            }
        )

    def _api_url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _ws_url(self, kernel_id: str, client_session_id: str) -> str:
        parsed = urlparse(self.base_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        path = f"{parsed.path.rstrip('/')}/api/kernels/{kernel_id}/channels"
        query = urlencode({"session_id": client_session_id, "token": self.token})
        return urlunparse((scheme, parsed.netloc, path, "", query, ""))

    def _request(self, method: str, path: str) -> requests.Response:
        response = self._http.request(
            method=method,
            url=self._api_url(path),
            params={"token": self.token},
            timeout=self.request_timeout_seconds,
        )
        if response.status_code in {401, 403}:
            raise TokenRejectedError(
                "Kaggle Jupyter token was rejected. Refresh it from the live notebook UI."
            )
        response.raise_for_status()
        return response

    def list_sessions(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/sessions").json()

    def list_kernels(self) -> list[dict[str, Any]]:
        return self._request("GET", "/api/kernels").json()

    def resolve_kernel(self) -> KernelTarget:
        sessions = self.list_sessions()
        if sessions:
            session = sessions[0]
            kernel = session.get("kernel") or {}
            kernel_id = kernel.get("id")
            if kernel_id:
                return KernelTarget(
                    kernel_id=kernel_id,
                    notebook_session_id=session.get("id"),
                    notebook_path=session.get("path"),
                )

        kernels = self.list_kernels()
        if kernels:
            return KernelTarget(
                kernel_id=kernels[0]["id"],
                notebook_session_id=None,
                notebook_path=None,
            )

        raise KernelBridgeError("No running Kaggle kernels were found.")

    def _kernel_state(self, kernel_id: str) -> str:
        payload = self._request("GET", f"/api/kernels/{kernel_id}").json()
        return payload.get("execution_state", "")

    def wait_for_idle(self, kernel_id: str) -> None:
        deadline = time.monotonic() + self.idle_wait_seconds
        while time.monotonic() < deadline:
            if self._kernel_state(kernel_id) == "idle":
                return
            time.sleep(0.5)
        raise KernelBusyError(
            "Kaggle kernel stayed busy past the idle-wait window. Ask the user before forcing it."
        )

    def run(self, code: str, *, timeout_seconds: float = 30.0) -> ExecutionResult:
        target = self.resolve_kernel()
        self.wait_for_idle(target.kernel_id)

        client_session_id = uuid.uuid4().hex
        msg_id = uuid.uuid4().hex
        ws = None
        result = ExecutionResult(
            kernel_id=target.kernel_id,
            client_session_id=client_session_id,
            msg_id=msg_id,
            status="ok",
        )

        payload = {
            "header": {
                "msg_id": msg_id,
                "username": "voicetree",
                "session": client_session_id,
                "msg_type": "execute_request",
                "version": "5.3",
            },
            "parent_header": {},
            "metadata": {},
            "content": {
                "code": code,
                "silent": False,
                "store_history": False,
                "user_expressions": {},
                "allow_stdin": False,
                "stop_on_error": True,
            },
            "channel": "shell",
        }

        try:
            ws = websocket.create_connection(
                self._ws_url(target.kernel_id, client_session_id),
                timeout=10.0,  # increased from 1.0 — new JWT-in-path URL needs more time
                header=[f"Authorization: token {self.token}"],
            )
        except websocket.WebSocketBadStatusException as exc:
            if exc.status_code in {401, 403}:
                raise TokenRejectedError(
                    "Kaggle Jupyter token was rejected during WebSocket handshake. Refresh it from the live notebook UI."
                ) from exc
            raise KernelBridgeError(f"WebSocket handshake failed: {exc}") from exc
        except OSError as exc:
            raise KernelBridgeError(f"Failed to open Jupyter WebSocket: {exc}") from exc

        try:
            ws.send(json.dumps(payload))

            saw_idle = False
            saw_execute_reply = False
            deadline = time.monotonic() + timeout_seconds

            while time.monotonic() < deadline:
                remaining = max(0.1, min(1.0, deadline - time.monotonic()))
                ws.settimeout(remaining)
                try:
                    raw_message = ws.recv()
                except websocket.WebSocketTimeoutException:
                    continue

                if raw_message is None:
                    continue

                if isinstance(raw_message, bytes):
                    raw_message = raw_message.decode("utf-8")

                message = json.loads(raw_message)
                parent_msg_id = (message.get("parent_header") or {}).get("msg_id")
                if parent_msg_id != msg_id:
                    continue

                msg_type = (message.get("header") or {}).get("msg_type")
                content = message.get("content") or {}

                if msg_type == "status" and content.get("execution_state") == "idle":
                    saw_idle = True
                elif msg_type == "stream":
                    text = content.get("text", "")
                    if content.get("name") == "stderr":
                        result.stderr += text
                    else:
                        result.stdout += text
                elif msg_type == "display_data":
                    result.display_outputs.append(
                        RichOutput(
                            output_type="display_data",
                            data=content.get("data") or {},
                            metadata=content.get("metadata") or {},
                        )
                    )
                elif msg_type == "execute_result":
                    result.execution_count = content.get("execution_count")
                    result.execute_results.append(
                        RichOutput(
                            output_type="execute_result",
                            data=content.get("data") or {},
                            metadata=content.get("metadata") or {},
                            execution_count=content.get("execution_count"),
                        )
                    )
                elif msg_type == "error":
                    result.status = "error"
                    result.error = ExecutionError(
                        ename=content.get("ename", "Error"),
                        evalue=content.get("evalue", ""),
                        traceback=content.get("traceback") or [],
                    )
                elif msg_type == "execute_reply":
                    saw_execute_reply = True
                    result.reply_content = content
                    if content.get("status") == "error" and result.error is None:
                        result.status = "error"
                        result.error = ExecutionError(
                            ename=content.get("ename", "Error"),
                            evalue=content.get("evalue", ""),
                            traceback=content.get("traceback") or [],
                        )

                if saw_idle and saw_execute_reply:
                    return result

            raise ExecutionTimeoutError(
                f"Execution exceeded {timeout_seconds:.0f}s without returning to idle."
            )
        finally:
            if ws is not None:
                ws.close()


def run_on_kaggle(code: str, *, timeout_seconds: float = 30.0) -> ExecutionResult:
    bridge = JupyterKernelBridge()
    return bridge.run(code, timeout_seconds=timeout_seconds)
