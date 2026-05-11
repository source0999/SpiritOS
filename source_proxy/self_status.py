from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from source_proxy.routing.litellm_router import routing_status


def build_self_status_manifest(project_root: Path | None = None) -> dict[str, Any]:
    root = (project_root or Path.cwd()).resolve()
    routes = routing_status()
    tools_manifest = build_tools_manifest(routes)

    return {
        "service": "source-proxy",
        "manifest_version": "2.7A-1",
        "access_scope": (
            "read_only_status_manifest_only; this response does not imply "
            "full-machine filesystem access"
        ),
        "configured_roots": _configured_roots(root),
        "windows_bridge_status": _windows_bridge_status(),
        "enabled_tools": tools_manifest["enabled_tools"],
        "disabled_tools": tools_manifest["disabled_tools"],
        "approval_boundaries": tools_manifest["approval_boundaries"],
        "available_routes": tools_manifest["available_routes"],
        "context_bundle_status": _context_bundle_status(root),
        "repo_metadata": _repo_metadata(root),
    }


def build_tools_manifest(
    routes: list[dict[str, str | bool | None]] | None = None,
) -> dict[str, Any]:
    route_status = routes if routes is not None else routing_status()
    return {
        "service": "source-proxy",
        "manifest_version": "2.7A-2",
        "access_scope": (
            "read_only_tools_manifest_only; this response describes configured "
            "capabilities and approval gates, not permission to execute them"
        ),
        "enabled_tools": _enabled_tools(route_status),
        "disabled_tools": _disabled_tools(),
        "approval_boundaries": _approval_boundaries(),
        "available_routes": _available_routes(route_status),
        "tool_manifest_notes": [
            "Unavailable tools are listed explicitly instead of omitted.",
            "Paid API routes remain gated by spend-before-send approval.",
            "Filesystem and terminal implementation tools are not granted here.",
        ],
    }


def build_context_index_manifest(project_root: Path | None = None) -> dict[str, Any]:
    root = (project_root or Path.cwd()).resolve()
    return {
        "service": "source-proxy",
        "manifest_version": "2.7A-3",
        "access_scope": (
            "read_only_context_index_only; this response reports context artifact "
            "presence and policy without reading file contents"
        ),
        "configured_roots": _configured_roots(root),
        "context_bundle_status": _context_bundle_status(root),
        "repo_metadata": _repo_metadata(root),
        "context_inclusion_policy": {
            "contents_included": False,
            "recursive_expansion": False,
            "windows_folder_listing": False,
            "secret_redaction_applied": False,
            "allowed_now": [
                "report generated context bundle presence",
                "report configured root candidates",
                "report limited repo metadata presence",
            ],
            "blocked_here": [
                "read bundle contents",
                "read source file contents",
                "expand Windows allowlisted folders",
                "include .env, certificates, private keys, or token files",
            ],
        },
        "next_context_selection_action": (
            "Ask the user which verified root or generated bundle should be used "
            "before building a prompt packet or reading excerpts."
        ),
    }


def build_action_preview(
    action: str,
    target: str | None = None,
    route_type: str | None = None,
) -> dict[str, Any]:
    normalized_action = action.strip().lower()
    normalized_target = (target or "").strip()
    normalized_route = (route_type or "").strip().lower()
    decision, reason_codes = _classify_preview_action(
        normalized_action,
        normalized_target,
        normalized_route,
    )

    return {
        "service": "source-proxy",
        "manifest_version": "2.7A-4",
        "access_scope": (
            "read_only_action_preview_only; this response classifies the requested "
            "action but never executes it"
        ),
        "requested_action": action,
        "target": normalized_target or None,
        "route_type": normalized_route or None,
        "decision": decision,
        "reason_codes": reason_codes,
        "would_execute": False,
        "requires_human_approval": decision == "requires_human_approval",
        "approval_boundaries": _approval_boundaries(),
        "safety_message": _preview_safety_message(reason_codes),
        "next_step": _preview_next_step(decision),
    }


def _configured_roots(root: Path) -> list[dict[str, Any]]:
    roots: list[dict[str, Any]] = [
        {
            "name": "source_proxy_workspace",
            "source": "process_cwd",
            "path": str(root),
            "status": "configured",
            "access": "read_only_status",
            "notes": (
                "Runtime workspace root used for status checks only; no recursive "
                "file inventory is implied."
            ),
        }
    ]

    for env_name in ("SPIRIT_PROJECT_PATH", "SOURCE_PROXY_PROJECT_ROOTS"):
        for value in _split_env_paths(os.getenv(env_name, "")):
            roots.append(
                {
                    "name": env_name.lower(),
                    "source": env_name,
                    "path": value,
                    "status": "configured",
                    "access": "read_only_candidate",
                    "notes": (
                        "Configured root candidate only; file contents are not "
                        "read by this manifest."
                    ),
                }
            )

    return roots


