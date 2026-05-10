from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def build_safe_context_inventory(project_root: Path | None = None) -> dict[str, Any]:
    root = (project_root or Path.cwd()).resolve()
    local_roots = _local_context_roots(root)
    windows_roots = _windows_context_roots()
    bundle_sources = _context_bundle_sources(root)

    return {
        "service": "source-proxy",
        "inventory_version": "2.8-1",
        "access_scope": (
            "read_only_context_source_inventory; this response lists candidate "
            "sources without reading file contents or expanding directories"
        ),
        "verified_context_roots": [
            *[item for item in local_roots if item["status"] == "verified"],
            *[item for item in windows_roots if item["status"] == "verified"],
        ],
        "unavailable_roots": [
            *[item for item in local_roots if item["status"] != "verified"],
            *[item for item in windows_roots if item["status"] != "verified"],
        ],
        "blocked_paths_policy": _blocked_paths_policy(),
        "available_read_only_sources": [
            *bundle_sources,
            *[source for source in _root_sources(local_roots + windows_roots)],
        ],
        "inventory_limits": {
            "file_contents_included": False,
            "directory_entries_included": False,
            "recursive_expansion": False,
            "hidden_files_included": False,
            "windows_bridge_probed": False,
            "max_default_entries": 0,
        },
        "next_context_selection_action": (
            "Ask the user to choose a verified root or generated bundle before "
            "listing paths or including excerpts in a prompt packet."
        ),
    }


def _local_context_roots(root: Path) -> list[dict[str, Any]]:
    candidates: list[tuple[str, str, str]] = [
        ("source_proxy_workspace", "process_cwd", str(root)),
    ]
    for env_name in ("SPIRIT_PROJECT_PATH", "SOURCE_PROXY_PROJECT_ROOTS"):
        for value in _split_env_paths(os.getenv(env_name, "")):
            candidates.append((env_name.lower(), env_name, value))

    roots: list[dict[str, Any]] = []
    seen: set[str] = set()
    for name, source, raw_path in candidates:
        if raw_path in seen:
            continue
        seen.add(raw_path)
        path = Path(raw_path).expanduser()
        exists = path.exists()
        roots.append(
            {
                "name": name,
                "source": source,
                "path": str(path.resolve()) if exists else raw_path,
                "status": "verified" if exists else "unavailable",
                "kind": "local_project_root",
                "access": "read_only_candidate",
                "contents_included": False,
                "directory_entries_included": False,
                "notes": (
                    "Root existence only; no recursive listing or file content read."
                    if exists
                    else "Configured path does not exist on this host."
                ),
            }
        )
    return roots


def _windows_context_roots() -> list[dict[str, Any]]:
    enabled = _env_true("SPIRIT_WINDOWS_FS_ENABLED") or _env_true("SPIRIT_DESKTOP_FS_ENABLED")
    allowlist = _split_env_paths(
        os.getenv("SPIRIT_WINDOWS_FS_ALLOWLIST", "")
        or os.getenv("SPIRIT_DESKTOP_FS_ALLOWLIST", "")
    )
    base_url_present = bool(os.getenv("SPIRIT_WINDOWS_FS_BASE_URL", "").strip())
    token_present = bool(
        os.getenv("SPIRIT_WINDOWS_FS_TOKEN", "").strip()
        or os.getenv("SPIRIT_DESKTOP_TOKEN", "").strip()
        or os.getenv("SPIRIT_AGENT_TOKEN", "").strip()
    )

    if not allowlist:
        return [
            {
                "name": "windows_bridge_allowlist",
                "source": "SPIRIT_WINDOWS_FS_ALLOWLIST",
                "path": None,
                "status": "unavailable",
                "kind": "windows_bridge_allowlist",
                "access": "read_only_listing_candidate",
                "contents_included": False,
                "directory_entries_included": False,
                "notes": "No Windows allowlist is configured.",
            }
        ]

    status = (
        "verified"
        if enabled and token_present and (base_url_present or _env_true("SPIRIT_DESKTOP_FS_ENABLED"))
        else "unavailable"
    )
    notes = (
        "Allowlisted Windows root candidate only; bridge is not probed by inventory."
        if status == "verified"
        else "Windows bridge is disabled or missing URL/token configuration."
    )

    return [
        {
            "name": "windows_bridge_allowlist",
            "source": "SPIRIT_WINDOWS_FS_ALLOWLIST",
            "path": value,
            "status": status,
            "kind": "windows_bridge_allowlist",
            "access": "read_only_listing_candidate",
            "contents_included": False,
            "directory_entries_included": False,
            "notes": notes,
        }
        for value in allowlist
    ]


def _context_bundle_sources(root: Path) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for name in ("repomix-output.ast.xml", "repomix-output.xml"):
        path = root / name
        exists = path.exists()
        sources.append(
            {
                "name": name,
                "kind": "generated_context_bundle",
                "path": str(path),
                "status": "available" if exists else "missing",
                "size_bytes": path.stat().st_size if exists else None,
                "contents_included": False,
                "notes": "Bundle presence only; contents are not read by inventory.",
            }
        )
    return sources


def _root_sources(roots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "name": root["name"],
            "kind": root["kind"],
            "path": root["path"],
            "status": "available",
            "contents_included": False,
            "directory_entries_included": False,
            "notes": "Root can be selected for a later read-only listing or excerpt step.",
        }
        for root in roots
        if root["status"] == "verified"
    ]


def _blocked_paths_policy() -> dict[str, Any]:
    return {
        "no_arbitrary_drive_browsing": True,
        "no_recursive_expansion_by_default": True,
        "no_hidden_files": True,
        "no_file_contents_yet": True,
        "blocked_name_patterns": [
            ".env",
            "*.pem",
            "*.key",
            "*secret*",
            "*token*",
            "*credential*",
            "id_rsa",
            "id_ed25519",
        ],
        "blocked_path_prefixes": [
            "C:\\Windows",
            "C:\\Users",
            "/etc",
            "/root",
            "/home",
        ],
        "notes": (
            "Allowlisted child paths may be selectable later, but broad system roots "
            "and secret-shaped files stay blocked."
        ),
    }


def _split_env_paths(value: str) -> list[str]:
    return [part.strip() for part in value.replace("\n", ",").split(",") if part.strip()]


def _env_true(name: str) -> bool:
    return os.getenv(name, "").strip().lower() == "true"
