from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from scout.config import get_settings
from scout.packets.promotions import (
    PromotionError,
    approve_promotion,
    dry_run_proxy_import,
    list_promotions,
    reject_promotion,
)

router = APIRouter(prefix="/v1/scout/promotions")


class FinalizePromotionRequest(BaseModel):
    promotion_id: str
    action: str = Field(pattern="^(approve|reject)$")
    approved_by: str | None = None
    rejected_reason: str | None = None


class ImportDryRunRequest(BaseModel):
    promotion_id: str
    requested_by: str | None = None


@router.get("")
async def get_promotions() -> dict:
    return list_promotions(get_settings())


@router.post("/finalize")
async def finalize_promotion(request: FinalizePromotionRequest) -> dict:
    try:
        if request.action == "approve":
            item = approve_promotion(
                get_settings(),
                request.promotion_id,
                approved_by=request.approved_by or "manual-review",
            )
            return {"promotion": item}
        reason = request.rejected_reason or "Rejected during manual Scout review."
        item = reject_promotion(get_settings(), request.promotion_id, reason=reason)
        return {"promotion": item}
    except PromotionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/import-dry-run")
async def import_dry_run(request: ImportDryRunRequest) -> dict:
    try:
        result = dry_run_proxy_import(get_settings(), request.promotion_id)
    except PromotionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    result["requested_by"] = request.requested_by or "manual-review"
    return result
