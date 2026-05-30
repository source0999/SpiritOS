"""Read-only runtime boundary snapshot for Agent Factory."""

from __future__ import annotations

from dataclasses import dataclass, field

from source_proxy.agent_factory.authority_invariants import audit_public_name_invariants
from source_proxy.agent_factory.contracts import AuthorityFlags, SummaryStatus
from source_proxy.agent_factory.foundation_packet import FoundationPacket
from source_proxy.agent_factory.phase_ledger import PhaseLedgerRollup


@dataclass(frozen=True)
class BoundarySnapshot:
    """Supplied-data boundary snapshot. It grants nothing."""

    status: SummaryStatus
    public_name_count: int = 0
    packet_status: SummaryStatus = "BLOCKED"
    ledger_status: SummaryStatus = "BLOCKED"
    blocked_by: tuple[str, ...] = field(default_factory=tuple)
    cautions: tuple[str, ...] = field(default_factory=tuple)
    authority: AuthorityFlags = field(default_factory=AuthorityFlags)

    @property
    def grants_approval(self) -> bool:
        return False

    @property
    def grants_permission(self) -> bool:
        return False


def build_boundary_snapshot(
    *,
    public_names: tuple[str, ...],
    foundation_packet: FoundationPacket,
    phase_ledger: PhaseLedgerRollup,
) -> BoundarySnapshot:
    """Build a deterministic boundary snapshot from supplied objects."""

    name_report = audit_public_name_invariants(public_names)
    blockers = list(foundation_packet.blocked_by)
    blockers.extend(phase_ledger.blocked_by)
    cautions = list(foundation_packet.cautions)
    cautions.extend(phase_ledger.cautions)

    if name_report.status == "blocked":
        blockers.extend(finding.subject for finding in name_report.findings)
    elif name_report.status == "caution":
        cautions.extend(finding.subject for finding in name_report.findings)

    status = _status(
        foundation_packet.status,
        phase_ledger.status,
        name_report.status,
        blockers,
        cautions,
    )
    return BoundarySnapshot(
        status=status,
        public_name_count=len(public_names),
        packet_status=foundation_packet.status,
        ledger_status=phase_ledger.status,
        blocked_by=_dedupe(blockers),
        cautions=_dedupe(cautions),
    )


def format_boundary_snapshot(snapshot: BoundarySnapshot) -> tuple[str, ...]:
    """Format a runtime boundary snapshot without granting authority."""

    lines = [
        f"Status: {snapshot.status}",
        f"Public names: {snapshot.public_name_count}",
        f"Foundation packet: {snapshot.packet_status}",
        f"Phase ledger: {snapshot.ledger_status}",
        "Permission: not granted",
        "Approval: not granted",
    ]
    if snapshot.blocked_by:
        lines.append(f"Blocked by: {', '.join(snapshot.blocked_by)}")
    if snapshot.cautions:
        lines.append(f"Cautions: {' | '.join(snapshot.cautions)}")
    return tuple(lines)


def _status(
    packet_status: SummaryStatus,
    ledger_status: SummaryStatus,
    name_status: str,
    blockers: list[str],
    cautions: list[str],
) -> SummaryStatus:
    if blockers or "BLOCKED" in {packet_status, ledger_status, name_status.upper()}:
        return "BLOCKED"
    if cautions or "CAUTION" in {packet_status, ledger_status, name_status.upper()}:
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
