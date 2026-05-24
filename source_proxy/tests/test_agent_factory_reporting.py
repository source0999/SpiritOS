from source_proxy.agent_factory.catalog import get_catalog_entry
from source_proxy.agent_factory.contracts import (
    AuditFinding,
    DependencyGateReport,
    EvidenceReference,
    LaneReport,
)
from source_proxy.agent_factory.reporting import (
    compose_agent_factory_summary,
    format_summary_lines,
)


def test_summary_ready_for_empty_supplied_reports_without_permission():
    summary = compose_agent_factory_summary(title="phase summary")

    assert summary.status == "READY"
    assert summary.grants_approval is False
    assert summary.grants_permission is False
    assert summary.authority.is_fail_closed is True


def test_summary_blocks_on_lane_report_findings():
    finding = AuditFinding(
        rule="forbidden_file",
        severity="blocked",
        subject="src/app/page.tsx",
        detail="Forbidden path.",
        evidence=EvidenceReference(file="src/app/page.tsx", rule="forbidden_file"),
    )
    lane_report = LaneReport.from_findings((finding,))

    summary = compose_agent_factory_summary(
        title="lane summary",
        lane_reports=(lane_report,),
    )

    assert summary.status == "BLOCKED"
    assert summary.reason_codes == ("lane_report_blocked",)
    assert summary.blocked_by == ("src/app/page.tsx",)
    assert summary.evidence[0].file == "src/app/page.tsx"


def test_summary_cautions_on_gate_caution_report():
    gate_report = DependencyGateReport(
        status="CAUTION",
        reason_codes=("gate_caution:cartographer_safe_write_ready",),
        blocked_by=("cartographer_safe_write_ready",),
    )

    summary = compose_agent_factory_summary(
        title="gate summary",
        gate_reports=(gate_report,),
    )

    assert summary.status == "CAUTION"
    assert summary.caution_items == ("cartographer_safe_write_ready",)
    assert summary.blocked_by == ()


def test_summary_blocks_on_future_catalog_entry():
    entry = get_catalog_entry("Proxy-Dependent Proposal Helpers")

    summary = compose_agent_factory_summary(
        title="catalog summary",
        catalog_entries=(entry,),
    )

    assert summary.status == "BLOCKED"
    assert summary.reason_codes == ("catalog_blocked:Plan 2",)
    assert summary.blocked_by == ("proxy_apply_verify_receipt_ready",)


def test_format_summary_lines_never_claims_permission():
    summary = compose_agent_factory_summary(title="display summary")

    lines = format_summary_lines(summary)

    assert "Status: READY" in lines
    assert "Permission: not granted" in lines
    assert "Approval: not granted" in lines
