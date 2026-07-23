from __future__ import annotations

import ast
import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Literal
from uuid import uuid4

from source_proxy.decision.proposal_task import (
    BoundedProposal,
    bounded_proposal_create_allowed,
    effective_planning_task_text,
    merge_proposal_forbidden_paths,
    parse_bounded_proposal_task,
)
from source_proxy.decision.router import (
    ResolvedTarget,
    resolve_target_from_task,
    unsafe_target_for_route,
)
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
from source_proxy.approval.external_gate import ExternalGateError, central_gate_check
from source_proxy.safety.paths import normalize_repo_path_candidate, unsafe_target_finding
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
_PYTHON_RELATIVE_IMPORT_RE = re.compile(
    r"^\s*from\s+(\.+[A-Za-z_][A-Za-z0-9_.]*)\s+import\s+",
    re.MULTILINE,
)
_EXPORT_DECLARATION_RE = re.compile(
    r"\bexport\s+(?:(?P<default>default)\s+)?"
    r"(?:(?:declare|abstract|async)\s+)*"
    r"(?:function|class|const|let|var|interface|type|enum|namespace|module)\s+"
    r"(?P<name>[A-Za-z_$][\w$]*)"
)
_CLASS_FRAGMENT_RE = re.compile(
    r"\b(?:[a-z]+:)*[a-z][a-z0-9-]*(?:-\[[^\]\s]+\]|-[a-z0-9./]+)+\b",
    re.IGNORECASE,
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
_ROUTE_RE = re.compile(r"(?<![A-Za-z0-9_./@<-])(/[A-Za-z0-9_()/.-]+)")
_FILE_PATH_IN_REPOMIX_RE = re.compile(r'<file\s+path="([^"]+)"')
_RISKY_COMMAND_RE = re.compile(
    r"\b(run|execute|shell|terminal|command|script|npm|python|pytest|curl|powershell|bash)\b",
    re.IGNORECASE,
)
_QUOTED_CODE_TOKEN_RE = re.compile(
    r"`([A-Za-z_][A-Za-z0-9_]*|/[A-Za-z0-9_(){}./-]+)`"
)
_DECLARATION_PREFIXES = (
    "async def",
    "def",
    "class",
    "function",
    "const",
    "let",
    "var",
    "func",
    "fn",
)
_PRIMARY_SOURCE_SUFFIXES = {
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".py",
    ".rs",
    ".ts",
    ".tsx",
}
_QUOTED_PATH_SUFFIXES = _PRIMARY_SOURCE_SUFFIXES | {
    ".cfg",
    ".conf",
    ".config",
    ".css",
    ".env",
    ".go",
    ".ini",
    ".java",
    ".json",
    ".md",
    ".mdx",
    ".rs",
    ".toml",
    ".yaml",
    ".yml",
}
_MAX_TARGET_DISCOVERY_BYTES = 256_000
_MAX_TARGET_DISCOVERY_FILES = 400
_TARGET_DISCOVERY_IGNORED_DIRS = {
    ".git",
    ".next",
    ".pytest_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "data",
    "dist",
    "node_modules",
    "venv",
}


class ArchitectLLMError(ValueError):
    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


BOUNDED_CREATE_REFERENCE_PAGE = "src/app/coding/page.tsx"


def plan_bounded_proposal_create_deterministically(
    task: str,
    task_id: str,
    workspace_root: Path,
    *,
    proposal: BoundedProposal | None = None,
    allowed_paths: tuple[str, ...] | None = None,
    readable_paths: tuple[str, ...] | None = None,
) -> Plan | FallthroughToLLM | Block:
    root = workspace_root.resolve()
    bounded = proposal or parse_bounded_proposal_task(task)
    if bounded is None:
        return FallthroughToLLM("no_bounded_proposal")
    create_ok, blocked_reason = bounded_proposal_create_allowed(bounded, workspace_root=root)
    if not create_ok:
        if blocked_reason in {"protected_path", "secret_path", "path_escape", "outside_workspace"}:
            return Block(blocked_reason)
        if blocked_reason != "target_already_exists":
            return FallthroughToLLM(blocked_reason or "bounded_create_not_allowed")

    target_path = normalize_repo_path_candidate(bounded.target_file)
    if allowed_paths is not None and not _resolved_path_allowed_by_scope(
        root,
        target_path,
        allowed_paths,
    ):
        return Block("architect_target_outside_allowed_scope")
    target_abs = (root / target_path).resolve()
    target_exists = target_abs.is_file()
    planning_task = bounded.task or effective_planning_task_text(task)
    context_mode = derive_context_mode(target_path)
    forbidden_paths = merge_proposal_forbidden_paths(
        bounded,
        context_defaults=forbidden_paths_for_context_mode(context_mode),
    )
    context_slices: list[ContextSlice] = []
    if target_exists:
        target_content = target_abs.read_text(encoding="utf-8", errors="replace")
        context_slices.append(_context_slice(target_path, "target", target_content))
    reference_page = root / BOUNDED_CREATE_REFERENCE_PAGE
    context_paths = readable_paths if readable_paths is not None else allowed_paths
    if reference_page.is_file() and (
        context_paths is None
        or _resolved_path_allowed_by_scope(
            root,
            BOUNDED_CREATE_REFERENCE_PAGE,
            context_paths,
        )
    ):
        reference_content = reference_page.read_text(encoding="utf-8", errors="replace")
        context_slices.append(
            _context_slice(BOUNDED_CREATE_REFERENCE_PAGE, "import", reference_content)
        )

    plan = ArchitectPlan(
        plan_id=uuid4().hex,
        task_id=task_id,
        schema_version=PLAN_SCHEMA_VERSION,
        created_at=_now_iso(),
        source_task=task,
        bundle_snapshot=_bundle_snapshot(root),
        classification=_classify_task(planning_task, target_path),
        coder_packet=CoderPacket(
            target_file=TargetFile(
                path=target_path,
                exists=target_exists,
                sha256_before=_sha256_bytes(target_abs.read_bytes()) if target_exists else None,
            ),
            operation="edit" if target_exists else "create",
            acceptance_criteria=[
                AcceptanceCriterion(
                    id="create-target-only",
                    description=(
                        f"Modify only {target_path} as a Next.js app route page."
                        if target_exists
                        else f"Create only {target_path} as a Next.js app route page."
                    ),
                    kind="behavioral",
                ),
            ],
            constraints=ContentConstraints(
                must_contain=[],
                must_not_contain=["Target file:", "Proposal task:"],
                preserve_imports=[],
                preserve_exports=[],
                max_added_lines=120,
                max_removed_lines=120 if target_exists else 0,
            ),
            context_slices=context_slices,
            forbidden_paths=forbidden_paths,
            style_directives=[
                "bounded_proposal_create",
                "deterministic_existing_file_route" if target_exists else "deterministic_new_file_route",
                *_style_directives(target_path),
            ],
        ),
        verification_plan=_verification_plan(target_path),
        budget=PlanBudget(
            max_coder_attempts=3,
            max_total_seconds=450,
            cloud_escalation_allowed=True,
        ),
    )
    return Plan(plan)


def plan_task_deterministically(
    task: str,
    task_id: str,
    workspace_root: Path,
    *,
    allowed_paths: tuple[str, ...] | None = None,
    readable_paths: tuple[str, ...] | None = None,
) -> DeterministicPlanResult:
    clean_task = (task or "").strip()
    root = workspace_root.resolve()
    context_paths = readable_paths if readable_paths is not None else allowed_paths
    planning_text = effective_planning_task_text(clean_task)
    bounded_create = plan_bounded_proposal_create_deterministically(
        task,
        task_id,
        root,
        allowed_paths=allowed_paths,
        readable_paths=context_paths,
    )
    if isinstance(bounded_create, (Plan, Block)):
        return bounded_create
    if len(planning_text) > 500:
        return FallthroughToLLM("task_too_long")

    resolved, inferred_target_ambiguity = _resolve_writable_task_target(
        clean_task,
        root,
        allowed_paths=allowed_paths,
    )
    if not resolved.path and not inferred_target_ambiguity:
        inferred_target = _resolve_ordinary_workspace_target(
            planning_text,
            root,
            allowed_paths=allowed_paths,
        )
        if inferred_target:
            resolved = ResolvedTarget(
                path=inferred_target,
                exists=True,
                source="inferred",
            )
    if inferred_target_ambiguity:
        return FallthroughToLLM(inferred_target_ambiguity)
    unsafe_target = unsafe_target_for_route(clean_task, resolved, root)
    if unsafe_target is not None:
        return Block(unsafe_target.reason_code)
    if _CREATION_INTENT_RE.search(planning_text):
        return FallthroughToLLM("creation_task")
    markdown_append = plan_markdown_append_deterministically(
        clean_task,
        task_id,
        root,
        resolved=resolved,
        proposal=parse_bounded_proposal_task(clean_task),
        allowed_paths=allowed_paths,
    )
    if isinstance(markdown_append, (Plan, Block)):
        return markdown_append
    if not resolved.path:
        return FallthroughToLLM("no_explicit_target")
    if allowed_paths is not None and not _resolved_path_allowed_by_scope(
        root,
        resolved.path,
        allowed_paths,
    ):
        return Block("architect_target_outside_allowed_scope")

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
        *_import_context_slices(
            root,
            resolved.path,
            target_content,
            allowed_paths=context_paths,
        ),
    ]

    plan = ArchitectPlan(
        plan_id=uuid4().hex,
        task_id=task_id,
        schema_version=PLAN_SCHEMA_VERSION,
        created_at=_now_iso(),
        source_task=clean_task,
        bundle_snapshot=_bundle_snapshot(root),
        classification=_classify_task(planning_text, resolved.path),
        coder_packet=CoderPacket(
            target_file=TargetFile(
                path=resolved.path,
                exists=True,
                sha256_before=target_hash,
            ),
            operation="edit",
            acceptance_criteria=_acceptance_criteria(planning_text, resolved.path),
            constraints=_content_constraints(
                planning_text,
                target_content,
                resolved.path,
            ),
            context_slices=context_slices,
            forbidden_paths=forbidden_paths,
            style_directives=_style_directives(resolved.path),
        ),
        verification_plan=_verification_plan(resolved.path),
        budget=PlanBudget(
            max_coder_attempts=3,
            max_total_seconds=450,
            cloud_escalation_allowed=True,
        ),
    )
    return Plan(plan)


