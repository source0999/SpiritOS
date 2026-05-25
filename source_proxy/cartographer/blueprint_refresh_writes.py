from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import Any


INTEGRATED_CONTROL_PLAN_11 = "Cartographer Integrated Control Master Plan 11"
SAFE_BLUEPRINT_REFRESH_WRITES_PHASE = (
    "Plan 11 Phase 11.1 Increment 11.1.1: Safe blueprint refresh proposals"
)

SAFE_BLUEPRINT_REFRESH_CLASSES: tuple[str, ...] = (
    "project_state_refresh",
    "component_blueprint_refresh",
    "manual_checks_blueprint_refresh",
    "blueprint_index_refresh",
)

SAFE_BLUEPRINT_TARGET_PREFIXES: tuple[str, ...] = (
    "_blueprints/",
    "docs/",
)

SAFE_BLUEPRINT_REFRESH_REQUIRED_FIELDS: tuple[str, ...] = (
    "proposal_id",
    "refresh_class",
    "target_blueprint_paths",
    "receipt_path",
    "exact_change_summary",
    "source_evidence_paths",
    "rollback_guidance",
    "verification_plan",
    "trust_tier",
    "approval_token_id",
    "status",
    "created_at",
)

FORBIDDEN_BLUEPRINT_REFRESH_AUTHORITIES: tuple[str, ...] = (
    "source_write",
    "test_write",
    "docs_write",
    "blueprint_write",
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
class SafeBlueprintRefreshWriteProposal:
    proposal_id: str
    refresh_class: str
    target_blueprint_paths: tuple[str, ...]
    receipt_path: str
    exact_change_summary: str
    source_evidence_paths: tuple[str, ...]
    rollback_guidance: str
    verification_plan: tuple[str, ...]
    trust_tier: str
    approval_token_id: str
    status: str
    created_at: str
    proposal_only_proof_complete: bool = True
    blueprint_write_enabled: bool = False
    docs_write_enabled: bool = False
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
class SafeBlueprintRefreshWriteValidation:
    phase: str
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    proposal_id: str | None
    refresh_class: str | None
    target_blueprint_paths: tuple[str, ...]
    receipt_path: str | None
    source_evidence_paths: tuple[str, ...]
    trust_tier: str | None
    approval_token_id: str | None
    validated_at: str
    proposal_only_proof_complete: bool = True
    blueprint_write_enabled: bool = False
    docs_write_enabled: bool = False
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


def build_safe_blueprint_refresh_write_status() -> dict[str, Any]:
    return {
        "plan": INTEGRATED_CONTROL_PLAN_11,
        "phase": SAFE_BLUEPRINT_REFRESH_WRITES_PHASE,
        "status": "proposal-only-proof",
        "safe_refresh_classes": SAFE_BLUEPRINT_REFRESH_CLASSES,
        "safe_target_prefixes": SAFE_BLUEPRINT_TARGET_PREFIXES,
        "required_fields": SAFE_BLUEPRINT_REFRESH_REQUIRED_FIELDS,
        "forbidden_authorities": FORBIDDEN_BLUEPRINT_REFRESH_AUTHORITIES,
        "proposal_only_proof_complete": True,
        "blueprint_write_enabled": False,
        "docs_write_enabled": False,
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
        "safe_next_action": "Review exact blueprint refresh proposals; require separate approval before any safe blueprint write.",
    }


def validate_safe_blueprint_refresh_write_proposal(
    proposal: Any,
    *,
    expected_trust_tier: str,
    expected_approval_token_id: str,
    now: datetime | None = None,
) -> SafeBlueprintRefreshWriteValidation:
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
        reasons.append("malformed_safe_blueprint_refresh_write_proposal")
        return _validation(
            reasons=reasons,
            current_time=current_time,
            proposal_id=None,
            refresh_class=None,
            target_blueprint_paths=(),
            receipt_path=None,
            source_evidence_paths=(),
            trust_tier=None,
            approval_token_id=None,
        )

    for field in SAFE_BLUEPRINT_REFRESH_REQUIRED_FIELDS:
        if field not in payload:
            reasons.append(f"missing_required_field:{field}")

    proposal_id = _string_field(payload, "proposal_id", reasons)
    refresh_class = _string_field(payload, "refresh_class", reasons)
    target_blueprint_paths = _string_tuple_field(payload, "target_blueprint_paths", reasons)
    receipt_path = _string_field(payload, "receipt_path", reasons)
    exact_change_summary = _string_field(payload, "exact_change_summary", reasons)
    source_evidence_paths = _string_tuple_field(payload, "source_evidence_paths", reasons)
    rollback_guidance = _string_field(payload, "rollback_guidance", reasons)
    verification_plan = _string_tuple_field(payload, "verification_plan", reasons)
    trust_tier = _string_field(payload, "trust_tier", reasons)
    approval_token_id = _string_field(payload, "approval_token_id", reasons)
    status = _string_field(payload, "status", reasons)
    created_at = _datetime_value(payload.get("created_at"))

    if refresh_class and refresh_class not in SAFE_BLUEPRINT_REFRESH_CLASSES:
        reasons.append("unknown_refresh_class")
    if target_blueprint_paths == ():
        reasons.append("missing_target_blueprint_paths")
    if len(set(target_blueprint_paths)) != len(target_blueprint_paths):
        reasons.append("duplicate_target_blueprint_path")
    for target_path in target_blueprint_paths:
        if _is_broad_file_scope(target_path):
            reasons.append("broad_target_blueprint_path")
        if not _is_safe_blueprint_target(target_path):
            reasons.append("target_must_be_exact_blueprint_markdown")
    if receipt_path and _is_broad_file_scope(receipt_path):
        reasons.append("broad_receipt_path")
    if receipt_path and not receipt_path.startswith("docs/"):
        reasons.append("receipt_path_must_be_docs")
    if receipt_path and not receipt_path.endswith(".md"):
        reasons.append("receipt_path_must_be_markdown")
    if source_evidence_paths == ():
        reasons.append("missing_source_evidence_paths")
    for evidence_path in source_evidence_paths:
        if _is_broad_file_scope(evidence_path):
            reasons.append("broad_source_evidence_path")
        if not evidence_path.endswith(".md"):
            reasons.append("source_evidence_must_be_markdown")
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
        refresh_class=refresh_class,
        target_blueprint_paths=target_blueprint_paths,
        receipt_path=receipt_path,
        source_evidence_paths=source_evidence_paths,
        trust_tier=trust_tier,
        approval_token_id=approval_token_id,
    )


