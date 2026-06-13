from __future__ import annotations

from pathlib import Path

from source_proxy.decision.expectation_scoring import (
    build_expectation_score,
    expectation_score_reason_vocabulary,
)
from source_proxy.decision.human_messy_homepage import run_human_messy_homepage


def _score() -> dict:
    return {
        "prompt": "make a calculator app",
        "route_status": "GO",
        "route_type": "product",
        "task_shape": "disposable_small_file_bundle",
        "task_shape_source": "generic_artifact_resolver",
        "artifact_class": "static_ui_artifact",
        "files_changed": ["index.html", "script.js", "styles.css"],
        "workspace_files": ["index.html", "script.js", "styles.css"],
        "model_authored_targets": ["index.html", "script.js", "styles.css"],
        "file_equals_model_action_content": True,
        "backend_created_content": False,
        "real_app_touched": False,
        "openable_homepage": True,
        "selected_preview_path": "workspace/index.html",
        "preview_selection_reason": "index_html_present",
        "selected_coder_lane": "qwen_local_coder",
        "model_lane_observability": {
            "sidecar_lanes_live": False,
        },
        "behavior_contract": {
            "behavior_required": True,
            "probe_targets": [
                {
                    "probe_id": "calculator-basic-arithmetic",
                    "acceptance_criterion": "Basic arithmetic computes correctly.",
                    "expected_observation": "The calculator displays 5 for 2 + 3.",
                }
            ],
        },
    }


def test_expectation_score_pass_requires_browser_behavior_evidence() -> None:
    result = build_expectation_score(
        score=_score(),
        browser_open_result={"opened": True, "consoleMessages": [], "pageErrors": []},
        behavior_probe_result={
            "verdict": "PASS",
            "passed": True,
            "expected": {"result": "5"},
            "actual": {"displayIncludesFive": True},
        },
        diagnostic_row={"artifact_matches_plain_user_intent": True},
    )

    assert result["product_verdict"] == "PASS"
    assert result["behavior_score"] == 100
    assert result["file_integrity_verdict"] == "PASS"
    assert result["lane_policy_verdict"] == "PASS"
    assert "behavior_pass" in result["score_reason_codes"]


def test_expectation_score_without_behavior_is_weak_pass_not_pass() -> None:
    result = build_expectation_score(
        score=_score(),
        browser_open_result={"opened": True, "consoleMessages": [], "pageErrors": []},
    )

    assert result["product_verdict"] == "WEAK_PASS"
    assert result["behavior_score"] == 50
    assert "behavior_weak" in result["score_reason_codes"]


def test_expectation_score_fails_for_backend_authored_content() -> None:
    score = _score()
    score["backend_created_content"] = True
    score["file_equals_model_action_content"] = False

    result = build_expectation_score(
        score=score,
        browser_open_result={"opened": True},
        behavior_probe_result={"verdict": "PASS", "passed": True},
    )

    assert result["product_verdict"] == "FAIL"
    assert result["file_integrity_verdict"] == "FAIL"
    assert result["safety_boundary_verdict"] == "FAIL"


def test_expectation_score_records_missing_refs_external_resources_and_context_decisions() -> None:
    result = build_expectation_score(
        score=_score(),
        browser_open_result={"opened": True},
        behavior_probe_result={"verdict": "PASS", "passed": True},
        diagnostic_row={
            "artifact_matches_plain_user_intent": True,
            "missing_local_references": ["missing.css"],
            "external_urls_or_remote_resources": ["https://example.com/image.png"],
            "web_search_used": True,
        },
    )

    assert "missing_linked_local_files" in result["score_reason_codes"]
    assert "external_resources_present_review_reasonability" in result["score_reason_codes"]
    assert "web_search_unnecessary_for_local_artifact_prompt" in result["score_reason_codes"]
    assert result["context_decision"]["web_search_used"] is True


def test_expectation_score_flags_live_sidecar_policy_violation() -> None:
    score = _score()
    score["model_lane_observability"]["sidecar_lanes_live"] = True

    result = build_expectation_score(
        score=score,
        browser_open_result={"opened": True},
        behavior_probe_result={"verdict": "PASS", "passed": True},
    )

    assert result["lane_policy_verdict"] == "FAIL"
    assert "sidecar_lane_live_requires_approval" in result["score_reason_codes"]


def test_reason_vocabulary_contains_core_dimensions() -> None:
    vocab = expectation_score_reason_vocabulary()

    assert "behavior_unverified" in vocab
    assert "model_authorship_pass" in vocab
    assert "safety_pass" in vocab


def test_live_product_score_includes_expectation_score_without_model_call(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"

    def fake_model_call(_packet: dict) -> str:
        return (
            '{"action_type":"WriteFile","target":"index.html","arguments":'
            '{"content":"<!doctype html><html><body><button>1</button></body></html>"},'
            '"reason":"create disposable artifact"}'
        )

    score = run_human_messy_homepage(
        prompt="make a calculator app",
        workspace=run_dir / "workspace",
        receipt_path=run_dir / "receipt.json",
        score_path=run_dir / "score.json",
        transcript_path=run_dir / "transcript.txt",
        diff_path=run_dir / "workspace.diff",
        model_call=fake_model_call,
        mode="product",
    )

    assert score["expectation_score"]["expectation_score_version"] == "source-proxy-expectation-score-v0.1"
    assert score["expectation_score"]["product_verdict"] == "WEAK_PASS"
    assert score["expectation_score"]["model_lane_selected"] == "qwen_local_coder"
