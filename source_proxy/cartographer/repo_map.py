from __future__ import annotations

import re
from collections import Counter
from time import perf_counter
from pathlib import Path

from source_proxy.cartographer.component_mapper import map_paths
from source_proxy.cartographer.models import RepoMapFile, RepoMapSummary, UnmappedPath
from source_proxy.cartographer.project_discovery import discover_projects

MAP_VERSION = 1
MAX_FILES = 180
MAX_SYMBOLS = 500
MAX_FILE_BYTES = 160_000

_INDEXED_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".md",
    ".json",
}

_SYMBOL_SUFFIXES = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
}

_SKIPPED_DIRS = {
    ".git",
    ".next",
    ".venv",
    ".venv-source-proxy",
    ".venv-source-proxy-windows",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "tmp",
    "temp",
}

_SECRET_SEGMENTS = {
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

_PRIORITY_DIRS = {
    "_blueprints": 0,
    "source_proxy": 1,
    "src": 2,
    "scout": 3,
    "scripts": 4,
}

_PY_SYMBOL_RE = re.compile(r"^(?:async\s+def|def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
_JS_SYMBOL_RE = re.compile(
    r"^(?:export\s+)?(?:async\s+)?(?:function|class|interface|type|const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)",
    re.MULTILINE,
)


def build_repo_maps() -> list[RepoMapSummary]:
    return [build_repo_map_for_project(project.project_id, Path(project.root)) for project in discover_projects()]


def build_repo_map_for_project(project_id: str, root: Path) -> RepoMapSummary:
    started = perf_counter()
    files_seen = 0
    files: list[RepoMapFile] = []
    unmapped: list[UnmappedPath] = []
    skipped: set[str] = set()
    component_counts: Counter[str] = Counter()
    risk_counts: Counter[str] = Counter()
    symbols_indexed = 0

    for path in _walk_project_files(root, skipped):
        files_seen += 1
        if len(files) >= MAX_FILES:
            skipped.add("file_limit_reached")
            break

        rel_path = path.relative_to(root).as_posix()
        component_id, blueprint_id, risk, mapped = _component_for_path(rel_path)
        risk_counts[risk] += 1
        if not mapped:
            unmapped.append(UnmappedPath(path=rel_path, risk=risk))
        elif component_id:
            component_counts[component_id] += 1

        symbols: list[str] = []
        if path.suffix in _SYMBOL_SUFFIXES and symbols_indexed < MAX_SYMBOLS:
            budget = MAX_SYMBOLS - symbols_indexed
            symbols = _extract_symbols(path, budget)
            symbols_indexed += len(symbols)
            if symbols_indexed >= MAX_SYMBOLS:
                skipped.add("symbol_limit_reached")

        files.append(
            RepoMapFile(
                path=rel_path,
                component_id=component_id,
                blueprint_id=blueprint_id,
                risk=risk,
                symbols=symbols,
            )
        )

    key_directories = _key_directories(files)
    api_routes = _paths_matching(files, _is_api_route)
    dashboard_widgets = _paths_matching(files, _is_dashboard_widget)
    tests = _paths_matching(files, _is_test_file)
    blueprints = _paths_matching(files, _is_blueprint_file)

    return RepoMapSummary(
        project_id=project_id,
        map_version=MAP_VERSION,
        scan_duration_ms=max(0, round((perf_counter() - started) * 1000)),
        files_seen=files_seen,
        files_indexed=len(files),
        symbols_indexed=symbols_indexed,
        max_files=MAX_FILES,
        max_symbols=MAX_SYMBOLS,
        component_counts=dict(sorted(component_counts.items())),
        risk_counts=dict(sorted(risk_counts.items())),
        key_directories=key_directories,
        api_routes=api_routes,
        dashboard_widgets=dashboard_widgets,
        tests=tests,
        blueprints=blueprints,
        skipped=sorted(skipped),
        files=files,
        unmapped_paths=unmapped,
    )


def _walk_project_files(root: Path, skipped: set[str]) -> list[Path]:
    files: list[Path] = []
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            entries = _sort_entries(root, directory, list(directory.iterdir()))
        except OSError:
            skipped.add("unreadable_directory")
            continue

        for entry in entries:
            rel_parts = _relative_parts(root, entry)
            skip_reason = _skip_reason(rel_parts)
            if skip_reason:
                skipped.add(skip_reason)
                continue

            if entry.is_dir():
                stack.append(entry)
                continue

            if not entry.is_file():
                continue

            if entry.suffix not in _INDEXED_SUFFIXES:
                continue

            try:
                if entry.stat().st_size > MAX_FILE_BYTES:
                    skipped.add("large_file")
                    continue
            except OSError:
                skipped.add("unreadable_file")
                continue

            files.append(entry)

    return files


def _sort_entries(root: Path, directory: Path, entries: list[Path]) -> list[Path]:
    def key(entry: Path) -> tuple[int, int, str]:
        rel_parts = _relative_parts(root, entry)
        top_level = rel_parts[0].lower() if rel_parts else entry.name.lower()
        priority = _PRIORITY_DIRS.get(top_level, 100)
        is_file = 1 if entry.is_file() else 0
        return (priority, is_file, entry.name.lower())

    # Stack is LIFO, so reverse sorted directory entries before pushing them.
    if directory == root:
        return sorted(entries, key=key, reverse=True)
    return sorted(entries, key=lambda item: item.name.lower(), reverse=True)


def _relative_parts(root: Path, path: Path) -> list[str]:
    try:
        return list(path.relative_to(root).parts)
    except ValueError:
        return list(path.parts)


def _skip_reason(parts: list[str]) -> str | None:
    normalized = [part.lower() for part in parts]
    for part in normalized:
        if part in _SKIPPED_DIRS:
            return part
    for part in normalized:
        if (
            part in _SECRET_SEGMENTS
            or part.startswith(".env")
            or "secret" in part
            or "token" in part
            or "credential" in part
            or "backup" in part
            or part.endswith(".pem")
            or part.endswith(".key")
        ):
            return part
    return None


def _component_for_path(rel_path: str) -> tuple[str | None, str | None, str, bool]:
    components, unmapped = map_paths([rel_path])
    if unmapped or not components:
        risk = unmapped[0].risk if unmapped else "unknown"
        return None, None, risk, False
    component = components[0]
    return (
        component.component_id,
        component.blueprint_id,
        component.matched_path_risks.get(rel_path, component.risk),
        True,
    )


def _key_directories(files: list[RepoMapFile]) -> list[str]:
    directories: set[str] = set()
    for item in files:
        parts = item.path.split("/")
        if len(parts) >= 2:
            directories.add("/".join(parts[:2]))
        elif parts:
            directories.add(parts[0])
    return sorted(directories)


def _paths_matching(files: list[RepoMapFile], predicate: object) -> list[str]:
    return sorted(item.path for item in files if predicate(item.path))


def _is_api_route(path: str) -> bool:
    return (
        path.startswith("src/app/api/")
        or path.startswith("src/app/v1/")
        or path.endswith("/route.ts")
        or path.endswith("/route.tsx")
        or path.startswith("source_proxy/api/")
    )


def _is_dashboard_widget(path: str) -> bool:
    return (
        path.startswith("src/components/dashboard/")
        and path.endswith((".ts", ".tsx", ".js", ".jsx"))
    )


def _is_test_file(path: str) -> bool:
    name = Path(path).name.lower()
    return (
        "/tests/" in path
        or "/__tests__/" in path
        or name.startswith("test_")
        or name.endswith(".test.ts")
        or name.endswith(".test.tsx")
        or name.endswith("_test.py")
    )


def _is_blueprint_file(path: str) -> bool:
    return path.startswith("_blueprints/") and path.endswith(".md")


def _extract_symbols(path: Path, limit: int) -> list[str]:
    if limit <= 0:
        return []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    pattern = _PY_SYMBOL_RE if path.suffix == ".py" else _JS_SYMBOL_RE
    symbols: list[str] = []
    seen: set[str] = set()
    for match in pattern.finditer(text):
        symbol = match.group(1)
        if symbol in seen:
            continue
        seen.add(symbol)
        symbols.append(symbol)
        if len(symbols) >= limit:
            break
    return symbols
