from source_proxy.agent_factory.contracts import AgentFactorySummary, ReadinessMatrixRow
from source_proxy.agent_factory.operator_summary import (
    build_operator_summary_packet,
    format_operator_summary_packet,
)
from source_proxy.agent_factory.verification_manifest import build_verification_manifest


def test_phase_13_operator_packet_preserves_completion_status_without_permission():
    packet = build_operator_summary_packet(
        phase=13,
        completion_summary=AgentFactorySummary(
            status="READY",
            title="Agent Factory Foundation Completion Gate",
        ),
    )

    assert packet.phase == 13
    assert packet.status == "READY"
    assert packet.grants_approval is False
    assert packet.grants_permission is False
    assert packet.authority.is_fail_closed is True


def test_phase_13_operator_packet_collects_readiness_blockers():
    packet = build_operator_summary_packet(
        phase=13,
        completion_summary=AgentFactorySummary(
            status="BLOCKED",
            title="Completion Gate",
            blocked_by=("proxy_apply_verify_receipt_ready",),
        ),
        readiness_rows=(
            ReadinessMatrixRow(
                plan="Plan 6",
                name="Design Agent Stack",
                status="BLOCKED",
                allowed_mode="blocked_future_design_proposal_only",
                blocked_by=("design_source_rights_boundary",),
            ),
        ),
    )

    assert packet.blockers == (
        "proxy_apply_verify_receipt_ready",
        "design_source_rights_boundary",
    )


def test_phase_13_operator_packet_collects_cautions():
    packet = build_operator_summary_packet(
        phase=13,
        completion_summary=AgentFactorySummary(
            status="CAUTION",
            title="Completion Gate",
            caution_items=("manual review pending",),
        ),
        readiness_rows=(
            ReadinessMatrixRow(
                plan="Plan 4",
                name="Safe-Write and Verification Dependent Helpers",
                status="CAUTION",
                allowed_mode="blocked_future_proposal_only",
                blocked_by=("cartographer_safe_write_ready",),
            ),
        ),
    )

    assert packet.cautions == ("manual review pending", "cartographer_safe_write_ready")


def test_phase_13_operator_packet_notes_verification_manifest():
    manifest = build_verification_manifest(
        phase=13,
        test_files=("source_proxy/tests/test_agent_factory_operator_summary.py",),
        closeout_doc="docs/agent-ecosystem-plan-1-phase-13-closeout-v0.1.md",
    )

    packet = build_operator_summary_packet(
        phase=13,
        completion_summary=AgentFactorySummary(status="READY", title="Completion Gate"),
        verification_manifest=manifest,
    )

    assert "Run the manual verification manifest commands." in packet.next_steps


def test_phase_13_operator_packet_format_never_claims_authority():
    packet = build_operator_summary_packet(
        phase=13,
        completion_summary=AgentFactorySummary(status="READY", title="Completion Gate"),
    )

    lines = format_operator_summary_packet(packet)

    assert "Phase: 13" in lines
    assert "Permission: not granted" in lines
    assert "Approval: not granted" in lines
