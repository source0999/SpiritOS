from __future__ import annotations

import dataclasses


PROTECTED_LANES: tuple[str, ...] = (
    "proxy_ui_makeover",
    "coding_ui_implementation_wiring",
    "source_proxy_stress_testing",
    "codex_adapter_lane",
)


@dataclasses.dataclass(frozen=True)
class CartographerLevel13WorkerRecord:
    worker_id: str
    worker_type: str
    owner: str
    task: str
    run_id: str
    lane: str
    allowed_files: tuple[str, ...]
    forbidden_files: tuple[str, ...]
    status: str
    lease_id: str | None
    stale_after_seconds: int
    closeout_ref: str | None


@dataclasses.dataclass(frozen=True)
class CartographerLevel13WorkerLease:
    lease_id: str
    worker_id: str
    run_id: str
    lane: str
    files: tuple[str, ...]
    status: str
    expires_at: str
    revoked: bool


@dataclasses.dataclass(frozen=True)
class CartographerLevel13OwnershipZone:
    zone_id: str
    owner_worker_id: str
    lane: str
    files: tuple[str, ...]
    mode: str
    protected: bool


@dataclasses.dataclass(frozen=True)
class CartographerLevel13WorkerCheck:
    level: str
    valid_for_dry_run: bool
    worker_dispatch_authority_granted: bool
    branch_worktree_authority_granted: bool
    write_authority_granted: bool
    local_execution_authority_granted: bool
    blocked_reasons: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class CartographerLevel13WorkerPacket:
    level: str
    title: str
    status: str
    mode: str
    would_dispatch_worker: bool
    would_reassign_worker: bool
    would_create_branch: bool
    would_create_worktree: bool
    would_release_lease: bool
    would_release_lock: bool
    would_write_files: bool
    worker_dispatch_authority_granted: bool
    blocked: bool
    blocked_reasons: tuple[str, ...]
    next_increment: str


def validate_level_13_worker_registry_dry_run(
    workers: tuple[CartographerLevel13WorkerRecord, ...],
) -> CartographerLevel13WorkerCheck:
    reasons: list[str] = []
    if not workers:
        reasons += ["missing_workers"]
    if len({worker.worker_id for worker in workers}) != len(workers):
        reasons += ["duplicate_worker_id"]
    for worker in workers:
        reasons += _worker_reasons(worker)
    return _check("13.1", reasons)


def validate_level_13_worker_lease_dry_run(
    worker: CartographerLevel13WorkerRecord,
    lease: CartographerLevel13WorkerLease,
) -> CartographerLevel13WorkerCheck:
    reasons = _worker_reasons(worker)
    if not lease.lease_id:
        reasons += ["missing_lease_id"]
    if lease.worker_id != worker.worker_id:
        reasons += ["lease_worker_mismatch"]
    if lease.run_id != worker.run_id:
        reasons += ["lease_run_mismatch"]
    if lease.lane != worker.lane:
        reasons += ["lease_lane_mismatch"]
    if not set(lease.files).issubset(set(worker.allowed_files)):
        reasons += ["lease_scope_exceeds_worker_scope"]
    if lease.status in ("expired", "stale") or lease.revoked:
        reasons += ["lease_not_active"]
    return _check("13.2", reasons)


def validate_level_13_ownership_zone_dry_run(
    zones: tuple[CartographerLevel13OwnershipZone, ...],
) -> CartographerLevel13WorkerCheck:
    reasons: list[str] = []
    seen_files: set[str] = set()
    for zone in zones:
        if not zone.zone_id:
            reasons += ["missing_zone_id"]
        if zone.lane in PROTECTED_LANES or zone.protected:
            reasons += [f"protected_lane_or_zone:{zone.zone_id}"]
        overlap = seen_files.intersection(zone.files)
        if overlap:
            reasons += [f"overlapping_ownership_zone:{zone.zone_id}"]
        seen_files.update(zone.files)
        if zone.mode not in ("observe", "preview", "dry_run", "approved_mutation"):
            reasons += [f"unsupported_zone_mode:{zone.zone_id}"]
    return _check("13.3", reasons)


def build_level_13_conflict_detection_dry_run_packet(
    *,
    workers: tuple[CartographerLevel13WorkerRecord, ...],
    dirty_files: tuple[str, ...],
    proposed_files: tuple[str, ...],
) -> CartographerLevel13WorkerPacket:
    reasons: list[str] = []
    active_files = {
        path
        for worker in workers
        if worker.status in ("active", "proposed")
        for path in worker.allowed_files
    }
    if set(proposed_files).intersection(active_files):
        reasons += ["active_worker_file_conflict"]
    if set(proposed_files).intersection(dirty_files):
        reasons += ["dirty_worktree_conflict_observed_only"]
    if any(_protected_path(path) for path in proposed_files):
        reasons += ["protected_path_conflict"]
    return _packet(
        level="13.4",
        title="Conflict Detection Dry Run Runtime",
        status="conflict-detection-dry-run-only",
        blocked_reasons=reasons,
        next_increment="Cartographer Level 13.5: Handoff Packet Runtime Dry Run",
    )


def build_level_13_handoff_packet_dry_run(
    *,
    source_worker: CartographerLevel13WorkerRecord,
    target_worker: CartographerLevel13WorkerRecord,
    conflict_report_ref: str | None,
    unresolved_files: tuple[str, ...],
) -> CartographerLevel13WorkerPacket:
    reasons = _worker_reasons(source_worker) + _worker_reasons(target_worker)
    if not conflict_report_ref:
        reasons += ["missing_conflict_report_ref"]
    if source_worker.lane != target_worker.lane:
        reasons += ["handoff_lane_mismatch"]
    if unresolved_files:
        reasons += ["handoff_has_unresolved_files"]
    return _packet(
        level="13.5",
        title="Handoff Packet Runtime Dry Run",
        status="handoff-packet-dry-run-only",
        blocked_reasons=reasons,
        next_increment="Cartographer Level 13.6: Branch Worktree Proposal Queue Dry Run",
    )


