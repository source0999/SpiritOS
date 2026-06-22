from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from source_proxy.diagnostics.status_codes import FailureClass


class BrainSwitchRecommendation(str, Enum):
    LOCAL_RETRY_RECOMMENDED = "LOCAL_RETRY_RECOMMENDED"
    LOCAL_DECOMPOSITION_RECOMMENDED = "LOCAL_DECOMPOSITION_RECOMMENDED"
    LOCAL_MODEL_INSUFFICIENT = "LOCAL_MODEL_INSUFFICIENT"
    API_ESCALATION_RECOMMENDED = "API_ESCALATION_RECOMMENDED"
    HUMAN_DECISION_REQUIRED = "HUMAN_DECISION_REQUIRED"


@dataclass(frozen=True)
class LaneAvailability:
    lane_id: str
    configured: bool
    available: bool
    privacy_class: str = "unknown"
    cost_class: str = "unknown"
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrainSwitchEvidence:
    task_shape: str
    local_attempts: int = 0
    formatting_failures: int = 0
    validation_failures: int = 0
    reasoning_or_capability_evidence: tuple[str, ...] = ()
    configured_lanes: tuple[str, ...] = ()
    unconfigured_lanes: tuple[str, ...] = ()
    unavailable_lanes: tuple[str, ...] = ()
    privacy_class: str = "unknown"
    cost_class: str = "unknown"
    evidence_ids: tuple[str, ...] = ()
    failure_classification: FailureClass = FailureClass.UNKNOWN_NEEDS_INVESTIGATION
    retryable: bool = False
    decomposable: bool = False
    capability_failure_validated: bool = False
    authority_required: bool = False
    uncertainty_requires_human: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["failure_classification"] = self.failure_classification.value
        payload["reasoning_or_capability_evidence"] = list(self.reasoning_or_capability_evidence)
        payload["configured_lanes"] = list(self.configured_lanes)
        payload["unconfigured_lanes"] = list(self.unconfigured_lanes)
        payload["unavailable_lanes"] = list(self.unavailable_lanes)
        payload["evidence_ids"] = list(self.evidence_ids)
        return payload


@dataclass(frozen=True)
class BrainSwitchVerdict:
    recommendation: BrainSwitchRecommendation
    task_shape: str
    local_attempts: int
    formatting_failures: int
    validation_failures: int
    reasoning_or_capability_evidence: tuple[str, ...]
    configured_lanes: tuple[str, ...]
    unconfigured_lanes: tuple[str, ...]
    unavailable_lanes: tuple[str, ...]
    privacy_class: str
    cost_class: str
    authority_required: bool
    evidence_ids: tuple[str, ...]
    failure_classification: FailureClass
    reason_code: str
    dry_run_only: bool = True
    provider_call_performed: bool = False
    provider_available: bool | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["recommendation"] = self.recommendation.value
        payload["failure_classification"] = self.failure_classification.value
        payload["reasoning_or_capability_evidence"] = list(self.reasoning_or_capability_evidence)
        payload["configured_lanes"] = list(self.configured_lanes)
        payload["unconfigured_lanes"] = list(self.unconfigured_lanes)
        payload["unavailable_lanes"] = list(self.unavailable_lanes)
        payload["evidence_ids"] = list(self.evidence_ids)
        payload["notes"] = list(self.notes)
        return payload


def recommend_brain_switch(evidence: BrainSwitchEvidence) -> BrainSwitchVerdict:
    recommendation, authority_required, reason_code, notes = _recommendation_for(evidence)
    provider_available = None
    if evidence.unavailable_lanes:
        provider_available = False
    elif evidence.configured_lanes:
        provider_available = True
    return BrainSwitchVerdict(
        recommendation=recommendation,
        task_shape=evidence.task_shape,
        local_attempts=evidence.local_attempts,
        formatting_failures=evidence.formatting_failures,
        validation_failures=evidence.validation_failures,
        reasoning_or_capability_evidence=evidence.reasoning_or_capability_evidence,
        configured_lanes=evidence.configured_lanes,
        unconfigured_lanes=evidence.unconfigured_lanes,
        unavailable_lanes=evidence.unavailable_lanes,
        privacy_class=evidence.privacy_class,
        cost_class=evidence.cost_class,
        authority_required=authority_required,
        evidence_ids=evidence.evidence_ids,
        failure_classification=evidence.failure_classification,
        reason_code=reason_code,
        dry_run_only=True,
        provider_call_performed=False,
        provider_available=provider_available,
        notes=notes,
    )


