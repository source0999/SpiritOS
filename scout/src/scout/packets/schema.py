from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SCOUT_PACKET_SCHEMA_VERSION = 1

PacketStatus = Literal["debugger_pending", "ignored", "stored", "surfaced", "promoted"]


class EntityRelation(BaseModel):
    source_entity: str
    target_entity: str
    relation_label: str


class PacketProvenance(BaseModel):
    raw_event_id: str
    extracted_artifact_path: str | None = None
    llm_model: str
    llm_latency_ms: int
    synthesized_at: datetime


class IntelligencePacket(BaseModel):
    schema_version: int = SCOUT_PACKET_SCHEMA_VERSION
    packet_id: str
    source_uri: str
    timestamp: datetime
    entity_tags: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=80, max_length=2000)
    impact_analysis: str = Field(min_length=80, max_length=4000)
    confidence_score: float = Field(ge=0.0, le=1.0)
    graph_relations: list[EntityRelation] = Field(default_factory=list)
    status: PacketStatus = "debugger_pending"
    provenance: PacketProvenance
