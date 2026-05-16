from datetime import datetime, timezone
import json

from scout.packets.schema import IntelligencePacket, PacketProvenance


def make_packet(packet_id: str = "pkt_1") -> IntelligencePacket:
    return IntelligencePacket(
        packet_id=packet_id,
        source_uri="https://example.com/feed.xml",
        timestamp=datetime.now(timezone.utc),
        entity_tags=["example"],
        summary=(
            "This is a sufficiently long packet summary for Scout schema testing "
            "and it deliberately exceeds the eighty character minimum enforced by Pydantic."
        ),
        impact_analysis=(
            "This packet has enough impact analysis text to satisfy validation rules "
            "including the eighty character minimum required for IntelligencePacket fields."
        ),
        confidence_score=0.75,
        provenance=PacketProvenance(
            raw_event_id="raw_1",
            extracted_artifact_path="extracted/example/raw_1.md",
            llm_model="test-model",
            llm_latency_ms=10,
            synthesized_at=datetime.now(timezone.utc),
        ),
    )


def test_packet_schema_json_round_trips():
    schema = IntelligencePacket.model_json_schema()

    assert json.loads(json.dumps(schema))["title"] == "IntelligencePacket"


def test_packet_model_json_round_trips():
    packet = make_packet()

    restored = IntelligencePacket.model_validate_json(packet.model_dump_json())

    assert restored.packet_id == packet.packet_id
    assert restored.status == "debugger_pending"
