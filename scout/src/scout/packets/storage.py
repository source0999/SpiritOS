from __future__ import annotations

from scout.config import ScoutSettings
from scout.packets.schema import IntelligencePacket
from scout.storage.db import open_connection


class PacketCapError(RuntimeError):
    pass


def insert_packet(settings: ScoutSettings, packet: IntelligencePacket) -> None:
    conn = open_connection(settings.database_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM packets").fetchone()[0]
        if count >= settings.vector_packet_cap:
            raise PacketCapError(
                f"packet cap reached: {count} >= {settings.vector_packet_cap}"
            )
        packet_json = packet.model_dump_json()
        conn.execute(
            """
            INSERT INTO packets (
                packet_id, schema_version, source_uri, timestamp, status,
                packet_json, synthesized_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                packet.packet_id,
                packet.schema_version,
                packet.source_uri,
                packet.timestamp.isoformat(),
                packet.status,
                packet_json,
                packet.provenance.synthesized_at.isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_packet_json(settings: ScoutSettings, packet_id: str) -> str | None:
    conn = open_connection(settings.database_path)
    try:
        row = conn.execute(
            "SELECT packet_json FROM packets WHERE packet_id = ?",
            (packet_id,),
        ).fetchone()
        return row["packet_json"] if row else None
    finally:
        conn.close()
