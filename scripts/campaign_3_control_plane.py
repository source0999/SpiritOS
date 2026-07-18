#!/usr/bin/env python3
"""Fail-closed Campaign 3 control-plane validators and evaluator."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

EXPECTED_SCHEMA = "spiritos-campaign-3-state/v1"
EXPECTED_TEST_SCHEMA = "spiritos-campaign-3-test-profiles/v1"
CAMPAIGN_ID = "spiritos-campaign-3-extended-coding-lanes"
TERMINAL_VERDICT = "CAMPAIGN_3_EXTENDED_CODING_LANES_INTEGRATED"
NOT_COMPLETE = "CAMPAIGN_3_NOT_COMPLETE"
GATE_3_0 = "gate_3_0_entry_verification_and_control_plane"
NEXT_GATE = "gate_3_1_extended_lane_inventory_and_classification"
R1_TERMINAL = "86cd484c8d09a14291da6a1226ecf24030d29caf"
R1_SOURCE = "ec204d63e431d10501c67db0264082db6e4d31e4"
HISTORICAL_C3 = "4aec510409e8bb82386190af9fa8f666efcbc63e"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
GATE_3_9_RECEIPT = "docs/architecture/evidence/campaign-3-gate-3-9-all-lane-r1-receipt-813912ce.json"
GATE_3_9_SIDECAR = GATE_3_9_RECEIPT.removesuffix(".json") + ".sha256"

ALL_GATES = [
    GATE_3_0,
    NEXT_GATE,
    "gate_3_2_scout_and_coding_research_integration",
    "gate_3_3_obsidian_coding_knowledge_integration",
    "gate_3_4_mac_worker_and_mac_coding_frameworks",
    "gate_3_5_retained_coding_sub_agents",
    "gate_3_6_cross_lane_conflict_resolution",
    "gate_3_7_extended_observability_and_diagnosis_backend",
    "gate_3_8_degradation_fallback_and_resumability",
    "gate_3_9_genuine_all_lane_proving_task",
    "gate_3_10_coding_ui_campaign_readiness",
    "gate_3_11_final_acceptance_and_closeout",
]

PROTECTED_REFS = {
    "source_proxy": ("refs/heads/codex/source-proxy-structural-milestone-20260711", "594d66ef8280953af767a273d7c91be765d1a6eb"),
    "spiritflix": ("refs/heads/codex/spiritflix-smart-scan-identity-fix", "5fde4ae064d471e1133e00d6bf25fb5aecb5d196"),
    "architecture_audit": ("refs/heads/codex/spiritos-architecture-audit-20260712", "05612d2ae358bc01b6ef997243137649f8d65f14"),
    "campaign_1_historical_terminal": ("refs/heads/codex/spiritos-campaign-1-foundation-20260712", "8a20473c2260bc132e595c64230d3fdfc9fef97f"),
    "campaign_2_historical_engineering_terminal": ("refs/heads/codex/spiritos-campaign-2-core-coding-os-20260716", "2b8ead66578d7f7053c01cb987e011b763c1c03d"),
    "historical_design_campaign_3": ("refs/heads/codex/spiritos-campaign-3-core-design-lane-20260717", HISTORICAL_C3),
    "foundation_remediation_r1_terminal": ("refs/heads/codex/spiritos-foundation-remediation-r1-20260717", R1_TERMINAL),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, f"json_unreadable:{path.as_posix()}:{error}"
    if not isinstance(data, dict):
        return None, f"json_not_object:{path.as_posix()}"
    return data, None


def state(root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    data, error = load_json(root / "docs/architecture/campaign-3-state.json")
    return data, [error] if error else []


def read_text(root: Path, rel: str) -> str:
    try:
        return (root / rel).read_text(encoding="utf-8")
    except OSError:
        return ""


def git(root: Path, *args: str) -> tuple[int, str]:
    completed = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=False)
    return completed.returncode, completed.stdout.strip()


def validate_continuity(root: Path) -> list[str]:
    data, failures = state(root)
    if failures or data is None:
        return failures
    for rel in (
        data.get("goal_path"),
        data.get("plan_path"),
        data.get("ledger_path"),
        data.get("lane_inventory_path"),
        data.get("decommission_registry_path"),
        data.get("evidence_index_path"),
        data.get("test_profiles_path"),
        data.get("campaign4_stub_path"),
    ):
        if not isinstance(rel, str) or not (root / rel).exists():
            failures.append(f"missing_control_plane_path:{rel}")
    if data.get("schema") != EXPECTED_SCHEMA:
        failures.append("state_schema_mismatch")
    if data.get("campaign_id") != CAMPAIGN_ID:
        failures.append("campaign_id_mismatch")
    if data.get("gate_dependency_order") != ALL_GATES:
        failures.append("gate_dependency_order_mismatch")
    completed = data.get("completed_gate_ids")
    if not isinstance(completed, list) or completed != ALL_GATES[: len(completed)]:
        failures.append("completed_gates_not_dependency_prefix")
    if data.get("partial_gate_ids") != []:
        failures.append("partial_gates_present")
    expected_next = ALL_GATES[len(completed)] if len(completed) < len(ALL_GATES) else "none"
    if data.get("next_gate_id") != expected_next:
        failures.append("next_gate_mismatch")
    if data.get("go_eligible") is not False or data.get("campaign4_started") is not False:
        failures.append("premature_go_or_campaign4")
    if data.get("base", {}).get("accepted_closeout_commit") != R1_TERMINAL:
        failures.append("r1_terminal_commit_mismatch")
    if data.get("base", {}).get("source_implementation_commit") != R1_SOURCE:
        failures.append("r1_source_commit_mismatch")
    rc, head = git(root, "rev-parse", "HEAD")
    if rc != 0 or not HEX40.fullmatch(head):
        failures.append("git_head_unreadable")
    # Gate commits are allowed after the control-plane commit, but every one
    # must remain on the accepted R1 terminal lineage rather than a mutable or
    # historical-design branch.
    rc, _ = git(root, "merge-base", "--is-ancestor", R1_TERMINAL, "HEAD")
    if rc != 0:
        failures.append("git_r1_terminal_not_ancestor")
    rc, _ = git(root, "merge-base", "--is-ancestor", R1_SOURCE, "HEAD")
    if rc != 0:
        failures.append("git_r1_source_not_ancestor")
    ledger = read_text(root, "docs/architecture/campaign-3-ledger.md")
    if ledger.count("## Current Checkpoint") != 1:
        failures.append("ledger_current_checkpoint_count_invalid")
    if expected_next not in ledger:
        failures.append("ledger_next_gate_missing")
    return failures


def validate_authority(root: Path) -> list[str]:
    data, failures = state(root)
    if failures or data is None:
        return failures
    exclusions = data.get("exclusions") if isinstance(data.get("exclusions"), dict) else {}
    for key in ("designer_implementation", "coding_ui_wiring", "coder_10_execution", "campaign_4_started", "push_performed"):
        if exclusions.get(key) is not False:
            failures.append(f"exclusion_not_false:{key}")
    combined = "\n".join([
        read_text(root, "docs/architecture/campaign-3-goal.md"),
        read_text(root, "docs/architecture/campaign-3-plan.md"),
        read_text(root, "docs/architecture/campaign-3-ledger.md"),
    ])
    for phrase in (
        "Campaign 3 extends R1. It does not replace it.",
        "They may not create parallel",
        "Every mutation-capable extended lane must use",
        "Do not fully wire the UI yet.",
    ):
        if phrase not in combined:
            failures.append(f"authority_phrase_missing:{phrase}")
    protected = data.get("protected_refs") if isinstance(data.get("protected_refs"), dict) else {}
    for key, (ref, expected) in PROTECTED_REFS.items():
        record = protected.get(key) if isinstance(protected.get(key), dict) else {}
        if record.get("ref") != ref or record.get("commit") != expected:
            failures.append(f"protected_ref_state_mismatch:{key}")
        rc, actual = git(root, "rev-parse", ref)
        if rc == 0 and key != "campaign_2_historical_engineering_terminal" and actual != expected:
            failures.append(f"protected_ref_git_drift:{key}")
    if data.get("terminal_verdict_token") != TERMINAL_VERDICT:
        failures.append("terminal_verdict_token_mismatch")
    return failures


def validate_lane_registry(root: Path) -> list[str]:
    inventory = read_text(root, "docs/architecture/campaign-3-lane-inventory.md")
    decommission = read_text(root, "docs/architecture/campaign-3-decommission-registry.md")
    failures: list[str] = []
    for lane in (
        "extended.scout-research",
        "extended.searxng-provider",
        "extended.web-fetch-docs",
        "extended.obsidian-knowledge",
        "extended.mac-worker",
        "extended.context-model",
        "extended.retained-sub-agent",
        "extended.platform-verifier",
        "extended.conflict-resolver",
        "extended.diagnosis-envelope",
        "extended.failure-injection",
    ):
        if lane not in inventory:
            failures.append(f"lane_missing:{lane}")
    for field in ("input schema", "output schema", "failure schema", "timeout", "retry", "fallback", "acknowledgement", "evidence"):
        if field not in inventory:
            failures.append(f"lane_required_field_missing:{field}")
    for rel in (
        "source_proxy/coding/extended_lane_registry.py",
        "source_proxy/tests/test_extended_lane_registry.py",
        "packages/contracts/schemas/coding/extended-lane-contracts.v1.json",
    ):
        if not (root / rel).exists():
            failures.append(f"extended_lane_runtime_path_missing:{rel}")
    registry_source = read_text(root, "source_proxy/coding/extended_lane_registry.py")
    for lane in (
        "extended.scout-research",
        "extended.obsidian-knowledge",
        "extended.mac-worker",
        "extended.retained-sub-agent",
        "extended.conflict-resolver",
        "extended.diagnosis-envelope",
    ):
        if lane not in registry_source:
            failures.append(f"runtime_lane_missing:{lane}")
    if "nonselectable_extended_lane" not in registry_source:
        failures.append("nonselectable_lane_rejection_missing")
    for phrase in ("Historical design Campaign 3", "preview-only", "SearXNG standalone authority", "Full `/coding` UI wiring", "CAMPAIGN_3_SCOPE_DIVERGED_TO_DESIGN"):
        if phrase not in decommission:
            failures.append(f"decommission_entry_missing:{phrase}")
    return failures


def gate_3_9_evidence_failures(root: Path) -> list[str]:
    """Validate the immutable all-lane lifecycle receipt before state may claim Gate 3.9."""
    receipt_path = root / GATE_3_9_RECEIPT
    sidecar_path = root / GATE_3_9_SIDECAR
    data, error = load_json(receipt_path)
    failures = ["gate_3_9_receipt_unreadable"] if error or data is None else []
    if failures:
        return failures
    digest = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    try:
        sidecar = sidecar_path.read_text(encoding="utf-8").split()[0]
    except OSError:
        return ["gate_3_9_receipt_sidecar_missing"]
    if sidecar != digest:
        failures.append("gate_3_9_receipt_hash_mismatch")
    if data.get("status") != "passed" or data.get("terminal_proof_eligible") is not False:
        failures.append("gate_3_9_lifecycle_status_invalid")
    source = data.get("source") if isinstance(data.get("source"), dict) else {}
    if source.get("source_head") != "813912cef6ace07fcd170f519d518bd755c9d9f8":
        failures.append("gate_3_9_receipt_source_binding_invalid")
    teardown = data.get("teardown") if isinstance(data.get("teardown"), dict) else {}
    for key in ("all_services_stopped", "operator_session_revoked", "tracked_status_clean", "ignored_status_restored"):
        if teardown.get(key) is not True:
            failures.append(f"gate_3_9_teardown_missing:{key}")
    inner = data.get("inner_proving") if isinstance(data.get("inner_proving"), dict) else {}
    runs = inner.get("runs") if isinstance(inner.get("runs"), list) else []
    if len(runs) != 2 or not isinstance(runs[0], dict) or not isinstance(runs[1], dict):
        failures.append("gate_3_9_runs_invalid")
        return failures
    first, second = runs
    lanes = first.get("extended_lanes") if isinstance(first.get("extended_lanes"), dict) else {}
    if lanes.get("all_required_live") is not True:
        failures.append("gate_3_9_required_lanes_not_live")
    recoveries = lanes.get("controlled_failures") if isinstance(lanes.get("controlled_failures"), list) else []
    if len(recoveries) < 2 or not any(isinstance(item, dict) and item.get("external_host_failure") is True for item in recoveries):
        failures.append("gate_3_9_controlled_recovery_invalid")
    if first.get("production_proof", {}).get("terminal_proof_eligible") is not True:
        failures.append("gate_3_9_production_proof_missing")
    if second.get("clean_rerun") is not True or inner.get("clean_rerun", {}).get("completed") is not True:
        failures.append("gate_3_9_clean_rerun_missing")
    return failures


def validate_participation(root: Path) -> list[str]:
    data, failures = state(root)
    if failures or data is None:
        return failures
    completed = data.get("completed_gate_ids") if isinstance(data.get("completed_gate_ids"), list) else []
    proving = data.get("proving_task") if isinstance(data.get("proving_task"), dict) else {}
    lane_req = data.get("lane_consumption_requirements") if isinstance(data.get("lane_consumption_requirements"), dict) else {}
    controlled = data.get("controlled_failure_requirements") if isinstance(data.get("controlled_failure_requirements"), dict) else {}
    if "gate_3_9_genuine_all_lane_proving_task" not in completed:
        for key, value in proving.items():
            if value is not False:
                failures.append(f"proving_task_claimed_too_early:{key}")
        if lane_req.get("all_retained_mandatory_outputs_consumed") is not False or lane_req.get("all_consumption_acknowledged") is not False:
            failures.append("lane_consumption_claimed_too_early")
        if controlled.get("proven_failures") != []:
            failures.append("controlled_failures_claimed_too_early")
        return failures
    if not all(value is True for value in proving.values()):
        failures.append("gate_3_9_proving_state_incomplete")
    if lane_req.get("all_retained_mandatory_outputs_consumed") is not True or lane_req.get("all_consumption_acknowledged") is not True:
        failures.append("gate_3_9_consumption_state_incomplete")
    if not isinstance(controlled.get("proven_failures"), list) or len(controlled["proven_failures"]) < 2:
        failures.append("gate_3_9_controlled_failure_state_incomplete")
    failures.extend(gate_3_9_evidence_failures(root))
    return failures


def validate_evidence(root: Path) -> list[str]:
    data, failures = state(root)
    if failures or data is None:
        return failures
    evidence = read_text(root, "docs/architecture/campaign-3-evidence-index.md")
    for phrase in ("R1 terminal tag peel", "R1 bundle verification", "Shared Git integrity", "Later Evidence Requirements"):
        if phrase not in evidence:
            failures.append(f"evidence_index_missing:{phrase}")
    immutable = data.get("immutable_evidence_requirements") if isinstance(data.get("immutable_evidence_requirements"), dict) else {}
    for key in ("source_bound_receipt_required", "manifest_required", "hashes_required", "terminal_tag_required", "bundle_required"):
        if immutable.get(key) is not True:
            failures.append(f"immutable_requirement_not_true:{key}")
    completed = data.get("completed_gate_ids") if isinstance(data.get("completed_gate_ids"), list) else []
    if "gate_3_11_final_acceptance_and_closeout" in completed:
        if immutable.get("current_terminal_evidence_complete") is not True:
            failures.append("terminal_evidence_incomplete")
    elif immutable.get("current_terminal_evidence_complete") is not False:
        failures.append("terminal_evidence_claimed_too_early")
    entry = data.get("entry_checks") if isinstance(data.get("entry_checks"), dict) else {}
    for key in ("r1_terminal_tag_verified", "r1_terminal_commit_verified", "r1_bundle_verified", "protected_refs_verified", "historical_design_c3_preserved"):
        if entry.get(key) is not True:
            failures.append(f"entry_check_not_true:{key}")
    return failures


def validate_test_profiles(root: Path) -> list[str]:
    data, error = load_json(root / "docs/architecture/campaign-3-test-profiles.json")
    failures = [error] if error else []
    if data is None:
        return failures
    if data.get("schema") != EXPECTED_TEST_SCHEMA or data.get("campaign_id") != CAMPAIGN_ID:
        failures.append("test_profile_identity_invalid")
    profiles = data.get("profiles")
    if not isinstance(profiles, list) or len(profiles) < 7:
        return failures + ["profiles_missing"]
    commands = set()
    ids = set()
    for profile in profiles:
        if not isinstance(profile, dict):
            failures.append("profile_not_object")
            continue
        pid = profile.get("id")
        if not isinstance(pid, str) or pid in ids:
            failures.append(f"profile_id_invalid_or_duplicate:{pid}")
        ids.add(str(pid))
        if profile.get("mandatory") is not True or profile.get("status") != "passed":
            failures.append(f"profile_not_currently_passed_mandatory:{pid}")
        if not isinstance(profile.get("claim_ceiling"), str):
            failures.append(f"profile_claim_ceiling_missing:{pid}")
        if isinstance(profile.get("command"), str):
            commands.add(profile["command"])
    for command in (
        "python3 ./scripts/validate-campaign-3-continuity.py",
        "python3 ./scripts/validate-campaign-3-authority.py",
        "python3 ./scripts/validate-campaign-3-lane-registry.py",
        "python3 ./scripts/validate-campaign-3-participation.py",
        "python3 ./scripts/validate-campaign-3-evidence.py",
        "python3 ./scripts/validate-campaign-3-test-profiles.py",
        "python3 ./scripts/test-campaign-3-completion.py",
    ):
        if command not in commands:
            failures.append(f"profile_command_missing:{command}")
    return failures


def current_validator_failures(root: Path) -> list[str]:
    failures: list[str] = []
    for name, validator in (
        ("continuity", validate_continuity),
        ("authority", validate_authority),
        ("lane-registry", validate_lane_registry),
        ("participation", validate_participation),
        ("evidence", validate_evidence),
        ("test-profiles", validate_test_profiles),
    ):
        failures.extend(f"{name}:{failure}" for failure in validator(root))
    return failures


def completion_failures(root: Path, override: dict[str, Any] | None = None) -> list[str]:
    data, failures = state(root)
    if failures or data is None:
        return failures
    data = copy.deepcopy(override if override is not None else data)
    if data.get("schema") != EXPECTED_SCHEMA:
        failures.append("unsupported_state_schema")
    if data.get("campaign_id") != CAMPAIGN_ID:
        failures.append("campaign_id_mismatch")
    if data.get("go_eligible") is not True:
        failures.append("go_not_true")
    if data.get("completed_gate_ids") != ALL_GATES:
        failures.append("mandatory_gates_missing")
    if data.get("partial_gate_ids") != []:
        failures.append("partial_gates_present")
    if data.get("next_gate_id") not in {"none", "gate_3_complete"}:
        failures.append("next_gate_not_terminal")
    proving = data.get("proving_task") if isinstance(data.get("proving_task"), dict) else {}
    for key in ("selected", "clean_isolated_baseline", "real_lane_invocation", "real_output_consumption", "model_authored_non_empty_diff", "authenticated_approval", "canonical_apply", "independent_review", "independent_verification", "anti_cheat", "immutable_evidence", "undo_reset", "clean_rerun"):
        if proving.get(key) is not True:
            failures.append(f"proving_task_missing:{key}")
    proven = data.get("controlled_failure_requirements", {}).get("proven_failures")
    if not isinstance(proven, list) or len(proven) < 2:
        failures.append("controlled_failures_missing")
    elif not any(isinstance(item, dict) and item.get("external_host_failure") is True for item in proven):
        failures.append("external_host_failure_missing")
    if data.get("immutable_evidence_requirements", {}).get("current_terminal_evidence_complete") is not True:
        failures.append("immutable_evidence_incomplete")
    lane_req = data.get("lane_consumption_requirements") if isinstance(data.get("lane_consumption_requirements"), dict) else {}
    if lane_req.get("all_retained_mandatory_outputs_consumed") is not True:
        failures.append("lane_consumption_missing")
    if lane_req.get("all_consumption_acknowledged") is not True:
        failures.append("lane_acknowledgement_missing")
    if data.get("base", {}).get("accepted_closeout_commit") == HISTORICAL_C3:
        failures.append("historical_design_c3_cannot_satisfy_corrected_c3")
    if override is None:
        failures.extend(current_validator_failures(root))
    return sorted(set(failures))


def terminal_fixture(root: Path) -> dict[str, Any]:
    data, failures = state(root)
    if failures or data is None:
        raise RuntimeError(",".join(failures))
    fixture = copy.deepcopy(data)
    fixture["completed_gate_ids"] = list(ALL_GATES)
    fixture["next_gate_id"] = "none"
    fixture["go_eligible"] = True
    for key in fixture["proving_task"]:
        fixture["proving_task"][key] = True
    fixture["controlled_failure_requirements"]["proven_failures"] = [
        {"lane_id": "extended.scout-research", "recovered": True, "external_host_failure": False},
        {"lane_id": "extended.mac-worker", "recovered": True, "external_host_failure": True},
    ]
    fixture["immutable_evidence_requirements"]["current_terminal_evidence_complete"] = True
    fixture["lane_consumption_requirements"]["all_retained_mandatory_outputs_consumed"] = True
    fixture["lane_consumption_requirements"]["all_consumption_acknowledged"] = True
    return fixture


def command_main(kind: str) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=repo_root())
    args = parser.parse_args()
    validators = {
        "continuity": validate_continuity,
        "authority": validate_authority,
        "lane-registry": validate_lane_registry,
        "participation": validate_participation,
        "evidence": validate_evidence,
        "test-profiles": validate_test_profiles,
    }
    failures = validators[kind](args.root.resolve())
    label = kind.upper().replace("-", "_")
    if failures:
        print(f"CAMPAIGN_3_{label}_INVALID " + ",".join(failures))
        return 1
    print(f"CAMPAIGN_3_{label}_VALID")
    return 0


def completion_main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=repo_root())
    args = parser.parse_args()
    failures = completion_failures(args.root.resolve())
    if failures:
        print(NOT_COMPLETE)
        print(",".join(failures))
        return 1
    print(TERMINAL_VERDICT)
    return 0
