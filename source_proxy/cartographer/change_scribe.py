from __future__ import annotations

from pathlib import Path

from source_proxy.cartographer.component_mapper import map_paths
from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.git_status import read_git_status_for_project, read_git_statuses
from source_proxy.cartographer.models import (
    ChangeScribeFileExplanation,
    ChangeScribeSummary,
    ComponentMapping,
    GitStatus,
    UnmappedPath,
)


def summarize_changes() -> list[ChangeScribeSummary]:
    drift_by_project: dict[str, bool] = {}
    for finding in detect_blueprint_drift():
        drift_by_project[finding.project_id] = True

    statuses = read_git_statuses()
    if not statuses:
        cwd = Path.cwd()
        if (cwd / ".git").exists():
            statuses = [read_git_status_for_project(project_id=cwd.name.lower(), root=cwd)]

    return [
        _summary_for_status(
            git_status,
            drift_detected=drift_by_project.get(git_status.project_id or "unknown", False),
        )
        for git_status in statuses
        if git_status.available
    ]


def _summary_for_status(
    git_status: GitStatus,
    *,
    drift_detected: bool,
) -> ChangeScribeSummary:
    project_id = git_status.project_id or "unknown"
    changed_files = [_normalize_repo_path(path) for path in git_status.changed_files]
    code_files = [path for path in changed_files if _is_code_file(path)]
    blueprint_files = [path for path in changed_files if path.startswith("_blueprints/")]
    mapped_components, unmapped_paths = map_paths(changed_files)
    components = [component.component_id for component in mapped_components]
    file_explanations = _file_explanations(
        changed_files=changed_files,
        mapped_components=mapped_components,
        unmapped_paths=unmapped_paths,
    )
    component_label = _component_label(components)
    blueprint_update_detected = bool(blueprint_files)

    summary = _summary_sentence(
        component_label=component_label,
        changed_files=changed_files,
        code_files=code_files,
        blueprint_update_detected=blueprint_update_detected,
    )
    evidence = _evidence(
        git_status=git_status,
        changed_files=changed_files,
        blueprint_update_detected=blueprint_update_detected,
    )
    recommended_actions = _recommended_actions(
        component_label=component_label,
        dirty=git_status.dirty,
        blueprint_update_detected=blueprint_update_detected,
        drift_detected=drift_detected,
    )

    return ChangeScribeSummary(
        project_id=project_id,
        summary=summary,
        branch=git_status.branch,
        dirty=git_status.dirty,
        commit_state="dirty" if git_status.dirty else "clean",
        components=components,
        changed_files=changed_files,
        file_explanations=file_explanations,
        evidence=evidence,
        recommended_actions=recommended_actions,
        uncertain_claims=[
            "Summary is based on file paths and Git state only; semantic behavior was not inferred."
        ],
        blueprint_update_detected=blueprint_update_detected,
        drift_detected=drift_detected,
    )


def _summary_sentence(
    *,
    component_label: str,
    changed_files: list[str],
    code_files: list[str],
    blueprint_update_detected: bool,
) -> str:
    if not changed_files:
        return "No uncommitted changes detected."
    if code_files:
        return f"{component_label} code changed."
    if blueprint_update_detected:
        return "Blueprint documentation changed."
    return f"{component_label} files changed."


def _evidence(
    *,
    git_status: GitStatus,
    changed_files: list[str],
    blueprint_update_detected: bool,
) -> list[str]:
    evidence = [
        f"branch: {git_status.branch or 'detached'}",
        f"commit state: {'dirty' if git_status.dirty else 'clean'}",
    ]
    if git_status.last_commit:
        evidence.append(
            f"last commit: {git_status.last_commit.get('sha', '')} {git_status.last_commit.get('message', '')}".strip()
        )
    evidence.extend(f"{path} changed" for path in changed_files[:12])
    evidence.append(
        "blueprint update detected"
        if blueprint_update_detected
        else "no blueprint update detected"
    )
    return evidence


def _recommended_actions(
    *,
    component_label: str,
    dirty: bool,
    blueprint_update_detected: bool,
    drift_detected: bool,
) -> list[str]:
    actions: list[str] = []
    if drift_detected or (dirty and not blueprint_update_detected):
        actions.append(f"review {component_label} blueprint")
    if dirty:
        actions.append("record tests or manual verification before commit")
    if not actions:
        actions.append("no action needed")
    return actions


def _file_explanations(
    *,
    changed_files: list[str],
    mapped_components: list[ComponentMapping],
    unmapped_paths: list[UnmappedPath],
) -> list[ChangeScribeFileExplanation]:
    component_by_path: dict[str, ComponentMapping] = {}
    for component in mapped_components:
        for path in component.matched_paths:
            component_by_path[path] = component
    unmapped_by_path = {item.path: item for item in unmapped_paths}

    explanations: list[ChangeScribeFileExplanation] = []
    for path in changed_files:
        component = component_by_path.get(path)
        if component:
            category = component.component_id
            explanation = _mapped_file_explanation(path=path, component=component)
            review_required = component.risk in {"high", "blocked", "unknown"}
        else:
            unmapped = unmapped_by_path.get(path)
            category = "unknown"
            explanation = (
                "Unknown file changed; manual review required before treating it as safe."
            )
            review_required = True
            if unmapped and unmapped.risk == "blocked":
                category = "blocked"
                explanation = "Blocked or sensitive-shaped path changed; manual safety review required."
        explanations.append(
            ChangeScribeFileExplanation(
                path=path,
                category=category,
                explanation=explanation,
                review_required=review_required,
            )
        )
    return explanations


def _mapped_file_explanation(*, path: str, component: ComponentMapping) -> str:
    if path.startswith("scout/soak-logs/"):
        return "Scout soak log snapshot changed, likely from a Scout soak or closeout run."
    if path.startswith("source_proxy/cartographer/soak-logs/"):
        return "Cartographer soak log snapshot changed, likely from a Cartographer verification run."
    if path.startswith("source_proxy/cartographer/"):
        return "Cartographer code changed, likely affecting autonomy or reporting logic."
    if path.startswith("source_proxy/tests/") or "/__tests__/" in path or path.endswith(".test.ts"):
        return f"{component.label} test changed."
    if path.startswith("_blueprints/"):
        return "Blueprint documentation changed."
    if path.startswith("docs/") or path.lower().endswith(".md"):
        return f"{component.label} documentation changed."
    return f"{component.label} file changed."


def _component_label(components: list[str]) -> str:
    if not components:
        return "Unmapped"
    if len(components) == 1:
        return components[0].replace("-", " ").title()
    return "Multiple components"


def _is_code_file(path: str) -> bool:
    return Path(path).suffix.lower() in {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}


def _normalize_repo_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    return normalized[2:] if normalized.startswith("./") else normalized
