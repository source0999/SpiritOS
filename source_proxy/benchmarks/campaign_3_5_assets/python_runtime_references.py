"""Executable private references for Python completed-code fixtures."""
from __future__ import annotations

import importlib.util
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from source_proxy.benchmarks.campaign_3_5_assets.core_references import apply_core_reference


PYTHON_RUNTIME_TASKS = frozenset({"S01", "S02", "S05", "S09", "S11", "S12", "S15", "S20", "S24", "B05", "B10", "B13", "B15", "C04", "R06", "R09"})


def _replace(path: Path, before: str, after: str) -> None:
    text = path.read_text(encoding="utf-8")
    if before not in text:
        raise ValueError("campaign_3_5_python_reference_baseline_mismatch")
    path.write_text(text.replace(before, after), encoding="utf-8")


def _module(path: Path):
    spec = importlib.util.spec_from_file_location(f"fixture_{path.stem}_{id(path)}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apply_python_runtime_reference(task_id: str, root: Path) -> None:
    if task_id == "S01":
        _replace(root / "src/api/items.py", "return list(ITEMS)", "\n    if limit is None: limit = 20\n    if not 1 <= limit <= 100: raise ValueError('limit out of range')\n    return list(ITEMS[:limit])")
    elif task_id == "S02":
        _replace(root / "src/identity/email.py", "return value.strip().lower()", "value = value.strip()\n    if value.count('@') != 1: raise ValueError('invalid email')\n    local, domain = value.split('@')\n    return local + '@' + domain.lower()")
    elif task_id == "S05":
        _replace(root / "src/net/retry.py", "import random\n    return base * (2 ** attempt) + random.random() * jitter", "import random\n    rng = rng or random\n    ceiling = min(cap, base * (2 ** attempt))\n    return max(0.0, min(cap, ceiling * (1 + rng.uniform(-jitter, jitter))))")
    elif task_id == "S09":
        _replace(root / "src/api/items.py", "return {\"status\": \"ok\"}", "return {\"status\": \"ok\", \"version\": PACKAGE_VERSION}")
    elif task_id == "S11":
        _replace(root / "src/cli/main.py", "def emit_result(result, progress, out, err):\n    out.write(f\"{result}\\n\")\n    out.write(f\"{progress}\\n\")  # Baseline: progress cannot be silenced.", "def emit_result(result, progress, out, err, quiet=False):\n    out.write(f\"{result}\\n\")\n    if not quiet: out.write(f\"{progress}\\n\")")
    elif task_id == "S15":
        _replace(root / "src/text/slug.py", "import re\n\ndef slug(value):\n    return re.sub(r\"[^a-z0-9]+\", \"-\", value.lower())", "import re, unicodedata\n\ndef slug(value):\n    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower()\n    value = re.sub(r'[^a-z0-9]+', '-', value).strip('-')\n    return value or 'item'")
    elif task_id == "S20":
        _replace(root / "src/config/parse.py", "return bool(value)", "value = value.strip().lower()\n    if value in {'1','true','yes','on'}: return True\n    if value in {'0','false','no','off'}: return False\n    if not value: return False\n    raise ValueError('invalid boolean')")
    elif task_id == "S24":
        _replace(root / "src/cli/main.py", "import os\n", "import os, tempfile\n")
        _replace(root / "src/cli/main.py", "with open(path, \"w\", encoding=\"utf-8\") as handle:\n        handle.write(value)  # Baseline: non-atomic replacement.", "directory = os.path.dirname(path) or '.'\n    fd, temporary = tempfile.mkstemp(dir=directory)\n    try:\n        with os.fdopen(fd, 'w', encoding='utf-8') as handle:\n            handle.write(value); handle.flush(); os.fsync(handle.fileno())\n        os.replace(temporary, path)\n    finally:\n        if os.path.exists(temporary): os.unlink(temporary)")
    elif task_id == "B05":
        _replace(root / "src/calendar/recurrence.py", "from datetime import timedelta\n\ndef weekly(start, count):\n    # Baseline defect: elapsed 7-day arithmetic loses local wall-time across DST.\n    return [start + timedelta(days=7 * index) for index in range(count)]", "from datetime import datetime, timedelta\n\ndef weekly(start, count):\n    return [datetime.combine(start.date() + timedelta(days=7 * index), start.timetz()).replace(tzinfo=start.tzinfo) for index in range(count)]")
    elif task_id == "B10":
        _replace(root / "src/cli/confirm.py", "value = stream.readline()\n        if value.strip().lower()", "value = stream.readline()\n        if value == '': return False\n        if value.strip().lower()")
    elif task_id in {"S12", "B13", "B15", "C04", "R06", "R09"}:
        apply_core_reference(task_id, root)
    else:
        raise ValueError("campaign_3_5_python_runtime_task_unknown")


def probe_python_runtime(task_id: str, root: Path) -> tuple[bool, str]:
    if task_id in {"S01", "S09"}:
        module = _module(root / "src/api/items.py")
        if task_id == "S01":
            try: module.list_items(0); return False, "range_not_enforced"
            except ValueError: return len(module.list_items()) == 20 and len(module.list_items(100)) == 100, "http_contract_equivalent"
        return module.health().get("version") == module.PACKAGE_VERSION, "version_metadata"
    if task_id == "S02":
        module = _module(root / "src/identity/email.py"); return module.normalize_email(" Local@EXAMPLE.com ") == "Local@example.com", "email_normalization"
    if task_id == "S05":
        module = _module(root / "src/net/retry.py")
        class R: 
            def uniform(self, a, b): return a
        return module.retry_delay(9, rng=R()) <= 8.0, "bounded_deterministic_retry"
    if task_id == "S11":
        from io import StringIO
        module = _module(root / "src/cli/main.py"); out=StringIO(); module.emit_result("ok","progress",out,StringIO(),quiet=True); return out.getvalue()=="ok\n", "quiet_output"
    if task_id == "S15":
        module = _module(root / "src/text/slug.py"); return module.slug("Café !!!") == "cafe" and module.slug("💥") == "item", "unicode_slug"
    if task_id == "S20":
        module = _module(root / "src/config/parse.py"); return module.parse_bool("YES") and not module.parse_bool("off"), "boolean_table"
    if task_id == "S24":
        import tempfile
        module = _module(root / "src/cli/main.py")
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"settings"; module.save_settings(str(path), "next"); return path.read_text()=="next", "atomic_save"
    if task_id == "B05":
        module = _module(root / "src/calendar/recurrence.py"); values=module.weekly(datetime(2026,3,1,9,tzinfo=ZoneInfo("America/New_York")),3); return all(value.hour==9 for value in values), "dst_wall_time"
    if task_id == "B10":
        from io import StringIO
        module = _module(root / "src/cli/confirm.py"); return module.confirm(StringIO("")) is False, "eof_termination"
    if task_id == "S12":
        module = _module(root / "src/security/tokens.py"); return module.is_valid_token("x", "x") and not module.is_valid_token("x", "y"), "constant_time_token_contract"
    if task_id == "B13":
        module = _module(root / "src/authz/cache.py"); cache=module.PermissionCache(); return cache.allowed("a","u","read",lambda *_:True) and not cache.allowed("b","u","read",lambda *_:False), "tenant_cache_isolation"
    if task_id == "B15":
        module = _module(root / "generator/docs.py"); return module.files(["b","a"]) == ["a","b"], "stable_file_traversal"
    if task_id == "C04":
        module = _module(root / "src/sort.py"); return module.sort([3,1,2,1]) == [1,1,2,3], "sorting_retry_repair"
    if task_id == "R06":
        module = _module(root / "src/jobs/state.py"); result=module.cancel("queued"); return result == ("cancelling", "cancelled", "audit-emitted"), "retained_adr_transition"
    if task_id == "R09":
        module = _module(root / "src/router/authenticated.py"); return module.select_model([{"healthy":False},{"healthy":True,"name":"good"}])["name"] == "good", "authenticated_router_health"
    return False, "unknown"
