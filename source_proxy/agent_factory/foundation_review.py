"""Final read-only review helpers for the Agent Factory foundation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from source_proxy.agent_factory.catalog import CatalogEntry, DEFAULT_AGENT_CATALOG
from source_proxy.agent_factory.contracts import AgentFactorySummary
from source_proxy.agent_factory.dependency_gates import evaluate_catalog_entry
from source_proxy.agent_factory.integrity import (
    audit_catalog_integrity,
    audit_report_authority_integrity,
)
from source_proxy.agent_factory.reporting import compose_agent_factory_summary


def review_agent_factory_foundation(
    *,
    catalog: tuple[CatalogEntry, ...] = DEFAULT_AGENT_CATALOG,
    supplied_gate_status: Mapping[str, Any] | None = None,
) -> AgentFactorySummary:
    """Compose a Phase 6 read-only foundation review from supplied data."""

    gate_status = supplied_gate_status or {}
    catalog_integrity = audit_catalog_integrity(catalog)
    gate_reports = tuple(
        evaluate_catalog_entry(entry, gate_status)
        for entry in catalog
        if entry.dependency_gates
    )
    summary = compose_agent_factory_summary(
        title="Agent Factory Foundation Review",
        lane_reports=(
            catalog_integrity,
            audit_report_authority_integrity(
                lane_reports=(catalog_integrity,),
                gate_reports=gate_reports,
            ),
        ),
        gate_reports=gate_reports,
        catalog_entries=tuple(entry for entry in catalog if not entry.can_run_now),
    )

    return AgentFactorySummary(
        status=summary.status,
        title=summary.title,
        reason_codes=_phase_6_reason_codes(summary.reason_codes),
        blocked_by=summary.blocked_by,
        caution_items=summary.caution_items,
        evidence=summary.evidence,
    )


def format_foundation_review(summary: AgentFactorySummary) -> tuple[str, ...]:
    """Return deterministic Phase 6 lines without granting authority."""

    lines = [
        f"Title: {summary.title}",
        "Phase: 6",
        f"Status: {summary.status}",
        "Foundation: deterministic reports only",
        "Permission: not granted",
        "Approval: not granted",
    ]
    if summary.reason_codes:
        lines.append(f"Reasons: {', '.join(summary.reason_codes)}")
    if summary.blocked_by:
        lines.append(f"Blocked by: {', '.join(summary.blocked_by)}")
    return tuple(lines)


def _phase_6_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if not reason_codes:
        return ("phase_6_foundation_ready",)
    result = ["phase_6_foundation_review"]
    for code in reason_codes:
        if code not in result:
            result.append(code)
    return tuple(result)
