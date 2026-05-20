from fastapi import FastAPI
from fastapi.testclient import TestClient

import scout.api.overview as overview_api
import scout.api.packets as packets_api
from scout.api.source_trust import classify_source
from scout.api.overview import router as overview_router
from scout.api.packets import router
from scout.config import ScoutSettings
from scout.packets.promotions import approve_promotion, queue_promotion, reject_promotion
from scout.packets.storage import insert_packet
from scout.storage.db import init_database, open_connection
from scout.storage.migrations import apply_migrations
from scout.tests.test_packet_schema import make_packet


def test_packets_api_recent_search_and_get(tmp_path, monkeypatch):
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    packet = make_packet("pkt_api")
    insert_packet(settings, packet)
    monkeypatch.setattr(packets_api, "get_settings", lambda: settings)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    recent = client.get("/v1/scout/packets/recent").json()
    search = client.get("/v1/scout/packets/search", params={"q": "Scout"}).json()
    fetched = client.get("/v1/scout/packets/pkt_api").json()

    assert recent["count"] == 1
    assert search["count"] == 1
    assert fetched["packet"]["packet_id"] == "pkt_api"


def test_packets_api_verdict_routes(tmp_path, monkeypatch):
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    packet = make_packet("pkt_verdict")
    insert_packet(settings, packet)
    conn = __import__("scout.storage.db", fromlist=["open_connection"]).open_connection(
        settings.database_path
    )
    try:
        conn.execute(
            """
            INSERT INTO verdicts (
                packet_id, decision, tier_reached, verdict_json, evaluated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "pkt_verdict",
                "surface",
                2,
                '{"packet_id":"pkt_verdict","decision":"surface"}',
                "2026-05-14T00:00:00+00:00",
            ),
        )
        conn.commit()
    finally:
        conn.close()
    monkeypatch.setattr(packets_api, "get_settings", lambda: settings)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    assert client.get("/v1/scout/packets/pkt_verdict/verdict").status_code == 200
    by_decision = client.get("/v1/scout/packets/by_decision/surface").json()
    recent = client.get(
        "/v1/scout/packets/recent",
        params={"with_verdict": "true"},
    ).json()

    assert by_decision["count"] == 1
    assert recent["packets"][0]["_verdict"]["decision"] == "surface"


def test_packets_api_exposes_effective_status_from_db_and_raw_json(tmp_path, monkeypatch):
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    packet = make_packet("pkt_status")
    insert_packet(settings, packet)
    conn = __import__("scout.storage.db", fromlist=["open_connection"]).open_connection(
        settings.database_path
    )
    try:
        conn.execute(
            "UPDATE packets SET status = ? WHERE packet_id = ?",
            ("stored", "pkt_status"),
        )
        conn.execute(
            """
            INSERT INTO verdicts (
                packet_id, decision, tier_reached, verdict_json, evaluated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "pkt_status",
                "store",
                3,
                '{"packet_id":"pkt_status","decision":"store"}',
                "2026-05-14T00:00:00+00:00",
            ),
        )
        conn.commit()
    finally:
        conn.close()
    monkeypatch.setattr(packets_api, "get_settings", lambda: settings)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    body = client.get("/v1/scout/packets/pkt_status").json()["packet"]

    assert body["raw_status"] == "debugger_pending"
    assert body["db_status"] == "stored"
    assert body["effective_status"] == "stored"
    assert body["status"] == "stored"
    assert body["_verdict"]["decision"] == "store"


def test_packets_api_db_surfaced_overrides_raw_pending(tmp_path, monkeypatch):
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    packet = make_packet("pkt_surf")
    insert_packet(settings, packet)
    conn = __import__("scout.storage.db", fromlist=["open_connection"]).open_connection(
        settings.database_path
    )
    try:
        conn.execute(
            "UPDATE packets SET status = ? WHERE packet_id = ?",
            ("surfaced", "pkt_surf"),
        )
        conn.commit()
    finally:
        conn.close()
    monkeypatch.setattr(packets_api, "get_settings", lambda: settings)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    body = client.get("/v1/scout/packets/pkt_surf").json()["packet"]

    assert body["raw_status"] == "debugger_pending"
    assert body["db_status"] == "surfaced"
    assert body["effective_status"] == "surfaced"
    assert body["status"] == "surfaced"


