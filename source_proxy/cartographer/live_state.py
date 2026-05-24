from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_GIT_TIMEOUT_SECONDS = 10

_CODING_PREFIXES = ("src/app/coding/", "src/components/coding/")
_MAP_PREFIXES = ("src/app/map/",)
_PACKAGE_CONFIG_ENV_PREFIXES = ("config/",)
_PACKAGE_CONFIG_ENV_FILES = ("package.json", "next.config.ts")
_SOURCE_PROXY_RUNTIME_PREFIXES = ("source_proxy/",)
_SOURCE_PROXY_RUNTIME_EXCLUDED_PREFIXES = ("source_proxy/tests/",)


@dataclass(frozen=True)
class GitCommandFailure:
    command: list[str]
    returncode: int
    stderr: str


def collect_live_repo_state(repo_root: str | Path = ".") -> dict[str, Any]:
    """Collect read-only repository state for Cartographer safety display."""
    root = Path(repo_root)
    collected_at = _utc_now()

    branch_result = _run_git(root, ["git", "branch", "--show-current"])
    head_result = _run_git(root, ["git", "rev-parse", "HEAD"])
    status_result = _run_git(
        root,
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
    )

    failures = [
        _failure_for(result)
        for result in (branch_result, head_result, status_result)
        if result.returncode != 0
    ]
    if failures:
        reasons = [
            f"git command failed closed: {' '.join(failure.command)}"
            for failure in failures
        ]
        return {
            "current_branch": None,
            "current_head": None,
            "tracked_dirty_files": [],
            "untracked_files": [],
            "protected_lane_matches": [],
            "coding_files_dirty": False,
            "map_files_dirty": False,
            "package_config_env_files_dirty": False,
            "source_proxy_runtime_files_dirty": False,
            "unknown_unclassified_dirty_files": [],
            "recommended_safety_state": "blocked",
            "blocker_reasons": reasons,
            "collected_at": collected_at,
            "no_mutation_guarantee": _no_mutation_guarantee(),
            "git_available": False,
            "git_errors": [
                {
                    "command": failure.command,
                    "returncode": failure.returncode,
                    "stderr": failure.stderr,
                }
                for failure in failures
            ],
        }

    parsed = _parse_porcelain_status(status_result.stdout)
    tracked_dirty_files = parsed["tracked_dirty_files"]
    untracked_files = parsed["untracked_files"]
    dirty_files = tracked_dirty_files + untracked_files
    classification = _classify_dirty_files(dirty_files)
    safety = _recommend_safety_state(classification, dirty_files)

    return {
        "current_branch": branch_result.stdout.strip() or None,
        "current_head": head_result.stdout.strip() or None,
        "tracked_dirty_files": tracked_dirty_files,
        "untracked_files": untracked_files,
        "protected_lane_matches": classification["protected_lane_matches"],
        "coding_files_dirty": classification["coding_files_dirty"],
        "map_files_dirty": classification["map_files_dirty"],
        "package_config_env_files_dirty": classification[
            "package_config_env_files_dirty"
        ],
        "source_proxy_runtime_files_dirty": classification[
            "source_proxy_runtime_files_dirty"
        ],
        "unknown_unclassified_dirty_files": classification[
            "unknown_unclassified_dirty_files"
        ],
        "recommended_safety_state": safety["state"],
        "blocker_reasons": safety["blocker_reasons"],
        "collected_at": collected_at,
        "no_mutation_guarantee": _no_mutation_guarantee(),
        "git_available": True,
        "git_errors": [],
    }


def _run_git(root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            command,
            returncode=124,
            stdout="",
            stderr="git_command_timeout",
        )
    except OSError as error:
        return subprocess.CompletedProcess(
            command,
            returncode=127,
            stdout="",
            stderr=str(error),
        )


def _failure_for(result: subprocess.CompletedProcess[str]) -> GitCommandFailure:
    return GitCommandFailure(
        command=[str(part) for part in result.args],
        returncode=result.returncode,
        stderr=result.stderr.strip(),
    )


