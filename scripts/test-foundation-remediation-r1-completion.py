#!/usr/bin/env python3
"""Regression tests for fail-closed R1 completion semantics."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = Path(__file__).with_name("foundation-remediation-r1-completion.py")


def load_evaluator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("foundation_remediation_r1_completion", EVALUATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("completion evaluator could not be imported")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVALUATOR_MODULE = load_evaluator()


def valid_terminal_state() -> dict:
    return {
        "schema": EVALUATOR_MODULE.EXPECTED_SCHEMA,
        "remediation_id": EVALUATOR_MODULE.EXPECTED_ID,
        "go_eligible": True,
        "completed_gate_ids": sorted(EVALUATOR_MODULE.MANDATORY_GATES),
        "partial_gate_ids": [],
        "next_gate_id": "r1_complete",
        "terminal_gate_id": "r1_complete",
        "valid_stop_reasons": [EVALUATOR_MODULE.TERMINAL_VERDICT],
        "terminal_evidence": {"receipt_path": "tracked-terminal-receipt.json"},
        "validator_status": {
            "authority_call_graph": "passed",
            "continuity": "passed",
            "evidence_provenance": "passed",
            "test_profiles": "passed",
            "completion": "passed",
        },
        "closeout": {
            "status": "complete",
            "verdict": EVALUATOR_MODULE.TERMINAL_VERDICT,
            **{field: True for field in EVALUATOR_MODULE.MANDATORY_CLOSEOUT_TRUE},
            "critical_blocker": None,
            "campaign_3_started": False,
            "campaign_4_started": False,
            "push_performed": False,
        },
    }


class FoundationRemediationCompletionTests(unittest.TestCase):
    def test_terminal_machine_state_requires_every_invariant(self) -> None:
        complete, failures = EVALUATOR_MODULE.evaluate_terminal_state(valid_terminal_state())
        self.assertTrue(complete, failures)

    def test_self_declared_go_cannot_replace_a_missing_gate(self) -> None:
        state = valid_terminal_state()
        state["completed_gate_ids"].remove("r1_7_production_orchestrator")
        complete, failures = EVALUATOR_MODULE.evaluate_terminal_state(state)
        self.assertFalse(complete)
        self.assertTrue(any(item.startswith("mandatory_gates_missing:") for item in failures))

    def test_false_closeout_invariant_rejects_terminal_verdict(self) -> None:
        state = valid_terminal_state()
        state["closeout"]["independent_participants_passed"] = False
        complete, failures = EVALUATOR_MODULE.evaluate_terminal_state(state)
        self.assertFalse(complete)
        self.assertIn("closeout_invariant_false:independent_participants_passed", failures)

    def test_terminal_completion_rejects_profile_pass_labels_without_execution_receipts(self) -> None:
        failures = EVALUATOR_MODULE.terminal_profile_execution_failures(ROOT, valid_terminal_state())
        self.assertIn("mandatory_profile_execution_missing:continuity", failures)
        self.assertIn("mandatory_profile_execution_evidence_incomplete", failures)

    def test_cli_executes_all_validators_and_rejects_preterminal_state(self) -> None:
        state = valid_terminal_state()
        state.update(
            {
                "go_eligible": False,
                "completed_gate_ids": [],
                "partial_gate_ids": ["r1_0_control_plane"],
                "next_gate_id": "r1_0_control_plane",
                "terminal_evidence": None,
            }
        )
        state["closeout"]["status"] = "in_progress"
        state["closeout"]["verdict"] = None
        with tempfile.TemporaryDirectory() as temp:
            state_path = Path(temp) / "state.json"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(EVALUATOR), "--root", str(ROOT), "--state", str(state_path)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        for name in ("continuity", "authority", "evidence", "test-profiles"):
            self.assertIn(f"[{name}] returncode=", completed.stdout)
        self.assertIn("SPIRITOS_FOUNDATION_REMEDIATION_NOT_COMPLETE", completed.stdout)

    def test_malformed_state_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            state_path = Path(temp) / "state.json"
            state_path.write_text("{", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(EVALUATOR), "--root", str(ROOT), "--state", str(state_path)],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("state_unreadable_or_malformed", completed.stdout)

    def test_next_gate_read_is_non_mutating(self) -> None:
        state = valid_terminal_state()
        state["next_gate_id"] = "r1_5_coding_lifecycle"
        with tempfile.TemporaryDirectory() as temp:
            state_path = Path(temp) / "state.json"
            state_path.write_text(json.dumps(state), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(EVALUATOR), "--root", str(ROOT), "--state", str(state_path), "--next-gate"],
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(completed.stdout.strip(), "r1_5_coding_lifecycle")


if __name__ == "__main__":
    unittest.main()
