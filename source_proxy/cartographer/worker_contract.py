from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import Any


WORKER_CONTRACT_MODEL_PHASE = "Plan 8 Phase 8.1: Worker identity registry"
WORKER_OWNERSHIP_LOCK_PHASE = "Plan 8 Phase 8.1: File ownership zones and leases"
WORKER_CONFLICT_DETECTION_PHASE = "Plan 8 Phase 8.2: Ownership conflict report"
WORKER_HANDOFF_PACKET_PHASE = "Plan 8 Phase 8.2: Proposal worker handoff packet"
STALE_WORKER_CLOSEOUT_PROPOSAL_PHASE = "Plan 8 Phase 8.2: Stale worker closeout proposal"
ONE_WORKER_FILE_ZONE_PROOF_PHASE = "Plan 8 closeout: One worker, one task, one file-zone proof"

WORKER_ROLES: tuple[str, ...] = (
    "codex",
    "scout",
    "proxy",
    "designer",
    "blueprinter",
    "sub_cartographer",
)

WORKER_STATUSES: tuple[str, ...] = (
    "proposed",
    "active",
    "blocked",
    "stale",
    "completed",
)

TERMINAL_WORKER_STATUSES: tuple[str, ...] = (
    "blocked",
    "completed",
)

WORKER_TRUST_TIER = "tier-1"
MAX_WORKER_LOCK_RENEWALS = 3

OWNERSHIP_ZONE_MODES: tuple[str, ...] = (
    "exclusive",
)

WORKER_LOCK_STATUSES: tuple[str, ...] = (
    "active",
    "released",
    "stale",
)

PROTECTED_WORKER_FILE_PREFIXES: tuple[str, ...] = (
    "src/",
    "source_proxy/api/",
    "source_proxy/codex/",
    "source_proxy/tasks/",
    "source_proxy/testing/runner.py",
)

REQUIRED_WORKER_CONTRACT_FIELDS: tuple[str, ...] = (
    "worker_id",
    "worker_name",
    "worker_role",
    "assigned_task_id",
    "allowed_files",
    "forbidden_files",
    "trust_tier",
    "approval_token_id",
    "status",
    "active",
    "stale",
    "current_step",
    "heartbeat_at",
    "last_check_in_at",
    "blocked_reason",
    "created_at",
    "started_at",
    "completed_at",
)

REQUIRED_OWNERSHIP_ZONE_FIELDS: tuple[str, ...] = (
    "zone_id",
    "worker_id",
    "assigned_task_id",
    "files",
    "mode",
    "trust_tier",
    "approval_token_id",
    "created_at",
)

REQUIRED_WORKER_FILE_LOCK_FIELDS: tuple[str, ...] = (
    "lock_id",
    "zone_id",
    "worker_id",
    "assigned_task_id",
    "files",
    "status",
    "acquired_at",
    "expires_at",
    "renewed_at",
    "renewal_count",
    "released_at",
    "stale",
    "blocked_reason",
)

REQUIRED_WORKER_HANDOFF_PACKET_FIELDS: tuple[str, ...] = (
    "handoff_id",
    "task_id",
    "source_worker_id",
    "target_worker_id",
    "assigned_files",
    "scope",
    "expected_files",
    "ownership_zone_id",
    "lock_id",
    "lock_status",
    "conflict_report_status",
    "allowed_actions",
    "forbidden_actions",
    "evidence_requirements",
    "required_checks",
    "receipt_refs",
    "closeout_expectations",
    "closeout_summary",
    "created_at",
)

REQUIRED_STALE_WORKER_CLOSEOUT_PROPOSAL_FIELDS: tuple[str, ...] = (
    "proposal_id",
    "worker_id",
    "assigned_task_id",
    "stale_reason",
    "affected_files",
    "recommended_operator_actions",
    "required_checks",
    "receipt_refs",
    "created_at",
)

REQUIRED_ONE_WORKER_FILE_ZONE_PROOF_FIELDS: tuple[str, ...] = (
    "proof_id",
    "worker_id",
    "assigned_task_id",
    "file_zone",
    "ownership_zone_id",
    "lock_id",
    "handoff_id",
    "conflict_report_status",
    "created_at",
)

