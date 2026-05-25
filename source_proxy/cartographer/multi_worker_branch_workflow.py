from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import Any


INTEGRATED_CONTROL_PLAN_9 = "Cartographer Integrated Control Master Plan 9/10"
CONTROLLED_MULTI_WORKER_BRANCH_WORKFLOW_PHASE = (
    "Plan 9 Phase 9.2: Controlled branch/worktree workflow proposals"
)
PLAN_9_MULTI_LANE_SOURCE_EDIT_BOUNDARY = (
    "Plan 9/10 requires explicit non-overlapping ownership before parallel source edits."
)

MULTI_WORKER_BRANCH_WORKFLOW_REQUIRED_FIELDS: tuple[str, ...] = (
    "workflow_id",
    "worker_slots",
    "proposed_branches",
    "proposed_worktrees",
    "branch_worktree_approval_id",
    "coordination_receipt_path",
    "rollback_guidance",
    "verification_plan",
    "trust_tier",
    "approval_token_id",
    "status",
    "created_at",
)

WORKER_SLOT_REQUIRED_FIELDS: tuple[str, ...] = (
    "worker_id",
    "task_id",
    "file_zone",
)

PROTECTED_BASE_BRANCHES: tuple[str, ...] = ("main", "master", "trunk")

FORBIDDEN_MULTI_WORKER_BRANCH_AUTHORITIES: tuple[str, ...] = (
    "worker_spawn",
    "task_execution",
    "queue_execution",
    "branch_creation",
    "worktree_creation",
    "checkout",
    "merge",
    "source_write",
    "test_write",
    "safe_write",
    "command_execution",
    "local_commit",
    "push",
    "stash",
    "clean",
    "reset",
    "approval_token_minting",
    "self_approval",
    "durable_storage_write",
    "api_mutation",
)


@dataclasses.dataclass(frozen=True)
class MultiWorkerSlot:
    worker_id: str
    task_id: str
    file_zone: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class ControlledMultiWorkerBranchWorkflow:
    workflow_id: str
    worker_slots: tuple[MultiWorkerSlot, ...]
    proposed_branches: tuple[str, ...]
    proposed_worktrees: tuple[str, ...]
    branch_worktree_approval_id: str
    coordination_receipt_path: str
    rollback_guidance: str
    verification_plan: tuple[str, ...]
    trust_tier: str
    approval_token_id: str
    status: str
    created_at: str
    design_only: bool = True
    explicit_branch_worktree_approval_required: bool = True
    exact_approval_before_creation_required: bool = True
    ownership_proof_required: bool = True
    rollback_proof_required: bool = True
    implicit_creation_blocked: bool = True
    worker_spawn_enabled: bool = False
    task_execution_enabled: bool = False
    queue_execution_enabled: bool = False
    branch_creation_enabled: bool = False
    worktree_creation_enabled: bool = False
    checkout_enabled: bool = False
    merge_enabled: bool = False
    command_execution_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    durable_storage_written: bool = False
    api_mutation_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class ControlledMultiWorkerBranchWorkflowValidation:
    phase: str
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    workflow_id: str | None
    worker_ids: tuple[str, ...]
    task_ids: tuple[str, ...]
    file_zones: tuple[str, ...]
    proposed_branches: tuple[str, ...]
    proposed_worktrees: tuple[str, ...]
    branch_worktree_approval_id: str | None
    trust_tier: str | None
    approval_token_id: str | None
    validated_at: str
    design_only: bool = True
    explicit_branch_worktree_approval_required: bool = True
    exact_approval_before_creation_required: bool = True
    ownership_proof_required: bool = True
    rollback_proof_required: bool = True
    implicit_creation_blocked: bool = True
    worker_spawn_enabled: bool = False
    task_execution_enabled: bool = False
    queue_execution_enabled: bool = False
    branch_creation_enabled: bool = False
    worktree_creation_enabled: bool = False
    checkout_enabled: bool = False
    merge_enabled: bool = False
    command_execution_enabled: bool = False
    commit_enabled: bool = False
    push_enabled: bool = False
    durable_storage_written: bool = False
    api_mutation_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_controlled_multi_worker_branch_workflow_status() -> dict[str, Any]:
    return {
        "plan": INTEGRATED_CONTROL_PLAN_9,
        "phase": CONTROLLED_MULTI_WORKER_BRANCH_WORKFLOW_PHASE,
        "status": "design-only",
        "required_fields": MULTI_WORKER_BRANCH_WORKFLOW_REQUIRED_FIELDS,
        "worker_slot_required_fields": WORKER_SLOT_REQUIRED_FIELDS,
        "protected_base_branches": PROTECTED_BASE_BRANCHES,
        "forbidden_authorities": FORBIDDEN_MULTI_WORKER_BRANCH_AUTHORITIES,
        "design_only": True,
        "explicit_branch_worktree_approval_required": True,
        "worker_spawn_enabled": False,
        "task_execution_enabled": False,
        "queue_execution_enabled": False,
        "branch_creation_enabled": False,
        "worktree_creation_enabled": False,
        "checkout_enabled": False,
        "merge_enabled": False,
        "command_execution_enabled": False,
        "commit_enabled": False,
        "push_enabled": False,
        "durable_storage_written": False,
        "api_mutation_available": False,
        "exact_approval_before_creation_required": True,
        "ownership_proof_required": True,
        "rollback_proof_required": True,
        "implicit_creation_blocked": True,
        "plan_9_multi_lane_source_edit_boundary": PLAN_9_MULTI_LANE_SOURCE_EDIT_BOUNDARY,
        "parallel_source_edits_without_ownership_blocked": True,
        "safe_next_action": "Review exact multi-worker branch/worktree workflow design; require separate approval before creation.",
    }


