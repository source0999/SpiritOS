from __future__ import annotations

from pathlib import Path

from source_proxy.cartographer.models import ClutterCandidate
from source_proxy.cartographer.project_discovery import discover_projects

_SKIPPED_DIRS = {
    ".git",
    ".next",
    ".pytest_cache",
    ".venv",
    ".venv-source-proxy",
    "__pycache__",
    "node_modules",
}
_MAX_FILES_SCANNED = 5000
_MAX_CANDIDATES = 250


def build_clutter_inventory() -> list[ClutterCandidate]:
    candidates: list[ClutterCandidate] = []
    seen: set[str] = set()
    for root in _scan_roots():
        scanned = 0
        for path in _iter_files(root):
            scanned += 1
            if scanned > _MAX_FILES_SCANNED or len(candidates) >= _MAX_CANDIDATES:
                break
            relative = _relative_path(root, path)
            candidate = _candidate_for_path(relative)
            if not candidate or candidate.path in seen:
                continue
            seen.add(candidate.path)
            candidates.append(candidate)
    return sorted(candidates, key=lambda item: (_risk_order(item.risk), item.path))


def _scan_roots() -> list[Path]:
    roots = [Path(project.root) for project in discover_projects()]
    if not roots and (Path.cwd() / ".git").exists():
        roots = [Path.cwd()]
    return roots


def _iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIPPED_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def _relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _candidate_for_path(path: str) -> ClutterCandidate | None:
    lower = path.lower()
    parts = lower.split("/")
    filename = parts[-1]

    if _is_blocked_path(parts, filename):
        return ClutterCandidate(
            path="[redacted]" if _is_secret_shaped(parts, filename) else path,
            risk="blocked",
            reason="Protected path requires explicit human review and cannot be treated as clutter.",
            confidence="high",
            category="protected",
        )

    if _is_generated_log(parts, filename):
        return ClutterCandidate(
            path=path,
            risk="low",
            reason="Generated snapshot or soak log; inventory only, no deletion allowed.",
            confidence="high",
            category="generated_log",
        )

    if _is_repomix_output(filename):
        return ClutterCandidate(
            path=path,
            risk="low",
            reason="Generated repomix output; inventory only, no deletion allowed.",
            confidence="high",
            category="generated_report",
        )

    if _is_empty_temp_marker(filename):
        return ClutterCandidate(
            path=path,
            risk="low",
            reason="Temporary or placeholder-shaped file; inventory only, no deletion allowed.",
            confidence="medium",
            category="temporary_file",
        )

    if _is_stale_doc_or_plan(parts, filename):
        return ClutterCandidate(
            path=path,
            risk="medium",
            reason="Plan or draft-style documentation may be stale; manual review required.",
            confidence="medium",
            category="stale_doc_or_plan",
        )

    if _is_source_or_config(parts, filename):
        return ClutterCandidate(
            path=path,
            risk="high",
            reason="Source, config, test, or safety-adjacent file is never low-risk clutter.",
            confidence="high",
            category="source_or_config",
        )

    return None


def _is_blocked_path(parts: list[str], filename: str) -> bool:
    return (
        ".git" in parts
        or ".env" in filename
        or filename.endswith(".pem")
        or filename.endswith(".key")
        or "auth" in parts
        or "approval" in parts
        or "secrets" in parts
        or "credentials" in parts
        or "database" in parts
    )


def _is_secret_shaped(parts: list[str], filename: str) -> bool:
    return (
        ".env" in filename
        or filename.endswith(".pem")
        or filename.endswith(".key")
        or "secrets" in parts
        or "credentials" in parts
    )


def _is_generated_log(parts: list[str], filename: str) -> bool:
    return (
        filename.endswith(".json")
        and ("soak-logs" in parts or filename.startswith("cartographer-soak-") or filename.startswith("scout-soak-"))
    )


def _is_repomix_output(filename: str) -> bool:
    return (
        filename.startswith("repomix")
        and "config" not in filename
        and filename.endswith((".txt", ".md", ".json"))
    )


def _is_empty_temp_marker(filename: str) -> bool:
    return filename in {".tmp", "tmp", "temp"} or filename.endswith((".tmp", ".bak"))


def _is_stale_doc_or_plan(parts: list[str], filename: str) -> bool:
    return filename.endswith(".md") and (
        "docs" in parts
        or "plan" in filename
        or "draft" in filename
        or "old" in filename
        or "archive" in parts
    )


def _is_source_or_config(parts: list[str], filename: str) -> bool:
    return (
        filename in {"package.json", "pyproject.toml", "requirements.txt", "dockerfile"}
        or filename.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".json", ".yaml", ".yml", ".toml"))
        or any(part in {"src", "source_proxy", "scripts", "tests"} for part in parts)
    )


def _risk_order(risk: str) -> int:
    return {"blocked": 0, "high": 1, "medium": 2, "low": 3}.get(risk, 4)
