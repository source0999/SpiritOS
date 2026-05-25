from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import Any


INTEGRATED_CONTROL_PLAN_11 = "Cartographer Integrated Control Master Plan 10/10"
TRUST_TIER_DECISION_GATE_PHASE = (
    "Plan 10 Phase 10.5: Trust tier advancement and regression gate"
)

TRUST_TIERS: tuple[str, ...] = ("tier-1", "tier-2", "tier-3")
TRUST_TIER_DECISION_OUTCOMES: tuple[str, ...] = ("advance", "hold", "demote")

TRUST_TIER_ADVANCEMENT_CRITERIA: tuple[str, ...] = (
    "72_hour_soak_evidence",
    "rollback_proof_recorded",
    "zero_false_positives",
    "zero_false_negatives",
    "zero_stop_events",
    "operator_review_recorded",
)

TRUST_TIER_REGRESSION_SIGNALS: tuple[str, ...] = (
    "false_positive_count",
    "false_negative_count",
    "stop_event_count",
    "missing_rollback_proof",
)

EXPANSION_CLASSES_REQUIRING_TRUST_TIER_REVIEW: tuple[str, ...] = (
    "safe_test_maintenance",
    "safe_docs_runbook_updates",
    "safe_blueprint_refresh_writes",
    "controlled_multi_worker_branch_workflow",
    "any_beyond_daily_driver_scope",
)

TRUST_TIER_DECISION_REQUIRED_FIELDS: tuple[str, ...] = (
    "decision_id",
    "requested_expansion_class",
    "current_trust_tier",
    "requested_trust_tier",
    "decision_outcome",
    "evidence_paths",
    "soak_evidence_hours",
    "rollback_proof_recorded",
    "false_positive_count",
    "false_negative_count",
    "stop_event_count",
    "operator_review_required",
    "operator_review_recorded",
    "approval_token_id",
    "status",
    "created_at",
)

FORBIDDEN_TRUST_TIER_DECISION_AUTHORITIES: tuple[str, ...] = (
    "trust_tier_promotion",
    "authority_expansion",
    "approval_token_minting",
    "self_approval",
    "worker_spawn",
    "task_execution",
    "queue_execution",
    "safe_write",
    "command_execution",
    "local_commit",
    "push",
    "branch",
    "worktree",
    "stash",
    "clean",
    "reset",
    "checkout",
    "durable_storage_write",
    "api_mutation",
)


@dataclasses.dataclass(frozen=True)
class TrustTierDecisionGate:
    decision_id: str
    requested_expansion_class: str
    current_trust_tier: str
    requested_trust_tier: str
    decision_outcome: str
    evidence_paths: tuple[str, ...]
    soak_evidence_hours: int
    rollback_proof_recorded: bool
    false_positive_count: int
    false_negative_count: int
    stop_event_count: int
    operator_review_required: bool
    operator_review_recorded: bool
    approval_token_id: str
    status: str
    created_at: str
    gate_only: bool = True
    expansion_enabled: bool = False
    trust_tier_promotion_recorded: bool = False
    approval_token_minted: bool = False
    self_approval_allowed: bool = False
    command_execution_enabled: bool = False
    queue_execution_enabled: bool = False
    task_execution_enabled: bool = False
    safe_write_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    branch_enabled: bool = False
    worktree_enabled: bool = False
    durable_storage_written: bool = False
    api_mutation_available: bool = False
    human_promotion_decision_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class TrustTierDecisionGateValidation:
    phase: str
    status: str
    accepted_for_review: bool
    blocked: bool
    reasons: tuple[str, ...]
    decision_id: str | None
    requested_expansion_class: str | None
    current_trust_tier: str | None
    requested_trust_tier: str | None
    decision_outcome: str | None
    evidence_paths: tuple[str, ...]
    soak_evidence_hours: int | None
    rollback_proof_recorded: bool | None
    false_positive_count: int | None
    false_negative_count: int | None
    stop_event_count: int | None
    approval_token_id: str | None
    validated_at: str
    gate_only: bool = True
    expansion_enabled: bool = False
    trust_tier_promotion_recorded: bool = False
    approval_token_minted: bool = False
    self_approval_allowed: bool = False
    command_execution_enabled: bool = False
    queue_execution_enabled: bool = False
    task_execution_enabled: bool = False
    safe_write_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    branch_enabled: bool = False
    worktree_enabled: bool = False
    durable_storage_written: bool = False
    api_mutation_available: bool = False
    human_promotion_decision_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_trust_tier_decision_gate_status() -> dict[str, Any]:
    return {
        "plan": INTEGRATED_CONTROL_PLAN_11,
        "phase": TRUST_TIER_DECISION_GATE_PHASE,
        "status": "gate-only",
        "trust_tiers": TRUST_TIERS,
        "current_trust_tier": "tier-1",
        "decision_outcomes": TRUST_TIER_DECISION_OUTCOMES,
        "advancement_criteria": TRUST_TIER_ADVANCEMENT_CRITERIA,
        "regression_signals": TRUST_TIER_REGRESSION_SIGNALS,
        "expansion_classes_requiring_review": EXPANSION_CLASSES_REQUIRING_TRUST_TIER_REVIEW,
        "required_fields": TRUST_TIER_DECISION_REQUIRED_FIELDS,
        "forbidden_authorities": FORBIDDEN_TRUST_TIER_DECISION_AUTHORITIES,
        "gate_only": True,
        "expansion_enabled": False,
        "trust_tier_promotion_recorded": False,
        "approval_token_minted": False,
        "self_approval_allowed": False,
        "command_execution_enabled": False,
        "queue_execution_enabled": False,
        "task_execution_enabled": False,
        "safe_write_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "branch_enabled": False,
        "worktree_enabled": False,
        "durable_storage_written": False,
        "api_mutation_available": False,
        "human_promotion_decision_required": True,
        "automatic_tier_advancement_enabled": False,
        "full_auto_enabled": False,
        "push_promotion_enabled": False,
        "next_explicit_decision_gate": "human operator review of the Plan 10/10 trust-tier decision packet",
        "safe_next_action": "Review trust-tier decision packet; require separate operator approval before any promotion, regression, or expansion.",
    }


