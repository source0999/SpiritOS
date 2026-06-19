from __future__ import annotations

import json
import shutil
import ssl
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

StatusValue = str

GO: StatusValue = "GO"
PARTIAL_GO: StatusValue = "PARTIAL_GO"
NO_GO: StatusValue = "NO_GO"
BLOCKED: StatusValue = "BLOCKED"
UNKNOWN: StatusValue = "UNKNOWN"

NEXT_ADMIN_URL = "https://127.0.0.1:3000/spiritflix/admin"
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"
OLLAMA_PS_URL = "http://127.0.0.1:11434/api/ps"
WATCHER_LOG_ROOT = Path("/mnt/spirit-8tb/spiritos-health")
WATCHER_TIMER_UNIT = "spiritos-health-snapshot.timer"
BOOT_POSTMORTEM_UNIT = "spiritos-boot-postmortem.service"
VALID_LIVENESS_ENDPOINTS = [
    "/health",
    "/v1/health",
    "/v1/runtime/status",
    "/docs",
    "/openapi.json",
]

_PACKAGE_CONFIG_RUNTIME_FILES = {
    "package.json",
    "package-lock.json",
    "next.config.ts",
    "next.config.js",
    "README.md",
    "scripts/runtime-port-guard.sh",
    "scripts/source-context-compress.mjs",
    "scripts/spiritos-lan-watchdog.sh",
}
_PACKAGE_CONFIG_RUNTIME_PREFIXES = (
    "config/",
    "scripts/spiritos-health/",
)
_CRASH_PATTERNS = (
    "oom",
    "out of memory",
    "killed process",
    "segfault",
    "panic",
)


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    unavailable: bool = False


def build_runtime_health_status(repo_root: str | Path = ".") -> dict[str, Any]:
    checks = {
        "api": _api_check(),
        "next": check_next(),
        "ollama": check_ollama(),
        "watchers": check_watchers(),
        "git_authority": check_git_authority(repo_root),
        "failed_units": check_failed_units(),
        "recent_crash_signals": check_recent_crash_signals(),
    }
    notes = _notes_for_checks(checks)
    status = _overall_status(checks)
    return {
        "status": status,
        "service": "source-proxy",
        "timestamp": _utc_now(),
        "checks": checks,
        "valid_liveness_endpoints": VALID_LIVENESS_ENDPOINTS,
        "invalid_legacy_health_endpoints": [],
        "notes": notes,
    }


def check_next(url: str = NEXT_ADMIN_URL, timeout_seconds: float = 2.0) -> dict[str, Any]:
    result = _http_json_or_text(url, timeout_seconds=timeout_seconds, verify_tls=False)
    status = GO if result["http_status"] == 200 else NO_GO
    if result["error"]:
        status = NO_GO
    return {
        "status": status,
        "url": url,
        "http_status": result["http_status"],
        "latency_ms": result["latency_ms"],
        "details": result["details"],
    }


def check_ollama(
    tags_url: str = OLLAMA_TAGS_URL,
    ps_url: str = OLLAMA_PS_URL,
    timeout_seconds: float = 2.0,
) -> dict[str, Any]:
    tags = _http_json_or_text(tags_url, timeout_seconds=timeout_seconds)
    loaded = _http_json_or_text(ps_url, timeout_seconds=timeout_seconds)
    model_names = _ollama_model_names(tags.get("json"))
    loaded_models = _ollama_model_names(loaded.get("json"))
    status = GO if tags["http_status"] == 200 else NO_GO
    if tags["error"]:
        status = NO_GO
    ps_status = GO if loaded["http_status"] == 200 else UNKNOWN
    return {
        "status": status,
        "url": tags_url,
        "http_status": tags["http_status"],
        "latency_ms": tags["latency_ms"],
        "model_count": len(model_names),
        "models": model_names[:20],
        "loaded_models": loaded_models[:20],
        "ps": {
            "status": ps_status,
            "url": ps_url,
            "http_status": loaded["http_status"],
            "latency_ms": loaded["latency_ms"],
        },
        "details": tags["details"],
    }


