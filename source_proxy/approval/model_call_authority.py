"""Durable, signed-session-issued authority for Campaign 3.5 model calls.

The authority deliberately stores only opaque identifiers and scope metadata.  A
caller never supplies an ``approved`` flag or a reusable token: every provider
call is checked against the durable grant using the current registered worktree
identity.
"""
from __future__ import annotations

import json
import os
import secrets
import sqlite3
import stat
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from source_proxy.approval.runtime_identity import (
    AuthorityRuntimeIdentity,
    AuthorityRuntimeIdentityError,
    resolve_authority_runtime_identity,
)


CAMPAIGN_ID = "campaign-3.5"
AUTHORIZED_BRANCH = "codex/campaign-3-5-execution-20260719"
ALLOWED_MODEL_ALIASES = frozenset({"coder", "local"})
ALLOWED_ACTIONS = frozenset({"model_call", "apply"})
MAX_AUTHORIZATION_MINUTES = 60


class ModelCallAuthorityError(ValueError):
    def __init__(self, reason_code: str, *, details: dict[str, Any] | None = None):
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.details = details or {}


@dataclass(frozen=True)
class ModelCallAuthorityReceipt:
    authorization_id: str
    campaign_id: str
    action: str
    model_alias: str
    run_id: str
    expires_at: str
    checked_at: str

    def as_payload(self) -> dict[str, str | bool]:
        return {
            "authorization_id": self.authorization_id,
            "campaign_id": self.campaign_id,
            "action": self.action,
            "model_alias": self.model_alias,
            "run_id": self.run_id,
            "expires_at": self.expires_at,
            "checked_at": self.checked_at,
            "model_call_authority_checked": True,
        }


def issue_campaign_3_5_model_call_authorization(
    *,
    operator: str,
    duration_minutes: int = 45,
) -> dict[str, Any]:
    """Issue one bounded, auditable authority after backend assertion validation."""
    identity = _identity()
    _require_authorized_branch(identity)
    _require_clean_worktree(identity)
    if not operator.strip():
        raise ModelCallAuthorityError("model_call_authority_operator_missing")
    duration = max(1, min(int(duration_minutes), MAX_AUTHORIZATION_MINUTES))
    now = _now()
    expires_at = now + timedelta(minutes=duration)
    authorization_id = f"mca_{secrets.token_urlsafe(18)}"
    database = _open_database(identity)
    try:
        database.execute("BEGIN IMMEDIATE")
        database.execute(
            "UPDATE campaign_model_call_authorizations_v1 "
            "SET state='revoked', revoked_at=? "
            "WHERE state='approved' AND campaign_id=? AND worktree=?",
            (_iso(now), CAMPAIGN_ID, identity.worktree),
        )
        database.execute(
            "INSERT INTO campaign_model_call_authorizations_v1 "
            "(id, generation, state, campaign_id, repository, worktree, branch, source_head, "
            "allowed_actions, allowed_model_aliases, operator, issued_at, expires_at, revoked_at) "
            "VALUES (?, 1, 'approved', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)",
            (
                authorization_id,
                CAMPAIGN_ID,
                identity.repository,
                identity.worktree,
                identity.branch,
                identity.source_head,
                json.dumps(sorted(ALLOWED_ACTIONS)),
                json.dumps(sorted(ALLOWED_MODEL_ALIASES)),
                operator,
                _iso(now),
                _iso(expires_at),
            ),
        )
        _append_event(
            database,
            authorization_id=authorization_id,
            event_type="model_call_authority_issued",
            run_id="campaign-3.5:operator-issuance",
            model_alias="not_applicable",
            result="approved",
        )
        database.execute("COMMIT")
    except Exception:
        if database.in_transaction:
            database.execute("ROLLBACK")
        raise
    finally:
        database.close()
    return {
        "schema_version": "campaign-3.5/model-call-authority/v1",
        "authorization_id": authorization_id,
        "generation": 1,
        "state": "approved",
        "campaign_id": CAMPAIGN_ID,
        "branch": identity.branch,
        "worktree": identity.worktree,
        "source_head": identity.source_head,
        "allowed_actions": sorted(ALLOWED_ACTIONS),
        "allowed_model_aliases": sorted(ALLOWED_MODEL_ALIASES),
        "expires_at": _iso(expires_at),
        "revocable": True,
        "secret_exposed": False,
    }


