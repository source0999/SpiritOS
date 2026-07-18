"""Independent production participants for one immutable coding artifact.

Each service reads the artifact itself, produces its own invocation and output
identity, and returns a content-hashed record.  The orchestrator persists these
records and applies the runtime lane boundary; labels or copied approval fields
cannot stand in for participation.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from source_proxy.verification.anticheat import run_anticheat_detectors


PARTICIPANT_OUTPUT_SCHEMA = "coding.participant-output/v2"
PARTICIPANT_RECORD_SCHEMA = "coding.participant-invocation/v2"
PARTICIPANT_ACKNOWLEDGEMENT_SCHEMA = "coding.participant-acknowledgement/v2"
ARTIFACT_SCHEMA = "coding.immutable-applied-artifact/v2"
MANUAL_DIFF_CLAIM_CEILING = "applied_diff_verified_no_model_authorship_proof"
MODEL_DIFF_CLAIM_CEILING = "model_authored_applied_diff_verified"
MODEL_AUTHORSHIP_COMPLETENESS_DETECTOR = "model_authorship_claim_completeness"

PARTICIPANT_SERVICES = {
    "coding-reviewer": "source-proxy.coding.participants.review/v1",
    "coding-verifier": "source-proxy.coding.participants.verify/v1",
    "coding-anti-cheat": "source-proxy.coding.participants.anti-cheat/v1",
    "evidence-recorder": "source-proxy.coding.participants.evidence/v1",
}
LEGACY_EXECUTOR_SERVICE = "source-proxy.tasks.long_running.execute-approved/v1"
_SHA256_PATTERN = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
_WORKER_MODE_ENV = "SPIRITOS_CODING_PARTICIPANT_WORKER"
_WORKER_TIMEOUT_SECONDS = 60
_ORCHESTRATOR_CONSUMER_SERVICE = "source-proxy.coding.orchestrator/v2"


class CodingParticipantError(ValueError):
    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


def build_applied_artifact(
    *,
    task_id: str,
    run_id: str,
    approval_id: str,
    generation: int,
    approved_diff: str,
    execution: Mapping[str, Any],
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the only artifact identity accepted by post-apply participants."""

    audit = execution.get("audit")
    if not isinstance(audit, Mapping):
        raise CodingParticipantError("coding_artifact_audit_missing")
    workspace_root = str(audit.get("workspace_root") or "").strip()
    snapshots = audit.get("changed_file_snapshots")
    if not workspace_root or not isinstance(snapshots, list) or not snapshots:
        raise CodingParticipantError("coding_artifact_result_snapshots_missing")
    normalized_snapshots: list[dict[str, Any]] = []
    for item in snapshots:
        if not isinstance(item, Mapping):
            raise CodingParticipantError("coding_artifact_result_snapshot_invalid")
        path = str(item.get("path") or "").replace("\\", "/").strip()
        after = item.get("sha256_after")
        if not path or not isinstance(after, str) or len(after) != 64:
            raise CodingParticipantError("coding_artifact_result_snapshot_invalid")
        normalized_snapshots.append(
            {
                "path": path,
                "sha256_before": item.get("sha256_before"),
                "sha256_after": after,
                "missing_before_apply": bool(item.get("missing_before_apply")),
            }
        )
    normalized_snapshots.sort(key=lambda item: item["path"])
    diff_sha256 = hashlib.sha256(approved_diff.encode("utf-8")).hexdigest()
    if audit.get("approved_diff_sha256") != diff_sha256:
        raise CodingParticipantError("coding_artifact_diff_hash_mismatch")
    result_sha256 = _sha256_json(normalized_snapshots)
    bound_provenance = _canonical_mapping(
        provenance or {},
        "coding_artifact_provenance_invalid",
    )
    body = {
        "schema_version": ARTIFACT_SCHEMA,
        "task_id": _required_text(task_id, "coding_artifact_task_id_missing"),
        "run_id": _required_text(run_id, "coding_artifact_run_id_missing"),
        "approval_id": _required_text(approval_id, "coding_artifact_approval_id_missing"),
        "generation": int(generation),
        "approved_diff_sha256": diff_sha256,
        "result_sha256": result_sha256,
        "workspace_root": str(Path(workspace_root).resolve()),
        "approved_diff_path": str(audit.get("approved_diff_path") or ""),
        "changed_files": normalized_snapshots,
        "source_commit": str(bound_provenance.get("source_commit") or "not_bound"),
        "repository_identity": dict(
            bound_provenance.get("repository_identity")
            if isinstance(bound_provenance.get("repository_identity"), Mapping)
            else {}
        ),
        "target_plugin_identity": dict(
            bound_provenance.get("target_plugin_identity")
            if isinstance(bound_provenance.get("target_plugin_identity"), Mapping)
            else {}
        ),
        "prompt_identity": dict(
            bound_provenance.get("prompt_identity")
            if isinstance(bound_provenance.get("prompt_identity"), Mapping)
            else {}
        ),
        "context_identity": dict(
            bound_provenance.get("context_identity")
            if isinstance(bound_provenance.get("context_identity"), Mapping)
            else {}
        ),
        "model_output_identity": dict(
            bound_provenance.get("model_output_identity")
            if isinstance(bound_provenance.get("model_output_identity"), Mapping)
            else {}
        ),
        "cartographer_identity": dict(
            bound_provenance.get("cartographer_identity")
            if isinstance(bound_provenance.get("cartographer_identity"), Mapping)
            else {}
        ),
        "claim_ceiling": str(
            bound_provenance.get("claim_ceiling")
            or "applied_diff_only_no_production_provenance"
        ),
    }
    body["artifact_sha256"] = _sha256_json(body)
    return body


