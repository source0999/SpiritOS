"""Operator-facing digest for supplied Agent Factory foundation packets."""

from __future__ import annotations

from dataclasses import dataclass, field

from source_proxy.agent_factory.boundary_snapshot import BoundarySnapshot
from source_proxy.agent_factory.contracts import AuthorityFlags, SummaryStatus
from source_proxy.agent_factory.foundation_packet import FoundationPacket


@dataclass(frozen=True)
class FoundationDigest:
    """Compact supplied-data digest. It is not approval or permission."""

    status: SummaryStatus
    headline: str
    phase: int
    blocked_by: tuple[str, ...] = field(default_factory=tuple)
    cautions: tuple[str, ...] = field(default_factory=tuple)
    evidence_lines: tuple[str, ...] = field(default_factory=tuple)
    authority: AuthorityFlags = field(default_factory=AuthorityFlags)

    @property
    def grants_approval(self) -> bool:
        return False

    @property
    def grants_permission(self) -> bool:
        return False


def build_foundation_digest(
    *,
    phase: int,
    foundation_packet: FoundationPacket,
    boundary_snapshot: BoundarySnapshot,
) -> FoundationDigest:
    """Build a deterministic digest from supplied report objects."""

    blocked_by = _dedupe(list(foundation_packet.blocked_by) + list(boundary_snapshot.blocked_by))
    cautions = _dedupe(list(foundation_packet.cautions) + list(boundary_snapshot.cautions))
    status = _status(foundation_packet.status, boundary_snapshot.status, blocked_by, cautions)
    headline = {
        "READY": "Agent Factory foundation reports ready for operator review.",
        "CAUTION": "Agent Factory foundation reports have cautions for operator review.",
        "BLOCKED": "Agent Factory foundation reports are blocked.",
    }[status]
    evidence_lines = (
        f"Foundation packet status: {foundation_packet.status}",
        f"Boundary snapshot status: {boundary_snapshot.status}",
        f"Verification commands listed: {foundation_packet.verification_command_count}",
        f"Public names checked: {boundary_snapshot.public_name_count}",
    )
    return FoundationDigest(
        status=status,
        headline=headline,
        phase=phase,
        blocked_by=blocked_by,
        cautions=cautions,
        evidence_lines=evidence_lines,
    )


def format_foundation_digest(digest: FoundationDigest) -> tuple[str, ...]:
    """Format the digest without granting authority."""

    lines = [
        f"Phase: {digest.phase}",
        f"Status: {digest.status}",
        f"Headline: {digest.headline}",
        "Permission: not granted",
        "Approval: not granted",
    ]
    lines.extend(digest.evidence_lines)
    if digest.blocked_by:
        lines.append(f"Blocked by: {', '.join(digest.blocked_by)}")
    if digest.cautions:
        lines.append(f"Cautions: {' | '.join(digest.cautions)}")
    return tuple(lines)


def _status(
    packet_status: SummaryStatus,
    boundary_status: SummaryStatus,
    blocked_by: tuple[str, ...],
    cautions: tuple[str, ...],
) -> SummaryStatus:
    if blocked_by or "BLOCKED" in {packet_status, boundary_status}:
        return "BLOCKED"
    if cautions or "CAUTION" in {packet_status, boundary_status}:
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
