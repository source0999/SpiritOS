import json
import structlog

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from scout.api.human import (
    finding_summaries,
    status_explanation,
    usefulness_explanation,
    verdict_decision,
)
from scout.api.source_trust import classify_source
from scout.config import get_settings
from scout.debugger.runner import recheck_packet
from scout.packets.promotions import PROMOTION_LABELS, PromotionError, queue_promotion
from scout.storage.db import open_connection

router = APIRouter(prefix="/v1/scout/packets")
logger = structlog.get_logger()


class QueuePromotionRequest(BaseModel):
    requested_by: str | None = None
    reason: str | None = None
    force: bool = False

_VERDICT_TO_PACKET_STATUS = {
    "ignore": "ignored",
    "store": "stored",
    "surface": "surfaced",
    "promote": "promoted",
}


def _verdict_derived_status(verdict: dict | None) -> str | None:
    if not verdict:
        return None
    decision = verdict.get("decision")
    if not decision:
        return None
    return _VERDICT_TO_PACKET_STATUS.get(decision)


def _effective_status(
    raw_status: str | None,
    db_status: str | None,
    verdict: dict | None,
) -> str:
    """DB wins when it has left the pending queue; else verdict; else raw JSON."""
    verdict_status = _verdict_derived_status(verdict)
    if db_status and db_status != "debugger_pending":
        return db_status
    if verdict_status:
        return verdict_status
    if db_status:
        return db_status
    return raw_status or "debugger_pending"


def _enrich_packet_response(
    conn,
    packet: dict,
    db_status: str | None,
    attach_verdict: bool,
) -> dict:
    if attach_verdict:
        row = conn.execute(
            "SELECT verdict_json FROM verdicts WHERE packet_id = ?",
            (packet.get("packet_id"),),
        ).fetchone()
        if row:
            packet["_verdict"] = json.loads(row["verdict_json"])
    verdict = packet.get("_verdict")
    raw_status = packet.get("status")
    effective = _effective_status(raw_status, db_status, verdict)
    packet["raw_status"] = raw_status
    packet["db_status"] = db_status
    packet["effective_status"] = effective
    packet["status_explanation"] = status_explanation(
        raw_status=raw_status,
        verdict=verdict,
        effective_status=effective,
    )
    packet["human_status_label"] = packet["status_explanation"]["label"]
    packet.update(
        usefulness_explanation(
            raw_status=raw_status,
            verdict=verdict,
            effective_status=effective,
        )
    )
    source_uri = packet.get("source_uri") or (packet.get("provenance") or {}).get("source_uri")
    if source_uri:
        trust = classify_source(source_uri)
        packet["source_trust_label"] = trust.trust_label
    packet["status"] = effective
    promotion = _promotion_state_for_packet(conn, packet.get("packet_id"))
    packet["promotion_status"] = promotion["promotion_status"] if promotion else None
    packet["promotion_id"] = promotion["promotion_id"] if promotion else None
    packet["promotion_label"] = promotion["promotion_label"] if promotion else None
    packet["promotion_reason"] = promotion["promotion_reason"] if promotion else None
    packet["promotion_requested_at"] = (
        promotion["promotion_requested_at"] if promotion else None
    )
    return packet


def _promotion_state_for_packet(conn, packet_id: str | None) -> dict | None:
    if not packet_id:
        return None
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


def _row_to_packet_dict(conn, row, attach_verdict: bool) -> dict:
    packet = json.loads(row["packet_json"])
    db_status = row["status"] if "status" in row.keys() else None
    return _enrich_packet_response(conn, packet, db_status, attach_verdict)


def _packet_title(packet: dict) -> str:
    summary = str(packet.get("summary") or "").strip()
    if not summary:
        return packet.get("packet_id") or "Scout packet"
    sentence = summary.split(". ", 1)[0].strip()
    return sentence[:140]


