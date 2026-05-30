from dataclasses import replace

from source_proxy.agent_factory.final_readiness import FinalReadinessDecision
from source_proxy.agent_factory.foundation_manifest import (
    EXPECTED_FOUNDATION_PHASES,
    build_foundation_phase_record,
)
from source_proxy.agent_factory.foundation_packet import (
    build_foundation_packet,
    format_foundation_packet,
)
from source_proxy.agent_factory.phase_ledger import build_phase_ledger_rollup
from source_proxy.agent_factory.verification_manifest import build_verification_manifest


def _ready_decision():
    return FinalReadinessDecision(
        status="READY",
        decision="agent_factory_foundation_ready_for_operator_review",
        reasons=("phase_17_packet",),
    )


def _phase_ledger():
    records = tuple(
        build_foundation_phase_record(
            phase=phase,
            title=f"Phase {phase}",
            checks_passed=True,
        )
        for phase in EXPECTED_FOUNDATION_PHASES
    )
    return build_phase_ledger_rollup(records)


def _manifest(phase=17):
    return build_verification_manifest(
        phase=phase,
        test_files=("source_proxy/tests/test_agent_factory_foundation_packet.py",),
        closeout_doc=f"docs/agent-ecosystem-plan-1-phase-{phase}-closeout-v0.1.md",
    )


def test_phase_17_foundation_packet_ready_from_ready_supplied_reports():
    packet = build_foundation_packet(
        phase=17,
        readiness_decision=_ready_decision(),
        phase_ledger=_phase_ledger(),
        verification_manifest=_manifest(),
    )

    assert packet.status == "READY"
    assert packet.phase == 17
    assert packet.verification_command_count == 3
    assert packet.grants_permission is False


def test_phase_17_foundation_packet_blocks_readiness_blockers():
    packet = build_foundation_packet(
        phase=17,
        readiness_decision=replace(_ready_decision(), status="BLOCKED", blockers=("audit",)),
        phase_ledger=_phase_ledger(),
        verification_manifest=_manifest(),
    )

    assert packet.status == "BLOCKED"
    assert packet.blocked_by == ("audit",)


def test_phase_17_foundation_packet_blocks_phase_mismatch():
    packet = build_foundation_packet(
        phase=17,
        readiness_decision=_ready_decision(),
        phase_ledger=_phase_ledger(),
        verification_manifest=_manifest(phase=16),
    )

    assert packet.status == "BLOCKED"
    assert packet.blocked_by == ("verification_manifest_phase_mismatch",)


def test_phase_17_foundation_packet_cautions_when_ledger_cautions():
    phase_ledger = replace(_phase_ledger(), status="CAUTION", cautions=("manual spot check",))

    packet = build_foundation_packet(
        phase=17,
        readiness_decision=_ready_decision(),
        phase_ledger=phase_ledger,
        verification_manifest=_manifest(),
    )

    assert packet.status == "CAUTION"
    assert packet.cautions == ("manual spot check",)


def test_phase_17_foundation_packet_format_never_claims_authority():
    packet = build_foundation_packet(
        phase=17,
        readiness_decision=_ready_decision(),
        phase_ledger=_phase_ledger(),
        verification_manifest=_manifest(),
    )

    lines = format_foundation_packet(packet)

    assert "Permission: not granted" in lines
    assert "Approval: not granted" in lines
