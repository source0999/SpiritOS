from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from scout.config import ScoutSettings
from scout.debugger.verdict import DebuggerFinding
from scout.packets.schema import IntelligencePacket
from scout.storage.db import open_connection


def update_source_quality(settings: ScoutSettings, source_uri: str) -> float:
    conn = open_connection(settings.database_path)
    try:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN decision = 'promote' THEN 1 ELSE 0 END) AS promoted,
                SUM(CASE WHEN decision = 'surface' THEN 1 ELSE 0 END) AS surfaced,
                SUM(CASE WHEN decision = 'ignore' THEN 1 ELSE 0 END) AS ignored
            FROM verdicts v
            JOIN packets p ON p.packet_id = v.packet_id
            WHERE p.source_uri = ?
            """,
            (source_uri,),
        ).fetchone()
        total = int(row["total"] or 0)
        promoted = int(row["promoted"] or 0)
        surfaced = int(row["surfaced"] or 0)
        ignored = int(row["ignored"] or 0)
        score = 0.5 if total == 0 else (promoted + 0.5 * surfaced) / max(1, total)
        conn.execute(
            """
            INSERT INTO source_quality (
                source_uri, packets_total, packets_promoted, packets_surfaced,
                packets_ignored, score, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_uri) DO UPDATE SET
                packets_total = excluded.packets_total,
                packets_promoted = excluded.packets_promoted,
                packets_surfaced = excluded.packets_surfaced,
                packets_ignored = excluded.packets_ignored,
                score = excluded.score,
                updated_at = excluded.updated_at
            """,
            (
                source_uri,
                total,
                promoted,
                surfaced,
                ignored,
                score,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        return float(score)
    finally:
        conn.close()


def load_topic_anchors(config_path: Path) -> set[str]:
    path = config_path.parent / "topic_anchors.yaml"
    if not path.exists():
        return set()
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    anchors = raw.get("anchors") or []
    return {str(anchor).strip().lower() for anchor in anchors if str(anchor).strip()}


def run_tier2(
    packet: IntelligencePacket,
    settings: ScoutSettings,
) -> tuple[list[DebuggerFinding], list[str], str, float]:
    findings: list[DebuggerFinding] = []
    reason_codes: list[str] = []
    source_quality = update_source_quality(settings, packet.source_uri)
    findings.append(
        DebuggerFinding(
            check_id="source_quality_score",
            tier=2,
            status="passed",
            detail=f"source_quality_score={source_quality:.3f}",
        )
    )

    anchors = load_topic_anchors(settings.config_path)
    tags = {tag.lower() for tag in packet.entity_tags}
    anchor_hits = tags & anchors
    union = tags | anchors
    jaccard = len(anchor_hits) / max(1, len(union))
    tag_anchor_coverage = len(anchor_hits) / max(1, len(tags))
    hits_repr = sorted(anchor_hits)

    if not anchor_hits:
        reason_codes.append("low_topic_overlap")
        relevance_status = "warning"
        decision = "store"
    else:
        relevance_status = "passed"
        decision = "surface"
    findings.append(
        DebuggerFinding(
            check_id="relevance_anchor",
            tier=2,
            status=relevance_status,
            detail=(
                f"anchor_hits={hits_repr!r}; jaccard={jaccard:.3f}; "
                f"tag_anchor_coverage={tag_anchor_coverage:.3f}; "
                f"confidence={packet.confidence_score:.3f}"
            ),
        )
    )

    if packet.confidence_score < 0.4:
        reason_codes.append("confidence_floor")
        decision = "store"
        confidence_status = "warning"
    else:
        confidence_status = "passed"
    findings.append(
        DebuggerFinding(
            check_id="confidence_floor",
            tier=2,
            status=confidence_status,
            detail=f"confidence_score={packet.confidence_score:.3f}",
        )
    )
    return findings, reason_codes, decision, source_quality
