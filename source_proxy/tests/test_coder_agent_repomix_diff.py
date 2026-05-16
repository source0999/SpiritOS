from __future__ import annotations

import json
import hashlib
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from source_proxy.planning.architect import Plan, plan_task_deterministically
from source_proxy.planning.plan import (
    AcceptanceCriterion,
    ArchitectPlan,
    BundleSnapshot,
    CoderPacket,
    ContentConstraints,
    ContextSlice,
    PlanBudget,
    TargetFile,
    TaskClassification,
    VerificationPlan,
)
from source_proxy.tasks.long_running import (
    CODER_SYSTEM_PROMPT,
    derive_context_mode,
    forbidden_paths_for_context_mode,
    generate_unified_diff_from_content,
    propose_coder_agent_diff_payload_from_plan,
    propose_coder_agent_implementation_diff as _coder_response_from_packet,
)


def _write_repomix(root: Path, rel: str, content: str = "x") -> None:
    (root / "repomix-output.xml").write_text(
        f'<repomix><files><file path="{rel}">{content}</file></files></repomix>',
        encoding="utf-8",
    )


def _json_response(rel: str, content: str) -> str:
    return json.dumps(
        {"action": "replace_file", "target": rel, "content": content, "notes": "ok"}
    )


def _json_lines_response(rel: str, content: str) -> str:
    return json.dumps(
        {
            "action": "replace_file",
            "target": rel,
            "content_lines": content.rstrip("\n").split("\n"),
            "notes": "ok",
        }
    )


def _packet(rel: str, content: str, *, exists: bool = True) -> CoderPacket:
    context_mode = derive_context_mode(rel)
    return CoderPacket(
        target_file=TargetFile(rel, exists, None),
        operation="edit" if exists else "create",
        acceptance_criteria=[
            AcceptanceCriterion("render-ok", "Render OK.", "literal"),
        ],
        constraints=ContentConstraints([], [], [], [], None, None),
        context_slices=[
            ContextSlice(
                rel,
                "target",
                hashlib.sha256(content.encode("utf-8")).hexdigest(),
                content,
                None,
            ),
        ],
        forbidden_paths=list(forbidden_paths_for_context_mode(context_mode)),
        style_directives=["Tailwind only"],
    )


def _architect_plan(task: str, packet: CoderPacket, root: Path) -> ArchitectPlan:
    bundle = root / "repomix-output.xml"
    bundle_sha = hashlib.sha256(bundle.read_bytes()).hexdigest() if bundle.is_file() else "0" * 64
    return ArchitectPlan(
        plan_id="packet-plan",
        task_id="task-packet",
        schema_version=1,
        created_at="2026-05-13T00:00:00Z",
        source_task=task,
        bundle_snapshot=BundleSnapshot(str(bundle), bundle_sha, str(root), "2026-05-13T00:00:00Z"),
        classification=TaskClassification("implement", False, False, "trivial"),
        coder_packet=packet,
        verification_plan=VerificationPlan([], False, False),
        budget=PlanBudget(3, 120, True),
    )


def _target_from_task(task: str) -> str:
    target = ""
    for line in task.splitlines():
        if line.lower().strip().startswith("target file:"):
            target = line.split(":", 1)[1].strip().strip("\"'`").replace("\\", "/").lstrip("./")
    if not target:
        bundle = getattr(_target_from_task, "workspace_root", None)
        if isinstance(bundle, Path):
            raw = bundle / "repomix-output.xml"
            if raw.is_file():
                paths = re.findall(r'<file\s+path="([^"]+)"', raw.read_text(encoding="utf-8", errors="replace"))
                app_paths = [path for path in paths if path.startswith("src/app/")]
                target = (app_paths or paths or [""])[0]
    return target


def propose_coder_agent_implementation_diff(
    *,
    task: str,
    workspace_root: Path,
    llm_call=None,
    model_alias: str | None = None,
    architect_plan: ArchitectPlan | None = None,
) -> dict:
    _target_from_task.workspace_root = workspace_root
    if architect_plan is None:
        rel = _target_from_task(task)
        content = ""
        target = workspace_root / rel
        if rel and target.is_file():
            content = target.read_text(encoding="utf-8", errors="replace")
        architect_plan = _architect_plan(task, _packet(rel, content, exists=target.is_file()), workspace_root)
    return propose_coder_agent_diff_payload_from_plan(
        architect_plan=architect_plan,
        workspace_root=workspace_root,
        llm_call=llm_call,
        model_alias=model_alias,
    )


