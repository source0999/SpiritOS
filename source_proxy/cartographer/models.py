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
    "deferred",
    "stale",
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
    confidence: str = "medium"
    reason: str = ""
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
class ClutterCandidate:
    path: str
    risk: Literal["low", "medium", "high", "blocked"]
    reason: str
    confidence: Literal["low", "medium", "high"] = "medium"
    category: str = "unknown"
    deletion_allowed: bool = False
    action_taken: bool = False


@dataclass(frozen=True)
class ClutterDeletionProposal:
    proposal_id: str
    status: Literal["drafted"] = "drafted"
    proposal_type: str = "low_risk_deletion"
    files: list[str] = field(default_factory=list)
    file_count: int = 0
    risk: Literal["low"] = "low"
    reason: str = ""
    confidence: Literal["low", "medium", "high"] = "medium"
    rollback_instructions: list[str] = field(default_factory=list)
    requires_approval: bool = True
    deletion_enabled: bool = False
    action_taken: bool = False


@dataclass(frozen=True)
class TrustScoreSignal:
    code: str
    label: str
    score_delta: int
    evidence: list[str] = field(default_factory=list)
    passed: bool = True


@dataclass(frozen=True)
class V1EvidenceArtifact:
    path: str
    profile: str
    result: str
    generated_at: str | None = None
    clean: bool = False
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class V1EvidenceProof:
    code: str
    required_count: int
    observed_count: int
    passed: bool
    evidence: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class V1ProofGateRecord:
    code: str
    path: str
    check_id: str
    status: str
    passed: bool
    evidence: list[str] = field(default_factory=list)


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
    head_sha: str | None = None
    changed_files: list[str] = field(default_factory=list)
    staged_files: list[str] = field(default_factory=list)
    unstaged_files: list[str] = field(default_factory=list)
    untracked_files: list[str] = field(default_factory=list)
    ahead: int = 0
    behind: int = 0
    upstream: str | None = None
    no_upstream_reason: str | None = None
    generated_at: str | None = None
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
    stale_targets: list[str] = field(default_factory=list)
    why_matters: str = ""
    safe_to_ignore: bool = False
    proposed_next_action: str = ""
    proposal_ids: list[str] = field(default_factory=list)
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
class ChangeScribeFileExplanation:
    path: str
    category: str
    explanation: str
    review_required: bool = False


@dataclass(frozen=True)
class ChangeScribeSummary:
    project_id: str
    summary: str
    branch: str | None = None
    dirty: bool = False
    commit_state: str = "unknown"
    components: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    file_explanations: list[ChangeScribeFileExplanation] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    uncertain_claims: list[str] = field(default_factory=list)
    blueprint_update_detected: bool = False
    drift_detected: bool = False


@dataclass(frozen=True)
class CodexEvidenceRecord:
    task_id: str
    artifact_path: str
    safety_verdict: str
    recommendation: str
    changed_files: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    risk: str = "unknown"
    tests_run: str = "not reported"
    proposal_pending_review: bool = False
    commit_proposal_needed: bool = False
    approval_authority: bool = False
    apply_authority: bool = False
    commit_authority: bool = False
    push_authority: bool = False
    action_taken: bool = False


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
    proposal_only: bool = True
    direct_write_enabled: bool = False
    max_authority: str = "proposal_only"
    review_required: bool = True
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
    allowed_inputs: list[str] = field(default_factory=list)
    allowed_outputs: list[str] = field(default_factory=list)
    max_authority: str = "read_only"
    forbidden_actions: list[str] = field(
        default_factory=lambda: ["approve", "apply", "commit", "push", "delete"]
    )
    can_write_files: bool = False
    can_approve: bool = False
    can_apply: bool = False
    can_commit: bool = False
    can_push: bool = False
    can_delete: bool = False
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
class SubCartographerOutput:
    role_id: str
    summary: str
    evidence: list[str] = field(default_factory=list)
    recommendation: str = ""
    risk: str = "low"
    required_approval: bool = False
    forbidden_actions_respected: bool = True
    next_manual_check: str = ""
    action_taken: bool = False


