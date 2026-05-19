from __future__ import annotations

import os


def docs_autopilot_config() -> dict[str, object]:
    requested = _env_bool("CARTOGRAPHER_DOCS_AUTOPILOT_ENABLED", default=False)
    daily_cap = _env_int("CARTOGRAPHER_DOCS_AUTOPILOT_DAILY_CAP", default=0)
    kill_switch = _env_bool("CARTOGRAPHER_AUTOPILOT_KILL_SWITCH", default=True)
    enabled = requested and daily_cap > 0 and not kill_switch
    return {
        "docs_autopilot_enabled": enabled,
        "docs_autopilot_requested": requested,
        "docs_autopilot_daily_cap": daily_cap,
        "autopilot_kill_switch": kill_switch,
        "autopilot_action_available": False,
        "autopilot_mode": "disabled" if not enabled else "configured_but_actions_unavailable",
        "write_actions_enabled": False,
        "actions_taken": False,
        "allowed_paths": [
            "docs/**",
            "scout/docs/**",
            "source_proxy/cartographer/soak-logs/**",
            "_blueprints/**/*.md",
        ],
        "forbidden_paths": [
            "source_proxy/approval/**",
            "source_proxy/safety/**",
            "source_proxy/cartographer/git_approvals.py",
            "source_proxy/cartographer/push_queue.py",
            "source_proxy/cartographer/apply.py",
            ".env*",
            "docker-compose*",
            "package-lock.json",
            "auth/**",
            "src/**",
            "app/**",
            "scout/activation/**",
        ],
    }


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, *, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return max(0, int(raw.strip()))
    except ValueError:
        return default
