from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import scout.api.discovery_jobs as discovery_jobs_api
from scout.api.discovery_jobs import router
from scout.config import ScoutSettings
from scout.sources.discovery_jobs import (
    DiscoveryJobError,
    classify_discovery_job_states,
    create_discovery_job,
    finish_discovery_job,
    get_discovery_job_budget,
    list_discovery_jobs,
    mark_discovery_job_started,
    pause_discovery_job,
    resume_discovery_job,
)
from scout.sources.storage import candidate_counts
from scout.storage.db import init_database
from scout.storage.db import open_connection
from scout.storage.migrations import apply_migrations


def _settings(tmp_path) -> ScoutSettings:
    settings = ScoutSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "scout.db",
        discovery_jobs_per_day=10,
        search_enabled=False,
        searxng_url=None,
    )
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    return settings


def _client(tmp_path, monkeypatch) -> tuple[TestClient, ScoutSettings]:
    settings = _settings(tmp_path)
    monkeypatch.setattr(discovery_jobs_api, "get_settings", lambda: settings)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app), settings


def test_create_list_pause_and_resume_discovery_job(tmp_path):
    settings = _settings(tmp_path)

    job = create_discovery_job(
        settings.database_path,
        query="official FastAPI release notes",
        topic_anchor="FastAPI",
        max_results=5,
        budget=4,
        metadata={"source": "manual"},
    )
    paused = pause_discovery_job(settings.database_path, job.job_id)
    resumed = resume_discovery_job(settings.database_path, job.job_id)
    jobs = list_discovery_jobs(settings.database_path)

    assert job.status == "queued"
    assert job.query == "official FastAPI release notes"
    assert job.topic_anchor == "FastAPI"
    assert job.max_results == 5
    assert job.budget == 4
    assert job.metadata == {"source": "manual"}
    assert paused.status == "paused"
    assert resumed.status == "queued"
    assert [item.job_id for item in jobs] == [job.job_id]


def test_discovery_job_transitions_are_guarded(tmp_path):
    settings = _settings(tmp_path)
    job = create_discovery_job(settings.database_path, query="official Python changelog")
    pause_discovery_job(settings.database_path, job.job_id)

    with pytest.raises(DiscoveryJobError, match="not queued"):
        mark_discovery_job_started(settings.database_path, job.job_id)

    resumed = resume_discovery_job(settings.database_path, job.job_id)
    running = mark_discovery_job_started(settings.database_path, resumed.job_id)
    completed = finish_discovery_job(settings.database_path, running.job_id)

    assert running.status == "running"
    assert running.started_at is not None
    assert completed.status == "completed"
    assert completed.finished_at is not None


def test_discovery_job_planner_does_not_create_candidates(tmp_path):
    settings = _settings(tmp_path)

    create_discovery_job(settings.database_path, query="official sqlite release notes")

    assert candidate_counts(settings.database_path) == {
        "recommended": 0,
        "needs_review": 0,
        "stored": 0,
        "rejected": 0,
        "blocked": 0,
        "approved": 0,
    }


def test_discovery_job_creation_respects_daily_limit(tmp_path):
    settings = _settings(tmp_path)
    create_discovery_job(
        settings.database_path,
        query="official FastAPI docs",
        max_jobs_per_day=1,
    )

    with pytest.raises(DiscoveryJobError, match="daily limit"):
        create_discovery_job(
            settings.database_path,
            query="official Python docs",
            max_jobs_per_day=1,
        )


def test_discovery_job_budget_reports_daily_limit_and_status_counts(tmp_path):
    settings = _settings(tmp_path)
    first = create_discovery_job(
        settings.database_path,
        query="official FastAPI docs",
        max_jobs_per_day=3,
    )
    second = create_discovery_job(
        settings.database_path,
        query="official Python docs",
        max_jobs_per_day=3,
    )
    pause_discovery_job(settings.database_path, second.job_id)
    running = mark_discovery_job_started(settings.database_path, first.job_id)
    finish_discovery_job(settings.database_path, running.job_id)

    budget = get_discovery_job_budget(settings.database_path, max_jobs_per_day=3)

    assert budget.daily_limit == 3
    assert budget.used_today == 2
    assert budget.remaining_today == 1
    assert budget.can_create_job is True
    assert budget.blocked_reason is None
    assert budget.next_reset_hint == "next UTC day"
    assert budget.queued_jobs == 0
    assert budget.running_jobs == 0
    assert budget.completed_jobs == 1
    assert budget.failed_jobs == 0


