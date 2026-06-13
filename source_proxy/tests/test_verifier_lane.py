from __future__ import annotations

from source_proxy.decision.verifier_lane import (
    build_verifier_lane_packet,
    normalize_verifier_lane_output,
    verifier_lane_preview,
)


def _contract() -> dict:
    return {
        "behavior_required": True,
        "probe_targets": [{"probe_id": "calculator-basic-arithmetic"}],
    }


def test_verifier_packet_is_advisory_and_contains_required_refs() -> None:
    packet = build_verifier_lane_packet(
        original_user_prompt="make a calculator",
        normalized_intent="disposable calculator artifact",
        behavior_contract=_contract(),
        task_spec={"task_type": "create_file_bundle"},
        planner_criteria=[{"criterion_id": "calculator-basic-arithmetic"}],
        selected_coder_lane="qwen_local_coder",
        changed_files_summary=["index.html"],
        generated_preview_path="workspace/index.html",
        browser_observation={"passed": True},
        receipt_path="receipt.json",
        transcript_path="transcript.txt",
        workspace_diff_path="workspace.diff",
        behavior_probe_evidence={"verdict": "PASS", "probe_id": "calculator-basic-arithmetic"},
        repair_packet={"status": "READY_FOR_LOCAL_REPAIR"},
        repair_result={"status": "READY_FOR_RETEST"},
        retest_result_path="retest-result.json",
    )

    assert packet["preview_only"] is True
    assert packet["advisory_only"] is True
    assert packet["model_calls_enabled"] is False
    assert packet["selected_coder_lane"] == "qwen_local_coder"
    assert packet["task_spec"]["task_type"] == "create_file_bundle"
    assert packet["planner_criteria"][0]["criterion_id"] == "calculator-basic-arithmetic"
    assert packet["transcript_path"] == "transcript.txt"
    assert packet["workspace_diff_path"] == "workspace.diff"
    assert packet["behavior_probe_evidence"]["verdict"] == "PASS"
    assert "model_self_report" in packet["non_authoritative_signals"]


def test_verifier_output_cannot_inflate_pass_without_browser_evidence() -> None:
    output = normalize_verifier_lane_output(
        verifier_lane_id="hermes_sidecar_verifier_preview",
        proposed_verdict="PASS",
        evidence_refs=["receipt.json"],
        browser_behavior_passed=False,
    )

    assert output["verdict"] != "PASS"
    assert "pass_blocked_without_browser_behavior_evidence" in output["reasons"]
    assert output["cannot_turn_unverified_into_pass"] is True


def test_missing_evidence_downgrades_pass_to_warning_or_unverified() -> None:
    output = normalize_verifier_lane_output(
        verifier_lane_id="hermes_sidecar_verifier_preview",
        proposed_verdict="PASS",
        evidence_refs=["receipt.json"],
        missing_evidence=["browser_observation"],
        browser_behavior_passed=True,
    )

    assert output["verdict"] == "WARNING"
    assert "pass_downgraded_for_missing_evidence" in output["reasons"]


def test_verifier_preview_marks_missing_evidence_without_model_call() -> None:
    packet = build_verifier_lane_packet(
        original_user_prompt="make a tracker",
        normalized_intent="tracker",
        behavior_contract={},
    )

    output = verifier_lane_preview(packet)

    assert output["model_calls_enabled"] is False
    assert output["verdict"] in {"UNVERIFIED", "WARNING", "NEEDS_FIX"}
    assert "browser_observation" in output["missing_evidence"]
    assert "planner_criteria" in output["missing_evidence"]


def test_verifier_preview_blocks_failed_browser_behavior() -> None:
    packet = build_verifier_lane_packet(
        original_user_prompt="make a theme toggle",
        normalized_intent="theme toggle",
        task_spec={"task_type": "create_file_bundle"},
        planner_criteria=[{"criterion_id": "theme-computed-color-change"}],
        behavior_contract=_contract(),
        generated_preview_path="workspace/index.html",
        browser_observation={"verdict": "FAIL", "passed": False, "opened": True},
        receipt_path="receipt.json",
        transcript_path="transcript.txt",
        workspace_diff_path="workspace.diff",
        behavior_probe_evidence={"verdict": "FAIL", "actual": {"before": "white", "after": "white"}},
        retest_result_path="retest.json",
    )

    output = verifier_lane_preview(packet)

    assert output["verdict"] in {"NEEDS_FIX", "HANDOFF", "FAIL", "UNVERIFIED"}
    assert output["verdict"] != "PASS"
    assert "browser_behavior_failed" in output["reasons"]
    assert output["cannot_override_browser_behavior"] is True


def test_verifier_pass_proposal_is_needs_fix_when_browser_failed() -> None:
    output = normalize_verifier_lane_output(
        verifier_lane_id="hermes_sidecar_verifier_preview",
        proposed_verdict="PASS",
        evidence_refs=["receipt.json", "probe.json"],
        browser_behavior_passed=False,
    )

    assert output["verdict"] == "NEEDS_FIX"
    assert "failed_browser_behavior_blocks_pass" in output["reasons"]


def test_verifier_preview_reports_missing_receipt_transcript_diff_probe() -> None:
    packet = build_verifier_lane_packet(
        original_user_prompt="make a tracker",
        normalized_intent="tracker",
        task_spec={"task_type": "create_file_bundle"},
        planner_criteria=[{"criterion_id": "tracker-state-change"}],
        behavior_contract=_contract(),
        generated_preview_path="workspace/index.html",
        browser_observation={"opened": True},
    )

    output = verifier_lane_preview(packet)

    assert output["verdict"] != "PASS"
    assert "receipt_path" in output["missing_evidence"]
    assert "transcript_path" in output["missing_evidence"]
    assert "workspace_diff_path" in output["missing_evidence"]
    assert "behavior_probe_evidence" in output["missing_evidence"]