def _resolve_ordinary_workspace_target(
    task: str,
    root: Path,
    *,
    allowed_paths: tuple[str, ...] | None,
) -> str:
    """Resolve a unique ordinary-code target from repository evidence.

    Human backend requests commonly name a function, setting, or route rather
    than a file.  A local model adds no value when one writable source file
    uniquely contains or declares that exact request token.  This search is
    bounded, repository-only, and deliberately contains no fixture names,
    benchmark IDs, or answer data. Ambiguity still falls through to the
    Architect model.
    """

    candidates, scan_complete = _ordinary_source_candidates(
        root,
        allowed_paths=allowed_paths,
    )
    if not scan_complete:
        return ""
    if not candidates:
        return ""

    tokens = _ordinary_target_tokens(task)
    contents: dict[str, str] = {}
    for path in candidates:
        target = root / path
        try:
            if target.stat().st_size > _MAX_TARGET_DISCOVERY_BYTES:
                return ""
            contents[path] = target.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    route_tokens = tuple(token for token in tokens if token.startswith("/"))
    route_matches = {
        path
        for path, content in contents.items()
        if any(
            _ordinary_code_literal_present(path, content, token)
            for token in route_tokens
        )
    }
    if len(route_matches) == 1:
        route_target = next(iter(route_matches))
    elif route_matches:
        return ""
    else:
        route_target = ""

    identifier_tokens = tuple(token for token in tokens if not token.startswith("/"))
    if not identifier_tokens:
        return route_target

    primary_token = identifier_tokens[0]
    primary_declarations = {
        path
        for path, content in contents.items()
        if _ordinary_target_declared(path, content, primary_token)
    }
    if route_target:
        if primary_declarations and primary_declarations != {route_target}:
            return ""
        if primary_declarations == {route_target}:
            return route_target
    elif len(primary_declarations) == 1:
        return next(iter(primary_declarations))
    elif primary_declarations:
        return ""

    primary_literals = {
        path
        for path, content in contents.items()
        if _ordinary_code_literal_present(path, content, primary_token)
    }
    if route_target:
        if primary_literals and primary_literals != {route_target}:
            return ""
        return route_target
    if len(primary_literals) == 1:
        return next(iter(primary_literals))
    if primary_literals:
        return ""

    secondary_tokens = identifier_tokens[1:]
    evidence_counts = {
        path: sum(
            1
            for token in secondary_tokens
            if _ordinary_target_declared(path, content, token)
            or _ordinary_code_literal_present(path, content, token)
        )
        for path, content in contents.items()
    }
    best_count = max(evidence_counts.values(), default=0)
    best_paths = sorted(
        path for path, count in evidence_counts.items() if count == best_count
    )
    if best_count > 0 and len(best_paths) == 1:
        return best_paths[0]

    return ""


