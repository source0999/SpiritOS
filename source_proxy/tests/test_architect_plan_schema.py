from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from dataclasses import FrozenInstanceError
from unittest import mock

from source_proxy.planning.plan import (
    PLAN_SCHEMA_VERSION,
    AcceptanceCriterion,
    ArchitectPlan,
    BundleSnapshot,
    CoderPacket,
    ContentConstraints,
    ContextSlice,
    PlanBudget,
    PlanSchemaTooNew,
    TargetFile,
    TaskClassification,
    VerificationCheck,
    VerificationPlan,
    load_plan,
    save_plan,
)
from source_proxy.tasks.long_running import create_long_running_task, reset_long_running_tasks


def _empty_plan() -> ArchitectPlan:
    return ArchitectPlan(
        plan_id="plan-empty",
        task_id="task-empty",
        schema_version=PLAN_SCHEMA_VERSION,
        created_at="2026-05-13T00:00:00Z",
        source_task="Target file: src/app/page.tsx\nNo-op.",
        bundle_snapshot=BundleSnapshot(
            bundle_path="/workspace/repomix-output.xml",
            bundle_sha256="0" * 64,
            workspace_root="/workspace",
            generated_at="2026-05-13T00:00:00Z",
        ),
        classification=TaskClassification(
            task_class="implement",
            visual_change=False,
            designer_required=False,
            estimated_complexity="trivial",
        ),
        coder_packet=CoderPacket(
            target_file=TargetFile(
                path="src/app/page.tsx",
                exists=False,
                sha256_before=None,
            ),
            operation="create",
            acceptance_criteria=[],
            constraints=ContentConstraints(
                must_contain=[],
                must_not_contain=[],
                preserve_imports=[],
                preserve_exports=[],
                max_added_lines=None,
                max_removed_lines=None,
            ),
            context_slices=[],
            forbidden_paths=[],
            style_directives=[],
        ),
        verification_plan=VerificationPlan(
            required_checks=[],
            designer_review_required=False,
            architect_review_required=False,
        ),
        budget=PlanBudget(
            max_coder_attempts=3,
            max_total_seconds=120,
            cloud_escalation_allowed=True,
        ),
    )


def _full_plan() -> ArchitectPlan:
    plan = _empty_plan()
    return ArchitectPlan(
        plan_id="plan-full",
        task_id=plan.task_id,
        schema_version=PLAN_SCHEMA_VERSION,
        created_at=plan.created_at,
        source_task="Target file: .\\src\\components\\ThemeStrip.tsx\nAdd hover.",
        bundle_snapshot=plan.bundle_snapshot,
        classification=TaskClassification(
            task_class="style",
            visual_change=True,
            designer_required=False,
            estimated_complexity="small",
        ),
        coder_packet=CoderPacket(
            target_file=TargetFile(
                path=".\\src\\components\\ThemeStrip.tsx",
                exists=True,
                sha256_before="a" * 64,
            ),
            operation="edit",
            acceptance_criteria=[
                AcceptanceCriterion(
                    id="hover-state",
                    description="Active swatch has a subtle hover state.",
                    kind="behavioral",
                ),
                AcceptanceCriterion(
                    id="class-fragment",
                    description="Contains transition-all.",
                    kind="literal",
                ),
            ],
            constraints=ContentConstraints(
                must_contain=["transition-all"],
                must_not_contain=["style={{"],
                preserve_imports=["cn"],
                preserve_exports=["ThemeStrip"],
                max_added_lines=40,
                max_removed_lines=20,
            ),
            context_slices=[
                ContextSlice(
                    path=".\\src\\components\\ThemeStrip.tsx",
                    kind="target",
                    sha256="b" * 64,
                    content="export function ThemeStrip() {}",
                    line_range=(1, 10),
                )
            ],
            forbidden_paths=[".\\source_proxy\\"],
            style_directives=["Tailwind utility classes only"],
        ),
        verification_plan=VerificationPlan(
            required_checks=[
                VerificationCheck(
                    id="typecheck",
                    command=["npm", "run", "typecheck"],
                    blocking=True,
                    timeout_seconds=30,
                )
            ],
            designer_review_required=False,
            architect_review_required=True,
        ),
        budget=plan.budget,
    )


