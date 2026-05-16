from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Literal
from uuid import uuid4

from source_proxy.decision.router import resolve_target_from_task
from source_proxy.planning.plan import (
    PLAN_SCHEMA_VERSION,
    AcceptanceCriterion,
    ArchitectPlan,
    BundleSnapshot,
    CoderPacket,
    ContentConstraints,
    ContextSlice,
    PlanBudget,
    TargetFile,
    TaskClassification,
    VerificationCheck,
    VerificationPlan,
)
from source_proxy.routing.litellm_router import available_model_aliases, get_router
from source_proxy.safety.paths import normalize_repo_path_candidate, unsafe_target_from_task
from source_proxy.tasks.long_running import (
    REPOMIX_BUNDLE_NAMES,
    derive_context_mode,
    forbidden_paths_for_context_mode,
)


DeterministicPlanKind = Literal["plan", "fallthrough_to_llm", "blocked"]


@dataclass(frozen=True)
class Plan:
    plan: ArchitectPlan
    kind: DeterministicPlanKind = "plan"


@dataclass(frozen=True)
class FallthroughToLLM:
    reason: str
    kind: DeterministicPlanKind = "fallthrough_to_llm"


@dataclass(frozen=True)
class Block:
    reason: str
    kind: DeterministicPlanKind = "blocked"


DeterministicPlanResult = Plan | FallthroughToLLM | Block

_CREATION_INTENT_RE = re.compile(
    r"\b(create|scaffold|build\s+from\s+scratch|implement\s+from\s+scratch|"
    r"new\s+(page|module|component|feature|file)|design\s+from\s+scratch)\b",
    re.IGNORECASE,
)
_FIX_RE = re.compile(r"\b(fix|bug|debug|broken|crash|error|regression)\b", re.IGNORECASE)
_REFACTOR_RE = re.compile(r"\b(refactor|rename|extract|dedupe|decompose)\b", re.IGNORECASE)
_STYLE_RE = re.compile(
    r"\b(style|hover|active|glow|spacing|padding|margin|layout|color|font|"
    r"visual|premium|polish|animation|transition|rounded|shadow)\b",
    re.IGNORECASE,
)
_EXPLAIN_RE = re.compile(r"\b(explain|summarize|describe|why)\b", re.IGNORECASE)
_IMPORT_RE = re.compile(
    r"^\s*import(?:\s+type)?(?:[\s\S]*?\s+from\s+)?[\"']([^\"']+)[\"'];?\s*$",
    re.MULTILINE,
)
_EXPORT_NAME_RE = re.compile(
    r"\bexport\s+(?:default\s+)?(?:function|class|const|let|var|interface|type)\s+([A-Za-z_$][\w$]*)"
)
_CLASS_FRAGMENT_RE = re.compile(
    r"\b(?:[a-z]+:)*[a-z][a-z0-9-]*(?:-\[[^\]\s]+\]|-[a-z0-9./]+)+\b",
    re.IGNORECASE,
)
_CODE_IDENTIFIER_RE = re.compile(
    r"(?<![A-Za-z0-9_$./-])(?:"
    r"[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)+"
    r"|[A-Z][A-Za-z0-9_$]*[a-z0-9_$][A-Za-z0-9_$]*[A-Z][A-Za-z0-9_$]*"
    r"|[a-z][A-Za-z0-9_$]*[A-Z][A-Za-z0-9_$]*"
    r"|[A-Za-z_$][\w$]*_[A-Za-z0-9_$][\w$]*"
    r")(?![A-Za-z0-9_$/-])"
)
_CLASS_UTILITY_PREFIXES = {
    "accent",
    "align",
    "animate",
    "aspect",
    "backdrop",
    "bg",
    "block",
    "border",
    "bottom",
    "col",
    "container",
    "content",
    "cursor",
    "decoration",
    "delay",
    "divide",
    "drop",
    "duration",
    "ease",
    "fill",
    "filter",
    "flex",
    "flow",
    "font",
    "gap",
    "gradient",
    "grid",
    "grow",
    "h",
    "hover",
    "inset",
    "items",
    "justify",
    "left",
    "leading",
    "line",
    "m",
    "max",
    "mb",
    "min",
    "ml",
    "mr",
    "mt",
    "mx",
    "my",
    "object",
    "opacity",
    "order",
    "outline",
    "overflow",
    "p",
    "pb",
    "place",
    "pl",
    "pointer",
    "pr",
    "pt",
    "px",
    "py",
    "relative",
    "resize",
    "right",
    "ring",
    "rotate",
    "rounded",
    "scale",
    "shadow",
    "shrink",
    "skew",
    "space",
    "sr",
    "stroke",
    "table",
    "text",
    "top",
    "tracking",
    "transform",
    "transition",
    "translate",
    "underline",
    "w",
    "z",
}
_FRAGMENT_META_WORDS = {"class", "classname", "classes", "fragment", "fragments", "include", "includes", "target"}
_CODE_FRAGMENT_PATH_SUFFIXES = {
    ".css",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".mdx",
    ".py",
    ".ts",
    ".tsx",
}
_ROUTE_RE = re.compile(r"(?<![A-Za-z0-9_./@<-])(/[A-Za-z0-9_()/.-]+)")
_FILE_PATH_IN_REPOMIX_RE = re.compile(r'<file\s+path="([^"]+)"')
_RISKY_COMMAND_RE = re.compile(
    r"\b(run|execute|shell|terminal|command|script|npm|python|pytest|curl|powershell|bash)\b",
    re.IGNORECASE,
)


