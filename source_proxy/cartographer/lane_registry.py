from __future__ import annotations

import dataclasses
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


LANE_REGISTRY_SCHEMA_VERSION = "cartographer.lane-registry.v0.1"
LANE_REGISTRY_PLAN = "Cartographer Auto Roadmap Plan 3"
LANE_REGISTRY_MODEL_PHASE = "Plan 3 Phase 3.1: Lane vocabulary and registry model"
OWNERSHIP_LOCK_PROPOSAL_PHASE = "Plan 3 Phase 3.2: Ownership locks as data"

LANE_RECORD_STATUSES: tuple[str, ...] = (
    "inactive",
    "active",
    "blocked",
    "stale",
)

DIRTY_OVERLAP_STATUSES: tuple[str, ...] = (
    "clear",
    "caution",
    "blocked",
    "unknown",
    "stale",
)

OWNERSHIP_LOCK_PROPOSAL_STATUSES: tuple[str, ...] = (
    "proposed",
    "active",
    "stale",
    "expired",
    "released",
)

DEFAULT_LANE_IDS: tuple[str, ...] = (
    "cartographer",
    "docs",
    "source_proxy_runtime",
    "coding",
    "dashboard",
    "agent_factory",
    "media",
    "package_config_env",
    "generated_cache",
)

REQUIRED_LANE_RECORD_FIELDS: tuple[str, ...] = (
    "lane_id",
    "owner",
    "allowed_path_prefixes",
    "forbidden_path_prefixes",
    "protected_path_prefixes",
    "status",
    "active",
    "created_at",
)

REQUIRED_OWNERSHIP_LOCK_PROPOSAL_FIELDS: tuple[str, ...] = (
    "lock_id",
    "lease_id",
    "lane_id",
    "owner",
    "scope",
    "exact_paths",
    "status",
    "created_at",
    "expires_at",
)

FALSE_LANE_AUTHORITY: dict[str, bool] = {
    "authority_granted": False,
    "write_actions_enabled": False,
    "lock_enforcement_enabled": False,
    "lock_storage_enabled": False,
    "worker_dispatch_enabled": False,
    "queue_execution_enabled": False,
    "git_mutation_enabled": False,
    "can_mutate": False,
}

_BROAD_PATH_MARKERS = ("*", "?", "[", "]", "{", "}")


