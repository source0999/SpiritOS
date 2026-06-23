from __future__ import annotations

from source_proxy.api import decision
from source_proxy.decision.lanes.status_helpers import (
    lane_status,
    packet_lane_status,
    receipt_failure_classification,
    receipt_failure_event,
    valid_lane_status_value,
)


def test_lane_status_helper_matches_decision_private_alias_for_failure() -> None:
    expected = lane_status(
        "failed",
        "local_model_output_not_json",
        source="qwen_coder",
        provider_errors=["JSONDecodeError"],
    )

    assert decision._lane_status(
        "failed",
        "local_model_output_not_json",
        source="qwen_coder",
        provider_errors=["JSONDecodeError"],
    ) == expected
    assert expected["reason_code"] == "MODEL_FORMATTING_FAILURE"
    assert expected["failure_classification"]["legacy_compat_string"] == "local_model_output_not_json"


def test_valid_lane_status_and_packet_status_parity() -> None:
    assert valid_lane_status_value("used") is True
    assert decision._valid_lane_status_value("used") is True
    assert valid_lane_status_value("bogus") is False

    packet = {
        "source": "cartographer",
        "status": "blocked",
        "reason": "missing_context",
        "diagnostics": {"mode": "local"},
        "packet": {"paths": []},
        "authority": {"write": False},
    }
    assert decision._packet_lane_status(packet, fallback_reason="fallback") == packet_lane_status(packet, fallback_reason="fallback")


def test_invalid_packet_status_keeps_existing_failure_shape() -> None:
    result = packet_lane_status({"source": "obsidian", "status": "weird", "reason": "raw"}, fallback_reason="fallback")

    assert result["status"] == "failed"
    assert result["reason"] == "context_lane_returned_invalid_status"
    assert result["raw_status"] == "weird"
    assert result["failure_classification"]["failure_class"] in {"UNKNOWN_NEEDS_INVESTIGATION", "VALIDATOR_FAILURE"}


def test_receipt_failure_classification_and_event_preserve_decision_shape() -> None:
    receipt = {
        "qwen_coder_status": lane_status("failed", "local_model_output_not_json", source="qwen_coder"),
        "context_router_status": lane_status("used", "context_ready"),
    }
    classification = receipt_failure_classification(receipt, decision.FIP0_LANE_STATUS_FIELDS)
    receipt["failure_classification"] = classification

    assert decision._receipt_failure_classification(receipt) == classification
    assert receipt_failure_event(receipt) == decision._receipt_failure_event(receipt)
    assert receipt_failure_event(receipt)["failure_present"] is True
    assert receipt_failure_event({}) == {"failure_present": False}
