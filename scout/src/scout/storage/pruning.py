from __future__ import annotations

from datetime import datetime, timezone, timedelta

import structlog

from scout.config import ScoutSettings
from scout.storage.db import open_connection

logger = structlog.get_logger()


def prune_packet_embeddings(settings: ScoutSettings) -> dict:
    ignored_cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    stored_cutoff = (datetime.now(timezone.utc) - timedelta(days=180)).isoformat()
    conn = open_connection(settings.database_path)
    try:
        before = conn.execute("SELECT COUNT(*) FROM packet_embeddings").fetchone()[0]
        ignored_rows = conn.execute(
            """
            SELECT e.packet_id
            FROM packet_embeddings e
            JOIN packets p ON p.packet_id = e.packet_id
            WHERE p.status = 'ignored' AND p.timestamp < ?
            """,
            (ignored_cutoff,),
        ).fetchall()
        stored_rows = conn.execute(
            """
            SELECT e.packet_id
            FROM packet_embeddings e
            JOIN packets p ON p.packet_id = e.packet_id
            LEFT JOIN source_quality sq ON sq.source_uri = p.source_uri
            WHERE p.status = 'stored'
              AND p.timestamp < ?
              AND COALESCE(sq.score, 0.5) < 0.4
            """,
            (stored_cutoff,),
        ).fetchall()
        packet_ids = sorted(
            {row["packet_id"] for row in ignored_rows}
            | {row["packet_id"] for row in stored_rows}
        )
        for packet_id in packet_ids:
            conn.execute(
                "DELETE FROM packet_embeddings WHERE packet_id = ?",
                (packet_id,),
            )
        conn.commit()
        after = conn.execute("SELECT COUNT(*) FROM packet_embeddings").fetchone()[0]
    finally:
        conn.close()

    result = {
        "embeddings_before": before,
        "embeddings_after": after,
        "embeddings_pruned": before - after,
        "bytes_reclaimed_estimate": (before - after) * 384 * 4,
    }
    logger.info("packet_embedding_prune_complete", **result)
    return result


def register_pruning_job(scheduler, settings: ScoutSettings) -> None:
    scheduler.add_job(
        prune_packet_embeddings,
        "interval",
        weeks=1,
        id="storage:prune_packet_embeddings",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        args=[settings],
    )
