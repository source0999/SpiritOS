from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import Any

from source_proxy.cartographer.approval_token_runtime import (
    ApprovalTokenValidationResult,
    validate_approval_token_payload as _validate_approval_token_payload,
)
from source_proxy.cartographer.workflow_event_ledger import (
    build_approval_event_preview as _build_approval_event_preview,
)

APPROVAL_TOKEN_CONSUMPTION_PHASE = (
    "Plan 4 Phase 4.1: Approval Token Consumption Preview"
)
APPROVAL_TOKEN_CONSUMPTION_MODE = "preview_only"
APPROVAL_TOKEN_DURABLE_RECORD_DECISION = (
    "blocked_until_explicit_human_approval_for_durable_single_use_storage"
)

REQUIRED_CONSUMPTION_CONTEXT_FIELDS: tuple[str, ...] = (
    "action_class",
    "trust_tier",
    "requested_trust_tier",
    "exact_allowed_files",
    "exact_forbidden_files",
    "expected_head",
    "expected_dirty_tree",
    "rollback",
    "verification",
)

FORBIDDEN_ACTION_CLASSES: tuple[str, ...] = (
    "apply",
    "write",
    "command_execution",
    "workflow_execution",
    "queue_execution",
    "commit",
    "push",
    "branch",
    "worktree",
    "stash",
    "clean",
    "reset",
    "checkout",
    "cleanup",
    "provider_call",
    "worker_dispatch",
)

CONSUMPTION_REASON_MESSAGES: dict[str, str] = {
    "missing_consumption_context": "Consumption preview requires exact context.",
    "missing_requested_action_class": "Requested action class is required.",
    "kill_switch_active": "Kill switch is active; consumption preview fails closed.",
    "missing_consumption_field": "Consumption context is missing a required field.",
    "malformed_consumption_field": "Consumption context field is malformed.",
    "forbidden_action_class": "Requested action class is forbidden.",
    "approved_action_class_forbidden": "Approved action class is forbidden.",
    "action_class_mismatch": "Requested action does not match the context action.",
    "trust_tier_mismatch": "Requested trust tier does not match the context tier.",
    "stale_head": "Current HEAD does not match the expected HEAD.",
    "stale_dirty_tree": "Current dirty tree does not match the expected dirty tree.",
    "empty_exact_allowed_files": "Allowed file list must contain exact files.",
    "wildcard_file_scope": "Allowed file scope cannot use wildcards.",
    "broad_file_scope": "Allowed file scope must be exact file paths.",
    "requested_files_exceed_exact_allowed_files": "Requested files exceed the exact allowed files.",
    "wildcard_forbidden_file_scope": "Forbidden file scope cannot use wildcards.",
    "requested_files_match_forbidden_files": "Requested files intersect forbidden files.",
}


@dataclasses.dataclass(frozen=True)
class ApprovalTokenConsumptionPreview:
    status: str
    eligible: bool
    blocked: bool
    go: bool
    no_go_default: bool
    reasons: tuple[str, ...]
    reason_details: tuple[dict[str, str], ...]
    validation: dict[str, Any]
    approval_event_preview: dict[str, Any]
    requested_actor: str
    requested_scope: dict[str, str]
    requested_action_class: str
    requested_files: tuple[str, ...]
    token_id: str | None
    run_id: str | None
    approver_id: str | None
    operator_id: str | None
    approved_lane_id: str | None
    requested_lane_id: str | None
    approved_action_class: str | None
    approved_trust_tier: str | None
    expected_head: str | None
    current_head: str | None
    expected_dirty_tree: dict[str, Any] | None
    current_dirty_tree: dict[str, Any] | None
    kill_switch_active: bool
    consumption_mode: str = APPROVAL_TOKEN_CONSUMPTION_MODE
    durable_token_storage_available: bool = False
    durable_consumption_record_available: bool = False
    single_use_enforced_by_runtime: bool = False
    token_consumed_for_real: bool = False
    durable_record_decision: str = APPROVAL_TOKEN_DURABLE_RECORD_DECISION
    preview_only: bool = True
    authority_granted: bool = False
    write_authority_granted: bool = False
    command_authority_granted: bool = False
    workflow_authority_granted: bool = False
    queue_authority_granted: bool = False
    git_authority_granted: bool = False
    no_execution_guarantee: str = (
        "Approval token consumption preview only checks whether a token and "
        "request are eligible for later human review. It does not execute, "
        "enqueue, persist, mutate files, or perform version-control actions."
    )
    safe_next_action: str = (
        "Keep this as a preview-only boundary until a later phase explicitly "
        "approves a safe write class."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_approval_token_consumption_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Integrated Control Master Plan 4",
        "phase": APPROVAL_TOKEN_CONSUMPTION_PHASE,
        "status": "preview-only",
        "required_context_fields": REQUIRED_CONSUMPTION_CONTEXT_FIELDS,
        "forbidden_action_classes": FORBIDDEN_ACTION_CLASSES,
        "consumption_mode": APPROVAL_TOKEN_CONSUMPTION_MODE,
        "preview_only": True,
        "no_go_default": True,
        "event_preview_only": True,
        "durable_token_storage_available": False,
        "durable_consumption_record_available": False,
        "single_use_enforced_by_runtime": False,
        "token_consumed_for_real": False,
        "durable_record_decision": APPROVAL_TOKEN_DURABLE_RECORD_DECISION,
        "authority_granted": False,
        "write_authority_granted": False,
        "command_authority_granted": False,
        "workflow_authority_granted": False,
        "queue_authority_granted": False,
        "git_authority_granted": False,
        "safe_next_action": "Preview token consumption only; do not execute or mutate.",
    }


