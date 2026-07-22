from __future__ import annotations

import pytest

from source_proxy.coding.runtime_lane_boundary import (
    ACKNOWLEDGEMENT_RECORD_VERSION,
    CONSUMPTION_RECORD_VERSION,
    OUTPUT_RECORD_VERSION,
    RuntimeLaneBoundary,
    RuntimeLaneBoundaryError,
    runtime_lane_artifact_hash,
)


CODER_OUTPUT = {
    "approved_diff": "diff --git a/app.py b/app.py",
    "changed_files": ["app.py"],
}
CODER_ACKNOWLEDGEMENT = {
    "approval_id": "approval-1",
    "generation": 1,
}


def _issue_coder_output(boundary: RuntimeLaneBoundary):
    return boundary.issue_output(
        lane_id="coder",
        contract_version="coding.lane-contract/v1.0.0",
        producer_invocation_id="coder-invocation-1",
        payload=CODER_OUTPUT,
    )


def test_issue_output_binds_canonical_version_invocation_payload_and_hash() -> None:
    boundary = RuntimeLaneBoundary()
    mutable_payload = {
        "approved_diff": CODER_OUTPUT["approved_diff"],
        "changed_files": ["app.py"],
    }

    output = boundary.issue_output(
        lane_id="coder",
        contract_version="coding.lane-contract/v1.0.0",
        producer_invocation_id="coder-invocation-1",
        payload=mutable_payload,
    )
    mutable_payload["changed_files"].append("later-mutation.py")

    assert output.schema_version == OUTPUT_RECORD_VERSION
    assert output.contract_version == "coding.lane-contract/v1.0.0"
    assert output.producer_invocation_id == "coder-invocation-1"
    assert output.payload == CODER_OUTPUT
    assert output.artifact_hash == runtime_lane_artifact_hash(CODER_OUTPUT)
    assert boundary.output(output.output_id) is output


@pytest.mark.parametrize(
    ("overrides", "reason_code"),
    [
        ({"lane_id": "unknown"}, "unknown_coding_lane:unknown"),
        ({"contract_version": None}, "coding_lane_contract_version_missing"),
        (
            {"contract_version": "coding.lane-contract/v2.0.0"},
            "incompatible_coding_lane_producer_version",
        ),
        ({"producer_invocation_id": ""}, "coding_lane_producer_invocation_id_missing"),
        ({"payload": {"approved_diff": "diff"}}, "malformed_coding_lane_output"),
        (
            {"payload": {**CODER_OUTPUT, "unexpected": True}},
            "malformed_coding_lane_output",
        ),
    ],
)
def test_issue_output_rejects_missing_unknown_incompatible_or_malformed_values(
    overrides: dict[str, object], reason_code: str
) -> None:
    boundary = RuntimeLaneBoundary()
    arguments: dict[str, object] = {
        "lane_id": "coder",
        "contract_version": "coding.lane-contract/v1.0.0",
        "producer_invocation_id": "coder-invocation-1",
        "payload": CODER_OUTPUT,
    }
    arguments.update(overrides)

    with pytest.raises(RuntimeLaneBoundaryError) as caught:
        boundary.issue_output(**arguments)  # type: ignore[arg-type]

    assert caught.value.reason_code.startswith(reason_code)


def test_consumer_acknowledgement_enforces_compatibility_schema_and_distinct_invocation() -> None:
    boundary = RuntimeLaneBoundary()
    output = _issue_coder_output(boundary)

    with pytest.raises(RuntimeLaneBoundaryError) as incompatible:
        boundary.record_consumer_acknowledgement(
            output_id=output.output_id,
            consumer_version="coding-reviewer/v1",
            consumer_invocation_id="reviewer-invocation-1",
            payload=CODER_ACKNOWLEDGEMENT,
        )
    assert incompatible.value.reason_code.startswith(
        "incompatible_coding_lane_consumer_version"
    )

    with pytest.raises(RuntimeLaneBoundaryError) as same_invocation:
        boundary.record_consumer_acknowledgement(
            output_id=output.output_id,
            consumer_version="coding-orchestrator/v1",
            consumer_invocation_id=output.producer_invocation_id,
            payload=CODER_ACKNOWLEDGEMENT,
        )
    assert (
        same_invocation.value.reason_code
        == "coding_lane_consumer_invocation_not_distinct"
    )

    with pytest.raises(RuntimeLaneBoundaryError) as malformed:
        boundary.record_consumer_acknowledgement(
            output_id=output.output_id,
            consumer_version="coding-orchestrator/v1",
            consumer_invocation_id="orchestrator-invocation-1",
            payload={"approval_id": "approval-1"},
        )
    assert malformed.value.reason_code.startswith(
        "malformed_coding_lane_acknowledgement"
    )

    acknowledgement = boundary.record_consumer_acknowledgement(
        output_id=output.output_id,
        consumer_version="coding-orchestrator/v1",
        consumer_invocation_id="orchestrator-invocation-1",
        payload=CODER_ACKNOWLEDGEMENT,
    )

    assert acknowledgement.schema_version == ACKNOWLEDGEMENT_RECORD_VERSION
    assert acknowledgement.output_id == output.output_id
    assert acknowledgement.artifact_hash == output.artifact_hash
    assert acknowledgement.producer_invocation_id == output.producer_invocation_id
    assert acknowledgement.consumer_invocation_id != output.producer_invocation_id
    assert acknowledgement.payload == CODER_ACKNOWLEDGEMENT


