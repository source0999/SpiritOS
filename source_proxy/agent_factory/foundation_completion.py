"""Completion gate composition for the Agent Factory foundation."""

from __future__ import annotations

from source_proxy.agent_factory.contracts import AgentFactorySummary, LaneReport
from source_proxy.agent_factory.reporting import compose_agent_factory_summary


def evaluate_foundation_completion(
    *,
    manifest_report: LaneReport,
    api_report: LaneReport,
    authority_report: LaneReport,
) -> AgentFactorySummary:
    """Compose a deterministic completion gate from supplied reports."""

    summary = compose_agent_factory_summary(
        title="Agent Factory Foundation Completion Gate",
        lane_reports=(manifest_report, api_report, authority_report),
    )
    reason_codes = summary.reason_codes or ("phase_11_completion_ready",)
    return AgentFactorySummary(
        status=summary.status,
        title=summary.title,
        reason_codes=reason_codes,
        blocked_by=summary.blocked_by,
        caution_items=summary.caution_items,
        evidence=summary.evidence,
    )


def format_foundation_completion(summary: AgentFactorySummary) -> tuple[str, ...]:
    """Format completion gate lines without granting authority."""

    lines = [
        f"Title: {summary.title}",
        "Phase: 11",
        f"Status: {summary.status}",
        "Plan 1 foundation: report-only",
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
