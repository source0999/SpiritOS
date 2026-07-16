#!/usr/bin/env python3
"""Strict, fail-closed Campaign 2 terminal-state evaluator.

Reads docs/architecture/campaign-2-state.json and decides whether Campaign 2 is
genuinely complete. Markdown is never parsed to infer JSON values; the JSON
state is the only source of truth for completion. Mirrors the Campaign 1
completion-evaluator pattern but keyed on the Campaign 2 terminal verdict and
its 11 mandatory gates.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


MANDATORY_GATES = {
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
}
EXPECTED_SCHEMA = "spiritos-campaign-2-state/v1"
EXPECTED_CAMPAIGN = "spiritos-campaign-2"
EXPECTED_LEDGER = "docs/architecture/campaign-2-ledger.md"
TERMINAL_VERDICT = "CAMPAIGN_2_CORE_CODING_OS_STABLE"


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
    if state.get("schema") != EXPECTED_SCHEMA:
        return reject("unsupported_state_schema")
    if state.get("campaign_id") != EXPECTED_CAMPAIGN:
        return reject("campaign_identity_mismatch")
    if state.get("ledger_path") != EXPECTED_LEDGER:
        return reject("ledger_path_mismatch")
    # Ledger must exist and identify the campaign (proves the control plane is coherent).
    try:
        ledger_text = ledger.read_text(encoding="utf-8")
    except OSError as error:
        return reject(f"ledger_unreadable:{error}")
    if "Campaign: `spiritos-campaign-2`" not in ledger_text:
        return reject("ledger_state_campaign_identity_mismatch")
    if state.get("go_eligible") is not True:
        return reject("go_not_true")
    if state.get("current_phase") != "Campaign 2 complete":
        return reject("phase_not_complete")
    if state.get("next_gate_id") not in {"campaign2_complete", None, "none"}:
        return reject("next_gate_not_terminal")
    completed = state.get("completed_gate_ids")
    if not isinstance(completed, list) or not all(isinstance(item, str) for item in completed):
        return reject("completed_gates_invalid")
    missing = sorted(MANDATORY_GATES - set(completed))
    if missing:
        return reject("mandatory_gates_missing:" + ",".join(missing))
    if state.get("partial_gate_ids") != []:
        return reject("partial_gates_present")
    if TERMINAL_VERDICT not in state.get("valid_stop_reasons", []):
        return reject("terminal_stop_reason_missing")
    closeout = state.get("closeout")
    if not isinstance(closeout, dict):
        return reject("closeout_missing")
    if closeout.get("verdict") != TERMINAL_VERDICT or closeout.get("status") != "complete":
        return reject("closeout_verdict_invalid")
    # The proving-task is the load-bearing proof; require every boolean.
    for proof_key in (
        "core_proving_task_passed_from_clean_baseline",
        "controlled_failure_injected_and_recovered",
        "clean_rerun_passed",
    ):
        if closeout.get(proof_key) is not True:
            return reject(f"closeout_proof_incomplete:{proof_key}")
    if closeout.get("critical_blocker") is not None:
        return reject("critical_blocker_present")
    if closeout.get("campaign3_started") is not False:
        return reject("campaign3_started")
    return True, "campaign2_complete"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--next-gate", action="store_true")
    args = parser.parse_args()
    state, error = load_state(args.state)
    if error:
        print(f"CAMPAIGN_2_NOT_COMPLETE {error}")
        return 1
    if args.next_gate:
        if state.get("schema") != EXPECTED_SCHEMA or state.get("campaign_id") != EXPECTED_CAMPAIGN:
            print("CAMPAIGN_2_NEXT_GATE_UNAVAILABLE")
            return 1
        next_gate = state.get("next_gate_id")
        if next_gate is None:
            print("none")
            return 0
        if not isinstance(next_gate, str):
            print("CAMPAIGN_2_NEXT_GATE_UNAVAILABLE")
            return 1
        print(next_gate)
        return 0
    complete, message = terminal_state(state, args.ledger)
    print("CAMPAIGN_2_COMPLETE" if complete else f"CAMPAIGN_2_NOT_COMPLETE {message}")
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
