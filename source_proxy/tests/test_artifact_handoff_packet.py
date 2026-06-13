from __future__ import annotations

from source_proxy.decision.artifact_behavior_contract import build_artifact_behavior_contract
from source_proxy.decision.artifact_handoff_packet import build_artifact_handoff_packet


def _contract() -> dict:
    return build_artifact_behavior_contract(
        prompt="make a calculator app",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )


def _failure(**overrides: object) -> dict:
    packet = {
        "status": "READY_FOR_LOCAL_REPAIR",
        "handoff_reasons": [],
        "artifact_paths": ["Z:/tmp/workspace/index.html"],
        "allowed_workspace": "Z:/tmp/workspace",
        "expected_behavior": {"probe_id": "calculator-basic-arithmetic"},
        "observed_behavior": {"verdict": "FAIL", "observed": {"display": "0"}},
        "reason_codes": ["behavior_probe_failed:calculator-basic-arithmetic"],
        "evidence_refs": {"receipt_path": "runs/receipt.json", "diff_path": "runs/workspace.diff"},
    }
    packet.update(overrides)
    return packet


def _repair(**overrides: object) -> dict:
    packet = {
        "status": "HANDOFF",
        "handoff_reason": "repair_attempts_exhausted",
        "attempts_used": 1,
        "changed_files": ["index.html"],
        "diffs": ["diff"],
        "reason_codes": ["repair_attempts_exhausted"],
    }
    packet.update(overrides)
    return packet


def _retest(**overrides: object) -> dict:
    packet = {
        "canonical_final_verdict": "FAIL",
        "product_pass": False,
        "artifact_ready": True,
        "behavior_result": {"verdict": "FAIL", "observed": {"display": "0"}},
        "final_reason_codes": ["behavior_failed"],
        "changed_files": ["index.html"],
        "diffs": ["diff"],
    }
    packet.update(overrides)
    return packet


def test_handoff_packet_for_failed_repair_is_copy_paste_useful() -> None:
    packet = build_artifact_handoff_packet(
        prompt="make a calculator app",
        behavior_contract=_contract(),
        failure_packet=_failure(),
        repair_result=_repair(),
        retest_result=_retest(),
    )

    assert packet["status"] == "HANDOFF"
    assert packet["final_verdict"] == "FAIL"
    assert packet["approval_needed"]["type"] == "stronger_repair_route_approval"
    assert packet["repair_summary"]["attempts_used"] == 1
    assert packet["evidence_refs"]["receipt_path"] == "runs/receipt.json"
    assert "No automatic escalation" in packet["operator_message"]
    assert packet["safety"]["automatic_escalation_performed"] is False


def test_handoff_packet_for_no_artifact_requests_regeneration_or_rerun_approval() -> None:
    packet = build_artifact_handoff_packet(
        prompt="make a drawing pad",
        behavior_contract=_contract(),
        failure_packet=_failure(
            status="HANDOFF",
            handoff_reasons=["artifact_path_missing"],
            artifact_paths=[],
            reason_codes=["artifact_or_preview_missing"],
        ),
    )

    assert packet["handoff_reason"] == "artifact_path_missing"
    assert packet["approval_needed"]["type"] == "artifact_generation_or_rerun_approval"
    assert packet["next_recommended_route"] == "approved disposable artifact regeneration or diagnostic rerun"


def test_handoff_packet_for_production_file_requirement_needs_scope_approval() -> None:
    packet = build_artifact_handoff_packet(
        prompt="fix the real production route",
        behavior_contract=_contract(),
        failure_packet=_failure(
            status="HANDOFF",
            handoff_reasons=["artifact_path_outside_allowed_workspace"],
            artifact_paths=["Z:/source_proxy/decision/human_messy_homepage.py"],
        ),
    )

    assert packet["approval_needed"]["type"] == "production_or_path_scope_approval"
    assert packet["safety"]["production_repair_performed"] is False


def test_handoff_packet_for_provider_needed_task_needs_provider_approval() -> None:
    packet = build_artifact_handoff_packet(
        prompt="make a weather card using a live weather API",
        behavior_contract=_contract(),
        reason="provider_api_required",
    )

    assert packet["handoff_reason"] == "provider_api_required"
    assert packet["approval_needed"]["type"] == "provider_api_approval"
    assert packet["safety"]["provider_api_used"] is False


def test_handoff_packet_for_local_worker_unavailable_needs_recovery_approval() -> None:
    packet = build_artifact_handoff_packet(
        prompt="make a calculator app",
        behavior_contract=_contract(),
        failure_packet=_failure(),
        repair_result=_repair(handoff_reason="repair_worker_failed", reason_codes=["repair_worker_failed"]),
    )

    assert packet["handoff_reason"] == "repair_worker_failed"
    assert packet["approval_needed"]["type"] == "local_worker_recovery_approval"
    assert "no worker was started automatically" in packet["approval_needed"]["description"].lower()


def test_unclear_handoff_reason_becomes_blocked_operator_review() -> None:
    packet = build_artifact_handoff_packet(
        prompt="make a tiny app",
        behavior_contract=_contract(),
    )

    assert packet["handoff_reason"] == "handoff_reason_unclear"
    assert packet["final_verdict"] == "HANDOFF"
    assert packet["approval_needed"]["type"] == "operator_review"
