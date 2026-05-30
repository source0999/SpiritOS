"""Fail-closed contracts for Agent Factory runtime checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ReportStatus = Literal["clear", "caution", "blocked"]
FindingSeverity = Literal["caution", "blocked"]
GateStatus = Literal["READY", "BLOCKED", "CAUTION"]
SummaryStatus = Literal["READY", "BLOCKED", "CAUTION"]


@dataclass(frozen=True)
class AuthorityFlags:
    """Authority flags default to no authority."""

    approval: bool = False
    apply: bool = False
    write: bool = False
    command_execution: bool = False
    workflow_execution: bool = False
    queue_execution: bool = False
    commit: bool = False
    push: bool = False
    branch_worktree: bool = False
    self_approval: bool = False
    background_autonomy: bool = False

    def granted(self) -> tuple[str, ...]:
        return tuple(
            name
            for name, value in (
                ("approval", self.approval),
                ("apply", self.apply),
                ("write", self.write),
                ("command_execution", self.command_execution),
                ("workflow_execution", self.workflow_execution),
                ("queue_execution", self.queue_execution),
                ("commit", self.commit),
                ("push", self.push),
                ("branch_worktree", self.branch_worktree),
                ("self_approval", self.self_approval),
                ("background_autonomy", self.background_autonomy),
            )
            if value
        )

    @property
    def is_fail_closed(self) -> bool:
        return not self.granted()


@dataclass(frozen=True)
class LaneScope:
    """Declared file lane for deterministic checks over supplied paths."""

    allowed_files: tuple[str, ...] = field(default_factory=tuple)
    forbidden_files: tuple[str, ...] = field(default_factory=tuple)
    file_families: dict[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceReference:
    """Stable evidence pointer. It does not claim verification was run."""

    file: str = ""
    source: str = ""
    rule: str = ""
    detail: str = ""
    verification_run: bool = False


@dataclass(frozen=True)
class AuditFinding:
    """A single deterministic finding. It is evidence, not permission."""

    rule: str
    severity: FindingSeverity
    subject: str
    detail: str
    evidence: EvidenceReference = field(default_factory=EvidenceReference)


@dataclass(frozen=True)
class LaneReport:
    """Report returned by Agent Factory checks."""

    status: ReportStatus = "clear"
    findings: tuple[AuditFinding, ...] = field(default_factory=tuple)
    authority: AuthorityFlags = field(default_factory=AuthorityFlags)

    @classmethod
    def from_findings(cls, findings: tuple[AuditFinding, ...]) -> "LaneReport":
        if any(finding.severity == "blocked" for finding in findings):
            status: ReportStatus = "blocked"
        elif findings:
            status = "caution"
        else:
            status = "clear"
        return cls(status=status, findings=findings)

    @property
    def grants_permission(self) -> bool:
        return False


@dataclass(frozen=True)
class DependencyGateReport:
    """Gate evaluation over supplied data only."""

    status: GateStatus = "BLOCKED"
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    blocked_by: tuple[str, ...] = field(default_factory=tuple)
    authority: AuthorityFlags = field(default_factory=AuthorityFlags)

    @property
    def grants_approval(self) -> bool:
        return False

    @property
    def grants_permission(self) -> bool:
        return False


@dataclass(frozen=True)
class AgentFactorySummary:
    """Read-only composed summary from supplied Agent Factory reports."""

    status: SummaryStatus = "BLOCKED"
    title: str = ""
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    blocked_by: tuple[str, ...] = field(default_factory=tuple)
    caution_items: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[EvidenceReference, ...] = field(default_factory=tuple)
    authority: AuthorityFlags = field(default_factory=AuthorityFlags)

    @property
    def grants_approval(self) -> bool:
        return False

    @property
    def grants_permission(self) -> bool:
        return False


@dataclass(frozen=True)
class ReadinessMatrixRow:
    """Read-only catalog readiness row."""

    plan: str
    name: str
    status: GateStatus
    allowed_mode: str
    required_gates: tuple[str, ...] = field(default_factory=tuple)
    blocked_by: tuple[str, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    authority: AuthorityFlags = field(default_factory=AuthorityFlags)

    @property
    def grants_approval(self) -> bool:
        return False

    @property
    def grants_permission(self) -> bool:
        return False


@dataclass(frozen=True)
class FoundationPhaseRecord:
    """Supplied completion record for one Agent Factory foundation phase."""

    phase: int
    title: str
    closeout_doc: str
    checks_passed: bool = False
    blockers: tuple[str, ...] = field(default_factory=tuple)
    authority: AuthorityFlags = field(default_factory=AuthorityFlags)

    @property
    def grants_approval(self) -> bool:
        return False

    @property
    def grants_permission(self) -> bool:
        return False


@dataclass(frozen=True)
class OperatorSummaryPacket:
    """Read-only operator packet for Agent Factory foundation status."""

    phase: int
    status: SummaryStatus
    headline: str
    blockers: tuple[str, ...] = field(default_factory=tuple)
    cautions: tuple[str, ...] = field(default_factory=tuple)
    next_steps: tuple[str, ...] = field(default_factory=tuple)
    authority: AuthorityFlags = field(default_factory=AuthorityFlags)

    @property
    def grants_approval(self) -> bool:
        return False

    @property
    def grants_permission(self) -> bool:
        return False
