from datetime import datetime, timezone
import json

import pytest

from scout.config import ScoutSettings
from scout.debugger.verdict import DebuggerVerdict
from scout.packets.promotions import (
    PromotionError,
    approve_promotion,
    dry_run_proxy_import,
    finalize_approved_promotion,
    list_promotions,
    list_queued_promotions,
    queue_promotion,
    reject_promotion,
)
from scout.packets.storage import insert_packet
from scout.storage.db import init_database, open_connection
from scout.storage.migrations import apply_migrations
from scout.tests.test_packet_schema import make_packet


def _settings(tmp_path) -> ScoutSettings:
    settings = ScoutSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "scout.db",
        promotion_signing_key="secret",
        promotion_proxy_intake_url="http://proxy.test/v1/scout-intake/promotion",
    )
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    return settings


def _insert_verdict(settings: ScoutSettings, packet_id: str, decision: str) -> None:
    verdict = DebuggerVerdict(
        packet_id=packet_id,
        decision=decision,
        tier_reached=3,
        reason_codes=[],
        findings=[],
        source_quality_score=0.8,
        evaluated_at=datetime.now(timezone.utc),
    )
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
                verdict.tier_reached,
                verdict.model_dump_json(),
                verdict.evaluated_at.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def test_queue_promotion_allows_surfaced_packet(tmp_path):
    settings = _settings(tmp_path)
    insert_packet(settings, make_packet("pkt_surface"))
    _insert_verdict(settings, "pkt_surface", "surface")

    queued = queue_promotion(
        settings,
        "pkt_surface",
        requested_by="tester",
        reason="worth retaining",
    )

    assert queued["status"] == "queued"
    assert queued["requested_by"] == "tester"
    assert queued["reason"] == "worth retaining"
    assert queued["effective_status"] == "surfaced"


def test_queue_promotion_allows_stored_packet(tmp_path):
    settings = _settings(tmp_path)
    insert_packet(settings, make_packet("pkt_store"))
    _insert_verdict(settings, "pkt_store", "store")

    queued = queue_promotion(settings, "pkt_store")

    assert queued["status"] == "queued"
    assert queued["effective_status"] == "stored"


def test_queue_promotion_rejects_ignored_without_force(tmp_path):
    settings = _settings(tmp_path)
    insert_packet(settings, make_packet("pkt_ignore"))
    _insert_verdict(settings, "pkt_ignore", "ignore")

    with pytest.raises(PromotionError):
        queue_promotion(settings, "pkt_ignore")


def test_approve_and_reject_promotions(tmp_path):
    settings = _settings(tmp_path)
    insert_packet(settings, make_packet("pkt_promote"))
    _insert_verdict(settings, "pkt_promote", "surface")
    promotion_id = queue_promotion(settings, "pkt_promote")["promotion_id"]

    assert list_queued_promotions(settings)[0]["promotion_id"] == promotion_id
    approve_promotion(settings, promotion_id, approved_by="tester")

    insert_packet(settings, make_packet("pkt_promote_2"))
    _insert_verdict(settings, "pkt_promote_2", "surface")
    rejected_id = queue_promotion(settings, "pkt_promote_2")["promotion_id"]
    reject_promotion(settings, rejected_id, reason="not relevant")

    conn = open_connection(settings.database_path)
    try:
        statuses = {
            row["promotion_id"]: row["status"]
            for row in conn.execute("SELECT promotion_id, status FROM promotion_queue")
        }
    finally:
        conn.close()
    assert statuses[promotion_id] == "approved"
    assert statuses[rejected_id] == "rejected"
    assert not (settings.data_dir / "audit" / "promotions_applied.jsonl").exists()


def test_list_promotions_counts_all_manual_states(tmp_path):
    settings = _settings(tmp_path)
    for packet_id in ("pkt_pending", "pkt_approved", "pkt_rejected"):
        insert_packet(settings, make_packet(packet_id))
        _insert_verdict(settings, packet_id, "surface")

    pending_id = queue_promotion(settings, "pkt_pending")["promotion_id"]
    approved_id = queue_promotion(settings, "pkt_approved")["promotion_id"]
    rejected_id = queue_promotion(settings, "pkt_rejected")["promotion_id"]
    approve_promotion(settings, approved_id, approved_by="tester")
    reject_promotion(settings, rejected_id, reason="not useful")

    body = list_promotions(settings)

    assert body["counts"] == {
        "pending": 1,
        "queued": 1,
        "approved": 1,
        "rejected": 1,
        "total": 3,
    }
    assert body["queued"][0]["promotion_id"] == pending_id
    assert body["approved"][0]["packet"]["summary"]
    assert body["rejected"][0]["rejected_reason"] == "not useful"


def test_queue_promotion_is_idempotent_for_pending_and_approved(tmp_path):
    settings = _settings(tmp_path)
    insert_packet(settings, make_packet("pkt_dup"))
    _insert_verdict(settings, "pkt_dup", "surface")

    first = queue_promotion(settings, "pkt_dup")
    second = queue_promotion(settings, "pkt_dup")
    approve_promotion(settings, first["promotion_id"], approved_by="tester")
    third = queue_promotion(settings, "pkt_dup")

    assert second["promotion_id"] == first["promotion_id"]
    assert second["idempotent"] is True
    assert third["promotion_id"] == first["promotion_id"]
    assert third["status"] == "approved"
    assert third["idempotent"] is True


