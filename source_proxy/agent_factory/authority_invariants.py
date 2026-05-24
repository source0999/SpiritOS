"""Final authority invariants for the Agent Factory foundation."""

from __future__ import annotations

from source_proxy.agent_factory.contracts import (
    AgentFactorySummary,
    AuditFinding,
    AuthorityFlags,
    DependencyGateReport,
    FoundationPhaseRecord,
    LaneReport,
    ReadinessMatrixRow,
)

FORBIDDEN_PUBLIC_NAME_TOKENS: tuple[str, ...] = (
    "apply",
    "approve",
    "approval_token",
    "command_runner",
    "commit",
    "execute",
    "push",
    "queue_runner",
    "self_approve",
    "workflow_runner",
    "worktree",
)


def audit_public_name_invariants(public_names: tuple[str, ...]) -> LaneReport:
    """Flag public names that imply blocked runtime authority."""

    findings: list[AuditFinding] = []
    for name in public_names:
        normalized = name.lower()
        for token in FORBIDDEN_PUBLIC_NAME_TOKENS:
            if token in normalized:
                findings.append(
                    AuditFinding(
                        rule="public_name_implies_forbidden_authority",
                        severity="blocked",
                        subject=name,
                        detail=f"Public name contains blocked authority token: {token}.",
                    )
                )
    return LaneReport.from_findings(tuple(findings))


def audit_authority_invariants(
    *,
    flags: tuple[AuthorityFlags, ...] = (),
    lane_reports: tuple[LaneReport, ...] = (),
    gate_reports: tuple[DependencyGateReport, ...] = (),
    summaries: tuple[AgentFactorySummary, ...] = (),
    readiness_rows: tuple[ReadinessMatrixRow, ...] = (),
    phase_records: tuple[FoundationPhaseRecord, ...] = (),
) -> LaneReport:
    """Check supplied Agent Factory objects for authority grants."""

    findings: list[AuditFinding] = []
    for index, authority in enumerate(flags):
        findings.extend(_authority_findings(f"flags[{index}]", authority))
    for index, report in enumerate(lane_reports):
        findings.extend(_authority_findings(f"lane_reports[{index}]", report.authority))
    for index, report in enumerate(gate_reports):
        findings.extend(_authority_findings(f"gate_reports[{index}]", report.authority))
    for index, summary in enumerate(summaries):
        findings.extend(_authority_findings(f"summaries[{index}]", summary.authority))
    for index, row in enumerate(readiness_rows):
        findings.extend(_authority_findings(f"readiness_rows[{index}]", row.authority))
    for index, record in enumerate(phase_records):
        findings.extend(_authority_findings(f"phase_records[{index}]", record.authority))
    return LaneReport.from_findings(tuple(findings))


def _authority_findings(subject: str, authority: AuthorityFlags) -> list[AuditFinding]:
    return [
        AuditFinding(
            rule="authority_invariant_grant",
            severity="blocked",
            subject=f"{subject}.{name}",
            detail="Supplied Agent Factory object carries a forbidden authority grant.",
        )
        for name in authority.granted()
    ]
