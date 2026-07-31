from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from source_proxy.jcode.containment import PreassembledRootConfig, assemble_preassembled_root, build_preassembled_root_args


def _root(tmp_path: Path, executable: Path, name: str) -> Path:
    return assemble_preassembled_root(PreassembledRootConfig(tmp_path / name, executable, executable_name=executable.name, runtime_files=(Path('/lib/x86_64-linux-gnu/libc.so.6'), Path('/lib64/ld-linux-x86-64.so.2'))))


def test_dynamic_executable_runs_in_read_only_preassembled_root(tmp_path: Path) -> None:
    root = _root(tmp_path, Path('/usr/bin/true'), 'dynamic')
    result = subprocess.run(build_preassembled_root_args(['/usr/bin/true'], root), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_static_executable_runs_and_writable_paths_are_not_executable(tmp_path: Path) -> None:
    root = _root(tmp_path, Path('/usr/bin/busybox'), 'static')
    result = subprocess.run(build_preassembled_root_args(['/usr/bin/busybox', 'true'], root), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    denied = subprocess.run(build_preassembled_root_args(['/usr/bin/busybox', 'sh', '-c', 'touch /workspace/nope'], root), capture_output=True, text=True)
    assert denied.returncode != 0


def test_root_exposes_no_host_home_or_network(tmp_path: Path) -> None:
    root = _root(tmp_path, Path('/usr/bin/busybox'), 'isolated')
    command = ['/usr/bin/busybox', 'sh', '-c', 'test ! -e /home/source && ! /usr/bin/busybox wget -q -T 1 http://1.1.1.1']
    result = subprocess.run(build_preassembled_root_args(command, root), capture_output=True, text=True)
    assert result.returncode == 0


def test_preassembled_root_copies_explicit_proxy_owned_launcher(tmp_path: Path) -> None:
    root = assemble_preassembled_root(
        PreassembledRootConfig(
            tmp_path / "root",
            Path("/usr/bin/true"),
            runtime_files=(Path("/lib/x86_64-linux-gnu/libc.so.6"), Path("/lib64/ld-linux-x86-64.so.2")),
            additional_executables=((Path("/usr/bin/false"), "proxy-launcher"),),
        )
    )
    launcher = root / "usr/bin/proxy-launcher"
    assert launcher.is_file()
    assert launcher.stat().st_mode & 0o111