@dataclasses.dataclass(frozen=True)
class LaneRegistryRecord:
    lane_id: str
    owner: str
    allowed_path_prefixes: tuple[str, ...]
    forbidden_path_prefixes: tuple[str, ...]
    protected_path_prefixes: tuple[str, ...]
    status: str
    active: bool
    created_at: str
    description: str = ""
    proposal_only: bool = True
    advisory_only: bool = True
    authority_granted: bool = False
    write_actions_enabled: bool = False
    lock_enforcement_enabled: bool = False
    lock_storage_enabled: bool = False
    worker_dispatch_enabled: bool = False
    queue_execution_enabled: bool = False
    git_mutation_enabled: bool = False
    can_mutate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class LaneRegistryValidation:
    status: str
    accepted: bool
    blocked: bool
    reason_codes: tuple[str, ...]
    lane_id: str | None
    owner: str | None
    active: bool
    proposal_only: bool = True
    advisory_only: bool = True
    authority: dict[str, bool] = dataclasses.field(
        default_factory=lambda: dict(FALSE_LANE_AUTHORITY)
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class LaneDirtyOverlap:
    status: str
    blocked: bool
    reason_codes: tuple[str, ...]
    active_lane_id: str | None
    dirty_paths: tuple[str, ...]
    allowed_dirty_paths: tuple[str, ...]
    outside_lane_dirty_paths: tuple[str, ...]
    forbidden_dirty_paths: tuple[str, ...]
    protected_dirty_paths: tuple[str, ...]
    protected_lane_count: int
    proposal_only: bool = True
    advisory_only: bool = True
    authority: dict[str, bool] = dataclasses.field(
        default_factory=lambda: dict(FALSE_LANE_AUTHORITY)
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class OwnershipLockProposal:
    lock_id: str
    lease_id: str
    lane_id: str
    owner: str
    scope: str
    exact_paths: tuple[str, ...]
    status: str
    created_at: str
    expires_at: str
    proposal_only: bool = True
    advisory_only: bool = True
    authority_granted: bool = False
    write_actions_enabled: bool = False
    lock_enforcement_enabled: bool = False
    lock_storage_enabled: bool = False
    worker_dispatch_enabled: bool = False
    queue_execution_enabled: bool = False
    git_mutation_enabled: bool = False
    can_mutate: bool = False

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class OwnershipLockProposalValidation:
    status: str
    accepted: bool
    blocked: bool
    reason_codes: tuple[str, ...]
    lock_id: str | None
    lease_id: str | None
    lane_id: str | None
    owner: str | None
    exact_paths: tuple[str, ...]
    dirty_overlap_status: str | None
    proposal_only: bool = True
    advisory_only: bool = True
    authority: dict[str, bool] = dataclasses.field(
        default_factory=lambda: dict(FALSE_LANE_AUTHORITY)
    )

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def build_lane_registry_model_status() -> dict[str, Any]:
    return {
        "schema_version": LANE_REGISTRY_SCHEMA_VERSION,
        "plan": LANE_REGISTRY_PLAN,
        "phase": LANE_REGISTRY_MODEL_PHASE,
        "status": "model-only",
        "lane_ids": DEFAULT_LANE_IDS,
        "lane_record_statuses": LANE_RECORD_STATUSES,
        "dirty_overlap_statuses": DIRTY_OVERLAP_STATUSES,
        "required_lane_record_fields": REQUIRED_LANE_RECORD_FIELDS,
        "proposal_only": True,
        "advisory_only": True,
        "authority": dict(FALSE_LANE_AUTHORITY),
        "safe_next_action": (
            "Use lane records for display and proposal checks only; require a "
            "later approved plan before enforcing locks or mutating state."
        ),
    }


def build_ownership_lock_proposal_status() -> dict[str, Any]:
    return {
        "schema_version": LANE_REGISTRY_SCHEMA_VERSION,
        "plan": LANE_REGISTRY_PLAN,
        "phase": OWNERSHIP_LOCK_PROPOSAL_PHASE,
        "status": "proposal-only",
        "ownership_lock_statuses": OWNERSHIP_LOCK_PROPOSAL_STATUSES,
        "required_ownership_lock_proposal_fields": REQUIRED_OWNERSHIP_LOCK_PROPOSAL_FIELDS,
        "proposal_only": True,
        "advisory_only": True,
        "authority": dict(FALSE_LANE_AUTHORITY),
        "safe_next_action": (
            "Display ownership lock proposals only; require a later approved "
            "plan before storing locks, enforcing locks, dispatching workers, "
            "or mutating files."
        ),
    }


def build_default_lane_registry(
    *,
    active_lane_id: str = "cartographer",
    created_at: str = "2026-05-24T00:00:00Z",
) -> tuple[LaneRegistryRecord, ...]:
    lanes = [
        _lane(
            lane_id="cartographer",
            owner="cartographer",
            allowed=(
                "source_proxy/cartographer/",
                "source_proxy/tests/test_cartographer_",
                "src/app/map/",
            ),
            forbidden=(
                "src/app/coding/",
                "src/components/coding/",
                "source_proxy/agent_factory/",
                "public/media/",
                "package.json",
                "package-lock.json",
                "next.config.ts",
                "next-env.d.ts",
                "allowed-dev-origins.ts",
                "docs/plan-index.md",
            ),
            protected=(
                "src/app/coding/",
                "src/components/coding/",
                "source_proxy/agent_factory/",
                "public/media/",
                "package.json",
                "package-lock.json",
                "next.config.ts",
                "next-env.d.ts",
                "allowed-dev-origins.ts",
                ".next",
                ".next/",
            ),
            active_lane_id=active_lane_id,
            created_at=created_at,
            description="Cartographer runtime, truth-source, lane registry, and /map display work.",
        ),
        _lane(
            lane_id="docs",
            owner="britton",
            allowed=("docs/",),
            forbidden=(
                "docs/plan-index.md",
                "source_proxy/",
                "src/",
                "public/media/",
                "package.json",
                "next.config.ts",
            ),
            protected=("docs/plan-index.md",),
            active_lane_id=active_lane_id,
            created_at=created_at,
            description="Docs-only planning and closeout notes.",
        ),
        _lane(
            lane_id="source_proxy_runtime",
            owner="source_proxy",
            allowed=("source_proxy/",),
            forbidden=(
                "src/app/coding/",
                "src/components/coding/",
                "public/media/",
                "package.json",
                "next.config.ts",
            ),
            protected=(
                "source_proxy/api/",
                "source_proxy/codex/",
                "source_proxy/tasks/",
            ),
            active_lane_id=active_lane_id,
            created_at=created_at,
            description="Source Proxy backend/runtime lane.",
        ),
        _lane(
            lane_id="coding",
            owner="coding",
            allowed=("src/app/coding/", "src/components/coding/", "src/lib/coding/"),
            forbidden=("source_proxy/", "public/media/", "package.json", "next.config.ts"),
            protected=("source_proxy/", "package.json", "next.config.ts"),
            active_lane_id=active_lane_id,
            created_at=created_at,
            description="/coding frontend and coding helper lane.",
        ),
        _lane(
            lane_id="dashboard",
            owner="dashboard",
            allowed=("src/components/dashboard/", "src/app/(dashboard)/", "src/styles/"),
            forbidden=("source_proxy/", "src/app/coding/", "public/media/", "package.json"),
            protected=("source_proxy/", "src/app/coding/", "public/media/"),
            active_lane_id=active_lane_id,
            created_at=created_at,
            description="Dashboard and shared shell lane.",
        ),
        _lane(
            lane_id="agent_factory",
            owner="agent_factory",
            allowed=("source_proxy/agent_factory/", "source_proxy/tests/test_agent_factory_"),
            forbidden=("src/app/coding/", "public/media/", "package.json", "next.config.ts"),
            protected=("src/app/coding/", "public/media/", "package.json"),
            active_lane_id=active_lane_id,
            created_at=created_at,
            description="Agent Factory contracts, tests, and advisory helpers.",
        ),
        _lane(
            lane_id="media",
            owner="media",
            allowed=("src/app/media/", "src/components/media/", "src/lib/media/", "public/media/"),
            forbidden=("source_proxy/", "src/app/coding/", "package.json", "next.config.ts"),
            protected=("source_proxy/", "src/app/coding/", "package.json", "next.config.ts"),
            active_lane_id=active_lane_id,
            created_at=created_at,
            description="Media app and media assets lane.",
        ),
        _lane(
            lane_id="package_config_env",
            owner="britton",
            allowed=("package.json", "package-lock.json", "next.config.ts", "config/", ".env"),
            forbidden=("source_proxy/", "src/", "public/media/"),
            protected=("package.json", "package-lock.json", "next.config.ts", "config/", ".env"),
            active_lane_id=active_lane_id,
            created_at=created_at,
            description="Package, config, and environment lane.",
        ),
        _lane(
            lane_id="generated_cache",
            owner="generated",
            allowed=(".next/", ".next.backup"),
            forbidden=("source_proxy/", "src/", "docs/", "public/media/"),
            protected=(".next/", ".next.backup"),
            active_lane_id=active_lane_id,
            created_at=created_at,
            description="Generated and cache artifacts, display-only for this plan.",
        ),
    ]
    return tuple(lanes)


def classify_lane_dirty_overlap(
    truth_packet: Mapping[str, Any] | None,
    active_lane: LaneRegistryRecord | Mapping[str, Any],
) -> LaneDirtyOverlap:
    lane_validation = validate_lane_registry_record(active_lane)
    lane_payload = active_lane.to_dict() if isinstance(active_lane, LaneRegistryRecord) else active_lane
    lane_id = lane_validation.lane_id
    if not lane_validation.accepted or not isinstance(lane_payload, Mapping):
        return _dirty_overlap(
            status="unknown",
            reason_codes=("lane_registry_record_invalid", *lane_validation.reason_codes),
            active_lane_id=lane_id,
        )

    if not isinstance(truth_packet, Mapping):
        return _dirty_overlap(
            status="unknown",
            reason_codes=("truth_packet_missing",),
            active_lane_id=lane_id,
        )
    if truth_packet.get("schema_version") != "cartographer.truth-packet.v0.1":
        return _dirty_overlap(
            status="unknown",
            reason_codes=("truth_packet_malformed",),
            active_lane_id=lane_id,
        )

    packet_status = _string_value(truth_packet.get("status")) or "unknown"
    unknown_fields = _string_tuple(truth_packet.get("unknown_fields"))
    stale_fields = _string_tuple(truth_packet.get("stale_fields"))
    if packet_status == "stale" or stale_fields:
        return _dirty_overlap(
            status="stale",
            reason_codes=("truth_packet_stale",),
            active_lane_id=lane_id,
        )
    if packet_status in {"unknown", "no_go"} or unknown_fields:
        return _dirty_overlap(
            status="unknown",
            reason_codes=("truth_packet_unknown",),
            active_lane_id=lane_id,
        )

    facts = truth_packet.get("facts")
    if not isinstance(facts, Mapping):
        return _dirty_overlap(
            status="unknown",
            reason_codes=("truth_packet_facts_missing",),
            active_lane_id=lane_id,
        )

    dirty_paths = _dirty_paths_from_truth_packet(truth_packet, facts)
    total_dirty_count = _int_value(facts.get("total_dirty_count"))
    protected_lane_count = _int_value(facts.get("protected_lane_count"))
    protected_match_paths = _protected_paths_from_truth_packet(truth_packet, facts)

    if total_dirty_count > 0 and not dirty_paths:
        return _dirty_overlap(
            status="unknown",
            reason_codes=("dirty_paths_missing",),
            active_lane_id=lane_id,
            protected_lane_count=protected_lane_count,
        )
    if protected_lane_count > 0 and not protected_match_paths:
        return _dirty_overlap(
            status="blocked",
            reason_codes=("protected_paths_unknown",),
            active_lane_id=lane_id,
            dirty_paths=dirty_paths,
            protected_lane_count=protected_lane_count,
        )

    allowed_prefixes = _string_tuple(lane_payload.get("allowed_path_prefixes"))
    forbidden_prefixes = _string_tuple(lane_payload.get("forbidden_path_prefixes"))
    protected_prefixes = _string_tuple(lane_payload.get("protected_path_prefixes"))
    allowed_dirty_paths = tuple(
        path for path in dirty_paths if _matches_any_prefix(path, allowed_prefixes)
    )
    outside_lane_dirty_paths = tuple(
        path for path in dirty_paths if not _matches_any_prefix(path, allowed_prefixes)
    )
    forbidden_dirty_paths = tuple(
        path for path in dirty_paths if _matches_any_prefix(path, forbidden_prefixes)
    )
    protected_dirty_paths = tuple(
        dict.fromkeys(
            path
            for path in (*dirty_paths, *protected_match_paths)
            if _matches_any_prefix(path, protected_prefixes)
            or path in protected_match_paths
        )
    )

    if forbidden_dirty_paths or protected_dirty_paths or protected_lane_count > 0:
        reason_codes = tuple(
            code
            for code, paths in (
                ("dirty_forbidden_path_overlap", forbidden_dirty_paths),
                ("dirty_protected_zone_overlap", protected_dirty_paths),
                ("protected_lane_matches_present", protected_match_paths),
            )
            if paths
        ) or ("protected_lane_matches_present",)
        return _dirty_overlap(
            status="blocked",
            reason_codes=reason_codes,
            active_lane_id=lane_id,
            dirty_paths=dirty_paths,
            allowed_dirty_paths=allowed_dirty_paths,
            outside_lane_dirty_paths=outside_lane_dirty_paths,
            forbidden_dirty_paths=forbidden_dirty_paths,
            protected_dirty_paths=protected_dirty_paths,
            protected_lane_count=protected_lane_count,
        )

    if outside_lane_dirty_paths:
        return _dirty_overlap(
            status="caution",
            reason_codes=("dirty_paths_outside_active_lane",),
            active_lane_id=lane_id,
            dirty_paths=dirty_paths,
            allowed_dirty_paths=allowed_dirty_paths,
            outside_lane_dirty_paths=outside_lane_dirty_paths,
            protected_lane_count=protected_lane_count,
        )

    return _dirty_overlap(
        status="clear",
        reason_codes=(),
        active_lane_id=lane_id,
        dirty_paths=dirty_paths,
        allowed_dirty_paths=allowed_dirty_paths,
        protected_lane_count=protected_lane_count,
    )


def validate_ownership_lock_proposal(
    proposal: OwnershipLockProposal | Mapping[str, Any],
    active_lane: LaneRegistryRecord | Mapping[str, Any],
    dirty_overlap: LaneDirtyOverlap | Mapping[str, Any],
    *,
    now: str,
) -> OwnershipLockProposalValidation:
    payload = proposal.to_dict() if isinstance(proposal, OwnershipLockProposal) else proposal
    lane_payload = active_lane.to_dict() if isinstance(active_lane, LaneRegistryRecord) else active_lane
    overlap_payload = dirty_overlap.to_dict() if isinstance(dirty_overlap, LaneDirtyOverlap) else dirty_overlap
    if not isinstance(payload, Mapping):
        return _lock_validation(
            accepted=False,
            reason_codes=("ownership_lock_proposal_malformed",),
            lock_id=None,
            lease_id=None,
            lane_id=None,
            owner=None,
            exact_paths=(),
            dirty_overlap_status=None,
        )

    reasons: list[str] = []
    for field in REQUIRED_OWNERSHIP_LOCK_PROPOSAL_FIELDS:
        if field not in payload:
            reasons.append(f"missing_required_field:{field}")

    lane_validation = validate_lane_registry_record(active_lane)
    if not lane_validation.accepted or not isinstance(lane_payload, Mapping):
        reasons.append("lane_registry_record_invalid")
    elif not lane_validation.active:
        reasons.append("active_lane_required")

    lock_id = _string_value(payload.get("lock_id"))
    lease_id = _string_value(payload.get("lease_id"))
    lane_id = _string_value(payload.get("lane_id"))
    owner = _string_value(payload.get("owner"))
    scope = _string_value(payload.get("scope"))
    status = _string_value(payload.get("status"))
    exact_paths = _string_tuple(payload.get("exact_paths"))
    expires_at = _string_value(payload.get("expires_at"))

    if lock_id is None:
        reasons.append("missing_lock_id")
    if lease_id is None:
        reasons.append("missing_lease_id")
    if lane_id is None:
        reasons.append("missing_lane_id")
    if owner is None:
        reasons.append("missing_owner")
    if scope is None:
        reasons.append("missing_scope")
    if status not in OWNERSHIP_LOCK_PROPOSAL_STATUSES:
        reasons.append("unknown_lock_status")
    if status in {"stale", "expired", "released"}:
        reasons.append(f"lock_status_not_acquirable:{status}")
    if lane_validation.lane_id and lane_id != lane_validation.lane_id:
        reasons.append("lock_lane_mismatch")
    if lane_validation.owner and owner != lane_validation.owner:
        reasons.append("lock_owner_mismatch")
    if not exact_paths:
        reasons.append("missing_exact_paths")

    allowed_prefixes = _string_tuple(lane_payload.get("allowed_path_prefixes")) if isinstance(lane_payload, Mapping) else ()
    forbidden_prefixes = _string_tuple(lane_payload.get("forbidden_path_prefixes")) if isinstance(lane_payload, Mapping) else ()
    protected_prefixes = _string_tuple(lane_payload.get("protected_path_prefixes")) if isinstance(lane_payload, Mapping) else ()
    seen_paths: set[str] = set()
    for path in exact_paths:
        if path in seen_paths:
            reasons.append("duplicate_exact_path")
        seen_paths.add(path)
        if not _safe_exact_path(path):
            reasons.append(f"unsafe_exact_path:{path}")
        if not _matches_any_prefix(path, allowed_prefixes):
            reasons.append(f"path_outside_active_lane:{path}")
        if _matches_any_prefix(path, forbidden_prefixes):
            reasons.append(f"path_forbidden:{path}")
        if _matches_any_prefix(path, protected_prefixes):
            reasons.append(f"path_protected:{path}")

    if not isinstance(overlap_payload, Mapping):
        dirty_overlap_status = None
        reasons.append("dirty_overlap_missing")
    else:
        dirty_overlap_status = _string_value(overlap_payload.get("status"))
        if dirty_overlap_status != "clear":
            reasons.append("dirty_overlap_not_clear")
        if overlap_payload.get("blocked") is True:
            reasons.append("dirty_overlap_blocked")

    if _is_expired(expires_at, now):
        reasons.append("lock_expired")
    if payload.get("proposal_only") is False:
        reasons.append("lock_must_be_proposal_only")
    if payload.get("advisory_only") is False:
        reasons.append("lock_must_be_advisory_only")
    for authority_name in FALSE_LANE_AUTHORITY:
        if payload.get(authority_name) is True:
            reasons.append(f"authority_must_be_false:{authority_name}")

    return _lock_validation(
        accepted=not reasons,
        reason_codes=tuple(dict.fromkeys(reasons)),
        lock_id=lock_id,
        lease_id=lease_id,
        lane_id=lane_id,
        owner=owner,
        exact_paths=exact_paths,
        dirty_overlap_status=dirty_overlap_status,
    )


def validate_lane_registry_record(record: LaneRegistryRecord | Mapping[str, Any]) -> LaneRegistryValidation:
    payload = record.to_dict() if isinstance(record, LaneRegistryRecord) else record
    if not isinstance(payload, Mapping):
        return _lane_validation(
            accepted=False,
            reason_codes=("lane_record_malformed",),
            lane_id=None,
            owner=None,
            active=False,
        )

    reasons: list[str] = []
    for field in REQUIRED_LANE_RECORD_FIELDS:
        if field not in payload:
            reasons.append(f"missing_required_field:{field}")

    lane_id = _string_value(payload.get("lane_id"))
    owner = _string_value(payload.get("owner"))
    allowed = _string_tuple(payload.get("allowed_path_prefixes"))
    forbidden = _string_tuple(payload.get("forbidden_path_prefixes"))
    protected = _string_tuple(payload.get("protected_path_prefixes"))
    status = _string_value(payload.get("status"))
    active = payload.get("active")

    if lane_id not in DEFAULT_LANE_IDS:
        reasons.append("unknown_lane_id")
    if owner is None:
        reasons.append("missing_lane_owner")
    if status not in LANE_RECORD_STATUSES:
        reasons.append("unknown_lane_status")
    if not isinstance(active, bool):
        reasons.append("invalid_active_state")
        active_bool = False
    else:
        active_bool = active
    if status == "active" and not active_bool:
        reasons.append("active_status_requires_active_true")
    if active_bool and status != "active":
        reasons.append("active_true_requires_active_status")

    _validate_prefixes("allowed_path_prefixes", allowed, reasons)
    _validate_prefixes("forbidden_path_prefixes", forbidden, reasons)
    _validate_prefixes("protected_path_prefixes", protected, reasons)
    if not allowed:
        reasons.append("missing_allowed_path_prefixes")
    if not forbidden:
        reasons.append("missing_forbidden_path_prefixes")
    if not protected:
        reasons.append("missing_protected_path_prefixes")
    if _prefix_sets_intersect(allowed, forbidden):
        reasons.append("allowed_forbidden_path_overlap")
    if payload.get("proposal_only") is False:
        reasons.append("lane_record_must_be_proposal_only")
    if payload.get("advisory_only") is False:
        reasons.append("lane_record_must_be_advisory_only")
    for authority_name in FALSE_LANE_AUTHORITY:
        if payload.get(authority_name) is True:
            reasons.append(f"authority_must_be_false:{authority_name}")

    return _lane_validation(
        accepted=not reasons,
        reason_codes=tuple(dict.fromkeys(reasons)),
        lane_id=lane_id,
        owner=owner,
        active=active_bool,
    )


def _lane(
    *,
    lane_id: str,
    owner: str,
    allowed: Sequence[str],
    forbidden: Sequence[str],
    protected: Sequence[str],
    active_lane_id: str,
    created_at: str,
    description: str,
) -> LaneRegistryRecord:
    active = lane_id == active_lane_id
    return LaneRegistryRecord(
        lane_id=lane_id,
        owner=owner,
        allowed_path_prefixes=tuple(allowed),
        forbidden_path_prefixes=tuple(forbidden),
        protected_path_prefixes=tuple(protected),
        status="active" if active else "inactive",
        active=active,
        created_at=created_at,
        description=description,
    )


def _lane_validation(
    *,
    accepted: bool,
    reason_codes: Sequence[str],
    lane_id: str | None,
    owner: str | None,
    active: bool,
) -> LaneRegistryValidation:
    return LaneRegistryValidation(
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reason_codes=tuple(reason_codes),
        lane_id=lane_id,
        owner=owner,
        active=active,
    )


def _dirty_overlap(
    *,
    status: str,
    reason_codes: Sequence[str],
    active_lane_id: str | None,
    dirty_paths: Sequence[str] = (),
    allowed_dirty_paths: Sequence[str] = (),
    outside_lane_dirty_paths: Sequence[str] = (),
    forbidden_dirty_paths: Sequence[str] = (),
    protected_dirty_paths: Sequence[str] = (),
    protected_lane_count: int = 0,
) -> LaneDirtyOverlap:
    return LaneDirtyOverlap(
        status=status,
        blocked=status in {"blocked", "unknown", "stale"},
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        active_lane_id=active_lane_id,
        dirty_paths=tuple(dirty_paths),
        allowed_dirty_paths=tuple(allowed_dirty_paths),
        outside_lane_dirty_paths=tuple(outside_lane_dirty_paths),
        forbidden_dirty_paths=tuple(forbidden_dirty_paths),
        protected_dirty_paths=tuple(protected_dirty_paths),
        protected_lane_count=protected_lane_count,
    )


def _lock_validation(
    *,
    accepted: bool,
    reason_codes: Sequence[str],
    lock_id: str | None,
    lease_id: str | None,
    lane_id: str | None,
    owner: str | None,
    exact_paths: Sequence[str],
    dirty_overlap_status: str | None,
) -> OwnershipLockProposalValidation:
    return OwnershipLockProposalValidation(
        status="accepted" if accepted else "blocked",
        accepted=accepted,
        blocked=not accepted,
        reason_codes=tuple(reason_codes),
        lock_id=lock_id,
        lease_id=lease_id,
        lane_id=lane_id,
        owner=owner,
        exact_paths=tuple(exact_paths),
        dirty_overlap_status=dirty_overlap_status,
    )


def _dirty_paths_from_truth_packet(
    truth_packet: Mapping[str, Any],
    facts: Mapping[str, Any],
) -> tuple[str, ...]:
    paths: list[str] = []
    for value in (
        facts.get("dirty_paths"),
        facts.get("tracked_dirty_files"),
        facts.get("untracked_files"),
        truth_packet.get("dirty_paths"),
        truth_packet.get("tracked_dirty_files"),
        truth_packet.get("untracked_files"),
    ):
        paths.extend(_string_tuple(value))
    return tuple(dict.fromkeys(paths))


def _protected_paths_from_truth_packet(
    truth_packet: Mapping[str, Any],
    facts: Mapping[str, Any],
) -> tuple[str, ...]:
    paths: list[str] = []
    for value in (
        facts.get("protected_lane_matches"),
        truth_packet.get("protected_lane_matches"),
    ):
        paths.extend(_paths_from_match_records(value))
    return tuple(dict.fromkeys(paths))


def _paths_from_match_records(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    paths: list[str] = []
    for item in value:
        if isinstance(item, Mapping):
            path = _string_value(item.get("path"))
            if path:
                paths.append(path)
    return tuple(paths)


def _matches_any_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path == prefix or path.startswith(prefix) for prefix in prefixes)


def _validate_prefixes(
    field_name: str,
    values: tuple[str, ...],
    reasons: list[str],
) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            reasons.append(f"duplicate_{field_name}")
        seen.add(value)
        if not _safe_path_prefix(value):
            reasons.append(f"unsafe_{field_name}:{value}")


def _safe_path_prefix(value: str) -> bool:
    if not value or value.startswith("/") or "\\" in value:
        return False
    if ".." in value.split("/"):
        return False
    return not any(marker in value for marker in _BROAD_PATH_MARKERS)


def _safe_exact_path(value: str) -> bool:
    if not _safe_path_prefix(value):
        return False
    return not value.endswith("/")


def _prefix_sets_intersect(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    return bool(set(left).intersection(right))


def _string_value(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _string_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item.strip())


def _int_value(value: Any) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


def _is_expired(expires_at: str | None, now: str) -> bool:
    expires_at_timestamp = _parse_utc_timestamp(expires_at)
    now_timestamp = _parse_utc_timestamp(now)
    if expires_at_timestamp is None or now_timestamp is None:
        return True
    return expires_at_timestamp <= now_timestamp


def _parse_utc_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.removesuffix("Z") + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)