def validate_controlled_multi_worker_branch_workflow(
    workflow: Any,
    *,
    expected_trust_tier: str,
    expected_approval_token_id: str,
    expected_branch_worktree_approval_id: str,
    now: datetime | None = None,
) -> ControlledMultiWorkerBranchWorkflowValidation:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []
    expected_trust_tier = expected_trust_tier.strip() if expected_trust_tier else ""
    expected_approval_token_id = expected_approval_token_id.strip() if expected_approval_token_id else ""
    expected_branch_worktree_approval_id = (
        expected_branch_worktree_approval_id.strip() if expected_branch_worktree_approval_id else ""
    )
    if not expected_trust_tier:
        reasons.append("missing_expected_trust_tier")
    if not expected_approval_token_id:
        reasons.append("missing_expected_approval_token_id")
    if not expected_branch_worktree_approval_id:
        reasons.append("missing_expected_branch_worktree_approval_id")

    payload = _workflow_payload(workflow)
    if payload is None:
        reasons.append("malformed_controlled_multi_worker_branch_workflow")
        return _validation(
            reasons=reasons,
            current_time=current_time,
            workflow_id=None,
            worker_ids=(),
            task_ids=(),
            file_zones=(),
            proposed_branches=(),
            proposed_worktrees=(),
            branch_worktree_approval_id=None,
            trust_tier=None,
            approval_token_id=None,
        )

    for field in MULTI_WORKER_BRANCH_WORKFLOW_REQUIRED_FIELDS:
        if field not in payload:
            reasons.append(f"missing_required_field:{field}")

    workflow_id = _string_field(payload, "workflow_id", reasons)
    worker_slots = _worker_slots(payload.get("worker_slots"), reasons)
    proposed_branches = _string_tuple_value(payload.get("proposed_branches"), "proposed_branches", reasons)
    proposed_worktrees = _string_tuple_value(payload.get("proposed_worktrees"), "proposed_worktrees", reasons)
    branch_worktree_approval_id = _string_field(payload, "branch_worktree_approval_id", reasons)
    coordination_receipt_path = _string_field(payload, "coordination_receipt_path", reasons)
    rollback_guidance = _string_field(payload, "rollback_guidance", reasons)
    verification_plan = _string_tuple_value(payload.get("verification_plan"), "verification_plan", reasons)
    trust_tier = _string_field(payload, "trust_tier", reasons)
    approval_token_id = _string_field(payload, "approval_token_id", reasons)
    status = _string_field(payload, "status", reasons)
    created_at = _datetime_value(payload.get("created_at"))

    worker_ids = tuple(slot["worker_id"] for slot in worker_slots)
    task_ids = tuple(slot["task_id"] for slot in worker_slots)
    file_zones = tuple(path for slot in worker_slots for path in slot["file_zone"])

    if len(worker_slots) < 2:
        reasons.append("multi_worker_workflow_requires_at_least_two_workers")
    if len(set(worker_ids)) != len(worker_ids):
        reasons.append("duplicate_worker_id")
    if len(set(task_ids)) != len(task_ids):
        reasons.append("duplicate_task_id")
    if len(set(file_zones)) != len(file_zones):
        reasons.append("overlapping_file_zone")
    for path in file_zones:
        if _is_broad_file_scope(path):
            reasons.append("broad_file_zone")
    if len(proposed_branches) != len(worker_slots):
        reasons.append("one_branch_per_worker_required")
    if len(proposed_worktrees) != len(worker_slots):
        reasons.append("one_worktree_per_worker_required")
    if len(set(proposed_branches)) != len(proposed_branches):
        reasons.append("duplicate_proposed_branch")
    if len(set(proposed_worktrees)) != len(proposed_worktrees):
        reasons.append("duplicate_proposed_worktree")
    for branch in proposed_branches:
        if _is_broad_branch_scope(branch):
            reasons.append("broad_proposed_branch")
        if branch in PROTECTED_BASE_BRANCHES:
            reasons.append("protected_base_branch_blocked")
        if branch and not branch.startswith("cartographer/"):
            reasons.append("proposed_branch_must_be_cartographer_scoped")
    for worktree in proposed_worktrees:
        if _is_broad_file_scope(worktree):
            reasons.append("broad_proposed_worktree")
        if worktree and not worktree.startswith(".cartographer/worktrees/"):
            reasons.append("proposed_worktree_must_be_cartographer_scoped")
    if coordination_receipt_path and _is_broad_file_scope(coordination_receipt_path):
        reasons.append("broad_coordination_receipt_path")
    if coordination_receipt_path and not coordination_receipt_path.startswith("docs/"):
        reasons.append("coordination_receipt_path_must_be_docs")
    if coordination_receipt_path and not coordination_receipt_path.endswith(".md"):
        reasons.append("coordination_receipt_path_must_be_markdown")
    if branch_worktree_approval_id and branch_worktree_approval_id != expected_branch_worktree_approval_id:
        reasons.append("wrong_branch_worktree_approval")
    if trust_tier and trust_tier != expected_trust_tier:
        reasons.append("wrong_trust_tier")
    if approval_token_id and approval_token_id != expected_approval_token_id:
        reasons.append("wrong_approval_token")
    if status and status != "proposed":
        reasons.append("status_must_remain_proposed")
    if verification_plan == ():
        reasons.append("missing_verification_plan")
    if rollback_guidance and "force" in rollback_guidance.lower():
        reasons.append("rollback_guidance_must_not_recommend_force")
    if created_at is None:
        reasons.append("invalid_created_at")
    elif created_at > current_time:
        reasons.append("created_at_in_future")

    return _validation(
        reasons=reasons,
        current_time=current_time,
        workflow_id=workflow_id,
        worker_ids=worker_ids,
        task_ids=task_ids,
        file_zones=file_zones,
        proposed_branches=proposed_branches,
        proposed_worktrees=proposed_worktrees,
        branch_worktree_approval_id=branch_worktree_approval_id,
        trust_tier=trust_tier,
        approval_token_id=approval_token_id,
    )