def _packet_explorer_item(conn, row) -> dict:
    packet = _row_to_packet_dict(conn, row, True)
    verdict = packet.get("_verdict")
    provenance = packet.get("provenance") or {}
    source_uri = packet.get("source_uri")
    trust = classify_source(source_uri)
    raw_event_id = provenance.get("raw_event_id")
    captured_at = None
    extracted_at = None
    artifact_path = provenance.get("extracted_artifact_path")
    if raw_event_id:
        raw_row = conn.execute(
            "SELECT captured_at_epoch FROM raw_event_index WHERE event_id = ?",
            (raw_event_id,),
        ).fetchone()
        if raw_row:
            captured_at = raw_row["captured_at_epoch"]
        artifact_row = conn.execute(
            """
            SELECT artifact_path, extracted_at_epoch
            FROM extracted_artifacts
            WHERE event_id = ?
            """,
            (raw_event_id,),
        ).fetchone()
        if artifact_row:
            extracted_at = artifact_row["extracted_at_epoch"]
            artifact_path = artifact_path or artifact_row["artifact_path"]

    promotion = _promotion_state_for_packet(conn, packet.get("packet_id"))
    return {
        "packet_id": packet.get("packet_id"),
        "source_uri": source_uri,
        "source_label": trust.label,
        "trust_label": trust.trust_label,
        "trust_tier": trust.trust_tier,
        "title": _packet_title(packet),
        "summary": packet.get("summary"),
        "entity_tags": packet.get("entity_tags") or packet.get("tags") or [],
        "confidence_score": packet.get("confidence_score"),
        "raw_status": packet.get("raw_status"),
        "verdict_decision": verdict_decision(verdict),
        "effective_status": packet.get("effective_status"),
        "human_status_label": packet.get("human_status_label"),
        "status_explanation": packet.get("status_explanation"),
        "usefulness_label": packet.get("usefulness_label"),
        "usefulness_reason": packet.get("usefulness_reason"),
        "recommended_action": packet.get("recommended_action"),
        "confidence_label": packet.get("confidence_label"),
        "source_trust_label": packet.get("source_trust_label") or trust.trust_label,
        "reason_codes": (verdict or {}).get("reason_codes") or [],
        "findings": finding_summaries(verdict),
        "source_quality_score": (verdict or {}).get("source_quality_score"),
        "evaluated_at": (verdict or {}).get("evaluated_at"),
        "artifact_path": artifact_path,
        "captured_at_epoch": captured_at,
        "extracted_at_epoch": extracted_at,
        "synthesized_at": provenance.get("synthesized_at"),
        "promotion_status": promotion["promotion_status"] if promotion else None,
        "promotion_id": promotion["promotion_id"] if promotion else None,
        "promotion_label": promotion["promotion_label"] if promotion else None,
        "promotion_reason": promotion["promotion_reason"] if promotion else None,
        "promotion_requested_at": promotion["promotion_requested_at"] if promotion else None,
    }


