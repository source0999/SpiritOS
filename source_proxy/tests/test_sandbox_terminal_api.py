from __future__ import annotations

import subprocess
import unittest
from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.sandbox_terminal import (
    _terminal_sessions,
    router as sandbox_terminal_router,
)
from source_proxy.sandbox.bubblewrap import BubblewrapUnavailable


class SandboxTerminalApiTests(unittest.TestCase):
    def setUp(self) -> None:
        _terminal_sessions.clear()

    def tearDown(self) -> None:
        _terminal_sessions.clear()

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
        self.assertEqual(payload["session"]["command_count"], 1)
        self.assertFalse(payload["session"]["writes_allowed"])
        self.assertTrue(payload["session"]["approval_required_for_apply"])
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

    def test_sandbox_terminal_sessions_persist_command_history(self) -> None:
        app = FastAPI()
        app.include_router(sandbox_terminal_router)
        client = TestClient(app)
        completed = Mock(returncode=0, stdout="ok\n", stderr="")

        with patch("source_proxy.api.sandbox_terminal.run_bubblewrap", return_value=completed):
            first = client.post(
                "/v1/sandbox/terminal/run",
                json={
                    "command": ["/bin/echo", "first"],
                    "session_id": "test-session",
                    "session_kind": "test_run",
                    "session_label": "Targeted tests",
                },
            )
            second = client.post(
                "/v1/sandbox/terminal/run",
                json={"command": ["/bin/echo", "second"], "session_id": "test-session"},
            )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["session"]["id"], "test-session")
        self.assertEqual(second.json()["session"]["kind"], "test_run")
        self.assertEqual(second.json()["session"]["command_count"], 2)

        listed = client.get("/v1/sandbox/terminal/sessions")
        self.assertEqual(listed.status_code, 200)
        self.assertFalse(listed.json()["write_actions_enabled"])
        self.assertEqual(listed.json()["sessions"][0]["id"], "test-session")
        self.assertNotIn("history", listed.json()["sessions"][0])

        detail = client.get("/v1/sandbox/terminal/sessions/test-session")
        self.assertEqual(detail.status_code, 200)
        history = detail.json()["session"]["history"]
        self.assertEqual([entry["command"] for entry in history], [["/bin/echo", "first"], ["/bin/echo", "second"]])

    def test_sandbox_terminal_session_detail_reports_missing_session(self) -> None:
        app = FastAPI()
        app.include_router(sandbox_terminal_router)
        client = TestClient(app)

        response = client.get("/v1/sandbox/terminal/sessions/missing")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"]["reason_code"], "terminal_session_not_found")

    def test_sandbox_terminal_presets_are_declarative_and_non_writing(self) -> None:
        app = FastAPI()
        app.include_router(sandbox_terminal_router)
        client = TestClient(app)

        response = client.get("/v1/sandbox/terminal/presets")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["tool"], "sandbox_terminal_presets")
        self.assertFalse(payload["write_actions_enabled"])
        by_id = {preset["id"]: preset for preset in payload["presets"]}
        self.assertIn("proxy-smoke", by_id)
        self.assertIn("targeted-proxy-tests", by_id)
        self.assertIn("scout-tests", by_id)
        self.assertIn("cartographer-safety-audit", by_id)
        self.assertIn("typecheck", by_id)
        self.assertIn("lint", by_id)
        self.assertTrue(
            all(preset["writes_allowed"] is False for preset in payload["presets"])
        )
        self.assertTrue(
            all(preset["approval_required_for_apply"] is True for preset in payload["presets"])
        )
        self.assertEqual(by_id["proxy-smoke"]["session_kind"], "test_run")


if __name__ == "__main__":
    unittest.main()