def _validation(
    *,
    reasons: list[str],
    current_time: datetime,
    proposal_id: str | None,
    refresh_class: str | None,
    target_blueprint_paths: tuple[str, ...],
    receipt_path: str | None,
    source_evidence_paths: tuple[str, ...],
    trust_tier: str | None,
    approval_token_id: str | None,
) -> SafeBlueprintRefreshWriteValidation:
    blocked_reasons = tuple(dict.fromkeys(reasons))
    accepted = not blocked_reasons
    return SafeBlueprintRefreshWriteValidation(
        phase=SAFE_BLUEPRINT_REFRESH_WRITES_PHASE,
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=blocked_reasons,
        proposal_id=proposal_id,
        refresh_class=refresh_class,
        target_blueprint_paths=target_blueprint_paths,
        receipt_path=receipt_path,
        source_evidence_paths=source_evidence_paths,
        trust_tier=trust_tier,
        approval_token_id=approval_token_id,
        validated_at=_format_utc(current_time),
    )


def _proposal_payload(proposal: Any) -> dict[str, Any] | None:
    if isinstance(proposal, SafeBlueprintRefreshWriteProposal):
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


def _is_safe_blueprint_target(path: str) -> bool:
    if not path.endswith(".md"):
        return False
    return path.startswith("_blueprints/") or path in {"docs/blueprint.md"}


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
