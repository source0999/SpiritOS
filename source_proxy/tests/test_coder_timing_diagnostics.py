from __future__ import annotations

import asyncio
import os
import unittest
from unittest import mock

from source_proxy.api.decision import (
    _bounded_coder_diff_or_stub,
    _infer_coder_timeout_stage,
)
from source_proxy.routing.litellm_router import clear_router_cache, route_models
from source_proxy.routing.ollama_route import (
    clear_ollama_route_cache,
    resolve_coder_ollama_model_name,
)
from source_proxy.tasks.long_running import (
    _call_coder_llm,
    _coder_model_alias,
    _mark_coder_timing,
    reset_coder_timing_diagnostics,
    snapshot_coder_timing_diagnostics,
)


class RealisticReversibleFixtureTests(unittest.TestCase):
    def test_component_trial_warning_uses_live_model_proof_path(self) -> None:
        from source_proxy.api.decision import _realistic_reversible_trial_coder_diff_payload

        task = "\n".join(
            [
                "Make the small badge component support a warning state for partial results.",
                "Target file: tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx",
            ]
        )
        with mock.patch(
            "source_proxy.tasks.long_running._call_coder_llm",
            return_value="Confirmed reversible warning badge edit.",
        ) as llm_mock:
            payload = _realistic_reversible_trial_coder_diff_payload(task)
        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload.get("reason_code"), "realistic_reversible_live_trial_diff")
        self.assertTrue(payload.get("coder_diagnostics", {}).get("provider_call_made"))
        llm_mock.assert_called_once()
        self.assertEqual(llm_mock.call_args.kwargs.get("model_alias"), "coder")


class CoderOllamaModelTests(unittest.TestCase):
    def tearDown(self) -> None:
        clear_ollama_route_cache()
        clear_router_cache()

    def test_resolve_coder_ollama_model_prefers_qwen_when_installed(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"SOURCE_PROXY_CODER_OLLAMA_MODEL": ""},
            clear=False,
        ), mock.patch(
            "source_proxy.routing.ollama_route._probe_ollama_tags",
            return_value=(True, ("hermes4:latest", "qwen2.5-coder:7b")),
        ):
            clear_ollama_route_cache()
            self.assertEqual(resolve_coder_ollama_model_name(probe=True), "qwen2.5-coder:7b")

    def test_coder_alias_route_uses_coder_ollama_model(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"SOURCE_PROXY_CODER_OLLAMA_MODEL": "qwen2.5-coder:7b"},
            clear=False,
        ), mock.patch(
            "source_proxy.routing.ollama_route._probe_ollama_tags",
            return_value=(True, ("hermes4:latest", "qwen2.5-coder:7b")),
        ):
            clear_ollama_route_cache()
            clear_router_cache()
            coder = next(item for item in route_models() if item.alias == "coder")
        self.assertEqual(coder.model, "ollama_chat/qwen2.5-coder:7b")

    def test_default_coder_model_alias_is_coder_lane(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"SOURCE_PROXY_CODER_MODEL_ALIAS": ""},
            clear=False,
        ), mock.patch(
            "source_proxy.routing.ollama_route._probe_ollama_tags",
            return_value=(True, ("hermes4:latest", "qwen2.5-coder:7b")),
        ):
            clear_ollama_route_cache()
            clear_router_cache()
            self.assertEqual(_coder_model_alias(), "coder")


class CoderTimeoutDiagnosticsTests(unittest.TestCase):
    def test_infer_timeout_stage_when_provider_started(self) -> None:
        timing = {
            "target_resolution_started_ms": 1.0,
            "provider_request_started_at_ms": 2.0,
        }
        self.assertEqual(_infer_coder_timeout_stage(timing), "provider_generation")

    def test_coder_sync_timeout_includes_stage_and_model_fields(self) -> None:
        class _SlowPlan:
            source_task = "Target file: docs/x.md\n\nDo thing"

        async def _slow_coder(*_args, **_kwargs) -> dict:
            _mark_coder_timing("target_resolution_started")
            _mark_coder_timing(
                "coder_llm",
                model_requested="coder",
                model_resolved="ollama_chat/qwen2.5-coder:7b",
            )
            await asyncio.sleep(5)
            return {}

        async def _run() -> dict:
            with mock.patch(
                "source_proxy.api.decision._propose_coder_via_executor",
                side_effect=_slow_coder,
            ), mock.patch(
                "source_proxy.api.decision._coder_sync_deadline_seconds",
                return_value=0.05,
            ):
                return await _bounded_coder_diff_or_stub(
                    "Target file: docs/x.md",
                    _SlowPlan(),
                    force_live_model=False,
                )

        payload = asyncio.run(_run())
        self.assertEqual(payload.get("reason_code"), "coder_sync_timeout")
        diagnostics = payload.get("coder_diagnostics") or {}
        self.assertEqual(diagnostics.get("timeout_stage"), "coder_llm_prepare")
        self.assertEqual(diagnostics.get("model_requested"), "coder")
        self.assertEqual(diagnostics.get("model_resolved"), "ollama_chat/qwen2.5-coder:7b")

    def test_provider_model_proof_fields_set_when_provider_call_starts(self) -> None:
        with mock.patch(
            "source_proxy.tasks.long_running.get_router"
        ) as router_mock, mock.patch(
            "source_proxy.tasks.long_running.route_model_for_alias",
            return_value="ollama_chat/qwen2.5-coder:7b",
        ), mock.patch(
            "source_proxy.tasks.long_running.central_gate_check",
        ):
            router_mock.return_value.completion.return_value = mock.Mock(
                model_dump=lambda: {"choices": [{"message": {"content": '{"replacement_content":"x"}'}}]}  # noqa: E501
            )
            reset_coder_timing_diagnostics()
            _mark_coder_timing("target_resolution_started")
            raw = _call_coder_llm("tiny", model_alias="coder", timeout_seconds=30)
        self.assertTrue(raw)
        timing = snapshot_coder_timing_diagnostics()
        self.assertIn("provider_request_started_at_ms", timing)
        self.assertEqual(timing.get("model_requested"), "coder")
        self.assertTrue(str(timing.get("model_resolved") or "").startswith("ollama_chat/"))
        completion_kwargs = router_mock.return_value.completion.call_args.kwargs
        self.assertEqual(completion_kwargs["messages"][0]["role"], "system")
        self.assertEqual(completion_kwargs["messages"][1], {"role": "user", "content": "tiny"})
        self.assertEqual(completion_kwargs["max_tokens"], 1000)