def test_acknowledgement_rejects_missing_or_unknown_output() -> None:
    boundary = RuntimeLaneBoundary()

    for output_id, reason_code in (
        ("", "coding_lane_output_id_missing"),
        ("lane-output-missing", "unknown_coding_lane_output:lane-output-missing"),
    ):
        with pytest.raises(RuntimeLaneBoundaryError) as caught:
            boundary.record_consumer_acknowledgement(
                output_id=output_id,
                consumer_version="coding-orchestrator/v1",
                consumer_invocation_id="orchestrator-invocation-1",
                payload=CODER_ACKNOWLEDGEMENT,
            )
        assert caught.value.reason_code == reason_code


def test_output_cannot_be_consumed_without_its_own_known_acknowledgement() -> None:
    boundary = RuntimeLaneBoundary()
    first = _issue_coder_output(boundary)
    second = boundary.issue_output(
        lane_id="coder",
        contract_version="coding.lane-contract/v1.0.0",
        producer_invocation_id="coder-invocation-2",
        payload=CODER_OUTPUT,
    )

    assert boundary.consumption(first.output_id) is None
    with pytest.raises(RuntimeLaneBoundaryError) as unknown_acknowledgement:
        boundary.mark_output_consumed(
            output_id=first.output_id,
            acknowledgement_id="lane-ack-missing",
        )
    assert unknown_acknowledgement.value.reason_code.startswith(
        "unknown_coding_lane_acknowledgement"
    )

    acknowledgement = boundary.record_consumer_acknowledgement(
        output_id=first.output_id,
        consumer_version="coding-executor/v1",
        consumer_invocation_id="executor-invocation-1",
        payload=CODER_ACKNOWLEDGEMENT,
    )
    assert boundary.consumption(first.output_id) is None

    with pytest.raises(RuntimeLaneBoundaryError) as wrong_output:
        boundary.mark_output_consumed(
            output_id=second.output_id,
            acknowledgement_id=acknowledgement.acknowledgement_id,
        )
    assert (
        wrong_output.value.reason_code
        == "coding_lane_acknowledgement_output_mismatch"
    )

    consumption = boundary.mark_output_consumed(
        output_id=first.output_id,
        acknowledgement_id=acknowledgement.acknowledgement_id,
    )

    assert consumption.schema_version == CONSUMPTION_RECORD_VERSION
    assert consumption.output_id == first.output_id
    assert consumption.acknowledgement_id == acknowledgement.acknowledgement_id
    assert consumption.artifact_hash == first.artifact_hash
    assert boundary.consumption(first.output_id) is consumption


def test_required_outputs_fail_closed_until_each_output_is_consumed() -> None:
    boundary = RuntimeLaneBoundary()
    output = _issue_coder_output(boundary)

    with pytest.raises(RuntimeLaneBoundaryError) as unconsumed:
        boundary.require_outputs_consumed([output.output_id])
    assert unconsumed.value.reason_code == (
        f"required_coding_lane_output_unconsumed:{output.output_id}"
    )

    acknowledgement = boundary.record_consumer_acknowledgement(
        output_id=output.output_id,
        consumer_version="coding-executor/v1",
        consumer_invocation_id="executor-invocation-1",
        payload=CODER_ACKNOWLEDGEMENT,
    )
    consumption = boundary.mark_output_consumed(
        output_id=output.output_id,
        acknowledgement_id=acknowledgement.acknowledgement_id,
    )

    assert boundary.require_outputs_consumed([output.output_id]) == (consumption,)

    with pytest.raises(RuntimeLaneBoundaryError) as unknown:
        boundary.require_outputs_consumed(["lane-output-missing"])
    assert unknown.value.reason_code == "unknown_coding_lane_output:lane-output-missing"


def test_durable_records_rehydrate_with_exact_bindings() -> None:
    boundary = RuntimeLaneBoundary()
    output = boundary.issue_output(
        lane_id="reviewer",
        contract_version="coding.lane-contract/v1.0.0",
        producer_invocation_id="reviewer-invocation-1",
        payload={
            "passed": True,
            "findings": [],
            "blocked_reasons": [],
            "semantic_review": {},
            "semantic_review_input_sha256": None,
        },
    )
    acknowledgement = boundary.record_consumer_acknowledgement(
        output_id=output.output_id,
        consumer_version="coding-orchestrator/v1",
        consumer_invocation_id="orchestrator-consumer-1",
        payload={"approval_id": "apr_1", "generation": 1},
    )
    consumption = boundary.mark_output_consumed(
        output_id=output.output_id,
        acknowledgement_id=acknowledgement.acknowledgement_id,
    )

    restored = RuntimeLaneBoundary.from_payloads(
        outputs=[output.to_payload()],
        acknowledgements=[acknowledgement.to_payload()],
        consumptions=[consumption.to_payload()],
    )

    assert restored.output(output.output_id).to_payload() == output.to_payload()
    assert restored.acknowledgement(acknowledgement.acknowledgement_id).to_payload() == acknowledgement.to_payload()
    assert restored.consumption(output.output_id).to_payload() == consumption.to_payload()


def test_durable_rehydration_rejects_tampered_artifact_hash() -> None:
    boundary = RuntimeLaneBoundary()
    output = boundary.issue_output(
        lane_id="anti-cheat",
        contract_version="coding.lane-contract/v1.0.0",
        producer_invocation_id="anti-cheat-invocation-1",
        payload={"passed": True, "detector_ids": ["canned_output"], "violations": []},
    ).to_payload()
    output["artifact_hash"] = "sha256:" + "0" * 64

    with pytest.raises(RuntimeLaneBoundaryError, match="artifact_hash_mismatch"):
        RuntimeLaneBoundary.from_payloads(outputs=[output])
