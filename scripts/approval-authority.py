#!/usr/bin/env python3
import hashlib,json,os,secrets,sqlite3,stat,sys
from datetime import datetime,timezone
from pathlib import Path
AUTHORITY_ID="spiritos-approval-authority"; ISSUER_ID="spiritos-approval-authority/campaign-1"
STATE_DIR=Path("/home/source/.local/state/spiritos/approvals"); DB_PATH=STATE_DIR/"approvals.sqlite3"
SECRET_DIR=Path("/home/source/.config/spiritos/secrets"); SECRET_PATH=SECRET_DIR/"approval-authority.env"
ROOT="/home/source/SpiritOS-campaign-1-20260712"; CONSUMERS={"design-writeback","coding-executor"}; OPERATIONS={"design_writeback","coding_execution"}
TERMINAL={"consumed","rejected","cancelled","expired","superseded","invalidated"}
def fail(code): raise RuntimeError(code)
def ensure_dir(p):
 p.mkdir(parents=True,exist_ok=True); os.chmod(p,0o700)
 if stat.S_IMODE(p.stat().st_mode)!=0o700: fail("approval_unsafe_directory_permissions")
def boot():
 ensure_dir(SECRET_DIR); ensure_dir(STATE_DIR)
 if SECRET_PATH.exists():
  if stat.S_IMODE(SECRET_PATH.stat().st_mode)!=0o600: fail("approval_unsafe_secret_permissions")
  line=SECRET_PATH.read_text().strip()
  if not line.startswith("SPIRITOS_APPROVAL_HMAC_KEY="): fail("approval_secret_malformed")
  key=line.split("=",1)[1]
 else:
  key=secrets.token_urlsafe(48); fd=os.open(SECRET_PATH,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,"w") as f:f.write("SPIRITOS_APPROVAL_HMAC_KEY="+key+"\n")
 db=sqlite3.connect(DB_PATH,isolation_level=None); db.execute("PRAGMA journal_mode=WAL")
 db.execute("""CREATE TABLE IF NOT EXISTS approvals (id TEXT PRIMARY KEY,generation INTEGER NOT NULL,state TEXT NOT NULL,consumer TEXT NOT NULL,operation TEXT NOT NULL,root TEXT NOT NULL,target TEXT NOT NULL,plugin TEXT NOT NULL,preview TEXT NOT NULL,content_hash TEXT NOT NULL,context TEXT NOT NULL,source_head TEXT NOT NULL,expires_at TEXT NOT NULL,result_id TEXT,evidence TEXT,created_at TEXT NOT NULL)""")
 os.chmod(DB_PATH,0o600)
 if stat.S_IMODE(DB_PATH.stat().st_mode)!=0o600: fail("approval_unsafe_database_permissions")
 return db,key
def now(): return datetime.now(timezone.utc).isoformat()
def req(d,k):
 v=d.get(k)
 if not isinstance(v,str) or not v: fail("approval_"+k+"_missing")
 return v
def issue(d):
 db,key=boot()
 for k in ("consumer","operation","root","target","plugin","preview","content_hash","context","source_head","expires_at"):req(d,k)
 if d["consumer"] not in CONSUMERS: fail("approval_consumer_mismatch")
 if d["operation"] not in OPERATIONS: fail("approval_operation_not_permitted")
 if os.path.realpath(d["root"])!=ROOT: fail("approval_root_mismatch")
 aid="apr_"+secrets.token_urlsafe(18); db.execute("INSERT INTO approvals VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(aid,1,"approved",d["consumer"],d["operation"],ROOT,d["target"],d["plugin"],d["preview"],d["content_hash"],d["context"],d["source_head"],d["expires_at"],None,None,now()))
 print(json.dumps({"approval_id":aid,"generation":1,"state":"approved","reference_mac":hashlib.sha256((aid+key).encode()).hexdigest()[:16]}))
def consume(d):
 db,key=boot(); aid=req(d,"approval_id"); db.execute("BEGIN IMMEDIATE"); row=db.execute("SELECT * FROM approvals WHERE id=?",(aid,)).fetchone()
 if not row: db.execute("ROLLBACK"); fail("approval_not_found")
 cols=["id","generation","state","consumer","operation","root","target","plugin","preview","content_hash","context","source_head","expires_at","result_id","evidence","created_at"]; r=dict(zip(cols,row))
 if r["state"]!="approved": db.execute("ROLLBACK"); fail("approval_already_consumed" if r["state"] in TERMINAL|{"consuming"} else "approval_not_approved")
 if r["expires_at"]<=now(): db.execute("UPDATE approvals SET state='expired' WHERE id=?",(aid,)); db.execute("COMMIT"); fail("approval_expired")
 for field,code in (("consumer","approval_consumer_mismatch"),("operation","approval_operation_not_permitted"),("root","approval_root_mismatch"),("target","approval_target_mismatch"),("plugin","approval_plugin_mismatch"),("preview","approval_preview_mismatch"),("content_hash","approval_content_hash_mismatch"),("context","approval_context_mismatch"),("source_head","approval_source_mismatch")):
  if d.get(field)!=r[field]: db.execute("ROLLBACK"); fail(code)
 db.execute("UPDATE approvals SET state='consuming' WHERE id=?",(aid,)); db.execute("COMMIT"); print(json.dumps({"approval_id":aid,"generation":r["generation"],"state":"consuming","reference_mac":hashlib.sha256((aid+key).encode()).hexdigest()[:16]}))
def preflight():
 db,key=boot(); print(json.dumps({"schema":"spiritos-approval-authority-preflight/v2","ready":True,"authorityId":AUTHORITY_ID,"issuerId":ISSUER_ID,"storeType":"sqlite","signingKeyFingerprint":hashlib.sha256(key.encode()).hexdigest()[:16],"registeredRoots":[ROOT],"consumers":sorted(CONSUMERS),"operations":sorted(OPERATIONS),"secretExposed":False}))
try:
 cmd=sys.argv[1]; data=json.load(sys.stdin) if cmd in {"issue","consume"} else {}
 {"preflight":preflight,"issue":lambda:issue(data),"consume":lambda:consume(data)}[cmd]()
except Exception as e: print(json.dumps({"ready":False,"reason":str(e),"secretExposed":False})); sys.exit(1)
