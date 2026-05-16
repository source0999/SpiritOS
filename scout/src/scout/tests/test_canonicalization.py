from scout.sources.discovery import extract_candidate_urls
from scout.sources.search import normalize_search_sources
from scout.sources.search_candidates import create_candidates_from_search_result
from scout.sources.discovery_jobs import create_discovery_job
from scout.sources.search import SearchResult, SearchSource
from scout.sources.storage import (
    approve_candidate,
    canonicalize_uri,
    list_candidates,
    upsert_candidate,
)
from scout.storage.migrations import apply_migrations


def _db_path(tmp_path):
    db_path = tmp_path / "scout.db"
    apply_migrations(db_path)
    return db_path


def test_canonicalize_uri_hardens_messy_github_repo_urls():
    messy_urls = [
        "https://github.com/FastAPI/FastAPI",
        "https://github.com/FastAPI/FastAPI/",
        "https://github.com/FastAPI/FastAPI.git",
        "https://github.com/FastAPI/FastAPI/issues/123?utm_source=x",
        "https://github.com/FastAPI/FastAPI/tree/main/docs#readme",
        "http://github.com/FastAPI/FastAPI?ref=nav",
        "github://FastAPI/FastAPI/commits/main",
    ]

    assert {canonicalize_uri(url) for url in messy_urls} == {
        "github://fastapi/fastapi"
    }


def test_canonicalize_uri_strips_tracking_default_ports_and_fragments():
    assert canonicalize_uri(
        "https://Example.com:443/docs/?utm_source=x&ref=nav&lang=en#intro"
    ) == "https://example.com/docs?lang=en"
    assert canonicalize_uri(
        "http://example.com:80/docs/?b=2&a=1&utm_campaign=x"
    ) == "http://example.com/docs?a=1&b=2"
    assert canonicalize_uri(
        "https://docs.python.org:443/3/whatsnew/?WT.mc_id=abc&view=reader"
    ) == "https://docs.python.org/3/whatsnew?view=reader"


def test_canonicalize_uri_upgrades_known_safe_http_hosts_only():
    assert (
        canonicalize_uri("http://fastapi.tiangolo.com/release-notes/")
        == "https://fastapi.tiangolo.com/release-notes"
    )
    assert (
        canonicalize_uri("http://unknown.example/release-notes/")
        == "http://unknown.example/release-notes"
    )


def test_artifact_and_search_paths_share_canonical_dedupe_rules(tmp_path):
    db_path = _db_path(tmp_path)
    job = create_discovery_job(db_path, query="official FastAPI release notes")
    artifact_urls = extract_candidate_urls(
        """
        [FastAPI](https://github.com/FastAPI/FastAPI/issues/123?utm_source=feed)
        [Docs](https://fastapi.tiangolo.com/release-notes/?utm_campaign=x)
        """
    )
    result = SearchResult(
        ok=True,
        searched=True,
        provider="searxng",
        query=job.query,
        elapsed_ms=1,
        sources=[
            SearchSource(
                title="FastAPI Repo",
                url="https://github.com/fastapi/fastapi/tree/main",
            ),
            SearchSource(
                title="FastAPI Release Notes",
                url="http://fastapi.tiangolo.com/release-notes/#latest",
            ),
        ],
    )

    for item in artifact_urls:
        upsert_candidate(
            db_path,
            display_uri=item.raw_url,
            canonical_uri=item.canonical_uri,
            source_kind=item.source_kind,
        )
    extraction = create_candidates_from_search_result(db_path, job=job, result=result)

    assert extraction.candidates_seen == 2
    assert extraction.candidates_created == 0
    assert {candidate.canonical_uri for candidate in list_candidates(db_path)} == {
        "github://fastapi/fastapi",
        "https://fastapi.tiangolo.com/release-notes",
    }


def test_search_normalizer_and_candidate_extraction_dedupe_active_sources(tmp_path):
    db_path = _db_path(tmp_path)
    active = upsert_candidate(
        db_path,
        display_uri="https://github.com/fastapi/fastapi",
        source_kind="github_repo",
    )
    approve_candidate(db_path, active.candidate_id, approved_by="tester")
    job = create_discovery_job(db_path, query="FastAPI")
    sources = normalize_search_sources(
        [
            {"title": "Repo", "url": "https://github.com/FastAPI/FastAPI/issues"},
            {"title": "Repo duplicate", "url": "https://github.com/fastapi/fastapi"},
        ],
        max_results=10,
    )
    result = SearchResult(
        ok=True,
        searched=True,
        provider="searxng",
        query=job.query,
        elapsed_ms=1,
        sources=sources,
    )

    extraction = create_candidates_from_search_result(db_path, job=job, result=result)

    assert extraction.candidates_seen == 0
    assert extraction.candidates_created == 0
    assert extraction.skipped_results == 2