FORBIDDEN_WORKER_CONTRACT_AUTHORITIES: tuple[str, ...] = (
    "worker_spawn",
    "worker_dispatch",
    "queue_worker",
    "background_loop",
    "task_execution",
    "queue_execution",
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
class WorkerContract:
    worker_id: str
    worker_name: str
    worker_role: str
    assigned_task_id: str
    allowed_files: tuple[str, ...]
    forbidden_files: tuple[str, ...]
    trust_tier: str
    approval_token_id: str
    status: str = "proposed"
    active: bool = False
    stale: bool = False
    current_step: str | None = None
    heartbeat_at: str | None = None
    last_check_in_at: str | None = None
    blocked_reason: str | None = None
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None
    model_only: bool = True
    durable_storage_available: bool = False
    worker_spawn_available: bool = False
    worker_dispatch_available: bool = False
    provider_call_available: bool = False
    queue_execution_available: bool = False
    task_execution_available: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class WorkerContractValidation:
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    worker_id: str | None
    worker_name: str | None
    worker_role: str | None
    assigned_task_id: str | None
    worker_status: str | None
    trust_tier: str | None
    approval_token_id: str | None
    validated_at: str
    model_only: bool = True
    durable_storage_available: bool = False
    worker_spawn_available: bool = False
    worker_dispatch_available: bool = False
    provider_call_available: bool = False
    queue_execution_available: bool = False
    task_execution_available: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    token_minting_available: bool = False
    approval_storage_available: bool = False
    no_execution_guarantee: str = (
        "Plan 8 Phase 8.1 validates worker registry contracts as data only. "
        "It does not spawn workers, dispatch workers, call providers, run "
        "queues, execute tasks, run commands, perform safe writes, mint or store approval "
        "tokens, stage changes, commit, push, branch, create worktrees, stash, "
        "clean, reset, or checkout."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class WorkerOwnershipZone:
    zone_id: str
    worker_id: str
    assigned_task_id: str
    files: tuple[str, ...]
    mode: str
    trust_tier: str
    approval_token_id: str
    created_at: str
    model_only: bool = True
    durable_storage_available: bool = False
    lock_storage_available: bool = False
    conflict_detection_available: bool = False
    worker_dispatch_available: bool = False
    write_authority_granted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class WorkerFileLock:
    lock_id: str
    zone_id: str
    worker_id: str
    assigned_task_id: str
    files: tuple[str, ...]
    status: str
    acquired_at: str
    expires_at: str
    renewed_at: str | None = None
    renewal_count: int = 0
    released_at: str | None = None
    stale: bool = False
    blocked_reason: str | None = None
    model_only: bool = True
    durable_storage_available: bool = False
    automatic_release_available: bool = False
    worker_dispatch_available: bool = False
    write_authority_granted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class WorkerOwnershipLockValidation:
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    zone_id: str | None
    lock_id: str | None
    worker_id: str | None
    assigned_task_id: str | None
    files: tuple[str, ...] | None
    lock_status: str | None
    renewed_at: str | None
    renewal_count: int | None
    validated_at: str
    model_only: bool = True
    durable_storage_available: bool = False
    lock_storage_available: bool = False
    conflict_detection_available: bool = False
    worker_dispatch_available: bool = False
    queue_execution_available: bool = False
    task_execution_available: bool = False
    automatic_release_available: bool = False
    lease_renewal_execution_available: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    no_execution_guarantee: str = (
        "Plan 8 Phase 8.1 validates ownership zones and lease records as data "
        "only. It does not detect cross-worker conflicts, store locks, renew "
        "or release leases, dispatch workers, run queues, execute tasks, run "
        "commands, perform safe writes, stage changes, commit, push, branch, "
        "create worktrees, stash, clean, reset, or checkout."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class WorkerConflictReport:
    status: str
    conflict_free: bool
    blocked: bool
    reasons: tuple[str, ...]
    candidate_files: tuple[str, ...]
    dirty_conflicts: tuple[str, ...]
    ownership_conflicts: tuple[str, ...]
    protected_lane_conflicts: tuple[str, ...]
    stale_lock_conflicts: tuple[str, ...]
    checked_at: str
    model_only: bool = True
    preview_only: bool = True
    durable_storage_available: bool = False
    conflict_resolution_available: bool = False
    worker_dispatch_available: bool = False
    queue_execution_available: bool = False
    task_execution_available: bool = False
    automatic_cleanup_available: bool = False
    automatic_lock_release_available: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    no_execution_guarantee: str = (
        "Plan 8 Phase 3 detects worker dispatch conflicts as data only. It "
        "does not dispatch workers, resolve conflicts, clean dirty files, "
        "release locks, run queues, execute tasks, run commands, perform safe "
        "writes, stage changes, commit, push, branch, create worktrees, stash, "
        "clean, reset, or checkout."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class WorkerHandoffPacket:
    handoff_id: str
    task_id: str
    source_worker_id: str
    target_worker_id: str
    assigned_files: tuple[str, ...]
    scope: tuple[str, ...]
    expected_files: tuple[str, ...]
    ownership_zone_id: str
    lock_id: str
    lock_status: str
    conflict_report_status: str
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    required_checks: tuple[str, ...]
    receipt_refs: tuple[str, ...]
    closeout_expectations: tuple[str, ...]
    closeout_summary: str
    created_at: str
    model_only: bool = True
    preview_only: bool = True
    durable_storage_available: bool = False
    worker_reassignment_available: bool = False
    worker_dispatch_available: bool = False
    queue_execution_available: bool = False
    task_execution_available: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class WorkerHandoffPacketValidation:
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    handoff_id: str | None
    task_id: str | None
    source_worker_id: str | None
    target_worker_id: str | None
    expected_files: tuple[str, ...] | None
    validated_at: str
    model_only: bool = True
    preview_only: bool = True
    durable_storage_available: bool = False
    worker_reassignment_available: bool = False
    worker_dispatch_available: bool = False
    queue_execution_available: bool = False
    task_execution_available: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    no_execution_guarantee: str = (
        "Plan 8 Phase 8.2 validates worker handoff packets as data only. It "
        "does not reassign workers, dispatch workers, persist packets, run "
        "queues, execute tasks, run commands, perform safe writes, stage "
        "changes, commit, push, branch, create worktrees, stash, clean, reset, "
        "or checkout."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class StaleWorkerCloseoutProposal:
    proposal_id: str
    worker_id: str
    assigned_task_id: str
    stale_reason: str
    affected_files: tuple[str, ...]
    recommended_operator_actions: tuple[str, ...]
    required_checks: tuple[str, ...]
    receipt_refs: tuple[str, ...]
    created_at: str
    model_only: bool = True
    proposal_only: bool = True
    operator_review_required: bool = True
    durable_storage_available: bool = False
    automatic_cleanup_available: bool = False
    automatic_lock_release_available: bool = False
    worker_reassignment_available: bool = False
    worker_dispatch_available: bool = False
    queue_execution_available: bool = False
    task_execution_available: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class StaleWorkerCloseoutProposalValidation:
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    proposal_id: str | None
    worker_id: str | None
    assigned_task_id: str | None
    affected_files: tuple[str, ...] | None
    stale_heartbeat_detected: bool
    blocked_worker_detected: bool
    expired_lease_detected: bool
    validated_at: str
    model_only: bool = True
    proposal_only: bool = True
    operator_review_required: bool = True
    durable_storage_available: bool = False
    automatic_cleanup_available: bool = False
    automatic_lock_release_available: bool = False
    worker_reassignment_available: bool = False
    worker_dispatch_available: bool = False
    queue_execution_available: bool = False
    task_execution_available: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    no_execution_guarantee: str = (
        "Plan 8 Phase 8.2 validates stale worker closeout proposals as data "
        "only. It does not clean up stale workers, release locks, stop "
        "workers, delete branches, reassign workers, dispatch workers, persist "
        "proposals, run queues, execute tasks, run commands, perform safe "
        "writes, stage changes, commit, push, branch, create worktrees, stash, "
        "clean, reset, or checkout."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class OneWorkerFileZoneProof:
    proof_id: str
    worker_id: str
    assigned_task_id: str
    file_zone: tuple[str, ...]
    ownership_zone_id: str
    lock_id: str
    handoff_id: str
    conflict_report_status: str
    created_at: str
    model_only: bool = True
    proof_only: bool = True
    worker_dispatch_available: bool = False
    queue_execution_available: bool = False
    task_execution_available: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class OneWorkerFileZoneProofValidation:
    status: str
    accepted: bool
    blocked: bool
    reasons: tuple[str, ...]
    proof_id: str | None
    worker_id: str | None
    assigned_task_id: str | None
    file_zone: tuple[str, ...] | None
    coordination_receipt: dict[str, Any] | None
    validated_at: str
    model_only: bool = True
    proof_only: bool = True
    worker_dispatch_available: bool = False
    queue_execution_available: bool = False
    task_execution_available: bool = False
    command_authority_granted: bool = False
    write_authority_granted: bool = False
    git_mutation_authority_granted: bool = False
    no_execution_guarantee: str = (
        "Plan 8 Phase 8.3 proves one worker, one task, and one exact file-zone "
        "as data only. It does not dispatch workers, run queues, execute "
        "tasks, run commands, perform safe writes, stage changes, commit, "
        "push, branch, create worktrees, stash, clean, reset, or checkout."
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_worker_contract_model_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Integrated Control Master Plan 8/10",
        "phase": WORKER_CONTRACT_MODEL_PHASE,
        "status": "model-only",
        "worker_roles": WORKER_ROLES,
        "worker_statuses": WORKER_STATUSES,
        "terminal_statuses": TERMINAL_WORKER_STATUSES,
        "required_fields": REQUIRED_WORKER_CONTRACT_FIELDS,
        "required_trust_tier": WORKER_TRUST_TIER,
        "forbidden_authorities": FORBIDDEN_WORKER_CONTRACT_AUTHORITIES,
        "durable_storage_available": False,
        "worker_spawn_available": False,
        "worker_dispatch_available": False,
        "provider_call_available": False,
        "queue_execution_available": False,
        "task_execution_available": False,
        "background_loop_available": False,
        "command_authority_granted": False,
        "write_authority_granted": False,
        "git_mutation_authority_granted": False,
        "token_minting_available": False,
        "approval_storage_available": False,
        "safe_next_action": "Model worker registry records only; require later phase approval for locks, handoff packets, dispatch, or storage.",
    }


def build_worker_ownership_lock_model_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Integrated Control Master Plan 8/10",
        "phase": WORKER_OWNERSHIP_LOCK_PHASE,
        "status": "model-only",
        "ownership_zone_modes": OWNERSHIP_ZONE_MODES,
        "worker_lock_statuses": WORKER_LOCK_STATUSES,
        "max_lock_renewals": MAX_WORKER_LOCK_RENEWALS,
        "required_ownership_zone_fields": REQUIRED_OWNERSHIP_ZONE_FIELDS,
        "required_worker_file_lock_fields": REQUIRED_WORKER_FILE_LOCK_FIELDS,
        "required_trust_tier": WORKER_TRUST_TIER,
        "forbidden_authorities": FORBIDDEN_WORKER_CONTRACT_AUTHORITIES,
        "durable_storage_available": False,
        "lock_storage_available": False,
        "conflict_detection_available": False,
        "worker_dispatch_available": False,
        "queue_execution_available": False,
        "task_execution_available": False,
        "automatic_release_available": False,
        "lease_renewal_execution_available": False,
        "command_authority_granted": False,
        "write_authority_granted": False,
        "git_mutation_authority_granted": False,
        "safe_next_action": "Model exact file ownership and lease records only; require Plan 8 conflict reporting before handoff.",
    }


def build_worker_conflict_detection_model_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Integrated Control Master Plan 8/10",
        "phase": WORKER_CONFLICT_DETECTION_PHASE,
        "status": "model-only",
        "protected_file_prefixes": PROTECTED_WORKER_FILE_PREFIXES,
        "forbidden_authorities": FORBIDDEN_WORKER_CONTRACT_AUTHORITIES,
        "durable_storage_available": False,
        "conflict_detection_available": True,
        "conflict_resolution_available": False,
        "worker_dispatch_available": False,
        "queue_execution_available": False,
        "task_execution_available": False,
        "automatic_cleanup_available": False,
        "automatic_lock_release_available": False,
        "command_authority_granted": False,
        "write_authority_granted": False,
        "git_mutation_authority_granted": False,
        "safe_next_action": "Report dispatch-blocking conflicts only; require later approval for handoff packets or worker dispatch.",
    }


def build_worker_handoff_packet_model_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Integrated Control Master Plan 8/10",
        "phase": WORKER_HANDOFF_PACKET_PHASE,
        "status": "model-only",
        "required_handoff_packet_fields": REQUIRED_WORKER_HANDOFF_PACKET_FIELDS,
        "forbidden_authorities": FORBIDDEN_WORKER_CONTRACT_AUTHORITIES,
        "durable_storage_available": False,
        "worker_reassignment_available": False,
        "worker_dispatch_available": False,
        "queue_execution_available": False,
        "task_execution_available": False,
        "command_authority_granted": False,
        "write_authority_granted": False,
        "git_mutation_authority_granted": False,
        "safe_next_action": "Format handoff packets only; require later approval for stale worker proposals or one-worker proof.",
    }


def build_stale_worker_closeout_proposal_model_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Integrated Control Master Plan 8/10",
        "phase": STALE_WORKER_CLOSEOUT_PROPOSAL_PHASE,
        "status": "model-only",
        "required_stale_worker_closeout_proposal_fields": REQUIRED_STALE_WORKER_CLOSEOUT_PROPOSAL_FIELDS,
        "forbidden_authorities": FORBIDDEN_WORKER_CONTRACT_AUTHORITIES,
        "proposal_only": True,
        "operator_review_required": True,
        "durable_storage_available": False,
        "automatic_cleanup_available": False,
        "automatic_lock_release_available": False,
        "worker_reassignment_available": False,
        "worker_dispatch_available": False,
        "queue_execution_available": False,
        "task_execution_available": False,
        "command_authority_granted": False,
        "write_authority_granted": False,
        "git_mutation_authority_granted": False,
        "safe_next_action": "Produce stale worker closeout proposals only; require operator review for any cleanup or reassignment.",
    }


def build_one_worker_file_zone_proof_model_status() -> dict[str, Any]:
    return {
        "plan": "Cartographer Integrated Control Master Plan 8/10",
        "phase": ONE_WORKER_FILE_ZONE_PROOF_PHASE,
        "status": "model-only",
        "required_one_worker_file_zone_proof_fields": REQUIRED_ONE_WORKER_FILE_ZONE_PROOF_FIELDS,
        "forbidden_authorities": FORBIDDEN_WORKER_CONTRACT_AUTHORITIES,
        "proof_only": True,
        "coordination_receipt_available": True,
        "worker_dispatch_available": False,
        "queue_execution_available": False,
        "task_execution_available": False,
        "command_authority_granted": False,
        "write_authority_granted": False,
        "git_mutation_authority_granted": False,
        "safe_next_action": "Stop after proof; require explicit Plan 9 approval before any commit-gate work.",
    }


def detect_worker_dispatch_conflicts(
    *,
    candidate_files: Any,
    ownership_zones: Any,
    worker_locks: Any,
    dirty_files: Any,
    protected_file_prefixes: tuple[str, ...] = PROTECTED_WORKER_FILE_PREFIXES,
    now: datetime | None = None,
) -> WorkerConflictReport:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []

    candidate_scope = _file_tuple_value(candidate_files, "candidate_files", reasons)
    dirty_scope = _file_tuple_value(dirty_files, "dirty_files", reasons)
    zone_payloads = _payload_tuple(
        ownership_zones,
        WorkerOwnershipZone,
        "ownership_zones",
        reasons,
    )
    lock_payloads = _payload_tuple(
        worker_locks,
        WorkerFileLock,
        "worker_locks",
        reasons,
    )

    dirty_conflicts: tuple[str, ...] = ()
    ownership_conflicts: tuple[str, ...] = ()
    protected_lane_conflicts: tuple[str, ...] = ()
    stale_lock_conflicts: tuple[str, ...] = ()

    if candidate_scope is None:
        candidate_scope = ()
    if dirty_scope is None:
        dirty_scope = ()
    if zone_payloads is None:
        zone_payloads = ()
    if lock_payloads is None:
        lock_payloads = ()

    if candidate_scope == ():
        reasons.append("missing_candidate_files")
    dirty_conflicts = tuple(path for path in candidate_scope if path in set(dirty_scope))
    if dirty_conflicts:
        reasons.append("dirty_file_conflict")

    protected_lane_conflicts = tuple(
        path for path in candidate_scope if _protected_worker_path(path, protected_file_prefixes)
    )
    if protected_lane_conflicts:
        reasons.append("protected_lane_conflict")

    ownership_conflicts = _ownership_conflict_files(candidate_scope, zone_payloads, reasons)
    if ownership_conflicts:
        reasons.append("overlapping_file_ownership")

    stale_lock_conflicts = _stale_lock_conflict_files(candidate_scope, lock_payloads)
    if stale_lock_conflicts:
        reasons.append("stale_lock_ambiguity")

    blocked_reasons = tuple(_dedupe_reasons(reasons))
    conflict_free = not blocked_reasons
    return WorkerConflictReport(
        status="clear" if conflict_free else "blocked",
        conflict_free=conflict_free,
        blocked=not conflict_free,
        reasons=blocked_reasons,
        candidate_files=candidate_scope,
        dirty_conflicts=dirty_conflicts,
        ownership_conflicts=ownership_conflicts,
        protected_lane_conflicts=protected_lane_conflicts,
        stale_lock_conflicts=stale_lock_conflicts,
        checked_at=_format_utc(current_time),
    )


def validate_worker_handoff_packet(
    packet: Any,
    *,
    expected_task_id: str,
    expected_files: Any,
    now: datetime | None = None,
) -> WorkerHandoffPacketValidation:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []

    expected_task_id = expected_task_id.strip() if expected_task_id else ""
    if not expected_task_id:
        reasons.append("missing_expected_task_id")
    expected_file_scope = _file_tuple_value(expected_files, "expected_files", reasons)

    payload = _handoff_packet_payload(packet)
    if payload is None:
        reasons.append("malformed_handoff_packet")
        return _handoff_packet_validation(
            reasons=reasons,
            current_time=current_time,
            handoff_id=None,
            task_id=None,
            source_worker_id=None,
            target_worker_id=None,
            expected_files=expected_file_scope,
        )

    for field in REQUIRED_WORKER_HANDOFF_PACKET_FIELDS:
        if field not in payload:
            reasons.append(f"missing_handoff_packet_field:{field}")

    handoff_id = _string_field(payload, "handoff_id", reasons)
    task_id = _string_field(payload, "task_id", reasons)
    source_worker_id = _string_field(payload, "source_worker_id", reasons)
    target_worker_id = _string_field(payload, "target_worker_id", reasons)
    assigned_files = _file_tuple_value(payload.get("assigned_files"), "assigned_files", reasons)
    scope = _file_tuple_value(payload.get("scope"), "scope", reasons)
    packet_expected_files = _file_tuple_value(payload.get("expected_files"), "expected_files", reasons)
    ownership_zone_id = _string_field(payload, "ownership_zone_id", reasons)
    lock_id = _string_field(payload, "lock_id", reasons)
    lock_status = _string_field(payload, "lock_status", reasons)
    allowed_actions = _string_tuple_value(payload.get("allowed_actions"), "allowed_actions", reasons)
    forbidden_actions = _string_tuple_value(payload.get("forbidden_actions"), "forbidden_actions", reasons)
    evidence_requirements = _string_tuple_value(
        payload.get("evidence_requirements"),
        "evidence_requirements",
        reasons,
    )
    required_checks = _string_tuple_value(payload.get("required_checks"), "required_checks", reasons)
    receipt_refs = _string_tuple_value(payload.get("receipt_refs"), "receipt_refs", reasons)
    closeout_expectations = _string_tuple_value(
        payload.get("closeout_expectations"),
        "closeout_expectations",
        reasons,
    )
    closeout_summary = _string_field(payload, "closeout_summary", reasons)
    conflict_report_status = _string_field(payload, "conflict_report_status", reasons)
    created_at = _datetime_field(payload, "created_at", reasons, required=True)

    if task_id and expected_task_id and task_id != expected_task_id:
        reasons.append("handoff_task_mismatch")
    if source_worker_id and target_worker_id and source_worker_id == target_worker_id:
        reasons.append("handoff_requires_distinct_workers")
    if assigned_files == ():
        reasons.append("missing_assigned_files")
    if expected_file_scope is not None and packet_expected_files is not None and packet_expected_files != expected_file_scope:
        reasons.append("handoff_expected_files_mismatch")
    if assigned_files is not None and packet_expected_files is not None and assigned_files != packet_expected_files:
        reasons.append("handoff_assigned_files_mismatch")
    if scope is not None and packet_expected_files is not None and not set(packet_expected_files).issubset(set(scope)):
        reasons.append("handoff_scope_missing_expected_files")
    if ownership_zone_id is None:
        reasons.append("missing_ownership_zone_id")
    if lock_id is None:
        reasons.append("missing_lock_id")
    if lock_status and lock_status != "active":
        reasons.append("handoff_requires_active_lock")
    if allowed_actions == ():
        reasons.append("missing_allowed_actions")
    if forbidden_actions == ():
        reasons.append("missing_forbidden_actions")
    if evidence_requirements == ():
        reasons.append("missing_evidence_requirements")
    if required_checks == ():
        reasons.append("missing_required_checks")
    if receipt_refs == ():
        reasons.append("missing_receipt_refs")
    if closeout_expectations == ():
        reasons.append("missing_closeout_expectations")
    if closeout_summary is not None and closeout_summary == "pending":
        reasons.append("closeout_summary_must_be_specific")
    if conflict_report_status and conflict_report_status != "clear":
        reasons.append("handoff_requires_clear_conflict_report")
    if created_at is not None and created_at > current_time:
        reasons.append("handoff_created_at_in_future")

    return _handoff_packet_validation(
        reasons=reasons,
        current_time=current_time,
        handoff_id=handoff_id,
        task_id=task_id,
        source_worker_id=source_worker_id,
        target_worker_id=target_worker_id,
        expected_files=packet_expected_files,
    )


def validate_stale_worker_closeout_proposal(
    proposal: Any,
    *,
    stale_worker: Any,
    stale_locks: Any,
    now: datetime | None = None,
) -> StaleWorkerCloseoutProposalValidation:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []

    payload = _stale_worker_closeout_proposal_payload(proposal)
    worker_payload = _contract_payload(stale_worker)
    lock_payloads = _payload_tuple(
        stale_locks,
        WorkerFileLock,
        "stale_locks",
        reasons,
    )
    if payload is None:
        reasons.append("malformed_stale_worker_closeout_proposal")
        return _stale_worker_closeout_proposal_validation(
            reasons=reasons,
            current_time=current_time,
            proposal_id=None,
            worker_id=None,
            assigned_task_id=None,
            affected_files=None,
            stale_heartbeat_detected=False,
            blocked_worker_detected=False,
            expired_lease_detected=False,
        )
    if worker_payload is None:
        reasons.append("malformed_stale_worker")
    if lock_payloads is None:
        lock_payloads = ()

    for field in REQUIRED_STALE_WORKER_CLOSEOUT_PROPOSAL_FIELDS:
        if field not in payload:
            reasons.append(f"missing_stale_worker_closeout_proposal_field:{field}")

    proposal_id = _string_field(payload, "proposal_id", reasons)
    worker_id = _string_field(payload, "worker_id", reasons)
    assigned_task_id = _string_field(payload, "assigned_task_id", reasons)
    stale_reason = _string_field(payload, "stale_reason", reasons)
    affected_files = _file_tuple_value(payload.get("affected_files"), "affected_files", reasons)
    recommended_operator_actions = _string_tuple_value(
        payload.get("recommended_operator_actions"),
        "recommended_operator_actions",
        reasons,
    )
    required_checks = _string_tuple_value(payload.get("required_checks"), "required_checks", reasons)
    receipt_refs = _string_tuple_value(payload.get("receipt_refs"), "receipt_refs", reasons)
    created_at = _datetime_field(payload, "created_at", reasons, required=True)

    stale_heartbeat_detected = False
    blocked_worker_detected = False
    if worker_payload is not None:
        worker_status = _string_field(worker_payload, "status", reasons)
        worker_stale = _bool_field(worker_payload, "stale", reasons)
        worker_blocked_reason = _optional_string_field(worker_payload, "blocked_reason", reasons)
        heartbeat_at = _datetime_field(worker_payload, "heartbeat_at", reasons, required=False)
        expected_worker_id = _string_field(worker_payload, "worker_id", reasons)
        expected_task_id = _string_field(worker_payload, "assigned_task_id", reasons)
        stale_heartbeat_detected = (
            worker_status == "stale"
            and worker_stale is True
            and heartbeat_at is not None
            and heartbeat_at < current_time
        )
        blocked_worker_detected = worker_status == "blocked" and bool(worker_blocked_reason)
        if not stale_heartbeat_detected and not blocked_worker_detected:
            reasons.append("worker_not_stale")
        if worker_id and expected_worker_id and worker_id != expected_worker_id:
            reasons.append("proposal_worker_mismatch")
        if assigned_task_id and expected_task_id and assigned_task_id != expected_task_id:
            reasons.append("proposal_task_mismatch")

    stale_lock_files = _stale_or_expired_lock_files(lock_payloads, current_time)
    expired_lease_detected = _expired_lease_detected(lock_payloads, current_time)
    if not stale_lock_files:
        reasons.append("missing_stale_lock_evidence")
    if affected_files == ():
        reasons.append("missing_affected_files")
    if affected_files is not None and stale_lock_files and not set(affected_files).issubset(set(stale_lock_files)):
        reasons.append("affected_files_lack_stale_lock_evidence")
    if not stale_reason or stale_reason == "stale":
        reasons.append("stale_reason_must_be_specific")
    if recommended_operator_actions == ():
        reasons.append("missing_recommended_operator_actions")
    if recommended_operator_actions and _unsafe_closeout_actions(recommended_operator_actions):
        reasons.append("unsafe_closeout_action")
    if required_checks == ():
        reasons.append("missing_required_checks")
    if receipt_refs == ():
        reasons.append("missing_receipt_refs")
    if created_at is not None and created_at > current_time:
        reasons.append("proposal_created_at_in_future")

    return _stale_worker_closeout_proposal_validation(
        reasons=reasons,
        current_time=current_time,
        proposal_id=proposal_id,
        worker_id=worker_id,
        assigned_task_id=assigned_task_id,
        affected_files=affected_files,
        stale_heartbeat_detected=stale_heartbeat_detected,
        blocked_worker_detected=blocked_worker_detected,
        expired_lease_detected=expired_lease_detected,
    )


def validate_one_worker_file_zone_proof(
    proof: Any,
    *,
    worker: Any,
    ownership_zone: Any,
    worker_lock: Any,
    conflict_report: Any,
    handoff_packet: Any,
    now: datetime | None = None,
) -> OneWorkerFileZoneProofValidation:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []

    payload = _one_worker_file_zone_proof_payload(proof)
    worker_payload = _contract_payload(worker)
    zone_payload = _ownership_zone_payload(ownership_zone)
    lock_payload = _worker_lock_payload(worker_lock)
    conflict_payload = _conflict_report_payload(conflict_report)
    handoff_payload = _handoff_packet_payload(handoff_packet)
    if payload is None:
        reasons.append("malformed_one_worker_file_zone_proof")
        return _one_worker_file_zone_proof_validation(
            reasons=reasons,
            current_time=current_time,
            proof_id=None,
            worker_id=None,
            assigned_task_id=None,
            file_zone=None,
        )

    for field in REQUIRED_ONE_WORKER_FILE_ZONE_PROOF_FIELDS:
        if field not in payload:
            reasons.append(f"missing_one_worker_file_zone_proof_field:{field}")

    proof_id = _string_field(payload, "proof_id", reasons)
    worker_id = _string_field(payload, "worker_id", reasons)
    assigned_task_id = _string_field(payload, "assigned_task_id", reasons)
    file_zone = _file_tuple_value(payload.get("file_zone"), "file_zone", reasons)
    ownership_zone_id = _string_field(payload, "ownership_zone_id", reasons)
    lock_id = _string_field(payload, "lock_id", reasons)
    handoff_id = _string_field(payload, "handoff_id", reasons)
    conflict_report_status = _string_field(payload, "conflict_report_status", reasons)
    created_at = _datetime_field(payload, "created_at", reasons, required=True)

    if file_zone == ():
        reasons.append("missing_file_zone")
    if worker_payload is None:
        reasons.append("malformed_worker_contract")
    if zone_payload is None:
        reasons.append("malformed_ownership_zone")
    if lock_payload is None:
        reasons.append("malformed_worker_file_lock")
    if conflict_payload is None:
        reasons.append("malformed_conflict_report")
    if handoff_payload is None:
        reasons.append("malformed_handoff_packet")

    if worker_payload is not None:
        _match_string(worker_id, _string_field(worker_payload, "worker_id", reasons), "proof_worker_mismatch", reasons)
        _match_string(assigned_task_id, _string_field(worker_payload, "assigned_task_id", reasons), "proof_task_mismatch", reasons)
        if _string_field(worker_payload, "status", reasons) != "active":
            reasons.append("proof_requires_active_worker")
        if _bool_field(worker_payload, "active", reasons) is not True:
            reasons.append("proof_requires_active_worker_state")
        worker_allowed_files = _file_tuple_value(worker_payload.get("allowed_files"), "worker_allowed_files", reasons)
        if file_zone is not None and worker_allowed_files is not None and file_zone != worker_allowed_files:
            reasons.append("proof_file_zone_must_match_worker_allowed_files")

    if zone_payload is not None:
        _match_string(worker_id, _string_field(zone_payload, "worker_id", reasons), "proof_zone_worker_mismatch", reasons)
        _match_string(assigned_task_id, _string_field(zone_payload, "assigned_task_id", reasons), "proof_zone_task_mismatch", reasons)
        _match_string(ownership_zone_id, _string_field(zone_payload, "zone_id", reasons), "proof_zone_id_mismatch", reasons)
        zone_files = _file_tuple_value(zone_payload.get("files"), "ownership_zone_files", reasons)
        if file_zone is not None and zone_files is not None and file_zone != zone_files:
            reasons.append("proof_file_zone_must_match_ownership_zone")

    if lock_payload is not None:
        _match_string(worker_id, _string_field(lock_payload, "worker_id", reasons), "proof_lock_worker_mismatch", reasons)
        _match_string(assigned_task_id, _string_field(lock_payload, "assigned_task_id", reasons), "proof_lock_task_mismatch", reasons)
        _match_string(ownership_zone_id, _string_field(lock_payload, "zone_id", reasons), "proof_lock_zone_mismatch", reasons)
        _match_string(lock_id, _string_field(lock_payload, "lock_id", reasons), "proof_lock_id_mismatch", reasons)
        if _string_field(lock_payload, "status", reasons) != "active":
            reasons.append("proof_requires_active_lock")
        if _bool_field(lock_payload, "stale", reasons) is True:
            reasons.append("proof_lock_cannot_be_stale")
        lock_files = _file_tuple_value(lock_payload.get("files"), "lock_files", reasons)
        if file_zone is not None and lock_files is not None and file_zone != lock_files:
            reasons.append("proof_file_zone_must_match_lock")

    if conflict_payload is not None:
        _match_string(conflict_report_status, _string_field(conflict_payload, "status", reasons), "proof_conflict_status_mismatch", reasons)
        if conflict_payload.get("conflict_free") is not True:
            reasons.append("proof_requires_clear_conflict_report")
        conflict_files = _file_tuple_value(conflict_payload.get("candidate_files"), "conflict_candidate_files", reasons)
        if file_zone is not None and conflict_files is not None and file_zone != conflict_files:
            reasons.append("proof_file_zone_must_match_conflict_report")

    if handoff_payload is not None:
        _match_string(worker_id, _string_field(handoff_payload, "source_worker_id", reasons), "proof_handoff_worker_mismatch", reasons)
        _match_string(assigned_task_id, _string_field(handoff_payload, "task_id", reasons), "proof_handoff_task_mismatch", reasons)
        _match_string(handoff_id, _string_field(handoff_payload, "handoff_id", reasons), "proof_handoff_id_mismatch", reasons)
        _match_string(ownership_zone_id, _string_field(handoff_payload, "ownership_zone_id", reasons), "proof_handoff_zone_mismatch", reasons)
        _match_string(lock_id, _string_field(handoff_payload, "lock_id", reasons), "proof_handoff_lock_mismatch", reasons)
        if _string_field(handoff_payload, "conflict_report_status", reasons) != "clear":
            reasons.append("proof_handoff_requires_clear_conflict_report")
        handoff_files = _file_tuple_value(handoff_payload.get("expected_files"), "handoff_expected_files", reasons)
        if file_zone is not None and handoff_files is not None and file_zone != handoff_files:
            reasons.append("proof_file_zone_must_match_handoff")

    if conflict_report_status and conflict_report_status != "clear":
        reasons.append("proof_requires_clear_conflict_status")
    if created_at is not None and created_at > current_time:
        reasons.append("proof_created_at_in_future")

    return _one_worker_file_zone_proof_validation(
        reasons=reasons,
        current_time=current_time,
        proof_id=proof_id,
        worker_id=worker_id,
        assigned_task_id=assigned_task_id,
        file_zone=file_zone,
        coordination_receipt=_one_worker_file_zone_coordination_receipt(
            proof_id=proof_id,
            worker_id=worker_id,
            assigned_task_id=assigned_task_id,
            file_zone=file_zone,
            ownership_zone_id=ownership_zone_id,
            lock_id=lock_id,
            handoff_id=handoff_id,
            conflict_report_status=conflict_report_status,
            created_at=created_at,
        )
        if not _dedupe_reasons(reasons)
        else None,
    )


def validate_worker_ownership_lock(
    ownership_zone: Any,
    worker_lock: Any,
    *,
    expected_trust_tier: str = WORKER_TRUST_TIER,
    expected_approval_token_id: str,
    now: datetime | None = None,
) -> WorkerOwnershipLockValidation:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []

    expected_trust_tier = expected_trust_tier.strip() if expected_trust_tier else ""
    expected_approval_token_id = expected_approval_token_id.strip() if expected_approval_token_id else ""
    if not expected_trust_tier:
        reasons.append("missing_expected_trust_tier")
    if not expected_approval_token_id:
        reasons.append("missing_expected_approval_token_id")

    zone_payload = _ownership_zone_payload(ownership_zone)
    lock_payload = _worker_lock_payload(worker_lock)
    if zone_payload is None:
        reasons.append("malformed_ownership_zone")
    if lock_payload is None:
        reasons.append("malformed_worker_file_lock")
    if zone_payload is None or lock_payload is None:
        return _ownership_lock_validation(
            reasons=reasons,
            current_time=current_time,
            zone_id=None,
            lock_id=None,
            worker_id=None,
            assigned_task_id=None,
            files=None,
            lock_status=None,
            renewed_at=None,
            renewal_count=None,
        )

    for field in REQUIRED_OWNERSHIP_ZONE_FIELDS:
        if field not in zone_payload:
            reasons.append(f"missing_ownership_zone_field:{field}")
    for field in REQUIRED_WORKER_FILE_LOCK_FIELDS:
        if field not in lock_payload:
            reasons.append(f"missing_worker_file_lock_field:{field}")

    zone_id = _string_field(zone_payload, "zone_id", reasons)
    zone_worker_id = _string_field(zone_payload, "worker_id", reasons)
    zone_task_id = _string_field(zone_payload, "assigned_task_id", reasons)
    zone_files = _exact_file_tuple_field(zone_payload, "files", reasons)
    zone_mode = _string_field(zone_payload, "mode", reasons)
    trust_tier = _string_field(zone_payload, "trust_tier", reasons)
    approval_token_id = _string_field(zone_payload, "approval_token_id", reasons)
    zone_created_at = _datetime_field(zone_payload, "created_at", reasons, required=True)

    lock_id = _string_field(lock_payload, "lock_id", reasons)
    lock_zone_id = _string_field(lock_payload, "zone_id", reasons)
    lock_worker_id = _string_field(lock_payload, "worker_id", reasons)
    lock_task_id = _string_field(lock_payload, "assigned_task_id", reasons)
    lock_files = _exact_file_tuple_field(lock_payload, "files", reasons)
    lock_status = _string_field(lock_payload, "status", reasons)
    acquired_at = _datetime_field(lock_payload, "acquired_at", reasons, required=True)
    expires_at = _datetime_field(lock_payload, "expires_at", reasons, required=True)
    renewed_at = _datetime_field(lock_payload, "renewed_at", reasons, required=False)
    renewal_count = _int_field(lock_payload, "renewal_count", reasons)
    released_at = _datetime_field(lock_payload, "released_at", reasons, required=False)
    stale = _bool_field(lock_payload, "stale", reasons)
    blocked_reason = _optional_string_field(lock_payload, "blocked_reason", reasons)

    if zone_mode and zone_mode not in OWNERSHIP_ZONE_MODES:
        reasons.append("unknown_ownership_zone_mode")
    if lock_status and lock_status not in WORKER_LOCK_STATUSES:
        reasons.append("unknown_worker_file_lock_status")
    if trust_tier and expected_trust_tier and trust_tier != expected_trust_tier:
        reasons.append("wrong_trust_tier")
    if approval_token_id and expected_approval_token_id and approval_token_id != expected_approval_token_id:
        reasons.append("wrong_approval_token")
    if zone_files == ():
        reasons.append("missing_ownership_zone_files")
    if lock_files == ():
        reasons.append("missing_worker_file_lock_files")
    if zone_id and lock_zone_id and zone_id != lock_zone_id:
        reasons.append("lock_zone_mismatch")
    if zone_worker_id and lock_worker_id and zone_worker_id != lock_worker_id:
        reasons.append("lock_worker_mismatch")
    if zone_task_id and lock_task_id and zone_task_id != lock_task_id:
        reasons.append("lock_task_mismatch")
    if zone_files is not None and lock_files is not None and zone_files != lock_files:
        reasons.append("lock_files_must_match_ownership_zone")
    if zone_created_at is not None and zone_created_at > current_time:
        reasons.append("ownership_zone_created_at_in_future")
    if acquired_at is not None and zone_created_at is not None and acquired_at < zone_created_at:
        reasons.append("lock_acquired_before_ownership_zone")
    if expires_at is not None and acquired_at is not None and expires_at <= acquired_at:
        reasons.append("lock_expires_at_not_after_acquired_at")
    if renewal_count is not None and (renewal_count < 0 or renewal_count > MAX_WORKER_LOCK_RENEWALS):
        reasons.append("renewal_count_out_of_bounds")
    if renewal_count and renewed_at is None:
        reasons.append("renewed_at_required")
    if renewed_at is not None and renewal_count == 0:
        reasons.append("renewal_count_required")
    if renewed_at is not None and acquired_at is not None and renewed_at < acquired_at:
        reasons.append("renewed_at_before_acquired_at")
    if renewed_at is not None and expires_at is not None and renewed_at >= expires_at:
        reasons.append("renewed_at_not_before_expires_at")
    if lock_status == "active" and stale is True:
        reasons.append("active_lock_cannot_be_stale")
    if lock_status == "active" and released_at is not None:
        reasons.append("active_lock_cannot_be_released")
    if lock_status == "released" and released_at is None:
        reasons.append("released_lock_requires_released_at")
    if lock_status == "stale" and stale is not True:
        reasons.append("stale_lock_requires_stale_flag")
    if lock_status == "stale" and not blocked_reason:
        reasons.append("stale_lock_requires_blocked_reason")

    return _ownership_lock_validation(
        reasons=reasons,
        current_time=current_time,
        zone_id=zone_id,
        lock_id=lock_id,
        worker_id=zone_worker_id,
        assigned_task_id=zone_task_id,
        files=zone_files,
        lock_status=lock_status,
        renewed_at=_format_utc(renewed_at) if renewed_at else None,
        renewal_count=renewal_count,
    )


def validate_worker_contract(
    contract: Any,
    *,
    expected_trust_tier: str = WORKER_TRUST_TIER,
    expected_approval_token_id: str,
    now: datetime | None = None,
) -> WorkerContractValidation:
    current_time = now or datetime.now(UTC)
    reasons: list[str] = []

    expected_trust_tier = expected_trust_tier.strip() if expected_trust_tier else ""
    expected_approval_token_id = expected_approval_token_id.strip() if expected_approval_token_id else ""
    if not expected_trust_tier:
        reasons.append("missing_expected_trust_tier")
    if not expected_approval_token_id:
        reasons.append("missing_expected_approval_token_id")

    payload = _contract_payload(contract)
    if payload is None:
        reasons.append("malformed_worker_contract")
        return _validation(
            reasons=reasons,
            current_time=current_time,
            worker_id=None,
            worker_name=None,
            worker_role=None,
            assigned_task_id=None,
            worker_status=None,
            trust_tier=None,
            approval_token_id=None,
        )

    for field in REQUIRED_WORKER_CONTRACT_FIELDS:
        if field not in payload:
            reasons.append(f"missing_required_field:{field}")

    worker_id = _string_field(payload, "worker_id", reasons)
    worker_name = _string_field(payload, "worker_name", reasons)
    worker_role = _string_field(payload, "worker_role", reasons)
    assigned_task_id = _string_field(payload, "assigned_task_id", reasons)
    trust_tier = _string_field(payload, "trust_tier", reasons)
    approval_token_id = _string_field(payload, "approval_token_id", reasons)
    worker_status = _string_field(payload, "status", reasons)
    active = _bool_field(payload, "active", reasons)
    stale = _bool_field(payload, "stale", reasons)
    current_step = _optional_string_field(payload, "current_step", reasons)
    heartbeat_at = _datetime_field(payload, "heartbeat_at", reasons, required=False)
    last_check_in_at = _datetime_field(payload, "last_check_in_at", reasons, required=False)
    blocked_reason = _optional_string_field(payload, "blocked_reason", reasons)
    created_at = _datetime_field(payload, "created_at", reasons, required=True)
    started_at = _datetime_field(payload, "started_at", reasons, required=False)
    completed_at = _datetime_field(payload, "completed_at", reasons, required=False)
    allowed_files = _exact_file_tuple_field(payload, "allowed_files", reasons)
    forbidden_files = _exact_file_tuple_field(payload, "forbidden_files", reasons)

    if worker_role and worker_role not in WORKER_ROLES:
        reasons.append("unknown_worker_role")
    if worker_status and worker_status not in WORKER_STATUSES:
        reasons.append("unknown_worker_status")
    if trust_tier and expected_trust_tier and trust_tier != expected_trust_tier:
        reasons.append("wrong_trust_tier")
    if approval_token_id and expected_approval_token_id and approval_token_id != expected_approval_token_id:
        reasons.append("wrong_approval_token")
    if allowed_files == ():
        reasons.append("missing_allowed_files")
    if forbidden_files == ():
        reasons.append("missing_forbidden_files")
    if allowed_files is not None and forbidden_files is not None:
        if set(allowed_files).intersection(forbidden_files):
            reasons.append("allowed_file_forbidden")
    if active is True and worker_status != "active":
        reasons.append("active_state_status_mismatch")
    if stale is True and worker_status != "stale":
        reasons.append("stale_state_status_mismatch")
    if active is True and stale is True:
        reasons.append("worker_cannot_be_active_and_stale")
    if worker_status == "active" and active is not True:
        reasons.append("active_status_requires_active_state")
    if worker_status == "stale" and stale is not True:
        reasons.append("stale_status_requires_stale_state")
    if worker_status == "blocked" and not blocked_reason:
        reasons.append("blocked_reason_required")
    if worker_status == "completed" and completed_at is None:
        reasons.append("completed_at_required")
    if worker_status in ("active", "stale") and heartbeat_at is None:
        reasons.append("heartbeat_required")
    if worker_status == "active" and not current_step:
        reasons.append("current_step_required")
    if created_at is not None and created_at > current_time:
        reasons.append("created_at_in_future")
    if started_at is not None and created_at is not None and started_at < created_at:
        reasons.append("started_at_before_created_at")
    if completed_at is not None and created_at is not None and completed_at < created_at:
        reasons.append("completed_at_before_created_at")
    if last_check_in_at is not None and created_at is not None and last_check_in_at < created_at:
        reasons.append("last_check_in_before_created_at")

    return _validation(
        reasons=reasons,
        current_time=current_time,
        worker_id=worker_id,
        worker_name=worker_name,
        worker_role=worker_role,
        assigned_task_id=assigned_task_id,
        worker_status=worker_status,
        trust_tier=trust_tier,
        approval_token_id=approval_token_id,
    )


def _validation(
    *,
    reasons: list[str],
    current_time: datetime,
    worker_id: str | None,
    worker_name: str | None,
    worker_role: str | None,
    assigned_task_id: str | None,
    worker_status: str | None,
    trust_tier: str | None,
    approval_token_id: str | None,
) -> WorkerContractValidation:
    blocked_reasons = tuple(_dedupe_reasons(reasons))
    accepted = not blocked_reasons
    return WorkerContractValidation(
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=blocked_reasons,
        worker_id=worker_id,
        worker_name=worker_name,
        worker_role=worker_role,
        assigned_task_id=assigned_task_id,
        worker_status=worker_status,
        trust_tier=trust_tier,
        approval_token_id=approval_token_id,
        validated_at=_format_utc(current_time),
    )


def _ownership_lock_validation(
    *,
    reasons: list[str],
    current_time: datetime,
    zone_id: str | None,
    lock_id: str | None,
    worker_id: str | None,
    assigned_task_id: str | None,
    files: tuple[str, ...] | None,
    lock_status: str | None,
    renewed_at: str | None,
    renewal_count: int | None,
) -> WorkerOwnershipLockValidation:
    blocked_reasons = tuple(_dedupe_reasons(reasons))
    accepted = not blocked_reasons
    return WorkerOwnershipLockValidation(
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=blocked_reasons,
        zone_id=zone_id,
        lock_id=lock_id,
        worker_id=worker_id,
        assigned_task_id=assigned_task_id,
        files=files,
        lock_status=lock_status,
        renewed_at=renewed_at,
        renewal_count=renewal_count,
        validated_at=_format_utc(current_time),
    )


def _handoff_packet_validation(
    *,
    reasons: list[str],
    current_time: datetime,
    handoff_id: str | None,
    task_id: str | None,
    source_worker_id: str | None,
    target_worker_id: str | None,
    expected_files: tuple[str, ...] | None,
) -> WorkerHandoffPacketValidation:
    blocked_reasons = tuple(_dedupe_reasons(reasons))
    accepted = not blocked_reasons
    return WorkerHandoffPacketValidation(
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=blocked_reasons,
        handoff_id=handoff_id,
        task_id=task_id,
        source_worker_id=source_worker_id,
        target_worker_id=target_worker_id,
        expected_files=expected_files,
        validated_at=_format_utc(current_time),
    )


def _stale_worker_closeout_proposal_validation(
    *,
    reasons: list[str],
    current_time: datetime,
    proposal_id: str | None,
    worker_id: str | None,
    assigned_task_id: str | None,
    affected_files: tuple[str, ...] | None,
    stale_heartbeat_detected: bool,
    blocked_worker_detected: bool,
    expired_lease_detected: bool,
) -> StaleWorkerCloseoutProposalValidation:
    blocked_reasons = tuple(_dedupe_reasons(reasons))
    accepted = not blocked_reasons
    return StaleWorkerCloseoutProposalValidation(
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=blocked_reasons,
        proposal_id=proposal_id,
        worker_id=worker_id,
        assigned_task_id=assigned_task_id,
        affected_files=affected_files,
        stale_heartbeat_detected=stale_heartbeat_detected,
        blocked_worker_detected=blocked_worker_detected,
        expired_lease_detected=expired_lease_detected,
        validated_at=_format_utc(current_time),
    )


def _one_worker_file_zone_proof_validation(
    *,
    reasons: list[str],
    current_time: datetime,
    proof_id: str | None,
    worker_id: str | None,
    assigned_task_id: str | None,
    file_zone: tuple[str, ...] | None,
    coordination_receipt: dict[str, Any] | None = None,
) -> OneWorkerFileZoneProofValidation:
    blocked_reasons = tuple(_dedupe_reasons(reasons))
    accepted = not blocked_reasons
    return OneWorkerFileZoneProofValidation(
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reasons=blocked_reasons,
        proof_id=proof_id,
        worker_id=worker_id,
        assigned_task_id=assigned_task_id,
        file_zone=file_zone,
        coordination_receipt=coordination_receipt,
        validated_at=_format_utc(current_time),
    )


def _one_worker_file_zone_coordination_receipt(
    *,
    proof_id: str | None,
    worker_id: str | None,
    assigned_task_id: str | None,
    file_zone: tuple[str, ...] | None,
    ownership_zone_id: str | None,
    lock_id: str | None,
    handoff_id: str | None,
    conflict_report_status: str | None,
    created_at: datetime | None,
) -> dict[str, Any]:
    return {
        "schema_version": "cartographer.one_worker_file_zone_coordination_receipt.v1",
        "phase": ONE_WORKER_FILE_ZONE_PROOF_PHASE,
        "proof_id": proof_id,
        "worker_id": worker_id,
        "assigned_task_id": assigned_task_id,
        "file_zone": file_zone or (),
        "ownership_zone_id": ownership_zone_id,
        "lock_id": lock_id,
        "handoff_id": handoff_id,
        "conflict_report_status": conflict_report_status,
        "created_at": _format_utc(created_at) if created_at else None,
        "worker_count": 1,
        "task_count": 1,
        "file_zone_count": 1 if file_zone else 0,
        "worker_dispatch_performed": False,
        "queue_execution_performed": False,
        "task_execution_performed": False,
        "command_execution_performed": False,
        "safe_write_performed": False,
        "git_mutation_performed": False,
        "branch_or_worktree_created": False,
        "provider_call_performed": False,
        "durable_storage_performed": False,
    }


def _contract_payload(contract: Any) -> dict[str, Any] | None:
    if isinstance(contract, WorkerContract):
        return contract.to_dict()
    if isinstance(contract, dict):
        return contract
    return None


def _handoff_packet_payload(packet: Any) -> dict[str, Any] | None:
    if isinstance(packet, WorkerHandoffPacket):
        return packet.to_dict()
    if isinstance(packet, dict):
        return packet
    return None


def _stale_worker_closeout_proposal_payload(proposal: Any) -> dict[str, Any] | None:
    if isinstance(proposal, StaleWorkerCloseoutProposal):
        return proposal.to_dict()
    if isinstance(proposal, dict):
        return proposal
    return None


def _one_worker_file_zone_proof_payload(proof: Any) -> dict[str, Any] | None:
    if isinstance(proof, OneWorkerFileZoneProof):
        return proof.to_dict()
    if isinstance(proof, dict):
        return proof
    return None


def _conflict_report_payload(conflict_report: Any) -> dict[str, Any] | None:
    if isinstance(conflict_report, WorkerConflictReport):
        return conflict_report.to_dict()
    if isinstance(conflict_report, dict):
        return conflict_report
    return None


def _ownership_zone_payload(ownership_zone: Any) -> dict[str, Any] | None:
    if isinstance(ownership_zone, WorkerOwnershipZone):
        return ownership_zone.to_dict()
    if isinstance(ownership_zone, dict):
        return ownership_zone
    return None


def _worker_lock_payload(worker_lock: Any) -> dict[str, Any] | None:
    if isinstance(worker_lock, WorkerFileLock):
        return worker_lock.to_dict()
    if isinstance(worker_lock, dict):
        return worker_lock
    return None


def _payload_tuple(
    values: Any,
    dataclass_type: type[Any],
    field: str,
    reasons: list[str],
) -> tuple[dict[str, Any], ...] | None:
    if not isinstance(values, (list, tuple)):
        reasons.append(f"malformed_{field}")
        return None

    payloads: list[dict[str, Any]] = []
    for value in values:
        if isinstance(value, dataclass_type):
            payloads.append(value.to_dict())
        elif isinstance(value, dict):
            payloads.append(value)
        else:
            reasons.append(f"malformed_{field}_entry")
    return tuple(payloads)


def _file_tuple_value(values: Any, field: str, reasons: list[str]) -> tuple[str, ...] | None:
    if not isinstance(values, (list, tuple)):
        reasons.append(f"invalid_{field}")
        return None

    files: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            reasons.append(f"invalid_{field}_entry")
            continue
        path = value.strip()
        if _is_broad_file_scope(path):
            reasons.append(f"broad_{field}_entry")
        files.append(path)
    if len(set(files)) != len(files):
        reasons.append(f"duplicate_{field}_entry")
    return tuple(files)


def _string_tuple_value(values: Any, field: str, reasons: list[str]) -> tuple[str, ...] | None:
    if not isinstance(values, (list, tuple)):
        reasons.append(f"invalid_{field}")
        return None

    items: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            reasons.append(f"invalid_{field}_entry")
            continue
        items.append(value.strip())
    if len(set(items)) != len(items):
        reasons.append(f"duplicate_{field}_entry")
    return tuple(items)


def _ownership_conflict_files(
    candidate_files: tuple[str, ...],
    zone_payloads: tuple[dict[str, Any], ...],
    reasons: list[str],
) -> tuple[str, ...]:
    active_files: set[str] = set()
    duplicate_zone_files: set[str] = set()
    for zone in zone_payloads:
        zone_files = _file_tuple_value(zone.get("files"), "ownership_zone_files", reasons)
        if zone_files is None:
            continue
        for path in zone_files:
            if path in active_files:
                duplicate_zone_files.add(path)
            active_files.add(path)

    conflicts = set(candidate_files).intersection(active_files)
    conflicts.update(duplicate_zone_files)
    return tuple(sorted(conflicts))


def _stale_lock_conflict_files(
    candidate_files: tuple[str, ...],
    lock_payloads: tuple[dict[str, Any], ...],
) -> tuple[str, ...]:
    conflicts: set[str] = set()
    candidate_set = set(candidate_files)
    for lock in lock_payloads:
        if lock.get("status") != "stale" and lock.get("stale") is not True:
            continue
        files = lock.get("files")
        if not isinstance(files, (list, tuple)):
            continue
        lock_files = {path.strip() for path in files if isinstance(path, str) and path.strip()}
        conflicts.update(candidate_set.intersection(lock_files))
    return tuple(sorted(conflicts))


def _stale_or_expired_lock_files(
    lock_payloads: tuple[dict[str, Any], ...],
    current_time: datetime,
) -> tuple[str, ...]:
    files: set[str] = set()
    for lock in lock_payloads:
        if (
            lock.get("status") != "stale"
            and lock.get("stale") is not True
            and not _lock_expired(lock, current_time)
        ):
            continue
        raw_files = lock.get("files")
        if not isinstance(raw_files, (list, tuple)):
            continue
        files.update(path.strip() for path in raw_files if isinstance(path, str) and path.strip())
    return tuple(sorted(files))


def _expired_lease_detected(
    lock_payloads: tuple[dict[str, Any], ...],
    current_time: datetime,
) -> bool:
    return any(_lock_expired(lock, current_time) for lock in lock_payloads)


def _lock_expired(lock: dict[str, Any], current_time: datetime) -> bool:
    value = lock.get("expires_at")
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    if parsed.tzinfo is None:
        return False
    return parsed.astimezone(UTC) <= current_time


def _unsafe_closeout_actions(actions: tuple[str, ...]) -> bool:
    unsafe_tokens = (
        "auto-clean",
        "kill process",
        "delete branch",
        "stash",
        "reset",
        "commit",
        "checkout",
        "push",
    )
    return any(
        token in action.lower()
        for action in actions
        for token in unsafe_tokens
    )


def _string_field(payload: dict[str, Any], field: str, reasons: list[str]) -> str | None:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        reasons.append(f"invalid_{field}")
        return None
    return value.strip()


def _match_string(
    actual: str | None,
    expected: str | None,
    reason: str,
    reasons: list[str],
) -> None:
    if actual and expected and actual != expected:
        reasons.append(reason)


def _optional_string_field(payload: dict[str, Any], field: str, reasons: list[str]) -> str | None:
    value = payload.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        reasons.append(f"invalid_{field}")
        return None
    return value.strip()


def _bool_field(payload: dict[str, Any], field: str, reasons: list[str]) -> bool | None:
    value = payload.get(field)
    if not isinstance(value, bool):
        reasons.append(f"invalid_{field}")
        return None
    return value


def _int_field(payload: dict[str, Any], field: str, reasons: list[str]) -> int | None:
    value = payload.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        reasons.append(f"invalid_{field}")
        return None
    return value


def _exact_file_tuple_field(
    payload: dict[str, Any],
    field: str,
    reasons: list[str],
) -> tuple[str, ...] | None:
    value = payload.get(field)
    if not isinstance(value, (list, tuple)):
        reasons.append(f"invalid_{field}")
        return None

    files: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            reasons.append(f"invalid_{field}_entry")
            continue
        path = item.strip()
        if _is_broad_file_scope(path):
            reasons.append(f"broad_{field}_entry")
        files.append(path)
    if len(set(files)) != len(files):
        reasons.append(f"duplicate_{field}_entry")
    return tuple(files)


def _is_broad_file_scope(path: str) -> bool:
    return (
        path.startswith("/")
        or path.endswith("/")
        or "*" in path
        or "?" in path
        or "[" in path
        or "]" in path
    )


def _protected_worker_path(path: str, protected_file_prefixes: tuple[str, ...]) -> bool:
    return any(path.startswith(prefix) for prefix in protected_file_prefixes)


def _datetime_field(
    payload: dict[str, Any],
    field: str,
    reasons: list[str],
    *,
    required: bool,
) -> datetime | None:
    value = payload.get(field)
    if value is None:
        if required:
            reasons.append(f"invalid_{field}")
        return None
    if not isinstance(value, str) or not value.strip():
        reasons.append(f"invalid_{field}")
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        reasons.append(f"invalid_{field}")
        return None
    if parsed.tzinfo is None:
        reasons.append(f"invalid_{field}")
        return None
    return parsed.astimezone(UTC)


def _dedupe_reasons(reasons: list[str]) -> list[str]:
    return list(dict.fromkeys(reasons))


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
