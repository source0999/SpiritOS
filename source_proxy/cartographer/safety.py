from __future__ import annotations


WRITE_ACTIONS_ENABLED = False
WRITE_POLICY = "read_only"


def cartographer_safety_manifest() -> dict[str, object]:
    return {
        "write_actions_enabled": WRITE_ACTIONS_ENABLED,
        "write_policy": WRITE_POLICY,
        "approval_required_for_file_writes": True,
        "approval_required_for_commits": True,
        "approval_required_for_pushes": True,
        "scout_bypass_allowed": False,
        "source_proxy_approval_bypass_allowed": False,
        "notes": (
            "Cartographer exposes read-only JSON contracts only; "
            "discovery, proposal drafting, apply, commit, and push actions are not enabled."
        ),
    }