class ArchitectLLMError(ValueError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def plan_task_deterministically(
    task: str,
    task_id: str,
    workspace_root: Path,
) -> DeterministicPlanResult:
    clean_task = (task or "").strip()
    root = workspace_root.resolve()
    if len(clean_task) > 500:
        return FallthroughToLLM("task_too_long")
    unsafe_target = unsafe_target_from_task(clean_task, root)
    if unsafe_target is not None:
        return Block(unsafe_target.reason_code)
    if _CREATION_INTENT_RE.search(clean_task):
        return FallthroughToLLM("creation_task")

    resolved = resolve_target_from_task(clean_task, root)
    markdown_append = plan_markdown_append_deterministically(
        clean_task,
        task_id,
        root,
        resolved=resolved,
    )
    if isinstance(markdown_append, (Plan, Block)):
        return markdown_append
    if not resolved.path:
        return FallthroughToLLM("no_explicit_target")

    target_abs = (root / resolved.path).resolve()
    if not _is_relative_to(target_abs, root):
        return Block("target_outside_workspace")
    if not target_abs.is_file():
        return FallthroughToLLM("target_missing")

    target_content = target_abs.read_text(encoding="utf-8", errors="replace")
    target_hash = _sha256_bytes(target_abs.read_bytes())
    context_mode = derive_context_mode(resolved.path)
    forbidden_paths = list(forbidden_paths_for_context_mode(context_mode))
    context_slices = [
        _context_slice(resolved.path, "target", target_content),
        *_import_context_slices(root, resolved.path, target_content),
    ]

    plan = ArchitectPlan(
        plan_id=uuid4().hex,
        task_id=task_id,
        schema_version=PLAN_SCHEMA_VERSION,
        created_at=_now_iso(),
        source_task=clean_task,
        bundle_snapshot=_bundle_snapshot(root),
        classification=_classify_task(clean_task, resolved.path),
        coder_packet=CoderPacket(
            target_file=TargetFile(
                path=resolved.path,
                exists=True,
                sha256_before=target_hash,
            ),
            operation="edit",
            acceptance_criteria=_acceptance_criteria(clean_task, resolved.path),
            constraints=_content_constraints(clean_task, target_content),
            context_slices=context_slices,
            forbidden_paths=forbidden_paths,
            style_directives=_style_directives(resolved.path),
        ),
        verification_plan=_verification_plan(resolved.path),
        budget=PlanBudget(
            max_coder_attempts=3,
            max_total_seconds=120,
            cloud_escalation_allowed=True,
        ),
    )
    return Plan(plan)


def plan_markdown_append_deterministically(
    task: str,
    task_id: str,
    workspace_root: Path,
    *,
    resolved: Any | None = None,
) -> DeterministicPlanResult:
    """Build the narrow no-LLM plan for tiny explicit Markdown append requests."""
    clean_task = (task or "").strip()
    root = workspace_root.resolve()
    if not clean_task or len(clean_task) > 500:
        return FallthroughToLLM("task_too_long")
    unsafe_target = unsafe_target_from_task(clean_task, root)
    if unsafe_target is not None:
        return Block(unsafe_target.reason_code)
    if _CREATION_INTENT_RE.search(clean_task):
        return FallthroughToLLM("creation_task")
    if _RISKY_COMMAND_RE.search(clean_task):
        return FallthroughToLLM("risky_command_requested")

    resolved_target = resolved or resolve_target_from_task(clean_task, root)
    if getattr(resolved_target, "source", "") != "explicit_line":
        return FallthroughToLLM("no_explicit_target")
    target_path = _normalize_repo_path(str(getattr(resolved_target, "path", "") or ""))
    if Path(target_path).suffix.lower() not in {".md", ".markdown"}:
        return FallthroughToLLM("not_markdown_append_target")
    if getattr(resolved_target, "exists", False) is not True:
        return FallthroughToLLM("target_missing")

    literal = markdown_append_literal(clean_task)
    if not literal:
        return FallthroughToLLM("ambiguous_markdown_append_literal")

    target_abs = (root / target_path).resolve()
    if not _is_relative_to(target_abs, root):
        return Block("target_outside_workspace")
    if not target_abs.is_file():
        return FallthroughToLLM("target_missing")

    target_content = target_abs.read_text(encoding="utf-8", errors="replace")
    target_hash = _sha256_bytes(target_abs.read_bytes())
    context_mode = derive_context_mode(target_path)
    plan = ArchitectPlan(
        plan_id=f"det-md-append-{uuid4().hex}",
        task_id=task_id,
        schema_version=PLAN_SCHEMA_VERSION,
        created_at=_now_iso(),
        source_task=clean_task,
        bundle_snapshot=BundleSnapshot(
            bundle_path="deterministic:markdown_append",
            bundle_sha256="",
            workspace_root=str(root),
            generated_at=_now_iso(),
        ),
        classification=TaskClassification(
            task_class="implement",
            visual_change=False,
            designer_required=False,
            estimated_complexity="small",
        ),
        coder_packet=CoderPacket(
            target_file=TargetFile(
                path=target_path,
                exists=True,
                sha256_before=target_hash,
            ),
            operation="edit",
            acceptance_criteria=[
                AcceptanceCriterion(
                    id="target-file",
                    description=f"Modify only {target_path}.",
                    kind="behavioral",
                ),
                AcceptanceCriterion(
                    id="literal-append",
                    description=f'Output must contain the appended literal sentence: "{literal}".',
                    kind="literal",
                ),
            ],
            constraints=ContentConstraints(
                must_contain=[literal],
                must_not_contain=["Target file:"],
                preserve_imports=[],
                preserve_exports=[],
                max_added_lines=4,
                max_removed_lines=0,
            ),
            context_slices=[_context_slice(target_path, "target", target_content)],
            forbidden_paths=list(forbidden_paths_for_context_mode(context_mode)),
            style_directives=[
                "Plan source: deterministic small Markdown append fallback.",
                "Append only the requested literal sentence to the target Markdown file.",
            ],
        ),
        verification_plan=VerificationPlan(
            required_checks=[
                VerificationCheck(
                    id="git_apply_check",
                    command=["git", "apply", "--check"],
                    blocking=True,
                    timeout_seconds=3,
                )
            ],
            designer_review_required=False,
            architect_review_required=False,
        ),
        budget=PlanBudget(
            max_coder_attempts=1,
            max_total_seconds=30,
            cloud_escalation_allowed=False,
        ),
    )
    return Plan(plan)


def plan_task_with_llm(
    task: str,
    task_id: str,
    workspace_root: Path,
    *,
    llm_call: Callable[[str, str], str] | None = None,
    rejection_feedback: list[dict[str, Any]] | None = None,
) -> ArchitectPlan:
    root = workspace_root.resolve()
    clean_task = (task or "").strip()
    file_index = _workspace_file_index(root)
    alias = _architect_model_alias()
    if llm_call is None:
        _raise_if_model_alias_unavailable(alias)

    prompt = _architect_prompt(clean_task, file_index, rejection_feedback=rejection_feedback)
    last_error = ""
    last_reason_code = "architect_llm_invalid_json"
    for attempt in range(2):
        try:
            raw_response = (
                llm_call(prompt, alias)
                if llm_call is not None
                else _call_architect_llm(prompt, model_alias=alias)
            )
            payload = _parse_json_object(raw_response)
            return _architect_plan_from_llm_payload(
                payload,
                task_id=task_id,
                task=clean_task,
                workspace_root=root,
            )
        except Exception as error:
            if _is_timeout_error(error):
                raise ArchitectLLMError(
                    "architect_llm_timeout",
                    f"LLM Architect timed out after {_architect_timeout_seconds()} seconds.",
                ) from error
            last_error = str(error)
            if isinstance(error, ArchitectLLMError):
                last_reason_code = error.reason_code
            prompt = (
                f"{prompt}\n\nYour previous response was invalid: {last_error}\n"
                "Retry with one valid JSON object only."
            )
    raise ArchitectLLMError(last_reason_code, f"LLM Architect response did not validate after retry: {last_error}")


def _architect_plan_from_llm_payload(
    payload: dict[str, Any],
    *,
    task_id: str,
    task: str,
    workspace_root: Path,
) -> ArchitectPlan:
    if payload.get("status") == "blocked":
        reason = str(payload.get("reason_code") or payload.get("reason") or "task_too_vague_for_plan")
        raise ArchitectLLMError(reason, reason)

    classification_payload = _require_payload_dict(payload, "classification")
    packet_payload = dict(_require_payload_dict(payload, "coder_packet"))
    target_payload = dict(_require_payload_dict(packet_payload, "target_file"))
    raw_target = str(target_payload.get("path") or "").strip()
    target_path = _normalize_repo_path(raw_target)
    if not target_path:
        raise ArchitectLLMError("architect_target_missing", "LLM Architect did not choose a target file.")
    target_abs = (workspace_root / target_path).resolve()
    if not _is_relative_to(target_abs, workspace_root):
        raise ArchitectLLMError(
            "architect_target_outside_workspace",
            f"LLM Architect chose path outside workspace: {target_path}",
        )

    operation = str(packet_payload.get("operation") or "").strip()
    if operation not in {"edit", "create", "delete"}:
        raise ArchitectLLMError("architect_invalid_operation", "operation must be edit, create, or delete.")
    target_exists = target_abs.is_file()
    if operation == "edit" and not target_exists:
        raise ArchitectLLMError(
            "architect_target_missing",
            f"LLM Architect chose missing edit target: {target_path}",
        )
    if operation == "create" and target_exists:
        operation = "edit"

    target_content = (
        target_abs.read_text(encoding="utf-8", errors="replace")
        if target_exists
        else ""
    )
    target_hash = _sha256_bytes(target_abs.read_bytes()) if target_exists else None
    packet_payload["operation"] = operation
    packet_payload["target_file"] = {
        "path": target_path,
        "exists": target_exists,
        "sha256_before": target_hash,
    }
    packet_payload["context_slices"] = (
        [
            _context_slice(target_path, "target", target_content),
            *_import_context_slices(workspace_root, target_path, target_content),
        ]
        if target_exists
        else []
    )
    context_mode = derive_context_mode(target_path)
    packet_payload["forbidden_paths"] = list(forbidden_paths_for_context_mode(context_mode))
    packet_payload["style_directives"] = _coerce_str_list(
        packet_payload.get("style_directives"),
        default=_style_directives(target_path),
    )[:6]
    packet_payload["acceptance_criteria"] = _coerce_acceptance_criteria(
        packet_payload.get("acceptance_criteria"),
        task,
        target_path,
    )
    packet_payload["constraints"] = _coerce_constraints(
        packet_payload.get("constraints"),
        task,
        target_content,
        operation=operation,
    )

    classification = _coerce_classification(classification_payload, task, target_path)
    packet = CoderPacket(
        target_file=TargetFile(**packet_payload["target_file"]),
        operation=packet_payload["operation"],
        acceptance_criteria=[
            AcceptanceCriterion(**item) for item in packet_payload["acceptance_criteria"]
        ],
        constraints=ContentConstraints(**packet_payload["constraints"]),
        context_slices=packet_payload["context_slices"],
        forbidden_paths=packet_payload["forbidden_paths"],
        style_directives=packet_payload["style_directives"],
    )

    return ArchitectPlan(
        plan_id=uuid4().hex,
        task_id=task_id,
        schema_version=PLAN_SCHEMA_VERSION,
        created_at=_now_iso(),
        source_task=task,
        bundle_snapshot=_bundle_snapshot(workspace_root),
        classification=classification,
        coder_packet=packet,
        verification_plan=_verification_plan(target_path),
        budget=PlanBudget(
            max_coder_attempts=3,
            max_total_seconds=120,
            cloud_escalation_allowed=True,
        ),
    )


def _architect_prompt(
    task: str,
    file_index: list[str],
    *,
    rejection_feedback: list[dict[str, Any]] | None = None,
) -> str:
    file_index_text = "\n".join(f"- {path}" for path in file_index[:400])
    rejection_text = _render_rejection_feedback(rejection_feedback or [])
    return f"""You are the SpiritOS Architect.
Your job is to choose one concrete target file and produce strict planning JSON.

Task:
{task}

Workspace file index (paths only):
{file_index_text or "- No file index available"}

Previous attempts and why they were rejected:
{rejection_text}

Return exactly one JSON object. Do not include markdown fences, prose, comments, or text outside JSON.

Required JSON shape:
{{
  "classification": {{
    "task_class": "implement" | "refactor" | "fix" | "style" | "explain",
    "visual_change": true | false,
    "designer_required": false,
    "estimated_complexity": "trivial" | "small" | "medium" | "large"
  }},
  "coder_packet": {{
    "target_file": {{"path": "repo/relative/path.tsx", "exists": true | false, "sha256_before": null}},
    "operation": "edit" | "create" | "delete",
    "acceptance_criteria": [
      {{"id": "short-slug", "description": "specific expected outcome", "kind": "literal" | "behavioral"}}
    ],
    "constraints": {{
      "must_contain": [],
      "must_not_contain": ["Target file:"],
      "preserve_imports": [],
      "preserve_exports": [],
      "max_added_lines": 120,
      "max_removed_lines": 80
    }},
    "context_slices": [],
    "forbidden_paths": [],
    "style_directives": ["Keep the diff focused on the selected target file."]
  }}
}}

Rules:
- Pick an existing file from the file index for vague edit/style/fix/refactor tasks.
- Use operation "create" only when the user explicitly asks for a new file/page/component.
- If the task is too vague to choose a real target, return {{"status":"blocked","reason_code":"task_too_vague_for_plan"}}.
- If previous attempts were rejected, adjust the target, approach, or constraints according to that feedback.
- Do not invent file contents. Leave context_slices empty; the Python wrapper fills them.
- Include exact quoted strings from the task in must_contain and as literal criteria.
- Keep target_file.path repo-relative with forward slashes.
"""


def _render_rejection_feedback(rejections: list[dict[str, Any]]) -> str:
    if not rejections:
        return "- none"
    lines: list[str] = []
    for item in rejections[-5:]:
        reason = str(item.get("reason_code") or "other")
        target = str(item.get("target") or "unknown target")
        plan_id = str(item.get("plan_id") or "unknown plan")
        details = str(item.get("details") or "").strip()
        suffix = f"; details: {details}" if details else ""
        lines.append(f"- plan {plan_id}, target {target}, rejected for {reason}{suffix}")
    return "\n".join(lines)


def _workspace_file_index(root: Path) -> list[str]:
    for name in REPOMIX_BUNDLE_NAMES:
        candidate = root / name
        if not candidate.is_file():
            continue
        try:
            text = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        paths = _dedupe(_FILE_PATH_IN_REPOMIX_RE.findall(text))
        if paths:
            return sorted(paths)

    paths: list[str] = []
    for child in root.rglob("*"):
        if len(paths) >= 400:
            break
        if not child.is_file():
            continue
        try:
            rel = child.relative_to(root).as_posix()
        except ValueError:
            continue
        if _file_index_path_allowed(rel):
            paths.append(rel)
    return sorted(paths)


def _file_index_path_allowed(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized.startswith((".git/", ".next/", "node_modules/", "data/")):
        return False
    return Path(normalized).suffix.lower() in {
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".py",
        ".css",
        ".md",
        ".json",
    }


def _bundle_snapshot(root: Path) -> BundleSnapshot:
    for name in REPOMIX_BUNDLE_NAMES:
        candidate = root / name
        if candidate.is_file():
            return BundleSnapshot(
                bundle_path=str(candidate),
                bundle_sha256=_sha256_bytes(candidate.read_bytes()),
                workspace_root=str(root),
                generated_at=_now_iso(),
            )
    return BundleSnapshot(
        bundle_path="",
        bundle_sha256="",
        workspace_root=str(root),
        generated_at=_now_iso(),
    )


def _classify_task(task: str, target_path: str) -> TaskClassification:
    suffix = Path(target_path).suffix.lower()
    visual_change = suffix in {".tsx", ".jsx", ".css"} or bool(_STYLE_RE.search(task))
    task_class = "implement"
    if _EXPLAIN_RE.search(task):
        task_class = "explain"
    elif _REFACTOR_RE.search(task):
        task_class = "refactor"
    elif _FIX_RE.search(task):
        task_class = "fix"
    elif _STYLE_RE.search(task):
        task_class = "style"

    criterion_count = len(_literal_requirements(task)) + len(_class_fragments(task))
    complexity = "trivial" if len(task) < 140 and criterion_count <= 2 else "small"
    if task_class == "refactor" or criterion_count > 5:
        complexity = "medium"

    return TaskClassification(
        task_class=task_class,  # type: ignore[arg-type]
        visual_change=visual_change,
        designer_required=False,
        estimated_complexity=complexity,  # type: ignore[arg-type]
    )


def _acceptance_criteria(task: str, target_path: str) -> list[AcceptanceCriterion]:
    criteria = [
        AcceptanceCriterion(
            id="target-file",
            description=f"Modify only {target_path}.",
            kind="behavioral",
        )
    ]
    for index, literal in enumerate(_literal_requirements(task), start=1):
        criteria.append(
            AcceptanceCriterion(
                id=f"literal-{index}",
                description=f'Output must contain "{literal}".',
                kind="literal",
            )
        )
    for index, fragment in enumerate(_class_fragments(task), start=1):
        criteria.append(
            AcceptanceCriterion(
                id=f"class-fragment-{index}",
                description=f"Output must contain class fragment {fragment}.",
                kind="literal",
            )
        )
    for index, route in enumerate(_route_requirements(task), start=1):
        criteria.append(
            AcceptanceCriterion(
                id=f"route-{index}",
                description=f"Preserve behavior for route {route}.",
                kind="behavioral",
            )
        )
    return criteria


def _content_constraints(task: str, existing_content: str) -> ContentConstraints:
    must_contain = _dedupe([*_literal_requirements(task), *_class_fragments(task)])
    preserve_exports = _dedupe(_EXPORT_NAME_RE.findall(existing_content))
    if "export default" in existing_content and "default" not in preserve_exports:
        preserve_exports.insert(0, "default")
    preserve_imports = _dedupe(_import_module_names(existing_content))
    return ContentConstraints(
        must_contain=must_contain,
        must_not_contain=["Target file:"],
        preserve_imports=preserve_imports,
        preserve_exports=preserve_exports,
        max_added_lines=80,
        max_removed_lines=60,
    )


def _verification_plan(target_path: str) -> VerificationPlan:
    suffix = Path(target_path).suffix.lower()
    checks = [
        VerificationCheck(
            id="git_apply_check",
            command=["git", "apply", "--check"],
            blocking=True,
            timeout_seconds=3,
        )
    ]
    if suffix in {".ts", ".tsx", ".js", ".jsx"}:
        checks.extend(
            [
                VerificationCheck(
                    id="eslint",
                    command=["npx", "eslint", target_path],
                    blocking=False,
                    timeout_seconds=10,
                ),
                VerificationCheck(
                    id="typecheck",
                    command=["npx", "tsc", "--noEmit", "-p", "tsconfig.json"],
                    blocking=False,
                    timeout_seconds=30,
                ),
            ]
        )
    elif suffix == ".py":
        checks.append(
            VerificationCheck(
                id="python_compile",
                command=["python3", "-m", "py_compile", target_path],
                blocking=True,
                timeout_seconds=5,
            )
        )
    return VerificationPlan(
        required_checks=checks,
        designer_review_required=False,
        architect_review_required=False,
    )


def _style_directives(target_path: str) -> list[str]:
    suffix = Path(target_path).suffix.lower()
    directives = ["Keep the diff focused on the requested target file."]
    if suffix in {".tsx", ".jsx"}:
        directives.extend(
            [
                "Follow existing component patterns in the target file.",
                "Prefer existing styling conventions and Tailwind utilities when present.",
            ]
        )
    elif suffix == ".py":
        directives.append("Preserve existing Python module structure and public API.")
    return directives[:6]


def _coerce_classification(
    payload: dict[str, Any],
    task: str,
    target_path: str,
) -> TaskClassification:
    fallback = _classify_task(task, target_path)
    task_class = payload.get("task_class")
    if task_class not in {"implement", "refactor", "fix", "style", "explain"}:
        task_class = fallback.task_class
    complexity = payload.get("estimated_complexity")
    if complexity not in {"trivial", "small", "medium", "large"}:
        complexity = fallback.estimated_complexity
    return TaskClassification(
        task_class=task_class,  # type: ignore[arg-type]
        visual_change=(
            payload.get("visual_change")
            if isinstance(payload.get("visual_change"), bool)
            else fallback.visual_change
        ),
        designer_required=(
            payload.get("designer_required")
            if isinstance(payload.get("designer_required"), bool)
            else False
        ),
        estimated_complexity=complexity,  # type: ignore[arg-type]
    )


def _coerce_acceptance_criteria(
    value: Any,
    task: str,
    target_path: str,
) -> list[dict[str, str]]:
    criteria: list[dict[str, str]] = []
    if isinstance(value, list):
        for index, item in enumerate(value, start=1):
            if not isinstance(item, dict):
                continue
            description = str(item.get("description") or "").strip()
            if not description:
                continue
            raw_kind = str(item.get("kind") or "behavioral").strip()
            criteria.append(
                {
                    "id": _slug(str(item.get("id") or f"criterion-{index}")),
                    "description": description,
                    "kind": raw_kind if raw_kind in {"literal", "behavioral"} else "behavioral",
                }
            )
    if not criteria:
        criteria = [
            {
                "id": criterion.id,
                "description": criterion.description,
                "kind": criterion.kind,
            }
            for criterion in _acceptance_criteria(task, target_path)
        ]
    return criteria


def _coerce_constraints(
    value: Any,
    task: str,
    existing_content: str,
    *,
    operation: str,
) -> dict[str, Any]:
    fallback = _content_constraints(task, existing_content)
    payload = value if isinstance(value, dict) else {}
    return {
        "must_contain": _dedupe(
            [
                *_coerce_str_list(payload.get("must_contain")),
                *_literal_requirements(task),
            ]
        ),
        "must_not_contain": _dedupe(
            [*_coerce_str_list(payload.get("must_not_contain")), "Target file:"]
        ),
        "preserve_imports": _coerce_str_list(
            payload.get("preserve_imports"),
            default=fallback.preserve_imports,
        ),
        "preserve_exports": _coerce_str_list(
            payload.get("preserve_exports"),
            default=fallback.preserve_exports,
        ),
        "max_added_lines": _optional_positive_int(
            payload.get("max_added_lines"),
            200 if operation == "create" else fallback.max_added_lines,
        ),
        "max_removed_lines": _optional_positive_int(
            payload.get("max_removed_lines"),
            0 if operation == "create" else fallback.max_removed_lines,
        ),
    }


def _context_slice(
    rel_path: str,
    kind: Literal["target", "import"],
    content: str,
) -> ContextSlice:
    line_count = max(1, content.count("\n") + (0 if content.endswith("\n") else 1))
    return ContextSlice(
        path=rel_path,
        kind=kind,
        sha256=_sha256_text(content),
        content=content,
        line_range=(1, line_count),
    )


def _import_context_slices(root: Path, target_path: str, content: str) -> list[ContextSlice]:
    slices: list[ContextSlice] = []
    for module_path in _import_module_names(content):
        if not module_path.startswith("."):
            continue
        imported = _resolve_relative_import(root, target_path, module_path)
        if imported is None:
            continue
        rel = imported.relative_to(root).as_posix()
        imported_content = imported.read_text(encoding="utf-8", errors="replace")
        slices.append(_context_slice(rel, "import", imported_content))
        if len(slices) >= 5:
            break
    return slices


def _resolve_relative_import(root: Path, target_path: str, module_path: str) -> Path | None:
    base = (root / target_path).parent
    raw = (base / module_path).resolve()
    candidates = [
        raw,
        *(Path(f"{raw}{suffix}") for suffix in (".ts", ".tsx", ".js", ".jsx", ".css")),
        *(raw / f"index{suffix}" for suffix in (".ts", ".tsx", ".js", ".jsx")),
    ]
    for candidate in candidates:
        if _is_relative_to(candidate, root) and candidate.is_file():
            return candidate
    return None


def _literal_requirements(task: str) -> list[str]:
    without_target_lines = "\n".join(
        line
        for line in task.splitlines()
        if not line.strip().lower().startswith("target file:")
    )
    return _dedupe(
        match.group(2).strip()
        for match in re.finditer(r"([\"'`])(.+?)\1", without_target_lines)
        if match.group(2).strip()
    )


def _quoted_spans(text: str) -> list[tuple[int, int]]:
    return [match.span() for match in re.finditer(r"([\"'`]).+?\1", text)]


def _without_quoted_text(text: str) -> str:
    chars = list(text)
    for start, end in _quoted_spans(text):
        chars[start:end] = " " * (end - start)
    return "".join(chars)


def _class_utility_like(value: str) -> bool:
    if not _CLASS_FRAGMENT_RE.fullmatch(value):
        return False
    base = value.split(":", 1)[-1]
    prefix = base.split("-", 1)[0]
    return prefix in _CLASS_UTILITY_PREFIXES


def markdown_append_literal(task: str) -> str:
    normalized = (task or "").strip()
    if len(normalized) > 500 or not re.search(r"\bappend\b", normalized, re.IGNORECASE):
        return ""
    without_target_lines = "\n".join(
        line
        for line in normalized.splitlines()
        if not line.strip().lower().startswith("target file:")
    )
    literals = _dedupe(
        match.group(2).strip()
        for match in re.finditer(r"([\"'`])(.+?)\1", without_target_lines)
        if match.group(2).strip()
    )
    if len(literals) != 1:
        return ""
    literal = literals[0]
    if "\n" in literal or len(literal) > 240:
        return ""
    return literal


def _class_fragments(task: str) -> list[str]:
    searchable = _without_quoted_text(task)
    fragments = []
    for match in _CLASS_FRAGMENT_RE.finditer(searchable):
        value = match.group(0).strip().strip("`'\".;:")
        if "/" in value or "." in value or value.lower().startswith("target"):
            continue
        if not _class_utility_like(value):
            continue
        fragments.append(value)
    for match in _CODE_IDENTIFIER_RE.finditer(searchable):
        value = match.group(0).strip().strip("`'\".;:")
        if value.lower() in _FRAGMENT_META_WORDS or value.lower().startswith("target"):
            continue
        if _path_like_code_fragment(value):
            continue
        fragments.append(value)
    return _dedupe(fragments)


def _path_like_code_fragment(value: str) -> bool:
    lowered = value.strip("`'\".;:").lower()
    return any(lowered.endswith(suffix) for suffix in _CODE_FRAGMENT_PATH_SUFFIXES)


def _route_requirements(task: str) -> list[str]:
    routes = []
    for match in _ROUTE_RE.finditer(task):
        route = match.group(1).rstrip(".,;:")
        if route and "." not in Path(route).name:
            routes.append(route)
    return _dedupe(routes)


def _import_module_names(content: str) -> list[str]:
    return _dedupe(match.group(1) for match in _IMPORT_RE.finditer(content))


def _parse_json_object(raw_response: str) -> dict[str, Any]:
    raw = (raw_response or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ArchitectLLMError("architect_llm_invalid_json", "response did not contain a JSON object")
    parsed = json.loads(raw[start : end + 1])
    if not isinstance(parsed, dict):
        raise ArchitectLLMError("architect_llm_invalid_json", "response JSON must be an object")
    return parsed


def _require_payload_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ArchitectLLMError("architect_llm_invalid_json", f"{key} must be an object")
    return value


def _coerce_str_list(value: Any, default: list[str] | None = None) -> list[str]:
    if isinstance(value, list):
        return _dedupe(item for item in value if isinstance(item, str))
    return list(default or [])


def _optional_positive_int(value: Any, default: int | None) -> int | None:
    if value is None:
        return default
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return default


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug[:48] or "criterion"


def _normalize_repo_path(path: str) -> str:
    return normalize_repo_path_candidate(path)


def _architect_model_alias() -> str:
    configured = (
        os.getenv("SOURCE_PROXY_ARCHITECT_MODEL_ALIAS", "").strip()
        or os.getenv("SOURCE_PROXY_CODER_MODEL_ALIAS", "").strip()
        or "local"
    )
    enabled = available_model_aliases()
    if configured in enabled:
        return configured
    if "local" in enabled:
        return "local"
    return configured


def _raise_if_model_alias_unavailable(alias: str) -> None:
    enabled = available_model_aliases()
    if alias not in enabled:
        available = ", ".join(sorted(enabled)) or "none"
        raise ArchitectLLMError(
            "architect_model_not_configured",
            f"{alias!r} is not an available model alias. Available aliases: {available}.",
        )


def _call_architect_llm(prompt: str, *, model_alias: str) -> str:
    completion = get_router().completion(
        model=model_alias,
        messages=[{"role": "system", "content": prompt}],
        stream=False,
        temperature=0,
        timeout=_architect_timeout_seconds(),
    )
    payload = completion.model_dump() if hasattr(completion, "model_dump") else dict(completion)
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        return content if isinstance(content, str) else ""
    text = first.get("text")
    return text if isinstance(text, str) else ""


def _architect_timeout_seconds() -> float:
    raw_value = os.getenv("SOURCE_PROXY_ARCHITECT_TIMEOUT_SECONDS", "20")
    try:
        timeout = float(raw_value)
    except ValueError as error:
        raise ValueError(
            f"SOURCE_PROXY_ARCHITECT_TIMEOUT_SECONDS must be numeric, got {raw_value!r}."
        ) from error
    if timeout <= 0:
        raise ValueError("SOURCE_PROXY_ARCHITECT_TIMEOUT_SECONDS must be greater than 0.")
    return timeout


def _is_timeout_error(error: Exception) -> bool:
    name = type(error).__name__.lower()
    message = str(error).lower()
    return "timeout" in name or "timed out" in message or "timeout" in message


def _dedupe(values) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