def test_discovery_job_budget_reports_daily_limit_reached(tmp_path):
    settings = _settings(tmp_path)
    create_discovery_job(
        settings.database_path,
        query="official FastAPI docs",
        max_jobs_per_day=1,
    )

    budget = get_discovery_job_budget(settings.database_path, max_jobs_per_day=1)

    assert budget.daily_limit == 1
    assert budget.used_today == 1
    assert budget.remaining_today == 0
    assert budget.can_create_job is False
    assert budget.blocked_reason == "daily_limit_reached"
    assert budget.queued_jobs == 1


def test_discovery_job_computed_states_classify_duplicates_spam_and_stale(tmp_path):
    settings = _settings(tmp_path)
    duplicate_a = create_discovery_job(
        settings.database_path,
        query=" official   Pydantic GitHub repository release notes ",
        topic_anchor="Python",
    )
    duplicate_b = create_discovery_job(
        settings.database_path,
        query="official pydantic github repository release notes",
        topic_anchor="python",
    )
    spam = create_discovery_job(
        settings.database_path,
        query="fastapi free download coupon crack tutorial mirror spam",
        topic_anchor="fastapi",
    )
    stale = create_discovery_job(
        settings.database_path,
        query="official FastAPI release notes",
        topic_anchor="FastAPI",
    )
    old_timestamp = (datetime.now(timezone.utc) - timedelta(hours=7)).isoformat()
    conn = open_connection(settings.database_path)
    try:
        conn.execute(
            """
            UPDATE discovery_jobs
            SET created_at = ?, updated_at = ?
            WHERE job_id = ?
            """,
            (old_timestamp, old_timestamp, stale.job_id),
        )
        conn.commit()
    finally:
        conn.close()

    jobs = list_discovery_jobs(settings.database_path, limit=10)
    budget = get_discovery_job_budget(settings.database_path, max_jobs_per_day=10)
    states = classify_discovery_job_states(jobs, budget=budget)

    assert states[duplicate_a.job_id].computed_status == "duplicate_queued"
    assert states[duplicate_b.job_id].computed_status == "duplicate_queued"
    assert states[spam.job_id].computed_status == "spam_test"
    assert states[stale.job_id].computed_status == "stale_queued"
    assert states[duplicate_a.job_id].safe_next_action == "cancel_duplicate_or_wait"
    assert states[spam.job_id].attention_label == "Noisy test search"


