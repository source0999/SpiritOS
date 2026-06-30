from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any


SUBJECTIVE_IMPROVEMENT_REQUIRES_DIFF_REASON_CODE = (
    "coder_subjective_improvement_requires_diff_or_review"
)
VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE = (
    "coder_visual_improvement_diff_too_shallow"
)
SUBJECTIVE_IMPROVEMENT_PHRASES: tuple[str, ...] = (
    "make it more",
    "make the",
    "feel more",
    "feels more",
    "more premium",
    "premium",
    "alive",
    "better glow",
    "smoother hover",
    "hover states",
    "cyber-minimal",
    "vibe",
    "energy",
    "sleek",
    "cleaner",
    "more professional",
    "futuristic",
    "glass",
    "glassy",
    "spacing",
    "tighter spacing",
    "visual",
    "polish",
    "enhance",
    "improve",
)
VISUAL_MATERIAL_DIFF_MARKERS: tuple[str, ...] = (
    "className=",
    "style=",
    "hover:",
    "focus:",
    "active:",
    "transition",
    "duration-",
    "ease-",
    "shadow",
    "drop-shadow",
    "ring",
    "border",
    "bg-",
    "text-",
    "opacity",
    "blur",
    "backdrop",
    "gap-",
    "p-",
    "px-",
    "py-",
    "m-",
    "mx-",
    "my-",
    "rounded",
    "scale-",
    "translate",
    "animate",
    "motion",
    "<button",
    "<div",
    "<span",
    "<GlassPanel",
    "data-",
    "aria-pressed",
    "onMouse",
    "onPointer",
    "onFocus",
    "onBlur",
)


def task_requests_subjective_improvement(task: str) -> bool:
    lowered = re.sub(r'(["`]).*?\1', " ", task.lower())
    if _task_requests_objective_lumacart_product_render(lowered):
        return False
    return any(
        re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", lowered)
        for phrase in SUBJECTIVE_IMPROVEMENT_PHRASES
    )


def _task_requests_objective_lumacart_product_render(lowered_task: str) -> bool:
    return (
        "coder-003-render-product-cards" in lowered_task
        or (
            "lumacart" in lowered_task
            and "src/products.js" in lowered_task
            and "src/main.js" in lowered_task
            and "product" in lowered_task
            and (
                "render" in lowered_task
                or "card" in lowered_task
                or "category" in lowered_task
            )
        )
    )


def subjective_visual_diff_is_material(
    unified_diff: str,
    replacement_content: str,
    task: str,
) -> tuple[bool, list[str]]:
    """Return true when a subjective visual task changes UI-affecting code."""
    if not task_requests_subjective_improvement(task):
        return True, []

    changed_lines: list[str] = []
    removed_lines: list[str] = []
    added_lines: list[str] = []
    for line in unified_diff.splitlines():
        if line.startswith(("+++", "---", "@@", "diff --git", "index ")):
            continue
        if not line.startswith(("+", "-")):
            continue
        body = line[1:]
        stripped = body.strip()
        if not stripped:
            continue
        if _visual_diff_line_is_non_material(stripped):
            continue
        changed_lines.append(stripped)
        if line.startswith("+"):
            added_lines.append(stripped)
        else:
            removed_lines.append(stripped)

    if not changed_lines:
        return False, ["subjective visual task produced only comment or non-visual changes"]
    if removed_lines and added_lines and _visual_semantic_text(removed_lines) == _visual_semantic_text(added_lines):
        return False, ["subjective visual task produced only comment or non-visual changes"]

    marker_line = next(
        (
            line
            for line in changed_lines
            if any(marker in line for marker in VISUAL_MATERIAL_DIFF_MARKERS)
        ),
        "",
    )
    if marker_line:
        return True, []

    # Replacement content is a secondary signal only. The gate is diff-first, but this
    # catches multi-line JSX/attribute edits where the changed diff line is structural.
    if any(marker in replacement_content for marker in VISUAL_MATERIAL_DIFF_MARKERS):
        for line in changed_lines:
            if re.search(r"</?[A-ZA-Za-z][A-Za-z0-9.:-]*\b|(?:className|style|data-[\w-]+)\s*=", line):
                return True, []

    return False, ["subjective visual task produced only comment or non-visual changes"]


def _visual_diff_line_is_non_material(stripped: str) -> bool:
    if stripped.startswith(("import ", "export type ", "type ", "interface ")):
        return True
    if stripped.startswith(("//", "/*", "*", "*/")):
        return True
    if stripped in {"{", "}", "(", ")", ");", "};", ",", ";"}:
        return True
    if re.match(r'^[rubf]*("""|\'\'\')', stripped):
        return True
    return False