def validate_trust_tier_decision_gate(
    decision: Any,
    *,
    expected_approval_token_id: str,
    now: datetime | None = None,
) -> TrustTierDecisionGateValidation:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []
    expected_approval_token_id = expected_approval_token_id.strip() if expected_approval_token_id else ""
    if not expected_approval_token_id:
        reasons.append("missing_expected_approval_token_id")

    payload = _decision_payload(decision)
    if payload is None:
        reasons.append("malformed_trust_tier_decision_gate")
        return _validation(
            reasons=reasons,
            current_time=current_time,
            decision_id=None,
            requested_expansion_class=None,
            current_trust_tier=None,
            requested_trust_tier=None,
            decision_outcome=None,
            evidence_paths=(),
            soak_evidence_hours=None,
            rollback_proof_recorded=None,
            false_positive_count=None,
            false_negative_count=None,
            stop_event_count=None,
            approval_token_id=None,
        )

    for field in TRUST_TIER_DECISION_REQUIRED_FIELDS:
        if field not in payload:
            reasons.append(f"missing_required_field:{field}")

    decision_id = _string_field(payload, "decision_id", reasons)
    requested_expansion_class = _string_field(payload, "requested_expansion_class", reasons)
    current_trust_tier = _string_field(payload, "current_trust_tier", reasons)
    requested_trust_tier = _string_field(payload, "requested_trust_tier", reasons)
    decision_outcome = _string_field(payload, "decision_outcome", reasons)
    evidence_paths = _string_tuple_field(payload, "evidence_paths", reasons)
    soak_evidence_hours = _int_field(payload, "soak_evidence_hours", reasons)
    rollback_proof_recorded = _bool_field(payload, "rollback_proof_recorded", reasons)
    false_positive_count = _int_field(payload, "false_positive_count", reasons)
    false_negative_count = _int_field(payload, "false_negative_count", reasons)
    stop_event_count = _int_field(payload, "stop_event_count", reasons)
    operator_review_required = payload.get("operator_review_required")
    operator_review_recorded = _bool_field(payload, "operator_review_recorded", reasons)
    approval_token_id = _string_field(payload, "approval_token_id", reasons)
    status = _string_field(payload, "status", reasons)
    created_at = _datetime_value(payload.get("created_at"))

    if requested_expansion_class and requested_expansion_class not in EXPANSION_CLASSES_REQUIRING_TRUST_TIER_REVIEW:
        reasons.append("unknown_requested_expansion_class")
    if current_trust_tier and current_trust_tier not in TRUST_TIERS:
        reasons.append("unknown_current_trust_tier")
    if requested_trust_tier and requested_trust_tier not in TRUST_TIERS:
        reasons.append("unknown_requested_trust_tier")
    if decision_outcome and decision_outcome not in TRUST_TIER_DECISION_OUTCOMES:
        reasons.append("unknown_decision_outcome")
    if current_trust_tier in TRUST_TIERS and requested_trust_tier in TRUST_TIERS:
        current_index = TRUST_TIERS.index(current_trust_tier)
        requested_index = TRUST_TIERS.index(requested_trust_tier)
        if decision_outcome == "advance" and requested_index != current_index + 1:
            reasons.append("advance_must_request_next_trust_tier")
        if decision_outcome == "hold" and requested_index != current_index:
            reasons.append("hold_must_keep_current_trust_tier")
        if decision_outcome == "demote" and requested_index >= current_index:
            reasons.append("demote_must_lower_trust_tier")
    if soak_evidence_hours is not None and soak_evidence_hours < 0:
        reasons.append("soak_evidence_hours_must_be_non_negative")
    if false_positive_count is not None and false_positive_count < 0:
        reasons.append("false_positive_count_must_be_non_negative")
    if false_negative_count is not None and false_negative_count < 0:
        reasons.append("false_negative_count_must_be_non_negative")
    if stop_event_count is not None and stop_event_count < 0:
        reasons.append("stop_event_count_must_be_non_negative")
    if decision_outcome == "advance":
        if soak_evidence_hours is not None and soak_evidence_hours < 72:
            reasons.append("advance_requires_72_hour_soak")
        if rollback_proof_recorded is not True:
            reasons.append("advance_requires_rollback_proof")
        if false_positive_count is not None and false_positive_count != 0:
            reasons.append("advance_blocked_by_false_positives")
        if false_negative_count is not None and false_negative_count != 0:
            reasons.append("advance_blocked_by_false_negatives")
        if stop_event_count is not None and stop_event_count != 0:
            reasons.append("advance_blocked_by_stop_events")
    if decision_outcome == "demote":
        regression_count = sum(
            value or 0 for value in (false_positive_count, false_negative_count, stop_event_count)
        )
        if regression_count == 0 and rollback_proof_recorded is True:
            reasons.append("demote_requires_regression_signal")
    if evidence_paths == ():
        reasons.append("missing_evidence_paths")
    if len(set(evidence_paths)) != len(evidence_paths):
        reasons.append("duplicate_evidence_path")
    for evidence_path in evidence_paths:
        if _is_broad_file_scope(evidence_path):
            reasons.append("broad_evidence_path")
        if not evidence_path.startswith("docs/"):
            reasons.append("evidence_path_must_be_docs")
        if not evidence_path.endswith(".md"):
            reasons.append("evidence_path_must_be_markdown")
    if operator_review_required is not True:
        reasons.append("operator_review_must_be_required")
    if operator_review_recorded is not True:
        reasons.append("operator_review_must_be_recorded")
    if approval_token_id and approval_token_id != expected_approval_token_id:
        reasons.append("wrong_approval_token")
    if status and status != "proposed":
        reasons.append("status_must_remain_proposed")
    if created_at is None:
        reasons.append("invalid_created_at")
    elif created_at > current_time:
        reasons.append("created_at_in_future")

    return _validation(
        reasons=reasons,
        current_time=current_time,
        decision_id=decision_id,
        requested_expansion_class=requested_expansion_class,
        current_trust_tier=current_trust_tier,
        requested_trust_tier=requested_trust_tier,
        decision_outcome=decision_outcome,
        evidence_paths=evidence_paths,
        soak_evidence_hours=soak_evidence_hours,
        rollback_proof_recorded=rollback_proof_recorded,
        false_positive_count=false_positive_count,
        false_negative_count=false_negative_count,
        stop_event_count=stop_event_count,
        approval_token_id=approval_token_id,
    )


