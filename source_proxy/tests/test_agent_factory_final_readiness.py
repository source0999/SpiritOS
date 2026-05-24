from source_proxy.agent_factory.contracts import (
    AgentFactorySummary,
    AuditFinding,
    LaneReport,
    OperatorSummaryPacket,
)
from source_proxy.agent_factory.final_readiness import (
    FinalReadinessDecision,
    audit_final_readiness_decision,
    build_final_readiness_decision,
    format_final_readiness_decision,
)


def test_phase_14_final_readiness_ready_without_permission():
    decision = build_final_readiness_decision(
        completion_summary=AgentFactorySummary(status="READY", title="Completion"),
        operator_packet=OperatorSummaryPacket(
            phase=14,
            status="READY",
            headline="Operator",
        ),
        invariant_report=LaneReport(),
    )

    assert decision.status == "READY"
    assert decision.decision == "agent_factory_foundation_ready_for_operator_review"
    assert decision.grants_approval is False
    assert decision.grants_permission is False


def test_phase_14_final_readiness_blocks_on_completion_blockers():
    decision = build_final_readiness_decision(
        completion_summary=AgentFactorySummary(
            status="BLOCKED",
            title="Completion",
            blocked_by=("missing_phase_record",),
        ),
        operator_packet=OperatorSummaryPacket(phase=14, status="READY", headline="Operator"),
        invariant_report=LaneReport(),
    )

    assert decision.status == "BLOCKED"
    assert decision.blockers == ("missing_phase_record",)


def test_phase_14_final_readiness_blocks_on_invariant_report():
    finding = AuditFinding(
        rule="authority_invariant_grant",
        severity="blocked",
        subject="flags[0].apply",
        detail="Forbidden authority grant.",
    )

    decision = build_final_readiness_decision(
        completion_summary=AgentFactorySummary(status="READY", title="Completion"),
        operator_packet=OperatorSummaryPacket(phase=14, status="READY", headline="Operator"),
        invariant_report=LaneReport.from_findings((finding,)),
    )

    assert decision.status == "BLOCKED"
    assert decision.blockers == ("flags[0].apply",)
    assert "authority_invariants_blocked" in decision.reasons


def test_phase_14_audit_blocks_permission_language():
    report = audit_final_readiness_decision(
        FinalReadinessDecision(status="READY", decision="approved_for_permission")
    )

    assert report.status == "blocked"
    assert report.findings[0].rule == "final_decision_implies_permission"


def test_phase_14_format_never_claims_authority():
    decision = build_final_readiness_decision(
        completion_summary=AgentFactorySummary(status="READY", title="Completion"),
        operator_packet=OperatorSummaryPacket(phase=14, status="READY", headline="Operator"),
        invariant_report=LaneReport(),
    )

    lines = format_final_readiness_decision(decision)

    assert "Permission: not granted" in lines
    assert "Approval: not granted" in lines
