from __future__ import annotations

from typing import Any

from source_proxy.decision.artifact_final_verdict import normalize_artifact_final_verdict


RETEST_RESULT_VERSION = "source-proxy-artifact-retest-result-v0.2.phase-6"


def build_artifact_retest_result(
    *,
    repair_result: dict[str, Any],
    behavior_contract: dict[str, Any],
    artifact_ready: bool,
    behavior_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    behavior = behavior_result or {}
    behavior_verdict = str(behavior.get("verdict") or "UNVERIFIED").upper()
    behavior_required = bool(behavior_contract.get("behavior_required"))
    repair_status = str(repair_result.get("status") or "UNKNOWN").upper()
    handoff_required = bool(repair_result.get("handoff_required")) or repair_status == "HANDOFF"
    reason_codes = _reason_codes(repair_result, behavior, artifact_ready)

    final = normalize_artifact_final_verdict(
        route_status="GO" if repair_status == "READY_FOR_RETEST" else repair_status,
        artifact_ready=artifact_ready,
        behavior_required=behavior_required,
        behavior_verdict=behavior_verdict,
        repair_verdict=repair_status,
        handoff_required=handoff_required,
        reason_codes=reason_codes,
    )

    return {
        "result_version": RETEST_RESULT_VERSION,
        "repair_status": repair_status,
        "artifact_ready": artifact_ready,
        "behavior_required": behavior_required,
        "behavior_result": {
            "verdict": behavior_verdict,
            "test": str(behavior.get("test") or ""),
            "observed": behavior.get("observed") if isinstance(behavior.get("observed"), dict) else {},
            "expected": behavior.get("expected") if isinstance(behavior.get("expected"), dict) else {},
            "actual": behavior.get("actual") if isinstance(behavior.get("actual"), dict) else {},
            "passed": bool(behavior.get("passed")) if "passed" in behavior else behavior_verdict == "PASS",
            "reason": str(behavior.get("reason") or ""),
        },
        "canonical_final_verdict": final["label"],
        "product_pass": final["product_pass"],
        "final_reason_codes": final["reason_codes"],
        "changed_files": list(repair_result.get("changed_files") or []),
        "diffs": list(repair_result.get("diffs") or []),
        "attempts_used": int(repair_result.get("attempts_used") or 0),
        "handoff_required": final["label"] == "HANDOFF",
        "handoff_reason": str(repair_result.get("handoff_reason") or ""),
    }


def _reason_codes(repair_result: dict[str, Any], behavior: dict[str, Any], artifact_ready: bool) -> list[str]:
    reasons = [str(code) for code in repair_result.get("reason_codes") or [] if str(code)]
    reasons.extend(str(code) for code in behavior.get("reason_codes") or [] if str(code))
    repair_status = str(repair_result.get("status") or "").upper()
    behavior_verdict = str(behavior.get("verdict") or "").upper()

    if repair_status == "READY_FOR_RETEST":
        reasons.append("repair_ready_for_retest")
    attempts_used = int(repair_result.get("attempts_used") or 0)
    if attempts_used:
        reasons.append(f"repair_attempts_{attempts_used}")
    if not artifact_ready:
        reasons.append("post_repair_artifact_not_ready")
    if behavior_verdict == "PASS":
        reasons.append("post_repair_behavior_pass")
        reasons.append("post_behavior_repair_pass")
    elif behavior_verdict == "FAIL":
        reasons.append("post_repair_behavior_fail")
        reasons.append("post_behavior_repair_failed")
        reasons.append("behavior_failed_verified")
    elif behavior_verdict in {"", "UNVERIFIED", "NOT_RUN", "SKIPPED", "UNKNOWN"}:
        reasons.append("post_repair_behavior_unverified")
    elif behavior_verdict in {"NEEDS_FIX", "ERROR"}:
        reasons.append("post_repair_verifier_needs_fix")
    return sorted(set(reasons))
