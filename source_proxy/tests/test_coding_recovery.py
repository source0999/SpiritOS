from __future__ import annotations

import copy
import hashlib

import pytest

from source_proxy.coding.recovery import (
    AUTHORIZED_CLAIM_CEILING,
    FALLBACK_SUCCESS_CLAIM_CEILING,
    FAILED_CLAIM_CEILING,
    RECOVERY_PARTICIPANT_SCHEMA,
    RETRY_SUCCESS_CLAIM_CEILING,
    ControlledRecoveryError,
    ControlledRecoveryLineage,
    RecoveryPolicy,
    build_failed_participant_event,
    controlled_recovery_record_sha256,
)


T0 = "2026-07-17T20:00:00Z"
T1 = "2026-07-17T20:00:01Z"
T2 = "2026-07-17T20:00:02Z"
T3 = "2026-07-17T20:00:03Z"
T4 = "2026-07-17T20:00:04Z"
T5 = "2026-07-17T20:00:05Z"


def _hash(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode()).hexdigest()}"


def _participant(
    *,
    passed: bool,
    attempt_id: str,
    provider: str,
    model: str,
    invocation_id: str,
    output_id: str,
    output_value: str,
    run_id: str = "run-1",
    task_id: str = "task-1",
    role: str = "coding-executor",
    lane_id: str = "coder",
    input_sha256: str | None = None,
    started_at: str = T0,
    completed_at: str = T1,
) -> dict:
    return {
        "schema_version": RECOVERY_PARTICIPANT_SCHEMA,
        "role": role,
        "lane_id": lane_id,
        "run_id": run_id,
        "task_id": task_id,
        "attempt_id": attempt_id,
        "invocation_id": invocation_id,
        "output_id": output_id,
        "provider": provider,
        "model": model,
        "input_sha256": input_sha256 or _hash("same-approved-input"),
        "output_sha256": _hash(output_value),
        "artifact_sha256": _hash("replacement-artifact") if passed else None,
        "result_id": "replacement-result-1" if passed else None,
        "error_code": None if passed else "provider_timeout",
        "error_message": None if passed else "Provider timed out after 30 seconds.",
        "started_at": started_at,
        "completed_at": completed_at,
        "passed": passed,
    }


def _failure_pair() -> tuple[dict, dict]:
    participant = _participant(
        passed=False,
        attempt_id="attempt-primary",
        provider="ollama",
        model="qwen2.5-coder:7b",
        invocation_id="invocation-primary",
        output_id="output-primary-failure",
        output_value="provider-timeout-record",
    )
    event = build_failed_participant_event(
        participant,
        parent_event_id="event-before-provider-call",
        event_id="event-primary-failed",
        recorded_at=T2,
    )
    return event, participant


def _fallback_authorization() -> ControlledRecoveryLineage:
    event, participant = _failure_pair()
    return ControlledRecoveryLineage.authorize(
        failed_event=event,
        failed_participant=participant,
        policy=RecoveryPolicy(
            allow_fallback=True,
            allowed_replacement_routes=(("litellm", "gpt-5-mini"),),
        ),
        decision="fallback",
        replacement_attempt_id="attempt-fallback",
        replacement_provider="litellm",
        replacement_model="gpt-5-mini",
        recovery_id="recovery-1",
        decision_event_id="event-recovery-decision",
        replacement_start_event_id="event-fallback-started",
        recorded_at=T3,
    )


def _fallback_success() -> dict:
    return _participant(
        passed=True,
        attempt_id="attempt-fallback",
        provider="litellm",
        model="gpt-5-mini",
        invocation_id="invocation-fallback",
        output_id="output-fallback-success",
        output_value="successful-replacement-output",
        started_at=T3,
        completed_at=T4,
    )


def _reseal(payload: dict) -> dict:
    payload["record_sha256"] = controlled_recovery_record_sha256(payload)
    return payload


