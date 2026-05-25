from __future__ import annotations

from dataclasses import replace
import inspect
import unittest

from source_proxy.cartographer import level_11_runtime_baseline
from source_proxy.cartographer.level_11_runtime_baseline import (
    build_level_11_runtime_baseline,
    level_11_runtime_baseline_is_safe_to_proceed,
)


class CartographerLevel11RuntimeBaselineTests(unittest.TestCase):
    def test_baseline_reports_locked_level_11_1_authority(self) -> None:
        baseline = build_level_11_runtime_baseline()

        self.assertEqual(baseline.level, "11.1")
        self.assertEqual(baseline.status, "locked-baseline")
        self.assertEqual(baseline.authority_state, "locked")
        self.assertIn("observe", baseline.allowed_current_modes)
        self.assertIn("recommend", baseline.allowed_current_modes)
        self.assertIn("preview", baseline.allowed_current_modes)
        self.assertIn("dry_run", baseline.allowed_current_modes)

    def test_forbidden_authority_keeps_current_runtime_non_autonomous(self) -> None:
        forbidden = set(build_level_11_runtime_baseline().forbidden_authority)

        self.assertIn("write_authority", forbidden)
        self.assertIn("local_execution_authority", forbidden)
        self.assertIn("autonomous_execution", forbidden)
        self.assertIn("automatic_execution", forbidden)
        self.assertIn("self_approval", forbidden)
        self.assertIn("proxy_ui_mutation", forbidden)
        self.assertIn("coding_ui_mutation", forbidden)
        self.assertIn("source_proxy_stress_mutation", forbidden)

    def test_protected_lanes_include_declared_parallel_work(self) -> None:
        protected = set(build_level_11_runtime_baseline().protected_lanes)

        self.assertIn("proxy_ui_makeover", protected)
        self.assertIn("coding_ui_implementation_wiring", protected)
        self.assertIn("source_proxy_stress_testing", protected)

    def test_safe_to_proceed_requires_locked_fail_closed_non_autonomous_state(self) -> None:
        baseline = build_level_11_runtime_baseline()

        self.assertTrue(level_11_runtime_baseline_is_safe_to_proceed(baseline))

        unsafe_variants = [
            replace(baseline, authority_state="unlocked"),
            self._without_forbidden(baseline, "automatic_execution"),
            self._without_forbidden(baseline, "self_approval"),
            self._without_forbidden(baseline, "write_authority"),
            self._without_forbidden(baseline, "local_execution_authority"),
            replace(baseline, protected_lanes=()),
            replace(
                baseline,
                required_user_controls=tuple(
                    control
                    for control in baseline.required_user_controls
                    if control != "fail-closed validation"
                ),
            ),
            replace(baseline, next_increment=""),
        ]

        for unsafe in unsafe_variants:
            with self.subTest(unsafe=unsafe):
                self.assertFalse(level_11_runtime_baseline_is_safe_to_proceed(unsafe))

    def test_module_exposes_no_execution_or_mutation_function_surface(self) -> None:
        public_functions = {
            name: value
            for name, value in vars(level_11_runtime_baseline).items()
            if inspect.isfunction(value) and not name.startswith("_")
        }
        self.assertEqual(
            set(public_functions),
            {
                "build_level_11_runtime_baseline",
                "level_11_runtime_baseline_is_safe_to_proceed",
            },
        )

        forbidden_function_name_fragments = (
            "write",
            "shell",
            "exec",
            "git",
            "network",
            "commit",
            "push",
            "merge",
            "cleanup",
            "stash",
            "checkout",
        )
        for function_name in public_functions:
            with self.subTest(function_name=function_name):
                self.assertFalse(
                    any(
                        fragment in function_name
                        for fragment in forbidden_function_name_fragments
                    )
                )

    def test_module_source_has_no_runtime_side_effect_imports_or_calls(self) -> None:
        source = inspect.getsource(level_11_runtime_baseline)

        forbidden_fragments = (
            "subprocess",
            "os.system",
            "os.popen",
            "Path(",
            "open(",
            ".write(",
            "write_text(",
            "requests",
            "urllib",
            "socket",
            "source_proxy.api",
            "source_proxy.codex",
            "source_proxy.testing.runner",
            "source_proxy.verification",
        )
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, source)

    @staticmethod
    def _without_forbidden(
        baseline: level_11_runtime_baseline.CartographerLevel11RuntimeBaseline,
        authority: str,
    ) -> level_11_runtime_baseline.CartographerLevel11RuntimeBaseline:
        return replace(
            baseline,
            forbidden_authority=tuple(
                item for item in baseline.forbidden_authority if item != authority
            ),
        )


if __name__ == "__main__":
    unittest.main()
