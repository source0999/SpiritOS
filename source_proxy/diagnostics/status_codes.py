"""Failure taxonomy for Source Proxy receipts and lane diagnostics.

This module owns classification labels only; it must not silently change final
verdict vocabulary or turn unknown failures into positive outcomes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any




class FailureClass(str, Enum):
    TECHNICAL_FAILURE = "TECHNICAL_FAILURE"
    ENVIRONMENT_FAILURE = "ENVIRONMENT_FAILURE"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    BRIDGE_INTEGRATION_FAILURE = "BRIDGE_INTEGRATION_FAILURE"
    ROUTING_FAILURE = "ROUTING_FAILURE"
    TOOL_FAILURE = "TOOL_FAILURE"
    SEARCH_PROVIDER_EMPTY = "SEARCH_PROVIDER_EMPTY"
    SEARCH_PROVIDER_FAILURE = "SEARCH_PROVIDER_FAILURE"
    MODEL_CAPABILITY_LIMIT = "MODEL_CAPABILITY_LIMIT"
    MODEL_FORMATTING_FAILURE = "MODEL_FORMATTING_FAILURE"
    LOCAL_MODEL_INSUFFICIENT = "LOCAL_MODEL_INSUFFICIENT"
    API_ESCALATION_RECOMMENDED = "API_ESCALATION_RECOMMENDED"
    POLICY_BLOCKED = "POLICY_BLOCKED"
    HUMAN_APPROVAL_REQUIRED = "HUMAN_APPROVAL_REQUIRED"
    EVIDENCE_MISSING = "EVIDENCE_MISSING"
    VALIDATOR_FAILURE = "VALIDATOR_FAILURE"
    PROMPT_AMBIGUITY = "PROMPT_AMBIGUITY"
    RESOURCE_PRESSURE = "RESOURCE_PRESSURE"
    UNKNOWN_NEEDS_INVESTIGATION = "UNKNOWN_NEEDS_INVESTIGATION"


class RepairFailureKind(str, Enum):
    """Orthogonal repair routing; public FailureClass vocabulary stays stable."""

    MODEL_ERROR = "model_error"
    PROMPT_CONTEXT_ERROR = "prompt_context_error"
    PATCH_FORMAT_ERROR = "patch_format_error"
    TEST_ENVIRONMENT_ERROR = "test_environment_error"
    FIXTURE_ERROR = "fixture_error"
    RUNTIME_ERROR = "runtime_error"
    REVIEWER_REJECTION = "reviewer_rejection"
    VERIFIER_REJECTION = "verifier_rejection"
    TASK_IMPOSSIBLE = "task_impossible"


_FAILURE_STATUS_VALUES = {"blocked", "failed", "timed_out", "config_blocked"}


@dataclass(frozen=True)
class FailureClassification:
    failure_class: FailureClass
    reason_code: str
    legacy_compat_string: str
    status: str
    source: str
    failure_present: bool = True
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["failure_class"] = self.failure_class.value
        payload["details"] = dict(self.details or {})
        return payload


@dataclass(frozen=True)
class ReceiptFailureClassification:
    failure_class: FailureClass | None
    reason_code: str
    legacy_compat_string: str
    failure_present: bool
    source: str = "receipt"
    lane: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure_present": self.failure_present,
            "failure_class": self.failure_class.value if self.failure_class else None,
            "reason_code": self.reason_code,
            "legacy_compat_string": self.legacy_compat_string,
            "source": self.source,
            "lane": self.lane,
        }


@dataclass(frozen=True)
class RepairFailureClassification:
    failure_kind: RepairFailureKind
    failure_class: FailureClass
    diagnostic_code: str
    stage: str
    retryable: bool
    retry_owner: str
    strategy_change_required: bool
    genuine_stop: bool
    legacy_compat_string: str
    details: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure_kind": self.failure_kind.value,
            "failure_class": self.failure_class.value,
            "diagnostic_code": self.diagnostic_code,
            "stage": self.stage,
            "retryable": self.retryable,
            "retry_owner": self.retry_owner,
            "strategy_change_required": self.strategy_change_required,
            "genuine_stop": self.genuine_stop,
            "legacy_compat_string": self.legacy_compat_string,
            "details": dict(self.details or {}),
        }


def is_failure_status(status: str) -> bool:
    return status.strip().lower() in _FAILURE_STATUS_VALUES


def classify_failure(
    *,
    reason: str,
    status: str = "failed",
    source: str = "unknown",
    provider_errors: list[Any] | tuple[Any, ...] | None = None,
    details: dict[str, Any] | None = None,
) -> FailureClassification:
    legacy = str(reason or "").strip() or "unknown_failure"
    haystack = " ".join(
        [
            legacy,
            str(status or ""),
            " ".join(str(item) for item in (provider_errors or [])),
        ]
    ).lower()
    failure_class = _class_for_text(haystack)
    return FailureClassification(
        failure_class=failure_class,
        reason_code=failure_class.value,
        legacy_compat_string=legacy,
        status=str(status or "failed"),
        source=str(source or "unknown"),
        details=details or {},
    )


def classify_repair_failure(
    *,
    diagnostic_code: str,
    stage: str,
    reason: str = "",
    details: dict[str, Any] | None = None,
) -> RepairFailureClassification:
    """Classify a repair decision from structured stage/code before free text."""

    code = str(diagnostic_code or "unknown_failure").strip().lower()
    normalized_stage = str(stage or "unknown").strip().lower()
    legacy = str(reason or diagnostic_code or "unknown_failure").strip()
    combined = f"{code} {legacy.lower()}"

    if any(token in combined for token in ("task_impossible", "irreconcilable_contract")):
        kind = RepairFailureKind.TASK_IMPOSSIBLE
        failure_class = FailureClass.POLICY_BLOCKED
        retryable = False
        retry_owner = "terminal"
        genuine_stop = True
    elif any(token in combined for token in ("fixture", "oracle_execution", "reference_validation")):
        kind = RepairFailureKind.FIXTURE_ERROR
        failure_class = FailureClass.BRIDGE_INTEGRATION_FAILURE
        retryable = True
        retry_owner = "fixture_harness"
        genuine_stop = False
    elif normalized_stage in {"architect", "coder", "model", "reviewer"} and any(
        token in combined
        for token in (
            "llm_timeout",
            "model_timeout",
            "provider_timeout",
            "model_execution_budget_exhausted",
        )
    ):
        kind = RepairFailureKind.MODEL_ERROR
        failure_class = FailureClass.RESOURCE_PRESSURE
        retryable = True
        retry_owner = (
            "architect_model_router"
            if normalized_stage == "architect"
            else "coder_model_router"
        )
        genuine_stop = False
    elif normalized_stage in {"architect", "coder", "model", "reviewer"} and any(
        token in combined
        for token in (
            "llm_router_error",
            "model_router_error",
            "model_not_configured",
            "provider_transport",
        )
    ):
        kind = RepairFailureKind.MODEL_ERROR
        failure_class = FailureClass.ROUTING_FAILURE
        retryable = True
        retry_owner = (
            "architect_model_router"
            if normalized_stage == "architect"
            else "coder_model_router"
        )
        genuine_stop = False
    elif any(
        token in combined
        for token in (
            "not_json",
            "invalid_json",
            "response_repair_exhausted",
            "wrong_format",
            "parse",
            "schema",
            "diff_apply_check",
            "patch",
            "replacement_payload",
        )
    ):
        kind = RepairFailureKind.PATCH_FORMAT_ERROR
        failure_class = FailureClass.MODEL_FORMATTING_FAILURE
        retryable = True
        retry_owner = "parser_then_coder"
        genuine_stop = False
    elif any(
        token in combined
        for token in (
            "environment",
            "missing_module",
            "dependency_unavailable",
            "service_unavailable",
            "timeout",
            "tool_missing",
            "command_not_found",
        )
    ):
        kind = RepairFailureKind.TEST_ENVIRONMENT_ERROR
        failure_class = classify_failure(
            reason=legacy,
            status="failed",
            source=f"repair.{normalized_stage}",
        ).failure_class
        if failure_class not in {
            FailureClass.ENVIRONMENT_FAILURE,
            FailureClass.SERVICE_UNAVAILABLE,
            FailureClass.RESOURCE_PRESSURE,
            FailureClass.TOOL_FAILURE,
        }:
            failure_class = FailureClass.ENVIRONMENT_FAILURE
        retryable = True
        retry_owner = "environment_recovery"
        genuine_stop = False
    elif normalized_stage in {"runtime", "tests", "debugger"} or any(
        token in combined
        for token in ("runtime", "visible_tests_failed", "test_failed", "assertion")
    ):
        kind = RepairFailureKind.RUNTIME_ERROR
        failure_class = FailureClass.VALIDATOR_FAILURE
        retryable = True
        retry_owner = "debugger_then_coder"
        genuine_stop = False
    elif normalized_stage == "reviewer" or "reviewer_reject" in combined:
        kind = RepairFailureKind.REVIEWER_REJECTION
        failure_class = FailureClass.VALIDATOR_FAILURE
        retryable = True
        retry_owner = "coder"
        genuine_stop = False
    elif normalized_stage == "verifier" or "verifier_reject" in combined:
        kind = RepairFailureKind.VERIFIER_REJECTION
        failure_class = FailureClass.VALIDATOR_FAILURE
        retryable = True
        retry_owner = "debugger_then_coder"
        genuine_stop = False
    elif normalized_stage in {"architect", "context", "routing", "scope"} or any(
        token in combined
        for token in ("context", "architect", "target_missing", "prompt_ambigu")
    ):
        kind = RepairFailureKind.PROMPT_CONTEXT_ERROR
        failure_class = (
            FailureClass.POLICY_BLOCKED
            if any(token in combined for token in ("outside_scope", "forbidden", "policy"))
            else FailureClass.BRIDGE_INTEGRATION_FAILURE
        )
        retryable = failure_class is not FailureClass.POLICY_BLOCKED
        retry_owner = "architect_context_selector"
        genuine_stop = False
    else:
        kind = RepairFailureKind.MODEL_ERROR
        failure_class = classify_failure(
            reason=legacy,
            status="failed",
            source=f"repair.{normalized_stage}",
        ).failure_class
        if failure_class is FailureClass.UNKNOWN_NEEDS_INVESTIGATION:
            failure_class = FailureClass.MODEL_CAPABILITY_LIMIT
        retryable = True
        retry_owner = "coder_model_router"
        genuine_stop = False

    return RepairFailureClassification(
        failure_kind=kind,
        failure_class=failure_class,
        diagnostic_code=str(diagnostic_code or "unknown_failure"),
        stage=normalized_stage,
        retryable=retryable,
        retry_owner=retry_owner,
        strategy_change_required=retryable,
        genuine_stop=genuine_stop,
        legacy_compat_string=legacy,
        details=details or {},
    )


def serialize_failure_classification(classification: FailureClassification) -> dict[str, Any]:
    return classification.to_dict()


def no_failure_classification(*, source: str = "receipt") -> dict[str, Any]:
    return ReceiptFailureClassification(
        failure_class=None,
        reason_code="",
        legacy_compat_string="",
        failure_present=False,
        source=source,
    ).to_dict()


def receipt_failure_classification_from_lanes(
    lanes: dict[str, dict[str, Any]],
    *,
    source: str = "fip0_receipt",
) -> dict[str, Any]:
    for lane_name, lane_status in lanes.items():
        if not isinstance(lane_status, dict):
            continue
        classification = lane_status.get("failure_classification")
        if not isinstance(classification, dict):
            continue
        raw_class = str(classification.get("failure_class") or "")
        try:
            failure_class = FailureClass(raw_class)
        except ValueError:
            failure_class = FailureClass.UNKNOWN_NEEDS_INVESTIGATION
        return ReceiptFailureClassification(
            failure_class=failure_class,
            reason_code=str(classification.get("reason_code") or failure_class.value),
            legacy_compat_string=str(classification.get("legacy_compat_string") or lane_status.get("reason") or ""),
            failure_present=True,
            source=source,
            lane=lane_name,
        ).to_dict()
    return no_failure_classification(source=source)


def _class_for_text(text: str) -> FailureClass:
    if any(token in text for token in ("exception", "traceback", "internal", "backend", "technical")):
        return FailureClass.TECHNICAL_FAILURE
    if any(token in text for token in ("policy", "forbidden", "not allowed", "disallowed", "safety_blocked")):
        return FailureClass.POLICY_BLOCKED
    if any(token in text for token in ("approval", "human", "britton", "manual decision")):
        return FailureClass.HUMAN_APPROVAL_REQUIRED
    if any(token in text for token in ("api_escalation", "escalation_recommended", "cloud route recommended")):
        return FailureClass.API_ESCALATION_RECOMMENDED
    if any(token in text for token in ("ambiguous", "ambiguity", "underspecified", "unclear prompt")):
        return FailureClass.PROMPT_AMBIGUITY
    if any(token in text for token in ("format", "schema", "jsondecode", "json_decode", "not_json", "invalid output", "parser", "contract_rejected", "no_action_json")):
        return FailureClass.MODEL_FORMATTING_FAILURE
    if any(token in text for token in ("validator", "verification", "verifier", "deterministic", "functional_verifier", "browser_verifier")):
        return FailureClass.VALIDATOR_FAILURE
    if any(token in text for token in ("evidence", "receipt_missing", "missing evidence", "source missing", "not found")):
        return FailureClass.EVIDENCE_MISSING
    if any(token in text for token in ("empty search", "no search results", "search_provider_empty", "result_count 0")):
        return FailureClass.SEARCH_PROVIDER_EMPTY
    if any(token in text for token in ("searxng", "scout", "search provider", "search_provider", "web search")):
        return FailureClass.SEARCH_PROVIDER_FAILURE
    if any(token in text for token in ("timeout", "resource", "memory", "disk", "too many", "pressure", "rate_limited")):
        return FailureClass.RESOURCE_PRESSURE
    if any(token in text for token in ("unavailable", "connection", "http", "service down", "provider", "ollama_inventory", "missing_from_local_ollama_inventory")):
        return FailureClass.SERVICE_UNAVAILABLE
    if any(token in text for token in ("environment", "dependency", "missing module", "venv", "path", "config_blocked", "configured")):
        return FailureClass.ENVIRONMENT_FAILURE
    if any(token in text for token in ("bridge", "worker", "consumer_event", "trace", "handoff")):
        return FailureClass.BRIDGE_INTEGRATION_FAILURE
    if any(token in text for token in ("route", "router", "target_missing", "unsafe target")):
        return FailureClass.ROUTING_FAILURE
    if any(token in text for token in ("tool", "subprocess", "command", "process", "git_status")):
        return FailureClass.TOOL_FAILURE
    if any(token in text for token in ("capability", "cannot", "unable", "insufficient reasoning", "repeated inability")):
        return FailureClass.MODEL_CAPABILITY_LIMIT
    if any(token in text for token in ("local_model_insufficient", "local model insufficient")):
        return FailureClass.LOCAL_MODEL_INSUFFICIENT
    return FailureClass.UNKNOWN_NEEDS_INVESTIGATION