def test_packets_api_effective_status_pending_without_verdict(tmp_path, monkeypatch):
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    packet = make_packet("pkt_nopend")
    insert_packet(settings, packet)
    monkeypatch.setattr(packets_api, "get_settings", lambda: settings)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    body = client.get("/v1/scout/packets/pkt_nopend").json()["packet"]

    assert body["db_status"] == "debugger_pending"
    assert body["effective_status"] == "debugger_pending"
    assert body["status"] == "debugger_pending"
    assert "_verdict" not in body


def _overview_client(tmp_path, monkeypatch):
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    monkeypatch.setattr(overview_api, "get_settings", lambda: settings)
    app = FastAPI()
    app.include_router(overview_router)
    return TestClient(app), settings


def _insert_unsynthesized_artifact(settings, event_id="raw_unsynth"):
    conn = open_connection(settings.database_path)
    try:
        conn.execute(
            """
            INSERT INTO raw_event_index (
                event_id, source_uri, event_kind, payload_path,
                payload_sha256, captured_at_epoch, content_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                "https://example.com/feed.xml",
                "rss.entry",
                "raw/events.jsonl",
                "sha",
                1778716800,
                f"hash-{event_id}",
            ),
        )
        conn.execute(
            """
            INSERT INTO extracted_artifacts (
                event_id, source_uri, event_kind, artifact_kind, artifact_path,
                metadata_json, extracted_at_epoch
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                "https://example.com/feed.xml",
                "rss.entry",
                "rss_markdown",
                f"extracted/example/{event_id}.md",
                "{}",
                1778716800,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _set_packet_status(settings, packet_id, status):
    conn = open_connection(settings.database_path)
    try:
        conn.execute(
            "UPDATE packets SET status = ? WHERE packet_id = ?",
            (status, packet_id),
        )
        conn.commit()
    finally:
        conn.close()


def _insert_verdict(settings, packet_id, decision):
    conn = open_connection(settings.database_path)
    try:
        conn.execute(
            """
            INSERT INTO verdicts (
                packet_id, decision, tier_reached, verdict_json, evaluated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                packet_id,
                decision,
                2,
                (
                    f'{{"packet_id":"{packet_id}","decision":"{decision}",'
                    '"tier_reached":2,'
                    '"reason_codes":["test_reason"],'
                    '"findings":[{"check_id":"embedding_storage","tier":3,'
                    '"status":"skipped","detail":"sentence-transformers unavailable"}],'
                    '"source_quality_score":0.75,'
                    '"evaluated_at":"2026-05-14T00:00:00+00:00"}'
                ),
                "2026-05-14T00:00:00+00:00",
            ),
        )
        conn.commit()
    finally:
        conn.close()


def test_scout_overview_empty(tmp_path, monkeypatch):
    client, _settings = _overview_client(tmp_path, monkeypatch)

    body = client.get("/v1/scout/overview").json()

    assert body["counts"] == {
        "raw_event_index": 0,
        "extracted_artifacts": 0,
        "packets": 0,
        "verdicts": 0,
        "packet_embeddings": 0,
        "source_quality": 0,
        "promotion_queue": 0,
        "source_tracking": 0,
    }
    assert body["backlog"]["unsynthesized_artifacts"] == 0
    assert body["backlog"]["debugger_pending_packets"] == 0
    assert body["backlog"]["debugger_pending_without_verdict"] == 0
    assert body["human_summary"]["pipeline_health"] == "idle"
    synthesis = body["packet_synthesis"]
    assert synthesis["state"] == "route_missing"
    assert synthesis["label"] == "Ollama route missing"
    assert synthesis["model"] == "ollama/llama3"
    assert synthesis["route_configured"] is False
    assert synthesis["pending_artifacts"] == 0
    assert body["human_summary"]["packet_synthesis_status"] == synthesis
    memory_status = body["human_summary"]["memory_status"]
    assert memory_status["label"] == "Semantic memory inactive"
    assert memory_status["state"] == "inactive"
    assert memory_status["mode_label"] == "Inactive"
    assert memory_status["write_enabled"] is False
    assert "not writing into proxy memory" in memory_status["reason"]
    assert "not writing to proxy memory" in memory_status["safety_label"]
    assert body["human_summary"]["promotion_status"]["promoted_count"] == 0
    assert body["recent"]["surfaced"] == []
    assert body["recent"]["stored"] == []
    assert body["recent"]["pending"] == []
    assert "job_count" in body["scheduler"]


def test_scout_overview_counts_pending_and_surfaced(tmp_path, monkeypatch):
    client, settings = _overview_client(tmp_path, monkeypatch)
    settings.litellm_api_base = "http://spirit-ollama:11434"
    _insert_unsynthesized_artifact(settings)
    stored_packet = make_packet("pkt_stored")
    surfaced_packet = make_packet("pkt_surfaced")
    pending_packet = make_packet("pkt_pending")
    insert_packet(settings, stored_packet)
    insert_packet(settings, surfaced_packet)
    insert_packet(settings, pending_packet)
    _set_packet_status(settings, "pkt_stored", "stored")
    _set_packet_status(settings, "pkt_surfaced", "surfaced")
    _insert_verdict(settings, "pkt_surfaced", "surface")

    body = client.get("/v1/scout/overview").json()

    assert body["counts"]["raw_event_index"] == 1
    assert body["counts"]["extracted_artifacts"] == 1
    assert body["counts"]["packets"] == 3
    assert body["counts"]["verdicts"] == 1
    assert body["backlog"]["unsynthesized_artifacts"] == 1
    assert body["packet_synthesis"]["state"] == "pending"
    assert body["packet_synthesis"]["pending_artifacts"] == 1
    assert body["backlog"]["debugger_pending_packets"] == 1
    assert body["human_summary"]["scan_flow"][0]["label"] == "Scanned"
    assert body["human_summary"]["scan_flow"][0]["count"] == 1
    assert body["recent"]["stored"][0]["packet_id"] == "pkt_stored"
    assert body["recent"]["surfaced"][0]["packet_id"] == "pkt_surfaced"
    assert body["recent"]["pending"][0]["packet_id"] == "pkt_pending"


def test_scout_overview_uses_effective_status(tmp_path, monkeypatch):
    client, settings = _overview_client(tmp_path, monkeypatch)
    packet = make_packet("pkt_effective")
    insert_packet(settings, packet)
    _insert_verdict(settings, "pkt_effective", "surface")

    body = client.get("/v1/scout/overview").json()
    surfaced = body["recent"]["surfaced"][0]

    assert surfaced["packet_id"] == "pkt_effective"
    assert surfaced["raw_status"] == "debugger_pending"
    assert surfaced["db_status"] == "debugger_pending"
    assert surfaced["effective_status"] == "surfaced"
    assert surfaced["status"] == "surfaced"
    assert surfaced["_verdict"]["decision"] == "surface"
    assert surfaced["status_explanation"]["verdict_decision"] == "surface"
    assert surfaced["status_explanation"]["label"] == "Useful now"
    assert surfaced["usefulness_label"] == "Useful now"
    assert surfaced["usefulness_reason"] == "sentence-transformers unavailable"
    assert surfaced["recommended_action"] == "inspect_now"
    assert surfaced["confidence_label"] == "high"
    assert surfaced["reason_codes"] == ["test_reason"]
    assert surfaced["findings"][0]["check_id"] == "embedding_storage"
    assert surfaced["source_quality_score"] == 0.75
    assert surfaced["evaluated_at"] == "2026-05-14T00:00:00+00:00"


def test_source_trust_classifies_seed_sources():
    assert classify_source(
        "https://blog.python.org/feeds/posts/default"
    ).category == "official_project_blog"
    assert classify_source(
        "github://fastapi/fastapi/commits"
    ).category == "official_github_repo"
    assert classify_source(
        "github://anthropics/anthropic-sdk-python/commits"
    ).category == "official_github_repo"


def _insert_source_tracking(settings, source_uri):
    conn = open_connection(settings.database_path)
    try:
        conn.execute(
            """
            INSERT INTO source_tracking (
                source_uri, page_key, last_polled_epoch, consecutive_failures
            )
            VALUES (?, '', 1778716800, 0)
            """,
            (source_uri,),
        )
        conn.commit()
    finally:
        conn.close()


def test_scout_overview_exposes_source_trust_labels(tmp_path, monkeypatch):
    client, settings = _overview_client(tmp_path, monkeypatch)
    sources = [
        "https://blog.python.org/feeds/posts/default",
        "github://fastapi/fastapi/commits",
        "github://anthropics/anthropic-sdk-python/commits",
    ]
    for source_uri in sources:
        _insert_source_tracking(settings, source_uri)

    body = client.get("/v1/scout/overview").json()
    trust_by_uri = {source["source_uri"]: source["trust_category"] for source in body["sources"]}

    assert trust_by_uri["https://blog.python.org/feeds/posts/default"] == "official_project_blog"
    assert trust_by_uri["github://fastapi/fastapi/commits"] == "official_github_repo"
    assert trust_by_uri[
        "github://anthropics/anthropic-sdk-python/commits"
    ] == "official_github_repo"


def test_scout_sources_endpoint_lists_active_sources(tmp_path, monkeypatch):
    client, settings = _overview_client(tmp_path, monkeypatch)
    _insert_source_tracking(settings, "github://fastapi/fastapi/commits")

    body = client.get("/v1/scout/sources").json()

    assert body["count"] == 1
    assert body["sources"][0]["trust_label"] == "Official GitHub repo"
    assert body["sources"][0]["health_label"] == "Healthy"


def test_packet_status_explanation_prefers_verdict_decision_label(tmp_path, monkeypatch):
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    insert_packet(settings, make_packet("pkt_human_status"))
    _insert_verdict(settings, "pkt_human_status", "store")
    monkeypatch.setattr(packets_api, "get_settings", lambda: settings)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    body = client.get("/v1/scout/packets/pkt_human_status").json()["packet"]

    assert body["raw_status"] == "debugger_pending"
    assert body["effective_status"] == "stored"
    assert body["status_explanation"]["verdict_decision"] == "store"
    assert body["status_explanation"]["label"] == "Saved for later"
    assert body["human_status_label"] == "Saved for later"
    assert body["usefulness_label"] == "Saved for later"
    assert body["recommended_action"] == "save_for_later"
    assert body["confidence_label"] == "medium"


def test_packet_embedding_skipped_gets_human_semantic_memory_label(tmp_path, monkeypatch):
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    insert_packet(settings, make_packet("pkt_embed_skip"))
    _insert_verdict(settings, "pkt_embed_skip", "promote")
    monkeypatch.setattr(packets_api, "get_settings", lambda: settings)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    body = client.get("/v1/scout/packets/pkt_embed_skip").json()["packet"]

    assert body["status_explanation"]["label"] == "Semantic memory skipped"
    assert "inactive" in body["status_explanation"]["help"]


def test_packet_explorer_returns_human_source_status_and_findings(tmp_path, monkeypatch):
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    packet = make_packet("pkt_explorer").model_copy(
        update={
            "source_uri": "github://fastapi/fastapi/commits",
            "entity_tags": ["fastapi", "release"],
        }
    )
    insert_packet(settings, packet)
    _insert_verdict(settings, "pkt_explorer", "surface")
    monkeypatch.setattr(packets_api, "get_settings", lambda: settings)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    body = client.get(
        "/v1/scout/packets/explorer",
        params={"decision": "surface"},
    ).json()

    item = body["packets"][0]
    assert item["packet_id"] == "pkt_explorer"
    assert item["trust_label"] == "Official GitHub repo"
    assert item["effective_status"] == "surfaced"
    assert item["human_status_label"] == "Useful now"
    assert item["usefulness_label"] == "Useful now"
    assert item["usefulness_reason"] == "sentence-transformers unavailable"
    assert item["recommended_action"] == "inspect_now"
    assert item["confidence_label"] == "high"
    assert item["source_trust_label"] == "Official GitHub repo"
    assert item["summary"]
    assert item["entity_tags"] == ["fastapi", "release"]
    assert item["confidence_score"] == 0.75
    assert item["reason_codes"] == ["test_reason"]
    assert item["findings"][0]["check_id"] == "embedding_storage"


def test_packet_explorer_exposes_promotion_state(tmp_path, monkeypatch):
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    packet = make_packet("pkt_promotion_state")
    insert_packet(settings, packet)
    _insert_verdict(settings, "pkt_promotion_state", "surface")
    promotion = queue_promotion(
        settings,
        "pkt_promotion_state",
        reason="manual review",
    )
    monkeypatch.setattr(packets_api, "get_settings", lambda: settings)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    body = client.get(
        "/v1/scout/packets/explorer",
        params={"decision": "surface"},
    ).json()

    item = body["packets"][0]
    assert item["promotion_status"] == "queued"
    assert item["promotion_id"] == promotion["promotion_id"]
    assert item["promotion_label"] == "Queued for review"
    assert item["promotion_reason"] == "manual review"
    assert item["promotion_requested_at"]


def test_packet_auto_rank_is_deterministic_and_read_only(tmp_path, monkeypatch):
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    surfaced = make_packet("pkt_rank_surfaced")
    stored = make_packet("pkt_rank_stored")
    ignored = make_packet("pkt_rank_ignored")
    insert_packet(settings, surfaced)
    insert_packet(settings, stored)
    insert_packet(settings, ignored)
    _insert_verdict(settings, "pkt_rank_surfaced", "surface")
    _insert_verdict(settings, "pkt_rank_stored", "store")
    _insert_verdict(settings, "pkt_rank_ignored", "ignore")
    _set_packet_status(settings, "pkt_rank_stored", "stored")
    _set_packet_status(settings, "pkt_rank_ignored", "ignored")
    before_counts = _packet_state_counts(settings)
    monkeypatch.setattr(packets_api, "get_settings", lambda: settings)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    first = client.get("/v1/scout/packets/explorer").json()
    second = client.get("/v1/scout/packets/explorer").json()

    first_ranks = {
        item["packet_id"]: item["recommended_review_order"]
        for item in first["packets"]
    }
    second_ranks = {
        item["packet_id"]: item["recommended_review_order"]
        for item in second["packets"]
    }
    assert first_ranks == second_ranks
    assert first_ranks["pkt_rank_surfaced"] == 1
    assert first_ranks["pkt_rank_stored"] == 2
    assert first_ranks["pkt_rank_ignored"] == 3
    top = next(item for item in first["packets"] if item["packet_id"] == "pkt_rank_surfaced")
    assert top["auto_rank"] == {
        "level": 1,
        "mode": "auto_rank_only",
        "read_only": True,
        "mutation_allowed": False,
        "recommended_review_order": 1,
        "why_this_first": "Surfaced packet is likely useful for manual packet review.",
        "risk_reason": "No automatic packet promotion is allowed.",
    }
    assert _packet_state_counts(settings) == before_counts


def test_packet_promotion_recommendations_are_read_only(tmp_path, monkeypatch):
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    insert_packet(settings, make_packet("pkt_recommend_promote"))
    insert_packet(settings, make_packet("pkt_recommend_surface"))
    insert_packet(settings, make_packet("pkt_recommend_store"))
    insert_packet(settings, make_packet("pkt_recommend_ignore"))
    _insert_verdict(settings, "pkt_recommend_promote", "promote")
    _insert_verdict(settings, "pkt_recommend_surface", "surface")
    _insert_verdict(settings, "pkt_recommend_store", "store")
    _insert_verdict(settings, "pkt_recommend_ignore", "ignore")
    before_counts = _packet_state_counts(settings)
    monkeypatch.setattr(packets_api, "get_settings", lambda: settings)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    body = client.get("/v1/scout/packets/promotion-recommendations").json()

    assert body["mode"] == "manual_packet_promotion_recommendations"
    assert body["read_only"] is True
    assert body["mutation_allowed"] is False
    assert body["approval_required_before"] == [
        "queue_promotion",
        "approve_promotion",
        "proxy-memory-write",
    ]
    assert "automatic packet promotion" in body["forbidden_actions"]
    assert "proxy memory writes" in body["forbidden_actions"]
    assert body["count"] == 3
    assert [
        item["packet_id"] for item in body["recommendations"]
    ] == [
        "pkt_recommend_promote",
        "pkt_recommend_surface",
        "pkt_recommend_store",
    ]
    top = body["recommendations"][0]
    assert top["recommended_review_order"] == 1
    assert top["safe_next_action"] == "operator_may_queue_promotion"
    assert top["mutation_effect"] == "none"
    assert top["why_this_first"].startswith("Debugger verdict suggests")
    assert top["risk_reason"] == "No automatic packet promotion or proxy memory write is allowed."
    assert _packet_state_counts(settings) == before_counts


def test_queue_promotion_api_accepts_surfaced_packet_body(tmp_path, monkeypatch):
    settings = ScoutSettings(data_dir=tmp_path, database_path=tmp_path / "scout.db")
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    insert_packet(settings, make_packet("pkt_queue_api"))
    _insert_verdict(settings, "pkt_queue_api", "surface")
    monkeypatch.setattr(packets_api, "get_settings", lambda: settings)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    body = client.post(
        "/v1/scout/packets/pkt_queue_api/queue_promotion",
        json={"requested_by": "manual-review", "reason": "keep this"},
    ).json()

    assert body["promotion"]["status"] == "queued"
    assert body["promotion"]["requested_by"] == "manual-review"
    assert body["promotion"]["reason"] == "keep this"
    assert body["promotion"]["effective_status"] == "surfaced"


def test_scout_overview_promotion_counts_use_manual_queue_states(tmp_path, monkeypatch):
    client, settings = _overview_client(tmp_path, monkeypatch)
    for packet_id in ("pkt_approved", "pkt_rejected"):
        insert_packet(settings, make_packet(packet_id))
        _insert_verdict(settings, packet_id, "surface")
    approved = queue_promotion(settings, "pkt_approved")
    rejected = queue_promotion(settings, "pkt_rejected")
    approve_promotion(settings, approved["promotion_id"], approved_by="tester")
    reject_promotion(settings, rejected["promotion_id"], reason="not relevant")

    body = client.get("/v1/scout/overview").json()

    promotion_status = body["human_summary"]["promotion_status"]
    assert promotion_status["promoted_count"] == 1
    assert promotion_status["pending_review_count"] == 0
    assert promotion_status["rejected_count"] == 1


def _packet_state_counts(settings):
    conn = open_connection(settings.database_path)
    try:
        return {
            "packets": {
                row["status"]: row["count"]
                for row in conn.execute(
                    "SELECT status, COUNT(*) AS count FROM packets GROUP BY status"
                ).fetchall()
            },
            "promotion_queue": conn.execute(
                "SELECT COUNT(*) AS count FROM promotion_queue"
            ).fetchone()["count"],
        }
    finally:
        conn.close()
