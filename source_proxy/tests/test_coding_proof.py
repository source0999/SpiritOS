from __future__ import annotations

import copy
import hashlib
import json
from types import SimpleNamespace
from typing import Any

import pytest

import source_proxy.coding.orchestrator as orchestrator_module
import source_proxy.coding.participants as participants_module
import source_proxy.coding.proof as proof_module
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
    render_evidence_guided_repair_model_task,
    target_plugin_model_input_sha256,
)
from source_proxy.coding.runtime_lane_boundary import RuntimeLaneBoundary
from source_proxy.context.canonical_broker import (
    acknowledge_context_consumer,
    build_context_broker_report,
)
from source_proxy.contracts.coding_lane_contracts import canonical_coding_lane_contracts
from source_proxy.planning.plan import ArchitectPlan
from source_proxy.tasks.long_running import LongRunningTaskError


SOURCE_HEAD = "a" * 40
TASK_ID = "task-production-proof"
RUN_ID = "run-production-proof"
TARGET = "tests/ui-agent-trials/fixtures/dummy-product-site/index.html"
SOURCE_SLICE_CONTENT = "old\n"
SOURCE_SLICE_SHA256 = hashlib.sha256(SOURCE_SLICE_CONTENT.encode("utf-8")).hexdigest()
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


def _model_participant(*, fallback: bool, repair: bool = False) -> dict[str, Any]:
    suffix = "repair" if repair else ("fallback" if fallback else "primary")
    provider = "provider-fallback" if fallback else "provider-primary"
    model = "model-fallback" if fallback else "model-primary"
    output_provenance = _model_output_provenance(
        provider=provider,
        model=model,
        attempt_id=(
            "attempt-repair"
            if repair
            else ("attempt-fallback" if fallback else "attempt-primary")
        ),
        invocation_id=f"model-{suffix}",
    )
    return {
        "schema_version": "coding.recovery-participant/v1",
        "role": "target-plugin-model",
        "lane_id": "coder",
        "run_id": RUN_ID,
        "task_id": TASK_ID,
        "attempt_id": "attempt-repair" if repair else ("attempt-fallback" if fallback else "attempt-primary"),
        "invocation_id": f"model-{suffix}",
        "output_id": f"model-{suffix}-output",
        "provider": provider,
        "model": model,
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


def _adapter_provenance(
    *,
    provider: str = "provider-primary",
    model: str = "model-primary",
    attempt_id: str = "attempt-primary",
    invocation_id: str = "model-primary",
) -> dict[str, Any]:
    producer_call = {
        "call_index": 1,
        "stage": "coder",
        "completed": True,
        "raw_response_observed": True,
        "rendered_prompt_sha256": "1" * 64,
        "raw_response_sha256": "2" * 64,
        "model_alias": "coder",
        "provider": provider,
        "model": model,
        "routed_model": model,
        "model_call_authority": {
            "central_gate_check_passed": True,
            "run_id": f"{RUN_ID}:{attempt_id}:{invocation_id}:coder:1",
        },
    }
    return {
        "schema_version": "spiritos-target-adapter-provenance/v1",
        "plugin_id": "lumacart",
        "selected_prompt_id": "coder-004-add-search-filter",
        "rendered_prompt_sha256": "1" * 64,
        "raw_response_sha256": "2" * 64,
        "transport_kind": "canonical_litellm_router",
        "provider_call_made": True,
        "provider_call_authorized": True,
        "generation_source": "model",
        "terminal_proof_eligible": True,
        "producer_call_index": 1,
        "producer_identity_bound": True,
        "selected_model_alias": "coder",
        "provider": provider,
        "model": model,
        "routed_model": model,
        "calls": [producer_call],
    }


def _model_output_provenance(
    *,
    provider: str = "provider-primary",
    model: str = "model-primary",
    attempt_id: str = "attempt-primary",
    invocation_id: str = "model-primary",
) -> dict[str, Any]:
    return {
        "schema_version": "coding.target-plugin-model-output-provenance/v1",
        "approved_diff_sha256": hashlib.sha256(APPROVED_DIFF.encode("utf-8")).hexdigest(),
        "changed_files": [TARGET],
        "blocked": False,
        "reason_code": "model_bundle_ready",
        "target_adapter_provenance": _adapter_provenance(
            provider=provider,
            model=model,
            attempt_id=attempt_id,
            invocation_id=invocation_id,
        ),
    }


def _semantic_plan_payload() -> dict[str, Any]:
    return {
        "plan_id": "plan-1",
        "task_id": TASK_ID,
        "schema_version": 1,
        "created_at": "2026-07-17T00:00:00Z",
        "source_task": "Repair the backend response semantics.",
        "bundle_snapshot": {
            "bundle_path": "repomix-output.xml",
            "bundle_sha256": "a" * 64,
            "workspace_root": "/tmp/spiritos-proof",
            "generated_at": "2026-07-17T00:00:00Z",
        },
        "classification": {
            "task_class": "fix",
            "visual_change": False,
            "designer_required": False,
            "estimated_complexity": "small",
        },
        "coder_packet": {
            "target_file": {
                "path": TARGET,
                "exists": True,
                "sha256_before": SOURCE_SLICE_SHA256,
            },
            "operation": "edit",
            "acceptance_criteria": [
                {
                    "id": "response_semantics",
                    "description": "The requested response semantics are implemented.",
                    "kind": "behavioral",
                }
            ],
            "constraints": {
                "must_contain": [],
                "must_not_contain": [],
                "preserve_imports": [],
                "preserve_exports": [],
                "max_added_lines": None,
                "max_removed_lines": None,
            },
            "context_slices": [
                {
                    "path": TARGET,
                    "kind": "target",
                    "sha256": SOURCE_SLICE_SHA256,
                    "content": SOURCE_SLICE_CONTENT,
                    "line_range": None,
                }
            ],
            "forbidden_paths": [],
            "style_directives": [],
        },
        "verification_plan": {
            "required_checks": [],
            "designer_review_required": False,
            "architect_review_required": True,
        },
        "budget": {
            "max_coder_attempts": 3,
            "max_total_seconds": 300,
            "cloud_escalation_allowed": False,
        },
    }


def _semantic_review_binding(
    *,
    repaired: bool,
    repair_request: dict[str, Any] | None,
) -> dict[str, Any]:
    return orchestrator_module._build_semantic_review_binding(
        task_id=TASK_ID,
        run_id=RUN_ID,
        attempt_id="attempt-repair" if repaired else "attempt-primary",
        planner_output={"payload": {"task_spec": _semantic_plan_payload()}},
        proposed_diff=APPROVED_DIFF,
        changed_files=[TARGET],
        adapter_diagnostics={},
        adapter_architect_plan_required=False,
        authorized_paths=[TARGET],
        repair_request=repair_request,
    )


def _adapter_semantic_review_binding() -> dict[str, Any]:
    plan_payload = _semantic_plan_payload()
    acceptance = copy.deepcopy(plan_payload["coder_packet"]["acceptance_criteria"])
    diff_sha256 = hashlib.sha256(APPROVED_DIFF.encode("utf-8")).hexdigest()
    canonical_context = _adapter_canonical_context()
    return orchestrator_module._build_semantic_review_binding(
        task_id=TASK_ID,
        run_id=RUN_ID,
        attempt_id="attempt-primary",
        planner_output={"payload": {"task_spec": plan_payload}},
        proposed_diff=APPROVED_DIFF,
        changed_files=[TARGET],
        adapter_diagnostics={
            "architect_plan_id": plan_payload["plan_id"],
            "architect_plan_sha256": hashlib.sha256(
                json.dumps(
                    plan_payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    default=str,
                ).encode("utf-8")
            ).hexdigest(),
            "acceptance_criteria": acceptance,
            "canonical_context_broker": copy.deepcopy(canonical_context),
            "canonical_context_report_hash": canonical_context[
                "canonical_report_hash"
            ],
            "rendered_prompt_sha256": "1" * 64,
            "coder_context_binding": {
                "schema_version": "source-proxy-coder-context-binding/v1",
                "call_index": 1,
                "canonical_context_report_hash": canonical_context[
                    "canonical_report_hash"
                ],
                "rendered_prompt_sha256": "1" * 64,
                "selected_sources": list(canonical_context["selected_sources"]),
                "consumed_sources": list(canonical_context["consumed_sources"]),
                "consumed": True,
            },
            "attempts": [
                {
                    "proposed_diff_sha256": diff_sha256,
                    "preview_status": "ready_for_approval_preview",
                    "git_apply_check": {"passed": True},
                }
            ],
        },
        adapter_architect_plan_required=True,
        authorized_paths=[TARGET],
        repair_request=None,
        canonical_context=canonical_context,
    )


def _adapter_canonical_context() -> dict[str, Any]:
    plan_payload = _semantic_plan_payload()
    rendered_file = f"--- {TARGET} ---\n{SOURCE_SLICE_CONTENT[:3_000]}\n"
    workspace_prefix = "ADDITIONAL CURRENT AUTHORIZED FILES:\n"
    workspace_context = f"{workspace_prefix}{rendered_file}"
    rendered_start = len(workspace_prefix)
    report = build_context_broker_report(
        [
            {
                "source": "http-task-description",
                "considered": True,
                "status": "used",
                "reason": "authenticated_request_bound",
                "required": True,
                "selected": True,
                "included": True,
                "packet": {},
            },
            {
                "source": "architect_repository_context",
                "considered": True,
                "status": "used",
                "reason": "architect_selected_current_scoped_source",
                "required": True,
                "selected": True,
                "included": True,
                "packet": {
                    "plan_id": plan_payload["plan_id"],
                    "target": TARGET,
                    "allowed_paths": [TARGET],
                    "context_slices": [
                        {
                            "path": TARGET,
                            "kind": "target",
                            "sha256": SOURCE_SLICE_SHA256,
                            "line_range": [],
                        }
                    ],
                    "scoped_workspace_context_manifest": [
                        {
                            "path": TARGET,
                            "sha256": SOURCE_SLICE_SHA256,
                            "size": len(SOURCE_SLICE_CONTENT.encode("utf-8")),
                            "rendered_sha256": hashlib.sha256(
                                rendered_file.encode("utf-8")
                            ).hexdigest(),
                            "rendered_chars": len(rendered_file),
                            "truncated": False,
                            "rendered_start": rendered_start,
                            "rendered_end": rendered_start + len(rendered_file),
                        }
                    ],
                    "scoped_workspace_context": workspace_context,
                    "scoped_workspace_context_sha256": hashlib.sha256(
                        workspace_context.encode("utf-8")
                    ).hexdigest(),
                    "scoped_workspace_context_char_count": len(workspace_context),
                },
                "authority": {
                    "schema_version": "source-proxy-derived-architect-context-authority/v1",
                    "kind": "derived_planner_output",
                    "producer": "source_proxy.planning.architect",
                    "separately_bound_by": [
                        "planner_runtime_output",
                        "adapter_plan_sha256",
                        "semantic_review_binding",
                    ],
                },
            },
        ],
        downstream_consumers={
            "planner": {
                "applicable": True,
                "acknowledged": True,
                "sources": [
                    "http-task-description",
                    "architect_repository_context",
                ],
                "evidence": "planner_consumed_authenticated_task",
                "reason": "planner_built_task_spec",
            }
        },
        applicable_consumers=("planner",),
    )
    rendered_coder_context = proof_module._render_independent_adapter_coder_context(
        ArchitectPlan.from_dict(plan_payload),
        report,
        workspace_context,
    )
    architect_source = next(
        item
        for item in report["sources_considered"]
        if item["source"] == "architect_repository_context"
    )
    architect_source["packet"].update(
        {
            "rendered_coder_context": rendered_coder_context,
            "rendered_coder_context_sha256": hashlib.sha256(
                rendered_coder_context.encode("utf-8")
            ).hexdigest(),
            "rendered_coder_context_char_count": len(rendered_coder_context),
        }
    )
    report = _rebuild_context_report(report)
    return acknowledge_context_consumer(
        report,
        consumer="coder",
        evidence="coder_prompt_bound_to_context",
        reason="coder_consumed_selected_context",
    )


def test_semantic_review_binding_canonically_binds_authorized_secondary_snapshot() -> None:
    secondary = "tests/ui-agent-trials/fixtures/dummy-product-site/tests/status.test.js"
    secondary_before = "old secondary\n"
    proposed_diff = (
        APPROVED_DIFF
        + f"diff --git a/{secondary} b/{secondary}\n"
        + f"--- a/{secondary}\n"
        + f"+++ b/{secondary}\n"
        + "@@ -1 +1 @@\n-old secondary\n+SecondaryLiteral\n"
    )
    plan_payload = _semantic_plan_payload()
    plan_payload["source_task"] = f'File "{secondary}" must contain "SecondaryLiteral".'
    plan_payload["coder_packet"]["acceptance_criteria"].append(
        {
            "id": "secondary-literal",
            "description": f'File "{secondary}" must contain "SecondaryLiteral".',
            "kind": "literal",
        }
    )
    acceptance = copy.deepcopy(plan_payload["coder_packet"]["acceptance_criteria"])
    snapshots = {
        TARGET: {
            "schema_version": "coding.review-artifact-snapshot/v1",
            "path": TARGET,
            "exists": True,
            "content": SOURCE_SLICE_CONTENT,
            "content_sha256": SOURCE_SLICE_SHA256,
        },
        secondary: {
            "schema_version": "coding.review-artifact-snapshot/v1",
            "path": secondary,
            "exists": True,
            "content": secondary_before,
            "content_sha256": hashlib.sha256(
                secondary_before.encode("utf-8")
            ).hexdigest(),
        },
    }
    context = _adapter_canonical_context()
    diagnostics = {
        "architect_plan_id": plan_payload["plan_id"],
        "architect_plan_sha256": hashlib.sha256(
            json.dumps(
                plan_payload,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
        ).hexdigest(),
        "acceptance_criteria": acceptance,
        "canonical_context_broker": copy.deepcopy(context),
        "canonical_context_report_hash": context["canonical_report_hash"],
        "rendered_prompt_sha256": "1" * 64,
        "coder_context_binding": {
            "schema_version": "source-proxy-coder-context-binding/v1",
            "call_index": 1,
            "canonical_context_report_hash": context["canonical_report_hash"],
            "rendered_prompt_sha256": "1" * 64,
            "selected_sources": list(context["selected_sources"]),
            "consumed_sources": list(context["consumed_sources"]),
            "consumed": True,
        },
        "review_artifact_snapshots": snapshots,
        "review_artifact_snapshots_sha256": orchestrator_module._sha256_json(
            snapshots
        ),
        "attempts": [
            {
                "proposed_diff_sha256": hashlib.sha256(
                    proposed_diff.encode("utf-8")
                ).hexdigest(),
                "preview_status": "ready_for_approval_preview",
                "git_apply_check": {"passed": True},
            }
        ],
    }
    authority = ["tests/ui-agent-trials/fixtures/dummy-product-site/"]

    binding = orchestrator_module._build_semantic_review_binding(
        task_id=TASK_ID,
        run_id=RUN_ID,
        attempt_id="attempt-primary",
        planner_output={"payload": {"task_spec": plan_payload}},
        proposed_diff=proposed_diff,
        changed_files=[TARGET, secondary],
        adapter_diagnostics=diagnostics,
        adapter_architect_plan_required=True,
        authorized_paths=authority,
        repair_request=None,
        canonical_context=context,
    )

    assert binding["server_task_spec"]["allowed_files"] == [TARGET, secondary]
    evidence = binding["preview_review_receipt"]["deterministic_review_report"][
        "evidence"
    ]
    secondary_evidence = next(
        item for item in evidence if item["requirement_id"] == "secondary-literal"
    )
    assert secondary_evidence["inspected_path"] == secondary
    assert secondary_evidence["satisfied"] is True
    assert orchestrator_module._valid_semantic_review_binding(
        binding,
        task_id=TASK_ID,
        run_id=RUN_ID,
        attempt_id="attempt-primary",
        proposed_diff=proposed_diff,
        changed_files=[TARGET, secondary],
        adapter_architect_plan_required=True,
        repair_request=None,
        canonical_context=context,
        target_plugin_identity={
            "plugin_id": "generic-workspace",
            "allowed_actions": authority,
        },
    )
    replayed = copy.deepcopy(binding)
    replay_receipt = replayed["preview_review_receipt"]
    replay_report = replay_receipt["deterministic_review_report"]
    replay_report["evidence"][0]["attempt_id"] = "attempt-replayed"
    replay_receipt["deterministic_review_report_sha256"] = (
        orchestrator_module._sha256_json(replay_report)
    )
    receipt_body = dict(replay_receipt)
    receipt_body.pop("receipt_sha256")
    replay_receipt["receipt_sha256"] = orchestrator_module._sha256_json(
        receipt_body
    )
    replayed["preview_review_receipt_sha256"] = replay_receipt["receipt_sha256"]
    binding_body = dict(replayed)
    binding_body.pop("semantic_review_binding_sha256")
    replayed["semantic_review_binding_sha256"] = orchestrator_module._sha256_json(
        binding_body
    )
    assert not orchestrator_module._valid_semantic_review_binding(
        replayed,
        task_id=TASK_ID,
        run_id=RUN_ID,
        attempt_id="attempt-primary",
        proposed_diff=proposed_diff,
        changed_files=[TARGET, secondary],
        adapter_architect_plan_required=True,
        repair_request=None,
        canonical_context=context,
        target_plugin_identity={
            "plugin_id": "generic-workspace",
            "allowed_actions": authority,
        },
    )


def _production_canonical_context() -> dict[str, Any]:
    report = build_context_broker_report(
        [
            {
                "source": "http-task-description",
                "considered": True,
                "status": "used",
                "reason": "authenticated_request_bound",
                "required": True,
                "selected": True,
                "included": True,
                "packet": {},
            }
        ],
        downstream_consumers={
            "planner": {
                "applicable": True,
                "acknowledged": True,
                "sources": ["http-task-description"],
                "evidence": "planner_consumed_authenticated_task",
                "reason": "planner_built_task_spec",
            }
        },
        applicable_consumers=("planner",),
    )
    return acknowledge_context_consumer(
        report,
        consumer="coder",
        evidence="coder_prompt_bound_to_context",
        reason="coder_consumed_selected_context",
    )


def _reseal_adapter_context_evidence(
    binding: dict[str, Any],
    canonical_context: dict[str, Any],
) -> None:
    receipt = binding["preview_review_receipt"]
    evidence = receipt["adapter_preview_evidence"]
    context_hash = canonical_context["canonical_report_hash"]
    evidence["canonical_context_report_hash"] = context_hash
    evidence["canonical_context_report_sha256"] = _sha256_json(
        canonical_context
    )
    evidence["canonical_context_selected_sources"] = list(
        canonical_context["selected_sources"]
    )
    evidence["canonical_context_consumed_sources"] = list(
        canonical_context["consumed_sources"]
    )
    coder_binding = evidence["coder_context_binding"]
    coder_binding["canonical_context_report_hash"] = context_hash
    coder_binding["selected_sources"] = list(canonical_context["selected_sources"])
    coder_binding["consumed_sources"] = list(canonical_context["consumed_sources"])
    receipt["adapter_preview_evidence_sha256"] = _sha256_json(evidence)
    receipt_body = dict(receipt)
    receipt_body.pop("receipt_sha256")
    receipt["receipt_sha256"] = _sha256_json(receipt_body)
    binding["preview_review_receipt_sha256"] = receipt["receipt_sha256"]
    binding_body = dict(binding)
    binding_body.pop("semantic_review_binding_sha256")
    binding["semantic_review_binding_sha256"] = _sha256_json(binding_body)


def _rebuild_context_report(report: dict[str, Any]) -> dict[str, Any]:
    sources: list[dict[str, Any]] = []
    for raw_source in report["sources_considered"]:
        source = copy.deepcopy(raw_source)
        source["consumed"] = source.get("consumed_claimed") is True
        sources.append(source)
    return build_context_broker_report(
        sources,
        downstream_consumers=copy.deepcopy(report["downstream_acknowledgements"]),
        applicable_consumers=list(report["applicable_consumers"]),
    )


def _repair_attempt_lineage(
    prior_state: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    prior_artifact = copy.deepcopy(prior_state["immutable_artifact"])
    prior_proposal = copy.deepcopy(prior_state["target_plugin_proposal"])
    feedback = {
        "source_lane": "verifier",
        "blocked_reasons": ["expected status 204 but received 200"],
    }
    failure = {
        "failure_class": "verifier_rejection",
        "source_lane": "verifier",
        "exact_feedback": feedback,
        "feedback_sha256": _sha256_json(feedback),
    }
    current_state_manifest = {
        "schema_version": "coding.current-applied-state-manifest/v1",
        "artifact_sha256": prior_artifact["artifact_sha256"],
        "approval_id": prior_artifact["approval_id"],
        "generation": prior_artifact["generation"],
        "approved_diff_sha256": prior_artifact["approved_diff_sha256"],
        "result_sha256": prior_artifact["result_sha256"],
        "workspace_root": prior_artifact["workspace_root"],
        "changed_files": copy.deepcopy(prior_artifact["changed_files"]),
    }
    current_state_manifest_sha256 = _sha256_json(current_state_manifest)
    classification_input = proof_module._structured_repair_diagnostic_input(
        failure_class=failure["failure_class"],
        source_lane=failure["source_lane"],
        exact_feedback=feedback,
    )
    classification = proof_module.classify_repair_failure(
        diagnostic_code=classification_input["diagnostic_code"],
        stage=classification_input["stage"],
        reason=classification_input["reason"],
        details=proof_module._repair_classification_details(
            classification_input,
            feedback_sha256=failure["feedback_sha256"],
            current_state_manifest_sha256=current_state_manifest_sha256,
        ),
    ).to_dict()
    diagnostic_body = {
        "schema_version": "coding.deterministic-repair-diagnostic/v1",
        "hook": "deterministic_failure_classifier",
        "model_debugger_invoked": False,
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "attempt_id": "attempt-primary",
        "failure_class": failure["failure_class"],
        "source_lane": failure["source_lane"],
        "classification_input": classification_input,
        "classification": classification,
        "deterministic_debugger_invoked": False,
        "debugger_trace": None,
        "exact_failure_output": copy.deepcopy(feedback),
        "exact_failure_output_sha256": failure["feedback_sha256"],
        "current_state_manifest": copy.deepcopy(current_state_manifest),
        "current_state_manifest_sha256": current_state_manifest_sha256,
    }
    repair_diagnostic = dict(diagnostic_body)
    repair_diagnostic["diagnostic_sha256"] = _sha256_json(diagnostic_body)
    diagnostic_event = {
        "event_type": "deterministic_repair_diagnostic_recorded",
        "lane_id": failure["source_lane"],
        "detail": {
            "diagnostic_sha256": repair_diagnostic["diagnostic_sha256"],
            "failure_kind": classification["failure_kind"],
            "failure_class": classification["failure_class"],
            "feedback_sha256": failure["feedback_sha256"],
            "current_state_manifest_sha256": current_state_manifest_sha256,
            "deterministic_debugger_invoked": False,
            "debugger_trace_sha256": None,
            "model_debugger_invoked": False,
        },
    }
    seal_body = {
        "schema_version": "coding.repair-attempt-seal/v1",
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "attempt_id": "attempt-primary",
        "parent_attempt_id": None,
        "attempt_number": 1,
        "next_attempt_id": "attempt-repair",
        "outcome": "verifier_rejection",
        "failure": failure,
        "repair_diagnostic": repair_diagnostic,
        "current_state_manifest": current_state_manifest,
        "current_state_manifest_sha256": current_state_manifest_sha256,
        "approval_binding": {
            "approval_id": prior_artifact["approval_id"],
            "generation": prior_artifact["generation"],
            "approved_diff_sha256": prior_artifact["approved_diff_sha256"],
            "artifact_sha256": prior_artifact["artifact_sha256"],
            "proposal_binding_sha256": prior_proposal["proposal_binding_sha256"],
        },
        "repair_strategy_signature": None,
        "attempt_state": {
            "lane_states": copy.deepcopy(prior_state["lane_states"]),
            "lane_reasons": {},
            "causal_events": [diagnostic_event],
            "runtime_outputs": copy.deepcopy(prior_state["runtime_outputs"]),
            "runtime_acknowledgements": copy.deepcopy(
                prior_state["runtime_acknowledgements"]
            ),
            "runtime_consumptions": copy.deepcopy(prior_state["runtime_consumptions"]),
            "required_output_ids": copy.deepcopy(prior_state["required_output_ids"]),
            "participant_records": copy.deepcopy(prior_state["participant_records"]),
            "immutable_artifact": prior_artifact,
            "target_plugin_proposal": prior_proposal,
            "cartographer_selection_consumption": copy.deepcopy(
                prior_state.get("cartographer_selection_consumption")
            ),
            "cartographer_transfer": copy.deepcopy(
                prior_state["cartographer_transfer"]
            ),
            "cartographer_finalization": copy.deepcopy(
                prior_state["cartographer_finalization"]
            ),
            "recovery_lineage": copy.deepcopy(prior_state["recovery_lineage"]),
            "model_invocations": copy.deepcopy(prior_state["model_invocations"]),
        },
        "sealed_at": "2026-07-17T00:01:00Z",
    }
    seal = dict(seal_body)
    seal["seal_sha256"] = _sha256_json(seal_body)
    disposition_body = {
        "schema_version": "coding.repair-approval-disposition/v1",
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "attempt_id": "attempt-primary",
        "attempt_seal_sha256": seal["seal_sha256"],
        "approval_id": prior_artifact["approval_id"],
        "generation": prior_artifact["generation"],
        "authority_state": "invalidated",
        "failure_reason": "repair_attempt_superseded:verifier_rejection",
    }
    disposition = dict(disposition_body)
    disposition["disposition_sha256"] = _sha256_json(disposition_body)
    request_body = {
        "schema_version": "coding.evidence-guided-repair-request/v1",
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "attempt_id": "attempt-repair",
        "parent_attempt_id": "attempt-primary",
        "attempt_number": 2,
        "original_task": "Repair the backend response semantics.",
        "max_attempts": 3,
        "failure_class": failure["failure_class"],
        "source_lane": failure["source_lane"],
        "exact_feedback": copy.deepcopy(feedback),
        "feedback_sha256": failure["feedback_sha256"],
        "current_state_manifest": copy.deepcopy(current_state_manifest),
        "current_state_manifest_sha256": seal["current_state_manifest_sha256"],
        "repair_diagnostic": copy.deepcopy(repair_diagnostic),
        "repair_diagnostic_sha256": repair_diagnostic["diagnostic_sha256"],
        "parent_attempt_seal_sha256": seal["seal_sha256"],
        "prior_approval_id": prior_artifact["approval_id"],
        "prior_approved_diff_sha256": prior_artifact["approved_diff_sha256"],
        "prior_approval_disposition": copy.deepcopy(disposition),
        "prior_approval_disposition_sha256": disposition["disposition_sha256"],
        "requirements": {
            "fresh_proposal_required": True,
            "fresh_approval_required": True,
            "current_applied_state_is_baseline": True,
            "new_evidence_or_changed_strategy_required": True,
        },
    }
    request = dict(request_body)
    request["repair_input_sha256"] = _sha256_json(request_body)
    return seal, request, disposition


def _production_state(
    *,
    fallback: bool = False,
    repaired: bool = False,
    source_head: str = SOURCE_HEAD,
) -> dict[str, Any]:
    prior_state = _production_state() if repaired else None
    attempt_history: list[dict[str, Any]] = []
    attempt_dispositions: list[dict[str, Any]] = []
    repair_request: dict[str, Any] | None = None
    if isinstance(prior_state, dict):
        seal, repair_request, disposition = _repair_attempt_lineage(prior_state)
        attempt_history = [seal]
        attempt_dispositions = [disposition]
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

    canonical_context_report = _production_canonical_context()
    context_hash = canonical_context_report["canonical_report_hash"]
    context_output = issue(
        "context-broker",
        "context-producer",
        {"context_hash": context_hash, "verdict": "GO"},
    )
    planner_context_output = issue(
        "context-broker",
        "planner-context-producer",
        {"context_hash": context_hash, "verdict": "GO"},
    )
    planner_output = issue(
        "planner",
        "planner-producer",
        {"plan_id": "plan-1", "task_spec": _semantic_plan_payload()},
    )
    selected_model = _model_participant(fallback=fallback, repair=repaired)
    model_task = "Repair the backend response semantics."
    if isinstance(repair_request, dict):
        model_task, _ = render_evidence_guided_repair_model_task(
            model_task,
            repair_request,
        )
    selected_model["input_sha256"] = target_plugin_model_input_sha256(
        task=model_task,
        target_plugin_identity={
            "plugin_id": "lumacart",
            "repository_id": "repo",
            "worktree_id": "worktree",
            "source_head": source_head,
            "selected_prompt_id": "coder-004-add-search-filter",
        },
        canonical_context=canonical_context_report,
    )
    model_output_provenance = _model_output_provenance(
        provider=selected_model["provider"],
        model=selected_model["model"],
        attempt_id=selected_model["attempt_id"],
        invocation_id=selected_model["invocation_id"],
    )
    adapter_provenance = model_output_provenance["target_adapter_provenance"]
    model_context_output = issue(
        "context-broker",
        "model-context-producer",
        {"context_hash": context_hash, "verdict": "GO"},
    )
    consume(
        context_output,
        consumer="context-refresh-consumer",
        payload={"consumer": "context-refresh", "context_hash": context_hash},
    )
    consume(
        planner_context_output,
        consumer="planner-consumer",
        payload={"consumer": "planner", "context_hash": context_hash},
    )
    model_context_ack, model_context_consumption = consume(
        model_context_output,
        consumer=selected_model["invocation_id"],
        payload={"consumer": "coder", "context_hash": context_hash},
    )
    planner_ack, planner_consumption = consume(
        planner_output,
        consumer=selected_model["invocation_id"],
        payload={"context_hash": context_hash},
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
        "attempt_id": "attempt-repair" if repaired else "attempt-primary",
        "parent_attempt_id": "attempt-primary" if repaired else None,
        "attempt_number": 2 if repaired else 1,
        "original_task": "Repair the backend response semantics.",
        "runtime_output_id": coder_output["output_id"],
        "runtime_output_artifact_sha256": coder_output["artifact_hash"],
        "producer_model_invocation_id": selected_model["invocation_id"],
        "producer_model_output_sha256": selected_model["output_sha256"],
        "producer_model_artifact_sha256": selected_model["artifact_sha256"],
        "producer_model_alias": adapter_provenance["selected_model_alias"],
        "producer_model_provider": selected_model["provider"],
        "producer_model_name": selected_model["model"],
        "producer_adapter_call_index": adapter_provenance["producer_call_index"],
        "planner_runtime_output_id": planner_output["output_id"],
        "planner_runtime_artifact_sha256": planner_output["artifact_hash"],
        "planner_consumer_acknowledgement_id": planner_ack["acknowledgement_id"],
        "planner_consumption_id": planner_consumption["consumption_id"],
        "model_output_provenance": model_output_provenance,
        "target_adapter_provenance": adapter_provenance,
        "target_plugin_identity": {
            "plugin_id": "lumacart",
            "repository_id": "repo",
            "worktree_id": "worktree",
            "source_head": source_head,
            "selected_prompt_id": "coder-004-add-search-filter",
        },
        "selected_prompt_id": "coder-004-add-search-filter",
        "selected_context_id": "search-filter",
        "context_hash": context_hash,
        "canonical_context_report": canonical_context_report,
        "canonical_context_report_sha256": _sha256_json(canonical_context_report),
        "context_runtime_output_id": model_context_output["output_id"],
        "context_runtime_artifact_sha256": model_context_output["artifact_hash"],
        "context_consumer_acknowledgement_id": model_context_ack[
            "acknowledgement_id"
        ],
        "context_consumption_id": model_context_consumption["consumption_id"],
        "source_head": source_head,
        "target_source_head": source_head,
        "target": TARGET,
        "approved_diff_sha256": hashlib.sha256(APPROVED_DIFF.encode("utf-8")).hexdigest(),
        "changed_files": [TARGET],
        "status": "ready_for_approval_preview",
    }
    if repaired:
        assert repair_request is not None
        proposal.update(
            {
                "repair_context": copy.deepcopy(repair_request),
                "repair_input_sha256": repair_request["repair_input_sha256"],
                "repair_prompt_sha256": _sha256_json({"repair": repair_request}),
                "repair_strategy_signature": _sha256_json(
                    {
                        "repair_input_sha256": repair_request["repair_input_sha256"],
                        "approved_diff_sha256": hashlib.sha256(
                            APPROVED_DIFF.encode("utf-8")
                        ).hexdigest(),
                        "provider": selected_model["provider"],
                        "model": selected_model["model"],
                    }
                ),
            }
        )
    semantic_review_binding = _semantic_review_binding(
        repaired=repaired,
        repair_request=repair_request,
    )
    proposal["semantic_review_binding"] = semantic_review_binding
    proposal["semantic_review_binding_sha256"] = semantic_review_binding[
        "semantic_review_binding_sha256"
    ]
    proposal["proposal_binding_sha256"] = _sha256_json(proposal)

    cart_consumer = selected_model["invocation_id"]
    transfer = {
        "proposal_id": "cart-proposal",
        "selection_id": "cart-selection",
        "selection_generation": 1,
        "transfer_event_id": "cart-transfer-event",
        "downstream_consumer_invocation_id": cart_consumer,
        "target": TARGET,
        "provenance": {"source_head": source_head},
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
        "source_head": source_head,
    }
    if isinstance(prior_state, dict):
        transfer = copy.deepcopy(prior_state["cartographer_transfer"])
        cart_finalization = copy.deepcopy(prior_state["cartographer_finalization"])
        cart_identity = copy.deepcopy(
            prior_state["immutable_artifact"]["cartographer_identity"]
        )
    approval_id = "coding-approval-repair" if repaired else "coding-approval"
    generation = 2 if repaired else 1
    artifact = {
        "schema_version": "coding.immutable-applied-artifact/v2",
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "approval_id": approval_id,
        "generation": generation,
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
        "source_commit": source_head,
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
        "semantic_review_identity": copy.deepcopy(semantic_review_binding),
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
    semantic_findings, semantic_result = participants_module._semantic_review_findings(
        artifact,
        semantic_review_binding,
    )
    assert semantic_findings == []
    reviewer = _service_participant(
        role="coding-reviewer",
        artifact=artifact,
        result={
            "passed": True,
            "findings": [],
            "blocked_reasons": [],
            "semantic_review": semantic_result,
            "semantic_review_input_sha256": _sha256_json(
                semantic_review_binding
            ),
        },
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
        {
            "passed": True,
            "findings": [],
            "blocked_reasons": [],
            "semantic_review": semantic_result,
            "semantic_review_input_sha256": _sha256_json(
                semantic_review_binding
            ),
        },
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
        coder_output,
        consumer=executor["invocation_id"],
        payload={"approval_id": approval_id, "generation": generation},
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
            payload={"approval_id": approval_id, "generation": generation},
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
        "attempt_id": "attempt-repair" if repaired else "attempt-primary",
        "parent_attempt_id": "attempt-primary" if repaired else None,
        "attempt_number": 2 if repaired else 1,
        "max_attempts": 3,
        "attempt_history": attempt_history,
        "attempt_dispositions": attempt_dispositions,
        "repair_request": repair_request,
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
            "repair": "completed" if repaired else "skipped",
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


def test_production_proof_accepts_sealed_evidence_guided_repair_with_fresh_approval() -> None:
    state = _production_state(repaired=True)

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["failures"] == []
    assert proof["terminal_proof_eligible"] is True
    assert proof["attempt_id"] == "attempt-repair"
    assert proof["attempt_count"] == 2
    assert proof["failed_attempt_seal_sha256s"] == [
        state["attempt_history"][0]["seal_sha256"]
    ]
    assert proof["failed_attempt_repair_diagnostic_sha256s"] == [
        state["attempt_history"][0]["repair_diagnostic"]["diagnostic_sha256"]
    ]
    assert state["immutable_artifact"]["approval_id"] != state["attempt_history"][0][
        "approval_binding"
    ]["approval_id"]


def test_production_proof_rejects_rehashed_acceptance_criterion_drift() -> None:
    state = _production_state()
    binding = state["target_plugin_proposal"]["semantic_review_binding"]
    binding["acceptance_criteria"][0]["description"] = "Forged criterion."
    binding["acceptance_criteria_sha256"] = _sha256_json(
        binding["acceptance_criteria"]
    )
    receipt = binding["preview_review_receipt"]
    receipt["acceptance_criteria_sha256"] = binding["acceptance_criteria_sha256"]
    receipt_body = dict(receipt)
    receipt_body.pop("receipt_sha256")
    receipt["receipt_sha256"] = _sha256_json(receipt_body)
    binding["preview_review_receipt_sha256"] = receipt["receipt_sha256"]
    binding_body = dict(binding)
    binding_body.pop("semantic_review_binding_sha256")
    binding["semantic_review_binding_sha256"] = _sha256_json(binding_body)
    state["target_plugin_proposal"]["semantic_review_binding_sha256"] = binding[
        "semantic_review_binding_sha256"
    ]

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "semantic_review_binding_invalid" in proof["failures"]


def test_semantic_review_builder_requires_generic_adapter_plan_evidence() -> None:
    with pytest.raises(
        orchestrator_module.CodingOrchestratorError,
        match="coding_adapter_architect_plan_mismatch",
    ):
        orchestrator_module._build_semantic_review_binding(
            task_id=TASK_ID,
            run_id=RUN_ID,
            attempt_id="attempt-primary",
            planner_output={"payload": {"task_spec": _semantic_plan_payload()}},
            proposed_diff=APPROVED_DIFF,
            changed_files=[TARGET],
            adapter_diagnostics={},
            adapter_architect_plan_required=True,
            authorized_paths=[TARGET],
            repair_request=None,
        )


@pytest.mark.parametrize(
    "field",
    [
        "architect_plan_id",
        "architect_plan_sha256",
        "acceptance_criteria",
        "canonical_context_report_hash",
        "producer_rendered_prompt_sha256",
        "removed",
        "object_removed",
    ],
)
def test_independent_semantic_review_rejects_rehashed_adapter_plan_drift(
    field: str,
) -> None:
    binding = _adapter_semantic_review_binding()
    receipt = binding["preview_review_receipt"]
    evidence = receipt["adapter_preview_evidence"]
    if field == "object_removed":
        receipt["adapter_preview_evidence"] = None
        receipt["adapter_preview_evidence_sha256"] = None
    elif field == "removed":
        evidence["architect_plan_id"] = None
        evidence["architect_plan_sha256"] = None
        evidence["acceptance_criteria"] = []
    elif field == "acceptance_criteria":
        evidence[field][0]["description"] = "Forged adapter criterion."
    else:
        evidence[field] = "forged"
    if field != "object_removed":
        receipt["adapter_preview_evidence_sha256"] = _sha256_json(evidence)
    receipt_body = dict(receipt)
    receipt_body.pop("receipt_sha256")
    receipt["receipt_sha256"] = _sha256_json(receipt_body)
    binding["preview_review_receipt_sha256"] = receipt["receipt_sha256"]
    binding_body = dict(binding)
    binding_body.pop("semantic_review_binding_sha256")
    binding["semantic_review_binding_sha256"] = _sha256_json(binding_body)

    assert proof_module._valid_semantic_review_binding(
        binding,
        task_id=TASK_ID,
        run_id=RUN_ID,
        attempt_id="attempt-primary",
        proposed_diff=APPROVED_DIFF,
        changed_files=[TARGET],
        adapter_architect_plan_required=True,
        repair_request=None,
        canonical_context=_adapter_canonical_context(),
        target_plugin_identity={
            "readable_actions": [TARGET],
            "allowed_actions": [TARGET],
        },
        adapter_provenance={"rendered_prompt_sha256": "1" * 64},
    ) is False


def test_independent_semantic_review_rejects_resealed_stale_context_hash() -> None:
    binding = _adapter_semantic_review_binding()
    canonical_context = _adapter_canonical_context()
    task_source = next(
        item
        for item in canonical_context["sources_considered"]
        if item["source"] == "http-task-description"
    )
    task_source["packet"] = {"forged": "replacement task material"}
    # The attacker updates every enclosing receipt seal but cannot make the
    # stale decision-bearing broker hash truthful without rebuilding it.
    _reseal_adapter_context_evidence(binding, canonical_context)

    assert proof_module._canonical_context_report_truth_valid(canonical_context) is False
    assert proof_module._valid_semantic_review_binding(
        binding,
        task_id=TASK_ID,
        run_id=RUN_ID,
        attempt_id="attempt-primary",
        proposed_diff=APPROVED_DIFF,
        changed_files=[TARGET],
        adapter_architect_plan_required=True,
        repair_request=None,
        canonical_context=canonical_context,
        target_plugin_identity={
            "readable_actions": [TARGET],
            "allowed_actions": [TARGET],
        },
        adapter_provenance={"rendered_prompt_sha256": "1" * 64},
    ) is False


def test_independent_semantic_review_rejects_rehashed_architect_scope_drift() -> None:
    binding = _adapter_semantic_review_binding()
    canonical_context = _adapter_canonical_context()
    architect_source = next(
        item
        for item in canonical_context["sources_considered"]
        if item["source"] == "architect_repository_context"
    )
    architect_source["packet"]["target"] = "forged/outside-plan.py"
    architect_source["packet"]["allowed_paths"] = ["forged/outside-plan.py"]
    canonical_context = _rebuild_context_report(canonical_context)
    _reseal_adapter_context_evidence(binding, canonical_context)

    assert proof_module._canonical_context_report_truth_valid(canonical_context) is True
    assert proof_module._valid_semantic_review_binding(
        binding,
        task_id=TASK_ID,
        run_id=RUN_ID,
        attempt_id="attempt-primary",
        proposed_diff=APPROVED_DIFF,
        changed_files=[TARGET],
        adapter_architect_plan_required=True,
        repair_request=None,
        canonical_context=canonical_context,
        target_plugin_identity={
            "readable_actions": [TARGET],
            "allowed_actions": [TARGET],
        },
        adapter_provenance={"rendered_prompt_sha256": "1" * 64},
    ) is False


def test_independent_semantic_review_rejects_rehashed_nonplan_manifest_claim() -> None:
    binding = _adapter_semantic_review_binding()
    canonical_context = _adapter_canonical_context()
    plan = ArchitectPlan.from_dict(_semantic_plan_payload())
    extra_path = "tests/support.py"
    extra_content = "VALUE = 'bound'\n"
    extra_rendered = f"--- {extra_path} ---\n{extra_content}\n"
    architect_source = next(
        item
        for item in canonical_context["sources_considered"]
        if item["source"] == "architect_repository_context"
    )
    packet = architect_source["packet"]
    rendered_start = len(packet["scoped_workspace_context"])
    packet["allowed_paths"] = [TARGET, extra_path]
    packet["scoped_workspace_context"] += extra_rendered
    packet["scoped_workspace_context_manifest"].append(
        {
            "path": extra_path,
            "sha256": hashlib.sha256(extra_content.encode("utf-8")).hexdigest(),
            "size": len(extra_content.encode("utf-8")),
            "rendered_sha256": hashlib.sha256(
                extra_rendered.encode("utf-8")
            ).hexdigest(),
            "rendered_chars": len(extra_rendered),
            "truncated": False,
            "rendered_start": rendered_start,
            "rendered_end": rendered_start + len(extra_rendered),
        }
    )
    packet["scoped_workspace_context_sha256"] = hashlib.sha256(
        packet["scoped_workspace_context"].encode("utf-8")
    ).hexdigest()
    packet["scoped_workspace_context_char_count"] = len(
        packet["scoped_workspace_context"]
    )
    rendered_coder_context = proof_module._render_independent_adapter_coder_context(
        plan,
        canonical_context,
        packet["scoped_workspace_context"],
    )
    packet.update(
        {
            "rendered_coder_context": rendered_coder_context,
            "rendered_coder_context_sha256": hashlib.sha256(
                rendered_coder_context.encode("utf-8")
            ).hexdigest(),
            "rendered_coder_context_char_count": len(rendered_coder_context),
        }
    )
    canonical_context = _rebuild_context_report(canonical_context)
    _reseal_adapter_context_evidence(binding, canonical_context)
    identity = {
        "readable_actions": [TARGET, extra_path],
        "allowed_actions": [TARGET, extra_path],
    }
    arguments = {
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "attempt_id": "attempt-primary",
        "proposed_diff": APPROVED_DIFF,
        "changed_files": [TARGET],
        "adapter_architect_plan_required": True,
        "repair_request": None,
        "canonical_context": canonical_context,
        "target_plugin_identity": identity,
        "adapter_provenance": {"rendered_prompt_sha256": "1" * 64},
    }
    assert proof_module._valid_semantic_review_binding(binding, **arguments) is True

    architect_source = next(
        item
        for item in canonical_context["sources_considered"]
        if item["source"] == "architect_repository_context"
    )
    extra_entry = architect_source["packet"][
        "scoped_workspace_context_manifest"
    ][1]
    extra_entry["sha256"] = "f" * 64
    extra_entry["size"] += 7
    canonical_context = _rebuild_context_report(canonical_context)
    _reseal_adapter_context_evidence(binding, canonical_context)
    arguments["canonical_context"] = canonical_context

    assert proof_module._canonical_context_report_truth_valid(canonical_context) is True
    assert proof_module._valid_semantic_review_binding(binding, **arguments) is False


def test_independent_semantic_review_accepts_server_owned_directory_prefix_scope() -> None:
    binding = _adapter_semantic_review_binding()
    canonical_context = _adapter_canonical_context()
    prefix = "tests/ui-agent-trials/fixtures/dummy-product-site/"
    architect_source = next(
        item
        for item in canonical_context["sources_considered"]
        if item["source"] == "architect_repository_context"
    )
    architect_source["packet"]["allowed_paths"] = [prefix]
    canonical_context = _rebuild_context_report(canonical_context)
    _reseal_adapter_context_evidence(binding, canonical_context)

    assert proof_module._is_canonical_repo_path(prefix) is True
    assert proof_module._valid_semantic_review_binding(
        binding,
        task_id=TASK_ID,
        run_id=RUN_ID,
        attempt_id="attempt-primary",
        proposed_diff=APPROVED_DIFF,
        changed_files=[TARGET],
        adapter_architect_plan_required=True,
        repair_request=None,
        canonical_context=canonical_context,
        target_plugin_identity={
            "readable_actions": [prefix],
            "allowed_actions": [prefix],
        },
        adapter_provenance={"rendered_prompt_sha256": "1" * 64},
    ) is True


def test_production_proof_rejects_unconsumed_repair_blocked_reasons() -> None:
    state = _production_state(repaired=True)
    reviewer = next(
        item for item in state["participant_records"] if item["role"] == "coding-reviewer"
    )
    reviewer["result"]["semantic_review"]["repair_feedback"][
        "blocked_reasons"
    ] = []
    reviewer["output_sha256"] = _sha256_json(reviewer["result"])
    reviewer["record_sha256"] = participant_record_sha256(reviewer)

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "reviewer_semantic_review_consumption_invalid" in proof["failures"]


def test_production_proof_rejects_adapter_producer_identity_drift() -> None:
    state = _production_state()
    state["target_plugin_proposal"]["producer_model_name"] = "forged-model"

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "model_adapter_producer_identity_binding_invalid" in proof["failures"]


def test_production_proof_rejects_tampered_repair_seal_and_context() -> None:
    state = _production_state(repaired=True)
    state["attempt_history"][0]["failure"]["exact_feedback"]["blocked_reasons"] = [
        "forged pass"
    ]

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "repair_attempt_history_invalid" in proof["failures"]
    assert "repair_context_binding_invalid" in proof["failures"]


def test_production_proof_rejects_approval_reuse_across_repair_attempts() -> None:
    state = _production_state(repaired=True)
    state["immutable_artifact"]["approval_id"] = state["attempt_history"][0][
        "approval_binding"
    ]["approval_id"]

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "repair_approval_reuse_detected" in proof["failures"]


def test_production_proof_requires_invalidated_approval_disposition_for_each_seal() -> None:
    state = _production_state(repaired=True)
    disposition = state["attempt_dispositions"][0]
    disposition["authority_state"] = "consuming"
    unsigned = dict(disposition)
    unsigned.pop("disposition_sha256")
    disposition["disposition_sha256"] = _sha256_json(unsigned)
    state["repair_request"]["prior_approval_disposition"] = copy.deepcopy(disposition)
    state["repair_request"]["prior_approval_disposition_sha256"] = disposition[
        "disposition_sha256"
    ]

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "repair_approval_disposition_invalid" in proof["failures"]


def test_live_repair_feedback_must_match_archived_participant_and_runtime_output() -> None:
    result = {
        "passed": False,
        "findings": ["status mismatch"],
        "blocked_reasons": ["status mismatch"],
        "semantic_review": {},
        "semantic_review_input_sha256": None,
    }
    failure = {
        "source_lane": "reviewer",
        "exact_feedback": {
            "source_lane": "reviewer",
            "participant_invocation_id": "reviewer-invocation",
            "runtime_output_id": "reviewer-runtime-output",
            "findings": ["status mismatch"],
            "blocked_reasons": ["status mismatch"],
            "participant_result": copy.deepcopy(result),
        },
    }
    attempt_state = {
        "participant_records": [
            {
                "role": "coding-reviewer",
                "invocation_id": "reviewer-invocation",
                "result": copy.deepcopy(result),
            }
        ],
        "runtime_outputs": [
            {
                "lane_id": "reviewer",
                "output_id": "reviewer-runtime-output",
                "producer_invocation_id": "reviewer-invocation",
                "payload": {
                    "passed": False,
                    "findings": ["status mismatch"],
                    "blocked_reasons": ["status mismatch"],
                    "semantic_review": {},
                    "semantic_review_input_sha256": None,
                },
            }
        ],
    }

    assert proof_module._valid_archived_failure_evidence(
        failure,
        attempt_state=attempt_state,
    ) is True
    attempt_state["runtime_outputs"][0]["payload"]["findings"] = ["forged pass"]
    assert proof_module._valid_archived_failure_evidence(
        failure,
        attempt_state=attempt_state,
    ) is False


def test_repair_diagnostic_proof_rejects_model_debugger_claim_or_input_drift() -> None:
    seal, _, _ = _repair_attempt_lineage(_production_state())
    diagnostic = seal["repair_diagnostic"]
    failure = seal["failure"]

    kwargs = {
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "attempt_id": seal["attempt_id"],
        "failure": failure,
        "current_state_manifest": seal["current_state_manifest"],
        "current_state_manifest_sha256": seal[
            "current_state_manifest_sha256"
        ],
        "attempt_state": seal["attempt_state"],
    }
    assert proof_module._valid_repair_diagnostic(diagnostic, **kwargs) is True

    forged = copy.deepcopy(diagnostic)
    forged["model_debugger_invoked"] = True
    unsigned = dict(forged)
    unsigned.pop("diagnostic_sha256")
    forged["diagnostic_sha256"] = _sha256_json(unsigned)
    assert proof_module._valid_repair_diagnostic(forged, **kwargs) is False

    forged = copy.deepcopy(diagnostic)
    forged["classification_input"]["stage"] = "reviewer"
    unsigned = dict(forged)
    unsigned.pop("diagnostic_sha256")
    forged["diagnostic_sha256"] = _sha256_json(unsigned)
    assert proof_module._valid_repair_diagnostic(forged, **kwargs) is False


def test_proof_validates_actual_bounded_runtime_debugger_trace(tmp_path: Any) -> None:
    changed = tmp_path / "service.py"
    changed.write_text("def handler():\n    return 200\n", encoding="utf-8")
    current_sha256 = hashlib.sha256(changed.read_bytes()).hexdigest()
    manifest = {
        "workspace_root": str(tmp_path),
        "changed_files": [
            {
                "path": "service.py",
                "current_exists": True,
                "current_sha256": current_sha256,
            }
        ],
    }
    manifest_sha256 = _sha256_json(manifest)
    feedback = {
        "post_apply_verification": {
            "checks": [
                {
                    "id": "public_api_contract",
                    "required": True,
                    "status": "failed",
                    "exit_code": 1,
                    "output_tail": "expected 204; got 200",
                }
            ]
        }
    }
    feedback_sha256 = _sha256_json(feedback)
    classification_input = proof_module._structured_repair_diagnostic_input(
        failure_class="verifier_rejection",
        source_lane="verifier",
        exact_feedback=feedback,
    )
    trace = orchestrator_module._run_deterministic_repair_debugger(
        task_id=TASK_ID,
        run_id=RUN_ID,
        attempt_id="attempt-runtime-debugger",
        classification_input=classification_input,
        exact_failure_output=feedback,
        feedback_sha256=feedback_sha256,
        current_state_manifest=manifest,
        current_state_manifest_sha256=manifest_sha256,
    )
    kwargs = {
        "task_id": TASK_ID,
        "run_id": RUN_ID,
        "attempt_id": "attempt-runtime-debugger",
        "classification_input": classification_input,
        "exact_failure_output": feedback,
        "feedback_sha256": feedback_sha256,
        "current_state_manifest": manifest,
        "current_state_manifest_sha256": manifest_sha256,
    }

    assert proof_module._valid_deterministic_debugger_trace(trace, **kwargs) is True
    assert trace["findings"]["failed_checks"] == feedback[
        "post_apply_verification"
    ]["checks"]
    assert trace["findings"]["files"][0]["python_syntax"] == "passed"

    forged = copy.deepcopy(trace)
    forged["findings"]["failed_checks"] = []
    unsigned = dict(forged)
    unsigned.pop("trace_sha256")
    forged["trace_sha256"] = _sha256_json(unsigned)
    assert proof_module._valid_deterministic_debugger_trace(forged, **kwargs) is False


def test_production_proof_rejects_reused_repair_strategy_signature() -> None:
    state = _production_state(repaired=True)
    state["attempt_history"][0]["repair_strategy_signature"] = state[
        "target_plugin_proposal"
    ]["repair_strategy_signature"]
    seal_body = dict(state["attempt_history"][0])
    seal_body.pop("seal_sha256")
    state["attempt_history"][0]["seal_sha256"] = _sha256_json(seal_body)

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "repair_attempt_strategy_reused" in proof["failures"]


def test_production_proof_rejects_forged_runtime_consumption_binding() -> None:
    state = _production_state()
    state["runtime_consumptions"][0]["consumer_invocation_id"] = "forged-consumer"

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "runtime_lane_boundary_invalid" in proof["failures"]


def test_production_proof_reports_exact_immutable_proposal_identity_drift() -> None:
    state = _production_state()
    state["immutable_artifact"]["target_plugin_identity"][
        "result_identity"
    ] = "forged-target-result"
    state["immutable_artifact"]["prompt_identity"][
        "selected_prompt_id"
    ] = "forged-prompt"
    state["immutable_artifact"]["model_output_identity"][
        "runtime_output_id"
    ] = "forged-output"

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "immutable_artifact_proposal_identity_mismatch" in proof["failures"]
    assert "immutable_artifact_target_plugin_identity_mismatch" in proof["failures"]
    assert "immutable_artifact_prompt_id_mismatch" in proof["failures"]
    assert (
        "immutable_artifact_model_output_runtime_output_id_mismatch"
        in proof["failures"]
    )


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


def test_production_proof_rejects_rehashed_adapter_plugin_identity_drift() -> None:
    state = _production_state()
    proposal = state["target_plugin_proposal"]
    adapter = copy.deepcopy(proposal["target_adapter_provenance"])
    adapter["plugin_id"] = "generic-workspace"
    output_provenance = copy.deepcopy(proposal["model_output_provenance"])
    output_provenance["target_adapter_provenance"] = adapter
    output_sha256 = _sha256_json(output_provenance)
    proposal["target_adapter_provenance"] = adapter
    proposal["model_output_provenance"] = output_provenance
    proposal["producer_model_output_sha256"] = output_sha256
    selected = next(
        item
        for item in state["model_invocations"]
        if item["invocation_id"] == proposal["producer_model_invocation_id"]
    )
    selected["output_sha256"] = output_sha256
    state["cartographer_finalization"]["downstream_acknowledgement"][
        "consumer_output_sha256"
    ] = output_sha256
    proposal_body = dict(proposal)
    proposal_body.pop("proposal_binding_sha256", None)
    proposal["proposal_binding_sha256"] = _sha256_json(proposal_body)
    artifact = state["immutable_artifact"]
    artifact["prompt_identity"]["proposal_binding_sha256"] = proposal[
        "proposal_binding_sha256"
    ]
    artifact["model_output_identity"]["producer_model_output_sha256"] = (
        output_sha256
    )

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "canonical_model_provenance_invalid" in proof["failures"]


def test_production_proof_rejects_model_call_authority_from_another_run() -> None:
    state = _production_state()
    state["target_plugin_proposal"]["target_adapter_provenance"]["calls"][0][
        "model_call_authority"
    ]["run_id"] = "unrelated-run:attempt-primary:model-primary:coder:1"

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "model_call_authority_binding_invalid" in proof["failures"]


def test_production_proof_rejects_rehashed_planner_handoff_drift() -> None:
    state = _production_state()
    proposal = state["target_plugin_proposal"]
    proposal["planner_runtime_output_id"] = proposal["context_runtime_output_id"]
    proposal_body = dict(proposal)
    proposal_body.pop("proposal_binding_sha256", None)
    proposal["proposal_binding_sha256"] = _sha256_json(proposal_body)
    state["immutable_artifact"]["prompt_identity"][
        "proposal_binding_sha256"
    ] = proposal["proposal_binding_sha256"]

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "model_planner_consumption_binding_invalid" in proof["failures"]


def test_production_proof_independently_rederives_model_input_binding() -> None:
    state = _production_state()
    state["model_invocations"][0]["input_sha256"] = "sha256:" + "f" * 64

    proof = derive_production_proof(state, expected_source_head=SOURCE_HEAD)

    assert proof["terminal_proof_eligible"] is False
    assert "model_input_binding_mismatch" in proof["failures"]


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
