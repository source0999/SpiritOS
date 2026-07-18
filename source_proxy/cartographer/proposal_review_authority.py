"""Canonical authenticated authority for Cartographer proposal reviews.

Cartographer remains proposal-only: this module may transition one persisted
proposal record, but it cannot apply the proposal, modify a blueprint target,
commit, push, or select a downstream executor.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any, Literal
from uuid import uuid4

from source_proxy.approval.campaign_authority import (
    REPOSITORY,
    ROOT,
    CampaignApprovalError,
    _call,
    canonical_json,
    current_head,
)
from source_proxy.cartographer.project_discovery import discover_projects
from source_proxy.cartographer.proposals import PROPOSAL_STATES


ReviewDecision = Literal["approve", "reject", "request_edit", "defer", "mark_stale"]
REVIEW_DECISIONS = {"approve", "reject", "request_edit", "defer", "mark_stale"}
REVIEWABLE_STATES = {"detected", "drafted", "pending_review"}
AUTHORITY = "spiritos-approval-authority"
CONSUMER = "cartographer-transfer-consumer"
OPERATION = "cartographer_selection_transfer"
PLUGIN = "cartographer-transfer"
REVIEW_SCHEMA = "cartographer-proposal-review/v2"
SERVER_ACTOR = "spiritos-local-operator"


class CartographerProposalReviewError(ValueError):
    def __init__(self, message: str, reason_code: str):
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True)
class PersistedProposal:
    project_id: str
    project_root: Path
    proposal_root: Path
    path: Path
    payload: dict[str, Any]
    snapshot_hash: str


@dataclass
class ProposalRecordTransaction:
    source_path: Path
    target_path: Path
    source_bytes: bytes
    target_bytes: bytes
    active: bool = True

    def rollback(self) -> None:
        if not self.active:
            return
        _atomic_write(self.source_path, self.source_bytes)
        if self.target_path != self.source_path:
            self.target_path.unlink(missing_ok=True)
        self.active = False

    def commit(self) -> None:
        self.active = False


def operator_action_for_decision(decision: str) -> Literal["approve", "reject"]:
    _validate_decision(decision)
    return "approve" if decision == "approve" else "reject"


def persist_cartographer_proposal_review_preview(
    *,
    proposal_id: str,
    decision: ReviewDecision,
    reason: str | None = None,
) -> dict[str, Any]:
    """Persist an immutable server-authored review plan in canonical authority."""
    _validate_decision(decision)
    proposal = _load_persisted_proposal(proposal_id)
    normalized_reason = _review_reason(decision, reason)
    plan = _build_review_plan(proposal, decision=decision, reason=normalized_reason)
    try:
        persisted = _call(
            "persist-preview",
            {
                "repository": REPOSITORY,
                "worktree": ROOT,
                "root": ROOT,
                "target": str(plan["target"]),
                "plugin": PLUGIN,
                "content_hash": _review_content_hash(plan),
                "context": canonical_json(plan),
                "source_head": current_head(),
            },
        )
    except CampaignApprovalError as error:
        raise _approval_error(error) from error
    generation = int(persisted.get("generation") or 0)
    if generation != int(plan["generation"]):
        raise CartographerProposalReviewError(
            "Canonical review preview generation did not match the server-authored plan.",
            "proposal_review_generation_mismatch",
        )
    return {
        "status": "review_previewed",
        "authority": AUTHORITY,
        "cartographer_identity": "cartographer-proposal-only",
        "preview": {
            "preview_id": str(persisted["preview_id"]),
            "generation": generation,
            "state": str(persisted.get("state") or "previewed"),
        },
        "binding": _public_binding(plan),
        "write_authority": False,
        "approval_issuer_authority": False,
        "apply_authority": False,
        "git_authority": False,
    }


def execute_cartographer_proposal_review(
    *,
    proposal_id: str,
    decision: ReviewDecision,
    preview_id: str,
    generation: int,
    operator: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """Consume approval, replace one proposal record, verify, and finalize."""
    _validate_decision(decision)
    if operator != SERVER_ACTOR:
        raise CartographerProposalReviewError(
            "Proposal review requires the authenticated local operator.",
            "proposal_review_operator_mismatch",
        )
    normalized_reason = _review_reason(decision, reason)
    plan, preview = _load_bound_plan(preview_id, generation)
    _validate_request_against_plan(
        plan,
        proposal_id=proposal_id,
        decision=decision,
        reason=normalized_reason,
        generation=generation,
    )
    proposal = _load_persisted_proposal(proposal_id)
    _validate_snapshot_against_plan(proposal, plan)

    issued: dict[str, Any] | None = None
    binding: dict[str, Any] | None = None
    transaction: ProposalRecordTransaction | None = None
    finalized = False
    try:
        issued = _call(
            "issue",
            {
                "preview_id": preview_id,
                "expected_generation": str(generation),
                "consumer": CONSUMER,
                "operation": OPERATION,
                "expires_at": (datetime.now(UTC) + timedelta(minutes=5)).isoformat(),
            },
        )
        approval_id = str(issued["approval_id"])
        if int(issued.get("generation") or 0) != generation:
            raise CartographerProposalReviewError(
                "Issued review approval generation changed.",
                "proposal_review_generation_mismatch",
            )
        binding = {
            "approval_id": approval_id,
            "generation": str(generation),
            "consumer": CONSUMER,
            "operation": OPERATION,
            "repository": REPOSITORY,
            "worktree": ROOT,
            "root": ROOT,
            "target": str(plan["target"]),
            "plugin": PLUGIN,
            "preview": preview_id,
            "content_hash": _review_content_hash(plan),
            "context": canonical_json(plan),
            "source_head": current_head(),
        }
        consuming = _call("consume", binding)
        if consuming.get("state") != "consuming":
            raise CartographerProposalReviewError(
                "Review approval did not enter consuming state.",
                "proposal_review_not_consuming",
            )

        review_invocation = _invoke_independent_review(plan, proposal)
        result_payload = deepcopy(plan["result_payload"])
        _validate_planned_result(result_payload, plan)
        target_path = Path(str(plan["target"]))
        transaction = _transactional_replace(
            proposal.path,
            target_path,
            result_payload,
            expected_snapshot_hash=str(plan["proposal_snapshot_hash"]),
        )
        verification_invocation = _invoke_independent_verification(
            plan,
            transaction=transaction,
        )
        evidence_invocation = _invoke_evidence_recording(plan, transaction=transaction)
        _validate_invocation_set(
            plan,
            review_invocation,
            verification_invocation,
            evidence_invocation,
        )
        evidence = {
            "schema": REVIEW_SCHEMA,
            "redacted": True,
            "proposal_id": proposal_id,
            "proposal_snapshot_hash": plan["proposal_snapshot_hash"],
            "review_artifact_hash": plan["review_artifact_hash"],
            "result_hash": plan["result_hash"],
            "invocation_ids": [
                review_invocation["invocation_id"],
                verification_invocation["invocation_id"],
                evidence_invocation["invocation_id"],
            ],
        }
        finalized_receipt = _call(
            "finalize",
            {
                **binding,
                "result_id": str(plan["result_id"]),
                "evidence": canonical_json(evidence),
                "status": "succeeded",
                "source_head": current_head(),
            },
        )
        if finalized_receipt.get("state") != "consumed":
            raise CartographerProposalReviewError(
                "Review approval did not finalize as consumed.",
                "proposal_review_finalization_failed",
            )
        finalized = True
        transaction.commit()
    except CartographerProposalReviewError:
        if transaction is not None:
            transaction.rollback()
        if binding is not None and not finalized:
            _best_effort_invalidate(binding, plan, "proposal_review_failed")
        raise
    except (CampaignApprovalError, OSError, KeyError, TypeError, ValueError) as error:
        if transaction is not None:
            transaction.rollback()
        if binding is not None and not finalized:
            _best_effort_invalidate(binding, plan, "proposal_review_failed")
        if isinstance(error, CampaignApprovalError):
            raise _approval_error(error) from error
        raise CartographerProposalReviewError(
            "Proposal review failed and any provisional record replacement was rolled back.",
            "proposal_review_failed_rolled_back",
        ) from error

    return {
        "status": "review_recorded",
        "authority": AUTHORITY,
        "cartographer_identity": "cartographer-proposal-only",
        "max_authority": "proposal_review_record_only",
        "proposal": result_payload,
        "decision": decision,
        "approval_id": str(issued["approval_id"]),
        "generation": generation,
        "proposal_snapshot_hash": plan["proposal_snapshot_hash"],
        "review_artifact_hash": plan["review_artifact_hash"],
        "result_hash": plan["result_hash"],
        "invocations": [
            review_invocation,
            verification_invocation,
            evidence_invocation,
        ],
        "write_actions_enabled": False,
        "actions_taken": False,
        "apply_ran": False,
        "commit_ran": False,
        "push_ran": False,
    }


def _build_review_plan(
    proposal: PersistedProposal,
    *,
    decision: ReviewDecision,
    reason: str,
) -> dict[str, Any]:
    expected_state = str(proposal.payload.get("status") or "")
    if expected_state not in REVIEWABLE_STATES:
        raise CartographerProposalReviewError(
            "Persisted proposal is not in a reviewable state.",
            "proposal_review_state_invalid",
        )
    expected_result_state = _status_for_decision(decision)
    target = _proposal_target(proposal, expected_result_state)
    if target.exists() and target != proposal.path:
        raise CartographerProposalReviewError(
            "The server-owned proposal review target is already occupied.",
            "proposal_review_target_occupied",
        )
    reviewed_at = _now_timestamp()
    artifact = {
        "schema": REVIEW_SCHEMA,
        "proposal_id": str(proposal.payload["proposal_id"]),
        "project_id": proposal.project_id,
        "proposal_snapshot_hash": proposal.snapshot_hash,
        "decision": decision,
        "reason": reason,
        "source": str(proposal.path),
        "target": str(target),
        "expected_state": expected_state,
        "expected_result_state": expected_result_state,
        "generation": 1,
    }
    review_artifact_hash = _hash(artifact)
    invocation_records = [
        {
            "invocation_id": f"cart-review-{uuid4().hex}",
            "output_id": f"cart-review-output-{uuid4().hex}",
            "consumer_acknowledgement_id": f"cart-review-ack-{uuid4().hex}",
            "role": "cartographer-reviewer",
            "kind": "independent_review",
            "artifact_hash": review_artifact_hash,
            "artifact_sha256": review_artifact_hash,
            "status": "succeeded",
        },
        {
            "invocation_id": f"cart-verify-{uuid4().hex}",
            "output_id": f"cart-verify-output-{uuid4().hex}",
            "consumer_acknowledgement_id": f"cart-verify-ack-{uuid4().hex}",
            "role": "cartographer-verifier",
            "kind": "independent_verification",
            "artifact_hash": review_artifact_hash,
            "artifact_sha256": review_artifact_hash,
            "status": "succeeded",
        },
        {
            "invocation_id": f"cart-evidence-{uuid4().hex}",
            "output_id": f"cart-evidence-output-{uuid4().hex}",
            "consumer_acknowledgement_id": f"cart-evidence-ack-{uuid4().hex}",
            "role": "evidence-recorder",
            "kind": "evidence_recording",
            "artifact_hash": review_artifact_hash,
            "artifact_sha256": review_artifact_hash,
            "status": "succeeded",
        },
    ]
    result_payload = _result_payload(
        proposal,
        decision=decision,
        reason=reason,
        expected_result_state=expected_result_state,
        reviewed_at=reviewed_at,
        review_artifact_hash=review_artifact_hash,
        invocation_records=invocation_records,
    )
    result_hash = _result_hash(result_payload)
    result_payload["proposal_review_authority"]["result_hash"] = result_hash
    return {
        **artifact,
        "review_artifact_hash": review_artifact_hash,
        "result_hash": result_hash,
        "result_id": f"cartographer-review-result-{uuid4().hex}",
        "invocation_records": invocation_records,
        "result_payload": result_payload,
    }


def _result_payload(
    proposal: PersistedProposal,
    *,
    decision: ReviewDecision,
    reason: str,
    expected_result_state: str,
    reviewed_at: str,
    review_artifact_hash: str,
    invocation_records: list[dict[str, str]],
) -> dict[str, Any]:
    payload = deepcopy(proposal.payload)
    payload.update(
        {
            "proposal_id": str(proposal.payload["proposal_id"]),
            "project_id": proposal.project_id,
            "status": expected_result_state,
            "generated": False,
            "persisted": True,
            "deduped": True,
            "applied": False,
            "action_taken": False,
            "transitions": [
                *_safe_transitions(payload.get("transitions")),
                {
                    "status": "approved" if decision == "approve" else expected_result_state,
                    "timestamp": reviewed_at,
                    "actor": SERVER_ACTOR,
                },
            ],
            "proposal_review_authority": {
                "schema": REVIEW_SCHEMA,
                "actor": SERVER_ACTOR,
                "decision": decision,
                "reason": reason,
                "generation": 1,
                "proposal_snapshot_hash": proposal.snapshot_hash,
                "review_artifact_hash": review_artifact_hash,
                "invocations": invocation_records,
            },
        }
    )
    if decision == "approve":
        payload.update(
            {
                "approved_by": SERVER_ACTOR,
                "approved_at": reviewed_at,
                "approved_diff": str(payload.get("approved_diff") or payload.get("diff_preview") or ""),
            }
        )
    elif decision == "reject":
        payload.update(
            {
                "rejected_by": SERVER_ACTOR,
                "rejected_at": reviewed_at,
                "rejection_reason": reason,
            }
        )
    elif decision == "defer":
        payload.update(
            {
                "deferred_by": SERVER_ACTOR,
                "deferred_at": reviewed_at,
                "review_note": reason,
            }
        )
    elif decision == "mark_stale":
        payload.update(
            {
                "marked_stale_by": SERVER_ACTOR,
                "marked_stale_at": reviewed_at,
                "review_note": reason,
            }
        )
    else:
        payload["review_note"] = reason
    return payload


def _load_bound_plan(preview_id: str, generation: int) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        preview = _call("lookup-preview", {"preview_id": preview_id})
    except CampaignApprovalError as error:
        raise _approval_error(error) from error
    if int(preview.get("generation") or 0) != generation:
        raise CartographerProposalReviewError(
            "Proposal review preview generation mismatch.",
            "proposal_review_generation_mismatch",
        )
    if preview.get("state") != "previewed":
        raise CartographerProposalReviewError(
            "Proposal review preview is no longer reviewable.",
            "proposal_review_preview_not_active",
        )
    if (
        preview.get("repository") != REPOSITORY
        or preview.get("worktree") != ROOT
        or os.path.realpath(str(preview.get("root") or "")) != os.path.realpath(ROOT)
        or preview.get("plugin") != PLUGIN
        or preview.get("source_head") != current_head()
    ):
        raise CartographerProposalReviewError(
            "Proposal review preview authority identity changed.",
            "proposal_review_authority_mismatch",
        )
    try:
        plan = json.loads(str(preview["context_hash"]))
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise CartographerProposalReviewError(
            "Proposal review preview context is invalid.",
            "proposal_review_context_invalid",
        ) from error
    if not isinstance(plan, dict) or plan.get("schema") != REVIEW_SCHEMA:
        raise CartographerProposalReviewError(
            "Proposal review preview schema is invalid.",
            "proposal_review_context_invalid",
        )
    if str(preview.get("target") or "") != str(plan.get("target") or ""):
        raise CartographerProposalReviewError(
            "Proposal review target binding changed.",
            "proposal_review_target_mismatch",
        )
    if str(preview.get("content_hash") or "") != _review_content_hash(plan):
        raise CartographerProposalReviewError(
            "Proposal review content binding changed.",
            "proposal_review_content_hash_mismatch",
        )
    return plan, preview


def _validate_request_against_plan(
    plan: dict[str, Any],
    *,
    proposal_id: str,
    decision: str,
    reason: str,
    generation: int,
) -> None:
    supplied = {
        "proposal_id": proposal_id,
        "decision": decision,
        "reason": reason,
        "generation": generation,
    }
    for field, value in supplied.items():
        if plan.get(field) != value:
            raise CartographerProposalReviewError(
                f"Proposal review {field} changed after preview.",
                f"proposal_review_{field}_mismatch",
            )


def _validate_snapshot_against_plan(proposal: PersistedProposal, plan: dict[str, Any]) -> None:
    checks = {
        "proposal_snapshot_hash": proposal.snapshot_hash,
        "expected_state": str(proposal.payload.get("status") or ""),
        "source": str(proposal.path),
        "target": str(_proposal_target(proposal, str(plan["expected_result_state"]))),
    }
    for field, actual in checks.items():
        if str(plan.get(field) or "") != actual:
            raise CartographerProposalReviewError(
                "Persisted proposal changed after review preview.",
                "proposal_review_snapshot_drift",
            )


def _load_persisted_proposal(proposal_id: str) -> PersistedProposal:
    matches: list[PersistedProposal] = []
    for project in discover_projects():
        project_root = Path(project.root).resolve()
        proposal_root = (project_root / "_blueprints" / "proposals").resolve()
        if not proposal_root.is_dir():
            continue
        try:
            paths = sorted(proposal_root.rglob("*.json"))
        except OSError:
            continue
        for path in paths:
            if not path.is_file():
                continue
            resolved = path.resolve()
            try:
                resolved.relative_to(proposal_root)
                payload = json.loads(resolved.read_text(encoding="utf-8"))
            except (ValueError, OSError, json.JSONDecodeError):
                continue
            if not isinstance(payload, dict) or str(payload.get("proposal_id") or "") != proposal_id:
                continue
            matches.append(
                PersistedProposal(
                    project_id=str(project.project_id),
                    project_root=project_root,
                    proposal_root=proposal_root,
                    path=resolved,
                    payload=payload,
                    snapshot_hash=_hash(payload),
                )
            )
    if not matches:
        raise CartographerProposalReviewError(
            "Persisted proposal was not found; caller snapshots are not accepted.",
            "persisted_proposal_not_found",
        )
    if len(matches) != 1:
        raise CartographerProposalReviewError(
            "Proposal identifier is not unique across persisted projects.",
            "persisted_proposal_ambiguous",
        )
    return matches[0]


def _transactional_replace(
    source_path: Path,
    target_path: Path,
    payload: dict[str, Any],
    *,
    expected_snapshot_hash: str,
) -> ProposalRecordTransaction:
    target_bytes = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    source_bytes = source_path.read_bytes()
    try:
        source_payload = json.loads(source_bytes)
    except json.JSONDecodeError as error:
        raise CartographerProposalReviewError(
            "Persisted proposal changed after approval entered consuming state.",
            "proposal_review_snapshot_drift",
        ) from error
    if not isinstance(source_payload, dict) or _hash(source_payload) != expected_snapshot_hash:
        raise CartographerProposalReviewError(
            "Persisted proposal changed after approval entered consuming state.",
            "proposal_review_snapshot_drift",
        )
    if target_path.exists() and target_path != source_path:
        raise CartographerProposalReviewError(
            "Proposal review target became occupied before replacement.",
            "proposal_review_target_occupied",
        )
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = _write_temporary(target_path.parent, target_bytes)
    try:
        os.replace(temporary, target_path)
        if source_path != target_path:
            source_path.unlink()
    except OSError:
        Path(temporary).unlink(missing_ok=True)
        if target_path.exists() and target_path != source_path:
            target_path.unlink(missing_ok=True)
        _atomic_write(source_path, source_bytes)
        raise
    return ProposalRecordTransaction(
        source_path=source_path,
        target_path=target_path,
        source_bytes=source_bytes,
        target_bytes=target_bytes,
    )


def _invoke_independent_review(
    plan: dict[str, Any],
    proposal: PersistedProposal,
) -> dict[str, str]:
    record = _invocation(plan, "independent_review")
    if proposal.snapshot_hash != plan["proposal_snapshot_hash"]:
        raise CartographerProposalReviewError(
            "Independent review detected proposal drift.",
            "proposal_review_snapshot_drift",
        )
    return record


def _invoke_independent_verification(
    plan: dict[str, Any],
    *,
    transaction: ProposalRecordTransaction,
) -> dict[str, str]:
    record = _invocation(plan, "independent_verification")
    if (
        not transaction.target_path.is_file()
        or transaction.target_path.read_bytes() != transaction.target_bytes
        or (transaction.source_path != transaction.target_path and transaction.source_path.exists())
    ):
        raise CartographerProposalReviewError(
            "Independent verification rejected the proposal record replacement.",
            "proposal_review_verification_failed",
        )
    try:
        payload = json.loads(transaction.target_bytes)
    except json.JSONDecodeError as error:
        raise CartographerProposalReviewError(
            "Independent verification could not parse the proposal result.",
            "proposal_review_verification_failed",
        ) from error
    _validate_planned_result(payload, plan)
    return record


def _invoke_evidence_recording(
    plan: dict[str, Any],
    *,
    transaction: ProposalRecordTransaction,
) -> dict[str, str]:
    record = _invocation(plan, "evidence_recording")
    if not transaction.target_path.is_file() or record["artifact_hash"] != plan["review_artifact_hash"]:
        raise CartographerProposalReviewError(
            "Evidence invocation could not bind the reviewed artifact.",
            "proposal_review_evidence_failed",
        )
    return record


def _validate_invocation_set(plan: dict[str, Any], *records: dict[str, str]) -> None:
    invocation_ids = {record["invocation_id"] for record in records}
    output_ids = {record["output_id"] for record in records}
    acknowledgement_ids = {record["consumer_acknowledgement_id"] for record in records}
    if (
        len(invocation_ids) != 3
        or len(output_ids) != 3
        or len(acknowledgement_ids) != 3
        or any(
            record["artifact_hash"] != plan["review_artifact_hash"]
            or record["artifact_sha256"] != plan["review_artifact_hash"]
            for record in records
        )
    ):
        raise CartographerProposalReviewError(
            "Review, verification, and evidence invocations were not independent and artifact-bound.",
            "proposal_review_invocation_binding_failed",
        )


def _invocation(plan: dict[str, Any], kind: str) -> dict[str, str]:
    records = plan.get("invocation_records")
    if not isinstance(records, list):
        raise CartographerProposalReviewError(
            "Review invocation plan is invalid.",
            "proposal_review_context_invalid",
        )
    record = next(
        (
            item
            for item in records
            if isinstance(item, dict) and item.get("kind") == kind
        ),
        None,
    )
    if not isinstance(record, dict):
        raise CartographerProposalReviewError(
            "Review invocation record is missing.",
            "proposal_review_context_invalid",
        )
    return {str(key): str(value) for key, value in record.items()}


def _validate_planned_result(payload: dict[str, Any], plan: dict[str, Any]) -> None:
    if _result_hash(payload) != plan.get("result_hash"):
        raise CartographerProposalReviewError(
            "Server-authored proposal review result hash changed.",
            "proposal_review_result_hash_mismatch",
        )
    authority = payload.get("proposal_review_authority")
    if not isinstance(authority, dict) or authority.get("result_hash") != plan.get("result_hash"):
        raise CartographerProposalReviewError(
            "Proposal review result binding is missing.",
            "proposal_review_result_hash_mismatch",
        )


def _review_content_hash(plan: dict[str, Any]) -> str:
    return _hash(
        {
            field: plan[field]
            for field in (
                "schema",
                "proposal_id",
                "project_id",
                "proposal_snapshot_hash",
                "decision",
                "reason",
                "source",
                "target",
                "expected_state",
                "expected_result_state",
                "result_hash",
                "generation",
            )
        }
    )


def _result_hash(payload: dict[str, Any]) -> str:
    value = deepcopy(payload)
    authority = value.get("proposal_review_authority")
    if isinstance(authority, dict):
        authority.pop("result_hash", None)
    return _hash(value)


def _hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _proposal_target(proposal: PersistedProposal, status: str) -> Path:
    normalized = status if status in PROPOSAL_STATES else "drafted"
    target = (proposal.proposal_root / normalized / f"{proposal.payload['proposal_id']}.json").resolve()
    try:
        target.relative_to(proposal.proposal_root)
    except ValueError as error:
        raise CartographerProposalReviewError(
            "Server-owned proposal target escaped the proposal root.",
            "proposal_review_target_invalid",
        ) from error
    return target


def _status_for_decision(decision: ReviewDecision) -> str:
    return {
        "approve": "approved",
        "reject": "rejected",
        "request_edit": "drafted",
        "defer": "deferred",
        "mark_stale": "stale",
    }[decision]


def _review_reason(decision: ReviewDecision, reason: str | None) -> str:
    normalized = str(reason or "").strip()
    if normalized:
        return normalized
    return {
        "approve": "Approved by the authenticated local operator.",
        "reject": "Rejected by the authenticated local operator.",
        "request_edit": "Edit requested by the authenticated local operator.",
        "defer": "Deferred by the authenticated local operator.",
        "mark_stale": "Marked stale by the authenticated local operator.",
    }[decision]


def _validate_decision(decision: str) -> None:
    if decision not in REVIEW_DECISIONS:
        raise CartographerProposalReviewError(
            "Unknown proposal review decision.",
            "invalid_review_decision",
        )


def _safe_transitions(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    return [
        {
            "status": str(item["status"]),
            "timestamp": str(item["timestamp"]),
            "actor": str(item["actor"]),
        }
        for item in value
        if isinstance(item, dict)
        and item.get("status")
        and item.get("timestamp")
        and item.get("actor")
    ]


def _public_binding(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        field: plan[field]
        for field in (
            "proposal_id",
            "project_id",
            "proposal_snapshot_hash",
            "decision",
            "reason",
            "target",
            "expected_state",
            "expected_result_state",
            "result_hash",
            "generation",
        )
    }


def _best_effort_invalidate(
    binding: dict[str, Any],
    plan: dict[str, Any],
    reason: str,
) -> None:
    try:
        _call(
            "finalize",
            {
                **binding,
                "result_id": f"{plan['result_id']}-failed",
                "evidence": canonical_json(
                    {
                        "redacted": True,
                        "proposal_id": plan["proposal_id"],
                        "reason": reason,
                        "result_hash": plan["result_hash"],
                    }
                ),
                "status": "failed",
                "source_head": current_head(),
            },
        )
    except (CampaignApprovalError, OSError, KeyError, TypeError, ValueError):
        return


def _approval_error(error: CampaignApprovalError) -> CartographerProposalReviewError:
    reason = str(getattr(error, "reason_code", "") or str(error) or "approval_issuer_unavailable")
    return CartographerProposalReviewError(
        "Canonical approval authority rejected the proposal review lifecycle.",
        reason,
    )


def _write_temporary(directory: Path, content: bytes) -> str:
    descriptor, temporary = tempfile.mkstemp(
        prefix=".cartographer-review-",
        suffix=".tmp",
        dir=directory,
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise
    return temporary


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = _write_temporary(path.parent, content)
    os.replace(temporary, path)


def _now_timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
