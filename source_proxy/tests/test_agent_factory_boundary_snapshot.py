from dataclasses import replace

import source_proxy.agent_factory as agent_factory
from source_proxy.agent_factory.boundary_snapshot import (
    build_boundary_snapshot,
    format_boundary_snapshot,
)
from source_proxy.agent_factory.final_readiness import FinalReadinessDecision
from source_proxy.agent_factory.foundation_manifest import (
    EXPECTED_FOUNDATION_PHASES,
    build_foundation_phase_record,
)
from source_proxy.agent_factory.foundation_packet import build_foundation_packet
from source_proxy.agent_factory.phase_ledger import build_phase_ledger_rollup
from source_proxy.agent_factory.verification_manifest import build_verification_manifest


def _ledger():
    records = tuple(
        build_foundation_phase_record(
            phase=phase,
            title=f"Phase {phase}",
            checks_passed=True,
        )
        for phase in EXPECTED_FOUNDATION_PHASES
    )
    return build_phase_ledger_rollup(records)


def _packet(ledger=None):
    ledger = ledger or _ledger()
    decision = FinalReadinessDecision(
        status="READY",
        decision="agent_factory_foundation_ready_for_operator_review",
        reasons=("phase_19_boundary_snapshot",),
    )
    manifest = build_verification_manifest(
        phase=19,
        test_files=("source_proxy/tests/test_agent_factory_boundary_snapshot.py",),
        closeout_doc="docs/agent-ecosystem-plan-1-phase-19-closeout-v0.1.md",
    )
    return build_foundation_packet(
        phase=19,
        readiness_decision=decision,
        phase_ledger=ledger,
        verification_manifest=manifest,
    )


def test_phase_19_boundary_snapshot_ready_for_clean_supplied_surface():
    ledger = _ledger()
    snapshot = build_boundary_snapshot(
        public_names=tuple(agent_factory.__all__),
        foundation_packet=_packet(ledger),
        phase_ledger=ledger,
    )

    assert snapshot.status == "READY"
    assert snapshot.public_name_count == len(agent_factory.__all__)
    assert snapshot.grants_permission is False


def test_phase_19_boundary_snapshot_blocks_for_forbidden_public_name():
    ledger = _ledger()
    snapshot = build_boundary_snapshot(
        public_names=("apply_changes",),
        foundation_packet=_packet(ledger),
        phase_ledger=ledger,
    )

    assert snapshot.status == "BLOCKED"
    assert snapshot.blocked_by == ("apply_changes",)


def test_phase_19_boundary_snapshot_blocks_for_packet_blockers():
    ledger = _ledger()
    packet = replace(_packet(ledger), status="BLOCKED", blocked_by=("packet_blocker",))

    snapshot = build_boundary_snapshot(
        public_names=tuple(agent_factory.__all__),
        foundation_packet=packet,
        phase_ledger=ledger,
    )

    assert snapshot.status == "BLOCKED"
    assert snapshot.blocked_by == ("packet_blocker",)


def test_phase_19_boundary_snapshot_cautions_for_ledger_cautions():
    ledger = replace(_ledger(), status="CAUTION", cautions=("manual review",))
    snapshot = build_boundary_snapshot(
        public_names=tuple(agent_factory.__all__),
        foundation_packet=_packet(ledger),
        phase_ledger=ledger,
    )

    assert snapshot.status == "CAUTION"
    assert snapshot.cautions == ("manual review",)


def test_phase_19_boundary_snapshot_format_never_claims_authority():
    snapshot = build_boundary_snapshot(
        public_names=tuple(agent_factory.__all__),
        foundation_packet=_packet(),
        phase_ledger=_ledger(),
    )

    lines = format_boundary_snapshot(snapshot)

    assert "Permission: not granted" in lines
    assert "Approval: not granted" in lines
