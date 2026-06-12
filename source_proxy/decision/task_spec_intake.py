from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

from source_proxy.decision.proposal_task import (
    bounded_proposal_create_allowed,
    parse_bounded_proposal_task,
    path_matches_forbidden,
)
from source_proxy.decision.router import (
    DecisionInput,
    decide_route,
    resolve_target_from_task,
    unsafe_target_for_route,
)
from source_proxy.planning.plan import PLAN_SCHEMA_VERSION
from source_proxy.safety.paths import normalize_repo_path_candidate

TaskKind = Literal[
    "modify_existing_file",
    "create_new_file",
    "create_file_bundle",
    "read_only",
    "ask_clarification",
    "target_unresolved",
    "protected_path",
    "path_escape",
    "unsupported",
]
WorkspaceMode = Literal["real_repo_preview", "disposable_workspace", "none"]
ClarificationState = Literal["not_needed", "required", "blocked"]


@dataclass(frozen=True)
class ArtifactCreateResolution:
    task_kind: TaskKind
    task_shape: str
    artifact_class: str
    allowed_extensions: list[str]
    max_file_count: int
    reason_code: str


@dataclass(frozen=True)
class TaskSpecIntake:
    schema_version: int
    task_kind: TaskKind
    intent: str
    user_prompt: str
    target_paths: list[str]
    allowed_files: list[str]
    forbidden_files: list[str]
    protected_paths: list[str]
    task_shape: str
    task_shape_source: str
    artifact_class: str
    allowed_extensions: list[str]
    max_file_count: int
    target_source: str
    workspace_decision_source: str
    allowed_scope_source: str
    workspace_mode: WorkspaceMode
    approval_level: str
    model_lane: str
    context_sources: list[str]
    verification_policy: list[str]
    risk_level: str
    clarification_state: ClarificationState
    clarification_prompt: str
    reason_codes: list[str]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_task_spec_intake(
    task: str,
    *,
    workspace_root: Path,
    allowed_files: list[str] | tuple[str, ...] | None = None,
    forbidden_files: list[str] | tuple[str, ...] | None = None,
    wants_implementation: bool = False,
    model_lane: str = "coder_agent",
    allow_messy_homepage_helper: bool = True,
) -> TaskSpecIntake:
    prompt = (task or "").strip()
    allowed = _normalize_list(allowed_files or [])
    explicit_forbidden = _normalize_list(forbidden_files or [])
    proposal = parse_bounded_proposal_task(prompt)
    decision = decide_route(DecisionInput(task=prompt, wants_implementation=wants_implementation))
    route_reasons = _dedupe(str(code) for code in decision.reason_codes)
    resolved = resolve_target_from_task(prompt, workspace_root)
    unsafe = unsafe_target_for_route(prompt, resolved, workspace_root)
    protected_paths = _dedupe(
        path
        for path in [
            unsafe.path if unsafe is not None else "",
            *[path for path in _target_candidates(prompt) if _is_protectedish(path)],
        ]
        if path
    )

    reason_codes = list(route_reasons)
    if unsafe is not None and unsafe.reason_code not in reason_codes:
        reason_codes.append(unsafe.reason_code)
    target = resolved.path
    target_paths = [target] if target else []
    intent = _intent_for(prompt, wants_implementation)
    task_kind: TaskKind = "read_only"
    workspace_mode: WorkspaceMode = "none"
    clarification_state: ClarificationState = "not_needed"
    clarification_prompt = ""
    risk_level = str(decision.risk_tier or "low")
    task_shape = ""
    task_shape_source = ""
    artifact_class = ""
    allowed_extensions: list[str] = []
    max_file_count = 8
    target_source = "none"
    workspace_decision_source = "route_decision"
    allowed_scope_source = "none"
    artifact_resolution = _resolve_disposable_artifact_create(prompt)

    if unsafe is not None:
        task_kind = "protected_path" if unsafe.reason_code == "protected_path" else "path_escape"
        target_paths = [unsafe.path]
        allowed = []
        task_shape = "blocked_protected_or_unsafe_path"
        task_shape_source = "protected_path_gate"
        target_source = "blocked_target"
        workspace_decision_source = "protected_path_gate"
        allowed_scope_source = "blocked"
        clarification_state = "blocked"
        clarification_prompt = _blocked_prompt(unsafe.reason_code, unsafe.path)
        risk_level = "high"
    elif proposal is not None and proposal.target_file:
        create_ok, blocked_reason = bounded_proposal_create_allowed(
            proposal,
            workspace_root=workspace_root,
        )
        target = normalize_repo_path_candidate(proposal.target_file)
        target_paths = [target] if target else []
        allowed = list(proposal.allowed_files)
        explicit_forbidden = _dedupe([*explicit_forbidden, *proposal.forbidden_files])
        task_shape = "bounded_disposable_create"
        task_shape_source = "explicit_task_spec"
        artifact_class = "explicit_target"
        target_source = "user_explicit"
        workspace_decision_source = "explicit_task_spec"
        allowed_scope_source = "user_explicit_allowed_files"
        if create_ok:
            task_kind = "create_new_file"
            workspace_mode = "disposable_workspace"
            clarification_state = "not_needed"
            reason_codes = _without(reason_codes, "target_missing", "target_unresolved")
        else:
            task_kind = "ask_clarification"
            clarification_state = "required"
            clarification_prompt = _proposal_clarification(blocked_reason, target)
            reason_codes = _dedupe([*reason_codes, blocked_reason or "bounded_create_not_allowed"])
    elif wants_implementation and target:
        if "target_missing" in route_reasons:
            task_kind = "ask_clarification"
            clarification_state = "required"
            clarification_prompt = (
                f"`{target}` does not exist. Confirm a disposable workspace create task "
                "with explicit allowed_files, or choose an existing repo file."
            )
            allowed = []
            task_shape = "explicit_target_missing"
            task_shape_source = "route_decision"
            target_source = "user_explicit_missing"
        else:
            task_kind = "modify_existing_file"
            workspace_mode = "real_repo_preview"
            allowed = allowed or [target]
            task_shape = _explicit_target_shape(target)
            task_shape_source = "explicit_user_target"
            artifact_class = _artifact_class_for_path(target)
            target_source = "user_explicit"
            workspace_decision_source = "explicit_user_target"
            allowed_scope_source = "user_explicit_target"
    elif wants_implementation and allow_messy_homepage_helper and artifact_resolution is not None:
        task_kind = artifact_resolution.task_kind
        intent = "create"
        workspace_mode = "disposable_workspace"
        task_shape = artifact_resolution.task_shape
        task_shape_source = "generic_artifact_resolver"
        artifact_class = artifact_resolution.artifact_class
        allowed_extensions = artifact_resolution.allowed_extensions
        max_file_count = artifact_resolution.max_file_count
        target_paths = []
        target_source = "model_authored_required"
        workspace_decision_source = "generic_artifact_resolver"
        allowed_scope_source = "artifact_class_extensions"
        clarification_state = "not_needed"
        reason_codes = _dedupe(
            [
                *_without(reason_codes, "target_missing", "target_unresolved"),
                artifact_resolution.reason_code,
            ]
        )
    elif wants_implementation:
        task_kind = "target_unresolved"
        task_shape = "clarification_required_real_repo_implementation"
        task_shape_source = "target_resolution"
        workspace_decision_source = "target_resolution"
        allowed_scope_source = "none"
        clarification_state = "required"
        clarification_prompt = (
            "Add one repo-relative Target file line or choose a disposable workspace "
            "create target before any model-action run."
        )
        allowed = []

    if allowed and target and target not in allowed and not any(
        item.endswith("/**") and target.startswith(item[:-3]) for item in allowed
    ):
        reason_codes = _dedupe([*reason_codes, "target_not_in_allowed_files"])
        clarification_state = "required"
        clarification_prompt = f"`{target}` must be included in allowed_files before preview."

    forbidden = _dedupe([*explicit_forbidden, *_default_forbidden_files()])
    if target and path_matches_forbidden(target, forbidden):
        reason_codes = _dedupe([*reason_codes, "target_forbidden"])
        allowed = []
        clarification_state = "blocked"
        clarification_prompt = f"`{target}` intersects forbidden_files."

    if clarification_state != "not_needed" and task_kind not in {"protected_path", "path_escape"}:
        workspace_mode = "none"

    return TaskSpecIntake(
        schema_version=PLAN_SCHEMA_VERSION,
        task_kind=task_kind,
        intent=intent,
        user_prompt=prompt,
        target_paths=target_paths,
        allowed_files=allowed,
        forbidden_files=forbidden,
        protected_paths=protected_paths,
        task_shape=task_shape,
        task_shape_source=task_shape_source,
        artifact_class=artifact_class,
        allowed_extensions=allowed_extensions,
        max_file_count=max_file_count,
        target_source=target_source,
        workspace_decision_source=workspace_decision_source,
        allowed_scope_source=allowed_scope_source,
        workspace_mode=workspace_mode,
        approval_level="preview_only_no_apply",
        model_lane=model_lane,
        context_sources=_context_sources_for(task_kind, target_paths),
        verification_policy=_verification_for(task_kind),
        risk_level=risk_level,
        clarification_state=clarification_state,
        clarification_prompt=clarification_prompt,
        reason_codes=_dedupe(reason_codes),
        summary=_summary(task_kind, target_paths, clarification_state),
    )