def _resolve_writable_task_target(
    task: str,
    root: Path,
    *,
    allowed_paths: tuple[str, ...] | None,
) -> tuple[ResolvedTarget, str]:
    """Skip inferred read-only mentions while preserving explicit authority."""

    first = resolve_target_from_task(task, root)
    if first.source == "explicit_line":
        return first, ""

    remaining = task
    skipped_read_only = False
    writable: list[ResolvedTarget] = []
    scan_complete = False
    for _attempt in range(10):
        resolved = resolve_target_from_task(remaining, root)
        if not resolved.path:
            scan_complete = True
            break
        if allowed_paths is None or _resolved_path_allowed_by_scope(
            root,
            resolved.path,
            allowed_paths,
        ):
            writable.append(resolved)
        else:
            skipped_read_only = True
        updated_remaining = remaining.replace(resolved.path, " ")
        if updated_remaining == remaining:
            break
        remaining = updated_remaining
    if not scan_complete:
        return (
            ResolvedTarget(path="", exists=False, source="inferred"),
            "inferred_target_scan_incomplete",
        )
    unique_writable = {item.path: item for item in writable}
    if len(unique_writable) == 1:
        return next(iter(unique_writable.values())), ""
    if len(unique_writable) > 1:
        return (
            ResolvedTarget(path="", exists=False, source="inferred"),
            "multiple_inferred_writable_targets",
        )
    return (
        ResolvedTarget(path="", exists=False, source="inferred"),
        "inferred_target_outside_writable_scope" if skipped_read_only else "",
    )


def _ordinary_source_candidates(
    root: Path,
    *,
    allowed_paths: tuple[str, ...] | None,
) -> tuple[list[str], bool]:
    """Return a complete bounded source-file set or decline deterministic use."""

    candidates: list[str] = []
    scan_errors: list[OSError] = []
    for directory, child_directories, filenames in os.walk(
        root,
        topdown=True,
        onerror=scan_errors.append,
        followlinks=False,
    ):
        directory_path = Path(directory)
        child_directories[:] = sorted(
            name
            for name in child_directories
            if name not in _TARGET_DISCOVERY_IGNORED_DIRS
            and not (directory_path / name).is_symlink()
        )
        for filename in sorted(filenames):
            candidate = directory_path / filename
            try:
                path = candidate.relative_to(root).as_posix()
            except ValueError:
                return [], False
            if (
                candidate.is_symlink()
                or candidate.suffix.lower() not in _PRIMARY_SOURCE_SUFFIXES
                or _test_like_path(path)
            ):
                continue
            if allowed_paths is not None:
                if not _resolved_path_allowed_by_scope(root, path, allowed_paths):
                    continue
            elif unsafe_target_finding(path, workspace_root=root) is not None:
                continue
            candidates.append(path)
            if len(candidates) > _MAX_TARGET_DISCOVERY_FILES:
                return [], False
    if scan_errors:
        return [], False
    return sorted(candidates), True