def _windows_bridge_status() -> dict[str, Any]:
    spirit_enabled = _env_true("SPIRIT_WINDOWS_FS_ENABLED")
    desktop_enabled = _env_true("SPIRIT_DESKTOP_FS_ENABLED")
    allowlisted_roots = _split_env_paths(
        os.getenv("SPIRIT_WINDOWS_FS_ALLOWLIST", "")
        or os.getenv("SPIRIT_DESKTOP_FS_ALLOWLIST", "")
    )
    base_url_present = bool(os.getenv("SPIRIT_WINDOWS_FS_BASE_URL", "").strip())
    token_present = bool(
        os.getenv("SPIRIT_WINDOWS_FS_TOKEN", "").strip()
        or os.getenv("SPIRIT_DESKTOP_TOKEN", "").strip()
        or os.getenv("SPIRIT_AGENT_TOKEN", "").strip()
    )

    enabled = spirit_enabled or desktop_enabled
    if not enabled:
        status = "disabled"
    elif allowlisted_roots and (base_url_present or desktop_enabled) and token_present:
        status = "configured_not_probed"
    else:
        status = "misconfigured"

    return {
        "status": status,
        "enabled": enabled,
        "base_url_present": base_url_present,
        "token_present": token_present,
        "allowlisted_roots": allowlisted_roots,
        "capability": "read_only_listing_when_configured",
        "notes": (
            "Status is derived from environment configuration only; this endpoint "
            "does not contact the Windows bridge."
        ),
    }


def _enabled_tools(routes: list[dict[str, str | bool | None]]) -> list[dict[str, Any]]:
    tools: list[dict[str, Any]] = [
        {
            "name": "route_decision",
            "category": "decision",
            "access": "read_only",
            "endpoint": "POST /v1/decisions/route",
        },
        {
            "name": "prompt_packet_generator",
            "category": "manual_route",
            "access": "read_only",
            "endpoint": "POST /v1/decisions/prompt-packet",
        },
        {
            "name": "manual_model_recommendation",
            "category": "manual_route",
            "access": "read_only",
            "endpoint": "POST /v1/decisions/recommend-model",
        },
        {
            "name": "api_vs_manual_preview",
            "category": "approval_preview",
            "access": "read_only",
            "endpoint": "POST /v1/decisions/api-vs-manual-preview",
        },
        {
            "name": "coding_proxy_test_surface",
            "category": "testing_surface",
            "access": "browser_ui_only",
            "endpoint": "GET /coding",
            "notes": (
                "Next.js /coding page exercises route decisions, research preview, "
                "prompt packets, and path choices without touching /chat."
            ),
            "feature_flag": "SPIRIT_CODING_USE_PROXY",
            "proxy_endpoints_used": [
                "POST /v1/decisions/route",
                "POST /v1/decisions/prompt-packet",
            ],
        },
        {
            "name": "healthcheck",
            "category": "diagnostics",
            "access": "read_only",
            "endpoint": "GET /healthcheck",
        },
    ]

    if _env_true("SPIRIT_ENABLE_PROXY_RESEARCH"):
        tools.append(
            {
                "name": "research_preview",
                "category": "research",
                "access": "read_only_local_search_preview",
                "endpoint": "POST /v1/decisions/route or POST /v1/decisions/prompt-packet",
                "provider": "searxng",
                "feature_flag": "SPIRIT_ENABLE_PROXY_RESEARCH",
                "output_contract": "title_url_snippet_sources_only",
            }
        )

    if any(route.get("alias") == "local" and route.get("enabled") for route in routes):
        tools.append(
            {
                "name": "local_chat_route",
                "category": "local_route",
                "access": "generation_after_request",
                "endpoint": "POST /v1/chat/completions",
            }
        )

    paid_aliases = [
        str(route["alias"])
        for route in routes
        if route.get("enabled") and route.get("provider") != "ollama"
    ]
    if paid_aliases:
        tools.append(
            {
                "name": "paid_api_chat_routes",
                "category": "paid_api_route",
                "access": "gated_by_spend_approval",
                "enabled_aliases": paid_aliases,
                "endpoint": "POST /v1/chat/completions",
            }
        )

    return tools


def _disabled_tools() -> list[dict[str, str]]:
    disabled = [
        {
            "name": "file_editing",
            "category": "implementation",
            "reason": "2.7A-1 exposes status manifest only; edit actions are not implemented.",
        },
        {
            "name": "terminal_execution",
            "category": "implementation",
            "reason": "Terminal actions are outside this endpoint and require a separate gate.",
        },
        {
            "name": "full_drive_browsing",
            "category": "filesystem",
            "reason": "Only configured roots and allowlists may be reported.",
        },
    ]
    if not _env_true("SPIRIT_ENABLE_PROXY_RESEARCH"):
        disabled.append(
            {
                "name": "research_preview",
                "category": "research",
                "reason": (
                    "SPIRIT_ENABLE_PROXY_RESEARCH is not true; route decisions may "
                    "recommend research but sources are not fetched."
                ),
            }
        )
    if not (_env_true("SPIRIT_WINDOWS_FS_ENABLED") or _env_true("SPIRIT_DESKTOP_FS_ENABLED")):
        disabled.append(
            {
                "name": "windows_folder_listing",
                "category": "filesystem",
                "reason": "Windows bridge filesystem access is disabled in environment.",
            }
        )
    return disabled


