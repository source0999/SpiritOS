from scout.sources.discovery_jobs import create_discovery_job
from scout.sources.search import SearchResult, SearchSource
from scout.sources.search_candidates import create_candidates_from_search_result
from scout.sources.storage import candidate_counts, list_candidates, list_registry_entries
from scout.storage.db import open_connection
from scout.storage.migrations import apply_migrations


def _db_path(tmp_path):
    db_path = tmp_path / "scout.db"
    apply_migrations(db_path)
    return db_path


def test_repeated_bounded_discovery_keeps_candidates_deduped_and_inactive(tmp_path):
    db_path = _db_path(tmp_path)
    result_sources = [
        SearchSource(
            title="FastAPI release notes",
            url="https://fastapi.tiangolo.com/release-notes/?utm_source=search",
        ),
        SearchSource(
            title="FastAPI repo",
            url="https://github.com/FastAPI/FastAPI/issues/123",
        ),
        SearchSource(
            title="Python release",
            url="https://blog.python.org/2024/10/python-3130-final-released/",
        ),
    ]

    for index in range(3):
        job = create_discovery_job(
            db_path,
            query=f"official release notes soak {index}",
            max_results=3,
            budget=3,
            max_jobs_per_day=3,
        )
        extraction = create_candidates_from_search_result(
            db_path,
            job=job,
            result=SearchResult(
                ok=True,
                searched=True,
                provider="searxng",
                query=job.query,
                elapsed_ms=1,
                sources=result_sources,
            ),
        )
        assert extraction.candidates_seen == 3

    candidates = list_candidates(db_path, limit=20)
    counts = candidate_counts(db_path)
    registry = list_registry_entries(db_path, status="active")
    conn = open_connection(db_path)
    try:
        discovery_event_count = conn.execute(
            "SELECT COUNT(*) AS count FROM source_discovery_events"
        ).fetchone()["count"]
        review_event_count = conn.execute(
            "SELECT COUNT(*) AS count FROM source_review_events"
        ).fetchone()["count"]
    finally:
        conn.close()

    assert {candidate.canonical_uri for candidate in candidates} == {
        "github://fastapi/fastapi",
        "https://blog.python.org/2024/10/python-3130-final-released",
        "https://fastapi.tiangolo.com/release-notes",
    }
    assert len(candidates) == 3
    assert counts["approved"] == 0
    assert registry == []
    assert discovery_event_count == 9
    assert review_event_count == 0
