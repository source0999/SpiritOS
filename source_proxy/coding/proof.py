"""Independent validation of a persisted production coding-run proof."""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path, PurePosixPath
from typing import Any

from source_proxy.coding.participants import (
    participant_record_sha256,
    validate_coding_participant_record,
)
from source_proxy.coding.recovery import (
    ControlledRecoveryLineage,
    render_evidence_guided_repair_model_task,
    target_plugin_model_input_sha256,
)
from source_proxy.coding.runtime_lane_boundary import RuntimeLaneBoundary
from source_proxy.benchmarks.campaign_3_5_fixture_authority import (
    Campaign35FixtureAuthorityError,
    load_campaign_3_5_fixture_authority,
)
from source_proxy.context.canonical_broker import build_context_broker_report
from source_proxy.diagnostics.status_codes import classify_repair_failure
from source_proxy.planning.plan import ArchitectPlan, review_task_spec_from_plan
from source_proxy.planning.reviewer import (
    review_diff_deterministically,
    validate_review_artifact_snapshots,
)
from source_proxy.target_plugins.adapter import (
    GENERIC_WORKSPACE_CONTEXT_ID,
    GENERIC_WORKSPACE_PLUGIN_ID,
    GENERIC_WORKSPACE_PROFILE,
    GENERIC_WORKSPACE_PROMPT_ID,
    target_adapter_model_call_accounting_valid,
    target_adapter_producer_identity_valid,
)
from source_proxy.target_plugins.selection import expected_target_plugin_id


PRODUCTION_PROOF_SCHEMA = "coding.production-proof/v1"
MAX_CODING_ATTEMPTS = 3
REPAIR_APPROVAL_DISPOSITION_SCHEMA = "coding.repair-approval-disposition/v1"
REPAIR_DIAGNOSTIC_SCHEMA = "coding.deterministic-repair-diagnostic/v1"
REPAIR_DEBUGGER_TRACE_SCHEMA = "coding.deterministic-debugger-trace/v1"
REPAIR_DEBUGGER_SCRIPT_SHA256 = (
    "sha256:75a086ea2f8d9a0d6155bdb99eb9024f493ed6657a40580f33fd24c329700b50"
)
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
CONTEXT_REPORT_DECISION_FIELDS = (
    "schema_version",
    "canonical",
    "sources_considered",
    "source_status",
    "selected_sources",
    "included_sources",
    "consumed_sources",
    "applicable_consumers",
    "downstream_acknowledgements",
    "required_context_blockers",
    "go_eligible",
    "verdict",
    "canonical_report_hash",
)
ARCHITECT_CONTEXT_SOURCE = "architect_repository_context"
ARCHITECT_CONTEXT_PACKET_FIELDS = {
    "plan_id",
    "target",
    "allowed_paths",
    "context_slices",
    "scoped_workspace_context_manifest",
    "scoped_workspace_context",
    "scoped_workspace_context_sha256",
    "scoped_workspace_context_char_count",
    "rendered_coder_context",
    "rendered_coder_context_sha256",
    "rendered_coder_context_char_count",
}
ARCHITECT_WORKSPACE_MANIFEST_FIELDS = {
    "path",
    "sha256",
    "size",
    "rendered_sha256",
    "rendered_chars",
    "truncated",
    "rendered_start",
    "rendered_end",
}
ARCHITECT_CONTEXT_AUTHORITY = {
    "schema_version": "source-proxy-derived-architect-context-authority/v1",
    "kind": "derived_planner_output",
    "producer": "source_proxy.planning.architect",
    "separately_bound_by": [
        "planner_runtime_output",
        "adapter_plan_sha256",
        "semantic_review_binding",
    ],
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

    plugin_identity: object = {}
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
        plugin_identity = proposal.get("target_plugin_identity")
        expected_target_source_head = (
            str(
                plugin_identity.get("target_source_head")
                or plugin_identity.get("source_head")
                or ""
            )
            if isinstance(plugin_identity, Mapping)
            else ""
        )
        if (
            not expected_target_source_head
            or proposal.get("target_source_head") != expected_target_source_head
            or expected_target_plugin_id(str(proposal.get("selected_prompt_id") or ""))
            != (
                plugin_identity.get("plugin_id")
                if isinstance(plugin_identity, Mapping)
                else None
            )
        ):
            failures.append("target_plugin_proposal_target_identity_mismatch")
        if isinstance(plugin_identity, Mapping) and plugin_identity.get(
            "plugin_id"
        ) == "generic-workspace":
            if not _generic_target_identity_matches_server_authority(
                plugin_identity
            ):
                failures.append(
                    "target_plugin_generic_server_authority_mismatch"
                )
            workspace_state = str(
                plugin_identity.get("target_workspace_state_sha256") or ""
            )
            workspace_paths = plugin_identity.get("target_workspace_state_paths")
            if (
                not workspace_state
                or not isinstance(workspace_paths, list)
                or proposal.get("target_workspace_state_sha256") != workspace_state
                or proposal.get("target_workspace_state_paths") != workspace_paths
            ):
                failures.append("target_plugin_workspace_state_binding_invalid")
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

    attempt_history, archived_model_invocation_ids = _validated_attempt_history(
        state,
        task_id=task_id,
        run_id=run_id,
        proposal=proposal,
        artifact=artifact,
        failures=failures,
    )

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
    if attempt_history and selected_model.get("attempt_id") != state.get("attempt_id"):
        failures.append("repair_current_model_attempt_binding_invalid")
    if [
        str(item.get("invocation_id") or "")
        for item in model_invocations
        if item.get("passed") is True
    ] != [selected_invocation_id]:
        failures.append("model_invocation_success_set_invalid")
    context_report_for_model = proposal.get("canonical_context_report")
    repair_context_for_model = proposal.get("repair_context")
    original_task_for_model = str(proposal.get("original_task") or "")
    if isinstance(repair_context_for_model, Mapping):
        model_task, _ = render_evidence_guided_repair_model_task(
            original_task_for_model,
            repair_context_for_model,
        )
    else:
        model_task = original_task_for_model
    if (
        not model_task
        or not isinstance(plugin_identity, Mapping)
        or not isinstance(context_report_for_model, Mapping)
    ):
        failures.append("model_input_binding_material_missing")
    else:
        expected_model_input_sha256 = target_plugin_model_input_sha256(
            task=model_task,
            target_plugin_identity=plugin_identity,
            canonical_context=context_report_for_model,
        )
        if any(
            item.get("input_sha256") != expected_model_input_sha256
            for item in model_invocations
        ):
            failures.append("model_input_binding_mismatch")
    adapter = proposal.get("target_adapter_provenance")
    if not isinstance(adapter, Mapping) or not (
        adapter.get("terminal_proof_eligible") is True
        and adapter.get("transport_kind") == "canonical_litellm_router"
        and adapter.get("provider_call_made") is True
        and adapter.get("provider_call_authorized") is True
        and adapter.get("generation_source") == "model"
        and _is_sha256(adapter.get("rendered_prompt_sha256"))
        and _is_sha256(adapter.get("raw_response_sha256"))
        and target_adapter_model_call_accounting_valid(adapter)
        and target_adapter_producer_identity_valid(adapter)
        and isinstance(plugin_identity, Mapping)
        and adapter.get("plugin_id") == plugin_identity.get("plugin_id")
        and adapter.get("selected_prompt_id")
        == proposal.get("selected_prompt_id")
    ):
        failures.append("canonical_model_provenance_invalid")
        adapter = {}
    if not (
        proposal.get("producer_model_alias")
        == adapter.get("selected_model_alias")
        and proposal.get("producer_model_provider") == adapter.get("provider")
        and proposal.get("producer_model_name") == adapter.get("model")
        and proposal.get("producer_adapter_call_index")
        == adapter.get("producer_call_index")
        and selected_model.get("provider")
        == proposal.get("producer_model_provider")
        and selected_model.get("model") == proposal.get("producer_model_name")
    ):
        failures.append("model_adapter_producer_identity_binding_invalid")
    if not _target_adapter_model_call_authority_matches(
        adapter,
        run_id=run_id,
        participant=selected_model,
    ):
        failures.append("model_call_authority_binding_invalid")
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
    if (
        set(runtime_lanes) != EXPECTED_RUNTIME_LANES
        or runtime_lanes.count("planner") < 1
        or any(
            runtime_lanes.count(lane_id) != 1
            for lane_id in EXPECTED_RUNTIME_LANES
            - {"context-broker", "planner"}
        )
    ):
        failures.append("runtime_lane_output_set_invalid")
    planner_outputs = [
        item for item in outputs if item.get("lane_id") == "planner"
    ]
    for prior, successor in zip(planner_outputs, planner_outputs[1:], strict=False):
        prior_consumptions = [
            item
            for item in consumptions
            if item.get("output_id") == prior.get("output_id")
        ]
        if (
            len(prior_consumptions) != 1
            or prior_consumptions[0].get("consumer_invocation_id")
            != successor.get("producer_invocation_id")
        ):
            failures.append("runtime_planner_refresh_chain_invalid")
            break

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
        and _canonical_context_report_truth_valid(context_report)
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
    semantic_review_binding = proposal.get("semantic_review_binding")
    planner_runtime_output = next(
        (item for item in reversed(outputs) if item.get("lane_id") == "planner"),
        None,
    )
    planner_runtime_payload = (
        planner_runtime_output.get("payload")
        if isinstance(planner_runtime_output, Mapping)
        and isinstance(planner_runtime_output.get("payload"), Mapping)
        else None
    )
    planner_acknowledgement = next(
        (
            item
            for item in runtime_acknowledgements
            if item.get("acknowledgement_id")
            == proposal.get("planner_consumer_acknowledgement_id")
        ),
        None,
    )
    planner_consumption = next(
        (
            item
            for item in consumptions
            if item.get("consumption_id")
            == proposal.get("planner_consumption_id")
        ),
        None,
    )
    if not (
        isinstance(planner_runtime_output, Mapping)
        and planner_runtime_output.get("output_id")
        == proposal.get("planner_runtime_output_id")
        and planner_runtime_output.get("artifact_hash")
        == proposal.get("planner_runtime_artifact_sha256")
        and isinstance(planner_acknowledgement, Mapping)
        and planner_acknowledgement.get("output_id")
        == planner_runtime_output.get("output_id")
        and planner_acknowledgement.get("consumer_invocation_id")
        == selected_invocation_id
        and isinstance(planner_consumption, Mapping)
        and planner_consumption.get("output_id")
        == planner_runtime_output.get("output_id")
        and planner_consumption.get("acknowledgement_id")
        == planner_acknowledgement.get("acknowledgement_id")
        and planner_consumption.get("consumer_invocation_id")
        == selected_invocation_id
    ):
        failures.append("model_planner_consumption_binding_invalid")
    if not (
        isinstance(semantic_review_binding, Mapping)
        and proposal.get("semantic_review_binding_sha256")
        == semantic_review_binding.get("semantic_review_binding_sha256")
        and isinstance(planner_runtime_payload, Mapping)
        and isinstance(semantic_review_binding.get("server_plan"), Mapping)
        and planner_runtime_payload.get("task_spec")
        == semantic_review_binding.get("server_plan")
        and planner_runtime_payload.get("plan_id")
        == semantic_review_binding.get("server_plan", {}).get("plan_id")
        and _valid_semantic_review_binding(
            semantic_review_binding,
            task_id=task_id,
            run_id=run_id,
            attempt_id=str(state.get("attempt_id") or ""),
            proposed_diff=exact_diff,
            changed_files=exact_changed_files,
            adapter_architect_plan_required=(
                isinstance(proposal.get("target_plugin_identity"), Mapping)
                and proposal["target_plugin_identity"].get("plugin_id")
                == GENERIC_WORKSPACE_PLUGIN_ID
            ),
            target_plugin_identity=(
                proposal.get("target_plugin_identity")
                if isinstance(proposal.get("target_plugin_identity"), Mapping)
                else None
            ),
            repair_request=(
                state.get("repair_request")
                if isinstance(state.get("repair_request"), Mapping)
                else None
            ),
            canonical_context=(
                proposal.get("canonical_context_report")
                if isinstance(
                    proposal.get("canonical_context_report"),
                    Mapping,
                )
                else None
            ),
            adapter_provenance=(
                proposal.get("target_adapter_provenance")
                if isinstance(
                    proposal.get("target_adapter_provenance"),
                    Mapping,
                )
                else None
            ),
        )
    ):
        failures.append("semantic_review_binding_invalid")
    if artifact.get("semantic_review_identity") != semantic_review_binding:
        failures.append("immutable_artifact_semantic_review_binding_mismatch")
    coder_consumption = next(
        (item for item in consumptions if item.get("output_id") == output_id),
        None,
    )
    if not isinstance(coder_consumption, Mapping):
        failures.append("model_runtime_output_not_consumed")

    artifact_cartographer = artifact.get("cartographer_identity")
    direct_generic_without_cartographer = (
        _direct_generic_server_authority_without_cartographer(
            state,
            plugin_identity=plugin_identity,
            artifact=artifact,
        )
    )
    transfer = state.get("cartographer_transfer")
    cartographer_finalization = state.get("cartographer_finalization")
    if direct_generic_without_cartographer:
        transfer = {}
        cartographer_finalization = {}
    elif not isinstance(transfer, Mapping) or not isinstance(
        cartographer_finalization, Mapping
    ):
        failures.append("cartographer_transfer_missing")
        transfer = {}
        cartographer_finalization = {}
    acknowledgement = cartographer_finalization.get("downstream_acknowledgement")
    authority_receipt = cartographer_finalization.get("authority_receipt")
    cartographer_model: Mapping[str, Any] = selected_model
    if attempt_history and isinstance(acknowledgement, Mapping):
        archived_cartographer_model = next(
            (
                model
                for seal in attempt_history
                for attempt_state in [seal.get("attempt_state")]
                if isinstance(attempt_state, Mapping)
                for model in _mapping_list(attempt_state.get("model_invocations"))
                if model.get("invocation_id")
                == acknowledgement.get("consumer_invocation_id")
            ),
            None,
        )
        if isinstance(archived_cartographer_model, Mapping):
            cartographer_model = archived_cartographer_model
    actual_invocation_ids = {
        str(item.get("invocation_id") or "") for item in model_invocations
    } | {
        str(item.get("invocation_id") or "")
        for item in _mapping_list(state.get("participant_records"))
        if item.get("role") == "coding-executor"
    } | archived_model_invocation_ids
    if not direct_generic_without_cartographer and not (
        cartographer_finalization.get("state") == "consumed"
        and isinstance(acknowledgement, Mapping)
        and acknowledgement.get("consumed") is True
        and acknowledgement.get("consumer_invocation_id")
        == transfer.get("downstream_consumer_invocation_id")
        and acknowledgement.get("consumer_invocation_id") in actual_invocation_ids
        and acknowledgement.get("schema_version")
        == "cartographer.downstream-acknowledgement/v2"
        and acknowledgement.get("consumer_output_id")
        == cartographer_model.get("output_id")
        and acknowledgement.get("consumer_output_sha256")
        == cartographer_model.get("output_sha256")
        and acknowledgement.get("consumer_artifact_sha256")
        == cartographer_model.get("artifact_sha256")
        and acknowledgement.get("consumer_completed_at")
        == cartographer_model.get("completed_at")
        and acknowledgement.get("consumer_passed") is True
        and acknowledgement.get("transfer_event_id") == transfer.get("transfer_event_id")
        and isinstance(authority_receipt, Mapping)
        and authority_receipt.get("state") == "consumed"
        and transfer.get("target") == proposal.get("target")
        and isinstance(transfer.get("provenance"), Mapping)
        and transfer["provenance"].get("source_head") == expected_source_head
    ):
        failures.append("cartographer_downstream_proof_invalid")
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
    if (
        not direct_generic_without_cartographer
        and artifact_cartographer != expected_cartographer
    ):
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
    if not _reviewer_consumed_semantic_review(
        participants_by_role.get("coding-reviewer"),
        semantic_review_binding,
    ):
        failures.append("reviewer_semantic_review_consumption_invalid")
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
        "repair": "completed" if attempt_history else "skipped",
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
        "attempt_id": state.get("attempt_id"),
        "attempt_count": len(attempt_history) + 1,
        "failed_attempt_seal_sha256s": [
            item.get("seal_sha256") for item in attempt_history
        ],
        "failed_attempt_repair_diagnostic_sha256s": [
            item.get("repair_diagnostic", {}).get("diagnostic_sha256")
            if isinstance(item.get("repair_diagnostic"), Mapping)
            else None
            for item in attempt_history
        ],
        "failed_attempt_approval_disposition_sha256s": [
            item.get("disposition_sha256")
            for item in _mapping_list(state.get("attempt_dispositions"))
        ],
        "failures": sorted(set(failures)),
        "terminal_proof_eligible": not failures,
        "claim_ceiling": claim_ceiling if not failures else "production_proof_not_established",
    }
    body["proof_sha256"] = _sha256_json(body)
    return body


