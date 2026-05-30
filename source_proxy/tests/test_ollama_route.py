from __future__ import annotations

import os
import unittest
from unittest import mock

from source_proxy.routing.litellm_router import clear_router_cache, route_models
from source_proxy.routing.ollama_route import (
    clear_ollama_route_cache,
    local_model_unavailable_from_error,
    ollama_route_status_entry,
    resolve_ollama_model_name,
    resolve_ollama_route,
)


class OllamaRouteTests(unittest.TestCase):
    def tearDown(self) -> None:
        clear_ollama_route_cache()
        clear_router_cache()

    def test_unreachable_primary_base_falls_back_to_localhost(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "OLLAMA_BASE_URL": "http://100.111.32.31:11434",
                "OLLAMA_URL": "http://127.0.0.1:11434",
                "SOURCE_PROXY_OLLAMA_BASE_URL": "",
                "SOURCE_PROXY_OLLAMA_MODEL": "",
                "OLLAMA_MODEL": "",
            },
            clear=False,
        ):
            clear_ollama_route_cache()
            route = resolve_ollama_route(probe=True)
        self.assertTrue(route.probe_ok, route)
        self.assertIn("127.0.0.1", route.api_base)
        self.assertIn("hermes", route.model)

    def test_default_model_is_hermes_when_unconfigured(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "SOURCE_PROXY_OLLAMA_MODEL": "",
                "OLLAMA_MODEL": "",
            },
            clear=False,
        ):
            self.assertEqual(resolve_ollama_model_name(), "hermes4")

    def test_unconfigured_route_prefers_available_hermes_model(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
                "SOURCE_PROXY_OLLAMA_MODEL": "",
                "OLLAMA_MODEL": "",
            },
            clear=False,
        ), mock.patch(
            "source_proxy.routing.ollama_route._probe_ollama_tags",
            return_value=(True, ("qwen2.5-coder:7b", "hermes3:8b-abliterated")),
        ):
            clear_ollama_route_cache()
            route = resolve_ollama_route(probe=True)

        self.assertEqual(route.model, "hermes3:8b-abliterated")
        self.assertEqual(route.requested_model, "hermes4")
        self.assertIn("available_hermes", route.selected_via)

    def test_status_exposes_requested_resolved_and_storage_proof(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
                "SOURCE_PROXY_OLLAMA_MODEL": "",
                "OLLAMA_MODEL": "",
                "OLLAMA_MODELS": "/mnt/spirit-8tb/ollama-models",
            },
            clear=False,
        ), mock.patch(
            "source_proxy.routing.ollama_route._probe_ollama_tags",
            return_value=(True, ("hermes4:latest", "qwen2.5-coder:7b")),
        ):
            clear_ollama_route_cache()
            status = ollama_route_status_entry()

        self.assertEqual(status["requested_ollama_model"], "hermes4")
        self.assertEqual(status["ollama_model"], "hermes4:latest")
        self.assertEqual(status["model"], "ollama_chat/hermes4:latest")
        self.assertEqual(status["model_storage_status"], "proven")
        self.assertEqual(status["model_storage_proof"], "OLLAMA_MODELS")

    def test_local_route_maps_to_ollama_chat_model(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
                "SOURCE_PROXY_OLLAMA_MODEL": "qwen2.5-coder:7b",
            },
            clear=False,
        ):
            clear_ollama_route_cache()
            clear_router_cache()
            local = next(item for item in route_models() if item.alias == "local")
        self.assertEqual(local.model, "ollama_chat/qwen2.5-coder:7b")

    def test_connection_refused_maps_to_local_model_unavailable(self) -> None:
        error = RuntimeError(
            "litellm.APIConnectionError: Ollama_chatException - [Errno 111] Connection refused. "
            "Received Model Group=local"
        )
        self.assertTrue(local_model_unavailable_from_error(error))


class OllamaRouteCoderReasonTests(unittest.TestCase):
    def test_coder_router_error_reason_code_for_local_connection_refused(self) -> None:
        from source_proxy.planning.plan import CoderPacket, TargetFile
        from source_proxy.tasks.long_running import CoderResponse, _coder_response_reason_code

        response = CoderResponse(
            status="blocked",
            target_path="docs/phase-8-manual-check.md",
            replacement_content=None,
            reasoning="Coder model/router call failed: Connection refused Model Group=local",
            blocked_reason="Coder model/router call failed.",
            blocked_needed_context="litellm.APIConnectionError: Ollama_chatException - [Errno 111] Connection refused",
        )
        packet = CoderPacket(
            target_file=TargetFile(path="docs/phase-8-manual-check.md", exists=True, sha256_before=None),
            operation="edit",
            acceptance_criteria=[],
            constraints=__import__(
                "source_proxy.planning.plan", fromlist=["ContentConstraints"]
            ).ContentConstraints(
                must_contain=[],
                must_not_contain=[],
                preserve_imports=[],
                preserve_exports=[],
                max_added_lines=10,
                max_removed_lines=0,
            ),
            context_slices=[],
            forbidden_paths=[],
            style_directives=[],
        )
        self.assertEqual(_coder_response_reason_code(response), "local_model_unavailable")
