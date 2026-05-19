from __future__ import annotations

import unittest

from source_proxy.agents.registry import (
    AGENT_REGISTRY,
    MAX_DEFAULT_AUTHORITY_LEVEL,
    get_agent_registry_payload,
    get_provider_capability_payload,
    normalize_agent_role,
    provider_capability,
    role_system_prompt,
    validate_registry_authority,
)
from source_proxy.decision.router import DecisionInput, decide_route


class AgentRegistryTests(unittest.TestCase):
    def test_registry_defines_phase_8_roles_and_boundaries(self) -> None:
        expected_roles = {
            "architect",
            "coder",
            "reviewer",
            "tester",
            "documenter",
            "researcher",
            "blueprinter",
            "cartographer",
            "oracle",
            "debugger",
        }

        self.assertEqual(set(AGENT_REGISTRY), expected_roles)
        for role, entry in AGENT_REGISTRY.items():
            self.assertEqual(entry.role, role)
            self.assertLessEqual(entry.authority_level, MAX_DEFAULT_AUTHORITY_LEVEL)
            self.assertTrue(entry.allowed_actions)
            self.assertIn("apply", entry.forbidden_actions)
            self.assertIn("commit", entry.forbidden_actions)
            self.assertIn("push", entry.forbidden_actions)
            self.assertTrue(entry.input_sources)
            self.assertTrue(entry.output_type)
            self.assertTrue(entry.required_approval_gates)

        self.assertEqual(validate_registry_authority(), [])

    def test_registry_payload_is_serializable_and_names_authority(self) -> None:
        payload = get_agent_registry_payload()

        self.assertEqual(payload["reviewer"]["display_name"], "Reviewer Agent")
        self.assertEqual(payload["tester"]["output_type"], "test_plan_or_dry_run_report")
        self.assertEqual(payload["oracle"]["authority_level"], 1)
        self.assertIn("write_without_approval", payload["cartographer"]["forbidden_actions"])

    def test_provider_capability_registry_is_recommendation_only(self) -> None:
        payload = get_provider_capability_payload()

        self.assertEqual(
            set(payload),
            {"codex_cli", "local_ollama", "gemini_cli", "api_adapter"},
        )
        self.assertEqual(payload["codex_cli"]["status"], "available")
        self.assertEqual(payload["local_ollama"]["status"], "config_blocked")
        self.assertEqual(payload["local_ollama"]["missing_reason"], "not_probed_in_phase_9_1")
        for provider in payload.values():
            self.assertTrue(provider["recommendation_only"])
            self.assertFalse(provider["approval_authority"])
            self.assertFalse(provider["apply_authority"])
            self.assertFalse(provider["commit_authority"])
            self.assertFalse(provider["push_authority"])

        self.assertIsNone(provider_capability("missing_provider"))

    def test_role_prompt_resolution_uses_registry(self) -> None:
        self.assertEqual(normalize_agent_role("Reviewer Agent"), "reviewer")
        self.assertEqual(normalize_agent_role("blueprinter-agent"), "blueprinter")
        self.assertIsNone(normalize_agent_role("unknown"))
        self.assertIn("Reviewer", role_system_prompt("reviewer") or "")

    def test_router_accepts_registered_read_only_roles(self) -> None:
        decision = decide_route(
            DecisionInput(
                task="Review proposed docs diff",
                current_agent_role="reviewer",
            )
        )

        self.assertEqual(decision.current_agent_role, "reviewer")
        self.assertIn("Reviewer", decision.role_system_prompt or "")
        self.assertIsNotNone(decision.as_payload()["role_system_prompt"])


if __name__ == "__main__":
    unittest.main()