def _parse_porcelain_status(output: str) -> dict[str, list[str]]:
    tracked_dirty_files: list[str] = []
    untracked_files: list[str] = []
    seen_tracked: set[str] = set()
    seen_untracked: set[str] = set()
    records = output.split("\x00")
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if len(record) < 4:
            continue

        status = record[:2]
        path = _normalize_path(record[3:])
        if status[0] in {"R", "C"} or status[1] in {"R", "C"}:
            index += 1
        if not path:
            continue

        if status == "??":
            _append_unique(untracked_files, seen_untracked, path)
        else:
            _append_unique(tracked_dirty_files, seen_tracked, path)

    return {
        "tracked_dirty_files": tracked_dirty_files,
        "untracked_files": untracked_files,
    }


def _classify_dirty_files(dirty_files: list[str]) -> dict[str, Any]:
    matches: list[dict[str, str]] = []
    unknown: list[str] = []
    coding_dirty = False
    map_dirty = False
    package_config_env_dirty = False
    source_proxy_runtime_dirty = False

    for path in dirty_files:
        categories = _categories_for(path)
        if not categories:
            unknown.append(path)
            continue

        for category in categories:
            matches.append({"path": path, "lane": category})
            if category == "coding":
                coding_dirty = True
            elif category == "map":
                map_dirty = True
            elif category == "package_config_env":
                package_config_env_dirty = True
            elif category == "source_proxy_runtime":
                source_proxy_runtime_dirty = True

    return {
        "protected_lane_matches": matches,
        "coding_files_dirty": coding_dirty,
        "map_files_dirty": map_dirty,
        "package_config_env_files_dirty": package_config_env_dirty,
        "source_proxy_runtime_files_dirty": source_proxy_runtime_dirty,
        "unknown_unclassified_dirty_files": unknown,
    }


def _categories_for(path: str) -> list[str]:
    categories: list[str] = []
    if _has_prefix(path, _CODING_PREFIXES):
        categories.append("coding")
    if _has_prefix(path, _MAP_PREFIXES):
        categories.append("map")
    if path in _PACKAGE_CONFIG_ENV_FILES or path.startswith(".env"):
        categories.append("package_config_env")
    if _has_prefix(path, _PACKAGE_CONFIG_ENV_PREFIXES):
        categories.append("package_config_env")
    if _is_source_proxy_runtime(path):
        categories.append("source_proxy_runtime")
    return categories


def _recommend_safety_state(
    classification: dict[str, Any],
    dirty_files: list[str],
) -> dict[str, Any]:
    blocker_reasons: list[str] = []
    if classification["coding_files_dirty"]:
        blocker_reasons.append("/coding files are dirty")
    if classification["package_config_env_files_dirty"]:
        blocker_reasons.append("package, config, or env files are dirty")
    if classification["source_proxy_runtime_files_dirty"]:
        blocker_reasons.append("source_proxy runtime files are dirty")

    if blocker_reasons:
        return {"state": "blocked", "blocker_reasons": blocker_reasons}

    if dirty_files:
        return {"state": "caution", "blocker_reasons": []}

    return {"state": "clear", "blocker_reasons": []}


def _is_source_proxy_runtime(path: str) -> bool:
    if not _has_prefix(path, _SOURCE_PROXY_RUNTIME_PREFIXES):
        return False
    return not _has_prefix(path, _SOURCE_PROXY_RUNTIME_EXCLUDED_PREFIXES)


def _has_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path.startswith(prefix) for prefix in prefixes)


def _normalize_path(path: str) -> str:
    return path.strip().replace("\\", "/")


def _append_unique(values: list[str], seen: set[str], value: str) -> None:
    if value not in seen:
        seen.add(value)
        values.append(value)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _no_mutation_guarantee() -> dict[str, Any]:
    return {
        "mutates_files": False,
        "stages_files": False,
        "commits": False,
        "pushes": False,
        "creates_branches": False,
        "creates_worktrees": False,
        "stashes": False,
        "cleans": False,
        "resets": False,
        "checkouts": False,
        "runs_package_installs": False,
        "executes_arbitrary_shell_strings": False,
        "git_commands": [
            ["git", "branch", "--show-current"],
            ["git", "rev-parse", "HEAD"],
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        ],
    }
