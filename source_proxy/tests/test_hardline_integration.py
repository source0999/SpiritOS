from __future__ import annotations

from source_proxy.decision.hardline_integration import (
    HardlineProofInput,
    browser_functional_verifier_lane_allows_go,
    classify_hardline_integration,
    plan2_final_go_allowed,
    qwen_coder_lane_allows_go,
    reject_go_like_label,
    specialist_lanes_allow_go,
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


def test_unsupported_mac_job_and_model_failure_cannot_go() -> None:
    assert classify_hardline_integration(_complete(needs_fix=True)) == "NEEDS_FIX"
    assert classify_hardline_integration(_complete(blocked_env=True)) == "BLOCKED_ENV"
    assert reject_go_like_label("NEEDS_FIX", "GO") is True
    assert reject_go_like_label("BLOCKED_ENV", "GO") is True


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


def _qwen_lane(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "required": True,
        "status": "INTEGRATED_LIVE",
        "activated": True,
        "live_invocation": True,
        "real_output": True,
        "downstream_consumed": True,
        "metadata_only": False,
        "trace_id": "trace_qwen",
        "invocation_event_id": "invocation_qwen",
        "consumer_event_id": "consumer_qwen",
        "consumer_subsystem": "cartographer_specialist_packet_consumer",
        "failure_changes_outcome": True,
    }
    data.update(overrides)
    return data


def _verifier_lane(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "required": True,
        "status": "INTEGRATED_LIVE",
        "live_invocation": True,
        "verification_result": "VERIFIED",
        "advisory_only": False,
        "preview_only": False,
        "unverified": False,
        "downstream_consumed": True,
        "trace_id": "trace_verifier",
        "invocation_event_id": "invocation_verifier",
        "consumer_event_id": "consumer_verifier",
        "consumer_subsystem": "cartographer_specialist_packet_consumer",
        "failure_changes_outcome": True,
    }
    data.update(overrides)
    return data


def _sidecar_lane(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "required": True,
        "status": "INTEGRATED_LIVE",
        "live_invocation": True,
        "real_output": True,
        "downstream_consumed": True,
        "trace_id": "trace_sidecar",
        "invocation_event_id": "invocation_sidecar",
        "consumer_event_id": "consumer_sidecar",
        "consumer_subsystem": "cartographer_specialist_packet_consumer",
        "failure_changes_outcome": True,
    }
    data.update(overrides)
    return data


def test_metadata_only_and_non_activated_qwen_cannot_be_go() -> None:
    assert qwen_coder_lane_allows_go(_qwen_lane()) is True
    assert qwen_coder_lane_allows_go(_qwen_lane(metadata_only=True)) is False
    assert qwen_coder_lane_allows_go(_qwen_lane(activated=False)) is False
    assert qwen_coder_lane_allows_go(_qwen_lane(live_invocation=False)) is False
    assert qwen_coder_lane_allows_go(_qwen_lane(downstream_consumed=False)) is False
    assert qwen_coder_lane_allows_go(_qwen_lane(consumer_event_id="")) is False


def test_advisory_preview_and_unverified_verifier_cannot_be_go() -> None:
    assert browser_functional_verifier_lane_allows_go(_verifier_lane()) is True
    assert browser_functional_verifier_lane_allows_go(_verifier_lane(advisory_only=True)) is False
    assert browser_functional_verifier_lane_allows_go(_verifier_lane(preview_only=True)) is False
    assert browser_functional_verifier_lane_allows_go(_verifier_lane(unverified=True)) is False
    assert browser_functional_verifier_lane_allows_go(_verifier_lane(verification_result="UNVERIFIED")) is False
    assert browser_functional_verifier_lane_allows_go(_verifier_lane(downstream_consumed=False)) is False
    assert browser_functional_verifier_lane_allows_go(_verifier_lane(consumer_event_id="")) is False


def test_plan2_final_gate_checks_specialist_lane_level_proof() -> None:
    lanes = {
        "gemma_intent_spec": _sidecar_lane(),
        "hermes_critique_risk": _sidecar_lane(),
        "qwen_coder": _qwen_lane(),
        "browser_functional_verifier": _verifier_lane(),
    }
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
        "metadata_only_go_detected": False,
        "non_activated_lane_go_detected": False,
        "unverified_verifier_go_detected": False,
        "unconsumed_output_go_detected": False,
        "plan_3_started": False,
        "specialist_lanes": lanes,
    }
    assert specialist_lanes_allow_go(lanes) is True
    assert plan2_final_go_allowed(**kwargs) is True
    bad_lanes = {**lanes, "qwen_coder": _qwen_lane(activated=False)}
    assert specialist_lanes_allow_go(bad_lanes) is False
    assert plan2_final_go_allowed(**{**kwargs, "specialist_lanes": bad_lanes}) is False
    assert plan2_final_go_allowed(**{**kwargs, "metadata_only_go_detected": True}) is False
