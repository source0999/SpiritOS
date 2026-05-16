from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scout.sources.discovery import classify_source_kind
from scout.sources.discovery_jobs import DiscoveryJob
from scout.sources.scoring import score_candidate
from scout.sources.search import SearchResult
from scout.sources.storage import canonicalize_uri, record_discovery_event, upsert_candidate
from scout.storage.db import open_connection


@dataclass(frozen=True)
class SearchCandidateExtraction:
    candidates_seen: int
    candidates_created: int
    discovery_events: int
    skipped_results: int
    candidate_limit: int
    skipped_by_limit: int
    errors: list[dict[str, Any]] = field(default_factory=list)


def create_candidates_from_search_result(
    db_path: Path,
    *,
    job: DiscoveryJob,
    result: SearchResult,
    max_candidates: int | None = None,
) -> SearchCandidateExtraction:
    candidate_limit = _candidate_limit(job, max_candidates=max_candidates)
    if not result.ok:
        return SearchCandidateExtraction(
            candidates_seen=0,
            candidates_created=0,
            discovery_events=0,
            skipped_results=0,
            candidate_limit=candidate_limit,
            skipped_by_limit=0,
            errors=[
                {
                    "provider": result.provider,
                    "error": result.error,
                    "detail": result.detail,
                }
            ],
        )

    candidates_seen = 0
    candidates_created = 0
    discovery_events = 0
    skipped_results = 0
    skipped_by_limit = 0
    errors: list[dict[str, Any]] = []
    discovery_source = f"search://{job.job_id}"
    seen_canonical_uris: set[str] = set()

    for source_index, source in enumerate(result.sources):
        if source_index >= candidate_limit:
            skipped_results += 1
            skipped_by_limit += 1
            continue
        try:
            canonical_uri = canonicalize_uri(source.url)
            if canonical_uri in seen_canonical_uris:
                skipped_results += 1
                continue
            seen_canonical_uris.add(canonical_uri)
            if _is_already_active(db_path, canonical_uri):
                skipped_results += 1
                continue
            source_kind = classify_source_kind(canonical_uri)
            before_exists = _candidate_exists(db_path, canonical_uri)
            score = score_candidate(
                db_path,
                canonical_uri=canonical_uri,
                source_kind=source_kind,
                discovered_from_uri=discovery_source,
                title=source.title,
                snippet=source.snippet,
                published_at=source.published_at,
            )
            candidate = upsert_candidate(
                db_path,
                display_uri=source.url,
                canonical_uri=canonical_uri,
                source_kind=source_kind,
                status=score.status,
                confidence_score=score.confidence_score,
                trust_label=score.trust_label,
                trust_tier=score.trust_tier,
                recommendation=score.recommendation,
                discovered_from_uri=discovery_source,
                reason_codes=["discovered_from_search_result"] + score.reason_codes,
                explanation=score.explanation,
                metadata={
                    "discovery_job_id": job.job_id,
                    "provider": source.provider,
                    "query": job.query,
                    "title": source.title,
                    "snippet": source.snippet,
                    "published_at": source.published_at,
                    "extraction_audit": _extraction_audit(
                        job,
                        candidate_limit=candidate_limit,
                        source_index=source_index,
                    ),
                },
            )
            record_discovery_event(
                db_path,
                candidate_id=candidate.candidate_id,
                discovery_kind="search_result",
                source_uri=discovery_source,
                raw_url=source.url,
                canonical_uri=canonical_uri,
                metadata={
                    "discovery_job_id": job.job_id,
                    "provider": source.provider,
                    "query": job.query,
                    "title": source.title,
                    "extraction_audit": _extraction_audit(
                        job,
                        candidate_limit=candidate_limit,
                        source_index=source_index,
                    ),
                },
            )
            candidates_seen += 1
            candidates_created += 0 if before_exists else 1
            discovery_events += 1
        except Exception as exc:
            skipped_results += 1
            errors.append({"url": source.url, "error": str(exc)})

    return SearchCandidateExtraction(
        candidates_seen=candidates_seen,
        candidates_created=candidates_created,
        discovery_events=discovery_events,
        skipped_results=skipped_results,
        candidate_limit=candidate_limit,
        skipped_by_limit=skipped_by_limit,
        errors=errors,
    )


def extraction_to_dict(extraction: SearchCandidateExtraction) -> dict[str, Any]:
    return {
        "candidates_seen": extraction.candidates_seen,
        "candidates_created": extraction.candidates_created,
        "discovery_events": extraction.discovery_events,
        "skipped_results": extraction.skipped_results,
        "candidate_limit": extraction.candidate_limit,
        "skipped_by_limit": extraction.skipped_by_limit,
        "activation_policy": "manual_review_required",
        "errors": extraction.errors,
    }


def _candidate_limit(job: DiscoveryJob, *, max_candidates: int | None) -> int:
    limits = [job.max_results, job.budget]
    if max_candidates is not None:
        limits.append(max_candidates)
    return max(1, min(limits))


def _extraction_audit(
    job: DiscoveryJob,
    *,
    candidate_limit: int,
    source_index: int,
) -> dict[str, Any]:
    return {
        "bounded": True,
        "candidate_limit": candidate_limit,
        "source_index": source_index,
        "job_max_results": job.max_results,
        "job_budget": job.budget,
        "activation_policy": "manual_review_required",
    }


def _is_already_active(db_path: Path, canonical_uri: str) -> bool:
    conn = open_connection(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM source_registry WHERE canonical_uri = ? AND status = 'active'",
            (canonical_uri,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def _candidate_exists(db_path: Path, canonical_uri: str) -> bool:
    conn = open_connection(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM source_candidates WHERE canonical_uri = ?",
            (canonical_uri,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()
