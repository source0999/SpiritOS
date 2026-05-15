from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import sqlite3
import shutil
import subprocess
import tempfile
from contextlib import closing
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Literal
from uuid import uuid4

from source_proxy.routing.litellm_router import available_model_aliases, get_router
from source_proxy.planning.plan import (
    AcceptanceCriterion,
    CoderPacket,
    CoderResponse,
    ContentConstraints,
    ContextSlice,
    TargetFile,
    task_spec_from_packet,
    task_spec_from_plan,
    validate_task_spec_for_packet,
)
from source_proxy.verification.contracts import (
    SUBJECTIVE_IMPROVEMENT_REQUIRES_DIFF_REASON_CODE,
    VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE,
    subjective_visual_diff_is_material,
    task_requests_subjective_improvement,
    validate_replacement_content,
)
from source_proxy.verification.diff import (
    DiffVerificationError,
    _parse_changed_files,
    diff_candidates_for_git_apply,
    preview_diff_verification,
    sanitize_unified_diff_for_git_apply,
    task_spec_diff_check,
)

# Mid-file ``patch does not apply``: try whitespace relaxations only. Do **not** use
# ``--3way`` here — it requires blobs in the git index; untracked or odd trees get
# ``does not exist in index`` and waste cycles (runtime-proven on CodingAgentInterface).
_GIT_APPLY_FLAG_CHAINS: tuple[tuple[str, ...], ...] = (
    (),
    ("--ignore-whitespace",),
    ("--ignore-space-change",),
)


def _workspace_root_from_package_walk() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "package.json").is_file() and (
            (parent / "source_proxy").is_dir() or (parent / "src").is_dir()
        ):
            return parent
    return Path.cwd().resolve()


def _spirit_project_path_roots_resolved() -> list[Path]:
    """Every comma-separated SPIRIT_PROJECT_PATH entry, expanded, in order (may not exist)."""
    raw = os.getenv("SPIRIT_PROJECT_PATH", "").strip()
    if not raw:
        return []
    roots: list[Path] = []
    for part in raw.split(","):
        segment = part.strip()
        if not segment:
            continue
        roots.append(Path(segment).expanduser().resolve())
    return roots


def _source_proxy_project_roots_resolved() -> list[Path]:
    """Extra roots from ``SOURCE_PROXY_PROJECT_ROOTS`` (comma list) for git apply on Linux."""
    raw = os.getenv("SOURCE_PROXY_PROJECT_ROOTS", "").strip()
    if not raw:
        return []
    roots: list[Path] = []
    for part in raw.split(","):
        segment = part.strip()
        if not segment:
            continue
        roots.append(Path(segment).expanduser().resolve())
    return roots


def _configured_apply_roots_missing_mounts() -> list[str]:
    """SPIRIT_PROJECT_PATH + SOURCE_PROXY_PROJECT_ROOTS entries that are not directories."""
    seen: set[str] = set()
    missing: list[str] = []
    for root in (
        *_spirit_project_path_roots_resolved(),
        *_source_proxy_project_roots_resolved(),
    ):
        resolved = root.resolve()
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        if not resolved.is_dir():
            missing.append(key)
    return missing


def _workspace_root() -> Path:
    """Repo root for SQLite, backups, audit logs, and git apply.

    First **existing** directory in ``SPIRIT_PROJECT_PATH`` (comma list), else walk
    from this file to ``package.json`` + ``src``/``source_proxy``. Stale mount
    entries that are not directories fall through instead of poisoning the whole stack.
    """
    for root in _spirit_project_path_roots_resolved():
        if root.is_dir():
            return root
    return _workspace_root_from_package_walk()


def _ordered_workspace_roots_for_apply() -> list[Path]:
    """SPIRIT dirs + ``SOURCE_PROXY_PROJECT_ROOTS``, then package-walk root if not listed."""
    ordered: list[Path] = []
    seen: set[str] = set()
    cwd = Path.cwd().resolve()
    if cwd.is_dir() and ((cwd / "src").is_dir() or (cwd / "source_proxy").is_dir()):
        ordered.append(cwd)
        seen.add(str(cwd))
    for root in (
        *_spirit_project_path_roots_resolved(),
        *_source_proxy_project_roots_resolved(),
    ):
        if root.is_dir():
            key = str(root.resolve())
            if key not in seen:
                ordered.append(root.resolve())
                seen.add(key)
    walk = _workspace_root_from_package_walk().resolve()
    if str(walk) not in seen:
        ordered.append(walk)
    return ordered if ordered else [walk]


def _unified_diff_adds_new_file_at(unified_diff: str, rel_posix: str) -> bool:
    """True when the patch creates ``rel_posix`` from ``/dev/null`` (git new-file conventions)."""
    norm = rel_posix.replace("\\", "/")
    u = unified_diff.replace("\\", "/").replace("\r\n", "\n")
    if f"+++ b/{norm}" not in u:
        return False
    if "new file mode" in u:
        return True
    return "--- a/dev/null" in u or "--- /dev/null" in u


def next_app_router_route_to_path(route: str, *, endpoint: str = "page.tsx") -> str | None:
    """Map a public Next App Router URL path to its exposing source file."""
    clean_route = route.strip().split("?", 1)[0].split("#", 1)[0].rstrip(".,;:")
    if not clean_route.startswith("/"):
        return None
    endpoint_name = endpoint if endpoint in {"page.tsx", "route.ts"} else "page.tsx"
    segments: list[str] = []
    for raw_segment in clean_route.strip("/").split("/"):
        segment = raw_segment.strip()
        if not segment or (segment.startswith("(") and segment.endswith(")")):
            continue
        if segment.startswith("_"):
            return None
        segments.append(segment)
    if not segments:
        return f"src/app/{endpoint_name}"
    return f"src/app/{'/'.join(segments)}/{endpoint_name}"


def next_app_router_path_to_route(rel_path: str) -> str | None:
    """Map ``src/app/**/(page.tsx|route.ts)`` to the public URL path it exposes."""
    normalized = rel_path.replace("\\", "/").strip().lstrip("./")
    prefix = "src/app/"
    if not normalized.startswith(prefix):
        return None
    parts = normalized[len(prefix) :].split("/")
    if not parts or parts[-1] not in {"page.tsx", "route.ts"}:
        return None
    route_segments: list[str] = []
    for segment in parts[:-1]:
        if not segment or (segment.startswith("(") and segment.endswith(")")):
            continue
        if segment.startswith("_"):
            return None
        route_segments.append(segment)
    return "/" + "/".join(route_segments)


def _next_app_router_duplicate_route_files(repo_root: Path, rel_path: str) -> list[str]:
    route = next_app_router_path_to_route(rel_path)
    if route is None:
        return []
    matches: list[str] = []
    app_root = repo_root / "src/app"
    if not app_root.is_dir():
        return []
    for endpoint in ("page.tsx", "route.ts"):
        for candidate in app_root.rglob(endpoint):
            try:
                candidate_rel = candidate.relative_to(repo_root).as_posix()
            except ValueError:
                continue
            if candidate_rel == rel_path.replace("\\", "/"):
                continue
            if next_app_router_path_to_route(candidate_rel) == route:
                matches.append(candidate_rel)
    return sorted(matches)


def _next_app_router_route_hint(
    repo_root: Path,
    rel: str | None,
    requested_route: str | None = None,
) -> str | None:
    if not rel:
        return None
    normalized_rel = rel.replace("\\", "/")
    target_route = next_app_router_path_to_route(normalized_rel)
    if requested_route:
        expected = next_app_router_route_to_path(requested_route)
        if expected is None:
            return f"Route {requested_route!r} is not exposed by a public Next App Router page or route file."
        if normalized_rel != expected:
            return (
                f"Route {requested_route!r} maps to `{expected}`, "
                f"but the diff targets `{normalized_rel}`."
            )
    if normalized_rel.startswith("src/app/") and target_route is None:
        return (
            f"`{normalized_rel}` is under src/app but is not a public page.tsx or route.ts "
            "path, or it includes a private `_` segment."
        )
    duplicates = _next_app_router_duplicate_route_files(repo_root, normalized_rel)
    if duplicates and target_route:
        return (
            f"`{normalized_rel}` exposes route `{target_route}`. Other files also expose "
            f"that route: {duplicates!r}. This is a warning only; explicit target wins."
        )
    return None


def _normalize_next_app_router_diff_targets(
    roots: list[Path],
    changed_files: list[dict[str, Any]],
    unified_diff: str,
) -> tuple[list[dict[str, Any]], str, bool]:
    """Validate App Router target semantics without rewriting explicit paths."""
    _ = roots
    return changed_files, unified_diff, False


def _rels_for_apply(
    changed_files: list[dict[str, Any]],
    unified_diff: str,
) -> list[str]:
    rels = [
        str(f.get("path") or "").strip().replace("\\", "/")
        for f in changed_files
        if str(f.get("path") or "").strip()
    ]
    if rels:
        return rels
    one = _first_target_rel_from_changed_or_diff(changed_files, unified_diff)
    return [one] if one else []


def _is_git_dev_null_old_line(line: str) -> bool:
    if not line.startswith("--- "):
        return False
    rest = line[4:].strip()
    return rest in ("/dev/null", "dev/null", "a/dev/null")


def _plus_line_target_relpath(line: str) -> str | None:
    if not line.startswith("+++ "):
        return None
    rest = line[4:].strip()
    if len(rest) >= 2 and rest[0] == rest[-1] == '"':
        rest = rest[1:-1]
    if rest.startswith("b/"):
        rest = rest[2:]
    elif rest.startswith("a/") and rest != "a/dev/null":
        rest = rest[2:]
    out = rest.replace("\\", "/").strip()
    return out or None


def _new_file_relpaths_from_unified_diff(unified_diff: str) -> set[str]:
    """Paths introduced from ``/dev/null`` in this unified diff (git new-file hunks)."""
    out: set[str] = set()
    lines = unified_diff.replace("\r\n", "\n").split("\n")
    for i in range(len(lines) - 1):
        if not _is_git_dev_null_old_line(lines[i]):
            continue
        rel = _plus_line_target_relpath(lines[i + 1])
        if rel:
            out.add(rel)
    return out


def _git_apply_recount_check(
    workspace_root: Path,
    patch_text: str,
    ws_flags: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        suffix=".patch",
        delete=False,
    ) as patch_file:
        patch_file.write(patch_text)
        patch_path = Path(patch_file.name)
    try:
        return subprocess.run(
            ["git", "apply", "--recount", *ws_flags, "--check", str(patch_path)],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            timeout=15,
        )
    finally:
        patch_path.unlink(missing_ok=True)


def _git_apply_recount(
    workspace_root: Path,
    patch_text: str,
    ws_flags: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        suffix=".patch",
        delete=False,
    ) as patch_file:
        patch_file.write(patch_text)
        patch_path = Path(patch_file.name)
    try:
        return subprocess.run(
            ["git", "apply", "--recount", *ws_flags, str(patch_path)],
            cwd=workspace_root,
            capture_output=True,
            text=True,
            timeout=15,
        )
    finally:
        patch_path.unlink(missing_ok=True)


def _pick_apply_workspace_root_and_candidate(
    *,
    unified_diff: str,
    changed_files: list[dict[str, Any]],
    patch_candidates: list[str],
    check_failures: list[str],
    require_existing_targets: bool = True,
) -> tuple[Path, str, tuple[str, ...]] | None:
    """First (root, candidate, ws_flags) where ``git apply --check`` passes.

    When ``require_existing_targets`` is True (execute-approved), paths that are
    **modified** (must already exist) are checked on disk under the candidate root
    so stale modify hunks against the wrong workspace fail early.

    Paths that appear only as **new file** targets (``--- /dev/null`` … ``+++ b/``)
    are exempt from that existence check so approved ``/dev/null`` adds can apply.

    Preview / dry-run checks pass ``False`` so ``new file`` hunks can still run
    ``git apply --check`` against a repo root even before the blob exists.
    """
    rels = _rels_for_apply(changed_files, unified_diff)
    new_file_only = _new_file_relpaths_from_unified_diff(unified_diff)
    rels_must_exist = [r for r in rels if r.replace("\\", "/") not in new_file_only]
    for root in _ordered_workspace_roots_for_apply():
        root = root.resolve()
        if require_existing_targets and rels_must_exist:
            missing: list[str] = []
            for rel in rels_must_exist:
                norm = rel.replace("\\", "/")
                if not (root / norm).is_file():
                    missing.append(norm)
            if missing:
                check_failures.append(
                    f"{root}: skipped — target file(s) not found under this root "
                    f"(require_existing_targets): {missing!r}",
                )
                continue
        for file in changed_files:
            rel_path = str(file.get("path") or "").strip()
            if not rel_path:
                continue
            resolved = (root / rel_path).resolve()
            if not _is_relative_to(resolved, root):
                check_failures.append(
                    f"{root}: path escape for {rel_path}",
                )
                break
        else:
            for candidate in patch_candidates:
                for flags in _GIT_APPLY_FLAG_CHAINS:
                    check = _git_apply_recount_check(root, candidate, flags)
                    if check.returncode != 0:
                        flag_note = ",".join(flags) or "default"
                        check_failures.append(
                            f"{root}: flags={flag_note} {check.stderr.strip() or 'git apply --check failed'}",
                        )
                        continue
                    return root, candidate, flags
    return None


