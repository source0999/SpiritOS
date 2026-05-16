from fastapi import FastAPI
from fastapi.testclient import TestClient

import scout.api.overview as overview_api
import scout.api.sources as sources_api
from scout.api.overview import router as overview_router
from scout.api.sources import router
from scout.config import ScoutSettings
from scout.sources.storage import block_candidate, upsert_candidate
from scout.sources.storage import approve_candidate
from scout.storage.db import init_database
from scout.storage.migrations import apply_migrations


def _client(tmp_path, monkeypatch) -> tuple[TestClient, ScoutSettings]:
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    monkeypatch.setattr(sources_api, "get_settings", lambda: settings)

    app = FastAPI()
    app.include_router(router)
    return TestClient(app), settings


def test_source_candidates_api_lists_counts_and_filters(tmp_path, monkeypatch):
    client, settings = _client(tmp_path, monkeypatch)
    recommended = upsert_candidate(
        settings.database_path,
        display_uri="https://github.com/fastapi/fastapi",
        source_kind="github_repo",
        status="recommended",
        confidence_score=0.98,
        trust_tier="official",
        reason_codes=["official_repo_pattern", "metadata_sufficient"],
    )
    upsert_candidate(
        settings.database_path,
        display_uri="https://casino.example.com/blog",
        source_kind="blog",
        status="stored",
        confidence_score=0.2,
        reason_codes=["spam_pattern_detected"],
    )

    body = client.get(
        "/v1/scout/source-candidates",
        params={"status": "recommended"},
    ).json()

    assert body["counts"]["recommended"] == 1
    assert body["counts"]["needs_review"] == 0
    assert body["counts"]["stored"] == 1
    assert [item["candidate_id"] for item in body["candidates"]] == [
        recommended.candidate_id
    ]
    assert body["candidates"][0]["reason_codes"] == [
        "official_repo_pattern",
        "metadata_sufficient",
    ]
    assert body["candidates"][0]["automation_tier"] == "low_risk_recommended"
    assert body["candidates"][0]["automation_label"] == "Low-risk recommended"
    assert body["candidates"][0]["suggested_action"] == "manual_review_for_approval"
    assert body["candidates"][0]["auto_approval_dry_run"] is True
    assert body["candidates"][0]["auto_approval_dry_run_reason"] == "eligible_dry_run_only"
    assert body["candidates"][0]["auto_approval_dry_run_label"] == (
        "Would be eligible for auto-approval dry run"
    )
    assert body["review_bundles"] == [
        {
            "key": "official_github_repos",
            "label": "Official GitHub repos",
            "description": "High-confidence GitHub repositories with official project signals.",
            "count": 1,
            "candidate_ids": [recommended.candidate_id],
        }
    ]

    all_candidates = client.get("/v1/scout/source-candidates").json()["candidates"]
    noisy = next(item for item in all_candidates if item["status"] == "stored")
    assert noisy["automation_tier"] == "noisy"
    assert noisy["automation_label"] == "Noisy"
    assert noisy["suggested_action"] == "review_for_rejection_or_block"
    assert noisy["auto_approval_dry_run"] is False
    assert noisy["auto_approval_dry_run_reason"] == "blocked_or_noisy_signal"
    bundles = {
        bundle["key"]: bundle
        for bundle in client.get("/v1/scout/source-candidates").json()["review_bundles"]
    }
    assert bundles["official_github_repos"]["count"] == 1
    assert bundles["block_suggested"]["count"] == 1


def test_sources_api_lists_static_and_approved_registry_sources(tmp_path, monkeypatch):
    client, settings = _client(tmp_path, monkeypatch)
    config_path = tmp_path / "sources.yaml"
    config_path.write_text(
        """
version: 1
github_repos:
  - owner: fastapi
    repo: fastapi
    poll_interval_minutes: 60
rss_feeds: []
web_pages: []
""",
        encoding="utf-8",
    )
    settings.config_path = config_path
    candidate = upsert_candidate(
        settings.database_path,
        display_uri="https://github.com/anthropics/anthropic-sdk-python",
        source_kind="github_repo",
    )
    approve_candidate(settings.database_path, candidate.candidate_id, approved_by="tester")

    body = client.get("/v1/scout/sources").json()

    sources = {source["canonical_uri"]: source for source in body["sources"]}
    assert body["count"] == 2
    assert sources["github://fastapi/fastapi"]["source_origin"] == "static_config"
    assert sources["github://anthropics/anthropic-sdk-python"]["source_origin"] == (
        "approved_registry"
    )
    assert sources["github://anthropics/anthropic-sdk-python"]["poller_supported"] is True


