from source_proxy.agent_factory.contracts import AuditFinding, LaneReport
from source_proxy.agent_factory.foundation_completion import (
    evaluate_foundation_completion,
    format_foundation_completion,
)


def test_phase_11_completion_ready_when_supplied_reports_clear():
    summary = evaluate_foundation_completion(
        manifest_report=LaneReport(),
        api_report=LaneReport(),
        authority_report=LaneReport(),
    )

    assert summary.status == "READY"
    assert summary.reason_codes == ("phase_11_completion_ready",)
    assert summary.grants_approval is False
    assert summary.grants_permission is False


def test_phase_11_completion_blocks_on_manifest_report():
    finding = AuditFinding(
        rule="missing_phase_record",
        severity="blocked",
        subject="Phase 9",
        detail="Missing phase record.",
    )

    summary = evaluate_foundation_completion(
        manifest_report=LaneReport.from_findings((finding,)),
        api_report=LaneReport(),
        authority_report=LaneReport(),
    )

    assert summary.status == "BLOCKED"
    assert summary.blocked_by == ("Phase 9",)
    assert summary.reason_codes == ("lane_report_blocked",)


def test_phase_11_completion_cautions_on_api_report():
    finding = AuditFinding(
        rule="unexpected_public_export",
        severity="caution",
        subject="surprise_helper",
        detail="Unexpected public export.",
    )

    summary = evaluate_foundation_completion(
        manifest_report=LaneReport(),
        api_report=LaneReport.from_findings((finding,)),
        authority_report=LaneReport(),
    )

    assert summary.status == "CAUTION"
    assert summary.caution_items == ("surprise_helper",)
    assert summary.grants_permission is False


def test_phase_11_completion_blocks_on_authority_report():
    finding = AuditFinding(
        rule="authority_invariant_grant",
        severity="blocked",
        subject="flags[0].apply",
        detail="Forbidden authority grant.",
    )

    summary = evaluate_foundation_completion(
        manifest_report=LaneReport(),
        api_report=LaneReport(),
        authority_report=LaneReport.from_findings((finding,)),
    )

    assert summary.status == "BLOCKED"
    assert summary.blocked_by == ("flags[0].apply",)


def test_phase_11_completion_format_never_claims_authority():
    summary = evaluate_foundation_completion(
        manifest_report=LaneReport(),
        api_report=LaneReport(),
        authority_report=LaneReport(),
    )

    lines = format_foundation_completion(summary)

    assert "Phase: 11" in lines
    assert "Permission: not granted" in lines
    assert "Approval: not granted" in lines
