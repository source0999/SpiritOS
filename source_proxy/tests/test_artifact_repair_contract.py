from __future__ import annotations

from source_proxy.decision.artifact_behavior_contract import build_artifact_behavior_contract
from source_proxy.decision.artifact_repair_contract import (
    build_artifact_failure_packet,
    build_behavior_failure_packet,
    build_repair_prompt_from_failure_packet,
)


WORKSPACE = "Z:/docs/evidence/source-proxy-general-intelligence-diagnostic-revamped-20260612/runs/03-make-a-calculator-app/workspace"


def test_failure_packet_for_calculator_contains_bounded_repair_evidence_without_solution() -> None:
    contract = build_artifact_behavior_contract(
        prompt="make a calculator app",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )
    packet = build_artifact_failure_packet(
        prompt="make a calculator app",
        behavior_contract=contract,
        verifier_result={
            "path": f"{WORKSPACE}/index.html",
            "test": "click 2 + 3 =",
            "observed": {"display": "0"},
            "verdict": "FAIL",
            "reason": "display did not equal 5",
        },
        evidence_packet={
            "evidence_packet_path": "docs/evidence/source-proxy-general-intelligence-diagnostic-revamped-20260612/runs/03/evidence-packet.json",
            "receipt_path": "docs/evidence/source-proxy-general-intelligence-diagnostic-revamped-20260612/runs/03/receipt.json",
            "source_proxy_score_status": "GO",
        },
        allowed_workspace=WORKSPACE,
    )
    prompt = build_repair_prompt_from_failure_packet(packet)

    assert packet["status"] == "READY_FOR_LOCAL_REPAIR"
    assert packet["handoff_required"] is False
    assert packet["expected_behavior"]["probe_id"] == "calculator-basic-arithmetic"
    assert packet["observed_behavior"]["observed"] == {"display": "0"}
    assert "route_go_not_behavior_pass" in packet["reason_codes"]
    assert "source_proxy/**" in packet["forbidden_paths"]
    assert "src/**" in packet["forbidden_paths"]
    assert "The calculator displays 5 for 2 + 3." in prompt
    assert "<!doctype html" not in prompt.lower()
    assert "function calculate" not in prompt


def test_failure_packets_cover_theme_habit_and_notes_shapes() -> None:
    cases = [
        (
            "make dark theme switcher page",
            "theme-computed-color-change",
            {"before": {"bg": "rgb(51, 51, 51)"}, "after": {"bg": "rgb(51, 51, 51)"}},
            "computed colors did not change",
        ),
        (
            "make a habit tracker",
            "habit-state-change",
            {"inputs": 0, "buttons": 0, "checkboxes": 0},
            "static hard-coded habits, no controls",
        ),
        (
            "make a notes app",
            "notes-create-edit-visible-note",
            {"artifact_type": "markdown_document"},
            "notes app generated markdown only instead of an app",
        ),
    ]

    for prompt, probe_id, observed, reason in cases:
        contract = build_artifact_behavior_contract(
            prompt=prompt,
            artifact_class="static_ui_artifact",
            task_shape="disposable_small_file_bundle",
        )
        packet = build_artifact_failure_packet(
            prompt=prompt,
            behavior_contract=contract,
            verifier_result={
                "path": f"{WORKSPACE}/index.html",
                "test": "behavior check",
                "observed": observed,
                "verdict": "FAIL",
                "reason": reason,
            },
            evidence_packet={"source_proxy_score_status": "GO"},
            allowed_workspace=WORKSPACE,
        )

        assert packet["expected_behavior"]["probe_id"] == probe_id
        assert packet["status"] == "READY_FOR_LOCAL_REPAIR"
        assert packet["repair_scope"]["production_paths_allowed"] is False


def test_failure_packet_handoff_for_missing_or_unsafe_evidence() -> None:
    contract = build_artifact_behavior_contract(
        prompt="make a password strength checker",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )
    packet = build_artifact_failure_packet(
        prompt="make a password strength checker",
        behavior_contract=contract,
        verifier_result={
            "path": "Z:/source_proxy/decision/human_messy_homepage.py",
            "test": "missing artifact",
            "observed": {},
            "verdict": "FAIL",
            "reason": "no artifact files",
        },
        evidence_packet=None,
        allowed_workspace=WORKSPACE,
    )
    prompt = build_repair_prompt_from_failure_packet(packet)

    assert packet["status"] == "HANDOFF"
    assert packet["handoff_required"] is True
    assert "artifact_path_outside_allowed_workspace" in packet["handoff_reasons"]
    assert "evidence_packet_missing" in packet["handoff_reasons"]
    assert "Do not attempt local repair" in prompt


