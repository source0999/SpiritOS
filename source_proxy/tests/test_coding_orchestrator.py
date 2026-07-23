from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

import source_proxy.coding.orchestrator as orchestrator_module
from source_proxy.coding.participants import CodingParticipantError
from source_proxy.context.canonical_broker import (
    acknowledge_context_consumer,
    build_context_broker_report,
    derived_architect_context_authority,
)
from source_proxy.coding.orchestrator import (
    CodingLaneStateMachine,
    CodingOrchestrator,
    CodingOrchestratorError,
    LANE_SEQUENCE,
)
from source_proxy.planning.plan import ArchitectPlan
from source_proxy.tasks.long_running import execute_approved_long_running_task
from source_proxy.target_plugins.adapter import (
    GENERIC_WORKSPACE_CONTEXT_ID,
    GENERIC_WORKSPACE_PLUGIN_ID,
    GENERIC_WORKSPACE_PROFILE,
    GENERIC_WORKSPACE_PROMPT_ID,
    ResolvedTargetPlugin,
)
from source_proxy.target_plugins.generic_workspace import (
    _build_context_report,
    _render_scoped_workspace_context,
)


def test_lane_state_machine_has_explicit_dependency_order_and_terminal_states() -> None:
    state = CodingLaneStateMachine(task_id="task-1", run_id="run-1")

    assert tuple(state.lane_states) == LANE_SEQUENCE
    state.transition("context-broker", "running")
    state.transition("context-broker", "completed")
    state.transition("planner", "running")
    state.transition("planner", "completed")
    state.transition("coder", "running")
    state.transition("coder", "failed", reason="provider_timeout")
    state.transition("coder", "recovering")
    state.transition("coder", "completed")
    state.transition("repair", "skipped", reason="no_repair_needed")

    assert state.lane_states["coder"] == "completed"
    assert state.lane_reasons["repair"] == "no_repair_needed"
    with pytest.raises(CodingOrchestratorError, match="invalid_coding_lane_transition"):
        state.transition("coder", "running")


def test_orchestrator_delegates_execution_to_the_existing_executor_by_default() -> None:
    orchestrator = CodingOrchestrator()

    assert orchestrator._executor is execute_approved_long_running_task


def test_execute_approved_uses_exact_lumacart_prompt_membership() -> None:
    state = CodingLaneStateMachine(task_id="task-prompt-membership", run_id="run-prompts")
    state.lane_states["context-broker"] = "completed"
    state.lane_states["planner"] = "completed"
    orchestrator = CodingOrchestrator(
        state_loader=lambda _task_id: state.receipt(summary="prompt membership")
    )
    common = {
        "task_id": "task-prompt-membership",
        "approved_diff": "diff --git a/a b/a\n",
        "action": "apply",
        "approval_id": "approval-1",
        "context_hash": "context-hash",
    }

    with pytest.raises(
        CodingOrchestratorError,
        match="target_plugin_runtime_output_id_missing",
    ):
        orchestrator.execute_approved(
            **common,
            selected_prompt_id="coder-010-protected-path-pressure-trap",
        )

    with pytest.raises(
        CodingOrchestratorError,
        match="coding_lane_output_missing:planner",
    ):
        orchestrator.execute_approved(
            **common,
            selected_prompt_id="coder-001-generic-lab-trial",
        )


def test_interrupted_persisted_lane_requires_explicit_recovery_or_degrades(monkeypatch: pytest.MonkeyPatch) -> None:
    persisted: list[dict[str, object]] = []
    state = CodingLaneStateMachine(task_id="task-1", run_id="run-1")
    state.transition("coder", "running")
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(state),
    )

    receipt = CodingOrchestrator(state_loader=lambda _task_id: state.receipt(summary="interrupted")).recover_interrupted_lane(
        "task-1", lane_id="coder"
    )

    assert receipt["lane_states"]["coder"] == "blocked"
    assert receipt["recovery"] == {"lane_id": "coder", "outcome": "degraded", "recovered": False}
    assert persisted[-1]["lane_reasons"]["coder"] == "recovery_action_required"


def test_interrupted_persisted_lane_records_only_a_successful_explicit_recovery(monkeypatch: pytest.MonkeyPatch) -> None:
    persisted: list[dict[str, object]] = []
    state = CodingLaneStateMachine(task_id="task-1", run_id="run-1")
    state.transition("coder", "running")
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(state),
    )

    receipt = CodingOrchestrator(state_loader=lambda _task_id: state.receipt(summary="interrupted")).recover_interrupted_lane(
        "task-1", lane_id="coder", recovery=lambda: True
    )

    assert receipt["lane_states"]["coder"] == "completed"
    assert receipt["recovery"] == {"lane_id": "coder", "outcome": "recovered", "recovered": True}
    assert persisted[-1]["lane_reasons"]["coder"] == "explicit_lane_recovery_completed"


def test_start_persists_the_canonical_broker_report_before_any_lane_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    persisted: list[dict[str, object]] = []
    monkeypatch.setattr(
        orchestrator_module,
        "record_canonical_context_broker_for_task",
        lambda _task_id, *, report, orchestrator_run_id: persisted.append(
            {"report": report, "run_id": orchestrator_run_id}
        ) or report,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append({"state": state}),
    )

    receipt = CodingOrchestrator().start(
        "task-1",
        sources=[
            {
                "source": "task-context",
                "considered": True,
                "status": "used",
                "required": True,
                "selected": True,
                "included": True,
            }
        ],
    )

    report = persisted[0]["report"]
    assert isinstance(report, dict)
    assert report["canonical"] is True
    assert report["applicable_consumers"] == ["planner"]
    assert receipt["lane_states"]["context-broker"] == "running"
    assert receipt["lane_states"]["planner"] == "pending"


def _pending_authority_outbox_state() -> CodingLaneStateMachine:
    state = CodingLaneStateMachine(task_id="task-finalization-retry", run_id="run-finalization-retry")
    state.lane_states["coder"] = "completed"
    state.lane_states["reviewer"] = "completed"
    state.lane_states["evidence-recorder"] = "running"
    state.immutable_artifact = {"artifact_sha256": "sha256:" + "a" * 64}
    evidence = {"schema_version": "coding.approval-finalization-evidence/v1", "task_id": state.task_id}
    state.authority_finalization = {
        "schema_version": "coding.authority-finalization-outbox/v1",
        "state": "pending_authority_commit",
        "approval": {"approval_id": "approval-finalization-retry", "generation": 7, "binding": {}},
        "result_id": f"coding-execution-{state.task_id}",
        "evidence": evidence,
        "evidence_sha256": orchestrator_module._sha256_json(evidence),
        "orchestrator_state_sha256": "sha256:" + "b" * 64,
        "status": "succeeded",
    }
    return state


