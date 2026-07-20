from __future__ import annotations

import json
from pathlib import Path

from source_proxy.benchmarks.campaign_3_5_assets.reference_validation import validate_core_references


ROOT = Path(__file__).resolve().parents[2]


def test_core_completed_fixture_references_pass_private_semantic_probes() -> None:
    tasks = json.loads((ROOT / "benchmarks/coder-backend-100/v1.1/tasks.json").read_text(encoding="utf-8"))
    report = validate_core_references(tasks)
    assert report["passed"] is True
    assert report["task_count"] == 16