def intake_as_legacy_task_spec(intake: TaskSpecIntake) -> dict[str, Any]:
    target = intake.target_paths[0] if intake.target_paths else ""
    return {
        "schema_version": intake.schema_version,
        "task_type": intake.task_kind,
        "target": target,
        "allowed_files": list(intake.allowed_files),
        "forbidden_files": list(intake.forbidden_files),
        "literal_requirements": [],
        "verification": list(intake.verification_policy),
        "risk_tier": intake.risk_level,
        "source": "task_spec_intake",
        "blockers": list(intake.reason_codes)
        if intake.clarification_state != "not_needed"
        else [],
        "clarification_state": intake.clarification_state,
        "clarification_prompt": intake.clarification_prompt,
        "workspace_mode": intake.workspace_mode,
        "approval_level": intake.approval_level,
        "intent": intake.intent,
        "context_sources": list(intake.context_sources),
        "task_shape": intake.task_shape,
        "task_shape_source": intake.task_shape_source,
        "artifact_class": intake.artifact_class,
        "allowed_extensions": list(intake.allowed_extensions),
        "max_file_count": intake.max_file_count,
        "target_source": intake.target_source,
        "workspace_decision_source": intake.workspace_decision_source,
        "allowed_scope_source": intake.allowed_scope_source,
    }


