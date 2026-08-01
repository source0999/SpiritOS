from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from source_proxy.context.model_ready_packet import (
    CANONICAL_SECTION_ORDER,
    build_model_ready_packet,
    canonical_packet_bytes,
    packet_sha256,
    validate_model_ready_packet_schema,
)
from source_proxy.context.packet_quality_validator import validate_packet_quality


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "docs/architecture/jcode-qualification/pipeline-diagnosis/glm-review/MODEL_READY_PACKET_SCHEMA.json"
SOURCE_PATH = "qualification/source.py"
TEST_PATH = "qualification/test_source.py"
MOUNTED_PATHS = (SOURCE_PATH, TEST_PATH)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def packet_fixture() -> dict[str, object]:
    return build_model_ready_packet(
        identity={
            "task_id": "PIPE-QUAL-001",
            "run_id": "run-001",
            "campaign_id": "C2J",
            "prompt_hash": _hash("prompt"),
            "acceptance_hash": _hash("acceptance"),
            "context_hash": _hash("context"),
            "base_commit": "3169e2eae83657170c6df1daf1560cd4500f9f4e",
            "executor_id": "fake-executor",
            "model_profile_id": "fake-model",
            "tool_profile_id": "qualification-tools",
            "evaluator_profile_id": "fake-evaluator",
        },
        objective="Add a deterministic helper to qualification/source.py.",
        desired_observable_behavior="The helper returns the normalized fixture value.",
        acceptance_criteria=["pytest -q qualification/test_source.py passes."],
        writable_files=[SOURCE_PATH],
        read_only_files=[TEST_PATH],
        mounted_tool_paths=MOUNTED_PATHS,
        focused_validation_command="pytest -q qualification/test_source.py",
        stop_condition="Stop after the focused test passes.",
        file_manifest=[
            {
                "path": SOURCE_PATH,
                "sha256": _hash("source"),
                "byte_count": 24,
                "content_or_excerpt": "def normalize(value):\n    return value\n",
            },
            {
                "path": TEST_PATH,
                "sha256": _hash("test"),
                "byte_count": 24,
                "content_or_excerpt": "def test_normalize():\n    assert True\n",
            },
        ],
        tools=[
            {
                "canonical_name": "read_file",
                "json_schema": {"type": "object"},
                "description": "Read a mounted file.",
                "allowed_paths": list(MOUNTED_PATHS),
                "error_contract": "returns a truthful error",
                "result_contract": "returns UTF-8 text",
                "timeout_seconds": 10,
                "evidence_output": "read receipt",
            }
        ],
        prohibited_paths=["benchmarks/**"],
        context_limit_tokens=4096,
    )


def validate(packet: dict[str, object], paired: bytes | None = None):
    return validate_packet_quality(
        packet,
        required_source_paths=[SOURCE_PATH],
        required_test_paths=[TEST_PATH],
        sandbox_mounted_paths=MOUNTED_PATHS,
        paired_lane_packet_bytes=paired,
    )


class ModelReadyPacketTests(unittest.TestCase):
    def test_packet_is_task_first_schema_valid_and_ready(self) -> None:
        packet = packet_fixture()
        report = validate(packet, canonical_packet_bytes(packet))

        self.assertEqual(packet["schema_version"], "source-proxy.model-ready-packet/v1")
        self.assertEqual(packet["ordering"], list(CANONICAL_SECTION_ORDER))
        self.assertEqual(validate_model_ready_packet_schema(packet), [])
        self.assertEqual(report.verdict, "PACKET_READY")
        self.assertLessEqual(report.measurements["first_critical_content_byte"], 1024)
        self.assertGreaterEqual(report.measurements["relevance_ratio"], 0.40)

    def test_schema_document_is_valid_json_and_matches_version(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], "source-proxy.model-ready-packet/v1")
        self.assertIn("identity", schema["required"])
        self.assertIn("quality_metrics", schema["required"])

    def test_packet_bytes_and_hash_are_deterministic(self) -> None:
        first = packet_fixture()
        second = packet_fixture()
        self.assertEqual(canonical_packet_bytes(first), canonical_packet_bytes(second))
        self.assertEqual(packet_sha256(first), packet_sha256(second))

    def test_controlled_failures_are_rejected(self) -> None:
        cases = {
            "missing_task": lambda p: p.__setitem__("task", {}),
            "missing_acceptance": lambda p: p["task"].__setitem__("acceptance_criteria", []),
            "missing_source": lambda p: p["context"].__setitem__("file_manifest", p["context"]["file_manifest"][1:]),
            "missing_test": lambda p: p["context"].__setitem__("file_manifest", p["context"]["file_manifest"][:1]),
            "path_mismatch": lambda p: p["task"].__setitem__("mounted_tool_paths", [SOURCE_PATH]),
            "relevance_below": lambda p: p["quality_metrics"].__setitem__("relevant_context_ratio", 0.39),
            "governance": lambda p: p["context"]["file_manifest"][0].__setitem__("content_or_excerpt", "Campaign 2-J policy"),
            "contradiction": lambda p: p["constraints"].__setitem__("network_policy", "allowed"),
            "critical_truncation": lambda p: p["context"].__setitem__("truncation_receipt", "critical bytes omitted"),
            "duplicate_sections": lambda p: p["ordering"].append("task"),
            "nondeterministic_order": lambda p: p["ordering"].__setitem__(0, "task"),
            "hidden_answer": lambda p: p["context"]["file_manifest"][0].__setitem__("content_or_excerpt", "__HIDDEN_ANSWER__"),
            "insufficient_budget": lambda p: p["quality_metrics"].__setitem__("available_output_budget_tokens", 1279),
        }
        for name, mutate in cases.items():
            with self.subTest(name=name):
                packet = copy.deepcopy(packet_fixture())
                mutate(packet)
                self.assertFalse(validate(packet).ready)

    def test_paired_lane_mismatch_is_rejected(self) -> None:
        self.assertIn("paired_lane_packet_mismatch", validate(packet_fixture(), b"other lane").failures)


if __name__ == "__main__":
    unittest.main()
