from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import Any

SAFE_TASK_QUEUE_MODEL_PHASE = "Plan 6 Phase 2: Trust-tier safe task classes"
SAFE_TASK_RUN_NEXT_PHASE = "Plan 6 Phase 3: run-next one-task-only endpoint"
SAFE_TASK_KILL_SWITCH_DRILL_PHASE = "Plan 6 Phase 4: Kill switch drill"
SAFE_TASK_FIRST_RUN_PHASE = "Plan 6 Phase 5: First auto-selected safe task run"

SAFE_TASK_STATUSES: tuple[str, ...] = (
    "pending",
    "selected",
    "running",
    "completed",
    "blocked",
    "failed",
    "cancelled",
)

TERMINAL_SAFE_TASK_STATUSES: tuple[str, ...] = (
    "completed",
    "blocked",
    "failed",
    "cancelled",
)

PLAN_6_SAFE_TASK_CLASSES: tuple[str, ...] = (
    "safe_docs_evidence_maintenance",
    "safe_receipt_closeout",
    "safe_project_health_snapshot",
    "safe_blueprint_refresh_proposal_only",
    "safe_stale_plan_summary_proposal_only",
)

SAFE_TASK_TRUST_TIER = "tier-1"
MAX_SAFE_TASK_ATTEMPTS = 3

SAFE_TASK_CLASS_TRUST_TIERS: dict[str, str] = {
    "safe_docs_evidence_maintenance": SAFE_TASK_TRUST_TIER,
    "safe_receipt_closeout": SAFE_TASK_TRUST_TIER,
    "safe_project_health_snapshot": SAFE_TASK_TRUST_TIER,
    "safe_blueprint_refresh_proposal_only": SAFE_TASK_TRUST_TIER,
    "safe_stale_plan_summary_proposal_only": SAFE_TASK_TRUST_TIER,
}

SAFE_TASK_CLASS_MODES: dict[str, str] = {
    "safe_docs_evidence_maintenance": "safe_write_later_phase",
    "safe_receipt_closeout": "safe_write_later_phase",
    "safe_project_health_snapshot": "safe_write_later_phase",
    "safe_blueprint_refresh_proposal_only": "proposal_only",
    "safe_stale_plan_summary_proposal_only": "proposal_only",
}

REQUIRED_SAFE_TASK_RECORD_FIELDS: tuple[str, ...] = (
    "task_id",
    "task_class",
    "trust_tier",
    "approval_token_id",
    "allowed_files",
    "forbidden_files",
    "status",
    "attempts",
    "created_at",
    "selected_at",
    "completed_at",
    "blocked_reason",
)

