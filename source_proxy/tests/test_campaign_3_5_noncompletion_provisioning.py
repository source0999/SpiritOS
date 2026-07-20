from __future__ import annotations

import json
from pathlib import Path

from source_proxy.benchmarks.campaign_3_5_assets.provisioning import validate_noncompletion_profiles


ROOT = Path(__file__).resolve().parents[2]


def test_all_blocked_and_escalation_profiles_have_independent_initial_conditions() -> None:
    tasks = json.loads((ROOT / "benchmarks/coder-backend-100/v1.1/tasks.json").read_text(encoding="utf-8"))
    result = validate_noncompletion_profiles(tasks)
    assert result["passed"] is True
    assert result["task_count"] == 30
