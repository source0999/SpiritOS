from __future__ import annotations

import importlib.util
from pathlib import Path

from source_proxy.verification.anticheat import detector_registry, run_anticheat_detectors
from source_proxy.verification.anticheat.legacy import copied_legacy_anticheat_verdict, new_registry_parity_verdict


NEGATIVE_CASES = {
    "canned_output_detected": {"canned_output": True, "output_origin": "canned template"},
    "static_source_labeled_live": {"research_label": "live", "research_origin": "static"},
    "route_only_integration_proof": {"integration_claim": True, "route_status_checked": True, "behavior_exercised": False},
    "status_ping_only_behavior_proof": {"behavior_claim": True, "status_ping_only": True},
    "repo_context_labeled_internet": {"internet_research_claim": True, "source_origin": "repo"},
    "fixture_or_mock_labeled_live": {"live_evidence_claim": True, "evidence_origin": "mock"},
    "preview_labeled_executed": {"executed_claim": True, "artifact_kind": "preview"},
    "fallback_counted_as_primary_success": {"fallback_used": True, "reported_success_path": "primary"},
    "renderer_created_substance": {"substantive_decision_source": "renderer"},
    "manual_pass_or_json_flip": {"manual_json_edit": True, "final_status": "PASS"},
    "consumer_event_does_not_launder_canned_output": {"canned_output": True, "consumer_event_id": "evt-123"},
    "unavailable_provider_reported_success": {"provider_available": False, "provider_result": "success"},
    "summary_pass_raw_failure": {"summary_status": "PASS", "raw_status": "FAIL"},
    "benchmark_specific_runtime_branch": {"runtime_code": "if prompt_id == 'A2': return expected_answer"},
    "test_only_path_labeled_production": {"runtime_integration": True, "implementation_origin": "test_only"},
}


def test_registry_imports_independently_and_lists_detectors() -> None:
    registry = detector_registry()

    assert len(registry.detector_ids) >= 15
    assert "canned_output" in registry.detector_ids
    assert "fallback_labeled_primary_success" in registry.detector_ids


def test_each_negative_case_is_flagged() -> None:
    for expected_code, payload in NEGATIVE_CASES.items():
        report = run_anticheat_detectors(payload)
        codes = {violation.violation_code for violation in report.violations}
        assert report.status == "fail"
        assert expected_code in codes


def test_positive_grounded_evidence_passes_without_false_positive() -> None:
    payload = {
        "raw_evidence_path": "docs/evidence/run/raw.json",
        "provider_available": True,
        "provider_result": "used",
        "tool_status": "used",
        "validator_result": "passed",
        "summary_status": "PASS",
        "raw_status": "PASS",
        "behavior_claim": True,
        "behavior_exercised": True,
        "fallback_used": False,
        "research_label": "live",
        "research_origin": "provider_query",
        "live_evidence_claim": True,
        "evidence_origin": "live_tool",
        "substantive_decision_source": "model",
    }

    report = run_anticheat_detectors(payload)

    assert report.status == "pass"
    assert report.violations == ()


def test_copied_legacy_parity_surface_matches_new_registry() -> None:
    shared_corpus = [
        {},
        {"canned_output": True},
        {"summary_status": "PASS", "raw_status": "FAIL"},
        {"fallback_used": True, "reported_success_path": "primary"},
    ]
    for payload in shared_corpus:
        assert copied_legacy_anticheat_verdict(payload) == new_registry_parity_verdict(payload)


def test_set_a_runner_imports_f2_registry_additively_without_execution() -> None:
    runner = Path("docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py")
    source = runner.read_text()

    assert "f2_anticheat_detector_registry" in source
    assert "from source_proxy.verification.anticheat import detector_registry" in source
    assert importlib.util.find_spec("source_proxy.verification.anticheat") is not None


def test_fake_go_detected_is_not_hardcoded_false_in_new_package() -> None:
    package_root = Path("source_proxy/verification/anticheat")
    text = "\n".join(path.read_text() for path in package_root.glob("*.py"))

    assert "fake_go_detected = False" not in text
    assert "fake_go_detected=False" not in text
