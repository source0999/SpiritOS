import pytest

from source_proxy.coding.campaign_3_recovery import assess_extended_lane_failure


def test_required_external_lane_failure_cannot_claim_full_success() -> None:
    result = assess_extended_lane_failure(lane_id="extended.mac-worker", failure="timeout", applicable=True)
    assert result["outcome"] == "BLOCKED_ENV"
    assert result["external_host_failure"] is True
    assert result["full_success_allowed"] is False


def test_declared_replacement_remains_below_full_success() -> None:
    result = assess_extended_lane_failure(lane_id="extended.retained-sub-agent", failure="provider_unreachable", applicable=True, replacement_used=True)
    assert result["outcome"] == "RECOVERING"
    assert result["claim_ceiling"] == "recovery_claim_only_not_full_success"
    assert result["full_success_allowed"] is False


def test_unknown_lane_fails_closed() -> None:
    with pytest.raises(ValueError, match="campaign_3_recovery_unknown_lane"):
        assess_extended_lane_failure(lane_id="fake", failure="timeout", applicable=True)
