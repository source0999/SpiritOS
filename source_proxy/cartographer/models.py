from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


WritePolicy = Literal["read_only"]
ProposalStatus = Literal[
    "detected",
    "drafted",
    "pending_review",
    "approved",
    "rejected",
    "applied",
    "commit_pending",
    "commit_approved",
    "push_pending",
    "push_approved",
    "pushed",
    "failed",
]


@dataclass(frozen=True)
class ConfiguredRoot:
    path: str
    status: Literal["configured", "unavailable", "blocked"]
    source: str = "SPIRIT_PROJECT_PATH"
    reason: str | None = None


@dataclass(frozen=True)
class CartographerProject:
    project_id: str
    name: str
    root: str
    markers: list[str] = field(default_factory=list)
    has_blueprints: bool = False
    blueprint_root: str | None = None
    status: Literal["detected"] = "detected"
    write_policy: WritePolicy = "read_only"
    source_root: str | None = None


@dataclass(frozen=True)
class ProjectCandidate:
    candidate_id: str
    project_id: str
    name: str
    root: str
    markers: list[str] = field(default_factory=list)
    status: Literal["new_project_candidate"] = "new_project_candidate"
    approval_status: Literal["needs_approval"] = "needs_approval"
    source_root: str | None = None
    action_taken: bool = False


@dataclass(frozen=True)
class BlueprintRecord:
    blueprint_id: str
    title: str
    project_id: str
    path: str
    component: str
    doc_type: str
    status: str
    source_of_truth: bool
    code_paths: list[str] = field(default_factory=list)
    related_blueprints: list[str] = field(default_factory=list)
    write_policy: str = "proposal_only_until_dashboard_approved"
    last_verified: str | None = None
    index_classification: str | None = None
    used_for_drift: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ComponentMapping:
    component_id: str
    label: str
    paths: list[str] = field(default_factory=list)
    blueprint_id: str | None = None
    matched_paths: list[str] = field(default_factory=list)
    risk: str = "low"
    matched_path_risks: dict[str, str] = field(default_factory=dict)
    sandbox: bool = False


@dataclass(frozen=True)
class UnmappedPath:
    path: str
    reason: str = "no_component_mapping_rule"
    risk: str = "unknown"


@dataclass(frozen=True)
class RepoMapFile:
    path: str
    component_id: str | None = None
    blueprint_id: str | None = None
    risk: str = "unknown"
    symbols: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RepoMapSummary:
    project_id: str
    map_version: int
    scan_duration_ms: int
    files_seen: int
    files_indexed: int
    symbols_indexed: int
    max_files: int
    max_symbols: int
    component_counts: dict[str, int] = field(default_factory=dict)
    risk_counts: dict[str, int] = field(default_factory=dict)
    key_directories: list[str] = field(default_factory=list)
    api_routes: list[str] = field(default_factory=list)
    dashboard_widgets: list[str] = field(default_factory=list)
    tests: list[str] = field(default_factory=list)
    blueprints: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    files: list[RepoMapFile] = field(default_factory=list)
    unmapped_paths: list[UnmappedPath] = field(default_factory=list)


@dataclass(frozen=True)
class GitStatus:
    project_id: str | None = None
    root: str | None = None
    available: bool = False
    dirty: bool = False
    branch: str | None = None
    changed_files: list[str] = field(default_factory=list)
    staged_files: list[str] = field(default_factory=list)
    unstaged_files: list[str] = field(default_factory=list)
    untracked_files: list[str] = field(default_factory=list)
    ahead: int = 0
    behind: int = 0
    upstream: str | None = None
    is_primary_branch: bool = False
    needs_branch_recommendation: bool = False
    needs_commit: bool = False
    needs_push: bool = False
    merge_ready: bool = False
    write_mode: str = "locked"
    last_commit: dict[str, str] | None = None
    error: str | None = None


@dataclass(frozen=True)
class DriftFinding:
    project_id: str
    drift_id: str
    component: str
    reason: str
    affected_blueprints: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    message: str = ""
    evidence: list[str] = field(default_factory=list)
    severity: Literal["info", "review_suggested", "action_recommended"] = "review_suggested"
    status: Literal["open"] = "open"
    dismissible: bool = True
    proposal_generated: bool = False


@dataclass(frozen=True)
class CartographerReminder:
    reminder_id: str
    project_id: str
    kind: str
    message: str
    reason: str
    severity: Literal["info", "review_suggested", "action_recommended"] = "review_suggested"
    dismissible: bool = True
    action_taken: bool = False
    changed_file_count: int = 0
    suggested_branch: str | None = None
    related_files: list[str] = field(default_factory=list)
    related_drift: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChangeScribeSummary:
    project_id: str
    summary: str
    branch: str | None = None
    dirty: bool = False
    commit_state: str = "unknown"
    components: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    uncertain_claims: list[str] = field(default_factory=list)
    blueprint_update_detected: bool = False
    drift_detected: bool = False


