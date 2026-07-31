"""OS-enforced containment for future JCode qualification probes.

This is deliberately a sandbox policy builder, not a JCode dispatcher. It
requires an explicit existing-file input set and uses Bubblewrap's unshared
network with an otherwise empty workspace for all Gate 2-J.2 probes.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from source_proxy.safety.paths import (
    has_percent_encoded_path_syntax,
    is_secret_shaped_path,
    path_escapes_workspace,
)
from source_proxy.sandbox.bubblewrap import BubblewrapConfig, build_bubblewrap_args
from source_proxy.jcode.cgroup_scope import CgroupScopeConfig, run_in_cgroup_scope


class JCodeContainmentError(ValueError):
    """The requested filesystem boundary cannot be enforced safely."""


@dataclass(frozen=True)
class PreassembledRootConfig:
    """Immutable, per-run root used when AppArmor rejects introduced binds."""

    root: Path
    executable: Path
    executable_name: str = "jcode"
    runtime_files: tuple[Path, ...] = ()
    additional_executables: tuple[tuple[Path, str], ...] = ()
    additional_files: tuple[tuple[Path, str], ...] = ()


@dataclass(frozen=True)
class ContainmentFixtureConfig:
    """No-model fixture boundary for Gate 2-J.9B proof only."""

    run_id: str
    fixture_input: Path
    fixture_output: Path
    isolated_home: Path
    isolated_tmp: Path
    memory_max_bytes: int = 536_870_912
    tasks_max: int = 32
    cpu_quota_percent: int = 400
    file_size_max_bytes: int = 10_485_760
    open_files_max: int = 1024
    bwrap_path: str = "bwrap"
    systemd_run_path: str = "systemd-run"


@dataclass(frozen=True)
class JCodeContainmentConfig:
    workspace: Path
    jcode_home: Path
    allowed_files: tuple[str, ...]
    protected_files: tuple[str, ...] = ()
    bwrap_path: str = "bwrap"


def build_jcode_containment_args(
    command: Sequence[str],
    config: JCodeContainmentConfig,
) -> list[str]:
    """Expose only explicit read-only files in an otherwise empty work root."""
    if not command:
        raise JCodeContainmentError("jcode_containment_command_missing")
    workspace = _validated_workspace(config.workspace)
    jcode_home = _validated_jcode_home(config.jcode_home, workspace)
    allowed = _validated_allowed_files(
        workspace,
        config.allowed_files,
        config.protected_files,
    )
    if shutil.which(config.bwrap_path) is None:
        raise JCodeContainmentError("jcode_containment_bubblewrap_unavailable")

    args = build_bubblewrap_args(
        command,
        BubblewrapConfig(bwrap_path=config.bwrap_path, network_policy="none"),
    )
    command_index = args.index("--")
    containment_binds: list[str] = [
        "--perms",
        "0755",
        "--dir",
        "/workspace",
        "--bind",
        str(jcode_home),
        "/jcode-home",
    ]
    for source, relative in allowed:
        containment_binds.extend(["--ro-bind", str(source), f"/workspace/{relative}"])
    return [
        *args[:command_index],
        *containment_binds,
        "--chdir",
        "/workspace",
        *args[command_index:],
    ]


def assemble_preassembled_root(config: PreassembledRootConfig) -> Path:
    """Copy only an executable and declared runtime files into a fresh root."""
    root = config.root.resolve()
    if root.exists() or root.is_symlink() or not config.executable.is_file() or config.executable.is_symlink():
        raise JCodeContainmentError("jcode_preassembled_root_invalid")
    if not config.executable_name or "/" in config.executable_name:
        raise JCodeContainmentError("jcode_preassembled_executable_name_invalid")
    root.mkdir(mode=0o700)
    for directory in ("usr/bin", "workspace", "jcode-home", "tmp", "proc", "dev", "run/jcode-bridge"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    _copy_root_file(config.executable, root / "usr/bin" / config.executable_name)
    for source, name in config.additional_executables:
        if not name or "/" in name or not source.is_file() or source.is_symlink():
            raise JCodeContainmentError("jcode_preassembled_extra_executable_invalid")
        _copy_root_file(source, root / "usr/bin" / name)
    for source, destination in config.additional_files:
        if not destination or destination.startswith("/") or ".." in Path(destination).parts or not source.is_file() or source.is_symlink():
            raise JCodeContainmentError("jcode_preassembled_extra_file_invalid")
        target = root / destination
        _copy_root_file(source, target)
        target.chmod(0o444)
    for runtime in config.runtime_files:
        source = runtime.absolute()
        if not source.is_absolute() or not source.is_file():
            raise JCodeContainmentError("jcode_preassembled_runtime_invalid")
        _copy_root_file(source, root / source.relative_to("/"))
    return root


def build_preassembled_root_args(
    command: Sequence[str], root: Path, *, writable_workspace: bool = False
) -> list[str]:
    """Run only a preassembled root, never an introduced host mount."""
    if not command or not root.is_dir() or root.is_symlink():
        raise JCodeContainmentError("jcode_preassembled_command_or_root_invalid")
    return [
        "bwrap", "--clearenv", "--unshare-user", "--unshare-pid", "--unshare-ipc",
        "--unshare-uts", "--unshare-cgroup", "--unshare-net", "--new-session",
        "--die-with-parent", "--cap-drop", "ALL", "--uid", "0", "--gid", "0",
        "--ro-bind", str(root.resolve()), "/", "--proc", "/proc", "--dev", "/dev",
        "--tmpfs", "/tmp", "--dir", "/tmp/jcode-home",
        "--chdir", "/tmp" if writable_workspace else "/workspace", "--setenv", "PATH", "/usr/bin:/bin",
        "--setenv", "HOME", "/tmp/jcode-home", "--setenv", "JCODE_HOME", "/tmp/jcode-home",
        "--setenv", "TMPDIR", "/tmp",
        "--setenv", "JCODE_ALLOW_COMMIT", "0", "--setenv", "JCODE_ALLOW_DEPLOY", "0",
        "--setenv", "JCODE_ALLOW_PUSH", "0", "--setenv", "JCODE_AUTO_UPDATE_ENABLED", "0",
        "--setenv", "JCODE_MEMORY_ENABLED", "0", "--setenv", "JCODE_NETWORK_ENABLED", "0",
        "--setenv", "JCODE_NO_TELEMETRY", "1", "--setenv", "JCODE_SESSION_RESUME_ENABLED", "0",
        "--", *command,
    ]


def _copy_root_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.parent.chmod(0o755)
    shutil.copyfile(source, destination, follow_symlinks=True)
    destination.chmod(0o755 if os.access(source, os.X_OK) else 0o444)


def run_jcode_containment_probe(
    command: Sequence[str],
    config: JCodeContainmentConfig,
    *,
    timeout_seconds: int = 15,
) -> subprocess.CompletedProcess[str]:
    """Run a diagnostic probe under the same boundary a future runner needs."""
    return subprocess.run(
        build_jcode_containment_args(command, config),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


def build_contained_fixture_args(
    command: Sequence[str], config: ContainmentFixtureConfig
) -> list[str]:
    """Build the C2-J.9B no-network, no-host-home fixture sandbox."""
    if not command:
        raise JCodeContainmentError("containment_fixture_command_missing")
    paths = {
        "fixture_input": _validated_fixture_directory(config.fixture_input, writable=False),
        "fixture_output": _validated_fixture_directory(config.fixture_output, writable=True),
        "isolated_home": _validated_fixture_directory(config.isolated_home, writable=True),
        "isolated_tmp": _validated_fixture_directory(config.isolated_tmp, writable=True),
    }
    if len({str(path) for path in paths.values()}) != len(paths):
        raise JCodeContainmentError("containment_fixture_paths_not_distinct")
    if shutil.which(config.bwrap_path) is None:
        raise JCodeContainmentError("containment_fixture_bubblewrap_unavailable")

    # The fixture command is the only executable payload. The root is constructed
    # from explicit system-library binds plus fresh fixture directories.
    args = [
        config.bwrap_path,
        "--clearenv",
        "--unshare-user",
        "--unshare-pid",
        "--unshare-ipc",
        "--unshare-uts",
        "--unshare-cgroup",
        "--unshare-net",
        "--new-session",
        "--die-with-parent",
        "--cap-drop",
        "ALL",
        "--uid",
        "0",
        "--gid",
        "0",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/run",
        "--tmpfs",
        "/tmp",
        "--dir",
        "/tmp/input",
        "--dir",
        "/tmp/output",
        "--dir",
        "/tmp/home",
        "--dir",
        "/workspace",
        "--ro-bind",
        "/usr",
        "/usr",
        "--ro-bind",
        "/bin",
        "/bin",
        "--ro-bind",
        "/lib",
        "/lib",
        "--ro-bind-try",
        "/lib64",
        "/lib64",
        "--ro-bind-try",
        "/etc/alternatives",
        "/etc/alternatives",
        "--setenv",
        "HOME",
        "/tmp/home",
        "--setenv",
        "TMPDIR",
        "/tmp",
        "--setenv",
        "PATH",
        "/usr/bin:/bin",
        "--setenv",
        "LANG",
        "C",
        "--setenv",
        "LC_ALL",
        "C",
        "--setenv",
        "TZ",
        "UTC",
        "--chdir",
        "/workspace",
        "--",
        "/usr/bin/prlimit",
        f"--as={config.memory_max_bytes}",
        f"--fsize={config.file_size_max_bytes}",
        f"--nofile={config.open_files_max}",
        "--",
        *command,
    ]
    return args


def run_contained_fixture(
    command: Sequence[str],
    config: ContainmentFixtureConfig,
    *,
    timeout_seconds: float = 60,
) -> subprocess.CompletedProcess[str]:
    """Launch one deterministic fixture in the selected cgroup and namespaces."""
    try:
        scope = CgroupScopeConfig(
            run_id=config.run_id,
            memory_max_bytes=config.memory_max_bytes,
            tasks_max=config.tasks_max,
            cpu_quota_percent=config.cpu_quota_percent,
            file_size_max_bytes=config.file_size_max_bytes,
            open_files_max=config.open_files_max,
            systemd_run_path=config.systemd_run_path,
        )
        file_descriptors = _open_fixture_input_files(config.fixture_input)
        try:
            args = _with_private_fixture_input(
                build_contained_fixture_args(command, config), file_descriptors
            )
            return run_in_cgroup_scope(
                args,
                scope,
                timeout_seconds=timeout_seconds,
                pass_fds=[fd for _, fd in file_descriptors],
            )
        finally:
            for _, descriptor in file_descriptors:
                os.close(descriptor)
    except ValueError as error:
        raise JCodeContainmentError(str(error)) from error


def containment_fixture_cleanup(paths: Sequence[Path]) -> dict[str, bool]:
    """Remove only explicitly supplied disposable fixture paths."""
    results: dict[str, bool] = {}
    for value in paths:
        path = value.resolve()
        if path == Path("/") or not path.is_dir() or path.is_symlink():
            raise JCodeContainmentError("containment_fixture_cleanup_path_invalid")
        shutil.rmtree(path)
        results[str(path)] = not path.exists()
    parents = {Path(key).parent for key in results}
    if len(parents) == 1:
        parent = parents.pop()
        try:
            parent.rmdir()
        except OSError:
            pass
        results[str(parent)] = not parent.exists()
    return results


def _validated_workspace(value: Path) -> Path:
    workspace = value.resolve()
    if not workspace.is_dir() or workspace.is_symlink():
        raise JCodeContainmentError("jcode_containment_workspace_invalid")
    return workspace


def _validated_fixture_directory(value: Path, *, writable: bool) -> Path:
    if value.is_symlink():
        raise JCodeContainmentError("containment_fixture_directory_invalid")
    path = value.resolve()
    if not path.is_dir():
        raise JCodeContainmentError("containment_fixture_directory_invalid")
    # User namespaces deliberately avoid host-identity inheritance. Writable
    # disposable mounts must therefore be accessible to the mapped sandbox UID.
    if writable and not path.stat().st_mode & 0o002:
        raise JCodeContainmentError("containment_fixture_directory_not_writable")
    return path


def _open_fixture_input_files(root: Path) -> list[tuple[str, int]]:
    """Open only regular, non-symlink fixture files for private tmpfs copying."""
    entries: list[tuple[str, int]] = []
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if path.is_symlink() or not path.is_file():
            raise JCodeContainmentError("containment_fixture_input_not_regular_file")
        relative = path.relative_to(root).as_posix()
        descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
        entries.append((relative, descriptor))
    if not entries:
        raise JCodeContainmentError("containment_fixture_input_missing")
    return entries


def _with_private_fixture_input(
    args: list[str], entries: Sequence[tuple[str, int]]
) -> list[str]:
    command_index = args.index("--")
    setup: list[str] = []
    known_directories = {"/tmp/input"}
    for relative, descriptor in entries:
        parts = relative.split("/")
        for size in range(1, len(parts)):
            directory = "/tmp/input/" + "/".join(parts[:size])
            if directory not in known_directories:
                setup.extend(["--dir", directory])
                known_directories.add(directory)
        setup.extend(["--perms", "0444", "--file", str(descriptor), f"/tmp/input/{relative}"])
    return [*args[:command_index], *setup, *args[command_index:]]


def _validated_jcode_home(value: Path, workspace: Path) -> Path:
    home = value.resolve()
    if not home.is_dir() or home.is_symlink():
        raise JCodeContainmentError("jcode_containment_home_invalid")
    if _is_relative_to(home, workspace) or _is_relative_to(workspace, home):
        raise JCodeContainmentError("jcode_containment_home_not_isolated")
    if any(home.iterdir()):
        raise JCodeContainmentError("jcode_containment_home_not_fresh")
    return home


def _validated_allowed_files(
    workspace: Path,
    allowed_files: Sequence[str],
    protected_files: Sequence[str],
) -> list[tuple[Path, str]]:
    if not allowed_files:
        raise JCodeContainmentError("jcode_containment_allowed_files_missing")
    protected = set(protected_files)
    results: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for raw in allowed_files:
        relative = str(raw).replace("\\", "/").strip()
        if (
            not relative
            or has_percent_encoded_path_syntax(relative)
            or path_escapes_workspace(relative)
            or is_secret_shaped_path(relative)
            or relative in protected
        ):
            raise JCodeContainmentError("jcode_containment_allowed_path_invalid")
        if relative in seen:
            raise JCodeContainmentError("jcode_containment_allowed_path_duplicate")
        seen.add(relative)
        candidate = workspace / relative
        if not candidate.is_file() or candidate.is_symlink():
            raise JCodeContainmentError("jcode_containment_allowed_file_missing_or_symlink")
        resolved = candidate.resolve()
        if not _is_relative_to(resolved, workspace) or resolved != candidate:
            raise JCodeContainmentError("jcode_containment_allowed_path_escape")
        if any(
            _is_relative_to(candidate, workspace / protected_path)
            or _is_relative_to(workspace / protected_path, candidate)
            for protected_path in protected
        ):
            raise JCodeContainmentError("jcode_containment_allowed_protected_overlap")
        results.append((resolved, relative))
    return results


def _is_relative_to(candidate: Path, parent: Path) -> bool:
    try:
        candidate.relative_to(parent)
        return True
    except ValueError:
        return False
