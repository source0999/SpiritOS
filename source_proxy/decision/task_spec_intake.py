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
class TaskSpecIntake:
    schema_version: int
    task_kind: TaskKind
    intent: str
    user_prompt: str
    target_paths: list[str]
    allowed_files: list[str]
    forbidden_files: list[str]
    protected_paths: list[str]
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

    if unsafe is not None:
        task_kind = "protected_path" if unsafe.reason_code == "protected_path" else "path_escape"
        target_paths = [unsafe.path]
        allowed = []
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
        else:
            task_kind = "modify_existing_file"
            workspace_mode = "real_repo_preview"
            allowed = allowed or [target]
    elif wants_implementation and _is_messy_homepage_disposable_prompt(prompt):
        target = "index.html"
        target_paths = [target]
        task_kind = "create_new_file"
        intent = "create"
        workspace_mode = "disposable_workspace"
        allowed = ["index.html", "styles.css"]
        clarification_state = "not_needed"
        reason_codes = _dedupe(
            [
                *_without(reason_codes, "target_missing", "target_unresolved"),
                "messy_homepage_disposable_candidate",
            ]
        )
    elif wants_implementation:
        task_kind = "target_unresolved"
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


def _is_messy_homepage_disposable_prompt(task: str) -> bool:
    normalized = (task or "").lower()
    createish = re.search(r"\b(init|initialize|make|create|build|new|repo|repository)\b", normalized)
    homepageish = re.search(r"\b(homepage|home page|index\.html|landing page)\b", normalized)
    return bool(createish and homepageish)


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
