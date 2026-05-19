from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from source_proxy.decision.prompt_packet import PromptPacketInput, build_prompt_packet
from source_proxy.decision.recommendation import ModelRecommendationInput, recommend_model
from source_proxy.decision.router import DecisionInput, decide_route, resolve_target_from_task


class ProxyAgentRoutingTests(unittest.TestCase):
    def test_fix_prompt_prefers_coder_agent_route(self) -> None:
        decision = decide_route(
            DecisionInput(
                task="Fix the history bug on the /coding page.",
                wants_implementation=True,
            )
        )

        self.assertEqual(decision.task_classification, "implementation")
        self.assertEqual(decision.recommended_route, "local_route")
        self.assertEqual(decision.next_prompt_action, "run_with_coder_agent")
        self.assertIn("target_unresolved", decision.reason_codes)
        self.assertNotIn("repo_first_research", decision.reason_codes)
        self.assertFalse(decision.research_recommended)

    def test_debug_prompt_prefers_proxy_agent_route(self) -> None:
        decision = decide_route(
            DecisionInput(
                task="Debug the route decision payload in this repo.",
                needs_codebase_context=True,
            )
        )

        self.assertEqual(decision.recommended_route, "local_route")
        self.assertEqual(decision.next_prompt_action, "run_with_coder_agent")

    def test_implementation_classification_locks_local_route_even_with_large_context(self) -> None:
        decision = decide_route(
            DecisionInput(
                task="Refactor the whole codebase",
                context_tokens=50_000,
                needs_codebase_context=True,
                wants_implementation=True,
            )
        )

        self.assertEqual(decision.task_classification, "implementation")
        self.assertEqual(decision.recommended_route, "local_route")
        self.assertEqual(decision.next_prompt_action, "run_with_coder_agent")
        self.assertIn("large_context", decision.reason_codes)

    def test_active_swarm_coding_task_overrides_manual_route(self) -> None:
        decision = decide_route(
            DecisionInput(
                task="Implement the next planned coding increment.",
                active_task_id="task-123",
                context_tokens=50_000,
                wants_implementation=True,
            )
        )
        checks = {check["id"]: check for check in decision.self_correction_checks}

        self.assertEqual(decision.recommended_route, "local_route")
        self.assertEqual(decision.next_prompt_action, "run_with_coder_agent")
        self.assertTrue(checks["passive_check"]["passed"])
        self.assertIn("proactive agent route", str(checks["passive_check"]["answer"]))

    def test_ui_change_prompt_is_codebase_intent_not_current_research(self) -> None:
        decision = decide_route(
            DecisionInput(
                task="Add a Husky medicine button to the interface.",
                needs_current_info=True,
            )
        )

        self.assertEqual(decision.task_classification, "implementation")
        self.assertEqual(decision.recommended_route, "local_route")
        self.assertIn("target_unresolved", decision.reason_codes)
        self.assertNotIn("repo_first_research", decision.reason_codes)
        self.assertFalse(decision.research_recommended)

    def test_visual_layout_prompt_is_codebase_intent(self) -> None:
        decision = decide_route(
            DecisionInput(
                task="Move the top bar and change the font color.",
                needs_current_info=True,
            )
        )

        self.assertEqual(decision.task_classification, "implementation")
        self.assertEqual(decision.recommended_route, "local_route")
        self.assertIn("target_unresolved", decision.reason_codes)
        self.assertNotIn("repo_first_research", decision.reason_codes)
        self.assertFalse(decision.research_recommended)

    def test_padding_prompt_is_implementation_even_with_current_info_hint(self) -> None:
        decision = decide_route(
            DecisionInput(
                task="Add some extra padding.",
                needs_current_info=True,
            )
        )

        self.assertEqual(decision.task_classification, "implementation")
        self.assertEqual(decision.recommended_route, "local_route")
        self.assertIn("target_unresolved", decision.reason_codes)
        self.assertNotIn("repo_first_research", decision.reason_codes)
        self.assertFalse(decision.research_recommended)

    def test_active_swarm_action_word_defaults_to_codebase_intent(self) -> None:
        decision = decide_route(
            DecisionInput(
                task="Add the medicine reminder.",
                active_task_id="task-123",
                needs_current_info=True,
            )
        )

        self.assertEqual(decision.task_classification, "codebase_analysis")
        self.assertEqual(decision.recommended_route, "local_route")
        self.assertIn("active_swarm_actionable_increment", decision.reason_codes)

    def test_model_recommendation_names_coder_agent(self) -> None:
        recommendation = recommend_model(
            ModelRecommendationInput(
                task="Fix the history bug on the /coding page.",
                wants_implementation=True,
            )
        )

        self.assertEqual(recommendation.route_type, "local_route")
        self.assertEqual(recommendation.primary_model, "coder_agent")
        self.assertIn("Coder Agent", recommendation.expected_user_action)
        self.assertEqual(recommendation.provider_capability["provider_id"], "codex_cli")
        self.assertFalse(recommendation.provider_capability["apply_authority"])

    def test_model_recommendation_is_recommendation_only_for_config_blocked_local_provider(self) -> None:
        recommendation = recommend_model(
            ModelRecommendationInput(
                task="Review whether .env.local should be changed.",
                sensitive=True,
                prefer_free=True,
            )
        )

        self.assertEqual(recommendation.primary_model, "local_ollama")
        self.assertEqual(recommendation.provider_capability["status"], "config_blocked")
        self.assertTrue(recommendation.provider_capability["recommendation_only"])
        self.assertFalse(recommendation.provider_capability["approval_authority"])
        self.assertFalse(recommendation.provider_capability["apply_authority"])
        self.assertFalse(recommendation.provider_capability["commit_authority"])
        self.assertFalse(recommendation.provider_capability["push_authority"])

    def test_model_recommendation_prioritizes_local_route_for_active_swarm_task(self) -> None:
        recommendation = recommend_model(
            ModelRecommendationInput(
                task="Patch the next planned coding increment for src/app/demo/page.tsx.",
                active_task_id="task-123",
                context_tokens=50_000,
                wants_implementation=True,
            )
        )

        self.assertEqual(recommendation.route_type, "local_route")
        self.assertEqual(recommendation.primary_model, "coder_agent")
        self.assertIn("File Edit", recommendation.rationale)

    def test_active_swarm_ui_increment_is_local_even_with_current_info_hint(self) -> None:
        recommendation = recommend_model(
            ModelRecommendationInput(
                task="Add a toggle indicator to the plan panel.",
                active_task_id="task-123",
                needs_current_info=True,
            )
        )

        self.assertEqual(recommendation.route_type, "local_route")
        self.assertEqual(
            recommendation.route_decision.task_classification,
            "implementation",
        )
        self.assertIn(
            "active_swarm_actionable_increment",
            recommendation.route_decision.reason_codes,
        )

    def test_prompt_packet_tells_agent_to_implement_first(self) -> None:
        packet = build_prompt_packet(
            PromptPacketInput(
                task="Fix the history bug for Phase 7C / Increment 7C.4 on the /coding page.",
                wants_implementation=True,
            )
        )

        self.assertEqual(packet.route_decision.recommended_route, "local_route")
        self.assertEqual(packet.phase_label, "Phase 7C")
        self.assertEqual(packet.increment_label, "Increment 7C.4")
        self.assertIn("Coder Agent route selected", packet.relevant_context)
        self.assertIn("Phase 7C / Increment 7C.4", packet.prompt_text)
        self.assertIn("Concrete code changes", packet.prompt_text)
        self.assertTrue(
            any("Coder Agent implementation path" in constraint for constraint in packet.constraints)
        )

    def test_fresh_page_task_does_not_inherit_phase_7c(self) -> None:
        task = (
            "Create a brand new clean design-demo page at /coding/design-demo.\n\n"
            "Target file: src/app/coding/design-demo/page.tsx"
        )
        decision = decide_route(DecisionInput(task=task, wants_implementation=True))
        checks = {check["id"]: check for check in decision.self_correction_checks}
        packet = build_prompt_packet(
            PromptPacketInput(task=task, wants_implementation=True)
        )

        self.assertEqual(decision.recommended_route, "local_route")
        self.assertIn("Coder Agent", packet.relevant_context)
        self.assertNotIn("Phase 7C", packet.relevant_context)
        self.assertNotIn("Increment 7C.4", packet.prompt_text)
        self.assertNotIn("Name Phase 7C", "\n".join(packet.constraints))
        self.assertEqual(
            checks["phase_check"]["answer"],
            "No active phase was specified in this task; do not inherit one from prior runs.",
        )

    def test_route_payload_includes_self_correction_checks(self) -> None:
        decision = decide_route(
            DecisionInput(
                task="Add stronger self-correction for 7C.4 on the /coding page.",
                wants_implementation=True,
            )
        )
        checks = {check["id"]: check for check in decision.self_correction_checks}

        self.assertTrue(checks["passive_check"]["passed"])
        self.assertEqual(
            checks["passive_check"]["answer"],
            "No. This is a coding/debugging task. A proactive agent route is required.",
        )
        self.assertTrue(checks["repo_first_check"]["passed"])
        self.assertEqual(
            checks["repo_first_check"]["answer"],
            "Repo-first research is not required for this prompt.",
        )
        self.assertTrue(checks["phase_check"]["passed"])
        self.assertIn("7C.4", str(checks["phase_check"]["answer"]))

    def test_route_payload_includes_backend_resolved_explicit_target(self) -> None:
        decision = decide_route(
            DecisionInput(
                task='Target file: "src/app/page.tsx"\nAdd a footer link.',
                wants_implementation=True,
            )
        )

        self.assertEqual(
            decision.as_payload()["resolved_target"],
            {
                "path": "src/app/page.tsx",
                "exists": False,
                "source": "explicit_line",
            },
        )
        self.assertIn("target_missing", decision.reason_codes)

    def test_resolve_target_infers_docs_path_from_task_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "docs" / "phase-8-manual-check.md"
            doc.parent.mkdir(parents=True)
            doc.write_text("# ok\n", encoding="utf-8")
            resolved = resolve_target_from_task(
                "Please update docs/phase-8-manual-check.md with a checklist.\n",
                workspace_root=root,
            )
            self.assertEqual(resolved.path, "docs/phase-8-manual-check.md")
            self.assertTrue(resolved.exists)
            self.assertEqual(resolved.source, "inferred")

    def test_resolve_target_strips_sentence_punctuation_after_extension(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc = root / "docs" / "phase-8-manual-check.md"
            doc.parent.mkdir(parents=True)
            doc.write_text("# ok\n", encoding="utf-8")

            resolved = resolve_target_from_task(
                "Append a sentence to docs/phase-8-manual-check.md. Do not edit any other file.",
                workspace_root=root,
            )

            self.assertEqual(resolved.path, "docs/phase-8-manual-check.md")
            self.assertTrue(resolved.exists)

    def test_wants_implementation_adds_target_unresolved_without_path(self) -> None:
        decision = decide_route(
            DecisionInput(
                task="Make the dashboard feel faster (no file paths in this stub).",
                wants_implementation=True,
            )
        )
        self.assertIn("target_unresolved", decision.reason_codes)
        resolved = resolve_target_from_task(
            "Target file: src/lib/ignore.ts\nTarget file: `source_proxy/decision/router.py`"
        )

        self.assertEqual(resolved.path, "source_proxy/decision/router.py")
        self.assertEqual(resolved.source, "explicit_line")

    def test_env_local_explicit_target_blocks_before_dot_is_stripped(self) -> None:
        for task in (
            ".env.local, add TEST_VALUE=1",
            "Target file: .env.local\n\nAdd TEST_VALUE=1",
            "Target file: ./.env.local\n\nAdd TEST_VALUE=1",
        ):
            with self.subTest(task=task):
                decision = decide_route(
                    DecisionInput(task=task, wants_implementation=True)
                )

                self.assertIn("protected_path", decision.reason_codes)
                self.assertIn("secret_path", decision.reason_codes)
                self.assertNotIn("repo_first_research", decision.reason_codes)
                self.assertFalse(decision.research_recommended)
                self.assertNotEqual(decision.resolved_target.path, "env.local")
                self.assertIn(decision.resolved_target.path, {".env.local", ""})

    def test_path_traversal_target_blocks_without_random_fallback(self) -> None:
        for task in (
            "../outside.txt, write hello",
            "Target file: ../outside.txt\n\nWrite hello.",
            "Target file: ..\\outside.txt\n\nWrite hello.",
        ):
            with self.subTest(task=task):
                decision = decide_route(
                    DecisionInput(task=task, wants_implementation=True)
                )

                self.assertIn("path_escape", decision.reason_codes)
                self.assertIn("outside_workspace", decision.reason_codes)
                self.assertNotIn("repo_first_research", decision.reason_codes)
                self.assertFalse(decision.research_recommended)
                self.assertIn(decision.resolved_target.path, {"../outside.txt", ""})
                self.assertNotEqual(decision.resolved_target.path, "public/next.svg")

    def test_vague_docs_write_blocks_as_target_unresolved(self) -> None:
        decision = decide_route(
            DecisionInput(
                task="Make a small improvement to the docs explaining approval safety.",
                wants_implementation=True,
            )
        )

        self.assertIn("target_unresolved", decision.reason_codes)
        self.assertNotIn("repo_first_research", decision.reason_codes)
        self.assertFalse(decision.research_recommended)
        self.assertEqual(decision.resolved_target.path, "")


if __name__ == "__main__":
    unittest.main()