def _approval_boundaries() -> dict[str, list[str]]:
    return {
        "always_blocked_here": [
            "arbitrary full-drive browsing",
            "file write/edit/delete actions",
            "ungated terminal execution",
            "secret or credential disclosure",
        ],
        "requires_human_approval": [
            "paid API provider requests with projected spend",
            "implementation actions beyond read-only preview/status",
        ],
        "allowed_without_spend": [
            "self status manifest",
            "manual route recommendation",
            "prompt packet generation",
            "local route recommendation",
        ],
    }


def _available_routes(routes: list[dict[str, str | bool | None]]) -> list[dict[str, Any]]:
    available: list[dict[str, Any]] = [
        {
            "route_type": "manual_route",
            "status": "available",
            "approval": "user_pastes_packet_externally",
            "spend": "none_from_source_proxy",
        },
        {
            "route_type": "local_route",
            "status": "available"
            if any(route.get("alias") == "local" and route.get("enabled") for route in routes)
            else "unavailable",
            "approval": "request_required",
            "spend": "local_compute_only",
        },
    ]

    paid_enabled = [
        route for route in routes if route.get("enabled") and route.get("provider") != "ollama"
    ]
    available.append(
        {
            "route_type": "api_route",
            "status": "available" if paid_enabled else "unavailable",
            "approval": "spend_before_send_required",
            "spend": "paid_provider_possible",
            "enabled_aliases": [route["alias"] for route in paid_enabled],
        }
    )
    return available


def _context_bundle_status(root: Path) -> dict[str, Any]:
    bundle_names = ["repomix-output.ast.xml", "repomix-output.xml"]
    bundles = []
    for name in bundle_names:
        path = root / name
        exists = path.exists()
        bundles.append(
            {
                "name": name,
                "status": "present" if exists else "missing",
                "path": str(path),
                "size_bytes": path.stat().st_size if exists else None,
                "content_included": False,
            }
        )

    return {
        "bundles": bundles,
        "content_included": False,
        "notes": "Only bundle presence is reported; bundle contents are not read here.",
    }


def _repo_metadata(root: Path) -> dict[str, Any]:
    return {
        "root": str(root),
        "git_directory_present": (root / ".git").exists(),
        "git_status_included": False,
        "notes": "Repo metadata is limited to safe presence checks in 2.7A-1.",
    }


def _classify_preview_action(
    action: str,
    target: str,
    route_type: str,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    combined = f"{action}\n{target}\n{route_type}"

    if not action:
        return "blocked", ["empty_action"]

    if _contains_any(
        combined,
        [
            "delete",
            "remove",
            "overwrite",
            "write",
            "edit",
            "patch",
            "commit",
            "push",
            "terminal",
            "shell",
            "exec",
            "run command",
        ],
    ):
        reasons.append("implementation_or_terminal_action")

    if _contains_any(
        combined,
        [
            "c:\\",
            "full drive",
            "entire drive",
            "/home",
            "/etc",
            "/root",
            "all files",
        ],
    ):
        reasons.append("broad_filesystem_scope")

    if _contains_any(
        combined,
        [
            ".env",
            "secret",
            "password",
            "token",
            "api_key",
            "private key",
            "certificate",
        ],
    ):
        reasons.append("possible_secret_or_credential_scope")

    if route_type == "api_route" or _contains_any(combined, ["paid", "openai", "anthropic", "deepseek"]):
        reasons.append("paid_api_route_possible")

    if _contains_any(combined, ["research", "search", "web", "source", "sources", "latest", "current"]):
        reasons.append("research_preview_requested")

    if "broad_filesystem_scope" in reasons or "possible_secret_or_credential_scope" in reasons:
        return "blocked", reasons

    if "implementation_or_terminal_action" in reasons or "paid_api_route_possible" in reasons:
        return "requires_human_approval", reasons

    return "preview_only", reasons or ["read_only_preview"]


def _preview_next_step(decision: str) -> str:
    if decision == "blocked":
        return "Do not execute; narrow the request to an allowlisted read-only scope."
    if decision == "requires_human_approval":
        return "Show the relevant approval or spend preview before any execution."
    return "Safe to continue with read-only planning or manifest inspection only."


def _preview_safety_message(reason_codes: list[str]) -> str:
    if "research_preview_requested" in reason_codes:
        return (
            "Research preview is read-only and may return only verified source metadata "
            "such as title, URL, and snippet when the feature flag is enabled."
        )
    return "This preview classifies the action only and does not execute it."


def _contains_any(value: str, needles: list[str]) -> bool:
    return any(needle in value for needle in needles)


def _split_env_paths(value: str) -> list[str]:
    return [part.strip() for part in value.replace("\n", ",").split(",") if part.strip()]


def _env_true(name: str) -> bool:
    return os.getenv(name, "").strip().lower() == "true"
