from __future__ import annotations

import socket
import subprocess
import urllib.request

import pytest

from source_proxy.decision.escalation_contract import (
    BrainSwitchEvidence,
    BrainSwitchRecommendation,
    FailureClass,
    LaneAvailability,
    advisory_from_route_statuses,
    evidence_from_lane_attempts,
    recommend_brain_switch,
)
from source_proxy.decision.model_lanes import brain_switch_advisory_from_model_lane_attempts
from source_proxy.routing.litellm_router import brain_switch_advisory_for_route_statuses


def test_all_recommendation_values_exist_and_serialize() -> None:
    values = [item.value for item in BrainSwitchRecommendation]

    assert values == [
        "LOCAL_RETRY_RECOMMENDED",
        "LOCAL_DECOMPOSITION_RECOMMENDED",
        "LOCAL_MODEL_INSUFFICIENT",
        "API_ESCALATION_RECOMMENDED",
        "HUMAN_DECISION_REQUIRED",
    ]
    verdict = recommend_brain_switch(
        BrainSwitchEvidence(
            task_shape="structured output",
            formatting_failures=1,
            failure_classification=FailureClass.MODEL_FORMATTING_FAILURE,
            evidence_ids=("ev-format",),
        )
    ).to_dict()
    assert verdict["recommendation"] == "LOCAL_RETRY_RECOMMENDED"
    assert verdict["dry_run_only"] is True
    assert verdict["provider_call_performed"] is False


def test_formatting_failure_does_not_equal_capability_failure() -> None:
    verdict = recommend_brain_switch(
        BrainSwitchEvidence(
            task_shape="structured output",
            local_attempts=1,
            formatting_failures=1,
            failure_classification=FailureClass.MODEL_FORMATTING_FAILURE,
            evidence_ids=("ev-json",),
        )
    )

    assert verdict.recommendation is BrainSwitchRecommendation.LOCAL_RETRY_RECOMMENDED
    assert verdict.failure_classification is FailureClass.MODEL_FORMATTING_FAILURE
    assert verdict.recommendation is not BrainSwitchRecommendation.API_ESCALATION_RECOMMENDED


def test_retryable_local_failure_recommends_local_retry() -> None:
    evidence = evidence_from_lane_attempts(
        task_shape="tool transient failure",
        attempts=[{"status": "timed_out", "retryable": True, "failure_classification": {"failure_class": "RESOURCE_PRESSURE"}}],
        lane_availability=[LaneAvailability("qwen_local", configured=True, available=True)],
        evidence_ids=["ev-timeout"],
    )

    assert recommend_brain_switch(evidence).recommendation is BrainSwitchRecommendation.LOCAL_RETRY_RECOMMENDED


def test_structured_output_failure_can_recommend_decomposition() -> None:
    evidence = evidence_from_lane_attempts(
        task_shape="large structured output",
        attempts=[
            {"status": "failed", "failure_classification": {"failure_class": "MODEL_FORMATTING_FAILURE"}, "reason": "schema invalid"},
            {"status": "failed", "failure_classification": {"failure_class": "MODEL_FORMATTING_FAILURE"}, "reason": "schema invalid again"},
        ],
        decomposable=True,
    )

    assert recommend_brain_switch(evidence).recommendation is BrainSwitchRecommendation.LOCAL_DECOMPOSITION_RECOMMENDED


def test_repeated_bounded_capability_evidence_can_recommend_dry_run_api_escalation() -> None:
    evidence = evidence_from_lane_attempts(
        task_shape="capability limited planning",
        attempts=[
            {"status": "failed", "failure_classification": {"failure_class": "MODEL_CAPABILITY_LIMIT"}, "reason": "validated inability one"},
            {"status": "failed", "failure_classification": {"failure_class": "MODEL_CAPABILITY_LIMIT"}, "reason": "validated inability two"},
        ],
        lane_availability=[LaneAvailability("local_coder", configured=True, available=True)],
        evidence_ids=["ev-cap-1", "ev-cap-2"],
    )
    verdict = recommend_brain_switch(evidence)

    assert verdict.recommendation is BrainSwitchRecommendation.API_ESCALATION_RECOMMENDED
    assert verdict.authority_required is True
    assert verdict.dry_run_only is True
    assert verdict.provider_call_performed is False
    assert verdict.reason_code == "bounded_validated_local_model_insufficient_dry_run"