def validate_campaign_3_5_model_call_authorization(
    *,
    action: str,
    model_alias: str,
    run_id: str,
) -> ModelCallAuthorityReceipt:
    identity = _identity()
    _require_authorized_branch(identity)
    _require_clean_worktree(identity)
    if action not in ALLOWED_ACTIONS:
        raise ModelCallAuthorityError("model_call_authority_action_forbidden")
    if action == "model_call" and model_alias not in ALLOWED_MODEL_ALIASES:
        raise ModelCallAuthorityError("model_call_authority_model_forbidden")
    if not run_id.strip():
        raise ModelCallAuthorityError("model_call_authority_run_id_missing")
    database = _open_database(identity)
    try:
        row = database.execute(
            "SELECT * FROM campaign_model_call_authorizations_v1 "
            "WHERE state='approved' AND campaign_id=? AND repository=? AND worktree=? "
            "ORDER BY issued_at DESC LIMIT 1",
            (CAMPAIGN_ID, identity.repository, identity.worktree),
        ).fetchone()
        if row is None:
            raise ModelCallAuthorityError("model_call_authority_missing")
        if row["branch"] != identity.branch:
            raise ModelCallAuthorityError("model_call_authority_branch_mismatch")
        if row["source_head"] != identity.source_head:
            raise ModelCallAuthorityError("model_call_authority_source_head_mismatch")
        if datetime.fromisoformat(str(row["expires_at"])).astimezone(UTC) <= _now():
            database.execute(
                "UPDATE campaign_model_call_authorizations_v1 SET state='expired' WHERE id=?",
                (row["id"],),
            )
            raise ModelCallAuthorityError("model_call_authority_expired")
        aliases = set(json.loads(str(row["allowed_model_aliases"])))
        actions = set(json.loads(str(row["allowed_actions"])))
        if action not in actions:
            raise ModelCallAuthorityError("model_call_authority_action_forbidden")
        if action == "model_call" and model_alias not in aliases:
            raise ModelCallAuthorityError("model_call_authority_model_forbidden")
        _append_event(
            database,
            authorization_id=str(row["id"]),
            event_type="model_call_authority_checked",
            run_id=run_id,
            model_alias=model_alias,
            result="allowed",
        )
        database.commit()
        return ModelCallAuthorityReceipt(
            authorization_id=str(row["id"]),
            campaign_id=CAMPAIGN_ID,
            action=action,
            model_alias=model_alias,
            run_id=run_id,
            expires_at=str(row["expires_at"]),
            checked_at=_iso(),
        )
    finally:
        database.close()


def revoke_campaign_3_5_model_call_authorization(*, operator: str) -> dict[str, Any]:
    identity = _identity()
    _require_authorized_branch(identity)
    database = _open_database(identity)
    try:
        database.execute("BEGIN IMMEDIATE")
        row = database.execute(
            "SELECT id FROM campaign_model_call_authorizations_v1 "
            "WHERE state='approved' AND campaign_id=? AND repository=? AND worktree=? "
            "ORDER BY issued_at DESC LIMIT 1",
            (CAMPAIGN_ID, identity.repository, identity.worktree),
        ).fetchone()
        if row is None:
            raise ModelCallAuthorityError("model_call_authority_missing")
        database.execute(
            "UPDATE campaign_model_call_authorizations_v1 SET state='revoked', revoked_at=? WHERE id=?",
            (_iso(), row["id"]),
        )
        _append_event(
            database,
            authorization_id=str(row["id"]),
            event_type="model_call_authority_revoked",
            run_id="campaign-3.5:operator-revocation",
            model_alias="not_applicable",
            result=f"revoked_by:{operator}",
        )
        database.execute("COMMIT")
        return {"authorization_id": str(row["id"]), "state": "revoked", "secret_exposed": False}
    except Exception:
        if database.in_transaction:
            database.execute("ROLLBACK")
        raise
    finally:
        database.close()


