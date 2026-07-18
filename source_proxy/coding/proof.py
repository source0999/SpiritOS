"""Independent validation of a persisted production coding-run proof."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any

from source_proxy.coding.participants import (
    participant_record_sha256,
    validate_coding_participant_record,
)
from source_proxy.coding.recovery import ControlledRecoveryLineage
from source_proxy.coding.runtime_lane_boundary import RuntimeLaneBoundary


PRODUCTION_PROOF_SCHEMA = "coding.production-proof/v1"
REQUIRED_ROLES = {
    "coding-executor",
    "coding-reviewer",
    "coding-verifier",
    "coding-anti-cheat",
    "evidence-recorder",
}
EXPECTED_RUNTIME_LANES = {
    "context-broker",
    "planner",
    "coder",
    "reviewer",
    "verifier",
    "anti-cheat",
    "evidence-recorder",
}
EXPECTED_LANE_SEQUENCE = (
    "context-broker",
    "planner",
    "coder",
    "reviewer",
    "verifier",
    "anti-cheat",
    "repair",
    "evidence-recorder",
)
PARTICIPANT_RUNTIME_LANES = {
    "coding-reviewer": "reviewer",
    "coding-verifier": "verifier",
    "coding-anti-cheat": "anti-cheat",
    "evidence-recorder": "evidence-recorder",
}
MODEL_INVOCATION_FIELDS = {
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
}


def derive_production_proof(
    state: Mapping[str, Any],
    *,
    expected_source_head: str,
) -> dict[str, Any]:
    """Recompute terminal eligibility without trusting a declared GO field."""

    failures: list[str] = []
    if state.get("schema_version") != "coding-orchestrator/v2" or state.get(
        "authoritative"
    ) is not True:
        failures.append("canonical_orchestrator_state_invalid")
    task_id = str(state.get("task_id") or "")
    run_id = str(state.get("run_id") or "")
    if not task_id or not run_id:
        failures.append("orchestrator_identity_missing")

    artifact = state.get("immutable_artifact")
    if not isinstance(artifact, Mapping):
        failures.append("immutable_artifact_missing")
        artifact = {}
    elif artifact.get("task_id") != task_id or artifact.get("run_id") != run_id:
        failures.append("immutable_artifact_run_binding_mismatch")
    if artifact.get("source_commit") != expected_source_head:
        failures.append("immutable_artifact_source_head_mismatch")
    repository_identity = artifact.get("repository_identity")
    if not isinstance(repository_identity, Mapping) or any(
        not str(repository_identity.get(key) or "")
        for key in ("repository", "worktree", "root")
    ):
        failures.append("immutable_artifact_repository_identity_missing")

    proposal = state.get("target_plugin_proposal")
    if not isinstance(proposal, Mapping):
        failures.append("target_plugin_proposal_missing")
        proposal = {}
    else:
        body = dict(proposal)
        recorded = str(body.pop("proposal_binding_sha256", ""))
        if not recorded or _sha256_json(body) != recorded:
            failures.append("target_plugin_proposal_hash_mismatch")
        if proposal.get("task_id") != task_id or proposal.get("run_id") != run_id:
            failures.append("target_plugin_proposal_run_binding_mismatch")
        if proposal.get("source_head") != expected_source_head:
            failures.append("target_plugin_proposal_source_head_mismatch")
        if proposal.get("status") != "ready_for_approval_preview":
            failures.append("target_plugin_proposal_not_applied_candidate")
    prompt_identity = artifact.get("prompt_identity")
    context_identity = artifact.get("context_identity")
    model_output_identity = artifact.get("model_output_identity")
    proposal_identity_failures: list[str] = []
    if artifact.get("target_plugin_identity") != proposal.get(
        "target_plugin_identity"
    ):
        proposal_identity_failures.append(
            "immutable_artifact_target_plugin_identity_mismatch"
        )
    if not isinstance(prompt_identity, Mapping):
        proposal_identity_failures.append("immutable_artifact_prompt_identity_missing")
    else:
        if prompt_identity.get("selected_prompt_id") != proposal.get(
            "selected_prompt_id"
        ):
            proposal_identity_failures.append(
                "immutable_artifact_prompt_id_mismatch"
            )
        if prompt_identity.get("proposal_binding_sha256") != proposal.get(
            "proposal_binding_sha256"
        ):
            proposal_identity_failures.append(
                "immutable_artifact_proposal_binding_sha256_mismatch"
            )
    if not isinstance(context_identity, Mapping):
        proposal_identity_failures.append("immutable_artifact_context_identity_missing")
    else:
        if context_identity.get("context_hash") != proposal.get("context_hash"):
            proposal_identity_failures.append(
                "immutable_artifact_context_hash_mismatch"
            )
        if context_identity.get("selected_context_id") != proposal.get(
            "selected_context_id"
        ):
            proposal_identity_failures.append(
                "immutable_artifact_selected_context_id_mismatch"
            )
    model_output_keys = (
        "runtime_output_id",
        "runtime_output_artifact_sha256",
        "producer_model_invocation_id",
        "producer_model_output_sha256",
        "producer_model_artifact_sha256",
        "approved_diff_sha256",
    )
    if not isinstance(model_output_identity, Mapping):
        proposal_identity_failures.append(
            "immutable_artifact_model_output_identity_missing"
        )
    else:
        for key in model_output_keys:
            if model_output_identity.get(key) != proposal.get(key):
                proposal_identity_failures.append(
                    f"immutable_artifact_model_output_{key}_mismatch"
                )
    if proposal_identity_failures:
        failures.extend(proposal_identity_failures)
        failures.append("immutable_artifact_proposal_identity_mismatch")

    model_invocations = _state_mapping_list(
        state,
        "model_invocations",
        failures,
        "model_invocation_records_invalid",
    )
    model_invocation_ids = [
        str(item.get("invocation_id") or "") for item in model_invocations
    ]
    model_output_ids = [str(item.get("output_id") or "") for item in model_invocations]
    if (
        not model_invocations
        or "" in model_invocation_ids
        or "" in model_output_ids
        or len(set(model_invocation_ids)) != len(model_invocation_ids)
        or len(set(model_output_ids)) != len(model_output_ids)
        or any(
            not _valid_model_invocation(item, task_id=task_id, run_id=run_id)
            for item in model_invocations
        )
    ):
        failures.append("model_invocation_records_invalid")
    selected_invocation_id = str(proposal.get("producer_model_invocation_id") or "")
    selected_model = next(
        (
            item
            for item in model_invocations
            if item.get("invocation_id") == selected_invocation_id
        ),
        None,
    )
    if not isinstance(selected_model, Mapping) or selected_model.get("passed") is not True:
        failures.append("model_invocation_success_missing")
        selected_model = {}
    if [
        str(item.get("invocation_id") or "")
        for item in model_invocations
        if item.get("passed") is True
    ] != [selected_invocation_id]:
        failures.append("model_invocation_success_set_invalid")
    adapter = proposal.get("target_adapter_provenance")
    if not isinstance(adapter, Mapping) or not (
        adapter.get("terminal_proof_eligible") is True
        and adapter.get("transport_kind") == "canonical_litellm_router"
        and adapter.get("provider_call_made") is True
        and adapter.get("provider_call_authorized") is True
        and adapter.get("generation_source") == "model"
        and _is_sha256(adapter.get("rendered_prompt_sha256"))
        and _is_sha256(adapter.get("raw_response_sha256"))
    ):
        failures.append("canonical_model_provenance_invalid")
        adapter = {}
    output_provenance = proposal.get("model_output_provenance")
    if not isinstance(output_provenance, Mapping) or (
        output_provenance.get("target_adapter_provenance") != adapter
    ):
        failures.append("model_adapter_provenance_binding_mismatch")
    if (
        selected_model.get("output_sha256")
        != proposal.get("producer_model_output_sha256")
        or selected_model.get("artifact_sha256")
        != proposal.get("producer_model_artifact_sha256")
        or _sha256_json(output_provenance or {})
        != selected_model.get("output_sha256")
    ):
        failures.append("model_output_provenance_mismatch")

    outputs = _state_mapping_list(
        state,
        "runtime_outputs",
        failures,
        "runtime_lane_records_invalid",
    )
    runtime_acknowledgements = _state_mapping_list(
        state,
        "runtime_acknowledgements",
        failures,
        "runtime_lane_records_invalid",
    )
    consumptions = _state_mapping_list(
        state,
        "runtime_consumptions",
        failures,
        "runtime_lane_records_invalid",
    )
    required_output_ids = state.get("required_output_ids")
    if not isinstance(required_output_ids, list) or any(
        not isinstance(item, str) or not item for item in required_output_ids
    ):
        failures.append("runtime_required_output_set_invalid")
        required_output_ids = []
    output_ids = [str(item.get("output_id") or "") for item in outputs]
    acknowledgement_output_ids = [
        str(item.get("output_id") or "") for item in runtime_acknowledgements
    ]
    consumed_output_ids = [str(item.get("output_id") or "") for item in consumptions]
    if (
        "" in output_ids
        or len(output_ids) != len(set(output_ids))
        or len(required_output_ids) != len(set(required_output_ids))
        or set(required_output_ids) != set(output_ids)
        or len(acknowledgement_output_ids) != len(output_ids)
        or set(acknowledgement_output_ids) != set(output_ids)
        or len(consumed_output_ids) != len(output_ids)
        or set(consumed_output_ids) != set(output_ids)
    ):
        failures.append("runtime_required_output_set_invalid")
    try:
        boundary = RuntimeLaneBoundary.from_payloads(
            outputs=outputs,
            acknowledgements=runtime_acknowledgements,
            consumptions=consumptions,
        )
        boundary.require_outputs_consumed(required_output_ids)
    except Exception:
        failures.append("runtime_lane_boundary_invalid")
    runtime_lanes = [str(item.get("lane_id") or "") for item in outputs]
    if set(runtime_lanes) != EXPECTED_RUNTIME_LANES or any(
        runtime_lanes.count(lane_id) != 1
        for lane_id in EXPECTED_RUNTIME_LANES - {"context-broker"}
    ):
        failures.append("runtime_lane_output_set_invalid")

    context_report = proposal.get("canonical_context_report")
    context_output = next(
        (
            item
            for item in outputs
            if item.get("output_id") == proposal.get("context_runtime_output_id")
        ),
        None,
    )
    context_acknowledgement = next(
        (
            item
            for item in runtime_acknowledgements
            if item.get("acknowledgement_id")
            == proposal.get("context_consumer_acknowledgement_id")
        ),
        None,
    )
    context_consumption = next(
        (
            item
            for item in consumptions
            if item.get("consumption_id") == proposal.get("context_consumption_id")
        ),
        None,
    )
    if not (
        isinstance(context_report, Mapping)
        and context_report.get("canonical") is True
        and context_report.get("canonical_report_hash") == proposal.get("context_hash")
        and _sha256_json(context_report)
        == proposal.get("canonical_context_report_sha256")
        and isinstance(context_output, Mapping)
        and context_output.get("lane_id") == "context-broker"
        and context_output.get("artifact_hash")
        == proposal.get("context_runtime_artifact_sha256")
        and isinstance(context_output.get("payload"), Mapping)
        and context_output["payload"].get("context_hash")
        == proposal.get("context_hash")
        and isinstance(context_acknowledgement, Mapping)
        and context_acknowledgement.get("output_id") == context_output.get("output_id")
        and context_acknowledgement.get("consumer_invocation_id")
        == selected_invocation_id
        and isinstance(context_acknowledgement.get("payload"), Mapping)
        and context_acknowledgement["payload"].get("context_hash")
        == proposal.get("context_hash")
        and isinstance(context_consumption, Mapping)
        and context_consumption.get("output_id") == context_output.get("output_id")
        and context_consumption.get("acknowledgement_id")
        == context_acknowledgement.get("acknowledgement_id")
        and context_consumption.get("consumer_invocation_id")
        == selected_invocation_id
    ):
        failures.append("model_context_consumption_binding_invalid")

    output_id = str(proposal.get("runtime_output_id") or "")
    coder_output = next((item for item in outputs if item.get("output_id") == output_id), None)
    if not isinstance(coder_output, Mapping) or not isinstance(
        coder_output.get("payload"), Mapping
    ):
        failures.append("model_runtime_output_missing")
        coder_output = {}
        coder_payload: Mapping[str, Any] = {}
    else:
        coder_payload = coder_output["payload"]
    exact_diff = str(coder_payload.get("approved_diff") or "")
    changed_files = coder_payload.get("changed_files")
    exact_changed_files = (
        [str(item) for item in changed_files]
        if isinstance(changed_files, list)
        else []
    )
    if (
        coder_output.get("lane_id") != "coder"
        or coder_output.get("producer_invocation_id") != selected_invocation_id
        or coder_output.get("artifact_hash")
        != proposal.get("runtime_output_artifact_sha256")
        or hashlib.sha256(exact_diff.encode("utf-8")).hexdigest()
        != artifact.get("approved_diff_sha256")
        or exact_changed_files != list(proposal.get("changed_files") or [])
        or not isinstance(output_provenance, Mapping)
        or output_provenance.get("approved_diff_sha256")
        != hashlib.sha256(exact_diff.encode("utf-8")).hexdigest()
        or output_provenance.get("changed_files") != exact_changed_files
        or output_provenance.get("blocked") is not False
        or selected_model.get("artifact_sha256")
        != _sha256_json(
            {
                "proposed_diff": exact_diff,
                "changed_files": exact_changed_files,
            }
        )
    ):
        failures.append("model_runtime_output_binding_mismatch")
    coder_consumption = next(
        (item for item in consumptions if item.get("output_id") == output_id),
        None,
    )
    if not isinstance(coder_consumption, Mapping):
        failures.append("model_runtime_output_not_consumed")

    transfer = state.get("cartographer_transfer")
    cartographer_finalization = state.get("cartographer_finalization")
    if not isinstance(transfer, Mapping) or not isinstance(
        cartographer_finalization, Mapping
    ):
        failures.append("cartographer_transfer_missing")
        transfer = {}
        cartographer_finalization = {}
    acknowledgement = cartographer_finalization.get("downstream_acknowledgement")
    authority_receipt = cartographer_finalization.get("authority_receipt")
    actual_invocation_ids = {
        str(item.get("invocation_id") or "") for item in model_invocations
    } | {
        str(item.get("invocation_id") or "")
        for item in _mapping_list(state.get("participant_records"))
        if item.get("role") == "coding-executor"
    }
    if not (
        cartographer_finalization.get("state") == "consumed"
        and isinstance(acknowledgement, Mapping)
        and acknowledgement.get("consumed") is True
        and acknowledgement.get("consumer_invocation_id")
        == transfer.get("downstream_consumer_invocation_id")
        and acknowledgement.get("consumer_invocation_id") in actual_invocation_ids
        and acknowledgement.get("schema_version")
        == "cartographer.downstream-acknowledgement/v2"
        and acknowledgement.get("consumer_output_id")
        == selected_model.get("output_id")
        and acknowledgement.get("consumer_output_sha256")
        == selected_model.get("output_sha256")
        and acknowledgement.get("consumer_artifact_sha256")
        == selected_model.get("artifact_sha256")
        and acknowledgement.get("consumer_completed_at")
        == selected_model.get("completed_at")
        and acknowledgement.get("consumer_passed") is True
        and acknowledgement.get("transfer_event_id") == transfer.get("transfer_event_id")
        and isinstance(authority_receipt, Mapping)
        and authority_receipt.get("state") == "consumed"
        and transfer.get("target") == proposal.get("target")
        and isinstance(transfer.get("provenance"), Mapping)
        and transfer["provenance"].get("source_head") == expected_source_head
    ):
        failures.append("cartographer_downstream_proof_invalid")
    artifact_cartographer = artifact.get("cartographer_identity")
    expected_cartographer = {
        "proposal_id": transfer.get("proposal_id"),
        "selection_id": transfer.get("selection_id"),
        "selection_generation": transfer.get("selection_generation"),
        "transfer_event_id": transfer.get("transfer_event_id"),
        "consumer_invocation_id": transfer.get("downstream_consumer_invocation_id"),
        "acknowledgement_id": (
            acknowledgement.get("acknowledgement_id")
            if isinstance(acknowledgement, Mapping)
            else None
        ),
        "authority_state": (
            authority_receipt.get("state")
            if isinstance(authority_receipt, Mapping)
            else None
        ),
        "source_head": (
            transfer.get("provenance", {}).get("source_head")
            if isinstance(transfer.get("provenance"), Mapping)
            else None
        ),
    }
    if artifact_cartographer != expected_cartographer:
        failures.append("immutable_artifact_cartographer_identity_mismatch")

    participant_records = _state_mapping_list(
        state,
        "participant_records",
        failures,
        "independent_participant_records_invalid",
    )
    roles = {str(item.get("role") or "") for item in participant_records}
    if roles != REQUIRED_ROLES or len(participant_records) != len(REQUIRED_ROLES):
        failures.append("independent_participant_set_invalid")
    validated_participants: list[dict[str, Any]] = []
    for record in participant_records:
        try:
            validated_participants.append(
                validate_coding_participant_record(
                    record,
                    artifact,
                    expected_role=str(record.get("role") or ""),
                )
            )
        except Exception:
            failures.append("independent_participant_records_invalid")
            validated_participants.append(record)
    participant_records = validated_participants
    participant_ids = [
        str(item.get(key) or "")
        for item in participant_records
        for key in ("invocation_id", "output_id", "consumer_acknowledgement_id")
    ]
    if (
        any(item.get("passed") is not True for item in participant_records)
        or "" in participant_ids
        or len(set(participant_ids)) != len(participant_ids)
        or any(
            item.get("artifact_sha256") != artifact.get("artifact_sha256")
            for item in participant_records
        )
    ):
        failures.append("independent_participant_proof_invalid")
    for participant in participant_records:
        role = str(participant.get("role") or "")
        producer_process = participant.get("producer_process")
        acknowledgement = participant.get("consumer_acknowledgement")
        expected_isolation = (
            "source_proxy_executor_transaction"
            if role == "coding-executor"
            else "dedicated_participant_subprocess"
        )
        if (
            participant.get("schema_version") != "coding.participant-invocation/v2"
            or not isinstance(producer_process, Mapping)
            or producer_process.get("isolation") != expected_isolation
            or not str(producer_process.get("executable_sha256") or "")
            or not str(producer_process.get("entrypoint_sha256") or "")
            or not isinstance(acknowledgement, Mapping)
            or acknowledgement.get("consumed") is not True
            or acknowledgement.get("output_id") != participant.get("output_id")
            or acknowledgement.get("output_sha256") != participant.get("output_sha256")
            or acknowledgement.get("artifact_sha256") != artifact.get("artifact_sha256")
            or (
                role != "coding-executor"
                and acknowledgement.get("consumer_process_id")
                == producer_process.get("process_id")
            )
        ):
            failures.append("independent_participant_process_proof_invalid")
    participants_by_role = {
        str(item.get("role") or ""): item for item in participant_records
    }
    for role, lane_id in PARTICIPANT_RUNTIME_LANES.items():
        participant = participants_by_role.get(role)
        lane_output = next(
            (item for item in outputs if item.get("lane_id") == lane_id),
            None,
        )
        if not _runtime_output_matches_participant(lane_output, participant, role=role):
            failures.append("participant_runtime_output_binding_invalid")
    executor = participants_by_role.get("coding-executor")
    if not isinstance(coder_consumption, Mapping) or not isinstance(executor, Mapping) or (
        coder_consumption.get("consumer_invocation_id") != executor.get("invocation_id")
    ):
        failures.append("executor_model_output_consumption_binding_invalid")

    recovery_records = _state_mapping_list(
        state,
        "recovery_lineage",
        failures,
        "controlled_recovery_records_invalid",
    )
    parsed_recovery_records: list[dict[str, Any]] = []
    for record in recovery_records:
        try:
            lineage = ControlledRecoveryLineage.from_payload(record).to_payload()
        except Exception:
            failures.append("controlled_recovery_records_invalid")
            continue
        if lineage.get("task_id") != task_id or lineage.get("run_id") != run_id:
            failures.append("controlled_recovery_records_invalid")
            continue
        parsed_recovery_records.append(lineage)
    recovery_ids = [str(item.get("recovery_id") or "") for item in parsed_recovery_records]
    if "" in recovery_ids or len(recovery_ids) != len(set(recovery_ids)):
        failures.append("controlled_recovery_records_invalid")
    failed_models = [item for item in model_invocations if item.get("passed") is False]
    fallback_used = bool(failed_models)
    recovery_id = None
    claim_ceiling = "model_authored_applied_diff_verified"
    if fallback_used:
        matched_records: list[dict[str, Any]] = []
        for lineage in parsed_recovery_records:
            replacement = lineage.get("replacement")
            participant = replacement.get("participant") if isinstance(replacement, Mapping) else None
            failure = lineage.get("failure")
            failed_participant = (
                failure.get("participant") if isinstance(failure, Mapping) else None
            )
            if (
                isinstance(participant, Mapping)
                and dict(participant) == dict(selected_model)
                and isinstance(failed_participant, Mapping)
                and any(dict(failed_participant) == dict(item) for item in failed_models)
            ):
                matched_records.append(lineage)
        if (
            len(failed_models) != 1
            or len(parsed_recovery_records) != 1
            or len(matched_records) != 1
            or matched_records[0].get("proof_eligible") is not True
        ):
            failures.append("controlled_recovery_proof_invalid")
        else:
            matched = matched_records[0]
            recovery_id = matched.get("recovery_id")
            claim_ceiling = str(matched.get("claim_ceiling_impact") or "")
    elif parsed_recovery_records:
        failures.append("controlled_recovery_proof_invalid")

    anti_cheat = participants_by_role.get("coding-anti-cheat")
    anti_result = anti_cheat.get("result") if isinstance(anti_cheat, Mapping) else None
    if not isinstance(anti_result, Mapping) or not (
        anti_result.get("model_authorship_proven") is True
        and anti_result.get("terminal_proof_eligible") is True
        and anti_result.get("claim_ceiling") == claim_ceiling
        and anti_result.get("fallback_used") is fallback_used
    ):
        failures.append("anti_cheat_model_authorship_proof_invalid")
    evidence_record = participants_by_role.get("evidence-recorder")
    evidence_result = (
        evidence_record.get("result") if isinstance(evidence_record, Mapping) else None
    )
    try:
        evidence_valid = _valid_evidence_result(
            evidence_result,
            participant_records=participant_records,
            artifact=artifact,
            claim_ceiling=claim_ceiling,
        )
    except Exception:
        evidence_valid = False
    if not evidence_valid:
        failures.append("evidence_recorder_terminal_proof_invalid")

    lane_states = state.get("lane_states")
    required_lane_states = {
        "context-broker": "completed",
        "planner": "completed",
        "coder": "completed",
        "reviewer": "completed",
        "verifier": "completed",
        "anti-cheat": "completed",
        "repair": "skipped",
    }
    if (
        state.get("lane_sequence") != list(EXPECTED_LANE_SEQUENCE)
        or not isinstance(lane_states, Mapping)
        or set(lane_states) != set(EXPECTED_LANE_SEQUENCE)
        or any(
            lane_states.get(lane) != expected
            for lane, expected in required_lane_states.items()
        )
        or lane_states.get("evidence-recorder") not in {"running", "completed"}
    ):
        failures.append("pre_finalization_lane_state_invalid")

    body = {
        "schema_version": PRODUCTION_PROOF_SCHEMA,
        "task_id": task_id,
        "run_id": run_id,
        "source_head": expected_source_head,
        "target_plugin_proposal_sha256": proposal.get("proposal_binding_sha256"),
        "model_invocation_id": selected_invocation_id or None,
        "model_output_id": selected_model.get("output_id") or None,
        "cartographer_proposal_id": transfer.get("proposal_id") or None,
        "cartographer_selection_id": transfer.get("selection_id") or None,
        "cartographer_transfer_event_id": transfer.get("transfer_event_id") or None,
        "recovery_id": recovery_id,
        "participant_invocation_ids": [
            str(item.get("invocation_id") or "") for item in participant_records
        ],
        "artifact_sha256": artifact.get("artifact_sha256"),
        "approval_id": artifact.get("approval_id"),
        "failures": sorted(set(failures)),
        "terminal_proof_eligible": not failures,
        "claim_ceiling": claim_ceiling if not failures else "production_proof_not_established",
    }
    body["proof_sha256"] = _sha256_json(body)
    return body


def _mapping_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _state_mapping_list(
    state: Mapping[str, Any],
    key: str,
    failures: list[str],
    reason_code: str,
) -> list[dict[str, Any]]:
    raw = state.get(key)
    records = _mapping_list(raw)
    if not isinstance(raw, list) or len(records) != len(raw):
        failures.append(reason_code)
    return records


def _valid_model_invocation(
    record: Mapping[str, Any],
    *,
    task_id: str,
    run_id: str,
) -> bool:
    if set(record) != MODEL_INVOCATION_FIELDS or not (
        record.get("schema_version") == "coding.recovery-participant/v1"
        and record.get("role") == "target-plugin-model"
        and record.get("lane_id") == "coder"
        and record.get("task_id") == task_id
        and record.get("run_id") == run_id
        and isinstance(record.get("passed"), bool)
    ):
        return False
    if any(
        not isinstance(record.get(key), str) or not str(record.get(key)).strip()
        for key in (
            "attempt_id",
            "invocation_id",
            "output_id",
            "provider",
            "model",
            "started_at",
            "completed_at",
        )
    ) or not (_is_sha256(record.get("input_sha256")) and _is_sha256(record.get("output_sha256"))):
        return False
    if record.get("passed") is True:
        return bool(
            isinstance(record.get("result_id"), str)
            and str(record.get("result_id")).strip()
            and _is_sha256(record.get("artifact_sha256"))
            and record.get("error_code") is None
            and record.get("error_message") is None
        )
    return bool(
        isinstance(record.get("error_code"), str)
        and str(record.get("error_code")).strip()
        and isinstance(record.get("error_message"), str)
        and str(record.get("error_message")).strip()
        and record.get("result_id") is None
        and (
            record.get("artifact_sha256") is None
            or _is_sha256(record.get("artifact_sha256"))
        )
    )


def _runtime_output_matches_participant(
    lane_output: Mapping[str, Any] | None,
    participant: Mapping[str, Any] | None,
    *,
    role: str,
) -> bool:
    if not isinstance(lane_output, Mapping) or not isinstance(participant, Mapping):
        return False
    if lane_output.get("producer_invocation_id") != participant.get("invocation_id"):
        return False
    payload = lane_output.get("payload")
    result = participant.get("result")
    if not isinstance(payload, Mapping) or not isinstance(result, Mapping):
        return False
    if role == "coding-reviewer":
        expected = {
            "passed": bool(participant.get("passed")),
            "findings": list(result.get("findings") or []),
        }
    elif role == "coding-verifier":
        expected = {
            "verdict": str(result.get("verdict") or "FAIL"),
            "checks": list(result.get("checks") or []),
        }
    elif role == "coding-anti-cheat":
        expected = {
            "passed": bool(participant.get("passed")),
            "detector_ids": list(result.get("detector_ids") or []),
            "violations": list(result.get("violations") or []),
        }
    elif role == "evidence-recorder":
        expected = {
            "receipt_id": str(result.get("receipt_id") or ""),
            "truth_status": str(result.get("truth_status") or "FAIL"),
        }
    else:
        return False
    return dict(payload) == expected


def _valid_evidence_result(
    result: Any,
    *,
    participant_records: list[Mapping[str, Any]],
    artifact: Mapping[str, Any],
    claim_ceiling: str,
) -> bool:
    if not isinstance(result, Mapping) or not (
        result.get("passed") is True
        and result.get("truth_status") == "PASS"
        and result.get("terminal_proof_eligible") is True
        and result.get("claim_ceiling") == claim_ceiling
    ):
        return False
    receipt = result.get("receipt")
    if not isinstance(receipt, Mapping):
        return False
    source_records = [
        dict(item)
        for item in participant_records
        if item.get("role") != "evidence-recorder"
    ]
    expected_receipts = []
    for record in source_records:
        participant_result = record.get("result")
        expected_receipts.append(
            {
                "role": str(record.get("role") or ""),
                "invocation_id": str(record.get("invocation_id") or ""),
                "output_id": str(record.get("output_id") or ""),
                "passed": record.get("passed") is True,
                "record_sha256": participant_record_sha256(record),
                "result": (
                    dict(participant_result)
                    if isinstance(participant_result, Mapping)
                    else {}
                ),
            }
        )
    if not (
        receipt.get("schema_version") == "coding.run-evidence/v1"
        and receipt.get("task_id") == artifact.get("task_id")
        and receipt.get("run_id") == artifact.get("run_id")
        and receipt.get("artifact_sha256") == artifact.get("artifact_sha256")
        and receipt.get("participant_invocation_ids")
        == [str(item.get("invocation_id") or "") for item in source_records]
        and receipt.get("participant_output_ids")
        == [str(item.get("output_id") or "") for item in source_records]
        and receipt.get("participant_records_sha256") == _sha256_json(source_records)
        and receipt.get("participant_records") == expected_receipts
        and receipt.get("missing") == []
        and receipt.get("failed") == []
        and receipt.get("invalid") == []
        and receipt.get("claim_ceiling") == claim_ceiling
        and receipt.get("terminal_proof_eligible") is True
    ):
        return False
    receipt_sha256 = _sha256_json(receipt)
    return bool(
        result.get("receipt_sha256") == receipt_sha256
        and result.get("receipt_id")
        == f"coding-evidence-{receipt_sha256.removeprefix('sha256:')[:24]}"
    )


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    text = value.removeprefix("sha256:")
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text)


def _sha256_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"