def _ordinary_target_tokens(task: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for raw in _QUOTED_CODE_TOKEN_RE.findall(task or ""):
        value = str(raw).strip()
        if not value or value.isdigit():
            continue
        if value.startswith("/") or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
            tokens.append(value)
    return tuple(_dedupe(tokens))


def _ordinary_target_declared(path: str, content: str, token: str) -> bool:
    if Path(path).suffix.lower() == ".py":
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return False
        for node in ast.walk(tree):
            if isinstance(node, (ast.AsyncFunctionDef, ast.ClassDef, ast.FunctionDef)):
                if node.name == token:
                    return True
            elif isinstance(node, (ast.Assign, ast.NamedExpr)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(isinstance(target, ast.Name) and target.id == token for target in targets):
                    return True
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name) and node.target.id == token:
                    return True
        return False
    code = _ordinary_non_python_code(content, preserve_strings=False)
    word = re.escape(token)
    return any(
        re.search(
            rf"(?m)^[ \t]*{re.escape(prefix)}\s+{word}\b",
            code,
        )
        is not None
        for prefix in _DECLARATION_PREFIXES
    )


def _ordinary_code_literal_present(path: str, content: str, token: str) -> bool:
    if Path(path).suffix.lower() == ".py":
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return False
        docstrings: set[int] = set()
        for node in ast.walk(tree):
            body = getattr(node, "body", None)
            if not isinstance(body, list) or not body:
                continue
            first = body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                docstrings.add(id(first.value))
        return any(
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value == token
            and id(node) not in docstrings
            for node in ast.walk(tree)
        )

    code = _ordinary_non_python_code(content)
    return (
        re.search(
            rf"(?P<quote>['\"`]){re.escape(token)}(?P=quote)",
            code,
        )
        is not None
    )


def _ordinary_non_python_code(
    content: str,
    *,
    preserve_strings: bool = True,
) -> str:
    """Remove C-style comments while preserving quoted literals and newlines."""

    output: list[str] = []
    index = 0
    quote = ""
    escaped = False
    in_block_comment = False
    in_line_comment = False
    while index < len(content):
        character = content[index]
        following = content[index + 1] if index + 1 < len(content) else ""
        if in_line_comment:
            if character == "\n":
                in_line_comment = False
                output.append(character)
            index += 1
            continue
        if in_block_comment:
            if character == "*" and following == "/":
                in_block_comment = False
                index += 2
                continue
            if character == "\n":
                output.append(character)
            index += 1
            continue
        if quote:
            output.append(
                character if preserve_strings or character == "\n" else " "
            )
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = ""
            index += 1
            continue
        if character in {"'", '"', "`"}:
            quote = character
            output.append(character if preserve_strings else " ")
            index += 1
            continue
        if character == "/" and following == "/":
            in_line_comment = True
            index += 2
            continue
        if character == "/" and following == "*":
            in_block_comment = True
            index += 2
            continue
        output.append(character)
        index += 1
    return "".join(output)


def _test_like_path(path: str) -> bool:
    normalized = "/" + path.replace("\\", "/").lower().strip("/")
    name = Path(path).name.lower()
    stem = Path(path).stem.lower()
    return (
        "/tests/" in normalized
        or "/test/" in normalized
        or "/spec/" in normalized
        or "/specs/" in normalized
        or "/__tests__/" in normalized
        or name.startswith("test_")
        or stem in {"conftest", "spec", "specs", "test", "tests"}
        or "_test." in name
        or ".test." in name
        or ".spec." in name
    )


def plan_markdown_append_deterministically(
    task: str,
    task_id: str,
    workspace_root: Path,
    *,
    resolved: Any | None = None,
    proposal: BoundedProposal | None = None,
    allowed_paths: tuple[str, ...] | None = None,
) -> DeterministicPlanResult:
    """Build the narrow no-LLM plan for tiny explicit Markdown append requests."""
    clean_task = (task or "").strip()
    planning_text = effective_planning_task_text(clean_task)
    root = workspace_root.resolve()
    if not planning_text or len(planning_text) > 500:
        return FallthroughToLLM("task_too_long")
    bounded = proposal or parse_bounded_proposal_task(clean_task)
    resolved_target = resolved or resolve_target_from_task(clean_task, root)
    unsafe_target = unsafe_target_for_route(clean_task, resolved_target, root)
    if unsafe_target is not None:
        return Block(unsafe_target.reason_code)
    if bounded is not None and bounded.allowed_files:
        target_path = _normalize_repo_path(str(getattr(resolved_target, "path", "") or ""))
        if target_path and target_path not in bounded.allowed_files:
            return FallthroughToLLM("target_not_in_allowed_files")
    if _CREATION_INTENT_RE.search(planning_text):
        return FallthroughToLLM("creation_task")
    if _RISKY_COMMAND_RE.search(planning_text):
        return FallthroughToLLM("risky_command_requested")
    if getattr(resolved_target, "source", "") != "explicit_line":
        return FallthroughToLLM("no_explicit_target")
    target_path = _normalize_repo_path(str(getattr(resolved_target, "path", "") or ""))
    if allowed_paths is not None and not _resolved_path_allowed_by_scope(
        root,
        target_path,
        allowed_paths,
    ):
        return Block("architect_target_outside_allowed_scope")
    if Path(target_path).suffix.lower() not in {".md", ".markdown"}:
        return FallthroughToLLM("not_markdown_append_target")
    if getattr(resolved_target, "exists", False) is not True:
        return FallthroughToLLM("target_missing")

    literal = markdown_append_literal(planning_text)
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
    forbidden_paths = list(forbidden_paths_for_context_mode(context_mode))
    if bounded is not None:
        forbidden_paths = merge_proposal_forbidden_paths(
            bounded,
            context_defaults=forbidden_paths,
        )
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
                must_not_contain=["Target file:", "Proposal task:"],
                preserve_imports=[],
                preserve_exports=[],
                max_added_lines=4,
                max_removed_lines=0,
            ),
            context_slices=[_context_slice(target_path, "target", target_content)],
            forbidden_paths=forbidden_paths,
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
            max_total_seconds=450,
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
    allowed_paths: tuple[str, ...] | None = None,
    readable_paths: tuple[str, ...] | None = None,
) -> ArchitectPlan:
    root = workspace_root.resolve()
    clean_task = (task or "").strip()
    file_index = _workspace_file_index(root, allowed_paths=allowed_paths)
    alias = _architect_model_alias()
    if llm_call is None:
        _raise_if_model_alias_unavailable(alias)

    prompt = _architect_prompt(
        effective_planning_task_text(clean_task),
        file_index,
        rejection_feedback=rejection_feedback,
        bounded_proposal=parse_bounded_proposal_task(clean_task),
    )
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
                allowed_paths=allowed_paths,
                readable_paths=(
                    readable_paths if readable_paths is not None else allowed_paths
                ),
            )
        except ExternalGateError as error:
            # A closed or mismatched approval gate is an intentional policy
            # decision, not malformed model output. Do not retry it or hide it
            # behind the generic JSON diagnostic.
            raise ArchitectLLMError(
                f"architect_{error.reason_code}",
                str(error),
            ) from error
        except Exception as error:
            if _is_timeout_error(error):
                raise ArchitectLLMError(
                    "architect_llm_timeout",
                    f"LLM Architect timed out after {_architect_timeout_seconds()} seconds.",
                ) from error
            last_error = str(error)
            if isinstance(error, ArchitectLLMError):
                last_reason_code = error.reason_code
            else:
                last_reason_code = "architect_llm_router_error"
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
    allowed_paths: tuple[str, ...] | None = None,
    readable_paths: tuple[str, ...] | None = None,
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
    if allowed_paths is not None and not _resolved_path_allowed_by_scope(
        workspace_root,
        target_path,
        allowed_paths,
    ):
        raise ArchitectLLMError(
            "architect_target_outside_allowed_scope",
            f"LLM Architect chose path outside the authorized scope: {target_path}",
        )
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
            *_import_context_slices(
                workspace_root,
                target_path,
                target_content,
                allowed_paths=(
                    readable_paths if readable_paths is not None else allowed_paths
                ),
            ),
        ]
        if target_exists
        else []
    )
    context_mode = derive_context_mode(target_path)
    packet_payload["forbidden_paths"] = list(forbidden_paths_for_context_mode(context_mode))
    # Model prose is advisory input, never normative coder authority.
    packet_payload["style_directives"] = _style_directives(target_path)
    planning_text = effective_planning_task_text(task)
    packet_payload["acceptance_criteria"] = _coerce_acceptance_criteria(
        packet_payload.get("acceptance_criteria"),
        planning_text,
        target_path,
    )
    packet_payload["constraints"] = _coerce_constraints(
        packet_payload.get("constraints"),
        planning_text,
        target_content,
        target_path,
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
            max_total_seconds=450,
            cloud_escalation_allowed=True,
        ),
    )


