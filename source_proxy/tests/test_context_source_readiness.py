from __future__ import annotations

import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from source_proxy.context.obsidian import ObsidianContextConfig, obsidian_context_config_from_env
from source_proxy.context.source_readiness import (
    ContextSourcePacket,
    build_context_source_readiness_packet,
    build_cartographer_context_packet,
    build_design_context_packet,
    build_obsidian_context_packet,
    build_scout_search_context_packet,
)


class ContextSourceReadinessTests(unittest.TestCase):
    def test_cartographer_packet_includes_repo_component_dirty_and_blueprint_truth(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text("{}", encoding="utf-8")
            (root / "source_proxy/cartographer").mkdir(parents=True)
            (root / "source_proxy/cartographer/example.py").write_text(
                "def build_example():\n    return {}\n",
                encoding="utf-8",
            )
            (root / "src/components/dashboard").mkdir(parents=True)
            (root / "src/components/dashboard/Widget.tsx").write_text(
                "export function Widget() { return null }\n",
                encoding="utf-8",
            )
            (root / "_blueprints").mkdir()
            (root / "_blueprints/INDEX.md").write_text("# Index\n", encoding="utf-8")

            packet = build_cartographer_context_packet(
                "Target file: src/components/dashboard/Widget.tsx",
                project_root=root,
            )

        self.assertEqual(packet.status, "used")
        self.assertGreater(packet.packet["repo_map"]["files_indexed"], 0)
        self.assertIn("component_map", packet.packet)
        self.assertIn("dirty_tree_status", packet.packet)
        self.assertEqual(
            packet.packet["ownership_conflict_status"],
            "no_dirty_tree_conflict_detected",
        )
        self.assertGreaterEqual(
            packet.packet["architecture_blueprint_truth"]["blueprint_count"],
            1,
        )
        self.assertFalse(packet.authority["can_apply"])

    def test_obsidian_disabled_is_skipped_with_diagnostics(self) -> None:
        packet = build_obsidian_context_packet(
            "coding output contract",
            config=ObsidianContextConfig(False, "", ("*.md",), ("secrets/**",), 8, 1200),
        )

        self.assertEqual(packet.status, "skipped")
        self.assertEqual(packet.reason, "disabled")
        self.assertFalse(packet.diagnostics["obsidian_context_used"])
        self.assertTrue(packet.authority["read_only"])
        self.assertFalse(packet.authority["can_write_memory"])

    def test_obsidian_selects_safe_task_specific_excerpt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            (vault / "note.md").write_text(
                "# Source Proxy\nToken: sk-123456789012345\nContext orchestration parser output contract.",
                encoding="utf-8",
            )
            packet = build_obsidian_context_packet(
                "parser output contract",
                config=ObsidianContextConfig(True, str(vault), ("*.md",), ("secrets/**",), 8, 1200),
            )

        self.assertEqual(packet.status, "used")
        self.assertEqual(packet.packet["notes"][0]["path"], "note.md")
        self.assertIn("Token=[redacted]", packet.packet["notes"][0]["safe_excerpt"])
        self.assertNotIn("sk-123456789012345", packet.packet["notes"][0]["safe_excerpt"])

    def test_obsidian_defaults_to_local_design_vault_when_env_unset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vault = root / "data/design-vault"
            vault.mkdir(parents=True)
            (vault / "token-model-v0.1.md").write_text(
                "# Token Model\nDesign token context for Source Proxy packets.",
                encoding="utf-8",
            )

            with (
                mock.patch.dict(os.environ, {}, clear=True),
                mock.patch("source_proxy.context.obsidian.Path.cwd", return_value=root),
            ):
                cfg = obsidian_context_config_from_env()
                packet = build_obsidian_context_packet("design token context")

        self.assertTrue(cfg.enabled)
        self.assertEqual(Path(cfg.vault_path), vault.resolve())
        self.assertEqual(packet.status, "used")
        self.assertEqual(packet.packet["notes"][0]["path"], "token-model-v0.1.md")

    def test_scout_search_sources_include_citations_and_no_write_authority(self) -> None:
        async def fake_research(*, task_id: str, query: str, max_results: int = 6):
            assert task_id.startswith("context-")
            assert query == "Source Proxy context readiness"
            sources = [
                {
                    "title": "Repo context",
                    "url": "repo://source_proxy/context/source_readiness.py",
                    "snippet": "Source Proxy context packet",
                    "source": "repo",
                    "evidence": {
                        "source": "repo://source_proxy/context/source_readiness.py",
                        "freshness": "current",
                        "trust_status": "workspace",
                        "review_status": "repo_first_match",
                        "packet_summary": "Context adapter",
                        "why_relevant": "Matches Source Proxy context readiness.",
                    },
                }
            ][:max_results]
            return {
                "status": "used",
                "reason": "research_sources_selected",
                "claim_ceiling": "repo_evidence_only",
                "sources": sources,
            }

        with mock.patch("source_proxy.context.source_readiness.run_canonical_coding_research", fake_research):
            packet = asyncio.run(build_scout_search_context_packet("Source Proxy context readiness"))

        self.assertEqual(packet.status, "used")
        source = packet.packet["sources"][0]
        self.assertEqual(source["evidence"]["trust_status"], "workspace")
        self.assertFalse(source["can_apply"])
        self.assertFalse(source["can_mutate_proxy_memory"])
        self.assertFalse(packet.diagnostics["hidden_code_writes"])
        self.assertFalse(packet.diagnostics["hidden_memory_writes"])

    def test_design_packet_is_advisory_only_with_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs/design-agent-example.md").write_text("# Design", encoding="utf-8")
            (root / "src/components/ui").mkdir(parents=True)
            (root / "src/components/ui/Button.tsx").write_text("export function Button() { return null }", encoding="utf-8")

            packet = build_design_context_packet("design Button polish", project_root=root)

        self.assertEqual(packet.status, "used")
        self.assertIn("docs/design-agent-example.md", packet.packet["design_system_refs"])
        self.assertIn("src/components/ui/Button.tsx", packet.packet["component_refs"])
        self.assertEqual(packet.packet["design_to_coder_handoff"]["authority"], "advisory_context_only")
        self.assertFalse(packet.authority["can_apply"])

    def test_combined_packet_reports_all_source_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text("{}", encoding="utf-8")
            (root / "source_proxy").mkdir()
            (root / "src/components/ui").mkdir(parents=True)
            (root / "src/components/ui/Button.tsx").write_text("export function Button() { return null }", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs/design-agent-example.md").write_text("# Design", encoding="utf-8")
            fake_cartographer = mock.Mock()
            fake_cartographer.source = "cartographer"
            fake_cartographer.status = "used"
            fake_cartographer.to_dict.return_value = {"source": "cartographer", "status": "used"}

            async def fake_scout(_task: str):
                fake = mock.Mock()
                fake.source = "scout_search"
                fake.status = "skipped"
                fake.to_dict.return_value = {"source": "scout_search", "status": "skipped"}
                return fake

            with (
                mock.patch("source_proxy.context.source_readiness.build_cartographer_context_packet", return_value=fake_cartographer),
                mock.patch("source_proxy.context.source_readiness.build_scout_search_context_packet", fake_scout),
            ):
                packet = asyncio.run(
                    build_context_source_readiness_packet(
                        "design Button polish",
                        project_root=root,
                        obsidian_config=ObsidianContextConfig(False, "", ("*.md",), ("secrets/**",), 8, 1200),
                    )
                )

        self.assertTrue(packet["ready_for_source_proxy_packet"])
        self.assertEqual(packet["schema_version"], 2)
        self.assertTrue(packet["canonical_context_broker"]["canonical"])
        self.assertEqual(packet["source_status"]["cartographer"], "used")
        self.assertEqual(packet["source_status"]["obsidian"], "skipped")
        self.assertEqual(packet["source_status"]["scout_search"], "skipped")
        self.assertEqual(packet["source_status"]["design"], "used")
        self.assertFalse(packet["authority"]["can_start_worker"])
        cartographer = next(
            source for source in packet["sources"] if source["source"] == "cartographer"
        )
        self.assertTrue(cartographer["considered"])
        self.assertFalse(cartographer["required"])
        self.assertFalse(cartographer["selected"])
        self.assertFalse(cartographer["included"])
        self.assertFalse(cartographer["consumed"])

    def test_selected_required_source_needs_real_v2_consumer_acknowledgement(self) -> None:
        cartographer = ContextSourcePacket(
            source="cartographer",
            status="used",
            reason="repo_map_ready",
            packet={"files_indexed": 4},
        )
        obsidian = ContextSourcePacket(
            source="obsidian",
            status="skipped",
            reason="disabled",
        )
        design = ContextSourcePacket(
            source="design",
            status="skipped",
            reason="not_needed",
        )

        async def fake_scout(_task: str):
            return ContextSourcePacket(
                source="scout_search",
                status="skipped",
                reason="not_needed",
            )

        with (
            mock.patch(
                "source_proxy.context.source_readiness.build_cartographer_context_packet",
                return_value=cartographer,
            ),
            mock.patch(
                "source_proxy.context.source_readiness.build_obsidian_context_packet",
                return_value=obsidian,
            ),
            mock.patch(
                "source_proxy.context.source_readiness.build_design_context_packet",
                return_value=design,
            ),
            mock.patch(
                "source_proxy.context.source_readiness.build_scout_search_context_packet",
                fake_scout,
            ),
        ):
            blocked = asyncio.run(
                build_context_source_readiness_packet(
                    "Implement the target",
                    source_states={
                        "cartographer": {
                            "required": True,
                            "selected": True,
                            "included": True,
                        }
                    },
                    applicable_consumers=("planner",),
                )
            )
            acknowledged = asyncio.run(
                build_context_source_readiness_packet(
                    "Implement the target",
                    source_states={
                        "cartographer": {
                            "required": True,
                            "selected": True,
                            "included": True,
                        }
                    },
                    downstream_consumers={
                        "planner": {
                            "applicable": True,
                            "acknowledged": True,
                            "sources": ["cartographer"],
                            "evidence": "planner_prompt_hash:abc123",
                        }
                    },
                    applicable_consumers=("planner",),
                )
            )

        self.assertFalse(blocked["ready_for_source_proxy_packet"])
        self.assertIn(
            "required_context_unacknowledged:cartographer:planner",
            blocked["canonical_context_broker"]["required_context_blockers"],
        )
        self.assertTrue(acknowledged["ready_for_source_proxy_packet"])
        selected = next(
            source
            for source in acknowledged["sources"]
            if source["source"] == "cartographer"
        )
        self.assertTrue(selected["required"])
        self.assertTrue(selected["selected"])
        self.assertTrue(selected["included"])
        self.assertTrue(selected["consumed"])
        self.assertEqual(selected["acknowledged_by"], ["planner"])

    def test_missing_named_required_source_is_preserved_and_fails_closed(self) -> None:
        cartographer = ContextSourcePacket(
            source="cartographer",
            status="skipped",
            reason="not_needed",
        )

        async def fake_scout(_task: str):
            return ContextSourcePacket(
                source="scout_search",
                status="skipped",
                reason="not_needed",
            )

        with (
            mock.patch(
                "source_proxy.context.source_readiness.build_cartographer_context_packet",
                return_value=cartographer,
            ),
            mock.patch(
                "source_proxy.context.source_readiness.build_obsidian_context_packet",
                return_value=ContextSourcePacket("obsidian", "skipped", "not_needed"),
            ),
            mock.patch(
                "source_proxy.context.source_readiness.build_design_context_packet",
                return_value=ContextSourcePacket("design", "skipped", "not_needed"),
            ),
            mock.patch(
                "source_proxy.context.source_readiness.build_scout_search_context_packet",
                fake_scout,
            ),
        ):
            packet = asyncio.run(
                build_context_source_readiness_packet(
                    "Use the Mac worker",
                    required_sources=("mac_worker",),
                )
            )

        mac_worker = next(
            source for source in packet["sources"] if source["source"] == "mac_worker"
        )
        self.assertEqual(mac_worker["status"], "unavailable")
        self.assertTrue(mac_worker["required"])
        self.assertFalse(packet["ready_for_source_proxy_packet"])
        self.assertIn(
            "required_context_unavailable:mac_worker",
            packet["canonical_context_broker"]["required_context_blockers"],
        )

    def test_combined_packet_uses_default_obsidian_vault_without_explicit_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.json").write_text("{}", encoding="utf-8")
            (root / "source_proxy").mkdir()
            vault = root / "data/design-vault"
            vault.mkdir(parents=True)
            (vault / "README.md").write_text(
                "# Context Vault\nSource Proxy context readiness note for coder packet flow.",
                encoding="utf-8",
            )
            (root / "src/components/ui").mkdir(parents=True)
            (root / "src/components/ui/Button.tsx").write_text("export function Button() { return null }", encoding="utf-8")
            fake_cartographer = mock.Mock()
            fake_cartographer.source = "cartographer"
            fake_cartographer.status = "used"
            fake_cartographer.to_dict.return_value = {"source": "cartographer", "status": "used"}

            async def fake_scout(_task: str):
                fake = mock.Mock()
                fake.source = "scout_search"
                fake.status = "skipped"
                fake.to_dict.return_value = {"source": "scout_search", "status": "skipped"}
                return fake

            with (
                mock.patch.dict(os.environ, {}, clear=True),
                mock.patch("source_proxy.context.obsidian.Path.cwd", return_value=root),
                mock.patch("source_proxy.context.source_readiness.build_cartographer_context_packet", return_value=fake_cartographer),
                mock.patch("source_proxy.context.source_readiness.build_scout_search_context_packet", fake_scout),
            ):
                packet = asyncio.run(
                    build_context_source_readiness_packet(
                        "Source Proxy context readiness coder packet flow",
                        project_root=root,
                    )
                )

        self.assertEqual(packet["source_status"]["obsidian"], "used")
        obsidian = next(source for source in packet["sources"] if source["source"] == "obsidian")
        self.assertEqual(obsidian["packet"]["notes"][0]["path"], "README.md")


if __name__ == "__main__":
    unittest.main()
