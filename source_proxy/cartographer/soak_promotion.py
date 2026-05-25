from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import Any


INTEGRATED_CONTROL_PLAN_10 = "Cartographer Integrated Control Master Plan 10/10"
TEN_TASK_SUPERVISED_RUN_PHASE = "Plan 10 Phase 10.1: 10-task supervised run"
TWENTY_FOUR_HOUR_SOAK_PHASE = "Plan 10 Phase 10.2: 24-hour soak"
SEVENTY_TWO_HOUR_SOAK_PHASE = "Plan 10 Phase 10.2: 72-hour soak"
KILL_SWITCH_AND_ROLLBACK_DRILLS_PHASE = "Plan 10 Phase 10.2: Kill switch and rollback drills"
PROMOTION_DECISION_PHASE = "Plan 10 Phase 10.2: Promotion decision"
TEN_TASK_SUPERVISED_RUN_REQUIRED_COUNT = 10
TWENTY_FOUR_HOUR_SOAK_REQUIRED_HOURS = 24
SEVENTY_TWO_HOUR_SOAK_REQUIRED_HOURS = 72
REQUIRED_KILL_SWITCH_DRILL_STAGES: tuple[str, ...] = (
    "before_selection",
    "mid_workflow",
    "after_verification",
    "before_commit_push",
)
PROMOTION_TIERS: dict[str, tuple[str, ...]] = {
    "tier-1": (
        "auto_safe_docs",
        "auto_safe_evidence",
        "auto_safe_receipts",
        "human_gated_commit",
        "human_gated_push",
    ),
    "tier-2": (
        "auto_safe_docs",
        "auto_safe_evidence",
        "auto_safe_receipts",
        "auto_local_commit",
        "human_gated_push",
    ),
    "tier-3": (
        "auto_safe_docs",
        "auto_safe_evidence",
        "auto_safe_receipts",
        "auto_local_commit",
        "auto_isolated_branch_push",
    ),
}
SAFE_SUPERVISED_ACTION_CLASSES: tuple[str, ...] = (
    "docs",
    "evidence",
    "receipt",
)

