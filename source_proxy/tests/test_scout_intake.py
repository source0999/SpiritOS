from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from source_proxy.api.scout_intake import router


def _payload(decision: str = "promote") -> bytes:
    packet = {
        "schema_version": 1,
        "packet_id": "pkt_1",
        "source_uri": "https://example.com/feed.xml",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "entity_tags": ["example"],
        "summary": (
            "This is a sufficiently long packet summary for intake testing, with enough "
            "detail to satisfy the Scout packet schema minimum length."
        ),
        "impact_analysis": (
            "This is a sufficiently long impact analysis for intake testing, with enough "
            "detail to satisfy the Scout packet schema minimum length."
        ),
        "confidence_score": 0.8,
        "graph_relations": [],
        "status": "debugger_pending",
        "provenance": {
            "raw_event_id": "raw_1",
            "extracted_artifact_path": None,
            "llm_model": "test",
            "llm_latency_ms": 1,
            "synthesized_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    verdict = {
        "schema_version": 1,
        "packet_id": "pkt_1",
        "decision": decision,
        "tier_reached": 3,
        "reason_codes": [],
        "findings": [],
        "source_quality_score": 0.8,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(
        {
            "promotion_id": "promo_1",
            "approved": True,
            "approved_by": "tester",
            "packet": packet,
            "verdict": verdict,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _signature(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


class ScoutIntakeTests(unittest.TestCase):
    def test_requires_valid_signature_and_promote_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            body = _payload()
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            env = {
                "SCOUT_PROMOTION_SIGNING_KEY": "secret",
                "SOURCE_PROXY_SCOUT_INTAKE_LOG": str(Path(temp_dir) / "intake.jsonl"),
            }
            with patch.dict(os.environ, env, clear=False):
                bad = client.post(
                    "/v1/scout-intake/promotion",
                    content=body,
                    headers={"X-Scout-Signature": "sha256=bad"},
                )
                good = client.post(
                    "/v1/scout-intake/promotion",
                    content=body,
                    headers={"X-Scout-Signature": _signature("secret", body)},
                )
                not_promote_body = _payload("surface")
                not_promote = client.post(
                    "/v1/scout-intake/promotion",
                    content=not_promote_body,
                    headers={
                        "X-Scout-Signature": _signature("secret", not_promote_body)
                    },
                )

            self.assertEqual(bad.status_code, 401)
            self.assertEqual(good.status_code, 200)
            self.assertEqual(
                good.json()["result"]["authority"],
                "append_only_evidence",
            )
            self.assertFalse(good.json()["result"]["applied"])
            self.assertFalse(good.json()["result"]["approved_proxy_action"])
            self.assertEqual(not_promote.status_code, 409)
            self.assertTrue((Path(temp_dir) / "intake.jsonl").exists())

    def test_requires_explicit_intake_log_path_before_writing_memory(self) -> None:
        body = _payload()
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        with patch.dict(
            os.environ,
            {
                "SCOUT_PROMOTION_SIGNING_KEY": "secret",
                "SOURCE_PROXY_SCOUT_INTAKE_LOG": "",
            },
            clear=False,
        ):
            response = client.post(
                "/v1/scout-intake/promotion",
                content=body,
                headers={"X-Scout-Signature": _signature("secret", body)},
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn("SOURCE_PROXY_SCOUT_INTAKE_LOG", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
