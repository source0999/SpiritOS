from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from pathlib import Path

import pytest
import source_proxy.coding.participants as participant_module

from source_proxy.coding.participants import (
    MANUAL_DIFF_CLAIM_CEILING,
    CodingParticipantError,
    acknowledge_coding_participant_output,
    build_applied_artifact,
    build_coding_executor_output,
    participant_record_sha256,
    run_coding_anti_cheat,
    run_coding_evidence_recorder,
    run_coding_reviewer,
    run_coding_verifier,
    validate_coding_participant_record,
)


def _artifact(
    tmp_path: Path,
    *,
    semantic_review_identity: dict | None = None,
) -> dict:
    target = tmp_path / "fixture.txt"
    target.write_text("after\n", encoding="utf-8")
    approved_diff = "diff --git a/fixture.txt b/fixture.txt\n"
    backup = tmp_path / ".spirit-backups" / "run"
    backup.mkdir(parents=True)
    (backup / "approved.diff").write_text(approved_diff, encoding="utf-8", newline="")
    execution = {
        "audit": {
            "workspace_root": str(tmp_path),
            "approved_diff_path": ".spirit-backups/run/approved.diff",
            "approved_diff_sha256": hashlib.sha256(approved_diff.encode()).hexdigest(),
            "changed_file_snapshots": [
                {
                    "path": "fixture.txt",
                    "sha256_before": hashlib.sha256(b"before\n").hexdigest(),
                    "sha256_after": hashlib.sha256(b"after\n").hexdigest(),
                    "missing_before_apply": False,
                }
            ],
        }
    }
    return build_applied_artifact(
        task_id="task-1",
        run_id="run-1",
        approval_id="apr_test",
        generation=1,
        approved_diff=approved_diff,
        execution=execution,
        provenance={
            "semantic_review_identity": semantic_review_identity or {},
        },
    )


def _semantic_review_binding(*, invalid_blocked_reasons: bool = False) -> dict:
    acceptance = [
        {
            "id": "response_semantics",
            "description": "The requested response semantics are implemented.",
            "kind": "behavioral",
        }
    ]
    plan = {"plan_id": "plan-task-1", "task_id": "task-1"}
    task_spec = {"task_id": "task-1", "target": "fixture.txt"}
    exact_feedback = {
        "blocked_reasons": ["expected status 204 but received 200"],
    }
    repair_body = {
        "schema_version": "coding.semantic-repair-feedback/v1",
        "parent_attempt_id": "attempt-1",
        "parent_attempt_seal_sha256": "sha256:" + "1" * 64,
        "failure_class": "verifier_rejection",
        "source_lane": "verifier",
        "exact_feedback": exact_feedback,
        "feedback_sha256": participant_module._sha256_json(exact_feedback),
        "blocked_reasons": (
            ["forged pass"]
            if invalid_blocked_reasons
            else exact_feedback["blocked_reasons"]
        ),
        "repair_diagnostic_sha256": "sha256:" + "2" * 64,
    }
    repair_feedback = dict(repair_body)
    repair_feedback["repair_feedback_sha256"] = participant_module._sha256_json(
        repair_body
    )
    review_report = {"passed": True, "findings": []}
    receipt_body = {
        "schema_version": "coding.preview-review-receipt/v1",
        "reviewer": "source-proxy.planning.reviewer.deterministic/v1",
        "task_id": "task-1",
        "run_id": "run-1",
        "attempt_id": "attempt-2",
        "server_plan_id": "plan-task-1",
        "server_plan_sha256": participant_module._sha256_json(plan),
        "server_task_spec_sha256": participant_module._sha256_json(task_spec),
        "acceptance_criteria_sha256": participant_module._sha256_json(acceptance),
        "acceptance_criterion_ids": ["response_semantics"],
        "proposed_diff_sha256": hashlib.sha256(
            b"diff --git a/fixture.txt b/fixture.txt\n"
        ).hexdigest(),
        "changed_files": ["fixture.txt"],
        "deterministic_review_report": review_report,
        "deterministic_review_report_sha256": participant_module._sha256_json(
            review_report
        ),
        "adapter_preview_evidence": None,
        "adapter_preview_evidence_sha256": None,
        "repair_feedback_sha256": repair_feedback["repair_feedback_sha256"],
        "blocked_reasons": [],
        "status": "passed",
    }
    receipt = dict(receipt_body)
    receipt["receipt_sha256"] = participant_module._sha256_json(receipt_body)
    binding_body = {
        "schema_version": "coding.semantic-review-binding/v1",
        "server_plan": plan,
        "server_plan_sha256": participant_module._sha256_json(plan),
        "server_task_spec": task_spec,
        "server_task_spec_sha256": participant_module._sha256_json(task_spec),
        "acceptance_criteria": acceptance,
        "acceptance_criteria_sha256": participant_module._sha256_json(acceptance),
        "preview_review_receipt": receipt,
        "preview_review_receipt_sha256": receipt["receipt_sha256"],
        "repair_feedback": repair_feedback,
        "repair_feedback_sha256": repair_feedback["repair_feedback_sha256"],
    }
    binding = dict(binding_body)
    binding["semantic_review_binding_sha256"] = participant_module._sha256_json(
        binding_body
    )
    return binding