def check_watchers(
    log_root: str | Path = WATCHER_LOG_ROOT,
    timer_unit: str = WATCHER_TIMER_UNIT,
    boot_unit: str = BOOT_POSTMORTEM_UNIT,
) -> dict[str, Any]:
    timer_active = _systemctl_value("is-active", timer_unit)
    timer_enabled = _systemctl_value("is-enabled", timer_unit)
    boot_status = _systemctl_value("is-enabled", boot_unit)
    latest_logs = latest_watcher_logs(log_root)

    if timer_active["status"] == GO and latest_logs:
        status = GO
        details = "watcher timer active and recent log metadata found"
    elif latest_logs:
        status = PARTIAL_GO
        details = "watcher logs found but timer state is not fully known"
    elif timer_active["status"] == UNKNOWN:
        status = UNKNOWN
        details = "watcher timer could not be checked"
    else:
        status = NO_GO
        details = "watcher timer inactive or no watcher logs found"

    return {
        "status": status,
        "timer": timer_active,
        "timer_enabled": timer_enabled,
        "boot_postmortem": boot_status,
        "latest_logs": latest_logs,
        "details": details,
    }


def latest_watcher_logs(log_root: str | Path, limit: int = 8) -> list[dict[str, Any]]:
    root = Path(log_root)
    if not root.exists() or not root.is_dir():
        return []
    files: list[Path] = []
    for path in root.rglob("*"):
        try:
            if path.is_file() and path.suffix == ".log":
                files.append(path)
        except OSError:
            continue
        if len(files) > 2000:
            break
    files.sort(key=lambda item: _safe_mtime(item), reverse=True)
    return [
        {
            "path": str(path),
            "modified_at": _timestamp_from_epoch(_safe_mtime(path)),
            "size_bytes": _safe_size(path),
        }
        for path in files[:limit]
    ]


def check_failed_units() -> dict[str, Any]:
    if not shutil.which("systemctl"):
        return {
            "status": UNKNOWN,
            "units": [],
            "details": "systemctl unavailable",
        }
    result = _run_command(["systemctl", "--failed", "--no-legend", "--no-pager"], timeout_seconds=2.0)
    if result.timed_out:
        return {"status": UNKNOWN, "units": [], "details": "systemctl failed-unit check timed out"}
    if result.unavailable:
        return {"status": UNKNOWN, "units": [], "details": "systemctl unavailable"}
    units = _parse_failed_units(result.stdout)
    status = PARTIAL_GO if units else GO
    return {
        "status": status,
        "units": units,
        "details": "failed units summarized by unit name only" if units else "no failed units reported",
    }


def check_git_authority(repo_root: str | Path = ".") -> dict[str, Any]:
    if not shutil.which("git"):
        return {
            "status": UNKNOWN,
            "staged_files": 0,
            "dirty_source_proxy": False,
            "details": "git unavailable",
        }
    result = _run_command(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=Path(repo_root),
        timeout_seconds=3.0,
    )
    if result.timed_out:
        return {
            "status": UNKNOWN,
            "staged_files": 0,
            "dirty_source_proxy": False,
            "details": "git status timed out",
        }
    if result.returncode != 0:
        return {
            "status": BLOCKED,
            "staged_files": 0,
            "dirty_source_proxy": False,
            "details": "git status failed",
        }
    parsed = _parse_git_porcelain_z(result.stdout)
    dirty_source_proxy_files = [
        item["path"]
        for item in parsed
        if item["path"].startswith("source_proxy/")
    ]
    package_config_runtime_files = [
        item["path"]
        for item in parsed
        if _is_package_config_runtime_path(item["path"])
    ]
    staged_files = [item["path"] for item in parsed if item["staged"]]
    if dirty_source_proxy_files:
        status = NO_GO
        details = "dirty Source Proxy files block implementation authority"
    elif parsed:
        status = PARTIAL_GO
        details = "unrelated dirty files exist; liveness is not failed by dirty tree alone"
    else:
        status = GO
        details = "git tree clean"
    return {
        "status": status,
        "dirty_source_proxy": bool(dirty_source_proxy_files),
        "dirty_source_proxy_count": len(dirty_source_proxy_files),
        "staged_files": len(staged_files),
        "dirty_files": len(parsed),
        "package_config_runtime_dirty_count": len(package_config_runtime_files),
        "details": details,
    }


