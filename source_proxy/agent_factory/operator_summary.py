"""Read-only operator summary packet for Agent Factory."""

from __future__ import annotations

from source_proxy.agent_factory.contracts import (
    AgentFactorySummary,
    OperatorSummaryPacket,
    ReadinessMatrixRow,
)
from source_proxy.agent_factory.verification_manifest import VerificationManifest


def build_operator_summary_packet(
    *,
    phase: int,
    completion_summary: AgentFactorySummary,
    readiness_rows: tuple[ReadinessMatrixRow, ...] = (),
    verification_manifest: VerificationManifest | None = None,
) -> OperatorSummaryPacket:
    """Build a deterministic operator packet from supplied reports."""

    blockers = list(completion_summary.blocked_by)
    cautions = list(completion_summary.caution_items)
    for row in readiness_rows:
        if row.status == "BLOCKED":
            blockers.extend(row.blocked_by or (row.name,))
        elif row.status == "CAUTION":
            cautions.extend(row.blocked_by or (row.name,))

    next_steps = ["Review blocked dependency gates before future helper work."]
    if verification_manifest is not None:
        next_steps.append("Run the manual verification manifest commands.")

    return OperatorSummaryPacket(
        phase=phase,
        status=completion_summary.status,
        headline=completion_summary.title,
        blockers=_dedupe(blockers),
        cautions=_dedupe(cautions),
        next_steps=tuple(next_steps),
    )


def format_operator_summary_packet(packet: OperatorSummaryPacket) -> tuple[str, ...]:
    """Format an operator packet without granting authority."""

    lines = [
        f"Phase: {packet.phase}",
        f"Status: {packet.status}",
        f"Headline: {packet.headline}",
        "Permission: not granted",
        "Approval: not granted",
    ]
    if packet.blockers:
        lines.append(f"Blockers: {', '.join(packet.blockers)}")
    if packet.cautions:
        lines.append(f"Cautions: {', '.join(packet.cautions)}")
    if packet.next_steps:
        lines.append(f"Next steps: {' | '.join(packet.next_steps)}")
    return tuple(lines)


def _dedupe(items: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return tuple(result)
