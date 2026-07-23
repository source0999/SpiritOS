from __future__ import annotations

import fnmatch
import hashlib
import json
import re
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

from pathlib import Path

from source_proxy.safety.paths import (
    normalize_repo_path_candidate,
    path_escapes_workspace,
    unsafe_target_finding,
)

_PROPOSAL_FENCED_JSON_RE = re.compile(r"```json\s*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
EVIDENCE_GUIDED_REPAIR_TASK_MARKER = (
    "SERVER-OWNED EVIDENCE-GUIDED REPAIR INPUT"
)
EVIDENCE_GUIDED_REPAIR_TASK_INSTRUCTION = (
    "Treat the current applied files as the baseline. Address the exact failure "
    "evidence below. Return a fresh proposal; do not reuse the prior patch or "
    "approval. Hash commitments bind omitted audit metadata; hashes are not "
    "implementation instructions."
)


@dataclass(frozen=True)
class BoundedProposal:
    task: str
    mode: str
    target_file: str
    allowed_files: tuple[str, ...]
    forbidden_files: tuple[str, ...]
    expected_checks: tuple[str, ...]
    rollback_hint: str


def parse_bounded_proposal_task(task: str) -> BoundedProposal | None:
    text = (task or "").strip()
    if "proposal task:" not in text.lower():
        return None
    match = _PROPOSAL_FENCED_JSON_RE.search(text)
    if not match:
        return None
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return _bounded_proposal_from_payload(payload)


def _bounded_proposal_from_payload(payload: dict[str, Any]) -> BoundedProposal | None:
    task_text = str(payload.get("task") or "").strip()
    target_raw = payload.get("target_file")
    target_file = ""
    if isinstance(target_raw, str):
        target_file = normalize_repo_path_candidate(target_raw)
    mode = "readonly" if str(payload.get("mode") or "").strip().lower() == "readonly" else "proposal"
    allowed_files = _normalize_path_list(payload.get("allowed_files"))
    forbidden_files = _normalize_path_list(payload.get("forbidden_files"))
    expected_checks = _normalize_string_list(payload.get("expected_checks"))
    rollback_hint = str(payload.get("rollback_hint") or "").strip()
    if not task_text and not target_file:
        return None
    return BoundedProposal(
        task=task_text,
        mode=mode,
        target_file=target_file,
        allowed_files=tuple(allowed_files),
        forbidden_files=tuple(forbidden_files),
        expected_checks=tuple(expected_checks),
        rollback_hint=rollback_hint,
    )


def path_matches_forbidden(path: str, forbidden_files: tuple[str, ...] | list[str]) -> bool:
    normalized = normalize_repo_path_candidate(path)
    if not normalized:
        return False
    base = normalized.split("/")[-1]
    for pattern in forbidden_files:
        blocked = normalize_repo_path_candidate(str(pattern))
        if not blocked:
            continue
        if blocked.endswith("/*"):
            if normalized.startswith(blocked[:-1]):
                return True
            continue
        if blocked.endswith("/"):
            if normalized.startswith(blocked):
                return True
            continue
        if normalized == blocked or base == blocked:
            return True
        if fnmatch.fnmatch(normalized, blocked) or fnmatch.fnmatch(base, blocked):
            return True
    return False


def _normalize_path_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        path = normalize_repo_path_candidate(item)
        if path:
            out.append(path)
    return out


def _normalize_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


_PROPOSAL_TASK_MARKER_RE = re.compile(
    r"(?im)^\s*proposal\s+task\s*:\s*$",
)
_REPAIR_TASK_MARKER_RE = re.compile(
    rf"(?m)^{re.escape(EVIDENCE_GUIDED_REPAIR_TASK_MARKER)}$",
)
_REPAIR_TASK_SCHEMAS = {
    "coding.evidence-guided-repair-prompt/v2",
}
_TRUSTED_REPAIR_TASK_TTL_SECONDS = 7_200.0
_TRUSTED_REPAIR_TASK_LIMIT = 512
_TRUSTED_REPAIR_TASKS: OrderedDict[str, tuple[str, float]] = OrderedDict()
_TRUSTED_REPAIR_TASKS_LOCK = threading.Lock()


def _text_before_proposal_marker(task: str) -> str:
    match = _PROPOSAL_TASK_MARKER_RE.search(task or "")
    if not match:
        return (task or "").strip()
    return (task or "")[: match.start()].rstrip()


def _validated_repair_original_task(task: str) -> str | None:
    text = (task or "").strip()
    markers = list(_REPAIR_TASK_MARKER_RE.finditer(text))
    if len(markers) != 1:
        return None
    marker = markers[0]
    json_start = text.rfind("\n{")
    if json_start < marker.end():
        return None
    prefix = text[: marker.start()]
    if not prefix.endswith("\n\n"):
        return None
    original_prefix = prefix[:-2]
    try:
        json_text = text[json_start + 1 :]
        payload = json.loads(json_text)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(payload, dict):
        return None
    schema = payload.get("schema_version")
    original_task = payload.get("original_task")
    if (
        schema not in _REPAIR_TASK_SCHEMAS
        or not isinstance(original_task, str)
        or not original_task.strip()
        or original_task != original_task.strip()
        or original_task != original_prefix
    ):
        return None
    if not _valid_v2_repair_envelope(
        payload,
        framing=text[marker.end() : json_start],
        json_text=json_text,
    ):
        return None
    return original_task


def register_trusted_evidence_guided_repair_task(
    task: str,
    *,
    original_task: str,
) -> None:
    """Register one exact server-rendered repair task for bounded planning.

    Textual markers and attacker-reproducible hashes are not authority.  The
    renderer and consumer share this bounded, process-local registration so
    arbitrary user text cannot create a Planner/Coder split view.
    """

    text = (task or "").strip()
    normalized_original = original_task.strip()
    if _validated_repair_original_task(text) != normalized_original:
        raise ValueError("trusted_repair_task_envelope_invalid")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    now = time.monotonic()
    with _TRUSTED_REPAIR_TASKS_LOCK:
        _prune_trusted_repair_tasks(now)
        _TRUSTED_REPAIR_TASKS[digest] = (
            normalized_original,
            now + _TRUSTED_REPAIR_TASK_TTL_SECONDS,
        )
        _TRUSTED_REPAIR_TASKS.move_to_end(digest)
        while len(_TRUSTED_REPAIR_TASKS) > _TRUSTED_REPAIR_TASK_LIMIT:
            _TRUSTED_REPAIR_TASKS.popitem(last=False)


def trusted_evidence_guided_repair_original_task(
    task: str,
) -> str | None:
    """Return the original task only for an exact active server registration."""

    text = (task or "").strip()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    now = time.monotonic()
    with _TRUSTED_REPAIR_TASKS_LOCK:
        _prune_trusted_repair_tasks(now)
        trusted = _TRUSTED_REPAIR_TASKS.get(digest)
    if trusted is None:
        return None
    validated = _validated_repair_original_task(text)
    return trusted[0] if validated == trusted[0] else None


def _prune_trusted_repair_tasks(now: float) -> None:
    expired = [
        digest
        for digest, (_original, expires_at) in _TRUSTED_REPAIR_TASKS.items()
        if expires_at <= now
    ]
    for digest in expired:
        _TRUSTED_REPAIR_TASKS.pop(digest, None)


def _valid_v2_repair_envelope(
    payload: dict[str, Any],
    *,
    framing: str,
    json_text: str,
) -> bool:
    evidence = payload.get("repair_evidence")
    commitments = payload.get("repair_request_commitments")
    public_failure = (
        evidence.get("public_failure")
        if isinstance(evidence, dict)
        else None
    )
    current_state = (
        evidence.get("current_applied_state")
        if isinstance(evidence, dict)
        else None
    )
    requirements = (
        evidence.get("requirements")
        if isinstance(evidence, dict)
        else None
    )
    diagnosis = (
        evidence.get("deterministic_diagnosis")
        if isinstance(evidence, dict)
        else None
    )
    if (
        framing != f"\n{EVIDENCE_GUIDED_REPAIR_TASK_INSTRUCTION}"
        or set(payload)
        != {
            "schema_version",
            "original_task",
            "repair_evidence",
            "repair_request_commitments",
        }
        or not isinstance(evidence, dict)
        or not isinstance(commitments, dict)
        or set(evidence)
        != {
            "failure_class",
            "source_lane",
            "public_failure",
            "deterministic_diagnosis",
            "current_applied_state",
            "requirements",
        }
        or not isinstance(public_failure, dict)
        or not isinstance(public_failure.get("checks"), list)
        or not isinstance(public_failure.get("blocked_reasons"), list)
        or not isinstance(public_failure.get("findings"), list)
        or not _valid_repair_public_failure(public_failure)
        or not _valid_repair_diagnosis(diagnosis)
        or not isinstance(current_state, dict)
        or not _valid_repair_current_state(current_state)
        or not isinstance(requirements, dict)
        or not set(requirements).issubset(
            {
                "fresh_proposal_required",
                "fresh_approval_required",
                "current_applied_state_is_baseline",
                "new_evidence_or_changed_strategy_required",
            }
        )
        or any(not isinstance(value, bool) for value in requirements.values())
        or not _valid_bounded_optional_scalar(
            evidence.get("failure_class"),
            limit=500,
        )
        or not _valid_bounded_optional_scalar(
            evidence.get("source_lane"),
            limit=500,
        )
        or not isinstance(commitments.get("repair_request_sha256"), str)
        or not re.fullmatch(
            r"sha256:[0-9a-f]{64}",
            commitments["repair_request_sha256"],
        )
    ):
        return False
    allowed_commitments = {
        "attempt_number",
        "repair_request_sha256",
        "repair_input_sha256",
        "feedback_sha256",
        "current_state_manifest_sha256",
        "repair_diagnostic_sha256",
        "parent_attempt_seal_sha256",
        "prior_approved_diff_sha256",
    }
    if not set(commitments).issubset(allowed_commitments):
        return False
    for key, value in commitments.items():
        if key == "attempt_number":
            if not isinstance(value, int) or isinstance(value, bool):
                return False
        elif not isinstance(value, str) or not re.fullmatch(
            r"(?:sha256:)?[0-9a-f]{64}",
            value,
        ):
            return False
    try:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError):
        return False
    return canonical == json_text