@router.get("/recent")
async def recent_packets(
    limit: int = Query(50, ge=1, le=200),
    with_verdict: bool = Query(False),
) -> dict:
    conn = open_connection(get_settings().database_path)
    try:
        rows = conn.execute(
            """
            SELECT packet_json, status FROM packets
            ORDER BY synthesized_at DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        packets = [_row_to_packet_dict(conn, row, with_verdict) for row in rows]
        return {"packets": packets, "count": len(rows)}
    finally:
        conn.close()


@router.get("/by_decision/{decision}")
async def packets_by_decision(
    decision: str,
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    conn = open_connection(get_settings().database_path)
    try:
        rows = conn.execute(
            """
            SELECT p.packet_json, p.status
            FROM packets p
            JOIN verdicts v ON v.packet_id = p.packet_id
            WHERE v.decision = ?
            ORDER BY v.evaluated_at DESC
            LIMIT ?
            """,
            (decision, limit),
        ).fetchall()
        return {
            "packets": [_row_to_packet_dict(conn, row, True) for row in rows],
            "count": len(rows),
        }
    finally:
        conn.close()


@router.get("/search")
async def search_packets(
    q: str = Query(..., min_length=2, max_length=200),
    status: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    with_verdict: bool = Query(False),
) -> dict:
    conn = open_connection(get_settings().database_path)
    try:
        sql = """
            SELECT packet_json, status FROM packets
            WHERE packet_json LIKE ?
        """
        params: list[str | int] = [f"%{q}%"]
        if status:
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY synthesized_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        packets = [_row_to_packet_dict(conn, row, with_verdict) for row in rows]
        return {"packets": packets, "count": len(rows)}
    finally:
        conn.close()


@router.get("/explorer")
async def packet_explorer(
    decision: str | None = Query(None, pattern="^(surface|store|ignore|promote)$"),
    status: str | None = Query(
        None,
        pattern="^(surfaced|stored|ignored|promoted|debugger_pending)$",
    ),
    q: str | None = Query(None, min_length=2, max_length=200),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    conn = open_connection(get_settings().database_path)
    try:
        sql = """
            SELECT p.packet_json, p.status
            FROM packets p
            LEFT JOIN verdicts v ON v.packet_id = p.packet_id
        """
        clauses: list[str] = []
        params: list[str | int] = []
        if decision:
            clauses.append("v.decision = ?")
            params.append(decision)
        if status:
            clauses.append("p.status = ?")
            params.append(status)
        if q:
            clauses.append("p.packet_json LIKE ?")
            params.append(f"%{q}%")
        if clauses:
            sql += " WHERE " + " AND ".join(f"({clause})" for clause in clauses)
        sql += " ORDER BY COALESCE(v.evaluated_at, p.synthesized_at) DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        packets = [_packet_explorer_item(conn, row) for row in rows]
        return {"packets": packets, "count": len(packets)}
    finally:
        conn.close()


@router.get("/{packet_id}/verdict")
async def get_packet_verdict(packet_id: str) -> dict:
    conn = open_connection(get_settings().database_path)
    try:
        row = conn.execute(
            "SELECT verdict_json FROM verdicts WHERE packet_id = ?",
            (packet_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404)
        return {"verdict": row["verdict_json"]}
    finally:
        conn.close()


@router.post("/{packet_id}/queue_promotion")
async def queue_packet_promotion(
    packet_id: str,
    request: QueuePromotionRequest | None = None,
) -> dict:
    body = request or QueuePromotionRequest()
    try:
        promotion = queue_promotion(
            get_settings(),
            packet_id,
            requested_by=body.requested_by or "manual-review",
            reason=body.reason,
            force=body.force,
        )
    except PromotionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"promotion": promotion, "promotion_id": promotion["promotion_id"]}


@router.post("/{packet_id}/recheck")
async def recheck_single_packet(packet_id: str) -> dict:
    settings = get_settings()
    recheck_settings = settings.model_copy(
        update={
            "litellm_timeout_seconds": min(settings.litellm_timeout_seconds, 8),
        }
    )
    try:
        result = recheck_packet(
            recheck_settings,
            packet_id,
            include_tier3=False,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.warning(
            "manual_recheck_failed",
            packet_id=packet_id,
            error=str(exc),
            error_type=type(exc).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="manual packet recheck failed before writing a new verdict",
        ) from exc
    conn = open_connection(settings.database_path)
    try:
        row = conn.execute(
            "SELECT packet_json, status FROM packets WHERE packet_id = ?",
            (packet_id,),
        ).fetchone()
        packet = _row_to_packet_dict(conn, row, True) if row else None
    finally:
        conn.close()
    if packet:
        result["human_status_label"] = packet["human_status_label"]
        result["status_explanation"] = packet["status_explanation"]
    return result


@router.get("/{packet_id}")
async def get_packet(packet_id: str) -> dict:
    conn = open_connection(get_settings().database_path)
    try:
        row = conn.execute(
            "SELECT packet_json, status FROM packets WHERE packet_id = ?",
            (packet_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404)
        return {"packet": _row_to_packet_dict(conn, row, True)}
    finally:
        conn.close()
