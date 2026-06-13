from __future__ import annotations

from source_proxy.decision.artifact_behavior_contract import build_artifact_behavior_contract
from source_proxy.decision.artifact_final_verdict import (
    build_artifact_final_verdict_row,
    classify_artifact_score_integrity,
    classify_repair_failure_bucket,
    normalize_artifact_final_verdict,
)


def test_runtime_go_with_behavior_fail_becomes_fail() -> None:
    verdict = normalize_artifact_final_verdict(
        route_status="GO",
        artifact_ready=True,
        behavior_required=True,
        behavior_verdict="FAIL",
    )

    assert verdict["label"] == "FAIL"
    assert verdict["product_pass"] is False
    assert "behavior_failed" in verdict["reason_codes"]


def test_behavior_fail_removes_stale_unverified_reason() -> None:
    verdict = normalize_artifact_final_verdict(
        route_status="GO",
        artifact_ready=True,
        behavior_required=True,
        behavior_verdict="FAIL",
        reason_codes=["behavior_required_but_unverified", "behavior_probe_failed"],
    )

    assert verdict["label"] == "FAIL"
    assert "behavior_failed" in verdict["reason_codes"]
    assert "behavior_probe_failed" in verdict["reason_codes"]
    assert "behavior_required_but_unverified" not in verdict["reason_codes"]


def test_missing_artifact_fails_readiness_and_does_not_pass_behavior() -> None:
    verdict = normalize_artifact_final_verdict(
        route_status="GO",
        artifact_ready=False,
        behavior_required=True,
        behavior_verdict=None,
    )

    assert verdict["label"] == "FAIL"
    assert verdict["product_pass"] is False
    assert "artifact_readiness_failed" in verdict["reason_codes"]
    assert "behavior_unverified_without_ready_artifact" in verdict["reason_codes"]


def test_runtime_go_with_required_unverified_behavior_stays_unverified() -> None:
    verdict = normalize_artifact_final_verdict(
        route_status="GO",
        artifact_ready=True,
        behavior_required=True,
        behavior_verdict=None,
    )

    assert verdict["label"] == "UNVERIFIED"
    assert verdict["product_pass"] is False
    assert "behavior_required_but_unverified" in verdict["reason_codes"]


def test_behavior_pass_is_required_for_product_pass() -> None:
    verdict = normalize_artifact_final_verdict(
        route_status="GO",
        artifact_ready=True,
        behavior_required=True,
        behavior_verdict="PASS",
    )

    assert verdict["label"] == "PASS"
    assert verdict["product_pass"] is True
    assert "behavior_pass_verified" in verdict["reason_codes"]


def test_behavior_pass_removes_stale_unverified_reason() -> None:
    verdict = normalize_artifact_final_verdict(
        route_status="GO",
        artifact_ready=True,
        behavior_required=True,
        behavior_verdict="PASS",
        reason_codes=["behavior_required_but_unverified", "artifact_ready"],
    )

    assert verdict["label"] == "PASS"
    assert "behavior_pass_verified" in verdict["reason_codes"]
    assert "behavior_required_but_unverified" not in verdict["reason_codes"]


def test_handoff_overrides_local_success_signals() -> None:
    verdict = normalize_artifact_final_verdict(
        route_status="GO",
        artifact_ready=True,
        behavior_required=True,
        behavior_verdict="PASS",
        handoff_required=True,
    )

    assert verdict["label"] == "HANDOFF"
    assert verdict["product_pass"] is False
    assert "handoff_required" in verdict["reason_codes"]


