from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from source_proxy.diagnostics.status_codes import FailureClass
from source_proxy.verification.anticheat.types import AntiCheatViolation

Payload = dict[str, Any]
DetectorFn = Callable[[Payload], AntiCheatViolation | None]


@dataclass(frozen=True)
class AntiCheatDetector:
    detector_id: str
    description: str
    detect: DetectorFn

    def run(self, payload: Payload) -> AntiCheatViolation | None:
        return self.detect(payload)


def _text(payload: Payload, *keys: str) -> str:
    parts: list[str] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif isinstance(value, dict):
            parts.extend(str(item) for item in value.values())
    return " ".join(parts).lower()


def _violation(detector_id: str, code: str, message: str, failure_class: FailureClass, **evidence: Any) -> AntiCheatViolation:
    return AntiCheatViolation(
        detector_id=detector_id,
        violation_code=code,
        message=message,
        failure_class=failure_class,
        evidence={k: v for k, v in evidence.items() if v not in (None, "", [], {})},
    )


def _canned_output(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("canned_output") is True or "canned" in _text(payload, "output_origin", "notes"):
        return _violation("canned_output", "canned_output_detected", "Output is marked or described as canned, not behavior-derived.", FailureClass.VALIDATOR_FAILURE)
    return None


def _static_research_labeled_live(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("research_label") == "live" and payload.get("research_origin") in {"static", "fixture", "repo_snapshot"}:
        return _violation("static_research_labeled_live", "static_source_labeled_live", "Static research was labeled as live.", FailureClass.EVIDENCE_MISSING)
    return None


def _route_existence_as_integration(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("integration_claim") is True and payload.get("route_status_checked") is True and not payload.get("behavior_exercised"):
        return _violation("route_existence_as_integration", "route_only_integration_proof", "Route existence was counted as integration proof.", FailureClass.VALIDATOR_FAILURE)
    return None


def _status_ping_as_behavior(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("behavior_claim") is True and payload.get("status_ping_only") is True:
        return _violation("status_ping_as_behavior", "status_ping_only_behavior_proof", "Status ping was counted as task behavior proof.", FailureClass.VALIDATOR_FAILURE)
    return None


def _repo_context_as_internet(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("internet_research_claim") is True and payload.get("source_origin") in {"repo", "local_repo", "context"}:
        return _violation("repo_context_as_internet", "repo_context_labeled_internet", "Repo context was labeled as internet research.", FailureClass.EVIDENCE_MISSING)
    return None


def _fixture_mock_labeled_live(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("live_evidence_claim") is True and payload.get("evidence_origin") in {"fixture", "mock", "test_double"}:
        return _violation("fixture_mock_labeled_live", "fixture_or_mock_labeled_live", "Fixture or mock evidence was labeled live.", FailureClass.EVIDENCE_MISSING)
    return None


def _preview_advisory_labeled_executed(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("executed_claim") is True and payload.get("artifact_kind") in {"preview", "advisory", "dry_run"}:
        return _violation("preview_advisory_labeled_executed", "preview_labeled_executed", "Preview/advisory output was labeled executed.", FailureClass.VALIDATOR_FAILURE)
    return None


def _fallback_labeled_primary_success(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("fallback_used") is True and payload.get("reported_success_path") == "primary":
        return _violation("fallback_labeled_primary_success", "fallback_counted_as_primary_success", "Fallback success was reported as primary success.", FailureClass.VALIDATOR_FAILURE)
    return None


def _renderer_created_decision(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("substantive_decision_source") == "renderer":
        return _violation("renderer_created_decision", "renderer_created_substance", "Renderer filled substantive decision fields.", FailureClass.VALIDATOR_FAILURE)
    return None


def _manual_pass_json_manipulation(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("manual_json_edit") is True and str(payload.get("final_status") or "").upper() in {"PASS", "GO"}:
        return _violation("manual_pass_json_manipulation", "manual_pass_or_json_flip", "Manual JSON/status edit produced a positive verdict.", FailureClass.VALIDATOR_FAILURE)
    return None


def _canned_output_with_consumer_event(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("canned_output") is True and payload.get("consumer_event_id"):
        return _violation("canned_output_with_consumer_event", "consumer_event_does_not_launder_canned_output", "Consumer event id cannot launder canned output.", FailureClass.VALIDATOR_FAILURE)
    return None


def _unavailable_provider_labeled_success(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("provider_available") is False and str(payload.get("provider_result") or "").lower() in {"success", "pass", "used"}:
        return _violation("unavailable_provider_labeled_success", "unavailable_provider_reported_success", "Unavailable provider was reported as success.", FailureClass.SERVICE_UNAVAILABLE)
    return None


def _summary_raw_contradiction(payload: Payload) -> AntiCheatViolation | None:
    summary = str(payload.get("summary_status") or "").upper()
    raw = str(payload.get("raw_status") or "").upper()
    if summary in {"PASS", "GO"} and raw in {"FAIL", "FAILED", "NO-GO", "NO_GO", "ERROR"}:
        return _violation("summary_raw_contradiction", "summary_pass_raw_failure", "Summary verdict contradicts raw evidence.", FailureClass.VALIDATOR_FAILURE)
    return None


def _benchmark_specific_runtime_branch(payload: Payload) -> AntiCheatViolation | None:
    code_text = str(payload.get("runtime_code") or payload.get("code_text") or "")
    lowered = code_text.lower()
    branch_markers = ("if ", "elif ", "case ", "switch", "match ")
    benchmark_tokens = ("a2", "a5", "a9", "set a", "4r", "known benchmark", "expected benchmark")
    if any(marker in lowered for marker in branch_markers) and any(token in lowered for token in benchmark_tokens):
        return _violation("benchmark_specific_runtime_branch", "benchmark_specific_runtime_branch", "Runtime code contains a benchmark-keyed branch.", FailureClass.VALIDATOR_FAILURE)
    return None


def _test_only_production_branch(payload: Payload) -> AntiCheatViolation | None:
    if payload.get("runtime_integration") is True and payload.get("implementation_origin") in {"test_only", "fixture", "harness_only"}:
        return _violation("test_only_production_branch", "test_only_path_labeled_production", "Test-only orchestration was labeled production integration.", FailureClass.VALIDATOR_FAILURE)
    return None


DETECTORS: tuple[AntiCheatDetector, ...] = (
    AntiCheatDetector("canned_output", "Detect canned output not derived from behavior.", _canned_output),
    AntiCheatDetector("static_research_labeled_live", "Detect static research labeled live.", _static_research_labeled_live),
    AntiCheatDetector("route_existence_as_integration", "Detect route-only integration proof.", _route_existence_as_integration),
    AntiCheatDetector("status_ping_as_behavior", "Detect status ping counted as behavior.", _status_ping_as_behavior),
    AntiCheatDetector("repo_context_as_internet", "Detect repo context labeled internet research.", _repo_context_as_internet),
    AntiCheatDetector("fixture_mock_labeled_live", "Detect fixture/mock evidence labeled live.", _fixture_mock_labeled_live),
    AntiCheatDetector("preview_advisory_labeled_executed", "Detect preview/advisory labeled executed.", _preview_advisory_labeled_executed),
    AntiCheatDetector("fallback_labeled_primary_success", "Detect fallback success counted as primary.", _fallback_labeled_primary_success),
    AntiCheatDetector("renderer_created_decision", "Detect renderer-created substantive decisions.", _renderer_created_decision),
    AntiCheatDetector("manual_pass_json_manipulation", "Detect manual PASS or JSON flipping.", _manual_pass_json_manipulation),
    AntiCheatDetector("canned_output_with_consumer_event", "Detect canned output carrying consumer event id.", _canned_output_with_consumer_event),
    AntiCheatDetector("unavailable_provider_labeled_success", "Detect unavailable provider reported successful.", _unavailable_provider_labeled_success),
    AntiCheatDetector("summary_raw_contradiction", "Detect summary/raw evidence contradiction.", _summary_raw_contradiction),
    AntiCheatDetector("benchmark_specific_runtime_branch", "Detect benchmark-keyed runtime branch.", _benchmark_specific_runtime_branch),
    AntiCheatDetector("test_only_production_branch", "Detect test-only path labeled production.", _test_only_production_branch),
)