def _identity() -> AuthorityRuntimeIdentity:
    try:
        return resolve_authority_runtime_identity()
    except AuthorityRuntimeIdentityError as error:
        raise ModelCallAuthorityError(error.reason_code) from error


def _require_authorized_branch(identity: AuthorityRuntimeIdentity) -> None:
    if identity.branch != AUTHORIZED_BRANCH:
        raise ModelCallAuthorityError("model_call_authority_branch_forbidden")


def _require_clean_worktree(identity: AuthorityRuntimeIdentity) -> None:
    try:
        status = subprocess.check_output(
            ["git", "-C", str(identity.root), "status", "--porcelain=v1", "--untracked-files=all"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise ModelCallAuthorityError("model_call_authority_worktree_status_unavailable") from error
    changed_paths = [line for line in status.splitlines() if line.strip()]
    if changed_paths == [" M next-env.d.ts"] and _is_generated_next_dev_routes_change(identity):
        return
    if changed_paths:
        raise ModelCallAuthorityError("model_call_authority_dirty_worktree")


def _is_generated_next_dev_routes_change(identity: AuthorityRuntimeIdentity) -> bool:
    try:
        committed = subprocess.check_output(
            ["git", "-C", str(identity.root), "show", "HEAD:next-env.d.ts"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        current = (identity.root / "next-env.d.ts").read_text(encoding="utf-8")
    except (OSError, subprocess.CalledProcessError):
        return False
    return current == committed.replace(
        'import "./.next/types/routes.d.ts";',
        'import "./.next/dev/types/routes.d.ts";',
    )


def _open_database(identity: AuthorityRuntimeIdentity) -> sqlite3.Connection:
    directory = identity.state_directory()
    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    if stat.S_IMODE(directory.stat().st_mode) != 0o700:
        raise ModelCallAuthorityError("model_call_authority_unsafe_directory_permissions")
    path = directory / "campaign-3.5-model-call-authority.sqlite3"
    database = sqlite3.connect(path, isolation_level=None)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA journal_mode=WAL")
    database.execute(
        "CREATE TABLE IF NOT EXISTS campaign_model_call_authorizations_v1 ("
        "id TEXT PRIMARY KEY, generation INTEGER NOT NULL, state TEXT NOT NULL, campaign_id TEXT NOT NULL, "
        "repository TEXT NOT NULL, worktree TEXT NOT NULL, branch TEXT NOT NULL, source_head TEXT NOT NULL, "
        "allowed_actions TEXT NOT NULL, allowed_model_aliases TEXT NOT NULL, operator TEXT NOT NULL, "
        "issued_at TEXT NOT NULL, expires_at TEXT NOT NULL, revoked_at TEXT)"
    )
    database.execute(
        "CREATE TABLE IF NOT EXISTS campaign_model_call_authority_events_v1 ("
        "id TEXT PRIMARY KEY, authorization_id TEXT NOT NULL, event_type TEXT NOT NULL, run_id TEXT NOT NULL, "
        "model_alias TEXT NOT NULL, result TEXT NOT NULL, created_at TEXT NOT NULL)"
    )
    os.chmod(path, 0o600)
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        database.close()
        raise ModelCallAuthorityError("model_call_authority_unsafe_database_permissions")
    return database


def _append_event(
    database: sqlite3.Connection,
    *,
    authorization_id: str,
    event_type: str,
    run_id: str,
    model_alias: str,
    result: str,
) -> None:
    database.execute(
        "INSERT INTO campaign_model_call_authority_events_v1 VALUES(?,?,?,?,?,?,?)",
        (f"mcae_{secrets.token_urlsafe(12)}", authorization_id, event_type, run_id, model_alias, result, _iso()),
    )


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime | None = None) -> str:
    return (value or _now()).isoformat()
