# Increment 4.2 - Source Proxy health/status

Date: 2026-05-29T20:00:25-04:00

```text
{
    "vram_used": "10 GB",
    "vram_total": "12 GB",
    "budget_remaining": "$3.50"
}
{
    "service": "source-proxy",
    "manifest_version": "2.7A-1",
    "access_scope": "read_only_status_manifest_only; this response does not imply full-machine filesystem access",
    "configured_roots": [
        {
            "name": "source_proxy_workspace",
            "source": "process_cwd",
            "path": "/home/source/SpiritOS",
            "status": "configured",
            "access": "read_only_status",
            "notes": "Runtime workspace root used for status checks only; no recursive file inventory is implied."
        }
    ],
    "windows_bridge_status": {
        "status": "disabled",
        "enabled": false,
        "base_url_present": false,
        "token_present": false,
        "allowlisted_roots": [],
        "capability": "read_only_listing_when_configured",
        "notes": "Status is derived from environment configuration only; this endpoint does not contact the Windows bridge."
    },
    "enabled_tools": [
        {
            "name": "route_decision",
            "category": "decision",
            "access": "read_only",
            "endpoint": "POST /v1/decisions/route"
        },
        {
            "name": "prompt_packet_generator",
            "category": "manual_route",
            "access": "read_only",
            "endpoint": "POST /v1/decisions/prompt-packet"
        },
        {
            "name": "manual_model_recommendation",
            "category": "manual_route",
            "access": "read_only",
            "endpoint": "POST /v1/decisions/recommend-model"
        },
        {
            "name": "api_vs_manual_preview",
            "category": "approval_preview",
            "access": "read_only",
            "endpoint": "POST /v1/decisions/api-vs-manual-preview"
        },
        {
            "name": "coding_proxy_test_surface",
            "category": "testing_surface",
            "access": "browser_ui_only",
            "endpoint": "GET /coding",
            "notes": "Next.js /coding page exercises route decisions, research preview, prompt packets, and path choices without touching /chat.",
            "feature_flag": "SPIRIT_CODING_USE_PROXY",
            "proxy_endpoints_used": [
                "POST /v1/decisions/route",
                "POST /v1/decisions/prompt-packet"
            ]
        },
        {
            "name": "healthcheck",
            "category": "diagnostics",
            "access": "read_only",
            "endpoint": "GET /healthcheck"
        },
        {
            "name": "workspace_read_only_tools",
            "category": "workspace_context",
            "access": "read_only_allowlisted_workspace",
            "endpoints": [
                "POST /v1/workspace/list",
                "POST /v1/workspace/read"
            ],
            "limits": {
                "writes_allowed": false,
                "recursive_listing": false,
                "hidden_files": false,
                "secret_shaped_paths": false
            }
        },
        {
            "name": "sandboxed_terminal_run",
            "category": "sandbox",
            "access": "bubblewrap_sandboxed_terminal",
            "endpoint": "POST /v1/sandbox/terminal/run",
            "limits": {
                "workspace_mount": "/workspace",
                "workspace_writable": false,
                "network_default": "none",
                "max_timeout_seconds": 30,
                "home_hidden": true
            }
        },
        {
            "name": "diff_verification_preview",
            "category": "verification",
            "access": "read_only_diff_preview",
            "endpoint": "POST /v1/verification/diff-preview",
            "limits": {
                "would_apply_diff": false,
                "would_execute": false,
                "secret_shaped_paths": false,
                "max_diff_bytes": 200000
            }
        },
        {
            "name": "long_running_task_tracker",
            "category": "task_tracking",
            "access": "read_only_status_tracking",
            "endpoints": [
                "POST /v1/tasks/long-running",
                "GET /v1/tasks/long-running/{task_id}",
                "POST /v1/tasks/long-running/{task_id}/cancel"
            ],
            "limits": {
                "executes_commands": false,
                "writes_files": false,
                "persists_across_restart": false
            }
        },
        {
            "name": "local_chat_route",
            "category": "local_route",
            "access": "generation_after_request",
            "endpoint": "POST /v1/chat/completions"
        }
    ],
    "disabled_tools": [
        {
            "name": "file_editing",
            "category": "implementation",
            "reason": "2.7A-1 exposes status manifest only; edit actions are not implemented."
        },
        {
            "name": "terminal_execution",
            "category": "implementation",
            "reason": "Terminal actions are outside this endpoint and require a separate gate."
        },
        {
            "name": "full_drive_browsing",
            "category": "filesystem",
            "reason": "Only configured roots and allowlists may be reported."
        },
        {
            "name": "research_preview",
            "category": "research",
            "reason": "SPIRIT_ENABLE_PROXY_RESEARCH is not true; route decisions may recommend research but sources are not fetched."
        },
        {
            "name": "windows_folder_listing",
            "category": "filesystem",
            "reason": "Windows bridge filesystem access is disabled in environment."
        }
    ],
    "approval_boundaries": {
        "always_blocked_here": [
            "arbitrary full-drive browsing",
            "file write/edit/delete actions",
            "ungated terminal execution",
            "secret or credential disclosure"
        ],
        "requires_human_approval": [
            "paid API provider requests with projected spend",
            "implementation actions beyond read-only preview/status"
        ],
        "allowed_without_spend": [
            "self status manifest",
            "manual route recommendation",
            "prompt packet generation",
            "local route recommendation"
        ]
    },
    "available_routes": [
        {
            "route_type": "manual_route",
            "next_prompt_action": "generate_manual_prompt_packet",
            "display_name": "Manual prompt packet",
            "execution_path": "manual_prompt_packet",
            "status": "available",
            "approval": "user_pastes_packet_externally",
            "spend": "none_from_source_proxy"
        },
        {
            "route_type": "local_route",
            "next_prompt_action": "run_with_coder_agent",
            "display_name": "Coder Agent",
            "execution_path": "coder_agent",
            "status": "available",
            "approval": "request_required",
            "spend": "local_compute_only"
        },
        {
            "route_type": "api_route",
            "next_prompt_action": "call_api_model",
            "display_name": "Cloud/API route",
            "execution_path": "paid_api_chat_route",
            "status": "unavailable",
            "approval": "spend_before_send_required",
            "spend": "paid_provider_possible",
            "enabled_aliases": []
        }
    ],
    "model_routes": [
        {
            "alias": "local",
            "provider": "ollama",
            "model": "ollama_chat/hermes4:latest",
            "enabled": true,
            "reason": null,
            "source": "config",
            "api_base_host": "127.0.0.1:11434",
            "configured_ollama_model": "hermes4:latest",
            "probe_ok": true,
            "selected_via": "probe:fallback_default+available_hermes"
        },
        {
            "alias": "openai",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "enabled": false,
            "reason": "OPENAI_API_KEY is not set",
            "source": "config"
        },
        {
            "alias": "anthropic",
            "provider": "anthropic",
            "model": "anthropic/claude-3-7-sonnet-20250219",
            "enabled": false,
            "reason": "ANTHROPIC_API_KEY is not set",
            "source": "config"
        },
        {
            "alias": "deepseek",
            "provider": "deepseek",
            "model": "deepseek/deepseek-chat",
            "enabled": false,
            "reason": "DEEPSEEK_API_KEY is not set",
            "source": "config"
        }
    ],
    "provider_capabilities": {
        "codex_cli": {
            "provider_id": "codex_cli",
            "display_name": "Codex CLI",
            "status": "available",
            "capabilities": [
                "planning",
                "review",
                "diff_drafting"
            ],
            "missing_reason": null,
            "recommendation_only": true,
            "approval_authority": false,
            "apply_authority": false,
            "commit_authority": false,
            "push_authority": false,
            "notes": "Experimental worker for readonly/proposal evidence only; Source Proxy gates remain final."
        },
        "local_ollama": {
            "provider_id": "local_ollama",
            "display_name": "Local Ollama",
            "status": "config_blocked",
            "capabilities": [
                "planning",
                "review"
            ],
            "missing_reason": "not_probed_in_phase_9_1",
            "recommendation_only": true,
            "approval_authority": false,
            "apply_authority": false,
            "commit_authority": false,
            "push_authority": false,
            "notes": "May be studied for local planning/review later; no file or tool authority is assumed."
        },
        "gemini_cli": {
            "provider_id": "gemini_cli",
            "display_name": "Gemini CLI",
            "status": "future_optional",
            "capabilities": [
                "planning",
                "review",
                "current_research"
            ],
            "missing_reason": "not_configured",
            "recommendation_only": true,
            "approval_authority": false,
            "apply_authority": false,
            "commit_authority": false,
            "push_authority": false,
            "notes": "Future optional reference only; no routing authority is enabled."
        },
        "api_adapter": {
            "provider_id": "api_adapter",
            "display_name": "Optional API Adapter",
            "status": "future_optional",
            "capabilities": [
                "planning",
                "review"
            ],
            "missing_reason": "not_configured",
            "recommendation_only": true,
            "approval_authority": false,
            "apply_authority": false,
            "commit_authority": false,
            "push_authority": false,
            "notes": "Paid or external API routes require separate spend and action approval before any use."
        }
    },
    "codex_cli_status": {
        "tool": "codex_cli",
        "status": "detected",
        "installed": true,
        "binary": "codex",
        "binary_path": "/home/source/.local/bin/codex",
        "version": "0.130.0",
        "raw_version": "codex-cli 0.130.0",
        "auth_status": "not_probed",
        "safe_features": {
            "exec": true,
            "json_events": true,
            "output_last_message": true,
            "output_schema": true,
            "profile": true,
            "sandbox_read_only": true,
            "sandbox_workspace_write": true
        },
        "safe_sandboxes": [
            "read-only",
            "workspace-write"
        ],
        "blocked_sandboxes": [
            "danger-full-access"
        ],
        "blocked_flags": [
            "--dangerously-bypass-approvals-and-sandbox",
            "--yolo"
        ],
        "can_run_live_task": false,
        "would_run_task": false,
        "approval_authority": false,
        "apply_authority": false,
        "commit_authority": false,
        "push_authority": false,
        "notes": [
            "Capability probe only; no Codex task is executed.",
            "Missing Codex CLI is config_blocked, not a Source Proxy failure."
        ],
        "version_returncode": 0
    },
    "context_bundle_status": {
        "bundles": [
            {
                "name": "repomix-output.ast.xml",
                "status": "present",
                "path": "/home/source/SpiritOS/repomix-output.ast.xml",
                "size_bytes": 722235,
                "content_included": false
            },
            {
                "name": "repomix-output.xml",
                "status": "present",
                "path": "/home/source/SpiritOS/repomix-output.xml",
                "size_bytes": 14656173,
                "content_included": false
            }
        ],
        "content_included": false,
        "notes": "Only bundle presence is reported; bundle contents are not read here."
    },
    "repo_metadata": {
        "root": "/home/source/SpiritOS",
        "git_directory_present": true,
        "git_status_included": false,
        "notes": "Repo metadata is limited to safe presence checks in 2.7A-1."
    }
}
{
    "object": "list",
    "data": [
        {
            "alias": "local",
            "provider": "ollama",
            "model": "ollama_chat/hermes4:latest",
            "enabled": true,
            "reason": null
        },
        {
            "alias": "openai",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "enabled": false,
            "reason": "OPENAI_API_KEY is not set"
        },
        {
            "alias": "anthropic",
            "provider": "anthropic",
            "model": "anthropic/claude-3-7-sonnet-20250219",
            "enabled": false,
            "reason": "ANTHROPIC_API_KEY is not set"
        },
        {
            "alias": "deepseek",
            "provider": "deepseek",
            "model": "deepseek/deepseek-chat",
            "enabled": false,
            "reason": "DEEPSEEK_API_KEY is not set"
        }
    ]
}
/tmp/source-proxy-hermes4-self-status.json:            "provider": "ollama",
/tmp/source-proxy-hermes4-self-status.json:            "model": "ollama_chat/hermes4:latest",
/tmp/source-proxy-hermes4-self-status.json:            "configured_ollama_model": "hermes4:latest",
/tmp/source-proxy-hermes4-self-status.json:            "probe_ok": true,
/tmp/source-proxy-hermes4-self-status.json:            "selected_via": "probe:fallback_default+available_hermes"
/tmp/source-proxy-hermes4-self-status.json:        "local_ollama": {
/tmp/source-proxy-hermes4-self-status.json:            "provider_id": "local_ollama",
/tmp/source-proxy-hermes4-self-status.json:            "display_name": "Local Ollama",
/tmp/source-proxy-hermes4-models.json:            "provider": "ollama",
/tmp/source-proxy-hermes4-models.json:            "model": "ollama_chat/hermes4:latest",
```

## Result

GO for Hermes 4 local routing; live status-refresh gap recorded.

- `https://localhost:8787/healthcheck` responded.
- `https://localhost:8787/v1/self/status` reports local Source Proxy model route as `ollama_chat/hermes4:latest`, with `probe_ok: true` and `selected_via: probe:fallback_default+available_hermes`.
- `https://localhost:8787/v1/models` includes the local route as `ollama_chat/hermes4:latest`.
- The new repo fields `requested_local_default`, `resolved_model`, and model storage proof are not visible in the live Source Proxy response yet, which indicates the running Source Proxy process has not reloaded the patched code. Restart Source Proxy only when approved.