@dataclass(frozen=True)
class SubCartographerControlRoute:
    route_id: str
    situation: str
    selected_roles: list[str] = field(default_factory=list)
    reason: str = ""
    evidence: list[str] = field(default_factory=list)
    parent_control_plane_required: bool = True
    approval_gate_required: bool = True
    mutation_allowed: bool = False
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
    changed_files: list[str] = field(default_factory=list)
    staged_files: list[str] = field(default_factory=list)
    unstaged_files: list[str] = field(default_factory=list)
    untracked_files: list[str] = field(default_factory=list)
    dirty_file_count: int = 0
    expected_evidence_files: list[str] = field(default_factory=list)
    unsafe_dirty_files: list[str] = field(default_factory=list)
    dirty_summary: str = "clean"
    ahead: int = 0
    behind: int = 0
    upstream: str | None = None
    no_upstream_reason: str | None = None
    merge_ready: bool = False
    merge_blockers: list[str] = field(default_factory=list)
    recommended_next_step: str = "no action needed"
    merge_target: str | None = None
    pushed: bool = False
    head_sha: str | None = None
    commit_audit_status: str = "not_needed"
    unaudited_head_change: bool = False
    push_audit_status: str = "missing"
    push_audit_explanation: str = ""
    push_warning_policy: str = "none"
    bootstrap_push_warning: bool = False
    push_approval_status: str = "not_required"
    push_enabled: bool = False
    push_reason_codes: list[str] = field(default_factory=list)
    commits_to_push: list[str] = field(default_factory=list)
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
    source_head: str | None = None
    dirty_state_requirement: str = "dirty_worktree_required"
    rollback_command: str = ""
    branch_exists: bool = False
    preview_generated: bool = True
    confidence: Literal["low", "medium", "high"] = "medium"
    recommendation: str = "create_branch"
    unsafe_to_create_branch: bool = False
    blockers: list[str] = field(default_factory=list)
    merge_readiness: str = "blocked"
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
    story: str = ""
    group_key: str = ""
    group_reason: str = ""
    files: list[str] = field(default_factory=list)
    included_files: list[str] = field(default_factory=list)
    excluded_files: list[str] = field(default_factory=list)
    reason: str = ""
    component: str = "unknown"
    risk: str = "unknown"
    diff_summary: str = ""
    required_checks: list[str] = field(default_factory=list)
    verification_status: str = "unknown"
    verification_checks: list[dict[str, Any]] = field(default_factory=list)
    audit_state: str = "not_recorded"
    rollback_command: str = ""
    stronger_confirmation_required: bool = False
    commit_blocked: bool = False
    commit_blockers: list[str] = field(default_factory=list)
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
    ahead: int = 0
    behind: int = 0
    commits_ahead: int = 0
    commits_to_push: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    audit_status: str = "missing"
    commit_audit_status: str = "missing"
    test_status: str = "unknown"
    dirty: bool = False
    drift_status: str = "unknown"
    push_command_preview: str = ""
    rollback_guidance: str = ""
    approval_status: str = "approval_required"
    reason_codes: list[str] = field(default_factory=list)
    push_blockers: list[str] = field(default_factory=list)
    branch_protection_warnings: list[str] = field(default_factory=list)
    remote_status: dict[str, Any] = field(default_factory=dict)
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
    previous_branch: str | None = None
    remote: str | None = None
    commit_sha: str | None = None
    parent_sha: str | None = None
    approved_files: list[str] = field(default_factory=list)
    excluded_files: list[str] = field(default_factory=list)
    source_head: str | None = None
    rollback_command: str | None = None
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
    source_drift_id: str | None = None
    review_note: str | None = None
    repo_purpose: str | None = None
    stack_guess: str | None = None
    scripts: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    risk_areas: list[str] = field(default_factory=list)
    suggested_docs: list[str] = field(default_factory=list)
    suggested_tests: list[str] = field(default_factory=list)
    suggested_runbook: list[str] = field(default_factory=list)
    generated: bool = False
    persisted: bool = True
    rejection_reason: str | None = None
    transitions: list[ProposalTransition] = field(default_factory=list)
    applied: bool = False
    action_taken: bool = False
    fingerprint: str | None = None
    deduped: bool = True
    warnings: list[str] = field(default_factory=list)
    post_apply_verification: dict[str, Any] | None = None


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