def preview_approval_token_consumption(
    payload: Any,
    *,
    requested_actor: str,
    requested_scope: dict[str, str],
    requested_action_class: str,
    requested_files: list[str] | tuple[str, ...],
    requested_lane_id: str | None = "cartographer",
    consumption_context: dict[str, Any] | None,
    current_head: str | None = None,
    current_dirty_tree: dict[str, Any] | None = None,
    kill_switch_active: bool = False,
    now: datetime | None = None,
) -> ApprovalTokenConsumptionPreview:
    context = consumption_context if isinstance(consumption_context, dict) else {}
    requested_trust_tier = _normalize_string(context.get("requested_trust_tier"))
    validation = _validate_approval_token_payload(
        payload,
        requested_actor=requested_actor,
        requested_scope=requested_scope,
        requested_action_type=requested_action_class,
        requested_lane_id=requested_lane_id,
        requested_files=requested_files,
        current_head=current_head,
        current_dirty_tree=current_dirty_tree,
        kill_switch_active=kill_switch_active,
        requested_trust_tier=requested_trust_tier or None,
        now=now,
    )
    reasons = [f"token_validation:{reason}" for reason in validation.reasons]
    normalized_requested_action = _normalize_string(requested_action_class)
    normalized_requested_files = _normalize_string_tuple(requested_files)

    if not isinstance(consumption_context, dict):
        reasons.append("missing_consumption_context")

    if not normalized_requested_action:
        reasons.append("missing_requested_action_class")

    if kill_switch_active:
        reasons.append("kill_switch_active")

    for field in REQUIRED_CONSUMPTION_CONTEXT_FIELDS:
        if field not in context:
            reasons.append(f"missing_consumption_field:{field}")

    approved_action_class = _string_context_field(context, "action_class", reasons)
    approved_trust_tier = _string_context_field(context, "trust_tier", reasons)
    requested_trust_tier = _string_context_field(context, "requested_trust_tier", reasons)
    expected_head = _string_context_field(context, "expected_head", reasons)
    _string_context_field(context, "rollback", reasons)
    _string_context_field(context, "verification", reasons)
    expected_dirty_tree = _dirty_tree_context_field(context, "expected_dirty_tree", reasons)

    exact_allowed_files = _string_list_context_field(
        context,
        "exact_allowed_files",
        reasons,
    )
    exact_forbidden_files = _string_list_context_field(
        context,
        "exact_forbidden_files",
        reasons,
    )

    if normalized_requested_action in FORBIDDEN_ACTION_CLASSES:
        reasons.append("forbidden_action_class")
    if approved_action_class in FORBIDDEN_ACTION_CLASSES:
        reasons.append("approved_action_class_forbidden")
    if approved_action_class and normalized_requested_action:
        if approved_action_class != normalized_requested_action:
            reasons.append("action_class_mismatch")

    if approved_trust_tier and requested_trust_tier and requested_trust_tier != approved_trust_tier:
        reasons.append("trust_tier_mismatch")

    if expected_head and current_head and expected_head != current_head.strip():
        reasons.append("stale_head")
    if expected_dirty_tree is not None and current_dirty_tree is not None:
        if expected_dirty_tree != current_dirty_tree:
            reasons.append("stale_dirty_tree")

    if exact_allowed_files is not None:
        if not exact_allowed_files and normalized_requested_files:
            reasons.append("empty_exact_allowed_files")
        if "*" in exact_allowed_files:
            reasons.append("wildcard_file_scope")
        if any(item in (".", "./", "/") or item.endswith("/") for item in exact_allowed_files):
            reasons.append("broad_file_scope")
        if not set(normalized_requested_files).issubset(set(exact_allowed_files)):
            reasons.append("requested_files_exceed_exact_allowed_files")

    if exact_forbidden_files is not None:
        if "*" in exact_forbidden_files:
            reasons.append("wildcard_forbidden_file_scope")
        blocked_files = set(normalized_requested_files).intersection(exact_forbidden_files)
        if blocked_files:
            reasons.append("requested_files_match_forbidden_files")

    reasons = _dedupe(reasons)
    eligible = validation.accepted and not reasons
    event_preview = _build_approval_event_preview(
        event_type=_approval_event_type_for_preview(eligible, reasons),
        run_id=validation.run_id or "",
        token_id=validation.token_id or "",
        actor=requested_actor,
        occurred_at=now or datetime.now(UTC),
        approver_id=validation.approver_id,
        operator_id=validation.operator_id,
        action_type=normalized_requested_action,
        reason_codes=reasons,
    )
    return ApprovalTokenConsumptionPreview(
        status="eligible" if eligible else "blocked",
        eligible=eligible,
        blocked=not eligible,
        go=False,
        no_go_default=True,
        reasons=tuple(reasons),
        reason_details=tuple(
            {"code": reason, "message": _reason_message(reason)}
            for reason in reasons
        ),
        validation=validation.to_dict(),
        approval_event_preview=event_preview.to_dict(),
        requested_actor=validation.requested_actor,
        requested_scope=validation.requested_scope,
        requested_action_class=normalized_requested_action,
        requested_files=normalized_requested_files,
        token_id=validation.token_id,
        run_id=validation.run_id,
        approver_id=validation.approver_id,
        operator_id=validation.operator_id,
        approved_lane_id=validation.lane_id,
        requested_lane_id=validation.requested_lane_id,
        approved_action_class=approved_action_class,
        approved_trust_tier=approved_trust_tier,
        expected_head=expected_head,
        current_head=current_head.strip() if current_head else None,
        expected_dirty_tree=expected_dirty_tree,
        current_dirty_tree=current_dirty_tree,
        kill_switch_active=kill_switch_active,
    )


