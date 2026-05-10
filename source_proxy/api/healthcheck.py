from fastapi import APIRouter, HTTPException, status

from source_proxy.budget.manager import (
    BudgetStatusUnavailable,
    collect_budget_status,
)
from source_proxy.diagnostics.gpu import GpuMetricsUnavailable, collect_vram_metrics

router = APIRouter()


@router.get("/healthcheck")
async def healthcheck() -> dict[str, str]:
    try:
        payload = collect_vram_metrics().as_healthcheck_payload()
        payload.update(collect_budget_status().as_healthcheck_payload())
        return payload
    except (GpuMetricsUnavailable, BudgetStatusUnavailable) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
