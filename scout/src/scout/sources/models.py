from __future__ import annotations

from dataclasses import dataclass, field
import json
import sqlite3
from typing import Any


def _json_object(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(value)
    return parsed if isinstance(parsed, dict) else {}


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    parsed = json.loads(value)
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


@dataclass(frozen=True)
class SourceRegistryEntry:
    source_id: str
    canonical_uri: str
    display_uri: str
    source_kind: str
    trust_label: str | None = None
    trust_tier: str | None = None
    status: str = "active"
    poll_interval_minutes: int | None = None
    approved_at: str | None = None
    approved_by: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> SourceRegistryEntry:
        return cls(
            source_id=row["source_id"],
            canonical_uri=row["canonical_uri"],
            display_uri=row["display_uri"],
            source_kind=row["source_kind"],
            trust_label=row["trust_label"],
            trust_tier=row["trust_tier"],
            status=row["status"],
            poll_interval_minutes=row["poll_interval_minutes"],
            approved_at=row["approved_at"],
            approved_by=row["approved_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=_json_object(row["metadata_json"]),
        )


@dataclass(frozen=True)
class SourceCandidate:
    candidate_id: str
    canonical_uri: str
    display_uri: str
    source_kind: str
    status: str
    confidence_score: float
    trust_label: str | None = None
    trust_tier: str | None = None
    recommendation: str | None = None
    discovered_from_uri: str | None = None
    discovered_from_event_id: str | None = None
    discovered_from_packet_id: str | None = None
    reason_codes: list[str] = field(default_factory=list)
    explanation: str | None = None
    first_seen_at: str | None = None
    last_seen_at: str | None = None
    reviewed_at: str | None = None
    reviewed_by: str | None = None
    rejection_reason: str | None = None
    blocked_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> SourceCandidate:
        return cls(
            candidate_id=row["candidate_id"],
            canonical_uri=row["canonical_uri"],
            display_uri=row["display_uri"],
            source_kind=row["source_kind"],
            status=row["status"],
            confidence_score=row["confidence_score"],
            trust_label=row["trust_label"],
            trust_tier=row["trust_tier"],
            recommendation=row["recommendation"],
            discovered_from_uri=row["discovered_from_uri"],
            discovered_from_event_id=row["discovered_from_event_id"],
            discovered_from_packet_id=row["discovered_from_packet_id"],
            reason_codes=_json_list(row["reason_codes_json"]),
            explanation=row["explanation"],
            first_seen_at=row["first_seen_at"],
            last_seen_at=row["last_seen_at"],
            reviewed_at=row["reviewed_at"],
            reviewed_by=row["reviewed_by"],
            rejection_reason=row["rejection_reason"],
            blocked_reason=row["blocked_reason"],
            metadata=_json_object(row["metadata_json"]),
        )