def _validation(
    *,
    reasons: list[str],
    current_time: datetime,
    decision_id: str | None,
    requested_expansion_class: str | None,
    current_trust_tier: str | None,
    requested_trust_tier: str | None,
    decision_outcome: str | None,
    evidence_paths: tuple[str, ...],
    soak_evidence_hours: int | None,
    rollback_proof_recorded: bool | None,
    false_positive_count: int | None,
    false_negative_count: int | None,
    stop_event_count: int | None,
    approval_token_id: str | None,
) -> TrustTierDecisionGateValidation:
    blocked_reasons = tuple(dict.fromkeys(reasons))
    accepted_for_review = not blocked_reasons
    return TrustTierDecisionGateValidation(
        phase=TRUST_TIER_DECISION_GATE_PHASE,
        status="accepted_for_review" if accepted_for_review else "blocked",
        accepted_for_review=accepted_for_review,
        blocked=not accepted_for_review,
        reasons=blocked_reasons,
        decision_id=decision_id,
        requested_expansion_class=requested_expansion_class,
        current_trust_tier=current_trust_tier,
        requested_trust_tier=requested_trust_tier,
        decision_outcome=decision_outcome,
        evidence_paths=evidence_paths,
        soak_evidence_hours=soak_evidence_hours,
        rollback_proof_recorded=rollback_proof_recorded,
        false_positive_count=false_positive_count,
        false_negative_count=false_negative_count,
        stop_event_count=stop_event_count,
        approval_token_id=approval_token_id,
        validated_at=_format_utc(current_time),
    )


def _decision_payload(decision: Any) -> dict[str, Any] | None:
    if isinstance(decision, TrustTierDecisionGate):
        return decision.to_dict()
    if isinstance(decision, dict):
        return decision
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


def _int_field(payload: dict[str, Any], field: str, reasons: list[str]) -> int | None:
    value = payload.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        reasons.append(f"invalid_{field}")
        return None
    return value


def _bool_field(payload: dict[str, Any], field: str, reasons: list[str]) -> bool | None:
    value = payload.get(field)
    if not isinstance(value, bool):
        reasons.append(f"invalid_{field}")
        return None
    return value


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
