"""Shared target-plugin selection predicates for approval and execution."""

from __future__ import annotations

from source_proxy.target_plugins.lumacart import is_lumacart_prompt_id


GENERIC_WORKSPACE_PROMPT_ID = "generic-architect-coder-packet"
GENERIC_WORKSPACE_PLUGIN_ID = "generic-workspace"
LUMACART_PLUGIN_ID = "lumacart"


def expected_target_plugin_id(selected_prompt_id: str) -> str | None:
    prompt_id = str(selected_prompt_id or "").strip()
    if prompt_id == GENERIC_WORKSPACE_PROMPT_ID:
        return GENERIC_WORKSPACE_PLUGIN_ID
    if is_lumacart_prompt_id(prompt_id):
        return LUMACART_PLUGIN_ID
    return None


def is_target_plugin_prompt_id(selected_prompt_id: str) -> bool:
    return expected_target_plugin_id(selected_prompt_id) is not None
