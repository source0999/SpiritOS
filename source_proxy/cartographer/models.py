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
    status: Literal["detected"] = "detected"
    write_policy: WritePolicy = "read_only"
    source_root: str | None = None


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
    sandbox: bool = False


@dataclass(frozen=True)
class UnmappedPath:
    path: str
    reason: str = "no_component_mapping_rule"


@dataclass(frozen=True)
class RepoMapFile:
    path: str
    component_id: str | None = None
    blueprint_id: str | None = None
    symbols: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RepoMapSummary:
    project_id: str
    map_version: int
    files_seen: int
    files_indexed: int
    symbols_indexed: int
    max_files: int
    max_symbols: int
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
    rejection_reason: str | None = None
    transitions: list[ProposalTransition] = field(default_factory=list)
    applied: bool = False
    action_taken: bool = False
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