def _validation(
    *,
    reasons: list[str],
    current_time: datetime,
    workflow_id: str | None,
    worker_ids: tuple[str, ...],
    task_ids: tuple[str, ...],
    file_zones: tuple[str, ...],
    proposed_branches: tuple[str, ...],
    proposed_worktrees: tuple[str, ...],
    branch_worktree_approval_id: str | None,
    trust_tier: str | None,
    approval_token_id: str | None,
) -> ControlledMultiWorkerBranchWorkflowValidation:
    blocked_reasons = tuple(dict.fromkeys(reasons))
    accepted = not blocked_reasons
    return ControlledMultiWorkerBranchWorkflowValidation(
        phase=CONTROLLED_MULTI_WORKER_BRANCH_WORKFLOW_PHASE,
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=blocked_reasons,
        workflow_id=workflow_id,
        worker_ids=worker_ids,
        task_ids=task_ids,
        file_zones=file_zones,
        proposed_branches=proposed_branches,
        proposed_worktrees=proposed_worktrees,
        branch_worktree_approval_id=branch_worktree_approval_id,
        trust_tier=trust_tier,
        approval_token_id=approval_token_id,
        validated_at=_format_utc(current_time),
    )


def _workflow_payload(workflow: Any) -> dict[str, Any] | None:
    if isinstance(workflow, ControlledMultiWorkerBranchWorkflow):
        return workflow.to_dict()
    if isinstance(workflow, dict):
        return workflow
    return None


def _worker_slots(value: Any, reasons: list[str]) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, (list, tuple)):
        reasons.append("invalid_worker_slots")
        return ()
    slots: list[dict[str, Any]] = []
    for item in value:
        slot = item.to_dict() if isinstance(item, MultiWorkerSlot) else item
        if not isinstance(slot, dict):
            reasons.append("invalid_worker_slot")
            continue
        for field in WORKER_SLOT_REQUIRED_FIELDS:
            if field not in slot:
                reasons.append(f"missing_worker_slot_field:{field}")
        worker_id = _string_value(slot.get("worker_id"), "worker_id", reasons)
        task_id = _string_value(slot.get("task_id"), "task_id", reasons)
        file_zone = _string_tuple_value(slot.get("file_zone"), "file_zone", reasons)
        slots.append({"worker_id": worker_id or "", "task_id": task_id or "", "file_zone": file_zone})
    return tuple(slots)


def _string_field(payload: dict[str, Any], field: str, reasons: list[str]) -> str | None:
    return _string_value(payload.get(field), field, reasons)


def _string_value(value: Any, field: str, reasons: list[str]) -> str | None:
    if not isinstance(value, str) or not value.strip():
        reasons.append(f"invalid_{field}")
        return None
    return value.strip()


def _string_tuple_value(value: Any, field: str, reasons: list[str]) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        reasons.append(f"invalid_{field}")
        return ()
    items = tuple(item.strip() for item in value if isinstance(item, str) and item.strip())
    if len(items) != len(value):
        reasons.append(f"invalid_{field}_entry")
    return items


def _is_broad_branch_scope(branch: str) -> bool:
    return _is_broad_file_scope(branch) or branch.startswith("-") or " " in branch or branch.endswith(".lock")


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
