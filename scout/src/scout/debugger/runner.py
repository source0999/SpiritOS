from __future__ import annotations

from datetime import datetime, timezone
import json

import structlog

from scout.config import ScoutSettings
from scout.debugger.tier1_deterministic import run_tier1
from scout.debugger.tier2_structural import run_tier2
from scout.debugger.tier3_llm import run_tier3
from scout.debugger.verdict import DebuggerFinding, DebuggerVerdict
from scout.packets.schema import IntelligencePacket
from scout.storage.db import open_connection

logger = structlog.get_logger()


STATUS_BY_DECISION = {
    "ignore": "ignored",
    "store": "stored",
    "surface": "surfaced",
    "promote": "promoted",
}


def _load_pending(settings: ScoutSettings) -> list:
    conn = open_connection(settings.database_path)
    try:
        return conn.execute(
            """
            SELECT packet_id, packet_json
            FROM packets
            WHERE status = 'debugger_pending'
            ORDER BY synthesized_at ASC
            LIMIT ?
            """,
            (settings.debugger_batch_size,),
        ).fetchall()
    finally:
        conn.close()


def _write_verdict(settings: ScoutSettings, verdict: DebuggerVerdict) -> None:
    conn = open_connection(settings.database_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            """
            INSERT OR REPLACE INTO verdicts (
                packet_id, decision, tier_reached, verdict_json, evaluated_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                verdict.packet_id,
                verdict.decision,
                verdict.tier_reached,
                verdict.model_dump_json(),
                verdict.evaluated_at.isoformat(),
            ),
        )
        conn.execute(
            """
            UPDATE packets
            SET status = ?
            WHERE packet_id = ?
            """,
            (STATUS_BY_DECISION[verdict.decision], verdict.packet_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def evaluate_packet(
    packet_json: str,
    settings: ScoutSettings,
    *,
    include_tier3: bool = True,
) -> DebuggerVerdict:
    packet = IntelligencePacket.model_validate_json(packet_json)
    findings, reason_codes, decision_cap = run_tier1(packet, packet_json, settings)
    tier_reached = 1
    source_quality = 0.5
    decision = decision_cap or "surface"

    hard_ignore = "source_not_allowed" in reason_codes or "duplicate" in reason_codes or "insufficient_evidence" in reason_codes
    if not hard_ignore and decision != "surface":
        pass
    if not hard_ignore:
        tier2_findings, tier2_reasons, tier2_decision, source_quality = run_tier2(
            packet,
            settings,
        )
        findings.extend(tier2_findings)
        reason_codes.extend(tier2_reasons)
        if decision == "surface":
            decision = tier2_decision
        tier_reached = 2

    if include_tier3:
        tier3_findings, tier3_reasons, tier3_decision = run_tier3(packet, settings, decision)
        findings.extend(tier3_findings)
        reason_codes.extend(tier3_reasons)
        decision = tier3_decision
        tier_reached = max(tier_reached, 3)
    else:
        findings.append(
            DebuggerFinding(
                check_id="tier3_manual_recheck",
                tier=3,
                status="skipped",
                detail="Tier 3 LLM checks skipped for bounded manual recheck",
            )
        )

    return DebuggerVerdict(
        packet_id=packet.packet_id,
        decision=decision,
        tier_reached=tier_reached,
        reason_codes=list(dict.fromkeys(reason_codes)),
        findings=findings,
        source_quality_score=source_quality,
        evaluated_at=datetime.now(timezone.utc),
    )


def process_pending_packets(settings: ScoutSettings) -> dict:
    rows = _load_pending(settings)
    processed = 0
    errors = 0
    for row in rows:
        try:
            verdict = evaluate_packet(row["packet_json"], settings)
            _write_verdict(settings, verdict)
            processed += 1
        except Exception as exc:
            errors += 1
            logger.warning(
                "debugger_packet_failed",
                packet_id=row["packet_id"],
                error=str(exc),
            )
    result = {"checked": len(rows), "processed": processed, "errors": errors}
    logger.info("debugger_run_complete", **result)
    return result


def recheck_packet(
    settings: ScoutSettings,
    packet_id: str,
    *,
    include_tier3: bool = True,
) -> dict:
    conn = open_connection(settings.database_path)
    try:
        row = conn.execute(
            """
            SELECT packet_json
            FROM packets
            WHERE packet_id = ?
            """,
            (packet_id,),
        ).fetchone()
        previous_row = conn.execute(
            """
            SELECT decision, verdict_json
            FROM verdicts
            WHERE packet_id = ?
            """,
            (packet_id,),
        ).fetchone()
    finally:
        conn.close()

    if not row:
        raise ValueError("packet not found")

    previous_verdict = (
        json.loads(previous_row["verdict_json"]) if previous_row and previous_row["verdict_json"] else None
    )
    verdict = evaluate_packet(row["packet_json"], settings, include_tier3=include_tier3)
    _write_verdict(settings, verdict)
    new_verdict = json.loads(verdict.model_dump_json())
    previous_status = (
        STATUS_BY_DECISION.get(previous_verdict.get("decision"))
        if previous_verdict
        else None
    )
    new_status = STATUS_BY_DECISION[verdict.decision]
    return {
        "packet_id": packet_id,
        "previous": {
            "decision": previous_verdict.get("decision") if previous_verdict else None,
            "status": previous_status,
        },
        "new": {
            "decision": verdict.decision,
            "status": new_status,
        },
        "changed": (previous_verdict or {}).get("decision") != verdict.decision,
        "findings": new_verdict.get("findings", []),
        "evaluated_at": verdict.evaluated_at.isoformat(),
    }


def register_debugger_job(scheduler, settings: ScoutSettings) -> None:
    scheduler.add_job(
        process_pending_packets,
        "interval",
        minutes=2,
        id="debugger:process_pending_packets",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        args=[settings],
    )
