from __future__ import annotations

from source_proxy.api import decision
from source_proxy.decision import model_lanes
from source_proxy.diagnostics.status_codes import (
    FailureClass,
    classify_failure,
    no_failure_classification,
    receipt_failure_classification_from_lanes,
    serialize_failure_classification,
)


ALL_CLASSES = [
    "TECHNICAL_FAILURE",
    "ENVIRONMENT_FAILURE",
    "SERVICE_UNAVAILABLE",
    "BRIDGE_INTEGRATION_FAILURE",
    "ROUTING_FAILURE",
    "TOOL_FAILURE",
    "SEARCH_PROVIDER_EMPTY",
    "SEARCH_PROVIDER_FAILURE",
    "MODEL_CAPABILITY_LIMIT",
    "MODEL_FORMATTING_FAILURE",
    "LOCAL_MODEL_INSUFFICIENT",
    "API_ESCALATION_RECOMMENDED",
    "POLICY_BLOCKED",
    "HUMAN_APPROVAL_REQUIRED",
    "EVIDENCE_MISSING",
    "VALIDATOR_FAILURE",
    "PROMPT_AMBIGUITY",
    "RESOURCE_PRESSURE",
    "UNKNOWN_NEEDS_INVESTIGATION",
]


def test_all_19_failure_classes_are_stable_strings() -> None:
    assert [item.value for item in FailureClass] == ALL_CLASSES
    assert len(FailureClass) == 19


def test_receipt_safe_serialization_preserves_legacy_string() -> None:
    classification = classify_failure(
        status="failed",
        reason="local_model_output_not_json",
        source="qwen_local_coder",
    )

    payload = serialize_failure_classification(classification)

    assert payload["failure_class"] == "MODEL_FORMATTING_FAILURE"
    assert payload["reason_code"] == "MODEL_FORMATTING_FAILURE"
    assert payload["legacy_compat_string"] == "local_model_output_not_json"
    assert payload["source"] == "qwen_local_coder"
    assert payload["failure_present"] is True


def test_known_shapes_do_not_fall_into_unknown() -> None:
    cases = {
        "TECHNICAL_FAILURE": "internal backend exception traceback",
        "ENVIRONMENT_FAILURE": "missing module dependency in venv",
        "SERVICE_UNAVAILABLE": "ollama_inventory_unavailable connection refused",
        "BRIDGE_INTEGRATION_FAILURE": "consumer_event trace bridge mismatch",
        "ROUTING_FAILURE": "router target_missing unsafe target",
        "TOOL_FAILURE": "subprocess command failed",
        "SEARCH_PROVIDER_EMPTY": "empty search no search results",
        "SEARCH_PROVIDER_FAILURE": "searxng search provider http failure",
        "MODEL_CAPABILITY_LIMIT": "repeated inability capability limit",
        "MODEL_FORMATTING_FAILURE": "json_decode_error invalid output schema",
        "LOCAL_MODEL_INSUFFICIENT": "local_model_insufficient",
        "API_ESCALATION_RECOMMENDED": "api_escalation_recommended",
        "POLICY_BLOCKED": "policy blocked forbidden path",
        "HUMAN_APPROVAL_REQUIRED": "human approval required",
        "EVIDENCE_MISSING": "receipt_missing evidence not found",
        "VALIDATOR_FAILURE": "verifier deterministic validation failed",
        "PROMPT_AMBIGUITY": "ambiguous prompt unclear prompt",
        "RESOURCE_PRESSURE": "timeout resource pressure rate_limited",
    }
    for expected, reason in cases.items():
        result = classify_failure(reason=reason, status="failed")
        assert result.failure_class.value == expected
        assert result.failure_class is not FailureClass.UNKNOWN_NEEDS_INVESTIGATION


def test_unknown_only_for_genuinely_novel_failure_shape() -> None:
    result = classify_failure(reason="novel unclassified opaque condition", status="failed")

    assert result.failure_class is FailureClass.UNKNOWN_NEEDS_INVESTIGATION


def test_model_formatting_failure_is_not_capability_or_local_insufficient() -> None:
    result = classify_failure(reason="model produced useful content but output schema invalid", status="failed")

    assert result.failure_class is FailureClass.MODEL_FORMATTING_FAILURE
    assert result.failure_class is not FailureClass.MODEL_CAPABILITY_LIMIT
    assert result.failure_class is not FailureClass.LOCAL_MODEL_INSUFFICIENT


def test_local_model_unavailable_is_environment_or_service_not_insufficient() -> None:
    result = classify_failure(
        reason="ollama_inventory_unavailable_for_qwen_coder",
        status="blocked",
        provider_errors=["Connection refused"],
    )

    assert result.failure_class in {FailureClass.ENVIRONMENT_FAILURE, FailureClass.SERVICE_UNAVAILABLE}
    assert result.failure_class is not FailureClass.LOCAL_MODEL_INSUFFICIENT


def test_repeated_validated_inability_can_map_to_capability_limit() -> None:
    result = classify_failure(reason="repeated inability capability limit after validation", status="failed")

    assert result.failure_class is FailureClass.MODEL_CAPABILITY_LIMIT


