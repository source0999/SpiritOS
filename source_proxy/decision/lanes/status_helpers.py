from __future__ import annotations

from typing import Any, Iterable

from source_proxy.diagnostics.status_codes import (
    classify_failure,
    is_failure_status,
    receipt_failure_classification_from_lanes,
    serialize_failure_classification,
)

VALID_LANE_STATUS_VALUES = frozenset({"used", "skipped", "blocked", "failed", "timed_out", "config_blocked"})


def lane_status(status: str, reason: str, **extra: Any) -> dict[str, Any]:
    payload = {"status": status, "reason": reason, **extra}
    if is_failure_status(status):
        classification = classify_failure(
            status=status,
            reason=reason,
            source=str(extra.get("source") or extra.get("lane") or "fip0_lane"),
            provider_errors=extra.get("provider_errors", []),
        )
        payload["reason_code"] = classification.reason_code
        payload["failure_classification"] = serialize_failure_classification(classification)
    return payload


def valid_lane_status_value(value: str) -> bool:
    return value in VALID_LANE_STATUS_VALUES


def packet_lane_status(packet: dict[str, Any], *, fallback_reason: str) -> dict[str, Any]:
    status = str(packet.get("status") or "")
    reason = str(packet.get("reason") or fallback_reason)
    if not valid_lane_status_value(status):
        return lane_status(
            "failed",
            "context_lane_returned_invalid_status",
            source=packet.get("source"),
            raw_status=status,
            raw_reason=reason,
        )
    return lane_status(
        status,
        reason,
        source=packet.get("source"),
        diagnostics=packet.get("diagnostics") if isinstance(packet.get("diagnostics"), dict) else {},
        packet=packet.get("packet") if isinstance(packet.get("packet"), dict) else {},
        authority=packet.get("authority") if isinstance(packet.get("authority"), dict) else {},
    )


def receipt_failure_classification(receipt: dict[str, Any], lane_status_fields: Iterable[str]) -> dict[str, Any]:
    lanes = {
        field: receipt.get(field)
        for field in lane_status_fields
        if isinstance(receipt.get(field), dict)
    }
    return receipt_failure_classification_from_lanes(lanes)


def receipt_failure_event(receipt: dict[str, Any]) -> dict[str, Any]:
    classification = receipt.get("failure_classification")
    if not isinstance(classification, dict) or not classification.get("failure_present"):
        return {"failure_present": False}
    return {
        "event_type": "failure",
        "failure_present": True,
        "failure_class": classification.get("failure_class"),
        "reason_code": classification.get("reason_code"),
        "legacy_compat_string": classification.get("legacy_compat_string"),
        "lane": classification.get("lane", ""),
    }
