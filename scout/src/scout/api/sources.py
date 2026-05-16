from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from scout.config import get_settings
from scout.pollers.registry import load_merged_registry
from scout.sources.discovery import run_artifact_discovery
from scout.sources.scoring import auto_approval_dry_run, rank_source_candidate
from scout.sources.storage import (
    CANDIDATE_STATUSES,
    SourceRegistryError,
    approve_candidate,
    block_candidate,
    candidate_counts,
    get_candidate,
    list_candidates,
    list_registry_entries,
    list_review_events,
    reject_candidate,
)

router = APIRouter(prefix="/v1/scout")


SOURCE_REVIEW_BUNDLES = {
    "official_github_repos": {
        "label": "Official GitHub repos",
        "description": "High-confidence GitHub repositories with official project signals.",
    },
    "official_docs": {
        "label": "Official docs",
        "description": "Documentation pages with official domain or docs-path signals.",
    },
    "release_notes": {
        "label": "Release notes",
        "description": "Changelogs and release pages worth checking for updates.",
    },
    "known_ecosystem_blogs": {
        "label": "Known ecosystem blogs",
        "description": "Known project or ecosystem sources that still need human review.",
    },
    "needs_review": {
        "label": "Needs review",
        "description": "Useful-looking sources without enough evidence for low-risk grouping.",
    },
    "block_suggested": {
        "label": "Block suggested",
        "description": "Noisy or blocked candidates that may deserve rejection or blocking.",
    },
}


class SourceReviewRequest(BaseModel):
    reason: str | None = None
    reviewed_by: str | None = None


class SourceApproveRequest(BaseModel):
    approved_by: str | None = None
    poll_interval_minutes: int | None = None


class SourceBatchApproveRequest(BaseModel):
    candidate_ids: list[str]
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


def source_candidate_to_dict(settings, candidate) -> dict:
    body = asdict(candidate)
    rank = rank_source_candidate(
        status=candidate.status,
        confidence_score=candidate.confidence_score,
        reason_codes=candidate.reason_codes,
        trust_tier=candidate.trust_tier,
    )
    body["automation_tier"] = rank.automation_tier
    body["automation_label"] = rank.automation_label
    body["suggested_action"] = rank.suggested_action
    dry_run = auto_approval_dry_run(
        status=candidate.status,
        confidence_score=candidate.confidence_score,
        source_kind=candidate.source_kind,
        reason_codes=candidate.reason_codes,
        trust_tier=candidate.trust_tier,
    )
    body["auto_approval_dry_run"] = dry_run.eligible
    body["auto_approval_dry_run_reason"] = dry_run.reason
    body["auto_approval_dry_run_label"] = dry_run.label
    body["review_history"] = [
        asdict(event)
        for event in list_review_events(
            settings.database_path,
            candidate_id=candidate.candidate_id,
            limit=20,
        )
    ]
    return body


def source_review_bundles(candidates: list[dict]) -> list[dict]:
    buckets = {
        key: {
            "key": key,
            "label": config["label"],
            "description": config["description"],
            "count": 0,
            "candidate_ids": [],
        }
        for key, config in SOURCE_REVIEW_BUNDLES.items()
    }
    for candidate in candidates:
        key = _source_review_bundle_key(candidate)
        buckets[key]["count"] += 1
        buckets[key]["candidate_ids"].append(candidate["candidate_id"])
    return [bundle for bundle in buckets.values() if bundle["count"] > 0]


def _source_review_bundle_key(candidate: dict) -> str:
    reason_codes = set(candidate.get("reason_codes") or [])
    source_kind = str(candidate.get("source_kind") or "")
    automation_tier = str(candidate.get("automation_tier") or "")
    if automation_tier in {"noisy", "block_candidate_suggested"}:
        return "block_suggested"
    if source_kind == "github_repo" and (
        candidate.get("trust_tier") == "official" or "official_repo_pattern" in reason_codes
    ):
        return "official_github_repos"
    if "official_docs_pattern" in reason_codes or source_kind == "docs_page":
        return "official_docs"
    if "release_notes_pattern" in reason_codes or source_kind in {"changelog", "release_feed"}:
        return "release_notes"
    if "known_ecosystem_match" in reason_codes:
        return "known_ecosystem_blogs"
    return "needs_review"


def _latest_review_event(candidate_body: dict) -> dict | None:
    history = candidate_body.get("review_history")
    if isinstance(history, list) and history:
        latest = history[0]
        return latest if isinstance(latest, dict) else None
    return None


def _poller_supported_for_source(source_body: dict | None) -> bool | None:
    if not source_body:
        return None
    source_kind = str(source_body.get("source_kind") or "")
    return source_kind in {"github_repo", "rss_feed"}