class CoderAgentRepomixDiffTests(unittest.TestCase):
    def setUp(self) -> None:
        self._repomix = mock.patch("source_proxy.tasks.long_running._ensure_fresh_repomix")
        self._repomix.start()

    def tearDown(self) -> None:
        self._repomix.stop()

    def test_packet_entrypoint_returns_coder_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/mock/CodingAgentInterface.tsx"
            current = "export default function Page() { return null; }\n"
            packet = _packet(rel, current)
            replacement = 'export default function Page() { return <main>OK</main>; }\n'

            response = _coder_response_from_packet(
                packet,
                root,
                source_task=f"Target file: {rel}\nRender OK.",
                llm_call=lambda prompt, _model: (
                    self.assertIn("render-ok (literal): Render OK.", prompt)
                    or self.assertIn("[target slice: src/mock/CodingAgentInterface.tsx]", prompt)
                    or _json_response(rel, replacement)
                ),
            )

            self.assertEqual(response.status, "ok")
            self.assertEqual(response.target_path, rel)
            self.assertEqual(response.replacement_content, replacement)

    def test_architect_packet_context_drives_compatibility_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/mock/CodingAgentInterface.tsx"
            current = "export default function Page() { return null; }\n"
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text(current, encoding="utf-8")
            _write_repomix(root, rel, "stale repomix content")
            packet = _packet(rel, "PACKET CONTEXT ONLY\n")
            task = f"Target file: {rel}\nRender OK."
            plan = _architect_plan(task, packet, root)

            out = propose_coder_agent_implementation_diff(
                task=task,
                workspace_root=root,
                architect_plan=plan,
                llm_call=lambda prompt, _model: (
                    self.assertIn("PACKET CONTEXT ONLY", prompt)
                    or self.assertNotIn("stale repomix content", prompt)
                    or _json_response(
                        rel,
                        'export default function Page() { return <main>OK</main>; }\n',
                    )
                ),
            )

            self.assertEqual(out["target"], rel)
            self.assertFalse(out.get("coder_blocked", False))
            self.assertEqual(out["coder_diagnostics"]["context_slices"], [{"path": rel, "kind": "target"}])

    def test_tiny_markdown_append_uses_deterministic_target_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "docs/phase-8-manual-check.md"
            current = "# Manual Check\n"
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text(current, encoding="utf-8")
            _write_repomix(root, rel)
            task = (
                "Target file: docs/phase-8-manual-check.md\n\n"
                'Append one short sentence under the existing paragraph:\n'
                '"Manual verification should clearly report whether a diff was produced."'
            )
            plan = _architect_plan(task, _packet(rel, current), root)

            def fail_llm(_prompt: str, _alias: str) -> str:
                raise AssertionError("tiny docs append should not call the local Coder model")

            out = propose_coder_agent_diff_payload_from_plan(
                architect_plan=plan,
                workspace_root=root,
                llm_call=fail_llm,
                model_alias="local",
            )

            self.assertFalse(out.get("coder_blocked", False))
            self.assertEqual(out["target"], rel)
            self.assertIn(
                "+Manual verification should clearly report whether a diff was produced.",
                out["proposed_diff"],
            )

    def test_valid_json_replacement_returns_backend_generated_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/mock/CodingAgentInterface.tsx"
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nRender OK.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_response(
                    rel,
                    'export default function Page() { return <main className="min-h-screen">OK</main>; }\n',
                ),
            )

            self.assertEqual(out["target"], rel)
            self.assertFalse(out.get("coder_blocked", False))
            self.assertIn("+export default function Page()", out["proposed_diff"])
            self.assertIn("--- a/", out["proposed_diff"])
            self.assertEqual(out["coder_diagnostics"]["parsed_output_mode"], "replace_file")
            self.assertTrue(out["coder_diagnostics"]["generated_diff_by_backend"])
            self.assertFalse(out["coder_diagnostics"]["model_raw_diff_used"])
            self.assertEqual(out["coder_diagnostics"]["validation_status"], "preview_ready")
            self.assertGreater(out["coder_diagnostics"]["generated_diff_length"], 0)
            self.assertIsNot(out.get("already_satisfied"), True)

    def test_reviewer_blocked_attempt_retries_and_surfaces_successful_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/mock/CodingAgentInterface.tsx"
            current = "export default function Page() { return <main>Old</main>; }\n"
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text(current, encoding="utf-8")
            _write_repomix(root, rel)
            packet = _packet(rel, current)
            packet = CoderPacket(
                target_file=packet.target_file,
                operation=packet.operation,
                acceptance_criteria=[],
                constraints=ContentConstraints(["RequiredLiteral"], [], [], [], None, None),
                context_slices=packet.context_slices,
                forbidden_paths=packet.forbidden_paths,
                style_directives=packet.style_directives,
            )
            plan = _architect_plan(f"Target file: {rel}\nUpdate the page.", packet, root)
            responses = iter(
                [
                    _json_response(rel, "export default function Page() { return <main>Missing</main>; }\n"),
                    _json_response(rel, "export default function Page() { return <main>RequiredLiteral</main>; }\n"),
                ]
            )
            prompts: list[str] = []

            with mock.patch.dict("os.environ", {"SPIRIT_PROJECT_PATH": str(root)}):
                out = propose_coder_agent_diff_payload_from_plan(
                    architect_plan=plan,
                    workspace_root=root,
                    llm_call=lambda prompt, _model: prompts.append(prompt) or next(responses),
                    model_alias="local",
                )

            self.assertFalse(out.get("coder_blocked", False))
            self.assertIn("RequiredLiteral", out["proposed_diff"])
            self.assertEqual(out["coder_diagnostics"]["validation_status"], "preview_ready")
            self.assertEqual(out["coder_diagnostics"]["coder_attempt_count"], 2)
            self.assertEqual(out["coder_diagnostics"]["reviewer_retry_count"], 1)
            self.assertIn("REVIEWER FEEDBACK FROM PREVIOUS ATTEMPT", prompts[1])

    def test_repeated_same_reviewer_block_stops_after_bounded_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/mock/CodingAgentInterface.tsx"
            current = "export default function Page() { return <main>Old</main>; }\n"
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text(current, encoding="utf-8")
            _write_repomix(root, rel)
            packet = _packet(rel, current)
            packet = CoderPacket(
                target_file=packet.target_file,
                operation=packet.operation,
                acceptance_criteria=[],
                constraints=ContentConstraints(["RequiredLiteral"], [], [], [], None, None),
                context_slices=packet.context_slices,
                forbidden_paths=packet.forbidden_paths,
                style_directives=packet.style_directives,
            )
            plan = _architect_plan(f"Target file: {rel}\nUpdate the page.", packet, root)
            calls = 0

            def bad(_prompt: str, _model: str) -> str:
                nonlocal calls
                calls += 1
                return _json_response(rel, "export default function Page() { return <main>Missing</main>; }\n")

            with mock.patch.dict("os.environ", {"SPIRIT_PROJECT_PATH": str(root)}):
                out = propose_coder_agent_diff_payload_from_plan(
                    architect_plan=plan,
                    workspace_root=root,
                    llm_call=bad,
                    model_alias="local",
                )

            self.assertEqual(calls, 2)
            self.assertTrue(out["coder_blocked"])
            self.assertEqual(out["reason_code"], "blocked_after_retries")
            self.assertEqual(out["proposed_diff"], "")
            self.assertEqual(out["coder_diagnostics"]["validation_status"], "blocked_after_retries")
            self.assertIn("missing_must_contain", out["needed_context"])

    def test_bundle_snapshot_drift_blocks_before_model_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel, "initial")
            plan_result = plan_task_deterministically(
                f"Target file: {rel}\nRender OK.",
                "task-drift",
                root,
            )
            self.assertIsInstance(plan_result, Plan)
            _write_repomix(root, rel, "mutated")
            calls = 0

            def should_not_call(_prompt: str, _model: str) -> str:
                nonlocal calls
                calls += 1
                return _json_response(
                    rel,
                    'export default function Page() { return <main>OK</main>; }\n',
                )

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nRender OK.",
                workspace_root=root,
                architect_plan=plan_result.plan,
                llm_call=should_not_call,
            )

            self.assertEqual(calls, 0)
            self.assertTrue(out["coder_blocked"])
            self.assertEqual(out["reason_code"], "bundle_snapshot_drift")
            self.assertEqual(out["target"], rel)
            self.assertEqual(out["coder_diagnostics"]["bundle_snapshot_check"], "failed")
            self.assertNotEqual(
                out["coder_diagnostics"]["bundle_snapshot_expected_sha256"],
                out["coder_diagnostics"]["bundle_snapshot_actual_sha256"],
            )

    def test_replacement_content_identical_to_disk_returns_already_satisfied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            current = 'export default function Page() { return <main className="min-h-screen">OK</main>; }\n'
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text(current, encoding="utf-8")
            _write_repomix(root, rel, current)

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nRender OK.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_response(rel, current),
            )

            self.assertEqual(out["target"], rel)
            self.assertEqual(out["proposed_diff"], "")
            self.assertFalse(out["coder_blocked"])
            self.assertTrue(out["already_satisfied"])
            self.assertTrue(out["alreadySatisfied"])
            self.assertEqual(out["reason_code"], "coder_no_changes_needed")
            self.assertEqual(out["reasonCode"], "coder_no_changes_needed")
            self.assertEqual(out["status"], "already_satisfied")
            self.assertEqual(
                out["coder_diagnostics"]["validation_status"],
                "already_satisfied",
            )
            self.assertEqual(out["coder_diagnostics"]["generated_diff_length"], 0)
            self.assertTrue(out["coder_diagnostics"]["already_satisfied"])
            self.assertTrue(out["coder_diagnostics"]["no_changes_needed"])

    def test_subjective_visual_task_identical_content_does_not_return_already_satisfied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/components/dashboard/ThemeStrip.tsx"
            current = (
                "export function ThemeStrip() {\n"
                "  return <div className=\"flex gap-2\">Theme</div>;\n"
                "}\n"
            )
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text(current, encoding="utf-8")
            _write_repomix(root, rel, current)

            out = propose_coder_agent_implementation_diff(
                task=(
                    "make ThemeStrip feel more premium and alive, tighter spacing, "
                    "better glow, smoother hover states.\n"
                    f"Target file: {rel}"
                ),
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_response(rel, current),
            )

            self.assertEqual(out["target"], rel)
            self.assertEqual(out["proposed_diff"], "")
            self.assertTrue(out["coder_blocked"])
            self.assertIsNot(out.get("already_satisfied"), True)
            self.assertEqual(
                out["reason_code"],
                "coder_subjective_improvement_requires_diff_or_review",
            )
            self.assertFalse(out["coder_diagnostics"]["already_satisfied"])
            self.assertFalse(out["coder_diagnostics"]["no_changes_needed"])
            self.assertTrue(out["coder_diagnostics"]["subjective_improvement_detected"])

    def test_exact_objective_task_identical_content_still_returns_already_satisfied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/coding/design-demo/page.tsx"
            current = (
                'import { GlassPanel } from "@/components/ui/GlassPanel";\n\n'
                "export default function Page() {\n"
                "  return <main className=\"min-h-screen\">"
                "<h1 className=\"text-6xl font-light tracking-tighter\">Design Demo — Vibe Test Canvas</h1>"
                "<GlassPanel>Ready</GlassPanel><GlassPanel>Preview</GlassPanel></main>;\n"
                "}\n"
            )
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text(current, encoding="utf-8")
            _write_repomix(root, rel, current)

            out = propose_coder_agent_implementation_diff(
                task=(
                    f"Target file: {rel}\n"
                    'Ensure exact UI text "Design Demo — Vibe Test Canvas" is present, import GlassPanel, '
                    "and keep className fragments text-6xl font-light tracking-tighter min-h-screen."
                ),
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_response(rel, current),
            )

            self.assertEqual(out["proposed_diff"], "")
            self.assertTrue(out["already_satisfied"])
            self.assertEqual(out["reason_code"], "coder_no_changes_needed")

    def test_subjective_visual_task_changed_content_returns_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/components/dashboard/ThemeStrip.tsx"
            current = (
                "export function ThemeStrip() {\n"
                "  return <div className=\"flex gap-2\">Theme</div>;\n"
                "}\n"
            )
            changed = (
                "export function ThemeStrip() {\n"
                "  return <div className=\"flex gap-1 rounded-md shadow-cyan-400/40 transition-all duration-200 hover:shadow-lg\">Theme</div>;\n"
                "}\n"
            )
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text(current, encoding="utf-8")
            _write_repomix(root, rel, current)

            out = propose_coder_agent_implementation_diff(
                task=(
                    "make ThemeStrip feel more premium and alive, tighter spacing, "
                    "better glow, smoother hover states.\n"
                    f"Target file: {rel}"
                ),
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_response(rel, changed),
            )

            self.assertGreater(len(out["proposed_diff"]), 0)
            self.assertFalse(out.get("coder_blocked", False))
            self.assertIsNot(out.get("already_satisfied"), True)
            self.assertEqual(out["coder_diagnostics"]["validation_status"], "preview_ready")
            self.assertTrue(out["coder_diagnostics"]["visual_materiality_ok"])

    def test_subjective_visual_comment_only_diff_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/components/dashboard/ThemeStrip.tsx"
            current = (
                "export function ThemeStrip() {\n"
                '  // Default "strip" variant - unchanged behavior\n'
                "  return <div className=\"flex gap-2\">Theme</div>;\n"
                "}\n"
            )
            changed = current.replace("unchanged behavior", "refined behavior")
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text(current, encoding="utf-8")
            _write_repomix(root, rel, current)

            out = propose_coder_agent_implementation_diff(
                task=(
                    "make ThemeStrip feel more premium and alive, tighter spacing, "
                    "better glow, smoother hover states.\n"
                    f"Target file: {rel}"
                ),
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_response(rel, changed),
            )

            self.assertEqual(out["proposed_diff"], "")
            self.assertTrue(out["coder_blocked"])
            self.assertEqual(
                out["reason_code"],
                "coder_visual_improvement_diff_too_shallow",
            )
            self.assertFalse(out["coder_diagnostics"]["visual_materiality_ok"])
            self.assertTrue(out["coder_diagnostics"]["subjective_improvement_detected"])

    def test_subjective_visual_classname_change_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/components/dashboard/ThemeStrip.tsx"
            current = (
                "export function ThemeStrip({ active }: { active: boolean }) {\n"
                "  return <button className={active ? \"flex gap-2 transition-colors\" : \"flex gap-2\"}>Theme</button>;\n"
                "}\n"
            )
            changed = (
                "export function ThemeStrip({ active }: { active: boolean }) {\n"
                "  return <button className={active ? \"flex gap-1.5 transition-all duration-200 ease-out ring-1 shadow-cyan-400/40\" : \"flex gap-1.5 transition-all duration-200 ease-out hover:shadow-lg\"}>Theme</button>;\n"
                "}\n"
            )
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text(current, encoding="utf-8")
            _write_repomix(root, rel, current)

            out = propose_coder_agent_implementation_diff(
                task=(
                    "make ThemeStrip feel more premium and alive, tighter spacing, "
                    "better glow, smoother hover states.\n"
                    f"Target file: {rel}"
                ),
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_response(rel, changed),
            )

            self.assertGreater(len(out["proposed_diff"]), 0)
            self.assertFalse(out.get("coder_blocked", False))
            self.assertEqual(out["coder_diagnostics"]["validation_status"], "preview_ready")
            self.assertTrue(out["coder_diagnostics"]["visual_materiality_ok"])

    def test_subjective_visual_whitespace_only_diff_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/components/dashboard/ThemeStrip.tsx"
            current = (
                "export function ThemeStrip() {\n"
                "  return <div className=\"flex gap-2\">Theme</div>;\n"
                "}\n"
            )
            changed = (
                "export function ThemeStrip() {\n"
                "  return (\n"
                "    <div className=\"flex gap-2\">Theme</div>\n"
                "  );\n"
                "}\n"
            )
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text(current, encoding="utf-8")
            _write_repomix(root, rel, current)

            out = propose_coder_agent_implementation_diff(
                task=(
                    "make ThemeStrip feel more premium and alive, tighter spacing, "
                    "better glow, smoother hover states.\n"
                    f"Target file: {rel}"
                ),
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_response(rel, changed),
            )

            self.assertTrue(out["coder_blocked"])
            self.assertEqual(
                out["reason_code"],
                "coder_visual_improvement_diff_too_shallow",
            )

    def test_non_subjective_comment_diff_not_blocked_by_visual_materiality_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/components/dashboard/ThemeStrip.tsx"
            current = (
                "export function ThemeStrip() {\n"
                "  // Old comment\n"
                "  return <div className=\"flex gap-2\">Theme</div>;\n"
                "}\n"
            )
            changed = current.replace("Old comment", "New comment")
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text(current, encoding="utf-8")
            _write_repomix(root, rel, current)

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nRename this comment.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_response(rel, changed),
            )

            self.assertFalse(out.get("coder_blocked", False))
            self.assertGreater(len(out["proposed_diff"]), 0)
            self.assertEqual(out["coder_diagnostics"]["validation_status"], "preview_ready")
            self.assertNotIn("visual_materiality_ok", out["coder_diagnostics"])

    def test_subjective_noop_still_uses_subjective_improvement_requires_diff_or_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/components/dashboard/ThemeStrip.tsx"
            current = (
                "export function ThemeStrip() {\n"
                "  return <div className=\"flex gap-2\">Theme</div>;\n"
                "}\n"
            )
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text(current, encoding="utf-8")
            _write_repomix(root, rel, current)

            noop = propose_coder_agent_implementation_diff(
                task=(
                    "make ThemeStrip feel more premium and alive, tighter spacing, "
                    "better glow, smoother hover states.\n"
                    f"Target file: {rel}"
                ),
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_response(rel, current),
            )
            comment_only = propose_coder_agent_implementation_diff(
                task=(
                    "make ThemeStrip feel more premium and alive, tighter spacing, "
                    "better glow, smoother hover states.\n"
                    f"Target file: {rel}"
                ),
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_response(
                    rel,
                    current.replace("return", "// refined behavior\n  return"),
                ),
            )

            self.assertEqual(
                noop["reason_code"],
                "coder_subjective_improvement_requires_diff_or_review",
            )
            self.assertEqual(
                comment_only["reason_code"],
                "coder_visual_improvement_diff_too_shallow",
            )

    def test_replacement_content_changed_returns_backend_generated_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text("export default function Page() { return <main>Old</main>; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nRender New.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_response(
                    rel,
                    "export default function Page() { return <main>New</main>; }\n",
                ),
            )

            self.assertFalse(out.get("coder_blocked", False))
            self.assertGreater(out["coder_diagnostics"]["generated_diff_length"], 0)
            self.assertEqual(out["coder_diagnostics"]["validation_status"], "preview_ready")
            self.assertIsNot(out.get("already_satisfied"), True)

    def test_empty_diff_without_matching_disk_still_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text("export default function Page() { return <main>Old</main>; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            with mock.patch(
                "source_proxy.tasks.long_running.generate_unified_diff_from_content",
                return_value="",
            ):
                out = propose_coder_agent_implementation_diff(
                    task=f"Target file: {rel}\nRender New.",
                    workspace_root=root,
                    llm_call=lambda _prompt, _model: _json_response(
                        rel,
                        "export default function Page() { return <main>New</main>; }\n",
                    ),
                )

            self.assertTrue(out["coder_blocked"])
            self.assertEqual(out["reason_code"], "coder_backend_diff_generation_failed")
            self.assertIsNot(out.get("already_satisfied"), True)

    def test_missing_target_empty_diff_does_not_become_already_satisfied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            _write_repomix(root, rel)

            with mock.patch(
                "source_proxy.tasks.long_running.generate_unified_diff_from_content",
                return_value="",
            ):
                out = propose_coder_agent_implementation_diff(
                    task=f"Target file: {rel}\nCreate New.",
                    workspace_root=root,
                    llm_call=lambda _prompt, _model: _json_response(
                        rel,
                        "export default function Page() { return <main>New</main>; }\n",
                    ),
                )

            self.assertTrue(out["coder_blocked"])
            self.assertEqual(out["reason_code"], "coder_backend_diff_generation_failed")
            self.assertIsNot(out.get("already_satisfied"), True)

    def test_fenced_json_replacement_returns_parsed_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            target = root / rel
            target.parent.mkdir(parents=True)
            target.write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nUpdate the page.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: "```json\n"
                + _json_response(rel, "export default function Page() { return <main>Done</main>; }\n")
                + "\n```",
            )

            self.assertEqual(out["target"], rel)
            self.assertIn("Done", out["proposed_diff"])

    def test_content_lines_replacement_returns_backend_generated_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            content = "export default function Page() {\n  return <main>Lines</main>;\n}\n"
            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nUpdate the page.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_lines_response(rel, content),
            )

            self.assertFalse(out.get("coder_blocked", False))
            self.assertIn("Lines", out["proposed_diff"])
            self.assertEqual(out["coder_diagnostics"]["json_attempt_count"], 1)

    def test_content_lines_preferred_over_legacy_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nUpdate the page.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: json.dumps(
                    {
                        "action": "replace_file",
                        "target": rel,
                        "content": "export default function Page() { return <main>Legacy</main>; }\n",
                        "content_lines": [
                            "export default function Page() {",
                            "  return <main>Preferred</main>;",
                            "}",
                        ],
                    }
                ),
            )

            self.assertFalse(out.get("coder_blocked", False))
            self.assertIn("Preferred", out["proposed_diff"])
            self.assertNotIn("Legacy", out["proposed_diff"])

    def test_content_lines_rejects_non_string_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nUpdate the page.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: json.dumps(
                    {
                        "action": "replace_file",
                        "target": rel,
                        "content_lines": ["export default function Page() {", 42, "}"],
                    }
                ),
            )

            self.assertTrue(out["coder_blocked"])
            self.assertEqual(out["reason_code"], "coder_response_repair_exhausted")
            self.assertIn("list of strings", out["coder_diagnostics"]["last_json_error"])

    def test_prose_wrapped_json_replacement_is_recovered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nUpdate the page.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: "Here is the JSON:\n"
                + _json_lines_response(rel, "export default function Page() { return <main>Recovered</main>; }\n")
                + "\nDone.",
            )

            self.assertFalse(out.get("coder_blocked", False))
            self.assertIn("Recovered", out["proposed_diff"])

    def test_trailing_comma_json_replacement_is_repaired(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nUpdate the page.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: (
                    "{"
                    f'"action":"replace_file","target":"{rel}",'
                    '"content_lines":["export default function Page() { return <main>Repair</main>; }",],'
                    "}"
                ),
            )

            self.assertFalse(out.get("coder_blocked", False))
            self.assertIn("Repair", out["proposed_diff"])

    def test_prose_response_returns_coder_response_not_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nUpdate the page.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: "Here is what I would do.",
            )

            self.assertTrue(out["coder_blocked"])
            self.assertEqual(out["reason_code"], "coder_response_repair_exhausted")
            self.assertEqual(out["proposed_diff"], "")
            self.assertIn("Here is what I would do.", out["coder_diagnostics"]["raw_response_excerpt"])
            self.assertEqual(out["coder_diagnostics"]["json_attempt_count"], 2)

    def test_unified_diff_response_retries_then_blocks_without_approval_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nUpdate the page.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: "\n".join(
                    [
                        "diff --git a/src/app/demo/page.tsx b/src/app/demo/page.tsx",
                        "--- a/src/app/demo/page.tsx",
                        "+++ b/src/app/demo/page.tsx",
                        "@@ -1 +1 @@",
                        "-export default function Page() { return null; }",
                        "+export default function Page() { return <main>Diff</main>; }",
                        "",
                    ]
                ),
            )

            self.assertTrue(out["coder_blocked"])
            self.assertEqual(out["reason_code"], "coder_response_repair_exhausted")
            self.assertEqual(out["proposed_diff"], "")
            self.assertIn(
                "unified diff",
                out["coder_diagnostics"]["last_json_error"].lower(),
            )

    def test_json_with_wrong_target_returns_coder_target_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            wrong = "src/app/other/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nUpdate the page.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_response(
                    wrong, "export default function Page() { return <main />; }\n"
                ),
            )

            self.assertTrue(out["coder_blocked"])
            self.assertEqual(out["reason_code"], "coder_target_mismatch")

    def test_json_with_missing_content_returns_invalid_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nUpdate the page.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: json.dumps(
                    {"action": "replace_file", "target": rel}
                ),
            )

            self.assertTrue(out["coder_blocked"])
            self.assertEqual(out["reason_code"], "coder_response_repair_exhausted")
            self.assertIn("content", out["coder_diagnostics"]["last_json_error"])

    def test_blocked_json_returns_coder_blocked_without_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/coding/design-demo/page.tsx"
            _write_repomix(root, rel, "")

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nCreate the page.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: json.dumps(
                    {
                        "action": "blocked",
                        "reason_code": "coder_needs_context",
                        "reason": "missing GlassPanel source",
                        "needed_context": ["src/components/ui/GlassPanel.tsx"],
                    }
                ),
            )

            self.assertEqual(out["target"], rel)
            self.assertEqual(out["proposed_diff"], "")
            self.assertTrue(out["coder_blocked"])
            self.assertEqual(out["reason_code"], "coder_needs_context")

    def test_raw_task_text_inside_tsx_content_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nOutput ONLY a clean replacement.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_response(
                    rel,
                    "Target file: src/app/demo/page.tsx\nexport default function Page() { return <main />; }\n",
                ),
            )

            self.assertTrue(out["coder_blocked"])
            self.assertEqual(out["reason_code"], "coder_replacement_content_validation_failed")

    def test_invalid_json_then_valid_json_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)
            responses = iter(
                [
                    "not json",
                    _json_response(rel, "export default function Page() { return <main>Fixed</main>; }\n"),
                ]
            )

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nUpdate the page.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: next(responses),
            )

            self.assertFalse(out.get("coder_blocked", False))
            self.assertIn("Fixed", out["proposed_diff"])

    def test_missing_requirement_then_fixed_content_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/coding/design-demo/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)
            valid = (
                'import { GlassPanel } from "@/components/ui/GlassPanel";\n\n'
                "const panels = ['One', 'Two'];\n\n"
                "export default function Page() {\n"
                "  return <main className=\"min-h-screen\"><h1 className=\"text-6xl font-light tracking-tighter\">Design Demo — Vibe Test Canvas</h1>"
                "{panels.map((panel) => <GlassPanel key={panel}>{panel}</GlassPanel>)}</main>;\n"
                "}\n"
            )
            out = propose_coder_agent_implementation_diff(
                task=(
                    f"Target file: {rel}\nCreate a brand new clean design-demo page at /coding/design-demo.\n"
                    'Big centered <h1 className="text-6xl font-light tracking-tighter">Design Demo — Vibe Test Canvas</h1>\n'
                    'Import GlassPanel from "@/components/ui/GlassPanel"'
                ),
                workspace_root=root,
                llm_call=lambda _prompt, _model: _json_response(rel, valid),
            )

            self.assertFalse(out.get("coder_blocked", False))
            self.assertIn("Design Demo", out["proposed_diff"])

    def test_three_invalid_attempts_returns_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nUpdate the page.",
                workspace_root=root,
                llm_call=lambda _prompt, _model: "still not json",
            )

            self.assertTrue(out["coder_blocked"])
            self.assertEqual(out["reason_code"], "coder_response_repair_exhausted")
            self.assertEqual(out["coder_diagnostics"]["json_attempt_count"], 2)

    def test_provider_exception_does_not_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)
            calls = 0

            def fail(_prompt: str, _model: str) -> str:
                nonlocal calls
                calls += 1
                raise RuntimeError("DeepSeek insufficient balance")

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {rel}\nUpdate the page.",
                workspace_root=root,
                llm_call=fail,
            )

            self.assertEqual(calls, 1)
            self.assertTrue(out["coder_blocked"])
            self.assertEqual(out["reason_code"], "coder_model_router_error")

    def test_missing_repomix_returns_empty_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = propose_coder_agent_implementation_diff(
                task="Add padding",
                workspace_root=Path(tmp),
            )
            self.assertEqual(out["proposed_diff"], "")
            self.assertEqual(out["target"], "")

    def test_missing_coder_model_alias_returns_configured_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/coding/design-demo/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            _write_repomix(root, rel)

            with mock.patch.dict("os.environ", {}, clear=True):
                out = propose_coder_agent_implementation_diff(
                    task=f"Target file: {rel}\nCreate a brand new page.",
                    workspace_root=root,
                )

            self.assertEqual(out["proposed_diff"], "")
            self.assertTrue(out["coder_blocked"])
            self.assertEqual(out["reason_code"], "coder_model_not_configured")
            self.assertIn("SOURCE_PROXY_CODER_MODEL_ALIAS", out["needed_context"])

    def test_repomix_ignores_spirit_backups_in_favor_of_src(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            good = "src/components/coding/CodingAgentInterface.tsx"
            bad = ".spirit-backups/2026-05-12/approved-diff-foo/src/components/coding/CodingAgentInterface.tsx"
            (root / good).parent.mkdir(parents=True, exist_ok=True)
            (root / good).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            (root / "repomix-output.xml").write_text(
                f'<repomix><files><file path="{bad}">x</file><file path="{good}">y</file></files></repomix>',
                encoding="utf-8",
            )

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {good}\nAdd padding to the main layout",
                workspace_root=root,
                llm_call=lambda prompt, _model: _json_response(
                    good,
                    'export default function Page() { return <main className="p-4">OK</main>; }\n',
                )
                if good in prompt and bad not in prompt
                else "not json",
            )

            self.assertEqual(out["target"], good)
            self.assertIn("p-4", out["proposed_diff"])
            self.assertNotIn(".spirit-backups/", out["proposed_diff"])

    def test_explicit_target_wins_over_repomix_ranking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            explicit = "src/app/coding/design-demo/page.tsx"
            tempting = "src/components/coding/CodingAgentInterface.tsx"
            for rel in (explicit, tempting):
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("export default function Page() { return null; }\n", encoding="utf-8")
            (root / "repomix-output.xml").write_text(
                f'<repomix><files><file path="{tempting}">x</file><file path="{explicit}">y</file></files></repomix>',
                encoding="utf-8",
            )

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {explicit}\nCreate the /coding/design-demo page.",
                workspace_root=root,
                llm_call=lambda prompt, _model: _json_response(
                    explicit,
                    'import { GlassPanel } from "@/components/ui/GlassPanel";\n\n'
                    "const panels = ['One', 'Two'];\n\n"
                    "export default function Page() {\n"
                    "  return <main className=\"min-h-screen\"><h1 className=\"text-6xl font-light tracking-tighter\">Design Demo — Vibe Test Canvas</h1>"
                    "{panels.map((panel) => <GlassPanel key={panel}>{panel}</GlassPanel>)}</main>;\n"
                    "}\n",
                )
                if f"Target file: {explicit}" in prompt
                else "not json",
            )

            self.assertEqual(out["target"], explicit)
            self.assertIn(f"+++ b/{explicit}", out["proposed_diff"])

    def test_user_app_mode_excludes_proxy_source_from_inferred_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app = "src/app/page.tsx"
            proxy = "source_proxy/decision/router.py"
            (root / app).parent.mkdir(parents=True, exist_ok=True)
            (root / app).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            (root / proxy).parent.mkdir(parents=True, exist_ok=True)
            (root / proxy).write_text("def route():\n    return None\n", encoding="utf-8")
            (root / "repomix-output.xml").write_text(
                f'<repomix><files><file path="{proxy}">proxy</file><file path="{app}">app</file></files></repomix>',
                encoding="utf-8",
            )

            out = propose_coder_agent_implementation_diff(
                task="Add a small heading to the main app page.",
                workspace_root=root,
                llm_call=lambda prompt, _model: _json_response(
                    app,
                    'export default function Page() { return <main>OK</main>; }\n',
                )
                if f"Target file: {app}" in prompt and proxy not in prompt
                else "not json",
            )

            self.assertEqual(out["target"], app)
            self.assertEqual(out["coder_diagnostics"]["context_mode"], "user_app")
            self.assertIn("source_proxy/", out["coder_diagnostics"]["forbidden_paths"])
            self.assertEqual(
                out["coder_diagnostics"]["context_slices"],
                [{"path": app, "kind": "target"}],
            )
            self.assertEqual(out["coder_diagnostics"]["validation_status"], "preview_ready")

    def test_agent_internal_mode_reports_opposite_side_forbidden_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = "source_proxy/decision/router.py"
            app = "src/app/page.tsx"
            (root / agent).parent.mkdir(parents=True, exist_ok=True)
            (root / agent).write_text("def route():\n    return None\n", encoding="utf-8")
            (root / app).parent.mkdir(parents=True, exist_ok=True)
            (root / app).write_text("export default function Page() { return null; }\n", encoding="utf-8")
            (root / "repomix-output.xml").write_text(
                f'<repomix><files><file path="{app}">app</file><file path="{agent}">agent</file></files></repomix>',
                encoding="utf-8",
            )

            out = propose_coder_agent_implementation_diff(
                task=f"Target file: {agent}\nFix route classification for empty tasks.",
                workspace_root=root,
                llm_call=lambda prompt, _model: _json_response(
                    agent,
                    "def route():\n    return 'ok'\n",
                )
                if f"Target file: {agent}" in prompt and app not in prompt
                else "not json",
            )

            self.assertEqual(out["target"], agent)
            self.assertEqual(out["coder_diagnostics"]["context_mode"], "agent_internal")
            self.assertIn("src/app/", out["coder_diagnostics"]["forbidden_paths"])
            self.assertEqual(
                out["coder_diagnostics"]["context_slices"],
                [{"path": agent, "kind": "target"}],
            )
            self.assertEqual(out["coder_diagnostics"]["validation_status"], "preview_ready")

    def test_generate_unified_diff_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            (root / rel).parent.mkdir(parents=True)
            (root / rel).write_text("old\n", encoding="utf-8")
            diff = generate_unified_diff_from_content(root, rel, "new")
            self.assertIn(f"--- a/{rel}", diff)
            self.assertIn(f"+++ b/{rel}", diff)
            self.assertIn("-old", diff)
            self.assertIn("+new", diff)
            self.assertTrue(diff.endswith("\n"))

    def test_generate_unified_diff_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "src/app/demo/page.tsx"
            diff = generate_unified_diff_from_content(root, rel, "new")
            self.assertIn("new file mode 100644", diff)
            self.assertIn("--- /dev/null", diff)
            self.assertIn(f"+++ b/{rel}", diff)

    def test_generate_unified_diff_blocks_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                generate_unified_diff_from_content(Path(tmp), "../outside.ts", "x")

    def test_prompt_contract_mentions_json_replacement_and_blocked(self) -> None:
        self.assertIn("complete final content", CODER_SYSTEM_PROMPT)
        self.assertIn('"action":"replace_file"', CODER_SYSTEM_PROMPT)
        self.assertIn('"content_lines":["line 1","line 2"]', CODER_SYSTEM_PROMPT)
        self.assertIn("Return only JSON", CODER_SYSTEM_PROMPT)
        self.assertIn("TaskSpec.allowed_files", CODER_SYSTEM_PROMPT)
        self.assertIn('"action":"blocked"', CODER_SYSTEM_PROMPT)
        self.assertNotIn("Output ONLY a valid unified diff", CODER_SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
