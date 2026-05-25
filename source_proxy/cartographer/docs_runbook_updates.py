from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import Any


INTEGRATED_CONTROL_PLAN_11 = "Cartographer Integrated Control Master Plan 11"
SAFE_DOCS_RUNBOOK_UPDATES_PHASE = (
    "Plan 11 Phase 11.1 Increment 11.1.1: Safe docs/runbook maintenance proposals"
)

SAFE_DOCS_RUNBOOK_UPDATE_CLASSES: tuple[str, ...] = (
    "operator_runbook_clarification",
    "docs_troubleshooting_note",
    "receipt_index_update",
    "manual_checklist_update",
)

SAFE_DOCS_RUNBOOK_TARGET_PREFIXES: tuple[str, ...] = (
    "docs/",
    "runbooks/",
)

SAFE_DOCS_RUNBOOK_REQUIRED_FIELDS: tuple[str, ...] = (
    "proposal_id",
    "update_class",
    "target_paths",
    "receipt_path",
    "exact_change_summary",
    "rationale",
    "rollback_guidance",
    "verification_plan",
    "trust_tier",
    "approval_token_id",
    "status",
    "created_at",
)

FORBIDDEN_DOCS_RUNBOOK_AUTHORITIES: tuple[str, ...] = (
    "source_write",
    "test_write",
    "docs_write",
    "runbook_write",
    "safe_write",
    "command_execution",
    "queue_execution",
    "background_loop",
    "local_commit",
    "push",
    "branch",
    "worktree",
    "stash",
    "clean",
    "reset",
    "checkout",
    "approval_token_minting",
    "self_approval",
    "durable_storage_write",
    "api_mutation",
)


@dataclasses.dataclass(frozen=True)
class SafeDocsRunbookUpdateProposal:
    proposal_id: str
    update_class: str
    target_paths: tuple[str, ...]
    receipt_path: str
    exact_change_summary: str
    rationale: str
    rollback_guidance: str
    verification_plan: tuple[str, ...]
    trust_tier: str
    approval_token_id: str
    status: str
    created_at: str
    proposal_only: bool = True
    docs_write_enabled: bool = False
    runbook_write_enabled: bool = False
    source_write_enabled: bool = False
    test_write_enabled: bool = False
    command_execution_enabled: bool = False
    queue_execution_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    durable_storage_written: bool = False
    api_mutation_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class SafeDocsRunbookUpdateValidation:
    phase: str
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    proposal_id: str | None
    update_class: str | None
    target_paths: tuple[str, ...]
    receipt_path: str | None
    trust_tier: str | None
    approval_token_id: str | None
    validated_at: str
    proposal_only: bool = True
    docs_write_enabled: bool = False
    runbook_write_enabled: bool = False
    source_write_enabled: bool = False
    test_write_enabled: bool = False
    command_execution_enabled: bool = False
    queue_execution_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    durable_storage_written: bool = False
    api_mutation_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_safe_docs_runbook_update_status() -> dict[str, Any]:
    return {
        "plan": INTEGRATED_CONTROL_PLAN_11,
        "phase": SAFE_DOCS_RUNBOOK_UPDATES_PHASE,
        "status": "proposal-only",
        "safe_update_classes": SAFE_DOCS_RUNBOOK_UPDATE_CLASSES,
        "safe_target_prefixes": SAFE_DOCS_RUNBOOK_TARGET_PREFIXES,
        "required_fields": SAFE_DOCS_RUNBOOK_REQUIRED_FIELDS,
        "forbidden_authorities": FORBIDDEN_DOCS_RUNBOOK_AUTHORITIES,
        "proposal_only": True,
        "docs_write_enabled": False,
        "runbook_write_enabled": False,
        "source_write_enabled": False,
        "test_write_enabled": False,
        "command_execution_enabled": False,
        "queue_execution_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "durable_storage_written": False,
        "api_mutation_available": False,
        "exact_scope_required": True,
        "approval_bound": True,
        "receipt_backed": True,
        "safe_next_action": "Review exact docs/runbook update proposals; require separate approval before any safe maintenance write.",
    }


