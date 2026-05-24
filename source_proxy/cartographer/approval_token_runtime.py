from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta
from typing import Any

APPROVAL_TOKEN_SCHEMA_VERSION = "cartographer.approval-token.v1"
APPROVAL_TOKEN_MAX_AGE = timedelta(hours=24)

REQUIRED_APPROVAL_TOKEN_FIELDS: tuple[str, ...] = (
    "schema_version",
    "token_id",
    "issued_at",
    "expires_at",
    "approved_by",
    "approved_for_actor",
    "scope",
    "reason",
)

SCOPE_REQUIRED_FIELDS: tuple[str, ...] = ("type", "value")


@dataclasses.dataclass(frozen=True)
class ApprovalTokenValidationResult:
    status: str
    accepted: bool
    rejected: bool
    reasons: tuple[str, ...]
    validated_at: str
    approval_actor: str | None
    approved_for_actor: str | None
    requested_actor: str
    token_scope: dict[str, str] | None
    requested_scope: dict[str, str]
    authority_granted: bool = False
    write_authority_granted: bool = False
    command_authority_granted: bool = False
    workflow_authority_granted: bool = False
    queue_authority_granted: bool = False
    git_authority_granted: bool = False
    validation_only: bool = True
    no_mutation_guarantee: str = (
        "Approval token validation is pure data validation only; it does not "
        "write files, run commands, execute queues, or perform git operations."
    )
    safe_next_action: str = "Require explicit human review before any later authority expansion."

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_approval_token_runtime_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Daily Driver Autonomy Roadmap Plan 2",
        "phase": "Plan 2 Phase 1: Approval Token Runtime",
        "status": "validation-only",
        "schema_version": APPROVAL_TOKEN_SCHEMA_VERSION,
        "required_fields": REQUIRED_APPROVAL_TOKEN_FIELDS,
        "scope_required_fields": SCOPE_REQUIRED_FIELDS,
        "max_token_age_seconds": int(APPROVAL_TOKEN_MAX_AGE.total_seconds()),
        "authority_granted": False,
        "write_authority_granted": False,
        "command_authority_granted": False,
        "workflow_authority_granted": False,
        "queue_authority_granted": False,
        "git_authority_granted": False,
        "self_approval_allowed": False,
        "validation_only": True,
        "safe_next_action": "Validate payload shape only; do not execute or mutate.",
    }


def validate_approval_token_payload(
    payload: Any,
    *,
    requested_actor: str,
    requested_scope: dict[str, str],
    now: datetime | None = None,
) -> ApprovalTokenValidationResult:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []
    approval_actor: str | None = None
    approved_for_actor: str | None = None
    token_scope: dict[str, str] | None = None

    requested_actor = requested_actor.strip() if requested_actor else ""
    if not requested_actor:
        reasons.append("missing_requested_actor")

    normalized_requested_scope = _normalize_scope(requested_scope)
    if normalized_requested_scope is None:
        reasons.append("malformed_requested_scope")
        normalized_requested_scope = {}

    if not isinstance(payload, dict):
        reasons.append("malformed_payload")
        return _result(
            reasons=reasons,
            current_time=current_time,
            approval_actor=approval_actor,
            approved_for_actor=approved_for_actor,
            requested_actor=requested_actor,
            token_scope=token_scope,
            requested_scope=normalized_requested_scope,
        )

    for field in REQUIRED_APPROVAL_TOKEN_FIELDS:
        if field not in payload:
            reasons.append(f"missing_required_field:{field}")

    schema_version = _string_field(payload, "schema_version", reasons)
    if schema_version and schema_version != APPROVAL_TOKEN_SCHEMA_VERSION:
        reasons.append("schema_version_mismatch")

    _string_field(payload, "token_id", reasons)
    _string_field(payload, "reason", reasons)
    approval_actor = _string_field(payload, "approved_by", reasons)
    approved_for_actor = _string_field(payload, "approved_for_actor", reasons)
    token_scope = _scope_field(payload, "scope", reasons)

    issued_at = _datetime_field(payload, "issued_at", reasons)
    expires_at = _datetime_field(payload, "expires_at", reasons)

    if approval_actor and requested_actor and approval_actor == requested_actor:
        reasons.append("self_approval_rejected")
    if approval_actor and approved_for_actor and approval_actor == approved_for_actor:
        reasons.append("self_approval_rejected")
    if approved_for_actor and requested_actor and approved_for_actor != requested_actor:
        reasons.append("wrong_actor")
    if token_scope is not None and token_scope != normalized_requested_scope:
        reasons.append("scope_mismatch")
    if issued_at is not None and issued_at > current_time:
        reasons.append("token_issued_in_future")
    if expires_at is not None and expires_at <= current_time:
        reasons.append("token_expired")
    if issued_at is not None and current_time - issued_at > APPROVAL_TOKEN_MAX_AGE:
        reasons.append("token_stale")
    if issued_at is not None and expires_at is not None and expires_at <= issued_at:
        reasons.append("token_expiration_not_after_issue")

    return _result(
        reasons=reasons,
        current_time=current_time,
        approval_actor=approval_actor,
        approved_for_actor=approved_for_actor,
        requested_actor=requested_actor,
        token_scope=token_scope,
        requested_scope=normalized_requested_scope,
    )


def _result(
    *,
    reasons: list[str],
    current_time: datetime,
    approval_actor: str | None,
    approved_for_actor: str | None,
    requested_actor: str,
    token_scope: dict[str, str] | None,
    requested_scope: dict[str, str],
) -> ApprovalTokenValidationResult:
    reasons = _dedupe_reasons(reasons)
    accepted = not reasons
    return ApprovalTokenValidationResult(
        status="accepted" if accepted else "rejected",
        accepted=accepted,
        rejected=not accepted,
        reasons=tuple(reasons),
        validated_at=_format_utc(current_time),
        approval_actor=approval_actor,
        approved_for_actor=approved_for_actor,
        requested_actor=requested_actor,
        token_scope=token_scope,
        requested_scope=requested_scope,
    )


def _dedupe_reasons(reasons: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        deduped.append(reason)
    return deduped


def _string_field(
    payload: dict[str, Any],
    field: str,
    reasons: list[str],
) -> str | None:
    if field not in payload:
        return None
    value = payload[field]
    if not isinstance(value, str) or not value.strip():
        reasons.append(f"malformed_field:{field}")
        return None
    return value.strip()


def _datetime_field(
    payload: dict[str, Any],
    field: str,
    reasons: list[str],
) -> datetime | None:
    value = _string_field(payload, field, reasons)
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        reasons.append(f"malformed_field:{field}")
        return None
    if parsed.tzinfo is None:
        reasons.append(f"malformed_field:{field}")
        return None
    return parsed.astimezone(UTC)


def _scope_field(
    payload: dict[str, Any],
    field: str,
    reasons: list[str],
) -> dict[str, str] | None:
    if field not in payload:
        return None
    scope = _normalize_scope(payload[field])
    if scope is None:
        reasons.append(f"malformed_field:{field}")
        return None
    return scope


def _normalize_scope(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    normalized: dict[str, str] = {}
    for field in SCOPE_REQUIRED_FIELDS:
        item = value.get(field)
        if not isinstance(item, str) or not item.strip():
            return None
        normalized[field] = item.strip()
    return normalized


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
