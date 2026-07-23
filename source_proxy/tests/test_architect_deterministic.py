from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from source_proxy.planning import architect as architect_module
from source_proxy.approval.external_gate import ExternalGateError
from source_proxy.coding.recovery import render_evidence_guided_repair_model_task
from source_proxy.planning.architect import (
    ArchitectLLMError,
    Block,
    FallthroughToLLM,
    Plan,
    plan_task_deterministically,
    plan_task_with_llm,
)
from source_proxy.planning.plan import ArchitectPlan
from source_proxy.planning.plan import task_spec_from_plan, validate_task_spec_for_packet


def _valid_llm_plan_payload(target_path: str) -> dict[str, object]:
    return {
        "classification": {
            "task_class": "fix",
            "visual_change": False,
            "designer_required": False,
            "estimated_complexity": "small",
        },
        "coder_packet": {
            "target_file": {
                "path": target_path,
                "exists": True,
                "sha256_before": None,
            },
            "operation": "edit",
            "acceptance_criteria": [],
            "constraints": {},
            "context_slices": [],
            "forbidden_paths": [],
            "style_directives": [],
        },
    }


class DeterministicArchitectTests(unittest.TestCase):
    def test_literal_roles_handle_transformations_preservation_and_exact_paths(self) -> None:
        task = "\n".join(
            [
                'Replace the label "Old" with "New".',
                'Do not remove "RequiredLiteral".',
                'Do not change the string "Stable" to "Unwanted".',
                'Do not include "debug-only".',
                'Output must contain "worker.py".',
                'Include "config/settings.json" in the rendered output.',
                'Load settings from ".env.local" and preserve ".gitignore".',
            ]
        )

        self.assertEqual(
            architect_module._literal_requirements(task),
            [
                "New",
                "RequiredLiteral",
                "Stable",
                "worker.py",
                "config/settings.json",
            ],
        )
        self.assertEqual(
            architect_module._negative_literal_requirements(task),
            ["debug-only"],
        )

    def test_secondary_literal_is_criterion_bound_without_becoming_primary_constraint(self) -> None:
        task = 'File tests/test_service.py must contain `SecondaryLiteral`.'

        criteria = architect_module._acceptance_criteria(task, "src/service.py")
        constraints = architect_module._content_constraints(
            task,
            "def service():\n    return True\n",
            "src/service.py",
        )

        literal = next(item for item in criteria if item.id == "literal-1")
        self.assertEqual(
            literal.description,
            'File "tests/test_service.py" must contain "SecondaryLiteral".',
        )
        self.assertNotIn("SecondaryLiteral", constraints.must_contain)

    def test_exact_filename_and_path_intent_excludes_bare_artifact_nouns(self) -> None:
        positive = "\n".join(
            [
                'Display the exact filename "worker.py".',
                'The filename must equal "runner.py".',
                'Show the exact text "config/settings.json".',
                '"nested/report.json" must be displayed.',
                'Include "assets/manifest.json" in the rendered output.',
            ]
        )
        bare_artifacts = "\n".join(
            [
                'File "worker.py" handles background jobs.',
                'Artifact "config/settings.json" stores settings.',
                'Target "src/main.py" imports the worker.',
                'Use the file path "nested/report.json" for persistence.',
            ]
        )

        self.assertEqual(
            architect_module._literal_requirements(positive),
            [
                "worker.py",
                "runner.py",
                "config/settings.json",
                "nested/report.json",
                "assets/manifest.json",
            ],
        )
        self.assertEqual(architect_module._literal_requirements(bare_artifacts), [])

    def test_common_secondary_literal_phrasings_and_bt07_postfix_paths_bind(
        self,
    ) -> None:
        target = "src/primary.py"
        cases = {
            'File src/secondary.py must contain "SecondaryLiteral".': (
                "SecondaryLiteral",
                "src/secondary.py",
            ),
            'In src/secondary.py, add "SecondaryLiteral".': (
                "SecondaryLiteral",
                "src/secondary.py",
            ),
            'Add "SecondaryLiteral" to src/secondary.py.': (
                "SecondaryLiteral",
                "src/secondary.py",
            ),
            'Ensure "SecondaryLiteral" is present in the file src/secondary.py.': (
                "SecondaryLiteral",
                "src/secondary.py",
            ),
            '`normalize_username` in `src/users.py` and `normalize_email` in '
            '`src/contacts.py` repeat the same cleanup.': (
                "normalize_username",
                "src/users.py",
            ),
        }
        for task, expected in cases.items():
            with self.subTest(task=task):
                bindings = architect_module._literal_requirement_bindings(task, target)
                self.assertIn(expected, bindings)

        bt07 = (
            '`normalize_username` in `src/users.py` and `normalize_email` in '
            '`src/contacts.py` repeat the same whitespace-and-lowercase cleanup.'
        )
        self.assertEqual(
            architect_module._literal_requirement_bindings(bt07, target),
            [
                ("normalize_username", "src/users.py"),
                ("normalize_email", "src/contacts.py"),
            ],
        )

    def test_short_and_duplicate_final_transformations_keep_occurrence_bindings(
        self,
    ) -> None:
        target = "src/primary.ts"
        task = "\n".join(
            [
                'Change "x" to "y" in src/secondary.ts.',
                'Replace the label "UI" with "UX" in src/primary.ts.',
                'Change "A" to "B" in src/secondary.ts.',
                'Change "X" to "B" in src/primary.ts.',
            ]
        )

        self.assertEqual(
            architect_module._literal_requirement_bindings(task, target),
            [
                ("y", "src/secondary.ts"),
                ("UX", "src/primary.ts"),
                ("B", "src/secondary.ts"),
                ("B", "src/primary.ts"),
            ],
        )

    def test_active_exports_cover_alias_default_and_typescript_declarations(self) -> None:
        content = (
            "const localPublic = 1;\n"
            "const localDefault = () => 1;\n"
            "export { localPublic as Public, localDefault as default };\n"
            "export enum Mode { One }\n"
            "export abstract class Base {}\n"
            "export declare function contract(): void;\n"
            "export namespace API { export const nested = 1; }\n"
        )

        self.assertEqual(
            architect_module._active_export_names(content),
            ["Mode", "Base", "contract", "API", "nested", "Public", "default"],
        )
        self.assertNotIn("localPublic", architect_module._active_export_names(content))
        self.assertNotIn("localDefault", architect_module._active_export_names(content))

    def test_bounded_create_uses_readable_reference_outside_writable_target_scope(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference = root / "src/app/coding/page.tsx"
            reference.parent.mkdir(parents=True)
            reference.write_text(
                "export default function CodingPage() { return null; }\n",
                encoding="utf-8",
            )
            target = "src/app/new/page.tsx"
            task = "\n".join(
                [
                    f"Target file: {target}",
                    "Create the new page.",
                    "Proposal task:",
                    "```json",
                    json.dumps(
                        {
                            "allowed_files": [target],
                            "expected_checks": ["target-only"],
                            "forbidden_files": [".env"],
                            "mode": "proposal",
                            "rollback_hint": "git restore <target_file>",
                            "target_file": target,
                            "task": "Create the new page.",
                        }
                    ),
                    "```",
                ]
            )

            result = plan_task_deterministically(
                task,
                "task-bounded-readable-reference",
                root,
                allowed_paths=("src/app/new/",),
                readable_paths=("src/app/",),
            )

        self.assertIsInstance(result, Plan)
        self.assertEqual(
            [item.path for item in result.plan.coder_packet.context_slices],
            ["src/app/coding/page.tsx"],
        )

    def test_python_relative_import_is_included_in_scoped_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "src" / "orders"
            package.mkdir(parents=True)
            (package / "service.py").write_text(
                "def total():\n    return 1\n",
                encoding="utf-8",
            )
            (package / "api.py").write_text(
                "from .service import total\n\ndef endpoint():\n    return total()\n",
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "Target file: src/orders/api.py\nFix the endpoint bug.",
                "task-python-context",
                root,
                allowed_paths=("src/",),
            )

        self.assertIsInstance(result, Plan)
        self.assertIn(
            "src/orders/service.py",
            [item.path for item in result.plan.coder_packet.context_slices],
        )

    def test_scoped_target_symlink_cannot_read_outside_resolved_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "outside").mkdir()
            secret = root / "outside" / "secret.py"
            secret.write_text("SECRET = 'must-not-enter-context'\n", encoding="utf-8")
            link = root / "src" / "linked.py"
            try:
                link.symlink_to(secret)
            except OSError as error:
                self.skipTest(f"symlinks unavailable: {error}")

            result = plan_task_deterministically(
                "Target file: src/linked.py\nFix the bug.",
                "task-symlink-scope",
                root,
                allowed_paths=("src/",),
            )

        self.assertIsInstance(result, Block)
        self.assertEqual(result.reason, "architect_target_outside_allowed_scope")

    def test_existing_explicit_target_produces_plan_with_context_and_literal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "src/components/Footer.tsx"
            helper = root / "src/components/footer-helper.ts"
            target.parent.mkdir(parents=True)
            helper.write_text("export const helper = 'ok';\n", encoding="utf-8")
            target.write_text(
                "import { helper } from './footer-helper';\n"
                "export function Footer() { return <footer>{helper}</footer>; }\n",
                encoding="utf-8",
            )
            (root / "repomix-output.xml").write_text("<files />", encoding="utf-8")

            result = plan_task_deterministically(
                'Target file: src/components/Footer.tsx\nAdd a "Built with SpiritOS" line at the end',
                "task-footer",
                root,
            )

            self.assertIsInstance(result, Plan)
            plan = result.plan
            self.assertEqual(plan.task_id, "task-footer")
            self.assertEqual(plan.coder_packet.target_file.path, "src/components/Footer.tsx")
            self.assertTrue(plan.coder_packet.target_file.exists)
            self.assertEqual(plan.coder_packet.operation, "edit")
            self.assertIn("Built with SpiritOS", plan.coder_packet.constraints.must_contain)
            self.assertIn("source_proxy/", plan.coder_packet.forbidden_paths)
            task_spec = task_spec_from_plan(plan)
            self.assertEqual(
                task_spec.to_dict(),
                {
                    "schema_version": 1,
                    "task_type": "modify_existing_file",
                    "target": "src/components/Footer.tsx",
                    "allowed_files": ["src/components/Footer.tsx"],
                    "forbidden_files": [
                        "source_proxy/",
                        "src/components/coding/",
                        "src/lib/coding/",
                        "src/lib/spirit/apply-unified-diff.ts",
                        "scripts/",
                        "masterProxyPlan.md",
                        "masterSwarmPlan.md",
                        "notes.md",
                    ],
                    "literal_requirements": ["Built with SpiritOS"],
                    "verification": [
                        "git apply check",
                        "eslint",
                        "typecheck",
                        "literal present",
                        "target-only",
                    ],
                    "risk_tier": "low",
                    "source": "deterministic",
                },
            )
            self.assertEqual(validate_task_spec_for_packet(task_spec, plan.coder_packet), [])
            self.assertEqual(
                [slice.path for slice in plan.coder_packet.context_slices],
                ["src/components/Footer.tsx", "src/components/footer-helper.ts"],
            )
            self.assertTrue(
                any(
                    criterion.kind == "literal"
                    and "Built with SpiritOS" in criterion.description
                    for criterion in plan.coder_packet.acceptance_criteria
                )
            )
            self.assertEqual(
                ArchitectPlan.from_dict(json.loads(json.dumps(plan.to_dict()))),
                plan,
            )

    def test_missing_explicit_target_falls_through(self) -> None:
        result = plan_task_deterministically(
            "Make the dashboard prettier",
            "task-vague",
            Path.cwd(),
        )

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "no_explicit_target")

    def test_unique_named_function_resolves_existing_source_without_llm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / "src" / "backend.py").write_text(
                "def total_values(values):\n    return sum(values[:-1])\n",
                encoding="utf-8",
            )
            (root / "tests" / "test_backend.py").write_text(
                "from src.backend import total_values\n",
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "The `total_values` helper drops the last value. Fix it without mutating input.",
                "task-symbol-target",
                root,
                allowed_paths=("src/", "tests/"),
            )

        self.assertIsInstance(result, Plan)
        self.assertEqual(
            result.plan.coder_packet.target_file.path,
            "src/backend.py",
        )

    def test_valid_repair_envelope_uses_original_task_for_deterministic_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / "src" / "backend.py").write_text(
                "def list_values():\n    return VALUES[:1]\n",
                encoding="utf-8",
            )
            (root / "tests" / "test_backend.py").write_text(
                "from src.backend import list_values\n",
                encoding="utf-8",
            )
            original_task = (
                "Fix list_values in src/backend.py so its default call returns "
                "all values."
            )
            repair_task, _ = render_evidence_guided_repair_model_task(
                original_task,
                {
                    "failure_class": "verifier_rejection",
                    "source_lane": "verifier",
                    "exact_feedback": {
                        "checks": [
                            {
                                "id": "public_pytest",
                                "status": "failed",
                                "output_tail": "FAILED: default call returned one value",
                            }
                        ],
                        "duplicated_trace": "x" * 50_000,
                    },
                },
            )

            result = plan_task_deterministically(
                repair_task,
                "task-evidence-guided-repair-plan",
                root,
                allowed_paths=("src/",),
                readable_paths=("src/", "tests/"),
            )

        self.assertIsInstance(result, Plan, result)
        assert isinstance(result, Plan)
        self.assertEqual(
            result.plan.coder_packet.target_file.path,
            "src/backend.py",
        )
        self.assertEqual(result.plan.source_task, repair_task)

    def test_route_literal_prefers_implementation_over_test_usage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / "src" / "backend.py").write_text(
                "ROUTE = '/items'\n\ndef list_items():\n    return [1, 2]\n",
                encoding="utf-8",
            )
            (root / "tests" / "test_backend.py").write_text(
                "def test_route():\n    assert '/items'\n",
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "Add an optional `limit` query parameter to the existing `/items` endpoint.",
                "task-route-target",
                root,
                allowed_paths=("src/", "tests/"),
            )

        self.assertIsInstance(result, Plan)
        self.assertEqual(
            result.plan.coder_packet.target_file.path,
            "src/backend.py",
        )

    def test_suffix_style_test_file_is_not_a_deterministic_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "backend.py").write_text(
                "def list_items():\n    return [1, 2]\n",
                encoding="utf-8",
            )
            (root / "src" / "handler_test.py").write_text(
                "ROUTE = '/items'\n",
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "Add an optional `limit` query parameter to the existing `/items` endpoint.",
                "task-test-suffix-excluded",
                root,
                allowed_paths=("src/",),
            )

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "no_explicit_target")

    def test_root_test_module_is_not_a_deterministic_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "test.py").write_text(
                "ROUTE = '/items'\n",
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "Fix the `/items` endpoint.",
                "task-root-test-module",
                root,
                allowed_paths=("test.py",),
            )

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "no_explicit_target")

    def test_conflicting_route_and_identifier_targets_fall_through(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "backend.py").write_text(
                "ROUTE = '/items'\n\ndef list_items():\n    return [1, 2]\n",
                encoding="utf-8",
            )
            (root / "src" / "utils.py").write_text(
                "def limit(value):\n    return value\n",
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "Add an optional `limit` query parameter to the existing `/items` endpoint.",
                "task-route-precedence",
                root,
                allowed_paths=("src/",),
            )

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "no_explicit_target")

    def test_route_prefix_does_not_count_as_exact_route_literal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "wrong.py").write_text(
                "ROUTE = '/items-old'\n",
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "Fix the `/items` endpoint without changing other routes.",
                "task-route-prefix",
                root,
                allowed_paths=("src/",),
            )

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "no_explicit_target")

    def test_comments_and_docstrings_do_not_count_as_target_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "notes.py").write_text(
                "'''/items'''\n"
                "# ROUTE = '/items'\n"
                "# def normalize(value): old API\n",
                encoding="utf-8",
            )

            route = plan_task_deterministically(
                "Fix the `/items` endpoint.",
                "task-comment-route",
                root,
                allowed_paths=("src/",),
            )
            symbol = plan_task_deterministically(
                "Fix the `normalize` helper.",
                "task-comment-symbol",
                root,
                allowed_paths=("src/",),
            )

        self.assertIsInstance(route, FallthroughToLLM)
        self.assertIsInstance(symbol, FallthroughToLLM)

    def test_non_python_comments_do_not_count_as_target_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "notes.js").write_text(
                "/*\nfunction normalize(value) {}\n*/\n"
                "const live = true; // '/items'\n",
                encoding="utf-8",
            )

            route = plan_task_deterministically(
                "Fix the `/items` endpoint.",
                "task-js-comment-route",
                root,
                allowed_paths=("src/",),
            )
            symbol = plan_task_deterministically(
                "Fix the `normalize` helper.",
                "task-js-comment-symbol",
                root,
                allowed_paths=("src/",),
            )

        self.assertIsInstance(route, FallthroughToLLM)
        self.assertIsInstance(symbol, FallthroughToLLM)

    def test_non_python_template_text_does_not_count_as_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "docs.js").write_text(
                "const docs = `\nfunction normalize(value) {}\n`;\n",
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "Fix the `normalize` helper.",
                "task-js-template-declaration",
                root,
                allowed_paths=("src/",),
            )

        self.assertIsInstance(result, FallthroughToLLM)

    def test_new_function_resolves_source_from_existing_domain_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "__init__.py").write_text("", encoding="utf-8")
            (root / "src" / "service.py").write_text(
                "ORDERS = [{'status': 'ready'}]\n\ndef get_order(order_id):\n    return None\n",
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "Add `count_ready_orders` for orders whose `status` exactly matches ready.",
                "task-sole-source",
                root,
                allowed_paths=("src/",),
            )

        self.assertIsInstance(result, Plan)
        self.assertEqual(
            result.plan.coder_packet.target_file.path,
            "src/service.py",
        )

    def test_secondary_declaration_does_not_override_stronger_domain_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "service.py").write_text(
                "ORDERS = [{'status': 'ready'}]\n",
                encoding="utf-8",
            )
            (root / "src" / "utils.py").write_text(
                "def status(value):\n    return value\n",
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "Add `count_ready_orders` for orders whose `status` is `ready`.",
                "task-secondary-domain-evidence",
                root,
                allowed_paths=("src/",),
            )

        self.assertIsInstance(result, Plan)
        self.assertEqual(
            result.plan.coder_packet.target_file.path,
            "src/service.py",
        )

    def test_ambiguous_named_symbol_still_falls_through_to_llm(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            for name in ("one.py", "two.py"):
                (root / "src" / name).write_text(
                    "def normalize(value):\n    return value\n",
                    encoding="utf-8",
                )

            result = plan_task_deterministically(
                "Fix `normalize` while preserving behavior.",
                "task-ambiguous-symbol",
                root,
                allowed_paths=("src/",),
            )

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "no_explicit_target")

    def test_read_only_symbol_is_not_selected_as_edit_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "support").mkdir()
            (root / "src" / "service.py").write_text(
                "def handle(value):\n    return value\n",
                encoding="utf-8",
            )
            (root / "support" / "helpers.py").write_text(
                "def normalize(value):\n    return value.strip()\n",
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "Fix `normalize` while preserving its signature.",
                "task-read-only-symbol",
                root,
                allowed_paths=("src/",),
                readable_paths=("src/", "support/"),
            )

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "no_explicit_target")

    def test_inferred_read_only_path_does_not_preempt_writable_planning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / "src" / "service.py").write_text(
                "def handle(value):\n    return value\n",
                encoding="utf-8",
            )
            (root / "tests" / "test_service.py").write_text(
                "from src.service import handle\n",
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "Make behavior asserted by tests/test_service.py pass by updating src/service.py.",
                "task-inferred-read-only-path",
                root,
                allowed_paths=("src/",),
                readable_paths=("src/", "tests/"),
            )

        self.assertIsInstance(result, Plan)
        self.assertEqual(
            result.plan.coder_packet.target_file.path,
            "src/service.py",
        )

    def test_multiple_inferred_writable_paths_require_architect_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "schema.py").write_text(
                "SCHEMA = {}\n",
                encoding="utf-8",
            )
            (root / "src" / "service.py").write_text(
                "def handle(value):\n    return value\n",
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "Use src/schema.py only as reference; see src/schema.py for shape; "
                "update src/service.py to fix `handle`.",
                "task-multiple-writable-paths",
                root,
                allowed_paths=("src/",),
            )
            unscoped = plan_task_deterministically(
                "Use src/schema.py only as reference; update src/service.py to fix `handle`.",
                "task-multiple-unscoped-paths",
                root,
            )

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "multiple_inferred_writable_targets")
        self.assertIsInstance(unscoped, FallthroughToLLM)
        self.assertEqual(unscoped.reason, "multiple_inferred_writable_targets")

    def test_read_only_path_without_writable_path_does_not_redirect_by_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "tests").mkdir()
            (root / "src" / "service.py").write_text(
                "def foo(value):\n    return value\n",
                encoding="utf-8",
            )
            (root / "tests" / "helper.py").write_text(
                "def helper(value):\n    return value\n",
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "Fix `foo` in tests/helper.py.",
                "task-read-only-path-symbol",
                root,
                allowed_paths=("src/",),
                readable_paths=("src/", "tests/"),
            )

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(
            result.reason,
            "inferred_target_outside_writable_scope",
        )

    def test_read_only_import_is_available_as_context_for_writable_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app" / "support").mkdir(parents=True)
            (root / "app" / "service.py").write_text(
                "from .support.helpers import normalize\n\n"
                "def handle(value):\n    return normalize(value)\n",
                encoding="utf-8",
            )
            (root / "app" / "support" / "helpers.py").write_text(
                "def normalize(value):\n    return value.strip()\n",
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "Fix `handle` in app/service.py without changing its signature.",
                "task-readable-import-context",
                root,
                allowed_paths=("app/service.py",),
                readable_paths=("app/",),
            )

        self.assertIsInstance(result, Plan)
        self.assertEqual(
            [item.path for item in result.plan.coder_packet.context_slices],
            ["app/service.py", "app/support/helpers.py"],
        )

    def test_oversized_source_scan_falls_through_without_claiming_uniqueness(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            for index in range(401):
                body = (
                    "def normalize(value):\n    return value\n"
                    if index == 0
                    else f"VALUE_{index} = {index}\n"
                )
                (root / "src" / f"module_{index:03d}.py").write_text(
                    body,
                    encoding="utf-8",
                )

            result = plan_task_deterministically(
                "Fix `normalize` while preserving its signature.",
                "task-bounded-source-scan",
                root,
                allowed_paths=("src/",),
            )

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "no_explicit_target")

    def test_oversized_source_file_prevents_false_unique_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / "src" / "small.py").write_text(
                "def normalize(value):\n    return value\n",
                encoding="utf-8",
            )
            (root / "src" / "large.py").write_text(
                "# `normalize` may also be implemented here\n"
                + ("x" * 256_001),
                encoding="utf-8",
            )

            result = plan_task_deterministically(
                "Fix `normalize` while preserving its signature.",
                "task-oversized-source-scan",
                root,
                allowed_paths=("src/",),
            )

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "no_explicit_target")

    def test_creation_task_falls_through_before_target_resolution(self) -> None:
        result = plan_task_deterministically(
            "Create a new page at src/app/billing/page.tsx that shows current usage",
            "task-create",
            Path.cwd(),
        )

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "creation_task")

    def test_missing_target_falls_through(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = plan_task_deterministically(
                "Target file: src/components/DoesNotExist.tsx\nFix the rendering",
                "task-missing",
                Path(tmp),
            )

        self.assertIsInstance(result, FallthroughToLLM)
        self.assertEqual(result.reason, "target_missing")

    def test_agent_internal_target_uses_agent_forbidden_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "source_proxy/decision/router.py"
            target.parent.mkdir(parents=True)
            target.write_text("def decide():\n    return 'ok'\n", encoding="utf-8")

            result = plan_task_deterministically(
                "Target file: source_proxy/decision/router.py\nFix empty task classification",
                "task-agent",
                root,
            )

            self.assertIsInstance(result, Plan)
            self.assertIn("src/app/", result.plan.coder_packet.forbidden_paths)
            self.assertNotIn("source_proxy/", result.plan.coder_packet.forbidden_paths)
            self.assertEqual(
                result.plan.verification_plan.required_checks[-1].id,
                "python_compile",
            )

    def test_llm_architect_builds_valid_plan_for_vague_existing_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "src/components/dashboard/DashboardInternalSidebar.tsx"
            target.parent.mkdir(parents=True)
            target.write_text(
                "export function DashboardInternalSidebar() { return <aside />; }\n",
                encoding="utf-8",
            )
            seen_prompts: list[str] = []

            def fake_llm(prompt: str, alias: str) -> str:
                seen_prompts.append(prompt)
                self.assertEqual(alias, "local")
                return json.dumps(
                    {
                        "classification": {
                            "task_class": "style",
                            "visual_change": True,
                            "designer_required": False,
                            "estimated_complexity": "small",
                        },
                        "coder_packet": {
                            "target_file": {
                                "path": "src/components/dashboard/DashboardInternalSidebar.tsx",
                                "exists": True,
                                "sha256_before": None,
                            },
                            "operation": "edit",
                            "acceptance_criteria": [
                                {
                                    "id": "visual-polish",
                                    "description": "Dashboard sidebar looks more polished.",
                                    "kind": "behavioral",
                                }
                            ],
                            "constraints": {
                                "must_contain": [],
                                "must_not_contain": ["Target file:"],
                                "preserve_imports": [],
                                "preserve_exports": ["DashboardInternalSidebar"],
                                "max_added_lines": 120,
                                "max_removed_lines": 80,
                            },
                            "context_slices": [],
                            "forbidden_paths": [],
                            "style_directives": ["Use existing dashboard styling patterns."],
                        },
                    }
                )

            plan = plan_task_with_llm(
                "Make the dashboard prettier",
                "task-llm",
                root,
                llm_call=fake_llm,
            )

            self.assertIn("DashboardInternalSidebar.tsx", seen_prompts[0])
            self.assertEqual(plan.classification.task_class, "style")
            self.assertEqual(
                plan.coder_packet.target_file.path,
                "src/components/dashboard/DashboardInternalSidebar.tsx",
            )
            self.assertEqual(plan.coder_packet.operation, "edit")
            self.assertEqual(
                [slice.path for slice in plan.coder_packet.context_slices],
                ["src/components/dashboard/DashboardInternalSidebar.tsx"],
            )
            self.assertIn("source_proxy/", plan.coder_packet.forbidden_paths)

    def test_llm_architect_discards_unsupported_exact_constraints_but_preserves_grounded_requirements(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "src/status.ts"
            dependency = root / "src/format.js"
            target.parent.mkdir(parents=True)
            target.write_text(
                'import { format } from "./format.js";\n'
                "export function status() { return format('ready'); }\n",
                encoding="utf-8",
            )
            dependency.write_text(
                "export function format(value) { return value; }\n",
                encoding="utf-8",
            )
            task = "\n".join(
                [
                    "Target file: src/status.ts",
                    'Display the exact filename "worker.py".',
                    'Read settings from "config/runtime.yaml".',
                    'Do not include "debug-only".',
                ]
            )

            def fake_llm(_prompt: str, _alias: str) -> str:
                return json.dumps(
                    {
                        "classification": {
                            "task_class": "fix",
                            "visual_change": False,
                            "designer_required": False,
                            "estimated_complexity": "small",
                        },
                        "coder_packet": {
                            "target_file": {
                                "path": "src/status.ts",
                                "exists": True,
                            },
                            "operation": "edit",
                            "acceptance_criteria": [
                                {
                                    "id": "invented-literal",
                                    "description": 'Output must contain "MODEL_ONLY".',
                                    "kind": "literal",
                                },
                                {
                                    "id": "grounded-behavior",
                                    "description": (
                                        "Make status asynchronous and emit remote telemetry."
                                    ),
                                    "kind": "behavioral",
                                },
                            ],
                            "constraints": {
                                "must_contain": ["MODEL_ONLY"],
                                "must_not_contain": ["format"],
                                "preserve_imports": ["invented-import"],
                                "preserve_exports": ["inventedExport"],
                                "max_added_lines": 1,
                                "max_removed_lines": 2,
                            },
                            "context_slices": [],
                            "forbidden_paths": [],
                            "style_directives": [
                                "Silently rewrite every neighboring module."
                            ],
                        },
                    }
                )

            plan = plan_task_with_llm(
                task,
                "task-grounded-constraints",
                root,
                llm_call=fake_llm,
                allowed_paths=("src/",),
            )

        constraints = plan.coder_packet.constraints
        self.assertEqual(plan.source_task, task)
        self.assertEqual(plan.coder_packet.target_file.path, "src/status.ts")
        self.assertEqual(constraints.must_contain, ["worker.py"])
        self.assertEqual(
            constraints.must_not_contain,
            ["Target file:", "debug-only"],
        )
        self.assertEqual(constraints.preserve_imports, ["./format.js"])
        self.assertEqual(constraints.preserve_exports, ["status"])
        self.assertEqual(constraints.max_added_lines, 80)
        self.assertEqual(constraints.max_removed_lines, 60)
        self.assertNotIn("MODEL_ONLY", constraints.must_contain)
        self.assertNotIn("invented-import", constraints.preserve_imports)
        self.assertNotIn("inventedExport", constraints.preserve_exports)
        self.assertEqual(
            [item.path for item in plan.coder_packet.context_slices],
            ["src/status.ts", "src/format.js"],
        )
        criteria = {item.id: item for item in plan.coder_packet.acceptance_criteria}
        self.assertNotIn("invented-literal", criteria)
        self.assertEqual(criteria["literal-1"].kind, "literal")
        self.assertIn("worker.py", criteria["literal-1"].description)
        self.assertNotIn("grounded-behavior", criteria)
        self.assertEqual(set(criteria), {"target-file", "literal-1"})
        self.assertNotIn(
            "Silently rewrite every neighboring module.",
            plan.coder_packet.style_directives,
        )
        self.assertEqual(
            task_spec_from_plan(plan).literal_requirements,
            ["worker.py"],
        )

    def test_llm_architect_scopes_file_index_and_context_to_server_allowed_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            allowed_files = {
                "src/service.py": "VALUE = 1\n",
                "src/worker.go": "package worker\n",
                "src/State.java": "class State {}\n",
                "src/lib.rs": "pub const VALUE: i32 = 1;\n",
                "src/query.sql": "SELECT 1;\n",
            }
            for relative, content in allowed_files.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            private = root / "private/answer.py"
            private.parent.mkdir()
            private.write_text("HIDDEN = True\n", encoding="utf-8")
            seen_prompts: list[str] = []

            def fake_llm(prompt: str, _alias: str) -> str:
                seen_prompts.append(prompt)
                return json.dumps(
                    {
                        "classification": {
                            "task_class": "fix",
                            "visual_change": False,
                            "designer_required": False,
                            "estimated_complexity": "small",
                        },
                        "coder_packet": {
                            "target_file": {"path": "src/service.py", "exists": True},
                            "operation": "edit",
                            "acceptance_criteria": [],
                            "constraints": {},
                            "context_slices": [],
                            "forbidden_paths": [],
                            "style_directives": [],
                        },
                    }
                )

            plan = plan_task_with_llm(
                "Fix the backend service",
                "task-scoped-index",
                root,
                llm_call=fake_llm,
                allowed_paths=("src/",),
            )

            for relative in allowed_files:
                self.assertIn(relative, seen_prompts[0])
            self.assertNotIn("private/answer.py", seen_prompts[0])
            self.assertEqual(
                [item.path for item in plan.coder_packet.context_slices],
                ["src/service.py"],
            )

    def test_llm_architect_rejects_target_outside_server_allowed_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "private/answer.py"
            target.parent.mkdir(parents=True)
            target.write_text("HIDDEN = True\n", encoding="utf-8")

            def fake_llm(_prompt: str, _alias: str) -> str:
                return json.dumps(
                    {
                        "classification": {},
                        "coder_packet": {
                            "target_file": {"path": "private/answer.py", "exists": True},
                            "operation": "edit",
                            "acceptance_criteria": [],
                            "constraints": {},
                            "context_slices": [],
                            "forbidden_paths": [],
                            "style_directives": [],
                        },
                    }
                )

            with self.assertRaises(ArchitectLLMError) as raised:
                plan_task_with_llm(
                    "Fix the backend service",
                    "task-out-of-scope",
                    root,
                    llm_call=fake_llm,
                    allowed_paths=("src/",),
                )

        self.assertEqual(
            raised.exception.reason_code,
            "architect_target_outside_allowed_scope",
        )

    def test_llm_architect_retries_after_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "src/app/page.tsx"
            target.parent.mkdir(parents=True)
            target.write_text("export default function Page() { return null; }\n", encoding="utf-8")
            calls = 0

            def fake_llm(_prompt: str, _alias: str) -> str:
                nonlocal calls
                calls += 1
                if calls == 1:
                    return "not json"
                return json.dumps(
                    {
                        "classification": {
                            "task_class": "style",
                            "visual_change": True,
                            "designer_required": False,
                            "estimated_complexity": "small",
                        },
                        "coder_packet": {
                            "target_file": {
                                "path": "src/app/page.tsx",
                                "exists": True,
                                "sha256_before": None,
                            },
                            "operation": "edit",
                            "acceptance_criteria": [],
                            "constraints": {
                                "must_contain": [],
                                "must_not_contain": [],
                                "preserve_imports": [],
                                "preserve_exports": [],
                                "max_added_lines": 80,
                                "max_removed_lines": 60,
                            },
                            "context_slices": [],
                            "forbidden_paths": [],
                            "style_directives": [],
                        },
                    }
                )

            plan = plan_task_with_llm("Make the homepage cleaner", "task-retry", root, llm_call=fake_llm)

            self.assertEqual(calls, 2)
            self.assertEqual(plan.coder_packet.target_file.path, "src/app/page.tsx")

    def test_llm_architect_selects_strict_json_root_without_extra_model_call(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "src/service.py"
            target.parent.mkdir(parents=True)
            target.write_text("def service():\n    return 'ready'\n", encoding="utf-8")
            calls = 0

            def fake_llm(_prompt: str, _alias: str) -> str:
                nonlocal calls
                calls += 1
                payload = json.dumps(_valid_llm_plan_payload("src/service.py"))
                return f"Here's a discarded non-plan object: {{}}\n```json\n{payload}\n```"

            plan = plan_task_with_llm(
                "Fix the backend service",
                "task-json-root-selection",
                root,
                llm_call=fake_llm,
            )

        self.assertEqual(calls, 1)
        self.assertEqual(plan.coder_packet.target_file.path, "src/service.py")

    def test_llm_architect_deduplicates_identical_viable_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "src/service.py"
            target.parent.mkdir(parents=True)
            target.write_text("def service():\n    return 'ready'\n", encoding="utf-8")
            calls = 0
            payload_object = _valid_llm_plan_payload("src/service.py")
            first = json.dumps(payload_object)
            second = json.dumps(payload_object, separators=(",", ":"), sort_keys=True)

            def fake_llm(_prompt: str, _alias: str) -> str:
                nonlocal calls
                calls += 1
                return f"{first}\n{second}"

            plan = plan_task_with_llm(
                "Fix the backend service",
                "task-json-deduplication",
                root,
                llm_call=fake_llm,
            )

        self.assertEqual(calls, 1)
        self.assertEqual(plan.coder_packet.target_file.path, "src/service.py")

    def test_llm_architect_rejects_distinct_viable_roots_as_ambiguous(
        self,
    ) -> None:
        first = json.dumps(_valid_llm_plan_payload("src/service.py"))
        second = json.dumps(_valid_llm_plan_payload("src/worker.py"))
        calls = 0

        def fake_llm(_prompt: str, _alias: str) -> str:
            nonlocal calls
            calls += 1
            return f"{first}\n{second}"

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in ("src/service.py", "src/worker.py"):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("VALUE = 1\n", encoding="utf-8")
            with self.assertRaises(ArchitectLLMError) as raised:
                plan_task_with_llm(
                    "Fix the backend service",
                    "task-json-ambiguity",
                    root,
                    llm_call=fake_llm,
                )

        self.assertEqual(calls, 2)
        self.assertEqual(
            raised.exception.reason_code,
            "architect_llm_ambiguous_json",
        )
        self.assertEqual(
            str(raised.exception),
            "LLM Architect response did not validate after retry.",
        )

    def test_llm_architect_strict_root_rejects_non_json_and_nonfinite_values(
        self,
    ) -> None:
        payload = _valid_llm_plan_payload("src/service.py")
        nonfinite_payload = _valid_llm_plan_payload("src/service.py")
        classification = nonfinite_payload["classification"]
        assert isinstance(classification, dict)
        classification["confidence"] = float("nan")
        malformed_responses = {
            "python_literal": str(payload),
            "trailing_comma": f"{json.dumps(payload)[:-1]},}}",
            "nonfinite_constant": json.dumps(nonfinite_payload),
        }

        for response_kind, response in malformed_responses.items():
            with self.subTest(response_kind=response_kind):
                with self.assertRaises(ArchitectLLMError) as raised:
                    architect_module._parse_json_object(response)
                self.assertEqual(
                    raised.exception.reason_code,
                    "architect_llm_invalid_json",
                )

    def test_llm_architect_blocked_root_requires_allowlisted_reason_code(self) -> None:
        valid = architect_module._parse_json_object(
            '{"status":"blocked","reason_code":"task_too_vague_for_plan"}'
        )
        self.assertEqual(valid["status"], "blocked")

        for response in (
            '{"status":"blocked"}',
            '{"status":"blocked","reason_code":""}',
            '{"status":"blocked","reason_code":7}',
            '{"status":"blocked","reason_code":"model_authored_reason"}',
        ):
            with self.subTest(response=response):
                with self.assertRaises(ArchitectLLMError) as raised:
                    architect_module._parse_json_object(response)
                self.assertEqual(
                    raised.exception.reason_code,
                    "architect_llm_invalid_json",
                )

    def test_llm_architect_rejects_duplicate_keys_and_overflow_numbers(
        self,
    ) -> None:
        responses = {
            "duplicate_nested_key": (
                '{"classification":{},'
                '"coder_packet":{"target_file":{"path":"src/one.py",'
                '"path":"src/two.py"}}}'
            ),
            "positive_overflow": (
                '{"classification":{"confidence":1e9999},'
                '"coder_packet":{"target_file":{}}}'
            ),
            "negative_overflow": (
                '{"classification":{"confidence":-1e9999},'
                '"coder_packet":{"target_file":{}}}'
            ),
        }
        for response_kind, response in responses.items():
            with self.subTest(response_kind=response_kind):
                with self.assertRaises(ArchitectLLMError) as raised:
                    architect_module._parse_json_object(response)
                self.assertEqual(
                    raised.exception.reason_code,
                    "architect_llm_invalid_json",
                )

    def test_llm_architect_does_not_replay_model_authored_block_reason(
        self,
    ) -> None:
        marker = "RAW_MODEL_MARKER_DO_NOT_REPLAY"
        prompts: list[str] = []

        def fake_llm(prompt: str, _alias: str) -> str:
            prompts.append(prompt)
            return json.dumps(
                {
                    "status": "blocked",
                    "reason_code": marker,
                    "reason": marker,
                }
            )

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ArchitectLLMError) as raised:
                plan_task_with_llm(
                    "Fix the backend service",
                    "task-no-raw-replay",
                    Path(tmp),
                    llm_call=fake_llm,
                )

        self.assertEqual(len(prompts), 2)
        self.assertNotIn(marker, prompts[1])
        self.assertNotIn(marker, str(raised.exception))
        self.assertNotIn(marker, raised.exception.reason_code)
        self.assertEqual(
            raised.exception.reason_code,
            "architect_llm_invalid_json",
        )

    def test_llm_architect_rejects_truncated_structure_without_synthesis(
        self,
    ) -> None:
        calls = 0
        truncated = json.dumps(_valid_llm_plan_payload("src/service.py"))[:-2]

        def fake_llm(_prompt: str, _alias: str) -> str:
            nonlocal calls
            calls += 1
            return truncated

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ArchitectLLMError) as raised:
                plan_task_with_llm(
                    "Fix the backend service",
                    "task-json-truncated",
                    Path(tmp),
                    llm_call=fake_llm,
                )

        self.assertEqual(calls, 2)
        self.assertEqual(
            raised.exception.reason_code,
            "architect_llm_invalid_json",
        )

    def test_llm_architect_keeps_two_call_bound_for_irreparable_response(
        self,
    ) -> None:
        calls = 0

        def fake_llm(_prompt: str, _alias: str) -> str:
            nonlocal calls
            calls += 1
            return '{"classification":}'

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ArchitectLLMError) as raised:
                plan_task_with_llm(
                    "Fix the backend service",
                    "task-json-hard-failure",
                    Path(tmp),
                    llm_call=fake_llm,
                )

        self.assertEqual(calls, 2)
        self.assertEqual(
            raised.exception.reason_code,
            "architect_llm_invalid_json",
        )

    def test_llm_architect_distinguishes_malformed_json_from_router_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            with self.assertRaises(ArchitectLLMError) as malformed:
                plan_task_with_llm(
                    "Fix the backend service",
                    "task-malformed-json",
                    root,
                    llm_call=lambda _prompt, _alias: '{"classification":}',
                )

            def unavailable(_prompt: str, _alias: str) -> str:
                raise ConnectionError("router unavailable")

            with self.assertRaises(ArchitectLLMError) as routed:
                plan_task_with_llm(
                    "Fix the backend service",
                    "task-router-unavailable",
                    root,
                    llm_call=unavailable,
                )

        self.assertEqual(
            malformed.exception.reason_code,
            "architect_llm_invalid_json",
        )
        self.assertEqual(
            routed.exception.reason_code,
            "architect_llm_router_error",
        )

    def test_llm_architect_prompt_includes_rejection_feedback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "src/app/page.tsx"
            target.parent.mkdir(parents=True)
            target.write_text("export default function Page() { return null; }\n", encoding="utf-8")
            seen_prompts: list[str] = []

            def fake_llm(prompt: str, _alias: str) -> str:
                seen_prompts.append(prompt)
                return json.dumps(
                    {
                        "classification": {
                            "task_class": "style",
                            "visual_change": True,
                            "designer_required": False,
                            "estimated_complexity": "small",
                        },
                        "coder_packet": {
                            "target_file": {
                                "path": "src/app/page.tsx",
                                "exists": True,
                                "sha256_before": None,
                            },
                            "operation": "edit",
                            "acceptance_criteria": [],
                            "constraints": {
                                "must_contain": [],
                                "must_not_contain": [],
                                "preserve_imports": [],
                                "preserve_exports": [],
                                "max_added_lines": 80,
                                "max_removed_lines": 60,
                            },
                            "context_slices": [],
                            "forbidden_paths": [],
                            "style_directives": [],
                        },
                    }
                )

            plan_task_with_llm(
                "Make the homepage cleaner",
                "task-rejected",
                root,
                llm_call=fake_llm,
                rejection_feedback=[
                    {
                        "plan_id": "plan-one",
                        "target": "src/components/Old.tsx",
                        "reason_code": "wrong_target",
                        "details": "Use the App Router page instead.",
                    }
                ],
            )

            self.assertIn("Previous attempts and why they were rejected", seen_prompts[0])
            self.assertIn("wrong_target", seen_prompts[0])
            self.assertIn("src/components/Old.tsx", seen_prompts[0])

    def test_llm_architect_rejects_missing_edit_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            def fake_llm(_prompt: str, _alias: str) -> str:
                return json.dumps(
                    {
                        "classification": {
                            "task_class": "fix",
                            "visual_change": False,
                            "designer_required": False,
                            "estimated_complexity": "small",
                        },
                        "coder_packet": {
                            "target_file": {
                                "path": "src/components/Missing.tsx",
                                "exists": True,
                                "sha256_before": None,
                            },
                            "operation": "edit",
                            "acceptance_criteria": [],
                            "constraints": {
                                "must_contain": [],
                                "must_not_contain": [],
                                "preserve_imports": [],
                                "preserve_exports": [],
                                "max_added_lines": 80,
                                "max_removed_lines": 60,
                            },
                            "context_slices": [],
                            "forbidden_paths": [],
                            "style_directives": [],
                        },
                    }
                )

            with self.assertRaises(ArchitectLLMError) as raised:
                plan_task_with_llm("Fix the missing thing", "task-missing-llm", Path(tmp), llm_call=fake_llm)

        self.assertEqual(raised.exception.reason_code, "architect_target_missing")

    def test_llm_architect_timeout_has_specific_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            def fake_llm(_prompt: str, _alias: str) -> str:
                raise TimeoutError("request timed out")

            with self.assertRaises(ArchitectLLMError) as raised:
                plan_task_with_llm(
                    "Make the dashboard easier to scan",
                    "task-timeout",
                    root,
                    llm_call=fake_llm,
                )

        self.assertEqual(raised.exception.reason_code, "architect_llm_timeout")
        self.assertIn("timed out", str(raised.exception))

    def test_llm_architect_surfaces_gate_denial_without_retrying_as_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with (
                patch("source_proxy.planning.architect.available_model_aliases", return_value={"local"}),
                patch(
                    "source_proxy.planning.architect._call_architect_llm",
                    side_effect=ExternalGateError("Gate state is missing.", "gate_missing"),
                ) as call,
            ):
                with self.assertRaises(ArchitectLLMError) as raised:
                    plan_task_with_llm(
                        "Create a small widget",
                        "task-gate-denied",
                        Path(tmp),
                    )

        self.assertEqual(raised.exception.reason_code, "architect_gate_missing")
        self.assertEqual(str(raised.exception), "Gate state is missing.")
        call.assert_called_once()

    def test_llm_architect_default_timeout_is_twenty_seconds(self) -> None:
        from source_proxy.planning import architect

        self.assertEqual(architect._architect_timeout_seconds(), 20.0)


if __name__ == "__main__":
    unittest.main()