def test_final_verdict_row_traces_planner_probe_repair_and_evidence_refs() -> None:
    contract = build_artifact_behavior_contract(
        prompt="make a calculator app",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )

    row = build_artifact_final_verdict_row(
        original_prompt="make a calculator app",
        normalized_intent="create static calculator UI",
        planner_criterion_id="criterion-calc-result",
        behavior_contract=contract,
        probe_result={
            "test": "calculator-basic-arithmetic",
            "verdict": "PASS",
            "actual": {"before": "0", "after": "5"},
        },
        selected_preview_path="workspace/index.html",
        route_status="GO",
        open_status="PASS",
        artifact_ready=True,
        repair_result={"status": "READY_FOR_RETEST", "attempts_used": 1, "reason_codes": ["repair_ready_for_retest"]},
        evidence_refs={"receipt": "receipt.json", "probe": "behavior.json"},
        anti_cheat_flags={"fallback_used": False},
    )

    assert row["original_prompt"] == "make a calculator app"
    assert row["normalized_intent"] == "create static calculator UI"
    assert row["planner_criterion_id"] == "criterion-calc-result"
    assert row["behavior_criterion_id"] == "criterion-calc-result"
    assert row["behavior_contract_id"] == contract["contract_version"]
    assert row["probe_id"] == "calculator-basic-arithmetic"
    assert row["selected_preview_path"] == "workspace/index.html"
    assert row["route_status"] == "GO"
    assert row["open_status"] == "PASS"
    assert row["observed_before"] == "0"
    assert row["observed_after"] == "5"
    assert row["repair_attempt_count"] == 1
    assert row["repair_status"] == "READY_FOR_RETEST"
    assert row["evidence_refs"]["probe"] == "behavior.json"
    assert row["anti_cheat_flags"]["fallback_used"] is False
    assert row["canonical_final_verdict"] == "PASS"
    assert row["product_pass"] is True
    assert "post_behavior_repair_pass" in row["final_reason_codes"]
    assert "repair_attempts_1" in row["final_reason_codes"]
    assert row["passed_stage"] == "passed_after_repair"


def test_final_verdict_row_route_and_open_only_cannot_pass() -> None:
    contract = build_artifact_behavior_contract(
        prompt="make a notes app",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )

    row = build_artifact_final_verdict_row(
        original_prompt="make a notes app",
        normalized_intent="create notes app",
        planner_criterion_id="criterion-note-visible",
        behavior_contract=contract,
        probe_result={"test": "notes-create-edit-visible-note", "verdict": "UNVERIFIED", "actual": {}},
        selected_preview_path="workspace/index.html",
        route_status="GO",
        open_status="PASS",
        artifact_ready=True,
    )

    assert row["canonical_final_verdict"] == "UNVERIFIED"
    assert row["product_pass"] is False
    assert "route_go_not_behavior_pass" in row["final_reason_codes"]
    assert "preview_open_not_behavior_pass" in row["final_reason_codes"]


def test_final_verdict_row_failed_browser_probe_stays_fail() -> None:
    contract = build_artifact_behavior_contract(
        prompt="make a theme toggle",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )

    row = build_artifact_final_verdict_row(
        original_prompt="make a theme toggle",
        normalized_intent="create theme toggle",
        planner_criterion_id="criterion-theme-computed",
        behavior_contract=contract,
        probe_result={
            "test": "theme-computed-color-change",
            "verdict": "FAIL",
            "actual": {"before": {"bg": "white"}, "after": {"bg": "white"}},
        },
        selected_preview_path="workspace/index.html",
        route_status="GO",
        open_status="PASS",
        artifact_ready=True,
        repair_result={"status": "HANDOFF", "handoff_required": True, "attempts_used": 1},
    )

    assert row["canonical_final_verdict"] == "HANDOFF"
    assert row["product_pass"] is False
    assert "behavior_failed_verified" in row["final_reason_codes"]
    assert "post_behavior_repair_failed" in row["final_reason_codes"]


def test_score_integrity_rejects_notes_saved_status_without_note_text() -> None:
    result = classify_artifact_score_integrity(
        prompt="make a quick jot pad app",
        open_status="PASS",
        behavior_probe={
            "verdict": "PASS",
            "passed": True,
            "actual": {
                "before": "Quick Jot Pad\nSave Note",
                "after": "Quick Jot Pad\nSave Note\n\nNote saved successfully.",
                "filled": 1,
                "clicked": True,
                "appears": False,
            },
        },
        raw_final_verdict="PASS",
    )

    assert result["strict_final_verdict"] == "FAIL"
    assert result["primary_behavior_failure_bucket"] == "notes_saved_status_without_note_text"
    assert result["score_integrity_failure"] is True
    assert result["classification"] == "false_positive_pass"