def _action_message(action: str, *, source_body: dict | None = None) -> str:
    if action == "approve" and source_body:
        supported = _poller_supported_for_source(source_body)
        if supported is False:
            return "Source candidate approved; source is active but has no poller support."
        return "Source candidate approved."
    if action == "reject":
        return "Source candidate rejected."
    if action == "block":
        return "Source candidate blocked."
    return f"Source candidate {action} completed."


def _action_warnings(action: str, *, source_body: dict | None = None) -> list[str]:
    warnings: list[str] = []
    if action == "approve" and _poller_supported_for_source(source_body) is False:
        warnings.append("approved source is active but poller_supported is false")
    return warnings


def normalized_action_result(
    *,
    action: str,
    candidate_body: dict | None = None,
    source_body: dict | None = None,
) -> dict:
    return {
        "ok": True,
        "action": action,
        "candidate": candidate_body,
        "source": source_body,
        "review_event": _latest_review_event(candidate_body or {}),
        "message": _action_message(action, source_body=source_body),
        "poller_supported": _poller_supported_for_source(source_body),
        "warnings": _action_warnings(action, source_body=source_body),
    }


def _source_entry_to_dict(source) -> dict:
    return asdict(source) if source is not None else None


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
    candidates = [
        source_candidate_to_dict(settings, candidate)
        for candidate in list_candidates(
            settings.database_path,
            status=status,
            limit=limit,
        )
    ]
    return {
        "counts": candidate_counts(settings.database_path),
        "review_bundles": source_review_bundles(candidates),
        "candidates": candidates,
    }


@router.post("/source-candidates/batch-approve")
async def batch_approve_source_candidates(request: SourceBatchApproveRequest) -> dict:
    candidate_ids = list(dict.fromkeys(request.candidate_ids))
    if not candidate_ids:
        raise HTTPException(status_code=422, detail="candidate_ids is required")

    settings = get_settings()
    selected = []
    for candidate_id in candidate_ids:
        try:
            candidate = get_candidate(settings.database_path, candidate_id)
        except SourceRegistryError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        rank = rank_source_candidate(
            status=candidate.status,
            confidence_score=candidate.confidence_score,
            reason_codes=candidate.reason_codes,
            trust_tier=candidate.trust_tier,
        )
        if candidate.status in {"blocked", "rejected", "approved"}:
            raise HTTPException(
                status_code=409,
                detail=f"candidate {candidate_id} cannot be batch approved from status {candidate.status}",
            )
        if rank.automation_tier != "low_risk_recommended":
            raise HTTPException(
                status_code=409,
                detail=f"candidate {candidate_id} is not low-risk recommended",
            )
        selected.append(candidate)

    approved = []
    warnings: list[str] = []
    for candidate in selected:
        try:
            source = approve_candidate(
                settings.database_path,
                candidate.candidate_id,
                approved_by=request.approved_by or "manual-review",
                poll_interval_minutes=request.poll_interval_minutes,
            )
        except SourceRegistryError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        source_body = _source_entry_to_dict(source)
        if _poller_supported_for_source(source_body) is False:
            warnings.append(
                f"{candidate.canonical_uri}: approved source is active but poller_supported is false"
            )
        approved.append(
            {
                "candidate_id": candidate.candidate_id,
                "canonical_uri": candidate.canonical_uri,
                "source": source_body,
            }
        )

    return {
        "ok": True,
        "action": "batch_approve",
        "requested": len(candidate_ids),
        "approved_count": len(approved),
        "approved": approved,
        "warnings": warnings,
        "message": f"{len(approved)} source candidate{'s' if len(approved) != 1 else ''} approved.",
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
        source_body = asdict(entry)
        return normalized_action_result(action="approve", source_body=source_body)
    except SourceRegistryError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/source-candidates/{candidate_id}/reject")
async def reject_source_candidate(
    candidate_id: str,
    request: SourceReviewRequest,
) -> dict:
    settings = get_settings()
    try:
        candidate = reject_candidate(
            settings.database_path,
            candidate_id,
            reason=request.reason or "Rejected during manual Scout source review.",
            reviewed_by=request.reviewed_by or "manual-review",
        )
        candidate_body = source_candidate_to_dict(settings, candidate)
        return normalized_action_result(action="reject", candidate_body=candidate_body)
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
    settings = get_settings()
    try:
        candidate = block_candidate(
            settings.database_path,
            candidate_id,
            reason=request.reason or "Blocked during manual Scout source review.",
            blocked_by=request.reviewed_by or "manual-review",
        )
        candidate_body = source_candidate_to_dict(settings, candidate)
        return normalized_action_result(action="block", candidate_body=candidate_body)
    except SourceRegistryError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