def _validated_attempt_history(
    state: Mapping[str, Any],
    *,
    task_id: str,
    run_id: str,
    proposal: Mapping[str, Any],
    artifact: Mapping[str, Any],
    failures: list[str],
) -> tuple[list[dict[str, Any]], set[str]]:
    raw_history = state.get("attempt_history", [])
    history = _mapping_list(raw_history)
    raw_dispositions = state.get("attempt_dispositions", [])
    dispositions = _mapping_list(raw_dispositions)
    if not isinstance(raw_history, list) or len(history) != len(raw_history):
        failures.append("repair_attempt_history_invalid")
        return history, set()
    repair_request = state.get("repair_request")
    if not history:
        if repair_request is not None:
            failures.append("repair_context_binding_invalid")
        if raw_dispositions not in (None, []):
            failures.append("repair_approval_disposition_invalid")
        return history, set()
    if len(history) >= MAX_CODING_ATTEMPTS:
        failures.append("repair_attempt_history_invalid")
    disposition_invalid = False
    if (
        not isinstance(raw_dispositions, list)
        or len(dispositions) != len(raw_dispositions)
        or len(dispositions) != len(history)
    ):
        failures.append("repair_approval_disposition_invalid")
        disposition_invalid = True

    invalid = False
    approval_reused = False
    strategy_reused = False
    archived_model_invocation_ids: set[str] = set()
    approval_ids: list[str] = []
    repair_strategy_signatures: list[str] = []
    previous_attempt_id: str | None = None
    previous_next_attempt_id: str | None = None
    inherited_cartographer_transfer: Mapping[str, Any] | None = None
    inherited_cartographer_finalization: Mapping[str, Any] | None = None
    inherited_direct_generic_without_cartographer: bool | None = None
    dispositions_by_seal: dict[str, dict[str, Any]] = {}
    for disposition in dispositions:
        body = dict(disposition)
        recorded = str(body.pop("disposition_sha256", ""))
        seal_sha256 = str(disposition.get("attempt_seal_sha256") or "")
        if (
            disposition.get("schema_version")
            != REPAIR_APPROVAL_DISPOSITION_SCHEMA
            or disposition.get("task_id") != task_id
            or disposition.get("run_id") != run_id
            or disposition.get("authority_state") != "invalidated"
            or not seal_sha256
            or seal_sha256 in dispositions_by_seal
            or not recorded
            or _sha256_json(body) != recorded
        ):
            invalid = True
            disposition_invalid = True
            continue
        dispositions_by_seal[seal_sha256] = disposition
    for index, seal in enumerate(history, start=1):
        body = dict(seal)
        recorded_seal_sha256 = str(body.pop("seal_sha256", ""))
        failure = seal.get("failure")
        repair_diagnostic = seal.get("repair_diagnostic")
        manifest = seal.get("current_state_manifest")
        binding = seal.get("approval_binding")
        attempt_state = seal.get("attempt_state")
        archived_artifact = (
            attempt_state.get("immutable_artifact")
            if isinstance(attempt_state, Mapping)
            else None
        )
        archived_proposal = (
            attempt_state.get("target_plugin_proposal")
            if isinstance(attempt_state, Mapping)
            else None
        )
        archived_identity = (
            archived_proposal.get("target_plugin_identity")
            if isinstance(archived_proposal, Mapping)
            else None
        )
        archived_cartographer_transfer = (
            attempt_state.get("cartographer_transfer")
            if isinstance(attempt_state, Mapping)
            else None
        )
        archived_cartographer_finalization = (
            attempt_state.get("cartographer_finalization")
            if isinstance(attempt_state, Mapping)
            else None
        )
        archived_direct_generic_without_cartographer = (
            _direct_generic_server_authority_without_cartographer(
                attempt_state,
                plugin_identity=archived_identity,
                artifact=archived_artifact,
            )
            if isinstance(attempt_state, Mapping)
            else False
        )
        archived_cartographer_bound = isinstance(
            archived_cartographer_transfer, Mapping
        ) and isinstance(archived_cartographer_finalization, Mapping)
        attempt_id = str(seal.get("attempt_id") or "")
        parent_attempt_id = seal.get("parent_attempt_id")
        if (
            seal.get("schema_version") != "coding.repair-attempt-seal/v1"
            or seal.get("task_id") != task_id
            or seal.get("run_id") != run_id
            or seal.get("attempt_number") != index
            or not attempt_id
            or (index > 1 and parent_attempt_id != previous_attempt_id)
            or (index > 1 and previous_next_attempt_id != attempt_id)
            or (index == 1 and parent_attempt_id not in {None, ""})
            or not recorded_seal_sha256
            or _sha256_json(body) != recorded_seal_sha256
            or not isinstance(failure, Mapping)
            or failure.get("failure_class")
            not in {"reviewer_rejection", "verifier_rejection"}
            or failure.get("source_lane") not in {"reviewer", "verifier"}
            or not isinstance(failure.get("exact_feedback"), Mapping)
            or _sha256_json(failure.get("exact_feedback"))
            != failure.get("feedback_sha256")
            or not isinstance(manifest, Mapping)
            or _sha256_json(manifest)
            != seal.get("current_state_manifest_sha256")
            or not _valid_repair_diagnostic(
                repair_diagnostic,
                task_id=task_id,
                run_id=run_id,
                attempt_id=attempt_id,
                failure=failure,
                current_state_manifest=manifest,
                current_state_manifest_sha256=str(
                    seal.get("current_state_manifest_sha256") or ""
                ),
                attempt_state=attempt_state,
            )
            or not isinstance(binding, Mapping)
            or not isinstance(attempt_state, Mapping)
            or not isinstance(archived_artifact, Mapping)
            or not isinstance(archived_proposal, Mapping)
            or not (
                archived_direct_generic_without_cartographer
                or archived_cartographer_bound
            )
        ):
            invalid = True
            previous_attempt_id = attempt_id or previous_attempt_id
            previous_next_attempt_id = str(seal.get("next_attempt_id") or "") or None
            continue
        disposition = dispositions_by_seal.get(recorded_seal_sha256)
        if (
            not isinstance(disposition, Mapping)
            or disposition.get("attempt_id") != attempt_id
            or disposition.get("approval_id") != binding.get("approval_id")
            or disposition.get("generation") != binding.get("generation")
        ):
            invalid = True
            disposition_invalid = True
        if index == 1:
            inherited_direct_generic_without_cartographer = (
                archived_direct_generic_without_cartographer
            )
            inherited_cartographer_transfer = archived_cartographer_transfer
            inherited_cartographer_finalization = archived_cartographer_finalization
        elif (
            archived_direct_generic_without_cartographer
            != inherited_direct_generic_without_cartographer
            or (
                not archived_direct_generic_without_cartographer
                and (
                    archived_cartographer_transfer
                    != inherited_cartographer_transfer
                    or archived_cartographer_finalization
                    != inherited_cartographer_finalization
                )
            )
        ):
            invalid = True
        if (
            manifest.get("schema_version")
            != "coding.current-applied-state-manifest/v1"
            or manifest.get("artifact_sha256")
            != archived_artifact.get("artifact_sha256")
            or manifest.get("approval_id") != archived_artifact.get("approval_id")
            or manifest.get("approved_diff_sha256")
            != archived_artifact.get("approved_diff_sha256")
            or binding.get("approval_id") != archived_artifact.get("approval_id")
            or binding.get("generation") != archived_artifact.get("generation")
            or binding.get("approved_diff_sha256")
            != archived_artifact.get("approved_diff_sha256")
            or binding.get("artifact_sha256")
            != archived_artifact.get("artifact_sha256")
            or not str(binding.get("proposal_binding_sha256") or "")
            or binding.get("proposal_binding_sha256")
            != archived_proposal.get("proposal_binding_sha256")
            or binding.get("approved_diff_sha256")
            != archived_proposal.get("approved_diff_sha256")
            or archived_proposal.get("attempt_id") != attempt_id
            or not str(archived_proposal.get("original_task") or "").strip()
        ):
            invalid = True
        if manifest.get("live_state_captured") is True:
            archived_changed = {
                str(item.get("path") or ""): item
                for item in archived_artifact.get("changed_files", [])
                if isinstance(item, Mapping)
            }
            live_changed = manifest.get("changed_files")
            expected_target_head = (
                str(
                    archived_identity.get("target_source_head")
                    or archived_identity.get("source_head")
                    or ""
                )
                if isinstance(archived_identity, Mapping)
                else ""
            )
            if (
                manifest.get("generation") != archived_artifact.get("generation")
                or manifest.get("result_sha256")
                != archived_artifact.get("result_sha256")
                or manifest.get("workspace_root")
                != archived_artifact.get("workspace_root")
                or manifest.get("stable_target_plugin_identity")
                != _stable_target_plugin_identity(archived_identity)
                or manifest.get("target_source_head") != expected_target_head
                or not isinstance(live_changed, list)
                or any(
                    not isinstance(item, Mapping)
                    or str(item.get("path") or "") not in archived_changed
                    or item.get("expected_sha256_after")
                    != archived_changed[str(item.get("path") or "")].get(
                        "sha256_after"
                    )
                    or not isinstance(item.get("current_exists"), bool)
                    or (
                        item.get("current_exists") is True
                        and not _is_sha256(item.get("current_sha256"))
                    )
                    or (
                        item.get("current_exists") is False
                        and item.get("current_sha256") is not None
                    )
                    for item in live_changed
                )
                or not _valid_archived_failure_evidence(
                    failure,
                    attempt_state=attempt_state,
                )
            ):
                invalid = True
            if isinstance(archived_identity, Mapping) and archived_identity.get(
                "plugin_id"
            ) == "generic-workspace" and (
                not str(manifest.get("target_workspace_state_sha256") or "")
                or not isinstance(manifest.get("target_workspace_state_paths"), list)
            ):
                invalid = True
        approval_id = str(binding.get("approval_id") or "")
        if not approval_id or approval_id in approval_ids:
            approval_reused = True
        approval_ids.append(approval_id)
        strategy_signature = str(seal.get("repair_strategy_signature") or "")
        if index == 1 and strategy_signature:
            invalid = True
            repair_strategy_signatures.append(strategy_signature)
        elif index > 1:
            if not strategy_signature or strategy_signature in repair_strategy_signatures:
                strategy_reused = True
            repair_strategy_signatures.append(strategy_signature)
        for model in _mapping_list(attempt_state.get("model_invocations")):
            invocation_id = str(model.get("invocation_id") or "")
            if invocation_id:
                archived_model_invocation_ids.add(invocation_id)
        previous_attempt_id = attempt_id
        previous_next_attempt_id = str(seal.get("next_attempt_id") or "") or None

    for index, seal in enumerate(history):
        manifest = seal.get("current_state_manifest")
        if not isinstance(manifest, Mapping) or manifest.get("live_state_captured") is not True:
            continue
        if index + 1 < len(history):
            next_state = history[index + 1].get("attempt_state")
            next_proposal = (
                next_state.get("target_plugin_proposal")
                if isinstance(next_state, Mapping)
                else None
            )
        else:
            next_proposal = proposal
        next_identity = (
            next_proposal.get("target_plugin_identity")
            if isinstance(next_proposal, Mapping)
            else None
        )
        if (
            not isinstance(next_identity, Mapping)
            or _stable_target_plugin_identity(next_identity)
            != manifest.get("stable_target_plugin_identity")
            or str(
                next_identity.get("target_source_head")
                or next_identity.get("source_head")
                or ""
            )
            != manifest.get("target_source_head")
        ):
            invalid = True
            continue
        if next_identity.get("plugin_id") == "generic-workspace" and (
            next_identity.get("target_workspace_state_sha256")
            != manifest.get("target_workspace_state_sha256")
            or list(next_identity.get("target_workspace_state_paths") or [])
            != list(manifest.get("target_workspace_state_paths") or [])
        ):
            invalid = True

    current_attempt_id = str(state.get("attempt_id") or "")
    current_attempt_number = state.get("attempt_number")
    if (
        current_attempt_number != len(history) + 1
        or current_attempt_number > MAX_CODING_ATTEMPTS
        or state.get("max_attempts", MAX_CODING_ATTEMPTS) != MAX_CODING_ATTEMPTS
        or state.get("parent_attempt_id") != previous_attempt_id
        or history[-1].get("next_attempt_id") != current_attempt_id
        or not isinstance(repair_request, Mapping)
    ):
        invalid = True
    else:
        repair_body = dict(repair_request)
        recorded_repair_sha256 = str(repair_body.pop("repair_input_sha256", ""))
        latest_failure = history[-1].get("failure")
        latest_attempt_state = history[-1].get("attempt_state")
        latest_proposal = (
            latest_attempt_state.get("target_plugin_proposal")
            if isinstance(latest_attempt_state, Mapping)
            else None
        )
        latest_disposition = dispositions_by_seal.get(
            str(history[-1].get("seal_sha256") or "")
        )
        if (
            repair_request.get("schema_version")
            != "coding.evidence-guided-repair-request/v1"
            or repair_request.get("task_id") != task_id
            or repair_request.get("run_id") != run_id
            or repair_request.get("attempt_id") != current_attempt_id
            or repair_request.get("parent_attempt_id") != previous_attempt_id
            or repair_request.get("attempt_number") != current_attempt_number
            or repair_request.get("max_attempts") != MAX_CODING_ATTEMPTS
            or repair_request.get("parent_attempt_seal_sha256")
            != history[-1].get("seal_sha256")
            or not recorded_repair_sha256
            or _sha256_json(repair_body) != recorded_repair_sha256
            or not isinstance(latest_failure, Mapping)
            or repair_request.get("failure_class")
            != latest_failure.get("failure_class")
            or repair_request.get("source_lane") != latest_failure.get("source_lane")
            or repair_request.get("exact_feedback")
            != latest_failure.get("exact_feedback")
            or repair_request.get("feedback_sha256")
            != latest_failure.get("feedback_sha256")
            or repair_request.get("current_state_manifest")
            != history[-1].get("current_state_manifest")
            or repair_request.get("current_state_manifest_sha256")
            != history[-1].get("current_state_manifest_sha256")
            or repair_request.get("repair_diagnostic")
            != history[-1].get("repair_diagnostic")
            or repair_request.get("repair_diagnostic_sha256")
            != (
                history[-1].get("repair_diagnostic", {}).get(
                    "diagnostic_sha256"
                )
                if isinstance(history[-1].get("repair_diagnostic"), Mapping)
                else None
            )
            or repair_request.get("prior_approval_disposition")
            != latest_disposition
            or repair_request.get("prior_approval_disposition_sha256")
            != (
                latest_disposition.get("disposition_sha256")
                if isinstance(latest_disposition, Mapping)
                else None
            )
            or repair_request.get("original_task")
            != (
                latest_proposal.get("original_task")
                if isinstance(latest_proposal, Mapping)
                else None
            )
            or proposal.get("attempt_id") != current_attempt_id
            or proposal.get("parent_attempt_id") != previous_attempt_id
            or proposal.get("attempt_number") != current_attempt_number
            or proposal.get("repair_context") != repair_request
            or proposal.get("repair_input_sha256") != recorded_repair_sha256
            or proposal.get("original_task") != repair_request.get("original_task")
        ):
            invalid = True

    current_approval_id = str(artifact.get("approval_id") or "")
    if not current_approval_id or current_approval_id in approval_ids:
        approval_reused = True
    current_strategy_signature = str(proposal.get("repair_strategy_signature") or "")
    if (
        not current_strategy_signature
        or current_strategy_signature in repair_strategy_signatures
    ):
        strategy_reused = True
    if artifact.get("approved_diff_sha256") != proposal.get("approved_diff_sha256"):
        invalid = True
    current_identity = proposal.get("target_plugin_identity")
    current_direct_generic_without_cartographer = (
        _direct_generic_server_authority_without_cartographer(
            state,
            plugin_identity=current_identity,
            artifact=artifact,
        )
    )
    if inherited_direct_generic_without_cartographer is True:
        if not current_direct_generic_without_cartographer:
            invalid = True
    elif (
        current_direct_generic_without_cartographer
        or state.get("cartographer_transfer") != inherited_cartographer_transfer
        or state.get("cartographer_finalization")
        != inherited_cartographer_finalization
    ):
        invalid = True

    if invalid:
        failures.append("repair_attempt_history_invalid")
    if disposition_invalid and "repair_approval_disposition_invalid" not in failures:
        failures.append("repair_approval_disposition_invalid")
    if approval_reused:
        failures.append("repair_approval_reuse_detected")
    if strategy_reused:
        failures.append("repair_attempt_strategy_reused")
    if invalid or approval_reused or strategy_reused:
        failures.append("repair_context_binding_invalid")
    return history, archived_model_invocation_ids


