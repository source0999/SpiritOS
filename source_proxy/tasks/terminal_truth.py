"""Campaign 1 canonical terminal-truth vocabulary and validators."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any

TERMINAL_TRUTH_SCHEMA = "source-proxy.terminal-truth/v1"

CANONICAL_STATES = (
    "not_started",
    "materialization_failed",
    "not_attempted",
    "running",
    "approval_required",
    "apply_failed",
    "verification_failed",
    "repair_required",
    "blocked_policy",
    "blocked_environment",
    "cancelled",
    "failed",
    "completed",
    "completed_verified",
)

TERMINAL_STATES = frozenset(
    {
        "materialization_failed",
        "not_attempted",
        "apply_failed",
        "verification_failed",
        "repair_required",
        "blocked_policy",
        "blocked_environment",
        "cancelled",
        "failed",
        "completed",
        "completed_verified",
    }
)

# This is intentionally task-level rather than lane-level.  Lanes remain useful
# execution diagnostics, but none of them can independently promote the task to
# verified completion.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "not_started": frozenset({"running", "not_attempted", "materialization_failed", "blocked_policy", "blocked_environment", "cancelled", "failed"}),
    "running": frozenset({"approval_required", "not_attempted", "verification_failed", "repair_required", "blocked_policy", "blocked_environment", "cancelled", "failed", "completed"}),
    "approval_required": frozenset({"running", "apply_failed", "verification_failed", "repair_required", "blocked_policy", "blocked_environment", "cancelled", "failed", "completed", "completed_verified"}),
    "repair_required": frozenset({"running", "blocked_policy", "blocked_environment", "cancelled", "failed"}),
}

VERIFIED_COMPLETION_REQUIRED_ROLES = frozenset(
    {
        "coding-executor",
        "coding-reviewer",
        "coding-verifier",
        "coding-anti-cheat",
        "evidence-recorder",
    }
)

_STATUS_TO_CANONICAL = {
    "queued": "not_started",
    "running": "running",
    "executing": "running",
    "needs_context": "not_attempted",
    "coder_config_blocked": "blocked_environment",
    "blocked": "blocked_policy",
    "blocked_after_retries": "repair_required",
    "blocked_approval_mismatch": "blocked_policy",
    "blocked_by_review": "repair_required",
    "waiting_for_operator_browser": "approval_required",
    "applied": "approval_required",
    "verified": "approval_required",
    "failed_needs_human": "failed",
    "applied_needs_verification": "approval_required",
    "applied_verification_failed": "verification_failed",
    "verification_failed": "verification_failed",
    "verification_passed_pending_participants": "approval_required",
    "cancelled": "cancelled",
    "completed": "completed",
    "completed_verified": "completed_verified",
}


class TerminalTruthError(ValueError):
    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


def canonical_state_for_task_status(status: str) -> str:
    value = str(status or "")
    if value in CANONICAL_STATES:
        return value
    return _STATUS_TO_CANONICAL.get(value, "failed")


def validate_canonical_transition(
    *,
    prior_state: str | None,
    next_state: str,
    terminal_proof_eligible: bool = False,
) -> None:
    """Reject terminal upgrades, stale replays, and unverifiable completion."""

    resolved_next = canonical_state_for_task_status(next_state)
    if resolved_next not in CANONICAL_STATES:
        raise TerminalTruthError("unknown_terminal_truth_state")
    if prior_state is None:
        if resolved_next != "not_started":
            raise TerminalTruthError("canonical_transition_origin_invalid")
        return
    resolved_prior = canonical_state_for_task_status(prior_state)
    if resolved_prior in TERMINAL_STATES:
        if resolved_prior == resolved_next:
            return
        raise TerminalTruthError("sealed_terminal_transition_rejected")
    if resolved_next not in ALLOWED_TRANSITIONS.get(resolved_prior, frozenset()):
        raise TerminalTruthError("canonical_transition_invalid")
    if resolved_next == "completed_verified" and not terminal_proof_eligible:
        raise TerminalTruthError("completed_verified_requires_terminal_proof")


def terminal_truth_payload(
    *,
    status: str,
    actor: str,
    source: str,
    prior_state: str | None = None,
    reason_code: str = "",
    attempt_id: str | None = None,
    coder_invocation_ids: Sequence[str] | None = None,
    artifact_sha256: str | None = None,
    verifier_invocation_id: str | None = None,
    verification_receipt_sha256: str | None = None,
    sidecar_authority: bool = False,
    transition_owner: str = "source_proxy.tasks.long_running",
    verifier_actor: str | None = None,
    terminal_proof_eligible: bool = False,
) -> dict[str, Any]:
    state = canonical_state_for_task_status(status)
    if state == "completed_verified":
        if not artifact_sha256:
            raise TerminalTruthError("completed_verified_artifact_missing")
        if not verifier_invocation_id or not verification_receipt_sha256:
            raise TerminalTruthError("completed_verified_verifier_missing")
        if sidecar_authority:
            raise TerminalTruthError("sidecar_cannot_verify_completion")
        if verifier_actor and verifier_actor == actor:
            raise TerminalTruthError("completed_verified_verifier_not_independent")
    if state == "completed" and verification_receipt_sha256:
        raise TerminalTruthError("completed_must_not_carry_verified_receipt")
    if state not in CANONICAL_STATES:
        raise TerminalTruthError("unknown_terminal_truth_state")
    if prior_state is not None:
        validate_canonical_transition(
            prior_state=prior_state,
            next_state=state,
            terminal_proof_eligible=terminal_proof_eligible,
        )
    body = {
        "schema_version": TERMINAL_TRUTH_SCHEMA,
        "canonical_state": state,
        "task_status": str(status or ""),
        "prior_state": prior_state,
        "actor": actor,
        "source": source,
        "reason_code": reason_code,
        "attempt_id": attempt_id,
        "coder_invocation_ids": list(coder_invocation_ids or []),
        "coder_attempted": bool(coder_invocation_ids),
        "artifact_sha256": artifact_sha256,
        "verifier_invocation_id": verifier_invocation_id,
        "verification_receipt_sha256": verification_receipt_sha256,
        "sidecar_authority": sidecar_authority,
        "transition_owner": transition_owner,
        "verifier_actor": verifier_actor,
        "terminal_proof_eligible": terminal_proof_eligible,
        "terminal": state in TERMINAL_STATES,
    }
    body["truth_sha256"] = _sha256_json(body)
    return body


def verified_completion_truth(
    *,
    task_status: str,
    production_proof: Mapping[str, Any],
    participant_records: Sequence[Mapping[str, Any]],
    artifact: Mapping[str, Any],
    prior_state: str | None = None,
) -> dict[str, Any]:
    if task_status != "completed_verified":
        raise TerminalTruthError("verified_completion_requires_completed_verified")
    if production_proof.get("terminal_proof_eligible") is not True:
        raise TerminalTruthError("production_proof_not_terminal")
    roles = {str(record.get("role") or "") for record in participant_records}
    if roles != VERIFIED_COMPLETION_REQUIRED_ROLES:
        raise TerminalTruthError("verified_completion_participant_set_invalid")
    failed = [
        str(record.get("role") or "")
        for record in participant_records
        if record.get("passed") is not True
    ]
    if failed:
        raise TerminalTruthError("verified_completion_participant_failed")
    verifier = next(
        (record for record in participant_records if record.get("role") == "coding-verifier"),
        None,
    )
    if not isinstance(verifier, Mapping):
        raise TerminalTruthError("verified_completion_verifier_missing")
    artifact_sha256 = str(artifact.get("artifact_sha256") or "")
    if not artifact_sha256:
        raise TerminalTruthError("verified_completion_artifact_missing")
    if str(verifier.get("role") or "") == "coding-executor":
        raise TerminalTruthError("verified_completion_verifier_not_independent")
    return terminal_truth_payload(
        status=task_status,
        actor="source_proxy.coding.orchestrator",
        source="independent_participant_finalization",
        prior_state=prior_state,
        reason_code="independent_verification_and_evidence_passed",
        attempt_id=str(artifact.get("attempt_id") or artifact.get("run_id") or ""),
        coder_invocation_ids=[
            str(record.get("invocation_id") or "")
            for record in participant_records
            if record.get("role") == "coding-executor"
        ],
        artifact_sha256=artifact_sha256,
        verifier_invocation_id=str(verifier.get("invocation_id") or ""),
        verification_receipt_sha256=str(production_proof.get("proof_sha256") or ""),
        transition_owner="source_proxy.coding.orchestrator",
        verifier_actor="coding-verifier",
        terminal_proof_eligible=True,
    )


def reject_report_upgrade(
    *,
    producer_state: str,
    requested_state: str,
    source: str,
) -> dict[str, Any]:
    producer = canonical_state_for_task_status(producer_state)
    requested = canonical_state_for_task_status(requested_state)
    if requested == "completed_verified" and producer != "completed_verified":
        return terminal_truth_payload(
            status=producer_state,
            actor="source_proxy.terminal_truth",
            source=source,
            reason_code="report_upgrade_rejected",
        )
    return terminal_truth_payload(
        status=requested_state,
        actor="source_proxy.terminal_truth",
        source=source,
        prior_state=producer,
        reason_code="report_preserved_authoritative_state",
    )


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def terminal_truth_is_valid(payload: Mapping[str, Any]) -> bool:
    """Verify the sealed digest before a receipt is reused after restart."""

    body = dict(payload)
    declared = str(body.pop("truth_sha256", ""))
    if not declared or declared != _sha256_json(body):
        return False
    try:
        expected = terminal_truth_payload(
            status=str(body.get("task_status") or ""),
            actor=str(body.get("actor") or ""),
            source=str(body.get("source") or ""),
            prior_state=(
                str(body["prior_state"])
                if body.get("prior_state") is not None
                else None
            ),
            reason_code=str(body.get("reason_code") or ""),
            attempt_id=str(body.get("attempt_id") or "") or None,
            coder_invocation_ids=[str(item) for item in body.get("coder_invocation_ids") or []],
            artifact_sha256=str(body.get("artifact_sha256") or "") or None,
            verifier_invocation_id=str(body.get("verifier_invocation_id") or "") or None,
            verification_receipt_sha256=(
                str(body.get("verification_receipt_sha256") or "") or None
            ),
            sidecar_authority=bool(body.get("sidecar_authority")),
            transition_owner=str(body.get("transition_owner") or ""),
            verifier_actor=str(body.get("verifier_actor") or "") or None,
            terminal_proof_eligible=bool(body.get("terminal_proof_eligible")),
        )
    except (TerminalTruthError, TypeError):
        return False
    expected_body = dict(expected)
    expected_body.pop("truth_sha256", None)
    return expected_body == body