def check_recent_crash_signals() -> dict[str, Any]:
    if not shutil.which("journalctl"):
        return {
            "status": UNKNOWN,
            "signal_count": 0,
            "patterns": list(_CRASH_PATTERNS),
            "details": "journalctl unavailable",
        }
    result = _run_command(
        [
            "journalctl",
            "-b",
            "-0",
            "--since",
            "4 hours ago",
            "--no-pager",
            "-g",
            "oom|out of memory|killed process|segfault|panic",
        ],
        timeout_seconds=3.0,
    )
    if result.timed_out:
        return {
            "status": UNKNOWN,
            "signal_count": 0,
            "patterns": list(_CRASH_PATTERNS),
            "details": "journal crash-signal check timed out",
        }
    if result.returncode not in {0, 1}:
        return {
            "status": UNKNOWN,
            "signal_count": 0,
            "patterns": list(_CRASH_PATTERNS),
            "details": "journal crash-signal check unavailable",
        }
    signal_count = len([line for line in result.stdout.splitlines() if line.strip()])
    return {
        "status": NO_GO if signal_count else GO,
        "signal_count": signal_count,
        "patterns": list(_CRASH_PATTERNS),
        "details": "fresh crash/OOM signal names counted; raw journal lines are not exposed",
    }


def _api_check() -> dict[str, Any]:
    return {
        "status": GO,
        "details": "runtime status endpoint responded",
    }


def _http_json_or_text(
    url: str,
    *,
    timeout_seconds: float,
    verify_tls: bool = True,
) -> dict[str, Any]:
    start = time.perf_counter()
    context = None if verify_tls else ssl._create_unverified_context()
    try:
        with urllib.request.urlopen(url, timeout=timeout_seconds, context=context) as response:
            body = response.read(512_000)
            latency_ms = int((time.perf_counter() - start) * 1000)
            parsed = _try_json(body)
            return {
                "http_status": getattr(response, "status", None),
                "latency_ms": latency_ms,
                "json": parsed,
                "error": None,
                "details": "request completed",
            }
    except TimeoutError:
        return _http_error("timeout", start)
    except urllib.error.URLError as error:
        return _http_error(_safe_error_reason(error), start)
    except OSError as error:
        return _http_error(error.__class__.__name__, start)


def _http_error(reason: str, start: float) -> dict[str, Any]:
    return {
        "http_status": None,
        "latency_ms": int((time.perf_counter() - start) * 1000),
        "json": None,
        "error": reason,
        "details": f"request failed: {reason}",
    }


