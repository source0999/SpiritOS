"""Read-only phase ledger rollup for Agent Factory foundation records."""

from __future__ import annotations

from dataclasses import dataclass, field

from source_proxy.agent_factory.contracts import (
    AuthorityFlags,
    FoundationPhaseRecord,
    SummaryStatus,
)
from source_proxy.agent_factory.foundation_manifest import EXPECTED_FOUNDATION_PHASES


@dataclass(frozen=True)
class PhaseLedgerRollup:
    """Supplied-record ledger rollup. It is not permission."""

    status: SummaryStatus
    expected_phases: tuple[int, ...] = EXPECTED_FOUNDATION_PHASES
    present_phases: tuple[int, ...] = field(default_factory=tuple)
    missing_phases: tuple[int, ...] = field(default_factory=tuple)
    failed_phases: tuple[int, ...] = field(default_factory=tuple)
    duplicate_phases: tuple[int, ...] = field(default_factory=tuple)
    blocked_by: tuple[str, ...] = field(default_factory=tuple)
    cautions: tuple[str, ...] = field(default_factory=tuple)
    authority: AuthorityFlags = field(default_factory=AuthorityFlags)

    @property
    def grants_approval(self) -> bool:
        return False

    @property
    def grants_permission(self) -> bool:
        return False


def build_phase_ledger_rollup(
    records: tuple[FoundationPhaseRecord, ...],
    *,
    expected_phases: tuple[int, ...] = EXPECTED_FOUNDATION_PHASES,
) -> PhaseLedgerRollup:
    """Build a deterministic rollup from supplied phase records only."""

    present = tuple(record.phase for record in records)
    missing = tuple(phase for phase in expected_phases if phase not in present)
    failed = tuple(record.phase for record in records if not record.checks_passed)
    duplicates = _duplicates(present)
    blockers: list[str] = []
    cautions: list[str] = []

    if missing:
        blockers.append("missing_phase_records")
    if failed:
        blockers.append("phase_checks_not_passed")
    if duplicates:
        blockers.append("duplicate_phase_records")

    for record in records:
        if record.blockers:
            cautions.extend(f"Phase {record.phase}: {blocker}" for blocker in record.blockers)
        if record.authority.granted():
            blockers.append(f"Phase {record.phase}: authority_grant_present")

    status: SummaryStatus = "READY"
    if blockers:
        status = "BLOCKED"
    elif cautions:
        status = "CAUTION"

    return PhaseLedgerRollup(
        status=status,
        expected_phases=expected_phases,
        present_phases=present,
        missing_phases=missing,
        failed_phases=failed,
        duplicate_phases=duplicates,
        blocked_by=_dedupe(blockers),
        cautions=_dedupe(cautions),
    )


def format_phase_ledger_rollup(rollup: PhaseLedgerRollup) -> tuple[str, ...]:
    """Format the phase ledger rollup without granting authority."""

    lines = [
        f"Status: {rollup.status}",
        f"Expected phases: {', '.join(str(phase) for phase in rollup.expected_phases)}",
        f"Present phases: {', '.join(str(phase) for phase in rollup.present_phases)}",
        "Permission: not granted",
        "Approval: not granted",
    ]
    if rollup.missing_phases:
        lines.append(f"Missing phases: {', '.join(str(phase) for phase in rollup.missing_phases)}")
    if rollup.failed_phases:
        lines.append(f"Failed phases: {', '.join(str(phase) for phase in rollup.failed_phases)}")
    if rollup.duplicate_phases:
        lines.append(f"Duplicate phases: {', '.join(str(phase) for phase in rollup.duplicate_phases)}")
    if rollup.blocked_by:
        lines.append(f"Blocked by: {', '.join(rollup.blocked_by)}")
    if rollup.cautions:
        lines.append(f"Cautions: {' | '.join(rollup.cautions)}")
    return tuple(lines)


def _duplicates(items: tuple[int, ...]) -> tuple[int, ...]:
    seen: set[int] = set()
    duplicates: list[int] = []
    for item in items:
        if item in seen and item not in duplicates:
            duplicates.append(item)
        seen.add(item)
    return tuple(duplicates)


def _dedupe(items: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return tuple(result)