FORBIDDEN_SOAK_AUTHORITIES: tuple[str, ...] = (
    "background_loop",
    "queue_execution",
    "task_execution",
    "command_execution",
    "safe_write",
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
class DailyDriverSoakVerification:
    status: str
    checks: tuple[str, ...]
    checked_at: str

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class SupervisedSafeTaskReceipt:
    task_id: str
    action_class: str
    trust_tier: str
    approval_token_id: str
    exact_files: tuple[str, ...]
    receipt_path: str
    status: str
    verification: dict[str, Any]
    rollback_guidance: str
    kill_switch_checked: bool
    operator_supervised: bool
    started_at: str
    completed_at: str
    human_reviewed: bool = True
    false_positive_count: int = 0
    false_negative_count: int = 0
    next_task_auto_started: bool = False
    background_loop_started: bool = False
    task_executed_by_soak_model: bool = False
    command_executed_by_soak_model: bool = False
    write_performed_by_soak_model: bool = False
    commit_performed_by_soak_model: bool = False
    push_performed_by_soak_model: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class TenTaskSupervisedRunValidation:
    phase: str
    status: str
    passed: bool
    blocked: bool
    reasons: tuple[str, ...]
    task_count: int
    receipt_paths: tuple[str, ...]
    task_ids: tuple[str, ...]
    first_supervised_receipt_path: str | None
    false_positive_count: int
    false_negative_count: int
    supervised_trial_summary: dict[str, Any]
    validated_at: str
    operator_supervision_required: bool = True
    human_review_required: bool = True
    background_loop_enabled: bool = False
    queue_execution_enabled: bool = False
    task_execution_enabled: bool = False
    command_execution_enabled: bool = False
    safe_write_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    durable_storage_written: bool = False
    api_mutation_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class TwentyFourHourSoakSample:
    sample_id: str
    hour: int
    bounded_invocation_count: int
    queue_depth: int
    blocked_task_count: int
    receipt_count: int
    kill_switch_checked: bool
    hidden_loop_detected: bool
    hidden_mutation_detected: bool
    head_changed: bool
    dirty_worktree_explained: bool
    protected_lane_mutation_detected: bool
    manual_intervention_required: bool
    sampled_at: str
    false_positive_count: int = 0
    false_negative_count: int = 0
    stop_events: tuple[str, ...] = ()
    operator_reviewed: bool = True
    drift_status: str = "clear"
    protected_lane_status: str = "clear"
    queue_status: str = "healthy"
    queue_executed_by_soak_model: bool = False
    task_executed_by_soak_model: bool = False
    command_executed_by_soak_model: bool = False
    write_performed_by_soak_model: bool = False
    commit_performed_by_soak_model: bool = False
    push_performed_by_soak_model: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class TwentyFourHourSoakValidation:
    phase: str
    status: str
    passed: bool
    blocked: bool
    reasons: tuple[str, ...]
    requested_duration_hours: int
    sample_count: int
    sample_ids: tuple[str, ...]
    validated_at: str
    bounded_invocations_only: bool = True
    false_positive_tracking_required: bool = True
    false_negative_tracking_required: bool = True
    stop_event_tracking_required: bool = True
    operator_review_required: bool = True
    background_loop_enabled: bool = False
    hidden_loop_allowed: bool = False
    queue_execution_enabled: bool = False
    task_execution_enabled: bool = False
    command_execution_enabled: bool = False
    safe_write_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    durable_storage_written: bool = False
    api_mutation_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class SeventyTwoHourSoakValidation:
    phase: str
    status: str
    passed: bool
    blocked: bool
    reasons: tuple[str, ...]
    requested_duration_hours: int
    sample_count: int
    sample_ids: tuple[str, ...]
    validated_at: str
    drift_checks_required: bool = True
    protected_lane_checks_required: bool = True
    queue_checks_required: bool = True
    bounded_invocations_only: bool = True
    false_positive_tracking_required: bool = True
    false_negative_tracking_required: bool = True
    stop_event_tracking_required: bool = True
    operator_review_required: bool = True
    background_loop_enabled: bool = False
    hidden_loop_allowed: bool = False
    queue_execution_enabled: bool = False
    task_execution_enabled: bool = False
    command_execution_enabled: bool = False
    safe_write_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    durable_storage_written: bool = False
    api_mutation_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class KillSwitchRollbackDrill:
    drill_id: str
    stage: str
    kill_switch_engaged: bool
    action_blocked: bool
    queue_execution_blocked: bool
    task_execution_blocked: bool
    command_execution_blocked: bool
    write_blocked: bool
    commit_blocked: bool
    push_blocked: bool
    rollback_guidance: str
    receipt_path: str
    verified_at: str
    rollback_executed_by_drill_model: bool = False
    mutation_performed_by_drill_model: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class KillSwitchRollbackDrillValidation:
    phase: str
    status: str
    passed: bool
    blocked: bool
    reasons: tuple[str, ...]
    drill_count: int
    drill_ids: tuple[str, ...]
    validated_at: str
    required_stages: tuple[str, ...] = REQUIRED_KILL_SWITCH_DRILL_STAGES
    rollback_guidance_required: bool = True
    rollback_execution_enabled: bool = False
    background_loop_enabled: bool = False
    queue_execution_enabled: bool = False
    task_execution_enabled: bool = False
    command_execution_enabled: bool = False
    safe_write_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    durable_storage_written: bool = False
    api_mutation_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class PromotionDecisionRecord:
    phase: str
    decision_id: str
    status: str
    recorded: bool
    blocked: bool
    reasons: tuple[str, ...]
    tier: str | None
    allowed_actions: tuple[str, ...]
    decided_by: str | None
    decided_at: str
    evidence: dict[str, Any]
    decision_packet: dict[str, Any]
    authority_change_requested: bool
    authority_granted_by_record: bool = False
    activation_requires_plan_12_explicit_approval: bool = True
    limited_daily_driver_activation_allowed: bool = False
    background_loop_enabled: bool = False
    queue_execution_enabled: bool = False
    task_execution_enabled: bool = False
    command_execution_enabled: bool = False
    safe_write_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    durable_storage_written: bool = False
    api_mutation_available: bool = False
    self_promotion_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_ten_task_supervised_run_status() -> dict[str, Any]:
    return {
        "plan": INTEGRATED_CONTROL_PLAN_10,
        "phase": TEN_TASK_SUPERVISED_RUN_PHASE,
        "status": "supervised-run-validation-only",
        "required_task_count": TEN_TASK_SUPERVISED_RUN_REQUIRED_COUNT,
        "safe_action_classes": SAFE_SUPERVISED_ACTION_CLASSES,
        "forbidden_authorities": FORBIDDEN_SOAK_AUTHORITIES,
        "operator_supervision_required": True,
        "human_review_required": True,
        "one_supervised_task_first": True,
        "ten_supervised_receipts_required": True,
        "false_positive_tracking_required": True,
        "false_negative_tracking_required": True,
        "supervised_trial_summary_available": True,
        "background_loop_enabled": False,
        "queue_execution_enabled": False,
        "task_execution_enabled": False,
        "command_execution_enabled": False,
        "safe_write_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "durable_storage_written": False,
        "api_mutation_available": False,
        "safe_next_action": "Validate exactly 10 supervised safe-task receipts before any 24-hour soak work.",
    }


def build_twenty_four_hour_soak_status() -> dict[str, Any]:
    return {
        "plan": INTEGRATED_CONTROL_PLAN_10,
        "phase": TWENTY_FOUR_HOUR_SOAK_PHASE,
        "status": "bounded-soak-validation-only",
        "required_duration_hours": TWENTY_FOUR_HOUR_SOAK_REQUIRED_HOURS,
        "forbidden_authorities": FORBIDDEN_SOAK_AUTHORITIES,
        "bounded_invocations_only": True,
        "false_positive_tracking_required": True,
        "false_negative_tracking_required": True,
        "stop_event_tracking_required": True,
        "operator_review_required": True,
        "background_loop_enabled": False,
        "hidden_loop_allowed": False,
        "queue_execution_enabled": False,
        "task_execution_enabled": False,
        "command_execution_enabled": False,
        "safe_write_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "durable_storage_written": False,
        "api_mutation_available": False,
        "safe_next_action": "Validate bounded 24-hour soak samples before any 72-hour soak work.",
    }


def build_seventy_two_hour_soak_status() -> dict[str, Any]:
    return {
        "plan": INTEGRATED_CONTROL_PLAN_10,
        "phase": SEVENTY_TWO_HOUR_SOAK_PHASE,
        "status": "bounded-soak-validation-only",
        "required_duration_hours": SEVENTY_TWO_HOUR_SOAK_REQUIRED_HOURS,
        "forbidden_authorities": FORBIDDEN_SOAK_AUTHORITIES,
        "drift_checks_required": True,
        "protected_lane_checks_required": True,
        "queue_checks_required": True,
        "bounded_invocations_only": True,
        "false_positive_tracking_required": True,
        "false_negative_tracking_required": True,
        "stop_event_tracking_required": True,
        "operator_review_required": True,
        "background_loop_enabled": False,
        "hidden_loop_allowed": False,
        "queue_execution_enabled": False,
        "task_execution_enabled": False,
        "command_execution_enabled": False,
        "safe_write_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "durable_storage_written": False,
        "api_mutation_available": False,
        "safe_next_action": "Validate bounded 72-hour soak samples before kill switch and rollback drills.",
    }


def build_kill_switch_rollback_drill_status() -> dict[str, Any]:
    return {
        "plan": INTEGRATED_CONTROL_PLAN_10,
        "phase": KILL_SWITCH_AND_ROLLBACK_DRILLS_PHASE,
        "status": "drill-validation-only",
        "required_stages": REQUIRED_KILL_SWITCH_DRILL_STAGES,
        "forbidden_authorities": FORBIDDEN_SOAK_AUTHORITIES,
        "rollback_guidance_required": True,
        "rollback_execution_enabled": False,
        "background_loop_enabled": False,
        "queue_execution_enabled": False,
        "task_execution_enabled": False,
        "command_execution_enabled": False,
        "safe_write_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "durable_storage_written": False,
        "api_mutation_available": False,
        "safe_next_action": "Validate kill switch and rollback drills before recording a promotion decision.",
    }


def build_promotion_decision_status() -> dict[str, Any]:
    return {
        "plan": INTEGRATED_CONTROL_PLAN_10,
        "phase": PROMOTION_DECISION_PHASE,
        "status": "decision-record-validation-only",
        "promotion_tiers": PROMOTION_TIERS,
        "forbidden_authorities": FORBIDDEN_SOAK_AUTHORITIES,
        "decision_packet_available": True,
        "activation_requires_plan_12_explicit_approval": True,
        "authority_granted_by_record": False,
        "limited_daily_driver_activation_allowed": False,
        "background_loop_enabled": False,
        "queue_execution_enabled": False,
        "task_execution_enabled": False,
        "command_execution_enabled": False,
        "safe_write_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "durable_storage_written": False,
        "api_mutation_available": False,
        "self_promotion_allowed": False,
        "safe_next_action": "Record exact promotion tier and allowed actions; require separate implementation approval to enable runtime authority.",
    }


def validate_ten_task_supervised_run(
    receipts: Any,
    *,
    expected_trust_tier: str,
    expected_approval_token_prefix: str,
    now: datetime | None = None,
) -> TenTaskSupervisedRunValidation:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []
    expected_trust_tier = expected_trust_tier.strip() if expected_trust_tier else ""
    expected_approval_token_prefix = (
        expected_approval_token_prefix.strip() if expected_approval_token_prefix else ""
    )
    if not expected_trust_tier:
        reasons.append("missing_expected_trust_tier")
    if not expected_approval_token_prefix:
        reasons.append("missing_expected_approval_token_prefix")
    if not isinstance(receipts, (list, tuple)):
        reasons.append("invalid_receipts")
        receipt_payloads: tuple[dict[str, Any], ...] = ()
    else:
        receipt_payloads = tuple(_receipt_payload(receipt) for receipt in receipts)

    if len(receipt_payloads) != TEN_TASK_SUPERVISED_RUN_REQUIRED_COUNT:
        reasons.append("ten_supervised_task_receipts_required")

    task_ids: list[str] = []
    receipt_paths: list[str] = []
    false_positive_count = 0
    false_negative_count = 0
    for index, receipt in enumerate(receipt_payloads):
        task_id = _string_value(receipt, "task_id")
        receipt_path = _string_value(receipt, "receipt_path")
        task_ids.append(task_id or f"missing-task-{index}")
        if receipt_path:
            receipt_paths.append(receipt_path)

        if not task_id:
            reasons.append(f"missing_task_id:{index}")
        if _string_value(receipt, "action_class") not in SAFE_SUPERVISED_ACTION_CLASSES:
            reasons.append(f"unsafe_action_class:{task_id or index}")
        if _string_value(receipt, "trust_tier") != expected_trust_tier:
            reasons.append(f"wrong_trust_tier:{task_id or index}")
        approval_token_id = _string_value(receipt, "approval_token_id")
        if not approval_token_id or not approval_token_id.startswith(expected_approval_token_prefix):
            reasons.append(f"wrong_approval_token:{task_id or index}")
        exact_files = _tuple_value(receipt, "exact_files")
        if not exact_files:
            reasons.append(f"missing_exact_files:{task_id or index}")
        if any(_is_broad_file_scope(path) for path in exact_files):
            reasons.append(f"broad_exact_files:{task_id or index}")
        if not receipt_path:
            reasons.append(f"missing_receipt_path:{task_id or index}")
        elif not receipt_path.startswith("docs/"):
            reasons.append(f"receipt_path_must_be_docs:{task_id or index}")
        if _string_value(receipt, "status") != "passed":
            reasons.append(f"task_not_passed:{task_id or index}")
        verification = _verification(receipt.get("verification"), reasons, task_id or str(index))
        if verification is not None and verification.get("status") != "passed":
            reasons.append(f"verification_not_passed:{task_id or index}")
        if not _string_value(receipt, "rollback_guidance"):
            reasons.append(f"missing_rollback_guidance:{task_id or index}")
        if not bool(receipt.get("kill_switch_checked")):
            reasons.append(f"kill_switch_not_checked:{task_id or index}")
        if not bool(receipt.get("operator_supervised")):
            reasons.append(f"operator_supervision_missing:{task_id or index}")
        if receipt.get("human_reviewed") is not True:
            reasons.append(f"human_review_missing:{task_id or index}")
        receipt_false_positive_count = _count_value(receipt, "false_positive_count")
        receipt_false_negative_count = _count_value(receipt, "false_negative_count")
        if receipt_false_positive_count is None:
            reasons.append(f"invalid_false_positive_count:{task_id or index}")
        else:
            false_positive_count += receipt_false_positive_count
        if receipt_false_negative_count is None:
            reasons.append(f"invalid_false_negative_count:{task_id or index}")
        else:
            false_negative_count += receipt_false_negative_count
        if bool(receipt.get("next_task_auto_started")):
            reasons.append(f"next_task_auto_started:{task_id or index}")
        if bool(receipt.get("background_loop_started")):
            reasons.append(f"background_loop_started:{task_id or index}")
        if _datetime_value(receipt.get("started_at")) is None:
            reasons.append(f"invalid_started_at:{task_id or index}")
        completed_at = _datetime_value(receipt.get("completed_at"))
        if completed_at is None:
            reasons.append(f"invalid_completed_at:{task_id or index}")
        elif completed_at > current_time:
            reasons.append(f"completed_at_in_future:{task_id or index}")
        if any(
            bool(receipt.get(flag))
            for flag in (
                "task_executed_by_soak_model",
                "command_executed_by_soak_model",
                "write_performed_by_soak_model",
                "commit_performed_by_soak_model",
                "push_performed_by_soak_model",
            )
        ):
            reasons.append(f"soak_model_performed_forbidden_action:{task_id or index}")

    if len(set(task_ids)) != len(task_ids):
        reasons.append("duplicate_task_id")
    if len(set(receipt_paths)) != len(receipt_paths):
        reasons.append("duplicate_receipt_path")

    blocked_reasons = tuple(dict.fromkeys(reasons))
    passed = not blocked_reasons
    first_receipt_path = receipt_paths[0] if receipt_paths else None
    return TenTaskSupervisedRunValidation(
        phase=TEN_TASK_SUPERVISED_RUN_PHASE,
        status="passed" if passed else "blocked",
        passed=passed,
        blocked=not passed,
        reasons=blocked_reasons,
        task_count=len(receipt_payloads),
        receipt_paths=tuple(receipt_paths),
        task_ids=tuple(task_ids),
        first_supervised_receipt_path=first_receipt_path,
        false_positive_count=false_positive_count,
        false_negative_count=false_negative_count,
        supervised_trial_summary=_supervised_trial_summary(
            status="passed" if passed else "blocked",
            reasons=blocked_reasons,
            task_ids=tuple(task_ids),
            receipt_paths=tuple(receipt_paths),
            false_positive_count=false_positive_count,
            false_negative_count=false_negative_count,
            validated_at=_format_utc(current_time),
        ),
        validated_at=_format_utc(current_time),
    )


def validate_twenty_four_hour_soak(
    samples: Any,
    *,
    requested_duration_hours: int,
    now: datetime | None = None,
) -> TwentyFourHourSoakValidation:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []
    if requested_duration_hours != TWENTY_FOUR_HOUR_SOAK_REQUIRED_HOURS:
        reasons.append("duration_must_be_exactly_24_hours")
    sample_payloads, sample_ids, hours = _validate_soak_sample_basics(
        samples=samples,
        reasons=reasons,
        current_time=current_time,
        required_hours=TWENTY_FOUR_HOUR_SOAK_REQUIRED_HOURS,
    )

    blocked_reasons = tuple(dict.fromkeys(reasons))
    passed = not blocked_reasons
    return TwentyFourHourSoakValidation(
        phase=TWENTY_FOUR_HOUR_SOAK_PHASE,
        status="passed" if passed else "blocked",
        passed=passed,
        blocked=not passed,
        reasons=blocked_reasons,
        requested_duration_hours=requested_duration_hours,
        sample_count=len(sample_payloads),
        sample_ids=tuple(sample_ids),
        validated_at=_format_utc(current_time),
    )


def validate_seventy_two_hour_soak(
    samples: Any,
    *,
    requested_duration_hours: int,
    now: datetime | None = None,
) -> SeventyTwoHourSoakValidation:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []
    if requested_duration_hours != SEVENTY_TWO_HOUR_SOAK_REQUIRED_HOURS:
        reasons.append("duration_must_be_exactly_72_hours")
    sample_payloads, sample_ids, _hours = _validate_soak_sample_basics(
        samples=samples,
        reasons=reasons,
        current_time=current_time,
        required_hours=SEVENTY_TWO_HOUR_SOAK_REQUIRED_HOURS,
    )
    for index, sample in enumerate(sample_payloads):
        sample_id = _string_value(sample, "sample_id") or str(index)
        if _string_value(sample, "drift_status") != "clear":
            reasons.append(f"drift_not_clear:{sample_id}")
        if _string_value(sample, "protected_lane_status") != "clear":
            reasons.append(f"protected_lane_not_clear:{sample_id}")
        if _string_value(sample, "queue_status") != "healthy":
            reasons.append(f"queue_not_healthy:{sample_id}")
        if sample.get("queue_depth") != 0:
            reasons.append(f"queue_depth_not_empty:{sample_id}")
        if sample.get("blocked_task_count") != 0:
            reasons.append(f"blocked_tasks_present:{sample_id}")
        if not isinstance(sample.get("receipt_count"), int) or int(sample.get("receipt_count", 0)) < TEN_TASK_SUPERVISED_RUN_REQUIRED_COUNT:
            reasons.append(f"receipt_count_below_supervised_run:{sample_id}")

    blocked_reasons = tuple(dict.fromkeys(reasons))
    passed = not blocked_reasons
    return SeventyTwoHourSoakValidation(
        phase=SEVENTY_TWO_HOUR_SOAK_PHASE,
        status="passed" if passed else "blocked",
        passed=passed,
        blocked=not passed,
        reasons=blocked_reasons,
        requested_duration_hours=requested_duration_hours,
        sample_count=len(sample_payloads),
        sample_ids=tuple(sample_ids),
        validated_at=_format_utc(current_time),
    )


def validate_kill_switch_rollback_drills(
    drills: Any,
    *,
    now: datetime | None = None,
) -> KillSwitchRollbackDrillValidation:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []
    if not isinstance(drills, (list, tuple)):
        reasons.append("invalid_kill_switch_drills")
        drill_payloads: tuple[dict[str, Any], ...] = ()
    else:
        drill_payloads = tuple(_drill_payload(drill) for drill in drills)

    drill_ids: list[str] = []
    stages: list[str] = []
    for index, drill in enumerate(drill_payloads):
        drill_id = _string_value(drill, "drill_id")
        stage = _string_value(drill, "stage")
        drill_ids.append(drill_id or f"missing-drill-{index}")
        if stage:
            stages.append(stage)
        if not drill_id:
            reasons.append(f"missing_drill_id:{index}")
        if stage not in REQUIRED_KILL_SWITCH_DRILL_STAGES:
            reasons.append(f"unknown_drill_stage:{drill_id or index}")
        if not bool(drill.get("kill_switch_engaged")):
            reasons.append(f"kill_switch_not_engaged:{drill_id or index}")
        for field in (
            "action_blocked",
            "queue_execution_blocked",
            "task_execution_blocked",
            "command_execution_blocked",
            "write_blocked",
            "commit_blocked",
            "push_blocked",
        ):
            if not bool(drill.get(field)):
                reasons.append(f"{field}_missing:{drill_id or index}")
        if not _string_value(drill, "rollback_guidance"):
            reasons.append(f"missing_rollback_guidance:{drill_id or index}")
        receipt_path = _string_value(drill, "receipt_path")
        if not receipt_path:
            reasons.append(f"missing_receipt_path:{drill_id or index}")
        elif not receipt_path.startswith("docs/"):
            reasons.append(f"receipt_path_must_be_docs:{drill_id or index}")
        verified_at = _datetime_value(drill.get("verified_at"))
        if verified_at is None:
            reasons.append(f"invalid_verified_at:{drill_id or index}")
        elif verified_at > current_time:
            reasons.append(f"verified_at_in_future:{drill_id or index}")
        if bool(drill.get("rollback_executed_by_drill_model")):
            reasons.append(f"rollback_executed_by_drill_model:{drill_id or index}")
        if bool(drill.get("mutation_performed_by_drill_model")):
            reasons.append(f"mutation_performed_by_drill_model:{drill_id or index}")

    missing_stages = set(REQUIRED_KILL_SWITCH_DRILL_STAGES) - set(stages)
    for stage in sorted(missing_stages):
        reasons.append(f"missing_required_drill_stage:{stage}")
    if len(set(drill_ids)) != len(drill_ids):
        reasons.append("duplicate_drill_id")
    if len(set(stages)) != len(stages):
        reasons.append("duplicate_drill_stage")

    blocked_reasons = tuple(dict.fromkeys(reasons))
    passed = not blocked_reasons
    return KillSwitchRollbackDrillValidation(
        phase=KILL_SWITCH_AND_ROLLBACK_DRILLS_PHASE,
        status="passed" if passed else "blocked",
        passed=passed,
        blocked=not passed,
        reasons=blocked_reasons,
        drill_count=len(drill_payloads),
        drill_ids=tuple(drill_ids),
        validated_at=_format_utc(current_time),
    )


def record_promotion_decision(
    *,
    tier: str,
    allowed_actions: Any,
    decided_by: str,
    ten_task_validation: Any,
    twenty_four_hour_validation: Any,
    seventy_two_hour_validation: Any,
    kill_switch_drill_validation: Any,
    authority_change_requested: bool,
    now: datetime | None = None,
) -> PromotionDecisionRecord:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []
    tier = tier.strip() if tier else ""
    decided_by = decided_by.strip() if decided_by else ""
    if tier not in PROMOTION_TIERS:
        reasons.append("unknown_promotion_tier")
        allowed_for_tier: tuple[str, ...] = ()
    else:
        allowed_for_tier = PROMOTION_TIERS[tier]
    if not decided_by:
        reasons.append("missing_decided_by")
    if decided_by.lower() in {"cartographer", "cartographer-runtime", "automation"}:
        reasons.append("self_promotion_blocked")
    if not isinstance(allowed_actions, (list, tuple)):
        reasons.append("invalid_allowed_actions")
        normalized_actions: tuple[str, ...] = ()
    else:
        normalized_actions = tuple(
            action.strip()
            for action in allowed_actions
            if isinstance(action, str) and action.strip()
        )
    if not normalized_actions:
        reasons.append("missing_allowed_actions")
    if len(set(normalized_actions)) != len(normalized_actions):
        reasons.append("duplicate_allowed_action")
    for action in normalized_actions:
        if action not in allowed_for_tier:
            reasons.append(f"action_not_allowed_for_tier:{action}")

    evidence = {
        "ten_task": _validation_status(ten_task_validation),
        "twenty_four_hour": _validation_status(twenty_four_hour_validation),
        "seventy_two_hour": _validation_status(seventy_two_hour_validation),
        "kill_switch_drills": _validation_status(kill_switch_drill_validation),
    }
    for key, status in evidence.items():
        if status != "passed":
            reasons.append(f"required_evidence_not_passed:{key}")

    if authority_change_requested:
        reasons.append("authority_change_requires_separate_implementation_approval")

    blocked_reasons = tuple(dict.fromkeys(reasons))
    recorded = not blocked_reasons
    return PromotionDecisionRecord(
        phase=PROMOTION_DECISION_PHASE,
        decision_id=_promotion_decision_id(tier=tier, status="recorded" if recorded else "blocked"),
        status="recorded" if recorded else "blocked",
        recorded=recorded,
        blocked=not recorded,
        reasons=blocked_reasons,
        tier=tier or None,
        allowed_actions=normalized_actions,
        decided_by=decided_by or None,
        decided_at=_format_utc(current_time),
        evidence=evidence,
        decision_packet=_promotion_decision_packet(
            status="recorded" if recorded else "blocked",
            reasons=blocked_reasons,
            tier=tier or None,
            allowed_actions=normalized_actions,
            decided_by=decided_by or None,
            evidence=evidence,
            decided_at=_format_utc(current_time),
        ),
        authority_change_requested=authority_change_requested,
    )


def _validate_soak_sample_basics(
    *,
    samples: Any,
    reasons: list[str],
    current_time: datetime,
    required_hours: int,
) -> tuple[tuple[dict[str, Any], ...], list[str], list[int]]:
    if not isinstance(samples, (list, tuple)):
        reasons.append("invalid_soak_samples")
        sample_payloads: tuple[dict[str, Any], ...] = ()
    else:
        sample_payloads = tuple(_sample_payload(sample) for sample in samples)
    if len(sample_payloads) < 2:
        reasons.append("missing_soak_samples")

    sample_ids: list[str] = []
    hours: list[int] = []
    for index, sample in enumerate(sample_payloads):
        sample_id = _string_value(sample, "sample_id")
        sample_ids.append(sample_id or f"missing-sample-{index}")
        hour = sample.get("hour")
        if not isinstance(hour, int):
            reasons.append(f"invalid_sample_hour:{sample_id or index}")
        else:
            hours.append(hour)
            if hour < 0 or hour > required_hours:
                reasons.append(f"sample_hour_outside_{required_hours}_hour_window:{sample_id or index}")
        bounded_invocation_count = sample.get("bounded_invocation_count")
        if not isinstance(bounded_invocation_count, int) or bounded_invocation_count < 0:
            reasons.append(f"invalid_bounded_invocation_count:{sample_id or index}")
        queue_depth = sample.get("queue_depth")
        if not isinstance(queue_depth, int) or queue_depth < 0:
            reasons.append(f"invalid_queue_depth:{sample_id or index}")
        blocked_task_count = sample.get("blocked_task_count")
        if not isinstance(blocked_task_count, int) or blocked_task_count < 0:
            reasons.append(f"invalid_blocked_task_count:{sample_id or index}")
        receipt_count = sample.get("receipt_count")
        if not isinstance(receipt_count, int) or receipt_count < 0:
            reasons.append(f"invalid_receipt_count:{sample_id or index}")
        if not bool(sample.get("kill_switch_checked")):
            reasons.append(f"kill_switch_not_checked:{sample_id or index}")
        if bool(sample.get("hidden_loop_detected")):
            reasons.append(f"hidden_loop_detected:{sample_id or index}")
        if bool(sample.get("hidden_mutation_detected")):
            reasons.append(f"hidden_mutation_detected:{sample_id or index}")
        if bool(sample.get("head_changed")):
            reasons.append(f"head_changed:{sample_id or index}")
        if not bool(sample.get("dirty_worktree_explained")):
            reasons.append(f"dirty_worktree_unexplained:{sample_id or index}")
        if bool(sample.get("protected_lane_mutation_detected")):
            reasons.append(f"protected_lane_mutation_detected:{sample_id or index}")
        if bool(sample.get("manual_intervention_required")):
            reasons.append(f"manual_intervention_required:{sample_id or index}")
        false_positive_count = sample.get("false_positive_count")
        if not isinstance(false_positive_count, int) or false_positive_count < 0:
            reasons.append(f"invalid_false_positive_count:{sample_id or index}")
        false_negative_count = sample.get("false_negative_count")
        if not isinstance(false_negative_count, int) or false_negative_count < 0:
            reasons.append(f"invalid_false_negative_count:{sample_id or index}")
        elif false_negative_count > 0:
            reasons.append(f"false_negative_detected:{sample_id or index}")
        stop_events = _tuple_value(sample, "stop_events")
        if stop_events:
            reasons.append(f"stop_event_recorded:{sample_id or index}")
        if sample.get("operator_reviewed") is not True:
            reasons.append(f"operator_review_missing:{sample_id or index}")
        sampled_at = _datetime_value(sample.get("sampled_at"))
        if sampled_at is None:
            reasons.append(f"invalid_sampled_at:{sample_id or index}")
        elif sampled_at > current_time:
            reasons.append(f"sampled_at_in_future:{sample_id or index}")
        if any(
            bool(sample.get(flag))
            for flag in (
                "queue_executed_by_soak_model",
                "task_executed_by_soak_model",
                "command_executed_by_soak_model",
                "write_performed_by_soak_model",
                "commit_performed_by_soak_model",
                "push_performed_by_soak_model",
            )
        ):
            reasons.append(f"soak_model_performed_forbidden_action:{sample_id or index}")

    if len(set(sample_ids)) != len(sample_ids):
        reasons.append("duplicate_sample_id")
    if hours:
        if hours != sorted(hours):
            reasons.append("sample_hours_not_increasing")
        if hours[0] != 0:
            reasons.append("missing_hour_0_sample")
        if hours[-1] != required_hours:
            reasons.append(f"missing_hour_{required_hours}_sample")
    return sample_payloads, sample_ids, hours


def _receipt_payload(receipt: Any) -> dict[str, Any]:
    if isinstance(receipt, SupervisedSafeTaskReceipt):
        return receipt.to_dict()
    if isinstance(receipt, dict):
        return receipt
    return {}


def _sample_payload(sample: Any) -> dict[str, Any]:
    if isinstance(sample, TwentyFourHourSoakSample):
        return sample.to_dict()
    if isinstance(sample, dict):
        return sample
    return {}


def _drill_payload(drill: Any) -> dict[str, Any]:
    if isinstance(drill, KillSwitchRollbackDrill):
        return drill.to_dict()
    if isinstance(drill, dict):
        return drill
    return {}


def _validation_status(validation: Any) -> str | None:
    if hasattr(validation, "to_dict"):
        validation = validation.to_dict()
    if not isinstance(validation, dict):
        return None
    status = validation.get("status")
    return status if isinstance(status, str) else None


def _promotion_decision_id(*, tier: str, status: str) -> str:
    tier_part = tier or "unknown-tier"
    return f"promotion-decision-{tier_part}-{status}"


def _string_value(payload: dict[str, Any], field: str) -> str | None:
    value = payload.get(field)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _tuple_value(payload: dict[str, Any], field: str) -> tuple[str, ...]:
    value = payload.get(field)
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item.strip() for item in value if isinstance(item, str) and item.strip())


