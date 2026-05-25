from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta
from typing import Any

APPROVAL_TOKEN_SCHEMA_VERSION = "cartographer.approval-token.v1"
APPROVAL_TOKEN_MAX_AGE = timedelta(hours=24)
APPROVAL_TOKEN_REQUIRED_KILL_SWITCH_STATE = "inactive"

REQUIRED_APPROVAL_TOKEN_FIELDS: tuple[str, ...] = (
    "schema_version",
    "token_id",
    "run_id",
    "operator_id",
    "approver_id",
    "action_type",
    "lane_id",
    "scope",
    "exact_allowed_files",
    "exact_forbidden_files",
    "expires_at",
    "rollback_instructions",
    "verification_instructions",
    "expected_head",
    "expected_dirty_tree",
    "kill_switch_state",
    "trust_tier",
    "single_action",
    "issued_by_human",
    "human_approved_at",
)

SCOPE_REQUIRED_FIELDS: tuple[str, ...] = ("type", "value")
BROAD_SCOPE_VALUES: frozenset[str] = frozenset(
    {"*", "all", "repo", "repository", "workspace", "global"}
)
BROAD_FILE_SCOPE_VALUES: frozenset[str] = frozenset(
    {"*", ".", "./", "/", "repo", "repository", "workspace", "all"}
)
BROAD_TRUST_TIER_VALUES: frozenset[str] = frozenset({"*", "all", "any"})
BROAD_LANE_VALUES: frozenset[str] = frozenset(
    {"*", "all", "any", "repo", "repository", "workspace", "global"}
)

APPROVAL_TOKEN_REASON_MESSAGES: dict[str, str] = {
    "missing_requested_actor": "Requested actor is required.",
    "malformed_requested_scope": "Requested scope must include non-empty type and value strings.",
    "malformed_requested_files": "Requested files must be an exact list of non-empty strings.",
    "malformed_current_dirty_tree": "Current dirty tree must be a structured dictionary.",
    "missing_requested_lane": "Requested lane is required.",
    "malformed_payload": "Approval token payload must be an object.",
    "missing_required_field": "Approval token is missing a required field.",
    "malformed_field": "Approval token field is malformed.",
    "schema_version_mismatch": "Approval token schema version does not match Cartographer.",
    "self_approval_rejected": "The operator cannot approve its own Cartographer action.",
    "wrong_actor": "Approval token operator does not match the requested actor.",
    "scope_mismatch": "Approval token scope does not match the requested scope.",
    "broad_scope": "Approval token scope is broad and must be exact.",
    "lane_mismatch": "Approval token lane does not match the requested lane.",
    "broad_lane": "Approval token lane is broad and must name one exact lane.",
    "action_type_mismatch": "Approval token action type does not match the requested action.",
    "single_action_required": "Approval token must approve exactly one action.",
    "human_issued_required": "Approval token must be marked as human-issued.",
    "empty_exact_allowed_files": "Approval token must list exact allowed files.",
    "wildcard_file_scope": "Approval token allowed files cannot use wildcards.",
    "broad_file_scope": "Approval token allowed files must be exact file paths.",
    "requested_files_exceed_exact_allowed_files": "Requested files exceed the token's exact allowed files.",
    "wildcard_forbidden_file_scope": "Approval token forbidden files cannot use wildcards.",
    "requested_files_match_forbidden_files": "Requested files intersect the token's forbidden files.",
    "allowed_files_overlap_forbidden_files": "Allowed and forbidden file scopes overlap.",
    "stale_head": "Current HEAD does not match the token's expected HEAD.",
    "stale_dirty_tree": "Current dirty tree does not match the token's expected dirty tree.",
    "kill_switch_active": "Kill switch is active; approval validation fails closed.",
    "kill_switch_state_not_inactive": "Approval token must require an inactive kill switch.",
    "broad_trust_tier": "Approval token trust tier must be exact.",
    "trust_tier_mismatch": "Approval token trust tier does not match the requested tier.",
    "token_approved_in_future": "Human approval timestamp is in the future.",
    "token_expired": "Approval token is expired.",
    "token_stale": "Approval token is older than the maximum approval age.",
    "token_expiration_not_after_approval": "Approval token expiration must be after human approval.",
}


