from __future__ import annotations

import os
from pathlib import Path

from source_proxy.cartographer.models import CartographerProject, ConfiguredRoot, ProjectCandidate

_BROAD_ROOTS = {
    "/",
    "/home",
    "/root",
    "/etc",
    "/var",
    "/usr",
    "C:\\",
    "C:/",
    "C:\\Users",
    "C:/Users",
    "C:\\Windows",
    "C:/Windows",
}

_BLOCKED_SEGMENTS = {
    ".env",
    ".ssh",
    "cert",
    "certs",
    "certificate",
    "certificates",
    "key",
    "keys",
    "private",
    "secret",
    "secrets",
    "token",
    "tokens",
    "credential",
    "credentials",
    "backup",
    "backups",
}

_PROJECT_MARKERS = (
    ".git",
    "package.json",
    "README.md",
    "pyproject.toml",
    "requirements.txt",
    "src",
    "app",
    "tests",
    "_blueprints",
)


def parse_project_roots(value: str | None = None) -> tuple[list[ConfiguredRoot], list[ConfiguredRoot]]:
    raw_value = os.getenv("SPIRIT_PROJECT_PATH", "") if value is None else value
    configured: list[ConfiguredRoot] = []
    blocked: list[ConfiguredRoot] = []
    seen: set[str] = set()

    for raw_path in _split_env_paths(raw_value):
        raw_normalized = raw_path.strip().strip('"').strip("'")
        raw_block_reason = _blocked_root_reason(raw_normalized)
        if raw_block_reason:
            blocked.append(
                ConfiguredRoot(
                    path=raw_normalized,
                    status="blocked",
                    reason=raw_block_reason,
                )
            )
            continue

        normalized = _normalize_root_path(raw_path)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)

        block_reason = _blocked_root_reason(normalized)
        if block_reason:
            blocked.append(
                ConfiguredRoot(
                    path=normalized,
                    status="blocked",
                    reason=block_reason,
                )
            )
            continue

        configured.append(
            ConfiguredRoot(
                path=normalized,
                status="configured",
                reason="explicitly_allowlisted",
            )
        )

    return configured, blocked


def configured_project_roots() -> list[ConfiguredRoot]:
    configured, _blocked = parse_project_roots()
    return configured


def blocked_project_roots() -> list[ConfiguredRoot]:
    _configured, blocked = parse_project_roots()
    return blocked


def discover_projects() -> list[CartographerProject]:
    projects: list[CartographerProject] = []
    seen_roots: set[str] = set()

    for configured_root in configured_project_roots():
        root = Path(configured_root.path)
        if not root.exists() or not root.is_dir():
            continue

        for candidate in _project_candidates(root):
            resolved = str(candidate.resolve())
            if resolved in seen_roots:
                continue

            markers = _detect_project_markers(candidate)
            if not markers:
                continue

            seen_roots.add(resolved)
            name = _project_name(candidate)
            blueprint_root = _blueprint_root(candidate)
            projects.append(
                CartographerProject(
                    project_id=_project_id(name),
                    name=name,
                    root=resolved,
                    markers=markers,
                    has_blueprints=blueprint_root is not None,
                    blueprint_root=blueprint_root,
                    source_root=configured_root.path,
                )
            )

    return projects


def discover_project_candidates() -> list[ProjectCandidate]:
    candidates: list[ProjectCandidate] = []
    seen_roots: set[str] = set()

    for configured_root in configured_project_roots():
        root = Path(configured_root.path)
        if not root.exists() or not root.is_dir() or _detect_project_markers(root):
            continue

        for candidate in _project_candidates(root):
            resolved = str(candidate.resolve())
            if resolved in seen_roots:
                continue

            markers = _detect_project_markers(candidate)
            if not markers:
                continue
            if "_blueprints" in markers:
                continue

            seen_roots.add(resolved)
            name = _project_name(candidate)
            project_id = _project_id(name)
            candidates.append(
                ProjectCandidate(
                    candidate_id=f"new-project-{project_id}",
                    project_id=project_id,
                    name=name,
                    root=resolved,
                    markers=markers,
                    source_root=configured_root.path,
                    action_taken=False,
                )
            )

    return candidates


def _split_env_paths(value: str) -> list[str]:
    return [part.strip() for part in value.replace("\n", ",").split(",") if part.strip()]


def _normalize_root_path(raw_path: str) -> str:
    path = raw_path.strip().strip('"').strip("'")
    if not path:
        return ""
    if _looks_like_windows_path(path):
        return path if len(path) == 3 else path.rstrip("\\/")

    expanded = Path(path).expanduser()
    try:
        return str(expanded.resolve(strict=False))
    except OSError:
        return str(expanded)


def _looks_like_windows_path(path: str) -> bool:
    return len(path) >= 3 and path[1] == ":" and path[2] in ("\\", "/")


def _blocked_root_reason(path: str) -> str | None:
    trimmed = path.rstrip("\\/")
    if trimmed.lower() in {item.rstrip("\\/").lower() for item in _BROAD_ROOTS}:
        return "broad_system_root_not_allowed"

    segments = [
        segment.lower()
        for segment in path.replace("\\", "/").split("/")
        if segment and segment != ":"
    ]
    if ".." in segments:
        return "path_traversal_root_not_allowed"

    for segment in segments:
        if (
            segment in _BLOCKED_SEGMENTS
            or segment.startswith(".env")
            or "secret" in segment
            or "token" in segment
            or "credential" in segment
            or "backup" in segment
            or segment.endswith(".pem")
            or segment.endswith(".key")
        ):
            return "secret_or_backup_shaped_root_not_allowed"

    return None


def _project_candidates(root: Path) -> list[Path]:
    if _detect_project_markers(root):
        return [root]

    candidates: list[Path] = []
    try:
        children = sorted(root.iterdir(), key=lambda item: item.name.lower())
    except OSError:
        return candidates

    for child in children:
        if not _is_within_root(child, root):
            continue
        if not child.is_dir() or _is_ignored_project_candidate(child):
            continue
        candidates.append(child)

    return candidates


def _detect_project_markers(candidate: Path) -> list[str]:
    markers: list[str] = []
    for marker in _PROJECT_MARKERS:
        marker_path = candidate / marker
        try:
            if marker_path.exists():
                markers.append(marker)
        except OSError:
            continue
    return markers


def _blueprint_root(candidate: Path) -> str | None:
    blueprint_path = candidate / "_blueprints"
    try:
        if blueprint_path.is_dir():
            return str(blueprint_path.resolve())
    except OSError:
        return None
    return None


def _is_ignored_project_candidate(path: Path) -> bool:
    name = path.name.lower()
    if name.startswith("."):
        return True
    if name in {
        "__pycache__",
        "node_modules",
        ".next",
        "dist",
        "build",
        "coverage",
        "tmp",
        "temp",
        "logs",
        "venv",
        ".venv",
    }:
        return True
    return _blocked_root_reason(str(path)) is not None


def _is_within_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def _project_id(name: str) -> str:
    chars: list[str] = []
    previous_dash = False
    for char in name.lower():
        if char.isalnum():
            chars.append(char)
            previous_dash = False
        elif not previous_dash:
            chars.append("-")
            previous_dash = True
    return "".join(chars).strip("-") or "project"


def _project_name(path: Path) -> str:
    if path.name:
        return path.name
    try:
        resolved_name = path.resolve().name
    except OSError:
        resolved_name = ""
    return resolved_name or "project"
