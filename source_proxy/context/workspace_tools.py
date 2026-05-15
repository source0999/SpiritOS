from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from typing import Any

from source_proxy.context.inventory import build_safe_context_inventory

MAX_LIST_ENTRIES = 100
MAX_READ_BYTES = 64_000


class WorkspaceToolError(ValueError):
    def __init__(self, message: str, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


@dataclass(frozen=True)
class ResolvedWorkspacePath:
    root: Path
    path: Path


def list_workspace_path(
    requested_path: str | None = None,
    *,
    project_root: Path | None = None,
    max_entries: int = MAX_LIST_ENTRIES,
) -> dict[str, Any]:
    resolved = resolve_workspace_path(requested_path, project_root=project_root)
    if not resolved.path.is_dir():
        raise WorkspaceToolError("Requested path is not a directory.", "not_directory")

    entries: list[dict[str, Any]] = []
    for child in sorted(resolved.path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
        if len(entries) >= max_entries:
            break
        if _is_blocked_path(child, resolved.root):
            continue
        entries.append(
            {
                "name": child.name,
                "path": _relative_path(child, resolved.root),
                "kind": "directory" if child.is_dir() else "file",
                "size_bytes": child.stat().st_size if child.is_file() else None,
            }
        )

    return {
        "tool": "workspace_list",
        "access_scope": "read_only_workspace_listing",
        "root": str(resolved.root),
        "path": _relative_path(resolved.path, resolved.root),
        "entries": entries,
        "truncated": len(entries) >= max_entries,
        "limits": {
            "max_entries": max_entries,
            "hidden_files_included": False,
            "secret_shaped_paths_included": False,
            "recursive": False,
        },
    }


def read_workspace_excerpt(
    requested_path: str,
    *,
    project_root: Path | None = None,
    max_bytes: int = MAX_READ_BYTES,
) -> dict[str, Any]:
    resolved = resolve_workspace_path(requested_path, project_root=project_root)
    if not resolved.path.is_file():
        raise WorkspaceToolError("Requested path is not a file.", "not_file")
    if _is_blocked_path(resolved.path, resolved.root):
        raise WorkspaceToolError("Requested path is blocked by workspace safety policy.", "blocked_path")

    raw = resolved.path.read_bytes()[:max_bytes]
    text = raw.decode("utf-8", errors="replace")
    size = resolved.path.stat().st_size

    return {
        "tool": "workspace_read_excerpt",
        "access_scope": "read_only_workspace_file_excerpt",
        "root": str(resolved.root),
        "path": _relative_path(resolved.path, resolved.root),
        "size_bytes": size,
        "excerpt": text,
        "truncated": size > max_bytes,
        "limits": {
            "max_bytes": max_bytes,
            "writes_allowed": False,
            "hidden_files_allowed": False,
            "secret_shaped_paths_allowed": False,
        },
    }


def resolve_workspace_path(
    requested_path: str | None = None,
    *,
    project_root: Path | None = None,
) -> ResolvedWorkspacePath:
    root = _default_workspace_root(project_root)
    raw_path = (requested_path or ".").strip() or "."
    if _is_foreign_absolute_path(raw_path):
        raise WorkspaceToolError("Requested path escapes the configured workspace root.", "path_escape")
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    path = candidate.resolve()

    if not _is_relative_to(path, root):
        raise WorkspaceToolError("Requested path escapes the configured workspace root.", "path_escape")
    if _is_blocked_path(path, root):
        raise WorkspaceToolError("Requested path is blocked by workspace safety policy.", "blocked_path")
    if not path.exists():
        raise WorkspaceToolError("Requested path does not exist.", "not_found")

    return ResolvedWorkspacePath(root=root, path=path)


def _default_workspace_root(project_root: Path | None = None) -> Path:
    inventory = build_safe_context_inventory(project_root)
    roots = inventory["verified_context_roots"]
    if not roots:
        raise WorkspaceToolError("No verified workspace root is available.", "no_verified_root")
    first_root = roots[0]["path"]
    if not first_root:
        raise WorkspaceToolError("Verified workspace root did not include a path.", "no_verified_root")
    return Path(str(first_root)).resolve()


def _is_blocked_path(path: Path, root: Path) -> bool:
    relative_path = _relative_path(path, root)
    if relative_path == ".":
        return False

    relative_parts = relative_path.split("/")
    return any(_is_blocked_name(part) for part in relative_parts)


def _is_blocked_name(name: str) -> bool:
    lowered = name.lower()
    if not lowered or lowered.startswith("."):
        return True
    return any(
        marker in lowered
        for marker in [
            ".env",
            ".pem",
            ".key",
            "secret",
            "token",
            "credential",
            "id_rsa",
            "id_ed25519",
        ]
    )


def _relative_path(path: Path, root: Path) -> str:
    value = path.relative_to(root).as_posix()
    return "." if value == "." else value


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _is_foreign_absolute_path(raw_path: str) -> bool:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return False

    windows_path = PureWindowsPath(raw_path)
    return bool(windows_path.drive or windows_path.root)