def _normalize_list(values: list[str] | tuple[str, ...]) -> list[str]:
    return _dedupe(
        path
        for value in values
        if (path := normalize_repo_path_candidate(str(value or "")))
    )


def _target_candidates(task: str) -> list[str]:
    pattern = re.compile(
        r"(?<![A-Za-z0-9_./-])((?:\.env(?:\.[A-Za-z0-9_.-]+)?|[A-Za-z0-9._/@()[\]-]+"
        r"\.(?:tsx?|jsx?|py|css|html|json|md|xml|ya?ml|toml|pem|key|crt)))"
    )
    return _dedupe(
        path
        for match in pattern.finditer(task or "")
        if (path := normalize_repo_path_candidate(match.group(1)))
    )


def _is_protectedish(path: str) -> bool:
    lowered = path.lower()
    return lowered.startswith(".env") or lowered.endswith((".pem", ".key", ".crt"))


def _intent_for(task: str, wants_implementation: bool) -> str:
    normalized = task.lower()
    if re.search(r"\b(create|new|scaffold|build)\b", normalized):
        return "create"
    if re.search(r"\b(fix|debug|bug|broken)\b", normalized):
        return "fix"
    if re.search(r"\b(style|polish|layout|visual|hover)\b", normalized):
        return "style"
    if wants_implementation:
        return "modify"
    return "analyze"