def test_declared_fallback_proves_one_same_run_causal_recovery() -> None:
    authorization = _fallback_authorization()
    authorized = authorization.to_payload()

    assert authorized["proof_eligible"] is False
    assert authorized["claim_ceiling_impact"] == AUTHORIZED_CLAIM_CEILING
    assert authorized["replacement"]["parent_attempt_id"] == "attempt-primary"
    assert authorized["decision"]["event"]["parent_event_id"] == "event-primary-failed"
    assert (
        authorized["replacement"]["start_event"]["parent_event_id"]
        == "event-recovery-decision"
    )

    completed = authorization.complete(
        replacement_participant=_fallback_success(),
        outcome_event_id="event-fallback-succeeded",
        recorded_at=T5,
    )
    payload = completed.require_proof_eligible()

    assert payload["state"] == "completed"
    assert payload["run_id"] == "run-1"
    assert payload["replacement"]["outcome"] == "succeeded"
    assert payload["claim_ceiling_impact"] == FALLBACK_SUCCESS_CLAIM_CEILING
    assert payload["replacement"]["outcome_event"]["parent_event_id"] == "event-fallback-started"
    assert [event["attempt_id"] for event in completed.events] == [
        "attempt-primary",
        "attempt-primary",
        "attempt-fallback",
        "attempt-fallback",
    ]
    assert ControlledRecoveryLineage.from_payload(payload).to_payload() == payload


def test_same_route_retry_has_distinct_attempt_and_bounded_claim() -> None:
    event, participant = _failure_pair()
    authorization = ControlledRecoveryLineage.authorize(
        failed_event=event,
        failed_participant=participant,
        policy=RecoveryPolicy(
            allow_retry=True,
            allowed_replacement_routes=(("ollama", "qwen2.5-coder:7b"),),
        ),
        decision="retry",
        replacement_attempt_id="attempt-retry",
        replacement_provider="ollama",
        replacement_model="qwen2.5-coder:7b",
        recorded_at=T3,
    )
    replacement = _participant(
        passed=True,
        attempt_id="attempt-retry",
        provider="ollama",
        model="qwen2.5-coder:7b",
        invocation_id="invocation-retry",
        output_id="output-retry",
        output_value="retry-success",
        started_at=T3,
        completed_at=T4,
    )

    payload = authorization.complete(
        replacement_participant=replacement,
        recorded_at=T5,
    ).require_proof_eligible()

    assert payload["decision"]["kind"] == "retry"
    assert payload["claim_ceiling_impact"] == RETRY_SUCCESS_CLAIM_CEILING


def test_failed_replacement_is_durable_but_never_proof_eligible() -> None:
    authorization = _fallback_authorization()
    replacement = _participant(
        passed=False,
        attempt_id="attempt-fallback",
        provider="litellm",
        model="gpt-5-mini",
        invocation_id="invocation-fallback-failed",
        output_id="output-fallback-failed",
        output_value="fallback-error",
        started_at=T3,
        completed_at=T4,
    )

    completed = authorization.complete(
        replacement_participant=replacement,
        recorded_at=T5,
    )
    payload = completed.to_payload()

    assert payload["replacement"]["outcome"] == "failed"
    assert payload["proof_eligible"] is False
    assert payload["claim_ceiling_impact"] == FAILED_CLAIM_CEILING
    with pytest.raises(ControlledRecoveryError, match="controlled_recovery_not_proof_eligible"):
        completed.require_proof_eligible()


