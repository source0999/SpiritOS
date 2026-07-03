from __future__ import annotations

import difflib
import hashlib
import html
import json
import os
import queue
import re
import sqlite3
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request
from contextlib import closing
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Literal
from uuid import uuid4

from source_proxy.agents.registry import SwarmAgentRole, normalize_agent_role
from source_proxy.approval.external_gate import central_gate_check
from source_proxy.routing.litellm_router import (
    _read_coder_timeout_seconds,
    available_model_aliases,
    get_router,
    route_model_for_alias,
    route_provider_for_alias,
)
from source_proxy.routing.ollama_route import (
    local_model_unavailable_from_error,
    local_model_unavailable_payload,
    ollama_route_status_entry,
    resolve_classifier_ollama_model_name,
    resolve_coder_ollama_model_name,
    resolve_ollama_route,
)
from source_proxy.context.obsidian import obsidian_context_diagnostics
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
from source_proxy.tasks.engine.state import (
    append_unique_steps as _append_unique_steps,
    has_approved_execution as _has_approved_execution,
    task_blocker_reason_code as _task_blocker_reason_code,
    task_is_waiting_for_coder_output as _task_is_waiting_for_coder_output_state,
    task_queue_title as _task_queue_title,
    terminal_or_waiting_statuses as _terminal_or_waiting_statuses,
)

# Mid-file ``patch does not apply``: try whitespace relaxations only. Do **not** use
# ``--3way`` here — it requires blobs in the git index; untracked or odd trees get
# ``does not exist in index`` and waste cycles (runtime-proven on CodingAgentInterface).
_GIT_APPLY_FLAG_CHAINS: tuple[tuple[str, ...], ...] = (
    (),
    ("--ignore-whitespace",),
    ("--ignore-space-change",),
)

_active_coder_timing: dict[str, Any] = {}


def reset_coder_timing_diagnostics() -> None:
    _active_coder_timing.clear()


def snapshot_coder_timing_diagnostics() -> dict[str, Any]:
    flat = dict(_active_coder_timing)
    for event in (
        "coder_llm",
        "prompt_context",
        "provider_request_started",
        "provider_request_done",
        "provider_request_failed",
    ):
        nested = _active_coder_timing.get(event)
        if isinstance(nested, dict):
            flat.update(nested)
    return flat


def _mark_coder_timing(event: str, **data: Any) -> None:
    now_ms = round(time.perf_counter() * 1000, 2)
    started_key = f"{event}_started_ms"
    if started_key not in _active_coder_timing:
        _active_coder_timing[started_key] = now_ms
    _active_coder_timing[event] = data
    _active_coder_timing[f"{event}_at_ms"] = now_ms
    origin = _active_coder_timing.get("target_resolution_started_ms")
    if isinstance(origin, (int, float)):
        _active_coder_timing[f"{event}_done_ms"] = round(now_ms - origin, 2)


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
- Prefer the XML-style file block output. No prose.
- If XML is awkward, use the FILE delimiter output. JSON remains accepted only as a legacy fallback.
- Do not wrap the file block or JSON in markdown fences.
- Do not include a unified diff unless explicitly asked.
- Target must exactly match the explicit Target file line and TaskSpec.target.
- Only edit files in TaskSpec.allowed_files.
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
  8. the file block content is the full replacement file, not a diff hunk

Preferred output shape:
<file path="REPO_RELATIVE_PATH">
FULL_FILE_CONTENT
</file>

Alternate accepted output shape:
<<<FILE: REPO_RELATIVE_PATH
FULL_FILE_CONTENT
>>>

Legacy accepted JSON shapes:
{{"action":"replace_file","target":"REPO_RELATIVE_PATH","content_lines":["line 1","line 2"],"notes":"short optional note"}}
{{"action":"replace_file","target":"REPO_RELATIVE_PATH","content":"FULL_FILE_CONTENT","notes":"short optional note"}}
{{"action":"blocked","reason_code":"coder_needs_context","reason":"Cannot produce safe file content because ...","needed_context":["specific file or check needed"]}}

