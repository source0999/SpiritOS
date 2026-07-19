from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validate-campaign-3-5-trace-event-map.py"
SPEC = importlib.util.spec_from_file_location("campaign_3_5_trace_map_validator", SCRIPT)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)
MAP = ROOT / "benchmarks/coder-backend-100/v1.1/trace-event-contract-map.json"


class Campaign35TraceEventMapTests(unittest.TestCase):
    def test_current_map_has_complete_static_emitter_coverage(self) -> None:
        self.assertEqual(validator.validate(MAP), [])

    def test_validator_rejects_duplicate_mapping_and_missing_payload(self) -> None:
        document = json.loads(MAP.read_text(encoding="utf-8"))
        document["mappings"].append(dict(document["mappings"][0]))
        document["mappings"][1]["payload_mapping"] = {}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "map.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            errors = validator.validate(path)

        self.assertTrue(any("duplicate benchmark mappings" in error for error in errors))
        self.assertTrue(any("payload mapping is missing" in error for error in errors))

    def test_validator_rejects_unknown_or_unemitted_production_event(self) -> None:
        document = json.loads(MAP.read_text(encoding="utf-8"))
        document["mappings"][0]["production_event"]["name"] = "not_a_real_emitter"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "map.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            errors = validator.validate(path)

        self.assertTrue(any("production event is not emitted" in error for error in errors))

    def test_validator_rejects_a_runtime_receipt_with_a_failed_browser_proof(self) -> None:
        document = json.loads(MAP.read_text(encoding="utf-8"))
        receipt_path = ROOT / document["runtime_confirmation"]["receipt"]
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["browser_verification_status"] = "failed"
        original = receipt_path.read_text(encoding="utf-8")
        try:
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            errors = validator.validate(MAP)
        finally:
            receipt_path.write_text(original, encoding="utf-8")

        self.assertTrue(any("browser_verification_status mismatch" in error for error in errors))
