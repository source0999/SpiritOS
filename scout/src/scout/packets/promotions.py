from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import hmac
import json
import uuid

import httpx

from scout.api.human import status_explanation, verdict_decision
from scout.api.source_trust import classify_source
from scout.config import ScoutSettings
from scout.debugger.verdict import DebuggerVerdict
from scout.packets.schema import IntelligencePacket
from scout.storage.db import open_connection


class PromotionError(RuntimeError):
    pass


PROMOTION_LABELS = {
    "queued": "Queued for review",
    "approved": "Promoted",
    "rejected": "Rejected",
}

_DECISION_TO_STATUS = {
    "ignore": "ignored",
    "store": "stored",
    "surface": "surfaced",
    "promote": "promoted",
}

_QUEUEABLE_STATUSES = {"surfaced", "stored", "surface", "store"}


def _payload_sha(packet: IntelligencePacket) -> str:
    return hashlib.sha256(packet.model_dump_json().encode("utf-8")).hexdigest()


def _row_to_promotion_item(row) -> dict:
    item = dict(row)
    item["promotion_label"] = PROMOTION_LABELS.get(item.get("status"))
    return item


def _effective_status(raw_status: str | None, db_status: str | None, verdict: dict | None) -> str:
    decision = (verdict or {}).get("decision")
    verdict_status = _DECISION_TO_STATUS.get(decision)
    if db_status and db_status != "debugger_pending":
        return db_status
    if verdict_status:
        return verdict_status
    if db_status:
        return db_status
    return raw_status or "debugger_pending"


def _promotion_row_to_response(
    row,
    packet: IntelligencePacket,
    verdict: dict | None,
    *,
    idempotent: bool,
    previous_rejection: dict | None = None,
) -> dict:
    item = _row_to_promotion_item(row)
    packet_summary = _promotion_packet_summary(json.loads(packet.model_dump_json()), verdict)
    item.update(
        {
            "idempotent": idempotent,
            "summary": packet_summary["summary"],
            "source_label": packet_summary["source_label"],
            "trust_label": packet_summary["trust_label"],
            "human_status_label": packet_summary["human_status_label"],
            "effective_status": packet_summary["effective_status"],
            "entity_tags": packet_summary["entity_tags"],
            "packet": packet_summary,
        }
    )
    if previous_rejection:
        item["previous_rejection"] = previous_rejection
    return item


