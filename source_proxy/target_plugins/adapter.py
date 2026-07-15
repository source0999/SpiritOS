"""Fail-closed target-plugin identity for Campaign 1 coding execution."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import subprocess
from pathlib import Path
from typing import Any


TARGET_PLUGIN_SCHEMA_VERSION = "spiritos-target-plugin/v1"
LUMACART_PLUGIN_ID = "lumacart"
CAMPAIGN_REPOSITORY_ID = "spiritos-campaign-1"
CAMPAIGN_WORKTREE_ID = "spiritos-campaign-1-20260712"
FIXTURE_ROOT = "tests/ui-agent-trials/fixtures/dummy-product-site/"
EXECUTION_PROFILE = "coder-10"
PROMPT_CONTEXTS = {
    "coder-001-init-dummy-product-site": "init-storefront",
    "coder-002-add-product-data": "product-data",
    "coder-003-render-product-cards": "render-cards",
    "coder-004-add-search-filter": "search-filter",
    "coder-005-add-category-chips": "category-chips",
    "coder-006-add-fake-cart-count": "cart-count",
    "coder-007-mobile-styling-pass": "mobile-styling",
    "coder-008-add-tiny-tests-smoke-checks": "smoke-checks",
    "coder-009-noop-category-proof": "category-proof",
    "coder-010-protected-path-pressure-trap": "protected-path-trap",
}


class TargetPluginResolutionError(ValueError):
    """An untrusted caller tried to select or substitute a target plugin."""


@dataclass(frozen=True)
class ResolvedTargetPlugin:
    schema_version: str
    plugin_id: str
    repository_id: str
    worktree_id: str
    workspace_root: str
    fixture_root: str
    source_head: str
    selected_prompt_id: str
    selected_context_id: str
    execution_profile: str
    allowed_actions: tuple[str, ...]
    result_identity: str
    approval_id: str | None = None
    approval_generation: int | None = None
    evidence_pointer: str | None = None
    failure_reason: str | None = None
    acknowledgement_status: str = "pending"

    def evidence_identity(self) -> dict[str, Any]:
        return asdict(self)


def _require(packet: dict[str, Any], key: str) -> str:
    value = str(packet.get(key) or "").strip()
    if not value:
        raise TargetPluginResolutionError(f"target_plugin_missing_{key}")
    return value


def _git_head(workspace_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(workspace_root), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise TargetPluginResolutionError("target_plugin_source_head_unavailable") from error


def resolve_target_plugin(packet: dict[str, Any], workspace_root: Path) -> ResolvedTargetPlugin:
    """Resolve a TS-selected plugin without letting Python infer an alternate target."""
    if not isinstance(packet, dict):
        raise TargetPluginResolutionError("target_plugin_missing_packet")
    declared = packet.get("target_plugin")
    if not isinstance(declared, dict):
        raise TargetPluginResolutionError("target_plugin_missing")
    root = workspace_root.resolve()
    if _require(declared, "schema_version") != TARGET_PLUGIN_SCHEMA_VERSION:
        raise TargetPluginResolutionError("target_plugin_schema_unsupported")
    if _require(declared, "id") != LUMACART_PLUGIN_ID:
        raise TargetPluginResolutionError("target_plugin_unsupported")
    if _require(declared, "repository_id") != CAMPAIGN_REPOSITORY_ID:
        raise TargetPluginResolutionError("target_plugin_repository_mismatch")
    if _require(declared, "worktree_id") != CAMPAIGN_WORKTREE_ID:
        raise TargetPluginResolutionError("target_plugin_worktree_mismatch")
    if _require(declared, "fixture_root") != FIXTURE_ROOT:
        raise TargetPluginResolutionError("target_plugin_root_mismatch")
    prompt_id = _require(declared, "selected_prompt_id")
    if prompt_id not in PROMPT_CONTEXTS:
        raise TargetPluginResolutionError("target_plugin_prompt_unsupported")
    context_id = _require(declared, "selected_context_id")
    if context_id != PROMPT_CONTEXTS[prompt_id]:
        raise TargetPluginResolutionError("target_plugin_context_mismatch")
    if _require(declared, "execution_profile") != EXECUTION_PROFILE:
        raise TargetPluginResolutionError("target_plugin_execution_profile_mismatch")
    source_head = _git_head(root)
    declared_head = str(declared.get("source_head") or "").strip()
    if declared_head and declared_head != source_head:
        raise TargetPluginResolutionError("target_plugin_source_head_mismatch")
    selected_prompt = str(packet.get("selected_prompt_id") or packet.get("trial_prompt_id") or "").strip()
    if selected_prompt and selected_prompt != prompt_id:
        raise TargetPluginResolutionError("target_plugin_selected_prompt_mismatch")
    result_identity = f"{LUMACART_PLUGIN_ID}:{prompt_id}:{source_head[:12]}"
    return ResolvedTargetPlugin(
        schema_version=TARGET_PLUGIN_SCHEMA_VERSION,
        plugin_id=LUMACART_PLUGIN_ID,
        repository_id=CAMPAIGN_REPOSITORY_ID,
        worktree_id=CAMPAIGN_WORKTREE_ID,
        workspace_root=str(root),
        fixture_root=FIXTURE_ROOT,
        source_head=source_head,
        selected_prompt_id=prompt_id,
        selected_context_id=context_id,
        execution_profile=EXECUTION_PROFILE,
        allowed_actions=("propose", "approve", "execute", "verify", "record-evidence"),
        result_identity=result_identity,
    )