def evidence_from_lane_attempts(
    *,
    task_shape: str,
    attempts: list[dict[str, Any]],
    lane_availability: list[LaneAvailability] | None = None,
    privacy_class: str = "unknown",
    cost_class: str = "unknown",
    evidence_ids: list[str] | None = None,
    decomposable: bool = False,
    uncertainty_requires_human: bool = False,
) -> BrainSwitchEvidence:
    formatting_failures = 0
    validation_failures = 0
    capability_failures = 0
    retryable = False
    capability_evidence: list[str] = []
    last_failure = FailureClass.UNKNOWN_NEEDS_INVESTIGATION
    for attempt in attempts:
        classification = _failure_class_from_attempt(attempt)
        last_failure = classification
        reason = str(attempt.get("reason") or attempt.get("reason_code") or classification.value)
        status = str(attempt.get("status") or "")
        if classification is FailureClass.MODEL_FORMATTING_FAILURE:
            formatting_failures += 1
        if classification is FailureClass.VALIDATOR_FAILURE:
            validation_failures += 1
        if classification in {FailureClass.MODEL_CAPABILITY_LIMIT, FailureClass.LOCAL_MODEL_INSUFFICIENT}:
            capability_failures += 1
            capability_evidence.append(reason)
        if bool(attempt.get("retryable")) or status in {"timed_out", "blocked"}:
            retryable = True
    lane_availability = lane_availability or []
    configured = tuple(lane.lane_id for lane in lane_availability if lane.configured)
    unconfigured = tuple(lane.lane_id for lane in lane_availability if not lane.configured)
    unavailable = tuple(lane.lane_id for lane in lane_availability if lane.configured and not lane.available)
    if capability_failures >= 2:
        last_failure = FailureClass.LOCAL_MODEL_INSUFFICIENT
    return BrainSwitchEvidence(
        task_shape=_normalize_task_shape(task_shape),
        local_attempts=len(attempts),
        formatting_failures=formatting_failures,
        validation_failures=validation_failures,
        reasoning_or_capability_evidence=tuple(capability_evidence),
        configured_lanes=configured,
        unconfigured_lanes=unconfigured,
        unavailable_lanes=unavailable,
        privacy_class=privacy_class,
        cost_class=cost_class,
        evidence_ids=tuple(evidence_ids or []),
        failure_classification=last_failure,
        retryable=retryable,
        decomposable=decomposable,
        capability_failure_validated=capability_failures >= 2,
        uncertainty_requires_human=uncertainty_requires_human,
    )


def advisory_from_route_statuses(
    *,
    route_statuses: list[dict[str, Any]],
    task_shape: str = "unknown",
    evidence_ids: list[str] | None = None,
) -> dict[str, Any]:
    lanes = [
        LaneAvailability(
            lane_id=str(item.get("alias") or item.get("lane_id") or item.get("provider") or "unknown"),
            configured=bool(item.get("enabled")),
            available=bool(item.get("enabled")) and not str(item.get("reason") or ""),
            privacy_class="local" if item.get("provider") == "ollama" else "external_or_unknown",
            cost_class="local_compute" if item.get("provider") == "ollama" else "external_or_unknown",
            reason=str(item.get("reason") or ""),
        )
        for item in route_statuses
    ]
    attempts = [
        {
            "status": "blocked",
            "failure_classification": {"failure_class": "SERVICE_UNAVAILABLE"},
            "reason": lane.reason or "lane_unavailable",
            "retryable": False,
        }
        for lane in lanes
        if lane.configured and not lane.available
    ]
    evidence = evidence_from_lane_attempts(
        task_shape=task_shape,
        attempts=attempts,
        lane_availability=lanes,
        evidence_ids=evidence_ids or [],
        uncertainty_requires_human=bool(lanes and all(not lane.available for lane in lanes if lane.configured)),
    )
    return recommend_brain_switch(evidence).to_dict()