def test_failure_packet_handoff_for_missing_preview_artifact() -> None:
    contract = build_artifact_behavior_contract(
        prompt="make a simple drawing pad",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )
    packet = build_artifact_failure_packet(
        prompt="make a simple drawing pad",
        behavior_contract=contract,
        verifier_result={
            "path": "",
            "test": "artifact readiness",
            "observed": {"files": []},
            "verdict": "FAIL",
            "reason": "no preview artifact",
        },
        evidence_packet={"source_proxy_score_status": "EXPECTED-BLOCKED"},
        allowed_workspace=WORKSPACE,
    )

    assert packet["status"] == "HANDOFF"
    assert "artifact_path_missing" in packet["handoff_reasons"]
    assert packet["expected_behavior"]["probe_id"] == "drawing-surface-changes"


def test_behavior_failure_packet_includes_structured_weather_delta() -> None:
    contract = build_artifact_behavior_contract(
        prompt="make a balcony forecast tile",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )
    packet = build_behavior_failure_packet(
        prompt="make a balcony forecast tile",
        artifact_class="static_ui_artifact",
        behavior_contract=contract,
        behavior_probe={
            "test": "weather-card-fields",
            "actual": {
                "before": "City: San Francisco Temperature: 68F Condition: Sunny",
                "after": "City: San Francisco Temperature: 68F Condition: Sunny",
                "clicked": True,
            },
            "verdict": "FAIL",
            "primary_behavior_failure_bucket": "weather_static_when_update_expected",
        },
        selected_preview_path=f"{WORKSPACE}/index.html",
        generated_files=["index.html", "script.js", "styles.css"],
        model_authored_targets=["index.html", "script.js", "styles.css"],
        final_reason_codes=[],
        allowed_workspace=WORKSPACE,
    )
    prompt = build_repair_prompt_from_failure_packet(packet)

    assert "artifact_family:" in prompt
    assert "original_prompt:" in prompt
    assert "selected_preview_path:" in prompt
    assert "allowed_files:" in prompt
    assert "failed_probe_id:" in prompt
    assert "expected_behavior:" in prompt
    assert "primary_failure_bucket:" in prompt
    assert "observed_before:" in prompt
    assert "observed_after:" in prompt
    assert "observed_interaction:" in prompt
    assert "why_this_failed:" in prompt
    assert "current_files_summary:" in prompt
    assert "required_repair:" in prompt
    assert "required_output_format:" in prompt
    assert "WriteFile" in prompt
    assert '<file path="RELATIVE_ALLOWED_FILE">' in prompt
    assert "If you change an element id" in prompt
    assert "backend-authored rescue content" in prompt


def test_browser_failure_packet_records_required_weather_and_drawing_repairs() -> None:
    weather_contract = build_artifact_behavior_contract(
        prompt="make a weather tile",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )
    weather_packet = build_behavior_failure_packet(
        prompt="make a weather tile",
        artifact_class="static_ui_artifact",
        behavior_contract=weather_contract,
        behavior_probe={
            "test": "weather-card-fields",
            "verdict": "FAIL",
            "actual": {"before": "SF 68F Sunny", "after": "SF 68F Sunny", "clicked": True},
            "primary_behavior_failure_bucket": "weather_static_when_update_expected",
        },
        selected_preview_path=f"{WORKSPACE}/index.html",
        generated_files=["index.html", "script.js", "styles.css"],
        model_authored_targets=["index.html", "script.js", "styles.css"],
        final_reason_codes=[],
        allowed_workspace=WORKSPACE,
    )
    drawing_contract = build_artifact_behavior_contract(
        prompt="make a drawing pad",
        artifact_class="static_ui_artifact",
        task_shape="disposable_small_file_bundle",
    )
    drawing_packet = build_behavior_failure_packet(
        prompt="make a drawing pad",
        artifact_class="static_ui_artifact",
        behavior_contract=drawing_contract,
        behavior_probe={
            "test": "drawing-surface-changes",
            "verdict": "FAIL",
            "actual": {"canvas": True, "changed": False},
            "primary_behavior_failure_bucket": "drawing_canvas_no_pixel_change",
        },
        selected_preview_path=f"{WORKSPACE}/index.html",
        generated_files=["index.html", "script.js", "styles.css"],
        model_authored_targets=["index.html", "script.js", "styles.css"],
        final_reason_codes=[],
        allowed_workspace=WORKSPACE,
    )

    assert weather_packet["artifact_family"] == "weather/forecast/tile"
    assert "weather control" in weather_packet["why_this_failed"]
    assert "changes forecast state" in weather_packet["required_repair"]
    assert drawing_packet["artifact_family"] == "drawing/canvas/sketch"
    assert "pointer/mouse drawing" in drawing_packet["why_this_failed"]
    assert "script selectors consistent" in drawing_packet["required_repair"]
