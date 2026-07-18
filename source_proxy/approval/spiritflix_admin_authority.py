"""Server-owned SpiritFlix administrative mutation contract.

This module intentionally performs no media mutation itself. It is the only
approved path from an immutable preview to a consumed admin-executor binding;
individual writer ports are migrated to it in subsequent slices.
"""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

from .campaign_authority import CampaignApprovalError, ROOT, _call, canonical_json, current_head

OPERATION = "spiritflix_admin_mutation"
CONSUMER = "spiritflix-admin-executor"
PLUGIN = "spiritflix-admin"


def admin_content_hash(*, action: str, target: str, configured_root: str, plan: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json({"action": action, "configured_root": configured_root, "plan": plan, "target": target}).encode("utf-8")).hexdigest()


def persist_spiritflix_admin_preview(*, action: str, target: str, configured_root: str, plan: dict[str, Any]) -> dict[str, Any]:
    if not action or not target or not configured_root or not isinstance(plan, dict):
        raise CampaignApprovalError("spiritflix_admin_preview_invalid")
    content_hash = admin_content_hash(action=action, target=target, configured_root=configured_root, plan=plan)
    return _call("persist-preview", {"repository": "SpiritOS", "worktree": ROOT, "root": ROOT, "target": target, "plugin": PLUGIN, "content_hash": content_hash, "context": configured_root, "source_head": current_head()})


def issue_spiritflix_admin_approval(*, preview_id: str, expected_generation: int) -> dict[str, Any]:
    issued = _call("issue", {"preview_id": preview_id, "expected_generation": str(expected_generation), "consumer": CONSUMER, "operation": OPERATION, "expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat()})
    return {"approval_id": str(issued["approval_id"]), "generation": int(issued["generation"]), "state": str(issued["state"])}


def consume_spiritflix_admin_approval(*, approval_id: str, action: str, target: str, configured_root: str, plan: dict[str, Any]) -> dict[str, Any]:
    approval = _call("lookup", {"approval_id": approval_id})
    if approval.get("consumer") != CONSUMER:
        raise CampaignApprovalError("spiritflix_admin_consumer_mismatch")
    if approval.get("operation") != OPERATION:
        raise CampaignApprovalError("spiritflix_admin_operation_mismatch")
    binding = {"approval_id": approval_id, "generation": str(approval.get("generation") or ""), "consumer": CONSUMER, "operation": OPERATION, "repository": "SpiritOS", "worktree": ROOT, "root": ROOT, "target": target, "plugin": PLUGIN, "preview": approval.get("preview"), "content_hash": admin_content_hash(action=action, target=target, configured_root=configured_root, plan=plan), "context": configured_root, "source_head": current_head()}
    _call("consume", binding)
    return {"approval_id": approval_id, "generation": int(approval["generation"]), "binding": binding}


def finalize_spiritflix_admin_execution(consumed: dict[str, Any], *, result_id: str, status: str = "succeeded") -> dict[str, Any]:
    binding = dict(consumed["binding"])
    binding.update({"result_id": result_id, "status": status, "evidence": canonical_json({"redacted": True, "operation": OPERATION}), "source_head": current_head()})
    return _call("finalize", binding)


def compensate_spiritflix_admin_execution(
    consumed: dict[str, Any],
    *,
    result_hash: str,
    evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    binding = dict(consumed["binding"])
    binding.update({
        "result_hash": result_hash,
        "evidence": canonical_json(evidence or {"compensation": True, "redacted": True, "operation": OPERATION}),
        "source_head": current_head(),
    })
    return _call("compensate", binding)
