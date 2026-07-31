from __future__ import annotations

from pathlib import Path

from source_proxy.jcode.containment import build_preassembled_root_args
from source_proxy.jcode.startup_diagnosis import status_memory_bytes


def test_preassembled_root_uses_fresh_writable_ephemeral_jcode_home(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    args = build_preassembled_root_args(["/usr/bin/jcode", "--version"], root)
    assert "--tmpfs" in args
    assert args[args.index("--tmpfs") + 1] == "/tmp"
    assert "JCODE_HOME" in args
    assert "/jcode-home" not in args


def test_status_memory_converts_proc_kib_to_bytes(tmp_path: Path) -> None:
    status = tmp_path / "123" / "status"
    status.parent.mkdir()
    status.write_text("Name:\tjcode\nVmSize:\t503808 kB\nVmRSS:\t270336 kB\n", encoding="utf-8")
    assert status_memory_bytes(123, tmp_path) == {
        "rss_bytes": 276_824_064,
        "virtual_bytes": 515_899_392,
    }
