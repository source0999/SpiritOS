import pytest

from scout.config import ScoutSettings
from scout.packets.storage import PacketCapError, insert_packet
from scout.storage.db import init_database, open_connection
from scout.storage.migrations import apply_migrations
from scout.tests.test_packet_schema import make_packet


def test_insert_packet_persists_packet_json(tmp_path):
    settings = ScoutSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "scout.db",
        vector_packet_cap=10,
    )
    init_database(settings.database_path)
    apply_migrations(settings.database_path)

    insert_packet(settings, make_packet())

    conn = open_connection(settings.database_path)
    try:
        row = conn.execute("SELECT packet_id, status FROM packets").fetchone()
    finally:
        conn.close()
    assert row["packet_id"] == "pkt_1"
    assert row["status"] == "debugger_pending"


def test_insert_packet_enforces_cap(tmp_path):
    settings = ScoutSettings(
        data_dir=tmp_path,
        database_path=tmp_path / "scout.db",
        vector_packet_cap=1,
    )
    init_database(settings.database_path)
    apply_migrations(settings.database_path)
    insert_packet(settings, make_packet("pkt_1"))

    with pytest.raises(PacketCapError):
        insert_packet(settings, make_packet("pkt_2"))
