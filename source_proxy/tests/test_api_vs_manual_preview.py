from __future__ import annotations

import unittest
from decimal import Decimal
from unittest.mock import patch

from fastapi.testclient import TestClient

from source_proxy.approval.gate import SpendBreakdown
from source_proxy.decision.preview import (
    ApiVsManualPreviewInput,
    build_api_vs_manual_preview,
)
from source_proxy.main import app


class ApiVsManualPreviewTests(unittest.TestCase):
    def test_preview_fails_closed_when_paid_alias_is_unavailable(self) -> None:
        preview = build_api_vs_manual_preview(
            ApiVsManualPreviewInput(
                task="Review this large repo change",
                api_model_alias="openai",
                context_tokens=42_000,
                needs_codebase_context=True,
            )
        )

        self.assertEqual(preview["preview_version"], "2.7B-2")
        self.assertEqual(preview["execution_status"], "paused_for_human_decision")
        self.assertFalse(preview["would_execute"])
        self.assertFalse(preview["projected_api_cost"]["available"])
        self.assertTrue(preview["projected_api_cost"]["fail_closed"])
        self.assertEqual(preview["required_human_decision"]["default_choice"], "manual")
        self.assertIn("codebase_context_requested", preview["privacy_flags"])
        self.assertEqual(preview["decision_summary"]["recommended_default"], "manual")
        self.assertTrue(preview["decision_summary"]["api_route"]["fail_closed"])
        self.assertEqual(preview["decision_summary"]["context"]["size_class"], "large")

    def test_preview_keeps_api_choice_gated_when_cost_is_available(self) -> None:
        fake_breakdown = SpendBreakdown(
            model_alias="openai",
            routed_model="gpt-4o-mini",
            provider="openai",
            prompt_tokens=128,
            max_completion_tokens=256,
            prompt_cost_usd=Decimal("0.00001920"),
            completion_cost_usd=Decimal("0.00015360"),
        )

        with (
            patch("source_proxy.decision.preview.route_model_for_alias", return_value="gpt-4o-mini"),
            patch("source_proxy.decision.preview.route_provider_for_alias", return_value="openai"),
            patch("source_proxy.decision.preview.projected_spend_breakdown", return_value=fake_breakdown),
        ):
            preview = build_api_vs_manual_preview(
                ApiVsManualPreviewInput(
                    task="Short API task",
                    api_model_alias="openai",
                    max_completion_tokens=256,
                    prefer_free=False,
                )
            )

        self.assertTrue(preview["projected_api_cost"]["available"])
        self.assertFalse(preview["projected_api_cost"]["fail_closed"])
        self.assertEqual(preview["projected_api_cost"]["projected_cost_usd"], "$0.00017280")
        self.assertTrue(preview["required_human_decision"]["api_choice_requires_approval"])
        self.assertFalse(preview["would_execute"])
        self.assertEqual(
            preview["decision_summary"]["api_route"]["projected_cost_usd"],
            "$0.00017280",
        )
        self.assertTrue(preview["decision_summary"]["api_route"]["requires_spend_approval"])

    def test_preview_endpoint_returns_required_decision_payload(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/v1/decisions/api-vs-manual-preview",
            json={
                "task": "Prepare a prompt packet for a private repo review with .env risk",
                "api_model_alias": "openai",
                "context_tokens": 12000,
                "sensitive": True,
                "needs_codebase_context": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["preview_version"], "2.7B-2")
        self.assertEqual(payload["execution_status"], "paused_for_human_decision")
        self.assertFalse(payload["would_execute"])
        self.assertIn("required_human_decision", payload)
        self.assertIn("projected_api_cost", payload)
        self.assertIn("manual_model_recommendation", payload)
        self.assertIn("manual_prompt_packet", payload)
        self.assertIn("decision_summary", payload)
        self.assertIn("user_marked_sensitive", payload["privacy_flags"])
        self.assertIn("possible_secret_or_env_content", payload["privacy_flags"])
        self.assertTrue(payload["decision_summary"]["privacy"]["has_flags"])

    def test_preview_contract_contains_plan_required_top_level_fields(self) -> None:
        preview = build_api_vs_manual_preview(
            ApiVsManualPreviewInput(
                task="Compare API and manual browser paths",
                context_tokens=9000,
            )
        )

        required_keys = {
            "projected_api_cost",
            "context_tokens",
            "manual_model_recommendation",
            "api_model_option",
            "privacy_flags",
            "required_human_decision",
            "decision_summary",
        }
        self.assertTrue(required_keys.issubset(preview.keys()))
        self.assertEqual(preview["decision_summary"]["context"]["tokens"], preview["context_tokens"])
        self.assertIn(
            preview["required_human_decision"]["default_choice"],
            preview["required_human_decision"]["allowed_choices"],
        )


if __name__ == "__main__":
    unittest.main()
