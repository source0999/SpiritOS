"""Final supplied-data packet for the Agent Factory foundation."""

from __future__ import annotations

from dataclasses import dataclass, field

from source_proxy.agent_factory.contracts import AuthorityFlags, SummaryStatus
from source_proxy.agent_factory.final_readiness import FinalReadinessDecision
from source_proxy.agent_factory.phase_ledger import PhaseLedgerRollup
from source_proxy.agent_factory.verification_manifest import VerificationManifest


@dataclass(frozen=True)
class FoundationPacket:
    """Combined Agent Factory foundation packet. It is report-only."""

    status: SummaryStatus
    phase: int
    decision: str
    ledger_status: SummaryStatus
    verification_command_count: int = 0
    blocked_by: tuple[str, ...] = field(default_factory=tuple)
    cautions: tuple[str, ...] = field(default_factory=tuple)
    authority: AuthorityFlags = field(default_factory=AuthorityFlags)

    @property
    def grants_approval(self) -> bool:
        return False

    @property
    def grants_permission(self) -> bool:
        return False


def build_foundation_packet(
    *,
    phase: int,
    readiness_decision: FinalReadinessDecision,
    phase_ledger: PhaseLedgerRollup,
    verification_manifest: VerificationManifest,
) -> FoundationPacket:
    """Build a deterministic packet from supplied Agent Factory reports."""

    blockers = list(readiness_decision.blockers)
    blockers.extend(phase_ledger.blocked_by)
    cautions = list(readiness_decision.cautions)
    cautions.extend(phase_ledger.cautions)

    if verification_manifest.phase != phase:
        blockers.append("verification_manifest_phase_mismatch")
    if not verification_manifest.commands:
        blockers.append("verification_manifest_empty")

    status = _status(readiness_decision.status, phase_ledger.status, blockers, cautions)
    return FoundationPacket(
        status=status,
        phase=phase,
        decision=readiness_decision.decision,
        ledger_status=phase_ledger.status,
        verification_command_count=len(verification_manifest.commands),
        blocked_by=_dedupe(blockers),
        cautions=_dedupe(cautions),
    )


def format_foundation_packet(packet: FoundationPacket) -> tuple[str, ...]:
    """Format a foundation packet without granting authority."""

    lines = [
        f"Phase: {packet.phase}",
        f"Status: {packet.status}",
        f"Decision: {packet.decision}",
        f"Ledger status: {packet.ledger_status}",
        f"Verification commands: {packet.verification_command_count}",
        "Permission: not granted",
        "Approval: not granted",
    ]
    if packet.blocked_by:
        lines.append(f"Blocked by: {', '.join(packet.blocked_by)}")
    if packet.cautions:
        lines.append(f"Cautions: {' | '.join(packet.cautions)}")
    return tuple(lines)


def _status(
    readiness_status: SummaryStatus,
    ledger_status: SummaryStatus,
    blockers: list[str],
    cautions: list[str],
) -> SummaryStatus:
    if blockers or "BLOCKED" in {readiness_status, ledger_status}:
        return "BLOCKED"
    if cautions or "CAUTION" in {readiness_status, ledger_status}:
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