class ArchitectPlanSchemaTests(unittest.TestCase):
    def test_plan_schema_version_constant_is_one(self) -> None:
        self.assertEqual(PLAN_SCHEMA_VERSION, 1)

    def test_roundtrip_empty_plan(self) -> None:
        plan = _empty_plan()

        restored = ArchitectPlan.from_dict(json.loads(json.dumps(plan.to_dict())))

        self.assertEqual(restored, plan)

    def test_roundtrip_full_plan(self) -> None:
        plan = _full_plan()

        restored = ArchitectPlan.from_dict(json.loads(json.dumps(plan.to_dict())))

        self.assertEqual(restored, plan)
        self.assertEqual(restored.coder_packet.target_file.path, "src/components/ThemeStrip.tsx")
        self.assertEqual(
            restored.coder_packet.context_slices[0].line_range,
            (1, 10),
        )

    def test_rejects_unknown_schema_version(self) -> None:
        payload = _empty_plan().to_dict()
        payload["schema_version"] = PLAN_SCHEMA_VERSION + 1

        with self.assertRaises(PlanSchemaTooNew):
            ArchitectPlan.from_dict(payload)

    def test_migrates_older_schema_version(self) -> None:
        payload = _empty_plan().to_dict()
        payload["schema_version"] = 0

        with mock.patch.dict(
            "source_proxy.planning.plan.PLAN_MIGRATORS",
            {0: lambda old: {**old, "schema_version": 1}},
            clear=True,
        ):
            restored = ArchitectPlan.from_dict(payload)

        self.assertEqual(restored.schema_version, PLAN_SCHEMA_VERSION)

    def test_rejects_unknown_top_level_field(self) -> None:
        payload = _empty_plan().to_dict()
        payload["extra"] = True

        with self.assertRaisesRegex(ValueError, "Unknown field"):
            ArchitectPlan.from_dict(payload)

    def test_rejects_unknown_nested_field(self) -> None:
        payload = _empty_plan().to_dict()
        payload["coder_packet"]["target_file"]["extra"] = True

        with self.assertRaisesRegex(ValueError, "Unknown field"):
            ArchitectPlan.from_dict(payload)

    def test_coder_packet_target_path_normalized(self) -> None:
        plan = _full_plan()

        self.assertEqual(plan.coder_packet.target_file.path, "src/components/ThemeStrip.tsx")
        self.assertEqual(plan.coder_packet.forbidden_paths, ["source_proxy/"])

    def test_dataclasses_are_frozen(self) -> None:
        plan = _empty_plan()

        with self.assertRaises(FrozenInstanceError):
            plan.plan_id = "mutated"  # type: ignore[misc]

    def test_save_and_load_plan_persists_to_task_sqlite(self) -> None:
        previous_database_path = os.environ.get("SOURCE_PROXY_LONG_RUNNING_TASKS_DB")
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = os.path.join(
                tmp,
                "tasks.sqlite3",
            )
            reset_long_running_tasks()
            created = create_long_running_task("Persist plan")
            task_id = created["task"]["id"]
            payload = _full_plan().to_dict()
            payload["task_id"] = task_id
            plan = ArchitectPlan.from_dict(payload)

            save_plan(task_id, plan)
            loaded = load_plan(task_id)

            with closing(sqlite3.connect(os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"])) as db:
                columns = {
                    row[1]
                    for row in db.execute("PRAGMA table_info(long_running_tasks)")
                }
                row = db.execute(
                    "SELECT architect_plan_json FROM long_running_tasks WHERE id = ?",
                    (task_id,),
                ).fetchone()

            self.assertIn("architect_plan_json", columns)
            self.assertIsNotNone(row[0])
            self.assertEqual(loaded, plan)
            reset_long_running_tasks()

        if previous_database_path is None:
            os.environ.pop("SOURCE_PROXY_LONG_RUNNING_TASKS_DB", None)
        else:
            os.environ["SOURCE_PROXY_LONG_RUNNING_TASKS_DB"] = previous_database_path


if __name__ == "__main__":
    unittest.main()