def _mapping_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _generic_target_identity_matches_server_authority(
    identity: Mapping[str, Any],
) -> bool:
    """Re-resolve immutable generic scope instead of trusting proposal claims."""

    try:
        authority = load_campaign_3_5_fixture_authority()
    except Campaign35FixtureAuthorityError:
        return False
    scope = authority.adapter_scope()
    manifest_namespace = authority.manifest_sha256[:24]
    readable = list(authority.readable_paths or authority.allowed_paths)
    writable = list(authority.writable_paths or authority.allowed_paths)
    return bool(
        identity.get("plugin_id") == GENERIC_WORKSPACE_PLUGIN_ID
        and identity.get("repository_id") == "campaign-3.5-fixture"
        and identity.get("worktree_id") == manifest_namespace
        and identity.get("state_namespace") == manifest_namespace
        and Path(str(identity.get("workspace_root") or "")).resolve()
        == authority.workspace_root.resolve()
        and identity.get("fixture_root") == "."
        and identity.get("selected_prompt_id") == GENERIC_WORKSPACE_PROMPT_ID
        and identity.get("selected_context_id") == GENERIC_WORKSPACE_CONTEXT_ID
        and identity.get("execution_profile") == GENERIC_WORKSPACE_PROFILE
        and list(identity.get("allowed_actions") or []) == writable
        and list(identity.get("readable_actions") or []) == readable
        and identity.get("result_identity")
        == f"generic-workspace:{authority.manifest_sha256[:12]}"
        and (
            authority.baseline_commit is None
            or identity.get("target_source_head") == scope.get("baseline_commit")
        )
    )


