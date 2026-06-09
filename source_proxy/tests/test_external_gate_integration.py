from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.chat import router as chat_router
from source_proxy.approval.external_gate import ExternalGateError
from source_proxy.tasks.long_running import _call_coder_llm


class ExternalGateIntegrationTests(unittest.TestCase):
    def test_chat_completion_blocks_before_router_call_when_gate_closed(self) -> None:
        app = FastAPI()
        app.include_router(chat_router)
        with self._gate_state({"status": "WAITING_FOR_HUMAN"}) as path:
            with (
                patch.dict(os.environ, {"SOURCE_PROXY_GATE_STATE_PATH": str(path)}, clear=False),
                patch("source_proxy.api.chat.available_model_aliases", return_value={"local"}) as aliases,
                patch("source_proxy.api.chat.get_router") as get_router,
            ):
                response = TestClient(app).post(
                    "/v1/chat/completions",
                    json={"model": "local", "messages": [{"role": "user", "content": "hi"}]},
                )

        self.assertEqual(response.status_code, 423)
        self.assertEqual(response.json()["detail"]["reason_code"], "gate_closed")
        aliases.assert_not_called()
        get_router.assert_not_called()

    def test_coder_llm_blocks_before_router_call_when_action_not_allowed(self) -> None:
        with self._gate_state(
            {
                "status": "RUNNING_INCREMENT",
                "approved_increment": "1.3",
                "approval_token": "1.3:test",
            }
        ) as path:
            with (
                patch.dict(os.environ, {"SOURCE_PROXY_GATE_STATE_PATH": str(path)}, clear=False),
                patch("source_proxy.tasks.long_running.get_router") as get_router,
            ):
                with self.assertRaises(ExternalGateError) as context:
                    _call_coder_llm("test", model_alias="coder")

        self.assertEqual(context.exception.reason_code, "action_not_allowed_for_increment")
        get_router.assert_not_called()

    def _gate_state(self, overrides: dict[str, object]):
        class GateStateContext:
            def __enter__(inner_self) -> Path:
                inner_self.temp_dir = tempfile.TemporaryDirectory()
                path = Path(inner_self.temp_dir.name) / "state.json"
                state = {
                    "status": "WAITING_FOR_HUMAN",
                    "approved_increment": None,
                    "last_completed_increment": None,
                    "approval_token": None,
                    "updated_at": None,
                    "notes": "",
                }
                state.update(overrides)
                path.write_text(json.dumps(state), encoding="utf-8")
                return path

            def __exit__(inner_self, *_args: object) -> None:
                inner_self.temp_dir.cleanup()

        return GateStateContext()