def _executor_record(artifact: dict) -> dict:
    result = {
        "passed": True,
        "applied_diff_sha256": artifact["approved_diff_sha256"],
        "result_sha256": artifact["result_sha256"],
        "changed_files": [item["path"] for item in artifact["changed_files"]],
    }
    return {
        "schema_version": "coding.participant-invocation/v1",
        "role": "coding-executor",
        "service": "source-proxy.tasks.long_running.execute-approved/v1",
        "provider": "source-proxy",
        "model": "canonical-diff-executor",
        "task_id": artifact["task_id"],
        "run_id": artifact["run_id"],
        "artifact_sha256": artifact["artifact_sha256"],
        "invocation_id": "executor-invocation-1",
        "input_sha256": artifact["approved_diff_sha256"],
        "output_id": "executor-output-1",
        "output_sha256": hashlib.sha256(
            json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "consumer_acknowledgement_id": "executor-ack-1",
        "started_at": "2026-07-17T00:00:00Z",
        "completed_at": "2026-07-17T00:00:01Z",
        "passed": True,
        "result": result,
    }


def test_independent_participants_consume_one_immutable_artifact(tmp_path: Path) -> None:
    source_root = Path(participant_module.__file__).resolve().parents[1]
    bytecode_before = {
        path.relative_to(source_root).as_posix(): (
            path.stat().st_size,
            path.stat().st_mtime_ns,
        )
        for path in source_root.rglob("*.pyc")
    }
    artifact = _artifact(tmp_path)
    executor = _executor_record(artifact)
    assert validate_coding_participant_record(
        executor,
        artifact,
        expected_role="coding-executor",
    ) == executor
    reviewer = run_coding_reviewer(artifact)
    verifier = run_coding_verifier(
        artifact,
        {
            "status": "verified",
            "checks": [{"id": "focused", "required": True, "status": "passed"}],
            "manual_browser_check_required": False,
        },
    )
    anti_cheat = run_coding_anti_cheat(
        artifact,
        model_evidence={"provider_available": True, "provider_result": "success"},
    )
    evidence = run_coding_evidence_recorder(
        artifact,
        participant_records=[executor, reviewer, verifier, anti_cheat],
    )

    records = [reviewer, verifier, anti_cheat, evidence]
    assert all(record["passed"] is True for record in records)
    assert {record["artifact_sha256"] for record in records} == {artifact["artifact_sha256"]}
    assert len({record["invocation_id"] for record in records}) == 4
    assert len({record["output_id"] for record in records}) == 4
    assert len({record["consumer_acknowledgement_id"] for record in records}) == 4
    assert all(record["schema_version"] == "coding.participant-invocation/v2" for record in records)
    assert all(
        record["producer_process"]["isolation"] == "dedicated_participant_subprocess"
        and record["producer_process"]["process_id"] != os.getpid()
        and record["producer_process"]["parent_process_id"] == os.getpid()
        and record["consumer_acknowledgement"]["consumer_process_id"] == os.getpid()
        and record["consumer_acknowledgement"]["output_sha256"] == record["output_sha256"]
        for record in records
    )
    assert evidence["result"]["truth_status"] == "PASS"
    assert evidence["result"]["claim_ceiling"] == MANUAL_DIFF_CLAIM_CEILING
    assert evidence["result"]["terminal_proof_eligible"] is False
    receipt_records = evidence["result"]["receipt"]["participant_records"]
    assert {item["role"] for item in receipt_records} == {
        "coding-executor",
        "coding-reviewer",
        "coding-verifier",
        "coding-anti-cheat",
    }
    assert all(item["record_sha256"].startswith("sha256:") for item in receipt_records)
    assert next(
        item for item in receipt_records if item["role"] == "coding-verifier"
    )["result"]["verdict"] == "PASS"
    bytecode_after = {
        path.relative_to(source_root).as_posix(): (
            path.stat().st_size,
            path.stat().st_mtime_ns,
        )
        for path in source_root.rglob("*.pyc")
    }
    assert bytecode_after == bytecode_before


def test_reviewer_consumes_bound_acceptance_and_exact_repair_blockers(
    tmp_path: Path,
) -> None:
    semantic = _semantic_review_binding()
    artifact = _artifact(tmp_path, semantic_review_identity=semantic)

    reviewer = run_coding_reviewer(artifact)

    assert reviewer["passed"] is True
    assert reviewer["result"]["blocked_reasons"] == []
    assert reviewer["result"]["semantic_review_input_sha256"] == (
        participant_module._sha256_json(semantic)
    )
    consumed = reviewer["result"]["semantic_review"]
    assert consumed["status"] == "passed"
    assert consumed["acceptance_criteria"] == [
        {
            "id": "response_semantics",
            "kind": "behavioral",
            "description": "The requested response semantics are implemented.",
            "status": "consumed_from_successful_preview",
        }
    ]
    assert consumed["repair_feedback"] == {
        "status": "consumed",
        "source_lane": "verifier",
        "feedback_sha256": semantic["repair_feedback"]["feedback_sha256"],
        "repair_feedback_sha256": semantic["repair_feedback_sha256"],
        "blocked_reasons": ["expected status 204 but received 200"],
    }


def test_reviewer_rejects_rehashed_repair_blocker_drift(tmp_path: Path) -> None:
    semantic = _semantic_review_binding(invalid_blocked_reasons=True)
    artifact = _artifact(tmp_path, semantic_review_identity=semantic)

    reviewer = run_coding_reviewer(artifact)

    assert reviewer["passed"] is False
    assert "semantic_repair_feedback_binding_invalid" in reviewer["result"][
        "blocked_reasons"
    ]


def test_executor_creates_its_output_and_orchestrator_creates_the_acknowledgement(
    tmp_path: Path,
) -> None:
    artifact = _artifact(tmp_path)
    result = {
        "passed": True,
        "applied_diff_sha256": artifact["approved_diff_sha256"],
        "result_sha256": artifact["result_sha256"],
        "changed_files": ["fixture.txt"],
    }

    output = build_coding_executor_output(
        artifact,
        result=result,
        started_at="2026-07-17T00:00:00Z",
    )
    record = acknowledge_coding_participant_output(
        output,
        artifact,
        consumer_service="source-proxy.coding.orchestrator/v2",
    )

    assert output["schema_version"] == "coding.participant-output/v2"
    assert "consumer_acknowledgement_id" not in output
    assert record["schema_version"] == "coding.participant-invocation/v2"
    assert record["consumer_acknowledgement"]["producer_record_sha256"] == output[
        "producer_record_sha256"
    ]
    assert record["consumer_acknowledgement"]["output_id"] == output["output_id"]


def test_reviewer_and_verifier_fail_after_result_tampering(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    (tmp_path / "fixture.txt").write_text("tampered\n", encoding="utf-8")

    reviewer = run_coding_reviewer(artifact)
    verifier = run_coding_verifier(
        artifact,
        {
            "status": "verified",
            "checks": [{"id": "focused", "required": True, "status": "passed"}],
            "manual_browser_check_required": False,
        },
    )

    assert reviewer["passed"] is False
    assert verifier["passed"] is False
    assert "artifact_result_hash_mismatch:fixture.txt" in reviewer["result"]["findings"]


def test_evidence_recorder_rejects_missing_or_failed_participant(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    reviewer = run_coding_reviewer(artifact)

    evidence = run_coding_evidence_recorder(
        artifact,
        participant_records=[reviewer],
    )

    assert evidence["passed"] is False
    assert "coding-executor" in evidence["result"]["receipt"]["missing"]


def test_participant_input_hashes_bind_role_specific_consumed_evidence(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)
    verification = {
        "status": "verified",
        "checks": [{"id": "focused", "required": True, "status": "passed"}],
        "manual_browser_check_required": False,
    }
    changed_verification = deepcopy(verification)
    changed_verification["checks"][0]["id"] = "different-check"

    first_verifier = run_coding_verifier(artifact, verification)
    second_verifier = run_coding_verifier(artifact, changed_verification)
    first_anti_cheat = run_coding_anti_cheat(
        artifact,
        model_evidence={"provider_available": True, "provider_result": "success"},
    )
    second_anti_cheat = run_coding_anti_cheat(
        artifact,
        model_evidence={"provider_available": False, "provider_result": "failed"},
    )

    assert first_verifier["consumed_input_sha256"] != second_verifier["consumed_input_sha256"]
    assert first_verifier["input_sha256"] != second_verifier["input_sha256"]
    assert first_anti_cheat["consumed_input_sha256"] != second_anti_cheat["consumed_input_sha256"]
    assert first_anti_cheat["input_sha256"] != second_anti_cheat["input_sha256"]
    assert validate_coding_participant_record(
        first_verifier,
        artifact,
        expected_role="coding-verifier",
        consumed_input={"verification": verification},
    ) == first_verifier
    with pytest.raises(CodingParticipantError, match="coding_participant_consumed_input_mismatch"):
        validate_coding_participant_record(
            first_verifier,
            artifact,
            expected_role="coding-verifier",
            consumed_input={"verification": changed_verification},
        )


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda value: value.update(schema_version="wrong"), "record_schema_invalid"),
        (lambda value: value.update(service="wrong"), "service_invalid"),
        (lambda value: value.update(role="coding-verifier"), "role_mismatch"),
        (lambda value: value.update(artifact_sha256="sha256:" + "0" * 64), "artifact_binding_mismatch"),
        (lambda value: value.update(input_sha256="sha256:" + "0" * 64), "input_hash_mismatch"),
        (
            lambda value: value["result"].update(reviewed_result_sha256="sha256:" + "0" * 64),
            "output_hash_mismatch",
        ),
        (lambda value: value.update(record_sha256="sha256:" + "0" * 64), "record_hash_mismatch"),
        (
            lambda value: value["producer_process"].update(isolation="same_process_callback"),
            "process_identity_invalid",
        ),
        (
            lambda value: value["consumer_acknowledgement"].update(output_id="forged-output"),
            "acknowledgement_binding_invalid",
        ),
    ],
)
def test_strict_participant_validator_rejects_tampering(
    tmp_path: Path,
    mutation,
    reason: str,
) -> None:
    artifact = _artifact(tmp_path)
    reviewer = run_coding_reviewer(artifact)
    tampered = deepcopy(reviewer)
    mutation(tampered)

    with pytest.raises(CodingParticipantError, match=reason):
        validate_coding_participant_record(
            tampered,
            artifact,
            expected_role="coding-reviewer",
        )


