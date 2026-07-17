from pathlib import Path

import pytest

from source_proxy.target_plugins.adapter import (
    CAMPAIGN_REPOSITORY_ID,
    CAMPAIGN_WORKTREE_ID,
    EXECUTION_PROFILE,
    FIXTURE_ROOT,
    LUMACART_PLUGIN_ID,
    PROMPT_CONTEXTS,
    TARGET_PLUGIN_SCHEMA_VERSION,
    TargetPluginResolutionError,
    resolve_target_plugin,
)


ROOT = Path(__file__).resolve().parents[2]


def packet(prompt_id: str = "coder-001-init-dummy-product-site") -> dict:
    return {
        "selected_prompt_id": prompt_id,
        "target_plugin": {
            "schema_version": TARGET_PLUGIN_SCHEMA_VERSION,
            "id": LUMACART_PLUGIN_ID,
            "repository_id": CAMPAIGN_REPOSITORY_ID,
            "worktree_id": CAMPAIGN_WORKTREE_ID,
            "fixture_root": FIXTURE_ROOT,
            "selected_prompt_id": prompt_id,
            "selected_context_id": PROMPT_CONTEXTS.get(prompt_id, "unsupported-context"),
            "execution_profile": EXECUTION_PROFILE,
        },
    }


@pytest.mark.parametrize(
    "prompt_id",
    ["coder-001-init-dummy-product-site", "coder-010-protected-path-pressure-trap", "coder-010-hardening"],
)
def test_resolves_known_prompt_or_fails_closed(prompt_id: str) -> None:
    if prompt_id in PROMPT_CONTEXTS:
        assert resolve_target_plugin(packet(prompt_id), ROOT).selected_prompt_id == prompt_id
    else:
        with pytest.raises(TargetPluginResolutionError, match="prompt_unsupported"):
            resolve_target_plugin(packet(prompt_id), ROOT)


@pytest.mark.parametrize(
    ("path", "value", "reason"),
    [
        ("id", "unknown", "unsupported"),
        ("repository_id", "other", "repository_mismatch"),
        ("worktree_id", "other", "worktree_mismatch"),
        ("fixture_root", "other/", "root_mismatch"),
        ("selected_context_id", "other", "context_mismatch"),
        ("execution_profile", "other", "execution_profile_mismatch"),
    ],
)
def test_rejects_substitution(path: str, value: str, reason: str) -> None:
    value_packet = packet()
    value_packet["target_plugin"][path] = value
    with pytest.raises(TargetPluginResolutionError, match=reason):
        resolve_target_plugin(value_packet, ROOT)


def test_rejects_missing_plugin_and_stale_head() -> None:
    with pytest.raises(TargetPluginResolutionError, match="missing"):
        resolve_target_plugin({}, ROOT)
    stale = packet()
    stale["target_plugin"]["source_head"] = "0" * 40
    with pytest.raises(TargetPluginResolutionError, match="source_head_mismatch"):
        resolve_target_plugin(stale, ROOT)


def test_typescript_selection_and_python_identity_bind_campaign_2_and_source_head() -> None:
    typescript_gateway = (ROOT / "src/lib/coding/target-plugins/index.ts").read_text(encoding="utf-8")
    resolved = resolve_target_plugin(packet(), ROOT)

    assert 'repository_id: "spiritos-campaign-2"' in typescript_gateway
    assert 'worktree_id: "spiritos-campaign-2-20260716"' in typescript_gateway
    identity = resolved.evidence_identity()
    assert identity["repository_id"] == "spiritos-campaign-2"
    assert identity["worktree_id"] == "spiritos-campaign-2-20260716"
    assert identity["source_head"]
    assert identity["selected_prompt_id"] == packet()["target_plugin"]["selected_prompt_id"]
