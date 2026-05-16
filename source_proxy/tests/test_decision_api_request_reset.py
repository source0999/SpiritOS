from __future__ import annotations

import unittest

from source_proxy.api.decision import (
    AVAILABLE_ROUTES,
    PromptPacketRequest,
    RouteDecisionRequest,
    _coder_prompt_packet_status,
    _request_with_cleared_file_focus,
    _route_payload_requests_coder_agent_diff,
    _with_bridge_route,
)
from source_proxy.decision.router import DecisionInput, decide_route


class DecisionApiRequestResetTests(unittest.TestCase):
    def test_coder_prompt_packet_status_for_missing_model_is_config_blocked(self) -> None:
        status = _coder_prompt_packet_status(
            already_satisfied=False,
            coder_blocked=True,
            proposed="",
            reason_code="coder_model_not_configured",
            subjective_improvement_needs_diff=False,
        )
        self.assertEqual(status, "coder_config_blocked")

    def test_coder_agent_route_is_registered_for_bridge_execution(self) -> None:
        route = AVAILABLE_ROUTES["run_with_coder_agent"]

        self.assertEqual(route["route_type"], "local_route")
        self.assertEqual(route["execution_path"], "coder_agent")
        self.assertFalse(route["manual_prompt_packet"])

    def test_local_route_payload_includes_coder_agent_bridge_route(self) -> None:
        payload = _with_bridge_route(
            {
                "recommended_route": "local_route",
                "next_prompt_action": "run_with_coder_agent",
            }
        )

        self.assertEqual(payload["bridge_route"]["action"], "run_with_coder_agent")
        self.assertEqual(payload["bridge_route"]["route_type"], "local_route")
        self.assertEqual(payload["bridge_route"]["execution_path"], "coder_agent")
        self.assertTrue(payload["bridge_route"]["available"])

    def test_route_payload_requests_coder_diff_by_route_or_bridge(self) -> None:
        self.assertTrue(
            _route_payload_requests_coder_agent_diff(
                {"next_prompt_action": "run_with_coder_agent", "recommended_route": "manual_route"}
            )
        )
        self.assertTrue(
            _route_payload_requests_coder_agent_diff(
                {"next_prompt_action": "", "recommended_route": "local_route"}
            )
        )
        self.assertTrue(
            _route_payload_requests_coder_agent_diff(
                {
                    "next_prompt_action": "",
                    "recommended_route": "api_route",
                    "bridge_route": {"execution_path": "coder_agent"},
                }
            )
        )
        self.assertFalse(
            _route_payload_requests_coder_agent_diff(
                {
                    "next_prompt_action": "generate_manual_prompt_packet",
                    "recommended_route": "manual_route",
                }
            )
        )

    def test_route_request_clears_stale_file_focus(self) -> None:
        request = RouteDecisionRequest(
            task="Add a button",
            proposed_diff="diff --git a/old.tsx b/old.tsx",
            target_files=["src/components/coding/CodingAgentInterface.tsx"],
            targeted_files=["source_proxy/decision/router.py"],
        )

        reset = _request_with_cleared_file_focus(request)

        self.assertEqual(reset.target_files, [])
        self.assertEqual(reset.targeted_files, [])
        self.assertIsNone(reset.proposed_diff)

    def test_prompt_packet_request_preserves_prompt_fields_while_clearing_focus(self) -> None:
        request = PromptPacketRequest(
            task="Move the top bar",
            relevant_context="Current task context",
            target_model_hint="chatgpt",
            target_files=["src/components/coding/CodingAgentInterface.tsx"],
        )

        reset = _request_with_cleared_file_focus(request)

        self.assertEqual(reset.task, request.task)
        self.assertEqual(reset.relevant_context, request.relevant_context)
        self.assertEqual(reset.target_model_hint, request.target_model_hint)
        self.assertEqual(reset.target_files, [])

    def test_prompt_packet_request_drops_prior_ui_memory_for_fresh_task(self) -> None:
        request = PromptPacketRequest(
            task="Add a button",
            conversation_context=[{"task": "old prompt"}],
            decision_memory=[{"task": "older route"}],
            context_tokens=1200,
            relevant_context=(
                "Recent coding conversation context:\n\n"
                "Turn 1: old prompt\n"
                "Route: manual_route\n\n"
                "Previous routing decision memory:\n\n"
                "Memory 1: older route\n"
                "Classification: general_reasoning\n\n"
                "Source 1: Repo: source_proxy/decision/router.py\n"
                "URL: repo://source_proxy/decision/router.py"
            ),
        )

        reset = _request_with_cleared_file_focus(request)

        self.assertEqual(reset.conversation_context, [])
        self.assertEqual(reset.decision_memory, [])
        self.assertIsNone(reset.context_tokens)
        self.assertNotIn("Recent coding conversation context", reset.relevant_context or "")
        self.assertNotIn("Previous routing decision memory", reset.relevant_context or "")
        self.assertIn("Source 1", reset.relevant_context or "")

    def test_previous_phase_memory_does_not_contaminate_fresh_route_decision(self) -> None:
        task = (
            "Create a brand new clean design-demo page at /coding/design-demo.\n\n"
            "Target file: src/app/coding/design-demo/page.tsx"
        )
        request = PromptPacketRequest(
            task=task,
            decision_memory=[
                {
                    "task": "Phase 7C / Increment 7C.4 old task",
                    "target": "src/components/coding/CodingAgentInterface.tsx",
                    "proposedDiff": "diff --git a/old b/old",
                }
            ],
            relevant_context=(
                "Previous routing decision memory:\n\n"
                "Memory 1: Phase 7C / Increment 7C.4 old task\n"
                "Target: src/components/coding/CodingAgentInterface.tsx"
            ),
        )
        reset = _request_with_cleared_file_focus(request)
        decision = decide_route(DecisionInput(task=reset.task, wants_implementation=True))
        checks = {check["id"]: check for check in decision.self_correction_checks}

        self.assertEqual(reset.decision_memory, [])
        self.assertNotIn("Phase 7C", reset.relevant_context or "")
        self.assertEqual(decision.recommended_route, "local_route")
        self.assertEqual(
            checks["phase_check"]["answer"],
            "No active phase was specified in this task; do not inherit one from prior runs.",
        )


if __name__ == "__main__":
    unittest.main()
