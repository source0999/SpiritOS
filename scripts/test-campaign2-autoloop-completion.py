#!/usr/bin/env python3
"""Regression tests for strict Campaign 2 completion detection."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


EVALUATOR = Path(__file__).with_name("campaign2-autoloop-completion.py")
MANDATORY = [
    "gate_2_1_versioned_lane_registry_and_contracts",
    "gate_2_2_canonical_orchestrator_and_lane_state_machine",
    "gate_2_3_canonical_context_broker_consumption_acknowledgement",
    "gate_2_4_source_proxy_routing_health_fallback_truthfulness",
    "gate_2_5_typescript_python_target_plugin_reconciliation",
    "gate_2_6_canonical_executor_and_lane_scoped_authority",
    "gate_2_7_reviewer_verifier_anticheat_evidence_identity_binding",
    "gate_2_8_cartographer_core_discovery_proposal_integration",
    "gate_2_9_task_lifecycle_reliability_and_recovery",
    "gate_2_10_canonical_shell_observability",
    "gate_2_11_core_proving_task_and_final_acceptance",
    "campaign2_complete",
]


def valid_state() -> dict:
    return {
        "schema": "spiritos-campaign-2-state/v1",
        "campaign_id": "spiritos-campaign-2",
        "ledger_path": "docs/architecture/campaign-2-ledger.md",
        "go_eligible": True,
        "current_phase": "Campaign 2 complete",
        "next_gate_id": "campaign2_complete",
        "completed_gate_ids": list(MANDATORY),
        "partial_gate_ids": [],
        "valid_stop_reasons": ["CAMPAIGN_2_CORE_CODING_OS_STABLE"],
        "closeout": {
            "verdict": "CAMPAIGN_2_CORE_CODING_OS_STABLE",
            "status": "complete",
            "core_proving_task_passed_from_clean_baseline": True,
            "controlled_failure_injected_and_recovered": True,
            "clean_rerun_passed": True,
            "critical_blocker": None,
            "campaign3_started": False,
        },
    }


class Campaign2CompletionTests(unittest.TestCase):
    def run_evaluator(self, state: object, ledger: str = "# Ledger\nCampaign: `spiritos-campaign-2`\n") -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, ledger_path = root / "state.json", root / "ledger.md"
            state_path.write_text(json.dumps(state) if not isinstance(state, str) else state, encoding="utf-8")
            ledger_path.write_text(ledger, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(EVALUATOR), "--state", str(state_path), "--ledger", str(ledger_path)],
                text=True, capture_output=True, check=False,
            )

    def test_valid_go_stops(self) -> None:
        result = self.run_evaluator(valid_state())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("CAMPAIGN_2_COMPLETE", result.stdout)

    def test_stale_markdown_below_summary_does_not_restart(self) -> None:
        ledger = (
            "Campaign: `spiritos-campaign-2`\nGO eligibility: `true`\n"
            "Historical: GO eligibility: `false`; blocked; phase not complete\n"
        )
        result = self.run_evaluator(valid_state(), ledger)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_go_false_does_not_stop(self) -> None:
        state = valid_state()
        state["go_eligible"] = False
        result = self.run_evaluator(state)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("go_not_true", result.stdout)

    def test_malformed_or_missing_state_fails_closed(self) -> None:
        result = self.run_evaluator("{")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CAMPAIGN_2_NOT_COMPLETE", result.stdout)

    def test_incomplete_mandatory_gates_do_not_stop(self) -> None:
        state = valid_state()
        state["completed_gate_ids"].remove("gate_2_11_core_proving_task_and_final_acceptance")
        result = self.run_evaluator(state)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mandatory_gates_missing", result.stdout)

    def test_proving_task_proof_required(self) -> None:
        # All gates complete and verdict set, but the clean-rerun proof is false.
        state = valid_state()
        state["closeout"]["clean_rerun_passed"] = False
        result = self.run_evaluator(state)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("closeout_proof_incomplete:clean_rerun_passed", result.stdout)

    def test_current_real_state_is_not_yet_complete(self) -> None:
        # The committed campaign-2-state.json must currently evaluate NOT complete
        # (the campaign has not been executed yet). Guards against a false-GO.
        repo_state = Path(__file__).parents[1] / "docs/architecture/campaign-2-state.json"
        repo_ledger = Path(__file__).parents[1] / "docs/architecture/campaign-2-ledger.md"
        state = json.loads(repo_state.read_text(encoding="utf-8"))
        ledger = repo_ledger.read_text(encoding="utf-8")
        result = self.run_evaluator(state, ledger)
        self.assertNotEqual(result.returncode, 0, "initial Campaign 2 state must NOT be terminal")
        self.assertIn("CAMPAIGN_2_NOT_COMPLETE", result.stdout)


if __name__ == "__main__":
    unittest.main()
