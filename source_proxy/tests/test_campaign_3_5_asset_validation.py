from __future__ import annotations

import json
from pathlib import Path

from source_proxy.benchmarks.campaign_3_5_assets.validation import validate_builders


ROOT = Path(__file__).resolve().parents[2]


def test_all_fixture_builders_pass_independent_reproducibility_and_boundary_checks() -> None:
    tasks = json.loads((ROOT / "benchmarks/coder-backend-100/v1.1/tasks.json").read_text(encoding="utf-8"))
    report = validate_builders(tasks)

    assert report["passed"] is True
    assert report["fixture_count"] == 65
    assert len(report["validated_fixture_ids"]) == 65
