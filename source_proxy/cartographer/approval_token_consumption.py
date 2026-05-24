from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Any

from source_proxy.cartographer.approval_token_runtime import (
    ApprovalTokenValidationResult,
    validate_approval_token_payload as _validate_approval_token_payload,
)

APPROVAL_TOKEN_CONSUMPTION_PHASE = (
    "Plan 2 Phase 2: Approval Token Consumption Boundary"
)

REQUIRED_CONSUMPTION_CONTEXT_FIELDS: tuple[str, ...] = (
    "action_class",
    "trust_tier",
    "exact_allowed_files",
    "exact_forbidden_files",
    "expected_head",
    "rollback",
    "verification",
)

FORBIDDEN_ACTION_CLASSES: tuple[str, ...] = (
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
)


@dataclasses.dataclass(frozen=True)
class ApprovalTokenConsumptionPreview:
    status: str
    eligible: bool
    blocked: bool
    reasons: tuple[str, ...]
    validation: dict[str, Any]
    requested_actor: str
    requested_scope: dict[str, str]
    requested_action_class: str
    requested_files: tuple[str, ...]
    approved_action_class: str | None
    approved_trust_tier: str | None
    expected_head: str | None
    current_head: str | None
    kill_switch_active: bool
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
        "plan": "Cartographer Daily Driver Autonomy Roadmap Plan 2",
        "phase": APPROVAL_TOKEN_CONSUMPTION_PHASE,
        "status": "preview-only",
        "required_context_fields": REQUIRED_CONSUMPTION_CONTEXT_FIELDS,
        "forbidden_action_classes": FORBIDDEN_ACTION_CLASSES,
        "preview_only": True,
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
    consumption_context: dict[str, Any] | None,
    current_head: str | None = None,
    kill_switch_active: bool = False,
    now: datetime | None = None,
) -> ApprovalTokenConsumptionPreview:
    validation = _validate_approval_token_payload(
        payload,
        requested_actor=requested_actor,
        requested_scope=requested_scope,
        now=now,
    )
    reasons = [f"token_validation:{reason}" for reason in validation.reasons]
    normalized_requested_action = _normalize_string(requested_action_class)
    normalized_requested_files = _normalize_string_tuple(requested_files)
    context = consumption_context if isinstance(consumption_context, dict) else {}

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
    expected_head = _string_context_field(context, "expected_head", reasons)
    _string_context_field(context, "rollback", reasons)
    _string_context_field(context, "verification", reasons)

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

    if approved_trust_tier and normalized_requested_action:
        requested_trust_tier = _normalize_string(context.get("requested_trust_tier"))
        if requested_trust_tier and requested_trust_tier != approved_trust_tier:
            reasons.append("trust_tier_mismatch")

    if expected_head and current_head and expected_head != current_head.strip():
        reasons.append("stale_head")

    if exact_allowed_files is not None:
        if not exact_allowed_files and normalized_requested_files:
            reasons.append("empty_exact_allowed_files")
        if "*" in exact_allowed_files:
            reasons.append("wildcard_file_scope")
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
    return ApprovalTokenConsumptionPreview(
        status="eligible" if eligible else "blocked",
        eligible=eligible,
        blocked=not eligible,
        reasons=tuple(reasons),
        validation=validation.to_dict(),
        requested_actor=validation.requested_actor,
        requested_scope=validation.requested_scope,
        requested_action_class=normalized_requested_action,
        requested_files=normalized_requested_files,
        approved_action_class=approved_action_class,
        approved_trust_tier=approved_trust_tier,
        expected_head=expected_head,
        current_head=current_head.strip() if current_head else None,
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