def _visual_semantic_text(lines: list[str]) -> str:
    text = "".join(lines)
    text = re.sub(r"\s+", "", text)
    return re.sub(r"[(){};]", "", text)


def validate_replacement_content(
    *,
    workspace_root: Path,
    target_path: str,
    content: str,
    task_text: str | None = None,
) -> dict[str, Any]:
    """Validate full replacement content before it is converted into a diff."""
    from source_proxy.verification.diff import (
        _extract_class_fragments,
        _extract_explicit_target,
        _extract_import_requirements,
        _requirement_source_text,
        _extract_text_requirements,
        _run_typescript_parse_check,
    )

    from source_proxy.safety.paths import normalize_repo_path_candidate

    normalized_target = normalize_repo_path_candidate(target_path)
    missing: list[str] = []
    task = _requirement_source_text(task_text or "")

    raw_prompt_markers = (
        "Target file:",
        "Output ONLY",
        "CURRENT FILE CONTENT",
        "ACCEPTANCE CRITERIA",
        "CODER_BLOCKED",
        "Create a brand new clean design-demo",
    )
    for marker in raw_prompt_markers:
        if marker in content:
            missing.append(f"raw prompt text detected: {marker}")

    target = _extract_explicit_target(task)
    if target:
        target = normalize_repo_path_candidate(target)
    if target and target != normalized_target:
        missing.append(f"target mismatch: {normalized_target} != {target}")

    text_requirements = _extract_text_requirements(task)
    texts = text_requirements["required_final_terms"]
    class_fragments = _extract_class_fragments(task)
    imports = _extract_import_requirements(task)
    for text in texts:
        if text not in content:
            missing.append(f"missing exact text: {text}")
    for fragment in class_fragments:
        if fragment not in content:
            missing.append(f"missing className: {fragment}")
    for item in imports:
        symbol = item["symbol"]
        source = item["source"]
        if symbol not in content or source not in content:
            missing.append(f"missing import: {symbol} from {source}")

    design_demo = "design-demo" in normalized_target or "/coding/design-demo" in task
    if design_demo:
        design_demo_title = "Design Demo \u2014 Vibe Test Canvas"
        required = {
            'import { GlassPanel } from "@/components/ui/GlassPanel";': "missing GlassPanel import",
            design_demo_title: f"missing exact text: {design_demo_title}",
            "text-6xl": "missing className: text-6xl",
            "font-light": "missing className: font-light",
            "tracking-tighter": "missing className: tracking-tighter",
        }
        optional_absent_terms = set(text_requirements["optional_absent_terms"])
        for needle, reason in required.items():
            if needle in optional_absent_terms:
                continue
            if needle not in content:
                missing.append(reason)
        if "min-h-screen" not in content and "min-h-dvh" not in content:
            missing.append("missing full-height class: min-h-screen or min-h-dvh")
        glasspanel_openings = len(re.findall(r"<GlassPanel\b", content))
        has_mapped_glasspanel = ".map(" in content and "<GlassPanel" in content
        if glasspanel_openings < 2 and not has_mapped_glasspanel:
            missing.append("missing multiple GlassPanel sections")
        if re.search(r"\b(?:const|function)\s+GlassPanel\b", content):
            missing.append("fake GlassPanel component declared in replacement content")
        h1_text_count = content.count(design_demo_title)
        h1_tag_count = len(re.findall(r"<h1\b", content, flags=re.IGNORECASE))
        if h1_text_count > 1 or h1_tag_count > 1:
            missing.append("duplicate nested h1 detected")

    suffix = PurePosixPath(normalized_target).suffix.lower()
    syntax_check = {
        "ok": True,
        "skipped": True,
        "summary": "No TS/TSX replacement syntax check required.",
    }
    if suffix in {".ts", ".tsx"}:
        try:
            with tempfile.TemporaryDirectory(prefix="spirit-replacement-preview-") as tmp:
                temp_root = Path(tmp)
                abs_target = temp_root / normalized_target
                abs_target.parent.mkdir(parents=True, exist_ok=True)
                abs_target.write_text(content, encoding="utf-8", newline="\n")
                syntax_check = _run_typescript_parse_check(
                    workspace_root=workspace_root,
                    temp_root=temp_root,
                    rel_paths=[normalized_target],
                )
        except (OSError, subprocess.SubprocessError) as error:
            syntax_check = {
                "ok": False,
                "path": normalized_target,
                "summary": f"TypeScript replacement syntax check failed to run: {error}",
            }
        if not syntax_check.get("ok"):
            missing.append(str(syntax_check.get("summary") or "TypeScript syntax failed"))

    return {
        "ok": not missing,
        "missing": list(dict.fromkeys(missing)),
        "summary": "Replacement content validation passed." if not missing else "; ".join(list(dict.fromkeys(missing))[:8]),
        "typescript_check": syntax_check,
    }
