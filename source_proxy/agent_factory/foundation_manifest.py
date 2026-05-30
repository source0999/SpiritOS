"""Completion manifest checks for the Agent Factory foundation."""

from __future__ import annotations

from source_proxy.agent_factory.contracts import (
    AuditFinding,
    FoundationPhaseRecord,
    LaneReport,
)


EXPECTED_FOUNDATION_PHASES: tuple[int, ...] = tuple(range(1, 16))


def build_foundation_phase_record(
    *,
    phase: int,
    title: str,
    checks_passed: bool,
    blockers: tuple[str, ...] = (),
) -> FoundationPhaseRecord:
    """Build an inert supplied phase record."""

    return FoundationPhaseRecord(
        phase=phase,
        title=title,
        closeout_doc=f"docs/agent-ecosystem-plan-1-phase-{phase}-closeout-v0.1.md",
        checks_passed=checks_passed,
        blockers=blockers,
    )


def audit_foundation_manifest(
    records: tuple[FoundationPhaseRecord, ...],
    *,
    expected_phases: tuple[int, ...] = EXPECTED_FOUNDATION_PHASES,
) -> LaneReport:
    """Validate supplied phase records without reading files."""

    findings: list[AuditFinding] = []
    phases = tuple(record.phase for record in records)
    seen: set[int] = set()

    for phase in phases:
        if phase in seen:
            findings.append(
                AuditFinding(
                    rule="duplicate_phase_record",
                    severity="blocked",
                    subject=f"Phase {phase}",
                    detail="Foundation manifest contains a duplicate phase record.",
                )
            )
        seen.add(phase)

    for phase in expected_phases:
        if phase not in seen:
            findings.append(
                AuditFinding(
                    rule="missing_phase_record",
                    severity="blocked",
                    subject=f"Phase {phase}",
                    detail="Foundation manifest is missing an expected phase record.",
                )
            )

    for record in records:
        expected_doc = f"docs/agent-ecosystem-plan-1-phase-{record.phase}-closeout-v0.1.md"
        if record.closeout_doc != expected_doc:
            findings.append(
                AuditFinding(
                    rule="phase_closeout_doc_mismatch",
                    severity="blocked",
                    subject=f"Phase {record.phase}",
                    detail=f"Expected closeout doc {expected_doc}.",
                )
            )
        if not record.checks_passed:
            findings.append(
                AuditFinding(
                    rule="phase_checks_not_passed",
                    severity="blocked",
                    subject=f"Phase {record.phase}",
                    detail="Supplied phase record does not show checks passed.",
                )
            )
        if record.blockers:
            findings.append(
                AuditFinding(
                    rule="phase_blockers_present",
                    severity="caution",
                    subject=f"Phase {record.phase}",
                    detail=", ".join(record.blockers),
                )
            )
        for grant in record.authority.granted():
            findings.append(
                AuditFinding(
                    rule="phase_authority_grant",
                    severity="blocked",
                    subject=f"Phase {record.phase}.{grant}",
                    detail="Supplied phase record carries a forbidden authority grant.",
                )
            )

    return LaneReport.from_findings(tuple(findings))


def format_foundation_manifest(records: tuple[FoundationPhaseRecord, ...]) -> tuple[str, ...]:
    """Format supplied phase records without granting authority."""

    lines = ("Phase | Checks | Closeout",)
    for record in records:
        checks = "passed" if record.checks_passed else "not passed"
        lines += (f"Phase {record.phase} | {checks} | {record.closeout_doc}",)
    lines += ("Permission: not granted", "Approval: not granted")
    return lines