def test_api_escalation_is_recommendation_only() -> None:
    result = classify_failure(reason="api_escalation_recommended after bounded local failure", status="blocked")

    assert result.failure_class is FailureClass.API_ESCALATION_RECOMMENDED
    assert "recommended" in result.legacy_compat_string


def test_search_empty_is_distinct_from_provider_failure() -> None:
    empty = classify_failure(reason="empty search no search results", status="failed")
    failed = classify_failure(reason="searxng search provider http failure", status="failed")

    assert empty.failure_class is FailureClass.SEARCH_PROVIDER_EMPTY
    assert failed.failure_class is FailureClass.SEARCH_PROVIDER_FAILURE


def test_validator_failure_distinct_from_model_failure() -> None:
    result = classify_failure(reason="verifier deterministic validation failed", status="failed")

    assert result.failure_class is FailureClass.VALIDATOR_FAILURE
    assert result.failure_class is not FailureClass.MODEL_FORMATTING_FAILURE


def test_human_approval_distinct_from_policy_blocked() -> None:
    approval = classify_failure(reason="human approval required", status="blocked")
    policy = classify_failure(reason="policy blocked forbidden path", status="blocked")

    assert approval.failure_class is FailureClass.HUMAN_APPROVAL_REQUIRED
    assert policy.failure_class is FailureClass.POLICY_BLOCKED


def test_qwen_lane_failure_emits_reason_code_and_legacy_reason() -> None:
    payload = model_lanes._model_lane_status(
        "failed",
        "local_model_output_not_json",
        lane="qwen_local_coder",
        provider_errors=["JSONDecodeError"],
    )

    assert payload["reason"] == "local_model_output_not_json"
    assert payload["reason_code"] == "MODEL_FORMATTING_FAILURE"
    assert payload["failure_classification"]["failure_class"] == "MODEL_FORMATTING_FAILURE"
    assert payload["failure_classification"]["legacy_compat_string"] == "local_model_output_not_json"


def test_fip0_lane_status_adds_failure_classification_without_replacing_reason() -> None:
    payload = decision._lane_status("blocked", "ollama_inventory_unavailable", source="qwen_coder")

    assert payload["status"] == "blocked"
    assert payload["reason"] == "ollama_inventory_unavailable"
    assert payload["reason_code"] == "SERVICE_UNAVAILABLE"
    assert payload["failure_classification"]["failure_class"] == "SERVICE_UNAVAILABLE"


def test_receipt_failure_classification_is_additive_and_can_report_no_failure() -> None:
    no_failure = no_failure_classification()
    assert no_failure == {
        "failure_present": False,
        "failure_class": None,
        "reason_code": "",
        "legacy_compat_string": "",
        "source": "receipt",
        "lane": "",
    }

    failure = receipt_failure_classification_from_lanes(
        {
            "qwen_coder_status": decision._lane_status(
                "failed",
                "local_model_output_not_json",
                source="qwen_coder",
            )
        }
    )
    assert failure["failure_present"] is True
    assert failure["failure_class"] == "MODEL_FORMATTING_FAILURE"
    assert failure["lane"] == "qwen_coder_status"


def test_fip6_trace_carries_additive_failure_event() -> None:
    receipt = {
        "run_id": "fip0-test",
        "timestamp": "2026-06-21T00:00:00+00:00",
        "raw_prompt": "demo",
        "normalized_task": "demo",
        "route_type": "manual_route",
        "workspace_mode": "repo",
        "dirty_tree_status": {},
        "qwen_coder_status": decision._lane_status(
            "failed",
            "local_model_output_not_json",
            source="qwen_coder",
        ),
        "failure_classification": {
            "failure_present": True,
            "failure_class": "MODEL_FORMATTING_FAILURE",
            "reason_code": "MODEL_FORMATTING_FAILURE",
            "legacy_compat_string": "local_model_output_not_json",
            "source": "fip0_receipt",
            "lane": "qwen_coder_status",
        },
        "failure_event": {
            "event_type": "failure",
            "failure_present": True,
            "failure_class": "MODEL_FORMATTING_FAILURE",
            "reason_code": "MODEL_FORMATTING_FAILURE",
            "legacy_compat_string": "local_model_output_not_json",
            "lane": "qwen_coder_status",
        },
        "final_verdict": "NO-GO",
        "productive": False,
        "coder_path": "legacy_stub",
        "verification_real": {},
        "verification_real_reasons": {},
        "degraded_lanes": [],
        "final_packet_hash": "hash",
        "coder_received_packet_hash": "",
        "receipt_path": "docs/fip0-test.json",
    }

    trace = decision._fip6_operator_trace_from_receipt(receipt, receipt_path=__import__("pathlib").Path("docs/fip0-test.json"))

    assert trace["failure_trace"]["failure_event"]["event_type"] == "failure"
    assert trace["failure_trace"]["failure_classification"]["failure_class"] == "MODEL_FORMATTING_FAILURE"