@dataclass(frozen=True)
class BlueprintScribeDraft:
    proposal_id: str
    project_id: str
    component: str
    affected_blueprint: str
    proposed_file: str
    suggested_update: str
    confidence: Literal["low", "medium", "high"] = "medium"
    reason: str = ""
    evidence: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    avoids_overclaiming: list[str] = field(default_factory=list)
    editable: bool = True
    rejectable: bool = True
    requires_apply_approval: bool = True
    action_taken: bool = False


@dataclass(frozen=True)
class RunbookScribeSuggestion:
    suggestion_id: str
    project_id: str
    component: str
    target_runbook: str
    reason: str
    changed_files: list[str] = field(default_factory=list)
    checklist_items: list[str] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    editable: bool = True
    rejectable: bool = True
    action_taken: bool = False


@dataclass(frozen=True)
class SubCartographerRole:
    role_id: str
    label: str
    responsibility: str
    consumes: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)
    can_write_files: bool = False
    failure_policy: str = "stop_at_proposal_queue"


@dataclass(frozen=True)
class SubCartographerRoute:
    route_id: str
    project_id: str
    proposal_id: str
    contributors: list[str] = field(default_factory=list)
    visible_outputs: list[str] = field(default_factory=list)
    status: str = "proposal_queue"
    failures_stop_at: str = "proposal_queue"
    action_taken: bool = False


@dataclass(frozen=True)
class ProjectHealth:
    project_id: str
    name: str
    root: str
    status: str
    blueprint_health: str
    blueprint_count: int = 0
    pending_drift: int = 0
    pending_proposals: int = 0
    dirty: bool = False
    branch: str | None = None
    merge_ready: bool = False
    merge_blockers: list[str] = field(default_factory=list)
    recommended_next_step: str = "no action needed"
    merge_target: str | None = None
    pushed: bool = False
    checks_passed: bool = False
    markers: list[str] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)
    action_taken: bool = False


@dataclass(frozen=True)
class BranchRecommendation:
    recommendation_id: str
    project_id: str
    current_branch: str | None
    suggested_branch: str
    reason: str
    changed_file_count: int = 0
    related_files: list[str] = field(default_factory=list)
    status: Literal["pending_approval"] = "pending_approval"
    requires_approval: bool = True
    branch_creation_enabled: bool = False
    action_taken: bool = False


@dataclass(frozen=True)
class CommitProposal:
    commit_proposal_id: str
    project_id: str
    source_proposal_id: str
    status: Literal["commit_pending"] = "commit_pending"
    suggested_message: str = ""
    files: list[str] = field(default_factory=list)
    reason: str = ""
    component: str = "unknown"
    risk: str = "unknown"
    generated: bool = False
    staged_files: list[str] = field(default_factory=list)
    unstaged_files: list[str] = field(default_factory=list)
    untracked_files: list[str] = field(default_factory=list)
    editable: bool = True
    requires_approval: bool = True
    commit_enabled: bool = False
    action_taken: bool = False


@dataclass(frozen=True)
class PushQueueItem:
    push_id: str
    project_id: str
    remote: str
    branch: str
    upstream: str | None = None
    commits_ahead: int = 0
    files: list[str] = field(default_factory=list)
    status: Literal["push_pending"] = "push_pending"
    requires_approval: bool = True
    push_enabled: bool = False
    action_taken: bool = False


@dataclass(frozen=True)
class AuditTrailEvent:
    event_id: str
    project_id: str
    event: str
    action: str | None = None
    actor: str | None = None
    timestamp: str | None = None
    proposal_id: str | None = None
    task_id: str | None = None
    component: str | None = None
    reason: str | None = None
    result: str | None = None
    files: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    branch: str | None = None
    remote: str | None = None
    commit_sha: str | None = None
    rollback_hint: str | None = None
    source: str = "cartographer"


@dataclass(frozen=True)
class ProposalTransition:
    status: ProposalStatus | str
    timestamp: str | None
    actor: str | None


@dataclass(frozen=True)
class ProposalRecord:
    proposal_id: str
    project_id: str
    status: ProposalStatus | str
    type: str
    component: str
    requires_approval: bool = True
    title: str | None = None
    affected_blueprints: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    proposed_files: list[str] = field(default_factory=list)
    approved_diff: str | None = None
    diff_preview: str | None = None
    confidence: str | None = None
    rationale: str | None = None
    generated: bool = False
    persisted: bool = True
    rejection_reason: str | None = None
    transitions: list[ProposalTransition] = field(default_factory=list)
    applied: bool = False
    action_taken: bool = False
    fingerprint: str | None = None
    deduped: bool = True
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CartographerStatus:
    status: Literal["observing"]
    write_actions_enabled: bool
    configured_roots: list[ConfiguredRoot] = field(default_factory=list)
    blocked_roots: list[ConfiguredRoot] = field(default_factory=list)
    projects: list[CartographerProject] = field(default_factory=list)
    blueprint_count: int = 0
    pending_proposals: int = 0


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value