def test_score_integrity_allows_visible_note_text() -> None:
    result = classify_artifact_score_integrity(
        prompt="make a pocket memo board app",
        open_status="PASS",
        behavior_probe={"verdict": "PASS", "passed": True, "actual": {"appears": True}},
        raw_final_verdict="PASS",
    )

    assert result["strict_final_verdict"] == "PASS"
    assert result["score_integrity_failure"] is False


def test_score_integrity_rejects_checklist_status_without_item_text() -> None:
    result = classify_artifact_score_integrity(
        prompt="make a camping packing list app",
        open_status="PASS",
        behavior_probe={"verdict": "PASS", "passed": True, "actual": {"after": "Saved", "appears": False}},
        raw_final_verdict="PASS",
    )

    assert result["strict_final_verdict"] == "FAIL"
    assert result["primary_behavior_failure_bucket"] == "checklist_status_without_item_text"


def test_score_integrity_allows_calculator_result_without_entered_text_echo() -> None:
    result = classify_artifact_score_integrity(
        prompt="make a pizza money splitter",
        open_status="PASS",
        behavior_probe={
            "verdict": "PASS",
            "passed": True,
            "actual": {"before": "Pizza Splitter", "after": "Pizza Splitter\nTotal per person: 21.00", "appears": False},
        },
        raw_final_verdict="PASS",
    )

    assert result["strict_final_verdict"] == "PASS"


def test_score_integrity_timer_start_must_change_before_stop() -> None:
    result = classify_artifact_score_integrity(
        prompt="build me a snack break countdown",
        open_status="PASS",
        behavior_probe={
            "verdict": "FAIL",
            "passed": False,
            "actual": {"before": "25:00", "afterStart": "25:00", "afterStop": "24:59"},
        },
        raw_final_verdict="FAIL",
    )

    assert result["strict_final_verdict"] == "FAIL"
    assert result["primary_behavior_failure_bucket"] == "timer_no_visible_change_after_start"
    assert result["secondary_behavior_failure_bucket"] == "timer_state_changed_after_wrong_action"


def test_score_integrity_preview_fail_gets_route_or_theme_bucket() -> None:
    result = classify_artifact_score_integrity(
        prompt="make a day night color flipper",
        route_status="EXPECTED-BLOCKED",
        open_status="FAIL",
        behavior_probe={"verdict": "FAIL", "passed": False, "actual": {}},
        raw_final_verdict="FAIL",
    )

    assert result["strict_final_verdict"] == "FAIL"
    assert result["primary_behavior_failure_bucket"] == "route_blocked_no_preview"


def test_score_integrity_password_text_must_change() -> None:
    result = classify_artifact_score_integrity(
        prompt="make a login safety gauge",
        open_status="PASS",
        behavior_probe={
            "verdict": "FAIL",
            "passed": False,
            "actual": {"weak": "Password", "strong": "Password", "changed": False},
        },
        raw_final_verdict="FAIL",
    )

    assert result["primary_behavior_failure_bucket"] == "password_no_visible_strength_text_change"


def test_score_integrity_drawing_requires_pixel_change() -> None:
    result = classify_artifact_score_integrity(
        prompt="make a scribble sketch pad",
        open_status="PASS",
        behavior_probe={"verdict": "FAIL", "passed": False, "actual": {"canvas": True, "changed": False}},
        raw_final_verdict="FAIL",
    )

    assert result["primary_behavior_failure_bucket"] == "drawing_canvas_no_pixel_change"


def test_repair_failure_bucket_preserves_free_floating_code_bucket() -> None:
    bucket = classify_repair_failure_bucket(
        {
            "status": "HANDOFF",
            "attempts_used": 1,
            "reason_codes": ["free_floating_code_no_path_action", "attempts_exhausted"],
        }
    )

    assert bucket == "repair_free_floating_code_no_path_action"
