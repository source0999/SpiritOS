from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

import source_proxy.coding.orchestrator as orchestrator_module
from source_proxy.context.canonical_broker import acknowledge_context_consumer
from source_proxy.coding.orchestrator import (
    CodingLaneStateMachine,
    CodingOrchestrator,
    CodingOrchestratorError,
    LANE_SEQUENCE,
)
from source_proxy.tasks.long_running import execute_approved_long_running_task
from source_proxy.target_plugins.adapter import ResolvedTargetPlugin


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


def _canonical_target_plugin_result(target: str) -> dict[str, Any]:
    provenance = {
        "schema_version": "spiritos-target-adapter-provenance/v1",
        "rendered_prompt_sha256": "1" * 64,
        "raw_response_sha256": "2" * 64,
        "transport_kind": "canonical_litellm_router",
        "provider_call_made": True,
        "provider_call_authorized": True,
        "generation_source": "model",
        "trust_status": "canonical_router_model_output_validated",
        "terminal_proof_eligible": True,
        "provider": "openai",
        "model": "openai/test-coder",
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


def _propose_canonical_target_plugin(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[CodingOrchestrator, list[dict[str, object]], dict[str, Any]]:
    persisted: list[dict[str, object]] = []
    state = CodingLaneStateMachine(task_id="task-binding", run_id="run-binding")
    state.lane_states["context-broker"] = "completed"
    state.lane_states["planner"] = "completed"
    _seed_consumed_context_output(state, context_hash="planner-context-hash")
    source_head = "a" * 40
    target = "tests/ui-agent-trials/fixtures/dummy-product-site/index.html"
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


def _seed_consumed_context_output(
    state: CodingLaneStateMachine,
    *,
    context_hash: str,
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
    assert (
        proposal["model_output_provenance"]["target_adapter_provenance"]
        == proposal["target_adapter_provenance"]
    )
    assert (
        orchestrator_module._sha256_json(proposal["model_output_provenance"])
        == participant["output_sha256"]
        == proposal["producer_model_output_sha256"]
    )
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