def _recommendation_for(evidence: BrainSwitchEvidence) -> tuple[BrainSwitchRecommendation, bool, str, tuple[str, ...]]:
    if evidence.uncertainty_requires_human or evidence.privacy_class == "high" or evidence.cost_class == "high":
        return (
            BrainSwitchRecommendation.HUMAN_DECISION_REQUIRED,
            True,
            "human_decision_required_for_privacy_cost_or_availability_uncertainty",
            ("human authority required before changing provider policy",),
        )
    if evidence.unavailable_lanes and not evidence.configured_lanes:
        return (
            BrainSwitchRecommendation.HUMAN_DECISION_REQUIRED,
            True,
            "no_configured_available_lane",
            ("unavailable provider is not reported available",),
        )
    if evidence.failure_classification is FailureClass.MODEL_FORMATTING_FAILURE:
        if evidence.decomposable or evidence.formatting_failures >= 2:
            return (
                BrainSwitchRecommendation.LOCAL_DECOMPOSITION_RECOMMENDED,
                False,
                "structured_output_failure_recommend_decomposition",
                ("formatting failure does not imply capability failure",),
            )
        return (
            BrainSwitchRecommendation.LOCAL_RETRY_RECOMMENDED,
            False,
            "formatting_failure_retry_local",
            ("formatting failure stays local within retry budget",),
        )
    if evidence.retryable and not evidence.capability_failure_validated:
        return (
            BrainSwitchRecommendation.LOCAL_RETRY_RECOMMENDED,
            False,
            "retryable_local_failure",
            ("retryable local failure is not an API recommendation",),
        )
    if evidence.decomposable:
        return (
            BrainSwitchRecommendation.LOCAL_DECOMPOSITION_RECOMMENDED,
            False,
            "task_shape_decomposable_local",
            ("decomposition remains local and feeds F4",),
        )
    if evidence.capability_failure_validated:
        if evidence.local_attempts >= 2 and evidence.configured_lanes and not evidence.unavailable_lanes:
            return (
                BrainSwitchRecommendation.API_ESCALATION_RECOMMENDED,
                True,
                "bounded_validated_local_model_insufficient_dry_run",
                ("dry-run recommendation only; Britton authority required",),
            )
        return (
            BrainSwitchRecommendation.LOCAL_MODEL_INSUFFICIENT,
            False,
            "local_model_insufficient_without_escalation_authority",
            ("capability evidence recorded without provider policy change",),
        )
    if evidence.failure_classification in {FailureClass.SERVICE_UNAVAILABLE, FailureClass.ENVIRONMENT_FAILURE}:
        return (
            BrainSwitchRecommendation.HUMAN_DECISION_REQUIRED,
            True,
            "lane_unavailable_or_environment_blocked",
            ("provider unavailable is never reported available",),
        )
    return (
        BrainSwitchRecommendation.LOCAL_RETRY_RECOMMENDED,
        False,
        "default_local_retry_for_unclassified_failure",
        ("unknown failure remains local until evidence improves",),
    )


def _failure_class_from_attempt(attempt: dict[str, Any]) -> FailureClass:
    value = attempt.get("failure_classification")
    if isinstance(value, dict):
        value = value.get("failure_class")
    if isinstance(value, FailureClass):
        return value
    if isinstance(value, str):
        try:
            return FailureClass(value)
        except ValueError:
            return FailureClass.UNKNOWN_NEEDS_INVESTIGATION
    reason_code = str(attempt.get("reason_code") or "")
    try:
        return FailureClass(reason_code)
    except ValueError:
        return FailureClass.UNKNOWN_NEEDS_INVESTIGATION


def _normalize_task_shape(task_shape: str) -> str:
    lowered = " ".join(str(task_shape or "unknown").lower().split())
    if not lowered:
        return "unknown"
    if any(term in lowered for term in ("multi", "decompose", "part", "large")):
        return "decomposable_multi_part"
    if "format" in lowered or "schema" in lowered:
        return "structured_output"
    if "capability" in lowered or "reasoning" in lowered:
        return "capability_limited"
    if "privacy" in lowered or "cost" in lowered or "security" in lowered:
        return "authority_sensitive"
    return lowered
