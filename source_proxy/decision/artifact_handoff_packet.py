from __future__ import annotations

from typing import Any


HANDOFF_PACKET_VERSION = "source-proxy-artifact-handoff-v0.2.phase-7"


def build_artifact_handoff_packet(
    *,
    prompt: str,
    behavior_contract: dict[str, Any],
    failure_packet: dict[str, Any] | None = None,
    repair_result: dict[str, Any] | None = None,
    retest_result: dict[str, Any] | None = None,
    reason: str = "",
) -> dict[str, Any]:
    failure = failure_packet or {}
    repair = repair_result or {}
    retest = retest_result or {}
    handoff_reason = reason or _infer_handoff_reason(failure, repair, retest)
    approval_needed = _approval_needed_for(handoff_reason)
    final_verdict = str(retest.get("canonical_final_verdict") or repair.get("status") or failure.get("status") or "HANDOFF")
    if final_verdict not in {"HANDOFF", "FAIL", "BLOCKED", "NEEDS_FIX", "UNVERIFIED"}:
        final_verdict = "HANDOFF"

    packet = {
        "packet_version": HANDOFF_PACKET_VERSION,
        "status": "HANDOFF",
        "prompt": prompt,
        "handoff_reason": handoff_reason,
        "final_verdict": final_verdict,
        "approval_needed": approval_needed,
        "next_recommended_route": _next_route_for(handoff_reason),
        "behavior_contract": behavior_contract,
        "failure_packet_summary": {
            "status": str(failure.get("status") or ""),
            "handoff_reasons": list(failure.get("handoff_reasons") or []),
            "artifact_paths": list(failure.get("artifact_paths") or []),
            "allowed_workspace": str(failure.get("allowed_workspace") or ""),
            "expected_behavior": failure.get("expected_behavior") or {},
            "observed_behavior": failure.get("observed_behavior") or {},
            "reason_codes": list(failure.get("reason_codes") or []),
        },
        "repair_summary": {
            "status": str(repair.get("status") or ""),
            "handoff_reason": str(repair.get("handoff_reason") or ""),
            "attempts_used": int(repair.get("attempts_used") or 0),
            "changed_files": list(repair.get("changed_files") or []),
            "diff_count": len(repair.get("diffs") or []),
            "reason_codes": list(repair.get("reason_codes") or []),
        },
        "retest_summary": {
            "canonical_final_verdict": str(retest.get("canonical_final_verdict") or ""),
            "product_pass": bool(retest.get("product_pass")),
            "artifact_ready": bool(retest.get("artifact_ready")),
            "behavior_result": retest.get("behavior_result") or {},
            "final_reason_codes": list(retest.get("final_reason_codes") or []),
        },
        "evidence_refs": _evidence_refs(failure, repair, retest),
        "operator_message": "",
        "safety": {
            "automatic_escalation_performed": False,
            "provider_api_used": False,
            "production_repair_performed": False,
            "obsidian_written": False,
        },
    }
    packet["operator_message"] = render_artifact_handoff_message(packet)
    return packet


def render_artifact_handoff_message(packet: dict[str, Any]) -> str:
    approval = packet.get("approval_needed") or {}
    return "\n".join(
        [
            "HANDOFF: Source Proxy local artifact repair could not safely finish.",
            f"Prompt: {packet.get('prompt') or ''}",
            f"Reason: {packet.get('handoff_reason') or ''}",
            f"Final verdict: {packet.get('final_verdict') or 'HANDOFF'}",
            f"Next recommended route: {packet.get('next_recommended_route') or ''}",
            f"Approval needed: {approval.get('type') or 'operator_review'} - {approval.get('description') or ''}",
            "No automatic escalation, provider/API call, production repair, or Obsidian write was performed.",
        ]
    )


def _infer_handoff_reason(failure: dict[str, Any], repair: dict[str, Any], retest: dict[str, Any]) -> str:
    for reason in failure.get("handoff_reasons") or []:
        if reason:
            return str(reason)
    if repair.get("handoff_reason"):
        return str(repair["handoff_reason"])
    if retest.get("canonical_final_verdict") in {"FAIL", "UNVERIFIED", "NEEDS_FIX", "BLOCKED"}:
        codes = retest.get("final_reason_codes") or []
        return str(codes[0]) if codes else "post_repair_final_verdict_not_pass"
    return "handoff_reason_unclear"


def _approval_needed_for(reason: str) -> dict[str, str]:
    lowered = reason.lower()
    if "artifact_path_missing" in lowered or "artifact_or_preview_missing" in lowered:
        return {
            "type": "artifact_generation_or_rerun_approval",
            "description": "Approve a new disposable artifact generation or rerun before local repair can continue.",
        }
    if "production" in lowered or "outside_allowed_workspace" in lowered or "path_outside" in lowered:
        return {
            "type": "production_or_path_scope_approval",
            "description": "Approve any broader path scope explicitly; local repair cannot touch production/source paths.",
        }
    if "provider" in lowered or "api" in lowered:
        return {
            "type": "provider_api_approval",
            "description": "Approve provider/API usage explicitly; local repair cannot escalate automatically.",
        }
    if "worker" in lowered or "unavailable" in lowered:
        return {
            "type": "local_worker_recovery_approval",
            "description": "Approve local worker recovery or another route; no worker was started automatically.",
        }
    if "attempt" in lowered or "failed" in lowered or "behavior" in lowered:
        return {
            "type": "stronger_repair_route_approval",
            "description": "Approve another bounded local attempt or stronger route after reviewing evidence.",
        }
    return {
        "type": "operator_review",
        "description": "Review packet evidence and choose the next approved route.",
    }


def _next_route_for(reason: str) -> str:
    approval = _approval_needed_for(reason)["type"]
    return {
        "artifact_generation_or_rerun_approval": "approved disposable artifact regeneration or diagnostic rerun",
        "production_or_path_scope_approval": "operator-approved production/path-scope handoff",
        "provider_api_approval": "operator-approved provider/API route",
        "local_worker_recovery_approval": "operator-approved local worker recovery",
        "stronger_repair_route_approval": "operator-approved bounded repair retry or stronger route",
    }.get(approval, "operator review")


def _evidence_refs(failure: dict[str, Any], repair: dict[str, Any], retest: dict[str, Any]) -> dict[str, Any]:
    refs = dict(failure.get("evidence_refs") or {})
    refs["repair_changed_files"] = list(repair.get("changed_files") or [])
    refs["repair_diff_count"] = len(repair.get("diffs") or [])
    refs["retest_changed_files"] = list(retest.get("changed_files") or [])
    refs["retest_diff_count"] = len(retest.get("diffs") or [])
    return refs
