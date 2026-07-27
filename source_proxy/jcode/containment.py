"""OS-enforced containment for future JCode qualification probes.

This is deliberately a sandbox policy builder, not a JCode dispatcher. It
requires an explicit existing-file input set and uses Bubblewrap's unshared
network with an otherwise empty workspace for all Gate 2-J.2 probes.
"""
from __future__ import annotations

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


class JCodeContainmentError(ValueError):
    """The requested filesystem boundary cannot be enforced safely."""


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


def _validated_workspace(value: Path) -> Path:
    workspace = value.resolve()
    if not workspace.is_dir() or workspace.is_symlink():
        raise JCodeContainmentError("jcode_containment_workspace_invalid")
    return workspace


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
