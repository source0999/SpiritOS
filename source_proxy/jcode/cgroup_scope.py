"""Transient-scope construction for no-model C2-J fixture processes."""
from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Sequence


class CgroupScopeError(ValueError):
    """A scope request is unsafe or cannot be constructed deterministically."""


@dataclass(frozen=True)
class CgroupScopeConfig:
    run_id: str
    memory_max_bytes: int
    tasks_max: int
    cpu_quota_percent: int
    file_size_max_bytes: int
    open_files_max: int
    systemd_run_path: str = "systemd-run"


def build_cgroup_scope_args(
    command: Sequence[str], config: CgroupScopeConfig
) -> list[str]:
    """Return a user-scope command with sealed resource limits."""
    if not command:
        raise CgroupScopeError("cgroup_scope_command_missing")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,63}", config.run_id):
        raise CgroupScopeError("cgroup_scope_run_id_invalid")
    for value in (
        config.memory_max_bytes,
        config.tasks_max,
        config.cpu_quota_percent,
        config.file_size_max_bytes,
        config.open_files_max,
    ):
        if not isinstance(value, int) or value <= 0:
            raise CgroupScopeError("cgroup_scope_limit_invalid")
    if shutil.which(config.systemd_run_path) is None:
        raise CgroupScopeError("cgroup_scope_systemd_run_unavailable")
    unit = f"jcode-run-{config.run_id}"
    return [
        config.systemd_run_path,
        "--user",
        "--scope",
        "--quiet",
        "--collect",
        f"--unit={unit}",
        "--property=Delegate=yes",
        f"--property=MemoryMax={config.memory_max_bytes}",
        f"--property=TasksMax={config.tasks_max}",
        f"--property=CPUQuota={config.cpu_quota_percent}%",
        "--",
        *command,
    ]


def run_in_cgroup_scope(
    command: Sequence[str],
    config: CgroupScopeConfig,
    *,
    timeout_seconds: float,
    pass_fds: Sequence[int] = (),
) -> subprocess.CompletedProcess[str]:
    """Run an inert command under its dedicated transient scope."""
    if timeout_seconds <= 0:
        raise CgroupScopeError("cgroup_scope_timeout_invalid")
    return subprocess.run(
        build_cgroup_scope_args(command, config),
        capture_output=True,
        text=True,
        pass_fds=tuple(pass_fds),
        timeout=timeout_seconds,
        check=False,
    )
