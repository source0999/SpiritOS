from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from scout.config import get_settings
from scout.pollers.registry import load_merged_registry
from scout.sources.discovery import run_artifact_discovery
from scout.sources.storage import (
    CANDIDATE_STATUSES,
    SourceRegistryError,
    approve_candidate,
    block_candidate,
    candidate_counts,
    list_candidates,
    list_registry_entries,
    reject_candidate,
)

router = APIRouter(prefix="/v1/scout")


class SourceReviewRequest(BaseModel):
    reason: str | None = None
    reviewed_by: str | None = None


class SourceApproveRequest(BaseModel):
    approved_by: str | None = None
    poll_interval_minutes: int | None = None


class SourceDiscoveryDebugRequest(BaseModel):
    limit: int = 50


def build_sources_response(settings) -> dict:
    registry = load_merged_registry(settings)
    db_sources = list_registry_entries(settings.database_path, status="active")
    sources = [
        {
            "source_uri": f"github://{source.owner}/{source.repo}/commits",
            "canonical_uri": f"github://{source.owner}/{source.repo}",
            "display_uri": f"github://{source.owner}/{source.repo}",
            "source_kind": "github_repo",
            "status": "active",
            "poll_interval_minutes": source.poll_interval_minutes,
            "source_origin": "merged",
            "poller_supported": True,
        }
        for source in registry.github_repos
    ]
    sources.extend(
        {
            "source_uri": str(source.url),
            "canonical_uri": str(source.url).rstrip("/"),
            "display_uri": str(source.url),
            "source_kind": "rss_feed",
            "status": "active",
            "poll_interval_minutes": source.poll_interval_minutes,
            "source_origin": "merged",
            "poller_supported": True,
        }
        for source in registry.rss_feeds
    )
    sources.extend(
        {
            "source_uri": str(source.url),
            "canonical_uri": str(source.url).rstrip("/"),
            "display_uri": str(source.url),
            "source_kind": "web_page",
            "status": "active",
            "poll_interval_minutes": source.poll_interval_minutes,
            "source_origin": "merged",
            "poller_supported": False,
        }
        for source in registry.web_pages
    )
    db_canonical = {source.canonical_uri for source in db_sources}
    for source in sources:
        source["source_origin"] = (
            "approved_registry" if source["canonical_uri"] in db_canonical else "static_config"
        )
    return {"count": len(sources), "sources": sources}


@router.get("/sources")
async def get_sources() -> dict:
    return build_sources_response(get_settings())


@router.get("/source-candidates")
async def get_source_candidates(
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict:
    if status is not None and status not in CANDIDATE_STATUSES:
        raise HTTPException(status_code=422, detail="unsupported source candidate status")
    settings = get_settings()
    return {
        "counts": candidate_counts(settings.database_path),
        "candidates": [
            asdict(candidate)
            for candidate in list_candidates(
                settings.database_path,
                status=status,
                limit=limit,
            )
        ],
    }


@router.post("/source-candidates/{candidate_id}/approve")
async def approve_source_candidate(
    candidate_id: str,
    request: SourceApproveRequest | None = None,
) -> dict:
    request = request or SourceApproveRequest()
    try:
        entry = approve_candidate(
            get_settings().database_path,
            candidate_id,
            approved_by=request.approved_by or "manual-review",
            poll_interval_minutes=request.poll_interval_minutes,
        )
        return {"source": asdict(entry)}
    except SourceRegistryError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/source-candidates/{candidate_id}/reject")
async def reject_source_candidate(
    candidate_id: str,
    request: SourceReviewRequest,
) -> dict:
    try:
        candidate = reject_candidate(
            get_settings().database_path,
            candidate_id,
            reason=request.reason or "Rejected during manual Scout source review.",
            reviewed_by=request.reviewed_by or "manual-review",
        )
        return {"candidate": asdict(candidate)}
    except SourceRegistryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/source-discovery/run-debug")
async def run_source_discovery_debug(request: SourceDiscoveryDebugRequest) -> dict:
    return run_artifact_discovery(get_settings(), limit=request.limit)


@router.post("/source-candidates/{candidate_id}/block")
async def block_source_candidate(
    candidate_id: str,
    request: SourceReviewRequest,
) -> dict:
    try:
        candidate = block_candidate(
            get_settings().database_path,
            candidate_id,
            reason=request.reason or "Blocked during manual Scout source review.",
            blocked_by=request.reviewed_by or "manual-review",
        )
        return {"candidate": asdict(candidate)}
    except SourceRegistryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