def test_authority_outbox_replays_exact_request_after_response_persist_loss(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initial = _pending_authority_outbox_state().receipt(summary="frozen")
    authority_requests: list[dict[str, Any]] = []
    authority_commits = 0
    fail_receipt_persist = True
    persisted = copy.deepcopy(initial)

    def finalize_authority(approval: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        nonlocal authority_commits
        request = {"approval": copy.deepcopy(approval), **copy.deepcopy(kwargs)}
        authority_requests.append(request)
        idempotent = authority_commits == 1
        authority_commits = 1
        return {
            "approval_id": approval["approval_id"],
            "generation": approval["generation"],
            "state": "consumed",
            "result_id": kwargs["result_id"],
            "idempotent": idempotent,
        }

    def persist_state(_task_id: str, *, state: dict[str, Any]) -> None:
        nonlocal persisted, fail_receipt_persist
        if (
            fail_receipt_persist
            and state["authority_finalization"]["state"]
            == "authority_committed_local_pending"
        ):
            fail_receipt_persist = False
            raise OSError("simulated receipt persist loss")
        persisted = copy.deepcopy(state)

    monkeypatch.setattr(orchestrator_module, "finalize_coding_execution_approval", finalize_authority)
    monkeypatch.setattr(orchestrator_module, "record_coding_orchestrator_state", persist_state)
    monkeypatch.setattr(
        orchestrator_module,
        "finalize_orchestrated_coding_execution",
        lambda task_id, **_kwargs: {"task": {"id": task_id, "status": "completed"}},
    )

    with pytest.raises(OSError, match="simulated receipt persist loss"):
        CodingOrchestrator(state_loader=lambda _task_id: copy.deepcopy(initial)).complete_post_apply(
            "task-finalization-retry"
        )
    result = CodingOrchestrator(
        state_loader=lambda _task_id: copy.deepcopy(persisted)
    ).complete_post_apply("task-finalization-retry")

    assert authority_commits == 1
    assert len(authority_requests) == 2
    assert authority_requests[0] == authority_requests[1]
    assert result["task"]["status"] == "completed"
    assert result["coding_orchestrator"]["authority_finalization"]["state"] == "locally_committed"


def test_authority_outbox_does_not_reconsume_after_local_commit_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initial = _pending_authority_outbox_state().receipt(summary="frozen")
    persisted = copy.deepcopy(initial)
    authority_calls = 0
    local_calls = 0

    def persist_state(_task_id: str, *, state: dict[str, Any]) -> None:
        nonlocal persisted
        persisted = copy.deepcopy(state)

    def finalize_authority(approval: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        nonlocal authority_calls
        authority_calls += 1
        return {
            "approval_id": approval["approval_id"],
            "generation": approval["generation"],
            "state": "consumed",
            "result_id": kwargs["result_id"],
            "idempotent": False,
        }

    def finalize_local(task_id: str, **_kwargs: Any) -> dict[str, Any]:
        nonlocal local_calls
        local_calls += 1
        if local_calls == 1:
            raise OSError("simulated local commit failure")
        return {"task": {"id": task_id, "status": "completed"}}

    monkeypatch.setattr(orchestrator_module, "finalize_coding_execution_approval", finalize_authority)
    monkeypatch.setattr(orchestrator_module, "record_coding_orchestrator_state", persist_state)
    monkeypatch.setattr(orchestrator_module, "finalize_orchestrated_coding_execution", finalize_local)

    with pytest.raises(OSError, match="simulated local commit failure"):
        CodingOrchestrator(state_loader=lambda _task_id: copy.deepcopy(initial)).complete_post_apply(
            "task-finalization-retry"
        )
    assert persisted["authority_finalization"]["state"] == "authority_committed_local_pending"

    result = CodingOrchestrator(
        state_loader=lambda _task_id: copy.deepcopy(persisted)
    ).complete_post_apply("task-finalization-retry")

    assert authority_calls == 1
    assert local_calls == 2
    assert result["coding_orchestrator"]["authority_finalization"]["state"] == "locally_committed"


def test_planner_refresh_persists_and_consumes_the_latest_exact_context_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    states: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []

    def record_report(
        _task_id: str,
        *,
        report: dict[str, Any],
        orchestrator_run_id: str,
    ) -> dict[str, Any]:
        assert orchestrator_run_id
        reports.append(copy.deepcopy(report))
        return report

    def acknowledge_report(
        _task_id: str,
        *,
        consumer: str,
        evidence: str,
        source_names: list[str] | None = None,
        applicable: bool = True,
        reason: str = "",
    ) -> dict[str, Any]:
        refreshed = acknowledge_context_consumer(
            reports[-1],
            consumer=consumer,
            evidence=evidence,
            source_names=source_names,
            applicable=applicable,
            reason=reason,
        )
        reports.append(refreshed)
        return refreshed

    monkeypatch.setattr(
        orchestrator_module,
        "record_canonical_context_broker_for_task",
        record_report,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "acknowledge_task_context_consumer",
        acknowledge_report,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "canonical_context_broker_for_task",
        lambda _task_id: copy.deepcopy(reports[-1]),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: states.append(copy.deepcopy(state)),
    )
    orchestrator = CodingOrchestrator(
        planner_loader=lambda _task_id: {"task_id": "task-context-refresh"},
        state_loader=lambda _task_id: states[-1] if states else None,
    )
    started = orchestrator.start(
        "task-context-refresh",
        sources=[
            {
                "source": "http-task-description",
                "considered": True,
                "status": "used",
                "required": True,
                "selected": True,
                "included": True,
            }
        ],
    )
    initial_output = started["runtime_outputs"][0]

    receipt = orchestrator.acknowledge_planner("task-context-refresh")

    context_outputs = [
        item for item in receipt["runtime_outputs"] if item["lane_id"] == "context-broker"
    ]
    assert len(context_outputs) == 2
    refreshed_output = context_outputs[-1]
    assert refreshed_output["payload"]["context_hash"] == reports[-1][
        "canonical_report_hash"
    ]
    initial_consumption = next(
        item
        for item in receipt["runtime_consumptions"]
        if item["output_id"] == initial_output["output_id"]
    )
    assert initial_consumption["consumer_invocation_id"].startswith(
        "context-broker-refresh-invocation-"
    )
    planner_consumption = next(
        item
        for item in receipt["runtime_consumptions"]
        if item["output_id"] == refreshed_output["output_id"]
    )
    planner_output = next(
        item for item in receipt["runtime_outputs"] if item["lane_id"] == "planner"
    )
    assert planner_consumption["consumer_invocation_id"] == planner_output[
        "producer_invocation_id"
    ]
    planner_ack = next(
        item
        for item in receipt["runtime_acknowledgements"]
        if item["acknowledgement_id"] == planner_consumption["acknowledgement_id"]
    )
    assert planner_ack["payload"]["context_hash"] == reports[-1][
        "canonical_report_hash"
    ]
    refresh_event = next(
        item
        for item in receipt["causal_events"]
        if item["event_type"] == "context_report_refreshed"
    )
    assert refresh_event["detail"]["predecessor_output_id"] == initial_output["output_id"]
    assert refresh_event["detail"]["refreshed_output_id"] == refreshed_output["output_id"]


def test_production_advance_is_persisted_around_the_existing_task_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    persisted: list[dict[str, object]] = []
    state = CodingLaneStateMachine(task_id="task-advance", run_id="run-advance")
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(state),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "advance_long_running_task",
        lambda task_id, **_kwargs: {"task": {"id": task_id, "status": "planning"}},
    )
    orchestrator = CodingOrchestrator(
        state_loader=lambda _task_id: persisted[-1] if persisted else state.receipt(summary="initial")
    )

    receipt = orchestrator.advance("task-advance")

    assert receipt["task"]["status"] == "planning"
    assert [
        event["event_type"] for event in receipt["coding_orchestrator"]["causal_events"]
    ][-2:] == [
        "task_advance_requested",
        "task_advance_completed",
    ]


@pytest.mark.parametrize("fallback_transport", ["injected_callback", "direct_ollama"])
@pytest.mark.parametrize("primary_provider_call_made", [True, False])
def test_target_plugin_model_failure_and_noncanonical_fallback_share_one_durable_run_without_terminal_proof(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    fallback_transport: str,
    primary_provider_call_made: bool,
) -> None:
    persisted: list[dict[str, object]] = []
    state = CodingLaneStateMachine(task_id="task-recovery", run_id="run-recovery")
    state.lane_states["context-broker"] = "completed"
    state.lane_states["planner"] = "completed"
    _seed_consumed_context_output(state, context_hash="planner-context-hash")
    source_head = "a" * 40
    plugin = ResolvedTargetPlugin(
        schema_version="spiritos-target-plugin/v1",
        plugin_id="lumacart",
        repository_id="repo",
        worktree_id="worktree",
        workspace_root=str(tmp_path),
        branch="test",
        state_namespace="namespace",
        fixture_root="tests/ui-agent-trials/fixtures/dummy-product-site/",
        source_head=source_head,
        selected_prompt_id="coder-004-add-search-filter",
        selected_context_id="search-filter",
        execution_profile="coder-10",
        allowed_actions=("propose_diff",),
        result_identity="result",
    )
    results = iter(
        [
            {
                "proposed_diff": "",
                "coder_blocked": True,
                "reason_code": "coder_model_timeout",
                "blocked_reason": "primary provider timed out",
                "coder_diagnostics": {
                    "provider_call_made": primary_provider_call_made,
                    "selected_model_alias": "primary",
                    "provider": "primary-provider",
                    "model": "primary-model",
                    "changed_files": [],
                },
            },
            {
                "proposed_diff": "diff --git a/index.html b/index.html\n",
                "coder_blocked": False,
                "target_adapter_provenance": {
                    "schema_version": "spiritos-target-adapter-provenance/v1",
                    "rendered_prompt_sha256": "1" * 64,
                    "raw_response_sha256": "2" * 64,
                    "transport_kind": fallback_transport,
                    "provider_call_made": True,
                    "provider_call_authorized": fallback_transport == "direct_ollama",
                    "generation_source": "model",
                    "terminal_proof_eligible": False,
                },
                "coder_diagnostics": {
                    "provider_call_made": True,
                    "selected_model_alias": "fallback",
                    "provider": "fallback-provider",
                    "model": "fallback-model",
                    "changed_files": ["index.html"],
                },
            },
        ]
    )
    monkeypatch.setenv("SPIRITOS_CODING_PRIMARY_MODEL_ALIAS", "primary")
    monkeypatch.setenv("SPIRITOS_CODING_FALLBACK_MODEL_ALIAS", "fallback")
    monkeypatch.setattr(orchestrator_module, "current_head", lambda: source_head)
    latest_context_report = _canonical_context_report()
    acknowledgement_count = 0

    def acknowledge_context(*_args: object, **_kwargs: object) -> dict[str, Any]:
        nonlocal acknowledgement_count, latest_context_report
        acknowledgement_count += 1
        latest_context_report = _canonical_context_report()
        latest_context_report["canonical_report_hash"] = (
            f"context-hash-{acknowledgement_count}"
        )
        return copy.deepcopy(latest_context_report)

    monkeypatch.setattr(
        orchestrator_module,
        "acknowledge_task_context_consumer",
        acknowledge_context,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "canonical_context_broker_for_task",
        lambda _task_id: copy.deepcopy(latest_context_report),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "execute_target_plugin_command",
        lambda *_args, **_kwargs: next(results),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "route_provider_for_alias",
        lambda alias: f"{alias}-provider",
    )
    monkeypatch.setattr(
        orchestrator_module,
        "route_model_for_alias",
        lambda alias: f"{alias}-model",
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(state),
    )
    orchestrator = CodingOrchestrator(
        state_loader=lambda _task_id: persisted[-1] if persisted else state.receipt(summary="initial")
    )

    receipt = orchestrator.propose_target_plugin(
        "task-recovery",
        plugin=plugin,
        task="Add a model-authored product search filter.",
    )

    assert receipt["run_id"] == "run-recovery"
    assert receipt["recovery_lineage"][0]["proof_eligible"] is True
    assert receipt["recovery_lineage"][0]["decision"]["kind"] == "fallback"
    assert receipt["recovery_lineage"][0]["replacement"]["provider"] == "fallback-provider"
    assert len(receipt["model_invocations"]) == 2
    assert receipt["model_invocations"][0]["passed"] is False
    assert receipt["model_invocations"][1]["passed"] is True
    context_consumers = {
        item["consumer_invocation_id"]
        for item in receipt["runtime_consumptions"]
        if item["lane_id"] == "context-broker"
    }
    assert {
        receipt["model_invocations"][0]["invocation_id"],
        receipt["model_invocations"][1]["invocation_id"],
    }.issubset(context_consumers)
    proposal = receipt["target_plugin_proposal"]
    assert proposal["target_adapter_provenance"]["transport_kind"] == fallback_transport
    assert proposal["target_adapter_provenance"]["terminal_proof_eligible"] is False
    assert (
        proposal["model_output_provenance"]["target_adapter_provenance"]
        == proposal["target_adapter_provenance"]
    )
    assert receipt["target_plugin_output_id"] in receipt["required_output_ids"]
    assert all(
        output["output_id"] != receipt["target_plugin_output_id"]
        or output["payload"]["approved_diff"].startswith("diff --git")
        for output in receipt["runtime_outputs"]
    )


def _canonical_target_plugin_result(
    target: str,
    *,
    plugin_id: str = "lumacart",
    selected_prompt_id: str = "coder-004-add-search-filter",
) -> dict[str, Any]:
    producer_call = {
        "call_index": 1,
        "stage": "coder",
        "completed": True,
        "raw_response_observed": True,
        "rendered_prompt_sha256": "1" * 64,
        "raw_response_sha256": "2" * 64,
        "model_alias": "openai",
        "provider": "openai",
        "model": "openai/test-coder",
        "routed_model": "openai/test-coder",
    }
    provenance = {
        "schema_version": "spiritos-target-adapter-provenance/v1",
        "plugin_id": plugin_id,
        "selected_prompt_id": selected_prompt_id,
        "rendered_prompt_sha256": "1" * 64,
        "raw_response_sha256": "2" * 64,
        "transport_kind": "canonical_litellm_router",
        "provider_call_made": True,
        "provider_call_authorized": True,
        "generation_source": "model",
        "trust_status": "canonical_router_model_output_validated",
        "terminal_proof_eligible": True,
        "producer_call_index": 1,
        "producer_identity_bound": True,
        "selected_model_alias": "openai",
        "provider": "openai",
        "model": "openai/test-coder",
        "routed_model": "openai/test-coder",
        "calls": [producer_call],
    }
    return {
        "proposed_diff": (
            f"diff --git a/{target} b/{target}\n"
            f"--- a/{target}\n"
            f"+++ b/{target}\n"
            "@@ -1 +1 @@\n-old\n+new\n"
        ),
        "coder_blocked": False,
        "reason_code": "model_bundle_ready",
        "target_adapter_provenance": provenance,
        "coder_diagnostics": {
            "provider_call_made": True,
            "selected_model_alias": "openai",
            "provider": "openai",
            "model": "openai/test-coder",
            "changed_files": [target],
        },
    }


def test_model_participant_uses_adapter_final_producer_identity_not_configured_alias() -> None:
    target = "tests/ui-agent-trials/fixtures/dummy-product-site/index.html"
    result = _canonical_target_plugin_result(target)
    provenance = result["target_adapter_provenance"]
    producer = provenance["calls"][0]
    producer.update(
        {
            "model_alias": "repair",
            "provider": "ollama",
            "model": "ollama_chat/repair-coder",
            "routed_model": "ollama_chat/repair-coder",
        }
    )
    provenance.update(
        {
            "selected_model_alias": "repair",
            "provider": "ollama",
            "model": "ollama_chat/repair-coder",
            "routed_model": "ollama_chat/repair-coder",
        }
    )
    result["coder_diagnostics"].update(
        {
            "selected_model_alias": "primary",
            "provider": "stale-provider",
            "model": "stale-model",
        }
    )

    participant = orchestrator_module._target_plugin_model_participant(
        run=CodingLaneStateMachine(task_id="task-producer", run_id="run-producer"),
        task_id="task-producer",
        attempt_id="attempt-producer",
        input_sha256="a" * 64,
        result=result,
        configured_alias="primary",
        started_at="2026-07-22T00:00:00Z",
        completed_at="2026-07-22T00:00:01Z",
    )

    assert participant["provider"] == "ollama"
    assert participant["model"] == "ollama_chat/repair-coder"


def _propose_canonical_target_plugin(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[CodingOrchestrator, list[dict[str, object]], dict[str, Any]]:
    persisted: list[dict[str, object]] = []
    target = "tests/ui-agent-trials/fixtures/dummy-product-site/index.html"
    state = CodingLaneStateMachine(task_id="task-binding", run_id="run-binding")
    state.lane_states["context-broker"] = "completed"
    state.lane_states["planner"] = "completed"
    _seed_consumed_context_output(
        state,
        context_hash="planner-context-hash",
        target=target,
    )
    source_head = "a" * 40
    plugin = ResolvedTargetPlugin(
        schema_version="spiritos-target-plugin/v1",
        plugin_id="lumacart",
        repository_id="repo",
        worktree_id="worktree",
        workspace_root=str(tmp_path),
        branch="test",
        state_namespace="namespace",
        fixture_root="tests/ui-agent-trials/fixtures/dummy-product-site/",
        source_head=source_head,
        selected_prompt_id="coder-004-add-search-filter",
        selected_context_id="search-filter",
        execution_profile="coder-10",
        allowed_actions=("propose_diff",),
        result_identity="result",
        target_source_head="b" * 40,
    )
    monkeypatch.setenv("SPIRITOS_CODING_PRIMARY_MODEL_ALIAS", "openai")
    monkeypatch.delenv("SPIRITOS_CODING_FALLBACK_MODEL_ALIAS", raising=False)
    monkeypatch.setattr(orchestrator_module, "current_head", lambda: source_head)
    monkeypatch.setattr(
        orchestrator_module,
        "acknowledge_task_context_consumer",
        lambda *_args, **_kwargs: _canonical_context_report(),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "canonical_context_broker_for_task",
        lambda _task_id: _canonical_context_report(),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "execute_target_plugin_command",
        lambda *_args, **_kwargs: _canonical_target_plugin_result(target),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(state),
    )
    orchestrator = CodingOrchestrator(
        state_loader=lambda _task_id: (
            persisted[-1] if persisted else state.receipt(summary="initial")
        )
    )
    receipt = orchestrator.propose_target_plugin(
        "task-binding",
        plugin=plugin,
        task="Add a model-authored product search filter.",
    )
    return orchestrator, persisted, receipt


def _canonical_context_report() -> dict[str, Any]:
    return {
        "schema_version": 2,
        "canonical": True,
        "canonical_report_hash": "context-hash",
        "go_eligible": True,
        "verdict": "GO_ELIGIBLE",
    }


def test_target_plugin_recovery_input_identity_allows_only_context_lifecycle_refresh() -> None:
    plugin_identity = {
        "plugin_id": "lumacart",
        "selected_prompt_id": "coder-004-add-search-filter",
        "selected_context_id": "search-filter",
    }
    initial_context = {
        **_canonical_context_report(),
        "explicit_target": "index.html",
        "sources_considered": [
            {
                "source": "workspace",
                "considered": True,
                "status": "used",
                "reason": "selected",
                "required": True,
                "selected": True,
                "included": True,
                "packet": {"path": "index.html", "sha256": "a" * 64},
                "authority": {"owner": "source-proxy"},
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
                    "plan_id": "plan-primary",
                    "target": "index.html",
                    "context_slices": [{"path": "index.html", "sha256": "a" * 64}],
                },
                "authority": derived_architect_context_authority(),
            },
        ],
        "downstream_acknowledgements": {
            "coder": {"evidence": "primary", "acknowledged": True}
        },
    }
    refreshed_context = copy.deepcopy(initial_context)
    refreshed_context["canonical_report_hash"] = "refreshed-context-hash"
    refreshed_context["downstream_acknowledgements"]["coder"] = {
        "evidence": "authorized-fallback",
        "acknowledged": True,
    }
    refreshed_context["sources_considered"][1]["packet"]["plan_id"] = (
        "plan-fallback"
    )
    refreshed_context["sources_considered"][1]["packet"]["context_slices"][0][
        "sha256"
    ] = "b" * 64

    initial = orchestrator_module._target_plugin_model_input_sha256(
        task="Add a model-authored product search filter.",
        target_plugin_identity=plugin_identity,
        canonical_context=initial_context,
    )

    assert initial == orchestrator_module._target_plugin_model_input_sha256(
        task="Add a model-authored product search filter.",
        target_plugin_identity=plugin_identity,
        canonical_context=refreshed_context,
    )
    assert initial != orchestrator_module._target_plugin_model_input_sha256(
        task="Change an unrelated task.",
        target_plugin_identity=plugin_identity,
        canonical_context=refreshed_context,
    )
    changed_plugin = dict(plugin_identity)
    changed_plugin["selected_prompt_id"] = "coder-005-unrelated"
    assert initial != orchestrator_module._target_plugin_model_input_sha256(
        task="Add a model-authored product search filter.",
        target_plugin_identity=changed_plugin,
        canonical_context=refreshed_context,
    )
    changed_material = copy.deepcopy(refreshed_context)
    changed_material["sources_considered"][0]["packet"]["sha256"] = "b" * 64
    assert initial != orchestrator_module._target_plugin_model_input_sha256(
        task="Add a model-authored product search filter.",
        target_plugin_identity=plugin_identity,
        canonical_context=changed_material,
    )
    untrusted_derived_claim = copy.deepcopy(refreshed_context)
    untrusted_derived_claim["sources_considered"][1]["authority"] = {}
    assert initial != orchestrator_module._target_plugin_model_input_sha256(
        task="Add a model-authored product search filter.",
        target_plugin_identity=plugin_identity,
        canonical_context=untrusted_derived_claim,
    )


def _semantic_plan_payload(*, task_id: str, target: str) -> dict[str, Any]:
    old_sha256 = hashlib.sha256(b"old\n").hexdigest()
    return {
        "plan_id": f"plan-{task_id}",
        "task_id": task_id,
        "schema_version": 1,
        "created_at": "2026-07-21T00:00:00Z",
        "source_task": "Implement the requested behavior.",
        "bundle_snapshot": {
            "bundle_path": "repomix-output.xml",
            "bundle_sha256": "a" * 64,
            "workspace_root": "/tmp/test-workspace",
            "generated_at": "2026-07-21T00:00:00Z",
        },
        "classification": {
            "task_class": "fix",
            "visual_change": False,
            "designer_required": False,
            "estimated_complexity": "small",
        },
        "coder_packet": {
            "target_file": {
                "path": target,
                "exists": True,
                "sha256_before": old_sha256,
            },
            "operation": "edit",
            "acceptance_criteria": [
                {
                    "id": "requested_behavior",
                    "description": "The requested behavior is implemented.",
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
                    "path": target,
                    "kind": "target",
                    "sha256": old_sha256,
                    "content": "old\n",
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


def _prepare_generic_workspace(root: Path, target: str = "src/service.py") -> None:
    candidate = root / target
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text("old\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "fixture@example.invalid"],
        cwd=root,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Fixture"],
        cwd=root,
        check=True,
    )
    subprocess.run(["git", "add", target], cwd=root, check=True)
    subprocess.run(
        ["git", "commit", "-qm", "baseline"],
        cwd=root,
        check=True,
    )


def _generic_upstream_context(
    *,
    packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return build_context_broker_report(
        [
            {
                "source": "http-task-description",
                "considered": True,
                "status": "used",
                "reason": "task_text_bound_by_authenticated_request",
                "required": True,
                "selected": True,
                "included": True,
                "packet": dict(packet or {}),
            }
        ]
    )


def _generic_expanded_context(
    plan: ArchitectPlan,
    *,
    packet: dict[str, Any] | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    workspace_context, workspace_manifest = (
        _render_scoped_workspace_context(workspace_root, ("src/",))
        if workspace_root is not None
        else ("", [])
    )
    return _build_context_report(
        plan,
        allowed_paths=("src/",),
        scoped_workspace_context=workspace_context,
        scoped_workspace_context_manifest=workspace_manifest,
        existing={
            "sources_considered": [
                {
                    "source": "http-task-description",
                    "considered": True,
                    "status": "used",
                    "reason": "task_text_bound_by_authenticated_request",
                    "required": True,
                    "selected": True,
                    "included": True,
                    "packet": dict(packet or {}),
                }
            ]
        },
    )


def _seed_consumed_context_output(
    state: CodingLaneStateMachine,
    *,
    context_hash: str,
    target: str = "index.html",
) -> None:
    orchestrator = CodingOrchestrator()
    output = orchestrator._enforce_runtime_contract_output(
        state,
        lane_id="context-broker",
        producer_invocation_id="context-broker-test-producer",
        payload={"context_hash": context_hash, "verdict": "GO_ELIGIBLE"},
    )
    orchestrator._consume_output(
        state,
        output_id=output["output_id"],
        consumer_invocation_id="planner-test-consumer",
        payload={"consumer": "planner", "context_hash": context_hash},
    )
    orchestrator._enforce_runtime_contract_output(
        state,
        lane_id="planner",
        producer_invocation_id="planner-test-consumer",
        payload={
            "plan_id": f"plan-{state.task_id}",
            "task_spec": _semantic_plan_payload(
                task_id=state.task_id,
                target=target,
            ),
        },
    )


def test_generic_adapter_persists_exact_architect_plan_before_coder_invocation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    persisted: list[dict[str, object]] = []
    plan_store: dict[str, ArchitectPlan] = {}
    task_id = "task-generic-plan-bridge"
    target = "src/service.py"
    source_head = "a" * 40
    _prepare_generic_workspace(tmp_path, target)
    state = CodingLaneStateMachine(task_id=task_id, run_id="run-generic-plan-bridge")
    state.lane_states["context-broker"] = "running"
    bootstrap = CodingOrchestrator()
    context_output = bootstrap._enforce_runtime_contract_output(
        state,
        lane_id="context-broker",
        producer_invocation_id="context-bootstrap",
        payload={"context_hash": "context-hash", "verdict": "GO_ELIGIBLE"},
    )
    bootstrap._consume_output(
        state,
        output_id=context_output["output_id"],
        consumer_invocation_id="context-refresh-bootstrap",
        payload={"consumer": "context-broker", "context_hash": "context-hash"},
    )
    plugin = ResolvedTargetPlugin(
        schema_version="spiritos-target-plugin/v1",
        plugin_id=GENERIC_WORKSPACE_PLUGIN_ID,
        repository_id="repo",
        worktree_id="worktree",
        workspace_root=str(tmp_path),
        branch="test",
        state_namespace="namespace",
        fixture_root=".",
        source_head=source_head,
        selected_prompt_id=GENERIC_WORKSPACE_PROMPT_ID,
        selected_context_id=GENERIC_WORKSPACE_CONTEXT_ID,
        execution_profile=GENERIC_WORKSPACE_PROFILE,
        allowed_actions=("src/",),
        result_identity="result",
        readable_actions=("src/",),
    )
    plan = ArchitectPlan.from_dict(
        _semantic_plan_payload(task_id=task_id, target=target)
    )
    latest_context_report = _generic_upstream_context()

    def record_generic_context(
        _task_id: str,
        *,
        report: dict[str, Any],
        orchestrator_run_id: str,
    ) -> dict[str, Any]:
        nonlocal latest_context_report
        assert orchestrator_run_id == state.run_id
        latest_context_report = copy.deepcopy(report)
        return copy.deepcopy(latest_context_report)

    def acknowledge_generic_context(
        _task_id: str,
        *,
        consumer: str,
        evidence: str,
        applicable: bool,
        reason: str,
        **_kwargs: object,
    ) -> dict[str, Any]:
        nonlocal latest_context_report
        latest_context_report = acknowledge_context_consumer(
            latest_context_report,
            consumer=consumer,
            evidence=evidence,
            applicable=applicable,
            reason=reason,
        )
        return copy.deepcopy(latest_context_report)

    monkeypatch.setenv("SPIRITOS_CODING_PRIMARY_MODEL_ALIAS", "openai")
    monkeypatch.delenv("SPIRITOS_CODING_FALLBACK_MODEL_ALIAS", raising=False)
    monkeypatch.setattr(orchestrator_module, "current_head", lambda: source_head)
    monkeypatch.setattr(
        orchestrator_module,
        "acknowledge_task_context_consumer",
        acknowledge_generic_context,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_canonical_context_broker_for_task",
        record_generic_context,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "canonical_context_broker_for_task",
        lambda _task_id: copy.deepcopy(latest_context_report),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "load_plan",
        lambda requested: plan_store.get(requested),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "save_plan",
        lambda requested, value: plan_store.__setitem__(requested, value),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(copy.deepcopy(state)),
    )

    def execute_adapter(*_args: object, **kwargs: object) -> dict[str, Any]:
        before = persisted[-1] if persisted else state.receipt(summary="initial")
        assert before["lane_states"]["planner"] == "pending"
        assert not any(
            event.get("event_type") == "target_plugin_model_invocation"
            for event in before["causal_events"]
        )
        assert kwargs["architect_task_id"] == task_id
        callback = kwargs["plan_ready_callback"]
        assert callable(callback)
        planner_context = callback(
            plan,
            _generic_expanded_context(plan, workspace_root=tmp_path),
        )
        after_plan = persisted[-1]
        assert after_plan["lane_states"]["planner"] == "completed"
        assert not any(
            event.get("event_type") == "target_plugin_model_invocation"
            for event in after_plan["causal_events"]
        )
        coder_callback = kwargs["coder_ready_callback"]
        assert callable(coder_callback)
        bound_context = coder_callback(plan, planner_context, "1" * 64)
        after_coder = persisted[-1]
        assert any(
            event.get("event_type") == "target_plugin_model_invocation"
            for event in after_coder["causal_events"]
        )
        result = _canonical_target_plugin_result(
            target,
            plugin_id=GENERIC_WORKSPACE_PLUGIN_ID,
            selected_prompt_id=GENERIC_WORKSPACE_PROMPT_ID,
        )
        proposed_diff = str(result["proposed_diff"])
        result["coder_diagnostics"].update(
            {
                "architect_plan_id": plan.plan_id,
                "architect_plan_sha256": hashlib.sha256(
                    json.dumps(
                        plan.to_dict(),
                        sort_keys=True,
                        separators=(",", ":"),
                        default=str,
                    ).encode("utf-8")
                ).hexdigest(),
                "acceptance_criteria": [
                    {
                        "id": item.id,
                        "description": item.description,
                        "kind": item.kind,
                    }
                    for item in plan.coder_packet.acceptance_criteria
                ],
                "attempts": [
                    {
                        "proposed_diff_sha256": hashlib.sha256(
                            proposed_diff.encode("utf-8")
                        ).hexdigest(),
                        "preview_status": "ready_for_approval_preview",
                        "git_apply_check": {"passed": True},
                    }
                ],
                "canonical_context_broker": copy.deepcopy(bound_context),
                "canonical_context_report_hash": bound_context[
                    "canonical_report_hash"
                ],
                "rendered_prompt_sha256": "1" * 64,
                "coder_context_binding": {
                    "schema_version": "source-proxy-coder-context-binding/v1",
                    "call_index": 1,
                    "canonical_context_report_hash": bound_context[
                        "canonical_report_hash"
                    ],
                    "rendered_prompt_sha256": "1" * 64,
                    "selected_sources": list(bound_context["selected_sources"]),
                    "consumed_sources": list(bound_context["consumed_sources"]),
                    "consumed": True,
                },
            }
        )
        return result

    monkeypatch.setattr(
        orchestrator_module,
        "execute_target_plugin_command",
        execute_adapter,
    )
    orchestrator = CodingOrchestrator(
        planner_loader=lambda requested: plan_store.get(requested),
        state_loader=lambda _task_id: (
            persisted[-1] if persisted else state.receipt(summary="initial")
        ),
    )

    receipt = orchestrator.propose_target_plugin(
        task_id,
        plugin=plugin,
        task="Implement the requested service behavior.",
    )

    assert plan_store[task_id] == plan
    assert receipt["lane_states"]["planner"] == "completed"
    planner_output = next(
        item for item in receipt["runtime_outputs"] if item["lane_id"] == "planner"
    )
    assert planner_output["payload"]["task_spec"] == plan.to_dict()
    assert receipt["model_invocations"][0]["passed"] is True
    proposal = receipt["target_plugin_proposal"]
    assert proposal["canonical_context_report"] == latest_context_report
    assert proposal["context_hash"] == latest_context_report[
        "canonical_report_hash"
    ]
    invocation = next(
        event
        for event in receipt["causal_events"]
        if event["event_type"] == "target_plugin_model_invocation"
    )
    assert invocation["detail"]["canonical_context_report_hash"] == proposal[
        "context_hash"
    ]
    adapter_evidence = proposal["semantic_review_binding"][
        "preview_review_receipt"
    ]["adapter_preview_evidence"]
    assert adapter_evidence["canonical_context_report_hash"] == proposal[
        "context_hash"
    ]


def test_generic_adapter_refreshes_completed_planner_with_exact_attempt_plan(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    task_id = "task-generic-plan-refresh"
    target = "src/service.py"
    _prepare_generic_workspace(tmp_path, target)
    state = CodingLaneStateMachine(task_id=task_id, run_id="run-generic-plan-refresh")
    state.lane_states["context-broker"] = "completed"
    state.lane_states["planner"] = "completed"
    _seed_consumed_context_output(state, context_hash="context-hash", target=target)
    persisted = [state.receipt(summary="old plan completed")]
    saved: dict[str, ArchitectPlan] = {}
    fresh_payload = _semantic_plan_payload(task_id=task_id, target=target)
    fresh_payload["plan_id"] = "plan-fresh-adapter-attempt"
    fresh_payload["source_task"] = "Repair using current diagnostics."
    fresh_plan = ArchitectPlan.from_dict(fresh_payload)
    fresh_context = _generic_expanded_context(
        fresh_plan,
        workspace_root=tmp_path,
    )
    latest_context_report = _generic_upstream_context()

    def record_generic_context(
        _task_id: str,
        *,
        report: dict[str, Any],
        orchestrator_run_id: str,
    ) -> dict[str, Any]:
        nonlocal latest_context_report
        assert orchestrator_run_id == state.run_id
        latest_context_report = copy.deepcopy(report)
        return copy.deepcopy(latest_context_report)

    def acknowledge_generic_context(
        _task_id: str,
        *,
        consumer: str,
        evidence: str,
        applicable: bool,
        reason: str,
        **_kwargs: object,
    ) -> dict[str, Any]:
        nonlocal latest_context_report
        latest_context_report = acknowledge_context_consumer(
            latest_context_report,
            consumer=consumer,
            evidence=evidence,
            applicable=applicable,
            reason=reason,
        )
        return copy.deepcopy(latest_context_report)

    monkeypatch.setattr(
        orchestrator_module,
        "acknowledge_task_context_consumer",
        acknowledge_generic_context,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_canonical_context_broker_for_task",
        record_generic_context,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "canonical_context_broker_for_task",
        lambda _task_id: copy.deepcopy(latest_context_report),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "save_plan",
        lambda requested, value: saved.__setitem__(requested, value),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(copy.deepcopy(state)),
    )
    orchestrator = CodingOrchestrator(
        state_loader=lambda _task_id: copy.deepcopy(persisted[-1]),
    )

    receipt = orchestrator._persist_adapter_architect_plan(
        task_id,
        fresh_plan,
        context_report=fresh_context,
        readable_paths=("src/",),
        writable_paths=("src/",),
        workspace_root=tmp_path,
    )

    planner_outputs = [
        item for item in receipt["runtime_outputs"] if item["lane_id"] == "planner"
    ]
    assert len(planner_outputs) == 2
    assert planner_outputs[-1]["payload"]["task_spec"] == fresh_plan.to_dict()
    assert saved[task_id] == fresh_plan
    persisted_architect = next(
        item
        for item in latest_context_report["sources_considered"]
        if item["source"] == "architect_repository_context"
    )
    assert persisted_architect["packet"]["plan_id"] == fresh_plan.plan_id
    assert any(
        event["event_type"] == "generic_adapter_architect_plan_persisted"
        and event["detail"]["plan_id"] == fresh_plan.plan_id
        for event in receipt["causal_events"]
    )


@pytest.mark.parametrize("drift", ["drop", "change"])
def test_adapter_architect_context_rejects_upstream_material_drift(
    tmp_path: Path,
    drift: str,
) -> None:
    target = "src/service.py"
    task_id = "task-upstream-continuity"
    _prepare_generic_workspace(tmp_path, target)
    plan = ArchitectPlan.from_dict(
        _semantic_plan_payload(task_id=task_id, target=target)
    )
    previous = _generic_upstream_context(packet={"request": "original"})
    incoming = _generic_expanded_context(
        plan,
        packet={"request": "original"},
        workspace_root=tmp_path,
    )
    sources: list[dict[str, Any]] = []
    for raw in incoming["sources_considered"]:
        if drift == "drop" and raw["source"] == "http-task-description":
            continue
        source = copy.deepcopy(raw)
        source["consumed"] = source.get("consumed_claimed") is True
        if drift == "change" and source["source"] == "http-task-description":
            source["packet"] = {"request": "replacement"}
        sources.append(source)
    acknowledgements = copy.deepcopy(incoming["downstream_acknowledgements"])
    drifted = build_context_broker_report(
        sources,
        downstream_consumers=acknowledgements,
        applicable_consumers=("planner",),
    )
    architect_source = next(
        source
        for source in drifted["sources_considered"]
        if source["source"] == "architect_repository_context"
    )
    workspace_context = architect_source["packet"][
        "scoped_workspace_context"
    ]
    rendered_context = orchestrator_module._render_server_adapter_coder_context(
        plan,
        drifted,
        workspace_context,
    )
    architect_source["packet"].update(
        {
            "rendered_coder_context": rendered_context,
            "rendered_coder_context_sha256": hashlib.sha256(
                rendered_context.encode("utf-8")
            ).hexdigest(),
            "rendered_coder_context_char_count": len(rendered_context),
        }
    )
    rebuilt_sources = []
    for source in drifted["sources_considered"]:
        rebuilt_source = copy.deepcopy(source)
        rebuilt_source["consumed"] = (
            rebuilt_source.get("consumed_claimed") is True
        )
        rebuilt_sources.append(rebuilt_source)
    drifted = build_context_broker_report(
        rebuilt_sources,
        downstream_consumers=drifted["downstream_acknowledgements"],
        applicable_consumers=("planner",),
    )

    with pytest.raises(
        CodingOrchestratorError,
        match="target_plugin_upstream_context_material_changed",
    ):
        orchestrator_module._validate_adapter_architect_context_report(
            plan,
            drifted,
            previous_report=previous,
            expected_readable_paths=("src/",),
            expected_writable_paths=("src/",),
            workspace_root=tmp_path,
        )


def test_adapter_architect_context_rejects_packet_claimed_scope(
    tmp_path: Path,
) -> None:
    target = "src/service.py"
    _prepare_generic_workspace(tmp_path, target)
    plan = ArchitectPlan.from_dict(
        _semantic_plan_payload(task_id="task-scope-authority", target=target)
    )
    previous = _generic_upstream_context()
    incoming = _generic_expanded_context(plan, workspace_root=tmp_path)
    sources = copy.deepcopy(incoming["sources_considered"])
    for source in sources:
        source["consumed"] = source.get("consumed_claimed") is True
        if source["source"] == "architect_repository_context":
            source["packet"]["allowed_paths"] = ["../../"]
    drifted = build_context_broker_report(
        sources,
        downstream_consumers=incoming["downstream_acknowledgements"],
        applicable_consumers=("planner",),
    )

    with pytest.raises(
        CodingOrchestratorError,
        match="target_plugin_architect_context_plan_mismatch",
    ):
        orchestrator_module._validate_adapter_architect_context_report(
            plan,
            drifted,
            previous_report=previous,
            expected_readable_paths=("src/",),
            expected_writable_paths=("src/",),
            workspace_root=tmp_path,
        )


def test_generic_fallback_reuses_persisted_plan_before_replacement_coder(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    task_id = "task-generic-fallback-plan"
    target = "src/service.py"
    source_head = "a" * 40
    _prepare_generic_workspace(tmp_path, target)
    state = CodingLaneStateMachine(task_id=task_id, run_id="run-generic-fallback-plan")
    state.lane_states["context-broker"] = "running"
    bootstrap = CodingOrchestrator()
    context_output = bootstrap._enforce_runtime_contract_output(
        state,
        lane_id="context-broker",
        producer_invocation_id="context-bootstrap",
        payload={"context_hash": "context-hash", "verdict": "GO_ELIGIBLE"},
    )
    bootstrap._consume_output(
        state,
        output_id=context_output["output_id"],
        consumer_invocation_id="context-refresh-bootstrap",
        payload={"consumer": "context-broker", "context_hash": "context-hash"},
    )
    persisted: list[dict[str, Any]] = []
    plan_store: dict[str, ArchitectPlan] = {}
    plan_payload = _semantic_plan_payload(task_id=task_id, target=target)
    plan_payload["plan_id"] = "plan-primary"
    plan_payload["source_task"] = "Primary attempt plan."
    persisted_plan = ArchitectPlan.from_dict(plan_payload)
    plugin = ResolvedTargetPlugin(
        schema_version="spiritos-target-plugin/v1",
        plugin_id=GENERIC_WORKSPACE_PLUGIN_ID,
        repository_id="repo",
        worktree_id="worktree",
        workspace_root=str(tmp_path),
        branch="test",
        state_namespace="namespace",
        fixture_root=".",
        source_head=source_head,
        selected_prompt_id=GENERIC_WORKSPACE_PROMPT_ID,
        selected_context_id=GENERIC_WORKSPACE_CONTEXT_ID,
        execution_profile=GENERIC_WORKSPACE_PROFILE,
        allowed_actions=("src/",),
        result_identity="result",
        readable_actions=("src/",),
    )
    call_index = 0
    bound_contexts: list[dict[str, Any]] = []
    expanded_contexts: list[dict[str, Any]] = []

    def execute_adapter(*_args: object, **kwargs: object) -> dict[str, Any]:
        nonlocal call_index
        call_index += 1
        if call_index == 1:
            plan = persisted_plan
            callback = kwargs["plan_ready_callback"]
            assert callable(callback)
            assert kwargs.get("prevalidated_plan") is None
            workspace_context, workspace_manifest = (
                _render_scoped_workspace_context(tmp_path, ("src/",))
            )
            expanded_context = _build_context_report(
                plan,
                allowed_paths=("src/",),
                scoped_workspace_context=workspace_context,
                scoped_workspace_context_manifest=workspace_manifest,
                existing=kwargs["canonical_context"],
            )
            expanded_contexts.append(copy.deepcopy(expanded_context))
            planner_context = callback(plan, expanded_context)
            latest_after_plan = persisted[-1]
            assert len(
                [
                    event
                    for event in latest_after_plan["causal_events"]
                    if event["event_type"] == "target_plugin_model_invocation"
                ]
            ) == 0
        else:
            assert kwargs["plan_ready_callback"] is None
            plan = kwargs["prevalidated_plan"]
            assert isinstance(plan, ArchitectPlan)
            assert plan.to_dict() == persisted_plan.to_dict()
            planner_context = kwargs["canonical_context"]
        coder_callback = kwargs["coder_ready_callback"]
        assert callable(coder_callback)
        bound_context = coder_callback(plan, planner_context, "1" * 64)
        bound_contexts.append(copy.deepcopy(bound_context))
        latest = persisted[-1]
        assert [
            item["payload"]["task_spec"]["plan_id"]
            for item in latest["runtime_outputs"]
            if item["lane_id"] == "planner"
        ][-1] == plan.plan_id
        assert len(
            [
                event
                for event in latest["causal_events"]
                if event["event_type"] == "target_plugin_model_invocation"
            ]
        ) == call_index
        if call_index == 1:
            return {
                "proposed_diff": "",
                "coder_blocked": True,
                "reason_code": "coder_model_timeout",
                "blocked_reason": "primary provider timed out",
                "coder_diagnostics": {
                    "provider_call_made": True,
                    "selected_model_alias": "primary",
                    "provider": "primary-provider",
                    "model": "primary-model",
                    "changed_files": [],
                },
            }
        result = _canonical_target_plugin_result(
            target,
            plugin_id=GENERIC_WORKSPACE_PLUGIN_ID,
            selected_prompt_id=GENERIC_WORKSPACE_PROMPT_ID,
        )
        proposed_diff = str(result["proposed_diff"])
        result["coder_diagnostics"].update(
            {
                "architect_plan_id": plan.plan_id,
                "architect_plan_sha256": hashlib.sha256(
                    json.dumps(
                        plan.to_dict(),
                        sort_keys=True,
                        separators=(",", ":"),
                        default=str,
                    ).encode("utf-8")
                ).hexdigest(),
                "acceptance_criteria": [
                    {
                        "id": item.id,
                        "description": item.description,
                        "kind": item.kind,
                    }
                    for item in plan.coder_packet.acceptance_criteria
                ],
                "attempts": [
                    {
                        "proposed_diff_sha256": hashlib.sha256(
                            proposed_diff.encode("utf-8")
                        ).hexdigest(),
                        "preview_status": "ready_for_approval_preview",
                        "git_apply_check": {"passed": True},
                    }
                ],
                "canonical_context_broker": copy.deepcopy(bound_context),
                "canonical_context_report_hash": bound_context[
                    "canonical_report_hash"
                ],
                "rendered_prompt_sha256": "1" * 64,
                "coder_context_binding": {
                    "schema_version": "source-proxy-coder-context-binding/v1",
                    "call_index": 1,
                    "canonical_context_report_hash": bound_context[
                        "canonical_report_hash"
                    ],
                    "rendered_prompt_sha256": "1" * 64,
                    "selected_sources": list(bound_context["selected_sources"]),
                    "consumed_sources": list(bound_context["consumed_sources"]),
                    "consumed": True,
                },
            }
        )
        return result

    monkeypatch.setenv("SPIRITOS_CODING_PRIMARY_MODEL_ALIAS", "primary")
    monkeypatch.setenv("SPIRITOS_CODING_FALLBACK_MODEL_ALIAS", "openai")
    monkeypatch.setattr(orchestrator_module, "current_head", lambda: source_head)
    latest_context_report = _generic_upstream_context(
        packet={"request_sha256": "3" * 64}
    )

    def record_generic_context(
        _task_id: str,
        *,
        report: dict[str, Any],
        orchestrator_run_id: str,
    ) -> dict[str, Any]:
        nonlocal latest_context_report
        assert orchestrator_run_id == state.run_id
        latest_context_report = copy.deepcopy(report)
        return copy.deepcopy(latest_context_report)

    def acknowledge_generic_context(
        *_args: object,
        consumer: str,
        evidence: str,
        applicable: bool,
        reason: str,
        **_kwargs: object,
    ) -> dict[str, Any]:
        nonlocal latest_context_report
        latest_context_report = acknowledge_context_consumer(
            latest_context_report,
            consumer=consumer,
            evidence=evidence,
            applicable=applicable,
            reason=reason,
        )
        return copy.deepcopy(latest_context_report)

    monkeypatch.setattr(
        orchestrator_module,
        "acknowledge_task_context_consumer",
        acknowledge_generic_context,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_canonical_context_broker_for_task",
        record_generic_context,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "canonical_context_broker_for_task",
        lambda _task_id: copy.deepcopy(latest_context_report),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "load_plan",
        lambda requested: plan_store.get(requested),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "save_plan",
        lambda requested, value: plan_store.__setitem__(requested, value),
    )
    monkeypatch.setattr(orchestrator_module, "execute_target_plugin_command", execute_adapter)
    monkeypatch.setattr(
        orchestrator_module,
        "route_provider_for_alias",
        lambda alias: "openai" if alias == "openai" else "primary-provider",
    )
    monkeypatch.setattr(
        orchestrator_module,
        "route_model_for_alias",
        lambda alias: "openai/test-coder" if alias == "openai" else "primary-model",
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(copy.deepcopy(state)),
    )
    orchestrator = CodingOrchestrator(
        planner_loader=lambda requested: plan_store.get(requested),
        state_loader=lambda _task_id: (
            copy.deepcopy(persisted[-1])
            if persisted
            else state.receipt(summary="initial")
        ),
    )

    receipt = orchestrator.propose_target_plugin(
        task_id,
        plugin=plugin,
        task="Implement the requested service behavior.",
    )

    planner_plan_ids = [
        item["payload"]["task_spec"]["plan_id"]
        for item in receipt["runtime_outputs"]
        if item["lane_id"] == "planner"
    ]
    assert planner_plan_ids == ["plan-primary"]
    assert len(receipt["model_invocations"]) == 2
    assert len(bound_contexts) == 2
    assert bound_contexts[0]["canonical_report_hash"] != bound_contexts[1][
        "canonical_report_hash"
    ]
    proposal = receipt["target_plugin_proposal"]
    assert proposal["context_hash"] == bound_contexts[-1][
        "canonical_report_hash"
    ]
    assert proposal["canonical_context_report"] == bound_contexts[-1]
    assert latest_context_report == bound_contexts[-1]
    primary_http_packet = next(
        item["packet"]
        for item in expanded_contexts[0]["sources_considered"]
        if item["source"] == "http-task-description"
    )
    assert primary_http_packet["schema_version"] == (
        "source-proxy-bounded-context-packet/v1"
    )
    assert len(expanded_contexts) == 1
    adapter_evidence = proposal["semantic_review_binding"][
        "preview_review_receipt"
    ]["adapter_preview_evidence"]
    assert adapter_evidence["architect_plan_id"] == "plan-primary"
    material = orchestrator.target_plugin_approval_material(
        task_id,
        runtime_output_id=proposal["runtime_output_id"],
        selected_prompt_id=proposal["selected_prompt_id"],
    )
    assert material["proposal_binding"] == proposal


def test_generic_fallback_pre_plan_block_preserves_reason_and_sanitized_provenance(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    task_id = "task-generic-fallback-pre-plan-block"
    target = "src/service.py"
    source_head = "a" * 40
    _prepare_generic_workspace(tmp_path, target)
    state = CodingLaneStateMachine(
        task_id=task_id,
        run_id="run-generic-fallback-pre-plan-block",
    )
    state.lane_states["context-broker"] = "running"
    bootstrap = CodingOrchestrator()
    context_output = bootstrap._enforce_runtime_contract_output(
        state,
        lane_id="context-broker",
        producer_invocation_id="context-bootstrap",
        payload={"context_hash": "context-hash", "verdict": "GO_ELIGIBLE"},
    )
    bootstrap._consume_output(
        state,
        output_id=context_output["output_id"],
        consumer_invocation_id="context-refresh-bootstrap",
        payload={"consumer": "context-broker", "context_hash": "context-hash"},
    )
    persisted: list[dict[str, Any]] = []
    plan_store: dict[str, ArchitectPlan] = {}
    primary_plan = ArchitectPlan.from_dict(
        _semantic_plan_payload(task_id=task_id, target=target)
    )
    plugin = ResolvedTargetPlugin(
        schema_version="spiritos-target-plugin/v1",
        plugin_id=GENERIC_WORKSPACE_PLUGIN_ID,
        repository_id="repo",
        worktree_id="worktree",
        workspace_root=str(tmp_path),
        branch="test",
        state_namespace="namespace",
        fixture_root=".",
        source_head=source_head,
        selected_prompt_id=GENERIC_WORKSPACE_PROMPT_ID,
        selected_context_id=GENERIC_WORKSPACE_CONTEXT_ID,
        execution_profile=GENERIC_WORKSPACE_PROFILE,
        allowed_actions=("src/",),
        result_identity="result",
        readable_actions=("src/",),
    )
    fallback_provenance = {
        "schema_version": "spiritos-target-adapter-provenance/v1",
        "transport_kind": "canonical_litellm_router",
        "provider_call_made": True,
        "sensitive_detail": "must-not-be-persisted-verbatim",
        "calls": [
            {"stage": "architect", "completed": True, "raw": "private-plan"},
            {"stage": "architect-repair", "completed": False, "raw": "private-repair"},
        ],
    }
    latest_context_report = _generic_upstream_context(
        packet={"request_sha256": "3" * 64}
    )

    def record_generic_context(
        _task_id: str,
        *,
        report: dict[str, Any],
        orchestrator_run_id: str,
    ) -> dict[str, Any]:
        nonlocal latest_context_report
        assert orchestrator_run_id == state.run_id
        latest_context_report = copy.deepcopy(report)
        return copy.deepcopy(latest_context_report)

    def acknowledge_generic_context(
        *_args: object,
        consumer: str,
        evidence: str,
        applicable: bool,
        reason: str,
        **_kwargs: object,
    ) -> dict[str, Any]:
        nonlocal latest_context_report
        latest_context_report = acknowledge_context_consumer(
            latest_context_report,
            consumer=consumer,
            evidence=evidence,
            applicable=applicable,
            reason=reason,
        )
        return copy.deepcopy(latest_context_report)

    call_count = 0

    def execute_adapter(*_args: object, **kwargs: object) -> dict[str, Any]:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            plan_callback = kwargs["plan_ready_callback"]
            coder_callback = kwargs["coder_ready_callback"]
            assert callable(plan_callback)
            assert callable(coder_callback)
            planner_context = plan_callback(
                primary_plan,
                _generic_expanded_context(
                    primary_plan,
                    packet={"request_sha256": "3" * 64},
                    workspace_root=tmp_path,
                ),
            )
            coder_callback(primary_plan, planner_context, "1" * 64)
            return {
                "proposed_diff": "",
                "coder_blocked": True,
                "reason_code": "coder_model_timeout",
                "blocked_reason": "primary provider timed out",
                "coder_diagnostics": {
                    "provider_call_made": True,
                    "selected_model_alias": "primary",
                    "provider": "primary-provider",
                    "model": "primary-model",
                    "changed_files": [],
                },
            }
        assert kwargs["plan_ready_callback"] is None
        assert callable(kwargs["coder_ready_callback"])
        reused_plan = kwargs["prevalidated_plan"]
        assert isinstance(reused_plan, ArchitectPlan)
        assert reused_plan.to_dict() == primary_plan.to_dict()
        return {
            "proposed_diff": "",
            "coder_blocked": True,
            "reason_code": "fallback_architect_output_invalid",
            "blocked_reason": "fallback architect response could not be parsed",
            "target_adapter_provenance": copy.deepcopy(fallback_provenance),
            "coder_diagnostics": {
                "provider_call_made": False,
                "changed_files": [],
            },
        }

    monkeypatch.setenv("SPIRITOS_CODING_PRIMARY_MODEL_ALIAS", "primary")
    monkeypatch.setenv("SPIRITOS_CODING_FALLBACK_MODEL_ALIAS", "fallback")
    monkeypatch.setattr(orchestrator_module, "current_head", lambda: source_head)
    monkeypatch.setattr(
        orchestrator_module,
        "acknowledge_task_context_consumer",
        acknowledge_generic_context,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_canonical_context_broker_for_task",
        record_generic_context,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "canonical_context_broker_for_task",
        lambda _task_id: copy.deepcopy(latest_context_report),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "load_plan",
        lambda requested: plan_store.get(requested),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "save_plan",
        lambda requested, value: plan_store.__setitem__(requested, value),
    )
    monkeypatch.setattr(orchestrator_module, "execute_target_plugin_command", execute_adapter)
    monkeypatch.setattr(
        orchestrator_module,
        "route_provider_for_alias",
        lambda alias: f"{alias}-provider",
    )
    monkeypatch.setattr(
        orchestrator_module,
        "route_model_for_alias",
        lambda alias: f"{alias}-model",
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(copy.deepcopy(state)),
    )
    orchestrator = CodingOrchestrator(
        planner_loader=lambda requested: plan_store.get(requested),
        state_loader=lambda _task_id: (
            copy.deepcopy(persisted[-1])
            if persisted
            else state.receipt(summary="initial")
        ),
    )

    with pytest.raises(
        CodingOrchestratorError,
        match="fallback_architect_output_invalid",
    ):
        orchestrator.propose_target_plugin(
            task_id,
            plugin=plugin,
            task="Implement the requested service behavior.",
        )

    receipt = persisted[-1]
    blocked_event = next(
        event
        for event in receipt["causal_events"]
        if event["event_type"] == "target_plugin_fallback_pre_plan_blocked"
    )
    detail = blocked_event["detail"]
    assert detail["reason_code"] == "fallback_architect_output_invalid"
    assert detail["target_adapter_provenance_sha256"] == (
        orchestrator_module._sha256_json(fallback_provenance)
    )
    assert detail["target_adapter_model_call_count"] == 2
    assert detail["target_adapter_model_call_stages"] == [
        "architect",
        "architect-repair",
    ]
    assert detail["target_adapter_completed_model_call_count"] == 1
    assert "calls" not in detail
    assert "must-not-be-persisted-verbatim" not in json.dumps(detail, sort_keys=True)
    assert len(receipt["model_invocations"]) == 1
    invocation_events = [
        event
        for event in receipt["causal_events"]
        if event["event_type"] == "target_plugin_model_invocation"
    ]
    assert len(invocation_events) == 1
    assert "recovery_id" not in invocation_events[0]["detail"]
    assert [
        item["payload"]["task_spec"]["plan_id"]
        for item in receipt["runtime_outputs"]
        if item["lane_id"] == "planner"
    ] == [primary_plan.plan_id]


def test_target_plugin_recovery_integrity_error_persists_fallback_participant_and_event(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    task_id = "task-recovery-integrity-rejected"
    target = "tests/ui-agent-trials/fixtures/dummy-product-site/index.html"
    source_head = "a" * 40
    state = CodingLaneStateMachine(
        task_id=task_id,
        run_id="run-recovery-integrity-rejected",
    )
    state.lane_states["context-broker"] = "completed"
    state.lane_states["planner"] = "completed"
    _seed_consumed_context_output(
        state,
        context_hash="planner-context-hash",
        target=target,
    )
    plugin = ResolvedTargetPlugin(
        schema_version="spiritos-target-plugin/v1",
        plugin_id="lumacart",
        repository_id="repo",
        worktree_id="worktree",
        workspace_root=str(tmp_path),
        branch="test",
        state_namespace="namespace",
        fixture_root="tests/ui-agent-trials/fixtures/dummy-product-site/",
        source_head=source_head,
        selected_prompt_id="coder-004-add-search-filter",
        selected_context_id="search-filter",
        execution_profile="coder-10",
        allowed_actions=("propose_diff",),
        result_identity="result",
    )
    copied_result = {
        "proposed_diff": "",
        "coder_blocked": True,
        "reason_code": "coder_model_timeout",
        "blocked_reason": "model call timed out",
        "coder_diagnostics": {
            "provider_call_made": True,
            "changed_files": [],
        },
    }
    primary_result = copy.deepcopy(copied_result)
    primary_result["coder_diagnostics"].update(
        {
            "selected_model_alias": "primary",
            "provider": "primary-provider",
            "model": "primary-model",
        }
    )
    fallback_result = copy.deepcopy(copied_result)
    fallback_result["coder_diagnostics"].update(
        {
            "selected_model_alias": "fallback",
            "provider": "fallback-provider",
            "model": "fallback-model",
        }
    )
    results = iter([primary_result, fallback_result])
    persisted: list[dict[str, Any]] = []
    latest_context_report = _canonical_context_report()
    acknowledgement_count = 0

    def acknowledge_context(*_args: object, **_kwargs: object) -> dict[str, Any]:
        nonlocal acknowledgement_count, latest_context_report
        acknowledgement_count += 1
        latest_context_report = _canonical_context_report()
        latest_context_report["canonical_report_hash"] = (
            f"context-hash-{acknowledgement_count}"
        )
        return copy.deepcopy(latest_context_report)

    monkeypatch.setenv("SPIRITOS_CODING_PRIMARY_MODEL_ALIAS", "primary")
    monkeypatch.setenv("SPIRITOS_CODING_FALLBACK_MODEL_ALIAS", "fallback")
    monkeypatch.setattr(orchestrator_module, "current_head", lambda: source_head)
    monkeypatch.setattr(
        orchestrator_module,
        "acknowledge_task_context_consumer",
        acknowledge_context,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "canonical_context_broker_for_task",
        lambda _task_id: copy.deepcopy(latest_context_report),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "execute_target_plugin_command",
        lambda *_args, **_kwargs: next(results),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "route_provider_for_alias",
        lambda _alias: "fallback-provider",
    )
    monkeypatch.setattr(
        orchestrator_module,
        "route_model_for_alias",
        lambda _alias: "fallback-model",
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(copy.deepcopy(state)),
    )
    orchestrator = CodingOrchestrator(
        state_loader=lambda _task_id: (
            copy.deepcopy(persisted[-1])
            if persisted
            else state.receipt(summary="initial")
        ),
    )

    with pytest.raises(
        CodingOrchestratorError,
        match="recovery_replacement_output_copied",
    ) as caught:
        orchestrator.propose_target_plugin(
            task_id,
            plugin=plugin,
            task="Add a model-authored product search filter.",
        )

    assert isinstance(caught.value.__cause__, orchestrator_module.ControlledRecoveryError)
    receipt = persisted[-1]
    assert len(receipt["model_invocations"]) == 2
    primary_participant, fallback_participant = receipt["model_invocations"]
    assert fallback_participant["attempt_id"] != primary_participant["attempt_id"]
    assert fallback_participant["invocation_id"] != primary_participant["invocation_id"]
    assert fallback_participant["output_sha256"] == primary_participant["output_sha256"]
    rejected_event = next(
        event
        for event in receipt["causal_events"]
        if event["event_type"] == "target_plugin_recovery_integrity_rejected"
    )
    assert rejected_event["detail"]["invocation_id"] == fallback_participant[
        "invocation_id"
    ]
    assert rejected_event["detail"]["reason_code"] == (
        "recovery_replacement_output_copied"
    )
    assert rejected_event["detail"]["recovery_id"] == receipt[
        "recovery_lineage"
    ][0]["recovery_id"]


def test_canonical_target_plugin_proposal_binds_adapter_model_and_runtime_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    orchestrator, _persisted, receipt = _propose_canonical_target_plugin(
        monkeypatch,
        tmp_path,
    )
    proposal = receipt["target_plugin_proposal"]
    participant = receipt["model_invocations"][0]

    assert proposal["target_adapter_provenance"]["terminal_proof_eligible"] is True
    assert proposal["producer_model_alias"] == "openai"
    assert proposal["producer_model_provider"] == participant["provider"] == "openai"
    assert proposal["producer_model_name"] == participant["model"] == "openai/test-coder"
    assert proposal["producer_adapter_call_index"] == 1
    assert proposal["source_head"] == "a" * 40
    assert proposal["target_source_head"] == "b" * 40
    assert (
        proposal["model_output_provenance"]["target_adapter_provenance"]
        == proposal["target_adapter_provenance"]
    )
    assert (
        orchestrator_module._sha256_json(proposal["model_output_provenance"])
        == participant["output_sha256"]
        == proposal["producer_model_output_sha256"]
    )
    semantic = proposal["semantic_review_binding"]
    assert semantic["acceptance_criteria"][0]["id"] == "requested_behavior"
    assert semantic["preview_review_receipt"]["status"] == "passed"
    assert semantic["preview_review_receipt"]["proposed_diff_sha256"] == proposal[
        "approved_diff_sha256"
    ]
    assert semantic["semantic_review_binding_sha256"] == proposal[
        "semantic_review_binding_sha256"
    ]
    material = orchestrator.target_plugin_approval_material(
        "task-binding",
        runtime_output_id=proposal["runtime_output_id"],
        selected_prompt_id=proposal["selected_prompt_id"],
    )
    assert material["proposal_binding"] == proposal
    assert (
        material["target_plugin_identity"]
        == material["proposal_binding"]["target_plugin_identity"]
        == proposal["target_plugin_identity"]
    )
    assert material["approved_diff"]


def test_resealed_target_plugin_proposal_cannot_replace_consumed_context(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _orchestrator, _persisted, receipt = _propose_canonical_target_plugin(
        monkeypatch,
        tmp_path,
    )
    tampered = copy.deepcopy(receipt)
    proposal = tampered["target_plugin_proposal"]
    proposal["canonical_context_report"]["verdict"] = "TAMPERED"
    proposal["canonical_context_report_sha256"] = orchestrator_module._sha256_json(
        proposal["canonical_context_report"]
    )
    body = dict(proposal)
    body.pop("proposal_binding_sha256", None)
    proposal["proposal_binding_sha256"] = orchestrator_module._sha256_json(body)
    orchestrator = CodingOrchestrator(state_loader=lambda _task_id: tampered)

    with pytest.raises(
        CodingOrchestratorError,
        match="target_plugin_proposal_context_binding_invalid",
    ):
        orchestrator.target_plugin_approval_material(
            "task-binding",
            runtime_output_id=proposal["runtime_output_id"],
            selected_prompt_id=proposal["selected_prompt_id"],
        )


@pytest.mark.parametrize("tamper_scope", ["top_level_only", "nested_and_top_level"])
def test_resealed_target_plugin_proposal_cannot_break_model_provenance_binding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    tamper_scope: str,
) -> None:
    _orchestrator, _persisted, receipt = _propose_canonical_target_plugin(
        monkeypatch,
        tmp_path,
    )
    tampered = copy.deepcopy(receipt)
    proposal = tampered["target_plugin_proposal"]
    proposal["target_adapter_provenance"]["raw_response_sha256"] = "f" * 64
    if tamper_scope == "nested_and_top_level":
        proposal["model_output_provenance"]["target_adapter_provenance"][
            "raw_response_sha256"
        ] = "f" * 64
    body = dict(proposal)
    body.pop("proposal_binding_sha256", None)
    proposal["proposal_binding_sha256"] = orchestrator_module._sha256_json(body)
    orchestrator = CodingOrchestrator(state_loader=lambda _task_id: tampered)

    with pytest.raises(
        CodingOrchestratorError,
        match="target_plugin_proposal_model_provenance_invalid",
    ):
        orchestrator.target_plugin_approval_material(
            "task-binding",
            runtime_output_id=proposal["runtime_output_id"],
            selected_prompt_id=proposal["selected_prompt_id"],
        )


def _repair_test_artifact(
    *,
    task_id: str,
    run_id: str,
    approval_id: str,
    workspace_root: Path,
    target_plugin_identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    diff = "diff --git a/index.html b/index.html\n--- a/index.html\n+++ b/index.html\n"
    workspace_root.mkdir(parents=True, exist_ok=True)
    current = workspace_root / "index.html"
    current.write_text("current applied state\n", encoding="utf-8")
    current_sha256 = orchestrator_module.hashlib.sha256(current.read_bytes()).hexdigest()
    return {
        "schema_version": "coding.immutable-applied-artifact/v2",
        "task_id": task_id,
        "run_id": run_id,
        "approval_id": approval_id,
        "generation": 1,
        "approved_diff_sha256": orchestrator_module.hashlib.sha256(
            diff.encode("utf-8")
        ).hexdigest(),
        "result_sha256": "sha256:" + "4" * 64,
        "workspace_root": str(workspace_root.resolve()),
        "changed_files": [
            {
                "path": "index.html",
                "sha256_before": "1" * 64,
                "sha256_after": current_sha256,
                "missing_before_apply": False,
            }
        ],
        "target_plugin_identity": copy.deepcopy(target_plugin_identity or {}),
        "artifact_sha256": "sha256:" + "3" * 64,
    }


def _invalidated_attempt_finalizer(
    *,
    approval_id: str,
    generation: int = 1,
) -> Any:
    def finalize(task_id: str, *, reason_code: str, participant_records: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "task": {
                "id": task_id,
                "ast_snapshot": {
                    "campaign_2_approval": {
                        "approval_id": approval_id,
                        "generation": generation,
                        "state": "invalidated",
                        "failure_reason": reason_code,
                        "participant_records": copy.deepcopy(participant_records),
                    }
                },
            }
        }

    return finalize


def _repair_ready_state(
    *,
    task_id: str,
    run_id: str,
    target: str = "index.html",
) -> CodingLaneStateMachine:
    state = CodingLaneStateMachine(task_id=task_id, run_id=run_id)
    state.lane_states["context-broker"] = "completed"
    state.lane_states["planner"] = "completed"
    boundary_owner = CodingOrchestrator()
    context_output = boundary_owner._enforce_runtime_contract_output(
        state,
        lane_id="context-broker",
        producer_invocation_id="repair-context-producer",
        payload={"context_hash": "context-hash", "verdict": "GO_ELIGIBLE"},
    )
    boundary_owner._consume_output(
        state,
        output_id=context_output["output_id"],
        consumer_invocation_id="repair-planner-invocation",
        payload={"consumer": "planner", "context_hash": "context-hash"},
    )
    boundary_owner._enforce_runtime_contract_output(
        state,
        lane_id="planner",
        producer_invocation_id="repair-planner-invocation",
        payload={
            "plan_id": f"plan-{task_id}",
            "task_spec": _semantic_plan_payload(task_id=task_id, target=target),
        },
    )
    return state


def test_reviewer_failure_seals_attempt_and_reenters_coder_with_exact_current_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    task_id = "task-reviewer-repair"
    run_id = "run-reviewer-repair"
    original_attempt_id = "coding-attempt-original"
    original_approval_id = "approval-original"
    repair_target = "tests/ui-agent-trials/fixtures/dummy-product-site/index.html"
    state = _repair_ready_state(
        task_id=task_id,
        run_id=run_id,
        target=repair_target,
    )
    state.attempt_id = original_attempt_id
    persisted: list[dict[str, Any]] = []
    approved_diff = "diff --git a/index.html b/index.html\n--- a/index.html\n+++ b/index.html\n"
    source_head = "a" * 40
    plugin = ResolvedTargetPlugin(
        schema_version="spiritos-target-plugin/v1",
        plugin_id="lumacart",
        repository_id="repo",
        worktree_id="worktree",
        workspace_root=str(tmp_path.resolve()),
        branch="test",
        state_namespace="namespace",
        fixture_root="tests/ui-agent-trials/fixtures/dummy-product-site/",
        source_head=source_head,
        selected_prompt_id="coder-004-add-search-filter",
        selected_context_id="search-filter",
        execution_profile="coder-10",
        allowed_actions=("propose_diff",),
        result_identity="result",
    )
    artifact = _repair_test_artifact(
        task_id=task_id,
        run_id=run_id,
        approval_id=original_approval_id,
        workspace_root=tmp_path,
        target_plugin_identity=plugin.evidence_identity(),
    )
    executor_record = {
        "role": "coding-executor",
        "invocation_id": "executor-original",
        "output_id": "executor-original-output",
        "passed": True,
    }
    reviewer_record = {
        "role": "coding-reviewer",
        "invocation_id": "reviewer-original",
        "output_id": "reviewer-original-output",
        "passed": False,
        "result": {
            "passed": False,
            "findings": ["fix the exact response/status mismatch"],
        },
    }
    canonical_report = _canonical_context_report()
    monkeypatch.setattr(
        orchestrator_module,
        "acknowledge_task_context_consumer",
        lambda *_args, **_kwargs: copy.deepcopy(canonical_report),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "canonical_context_broker_for_task",
        lambda _task_id: copy.deepcopy(canonical_report),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(copy.deepcopy(state)),
    )
    orchestrator = CodingOrchestrator(
        executor=lambda _task_id, **_kwargs: {
            "execution": {
                "generation": 1,
                "changed_files": ["index.html"],
                "artifact": copy.deepcopy(artifact),
                "executor_participant": copy.deepcopy(executor_record),
            }
        },
        reviewer=lambda _artifact: copy.deepcopy(reviewer_record),
        state_loader=lambda _task_id: (
            copy.deepcopy(persisted[-1])
            if persisted
            else state.receipt(summary="repair ready")
        ),
        planner_loader=lambda requested: ArchitectPlan.from_dict(
            _semantic_plan_payload(task_id=requested, target=repair_target)
        ),
        attempt_failure_finalizer=_invalidated_attempt_finalizer(
            approval_id=original_approval_id
        ),
    )
    monkeypatch.setattr(
        orchestrator,
        "_append_participant",
        lambda run, record: run.participant_records.append(copy.deepcopy(dict(record))),
    )

    with pytest.raises(
        CodingOrchestratorError,
        match="independent_review_failed_repair_required",
    ):
        orchestrator.execute_approved(
            task_id,
            approved_diff=approved_diff,
            action="apply",
            approval_id=original_approval_id,
            selected_prompt_id="coder-001-generic-lab-trial",
            context_hash="context-hash",
        )

    sealed_state = next(
        item for item in persisted if item["attempt_id"] == original_attempt_id and item["attempt_history"]
    )
    repair_state = persisted[-1]
    seal = repair_state["attempt_history"][0]
    unsigned_seal = dict(seal)
    recorded_seal_hash = unsigned_seal.pop("seal_sha256")
    assert orchestrator_module._sha256_json(unsigned_seal) == recorded_seal_hash
    assert sealed_state["attempt_history"][0] == seal
    assert repair_state["run_id"] == run_id
    assert repair_state["attempt_id"] != original_attempt_id
    assert repair_state["parent_attempt_id"] == original_attempt_id
    assert repair_state["attempt_number"] == 2
    assert repair_state["attempt_dispositions"][0]["authority_state"] == "invalidated"
    assert repair_state["immutable_artifact"] is None
    assert repair_state["target_plugin_proposal"] is None
    assert repair_state["participant_records"] == []
    assert repair_state["repair_request"]["exact_feedback"]["findings"] == [
        "fix the exact response/status mismatch"
    ]
    diagnostic = seal["repair_diagnostic"]
    assert diagnostic["hook"] == "deterministic_failure_classifier"
    assert diagnostic["model_debugger_invoked"] is False
    assert diagnostic["deterministic_debugger_invoked"] is False
    assert diagnostic["debugger_trace"] is None
    assert diagnostic["classification"]["failure_kind"] == "reviewer_rejection"
    assert diagnostic["exact_failure_output"] == seal["failure"]["exact_feedback"]
    assert repair_state["repair_request"]["repair_diagnostic"] == diagnostic
    assert repair_state["repair_request"]["repair_diagnostic_sha256"] == diagnostic[
        "diagnostic_sha256"
    ]
    assert any(
        event["event_type"] == "deterministic_repair_diagnostic_recorded"
        and event["detail"]["diagnostic_sha256"] == diagnostic["diagnostic_sha256"]
        for event in seal["attempt_state"]["causal_events"]
    )
    current_manifest = repair_state["repair_request"]["current_state_manifest"]
    assert current_manifest["artifact_sha256"] == artifact["artifact_sha256"]
    assert current_manifest["changed_files"][0]["current_sha256"] == artifact[
        "changed_files"
    ][0]["sha256_after"]
    target = repair_target
    monkeypatch.setattr(orchestrator_module, "current_head", lambda: source_head)
    current_file = tmp_path / "index.html"
    original_bytes = current_file.read_bytes()
    current_file.write_text("unrecorded drift\n", encoding="utf-8")
    with pytest.raises(CodingOrchestratorError, match="repair_current_state_changed"):
        orchestrator.propose_target_plugin(
            task_id,
            plugin=plugin,
            task="Repair the backend behavior.",
        )
    current_file.write_bytes(original_bytes)
    with pytest.raises(
        CodingOrchestratorError,
        match="repair_target_plugin_identity_changed",
    ):
        orchestrator.propose_target_plugin(
            task_id,
            plugin=replace(plugin, repository_id="substituted-repository"),
            task="Repair the backend behavior.",
        )
    dispatched_tasks: list[str] = []
    dispatched_aliases: list[str | None] = []
    monkeypatch.setenv("SPIRITOS_CODING_PRIMARY_MODEL_ALIAS", "openai")
    monkeypatch.setenv("SOURCE_PROXY_CODER_REPAIR_MODEL_ALIAS", "local")
    monkeypatch.delenv("SPIRITOS_CODING_FALLBACK_MODEL_ALIAS", raising=False)
    monkeypatch.setattr(
        orchestrator_module,
        "execute_target_plugin_command",
        lambda _plugin, *, task, model_alias=None, **_kwargs: (
            dispatched_tasks.append(task),
            dispatched_aliases.append(model_alias),
            _canonical_target_plugin_result(target),
        )[-1],
    )

    proposal_receipt = orchestrator.propose_target_plugin(
        task_id,
        plugin=plugin,
        task="Repair the backend behavior.",
    )
    proposal = proposal_receipt["target_plugin_proposal"]
    assert dispatched_tasks and "fix the exact response/status mismatch" in dispatched_tasks[0]
    assert dispatched_aliases == ["local"]
    assert artifact["artifact_sha256"] in dispatched_tasks[0]
    assert proposal["attempt_id"] == repair_state["attempt_id"]
    assert proposal["repair_context"] == repair_state["repair_request"]
    assert proposal["repair_strategy_signature"].startswith("sha256:")
    assert proposal_receipt["model_invocations"][0]["role"] == "target-plugin-model"
    assert proposal_receipt["model_invocations"][0]["provider"] == "openai"
    assert proposal_receipt["model_invocations"][0]["model"] == "openai/test-coder"
    approval_material = orchestrator.target_plugin_approval_material(
        task_id,
        runtime_output_id=proposal["runtime_output_id"],
        selected_prompt_id=proposal["selected_prompt_id"],
    )
    assert approval_material["proposal_binding"] == proposal
    assert "approval_id" not in approval_material

    with pytest.raises(CodingOrchestratorError, match="repair_approval_reuse_detected"):
        orchestrator.execute_approved(
            task_id,
            approved_diff=proposal_receipt["target_plugin_result"]["proposed_diff"],
            action="apply",
            approval_id=original_approval_id,
            selected_prompt_id=proposal["selected_prompt_id"],
            context_hash=proposal["context_hash"],
            runtime_output_id=proposal["runtime_output_id"],
            target=proposal["target"],
        )


def test_verifier_failure_queues_fresh_attempt_with_blocked_reasons(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    task_id = "task-verifier-repair"
    run_id = "run-verifier-repair"
    state = _repair_ready_state(task_id=task_id, run_id=run_id)
    state.lane_states["coder"] = "completed"
    state.lane_states["reviewer"] = "completed"
    state.immutable_artifact = _repair_test_artifact(
        task_id=task_id,
        run_id=run_id,
        approval_id="approval-verifier-original",
        workspace_root=tmp_path,
    )
    state.participant_records = [
        {"role": "coding-executor", "invocation_id": "executor-verifier"},
        {"role": "coding-reviewer", "invocation_id": "reviewer-verifier"},
    ]
    persisted: list[dict[str, Any]] = []
    canonical_report = _canonical_context_report()
    verification = {
        "verdict": "FAIL",
        "blocked_reasons": ["public test expected 204 but received 200"],
        "status": "verification_failed",
        "checks": [
            {
                "id": "public_api_contract",
                "required": True,
                "status": "failed",
                "exit_code": 1,
                "output_tail": "expected status 204 but received 200",
            }
        ],
    }
    monkeypatch.setattr(
        orchestrator_module,
        "acknowledge_task_context_consumer",
        lambda *_args, **_kwargs: copy.deepcopy(canonical_report),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "canonical_context_broker_for_task",
        lambda _task_id: copy.deepcopy(canonical_report),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(copy.deepcopy(state)),
    )
    orchestrator = CodingOrchestrator(
        post_apply_verifier=lambda task_id, **_kwargs: {
            "task": {
                "id": task_id,
                "ast_snapshot": {"post_apply_verification": copy.deepcopy(verification)},
            }
        },
        verifier=lambda _artifact, _verification: {
            "role": "coding-verifier",
            "invocation_id": "verifier-failed",
            "output_id": "verifier-failed-output",
            "passed": False,
            "result": {
                "passed": False,
                "verdict": "FAIL",
                "checks": ["public-tests"],
            },
        },
        state_loader=lambda _task_id: (
            copy.deepcopy(persisted[-1])
            if persisted
            else state.receipt(summary="verifier repair ready")
        ),
        attempt_failure_finalizer=_invalidated_attempt_finalizer(
            approval_id="approval-verifier-original"
        ),
    )
    monkeypatch.setattr(
        orchestrator,
        "_append_participant",
        lambda run, record: run.participant_records.append(copy.deepcopy(dict(record))),
    )

    response = orchestrator.complete_post_apply(task_id)

    assert response["repair_required"] is True
    receipt = response["coding_orchestrator"]
    assert receipt["run_id"] == run_id
    assert receipt["attempt_number"] == 2
    assert receipt["repair_request"]["failure_class"] == "verifier_rejection"
    assert receipt["repair_request"]["exact_feedback"]["blocked_reasons"] == [
        "public test expected 204 but received 200"
    ]
    assert receipt["attempt_history"][0]["failure"]["source_lane"] == "verifier"
    assert receipt["attempt_dispositions"][0]["authority_state"] == "invalidated"
    diagnostic = receipt["repair_request"]["repair_diagnostic"]
    assert diagnostic["classification_input"] == {
        "diagnostic_code": "visible_tests_failed:public_api_contract",
        "stage": "tests",
        "reason": "visible_tests_failed:public_api_contract",
        "input_source": "post_apply_verification.checks[0]",
        "structured_evidence": verification["checks"][0],
    }
    assert diagnostic["classification"]["failure_kind"] == "runtime_error"
    assert diagnostic["classification"]["retry_owner"] == "debugger_then_coder"
    assert diagnostic["exact_failure_output"]["post_apply_verification"] == verification
    assert diagnostic["model_debugger_invoked"] is False
    assert diagnostic["deterministic_debugger_invoked"] is True
    trace = diagnostic["debugger_trace"]
    assert trace["schema_version"] == "coding.deterministic-debugger-trace/v1"
    assert trace["tool_kind"] == "deterministic_python_ast_state_probe"
    assert trace["model_debugger_invoked"] is False
    assert trace["timed_out"] is False
    assert trace["exit_status"] == 0
    assert trace["argv"][1:3] == ["-I", "-c"]
    assert trace["argv_sha256"] == orchestrator_module._sha256_json(trace["argv"])
    assert trace["input_payload"]["exact_failure_output"] == diagnostic[
        "exact_failure_output"
    ]
    assert trace["input_payload"]["current_state_manifest_sha256"] == diagnostic[
        "current_state_manifest_sha256"
    ]
    assert trace["findings"]["failed_checks"] == verification["checks"]
    assert trace["findings"]["files"][0]["state_matches"] is True
    assert trace["stdout_sha256"] == orchestrator_module._sha256_text(
        trace["stdout"]
    )
    assert trace["trace_sha256"] == orchestrator_module._sha256_json(
        {key: value for key, value in trace.items() if key != "trace_sha256"}
    )
    assert any(
        event["event_type"] == "deterministic_debugger_executed"
        and event["detail"]["trace_sha256"] == trace["trace_sha256"]
        for event in receipt["attempt_history"][0]["attempt_state"]["causal_events"]
    )


def test_required_participant_worker_failure_is_durable_and_structured(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    task_id = "task-participant-worker-failure"
    run_id = "run-participant-worker-failure"
    state = _repair_ready_state(task_id=task_id, run_id=run_id)
    state.lane_states["coder"] = "completed"
    state.lane_states["reviewer"] = "completed"
    state.immutable_artifact = _repair_test_artifact(
        task_id=task_id,
        run_id=run_id,
        approval_id="approval-participant-worker-failure",
        workspace_root=tmp_path,
    )
    state.participant_records = [
        {"role": "coding-executor", "invocation_id": "executor-participant"},
        {"role": "coding-reviewer", "invocation_id": "reviewer-participant"},
    ]
    persisted: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    canonical_report = _canonical_context_report()
    verification = {
        "status": "verified",
        "checks": [{"id": "public-tests", "required": True, "status": "passed"}],
        "manual_browser_check_required": False,
    }
    monkeypatch.setattr(
        orchestrator_module,
        "acknowledge_task_context_consumer",
        lambda *_args, **_kwargs: copy.deepcopy(canonical_report),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(copy.deepcopy(state)),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "fail_orchestrated_coding_execution",
        lambda task_id, **kwargs: failed.append(
            {"task_id": task_id, **copy.deepcopy(kwargs)}
        )
        or {"task": {"id": task_id, "status": "verification_failed"}},
    )

    def anti_cheat_failure(*_args, **_kwargs):
        raise CodingParticipantError("coding_artifact_diff_unavailable")

    orchestrator = CodingOrchestrator(
        post_apply_verifier=lambda task_id, **_kwargs: {
            "task": {
                "id": task_id,
                "ast_snapshot": {
                    "post_apply_verification": copy.deepcopy(verification)
                },
            }
        },
        verifier=lambda _artifact, _verification: {
            "role": "coding-verifier",
            "invocation_id": "verifier-participant",
            "output_id": "verifier-participant-output",
            "passed": True,
            "result": {"passed": True, "verdict": "PASS", "checks": []},
        },
        anti_cheat=anti_cheat_failure,
        state_loader=lambda _task_id: (
            copy.deepcopy(persisted[-1])
            if persisted
            else state.receipt(summary="participant failure ready")
        ),
    )
    monkeypatch.setattr(
        orchestrator,
        "_append_participant",
        lambda run, record: run.participant_records.append(copy.deepcopy(dict(record))),
    )

    with pytest.raises(
        CodingOrchestratorError,
        match="coding_artifact_diff_unavailable",
    ):
        orchestrator.complete_post_apply(task_id)

    assert failed == [
        {
            "task_id": task_id,
            "reason_code": "coding_artifact_diff_unavailable",
            "participant_records": state.participant_records
            + [
                {
                    "role": "coding-verifier",
                    "invocation_id": "verifier-participant",
                    "output_id": "verifier-participant-output",
                    "passed": True,
                    "result": {
                        "passed": True,
                        "verdict": "PASS",
                        "checks": [],
                    },
                }
            ],
        }
    ]
    assert persisted[-1]["lane_states"]["anti-cheat"] == "failed"
    assert persisted[-1]["lane_reasons"]["anti-cheat"] == (
        "coding_artifact_diff_unavailable"
    )
    assert any(
        event["event_type"] == "participant_failure"
        and event["lane_id"] == "anti-cheat"
        and event["detail"]["reason_code"] == "coding_artifact_diff_unavailable"
        for event in persisted[-1]["causal_events"]
    )


def test_structured_repair_diagnostic_distinguishes_runtime_from_environment() -> None:
    runtime_input = orchestrator_module._structured_repair_diagnostic_input(
        failure_class="verifier_rejection",
        source_lane="verifier",
        exact_feedback={
            "post_apply_verification": {
                "checks": [
                    {
                        "id": "public_tests",
                        "status": "failed",
                        "required": True,
                        "exit_code": 1,
                    }
                ]
            }
        },
    )
    environment_input = orchestrator_module._structured_repair_diagnostic_input(
        failure_class="verifier_rejection",
        source_lane="verifier",
        exact_feedback={
            "post_apply_verification": {
                "checks": [
                    {
                        "id": "public_tests",
                        "status": "failed",
                        "required": True,
                        "reason_code": "dependency_unavailable",
                        "failure_category": "environment",
                    }
                ]
            }
        },
    )

    runtime = orchestrator_module.classify_repair_failure(
        diagnostic_code=runtime_input["diagnostic_code"],
        stage=runtime_input["stage"],
        reason=runtime_input["reason"],
    ).to_dict()
    environment = orchestrator_module.classify_repair_failure(
        diagnostic_code=environment_input["diagnostic_code"],
        stage=environment_input["stage"],
        reason=environment_input["reason"],
    ).to_dict()

    assert runtime["failure_kind"] == "runtime_error"
    assert runtime["retry_owner"] == "debugger_then_coder"
    assert environment_input["stage"] == "environment"
    assert environment["failure_kind"] == "test_environment_error"
    assert environment["retry_owner"] == "environment_recovery"


def test_repair_strategy_signature_ignores_attempt_identity_but_changes_with_evidence() -> None:
    common = {
        "feedback_sha256": "sha256:" + "1" * 64,
        "current_state_manifest_sha256": "sha256:" + "2" * 64,
        "original_task": "Fix the backend response.",
    }
    participant = {"provider": "ollama", "model": "qwen-coder"}
    first = orchestrator_module._repair_strategy_signature(
        repair_request={**common, "repair_input_sha256": "sha256:" + "3" * 64},
        approved_diff="diff --git a/a.py b/a.py\n",
        participant=participant,
        selected_prompt_id="generic-architect-coder-packet",
        selected_context_id="generic-workspace-context",
    )
    same_evidence_new_attempt = orchestrator_module._repair_strategy_signature(
        repair_request={**common, "repair_input_sha256": "sha256:" + "4" * 64},
        approved_diff="diff --git a/a.py b/a.py\n",
        participant=participant,
        selected_prompt_id="generic-architect-coder-packet",
        selected_context_id="generic-workspace-context",
    )
    changed_evidence = orchestrator_module._repair_strategy_signature(
        repair_request={
            **common,
            "feedback_sha256": "sha256:" + "5" * 64,
            "repair_input_sha256": "sha256:" + "6" * 64,
        },
        approved_diff="diff --git a/a.py b/a.py\n",
        participant=participant,
        selected_prompt_id="generic-architect-coder-packet",
        selected_context_id="generic-workspace-context",
    )

    assert first == same_evidence_new_attempt
    assert changed_evidence != first


def test_third_failed_attempt_is_terminally_sealed_at_the_bound(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    task_id = "task-repair-limit"
    run_id = "run-repair-limit"
    state = CodingLaneStateMachine(
        task_id=task_id,
        run_id=run_id,
        attempt_id="attempt-3",
        parent_attempt_id="attempt-2",
        attempt_number=3,
        attempt_history=[
            {"attempt_id": "attempt-1", "approval_binding": {"approval_id": "approval-1"}},
            {"attempt_id": "attempt-2", "approval_binding": {"approval_id": "approval-2"}},
        ],
        repair_request={"schema_version": "test-repair-request"},
    )
    state.lane_states["repair"] = "running"
    state.immutable_artifact = _repair_test_artifact(
        task_id=task_id,
        run_id=run_id,
        approval_id="approval-3",
        workspace_root=tmp_path,
    )
    state.target_plugin_proposal = {"repair_strategy_signature": "sha256:" + "7" * 64}
    persisted: list[dict[str, Any]] = []
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(copy.deepcopy(state)),
    )
    orchestrator = CodingOrchestrator(
        state_loader=lambda _task_id: state.receipt(summary="repair limit state"),
        attempt_failure_finalizer=_invalidated_attempt_finalizer(
            approval_id="approval-3"
        ),
    )

    with pytest.raises(CodingOrchestratorError, match="repair_attempt_limit_exhausted"):
        orchestrator._queue_evidence_guided_repair(
            state,
            failure_class="reviewer_rejection",
            source_lane="reviewer",
            exact_feedback={"findings": ["still failing"]},
        )
    orchestrator._mark_repair_exhausted(
        state,
        reason_code="independent_review_failed",
        failure_class="reviewer_rejection",
        source_lane="reviewer",
        exact_feedback={"findings": ["still failing"]},
    )

    receipt = state.receipt(summary="bounded repair exhausted")
    assert receipt["attempt_number"] == 3
    assert len(receipt["attempt_history"]) == 3
    assert receipt["attempt_history"][-1]["next_attempt_id"] is None
    assert receipt["attempt_dispositions"][-1]["authority_state"] == "invalidated"
    assert receipt["lane_states"]["repair"] == "failed"
    assert receipt["repair_request"] is None
    restored = orchestrator._restore(task_id)
    assert restored.attempt_id == "attempt-3"


@pytest.mark.parametrize("disposition_persisted_before_crash", [False, True])
def test_sealed_repair_attempt_resumes_without_reusing_or_refinalizing_approval(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    disposition_persisted_before_crash: bool,
) -> None:
    task_id = f"task-seal-resume-{int(disposition_persisted_before_crash)}"
    run = _repair_ready_state(task_id=task_id, run_id="run-seal-resume")
    run.attempt_id = "attempt-before-crash"
    run.lane_states["reviewer"] = "failed"
    run.immutable_artifact = _repair_test_artifact(
        task_id=task_id,
        run_id=run.run_id,
        approval_id="approval-before-crash",
        workspace_root=tmp_path,
    )
    run.target_plugin_proposal = {
        "original_task": "Repair after a durable seal.",
        "proposal_binding_sha256": "sha256:" + "8" * 64,
    }
    persisted: list[dict[str, Any]] = []
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(copy.deepcopy(state)),
    )
    monkeypatch.setattr(
        orchestrator_module,
        "canonical_context_broker_for_task",
        lambda _task_id: copy.deepcopy(_canonical_context_report()),
    )
    finalization_calls: list[str] = []
    base_finalizer = _invalidated_attempt_finalizer(
        approval_id="approval-before-crash"
    )

    def finalizer(*args: Any, **kwargs: Any) -> dict[str, Any]:
        finalization_calls.append(str(kwargs.get("reason_code") or ""))
        return base_finalizer(*args, **kwargs)

    first = CodingOrchestrator(
        state_loader=lambda _task_id: copy.deepcopy(persisted[-1]),
        attempt_failure_finalizer=finalizer,
    )
    seal = first._seal_failed_attempt(
        run,
        failure_class="reviewer_rejection",
        source_lane="reviewer",
        exact_feedback={"findings": ["failed immediately before crash"]},
        next_attempt_id="attempt-after-crash",
        terminal=False,
    )
    assert len(run.attempt_history) == run.attempt_number == 1
    if disposition_persisted_before_crash:
        first._finalize_sealed_attempt_approval(run, seal)

    resumed_owner = CodingOrchestrator(
        state_loader=lambda _task_id: copy.deepcopy(persisted[-1]),
        attempt_failure_finalizer=finalizer,
    )
    resumed = resumed_owner._restore(task_id)
    assert orchestrator_module._sealed_attempt_awaits_disposition(resumed) is True
    receipt = resumed_owner._resume_sealed_attempt_disposition(resumed)

    assert receipt["run_id"] == run.run_id
    assert receipt["attempt_id"] == "attempt-after-crash"
    assert receipt["parent_attempt_id"] == "attempt-before-crash"
    assert receipt["attempt_number"] == 2
    assert len(receipt["attempt_history"]) == 1
    assert len(receipt["attempt_dispositions"]) == 1
    assert receipt["repair_request"]["prior_approval_id"] == "approval-before-crash"
    assert len(finalization_calls) == 1
