from __future__ import annotations

import os
from pathlib import Path

import pytest

from source_proxy.context.obsidian import ObsidianContextConfig, build_obsidian_write_plan, query_obsidian_context


def _config(vault: Path, *, age: int = 60 * 60 * 24 * 30) -> ObsidianContextConfig:
    return ObsidianContextConfig(True, str(vault), ("*.md",), ("private/**",), 8, 1200, age)


def test_obsidian_context_has_exact_note_identity_and_detects_repository_conflict(tmp_path: Path) -> None:
    note = tmp_path / "coding.md"
    note.write_text("# Coding\nRepository conflict: use executable source for the current API.\n", encoding="utf-8")
    result = query_obsidian_context("current coding API", config=_config(tmp_path))
    assert result["status"] == "used"
    selected = result["notes"][0]
    assert selected["note_identity"].startswith("sha256:")
    assert selected["repository_conflict"] is True
    assert selected["freshness"]["age_seconds"] >= 0


def test_obsidian_write_is_a_bound_plan_not_a_filesystem_write(tmp_path: Path) -> None:
    plan = build_obsidian_write_plan(config=_config(tmp_path), relative_path="knowledge/coding.md", content="# Knowledge", task_id="task-1")
    assert plan["write_performed"] is False
    assert plan["requires_canonical_approval"] is True
    assert not (tmp_path / "knowledge" / "coding.md").exists()
    with pytest.raises(ValueError, match="path_invalid"):
        build_obsidian_write_plan(config=_config(tmp_path), relative_path="../escape.md", content="x", task_id="task-1")