def git_apply_check_for_preview(
    unified_diff: str,
    changed_files: list[dict[str, Any]],
) -> tuple[bool, str]:
    """Dry-run ``git apply --check`` for approval gating (read-only).

    Uses ``require_existing_targets=False`` so ``new file`` patches can be checked
    before the destination blob exists on disk.
    """
    roots = _ordered_workspace_roots_for_apply()
    changed_files, unified_diff, _did_remap = _normalize_next_app_router_diff_targets(
        roots,
        [dict(x) for x in changed_files],
        unified_diff,
    )
    patch_candidates = diff_candidates_for_git_apply(unified_diff)
    if not patch_candidates:
        patch_candidates = [unified_diff]
    check_failures: list[str] = []
    picked = _pick_apply_workspace_root_and_candidate(
        unified_diff=unified_diff,
        changed_files=changed_files,
        patch_candidates=patch_candidates,
        check_failures=check_failures,
        require_existing_targets=False,
    )
    if picked is not None:
        return True, ""
    tail = (
        check_failures[-1]
        if check_failures
        else "git apply --check did not succeed for any workspace root or patch variant."
    )
    return False, tail


MAX_LONG_TASKS = 50
MAX_CYCLES = 5
TRUNCATED_TEST_RESULTS_LIMIT = 1500
# â”€â”€ Coder Agent (repomix-assisted) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
# Repomix bundles are the read-only source for coder context assembly.
REPOMIX_BUNDLE_NAMES: tuple[str, ...] = ("repomix-output.ast.xml", "repomix-output.xml")
USER_APP_FORBIDDEN_PATHS: tuple[str, ...] = (
    "source_proxy/",
    "src/components/coding/",
    "src/lib/coding/",
    "src/lib/spirit/apply-unified-diff.ts",
    "scripts/",
    "masterProxyPlan.md",
    "masterSwarmPlan.md",
    "notes.md",
)
AGENT_INTERNAL_FORBIDDEN_PATHS: tuple[str, ...] = (
    "src/app/",
    "src/components/dashboard/",
    "src/components/chat/",
    "public/",
    "backend/searxng_data/",
)
ContextMode = Literal["user_app", "agent_internal"]
CODER_SYSTEM_PROMPT = """You are Codex, an expert senior full-stack React/TypeScript/Tailwind engineer working inside SpiritOS.

You are given repomix-backed workspace context for SpiritOS.

TASK:
{task}

Target file: {file_path}

ACCEPTANCE CRITERIA EXTRACTED FROM TASK:
{acceptance_criteria}

SUBJECTIVE IMPROVEMENT CONTRACT:
{subjective_improvement_contract}

CURRENT FILE CONTENT (slice from repomix / disk when available):
{repomix_file_content}

DETERMINISTIC TASK CONTRACT:
{task_contract}

INSTRUCTIONS (NEVER violate):
- Make the minimal, precise change needed to complete the task.
- You are not allowed to return generic placeholder scaffolds for implementation tasks.
- You must satisfy exact user requirements.
- You are not writing a patch or unified diff.
- You are writing the complete final content for exactly one target file.
- Return strict JSON only. Do not wrap it in markdown unless using a single ```json fence.
- Include all imports needed by the final file.
- Use only real repo components and imports from context.
- Do not include explanations.
- Before outputting JSON, verify:
  1. target path matches the explicit Target file line, when present
  2. route path maps correctly if this is a Next App Router page
  3. all quoted UI text from the user appears exactly if requested
  4. all requested className fragments appear exactly if requested
  5. required existing components are imported from real repo paths
  6. TSX is syntactically valid
  7. no raw task text appears in code
  8. content is the full replacement file, not a diff hunk

Return exactly one of these JSON shapes:
{{"action":"replace_file","target":"{file_path}","content":"FULL FILE CONTENT HERE","notes":"short optional note"}}
{{"action":"blocked","reason_code":"coder_needs_context","reason":"Cannot produce safe file content because ...","needed_context":["specific file or check needed"]}}

Return the JSON now.
"""
DEFAULT_SQLITE_PATH = Path("data") / "long_running_tasks.sqlite3"
DEFAULT_AUDIT_LOG_PATH = Path("data") / "approved_actions.audit.jsonl"
SwarmAgentRole = Literal["architect", "coder", "debugger"]
DEFAULT_STEPS = [
    "Capture task scope.",
    "Collect safe context.",
    "Prepare verification plan.",
    "Wait for explicit execution path.",
]


class LongRunningTaskError(ValueError):
    def __init__(self, message: str, reason_code: str) -> None:
        super().__init__(message)
        self.reason_code = reason_code


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class LongRunningTask:
    description: str
    id: str = field(default_factory=lambda: f"task_{uuid4().hex[:12]}")
    status: str = "queued"
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    cancelled_at: str | None = None
    steps: list[str] = field(default_factory=lambda: list(DEFAULT_STEPS))
    poll_count: int = 0
    ast_snapshot: Any | None = None
    open_diffs: list[dict[str, Any]] = field(default_factory=list)
    truncated_test_results: str = ""
    current_agent_role: SwarmAgentRole = "architect"
    cycle_count: int = 0
    architect_status: str = "idle"
    architect_reason: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "cancelled_at": self.cancelled_at,
            "steps": self.steps,
            "poll_count": self.poll_count,
            "progress": self.progress,
            "ast_snapshot": self.ast_snapshot,
            "open_diffs": self.open_diffs,
            "truncated_test_results": self.truncated_test_results,
            "current_agent_role": self.current_agent_role,
            "role_transitions": (
                self.ast_snapshot.get("role_transitions", [])
                if isinstance(self.ast_snapshot, dict)
                else []
            ),
            "cycle_count": self.cycle_count,
            "architect_status": self.architect_status,
            "architect_reason": self.architect_reason,
            "would_execute": _has_approved_execution(self.open_diffs),
            "writes_allowed": _has_approved_execution(self.open_diffs),
            "next_action": self.next_action,
        }

    @property
    def progress(self) -> int:
        if self.status == "cancelled":
            return 0
        if self.status in {"blocked", "blocked_after_retries", "blocked_by_review", "needs_context", "coder_config_blocked"}:
            if self.current_agent_role == "coder" and not _has_approved_execution(self.open_diffs):
                return 50
            return min(75, max(25, self.poll_count * 25))
        if self.status == "failed_needs_human":
            return min(95, self.cycle_count * 18)
        if self.status == "applied_verification_failed":
            return 95
        if self.status == "applied_needs_verification":
            return 92
        if self.status == "completed":
            return 100
        return min(90, self.poll_count * 25)

    @property
    def next_action(self) -> str:
        if self.status == "cancelled":
            return "Task was cancelled. Start a new task with narrower scope if needed."
        if self.status == "needs_context":
            return "Coder needs a valid Architect CoderPacket with target context before it can produce a diff."
        if self.status == "coder_config_blocked":
            return (
                "Coder model is not configured or the alias is unavailable. "
                "Set SOURCE_PROXY_CODER_MODEL_ALIAS to a valid enabled alias, then retry."
            )
        if self.status == "blocked_by_review":
            return "Deterministic review blocked the proposed diff. Regenerate the patch before approval."
        if self.status == "blocked_after_retries":
            return "Reviewer blocked the generated diff after bounded Coder retries. No approval action is available."
        if self.status == "blocked":
            if self.architect_status == "blocked" and self.current_agent_role == "architect":
                return (
                    f"Planning blocked ({self.architect_reason or 'unknown'}). "
                    "Fix the task target, proxy model configuration, or timeout settings and retry."
                )
            return "Coder did not produce an approvable diff. Regenerate the plan, retry Coder, or use a manual/cloud route."
        if self.status == "failed_needs_human":
            return "The swarm hit the safety cycle limit. Review the latest diff and sandbox output manually."
        if self.status == "applied_verification_failed":
            return "Approved diff was applied, but verification failed. Generate a fix prompt from the verification error."
        if self.status == "applied_needs_verification":
            verification = _current_post_apply_verification(self)
            if isinstance(verification, dict) and verification.get("docs_only"):
                return "Docs-only verification ready. Complete the manual checklist before marking the task done."
            return "Approved diff was applied. Automated verification for code changes will be handled in Phase 2B."
        if self.status == "completed":
            if _has_approved_execution(self.open_diffs):
                return "Approved execution finished and verification is complete."
            verification = _current_post_apply_verification(self)
            if isinstance(verification, dict) and verification.get("status") == "verified":
                return "Verification complete."
            return "Review the plan and choose an approved execution path."
        return "Poll again or cancel before any execution is allowed."


_tasks: dict[str, LongRunningTask] = {}


def create_long_running_task(
    description: str,
    steps: list[str] | None = None,
) -> dict[str, Any]:
    normalized_description = _normalize_task_description(description)
    if not normalized_description:
        raise LongRunningTaskError("Task description is required.", "empty_description")

    if len(_tasks) >= MAX_LONG_TASKS:
        oldest_id = next(iter(_tasks))
        _tasks.pop(oldest_id, None)

    task = LongRunningTask(description=normalized_description)
    if steps:
        task.steps = [step.strip() for step in steps if step.strip()][:12] or list(
            DEFAULT_STEPS
        )
    _reset_task_focus(task)
    _tasks[task.id] = task
    _save_task(task)
    _prune_old_tasks()
    return _task_envelope(task)


def _normalize_task_description(description: str) -> str:
    return "\n".join(
        " ".join(line.strip().split())
        for line in description.strip().splitlines()
        if line.strip()
    )


def get_long_running_task(task_id: str) -> dict[str, Any]:
    task = _lookup_task(task_id)
    if task.status not in _terminal_or_waiting_statuses():
        task.poll_count += 1
        task.status = (
            "running"
            if _task_is_waiting_for_coder_output(task)
            else "completed" if task.poll_count >= 4 else "running"
        )
        task.updated_at = _now_iso()
        _save_task(task)
    return _task_envelope(task)


def _task_is_waiting_for_coder_output(task: LongRunningTask) -> bool:
    return (
        task.current_agent_role == "coder"
        and task.architect_status == "planned"
        and not task.open_diffs
    )


def get_long_running_task_snapshot(task_id: str) -> dict[str, Any]:
    task = _lookup_task(task_id)
    return _task_envelope(task)


def advance_long_running_task(
    task_id: str,
    *,
    proposed_diff: str | None = None,
    sandbox_result: dict[str, Any] | None = None,
    test_command: list[str] | None = None,
) -> dict[str, Any]:
    task = _lookup_task(task_id)
    if task.status in _terminal_or_waiting_statuses():
        return _task_envelope(task)

    if task.current_agent_role == "architect":
        _run_architect_handoff(task)
    elif task.current_agent_role == "coder":
        _run_coder_handoff(task, proposed_diff=proposed_diff, test_command=test_command)
    else:
        _run_debugger_handoff(task, sandbox_result=sandbox_result)

    task.updated_at = _now_iso()
    _save_task(task)
    return _task_envelope(task)


def execute_approved_long_running_task(
    task_id: str,
    *,
    approved_diff: str,
    action: str,
    target: str | None = None,
    approved_by: str = "human",
    test_command: list[str] | None = None,
) -> dict[str, Any]:
    """Apply a user-approved diff after the same read-only safety preview passes.

    This is the one-way bridge from Approval Gate to execution: callers must pass
    explicit approval intent, and this function still fails closed on blocked
    paths before any workspace write occurs.
    """
    task = _lookup_task(task_id)
    from source_proxy.planning.plan import load_plan

    architect_plan = load_plan(task_id)
    verification = preview_diff_verification(
        approved_diff,
        test_command=test_command,
        task_text=task.description,
        architect_plan=architect_plan,
    )
    if verification["status"] == "blocked":
        raise LongRunningTaskError(
            "Approved diff was blocked by safety verification.",
            "approved_diff_blocked",
        )

    task.status = "executing"
    _set_task_role(task, "debugger", reason="human_approved_execution")
    task.poll_count = max(task.poll_count, 3)
    task.steps = _append_unique_steps(
        task.steps,
        [
            "Human approved the reviewed action.",
            "Execution layer re-ran diff safety checks.",
            "Applying the approved diff to the workspace.",
        ],
    )
    task.open_diffs.append(
        {
            "diff": approved_diff,
            "status": "executing",
            "risk": verification["risk"],
            "changed_files": verification["changed_files"],
            "blocked_reasons": verification["blocked_reasons"],
            "suggested_commands": verification["suggested_commands"],
        }
    )
    task.updated_at = _now_iso()
    _save_task(task)

    try:
        apply_result = _apply_verified_diff(approved_diff, verification)
    except LongRunningTaskError:
        task.status = "failed_needs_human"
        task.truncated_test_results = "Approved diff failed during workspace application."
        task.updated_at = _now_iso()
        _save_task(task)
        raise

    audit_record = {
        "action": action,
        "approved_at": _now_iso(),
        "approved_by": approved_by,
        "changed_files": [file["path"] for file in verification["changed_files"]],
        "risk": verification["risk"],
        "target": target,
        "task_id": task.id,
    }
    _append_audit_log(audit_record)

    task.status = "applied_needs_verification"
    _set_task_role(task, "debugger", reason="approved_diff_applied")
    post_apply_verification = _initial_post_apply_verification(verification)
    for diff in task.open_diffs:
        if diff.get("status") == "executing":
            diff["status"] = "applied_needs_verification"
            diff["verification_required"] = True
            diff["post_apply_verification"] = post_apply_verification
    task.truncated_test_results = json.dumps(
        {
            "audit": audit_record,
            "backup_root": apply_result["backup_root"],
            "post_apply_verification": post_apply_verification,
            "verification_plan": verification["verification_plan"],
        },
        indent=2,
    )
    task.steps = _append_unique_steps(
        task.steps,
        [
            "Approved diff applied with backups captured.",
            "Status is applied_needs_verification until post-apply verification is explicitly completed.",
        ],
    )
    task.updated_at = _now_iso()
    _save_task(task)
    payload = _task_envelope(task)
    payload["execution"] = {
        "ok": True,
        "action": action,
        "applied_at": audit_record["approved_at"],
        "audit": audit_record,
        "backup_root": apply_result["backup_root"],
        "changed_files": verification["changed_files"],
        "message": "Approved diff applied after safety verification; post-apply verification is required before completion.",
        "post_apply_verification": post_apply_verification,
        "risk": verification["risk"],
        "status": task.status,
        "target": target,
        "verification_plan": verification["verification_plan"],
    }
    return payload


