from __future__ import annotations

from typing import Any

from source_proxy.decision.model_lanes import get_model_lane


VERIFIER_LANE_PACKET_VERSION = "source-proxy-verifier-lane-packet-v0.1"
VERIFIER_LANE_OUTPUT_VERSION = "source-proxy-verifier-lane-output-v0.1"
ALLOWED_VERDICTS = {"PASS", "WARNING", "NEEDS_FIX", "HANDOFF", "FAIL", "UNVERIFIED"}


def build_verifier_lane_packet(
    *,
    original_user_prompt: str,
    normalized_intent: str,
    behavior_contract: dict[str, Any],
    task_spec: dict[str, Any] | None = None,
    planner_criteria: list[dict[str, Any]] | None = None,
    context_packet_summary: dict[str, Any] | None = None,
    selected_coder_lane: str = "qwen_local_coder",
    changed_files_summary: list[str] | None = None,
    generated_preview_path: str = "",
    test_output_summary: dict[str, Any] | None = None,
    browser_observation: dict[str, Any] | None = None,
    receipt_path: str = "",
    transcript_path: str = "",
    workspace_diff_path: str = "",
    behavior_probe_evidence: dict[str, Any] | None = None,
    repair_packet: dict[str, Any] | None = None,
    repair_result: dict[str, Any] | None = None,
    retest_result_path: str = "",
    known_failure_modes: list[str] | None = None,
    model_claim_if_any: str = "",
) -> dict[str, Any]:
    return {
        "packet_version": VERIFIER_LANE_PACKET_VERSION,
        "preview_only": True,
        "advisory_only": True,
        "model_calls_enabled": False,
        "original_user_prompt": original_user_prompt,
        "normalized_intent": normalized_intent,
        "task_spec": task_spec or {},
        "planner_criteria": list(planner_criteria or []),
        "behavior_contract": behavior_contract,
        "context_packet_summary": context_packet_summary or {},
        "selected_coder_lane": selected_coder_lane,
        "changed_files_summary": list(changed_files_summary or []),
        "generated_preview_path": generated_preview_path,
        "test_output_summary": test_output_summary or {},
        "browser_observation": browser_observation or {},
        "receipt_path": receipt_path,
        "transcript_path": transcript_path,
        "workspace_diff_path": workspace_diff_path,
        "behavior_probe_evidence": behavior_probe_evidence or {},
        "repair_packet": repair_packet or {},
        "repair_result": repair_result or {},
        "retest_result_path": retest_result_path,
        "known_failure_modes": list(known_failure_modes or []),
        "model_claim_if_any": model_claim_if_any,
        "non_authoritative_signals": [
            "route_go",
            "file_creation",
            "preview_opens",
            "static_dom_presence",
            "model_self_report",
        ],
    }


