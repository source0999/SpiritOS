from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.parse import quote

import asyncpg

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS source_expenditure_log (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    model_alias TEXT NOT NULL,
    routed_model TEXT,
    provider TEXT,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd NUMERIC(18, 8) NOT NULL DEFAULT 0,
    latency_ms NUMERIC(12, 2),
    response_id TEXT
);

CREATE INDEX IF NOT EXISTS source_expenditure_user_project_created_idx
ON source_expenditure_log (user_id, project_id, created_at DESC);
"""


@dataclass(frozen=True)
class ExpenditureRecord:
    user_id: str
    project_id: str
    model_alias: str
    routed_model: str | None
    provider: str | None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: Decimal
    latency_ms: float | None
    response_id: str | None


async def initialize_expenditure_store() -> None:
    database_url = _database_url()
    if not database_url:
        logger.info("SOURCE_PROXY_DATABASE_URL is unset; expenditure logging disabled.")
        return

    connection = await asyncpg.connect(database_url)
    try:
        await connection.execute(SCHEMA_SQL)
    finally:
        await connection.close()


async def log_completion_expenditure(record: ExpenditureRecord) -> None:
    database_url = _database_url()
    if not database_url:
        return

    try:
        connection = await asyncpg.connect(database_url)
        try:
            await connection.execute(
                """
                INSERT INTO source_expenditure_log (
                    user_id,
                    project_id,
                    model_alias,
                    routed_model,
                    provider,
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                    cost_usd,
                    latency_ms,
                    response_id
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """,
                record.user_id,
                record.project_id,
                record.model_alias,
                record.routed_model,
                record.provider,
                record.prompt_tokens,
                record.completion_tokens,
                record.total_tokens,
                record.cost_usd,
                record.latency_ms,
                record.response_id,
            )
        finally:
            await connection.close()
    except Exception:
        logger.exception("Failed to asynchronously log completion expenditure.")


def build_expenditure_record(
    *,
    completion_payload: dict[str, Any],
    model_alias: str,
    provider: str | None,
    user_id: str,
    project_id: str,
    latency_ms: float,
) -> ExpenditureRecord:
    usage = completion_payload.get("usage") or {}
    return ExpenditureRecord(
        user_id=user_id,
        project_id=project_id,
        model_alias=model_alias,
        routed_model=completion_payload.get("model"),
        provider=provider,
        prompt_tokens=int(usage.get("prompt_tokens") or 0),
        completion_tokens=int(usage.get("completion_tokens") or 0),
        total_tokens=int(usage.get("total_tokens") or 0),
        cost_usd=_completion_cost(completion_payload),
        latency_ms=latency_ms,
        response_id=completion_payload.get("id"),
    )


def _completion_cost(completion_payload: dict[str, Any]) -> Decimal:
    try:
        import litellm

        return Decimal(
            str(litellm.completion_cost(completion_response=completion_payload))
        )
    except Exception:
        return Decimal("0")


def _database_url() -> str | None:
    value = os.getenv("SOURCE_PROXY_DATABASE_URL") or _default_database_url()
    if value.strip().lower() in {"", "0", "false", "none", "disabled"}:
        return None
    return value


def _default_database_url() -> str:
    user = os.getenv("SOURCE_PROXY_DATABASE_USER", "source_proxy")
    password = os.getenv("SOURCE_PROXY_DATABASE_PASSWORD", "source_proxy")
    host = os.getenv("SOURCE_PROXY_DATABASE_HOST", "localhost")
    port = os.getenv("SOURCE_PROXY_DATABASE_PORT", "5432")
    database = os.getenv("SOURCE_PROXY_DATABASE_NAME", "source_proxy")
    return (
        f"postgresql://{quote(user)}:{quote(password)}@"
        f"{host}:{port}/{quote(database)}"
    )
