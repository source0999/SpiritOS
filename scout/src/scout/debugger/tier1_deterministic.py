from __future__ import annotations

from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
import hashlib
import sqlite3

from scout.config import ScoutSettings
from scout.debugger.content_injection import CONTENT_INJECTION_PATTERNS
from scout.debugger.verdict import DebuggerFinding
from scout.packets.schema import IntelligencePacket
from scout.pollers.registry import load_registry
from scout.storage.db import open_connection

def _read_extracted_artifact_text(
    packet: IntelligencePacket, settings: ScoutSettings
) -> str:
    rel = packet.provenance.extracted_artifact_path
    if not rel:
        return ""
    root = settings.data_dir.resolve()
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return ""
    if not candidate.is_file():
        return ""
    return candidate.read_text(encoding="utf-8", errors="replace")


def _host(source_uri: str) -> str:
    if source_uri.startswith("github://"):
        return "github.com"
    return urlparse(source_uri).hostname or ""


def check_schema_completeness(packet_json: str) -> DebuggerFinding:
    try:
        IntelligencePacket.model_validate_json(packet_json)
    except Exception as exc:
        return DebuggerFinding(
            check_id="schema_completeness",
            tier=1,
            status="failed",
            detail=str(exc)[:4000],
        )
    return DebuggerFinding(
        check_id="schema_completeness",
        tier=1,
        status="passed",
        detail="packet validates against IntelligencePacket",
    )


def check_source_allowlist(packet: IntelligencePacket, settings: ScoutSettings) -> DebuggerFinding:
    registry = load_registry(settings.config_path)
    allowed_hosts = {"github.com"} if registry.github_repos else set()
    allowed_urls = {str(source.url) for source in registry.rss_feeds + registry.web_pages}
    source_host = _host(packet.source_uri)
    allowed = source_host in allowed_hosts or packet.source_uri in allowed_urls
    return DebuggerFinding(
        check_id="source_allowlist",
        tier=1,
        status="passed" if allowed else "failed",
        detail="source is allowlisted" if allowed else f"source not allowed: {packet.source_uri}",
    )


def check_injection_signature_regex(
    packet: IntelligencePacket, settings: ScoutSettings
) -> DebuggerFinding:
    packet_blob = "\n".join(
        [packet.summary, packet.impact_analysis, *[str(t) for t in packet.entity_tags]]
    )
    source_blob = _read_extracted_artifact_text(packet, settings)
    for label, text in ("packet", packet_blob), ("source", source_blob):
        for pattern in CONTENT_INJECTION_PATTERNS:
            match = pattern.search(text)
            if match:
                return DebuggerFinding(
                    check_id="injection_signature_regex",
                    tier=1,
                    status="failed",
                    detail=(
                        f"injection-like text matched ({label}): "
                        f"{match.group(0)[:120]}"
                    ),
                )
    return DebuggerFinding(
        check_id="injection_signature_regex",
        tier=1,
        status="passed",
        detail="no injection signatures detected",
    )


def check_duplicate(packet: IntelligencePacket, settings: ScoutSettings) -> DebuggerFinding:
    dupe_hash = hashlib.sha256(
        f"{packet.source_uri}|{packet.summary[:240]}".encode("utf-8")
    ).hexdigest()
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    conn = open_connection(settings.database_path)
    try:
        rows = conn.execute(
            """
            SELECT packet_id, packet_json FROM packets
            WHERE source_uri = ? AND timestamp >= ? AND packet_id != ?
            """,
            (packet.source_uri, cutoff.isoformat(), packet.packet_id),
        ).fetchall()
    except sqlite3.OperationalError as exc:
        return DebuggerFinding(
            check_id="duplicate",
            tier=1,
            status="skipped",
            detail=f"duplicate check skipped: {exc}",
        )
    finally:
        conn.close()
    for row in rows:
        other = IntelligencePacket.model_validate_json(row["packet_json"])
        other_hash = hashlib.sha256(
            f"{other.source_uri}|{other.summary[:240]}".encode("utf-8")
        ).hexdigest()
        if other_hash == dupe_hash:
            return DebuggerFinding(
                check_id="duplicate",
                tier=1,
                status="failed",
                detail=f"duplicate of packet {row['packet_id']}",
            )
    return DebuggerFinding(
        check_id="duplicate",
        tier=1,
        status="passed",
        detail="no duplicate detected in last 30 days",
    )


def check_staleness(packet: IntelligencePacket, ttl_days: int = 90) -> DebuggerFinding:
    timestamp = packet.timestamp
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    stale = datetime.now(timezone.utc) - timestamp > timedelta(days=ttl_days)
    return DebuggerFinding(
        check_id="staleness",
        tier=1,
        status="warning" if stale else "passed",
        detail=f"stale=true ttl_days={ttl_days}" if stale else "packet is within TTL",
    )


def check_evidence_sufficiency(packet: IntelligencePacket) -> DebuggerFinding:
    sufficient = bool(packet.entity_tags or packet.graph_relations)
    return DebuggerFinding(
        check_id="evidence_sufficiency",
        tier=1,
        status="passed" if sufficient else "failed",
        detail="packet has entity tags or graph relations"
        if sufficient
        else "packet lacks entity tags and graph relations",
    )


def run_tier1(
    packet: IntelligencePacket,
    packet_json: str,
    settings: ScoutSettings,
) -> tuple[list[DebuggerFinding], list[str], str | None]:
    findings = [
        check_schema_completeness(packet_json),
        check_source_allowlist(packet, settings),
        check_injection_signature_regex(packet, settings),
        check_duplicate(packet, settings),
        check_staleness(packet),
        check_evidence_sufficiency(packet),
    ]
    reason_codes: list[str] = []
    decision_cap: str | None = None
    by_id = {finding.check_id: finding for finding in findings}
    if by_id["source_allowlist"].status == "failed":
        reason_codes.append("source_not_allowed")
        decision_cap = "ignore"
    if by_id["duplicate"].status == "failed":
        reason_codes.append("duplicate")
        decision_cap = "ignore"
    if by_id["evidence_sufficiency"].status == "failed":
        reason_codes.append("insufficient_evidence")
        decision_cap = "ignore"
    if by_id["injection_signature_regex"].status == "failed":
        reason_codes.append("injection_signature")
        decision_cap = "surface"
    return findings, reason_codes, decision_cap