def _valid_repair_public_failure(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    required = {"blocked_reasons", "checks", "findings"}
    allowed = required | {
        "status",
        "verdict",
        "reason_code",
        "summary",
        "bounded_feedback_excerpt",
    }
    if not required.issubset(value) or not set(value).issubset(allowed):
        return False
    blocked = value.get("blocked_reasons")
    findings = value.get("findings")
    checks = value.get("checks")
    if (
        not _valid_bounded_string_list(blocked, count=6, item_limit=500)
        or not _valid_bounded_string_list(findings, count=8, item_limit=500)
        or not isinstance(checks, list)
        or len(checks) > 6
    ):
        return False
    output_budget = 0
    allowed_check_keys = {
        "id",
        "status",
        "summary",
        "command_text",
        "exit_code",
        "output_tail",
    }
    for check in checks:
        if (
            not isinstance(check, dict)
            or not set(check).issubset(allowed_check_keys)
            or any(
                not _valid_bounded_optional_scalar(item, limit=500)
                for key, item in check.items()
                if key != "output_tail"
            )
        ):
            return False
        output = check.get("output_tail")
        if output is not None:
            if not isinstance(output, str) or len(output) > 3_000:
                return False
            output_budget += len(output)
    if output_budget > 8_000:
        return False
    for key in ("status", "verdict", "reason_code", "summary"):
        if key in value and not _valid_bounded_optional_scalar(
            value[key],
            limit=500,
        ):
            return False
    fallback = value.get("bounded_feedback_excerpt")
    return fallback is None or (
        isinstance(fallback, str) and len(fallback) <= 8_000
    )


def _valid_repair_diagnosis(value: Any) -> bool:
    allowed = {
        "diagnostic_code",
        "failure_class",
        "failure_kind",
        "stage",
        "retry_owner",
        "retryable",
        "strategy_change_required",
        "genuine_stop",
    }
    return (
        isinstance(value, dict)
        and set(value).issubset(allowed)
        and all(
            _valid_bounded_optional_scalar(item, limit=500)
            for item in value.values()
        )
    )


def _valid_repair_current_state(value: Any) -> bool:
    if (
        not isinstance(value, dict)
        or set(value)
        != {
            "generation",
            "target_workspace_state_paths",
            "changed_files",
        }
        or (
            value.get("generation") is not None
            and (
                not isinstance(value.get("generation"), int)
                or isinstance(value.get("generation"), bool)
            )
        )
    ):
        return False
    paths = value.get("target_workspace_state_paths")
    changed_files = value.get("changed_files")
    if (
        not isinstance(paths, list)
        or len(paths) > 8
        or any(not _valid_repair_relative_path(path) for path in paths)
        or not isinstance(changed_files, list)
        or len(changed_files) > 8
    ):
        return False
    allowed_file_keys = {
        "path",
        "current_exists",
        "current_sha256",
        "expected_sha256_after",
    }
    for changed_file in changed_files:
        if (
            not isinstance(changed_file, dict)
            or "path" not in changed_file
            or not set(changed_file).issubset(allowed_file_keys)
            or not _valid_repair_relative_path(changed_file["path"])
            or (
                "current_exists" in changed_file
                and not isinstance(changed_file["current_exists"], bool)
            )
        ):
            return False
        for key in ("current_sha256", "expected_sha256_after"):
            digest = changed_file.get(key)
            if digest is not None and (
                not isinstance(digest, str)
                or not re.fullmatch(r"(?:sha256:)?[0-9a-f]{64}", digest)
            ):
                return False
    return True


def _valid_repair_relative_path(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.replace("\\", "/")
    return bool(
        normalized
        and len(normalized) <= 300
        and not normalized.startswith("/")
        and not re.match(r"^[A-Za-z]:/", normalized)
        and all(part not in {"", ".", ".."} for part in normalized.split("/"))
    )


def _valid_bounded_string_list(
    value: Any,
    *,
    count: int,
    item_limit: int,
) -> bool:
    return (
        isinstance(value, list)
        and len(value) <= count
        and all(
            isinstance(item, str) and len(item) <= item_limit
            for item in value
        )
    )


def _valid_bounded_optional_scalar(value: Any, *, limit: int) -> bool:
    return value is None or (
        isinstance(value, (str, bool, int, float))
        and not isinstance(value, complex)
        and (not isinstance(value, str) or len(value) <= limit)
    )


def effective_planning_task_text(task: str) -> str:
    """Return the validated human task used by planning and heuristics.

    Server-owned proposal and repair envelopes remain available as the plan's
    source task for Coder evidence, but their structured metadata must not
    inflate target inference or Architect prompts.
    """

    repair_original = trusted_evidence_guided_repair_original_task(task)
    if repair_original is not None:
        return repair_original
    proposal = parse_bounded_proposal_task(task)
    if proposal is None:
        return (task or "").strip()
    if proposal.task:
        return proposal.task
    before = _text_before_proposal_marker(task)
    if before.strip():
        return before.strip()
    if proposal.target_file:
        return f"Target file: {proposal.target_file}"
    return ""


def bounded_proposal_create_allowed(
    proposal: BoundedProposal,
    *,
    workspace_root: Path,
) -> tuple[bool, str]:
    if proposal.mode != "proposal":
        return False, "readonly_mode"
    target = normalize_repo_path_candidate(proposal.target_file)
    if not target:
        return False, "missing_target_file"
    if not proposal.allowed_files:
        return False, "missing_allowed_files"
    if target not in proposal.allowed_files:
        return False, "target_not_in_allowed_files"
    if path_matches_forbidden(target, proposal.forbidden_files):
        return False, "target_forbidden"
    if path_escapes_workspace(target, workspace_root=workspace_root):
        return False, "path_escape"
    unsafe = unsafe_target_finding(target, workspace_root=workspace_root)
    if unsafe is not None:
        return False, unsafe.reason_code
    root = workspace_root.resolve()
    target_abs = (root / target).resolve()
    if not _is_relative_to(target_abs, root):
        return False, "outside_workspace"
    if target_abs.is_file():
        return False, "target_already_exists"
    parent = target_abs.parent
    if parent != root and not parent.exists():
        try:
            parent.relative_to(root)
        except ValueError:
            return False, "invalid_parent_directory"
    return True, ""


def merge_proposal_forbidden_paths(
    proposal: BoundedProposal,
    *,
    context_defaults: list[str] | tuple[str, ...],
) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for path in (*proposal.forbidden_files, *context_defaults):
        normalized = normalize_repo_path_candidate(str(path))
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        merged.append(normalized)
    return merged


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
