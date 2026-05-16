from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from scout.config import get_settings
from scout.sources.discovery_jobs import (
    DiscoveryJob,
    DiscoveryJobError,
    create_discovery_job,
    get_discovery_job,
    list_discovery_jobs,
    pause_discovery_job,
    resume_discovery_job,
)
from scout.sources.search import run_searxng_search, search_result_to_dict
from scout.sources.search_candidates import (
    create_candidates_from_search_result,
    extraction_to_dict,
)

router = APIRouter(prefix="/v1/scout", tags=["scout"])


class DiscoveryJobCreateRequest(BaseModel):
    query: str = Field(min_length=1)
    topic_anchor: str | None = None
    max_results: int = Field(default=10, ge=1, le=50)
    budget: int = Field(default=10, ge=1, le=50)
    metadata: dict[str, Any] | None = None


@router.get("/discovery-jobs")
def get_discovery_jobs(
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    settings = get_settings()
    try:
        jobs = list_discovery_jobs(settings.database_path, status=status, limit=limit)
    except DiscoveryJobError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "count": len(jobs),
        "jobs": [_job_to_dict(job) for job in jobs],
    }


@router.post("/discovery-jobs", status_code=201)
def post_discovery_job(request: DiscoveryJobCreateRequest) -> dict[str, Any]:
    settings = get_settings()
    if not settings.discovery_jobs_enabled:
        raise HTTPException(status_code=409, detail="Scout discovery jobs are disabled")
    try:
        job = create_discovery_job(
            settings.database_path,
            query=request.query,
            topic_anchor=request.topic_anchor,
            max_results=request.max_results,
            budget=request.budget,
            max_jobs_per_day=settings.discovery_jobs_per_day,
            metadata=request.metadata,
        )
    except DiscoveryJobError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"job": _job_to_dict(job)}


@router.post("/discovery-jobs/{job_id}/pause")
def post_pause_discovery_job(job_id: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        job = pause_discovery_job(settings.database_path, job_id)
    except DiscoveryJobError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"job": _job_to_dict(job)}


@router.post("/discovery-jobs/{job_id}/resume")
def post_resume_discovery_job(job_id: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        job = resume_discovery_job(settings.database_path, job_id)
    except DiscoveryJobError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"job": _job_to_dict(job)}


@router.post("/discovery-jobs/{job_id}/search-preview")
def post_discovery_job_search_preview(job_id: str) -> dict[str, Any]:
    settings = get_settings()
    job = get_discovery_job(settings.database_path, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="discovery job not found")
    if job.status != "queued":
        raise HTTPException(status_code=409, detail="discovery job is not queued")
    if not settings.search_enabled:
        raise HTTPException(status_code=409, detail="Scout search is disabled")
    if settings.search_provider != "searxng":
        raise HTTPException(status_code=422, detail="unsupported Scout search provider")

    result = run_searxng_search(
        query=job.query,
        base_url=settings.searxng_url,
        max_results=_effective_result_limit(settings, job),
        timeout_seconds=settings.search_timeout_seconds,
        user_agent=settings.search_user_agent,
    )
    return {
        "job": _job_to_dict(job),
        "result": search_result_to_dict(result),
        "candidate_effect": "none",
    }


@router.post("/discovery-jobs/{job_id}/extract-candidates")
def post_discovery_job_extract_candidates(job_id: str) -> dict[str, Any]:
    settings = get_settings()
    job = get_discovery_job(settings.database_path, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="discovery job not found")
    if job.status != "queued":
        raise HTTPException(status_code=409, detail="discovery job is not queued")
    if not settings.search_enabled:
        raise HTTPException(status_code=409, detail="Scout search is disabled")
    if settings.search_provider != "searxng":
        raise HTTPException(status_code=422, detail="unsupported Scout search provider")

    result = run_searxng_search(
        query=job.query,
        base_url=settings.searxng_url,
        max_results=_effective_result_limit(settings, job),
        timeout_seconds=settings.search_timeout_seconds,
        user_agent=settings.search_user_agent,
    )
    extraction = create_candidates_from_search_result(
        settings.database_path,
        job=job,
        result=result,
    )
    return {
        "job": _job_to_dict(job),
        "result": search_result_to_dict(result),
        "candidate_effect": "created_or_updated",
        "extraction": extraction_to_dict(extraction),
    }


def _job_to_dict(job: DiscoveryJob) -> dict[str, Any]:
    return {
        "job_id": job.job_id,
        "query": job.query,
        "topic_anchor": job.topic_anchor,
        "status": job.status,
        "max_results": job.max_results,
        "budget": job.budget,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "error": job.error,
        "metadata": job.metadata,
    }


def _effective_result_limit(settings: Any, job: DiscoveryJob) -> int:
    return max(
        1,
        min(
            job.max_results,
            job.budget,
            settings.search_max_results,
            settings.discovery_candidates_per_job,
        ),
    )