def _direct_generic_server_authority_without_cartographer(
    state: Mapping[str, Any],
    *,
    plugin_identity: object,
    artifact: object,
) -> bool:
    """Recognize the exact direct-generic route where Cartographer is inapplicable."""

    if (
        not isinstance(plugin_identity, Mapping)
        or plugin_identity.get("plugin_id") != GENERIC_WORKSPACE_PLUGIN_ID
        or not _generic_target_identity_matches_server_authority(plugin_identity)
        or not isinstance(artifact, Mapping)
    ):
        return False
    cartographer_keys = (
        "cartographer_selection_consumption",
        "cartographer_transfer",
        "cartographer_finalization",
    )
    if any(key not in state or state[key] is not None for key in cartographer_keys):
        return False
    causal_events = state.get("causal_events")
    if not isinstance(causal_events, list) or any(
        not isinstance(event, Mapping)
        or not isinstance(event.get("event_type"), str)
        or not event.get("event_type", "").strip()
        or event.get("event_type", "").strip().lower().startswith("cartographer_")
        for event in causal_events
    ):
        return False
    cartographer_identity = artifact.get("cartographer_identity")
    return isinstance(cartographer_identity, dict) and not cartographer_identity


def _stable_target_plugin_identity(identity: object) -> dict[str, Any]:
    if not isinstance(identity, Mapping):
        return {}
    mutable = {
        "target_workspace_state_sha256",
        "target_workspace_state_paths",
        "approval_id",
        "approval_generation",
        "evidence_pointer",
        "failure_reason",
        "acknowledgement_status",
    }
    return {
        str(key): json.loads(json.dumps(value, sort_keys=True, default=str))
        for key, value in identity.items()
        if str(key) not in mutable
    }


def _structured_repair_diagnostic_input(
    *,
    failure_class: str,
    source_lane: str,
    exact_feedback: Mapping[str, Any],
) -> dict[str, Any]:
    """Recompute the structured diagnostic selection sealed by the orchestrator."""

    def selected(
        code: str,
        stage: str,
        source: str,
        evidence: Mapping[str, Any],
    ) -> dict[str, Any]:
        normalized_code = str(code or failure_class).strip() or failure_class
        normalized_stage = str(stage or source_lane).strip().lower() or source_lane
        return {
            "diagnostic_code": normalized_code,
            "stage": normalized_stage,
            "reason": normalized_code,
            "input_source": source,
            "structured_evidence": json.loads(
                json.dumps(dict(evidence), sort_keys=True, default=str)
            ),
        }

    def structured_code(record: Mapping[str, Any]) -> str:
        for key in (
            "diagnostic_code",
            "reason_code",
            "error_code",
            "failure_kind",
            "failure_class",
        ):
            value = record.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def structured_stage(record: Mapping[str, Any], default: str) -> str:
        for key in ("diagnostic_stage", "failure_stage", "stage"):
            value = record.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip().lower()
        category = str(
            record.get("failure_category")
            or record.get("category")
            or record.get("failure_kind")
            or record.get("failure_class")
            or ""
        ).strip().lower()
        if any(
            token in category
            for token in ("environment", "dependency", "service", "tool")
        ):
            return "environment"
        if "runtime" in category:
            return "runtime"
        if any(token in category for token in ("test", "assertion", "fixture")):
            return "tests"
        return default

    direct_code = structured_code(exact_feedback)
    if direct_code:
        return selected(
            direct_code,
            structured_stage(exact_feedback, source_lane),
            "exact_feedback",
            exact_feedback,
        )

    post_apply = exact_feedback.get("post_apply_verification")
    if isinstance(post_apply, Mapping):
        post_code = structured_code(post_apply)
        generic_post_codes = {
            "post_apply_verification_failed",
            "verification_failed",
            "server_verification_not_verified",
        }
        if post_code and post_code.lower() not in generic_post_codes:
            return selected(
                post_code,
                structured_stage(post_apply, source_lane),
                "post_apply_verification",
                post_apply,
            )
        checks = post_apply.get("checks")
        if isinstance(checks, list):
            for index, check in enumerate(checks):
                if not isinstance(check, Mapping) or str(
                    check.get("status") or ""
                ).strip().lower() != "failed":
                    continue
                check_code = structured_code(check)
                check_stage = structured_stage(check, "tests")
                if not check_code:
                    exit_code = check.get("exit_code")
                    check_id = str(
                        check.get("id") or check.get("command_text") or "unknown"
                    ).strip()
                    if isinstance(exit_code, int) and not isinstance(exit_code, bool) and exit_code == 124:
                        check_code = f"test_timeout:{check_id}"
                        check_stage = "environment"
                    else:
                        check_code = f"visible_tests_failed:{check_id}"
                return selected(
                    check_code,
                    check_stage,
                    f"post_apply_verification.checks[{index}]",
                    check,
                )
        browser = post_apply.get("browser_evidence")
        if isinstance(browser, Mapping) and any(
            str(browser.get(key) or "").strip().lower() == "failed"
            for key in (
                "status",
                "browser_verification_status",
                "storefront_runtime_status",
            )
        ):
            return selected(
                structured_code(browser) or "browser_runtime_failed",
                structured_stage(browser, "runtime"),
                "post_apply_verification.browser_evidence",
                browser,
            )
        snapshot = post_apply.get("snapshot_verification")
        if isinstance(snapshot, Mapping):
            issue_key = next(
                (
                    str(key)
                    for key, value in snapshot.items()
                    if str(key).endswith("_issue")
                    and isinstance(value, str)
                    and value.strip()
                ),
                "",
            )
            if issue_key:
                return selected(
                    str(snapshot[issue_key]),
                    "tests",
                    f"post_apply_verification.snapshot_verification.{issue_key}",
                    {issue_key: snapshot[issue_key]},
                )
        if post_code:
            return selected(
                post_code,
                structured_stage(post_apply, source_lane),
                "post_apply_verification",
                post_apply,
            )

    participant_result = exact_feedback.get("participant_result")
    if isinstance(participant_result, Mapping):
        result_code = structured_code(participant_result)
        if result_code:
            return selected(
                result_code,
                structured_stage(participant_result, source_lane),
                "participant_result",
                participant_result,
            )
        findings = participant_result.get("findings")
        if isinstance(findings, list):
            finding = next(
                (
                    item.strip()
                    for item in findings
                    if isinstance(item, str)
                    and item.strip()
                    and not any(character.isspace() for character in item.strip())
                ),
                "",
            )
            if finding:
                return selected(
                    finding,
                    source_lane,
                    "participant_result.findings[0]",
                    {"finding": finding},
                )

    return selected(
        failure_class,
        source_lane,
        "orchestrator_failure_binding",
        {"failure_class": failure_class, "source_lane": source_lane},
    )


