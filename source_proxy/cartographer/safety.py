from __future__ import annotations

from source_proxy.cartographer.autopilot_config import docs_autopilot_config, level_7_autopilot_config


WRITE_ACTIONS_ENABLED = False
WRITE_POLICY = "read_only"


def cartographer_safety_manifest() -> dict[str, object]:
    autopilot = docs_autopilot_config()
    level_7 = level_7_autopilot_config()
    return {
        "write_actions_enabled": WRITE_ACTIONS_ENABLED,
        "write_policy": WRITE_POLICY,
        "approval_required_for_file_writes": True,
        "approval_required_for_commits": True,
        "approval_required_for_pushes": True,
        "scout_bypass_allowed": False,
        "source_proxy_approval_bypass_allowed": False,
        "docs_autopilot_enabled": autopilot["docs_autopilot_enabled"],
        "docs_autopilot_daily_cap": autopilot["docs_autopilot_daily_cap"],
        "autopilot_kill_switch": autopilot["autopilot_kill_switch"],
        "autopilot_action_available": autopilot["autopilot_action_available"],
        "level_7_autopilot_enabled": level_7["level_7_autopilot_enabled"],
        "level_7_autopilot_kill_switch": level_7["level_7_autopilot_kill_switch"],
        "level_7_autopilot_action_available": level_7["level_7_autopilot_action_available"],
        "notes": (
            "Cartographer exposes read-only JSON contracts only; "
            "discovery, proposal drafting, apply, commit, and push actions are not enabled."
        ),
    }