def test_manual_diff_anti_cheat_is_honest_and_keeps_lower_claim_ceiling(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)

    record = run_coding_anti_cheat(artifact)

    assert record["passed"] is True
    assert record["result"]["model_authorship_proven"] is False
    assert record["result"]["terminal_proof_eligible"] is False
    assert record["result"]["claim_ceiling"] == MANUAL_DIFF_CLAIM_CEILING
    assert record["result"]["fallback_used"] is False


def test_incomplete_terminal_model_claim_fails_closed(tmp_path: Path) -> None:
    artifact = _artifact(tmp_path)

    record = run_coding_anti_cheat(
        artifact,
        model_evidence={
            "terminal_proof_eligible": True,
            "proof_eligible": True,
            "provider_available": True,
            "provider_result": "success",
        },
    )

    assert record["passed"] is False
    assert record["result"]["terminal_proof_eligible"] is False
    assert record["result"]["claim_ceiling"] == MANUAL_DIFF_CLAIM_CEILING
    assert any(
        violation["violation_code"] == "terminal_model_authorship_unproven"
        for violation in record["result"]["violations"]
    )


def test_complete_router_model_provenance_can_raise_only_the_model_claim_ceiling(
    tmp_path: Path,
) -> None:
    artifact = _artifact(tmp_path)
    model_evidence = {
        "proof_eligible": True,
        "provider_available": True,
        "provider_result": "success",
        "provider": "ollama",
        "model": "qwen2.5-coder:7b",
        "generation_source": "model",
        "provider_transport": "model_router",
        "model_invocation_id": "model-invocation-1",
        "model_output_sha256": "sha256:" + "1" * 64,
        "raw_model_response_sha256": "sha256:" + "2" * 64,
        "reported_success_path": "primary",
        "fallback_used": False,
    }

    record = run_coding_anti_cheat(artifact, model_evidence=model_evidence)

    assert record["passed"] is True
    assert record["result"]["model_authorship_proven"] is True
    assert record["result"]["terminal_proof_eligible"] is True
    assert record["result"]["claim_ceiling"] != MANUAL_DIFF_CLAIM_CEILING


