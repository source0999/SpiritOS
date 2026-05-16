from __future__ import annotations

from pathlib import Path
import hashlib
import hmac
import json
import os
import sys

from fastapi import APIRouter, Header, HTTPException, Request

from source_proxy.proxy_memory.scout_intake import (
    ScoutIntakeConfigError,
    write as write_scout_intake,
)

router = APIRouter(prefix="/v1/scout-intake")


def _ensure_scout_schema_importable() -> None:
    for candidate in [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve(), *Path(__file__).resolve().parents]:
        scout_src = candidate / "scout" / "src"
        if scout_src.is_dir() and str(scout_src) not in sys.path:
            sys.path.insert(0, str(scout_src))
            return


def _secret() -> str:
    value = os.environ.get("SCOUT_PROMOTION_SIGNING_KEY", "")
    if not value:
        raise HTTPException(status_code=503, detail="SCOUT_PROMOTION_SIGNING_KEY is required")
    return value


def _verify_signature(body: bytes, signature_header: str | None) -> None:
    if not signature_header or not signature_header.startswith("sha256="):
        raise HTTPException(status_code=401, detail="missing Scout signature")
    expected = hmac.new(_secret().encode("utf-8"), body, hashlib.sha256).hexdigest()
    supplied = signature_header.removeprefix("sha256=")
    if not hmac.compare_digest(expected, supplied):
        raise HTTPException(status_code=401, detail="invalid Scout signature")


@router.post("/promotion")
async def ingest_scout_promotion(
    request: Request,
    x_scout_signature: str | None = Header(default=None),
) -> dict:
    body = await request.body()
    _verify_signature(body, x_scout_signature)
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid JSON") from exc
    if payload.get("approved") is not True:
        raise HTTPException(status_code=409, detail="promotion approval is required")

    _ensure_scout_schema_importable()
    from scout.debugger.verdict import DebuggerVerdict
    from scout.packets.schema import IntelligencePacket

    packet = IntelligencePacket.model_validate(payload.get("packet"))
    verdict = DebuggerVerdict.model_validate(payload.get("verdict"))
    if verdict.decision != "promote":
        raise HTTPException(status_code=409, detail="verdict must be promote")
    if verdict.packet_id != packet.packet_id:
        raise HTTPException(status_code=409, detail="packet/verdict mismatch")

    try:
        result = write_scout_intake(
            packet,
            verdict,
            promotion_id=str(payload.get("promotion_id")),
            approved_by=str(payload.get("approved_by") or "human"),
        )
    except ScoutIntakeConfigError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"ok": True, "result": result}
