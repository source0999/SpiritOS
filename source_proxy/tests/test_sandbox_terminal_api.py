from __future__ import annotations

import subprocess
import unittest
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.sandbox_terminal import router as sandbox_terminal_router
from source_proxy.sandbox.bubblewrap import BubblewrapUnavailable


class SandboxTerminalApiTests(unittest.TestCase):
    def test_sandbox_terminal_run_returns_bounded_result(self) -> None:
        app = FastAPI()
        app.include_router(sandbox_terminal_router)
        client = TestClient(app)
        completed = Mock(returncode=0, stdout="ok\n", stderr="")

        with patch("source_proxy.api.sandbox_terminal.run_bubblewrap", return_value=completed) as run:
            response = client.post(
                "/v1/sandbox/terminal/run",
                json={"command": ["/bin/echo", "ok"], "timeout_seconds": 5},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["tool"], "sandbox_terminal_run")
        self.assertEqual(payload["stdout"], "ok\n")
        self.assertFalse(payload["sandbox"]["workspace_writable"])
        self.assertEqual(payload["sandbox"]["network_policy"], "none")
        self.assertEqual(run.call_args.kwargs["timeout_seconds"], 5)
        self.assertEqual(run.call_args.args[1].network_policy, "none")

    def test_sandbox_terminal_run_reports_bubblewrap_unavailable(self) -> None:
        app = FastAPI()
        app.include_router(sandbox_terminal_router)
        client = TestClient(app)

        with patch(
            "source_proxy.api.sandbox_terminal.run_bubblewrap",
            side_effect=BubblewrapUnavailable("missing bwrap"),
        ):
            response = client.post(
                "/v1/sandbox/terminal/run",
                json={"command": ["/bin/true"]},
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"]["reason_code"], "bubblewrap_unavailable")

    def test_sandbox_terminal_run_reports_timeout(self) -> None:
        app = FastAPI()
        app.include_router(sandbox_terminal_router)
        client = TestClient(app)

        with patch(
            "source_proxy.api.sandbox_terminal.run_bubblewrap",
            side_effect=subprocess.TimeoutExpired(["/bin/sleep", "5"], timeout=1),
        ):
            response = client.post(
                "/v1/sandbox/terminal/run",
                json={"command": ["/bin/sleep", "5"], "timeout_seconds": 1},
            )

        self.assertEqual(response.status_code, 408)
        self.assertEqual(response.json()["detail"]["reason_code"], "sandbox_timeout")


if __name__ == "__main__":
    unittest.main()
