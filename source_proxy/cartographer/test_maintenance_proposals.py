from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import Any


INTEGRATED_CONTROL_PLAN_11 = "Cartographer Integrated Control Master Plan 11"
SAFE_TEST_MAINTENANCE_PROPOSALS_PHASE = (
    "Plan 11 Phase 11.1 Increment 11.1.2: Safe test maintenance proposals"
)

SAFE_TEST_MAINTENANCE_CLASSES: tuple[str, ...] = (
    "assertion_message_clarification",
    "deterministic_fixture_cleanup",
    "test_name_clarification",
    "focused_expectation_tightening",
)

SAFE_TEST_MAINTENANCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "proposal_id",
    "maintenance_class",
    "target_test_file",
    "exact_change_summary",
    "rationale",
    "verification_plan",
    "trust_tier",
    "approval_token_id",
    "status",
    "created_at",
)

FORBIDDEN_TEST_MAINTENANCE_AUTHORITIES: tuple[str, ...] = (
    "source_write",
    "test_write",
    "safe_write",
    "command_execution",
    "test_execution",
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
class SafeTestMaintenanceProposal:
    proposal_id: str
    maintenance_class: str
    target_test_file: str
    exact_change_summary: str
    rationale: str
    verification_plan: tuple[str, ...]
    trust_tier: str
    approval_token_id: str
    status: str
    created_at: str
    proposal_only: bool = True
    source_write_enabled: bool = False
    test_write_enabled: bool = False
    command_execution_enabled: bool = False
    test_execution_enabled: bool = False
    queue_execution_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    durable_storage_written: bool = False
    api_mutation_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class SafeTestMaintenanceProposalValidation:
    phase: str
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    proposal_id: str | None
    maintenance_class: str | None
    target_test_file: str | None
    trust_tier: str | None
    approval_token_id: str | None
    validated_at: str
    proposal_only: bool = True
    source_write_enabled: bool = False
    test_write_enabled: bool = False
    command_execution_enabled: bool = False
    test_execution_enabled: bool = False
    queue_execution_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    durable_storage_written: bool = False
    api_mutation_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_safe_test_maintenance_proposal_status() -> dict[str, Any]:
    return {
        "plan": INTEGRATED_CONTROL_PLAN_11,
        "phase": SAFE_TEST_MAINTENANCE_PROPOSALS_PHASE,
        "status": "proposal-only",
        "safe_maintenance_classes": SAFE_TEST_MAINTENANCE_CLASSES,
        "required_fields": SAFE_TEST_MAINTENANCE_REQUIRED_FIELDS,
        "forbidden_authorities": FORBIDDEN_TEST_MAINTENANCE_AUTHORITIES,
        "proposal_only": True,
        "source_write_enabled": False,
        "test_write_enabled": False,
        "command_execution_enabled": False,
        "test_execution_enabled": False,
        "queue_execution_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "durable_storage_written": False,
        "api_mutation_available": False,
        "exact_scope_required": True,
        "approval_bound": True,
        "verification_plan_required": True,
        "automatic_test_edits_blocked": True,
        "safe_next_action": "Review exact safe test maintenance proposals; require separate approval before any test write.",
    }


def validate_safe_test_maintenance_proposal(
    proposal: Any,
    *,
    expected_trust_tier: str,
    expected_approval_token_id: str,
    now: datetime | None = None,
) -> SafeTestMaintenanceProposalValidation:
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
        reasons.append("malformed_safe_test_maintenance_proposal")
        return _validation(
            reasons=reasons,
            current_time=current_time,
            proposal_id=None,
            maintenance_class=None,
            target_test_file=None,
            trust_tier=None,
            approval_token_id=None,
        )

    for field in SAFE_TEST_MAINTENANCE_REQUIRED_FIELDS:
        if field not in payload:
            reasons.append(f"missing_required_field:{field}")

    proposal_id = _string_field(payload, "proposal_id", reasons)
    maintenance_class = _string_field(payload, "maintenance_class", reasons)
    target_test_file = _string_field(payload, "target_test_file", reasons)
    exact_change_summary = _string_field(payload, "exact_change_summary", reasons)
    rationale = _string_field(payload, "rationale", reasons)
    verification_plan = _string_tuple_field(payload, "verification_plan", reasons)
    trust_tier = _string_field(payload, "trust_tier", reasons)
    approval_token_id = _string_field(payload, "approval_token_id", reasons)
    status = _string_field(payload, "status", reasons)
    created_at = _datetime_value(payload.get("created_at"))

    if maintenance_class and maintenance_class not in SAFE_TEST_MAINTENANCE_CLASSES:
        reasons.append("unknown_maintenance_class")
    if target_test_file and not _is_exact_safe_test_path(target_test_file):
        reasons.append("target_must_be_exact_test_file")
    if target_test_file and _is_broad_file_scope(target_test_file):
        reasons.append("broad_target_test_file")
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
    if rationale and "source" in rationale.lower():
        reasons.append("rationale_must_not_expand_to_source_changes")
    if created_at is None:
        reasons.append("invalid_created_at")
    elif created_at > current_time:
        reasons.append("created_at_in_future")

    return _validation(
        reasons=reasons,
        current_time=current_time,
        proposal_id=proposal_id,
        maintenance_class=maintenance_class,
        target_test_file=target_test_file,
        trust_tier=trust_tier,
        approval_token_id=approval_token_id,
    )


def _validation(
    *,
    reasons: list[str],
    current_time: datetime,
    proposal_id: str | None,
    maintenance_class: str | None,
    target_test_file: str | None,
    trust_tier: str | None,
    approval_token_id: str | None,
) -> SafeTestMaintenanceProposalValidation:
    blocked_reasons = tuple(dict.fromkeys(reasons))
    accepted = not blocked_reasons
    return SafeTestMaintenanceProposalValidation(
        phase=SAFE_TEST_MAINTENANCE_PROPOSALS_PHASE,
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=blocked_reasons,
        proposal_id=proposal_id,
        maintenance_class=maintenance_class,
        target_test_file=target_test_file,
        trust_tier=trust_tier,
        approval_token_id=approval_token_id,
        validated_at=_format_utc(current_time),
    )


def _proposal_payload(proposal: Any) -> dict[str, Any] | None:
    if isinstance(proposal, SafeTestMaintenanceProposal):
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


def _string_tuple_field(payload: dict[str, Any], field: str, reasons: list[str]) -> tuple[str, ...] | None:
    value = payload.get(field)
    if not isinstance(value, (list, tuple)):
        reasons.append(f"invalid_{field}")
        return ()
    items = tuple(item.strip() for item in value if isinstance(item, str) and item.strip())
    if len(items) != len(value):
        reasons.append(f"invalid_{field}_entry")
    if len(set(items)) != len(items):
        reasons.append(f"duplicate_{field}_entry")
    return items


def _is_exact_safe_test_path(path: str) -> bool:
    return path.startswith("source_proxy/tests/test_") and path.endswith(".py")


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