@dataclasses.dataclass(frozen=True)
class ApprovalTokenValidationResult:
    status: str
    accepted: bool
    rejected: bool
    go: bool
    no_go_default: bool
    reasons: tuple[str, ...]
    reason_details: tuple[dict[str, str], ...]
    validated_at: str
    token_id: str | None
    run_id: str | None
    action_type: str | None
    lane_id: str | None
    requested_lane_id: str | None
    approval_actor: str | None
    approver_id: str | None
    approved_for_actor: str | None
    operator_id: str | None
    requested_actor: str
    token_scope: dict[str, str] | None
    requested_scope: dict[str, str]
    exact_allowed_files: tuple[str, ...] | None
    exact_forbidden_files: tuple[str, ...] | None
    requested_files: tuple[str, ...]
    expected_head: str | None
    current_head: str | None
    expected_dirty_tree: dict[str, Any] | None
    current_dirty_tree: dict[str, Any] | None
    kill_switch_state: str | None
    requested_kill_switch_active: bool
    trust_tier: str | None
    requested_trust_tier: str | None
    single_action: bool | None
    issued_by_human: bool | None
    human_approved_at: str | None
    expires_at: str | None
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
        "plan": "Cartographer Integrated Control Master Plan 4",
        "phase": "Plan 4 Phase 4.1: Token Model",
        "status": "validation-only",
        "schema_version": APPROVAL_TOKEN_SCHEMA_VERSION,
        "required_fields": REQUIRED_APPROVAL_TOKEN_FIELDS,
        "scope_required_fields": SCOPE_REQUIRED_FIELDS,
        "required_kill_switch_state": APPROVAL_TOKEN_REQUIRED_KILL_SWITCH_STATE,
        "max_token_age_seconds": int(APPROVAL_TOKEN_MAX_AGE.total_seconds()),
        "exact_contract_fields": (
            "actor",
            "action",
            "lane",
            "files",
            "expiry",
            "expected_head",
            "trust_tier",
            "rollback",
            "verification",
        ),
        "no_go_default": True,
        "authority_granted": False,
        "write_authority_granted": False,
        "command_authority_granted": False,
        "workflow_authority_granted": False,
        "queue_authority_granted": False,
        "git_authority_granted": False,
        "self_approval_allowed": False,
        "token_issuance_available": False,
        "token_storage_available": False,
        "validation_only": True,
        "safe_next_action": "Validate Plan 4 token shape only; do not execute or mutate.",
    }


