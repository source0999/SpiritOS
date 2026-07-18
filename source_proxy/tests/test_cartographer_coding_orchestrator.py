from __future__ import annotations

import source_proxy.coding.orchestrator as orchestrator_module
from source_proxy.coding.orchestrator import CodingLaneStateMachine, CodingOrchestrator


def test_cartographer_selection_finalizes_only_after_completed_coding_output(monkeypatch) -> None:
    consumed_calls: list[dict[str, str]] = []
    finalized_calls: list[dict[str, object]] = []
    persisted: list[dict[str, object]] = []
    state = CodingLaneStateMachine(task_id="task-1", run_id="run-1")
    consumed = {
        "approval_id": "apr-selection",
        "generation": 1,
        "binding": {
            "content_hash": "content-hash",
            "context": "context-json",
            "preview": "preview-1",
            "source_head": "a" * 40,
        },
    }
    monkeypatch.setattr(
        orchestrator_module,
        "consume_cartographer_selection",
        lambda **kwargs: consumed_calls.append(kwargs) or consumed,
    )
    monkeypatch.setattr(
        orchestrator_module,
        "finalize_cartographer_selection",
        lambda **kwargs: finalized_calls.append(kwargs)
        or {
            "receipt": {
                "approval_id": "apr-selection",
                "generation": 1,
                "state": "consumed",
                "result_id": "cartographer-transfer-selection",
            }
        },
    )
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(state),
    )
    monkeypatch.setattr(orchestrator_module, "current_head", lambda: "a" * 40)

    def start(_self, _task_id, *, sources):
        del sources
        payload = state.receipt(summary="started")
        persisted.append(payload)
        return payload

    monkeypatch.setattr(CodingOrchestrator, "start", start)
    orchestrator = CodingOrchestrator(
        state_loader=lambda _task_id: persisted[-1]
    )

    receipt = orchestrator.start_from_cartographer_selection(
        "task-1", selection_approval_id="apr-selection", proposal_id="proposal-1",
        target="src/example.ts", sources=[],
    )

    assert consumed_calls == [{"approval_id": "apr-selection", "proposal_id": "proposal-1", "consumer": "coding-executor:coder", "target": "src/example.ts"}]
    assert finalized_calls == []
    assert receipt["cartographer_selection"]["downstream_consumer_invocation_id"] is None

    run = orchestrator._restore("task-1")
    participant = {
        "invocation_id": "target-model-invocation-1",
        "output_id": "target-model-output-1",
        "output_sha256": "b" * 64,
        "artifact_sha256": "c" * 64,
        "completed_at": "2026-07-17T12:00:00+00:00",
        "passed": True,
    }
    orchestrator._finalize_cartographer_transfer_after_invocation(
        run,
        participant=participant,
        target="src/example.ts",
    )

    transfer = finalized_calls[0]["transfer"]
    acknowledgement = finalized_calls[0]["downstream_acknowledgement"]
    assert transfer["proposal_id"] == "proposal-1"
    assert transfer["selection_id"] == "apr-selection"
    assert transfer["run_id"] == "run-1"
    assert acknowledgement["transfer_event_id"] == transfer["transfer_event_id"]
    assert acknowledgement["consumer_invocation_id"] == transfer["downstream_consumer_invocation_id"]
    assert acknowledgement["consumer_output_id"] == participant["output_id"]
    assert acknowledgement["consumer_output_sha256"] == participant["output_sha256"]
    assert acknowledgement["consumer_artifact_sha256"] == participant["artifact_sha256"]
    assert acknowledgement["consumer_completed_at"] == participant["completed_at"]
    assert acknowledgement["consumer_passed"] is True
    assert persisted[-1]["cartographer_finalization"]["state"] == "consumed"
    assert (
        persisted[-1]["cartographer_finalization"]["downstream_acknowledgement"][
            "consumer_invocation_id"
        ]
        == "target-model-invocation-1"
    )


def test_cartographer_selection_rejects_started_invocation_without_output(
    monkeypatch,
) -> None:
    persisted: list[dict[str, object]] = []
    state = CodingLaneStateMachine(task_id="task-1", run_id="run-1")
    state.cartographer_selection_consumption = {
        "approval_id": "apr-selection",
        "generation": 1,
        "binding": {"source_head": "a" * 40},
    }
    state.cartographer_transfer = {
        "schema_version": "cartographer.coding-transfer/v1",
        "proposal_id": "proposal-1",
        "selection_id": "apr-selection",
        "selection_approval_id": "apr-selection",
        "selection_generation": 1,
        "consumer": "coding-executor:coder",
        "target": "src/example.ts",
        "task_id": "task-1",
        "run_id": "run-1",
        "transfer_event_id": "transfer-event-1",
        "downstream_consumer_invocation_id": None,
        "provenance": {"source_head": "a" * 40},
    }
    monkeypatch.setattr(orchestrator_module, "current_head", lambda: "a" * 40)
    monkeypatch.setattr(
        orchestrator_module,
        "record_coding_orchestrator_state",
        lambda _task_id, *, state: persisted.append(state),
    )
    orchestrator = CodingOrchestrator()

    try:
        orchestrator._finalize_cartographer_transfer_after_invocation(
            state,
            participant={
                "invocation_id": "target-model-invocation-1",
                "passed": False,
            },
            target="src/example.ts",
        )
    except orchestrator_module.CodingOrchestratorError as error:
        assert error.reason_code == "cartographer_downstream_completed_output_missing"
    else:
        raise AssertionError("started-only invocation finalized Cartographer selection")
    assert state.cartographer_finalization is None
    assert state.cartographer_transfer["downstream_consumer_invocation_id"] is None