def test_legacy_sources_route_returns_normalized_registry_shape(tmp_path, monkeypatch):
    client, settings = _client(tmp_path, monkeypatch)
    config_path = tmp_path / "sources.yaml"
    config_path.write_text(
        """
version: 1
github_repos: []
rss_feeds: []
web_pages: []
""",
        encoding="utf-8",
    )
    settings.config_path = config_path
    monkeypatch.setattr(overview_api, "get_settings", lambda: settings)
    app = FastAPI()
    app.include_router(overview_router)
    legacy_client = TestClient(app)

    body = legacy_client.get("/v1/scout/sources").json()

    assert body["count"] == 0
    assert body["sources"] == []


def test_main_app_prefers_normalized_sources_route():
    from scout.main import app

    matching = [
        route
        for route in app.routes
        if getattr(route, "path", None) == "/v1/scout/sources"
    ]

    assert matching[0].endpoint.__name__ == "get_sources"


def test_source_candidates_api_rejects_unknown_status(tmp_path, monkeypatch):
    client, _settings = _client(tmp_path, monkeypatch)

    response = client.get(
        "/v1/scout/source-candidates",
        params={"status": "pending"},
    )

    assert response.status_code == 422


def test_source_candidates_api_approve_reject_and_block(tmp_path, monkeypatch):
    client, settings = _client(tmp_path, monkeypatch)
    approved = upsert_candidate(
        settings.database_path,
        display_uri="https://github.com/anthropics/anthropic-sdk-python",
        source_kind="github_repo",
        status="recommended",
    )
    rejected = upsert_candidate(
        settings.database_path,
        display_uri="https://example.com/noisy-blog",
        source_kind="blog",
    )
    blocked = upsert_candidate(
        settings.database_path,
        display_uri="https://spam.example/tracker",
        source_kind="unknown",
    )

    approve_body = client.post(
        f"/v1/scout/source-candidates/{approved.candidate_id}/approve",
        json={"approved_by": "tester", "poll_interval_minutes": 45},
    ).json()
    reject_body = client.post(
        f"/v1/scout/source-candidates/{rejected.candidate_id}/reject",
        json={"reason": "not useful", "reviewed_by": "tester"},
    ).json()
    block_body = client.post(
        f"/v1/scout/source-candidates/{blocked.candidate_id}/block",
        json={"reason": "spam", "reviewed_by": "tester"},
    ).json()

    assert approve_body["source"]["canonical_uri"] == (
        "github://anthropics/anthropic-sdk-python"
    )
    assert approve_body["ok"] is True
    assert approve_body["action"] == "approve"
    assert approve_body["candidate"] is None
    assert approve_body["review_event"] is None
    assert approve_body["message"] == "Source candidate approved."
    assert approve_body["poller_supported"] is True
    assert approve_body["warnings"] == []
    assert approve_body["source"]["approved_by"] == "tester"
    assert approve_body["source"]["poll_interval_minutes"] == 45
    assert reject_body["ok"] is True
    assert reject_body["action"] == "reject"
    assert reject_body["candidate"]["status"] == "rejected"
    assert reject_body["candidate"]["rejection_reason"] == "not useful"
    assert reject_body["source"] is None
    assert reject_body["review_event"]["action"] == "reject"
    assert reject_body["message"] == "Source candidate rejected."
    assert reject_body["poller_supported"] is None
    assert reject_body["warnings"] == []
    assert reject_body["candidate"]["review_history"][0]["action"] == "reject"
    assert reject_body["candidate"]["review_history"][0]["reason"] == "not useful"
    assert block_body["ok"] is True
    assert block_body["action"] == "block"
    assert block_body["candidate"]["status"] == "blocked"
    assert block_body["candidate"]["blocked_reason"] == "spam"
    assert block_body["source"] is None
    assert block_body["review_event"]["action"] == "block"
    assert block_body["message"] == "Source candidate blocked."
    assert block_body["poller_supported"] is None
    assert block_body["warnings"] == []
    assert block_body["candidate"]["review_history"][0]["action"] == "block"


