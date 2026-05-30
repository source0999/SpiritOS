from source_proxy.agent_factory.catalog import (
    DEFAULT_AGENT_CATALOG,
    FORBIDDEN_AUTHORITY,
    get_catalog_entry,
)


def test_catalog_includes_all_major_plans():
    names = {entry.name for entry in DEFAULT_AGENT_CATALOG}

    assert names == {
        "Agent Factory Runtime Foundation",
        "Proxy-Dependent Proposal Helpers",
        "Cartographer Read-Only Context Helpers",
        "Safe-Write and Verification Dependent Helpers",
        "Workflow Queue and Worker Coordination Helpers",
        "Design Agent Stack",
        "Scout Helper Stack",
        "Oracle and Chat Helper Polish",
        "Multi-Agent Orchestration and Future Autonomy",
    }


def test_catalog_does_not_grant_forbidden_authority():
    for entry in DEFAULT_AGENT_CATALOG:
        assert entry.forbidden_authority == FORBIDDEN_AUTHORITY
        assert entry.authority.is_fail_closed is True
        assert entry.grants_permission is False


def test_plan_1_catalog_entry_can_run_now_without_proxy_or_cartographer_gates():
    entry = get_catalog_entry("Agent Factory Runtime Foundation")

    assert entry is not None
    assert entry.plan == "Plan 1"
    assert entry.dependency_gates == ()
    assert entry.can_run_now is True
    assert entry.blocked_by == ()


def test_future_catalog_entries_are_blocked_by_dependencies():
    plan_2 = get_catalog_entry("Proxy-Dependent Proposal Helpers")
    plan_3 = get_catalog_entry("Cartographer Read-Only Context Helpers")
    plan_5 = get_catalog_entry("Workflow Queue and Worker Coordination Helpers")

    assert plan_2 is not None
    assert plan_2.can_run_now is False
    assert plan_2.blocked_by == ("proxy_apply_verify_receipt_ready",)

    assert plan_3 is not None
    assert plan_3.can_run_now is False
    assert "cartographer_live_state_ready" in plan_3.blocked_by
    assert "cartographer_approval_token_boundary_ready" in plan_3.blocked_by

    assert plan_5 is not None
    assert plan_5.can_run_now is False
    assert "cartographer_workflow_queue_ready" in plan_5.blocked_by