def validate_safe_docs_runbook_update_proposal(
    proposal: Any,
    *,
    expected_trust_tier: str,
    expected_approval_token_id: str,
    now: datetime | None = None,
) -> SafeDocsRunbookUpdateValidation:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []
    expected_trust_tier = expected_trust_tier.strip() if expected_trust_tier else ""
    expected_approval_token_id = expected_approval_token_id.strip() if expected_approval_token_id else ""
    if not expected_trust_tier:
        reasons.append("missing_expected_trust_tier")
    if not expected_approval_token_id:
        reasons.append("missing_expected_approval_token_id")

    payload = _proposal_payload(proposal)
    if payload is None:
        reasons.append("malformed_safe_docs_runbook_update_proposal")
        return _validation(
            reasons=reasons,
            current_time=current_time,
            proposal_id=None,
            update_class=None,
            target_paths=(),
            receipt_path=None,
            trust_tier=None,
            approval_token_id=None,
        )

    for field in SAFE_DOCS_RUNBOOK_REQUIRED_FIELDS:
        if field not in payload:
            reasons.append(f"missing_required_field:{field}")

    proposal_id = _string_field(payload, "proposal_id", reasons)
    update_class = _string_field(payload, "update_class", reasons)
    target_paths = _string_tuple_field(payload, "target_paths", reasons)
    receipt_path = _string_field(payload, "receipt_path", reasons)
    exact_change_summary = _string_field(payload, "exact_change_summary", reasons)
    rationale = _string_field(payload, "rationale", reasons)
    rollback_guidance = _string_field(payload, "rollback_guidance", reasons)
    verification_plan = _string_tuple_field(payload, "verification_plan", reasons)
    trust_tier = _string_field(payload, "trust_tier", reasons)
    approval_token_id = _string_field(payload, "approval_token_id", reasons)
    status = _string_field(payload, "status", reasons)
    created_at = _datetime_value(payload.get("created_at"))

    if update_class and update_class not in SAFE_DOCS_RUNBOOK_UPDATE_CLASSES:
        reasons.append("unknown_update_class")
    if target_paths == ():
        reasons.append("missing_target_paths")
    if len(set(target_paths)) != len(target_paths):
        reasons.append("duplicate_target_path")
    for target_path in target_paths:
        if _is_broad_file_scope(target_path):
            reasons.append("broad_target_path")
        if not _is_safe_docs_runbook_target(target_path):
            reasons.append("target_must_be_docs_or_runbook_markdown")
    if receipt_path and _is_broad_file_scope(receipt_path):
        reasons.append("broad_receipt_path")
    if receipt_path and not receipt_path.startswith("docs/"):
        reasons.append("receipt_path_must_be_docs")
    if receipt_path and not receipt_path.endswith(".md"):
        reasons.append("receipt_path_must_be_markdown")
    if trust_tier and trust_tier != expected_trust_tier:
        reasons.append("wrong_trust_tier")
    if approval_token_id and approval_token_id != expected_approval_token_id:
        reasons.append("wrong_approval_token")
    if status and status != "proposed":
        reasons.append("status_must_remain_proposed")
    if verification_plan == ():
        reasons.append("missing_verification_plan")
    if exact_change_summary and any(token in exact_change_summary.lower() for token in ("write now", "apply now")):
        reasons.append("change_summary_must_not_request_application")
    if rationale and any(token in rationale.lower() for token in ("source", "test file", "production code")):
        reasons.append("rationale_must_not_expand_beyond_docs_runbooks")
    if rollback_guidance and "force" in rollback_guidance.lower():
        reasons.append("rollback_guidance_must_not_recommend_force")
    if created_at is None:
        reasons.append("invalid_created_at")
    elif created_at > current_time:
        reasons.append("created_at_in_future")

    return _validation(
        reasons=reasons,
        current_time=current_time,
        proposal_id=proposal_id,
        update_class=update_class,
        target_paths=target_paths,
        receipt_path=receipt_path,
        trust_tier=trust_tier,
        approval_token_id=approval_token_id,
    )


def _validation(
    *,
    reasons: list[str],
    current_time: datetime,
    proposal_id: str | None,
    update_class: str | None,
    target_paths: tuple[str, ...],
    receipt_path: str | None,
    trust_tier: str | None,
    approval_token_id: str | None,
) -> SafeDocsRunbookUpdateValidation:
    blocked_reasons = tuple(dict.fromkeys(reasons))
    accepted = not blocked_reasons
    return SafeDocsRunbookUpdateValidation(
        phase=SAFE_DOCS_RUNBOOK_UPDATES_PHASE,
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=blocked_reasons,
        proposal_id=proposal_id,
        update_class=update_class,
        target_paths=target_paths,
        receipt_path=receipt_path,
        trust_tier=trust_tier,
        approval_token_id=approval_token_id,
        validated_at=_format_utc(current_time),
    )


def _proposal_payload(proposal: Any) -> dict[str, Any] | None:
    if isinstance(proposal, SafeDocsRunbookUpdateProposal):
        return proposal.to_dict()
    if isinstance(proposal, dict):
        return proposal
    return None


def _string_field(payload: dict[str, Any], field: str, reasons: list[str]) -> str | None:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        reasons.append(f"invalid_{field}")
        return None
    return value.strip()


def _string_tuple_field(payload: dict[str, Any], field: str, reasons: list[str]) -> tuple[str, ...]:
    value = payload.get(field)
    if not isinstance(value, (list, tuple)):
        reasons.append(f"invalid_{field}")
        return ()
    items = tuple(item.strip() for item in value if isinstance(item, str) and item.strip())
    if len(items) != len(value):
        reasons.append(f"invalid_{field}_entry")
    return items


def _is_safe_docs_runbook_target(path: str) -> bool:
    return path.endswith(".md") and path.startswith(SAFE_DOCS_RUNBOOK_TARGET_PREFIXES)


def _is_broad_file_scope(path: str) -> bool:
    return (
        path.startswith("/")
        or path.endswith("/")
        or path in {".", ".."}
        or path.startswith("../")
        or "/../" in path
        or "\\" in path
        or "*" in path
        or "?" in path
        or "[" in path
        or "]" in path
    )


def _datetime_value(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(UTC)


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
