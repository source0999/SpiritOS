"""Harness-private reference transformations and semantic probes for Core-30.

These transformations are used only in a separate validation materialization to
prove a fixture/oracle pair is internally consistent.  The production coder
never receives this module, its patches, or probe outcomes.
"""
from __future__ import annotations

from pathlib import Path


CORE_COMPLETED_TASKS = frozenset({"S08", "S12", "S21", "M12", "M13", "M15", "B09", "B13", "B15", "R06", "R09", "R10", "C01", "C04", "C05", "A01"})


def _replace(path: Path, before: str, after: str) -> None:
    text = path.read_text(encoding="utf-8")
    if before not in text:
        raise ValueError("campaign_3_5_reference_baseline_mismatch")
    path.write_text(text.replace(before, after), encoding="utf-8")


def apply_core_reference(task_id: str, root: Path) -> None:
    if task_id == "S08":
        _replace(root / "src/security/redact.ts", "export function redactSecrets(value: unknown) { return value; } // baseline does not traverse", "export function redactSecrets(value: unknown): unknown { if (Array.isArray(value)) return value.map(redactSecrets); if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value as Record<string, unknown>).map(([k,v]) => (/^(token|password|secret|apikey)$/i.test(k) ? [k, '[REDACTED]'] : [k, redactSecrets(v)]))); return value; }")
    elif task_id == "S12":
        _replace(root / "src/security/tokens.py", "return provided == expected", "import hmac\n    return hmac.compare_digest(provided, expected)")
    elif task_id == "S21":
        _replace(root / "src/main.rs", "values.sort(); values", "values.sort_by(|a,b| semver::Version::parse(a).unwrap().cmp(&semver::Version::parse(b).unwrap())); values")
        _replace(root / "Cargo.toml", "edition=\"2021\"", "edition=\"2021\"\n[dependencies]\nsemver=\"1\"")
    elif task_id == "M12":
        (root / "packages/worker/src/thumbnail.ts").write_text("export async function processThumbnail(job:any) { return {sizes:['sm','md','lg'], status:'complete', id:job.id}; }\n", encoding="utf-8")
        (root / "packages/api/src/thumbnail.ts").write_text("export const enqueueThumbnail=(queue:any,id:string)=>queue.enqueue({id}); export const thumbnailStatus=(store:any,id:string)=>store.status(id);\n", encoding="utf-8")
    elif task_id == "M13":
        (root / "src/services/policy.py").write_text("import yaml\ndef require_approval(policy, operation): return bool(policy.get('destructive') and operation)\n", encoding="utf-8")
        _replace(root / "src/services/operations.py", "return operation()  # Baseline: no server-side policy evaluation.", "from src.services.policy import require_approval\n    if require_approval({'destructive': True}, operation): return 'approval-required'\n    return operation()")
    elif task_id == "M15":
        _replace(root / "packages/core/src/result.ts", "export type LegacyResult={value:string}; ", "")
        _replace(root / "packages/python/producer.py", "return {'value':'x'}", "return {'ok': True, 'value':'x'}")
        _replace(root / "packages/go/consumer.go", "type LegacyResult struct{ Value string }", "type ResultV2 struct{ OK bool; Value string }")
        _replace(root / "examples/legacy.md", "LegacyResult", "ResultV2")
    elif task_id == "B09":
        _replace(root / "migrations/002_add_status.sql", "ALTER TABLE users ADD COLUMN status TEXT NOT NULL; -- baseline fails populated rows", "ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT 'active';\n-- backfill existing rows before enforcing new writes")
    elif task_id == "B13":
        _replace(root / "src/authz/cache.py", "key = (user_id, action)  # Baseline defect: tenant omitted.", "key = (tenant_id, user_id, action)")
    elif task_id == "B15":
        _replace(root / "generator/docs.py", "return list(paths) # filesystem order baseline", "return sorted(paths) # sort only independent file traversal")
    elif task_id == "R06":
        _replace(root / "src/jobs/state.py", "return 'cancelled' # baseline ignores approved transition", "return ('cancelling', 'cancelled', 'audit-emitted')")
    elif task_id == "R09":
        _replace(root / "src/router/authenticated.py", "def select_model(candidates): return candidates[0] # baseline ignores health", "def select_model(candidates): return next(candidate for candidate in candidates if candidate.get('healthy'))")
    elif task_id == "R10":
        _replace(root / "services/logging/access.py", "return f'access_token={token}' # baseline secret leak", "from shared.redaction import redact\n    return f'access_token={redact(token)}'")
    elif task_id == "C01":
        (root / "src/validation.py").write_text("def validate(first, second): return first is not None and second is not None\n", encoding="utf-8")
        _replace(root / "src/worker.py", "def apply_second_file(): return 'pending'", "def apply_second_file(): return 'written-after-restart'")
    elif task_id == "C04":
        _replace(root / "src/sort.py", "return list(set(values)) # baseline unstable", "return sorted(values)")
    elif task_id == "C05":
        _replace(root / "src/worker.py", "def apply_first_file(): return 'written'", "def apply_first_file(): return {'status': 'written', 'lease_owner': 'takeover-safe'}")
    elif task_id == "A01":
        _replace(root / "src/reporting/formatting.py", "  return  { 'count':len(values),'values':values }", "    return {'count': len(values), 'values': values}")
    else:
        raise ValueError("campaign_3_5_core_reference_unknown_task")


def probe_core_reference(task_id: str, root: Path) -> tuple[bool, str]:
    checks = {
        "S08": lambda: "Object.fromEntries" in (root / "src/security/redact.ts").read_text(),
        "S12": lambda: "compare_digest" in (root / "src/security/tokens.py").read_text(),
        "S21": lambda: "semver::Version" in (root / "src/main.rs").read_text(),
        "M12": lambda: (root / "packages/api/src/thumbnail.ts").is_file() and "sizes" in (root / "packages/worker/src/thumbnail.ts").read_text(),
        "M13": lambda: (root / "src/services/policy.py").is_file() and "approval-required" in (root / "src/services/operations.py").read_text(),
        "M15": lambda: "LegacyResult" not in (root / "packages/core/src/result.ts").read_text() and "ResultV2" in (root / "packages/go/consumer.go").read_text(),
        "B09": lambda: "DEFAULT 'active'" in (root / "migrations/002_add_status.sql").read_text(),
        "B13": lambda: "tenant_id, user_id, action" in (root / "src/authz/cache.py").read_text(),
        "B15": lambda: "sorted(paths)" in (root / "generator/docs.py").read_text(),
        "R06": lambda: "audit-emitted" in (root / "src/jobs/state.py").read_text(),
        "R09": lambda: "healthy" in (root / "src/router/authenticated.py").read_text(),
        "R10": lambda: "redact(token)" in (root / "services/logging/access.py").read_text(),
        "C01": lambda: (root / "src/validation.py").is_file() and "after-restart" in (root / "src/worker.py").read_text(),
        "C04": lambda: "sorted(values)" in (root / "src/sort.py").read_text(),
        "C05": lambda: "lease_owner" in (root / "src/worker.py").read_text(),
        "A01": lambda: "    return {'count': len(values)" in (root / "src/reporting/formatting.py").read_text(),
    }
    passed = checks[task_id]()
    return passed, "core_semantic_reference" if passed else "core_semantic_reference_failed"