def validate_approval_token_payload(
    payload: Any,
    *,
    requested_actor: str,
    requested_scope: dict[str, str],
    requested_action_type: str | None = None,
    requested_lane_id: str | None = "cartographer",
    requested_files: list[str] | tuple[str, ...] | None = None,
    current_head: str | None = None,
    current_dirty_tree: dict[str, Any] | None = None,
    kill_switch_active: bool = False,
    requested_trust_tier: str | None = None,
    now: datetime | None = None,
) -> ApprovalTokenValidationResult:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []
    token_id: str | None = None
    run_id: str | None = None
    action_type: str | None = None
    lane_id: str | None = None
    approver_id: str | None = None
    operator_id: str | None = None
    token_scope: dict[str, str] | None = None
    exact_allowed_files: tuple[str, ...] | None = None
    exact_forbidden_files: tuple[str, ...] | None = None
    expected_head: str | None = None
    expected_dirty_tree: dict[str, Any] | None = None
    kill_switch_state: str | None = None
    trust_tier: str | None = None
    single_action: bool | None = None
    issued_by_human: bool | None = None
    human_approved_at: datetime | None = None
    expires_at: datetime | None = None

    requested_actor = requested_actor.strip() if requested_actor else ""
    if not requested_actor:
        reasons.append("missing_requested_actor")

    normalized_requested_action_type = _normalize_string(requested_action_type)
    normalized_requested_lane_id = _normalize_string(requested_lane_id)
    if requested_lane_id is not None and not normalized_requested_lane_id:
        reasons.append("missing_requested_lane")
    normalized_current_head = _normalize_string(current_head)
    normalized_requested_trust_tier = _normalize_string(requested_trust_tier)
    normalized_requested_files = _normalize_string_tuple(requested_files or ())
    if requested_files is not None and len(normalized_requested_files) != len(requested_files):
        reasons.append("malformed_requested_files")

    normalized_requested_scope = _normalize_scope(requested_scope)
    if normalized_requested_scope is None:
        reasons.append("malformed_requested_scope")
        normalized_requested_scope = {}

    normalized_current_dirty_tree = _normalize_dirty_tree(current_dirty_tree)
    if current_dirty_tree is not None and normalized_current_dirty_tree is None:
        reasons.append("malformed_current_dirty_tree")

    if not isinstance(payload, dict):
        reasons.append("malformed_payload")
        return _result(
            reasons=reasons,
            current_time=current_time,
            token_id=token_id,
            run_id=run_id,
            action_type=action_type,
            lane_id=lane_id,
            requested_lane_id=normalized_requested_lane_id or None,
            approver_id=approver_id,
            operator_id=operator_id,
            requested_actor=requested_actor,
            token_scope=token_scope,
            requested_scope=normalized_requested_scope,
            exact_allowed_files=exact_allowed_files,
            exact_forbidden_files=exact_forbidden_files,
            requested_files=normalized_requested_files,
            expected_head=expected_head,
            current_head=normalized_current_head or None,
            expected_dirty_tree=expected_dirty_tree,
            current_dirty_tree=normalized_current_dirty_tree,
            kill_switch_state=kill_switch_state,
            requested_kill_switch_active=kill_switch_active,
            trust_tier=trust_tier,
            requested_trust_tier=normalized_requested_trust_tier or None,
            single_action=single_action,
            issued_by_human=issued_by_human,
            human_approved_at=human_approved_at,
            expires_at=expires_at,
        )

    for field in REQUIRED_APPROVAL_TOKEN_FIELDS:
        if field not in payload:
            reasons.append(f"missing_required_field:{field}")

    schema_version = _string_field(payload, "schema_version", reasons)
    if schema_version and schema_version != APPROVAL_TOKEN_SCHEMA_VERSION:
        reasons.append("schema_version_mismatch")

    token_id = _string_field(payload, "token_id", reasons)
    run_id = _string_field(payload, "run_id", reasons)
    operator_id = _string_field(payload, "operator_id", reasons)
    approver_id = _string_field(payload, "approver_id", reasons)
    action_type = _string_field(payload, "action_type", reasons)
    lane_id = _string_field(payload, "lane_id", reasons)
    token_scope = _scope_field(payload, "scope", reasons)
    exact_allowed_files = _string_tuple_field(payload, "exact_allowed_files", reasons)
    exact_forbidden_files = _string_tuple_field(payload, "exact_forbidden_files", reasons)
    expected_head = _string_field(payload, "expected_head", reasons)
    expected_dirty_tree = _dirty_tree_field(payload, "expected_dirty_tree", reasons)
    kill_switch_state = _string_field(payload, "kill_switch_state", reasons)
    trust_tier = _string_field(payload, "trust_tier", reasons)
    single_action = _bool_field(payload, "single_action", reasons)
    issued_by_human = _bool_field(payload, "issued_by_human", reasons)
    _string_field(payload, "rollback_instructions", reasons)
    _string_field(payload, "verification_instructions", reasons)

    human_approved_at = _datetime_field(payload, "human_approved_at", reasons)
    expires_at = _datetime_field(payload, "expires_at", reasons)

    if approver_id and requested_actor and approver_id == requested_actor:
        reasons.append("self_approval_rejected")
    if approver_id and operator_id and approver_id == operator_id:
        reasons.append("self_approval_rejected")
    if operator_id and requested_actor and operator_id != requested_actor:
        reasons.append("wrong_actor")
    if token_scope is not None and token_scope != normalized_requested_scope:
        reasons.append("scope_mismatch")
    if token_scope is not None and _scope_is_broad(token_scope):
        reasons.append("broad_scope")
    if lane_id and normalized_requested_lane_id and lane_id != normalized_requested_lane_id:
        reasons.append("lane_mismatch")
    if lane_id and _lane_is_broad(lane_id):
        reasons.append("broad_lane")
    if action_type and normalized_requested_action_type:
        if action_type != normalized_requested_action_type:
            reasons.append("action_type_mismatch")
    if single_action is False:
        reasons.append("single_action_required")
    if issued_by_human is False:
        reasons.append("human_issued_required")
    if exact_allowed_files is not None:
        _add_file_scope_reasons(
            exact_allowed_files,
            normalized_requested_files,
            reasons,
        )
    if exact_forbidden_files is not None:
        _add_forbidden_file_scope_reasons(
            exact_forbidden_files,
            normalized_requested_files,
            reasons,
        )
    if exact_allowed_files is not None and exact_forbidden_files is not None:
        if set(exact_allowed_files).intersection(exact_forbidden_files):
            reasons.append("allowed_files_overlap_forbidden_files")
    if expected_head and normalized_current_head and expected_head != normalized_current_head:
        reasons.append("stale_head")
    if expected_dirty_tree is not None and normalized_current_dirty_tree is not None:
        if expected_dirty_tree != normalized_current_dirty_tree:
            reasons.append("stale_dirty_tree")
    if kill_switch_active:
        reasons.append("kill_switch_active")
    if kill_switch_state and kill_switch_state != APPROVAL_TOKEN_REQUIRED_KILL_SWITCH_STATE:
        reasons.append("kill_switch_state_not_inactive")
    if trust_tier and trust_tier in BROAD_TRUST_TIER_VALUES:
        reasons.append("broad_trust_tier")
    if trust_tier and normalized_requested_trust_tier:
        if trust_tier != normalized_requested_trust_tier:
            reasons.append("trust_tier_mismatch")
    if human_approved_at is not None and human_approved_at > current_time:
        reasons.append("token_approved_in_future")
    if expires_at is not None and expires_at <= current_time:
        reasons.append("token_expired")
    if human_approved_at is not None and current_time - human_approved_at > APPROVAL_TOKEN_MAX_AGE:
        reasons.append("token_stale")
    if human_approved_at is not None and expires_at is not None:
        if expires_at <= human_approved_at:
            reasons.append("token_expiration_not_after_approval")

    return _result(
        reasons=reasons,
        current_time=current_time,
        token_id=token_id,
        run_id=run_id,
        action_type=action_type,
        lane_id=lane_id,
        requested_lane_id=normalized_requested_lane_id or None,
        approver_id=approver_id,
        operator_id=operator_id,
        requested_actor=requested_actor,
        token_scope=token_scope,
        requested_scope=normalized_requested_scope,
        exact_allowed_files=exact_allowed_files,
        exact_forbidden_files=exact_forbidden_files,
        requested_files=normalized_requested_files,
        expected_head=expected_head,
        current_head=normalized_current_head or None,
        expected_dirty_tree=expected_dirty_tree,
        current_dirty_tree=normalized_current_dirty_tree,
        kill_switch_state=kill_switch_state,
        requested_kill_switch_active=kill_switch_active,
        trust_tier=trust_tier,
        requested_trust_tier=normalized_requested_trust_tier or None,
        single_action=single_action,
        issued_by_human=issued_by_human,
        human_approved_at=human_approved_at,
        expires_at=expires_at,
    )


