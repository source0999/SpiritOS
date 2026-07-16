#!/usr/bin/env python3
"""Strict, fail-closed Campaign 1 terminal-state evaluator for the autoloop."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


MANDATORY_GATES = {
    "phase0_authenticated_no_reversion",
    "phase2_shared_contracts_and_boundary_enforcement",
    "phase3_canonical_shell_migration",
    "phase3_evidence_and_gallery_externalization",
    "phase3_context_discovery_exclusions",
    "phase3_python_target_adapter",
    "phase3_duplicate_path_reconciliation",
    "phase3_truthful_test_profile_registry",
    "phase3_authenticated_browser_lifecycle_credential_gate",
    "phase3_final_acceptance",
    "ar001_spiritflix_authority",
    "ar002_cartographer_durable_selection_consumer_proof",
    "ar003_design_writeback_final_acknowledgement_envelope",
    "campaign1_complete",
}
PHASES = {"phase0", "phase1", "phase2", "phase3"}
ARS = {"AR-001", "AR-002", "AR-003"}


def reject(message: str) -> tuple[bool, str]:
    return False, message


def load_state(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, f"state_unreadable_or_malformed:{error}"
    if not isinstance(payload, dict):
        return None, "state_not_object"
    return payload, None


def terminal_state(state: dict[str, Any], ledger: Path) -> tuple[bool, str]:
    if state.get("schema") != "spiritos-campaign-1-state/v1":
        return reject("unsupported_state_schema")
    if state.get("campaign_id") != "spiritos-campaign-1":
        return reject("campaign_identity_mismatch")
    if state.get("ledger_path") != "docs/architecture/campaign-1-ledger.md":
        return reject("ledger_path_mismatch")
    try:
        ledger_text = ledger.read_text(encoding="utf-8")
    except OSError as error:
        return reject(f"ledger_unreadable:{error}")
    if "Campaign: `spiritos-campaign-1`" not in ledger_text:
        return reject("ledger_state_campaign_identity_mismatch")
    if state.get("go_eligible") is not True:
        return reject("go_not_true")
    if state.get("current_phase") != "Campaign 1 complete":
        return reject("phase_not_complete")
    if state.get("next_gate_id") not in {"campaign1_complete", None, "none"}:
        return reject("next_gate_not_terminal")
    completed = state.get("completed_gate_ids")
    if not isinstance(completed, list) or not all(isinstance(item, str) for item in completed):
        return reject("completed_gates_invalid")
    missing = sorted(MANDATORY_GATES - set(completed))
    if missing:
        return reject("mandatory_gates_missing:" + ",".join(missing))
    if state.get("partial_gate_ids") != []:
        return reject("partial_gates_present")
    if "GO_CAMPAIGN_1_COMPLETE" not in state.get("valid_stop_reasons", []):
        return reject("terminal_stop_reason_missing")
    closeout = state.get("closeout")
    if not isinstance(closeout, dict):
        return reject("closeout_missing")
    if closeout.get("verdict") != "GO_CAMPAIGN_1_COMPLETE" or closeout.get("status") != "complete":
        return reject("closeout_verdict_invalid")
    if closeout.get("s1_verified") is not True or closeout.get("commit_safe") is not True:
        return reject("closeout_verification_incomplete")
    if closeout.get("critical_blocker") is not None:
        return reject("critical_blocker_present")
    if closeout.get("campaign2_started") is not False:
        return reject("campaign2_started")
    phases = closeout.get("phase_acceptance")
    if not isinstance(phases, dict) or any(phases.get(phase) != "accepted" for phase in PHASES):
        return reject("phase_acceptance_incomplete")
    ars = closeout.get("ar_acceptance")
    if not isinstance(ars, dict) or any(ars.get(ar) != "accepted" for ar in ARS):
        return reject("ar_acceptance_incomplete")
    return True, "campaign1_complete"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--next-gate", action="store_true")
    args = parser.parse_args()
    state, error = load_state(args.state)
    if error:
        print(f"CAMPAIGN_1_NOT_COMPLETE {error}")
        return 1
    if args.next_gate:
        if state.get("schema") != "spiritos-campaign-1-state/v1" or state.get("campaign_id") != "spiritos-campaign-1":
            print("CAMPAIGN_1_NEXT_GATE_UNAVAILABLE")
            return 1
        next_gate = state.get("next_gate_id")
        if next_gate is None:
            print("none")
            return 0
        if not isinstance(next_gate, str):
            print("CAMPAIGN_1_NEXT_GATE_UNAVAILABLE")
            return 1
        print(next_gate)
        return 0
    complete, message = terminal_state(state, args.ledger)
    print("CAMPAIGN_1_COMPLETE" if complete else f"CAMPAIGN_1_NOT_COMPLETE {message}")
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
