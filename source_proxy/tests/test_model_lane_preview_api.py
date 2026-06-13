from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.decision import router as decision_router


def test_model_lanes_preview_endpoint_is_preview_only() -> None:
    app = FastAPI()
    app.include_router(decision_router)
    client = TestClient(app)

    response = client.post("/v1/decisions/model-lanes/preview", json={"task_type": "disposable_artifact"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview_only"] is True
    assert payload["would_call_models"] is False
    assert payload["would_start_workers"] is False
    assert payload["active_primary_lane"] == "qwen_local_coder"
    assert "hermes_sidecar_verifier_preview" in payload["future_sidecar_lanes"]
