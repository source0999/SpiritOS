from fastapi import FastAPI
from fastapi.testclient import TestClient

import source_proxy.api.campaign_3_readiness as readiness
from source_proxy.api.campaign_3_readiness import router


def test_readiness_is_backend_only_and_reconciles_existing_contracts(monkeypatch) -> None:
    monkeypatch.setattr(readiness, "build_coding_shell_observability", lambda task_id: {"task_id": task_id, "diagnosis": True})
    app = FastAPI()
    app.include_router(router)
    response = TestClient(app).get("/v1/coding/tasks/task-1/campaign-readiness")
    payload = response.json()
    assert response.status_code == 200
    assert payload["read_only"] is True
    assert payload["reconciliation"]["ui_state_authoritative"] is False
    assert payload["reconciliation"]["campaign_4_ui_wiring_started"] is False
    assert payload["contracts"]["cancel"].endswith("/cancel")
    assert payload["contracts"]["retry_recovery"].endswith("/advance")
    assert payload["contracts"]["evidence_reconciliation"].endswith("trial-receipt-reconcile")
    assert payload["reconciliation"]["mutation_projection_forbidden"] is True
    assert payload["reconciliation"]["retry_requires_existing_authority_boundary"] is True