FORBIDDEN_SAFE_TASK_AUTHORITIES: tuple[str, ...] = (
    "task_execution",
    "task_selection",
    "queue_worker",
    "background_loop",
    "command",
    "safe_write",
    "approval_token_minting",
    "approval_token_storage",
    "durable_storage",
    "git_stage",
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
class SafeTaskRecord:
    task_id: str
    task_class: str
    trust_tier: str
    approval_token_id: str
    allowed_files: tuple[str, ...]
    forbidden_files: tuple[str, ...]
    status: str = "pending"
    attempts: int = 0
    created_at: str = ""
    selected_at: str | None = None
    completed_at: str | None = None
    blocked_reason: str | None = None
    model_only: bool = True
    durable_storage_available: bool = False
    selection_available: bool = False
    execution_available: bool = False
    queue_worker_available: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class SafeTaskRecordValidation:
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    task_id: str | None
    task_class: str | None
    trust_tier: str | None
    approval_token_id: str | None
    task_status: str | None
    attempts: int | None
    validated_at: str
    model_only: bool = True
    durable_storage_available: bool = False
    selection_available: bool = False
    execution_available: bool = False
    queue_worker_available: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    token_minting_available: bool = False
    approval_storage_available: bool = False
    no_execution_guarantee: str = (
        "Plan 6 Phase 2 validates safe task queue records and task classes "
        "as data only. It "
        "does not select tasks, execute tasks, run queues, run commands, "
        "perform safe writes, mint or store approval tokens, stage changes, "
        "commit, push, branch, create worktrees, stash, clean, reset, or checkout."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class SafeTaskRunNextSelection:
    status: str
    selected: bool
    blocked: bool
    reasons: tuple[str, ...]
    selected_task: dict[str, Any] | None
    selected_task_id: str | None
    selected_count: int
    eligible_count: int
    rejected_count: int
    evaluated_count: int
    selected_at: str
    validation_results: tuple[dict[str, Any], ...]
    model_only: bool = True
    durable_storage_available: bool = False
    execution_available: bool = False
    queue_worker_available: bool = False
    background_loop_available: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    token_minting_available: bool = False
    approval_storage_available: bool = False
    no_execution_guarantee: str = (
        "Plan 6 Phase 3 run-next selects at most one eligible safe task as "
        "response data only. It does not execute tasks, persist queue records, "
        "run queues, run commands, perform safe writes, mint or store approval "
        "tokens, stage changes, commit, push, branch, create worktrees, stash, "
        "clean, reset, or checkout."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class SafeTaskKillSwitchDrill:
    status: str
    passed: bool
    blocked: bool
    reasons: tuple[str, ...]
    checkpoints: tuple[dict[str, Any], ...]
    selected_task_id: str | None
    drilled_at: str
    model_only: bool = True
    durable_storage_available: bool = False
    execution_available: bool = False
    queue_worker_available: bool = False
    background_loop_available: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    verification_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    no_execution_guarantee: str = (
        "Plan 6 Phase 4 drills kill-switch checkpoints as data only. It does "
        "not execute tasks, persist queue records, run queues, run commands, "
        "perform safe writes, run verification, mint or store approval tokens, "
        "stage changes, commit, push, branch, create worktrees, stash, clean, "
        "reset, or checkout."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class SafeTaskRunReceipt:
    status: str
    completed: bool
    blocked: bool
    reasons: tuple[str, ...]
    selected_task_id: str | None
    selected_count: int
    completed_count: int
    receipt: dict[str, Any] | None
    selected_at: str
    completed_at: str
    selection: dict[str, Any]
    durable_storage_available: bool = False
    queue_worker_available: bool = False
    background_loop_available: bool = False
    source_write_performed: bool = False
    safe_write_performed: bool = False
    verification_run_performed: bool = False
    command_run_performed: bool = False
    git_mutation_performed: bool = False
    token_minting_available: bool = False
    approval_storage_available: bool = False
    no_background_loop_guarantee: str = "This run handles one explicit request and then stops."
    no_mutation_guarantee: str = (
        "Plan 6 Phase 5 runs the first auto-selected proposal-only safe task "
        "and produces an in-memory receipt. It does not write files, persist "
        "queue records, run commands, run verification, mint or store approval "
        "tokens, stage changes, commit, push, branch, create worktrees, stash, "
        "clean, reset, or checkout."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_safe_task_queue_model_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Daily Driver Autonomy Roadmap Plan 6",
        "phase": SAFE_TASK_QUEUE_MODEL_PHASE,
        "status": "model-only",
        "run_next_phase": SAFE_TASK_RUN_NEXT_PHASE,
        "kill_switch_drill_phase": SAFE_TASK_KILL_SWITCH_DRILL_PHASE,
        "first_run_phase": SAFE_TASK_FIRST_RUN_PHASE,
        "required_fields": REQUIRED_SAFE_TASK_RECORD_FIELDS,
        "task_statuses": SAFE_TASK_STATUSES,
        "terminal_statuses": TERMINAL_SAFE_TASK_STATUSES,
        "allowed_task_classes": PLAN_6_SAFE_TASK_CLASSES,
        "task_class_trust_tiers": SAFE_TASK_CLASS_TRUST_TIERS,
        "task_class_modes": SAFE_TASK_CLASS_MODES,
        "required_trust_tier": SAFE_TASK_TRUST_TIER,
        "max_attempts": MAX_SAFE_TASK_ATTEMPTS,
        "forbidden_authorities": FORBIDDEN_SAFE_TASK_AUTHORITIES,
        "durable_storage_available": False,
        "run_next_endpoint_available": True,
        "first_run_available": True,
        "receipt_available": True,
        "selection_available": False,
        "execution_available": False,
        "queue_worker_available": False,
        "command_authority_granted": False,
        "write_authority_granted": False,
        "verification_authority_granted": False,
        "git_mutation_authority_granted": False,
        "token_minting_available": False,
        "approval_storage_available": False,
        "safe_next_action": "Run one approved proposal-only safe task per explicit request; require later approval for durable storage or write-backed classes.",
}


def run_first_auto_selected_safe_task(
    records: Any,
    *,
    expected_trust_tier: str = SAFE_TASK_TRUST_TIER,
    expected_approval_token_id: str,
    kill_switch_active: bool = False,
    now: datetime | None = None,
) -> SafeTaskRunReceipt:
    current_time = now or datetime.now(UTC)
    completed_at = _format_utc(current_time)
    selection = select_next_safe_task(
        records,
        expected_trust_tier=expected_trust_tier,
        expected_approval_token_id=expected_approval_token_id,
        kill_switch_active=kill_switch_active,
        now=current_time,
    )
    selection_payload = selection.to_dict()
    reasons: list[str] = list(selection.reasons)
    receipt: dict[str, Any] | None = None

    if selection.selected_task is not None:
        task_class = _string_value(selection.selected_task, "task_class")
        task_mode = SAFE_TASK_CLASS_MODES.get(task_class or "")
        if task_mode != "proposal_only":
            reasons.append("task_class_requires_later_safe_write_phase")
        if not reasons:
            receipt = _safe_task_run_receipt(
                selected_task=selection.selected_task,
                completed_at=completed_at,
                task_mode=task_mode,
            )

    completed = receipt is not None
    return SafeTaskRunReceipt(
        status="completed" if completed else "blocked",
        completed=completed,
        blocked=not completed,
        reasons=tuple(_dedupe_reasons(reasons)),
        selected_task_id=selection.selected_task_id,
        selected_count=selection.selected_count,
        completed_count=1 if completed else 0,
        receipt=receipt,
        selected_at=selection.selected_at,
        completed_at=completed_at,
        selection=selection_payload,
    )


def drill_safe_task_kill_switch(
    records: Any,
    *,
    expected_trust_tier: str = SAFE_TASK_TRUST_TIER,
    expected_approval_token_id: str,
    now: datetime | None = None,
) -> SafeTaskKillSwitchDrill:
    current_time = now or datetime.now(UTC)
    drilled_at = _format_utc(current_time)
    checkpoints: list[dict[str, Any]] = []

    before_selection = select_next_safe_task(
        records,
        expected_trust_tier=expected_trust_tier,
        expected_approval_token_id=expected_approval_token_id,
        kill_switch_active=True,
        now=current_time,
    )
    checkpoints.append(
        _kill_switch_checkpoint(
            name="before_selection",
            blocked=before_selection.blocked and before_selection.selected_count == 0,
            reasons=before_selection.reasons,
            selected_task_id=before_selection.selected_task_id,
        ),
    )

    selection = select_next_safe_task(
        records,
        expected_trust_tier=expected_trust_tier,
        expected_approval_token_id=expected_approval_token_id,
        kill_switch_active=False,
        now=current_time,
    )
    checkpoints.append(
        _kill_switch_checkpoint(
            name="after_selection",
            blocked=selection.selected and selection.selected_count == 1,
            reasons=("kill_switch_active_after_selection",),
            selected_task_id=selection.selected_task_id,
        ),
    )
    checkpoints.append(
        _kill_switch_checkpoint(
            name="before_write_verification",
            blocked=selection.selected and selection.selected_count == 1,
            reasons=("kill_switch_active_before_write_verification",),
            selected_task_id=selection.selected_task_id,
        ),
    )

    failed = [checkpoint["checkpoint"] for checkpoint in checkpoints if not checkpoint["blocked"]]
    reasons = [f"checkpoint_not_blocked:{checkpoint}" for checkpoint in failed]
    passed = not reasons

    return SafeTaskKillSwitchDrill(
        status="passed" if passed else "failed",
        passed=passed,
        blocked=True,
        reasons=tuple(reasons),
        checkpoints=tuple(checkpoints),
        selected_task_id=selection.selected_task_id,
        drilled_at=drilled_at,
    )


def select_next_safe_task(
    records: Any,
    *,
    expected_trust_tier: str = SAFE_TASK_TRUST_TIER,
    expected_approval_token_id: str,
    kill_switch_active: bool = False,
    now: datetime | None = None,
) -> SafeTaskRunNextSelection:
    current_time = now or datetime.now(UTC)
    selected_at = _format_utc(current_time)
    reasons: list[str] = []

    if kill_switch_active:
        reasons.append("kill_switch_active")
    if not isinstance(records, (list, tuple)):
        reasons.append("malformed_queue_records")
        records = ()
    if len(records) == 0:
        reasons.append("empty_queue")

    validation_results: list[dict[str, Any]] = []
    eligible: list[dict[str, Any]] = []
    rejected_count = 0

    for record in records:
        validation = validate_safe_task_record(
            record,
            expected_trust_tier=expected_trust_tier,
            expected_approval_token_id=expected_approval_token_id,
            now=current_time,
        )
        validation_payload = validation.to_dict()
        validation_results.append(validation_payload)
        payload = _record_payload(record)
        if validation.accepted and payload is not None and validation.task_status == "pending":
            eligible.append(payload)
        else:
            rejected_count += 1

    if records and not eligible:
        reasons.append("no_eligible_pending_task")

    selected_task: dict[str, Any] | None = None
    if not reasons and eligible:
        selected_task = dict(eligible[0])
        selected_task["status"] = "selected"
        selected_task["selected_at"] = selected_at

    selected_count = 1 if selected_task is not None else 0
    accepted = selected_count == 1 and not reasons

    return SafeTaskRunNextSelection(
        status="selected" if accepted else "blocked",
        selected=accepted,
        blocked=not accepted,
        reasons=tuple(_dedupe_reasons(reasons)),
        selected_task=selected_task,
        selected_task_id=_string_value(selected_task, "task_id"),
        selected_count=selected_count,
        eligible_count=len(eligible),
        rejected_count=rejected_count,
        evaluated_count=len(records),
        selected_at=selected_at,
        validation_results=tuple(validation_results),
    )


def validate_safe_task_record(
    record: Any,
    *,
    expected_trust_tier: str = SAFE_TASK_TRUST_TIER,
    expected_approval_token_id: str,
    now: datetime | None = None,
) -> SafeTaskRecordValidation:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []

    expected_trust_tier = expected_trust_tier.strip() if expected_trust_tier else ""
    expected_approval_token_id = expected_approval_token_id.strip() if expected_approval_token_id else ""
    if not expected_trust_tier:
        reasons.append("missing_expected_trust_tier")
    if not expected_approval_token_id:
        reasons.append("missing_expected_approval_token_id")

    payload = _record_payload(record)
    if payload is None:
        reasons.append("malformed_record")
        return _validation(
            reasons=reasons,
            current_time=current_time,
            task_id=None,
            task_class=None,
            trust_tier=None,
            approval_token_id=None,
            task_status=None,
            attempts=None,
        )

    for field in REQUIRED_SAFE_TASK_RECORD_FIELDS:
        if field not in payload:
            reasons.append(f"missing_required_field:{field}")

    task_id = _string_field(payload, "task_id", reasons)
    task_class = _string_field(payload, "task_class", reasons)
    trust_tier = _string_field(payload, "trust_tier", reasons)
    approval_token_id = _string_field(payload, "approval_token_id", reasons)
    task_status = _string_field(payload, "status", reasons)
    attempts = _attempts_field(payload, "attempts", reasons)
    allowed_files = _file_tuple_field(payload, "allowed_files", reasons)
    forbidden_files = _file_tuple_field(payload, "forbidden_files", reasons)
    created_at = _datetime_field(payload, "created_at", reasons, required=True)
    selected_at = _datetime_field(payload, "selected_at", reasons, required=False)
    completed_at = _datetime_field(payload, "completed_at", reasons, required=False)
    blocked_reason = _optional_string_field(payload, "blocked_reason", reasons)

    if task_class and task_class not in PLAN_6_SAFE_TASK_CLASSES:
        reasons.append("unknown_task_class")
    class_trust_tier = SAFE_TASK_CLASS_TRUST_TIERS.get(task_class or "")
    if class_trust_tier and trust_tier and trust_tier != class_trust_tier:
        reasons.append("wrong_task_class_trust_tier")
    if trust_tier and expected_trust_tier and trust_tier != expected_trust_tier:
        reasons.append("wrong_trust_tier")
    if approval_token_id and expected_approval_token_id and approval_token_id != expected_approval_token_id:
        reasons.append("wrong_approval_token")
    if task_status and task_status not in SAFE_TASK_STATUSES:
        reasons.append("unknown_status")
    if attempts is not None and (attempts < 0 or attempts > MAX_SAFE_TASK_ATTEMPTS):
        reasons.append("attempts_out_of_bounds")
    if allowed_files == ():
        reasons.append("missing_allowed_files")
    if allowed_files is not None and forbidden_files is not None:
        overlap = set(allowed_files).intersection(forbidden_files)
        if overlap:
            reasons.append("allowed_file_forbidden")
    if created_at is not None and created_at > current_time:
        reasons.append("created_at_in_future")
    if selected_at is not None and created_at is not None and selected_at < created_at:
        reasons.append("selected_at_before_created_at")
    if completed_at is not None and created_at is not None and completed_at < created_at:
        reasons.append("completed_at_before_created_at")
    if task_status in ("selected", "running") and selected_at is None:
        reasons.append("selected_at_required")
    if task_status == "completed" and completed_at is None:
        reasons.append("completed_at_required")
    if task_status in ("blocked", "failed") and not blocked_reason:
        reasons.append("blocked_reason_required")

    return _validation(
        reasons=reasons,
        current_time=current_time,
        task_id=task_id,
        task_class=task_class,
        trust_tier=trust_tier,
        approval_token_id=approval_token_id,
        task_status=task_status,
        attempts=attempts,
    )


def _validation(
    *,
    reasons: list[str],
    current_time: datetime,
    task_id: str | None,
    task_class: str | None,
    trust_tier: str | None,
    approval_token_id: str | None,
    task_status: str | None,
    attempts: int | None,
) -> SafeTaskRecordValidation:
    deduped = _dedupe_reasons(reasons)
    accepted = not deduped
    return SafeTaskRecordValidation(
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=tuple(deduped),
        task_id=task_id,
        task_class=task_class,
        trust_tier=trust_tier,
        approval_token_id=approval_token_id,
        task_status=task_status,
        attempts=attempts,
        validated_at=_format_utc(current_time),
    )


def _record_payload(record: Any) -> dict[str, Any] | None:
    if isinstance(record, SafeTaskRecord):
        return record.to_dict()
    if isinstance(record, dict):
        return record
    return None


def _string_value(payload: dict[str, Any] | None, field: str) -> str | None:
    if payload is None:
        return None
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip()


def _kill_switch_checkpoint(
    *,
    name: str,
    blocked: bool,
    reasons: tuple[str, ...],
    selected_task_id: str | None,
) -> dict[str, Any]:
    return {
        "checkpoint": name,
        "blocked": blocked,
        "reasons": reasons,
        "selected_task_id": selected_task_id,
        "execution_available": False,
        "write_authority_granted": False,
        "verification_authority_granted": False,
        "command_authority_granted": False,
        "git_mutation_authority_granted": False,
    }


def _safe_task_run_receipt(
    *,
    selected_task: dict[str, Any],
    completed_at: str,
    task_mode: str,
) -> dict[str, Any]:
    return {
        "schema_version": "cartographer.safe_task_run_receipt.v1",
        "phase": SAFE_TASK_FIRST_RUN_PHASE,
        "task_id": _string_value(selected_task, "task_id"),
        "task_class": _string_value(selected_task, "task_class"),
        "task_mode": task_mode,
        "trust_tier": _string_value(selected_task, "trust_tier"),
        "approval_token_id": _string_value(selected_task, "approval_token_id"),
        "status": "completed",
        "selected_at": _string_value(selected_task, "selected_at"),
        "completed_at": completed_at,
        "selected_count": 1,
        "completed_count": 1,
        "allowed_files": tuple(selected_task.get("allowed_files", ())),
        "forbidden_files": tuple(selected_task.get("forbidden_files", ())),
        "action": "proposal_only_receipt",
        "source_write_performed": False,
        "safe_write_performed": False,
        "verification_run_performed": False,
        "command_run_performed": False,
        "git_mutation_performed": False,
        "durable_storage_performed": False,
        "background_loop_started": False,
    }


def _string_field(payload: dict[str, Any], field: str, reasons: list[str]) -> str | None:
    if field not in payload:
        return None
    value = payload[field]
    if not isinstance(value, str) or not value.strip():
        reasons.append(f"malformed_field:{field}")
        return None
    return value.strip()


def _optional_string_field(payload: dict[str, Any], field: str, reasons: list[str]) -> str | None:
    if field not in payload or payload[field] is None:
        return None
    value = payload[field]
    if not isinstance(value, str) or not value.strip():
        reasons.append(f"malformed_field:{field}")
        return None
    return value.strip()


def _attempts_field(payload: dict[str, Any], field: str, reasons: list[str]) -> int | None:
    if field not in payload:
        return None
    value = payload[field]
    if not isinstance(value, int) or isinstance(value, bool):
        reasons.append(f"malformed_field:{field}")
        return None
    return value


def _file_tuple_field(payload: dict[str, Any], field: str, reasons: list[str]) -> tuple[str, ...] | None:
    if field not in payload:
        return None
    value = payload[field]
    if not isinstance(value, (list, tuple)):
        reasons.append(f"malformed_field:{field}")
        return None
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            reasons.append(f"malformed_field:{field}")
            return None
        normalized.append(item.strip())
    if len(set(normalized)) != len(normalized):
        reasons.append(f"duplicate_field:{field}")
    return tuple(normalized)


def _datetime_field(
    payload: dict[str, Any],
    field: str,
    reasons: list[str],
    *,
    required: bool,
) -> datetime | None:
    if field not in payload or payload[field] is None:
        if required:
            return None
        return None
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


def _dedupe_reasons(reasons: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        deduped.append(reason)
    return deduped


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
