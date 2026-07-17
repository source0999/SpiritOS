from __future__ import annotations

import pytest

from source_proxy.routing.fallback import FallbackPolicy, RouteFallbackError, invoke_with_truthful_fallback


def test_primary_success_cannot_claim_a_fallback() -> None:
    value, receipt = invoke_with_truthful_fallback(FallbackPolicy("primary"), primary=lambda: "ok")
    assert value == "ok"
    assert receipt["primary_success"] is True
    assert receipt["fallback_used"] is False
    assert receipt["selected_provider"] == "primary"


def test_fallback_is_explicit_and_cannot_claim_primary_success() -> None:
    value, receipt = invoke_with_truthful_fallback(
        FallbackPolicy("primary", "secondary", allow_fallback=True),
        primary=lambda: (_ for _ in ()).throw(TimeoutError()),
        secondary=lambda: "recovered",
    )
    assert value == "recovered"
    assert receipt["fallback_used"] is True
    assert receipt["primary_success"] is False
    assert receipt["selected_provider"] == "secondary"
    assert receipt["failure_reason"] == "primary_failed:TimeoutError"


def test_primary_failure_without_explicit_fallback_fails_closed() -> None:
    with pytest.raises(RouteFallbackError) as error:
        invoke_with_truthful_fallback(
            FallbackPolicy("primary", "secondary", allow_fallback=False),
            primary=lambda: (_ for _ in ()).throw(ConnectionError()),
            secondary=lambda: "must-not-run",
        )
    assert error.value.reason_code == "primary_route_failed_no_fallback"
    assert error.value.receipt["fallback_used"] is False
