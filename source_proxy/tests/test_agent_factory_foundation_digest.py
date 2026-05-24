from dataclasses import replace

from source_proxy.agent_factory.boundary_snapshot import BoundarySnapshot
from source_proxy.agent_factory.foundation_digest import (
    build_foundation_digest,
    format_foundation_digest,
)
from source_proxy.agent_factory.foundation_packet import FoundationPacket


def _packet():
    return FoundationPacket(
        status="READY",
        phase=20,
        decision="agent_factory_foundation_ready_for_operator_review",
        ledger_status="READY",
        verification_command_count=3,
    )


def _snapshot():
    return BoundarySnapshot(
        status="READY",
        public_name_count=58,
        packet_status="READY",
        ledger_status="READY",
    )


def test_phase_20_digest_ready_for_ready_supplied_reports():
    digest = build_foundation_digest(
        phase=20,
        foundation_packet=_packet(),
        boundary_snapshot=_snapshot(),
    )

    assert digest.status == "READY"
    assert digest.phase == 20
    assert digest.grants_permission is False
    assert "Verification commands listed: 3" in digest.evidence_lines


def test_phase_20_digest_blocks_when_packet_blocks():
    packet = replace(_packet(), status="BLOCKED", blocked_by=("packet_blocker",))

    digest = build_foundation_digest(
        phase=20,
        foundation_packet=packet,
        boundary_snapshot=_snapshot(),
    )

    assert digest.status == "BLOCKED"
    assert digest.blocked_by == ("packet_blocker",)


def test_phase_20_digest_blocks_when_boundary_blocks():
    snapshot = replace(_snapshot(), status="BLOCKED", blocked_by=("boundary_blocker",))

    digest = build_foundation_digest(
        phase=20,
        foundation_packet=_packet(),
        boundary_snapshot=snapshot,
    )

    assert digest.status == "BLOCKED"
    assert digest.blocked_by == ("boundary_blocker",)


def test_phase_20_digest_cautions_when_reports_caution():
    packet = replace(_packet(), status="CAUTION", cautions=("packet_caution",))
    snapshot = replace(_snapshot(), status="CAUTION", cautions=("boundary_caution",))

    digest = build_foundation_digest(
        phase=20,
        foundation_packet=packet,
        boundary_snapshot=snapshot,
    )

    assert digest.status == "CAUTION"
    assert digest.cautions == ("packet_caution", "boundary_caution")


def test_phase_20_digest_format_never_claims_authority():
    digest = build_foundation_digest(
        phase=20,
        foundation_packet=_packet(),
        boundary_snapshot=_snapshot(),
    )

    lines = format_foundation_digest(digest)

    assert "Permission: not granted" in lines
    assert "Approval: not granted" in lines