def test_source_candidates_api_batch_approves_selected_low_risk_only(tmp_path, monkeypatch):
    client, settings = _client(tmp_path, monkeypatch)
    first = upsert_candidate(
        settings.database_path,
        display_uri="https://github.com/fastapi/fastapi",
        source_kind="github_repo",
        status="recommended",
        confidence_score=0.98,
        trust_tier="official",
        reason_codes=["official_repo_pattern", "metadata_sufficient"],
    )
    second = upsert_candidate(
        settings.database_path,
        display_uri="https://github.com/python/cpython",
        source_kind="github_repo",
        status="recommended",
        confidence_score=0.97,
        trust_tier="official",
        reason_codes=["official_repo_pattern", "metadata_sufficient"],
    )
    noisy = upsert_candidate(
        settings.database_path,
        display_uri="https://casino.example.com/feed",
        source_kind="blog",
        status="stored",
        confidence_score=0.2,
        reason_codes=["spam_pattern_detected"],
    )

    blocked_response = client.post(
        "/v1/scout/source-candidates/batch-approve",
        json={"candidate_ids": [first.candidate_id, noisy.candidate_id], "approved_by": "tester"},
    )
    body = client.post(
        "/v1/scout/source-candidates/batch-approve",
        json={
            "candidate_ids": [first.candidate_id, second.candidate_id],
            "approved_by": "tester",
            "poll_interval_minutes": 30,
        },
    ).json()
    reviewed = client.get("/v1/scout/source-candidates").json()["candidates"]
    reviewed_by_id = {item["candidate_id"]: item for item in reviewed}

    assert blocked_response.status_code == 409
    assert "not low-risk recommended" in blocked_response.json()["detail"]
    assert body["ok"] is True
    assert body["action"] == "batch_approve"
    assert body["requested"] == 2
    assert body["approved_count"] == 2
    assert [item["canonical_uri"] for item in body["approved"]] == [
        "github://fastapi/fastapi",
        "github://python/cpython",
    ]
    assert body["approved"][0]["source"]["poll_interval_minutes"] == 30
    assert body["warnings"] == []
    assert reviewed_by_id[first.candidate_id]["status"] == "approved"
    assert reviewed_by_id[first.candidate_id]["review_history"][0]["action"] == "approve"
    assert reviewed_by_id[second.candidate_id]["review_history"][0]["reviewed_by"] == "tester"
    assert reviewed_by_id[noisy.candidate_id]["status"] == "stored"


def test_source_candidates_api_approve_unsupported_source_reports_poller_false(
    tmp_path,
    monkeypatch,
):
    client, settings = _client(tmp_path, monkeypatch)
    candidate = upsert_candidate(
        settings.database_path,
        display_uri="https://example.com/release-notes",
        source_kind="web_page",
        status="recommended",
    )

    body = client.post(
        f"/v1/scout/source-candidates/{candidate.candidate_id}/approve",
        json={"approved_by": "tester"},
    ).json()

    assert body["ok"] is True
    assert body["action"] == "approve"
    assert body["source"]["canonical_uri"] == "https://example.com/release-notes"
    assert body["poller_supported"] is False
    assert body["message"] == (
        "Source candidate approved; source is active but has no poller support."
    )
    assert body["warnings"] == ["approved source is active but poller_supported is false"]


def test_source_candidates_api_does_not_approve_blocked_candidate(tmp_path, monkeypatch):
    client, settings = _client(tmp_path, monkeypatch)
    candidate = upsert_candidate(
        settings.database_path,
        display_uri="https://spam.example/tracker",
    )
    block_candidate(
        settings.database_path,
        candidate.candidate_id,
        reason="spam",
        blocked_by="tester",
    )

    response = client.post(
        f"/v1/scout/source-candidates/{candidate.candidate_id}/approve",
        json={"approved_by": "tester"},
    )

    assert response.status_code == 409
    assert "blocked" in response.json()["detail"]


def test_source_candidates_api_includes_review_history(tmp_path, monkeypatch):
    client, settings = _client(tmp_path, monkeypatch)
    candidate = upsert_candidate(
        settings.database_path,
        display_uri="https://example.com/noisy-blog",
        source_kind="blog",
    )
    reject_candidate = client.post(
        f"/v1/scout/source-candidates/{candidate.candidate_id}/reject",
        json={"reason": "duplicate source", "reviewed_by": "tester"},
    )
    assert reject_candidate.status_code == 200

    body = client.get("/v1/scout/source-candidates").json()

    reviewed = body["candidates"][0]
    assert reviewed["candidate_id"] == candidate.candidate_id
    assert reviewed["review_history"][0]["action"] == "reject"
    assert reviewed["review_history"][0]["previous_status"] == "needs_review"
    assert reviewed["review_history"][0]["new_status"] == "rejected"
    assert reviewed["review_history"][0]["reviewed_by"] == "tester"