@pytest.mark.parametrize(
    ("policy", "decision", "provider", "model", "reason"),
    [
        (
            RecoveryPolicy(
                allow_fallback=False,
                allowed_replacement_routes=(("litellm", "gpt-5-mini"),),
            ),
            "fallback",
            "litellm",
            "gpt-5-mini",
            "recovery_fallback_not_authorized",
        ),
        (
            RecoveryPolicy(
                allow_fallback=True,
                allowed_replacement_routes=(("other", "other-model"),),
            ),
            "fallback",
            "litellm",
            "gpt-5-mini",
            "recovery_replacement_route_not_allowlisted",
        ),
        (
            RecoveryPolicy(
                allow_fallback=True,
                allowed_replacement_routes=(("ollama", "qwen2.5-coder:7b"),),
            ),
            "fallback",
            "ollama",
            "qwen2.5-coder:7b",
            "recovery_fallback_route_not_replaced",
        ),
        (
            RecoveryPolicy(
                allow_retry=True,
                allowed_replacement_routes=(("litellm", "gpt-5-mini"),),
            ),
            "retry",
            "litellm",
            "gpt-5-mini",
            "recovery_retry_route_changed",
        ),
    ],
)
def test_recovery_decision_fails_closed(
    policy: RecoveryPolicy,
    decision: str,
    provider: str,
    model: str,
    reason: str,
) -> None:
    event, participant = _failure_pair()

    with pytest.raises(ControlledRecoveryError, match=reason):
        ControlledRecoveryLineage.authorize(
            failed_event=event,
            failed_participant=participant,
            policy=policy,
            decision=decision,
            replacement_attempt_id="attempt-replacement",
            replacement_provider=provider,
            replacement_model=model,
            recorded_at=T3,
        )


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        ("replacement_attempt_id", "attempt-primary", "recovery_replacement_attempt_not_distinct"),
        ("replacement_provider", "", "recovery_replacement_provider_missing"),
        ("replacement_model", "", "recovery_replacement_model_missing"),
    ],
)
def test_authorization_rejects_same_attempt_or_missing_replacement(
    field: str,
    value: str,
    reason: str,
) -> None:
    event, participant = _failure_pair()
    kwargs = {
        "failed_event": event,
        "failed_participant": participant,
        "policy": RecoveryPolicy(
            allow_fallback=True,
            allowed_replacement_routes=(("litellm", "gpt-5-mini"),),
        ),
        "decision": "fallback",
        "replacement_attempt_id": "attempt-fallback",
        "replacement_provider": "litellm",
        "replacement_model": "gpt-5-mini",
        "recorded_at": T3,
    }
    kwargs[field] = value

    with pytest.raises(ControlledRecoveryError, match=reason):
        ControlledRecoveryLineage.authorize(**kwargs)


def test_missing_failure_error_or_mismatched_failure_event_is_rejected() -> None:
    event, participant = _failure_pair()
    missing_error = dict(participant)
    missing_error["error_message"] = ""

    with pytest.raises(ControlledRecoveryError, match="recovery_failure_error_message_missing"):
        ControlledRecoveryLineage.authorize(
            failed_event=event,
            failed_participant=missing_error,
            policy=RecoveryPolicy(),
            decision="fallback",
            replacement_attempt_id="attempt-fallback",
            replacement_provider="litellm",
            replacement_model="gpt-5-mini",
            recorded_at=T3,
        )

    mismatched_event = copy.deepcopy(event)
    mismatched_event["detail"]["error_code"] = "copied_wrong_error"
    with pytest.raises(ControlledRecoveryError, match="recovery_failure_event_binding_mismatch"):
        ControlledRecoveryLineage.authorize(
            failed_event=mismatched_event,
            failed_participant=participant,
            policy=RecoveryPolicy(),
            decision="fallback",
            replacement_attempt_id="attempt-fallback",
            replacement_provider="litellm",
            replacement_model="gpt-5-mini",
            recorded_at=T3,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("run_id", "unrelated-run"),
        ("task_id", "unrelated-task"),
        ("attempt_id", "unrelated-attempt"),
        ("role", "unrelated-role"),
        ("lane_id", "unrelated-lane"),
        ("input_sha256", _hash("unrelated-input")),
    ],
)
def test_replacement_cannot_be_an_unrelated_rerun(field: str, value: str) -> None:
    authorization = _fallback_authorization()
    replacement = _fallback_success()
    replacement[field] = value

    with pytest.raises(ControlledRecoveryError, match="recovery_replacement_unrelated_rerun"):
        authorization.complete(replacement_participant=replacement, recorded_at=T5)


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    [
        (
            "invocation_id",
            "invocation-primary",
            "recovery_replacement_invocation_identity_reused",
        ),
        ("output_id", "output-primary-failure", "recovery_replacement_output_identity_reused"),
        (
            "output_sha256",
            _hash("provider-timeout-record"),
            "recovery_replacement_output_copied",
        ),
    ],
)
def test_replacement_cannot_copy_failed_participant_identity(
    field: str,
    value: str,
    reason: str,
) -> None:
    authorization = _fallback_authorization()
    replacement = _fallback_success()
    replacement[field] = value

    with pytest.raises(ControlledRecoveryError, match=reason):
        authorization.complete(replacement_participant=replacement, recorded_at=T5)


