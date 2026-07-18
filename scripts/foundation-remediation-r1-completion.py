#!/usr/bin/env python3
"""Fail-closed Foundation Remediation R1 completion evaluator."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


EXPECTED_SCHEMA = "spiritos-foundation-remediation-r1-state/v1"
EXPECTED_ID = "spiritos-foundation-remediation-r1"
PROFILE_RECEIPT_SCHEMA = "spiritos-foundation-remediation-r1-profile-execution-receipt/v1"
TERMINAL_VERDICT = "SPIRITOS_FOUNDATION_REMEDIATION_COMPLETE"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MANDATORY_GATES = {
    "r1_0_control_plane",
    "r1_1_portable_authority",
    "r1_2_cartographer_authority",
    "r1_3_spiritflix_authority",
    "r1_4_design_security",
    "r1_5_coding_lifecycle",
    "r1_6_target_adapters_1_10",
    "r1_7_production_orchestrator",
    "r1_8_runtime_contracts_and_cartographer_transfer",
    "r1_9_backend_state_and_recovery",
    "r1_10_immutable_evidence",
    "r1_11_clean_proving_task",
    "r1_12_closeout",
    "r1_complete",
}
MANDATORY_CLOSEOUT_TRUE = {
    "production_call_graph_passed",
    "authority_boundaries_passed",
    "independent_participants_passed",
    "runtime_contracts_passed",
    "backend_state_owner_passed",
    "target_adapters_1_10_passed",
    "clean_proving_task_passed",
    "controlled_failure_recovered_in_lineage",
    "undo_reset_clean_rerun_passed",
    "immutable_evidence_anchored",
    "temporary_authority_revoked",
    "protected_heads_verified",
}
VALIDATORS = (
    ("continuity", "validate-foundation-remediation-r1-continuity.py"),
    ("authority", "validate-foundation-remediation-r1-authority.py"),
    ("evidence", "validate-foundation-remediation-r1-evidence.py"),
    ("test-profiles", "validate-foundation-remediation-r1-test-profiles.py"),
)


def load_state(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, f"state_unreadable_or_malformed:{error}"
    if not isinstance(payload, dict):
        return None, "state_not_object"
    return payload, None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_repo_path(root: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = (root / value).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path


def terminal_candidate(state: dict[str, Any]) -> bool:
    closeout = state.get("closeout")
    return bool(
        state.get("go_eligible") is True
        or "r1_complete" in (state.get("completed_gate_ids") or [])
        or (isinstance(closeout, dict) and closeout.get("status") == "complete")
    )


def terminal_profile_execution_failures(root: Path, state: dict[str, Any]) -> list[str]:
    """Independently reject terminal metadata without real profile receipts.

    The profile validator performs the full Git/tag checks. This second completion
    gate deliberately verifies the decision-bearing bindings itself so a registry
    full of ``passed`` labels cannot make completion true.
    """
    if not terminal_candidate(state):
        return []
    failures: list[str] = []
    registry_path = root / "docs/architecture/foundation-remediation-r1-test-profiles.json"
    registry, error = load_state(registry_path)
    if error:
        return [f"mandatory_profile_registry_invalid:{error}"]
    assert registry is not None
    profiles = registry.get("profiles")
    if not isinstance(profiles, list):
        return ["mandatory_profile_registry_invalid:profiles_not_array"]
    evidence = state.get("terminal_evidence")
    source_commit = evidence.get("source_commit") if isinstance(evidence, dict) else None
    if not isinstance(source_commit, str) or not HEX40.fullmatch(source_commit):
        failures.append("mandatory_profile_source_commit_missing")

    mandatory_count = 0
    bound_ids: set[str] = set()
    receipt_paths: set[str] = set()
    for index, profile in enumerate(profiles):
        if not isinstance(profile, dict) or profile.get("mandatory") is not True:
            continue
        mandatory_count += 1
        profile_id = profile.get("id")
        if not isinstance(profile_id, str) or not profile_id:
            failures.append(f"mandatory_profile_id_invalid:{index}")
            continue
        if profile.get("status") != "passed":
            failures.append(f"mandatory_profile_execution_missing:{profile_id}")
        accepted = profile.get("latest_accepted")
        if not isinstance(accepted, dict):
            failures.append(f"mandatory_profile_receipt_missing:{profile_id}")
            continue
        receipt_path = safe_repo_path(root, accepted.get("receipt_path"))
        if receipt_path is None or not receipt_path.is_file():
            failures.append(f"mandatory_profile_receipt_missing:{profile_id}")
            continue
        relative = receipt_path.relative_to(root).as_posix()
        if relative in receipt_paths:
            failures.append(f"mandatory_profile_receipt_reused:{profile_id}")
        receipt_paths.add(relative)
        recorded_receipt_hash = accepted.get("receipt_sha256")
        if not isinstance(recorded_receipt_hash, str) or not HEX64.fullmatch(recorded_receipt_hash):
            failures.append(f"mandatory_profile_receipt_hash_invalid:{profile_id}")
        elif sha256(receipt_path) != recorded_receipt_hash:
            failures.append(f"mandatory_profile_receipt_hash_mismatch:{profile_id}")
        receipt, receipt_error = load_state(receipt_path)
        if receipt_error:
            failures.append(f"mandatory_profile_receipt_invalid:{profile_id}")
            continue
        assert receipt is not None
        if receipt.get("schema") != PROFILE_RECEIPT_SCHEMA:
            failures.append(f"mandatory_profile_receipt_schema_mismatch:{profile_id}")
        if receipt.get("remediation_id") != EXPECTED_ID:
            failures.append(f"mandatory_profile_receipt_remediation_mismatch:{profile_id}")
        if receipt.get("profile_id") != profile_id:
            failures.append(f"mandatory_profile_receipt_profile_mismatch:{profile_id}")
        elif profile_id in bound_ids:
            failures.append(f"mandatory_profile_receipt_profile_reused:{profile_id}")
        else:
            bound_ids.add(profile_id)
        if receipt.get("command") != profile.get("command"):
            failures.append(f"mandatory_profile_receipt_command_mismatch:{profile_id}")
        if receipt.get("claim_ceiling") != profile.get("claim_ceiling"):
            failures.append(f"mandatory_profile_receipt_claim_ceiling_mismatch:{profile_id}")
        if receipt.get("source_commit") != source_commit:
            failures.append(f"mandatory_profile_receipt_source_mismatch:{profile_id}")
        if receipt.get("result") != "pass" or receipt.get("passed") is not True:
            failures.append(f"mandatory_profile_receipt_result_not_pass:{profile_id}")
        artifact_path = safe_repo_path(root, receipt.get("artifact_path"))
        artifact_hash = receipt.get("artifact_sha256")
        if artifact_path is None or not artifact_path.is_file():
            failures.append(f"mandatory_profile_artifact_missing:{profile_id}")
        elif not isinstance(artifact_hash, str) or not HEX64.fullmatch(artifact_hash):
            failures.append(f"mandatory_profile_artifact_hash_invalid:{profile_id}")
        elif sha256(artifact_path) != artifact_hash:
            failures.append(f"mandatory_profile_artifact_hash_mismatch:{profile_id}")

    if mandatory_count == 0:
        failures.append("mandatory_profiles_missing")
    if len(bound_ids) != mandatory_count:
        failures.append("mandatory_profile_execution_evidence_incomplete")
    return sorted(set(failures))


def evaluate_terminal_state(state: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if state.get("schema") != EXPECTED_SCHEMA:
        failures.append("unsupported_state_schema")
    if state.get("remediation_id") != EXPECTED_ID:
        failures.append("remediation_identity_mismatch")
    if state.get("go_eligible") is not True:
        failures.append("go_not_true")
    completed = state.get("completed_gate_ids")
    if not isinstance(completed, list) or not all(isinstance(item, str) for item in completed):
        failures.append("completed_gates_invalid")
    else:
        missing = sorted(MANDATORY_GATES - set(completed))
        if missing:
            failures.append("mandatory_gates_missing:" + ",".join(missing))
    if state.get("partial_gate_ids") != []:
        failures.append("partial_gates_present")
    if state.get("next_gate_id") not in {"r1_complete", "none", None}:
        failures.append("next_gate_not_terminal")
    if state.get("terminal_gate_id") != "r1_complete":
        failures.append("terminal_gate_id_mismatch")
    if TERMINAL_VERDICT not in (state.get("valid_stop_reasons") or []):
        failures.append("terminal_stop_reason_missing")
    if not isinstance(state.get("terminal_evidence"), dict):
        failures.append("terminal_evidence_missing")
    validator_status = state.get("validator_status")
    if not isinstance(validator_status, dict):
        failures.append("validator_status_missing")
    else:
        for field in ("authority_call_graph", "continuity", "evidence_provenance", "test_profiles"):
            if validator_status.get(field) not in {"passed", "valid", "complete"}:
                failures.append(f"validator_status_not_terminal:{field}")
        if validator_status.get("completion") not in {"ready_for_evaluation", "passed", "valid", "complete"}:
            failures.append("validator_status_not_terminal:completion")

    closeout = state.get("closeout")
    if not isinstance(closeout, dict):
        failures.append("closeout_missing")
    else:
        if closeout.get("status") != "complete" or closeout.get("verdict") != TERMINAL_VERDICT:
            failures.append("closeout_verdict_invalid")
        for field in sorted(MANDATORY_CLOSEOUT_TRUE):
            if closeout.get(field) is not True:
                failures.append(f"closeout_invariant_false:{field}")
        if closeout.get("critical_blocker") is not None:
            failures.append("critical_blocker_present")
        if closeout.get("campaign_3_started") is not False:
            failures.append("campaign_3_started")
        if closeout.get("campaign_4_started") is not False:
            failures.append("campaign_4_started")
        if closeout.get("push_performed") is not False:
            failures.append("push_performed")
    return not failures, failures


def run_validators(root: Path) -> tuple[bool, list[str]]:
    script_dir = Path(__file__).resolve().parent
    failures: list[str] = []
    for name, filename in VALIDATORS:
        completed = subprocess.run(
            [sys.executable, str(script_dir / filename), "--root", str(root)],
            text=True,
            capture_output=True,
            check=False,
        )
        combined = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part)
        print(f"[{name}] returncode={completed.returncode}")
        if combined:
            print(combined)
        if completed.returncode != 0:
            failures.append(f"validator_failed:{name}")
    return not failures, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(os.environ.get("SPIRITOS_FOUNDATION_R1_ROOT", Path(__file__).resolve().parents[1])),
    )
    parser.add_argument("--state", type=Path)
    parser.add_argument("--next-gate", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    state_path = args.state.resolve() if args.state else root / "docs/architecture/foundation-remediation-r1-state.json"
    state, error = load_state(state_path)
    if args.next_gate:
        if error:
            print(f"FOUNDATION_REMEDIATION_R1_NEXT_GATE_UNAVAILABLE {error}")
            return 1
        assert state is not None
        next_gate = state.get("next_gate_id")
        if not isinstance(next_gate, str):
            print("FOUNDATION_REMEDIATION_R1_NEXT_GATE_UNAVAILABLE")
            return 1
        print(next_gate)
        return 0

    validators_ok, validator_failures = run_validators(root)
    if error:
        print(f"SPIRITOS_FOUNDATION_REMEDIATION_NOT_COMPLETE {error}," + ",".join(validator_failures))
        return 1
    assert state is not None
    terminal, state_failures = evaluate_terminal_state(state)
    profile_execution_failures = terminal_profile_execution_failures(root, state)
    failures = [*validator_failures, *state_failures, *profile_execution_failures]
    if validators_ok and terminal:
        print(TERMINAL_VERDICT)
        return 0
    print("SPIRITOS_FOUNDATION_REMEDIATION_NOT_COMPLETE " + ",".join(failures))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
