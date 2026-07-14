#!/usr/bin/env python3
"""Campaign 1 durable, server-owned approval authority."""

import hashlib
import json
import os
import secrets
import sqlite3
import stat
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

AUTHORITY_ID = "spiritos-approval-authority"
ISSUER_ID = "spiritos-approval-authority/campaign-1"
ROOT = "/home/source/SpiritOS-campaign-1-20260712"
REPOSITORY = "SpiritOS"
WORKTREE = ROOT
STATE_DIR = Path("/home/source/.local/state/spiritos/approvals")
DB_PATH = STATE_DIR / "approvals.sqlite3"
SECRET_DIR = Path("/home/source/.config/spiritos/secrets")
SECRET_PATH = SECRET_DIR / "approval-authority.env"
CONSUMER_OPERATIONS = {
    "design-writeback": "design_writeback",
    "coding-executor": "coding_execution",
    "spiritflix-admin-executor": "spiritflix_admin_mutation",
    "cartographer-transfer-consumer": "cartographer_selection_transfer",
}
ACKNOWLEDGEMENT_CONSUMERS = {"coding-reviewer", "coding-verifier", "spiritflix-admin-reviewer", "spiritflix-admin-verifier", "cartographer-reviewer", "cartographer-verifier", "evidence-recorder"}
TERMINAL_REASONS = {
    "consumed": "approval_already_consumed",
    "rejected": "approval_rejected",
    "cancelled": "approval_cancelled",
    "expired": "approval_expired",
    "superseded": "approval_superseded",
    "invalidated": "approval_invalidated",
}


def fail(reason):
    raise RuntimeError(reason)


def now():
    return datetime.now(timezone.utc)


def iso(value=None):
    return (value or now()).isoformat()


def require(data, field):
    value = data.get(field)
    if not isinstance(value, str) or not value:
        fail(f"approval_{field}_missing")
    return value


def ensure_directory(path):
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    if stat.S_IMODE(path.stat().st_mode) != 0o700:
        fail("approval_unsafe_directory_permissions")


def source_head():
    return subprocess.check_output(["git", "-C", ROOT, "rev-parse", "HEAD"], text=True).strip()