def _repair_classification_details(
    classification_input: Mapping[str, Any],
    *,
    feedback_sha256: str,
    current_state_manifest_sha256: str,
) -> dict[str, Any]:
    return {
        "feedback_sha256": feedback_sha256,
        "current_state_manifest_sha256": current_state_manifest_sha256,
        "classification_input_sha256": _sha256_json(classification_input),
        "input_source": classification_input.get("input_source"),
        "structured_evidence_sha256": _sha256_json(
            classification_input.get("structured_evidence")
        ),
    }


def _expected_debugger_input_payload(
    *,
    task_id: str,
    run_id: str,
    attempt_id: str,
    classification_input: Mapping[str, Any],
    exact_failure_output: Mapping[str, Any],
    feedback_sha256: str,
    current_state_manifest: Mapping[str, Any],
    current_state_manifest_sha256: str,
) -> tuple[str, dict[str, Any]] | None:
    workspace_text = str(current_state_manifest.get("workspace_root") or "").strip()
    changed_files = current_state_manifest.get("changed_files")
    if (
        not workspace_text
        or not isinstance(changed_files, list)
        or len(changed_files) > 128
    ):
        return None
    workspace = Path(workspace_text).resolve()
    files: list[dict[str, Any]] = []
    for item in changed_files:
        if not isinstance(item, Mapping):
            return None
        relative = str(item.get("path") or "").replace("\\", "/").strip()
        if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            return None
        resolved = (workspace / relative).resolve()
        try:
            resolved.relative_to(workspace)
        except ValueError:
            return None
        files.append(
            {
                "path": relative,
                "absolute_path": str(resolved),
                "expected_exists": item.get("current_exists") is True,
                "expected_sha256": item.get("current_sha256"),
            }
        )
    return str(workspace), {
        "schema_version": "coding.deterministic-debugger-input/v1",
        "task_id": task_id,
        "run_id": run_id,
        "attempt_id": attempt_id,
        "classification_input": json.loads(
            json.dumps(dict(classification_input), sort_keys=True, default=str)
        ),
        "exact_failure_output": json.loads(
            json.dumps(dict(exact_failure_output), sort_keys=True, default=str)
        ),
        "feedback_sha256": feedback_sha256,
        "current_state_manifest_sha256": current_state_manifest_sha256,
        "files": files,
    }


