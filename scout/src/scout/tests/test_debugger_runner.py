from scout.config import ScoutSettings
from scout.debugger.runner import evaluate_packet, process_pending_packets, recheck_packet
from scout.debugger.verdict import DebuggerFinding
from scout.packets.storage import insert_packet
from scout.storage.db import init_database, open_connection
from scout.storage.migrations import apply_migrations
from scout.tests.test_packet_schema import make_packet


def test_debugger_runner_writes_verdict_and_updates_status(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "sources.yaml").write_text(
        """
version: 1
github_repos: []
rss_feeds:
  - url: https://example.com/feed.xml
    poll_interval_minutes: 60
web_pages: []
""",
        encoding="utf-8",
    )
    (config_dir / "topic_anchors.yaml").write_text(
        "version: 1\nanchors:\n  - example\n",
        encoding="utf-8",
    )
    settings = ScoutSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "scout.db",
        config_path=config_dir / "sources.yaml",
        debugger_batch_size=5,
    )
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    packet = make_packet("pkt_runner")
    packet.entity_tags = ["example"]
    insert_packet(settings, packet)

    result = process_pending_packets(settings)

    conn = open_connection(settings.database_path)
    try:
        verdict = conn.execute("SELECT decision FROM verdicts").fetchone()
        stored = conn.execute(
            "SELECT status FROM packets WHERE packet_id = 'pkt_runner'"
        ).fetchone()
    finally:
        conn.close()

    assert result["processed"] == 1
    assert verdict["decision"] == "surface"
    assert stored["status"] == "surfaced"


def test_evaluate_packet_tier3_injection_warning_no_legacy_reason_code(
    tmp_path, monkeypatch
):
    """Full pipeline: Tier 1 injection passed; Tier 3 screen warning must not headline."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "sources.yaml").write_text(
        """
version: 1
github_repos: []
rss_feeds:
  - url: https://example.com/feed.xml
    poll_interval_minutes: 60
web_pages: []
""",
        encoding="utf-8",
    )
    (config_dir / "topic_anchors.yaml").write_text(
        "version: 1\nanchors:\n  - example\n",
        encoding="utf-8",
    )
    settings = ScoutSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "scout.db",
        config_path=config_dir / "sources.yaml",
    )
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    packet = make_packet("pkt_t3_rc")
    packet.entity_tags = ["example"]
    packet_json = packet.model_dump_json()

    def fake_run_tier3(_packet, _settings, decision):
        return (
            [
                DebuggerFinding(
                    check_id="injection_screen_llm",
                    tier=3,
                    status="warning",
                    detail="Return InjectionScreen",
                )
            ],
            [],
            decision,
        )

    monkeypatch.setattr("scout.debugger.runner.run_tier3", fake_run_tier3)

    verdict = evaluate_packet(packet_json, settings)

    assert verdict.decision == "surface"
    assert "injection_signal_llm" not in verdict.reason_codes
    inj = next(f for f in verdict.findings if f.check_id == "injection_screen_llm")
    assert inj.status == "warning"


def test_recheck_packet_replaces_verdict_without_touching_packet_json(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "sources.yaml").write_text(
        """
version: 1
github_repos: []
rss_feeds:
  - url: https://example.com/feed.xml
    poll_interval_minutes: 60
web_pages: []
""",
        encoding="utf-8",
    )
    (config_dir / "topic_anchors.yaml").write_text(
        "version: 1\nanchors:\n  - example\n",
        encoding="utf-8",
    )
    settings = ScoutSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "scout.db",
        config_path=config_dir / "sources.yaml",
    )
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    packet = make_packet("pkt_recheck")
    packet.entity_tags = ["example"]
    insert_packet(settings, packet)
    original_packet_json = packet.model_dump_json()
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
                "pkt_recheck",
                "ignore",
                1,
                '{"packet_id":"pkt_recheck","decision":"ignore","tier_reached":1,'
                '"reason_codes":["old"],"findings":[],"source_quality_score":0.1,'
                '"evaluated_at":"2026-05-14T00:00:00+00:00"}',
                "2026-05-14T00:00:00+00:00",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    result = recheck_packet(settings, "pkt_recheck")

    conn = open_connection(settings.database_path)
    try:
        stored_packet = conn.execute(
            "SELECT packet_json, status FROM packets WHERE packet_id = 'pkt_recheck'"
        ).fetchone()
        verdict = conn.execute(
            "SELECT decision FROM verdicts WHERE packet_id = 'pkt_recheck'"
        ).fetchone()
    finally:
        conn.close()

    assert result["previous"]["decision"] == "ignore"
    assert result["new"]["decision"] == "surface"
    assert result["changed"] is True
    assert stored_packet["packet_json"] == original_packet_json
    assert stored_packet["status"] == "surfaced"
    assert verdict["decision"] == "surface"
    assert not (tmp_path / "audit" / "promotions_applied.jsonl").exists()


def test_recheck_packet_can_skip_tier3_for_manual_flow(tmp_path, monkeypatch):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "sources.yaml").write_text(
        """
version: 1
github_repos: []
rss_feeds:
  - url: https://example.com/feed.xml
    poll_interval_minutes: 60
web_pages: []
""",
        encoding="utf-8",
    )
    (config_dir / "topic_anchors.yaml").write_text(
        "version: 1\nanchors:\n  - example\n",
        encoding="utf-8",
    )
    settings = ScoutSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "scout.db",
        config_path=config_dir / "sources.yaml",
    )
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    packet = make_packet("pkt_recheck_timeout")
    packet.entity_tags = ["example"]
    insert_packet(settings, packet)
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
                "pkt_recheck_timeout",
                "store",
                1,
                '{"packet_id":"pkt_recheck_timeout","decision":"store","tier_reached":1,'
                '"reason_codes":[],"findings":[],"source_quality_score":0.5,'
                '"evaluated_at":"2026-05-14T00:00:00+00:00"}',
                "2026-05-14T00:00:00+00:00",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    def fail_tier3(*_args, **_kwargs):
        raise AssertionError("manual recheck should not call tier 3")

    monkeypatch.setattr("scout.debugger.runner.run_tier3", fail_tier3)
    result = recheck_packet(settings, "pkt_recheck_timeout", include_tier3=False)

    conn = open_connection(settings.database_path)
    try:
        verdict = conn.execute(
            "SELECT decision FROM verdicts WHERE packet_id = 'pkt_recheck_timeout'"
        ).fetchone()
    finally:
        conn.close()

    assert result["new"]["decision"] == "surface"
    assert verdict["decision"] == "surface"
