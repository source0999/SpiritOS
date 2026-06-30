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

    def test_lumacart_prompt_3_render_task_is_not_subjective_visual_polish(self) -> None:
        self.assertFalse(
            task_requests_subjective_improvement(
                "coder-003-render-product-cards\n"
                "make the dummy LumaCart page actually show the products as cards.\n"
                "Target file: tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js\n"
                "Implementation notes: src/products.js is the source of truth. Render cards dynamically in src/main.js."
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

    def test_validate_replacement_content_passes_when_exact_text_is_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = validate_replacement_content(
                workspace_root=root,
                target_path="docs/demo.md",
                content="hello\nBuilt with SpiritOS\n",
                task_text='Target file: docs/demo.md\nAdd exact text "Built with SpiritOS"',
            )

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["missing"], [])
        self.assertTrue(result["typescript_check"]["skipped"])

    def test_validate_replacement_content_ignores_trailing_slash_on_file_targets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_replacement_content(
                workspace_root=Path(tmp),
                target_path="docs/phase-8-manual-check.md/",
                content="append smoke\n",
                task_text=(
                    "Append a line.\n\nTarget file: docs/phase-8-manual-check.md"
                ),
            )

        self.assertTrue(result["ok"], result)

    def test_validate_replacement_content_does_not_treat_natural_language_as_class_fragments(self) -> None:
        task = (
            "make a new isolated test area at `/agent-lab`. if it doesnt exist create the route "
            "and page files needed. the page should say Agent Lab, explain this is for local coder "
            "benchmark tests, and have empty sections for basic apps, tools, diagnostics, and tests. "
            "dont touch real SpiritOS pages. verify `/agent-lab` loads."
        )
        content = (
            "export default function Page() {\n"
            "  return <main><h1>Agent Lab</h1><p>local coder benchmark tests</p><p>/agent-lab</p></main>;\n"
            "}\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_replacement_content(
                workspace_root=Path(tmp),
                target_path="src/app/agent-lab/page.tsx",
                content=content,
                task_text=task,
            )

        self.assertTrue(result["ok"], result)


if __name__ == "__main__":
    unittest.main()
