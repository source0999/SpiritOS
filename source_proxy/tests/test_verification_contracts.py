from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from source_proxy.verification.contracts import (
    _visual_diff_line_is_non_material,
    _visual_semantic_text,
    subjective_visual_diff_is_material,
    task_requests_subjective_improvement,
    validate_replacement_content,
)


class VerificationContractTests(unittest.TestCase):
    def test_subjective_improvement_detection_ignores_quoted_text(self) -> None:
        self.assertTrue(
            task_requests_subjective_improvement(
                "Make the dashboard prettier with tighter spacing"
            )
        )
        self.assertFalse(
            task_requests_subjective_improvement(
                'Change the label to "make the dashboard prettier"'
            )
        )

    def test_visual_diff_line_materiality_filter(self) -> None:
        self.assertTrue(_visual_diff_line_is_non_material("// refined spacing"))
        self.assertTrue(_visual_diff_line_is_non_material("export type Theme = string"))
        self.assertFalse(_visual_diff_line_is_non_material('<button className="gap-1">'))

    def test_visual_semantic_text_strips_whitespace_and_wrappers(self) -> None:
        self.assertEqual(
            _visual_semantic_text(["  return (", " <div /> ", ");"]),
            "return<div/>",
        )

    def test_subjective_visual_diff_requires_material_ui_change(self) -> None:
        shallow = "\n".join(
            [
                "diff --git a/src/Button.tsx b/src/Button.tsx",
                "--- a/src/Button.tsx",
                "+++ b/src/Button.tsx",
                "@@ -1 +1 @@",
                "-// old spacing",
                "+// refined spacing",
            ]
        )
        ok, reasons = subjective_visual_diff_is_material(
            shallow,
            '<button className="gap-2">Save</button>',
            "Make the button feel more premium",
        )
        self.assertFalse(ok)
        self.assertIn("non-visual", reasons[0])

        material = shallow.replace(
            "+// refined spacing",
            '+<button className="gap-1.5 transition-all hover:shadow-lg">Save</button>',
        )
        ok, reasons = subjective_visual_diff_is_material(
            material,
            '<button className="gap-1.5 transition-all hover:shadow-lg">Save</button>',
            "Make the button feel more premium",
        )
        self.assertTrue(ok)
        self.assertEqual(reasons, [])

    def test_validate_replacement_content_checks_contract_requirements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = validate_replacement_content(
                workspace_root=root,
                target_path="docs/demo.md",
                content="hello\n",
                task_text='Target file: docs/demo.md\nAdd exact text "Built with SpiritOS"',
            )

        self.assertFalse(result["ok"])
        self.assertIn("missing exact text: Built with SpiritOS", result["missing"])
        self.assertTrue(result["typescript_check"]["skipped"])


if __name__ == "__main__":
    unittest.main()
