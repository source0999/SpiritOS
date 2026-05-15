from scout.config import ScoutSettings
from scout.debugger.tier2_structural import load_topic_anchors, run_tier2
from scout.storage.db import init_database
from scout.storage.migrations import apply_migrations
from scout.tests.test_packet_schema import make_packet


def _settings(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "sources.yaml").write_text("version: 1\n", encoding="utf-8")
    (config_dir / "topic_anchors.yaml").write_text(
        "version: 1\nanchors:\n  - fastapi\n  - python\n",
        encoding="utf-8",
    )
    settings = ScoutSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "scout.db",
        config_path=config_dir / "sources.yaml",
    )
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    return settings


def test_load_topic_anchors(tmp_path):
    settings = _settings(tmp_path)

    assert load_topic_anchors(settings.config_path) == {"fastapi", "python"}


def test_tier2_surfaces_relevant_confident_packet(tmp_path):
    settings = _settings(tmp_path)
    packet = make_packet()
    packet.entity_tags = ["fastapi", "python"]
    packet.confidence_score = 0.8

    _findings, reason_codes, decision, score = run_tier2(packet, settings)

    assert reason_codes == []
    assert decision == "surface"
    assert score == 0.5


def test_tier2_caps_low_relevance_at_store(tmp_path):
    settings = _settings(tmp_path)
    packet = make_packet()
    packet.entity_tags = ["unrelated"]

    _findings, reason_codes, decision, _score = run_tier2(packet, settings)

    assert "low_topic_overlap" in reason_codes
    assert decision == "store"


def test_tier2_direct_anchor_hit_not_low_relevance(tmp_path):
    settings = _settings(tmp_path)
    packet = make_packet()
    packet.entity_tags = ["python", "software"]
    packet.confidence_score = 0.8

    findings, reason_codes, decision, _score = run_tier2(packet, settings)

    assert "low_topic_overlap" not in reason_codes
    assert decision == "surface"
    rel = next(f for f in findings if f.check_id == "relevance_anchor")
    assert rel.status == "passed"
    assert "anchor_hits=['python']" in rel.detail
    assert "confidence=0.800" in rel.detail


def test_tier2_surfaces_direct_anchor_high_confidence(tmp_path):
    settings = _settings(tmp_path)
    packet = make_packet()
    packet.entity_tags = ["python", "jit"]
    packet.confidence_score = 0.8

    _findings, reason_codes, decision, _score = run_tier2(packet, settings)

    assert decision == "surface"
    assert "low_topic_overlap" not in reason_codes


def test_tier2_surfaces_python_security_anchor(tmp_path):
    settings = _settings(tmp_path)
    packet = make_packet()
    packet.entity_tags = ["python", "security"]
    packet.confidence_score = 0.8

    _findings, reason_codes, decision, _score = run_tier2(packet, settings)

    assert decision == "surface"
    assert "low_topic_overlap" not in reason_codes


def test_tier2_low_confidence_anchor_stores_without_low_topic_overlap(tmp_path):
    settings = _settings(tmp_path)
    packet = make_packet()
    packet.entity_tags = ["python"]
    packet.confidence_score = 0.2

    _findings, reason_codes, decision, _score = run_tier2(packet, settings)

    assert decision == "store"
    assert "confidence_floor" in reason_codes
    assert "low_topic_overlap" not in reason_codes


def test_tier2_no_anchor_hit_stores_low_topic_overlap(tmp_path):
    settings = _settings(tmp_path)
    packet = make_packet()
    packet.entity_tags = ["celebrity", "sports"]
    packet.confidence_score = 0.9

    _findings, reason_codes, decision, _score = run_tier2(packet, settings)

    assert decision == "store"
    assert "low_topic_overlap" in reason_codes
