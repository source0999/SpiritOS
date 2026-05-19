from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path


SECRET_NAME_MARKERS = (
    ".env",
    ".pem",
    ".key",
    "secret",
    "token",
    "credential",
    "id_rsa",
    "id_ed25519",
)

EXPLICIT_TARGET_LINE_RE = re.compile(
    r"^\s*target\s+file\s*:\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)

_LEADING_COMMA_TARGET_RE = re.compile(
    r"^\s*([`'\"]?)(?P<path>"
    r"(?:[A-Za-z]:[\\/][^,\r\n]+)"
    r"|(?:\.\.[\\/][^,\r\n]+)"
    r"|(?:\.[\\/]\.env(?:\.[A-Za-z0-9_.-]+)?)"
    r"|(?:\.env(?:\.[A-Za-z0-9_.-]+)?)"
    r"|(?:[A-Za-z0-9._/@()[\]\\-]+\.[A-Za-z0-9]+)"
    r")\1\s*,",
    re.MULTILINE,
)

_UNSAFE_PATH_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_./\\:-])(?P<path>"
    r"(?:[A-Za-z]:[\\/][^\s,;]+)"
    r"|(?:\\\\[^\s,;]+)"
    r"|(?:\.\.[\\/][^\s,;]+)"
    r"|(?:\.[\\/]\.env(?:\.[A-Za-z0-9_.-]+)?)"
    r"|(?:\.env(?:\.[A-Za-z0-9_.-]+)?)"
    r"|(?:/(?:home|users|tmp|etc|var|opt|mnt|volumes|workspace|root|usr|private)/[^\s,;]+)"
    r")",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class UnsafeTargetFinding:
    path: str
    reason_code: str
    message: str


def strip_wrapping_quotes(raw: str) -> str:
    value = raw.strip()
    while len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'", "`"}:
        value = value[1:-1].strip()
    return value


def strip_repo_path_sentence_punctuation(path: str) -> str:
    stripped = path.strip()
    while stripped and stripped[-1] in ".,:;!?":
        candidate = stripped[:-1]
        if re.search(r"\.[A-Za-z0-9_-]+$", candidate):
            stripped = candidate
            continue
        break
    return stripped


def normalize_repo_path_candidate(raw_path: str, *, strip_diff_prefix: bool = False) -> str:
    path = strip_wrapping_quotes(raw_path).replace("\\", "/").strip()
    if "\t" in path:
        path = path.split("\t", 1)[0].strip()
    path = re.sub(
        r"\s+\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\s+[+-]\d{4})?)?$",
        "",
        path,
    ).strip()
    if path in {"", "/dev/null", "dev/null", "a/dev/null", "b/dev/null"}:
        return ""
    if strip_diff_prefix and (path.startswith("a/") or path.startswith("b/")):
        path = path[2:]
    while path.startswith("./"):
        path = path[2:]
    return _remove_current_directory_segments(strip_repo_path_sentence_punctuation(path))


def explicit_target_file_lines(task: str) -> list[str]:
    paths: list[str] = []
    for match in EXPLICIT_TARGET_LINE_RE.finditer(task or ""):
        path = normalize_repo_path_candidate(match.group(1))
        if path:
            paths.append(path)
    return paths


def explicit_target_from_task(task: str) -> str:
    paths = explicit_target_file_lines(task)
    return paths[-1] if paths else ""


def explicit_or_unsafe_target_candidates(
    task: str,
    *,
    skip_paths: frozenset[str] | None = None,
) -> list[str]:
    text = task or ""
    candidates: list[str] = []
    candidates.extend(explicit_target_file_lines(text))
    for match in _LEADING_COMMA_TARGET_RE.finditer(text):
        candidates.append(normalize_repo_path_candidate(match.group("path")))
    for match in _UNSAFE_PATH_TOKEN_RE.finditer(text):
        candidates.append(normalize_repo_path_candidate(match.group("path")))
    if not skip_paths:
        return _dedupe_paths(candidates)
    filtered: list[str] = []
    for candidate in _dedupe_paths(candidates):
        if candidate in skip_paths:
            continue
        filtered.append(candidate)
    return filtered


def unsafe_target_from_task(
    task: str,
    workspace_root: Path | None = None,
    *,
    skip_paths: frozenset[str] | None = None,
    skip_path_checker: Callable[[str], bool] | None = None,
) -> UnsafeTargetFinding | None:
    for candidate in explicit_or_unsafe_target_candidates(task, skip_paths=skip_paths):
        if skip_path_checker is not None and skip_path_checker(candidate):
            continue
        finding = unsafe_target_finding(candidate, workspace_root=workspace_root)
        if finding is not None:
            return finding
    return None


def unsafe_target_finding(
    raw_path: str,
    *,
    workspace_root: Path | None = None,
) -> UnsafeTargetFinding | None:
    path = normalize_repo_path_candidate(raw_path)
    if not path:
        return None
    if path_escapes_workspace(path, workspace_root=workspace_root):
        return UnsafeTargetFinding(
            path=path,
            reason_code="path_escape",
            message="Target path escapes the workspace.",
        )
    if is_secret_shaped_path(path):
        return UnsafeTargetFinding(
            path=path,
            reason_code="protected_path",
            message="Target path is protected or secret-shaped.",
        )
    return None


def path_escapes_workspace(path: str, *, workspace_root: Path | None = None) -> bool:
    normalized = path.replace("\\", "/").strip()
    if not normalized:
        return False
    if normalized.startswith("/") or normalized.startswith("//"):
        return True
    if len(normalized) >= 3 and normalized[1:3] == ":/":
        return True
    parts = [part for part in normalized.split("/") if part]
    if ".." in parts:
        return True
    if workspace_root is not None:
        root = workspace_root.resolve()
        try:
            candidate = (root / normalized).resolve()
            candidate.relative_to(root)
        except ValueError:
            return True
    return False


def is_secret_shaped_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    parts = [part for part in normalized.split("/") if part]
    return any(
        part.startswith(".") or any(marker in part for marker in SECRET_NAME_MARKERS)
        for part in parts
    )


def _dedupe_paths(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        path = normalize_repo_path_candidate(value)
        if not path or path in seen:
            continue
        seen.add(path)
        result.append(path)
    return result


def _remove_current_directory_segments(path: str) -> str:
    if not path:
        return ""
    absolute = path.startswith("/")
    trailing_slash = path.endswith("/") and path != "/"
    parts = [part for part in path.split("/") if part and part != "."]
    normalized = "/".join(parts)
    if absolute:
        normalized = f"/{normalized}"
    if trailing_slash and normalized and not normalized.endswith("/"):
        normalized = f"{normalized}/"
    return normalized