def queue_promotion(
    settings: ScoutSettings,
    packet_id: str,
    *,
    requested_by: str = "manual-review",
    reason: str | None = None,
    force: bool = False,
) -> dict:
    packet, verdict, db_status = load_packet_for_queue(settings, packet_id)
    verdict_dict = json.loads(verdict.model_dump_json()) if verdict else None
    effective_status = _effective_status(packet.status, db_status, verdict_dict)
    if effective_status not in _QUEUEABLE_STATUSES and not force:
        raise PromotionError(
            f"packet effective status is {effective_status!r}; manual queue requires surfaced or stored"
        )
    payload_sha = _payload_sha(packet)
    conn = open_connection(settings.database_path)
    try:
        existing = conn.execute(
            """
            SELECT *
            FROM promotion_queue
            WHERE packet_id = ? AND status IN ('queued', 'approved')
            ORDER BY
                CASE status WHEN 'queued' THEN 0 WHEN 'approved' THEN 1 ELSE 2 END,
                requested_at DESC
            LIMIT 1
            """,
            (packet_id,),
        ).fetchone()
        if existing:
            return _promotion_row_to_response(
                existing,
                packet,
                verdict_dict,
                idempotent=True,
            )

        rejected = conn.execute(
            """
            SELECT promotion_id, rejected_at, rejected_reason
            FROM promotion_queue
            WHERE packet_id = ? AND status = 'rejected'
            ORDER BY rejected_at DESC, requested_at DESC
            LIMIT 1
            """,
            (packet_id,),
        ).fetchone()
        previous_rejection = dict(rejected) if rejected else None

        promotion_id = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO promotion_queue (
                promotion_id, packet_id, requested_at, requested_by, reason,
                payload_sha256, status
            )
            VALUES (?, ?, ?, ?, ?, ?, 'queued')
            """,
            (
                promotion_id,
                packet_id,
                datetime.now(timezone.utc).isoformat(),
                requested_by,
                reason,
                payload_sha,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM promotion_queue WHERE promotion_id = ?",
            (promotion_id,),
        ).fetchone()
        return _promotion_row_to_response(
            row,
            packet,
            verdict_dict,
            idempotent=False,
            previous_rejection=previous_rejection,
        )
    finally:
        conn.close()


def load_packet_and_verdict(
    settings: ScoutSettings,
    packet_id: str,
) -> tuple[IntelligencePacket, DebuggerVerdict]:
    conn = open_connection(settings.database_path)
    try:
        row = conn.execute(
            """
            SELECT p.packet_json, v.verdict_json
            FROM packets p
            LEFT JOIN verdicts v ON v.packet_id = p.packet_id
            WHERE p.packet_id = ?
            """,
            (packet_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise PromotionError("packet not found")
    if not row["verdict_json"]:
        raise PromotionError("packet has no verdict")
    return (
        IntelligencePacket.model_validate_json(row["packet_json"]),
        DebuggerVerdict.model_validate_json(row["verdict_json"]),
    )


def load_packet_for_queue(
    settings: ScoutSettings,
    packet_id: str,
) -> tuple[IntelligencePacket, DebuggerVerdict | None, str | None]:
    conn = open_connection(settings.database_path)
    try:
        row = conn.execute(
            """
            SELECT p.packet_json, p.status, v.verdict_json
            FROM packets p
            LEFT JOIN verdicts v ON v.packet_id = p.packet_id
            WHERE p.packet_id = ?
            """,
            (packet_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise PromotionError("packet not found")
    try:
        packet = IntelligencePacket.model_validate_json(row["packet_json"])
        verdict = (
            DebuggerVerdict.model_validate_json(row["verdict_json"])
            if row["verdict_json"]
            else None
        )
    except Exception as exc:
        raise PromotionError("malformed packet") from exc
    return packet, verdict, row["status"]


def list_queued_promotions(settings: ScoutSettings) -> list[dict]:
    conn = open_connection(settings.database_path)
    try:
        rows = conn.execute(
            """
            SELECT promotion_id, packet_id, requested_at, requested_by, reason,
                   payload_sha256, status
            FROM promotion_queue
            WHERE status = 'queued'
            ORDER BY requested_at ASC
            """
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def _packet_title(packet: dict) -> str:
    summary = str(packet.get("summary") or "").strip()
    if not summary:
        return packet.get("packet_id") or "Scout packet"
    return summary.split(". ", 1)[0].strip()[:140]


def _promotion_packet_summary(packet: dict, verdict: dict | None) -> dict:
    source_uri = packet.get("source_uri")
    trust = classify_source(source_uri)
    raw_status = packet.get("status")
    decision = verdict_decision(verdict)
    effective_status = {
        "ignore": "ignored",
        "store": "stored",
        "surface": "surfaced",
        "promote": "promoted",
    }.get(decision or "", raw_status or "debugger_pending")
    explanation = status_explanation(
        raw_status=raw_status,
        verdict=verdict,
        effective_status=effective_status,
    )
    return {
        "title": _packet_title(packet),
        "summary": packet.get("summary"),
        "source_uri": source_uri,
        "source_label": trust.label,
        "trust_label": trust.trust_label,
        "human_status_label": explanation["label"],
        "effective_status": effective_status,
        "entity_tags": packet.get("entity_tags") or packet.get("tags") or [],
        "tags": packet.get("entity_tags") or packet.get("tags") or [],
    }


def list_promotions(settings: ScoutSettings) -> dict:
    conn = open_connection(settings.database_path)
    try:
        rows = conn.execute(
            """
            SELECT
                pq.promotion_id,
                pq.packet_id,
                pq.requested_at,
                pq.requested_by,
                pq.reason,
                pq.approved_at,
                pq.approved_by,
                pq.rejected_at,
                pq.rejected_reason,
                pq.status,
                pq.payload_sha256,
                p.packet_json,
                v.verdict_json
            FROM promotion_queue pq
            LEFT JOIN packets p ON p.packet_id = pq.packet_id
            LEFT JOIN verdicts v ON v.packet_id = pq.packet_id
            WHERE pq.status IN ('queued', 'approved', 'rejected')
            ORDER BY pq.requested_at DESC
            """
        ).fetchall()
        counts = {"pending": 0, "queued": 0, "approved": 0, "rejected": 0, "total": 0}
        items: list[dict] = []
        for row in rows:
            status = row["status"]
            counts["total"] += 1
            if status == "queued":
                counts["pending"] += 1
            if status in counts:
                counts[status] += 1
            packet = json.loads(row["packet_json"]) if row["packet_json"] else {}
            verdict = json.loads(row["verdict_json"]) if row["verdict_json"] else None
            packet_summary = _promotion_packet_summary(packet, verdict)
            items.append(
                {
                    "promotion_id": row["promotion_id"],
                    "packet_id": row["packet_id"],
                    "requested_at": row["requested_at"],
                    "requested_by": row["requested_by"],
                    "reason": row["reason"],
                    "approved_at": row["approved_at"],
                    "approved_by": row["approved_by"],
                    "rejected_at": row["rejected_at"],
                    "rejected_reason": row["rejected_reason"],
                    "status": status,
                    "payload_sha256": row["payload_sha256"],
                    "summary": packet_summary["summary"],
                    "source_label": packet_summary["source_label"],
                    "trust_label": packet_summary["trust_label"],
                    "human_status_label": packet_summary["human_status_label"],
                    "effective_status": packet_summary["effective_status"],
                    "entity_tags": packet_summary["entity_tags"],
                    "packet": packet_summary,
                }
            )
        return {
            "items": items,
            "queued": [item for item in items if item["status"] == "queued"],
            "approved": [item for item in items if item["status"] == "approved"],
            "rejected": [item for item in items if item["status"] == "rejected"],
            "counts": counts,
        }
    finally:
        conn.close()


def get_packet_promotion_state(settings: ScoutSettings, packet_id: str) -> dict | None:
    conn = open_connection(settings.database_path)
    try:
        row = conn.execute(
            """
            SELECT promotion_id, status, reason, requested_at
            FROM promotion_queue
            WHERE packet_id = ? AND status IN ('queued', 'approved', 'rejected')
            ORDER BY
                CASE status WHEN 'approved' THEN 0 WHEN 'queued' THEN 1 ELSE 2 END,
                requested_at DESC
            LIMIT 1
            """,
            (packet_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "promotion_id": row["promotion_id"],
            "promotion_status": row["status"],
            "promotion_label": PROMOTION_LABELS.get(row["status"]),
            "promotion_reason": row["reason"],
            "promotion_requested_at": row["requested_at"],
        }
    finally:
        conn.close()


def approve_promotion(
    settings: ScoutSettings,
    promotion_id: str,
    *,
    approved_by: str,
) -> dict:
    conn = open_connection(settings.database_path)
    try:
        cursor = conn.execute(
            """
            UPDATE promotion_queue
            SET status = 'approved', approved_at = ?, approved_by = ?
            WHERE promotion_id = ? AND status = 'queued'
            """,
            (datetime.now(timezone.utc).isoformat(), approved_by, promotion_id),
        )
        conn.commit()
        if cursor.rowcount != 1:
            raise PromotionError("queued promotion not found")
        row = conn.execute(
            "SELECT * FROM promotion_queue WHERE promotion_id = ?",
            (promotion_id,),
        ).fetchone()
        return _row_to_promotion_item(row)
    finally:
        conn.close()


def reject_promotion(settings: ScoutSettings, promotion_id: str, *, reason: str) -> dict:
    conn = open_connection(settings.database_path)
    try:
        cursor = conn.execute(
            """
            UPDATE promotion_queue
            SET status = 'rejected', rejected_at = ?, rejected_reason = ?
            WHERE promotion_id = ? AND status = 'queued'
            """,
            (datetime.now(timezone.utc).isoformat(), reason, promotion_id),
        )
        conn.commit()
        if cursor.rowcount != 1:
            raise PromotionError("queued promotion not found")
        row = conn.execute(
            "SELECT * FROM promotion_queue WHERE promotion_id = ?",
            (promotion_id,),
        ).fetchone()
        return _row_to_promotion_item(row)
    finally:
        conn.close()


def _sign_payload(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def _load_approved_promotion_payload(
    settings: ScoutSettings,
    promotion_id: str,
) -> tuple[dict, IntelligencePacket, DebuggerVerdict, bytes, str]:
    if not settings.promotion_signing_key:
        raise PromotionError("SCOUT_PROMOTION_SIGNING_KEY is required")
    conn = open_connection(settings.database_path)
    try:
        row = conn.execute(
            """
            SELECT promotion_id, packet_id, approved_at, approved_by, payload_sha256, status
            FROM promotion_queue
            WHERE promotion_id = ?
            """,
            (promotion_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise PromotionError("promotion not found")
    if row["status"] != "approved":
        raise PromotionError("promotion must be approved before import dry run")

    packet, verdict = load_packet_and_verdict(settings, row["packet_id"])
    if verdict.decision != "promote":
        raise PromotionError("verdict must still be promote")
    payload_sha = _payload_sha(packet)
    if row["payload_sha256"] != payload_sha:
        raise PromotionError("promotion payload hash no longer matches packet")

    payload = {
        "promotion_id": promotion_id,
        "approved": True,
        "approved_at": row["approved_at"],
        "approved_by": row["approved_by"],
        "packet": json.loads(packet.model_dump_json()),
        "verdict": json.loads(verdict.model_dump_json()),
        "payload_sha256": row["payload_sha256"],
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = _sign_payload(settings.promotion_signing_key, body)
    return dict(row), packet, verdict, body, signature


def _manual_import_receipt_preview(
    row: dict,
    packet: IntelligencePacket,
    verdict: DebuggerVerdict,
    body: bytes,
) -> dict:
    trust = classify_source(packet.source_uri)
    return {
        "receipt_version": 1,
        "event": "scout_manual_import_receipt_preview",
        "imported": False,
        "dry_run": True,
        "manual_controlled": True,
        "operator_required": True,
        "promotion_id": row["promotion_id"],
        "packet_id": packet.packet_id,
        "approved_by": row["approved_by"],
        "approved_at": row["approved_at"],
        "written_at": None,
        "intake_log_path": None,
        "payload_sha256": row["payload_sha256"],
        "signed_payload_sha256": hashlib.sha256(body).hexdigest(),
        "signature_key_hint": "configured",
        "verdict_decision": verdict.decision,
        "source_uri": packet.source_uri,
        "source_trust_label": trust.trust_label,
        "authority": "append_only_evidence",
        "applied": False,
        "approved_proxy_action": False,
        "writes": {
            "append_only_evidence": False,
            "proxy_memory": False,
            "coding_context": False,
            "active_context": False,
        },
        "rollback": {
            "promotion_id": row["promotion_id"],
            "intake_log_path": None,
            "rollback_action": "none_needed_for_dry_run",
            "tombstone_event": "scout_manual_import_tombstone",
            "delete_allowed": False,
        },
        "safety": {
            "automatic_packet_promotion": False,
            "proxy_memory_write": False,
            "coding_context_write": False,
            "active_context_changed": False,
            "source_activation": False,
            "discovery_job_created": False,
            "search_preview_ran": False,
            "candidate_extraction_ran": False,
            "apply_action": False,
            "commit": False,
            "push": False,
            "hidden_background_worker": False,
            "scheduled_write": False,
        },
    }


def dry_run_proxy_import(settings: ScoutSettings, promotion_id: str) -> dict:
    row, packet, verdict, body, signature = _load_approved_promotion_payload(
        settings,
        promotion_id,
    )
    return {
        "dry_run": True,
        "import_ready": True,
        "read_only": True,
        "mutation_allowed": False,
        "promotion_id": promotion_id,
        "packet_id": packet.packet_id,
        "approved_at": row["approved_at"],
        "approved_by": row["approved_by"],
        "verdict_decision": verdict.decision,
        "payload_sha256": row["payload_sha256"],
        "signed_payload_sha256": hashlib.sha256(body).hexdigest(),
        "signature_preview": f"sha256={signature[:12]}...",
        "proxy_intake_url": settings.promotion_proxy_intake_url,
        "receipt_preview": _manual_import_receipt_preview(row, packet, verdict, body),
        "would_call_proxy_intake": False,
        "would_write_proxy_memory": False,
        "would_write_coding_context": False,
        "would_finalize_promotion": False,
        "approval_required_before": [
            "proxy-intake-call",
            "proxy-memory-write",
            "coding-context-write",
        ],
        "forbidden_actions": [
            "automatic packet promotion",
            "proxy intake call",
            "proxy memory writes",
            "coding context writes",
            "promotion finalization",
            "hidden background workers",
            "scheduled writes",
        ],
    }


def _audit_path(settings: ScoutSettings) -> Path:
    path = settings.data_dir / "audit" / "promotions_applied.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _append_audit(settings: ScoutSettings, record: dict) -> None:
    with _audit_path(settings).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


async def finalize_approved_promotion(settings: ScoutSettings, promotion_id: str) -> dict:
    row, packet, verdict, body, signature = _load_approved_promotion_payload(
        settings,
        promotion_id,
    )

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            settings.promotion_proxy_intake_url,
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Scout-Signature": f"sha256={signature}",
            },
        )
    if response.status_code >= 400:
        raise PromotionError(f"proxy intake failed: HTTP {response.status_code}")
    result = response.json()

    conn = open_connection(settings.database_path)
    try:
        conn.execute(
            "UPDATE promotion_queue SET status = 'finalized' WHERE promotion_id = ?",
            (promotion_id,),
        )
        conn.commit()
    finally:
        conn.close()

    audit = {
        "event": "promotion_finalized",
        "promotion_id": promotion_id,
        "packet_id": packet.packet_id,
        "approved_at": row["approved_at"],
        "approved_by": row["approved_by"],
        "proxy_response": result,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    _append_audit(settings, audit)
    return audit
