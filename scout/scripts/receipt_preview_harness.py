from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scout.config import ScoutSettings
from scout.debugger.verdict import DebuggerVerdict
from scout.packets.promotions import approve_promotion, dry_run_proxy_import, queue_promotion
from scout.packets.storage import insert_packet
from scout.storage.db import init_database, open_connection
from scout.storage.migrations import apply_migrations
from scout.tests.test_packet_schema import make_packet


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


def _promotion_statuses(settings: ScoutSettings) -> dict[str, str]:
    conn = open_connection(settings.database_path)
    try:
        return {
            row["promotion_id"]: row["status"]
            for row in conn.execute("SELECT promotion_id, status FROM promotion_queue")
        }
    finally:
        conn.close()


def run_harness() -> dict:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        settings = ScoutSettings(
            data_dir=root,
            database_path=root / "scout.db",
            promotion_signing_key="receipt-harness-secret",
            promotion_proxy_intake_url="http://proxy.test/v1/scout-intake/promotion",
        )
        init_database(settings.database_path)
        apply_migrations(settings.database_path)
        insert_packet(settings, make_packet("pkt_receipt_harness"))
        _insert_verdict(settings, "pkt_receipt_harness", "promote")
        promotion_id = queue_promotion(
            settings,
            "pkt_receipt_harness",
            force=True,
        )["promotion_id"]
        approve_promotion(settings, promotion_id, approved_by="receipt-harness")
        before = _promotion_statuses(settings)

        result = dry_run_proxy_import(settings, promotion_id)
        receipt = result["receipt_preview"]
        checks = {
            "dry_run": result["dry_run"] is True,
            "import_ready": result["import_ready"] is True,
            "receipt_preview_present": isinstance(receipt, dict),
            "receipt_preview_event": receipt.get("event")
            == "scout_manual_import_receipt_preview",
            "receipt_not_imported": receipt.get("imported") is False,
            "receipt_not_applied": receipt.get("applied") is False,
            "approved_proxy_action_false": receipt.get("approved_proxy_action") is False,
            "append_only_evidence_false": receipt.get("writes", {}).get("append_only_evidence")
            is False,
            "proxy_memory_false": receipt.get("writes", {}).get("proxy_memory") is False,
            "coding_context_false": receipt.get("writes", {}).get("coding_context") is False,
            "active_context_false": receipt.get("writes", {}).get("active_context") is False,
            "tombstone_present": receipt.get("rollback", {}).get("tombstone_event")
            == "scout_manual_import_tombstone",
            "delete_not_allowed": receipt.get("rollback", {}).get("delete_allowed") is False,
            "hidden_worker_false": receipt.get("safety", {}).get("hidden_background_worker")
            is False,
            "scheduled_write_false": receipt.get("safety", {}).get("scheduled_write") is False,
            "promotion_status_unchanged": _promotion_statuses(settings) == before,
            "no_audit_file": not (root / "audit" / "promotions_applied.jsonl").exists(),
        }
        return {
            "result": "pass" if all(checks.values()) else "fail",
            "read_only": True,
            "mutated": False,
            "promotion_id": promotion_id,
            "checks": checks,
            "receipt_preview": {
                "event": receipt.get("event"),
                "imported": receipt.get("imported"),
                "applied": receipt.get("applied"),
                "approved_proxy_action": receipt.get("approved_proxy_action"),
                "writes": receipt.get("writes"),
                "rollback": receipt.get("rollback"),
            },
        }


def main() -> int:
    payload = run_harness()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
