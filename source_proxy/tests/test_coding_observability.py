from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

import source_proxy.coding.observability as observability
from source_proxy.api.coding_observability import router


def _persisted_task() -> dict[str, object]:
    return {
        "task": {
            "status": "completed",
            "ast_snapshot": {
                "coding_orchestrator": {
                    "schema_version": "coding-orchestrator/v1",
                    "run_id": "coding-run-1",
                    "summary": "canonical coding run completed through final evidence",
                    "lane_states": {
                        "context-broker": "completed", "planner": "completed", "coder": "completed",
                        "reviewer": "completed", "verifier": "completed", "repair": "skipped",
                        "evidence-recorder": "completed",
                    },
                    "lane_reasons": {"repair": "verification_passed_no_repair_needed"},
                },
                "campaign_2_approval": {
                    "approval_id": "apr_c2", "generation": 4, "consumer": "coding-executor:coder",
                    "target_plugin_identity": {"plugin_id": "lumacart", "selected_prompt_id": "coder-001"},
                },
            },
        }
    }


def test_observability_surfaces_persisted_lane_authority_and_evidence(monkeypatch) -> None:
    monkeypatch.setattr(observability, "get_long_running_task_snapshot", lambda _task_id: _persisted_task())

    payload = observability.build_coding_shell_observability("task-1")

    assert payload["verdict"] == "RECORDED: canonical_coding_run_facts_available"
    assert payload["authority"]["lane_binding_valid"] is True
    assert payload["evidence_identity"] == {"plugin_id": "lumacart", "selected_prompt_id": "coder-001"}
    assert payload["lane_participation"][2] == {"lane_id": "coder", "state": "completed", "reason": ""}


def test_observability_reports_missing_or_unbound_facts_without_success_claim(monkeypatch) -> None:
    payload = _persisted_task()
    task = payload["task"]
    assert isinstance(task, dict)
    snapshot = task["ast_snapshot"]
    assert isinstance(snapshot, dict)
    snapshot["campaign_2_approval"] = {"consumer": "coding-executor"}
    monkeypatch.setattr(observability, "get_long_running_task_snapshot", lambda _task_id: payload)

    result = observability.build_coding_shell_observability("task-1")

    assert result["verdict"] == "DEGRADED: coding_authority_lane_binding_invalid"
    assert result["authority"]["lane_binding_valid"] is False


def test_observability_endpoint_is_read_only_surface(monkeypatch) -> None:
    monkeypatch.setattr(observability, "get_long_running_task_snapshot", lambda _task_id: _persisted_task())
    app = FastAPI()
    app.include_router(router)

    response = TestClient(app).get("/v1/coding/tasks/task-1/observability")

    assert response.status_code == 200
    assert response.json()["access_scope"] == "read_only_persisted_coding_run_observability"
