"""Runtime enforcement for versioned coding-lane producer/consumer records.

The canonical lane catalog describes payload schemas and compatible consumers.
This module applies those declarations to live records without owning task or
orchestrator lifecycle state.  Records are immutable and serializable so a
durable owner can persist them when the production orchestrator is integrated.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from uuid import uuid4

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from source_proxy.contracts.coding_lane_contracts import canonical_coding_lane_contracts


OUTPUT_RECORD_VERSION = "coding.runtime-lane-output/v1"
ACKNOWLEDGEMENT_RECORD_VERSION = "coding.runtime-lane-acknowledgement/v1"
CONSUMPTION_RECORD_VERSION = "coding.runtime-lane-consumption/v1"


class RuntimeLaneBoundaryError(ValueError):
    """A runtime lane record failed its producer/consumer boundary."""

    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


@dataclass(frozen=True, slots=True)
class RuntimeLaneOutputRecord:
    """An immutable, contract-versioned result from one producer invocation."""

    schema_version: str
    output_id: str
    lane_id: str
    contract_version: str
    producer_invocation_id: str
    artifact_hash: str
    issued_at: str
    _payload_json: str = field(repr=False)

    @property
    def payload(self) -> dict[str, Any]:
        return json.loads(self._payload_json)

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "output_id": self.output_id,
            "lane_id": self.lane_id,
            "contract_version": self.contract_version,
            "producer_invocation_id": self.producer_invocation_id,
            "artifact_hash": self.artifact_hash,
            "issued_at": self.issued_at,
            "payload": self.payload,
        }


@dataclass(frozen=True, slots=True)
class RuntimeLaneAcknowledgementRecord:
    """A consumer-owned acknowledgement of one exact lane output artifact."""

    schema_version: str
    acknowledgement_id: str
    output_id: str
    lane_id: str
    contract_version: str
    producer_invocation_id: str
    artifact_hash: str
    consumer_version: str
    consumer_invocation_id: str
    acknowledged_at: str
    _payload_json: str = field(repr=False)

    @property
    def payload(self) -> dict[str, Any]:
        return json.loads(self._payload_json)

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "acknowledgement_id": self.acknowledgement_id,
            "output_id": self.output_id,
            "lane_id": self.lane_id,
            "contract_version": self.contract_version,
            "producer_invocation_id": self.producer_invocation_id,
            "artifact_hash": self.artifact_hash,
            "consumer_version": self.consumer_version,
            "consumer_invocation_id": self.consumer_invocation_id,
            "acknowledged_at": self.acknowledged_at,
            "payload": self.payload,
        }


@dataclass(frozen=True, slots=True)
class RuntimeLaneConsumptionRecord:
    """Proof that a known acknowledgement was used to consume an output."""

    schema_version: str
    consumption_id: str
    output_id: str
    acknowledgement_id: str
    lane_id: str
    contract_version: str
    artifact_hash: str
    consumer_version: str
    consumer_invocation_id: str
    consumed_at: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "consumption_id": self.consumption_id,
            "output_id": self.output_id,
            "acknowledgement_id": self.acknowledgement_id,
            "lane_id": self.lane_id,
            "contract_version": self.contract_version,
            "artifact_hash": self.artifact_hash,
            "consumer_version": self.consumer_version,
            "consumer_invocation_id": self.consumer_invocation_id,
            "consumed_at": self.consumed_at,
        }


class RuntimeLaneBoundary:
    """Issue, acknowledge, and consume canonical coding-lane outputs.

    The registry is intentionally scoped to a boundary instance.  It does not
    claim durability; callers integrating the production orchestrator must
    persist the serializable records with the authoritative task state.
    """

    def __init__(self) -> None:
        self._contracts = deepcopy(canonical_coding_lane_contracts())
        self._validators: dict[tuple[str, str], Draft202012Validator] = {}
        for lane_id, contract in self._contracts.items():
            for schema_name in (
                "input_schema",
                "output_schema",
                "failure_schema",
                "acknowledgement_schema",
                "evidence_schema",
            ):
                schema = contract[schema_name]
                try:
                    Draft202012Validator.check_schema(schema)
                except SchemaError as error:
                    raise RuntimeLaneBoundaryError(
                        f"invalid_canonical_lane_schema:{lane_id}:{schema_name}"
                    ) from error
                self._validators[(lane_id, schema_name)] = Draft202012Validator(schema)

        self._outputs: dict[str, RuntimeLaneOutputRecord] = {}
        self._acknowledgements: dict[str, RuntimeLaneAcknowledgementRecord] = {}
        self._consumptions: dict[str, RuntimeLaneConsumptionRecord] = {}
        self._lock = RLock()

    def issue_output(
        self,
        *,
        lane_id: str,
        contract_version: str | None,
        producer_invocation_id: str,
        payload: Mapping[str, Any] | None,
    ) -> RuntimeLaneOutputRecord:
        """Validate and issue an immutable output for one producer invocation."""
        lane_id = self._required_text(lane_id, "coding_lane_missing")
        contract = self._contract(lane_id)
        if not isinstance(contract_version, str) or not contract_version.strip():
            raise RuntimeLaneBoundaryError("coding_lane_contract_version_missing")
        if contract_version != contract["contract_version"]:
            raise RuntimeLaneBoundaryError(
                "incompatible_coding_lane_producer_version:"
                f"{lane_id}:{contract_version}:{contract['contract_version']}"
            )
        producer_invocation_id = self._required_text(
            producer_invocation_id,
            "coding_lane_producer_invocation_id_missing",
        )
        normalized, payload_json = self._validate_payload(
            lane_id=lane_id,
            schema_name="output_schema",
            payload=payload,
            malformed_reason="malformed_coding_lane_output",
        )
        artifact_hash = runtime_lane_artifact_hash(normalized)
        record = RuntimeLaneOutputRecord(
            schema_version=OUTPUT_RECORD_VERSION,
            output_id=f"lane-output-{uuid4().hex}",
            lane_id=lane_id,
            contract_version=contract_version,
            producer_invocation_id=producer_invocation_id,
            artifact_hash=artifact_hash,
            issued_at=_utc_now(),
            _payload_json=payload_json,
        )
        with self._lock:
            self._outputs[record.output_id] = record
        return record

    def record_consumer_acknowledgement(
        self,
        *,
        output_id: str,
        consumer_version: str,
        consumer_invocation_id: str,
        payload: Mapping[str, Any] | None,
    ) -> RuntimeLaneAcknowledgementRecord:
        """Record a compatible consumer's own acknowledgement of an output."""
        with self._lock:
            output = self._require_output(output_id)
            contract = self._contract(output.lane_id)
            consumer_version = self._required_text(
                consumer_version,
                "coding_lane_consumer_version_missing",
            )
            if consumer_version not in contract["compatible_consumer_versions"]:
                raise RuntimeLaneBoundaryError(
                    "incompatible_coding_lane_consumer_version:"
                    f"{output.lane_id}:{consumer_version}"
                )
            consumer_invocation_id = self._required_text(
                consumer_invocation_id,
                "coding_lane_consumer_invocation_id_missing",
            )
            if consumer_invocation_id == output.producer_invocation_id:
                raise RuntimeLaneBoundaryError(
                    "coding_lane_consumer_invocation_not_distinct"
                )
            _, payload_json = self._validate_payload(
                lane_id=output.lane_id,
                schema_name="acknowledgement_schema",
                payload=payload,
                malformed_reason="malformed_coding_lane_acknowledgement",
            )
            acknowledgement = RuntimeLaneAcknowledgementRecord(
                schema_version=ACKNOWLEDGEMENT_RECORD_VERSION,
                acknowledgement_id=f"lane-ack-{uuid4().hex}",
                output_id=output.output_id,
                lane_id=output.lane_id,
                contract_version=output.contract_version,
                producer_invocation_id=output.producer_invocation_id,
                artifact_hash=output.artifact_hash,
                consumer_version=consumer_version,
                consumer_invocation_id=consumer_invocation_id,
                acknowledged_at=_utc_now(),
                _payload_json=payload_json,
            )
            self._acknowledgements[acknowledgement.acknowledgement_id] = acknowledgement
            return acknowledgement

    def mark_output_consumed(
        self,
        *,
        output_id: str,
        acknowledgement_id: str,
    ) -> RuntimeLaneConsumptionRecord:
        """Mark an output consumed only through its distinct known acknowledgement."""
        with self._lock:
            output = self._require_output(output_id)
            if output.output_id in self._consumptions:
                raise RuntimeLaneBoundaryError("coding_lane_output_already_consumed")
            acknowledgement = self._require_acknowledgement(acknowledgement_id)
            if acknowledgement.output_id != output.output_id:
                raise RuntimeLaneBoundaryError(
                    "coding_lane_acknowledgement_output_mismatch"
                )
            if (
                acknowledgement.lane_id != output.lane_id
                or acknowledgement.contract_version != output.contract_version
                or acknowledgement.artifact_hash != output.artifact_hash
                or acknowledgement.producer_invocation_id != output.producer_invocation_id
            ):
                raise RuntimeLaneBoundaryError(
                    "coding_lane_acknowledgement_binding_mismatch"
                )
            consumption = RuntimeLaneConsumptionRecord(
                schema_version=CONSUMPTION_RECORD_VERSION,
                consumption_id=f"lane-consumption-{uuid4().hex}",
                output_id=output.output_id,
                acknowledgement_id=acknowledgement.acknowledgement_id,
                lane_id=output.lane_id,
                contract_version=output.contract_version,
                artifact_hash=output.artifact_hash,
                consumer_version=acknowledgement.consumer_version,
                consumer_invocation_id=acknowledgement.consumer_invocation_id,
                consumed_at=_utc_now(),
            )
            self._consumptions[output.output_id] = consumption
            return consumption

    def output(self, output_id: str) -> RuntimeLaneOutputRecord:
        with self._lock:
            return self._require_output(output_id)

    def acknowledgement(
        self, acknowledgement_id: str
    ) -> RuntimeLaneAcknowledgementRecord:
        with self._lock:
            return self._require_acknowledgement(acknowledgement_id)

    def consumption(self, output_id: str) -> RuntimeLaneConsumptionRecord | None:
        with self._lock:
            output = self._require_output(output_id)
            return self._consumptions.get(output.output_id)

    def require_outputs_consumed(
        self, output_ids: Iterable[str]
    ) -> tuple[RuntimeLaneConsumptionRecord, ...]:
        """Fail closed when any required output is unknown or unconsumed."""
        with self._lock:
            records: list[RuntimeLaneConsumptionRecord] = []
            for output_id in output_ids:
                output = self._require_output(output_id)
                consumption = self._consumptions.get(output.output_id)
                if consumption is None:
                    raise RuntimeLaneBoundaryError(
                        f"required_coding_lane_output_unconsumed:{output.output_id}"
                    )
                records.append(consumption)
            return tuple(records)

    def _contract(self, lane_id: str) -> dict[str, Any]:
        try:
            contract = self._contracts[lane_id]
        except KeyError as error:
            raise RuntimeLaneBoundaryError(f"unknown_coding_lane:{lane_id}") from error
        if contract["deprecation_state"] != "active":
            raise RuntimeLaneBoundaryError(f"inactive_coding_lane:{lane_id}")
        return contract

    def _require_output(self, output_id: str) -> RuntimeLaneOutputRecord:
        output_id = self._required_text(
            output_id,
            "coding_lane_output_id_missing",
        )
        try:
            return self._outputs[output_id]
        except KeyError as error:
            raise RuntimeLaneBoundaryError(
                f"unknown_coding_lane_output:{output_id}"
            ) from error

    def _require_acknowledgement(
        self, acknowledgement_id: str
    ) -> RuntimeLaneAcknowledgementRecord:
        acknowledgement_id = self._required_text(
            acknowledgement_id,
            "coding_lane_acknowledgement_id_missing",
        )
        try:
            return self._acknowledgements[acknowledgement_id]
        except KeyError as error:
            raise RuntimeLaneBoundaryError(
                f"unknown_coding_lane_acknowledgement:{acknowledgement_id}"
            ) from error

    def _validate_payload(
        self,
        *,
        lane_id: str,
        schema_name: str,
        payload: Mapping[str, Any] | None,
        malformed_reason: str,
    ) -> tuple[dict[str, Any], str]:
        if not isinstance(payload, Mapping):
            raise RuntimeLaneBoundaryError(
                f"{malformed_reason}:{lane_id}:<root>:must be an object"
            )
        try:
            payload_json = _canonical_json(dict(payload))
            normalized = json.loads(payload_json)
        except (TypeError, ValueError) as error:
            raise RuntimeLaneBoundaryError(
                f"{malformed_reason}:{lane_id}:<root>:not JSON serializable"
            ) from error
        errors = sorted(
            self._validators[(lane_id, schema_name)].iter_errors(normalized),
            key=lambda error: tuple(str(part) for part in error.absolute_path),
        )
        if errors:
            first = errors[0]
            location = "/".join(str(part) for part in first.absolute_path) or "<root>"
            raise RuntimeLaneBoundaryError(
                f"{malformed_reason}:{lane_id}:{location}:{first.message}"
            )
        return normalized, payload_json

    @staticmethod
    def _required_text(value: object, reason_code: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise RuntimeLaneBoundaryError(reason_code)
        return value.strip()


def runtime_lane_artifact_hash(payload: Mapping[str, Any]) -> str:
    """Return the content hash used to bind outputs and acknowledgements."""
    try:
        canonical = _canonical_json(dict(payload))
    except (TypeError, ValueError) as error:
        raise RuntimeLaneBoundaryError("coding_lane_artifact_not_json_serializable") from error
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