def build_level_13_branch_worktree_proposal_dry_run(
    *,
    worker: CartographerLevel13WorkerRecord,
    branch_name: str,
    worktree_path: str,
    existing_names: tuple[str, ...],
    dirty_files: tuple[str, ...],
) -> CartographerLevel13WorkerPacket:
    reasons = _worker_reasons(worker)
    if not branch_name:
        reasons += ["missing_branch_name"]
    if not worktree_path:
        reasons += ["missing_worktree_path"]
    if branch_name in existing_names or worktree_path in existing_names:
        reasons += ["branch_or_worktree_name_collision"]
    if dirty_files:
        reasons += ["dirty_worktree_blocks_branch_worktree_proposal"]
    return _packet(
        level="13.6",
        title="Branch Worktree Proposal Queue Dry Run",
        status="branch-worktree-proposal-dry-run-only",
        blocked_reasons=reasons,
        next_increment="Cartographer Level 13.7: Worker Closeout Packet Runtime Dry Run",
    )


def build_level_13_worker_closeout_packet_dry_run(
    *,
    worker: CartographerLevel13WorkerRecord,
    verification_summary: str | None,
    conflicted: bool,
) -> CartographerLevel13WorkerPacket:
    reasons = _worker_reasons(worker)
    if not verification_summary:
        reasons += ["missing_verification_summary"]
    if conflicted:
        reasons += ["conflicted_worker_requires_review"]
    if worker.status in ("stale", "expired"):
        reasons += ["stale_worker_cannot_close_cleanly"]
    return _packet(
        level="13.7",
        title="Worker Closeout Packet Runtime Dry Run",
        status="worker-closeout-packet-dry-run-only",
        blocked_reasons=reasons,
        next_increment="Cartographer Level 13.8: Stale Worker Handling Dry Run",
    )


def build_level_13_stale_worker_handling_dry_run(
    worker: CartographerLevel13WorkerRecord,
) -> CartographerLevel13WorkerPacket:
    reasons = _worker_reasons(worker)
    if worker.status != "stale":
        reasons += ["worker_not_stale"]
    reasons += ["operator_review_required_for_stale_worker"]
    return _packet(
        level="13.8",
        title="Stale Worker Handling Dry Run",
        status="stale-worker-handling-dry-run-only",
        blocked_reasons=reasons,
        next_increment="Cartographer Level 13.9: Cross-Worker Safety Gate And Level 14 Access Check",
    )


def build_level_13_closeout_level_14_access_check() -> dict[str, object]:
    return {
        "level": "13.9",
        "title": "Cross-Worker Safety Gate And Level 14 Access Check",
        "status": "level-13-runtime-dry-run-closeout",
        "level_14_access": "requires_explicit_human_verification",
        "worker_dispatch_authority_granted": False,
        "worker_orchestration_authority_granted": False,
        "branch_worktree_authority_granted": False,
        "write_authority_granted": False,
        "local_execution_authority_granted": False,
        "commit_push_merge_authority_granted": False,
        "cleanup_authority_granted": False,
        "autonomy_granted": False,
        "protected_lanes_remain_locked": PROTECTED_LANES,
        "next_increment": "Cartographer Level 14.1: Approved Safe Task Queue Runtime Dry Run",
    }


def _worker_reasons(worker: CartographerLevel13WorkerRecord) -> list[str]:
    reasons: list[str] = []
    if not worker.worker_id:
        reasons += ["missing_worker_id"]
    if not worker.owner:
        reasons += ["missing_worker_owner"]
    if not worker.run_id:
        reasons += ["missing_run_id"]
    if worker.lane in PROTECTED_LANES:
        reasons += ["protected_lane_in_scope"]
    if not worker.allowed_files:
        reasons += ["missing_allowed_files"]
    if set(worker.allowed_files).intersection(worker.forbidden_files):
        reasons += ["allowed_files_intersect_forbidden_files"]
    if any(_protected_path(path) for path in worker.allowed_files):
        reasons += ["protected_path_in_scope"]
    if worker.stale_after_seconds < 1:
        reasons += ["invalid_stale_threshold"]
    return reasons


def _protected_path(path: str) -> bool:
    return path.startswith(
        (
            "src/",
            "source_proxy/api/",
            "source_proxy/verification/",
            "source_proxy/codex/",
            "source_proxy/testing/runner.py",
        )
    )


def _check(level: str, blocked_reasons: list[str]) -> CartographerLevel13WorkerCheck:
    return CartographerLevel13WorkerCheck(
        level=level,
        valid_for_dry_run=not blocked_reasons,
        worker_dispatch_authority_granted=False,
        branch_worktree_authority_granted=False,
        write_authority_granted=False,
        local_execution_authority_granted=False,
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
    )


def _packet(
    *,
    level: str,
    title: str,
    status: str,
    blocked_reasons: list[str],
    next_increment: str,
) -> CartographerLevel13WorkerPacket:
    return CartographerLevel13WorkerPacket(
        level=level,
        title=title,
        status=status,
        mode="dry_run",
        would_dispatch_worker=False,
        would_reassign_worker=False,
        would_create_branch=False,
        would_create_worktree=False,
        would_release_lease=False,
        would_release_lock=False,
        would_write_files=False,
        worker_dispatch_authority_granted=False,
        blocked=bool(blocked_reasons),
        blocked_reasons=tuple(dict.fromkeys(blocked_reasons)),
        next_increment=next_increment,
    )
