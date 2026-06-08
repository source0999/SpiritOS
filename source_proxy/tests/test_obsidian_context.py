from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from source_proxy.context.obsidian import (
    ObsidianContextConfig,
    obsidian_context_diagnostics,
    query_obsidian_context,
)


class ObsidianContextTests(unittest.TestCase):
    def test_disabled_by_default_does_not_scan(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ObsidianContextConfig(
                enabled=False,
                vault_path=temp_dir,
                include_globs=("*.md",),
                exclude_globs=(".obsidian/**", "private/**", "secrets/**", "archive/**"),
                max_notes=4,
                max_chars_per_note=500,
            )
            result = query_obsidian_context("coder trial", config=config)

        self.assertEqual(result["status"], "disabled")
        self.assertEqual(result["diagnostics"]["obsidian_notes_considered"], 0)
        self.assertEqual(result["notes"], [])

    def test_missing_vault_path_fails_safely(self) -> None:
        config = ObsidianContextConfig(
            enabled=True,
            vault_path="",
            include_globs=("*.md",),
            exclude_globs=(".obsidian/**", "private/**", "secrets/**", "archive/**"),
            max_notes=4,
            max_chars_per_note=500,
        )

        result = query_obsidian_context("coder trial", config=config)

        self.assertEqual(result["status"], "missing_vault_path")
        self.assertFalse(result["diagnostics"]["obsidian_context_used"])

    def test_query_selects_relevant_notes_and_respects_excludes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "coder-trials.md").write_text(
                "# Coder Trials\nTrial PASS requires model-authored diff. token=secret-value",
                encoding="utf-8",
            )
            (root / "private").mkdir()
            (root / "private" / "coder-secret.md").write_text(
                "# Secret\nCoder trial password=private-value",
                encoding="utf-8",
            )
            (root / ".obsidian").mkdir()
            (root / ".obsidian" / "workspace.md").write_text(
                "internal state",
                encoding="utf-8",
            )
            (root / "coder-trials.txt").write_text(
                "Coder trial txt files must not be scanned.",
                encoding="utf-8",
            )
            config = ObsidianContextConfig(
                enabled=True,
                vault_path=temp_dir,
                include_globs=("*.md",),
                exclude_globs=(".obsidian/**", "private/**", "secrets/**", "archive/**"),
                max_notes=4,
                max_chars_per_note=500,
            )

            result = query_obsidian_context("coder trial pass", config=config)

        self.assertEqual(result["status"], "used")
        self.assertEqual(result["diagnostics"]["obsidian_notes_considered"], 1)
        self.assertEqual(result["diagnostics"]["obsidian_notes_selected"], 1)
        self.assertEqual(result["diagnostics"]["obsidian_context_paths"], ["coder-trials.md"])
        self.assertEqual(result["notes"][0]["path"], "coder-trials.md")
        self.assertIn("model-authored diff", result["notes"][0]["safe_excerpt"])
        self.assertNotIn("txt files", str(result))
        self.assertNotIn("secret-value", result["notes"][0]["safe_excerpt"])
        self.assertNotIn("private-value", str(result))

    def test_diagnostics_shape_matches_trial_memory_context_fields(self) -> None:
        diagnostics = obsidian_context_diagnostics(
            ObsidianContextConfig(
                enabled=False,
                vault_path="",
                include_globs=("*.md",),
                exclude_globs=(".obsidian/**", "private/**", "secrets/**", "archive/**"),
                max_notes=8,
                max_chars_per_note=1200,
            )
        )

        self.assertEqual(
            {
                "obsidian_context_enabled",
                "obsidian_context_used",
                "obsidian_notes_considered",
                "obsidian_notes_selected",
                "obsidian_context_chars",
                "obsidian_context_paths",
            }
            - set(diagnostics),
            set(),
        )
        self.assertTrue(diagnostics["obsidian_read_only"])


if __name__ == "__main__":
    unittest.main()