def normalize_verifier_lane_output(
    *,
    verifier_lane_id: str,
    proposed_verdict: str,
    reasons: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    suspected_fake_success: bool = False,
    suspected_hardcoding: bool = False,
    suspected_scaffold_or_fallback: bool = False,
    missing_evidence: list[str] | None = None,
    recommended_next_action: str = "",
    browser_behavior_passed: bool | None = None,
) -> dict[str, Any]:
    lane = get_model_lane(verifier_lane_id)
    verdict = proposed_verdict.upper()
    if verdict not in ALLOWED_VERDICTS:
        verdict = "UNVERIFIED"

    missing = list(missing_evidence or [])
    refs = list(evidence_refs or [])
    reason_codes = list(reasons or [])
    if lane["status"] != "active_primary_local_lane":
        reason_codes.append("verifier_lane_advisory_only")
    if missing:
        reason_codes.append("missing_evidence")
    if suspected_fake_success:
        reason_codes.append("suspected_fake_success")
    if suspected_hardcoding:
        reason_codes.append("suspected_hardcoding")
    if suspected_scaffold_or_fallback:
        reason_codes.append("suspected_scaffold_or_fallback")

    if verdict == "PASS" and browser_behavior_passed is not True:
        verdict = "WARNING" if refs else "UNVERIFIED"
        reason_codes.append("pass_blocked_without_browser_behavior_evidence")
    if verdict == "PASS" and missing:
        verdict = "WARNING"
        reason_codes.append("pass_downgraded_for_missing_evidence")
    if verdict == "PASS" and (suspected_fake_success or suspected_hardcoding or suspected_scaffold_or_fallback):
        verdict = "WARNING"
        reason_codes.append("pass_downgraded_for_risk_signal")
    if browser_behavior_passed is False and proposed_verdict.upper() == "PASS":
        verdict = "NEEDS_FIX" if refs else "UNVERIFIED"
        reason_codes.append("failed_browser_behavior_blocks_pass")

    return {
        "output_version": VERIFIER_LANE_OUTPUT_VERSION,
        "verifier_lane_id": verifier_lane_id,
        "advisory_only": True,
        "model_calls_enabled": False,
        "verdict": verdict,
        "reasons": sorted(set(reason_codes)),
        "evidence_refs": refs,
        "suspected_fake_success": suspected_fake_success,
        "suspected_hardcoding": suspected_hardcoding,
        "suspected_scaffold_or_fallback": suspected_scaffold_or_fallback,
        "missing_evidence": missing,
        "recommended_next_action": recommended_next_action or _default_next_action(verdict),
        "cannot_override_browser_behavior": True,
        "cannot_turn_unverified_into_pass": True,
        "cannot_trust_model_claim_alone": True,
        "hidden_benchmark_hint_provider": False,
    }


def verifier_lane_preview(packet: dict[str, Any]) -> dict[str, Any]:
    missing = []
    if not packet.get("task_spec"):
        missing.append("task_spec")
    if not packet.get("planner_criteria"):
        missing.append("planner_criteria")
    if not packet.get("generated_preview_path"):
        missing.append("generated_preview_path")
    if not packet.get("browser_observation"):
        missing.append("browser_observation")
    if not packet.get("receipt_path"):
        missing.append("receipt_path")
    if not packet.get("transcript_path"):
        missing.append("transcript_path")
    if not packet.get("workspace_diff_path"):
        missing.append("workspace_diff_path")
    if not packet.get("behavior_probe_evidence"):
        missing.append("behavior_probe_evidence")
    if not packet.get("retest_result_path"):
        missing.append("retest_result_path")
    if not (packet.get("behavior_contract") or {}).get("behavior_required"):
        missing.append("behavior_contract_required_probe")
    browser = packet.get("browser_observation") or {}
    browser_failed = str(browser.get("verdict") or "").upper() == "FAIL" or browser.get("passed") is False
    route_open_only = bool(browser.get("opened")) and "passed" not in browser and not packet.get("behavior_probe_evidence")
    proposed = "NEEDS_FIX" if browser_failed else "UNVERIFIED" if missing else "WARNING"
    reasons = ["preview_contract_only_no_model_call"]
    if browser_failed:
        reasons.append("browser_behavior_failed")
    if route_open_only:
        reasons.append("route_or_open_only_success_signal")
    return normalize_verifier_lane_output(
        verifier_lane_id="hermes_sidecar_verifier_preview",
        proposed_verdict=proposed,
        reasons=reasons,
        evidence_refs=[
            ref
            for ref in [
                packet.get("receipt_path"),
                packet.get("transcript_path"),
                packet.get("workspace_diff_path"),
                packet.get("retest_result_path"),
            ]
            if ref
        ],
        missing_evidence=missing,
        browser_behavior_passed=bool((packet.get("browser_observation") or {}).get("passed")),
    )


def _default_next_action(verdict: str) -> str:
    if verdict == "PASS":
        return "preserve evidence and continue within approved scope"
    if verdict in {"WARNING", "NEEDS_FIX", "UNVERIFIED"}:
        return "collect missing browser/retest evidence before any PASS"
    if verdict == "HANDOFF":
        return "operator reviews handoff packet"
    return "fix observed behavior failure or prepare handoff"
