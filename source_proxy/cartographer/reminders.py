from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from source_proxy.cartographer.component_mapper import map_paths
from source_proxy.cartographer.drift import detect_blueprint_drift
from source_proxy.cartographer.git_status import read_git_statuses
from source_proxy.cartographer.models import CartographerReminder, DriftFinding, GitStatus


PRIMARY_BRANCHES = {"main", "master", "trunk"}
MANY_CHANGED_FILES_THRESHOLD = 8


def build_reminders() -> list[CartographerReminder]:
    drift = detect_blueprint_drift()
    drift_by_project: dict[str, list[DriftFinding]] = {}
    for finding in drift:
        drift_by_project.setdefault(finding.project_id, []).append(finding)

    reminders: list[CartographerReminder] = []
    seen: set[str] = set()
    for git_status in read_git_statuses():
        for reminder in _reminders_for_git_status(
            git_status=git_status,
            project_drift=drift_by_project.get(git_status.project_id or "unknown", []),
        ):
            if reminder.reminder_id in seen:
                continue
            seen.add(reminder.reminder_id)
            reminders.append(reminder)
    return reminders


def _reminders_for_git_status(
    *, git_status: GitStatus, project_drift: list[DriftFinding]
) -> list[CartographerReminder]:
    if not git_status.available:
        return []

    project_id = git_status.project_id or "unknown"
    changed_files = [_normalize_repo_path(path) for path in git_status.changed_files]
    changed_count = len(changed_files)
    reminders: list[CartographerReminder] = []

    if git_status.dirty:
        reminders.append(
            _reminder(
                project_id=project_id,
                kind="dirty_working_tree",
                message="Working tree has uncommitted changes.",
                reason=f"{changed_count} files changed.",
                changed_file_count=changed_count,
                related_files=changed_files[:12],
                severity="info",
            )
        )

    if changed_count >= MANY_CHANGED_FILES_THRESHOLD:
        reminders.append(
            _reminder(
                project_id=project_id,
                kind="checkpoint_commit_suggested",
                message="Recommendation: make a checkpoint commit after review.",
                reason=f"{changed_count} files changed.",
                changed_file_count=changed_count,
                related_files=changed_files[:12],
                severity="review_suggested",
            )
        )

    if git_status.branch in PRIMARY_BRANCHES and git_status.dirty:
        reminders.append(
            _reminder(
                project_id=project_id,
                kind="branch_recommended",
                message="Recommendation: create branch before continuing.",
                reason=f"{changed_count} files changed on {git_status.branch}.",
                changed_file_count=changed_count,
                related_files=changed_files[:12],
                suggested_branch=_suggested_branch(changed_files),
                severity="action_recommended",
            )
        )

    if project_drift:
        reminders.append(
            _reminder(
                project_id=project_id,
                kind="blueprint_stale_before_commit",
                message="Blueprint review is suggested before committing.",
                reason=f"{len(project_drift)} drift findings are open.",
                changed_file_count=changed_count,
                related_files=_related_drift_files(project_drift),
                related_drift=[finding.drift_id for finding in project_drift],
                severity="review_suggested",
            )
        )

    if _code_changed_without_test_record(changed_files):
        reminders.append(
            _reminder(
                project_id=project_id,
                kind="tests_not_recorded",
                message="Test evidence has not been recorded for these code changes.",
                reason="Code changed without a matching test or docs verification file change.",
                changed_file_count=changed_count,
                related_files=[
                    path for path in changed_files if _is_code_file(path) and not _is_test_path(path)
                ][:12],
                severity="review_suggested",
            )
        )

    return reminders


def _code_changed_without_test_record(changed_files: list[str]) -> bool:
    code_changes = [
        path for path in changed_files if _is_code_file(path) and not _is_test_path(path)
    ]
    if not code_changes:
        return False
    return not any(_is_test_path(path) or _is_verification_doc(path) for path in changed_files)


def _is_code_file(path: str) -> bool:
    return Path(path).suffix in {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}


def _is_test_path(path: str) -> bool:
    lowered = path.lower()
    return (
        "/test" in lowered
        or "/__tests__/" in lowered
        or lowered.endswith(".test.ts")
        or lowered.endswith(".test.tsx")
        or lowered.endswith("_test.py")
        or lowered.startswith("tests/")
    )


def _is_verification_doc(path: str) -> bool:
    lowered = path.lower()
    return "manual-check" in lowered or "verification" in lowered or "runbook" in lowered


def _suggested_branch(changed_files: list[str]) -> str:
    components, _unmapped = map_paths(
        [path for path in changed_files if not path.startswith("_blueprints/")]
    )
    if components:
        component = components[0].component_id
    else:
        component = "work"
    return f"cartographer/{_slug(component)}-blueprint-review"


def _related_drift_files(project_drift: list[DriftFinding]) -> list[str]:
    files: list[str] = []
    seen: set[str] = set()
    for finding in project_drift:
        for path in finding.changed_files:
            if path in seen:
                continue
            seen.add(path)
            files.append(path)
    return files[:12]


def _reminder(
    *,
    project_id: str,
    kind: str,
    message: str,
    reason: str,
    changed_file_count: int,
    related_files: list[str],
    severity: str,
    suggested_branch: str | None = None,
    related_drift: list[str] | None = None,
) -> CartographerReminder:
    key = "|".join([project_id, kind, reason, suggested_branch or ""])
    return CartographerReminder(
        reminder_id=sha256(key.encode("utf-8")).hexdigest()[:16],
        project_id=project_id,
        kind=kind,
        message=message,
        reason=reason,
        severity=severity,  # type: ignore[arg-type]
        changed_file_count=changed_file_count,
        suggested_branch=suggested_branch,
        related_files=related_files,
        related_drift=related_drift or [],
    )


def _slug(value: str) -> str:
    return "".join(char if char.isalnum() else "-" for char in value.lower()).strip("-") or "work"


def _normalize_repo_path(path: str) -> str:
    return path.strip().replace("\\", "/").lstrip("./")