def test_evidence_recorder_hashes_each_record_and_rejects_tampered_result(
    tmp_path: Path,
) -> None:
    artifact = _artifact(tmp_path)
    executor = _executor_record(artifact)
    reviewer = run_coding_reviewer(artifact)
    verification = {
        "status": "verified",
        "checks": [{"id": "focused", "required": True, "status": "passed"}],
        "manual_browser_check_required": False,
    }
    verifier = run_coding_verifier(artifact, verification)
    anti_cheat = run_coding_anti_cheat(artifact)
    records = [executor, reviewer, verifier, anti_cheat]

    evidence = run_coding_evidence_recorder(artifact, participant_records=records)
    assert evidence["passed"] is True
    receipt = evidence["result"]["receipt"]
    assert receipt["participant_records_sha256"].startswith("sha256:")
    expected_hashes = {
        item["role"]: participant_record_sha256(item) for item in records
    }
    assert {
        item["role"]: item["record_sha256"] for item in receipt["participant_records"]
    } == expected_hashes

    tampered = deepcopy(records)
    tampered[2]["result"]["verdict"] = "FAIL"
    rejected = run_coding_evidence_recorder(artifact, participant_records=tampered)
    assert rejected["passed"] is False
    assert any(
        value.startswith("coding-verifier:coding_participant_output_hash_mismatch")
        for value in rejected["result"]["receipt"]["invalid"]
    )
