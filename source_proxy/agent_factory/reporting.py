"""Read-only report composition for Agent Factory outputs."""

from __future__ import annotations

from source_proxy.agent_factory.catalog import CatalogEntry
from source_proxy.agent_factory.contracts import (
    AgentFactorySummary,
    DependencyGateReport,
    EvidenceReference,
    LaneReport,
    SummaryStatus,
)


def compose_agent_factory_summary(
    *,
    title: str,
    lane_reports: tuple[LaneReport, ...] = (),
    gate_reports: tuple[DependencyGateReport, ...] = (),
    catalog_entries: tuple[CatalogEntry, ...] = (),
) -> AgentFactorySummary:
    """Compose a read-only summary from supplied reports."""

    reason_codes: list[str] = []
    blocked_by: list[str] = []
    caution_items: list[str] = []
    evidence: list[EvidenceReference] = []

    for report in lane_reports:
        if report.status == "blocked":
            reason_codes.append("lane_report_blocked")
        elif report.status == "caution":
            reason_codes.append("lane_report_caution")
        for finding in report.findings:
            evidence.append(finding.evidence)
            if finding.severity == "blocked":
                blocked_by.append(finding.subject)
            else:
                caution_items.append(finding.subject)

    for report in gate_reports:
        reason_codes.extend(report.reason_codes)
        if report.status == "BLOCKED":
            blocked_by.extend(report.blocked_by)
        elif report.status == "CAUTION":
            caution_items.extend(report.blocked_by)

    for entry in catalog_entries:
        if not entry.can_run_now:
            reason_codes.append(f"catalog_blocked:{entry.plan}")
            blocked_by.extend(entry.blocked_by)

    return AgentFactorySummary(
        status=_summary_status(lane_reports, gate_reports, blocked_by, caution_items),
        title=title,
        reason_codes=_dedupe(reason_codes),
        blocked_by=_dedupe(blocked_by),
        caution_items=_dedupe(caution_items),
        evidence=tuple(evidence),
    )


def format_summary_lines(summary: AgentFactorySummary) -> tuple[str, ...]:
    """Return deterministic display lines without implying permission."""

    lines = [
        f"Title: {summary.title}",
        f"Status: {summary.status}",
        "Permission: not granted",
        "Approval: not granted",
    ]
    if summary.reason_codes:
        lines.append(f"Reasons: {', '.join(summary.reason_codes)}")
    if summary.blocked_by:
        lines.append(f"Blocked by: {', '.join(summary.blocked_by)}")
    if summary.caution_items:
        lines.append(f"Cautions: {', '.join(summary.caution_items)}")
    return tuple(lines)


def _summary_status(
    lane_reports: tuple[LaneReport, ...],
    gate_reports: tuple[DependencyGateReport, ...],
    blocked_by: list[str],
    caution_items: list[str],
) -> SummaryStatus:
    if blocked_by:
        return "BLOCKED"
    if caution_items:
        return "CAUTION"
    if any(report.status == "blocked" for report in lane_reports):
        return "BLOCKED"
    if any(report.status == "caution" for report in lane_reports):
        return "CAUTION"
    if any(report.status == "BLOCKED" for report in gate_reports):
        return "BLOCKED"
    if any(report.status == "CAUTION" for report in gate_reports):
        return "CAUTION"
    return "READY"


def _dedupe(items: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return tuple(result)
