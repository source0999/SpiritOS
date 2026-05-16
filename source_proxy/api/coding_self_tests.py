from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from source_proxy.testing.self_tests import (
    DRY_RUN_MODE,
    SUITE_PHASE_4E_SAFETY_SEED,
    run_self_test_suite,
)


router = APIRouter(prefix="/v1/coding")


class CodingSelfTestRunRequest(BaseModel):
    suite: str = Field(default=SUITE_PHASE_4E_SAFETY_SEED)
    case_ids: list[str] | None = None
    mode: str = Field(default=DRY_RUN_MODE)


@router.post("/self-tests/run")
async def coding_self_tests_run(request: CodingSelfTestRunRequest) -> dict[str, Any]:
    if request.mode != DRY_RUN_MODE:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Only dry_run mode is supported for coding self-tests.",
                "supported_modes": [DRY_RUN_MODE],
            },
        )
    try:
        return run_self_test_suite(
            suite=request.suite,
            case_ids=request.case_ids,
            mode=request.mode,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"error": str(error)}) from error