def _try_json(body: bytes) -> Any:
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _ollama_model_names(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return []
    models = payload.get("models")
    if not isinstance(models, list):
        return []
    names: list[str] = []
    for item in models:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("model")
        if isinstance(name, str) and _safe_public_value(name):
            names.append(name)
    return names


def _systemctl_value(action: str, unit: str) -> dict[str, Any]:
    if not shutil.which("systemctl"):
        return {
            "status": UNKNOWN,
            "unit": unit,
            "state": None,
            "details": "systemctl unavailable",
        }
    result = _run_command(["systemctl", action, unit], timeout_seconds=2.0)
    state = result.stdout.strip().splitlines()[0] if result.stdout.strip() else None
    if result.timed_out:
        return {"status": UNKNOWN, "unit": unit, "state": None, "details": "systemctl timed out"}
    if action == "is-active":
        status = GO if state == "active" else NO_GO
    elif action == "is-enabled":
        status = GO if state == "enabled" else PARTIAL_GO
    else:
        status = UNKNOWN
    if result.returncode not in {0, 1, 3} and not state:
        status = UNKNOWN
    return {
        "status": status,
        "unit": unit,
        "state": state,
        "details": f"systemctl {action} summarized",
    }


def _run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout_seconds: float,
) -> CommandResult:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return CommandResult(
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    except FileNotFoundError:
        return CommandResult(returncode=127, stdout="", stderr="", unavailable=True)
    except subprocess.TimeoutExpired as error:
        return CommandResult(
            returncode=124,
            stdout=error.stdout if isinstance(error.stdout, str) else "",
            stderr="timeout",
            timed_out=True,
        )


def _parse_failed_units(output: str) -> list[str]:
    units: list[str] = []
    for line in output.splitlines():
        parts = line.split()
        if not parts:
            continue
        unit = parts[0].lstrip("●")
        if unit.endswith(".service") or unit.endswith(".mount") or unit.endswith(".timer"):
            units.append(unit)
    return units[:20]


def _parse_git_porcelain_z(output: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    records = output.split("\x00")
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if len(record) < 4:
            continue
        status = record[:2]
        path = record[3:].replace("\\", "/")
        if status[0] in {"R", "C"} or status[1] in {"R", "C"}:
            index += 1
        if not path:
            continue
        entries.append(
            {
                "path": path,
                "staged": status != "??" and status[0] != " ",
                "untracked": status == "??",
            }
        )
    return entries


def _is_package_config_runtime_path(path: str) -> bool:
    return path in _PACKAGE_CONFIG_RUNTIME_FILES or path.startswith(_PACKAGE_CONFIG_RUNTIME_PREFIXES)


def _notes_for_checks(checks: dict[str, dict[str, Any]]) -> list[str]:
    notes: list[str] = []
    failed_units = checks.get("failed_units", {}).get("units", [])
    if "mnt-spirit\\x2dprojects.mount" in failed_units:
        notes.append("Known unrelated failed mount is present: mnt-spirit\\x2dprojects.mount.")
    git_authority = checks.get("git_authority", {})
    if git_authority.get("status") == PARTIAL_GO:
        notes.append("Dirty files outside source_proxy are present; liveness remains separate from implementation authority.")
    if git_authority.get("package_config_runtime_dirty_count", 0):
        notes.append("Package/config/runtime helper files are dirty, so authority is partial.")
    return notes


def _overall_status(checks: dict[str, dict[str, Any]]) -> StatusValue:
    if checks["api"]["status"] != GO:
        return NO_GO
    if checks["git_authority"]["status"] == NO_GO:
        return NO_GO
    if checks["recent_crash_signals"]["status"] == NO_GO:
        return NO_GO
    required = (checks["next"]["status"], checks["ollama"]["status"])
    if any(status == NO_GO for status in required):
        return NO_GO
    partial_markers = {
        PARTIAL_GO,
        UNKNOWN,
        BLOCKED,
    }
    if any(check.get("status") in partial_markers for check in checks.values()):
        return PARTIAL_GO
    return GO


def _safe_public_value(value: str) -> bool:
    lowered = value.lower()
    return not any(marker in lowered for marker in ("token", "secret", "password", "apikey", "api_key"))


def _safe_error_reason(error: urllib.error.URLError) -> str:
    reason = getattr(error, "reason", error)
    text = reason.__class__.__name__ if not isinstance(reason, str) else reason
    if not _safe_public_value(text):
        return "request_error"
    return text[:80]


def _safe_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _safe_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _timestamp_from_epoch(value: float) -> str | None:
    if value <= 0:
        return None
    return datetime.fromtimestamp(value, UTC).isoformat().replace("+00:00", "Z")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
