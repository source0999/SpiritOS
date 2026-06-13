from __future__ import annotations

from pathlib import Path

from source_proxy.decision.expectation_reporting import (
    build_batch_rollup,
    build_decision_trace,
    detect_artifact_evidence_gaps,
    render_batch_report_html,
)
from source_proxy.decision.expectation_scoring import (
    build_expectation_score,
    expectation_score_reason_vocabulary,
)


def _score() -> dict:
    return {
        "prompt": "make a timer app",
        "route_status": "GO",
        "route_type": "product",
        "task_shape": "disposable_small_file_bundle",
        "task_shape_source": "generic_artifact_resolver",
        "artifact_class": "static_ui_artifact",
        "files_changed": ["index.html", "app.js"],
        "workspace_files": ["index.html", "app.js"],
        "model_authored_targets": ["index.html", "app.js"],
        "file_equals_model_action_content": True,
        "backend_created_content": False,
        "real_app_touched": False,
        "openable_homepage": True,
        "selected_preview_path": "workspace/index.html",
        "preview_selection_reason": "index_html_present",
        "selected_coder_lane": "qwen_local_coder",
        "model_lane_observability": {
            "sidecar_lanes_live": False,
            "sidecar_lanes_considered": ["hermes_sidecar_verifier_preview"],
        },
        "behavior_contract": {
            "behavior_required": True,
            "probe_targets": [
                {
                    "probe_id": "timer-start-stop-freeze",
                    "acceptance_criterion": "Timer starts and stops.",
                    "expected_observation": "Displayed time changes after start.",
                }
            ],
        },
        "expectation_score": {
            "product_verdict": "WEAK_PASS",
        },
    }


def test_detect_artifact_evidence_gaps_finds_missing_and_external_refs(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        '<!doctype html><html><head><link rel="stylesheet" href="missing.css"></head>'
        '<body><script src="app.js"></script><img src="https://example.com/a.png"></body></html>',
        encoding="utf-8",
    )
    (tmp_path / "app.js").write_text("console.log('ok')", encoding="utf-8")

    gaps = detect_artifact_evidence_gaps(workspace=tmp_path, entrypoint="index.html")

    assert gaps["missing_local_references"] == ["missing.css"]
    assert gaps["external_resources"] == ["https://example.com/a.png"]
    assert "missing_linked_local_files" in gaps["reason_codes"]
    assert "external_resources_present" in gaps["reason_codes"]


def test_decision_trace_surfaces_initial_vs_verified_and_lane_context_fields() -> None:
    score = _score()
    verified = build_expectation_score(
        score=score,
        browser_open_result={"opened": True},
        behavior_probe_result={"verdict": "PASS", "passed": True},
        diagnostic_row={"artifact_matches_plain_user_intent": True},
    )

    trace = build_decision_trace(
        score=score,
        verified_expectation_score=verified,
        browser_open_result={"opened": True},
        behavior_probe_result={"verdict": "PASS", "passed": True},
    )

    assert trace["initial_live_expectation_verdict"] == "WEAK_PASS"
    assert trace["final_verified_expectation_verdict"] == "PASS"
    assert trace["behavior_evidence_attached"] is True
    assert trace["model_lane_selected"] == "qwen_local_coder"
    assert trace["sidecar_lane_status"]["live"] is False
    assert trace["context_decision"]["web_search_used"] is False


def test_batch_rollup_and_html_render_summary_table() -> None:
    score = _score()
    verified = build_expectation_score(
        score=score,
        browser_open_result={"opened": True},
        behavior_probe_result={"verdict": "PASS", "passed": True},
        diagnostic_row={"artifact_matches_plain_user_intent": True},
    )
    trace = build_decision_trace(
        score=score,
        verified_expectation_score=verified,
        browser_open_result={"opened": True},
        behavior_probe_result={"verdict": "PASS", "passed": True},
    )

    rollup = build_batch_rollup([trace])
    html = render_batch_report_html(
        title="Level 2 Report",
        traces=[trace],
        vocabulary=expectation_score_reason_vocabulary(),
    )

    assert rollup["initial_verdict_counts"] == {"WEAK_PASS": 1}
    assert rollup["verified_verdict_counts"] == {"PASS": 1}
    assert "Scorer Summary Rollup" in html
    assert "Per-Run Decision Traces" in html
    assert "make a timer app" in html