def test_replacement_must_use_exact_authorized_provider_and_model() -> None:
    authorization = _fallback_authorization()
    replacement = _fallback_success()
    replacement["model"] = "gpt-5-mini-unapproved"

    with pytest.raises(ControlledRecoveryError, match="recovery_replacement_route_mismatch"):
        authorization.complete(replacement_participant=replacement, recorded_at=T5)


def test_rehydration_rejects_inflated_claim_even_with_recomputed_digest() -> None:
    completed = _fallback_authorization().complete(
        replacement_participant=_fallback_success(),
        recorded_at=T5,
    )
    tampered = completed.to_payload()
    tampered["claim_ceiling_impact"] = "primary_success"
    _reseal(tampered)

    with pytest.raises(ControlledRecoveryError, match="recovery_claim_ceiling_inflated"):
        ControlledRecoveryLineage.from_payload(tampered)


def test_rehydration_rejects_broken_causal_parent_even_with_recomputed_digest() -> None:
    payload = _fallback_authorization().to_payload()
    payload["replacement"]["start_event"]["parent_event_id"] = "unrelated-event"
    _reseal(payload)

    with pytest.raises(ControlledRecoveryError, match="recovery_start_event_binding_mismatch"):
        ControlledRecoveryLineage.from_payload(payload)


def test_rehydration_rejects_completed_record_without_replacement() -> None:
    payload = _fallback_authorization().to_payload()
    payload["state"] = "completed"
    _reseal(payload)

    with pytest.raises(ControlledRecoveryError, match="recovery_completed_replacement_missing"):
        ControlledRecoveryLineage.from_payload(payload)


def test_rehydration_rejects_unknown_fields_and_digest_tampering() -> None:
    payload = _fallback_authorization().to_payload()
    with_extra = copy.deepcopy(payload)
    with_extra["untrusted_claim"] = "primary_success"
    with pytest.raises(ControlledRecoveryError, match="controlled_recovery_record_invalid"):
        ControlledRecoveryLineage.from_payload(with_extra)

    bad_digest = copy.deepcopy(payload)
    bad_digest["record_sha256"] = _hash("not-this-record")
    with pytest.raises(ControlledRecoveryError, match="controlled_recovery_record_hash_mismatch"):
        ControlledRecoveryLineage.from_payload(bad_digest)


def test_public_constructor_cannot_bypass_lineage_validation() -> None:
    with pytest.raises(ControlledRecoveryError, match="controlled_recovery_record_invalid"):
        ControlledRecoveryLineage('{"proof_eligible":true}')


def test_failure_must_have_a_prior_causal_event() -> None:
    _event, participant = _failure_pair()

    with pytest.raises(ControlledRecoveryError, match="recovery_failure_parent_event_id_missing"):
        build_failed_participant_event(
            participant,
            parent_event_id="",
            recorded_at=T2,
        )


def test_policy_payload_is_canonical_and_duplicate_routes_fail() -> None:
    policy = RecoveryPolicy(
        allow_retry=True,
        allowed_replacement_routes=(
            ("provider-b", "model-b"),
            ("provider-a", "model-a"),
        ),
    )
    assert RecoveryPolicy.from_payload(policy.to_payload()) == policy

    with pytest.raises(ControlledRecoveryError, match="recovery_policy_route_duplicate"):
        RecoveryPolicy(
            allow_retry=True,
            allowed_replacement_routes=(("provider", "model"), ("provider", "model")),
        )
