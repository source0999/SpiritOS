from __future__ import annotations

from source_proxy.decision.hardline_integration import (
    HardlineProofInput,
    classify_hardline_integration,
    plan2_final_go_allowed,
    reject_go_like_label,
)


def _complete(**overrides: object) -> HardlineProofInput:
    data = {
        "invoked_by_canonical_workflow": True,
        "real_upstream_state": True,
        "live_function_performed": True,
        "output_consumed_downstream": True,
        "failure_changes_outcome": True,
        "causal_trace_recorded": True,
        "focused_tests": True,
        "live_proof": True,
        "active_surface_visible": True,
    }
    data.update(overrides)
    return HardlineProofInput(**data)


def test_preview_advisory_status_and_route_existence_cannot_be_go() -> None:
    assert classify_hardline_integration(_complete(preview_only=True)) == "NOT_INTEGRATED_PREVIEW_ONLY"
    assert classify_hardline_integration(_complete(advisory_only=True)) == "NOT_INTEGRATED_ADVISORY_ONLY"
    assert classify_hardline_integration(_complete(status_only=True)) == "NOT_INTEGRATED_STATUS_ONLY"
    assert classify_hardline_integration(_complete(live_function_performed=False)) == "NEEDS_FIX"


def test_read_only_mac_system_status_cannot_be_mac_full_go() -> None:
    status = classify_hardline_integration(_complete(read_only_for_action_subsystem=True))
    assert status == "NOT_INTEGRATED_READ_ONLY_FOR_ACTION"
    assert reject_go_like_label(status, "GO") is True


def test_research_without_provider_or_consumer_cannot_go() -> None:
    assert classify_hardline_integration(_complete(live_proof=False)) == "NEEDS_FIX"
    assert classify_hardline_integration(_complete(output_consumed_downstream=False)) == "NOT_INTEGRATED_UNCONSUMED_OUTPUT"


def test_model_timeout_mock_and_fixture_only_cannot_go() -> None:
    assert classify_hardline_integration(_complete(blocked_env=True)) == "BLOCKED_ENV"
    assert classify_hardline_integration(_complete(mock_only=True)) == "NOT_INTEGRATED_MOCK_ONLY"
    assert classify_hardline_integration(_complete(fixture_only=True)) == "NOT_INTEGRATED_FIXTURE_ONLY"


def test_plan2_final_go_requires_every_hardline_gate() -> None:
    kwargs = {
        "mac_write_integration": "INTEGRATED_LIVE",
        "mac_search_check_integration": "INTEGRATED_LIVE",
        "research_integration": "INTEGRATED_LIVE",
        "specialist_lane_integration": "INTEGRATED_LIVE",
        "task_a": "PASS",
        "task_b": "PASS",
        "task_c": "PASS",
        "operator_check": "PASS",
        "focused_tests": "PASS",
        "preview_go_detected": False,
        "advisory_go_detected": False,
        "status_only_go_detected": False,
        "read_only_action_go_detected": False,
        "mock_go_detected": False,
        "fixture_only_go_detected": False,
        "plan_3_started": False,
    }
    assert plan2_final_go_allowed(**kwargs) is True
    assert plan2_final_go_allowed(**{**kwargs, "mac_write_integration": "BLOCKED_HUMAN"}) is False
    assert plan2_final_go_allowed(**{**kwargs, "preview_go_detected": True}) is False
