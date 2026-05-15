from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SCOUT_VERDICT_SCHEMA_VERSION = 1

VerdictDecision = Literal["ignore", "store", "surface", "promote"]


class DebuggerFinding(BaseModel):
    check_id: str
    tier: int
    status: Literal["passed", "failed", "warning", "skipped"]
    detail: str = Field(max_length=4000)


class DebuggerVerdict(BaseModel):
    schema_version: int = SCOUT_VERDICT_SCHEMA_VERSION
    packet_id: str
    decision: VerdictDecision
    tier_reached: int
    reason_codes: list[str] = Field(default_factory=list)
    findings: list[DebuggerFinding] = Field(default_factory=list)
    source_quality_score: float = Field(ge=0.0, le=1.0)
    evaluated_at: datetime
