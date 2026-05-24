from source_proxy.agent_factory.catalog import get_catalog_entry
from source_proxy.agent_factory.readiness_matrix import (
    build_readiness_matrix,
    format_readiness_matrix,
)


def test_phase_7_matrix_includes_all_catalog_entries():
    rows = build_readiness_matrix()

    assert len(rows) == 9
    assert rows[0].name == "Agent Factory Runtime Foundation"
    assert rows[0].plan == "Plan 1"


def test_phase_7_matrix_marks_plan_1_ready_without_permission():
    row = build_readiness_matrix(catalog=(get_catalog_entry("Agent Factory Runtime Foundation"),))[0]

    assert row.status == "READY"
    assert row.blocked_by == ()
    assert row.reason_codes == ("all_required_gates_ready",)
    assert row.grants_approval is False
    assert row.grants_permission is False
    assert row.authority.is_fail_closed is True


def test_phase_7_matrix_blocks_plan_2_without_proxy_gate():
    row = build_readiness_matrix(catalog=(get_catalog_entry("Proxy-Dependent Proposal Helpers"),))[0]

    assert row.status == "BLOCKED"
    assert row.blocked_by == ("proxy_apply_verify_receipt_ready",)
    assert "gate_not_ready:proxy_apply_verify_receipt_ready" in row.reason_codes


def test_phase_7_matrix_keeps_manual_blockers_even_when_dependency_gates_ready():
    row = build_readiness_matrix(
        catalog=(get_catalog_entry("Design Agent Stack"),),
        supplied_gate_status={},
    )[0]

    assert row.status == "BLOCKED"
    assert row.blocked_by == ("design_source_rights_boundary",)
    assert row.reason_codes == ("catalog_blocked:Plan 6",)


def test_phase_7_matrix_reports_caution_gate_without_permission():
    row = build_readiness_matrix(
        catalog=(get_catalog_entry("Safe-Write and Verification Dependent Helpers"),),
        supplied_gate_status={
            "cartographer_safe_write_ready": "caution",
            "cartographer_verification_runner_ready": True,
        },
    )[0]

    assert row.status == "BLOCKED"
    assert "cartographer_safe_write_ready" in row.blocked_by
    assert row.grants_permission is False


def test_phase_7_matrix_format_never_claims_approval():
    rows = build_readiness_matrix(catalog=(get_catalog_entry("Agent Factory Runtime Foundation"),))

    lines = format_readiness_matrix(rows)

    assert lines[0] == "Plan | Status | Name | Blocked By"
    assert "Permission: not granted" in lines
    assert "Approval: not granted" in lines
