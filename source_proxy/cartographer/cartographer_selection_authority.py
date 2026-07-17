"""Durable, proposal-only Cartographer selection handoff.

Cartographer may describe a selected proposal, but it may never issue an
approval or perform a write.  The authenticated operator and this canonical
Source Proxy consumer own the Approval Authority lifecycle.
"""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

from source_proxy.approval.campaign_authority import (
    CampaignApprovalError,
    ROOT,
    _call,
    canonical_json,
    current_head,
)
from source_proxy.cartographer.proposals import list_proposals


CONSUMER = "cartographer-transfer-consumer"
OPERATION = "cartographer_selection_transfer"
PLUGIN = "cartographer-transfer"
ALLOWED_DOWNSTREAM_CONSUMERS = {"design-writeback", "coding-executor:coder"}


class CartographerSelectionError(CampaignApprovalError):
    pass


def _proposal(proposal_id: str) -> Any:
    proposal = next((item for item in list_proposals() if item.proposal_id == proposal_id), None)
    if proposal is None:
        raise CartographerSelectionError("cartographer_proposal_not_found")
    return proposal


def _selection(*, proposal_id: str, consumer: str, target: str) -> tuple[dict[str, Any], str]:
    if consumer not in ALLOWED_DOWNSTREAM_CONSUMERS:
        raise CartographerSelectionError("cartographer_selection_consumer_mismatch")
    if not target or target.strip() != target:
        raise CartographerSelectionError("cartographer_selection_target_invalid")
    proposal = _proposal(proposal_id)
    content = {
        "approved_diff": proposal.approved_diff or proposal.diff_preview or "",
        "proposal_fingerprint": proposal.fingerprint or "",
        "proposal_id": proposal.proposal_id,
        "proposed_files": list(proposal.proposed_files),
        "target": target,
    }
    context = canonical_json({"consumer": consumer, "proposal_id": proposal.proposal_id})
    return content, context


def selection_content_hash(*, proposal_id: str, consumer: str, target: str) -> str:
    content, context = _selection(proposal_id=proposal_id, consumer=consumer, target=target)
    return hashlib.sha256(canonical_json({"content": content, "context": context}).encode("utf-8")).hexdigest()


def persist_cartographer_selection(*, proposal_id: str, consumer: str, target: str) -> dict[str, Any]:
    _content, context = _selection(proposal_id=proposal_id, consumer=consumer, target=target)
    return _call("persist-preview", {
        "repository": "SpiritOS", "worktree": ROOT, "root": ROOT,
        "target": target, "plugin": PLUGIN,
        "content_hash": selection_content_hash(proposal_id=proposal_id, consumer=consumer, target=target),
        "context": context, "source_head": current_head(),
    })


def issue_cartographer_selection(*, preview_id: str, expected_generation: int) -> dict[str, Any]:
    issued = _call("issue", {
        "preview_id": preview_id, "expected_generation": str(expected_generation),
        "consumer": CONSUMER, "operation": OPERATION,
        "expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
    })
    return {"approval_id": str(issued["approval_id"]), "generation": int(issued["generation"]), "state": str(issued["state"])}


def reject_cartographer_selection(*, preview_id: str, expected_generation: int) -> dict[str, Any]:
    return _call("transition-preview", {"preview_id": preview_id, "expected_generation": str(expected_generation), "state": "rejected"})


def consume_cartographer_selection(*, approval_id: str, proposal_id: str, consumer: str, target: str) -> dict[str, Any]:
    approval = _call("lookup", {"approval_id": approval_id})
    if approval.get("consumer") != CONSUMER:
        raise CartographerSelectionError("cartographer_selection_consumer_mismatch")
    if approval.get("operation") != OPERATION:
        raise CartographerSelectionError("cartographer_selection_operation_mismatch")
    _content, context = _selection(proposal_id=proposal_id, consumer=consumer, target=target)
    binding = {
        "approval_id": approval_id, "generation": str(approval.get("generation") or ""),
        "consumer": CONSUMER, "operation": OPERATION, "repository": "SpiritOS",
        "worktree": ROOT, "root": ROOT, "target": target, "plugin": PLUGIN,
        "preview": approval.get("preview"),
        "content_hash": selection_content_hash(proposal_id=proposal_id, consumer=consumer, target=target),
        "context": context, "source_head": current_head(),
    }
    _call("consume", binding)
    return {"approval_id": approval_id, "generation": int(approval["generation"]), "binding": binding}


def finalize_cartographer_selection(*, consumed: dict[str, Any], proposal_id: str, consumer: str, target: str) -> dict[str, Any]:
    approval_id = str(consumed["approval_id"])
    generation = int(consumed["generation"])
    acknowledgements = {
        name: {"approval_id": approval_id, "generation": generation}
        for name in (CONSUMER, "cartographer-reviewer", "cartographer-verifier", "evidence-recorder")
    }
    binding = dict(consumed["binding"])
    binding.update({
        "result_id": f"cartographer-transfer-{approval_id[-12:]}", "status": "succeeded",
        "source_head": current_head(),
        "evidence": canonical_json({
            "redacted": True, "proposal_id": proposal_id, "consumer": consumer,
            "target": target, "acknowledgements": acknowledgements,
        }),
    })
    receipt = _call("finalize", binding)
    return {"receipt": receipt, "acknowledgements": acknowledgements}
