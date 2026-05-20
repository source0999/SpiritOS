from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from scout.config import get_settings
from scout.sources.storage import list_candidates
from scout.sources.discovery_jobs import (
    DiscoveryJob,
    DiscoveryJobBudget,
    DiscoveryJobComputedState,
    DiscoveryJobError,
    classify_discovery_job_states,
    create_discovery_job,
    get_discovery_job,
    get_discovery_job_budget,
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


@router.get("/discovery-proposals")
def get_discovery_proposals(
    limit: int = Query(default=10, ge=1, le=50),
) -> dict[str, Any]:
    settings = get_settings()
    candidates = list_candidates(settings.database_path, limit=200)
    budget = get_discovery_job_budget(
        settings.database_path,
        max_jobs_per_day=settings.discovery_jobs_per_day,
    )
    proposals = _build_discovery_proposals(candidates, limit=limit)
    return {
        "count": len(proposals),
        "mode": "manual_approved_proposals",
        "read_only": True,
        "mutation_allowed": False,
        "approval_required_before": ["create_discovery_job", "search-preview", "extract-candidates"],
        "forbidden_actions": [
            "automatic_discovery_execution",
            "automatic_candidate_extraction",
            "source_activation",
            "source_approval",
            "source_rejection",
            "source_blocking",
            "packet_promotion",
            "proxy_memory_write",
            "coding_context_write",
        ],
        "budget": _budget_to_dict(budget),
        "proposals": proposals,
    }


@router.get("/discovery-jobs")
def get_discovery_jobs(
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    settings = get_settings()
    try:
        jobs = list_discovery_jobs(settings.database_path, status=status, limit=limit)
        budget = get_discovery_job_budget(
            settings.database_path,
            max_jobs_per_day=settings.discovery_jobs_per_day,
        )
        computed_states = classify_discovery_job_states(jobs, budget=budget)
    except DiscoveryJobError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "count": len(jobs),
        "budget": _budget_to_dict(budget),
        "execution": _execution_to_dict(),
        "jobs": [
            _job_to_dict(job, computed_state=computed_states.get(job.job_id))
            for job in jobs
        ],
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

    effective_limit = _effective_result_limit(settings, job)
    result = run_searxng_search(
        query=job.query,
        base_url=settings.searxng_url,
        max_results=effective_limit,
        timeout_seconds=settings.search_timeout_seconds,
        user_agent=settings.search_user_agent,
    )
    return {
        "job": _job_to_dict(job),
        "result": search_result_to_dict(result),
        "candidate_effect": "none",
        "bounds": _bounds_to_dict(settings, job, effective_limit=effective_limit),
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

    effective_limit = _effective_result_limit(settings, job)
    result = run_searxng_search(
        query=job.query,
        base_url=settings.searxng_url,
        max_results=effective_limit,
        timeout_seconds=settings.search_timeout_seconds,
        user_agent=settings.search_user_agent,
    )
    extraction = create_candidates_from_search_result(
        settings.database_path,
        job=job,
        result=result,
        max_candidates=effective_limit,
    )
    return {
        "job": _job_to_dict(job),
        "result": search_result_to_dict(result),
        "candidate_effect": "created_or_updated",
        "bounds": _bounds_to_dict(settings, job, effective_limit=effective_limit),
        "extraction": extraction_to_dict(extraction),
    }


def _job_to_dict(
    job: DiscoveryJob,
    *,
    computed_state: DiscoveryJobComputedState | None = None,
) -> dict[str, Any]:
    computed_state = computed_state or DiscoveryJobComputedState(
        computed_status=job.status,
        attention_label=None,
        safe_next_action="inspect_job",
    )
    return {
        "job_id": job.job_id,
        "query": job.query,
        "topic_anchor": job.topic_anchor,
        "status": job.status,
        "computed_status": computed_state.computed_status,
        "attention_label": computed_state.attention_label,
        "safe_next_action": computed_state.safe_next_action,
        "max_results": job.max_results,
        "budget": job.budget,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "error": job.error,
        "metadata": job.metadata,
    }


def _budget_to_dict(budget: DiscoveryJobBudget) -> dict[str, Any]:
    return {
        "daily_limit": budget.daily_limit,
        "used_today": budget.used_today,
        "remaining_today": budget.remaining_today,
        "can_create_job": budget.can_create_job,
        "blocked_reason": budget.blocked_reason,
        "next_reset_hint": budget.next_reset_hint,
        "queued_jobs": budget.queued_jobs,
        "running_jobs": budget.running_jobs,
        "completed_jobs": budget.completed_jobs,
        "failed_jobs": budget.failed_jobs,
    }


def _execution_to_dict() -> dict[str, Any]:
    return {
        "mode": "manual_controlled",
        "automatic_execution": False,
        "worker_registered": False,
        "queued_job_meaning": "saved_search_plan",
        "advance_actions": ["search-preview", "extract-candidates"],
        "explanation": (
            "Discovery jobs are saved controlled search plans. Scout does not run "
            "them in the background; use Preview Search or Extract Candidates to advance one."
        ),
    }


def _build_discovery_proposals(candidates: list[Any], *, limit: int) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    seen_queries: set[str] = set()
    for candidate in candidates:
        if candidate.status not in {"recommended", "needs_review"}:
            continue
        label = _proposal_topic_label(candidate)
        if not label:
            continue
        query = f"official {label} release notes changelog"
        normalized_query = " ".join(query.lower().split())
        if normalized_query in seen_queries:
            continue
        seen_queries.add(normalized_query)
        proposals.append(
            {
                "proposal_id": f"proposal:{candidate.candidate_id}",
                "query": query,
                "topic_anchor": _proposal_topic_anchor(candidate),
                "max_results": 5,
                "budget": 5,
                "source_candidate_id": candidate.candidate_id,
                "source_candidate_status": candidate.status,
                "source_candidate_uri": candidate.canonical_uri,
                "reason": _proposal_reason(candidate),
                "risk_reason": "Proposal only; operator approval is required before creating a discovery job.",
                "safe_next_action": "operator_may_create_discovery_job",
                "mutation_effect": "none",
                "approval_required_before": ["create_discovery_job", "search-preview", "extract-candidates"],
            }
        )
        if len(proposals) >= limit:
            break
    return proposals


def _proposal_topic_label(candidate: Any) -> str:
    uri = str(candidate.canonical_uri or candidate.display_uri or "").strip()
    if uri.startswith("github://"):
        return uri.removeprefix("github://").replace("/", " ")
    if "://" in uri:
        without_scheme = uri.split("://", 1)[1]
        return without_scheme.split("/", 1)[0].replace("www.", "")
    return uri.replace("_", " ").replace("-", " ")


def _proposal_topic_anchor(candidate: Any) -> str:
    uri = str(candidate.canonical_uri or candidate.display_uri or "").lower()
    if uri.startswith("github://"):
        parts = uri.removeprefix("github://").split("/")
        return parts[0] if parts and parts[0] else "source"
    if "python" in uri:
        return "python"
    if "fastapi" in uri:
        return "fastapi"
    if "pydantic" in uri:
        return "pydantic"
    return "source"


def _proposal_reason(candidate: Any) -> str:
    if candidate.status == "recommended":
        return "Recommended Source Gate evidence suggests a bounded manual discovery job may be useful."
    return "Needs-review Source Gate evidence may benefit from a bounded manual discovery job."


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


def _bounds_to_dict(
    settings: Any,
    job: DiscoveryJob,
    *,
    effective_limit: int,
) -> dict[str, Any]:
    return {
        "effective_result_limit": effective_limit,
        "job_max_results": job.max_results,
        "job_budget": job.budget,
        "search_max_results": settings.search_max_results,
        "discovery_candidates_per_job": settings.discovery_candidates_per_job,
        "manual_activation_required": True,
        "automatic_activation": False,
    }