PLAN_REJECTION_REASON_CODES = {
    "wrong_target",
    "wrong_approach",
    "missing_constraint",
    "style_violation",
    "other",
}


def reject_long_running_task_plan(
    task_id: str,
    *,
    reason_code: str,
    details: str = "",
    rejected_by: str = "human",
) -> dict[str, Any]:
    """Persist structured rejection feedback and regenerate the Architect plan."""
    normalized_reason = reason_code.strip().lower()
    if normalized_reason not in PLAN_REJECTION_REASON_CODES:
        raise LongRunningTaskError("Unknown plan rejection reason.", "invalid_rejection_reason")

    from source_proxy.planning.plan import load_plan

    task = _lookup_task(task_id)
    plan = load_plan(task_id)
    plan_id = getattr(plan, "plan_id", "") if plan is not None else ""
    packet = getattr(plan, "coder_packet", None)
    target_file = getattr(packet, "target_file", None)
    target = str(getattr(target_file, "path", "") or "")
    now = _now_iso()
    rejection = {
        "details": details.strip()[:1000],
        "plan_id": plan_id,
        "reason_code": normalized_reason,
        "rejected_at": now,
        "rejected_by": rejected_by,
        "target": target,
    }

    snapshot = task.ast_snapshot if isinstance(task.ast_snapshot, dict) else {}
    prior_rejections = snapshot.get("plan_rejections")
    if not isinstance(prior_rejections, list):
        prior_rejections = []
    snapshot["plan_rejections"] = [*prior_rejections, rejection]
    task.ast_snapshot = snapshot
    task.status = "running"
    _set_task_role(task, "architect", reason="human_rejected_plan")
    task.architect_status = "rejected"
    task.architect_reason = normalized_reason
    task.cycle_count += 1
    task.steps = _append_unique_steps(
        task.steps,
        [
            f"Human rejected Architect plan: {normalized_reason}.",
            "Architect regenerates the plan with rejection feedback.",
        ],
    )

    _append_audit_log(
        {
            "event": "plan_rejected",
            "task_id": task.id,
            "plan_id": plan_id,
            "target": target,
            "reason_code": normalized_reason,
            "details": rejection["details"],
            "rejected_at": now,
            "rejected_by": rejected_by,
        }
    )
    _run_architect_handoff(task)
    task.updated_at = _now_iso()
    _save_task(task)
    payload = _task_envelope(task)
    payload["rejection"] = rejection
    payload["message"] = (
        "Plan will be regenerated with this feedback."
        if normalized_reason != "other"
        else "Plan rejection recorded."
    )
    return payload


def record_post_apply_verification(
    task_id: str,
    *,
    checks: list[dict[str, Any]] | None = None,
    confirm_backup_audit_present: bool = False,
    confirm_changed_files_reviewed: bool = False,
    confirm_expected_change_present: bool = False,
    confirm_no_unintended_files: bool = False,
    manual_browser_check_done: bool = False,
    skip_reason: str | None = None,
    verification_note: str | None = None,
) -> dict[str, Any]:
    task = _lookup_task(task_id)
    if task.status != "applied_needs_verification":
        raise LongRunningTaskError(
            "Post-apply verification can only be completed from applied_needs_verification.",
            "invalid_post_apply_verification_state",
        )

    verification = _current_post_apply_verification(task)
    if verification is None:
        raise LongRunningTaskError(
            "Post-apply verification data is missing.",
            "post_apply_verification_missing",
        )
    if verification.get("required") is not True:
        raise LongRunningTaskError(
            "Post-apply verification is not marked required for this task.",
            "post_apply_verification_not_required",
        )
    changed_files = _verification_changed_files(verification, task)
    docs_only = _docs_only_changed_files(changed_files)
    skip = (skip_reason or "").strip()

    confirmations = {
        "file_changed_as_expected": bool(
            confirm_expected_change_present or confirm_changed_files_reviewed
        ),
        "no_unintended_files": bool(confirm_no_unintended_files),
        "backup_audit_present": bool(
            confirm_backup_audit_present and _post_apply_has_backup_audit(task)
        ),
    }

    incoming = checks or []
    by_id = {str(check.get("id") or check.get("command") or ""): check for check in incoming}
    updated_checks = []
    any_failed = False
    for check in verification.get("checks", []):
        check_id = str(check.get("id") or "")
        incoming_check = by_id.get(check_id)
        if incoming_check:
            status = str(incoming_check.get("status") or "").strip().lower()
            if status in {"passed", "failed", "skipped"}:
                check["status"] = status
            if incoming_check.get("summary"):
                check["summary"] = str(incoming_check["summary"])
        if check.get("required") and check.get("status") == "failed":
            any_failed = True
        updated_checks.append(check)

    if not any_failed:
        if not docs_only and not skip:
            raise LongRunningTaskError(
                "Docs-only verification cannot complete a task with code changes. Automated verification for code changes will be handled in Phase 2B.",
                "code_verification_not_implemented",
            )
        if docs_only:
            missing = [
                name for name, confirmed in confirmations.items() if not confirmed
            ]
            if missing:
                raise LongRunningTaskError(
                    "Required docs-only verification confirmations are missing: "
                    + ", ".join(missing),
                    "missing_post_apply_confirmations",
                )

    verification["checks"] = updated_checks
    verification["docs_only_confirmations"] = confirmations
    verification["docs_only"] = docs_only
    verification["manual_browser_check_done"] = bool(manual_browser_check_done)
    if skip_reason is not None:
        verification["skip_reason"] = skip
    if verification_note is not None:
        verification["verification_note"] = verification_note.strip()
    verification["updated_at"] = _now_iso()

    required_checks = [check for check in updated_checks if check.get("required")]
    all_required_done = all(
        check.get("status") == "passed"
        or (check.get("status") == "skipped" and verification.get("skip_reason"))
        for check in required_checks
    )
    browser_required = bool(verification.get("manual_browser_check_required"))
    browser_done = bool(verification.get("manual_browser_check_done")) or bool(
        verification.get("skip_reason")
    )

    if any_failed:
        verification["status"] = "failed"
        task.status = "applied_verification_failed"
    elif all_required_done and (not browser_required or browser_done):
        verification["status"] = "verified"
        task.status = "completed"
        task.steps = _append_unique_steps(
            task.steps,
            ["Post-apply verification completed."],
        )
    else:
        verification["status"] = "verification_ready"
        task.status = "applied_needs_verification"

    for diff in task.open_diffs:
        if str(diff.get("status") or "").startswith("applied"):
            diff["status"] = task.status if task.status != "completed" else "verified"
            diff["post_apply_verification"] = verification
            diff["verified"] = task.status == "completed"

    task.truncated_test_results = _post_apply_results_json(task, verification)
    snapshot = task.ast_snapshot if isinstance(task.ast_snapshot, dict) else {}
    snapshot["post_apply_verification"] = verification
    task.ast_snapshot = snapshot
    task.updated_at = _now_iso()
    _save_task(task)
    return _task_envelope(task)


def _current_post_apply_verification(task: LongRunningTask) -> dict[str, Any] | None:
    for diff in reversed(task.open_diffs):
        if diff.get("status") not in {
            "applied_needs_verification",
            "applied_verification_failed",
            "verified",
        }:
            continue
        verification = diff.get("post_apply_verification")
        if isinstance(verification, dict):
            return verification
    snapshot = task.ast_snapshot if isinstance(task.ast_snapshot, dict) else {}
    verification = snapshot.get("post_apply_verification")
    if isinstance(verification, dict):
        return verification
    return None


def _changed_files_from_task(task: LongRunningTask) -> list[dict[str, Any]]:
    for diff in reversed(task.open_diffs):
        changed_files = diff.get("changed_files")
        if isinstance(changed_files, list):
            return [file for file in changed_files if isinstance(file, dict)]
    return []


def _verification_changed_files(
    verification: dict[str, Any],
    task: LongRunningTask,
) -> list[dict[str, Any]]:
    changed_files = verification.get("changed_files")
    if isinstance(changed_files, list):
        return [file for file in changed_files if isinstance(file, dict)]
    return _changed_files_from_task(task)


def _docs_only_changed_files(changed_files: list[dict[str, Any]]) -> bool:
    if not changed_files:
        return False
    docs_extensions = {".md", ".mdx"}
    for file in changed_files:
        path = str(file.get("path") or "").replace("\\", "/").lower()
        if not path:
            return False
        if Path(path).suffix in docs_extensions:
            continue
        return False
    return True


def _post_apply_results_json(
    task: LongRunningTask,
    verification: dict[str, Any],
) -> str:
    try:
        prior = json.loads(task.truncated_test_results or "{}")
    except json.JSONDecodeError:
        prior = {}
    if not isinstance(prior, dict):
        prior = {}
    prior["post_apply_verification"] = verification
    return json.dumps(prior, indent=2)


def _post_apply_has_backup_audit(task: LongRunningTask) -> bool:
    try:
        prior = json.loads(task.truncated_test_results or "{}")
    except json.JSONDecodeError:
        return False
    if not isinstance(prior, dict):
        return False
    return isinstance(prior.get("audit"), dict) and bool(prior.get("backup_root"))


def _initial_post_apply_verification(verification: dict[str, Any]) -> dict[str, Any]:
    changed_files = [
        file for file in verification.get("changed_files", []) if isinstance(file, dict)
    ]
    suggested_commands = [
        item for item in verification.get("suggested_commands", []) if isinstance(item, dict)
    ]
    ts_changed = any(
        str(file.get("path") or "").lower().endswith((".ts", ".tsx"))
        for file in changed_files
    )
    route_or_ui_changed = any(
        str(file.get("path") or "").replace("\\", "/").startswith("src/app/")
        or str(file.get("path") or "").lower().endswith((".tsx", ".jsx", ".css"))
        for file in changed_files
    )
    docs_only = _docs_only_changed_files(changed_files)

    checks: list[dict[str, Any]] = []
    if ts_changed:
        checks.append(
            {
                "id": "typecheck",
                "command": ["npm", "run", "typecheck"],
                "required": True,
                "status": "pending",
                "summary": "TypeScript or JavaScript files changed.",
            }
        )
    for item in suggested_commands:
        command = item.get("command")
        if not isinstance(command, list) or not command:
            continue
        command_text = " ".join(str(part) for part in command)
        check_id = "lint" if "eslint" in command_text else command_text
        if any(check.get("id") == check_id for check in checks):
            continue
        checks.append(
            {
                "id": check_id,
                "command": [str(part) for part in command],
                "required": "eslint" in command_text,
                "status": "pending",
                "summary": str(item.get("reason") or "Suggested verification command."),
            }
        )

    return {
        "checks": checks,
        "changed_files": changed_files,
        "docs_only": docs_only,
        "docs_only_confirmations": {
            "backup_audit_present": False,
            "file_changed_as_expected": False,
            "no_unintended_files": False,
        },
        "manual_browser_check_done": False,
        "manual_browser_check_required": route_or_ui_changed,
        "required": True,
        "skip_reason": "",
        "status": "verification_ready",
        "updated_at": _now_iso(),
        "verification_note": "",
    }


def cancel_long_running_task(task_id: str) -> dict[str, Any]:
    task = _lookup_task(task_id)
    if task.status not in _terminal_or_waiting_statuses():
        task.status = "cancelled"
        task.cancelled_at = _now_iso()
        task.updated_at = task.cancelled_at
        _save_task(task)
    return _task_envelope(task)


def reset_long_running_tasks() -> None:
    _tasks.clear()
    _delete_persisted_tasks()


def update_long_running_task(task_id: str, **changes: Any) -> dict[str, Any]:
    task = _lookup_task(task_id)
    for key, value in changes.items():
        if not hasattr(task, key):
            raise LongRunningTaskError(
                f"Long-running task field is not supported: {key}",
                "unsupported_field",
            )
        if key == "current_agent_role":
            _set_task_role(
                task,
                _normalize_agent_role(str(value)),
                reason="manual_task_update",
            )
            continue
        setattr(task, key, value)
    task.updated_at = _now_iso()
    _save_task(task)
    return _task_envelope(task)


def _reset_task_focus(task: LongRunningTask) -> None:
    task.ast_snapshot = None
    task.open_diffs = []
    task.truncated_test_results = ""
    task.current_agent_role = "architect"
    task.cycle_count = 0
    task.architect_status = "idle"
    task.architect_reason = ""


def _lookup_task(task_id: str) -> LongRunningTask:
    task = _tasks.get(task_id)
    if task is None:
        task = _load_task(task_id)
    if task is None:
        raise LongRunningTaskError("Long-running task was not found.", "not_found")
    _tasks[task.id] = task
    return task


def _task_envelope(task: LongRunningTask) -> dict[str, Any]:
    payload = task.to_payload()
    payload["post_apply_verification"] = _current_post_apply_verification(task)
    return {
        "tool": "long_running_task_tracker",
        "access_scope": "read_only_task_status_tracking",
        "task": payload,
        "limits": {
            "executes_commands": False,
            "writes_files": False,
            "persists_across_restart": True,
            "max_tracked_tasks": MAX_LONG_TASKS,
            "max_cycles": MAX_CYCLES,
        },
    }


def _ensure_ast_snapshot_dict(task: LongRunningTask) -> dict[str, Any]:
    if isinstance(task.ast_snapshot, dict):
        return task.ast_snapshot
    task.ast_snapshot = {}
    return task.ast_snapshot


