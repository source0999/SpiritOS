"""External process measurements for bounded JCode startup diagnosis."""
from __future__ import annotations

from pathlib import Path


def status_memory_bytes(pid: int, proc_root: Path = Path("/proc")) -> dict[str, int]:
    """Return byte values from proc status; never report kernel KiB as bytes."""
    status = (proc_root / str(pid) / "status").read_text(encoding="utf-8")
    values: dict[str, int] = {}
    for line in status.splitlines():
        key, _, raw = line.partition(":")
        if key not in {"VmRSS", "VmSize"}:
            continue
        amount, unit = raw.split()[:2]
        if unit != "kB":
            raise ValueError("jcode_memory_unit_unexpected")
        values[key] = int(amount) * 1024
    if set(values) != {"VmRSS", "VmSize"}:
        raise ValueError("jcode_memory_status_incomplete")
    return {"rss_bytes": values["VmRSS"], "virtual_bytes": values["VmSize"]}