def _valid_deterministic_debugger_trace(
    trace: object,
    *,
    task_id: str,
    run_id: str,
    attempt_id: str,
    classification_input: Mapping[str, Any],
    exact_failure_output: Mapping[str, Any],
    feedback_sha256: str,
    current_state_manifest: Mapping[str, Any],
    current_state_manifest_sha256: str,
) -> bool:
    if not isinstance(trace, Mapping):
        return False
    expected = _expected_debugger_input_payload(
        task_id=task_id,
        run_id=run_id,
        attempt_id=attempt_id,
        classification_input=classification_input,
        exact_failure_output=exact_failure_output,
        feedback_sha256=feedback_sha256,
        current_state_manifest=current_state_manifest,
        current_state_manifest_sha256=current_state_manifest_sha256,
    )
    if expected is None:
        return False
    workspace, expected_payload = expected
    body = dict(trace)
    recorded_sha256 = str(body.pop("trace_sha256", ""))
    argv = trace.get("argv")
    stdout = trace.get("stdout")
    stderr = trace.get("stderr")
    findings = trace.get("findings")
    stdin_text = json.dumps(
        expected_payload,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    if not (
        isinstance(argv, list)
        and len(argv) == 4
        and isinstance(argv[0], str)
        and bool(argv[0])
        and argv[1:3] == ["-I", "-c"]
        and isinstance(argv[3], str)
        and _sha256_text(argv[3]) == REPAIR_DEBUGGER_SCRIPT_SHA256
        and isinstance(stdout, str)
        and isinstance(stderr, str)
        and isinstance(findings, Mapping)
    ):
        return False

    try:
        parsed_stdout = json.loads(stdout)
    except json.JSONDecodeError:
        return False
    post_apply = exact_failure_output.get("post_apply_verification")
    expected_failed_checks = [
        dict(check)
        for check in (
            post_apply.get("checks", []) if isinstance(post_apply, Mapping) else []
        )
        if isinstance(check, Mapping)
        and str(check.get("status") or "").strip().lower() == "failed"
    ]
    finding_files = findings.get("files")
    expected_files = expected_payload["files"]
    if not isinstance(finding_files, list) or len(finding_files) != len(expected_files):
        return False
    for result, expected_file in zip(finding_files, expected_files, strict=True):
        if (
            not isinstance(result, Mapping)
            or result.get("path") != expected_file.get("path")
            or result.get("expected_exists")
            != expected_file.get("expected_exists")
            or result.get("expected_sha256")
            != expected_file.get("expected_sha256")
            or result.get("state_matches") is not True
            or result.get("python_syntax")
            not in {"passed", "failed", "not_applicable"}
        ):
            return False
    exit_status = trace.get("exit_status")
    probe_passed = findings.get("probe_passed")
    return bool(
        trace.get("schema_version") == REPAIR_DEBUGGER_TRACE_SCHEMA
        and trace.get("tool_kind") == "deterministic_python_ast_state_probe"
        and trace.get("deterministic_debugger_invoked") is True
        and trace.get("model_debugger_invoked") is False
        and trace.get("task_id") == task_id
        and trace.get("run_id") == run_id
        and trace.get("attempt_id") == attempt_id
        and trace.get("argv_sha256") == _sha256_json(argv)
        and trace.get("tool_script_sha256") == REPAIR_DEBUGGER_SCRIPT_SHA256
        and trace.get("cwd") == workspace
        and trace.get("input_payload") == expected_payload
        and trace.get("input_sha256") == _sha256_text(stdin_text)
        and trace.get("feedback_sha256") == feedback_sha256
        and trace.get("current_state_manifest_sha256")
        == current_state_manifest_sha256
        and isinstance(exit_status, int)
        and not isinstance(exit_status, bool)
        and exit_status in {0, 1}
        and trace.get("timed_out") is False
        and isinstance(trace.get("duration_ms"), int)
        and not isinstance(trace.get("duration_ms"), bool)
        and trace.get("duration_ms") >= 0
        and trace.get("stdout_sha256") == _sha256_text(stdout)
        and trace.get("stderr_sha256") == _sha256_text(stderr)
        and parsed_stdout == findings
        and findings.get("schema_version")
        == "coding.deterministic-debugger-findings/v1"
        and findings.get("classification_input") == classification_input
        and findings.get("failed_checks") == expected_failed_checks
        and isinstance(probe_passed, bool)
        and probe_passed is (exit_status == 0)
        and trace.get("findings_sha256") == _sha256_json(findings)
        and recorded_sha256
        and _sha256_json(body) == recorded_sha256
    )


def _valid_repair_diagnostic(
    diagnostic: object,
    *,
    task_id: str,
    run_id: str,
    attempt_id: str,
    failure: Mapping[str, Any],
    current_state_manifest: Mapping[str, Any],
    current_state_manifest_sha256: str,
    attempt_state: object,
) -> bool:
    if not isinstance(diagnostic, Mapping) or not isinstance(attempt_state, Mapping):
        return False
    body = dict(diagnostic)
    recorded_sha256 = str(body.pop("diagnostic_sha256", ""))
    feedback_sha256 = str(failure.get("feedback_sha256") or "")
    failure_class = str(failure.get("failure_class") or "")
    source_lane = str(failure.get("source_lane") or "")
    feedback = failure.get("exact_feedback")
    if not isinstance(feedback, Mapping):
        return False
    expected_input = _structured_repair_diagnostic_input(
        failure_class=failure_class,
        source_lane=source_lane,
        exact_feedback=feedback,
    )
    expected_classification = classify_repair_failure(
        diagnostic_code=expected_input["diagnostic_code"],
        stage=expected_input["stage"],
        reason=expected_input["reason"],
        details=_repair_classification_details(
            expected_input,
            feedback_sha256=feedback_sha256,
            current_state_manifest_sha256=current_state_manifest_sha256,
        ),
    ).to_dict()
    debugger_required = expected_classification.get("failure_kind") in {
        "runtime_error",
        "test_environment_error",
    }
    debugger_trace = diagnostic.get("debugger_trace")
    debugger_trace_valid = (
        _valid_deterministic_debugger_trace(
            debugger_trace,
            task_id=task_id,
            run_id=run_id,
            attempt_id=attempt_id,
            classification_input=expected_input,
            exact_failure_output=feedback,
            feedback_sha256=feedback_sha256,
            current_state_manifest=current_state_manifest,
            current_state_manifest_sha256=current_state_manifest_sha256,
        )
        if debugger_required
        else debugger_trace is None
    )
    debugger_events = [
        item
        for item in _mapping_list(attempt_state.get("causal_events"))
        if item.get("event_type") == "deterministic_debugger_executed"
        and item.get("lane_id") == source_lane
    ]
    debugger_event_valid = not debugger_events and not debugger_required
    if debugger_required and len(debugger_events) == 1 and isinstance(
        debugger_trace, Mapping
    ):
        debugger_detail = debugger_events[0].get("detail")
        debugger_event_valid = bool(
            isinstance(debugger_detail, Mapping)
            and debugger_detail.get("trace_sha256")
            == debugger_trace.get("trace_sha256")
            and debugger_detail.get("argv_sha256")
            == debugger_trace.get("argv_sha256")
            and debugger_detail.get("input_sha256")
            == debugger_trace.get("input_sha256")
            and debugger_detail.get("stdout_sha256")
            == debugger_trace.get("stdout_sha256")
            and debugger_detail.get("stderr_sha256")
            == debugger_trace.get("stderr_sha256")
            and debugger_detail.get("findings_sha256")
            == debugger_trace.get("findings_sha256")
            and debugger_detail.get("exit_status")
            == debugger_trace.get("exit_status")
            and debugger_detail.get("timed_out")
            == debugger_trace.get("timed_out")
            and debugger_detail.get("duration_ms")
            == debugger_trace.get("duration_ms")
            and debugger_detail.get("model_debugger_invoked") is False
        )
    event = next(
        (
            item
            for item in _mapping_list(attempt_state.get("causal_events"))
            if item.get("event_type")
            == "deterministic_repair_diagnostic_recorded"
            and item.get("lane_id") == source_lane
            and isinstance(item.get("detail"), Mapping)
            and item["detail"].get("diagnostic_sha256") == recorded_sha256
        ),
        None,
    )
    detail = event.get("detail") if isinstance(event, Mapping) else None
    return bool(
        diagnostic.get("schema_version") == REPAIR_DIAGNOSTIC_SCHEMA
        and diagnostic.get("hook") == "deterministic_failure_classifier"
        and diagnostic.get("model_debugger_invoked") is False
        and diagnostic.get("task_id") == task_id
        and diagnostic.get("run_id") == run_id
        and diagnostic.get("attempt_id") == attempt_id
        and diagnostic.get("failure_class") == failure_class
        and diagnostic.get("source_lane") == source_lane
        and diagnostic.get("classification_input") == expected_input
        and diagnostic.get("classification") == expected_classification
        and diagnostic.get("deterministic_debugger_invoked")
        is debugger_required
        and debugger_trace_valid
        and debugger_event_valid
        and diagnostic.get("exact_failure_output")
        == failure.get("exact_feedback")
        and diagnostic.get("exact_failure_output_sha256") == feedback_sha256
        and diagnostic.get("current_state_manifest") == current_state_manifest
        and diagnostic.get("current_state_manifest_sha256")
        == current_state_manifest_sha256
        and _sha256_json(current_state_manifest)
        == current_state_manifest_sha256
        and recorded_sha256
        and _sha256_json(body) == recorded_sha256
        and isinstance(detail, Mapping)
        and detail.get("failure_kind")
        == expected_classification.get("failure_kind")
        and detail.get("failure_class")
        == expected_classification.get("failure_class")
        and detail.get("feedback_sha256") == feedback_sha256
        and detail.get("current_state_manifest_sha256")
        == current_state_manifest_sha256
        and detail.get("deterministic_debugger_invoked")
        is debugger_required
        and detail.get("debugger_trace_sha256")
        == (
            debugger_trace.get("trace_sha256")
            if isinstance(debugger_trace, Mapping)
            else None
        )
        and detail.get("model_debugger_invoked") is False
    )


def _valid_archived_failure_evidence(
    failure: Mapping[str, Any],
    *,
    attempt_state: Mapping[str, Any],
) -> bool:
    feedback = failure.get("exact_feedback")
    if not isinstance(feedback, Mapping):
        return False
    source_lane = str(failure.get("source_lane") or "")
    expected_role = {
        "reviewer": "coding-reviewer",
        "verifier": "coding-verifier",
    }.get(source_lane)
    participant_id = str(feedback.get("participant_invocation_id") or "")
    runtime_output_id = str(feedback.get("runtime_output_id") or "")
    participant = next(
        (
            item
            for item in _mapping_list(attempt_state.get("participant_records"))
            if item.get("role") == expected_role
            and item.get("invocation_id") == participant_id
        ),
        None,
    )
    runtime_output = next(
        (
            item
            for item in _mapping_list(attempt_state.get("runtime_outputs"))
            if item.get("lane_id") == source_lane
            and item.get("output_id") == runtime_output_id
        ),
        None,
    )
    if (
        not expected_role
        or not participant_id
        or not runtime_output_id
        or not isinstance(participant, Mapping)
        or not isinstance(runtime_output, Mapping)
        or runtime_output.get("producer_invocation_id") != participant_id
        or feedback.get("participant_result") != participant.get("result")
    ):
        return False
    result = participant.get("result")
    payload = runtime_output.get("payload")
    if not isinstance(result, Mapping) or not isinstance(payload, Mapping):
        return False
    if source_lane == "reviewer":
        return (
            list(feedback.get("findings") or []) == list(result.get("findings") or [])
            and list(feedback.get("blocked_reasons") or [])
            == list(result.get("blocked_reasons") or [])
            and list(payload.get("findings") or []) == list(result.get("findings") or [])
            and list(payload.get("blocked_reasons") or [])
            == list(result.get("blocked_reasons") or [])
            and payload.get("semantic_review") == result.get("semantic_review")
            and payload.get("semantic_review_input_sha256")
            == result.get("semantic_review_input_sha256")
            and payload.get("passed") is False
        )
    return (
        str(feedback.get("verdict") or "") == str(result.get("verdict") or "")
        and list(feedback.get("checks") or []) == list(result.get("checks") or [])
        and str(payload.get("verdict") or "") == str(result.get("verdict") or "")
        and list(payload.get("checks") or []) == list(result.get("checks") or [])
    )


def _semantic_repair_feedback_binding(
    repair_request: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(repair_request, Mapping):
        return None
    exact_feedback = repair_request.get("exact_feedback")
    if (
        not isinstance(exact_feedback, Mapping)
        or repair_request.get("feedback_sha256") != _sha256_json(exact_feedback)
    ):
        raise ValueError("semantic_repair_feedback_invalid")
    body = {
        "schema_version": "coding.semantic-repair-feedback/v1",
        "parent_attempt_id": repair_request.get("parent_attempt_id"),
        "parent_attempt_seal_sha256": repair_request.get(
            "parent_attempt_seal_sha256"
        ),
        "failure_class": repair_request.get("failure_class"),
        "source_lane": repair_request.get("source_lane"),
        "exact_feedback": json.loads(
            json.dumps(dict(exact_feedback), sort_keys=True, default=str)
        ),
        "feedback_sha256": repair_request.get("feedback_sha256"),
        "blocked_reasons": list(exact_feedback.get("blocked_reasons") or []),
        "repair_diagnostic_sha256": repair_request.get(
            "repair_diagnostic_sha256"
        ),
    }
    binding = dict(body)
    binding["repair_feedback_sha256"] = _sha256_json(body)
    return binding


def _valid_semantic_review_binding(
    binding: object,
    *,
    task_id: str,
    run_id: str,
    attempt_id: str,
    proposed_diff: str,
    changed_files: list[str],
    adapter_architect_plan_required: bool,
    repair_request: Mapping[str, Any] | None,
    target_plugin_identity: Mapping[str, Any] | None = None,
    canonical_context: Mapping[str, Any] | None = None,
    adapter_provenance: Mapping[str, Any] | None = None,
) -> bool:
    if not isinstance(binding, Mapping):
        return False
    body = dict(binding)
    recorded_binding_sha256 = str(
        body.pop("semantic_review_binding_sha256", "")
    )
    plan_payload = binding.get("server_plan")
    task_spec = binding.get("server_task_spec")
    artifact_snapshots = binding.get("review_artifact_snapshots")
    acceptance = binding.get("acceptance_criteria")
    receipt = binding.get("preview_review_receipt")
    repair_feedback = binding.get("repair_feedback")
    if not (
        isinstance(plan_payload, Mapping)
        and isinstance(task_spec, Mapping)
        and isinstance(artifact_snapshots, Mapping)
        and isinstance(acceptance, list)
        and acceptance
        and isinstance(receipt, Mapping)
    ):
        return False
    try:
        plan = ArchitectPlan.from_dict(dict(plan_payload))
        authority = (
            target_plugin_identity.get("allowed_actions")
            if adapter_architect_plan_required
            and isinstance(target_plugin_identity, Mapping)
            else [plan.coder_packet.target_file.path]
        )
        if not isinstance(authority, (list, tuple)):
            return False
        expected_task_spec = review_task_spec_from_plan(
            plan,
            changed_files,
            authorized_paths=[str(value) for value in authority],
            artifact_snapshots=artifact_snapshots,
        ).to_dict()
        snapshot_baselines = validate_review_artifact_snapshots(
            artifact_snapshots,
            expected_paths=changed_files,
        )
        target_slice = next(
            (
                item
                for item in plan.coder_packet.context_slices
                if item.path == plan.coder_packet.target_file.path
                and item.kind == "target"
            ),
            None,
        )
        if (
            (target_slice is None and plan.coder_packet.target_file.exists)
            or snapshot_baselines.get(plan.coder_packet.target_file.path)
            != (target_slice.content if target_slice is not None else "")
            or not isinstance(
                artifact_snapshots.get(plan.coder_packet.target_file.path),
                Mapping,
            )
            or artifact_snapshots[plan.coder_packet.target_file.path].get(
                "exists"
            )
            is not plan.coder_packet.target_file.exists
        ):
            return False
        review_report = review_diff_deterministically(
            plan,
            proposed_diff,
            task_spec=expected_task_spec,
            task_id=task_id,
            attempt_id=attempt_id,
            artifact_snapshots=artifact_snapshots,
        ).to_dict()
        expected_repair_feedback = _semantic_repair_feedback_binding(
            repair_request
        )
    except Exception:
        return False
    expected_acceptance = [
        {"id": item.id, "description": item.description, "kind": item.kind}
        for item in plan.coder_packet.acceptance_criteria
    ]
    receipt_body = dict(receipt)
    recorded_receipt_sha256 = str(receipt_body.pop("receipt_sha256", ""))
    adapter_evidence = receipt.get("adapter_preview_evidence")
    adapter_evidence_valid = (
        isinstance(adapter_evidence, Mapping)
        and _adapter_architect_plan_evidence_matches(
            adapter_evidence,
            plan_payload=plan_payload,
            plan_id=plan.plan_id,
            acceptance_criteria=expected_acceptance,
            required=adapter_architect_plan_required,
        )
        and (
            not adapter_architect_plan_required
            or _adapter_context_evidence_matches(
                adapter_evidence,
                canonical_context=canonical_context,
                plan=plan,
                target_plugin_identity=target_plugin_identity,
                producer_rendered_prompt_sha256=(
                    str(adapter_provenance.get("rendered_prompt_sha256") or "")
                    if isinstance(adapter_provenance, Mapping)
                    else None
                ),
            )
        )
        and receipt.get("adapter_preview_evidence_sha256")
        == _sha256_json(adapter_evidence)
        and isinstance(adapter_evidence.get("attempt"), Mapping)
        and adapter_evidence["attempt"].get("proposed_diff_sha256")
        == receipt.get("proposed_diff_sha256")
        and adapter_evidence["attempt"].get("preview_status") != "blocked"
        and isinstance(
            adapter_evidence["attempt"].get("git_apply_check"), Mapping
        )
        and adapter_evidence["attempt"]["git_apply_check"].get("passed")
        is True
    ) or (
        adapter_architect_plan_required is False
        and
        adapter_evidence is None
        and receipt.get("adapter_preview_evidence_sha256") is None
    )
    expected_repair_sha256 = (
        expected_repair_feedback.get("repair_feedback_sha256")
        if isinstance(expected_repair_feedback, Mapping)
        else None
    )
    return bool(
        binding.get("schema_version") == "coding.semantic-review-binding/v1"
        and plan.task_id == task_id
        and plan.coder_packet.target_file.path in changed_files
        and list(acceptance) == expected_acceptance
        and dict(task_spec) == expected_task_spec
        and binding.get("server_plan_sha256") == _sha256_json(plan_payload)
        and binding.get("server_task_spec_sha256") == _sha256_json(task_spec)
        and binding.get("review_artifact_snapshots_sha256")
        == _sha256_json(artifact_snapshots)
        and binding.get("acceptance_criteria_sha256")
        == _sha256_json(acceptance)
        and receipt.get("schema_version")
        == "coding.preview-review-receipt/v1"
        and receipt.get("reviewer")
        == "source-proxy.planning.reviewer.deterministic/v1"
        and receipt.get("task_id") == task_id
        and receipt.get("run_id") == run_id
        and receipt.get("attempt_id") == attempt_id
        and receipt.get("server_plan_id") == plan.plan_id
        and receipt.get("server_plan_sha256") == _sha256_json(plan_payload)
        and receipt.get("server_task_spec_sha256") == _sha256_json(task_spec)
        and receipt.get("review_artifact_snapshots_sha256")
        == _sha256_json(artifact_snapshots)
        and receipt.get("acceptance_criteria_sha256")
        == _sha256_json(acceptance)
        and receipt.get("acceptance_criterion_ids")
        == [str(item.get("id") or "") for item in acceptance]
        and receipt.get("adapter_architect_plan_required")
        is adapter_architect_plan_required
        and receipt.get("proposed_diff_sha256")
        == hashlib.sha256(proposed_diff.encode("utf-8")).hexdigest()
        and receipt.get("changed_files") == changed_files
        and receipt.get("deterministic_review_report") == review_report
        and receipt.get("deterministic_review_report_sha256")
        == _sha256_json(review_report)
        and receipt.get("repair_feedback_sha256") == expected_repair_sha256
        and receipt.get("status") == "passed"
        and receipt.get("blocked_reasons") == []
        and review_report.get("passed") is True
        and repair_feedback == expected_repair_feedback
        and binding.get("adapter_architect_plan_required")
        is adapter_architect_plan_required
        and binding.get("repair_feedback_sha256") == expected_repair_sha256
        and adapter_evidence_valid
        and (
            not adapter_architect_plan_required
            or (
                isinstance(adapter_evidence, Mapping)
                and adapter_evidence.get(
                    "review_artifact_snapshots_sha256"
                )
                == _sha256_json(artifact_snapshots)
            )
        )
        and recorded_receipt_sha256
        and _sha256_json(receipt_body) == recorded_receipt_sha256
        and binding.get("preview_review_receipt_sha256")
        == recorded_receipt_sha256
        and recorded_binding_sha256
        and _sha256_json(body) == recorded_binding_sha256
    )


def _adapter_architect_plan_evidence_matches(
    evidence: Mapping[str, Any],
    *,
    plan_payload: Mapping[str, Any],
    plan_id: str,
    acceptance_criteria: list[dict[str, Any]],
    required: bool,
) -> bool:
    """Independently bind claimed adapter planning evidence to the server plan."""

    adapter_plan_id = str(evidence.get("architect_plan_id") or "")
    adapter_plan_sha256 = str(evidence.get("architect_plan_sha256") or "")
    adapter_criteria = evidence.get("acceptance_criteria")
    claimed = bool(adapter_plan_id or adapter_plan_sha256 or adapter_criteria)
    if not claimed:
        return not required
    expected_sha256 = hashlib.sha256(
        json.dumps(
            plan_payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    return bool(
        adapter_plan_id == plan_id
        and adapter_plan_sha256.removeprefix("sha256:") == expected_sha256
        and isinstance(adapter_criteria, list)
        and adapter_criteria
        == json.loads(
            json.dumps(acceptance_criteria, sort_keys=True, default=str)
        )
    )


def _canonical_context_report_truth_valid(report: Mapping[str, Any]) -> bool:
    """Rebuild broker decisions from source and acknowledgement evidence.

    A persisted canonical hash is only a claim.  Independent proof recreates
    the decision-bearing report from the primitive source material and
    lifecycle acknowledgements, then requires every derived field to match.
    """

    raw_sources = report.get("sources_considered")
    raw_acknowledgements = report.get("downstream_acknowledgements")
    raw_applicable_consumers = report.get("applicable_consumers")
    if not (
        isinstance(raw_sources, list)
        and all(isinstance(item, Mapping) for item in raw_sources)
        and isinstance(raw_acknowledgements, Mapping)
        and all(
            isinstance(name, str) and isinstance(value, Mapping)
            for name, value in raw_acknowledgements.items()
        )
        and isinstance(raw_applicable_consumers, list)
        and all(
            isinstance(name, str) and name and name == name.strip()
            for name in raw_applicable_consumers
        )
        and len(raw_applicable_consumers) == len(set(raw_applicable_consumers))
    ):
        return False

    sources: list[dict[str, Any]] = []
    for raw_source in raw_sources:
        source = dict(raw_source)
        # ``consumed`` is a derived field in a persisted broker report.  Only
        # the separately retained caller claim may be replayed into a rebuild.
        source["consumed"] = raw_source.get("consumed_claimed") is True
        sources.append(source)
    try:
        rebuilt = build_context_broker_report(
            sources,
            downstream_consumers={
                str(name): dict(value)
                for name, value in raw_acknowledgements.items()
            },
            applicable_consumers=raw_applicable_consumers,
        )
    except Exception:
        return False
    return all(
        rebuilt.get(field_name) == report.get(field_name)
        for field_name in CONTEXT_REPORT_DECISION_FIELDS
    )


def _architect_context_source_matches_plan(
    report: Mapping[str, Any],
    *,
    plan: ArchitectPlan,
    readable_paths: list[str],
    writable_paths: list[str],
) -> bool:
    """Bind generic-workspace context claims to exact plan and scoped text."""

    raw_sources = report.get("sources_considered")
    if not isinstance(raw_sources, list):
        return False
    architect_sources = [
        item
        for item in raw_sources
        if isinstance(item, Mapping)
        and item.get("source") == ARCHITECT_CONTEXT_SOURCE
    ]
    if len(architect_sources) != 1:
        return False
    source = architect_sources[0]
    packet = source.get("packet")
    if not (
        source.get("considered") is True
        and source.get("status") == "used"
        and source.get("reason") == "architect_selected_current_scoped_source"
        and source.get("required") is True
        and source.get("selected") is True
        and source.get("included") is True
        and source.get("included_in_packet") is True
        and source.get("consumed") is True
        and source.get("authority") == ARCHITECT_CONTEXT_AUTHORITY
        and isinstance(packet, Mapping)
        and set(packet) == ARCHITECT_CONTEXT_PACKET_FIELDS
    ):
        return False

    allowed_paths = packet.get("allowed_paths")
    if not (
        isinstance(allowed_paths, list)
        and allowed_paths == readable_paths
        and writable_paths
        and all(_is_canonical_repo_path(path) for path in allowed_paths)
        and len(allowed_paths) == len(set(allowed_paths))
    ):
        return False
    target = plan.coder_packet.target_file.path
    if not (
        packet.get("plan_id") == plan.plan_id
        and packet.get("target") == target
        and _repo_path_in_scope(target, allowed_paths)
        and _repo_path_in_scope(target, writable_paths)
    ):
        return False

    expected_slices: list[dict[str, Any]] = []
    slice_by_path: dict[str, Any] = {}
    for context_slice in plan.coder_packet.context_slices:
        if not (
            _is_canonical_repo_path(context_slice.path)
            and _repo_path_in_scope(context_slice.path, allowed_paths)
            and _plain_sha256(context_slice.sha256)
            == hashlib.sha256(context_slice.content.encode("utf-8")).hexdigest()
        ):
            return False
        expected_slices.append(
            {
                "path": context_slice.path,
                "kind": context_slice.kind,
                "sha256": context_slice.sha256,
                "line_range": list(context_slice.line_range or ()),
            }
        )
        slice_by_path[context_slice.path] = context_slice
    if packet.get("context_slices") != expected_slices:
        return False

    workspace_context = packet.get("scoped_workspace_context")
    workspace_sha256 = packet.get("scoped_workspace_context_sha256")
    workspace_char_count = packet.get("scoped_workspace_context_char_count")
    manifest = packet.get("scoped_workspace_context_manifest")
    if not (
        isinstance(workspace_context, str)
        and len(workspace_context) <= 12_000
        and _plain_sha256(workspace_sha256)
        == hashlib.sha256(workspace_context.encode("utf-8")).hexdigest()
        and isinstance(workspace_char_count, int)
        and not isinstance(workspace_char_count, bool)
        and workspace_char_count == len(workspace_context)
        and isinstance(manifest, list)
        and all(isinstance(item, Mapping) for item in manifest)
        and bool(workspace_context) is bool(manifest)
    ):
        return False

    workspace_header = "ADDITIONAL CURRENT AUTHORIZED FILES:\n"
    if manifest and not workspace_context.startswith(workspace_header):
        return False
    previous_end = len(workspace_header) if manifest else 0
    manifest_paths: list[str] = []
    for entry in manifest:
        path = entry.get("path")
        rendered_start = entry.get("rendered_start")
        rendered_end = entry.get("rendered_end")
        size = entry.get("size")
        rendered_chars = entry.get("rendered_chars")
        if not (
            set(entry) == ARCHITECT_WORKSPACE_MANIFEST_FIELDS
            and _is_canonical_repo_path(path)
            and _repo_path_in_scope(path, allowed_paths)
            and _plain_sha256(entry.get("sha256")) is not None
            and isinstance(size, int)
            and not isinstance(size, bool)
            and size >= 0
            and _plain_sha256(entry.get("rendered_sha256")) is not None
            and isinstance(rendered_chars, int)
            and not isinstance(rendered_chars, bool)
            and rendered_chars > 0
            and isinstance(entry.get("truncated"), bool)
            and isinstance(rendered_start, int)
            and not isinstance(rendered_start, bool)
            and isinstance(rendered_end, int)
            and not isinstance(rendered_end, bool)
            and previous_end == rendered_start < rendered_end <= len(workspace_context)
        ):
            return False
        rendered = workspace_context[rendered_start:rendered_end]
        rendered_prefix = f"--- {path} ---\n"
        if not (
            len(rendered) == rendered_chars
            and _plain_sha256(entry.get("rendered_sha256"))
            == hashlib.sha256(rendered.encode("utf-8")).hexdigest()
            and rendered.startswith(rendered_prefix)
            and rendered.endswith("\n")
        ):
            return False
        visible_content = rendered[len(rendered_prefix) : -1]
        visible_bytes = visible_content.encode("utf-8")
        truncated = entry.get("truncated")
        if truncated is False and not (
            len(visible_content) <= 3_000
            and size == len(visible_bytes)
            and _plain_sha256(entry.get("sha256"))
            == hashlib.sha256(visible_bytes).hexdigest()
        ):
            return False
        if truncated is True and not (
            len(visible_content) == 3_000
            and size >= len(visible_bytes)
        ):
            return False
        planned_slice = slice_by_path.get(str(path))
        if planned_slice is not None and not (
            _plain_sha256(entry.get("sha256"))
            == _plain_sha256(planned_slice.sha256)
            and size == len(planned_slice.content.encode("utf-8"))
        ):
            return False
        manifest_paths.append(str(path))
        previous_end = rendered_end
    rendered_coder_context = packet.get("rendered_coder_context")
    if not (
        isinstance(rendered_coder_context, str)
        and rendered_coder_context
        and len(rendered_coder_context) <= 24_000
        and _plain_sha256(packet.get("rendered_coder_context_sha256"))
        == hashlib.sha256(rendered_coder_context.encode("utf-8")).hexdigest()
        and isinstance(packet.get("rendered_coder_context_char_count"), int)
        and not isinstance(packet.get("rendered_coder_context_char_count"), bool)
        and packet.get("rendered_coder_context_char_count")
        == len(rendered_coder_context)
        and rendered_coder_context
        == _render_independent_adapter_coder_context(
            plan,
            report,
            workspace_context,
        )
    ):
        return False
    return bool(
        len(manifest_paths) == len(set(manifest_paths))
        and previous_end == len(workspace_context)
    )


def _is_canonical_repo_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    if "\\" in value or "\x00" in value or ":" in value:
        return False
    directory_prefix = value.endswith("/")
    canonical_value = value[:-1] if directory_prefix else value
    if not canonical_value:
        return False
    candidate = PurePosixPath(canonical_value)
    return bool(
        not candidate.is_absolute()
        and candidate.parts
        and all(part not in {"", ".", ".."} for part in candidate.parts)
        and candidate.as_posix() == canonical_value
    )


def _render_independent_adapter_coder_context(
    plan: ArchitectPlan,
    report: Mapping[str, Any],
    workspace_context: str,
) -> str:
    sections = ["CURRENT SERVER-SCOPED SOURCE STATE (read before editing):"]
    for item in plan.coder_packet.context_slices:
        sections.extend(
            [
                f"--- {item.path} ({item.kind}; sha256={item.sha256}) ---",
                item.content,
            ]
        )
    for source in report.get("sources_considered", []):
        if not isinstance(source, Mapping):
            continue
        if str(source.get("source") or "") == ARCHITECT_CONTEXT_SOURCE:
            continue
        if source.get("selected") is not True or source.get("included") is not True:
            continue
        packet = source.get("packet")
        bounded = (
            str(packet.get("bounded_context") or "")
            if isinstance(packet, Mapping)
            else ""
        )
        if bounded:
            sections.extend(
                [
                    f"--- selected context packet: {source.get('source')} ---",
                    bounded,
                ]
            )
    sections.extend(
        [
            "CANONICAL CONTEXT MANIFEST:",
            json.dumps(
                {
                    "selected_sources": report.get("selected_sources", []),
                    "target": plan.coder_packet.target_file.path,
                },
                sort_keys=True,
            ),
        ]
    )
    current_context = "\n".join(sections)[:24_000]
    return "\n".join(
        part for part in (current_context, workspace_context) if part
    )[:24_000]


def _repo_path_in_scope(path: str, allowed_paths: list[str]) -> bool:
    return any(
        path == allowed_path.rstrip("/")
        or path.startswith(allowed_path.rstrip("/") + "/")
        for allowed_path in allowed_paths
    )


def _plain_sha256(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    plain = value.removeprefix("sha256:")
    return plain if re.fullmatch(r"[0-9a-f]{64}", plain) is not None else None


def _adapter_context_evidence_matches(
    evidence: Mapping[str, Any],
    *,
    canonical_context: Mapping[str, Any] | None,
    plan: ArchitectPlan,
    target_plugin_identity: Mapping[str, Any] | None,
    producer_rendered_prompt_sha256: str | None = None,
) -> bool:
    """Independently bind adapter prompt context to the proposal report."""

    if not (
        isinstance(canonical_context, Mapping)
        and isinstance(target_plugin_identity, Mapping)
    ):
        return False
    readable_paths = list(
        target_plugin_identity.get("readable_actions")
        or target_plugin_identity.get("allowed_actions")
        or []
    )
    writable_paths = list(target_plugin_identity.get("allowed_actions") or [])
    if not (
        all(_is_canonical_repo_path(path) for path in readable_paths)
        and all(_is_canonical_repo_path(path) for path in writable_paths)
    ):
        return False
    context_hash = str(canonical_context.get("canonical_report_hash") or "")
    selected = [str(value) for value in canonical_context.get("selected_sources", [])]
    consumed = [str(value) for value in canonical_context.get("consumed_sources", [])]
    coder = (canonical_context.get("downstream_acknowledgements") or {}).get(
        "coder"
    )
    binding = evidence.get("coder_context_binding")
    return bool(
        _canonical_context_report_truth_valid(canonical_context)
        and _architect_context_source_matches_plan(
            canonical_context,
            plan=plan,
            readable_paths=readable_paths,
            writable_paths=writable_paths,
        )
        and context_hash
        and evidence.get("canonical_context_report_hash") == context_hash
        and evidence.get("canonical_context_report_sha256")
        == _sha256_json(canonical_context)
        and list(evidence.get("canonical_context_selected_sources") or [])
        == selected
        and list(evidence.get("canonical_context_consumed_sources") or [])
        == consumed
        and consumed == selected
        and isinstance(coder, Mapping)
        and coder.get("applicable") is True
        and coder.get("acknowledged") is True
        and list(coder.get("sources") or []) == selected
        and isinstance(binding, Mapping)
        and binding.get("canonical_context_report_hash") == context_hash
        and binding.get("rendered_prompt_sha256")
        == evidence.get("producer_rendered_prompt_sha256")
        and (
            producer_rendered_prompt_sha256 is None
            or evidence.get("producer_rendered_prompt_sha256")
            == producer_rendered_prompt_sha256
        )
        and binding.get("consumed") is True
        and list(binding.get("selected_sources") or []) == selected
        and list(binding.get("consumed_sources") or []) == selected
        and re.fullmatch(
            r"[0-9a-f]{64}",
            str(binding.get("rendered_prompt_sha256") or ""),
        )
        is not None
    )


def _reviewer_consumed_semantic_review(
    participant: Mapping[str, Any] | None,
    binding: object,
) -> bool:
    if not isinstance(participant, Mapping) or not isinstance(binding, Mapping):
        return False
    result = participant.get("result")
    acceptance = binding.get("acceptance_criteria")
    if not isinstance(result, Mapping) or not isinstance(acceptance, list):
        return False
    repair_feedback = binding.get("repair_feedback")
    consumed_repair_feedback: dict[str, Any] | None = None
    if isinstance(repair_feedback, Mapping):
        exact_feedback = repair_feedback.get("exact_feedback")
        if not isinstance(exact_feedback, Mapping):
            return False
        consumed_repair_feedback = {
            "status": "consumed",
            "source_lane": repair_feedback.get("source_lane"),
            "feedback_sha256": repair_feedback.get("feedback_sha256"),
            "repair_feedback_sha256": repair_feedback.get(
                "repair_feedback_sha256"
            ),
            "blocked_reasons": list(exact_feedback.get("blocked_reasons") or []),
        }
    expected_semantic_review = {
        "bound": True,
        "status": "passed",
        "semantic_review_binding_sha256": binding.get(
            "semantic_review_binding_sha256"
        ),
        "server_plan_sha256": binding.get("server_plan_sha256"),
        "server_task_spec_sha256": binding.get("server_task_spec_sha256"),
        "acceptance_criteria_sha256": binding.get(
            "acceptance_criteria_sha256"
        ),
        "preview_review_receipt_sha256": binding.get(
            "preview_review_receipt_sha256"
        ),
        "acceptance_criteria": [
            {
                "id": str(item.get("id") or ""),
                "kind": str(item.get("kind") or ""),
                "description": str(item.get("description") or ""),
                "status": "consumed_from_successful_preview",
            }
            for item in acceptance
            if isinstance(item, Mapping)
        ],
        "repair_feedback": consumed_repair_feedback,
    }
    return bool(
        participant.get("passed") is True
        and result.get("passed") is True
        and result.get("findings") == []
        and result.get("blocked_reasons") == []
        and result.get("semantic_review_input_sha256") == _sha256_json(binding)
        and result.get("semantic_review") == expected_semantic_review
    )


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


def _target_adapter_model_call_authority_matches(
    adapter: Mapping[str, Any],
    *,
    run_id: str,
    participant: Mapping[str, Any],
) -> bool:
    """Bind every routed call receipt to this exact run, attempt, and invocation."""

    calls = adapter.get("calls")
    attempt_id = str(participant.get("attempt_id") or "")
    invocation_id = str(participant.get("invocation_id") or "")
    if not (
        isinstance(calls, list)
        and calls
        and attempt_id
        and invocation_id
        and isinstance(adapter.get("call_count"), int)
        and not isinstance(adapter.get("call_count"), bool)
        and adapter.get("call_count") == len(calls)
    ):
        return False
    for index, call in enumerate(calls, start=1):
        if not isinstance(call, Mapping):
            return False
        stage = str(call.get("stage") or "")
        authority = call.get("model_call_authority")
        expected_authority_run_id = (
            f"{run_id}:{attempt_id}:{invocation_id}:{stage}:{index}"
        )
        if not (
            stage in {"architect", "coder", "reviewer"}
            and isinstance(call.get("call_index"), int)
            and not isinstance(call.get("call_index"), bool)
            and call.get("call_index") == index
            and isinstance(authority, Mapping)
            and authority.get("central_gate_check_passed") is True
            and authority.get("run_id") == expected_authority_run_id
        ):
            return False
    return True


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
            "blocked_reasons": list(result.get("blocked_reasons") or []),
            "semantic_review": dict(result.get("semantic_review") or {}),
            "semantic_review_input_sha256": result.get(
                "semantic_review_input_sha256"
            ),
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


def _sha256_text(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"