def _architect_prompt(
    task: str,
    file_index: list[str],
    *,
    rejection_feedback: list[dict[str, Any]] | None = None,
    bounded_proposal: BoundedProposal | None = None,
) -> str:
    file_index_text = "\n".join(f"- {path}" for path in file_index[:400])
    rejection_text = _render_rejection_feedback(rejection_feedback or [])
    bounded_block = ""
    if bounded_proposal is not None:
        bounded_block = "\n".join(
            [
                "",
                "Bounded proposal metadata (safety only — do not require these keys in file content):",
                f"- target_file: {bounded_proposal.target_file}",
                f"- allowed_files: {', '.join(bounded_proposal.allowed_files) or 'none'}",
                f"- forbidden_files: {', '.join(bounded_proposal.forbidden_files) or 'none'}",
                f"- expected_checks (verification commands, not output text): {', '.join(bounded_proposal.expected_checks) or 'none'}",
            ]
        )
    return f"""You are the SpiritOS Architect.
Your job is to choose one concrete target file and produce strict planning JSON.

Task:
{task}
{bounded_block}

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
    "acceptance_criteria": [],
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
    "style_directives": []
  }}
}}

Rules:
- Pick an existing file from the file index for vague edit/style/fix/refactor tasks.
- Use operation "create" only when the user explicitly asks for a new file/page/component.
- If the task is too vague to choose a real target, return {{"status":"blocked","reason_code":"task_too_vague_for_plan"}}.
- If previous attempts were rejected, adjust the target, approach, or constraints according to that feedback.
- Do not invent file contents. Leave context_slices empty; the Python wrapper fills them.
- Leave acceptance_criteria and style_directives empty. The Python wrapper derives
  all normative criteria, constraints, and style guidance from the public task.
- Never treat JSON field names (allowed_files, forbidden_files, expected_checks) as required output text.
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


def _workspace_file_index(
    root: Path,
    *,
    allowed_paths: tuple[str, ...] | None = None,
) -> list[str]:
    for name in REPOMIX_BUNDLE_NAMES:
        candidate = root / name
        if not candidate.is_file():
            continue
        try:
            text = candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        paths = [
            path
            for path in _dedupe(_FILE_PATH_IN_REPOMIX_RE.findall(text))
            if _file_index_path_allowed(path)
            and unsafe_target_finding(path, workspace_root=root) is None
            and (allowed_paths is None or _path_allowed_by_scope(path, allowed_paths))
        ]
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
        if _file_index_path_allowed(rel) and unsafe_target_finding(
            rel,
            workspace_root=root,
        ) is None and (
            allowed_paths is None or _path_allowed_by_scope(rel, allowed_paths)
        ):
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
        ".go",
        ".java",
        ".rs",
        ".sql",
        ".css",
        ".md",
        ".json",
        ".toml",
        ".yaml",
        ".yml",
    }


def _path_allowed_by_scope(path: str, allowed_paths: tuple[str, ...]) -> bool:
    normalized = _normalize_repo_path(path)
    if not normalized:
        return False
    for raw_allowed in allowed_paths:
        allowed = _normalize_repo_path(str(raw_allowed or ""))
        if not allowed:
            continue
        if normalized == allowed or normalized.startswith(allowed.rstrip("/") + "/"):
            return True
    return False


def _resolved_path_allowed_by_scope(
    root: Path,
    path: str,
    allowed_paths: tuple[str, ...],
) -> bool:
    """Bind lexical scope to the real target and reject symlink traversal."""

    normalized = _normalize_repo_path(path)
    if not _path_allowed_by_scope(normalized, allowed_paths):
        return False
    if unsafe_target_finding(normalized, workspace_root=root) is not None:
        return False
    candidate = root.resolve()
    for part in Path(normalized).parts:
        candidate = candidate / part
        if candidate.is_symlink():
            return False
    resolved = candidate.resolve()
    if not _is_relative_to(resolved, root.resolve()):
        return False
    try:
        resolved_relative = resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return False
    return _path_allowed_by_scope(resolved_relative, allowed_paths)


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
    for index, (literal, intended_path) in enumerate(
        _literal_requirement_bindings(task, target_path),
        start=1,
    ):
        description = (
            f'File "{intended_path}" must contain "{literal}".'
            if intended_path and intended_path != target_path
            else f'Output must contain "{literal}".'
        )
        criteria.append(
            AcceptanceCriterion(
                id=f"literal-{index}",
                description=description,
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


def _content_constraints(
    task: str,
    existing_content: str,
    target_path: str,
) -> ContentConstraints:
    must_contain = _dedupe(
        [
            *(
                literal
                for literal, intended_path in _literal_requirement_bindings(
                    task,
                    target_path,
                )
                if intended_path in {None, target_path}
            ),
            *_class_fragments(task),
        ]
    )
    preserve_exports = _active_export_names(existing_content)
    preserve_imports = _dedupe(_import_module_names(existing_content))
    return ContentConstraints(
        must_contain=must_contain,
        must_not_contain=_dedupe(["Target file:", *_negative_literal_requirements(task)]),
        preserve_imports=preserve_imports,
        preserve_exports=preserve_exports,
        max_added_lines=80,
        max_removed_lines=60,
    )


def _active_export_names(content: str) -> list[str]:
    """Return public JavaScript/TypeScript export names, not local aliases."""

    active_source = _mask_js_comments_and_strings(content)
    names: list[str] = []
    for match in _EXPORT_DECLARATION_RE.finditer(active_source):
        names.append("default" if match.group("default") else match.group("name"))
    if re.search(r"\bexport\s+default\b", active_source):
        names.append("default")
    for match in re.finditer(
        r"\bexport\s+(?:type\s+)?\{(?P<body>[^}]*)\}",
        active_source,
        flags=re.DOTALL,
    ):
        for raw_item in match.group("body").split(","):
            item = re.sub(r"^\s*type\s+", "", raw_item).strip()
            specifier = re.fullmatch(
                r"(?P<local>[A-Za-z_$][\w$]*)"
                r"(?:\s+as\s+(?P<exported>[A-Za-z_$][\w$]*))?",
                item,
            )
            if specifier:
                names.append(specifier.group("exported") or specifier.group("local"))
    names.extend(
        re.findall(
            r"\bexport\s*\*\s*as\s*([A-Za-z_$][\w$]*)\s+from\b",
            active_source,
        )
    )
    names.extend(
        re.findall(
            r"\b(?:module\.)?exports\.([A-Za-z_$][\w$]*)\s*=",
            active_source,
        )
    )
    if re.search(r"\bmodule\.exports\s*=", active_source):
        names.append("module.exports")
    return _dedupe(names)


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
    # The public task is the sole normative source.  Even apparently
    # "behavioral" model criteria reach coder/reviewer prompts and can silently
    # tighten the contract, so no model-authored criterion is retained here.
    del value
    return [
        {
            "id": criterion.id,
            "description": criterion.description,
            "kind": criterion.kind,
        }
        for criterion in _acceptance_criteria(task, target_path)
    ]


def _coerce_constraints(
    value: Any,
    task: str,
    existing_content: str,
    target_path: str,
    *,
    operation: str,
) -> dict[str, Any]:
    """Return only repository/task-grounded exact constraints.

    An LLM plan may propose useful behavioral acceptance criteria, but it is
    not authoritative for exact source literals.  Trusting invented
    ``must_contain`` or ``must_not_contain`` strings makes an otherwise valid
    patch impossible to approve, and trusting omitted preserve lists can
    silently weaken the deterministic review.  Exact constraints therefore
    come from the public task and the inspected target source only.
    """

    del value
    fallback = _content_constraints(task, existing_content, target_path)
    return {
        "must_contain": list(fallback.must_contain),
        "must_not_contain": list(fallback.must_not_contain),
        "preserve_imports": list(fallback.preserve_imports),
        "preserve_exports": list(fallback.preserve_exports),
        "max_added_lines": (
            200 if operation == "create" else fallback.max_added_lines
        ),
        "max_removed_lines": (
            0 if operation == "create" else fallback.max_removed_lines
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


def _import_context_slices(
    root: Path,
    target_path: str,
    content: str,
    *,
    allowed_paths: tuple[str, ...] | None = None,
) -> list[ContextSlice]:
    slices: list[ContextSlice] = []
    for module_path in _import_module_names(content):
        if not module_path.startswith("."):
            continue
        imported = _resolve_relative_import(root, target_path, module_path)
        if imported is None:
            continue
        rel = imported.relative_to(root).as_posix()
        if unsafe_target_finding(rel, workspace_root=root) is not None:
            continue
        if allowed_paths is not None and not _path_allowed_by_scope(rel, allowed_paths):
            continue
        imported_content = imported.read_text(encoding="utf-8", errors="replace")
        slices.append(_context_slice(rel, "import", imported_content))
        if len(slices) >= 5:
            break
    return slices


def _resolve_relative_import(root: Path, target_path: str, module_path: str) -> Path | None:
    base = (root / target_path).parent
    if Path(target_path).suffix.lower() == ".py":
        dot_count = len(module_path) - len(module_path.lstrip("."))
        python_base = base
        for _index in range(max(0, dot_count - 1)):
            python_base = python_base.parent
        module_tail = module_path.lstrip(".").replace(".", "/")
        raw = (python_base / module_tail).resolve()
        candidates = [Path(f"{raw}.py"), raw / "__init__.py"]
    else:
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
        value
        for match in re.finditer(r"([\"'`])(.+?)\1", without_target_lines)
        if (value := match.group(2).strip())
        and _quoted_requirement_role(without_target_lines, match) == "required"
        and (
            not _quoted_value_is_path(value)
            or _quoted_requirement_has_literal_intent(without_target_lines, match)
        )
    )


def _negative_literal_requirements(task: str) -> list[str]:
    without_target_lines = "\n".join(
        line
        for line in task.splitlines()
        if not line.strip().lower().startswith("target file:")
    )
    return _dedupe(
        value
        for match in re.finditer(r"([\"'`])(.+?)\1", without_target_lines)
        if (value := match.group(2).strip())
        and _quoted_requirement_role(without_target_lines, match) == "forbidden"
        and (
            not _quoted_value_is_path(value)
            or _quoted_requirement_has_literal_intent(without_target_lines, match)
        )
    )


def _literal_requirement_bindings(
    task: str,
    target_path: str,
) -> list[tuple[str, str | None]]:
    without_target_lines = "\n".join(
        line
        for line in task.splitlines()
        if not line.strip().lower().startswith("target file:")
    )
    bindings: list[tuple[str, str | None]] = []
    for match in re.finditer(r"([\"'`])(.+?)\1", without_target_lines):
        value = match.group(2).strip()
        if (
            not value
            or _quoted_requirement_role(without_target_lines, match) != "required"
            or (
                _quoted_value_is_path(value)
                and not _quoted_requirement_has_literal_intent(
                    without_target_lines,
                    match,
                )
            )
        ):
            continue
        intended_path = _quoted_literal_artifact_path(
            without_target_lines,
            match,
        )
        binding = (value, intended_path or target_path)
        if binding not in bindings:
            bindings.append(binding)
    return bindings


def _quoted_value_is_path(value: str) -> bool:
    normalized = value.replace("\\", "/").strip()
    name = Path(normalized).name.lower()
    return bool(
        "/" in normalized
        or name.startswith(".")
        or Path(normalized).suffix.lower() in _QUOTED_PATH_SUFFIXES
    )


_QUOTED_TRANSFORMATION_PATTERNS = (
    re.compile(
        r"\b(?:replace|change|rename)\s+"
        r"(?:(?:the\s+)?(?:copy|heading|label|message|response|status|string|text|title|value|word)\s+)?"
        r"(?P<src_quote>[\"'`])(?P<source>[^\"'`\n]+)(?P=src_quote)\s+"
        r"(?:with|to|as)\s+"
        r"(?P<final_quote>[\"'`])(?P<final>[^\"'`\n]+)(?P=final_quote)",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\bswap\s+"
        r"(?:(?:the\s+)?(?:copy|heading|label|message|response|status|string|text|title|value|word)\s+)?"
        r"(?P<src_quote>[\"'`])(?P<source>[^\"'`\n]+)(?P=src_quote)\s+"
        r"for\s+"
        r"(?P<final_quote>[\"'`])(?P<final>[^\"'`\n]+)(?P=final_quote)",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"\bfrom\s+"
        r"(?P<src_quote>[\"'`])(?P<source>[^\"'`\n]+)(?P=src_quote)\s+"
        r"to\s+"
        r"(?P<final_quote>[\"'`])(?P<final>[^\"'`\n]+)(?P=final_quote)",
        flags=re.IGNORECASE,
    ),
)


def _quoted_requirement_role(text: str, match: re.Match[str]) -> str:
    line_start = text.rfind("\n", 0, match.start()) + 1
    line_end = text.find("\n", match.end())
    if line_end < 0:
        line_end = len(text)
    line = text[line_start:line_end]
    relative_span = (match.start() - line_start, match.end() - line_start)
    for pattern in _QUOTED_TRANSFORMATION_PATTERNS:
        for transformation in pattern.finditer(line):
            source_span = transformation.span("source")
            final_span = transformation.span("final")
            value_span = (relative_span[0] + 1, relative_span[1] - 1)
            if value_span not in {source_span, final_span}:
                continue
            prefix = line[: transformation.start()]
            negated = bool(
                re.search(
                    r"\b(?:do\s+not|don't|must\s+not|never)\s*$",
                    prefix,
                    flags=re.IGNORECASE,
                )
            )
            if value_span == source_span:
                return "required" if negated else "skip"
            return "skip" if negated else "required"
    return "forbidden" if _quoted_requirement_is_forbidden(text, match) else "required"


def _quoted_requirement_is_forbidden(text: str, match: re.Match[str]) -> bool:
    line_start = text.rfind("\n", 0, match.start()) + 1
    prefix = text[line_start : match.start()]
    if re.search(
        r"\b(?:do\s+not|don't|must\s+not|never)\s+"
        r"(?:change|delete|exclude|omit|remove|rename|replace)\b"
        r"[^\n.!?]{0,80}$",
        prefix,
        flags=re.IGNORECASE,
    ):
        return False
    return bool(
        re.search(
            r"(?:\b(?:delete|exclude|omit|remove|without)\b|"
            r"\b(?:do\s+not|don't|must\s+not|never)\s+"
            r"(?:add|contain|display|emit|include|introduce|print|render|show|write)\b)"
            r"[^\n.!?]{0,96}$",
            prefix,
            flags=re.IGNORECASE,
        )
    )


def _quoted_requirement_has_literal_intent(
    text: str,
    match: re.Match[str],
) -> bool:
    line_start = text.rfind("\n", 0, match.start()) + 1
    prefix = text[max(line_start, match.start() - 120) : match.start()]
    line_end = text.find("\n", match.end())
    if line_end < 0:
        line_end = len(text)
    suffix = text[match.end() : min(line_end, match.end() + 96)]
    artifact_noun_prefix = bool(
        re.search(
            r"\b(?:artifact|file|target)\s*$",
            prefix,
            flags=re.IGNORECASE,
        )
    )
    suffix_literal = bool(
        re.match(
            r"\s+(?:must|should|shall|needs?\s+to)\s+"
            r"(?:appear\b(?:\s+in\s+(?:the\s+)?(?:output|text|label|message))?"
            r"|equal\b"
            r"|(?:be\s+)?(?:displayed|emitted|printed|rendered|shown)\b)",
            suffix,
            flags=re.IGNORECASE,
        )
    )
    if suffix_literal and not artifact_noun_prefix:
        return True
    return bool(
        re.search(
            r"(?:\b(?:copy|display|displayed|emit|heading|label|message|print|render|rendered|say|show|shown|title)\b|"
            r"\b(?:output|text|label|message|filename|file\s+path)\s+"
            r"(?:must|should|shall|needs?\s+to)\s+(?:equal|match)\b|"
            r"\bset\b[^\n.!?]{0,88}\bto\s*$|"
            r"\b(?:must|should|shall|needs?\s+to)\s+(?:contain|include)\b|"
            r"\bexact\s+(?:text|filename)\b)"
            r"[^\n.!?]{0,112}$",
            prefix,
            flags=re.IGNORECASE,
        )
        or (
            re.search(r"\binclude\s*$", prefix, flags=re.IGNORECASE)
            and re.match(
                r"\s+(?:in|as)\s+(?:the\s+)?(?:rendered\s+)?"
                r"(?:output|text|label|message)\b",
                suffix,
                flags=re.IGNORECASE,
            )
        )
    )


def _quoted_literal_artifact_path(
    text: str,
    literal_match: re.Match[str],
) -> str | None:
    line_start = text.rfind("\n", 0, literal_match.start()) + 1
    line_end = text.find("\n", literal_match.end())
    if line_end < 0:
        line_end = len(text)
    line = text[line_start:line_end]
    literal_start = literal_match.start() - line_start
    literal_end = literal_match.end() - line_start
    quoted_spans: list[tuple[int, int]] = []
    for candidate in re.finditer(r"([\"'`])(.+?)\1", line):
        quoted_spans.append(candidate.span())
        if candidate.span() == (literal_start, literal_end):
            continue
        value = candidate.group(2).strip().replace("\\", "/")
        if not value or not _quoted_value_is_path(value):
            continue
        if _artifact_path_binds_literal(
            line,
            candidate.start(),
            candidate.end(),
            literal_start,
            literal_end,
        ):
            return value
    for candidate in re.finditer(
        r"(?<![A-Za-z0-9_./-])"
        r"(?P<path>[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.[A-Za-z0-9_-]+)"
        r"(?![A-Za-z0-9_/-])",
        line,
    ):
        if any(start <= candidate.start() < end for start, end in quoted_spans):
            continue
        value = normalize_repo_path_candidate(candidate.group("path"))
        if value and _artifact_path_binds_literal(
            line,
            candidate.start(),
            candidate.end(),
            literal_start,
            literal_end,
        ):
            return value
    return None


def _artifact_path_binds_literal(
    line: str,
    path_start: int,
    path_end: int,
    literal_start: int,
    literal_end: int,
) -> bool:
    if path_end <= literal_start:
        prefix = line[max(0, path_start - 96) : path_start]
        between = line[path_end:literal_start]
        if re.search(r"[.!?]|\b(?:and|or)\b", between, flags=re.IGNORECASE):
            return False
        explicit_prefix = bool(
            re.search(
                r"\b(?:artifact|file|in|inside|target|within)(?:\s+path)?\s*[\"'`]?\s*$",
                prefix,
                flags=re.IGNORECASE,
            )
        )
        linked_action = bool(
            re.search(
                r"^\s*(?:[,;:]\s*)?"
                r"(?:(?:the\s+)?(?:artifact|file|target)\s+)?"
                r"(?:(?:must|should|shall|needs?\s+to)\s+)?"
                r"(?:to\s+)?"
                r"(?:add|append|contain|display|have|include|render|replace|show|update)"
                r"[^\n.!?]{0,80}$",
                between,
                flags=re.IGNORECASE,
            )
        )
        mutation_prefix = bool(
            re.search(
                r"\b(?:add|append|edit|ensure|modify|update|write)\s+$",
                prefix,
                flags=re.IGNORECASE,
            )
        )
        return explicit_prefix or linked_action or (mutation_prefix and linked_action)
    if path_start >= literal_end:
        between = line[literal_end:path_start]
        return bool(
            re.fullmatch(
                r"\s*(?:is\s+present\s+)?"
                r"(?:in|inside|into|to|within)\s+"
                r"(?:(?:the\s+)?(?:artifact|file|target)\s+)?[\"'`]?\s*",
                between,
                flags=re.IGNORECASE,
            )
        )
    return False


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
    return _dedupe(fragments)


def _route_requirements(task: str) -> list[str]:
    routes = []
    for match in _ROUTE_RE.finditer(task):
        route = match.group(1).rstrip(".,;:")
        if route and "." not in Path(route).name:
            routes.append(route)
    return _dedupe(routes)


def _import_module_names(content: str) -> list[str]:
    active_js = _strip_js_comments_and_templates(content)
    try:
        tree = ast.parse(content)
    except SyntaxError:
        python_relative: list[str] = []
    else:
        python_relative = [
            f"{'.' * node.level}{node.module or ''}"
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level > 0
        ]
    return _dedupe(
        [
            *(match.group(1) for match in _IMPORT_RE.finditer(active_js)),
            *python_relative,
        ]
    )


def _strip_js_comments_and_templates(content: str) -> str:
    chars = list(content)
    index = 0
    state = "code"
    quote = ""
    while index < len(chars):
        char = chars[index]
        next_char = chars[index + 1] if index + 1 < len(chars) else ""
        if state == "code":
            if char in {"'", '"'}:
                state = "string"
                quote = char
            elif char == "`":
                chars[index] = " "
                state = "template"
            elif char == "/" and next_char == "/":
                chars[index] = chars[index + 1] = " "
                state = "line_comment"
                index += 1
            elif char == "/" and next_char == "*":
                chars[index] = chars[index + 1] = " "
                state = "block_comment"
                index += 1
        elif state == "string":
            if char == "\\":
                index += 1
            elif char == quote:
                state = "code"
        elif state == "template":
            if char != "\n":
                chars[index] = " "
            if char == "\\":
                if index + 1 < len(chars) and chars[index + 1] != "\n":
                    chars[index + 1] = " "
                index += 1
            elif char == "`":
                state = "code"
        elif state == "line_comment":
            if char == "\n":
                state = "code"
            else:
                chars[index] = " "
        elif state == "block_comment":
            if char == "*" and next_char == "/":
                chars[index] = chars[index + 1] = " "
                state = "code"
                index += 1
            elif char != "\n":
                chars[index] = " "
        index += 1
    return "".join(chars)


def _mask_js_comments_and_strings(content: str) -> str:
    pattern = re.compile(
        r"(?:\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|"
        r"`(?:\\.|[^`\\])*`|//[^\n]*|/\*[\s\S]*?\*/)",
    )
    return pattern.sub(
        lambda match: "".join(
            "\n" if char == "\n" else " " for char in match.group(0)
        ),
        content,
    )


def _parse_json_object(raw_response: str) -> dict[str, Any]:
    raw = (raw_response or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ArchitectLLMError("architect_llm_invalid_json", "response did not contain a JSON object")
    try:
        parsed = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as error:
        raise ArchitectLLMError(
            "architect_llm_invalid_json",
            "response did not contain valid JSON",
        ) from error
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
    central_gate_check("model_call", run_id="architect_llm", model_alias=model_alias)
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
