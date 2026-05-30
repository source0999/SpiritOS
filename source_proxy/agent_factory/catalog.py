"""Default Agent Factory sub-agent catalog."""

from __future__ import annotations

from dataclasses import dataclass, field

from source_proxy.agent_factory.contracts import AuthorityFlags


FORBIDDEN_AUTHORITY: tuple[str, ...] = (
    "approval",
    "apply",
    "write",
    "command_execution",
    "workflow_execution",
    "queue_execution",
    "commit",
    "push",
    "branch_worktree",
    "self_approval",
    "background_autonomy",
)


@dataclass(frozen=True)
class CatalogEntry:
    """Static catalog entry. It describes gates; it does not grant authority."""

    name: str
    purpose: str
    plan: str
    earliest_safe_start: str
    dependency_gates: tuple[str, ...]
    allowed_mode: str
    forbidden_authority: tuple[str, ...] = FORBIDDEN_AUTHORITY
    can_run_now: bool = False
    blocked_by: tuple[str, ...] = field(default_factory=tuple)
    authority: AuthorityFlags = field(default_factory=AuthorityFlags)

    @property
    def grants_permission(self) -> bool:
        return False


DEFAULT_AGENT_CATALOG: tuple[CatalogEntry, ...] = (
    CatalogEntry(
        name="Agent Factory Runtime Foundation",
        purpose="Provide deterministic Agent Factory contracts, audits, lane checks, catalog data, and dependency gate reports.",
        plan="Plan 1",
        earliest_safe_start="Now, after explicit Plan 1 phase approval.",
        dependency_gates=(),
        allowed_mode="deterministic_runtime_foundation",
        can_run_now=True,
    ),
    CatalogEntry(
        name="Proxy-Dependent Proposal Helpers",
        purpose="Future tester, reviewer, receipt, and handoff proposal helpers that depend on Proxy apply/verify/receipt stability.",
        plan="Plan 2",
        earliest_safe_start="After Source Proxy apply/verify/receipt loop is stable.",
        dependency_gates=("proxy_apply_verify_receipt_ready",),
        allowed_mode="blocked_future_proposal_only",
        blocked_by=("proxy_apply_verify_receipt_ready",),
    ),
    CatalogEntry(
        name="Cartographer Read-Only Context Helpers",
        purpose="Future read-only context pack and lane-state helpers that depend on Cartographer live state and approval-token boundary proof.",
        plan="Plan 3",
        earliest_safe_start="After Cartographer live state and approval-token boundary are stable.",
        dependency_gates=(
            "cartographer_live_state_ready",
            "cartographer_approval_token_boundary_ready",
        ),
        allowed_mode="blocked_future_read_only",
        blocked_by=(
            "cartographer_live_state_ready",
            "cartographer_approval_token_boundary_ready",
        ),
    ),
    CatalogEntry(
        name="Safe-Write and Verification Dependent Helpers",
        purpose="Future scaffold proposal and verification-planning helpers that depend on safe-write and verification runner proof.",
        plan="Plan 4",
        earliest_safe_start="After Cartographer safe writes and verification runner are stable.",
        dependency_gates=(
            "cartographer_safe_write_ready",
            "cartographer_verification_runner_ready",
        ),
        allowed_mode="blocked_future_proposal_only",
        blocked_by=(
            "cartographer_safe_write_ready",
            "cartographer_verification_runner_ready",
        ),
    ),
    CatalogEntry(
        name="Workflow Queue and Worker Coordination Helpers",
        purpose="Future worker registry, ownership, stale closeout, and one-worker-one-task helpers.",
        plan="Plan 5",
        earliest_safe_start="After durable workflow queue and worker coordination are proven.",
        dependency_gates=(
            "cartographer_workflow_queue_ready",
            "cartographer_worker_coordination_ready",
        ),
        allowed_mode="blocked_future_worker_coordination",
        blocked_by=(
            "cartographer_workflow_queue_ready",
            "cartographer_worker_coordination_ready",
        ),
    ),
    CatalogEntry(
        name="Design Agent Stack",
        purpose="Future design source-rights, vault, reverse designer, blender, pack, and visual-verification helpers.",
        plan="Plan 6",
        earliest_safe_start="After Agent Factory foundation and design source-rights boundary are approved.",
        dependency_gates=(),
        allowed_mode="blocked_future_design_proposal_only",
        blocked_by=("design_source_rights_boundary",),
    ),
    CatalogEntry(
        name="Scout Helper Stack",
        purpose="Future Scout intake, trust classification, design bridge, and recommendation helpers.",
        plan="Plan 7",
        earliest_safe_start="After Scout review flow and Agent Factory contracts are stable.",
        dependency_gates=(),
        allowed_mode="blocked_future_advisory_only",
        blocked_by=("scout_review_flow",),
    ),
    CatalogEntry(
        name="Oracle and Chat Helper Polish",
        purpose="Future tool-honesty, task clarity, and memory/tool-boundary polish helpers.",
        plan="Plan 8",
        earliest_safe_start="After Proxy and Cartographer daily-driver patterns are stable enough to reuse.",
        dependency_gates=("proxy_cartographer_daily_driver_ready",),
        allowed_mode="blocked_future_advisory_only",
        blocked_by=("proxy_cartographer_daily_driver_ready",),
    ),
    CatalogEntry(
        name="Multi-Agent Orchestration and Future Autonomy",
        purpose="Future leases, handoffs, dashboard, branch/worktree proposals, and later release steward helpers.",
        plan="Plan 9",
        earliest_safe_start="After Worker Registry, safe queue, and repeated soak proof.",
        dependency_gates=(
            "cartographer_workflow_queue_ready",
            "cartographer_worker_coordination_ready",
        ),
        allowed_mode="blocked_future_orchestration_proposal_only",
        blocked_by=(
            "cartographer_workflow_queue_ready",
            "cartographer_worker_coordination_ready",
            "repeated_soak_proof",
        ),
    ),
)


def get_default_catalog() -> tuple[CatalogEntry, ...]:
    return DEFAULT_AGENT_CATALOG


def get_catalog_entry(name: str) -> CatalogEntry | None:
    for entry in DEFAULT_AGENT_CATALOG:
        if entry.name == name:
            return entry
    return None