def _resolve_disposable_artifact_create(task: str) -> ArtifactCreateResolution | None:
    normalized = (task or "").lower()
    createish = re.search(r"\b(init|initialize|make|create|build|new|scaffold|start|draft)\b", normalized)
    if not createish:
        return None
    markdownish = re.search(r"\b(markdown|readme|checklist|notes?|guide|document)\b", normalized)
    jsonish = re.search(r"\b(json|config example|configuration example|sample config|example config)\b", normalized)
    static_pageish = re.search(
        r"\b(homepage|home page|landing page|index\.html|html page|static page|website|web page)\b",
        normalized,
    )
    browser_uiish = re.search(
        r"\b(page|site|app|demo|prototype|ui|interface|dashboard|panel|viewer|tracker|portal|screen|widget)\b",
        normalized,
    )
    bundleish = re.search(r"\b(bundle|tiny project|small project|static demo|demo bundle)\b", normalized)
    textish = re.search(r"\b(text file|txt|artifact|example)\b", normalized)
    implementationish = re.search(
        r"\b(fix|refactor|wire|database|api|backend|server|component|route|auth|integrate|migration)\b",
        normalized,
    )
    disposable_hint = re.search(
        r"\b(tiny|small|simple|standalone|static|demo|artifact|example|prototype|draft|mock|sample)\b",
        normalized,
    )
    if implementationish and not (browser_uiish and disposable_hint) and not markdownish and not jsonish:
        return None
    if markdownish:
        return ArtifactCreateResolution(
            task_kind="create_new_file",
            task_shape="disposable_single_file_artifact",
            artifact_class="markdown_document",
            allowed_extensions=[".md"],
            max_file_count=1,
            reason_code="generic_artifact_create_candidate",
        )
    if jsonish:
        return ArtifactCreateResolution(
            task_kind="create_new_file",
            task_shape="disposable_single_file_artifact",
            artifact_class="json_example",
            allowed_extensions=[".json"],
            max_file_count=1,
            reason_code="generic_artifact_create_candidate",
        )
    if static_pageish:
        return ArtifactCreateResolution(
            task_kind="create_new_file",
            task_shape="disposable_single_file_artifact",
            artifact_class="html_static_page",
            allowed_extensions=[".html"],
            max_file_count=1,
            reason_code="generic_artifact_create_candidate",
        )
    if browser_uiish:
        return ArtifactCreateResolution(
            task_kind="create_file_bundle",
            task_shape="disposable_small_file_bundle",
            artifact_class="static_ui_artifact",
            allowed_extensions=[".html", ".css", ".js"],
            max_file_count=3,
            reason_code="generic_static_ui_artifact_candidate",
        )
    if bundleish:
        return ArtifactCreateResolution(
            task_kind="create_file_bundle",
            task_shape="disposable_small_file_bundle",
            artifact_class="static_ui_artifact",
            allowed_extensions=[".html", ".css", ".js"],
            max_file_count=3,
            reason_code="generic_artifact_bundle_candidate",
        )
    if textish:
        return ArtifactCreateResolution(
            task_kind="create_new_file",
            task_shape="disposable_single_file_artifact",
            artifact_class="text_artifact",
            allowed_extensions=[".txt", ".md"],
            max_file_count=1,
            reason_code="generic_artifact_create_candidate",
        )
    return None


def _explicit_target_shape(target: str) -> str:
    if target.lower().endswith((".md", ".json", ".yaml", ".yml", ".toml", ".xml")):
        return "explicit_docs_or_config_edit"
    return "bounded_existing_repo_edit"


def _artifact_class_for_path(target: str) -> str:
    lowered = target.lower()
    if lowered.endswith(".md"):
        return "markdown_document"
    if lowered.endswith(".json"):
        return "json_example"
    if lowered.endswith((".yaml", ".yml", ".toml", ".xml")):
        return "config_file"
    if lowered.endswith(".html"):
        return "html_static_page"
    return "existing_repo_file"


def _default_forbidden_files() -> list[str]:
    return [".env", ".env.*", "*.pem", "*.key", "certificates/*"]


def _verification_for(task_kind: TaskKind) -> list[str]:
    if task_kind in {"modify_existing_file", "create_new_file", "create_file_bundle"}:
        return ["git diff --check"]
    return []


def _context_sources_for(task_kind: TaskKind, target_paths: list[str]) -> list[str]:
    if task_kind in {"modify_existing_file", "create_new_file"} and target_paths:
        return ["target_path", "repo_map"]
    if task_kind == "target_unresolved":
        return ["clarification_request"]
    return []


def _blocked_prompt(reason_code: str, target: str) -> str:
    if reason_code == "protected_path":
        return f"`{target}` is protected or secret-shaped; choose a non-secret repo file."
    if reason_code == "path_escape":
        return f"`{target}` escapes the workspace; choose a repo-relative path."
    return f"`{target}` is blocked by `{reason_code}`."


def _proposal_clarification(blocked_reason: str, target: str) -> str:
    if blocked_reason == "missing_allowed_files":
        return "Disposable workspace create tasks require explicit allowed_files."
    if blocked_reason == "target_not_in_allowed_files":
        return f"`{target}` must be listed in allowed_files."
    if blocked_reason == "target_already_exists":
        return f"`{target}` already exists; choose modify_existing_file or another target."
    return f"Clarify the proposal scope before model execution: {blocked_reason or 'unknown'}."


def _summary(
    task_kind: TaskKind,
    target_paths: list[str],
    clarification_state: ClarificationState,
) -> str:
    target = ", ".join(target_paths) if target_paths else "no target"
    if clarification_state == "not_needed":
        return f"TaskSpec ready: {task_kind} for {target}."
    return f"TaskSpec {clarification_state}: {task_kind} for {target}."


def _dedupe(values: Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _without(values: list[str], *blocked: str) -> list[str]:
    blocked_set = set(blocked)
    return [value for value in values if value not in blocked_set]