def boot():
    ensure_directory(SECRET_DIR)
    ensure_directory(STATE_DIR)
    if SECRET_PATH.exists():
        if stat.S_IMODE(SECRET_PATH.stat().st_mode) != 0o600:
            fail("approval_unsafe_secret_permissions")
        secret = SECRET_PATH.read_text().strip()
        if not secret.startswith("SPIRITOS_APPROVAL_HMAC_KEY="):
            fail("approval_secret_malformed")
        key = secret.split("=", 1)[1]
    else:
        key = secrets.token_urlsafe(48)
        descriptor = os.open(SECRET_PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as handle:
            handle.write(f"SPIRITOS_APPROVAL_HMAC_KEY={key}\n")

    database = sqlite3.connect(DB_PATH, isolation_level=None)
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA journal_mode=WAL")
    database.execute(
        """CREATE TABLE IF NOT EXISTS approval_previews_v3 (
        id TEXT PRIMARY KEY, generation INTEGER NOT NULL, state TEXT NOT NULL,
        repository TEXT NOT NULL, worktree TEXT NOT NULL, root TEXT NOT NULL,
        target TEXT NOT NULL, plugin TEXT NOT NULL, content_hash TEXT NOT NULL,
        context_hash TEXT NOT NULL, source_head TEXT NOT NULL, created_at TEXT NOT NULL)"""
    )
    database.execute(
        """CREATE TABLE IF NOT EXISTS approval_records_v3 (
        id TEXT PRIMARY KEY, generation INTEGER NOT NULL, state TEXT NOT NULL,
        consumer TEXT NOT NULL, operation TEXT NOT NULL, repository TEXT NOT NULL,
        worktree TEXT NOT NULL, root TEXT NOT NULL, target TEXT NOT NULL,
        plugin TEXT NOT NULL, preview TEXT NOT NULL, content_hash TEXT NOT NULL,
        context TEXT NOT NULL, source_head TEXT NOT NULL, expires_at TEXT NOT NULL,
        result_id TEXT, evidence TEXT, created_at TEXT NOT NULL)"""
    )
    os.chmod(DB_PATH, 0o600)
    if stat.S_IMODE(DB_PATH.stat().st_mode) != 0o600:
        fail("approval_unsafe_database_permissions")
    return database, key


def exact_campaign_identity(data):
    if data.get("repository") != REPOSITORY:
        fail("approval_repository_mismatch")
    if data.get("worktree") != WORKTREE:
        fail("approval_worktree_mismatch")
    if os.path.realpath(str(data.get("root", ""))) != ROOT:
        fail("approval_root_mismatch")


def persist_preview(data):
    database, _ = boot()
    exact_campaign_identity(data)
    target = require(data, "target")
    plugin = require(data, "plugin")
    if plugin not in {"design-studio", "coding-shell", "dummy-product-site", "spiritflix-admin", "cartographer-transfer"}:
        fail("approval_plugin_mismatch")
    content_hash = require(data, "content_hash")
    context_hash = require(data, "context")
    if data.get("source_head") != source_head():
        fail("approval_source_mismatch")
    preview_id = f"prv_{secrets.token_urlsafe(18)}"
    database.execute(
        "INSERT INTO approval_previews_v3 VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
        (preview_id, 1, "previewed", REPOSITORY, WORKTREE, ROOT, target, plugin,
         content_hash, context_hash, source_head(), iso()),
    )
    print(json.dumps({"preview_id": preview_id, "generation": 1, "state": "previewed"}))


def parse_expiry(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        fail("approval_expiry_invalid")
    if parsed.tzinfo is None:
        fail("approval_expiry_invalid")
    if parsed <= now() or parsed > now() + timedelta(minutes=60):
        fail("approval_expiry_invalid")
    return parsed.astimezone(timezone.utc).isoformat()


def issue(data):
    database, key = boot()
    preview_id = require(data, "preview_id")
    expected_generation = require(data, "expected_generation")
    consumer = require(data, "consumer")
    operation = require(data, "operation")
    if CONSUMER_OPERATIONS.get(consumer) != operation:
        fail("approval_operation_not_permitted" if consumer in CONSUMER_OPERATIONS else "approval_consumer_mismatch")
    expiry = parse_expiry(require(data, "expires_at"))
    database.execute("BEGIN IMMEDIATE")
    try:
        preview = database.execute("SELECT * FROM approval_previews_v3 WHERE id=?", (preview_id,)).fetchone()
        if not preview:
            fail("approval_not_found")
        if str(preview["generation"]) != expected_generation:
            fail("approval_generation_mismatch")
        if preview["state"] != "previewed":
            fail("approval_not_approved")
        if preview["source_head"] != source_head():
            fail("approval_source_mismatch")
        approval_id = f"apr_{secrets.token_urlsafe(18)}"
        database.execute(
            """INSERT INTO approval_records_v3 VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (approval_id, preview["generation"], "approved", consumer, operation,
             preview["repository"], preview["worktree"], preview["root"], preview["target"],
             preview["plugin"], preview_id, preview["content_hash"], preview["context_hash"],
             preview["source_head"], expiry, None, None, iso()),
        )
        database.execute("UPDATE approval_previews_v3 SET state='approved' WHERE id=?", (preview_id,))
        database.execute("COMMIT")
    except Exception:
        if database.in_transaction:
            database.execute("ROLLBACK")
        raise
    print(json.dumps({"approval_id": approval_id, "generation": preview["generation"], "state": "approved",
                      "reference_mac": hashlib.sha256((approval_id + key).encode()).hexdigest()[:16]}))


def approval_row(database, approval_id):
    row = database.execute("SELECT * FROM approval_records_v3 WHERE id=?", (approval_id,)).fetchone()
    if not row:
        fail("approval_not_found")
    return row


def validate_binding(data, row):
    for field, reason in (
        ("generation", "approval_generation_mismatch"), ("consumer", "approval_consumer_mismatch"),
        ("operation", "approval_operation_not_permitted"), ("repository", "approval_repository_mismatch"),
        ("worktree", "approval_worktree_mismatch"), ("root", "approval_root_mismatch"),
        ("target", "approval_target_mismatch"), ("plugin", "approval_plugin_mismatch"),
        ("preview", "approval_preview_mismatch"), ("content_hash", "approval_content_hash_mismatch"),
        ("context", "approval_context_mismatch"), ("source_head", "approval_source_mismatch"),
    ):
        expected = str(row[field])
        actual = str(data.get(field, ""))
        if actual != expected:
            fail(reason)
    if data.get("source_head") != source_head():
        fail("approval_source_mismatch")


def consume(data):
    database, key = boot()
    approval_id = require(data, "approval_id")
    database.execute("BEGIN IMMEDIATE")
    try:
        row = approval_row(database, approval_id)
        if row["state"] == "consuming":
            fail("approval_concurrent_consumption")
        if row["state"] in TERMINAL_REASONS:
            fail(TERMINAL_REASONS[row["state"]])
        if row["state"] != "approved":
            fail("approval_not_approved")
        if datetime.fromisoformat(row["expires_at"]) <= now():
            database.execute("UPDATE approval_records_v3 SET state='expired' WHERE id=?", (approval_id,))
            database.execute("COMMIT")
            fail("approval_expired")
        validate_binding(data, row)
        database.execute("UPDATE approval_records_v3 SET state='consuming' WHERE id=?", (approval_id,))
        database.execute("COMMIT")
    except Exception:
        if database.in_transaction:
            database.execute("ROLLBACK")
        raise
    print(json.dumps({"approval_id": approval_id, "generation": row["generation"], "state": "consuming",
                      "reference_mac": hashlib.sha256((approval_id + key).encode()).hexdigest()[:16]}))


def lookup(data):
    database, _ = boot()
    row = approval_row(database, require(data, "approval_id"))
    fields = ("id", "generation", "state", "consumer", "operation", "repository", "worktree", "root",
              "target", "plugin", "preview", "content_hash", "context", "source_head", "expires_at")
    print(json.dumps({field: row[field] for field in fields}))


def lookup_preview(data):
    database, _ = boot()
    preview = database.execute("SELECT * FROM approval_previews_v3 WHERE id=?", (require(data, "preview_id"),)).fetchone()
    if not preview:
        fail("approval_not_found")
    fields = ("id", "generation", "state", "repository", "worktree", "root", "target", "plugin", "content_hash", "context_hash", "source_head", "created_at")
    print(json.dumps({field: preview[field] for field in fields}))


def transition_preview(data):
    database, _ = boot()
    preview_id = require(data, "preview_id")
    expected_generation = require(data, "expected_generation")
    state = require(data, "state")
    if state != "rejected":
        fail("approval_transition_not_permitted")
    database.execute("BEGIN IMMEDIATE")
    try:
        preview = database.execute("SELECT * FROM approval_previews_v3 WHERE id=?", (preview_id,)).fetchone()
        if not preview:
            fail("approval_not_found")
        if str(preview["generation"]) != expected_generation:
            fail("approval_generation_mismatch")
        if preview["state"] != "previewed":
            fail("approval_not_approved")
        database.execute("UPDATE approval_previews_v3 SET state=? WHERE id=?", (state, preview_id))
        database.execute("COMMIT")
    except Exception:
        if database.in_transaction:
            database.execute("ROLLBACK")
        raise
    print(json.dumps({"preview_id": preview_id, "generation": preview["generation"], "state": state}))


def finalize(data):
    database, _ = boot()
    approval_id = require(data, "approval_id")
    result_id = require(data, "result_id")
    evidence = require(data, "evidence")
    succeeded = data.get("status") == "succeeded"
    database.execute("BEGIN IMMEDIATE")
    try:
        row = approval_row(database, approval_id)
        validate_binding(data, row)
        if row["state"] != "consuming":
            fail(TERMINAL_REASONS.get(row["state"], "approval_not_approved"))
        state = "consumed" if succeeded else "invalidated"
        database.execute("UPDATE approval_records_v3 SET state=?, result_id=?, evidence=? WHERE id=?", (state, result_id, evidence[:512], approval_id))
        database.execute("COMMIT")
    except Exception:
        if database.in_transaction:
            database.execute("ROLLBACK")
        raise
    print(json.dumps({"approval_id": approval_id, "generation": row["generation"], "state": state, "result_id": result_id}))


def transition(data):
    database, _ = boot()
    approval_id = require(data, "approval_id")
    state = require(data, "state")
    if state not in {"rejected", "cancelled", "superseded", "invalidated"}:
        fail("approval_transition_not_permitted")
    database.execute("BEGIN IMMEDIATE")
    try:
        row = approval_row(database, approval_id)
        if row["state"] != "approved":
            fail(TERMINAL_REASONS.get(row["state"], "approval_not_approved"))
        database.execute("UPDATE approval_records_v3 SET state=? WHERE id=?", (state, approval_id))
        database.execute("COMMIT")
    except Exception:
        if database.in_transaction:
            database.execute("ROLLBACK")
        raise
    print(json.dumps({"approval_id": approval_id, "state": state}))


def preflight():
    _, key = boot()
    print(json.dumps({"schema": "spiritos-approval-authority-preflight/v3", "ready": True,
                      "authorityId": AUTHORITY_ID, "issuerId": ISSUER_ID, "storeType": "sqlite",
                      "signingKeyFingerprint": hashlib.sha256(key.encode()).hexdigest()[:16],
                      "registeredRoots": [ROOT], "consumers": sorted(CONSUMER_OPERATIONS),
                      "acknowledgementConsumers": sorted(ACKNOWLEDGEMENT_CONSUMERS),
                      "operations": sorted(CONSUMER_OPERATIONS.values()), "secretExposed": False}))


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    data = json.load(sys.stdin) if command in {"persist-preview", "issue", "lookup", "lookup-preview", "transition-preview", "consume", "finalize", "transition"} else {}
    commands = {"preflight": preflight, "persist-preview": lambda: persist_preview(data), "issue": lambda: issue(data),
                "lookup": lambda: lookup(data), "lookup-preview": lambda: lookup_preview(data), "transition-preview": lambda: transition_preview(data), "consume": lambda: consume(data), "finalize": lambda: finalize(data), "transition": lambda: transition(data)}
    if command not in commands:
        fail("approval_command_unknown")
    commands[command]()


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"ready": False, "reason": str(error), "secretExposed": False}))
        sys.exit(1)
