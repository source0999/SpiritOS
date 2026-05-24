from source_proxy.agent_factory.catalog import get_catalog_entry
from source_proxy.agent_factory.dependency_gates import (
    evaluate_catalog_entry,
    evaluate_dependency_gates,
)


def test_plan_1_evaluates_ready_without_proxy_or_cartographer_gates():
    entry = get_catalog_entry("Agent Factory Runtime Foundation")

    report = evaluate_catalog_entry(entry, {})

    assert report.status == "READY"
    assert report.reason_codes == ("all_required_gates_ready",)
    assert report.grants_approval is False
    assert report.grants_permission is False


def test_plan_2_blocks_until_proxy_apply_verify_receipt_ready():
    entry = get_catalog_entry("Proxy-Dependent Proposal Helpers")

    blocked = evaluate_catalog_entry(entry, {})
    ready = evaluate_catalog_entry(entry, {"proxy_apply_verify_receipt_ready": True})

    assert blocked.status == "BLOCKED"
    assert blocked.blocked_by == ("proxy_apply_verify_receipt_ready",)
    assert "gate_not_ready:proxy_apply_verify_receipt_ready" in blocked.reason_codes
    assert ready.status == "READY"


def test_plan_3_blocks_until_cartographer_live_state_and_approval_boundary_ready():
    entry = get_catalog_entry("Cartographer Read-Only Context Helpers")

    blocked = evaluate_catalog_entry(entry, {"cartographer_live_state_ready": True})
    ready = evaluate_catalog_entry(
        entry,
        {
            "cartographer_live_state_ready": True,
            "cartographer_approval_token_boundary_ready": True,
        },
    )

    assert blocked.status == "BLOCKED"
    assert blocked.blocked_by == ("cartographer_approval_token_boundary_ready",)
    assert ready.status == "READY"


def test_plan_5_blocks_until_workflow_queue_is_ready():
    entry = get_catalog_entry("Workflow Queue and Worker Coordination Helpers")

    report = evaluate_catalog_entry(
        entry,
        {"cartographer_worker_coordination_ready": True},
    )

    assert report.status == "BLOCKED"
    assert "cartographer_workflow_queue_ready" in report.blocked_by


def test_unknown_dependency_gate_fails_closed():
    report = evaluate_dependency_gates(("mystery_gate_ready",), {})

    assert report.status == "BLOCKED"
    assert report.blocked_by == ("mystery_gate_ready",)
    assert report.reason_codes == ("unknown_gate:mystery_gate_ready",)


def test_evaluator_can_return_caution_without_permission():
    report = evaluate_dependency_gates(
        ("cartographer_safe_write_ready",),
        {"cartographer_safe_write_ready": "caution"},
    )

    assert report.status == "CAUTION"
    assert report.blocked_by == ("cartographer_safe_write_ready",)
    assert report.grants_approval is False
    assert report.grants_permission is False


def test_evaluator_returns_reports_only_and_never_approval():
    report = evaluate_dependency_gates(
        ("proxy_apply_verify_receipt_ready",),
        {"proxy_apply_verify_receipt_ready": True},
    )

    assert report.status == "READY"
    assert report.authority.is_fail_closed is True
    assert report.grants_approval is False
    assert report.grants_permission is False