def _count_value(payload: dict[str, Any], field: str) -> int | None:
    value = payload.get(field, 0)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _supervised_trial_summary(
    *,
    status: str,
    reasons: tuple[str, ...],
    task_ids: tuple[str, ...],
    receipt_paths: tuple[str, ...],
    false_positive_count: int,
    false_negative_count: int,
    validated_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": "cartographer.supervised_daily_driver_trial_summary.v1",
        "status": status,
        "reasons": reasons,
        "first_task_id": task_ids[0] if task_ids else None,
        "first_receipt_path": receipt_paths[0] if receipt_paths else None,
        "task_count": len(task_ids),
        "receipt_count": len(receipt_paths),
        "false_positive_count": false_positive_count,
        "false_negative_count": false_negative_count,
        "one_task_first_required": True,
        "ten_supervised_receipts_required": True,
        "operator_supervision_required": True,
        "human_review_required": True,
        "validated_at": validated_at,
        "next_task_auto_started": False,
        "background_loop_started": False,
        "queue_execution_performed": False,
        "task_execution_performed": False,
        "command_execution_performed": False,
        "safe_write_performed": False,
        "commit_performed": False,
        "push_performed": False,
        "durable_storage_performed": False,
        "authority_granted_by_summary": False,
    }


def _promotion_decision_packet(
    *,
    status: str,
    reasons: tuple[str, ...],
    tier: str | None,
    allowed_actions: tuple[str, ...],
    decided_by: str | None,
    evidence: dict[str, Any],
    decided_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": "cartographer.promotion_decision_packet.v1",
        "status": status,
        "reasons": reasons,
        "tier": tier,
        "allowed_actions": allowed_actions,
        "decided_by": decided_by,
        "decided_at": decided_at,
        "evidence": evidence,
        "required_evidence": (
            "ten_supervised_safe_task_receipts",
            "twenty_four_hour_soak",
            "seventy_two_hour_soak",
            "kill_switch_and_rollback_drills",
        ),
        "britton_manual_decision_required": True,
        "plan_12_explicit_approval_required": True,
        "authority_granted_by_packet": False,
        "daily_driver_active": False,
        "limited_daily_driver_activation_allowed": False,
        "background_loop_enabled": False,
        "queue_execution_enabled": False,
        "task_execution_enabled": False,
        "safe_write_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "self_promotion_allowed": False,
    }


def _verification(value: Any, reasons: list[str], task_id: str) -> dict[str, Any] | None:
    if isinstance(value, DailyDriverSoakVerification):
        value = value.to_dict()
    if not isinstance(value, dict):
        reasons.append(f"invalid_verification:{task_id}")
        return None
    checks = value.get("checks")
    if not isinstance(value.get("status"), str) or not value.get("status"):
        reasons.append(f"invalid_verification_status:{task_id}")
    if not isinstance(checks, (list, tuple)) or not checks:
        reasons.append(f"missing_verification_checks:{task_id}")
    if _datetime_value(value.get("checked_at")) is None:
        reasons.append(f"invalid_verification_checked_at:{task_id}")
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