def run_coding_reviewer(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Independently review scope and exact on-disk result hashes."""

    consumed_input = {
        "operation": "review_applied_artifact_disk_state",
        "artifact_sha256": str(artifact.get("artifact_sha256") or ""),
    }

    def review() -> dict[str, Any]:
        findings = _artifact_disk_findings(artifact)
        return {
            "passed": not findings,
            "findings": findings,
            "reviewed_diff_sha256": str(artifact.get("approved_diff_sha256") or ""),
            "reviewed_result_sha256": str(artifact.get("result_sha256") or ""),
        }

    return _invoke(
        role="coding-reviewer",
        service=PARTICIPANT_SERVICES["coding-reviewer"],
        artifact=artifact,
        consumed_input=consumed_input,
        operation=review,
    )


def run_coding_verifier(
    artifact: Mapping[str, Any],
    verification: Mapping[str, Any],
) -> dict[str, Any]:
    """Independently consume server verification output and current disk state."""

    verification_payload = _canonical_mapping(
        verification,
        "coding_verifier_input_invalid",
    )
    consumed_input = {"verification": verification_payload}

    def verify() -> dict[str, Any]:
        findings = _artifact_disk_findings(artifact)
        checks = verification_payload.get("checks")
        if not isinstance(checks, list) or not checks:
            findings.append("verification_checks_missing")
            normalized_checks: list[dict[str, Any]] = []
        else:
            normalized_checks = [dict(item) for item in checks if isinstance(item, Mapping)]
            for check in normalized_checks:
                if check.get("required") is True and check.get("status") != "passed":
                    findings.append(
                        f"required_check_not_passed:{str(check.get('id') or 'unknown')}"
                    )
        if verification_payload.get("status") != "verified":
            findings.append("server_verification_not_verified")
        if verification_payload.get("manual_browser_check_required") is True and not (
            verification_payload.get("manual_browser_check_done") is True
            or bool(str(verification_payload.get("skip_reason") or "").strip())
        ):
            findings.append("required_browser_verification_missing")
        return {
            "passed": not findings,
            "verdict": "PASS" if not findings else "FAIL",
            "findings": findings,
            "checks": normalized_checks,
            "verification_sha256": _sha256_json(verification_payload),
        }

    return _invoke(
        role="coding-verifier",
        service=PARTICIPANT_SERVICES["coding-verifier"],
        artifact=artifact,
        consumed_input=consumed_input,
        operation=verify,
    )


def run_coding_anti_cheat(
    artifact: Mapping[str, Any],
    *,
    model_evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the production anti-cheat registry as its own artifact consumer."""

    evidence = _canonical_mapping(
        model_evidence or {},
        "coding_anti_cheat_model_evidence_invalid",
    )
    consumed_input = {"model_evidence": evidence}

    def inspect() -> dict[str, Any]:
        approved_diff = _read_approved_diff(artifact)
        payload = dict(evidence)
        # These three facts come from the independently hash-checked applied
        # artifact.  Model availability, behavior, live evidence, and verdict
        # fields remain exactly as supplied; absence is not upgraded to PASS.
        payload.update(
            {
                "runtime_code": approved_diff,
                "executed_claim": True,
                "artifact_kind": "applied_diff",
            }
        )
        payload.setdefault("runtime_integration", False)
        payload.setdefault("implementation_origin", "unknown")
        payload.setdefault("behavior_exercised", False)
        payload.setdefault("live_evidence_claim", False)
        payload.setdefault("evidence_origin", "applied_artifact")
        payload.setdefault("summary_status", "NOT_PROVEN")
        payload.setdefault("raw_status", "NOT_PROVEN")
        report = run_anticheat_detectors(payload).to_dict()
        model_authorship_proven = _model_authorship_proven(evidence)
        terminal_claim_requested = (
            evidence.get("terminal_proof_eligible") is True
            or evidence.get("proof_eligible") is True
        )
        integrity_violations: list[dict[str, Any]] = []
        detector_ids = list(report["checked_detector_ids"])
        if MODEL_AUTHORSHIP_COMPLETENESS_DETECTOR not in detector_ids:
            detector_ids.append(MODEL_AUTHORSHIP_COMPLETENESS_DETECTOR)
        if terminal_claim_requested and not model_authorship_proven:
            integrity_violations.append(
                {
                    "detector_id": MODEL_AUTHORSHIP_COMPLETENESS_DETECTOR,
                    "violation_code": "terminal_model_authorship_unproven",
                    "message": (
                        "Terminal model authorship was claimed without complete "
                        "production model provenance."
                    ),
                    "severity": "error",
                    "failure_class": "evidence_missing",
                    "evidence": {
                        "model_evidence_sha256": _sha256_json(evidence),
                    },
                }
            )
        violations = [*list(report["violations"]), *integrity_violations]
        passed = report["passed"] is True and not integrity_violations
        claim_ceiling = (
            str(evidence.get("claim_ceiling_impact") or MODEL_DIFF_CLAIM_CEILING)
            if model_authorship_proven
            else MANUAL_DIFF_CLAIM_CEILING
        )
        return {
            "passed": passed,
            "detector_ids": detector_ids,
            "violations": violations,
            "approved_diff_sha256": hashlib.sha256(approved_diff.encode("utf-8")).hexdigest(),
            "model_evidence_sha256": _sha256_json(evidence),
            "model_authorship_proven": model_authorship_proven,
            "terminal_proof_eligible": passed and model_authorship_proven,
            "claim_ceiling": claim_ceiling,
            "fallback_used": evidence.get("fallback_used") is True,
        }

    return _invoke(
        role="coding-anti-cheat",
        service=PARTICIPANT_SERVICES["coding-anti-cheat"],
        artifact=artifact,
        consumed_input=consumed_input,
        operation=inspect,
    )


def run_coding_evidence_recorder(
    artifact: Mapping[str, Any],
    *,
    participant_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a content-addressed per-run receipt from prior distinct outputs."""

    normalized_records = [
        _canonical_mapping(record, "coding_evidence_participant_record_invalid")
        for record in participant_records
    ]
    consumed_input = {"participant_records": normalized_records}

    def record() -> dict[str, Any]:
        required = {"coding-executor", "coding-reviewer", "coding-verifier", "coding-anti-cheat"}
        roles = {str(item.get("role") or "") for item in normalized_records}
        missing = sorted(required - roles)
        failed = sorted(
            str(item.get("role") or "unknown")
            for item in normalized_records
            if item.get("passed") is not True
        )
        invalid: list[str] = []
        record_receipts: list[dict[str, Any]] = []
        for item in normalized_records:
            role = str(item.get("role") or "unknown")
            try:
                validated = _validate_evidence_source_record(item, artifact)
            except CodingParticipantError as error:
                invalid.append(f"{role}:{error.reason_code}")
                validated = item
            result = validated.get("result")
            record_receipts.append(
                {
                    "role": role,
                    "invocation_id": str(validated.get("invocation_id") or ""),
                    "output_id": str(validated.get("output_id") or ""),
                    "passed": validated.get("passed") is True,
                    "record_sha256": participant_record_sha256(validated),
                    "result": dict(result) if isinstance(result, Mapping) else {},
                }
            )
        invocation_ids = [str(item.get("invocation_id") or "") for item in normalized_records]
        output_ids = [str(item.get("output_id") or "") for item in normalized_records]
        if len(set(invocation_ids)) != len(invocation_ids) or "" in invocation_ids:
            missing.append("distinct_invocation_ids")
        if len(set(output_ids)) != len(output_ids) or "" in output_ids:
            missing.append("distinct_output_ids")
        anti_cheat_result = next(
            (
                item.get("result")
                for item in normalized_records
                if item.get("role") == "coding-anti-cheat" and isinstance(item.get("result"), Mapping)
            ),
            {},
        )
        receipt_body = {
            "schema_version": "coding.run-evidence/v1",
            "task_id": artifact.get("task_id"),
            "run_id": artifact.get("run_id"),
            "artifact_sha256": artifact.get("artifact_sha256"),
            "participant_invocation_ids": invocation_ids,
            "participant_output_ids": output_ids,
            "participant_records_sha256": _sha256_json(normalized_records),
            "participant_records": record_receipts,
            "missing": missing,
            "failed": failed,
            "invalid": sorted(invalid),
            "claim_ceiling": str(
                anti_cheat_result.get("claim_ceiling") or MANUAL_DIFF_CLAIM_CEILING
            ),
            "terminal_proof_eligible": (
                anti_cheat_result.get("terminal_proof_eligible") is True
                and not missing
                and not failed
                and not invalid
            ),
        }
        receipt_hash = _sha256_json(receipt_body)
        passed = not missing and not failed and not invalid
        return {
            "passed": passed,
            "receipt_id": f"coding-evidence-{receipt_hash.removeprefix('sha256:')[:24]}",
            "truth_status": "PASS" if passed else "FAIL",
            "receipt_sha256": receipt_hash,
            "receipt": receipt_body,
            "claim_ceiling": receipt_body["claim_ceiling"],
            "terminal_proof_eligible": receipt_body["terminal_proof_eligible"],
        }

    return _invoke(
        role="evidence-recorder",
        service=PARTICIPANT_SERVICES["evidence-recorder"],
        artifact=artifact,
        consumed_input=consumed_input,
        operation=record,
    )


def _invoke(
    *,
    role: str,
    service: str,
    artifact: Mapping[str, Any],
    consumed_input: Mapping[str, Any],
    operation: Any,
) -> dict[str, Any]:
    if os.environ.get(_WORKER_MODE_ENV) != "1":
        producer_output = _invoke_worker_process(
            role=role,
            service=service,
            artifact=artifact,
            consumed_input=consumed_input,
        )
        return acknowledge_coding_participant_output(
            producer_output,
            artifact,
            consumer_service=_ORCHESTRATOR_CONSUMER_SERVICE,
        )

    artifact_record = _validate_artifact(artifact)
    artifact_hash = str(artifact_record["artifact_sha256"])
    consumed = _canonical_mapping(consumed_input, "coding_participant_input_invalid")
    consumed_input_sha256 = _sha256_json(consumed)
    input_sha256 = _sha256_json(
        {
            "artifact_sha256": artifact_hash,
            "consumed_input_sha256": consumed_input_sha256,
            "role": role,
            "service": service,
        }
    )
    invocation_id = f"{role}-invocation-{uuid4().hex}"
    started_at = _utc_now()
    result = operation()
    if not isinstance(result, dict) or not isinstance(result.get("passed"), bool):
        raise CodingParticipantError(f"coding_participant_result_invalid:{role}")
    result = _canonical_mapping(result, f"coding_participant_result_invalid:{role}")
    prior_consumed_hash = result.get("consumed_input_sha256")
    if prior_consumed_hash not in (None, consumed_input_sha256):
        raise CodingParticipantError(f"coding_participant_result_input_mismatch:{role}")
    result["consumed_input_sha256"] = consumed_input_sha256
    completed_at = _utc_now()
    output_hash = _sha256_json(result)
    record = {
        "schema_version": PARTICIPANT_OUTPUT_SCHEMA,
        "role": role,
        "service": service,
        "provider": "source-proxy",
        "model": service,
        "task_id": artifact.get("task_id"),
        "run_id": artifact.get("run_id"),
        "artifact_sha256": artifact_hash,
        "invocation_id": invocation_id,
        "consumed_input_sha256": consumed_input_sha256,
        "input_sha256": input_sha256,
        "output_id": f"{role}-output-{uuid4().hex}",
        "output_sha256": output_hash,
        "started_at": started_at,
        "completed_at": completed_at,
        "passed": result["passed"],
        "result": result,
        "producer_process": _producer_process_identity(
            isolation="dedicated_participant_subprocess",
        ),
    }
    record["producer_record_sha256"] = _producer_record_sha256(record)
    return validate_coding_participant_output(
        record,
        artifact_record,
        expected_role=role,
        consumed_input=consumed,
    )


def _invoke_worker_process(
    *,
    role: str,
    service: str,
    artifact: Mapping[str, Any],
    consumed_input: Mapping[str, Any],
) -> dict[str, Any]:
    if PARTICIPANT_SERVICES.get(role) != service:
        raise CodingParticipantError(f"coding_participant_service_invalid:{role}")
    root = Path(__file__).resolve().parents[2]
    executable = Path(sys.executable).resolve()
    entrypoint = Path(__file__).resolve()
    expected_executable_sha256 = _sha256_file(executable)
    expected_entrypoint_sha256 = _sha256_file(entrypoint)
    payload = {
        "schema_version": "coding.participant-worker-request/v1",
        "role": role,
        "artifact": _canonical_mapping(artifact, "coding_participant_artifact_invalid"),
        "consumed_input": _canonical_mapping(
            consumed_input,
            "coding_participant_input_invalid",
        ),
        "expected_executable_sha256": expected_executable_sha256,
        "expected_entrypoint_sha256": expected_entrypoint_sha256,
    }
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": os.pathsep.join(
            item
            for item in (str(root), os.environ.get("PYTHONPATH", ""))
            if item
        ),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "PYTHONDONTWRITEBYTECODE": "1",
        _WORKER_MODE_ENV: "1",
    }
    completed = subprocess.run(
        [
            str(executable),
            "-B",
            "-m",
            "source_proxy.coding.participants",
            "--worker",
        ],
        input=json.dumps(payload, sort_keys=True, separators=(",", ":")),
        text=True,
        capture_output=True,
        check=False,
        cwd=str(root),
        env=environment,
        timeout=_WORKER_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        raise CodingParticipantError(f"coding_participant_worker_failed:{role}")
    try:
        output = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise CodingParticipantError(
            f"coding_participant_worker_output_invalid:{role}"
        ) from error
    if _sha256_file(executable) != expected_executable_sha256:
        raise CodingParticipantError("coding_participant_worker_executable_changed")
    if _sha256_file(entrypoint) != expected_entrypoint_sha256:
        raise CodingParticipantError("coding_participant_worker_entrypoint_changed")
    normalized = validate_coding_participant_output(
        output,
        artifact,
        expected_role=role,
        consumed_input=consumed_input,
    )
    process_identity = normalized.get("producer_process")
    if not isinstance(process_identity, Mapping) or (
        process_identity.get("executable_sha256") != expected_executable_sha256
        or process_identity.get("entrypoint_sha256") != expected_entrypoint_sha256
        or process_identity.get("isolation") != "dedicated_participant_subprocess"
        or int(process_identity.get("process_id") or 0) in {0, os.getpid()}
        or int(process_identity.get("parent_process_id") or 0) != os.getpid()
    ):
        raise CodingParticipantError("coding_participant_worker_identity_invalid")
    return normalized


def acknowledge_coding_participant_output(
    output: Mapping[str, Any],
    artifact: Mapping[str, Any],
    *,
    consumer_service: str,
) -> dict[str, Any]:
    """Create the consumer-owned acknowledgement after exact output validation."""

    if output.get("schema_version") == PARTICIPANT_RECORD_SCHEMA:
        return validate_coding_participant_record(output, artifact)
    producer = validate_coding_participant_output(output, artifact)
    acknowledgement_id = f"{producer['role']}-ack-{uuid4().hex}"
    acknowledgement = {
        "schema_version": PARTICIPANT_ACKNOWLEDGEMENT_SCHEMA,
        "acknowledgement_id": acknowledgement_id,
        "approval_id": artifact.get("approval_id"),
        "generation": artifact.get("generation"),
        "consumer_service": _required_text(
            consumer_service,
            "coding_participant_consumer_service_missing",
        ),
        "consumer_process_id": os.getpid(),
        "invocation_id": producer["invocation_id"],
        "output_id": producer["output_id"],
        "output_sha256": producer["output_sha256"],
        "artifact_sha256": producer["artifact_sha256"],
        "producer_record_sha256": producer["producer_record_sha256"],
        "acknowledged_at": _utc_now(),
        "consumed": True,
    }
    record = dict(producer)
    record["schema_version"] = PARTICIPANT_RECORD_SCHEMA
    record["consumer_acknowledgement_id"] = acknowledgement_id
    record["consumer_acknowledgement"] = acknowledgement
    record["record_sha256"] = participant_record_sha256(record)
    return validate_coding_participant_record(record, artifact)


def build_coding_executor_output(
    artifact: Mapping[str, Any],
    *,
    result: Mapping[str, Any],
    started_at: str,
) -> dict[str, Any]:
    """Record the executor's own output; the orchestrator acknowledges it later."""

    artifact_record = _validate_artifact(artifact)
    normalized_result = _canonical_mapping(result, "coding_executor_result_invalid")
    if not isinstance(normalized_result.get("passed"), bool):
        raise CodingParticipantError("coding_executor_result_invalid")
    record = {
        "schema_version": PARTICIPANT_OUTPUT_SCHEMA,
        "role": "coding-executor",
        "service": LEGACY_EXECUTOR_SERVICE,
        "provider": "source-proxy",
        "model": "canonical-diff-executor",
        "task_id": artifact_record["task_id"],
        "run_id": artifact_record["run_id"],
        "artifact_sha256": artifact_record["artifact_sha256"],
        "invocation_id": f"coding-executor-invocation-{uuid4().hex}",
        "consumed_input_sha256": _sha256_json(
            {"approved_diff_sha256": artifact_record["approved_diff_sha256"]}
        ),
        "input_sha256": artifact_record["approved_diff_sha256"],
        "output_id": f"coding-executor-output-{uuid4().hex}",
        "output_sha256": _sha256_json(normalized_result),
        "started_at": _required_text(started_at, "coding_executor_started_at_missing"),
        "completed_at": _utc_now(),
        "passed": normalized_result["passed"],
        "result": normalized_result,
        "producer_process": _producer_process_identity(
            isolation="source_proxy_executor_transaction",
        ),
    }
    record["producer_record_sha256"] = _producer_record_sha256(record)
    return validate_coding_participant_output(
        record,
        artifact_record,
        expected_role="coding-executor",
    )


def validate_coding_participant_record(
    record: Mapping[str, Any],
    artifact: Mapping[str, Any],
    *,
    expected_role: str | None = None,
    consumed_input: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate an independent participant record and every content binding.

    When the caller has the role-specific input preimage it must pass
    ``consumed_input``; the validator then proves that changing verification,
    model, or participant evidence changes the participant input identity.
    """

    artifact_record = _validate_artifact(artifact)
    if (
        record.get("role") == "coding-executor"
        and record.get("schema_version") == "coding.participant-invocation/v1"
    ):
        if expected_role not in (None, "coding-executor"):
            raise CodingParticipantError("coding_participant_role_mismatch")
        return _validate_legacy_executor_record(record, artifact_record)
    value = _canonical_mapping(record, "coding_participant_record_invalid")
    required = _participant_output_fields() | {
        "consumer_acknowledgement_id",
        "consumer_acknowledgement",
        "record_sha256",
    }
    if set(value) != required:
        raise CodingParticipantError("coding_participant_record_fields_invalid")
    if value["schema_version"] != PARTICIPANT_RECORD_SCHEMA:
        raise CodingParticipantError("coding_participant_record_schema_invalid")
    producer = {
        key: item for key, item in value.items() if key in _participant_output_fields()
    }
    producer["schema_version"] = PARTICIPANT_OUTPUT_SCHEMA
    validate_coding_participant_output(
        producer,
        artifact_record,
        expected_role=expected_role,
        consumed_input=consumed_input,
    )
    acknowledgement_id = _required_text(
        value["consumer_acknowledgement_id"],
        "coding_participant_consumer_acknowledgement_id_missing",
    )
    acknowledgement = value["consumer_acknowledgement"]
    if not isinstance(acknowledgement, Mapping) or set(acknowledgement) != {
        "schema_version",
        "acknowledgement_id",
        "approval_id",
        "generation",
        "consumer_service",
        "consumer_process_id",
        "invocation_id",
        "output_id",
        "output_sha256",
        "artifact_sha256",
        "producer_record_sha256",
        "acknowledged_at",
        "consumed",
    }:
        raise CodingParticipantError("coding_participant_acknowledgement_invalid")
    if (
        acknowledgement.get("schema_version") != PARTICIPANT_ACKNOWLEDGEMENT_SCHEMA
        or acknowledgement.get("acknowledgement_id") != acknowledgement_id
        or acknowledgement.get("approval_id") != artifact_record["approval_id"]
        or acknowledgement.get("generation") != artifact_record["generation"]
        or acknowledgement.get("consumer_service") != _ORCHESTRATOR_CONSUMER_SERVICE
        or not isinstance(acknowledgement.get("consumer_process_id"), int)
        or (
            value["producer_process"].get("isolation")
            == "dedicated_participant_subprocess"
            and acknowledgement.get("consumer_process_id")
            == value["producer_process"].get("process_id")
        )
        or acknowledgement.get("invocation_id") != value["invocation_id"]
        or acknowledgement.get("output_id") != value["output_id"]
        or acknowledgement.get("output_sha256") != value["output_sha256"]
        or acknowledgement.get("artifact_sha256") != value["artifact_sha256"]
        or acknowledgement.get("producer_record_sha256")
        != value["producer_record_sha256"]
        or acknowledgement.get("consumed") is not True
    ):
        raise CodingParticipantError("coding_participant_acknowledgement_binding_invalid")
    _required_text(
        acknowledgement.get("acknowledged_at"),
        "coding_participant_acknowledged_at_missing",
    )
    if value["record_sha256"] != participant_record_sha256(value):
        raise CodingParticipantError("coding_participant_record_hash_mismatch")
    return value


def validate_coding_participant_output(
    record: Mapping[str, Any],
    artifact: Mapping[str, Any],
    *,
    expected_role: str | None = None,
    consumed_input: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    artifact_record = _validate_artifact(artifact)
    value = _canonical_mapping(record, "coding_participant_output_invalid")
    if set(value) != _participant_output_fields():
        raise CodingParticipantError("coding_participant_output_fields_invalid")
    if value.get("schema_version") != PARTICIPANT_OUTPUT_SCHEMA:
        raise CodingParticipantError("coding_participant_output_schema_invalid")
    role = _required_text(value.get("role"), "coding_participant_role_missing")
    if expected_role is not None and role != expected_role:
        raise CodingParticipantError("coding_participant_role_mismatch")
    service = (
        LEGACY_EXECUTOR_SERVICE if role == "coding-executor" else PARTICIPANT_SERVICES.get(role)
    )
    expected_model = "canonical-diff-executor" if role == "coding-executor" else service
    if service is None or value.get("service") != service:
        raise CodingParticipantError("coding_participant_service_invalid")
    if value.get("provider") != "source-proxy" or value.get("model") != expected_model:
        raise CodingParticipantError("coding_participant_provider_model_invalid")
    if (
        value.get("task_id") != artifact_record["task_id"]
        or value.get("run_id") != artifact_record["run_id"]
        or value.get("artifact_sha256") != artifact_record["artifact_sha256"]
    ):
        raise CodingParticipantError("coding_participant_artifact_binding_mismatch")
    invocation_id = _required_text(value.get("invocation_id"), "coding_participant_invocation_id_missing")
    output_id = _required_text(value.get("output_id"), "coding_participant_output_id_missing")
    if invocation_id == output_id:
        raise CodingParticipantError("coding_participant_identity_reused")
    consumed_sha256 = _require_sha256(
        value.get("consumed_input_sha256"),
        "coding_participant_consumed_input_hash_invalid",
    )
    if role == "coding-executor":
        expected_input_sha256 = artifact_record["approved_diff_sha256"]
    else:
        expected_input_sha256 = _sha256_json(
            {
                "artifact_sha256": artifact_record["artifact_sha256"],
                "consumed_input_sha256": consumed_sha256,
                "role": role,
                "service": service,
            }
        )
    if value.get("input_sha256") != expected_input_sha256:
        raise CodingParticipantError("coding_participant_input_hash_mismatch")
    if consumed_input is not None:
        expected_consumed_sha256 = _sha256_json(
            _canonical_mapping(consumed_input, "coding_participant_input_invalid")
        )
        if consumed_sha256 != expected_consumed_sha256:
            raise CodingParticipantError("coding_participant_consumed_input_mismatch")
    result = value.get("result")
    if not isinstance(result, Mapping) or not isinstance(result.get("passed"), bool):
        raise CodingParticipantError("coding_participant_result_invalid")
    if role != "coding-executor" and result.get("consumed_input_sha256") != consumed_sha256:
        raise CodingParticipantError("coding_participant_result_input_hash_mismatch")
    if value.get("passed") is not result["passed"]:
        raise CodingParticipantError("coding_participant_result_status_mismatch")
    if value.get("output_sha256") != _sha256_json(dict(result)):
        raise CodingParticipantError("coding_participant_output_hash_mismatch")
    _required_text(value.get("started_at"), "coding_participant_started_at_missing")
    _required_text(value.get("completed_at"), "coding_participant_completed_at_missing")
    process = value.get("producer_process")
    if not isinstance(process, Mapping) or set(process) != {
        "process_id",
        "parent_process_id",
        "executable_sha256",
        "entrypoint_sha256",
        "isolation",
        "worker_nonce",
    }:
        raise CodingParticipantError("coding_participant_process_identity_invalid")
    if (
        not isinstance(process.get("process_id"), int)
        or int(process.get("process_id") or 0) <= 0
        or not isinstance(process.get("parent_process_id"), int)
        or int(process.get("parent_process_id") or 0) <= 0
        or not _is_sha256(process.get("executable_sha256"))
        or not _is_sha256(process.get("entrypoint_sha256"))
        or process.get("isolation")
        not in {"dedicated_participant_subprocess", "source_proxy_executor_transaction"}
        or not str(process.get("worker_nonce") or "").startswith("participant-worker-")
    ):
        raise CodingParticipantError("coding_participant_process_identity_invalid")
    if value.get("producer_record_sha256") != _producer_record_sha256(value):
        raise CodingParticipantError("coding_participant_producer_record_hash_mismatch")
    return value


def participant_record_sha256(record: Mapping[str, Any]) -> str:
    """Hash a participant record without trusting its declared record hash."""

    if not isinstance(record, Mapping):
        raise CodingParticipantError("coding_participant_record_invalid")
    unsigned = dict(record)
    unsigned.pop("record_sha256", None)
    return _sha256_json(unsigned)


def _participant_output_fields() -> set[str]:
    return {
        "schema_version",
        "role",
        "service",
        "provider",
        "model",
        "task_id",
        "run_id",
        "artifact_sha256",
        "invocation_id",
        "consumed_input_sha256",
        "input_sha256",
        "output_id",
        "output_sha256",
        "started_at",
        "completed_at",
        "passed",
        "result",
        "producer_process",
        "producer_record_sha256",
    }


def _producer_record_sha256(record: Mapping[str, Any]) -> str:
    unsigned = dict(record)
    unsigned.pop("producer_record_sha256", None)
    return _sha256_json(unsigned)


def _producer_process_identity(*, isolation: str) -> dict[str, Any]:
    executable = Path(sys.executable).resolve()
    return {
        "process_id": os.getpid(),
        "parent_process_id": os.getppid(),
        "executable_sha256": _sha256_file(executable),
        "entrypoint_sha256": _sha256_file(Path(__file__).resolve()),
        "isolation": isolation,
        "worker_nonce": f"participant-worker-{uuid4().hex}",
    }


def _validate_evidence_source_record(
    record: Mapping[str, Any],
    artifact: Mapping[str, Any],
) -> dict[str, Any]:
    return validate_coding_participant_record(record, artifact)


def _validate_legacy_executor_record(
    record: Mapping[str, Any],
    artifact: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the existing executor record until its producer adopts v2 inputs."""

    artifact_record = _validate_artifact(artifact)
    value = _canonical_mapping(record, "coding_executor_record_invalid")
    required = {
        "schema_version",
        "role",
        "service",
        "provider",
        "model",
        "task_id",
        "run_id",
        "artifact_sha256",
        "invocation_id",
        "input_sha256",
        "output_id",
        "output_sha256",
        "consumer_acknowledgement_id",
        "started_at",
        "completed_at",
        "passed",
        "result",
    }
    if not required.issubset(value):
        raise CodingParticipantError("coding_executor_record_fields_invalid")
    if (
            value.get("schema_version") != "coding.participant-invocation/v1"
        or value.get("role") != "coding-executor"
        or value.get("service") != LEGACY_EXECUTOR_SERVICE
        or value.get("provider") != "source-proxy"
        or value.get("model") != "canonical-diff-executor"
    ):
        raise CodingParticipantError("coding_executor_record_identity_invalid")
    if (
        value.get("task_id") != artifact_record["task_id"]
        or value.get("run_id") != artifact_record["run_id"]
        or value.get("artifact_sha256") != artifact_record["artifact_sha256"]
        or value.get("input_sha256") != artifact_record["approved_diff_sha256"]
    ):
        raise CodingParticipantError("coding_executor_record_artifact_binding_mismatch")
    result = value.get("result")
    if not isinstance(result, Mapping) or not isinstance(result.get("passed"), bool):
        raise CodingParticipantError("coding_executor_result_invalid")
    if value.get("passed") is not result["passed"]:
        raise CodingParticipantError("coding_executor_result_status_mismatch")
    output_hash = _sha256_json(dict(result))
    if value.get("output_sha256") not in {output_hash, output_hash.removeprefix("sha256:")}:
        raise CodingParticipantError("coding_executor_output_hash_mismatch")
    for key in (
        "invocation_id",
        "output_id",
        "consumer_acknowledgement_id",
        "started_at",
        "completed_at",
    ):
        _required_text(value.get(key), f"coding_executor_{key}_missing")
    return value


def _validate_artifact(artifact: Mapping[str, Any]) -> dict[str, Any]:
    value = _canonical_mapping(artifact, "coding_participant_artifact_invalid")
    required = {
        "schema_version",
        "task_id",
        "run_id",
        "approval_id",
        "generation",
        "approved_diff_sha256",
        "result_sha256",
        "workspace_root",
        "approved_diff_path",
        "changed_files",
        "source_commit",
        "repository_identity",
        "target_plugin_identity",
        "prompt_identity",
        "context_identity",
        "model_output_identity",
        "cartographer_identity",
        "claim_ceiling",
        "artifact_sha256",
    }
    if set(value) != required or value.get("schema_version") != ARTIFACT_SCHEMA:
        raise CodingParticipantError("coding_participant_artifact_schema_invalid")
    declared_hash = _require_sha256(
        value.get("artifact_sha256"),
        "coding_participant_artifact_hash_missing",
    )
    unsigned = dict(value)
    unsigned.pop("artifact_sha256", None)
    if declared_hash != _sha256_json(unsigned):
        raise CodingParticipantError("coding_participant_artifact_hash_mismatch")
    return value


def _model_authorship_proven(evidence: Mapping[str, Any]) -> bool:
    provider_result = str(evidence.get("provider_result") or "").lower()
    generation_source = str(evidence.get("generation_source") or "").lower()
    transport = str(evidence.get("provider_transport") or "").lower()
    invocation_id = str(evidence.get("model_invocation_id") or "").strip()
    provider = str(evidence.get("provider") or "").strip()
    model = str(evidence.get("model") or "").strip()
    output_hash = evidence.get("model_output_sha256")
    response_hash = evidence.get("raw_model_response_sha256")
    if not (
        evidence.get("proof_eligible") is True
        and evidence.get("provider_available") is True
        and provider_result in {"success", "succeeded", "pass", "passed"}
        and generation_source == "model"
        and transport in {"model_router", "source_proxy_model_router", "litellm_router"}
        and invocation_id
        and provider
        and model
        and _is_sha256(output_hash)
        and _is_sha256(response_hash)
    ):
        return False
    if evidence.get("fallback_used") is True:
        return bool(
            str(evidence.get("recovery_id") or "").strip()
            and evidence.get("reported_success_path") == "fallback"
            and evidence.get("claim_ceiling_impact")
            == "recovered_via_declared_fallback_only"
        )
    return evidence.get("reported_success_path") in {None, "", "primary"}


def _canonical_mapping(value: Mapping[str, Any], reason_code: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise CodingParticipantError(reason_code)
    try:
        return json.loads(
            json.dumps(
                dict(value),
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            )
        )
    except (TypeError, ValueError) as error:
        raise CodingParticipantError(reason_code) from error


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and _SHA256_PATTERN.fullmatch(value) is not None


def _require_sha256(value: Any, reason_code: str) -> str:
    if not _is_sha256(value):
        raise CodingParticipantError(reason_code)
    return str(value)


def _artifact_disk_findings(artifact: Mapping[str, Any]) -> list[str]:
    root_text = str(artifact.get("workspace_root") or "")
    root = Path(root_text).resolve()
    findings: list[str] = []
    changed = artifact.get("changed_files")
    if not root_text or not root.is_dir() or not isinstance(changed, list):
        return ["artifact_workspace_or_changed_files_invalid"]
    normalized: list[dict[str, Any]] = []
    for item in changed:
        if not isinstance(item, Mapping):
            findings.append("artifact_changed_file_invalid")
            continue
        relative = str(item.get("path") or "").replace("\\", "/")
        target = (root / relative).resolve()
        try:
            target.relative_to(root)
        except ValueError:
            findings.append(f"artifact_path_escape:{relative}")
            continue
        expected = str(item.get("sha256_after") or "")
        actual = _sha256_file(target) if target.is_file() else None
        if actual != expected:
            findings.append(f"artifact_result_hash_mismatch:{relative}")
        normalized.append(
            {
                "path": relative,
                "sha256_before": item.get("sha256_before"),
                "sha256_after": expected,
                "missing_before_apply": bool(item.get("missing_before_apply")),
            }
        )
    normalized.sort(key=lambda item: item["path"])
    if _sha256_json(normalized) != artifact.get("result_sha256"):
        findings.append("artifact_result_manifest_hash_mismatch")
    return findings


def _read_approved_diff(artifact: Mapping[str, Any]) -> str:
    root = Path(str(artifact.get("workspace_root") or "")).resolve()
    relative = str(artifact.get("approved_diff_path") or "").replace("\\", "/")
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise CodingParticipantError("coding_artifact_diff_path_escape") from error
    try:
        value = path.read_text(encoding="utf-8")
    except OSError as error:
        raise CodingParticipantError("coding_artifact_diff_unavailable") from error
    if hashlib.sha256(value.encode("utf-8")).hexdigest() != artifact.get("approved_diff_sha256"):
        raise CodingParticipantError("coding_artifact_diff_file_hash_mismatch")
    return value


def _required_text(value: Any, reason_code: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CodingParticipantError(reason_code)
    return value.strip()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _worker_main() -> int:
    try:
        payload = json.load(sys.stdin)
        if payload.get("schema_version") != "coding.participant-worker-request/v1":
            raise CodingParticipantError("coding_participant_worker_request_invalid")
        if payload.get("expected_executable_sha256") != _sha256_file(
            Path(sys.executable).resolve()
        ):
            raise CodingParticipantError("coding_participant_worker_executable_mismatch")
        if payload.get("expected_entrypoint_sha256") != _sha256_file(Path(__file__).resolve()):
            raise CodingParticipantError("coding_participant_worker_entrypoint_mismatch")
        role = str(payload.get("role") or "")
        artifact = payload.get("artifact")
        consumed = payload.get("consumed_input")
        if not isinstance(artifact, Mapping) or not isinstance(consumed, Mapping):
            raise CodingParticipantError("coding_participant_worker_request_invalid")
        if role == "coding-reviewer":
            record = run_coding_reviewer(artifact)
        elif role == "coding-verifier":
            verification = consumed.get("verification")
            if not isinstance(verification, Mapping):
                raise CodingParticipantError("coding_verifier_input_invalid")
            record = run_coding_verifier(artifact, verification)
        elif role == "coding-anti-cheat":
            model_evidence = consumed.get("model_evidence")
            if not isinstance(model_evidence, Mapping):
                raise CodingParticipantError("coding_anti_cheat_model_evidence_invalid")
            record = run_coding_anti_cheat(artifact, model_evidence=model_evidence)
        elif role == "evidence-recorder":
            participant_records = consumed.get("participant_records")
            if not isinstance(participant_records, list):
                raise CodingParticipantError("coding_evidence_participant_record_invalid")
            record = run_coding_evidence_recorder(
                artifact,
                participant_records=[
                    item for item in participant_records if isinstance(item, Mapping)
                ],
            )
        else:
            raise CodingParticipantError("coding_participant_role_missing")
        print(json.dumps(record, sort_keys=True, separators=(",", ":")))
        return 0
    except Exception as error:
        print(
            str(getattr(error, "reason_code", "coding_participant_worker_failed")),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    if sys.argv[1:] != ["--worker"] or os.environ.get(_WORKER_MODE_ENV) != "1":
        raise SystemExit(2)
    raise SystemExit(_worker_main())