def _string_context_field(
    context: dict[str, Any],
    field: str,
    reasons: list[str],
) -> str | None:
    if field not in context:
        return None
    value = _normalize_string(context[field])
    if not value:
        reasons.append(f"malformed_consumption_field:{field}")
        return None
    return value


def _string_list_context_field(
    context: dict[str, Any],
    field: str,
    reasons: list[str],
) -> tuple[str, ...] | None:
    if field not in context:
        return None
    value = context[field]
    if not isinstance(value, list):
        reasons.append(f"malformed_consumption_field:{field}")
        return None
    normalized = _normalize_string_tuple(value)
    if len(normalized) != len(value):
        reasons.append(f"malformed_consumption_field:{field}")
        return None
    return normalized


def _dirty_tree_context_field(
    context: dict[str, Any],
    field: str,
    reasons: list[str],
) -> dict[str, Any] | None:
    if field not in context:
        return None
    value = context[field]
    if not isinstance(value, dict) or not value:
        reasons.append(f"malformed_consumption_field:{field}")
        return None
    if any(not isinstance(key, str) or not key.strip() for key in value):
        reasons.append(f"malformed_consumption_field:{field}")
        return None
    return value


def _normalize_string_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    normalized: list[str] = []
    for item in value:
        text = _normalize_string(item)
        if text:
            normalized.append(text)
    return tuple(normalized)


def _normalize_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _dedupe(reasons: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        deduped.append(reason)
    return deduped


def _approval_event_type_for_preview(eligible: bool, reasons: list[str]) -> str:
    if eligible:
        return "approval_consumed_preview"
    if any(reason == "token_validation:token_expired" for reason in reasons):
        return "approval_expired"
    if any(reason.startswith("token_validation:") for reason in reasons):
        return "approval_rejected"
    return "approval_blocked"


def _reason_message(reason: str) -> str:
    if reason.startswith("token_validation:"):
        return "Approval token validation failed before consumption preview."
    base_reason = reason.split(":", 1)[0]
    return CONSUMPTION_REASON_MESSAGES.get(
        base_reason,
        "Approval token consumption preview failed closed.",
    )
