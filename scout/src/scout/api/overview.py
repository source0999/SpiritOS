from fastapi import APIRouter, Query

from scout.api.packets import _row_to_packet_dict
from scout.api.source_trust import classify_source
from scout.config import get_settings
from scout.storage.db import open_connection

router = APIRouter(prefix="/v1/scout")


def _table_count(conn, table_name: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


def _distinct_source_count(conn) -> int:
    return conn.execute("SELECT COUNT(DISTINCT source_uri) FROM source_tracking").fetchone()[0]


def _pending_artifact_count(conn) -> int:
    return conn.execute(
        """
        SELECT COUNT(*)
        FROM extracted_artifacts ea
        LEFT JOIN packets p
          ON json_extract(
              p.packet_json,
              '$.provenance.raw_event_id'
          ) = ea.event_id
        WHERE p.packet_id IS NULL
        """
    ).fetchone()[0]


def _debugger_pending_without_verdict_count(conn) -> int:
    return conn.execute(
        """
        SELECT COUNT(*)
        FROM packets p
        LEFT JOIN verdicts v ON v.packet_id = p.packet_id
        WHERE p.status = 'debugger_pending' AND v.packet_id IS NULL
        """
    ).fetchone()[0]


def _packet_synthesis_status(settings, backlog: dict) -> dict:
    route_configured = bool(settings.litellm_api_base)
    pending_artifacts = int(backlog.get("unsynthesized_artifacts") or 0)
    if not settings.litellm_model:
        state = "not_configured"
        label = "Packet model not configured"
        help_text = "Scout cannot synthesize model-backed packets until a LiteLLM model is configured."
    elif not route_configured and settings.litellm_model.lower().startswith("ollama/"):
        state = "route_missing"
        label = "Ollama route missing"
        help_text = "Set a Scout-reachable Ollama API base before claiming packet synthesis is model-backed ready."
    elif pending_artifacts > 0:
        state = "pending"
        label = "Packet synthesis pending"
        help_text = f"{pending_artifacts} extracted artifact(s) are waiting for packet synthesis."
    else:
        state = "ready"
        label = "Packet synthesis ready"
        help_text = "Model route is configured and no extracted artifacts are waiting for synthesis."

    return {
        "state": state,
        "label": label,
        "help": help_text,
        "model": settings.litellm_model,
        "api_base": settings.litellm_api_base,
        "timeout_seconds": settings.litellm_timeout_seconds,
        "route_configured": route_configured,
        "pending_artifacts": pending_artifacts,
    }


def _human_summary(
    counts: dict,
    backlog: dict,
    promotion_status: dict,
    packet_synthesis_status: dict,
) -> dict:
    raw = counts["raw_event_index"]
    extracted = counts["extracted_artifacts"]
    packets = counts["packets"]
    verdicts = counts["verdicts"]
    pending_debugger = backlog["debugger_pending_without_verdict"]

    if raw == extracted == packets == verdicts == 0:
        pipeline_health = "idle"
        headline = "Scout is ready, but has not scanned any source items yet."
    elif raw > 0 and packets == 0:
        pipeline_health = "needs_review"
        headline = "Scout scanned sources, but summaries have not been created yet."
    elif packets > verdicts or pending_debugger > 0:
        pipeline_health = "needs_review"
        headline = "Scout has packets waiting for debugger review."
    elif raw == extracted == packets == verdicts and raw > 0:
        pipeline_health = "healthy"
        headline = "Scout processed all scanned items into checked intelligence packets."
    else:
        pipeline_health = "needs_review"
        headline = "Scout is running, with some pipeline counts still catching up."

    embeddings = counts.get("packet_embeddings", 0)
    memory_active = embeddings > 0
    memory_status = {
        "label": "Semantic memory active" if memory_active else "Semantic memory inactive",
        "active": memory_active,
        "state": "read_only_context" if memory_active else "inactive",
        "write_enabled": False,
        "mode_label": "Read-only context" if memory_active else "Inactive",
        "safety_label": (
            "Scout is not writing to proxy memory or coding context automatically."
        ),
    }
    if not memory_active:
        memory_status["reason"] = (
            "Scout is storing packets and source decisions, but it is not writing into proxy memory or coding context automatically."
        )
    else:
        memory_status["reason"] = (
            "Packet embeddings are available for Scout context, but memory writes still require an explicit approved bridge."
        )

    return {
        "pipeline_health": pipeline_health,
        "headline": headline,
        "scan_flow": [
            {
                "id": "scanned",
                "label": "Scanned",
                "count": raw,
                "help": "Unique source events Scout noticed from approved sources.",
            },
            {
                "id": "cleaned",
                "label": "Cleaned",
                "count": extracted,
                "help": "Pages or commits converted into readable artifacts.",
            },
            {
                "id": "summarized",
                "label": "Summarized",
                "count": packets,
                "help": "Scout intelligence packets created.",
            },
            {
                "id": "checked",
                "label": "Checked",
                "count": verdicts,
                "help": "Packets reviewed by the Scout debugger.",
            },
        ],
        "memory_status": memory_status,
        "promotion_status": promotion_status,
        "packet_synthesis_status": packet_synthesis_status,
    }


def _promotion_status(conn) -> dict:
    row = conn.execute(
        """
        SELECT
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END)
                AS promoted_count,
            SUM(CASE WHEN status = 'queued' THEN 1 ELSE 0 END)
                AS pending_review_count,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END)
                AS rejected_count
        FROM promotion_queue
        """
    ).fetchone()
    promoted_count = int(row["promoted_count"] or 0)
    pending_review_count = int(row["pending_review_count"] or 0)
    rejected_count = int(row["rejected_count"] or 0)
    if promoted_count == 0 and pending_review_count == 0:
        label = "No human-approved memory promotions yet"
    elif pending_review_count:
        label = f"{pending_review_count} memory promotion pending human review"
    else:
        label = f"{promoted_count} human-approved memory promotion"
    return {
        "promoted_count": promoted_count,
        "pending_review_count": pending_review_count,
        "rejected_count": rejected_count,
        "label": label,
    }


def _epoch_to_iso(value) -> str | None:
    if value is None:
        return None
    from datetime import datetime, timezone

    return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()


def _source_summaries(conn) -> list[dict]:
    source_rows = conn.execute(
        """
        SELECT source_uri,
               MAX(last_polled_epoch) AS last_polled_epoch,
               MAX(last_modified) AS last_modified,
               MAX(consecutive_failures) AS consecutive_failures,
               MIN(ratelimit_remaining) AS ratelimit_remaining
        FROM source_tracking
        GROUP BY source_uri
        """
    ).fetchall()
    source_uris = {row["source_uri"] for row in source_rows}
    for table in ("raw_event_index", "extracted_artifacts", "packets"):
        for row in conn.execute(f"SELECT DISTINCT source_uri FROM {table}").fetchall():
            source_uris.add(row["source_uri"])

    tracking = {row["source_uri"]: row for row in source_rows}
    result: list[dict] = []
    for source_uri in sorted(source_uris):
        trust = classify_source(source_uri)
        tracked = tracking.get(source_uri)
        packet_row = conn.execute(
            """
            SELECT
                COUNT(p.packet_id) AS packets_total,
                SUM(CASE WHEN v.decision = 'surface' OR p.status = 'surfaced' THEN 1 ELSE 0 END)
                    AS packets_surfaced,
                SUM(CASE WHEN v.decision = 'store' OR p.status = 'stored' THEN 1 ELSE 0 END)
                    AS packets_stored,
                SUM(CASE WHEN v.decision = 'ignore' OR p.status = 'ignored' THEN 1 ELSE 0 END)
                    AS packets_ignored
            FROM packets p
            LEFT JOIN verdicts v ON v.packet_id = p.packet_id
            WHERE p.source_uri = ?
            """,
            (source_uri,),
        ).fetchone()
        quality_row = conn.execute(
            "SELECT score FROM source_quality WHERE source_uri = ?",
            (source_uri,),
        ).fetchone()
        failures = int(tracked["consecutive_failures"] or 0) if tracked else 0
        health_label = "Needs review" if failures else "Healthy"
        if not tracked:
            health_label = "Idle"
        result.append(
            {
                "source_uri": source_uri,
                "label": trust.label,
                "trust_category": trust.category,
                "trust_label": trust.trust_label,
                "trust_tier": trust.trust_tier,
                "last_polled_at": _epoch_to_iso(tracked["last_polled_epoch"]) if tracked else None,
                "last_modified": tracked["last_modified"] if tracked else None,
                "consecutive_failures": failures,
                "rate_limit_remaining": tracked["ratelimit_remaining"] if tracked else None,
                "health_label": health_label,
                "packets_total": int(packet_row["packets_total"] or 0),
                "packets_surfaced": int(packet_row["packets_surfaced"] or 0),
                "packets_stored": int(packet_row["packets_stored"] or 0),
                "packets_ignored": int(packet_row["packets_ignored"] or 0),
                "source_quality_score": float(quality_row["score"]) if quality_row else None,
            }
        )
    return result


def _recent_packets_by_effective_status(
    conn,
    *,
    status: str,
    limit: int,
    q: str | None,
) -> list[dict]:
    decision_by_status = {
        "surfaced": "surface",
        "stored": "store",
        "ignored": "ignore",
        "promoted": "promote",
    }
    sql = """
        SELECT p.packet_json, p.status
        FROM packets p
        LEFT JOIN verdicts v ON v.packet_id = p.packet_id
    """
    params: list[str | int] = []
    clauses: list[str] = []
    if q:
        clauses.append("p.packet_json LIKE ?")
        params.append(f"%{q}%")
    if status == "debugger_pending":
        clauses.append("p.status = 'debugger_pending' AND v.packet_id IS NULL")
    else:
        clauses.append(
            "(p.status = ? OR (p.status = 'debugger_pending' AND v.decision = ?))"
        )
        params.extend([status, decision_by_status[status]])
    sql += " WHERE " + " AND ".join(f"({clause})" for clause in clauses)
    sql += " ORDER BY synthesized_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_packet_dict(conn, row, True) for row in rows]


def _scheduler_summary() -> dict:
    from scout.main import scheduler

    jobs = [
        {
            "id": job.id,
            "next_run_time": job.next_run_time.isoformat()
            if job.next_run_time
            else None,
        }
        for job in scheduler.get_jobs()
    ]
    return {
        "scheduler_running": scheduler.running,
        "job_count": len(jobs),
        "jobs": jobs,
    }


@router.get("/overview")
async def scout_overview(
    limit: int = Query(10, ge=1, le=50),
    q: str | None = Query(None, min_length=2, max_length=200),
) -> dict:
    settings = get_settings()
    conn = open_connection(settings.database_path)
    try:
        counts = {
            "raw_event_index": _table_count(conn, "raw_event_index"),
            "extracted_artifacts": _table_count(conn, "extracted_artifacts"),
            "packets": _table_count(conn, "packets"),
            "verdicts": _table_count(conn, "verdicts"),
            "packet_embeddings": _table_count(conn, "packet_embeddings"),
            "source_quality": _table_count(conn, "source_quality"),
            "promotion_queue": _table_count(conn, "promotion_queue"),
            "source_tracking": _distinct_source_count(conn),
        }
        backlog = {
            "unsynthesized_artifacts": _pending_artifact_count(conn),
            "debugger_pending_packets": conn.execute(
                "SELECT COUNT(*) FROM packets WHERE status = 'debugger_pending'"
            ).fetchone()[0],
            "debugger_pending_without_verdict": _debugger_pending_without_verdict_count(conn),
        }
        promotion_status = _promotion_status(conn)
        packet_synthesis_status = _packet_synthesis_status(settings, backlog)
        human_summary = _human_summary(
            counts,
            backlog,
            promotion_status,
            packet_synthesis_status,
        )
        sources = _source_summaries(conn)
        recent_surfaced = _recent_packets_by_effective_status(
            conn,
            status="surfaced",
            limit=limit,
            q=q,
        )
        recent_stored = _recent_packets_by_effective_status(
            conn,
            status="stored",
            limit=limit,
            q=q,
        )
        recent_pending = _recent_packets_by_effective_status(
            conn,
            status="debugger_pending",
            limit=limit,
            q=q,
        )
    finally:
        conn.close()

    return {
            "counts": counts,
            "backlog": backlog,
            "human_summary": human_summary,
            "packet_synthesis": packet_synthesis_status,
            "sources": sources,
        "recent": {
            "surfaced": recent_surfaced,
            "stored": recent_stored,
            "pending": recent_pending,
        },
        "scheduler": _scheduler_summary(),
    }


@router.get("/sources")
async def scout_sources() -> dict:
    settings = get_settings()
    conn = open_connection(settings.database_path)
    try:
        sources = _source_summaries(conn)
        return {"sources": sources, "count": len(sources)}
    finally:
        conn.close()
