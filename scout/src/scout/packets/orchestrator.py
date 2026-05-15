from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

import structlog

from scout.config import ScoutSettings
from scout.packets import synthesis
from scout.packets.synthesis import (
    PacketSynthesisFatalModelError,
    PacketSynthesisJsonInvalid,
)
from scout.packets.schema import IntelligencePacket
from scout.packets.storage import insert_packet
from scout.packets.untrusted_envelope import wrap_untrusted
from scout.storage.db import open_connection

logger = structlog.get_logger()


@dataclass(frozen=True)
class PacketSynthesisError:
    event_id: str
    artifact_path: str
    error: str


@dataclass(frozen=True)
class PacketSynthesisResult:
    checked: int
    processed: int
    skipped: int
    errors: list[PacketSynthesisError] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "checked": self.checked,
            "processed": self.processed,
            "skipped": self.skipped,
            "errors": [error.__dict__ for error in self.errors],
        }


def _resolve_artifact_path(data_dir: Path, artifact_path: str) -> Path:
    root = data_dir.resolve()
    path = Path(artifact_path)
    full_path = path if path.is_absolute() else root / path
    resolved = full_path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"artifact path escapes data_dir: {artifact_path}") from exc
    return resolved


def _packet_raw_event_ids(settings: ScoutSettings) -> set[str]:
    conn = open_connection(settings.database_path)
    try:
        rows = conn.execute("SELECT packet_json FROM packets").fetchall()
    finally:
        conn.close()

    raw_event_ids: set[str] = set()
    for row in rows:
        try:
            packet = IntelligencePacket.model_validate_json(row["packet_json"])
        except Exception:
            logger.warning("packet_provenance_unreadable")
            continue
        raw_event_ids.add(packet.provenance.raw_event_id)
    return raw_event_ids


def _load_candidate_artifacts(settings: ScoutSettings, *, limit: int) -> list:
    conn = open_connection(settings.database_path)
    try:
        try:
            return conn.execute(
                """
                SELECT
                    ea.event_id,
                    ea.source_uri,
                    ea.artifact_path,
                    ea.extracted_at_epoch,
                    rei.captured_at_epoch
                FROM extracted_artifacts ea
                LEFT JOIN raw_event_index rei ON rei.event_id = ea.event_id
                LEFT JOIN packets p
                  ON json_extract(
                      p.packet_json,
                      '$.provenance.raw_event_id'
                  ) = ea.event_id
                WHERE p.packet_id IS NULL
                ORDER BY ea.extracted_at_epoch ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        except sqlite3.OperationalError:
            return conn.execute(
                """
                SELECT
                    ea.event_id,
                    ea.source_uri,
                    ea.artifact_path,
                    ea.extracted_at_epoch,
                    rei.captured_at_epoch
                FROM extracted_artifacts ea
                LEFT JOIN raw_event_index rei ON rei.event_id = ea.event_id
                ORDER BY ea.extracted_at_epoch ASC
                """
            ).fetchall()
    finally:
        conn.close()


def _assert_tier0_wrapper_available(source_uri: str, content: str) -> None:
    wrapped = wrap_untrusted(source_uri, content, max_chars=1)
    if not wrapped.startswith("<untrusted_source ") or not wrapped.endswith(
        "</untrusted_source>"
    ):
        raise RuntimeError("Tier 0 untrusted envelope is unavailable")


def synthesize_pending_artifacts(
    settings: ScoutSettings, *, limit: int | None = None
) -> dict:
    limit = limit if limit is not None else settings.synthesis_batch_size
    rows = _load_candidate_artifacts(settings, limit=limit)
    existing_raw_event_ids = _packet_raw_event_ids(settings)
    rows = [
        row for row in rows if row["event_id"] not in existing_raw_event_ids
    ][:limit]

    processed = 0
    skipped = 0
    errors: list[PacketSynthesisError] = []

    for row in rows:
        event_id = row["event_id"]
        artifact_path = row["artifact_path"]
        if event_id in existing_raw_event_ids:
            skipped += 1
            continue

        try:
            full_path = _resolve_artifact_path(settings.data_dir, artifact_path)
            if not full_path.is_file():
                raise FileNotFoundError(f"artifact file not found: {artifact_path}")

            content = full_path.read_text(encoding="utf-8")
            _assert_tier0_wrapper_available(row["source_uri"], content)
            epoch = row["captured_at_epoch"] or row["extracted_at_epoch"]
            packet = synthesis.synthesize_packet(
                raw_event_id=event_id,
                source_uri=row["source_uri"],
                extracted_content=content,
                extracted_artifact_path=Path(artifact_path),
                source_timestamp=datetime.fromtimestamp(epoch, tz=timezone.utc),
                settings=settings,
            )
            insert_packet(settings, packet)
            existing_raw_event_ids.add(event_id)
            processed += 1
        except PacketSynthesisFatalModelError as exc:
            errors.append(
                PacketSynthesisError(
                    event_id=event_id,
                    artifact_path=artifact_path,
                    error=str(exc),
                )
            )
            logger.error(
                "packet_synthesis_model_failed",
                event_id=event_id,
                artifact_path=artifact_path,
                error=str(exc),
            )
            break
        except PacketSynthesisJsonInvalid as exc:
            errors.append(
                PacketSynthesisError(
                    event_id=event_id,
                    artifact_path=artifact_path,
                    error=str(exc),
                )
            )
            logger.warning(
                "packet_synthesis_json_invalid",
                event_id=event_id,
                artifact_path=artifact_path,
                error=str(exc),
                raw_model_output_truncated=getattr(
                    exc, "raw_model_output_truncated", ""
                )
                or None,
                parsed_model_truncated=getattr(exc, "parsed_model_truncated", "")
                or None,
            )
        except Exception as exc:
            errors.append(
                PacketSynthesisError(
                    event_id=event_id,
                    artifact_path=artifact_path,
                    error=str(exc),
                )
            )
            logger.warning(
                "packet_synthesis_artifact_failed",
                event_id=event_id,
                artifact_path=artifact_path,
                error=str(exc),
            )

    result = PacketSynthesisResult(
        checked=len(rows),
        processed=processed,
        skipped=skipped,
        errors=errors,
    )
    logger.info("packet_synthesis_run_complete", **result.as_dict())
    return result.as_dict()


def register_synthesis_job(scheduler, settings: ScoutSettings) -> None:
    scheduler.add_job(
        synthesize_pending_artifacts,
        "interval",
        minutes=2,
        id="packets:synthesize_pending_artifacts",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        args=[settings],
    )
