#!/usr/bin/env python3
"""Campaign 1 server-owned approval authority bootstrap/preflight."""
import hashlib, json, os, secrets, sqlite3, stat, sys
from pathlib import Path

AUTHORITY_ID="spiritos-approval-authority"
ISSUER_ID="spiritos-approval-authority/campaign-1"
STATE_DIR=Path("/home/source/.local/state/spiritos/approvals")
DB_PATH=STATE_DIR/"approvals.sqlite3"
SECRET_DIR=Path("/home/source/.config/spiritos/secrets")
SECRET_PATH=SECRET_DIR/"approval-authority.env"
ROOT="/home/source/SpiritOS-campaign-1-20260712"
CONSUMERS=["design-writeback","coding-executor"]
OPERATIONS=["design_writeback","coding_execution"]
STATES=["proposed","previewed","approved","consuming","consumed","rejected","cancelled","expired","superseded","invalidated","failed"]

def mode(path):
    return stat.S_IMODE(path.stat().st_mode)

def ensure_dir(path):
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, 0o700)
    if mode(path) != 0o700: raise RuntimeError("approval_unsafe_directory_permissions")

def ensure_secret():
    ensure_dir(SECRET_DIR)
    if SECRET_PATH.exists():
        if mode(SECRET_PATH) != 0o600: raise RuntimeError("approval_unsafe_secret_permissions")
        value=SECRET_PATH.read_text(encoding="utf8").strip()
        if not value.startswith("SPIRITOS_APPROVAL_HMAC_KEY="): raise RuntimeError("approval_secret_malformed")
        return value.split("=",1)[1]
    value=secrets.token_urlsafe(48)
    fd=os.open(SECRET_PATH, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
    with os.fdopen(fd,"w",encoding="utf8") as f: f.write("SPIRITOS_APPROVAL_HMAC_KEY="+value+"\n")
    os.chmod(SECRET_PATH,0o600)
    return value

def ensure_db():
    ensure_dir(STATE_DIR)
    db=sqlite3.connect(DB_PATH)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    db.execute("""CREATE TABLE IF NOT EXISTS approvals (
      approval_id TEXT PRIMARY KEY, generation INTEGER NOT NULL, state TEXT NOT NULL,
      issuer_id TEXT NOT NULL, consumer_id TEXT NOT NULL, operation TEXT NOT NULL,
      repository_id TEXT NOT NULL, worktree_path TEXT NOT NULL, root_path TEXT NOT NULL,
      target_id TEXT NOT NULL, plugin_id TEXT NOT NULL, preview_id TEXT NOT NULL,
      preview_hash TEXT NOT NULL, content_hash TEXT NOT NULL, context_id TEXT NOT NULL,
      source_head TEXT NOT NULL, expires_at TEXT NOT NULL, result_id TEXT, evidence_pointer TEXT,
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, consumed_at TEXT
    )""")
    db.commit(); db.close()
    os.chmod(DB_PATH,0o600)
    if mode(DB_PATH)!=0o600: raise RuntimeError("approval_unsafe_database_permissions")

def preflight():
    key=ensure_secret(); ensure_db()
    print(json.dumps({"schema":"spiritos-approval-authority-preflight/v1","ready":True,"authorityId":AUTHORITY_ID,
      "issuerId":ISSUER_ID,"storeType":"sqlite","storeFingerprint":hashlib.sha256(str(DB_PATH).encode()).hexdigest()[:16],
      "signingKeyFingerprint":hashlib.sha256(key.encode()).hexdigest()[:16],"registeredRoots":[ROOT],
      "consumers":CONSUMERS,"operations":OPERATIONS,"states":STATES,"secretExposed":False},sort_keys=True))

if __name__=="__main__":
    try:
        if len(sys.argv)!=2 or sys.argv[1]!="preflight": raise RuntimeError("approval_command_not_permitted")
        preflight()
    except Exception as exc:
        print(json.dumps({"schema":"spiritos-approval-authority-preflight/v1","ready":False,"reason":str(exc),"secretExposed":False}))
        sys.exit(1)