def test_queue_promotion_after_rejection_creates_new_pending_request(tmp_path):
    settings = _settings(tmp_path)
    insert_packet(settings, make_packet("pkt_retry"))
    _insert_verdict(settings, "pkt_retry", "surface")

    first = queue_promotion(settings, "pkt_retry")
    reject_promotion(settings, first["promotion_id"], reason="too noisy")
    second = queue_promotion(settings, "pkt_retry")

    assert second["promotion_id"] != first["promotion_id"]
    assert second["status"] == "queued"


def test_dry_run_proxy_import_validates_without_mutation(tmp_path):
    settings = _settings(tmp_path)
    insert_packet(settings, make_packet("pkt_import_dry_run"))
    _insert_verdict(settings, "pkt_import_dry_run", "promote")
    promotion_id = queue_promotion(settings, "pkt_import_dry_run", force=True)[
        "promotion_id"
    ]
    approve_promotion(settings, promotion_id, approved_by="tester")
    before = _promotion_statuses(settings)

    result = dry_run_proxy_import(settings, promotion_id)

    assert result["dry_run"] is True
    assert result["import_ready"] is True
    assert result["read_only"] is True
    assert result["mutation_allowed"] is False
    assert result["promotion_id"] == promotion_id
    assert result["packet_id"] == "pkt_import_dry_run"
    assert result["verdict_decision"] == "promote"
    assert result["would_call_proxy_intake"] is False
    assert result["would_write_proxy_memory"] is False
    assert result["would_write_coding_context"] is False
    assert result["would_finalize_promotion"] is False
    receipt = result["receipt_preview"]
    assert receipt["event"] == "scout_manual_import_receipt_preview"
    assert receipt["imported"] is False
    assert receipt["dry_run"] is True
    assert receipt["manual_controlled"] is True
    assert receipt["promotion_id"] == promotion_id
    assert receipt["packet_id"] == "pkt_import_dry_run"
    assert receipt["authority"] == "append_only_evidence"
    assert receipt["applied"] is False
    assert receipt["approved_proxy_action"] is False
    assert receipt["writes"] == {
        "append_only_evidence": False,
        "proxy_memory": False,
        "coding_context": False,
        "active_context": False,
    }
    assert receipt["rollback"]["tombstone_event"] == "scout_manual_import_tombstone"
    assert receipt["rollback"]["delete_allowed"] is False
    assert receipt["safety"]["proxy_memory_write"] is False
    assert receipt["safety"]["coding_context_write"] is False
    assert receipt["safety"]["hidden_background_worker"] is False
    assert "proxy memory writes" in result["forbidden_actions"]
    assert "promotion finalization" in result["forbidden_actions"]
    assert _promotion_statuses(settings) == before
    assert not (settings.data_dir / "audit" / "promotions_applied.jsonl").exists()


def test_dry_run_proxy_import_requires_approved_promote_verdict(tmp_path):
    settings = _settings(tmp_path)
    insert_packet(settings, make_packet("pkt_dry_run_surface"))
    _insert_verdict(settings, "pkt_dry_run_surface", "surface")
    promotion_id = queue_promotion(settings, "pkt_dry_run_surface")["promotion_id"]

    with pytest.raises(PromotionError, match="approved"):
        dry_run_proxy_import(settings, promotion_id)

    approve_promotion(settings, promotion_id, approved_by="tester")
    with pytest.raises(PromotionError, match="promote"):
        dry_run_proxy_import(settings, promotion_id)


@pytest.mark.anyio
async def test_finalize_approved_promotion_posts_signed_payload(tmp_path, monkeypatch):
    settings = _settings(tmp_path)
    insert_packet(settings, make_packet("pkt_finalize"))
    _insert_verdict(settings, "pkt_finalize", "promote")
    promotion_id = queue_promotion(settings, "pkt_finalize", force=True)["promotion_id"]
    approve_promotion(settings, promotion_id, approved_by="tester")
    captured = {}

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"ok": True}

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def post(self, url, *, content, headers):
            captured["url"] = url
            captured["content"] = content
            captured["headers"] = headers
            return FakeResponse()

    monkeypatch.setattr("scout.packets.promotions.httpx.AsyncClient", FakeClient)

    audit = await finalize_approved_promotion(settings, promotion_id)

    payload = json.loads(captured["content"])
    assert captured["headers"]["X-Scout-Signature"].startswith("sha256=")
    assert payload["approved"] is True
    assert audit["promotion_id"] == promotion_id


def _promotion_statuses(settings: ScoutSettings) -> dict[str, str]:
    conn = open_connection(settings.database_path)
    try:
        return {
            row["promotion_id"]: row["status"]
            for row in conn.execute("SELECT promotion_id, status FROM promotion_queue")
        }
    finally:
        conn.close()
