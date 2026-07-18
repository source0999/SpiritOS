"""Fail-closed, durable recovery lineage for production coding participants.

This module does not execute a provider and does not own orchestrator storage.
It validates a real failed participant/event pair, authorizes one bounded retry
or fallback, and returns immutable payloads for the orchestrator to persist.
Only a distinct replacement attempt in the same run and causal lineage can
become proof eligible.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


CONTROLLED_RECOVERY_SCHEMA = "coding.controlled-recovery/v1"
RECOVERY_POLICY_SCHEMA = "coding.recovery-policy/v1"
RECOVERY_PARTICIPANT_SCHEMA = "coding.recovery-participant/v1"
ORCHESTRATOR_EVENT_SCHEMA = "coding.orchestrator-event/v1"

RETRY_DECISION = "retry"
FALLBACK_DECISION = "fallback"
RECOVERY_DECISIONS = frozenset({RETRY_DECISION, FALLBACK_DECISION})

AUTHORIZED_CLAIM_CEILING = "recovery_authorized_no_success_claim"
FAILED_CLAIM_CEILING = "recovery_attempt_failed_no_success_claim"
RETRY_SUCCESS_CLAIM_CEILING = "recovered_after_retry_only"
FALLBACK_SUCCESS_CLAIM_CEILING = "recovered_via_declared_fallback_only"

_SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


class ControlledRecoveryError(ValueError):
    """A controlled-recovery record failed a production invariant."""

    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclasses.dataclass(frozen=True, slots=True)
class RecoveryPolicy:
    """Server-owned allowlist for one recovery decision.

    Replacement routes are exact ``(provider, model)`` pairs.  A route must be
    allowlisted even for a same-route retry; a generic fallback permission is
    never sufficient.
    """

    allow_retry: bool = False
    allow_fallback: bool = False
    allowed_replacement_routes: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.allow_retry, bool) or not isinstance(self.allow_fallback, bool):
            raise ControlledRecoveryError("recovery_policy_flag_invalid")
        normalized: list[tuple[str, str]] = []
        for route in self.allowed_replacement_routes:
            if not isinstance(route, (tuple, list)) or len(route) != 2:
                raise ControlledRecoveryError("recovery_policy_route_invalid")
            normalized.append(
                (
                    _required_text(route[0], "recovery_policy_provider_missing"),
                    _required_text(route[1], "recovery_policy_model_missing"),
                )
            )
        if len(set(normalized)) != len(normalized):
            raise ControlledRecoveryError("recovery_policy_route_duplicate")
        object.__setattr__(self, "allowed_replacement_routes", tuple(sorted(normalized)))

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": RECOVERY_POLICY_SCHEMA,
            "allow_retry": self.allow_retry,
            "allow_fallback": self.allow_fallback,
            "allowed_replacement_routes": [
                {"provider": provider, "model": model}
                for provider, model in self.allowed_replacement_routes
            ],
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "RecoveryPolicy":
        value = _exact_mapping(
            payload,
            {
                "schema_version",
                "allow_retry",
                "allow_fallback",
                "allowed_replacement_routes",
            },
            "recovery_policy_record_invalid",
        )
        if value["schema_version"] != RECOVERY_POLICY_SCHEMA:
            raise ControlledRecoveryError("recovery_policy_schema_invalid")
        routes = value["allowed_replacement_routes"]
        if not isinstance(routes, list):
            raise ControlledRecoveryError("recovery_policy_routes_invalid")
        normalized_routes: list[tuple[str, str]] = []
        for route in routes:
            item = _exact_mapping(
                route,
                {"provider", "model"},
                "recovery_policy_route_invalid",
            )
            normalized_routes.append((item["provider"], item["model"]))
        policy = cls(
            allow_retry=value["allow_retry"],
            allow_fallback=value["allow_fallback"],
            allowed_replacement_routes=tuple(normalized_routes),
        )
        if policy.to_payload() != value:
            raise ControlledRecoveryError("recovery_policy_not_canonical")
        return policy

    def require_authorized(
        self,
        *,
        decision: str,
        failed_provider: str,
        failed_model: str,
        replacement_provider: str,
        replacement_model: str,
    ) -> None:
        if decision == RETRY_DECISION:
            if not self.allow_retry:
                raise ControlledRecoveryError("recovery_retry_not_authorized")
            if (replacement_provider, replacement_model) != (failed_provider, failed_model):
                raise ControlledRecoveryError("recovery_retry_route_changed")
        elif decision == FALLBACK_DECISION:
            if not self.allow_fallback:
                raise ControlledRecoveryError("recovery_fallback_not_authorized")
            if (replacement_provider, replacement_model) == (failed_provider, failed_model):
                raise ControlledRecoveryError("recovery_fallback_route_not_replaced")
        else:
            raise ControlledRecoveryError("recovery_decision_invalid")
        if (replacement_provider, replacement_model) not in self.allowed_replacement_routes:
            raise ControlledRecoveryError("recovery_replacement_route_not_allowlisted")


@dataclasses.dataclass(frozen=True, slots=True)
class ControlledRecoveryLineage:
    """Immutable authorization or outcome record suitable for durable storage."""

    _payload_json: str = dataclasses.field(repr=False)

    def __post_init__(self) -> None:
        """Prevent callers from bypassing ``from_payload`` validation."""

        try:
            decoded = json.loads(self._payload_json)
        except (TypeError, json.JSONDecodeError) as error:
            raise ControlledRecoveryError("controlled_recovery_json_invalid") from error
        validated = _validate_payload(decoded)
        object.__setattr__(self, "_payload_json", _canonical_json(validated))

    @property
    def payload(self) -> dict[str, Any]:
        return json.loads(self._payload_json)

    @property
    def proof_eligible(self) -> bool:
        return self.payload["proof_eligible"] is True

    @property
    def events(self) -> tuple[dict[str, Any], ...]:
        payload = self.payload
        events = [
            payload["failure"]["event"],
            payload["decision"]["event"],
            payload["replacement"]["start_event"],
        ]
        outcome = payload["replacement"]["outcome_event"]
        if outcome is not None:
            events.append(outcome)
        return tuple(events)

    def to_payload(self) -> dict[str, Any]:
        return self.payload

    @classmethod
    def authorize(
        cls,
        *,
        failed_event: Mapping[str, Any],
        failed_participant: Mapping[str, Any],
        policy: RecoveryPolicy,
        decision: str,
        replacement_attempt_id: str,
        replacement_provider: str,
        replacement_model: str,
        recovery_id: str | None = None,
        decision_event_id: str | None = None,
        replacement_start_event_id: str | None = None,
        recorded_at: str | None = None,
    ) -> "ControlledRecoveryLineage":
        """Authorize a bounded replacement only after an exact failed pair."""

        failure_event, failure_participant = _validate_failure_pair(
            failed_event,
            failed_participant,
        )
        if not isinstance(policy, RecoveryPolicy):
            raise ControlledRecoveryError("recovery_policy_required")
        decision_kind = _required_text(decision, "recovery_decision_missing")
        if decision_kind not in RECOVERY_DECISIONS:
            raise ControlledRecoveryError("recovery_decision_invalid")
        replacement_attempt = _required_text(
            replacement_attempt_id,
            "recovery_replacement_attempt_id_missing",
        )
        if replacement_attempt == failure_participant["attempt_id"]:
            raise ControlledRecoveryError("recovery_replacement_attempt_not_distinct")
        provider = _required_text(
            replacement_provider,
            "recovery_replacement_provider_missing",
        )
        model = _required_text(replacement_model, "recovery_replacement_model_missing")
        policy.require_authorized(
            decision=decision_kind,
            failed_provider=failure_participant["provider"],
            failed_model=failure_participant["model"],
            replacement_provider=provider,
            replacement_model=model,
        )

        now = _timestamp(recorded_at or _utc_now(), "recovery_recorded_at_invalid")
        if _parse_timestamp(now) < _parse_timestamp(failure_event["recorded_at"]):
            raise ControlledRecoveryError("recovery_decision_precedes_failure")
        actual_recovery_id = _required_text(
            recovery_id or f"coding-recovery-{uuid4().hex}",
            "recovery_id_missing",
        )
        actual_decision_event_id = _required_text(
            decision_event_id or f"coding-event-{uuid4().hex}",
            "recovery_decision_event_id_missing",
        )
        actual_start_event_id = _required_text(
            replacement_start_event_id or f"coding-event-{uuid4().hex}",
            "recovery_start_event_id_missing",
        )
        if len(
            {
                failure_event["event_id"],
                actual_decision_event_id,
                actual_start_event_id,
            }
        ) != 3:
            raise ControlledRecoveryError("recovery_event_identity_reused")

        policy_payload = policy.to_payload()
        policy_sha256 = _sha256_json(policy_payload)
        failed_participant_sha256 = _sha256_json(failure_participant)
        success_ceiling = _success_claim_ceiling(decision_kind)
        decision_event = _event(
            event_id=actual_decision_event_id,
            parent_event_id=failure_event["event_id"],
            run_id=failure_participant["run_id"],
            attempt_id=failure_participant["attempt_id"],
            task_id=failure_participant["task_id"],
            event_type="controlled_recovery_decision",
            lane_id=failure_participant["lane_id"],
            status_before="failed",
            status_after="recovering",
            detail={
                "recovery_id": actual_recovery_id,
                "failed_event_id": failure_event["event_id"],
                "failed_participant_sha256": failed_participant_sha256,
                "decision": decision_kind,
                "replacement_attempt_id": replacement_attempt,
                "replacement_provider": provider,
                "replacement_model": model,
                "authorized_claim_ceiling": success_ceiling,
                "policy_sha256": policy_sha256,
            },
            recorded_at=now,
        )
        start_event = _event(
            event_id=actual_start_event_id,
            parent_event_id=actual_decision_event_id,
            run_id=failure_participant["run_id"],
            attempt_id=replacement_attempt,
            task_id=failure_participant["task_id"],
            event_type="controlled_recovery_attempt_started",
            lane_id=failure_participant["lane_id"],
            status_before="recovering",
            status_after="running",
            detail={
                "recovery_id": actual_recovery_id,
                "failed_attempt_id": failure_participant["attempt_id"],
                "failed_event_id": failure_event["event_id"],
                "decision_event_id": actual_decision_event_id,
                "decision": decision_kind,
                "replacement_provider": provider,
                "replacement_model": model,
                "participant_role": failure_participant["role"],
                "input_sha256": failure_participant["input_sha256"],
            },
            recorded_at=now,
        )
        payload = {
            "schema_version": CONTROLLED_RECOVERY_SCHEMA,
            "recovery_id": actual_recovery_id,
            "state": "authorized",
            "run_id": failure_participant["run_id"],
            "task_id": failure_participant["task_id"],
            "failure": {
                "attempt_id": failure_participant["attempt_id"],
                "event": failure_event,
                "participant": failure_participant,
                "participant_sha256": failed_participant_sha256,
            },
            "decision": {
                "kind": decision_kind,
                "event": decision_event,
                "policy": policy_payload,
                "policy_sha256": policy_sha256,
            },
            "replacement": {
                "attempt_id": replacement_attempt,
                "parent_attempt_id": failure_participant["attempt_id"],
                "provider": provider,
                "model": model,
                "start_event": start_event,
                "participant": None,
                "participant_sha256": None,
                "outcome_event": None,
                "outcome": "pending",
            },
            "claim_ceiling_impact": AUTHORIZED_CLAIM_CEILING,
            "proof_eligible": False,
            "created_at": now,
            "updated_at": now,
        }
        return cls.from_payload(_seal(payload))

    def complete(
        self,
        *,
        replacement_participant: Mapping[str, Any],
        outcome_event_id: str | None = None,
        recorded_at: str | None = None,
    ) -> "ControlledRecoveryLineage":
        """Bind one actual replacement outcome to this authorization."""

        payload = self.payload
        if payload["state"] != "authorized":
            raise ControlledRecoveryError("recovery_already_completed")
        participant = _validate_participant(replacement_participant)
        _validate_replacement_participant(payload, participant)
        now = _timestamp(recorded_at or _utc_now(), "recovery_outcome_recorded_at_invalid")
        if _parse_timestamp(now) < _parse_timestamp(participant["completed_at"]):
            raise ControlledRecoveryError("recovery_outcome_precedes_participant_completion")
        actual_outcome_event_id = _required_text(
            outcome_event_id or f"coding-event-{uuid4().hex}",
            "recovery_outcome_event_id_missing",
        )
        prior_event_ids = {event["event_id"] for event in self.events}
        if actual_outcome_event_id in prior_event_ids:
            raise ControlledRecoveryError("recovery_event_identity_reused")

        participant_sha256 = _sha256_json(participant)
        succeeded = participant["passed"] is True
        event_type = (
            "controlled_recovery_attempt_succeeded"
            if succeeded
            else "controlled_recovery_attempt_failed"
        )
        outcome_event = _event(
            event_id=actual_outcome_event_id,
            parent_event_id=payload["replacement"]["start_event"]["event_id"],
            run_id=payload["run_id"],
            attempt_id=payload["replacement"]["attempt_id"],
            task_id=payload["task_id"],
            event_type=event_type,
            lane_id=payload["failure"]["participant"]["lane_id"],
            status_before="running",
            status_after="completed" if succeeded else "failed",
            detail={
                "recovery_id": payload["recovery_id"],
                "participant_invocation_id": participant["invocation_id"],
                "participant_output_id": participant["output_id"],
                "participant_sha256": participant_sha256,
                "provider": participant["provider"],
                "model": participant["model"],
                "result_id": participant["result_id"],
                "artifact_sha256": participant["artifact_sha256"],
                "error_code": participant["error_code"],
                "error_message": participant["error_message"],
            },
            recorded_at=now,
        )
        replacement = dict(payload["replacement"])
        replacement.update(
            {
                "participant": participant,
                "participant_sha256": participant_sha256,
                "outcome_event": outcome_event,
                "outcome": "succeeded" if succeeded else "failed",
            }
        )
        payload.update(
            {
                "state": "completed",
                "replacement": replacement,
                "claim_ceiling_impact": (
                    _success_claim_ceiling(payload["decision"]["kind"])
                    if succeeded
                    else FAILED_CLAIM_CEILING
                ),
                "proof_eligible": succeeded,
                "updated_at": now,
            }
        )
        payload.pop("record_sha256", None)
        return self.from_payload(_seal(payload))

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "ControlledRecoveryLineage":
        return cls(_canonical_json(payload))

    def require_proof_eligible(self) -> dict[str, Any]:
        payload = self.payload
        if payload["proof_eligible"] is not True:
            raise ControlledRecoveryError("controlled_recovery_not_proof_eligible")
        return payload


def build_failed_participant_event(
    participant: Mapping[str, Any],
    *,
    parent_event_id: str,
    event_id: str | None = None,
    recorded_at: str | None = None,
) -> dict[str, Any]:
    """Create the exact orchestrator event required to authorize recovery."""

    record = _validate_participant(participant, expected_passed=False)
    now = _timestamp(recorded_at or _utc_now(), "recovery_failure_recorded_at_invalid")
    if _parse_timestamp(now) < _parse_timestamp(record["completed_at"]):
        raise ControlledRecoveryError("recovery_failure_event_precedes_participant_completion")
    return _event(
        event_id=_required_text(
            event_id or f"coding-event-{uuid4().hex}",
            "recovery_failure_event_id_missing",
        ),
        parent_event_id=_required_text(
            parent_event_id,
            "recovery_failure_parent_event_id_missing",
        ),
        run_id=record["run_id"],
        attempt_id=record["attempt_id"],
        task_id=record["task_id"],
        event_type="participant_failed",
        lane_id=record["lane_id"],
        status_before="running",
        status_after="failed",
        detail={
            "participant_role": record["role"],
            "participant_invocation_id": record["invocation_id"],
            "participant_output_id": record["output_id"],
            "participant_record_sha256": _sha256_json(record),
            "provider": record["provider"],
            "model": record["model"],
            "input_sha256": record["input_sha256"],
            "error_code": record["error_code"],
            "error_message": record["error_message"],
        },
        recorded_at=now,
    )


def controlled_recovery_record_sha256(payload: Mapping[str, Any]) -> str:
    """Return the canonical record digest, excluding its digest field."""

    if not isinstance(payload, Mapping):
        raise ControlledRecoveryError("controlled_recovery_record_invalid")
    unsigned = dict(payload)
    unsigned.pop("record_sha256", None)
    return _sha256_json(unsigned)


def _validate_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    value = _exact_mapping(
        payload,
        {
            "schema_version",
            "recovery_id",
            "state",
            "run_id",
            "task_id",
            "failure",
            "decision",
            "replacement",
            "claim_ceiling_impact",
            "proof_eligible",
            "created_at",
            "updated_at",
            "record_sha256",
        },
        "controlled_recovery_record_invalid",
    )
    if value["schema_version"] != CONTROLLED_RECOVERY_SCHEMA:
        raise ControlledRecoveryError("controlled_recovery_schema_invalid")
    recovery_id = _required_text(value["recovery_id"], "recovery_id_missing")
    state = _required_text(value["state"], "recovery_state_missing")
    if state not in {"authorized", "completed"}:
        raise ControlledRecoveryError("recovery_state_invalid")
    run_id = _required_text(value["run_id"], "recovery_run_id_missing")
    task_id = _required_text(value["task_id"], "recovery_task_id_missing")
    created_at = _timestamp(value["created_at"], "recovery_created_at_invalid")
    updated_at = _timestamp(value["updated_at"], "recovery_updated_at_invalid")
    if _parse_timestamp(updated_at) < _parse_timestamp(created_at):
        raise ControlledRecoveryError("recovery_updated_before_created")
    if not isinstance(value["proof_eligible"], bool):
        raise ControlledRecoveryError("recovery_proof_eligible_invalid")

    failure = _exact_mapping(
        value["failure"],
        {"attempt_id", "event", "participant", "participant_sha256"},
        "recovery_failure_record_invalid",
    )
    failure_event, failure_participant = _validate_failure_pair(
        failure["event"],
        failure["participant"],
    )
    if failure["attempt_id"] != failure_participant["attempt_id"]:
        raise ControlledRecoveryError("recovery_failed_attempt_binding_mismatch")
    if failure["participant_sha256"] != _sha256_json(failure_participant):
        raise ControlledRecoveryError("recovery_failed_participant_hash_mismatch")
    if (run_id, task_id) != (
        failure_participant["run_id"],
        failure_participant["task_id"],
    ):
        raise ControlledRecoveryError("recovery_failure_identity_mismatch")

    decision_record = _exact_mapping(
        value["decision"],
        {"kind", "event", "policy", "policy_sha256"},
        "recovery_decision_record_invalid",
    )
    decision_kind = _required_text(decision_record["kind"], "recovery_decision_missing")
    if decision_kind not in RECOVERY_DECISIONS:
        raise ControlledRecoveryError("recovery_decision_invalid")
    policy = RecoveryPolicy.from_payload(decision_record["policy"])
    if decision_record["policy_sha256"] != _sha256_json(policy.to_payload()):
        raise ControlledRecoveryError("recovery_policy_hash_mismatch")

    replacement = _exact_mapping(
        value["replacement"],
        {
            "attempt_id",
            "parent_attempt_id",
            "provider",
            "model",
            "start_event",
            "participant",
            "participant_sha256",
            "outcome_event",
            "outcome",
        },
        "recovery_replacement_record_invalid",
    )
    replacement_attempt = _required_text(
        replacement["attempt_id"],
        "recovery_replacement_attempt_id_missing",
    )
    if replacement_attempt == failure_participant["attempt_id"]:
        raise ControlledRecoveryError("recovery_replacement_attempt_not_distinct")
    if replacement["parent_attempt_id"] != failure_participant["attempt_id"]:
        raise ControlledRecoveryError("recovery_replacement_parent_attempt_mismatch")
    replacement_provider = _required_text(
        replacement["provider"],
        "recovery_replacement_provider_missing",
    )
    replacement_model = _required_text(
        replacement["model"],
        "recovery_replacement_model_missing",
    )
    policy.require_authorized(
        decision=decision_kind,
        failed_provider=failure_participant["provider"],
        failed_model=failure_participant["model"],
        replacement_provider=replacement_provider,
        replacement_model=replacement_model,
    )

    decision_event = _validate_event(decision_record["event"])
    start_event = _validate_event(replacement["start_event"])
    _validate_decision_event(
        decision_event,
        recovery_id=recovery_id,
        failure_event=failure_event,
        failure_participant=failure_participant,
        participant_sha256=failure["participant_sha256"],
        decision=decision_kind,
        replacement_attempt_id=replacement_attempt,
        replacement_provider=replacement_provider,
        replacement_model=replacement_model,
        policy_sha256=decision_record["policy_sha256"],
    )
    _validate_start_event(
        start_event,
        recovery_id=recovery_id,
        failure_event=failure_event,
        failure_participant=failure_participant,
        decision_event=decision_event,
        decision=decision_kind,
        replacement_attempt_id=replacement_attempt,
        replacement_provider=replacement_provider,
        replacement_model=replacement_model,
    )
    if _parse_timestamp(decision_event["recorded_at"]) < _parse_timestamp(
        failure_event["recorded_at"]
    ):
        raise ControlledRecoveryError("recovery_decision_precedes_failure")
    if _parse_timestamp(start_event["recorded_at"]) < _parse_timestamp(
        decision_event["recorded_at"]
    ):
        raise ControlledRecoveryError("recovery_attempt_precedes_decision")
    if created_at != decision_event["recorded_at"] or created_at != start_event["recorded_at"]:
        raise ControlledRecoveryError("recovery_created_at_event_binding_mismatch")
    if len(
        {
            failure_event["event_id"],
            decision_event["event_id"],
            start_event["event_id"],
        }
    ) != 3:
        raise ControlledRecoveryError("recovery_event_identity_reused")

    if state == "authorized":
        if any(
            replacement[key] is not None
            for key in ("participant", "participant_sha256", "outcome_event")
        ) or replacement["outcome"] != "pending":
            raise ControlledRecoveryError("recovery_authorization_outcome_present")
        if value["claim_ceiling_impact"] != AUTHORIZED_CLAIM_CEILING:
            raise ControlledRecoveryError("recovery_claim_ceiling_inflated")
        if value["proof_eligible"] is not False:
            raise ControlledRecoveryError("recovery_authorization_marked_proof_eligible")
        if updated_at != created_at:
            raise ControlledRecoveryError("recovery_authorization_updated_at_invalid")
    else:
        if replacement["participant"] is None or replacement["outcome_event"] is None:
            raise ControlledRecoveryError("recovery_completed_replacement_missing")
        participant = _validate_participant(replacement["participant"])
        _validate_replacement_participant(value, participant)
        if replacement["participant_sha256"] != _sha256_json(participant):
            raise ControlledRecoveryError("recovery_replacement_participant_hash_mismatch")
        outcome_event = _validate_event(replacement["outcome_event"])
        _validate_outcome_event(
            outcome_event,
            recovery_id=recovery_id,
            start_event=start_event,
            participant=participant,
            participant_sha256=replacement["participant_sha256"],
        )
        if _parse_timestamp(participant["started_at"]) < _parse_timestamp(
            start_event["recorded_at"]
        ):
            raise ControlledRecoveryError("recovery_participant_precedes_attempt")
        if _parse_timestamp(outcome_event["recorded_at"]) < _parse_timestamp(
            participant["completed_at"]
        ):
            raise ControlledRecoveryError("recovery_outcome_precedes_participant_completion")
        if updated_at != outcome_event["recorded_at"]:
            raise ControlledRecoveryError("recovery_updated_at_event_binding_mismatch")
        if outcome_event["event_id"] in {
            failure_event["event_id"],
            decision_event["event_id"],
            start_event["event_id"],
        }:
            raise ControlledRecoveryError("recovery_event_identity_reused")
        expected_outcome = "succeeded" if participant["passed"] else "failed"
        if replacement["outcome"] != expected_outcome:
            raise ControlledRecoveryError("recovery_outcome_binding_mismatch")
        expected_ceiling = (
            _success_claim_ceiling(decision_kind)
            if participant["passed"]
            else FAILED_CLAIM_CEILING
        )
        if value["claim_ceiling_impact"] != expected_ceiling:
            raise ControlledRecoveryError("recovery_claim_ceiling_inflated")
        if value["proof_eligible"] is not participant["passed"]:
            raise ControlledRecoveryError("recovery_proof_eligibility_mismatch")

    if value["record_sha256"] != controlled_recovery_record_sha256(value):
        raise ControlledRecoveryError("controlled_recovery_record_hash_mismatch")
    return json.loads(_canonical_json(value))


def _validate_failure_pair(
    event: Mapping[str, Any],
    participant: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    record = _validate_participant(participant, expected_passed=False)
    failure_event = _validate_event(event)
    expected_detail = {
        "participant_role": record["role"],
        "participant_invocation_id": record["invocation_id"],
        "participant_output_id": record["output_id"],
        "participant_record_sha256": _sha256_json(record),
        "provider": record["provider"],
        "model": record["model"],
        "input_sha256": record["input_sha256"],
        "error_code": record["error_code"],
        "error_message": record["error_message"],
    }
    if failure_event["event_type"] != "participant_failed":
        raise ControlledRecoveryError("recovery_failure_event_type_invalid")
    if failure_event["parent_event_id"] is None:
        raise ControlledRecoveryError("recovery_failure_parent_event_id_missing")
    if (failure_event["status_before"], failure_event["status_after"]) != (
        "running",
        "failed",
    ):
        raise ControlledRecoveryError("recovery_failure_event_status_invalid")
    if failure_event["detail"] != expected_detail:
        raise ControlledRecoveryError("recovery_failure_event_binding_mismatch")
    if (
        failure_event["run_id"],
        failure_event["attempt_id"],
        failure_event["task_id"],
        failure_event["lane_id"],
    ) != (
        record["run_id"],
        record["attempt_id"],
        record["task_id"],
        record["lane_id"],
    ):
        raise ControlledRecoveryError("recovery_failure_event_identity_mismatch")
    if _parse_timestamp(failure_event["recorded_at"]) < _parse_timestamp(
        record["completed_at"]
    ):
        raise ControlledRecoveryError("recovery_failure_event_precedes_participant_completion")
    return failure_event, record


def _validate_replacement_participant(
    recovery: Mapping[str, Any],
    participant: Mapping[str, Any],
) -> None:
    failure = recovery["failure"]["participant"]
    replacement = recovery["replacement"]
    if (
        participant["run_id"],
        participant["task_id"],
        participant["attempt_id"],
        participant["role"],
        participant["lane_id"],
        participant["input_sha256"],
    ) != (
        recovery["run_id"],
        recovery["task_id"],
        replacement["attempt_id"],
        failure["role"],
        failure["lane_id"],
        failure["input_sha256"],
    ):
        raise ControlledRecoveryError("recovery_replacement_unrelated_rerun")
    if (participant["provider"], participant["model"]) != (
        replacement["provider"],
        replacement["model"],
    ):
        raise ControlledRecoveryError("recovery_replacement_route_mismatch")
    if participant["attempt_id"] == failure["attempt_id"]:
        raise ControlledRecoveryError("recovery_replacement_attempt_not_distinct")
    if participant["invocation_id"] == failure["invocation_id"]:
        raise ControlledRecoveryError("recovery_replacement_invocation_identity_reused")
    if participant["output_id"] == failure["output_id"]:
        raise ControlledRecoveryError("recovery_replacement_output_identity_reused")
    if participant["output_sha256"] == failure["output_sha256"]:
        raise ControlledRecoveryError("recovery_replacement_output_copied")


def _validate_participant(
    participant: Mapping[str, Any],
    *,
    expected_passed: bool | None = None,
) -> dict[str, Any]:
    value = _exact_mapping(
        participant,
        {
            "schema_version",
            "role",
            "lane_id",
            "run_id",
            "task_id",
            "attempt_id",
            "invocation_id",
            "output_id",
            "provider",
            "model",
            "input_sha256",
            "output_sha256",
            "artifact_sha256",
            "result_id",
            "error_code",
            "error_message",
            "started_at",
            "completed_at",
            "passed",
        },
        "recovery_participant_record_invalid",
    )
    if value["schema_version"] != RECOVERY_PARTICIPANT_SCHEMA:
        raise ControlledRecoveryError("recovery_participant_schema_invalid")
    for key in (
        "role",
        "lane_id",
        "run_id",
        "task_id",
        "attempt_id",
        "invocation_id",
        "output_id",
        "provider",
        "model",
    ):
        _required_text(value[key], f"recovery_participant_{key}_missing")
    _sha256(value["input_sha256"], "recovery_participant_input_hash_invalid")
    _sha256(value["output_sha256"], "recovery_participant_output_hash_invalid")
    started = _timestamp(value["started_at"], "recovery_participant_started_at_invalid")
    completed = _timestamp(value["completed_at"], "recovery_participant_completed_at_invalid")
    if _parse_timestamp(completed) < _parse_timestamp(started):
        raise ControlledRecoveryError("recovery_participant_completed_before_started")
    if not isinstance(value["passed"], bool):
        raise ControlledRecoveryError("recovery_participant_passed_invalid")
    if expected_passed is not None and value["passed"] is not expected_passed:
        raise ControlledRecoveryError("recovery_failed_participant_not_failed")
    if value["passed"]:
        _required_text(value["result_id"], "recovery_success_result_id_missing")
        _sha256(value["artifact_sha256"], "recovery_success_artifact_hash_missing")
        if value["error_code"] is not None or value["error_message"] is not None:
            raise ControlledRecoveryError("recovery_success_contains_error")
    else:
        _required_text(value["error_code"], "recovery_failure_error_code_missing")
        _required_text(value["error_message"], "recovery_failure_error_message_missing")
        if value["result_id"] is not None:
            raise ControlledRecoveryError("recovery_failure_contains_result")
        if value["artifact_sha256"] is not None:
            _sha256(value["artifact_sha256"], "recovery_failure_artifact_hash_invalid")
    return json.loads(_canonical_json(value))


def _validate_decision_event(
    event: Mapping[str, Any],
    *,
    recovery_id: str,
    failure_event: Mapping[str, Any],
    failure_participant: Mapping[str, Any],
    participant_sha256: str,
    decision: str,
    replacement_attempt_id: str,
    replacement_provider: str,
    replacement_model: str,
    policy_sha256: str,
) -> None:
    expected_detail = {
        "recovery_id": recovery_id,
        "failed_event_id": failure_event["event_id"],
        "failed_participant_sha256": participant_sha256,
        "decision": decision,
        "replacement_attempt_id": replacement_attempt_id,
        "replacement_provider": replacement_provider,
        "replacement_model": replacement_model,
        "authorized_claim_ceiling": _success_claim_ceiling(decision),
        "policy_sha256": policy_sha256,
    }
    if (
        event["parent_event_id"],
        event["run_id"],
        event["attempt_id"],
        event["task_id"],
        event["event_type"],
        event["lane_id"],
        event["status_before"],
        event["status_after"],
        event["detail"],
    ) != (
        failure_event["event_id"],
        failure_participant["run_id"],
        failure_participant["attempt_id"],
        failure_participant["task_id"],
        "controlled_recovery_decision",
        failure_participant["lane_id"],
        "failed",
        "recovering",
        expected_detail,
    ):
        raise ControlledRecoveryError("recovery_decision_event_binding_mismatch")


def _validate_start_event(
    event: Mapping[str, Any],
    *,
    recovery_id: str,
    failure_event: Mapping[str, Any],
    failure_participant: Mapping[str, Any],
    decision_event: Mapping[str, Any],
    decision: str,
    replacement_attempt_id: str,
    replacement_provider: str,
    replacement_model: str,
) -> None:
    expected_detail = {
        "recovery_id": recovery_id,
        "failed_attempt_id": failure_participant["attempt_id"],
        "failed_event_id": failure_event["event_id"],
        "decision_event_id": decision_event["event_id"],
        "decision": decision,
        "replacement_provider": replacement_provider,
        "replacement_model": replacement_model,
        "participant_role": failure_participant["role"],
        "input_sha256": failure_participant["input_sha256"],
    }
    if (
        event["parent_event_id"],
        event["run_id"],
        event["attempt_id"],
        event["task_id"],
        event["event_type"],
        event["lane_id"],
        event["status_before"],
        event["status_after"],
        event["detail"],
    ) != (
        decision_event["event_id"],
        failure_participant["run_id"],
        replacement_attempt_id,
        failure_participant["task_id"],
        "controlled_recovery_attempt_started",
        failure_participant["lane_id"],
        "recovering",
        "running",
        expected_detail,
    ):
        raise ControlledRecoveryError("recovery_start_event_binding_mismatch")


def _validate_outcome_event(
    event: Mapping[str, Any],
    *,
    recovery_id: str,
    start_event: Mapping[str, Any],
    participant: Mapping[str, Any],
    participant_sha256: str,
) -> None:
    succeeded = participant["passed"] is True
    expected_detail = {
        "recovery_id": recovery_id,
        "participant_invocation_id": participant["invocation_id"],
        "participant_output_id": participant["output_id"],
        "participant_sha256": participant_sha256,
        "provider": participant["provider"],
        "model": participant["model"],
        "result_id": participant["result_id"],
        "artifact_sha256": participant["artifact_sha256"],
        "error_code": participant["error_code"],
        "error_message": participant["error_message"],
    }
    if (
        event["parent_event_id"],
        event["run_id"],
        event["attempt_id"],
        event["task_id"],
        event["event_type"],
        event["lane_id"],
        event["status_before"],
        event["status_after"],
        event["detail"],
    ) != (
        start_event["event_id"],
        participant["run_id"],
        participant["attempt_id"],
        participant["task_id"],
        (
            "controlled_recovery_attempt_succeeded"
            if succeeded
            else "controlled_recovery_attempt_failed"
        ),
        participant["lane_id"],
        "running",
        "completed" if succeeded else "failed",
        expected_detail,
    ):
        raise ControlledRecoveryError("recovery_outcome_event_binding_mismatch")


def _validate_event(event: Mapping[str, Any]) -> dict[str, Any]:
    value = _exact_mapping(
        event,
        {
            "schema_version",
            "event_id",
            "parent_event_id",
            "run_id",
            "attempt_id",
            "task_id",
            "event_type",
            "lane_id",
            "status_before",
            "status_after",
            "detail",
            "recorded_at",
        },
        "recovery_event_record_invalid",
    )
    if value["schema_version"] != ORCHESTRATOR_EVENT_SCHEMA:
        raise ControlledRecoveryError("recovery_event_schema_invalid")
    for key in (
        "event_id",
        "run_id",
        "attempt_id",
        "task_id",
        "event_type",
        "lane_id",
        "status_before",
        "status_after",
    ):
        _required_text(value[key], f"recovery_event_{key}_missing")
    _optional_text(value["parent_event_id"], "recovery_event_parent_event_id_invalid")
    if value["parent_event_id"] == value["event_id"]:
        raise ControlledRecoveryError("recovery_event_parent_self_reference")
    if not isinstance(value["detail"], Mapping):
        raise ControlledRecoveryError("recovery_event_detail_invalid")
    _timestamp(value["recorded_at"], "recovery_event_recorded_at_invalid")
    return json.loads(_canonical_json(value))


def _event(
    *,
    event_id: str,
    parent_event_id: str | None,
    run_id: str,
    attempt_id: str,
    task_id: str,
    event_type: str,
    lane_id: str,
    status_before: str,
    status_after: str,
    detail: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": ORCHESTRATOR_EVENT_SCHEMA,
        "event_id": event_id,
        "parent_event_id": parent_event_id,
        "run_id": run_id,
        "attempt_id": attempt_id,
        "task_id": task_id,
        "event_type": event_type,
        "lane_id": lane_id,
        "status_before": status_before,
        "status_after": status_after,
        "detail": json.loads(_canonical_json(detail)),
        "recorded_at": recorded_at,
    }


def _success_claim_ceiling(decision: str) -> str:
    if decision == RETRY_DECISION:
        return RETRY_SUCCESS_CLAIM_CEILING
    if decision == FALLBACK_DECISION:
        return FALLBACK_SUCCESS_CLAIM_CEILING
    raise ControlledRecoveryError("recovery_decision_invalid")


def _seal(payload: Mapping[str, Any]) -> dict[str, Any]:
    value = json.loads(_canonical_json(payload))
    value["record_sha256"] = controlled_recovery_record_sha256(value)
    return value


def _exact_mapping(
    value: Any,
    keys: set[str],
    reason_code: str,
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise ControlledRecoveryError(reason_code)
    return dict(value)


def _required_text(value: Any, reason_code: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ControlledRecoveryError(reason_code)
    return value


def _optional_text(value: Any, reason_code: str) -> str | None:
    if value is None:
        return None
    return _required_text(value, reason_code)


def _sha256(value: Any, reason_code: str) -> str:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise ControlledRecoveryError(reason_code)
    return value


def _timestamp(value: Any, reason_code: str) -> str:
    text = _required_text(value, reason_code)
    try:
        parsed = _parse_timestamp(text)
    except ValueError as error:
        raise ControlledRecoveryError(reason_code) from error
    if parsed.tzinfo is None:
        raise ControlledRecoveryError(reason_code)
    return text


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        raise ControlledRecoveryError("controlled_recovery_json_invalid") from error


def _sha256_json(value: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical_json(value).encode('utf-8')).hexdigest()}"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
