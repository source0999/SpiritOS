"""Fail-closed conflict receipts for Campaign 3 coding-lane evidence."""
from __future__ import annotations

import hashlib
import json
from typing import Any


CONFLICT_RECEIPT_VERSION = "campaign-3/conflict-receipt/v1"
_PRECEDENCE = {
    "repository_current": 500,
    "mac_platform_verifier": 400,
    "local_verifier": 350,
    "scout_current": 300,
    "context_model": 200,
    "research": 150,
    "obsidian_current": 100,
    "obsidian_stale": 0,
}


def resolve_coding_lane_conflicts(*, task_id: str, claims: list[dict[str, Any]]) -> dict[str, Any]:
    """Resolve only explicitly-proven claims; unresolved disagreement blocks GO."""
    normalized = [_normalize_claim(claim) for claim in claims]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for claim in normalized:
        grouped.setdefault(claim["subject"], []).append(claim)
    conflicts = []
    for subject, group in sorted(grouped.items()):
        values = {json.dumps(item["value"], sort_keys=True) for item in group}
        if len(values) < 2:
            continue
        ranked = sorted(group, key=lambda item: (-item["precedence"], item["lane_id"]))
        winner = ranked[0]
        tied = len(ranked) > 1 and ranked[0]["precedence"] == ranked[1]["precedence"]
        conflicts.append({
            "conflict_id": "conflict_" + hashlib.sha256(subject.encode()).hexdigest()[:12],
            "subject": subject, "claims": group, "selected": None if tied else winner,
            "resolution": "unresolved_equal_precedence" if tied else "precedence_selected",
            "reason": "equal_precedence_conflicting_claims" if tied else f"{winner['lane_id']} outranks conflicting evidence",
        })
    unresolved = [item for item in conflicts if item["selected"] is None]
    ceiling = "blocked_unresolved_conflict" if unresolved else ("resolved_conflict_no_product_pass" if conflicts else "no_conflict_detected")
    receipt = {
        "schema_version": CONFLICT_RECEIPT_VERSION, "task_id": task_id,
        "precedence_order": [name for name, _ in sorted(_PRECEDENCE.items(), key=lambda item: -item[1])],
        "claims": normalized, "conflicts": conflicts, "unresolved": bool(unresolved),
        "claim_ceiling": ceiling, "verdict_effect": "BLOCKED_ENV" if unresolved else "INTEGRATED_LIVE",
    }
    receipt["receipt_hash"] = "sha256:" + hashlib.sha256(json.dumps(receipt, sort_keys=True).encode()).hexdigest()
    return receipt


def resolve_coding_lane_conflicts_for_task(task_id: str, *, claims: list[dict[str, Any]]) -> dict[str, Any]:
    from source_proxy.tasks.long_running import record_subsystem_integration_result
    receipt = resolve_coding_lane_conflicts(task_id=task_id, claims=claims)
    status = "BLOCKED_ENV" if receipt["unresolved"] else "INTEGRATED_LIVE"
    payload = record_subsystem_integration_result(
        task_id, subsystem="campaign_3_conflict_resolver", consumer_subsystem="coding_verifier_conflict_consumer",
        upstream_state={"task_id": task_id, "claim_count": len(claims), "conflict_receipt_version": CONFLICT_RECEIPT_VERSION},
        output={"summary": receipt["claim_ceiling"], "conflict_receipt": receipt}, status=status,
        changed_state_fields=["ast_snapshot.campaign_3_conflicts"],
        failure_reason="unresolved_coding_lane_conflict" if receipt["unresolved"] else None,
    )
    return {"status": status, "receipt": receipt, "task": payload["task"]}


def _normalize_claim(claim: dict[str, Any]) -> dict[str, Any]:
    lane_id = str(claim.get("lane_id") or "")
    if lane_id not in _PRECEDENCE:
        raise ValueError("campaign_3_conflict_unknown_lane")
    subject = str(claim.get("subject") or "")
    if not subject or "value" not in claim:
        raise ValueError("campaign_3_conflict_claim_invalid")
    freshness = str(claim.get("freshness") or "current")
    if lane_id == "obsidian_stale" or freshness == "stale":
        precedence = 0
    else:
        precedence = _PRECEDENCE[lane_id]
    return {"lane_id": lane_id, "subject": subject, "value": claim["value"], "provenance": str(claim.get("provenance") or ""), "freshness": freshness, "precedence": precedence}