def test_unavailable_provider_never_reported_available() -> None:
    verdict = advisory_from_route_statuses(
        route_statuses=[{"alias": "local", "provider": "ollama", "enabled": True, "reason": "connection refused"}],
        task_shape="capability limited planning",
    )

    assert verdict["provider_available"] is False
    assert verdict["recommendation"] == "HUMAN_DECISION_REQUIRED"


def test_human_cost_privacy_uncertainty_requires_human_decision() -> None:
    verdict = recommend_brain_switch(
        BrainSwitchEvidence(
            task_shape="private customer security review",
            privacy_class="high",
            cost_class="high",
            uncertainty_requires_human=True,
            failure_classification=FailureClass.HUMAN_APPROVAL_REQUIRED,
        )
    )

    assert verdict.recommendation is BrainSwitchRecommendation.HUMAN_DECISION_REQUIRED
    assert verdict.authority_required is True


def test_no_provider_call_is_performed(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: object, **kwargs: object) -> None:
        raise AssertionError("provider/network/subprocess call attempted")

    monkeypatch.setattr(socket, "create_connection", fail)
    monkeypatch.setattr(urllib.request, "urlopen", fail)
    monkeypatch.setattr(subprocess, "run", fail)

    verdict = recommend_brain_switch(
        BrainSwitchEvidence(
            task_shape="capability limited planning",
            local_attempts=2,
            reasoning_or_capability_evidence=("validated inability",),
            configured_lanes=("local",),
            failure_classification=FailureClass.LOCAL_MODEL_INSUFFICIENT,
            capability_failure_validated=True,
        )
    )

    assert verdict.provider_call_performed is False
    assert verdict.recommendation is BrainSwitchRecommendation.API_ESCALATION_RECOMMENDED


def test_benchmark_labels_do_not_affect_recommendation() -> None:
    attempts = [
        {"status": "failed", "failure_classification": {"failure_class": "MODEL_FORMATTING_FAILURE"}, "reason": "schema invalid"},
    ]
    plain = evidence_from_lane_attempts(task_shape="structured output comparison", attempts=attempts)
    labeled = evidence_from_lane_attempts(task_shape="structured output comparison A2 A5 A9", attempts=attempts)

    assert recommend_brain_switch(plain).recommendation == recommend_brain_switch(labeled).recommendation
    assert recommend_brain_switch(plain).reason_code == recommend_brain_switch(labeled).reason_code


def test_same_shape_different_words_same_recommendation() -> None:
    first = evidence_from_lane_attempts(
        task_shape="multi part migration too large for one pass",
        attempts=[{"status": "failed", "failure_classification": {"failure_class": "MODEL_FORMATTING_FAILURE"}}],
        decomposable=True,
    )
    second = evidence_from_lane_attempts(
        task_shape="large staged work should be decomposed",
        attempts=[{"status": "failed", "failure_classification": {"failure_class": "MODEL_FORMATTING_FAILURE"}}],
        decomposable=True,
    )

    assert recommend_brain_switch(first).recommendation == recommend_brain_switch(second).recommendation


def test_model_lanes_and_router_consult_contract_read_only() -> None:
    model_advisory = brain_switch_advisory_from_model_lane_attempts(
        task_shape="structured output",
        attempts=[{"status": "failed", "failure_classification": {"failure_class": "MODEL_FORMATTING_FAILURE"}}],
        evidence_refs=["ev-model"],
    )
    router_advisory = brain_switch_advisory_for_route_statuses(
        [{"alias": "local", "provider": "ollama", "enabled": True, "reason": "connection refused"}],
        task_shape="route availability",
        evidence_ids=["ev-route"],
    )

    assert model_advisory["dry_run_only"] is True
    assert router_advisory["dry_run_only"] is True
    assert model_advisory["provider_call_performed"] is False
    assert router_advisory["provider_call_performed"] is False
