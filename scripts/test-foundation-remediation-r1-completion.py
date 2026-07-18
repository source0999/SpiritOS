#!/usr/bin/env python3
"""Regression tests for fail-closed R1 completion semantics."""
from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import ModuleType
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = Path(__file__).with_name("foundation-remediation-r1-completion.py")
AUTHORITY_VALIDATOR = Path(__file__).with_name("validate-foundation-remediation-r1-authority.py")


def load_evaluator() -> ModuleType:
    spec = importlib.util.spec_from_file_location("foundation_remediation_r1_completion", EVALUATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("completion evaluator could not be imported")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_authority_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "foundation_remediation_r1_authority", AUTHORITY_VALIDATOR
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("authority validator could not be imported")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


EVALUATOR_MODULE = load_evaluator()
AUTHORITY_MODULE = load_authority_validator()


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
    def test_authority_validator_detects_direct_decision_task_advance_bypass(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "source_proxy/api/decision.py"
            path.parent.mkdir(parents=True)
            source = (ROOT / "source_proxy/api/decision.py").read_text(encoding="utf-8")
            source = source.replace(
                "get_coding_orchestrator().advance(task_id)",
                "advance_long_running_task(task_id)",
                1,
            )
            path.write_text(source, encoding="utf-8")
            failures: list[str] = []
            AUTHORITY_MODULE.production_prompt_packet_authority_failures(root, failures)
        self.assertIn("production_decision_direct_task_advance_bypass", failures)

    def test_authority_validator_detects_presynthesized_cartographer_participant(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "source_proxy/cartographer/proposal_review_authority.py"
            path.parent.mkdir(parents=True)
            source = (ROOT / "source_proxy/cartographer/proposal_review_authority.py").read_text(
                encoding="utf-8"
            )
            source = source.replace(
                '"participant_requirements": participant_requirements,\n        "result_payload": result_payload,',
                '"participant_requirements": participant_requirements,\n        "invocation_id": "forged-preview-invocation",\n        "result_payload": result_payload,',
                1,
            )
            path.write_text(source, encoding="utf-8")
            failures: list[str] = []
            AUTHORITY_MODULE.cartographer_proposal_review_invariant_failures(root, failures)
        self.assertTrue(
            any(item.startswith("cartographer_review_plan_presynthesizes_runtime_state") for item in failures),
            failures,
        )

    def test_authority_validator_detects_cartographer_finalization_before_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            authority = root / "source_proxy/cartographer/cartographer_selection_authority.py"
            authority.parent.mkdir(parents=True)
            authority.write_text(
                "\n".join(
                    (
                        "proposal.persisted is not True",
                        "proposal.status not in",
                        "proposal.warnings",
                        "target not in proposed_files",
                        "cartographer_selection_target_not_proposed",
                        "cartographer.downstream-acknowledgement/v2",
                        "consumer_output_id consumer_output_sha256 consumer_artifact_sha256 consumer_completed_at",
                    )
                ),
                encoding="utf-8",
            )
            orchestrator = root / "source_proxy/coding/orchestrator.py"
            orchestrator.parent.mkdir(parents=True)
            orchestrator.write_text(
                "class Sample:\n"
                "    def propose_target_plugin(self):\n"
                "        self._finalize_cartographer_transfer_after_invocation()\n"
                "        execute_target_plugin_command()\n"
                "    def execute_approved(self):\n"
                "        self._call_executor()\n",
                encoding="utf-8",
            )
            failures: list[str] = []
            AUTHORITY_MODULE.cartographer_selection_invariant_failures(root, failures)
        self.assertIn(
            "cartographer_selection_finalized_before_downstream_output:propose_target_plugin",
            failures,
        )

    def test_authority_validator_detects_missing_terminal_projection_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            next_path = root / "src/lib/coding/durable-run-store.ts"
            task_path = root / "source_proxy/tasks/long_running.py"
            next_path.parent.mkdir(parents=True)
            task_path.parent.mkdir(parents=True)
            next_path.write_text("export const status = 'completed';\n", encoding="utf-8")
            task_path.write_text("TRUTH = 'GO'\n", encoding="utf-8")
            failures: list[str] = []
            AUTHORITY_MODULE.terminal_projection_invariant_failures(root, failures)
        self.assertIn(
            "next_terminal_projection_invariant_missing:terminal_proof_eligible",
            failures,
        )

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

    def test_profile_execution_failures_are_a_hard_cli_terminal_blocker(self) -> None:
        output = io.StringIO()
        with (
            mock.patch.object(EVALUATOR_MODULE, "run_validators", return_value=(True, [])),
            mock.patch.object(
                EVALUATOR_MODULE,
                "load_state",
                return_value=(valid_terminal_state(), None),
            ),
            mock.patch.object(EVALUATOR_MODULE, "evaluate_terminal_state", return_value=(True, [])),
            mock.patch.object(
                EVALUATOR_MODULE,
                "terminal_profile_execution_failures",
                return_value=["mandatory_profile_execution_evidence_incomplete"],
            ),
            mock.patch.object(sys, "argv", [str(EVALUATOR)]),
            redirect_stdout(output),
        ):
            returncode = EVALUATOR_MODULE.main()
        self.assertEqual(returncode, 1)
        self.assertIn("mandatory_profile_execution_evidence_incomplete", output.getvalue())
        self.assertNotIn(EVALUATOR_MODULE.TERMINAL_VERDICT + "\n", output.getvalue())

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