def _result(
    *,
    reasons: list[str],
    current_time: datetime,
    token_id: str | None,
    run_id: str | None,
    action_type: str | None,
    lane_id: str | None,
    requested_lane_id: str | None,
    approver_id: str | None,
    operator_id: str | None,
    requested_actor: str,
    token_scope: dict[str, str] | None,
    requested_scope: dict[str, str],
    exact_allowed_files: tuple[str, ...] | None,
    exact_forbidden_files: tuple[str, ...] | None,
    requested_files: tuple[str, ...],
    expected_head: str | None,
    current_head: str | None,
    expected_dirty_tree: dict[str, Any] | None,
    current_dirty_tree: dict[str, Any] | None,
    kill_switch_state: str | None,
    requested_kill_switch_active: bool,
    trust_tier: str | None,
    requested_trust_tier: str | None,
    single_action: bool | None,
    issued_by_human: bool | None,
    human_approved_at: datetime | None,
    expires_at: datetime | None,
) -> ApprovalTokenValidationResult:
    reasons = _dedupe_reasons(reasons)
    accepted = not reasons
    return ApprovalTokenValidationResult(
        status="accepted" if accepted else "rejected",
        accepted=accepted,
        rejected=not accepted,
        go=False,
        no_go_default=True,
        reasons=tuple(reasons),
        reason_details=tuple(
            {"code": reason, "message": _reason_message(reason)}
            for reason in reasons
        ),
        validated_at=_format_utc(current_time),
        token_id=token_id,
        run_id=run_id,
        action_type=action_type,
        lane_id=lane_id,
        requested_lane_id=requested_lane_id,
        approval_actor=approver_id,
        approver_id=approver_id,
        approved_for_actor=operator_id,
        operator_id=operator_id,
        requested_actor=requested_actor,
        token_scope=token_scope,
        requested_scope=requested_scope,
        exact_allowed_files=exact_allowed_files,
        exact_forbidden_files=exact_forbidden_files,
        requested_files=requested_files,
        expected_head=expected_head,
        current_head=current_head,
        expected_dirty_tree=expected_dirty_tree,
        current_dirty_tree=current_dirty_tree,
        kill_switch_state=kill_switch_state,
        requested_kill_switch_active=requested_kill_switch_active,
        trust_tier=trust_tier,
        requested_trust_tier=requested_trust_tier,
        single_action=single_action,
        issued_by_human=issued_by_human,
        human_approved_at=_format_utc(human_approved_at) if human_approved_at else None,
        expires_at=_format_utc(expires_at) if expires_at else None,
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


def _bool_field(
    payload: dict[str, Any],
    field: str,
    reasons: list[str],
) -> bool | None:
    if field not in payload:
        return None
    value = payload[field]
    if not isinstance(value, bool):
        reasons.append(f"malformed_field:{field}")
        return None
    return value


def _dirty_tree_field(
    payload: dict[str, Any],
    field: str,
    reasons: list[str],
) -> dict[str, Any] | None:
    if field not in payload:
        return None
    value = _normalize_dirty_tree(payload[field])
    if value is None:
        reasons.append(f"malformed_field:{field}")
        return None
    return value


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


def _string_tuple_field(
    payload: dict[str, Any],
    field: str,
    reasons: list[str],
) -> tuple[str, ...] | None:
    if field not in payload:
        return None
    value = payload[field]
    if not isinstance(value, list):
        reasons.append(f"malformed_field:{field}")
        return None
    normalized = _normalize_string_tuple(value)
    if len(normalized) != len(value):
        reasons.append(f"malformed_field:{field}")
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


def _normalize_dirty_tree(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict) or not value:
        return None
    if any(not isinstance(key, str) or not key.strip() for key in value):
        return None
    return value


def _scope_is_broad(scope: dict[str, str]) -> bool:
    return any(value.lower() in BROAD_SCOPE_VALUES for value in scope.values())


def _lane_is_broad(lane_id: str) -> bool:
    normalized = lane_id.strip().lower()
    return (
        normalized in BROAD_LANE_VALUES
        or "*" in normalized
        or normalized.endswith("/")
    )


def _add_file_scope_reasons(
    exact_allowed_files: tuple[str, ...],
    requested_files: tuple[str, ...],
    reasons: list[str],
) -> None:
    if not exact_allowed_files:
        reasons.append("empty_exact_allowed_files")
    if any("*" in item for item in exact_allowed_files):
        reasons.append("wildcard_file_scope")
    if any(item.lower() in BROAD_FILE_SCOPE_VALUES or item.endswith("/") for item in exact_allowed_files):
        reasons.append("broad_file_scope")
    if requested_files and not set(requested_files).issubset(set(exact_allowed_files)):
        reasons.append("requested_files_exceed_exact_allowed_files")


def _add_forbidden_file_scope_reasons(
    exact_forbidden_files: tuple[str, ...],
    requested_files: tuple[str, ...],
    reasons: list[str],
) -> None:
    if any("*" in item for item in exact_forbidden_files):
        reasons.append("wildcard_forbidden_file_scope")
    if requested_files and set(requested_files).intersection(exact_forbidden_files):
        reasons.append("requested_files_match_forbidden_files")


def _reason_message(reason: str) -> str:
    base_reason = reason.split(":", 1)[0]
    return APPROVAL_TOKEN_REASON_MESSAGES.get(
        base_reason,
        "Approval token validation failed closed.",
    )


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
