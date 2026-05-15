from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from scout.config import get_settings
from scout.sources.discovery_jobs import (
    DiscoveryJob,
    DiscoveryJobError,
    create_discovery_job,
    list_discovery_jobs,
    pause_discovery_job,
    resume_discovery_job,
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
    try:
        job = create_discovery_job(
            settings.database_path,
            query=request.query,
            topic_anchor=request.topic_anchor,
            max_results=request.max_results,
            budget=request.budget,
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