def _role_transitions_for_task(task: LongRunningTask) -> list[dict[str, Any]]:
    snapshot = task.ast_snapshot if isinstance(task.ast_snapshot, dict) else {}
    transitions = snapshot.get("role_transitions")
    if not isinstance(transitions, list):
        return []
    return [item for item in transitions if isinstance(item, dict)]


def _set_task_role(
    task: LongRunningTask,
    role: SwarmAgentRole,
    *,
    reason: str,
) -> None:
    previous = _normalize_agent_role(task.current_agent_role)
    next_role = _normalize_agent_role(role)
    task.current_agent_role = next_role
    if previous == next_role:
        return
    snapshot = _ensure_ast_snapshot_dict(task)
    transitions = snapshot.get("role_transitions")
    if not isinstance(transitions, list):
        transitions = []
    transitions.append(
        {
            "at": _now_iso(),
            "from": previous,
            "to": next_role,
            "reason": reason,
        }
    )
    snapshot["role_transitions"] = transitions[-100:]
    task.ast_snapshot = snapshot


def _append_unique_steps(current_steps: list[str], next_steps: list[str]) -> list[str]:
    merged = list(current_steps)
    for step in next_steps:
        if step not in merged:
            merged.append(step)
    return merged[:12]


def _has_approved_execution(open_diffs: list[dict[str, Any]]) -> bool:
    return any(
        str(diff.get("status") or "")
        in {
            "executing",
            "applied",
            "applied_needs_verification",
            "applied_verification_failed",
            "verified",
        }
        for diff in open_diffs
    )


def _terminal_or_waiting_statuses() -> set[str]:
    return {
        "blocked",
        "blocked_after_retries",
        "blocked_by_review",
        "cancelled",
        "completed",
        "coder_config_blocked",
        "failed_needs_human",
        "needs_context",
        "applied_needs_verification",
        "applied_verification_failed",
    }


def _first_target_rel_from_changed_or_diff(
    changed_files: list[dict[str, Any]],
    unified_diff: str,
) -> str | None:
    if changed_files:
        p = str(changed_files[0].get("path") or "").strip().replace("\\", "/")
        return p or None
    for raw_line in unified_diff.replace("\r\n", "\n").splitlines():
        if raw_line.startswith("+++ b/"):
            return raw_line[6:].strip() or None
    return None


