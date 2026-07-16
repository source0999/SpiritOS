#!/usr/bin/env python3
"""Regression tests for strict Campaign 1 autoloop completion detection."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


EVALUATOR = Path(__file__).with_name("campaign1-autoloop-completion.py")
MANDATORY = [
    "phase0_authenticated_no_reversion", "phase2_shared_contracts_and_boundary_enforcement",
    "phase3_canonical_shell_migration", "phase3_evidence_and_gallery_externalization",
    "phase3_context_discovery_exclusions", "phase3_python_target_adapter",
    "phase3_duplicate_path_reconciliation", "phase3_truthful_test_profile_registry",
    "phase3_authenticated_browser_lifecycle_credential_gate", "phase3_final_acceptance",
    "ar001_spiritflix_authority", "ar002_cartographer_durable_selection_consumer_proof",
    "ar003_design_writeback_final_acknowledgement_envelope", "campaign1_complete",
]


def valid_state() -> dict:
    return {
        "schema": "spiritos-campaign-1-state/v1", "campaign_id": "spiritos-campaign-1",
        "ledger_path": "docs/architecture/campaign-1-ledger.md", "go_eligible": True,
        "current_phase": "Campaign 1 complete", "next_gate_id": "campaign1_complete",
        "completed_gate_ids": list(MANDATORY), "partial_gate_ids": [],
        "valid_stop_reasons": ["GO_CAMPAIGN_1_COMPLETE"],
        "closeout": {"verdict": "GO_CAMPAIGN_1_COMPLETE", "status": "complete", "s1_verified": True,
                     "commit_safe": True, "critical_blocker": None, "campaign2_started": False,
                     "phase_acceptance": {phase: "accepted" for phase in ("phase0", "phase1", "phase2", "phase3")},
                     "ar_acceptance": {ar: "accepted" for ar in ("AR-001", "AR-002", "AR-003")}},
    }


class CampaignAutoloopCompletionTests(unittest.TestCase):
    def run_evaluator(self, state: object, ledger: str = "# Ledger\nCampaign: `spiritos-campaign-1`\n") -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state_path, ledger_path = root / "state.json", root / "ledger.md"
            state_path.write_text(json.dumps(state) if not isinstance(state, str) else state, encoding="utf-8")
            ledger_path.write_text(ledger, encoding="utf-8")
            return subprocess.run([sys.executable, str(EVALUATOR), "--state", str(state_path), "--ledger", str(ledger_path)], text=True, capture_output=True, check=False)

    def test_valid_go_stops(self) -> None:
        result = self.run_evaluator(valid_state())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("CAMPAIGN_1_COMPLETE", result.stdout)

    def test_stale_markdown_below_summary_does_not_restart(self) -> None:
        result = self.run_evaluator(valid_state(), "Campaign: `spiritos-campaign-1`\nGO eligibility: `true`\nHistorical: GO eligibility: `false`; blocked\n")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_go_false_does_not_stop(self) -> None:
        state = valid_state(); state["go_eligible"] = False
        result = self.run_evaluator(state)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("go_not_true", result.stdout)

    def test_malformed_or_missing_state_fails_closed(self) -> None:
        result = self.run_evaluator("{")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("CAMPAIGN_1_NOT_COMPLETE", result.stdout)

    def test_incomplete_mandatory_gates_do_not_stop(self) -> None:
        state = valid_state(); state["completed_gate_ids"].remove("phase3_final_acceptance")
        result = self.run_evaluator(state)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mandatory_gates_missing", result.stdout)

    def test_terminal_gate_with_blocker_is_rejected(self) -> None:
        state = valid_state(); state["closeout"]["critical_blocker"] = "credential"
        result = self.run_evaluator(state)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("critical_blocker_present", result.stdout)

    def test_current_valid_final_state_is_accepted(self) -> None:
        state = json.loads((Path(__file__).parents[1] / "docs/architecture/campaign-1-state.json").read_text(encoding="utf-8"))
        ledger = (Path(__file__).parents[1] / "docs/architecture/campaign-1-ledger.md").read_text(encoding="utf-8")
        result = self.run_evaluator(state, ledger)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
