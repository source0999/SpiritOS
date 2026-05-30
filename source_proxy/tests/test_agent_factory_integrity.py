from dataclasses import replace

from source_proxy.agent_factory.catalog import DEFAULT_AGENT_CATALOG, get_catalog_entry
from source_proxy.agent_factory.contracts import (
    AgentFactorySummary,
    AuthorityFlags,
    DependencyGateReport,
    LaneReport,
)
from source_proxy.agent_factory.integrity import (
    audit_catalog_integrity,
    audit_report_authority_integrity,
)


def test_default_catalog_integrity_is_clear_without_permission():
    report = audit_catalog_integrity()

    assert report.status == "clear"
    assert report.findings == ()
    assert report.grants_permission is False
    assert report.authority.is_fail_closed is True


def test_catalog_integrity_blocks_duplicate_names():
    entry = DEFAULT_AGENT_CATALOG[0]

    report = audit_catalog_integrity((entry, entry))

    assert report.status == "blocked"
    assert report.findings[0].rule == "duplicate_catalog_name"


def test_catalog_integrity_blocks_unknown_dependency_gate():
    entry = replace(
        get_catalog_entry("Proxy-Dependent Proposal Helpers"),
        dependency_gates=("unknown_gate_ready",),
    )

    report = audit_catalog_integrity((entry,))

    assert report.status == "blocked"
    assert report.findings[0].rule == "catalog_unknown_dependency_gate"


def test_catalog_integrity_blocks_ready_entry_with_blockers():
    entry = replace(
        get_catalog_entry("Agent Factory Runtime Foundation"),
        can_run_now=True,
        blocked_by=("proxy_apply_verify_receipt_ready",),
    )

    report = audit_catalog_integrity((entry,))

    assert report.status == "blocked"
    assert report.findings[0].rule == "catalog_ready_while_blocked"


def test_report_authority_integrity_blocks_any_report_authority_grants():
    report = audit_report_authority_integrity(
        lane_reports=(LaneReport(authority=AuthorityFlags(write=True)),),
        gate_reports=(DependencyGateReport(authority=AuthorityFlags(queue_execution=True)),),
        summaries=(AgentFactorySummary(authority=AuthorityFlags(approval=True)),),
    )

    assert report.status == "blocked"
    assert [finding.subject for finding in report.findings] == [
        "lane_reports[0].write",
        "gate_reports[0].queue_execution",
        "summaries[0].approval",
    ]


def test_report_authority_integrity_clear_for_fail_closed_reports():
    report = audit_report_authority_integrity(
        lane_reports=(LaneReport(),),
        gate_reports=(DependencyGateReport(),),
        summaries=(AgentFactorySummary(),),
    )

    assert report.status == "clear"
    assert report.findings == ()
