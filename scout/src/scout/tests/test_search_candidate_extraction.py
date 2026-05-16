from scout.sources.discovery_jobs import create_discovery_job
from scout.sources.search import SearchResult, SearchSource
from scout.sources.search_candidates import create_candidates_from_search_result
from scout.sources.storage import approve_candidate, candidate_counts, upsert_candidate
from scout.storage.db import open_connection
from scout.storage.migrations import apply_migrations


def _db_path(tmp_path):
    db_path = tmp_path / "scout.db"
    apply_migrations(db_path)
    return db_path


def test_search_result_extraction_creates_scored_candidates_with_provenance(tmp_path):
    db_path = _db_path(tmp_path)
    job = create_discovery_job(
        db_path,
        query="official FastAPI release notes",
        topic_anchor="FastAPI",
        max_results=5,
    )
    result = SearchResult(
        ok=True,
        searched=True,
        provider="searxng",
        query=job.query,
        elapsed_ms=1,
        sources=[
            SearchSource(
                title="FastAPI Release Notes",
                url="https://fastapi.tiangolo.com/release-notes/?utm_source=x",
                snippet="Release notes",
            ),
            SearchSource(
                title="FastAPI GitHub",
                url="https://github.com/fastapi/fastapi",
            ),
        ],
    )

    extraction = create_candidates_from_search_result(db_path, job=job, result=result)

    assert extraction.candidates_seen == 2
    assert extraction.candidates_created == 2
    assert extraction.discovery_events == 2
    assert extraction.skipped_results == 0
    counts = candidate_counts(db_path)
    assert counts["recommended"] >= 1
    conn = open_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT canonical_uri, discovered_from_uri, reason_codes_json, metadata_json
            FROM source_candidates
            ORDER BY canonical_uri
            """
        ).fetchall()
        events = conn.execute(
            "SELECT discovery_kind, source_uri FROM source_discovery_events"
        ).fetchall()
    finally:
        conn.close()
    assert {row["canonical_uri"] for row in rows} == {
        "github://fastapi/fastapi",
        "https://fastapi.tiangolo.com/release-notes",
    }
    assert all(row["discovered_from_uri"] == f"search://{job.job_id}" for row in rows)
    assert all("discovered_from_search_result" in row["reason_codes_json"] for row in rows)
    assert all(job.job_id in row["metadata_json"] for row in rows)
    assert {row["discovery_kind"] for row in events} == {"search_result"}


def test_search_result_extraction_dedupes_existing_candidates(tmp_path):
    db_path = _db_path(tmp_path)
    job = create_discovery_job(db_path, query="official Python release notes")
    upsert_candidate(
        db_path,
        display_uri="https://blog.python.org/2024/10/python-3130-final-released/",
        source_kind="blog",
    )
    result = SearchResult(
        ok=True,
        searched=True,
        provider="searxng",
        query=job.query,
        elapsed_ms=1,
        sources=[
            SearchSource(
                title="Python 3.13",
                url="https://blog.python.org/2024/10/python-3130-final-released",
            )
        ],
    )

    extraction = create_candidates_from_search_result(db_path, job=job, result=result)

    assert extraction.candidates_seen == 1
    assert extraction.candidates_created == 0


def test_search_result_extraction_skips_already_active_sources(tmp_path):
    db_path = _db_path(tmp_path)
    job = create_discovery_job(db_path, query="FastAPI repo")
    candidate = upsert_candidate(
        db_path,
        display_uri="https://github.com/fastapi/fastapi",
        source_kind="github_repo",
    )
    approve_candidate(db_path, candidate.candidate_id, approved_by="tester")
    result = SearchResult(
        ok=True,
        searched=True,
        provider="searxng",
        query=job.query,
        elapsed_ms=1,
        sources=[SearchSource(title="FastAPI", url="https://github.com/fastapi/fastapi")],
    )

    extraction = create_candidates_from_search_result(db_path, job=job, result=result)

    assert extraction.candidates_seen == 0
    assert extraction.candidates_created == 0
    assert extraction.skipped_results == 1


def test_search_result_extraction_reports_provider_failure_without_candidates(tmp_path):
    db_path = _db_path(tmp_path)
    job = create_discovery_job(db_path, query="FastAPI repo")
    result = SearchResult(
        ok=False,
        searched=True,
        provider="searxng",
        elapsed_ms=1,
        error="searxng_unreachable",
        detail="down",
    )

    extraction = create_candidates_from_search_result(db_path, job=job, result=result)

    assert extraction.candidates_seen == 0
    assert extraction.errors == [
        {"provider": "searxng", "error": "searxng_unreachable", "detail": "down"}
    ]
    assert all(value == 0 for value in candidate_counts(db_path).values())
