from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from source_proxy.testing.runner import (
    PROFILE_CARTOGRAPHER_SAFETY,
    PROFILE_CARTOGRAPHER_SOAK_SNAPSHOT,
    PROFILE_PROXY_CLOSEOUT,
    PROFILE_PROXY_REGRESSION,
    PROFILE_PROXY_SMOKE,
    PROFILE_PHASE_4F_CLOSEOUT,
    PROFILE_SCOUT_SEARCH_DIAGNOSTICS,
    PROFILE_SCOUT_SEARCH_SMOKE,
    PROFILE_SCOUT_SMOKE,
    PROFILE_SCOUT_SOAK_SNAPSHOT,
    PROFILE_SCOUT_SOURCE_GATE,
    run_runner_profile,
)
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
    profile: str | None = None


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
    if request.profile is not None:
        supported_profiles = {
            PROFILE_PROXY_SMOKE,
            PROFILE_CARTOGRAPHER_SAFETY,
            PROFILE_CARTOGRAPHER_SOAK_SNAPSHOT,
            PROFILE_PROXY_REGRESSION,
            PROFILE_PROXY_CLOSEOUT,
            PROFILE_PHASE_4F_CLOSEOUT,
            PROFILE_SCOUT_SMOKE,
            PROFILE_SCOUT_SOURCE_GATE,
            PROFILE_SCOUT_SEARCH_DIAGNOSTICS,
            PROFILE_SCOUT_SEARCH_SMOKE,
            PROFILE_SCOUT_SOAK_SNAPSHOT,
        }
        if request.profile not in supported_profiles:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": f"Unsupported self-test profile: {request.profile}",
                    "supported_profiles": sorted(supported_profiles),
                },
            )
        try:
            payload = run_runner_profile(profile=request.profile)
        except ValueError as error:
            raise HTTPException(status_code=400, detail={"error": str(error)}) from error
        return {
            **payload,
            "mode": DRY_RUN_MODE,
            "applied_anything": False,
        }

    try:
        return run_self_test_suite(
            suite=request.suite,
            case_ids=request.case_ids,
            mode=request.mode,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"error": str(error)}) from error