def test_discovery_jobs_api_create_list_pause_and_resume(tmp_path, monkeypatch):
    client, _settings = _client(tmp_path, monkeypatch)

    created = client.post(
        "/v1/scout/discovery-jobs",
        json={
            "query": "official FastAPI release notes",
            "topic_anchor": "FastAPI",
            "max_results": 5,
            "budget": 5,
        },
    )
    job_id = created.json()["job"]["job_id"]
    paused = client.post(f"/v1/scout/discovery-jobs/{job_id}/pause")
    resumed = client.post(f"/v1/scout/discovery-jobs/{job_id}/resume")
    listed = client.get("/v1/scout/discovery-jobs")

    assert created.status_code == 201
    assert created.json()["job"]["status"] == "queued"
    assert paused.json()["job"]["status"] == "paused"
    assert resumed.json()["job"]["status"] == "queued"
    assert listed.json()["count"] == 1
    assert listed.json()["budget"] == {
        "daily_limit": 10,
        "used_today": 1,
        "remaining_today": 9,
        "can_create_job": True,
        "blocked_reason": None,
        "next_reset_hint": "next UTC day",
        "queued_jobs": 1,
        "running_jobs": 0,
        "completed_jobs": 0,
        "failed_jobs": 0,
    }
    assert listed.json()["execution"] == {
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
    assert listed.json()["jobs"][0]["job_id"] == job_id
    assert listed.json()["jobs"][0]["computed_status"] == "queued"
    assert listed.json()["jobs"][0]["attention_label"] is None
    assert listed.json()["jobs"][0]["safe_next_action"] == "wait_for_worker"


def test_discovery_jobs_api_respects_global_pause(tmp_path, monkeypatch):
    client, settings = _client(tmp_path, monkeypatch)
    settings.discovery_jobs_enabled = False

    response = client.post(
        "/v1/scout/discovery-jobs",
        json={"query": "official FastAPI release notes"},
    )

    assert response.status_code == 409
    assert "disabled" in response.json()["detail"]


def test_discovery_jobs_api_respects_daily_limit(tmp_path, monkeypatch):
    client, settings = _client(tmp_path, monkeypatch)
    settings.discovery_jobs_per_day = 1

    first = client.post(
        "/v1/scout/discovery-jobs",
        json={"query": "official FastAPI release notes"},
    )
    second = client.post(
        "/v1/scout/discovery-jobs",
        json={"query": "official Python release notes"},
    )

    assert first.status_code == 201
    assert second.status_code == 422
    assert "daily limit" in second.json()["detail"]

    listed = client.get("/v1/scout/discovery-jobs")

    assert listed.json()["budget"]["daily_limit"] == 1
    assert listed.json()["budget"]["used_today"] == 1
    assert listed.json()["budget"]["remaining_today"] == 0
    assert listed.json()["budget"]["can_create_job"] is False
    assert listed.json()["budget"]["blocked_reason"] == "daily_limit_reached"


def test_discovery_jobs_api_rejects_invalid_status_filter(tmp_path, monkeypatch):
    client, _settings = _client(tmp_path, monkeypatch)

    response = client.get("/v1/scout/discovery-jobs", params={"status": "searching"})

    assert response.status_code == 422


def test_discovery_job_search_preview_is_disabled_by_default(tmp_path, monkeypatch):
    client, settings = _client(tmp_path, monkeypatch)
    job = create_discovery_job(settings.database_path, query="official FastAPI docs")

    response = client.post(f"/v1/scout/discovery-jobs/{job.job_id}/search-preview")

    assert response.status_code == 409
    assert "disabled" in response.json()["detail"]


def test_discovery_job_search_preview_returns_provider_result_without_candidates(
    tmp_path,
    monkeypatch,
):
    client, settings = _client(tmp_path, monkeypatch)
    job = create_discovery_job(settings.database_path, query="official FastAPI docs")
    settings.search_enabled = True
    settings.searxng_url = "http://127.0.0.1:8080"
    settings.search_max_results = 10
    settings.discovery_candidates_per_job = 1

    seen_kwargs = {}

    def fake_search(**kwargs):
        from scout.sources.search import SearchResult, SearchSource

        seen_kwargs.update(kwargs)
        return SearchResult(
            ok=True,
            searched=True,
            provider="searxng",
            query="official FastAPI docs",
            elapsed_ms=1,
            sources=[
                SearchSource(
                    title="FastAPI Docs",
                    url="https://fastapi.tiangolo.com",
                )
            ],
        )

    monkeypatch.setattr(discovery_jobs_api, "run_searxng_search", fake_search)

    response = client.post(f"/v1/scout/discovery-jobs/{job.job_id}/search-preview")

    assert response.status_code == 200
    assert response.json()["candidate_effect"] == "none"
    assert response.json()["bounds"] == {
        "effective_result_limit": 1,
        "job_max_results": 10,
        "job_budget": 10,
        "search_max_results": 10,
        "discovery_candidates_per_job": 1,
        "manual_activation_required": True,
        "automatic_activation": False,
    }
    assert response.json()["result"]["sources"][0]["url"] == (
        "https://fastapi.tiangolo.com"
    )
    assert seen_kwargs["max_results"] == 1
    assert candidate_counts(settings.database_path) == {
        "recommended": 0,
        "needs_review": 0,
        "stored": 0,
        "rejected": 0,
        "blocked": 0,
        "approved": 0,
    }


def test_discovery_job_extract_candidates_creates_reviewable_candidates(
    tmp_path,
    monkeypatch,
):
    client, settings = _client(tmp_path, monkeypatch)
    job = create_discovery_job(settings.database_path, query="official FastAPI docs")
    settings.search_enabled = True
    settings.searxng_url = "http://127.0.0.1:8080"

    def fake_search(**_kwargs):
        from scout.sources.search import SearchResult, SearchSource

        return SearchResult(
            ok=True,
            searched=True,
            provider="searxng",
            query="official FastAPI docs",
            elapsed_ms=1,
            sources=[
                SearchSource(
                    title="FastAPI Docs",
                    url="https://fastapi.tiangolo.com/release-notes/",
                )
            ],
        )

    monkeypatch.setattr(discovery_jobs_api, "run_searxng_search", fake_search)

    response = client.post(f"/v1/scout/discovery-jobs/{job.job_id}/extract-candidates")

    assert response.status_code == 200
    assert response.json()["candidate_effect"] == "created_or_updated"
    assert response.json()["extraction"]["candidates_created"] == 1
    counts = candidate_counts(settings.database_path)
    assert counts["recommended"] == 1
    assert counts["approved"] == 0


def test_discovery_job_extract_candidates_caps_provider_overflow_and_reports_bounds(
    tmp_path,
    monkeypatch,
):
    client, settings = _client(tmp_path, monkeypatch)
    job = create_discovery_job(
        settings.database_path,
        query="official Python project docs",
        max_results=5,
        budget=4,
    )
    settings.search_enabled = True
    settings.searxng_url = "http://127.0.0.1:8080"
    settings.search_max_results = 10
    settings.discovery_candidates_per_job = 2
    seen_kwargs = {}

    def fake_search(**kwargs):
        from scout.sources.search import SearchResult, SearchSource

        seen_kwargs.update(kwargs)
        return SearchResult(
            ok=True,
            searched=True,
            provider="searxng",
            query="official Python project docs",
            elapsed_ms=1,
            sources=[
                SearchSource(title="FastAPI", url="https://github.com/fastapi/fastapi"),
                SearchSource(title="Pydantic", url="https://github.com/pydantic/pydantic"),
                SearchSource(title="Starlette", url="https://github.com/encode/starlette"),
            ],
        )

    monkeypatch.setattr(discovery_jobs_api, "run_searxng_search", fake_search)

    response = client.post(f"/v1/scout/discovery-jobs/{job.job_id}/extract-candidates")

    assert response.status_code == 200
    assert seen_kwargs["max_results"] == 2
    assert response.json()["bounds"] == {
        "effective_result_limit": 2,
        "job_max_results": 5,
        "job_budget": 4,
        "search_max_results": 10,
        "discovery_candidates_per_job": 2,
        "manual_activation_required": True,
        "automatic_activation": False,
    }
    assert response.json()["extraction"]["candidate_limit"] == 2
    assert response.json()["extraction"]["skipped_by_limit"] == 1
    assert response.json()["extraction"]["activation_policy"] == "manual_review_required"
    counts = candidate_counts(settings.database_path)
    assert sum(counts.values()) == 2
    assert counts["approved"] == 0

    conn = open_connection(settings.database_path)
    try:
        active_count = conn.execute(
            "SELECT COUNT(*) AS count FROM source_registry WHERE status = 'active'"
        ).fetchone()["count"]
        event_rows = conn.execute(
            "SELECT metadata_json FROM source_discovery_events ORDER BY canonical_uri"
        ).fetchall()
    finally:
        conn.close()

    assert active_count == 0
    assert len(event_rows) == 2
    assert all('"candidate_limit": 2' in row["metadata_json"] for row in event_rows)


def test_discovery_job_extract_candidates_requires_queued_job(tmp_path, monkeypatch):
    client, settings = _client(tmp_path, monkeypatch)
    job = create_discovery_job(settings.database_path, query="official FastAPI docs")
    pause_discovery_job(settings.database_path, job.job_id)
    settings.search_enabled = True
    settings.searxng_url = "http://127.0.0.1:8080"

    response = client.post(f"/v1/scout/discovery-jobs/{job.job_id}/extract-candidates")

    assert response.status_code == 409
    assert "not queued" in response.json()["detail"]
