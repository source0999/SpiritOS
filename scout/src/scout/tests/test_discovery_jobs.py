import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import scout.api.discovery_jobs as discovery_jobs_api
from scout.api.discovery_jobs import router
from scout.config import ScoutSettings
from scout.sources.discovery_jobs import (
    DiscoveryJobError,
    create_discovery_job,
    finish_discovery_job,
    list_discovery_jobs,
    mark_discovery_job_started,
    pause_discovery_job,
    resume_discovery_job,
)
from scout.sources.storage import candidate_counts
from scout.storage.db import init_database
from scout.storage.migrations import apply_migrations


def _settings(tmp_path) -> ScoutSettings:
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
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
    assert listed.json()["jobs"][0]["job_id"] == job_id


def test_discovery_jobs_api_rejects_invalid_status_filter(tmp_path, monkeypatch):
    client, _settings = _client(tmp_path, monkeypatch)

    response = client.get("/v1/scout/discovery-jobs", params={"status": "searching"})

    assert response.status_code == 422
