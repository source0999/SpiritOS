from dataclasses import replace

from source_proxy.agent_factory.catalog import DEFAULT_AGENT_CATALOG, get_catalog_entry
from source_proxy.agent_factory.contracts import AuthorityFlags
from source_proxy.agent_factory.foundation_review import (
    format_foundation_review,
    review_agent_factory_foundation,
)


def test_phase_6_review_blocks_future_catalog_entries_without_gates():
    summary = review_agent_factory_foundation()

    assert summary.status == "BLOCKED"
    assert "phase_6_foundation_review" in summary.reason_codes
    assert "proxy_apply_verify_receipt_ready" in summary.blocked_by
    assert summary.grants_approval is False
    assert summary.grants_permission is False


def test_phase_6_review_still_blocks_manual_future_boundaries_when_gates_ready():
    summary = review_agent_factory_foundation(
        supplied_gate_status={
            "proxy_apply_verify_receipt_ready": True,
            "cartographer_live_state_ready": True,
            "cartographer_approval_token_boundary_ready": True,
            "cartographer_safe_write_ready": True,
            "cartographer_verification_runner_ready": True,
            "cartographer_workflow_queue_ready": True,
            "cartographer_worker_coordination_ready": True,
            "proxy_cartographer_daily_driver_ready": True,
        }
    )

    assert summary.status == "BLOCKED"
    assert "design_source_rights_boundary" in summary.blocked_by
    assert "scout_review_flow" in summary.blocked_by
    assert "repeated_soak_proof" in summary.blocked_by
    assert summary.grants_permission is False


def test_phase_6_review_blocks_catalog_authority_grant():
    entry = replace(
        DEFAULT_AGENT_CATALOG[0],
        authority=AuthorityFlags(command_execution=True),
    )

    summary = review_agent_factory_foundation(catalog=(entry,))

    assert summary.status == "BLOCKED"
    assert "Agent Factory Runtime Foundation" in summary.blocked_by
    assert "lane_report_blocked" in summary.reason_codes


def test_phase_6_review_ready_for_plan_1_only_catalog():
    entry = get_catalog_entry("Agent Factory Runtime Foundation")

    summary = review_agent_factory_foundation(catalog=(entry,))

    assert summary.status == "READY"
    assert summary.reason_codes == ("phase_6_foundation_ready",)
    assert summary.grants_approval is False
    assert summary.grants_permission is False


def test_phase_6_format_lines_do_not_claim_authority():
    entry = get_catalog_entry("Agent Factory Runtime Foundation")
    summary = review_agent_factory_foundation(catalog=(entry,))

    lines = format_foundation_review(summary)

    assert "Phase: 6" in lines
    assert "Permission: not granted" in lines
    assert "Approval: not granted" in lines
