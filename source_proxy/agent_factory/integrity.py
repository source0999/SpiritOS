"""Self-contained integrity checks for Agent Factory foundation objects."""

from __future__ import annotations

from source_proxy.agent_factory.catalog import CatalogEntry, DEFAULT_AGENT_CATALOG
from source_proxy.agent_factory.contracts import (
    AgentFactorySummary,
    AuditFinding,
    DependencyGateReport,
    LaneReport,
)
from source_proxy.agent_factory.dependency_gates import REQUIRED_GATES

_KNOWN_GATES = set(REQUIRED_GATES)


def audit_catalog_integrity(
    catalog: tuple[CatalogEntry, ...] = DEFAULT_AGENT_CATALOG,
) -> LaneReport:
    """Check supplied catalog entries for deterministic foundation issues."""

    findings: list[AuditFinding] = []
    seen_names: set[str] = set()

    for entry in catalog:
        if entry.name in seen_names:
            findings.append(
                AuditFinding(
                    rule="duplicate_catalog_name",
                    severity="blocked",
                    subject=entry.name,
                    detail="Catalog entry names must be unique.",
                )
            )
        seen_names.add(entry.name)

        if entry.authority.granted():
            findings.append(
                AuditFinding(
                    rule="catalog_authority_grant",
                    severity="blocked",
                    subject=entry.name,
                    detail=(
                        "Catalog entry carries authority grants: "
                        f"{', '.join(entry.authority.granted())}."
                    ),
                )
            )

        if entry.can_run_now and entry.blocked_by:
            findings.append(
                AuditFinding(
                    rule="catalog_ready_while_blocked",
                    severity="blocked",
                    subject=entry.name,
                    detail="Catalog entry cannot run now while blocked_by is set.",
                )
            )

        for gate in entry.dependency_gates:
            if gate not in _KNOWN_GATES:
                findings.append(
                    AuditFinding(
                        rule="catalog_unknown_dependency_gate",
                        severity="blocked",
                        subject=entry.name,
                        detail=f"Catalog entry references unknown dependency gate: {gate}.",
                    )
                )

    return LaneReport.from_findings(tuple(findings))


def audit_report_authority_integrity(
    *,
    lane_reports: tuple[LaneReport, ...] = (),
    gate_reports: tuple[DependencyGateReport, ...] = (),
    summaries: tuple[AgentFactorySummary, ...] = (),
) -> LaneReport:
    """Check supplied reports for accidental authority grants."""

    findings: list[AuditFinding] = []

    for index, report in enumerate(lane_reports):
        findings.extend(_authority_findings(f"lane_reports[{index}]", report.authority))
    for index, report in enumerate(gate_reports):
        findings.extend(_authority_findings(f"gate_reports[{index}]", report.authority))
    for index, summary in enumerate(summaries):
        findings.extend(_authority_findings(f"summaries[{index}]", summary.authority))

    return LaneReport.from_findings(tuple(findings))


def _authority_findings(subject: str, authority: object) -> list[AuditFinding]:
    granted = getattr(authority, "granted", lambda: ())()
    return [
        AuditFinding(
            rule="report_authority_grant",
            severity="blocked",
            subject=f"{subject}.{name}",
            detail="Supplied report object carries a forbidden authority grant.",
        )
        for name in granted
    ]
