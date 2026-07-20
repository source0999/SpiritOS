"""Combine independently produced runtime-validation reports without hiding gaps."""
from __future__ import annotations

from typing import Any


def combine_runtime_reports(*reports: dict[str, Any]) -> dict[str, Any]:
    task_rows: dict[str, dict[str, Any]] = {}
    for report in reports:
        for task in report.get("tasks", []):
            task_id = task["task_id"]
            if task_id in task_rows:
                raise ValueError("campaign_3_5_runtime_report_task_duplicate")
            task_rows[task_id] = task
    return {
        "schema_version": "campaign-3.5-combined-runtime-validation/v1",
        "passed": all(task["passed"] for task in task_rows.values()),
        "task_count": len(task_rows),
        "tasks": [task_rows[task_id] for task_id in sorted(task_rows)],
        "validated_task_ids": [task_id for task_id in sorted(task_rows) if task_rows[task_id]["passed"]],
    }
