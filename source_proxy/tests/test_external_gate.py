from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from source_proxy.approval.external_gate import ExternalGateError, central_gate_check


class ExternalGateTests(unittest.TestCase):
    def test_closed_gate_blocks_model_call(self) -> None:
        with self._gate_state({"status": "WAITING_FOR_HUMAN"}) as path:
            with patch.dict(os.environ, {"SOURCE_PROXY_GATE_STATE_PATH": str(path)}, clear=False):
                with self.assertRaises(ExternalGateError) as context:
                    central_gate_check("model_call", increment_id="1.3", run_id="test")

        self.assertEqual(context.exception.reason_code, "gate_closed")
        self.assertFalse(context.exception.payload["central_gate_check_passed"])

    def test_increment_mismatch_blocks(self) -> None:
        with self._gate_state(
            {
                "status": "RUNNING_INCREMENT",
                "approved_increment": "1.2",
                "approval_token": "1.2:test",
            }
        ) as path:
            with patch.dict(os.environ, {"SOURCE_PROXY_GATE_STATE_PATH": str(path)}, clear=False):
                with self.assertRaises(ExternalGateError) as context:
                    central_gate_check("gate_implementation", increment_id="1.3", run_id="test")

        self.assertEqual(context.exception.reason_code, "increment_mismatch")

    def test_model_call_requires_explicit_allowed_action(self) -> None:
        with self._gate_state(
            {
                "status": "RUNNING_INCREMENT",
                "approved_increment": "1.3",
                "approval_token": "1.3:test",
            }
        ) as path:
            with patch.dict(os.environ, {"SOURCE_PROXY_GATE_STATE_PATH": str(path)}, clear=False):
                with self.assertRaises(ExternalGateError) as context:
                    central_gate_check("model_call", increment_id="1.3", run_id="test")

        self.assertEqual(context.exception.reason_code, "action_not_allowed_for_increment")

    def test_allowed_action_passes_with_receipt(self) -> None:
        with self._gate_state(
            {
                "status": "RUNNING_INCREMENT",
                "approved_increment": "1.3",
                "approval_token": "1.3:test",
            }
        ) as path:
            with patch.dict(
                os.environ,
                {
                    "SOURCE_PROXY_GATE_STATE_PATH": str(path),
                    "SOURCE_PROXY_GATE_ALLOWED_ACTIONS": "model_call",
                },
                clear=False,
            ):
                receipt = central_gate_check("model_call", increment_id="1.3", run_id="test")

        self.assertEqual(receipt.action, "model_call")
        self.assertEqual(receipt.increment_id, "1.3")
        self.assertEqual(receipt.approval_token_id, "1.3:test")

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
