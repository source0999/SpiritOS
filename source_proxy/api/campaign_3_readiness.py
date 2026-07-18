"""Read-only Campaign 3 backend contract for a future coding UI."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from source_proxy.coding.observability import build_coding_shell_observability
from source_proxy.tasks.long_running import LongRunningTaskError


router = APIRouter(prefix="/v1/coding")


@router.get("/tasks/{task_id}/campaign-readiness")
async def campaign_readiness(task_id: str) -> dict[str, object]:
    """Return backend capabilities only; this endpoint grants no mutation authority."""
    try:
        diagnosis = build_coding_shell_observability(task_id)
    except LongRunningTaskError as error:
        raise HTTPException(status_code=404, detail=error.reason_code) from error
    return {
        "schema_version": "campaign-3/coding-readiness/v1",
        "task_id": task_id,
        "read_only": True,
        "diagnosis": diagnosis,
        "contracts": {
            "task": "/v1/tasks/long-running/{task_id}",
            "runs": "/v1/coding/runs",
            "lane_state": "/v1/coding/tasks/{task_id}/observability",
            "diagnosis": "/v1/coding/tasks/{task_id}/campaign-readiness",
            "cancel": "/v1/tasks/long-running/{task_id}/cancel",
            "retry_recovery": "/v1/tasks/long-running/{task_id}/advance",
            "undo": "/v1/tasks/long-running/{task_id}/undo",
            "reset": "/v1/coding/dummy-product-site/reset",
            "browser_fixture": "/v1/coding/dummy-product-site-preview",
            "evidence_reconciliation": "/v1/coding/trial-receipt-reconcile",
            "self_test": "/v1/coding/self-tests/run",
        },
        "reconciliation": {
            "authority_boundary": "all mutation routes retain their existing approval checks",
            "evidence_boundary": "lane evidence is sourced from persisted task state only",
            "ui_state_authoritative": False,
            "campaign_4_ui_wiring_started": False,
            "mutation_projection_forbidden": True,
            "retry_requires_existing_authority_boundary": True,
        },
    }
