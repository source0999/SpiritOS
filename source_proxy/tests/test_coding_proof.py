from __future__ import annotations

import copy
import hashlib
import json
from types import SimpleNamespace
from typing import Any

import pytest

import source_proxy.tasks.long_running as long_running_module
from source_proxy.coding.participants import (
    PARTICIPANT_OUTPUT_SCHEMA,
    PARTICIPANT_RECORD_SCHEMA,
    PARTICIPANT_SERVICES,
    acknowledge_coding_participant_output,
    build_coding_executor_output,
    participant_record_sha256,
    run_coding_evidence_recorder,
)
from source_proxy.coding.proof import derive_production_proof
from source_proxy.coding.recovery import (
    ControlledRecoveryLineage,
    RecoveryPolicy,
    build_failed_participant_event,
)
from source_proxy.coding.runtime_lane_boundary import RuntimeLaneBoundary
from source_proxy.contracts.coding_lane_contracts import canonical_coding_lane_contracts
from source_proxy.tasks.long_running import LongRunningTaskError


SOURCE_HEAD = "a" * 40
TASK_ID = "task-production-proof"
RUN_ID = "run-production-proof"
TARGET = "tests/ui-agent-trials/fixtures/dummy-product-site/index.html"
APPROVED_DIFF = (
    f"diff --git a/{TARGET} b/{TARGET}\n"
    f"--- a/{TARGET}\n"
    f"+++ b/{TARGET}\n"
    "@@ -1 +1 @@\n-old\n+new\n"
)


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _service_participant(
    *,
    role: str,
    artifact: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    service = PARTICIPANT_SERVICES[role]
    consumed_input_sha256 = _sha256_json({"role": role, "source": "test"})
    normalized_result = dict(result)
    normalized_result["consumed_input_sha256"] = consumed_input_sha256
    output = {
        "schema_version": PARTICIPANT_OUTPUT_SCHEMA,
        "role": role,
        "service": service,
        "provider": "source-proxy",
        "model": service,
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "artifact_sha256": artifact["artifact_sha256"],
        "invocation_id": f"{role}-invocation",
        "consumed_input_sha256": consumed_input_sha256,
        "input_sha256": _sha256_json(
            {
                "artifact_sha256": artifact["artifact_sha256"],
                "consumed_input_sha256": consumed_input_sha256,
                "role": role,
                "service": service,
            }
        ),
        "output_id": f"{role}-participant-output",
        "output_sha256": _sha256_json(normalized_result),
        "started_at": "2026-07-17T00:00:10Z",
        "completed_at": "2026-07-17T00:00:11Z",
        "passed": normalized_result["passed"],
        "result": normalized_result,
        "producer_process": {
            "process_id": 10001 + len(role),
            "parent_process_id": 10000,
            "executable_sha256": "1" * 64,
            "entrypoint_sha256": "2" * 64,
            "isolation": "dedicated_participant_subprocess",
            "worker_nonce": f"participant-worker-{role}",
        },
    }
    output["producer_record_sha256"] = _sha256_json(output)
    return acknowledge_coding_participant_output(
        output,
        artifact,
        consumer_service="source-proxy.coding.orchestrator/v2",
    )


def _model_participant(*, fallback: bool) -> dict[str, Any]:
    output_provenance = _model_output_provenance()
    return {
        "schema_version": "coding.recovery-participant/v1",
        "role": "target-plugin-model",
        "lane_id": "coder",
        "run_id": RUN_ID,
        "task_id": TASK_ID,
        "attempt_id": "attempt-fallback" if fallback else "attempt-primary",
        "invocation_id": "model-fallback" if fallback else "model-primary",
        "output_id": "model-fallback-output" if fallback else "model-primary-output",
        "provider": "provider-fallback" if fallback else "provider-primary",
        "model": "model-fallback" if fallback else "model-primary",
        "input_sha256": _sha256_json({"task": TASK_ID, "context": "context-hash"}),
        "output_sha256": _sha256_json(output_provenance),
        "artifact_sha256": _sha256_json(
            {"proposed_diff": APPROVED_DIFF, "changed_files": [TARGET]}
        ),
        "result_id": "target-plugin-result",
        "error_code": None,
        "error_message": None,
        "started_at": "2026-07-17T00:00:03Z",
        "completed_at": "2026-07-17T00:00:04Z",
        "passed": True,
    }


def _failed_model_participant(selected: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "coding.recovery-participant/v1",
        "role": "target-plugin-model",
        "lane_id": "coder",
        "run_id": RUN_ID,
        "task_id": TASK_ID,
        "attempt_id": "attempt-primary",
        "invocation_id": "model-primary",
        "output_id": "model-primary-output",
        "provider": "provider-primary",
        "model": "model-primary",
        "input_sha256": selected["input_sha256"],
        "output_sha256": _sha256_json({"failure": "provider_timeout"}),
        "artifact_sha256": None,
        "result_id": None,
        "error_code": "provider_timeout",
        "error_message": "primary provider timed out",
        "started_at": "2026-07-17T00:00:00Z",
        "completed_at": "2026-07-17T00:00:01Z",
        "passed": False,
    }


def _adapter_provenance() -> dict[str, Any]:
    return {
        "schema_version": "spiritos-target-adapter-provenance/v1",
        "rendered_prompt_sha256": "1" * 64,
        "raw_response_sha256": "2" * 64,
        "transport_kind": "canonical_litellm_router",
        "provider_call_made": True,
        "provider_call_authorized": True,
        "generation_source": "model",
        "terminal_proof_eligible": True,
    }


def _model_output_provenance() -> dict[str, Any]:
    return {
        "schema_version": "coding.target-plugin-model-output-provenance/v1",
        "approved_diff_sha256": hashlib.sha256(APPROVED_DIFF.encode("utf-8")).hexdigest(),
        "changed_files": [TARGET],
        "blocked": False,
        "reason_code": "model_bundle_ready",
        "target_adapter_provenance": _adapter_provenance(),
    }


def _production_state(*, fallback: bool = False) -> dict[str, Any]:
    contracts = canonical_coding_lane_contracts()
    boundary = RuntimeLaneBoundary()
    outputs: list[dict[str, Any]] = []
    acknowledgements: list[dict[str, Any]] = []
    consumptions: list[dict[str, Any]] = []

    def issue(lane_id: str, producer: str, payload: dict[str, Any]) -> dict[str, Any]:
        output = boundary.issue_output(
            lane_id=lane_id,
            contract_version=contracts[lane_id]["contract_version"],
            producer_invocation_id=producer,
            payload=payload,
        ).to_payload()
        outputs.append(output)
        return output

    def consume(
        output: dict[str, Any],
        *,
        consumer: str,
        payload: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        acknowledgement = boundary.record_consumer_acknowledgement(
            output_id=output["output_id"],
            consumer_version="coding-orchestrator/v1",
            consumer_invocation_id=consumer,
            payload=payload,
        )
        consumption = boundary.mark_output_consumed(
            output_id=output["output_id"],
            acknowledgement_id=acknowledgement.acknowledgement_id,
        )
        acknowledgement_payload = acknowledgement.to_payload()
        consumption_payload = consumption.to_payload()
        acknowledgements.append(acknowledgement_payload)
        consumptions.append(consumption_payload)
        return acknowledgement_payload, consumption_payload

    canonical_context_report = {
        "schema_version": "canonical-context-broker/v1",
        "canonical": True,
        "canonical_report_hash": "context-hash",
        "go_eligible": True,
    }
    context_output = issue(
        "context-broker",
        "context-producer",
        {"context_hash": "context-hash", "verdict": "GO"},
    )
    planner_context_output = issue(
        "context-broker",
        "planner-context-producer",
        {"context_hash": "context-hash", "verdict": "GO"},
    )
    planner_output = issue(
        "planner",
        "planner-producer",
        {"plan_id": "plan-1", "task_spec": {"task": TASK_ID}},
    )
    selected_model = _model_participant(fallback=fallback)
    model_context_output = issue(
        "context-broker",
        "model-context-producer",
        {"context_hash": "context-hash", "verdict": "GO"},
    )
    consume(
        context_output,
        consumer="context-refresh-consumer",
        payload={"consumer": "context-refresh", "context_hash": "context-hash"},
    )
    consume(
        planner_context_output,
        consumer="planner-consumer",
        payload={"consumer": "planner", "context_hash": "context-hash"},
    )
    model_context_ack, model_context_consumption = consume(
        model_context_output,
        consumer=selected_model["invocation_id"],
        payload={"consumer": "coder", "context_hash": "context-hash"},
    )
    coder_output = issue(
        "coder",
        selected_model["invocation_id"],
        {"approved_diff": APPROVED_DIFF, "changed_files": [TARGET]},
    )
    proposal = {
        "schema_version": "coding.target-plugin-proposal/v1",
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "runtime_output_id": coder_output["output_id"],
        "runtime_output_artifact_sha256": coder_output["artifact_hash"],
        "producer_model_invocation_id": selected_model["invocation_id"],
        "producer_model_output_sha256": selected_model["output_sha256"],
        "producer_model_artifact_sha256": selected_model["artifact_sha256"],
        "model_output_provenance": _model_output_provenance(),
        "target_adapter_provenance": _adapter_provenance(),
        "target_plugin_identity": {
            "plugin_id": "lumacart",
            "repository_id": "repo",
            "worktree_id": "worktree",
            "source_head": SOURCE_HEAD,
            "selected_prompt_id": "coder-004-add-search-filter",
        },
        "selected_prompt_id": "coder-004-add-search-filter",
        "selected_context_id": "search-filter",
        "context_hash": "context-hash",
        "canonical_context_report": canonical_context_report,
        "canonical_context_report_sha256": _sha256_json(canonical_context_report),
        "context_runtime_output_id": model_context_output["output_id"],
        "context_runtime_artifact_sha256": model_context_output["artifact_hash"],
        "context_consumer_acknowledgement_id": model_context_ack[
            "acknowledgement_id"
        ],
        "context_consumption_id": model_context_consumption["consumption_id"],
        "source_head": SOURCE_HEAD,
        "target": TARGET,
        "approved_diff_sha256": hashlib.sha256(APPROVED_DIFF.encode("utf-8")).hexdigest(),
        "changed_files": [TARGET],
        "status": "ready_for_approval_preview",
    }
    proposal["proposal_binding_sha256"] = _sha256_json(proposal)

    cart_consumer = selected_model["invocation_id"]
    transfer = {
        "proposal_id": "cart-proposal",
        "selection_id": "cart-selection",
        "selection_generation": 1,
        "transfer_event_id": "cart-transfer-event",
        "downstream_consumer_invocation_id": cart_consumer,
        "target": TARGET,
        "provenance": {"source_head": SOURCE_HEAD},
    }
    cart_ack = {
        "schema_version": "cartographer.downstream-acknowledgement/v2",
        "acknowledgement_id": "cart-ack",
        "transfer_event_id": "cart-transfer-event",
        "consumer_invocation_id": cart_consumer,
        "consumer_output_id": selected_model["output_id"],
        "consumer_output_sha256": selected_model["output_sha256"],
        "consumer_artifact_sha256": selected_model["artifact_sha256"],
        "consumer_completed_at": selected_model["completed_at"],
        "consumer_passed": True,
        "consumed": True,
    }
    cart_finalization = {
        "state": "consumed",
        "downstream_acknowledgement": cart_ack,
        "authority_receipt": {"state": "consumed"},
    }
    cart_identity = {
        "proposal_id": "cart-proposal",
        "selection_id": "cart-selection",
        "selection_generation": 1,
        "transfer_event_id": "cart-transfer-event",
        "consumer_invocation_id": cart_consumer,
        "acknowledgement_id": "cart-ack",
        "authority_state": "consumed",
        "source_head": SOURCE_HEAD,
    }
    artifact = {
        "schema_version": "coding.immutable-applied-artifact/v2",
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "approval_id": "coding-approval",
        "generation": 1,
        "approved_diff_sha256": hashlib.sha256(APPROVED_DIFF.encode("utf-8")).hexdigest(),
        "result_sha256": _sha256_json([{"path": TARGET, "sha256_after": "3" * 64}]),
        "workspace_root": "/tmp/spiritos-proof",
        "approved_diff_path": "/tmp/spiritos-proof/approved.diff",
        "changed_files": [
            {
                "path": TARGET,
                "sha256_before": "4" * 64,
                "sha256_after": "3" * 64,
                "missing_before_apply": False,
            }
        ],
        "source_commit": SOURCE_HEAD,
        "repository_identity": {
            "repository": "SpiritOS",
            "worktree": "foundation-r1",
            "root": "/tmp/spiritos-proof",
        },
        "target_plugin_identity": copy.deepcopy(proposal["target_plugin_identity"]),
        "prompt_identity": {
            "selected_prompt_id": proposal["selected_prompt_id"],
            "proposal_binding_sha256": proposal["proposal_binding_sha256"],
        },
        "context_identity": {
            "context_hash": proposal["context_hash"],
            "selected_context_id": proposal["selected_context_id"],
        },
        "model_output_identity": {
            key: proposal[key]
            for key in (
                "runtime_output_id",
                "runtime_output_artifact_sha256",
                "producer_model_invocation_id",
                "producer_model_output_sha256",
                "producer_model_artifact_sha256",
                "approved_diff_sha256",
            )
        },
        "cartographer_identity": cart_identity,
        "claim_ceiling": "model_authored_diff_pending_independent_verification",
    }
    artifact["artifact_sha256"] = _sha256_json(artifact)

    executor_result = {"passed": True, "status": "applied"}
    executor = acknowledge_coding_participant_output(
        build_coding_executor_output(
            artifact,
            result=executor_result,
            started_at="2026-07-17T00:00:06Z",
        ),
        artifact,
        consumer_service="source-proxy.coding.orchestrator/v2",
    )
    claim_ceiling = (
        "recovered_via_declared_fallback_only"
        if fallback
        else "model_authored_applied_diff_verified"
    )
    reviewer = _service_participant(
        role="coding-reviewer",
        artifact=artifact,
        result={"passed": True, "findings": []},
    )
    verifier = _service_participant(
        role="coding-verifier",
        artifact=artifact,
        result={"passed": True, "verdict": "PASS", "checks": []},
    )
    anti_cheat = _service_participant(
        role="coding-anti-cheat",
        artifact=artifact,
        result={
            "passed": True,
            "detector_ids": ["model_authorship_claim_completeness"],
            "violations": [],
            "model_authorship_proven": True,
            "terminal_proof_eligible": True,
            "claim_ceiling": claim_ceiling,
            "fallback_used": fallback,
        },
    )
    source_participants = [executor, reviewer, verifier, anti_cheat]
    evidence = run_coding_evidence_recorder(
        artifact,
        participant_records=source_participants,
    )
    participants = [*source_participants, evidence]

    reviewer_output = issue(
        "reviewer",
        reviewer["invocation_id"],
        {"passed": True, "findings": []},
    )
    verifier_output = issue(
        "verifier",
        verifier["invocation_id"],
        {"verdict": "PASS", "checks": []},
    )
    anti_output = issue(
        "anti-cheat",
        anti_cheat["invocation_id"],
        {
            "passed": True,
            "detector_ids": ["model_authorship_claim_completeness"],
            "violations": [],
        },
    )
    evidence_output = issue(
        "evidence-recorder",
        evidence["invocation_id"],
        {
            "receipt_id": evidence["result"]["receipt_id"],
            "truth_status": "PASS",
        },
    )

    consume(
        planner_output,
        consumer="coder-plan-consumer",
        payload={"context_hash": "context-hash"},
    )
    consume(
        coder_output,
        consumer=executor["invocation_id"],
        payload={"approval_id": "coding-approval", "generation": 1},
    )
    for lane_output, consumer in (
        (reviewer_output, "reviewer-consumer"),
        (verifier_output, "verifier-consumer"),
        (anti_output, "anti-consumer"),
        (evidence_output, "evidence-consumer"),
    ):
        consume(
            lane_output,
            consumer=consumer,
            payload={"approval_id": "coding-approval", "generation": 1},
        )

    model_invocations = [selected_model]
    recovery_lineage: list[dict[str, Any]] = []
    if fallback:
        failed_model = _failed_model_participant(selected_model)
        failure_event = build_failed_participant_event(
            failed_model,
            parent_event_id="model-call-event",
            recorded_at="2026-07-17T00:00:01Z",
        )
        authorization = ControlledRecoveryLineage.authorize(
            failed_event=failure_event,
            failed_participant=failed_model,
            policy=RecoveryPolicy(
                allow_fallback=True,
                allowed_replacement_routes=((selected_model["provider"], selected_model["model"]),),
            ),
            decision="fallback",
            replacement_attempt_id=selected_model["attempt_id"],
            replacement_provider=selected_model["provider"],
            replacement_model=selected_model["model"],
            recorded_at="2026-07-17T00:00:02Z",
        )
        completed = authorization.complete(
            replacement_participant=selected_model,
            recorded_at="2026-07-17T00:00:05Z",
        )
        model_invocations = [failed_model, selected_model]
        recovery_lineage = [completed.to_payload()]

    return {
        "schema_version": "coding-orchestrator/v2",
        "authoritative": True,
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "lane_sequence": [
            "context-broker",
            "planner",
            "coder",
            "reviewer",
            "verifier",
            "anti-cheat",
            "repair",
            "evidence-recorder",
        ],
        "lane_states": {
            "context-broker": "completed",
            "planner": "completed",
            "coder": "completed",
            "reviewer": "completed",
            "verifier": "completed",
            "anti-cheat": "completed",
            "repair": "skipped",
            "evidence-recorder": "running",
        },
        "runtime_outputs": outputs,
        "runtime_acknowledgements": acknowledgements,
        "runtime_consumptions": consumptions,
        "required_output_ids": [item["output_id"] for item in outputs],
        "participant_records": participants,
        "immutable_artifact": artifact,
        "target_plugin_proposal": proposal,
        "cartographer_transfer": transfer,
        "cartographer_finalization": cart_finalization,
        "recovery_lineage": recovery_lineage,
        "model_invocations": model_invocations,
    }


@pytest.mark.parametrize("fallback", [False, True])
def test_production_proof_accepts_exact_primary_and_controlled_fallback_runs(
    fallback: bool,
) -> None:
    proof = derive_production_proof(
        _production_state(fallback=fallback),
        expected_source_head=SOURCE_HEAD,
    )

    assert proof["failures"] == []
    assert proof["terminal_proof_eligible"] is True
    assert proof["claim_ceiling"] == (
        "recovered_via_declared_fallback_only"
        if fallback
        else "model_authored_applied_diff_verified"
    )


def test_production_proof_rejects_forged_runtime_consumption_binding() -> None:
    state = _production_state()
    state["runtime_consumptions"][0]["consumer_invocation_id"] = "forged-consumer"

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "runtime_lane_boundary_invalid" in proof["failures"]


def test_production_proof_revalidates_participant_result_and_record_hashes() -> None:
    state = _production_state()
    reviewer = next(
        item for item in state["participant_records"] if item["role"] == "coding-reviewer"
    )
    reviewer["result"]["findings"] = ["forged-pass"]

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "independent_participant_records_invalid" in proof["failures"]


def test_production_proof_binds_model_to_its_exact_context_consumption() -> None:
    state = _production_state()
    proposal = state["target_plugin_proposal"]
    acknowledgement = next(
        item
        for item in state["runtime_acknowledgements"]
        if item["acknowledgement_id"]
        == proposal["context_consumer_acknowledgement_id"]
    )
    consumption = next(
        item
        for item in state["runtime_consumptions"]
        if item["consumption_id"] == proposal["context_consumption_id"]
    )
    acknowledgement["consumer_invocation_id"] = "unrelated-context-consumer"
    consumption["consumer_invocation_id"] = "unrelated-context-consumer"

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "runtime_lane_boundary_invalid" not in proof["failures"]
    assert "model_context_consumption_binding_invalid" in proof["failures"]


def test_production_proof_rejects_semantically_nonterminal_evidence_after_reseal() -> None:
    state = _production_state()
    evidence = next(
        item for item in state["participant_records"] if item["role"] == "evidence-recorder"
    )
    evidence["result"]["terminal_proof_eligible"] = False
    evidence["output_sha256"] = _sha256_json(evidence["result"])
    evidence["record_sha256"] = participant_record_sha256(evidence)

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "evidence_recorder_terminal_proof_invalid" in proof["failures"]


def test_production_proof_rejects_ignored_malformed_recovery_record() -> None:
    state = _production_state()
    state["recovery_lineage"].append({"schema_version": "forged-recovery/v1"})

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "controlled_recovery_records_invalid" in proof["failures"]


def test_production_proof_rejects_duplicate_required_participant_role() -> None:
    state = _production_state()
    reviewer = copy.deepcopy(
        next(
            item
            for item in state["participant_records"]
            if item["role"] == "coding-reviewer"
        )
    )
    reviewer["invocation_id"] = "coding-reviewer-duplicate-invocation"
    reviewer["output_id"] = "coding-reviewer-duplicate-output"
    reviewer["consumer_acknowledgement_id"] = "coding-reviewer-duplicate-ack"
    reviewer["record_sha256"] = participant_record_sha256(reviewer)
    state["participant_records"].append(reviewer)

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "independent_participant_set_invalid" in proof["failures"]


def test_production_bound_finalization_blocks_nonterminal_independent_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state = _production_state()
    state["runtime_consumptions"][0]["consumer_invocation_id"] = "forged-consumer"
    artifact = state["immutable_artifact"]
    snapshot = {
        "campaign_2_approval": {
            "state": "consuming",
            "approval_id": "coding-approval",
            "generation": 1,
            "target_plugin_identity": {},
            "binding": {},
        },
        "coding_artifact": artifact,
        "canonical_context_broker": {
            "downstream_acknowledgements": {
                consumer: {"acknowledged": True}
                for consumer in (
                    "planner",
                    "coder",
                    "verifier",
                    "final_receipt_builder",
                )
            }
        },
    }
    task = SimpleNamespace(
        id=TASK_ID,
        status="verification_passed_pending_participants",
        ast_snapshot=snapshot,
    )
    monkeypatch.setattr(long_running_module, "_lookup_task", lambda _task_id: task)
    monkeypatch.setattr(
        long_running_module,
        "_ensure_ast_snapshot_dict",
        lambda _task: snapshot,
    )
    monkeypatch.setattr(
        long_running_module,
        "coding_orchestrator_state_for_task",
        lambda _task_id: state,
    )
    monkeypatch.setattr(long_running_module, "current_head", lambda: SOURCE_HEAD)

    with pytest.raises(LongRunningTaskError) as raised:
        long_running_module.prepare_orchestrated_coding_finalization(
            TASK_ID,
            participant_records=state["participant_records"],
            runtime_outputs=state["runtime_outputs"],
            runtime_acknowledgements=state["runtime_acknowledgements"],
            runtime_consumptions=state["runtime_consumptions"],
            orchestrator_state_sha256=long_running_module._coding_state_sha256(state),
        )

    assert raised.value.reason_code == "coding_production_proof_not_terminal"
    assert raised.value.diagnostics == {
        "truth_status": "BLOCKED_SAFE",
        "safe_block": True,
        "commit_safe": False,
        "claim_ceiling": "production_proof_not_established",
        "production_proof_failures": ["runtime_lane_boundary_invalid"],
    }