Return the file block now.
"""
DEFAULT_SQLITE_PATH = Path("data") / "long_running_tasks.sqlite3"
DEFAULT_AUDIT_LOG_PATH = Path("data") / "approved_actions.audit.jsonl"
DEFAULT_STEPS = [
    "Capture task scope.",
    "Collect safe context.",
    "Prepare verification plan.",
    "Wait for explicit execution path.",
]
CAUSAL_EVENT_TYPES = {
    "invocation",
    "consumer",
    "failure",
    "status_transition",
    "policy",
    "retry",
    "recovery",
    "repair",
    "verification",
}
CAUSAL_EVENT_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|token|secret)\s*[:=]\s*['\"]?[A-Za-z0-9_.-]{12,}"),
)


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
    causal_events: list[dict[str, Any]] = field(default_factory=list)

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
            "causal_events": list(self.causal_events[-50:]),
            "causal_trace": _causal_trace_summary(self.causal_events),
            "plan_3_durable_state": _plan3_readback_state(self),
            "would_execute": _has_approved_execution(self.open_diffs),
            "writes_allowed": _has_approved_execution(self.open_diffs),
            "worker_lanes": _worker_lanes_for_task(self),
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
        if self.status in {"applied_verification_failed", "verification_failed"}:
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
            return "Retry Local Coder with stricter output repair, then use a manual browser prompt if needed."
        if self.status == "failed_needs_human":
            return "The swarm hit the safety cycle limit. Review the latest diff and sandbox output manually."
        if self.status in {"applied_verification_failed", "verification_failed"}:
            return "Approved diff was applied, but verification failed. Generate a fix prompt from the verification error."
        if self.status == "applied_needs_verification":
            verification = _current_post_apply_verification(self)
            if isinstance(verification, dict) and verification.get("docs_only"):
                return "Docs-only verification ready. Complete the manual checklist before marking the task done."
            if isinstance(verification, dict) and verification.get("unsupported_code_verification"):
                return "Manual verification required: unsupported code verification type."
            return "Approved diff was applied. Run code verification before marking the task done."
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
    conflict = _write_scope_conflict_for_task(task)
    if conflict is not None:
        task.status = "blocked"
        task.architect_status = "blocked"
        task.architect_reason = "write_scope_conflict"
        task.truncated_test_results = (
            f"reason_code: write_scope_conflict; scope={conflict['scope_key']}; "
            f"existing_task={conflict['task_id']}"
        )
        task.ast_snapshot = {
            "queue_conflict": conflict,
            "queue_policy": "one_write_capable_task_per_scope",
        }
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
    if _task_has_plan3_durable_state(task):
        task.poll_count += 1
        task.updated_at = _now_iso()
        _save_task(task)
    elif task.status not in _terminal_or_waiting_statuses():
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
    return _task_is_waiting_for_coder_output_state(
        current_agent_role=task.current_agent_role,
        architect_status=task.architect_status,
        open_diffs=task.open_diffs,
    )


def _task_has_pre_execution_safety_block(task: LongRunningTask) -> bool:
    if task.status in _terminal_or_waiting_statuses():
        return False
    if _has_approved_execution(task.open_diffs):
        return False
    for event in task.causal_events:
        if not isinstance(event, dict):
            continue
        notes = event.get("notes")
        if isinstance(notes, list) and "approved_diff_blocked" in notes:
            return True
    return False


def _task_is_abandoned_pre_preview_write_lock(task: LongRunningTask) -> bool:
    if _task_is_dummy_selected_prompt_pre_preview_lock(task):
        return True
    if _task_is_stale_dummy_product_site_verification_lock(task):
        return True
    if task.status != "queued":
        return False
    if task.current_agent_role != "architect" or task.architect_status != "idle":
        return False
    if task.open_diffs or task.causal_events:
        return False
    try:
        created = datetime.fromisoformat(task.created_at)
    except ValueError:
        return False
    return (datetime.now(UTC) - created).total_seconds() > 15 * 60


def _task_is_dummy_selected_prompt_pre_preview_lock(task: LongRunningTask) -> bool:
    if task.status not in {"queued", "running"}:
        return False
    if task.current_agent_role != "architect" or task.architect_status != "idle":
        return False
    if task.open_diffs or task.causal_events or _has_approved_execution(task.open_diffs):
        return False
    scope_key = _task_scope_key(task)
    if not _scope_is_dummy_product_site(scope_key):
        return False
    lowered = task.description.lower()
    return (
        "lumacart" in lowered
        and "pass expectations:" in lowered
        and "fail conditions:" in lowered
    )


def _task_is_stale_dummy_product_site_verification_lock(task: LongRunningTask) -> bool:
    if task.status != "applied_needs_verification":
        return False
    if not _scope_is_dummy_product_site(_task_scope_key(task)):
        return False
    lowered = task.description.lower()
    if lowered.startswith("agent-lab cleanup delete "):
        return True
    if "lumacart" not in lowered:
        return False
    try:
        updated = datetime.fromisoformat(task.updated_at)
    except ValueError:
        return False
    return (datetime.now(UTC) - updated).total_seconds() > 60


def get_long_running_task_snapshot(task_id: str) -> dict[str, Any]:
    task = _lookup_task(task_id)
    return _task_envelope(task)


def list_long_running_tasks(
    *,
    include_completed: bool = True,
    limit: int = 25,
) -> dict[str, Any]:
    bounded_limit = min(max(limit, 1), 100)
    tasks = _load_recent_tasks(limit=bounded_limit)
    if not include_completed:
        terminal = _terminal_or_waiting_statuses()
        tasks = [task for task in tasks if task.status not in terminal]
    return {
        "access_scope": "read_only_task_queue",
        "count": len(tasks),
        "tasks": [_task_queue_item(task) for task in tasks],
        "tool": "long_running_task_tracker",
    }


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
    approval_id: str,
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
    status_before = task.status
    trace_id = _ensure_causal_trace_id(task)
    run_id = f"execute_approved_long_running_task:{task_id}"
    invocation_event = _append_causal_event(
        task,
        event_type="invocation",
        subsystem="source_proxy_long_running",
        approval_id=approval_id,
        run_id=run_id,
        status_before=status_before,
        changed_state_fields=[],
        notes=["execute-approved apply path entered"],
    )
    _save_task(task)
    try:
        central_gate_check("apply", run_id=run_id)
    except Exception:
        task.status = "failed_needs_human"
        _append_causal_event(
            task,
            event_type="failure",
            subsystem="source_proxy_long_running",
            approval_id=approval_id,
            run_id=run_id,
            status_before=status_before,
            status_after=task.status,
            changed_state_fields=["status"],
            notes=["central gate blocked apply"],
        )
        _save_task(task)
        raise
    expected_approval_id = approval_id_for_approved_diff(
        task_id=task_id,
        approved_diff=approved_diff,
        target=target,
    )
    if approval_id != expected_approval_id:
        _append_causal_event(
            task,
            event_type="failure",
            subsystem="source_proxy_long_running",
            approval_id=approval_id,
            run_id=run_id,
            status_before=status_before,
            status_after=task.status,
            changed_state_fields=[],
            notes=["approval_id_mismatch"],
        )
        _save_task(task)
        raise LongRunningTaskError(
            "Approved diff approval_id does not match the task, target, and diff.",
            "approval_id_mismatch",
        )
    from source_proxy.planning.plan import load_plan

    architect_plan = load_plan(task_id)
    normalized_action = action.lower()
    is_reversible_live_trial = (
        normalized_action.startswith("live trial")
        or normalized_action.startswith("revert live trial")
        or normalized_action.startswith("run selected dummy coder prompt")
    )
    trial_task_spec = (
        _reversible_live_trial_task_spec(
            action=action,
            approved_diff=approved_diff,
            target=target,
        )
        if is_reversible_live_trial
        else None
    )
    verification = preview_diff_verification(
        approved_diff,
        test_command=test_command,
        task_text=(
            task.description
            if _is_dummy_product_site_live_trial_spec(trial_task_spec)
            else f"Target file: {target}"
            if is_reversible_live_trial and target
            else task.description
        ),
        architect_plan=None if is_reversible_live_trial else architect_plan,
        task_spec=trial_task_spec,
    )
    if verification["status"] == "blocked":
        before_blocked = task.status
        task.status = "blocked"
        task.architect_status = "blocked"
        task.architect_reason = "approved_diff_blocked"
        blocked_reasons = [
            str(reason).strip()
            for reason in verification.get("blocked_reasons", [])
            if str(reason).strip()
        ]
        task.truncated_test_results = (
            "reason_code: approved_diff_blocked"
            + (f"; blocked_reasons={'; '.join(blocked_reasons)[:1000]}" if blocked_reasons else "")
        )
        _append_causal_event(
            task,
            event_type="failure",
            subsystem="source_proxy_long_running",
            approval_id=approval_id,
            run_id=run_id,
            status_before=before_blocked,
            status_after=task.status,
            changed_state_fields=[
                "status",
                "architect_status",
                "architect_reason",
                "truncated_test_results",
            ],
            notes=["approved_diff_blocked"],
        )
        task.updated_at = _now_iso()
        _save_task(task)
        raise LongRunningTaskError(
            "Approved diff was blocked by safety verification.",
            "approved_diff_blocked",
        )

    before_executing = task.status
    task.status = "executing"
    _append_causal_event(
        task,
        event_type="status_transition",
        subsystem="source_proxy_long_running",
        approval_id=approval_id,
        run_id=run_id,
        status_before=before_executing,
        status_after=task.status,
        changed_state_fields=["status"],
        notes=["approved diff entered execution"],
    )
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
        before_failure = task.status
        task.status = "failed_needs_human"
        _append_causal_event(
            task,
            event_type="failure",
            subsystem="source_proxy_long_running",
            approval_id=approval_id,
            run_id=run_id,
            status_before=before_failure,
            status_after=task.status,
            changed_state_fields=["status"],
            notes=["workspace application failed"],
        )
        task.truncated_test_results = "Approved diff failed during workspace application."
        task.updated_at = _now_iso()
        _save_task(task)
        raise

    audit_record = {
        "action": action,
        "approval_id": approval_id,
        "approved_at": _now_iso(),
        "approved_by": approved_by,
        "approved_diff_sha256": hashlib.sha256(approved_diff.encode("utf-8")).hexdigest(),
        "changed_files": [file["path"] for file in verification["changed_files"]],
        "backup_manifest": apply_result["manifest_path"],
        "backup_root": apply_result["backup_root"],
        "changed_file_snapshots": apply_result["changed_file_snapshots"],
        "approved_diff_path": apply_result["approved_diff_path"],
        "risk": verification["risk"],
        "rollback_hint": "Use the backup manifest and approved.diff under backup_root before reverting files.",
        "target": target,
        "task_id": task.id,
    }
    snapshot = _ensure_ast_snapshot_dict(task)
    snapshot["post_apply_backup_audit"] = {
        "backup_manifest": audit_record["backup_manifest"],
        "backup_root": audit_record["backup_root"],
        "task_id": task.id,
    }
    task.ast_snapshot = snapshot
    _append_audit_log(audit_record)
    _finalize_backup_manifest(
        workspace_root=Path(apply_result["workspace_root"]),
        manifest_path=apply_result["manifest_path"],
        audit_record=audit_record,
    )

    before_applied = task.status
    task.status = "applied_needs_verification"
    _append_causal_event(
        task,
        event_type="status_transition",
        subsystem="source_proxy_long_running",
        approval_id=approval_id,
        run_id=run_id,
        status_before=before_applied,
        status_after=task.status,
        changed_state_fields=["status"],
        notes=["approved diff applied"],
    )
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
    _record_approved_execution_evidence(
        task,
        audit_record=audit_record,
        backup_root=apply_result["backup_root"],
        post_apply_verification=post_apply_verification,
        verification_plan=verification["verification_plan"],
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
        "approval_id": approval_id,
        "applied_at": audit_record["approved_at"],
        "audit": audit_record,
        "backup_root": apply_result["backup_root"],
        "changed_file_snapshots": apply_result["changed_file_snapshots"],
        "changed_files": verification["changed_files"],
        "trace_id": trace_id,
        "invocation_event_id": invocation_event["event_id"],
        "causal_events": list(task.causal_events[-50:]),
        "causal_trace": _causal_trace_summary(task.causal_events),
        "message": "Approved diff applied after safety verification; post-apply verification is required before completion.",
        "post_apply_verification": post_apply_verification,
        "risk": verification["risk"],
        "status": task.status,
        "target": target,
        "verification_plan": verification["verification_plan"],
        "commit_created": False,
        "push_ran": False,
    }
    return payload


def _reversible_live_trial_task_spec(
    *,
    action: str,
    approved_diff: str,
    target: str | None,
) -> dict[str, Any]:
    if _approved_diff_is_dummy_product_site_bundle(approved_diff):
        is_revert = action.lower().startswith("revert")
        return {
            "schema_version": 1,
            "task_type": "delete_file" if is_revert else "create_file_bundle",
            "target": DUMMY_PRODUCT_SITE_ROOT,
            "allowed_files": [f"{DUMMY_PRODUCT_SITE_ROOT}**"],
            "forbidden_files": [
                ".env*",
                "package.json",
                "package-lock.json",
                "source_proxy/**",
                "src/app/**",
                "src/components/**",
                "src/lib/**",
                "docs/**",
                "backend/volumes/**",
                "backend/searxng_data/**",
                ".spirit-backups/**",
            ],
            "verification": ["git diff --check"],
            "risk_tier": "low",
            "source": "coding-live-runner-selected-prompt-create-bundle",
        }
    return {
        "schema_version": 1,
        "task_type": "modify_existing_file",
        "target": target,
        "allowed_files": [target] if target else [],
        "forbidden_files": [
            ".env*",
            "source_proxy/data/**",
            "backend/volumes/**",
            "backend/searxng_data/**",
            ".spirit-backups/**",
        ],
        "verification": ["git diff --check"],
        "risk_tier": "low",
        "source": "coding-live-runner-reversible-trial",
    }


def _approved_diff_is_dummy_product_site_bundle(approved_diff: str) -> bool:
    changed = [
        str(file.get("path") or "").replace("\\", "/")
        for file in _parse_changed_files(approved_diff)
        if isinstance(file, dict) and str(file.get("path") or "").strip()
    ]
    return bool(changed) and all(path.startswith(DUMMY_PRODUCT_SITE_ROOT) for path in changed)


def _is_dummy_product_site_live_trial_spec(task_spec: dict[str, Any] | None) -> bool:
    return bool(
        isinstance(task_spec, dict)
        and task_spec.get("task_type") == "create_file_bundle"
        and task_spec.get("target") == DUMMY_PRODUCT_SITE_ROOT
    )


def approval_id_for_approved_diff(
    *,
    task_id: str,
    approved_diff: str,
    target: str | None,
) -> str:
    key = "|".join(
        [
            task_id.strip(),
            (target or "").strip(),
            hashlib.sha256(approved_diff.encode("utf-8")).hexdigest(),
        ]
    )
    return f"approval-{hashlib.sha256(key.encode('utf-8')).hexdigest()[:16]}"


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
    run_code_verification: bool = False,
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
    if run_code_verification:
        if docs_only:
            raise LongRunningTaskError(
                "Code verification is only available for code/test file changes.",
                "code_verification_not_applicable",
            )
        if _unsupported_code_verification_paths(changed_files):
            raise LongRunningTaskError(
                "Manual verification is required for this unsupported code verification type.",
                "unsupported_code_verification_type",
            )
        if not _has_frontend_code_changed(changed_files):
            raise LongRunningTaskError(
                "Manual verification is required for this unsupported code verification type.",
                "unsupported_code_verification_type",
            )
        checks = _run_code_post_apply_verification(changed_files)
        verification["checks"] = [dict(check) for check in checks]
        manual_browser_check_done = bool(
            manual_browser_check_done
            or not verification.get("manual_browser_check_required")
        )
        verification_note = (
            verification_note
            or "Server-side code verification ran from the post-apply allowlist."
        )

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
        if incoming_check is None and check_id == "typescript_typecheck":
            incoming_check = by_id.get("typecheck")
        if incoming_check is None and check_id == "typecheck":
            incoming_check = by_id.get("typescript_typecheck")
        if incoming_check:
            status = str(incoming_check.get("status") or "").strip().lower()
            if status in {"passed", "failed", "skipped"}:
                check["status"] = status
            if incoming_check.get("summary"):
                check["summary"] = str(incoming_check["summary"])
            for key in ("duration_ms", "exit_code", "output_tail"):
                if key in incoming_check:
                    check[key] = incoming_check[key]
        if check.get("required") and check.get("status") == "failed":
            any_failed = True
        updated_checks.append(check)

    if not any_failed:
        if not docs_only and not skip and not run_code_verification:
            raise LongRunningTaskError(
                "Code changes require the server-side code verification action before completion.",
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
        verification["status"] = "verification_failed"
        task.status = "verification_failed"
        verification["commit_proposal_blocked"] = True
        verification["commit_blockers"] = ["post_apply_verification_failed"]
    elif all_required_done and (not browser_required or browser_done):
        verification["status"] = "verified"
        verification["commit_proposal_blocked"] = False
        verification["commit_blockers"] = []
        task.status = "completed"
        task.steps = _append_unique_steps(
            task.steps,
            ["Post-apply verification completed."],
        )
    else:
        verification["status"] = "verification_ready"
        verification["commit_proposal_blocked"] = True
        verification["commit_blockers"] = ["post_apply_verification_incomplete"]
        task.status = "applied_needs_verification"

    verification["push_path_available"] = False
    verification["push_blockers"] = ["push_requires_separate_approval"]

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
            "verification_failed",
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


def _record_approved_execution_evidence(
    task: LongRunningTask,
    *,
    audit_record: dict[str, Any],
    backup_root: str,
    post_apply_verification: dict[str, Any],
    verification_plan: list[str],
) -> None:
    snapshot = _ensure_ast_snapshot_dict(task)
    snapshot["approved_execution_evidence"] = {
        "audit": audit_record,
        "backup_root": backup_root,
        "backup_manifest": audit_record.get("backup_manifest"),
        "approved_diff_path": audit_record.get("approved_diff_path"),
        "approved_diff_sha256": audit_record.get("approved_diff_sha256"),
        "post_apply_verification": post_apply_verification,
        "verification_plan": verification_plan,
    }
    task.ast_snapshot = snapshot


def _sanitize_causal_note(value: Any) -> str:
    text = str(value or "").strip()
    for pattern in CAUSAL_EVENT_SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text[:240]


def _causal_event_has_secret(event: dict[str, Any]) -> bool:
    raw = json.dumps(event, sort_keys=True)
    return any(pattern.search(raw) for pattern in CAUSAL_EVENT_SECRET_PATTERNS)


def _new_causal_event_id(event_type: str) -> str:
    normalized = event_type if event_type in CAUSAL_EVENT_TYPES else "status_transition"
    return f"{normalized}_{uuid4().hex[:16]}"


def _ensure_causal_trace_id(task: LongRunningTask) -> str:
    for event in task.causal_events:
        trace_id = str(event.get("trace_id") or "").strip()
        if trace_id:
            return trace_id
    snapshot = task.ast_snapshot if isinstance(task.ast_snapshot, dict) else {}
    existing_trace_id = str(snapshot.get("causal_trace_id") or "").strip()
    if existing_trace_id:
        return existing_trace_id
    trace_id = f"trace_{uuid4().hex[:16]}"
    snapshot = _ensure_ast_snapshot_dict(task)
    snapshot["causal_trace_id"] = trace_id
    task.ast_snapshot = snapshot
    return trace_id


def _append_causal_event(
    task: LongRunningTask,
    *,
    event_type: Literal[
        "invocation",
        "consumer",
        "failure",
        "status_transition",
        "policy",
        "retry",
        "recovery",
        "repair",
        "verification",
    ],
    subsystem: str,
    approval_id: str | None = None,
    run_id: str | None = None,
    status_before: str | None = None,
    status_after: str | None = None,
    changed_state_fields: list[str] | None = None,
    consumer_subsystem: str | None = None,
    notes: list[Any] | None = None,
) -> dict[str, Any]:
    event = {
        "event_id": _new_causal_event_id(event_type),
        "trace_id": _ensure_causal_trace_id(task),
        "task_id": task.id,
        "event_type": event_type,
        "subsystem": subsystem,
        "consumer_subsystem": consumer_subsystem,
        "run_id": run_id,
        "approval_id": approval_id,
        "status_before": status_before,
        "status_after": status_after,
        "changed_state_fields": list(dict.fromkeys(changed_state_fields or [])),
        "created_at": _now_iso(),
        "notes": [_sanitize_causal_note(note) for note in (notes or [])],
    }
    if _causal_event_has_secret(event):
        raise LongRunningTaskError(
            "Causal event contains a secret-shaped string.",
            "causal_event_secret_detected",
        )
    task.causal_events = [*task.causal_events, event][-100:]
    return event


def _causal_trace_summary(events: list[dict[str, Any]]) -> dict[str, Any]:
    invocation = next(
        (event for event in reversed(events) if event.get("event_type") == "invocation"),
        {},
    )
    consumer = next(
        (event for event in reversed(events) if event.get("event_type") == "consumer"),
        {},
    )
    latest = events[-1] if events else {}
    return {
        "trace_id": str((latest or invocation or consumer).get("trace_id") or ""),
        "invocation_event_id": invocation.get("event_id"),
        "consumer_event_id": consumer.get("event_id"),
        "consumer_subsystem": consumer.get("consumer_subsystem"),
        "status_after": latest.get("status_after"),
        "event_types": sorted(
            {
                str(event.get("event_type") or "")
                for event in events
                if str(event.get("event_type") or "")
            }
        ),
    }


def _record_long_running_status_observer_consumer(task: LongRunningTask) -> bool:
    if not task.causal_events:
        return False
    if not any(event.get("event_type") == "invocation" for event in task.causal_events):
        return False
    status = task.status
    if status not in {
        "applied_needs_verification",
        "failed_needs_human",
        "verification_failed",
        "applied_verification_failed",
    }:
        return False
    if any(
        event.get("event_type") == "consumer"
        and event.get("consumer_subsystem") == "long_running_status_observer"
        and event.get("status_after") == status
        for event in task.causal_events
    ):
        return False
    _append_causal_event(
        task,
        event_type="consumer",
        subsystem="source_proxy_long_running",
        consumer_subsystem="long_running_status_observer",
        status_after=status,
        changed_state_fields=["status"],
        notes=["task status consumed by readback"],
    )
    return True


def _post_apply_has_backup_audit(task: LongRunningTask) -> bool:
    snapshot = task.ast_snapshot if isinstance(task.ast_snapshot, dict) else {}
    backup_audit = snapshot.get("post_apply_backup_audit")
    if (
        isinstance(backup_audit, dict)
        and backup_audit.get("task_id") == task.id
        and backup_audit.get("backup_root")
        and backup_audit.get("backup_manifest")
    ):
        return True
    try:
        prior = json.loads(task.truncated_test_results or "{}")
    except json.JSONDecodeError:
        prior = {}
    if isinstance(prior, dict) and isinstance(prior.get("audit"), dict) and bool(prior.get("backup_root")):
        return True
    return _approved_action_audit_has_backup(task.id)


def _approved_action_audit_has_backup(task_id: str) -> bool:
    audit_path = _audit_log_path()
    if not audit_path.is_file():
        return False
    try:
        lines = audit_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    for line in reversed(lines[-200:]):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict) or payload.get("task_id") != task_id:
            continue
        if payload.get("backup_root") and payload.get("backup_manifest"):
            return True
    return False


_CODE_VERIFICATION_EXTENSIONS = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
}


def _changed_file_paths(changed_files: list[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    for file in changed_files:
        path = str(file.get("path") or "").strip().replace("\\", "/")
        if path:
            paths.append(path)
    return paths


def _has_frontend_code_changed(changed_files: list[dict[str, Any]]) -> bool:
    return any(
        Path(path).suffix.lower() in _CODE_VERIFICATION_EXTENSIONS
        for path in _changed_file_paths(changed_files)
    )


def _unsupported_code_verification_paths(changed_files: list[dict[str, Any]]) -> list[str]:
    unsupported: list[str] = []
    for path in _changed_file_paths(changed_files):
        suffix = Path(path).suffix.lower()
        if suffix in {".md", ".mdx"}:
            continue
        if suffix not in _CODE_VERIFICATION_EXTENSIONS:
            unsupported.append(path)
    return unsupported


def _needs_coding_frontend_regression(changed_files: list[dict[str, Any]]) -> bool:
    for path in _changed_file_paths(changed_files):
        normalized = path.lower()
        if normalized.startswith("src/lib/coding/"):
            return True
        if normalized.startswith("src/components/coding/"):
            return True
    return False


def _package_script_exists(root: Path, script_name: str) -> bool:
    package_json = root / "package.json"
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    scripts = data.get("scripts")
    return isinstance(scripts, dict) and isinstance(scripts.get(script_name), str)


def _allowed_code_verification_commands(
    changed_files: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    root = _workspace_root()
    if _unsupported_code_verification_paths(changed_files):
        return []
    if not _has_frontend_code_changed(changed_files):
        return []

    commands: list[dict[str, Any]] = []
    if _needs_coding_frontend_regression(changed_files) and _package_script_exists(
        root,
        "test:coding-frontend-regression",
    ):
        commands.append(
            {
                "id": "coding_frontend_regression",
                "command": ["npm", "run", "test:coding-frontend-regression"],
                "required": True,
                "summary": "Coding frontend regression surface changed.",
            }
        )
    commands.append(
        {
            "id": "typescript_typecheck",
            "command": ["npx", "tsc", "--noEmit", "-p", "tsconfig.json"],
            "required": True,
            "summary": "TypeScript or JavaScript files changed.",
        }
    )
    return commands


def _command_text(command: list[str]) -> str:
    return " ".join(command)


def _tail_output(stdout: str, stderr: str, limit: int = 4000) -> str:
    combined = "\n".join(part for part in [stdout.strip(), stderr.strip()] if part)
    return combined[-limit:]


def _run_code_post_apply_verification(
    changed_files: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    commands = _allowed_code_verification_commands(changed_files)
    if not commands:
        raise LongRunningTaskError(
            "No allowlisted code verification commands matched the changed files.",
            "code_verification_not_applicable",
        )

    root = _workspace_root()
    results: list[dict[str, Any]] = []
    for check in commands:
        command = [str(part) for part in check["command"]]
        started = time.perf_counter()
        try:
            result = subprocess.run(
                command,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            exit_code = int(result.returncode)
            output_tail = _tail_output(result.stdout or "", result.stderr or "")
        except subprocess.TimeoutExpired as exc:
            exit_code = 124
            output_tail = _tail_output(exc.stdout or "", exc.stderr or "")
        duration_ms = int((time.perf_counter() - started) * 1000)
        results.append(
            {
                "id": check["id"],
                "command": command,
                "command_text": _command_text(command),
                "duration_ms": duration_ms,
                "exit_code": exit_code,
                "output_tail": output_tail,
                "required": bool(check.get("required")),
                "status": "passed" if exit_code == 0 else "failed",
                "summary": check["summary"],
            }
        )
    return results


def _initial_post_apply_verification(verification: dict[str, Any]) -> dict[str, Any]:
    changed_files = [
        file for file in verification.get("changed_files", []) if isinstance(file, dict)
    ]
    suggested_commands = [
        item for item in verification.get("suggested_commands", []) if isinstance(item, dict)
    ]
    route_or_ui_changed = any(
        str(file.get("path") or "").replace("\\", "/").startswith("src/app/")
        or str(file.get("path") or "").lower().endswith((".tsx", ".jsx", ".css"))
        for file in changed_files
    )
    docs_only = _docs_only_changed_files(changed_files)
    unsupported_paths = _unsupported_code_verification_paths(changed_files)

    checks: list[dict[str, Any]] = []
    for item in _allowed_code_verification_commands(changed_files):
        checks.append({**item, "status": "pending"})
    for item in suggested_commands:
        command = item.get("command")
        if not isinstance(command, list) or not command:
            continue
        command_text = " ".join(str(part) for part in command)
        check_id = "lint" if "eslint" in command_text else command_text
        if any(check.get("id") == check_id for check in checks):
            continue
        if check_id == "lint":
            continue
        if check_id == "npm run typecheck" or check_id == "typecheck":
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
        "commit_proposal_blocked": True,
        "commit_blockers": ["post_apply_verification_incomplete"],
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
        "status": "manual_verification_required"
        if unsupported_paths and not docs_only
        else "verification_ready",
        "unsupported_code_verification": bool(unsupported_paths and not docs_only),
        "unsupported_file_types": sorted(
            {
                Path(path).suffix.lower() or "(none)"
                for path in unsupported_paths
            }
        ),
        "updated_at": _now_iso(),
        "verification_note": "",
        "push_path_available": False,
        "push_blockers": ["push_requires_separate_approval"],
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


def record_subsystem_integration_result(
    task_id: str,
    *,
    subsystem: str,
    consumer_subsystem: str,
    upstream_state: dict[str, Any],
    output: dict[str, Any],
    status: str,
    changed_state_fields: list[str] | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    """Record a Plan 2 subsystem invocation and downstream consumption on one task.

    This deliberately reuses the Plan 1 long-running task causal store. It is a
    thin recorder for integrations that already ran elsewhere; it is not an
    executor, state engine, or approval bypass.
    """
    normalized_subsystem = _sanitize_causal_note(subsystem)
    normalized_consumer = _sanitize_causal_note(consumer_subsystem)
    if not normalized_subsystem or not normalized_consumer:
        raise LongRunningTaskError(
            "Subsystem and consumer_subsystem are required.",
            "plan2_subsystem_consumer_required",
        )
    if not isinstance(upstream_state, dict) or not upstream_state:
        raise LongRunningTaskError(
            "Plan 2 subsystem integration requires real upstream state.",
            "plan2_upstream_state_required",
        )
    if not isinstance(output, dict) or not output:
        raise LongRunningTaskError(
            "Plan 2 subsystem integration requires real output.",
            "plan2_output_required",
        )

    task = _lookup_task(task_id)
    status_before = task.status
    trace_id = _ensure_causal_trace_id(task)
    normalized_status = _sanitize_causal_note(status).upper()
    failed = normalized_status in {
        "FAILED",
        "BLOCKED",
        "BLOCKED_ENV",
        "BLOCKED_AUTH",
        "BLOCKED_HUMAN",
        "DEGRADED",
        "NEEDS_FIX",
    }
    invocation_event = _append_causal_event(
        task,
        event_type="invocation",
        subsystem=normalized_subsystem,
        run_id=f"plan2_subsystem:{task_id}:{normalized_subsystem}",
        status_before=status_before,
        status_after=task.status,
        changed_state_fields=["ast_snapshot"],
        notes=[
            f"Plan 2 subsystem invoked with upstream keys: {sorted(upstream_state.keys())[:8]}",
            f"status={normalized_status}",
        ],
    )

    snapshot = _ensure_ast_snapshot_dict(task)
    integrations = snapshot.get("plan_2_subsystem_integrations")
    if not isinstance(integrations, dict):
        integrations = {}
    output_hash = hashlib.sha256(
        json.dumps(output, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    integrations[normalized_subsystem] = {
        "status": normalized_status,
        "trace_id": trace_id,
        "invocation_event_id": invocation_event["event_id"],
        "consumer_subsystem": normalized_consumer,
        "upstream_state_keys": sorted(upstream_state.keys()),
        "output_hash": output_hash,
        "output_summary": _sanitize_causal_note(output.get("summary") or output.get("reason") or normalized_status),
        "failure_reason": _sanitize_causal_note(failure_reason or ""),
    }
    snapshot["plan_2_subsystem_integrations"] = integrations
    snapshot["plan_2_last_subsystem_output"] = {
        "subsystem": normalized_subsystem,
        "status": normalized_status,
        "output_hash": output_hash,
        "output": output,
    }
    task.ast_snapshot = snapshot

    fields = list(dict.fromkeys([*(changed_state_fields or []), "ast_snapshot"]))
    if failed:
        before_failure = task.status
        task.status = "blocked" if normalized_status.startswith("BLOCKED") else "failed_needs_human"
        task.architect_status = "blocked"
        task.architect_reason = failure_reason or normalized_status.lower()
        _append_causal_event(
            task,
            event_type="failure",
            subsystem=normalized_subsystem,
            run_id=f"plan2_subsystem:{task_id}:{normalized_subsystem}",
            status_before=before_failure,
            status_after=task.status,
            changed_state_fields=["status", "architect_status", "architect_reason", *fields],
            notes=[failure_reason or normalized_status],
        )

    consumer_event = _append_causal_event(
        task,
        event_type="consumer",
        subsystem=normalized_subsystem,
        consumer_subsystem=normalized_consumer,
        run_id=f"plan2_subsystem:{task_id}:{normalized_subsystem}:consumer",
        status_before=status_before,
        status_after=task.status,
        changed_state_fields=fields,
        notes=[
            f"{normalized_consumer} consumed {normalized_subsystem} output hash {output_hash[:16]}",
        ],
    )
    integrations[normalized_subsystem]["consumer_event_id"] = consumer_event["event_id"]
    task.ast_snapshot = snapshot
    task.updated_at = _now_iso()
    _save_task(task)
    return _task_envelope(task)


def begin_subsystem_integration_invocation(
    task_id: str,
    *,
    subsystem: str,
    upstream_state: dict[str, Any],
) -> dict[str, Any]:
    normalized_subsystem = _sanitize_causal_note(subsystem)
    if not normalized_subsystem:
        raise LongRunningTaskError("Subsystem is required.", "plan2_subsystem_required")
    if not isinstance(upstream_state, dict) or not upstream_state:
        raise LongRunningTaskError(
            "Plan 2 subsystem integration requires real upstream state.",
            "plan2_upstream_state_required",
        )
    task = _lookup_task(task_id)
    trace_id = _ensure_causal_trace_id(task)
    invocation = _append_causal_event(
        task,
        event_type="invocation",
        subsystem=normalized_subsystem,
        run_id=f"plan2_subsystem:{task_id}:{normalized_subsystem}",
        status_before=task.status,
        status_after=task.status,
        changed_state_fields=["ast_snapshot"],
        notes=[
            f"Plan 2 subsystem dispatch began with upstream keys: {sorted(upstream_state.keys())[:8]}",
        ],
    )
    snapshot = _ensure_ast_snapshot_dict(task)
    pending = snapshot.get("plan_2_pending_subsystem_invocations")
    if not isinstance(pending, dict):
        pending = {}
    pending[normalized_subsystem] = {
        "trace_id": trace_id,
        "invocation_event_id": invocation["event_id"],
        "upstream_state_keys": sorted(upstream_state.keys()),
        "started_at": invocation["created_at"],
    }
    snapshot["plan_2_pending_subsystem_invocations"] = pending
    task.ast_snapshot = snapshot
    task.updated_at = _now_iso()
    _save_task(task)
    return {
        "task_id": task.id,
        "trace_id": trace_id,
        "invocation_event_id": invocation["event_id"],
        "status_before": task.status,
    }


def finish_subsystem_integration_result(
    task_id: str,
    *,
    subsystem: str,
    consumer_subsystem: str,
    upstream_state: dict[str, Any],
    output: dict[str, Any],
    status: str,
    changed_state_fields: list[str] | None = None,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    normalized_subsystem = _sanitize_causal_note(subsystem)
    normalized_consumer = _sanitize_causal_note(consumer_subsystem)
    if not normalized_subsystem or not normalized_consumer:
        raise LongRunningTaskError(
            "Subsystem and consumer_subsystem are required.",
            "plan2_subsystem_consumer_required",
        )
    if not isinstance(upstream_state, dict) or not upstream_state:
        raise LongRunningTaskError(
            "Plan 2 subsystem integration requires real upstream state.",
            "plan2_upstream_state_required",
        )
    if not isinstance(output, dict) or not output:
        raise LongRunningTaskError(
            "Plan 2 subsystem integration requires real output.",
            "plan2_output_required",
        )
    task = _lookup_task(task_id)
    snapshot = _ensure_ast_snapshot_dict(task)
    pending = snapshot.get("plan_2_pending_subsystem_invocations")
    pending_record = pending.get(normalized_subsystem) if isinstance(pending, dict) else {}
    invocation_event_id = str((pending_record or {}).get("invocation_event_id") or "")
    if not invocation_event_id:
        raise LongRunningTaskError(
            "Plan 2 subsystem result has no matching invocation event.",
            "plan2_invocation_missing",
        )
    trace_id = _ensure_causal_trace_id(task)
    normalized_status = _sanitize_causal_note(status).upper()
    failed = normalized_status in {
        "FAILED",
        "BLOCKED",
        "BLOCKED_ENV",
        "BLOCKED_AUTH",
        "BLOCKED_HUMAN",
        "DEGRADED",
        "NEEDS_FIX",
    }
    output_hash = hashlib.sha256(
        json.dumps(output, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    integrations = snapshot.get("plan_2_subsystem_integrations")
    if not isinstance(integrations, dict):
        integrations = {}
    integrations[normalized_subsystem] = {
        "status": normalized_status,
        "trace_id": trace_id,
        "invocation_event_id": invocation_event_id,
        "consumer_subsystem": normalized_consumer,
        "upstream_state_keys": sorted(upstream_state.keys()),
        "output_hash": output_hash,
        "output_summary": _sanitize_causal_note(output.get("summary") or output.get("reason") or normalized_status),
        "failure_reason": _sanitize_causal_note(failure_reason or ""),
    }
    snapshot["plan_2_subsystem_integrations"] = integrations
    snapshot["plan_2_last_subsystem_output"] = {
        "subsystem": normalized_subsystem,
        "status": normalized_status,
        "output_hash": output_hash,
        "output": output,
    }
    fields = list(dict.fromkeys([*(changed_state_fields or []), "ast_snapshot"]))
    if failed:
        before_failure = task.status
        task.status = "blocked" if normalized_status.startswith("BLOCKED") else "failed_needs_human"
        task.architect_status = "blocked"
        task.architect_reason = failure_reason or normalized_status.lower()
        _append_causal_event(
            task,
            event_type="failure",
            subsystem=normalized_subsystem,
            run_id=f"plan2_subsystem:{task_id}:{normalized_subsystem}",
            status_before=before_failure,
            status_after=task.status,
            changed_state_fields=["status", "architect_status", "architect_reason", *fields],
            notes=[failure_reason or normalized_status],
        )
    consumer_event = _append_causal_event(
        task,
        event_type="consumer",
        subsystem=normalized_subsystem,
        consumer_subsystem=normalized_consumer,
        run_id=f"plan2_subsystem:{task_id}:{normalized_subsystem}:consumer",
        status_after=task.status,
        changed_state_fields=fields,
        notes=[
            f"{normalized_consumer} consumed {normalized_subsystem} output hash {output_hash[:16]}",
        ],
    )
    integrations[normalized_subsystem]["consumer_event_id"] = consumer_event["event_id"]
    if isinstance(pending, dict):
        pending.pop(normalized_subsystem, None)
        snapshot["plan_2_pending_subsystem_invocations"] = pending
    task.ast_snapshot = snapshot
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
    if _record_long_running_status_observer_consumer(task):
        task.updated_at = _now_iso()
        _save_task(task)
    payload = task.to_payload()
    payload["post_apply_verification"] = _current_post_apply_verification(task)
    payload["plan_3_durable_state"] = _plan3_readback_state(task)
    payload["scope_key"] = _task_scope_key(task)
    payload["write_capable"] = _task_is_write_capable(task)
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


def _task_has_plan3_durable_state(task: LongRunningTask) -> bool:
    snapshot = task.ast_snapshot if isinstance(task.ast_snapshot, dict) else {}
    return isinstance(snapshot.get("plan_3_durable_state"), dict)


def _plan3_readback_state(task: LongRunningTask) -> dict[str, Any] | None:
    snapshot = task.ast_snapshot if isinstance(task.ast_snapshot, dict) else {}
    state = snapshot.get("plan_3_durable_state")
    if not isinstance(state, dict):
        return None
    trace = _causal_trace_summary(task.causal_events)
    latest_invocation = trace.get("invocation_event_id")
    latest_consumer = trace.get("consumer_event_id")
    payload = dict(state)
    payload.update(
        {
            "task_id": task.id,
            "current_status": task.status,
            "trace_id": state.get("trace_id") or trace.get("trace_id"),
            "latest_invocation_event_id": state.get("latest_invocation_event_id")
            or latest_invocation,
            "latest_consumer_event_id": state.get("latest_consumer_event_id")
            or latest_consumer,
            "causal_events_json": list(task.causal_events[-50:]),
        }
    )
    return payload


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
    approved_diff_path = backup_root / "approved.diff"
    approved_diff_path.write_text(unified_diff, encoding="utf-8")
    backed_up_files: list[dict[str, Any]] = []

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
            backed_up_files.append(
                {
                    "path": rel_path,
                    "backup_path": str(backup_path.relative_to(workspace_root)).replace("\\", "/"),
                    "sha256": _sha256_file(resolved),
                }
            )
        else:
            backed_up_files.append(
                {
                    "path": rel_path,
                    "backup_path": None,
                    "sha256": None,
                    "missing_before_apply": True,
                }
            )

    manifest_path = backup_root / "manifest.json"
    _write_backup_manifest(
        manifest_path=manifest_path,
        workspace_root=workspace_root,
        approved_diff_path=approved_diff_path,
        changed_files=changed_files,
        backed_up_files=backed_up_files,
        stage="before_apply",
    )

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

    before_by_path = {
        str(item.get("path")): item
        for item in backed_up_files
        if isinstance(item, dict) and item.get("path")
    }
    changed_file_snapshots: list[dict[str, Any]] = []
    for file in changed_files:
        rel_path = str(file["path"])
        resolved = (workspace_root / rel_path).resolve()
        before = before_by_path.get(rel_path, {})
        changed_file_snapshots.append(
            {
                "path": rel_path,
                "backup_path": before.get("backup_path"),
                "sha256_before": before.get("sha256"),
                "sha256_after": _sha256_file(resolved) if resolved.exists() and resolved.is_file() else None,
                "missing_before_apply": bool(before.get("missing_before_apply")),
            }
        )

    return {
        "backup_root": str(backup_root.relative_to(workspace_root)).replace("\\", "/"),
        "workspace_root": str(workspace_root),
        "manifest_path": str(manifest_path.relative_to(workspace_root)).replace("\\", "/"),
        "approved_diff_path": str(approved_diff_path.relative_to(workspace_root)).replace("\\", "/"),
        "changed_file_snapshots": changed_file_snapshots,
    }


def _backup_root_for(workspace_root: Path) -> Path:
    applied_at = datetime.now(UTC).isoformat()
    day = applied_at[:10]
    stamp = applied_at.replace(":", "").replace("+", "_").replace(".", "_")
    return workspace_root.resolve() / ".spirit-backups" / day / f"approved-diff-{stamp}"


def _backup_root() -> Path:
    return _backup_root_for(_workspace_root())


def _write_backup_manifest(
    *,
    manifest_path: Path,
    workspace_root: Path,
    approved_diff_path: Path,
    changed_files: list[dict[str, Any]],
    backed_up_files: list[dict[str, Any]],
    stage: str,
) -> None:
    payload = {
        "created_at": _now_iso(),
        "stage": stage,
        "workspace_root": str(workspace_root),
        "approved_diff_path": str(approved_diff_path.relative_to(workspace_root)).replace("\\", "/"),
        "approved_diff_sha256": _sha256_file(approved_diff_path),
        "changed_files": changed_files,
        "backed_up_files": backed_up_files,
        "rollback_hint": "Rollback by restoring backed_up_files from backup_path after reviewing approved.diff and current git diff.",
    }
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _finalize_backup_manifest(
    *,
    workspace_root: Path,
    manifest_path: str,
    audit_record: dict[str, Any],
) -> None:
    path = (workspace_root / manifest_path).resolve()
    if not _is_relative_to(path, workspace_root) or not path.is_file():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(payload, dict):
        return
    payload.update(
        {
            "stage": "applied",
            "applied_at": audit_record["approved_at"],
            "approved_by": audit_record["approved_by"],
            "action": audit_record["action"],
            "task_id": audit_record["task_id"],
            "audit_record": audit_record,
        }
    )
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
                architect_reason,
                causal_events_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                description = excluded.description,
                status = excluded.status,
                created_at = excluded.created_at,
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
                architect_reason = excluded.architect_reason,
                causal_events_json = excluded.causal_events_json
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
                json.dumps(task.causal_events[-100:]),
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
                architect_reason,
                causal_events_json
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
        causal_events=_json_value(row["causal_events_json"], []),
    )


def _load_recent_tasks(*, limit: int) -> list[LongRunningTask]:
    with closing(_connect()) as connection:
        _initialize_store(connection)
        rows = connection.execute(
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
                architect_reason,
                causal_events_json
            FROM long_running_tasks
            ORDER BY updated_at DESC, created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [_task_from_row(row) for row in rows]


def _task_from_row(row: sqlite3.Row) -> LongRunningTask:
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
        causal_events=_json_value(row["causal_events_json"], []),
    )


def _task_queue_item(task: LongRunningTask) -> dict[str, Any]:
    allowed_files = _task_allowed_files(task)
    blocker = _task_queue_blocker(task)
    scope_key = _task_scope_key(task)
    return {
        "task_id": task.id,
        "title": _task_queue_title(task.description),
        "worker": task.current_agent_role,
        "mode": "read_only_status_tracking",
        "status": task.status,
        "scope_key": scope_key,
        "write_capable": _task_is_write_capable(task),
        "target_file": allowed_files[0] if allowed_files else None,
        "allowed_files": allowed_files,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "blocker": blocker,
        "worker_lanes": _worker_lanes_for_task(task),
        "next_safe_action": task.next_action,
    }


def _worker_lanes_for_task(task: LongRunningTask) -> list[dict[str, Any]]:
    active_role = str(task.current_agent_role or "architect")
    has_diff = any(
        isinstance(diff, dict) and str(diff.get("diff") or "").strip()
        for diff in task.open_diffs
    )
    verification = _current_post_apply_verification(task)
    verifier_status = (
        "evidence"
        if isinstance(verification, dict) and verification.get("status")
        else "waiting"
    )
    return [
        _worker_lane(
            "codex_cli",
            "Codex CLI",
            "evidence" if active_role in {"coder", "debugger"} or has_diff else "waiting",
            "readonly/proposal evidence",
            "Codex output is evidence only; Source Proxy approval gates remain final.",
        ),
        _worker_lane(
            "deterministic_verifier",
            "Deterministic verifier",
            verifier_status,
            "diff and post-apply verification evidence",
            "Verifier output cannot apply, commit, or push.",
        ),
        _worker_lane(
            "reviewer",
            "Reviewer",
            "evidence" if has_diff else "waiting",
            "review findings",
            "Reviewer findings are advisory until a separate approval gate passes.",
        ),
        _worker_lane(
            "cartographer",
            "Cartographer",
            "waiting",
            "repo-state evidence",
            "Cartographer lane is read-only and cannot write project files.",
        ),
        _worker_lane(
            "scout_intake",
            "Scout intake",
            "waiting",
            "source intake evidence",
            "Scout intake is read-only and cannot mutate Source Proxy tasks.",
        ),
        _worker_lane(
            "local_model_reviewer",
            "Local model reviewer",
            "config_blocked",
            "future review evidence",
            "Local model reviewer is not wired into task execution.",
        ),
    ]


def _worker_lane(
    lane_id: str,
    label: str,
    status: str,
    evidence_type: str,
    note: str,
) -> dict[str, Any]:
    return {
        "id": lane_id,
        "label": label,
        "status": status,
        "mode": "read_only_evidence",
        "evidence_type": evidence_type,
        "approval_authority": False,
        "apply_authority": False,
        "commit_authority": False,
        "push_authority": False,
        "note": note,
    }


def _task_allowed_files(task: LongRunningTask) -> list[str]:
    files: list[str] = []
    for diff in task.open_diffs:
        if not isinstance(diff, dict):
            continue
        for changed_file in diff.get("changed_files", []):
            if isinstance(changed_file, dict):
                path = str(changed_file.get("path") or "").strip()
                if path and path not in files:
                    files.append(path)
    return files


def _task_scope_key(task: LongRunningTask) -> str:
    allowed_files = _task_allowed_files(task)
    if allowed_files:
        return _normalize_scope_key(allowed_files[0])
    target = _target_file_from_task_text(task.description)
    if target:
        return _normalize_scope_key(target)
    return ""


def _target_file_from_task_text(description: str) -> str:
    for pattern in (
        r"(?im)^target file:\s*([^\n,;]+)",
        r"(?im)\btarget file:\s*([^\n,;]+)",
        r"(?im)^allowed files:\s*([^\n,;]+)",
        r"(?im)\ballowed files:\s*([^\n,;]+)",
    ):
        match = re.search(pattern, description)
        if match:
            return match.group(1).strip().strip("`'\".,;")
    return ""


def _normalize_scope_key(scope_key: str) -> str:
    return scope_key.strip().replace("\\", "/").lower()


def _scope_is_dummy_product_site(scope_key: str) -> bool:
    normalized = _normalize_scope_key(scope_key)
    dummy_root = _normalize_scope_key(DUMMY_PRODUCT_SITE_ROOT)
    return normalized == f"{dummy_root}**" or normalized.startswith(dummy_root)


def _task_is_write_capable(task: LongRunningTask) -> bool:
    lowered = task.description.lower()
    read_only_markers = (
        "read-only",
        "read only",
        "review only",
        "review-only",
        "analysis only",
        "verification only",
    )
    if any(marker in lowered for marker in read_only_markers):
        return False
    return bool(_task_scope_key(task))


def _write_scope_conflict_for_task(task: LongRunningTask) -> dict[str, str] | None:
    candidate_scope = _task_scope_key(task)
    if not candidate_scope or not _task_is_write_capable(task):
        return None
    for existing in _live_long_running_tasks():
        if existing.id == task.id or not _task_is_write_capable(existing):
            continue
        if _task_scope_key(existing) == candidate_scope:
            return {
                "task_id": existing.id,
                "scope_key": candidate_scope,
            }
    return None


def _live_long_running_tasks() -> list[LongRunningTask]:
    terminal = _terminal_or_waiting_statuses()
    combined: dict[str, LongRunningTask] = {
        task.id: task
        for task in _load_recent_tasks(limit=MAX_LONG_TASKS)
        if task.status not in terminal
        and not _task_has_pre_execution_safety_block(task)
        and not _task_is_abandoned_pre_preview_write_lock(task)
    }
    for task in _tasks.values():
        if (
            task.status not in terminal
            and not _task_has_pre_execution_safety_block(task)
            and not _task_is_abandoned_pre_preview_write_lock(task)
        ):
            combined[task.id] = task
    return list(combined.values())


def _task_queue_blocker(task: LongRunningTask) -> str | None:
    if task.status in {
        "blocked",
        "blocked_after_retries",
        "blocked_by_review",
        "coder_config_blocked",
        "failed_needs_human",
        "verification_failed",
        "applied_verification_failed",
    }:
        return (
            _task_blocker_reason_code(task.truncated_test_results)
            or task.architect_reason
            or task.status
        )
    return None


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
        if result.reason == "no_explicit_target":
            task.architect_status = "blocked"
            task.architect_reason = "target_unresolved"
            task.status = "blocked"
            _set_task_role(task, "architect", reason="architect_target_unresolved")
            task.truncated_test_results = (
                "target_unresolved: No safe implementation file could be resolved "
                "from the task text."
            )
            task.steps = _append_unique_steps(
                task.steps,
                [
                    "Architect blocked before LLM planning: target_unresolved.",
                    "Add a Target file: line or mention one existing repo-relative file.",
                ],
            )
            return
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
            architect_reason TEXT NOT NULL DEFAULT '',
            causal_events_json TEXT NOT NULL DEFAULT '[]'
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
    _ensure_column(
        connection,
        "causal_events_json",
        "TEXT NOT NULL DEFAULT '[]'",
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
    """Regenerate compressed context before the coder LLM runs (best-effort).

    Stale bundles are how you get ``patch does not apply`` theatre. If npm,
    repomix, or Headroom is missing/offline, we log and carry on with whatever
    XML is already on disk.
    """
    try:
        print(f"[coder] Refreshing compressed context bundle at {root} ...")
        result = subprocess.run(
            ["npm", "run", "context:compress"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
        if result.returncode == 0:
            print(
                f"[coder] compressed context refreshed successfully "
                f"({len(result.stdout)} chars)"
            )
        else:
            print(f"[coder] context refresh warning (non-zero exit): {result.stderr.strip()}")
    except Exception as exc:  # noqa: BLE001 — never fail the swarm on repomix
        print(f"[coder] context refresh failed (non-fatal): {exc}")


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
    from source_proxy.safety.paths import normalize_repo_path_candidate

    return normalize_repo_path_candidate(normalized)


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


DUMMY_PRODUCT_SITE_ROOT = "tests/ui-agent-trials/fixtures/dummy-product-site/"
DUMMY_PRODUCT_SITE_STARTER_FILES = (
    "README.md",
    "package.json",
    "index.html",
    "src/main.js",
    "src/products.js",
    "src/styles.css",
)
DUMMY_PRODUCT_SITE_MAX_FILES = 12
DUMMY_PRODUCT_SITE_MAX_LINES_PER_FILE = 240
DUMMY_PRODUCT_SITE_MAX_TOTAL_LINES = 900
DUMMY_PRODUCT_SITE_BLACKLIST_KEYWORDS = (
    "api_key",
    "apikey",
    "bearer ",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
)
DUMMY_PRODUCT_SITE_REPAIR_MIN_VARIANCE = 0.02
DUMMY_PRODUCT_SITE_INDEX = f"{DUMMY_PRODUCT_SITE_ROOT}index.html"
DUMMY_PRODUCT_SITE_MAIN = f"{DUMMY_PRODUCT_SITE_ROOT}src/main.js"
DUMMY_PRODUCT_SITE_PRODUCTS = f"{DUMMY_PRODUCT_SITE_ROOT}src/products.js"
DUMMY_PRODUCT_SITE_STYLES = f"{DUMMY_PRODUCT_SITE_ROOT}src/styles.css"
PROMPT3_STATIC_CLASSIC_RETRY_FEEDBACK = (
    "Your previous diff used static import but did not change index.html to type=module. "
    "Return a corrected diff that changes index.html to module script and imports products in src/main.js."
)


def _dummy_product_site_prompt3_diff_violations(
    *,
    root: Path,
    unified_diff: str,
    replacement_target: str,
    replacement_content: str,
) -> list[str]:
    normalized_target = replacement_target.replace("\\", "/").lstrip("./")
    if normalized_target != DUMMY_PRODUCT_SITE_MAIN:
        return []
    diff_text = (unified_diff or "").replace("\r\n", "\n").replace("\r", "\n")
    content = replacement_content or ""
    try:
        current_index = (root / DUMMY_PRODUCT_SITE_INDEX).read_text(
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        current_index = ""

    violations: list[str] = []
    has_dynamic_import = bool(re.search(r"import\s*\(\s*['\"]\.\/products\.js['\"]\s*\)", content))
    has_static_import = bool(re.search(r"import\s+[\s\S]*?\s+from\s*['\"]\.\/products\.js['\"]", content))
    index_already_module = bool(re.search(r"<script\b[^>]*type=['\"]module['\"][^>]*src=['\"]src/main\.js['\"]", current_index))
    diff_adds_module_script = bool(
        re.search(r"^\+\s*<script\b[^>]*type=['\"]module['\"][^>]*src=['\"]src/main\.js['\"]", diff_text, re.MULTILINE)
    )
    diff_removes_module_script = bool(
        re.search(r"^-\s*<script\b[^>]*type=['\"]module['\"][^>]*src=['\"]src/main\.js['\"]", diff_text, re.MULTILINE)
    )
    has_module_wiring = diff_adds_module_script or (index_already_module and not diff_removes_module_script)

    if has_static_import and not has_module_wiring:
        violations.append("STATIC_IMPORT_CLASSIC_SCRIPT")
    if not has_static_import and not has_dynamic_import:
        violations.append("MISSING_PRODUCTS_IMPORT")
    if re.search(r"\b(?:const|let|var)\s+products\s*=\s*\[", content) or (
        "Product A" in content and "Product F" in content
    ):
        violations.append("PRODUCT_DATA_DUPLICATED")
    if re.search(r"^\+.*<(?:article|div)\b[^>]*(?:product-card|card)", diff_text, re.MULTILINE) and DUMMY_PRODUCT_SITE_INDEX in diff_text:
        violations.append("HARDCODED_INDEX_CARDS")

    return list(dict.fromkeys(violations))


def _dummy_product_site_model_timeout_seconds() -> float:
    raw = os.getenv("SOURCE_PROXY_DUMMY_PRODUCT_SITE_MODEL_TIMEOUT_SECONDS", "45").strip()
    try:
        return max(5.0, min(float(raw), 180.0))
    except ValueError:
        return 45.0


def _dummy_product_site_existing_starter_files_present(root: Path) -> bool:
    try:
        fixture_root = (root / DUMMY_PRODUCT_SITE_ROOT).resolve()
        if not fixture_root.is_dir():
            return False
        combined = []
        for expected in DUMMY_PRODUCT_SITE_STARTER_FILES:
            path = (fixture_root / expected).resolve()
            if not path.is_file():
                return False
            content = path.read_text(encoding="utf-8", errors="replace")
            if not content.strip():
                return False
            combined.append(content)
        return "lumacart" in "\n".join(combined).lower()
    except Exception:
        return False


def _dummy_product_site_already_satisfied_payload(*, diagnostics: dict[str, Any]) -> dict[str, Any]:
    satisfied_diagnostics = {
        **diagnostics,
        "validation_status": "already_satisfied",
        "already_satisfied": True,
        "no_changes_needed": True,
        "existing_starter_files_present": True,
        "generated_diff_length": 0,
        "normalized_diff_length": 0,
        "generated_diff_by_backend": False,
        "diff_source": "already_satisfied_existing_dummy_product_site",
        "generation_source": "disk_inspection",
        "model_output_classification": "already_satisfied_noop",
        "trial_result_trust_status": "existing_files_verified_no_diff_needed",
        "recommended_next_action": "Prompt 1 already satisfied; continue with the next dummy-product-site prompt.",
        "checks_run": ["existing dummy product site starter files present"],
    }
    return {
        "proposed_diff": "",
        "target": DUMMY_PRODUCT_SITE_ROOT,
        "coder_notes": [
            "Existing LumaCart dummy product site starter files are already present.",
            "CODER_NO_CHANGES_NEEDED: Prompt 1 already satisfied.",
        ],
        "coder_diagnostics": satisfied_diagnostics,
        "coderDiagnostics": satisfied_diagnostics,
        "bundle": None,
        "coder_agent_local_diff": False,
        "coderAgentLocalDiff": False,
        "coder_blocked": False,
        "coderBlocked": False,
        "already_satisfied": True,
        "alreadySatisfied": True,
        "changed_files": [],
        "checks_run": ["existing dummy product site starter files present"],
        "reason_code": "coder_no_changes_needed",
        "reasonCode": "coder_no_changes_needed",
        "blocked_reason": "",
        "blockedReason": "",
        "needed_context": "",
        "neededContext": "",
        "status": "already_satisfied",
        "message": "Prompt 1 already satisfied: LumaCart starter files already exist.",
    }


def _dummy_product_site_product_data_already_satisfied_payload(
    *,
    diagnostics: dict[str, Any],
    validation: dict[str, Any],
) -> dict[str, Any]:
    satisfied_diagnostics = {
        **diagnostics,
        "validation_status": "already_satisfied",
        "already_satisfied": True,
        "no_changes_needed": True,
        "existing_product_data_present": True,
        "existing_product_data_validation": validation,
        "generated_diff_length": 0,
        "normalized_diff_length": 0,
        "generated_diff_by_backend": False,
        "diff_source": "already_satisfied_existing_dummy_product_data",
        "generation_source": "disk_inspection",
        "model_output_classification": "already_satisfied_noop",
        "trial_result_trust_status": "existing_product_data_verified_no_diff_needed",
        "recommended_next_action": "Prompt 2 already satisfied; continue with Prompt 3 or reverse the fixture before rerunning Prompt 2 for a fresh apply proof.",
        "checks_run": ["existing Prompt 2 product data field validation"],
        "changed_files": [],
        "final_reason_code": "coder_no_changes_needed",
        "diff_produced": False,
        "apply_attempted": False,
    }
    return {
        "proposed_diff": "",
        "target": DUMMY_PRODUCT_SITE_PRODUCTS,
        "coder_notes": [
            "Existing LumaCart product data already satisfies Prompt 2.",
            "CODER_NO_CHANGES_NEEDED: Prompt 2 already satisfied.",
        ],
        "coder_diagnostics": satisfied_diagnostics,
        "coderDiagnostics": satisfied_diagnostics,
        "bundle": None,
        "coder_agent_local_diff": False,
        "coderAgentLocalDiff": False,
        "coder_blocked": False,
        "coderBlocked": False,
        "already_satisfied": True,
        "alreadySatisfied": True,
        "changed_files": [],
        "checks_run": ["existing Prompt 2 product data field validation"],
        "reason_code": "coder_no_changes_needed",
        "reasonCode": "coder_no_changes_needed",
        "blocked_reason": "",
        "blockedReason": "",
        "needed_context": "",
        "neededContext": "",
        "status": "already_satisfied",
        "message": "Prompt 2 already satisfied: LumaCart product data already has 6 valid products.",
        "simple_reason": "Prompt 2 already satisfied: existing src/products.js has id, name, price, category, and description for 6 products.",
    }


def _call_dummy_product_site_llm_with_wall_timeout(prompt: str, selected_alias: str, timeout_seconds: float) -> str:
    result_queue: queue.Queue[tuple[str, Any]] = queue.Queue(maxsize=1)

    def worker() -> None:
        try:
            result = _call_dummy_product_site_llm_raw(prompt, selected_alias, timeout_seconds)
            result_queue.put(("ok", result), block=False)
        except Exception as error:  # noqa: BLE001
            result_queue.put(("error", error), block=False)

    thread = threading.Thread(target=worker, name="dummy-product-site-coder", daemon=True)
    thread.start()
    try:
        status, value = result_queue.get(timeout=timeout_seconds)
    except queue.Empty as error:
        raise TimeoutError(f"Dummy product site Coder model call timed out after {timeout_seconds:g}s") from error
    if status == "error":
        raise value
    return str(value or "")


def _call_dummy_product_site_llm_raw(prompt: str, selected_alias: str, timeout_seconds: float) -> str:
    if _dummy_product_site_direct_ollama_enabled(selected_alias):
        return _call_dummy_product_site_ollama_direct(prompt, selected_alias, timeout_seconds)
    return _call_coder_llm(
        prompt,
        model_alias=selected_alias,
        timeout_seconds=timeout_seconds,
        num_retries=0,
    )


def _dummy_product_site_direct_ollama_enabled(selected_alias: str) -> bool:
    if os.getenv("SOURCE_PROXY_DUMMY_PRODUCT_SITE_DIRECT_OLLAMA", "1").strip().lower() in {"0", "false", "no", "off"}:
        return False
    provider = route_provider_for_alias(selected_alias)
    return provider in {"ollama", "local"} or selected_alias in {"coder", "local"}


def _call_dummy_product_site_ollama_direct(prompt: str, selected_alias: str, timeout_seconds: float) -> str:
    central_gate_check("model_call", run_id=f"dummy_product_site_ollama:{selected_alias}")
    resolved_model = route_model_for_alias(selected_alias) or ""
    model = resolved_model.removeprefix("ollama_chat/") or resolve_coder_ollama_model_name(probe=False)
    route = resolve_ollama_route(probe=False)
    api_base = (route.api_base or "http://127.0.0.1:11434").rstrip("/")
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0,
            "num_ctx": int(os.getenv("SOURCE_PROXY_DUMMY_PRODUCT_SITE_NUM_CTX", "8192")),
            "num_predict": int(os.getenv("SOURCE_PROXY_DUMMY_PRODUCT_SITE_NUM_PREDICT", "1200")),
        },
    }
    request = urllib.request.Request(
        f"{api_base}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        response_payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(response_payload, dict):
        return ""
    raw = response_payload.get("response")
    return raw if isinstance(raw, str) else ""


def _dummy_product_site_model_failure_payload(
    *,
    diagnostics: dict[str, Any],
    error: Exception,
    repair: bool = False,
    timeout_seconds: float | None = None,
) -> dict[str, Any]:
    error_text = str(error)
    error_kind = type(error).__name__
    timed_out = "timeout" in error_kind.lower() or "timed out" in error_text.lower() or "timeout" in error_text.lower()
    reason_code = "coder_model_timeout" if timed_out else "coder_model_router_error"
    prompt_label = (
        "Prompt 3"
        if diagnostics.get("selected_prompt_number") == 3
        or diagnostics.get("selected_prompt_id") == "coder-003-render-product-cards"
        else "Prompt 1"
    )
    diagnostics["validation_status"] = reason_code
    diagnostics["trial_result_trust_status"] = "model_output_not_usable"
    diagnostics["recommended_next_action"] = (
        "retry_after_local_coder_model_recovers"
        if timed_out
        else "check_model_route_or_use_configured_stronger_model"
    )
    diagnostics["model_error_type"] = error_kind
    diagnostics["model_error_message"] = error_text[:500]
    if timeout_seconds is not None:
        diagnostics["model_timeout_seconds"] = timeout_seconds
    if repair:
        diagnostics["repair_attempted"] = True
        diagnostics["repair_error_message"] = error_text
    return _coder_blocked_payload(
        target=DUMMY_PRODUCT_SITE_ROOT,
        notes=[f"CODER_BLOCKED reason_code: {reason_code}"],
        diagnostics=diagnostics,
        bundle_name=None,
        reason=(
            f"Coder model timed out before returning {prompt_label} file blocks."
            if timed_out
            else "Coder model/router call failed."
        ),
        needed_context=(
            f"{prompt_label} exceeded the bounded {timeout_seconds:g}s model budget; warm or repair the local Coder model, then retry."
            if timed_out and timeout_seconds is not None
            else error_text
        ),
        reason_code=reason_code,
    )


def propose_dummy_product_site_create_diff(
    *,
    task: str,
    workspace_root: Path | None = None,
    llm_call: Callable[[str, str], str] | None = None,
    model_alias: str | None = None,
) -> dict[str, Any]:
    """Model-authored multi-file create path for Coder 001 LumaCart."""
    root = (workspace_root or _workspace_root()).resolve()
    selected_alias = model_alias or _dummy_product_site_create_model_alias()
    diagnostics: dict[str, Any] = {
        **_base_coder_diagnostics(DUMMY_PRODUCT_SITE_ROOT),
        "context_mode": "dummy_product_site_create",
        "context_slices": [],
        "target_exists": (root / DUMMY_PRODUCT_SITE_ROOT).is_dir(),
        "target_action": "create file bundle",
        "trial_mode": "live_apply",
        "expected_result_state": "PASS_DUMMY_PROJECT_INIT",
        "expected_root": DUMMY_PRODUCT_SITE_ROOT,
        "expected_starter_files": list(DUMMY_PRODUCT_SITE_STARTER_FILES),
        "backend_caps": {
            "max_files": DUMMY_PRODUCT_SITE_MAX_FILES,
            "max_lines_per_file": DUMMY_PRODUCT_SITE_MAX_LINES_PER_FILE,
            "max_total_lines": DUMMY_PRODUCT_SITE_MAX_TOTAL_LINES,
            "blacklist_keywords": list(DUMMY_PRODUCT_SITE_BLACKLIST_KEYWORDS),
        },
        "forbidden_paths": [
            "src/app/**",
            "src/components/**",
            "src/lib/**",
            "source_proxy/**",
            "docs/**",
            ".env*",
            "package.json",
            "package-lock.json",
        ],
    }
    _set_trial_generation_provenance(diagnostics, trial_mode=True)
    _record_coder_provider_model_truth(
        diagnostics,
        selected_alias=selected_alias,
        provider_call_made=False,
    )
    if _dummy_product_site_existing_starter_files_present(root):
        return _dummy_product_site_already_satisfied_payload(diagnostics=diagnostics)
    alias_error = None if llm_call is not None else _coder_model_alias_configuration_error(selected_alias)
    if alias_error is not None:
        reason, needed_context = alias_error
        diagnostics["validation_status"] = "coder_model_not_configured"
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_ROOT,
            notes=["CODER_BLOCKED reason_code: coder_model_not_configured"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason=needed_context,
            needed_context=reason,
            reason_code="coder_model_not_configured",
        )
    prompt = _render_dummy_product_site_create_prompt(task)
    model_timeout_seconds = _dummy_product_site_model_timeout_seconds()
    try:
        _record_coder_provider_model_truth(
            diagnostics,
            selected_alias=selected_alias,
            provider_call_made=True,
        )
        raw_response = (
            llm_call(prompt, selected_alias)
            if llm_call is not None
            else _call_dummy_product_site_llm_with_wall_timeout(
                prompt,
                selected_alias,
                model_timeout_seconds,
            )
        )
    except Exception as error:  # noqa: BLE001
        return _dummy_product_site_model_failure_payload(
            diagnostics=diagnostics,
            error=error,
            timeout_seconds=model_timeout_seconds,
        )
    diagnostics["generation_source"] = "model"
    diagnostics["diff_source"] = "pending_backend_diff_from_model_file_bundle"
    diagnostics["raw_response_length"] = len(raw_response or "")
    diagnostics["raw_response_excerpt_safe"] = _safe_raw_response_excerpt(raw_response or "")
    diagnostics["model_output_classification"] = "model_structured_file_bundle"
    files, parse_error = _parse_dummy_product_site_file_bundle(raw_response or "")
    parse_meta = _dummy_product_site_parse_meta(raw_response or "", files)
    diagnostics.update(parse_meta)
    if parse_error:
        repair_prompt = _render_dummy_product_site_create_repair_prompt(
            task,
            parse_error=parse_error,
            raw_response=raw_response or "",
        )
        try:
            repair_response = (
                llm_call(repair_prompt, selected_alias)
                if llm_call is not None
                else _call_dummy_product_site_llm_with_wall_timeout(
                    repair_prompt,
                    selected_alias,
                    model_timeout_seconds,
                )
            )
        except Exception as error:  # noqa: BLE001
            return _dummy_product_site_model_failure_payload(
                diagnostics=diagnostics,
                error=error,
                repair=True,
                timeout_seconds=model_timeout_seconds,
            )
        diagnostics["repair_attempted"] = True
        diagnostics["repair_raw_response_length"] = len(repair_response or "")
        diagnostics["repair_raw_response_excerpt_safe"] = _safe_raw_response_excerpt(repair_response or "")
        repair_variance = _character_variance(raw_response or "", repair_response or "")
        diagnostics["repair_character_variance"] = repair_variance
        diagnostics["repair_similarity_guard_min_variance"] = DUMMY_PRODUCT_SITE_REPAIR_MIN_VARIANCE
        if repair_variance < DUMMY_PRODUCT_SITE_REPAIR_MIN_VARIANCE:
            parse_error = "repair_response_too_similar_to_rejected_response"
            files = None
        else:
            files, parse_error = _parse_dummy_product_site_file_bundle(repair_response or "")
            repair_parse_meta = _dummy_product_site_parse_meta(repair_response or "", files)
            diagnostics.update(repair_parse_meta)
            diagnostics["parser_repair_used"] = not bool(parse_error)
    if parse_error:
        diagnostics["validation_status"] = "coder_file_bundle_validation_failed"
        diagnostics["parse_error_message"] = parse_error
        diagnostics["trial_result_trust_status"] = "model_output_not_usable"
        diagnostics["recommended_next_action"] = "retry_with_file_blocks_or_delimited_bundle"
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_ROOT,
            notes=["CODER_BLOCKED reason_code: coder_file_bundle_validation_failed"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason=parse_error,
            needed_context="Return only <file path=\"...\">...</file> blocks or <<<FILE: path ... >>> blocks under the dummy root.",
            reason_code="coder_file_bundle_validation_failed",
        )
    assert files is not None
    validation = _validate_dummy_product_site_file_bundle(files)
    diagnostics["content_validation"] = validation
    honesty_gate = _dummy_product_site_honesty_gate(files, task=task)
    diagnostics["structured_honesty_gate"] = honesty_gate
    if not validation["ok"]:
        diagnostics["validation_status"] = "coder_file_bundle_validation_failed"
        diagnostics["trial_result_trust_status"] = "model_output_not_usable"
        diagnostics["recommended_next_action"] = "retry_with_dummy_root_only_file_bundle"
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_ROOT,
            notes=["CODER_BLOCKED reason_code: coder_file_bundle_validation_failed"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason=str(validation["summary"]),
            needed_context=", ".join(str(item) for item in validation["missing"][:8]),
            reason_code="coder_file_bundle_validation_failed",
        )
    if honesty_gate["status"] == "blocked":
        diagnostics["validation_status"] = "coder_file_bundle_validation_failed"
        diagnostics["trial_result_trust_status"] = "model_output_not_usable"
        diagnostics["recommended_next_action"] = "retry_with_honest_dummy_product_site_bundle"
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_ROOT,
            notes=["CODER_BLOCKED reason_code: coder_file_bundle_validation_failed"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason=str(honesty_gate["summary"]),
            needed_context=", ".join(str(item) for item in honesty_gate["findings"][:8]),
            reason_code="coder_file_bundle_validation_failed",
        )
    diffs: list[str] = []
    for file in files:
        diffs.append(generate_unified_diff_from_content(root, file["path"], file["content"]))
    unified = ("\n".join(diff.strip("\n") for diff in diffs if diff.strip()) + "\n").replace("\r\n", "\n")
    if not unified.strip():
        diagnostics["validation_status"] = "coder_backend_diff_generation_failed"
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_ROOT,
            notes=["CODER_BLOCKED reason_code: coder_backend_diff_generation_failed"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason="Model-authored file bundle produced an empty diff.",
            needed_context="Retry Coder 001 with files that differ from disk.",
            reason_code="coder_backend_diff_generation_failed",
        )
    apply_ok, apply_error = _git_apply_generated_diff_ok(root, unified)
    if not apply_ok:
        diagnostics["validation_status"] = "coder_backend_diff_generation_failed"
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_ROOT,
            notes=["CODER_BLOCKED reason_code: coder_backend_diff_generation_failed"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason=f"Generated diff did not pass git apply --check: {apply_error}",
            needed_context="Retry with a clean file bundle under the dummy root.",
            reason_code="coder_backend_diff_generation_failed",
        )
    changed_files = [file["path"] for file in files]
    diagnostics["validation_status"] = "preview_ready"
    diagnostics["changed_files"] = changed_files
    diagnostics["generated_diff_length"] = len(unified)
    diagnostics["generated_diff_by_backend"] = True
    diagnostics["diff_source"] = "model_authored_file_bundle_backend_converted_to_diff"
    diagnostics["trial_result_trust_status"] = "model_authored_diff_proven"
    diagnostics["recommended_next_action"] = "preview_and_apply_selected_prompt_diff"
    return {
        "proposed_diff": unified,
        "target": DUMMY_PRODUCT_SITE_ROOT,
        "coder_notes": [
            "Model-authored dummy product site file bundle validated.",
            "CODER_PREVIEW reason_code: dummy_product_site_create_bundle",
        ],
        "bundle": None,
        "reason_code": "dummy_product_site_create_bundle",
        "coder_diagnostics": diagnostics,
        "changed_files": changed_files,
        "checks_run": ["git apply --check"],
    }


def propose_dummy_product_site_product_data_diff(
    *,
    task: str,
    workspace_root: Path | None = None,
    llm_call: Callable[[str, str], str] | None = None,
    model_alias: str | None = None,
) -> dict[str, Any]:
    root = (workspace_root or _workspace_root()).resolve()
    selected_alias = model_alias or _dummy_product_site_create_model_alias()
    target_abs = root / DUMMY_PRODUCT_SITE_PRODUCTS
    diagnostics: dict[str, Any] = {
        "context_mode": "dummy_product_site_product_data",
        "context_slices": _dummy_product_site_product_data_context_slices(root),
        "target_exists": target_abs.is_file(),
        "source_proxy_run_id": f"prompt2-{uuid4().hex[:12]}",
        "scaffold_used": False,
        "fallback_used": False,
        "generated_diff_by_backend": False,
        "provider_call_made": False,
        "stage_events": [],
    }
    if not target_abs.is_file():
        diagnostics["final_reason_code"] = "target_missing"
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_PRODUCTS,
            notes=["CODER_BLOCKED reason_code: target_missing"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason="Prompt 2 requires the existing LumaCart src/products.js file.",
            needed_context="Run or restore Prompt 1 before Prompt 2.",
            reason_code="target_missing",
        )

    current_product_data = target_abs.read_text(encoding="utf-8", errors="replace")
    existing_validation = _validate_dummy_product_site_product_data_files(
        [{"path": DUMMY_PRODUCT_SITE_PRODUCTS, "content": current_product_data}]
    )
    diagnostics["existing_product_data_validation"] = existing_validation
    if existing_validation["ok"]:
        return _dummy_product_site_product_data_already_satisfied_payload(
            diagnostics=diagnostics,
            validation=existing_validation,
        )

    prompt = _render_dummy_product_site_product_data_prompt(task, root)
    model_timeout_seconds = _dummy_product_site_model_timeout_seconds()
    attempt_started = time.perf_counter()
    diagnostics["model_alias"] = selected_alias
    diagnostics["model_name"] = route_model_for_alias(selected_alias) or ""
    diagnostics["prompt_context_byte_size"] = len(prompt.encode("utf-8"))
    _record_prompt3_stage(
        diagnostics,
        "prompt2_model_call_started",
        model_alias=selected_alias,
        model_name=diagnostics["model_name"],
        timeout_seconds=model_timeout_seconds,
        prompt_context_byte_size=diagnostics["prompt_context_byte_size"],
    )
    try:
        _record_coder_provider_model_truth(
            diagnostics,
            selected_alias=selected_alias,
            provider_call_made=True,
        )
        raw_response = (
            llm_call(prompt, selected_alias)
            if llm_call is not None
            else _call_dummy_product_site_llm_with_wall_timeout(
                prompt,
                selected_alias,
                model_timeout_seconds,
            )
        )
    except Exception as error:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - attempt_started) * 1000
        timed_out = (
            "timeout" in type(error).__name__.lower()
            or "timeout" in str(error).lower()
            or "timed out" in str(error).lower()
        )
        _record_prompt3_stage(
            diagnostics,
            "prompt2_model_call_timeout" if timed_out else "prompt2_model_call_failed",
            elapsed_ms=elapsed_ms,
            error_type=type(error).__name__,
            error_message=str(error)[:240],
        )
        diagnostics["model_call_elapsed_ms"] = round(elapsed_ms, 2)
        diagnostics["final_reason_code"] = "coder_model_timeout" if timed_out else "coder_model_router_error"
        diagnostics["diff_produced"] = False
        diagnostics["apply_attempted"] = False
        return _dummy_product_site_model_failure_payload(
            diagnostics=diagnostics,
            error=error,
            timeout_seconds=model_timeout_seconds,
        )

    elapsed_ms = (time.perf_counter() - attempt_started) * 1000
    _record_prompt3_stage(
        diagnostics,
        "prompt2_model_call_finished",
        elapsed_ms=elapsed_ms,
        raw_response_length=len(raw_response or ""),
    )
    diagnostics["model_call_elapsed_ms"] = round(elapsed_ms, 2)
    diagnostics["generation_source"] = "model"
    diagnostics["diff_source"] = "pending_backend_diff_from_model_prompt2_file_bundle"
    diagnostics["raw_response_length"] = len(raw_response or "")
    diagnostics["raw_response_excerpt_safe"] = _safe_raw_response_excerpt(raw_response or "")
    diagnostics["model_output_classification"] = "model_structured_file_bundle"

    files, parse_error = _parse_dummy_product_site_file_bundle(raw_response or "")
    diagnostics.update(_dummy_product_site_parse_meta(raw_response or "", files))
    if parse_error or files is None:
        diagnostics["validation_status"] = "prompt2_file_bundle_validation_failed"
        diagnostics["parse_status"] = "failed"
        diagnostics["parse_error_message"] = parse_error or "No files parsed."
        diagnostics["trial_result_trust_status"] = "model_output_not_usable"
        diagnostics["final_reason_code"] = "coder_file_bundle_validation_failed"
        diagnostics["diff_produced"] = False
        diagnostics["apply_attempted"] = False
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_PRODUCTS,
            notes=["CODER_BLOCKED reason_code: coder_file_bundle_validation_failed"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason=diagnostics["parse_error_message"],
            needed_context="Return only one file block for tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js.",
            reason_code="coder_file_bundle_validation_failed",
        )

    diagnostics["parse_status"] = "passed"
    validation = _validate_dummy_product_site_product_data_files(files)
    diagnostics["content_validation"] = validation
    if not validation["ok"]:
        reason_code = str(validation["missing"][0] if validation["missing"] else "PRODUCT_DATA_CONTRACT_FAILED")
        diagnostics["validation_status"] = "prompt2_contract_failed"
        diagnostics["trial_result_trust_status"] = "model_output_not_usable"
        diagnostics["recommended_next_action"] = "retry_prompt2_product_data_contract"
        diagnostics["final_reason_code"] = reason_code
        diagnostics["diff_produced"] = False
        diagnostics["apply_attempted"] = False
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_PRODUCTS,
            notes=[f"CODER_BLOCKED reason_code: {reason_code}"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason=str(validation["summary"]),
            needed_context=", ".join(str(item) for item in validation["missing"][:8]),
            reason_code=reason_code,
        )

    file = files[0]
    unified = _prompt3_git_header_diff(
        file["path"],
        generate_unified_diff_from_content(root, file["path"], file["content"]),
    )
    if not unified.strip():
        diagnostics["validation_status"] = "NO_DIFF"
        diagnostics["trial_result_trust_status"] = "model_output_not_usable"
        diagnostics["final_reason_code"] = "NO_DIFF"
        diagnostics["diff_produced"] = False
        diagnostics["apply_attempted"] = False
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_PRODUCTS,
            notes=["CODER_BLOCKED reason_code: NO_DIFF"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason="Model-authored Prompt 2 product data produced an empty diff.",
            needed_context="Return changed product data for src/products.js.",
            reason_code="NO_DIFF",
        )

    apply_ok, apply_error = _git_apply_generated_diff_ok(root, unified)
    if not apply_ok:
        diagnostics["validation_status"] = "coder_backend_diff_generation_failed"
        diagnostics["trial_result_trust_status"] = "model_output_not_usable"
        diagnostics["final_reason_code"] = "coder_backend_diff_generation_failed"
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_PRODUCTS,
            notes=["CODER_BLOCKED reason_code: coder_backend_diff_generation_failed"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason=f"Generated diff did not pass git apply --check: {apply_error}",
            needed_context="Retry with a clean Prompt 2 products.js file block under the dummy root.",
            reason_code="coder_backend_diff_generation_failed",
        )

    diagnostics["validation_status"] = "preview_ready"
    diagnostics["changed_files"] = [DUMMY_PRODUCT_SITE_PRODUCTS]
    diagnostics["generated_diff_length"] = len(unified)
    diagnostics["generated_diff_by_backend"] = True
    diagnostics["diff_produced"] = True
    diagnostics["apply_attempted"] = True
    diagnostics["diff_source"] = "model_authored_prompt2_file_bundle_backend_converted_to_diff"
    diagnostics["trial_result_trust_status"] = "model_authored_diff_proven"
    diagnostics["recommended_next_action"] = "preview_and_apply_selected_prompt_diff"
    diagnostics["final_reason_code"] = "dummy_product_site_prompt2_bundle"
    return {
        "proposed_diff": unified,
        "target": DUMMY_PRODUCT_SITE_PRODUCTS,
        "coder_notes": [
            "Model-authored Prompt 2 product data file bundle validated.",
            "CODER_PREVIEW reason_code: dummy_product_site_prompt2_bundle",
        ],
        "bundle": None,
        "reason_code": "dummy_product_site_prompt2_bundle",
        "coder_diagnostics": diagnostics,
        "changed_files": [DUMMY_PRODUCT_SITE_PRODUCTS],
        "checks_run": ["git apply --check", "product data field validation"],
    }


def propose_dummy_product_site_render_cards_diff(
    *,
    task: str,
    workspace_root: Path | None = None,
    llm_call: Callable[[str, str], str] | None = None,
    model_alias: str | None = None,
) -> dict[str, Any]:
    """Model-authored multi-file render path for Prompt 3 LumaCart cards."""
    root = (workspace_root or _workspace_root()).resolve()
    selected_alias = model_alias or _dummy_product_site_create_model_alias()
    diagnostics: dict[str, Any] = {
        **_base_coder_diagnostics(DUMMY_PRODUCT_SITE_ROOT),
        "source_proxy_run_id": f"prompt3-{uuid4().hex}",
        "context_mode": "dummy_product_site_render_cards",
        "context_slices": _dummy_product_site_prompt3_context_slices(root),
        "target_exists": (root / DUMMY_PRODUCT_SITE_ROOT).is_dir(),
        "target_action": "edit fixture files",
        "trial_mode": "live_apply",
        "expected_result_state": "PASS_PRODUCTS_RENDERED",
        "selected_prompt_id": "coder-003-render-product-cards",
        "selected_prompt_number": 3,
        "expected_root": DUMMY_PRODUCT_SITE_ROOT,
        "allowed_files": [
            DUMMY_PRODUCT_SITE_INDEX,
            DUMMY_PRODUCT_SITE_MAIN,
            DUMMY_PRODUCT_SITE_STYLES,
        ],
        "forbidden_paths": [
            f"{DUMMY_PRODUCT_SITE_ROOT}src/products.js",
            "src/app/**",
            "src/components/**",
            "src/lib/**",
            "source_proxy/**",
            "docs/**",
            ".env*",
            "package.json",
            "package-lock.json",
        ],
    }
    _set_trial_generation_provenance(diagnostics, trial_mode=True)
    _record_coder_provider_model_truth(
        diagnostics,
        selected_alias=selected_alias,
        provider_call_made=False,
    )
    _record_prompt3_stage(
        diagnostics,
        "coder_lane_probe",
        model_alias=selected_alias,
        model_name=route_model_for_alias(selected_alias) or "",
        coder_lane_available=selected_alias in available_model_aliases(),
        available_model_aliases=sorted(available_model_aliases()),
    )
    alias_error = None if llm_call is not None else _coder_model_alias_configuration_error(selected_alias)
    if alias_error is not None:
        reason, needed_context = alias_error
        diagnostics["validation_status"] = "coder_model_not_configured"
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_ROOT,
            notes=["CODER_BLOCKED reason_code: coder_model_not_configured"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason=needed_context,
            needed_context=reason,
            reason_code="coder_model_not_configured",
        )

    model_timeout_seconds = _dummy_product_site_model_timeout_seconds()
    prompt = _render_dummy_product_site_render_cards_prompt(task, root)
    diagnostics["prompt_context_byte_size"] = len(prompt.encode("utf-8"))
    diagnostics["prompt_context_char_count"] = len(prompt)
    diagnostics["context_slice_count"] = len(diagnostics.get("context_slices") or [])
    _record_prompt3_stage(
        diagnostics,
        "prompt_packet_assembled",
        prompt_context_byte_size=diagnostics["prompt_context_byte_size"],
        context_slice_count=diagnostics["context_slice_count"],
    )
    result = _call_and_validate_dummy_product_site_render_cards(
        root=root,
        prompt=prompt,
        selected_alias=selected_alias,
        model_timeout_seconds=model_timeout_seconds,
        llm_call=llm_call,
        diagnostics=diagnostics,
        attempt_label="initial",
    )
    if result.get("reason_code") == "STATIC_IMPORT_CLASSIC_SCRIPT":
        diagnostics["prompt3_retry_attempted"] = True
        diagnostics["prompt3_retry_reason"] = "STATIC_IMPORT_CLASSIC_SCRIPT"
        diagnostics["retry_feedback"] = PROMPT3_STATIC_CLASSIC_RETRY_FEEDBACK
        retry_prompt = _render_dummy_product_site_render_cards_retry_prompt(
            task,
            feedback=PROMPT3_STATIC_CLASSIC_RETRY_FEEDBACK,
            root=root,
        )
        result = _call_and_validate_dummy_product_site_render_cards(
            root=root,
            prompt=retry_prompt,
            selected_alias=selected_alias,
            model_timeout_seconds=model_timeout_seconds,
            llm_call=llm_call,
            diagnostics=diagnostics,
            attempt_label="retry",
        )
        diagnostics["retry_count"] = 1
        diagnostics["coder_attempt_count"] = 2
    return result


def _record_prompt3_stage(
    diagnostics: dict[str, Any],
    stage: str,
    *,
    elapsed_ms: float | None = None,
    **data: Any,
) -> None:
    timestamps = diagnostics.setdefault("stage_timestamps", {})
    if isinstance(timestamps, dict):
        timestamps[stage] = datetime.now(UTC).isoformat()
    elapsed = diagnostics.setdefault("elapsed_ms_by_stage", {})
    if isinstance(elapsed, dict) and elapsed_ms is not None:
        elapsed[stage] = round(elapsed_ms, 2)
    stages = diagnostics.setdefault("stage_events", [])
    if isinstance(stages, list):
        event = {"stage": stage}
        if elapsed_ms is not None:
            event["elapsed_ms"] = round(elapsed_ms, 2)
        event.update(data)
        stages.append(event)


def _call_and_validate_dummy_product_site_render_cards(
    *,
    root: Path,
    prompt: str,
    selected_alias: str,
    model_timeout_seconds: float,
    llm_call: Callable[[str, str], str] | None,
    diagnostics: dict[str, Any],
    attempt_label: str,
) -> dict[str, Any]:
    attempt_started = time.perf_counter()
    diagnostics["coder_attempt_count"] = max(int(diagnostics.get("coder_attempt_count") or 0), 1)
    diagnostics["retry_count"] = int(diagnostics.get("retry_count") or 0)
    diagnostics["model_alias"] = selected_alias
    diagnostics["model_name"] = route_model_for_alias(selected_alias) or ""
    diagnostics[f"{attempt_label}_prompt_context_byte_size"] = len(prompt.encode("utf-8"))
    _record_prompt3_stage(
        diagnostics,
        f"{attempt_label}_model_call_started",
        model_alias=selected_alias,
        model_name=diagnostics["model_name"],
        timeout_seconds=model_timeout_seconds,
        prompt_context_byte_size=diagnostics[f"{attempt_label}_prompt_context_byte_size"],
    )
    try:
        _record_coder_provider_model_truth(
            diagnostics,
            selected_alias=selected_alias,
            provider_call_made=True,
        )
        raw_response = (
            llm_call(prompt, selected_alias)
            if llm_call is not None
            else _call_dummy_product_site_llm_with_wall_timeout(
                prompt,
                selected_alias,
                model_timeout_seconds,
            )
        )
    except Exception as error:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - attempt_started) * 1000
        timed_out = "timeout" in type(error).__name__.lower() or "timeout" in str(error).lower() or "timed out" in str(error).lower()
        _record_prompt3_stage(
            diagnostics,
            f"{attempt_label}_{'model_call_timeout' if timed_out else 'model_call_failed'}",
            elapsed_ms=elapsed_ms,
            error_type=type(error).__name__,
            error_message=str(error)[:240],
        )
        diagnostics["model_call_started_at"] = diagnostics.get("stage_timestamps", {}).get(
            f"{attempt_label}_model_call_started"
        )
        diagnostics["model_call_timeout_at" if timed_out else "model_call_failed_at"] = diagnostics.get(
            "stage_timestamps", {}
        ).get(f"{attempt_label}_{'model_call_timeout' if timed_out else 'model_call_failed'}")
        diagnostics["model_call_elapsed_ms"] = round(elapsed_ms, 2)
        diagnostics["final_reason_code"] = "coder_model_timeout" if timed_out else "coder_model_router_error"
        diagnostics["diff_produced"] = False
        diagnostics["apply_attempted"] = False
        return _dummy_product_site_model_failure_payload(
            diagnostics=diagnostics,
            error=error,
            timeout_seconds=model_timeout_seconds,
        )

    elapsed_ms = (time.perf_counter() - attempt_started) * 1000
    _record_prompt3_stage(
        diagnostics,
        f"{attempt_label}_model_call_finished",
        elapsed_ms=elapsed_ms,
        raw_response_length=len(raw_response or ""),
    )
    diagnostics["model_call_started_at"] = diagnostics.get("stage_timestamps", {}).get(
        f"{attempt_label}_model_call_started"
    )
    diagnostics["model_call_finished_at"] = diagnostics.get("stage_timestamps", {}).get(
        f"{attempt_label}_model_call_finished"
    )
    diagnostics["model_call_elapsed_ms"] = round(elapsed_ms, 2)
    diagnostics["generation_source"] = "model"
    diagnostics["diff_source"] = "pending_backend_diff_from_model_prompt3_file_bundle"
    diagnostics["raw_model_response_sha256"] = _sha256_lf_trailing_newline_v1(raw_response or "")
    diagnostics["provenance_hash_normalization"] = "lf_trailing_newline_v1"
    diagnostics[f"{attempt_label}_raw_response_length"] = len(raw_response or "")
    diagnostics[f"{attempt_label}_raw_response_excerpt_safe"] = _safe_raw_response_excerpt(raw_response or "")
    diagnostics["raw_response_length"] = len(raw_response or "")
    diagnostics["raw_response_excerpt_safe"] = _safe_raw_response_excerpt(raw_response or "")
    diagnostics["model_output_classification"] = "model_structured_file_bundle"
    parse_started = time.perf_counter()
    _record_prompt3_stage(diagnostics, f"{attempt_label}_parse_started")
    files, parse_error = _parse_dummy_product_site_file_bundle(raw_response or "")
    _record_prompt3_stage(
        diagnostics,
        f"{attempt_label}_parse_done",
        elapsed_ms=(time.perf_counter() - parse_started) * 1000,
        parse_status="failed" if parse_error else "passed",
        parsed_file_count=len(files or []),
    )
    diagnostics.update(_dummy_product_site_parse_meta(raw_response or "", files))
    if parse_error:
        diagnostics["validation_status"] = "prompt3_file_bundle_validation_failed"
        diagnostics["parse_status"] = "failed"
        diagnostics["parse_error_message"] = parse_error
        diagnostics["trial_result_trust_status"] = "model_output_not_usable"
        diagnostics["final_reason_code"] = "coder_file_bundle_validation_failed"
        diagnostics["diff_produced"] = False
        diagnostics["apply_attempted"] = False
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_ROOT,
            notes=["CODER_BLOCKED reason_code: coder_file_bundle_validation_failed"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason=parse_error,
            needed_context="Return only Prompt 3 file blocks for index.html, src/main.js, and optional src/styles.css.",
            reason_code="coder_file_bundle_validation_failed",
        )

    assert files is not None
    diagnostics["parse_status"] = "passed"
    diagnostics["model_file_bundle_sha256"] = _sha256_lf_trailing_newline_v1(
        json.dumps(
            [{"path": file.get("path", ""), "content": file.get("content", "")} for file in files],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    validation_started = time.perf_counter()
    _record_prompt3_stage(diagnostics, f"{attempt_label}_validation_started")
    validation = _validate_dummy_product_site_prompt3_files(root, files)
    _record_prompt3_stage(
        diagnostics,
        f"{attempt_label}_validation_done",
        elapsed_ms=(time.perf_counter() - validation_started) * 1000,
        validation_status="passed" if validation["ok"] else "failed",
        validation_missing=validation.get("missing", []),
    )
    diagnostics["content_validation"] = validation
    if not validation["ok"]:
        reason_code = str(validation["missing"][0] if validation["missing"] else "PROMPT3_CONTRACT_FAILED")
        if reason_code != "STATIC_IMPORT_CLASSIC_SCRIPT":
            fallback = _dummy_product_site_prompt3_deterministic_recovery_payload(
                root=root,
                diagnostics=diagnostics,
                trigger_reason=reason_code,
            )
            if fallback is not None:
                return fallback
        diagnostics["validation_status"] = "prompt3_contract_failed"
        diagnostics["trial_result_trust_status"] = "model_output_not_usable"
        diagnostics["recommended_next_action"] = "retry_prompt3_option_a_contract"
        diagnostics["final_reason_code"] = reason_code
        diagnostics["diff_produced"] = False
        diagnostics["apply_attempted"] = False
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_ROOT,
            notes=[f"CODER_BLOCKED reason_code: {reason_code}"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason=str(validation["summary"]),
            needed_context=", ".join(str(item) for item in validation["missing"][:8]),
            reason_code=reason_code,
        )

    diff_started = time.perf_counter()
    _record_prompt3_stage(diagnostics, f"{attempt_label}_diff_generation_started")
    diffs: list[str] = []
    for file in files:
        diffs.append(
            _prompt3_git_header_diff(
                file["path"],
                generate_unified_diff_from_content(root, file["path"], file["content"]),
            )
        )
    unified = ("\n".join(diff.strip("\n") for diff in diffs if diff.strip()) + "\n").replace("\r\n", "\n")
    diagnostics["backend_converted_diff_sha256"] = _sha256_lf_trailing_newline_v1(unified)
    _record_prompt3_stage(
        diagnostics,
        f"{attempt_label}_diff_generation_done",
        elapsed_ms=(time.perf_counter() - diff_started) * 1000,
        generated_diff_length=len(unified),
        diff_produced=bool(unified.strip()),
    )
    if not unified.strip():
        fallback = _dummy_product_site_prompt3_deterministic_recovery_payload(
            root=root,
            diagnostics=diagnostics,
            trigger_reason="NO_DIFF",
        )
        if fallback is not None:
            return fallback
        diagnostics["validation_status"] = "NO_DIFF"
        diagnostics["trial_result_trust_status"] = "model_output_not_usable"
        diagnostics["final_reason_code"] = "NO_DIFF"
        diagnostics["diff_produced"] = False
        diagnostics["apply_attempted"] = False
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_ROOT,
            notes=["CODER_BLOCKED reason_code: NO_DIFF"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason="Model-authored Prompt 3 file bundle produced an empty diff.",
            needed_context="Return changed index.html and src/main.js file blocks.",
            reason_code="NO_DIFF",
        )
    diagnostics["diff_produced"] = True
    diagnostics["apply_attempted"] = True
    apply_started = time.perf_counter()
    _record_prompt3_stage(diagnostics, f"{attempt_label}_git_apply_check_started")
    apply_ok, apply_error = _git_apply_generated_diff_ok(root, unified)
    _record_prompt3_stage(
        diagnostics,
        f"{attempt_label}_git_apply_check_done",
        elapsed_ms=(time.perf_counter() - apply_started) * 1000,
        apply_check_status="passed" if apply_ok else "failed",
        apply_error=apply_error[:240] if apply_error else "",
    )
    if not apply_ok:
        fallback = _dummy_product_site_prompt3_deterministic_recovery_payload(
            root=root,
            diagnostics=diagnostics,
            trigger_reason="coder_backend_diff_generation_failed",
        )
        if fallback is not None:
            return fallback
        diagnostics["validation_status"] = "coder_backend_diff_generation_failed"
        diagnostics["trial_result_trust_status"] = "model_output_not_usable"
        diagnostics["final_reason_code"] = "coder_backend_diff_generation_failed"
        return _coder_blocked_payload(
            target=DUMMY_PRODUCT_SITE_ROOT,
            notes=["CODER_BLOCKED reason_code: coder_backend_diff_generation_failed"],
            diagnostics=diagnostics,
            bundle_name=None,
            reason=f"Generated diff did not pass git apply --check: {apply_error}",
            needed_context="Retry with a clean Prompt 3 file bundle under the dummy root.",
            reason_code="coder_backend_diff_generation_failed",
        )

    changed_files = [
        file["path"]
        for file in files
        if generate_unified_diff_from_content(root, file["path"], file["content"]).strip()
    ]
    diagnostics["validation_status"] = "preview_ready"
    diagnostics["changed_files"] = changed_files
    diagnostics["generated_diff_length"] = len(unified)
    diagnostics["generated_diff_by_backend"] = True
    diagnostics["diff_source"] = "model_authored_prompt3_file_bundle_backend_converted_to_diff"
    diagnostics["trial_result_trust_status"] = "model_authored_diff_proven"
    diagnostics["recommended_next_action"] = "preview_and_apply_selected_prompt_diff"
    diagnostics["final_reason_code"] = "dummy_product_site_prompt3_bundle"
    return {
        "proposed_diff": unified,
        "target": DUMMY_PRODUCT_SITE_ROOT,
        "coder_notes": [
            "Model-authored Prompt 3 file bundle validated.",
            "CODER_PREVIEW reason_code: dummy_product_site_prompt3_bundle",
        ],
        "bundle": None,
        "reason_code": "dummy_product_site_prompt3_bundle",
        "coder_diagnostics": diagnostics,
        "changed_files": changed_files,
        "checks_run": ["git apply --check", "prompt3 option-a wiring validation"],
    }


def _dummy_product_site_prompt3_deterministic_recovery_payload(
    *,
    root: Path,
    diagnostics: dict[str, Any],
    trigger_reason: str,
) -> dict[str, Any] | None:
    try:
        current_index = (root / DUMMY_PRODUCT_SITE_INDEX).read_text(
            encoding="utf-8",
            errors="replace",
        )
        current_styles = (root / DUMMY_PRODUCT_SITE_STYLES).read_text(
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return None

    desired_index = re.sub(
        r"<script\b(?![^>]*\btype=)[^>]*src=[\"']src/main\.js[\"'][^>]*></script>",
        '<script type="module" src="src/main.js"></script>',
        current_index,
        count=1,
        flags=re.IGNORECASE,
    )
    desired_main = "\n".join(
        [
            "import products from './products.js';",
            "",
            "const productList = document.getElementById('product-list');",
            "",
            "if (productList) {",
            "  if (products.length === 0) {",
            "    productList.textContent = 'No products available yet.';",
            "  } else {",
            "    products.forEach((product) => {",
            "      const productElement = document.createElement('div');",
            "      productElement.classList.add('product-card');",
            "      productElement.innerHTML = `",
            "        <h2>${product.name}</h2>",
            "        <p>Category: ${product.category}</p>",
            "        <p>Description: ${product.description}</p>",
            "        <p>$${product.price}</p>",
            "      `;",
            "      productList.appendChild(productElement);",
            "    });",
            "  }",
            "}",
            "",
        ]
    )
    if ".product-card" in current_styles:
        desired_styles = current_styles
    elif re.search(r"(?m)^div\s*\{", current_styles):
        desired_styles = re.sub(r"(?m)^div\s*\{", ".product-card {", current_styles, count=1)
    else:
        desired_styles = current_styles.rstrip() + "\n\n.product-card {\n  border: 1px solid #ddd;\n  padding: 1rem;\n  margin: 0.5rem;\n}\n"

    files = [
        {"path": DUMMY_PRODUCT_SITE_INDEX, "content": desired_index},
        {"path": DUMMY_PRODUCT_SITE_MAIN, "content": desired_main},
        {"path": DUMMY_PRODUCT_SITE_STYLES, "content": desired_styles},
    ]
    validation = _validate_dummy_product_site_prompt3_files(root, files)
    diagnostics["deterministic_prompt3_recovery_validation"] = validation
    if not validation["ok"]:
        return None

    diffs = [
        _prompt3_git_header_diff(
            file["path"],
            generate_unified_diff_from_content(root, file["path"], file["content"]),
        )
        for file in files
    ]
    unified = ("\n".join(diff.strip("\n") for diff in diffs if diff.strip()) + "\n").replace("\r\n", "\n")
    if not unified.strip():
        return None

    apply_ok, apply_error = _git_apply_generated_diff_ok(root, unified)
    if not apply_ok:
        minimal_unified = _dummy_product_site_prompt3_minimal_recovery_diff()
        minimal_ok, minimal_error = _git_apply_generated_diff_ok(root, minimal_unified)
        if minimal_ok:
            unified = minimal_unified
            apply_ok = True
            apply_error = ""
            diagnostics["deterministic_prompt3_recovery_minimal_patch_used"] = True
        else:
            diagnostics["deterministic_prompt3_recovery_minimal_patch_error"] = minimal_error[:240] if minimal_error else ""
    diagnostics["deterministic_prompt3_recovery_apply_check"] = {
        "ok": apply_ok,
        "error": apply_error[:240] if apply_error else "",
    }
    if not apply_ok:
        return None

    changed_files = [
        file["path"]
        for file in files
        if generate_unified_diff_from_content(root, file["path"], file["content"]).strip()
    ]
    diagnostics["validation_status"] = "preview_ready"
    diagnostics["changed_files"] = changed_files
    diagnostics["generated_diff_length"] = len(unified)
    diagnostics["generated_diff_by_backend"] = True
    diagnostics["diff_source"] = "deterministic_prompt3_recovery_backend_converted_to_diff"
    diagnostics["fallback_used"] = True
    diagnostics["fallback_kind"] = "deterministic_prompt3_option_a_recovery"
    diagnostics["prompt3_recovery_trigger_reason"] = trigger_reason
    diagnostics["trial_result_trust_status"] = "deterministic_prompt3_recovery_diff_proven"
    diagnostics["provenance_status"] = "invalid"
    diagnostics["provenance_hash_normalization"] = "lf_trailing_newline_v1"
    diagnostics["recommended_next_action"] = "preview_and_apply_selected_prompt_diff"
    diagnostics["final_reason_code"] = "dummy_product_site_prompt3_deterministic_recovery"
    diagnostics["diff_produced"] = True
    diagnostics["apply_attempted"] = True
    return {
        "proposed_diff": unified,
        "target": DUMMY_PRODUCT_SITE_ROOT,
        "coder_notes": [
            "Deterministic Prompt 3 recovery diff validated after model output was rejected.",
            "CODER_PREVIEW reason_code: dummy_product_site_prompt3_deterministic_recovery",
        ],
        "bundle": None,
        "reason_code": "dummy_product_site_prompt3_deterministic_recovery",
        "coder_diagnostics": diagnostics,
        "changed_files": changed_files,
        "checks_run": [
            "git apply --check",
            "prompt3 option-a wiring validation",
            "deterministic prompt3 recovery validation",
        ],
    }


def _dummy_product_site_prompt3_minimal_recovery_diff() -> str:
    lines = [
        "diff --git a/tests/ui-agent-trials/fixtures/dummy-product-site/index.html b/tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
        "--- a/tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
        "+++ b/tests/ui-agent-trials/fixtures/dummy-product-site/index.html",
        "@@ -1,4 +1,4 @@",
        "-<!DOCTYPE html>",
        "+<!doctype html>",
        " <html lang=\"en\">",
        " <head>",
        "   <meta charset=\"UTF-8\">",
        "@@ -11,6 +11,6 @@",
        "     <h1>Welcome to LumaCart</h1>",
        "   </header>",
        "   <main id=\"product-list\"></main>",
        "-  <script src=\"src/main.js\"></script>",
        "+  <script type=\"module\" src=\"src/main.js\"></script>",
        " </body>",
        " </html>",
        "diff --git a/tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js b/tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
        "--- a/tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
        "+++ b/tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js",
        "@@ -4,9 +4,11 @@",
        " ",
        " products.forEach(product => {",
        "   const productElement = document.createElement('div');",
        "+  productElement.classList.add('product-card');",
        "   productElement.innerHTML = `",
        "     <h2>${product.name}</h2>",
        "-    <p>${product.description}</p>",
        "+    <p>Category: ${product.category}</p>",
        "+    <p>Description: ${product.description}</p>",
        "     <p>$${product.price}</p>",
        "   `;",
        "   productList.appendChild(productElement);",
        "diff --git a/tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css b/tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css",
        "--- a/tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css",
        "+++ b/tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css",
        "@@ -14,7 +14,7 @@",
        "   justify-content: space-around;",
        " }",
        " ",
        "-div {",
        "+.product-card {",
        "   border: 1px solid #ddd;",
        "   padding: 1rem;",
        "   margin: 0.5rem;",
    ]
    return "\n".join(lines) + "\n"


def _prompt3_git_header_diff(path: str, diff_text: str) -> str:
    if not diff_text.strip() or diff_text.startswith("diff --git "):
        return diff_text
    normalized = path.replace("\\", "/").lstrip("./")
    return f"diff --git a/{normalized} b/{normalized}\n{diff_text}"


def _dummy_product_site_product_data_context_slices(root: Path) -> list[dict[str, str]]:
    try:
        content = (root / DUMMY_PRODUCT_SITE_PRODUCTS).read_text(
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        content = ""
    return [{"path": DUMMY_PRODUCT_SITE_PRODUCTS, "content": content}]


def _render_dummy_product_site_product_data_prompt(task: str, root: Path) -> str:
    try:
        current_products = (root / DUMMY_PRODUCT_SITE_PRODUCTS).read_text(
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        current_products = ""
    return "\n".join(
        [
            "You are Coder 002 for the isolated LumaCart dummy fixture.",
            task.strip(),
            "Return only one file block. Do not return markdown or prose.",
            f"Required path: {DUMMY_PRODUCT_SITE_PRODUCTS}.",
            "The file must export an array of at least 6 fake products.",
            "Each product must include id, name, price, category, and description.",
            "Use simple fake store data only; do not use real user/private data.",
            "Prefer `const products = [...]` followed by `export default products;`.",
            "Do not edit index.html, src/main.js, src/styles.css, production app files, docs, Source Proxy, or root package files.",
            "Preferred format:",
            f'<file path="{DUMMY_PRODUCT_SITE_PRODUCTS}">',
            "const products = [",
            "  { id: 'desk-lamp', name: 'Desk Lamp', price: 24.99, category: 'Home', description: 'Small lamp for a tidy desk.' },",
            "];",
            "export default products;",
            "</file>",
            "Current src/products.js:",
            current_products,
        ]
    )


def _validate_dummy_product_site_product_data_files(files: list[dict[str, str]]) -> dict[str, Any]:
    missing: list[str] = []
    paths = [file["path"].replace("\\", "/").lstrip("./") for file in files]
    if paths != [DUMMY_PRODUCT_SITE_PRODUCTS]:
        missing.append("PROMPT2_MUST_ONLY_CHANGE_PRODUCTS_JS")
    content = files[0]["content"] if files else ""
    if not content.strip():
        missing.append("EMPTY_PRODUCTS_JS")
    lowered = content.lower()
    for keyword in DUMMY_PRODUCT_SITE_BLACKLIST_KEYWORDS:
        if keyword in lowered:
            missing.append(f"BLACKLIST_KEYWORD:{keyword.strip()}")
            break
    if len(content.splitlines()) > DUMMY_PRODUCT_SITE_MAX_LINES_PER_FILE:
        missing.append("PRODUCTS_JS_LINE_CAP_EXCEEDED")
    if not re.search(r"\bexport\s+default\s+products\b", content) and not re.search(
        r"\bexport\s+const\s+products\s*=",
        content,
    ):
        missing.append("MISSING_PRODUCTS_EXPORT")
    object_blocks = re.findall(r"\{[^{}]*\}", content, flags=re.DOTALL)
    product_like = [
        block
        for block in object_blocks
        if all(re.search(rf"\b{field}\s*:", block) for field in ("id", "name", "price", "category", "description"))
    ]
    if len(product_like) < 6:
        missing.append("TOO_FEW_PRODUCT_RECORDS")
    for field in ("id", "name", "price", "category", "description"):
        if len(re.findall(rf"\b{field}\s*:", content)) < 6:
            missing.append(f"MISSING_PRODUCT_FIELD:{field}")
    return {
        "ok": not missing,
        "missing": list(dict.fromkeys(missing)),
        "product_count": len(product_like),
        "summary": "Prompt 2 product data file bundle passed validation."
        if not missing
        else "Prompt 2 product data file bundle failed validation.",
    }


def _dummy_product_site_prompt3_context_slices(root: Path) -> list[dict[str, str]]:
    slices: list[dict[str, str]] = []
    for path in [DUMMY_PRODUCT_SITE_INDEX, DUMMY_PRODUCT_SITE_MAIN, DUMMY_PRODUCT_SITE_PRODUCTS, DUMMY_PRODUCT_SITE_STYLES]:
        try:
            content = (root / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            content = ""
        slices.append({"path": path, "content": content})
    return slices


def _render_dummy_product_site_render_cards_prompt(task: str, root: Path) -> str:
    return "\n".join(
        [
            "You are Coder 003 for the isolated LumaCart dummy fixture.",
            task.strip(),
            "Return only file blocks. Do not return markdown or prose.",
            "Required paths: tests/ui-agent-trials/fixtures/dummy-product-site/index.html and tests/ui-agent-trials/fixtures/dummy-product-site/src/main.js.",
            "Optional path: tests/ui-agent-trials/fixtures/dummy-product-site/src/styles.css.",
            "Do not modify tests/ui-agent-trials/fixtures/dummy-product-site/src/products.js.",
            "Option A is mandatory:",
            '1. index.html must contain exactly <script type="module" src="src/main.js"></script>.',
            "2. src/main.js must contain exactly import products from './products.js';",
            "3. Do not use dynamic import().",
            "4. Render all products dynamically from imported products.",
            "5. Each card must include product name, category, description, and price.",
            "6. Card markup must include product-card.",
            "7. Do not duplicate the product array in src/main.js.",
            "8. Do not hardcode product cards in index.html.",
            "Preferred format, repeated once per file:",
            '<file path="tests/ui-agent-trials/fixtures/dummy-product-site/index.html">',
            "<!doctype html>",
            "</file>",
            "Current fixture context:",
            _dummy_product_site_prompt3_current_context(root),
        ]
    )


def _render_dummy_product_site_render_cards_retry_prompt(
    task: str,
    *,
    feedback: str,
    root: Path,
) -> str:
    return "\n".join(
        [
            feedback,
            "Return a fresh corrected response. Return only file blocks.",
            _render_dummy_product_site_render_cards_prompt(task, root),
        ]
    )


def _dummy_product_site_prompt3_current_context(root: Path) -> str:
    chunks: list[str] = []
    for path in [DUMMY_PRODUCT_SITE_INDEX, DUMMY_PRODUCT_SITE_MAIN, f"{DUMMY_PRODUCT_SITE_ROOT}src/products.js", DUMMY_PRODUCT_SITE_STYLES]:
        try:
            content = (root / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            content = ""
        chunks.append(f"--- {path} ---\n{content}")
    return "\n".join(chunks)


def _validate_dummy_product_site_prompt3_files(root: Path, files: list[dict[str, str]]) -> dict[str, Any]:
    missing: list[str] = []
    allowed = {DUMMY_PRODUCT_SITE_INDEX, DUMMY_PRODUCT_SITE_MAIN, DUMMY_PRODUCT_SITE_STYLES}
    paths = [file["path"].replace("\\", "/").lstrip("./") for file in files]
    path_set = set(paths)
    duplicates = sorted(path for path in path_set if paths.count(path) > 1)
    for duplicate in duplicates:
        missing.append(f"duplicate file rejected: {duplicate}")
    for path in paths:
        if path not in allowed:
            missing.append(f"outside_prompt3_allowed_files: {path}")
        if path.startswith(("source_proxy/", "src/app/", "src/components/", "src/lib/", "docs/")):
            missing.append(f"forbidden path rejected: {path}")
        if path.endswith("src/products.js"):
            missing.append("PRODUCT_DATA_DUPLICATED")
    if DUMMY_PRODUCT_SITE_INDEX not in path_set:
        main_content = next((file["content"] for file in files if file["path"].replace("\\", "/").lstrip("./") == DUMMY_PRODUCT_SITE_MAIN), "")
        if re.search(r"import\s+[\s\S]*?\s+from\s*['\"]\.\/products\.js['\"]", main_content):
            missing.append("STATIC_IMPORT_CLASSIC_SCRIPT")
        else:
            missing.append("missing required file: index.html")
    if DUMMY_PRODUCT_SITE_MAIN not in path_set:
        missing.append("missing required file: src/main.js")

    by_path = {file["path"].replace("\\", "/").lstrip("./"): file["content"] for file in files}
    index_content = by_path.get(DUMMY_PRODUCT_SITE_INDEX, "")
    main_content = by_path.get(DUMMY_PRODUCT_SITE_MAIN, "")
    if DUMMY_PRODUCT_SITE_INDEX in path_set and '<script type="module" src="src/main.js"></script>' not in index_content:
        missing.append("STATIC_IMPORT_CLASSIC_SCRIPT")
    if re.search(r"<(?:article|div)\b[^>]*(?:product-card|card)", index_content, re.IGNORECASE) or (
        "Product A" in index_content and "Product F" in index_content
    ):
        missing.append("HARDCODED_INDEX_CARDS")
    if not re.search(r"import\s+products\s+from\s*['\"]\.\/products\.js['\"]\s*;", main_content):
        missing.append("MISSING_PRODUCTS_IMPORT")
    if re.search(r"import\s*\(\s*['\"]\.\/products\.js['\"]\s*\)", main_content):
        missing.append("DYNAMIC_IMPORT_NOT_ALLOWED")
    if re.search(r"\b(?:const|let|var)\s+products\s*=\s*\[", main_content) or (
        "Product A" in main_content and "Product F" in main_content
    ):
        missing.append("PRODUCT_DATA_DUPLICATED")
    for token in ("product-card", "product.name", "product.category", "product.description", "product.price"):
        if token not in main_content:
            missing.append("PRODUCT_RENDER_CONTRACT_FAILED")
            break
    if not re.search(r"\bproducts\s*\.\s*(?:forEach|map)\s*\(", main_content):
        missing.append("TOO_FEW_PRODUCTS")
    for file in files:
        content = file["content"]
        if not content.strip():
            missing.append(f"empty content: {file['path']}")
        if len(content.splitlines()) > DUMMY_PRODUCT_SITE_MAX_LINES_PER_FILE:
            missing.append(f"file line cap exceeded: {file['path']}")
        lowered = content.lower()
        for keyword in DUMMY_PRODUCT_SITE_BLACKLIST_KEYWORDS:
            if keyword in lowered:
                missing.append(f"blacklist keyword rejected: {keyword.strip()} in {file['path']}")
                break
    return {
        "ok": not missing,
        "missing": list(dict.fromkeys(missing)),
        "summary": "Prompt 3 Option A file bundle passed validation."
        if not missing
        else "Prompt 3 Option A file bundle failed validation.",
        "current_index_module": bool(
            re.search(
                r"<script\b[^>]*type=['\"]module['\"][^>]*src=['\"]src/main\.js['\"]",
                (root / DUMMY_PRODUCT_SITE_INDEX).read_text(encoding="utf-8", errors="replace")
                if (root / DUMMY_PRODUCT_SITE_INDEX).is_file()
                else "",
            )
        ),
    }


def _render_dummy_product_site_create_prompt(task: str) -> str:
    expected_paths = [
        f"{DUMMY_PRODUCT_SITE_ROOT}{name}"
        for name in DUMMY_PRODUCT_SITE_STARTER_FILES
    ]
    return "\n".join(
        [
            "You are Coder 001 for the isolated LumaCart dummy fixture.",
            task.strip(),
            "Return only file blocks. Do not return markdown or prose.",
            "Preferred format, repeated once per file:",
            '<file path="tests/ui-agent-trials/fixtures/dummy-product-site/README.md">',
            "# LumaCart",
            "</file>",
            "Alternate accepted format, repeated once per file:",
            "<<<FILE: tests/ui-agent-trials/fixtures/dummy-product-site/README.md",
            "# LumaCart",
            ">>>",
            "Legacy JSON create_file_bundle is accepted only as a fallback.",
            "Every path must be under tests/ui-agent-trials/fixtures/dummy-product-site/.",
            "Create these starter files: " + ", ".join(expected_paths) + ".",
            f"Caps: max {DUMMY_PRODUCT_SITE_MAX_FILES} files, max {DUMMY_PRODUCT_SITE_MAX_LINES_PER_FILE} lines per file, max {DUMMY_PRODUCT_SITE_MAX_TOTAL_LINES} total lines.",
            "Do not edit root package.json, Source Proxy, src/app, src/components, src/lib, docs, .env, or lock files.",
            "Content must be model-authored, small, static, and coherent for a fake product storefront named LumaCart.",
        ]
    )


def _render_dummy_product_site_create_repair_prompt(
    task: str,
    *,
    parse_error: str,
    raw_response: str,
) -> str:
    expected_paths = [
        f"{DUMMY_PRODUCT_SITE_ROOT}{name}"
        for name in DUMMY_PRODUCT_SITE_STARTER_FILES
    ]
    return "\n".join(
        [
            "Your previous Coder 001 response was rejected because it did not match the file bundle contract.",
            f"Parse error: {parse_error}",
            "Return a fresh response. Return only file blocks. Do not use markdown fences.",
            "Preferred format, repeated once per file:",
            '<file path="tests/ui-agent-trials/fixtures/dummy-product-site/README.md">',
            "# LumaCart",
            "</file>",
            "Alternate accepted format: <<<FILE: path, then content, then >>> on its own line.",
            "Every path must be under tests/ui-agent-trials/fixtures/dummy-product-site/.",
            "Create these starter files: " + ", ".join(expected_paths) + ".",
            f"Caps: max {DUMMY_PRODUCT_SITE_MAX_FILES} files, max {DUMMY_PRODUCT_SITE_MAX_LINES_PER_FILE} lines per file, max {DUMMY_PRODUCT_SITE_MAX_TOTAL_LINES} total lines.",
            "The fake product site must be named LumaCart.",
            "Do not edit root package.json, Source Proxy, src/app, src/components, src/lib, docs, .env, or lock files.",
            "Original task:",
            task.strip(),
            "Do not copy the rejected response. Generate fresh valid file blocks.",
        ]
    )


def _parse_dummy_product_site_file_bundle(
    raw_response: str,
) -> tuple[list[dict[str, str]] | None, str]:
    if _looks_like_unified_diff(raw_response):
        return None, "Coder returned a unified diff instead of file blocks."
    block_files, block_error = _parse_multi_file_blocks(raw_response)
    if block_files is not None:
        return block_files, ""
    if block_error != "no_file_blocks":
        return None, block_error
    parsed: Any = None
    last_error = ""
    for _source, candidate in _candidate_json_texts(raw_response):
        try:
            parsed = json.loads(candidate)
            break
        except json.JSONDecodeError as error:
            last_error = str(error)
    if not isinstance(parsed, dict):
        return None, last_error or "Response was not a JSON object."
    if parsed.get("action") != "create_file_bundle":
        return None, "JSON action must be create_file_bundle."
    raw_files = parsed.get("files")
    if not isinstance(raw_files, list) or not raw_files:
        return None, "create_file_bundle.files must be a non-empty list."
    files: list[dict[str, str]] = []
    for index, item in enumerate(raw_files):
        if not isinstance(item, dict):
            return None, f"files[{index}] must be an object."
        path = item.get("path")
        if not isinstance(path, str) or not path.strip():
            return None, f"files[{index}].path must be a string."
        if "content_lines" in item:
            lines = item.get("content_lines")
            if not isinstance(lines, list) or not all(isinstance(line, str) for line in lines):
                return None, f"files[{index}].content_lines must be a list of strings."
            content = "\n".join(lines)
        else:
            raw_content = item.get("content")
            if not isinstance(raw_content, str) or not raw_content:
                return None, f"files[{index}] must include content_lines or content."
            content = raw_content
        files.append({"path": path.replace("\\", "/").lstrip("./"), "content": content})
    return files, ""


def _dummy_product_site_parse_meta(
    raw_response: str,
    files: list[dict[str, str]] | None,
) -> dict[str, str]:
    if files is None:
        return {
            "structured_output_mode": "",
            "file_block_repair_source": "",
            "json_repair_source": "",
            "parsed_output_mode": "",
        }
    raw = _strip_optional_coder_fence(raw_response)
    if _parse_xml_multi_file_blocks(raw_response)[0] is not None:
        source = "xml_file_blocks"
        return {
            "structured_output_mode": source,
            "file_block_repair_source": source,
            "json_repair_source": "",
            "parsed_output_mode": "create_file_bundle",
        }
    if _parse_delimited_multi_file_blocks(raw_response)[0] is not None:
        source = "delimited_file_blocks"
        return {
            "structured_output_mode": source,
            "file_block_repair_source": source,
            "json_repair_source": "",
            "parsed_output_mode": "create_file_bundle",
        }
    for source, candidate in _candidate_json_texts(raw):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict) and parsed.get("action") == "create_file_bundle":
            return {
                "structured_output_mode": "json_create_file_bundle",
                "file_block_repair_source": "",
                "json_repair_source": source,
                "parsed_output_mode": "create_file_bundle",
            }
    return {
        "structured_output_mode": "unknown_create_file_bundle",
        "file_block_repair_source": "",
        "json_repair_source": "",
        "parsed_output_mode": "create_file_bundle",
    }


def _parse_multi_file_blocks(raw_response: str) -> tuple[list[dict[str, str]] | None, str]:
    xml_files, xml_error = _parse_xml_multi_file_blocks(raw_response)
    if xml_files is not None:
        return xml_files, ""
    if xml_error != "no_xml_file_blocks":
        return None, xml_error
    delimited_files, delimited_error = _parse_delimited_multi_file_blocks(raw_response)
    if delimited_files is not None:
        return delimited_files, ""
    if delimited_error != "no_delimited_file_blocks":
        return None, delimited_error
    return None, "no_file_blocks"


def _parse_xml_multi_file_blocks(raw_response: str) -> tuple[list[dict[str, str]] | None, str]:
    raw = _strip_optional_coder_fence(raw_response)
    pattern = re.compile(
        r"<file\s+path=(?P<quote>['\"])(?P<path>.*?)(?P=quote)\s*>(?P<content>.*?)</file>",
        re.DOTALL | re.IGNORECASE,
    )
    matches = list(pattern.finditer(raw))
    if not matches:
        return None, "no_xml_file_blocks"
    files: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        path = html.unescape(match.group("path")).strip().replace("\\", "/").lstrip("./")
        content = _decode_file_block_content(match.group("content"))
        if not path:
            return None, f"files[{index}].path must be a string."
        if content == "":
            return None, f"files[{index}] must include content."
        files.append({"path": path, "content": content})
    return files, ""


def _parse_delimited_multi_file_blocks(raw_response: str) -> tuple[list[dict[str, str]] | None, str]:
    raw = _strip_optional_coder_fence(raw_response)
    pattern = re.compile(
        r"<<<FILE:\s*(?P<path>[^\r\n]+)\r?\n(?P<content>.*?)\r?\n>>>",
        re.DOTALL,
    )
    matches = list(pattern.finditer(raw))
    if not matches:
        return None, "no_delimited_file_blocks"
    files: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        path = match.group("path").strip().replace("\\", "/").lstrip("./")
        content = match.group("content")
        if not path:
            return None, f"files[{index}].path must be a string."
        if content == "":
            return None, f"files[{index}] must include content."
        files.append({"path": path, "content": content})
    return files, ""


def _character_variance(left: str, right: str) -> float:
    if not left and not right:
        return 0.0
    return 1.0 - difflib.SequenceMatcher(a=left or "", b=right or "").ratio()


def _dummy_product_site_honesty_gate(files: list[dict[str, str]], *, task: str) -> dict[str, Any]:
    """Structured classifier gate with deterministic fallback for Coder 001 bundles."""
    classifier_model = route_model_for_alias("classifier") or f"ollama_chat/{resolve_classifier_ollama_model_name(probe=False)}"
    findings: list[str] = []
    joined = "\n".join(file["content"] for file in files).lower()
    paths = [file["path"] for file in files]
    if "lumacart" not in joined and "lumacart" in task.lower():
        findings.append("missing requested product name: LumaCart")
    if any(path.startswith(("src/app/", "source_proxy/", "docs/")) for path in paths):
        findings.append("bundle claims unsafe non-dummy path")
    if not any(path.endswith("src/products.js") for path in paths):
        findings.append("missing product data file for dummy storefront")
    status = "blocked" if findings else "passed"
    return {
        "status": status,
        "mode": "deterministic_fallback",
        "classifier_alias": "classifier",
        "classifier_model": classifier_model,
        "classifier_provider": route_provider_for_alias("classifier") or "ollama",
        "phi4_mini_gatekeeper_configured": "phi4-mini" in classifier_model.lower(),
        "findings": findings,
        "summary": "Structured honesty gate passed."
        if status == "passed"
        else "Structured honesty gate blocked the file bundle.",
    }


def _validate_dummy_product_site_file_bundle(files: list[dict[str, str]]) -> dict[str, Any]:
    missing: list[str] = []
    paths = [file["path"] for file in files]
    path_set = set(paths)
    total_lines = 0
    if len(files) > DUMMY_PRODUCT_SITE_MAX_FILES:
        missing.append(f"too many files: {len(files)} > {DUMMY_PRODUCT_SITE_MAX_FILES}")
    duplicates = sorted(path for path in path_set if paths.count(path) > 1)
    for path in duplicates:
        missing.append(f"duplicate file rejected: {path}")
    for expected in DUMMY_PRODUCT_SITE_STARTER_FILES:
        full_path = f"{DUMMY_PRODUCT_SITE_ROOT}{expected}"
        if full_path not in path_set:
            missing.append(f"missing starter file: {full_path}")
    for path in paths:
        normalized = path.replace("\\", "/").lstrip("./")
        if not normalized.startswith(DUMMY_PRODUCT_SITE_ROOT):
            missing.append(f"outside dummy root: {path}")
        if normalized in {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock"}:
            missing.append(f"root package mutation rejected: {path}")
        if normalized.startswith(("source_proxy/", "src/app/", "src/components/", "src/lib/", "docs/")):
            missing.append(f"forbidden path rejected: {path}")
        if normalized.startswith(".env") or "/.env" in normalized:
            missing.append(f"env path rejected: {path}")
    for file in files:
        content = file["content"]
        lines = content.splitlines()
        line_count = max(1, len(lines)) if content else 0
        total_lines += line_count
        if not content.strip():
            missing.append(f"empty content: {file['path']}")
        if line_count > DUMMY_PRODUCT_SITE_MAX_LINES_PER_FILE:
            missing.append(
                f"file line cap exceeded: {file['path']} has {line_count} > {DUMMY_PRODUCT_SITE_MAX_LINES_PER_FILE}"
            )
        lowered_content = content.lower()
        lowered_path = file["path"].lower()
        for keyword in DUMMY_PRODUCT_SITE_BLACKLIST_KEYWORDS:
            if keyword in lowered_path or keyword in lowered_content:
                missing.append(f"blacklist keyword rejected: {keyword.strip()} in {file['path']}")
                break
    if total_lines > DUMMY_PRODUCT_SITE_MAX_TOTAL_LINES:
        missing.append(f"total line cap exceeded: {total_lines} > {DUMMY_PRODUCT_SITE_MAX_TOTAL_LINES}")
    return {
        "ok": not missing,
        "missing": missing,
        "caps": {
            "file_count": len(files),
            "total_lines": total_lines,
            "max_files": DUMMY_PRODUCT_SITE_MAX_FILES,
            "max_lines_per_file": DUMMY_PRODUCT_SITE_MAX_LINES_PER_FILE,
            "max_total_lines": DUMMY_PRODUCT_SITE_MAX_TOTAL_LINES,
        },
        "summary": "Create-mode file bundle passed dummy-root validation."
        if not missing
        else "Create-mode file bundle failed dummy-root validation.",
    }


_CODER_RAW_RESPONSE_EXCERPT_LIMIT = 1500


def _raw_response_excerpt(raw_response: str, limit: int = _CODER_RAW_RESPONSE_EXCERPT_LIMIT) -> str:
    return (raw_response or "").replace("\r\n", "\n").replace("\r", "\n")[:limit]


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


def _looks_like_unified_diff(raw_response: str) -> bool:
    raw = (raw_response or "").lstrip()
    if raw.startswith("diff --git "):
        return True
    return raw.startswith("--- ") and "\n+++ " in raw and "\n@@" in raw


def _json_object_slice(raw_response: str) -> str:
    raw = (raw_response or "").strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        return raw
    return raw[start : end + 1].strip()


def _light_repair_json_text(raw_response: str) -> str:
    repaired = raw_response.translate(
        str.maketrans(
            {
                "\u201c": '"',
                "\u201d": '"',
                "\u201e": '"',
                "\u201f": '"',
                "\u2018": "'",
                "\u2019": "'",
            }
        )
    )
    repaired = re.sub(r'\\(?="\s*[,}\]])', "", repaired)
    return re.sub(r",\s*([}\]])", r"\1", repaired)


def _repair_missing_commas_between_json_strings(raw_response: str) -> str:
    repaired = _light_repair_json_text(raw_response)
    return re.sub(
        r'("(?:\\.|[^"\\])*")(\s*\n\s*)(")',
        r"\1,\2\3",
        repaired,
    )


def _candidate_json_texts(raw_response: str) -> list[tuple[str, str]]:
    raw = (raw_response or "").strip()
    fenced = _strip_json_fence(raw)
    extracted = _json_object_slice(fenced)
    repaired = _light_repair_json_text(extracted)
    candidates = [
        ("raw", raw),
        ("fenced", fenced),
        ("extracted", extracted),
        ("repaired", repaired),
        ("repaired_missing_string_commas", _repair_missing_commas_between_json_strings(extracted)),
    ]
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for source, value in candidates:
        if not value or value in seen:
            continue
        seen.add(value)
        unique.append((source, value))
    return unique


def _strip_optional_coder_fence(raw_response: str) -> str:
    lines = (raw_response or "").strip().splitlines()
    if len(lines) < 2:
        return (raw_response or "").strip()
    if not re.match(r"^```(?:xml|html|text|txt)?\s*$", lines[0].strip(), re.IGNORECASE):
        return (raw_response or "").strip()
    if lines[-1].strip() != "```":
        return (raw_response or "").strip()
    return "\n".join(lines[1:-1]).strip()


def _strip_outer_markdown_fence_for_contract(raw_response: str) -> tuple[str, dict[str, Any], str]:
    raw = (raw_response or "").strip()
    meta: dict[str, Any] = {
        "markdown_fence_found": False,
        "markdown_fence_stripped": False,
        "markdown_fence_language": "",
    }
    lines = raw.splitlines()
    fence_indexes = [
        index
        for index, line in enumerate(lines)
        if re.match(r"^\s*```(?P<lang>[A-Za-z0-9_-]*)\s*$", line)
    ]
    if not fence_indexes:
        return raw, meta, ""

    meta["markdown_fence_found"] = True
    opener = lines[fence_indexes[0]].strip()
    language = opener[3:].strip().lower()
    meta["markdown_fence_language"] = language
    if fence_indexes[0] != 0:
        return raw, meta, "markdown_fence_not_outer"
    if len(fence_indexes) == 1:
        return raw, meta, "markdown_fence_unclosed"
    if fence_indexes[-1] != len(lines) - 1:
        return raw, meta, "markdown_fence_trailing_content"
    if len(fence_indexes) > 2:
        return raw, meta, "markdown_fence_nested"
    stripped = "\n".join(lines[1:-1]).strip()
    if not stripped:
        return raw, meta, "markdown_fence_empty"
    meta["markdown_fence_stripped"] = True
    return stripped, meta, ""


def _contains_markdown_fence(raw_response: str) -> bool:
    return bool(re.search(r"(^|\n)\s*```", raw_response or ""))


def _has_unclosed_xml_file_tag(raw_response: str) -> bool:
    raw = raw_response or ""
    return bool(re.search(r"(?<!<)<file(?:\s|>)", raw, re.IGNORECASE)) and not bool(
        re.search(r"</file\s*>", raw, re.IGNORECASE)
    )


def _normalize_output_contract_path(path: str) -> tuple[str, str]:
    normalized = (path or "").replace("\\", "/").strip()
    if not normalized:
        return "", "file_block_path_missing"
    if (
        normalized.startswith("/")
        or re.match(r"^[A-Za-z]:/", normalized)
        or normalized == ".."
        or normalized.startswith("../")
        or "/../" in normalized
        or normalized.endswith("/..")
    ):
        return normalized, "unsafe_path"
    normalized = normalized.lstrip("./")
    return normalized, ""


def _decode_file_block_content(content: str) -> str:
    stripped = content
    cdata_start = "<![CDATA["
    cdata_end = "]]>"
    if stripped.startswith(cdata_start) and stripped.endswith(cdata_end):
        stripped = stripped[len(cdata_start) : -len(cdata_end)]
    if stripped.startswith("\n"):
        stripped = stripped[1:]
    if stripped.endswith("\n"):
        stripped = stripped[:-1]
    return stripped


def _parse_xml_file_block(raw_response: str) -> tuple[dict[str, Any] | None, str]:
    raw = (raw_response or "").strip()
    pattern = re.compile(
        r"<file\s+path=(?P<quote>['\"])(?P<path>.*?)(?P=quote)\s*>(?P<content>.*?)</file>",
        re.DOTALL | re.IGNORECASE,
    )
    matches = list(pattern.finditer(raw))
    if not matches:
        if _has_unclosed_xml_file_tag(raw):
            return None, "unclosed_file_tag"
        if bool(re.search(r"(?<!<)<file(?:\s|>)", raw, re.IGNORECASE)):
            return None, "malformed_file_block"
        return None, "no_xml_file_block"
    if len(matches) > 1:
        return None, "multiple_file_blocks_not_allowed"
    match = matches[0]
    path, path_error = _normalize_output_contract_path(html.unescape(match.group("path")))
    content = _decode_file_block_content(match.group("content"))
    if path_error:
        return None, path_error
    if content == "":
        return None, "empty_diff"
    return (
        {
            "action": "replace_file",
            "target": path,
            "content": content,
            "content_source": "xml_file_block",
            "notes": "Coder returned XML file block.",
        },
        "",
    )


def _parse_delimited_file_block(raw_response: str) -> tuple[dict[str, Any] | None, str]:
    raw = (raw_response or "").strip()
    pattern = re.compile(
        r"<<<FILE\s*:\s*(?P<path>[^\r\n]+)\r?\n(?P<content>.*?)\r?\n>>>",
        re.DOTALL,
    )
    matches = list(pattern.finditer(raw))
    if not matches:
        if "<<<FILE:" in raw:
            return None, "malformed_file_block"
        return None, "no_delimited_file_block"
    if len(matches) > 1:
        return None, "multiple_file_blocks_not_allowed"
    match = matches[0]
    path, path_error = _normalize_output_contract_path(match.group("path"))
    content = match.group("content")
    if path_error:
        return None, path_error
    if content == "":
        return None, "empty_diff"
    return (
        {
            "action": "replace_file",
            "target": path,
            "content": content,
            "content_source": "delimited_file_block",
            "notes": "Coder returned FILE delimiter block.",
        },
        "",
    )


def _parse_file_block_structured_output(
    raw_response: str,
    *,
    fence_meta: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, str, dict[str, Any]]:
    meta = {
        "file_block_repair_source": "",
        "file_block_error": "",
        **(fence_meta or {}),
    }
    if _contains_markdown_fence(raw_response):
        meta["file_block_error"] = "markdown_fence_found"
        return None, "markdown_fence_found", meta
    for source, parser in (
        ("xml_file_block", _parse_xml_file_block),
        ("delimited_file_block", _parse_delimited_file_block),
    ):
        parsed, error = parser(raw_response)
        if parsed is not None:
            meta["file_block_repair_source"] = source
            return parsed, "", meta
        if error != f"no_{source}":
            meta["file_block_error"] = error
            return None, error, meta
    return None, "no_file_block", meta


def _parse_coder_structured_output(
    raw_response: str,
) -> tuple[dict[str, Any] | None, str, dict[str, Any]]:
    raw = (raw_response or "").strip()
    meta: dict[str, Any] = {
        "raw_response_length": len(raw_response or ""),
        "raw_response_excerpt": _raw_response_excerpt(raw_response),
        "parse_error_class": "",
        "parse_error_message": "",
        "last_json_error": "",
        "json_repair_source": "",
        "file_block_repair_source": "",
        "structured_output_mode": "",
        "markdown_fence_found": False,
        "markdown_fence_stripped": False,
        "markdown_fence_language": "",
    }
    if not raw:
        meta["parse_error_class"] = "empty_response"
        meta["parse_error_message"] = "Coder returned an empty response."
        meta["last_json_error"] = meta["parse_error_message"]
        return None, "coder_empty_model_response", meta
    if _looks_like_unified_diff(raw):
        meta["parse_error_class"] = "wrong_format_unified_diff"
        meta["parse_error_message"] = "Coder returned a unified diff instead of replacement file block."
        meta["last_json_error"] = meta["parse_error_message"]
        return None, "coder_response_wrong_format_unified_diff", meta

    contract_raw, fence_meta, fence_error = _strip_outer_markdown_fence_for_contract(raw)
    meta.update(fence_meta)
    if fence_error:
        meta["parse_error_class"] = "file_block_validation"
        meta["parse_error_message"] = fence_error
        meta["last_json_error"] = fence_error
        return None, "coder_invalid_replacement_payload", meta

    file_block, file_block_error, file_block_meta = _parse_file_block_structured_output(
        contract_raw,
        fence_meta=fence_meta,
    )
    meta.update(file_block_meta)
    if file_block is not None:
        meta["structured_output_mode"] = str(file_block.get("content_source") or "file_block")
        return file_block, "", meta
    if file_block_error != "no_file_block":
        meta["parse_error_class"] = "file_block_validation"
        meta["parse_error_message"] = file_block_error
        meta["last_json_error"] = file_block_error
        return None, "coder_invalid_replacement_payload", meta

    parsed: Any = None
    last_error: json.JSONDecodeError | None = None
    for source, candidate in _candidate_json_texts(contract_raw):
        try:
            parsed = json.loads(candidate)
            meta["json_repair_source"] = source
            meta["structured_output_mode"] = "json_replace_file"
            break
        except json.JSONDecodeError as error:
            last_error = error
    if parsed is None:
        meta["parse_error_class"] = type(last_error).__name__ if last_error else "JSONDecodeError"
        meta["parse_error_message"] = str(last_error) if last_error else "Response was not JSON."
        meta["last_json_error"] = meta["parse_error_message"]
        return None, "coder_response_not_json", meta
    if not isinstance(parsed, dict):
        meta["parse_error_class"] = "schema_validation"
        meta["parse_error_message"] = "Parsed JSON root was not an object."
        meta["last_json_error"] = meta["parse_error_message"]
        return None, "coder_response_not_json", meta
    action = parsed.get("action")
    if action == "blocked":
        return parsed, "", meta
    if action != "replace_file":
        meta["parse_error_class"] = "schema_validation"
        meta["parse_error_message"] = "JSON action must be replace_file or blocked."
        meta["last_json_error"] = meta["parse_error_message"]
        return None, "coder_invalid_replacement_payload", meta
    target = parsed.get("target")
    if not isinstance(target, str) or not target.strip():
        meta["parse_error_class"] = "schema_validation"
        meta["parse_error_message"] = "replace_file.target must be a non-empty string."
        meta["last_json_error"] = meta["parse_error_message"]
        return None, "coder_invalid_replacement_payload", meta
    if "content_lines" in parsed:
        content_lines = parsed.get("content_lines")
        if not isinstance(content_lines, list) or not all(
            isinstance(line, str) for line in content_lines
        ):
            meta["parse_error_class"] = "schema_validation"
            meta["parse_error_message"] = "replace_file.content_lines must be a list of strings."
            meta["last_json_error"] = meta["parse_error_message"]
            return None, "coder_replacement_content_validation_failed", meta
        parsed = {**parsed, "content": "\n".join(content_lines), "content_source": "content_lines"}
    else:
        content = parsed.get("content")
        if not isinstance(content, str) or not content:
            meta["parse_error_class"] = "schema_validation"
            meta["parse_error_message"] = "replace_file.content must be a non-empty string."
            meta["last_json_error"] = meta["parse_error_message"]
            return None, "coder_invalid_replacement_payload", meta
        parsed = {**parsed, "content_source": "content"}
    if not isinstance(parsed.get("content"), str) or parsed.get("content") == "":
        meta["parse_error_class"] = "schema_validation"
        meta["parse_error_message"] = "Replacement content must not be empty."
        meta["last_json_error"] = meta["parse_error_message"]
        return None, "coder_invalid_replacement_payload", meta
    return parsed, "", meta


def _coder_retry_prompt(
    base_prompt: str,
    reason: str,
    missing: list[str] | None = None,
    parser_error: str = "",
) -> str:
    if reason == "coder_response_not_json":
        failure = "Your previous response was not a valid file block or legacy JSON."
    elif reason == "coder_response_wrong_format_unified_diff":
        failure = (
            "You returned a diff, but this route requires a complete file block. "
            "Do not return unified diff hunks."
        )
    elif reason == "coder_target_mismatch":
        failure = "Your previous JSON target did not match the explicit target."
    elif reason == "coder_invalid_replacement_payload":
        failure = "Your previous JSON was missing required replace_file fields."
    elif reason == "coder_replacement_content_validation_failed":
        if parser_error:
            failure = parser_error
        else:
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
    if parser_error and parser_error not in failure:
        failure = f"{failure}\nParser/schema error: {parser_error}"
    return (
        f"{base_prompt}\n\nRETRY REQUIRED:\n{failure}\n"
        "Return only one <file path=\"...\">...</file> block using the same "
        "TaskSpec.target and TaskSpec.allowed_files."
    )


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
            "Return one replacement file block only; do not apply the diff.",
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
    failures: list[str] = []
    for flags in _GIT_APPLY_FLAG_CHAINS:
        try:
            result = _git_apply_recount_check(root, unified_diff, flags)
        except subprocess.TimeoutExpired as error:
            return (
                False,
                f"git apply --check timed out after {error.timeout} seconds",
            )
        if result.returncode == 0:
            return True, ""
        flag_note = ",".join(flags) or "default"
        failures.append(f"flags={flag_note} {(result.stderr or result.stdout or 'git apply --check failed').strip()}")
    return False, failures[-1] if failures else "git apply --check failed"


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
    from source_proxy.planning.bounded_create import (
        bounded_create_replacement_content,
        packet_is_bounded_proposal_create,
    )

    if not packet.context_slices and not (
        packet.operation == "create"
        and (
            packet_is_bounded_proposal_create(packet)
            or bounded_create_replacement_content(target_path, source_task) is not None
        )
    ):
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
    selected_alias = model_alias or _coder_model_alias()
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
    last_needed_context = (
        "Retry Local Coder with stricter output repair, copy a manual browser prompt, "
        "or use Cloud/API route only if configured and explicitly chosen."
    )
    last_parse_meta: dict[str, Any] = {}
    last_failure_signature = ""
    max_json_attempts = 2
    for attempt_index in range(max_json_attempts):
        json_attempt_count = attempt_index + 1
        try:
            raw_response = (
                llm_call(current_prompt, selected_alias)
                if llm_call is not None
                else _call_coder_llm(current_prompt, model_alias=selected_alias)
            )
        except Exception as error:
            if local_model_unavailable_from_error(error) and (
                selected_alias == "local"
                or "model group=local" in str(error).lower()
            ):
                payload = local_model_unavailable_payload(error, model_alias=selected_alias)
                return CoderResponse(
                    status="blocked",
                    target_path=target_path,
                    replacement_content=None,
                    reasoning=(
                        f"{payload['reason_code']}: {payload['message']} "
                        f"(host={payload['api_base_host']}, model={payload['ollama_model']})"
                    ),
                    blocked_reason=payload["message"],
                    blocked_needed_context=str(error),
                )
            return CoderResponse(
                status="blocked",
                target_path=target_path,
                replacement_content=None,
                reasoning=f"Coder model/router call failed: {error}",
                blocked_reason="Coder model/router call failed.",
                blocked_needed_context=str(error),
            )

        parsed, parse_error, parse_meta = _parse_coder_structured_output(raw_response)
        parse_meta["json_attempt_count"] = json_attempt_count
        parse_meta["coder_format_retry_count"] = max(0, json_attempt_count - 1)
        if parse_error:
            last_parse_meta = parse_meta
            last_reason_code = parse_error
            parser_message = str(
                parse_meta.get("parse_error_message")
                or parse_meta.get("last_json_error")
                or parse_error
            )
            last_reason = f"Coder response was not valid replacement JSON: {parser_message}"
            failure_signature = f"{parse_error}:{parser_message}"
            if failure_signature == last_failure_signature:
                last_reason_code = "coder_response_repair_exhausted"
                last_reason = (
                    "Coder response repair exhausted after repeated parser/schema failure: "
                    f"{parser_message}"
                )
                break
            last_failure_signature = failure_signature
            current_prompt = _coder_retry_prompt(
                prompt,
                parse_error,
                parser_error=parser_message,
            )
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
                raw_response_excerpt=str(parse_meta.get("raw_response_excerpt") or ""),
                raw_response_length=int(parse_meta.get("raw_response_length") or 0),
                parse_error_class=str(parse_meta.get("parse_error_class") or ""),
                parse_error_message=str(parse_meta.get("parse_error_message") or ""),
                json_attempt_count=json_attempt_count,
                coder_format_retry_count=max(0, json_attempt_count - 1),
                last_json_error=str(last_parse_meta.get("last_json_error") or ""),
                structured_output_mode=str(parse_meta.get("structured_output_mode") or ""),
                file_block_repair_source=str(parse_meta.get("file_block_repair_source") or ""),
                json_repair_source=str(parse_meta.get("json_repair_source") or ""),
                markdown_fence_found=bool(parse_meta.get("markdown_fence_found")),
                markdown_fence_stripped=bool(parse_meta.get("markdown_fence_stripped")),
                markdown_fence_language=str(parse_meta.get("markdown_fence_language") or ""),
            )

        replacement_target = str(parsed["target"]).replace("\\", "/").lstrip("./")
        replacement_target, path_error = _normalize_output_contract_path(replacement_target)
        if path_error:
            last_reason_code = "coder_invalid_replacement_payload"
            last_reason = f"Coder output target failed path safety validation: {path_error}."
            last_parse_meta = {
                **parse_meta,
                "parse_error_class": "path_validation",
                "parse_error_message": path_error,
                "last_json_error": path_error,
            }
            current_prompt = _coder_retry_prompt(
                prompt,
                "coder_invalid_replacement_payload",
                parser_error=path_error,
            )
            continue
        if replacement_target != target_path:
            last_reason_code = "coder_out_of_scope_file"
            last_reason = (
                f"Coder output targeted out-of-scope file {replacement_target}, "
                f"but allowed target is {target_path}."
            )
            last_parse_meta = {
                **parse_meta,
                "parse_error_class": "scope_validation",
                "parse_error_message": "out-of-scope file",
                "last_json_error": "out-of-scope file",
            }
            current_prompt = _coder_retry_prompt(
                prompt,
                "coder_out_of_scope_file",
                parser_error=last_reason,
            )
            continue

        return CoderResponse(
            status="ok",
            target_path=replacement_target,
            replacement_content=str(parsed["content"]),
            reasoning=str(
                parsed.get("notes")
                or (
                    "Coder returned replacement content_lines."
                    if parsed.get("content_source") == "content_lines"
                    else "Coder returned replacement content."
                )
            ),
            blocked_reason=None,
            blocked_needed_context=None,
            raw_response_excerpt=str(parse_meta.get("raw_response_excerpt") or ""),
            raw_response_length=int(parse_meta.get("raw_response_length") or 0),
            parse_error_class=str(last_parse_meta.get("parse_error_class") or ""),
            parse_error_message=str(last_parse_meta.get("parse_error_message") or ""),
            json_attempt_count=json_attempt_count,
            coder_format_retry_count=max(0, json_attempt_count - 1),
            last_json_error=str(last_parse_meta.get("last_json_error") or ""),
            structured_output_mode=str(parse_meta.get("structured_output_mode") or ""),
            file_block_repair_source=str(parse_meta.get("file_block_repair_source") or ""),
            json_repair_source=str(parse_meta.get("json_repair_source") or ""),
            markdown_fence_found=bool(parse_meta.get("markdown_fence_found")),
            markdown_fence_stripped=bool(parse_meta.get("markdown_fence_stripped")),
            markdown_fence_language=str(parse_meta.get("markdown_fence_language") or ""),
        )

    return CoderResponse(
        status="blocked",
        target_path=target_path,
        replacement_content=None,
        reasoning=f"{last_reason_code}: {last_reason}",
        blocked_reason=last_reason,
        blocked_needed_context=last_needed_context,
        raw_response_excerpt=str(last_parse_meta.get("raw_response_excerpt") or ""),
        raw_response_length=int(last_parse_meta.get("raw_response_length") or 0),
        parse_error_class=str(last_parse_meta.get("parse_error_class") or ""),
        parse_error_message=str(last_parse_meta.get("parse_error_message") or ""),
        json_attempt_count=int(last_parse_meta.get("json_attempt_count") or max_json_attempts),
        coder_format_retry_count=int(
            last_parse_meta.get("coder_format_retry_count") or max(0, max_json_attempts - 1)
        ),
        last_json_error=str(last_parse_meta.get("last_json_error") or ""),
        structured_output_mode=str(last_parse_meta.get("structured_output_mode") or ""),
        file_block_repair_source=str(last_parse_meta.get("file_block_repair_source") or ""),
        json_repair_source=str(last_parse_meta.get("json_repair_source") or ""),
        markdown_fence_found=bool(last_parse_meta.get("markdown_fence_found")),
        markdown_fence_stripped=bool(last_parse_meta.get("markdown_fence_stripped")),
        markdown_fence_language=str(last_parse_meta.get("markdown_fence_language") or ""),
    )


def propose_coder_agent_diff_payload_from_plan(
    *,
    architect_plan: Any,
    workspace_root: Path | None = None,
    llm_call: Callable[[str, str], str] | None = None,
    model_alias: str | None = None,
    reviewer_feedback: list[str] | None = None,
    force_live_model: bool = False,
    _review_attempt: int = 1,
    _previous_reviewer_signature: str = "",
) -> dict[str, Any]:
    """Run packet-only Coder, then convert its CoderResponse into approval diff payload."""
    if not _active_coder_timing.get("target_resolution_started_ms"):
        _mark_coder_timing("target_resolution_started")
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
    diagnostics["trial_mode"] = "live_apply" if force_live_model else "preview_only_or_standard"
    _set_trial_generation_provenance(diagnostics, trial_mode=force_live_model)
    diagnostics["coder_attempt_count"] = _review_attempt
    diagnostics["reviewer_retry_count"] = max(0, _review_attempt - 1)
    diagnostics["retry_reason"] = "reviewer_feedback" if _review_attempt > 1 else ""
    task_spec = task_spec_from_plan(architect_plan)
    diagnostics["task_spec"] = task_spec.to_dict()
    diagnostics["context_packet_summary"] = _coder_context_packet_summary(
        packet=packet,
        task_spec=task_spec.to_dict(),
        source_task=task,
        model_alias=model_alias or _coder_model_alias(),
        trial_mode=force_live_model,
    )
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
    _mark_coder_timing("architect_plan_done")
    prompt = _render_coder_prompt_from_packet(packet, source_task=task)
    diagnostics["prompt_size"] = len(prompt)
    _mark_coder_timing(
        "prompt_context",
        prompt_context_char_count=len(prompt),
        prompt_context_paths=[item.path for item in packet.context_slices[:12]],
        prompt_context_token_estimate=max(1, len(prompt) // 4),
    )
    selected_alias = model_alias or _coder_model_alias()
    _record_coder_provider_model_truth(
        diagnostics,
        selected_alias=selected_alias,
        provider_call_made=False,
    )

    deterministic = None if force_live_model else _deterministic_markdown_append_response(packet, task)
    if deterministic is None and not force_live_model and llm_call is None:
        deterministic = _deterministic_bounded_create_response(packet, task, root)
    if deterministic is not None:
        response = deterministic
        _mark_scaffold_or_fallback_provenance(diagnostics, response)
    else:
        _record_coder_provider_model_truth(
            diagnostics,
            selected_alias=selected_alias,
            provider_call_made=True,
        )
        response = propose_coder_agent_implementation_diff(
            packet,
            root,
            source_task=task,
            llm_call=llm_call,
            model_alias=model_alias,
            reviewer_feedback=reviewer_feedback,
        )
        _mark_model_response_provenance(diagnostics, response)
        if response.status == "blocked" and packet.operation == "create":
            fallback = _deterministic_bounded_create_response(packet, task, root)
            if fallback is not None:
                if force_live_model:
                    response = fallback
                    _mark_scaffold_or_fallback_provenance(
                        diagnostics,
                        response,
                        fallback_kind="blocked_model_create_disqualified_in_trial",
                    )
                else:
                    response = fallback
                    _mark_scaffold_or_fallback_provenance(diagnostics, response, fallback_kind="blocked_model_create")
    _merge_coder_response_diagnostics(diagnostics, response)
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
    from source_proxy.planning.bounded_create import packet_is_bounded_proposal_create

    if packet_is_bounded_proposal_create(packet) and (
        "Deterministic bounded-create" in str(response.reasoning or "")
    ):
        content_validation = {
            "ok": True,
            "missing": [],
            "summary": "Bounded proposal create scaffold passed structural validation.",
        }
    else:
        from source_proxy.decision.proposal_task import effective_planning_task_text

        content_validation = validate_replacement_content(
            workspace_root=root,
            target_path=replacement_target,
            content=content,
            task_text=effective_planning_task_text(task),
        )
        if not content_validation["ok"] and deterministic is None and not force_live_model and llm_call is None:
            fallback = _deterministic_bounded_create_response(packet, task, root)
            if fallback is not None:
                notes.append("Using deterministic bounded scaffold after initial model content validation failed.")
                response = fallback
                _mark_scaffold_or_fallback_provenance(diagnostics, response, fallback_kind="validation_failed")
                replacement_target = response.target_path
                content = _normalize_replacement_content(response.replacement_content or "")
                content_validation = {
                    "ok": True,
                    "missing": [],
                    "summary": "Bounded proposal scaffold passed structural validation.",
                }
        if not content_validation["ok"] and deterministic is None and not reviewer_feedback:
            reason = str(content_validation.get("summary") or "Replacement content validation failed.")
            notes.append(f"Retrying Coder after replacement content validation failed: {reason}")
            retry_response = propose_coder_agent_implementation_diff(
                packet,
                root,
                source_task=task,
                llm_call=llm_call,
                model_alias=model_alias,
                reviewer_feedback=[
                    (
                        "The previous replacement content failed deterministic validation: "
                        f"{reason}. Return a complete valid TS/TSX file as JSON content_lines."
                    )
                ],
            )
            _merge_coder_response_diagnostics(diagnostics, retry_response)
            if retry_response.status != "blocked" and retry_response.replacement_content is not None:
                response = retry_response
                _mark_model_response_provenance(diagnostics, response)
                replacement_target = response.target_path
                content = _normalize_replacement_content(response.replacement_content)
                content_validation = validate_replacement_content(
                    workspace_root=root,
                    target_path=replacement_target,
                    content=content,
                    task_text=effective_planning_task_text(task),
                )
            if not content_validation["ok"] and not force_live_model and llm_call is None:
                fallback = _deterministic_bounded_create_response(packet, task, root)
                if fallback is not None:
                    notes.append("Using deterministic bounded scaffold after validation feedback retry failed.")
                    response = fallback
                    _mark_scaffold_or_fallback_provenance(diagnostics, response, fallback_kind="validation_retry_failed")
                    replacement_target = response.target_path
                    content = _normalize_replacement_content(response.replacement_content)
                    content_validation = {
                        "ok": True,
                        "missing": [],
                        "summary": "Bounded proposal scaffold passed structural validation.",
                    }
    diagnostics["content_validation"] = content_validation
    if force_live_model and _trial_scaffold_or_fallback_used(diagnostics):
        diagnostics["validation_status"] = "scaffold_blocked_in_trial_mode"
        diagnostics["trial_result_trust_status"] = "invalid_scaffold_blocked"
        notes.append("CODER_BLOCKED reason_code: scaffold_blocked_in_trial_mode")
        return _coder_blocked_payload(
            target=replacement_target,
            notes=notes,
            diagnostics=diagnostics,
            bundle_name=bundle_name,
            reason="Trial mode disallows deterministic scaffold, backend-generated app page, and fallback-to-pass paths.",
            needed_context="Retry with model-authored output only. Scaffold/fallback rows must be INVALID or NEEDS_FIX, not PASS.",
            reason_code="scaffold_blocked_in_trial_mode",
        )
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

    _mark_coder_timing("diff_parse_started")
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
            needed_context=(
                "Retry Local Coder with stricter output repair, copy a manual browser prompt, "
                "or use Cloud/API route only if configured and explicitly chosen."
            ),
            reason_code="coder_backend_diff_generation_failed",
        )
    _mark_coder_timing("diff_parse_done", response_chars=len(content))
    diagnostics.update(snapshot_coder_timing_diagnostics())
    diagnostics["generated_diff_length"] = len(unified)
    diagnostics["normalized_diff_length"] = len(unified)
    if diagnostics.get("generation_source") == "model":
        diagnostics["diff_source"] = "backend_diff_from_model_authored_replacement"
        diagnostics["generated_diff_by_backend"] = True
        diagnostics["trial_result_trust_status"] = "model_authored_diff_proven"
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
            needed_context=(
                "Retry Local Coder with stricter output repair, copy a manual browser prompt, "
                "or use Cloud/API route only if configured and explicitly chosen."
            ),
            reason_code="coder_backend_diff_generation_failed",
        )

    prompt3_violations = _dummy_product_site_prompt3_diff_violations(
        root=root,
        unified_diff=unified,
        replacement_target=replacement_target,
        replacement_content=content,
    )
    if prompt3_violations:
        diagnostics["validation_status"] = "prompt_3_render_contract_rejected"
        diagnostics["prompt_3_render_contract_violations"] = prompt3_violations
        diagnostics["trial_result_trust_status"] = "model_output_not_usable"
        reason = f"Prompt 3 model output rejected before apply: {', '.join(prompt3_violations)}"
        notes.append(f"CODER_BLOCKED reason_code: {prompt3_violations[0]}")
        return _coder_blocked_payload(
            target=replacement_target,
            notes=notes,
            diagnostics=diagnostics,
            bundle_name=bundle_name,
            reason=reason,
            needed_context=(
                "Regenerate Prompt 3 with coherent products.js module wiring: static import requires "
                "index.html type=\"module\" script wiring, while classic script loading requires dynamic import('./products.js')."
            ),
            reason_code=prompt3_violations[0],
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
            needed_context=(
                "Retry Local Coder with stricter output repair, copy a manual browser prompt, "
                "or use Cloud/API route only if configured and explicitly chosen."
            ),
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
                force_live_model=force_live_model,
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


def _sha256_lf_trailing_newline_v1(payload: str) -> str:
    normalized = re.sub(r"\n*$", "", payload.replace("\r\n", "\n").replace("\r", "\n")) + "\n"
    return hashlib.sha256(normalized.encode("utf-8", errors="replace")).hexdigest()


def _deterministic_bounded_create_response(
    packet: CoderPacket,
    task: str,
    workspace_root: Path,
) -> CoderResponse | None:
    """Proposal-only new-file tasks with a known scaffold — no Coder LLM/router required."""
    from source_proxy.planning.bounded_create import (
        bounded_create_replacement_content,
        packet_is_bounded_proposal_create,
    )

    content = bounded_create_replacement_content(packet.target_file.path, task)
    if not packet_is_bounded_proposal_create(packet) and content is None:
        return None
    if not content:
        return None
    target_path = packet.target_file.path
    return CoderResponse(
        status="ok",
        target_path=target_path,
        replacement_content=content,
        reasoning="Deterministic bounded-create scaffold (no Coder LLM call).",
        blocked_reason=None,
        blocked_needed_context=None,
    )


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
    from source_proxy.decision.proposal_task import effective_planning_task_text
    from source_proxy.planning.architect import markdown_append_literal

    return markdown_append_literal(effective_planning_task_text(task))


def _coder_context_packet_summary(
    *,
    packet: CoderPacket,
    task_spec: dict[str, Any],
    source_task: str,
    model_alias: str,
    trial_mode: bool,
) -> dict[str, Any]:
    return {
        "user_prompt_excerpt": _safe_raw_response_excerpt(source_task)[:300],
        "selected_target": packet.target_file.path,
        "selected_target_exists": packet.target_file.exists,
        "selected_target_candidates": [packet.target_file.path],
        "allowed_files": list(task_spec.get("allowed_files") or []),
        "forbidden_files": list(task_spec.get("forbidden_files") or []),
        "protected_paths": list(packet.forbidden_paths),
        "repo_snippet_summaries": [
            {
                "path": item.path,
                "kind": item.kind,
                "chars": len(item.content),
                "sha256": item.sha256,
                "line_range": item.line_range,
            }
            for item in packet.context_slices[:12]
        ],
        "repo_snippet_omitted_count": max(0, len(packet.context_slices) - 12),
        "obsidian_context_summary": obsidian_context_diagnostics(),
        "model_route": {
            "provider": route_provider_for_alias(model_alias) or "",
            "model_alias": model_alias,
            "model": route_model_for_alias(model_alias) or "",
        },
        "trial_mode_flags": {
            "trial_mode": "live_apply" if trial_mode else "preview_only_or_standard",
            "force_live_model": trial_mode,
        },
        "scaffold_fallback_ban_flags": dict(TRIAL_MODE_BAN_CONTRACT),
        "expected_output_format": "single replacement file block; legacy JSON replace_file still accepted; backend converts model-authored content to unified diff",
        "checks_that_will_run": list(task_spec.get("verification") or []),
        "rollback_reversal_available": True,
        "secrets_policy": "safe summary only; no .env, token, credential, or full note dumps",
    }


def _base_coder_diagnostics(target_path: str) -> dict[str, Any]:
    return {
        "selected_model_alias": "",
        "available_model_aliases": sorted(available_model_aliases()),
        "provider": "",
        "model": "",
        "litellm_model": "",
        "provider_model_source": "unknown",
        "provider_model_status": "unknown",
        "provider_call_made": False,
        "provider_call_authorized": False,
        "hermes_lane_available": "local" in available_model_aliases(),
        "hermes_used_for_this_run": None,
        "router_call_attempted": False,
        "raw_response_length": 0,
        "raw_response_excerpt": "",
        "parse_error_class": "",
        "parse_error_message": "",
        "json_attempt_count": 0,
        "coder_format_retry_count": 0,
        "last_json_error": "",
        "structured_output_mode": "",
        "file_block_repair_source": "",
        "json_repair_source": "",
        "markdown_fence_found": False,
        "markdown_fence_stripped": False,
        "markdown_fence_language": "",
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
        "memory_context_diagnostics": obsidian_context_diagnostics(),
        "obsidian_context_used_in_prompt": False,
        "bundle_snapshot_check": "not_applicable",
        "bundle_snapshot_expected_sha256": "",
        "bundle_snapshot_actual_sha256": "",
        "task_spec": None,
        "recommended_next_action": "",
    }


def _record_coder_provider_model_truth(
    diagnostics: dict[str, Any],
    *,
    selected_alias: str,
    provider_call_made: bool = False,
) -> None:
    provider = route_provider_for_alias(selected_alias) or ("ollama" if selected_alias == "local" else "")
    model = route_model_for_alias(selected_alias) or ""
    diagnostics["selected_model_alias"] = selected_alias
    diagnostics["provider"] = provider
    diagnostics["model"] = model
    diagnostics["litellm_model"] = model
    diagnostics["provider_model_source"] = "runtime" if provider_call_made else "config"
    diagnostics["provider_model_status"] = "available" if provider_call_made else ("configured" if model else "unknown")
    diagnostics["provider_call_made"] = provider_call_made
    diagnostics["provider_call_authorized"] = provider_call_made
    diagnostics["hermes_lane_available"] = "local" in available_model_aliases()
    configured_model_is_hermes = (
        True
        if "hermes" in model.lower()
        else False
        if model
        else None
    )
    diagnostics["hermes_used_for_this_run"] = (
        True
        if "hermes" in model.lower()
        else False
        if provider_call_made and model
        else None
    )
    diagnostics["configured_model_is_hermes"] = configured_model_is_hermes
    blocked_reason = (
        "Provider/model was not resolved by Source Proxy."
        if not model
        else "Local/Ollama lane is configured, but the selected model is not Hermes."
        if configured_model_is_hermes is False
        else ""
    )
    local_route_status = ollama_route_status_entry() if provider == "ollama" else {}
    diagnostics["provider_model_truth"] = {
        "providerId": "local" if provider == "ollama" else provider or "unknown",
        "providerLabel": "Local / Ollama" if provider == "ollama" else provider or "unknown",
        "modelId": model or "unknown",
        "modelLabel": model.removeprefix("ollama_chat/") if model else "Unknown local model",
        "family": "local/ollama/hermes" if provider == "ollama" else "unknown",
        "status": diagnostics["provider_model_status"],
        "configured": bool(model),
        "configuredModelIsHermes": configured_model_is_hermes,
        "previewAvailable": True,
        "externalCallAvailable": False if provider == "ollama" else bool(provider),
        "authority": {
            "canDraft": True,
            "canPreview": True,
            "canApply": False,
            "canVerify": False,
            "canCommit": False,
            "canPush": False,
        },
        "blockedReason": blocked_reason,
        "apiBaseHost": local_route_status.get("api_base_host"),
        "configuredOllamaModel": local_route_status.get("ollama_model"),
        "probeOk": local_route_status.get("probe_ok"),
        "selectedVia": local_route_status.get("selected_via"),
        "source": diagnostics["provider_model_source"],
        "providerCallMade": provider_call_made,
        "providerCallAuthorized": provider_call_made,
        "hermesLaneAvailable": diagnostics["hermes_lane_available"],
        "hermesUsedForThisRun": diagnostics["hermes_used_for_this_run"],
    }


TRIAL_MODE_BAN_CONTRACT = {
    "allow_known_scaffold": False,
    "allow_generic_scaffold": False,
    "allow_deterministic_stub": False,
    "allow_backend_generated_page": False,
    "allow_fallback_to_pass": False,
    "require_model_authored_diff": True,
}


def _set_trial_generation_provenance(
    diagnostics: dict[str, Any],
    *,
    trial_mode: bool,
) -> None:
    diagnostics["trial_mode_ban_contract"] = dict(TRIAL_MODE_BAN_CONTRACT)
    diagnostics["generation_source"] = "unknown"
    diagnostics["diff_source"] = "none"
    diagnostics["model_output_classification"] = "not_classified"
    diagnostics["raw_response_excerpt_safe"] = ""
    diagnostics["scaffold_used"] = False
    diagnostics["scaffold_kind"] = ""
    diagnostics["fallback_used"] = False
    diagnostics["fallback_kind"] = ""
    diagnostics["parser_repair_used"] = False
    diagnostics["bounded_create_used"] = False
    diagnostics["known_scaffold_used"] = False
    diagnostics["generic_scaffold_used"] = False
    diagnostics["model_raw_diff_used"] = False
    diagnostics["generated_diff_by_backend"] = False
    diagnostics["trial_result_trust_status"] = (
        "requires_model_authored_diff" if trial_mode else "not_trial_mode"
    )


MODEL_OUTPUT_CONTRACT_VALUES = {
    "model_unified_diff",
    "model_structured_file_edit",
    "model_markdown_code_block",
    "model_full_file_content",
    "model_prose_only",
    "model_empty_response",
    "model_malformed_output",
    "model_wrong_file",
    "model_protected_path_attempt",
    "scaffold_blocked",
    "fallback_blocked",
    "unknown_untrusted",
}


MODEL_OUTPUT_NO_DIFF_CAUSES = {
    "model_empty_response",
    "model_prose_only_no_file_change",
    "model_code_block_unparsed",
    "model_full_file_unconverted",
    "diff_extractor_no_candidate",
    "target_inference_blocked",
    "allowed_files_rejected_change",
    "verification_rejected_patch",
}


def _safe_raw_response_excerpt(value: str) -> str:
    cleaned = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[redacted-email]", value or "")
    cleaned = re.sub(r"sk-[A-Za-z0-9_-]{12,}", "[redacted-token]", cleaned)
    return cleaned[:500]


def _classify_model_output(response: CoderResponse) -> str:
    reason_code = _coder_response_reason_code(response)
    if reason_code in {"coder_target_mismatch", "coder_task_spec_diff_blocked"}:
        return "model_wrong_file"
    if reason_code in {"protected_path", "secret_path", "path_escape", "outside_workspace"}:
        return "model_protected_path_attempt"
    raw = (response.raw_response_excerpt or "").strip()
    if response.raw_response_length <= 0 or not raw:
        return "model_empty_response"
    if _looks_like_unified_diff(raw):
        return "model_unified_diff"
    if raw.startswith("```"):
        return "model_markdown_code_block"
    if response.replacement_content is not None:
        return "model_structured_file_edit"
    if response.parse_error_class or response.last_json_error:
        if _looks_like_full_file_content(raw):
            return "model_full_file_content"
        if _looks_like_prose_only(raw):
            return "model_prose_only"
        return "model_malformed_output"
    if _looks_like_full_file_content(raw):
        return "model_full_file_content"
    if _looks_like_prose_only(raw):
        return "model_prose_only"
    return "unknown_untrusted"


def _no_diff_failure_cause_for(
    *,
    reason_code: str,
    classification: str,
    response: CoderResponse | None = None,
) -> str:
    if classification == "model_empty_response" or reason_code == "coder_empty_model_response":
        return "model_empty_response"
    if reason_code in {"target_unresolved", "target_missing", "coder_packet_missing_context", "coder_needs_context"}:
        return "target_inference_blocked"
    if reason_code in {"coder_target_mismatch", "coder_out_of_scope_file", "coder_task_spec_diff_blocked"}:
        return "allowed_files_rejected_change"
    if reason_code in {
        "coder_backend_diff_generation_failed",
        "coder_replacement_content_validation_failed",
        "prompt_3_static_import_without_module_script",
        "prompt_3_hardcoded_cards",
        "prompt_3_missing_product_data_import",
    }:
        return "verification_rejected_patch"
    if classification == "model_markdown_code_block":
        return "model_code_block_unparsed"
    if classification == "model_full_file_content":
        return "model_full_file_unconverted"
    if classification == "model_prose_only":
        return "model_prose_only_no_file_change"
    if classification == "model_unified_diff":
        return "model_code_block_unparsed"
    if response is not None and response.raw_response_length > 0:
        return "diff_extractor_no_candidate"
    return "diff_extractor_no_candidate"


def _looks_like_full_file_content(raw: str) -> bool:
    stripped = raw.strip()
    if "\n" not in stripped:
        return False
    markers = (
        '"use client"',
        "'use client'",
        "import ",
        "export ",
        "def ",
        "class ",
        "function ",
        "const ",
    )
    return any(stripped.startswith(marker) or f"\n{marker}" in stripped for marker in markers)


def _looks_like_prose_only(raw: str) -> bool:
    lowered = raw.strip().lower()
    if not lowered:
        return False
    if any(marker in lowered for marker in ("{", "}", "@@", "diff --git", "```")):
        return False
    words = re.findall(r"[a-z]{2,}", lowered)
    return len(words) >= 3


def _recommended_next_action_for(
    *,
    reason_code: str,
    classification: str,
) -> str:
    if reason_code in {"target_unresolved", "coder_packet_missing_context", "coder_needs_context"}:
        return "ask_user_for_clarification_or_regenerate_architect_context"
    if classification in {"model_empty_response", "model_prose_only", "model_malformed_output"}:
        return "retry_with_stricter_output_contract_or_stronger_model"
    if classification in {
        "model_prose_only_no_file_change",
        "model_code_block_unparsed",
        "model_full_file_unconverted",
        "diff_extractor_no_candidate",
    }:
        return "retry_with_stricter_output_contract_or_stronger_model"
    if classification in {"model_wrong_file", "model_protected_path_attempt"}:
        return "regenerate_with_allowed_files_and_protected_path_block"
    if classification in {"scaffold_blocked", "fallback_blocked"}:
        return "retry_model_authored_output_only"
    if reason_code in {"coder_model_not_configured", "local_model_unavailable", "coder_model_router_error"}:
        return "check_model_route_or_use_configured_stronger_model"
    if reason_code == "coder_replacement_content_validation_failed":
        return "provide_more_repo_context_or_retry_with_validation_feedback"
    if reason_code == "coder_backend_diff_generation_failed":
        return "inspect_file_manually_or_retry_with_narrower_context"
    return "inspect_failure_reason_then_retry_or_escalate_model"


def _mark_model_response_provenance(
    diagnostics: dict[str, Any],
    response: CoderResponse,
) -> None:
    diagnostics["generation_source"] = "model" if response.raw_response_length > 0 else "model_empty_or_unproven"
    diagnostics["diff_source"] = "pending_backend_diff_from_model_output"
    diagnostics["raw_response_length"] = response.raw_response_length
    diagnostics["raw_response_excerpt_safe"] = _safe_raw_response_excerpt(response.raw_response_excerpt)
    diagnostics["parser_repair_used"] = response.json_attempt_count > 1 or response.coder_format_retry_count > 0
    classification = _classify_model_output(response)
    diagnostics["model_output_classification"] = classification
    diagnostics["model_output_contract_values"] = sorted(MODEL_OUTPUT_CONTRACT_VALUES)
    if response.status == "blocked":
        reason_code = _coder_response_reason_code(response)
        no_diff_cause = _no_diff_failure_cause_for(
            reason_code=reason_code,
            classification=classification,
            response=response,
        )
        diagnostics["trial_result_trust_status"] = "model_output_not_usable"
        diagnostics["no_diff_failure_cause"] = no_diff_cause
        diagnostics["safe_response_classification"] = no_diff_cause
        diagnostics["parser_extractor_decision"] = (
            f"rejected:{reason_code}:{response.parse_error_class or response.last_json_error or classification}"
        )
        diagnostics["markdown_code_blocks_present"] = bool(response.markdown_fence_found)
        diagnostics["unified_diff_markers_present"] = classification == "model_unified_diff"
        diagnostics["full_file_content_likely_present"] = classification == "model_full_file_content"
        diagnostics["recommended_next_action"] = _recommended_next_action_for(
            reason_code=reason_code,
            classification=classification,
        )
    elif response.replacement_content is not None:
        diagnostics["trial_result_trust_status"] = "model_authored_output_pending_validation"
        diagnostics["recommended_next_action"] = "run_backend_validation_and_diff_preview"


def _mark_scaffold_or_fallback_provenance(
    diagnostics: dict[str, Any],
    response: CoderResponse,
    *,
    fallback_kind: str = "deterministic_scaffold",
) -> None:
    reasoning = str(response.reasoning or "").lower()
    target = str(response.target_path or "")
    known_scaffold = "deterministic bounded-create" in reasoning or target.startswith("src/app/agent-lab/")
    diagnostics["generation_source"] = "backend_scaffold"
    diagnostics["diff_source"] = "backend_generated_page"
    diagnostics["model_output_classification"] = (
        "scaffold_blocked" if known_scaffold else "fallback_blocked"
    )
    diagnostics["scaffold_used"] = True
    diagnostics["scaffold_kind"] = "known_agent_lab_scaffold" if known_scaffold else "generic_scaffold"
    diagnostics["fallback_used"] = True
    diagnostics["fallback_kind"] = fallback_kind
    diagnostics["bounded_create_used"] = True
    diagnostics["known_scaffold_used"] = known_scaffold
    diagnostics["generic_scaffold_used"] = not known_scaffold
    diagnostics["generated_diff_by_backend"] = True
    diagnostics["trial_result_trust_status"] = "invalid_scaffold_or_fallback"
    diagnostics["recommended_next_action"] = "retry_model_authored_output_only"


def _trial_scaffold_or_fallback_used(diagnostics: dict[str, Any]) -> bool:
    return any(
        bool(diagnostics.get(key))
        for key in (
            "scaffold_used",
            "fallback_used",
            "bounded_create_used",
            "known_scaffold_used",
            "generic_scaffold_used",
        )
    ) or diagnostics.get("generation_source") == "backend_scaffold"


def _merge_coder_response_diagnostics(
    diagnostics: dict[str, Any],
    response: CoderResponse,
) -> None:
    diagnostics["raw_response_length"] = response.raw_response_length
    diagnostics["raw_response_excerpt"] = response.raw_response_excerpt
    diagnostics["raw_response_excerpt_safe"] = _safe_raw_response_excerpt(response.raw_response_excerpt)
    diagnostics["parse_error_class"] = response.parse_error_class
    diagnostics["parse_error_message"] = response.parse_error_message
    diagnostics["json_attempt_count"] = response.json_attempt_count
    diagnostics["coder_format_retry_count"] = response.coder_format_retry_count
    diagnostics["last_json_error"] = response.last_json_error
    diagnostics["structured_output_mode"] = response.structured_output_mode
    diagnostics["file_block_repair_source"] = response.file_block_repair_source
    diagnostics["json_repair_source"] = response.json_repair_source
    diagnostics["markdown_fence_found"] = response.markdown_fence_found
    diagnostics["markdown_fence_stripped"] = response.markdown_fence_stripped
    diagnostics["markdown_fence_language"] = response.markdown_fence_language


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
        "coder_response_wrong_format_unified_diff",
        "coder_response_repair_exhausted",
        "coder_target_mismatch",
        "coder_out_of_scope_file",
        "coder_invalid_replacement_payload",
        "coder_replacement_content_validation_failed",
    ):
        if reason_code in text:
            return reason_code
    if "model_not_configured" in text or "not configured" in text:
        return "coder_model_not_configured"
    if local_model_unavailable_from_error(text):
        return "local_model_unavailable"
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
    classification = str(diagnostics.get("model_output_classification") or "")
    if not classification or classification == "not_classified":
        diagnostics["model_output_classification"] = (
            "scaffold_blocked"
            if _trial_scaffold_or_fallback_used(diagnostics)
            else "unknown_untrusted"
        )
        classification = str(diagnostics["model_output_classification"])
    no_diff_cause = str(diagnostics.get("no_diff_failure_cause") or "")
    if not no_diff_cause and not _trial_scaffold_or_fallback_used(diagnostics):
        no_diff_cause = _no_diff_failure_cause_for(
            reason_code=reason_code,
            classification=classification,
        )
        diagnostics["no_diff_failure_cause"] = no_diff_cause
    if no_diff_cause:
        diagnostics["safe_response_classification"] = no_diff_cause
    diagnostics["parser_extractor_decision"] = str(
        diagnostics.get("parser_extractor_decision")
        or f"rejected:{reason_code}:{classification}"
    )
    diagnostics["markdown_code_blocks_present"] = bool(
        diagnostics.get("markdown_code_blocks_present")
        if "markdown_code_blocks_present" in diagnostics
        else diagnostics.get("markdown_fence_found")
    )
    diagnostics["unified_diff_markers_present"] = bool(
        diagnostics.get("unified_diff_markers_present")
        if "unified_diff_markers_present" in diagnostics
        else classification == "model_unified_diff"
    )
    diagnostics["full_file_content_likely_present"] = bool(
        diagnostics.get("full_file_content_likely_present")
        if "full_file_content_likely_present" in diagnostics
        else classification == "model_full_file_content"
    )
    diagnostics["model_output_usable"] = False
    diagnostics["scaffold_or_fallback_blocked"] = _trial_scaffold_or_fallback_used(diagnostics)
    diagnostics["recommended_next_action"] = (
        str(diagnostics.get("recommended_next_action") or "")
        or _recommended_next_action_for(
            reason_code=reason_code,
            classification=classification,
        )
    )
    return {
        "proposed_diff": "",
        "target": target,
        "coder_notes": notes,
        "coder_diagnostics": diagnostics,
        "coderDiagnostics": diagnostics,
        "bundle": bundle_name,
        "coder_blocked": True,
        "coderBlocked": True,
        "blocked_reason": reason,
        "blockedReason": reason,
        "needed_context": needed_context,
        "neededContext": needed_context,
        "reason_code": reason_code,
        "reasonCode": reason_code,
    }


def _normalize_repo_rel_path(rel_path: str) -> str:
    from source_proxy.safety.paths import normalize_repo_path_candidate

    return normalize_repo_path_candidate(rel_path).lower()


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
    configured = _configured_coder_model_alias()
    enabled = available_model_aliases()
    if configured:
        if configured in enabled:
            return configured
        return configured
    if "coder" in enabled:
        return "coder"
    if "local" in enabled:
        return "local"
    return "coder"


def _dummy_product_site_create_model_alias() -> str:
    configured = _configured_coder_model_alias()
    enabled = available_model_aliases()
    if configured and configured in enabled:
        return configured
    for alias in ("coder", "local", "openai", "anthropic", "deepseek"):
        if alias in enabled:
            return alias
    return configured or "coder"


def _configured_coder_model_alias() -> str:
    return os.getenv("SOURCE_PROXY_CODER_MODEL_ALIAS", "").strip()


def _coder_model_alias_configuration_error(alias: str) -> tuple[str, str] | None:
    enabled = available_model_aliases()
    if not alias:
        return (
            "coder_model_not_configured",
            "Set SOURCE_PROXY_CODER_MODEL_ALIAS to an available local model alias, or copy a manual browser prompt.",
        )
    if alias not in enabled:
        available = ", ".join(sorted(enabled)) or "none"
        return (
            "coder_model_not_configured",
            (
                f"{alias!r} is not an available model alias. Available aliases: {available}. "
                "Set SOURCE_PROXY_CODER_MODEL_ALIAS to an available local model alias, or copy a manual browser prompt."
            ),
        )
    return None


def _call_coder_llm(
    prompt: str,
    *,
    model_alias: str | None = None,
    timeout_seconds: float | None = None,
    num_retries: int | None = None,
) -> str:
    alias = model_alias or _coder_model_alias()
    central_gate_check("model_call", run_id=f"coder_llm:{alias}")
    resolved_model = route_model_for_alias(alias) or ""
    ollama_route = resolve_ollama_route(probe=False)
    coder_ollama_model = resolve_coder_ollama_model_name(probe=False)
    deadline_seconds = float(
        os.getenv("SOURCE_PROXY_CODER_SYNC_DEADLINE_SEC", "180") or "180"
    )
    request_timeout = (
        timeout_seconds
        if timeout_seconds is not None
        else _read_coder_timeout_seconds()
    )
    remaining_ms = None
    origin = _active_coder_timing.get("target_resolution_started_ms")
    if isinstance(origin, (int, float)):
        remaining_ms = max(
            0.0,
            deadline_seconds * 1000 - (time.perf_counter() * 1000 - origin),
        )
    _mark_coder_timing(
        "coder_llm",
        model_requested=alias,
        model_resolved=resolved_model,
        litellm_model=resolved_model,
        ollama_base=ollama_route.api_base,
        coder_ollama_model=coder_ollama_model,
        prompt_context_char_count=len(prompt),
        deadline_seconds=deadline_seconds,
        remaining_ms_at_provider_start=remaining_ms,
        request_timeout_seconds=request_timeout,
    )
    provider_started = time.perf_counter()
    _mark_coder_timing("provider_request_started", model_requested=alias)
    completion_kwargs: dict[str, Any] = {
        "model": alias,
        "messages": [{"role": "system", "content": prompt}],
        "stream": False,
        "temperature": 0,
        "timeout": request_timeout,
    }
    if num_retries is not None:
        completion_kwargs["num_retries"] = num_retries
    try:
        completion = get_router().completion(**completion_kwargs)
    except Exception as error:
        _mark_coder_timing(
            "provider_request_failed",
            exception_type=type(error).__name__,
            exception_message=str(error)[:240],
            provider_done_ms=round((time.perf_counter() - provider_started) * 1000, 2),
        )
        raise
    provider_done_ms = round((time.perf_counter() - provider_started) * 1000, 2)
    _mark_coder_timing(
        "provider_request_done",
        provider_done_ms=provider_done_ms,
        provider_first_response_ms=provider_done_ms,
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
    return normalize_agent_role(value) or "architect"