def _read_text_first_line(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    lines = text.splitlines()
    return lines[0] if lines else ""


def _first_space_prefixed_line_in_first_hunk(diff: str, rel_posix: str) -> str | None:
    """First unified-diff context line (`` `` prefix) after the first ``@@`` for ``rel_posix``."""
    norm = rel_posix.replace("\\", "/")
    lines = diff.replace("\r\n", "\n").splitlines()
    i = 0
    while i < len(lines):
        if lines[i].startswith("+++ b/"):
            path = lines[i][6:].strip()
            if path != norm and not path.endswith(norm):
                i += 1
                continue
            i += 1
            while i < len(lines) and not lines[i].startswith("@@"):
                i += 1
            if i >= len(lines):
                return None
            i += 1
            while i < len(lines):
                ln = lines[i]
                if ln.startswith("diff --git "):
                    return None
                if ln.startswith("@@ "):
                    break
                if ln.startswith(" ") and len(ln) >= 1:
                    return ln[1:] if len(ln) > 1 else ""
                i += 1
            return None
        i += 1
    return None


def _apply_verified_diff(
    unified_diff: str,
    verification: dict[str, Any],
) -> dict[str, Any]:
    raw_cf = verification.get("changed_files") or []
    changed_files = [dict(x) for x in raw_cf if isinstance(x, dict)]
    roots = _ordered_workspace_roots_for_apply()
    changed_files, unified_diff, _did_remap = _normalize_next_app_router_diff_targets(
        roots,
        changed_files,
        unified_diff,
    )
    patch_candidates = diff_candidates_for_git_apply(unified_diff)
    if not patch_candidates:
        patch_candidates = [unified_diff]

    check_failures: list[str] = []
    apply_failures: list[str] = []

    picked = _pick_apply_workspace_root_and_candidate(
        unified_diff=unified_diff,
        changed_files=changed_files,
        patch_candidates=patch_candidates,
        check_failures=check_failures,
        require_existing_targets=True,
    )

    if picked is None:
        workspace_root = _workspace_root().resolve()
        rel = _first_target_rel_from_changed_or_diff(changed_files, unified_diff)
        target_path = (workspace_root / rel.replace("\\", "/")) if rel else None
        disk_first = _read_text_first_line(target_path) if target_path else None
        ctx_line = _first_space_prefixed_line_in_first_hunk(unified_diff, rel) if rel else None
        spirit_first = os.getenv("SPIRIT_PROJECT_PATH", "").strip().split(",")[0].strip()
        roots_tried = [str(p) for p in _ordered_workspace_roots_for_apply()]
        ctx_matches = None
        if disk_first is not None and ctx_line is not None:
            ctx_matches = disk_first == ctx_line
        hint_parts: list[str] = []
        hint_parts.append(f"workspace_root={workspace_root}")
        hint_parts.append(f"roots_tried={repr(roots_tried)[:400]}")
        if spirit_first:
            hint_parts.append(f"SPIRIT_PROJECT_PATH[0]={spirit_first!r}")
        for bad in _configured_apply_roots_missing_mounts()[:8]:
            hint_parts.append(
                f"Configured project root not found on this host (fix mount or path): {bad!r}",
            )
        route_hint = _next_app_router_route_hint(workspace_root, rel)
        if route_hint:
            hint_parts.append(route_hint)
        if rel:
            hint_parts.append(f"target={rel!r}")
        if disk_first is not None:
            hint_parts.append(f"disk_line1={disk_first[:120]!r}")
        if ctx_line is not None:
            hint_parts.append(f"patch_first_ctx={ctx_line[:120]!r}")
        if ctx_matches is False:
            hint_parts.append("first_hunk_context!=disk_line1 (stale diff or wrong file)")
        elif ctx_matches is True:
            hint_parts.append(
                "line1_ctx_ok_but_apply_failed_mid_file (regenerate diff; git ws-only flags tried)",
            )
        hint = " | ".join(hint_parts)[:2000]

        if apply_failures:
            raise LongRunningTaskError(
                f"{apply_failures[-1]}\n{hint}".strip(),
                "diff_apply_failed",
            )
        last_msg = check_failures[-1] if check_failures else "No diff variants to try."
        raise LongRunningTaskError(f"{last_msg}\n{hint}".strip(), "diff_apply_check_failed")

    workspace_root, _winning, _win_ws = picked
    workspace_root = workspace_root.resolve()
    backup_root = _backup_root_for(workspace_root)
    backup_root.mkdir(parents=True, exist_ok=True)

    for file in changed_files:
        rel_path = str(file["path"])
        resolved = (workspace_root / rel_path).resolve()
        if not _is_relative_to(resolved, workspace_root):
            raise LongRunningTaskError(
                f"Approved diff path escapes the workspace: {rel_path}",
                "path_escape",
            )
        if resolved.exists() and resolved.is_file():
            backup_path = backup_root / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(resolved, backup_path)

    chosen: str | None = None
    for candidate in patch_candidates:
        for flags in _GIT_APPLY_FLAG_CHAINS:
            check = _git_apply_recount_check(workspace_root, candidate, flags)
            if check.returncode != 0:
                check_failures.append(
                    check.stderr.strip() or "Approved diff failed git apply --check.",
                )
                continue
            applied = _git_apply_recount(workspace_root, candidate, flags)
            if applied.returncode != 0:
                apply_failures.append(
                    applied.stderr.strip() or "Approved diff failed while applying.",
                )
                continue
            chosen = candidate
            break
        if chosen is not None:
            break

    if chosen is None:
        rel = _first_target_rel_from_changed_or_diff(changed_files, unified_diff)
        target_path = (workspace_root / rel.replace("\\", "/")) if rel else None
        disk_first = _read_text_first_line(target_path) if target_path else None
        ctx_line = _first_space_prefixed_line_in_first_hunk(unified_diff, rel) if rel else None
        spirit_first = os.getenv("SPIRIT_PROJECT_PATH", "").strip().split(",")[0].strip()
        roots_tried = [str(p) for p in _ordered_workspace_roots_for_apply()]
        ctx_matches = None
        if disk_first is not None and ctx_line is not None:
            ctx_matches = disk_first == ctx_line
        hint_parts: list[str] = []
        hint_parts.append(f"workspace_root={workspace_root}")
        hint_parts.append(f"roots_tried={repr(roots_tried)[:400]}")
        if spirit_first:
            hint_parts.append(f"SPIRIT_PROJECT_PATH[0]={spirit_first!r}")
        for bad in _configured_apply_roots_missing_mounts()[:8]:
            hint_parts.append(
                f"Configured project root not found on this host (fix mount or path): {bad!r}",
            )
        route_hint = _next_app_router_route_hint(workspace_root, rel)
        if route_hint:
            hint_parts.append(route_hint)
        if rel:
            hint_parts.append(f"target={rel!r}")
        if disk_first is not None:
            hint_parts.append(f"disk_line1={disk_first[:120]!r}")
        if ctx_line is not None:
            hint_parts.append(f"patch_first_ctx={ctx_line[:120]!r}")
        if ctx_matches is False:
            hint_parts.append("first_hunk_context!=disk_line1 (stale diff or wrong file)")
        elif ctx_matches is True:
            hint_parts.append(
                "line1_ctx_ok_but_apply_failed_mid_file (regenerate diff; git ws-only flags tried)",
            )
        hint = " | ".join(hint_parts)[:2000]

        if apply_failures:
            raise LongRunningTaskError(
                f"{apply_failures[-1]}\n{hint}".strip(),
                "diff_apply_failed",
            )
        last_msg = check_failures[-1] if check_failures else "No diff variants to try."
        raise LongRunningTaskError(f"{last_msg}\n{hint}".strip(), "diff_apply_check_failed")

    return {"backup_root": str(backup_root.relative_to(workspace_root)).replace("\\", "/")}


def _backup_root_for(workspace_root: Path) -> Path:
    applied_at = datetime.now(UTC).isoformat()
    day = applied_at[:10]
    stamp = applied_at.replace(":", "").replace("+", "_").replace(".", "_")
    return workspace_root.resolve() / ".spirit-backups" / day / f"approved-diff-{stamp}"


def _backup_root() -> Path:
    return _backup_root_for(_workspace_root())


def _append_audit_log(record: dict[str, Any]) -> None:
    audit_path = _audit_log_path()
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def _audit_log_path() -> Path:
    configured = os.getenv("SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG")
    if configured:
        return Path(configured)
    return _workspace_root() / DEFAULT_AUDIT_LOG_PATH


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _save_task(task: LongRunningTask) -> None:
    _apply_pre_save_hook(task)
    with closing(_connect()) as connection:
        _initialize_store(connection)
        connection.execute(
            """
            INSERT INTO long_running_tasks (
                id,
                description,
                status,
                created_at,
                updated_at,
                cancelled_at,
                steps_json,
                poll_count,
                ast_snapshot_json,
                open_diffs_json,
                truncated_test_results,
                current_agent_role,
                cycle_count,
                architect_status,
                architect_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                description = excluded.description,
                status = excluded.status,
                updated_at = excluded.updated_at,
                cancelled_at = excluded.cancelled_at,
                steps_json = excluded.steps_json,
                poll_count = excluded.poll_count,
                ast_snapshot_json = excluded.ast_snapshot_json,
                open_diffs_json = excluded.open_diffs_json,
                truncated_test_results = excluded.truncated_test_results,
                current_agent_role = excluded.current_agent_role,
                cycle_count = excluded.cycle_count,
                architect_status = excluded.architect_status,
                architect_reason = excluded.architect_reason
            """,
            (
                task.id,
                task.description,
                task.status,
                task.created_at,
                task.updated_at,
                task.cancelled_at,
                json.dumps(task.steps),
                task.poll_count,
                json.dumps(task.ast_snapshot),
                json.dumps(task.open_diffs),
                task.truncated_test_results,
                task.current_agent_role,
                task.cycle_count,
                task.architect_status,
                task.architect_reason,
            ),
        )
        connection.commit()


def _load_task(task_id: str) -> LongRunningTask | None:
    with closing(_connect()) as connection:
        _initialize_store(connection)
        row = connection.execute(
            """
            SELECT
                id,
                description,
                status,
                created_at,
                updated_at,
                cancelled_at,
                steps_json,
                poll_count,
                ast_snapshot_json,
                open_diffs_json,
                truncated_test_results,
                current_agent_role,
                cycle_count,
                architect_status,
                architect_reason
            FROM long_running_tasks
            WHERE id = ?
            """,
            (task_id,),
        ).fetchone()
    if row is None:
        return None

    return LongRunningTask(
        id=row["id"],
        description=row["description"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        cancelled_at=row["cancelled_at"],
        steps=_json_value(row["steps_json"], list(DEFAULT_STEPS)),
        poll_count=row["poll_count"],
        ast_snapshot=_json_value(row["ast_snapshot_json"], None),
        open_diffs=_json_value(row["open_diffs_json"], []),
        truncated_test_results=row["truncated_test_results"] or "",
        current_agent_role=_normalize_agent_role(row["current_agent_role"]),
        cycle_count=row["cycle_count"],
        architect_status=row["architect_status"] or "idle",
        architect_reason=row["architect_reason"] or "",
    )


def _run_architect_handoff(task: LongRunningTask) -> None:
    from source_proxy.planning.architect import (
        ArchitectLLMError,
        FallthroughToLLM,
        Plan,
        plan_markdown_append_deterministically,
        plan_task_deterministically,
        plan_task_with_llm,
    )
    from source_proxy.planning.plan import save_plan

    if task.ast_snapshot is None:
        task.ast_snapshot = {
            "task_id": task.id,
            "description": task.description,
            "captured_at": _now_iso(),
            "context_source": "long_running_task_blackboard",
        }
    if task.steps == DEFAULT_STEPS:
        task.steps = [
            "Architect captured task scope and context.",
            "Coder prepares a focused diff.",
            "Debugger verifies the diff in the sandbox.",
        ]
    rejection_feedback = _plan_rejections_for_task(task)
    use_feedback = any(item.get("reason_code") != "other" for item in rejection_feedback)
    result = (
        FallthroughToLLM("rejection_feedback")
        if use_feedback
        else plan_task_deterministically(task.description, task.id, _workspace_root())
    )
    if isinstance(result, Plan):
        save_plan(task.id, result.plan)
        task.architect_status = "planned"
        task.architect_reason = ""
        task.status = "running"
        _set_task_role(task, "coder", reason="architect_plan_ready")
        return
    if isinstance(result, FallthroughToLLM):
        try:
            llm_plan = plan_task_with_llm(
                task.description,
                task.id,
                _workspace_root(),
                rejection_feedback=rejection_feedback,
            )
        except ArchitectLLMError as error:
            fallback = plan_markdown_append_deterministically(
                task.description,
                task.id,
                _workspace_root(),
            )
            if error.reason_code == "architect_llm_timeout" and isinstance(fallback, Plan):
                save_plan(task.id, fallback.plan)
                task.architect_status = "planned"
                task.architect_reason = "deterministic_markdown_append_fallback"
                task.status = "running"
                _set_task_role(task, "coder", reason="architect_deterministic_fallback_ready")
                task.steps = _append_unique_steps(
                    task.steps,
                    [
                        f"Planning with LLM Architect: {result.reason}.",
                        "LLM Architect timed out; deterministic small Markdown append fallback produced a validated CoderPacket.",
                    ],
                )
                return
            task.architect_status = "blocked"
            task.architect_reason = error.reason_code
            task.status = "blocked"
            _set_task_role(task, "architect", reason="architect_llm_blocked")
            task.truncated_test_results = f"architect_llm_blocked: {error}"
            task.steps = _append_unique_steps(
                task.steps,
                [f"Planning with LLM Architect: {result.reason}.", f"LLM Architect blocked: {error.reason_code}."],
            )
            return
        save_plan(task.id, llm_plan)
        task.architect_status = "planned"
        task.architect_reason = result.reason
        task.status = "running"
        _set_task_role(task, "coder", reason="architect_plan_ready")
        task.steps = _append_unique_steps(
            task.steps,
            [f"Planning with LLM Architect: {result.reason}.", "LLM Architect produced a validated plan."],
        )
        return
    task.architect_status = "blocked"
    task.architect_reason = result.reason
    task.status = "blocked"
    _set_task_role(task, "architect", reason="architect_blocked")
    task.truncated_test_results = f"architect_blocked: {result.reason}"
    task.steps = _append_unique_steps(
        task.steps,
        [f"Architect blocked deterministic planning: {result.reason}."],
    )
    return


def _plan_rejections_for_task(task: LongRunningTask) -> list[dict[str, Any]]:
    snapshot = task.ast_snapshot if isinstance(task.ast_snapshot, dict) else {}
    rejections = snapshot.get("plan_rejections")
    if not isinstance(rejections, list):
        return []
    return [item for item in rejections if isinstance(item, dict)]


def _run_coder_handoff(
    task: LongRunningTask,
    *,
    proposed_diff: str | None,
    test_command: list[str] | None,
) -> None:
    if not proposed_diff:
        task.status = "running"
        return

    try:
        from source_proxy.planning.plan import load_plan

        architect_plan = load_plan(task.id)
        verification = preview_diff_verification(
            proposed_diff,
            test_command=test_command,
            task_text=task.description,
            architect_plan=architect_plan,
        )
    except DiffVerificationError as error:
        task.truncated_test_results = f"{error.reason_code}: {error}"
        _set_task_role(task, "coder", reason="coder_diff_verification_error")
        task.status = "running"
        return

    blocked_reason_codes = {
        str(reason.get("reason_code") or "")
        for reason in verification.get("blocked_reasons", [])
        if isinstance(reason, dict)
    }
    reviewer_blocked = verification.get("status") == "blocked" and any(
        code.startswith("review_") for code in blocked_reason_codes
    )
    verification_blocked = verification.get("status") == "blocked"
    diff_status = "blocked_by_review" if verification_blocked else "pending_verification"
    task.open_diffs.append(
        {
            "diff": proposed_diff,
            "status": diff_status,
            "risk": verification["risk"],
            "changed_files": verification["changed_files"],
            "blocked_reasons": verification["blocked_reasons"],
            "suggested_commands": verification["suggested_commands"],
        }
    )
    if verification_blocked:
        task.status = "blocked_by_review"
        prefix = (
            "deterministic_review_blocked"
            if reviewer_blocked
            else "diff_verification_blocked"
        )
        task.truncated_test_results = prefix + ": " + "; ".join(sorted(blocked_reason_codes))
        _set_task_role(task, "coder", reason=prefix)
        return
    task.status = "running"
    _set_task_role(task, "debugger", reason="coder_diff_ready")


def _run_debugger_handoff(
    task: LongRunningTask,
    *,
    sandbox_result: dict[str, Any] | None,
) -> None:
    task.cycle_count += 1
    if sandbox_result is not None:
        task.truncated_test_results = _format_sandbox_result(sandbox_result)

    if _sandbox_passed(sandbox_result) or _no_high_risk_items_remain(task):
        for diff in task.open_diffs:
            diff["status"] = "verified"
            diff["verified"] = True
        task.status = "completed"
        _set_task_role(task, "debugger", reason="debugger_verified")
        return

    for diff in task.open_diffs:
        if diff.get("status") == "pending_verification":
            diff["status"] = "needs_revision"
    if task.cycle_count >= MAX_CYCLES:
        task.status = "failed_needs_human"
        _set_task_role(task, "debugger", reason="debugger_cycle_limit")
        return
    task.status = "running"
    _set_task_role(task, "coder", reason="debugger_requested_revision")


def _format_sandbox_result(result: dict[str, Any]) -> str:
    stdout = str(result.get("stdout") or "")
    stderr = str(result.get("stderr") or "")
    return "\n".join(
        part
        for part in [
            f"returncode={result.get('returncode')}",
            stdout.strip(),
            stderr.strip(),
        ]
        if part
    )


def _sandbox_passed(result: dict[str, Any] | None) -> bool:
    if result is None or "returncode" not in result:
        return False
    return int(result["returncode"]) == 0


def _no_high_risk_items_remain(task: LongRunningTask) -> bool:
    if not task.open_diffs:
        return False
    return all(
        str(diff.get("risk") or "").lower() not in {"blocked", "high"}
        for diff in task.open_diffs
    )


def _apply_pre_save_hook(task: LongRunningTask) -> None:
    if task.truncated_test_results is None:
        task.truncated_test_results = ""
    if len(task.truncated_test_results) > TRUNCATED_TEST_RESULTS_LIMIT:
        task.truncated_test_results = task.truncated_test_results[
            -TRUNCATED_TEST_RESULTS_LIMIT:
        ]
    task.open_diffs = [
        diff
        for diff in task.open_diffs
        if isinstance(diff, dict) and not _diff_is_verified(diff)
    ]
    task.current_agent_role = _normalize_agent_role(task.current_agent_role)


def _diff_is_verified(diff: dict[str, Any]) -> bool:
    if diff.get("verified") is True:
        return True
    status = str(
        diff.get("verification_status")
        or diff.get("verificationStatus")
        or diff.get("status")
        or ""
    ).lower()
    return status in {"verified", "approved"}


def _prune_old_tasks() -> None:
    with closing(_connect()) as connection:
        _initialize_store(connection)
        stale_ids = [
            row["id"]
            for row in connection.execute(
                """
                SELECT id
                FROM long_running_tasks
                ORDER BY created_at DESC
                LIMIT -1 OFFSET ?
                """,
                (MAX_LONG_TASKS,),
            ).fetchall()
        ]
        if stale_ids:
            placeholders = ",".join("?" for _ in stale_ids)
            connection.execute(
                f"DELETE FROM long_running_tasks WHERE id IN ({placeholders})",
                stale_ids,
            )
            connection.commit()
            for task_id in stale_ids:
                _tasks.pop(task_id, None)


def _delete_persisted_tasks() -> None:
    with closing(_connect()) as connection:
        _initialize_store(connection)
        connection.execute("DELETE FROM long_running_tasks")
        connection.commit()


def _connect() -> sqlite3.Connection:
    database_path = _sqlite_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def _initialize_store(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS long_running_tasks (
            id TEXT PRIMARY KEY,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            cancelled_at TEXT,
            steps_json TEXT NOT NULL,
            poll_count INTEGER NOT NULL DEFAULT 0,
            ast_snapshot_json TEXT,
            open_diffs_json TEXT NOT NULL DEFAULT '[]',
            truncated_test_results TEXT NOT NULL DEFAULT '',
            current_agent_role TEXT NOT NULL DEFAULT 'architect',
            cycle_count INTEGER NOT NULL DEFAULT 0,
            architect_plan_json TEXT,
            architect_status TEXT NOT NULL DEFAULT 'idle',
            architect_reason TEXT NOT NULL DEFAULT ''
        )
        """
    )
    _ensure_column(connection, "ast_snapshot_json", "TEXT")
    _ensure_column(connection, "open_diffs_json", "TEXT NOT NULL DEFAULT '[]'")
    _ensure_column(
        connection,
        "truncated_test_results",
        "TEXT NOT NULL DEFAULT ''",
    )
    _ensure_column(
        connection,
        "current_agent_role",
        "TEXT NOT NULL DEFAULT 'architect'",
    )
    _ensure_column(connection, "cycle_count", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column(connection, "architect_plan_json", "TEXT")
    _ensure_column(
        connection,
        "architect_status",
        "TEXT NOT NULL DEFAULT 'idle'",
    )
    _ensure_column(
        connection,
        "architect_reason",
        "TEXT NOT NULL DEFAULT ''",
    )


def _ensure_column(
    connection: sqlite3.Connection,
    column_name: str,
    column_definition: str,
) -> None:
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(long_running_tasks)")
    }
    if column_name not in columns:
        connection.execute(
            f"ALTER TABLE long_running_tasks ADD COLUMN {column_name} {column_definition}"
        )


def _sqlite_path() -> Path:
    configured = os.getenv("SOURCE_PROXY_LONG_RUNNING_TASKS_DB")
    if configured:
        return Path(configured)
    return _workspace_root() / DEFAULT_SQLITE_PATH


def _json_value(raw_value: str | None, default: Any) -> Any:
    if raw_value is None:
        return default
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return default


def _ensure_fresh_repomix(root: Path) -> None:
    """Regenerate repomix bundle before the coder LLM runs (best-effort).

    Stale bundles are how you get ``patch does not apply`` theatre. If npx or
    repomix is missing, we log and carry on with whatever XML is already on disk.
    """
    try:
        print(f"[coder] Refreshing repomix bundle at {root} ...")
        result = subprocess.run(
            ["npx", "repomix", "--config", "repomix.config.json"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if result.returncode == 0:
            print(f"[coder] repomix refreshed successfully ({len(result.stdout)} chars)")
        else:
            print(f"[coder] repomix warning (non-zero exit): {result.stderr.strip()}")
    except Exception as exc:  # noqa: BLE001 — never fail the swarm on repomix
        print(f"[coder] repomix refresh failed (non-fatal): {exc}")


def _normalize_replacement_target(workspace_root: Path, target_path: str) -> str:
    raw = target_path.replace("\\", "/").strip()
    if not raw or raw.startswith("/") or "\x00" in raw:
        raise ValueError("target path is empty or absolute")
    if raw == ".." or raw.startswith("../") or "/../" in raw:
        raise ValueError("target path may not traverse outside the workspace")
    normalized = raw.lstrip("./")
    parts = Path(normalized).parts
    if any(part == ".." for part in parts):
        raise ValueError("target path may not traverse outside the workspace")
    resolved = (workspace_root / normalized).resolve()
    if not _is_relative_to(resolved, workspace_root):
        raise ValueError("target path resolves outside the workspace")
    return normalized


def _normalize_replacement_content(content: str) -> str:
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    if not normalized.endswith("\n"):
        normalized += "\n"
    return normalized


def generate_unified_diff_from_content(
    workspace_root: Path,
    target_path: str,
    new_content: str,
) -> str:
    """Generate a deterministic unified diff from full replacement content."""
    root = workspace_root.resolve()
    normalized_target = _normalize_replacement_target(root, target_path)
    target = (root / normalized_target).resolve()
    if target.is_file():
        old_content = target.read_text(encoding="utf-8", errors="replace")
        old_content = _normalize_replacement_content(old_content)
        old_lines = old_content.splitlines(keepends=True)
        fromfile = f"a/{normalized_target}"
        header: list[str] = []
    else:
        old_lines = []
        fromfile = "/dev/null"
        header = [
            f"diff --git a/{normalized_target} b/{normalized_target}\n",
            "new file mode 100644\n",
        ]
    new_content = _normalize_replacement_content(new_content)
    new_lines = new_content.splitlines(keepends=True)
    diff_lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=fromfile,
            tofile=f"b/{normalized_target}",
            lineterm="\n",
        )
    )
    diff_text = "".join(header + diff_lines)
    if not diff_text and old_lines == new_lines:
        return ""
    if not diff_text.endswith("\n"):
        diff_text += "\n"
    return sanitize_unified_diff_for_git_apply(diff_text, repair_hunks=False)


def replacement_content_matches_disk(
    workspace_root: Path,
    target_path: str,
    new_content: str,
) -> bool:
    """True when replacement content is a normalized no-op against the target file."""
    try:
        root = workspace_root.resolve()
        normalized_target = _normalize_replacement_target(root, target_path)
        target = (root / normalized_target).resolve()
        if not target.is_file():
            return False
        current_content = target.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    return _normalize_replacement_content(current_content) == _normalize_replacement_content(
        new_content
    )


def _strip_json_fence(raw_response: str) -> str:
    raw = (raw_response or "").strip()
    if not raw.startswith("```"):
        return raw
    lines = raw.splitlines()
    if not lines or not re.match(r"^```(?:json)?\s*$", lines[0].strip(), re.IGNORECASE):
        return raw
    if len(lines) < 2 or lines[-1].strip() != "```":
        return raw
    return "\n".join(lines[1:-1]).strip()


def _parse_coder_structured_output(raw_response: str) -> tuple[dict[str, Any] | None, str]:
    raw = _strip_json_fence(raw_response)
    if not raw:
        return None, "coder_empty_model_response"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None, "coder_response_not_json"
    if not isinstance(parsed, dict):
        return None, "coder_response_not_json"
    action = parsed.get("action")
    if action == "blocked":
        return parsed, ""
    if action != "replace_file":
        return None, "coder_invalid_replacement_payload"
    target = parsed.get("target")
    content = parsed.get("content")
    if not isinstance(target, str) or not target.strip() or not isinstance(content, str) or not content:
        return None, "coder_invalid_replacement_payload"
    return parsed, ""


def _coder_retry_prompt(base_prompt: str, reason: str, missing: list[str] | None = None) -> str:
    if reason == "coder_response_not_json":
        failure = "Your previous response was not valid JSON."
    elif reason == "coder_target_mismatch":
        failure = "Your previous JSON target did not match the explicit target."
    elif reason == "coder_invalid_replacement_payload":
        failure = "Your previous JSON was missing required replace_file fields."
    elif reason == "coder_replacement_content_validation_failed":
        failure = f"Your previous content missed: {', '.join((missing or [])[:8])}."
    elif reason == VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE:
        failure = (
            "Your previous replacement content produced a diff, but the diff only changed "
            "comments, whitespace, or non-visual text. This task requires a concrete visual "
            "change. Modify actual UI-affecting code: className strings, spacing, glow/ring/"
            "shadow, hover/focus/active states, transitions, or layout."
        )
    else:
        failure = f"Your previous response failed validation: {reason}."
    return f"{base_prompt}\n\nRETRY REQUIRED:\n{failure}\nReturn strict JSON only using the same schema."


def _coder_reviewer_feedback_task(source_task: str, reviewer_feedback: list[str] | None) -> str:
    feedback = [item for item in (reviewer_feedback or []) if str(item).strip()]
    if not feedback:
        return source_task
    return "\n".join(
        [
            source_task.rstrip(),
            "",
            "REVIEWER FEEDBACK FROM PREVIOUS ATTEMPT:",
            *(f"- {item}" for item in feedback[:8]),
            "",
            "Retry with the same target file and the same TaskSpec.allowed_files. "
            "Return replacement JSON only; do not apply the diff.",
        ]
    )


def _coder_already_satisfied_payload(
    *,
    target: str,
    notes: list[str],
    diagnostics: dict[str, Any],
    bundle_name: str | None,
) -> dict[str, Any]:
    satisfied_diagnostics = {
        **diagnostics,
        "validation_status": "already_satisfied",
        "generated_diff_length": 0,
        "normalized_diff_length": 0,
        "already_satisfied": True,
        "no_changes_needed": True,
    }
    notes.append("CODER_NO_CHANGES_NEEDED: replacement content already matches target.")
    return {
        "proposed_diff": "",
        "target": target,
        "coder_notes": notes,
        "coder_diagnostics": satisfied_diagnostics,
        "coderDiagnostics": satisfied_diagnostics,
        "bundle": bundle_name,
        "coder_agent_local_diff": False,
        "coderAgentLocalDiff": False,
        "coder_blocked": False,
        "coderBlocked": False,
        "already_satisfied": True,
        "alreadySatisfied": True,
        "reason_code": "coder_no_changes_needed",
        "reasonCode": "coder_no_changes_needed",
        "blocked_reason": "",
        "blockedReason": "",
        "needed_context": "",
        "neededContext": "",
        "status": "already_satisfied",
        "message": "The target file already matches the requested replacement content.",
    }


def _coder_subjective_improvement_requires_diff_payload(
    *,
    target: str,
    notes: list[str],
    diagnostics: dict[str, Any],
    bundle_name: str | None,
) -> dict[str, Any]:
    blocked_diagnostics = {
        **diagnostics,
        "validation_status": "subjective_improvement_requires_diff_or_review",
        "generated_diff_length": 0,
        "normalized_diff_length": 0,
        "already_satisfied": False,
        "no_changes_needed": False,
        "subjective_improvement_detected": True,
    }
    notes.append(
        "CODER_BLOCKED: subjective improvement request returned unchanged replacement content."
    )
    blocked_reason = (
        "This task asks for subjective visual improvement, so identical replacement "
        "content cannot be treated as already satisfied."
    )
    needed_context = "Produce an actual visual refinement diff or use manual visual review."
    return {
        "proposed_diff": "",
        "target": target,
        "coder_notes": notes,
        "coder_diagnostics": blocked_diagnostics,
        "coderDiagnostics": blocked_diagnostics,
        "bundle": bundle_name,
        "coder_agent_local_diff": False,
        "coderAgentLocalDiff": False,
        "coder_blocked": True,
        "coderBlocked": True,
        "already_satisfied": False,
        "alreadySatisfied": False,
        "reason_code": SUBJECTIVE_IMPROVEMENT_REQUIRES_DIFF_REASON_CODE,
        "reasonCode": SUBJECTIVE_IMPROVEMENT_REQUIRES_DIFF_REASON_CODE,
        "blocked_reason": blocked_reason,
        "blockedReason": blocked_reason,
        "needed_context": needed_context,
        "neededContext": needed_context,
        "status": "needs_coder_diff",
        "message": blocked_reason,
    }


def _coder_visual_improvement_diff_too_shallow_payload(
    *,
    target: str,
    notes: list[str],
    diagnostics: dict[str, Any],
    bundle_name: str | None,
    material_reasons: list[str],
) -> dict[str, Any]:
    blocked_diagnostics = {
        **diagnostics,
        "validation_status": "visual_improvement_diff_too_shallow",
        "visual_materiality_ok": False,
        "visual_materiality_reasons": material_reasons,
        "subjective_improvement_detected": True,
    }
    notes.append("CODER_BLOCKED: subjective visual improvement diff was too shallow.")
    blocked_reason = (
        "The generated diff does not materially change UI styling, layout, hover, "
        "active, glow, spacing, or visual behavior for this subjective improvement task."
    )
    needed_context = (
        "Generate a concrete visual refinement diff that changes className, styling, "
        "layout, hover, active, glow, spacing, or animation behavior."
    )
    return {
        "proposed_diff": "",
        "target": target,
        "coder_notes": notes,
        "coder_diagnostics": blocked_diagnostics,
        "coderDiagnostics": blocked_diagnostics,
        "bundle": bundle_name,
        "coder_agent_local_diff": False,
        "coderAgentLocalDiff": False,
        "coder_blocked": True,
        "coderBlocked": True,
        "already_satisfied": False,
        "alreadySatisfied": False,
        "reason_code": VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE,
        "reasonCode": VISUAL_IMPROVEMENT_DIFF_TOO_SHALLOW_REASON_CODE,
        "blocked_reason": blocked_reason,
        "blockedReason": blocked_reason,
        "needed_context": needed_context,
        "neededContext": needed_context,
        "status": "needs_coder_diff",
        "message": blocked_reason,
    }


def _git_apply_generated_diff_ok(root: Path, unified_diff: str) -> tuple[bool, str]:
    try:
        result = _git_apply_recount_check(root, unified_diff)
    except subprocess.TimeoutExpired as error:
        return (
            False,
            f"git apply --check timed out after {error.timeout} seconds",
        )
    if result.returncode == 0:
        return True, ""
    return False, (result.stderr or result.stdout or "git apply --check failed").strip()


def propose_coder_agent_implementation_diff(
    packet: CoderPacket,
    workspace_root: Path,
    *,
    source_task: str = "",
    llm_call: Callable[[str, str], str] | None = None,
    model_alias: str | None = None,
    reviewer_feedback: list[str] | None = None,
) -> CoderResponse:
    """Ask Coder for replacement content using only an Architect-owned packet."""
    _ = workspace_root
    target_path = packet.target_file.path
    task_spec = task_spec_from_packet(packet)
    task_spec_errors = validate_task_spec_for_packet(task_spec, packet)
    if task_spec_errors:
        return CoderResponse(
            status="blocked",
            target_path=target_path,
            replacement_content=None,
            reasoning=f"coder_task_spec_invalid: {', '.join(task_spec_errors)}",
            blocked_reason="Deterministic TaskSpec did not validate against the CoderPacket.",
            blocked_needed_context="Regenerate the Architect plan before running Coder.",
        )
    if not packet.context_slices:
        return CoderResponse(
            status="blocked",
            target_path=target_path,
            replacement_content=None,
            reasoning="CoderPacket does not include context slices.",
            blocked_reason="CoderPacket missing context.",
            blocked_needed_context="Regenerate the Architect plan with at least one target context slice.",
        )
    tampered = _tampered_context_slices(packet)
    if tampered:
        return CoderResponse(
            status="blocked",
            target_path=target_path,
            replacement_content=None,
            reasoning="CoderPacket context slice hash mismatch.",
            blocked_reason="CoderPacket context slice hash mismatch.",
            blocked_needed_context=f"Regenerate the Architect plan; mismatched slices: {', '.join(tampered[:5])}.",
        )
    prompt = _render_coder_prompt_from_packet(
        packet,
        source_task=_coder_reviewer_feedback_task(source_task, reviewer_feedback),
    )
    selected_alias = model_alias or _configured_coder_model_alias()
    if llm_call is None:
        alias_error = _coder_model_alias_configuration_error(selected_alias)
        if alias_error is not None:
            reason, needed_context = alias_error
            return CoderResponse(
                status="blocked",
                target_path=target_path,
                replacement_content=None,
                reasoning=reason,
                blocked_reason=needed_context,
                blocked_needed_context=needed_context,
            )

    current_prompt = prompt
    last_reason = "Coder model did not return valid replacement JSON."
    last_reason_code = "coder_response_not_json"
    last_needed_context = "Retry with local coder, use manual prompt packet, or switch to Cloud/API route."
    for _attempt in range(3):
        try:
            raw_response = (
                llm_call(current_prompt, selected_alias)
                if llm_call is not None
                else _call_coder_llm(current_prompt, model_alias=selected_alias)
            )
        except Exception as error:
            return CoderResponse(
                status="blocked",
                target_path=target_path,
                replacement_content=None,
                reasoning=f"Coder model/router call failed: {error}",
                blocked_reason="Coder model/router call failed.",
                blocked_needed_context=str(error),
            )

        parsed, parse_error = _parse_coder_structured_output(raw_response)
        if parse_error:
            last_reason_code = parse_error
            last_reason = "Coder response was not valid strict replacement JSON."
            current_prompt = _coder_retry_prompt(prompt, parse_error)
            continue

        assert parsed is not None
        if parsed.get("action") == "blocked":
            reason_code = str(parsed.get("reason_code") or "coder_blocked")
            reason = str(parsed.get("reason") or "Coder Agent blocked without a reason.")
            needed_raw = parsed.get("needed_context") or []
            needed = ", ".join(str(item) for item in needed_raw) if isinstance(needed_raw, list) else str(needed_raw)
            return CoderResponse(
                status="blocked",
                target_path=target_path,
                replacement_content=None,
                reasoning=f"{reason_code}: {reason}",
                blocked_reason=reason,
                blocked_needed_context=needed or "No needed context provided.",
            )

        replacement_target = str(parsed["target"]).replace("\\", "/").lstrip("./")
        if replacement_target != target_path:
            last_reason_code = "coder_target_mismatch"
            last_reason = f"Coder JSON targeted {replacement_target}, but packet target is {target_path}."
            current_prompt = _coder_retry_prompt(prompt, "coder_target_mismatch")
            continue

        return CoderResponse(
            status="ok",
            target_path=replacement_target,
            replacement_content=str(parsed["content"]),
            reasoning=str(parsed.get("notes") or "Coder returned replacement content."),
            blocked_reason=None,
            blocked_needed_context=None,
        )

    return CoderResponse(
        status="blocked",
        target_path=target_path,
        replacement_content=None,
        reasoning=f"{last_reason_code}: {last_reason}",
        blocked_reason=last_reason,
        blocked_needed_context=last_needed_context,
    )


def propose_coder_agent_diff_payload_from_plan(
    *,
    architect_plan: Any,
    workspace_root: Path | None = None,
    llm_call: Callable[[str, str], str] | None = None,
    model_alias: str | None = None,
    reviewer_feedback: list[str] | None = None,
    _review_attempt: int = 1,
    _previous_reviewer_signature: str = "",
) -> dict[str, Any]:
    """Run packet-only Coder, then convert its CoderResponse into approval diff payload."""
    root = (workspace_root or _workspace_root()).resolve()
    task = str(getattr(architect_plan, "source_task", "") or "")
    packet = _architect_coder_packet(architect_plan)
    if packet is None:
        return _coder_blocked_payload(
            target="",
            notes=["CODER_BLOCKED reason_code: coder_packet_missing_context"],
            diagnostics={
                **_base_coder_diagnostics(""),
                "validation_status": "coder_packet_missing_context",
            },
            bundle_name=None,
            reason="Architect plan does not contain a CoderPacket.",
            needed_context="Regenerate the Architect plan before running Coder.",
            reason_code="coder_packet_missing_context",
        )
    target_path = packet.target_file.path
    notes: list[str] = []
    diagnostics: dict[str, Any] = _base_coder_diagnostics(target_path)
    diagnostics["coder_attempt_count"] = _review_attempt
    diagnostics["reviewer_retry_count"] = max(0, _review_attempt - 1)
    diagnostics["retry_reason"] = "reviewer_feedback" if _review_attempt > 1 else ""
    task_spec = task_spec_from_plan(architect_plan)
    diagnostics["task_spec"] = task_spec.to_dict()
    task_spec_errors = validate_task_spec_for_packet(task_spec, packet)
    if task_spec_errors:
        notes.append(
            "CODER_BLOCKED reason_code: coder_task_spec_invalid; "
            + ", ".join(task_spec_errors)
        )
        return _coder_blocked_payload(
            target=target_path,
            notes=notes,
            diagnostics=diagnostics,
            bundle_name=None,
            reason="Deterministic TaskSpec did not validate against the CoderPacket.",
            needed_context="Regenerate the Architect plan before running Coder.",
            reason_code="coder_task_spec_invalid",
        )
    snapshot_drift = _coder_bundle_snapshot_drift(
        architect_plan=architect_plan,
        workspace_root=root,
        diagnostics=diagnostics,
    )
    if snapshot_drift is not None:
        notes.append(snapshot_drift["note"])
        return _coder_blocked_payload(
            target=str(snapshot_drift.get("target") or target_path),
            notes=notes,
            diagnostics=diagnostics,
            bundle_name=snapshot_drift.get("bundle_name"),
            reason="Bundle changed since the Architect plan was created.",
            needed_context="Regenerate the Architect plan before running Coder.",
            reason_code="bundle_snapshot_drift",
        )
    snapshot = getattr(architect_plan, "bundle_snapshot", None)
    snapshot_path = str(getattr(snapshot, "bundle_path", "") or "")
    bundle_name = Path(snapshot_path).name if snapshot_path else None
    diagnostics["repomix_bundle_used"] = bundle_name
    diagnostics["target_path_selected"] = target_path
    diagnostics["context_mode"] = derive_context_mode(target_path)
    diagnostics["forbidden_paths"] = list(packet.forbidden_paths)
    diagnostics["context_slices"] = [
        {"path": item.path, "kind": item.kind}
        for item in packet.context_slices
    ]
    abs_target = (root / target_path).resolve()
    if not _is_relative_to(abs_target, root):
        notes.append(f"Rejected path outside workspace: {target_path}")
        return {
            "proposed_diff": "",
            "target": "",
            "coder_notes": notes,
            "coder_diagnostics": diagnostics,
            "bundle": bundle_name,
        }
    target_exists = abs_target.is_file()
    diagnostics["target_exists"] = target_exists
    diagnostics["target_action"] = "replace file" if target_exists else "create file"
    prompt = _render_coder_prompt_from_packet(packet, source_task=task)
    diagnostics["prompt_size"] = len(prompt)
    selected_alias = model_alias or _configured_coder_model_alias()
    diagnostics["selected_model_alias"] = selected_alias

    deterministic = _deterministic_markdown_append_response(packet, task)
    if deterministic is not None:
        response = deterministic
    else:
        response = propose_coder_agent_implementation_diff(
            packet,
            root,
            source_task=task,
            llm_call=llm_call,
            model_alias=model_alias,
            reviewer_feedback=reviewer_feedback,
        )
    if response.status == "blocked" or response.replacement_content is None:
        diagnostics["validation_status"] = "coder_blocked"
        reason_code = _coder_response_reason_code(response)
        notes.append(f"CODER_BLOCKED reason_code: {reason_code}")
        notes.append(str(response.blocked_reason or response.reasoning))
        return _coder_blocked_payload(
            target=response.target_path or target_path,
            notes=notes,
            diagnostics=diagnostics,
            bundle_name=bundle_name,
            reason=str(response.blocked_reason or response.reasoning),
            needed_context=str(response.blocked_needed_context or "No needed context provided."),
            reason_code=reason_code,
        )

    diagnostics["parsed_output_mode"] = "replace_file"
    replacement_target = response.target_path
    content = _normalize_replacement_content(response.replacement_content)
    content_validation = validate_replacement_content(
        workspace_root=root,
        target_path=replacement_target,
        content=content,
        task_text=task,
    )
    diagnostics["content_validation"] = content_validation
    if not content_validation["ok"]:
        reason = str(content_validation.get("summary") or "Replacement content validation failed.")
        diagnostics["validation_status"] = "coder_replacement_content_validation_failed"
        notes.append(f"Replacement content validation failed: {reason}")
        return _coder_blocked_payload(
            target=replacement_target,
            notes=notes,
            diagnostics=diagnostics,
            bundle_name=bundle_name,
            reason=reason,
            needed_context=", ".join(str(item) for item in content_validation.get("missing", [])[:8]),
            reason_code="coder_replacement_content_validation_failed",
        )

    try:
        unified = generate_unified_diff_from_content(root, replacement_target, content)
    except Exception as error:  # noqa: BLE001 - fail closed with diagnostics
        diagnostics["exception_message"] = str(error)
        diagnostics["validation_status"] = "coder_backend_diff_generation_failed"
        return _coder_blocked_payload(
            target=replacement_target,
            notes=notes,
            diagnostics=diagnostics,
            bundle_name=bundle_name,
            reason=str(error),
            needed_context="Retry with local coder, use manual prompt packet, or switch to Cloud/API route.",
            reason_code="coder_backend_diff_generation_failed",
        )
    diagnostics["generated_diff_length"] = len(unified)
    diagnostics["normalized_diff_length"] = len(unified)
    if not unified:
        if content_validation["ok"] and replacement_content_matches_disk(
            root, replacement_target, content
        ):
            if task_requests_subjective_improvement(task):
                return _coder_subjective_improvement_requires_diff_payload(
                    target=replacement_target,
                    notes=notes,
                    diagnostics=diagnostics,
                    bundle_name=bundle_name,
                )
            return _coder_already_satisfied_payload(
                target=replacement_target,
                notes=notes,
                diagnostics=diagnostics,
                bundle_name=bundle_name,
            )
        diagnostics["validation_status"] = "coder_backend_diff_generation_failed"
        return _coder_blocked_payload(
            target=replacement_target,
            notes=notes,
            diagnostics=diagnostics,
            bundle_name=bundle_name,
            reason="Replacement content produced an empty diff.",
            needed_context="Retry with local coder, use manual prompt packet, or switch to Cloud/API route.",
            reason_code="coder_backend_diff_generation_failed",
        )

    task_spec_check = task_spec_diff_check(task_spec.to_dict(), _parse_changed_files(unified))
    diagnostics["task_spec_check"] = task_spec_check
    if not task_spec_check["ok"]:
        reason_codes = [
            str(code)
            for code in task_spec_check.get("reason_codes", [])
            if isinstance(code, str)
        ]
        reason = (
            "TaskSpec blocked this diff because it touches files outside the allowed list."
            if "task_spec_allowed_file_violation" in reason_codes
            else str(task_spec_check.get("summary") or "TaskSpec blocked the generated diff.")
        )
        diagnostics["validation_status"] = "coder_task_spec_diff_blocked"
        notes.append(f"CODER_BLOCKED reason_code: {reason_codes[0] if reason_codes else 'coder_task_spec_diff_blocked'}")
        return _coder_blocked_payload(
            target=replacement_target,
            notes=notes,
            diagnostics=diagnostics,
            bundle_name=bundle_name,
            reason=reason,
            needed_context="Regenerate a diff that only touches TaskSpec.allowed_files and avoids TaskSpec.forbidden_files.",
            reason_code=reason_codes[0] if reason_codes else "coder_task_spec_diff_blocked",
        )

    apply_ok, apply_error = _git_apply_generated_diff_ok(root, unified)
    if not apply_ok:
        reason = f"Generated diff did not pass git apply --check: {apply_error}"
        diagnostics["validation_status"] = "coder_backend_diff_generation_failed"
        notes.append(reason)
        return _coder_blocked_payload(
            target=replacement_target,
            notes=notes,
            diagnostics=diagnostics,
            bundle_name=bundle_name,
            reason=reason,
            needed_context="Retry with local coder, use manual prompt packet, or switch to Cloud/API route.",
            reason_code="coder_backend_diff_generation_failed",
        )

    if task_requests_subjective_improvement(task):
        material, material_reasons = subjective_visual_diff_is_material(
            unified,
            content,
            task,
        )
        diagnostics["visual_materiality_ok"] = material
        diagnostics["visual_materiality_reasons"] = material_reasons
        diagnostics["subjective_improvement_detected"] = True
        if not material:
            diagnostics["validation_status"] = "visual_improvement_diff_too_shallow"
            notes.append(
                "Visual materiality check failed: "
                + "; ".join(material_reasons or ["no UI-affecting diff markers found"])
            )
            return _coder_visual_improvement_diff_too_shallow_payload(
                target=replacement_target,
                notes=notes,
                diagnostics=diagnostics,
                bundle_name=bundle_name,
                material_reasons=material_reasons,
            )

    reviewer_retry_preview = _reviewer_blocked_retry_preview(
        unified,
        task=task,
        architect_plan=architect_plan,
        task_spec=task_spec.to_dict(),
    )
    if reviewer_retry_preview is not None:
        feedback = _reviewer_retry_feedback(reviewer_retry_preview)
        signature = _reviewer_retry_signature(unified, feedback)
        diagnostics["validation_status"] = "reviewer_blocked"
        diagnostics["last_reviewer_blockers"] = feedback
        diagnostics["retry_reason"] = "reviewer_blocked"
        notes.append(f"Reviewer blocked attempt {_review_attempt}: " + "; ".join(feedback[:5]))
        max_attempts = _max_reviewer_retry_attempts(architect_plan)
        if _review_attempt < max_attempts and signature != _previous_reviewer_signature:
            notes.append("Retrying Coder with reviewer feedback.")
            return propose_coder_agent_diff_payload_from_plan(
                architect_plan=architect_plan,
                workspace_root=root,
                llm_call=llm_call,
                model_alias=model_alias,
                reviewer_feedback=feedback,
                _review_attempt=_review_attempt + 1,
                _previous_reviewer_signature=signature,
            )
        diagnostics["validation_status"] = "blocked_after_retries"
        diagnostics["blocked_after_retries"] = True
        notes.append("CODER_BLOCKED reason_code: blocked_after_retries")
        return _coder_blocked_payload(
            target=replacement_target,
            notes=notes,
            diagnostics=diagnostics,
            bundle_name=bundle_name,
            reason="Reviewer blocked the generated diff after bounded retries.",
            needed_context="; ".join(feedback[:8]),
            reason_code="blocked_after_retries",
        )

    diagnostics["validation_status"] = "preview_ready"
    notes.append(f"Backend generated validated diff for {replacement_target}.")
    return {
        "proposed_diff": unified,
        "target": replacement_target,
        "coder_notes": notes,
        "coder_diagnostics": diagnostics,
        "bundle": bundle_name,
    }


def _max_reviewer_retry_attempts(architect_plan: Any) -> int:
    budget = getattr(architect_plan, "budget", None)
    raw = getattr(budget, "max_coder_attempts", 3)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = 3
    return max(1, min(value, 3))


def _reviewer_blocked_retry_preview(
    unified_diff: str,
    *,
    task: str,
    architect_plan: Any,
    task_spec: dict[str, Any],
) -> dict[str, Any] | None:
    try:
        preview = preview_diff_verification(
            unified_diff,
            task_text=task,
            architect_plan=architect_plan,
            task_spec=task_spec,
            route_type="local_route",
        )
    except DiffVerificationError:
        return None
    if preview.get("status") != "blocked":
        return None
    reasons = [
        str(reason.get("reason_code") or "")
        for reason in preview.get("blocked_reasons", [])
        if isinstance(reason, dict)
    ]
    reviewer_reasons = [reason for reason in reasons if reason.startswith("review_")]
    non_reviewer_reasons = [
        reason
        for reason in reasons
        if reason and not reason.startswith("review_")
    ]
    if reviewer_reasons and not non_reviewer_reasons:
        return preview
    return None


def _reviewer_retry_feedback(preview: dict[str, Any]) -> list[str]:
    report = preview.get("review_report")
    findings = report.get("findings") if isinstance(report, dict) else []
    feedback: list[str] = []
    if isinstance(findings, list):
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            finding_id = str(finding.get("id") or "reviewer_blocked").strip()
            details = str(finding.get("details") or "").strip()
            if finding_id or details:
                feedback.append(f"{finding_id}: {details}".strip(": "))
    if feedback:
        return feedback
    return [
        str(reason.get("reason_code") or "reviewer_blocked")
        for reason in preview.get("blocked_reasons", [])
        if isinstance(reason, dict)
    ]


def _reviewer_retry_signature(unified_diff: str, feedback: list[str]) -> str:
    payload = "\n".join([unified_diff, *feedback])
    return hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()


def _deterministic_markdown_append_response(
    packet: CoderPacket,
    task: str,
) -> CoderResponse | None:
    """Complete tiny explicit Markdown append tasks without waiting on a local model."""
    target_path = packet.target_file.path
    if Path(target_path).suffix.lower() not in {".md", ".markdown"} or packet.operation != "edit":
        return None
    literal = _markdown_append_literal(task)
    if not literal:
        return None
    target_slice = next(
        (
            item
            for item in packet.context_slices
            if item.kind == "target" and item.path == target_path
        ),
        None,
    )
    if target_slice is None:
        return None
    current = _normalize_replacement_content(target_slice.content)
    if literal in current:
        content = current
    else:
        content = f"{current.rstrip()}\n{literal}\n"
    return CoderResponse(
        status="ok",
        target_path=target_path,
        replacement_content=content,
        reasoning="Deterministic Coder handled a tiny explicit Markdown append task.",
        blocked_reason=None,
        blocked_needed_context=None,
    )


def _markdown_append_literal(task: str) -> str:
    from source_proxy.planning.architect import markdown_append_literal

    return markdown_append_literal(task)


def _base_coder_diagnostics(target_path: str) -> dict[str, Any]:
    return {
        "selected_model_alias": "",
        "available_model_aliases": sorted(available_model_aliases()),
        "router_call_attempted": False,
        "raw_response_length": 0,
        "raw_response_excerpt": "",
        "parsed_output_mode": "",
        "normalized_diff_length": 0,
        "generated_diff_length": 0,
        "validation_status": "",
        "model_output_mode": "replacement_content",
        "generated_diff_by_backend": True,
        "model_raw_diff_used": False,
        "retry_count": 0,
        "coder_attempt_count": 1,
        "reviewer_retry_count": 0,
        "last_reviewer_blockers": [],
        "retry_reason": "",
        "blocked_after_retries": False,
        "target_path_selected": target_path,
        "explicit_target_parsed": target_path,
        "repomix_bundle_used": None,
        "blocked_response_parsed": False,
        "exception_message": "",
        "prompt_size": 0,
        "target_exists": False,
        "target_action": "",
        "context_mode": derive_context_mode(target_path),
        "forbidden_paths": [],
        "context_slices": [],
        "bundle_snapshot_check": "not_applicable",
        "bundle_snapshot_expected_sha256": "",
        "bundle_snapshot_actual_sha256": "",
        "task_spec": None,
    }


def _tampered_context_slices(packet: CoderPacket) -> list[str]:
    mismatched: list[str] = []
    for context_slice in packet.context_slices:
        actual = hashlib.sha256(context_slice.content.encode("utf-8")).hexdigest()
        if context_slice.sha256 and actual != context_slice.sha256:
            mismatched.append(context_slice.path)
    return mismatched


def _coder_response_reason_code(response: CoderResponse) -> str:
    text = " ".join(
        str(value or "")
        for value in (response.reasoning, response.blocked_reason, response.blocked_needed_context)
    ).lower()
    if "missing context" in text:
        return "coder_packet_missing_context"
    if "hash mismatch" in text or "tampered" in text:
        return "coder_packet_context_hash_mismatch"
    for reason_code in (
        "coder_task_spec_invalid",
        "coder_needs_context",
        "coder_response_not_json",
        "coder_target_mismatch",
        "coder_invalid_replacement_payload",
    ):
        if reason_code in text:
            return reason_code
    if "model_not_configured" in text or "not configured" in text:
        return "coder_model_not_configured"
    if "router call failed" in text or "model/router" in text:
        return "coder_model_router_error"
    return "coder_blocked"


def _coder_bundle_snapshot_drift(
    *,
    architect_plan: Any | None,
    workspace_root: Path,
    diagnostics: dict[str, Any],
) -> dict[str, str | None] | None:
    if architect_plan is None:
        return None
    snapshot = getattr(architect_plan, "bundle_snapshot", None)
    if snapshot is None:
        return None
    expected = str(getattr(snapshot, "bundle_sha256", "") or "")
    if not expected:
        diagnostics["bundle_snapshot_check"] = "skipped_no_snapshot_hash"
        return None

    bundle_path = Path(str(getattr(snapshot, "bundle_path", "") or ""))
    if not bundle_path.is_file():
        for name in REPOMIX_BUNDLE_NAMES:
            candidate = workspace_root / name
            if candidate.is_file():
                bundle_path = candidate
                break
    if not bundle_path.is_file():
        diagnostics["bundle_snapshot_check"] = "failed_missing_bundle"
        diagnostics["bundle_snapshot_expected_sha256"] = expected
        return {
            "bundle_name": None,
            "target": _plan_target_path(architect_plan),
            "note": "CODER_BLOCKED reason_code: bundle_snapshot_drift; bundle file missing.",
        }

    actual = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
    diagnostics["bundle_snapshot_expected_sha256"] = expected
    diagnostics["bundle_snapshot_actual_sha256"] = actual
    diagnostics["bundle_snapshot_path"] = str(bundle_path)
    if actual == expected:
        diagnostics["bundle_snapshot_check"] = "passed"
        return None
    diagnostics["bundle_snapshot_check"] = "failed"
    return {
        "bundle_name": bundle_path.name,
        "target": _plan_target_path(architect_plan),
        "note": (
            "CODER_BLOCKED reason_code: bundle_snapshot_drift; "
            f"expected {expected}, got {actual}."
        ),
    }


def _plan_target_path(architect_plan: Any) -> str:
    packet = getattr(architect_plan, "coder_packet", None)
    target_file = getattr(packet, "target_file", None)
    return str(getattr(target_file, "path", "") or "")


def _coder_blocked_payload(
    *,
    target: str,
    notes: list[str],
    diagnostics: dict[str, Any],
    bundle_name: str | None,
    reason: str,
    needed_context: str,
    reason_code: str,
) -> dict[str, Any]:
    return {
        "proposed_diff": "",
        "target": target,
        "coder_notes": notes,
        "coder_diagnostics": diagnostics,
        "bundle": bundle_name,
        "coder_blocked": True,
        "blocked_reason": reason,
        "needed_context": needed_context,
        "reason_code": reason_code,
    }


def _normalize_repo_rel_path(rel_path: str) -> str:
    return rel_path.replace("\\", "/").lstrip("./").lower()


def derive_context_mode(target_path: str) -> ContextMode:
    normalized = _normalize_repo_rel_path(target_path)
    agent_prefixes = (
        "source_proxy/",
        "src/components/coding/",
        "src/lib/coding/",
        "src/lib/spirit/apply-unified-diff.ts",
    )
    return "agent_internal" if normalized.startswith(agent_prefixes) else "user_app"


def forbidden_paths_for_context_mode(context_mode: ContextMode) -> tuple[str, ...]:
    return (
        AGENT_INTERNAL_FORBIDDEN_PATHS
        if context_mode == "agent_internal"
        else USER_APP_FORBIDDEN_PATHS
    )


def _render_coder_prompt_from_packet(packet: CoderPacket, *, source_task: str = "") -> str:
    target_path = packet.target_file.path
    criteria = _render_packet_acceptance_criteria(packet)
    constraints = _render_packet_constraints(packet)
    styles = "\n".join(f"- {item}" for item in packet.style_directives[:6]) or "- none"
    context = _render_packet_context_slices(packet)
    task = source_task.strip() or f"Target file: {target_path}"
    task_contract = json.dumps(
        task_spec_from_packet(packet).to_dict(),
        indent=2,
        sort_keys=True,
    )
    prompt = CODER_SYSTEM_PROMPT.format(
        task=task,
        file_path=target_path,
        acceptance_criteria="\n".join(
            item
            for item in (criteria, constraints, "STYLE DIRECTIVES:", styles)
            if item
        ),
        subjective_improvement_contract=_coder_subjective_improvement_contract(task),
        repomix_file_content=context,
        task_contract=task_contract,
    )
    if packet.target_file.exists:
        prompt += (
            "\nTARGET FILE EXISTS: yes\n"
            "Treat any request to create a brand new page as a request to modify or replace "
            "the existing target file. Return the complete replacement content.\n"
        )
    else:
        prompt += "\nTARGET FILE EXISTS: no\nReturn complete new file content.\n"
    return prompt


def _render_packet_acceptance_criteria(packet: CoderPacket) -> str:
    criteria = [f"- target: {packet.target_file.path}"]
    for item in packet.acceptance_criteria:
        criteria.append(f"- {item.id} ({item.kind}): {item.description}")
    return "\n".join(criteria)


def _render_packet_constraints(packet: CoderPacket) -> str:
    constraints = packet.constraints
    lines: list[str] = []
    for value in constraints.must_contain:
        lines.append(f"- must contain: {value}")
    for value in constraints.must_not_contain:
        lines.append(f"- must not contain: {value}")
    for value in constraints.preserve_imports:
        lines.append(f"- preserve import: {value}")
    for value in constraints.preserve_exports:
        lines.append(f"- preserve export: {value}")
    if constraints.max_added_lines is not None:
        lines.append(f"- max added lines: {constraints.max_added_lines}")
    if constraints.max_removed_lines is not None:
        lines.append(f"- max removed lines: {constraints.max_removed_lines}")
    return "PACKET CONSTRAINTS:\n" + "\n".join(lines) if lines else ""


def _render_packet_context_slices(packet: CoderPacket) -> str:
    rendered: list[str] = []
    for context_slice in packet.context_slices:
        rendered.append(
            "\n".join(
                [
                    f"[{context_slice.kind} slice: {context_slice.path}]",
                    context_slice.content,
                ]
            )
        )
    return "\n\n".join(rendered)


def _architect_coder_packet(architect_plan: Any | None) -> CoderPacket | None:
    packet = getattr(architect_plan, "coder_packet", None)
    return packet if isinstance(packet, CoderPacket) else None


def _coder_subjective_improvement_contract(task: str) -> str:
    if task_requests_subjective_improvement(task):
        return (
            "This is an improvement request. Returning unchanged replacement content is "
            "not acceptable. Produce a concrete refined replacement file, or return "
            "blocked JSON explaining why visual/manual review is needed."
        )
    return "No subjective improvement language detected; exact objective no-op is allowed when verifiable."


def _coder_model_alias() -> str:
    configured = _configured_coder_model_alias() or "local"
    enabled = available_model_aliases()
    if configured in enabled:
        return configured
    if "local" in enabled:
        return "local"
    return configured


def _configured_coder_model_alias() -> str:
    return os.getenv("SOURCE_PROXY_CODER_MODEL_ALIAS", "").strip()


def _coder_model_alias_configuration_error(alias: str) -> tuple[str, str] | None:
    enabled = available_model_aliases()
    if not alias:
        return (
            "coder_model_not_configured",
            "Set SOURCE_PROXY_CODER_MODEL_ALIAS to an available model alias or use manual/cloud route.",
        )
    if alias not in enabled:
        available = ", ".join(sorted(enabled)) or "none"
        return (
            "coder_model_not_configured",
            (
                f"{alias!r} is not an available model alias. Available aliases: {available}. "
                "Set SOURCE_PROXY_CODER_MODEL_ALIAS to an available model alias or use manual/cloud route."
            ),
        )
    return None


def _call_coder_llm(prompt: str, *, model_alias: str | None = None) -> str:
    alias = model_alias or _coder_model_alias()
    completion = get_router().completion(
        model=alias,
        messages=[{"role": "system", "content": prompt}],
        stream=False,
        temperature=0,
        timeout=float(os.getenv("SOURCE_PROXY_CODER_TIMEOUT_SECONDS", "180")),
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


def _normalize_coder_unified_diff(raw_response: str, target_path: str) -> str:
    raw = _strip_diff_fence(raw_response)
    if not raw:
        return ""

    starts = [
        index
        for index in (
            raw.find("diff --git "),
            raw.find("--- "),
            raw.find("@@ "),
        )
        if index >= 0
    ]
    if starts:
        raw = raw[min(starts) :]
    raw = raw.replace("\r\n", "\n").replace("\r", "\n").strip()
    if "@@" not in raw:
        return ""

    if raw.startswith("@@"):
        raw = f"--- a/{target_path}\n+++ b/{target_path}\n{raw}"
    if not raw.endswith("\n"):
        raw += "\n"
    return sanitize_unified_diff_for_git_apply(raw)


def _parse_coder_blocked_response(raw_response: str) -> dict[str, str] | None:
    raw = (raw_response or "").strip()
    if not raw.startswith("CODER_BLOCKED:"):
        return None
    reason = ""
    needed_context = ""
    reason_code = "coder_blocked_response"
    for line in raw.splitlines()[1:]:
        if line.lower().startswith("reason:"):
            reason = line.split(":", 1)[1].strip()
        elif line.lower().startswith("reason_code:"):
            reason_code = line.split(":", 1)[1].strip() or reason_code
        elif line.lower().startswith("needed_context:"):
            needed_context = line.split(":", 1)[1].strip()
    return {
        "reason": reason,
        "needed_context": needed_context,
        "reason_code": reason_code,
    }


def _looks_like_new_file_diff(unified_diff: str) -> bool:
    lines = [line.strip() for line in unified_diff.splitlines()]
    return "new file mode 100644" in lines or "--- /dev/null" in lines


def _strip_diff_fence(raw_response: str) -> str:
    raw = raw_response.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return raw


def _target_from_unified_diff(unified_diff: str) -> str | None:
    for raw_line in unified_diff.splitlines():
        line = raw_line.strip()
        if line.startswith("+++ "):
            raw_path = line[4:].strip()
            if raw_path == "/dev/null":
                return None
            if raw_path.startswith("b/") or raw_path.startswith("a/"):
                return raw_path[2:]
            return raw_path
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                path = parts[3]
                return path[2:] if path.startswith("b/") else path
    return None


def _normalize_agent_role(value: Any) -> SwarmAgentRole:
    normalized = str(value or "").strip().lower()
    if normalized in {"architect", "coder", "debugger"}:
        return normalized  # type: ignore[return-value]
    return "architect"
