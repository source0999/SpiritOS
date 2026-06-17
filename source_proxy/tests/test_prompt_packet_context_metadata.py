from __future__ import annotations

import os
import asyncio
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.decision import (
    PromptPacketRequest,
    _attach_fip0_truth_receipt,
    _build_fip2_research_packet,
    _fip4_allow_fip5_chain,
    _fip4_call_timeout_seconds,
    _fip4_call_qwen,
    _fip4_qwen_max_attempts,
    _fip5_call_hermes_verifier,
    _fip5_browser_probe,
    _fip5_browser_verifier,
    _fip5_functional_verifier,
    _fip5_normalize_hermes_verifier_output,
    _json_hash,
    _bounded_coder_diff_or_stub,
    _run_fip4_qwen_coder,
    _run_fip5_verifier_and_repair,
    router as decision_router,
)
from source_proxy.decision.model_lanes import _normalize_gemma_output
from source_proxy.decision.prompt_packet import PromptPacketInput, build_prompt_packet
from source_proxy.tasks.long_running import (
    advance_long_running_task,
    create_long_running_task,
    get_long_running_task,
    reset_long_running_tasks,
    update_long_running_task,
)


class PromptPacketContextMetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self._previous_database_path = os.environ.get(
            "SOURCE_PROXY_LONG_RUNNING_TASKS_DB"
        )
        self._previous_fip0_receipt_dir = os.environ.get(
            "SOURCE_PROXY_FIP0_RECEIPT_DIR"
        )
        self._previous_fip1_context_enabled = os.environ.get(
            "SOURCE_PROXY_FIP1_CONTEXT_ENABLED"
        )
        self._previous_fip2_research_enabled = os.environ.get(
            "SOURCE_PROXY_FIP2_RESEARCH_ENABLED"
        )
        self._previous_fip3_model_lanes_enabled = os.environ.get(
            "SOURCE_PROXY_FIP3_MODEL_LANES_ENABLED"
        )
        self._tempdir = tempfile.TemporaryDirectory()
        os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = os.path.join(
            self._tempdir.name,
            "tasks.sqlite3",
        )
        os.environ["SOURCE_PROXY_FIP0_RECEIPT_DIR"] = os.path.join(
            self._tempdir.name,
            "fip0-receipts",
        )
        os.environ["SOURCE_PROXY_FIP1_CONTEXT_ENABLED"] = "0"
        os.environ["SOURCE_PROXY_FIP2_RESEARCH_ENABLED"] = "0"
        os.environ["SOURCE_PROXY_FIP3_MODEL_LANES_ENABLED"] = "0"
        reset_long_running_tasks()

    def tearDown(self) -> None:
        reset_long_running_tasks()
        if self._previous_database_path is None:
            os.environ.pop("SOURCE_PROXY_LONG_RUNNING_TASKS_DB", None)
        else:
            os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = (
                self._previous_database_path
            )
        if self._previous_fip0_receipt_dir is None:
            os.environ.pop("SOURCE_PROXY_FIP0_RECEIPT_DIR", None)
        else:
            os.environ["SOURCE_PROXY_FIP0_RECEIPT_DIR"] = (
                self._previous_fip0_receipt_dir
            )
        if self._previous_fip1_context_enabled is None:
            os.environ.pop("SOURCE_PROXY_FIP1_CONTEXT_ENABLED", None)
        else:
            os.environ["SOURCE_PROXY_FIP1_CONTEXT_ENABLED"] = (
                self._previous_fip1_context_enabled
            )
        if self._previous_fip2_research_enabled is None:
            os.environ.pop("SOURCE_PROXY_FIP2_RESEARCH_ENABLED", None)
        else:
            os.environ["SOURCE_PROXY_FIP2_RESEARCH_ENABLED"] = (
                self._previous_fip2_research_enabled
            )
        if self._previous_fip3_model_lanes_enabled is None:
            os.environ.pop("SOURCE_PROXY_FIP3_MODEL_LANES_ENABLED", None)
        else:
            os.environ["SOURCE_PROXY_FIP3_MODEL_LANES_ENABLED"] = (
                self._previous_fip3_model_lanes_enabled
            )
        self._tempdir.cleanup()

    def _client(self) -> TestClient:
        app = FastAPI()
        app.include_router(decision_router)
        return TestClient(app)

    def _write_fip0_receipt(self, receipt: dict[str, object]) -> Path:
        root = Path(os.environ["SOURCE_PROXY_FIP0_RECEIPT_DIR"])
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{receipt['run_id']}.json"
        path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        return path

    def _urlopen_json_response(self, payload: dict[str, object]):
        class Response:
            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, exc_type, exc, tb):
                return False

            def read(self_inner) -> bytes:
                return json.dumps(payload).encode("utf-8")

        return Response()

    def test_prompt_packet_marks_missing_context_without_claiming_file_contents(self) -> None:
        packet = build_prompt_packet(
            PromptPacketInput(
                task="Review the repo architecture",
                needs_codebase_context=True,
            )
        ).as_payload()

        metadata = packet["context_metadata"]
        self.assertEqual(metadata["context_inclusion_mode"], "none")
        self.assertFalse(metadata["file_contents_claimed"])
        self.assertEqual(metadata["included_paths"], [])
        self.assertIn("ask for the specific files", packet["relevant_context"])

    def test_prompt_packet_marks_path_listing_only_and_omits_secret_paths(self) -> None:
        packet = build_prompt_packet(
            PromptPacketInput(
                task="Review Windows project folder listing",
                relevant_context=(
                    "Path listing only:\n"
                    "C:\\Projects\\SpiritOS\\package.json\n"
                    "C:\\Projects\\SpiritOS\\.env\n"
                    "src/app/page.tsx\n"
                ),
                needs_codebase_context=True,
            )
        ).as_payload()

        metadata = packet["context_metadata"]
        self.assertEqual(metadata["context_inclusion_mode"], "path_listing_only")
        self.assertFalse(metadata["file_contents_claimed"])
        self.assertIn("C:\\Projects\\SpiritOS\\package.json", metadata["included_paths"])
        self.assertIn("src/app/page.tsx", metadata["included_paths"])
        self.assertNotIn("C:\\Projects\\SpiritOS\\.env", metadata["included_paths"])
        self.assertIn("C:\\Projects\\SpiritOS\\.env", metadata["omitted_paths"])

    def test_prompt_packet_marks_generated_bundle_reference(self) -> None:
        packet = build_prompt_packet(
            PromptPacketInput(
                task="Use compressed context",
                relevant_context="generated_context_bundle: repomix-output.ast.xml",
                context_tokens=12000,
            )
        ).as_payload()

        metadata = packet["context_metadata"]
        self.assertEqual(metadata["context_inclusion_mode"], "generated_bundle_reference")
        self.assertFalse(metadata["file_contents_claimed"])
        self.assertIn("repomix-output.ast.xml", metadata["included_paths"])
        self.assertGreater(metadata["estimated_context_tokens"], 0)

    def test_prompt_packet_endpoint_returns_context_metadata(self) -> None:
        client = self._client()
        response = client.post(
            "/v1/decisions/prompt-packet",
            json={
                "task": "Create prompt packet from listing",
                "relevant_context": "folder listing:\nsrc/lib/example.ts",
                "needs_codebase_context": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("context_metadata", payload)
        self.assertEqual(
            payload["context_metadata"]["context_inclusion_mode"],
            "path_listing_only",
        )

    def test_prompt_packet_endpoint_writes_fip0_universal_truth_receipt(self) -> None:
        client = self._client()
        response = client.post(
            "/v1/decisions/prompt-packet",
            json={
                "task": "Route a FIP-0 receipt foundation prompt through /coding truth.",
                "needs_codebase_context": True,
                "allowed_files": ["docs/evidence/source-proxy-full-integration-pivot/master-plan.md"],
                "forbidden_files": [".env"],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        receipt = payload["fip0_truth_receipt"]
        receipt_path = Path(payload["fip0_truth_receipt_path"])
        self.assertTrue(receipt_path.is_file())
        saved = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["run_id"], receipt["run_id"])
        self.assertEqual(saved["final_packet_hash"], receipt["final_packet_hash"])
        self.assertTrue(receipt["final_packet_hash"])
        self.assertIn("coder_received_packet_hash", receipt)
        required_statuses = [
            "context_router_status",
            "repo_research_status",
            "obsidian_status",
            "cartographer_status",
            "design_status",
            "mac_worker_status",
            "scout_status",
            "searxng_status",
            "gemma_status",
            "hermes_critic_status",
            "qwen_coder_status",
            "hermes_verifier_status",
            "repair_loop_status",
            "browser_behavior_status",
            "deterministic_check_status",
            "output_contract_status",
            "anti_tailoring_status",
        ]
        for field in required_statuses:
            self.assertIn(field, receipt)
            self.assertIn(
                receipt[field]["status"],
                {"used", "skipped", "blocked", "failed"},
            )
            self.assertTrue(receipt[field]["reason"])
        self.assertEqual(receipt["context_router_status"]["status"], "used")
        self.assertEqual(receipt["searxng_status"]["status"], "skipped")
        self.assertEqual(
            receipt["searxng_status"]["reason"],
            "fip0_foundation_only_live_searxng_not_wired_until_fip2",
        )
        self.assertNotIn("searxng_status", receipt["used_sources"])
        self.assertEqual(receipt["coder_received_packet_hash"], "")
        self.assertEqual(receipt["qwen_coder_status"]["status"], "skipped")
        self.assertEqual(
            receipt["qwen_coder_status"]["reason"],
            "fip0_receipt_foundation_does_not_activate_qwen_coder",
        )
        self.assertIn(
            receipt["final_verdict"],
            {
                "GO: fip0_receipt_foundation_complete_runtime_lanes_not_yet_wired",
                "GO: fip1_context_lanes_integrated_runtime_future_lanes_not_wired",
                "NO-GO",
                "CONFIG-BLOCKED",
            },
        )

    def test_prompt_packet_wires_fip1_approved_context_lanes_into_receipt(self) -> None:
        client = self._client()

        def packet(source: str, status: str, reason: str) -> SimpleNamespace:
            return SimpleNamespace(
                to_dict=lambda: {
                    "source": source,
                    "status": status,
                    "reason": reason,
                    "packet": {"summary": f"{source} context"},
                    "diagnostics": {"read_only": True},
                    "authority": {"can_apply": False, "can_commit": False, "can_push": False},
                }
            )

        with (
            patch.dict(os.environ, {"SOURCE_PROXY_FIP1_CONTEXT_ENABLED": "1"}, clear=False),
            patch(
                "source_proxy.api.decision.build_cartographer_context_packet",
                return_value=packet("cartographer", "used", "cartographer_packet_ready"),
            ),
            patch(
                "source_proxy.api.decision.build_obsidian_context_packet",
                return_value=packet("obsidian", "skipped", "disabled"),
            ),
            patch(
                "source_proxy.api.decision.build_design_context_packet",
                return_value=packet("design", "used", "design_context_ready"),
            ),
        ):
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": "Wire FIP-1 context lanes into prompt packet truth receipt.",
                    "needs_codebase_context": True,
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        receipt = payload["fip0_truth_receipt"]
        self.assertEqual(receipt["cartographer_status"]["status"], "used")
        self.assertEqual(receipt["obsidian_status"]["status"], "skipped")
        self.assertEqual(receipt["design_status"]["status"], "used")
        self.assertEqual(receipt["mac_worker_status"]["status"], "skipped")
        self.assertEqual(
            receipt["mac_worker_status"]["reason"],
            "fip1_advisory_status_only_no_worker_invocation",
        )
        self.assertEqual(receipt["source_readiness_status"]["status"], "used")
        self.assertEqual(receipt["searxng_status"]["status"], "skipped")
        self.assertFalse(receipt["fip1_context_packet"]["scout_invoked"])
        self.assertFalse(receipt["fip1_context_packet"]["live_searxng_invoked"])
        self.assertFalse(receipt["fip1_context_packet"]["tinyfish_invoked"])
        self.assertFalse(receipt["fip1_context_packet"]["xersearch_created"])
        self.assertIn("cartographer_status", receipt["used_sources"])
        self.assertIn("design_status", receipt["used_sources"])
        self.assertIn("source_readiness_status", receipt["used_sources"])
        self.assertNotIn("searxng_status", receipt["used_sources"])
        self.assertEqual(
            receipt["final_verdict"],
            "GO: fip1_context_lanes_integrated_runtime_future_lanes_not_wired",
        )

    def test_fip0_receipt_retrieval_routes_return_latest_and_by_run_id(self) -> None:
        client = self._client()
        created = client.post(
            "/v1/decisions/prompt-packet",
            json={
                "task": "Create a retrievable FIP-0 receipt for manual proof.",
                "needs_codebase_context": True,
                "allowed_files": ["docs/evidence/source-proxy-full-integration-pivot/master-plan.md"],
                "forbidden_files": [".env"],
            },
        )
        self.assertEqual(created.status_code, 200)
        created_payload = created.json()
        run_id = created_payload["fip0_truth_receipt"]["run_id"]

        latest = client.get("/v1/decisions/fip0-receipts/latest")
        self.assertEqual(latest.status_code, 200)
        latest_payload = latest.json()
        self.assertEqual(latest_payload["run_id"], run_id)
        self.assertEqual(latest_payload["receipt"]["run_id"], run_id)
        self.assertNotIn("raw_prompt", latest_payload["receipt"])
        self.assertTrue(latest_payload["final_packet_hash"])
        self.assertIn("coder_received_packet_hash", latest_payload)
        self.assertFalse(latest_payload["public_redaction_summary"]["private_access"])

        by_run = client.get(f"/v1/decisions/fip0-receipts/{run_id}")
        self.assertEqual(by_run.status_code, 200)
        by_run_payload = by_run.json()
        self.assertEqual(by_run_payload["run_id"], run_id)
        self.assertEqual(by_run_payload["receipt_path"], latest_payload["receipt_path"])

        bad = client.get("/v1/decisions/fip0-receipts/fip0-nothex")
        self.assertEqual(bad.status_code, 400)

    def test_fip0_receipt_private_fields_require_local_dev_token(self) -> None:
        client = self._client()
        receipt = {
            "run_id": "fip0-4444444444444444",
            "timestamp": "2026-06-16T12:00:00+00:00",
            "raw_prompt": "Target file: docs/private.txt\n\nDo private work.",
            "final_verdict": "NO-GO: proof",
            "fip4_qwen_coder_result": {"raw_output_excerpt": "model raw output"},
        }
        self._write_fip0_receipt(receipt)

        public = client.get("/v1/decisions/fip0-receipts/fip0-4444444444444444")
        self.assertEqual(public.status_code, 200, public.text)
        public_body = public.json()
        self.assertNotIn("raw_prompt", public_body["receipt"])
        self.assertNotIn("raw_output_excerpt", json.dumps(public_body))
        self.assertFalse(public_body["public_redaction_summary"]["private_access"])

        with patch.dict(os.environ, {"SOURCE_PROXY_LOCAL_DEV_TOKEN": "local-proof"}, clear=False):
            private = client.get(
                "/v1/decisions/fip0-receipts/fip0-4444444444444444",
                headers={"x-source-proxy-dev-token": "local-proof"},
            )
        self.assertEqual(private.status_code, 200, private.text)
        private_body = private.json()
        self.assertEqual(private_body["receipt"]["raw_prompt"], receipt["raw_prompt"])
        self.assertEqual(
            private_body["receipt"]["fip4_qwen_coder_result"]["raw_output_excerpt"],
            "model raw output",
        )
        self.assertTrue(private_body["public_redaction_summary"]["private_access"])

    def test_fip2_search_needed_receipt_uses_live_searxng_provider_call(self) -> None:
        client = self._client()
        searxng_packet = {
            "status": "used",
            "reason": "live_searxng_provider_query_executed",
            "query": "latest local search proof",
            "searxng_url": "http://127.0.0.1:8080",
            "searxng_format_json_status": "enabled",
            "searxng_latency_ms": 42,
            "searxng_result_count": 1,
            "searxng_sources": [
                {
                    "title": "Local result",
                    "url": "https://example.com/local",
                    "snippet": "Local SearXNG result.",
                    "source": "web",
                }
            ],
            "provider_call_made": True,
            "provider_errors": [],
        }
        scout_packet = {
            "status": "skipped",
            "reason": "scout_research_disabled",
            "scout_enabled": False,
            "scout_result_count": 0,
            "scout_sources": [],
            "provider_errors": [],
        }

        with (
            patch.dict(os.environ, {"SOURCE_PROXY_FIP2_RESEARCH_ENABLED": "1"}, clear=False),
            patch(
                "source_proxy.api.decision.run_repo_research_preview",
                return_value=[
                    {
                        "title": "Repo research",
                        "url": "repo://source_proxy/api/decision.py",
                        "snippet": "Repo context.",
                        "source": "repo",
                    }
                ],
            ),
            patch(
                "source_proxy.api.decision.run_scout_research_diagnostics",
                new=AsyncMock(return_value=scout_packet),
            ),
            patch(
                "source_proxy.api.decision.run_searxng_research_diagnostics",
                new=AsyncMock(return_value=searxng_packet),
            ) as searxng_mock,
        ):
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": "What are the latest local Source Proxy search changes?",
                    "needs_current_info": True,
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        searxng_mock.assert_awaited_once()
        receipt = response.json()["fip0_truth_receipt"]
        self.assertTrue(receipt["search_needed"])
        self.assertEqual(receipt["searxng_status"]["status"], "used")
        self.assertEqual(receipt["searxng_result_count"], 1)
        self.assertEqual(receipt["searxng_format_json_status"], "enabled")
        self.assertIn("searxng_status", receipt["used_sources"])
        self.assertEqual(receipt["repo_research_status"]["status"], "used")
        self.assertNotEqual(receipt["repo_research_status"]["reason"], receipt["searxng_status"]["reason"])
        self.assertEqual(receipt["qwen_coder_status"]["status"], "skipped")
        self.assertEqual(receipt["coder_received_packet_hash"], "")
        self.assertEqual(
            receipt["tinyfish_status"]["reason"],
            "deferred_cloud_requires_britton_approval",
        )
        self.assertEqual(
            receipt["xersearch_status"]["reason"],
            "missing_alias_do_not_create",
        )
        self.assertTrue(receipt["research_packet_hash"])
        self.assertTrue(receipt["research_packet_included_in_context"])

    def test_fip2_no_search_needed_receipt_skips_searxng(self) -> None:
        client = self._client()
        with (
            patch.dict(os.environ, {"SOURCE_PROXY_FIP2_RESEARCH_ENABLED": "1"}, clear=False),
            patch(
                "source_proxy.api.decision.run_searxng_research_diagnostics",
                new=AsyncMock(),
            ) as searxng_mock,
        ):
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": "Summarize this stable local prompt."},
            )

        self.assertEqual(response.status_code, 200, response.text)
        searxng_mock.assert_not_awaited()
        receipt = response.json()["fip0_truth_receipt"]
        self.assertFalse(receipt["search_needed"])
        self.assertEqual(receipt["searxng_status"]["status"], "skipped")
        self.assertEqual(receipt["searxng_result_count"], 0)
        self.assertNotIn("searxng_status", receipt["used_sources"])

    def test_fip2_repo_first_research_does_not_force_live_searxng(self) -> None:
        with (
            patch.dict(os.environ, {"SOURCE_PROXY_FIP2_RESEARCH_ENABLED": "1"}, clear=False),
            patch(
                "source_proxy.api.decision.run_repo_research_preview",
                return_value=[
                    {
                        "title": "Repo result",
                        "url": "repo://docs/fip4-runtime-target.txt",
                        "snippet": "Repo-only context.",
                        "source": "repo",
                    }
                ],
            ),
            patch(
                "source_proxy.api.decision.run_searxng_research_diagnostics",
                new=AsyncMock(),
            ) as searxng_mock,
            patch(
                "source_proxy.api.decision.run_scout_research_diagnostics",
                new=AsyncMock(),
            ) as scout_mock,
        ):
            packet = asyncio.run(
                _build_fip2_research_packet(
                    task="Target file: docs/fip4-runtime-target.txt",
                    route_payload={"research_recommended": True},
                    route_reasons=["repo_first_research"],
                )
            )

        searxng_mock.assert_not_awaited()
        scout_mock.assert_not_awaited()
        self.assertFalse(packet["search_needed"])
        self.assertEqual(
            packet["search_reason"],
            "context_router_repo_first_research_local_only",
        )
        self.assertEqual(packet["searxng"]["status"], "skipped")
        self.assertEqual(packet["repo_result_count"], 1)

    def test_fip3_model_lanes_write_gemma_hermes_receipt_without_qwen(self) -> None:
        client = self._client()
        fip3_packet = {
            "packet_version": "source-proxy-fip3-local-model-lanes-v0.1",
            "gemma": {
                "status": "used",
                "reason": "local_ollama_model_json_schema_valid",
                "model": "gemma3n:e4b",
                "prompt_hash": "gemma-prompt",
                "output_hash": "gemma-output",
                "output_schema_valid": True,
                "intent": "Summarize the stable prompt",
                "normalized_spec": "Return a concise prompt packet.",
                "context_needed": True,
                "search_needed_review": False,
                "acceptance_criteria": ["Receipt includes context lane status."],
                "provider_errors": [],
            },
            "hermes_critic": {
                "status": "used",
                "reason": "local_ollama_model_json_schema_valid",
                "model": "hermes4:latest",
                "prompt_hash": "hermes-prompt",
                "output_hash": "hermes-output",
                "output_schema_valid": True,
                "ambiguities": ["No target file is specified."],
                "risks": ["Do not activate coder lanes."],
                "requirement_conflicts": [],
                "pre_coder_notes": ["Qwen remains skipped."],
                "provider_errors": [],
            },
            "hermes_verifier": {
                "status": "skipped",
                "reason": "hermes_verifier_role_reserved_for_future_fip5_not_authoritative",
                "model": "hermes4:latest",
                "role_reserved": True,
                "authority": "future_fip5_necessary_not_sufficient",
            },
            "model_route_truth": {
                "local_ollama_only": True,
                "qwen_pre_coder_reasoning_used": False,
                "fallback_to_qwen_attempted": False,
                "cloud_provider_used": False,
            },
            "no_qwen_pre_coder_reasoning": True,
            "fip3_model_packet_hash": "fip3-hash",
        }

        with (
            patch.dict(os.environ, {"SOURCE_PROXY_FIP3_MODEL_LANES_ENABLED": "1"}, clear=False),
            patch(
                "source_proxy.api.decision.build_fip3_model_lane_packet",
                new=AsyncMock(return_value=fip3_packet),
            ),
        ):
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": "Summarize this stable local prompt."},
            )

        self.assertEqual(response.status_code, 200, response.text)
        receipt = response.json()["fip0_truth_receipt"]
        self.assertEqual(receipt["gemma_status"]["status"], "used")
        self.assertEqual(receipt["gemma_model"], "gemma3n:e4b")
        self.assertTrue(receipt["gemma_output_schema_valid"])
        self.assertEqual(receipt["hermes_critic_status"]["status"], "used")
        self.assertEqual(receipt["hermes_critic_model"], "hermes4:latest")
        self.assertTrue(receipt["hermes_critic_output_schema_valid"])
        self.assertEqual(receipt["hermes_verifier_lane_status"]["status"], "skipped")
        self.assertTrue(receipt["hermes_verifier_role_reserved"])
        self.assertEqual(
            receipt["hermes_verifier_authority"],
            "future_fip5_necessary_not_sufficient",
        )
        self.assertTrue(receipt["no_qwen_pre_coder_reasoning"])
        self.assertEqual(receipt["qwen_coder_status"]["status"], "skipped")
        self.assertEqual(receipt["coder_received_packet_hash"], "")
        self.assertIn("gemma_status", receipt["used_sources"])
        self.assertIn("hermes_critic_status", receipt["used_sources"])
        self.assertEqual(
            receipt["final_verdict"],
            "GO: fip3_local_non_coding_model_lanes_runtime_future_lanes_not_wired",
        )

    def test_fip4_gemma_acceptance_criteria_parser_accepts_model_variants(self) -> None:
        normalized, errors = _normalize_gemma_output(
            {
                "intent": "code_generation",
                "normalized_spec": "Replace a target file.",
                "context_needed": False,
                "search_needed_review": False,
                "acceptance_criteria": [
                    {"criterion": "Target file content is updated."},
                    7,
                    "",
                ],
            }
        )

        self.assertEqual(errors, [])
        self.assertEqual(
            normalized["acceptance_criteria"],
            ["Target file content is updated.", "7"],
        )

        normalized_missing, missing_errors = _normalize_gemma_output(
            {
                "intent": "code_generation",
                "normalized_spec": "Replace a target file.",
                "context_needed": False,
                "search_needed_review": False,
            }
        )

        self.assertEqual(missing_errors, [])
        self.assertEqual(normalized_missing["acceptance_criteria"], [])

    def test_fip3_missing_model_is_config_blocked_not_stubbed(self) -> None:
        payload = _attach_fip0_truth_receipt(
            {},
            request=PromptPacketRequest(task="FIP-3 missing model proof"),
            route_payload={"recommended_route": "manual_route"},
            intake_payload={},
            decision=SimpleNamespace(research_sources=[]),
            explicit_target="",
            route_reasons=[],
            fip3_model_packet={
                "gemma": {
                    "status": "blocked",
                    "reason": "gemma_model_missing_from_local_ollama_inventory",
                    "model": "gemma3n:e4b",
                    "provider_errors": ["gemma3n:e4b not present in local Ollama inventory"],
                    "fix_command": "ssh source@10.0.0.186 'ollama pull gemma3n:e4b' # then restart npm run proxy:https:lan",
                },
                "hermes_critic": {
                    "status": "used",
                    "reason": "local_ollama_model_json_schema_valid",
                    "model": "hermes4:latest",
                    "output_schema_valid": True,
                    "provider_errors": [],
                },
                "hermes_verifier": {
                    "status": "skipped",
                    "reason": "hermes_verifier_role_reserved_for_future_fip5_not_authoritative",
                    "model": "hermes4:latest",
                    "role_reserved": True,
                    "authority": "future_fip5_necessary_not_sufficient",
                },
                "model_route_truth": {
                    "qwen_pre_coder_reasoning_used": False,
                    "fallback_to_qwen_attempted": False,
                },
                "no_qwen_pre_coder_reasoning": True,
            },
        )

        receipt = payload["fip0_truth_receipt"]
        self.assertEqual(receipt["gemma_status"]["status"], "blocked")
        self.assertIn("ollama pull gemma3n:e4b", receipt["gemma_status"]["fix_command"])
        self.assertEqual(
            receipt["final_verdict"],
            "CONFIG-BLOCKED: fip3_local_model_lane_unavailable",
        )

    def test_fip3_rejects_qwen_as_precoder_fallback(self) -> None:
        payload = _attach_fip0_truth_receipt(
            {},
            request=PromptPacketRequest(task="FIP-3 no Qwen fallback proof"),
            route_payload={"recommended_route": "manual_route"},
            intake_payload={},
            decision=SimpleNamespace(research_sources=[]),
            explicit_target="",
            route_reasons=[],
            fip3_model_packet={
                "gemma": {
                    "status": "used",
                    "reason": "local_ollama_model_json_schema_valid",
                    "model": "qwen2.5-coder:7b",
                    "output_schema_valid": True,
                    "provider_errors": [],
                },
                "hermes_critic": {
                    "status": "used",
                    "reason": "local_ollama_model_json_schema_valid",
                    "model": "hermes4:latest",
                    "output_schema_valid": True,
                    "provider_errors": [],
                },
                "hermes_verifier": {
                    "status": "skipped",
                    "reason": "hermes_verifier_role_reserved_for_future_fip5_not_authoritative",
                    "model": "hermes4:latest",
                    "role_reserved": True,
                    "authority": "future_fip5_necessary_not_sufficient",
                },
                "model_route_truth": {
                    "qwen_pre_coder_reasoning_used": True,
                    "fallback_to_qwen_attempted": True,
                },
                "no_qwen_pre_coder_reasoning": True,
            },
        )

        receipt = payload["fip0_truth_receipt"]
        self.assertEqual(receipt["gemma_status"]["status"], "failed")
        self.assertEqual(
            receipt["gemma_status"]["reason"],
            "fip3_qwen_precoder_fallback_disallowed",
        )
        self.assertEqual(receipt["qwen_coder_status"]["status"], "skipped")
        self.assertEqual(receipt["coder_received_packet_hash"], "")
        self.assertEqual(
            receipt["final_verdict"],
            "NO-GO: fip3_local_model_lane_failed",
        )

    def test_fip2_rejects_searxng_used_without_live_provider_call(self) -> None:
        payload = _attach_fip0_truth_receipt(
            {},
            request=PromptPacketRequest(task="latest proof"),
            route_payload={"recommended_route": "manual_route", "research_recommended": True},
            intake_payload={},
            decision=SimpleNamespace(research_sources=[]),
            explicit_target="",
            route_reasons=["needs_current_information"],
            fip2_research_packet={
                "search_needed": True,
                "search_reason": "test",
                "research_query": "latest proof",
                "research_sources": [],
                "repo_sources": [],
                "scout": {
                    "status": "skipped",
                    "reason": "scout_research_disabled",
                    "scout_enabled": False,
                    "scout_result_count": 0,
                    "scout_sources": [],
                    "provider_errors": [],
                },
                "searxng": {
                    "status": "used",
                    "reason": "live_searxng_provider_query_executed",
                    "provider_call_made": False,
                    "searxng_url": "http://127.0.0.1:8080",
                    "searxng_format_json_status": "enabled",
                    "searxng_latency_ms": 1,
                    "searxng_result_count": 1,
                    "searxng_sources": [{"source": "web"}],
                    "provider_errors": [],
                },
                "research_packet_hash": "hash",
                "research_packet_included_in_context": False,
            },
        )

        receipt = payload["fip0_truth_receipt"]
        self.assertEqual(receipt["searxng_status"]["status"], "failed")
        self.assertEqual(
            receipt["searxng_status"]["reason"],
            "searxng_marked_used_without_live_provider_call",
        )
        self.assertEqual(
            receipt["final_verdict"],
            "CONFIG-BLOCKED: fip2_local_searxng_not_available",
        )

    def test_fip2_search_needed_provider_blocked_is_config_blocked_with_fix(self) -> None:
        client = self._client()
        blocked = {
            "status": "blocked",
            "reason": "searxng_url_missing",
            "query": "latest local search proof",
            "searxng_url": "",
            "searxng_format_json_status": "not_checked",
            "searxng_latency_ms": None,
            "searxng_result_count": 0,
            "searxng_sources": [],
            "provider_call_made": False,
            "provider_errors": [],
            "fix_command": "Set SEARXNG_URL=http://127.0.0.1:8080 in config/source-proxy.env, then restart npm run proxy:https:lan.",
        }

        with (
            patch.dict(os.environ, {"SOURCE_PROXY_FIP2_RESEARCH_ENABLED": "1"}, clear=False),
            patch("source_proxy.api.decision.run_repo_research_preview", return_value=[]),
            patch(
                "source_proxy.api.decision.run_scout_research_diagnostics",
                new=AsyncMock(
                    return_value={
                        "status": "skipped",
                        "reason": "scout_research_disabled",
                        "scout_enabled": False,
                        "scout_result_count": 0,
                        "scout_sources": [],
                        "provider_errors": [],
                    }
                ),
            ),
            patch(
                "source_proxy.api.decision.run_searxng_research_diagnostics",
                new=AsyncMock(return_value=blocked),
            ),
        ):
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": "What are the latest local search changes?", "needs_current_info": True},
            )

        self.assertEqual(response.status_code, 200, response.text)
        receipt = response.json()["fip0_truth_receipt"]
        self.assertEqual(receipt["searxng_status"]["status"], "blocked")
        self.assertIn("SEARXNG_URL", receipt["searxng_status"]["fix_command"])
        self.assertEqual(
            receipt["final_verdict"],
            "CONFIG-BLOCKED: fip2_local_searxng_not_available",
        )

    def test_research_prompt_packet_endpoint_attaches_sources(self) -> None:
        client = self._client()
        sources = [
            {
                "title": "Vite 6.0 is out!",
                "url": "repo://docs/vite-notes.md",
                "snippet": "Vite 6 release notes.",
                "source": "repo",
            }
        ]

        with patch(
            "source_proxy.decision.router.run_local_research_preview",
            new=AsyncMock(return_value=sources),
        ):
            with patch.dict(os.environ, {"SPIRIT_ENABLE_PROXY_RESEARCH": "true"}, clear=False):
                response = client.post(
                    "/v1/decisions/prompt-packet",
                    json={"task": "What are the latest changes in Vite 6?"},
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["route_decision"]["research_recommended"])
        self.assertEqual(payload["research_sources"], sources)
        self.assertEqual(payload["route_decision"]["research_sources"], sources)
        receipt = payload["fip0_truth_receipt"]
        self.assertEqual(receipt["repo_research_status"]["status"], "used")
        self.assertEqual(
            receipt["repo_research_status"]["reason"],
            "repo_router_research_sources_present_not_live_searxng",
        )
        self.assertEqual(receipt["searxng_status"]["status"], "skipped")
        self.assertEqual(
            receipt["searxng_status"]["reason"],
            "fip0_foundation_only_live_searxng_not_wired_until_fip2",
        )
        self.assertIn("repo_research_status", receipt["used_sources"])
        self.assertNotIn("searxng_status", receipt["used_sources"])

    def test_fip0_receipt_marks_empty_coder_hash_failed_when_qwen_ran(self) -> None:
        payload = _attach_fip0_truth_receipt(
            {},
            request=PromptPacketRequest(task="Future coder packet proof"),
            route_payload={"recommended_route": "local_route"},
            intake_payload={},
            decision=SimpleNamespace(research_sources=[]),
            explicit_target="",
            route_reasons=[],
            provider_call_made=True,
            provider_model_truth={"providerCallMade": True},
        )

        receipt = payload["fip0_truth_receipt"]
        self.assertEqual(receipt["coder_received_packet_hash"], "")
        self.assertEqual(receipt["qwen_coder_status"]["status"], "failed")
        self.assertEqual(
            receipt["qwen_coder_status"]["reason"],
            "qwen_coder_provider_call_without_coder_packet_hash",
        )

    def test_fip4_qwen_receives_exact_final_coder_packet_hash(self) -> None:
        target = "source_proxy/tests/fip4-target-proof.txt"
        captured: dict[str, object] = {}

        def qwen_side_effect(final_packet: dict[str, object]) -> dict[str, object]:
            captured["packet"] = final_packet
            packet_hash = str(final_packet["final_packet_hash"])
            return {
                "status": "used",
                "reason": "qwen_received_final_coder_packet_and_returned_output",
                "model": "qwen2.5-coder:7b",
                "coder_received_packet_hash": packet_hash,
                "qwen_output_hash": "output-hash",
                "raw_output": json.dumps(
                    {
                        "action": "replace_file",
                        "target": target,
                        "content_lines": ["FIP-4 exact packet proof"],
                    }
                ),
                "provider_errors": [],
            }

        fip3_packet = {
            "gemma": {
                "status": "used",
                "reason": "local_ollama_model_json_schema_valid",
                "acceptance_criteria": ["Target file is changed."],
                "provider_errors": [],
            },
            "hermes_critic": {
                "status": "used",
                "reason": "local_ollama_model_json_schema_valid",
                "provider_errors": [],
            },
            "hermes_verifier": {
                "status": "skipped",
                "reason": "hermes_verifier_role_reserved_for_future_fip5_not_authoritative",
            },
            "fip3_model_packet_hash": "fip3-hash",
        }
        with patch("source_proxy.api.decision._fip4_call_qwen", side_effect=qwen_side_effect):
            result = _run_fip4_qwen_coder(
                request=PromptPacketRequest(
                    task=f"Target file: {target}\n\nWrite FIP-4 proof text.",
                    allowed_files=[target],
                    wants_implementation=True,
                ),
                trial_task=f"Target file: {target}\n\nWrite FIP-4 proof text.",
                explicit_target=target,
                intake_payload={"allowed_files": [target], "forbidden_files": [".env"]},
                route_payload={"recommended_route": "local_route"},
                route_reasons=[],
                fip1_context_packet={"sources": [], "source_status": {}},
                fip2_research_packet={"research_packet_hash": "research-hash"},
                fip3_model_packet=fip3_packet,
            )

        self.assertEqual(result["status"], "used")
        self.assertEqual(
            result["coder_received_packet_hash"],
            result["final_coder_packet_hash"],
        )
        self.assertEqual(result["changed_files"], [target])
        self.assertIn("FIP-4 exact packet proof", result["proposed_diff"])
        packet = captured["packet"]
        self.assertIsInstance(packet, dict)
        packet_dict = packet if isinstance(packet, dict) else {}
        self.assertEqual(packet_dict["raw_prompt"], f"Target file: {target}\n\nWrite FIP-4 proof text.")
        self.assertEqual(packet_dict["target_file"], target)
        self.assertIn(target, packet_dict["allowed_files"])
        self.assertIn("fip1_context_packet", packet_dict)
        self.assertEqual(packet_dict["fip2_research_packet"]["research_packet_hash"], "research-hash")
        self.assertEqual(
            packet_dict["fip3_gemma_output"]["acceptance_criteria"],
            ["Target file is changed."],
        )
        self.assertEqual(
            packet_dict["role_rules"]["qwen"],
            "coding/action output only",
        )
        self.assertTrue(packet_dict["output_contract_instructions"]["must_touch_only_allowed_files"])
        self.assertTrue(packet_dict["final_packet_hash"])

        payload = _attach_fip0_truth_receipt(
            {"fip4": "proof"},
            request=PromptPacketRequest(task="FIP-4 exact hash proof"),
            route_payload={"recommended_route": "local_route"},
            intake_payload={"allowed_files": [target], "forbidden_files": [".env"]},
            decision=SimpleNamespace(research_sources=[]),
            explicit_target=target,
            route_reasons=[],
            fip3_model_packet=fip3_packet,
            fip4_coder_result=result,
        )
        receipt = payload["fip0_truth_receipt"]
        self.assertEqual(receipt["qwen_coder_status"]["status"], "used")
        self.assertEqual(
            receipt["coder_received_packet_hash"],
            receipt["final_coder_packet_hash"],
        )
        self.assertEqual(
            receipt["final_verdict"],
            "GO: fip4_qwen_coding_only_execution_complete",
        )
        self.assertEqual(receipt["hermes_verifier_status"]["status"], "skipped")
        self.assertEqual(receipt["repair_loop_status"]["status"], "skipped")

    def test_fip4_qwen_cannot_run_without_final_coder_packet_target(self) -> None:
        client = self._client()
        with (
            patch.dict(
                os.environ,
                {
                    "SOURCE_PROXY_FIP4_QWEN_CODER_ENABLED": "1",
                    "SOURCE_PROXY_FIP3_MODEL_LANES_ENABLED": "0",
                },
                clear=False,
            ),
            patch("source_proxy.api.decision._fip4_call_qwen") as qwen_mock,
        ):
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={
                    "task": "Implement an unspecified change without naming any target file.",
                    "wants_implementation": True,
                },
            )

        self.assertEqual(response.status_code, 200, response.text)
        qwen_mock.assert_not_called()
        receipt = response.json()["fip0_truth_receipt"]
        self.assertEqual(receipt["qwen_coder_status"]["status"], "skipped")
        self.assertEqual(receipt["coder_received_packet_hash"], "")

    def test_fip4_does_not_start_fip5_from_fip5_env_alone(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SOURCE_PROXY_FIP5_VERIFIER_ENABLED": "1",
                "SOURCE_PROXY_FIP4_ALLOW_FIP5_CHAIN": "0",
            },
            clear=False,
        ):
            self.assertFalse(_fip4_allow_fip5_chain())
        with patch.dict(
            os.environ,
            {
                "SOURCE_PROXY_FIP5_VERIFIER_ENABLED": "1",
                "SOURCE_PROXY_FIP4_ALLOW_FIP5_CHAIN": "1",
            },
            clear=False,
        ):
            self.assertTrue(_fip4_allow_fip5_chain())

    def test_fip4_qwen_defaults_allow_slow_local_ollama(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SOURCE_PROXY_FIP4_QWEN_TIMEOUT_SECONDS": "",
                "SOURCE_PROXY_FIP4_QWEN_MAX_ATTEMPTS": "",
            },
            clear=False,
        ):
            self.assertEqual(_fip4_call_timeout_seconds(), 300.0)
            self.assertEqual(_fip4_qwen_max_attempts(), 3)

    def test_fip4_qwen_config_caps_remain_bounded(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SOURCE_PROXY_FIP4_QWEN_TIMEOUT_SECONDS": "2000",
                "SOURCE_PROXY_FIP4_QWEN_MAX_ATTEMPTS": "99",
            },
            clear=False,
        ):
            self.assertEqual(_fip4_call_timeout_seconds(), 900.0)
            self.assertEqual(_fip4_qwen_max_attempts(), 3)

    def test_fip4_qwen_retries_empty_output_with_same_packet_hash(self) -> None:
        target = "source_proxy/tests/fip4-target-proof.txt"
        final_packet = {"target_file": target, "allowed_files": [target]}
        packet_hash = _json_hash(final_packet)

        class TagsResponse:
            def __enter__(self) -> "TagsResponse":
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def read(self) -> bytes:
                return json.dumps({"models": [{"name": "qwen2.5-coder:7b"}]}).encode()

        def call_once_side_effect(**kwargs: object) -> dict[str, object]:
            attempt = int(kwargs["attempt"])
            if attempt == 1:
                return {
                    "status": "failed",
                    "reason": "qwen_empty_model_output",
                    "attempt": attempt,
                    "model": "qwen2.5-coder:7b",
                    "coder_received_packet_hash": packet_hash,
                    "final_coder_packet_hash": packet_hash,
                    "raw_output": "",
                    "raw_output_length": 0,
                    "provider_errors": ["empty_qwen_output_before_parser"],
                }
            raw = json.dumps(
                {
                    "action": "replace_file",
                    "target": target,
                    "content_lines": ["retry worked"],
                }
            )
            return {
                "status": "used",
                "reason": "qwen_received_final_coder_packet_and_returned_output",
                "attempt": attempt,
                "model": "qwen2.5-coder:7b",
                "coder_received_packet_hash": packet_hash,
                "final_coder_packet_hash": packet_hash,
                "qwen_output_hash": _json_hash(raw),
                "raw_output": raw,
                "raw_output_length": len(raw),
                "provider_errors": [],
            }

        with (
            patch.dict(os.environ, {"SOURCE_PROXY_FIP4_QWEN_MAX_ATTEMPTS": "2"}),
            patch("source_proxy.api.decision.urllib.request.urlopen", return_value=TagsResponse()),
            patch("source_proxy.api.decision._fip4_call_qwen_once", side_effect=call_once_side_effect),
        ):
            result = _fip4_call_qwen(final_packet)

        self.assertEqual(result["status"], "used")
        self.assertEqual(result["attempt_count"], 2)
        self.assertTrue(result["retry_attempted"])
        self.assertEqual(result["retry_reason"], "qwen_empty_model_output")
        self.assertEqual(result["coder_received_packet_hash"], packet_hash)
        self.assertEqual(
            [attempt["coder_received_packet_hash"] for attempt in result["attempts"]],
            [packet_hash, packet_hash],
        )

    def test_fip4_qwen_records_exhausted_timeout_attempts(self) -> None:
        final_packet = {"target_file": "source_proxy/tests/fip4-target-proof.txt"}
        packet_hash = _json_hash(final_packet)

        class TagsResponse:
            def __enter__(self) -> "TagsResponse":
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def read(self) -> bytes:
                return json.dumps({"models": [{"name": "qwen2.5-coder:7b"}]}).encode()

        def timeout_side_effect(**kwargs: object) -> dict[str, object]:
            attempt = int(kwargs["attempt"])
            return {
                "status": "failed",
                "reason": "qwen_coder_timeout",
                "attempt": attempt,
                "model": "qwen2.5-coder:7b",
                "coder_received_packet_hash": packet_hash,
                "final_coder_packet_hash": packet_hash,
                "latency_ms": 120000,
                "timeout_seconds": 120.0,
                "provider_errors": ["TimeoutError: timed out"],
            }

        with (
            patch.dict(os.environ, {"SOURCE_PROXY_FIP4_QWEN_MAX_ATTEMPTS": "2"}),
            patch("source_proxy.api.decision.urllib.request.urlopen", return_value=TagsResponse()),
            patch("source_proxy.api.decision._fip4_call_qwen_once", side_effect=timeout_side_effect),
        ):
            result = _fip4_call_qwen(final_packet)

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "qwen_coder_timeout")
        self.assertEqual(result["attempt_count"], 2)
        self.assertEqual(result["coder_received_packet_hash"], packet_hash)
        self.assertEqual(result["attempts"][0]["timeout_seconds"], 120.0)

    def test_fip4_malformed_qwen_output_is_rejected_after_format_retry(self) -> None:
        target = "source_proxy/tests/fip4-target-proof.txt"

        def qwen_side_effect(final_packet: dict[str, object]) -> dict[str, object]:
            packet_hash = str(final_packet["final_packet_hash"])
            return {
                "status": "used",
                "reason": "qwen_received_final_coder_packet_and_returned_output",
                "model": "qwen2.5-coder:7b",
                "coder_received_packet_hash": packet_hash,
                "final_coder_packet_hash": packet_hash,
                "qwen_output_hash": "first-malformed-output",
                "raw_output": "I would update the file, but here is prose instead.",
                "provider_errors": [],
            }

        def retry_side_effect(
            *,
            final_packet: dict[str, object],
            previous_qwen: dict[str, object],
            previous_parse_meta: dict[str, object],
        ) -> dict[str, object]:
            packet_hash = str(final_packet["final_packet_hash"])
            return {
                "status": "used",
                "reason": "qwen_received_final_coder_packet_and_returned_output",
                "model": "qwen2.5-coder:7b",
                "coder_received_packet_hash": packet_hash,
                "final_coder_packet_hash": packet_hash,
                "qwen_output_hash": "retry-malformed-output",
                "raw_output": "Still prose, still not an action.",
                "same_final_coder_packet_hash": True,
                "provider_errors": [],
            }

        with (
            patch("source_proxy.api.decision._fip4_call_qwen", side_effect=qwen_side_effect),
            patch(
                "source_proxy.api.decision._fip4_call_qwen_output_contract_retry",
                side_effect=retry_side_effect,
            ),
        ):
            result = _run_fip4_qwen_coder(
                request=PromptPacketRequest(
                    task=f"Target file: {target}\n\nReturn malformed output.",
                    allowed_files=[target],
                    wants_implementation=True,
                ),
                trial_task=f"Target file: {target}\n\nReturn malformed output.",
                explicit_target=target,
                intake_payload={"allowed_files": [target], "forbidden_files": []},
                route_payload={"recommended_route": "local_route"},
                route_reasons=[],
                fip1_context_packet={"sources": [], "source_status": {}},
                fip2_research_packet={},
                fip3_model_packet={},
            )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "qwen_output_contract_rejected")
        self.assertEqual(result["changed_files"], [])
        self.assertEqual(result["proposed_diff"], "")
        self.assertEqual(result["qwen_output_contract_retry"]["status"], "used")
        self.assertEqual(
            result["qwen_output_contract_retry"]["previous_parse_error"],
            "no_action_json_or_file_block",
        )
        self.assertTrue(result["qwen_output_contract_retry"]["same_final_coder_packet_hash"])
        self.assertTrue(result["qwen"]["retry_attempted"])
        self.assertEqual(result["qwen"]["retry_reason"], "qwen_output_contract_rejected")

    def test_fip4_malformed_qwen_output_retry_accepts_same_packet_hash(self) -> None:
        target = "source_proxy/tests/fip4-target-proof.txt"
        replacement = "FIP-4 output-contract retry proof."

        def qwen_side_effect(final_packet: dict[str, object]) -> dict[str, object]:
            packet_hash = str(final_packet["final_packet_hash"])
            return {
                "status": "used",
                "reason": "qwen_received_final_coder_packet_and_returned_output",
                "model": "qwen2.5-coder:7b",
                "coder_received_packet_hash": packet_hash,
                "final_coder_packet_hash": packet_hash,
                "qwen_output_hash": "first-malformed-output",
                "raw_output": "### Recommendation\nUse implementation advice instead of JSON.",
                "provider_errors": [],
            }

        def retry_side_effect(
            *,
            final_packet: dict[str, object],
            previous_qwen: dict[str, object],
            previous_parse_meta: dict[str, object],
        ) -> dict[str, object]:
            packet_hash = str(final_packet["final_packet_hash"])
            return {
                "status": "used",
                "reason": "qwen_received_final_coder_packet_and_returned_output",
                "model": "qwen2.5-coder:7b",
                "coder_received_packet_hash": packet_hash,
                "final_coder_packet_hash": packet_hash,
                "qwen_output_hash": "retry-valid-output",
                "raw_output": json.dumps(
                    {
                        "action": "replace_file",
                        "target": target,
                        "content_lines": [replacement],
                    }
                ),
                "same_final_coder_packet_hash": True,
                "provider_errors": [],
            }

        with (
            patch("source_proxy.api.decision._fip4_call_qwen", side_effect=qwen_side_effect),
            patch(
                "source_proxy.api.decision._fip4_call_qwen_output_contract_retry",
                side_effect=retry_side_effect,
            ),
        ):
            result = _run_fip4_qwen_coder(
                request=PromptPacketRequest(
                    task=f"Target file: {target}\n\nReplace with exactly this content: {replacement}",
                    allowed_files=[target],
                    wants_implementation=True,
                ),
                trial_task=f"Target file: {target}\n\nReplace with exactly this content: {replacement}",
                explicit_target=target,
                intake_payload={"allowed_files": [target], "forbidden_files": []},
                route_payload={"recommended_route": "local_route"},
                route_reasons=[],
                fip1_context_packet={"sources": [], "source_status": {}},
                fip2_research_packet={},
                fip3_model_packet={},
            )

        self.assertEqual(result["status"], "used")
        self.assertEqual(result["reason"], "fip4_qwen_action_output_parsed_and_diff_generated")
        self.assertEqual(result["changed_files"], [target])
        self.assertIn(replacement, result["proposed_diff"])
        self.assertEqual(result["parser"]["parsed_output_mode"], "json_content_lines")
        self.assertEqual(result["final_coder_packet_hash"], result["coder_received_packet_hash"])
        self.assertEqual(result["qwen_output_contract_retry"]["status"], "used")
        self.assertTrue(result["qwen_output_contract_retry"]["same_final_coder_packet_hash"])
        self.assertTrue(result["qwen"]["retry_attempted"])
        self.assertEqual(result["qwen"]["attempt_count"], 2)

    def test_fip4_wrong_or_protected_file_is_blocked(self) -> None:
        allowed_target = "source_proxy/tests/fip4-target-proof.txt"

        def qwen_side_effect(final_packet: dict[str, object]) -> dict[str, object]:
            return {
                "status": "used",
                "reason": "qwen_received_final_coder_packet_and_returned_output",
                "model": "qwen2.5-coder:7b",
                "coder_received_packet_hash": str(final_packet["final_packet_hash"]),
                "raw_output": json.dumps(
                    {
                        "action": "replace_file",
                        "target": ".env",
                        "content": "SECRET=bad",
                    }
                ),
                "provider_errors": [],
            }

        with patch("source_proxy.api.decision._fip4_call_qwen", side_effect=qwen_side_effect):
            result = _run_fip4_qwen_coder(
                request=PromptPacketRequest(
                    task=f"Target file: {allowed_target}\n\nTry to touch a protected file.",
                    allowed_files=[allowed_target],
                    forbidden_files=[".env"],
                    wants_implementation=True,
                ),
                trial_task=f"Target file: {allowed_target}\n\nTry to touch a protected file.",
                explicit_target=allowed_target,
                intake_payload={"allowed_files": [allowed_target], "forbidden_files": [".env"]},
                route_payload={"recommended_route": "local_route"},
                route_reasons=[],
                fip1_context_packet={"sources": [], "source_status": {}},
                fip2_research_packet={},
                fip3_model_packet={},
            )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "target_not_in_allowed_files")
        self.assertEqual(result["changed_files"], [])
        self.assertEqual(result["proposed_diff"], "")

    def test_fip5_clean_pass_writes_required_verifier_receipt_fields(self) -> None:
        target = "source_proxy/tests/fip5-target-proof.txt"
        fip4_result = {
            "status": "used",
            "reason": "fip4_qwen_action_output_parsed_and_diff_generated",
            "final_coder_packet_hash": "packet-hash",
            "coder_received_packet_hash": "packet-hash",
            "parser": {"parsed_output_mode": "json_content_lines", "parse_error": ""},
            "allowed_files": [target],
            "forbidden_files": [".env"],
            "changed_files": [target],
            "action": {"target": target, "content": "FIP-5 clean pass proof."},
            "proposed_diff": "--- a/x\n+++ b/x\n@@\n-proof\n+FIP-5 clean pass proof.\n",
            "qwen": {"qwen_output_hash": "qwen-output"},
            "final_coder_packet": {"target_file": target},
        }
        with patch(
            "source_proxy.api.decision._fip5_call_hermes_verifier",
            return_value={
                "status": "used",
                "reason": "hermes_verifier_schema_valid",
                "model": "hermes3:8b-abliterated",
                "role": "post_code_verifier",
                "prompt_hash": "prompt-hash",
                "output_hash": "output-hash",
                "schema_valid": True,
                "verdict": "PASS",
                "repair_instructions": [],
            },
        ):
            fip5 = _run_fip5_verifier_and_repair(
                request=PromptPacketRequest(
                    task="Target file: source_proxy/tests/fip5-target-proof.txt\n\nReplace the file with exactly this content: FIP-5 clean pass proof.",
                    allowed_files=[target],
                ),
                explicit_target=target,
                fip4_result=fip4_result,
            )
        payload = _attach_fip0_truth_receipt(
            {"fip5": "proof"},
            request=PromptPacketRequest(task="FIP-5 clean pass proof"),
            route_payload={"recommended_route": "local_route"},
            intake_payload={"allowed_files": [target], "forbidden_files": [".env"]},
            decision=SimpleNamespace(research_sources=[]),
            explicit_target=target,
            route_reasons=[],
            fip4_coder_result=fip4_result,
            fip5_verifier_result=fip5,
        )
        receipt = payload["fip0_truth_receipt"]
        self.assertEqual(receipt["final_verdict"], "GO: fip5_required_verifier_and_repair_complete")
        self.assertEqual(receipt["deterministic_verifier_status"]["status"], "used")
        self.assertEqual(receipt["deterministic_failures"], [])
        self.assertEqual(receipt["hermes_verifier_status"]["status"], "used")
        self.assertEqual(receipt["hermes_verifier_role"], "post_code_verifier")
        self.assertTrue(receipt["hermes_verifier_schema_valid"])
        self.assertTrue(receipt["cannot_turn_unverified_into_pass"])
        self.assertTrue(receipt["cannot_override_browser_behavior"])
        self.assertEqual(receipt["repair_loop_status"]["status"], "skipped")
        self.assertFalse(receipt["productive"])
        self.assertEqual(receipt["coder_path"], "fip4_real")
        self.assertEqual(
            receipt["verification_real"],
            {
                "deterministic": True,
                "browser": False,
                "functional": False,
                "behavior": False,
                "hermes": True,
            },
        )
        self.assertEqual(
            receipt["verification_real_reasons"]["functional"],
            "functional_verifier_skipped_unsupported_extension",
        )
        self.assertEqual(receipt["degraded_lanes"], [])

    def test_html_receipt_is_unproductive_without_real_browser_verification(self) -> None:
        target = "docs/evidence/source-proxy-claude-3x10-audit-20260615/targets/set1/page.html"
        fip4_result = {
            "status": "used",
            "reason": "fip4_qwen_action_output_parsed_and_diff_generated",
            "final_coder_packet_hash": "packet-hash",
            "coder_received_packet_hash": "packet-hash",
            "parser": {"parsed_output_mode": "json_replace_file", "parse_error": ""},
            "allowed_files": [target],
            "forbidden_files": [".env"],
            "changed_files": [target],
            "proposed_diff": "--- a/page.html\n+++ b/page.html\n@@\n-old\n+<main>proof</main>\n",
            "qwen": {"qwen_output_hash": "qwen-output"},
            "final_coder_packet": {"target_file": target},
        }
        fip5 = {
            "final_verdict": "NO-GO: fip5_browser_behavior_authority_blocks_pass",
            "deterministic": {
                "status": "used",
                "reason": "deterministic_passed",
                "passed": True,
                "checks_run": ["content_exact_match"],
                "failures": [],
            },
            "browser": {
                "status": "skipped",
                "reason": "browser_verifier_not_enabled_phase_a",
                "passed": False,
                "authoritative": True,
            },
            "hermes": {
                "status": "used",
                "reason": "schema_valid",
                "schema_valid": True,
                "verdict": "PASS",
            },
            "repair_loop_status": {"status": "skipped", "reason": "browser_required"},
            "repair_attempt_count": 0,
            "repair_max_attempts": 0,
        }
        payload = _attach_fip0_truth_receipt(
            {"fip5": "html-proof"},
            request=PromptPacketRequest(task="HTML proof"),
            route_payload={"recommended_route": "local_route"},
            intake_payload={"allowed_files": [target], "forbidden_files": [".env"]},
            decision=SimpleNamespace(research_sources=[]),
            explicit_target=target,
            route_reasons=[],
            fip4_coder_result=fip4_result,
            fip5_verifier_result=fip5,
        )
        receipt = payload["fip0_truth_receipt"]
        self.assertFalse(receipt["productive"])
        self.assertEqual(receipt["coder_path"], "fip4_real")
        self.assertFalse(receipt["verification_real"]["browser"])
        self.assertTrue(receipt["verification_real"]["deterministic"])
        self.assertFalse(receipt["verification_real"]["functional"])
        self.assertFalse(receipt["verification_real"]["behavior"])
        self.assertEqual(receipt["browser_verifier_status"]["status"], "skipped")
        self.assertEqual(
            receipt["verification_real_reasons"]["functional"],
            "functional_verifier_skipped_no_supported_contract",
        )

    def test_functional_verification_is_false_when_lane_missing(self) -> None:
        target = "source_proxy/tests/fip5-target-proof.txt"
        fip4_result = {
            "status": "used",
            "reason": "fip4_qwen_action_output_parsed_and_diff_generated",
            "final_coder_packet_hash": "packet-hash",
            "coder_received_packet_hash": "packet-hash",
            "parser": {"parsed_output_mode": "json_content_lines", "parse_error": ""},
            "allowed_files": [target],
            "forbidden_files": [".env"],
            "changed_files": [target],
            "proposed_diff": "--- a/x\n+++ b/x\n@@\n-old\n+new\n",
            "qwen": {"qwen_output_hash": "qwen-output"},
            "final_coder_packet": {"target_file": target},
        }
        payload = _attach_fip0_truth_receipt(
            {"fip4": "functional-missing-proof"},
            request=PromptPacketRequest(task="Functional truth proof"),
            route_payload={"recommended_route": "local_route"},
            intake_payload={"allowed_files": [target], "forbidden_files": [".env"]},
            decision=SimpleNamespace(research_sources=[]),
            explicit_target=target,
            route_reasons=[],
            fip4_coder_result=fip4_result,
        )
        receipt = payload["fip0_truth_receipt"]
        self.assertFalse(receipt["verification_real"]["functional"])
        self.assertEqual(
            receipt["verification_real_reasons"]["functional"],
            "functional_verifier_not_implemented",
        )
        self.assertFalse(receipt["productive"])

    def test_functional_verification_is_false_when_verifier_skips(self) -> None:
        target = "source_proxy/tests/fip5-target-proof.txt"
        fip4_result = {
            "status": "used",
            "reason": "fip4_qwen_action_output_parsed_and_diff_generated",
            "final_coder_packet_hash": "packet-hash",
            "coder_received_packet_hash": "packet-hash",
            "parser": {"parsed_output_mode": "json_content_lines", "parse_error": ""},
            "allowed_files": [target],
            "forbidden_files": [".env"],
            "changed_files": [target],
            "action": {"target": target, "content": "plain text, not executable"},
            "proposed_diff": "--- a/x\n+++ b/x\n@@\n-old\n+plain text\n",
            "qwen": {"qwen_output_hash": "qwen-output"},
            "final_coder_packet": {"target_file": target},
        }
        skipped = _fip5_functional_verifier(
            request=PromptPacketRequest(task=f"Target file: {target}\n\nWrite plain text."),
            explicit_target=target,
            fip4_result=fip4_result,
        )
        self.assertEqual(skipped["status"], "skipped")
        self.assertFalse(skipped["passed"])
        self.assertEqual(skipped["reason"], "functional_verifier_skipped_unsupported_extension")

    def test_functional_verification_true_only_when_lane_used_and_passed(self) -> None:
        target = "docs/evidence/source-proxy-claude-3x10-audit-20260615/targets/unit/add.js"
        content = "export function add(a, b) { return Number(a) + Number(b); }\n"
        fip4_result = {
            "status": "used",
            "reason": "fip4_qwen_action_output_parsed_and_diff_generated",
            "final_coder_packet_hash": "packet-hash",
            "coder_received_packet_hash": "packet-hash",
            "parser": {"parsed_output_mode": "json_replace_file", "parse_error": ""},
            "allowed_files": [target],
            "forbidden_files": [".env"],
            "changed_files": [target],
            "action": {"target": target, "content": content},
            "proposed_diff": "--- a/add.js\n+++ b/add.js\n@@\n-old\n+export function add(a, b) { return Number(a) + Number(b); }\n",
            "qwen": {"qwen_output_hash": "qwen-output"},
            "final_coder_packet": {"target_file": target},
        }
        functional = _fip5_functional_verifier(
            request=PromptPacketRequest(task=f"Target file: {target}\n\nMake a calculator helper function."),
            explicit_target=target,
            fip4_result=fip4_result,
        )
        self.assertEqual(functional["status"], "used")
        self.assertTrue(functional["passed"])
        fip5 = {
            "final_verdict": "GO: fip5_required_verifier_and_repair_complete",
            "deterministic": {"status": "used", "reason": "passed", "passed": True},
            "browser": {"status": "skipped", "reason": "not_html", "passed": True},
            "functional": functional,
            "hermes": {"status": "used", "reason": "schema_valid", "verdict": "PASS"},
            "repair_loop_status": {"status": "skipped", "reason": "not_needed"},
        }
        payload = _attach_fip0_truth_receipt(
            {"fip5": "functional-proof"},
            request=PromptPacketRequest(task="Functional truth proof"),
            route_payload={"recommended_route": "local_route"},
            intake_payload={"allowed_files": [target], "forbidden_files": [".env"]},
            decision=SimpleNamespace(research_sources=[]),
            explicit_target=target,
            route_reasons=[],
            fip4_coder_result=fip4_result,
            fip5_verifier_result=fip5,
        )
        receipt = payload["fip0_truth_receipt"]
        self.assertTrue(receipt["verification_real"]["functional"])
        self.assertTrue(receipt["verification_real"]["behavior"])
        self.assertEqual(receipt["functional_verifier_status"]["status"], "used")
        self.assertTrue(receipt["functional_verifier_status"]["passed"])
        self.assertTrue(receipt["productive"])

    def test_browser_verification_true_only_when_lane_used_and_passed(self) -> None:
        target = "docs/evidence/source-proxy-claude-3x10-audit-20260615/targets/unit/page.html"
        fip4_result = {
            "status": "used",
            "reason": "fip4_qwen_action_output_parsed_and_diff_generated",
            "final_coder_packet_hash": "packet-hash",
            "coder_received_packet_hash": "packet-hash",
            "parser": {"parsed_output_mode": "json_replace_file", "parse_error": ""},
            "allowed_files": [target],
            "forbidden_files": [".env"],
            "changed_files": [target],
            "action": {"target": target, "content": "<main><h1>Browser proof</h1></main>"},
            "proposed_diff": "diff",
            "qwen": {"qwen_output_hash": "qwen-output"},
            "final_coder_packet": {"target_file": target},
        }
        fip5 = {
            "final_verdict": "GO: fip5_required_verifier_and_repair_complete",
            "deterministic": {"status": "used", "reason": "passed", "passed": True},
            "browser": {
                "status": "used",
                "reason": "browser_verifier_headless_page_passed",
                "passed": True,
                "checks": [{"name": "headless_browser_load", "passed": True}],
                "target_path": target,
                "timeout_ms": 10000,
                "verifier_version": "browser-verifier-v0",
                "browser_engine": "chromium",
            },
            "functional": {
                "status": "skipped",
                "reason": "functional_verifier_skipped_browser_or_ui_target",
                "passed": False,
            },
            "hermes": {"status": "used", "reason": "schema_valid", "verdict": "PASS"},
            "repair_loop_status": {"status": "skipped", "reason": "not_needed"},
        }
        payload = _attach_fip0_truth_receipt(
            {"fip5": "browser-proof"},
            request=PromptPacketRequest(task="Browser truth proof"),
            route_payload={"recommended_route": "local_route"},
            intake_payload={"allowed_files": [target], "forbidden_files": [".env"]},
            decision=SimpleNamespace(research_sources=[]),
            explicit_target=target,
            route_reasons=[],
            fip4_coder_result=fip4_result,
            fip5_verifier_result=fip5,
        )
        receipt = payload["fip0_truth_receipt"]
        self.assertTrue(receipt["verification_real"]["browser"])
        self.assertFalse(receipt["verification_real"]["functional"])
        self.assertTrue(receipt["verification_real"]["behavior"])
        self.assertTrue(receipt["productive"])
        self.assertEqual(receipt["browser_verifier_status"]["status"], "used")
        self.assertEqual(receipt["browser_verifier_target_path"], target)

    def test_static_html_without_browser_pass_is_not_productive(self) -> None:
        target = "docs/evidence/source-proxy-claude-3x10-audit-20260615/targets/unit/page.html"
        fip4_result = {
            "status": "used",
            "reason": "fip4_qwen_action_output_parsed_and_diff_generated",
            "final_coder_packet_hash": "packet-hash",
            "coder_received_packet_hash": "packet-hash",
            "parser": {"parsed_output_mode": "json_replace_file", "parse_error": ""},
            "allowed_files": [target],
            "forbidden_files": [".env"],
            "changed_files": [target],
            "action": {"target": target, "content": "<main>Static only</main>"},
            "proposed_diff": "diff",
            "qwen": {"qwen_output_hash": "qwen-output"},
            "final_coder_packet": {"target_file": target},
        }
        fip5 = {
            "final_verdict": "GO: fip5_required_verifier_and_repair_complete",
            "deterministic": {"status": "used", "reason": "passed", "passed": True},
            "browser": {
                "status": "skipped",
                "reason": "browser_verifier_skipped_unsupported_browser_target",
                "passed": False,
            },
            "functional": {
                "status": "skipped",
                "reason": "functional_verifier_skipped_browser_or_ui_target",
                "passed": False,
            },
            "hermes": {"status": "used", "reason": "schema_valid", "verdict": "PASS"},
            "repair_loop_status": {"status": "skipped", "reason": "not_needed"},
        }
        payload = _attach_fip0_truth_receipt(
            {"fip5": "static-html-proof"},
            request=PromptPacketRequest(task="Static-only HTML proof"),
            route_payload={"recommended_route": "local_route"},
            intake_payload={"allowed_files": [target], "forbidden_files": [".env"]},
            decision=SimpleNamespace(research_sources=[]),
            explicit_target=target,
            route_reasons=[],
            fip4_coder_result=fip4_result,
            fip5_verifier_result=fip5,
        )
        receipt = payload["fip0_truth_receipt"]
        self.assertFalse(receipt["verification_real"]["browser"])
        self.assertFalse(receipt["verification_real"]["behavior"])
        self.assertFalse(receipt["productive"])

    def test_synthetic_browser_pass_is_rejected_by_default(self) -> None:
        target = "docs/evidence/source-proxy-claude-3x10-audit-20260615/targets/unit/page.html"
        fip4_result = {
            "changed_files": [target],
            "allowed_files": [target],
        }
        with patch.dict(os.environ, {"SOURCE_PROXY_TRIAL_HARNESS_ONLY": "0"}, clear=False):
            browser = _fip5_browser_probe(
                request=PromptPacketRequest(
                    task=f"Target file: {target}\n\nMake a page.",
                    expected_result_state="browser_pass_expected",
                ),
                explicit_target=target,
                fip4_result=fip4_result,
            )
        self.assertEqual(browser["status"], "failed")
        self.assertFalse(browser["passed"])
        self.assertEqual(browser["reason"], "browser_behavior_synthetic_pass_rejected_default")

    def test_browser_verifier_skips_non_browser_targets_without_claiming_browser_truth(self) -> None:
        target = "docs/evidence/source-proxy-claude-3x10-audit-20260615/targets/unit/add.js"
        fip4_result = {
            "status": "used",
            "allowed_files": [target],
            "changed_files": [target],
            "action": {"target": target, "content": "export function add(a,b){return a+b;}"},
        }
        browser = _fip5_browser_verifier(
            request=PromptPacketRequest(task=f"Target file: {target}\n\nMake add helper."),
            explicit_target=target,
            fip4_result=fip4_result,
        )
        self.assertEqual(browser["status"], "skipped")
        self.assertEqual(browser["reason"], "browser_verifier_skipped_non_browser_target")
        self.assertTrue(browser["passed"])

    def test_browser_verifier_loads_generated_html_with_headless_browser(self) -> None:
        playwright_check = subprocess.run(
            ["node", "-e", "require.resolve('playwright');"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if playwright_check.returncode != 0:
            self.skipTest("playwright unavailable")
        target = "docs/evidence/source-proxy-claude-3x10-audit-20260615/targets/unit/browser-pass.html"
        fip4_result = {
            "status": "used",
            "allowed_files": [target],
            "changed_files": [target],
            "action": {
                "target": target,
                "content": "<!doctype html><html><body><main><h1>Headless proof</h1></main></body></html>",
            },
        }
        browser = _fip5_browser_verifier(
            request=PromptPacketRequest(task=f"Target file: {target}\n\nMake a visible page."),
            explicit_target=target,
            fip4_result=fip4_result,
        )
        self.assertEqual(browser["status"], "used")
        self.assertTrue(browser["passed"])
        self.assertEqual(browser["browser_engine"], "chromium")

    def test_functional_verifier_skips_browser_ui_tasks(self) -> None:
        target = "docs/evidence/source-proxy-claude-3x10-audit-20260615/targets/unit/page.html"
        fip4_result = {
            "status": "used",
            "reason": "fip4_qwen_action_output_parsed_and_diff_generated",
            "final_coder_packet_hash": "packet-hash",
            "coder_received_packet_hash": "packet-hash",
            "parser": {"parsed_output_mode": "json_replace_file", "parse_error": ""},
            "allowed_files": [target],
            "forbidden_files": [".env"],
            "changed_files": [target],
            "action": {"target": target, "content": "<button>Click</button>"},
            "proposed_diff": "--- a/page.html\n+++ b/page.html\n@@\n-old\n+<button>Click</button>\n",
            "qwen": {"qwen_output_hash": "qwen-output"},
            "final_coder_packet": {"target_file": target},
        }
        functional = _fip5_functional_verifier(
            request=PromptPacketRequest(task=f"Target file: {target}\n\nMake a signup page."),
            explicit_target=target,
            fip4_result=fip4_result,
        )
        self.assertEqual(functional["status"], "skipped")
        self.assertEqual(functional["reason"], "functional_verifier_skipped_browser_or_ui_target")
        self.assertFalse(functional["passed"])

    def test_required_lane_timeout_downgrades_go_verdict(self) -> None:
        target = "docs/fip5-target-proof.txt"
        fip4_result = {
            "status": "used",
            "reason": "fip4_qwen_action_output_parsed_and_diff_generated",
            "final_coder_packet_hash": "packet-hash",
            "coder_received_packet_hash": "packet-hash",
            "parser": {"parsed_output_mode": "json_content_lines", "parse_error": ""},
            "allowed_files": [target],
            "forbidden_files": [".env"],
            "changed_files": [target],
            "proposed_diff": "--- a/x\n+++ b/x\n@@\n-old\n+new\n",
            "qwen": {"qwen_output_hash": "qwen-output"},
            "final_coder_packet": {"target_file": target},
        }
        fip5 = {
            "final_verdict": "GO: fip5_required_verifier_and_repair_complete",
            "deterministic": {"status": "used", "reason": "passed", "passed": True},
            "browser": {"status": "skipped", "reason": "not_html", "passed": None},
            "hermes": {
                "status": "failed",
                "reason": "hermes_required_lane_timeout",
                "verdict": "UNVERIFIED",
            },
            "repair_loop_status": {"status": "skipped", "reason": "not_needed"},
        }
        payload = _attach_fip0_truth_receipt(
            {"fip5": "degraded-proof"},
            request=PromptPacketRequest(task="Forced Hermes timeout proof"),
            route_payload={"recommended_route": "local_route"},
            intake_payload={"allowed_files": [target], "forbidden_files": [".env"]},
            decision=SimpleNamespace(research_sources=[]),
            explicit_target=target,
            route_reasons=[],
            fip4_coder_result=fip4_result,
            fip5_verifier_result=fip5,
        )
        receipt = payload["fip0_truth_receipt"]
        self.assertEqual(receipt["final_verdict"], "NO-GO: expected_degraded_lane")
        self.assertFalse(receipt["productive"])
        self.assertEqual(receipt["degraded_lanes"][0]["lane"], "hermes_verifier")
        self.assertEqual(receipt["degraded_lanes"][0]["reason"], "hermes_required_lane_timeout")

    def test_trial_scaffold_paths_are_unreachable_without_harness_flag(self) -> None:
        async def run_case() -> dict[str, object]:
            with patch.dict(os.environ, {"SOURCE_PROXY_TRIAL_HARNESS_ONLY": ""}, clear=False):
                with patch(
                    "source_proxy.api.decision._deterministic_architect_plan_for_prompt_packet",
                    return_value={"target_file": "src/app/page.tsx"},
                ):
                    with patch(
                        "source_proxy.api.decision._propose_coder_via_executor",
                        new=AsyncMock(return_value={"reason_code": "real_executor_path"}),
                    ):
                        return await _bounded_coder_diff_or_stub(
                            "Target file: src/app/page.tsx\n\ninit a repo and make a homepage for my app",
                            force_live_model=True,
                        )

        result = asyncio.run(run_case())
        self.assertEqual(result["reason_code"], "real_executor_path")

    def test_fip5_hermes_verifier_accepts_valid_noop_pass_schema(self) -> None:
        normalized, errors = _fip5_normalize_hermes_verifier_output(
            {
                "verdict": "PASS",
                "reason": "already satisfied with deterministic evidence",
                "repair_instruction": "",
            },
            deterministic={"passed": True},
            browser={"passed": True},
        )

        self.assertEqual(errors, [])
        self.assertEqual(normalized["verdict"], "PASS")
        self.assertEqual(
            normalized["reasons"],
            ["already satisfied with deterministic evidence"],
        )
        self.assertEqual(normalized["repair_instructions"], [])

    def test_fip5_hermes_invalid_json_remains_config_blocked_after_retry(self) -> None:
        inventory = self._urlopen_json_response(
            {"models": [{"name": "hermes3:8b-abliterated"}]}
        )
        first_invalid = "not json"
        second_invalid = "still not json"
        first_generate = self._urlopen_json_response({"response": first_invalid})
        second_generate = self._urlopen_json_response({"response": second_invalid})

        with (
            patch.dict(
                os.environ,
                {"SOURCE_PROXY_FIP5_HERMES_VERIFIER_MODEL": "hermes3:8b-abliterated"},
                clear=False,
            ),
            patch(
                "source_proxy.api.decision.urllib.request.urlopen",
                side_effect=[inventory, first_generate, second_generate],
            ),
        ):
            hermes = _fip5_call_hermes_verifier(
                request=PromptPacketRequest(task="already satisfied no-op"),
                fip4_result={
                    "final_coder_packet_hash": "packet",
                    "coder_received_packet_hash": "packet",
                    "qwen": {"qwen_output_hash": "qwen"},
                    "parser": {"parsed_output_mode": "json_content_lines"},
                    "changed_files": ["docs/noop.txt"],
                },
                deterministic={"passed": True},
                browser={"passed": True},
            )

        self.assertEqual(hermes["status"], "failed")
        self.assertEqual(hermes["reason"], "hermes_verifier_output_not_json")
        self.assertEqual(hermes["verdict"], "UNVERIFIED")
        self.assertFalse(hermes["schema_valid"])
        self.assertEqual(hermes["attempt_count"], 2)
        self.assertTrue(hermes["retry_attempted"])
        self.assertEqual(hermes["retry_reason"], "hermes_verifier_output_not_json")
        self.assertEqual(
            hermes["first_invalid_output_hash"],
            _json_hash(first_invalid),
        )
        self.assertIn(_json_hash(second_invalid), hermes["invalid_output_hashes"])

    def test_fip5_browser_pass_and_deterministic_pass_can_receive_hermes_pass(self) -> None:
        inventory = self._urlopen_json_response(
            {"models": [{"name": "hermes3:8b-abliterated"}]}
        )
        verifier_pass = self._urlopen_json_response(
            {
                "response": json.dumps(
                    {
                        "verdict": "PASS",
                        "reasons": ["deterministic and browser evidence passed"],
                        "repair_instructions": [],
                    }
                )
            }
        )

        with (
            patch.dict(
                os.environ,
                {"SOURCE_PROXY_FIP5_HERMES_VERIFIER_MODEL": "hermes3:8b-abliterated"},
                clear=False,
            ),
            patch(
                "source_proxy.api.decision.urllib.request.urlopen",
                side_effect=[inventory, verifier_pass],
            ),
        ):
            hermes = _fip5_call_hermes_verifier(
                request=PromptPacketRequest(task="browser verifier pass"),
                fip4_result={
                    "final_coder_packet_hash": "packet",
                    "coder_received_packet_hash": "packet",
                    "qwen": {"qwen_output_hash": "qwen"},
                    "parser": {"parsed_output_mode": "json_content_lines"},
                    "changed_files": ["src/app/coding/page.tsx"],
                },
                deterministic={"passed": True, "failures": [], "checks_run": ["all"]},
                browser={"passed": True, "reason": "browser_passed", "status": "used"},
            )

        self.assertEqual(hermes["status"], "used")
        self.assertEqual(hermes["reason"], "hermes_verifier_schema_valid")
        self.assertEqual(hermes["verdict"], "PASS")
        self.assertFalse(hermes["evidence_mismatch"])

    def test_fip5_hermes_needs_fix_without_failed_evidence_reasks_once(self) -> None:
        inventory = self._urlopen_json_response(
            {"models": [{"name": "hermes3:8b-abliterated"}]}
        )
        mismatch = self._urlopen_json_response(
            {
                "response": json.dumps(
                    {
                        "verdict": "NEEDS_FIX",
                        "reasons": ["deterministic evidence failed"],
                        "repair_instructions": [],
                    }
                )
            }
        )
        corrected = self._urlopen_json_response(
            {
                "response": json.dumps(
                    {
                        "verdict": "PASS",
                        "reasons": ["deterministic and browser evidence passed"],
                        "repair_instructions": [],
                    }
                )
            }
        )

        with (
            patch.dict(
                os.environ,
                {"SOURCE_PROXY_FIP5_HERMES_VERIFIER_MODEL": "hermes3:8b-abliterated"},
                clear=False,
            ),
            patch(
                "source_proxy.api.decision.urllib.request.urlopen",
                side_effect=[inventory, mismatch, corrected],
            ),
        ):
            hermes = _fip5_call_hermes_verifier(
                request=PromptPacketRequest(task="browser verifier pass"),
                fip4_result={
                    "final_coder_packet_hash": "packet",
                    "coder_received_packet_hash": "packet",
                    "qwen": {"qwen_output_hash": "qwen"},
                    "parser": {"parsed_output_mode": "json_content_lines"},
                    "changed_files": ["src/app/coding/page.tsx"],
                },
                deterministic={"passed": True, "failures": [], "checks_run": ["all"]},
                browser={"passed": True, "reason": "browser_passed", "status": "used"},
            )

        self.assertEqual(hermes["status"], "used")
        self.assertEqual(hermes["verdict"], "PASS")
        self.assertEqual(hermes["attempt_count"], 2)
        self.assertTrue(hermes["retry_attempted"])
        self.assertEqual(hermes["retry_reason"], "hermes_verifier_evidence_mismatch")
        self.assertTrue(hermes["attempts"][0]["evidence_mismatch"])
        self.assertFalse(hermes["evidence_mismatch"])

    def test_fip5_hermes_cannot_override_browser_failure_with_pass(self) -> None:
        normalized, errors = _fip5_normalize_hermes_verifier_output(
            {
                "verdict": "PASS",
                "reasons": ["looks good"],
                "repair_instructions": [],
            },
            deterministic={"passed": True},
            browser={"passed": False, "reason": "browser_failed"},
        )

        self.assertEqual(errors, [])
        self.assertEqual(normalized["verdict"], "FAIL")
        self.assertIn("pass_blocked_by_browser_behavior_failure", normalized["reasons"])

    def test_fip5_hermes_schema_invalid_output_is_receipted_with_attempts(self) -> None:
        target = "source_proxy/tests/fip5-target-proof.txt"
        hermes = {
            "status": "failed",
            "reason": "hermes_verifier_schema_invalid",
            "model": "hermes3:8b-abliterated",
            "role": "post_code_verifier",
            "prompt_hash": "prompt-hash-2",
            "output_hash": "output-hash-2",
            "schema_valid": False,
            "verdict": "UNVERIFIED",
            "repair_instructions": [],
            "attempt_count": 2,
            "retry_attempted": True,
            "retry_reason": "hermes_verifier_schema_invalid",
            "first_invalid_output_hash": "output-hash-1",
            "invalid_output_hashes": ["output-hash-1", "output-hash-2"],
            "attempts": [
                {"attempt": 1, "reason": "hermes_verifier_schema_invalid", "output_hash": "output-hash-1"},
                {"attempt": 2, "reason": "hermes_verifier_schema_invalid", "output_hash": "output-hash-2"},
            ],
        }
        fip5 = {
            "status": "failed",
            "reason": "CONFIG-BLOCKED: hermes_verifier_schema_invalid",
            "deterministic": {
                "status": "used",
                "reason": "fip5_deterministic_verifier_executed",
                "passed": True,
                "checks_run": [],
                "failures": [],
            },
            "browser": {"status": "skipped", "reason": "not_relevant", "passed": True},
            "hermes": hermes,
            "repair_loop_status": {"status": "skipped", "reason": "fip5_repair_not_needed"},
            "repair_attempt_count": 0,
            "repair_max_attempts": 2,
            "repair_packets": [],
            "qwen_repair_outputs": [],
            "final_fip4_result": {},
            "final_verdict": "CONFIG-BLOCKED: hermes_verifier_schema_invalid",
        }
        payload = _attach_fip0_truth_receipt(
            {"fip5": "schema invalid proof"},
            request=PromptPacketRequest(task="FIP-5 schema invalid receipt proof"),
            route_payload={"recommended_route": "local_route"},
            intake_payload={"allowed_files": [target], "forbidden_files": []},
            decision=SimpleNamespace(research_sources=[]),
            explicit_target=target,
            route_reasons=[],
            fip5_verifier_result=fip5,
        )

        receipt = payload["fip0_truth_receipt"]
        self.assertEqual(receipt["final_verdict"], "CONFIG-BLOCKED: hermes_verifier_schema_invalid")
        self.assertEqual(receipt["hermes_verifier_attempt_count"], 2)
        self.assertTrue(receipt["hermes_verifier_retry_attempted"])
        self.assertEqual(receipt["hermes_verifier_first_invalid_output_hash"], "output-hash-1")
        self.assertEqual(
            receipt["hermes_verifier_invalid_output_hashes"],
            ["output-hash-1", "output-hash-2"],
        )
        self.assertEqual(len(receipt["hermes_verifier_attempts"]), 2)

    def test_fip5_noop_pass_requires_deterministic_and_schema_valid_hermes(self) -> None:
        target = "docs/evidence/source-proxy-full-integration-pivot/level-5-targets/noop-note.txt"
        fip4_result = {
            "status": "used",
            "reason": "fip4_qwen_action_output_parsed_and_diff_generated",
            "final_coder_packet_hash": "packet-hash",
            "coder_received_packet_hash": "packet-hash",
            "parser": {"parsed_output_mode": "json_content_lines", "parse_error": ""},
            "allowed_files": [target],
            "forbidden_files": [".env"],
            "changed_files": [target],
            "action": {"target": target, "content": "Level 5 no-op honesty is visible."},
            "proposed_diff": "--- a/noop\n+++ b/noop\n@@\n-old\n+Level 5 no-op honesty is visible.\n",
            "qwen": {"qwen_output_hash": "qwen-output"},
            "final_coder_packet": {"target_file": target},
        }
        with patch(
            "source_proxy.api.decision._fip5_call_hermes_verifier",
            return_value={
                "status": "used",
                "reason": "hermes_verifier_schema_valid",
                "model": "hermes3:8b-abliterated",
                "role": "post_code_verifier",
                "prompt_hash": "prompt-hash",
                "output_hash": "output-hash",
                "schema_valid": True,
                "verdict": "PASS",
                "reasons": ["already satisfied with deterministic evidence"],
                "repair_instructions": [],
                "attempt_count": 1,
                "attempts": [{"attempt": 1, "reason": "hermes_verifier_schema_valid"}],
            },
        ):
            fip5 = _run_fip5_verifier_and_repair(
                request=PromptPacketRequest(
                    task="if this already says Level 5 no-op honesty is visible, don't invent edits.",
                    allowed_files=[target],
                    expected_result_state="already_satisfied_expected",
                ),
                explicit_target=target,
                fip4_result=fip4_result,
            )

        self.assertEqual(fip5["final_verdict"], "GO: fip5_required_verifier_and_repair_complete")
        self.assertTrue(fip5["deterministic"]["passed"])
        self.assertEqual(fip5["hermes"]["status"], "used")
        self.assertTrue(fip5["hermes"]["schema_valid"])
        self.assertEqual(fip5["hermes"]["verdict"], "PASS")

    def test_fip5_hermes_cannot_turn_deterministic_failure_into_pass(self) -> None:
        target = "source_proxy/tests/fip5-target-proof.txt"
        fip4_result = {
            "status": "used",
            "final_coder_packet_hash": "packet-hash",
            "coder_received_packet_hash": "packet-hash",
            "parser": {"parsed_output_mode": "json_content_lines", "parse_error": ""},
            "allowed_files": [target],
            "forbidden_files": [],
            "changed_files": [target],
            "action": {"target": target, "content": "wrong"},
            "proposed_diff": "diff",
            "final_coder_packet": {"target_file": target},
        }
        with (
            patch(
                "source_proxy.api.decision._fip5_call_hermes_verifier",
                return_value={
                    "status": "used",
                    "reason": "hermes_verifier_schema_valid",
                    "model": "hermes3:8b-abliterated",
                    "role": "post_code_verifier",
                    "prompt_hash": "prompt-hash",
                    "output_hash": "output-hash",
                    "schema_valid": True,
                    "verdict": "NEEDS_FIX",
                    "repair_instructions": ["Replace with required text."],
                },
            ),
            patch(
                "source_proxy.api.decision._fip5_call_qwen_repair",
                return_value={
                    "status": "used",
                    "coder_received_packet_hash": "repair-hash",
                    "raw_output": json.dumps(
                        {"action": "replace_file", "target": target, "content": "still wrong"}
                    ),
                },
            ),
        ):
            fip5 = _run_fip5_verifier_and_repair(
                request=PromptPacketRequest(
                    task=f"Target file: {target}\n\nReplace with exactly this content: required text.",
                    allowed_files=[target],
                    expected_result_state="max_repair_expected",
                ),
                explicit_target=target,
                fip4_result=fip4_result,
            )
        self.assertEqual(
            fip5["final_verdict"],
            "NO-GO: fip5_repair_attempts_exhausted_operator_intervention_required",
        )
        self.assertEqual(fip5["repair_attempt_count"], 2)
        self.assertEqual(len(fip5["repair_packets"]), 2)
        self.assertTrue(
            all(packet["role"] == "qwen_repair_as_coder_only" for packet in fip5["repair_packets"])
        )

    def test_fip5_browser_failure_blocks_pass(self) -> None:
        target = "src/app/fip5-proof/page.tsx"
        fip4_result = {
            "status": "used",
            "final_coder_packet_hash": "packet-hash",
            "coder_received_packet_hash": "packet-hash",
            "parser": {"parsed_output_mode": "json_content_lines", "parse_error": ""},
            "allowed_files": [target],
            "forbidden_files": [],
            "changed_files": [target],
            "action": {"target": target, "content": "export default function Page(){return <div>ok</div>}"},
            "proposed_diff": "diff",
            "final_coder_packet": {"target_file": target},
        }
        with patch(
            "source_proxy.api.decision._fip5_call_hermes_verifier",
            return_value={
                "status": "used",
                "reason": "hermes_verifier_schema_valid",
                "model": "hermes3:8b-abliterated",
                "role": "post_code_verifier",
                "prompt_hash": "prompt-hash",
                "output_hash": "output-hash",
                "schema_valid": True,
                "verdict": "FAIL",
                "repair_instructions": ["Browser evidence is required."],
            },
        ):
            fip5 = _run_fip5_verifier_and_repair(
                request=PromptPacketRequest(task=f"Target file: {target}\n\nMake page visible."),
                explicit_target=target,
                fip4_result=fip4_result,
            )
        self.assertEqual(
            fip5["final_verdict"],
            "NO-GO: fip5_browser_behavior_authority_blocks_pass",
        )
        self.assertFalse(fip5["browser"]["passed"])
        self.assertTrue(fip5["browser"]["authoritative"])

    def test_fip6_trace_route_matches_durable_receipt_selected_fields(self) -> None:
        client = self._client()
        receipt = {
            "run_id": "fip0-1111111111111111",
            "timestamp": "2026-06-13T12:00:00+00:00",
            "raw_prompt": "Target file: docs/fip6.txt\n\nWrite FIP-6 proof.",
            "normalized_task": "Write FIP-6 proof.",
            "route_type": "local_route",
            "workspace_mode": "repo",
            "dirty_tree_status": {"status": "used", "summary": "dirty"},
            "context_router_status": {"status": "used", "reason": "route_done"},
            "obsidian_status": {"status": "used", "reason": "selected_note_read"},
            "cartographer_status": {"status": "used", "reason": "advisory_context"},
            "design_status": {"status": "used", "reason": "design_refs"},
            "mac_worker_status": {"status": "skipped", "reason": "advisory_only"},
            "source_readiness_status": {"status": "used", "reason": "packet_built"},
            "search_needed": True,
            "research_query": "FIP-6 trace",
            "repo_research_status": {"status": "used", "reason": "repo_sources"},
            "scout_status": {"status": "used", "reason": "scout_sources"},
            "scout_sources": [{"title": "Scout source"}],
            "searxng_status": {"status": "used", "reason": "live_search"},
            "searxng_url": "http://127.0.0.1:8080",
            "searxng_result_count": 1,
            "searxng_sources": [{"title": "SearXNG source"}],
            "tinyfish_status": {"status": "skipped", "reason": "deferred_cloud_requires_britton_approval"},
            "xersearch_status": {"status": "skipped", "reason": "missing_alias_do_not_create"},
            "gemma_status": {"status": "used", "reason": "gemma_json"},
            "gemma_model": "gemma3n:e4b",
            "gemma_prompt_hash": "gemma-prompt",
            "gemma_output_hash": "gemma-output",
            "gemma_intent": "edit_file",
            "hermes_critic_status": {"status": "used", "reason": "hermes_json"},
            "hermes_critic_model": "hermes3:8b-abliterated",
            "hermes_critic_prompt_hash": "critic-prompt",
            "hermes_critic_output_hash": "critic-output",
            "hermes_risks": ["risk"],
            "final_coder_packet_hash": "packet-hash",
            "coder_received_packet_hash": "packet-hash",
            "qwen_coder_status": {"status": "used", "reason": "qwen_used"},
            "qwen_coder_model": "qwen2.5-coder:7b",
            "qwen_coder_output_hash": "qwen-output",
            "output_contract_status": {"status": "used", "reason": "parsed"},
            "fip4_qwen_coder_result": {
                "parser": {"parsed_output_mode": "json_replace_file"},
                "changed_files": ["docs/fip6.txt"],
                "raw_output_excerpt": "PRIVATE MODEL OUTPUT SHOULD NOT LEAK",
            },
            "fip4_final_coder_packet": {
                "target_file": "docs/fip6.txt",
                "allowed_files": ["docs/fip6.txt"],
                "forbidden_files": [".env"],
            },
            "protected_path_check": {"status": "used", "reason": "guard_evaluated"},
            "allowed_files": ["docs/fip6.txt"],
            "forbidden_files": [".env"],
            "diff_summary": {"changed_files": ["docs/fip6.txt"]},
            "checks_run": ["pytest"],
            "deterministic_verifier_status": {"status": "used", "reason": "passed"},
            "deterministic_checks_run": ["content_exact_match"],
            "deterministic_failures": [],
            "browser_behavior_status": {"status": "skipped", "reason": "not_html"},
            "hermes_verifier_status": {"status": "used", "reason": "schema_valid"},
            "hermes_verifier_model": "hermes3:8b-abliterated",
            "hermes_verifier_role": "post_code_verifier",
            "hermes_verifier_verdict": "PASS",
            "hermes_verifier_prompt_hash": "verifier-prompt",
            "hermes_verifier_output_hash": "verifier-output",
            "hermes_verifier_repair_instructions": [],
            "repair_loop_status": {"status": "skipped", "reason": "not_needed"},
            "repair_attempt_count": 0,
            "repair_packets": [],
            "final_verdict": "GO: fip5_required_verifier_and_repair_complete",
            "used_sources": ["context_router_status", "qwen_coder_status"],
            "skipped_reasons": ["tinyfish_status:deferred_cloud_requires_britton_approval"],
            "blocked_reasons": [],
            "failed_reasons": [],
        }
        receipt_path = self._write_fip0_receipt(receipt)

        response = client.get("/v1/decisions/fip0-receipts/fip0-1111111111111111/trace")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        trace = body["operator_trace"]
        self.assertEqual(body["receipt_path"], str(receipt_path))
        self.assertEqual(trace["run_metadata"]["run_id"], receipt["run_id"])
        self.assertNotIn("raw_prompt", trace["run_metadata"])
        self.assertEqual(trace["run_metadata"]["prompt_hash"], _json_hash(receipt["raw_prompt"]))
        self.assertEqual(trace["coder_trace"]["final_coder_packet_hash"], "packet-hash")
        self.assertEqual(trace["coder_trace"]["coder_received_packet_hash"], "packet-hash")
        self.assertTrue(trace["coder_trace"]["packet_hash_match_status"]["match"])
        self.assertEqual(trace["verdict_trace"]["final_verdict"], receipt["final_verdict"])
        self.assertEqual(body["receipt"]["final_verdict"], trace["verdict_trace"]["final_verdict"])
        self.assertEqual(trace["trace_hygiene_check"]["status"], "used")
        self.assertNotIn("no_hidden_thinking_displayed", trace)
        serialized = json.dumps(body).lower()
        self.assertNotIn("private model output should not leak".lower(), serialized)
        self.assertNotIn("raw_output_excerpt", serialized)
        self.assertNotIn("chain_of_thought", serialized)
        self.assertNotIn("hidden_reasoning", serialized)

    def test_fip6_trace_hygiene_scanner_fails_on_private_shape(self) -> None:
        from source_proxy.api.decision import _trace_hygiene_scan

        scan = _trace_hygiene_scan(
            {
                "safe": {"status": "used"},
                "unsafe": {"raw_output_excerpt": "chain_of_thought: hidden"},
            }
        )
        self.assertEqual(scan["status"], "failed")
        self.assertFalse(scan["passed"])
        self.assertGreaterEqual(scan["leak_count"], 1)

    def test_fip6_trace_displays_skipped_failed_and_missing_lanes(self) -> None:
        client = self._client()
        receipt = {
            "run_id": "fip0-2222222222222222",
            "timestamp": "2026-06-13T12:01:00+00:00",
            "raw_prompt": "Trace missing lanes.",
            "normalized_task": "Trace missing lanes.",
            "route_type": "local_route",
            "workspace_mode": "repo",
            "dirty_tree_status": {"status": "used"},
            "context_router_status": {"status": "used", "reason": "route_done"},
            "tinyfish_status": {"status": "skipped", "reason": "deferred_cloud_requires_britton_approval"},
            "xersearch_status": {"status": "skipped", "reason": "missing_alias_do_not_create"},
            "gemma_status": {"status": "failed", "reason": "model_empty_output"},
            "qwen_coder_status": {"status": "blocked", "reason": "protected_path_route_block"},
            "final_coder_packet_hash": "packet-hash",
            "coder_received_packet_hash": "",
            "protected_path_check": {"status": "blocked", "reason": "protected_path_route_block"},
            "allowed_files": ["docs/fip6.txt"],
            "forbidden_files": [".env"],
            "diff_summary": {"changed_files": []},
            "checks_run": [],
            "repair_loop_status": {"status": "skipped", "reason": "qwen_not_run"},
            "final_verdict": "NO-GO: protected_path_route_block",
            "used_sources": ["context_router_status"],
            "skipped_reasons": [
                "tinyfish_status:deferred_cloud_requires_britton_approval",
                "xersearch_status:missing_alias_do_not_create",
            ],
            "blocked_reasons": ["qwen_coder_status:protected_path_route_block"],
            "failed_reasons": ["gemma_status:model_empty_output"],
        }
        self._write_fip0_receipt(receipt)

        response = client.get("/v1/decisions/fip0-receipts/fip0-2222222222222222/trace")
        self.assertEqual(response.status_code, 200, response.text)
        trace = response.json()["operator_trace"]
        self.assertEqual(
            trace["search_trace"]["tinyfish_deferred_status"]["reason"],
            "deferred_cloud_requires_britton_approval",
        )
        self.assertEqual(
            trace["search_trace"]["xersearch_missing_alias_status"]["reason"],
            "missing_alias_do_not_create",
        )
        self.assertEqual(trace["model_trace"]["gemma"]["status"]["status"], "failed")
        self.assertEqual(trace["coder_trace"]["qwen"]["status"]["status"], "blocked")
        self.assertIn("obsidian_status", trace["missing_fields"])
        self.assertEqual(trace["context_trace"]["obsidian"]["status"]["status"], "unknown")
        self.assertEqual(
            trace["coder_trace"]["packet_hash_match_status"]["reason"],
            "coder_packet_not_received_or_hash_missing",
        )

    def test_fip6_trace_displays_repair_attempt_packets_and_verifier_result(self) -> None:
        client = self._client()
        receipt = {
            "run_id": "fip0-3333333333333333",
            "timestamp": "2026-06-13T12:02:00+00:00",
            "raw_prompt": "Repair trace.",
            "normalized_task": "Repair trace.",
            "route_type": "local_route",
            "workspace_mode": "repo",
            "dirty_tree_status": {"status": "used"},
            "context_router_status": {"status": "used", "reason": "route_done"},
            "tinyfish_status": {"status": "skipped", "reason": "deferred_cloud_requires_britton_approval"},
            "xersearch_status": {"status": "skipped", "reason": "missing_alias_do_not_create"},
            "gemma_status": {"status": "used", "reason": "ok"},
            "hermes_critic_status": {"status": "used", "reason": "ok"},
            "final_coder_packet_hash": "packet-hash",
            "coder_received_packet_hash": "packet-hash",
            "qwen_coder_status": {"status": "used", "reason": "qwen_used"},
            "qwen_coder_model": "qwen2.5-coder:7b",
            "qwen_coder_output_hash": "initial-output",
            "protected_path_check": {"status": "used", "reason": "guard_evaluated"},
            "allowed_files": ["docs/fip6.txt"],
            "forbidden_files": [],
            "diff_summary": {"changed_files": ["docs/fip6.txt"]},
            "checks_run": ["pytest"],
            "deterministic_verifier_status": {"status": "used", "reason": "passed_after_repair"},
            "deterministic_failures": [],
            "browser_behavior_status": {"status": "skipped", "reason": "not_html"},
            "hermes_verifier_status": {"status": "used", "reason": "schema_valid"},
            "hermes_verifier_model": "hermes3:8b-abliterated",
            "hermes_verifier_role": "post_code_verifier",
            "hermes_verifier_verdict": "PASS",
            "hermes_verifier_repair_instructions": [],
            "repair_loop_status": {"status": "used", "reason": "repair_applied"},
            "repair_attempt_count": 1,
            "repair_max_attempts": 2,
            "repair_packets": [
                {"attempt": 1, "role": "qwen_repair_as_coder_only", "packet_hash": "repair-packet"}
            ],
            "qwen_repair_outputs": [{"attempt": 1, "output_hash": "repair-output"}],
            "fip5_verifier_result": {
                "final_verifier_result": {"passed": True, "failures": []}
            },
            "final_verdict": "GO: fip5_required_verifier_and_repair_complete",
            "used_sources": ["repair_loop_status"],
            "skipped_reasons": [],
            "blocked_reasons": [],
            "failed_reasons": [],
        }
        self._write_fip0_receipt(receipt)

        response = client.get("/v1/decisions/fip0-receipts/fip0-3333333333333333/trace")
        self.assertEqual(response.status_code, 200, response.text)
        repair_trace = response.json()["operator_trace"]["repair_trace"]
        self.assertEqual(repair_trace["repair_loop_status"]["status"], "used")
        self.assertEqual(repair_trace["repair_attempt_count"], 1)
        self.assertEqual(
            repair_trace["repair_packets"][0]["role"],
            "qwen_repair_as_coder_only",
        )
        self.assertEqual(repair_trace["qwen_repair_outputs"][0]["output_hash"], "repair-output")
        self.assertEqual(repair_trace["verifier_result"]["passed"], True)

    def test_research_route_endpoint_attaches_sources(self) -> None:
        client = self._client()
        sources = [
            {
                "title": "Releases | Vite",
                "url": "https://vite.dev/releases",
                "snippet": "Current releases.",
            }
        ]

        with patch(
            "source_proxy.decision.router.run_local_research_preview",
            new=AsyncMock(return_value=sources),
        ):
            with patch.dict(os.environ, {"SPIRIT_ENABLE_PROXY_RESEARCH": "true"}, clear=False):
                response = client.post(
                    "/v1/decisions/route",
                    json={"task": "What are the latest changes in Vite 6?"},
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["research_recommended"])
        self.assertEqual(payload["research_sources"], sources)

    def test_proxy_research_sources_are_disabled_by_default(self) -> None:
        client = self._client()
        search = AsyncMock(
            return_value=[
                {
                    "title": "Releases | Vite",
                    "url": "https://vite.dev/releases",
                    "snippet": "Current releases.",
                }
            ],
        )

        with (
            patch.dict(os.environ, {"SPIRIT_ENABLE_PROXY_RESEARCH": ""}, clear=False),
            patch("source_proxy.decision.router.run_local_research_preview", new=search),
        ):
            response = client.post(
                "/v1/decisions/route",
                json={"task": "What are the latest changes in Vite 6?"},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["research_recommended"])
        self.assertEqual(payload["research_sources"], [])
        search.assert_not_awaited()

    def test_route_endpoint_injects_role_prompt_from_active_task(self) -> None:
        client = self._client()
        created = create_long_running_task("Swarm route")
        task_id = created["task"]["id"]
        update_long_running_task(task_id, current_agent_role="debugger")

        response = client.post(
            "/v1/decisions/route",
            json={"task": "Run verification", "active_task_id": task_id},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["current_agent_role"], "debugger")
        self.assertIn("Debugger", payload["role_system_prompt"])
        self.assertIn("sandboxed tools", payload["role_system_prompt"])

    def test_route_endpoint_explicit_role_overrides_active_task(self) -> None:
        client = self._client()
        created = create_long_running_task("Swarm route")
        task_id = created["task"]["id"]
        update_long_running_task(task_id, current_agent_role="debugger")

        response = client.post(
            "/v1/decisions/route",
            json={
                "task": "Plan implementation",
                "active_task_id": task_id,
                "current_agent_role": "architect",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["current_agent_role"], "architect")
        self.assertIn("Architect", payload["role_system_prompt"])

    def test_prompt_packet_active_task_uses_saved_architect_packet_context(self) -> None:
        client = self._client()
        previous_project_path = os.environ.get("SPIRIT_PROJECT_PATH")
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            target = root / "docs/phase-8-manual-check.md"
            target.parent.mkdir(parents=True)
            target.write_text("# Manual Check\n", encoding="utf-8")
            os.environ["SPIRIT_PROJECT_PATH"] = workspace
            task = (
                "Target file: docs/phase-8-manual-check.md\n"
                'Add "Manual check complete." as one short sentence.'
            )
            created = create_long_running_task(task)
            task_id = created["task"]["id"]
            advance_long_running_task(task_id)

            def fake_coder(*, architect_plan, **_kwargs):
                packet = architect_plan.coder_packet
                self.assertEqual(
                    packet.target_file.path,
                    "docs/phase-8-manual-check.md",
                )
                self.assertEqual(
                    [item.path for item in packet.context_slices],
                    ["docs/phase-8-manual-check.md"],
                )
                self.assertIn(
                    "Manual check complete.",
                    packet.constraints.must_contain,
                )
                return {
                    "proposed_diff": "\n".join(
                        [
                            "diff --git a/docs/phase-8-manual-check.md b/docs/phase-8-manual-check.md",
                            "--- a/docs/phase-8-manual-check.md",
                            "+++ b/docs/phase-8-manual-check.md",
                            "@@ -1 +1,2 @@",
                            " # Manual Check",
                            '+Manual check complete.',
                            "",
                        ]
                    ),
                    "target": "docs/phase-8-manual-check.md",
                    "coder_notes": ["ok"],
                    "bundle": None,
                    "coder_diagnostics": {
                        "context_mode": "user_app",
                        "target_exists": True,
                        "context_slices": [
                            {"path": "docs/phase-8-manual-check.md", "kind": "target"}
                        ],
                        "forbidden_paths": ["source_proxy/"],
                    },
                }

            try:
                with patch(
                    "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
                    side_effect=fake_coder,
                ) as coder_mock:
                    response = client.post(
                        "/v1/decisions/prompt-packet",
                        json={
                            "task": task,
                            "wants_implementation": True,
                            "active_task_id": task_id,
                            "current_agent_role": "coder",
                        },
                    )
            finally:
                if previous_project_path is None:
                    os.environ.pop("SPIRIT_PROJECT_PATH", None)
                else:
                    os.environ["SPIRIT_PROJECT_PATH"] = previous_project_path

        self.assertEqual(response.status_code, 200, response.text)
        coder_mock.assert_called_once()
        body = response.json()
        self.assertEqual(body["target"], "docs/phase-8-manual-check.md")
        self.assertIn("diff --git", body["proposed_diff"])
        self.assertEqual(
            body["coder_packet"]["target_file"]["path"],
            "docs/phase-8-manual-check.md",
        )
        self.assertEqual(
            body["coder_packet"]["context_slices"][0]["path"],
            "docs/phase-8-manual-check.md",
        )
        self.assertIn(
            "Manual check complete.",
            body["coder_packet"]["constraints"]["must_contain"],
        )
        self.assertEqual(
            body["verification_plan"]["required_checks"][0]["id"],
            "git_apply_check",
        )

    def test_prompt_packet_coder_missing_context_marks_task_needs_context(self) -> None:
        client = self._client()
        previous_project_path = os.environ.get("SPIRIT_PROJECT_PATH")
        with tempfile.TemporaryDirectory() as workspace:
            root = Path(workspace)
            target = root / "docs/phase-8-manual-check.md"
            target.parent.mkdir(parents=True)
            target.write_text("# Manual Check\n", encoding="utf-8")
            os.environ["SPIRIT_PROJECT_PATH"] = workspace
            task = (
                "Target file: docs/phase-8-manual-check.md\n"
                'Add "Manual check complete." as one short sentence.'
            )
            created = create_long_running_task(task)
            task_id = created["task"]["id"]
            advance_long_running_task(task_id)

            with patch(
                "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
                return_value={
                    "proposed_diff": "",
                    "target": "docs/phase-8-manual-check.md",
                    "coder_notes": ["CODER_BLOCKED reason_code: coder_packet_missing_context"],
                    "bundle": None,
                    "coder_blocked": True,
                    "blocked_reason": "Coder requires an Architect CoderPacket.",
                    "needed_context": "Regenerate Architect plan.",
                    "reason_code": "coder_packet_missing_context",
                    "coder_diagnostics": {
                        "context_mode": "user_app",
                        "target_exists": True,
                        "context_slices": [],
                        "forbidden_paths": ["source_proxy/"],
                    },
                },
            ):
                response = client.post(
                    "/v1/decisions/prompt-packet",
                    json={
                        "task": task,
                        "wants_implementation": True,
                        "active_task_id": task_id,
                        "current_agent_role": "coder",
                    },
                )
            try:
                for _ in range(4):
                    payload = get_long_running_task(task_id)
            finally:
                if previous_project_path is None:
                    os.environ.pop("SPIRIT_PROJECT_PATH", None)
                else:
                    os.environ["SPIRIT_PROJECT_PATH"] = previous_project_path

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["status"], "needs_context")
        self.assertEqual(body["reason_code"], "coder_packet_missing_context")
        self.assertEqual(payload["task"]["status"], "needs_context")
        self.assertNotEqual(payload["task"]["status"], "completed")
        self.assertIn("CoderPacket", payload["task"]["next_action"])

    def test_prompt_packet_pinned_app_page_invokes_sync_coder(self) -> None:
        client = self._client()
        task = (
            "Target file: src/app/(dashboard)/design/page.tsx\n\n"
            "Add a visible status widget at the top of the page."
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "src/app/(dashboard)/design/page.tsx",
                "coder_notes": [],
                "bundle": "test",
                "coder_blocked": True,
                "blocked_reason": "Coder model returned no content.",
                "needed_context": "Set SOURCE_PROXY_CODER_MODEL_ALIAS.",
                "reason_code": "coder_empty_model_response",
                "coder_diagnostics": {
                    "context_mode": "user_app",
                    "target_exists": True,
                    "context_slices": [
                        {"path": "src/app/(dashboard)/design/page.tsx", "kind": "target"}
                    ],
                    "forbidden_paths": ["source_proxy/"],
                },
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
            )
        self.assertEqual(response.status_code, 200, response.text)
        coder_mock.assert_not_called()
        body = response.json()
        self.assertEqual(
            body.get("target"),
            "src/app/(dashboard)/design/page.tsx",
        )
        self.assertEqual(body.get("proposed_diff"), "")
        self.assertFalse(body.get("coder_agent_local_diff"))
        self.assertTrue(body.get("manual_prompt_packet_available"))
        self.assertEqual(body.get("reason_code"), "target_missing")
        rd = body.get("route_decision") or {}
        self.assertEqual(rd.get("recommended_route"), "local_route")

    def test_prompt_packet_already_satisfied_maps_to_no_approval_needed(self) -> None:
        client = self._client()
        task = (
            "Target file: src/app/coding/design-demo/page.tsx\n\n"
            "Ensure the design demo page is already complete."
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "src/app/coding/design-demo/page.tsx",
                "coder_notes": [],
                "bundle": "test",
                "coder_blocked": False,
                "already_satisfied": True,
                "alreadySatisfied": True,
                "blocked_reason": "",
                "needed_context": "",
                "reason_code": "coder_no_changes_needed",
                "coder_diagnostics": {
                    "validation_status": "already_satisfied",
                    "generated_diff_length": 0,
                    "already_satisfied": True,
                    "no_changes_needed": True,
                },
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
            )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["proposed_diff"], "")
        coder_mock.assert_called_once()
        self.assertFalse(body["coder_blocked"])
        self.assertTrue(body["already_satisfied"])
        self.assertEqual(body["reason_code"], "coder_no_changes_needed")
        self.assertFalse(body["manual_prompt_packet_available"])
        self.assertEqual(body["status"], "already_satisfied")
        self.assertEqual(
            body["coder_packet"]["target_file"]["path"],
            "src/app/coding/design-demo/page.tsx",
        )

    def test_prompt_packet_subjective_improvement_noop_maps_to_needs_diff(self) -> None:
        client = self._client()
        task = (
            "make ThemeStrip feel more premium and alive, tighter spacing, better glow, "
            "smoother hover states.\n"
            "Target file: src/components/dashboard/ThemeStrip.tsx"
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "src/components/dashboard/ThemeStrip.tsx",
                "coder_notes": [],
                "bundle": "test",
                "coder_blocked": True,
                "already_satisfied": False,
                "blocked_reason": (
                    "This task asks for subjective visual improvement, so identical "
                    "replacement content cannot be treated as already satisfied."
                ),
                "needed_context": (
                    "Produce an actual visual refinement diff or use manual visual review."
                ),
                "reason_code": "coder_subjective_improvement_requires_diff_or_review",
                "coder_diagnostics": {
                    "validation_status": "subjective_improvement_requires_diff_or_review",
                    "already_satisfied": False,
                    "no_changes_needed": False,
                    "subjective_improvement_detected": True,
                },
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
            )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["manual_prompt_packet_available"])
        self.assertTrue(body["cloud_route_available"])
        self.assertFalse(body["already_satisfied"])
        self.assertEqual(
            body["reason_code"],
            "coder_subjective_improvement_requires_diff_or_review",
        )
        self.assertEqual(body["status"], "needs_coder_diff")
        self.assertEqual(
            body["coder_packet"]["target_file"]["path"],
            "src/components/dashboard/ThemeStrip.tsx",
        )

    def test_prompt_packet_shallow_visual_diff_maps_to_needs_diff(self) -> None:
        client = self._client()
        task = (
            "make ThemeStrip feel more premium and alive, tighter spacing, better glow, "
            "smoother hover states.\n"
            "Target file: src/components/dashboard/ThemeStrip.tsx"
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "src/components/dashboard/ThemeStrip.tsx",
                "coder_notes": [],
                "bundle": "test",
                "coder_blocked": True,
                "already_satisfied": False,
                "blocked_reason": (
                    "The generated diff does not materially change UI styling, layout, "
                    "hover, active, glow, spacing, or visual behavior for this subjective "
                    "improvement task."
                ),
                "needed_context": (
                    "Generate a concrete visual refinement diff that changes className, "
                    "styling, layout, hover, active, glow, spacing, or animation behavior."
                ),
                "reason_code": "coder_visual_improvement_diff_too_shallow",
                "coder_diagnostics": {
                    "validation_status": "visual_improvement_diff_too_shallow",
                    "visual_materiality_ok": False,
                    "visual_materiality_reasons": [
                        "subjective visual task produced only comment or non-visual changes"
                    ],
                    "subjective_improvement_detected": True,
                },
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
            )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["manual_prompt_packet_available"])
        self.assertTrue(body["cloud_route_available"])
        self.assertEqual(body["proposed_diff"], "")
        self.assertEqual(body["reason_code"], "coder_visual_improvement_diff_too_shallow")
        self.assertEqual(body["status"], "needs_coder_diff")

    def test_prompt_packet_pinned_app_page_backticks_invokes_sync_coder(self) -> None:
        client = self._client()
        task = (
            "Target file: `src/app/(dashboard)/design/page.tsx`\n\n"
            "Add a visible status widget at the top of the page."
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "src/app/(dashboard)/design/page.tsx",
                "coder_notes": [],
                "bundle": "test",
                "coder_blocked": True,
                "blocked_reason": "Coder model returned no content.",
                "needed_context": "Set SOURCE_PROXY_CODER_MODEL_ALIAS.",
                "reason_code": "coder_empty_model_response",
                "coder_diagnostics": {
                    "context_mode": "user_app",
                    "target_exists": True,
                    "context_slices": [
                        {"path": "src/app/(dashboard)/design/page.tsx", "kind": "target"}
                    ],
                    "forbidden_paths": ["source_proxy/"],
                },
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
            )
        self.assertEqual(response.status_code, 200, response.text)
        coder_mock.assert_not_called()
        self.assertEqual(
            response.json().get("target"),
            "src/app/(dashboard)/design/page.tsx",
        )
        body = response.json()
        self.assertEqual(body.get("context_mode"), "user_app")
        self.assertEqual(
            body.get("coder_packet", {}).get("context_slices"),
            [],
        )
        self.assertIn(
            "source_proxy/",
            body.get("coder_packet", {}).get("forbidden_paths") or [],
        )

    def test_prompt_packet_derives_context_mode_when_coder_diagnostics_missing(self) -> None:
        client = self._client()
        task = (
            "Target file: source_proxy/decision/router.py\n\n"
            "Fix the route classification for empty tasks."
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "source_proxy/decision/router.py",
                "coder_notes": [],
                "bundle": "test",
                "coder_blocked": True,
                "blocked_reason": "Coder timed out.",
                "needed_context": "Retry.",
                "reason_code": "coder_timeout",
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
            )

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body.get("context_mode"), "agent_internal")
        self.assertEqual(
            body.get("coder_packet", {}).get("context_slices", [])[0].get("path"),
            "source_proxy/decision/router.py",
        )
        self.assertIn(
            "src/app/",
            body.get("coder_packet", {}).get("forbidden_paths") or [],
        )

    def test_prompt_packet_last_target_line_wins_for_fast_path(self) -> None:
        client = self._client()
        task = (
            "Target file: src/lib/ignore-me.ts\n"
            "Target file: src/app/(group)/final/page.tsx\n\n"
            "Add padding to the hero section."
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "src/app/(group)/final/page.tsx",
                "coder_notes": [],
                "bundle": "test",
                "coder_blocked": True,
                "blocked_reason": "Coder model returned no content.",
                "needed_context": "Set SOURCE_PROXY_CODER_MODEL_ALIAS.",
                "reason_code": "coder_empty_model_response",
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
            )
        self.assertEqual(response.status_code, 200, response.text)
        coder_mock.assert_not_called()
        self.assertEqual(
            response.json().get("target"),
            "src/app/(group)/final/page.tsx",
        )

    def test_prompt_packet_pinned_lib_file_still_invokes_sync_coder(self) -> None:
        client = self._client()
        task = (
            "Target file: src/lib/coding/example.ts\n\n"
            "Add export const FOO = 1."
        )
        with patch(
            "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
        ) as coder_mock:
            coder_mock.return_value = {
                "proposed_diff": "",
                "target": "src/lib/coding/example.ts",
                "coder_notes": [],
                "bundle": "test",
            }
            response = client.post(
                "/v1/decisions/prompt-packet",
                json={"task": task, "wants_implementation": True},
        )
        self.assertEqual(response.status_code, 200, response.text)
        coder_mock.assert_not_called()

    def test_prompt_packet_dummy_trial_prompt_gets_deterministic_preview(self) -> None:
        client = self._client()
        target = "tests/ui-agent-trials/fixtures/dummy-coding-targets/component-trial.tsx"
        task = (
            f"Target file: {target}\n\n"
            "the tiny badge helper thing feels a little too binary, can u make it "
            "support a warning-ish state too? i dont remember the file name, it is "
            "one of the dummy trial bits. preview only, no apply no commit no push."
        )
        previous_project_path = os.environ.get("SPIRIT_PROJECT_PATH")
        os.environ["SPIRIT_PROJECT_PATH"] = str(Path(__file__).resolve().parents[2])
        try:
            with patch(
                "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
            ) as coder_mock:
                response = client.post(
                    "/v1/decisions/prompt-packet",
                    json={
                        "task": task,
                        "wants_implementation": True,
                        "needs_codebase_context": True,
                        "target_files": [target],
                        "targeted_files": [target],
                    },
                )
        finally:
            if previous_project_path is None:
                os.environ.pop("SPIRIT_PROJECT_PATH", None)
            else:
                os.environ["SPIRIT_PROJECT_PATH"] = previous_project_path

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        coder_mock.assert_not_called()
        self.assertEqual(body.get("target"), target)
        self.assertEqual(
            body.get("coder_diagnostics", {}).get("context_mode"),
            "dummy_trial_fixture",
        )
        self.assertIn(
            body.get("reason_code"),
            {"dummy_trial_preview_diff", "coder_no_changes_needed"},
        )
        if body.get("reason_code") == "dummy_trial_preview_diff":
            self.assertTrue(body.get("coder_agent_local_diff"))
            self.assertIn('"success" | "warning"', body.get("proposed_diff") or "")
        else:
            self.assertTrue(body.get("already_satisfied"))
            self.assertEqual(body.get("proposed_diff"), "")
        self.assertNotEqual(body.get("reason_code"), "coder_response_repair_exhausted")

    def test_prompt_packet_dummy_no_diff_trial_reports_already_satisfied(self) -> None:
        client = self._client()
        target = "tests/ui-agent-trials/fixtures/dummy-coding-targets/no-diff-trial.json"
        task = (
            f"Target file: {target}\n\n"
            "check that no-diff json thing already says already-satisfied. "
            "if it does, dont invent a patch just to look useful."
        )
        previous_project_path = os.environ.get("SPIRIT_PROJECT_PATH")
        os.environ["SPIRIT_PROJECT_PATH"] = str(Path(__file__).resolve().parents[2])
        try:
            with patch(
                "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
            ) as coder_mock:
                response = client.post(
                    "/v1/decisions/prompt-packet",
                    json={
                        "task": task,
                        "wants_implementation": True,
                        "needs_codebase_context": True,
                        "target_files": [target],
                        "targeted_files": [target],
                    },
                )
        finally:
            if previous_project_path is None:
                os.environ.pop("SPIRIT_PROJECT_PATH", None)
            else:
                os.environ["SPIRIT_PROJECT_PATH"] = previous_project_path

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        coder_mock.assert_not_called()
        self.assertEqual(body.get("target"), target)
        self.assertEqual(body.get("reason_code"), "coder_no_changes_needed")
        self.assertTrue(body.get("already_satisfied"))
        self.assertFalse(body.get("coder_agent_local_diff"))
        self.assertEqual(body.get("proposed_diff"), "")

    def test_prompt_packet_dummy_backend_route_trial_reports_already_satisfied_when_ok_param_present(
        self,
    ) -> None:
        client = self._client()
        target = "tests/ui-agent-trials/fixtures/dummy-coding-targets/backend-route-trial.ts"
        task = (
            f"Target file: {target}\n\n"
            "that fake route response helper should let me pass ok=false for sad paths. "
            "preview diff only pls."
        )
        previous_project_path = os.environ.get("SPIRIT_PROJECT_PATH")
        os.environ["SPIRIT_PROJECT_PATH"] = str(Path(__file__).resolve().parents[2])
        try:
            with patch(
                "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
            ) as coder_mock:
                response = client.post(
                    "/v1/decisions/prompt-packet",
                    json={
                        "task": task,
                        "wants_implementation": True,
                        "needs_codebase_context": True,
                        "target_files": [target],
                        "targeted_files": [target],
                    },
                )
        finally:
            if previous_project_path is None:
                os.environ.pop("SPIRIT_PROJECT_PATH", None)
            else:
                os.environ["SPIRIT_PROJECT_PATH"] = previous_project_path

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        coder_mock.assert_not_called()
        self.assertEqual(body.get("target"), target)
        self.assertEqual(body.get("reason_code"), "coder_no_changes_needed")
        self.assertTrue(body.get("already_satisfied"))
        self.assertEqual(body.get("proposed_diff"), "")
        self.assertEqual(
            body.get("coder_diagnostics", {}).get("context_mode"),
            "dummy_trial_fixture",
        )

    def test_prompt_packet_agent_trials_ui_test_prompt_gets_deterministic_preview(self) -> None:
        client = self._client()
        target = "src/lib/coding/__tests__/agent-trials-ui.test.ts"
        task = (
            f"Target file: {target}\n\n"
            "can u add a focused test around the thing that classifies productive previews? "
            "i dont know the exact helper file, find the trial ui test if thats the right spot. "
            "preview diff only."
        )
        previous_project_path = os.environ.get("SPIRIT_PROJECT_PATH")
        os.environ["SPIRIT_PROJECT_PATH"] = str(Path(__file__).resolve().parents[2])
        try:
            with patch(
                "source_proxy.api.decision.propose_coder_agent_diff_payload_from_plan",
            ) as coder_mock:
                response = client.post(
                    "/v1/decisions/prompt-packet",
                    json={
                        "task": task,
                        "wants_implementation": True,
                        "needs_codebase_context": True,
                        "target_files": [target],
                        "targeted_files": [target],
                    },
                )
        finally:
            if previous_project_path is None:
                os.environ.pop("SPIRIT_PROJECT_PATH", None)
            else:
                os.environ["SPIRIT_PROJECT_PATH"] = previous_project_path

        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        coder_mock.assert_not_called()
        self.assertTrue(body.get("coder_agent_local_diff"))
        self.assertEqual(body.get("target"), target)
        self.assertEqual(
            body.get("reason_code"),
            "deterministic_agent_trials_ui_test_preview",
        )
        self.assertIn(
            "keeps productive preview classification useful for manual retests",
            body.get("proposed_diff") or "",
        )
        self.assertNotEqual(body.get("reason_code"), "coder_model_not_configured")


if __name__ == "__main__":
    unittest.main()
