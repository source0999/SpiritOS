from __future__ import annotations

import difflib
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from source_proxy.decision.tool_actions import SourceProxyAction, SourceProxyActionResult
from source_proxy.safety.paths import normalize_repo_path_candidate, unsafe_target_finding


ActionExecutionStatus = Literal["completed", "blocked", "failed"]

DEFAULT_OUTPUT_LIMIT_BYTES = 12_000
DEFAULT_SEARCH_RESULT_LIMIT = 50
DEFAULT_RUN_TIMEOUT_SECONDS = 10

SAFE_RUNCHECK_COMMANDS = {
    ("git", "diff", "--check"),
    ("git", "status", "--short"),
    ("python", "-m", "py_compile"),
    ("python3", "-m", "py_compile"),
}

UNSAFE_COMMAND_MARKERS = (
    "&&",
    "||",
    ";",
    "|",
    ">",
    "<",
    "`",
    "$(",
    "&",
    "curl",
    "wget",
    "nc ",
    "netcat",
    "Start-Process",
    "nohup",
    "setsid",
)


@dataclass(frozen=True)
class ToolActionWorkspaceContract:
    workspace_root: Path
    allowed_files: tuple[str, ...] = ()
    forbidden_files: tuple[str, ...] = ()
    protected_paths: tuple[str, ...] = ()
    approval_level: str = "disposable_workspace"
    network_allowed: bool = False
    output_limit_bytes: int = DEFAULT_OUTPUT_LIMIT_BYTES
    search_result_limit: int = DEFAULT_SEARCH_RESULT_LIMIT
    run_timeout_seconds: int = DEFAULT_RUN_TIMEOUT_SECONDS

    def normalized_allowed_files(self) -> set[str]:
        return {
            normalize_repo_path_candidate(path)
            for path in self.allowed_files
            if normalize_repo_path_candidate(path)
        }

    def normalized_forbidden_files(self) -> set[str]:
        return {
            normalize_repo_path_candidate(path)
            for path in (*self.forbidden_files, *self.protected_paths)
            if normalize_repo_path_candidate(path)
        }


@dataclass(frozen=True)
class WorkspaceStatus:
    file_count: int
    files: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"file_count": self.file_count, "files": list(self.files)}


@dataclass(frozen=True)
class ToolActionExecutionReceipt:
    action_id: str
    action_type: str
    status: ActionExecutionStatus
    workspace_root: str
    target: str
    before_status: WorkspaceStatus
    after_status: WorkspaceStatus
    files_touched: tuple[str, ...] = ()
    diff_summary: str = ""
    stdout: str = ""
    stderr: str = ""
    blocked_reason: str = ""
    error_code: str = ""
    adapter_source: str = "generic"

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "status": self.status,
            "workspace_root": self.workspace_root,
            "target": self.target,
            "before_status": self.before_status.to_dict(),
            "after_status": self.after_status.to_dict(),
            "files_touched": list(self.files_touched),
            "diff_summary": self.diff_summary,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "blocked_reason": self.blocked_reason,
            "error_code": self.error_code,
            "adapter_source": self.adapter_source,
        }


@dataclass(frozen=True)
class ToolActionExecution:
    result: SourceProxyActionResult
    receipt: ToolActionExecutionReceipt

    def to_dict(self) -> dict[str, Any]:
        return {"result": self.result.to_dict(), "receipt": self.receipt.to_dict()}


@dataclass(frozen=True)
class _ResolvedTarget:
    repo_path: str
    path: Path


def execute_tool_action(
    action: SourceProxyAction,
    contract: ToolActionWorkspaceContract,
) -> ToolActionExecution:
    before = workspace_status(contract.workspace_root)
    if action.action_type == "RunCheck":
        return _execute_run_check(action, contract, before)
    try:
        resolved = _resolve_target(action, contract, require_allowed=action.action_type in {"WriteFile", "EditFile", "MultiEdit"})
    except _BlockedAction as blocked:
        return _blocked_execution(action, contract, before, before, blocked.code, blocked.message)

    if action.action_type == "WriteFile":
        return _execute_write_file(action, contract, resolved, before)
    if action.action_type == "EditFile":
        return _execute_edit_file(action, contract, resolved, before)
    if action.action_type == "MultiEdit":
        return _execute_multi_edit(action, contract, resolved, before)
    if action.action_type == "ReadFile":
        return _execute_read_file(action, contract, resolved, before)
    if action.action_type == "ListFiles":
        return _execute_list_files(action, contract, resolved, before)
    if action.action_type == "SearchRepo":
        return _execute_search_repo(action, contract, resolved, before)
    if action.action_type in {"AskClarification", "ReturnFinal"}:
        return _completed_execution(
            action,
            contract,
            resolved,
            before,
            before,
            observation=str(action.arguments.get("message") or action.arguments.get("question") or action.reason),
        )
    return _blocked_execution(
        action,
        contract,
        before,
        before,
        "unsupported_action_type",
        f"Unsupported action type: {action.action_type}",
    )


def workspace_status(workspace_root: Path) -> WorkspaceStatus:
    root = workspace_root.resolve()
    files: list[str] = []
    if root.exists():
        for path in root.rglob("*"):
            if path.is_file() and not path.is_symlink():
                files.append(path.relative_to(root).as_posix())
    return WorkspaceStatus(file_count=len(files), files=tuple(sorted(files)))


def _execute_write_file(
    action: SourceProxyAction,
    contract: ToolActionWorkspaceContract,
    resolved: _ResolvedTarget,
    before: WorkspaceStatus,
) -> ToolActionExecution:
    content = action.arguments.get("content")
    if not isinstance(content, str):
        return _blocked_execution(action, contract, before, before, "content_required", "WriteFile requires string content.")
    old = _read_text_if_exists(resolved.path)
    resolved.path.parent.mkdir(parents=True, exist_ok=True)
    resolved.path.write_text(content, encoding="utf-8")
    after = workspace_status(contract.workspace_root)
    diff = _unified_diff(resolved.repo_path, old, content)
    return _completed_execution(action, contract, resolved, before, after, files_touched=(resolved.repo_path,), diff_summary=diff)


def _execute_edit_file(
    action: SourceProxyAction,
    contract: ToolActionWorkspaceContract,
    resolved: _ResolvedTarget,
    before: WorkspaceStatus,
) -> ToolActionExecution:
    old_fragment = action.arguments.get("old")
    new_fragment = action.arguments.get("new")
    if not isinstance(old_fragment, str) or not isinstance(new_fragment, str):
        return _blocked_execution(action, contract, before, before, "content_required", "EditFile requires old and new strings.")
    old = _read_text_if_exists(resolved.path)
    if old_fragment not in old:
        return _failed_execution(action, contract, resolved, before, before, "edit_match_not_found", "EditFile old fragment was not found.")
    new = old.replace(old_fragment, new_fragment, 1)
    resolved.path.write_text(new, encoding="utf-8")
    after = workspace_status(contract.workspace_root)
    diff = _unified_diff(resolved.repo_path, old, new)
    return _completed_execution(action, contract, resolved, before, after, files_touched=(resolved.repo_path,), diff_summary=diff)


def _execute_multi_edit(
    action: SourceProxyAction,
    contract: ToolActionWorkspaceContract,
    resolved: _ResolvedTarget,
    before: WorkspaceStatus,
) -> ToolActionExecution:
    edits = action.arguments.get("edits")
    if not isinstance(edits, list):
        return _blocked_execution(action, contract, before, before, "content_required", "MultiEdit requires an edits list.")
    old = _read_text_if_exists(resolved.path)
    new = old
    for edit in edits:
        if not isinstance(edit, dict) or not isinstance(edit.get("old"), str) or not isinstance(edit.get("new"), str):
            return _blocked_execution(action, contract, before, before, "content_required", "Each MultiEdit item requires old and new strings.")
        if edit["old"] not in new:
            return _failed_execution(action, contract, resolved, before, before, "edit_match_not_found", "MultiEdit old fragment was not found.")
        new = new.replace(edit["old"], edit["new"], 1)
    resolved.path.write_text(new, encoding="utf-8")
    after = workspace_status(contract.workspace_root)
    diff = _unified_diff(resolved.repo_path, old, new)
    return _completed_execution(action, contract, resolved, before, after, files_touched=(resolved.repo_path,), diff_summary=diff)


def _execute_read_file(
    action: SourceProxyAction,
    contract: ToolActionWorkspaceContract,
    resolved: _ResolvedTarget,
    before: WorkspaceStatus,
) -> ToolActionExecution:
    if not resolved.path.is_file():
        return _failed_execution(action, contract, resolved, before, before, "target_not_found", "ReadFile target was not found.")
    text = resolved.path.read_text(encoding="utf-8", errors="replace")
    after = workspace_status(contract.workspace_root)
    return _completed_execution(
        action,
        contract,
        resolved,
        before,
        after,
        stdout=_limit_output(text, contract.output_limit_bytes),
    )


def _execute_list_files(
    action: SourceProxyAction,
    contract: ToolActionWorkspaceContract,
    resolved: _ResolvedTarget,
    before: WorkspaceStatus,
) -> ToolActionExecution:
    if not resolved.path.exists():
        return _failed_execution(action, contract, resolved, before, before, "target_not_found", "ListFiles target was not found.")
    files = []
    for path in resolved.path.rglob("*") if resolved.path.is_dir() else [resolved.path]:
        if path.is_file() and not _is_protected_repo_path(path.relative_to(contract.workspace_root.resolve()).as_posix(), contract):
            files.append(path.relative_to(contract.workspace_root.resolve()).as_posix())
    after = workspace_status(contract.workspace_root)
    return _completed_execution(action, contract, resolved, before, after, stdout=_limit_output("\n".join(sorted(files)), contract.output_limit_bytes))


def _execute_search_repo(
    action: SourceProxyAction,
    contract: ToolActionWorkspaceContract,
    resolved: _ResolvedTarget,
    before: WorkspaceStatus,
) -> ToolActionExecution:
    query = str(action.arguments.get("query") or action.arguments.get("pattern") or "").strip()
    if not query:
        return _blocked_execution(action, contract, before, before, "content_required", "SearchRepo requires a query.")
    results: list[str] = []
    root = contract.workspace_root.resolve()
    search_root = resolved.path if resolved.path.exists() else root
    for path in search_root.rglob("*") if search_root.is_dir() else [search_root]:
        if len(results) >= contract.search_result_limit:
            break
        if not path.is_file() or path.is_symlink():
            continue
        repo_path = path.relative_to(root).as_posix()
        if _is_protected_repo_path(repo_path, contract):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if query in line:
                results.append(f"{repo_path}:{line_number}:{line}")
                if len(results) >= contract.search_result_limit:
                    break
    after = workspace_status(contract.workspace_root)
    return _completed_execution(action, contract, resolved, before, after, stdout=_limit_output("\n".join(results), contract.output_limit_bytes))


def _execute_run_check(
    action: SourceProxyAction,
    contract: ToolActionWorkspaceContract,
    before: WorkspaceStatus,
) -> ToolActionExecution:
    command = str(action.arguments.get("command") or "").strip()
    if not command:
        return _blocked_execution(action, contract, before, before, "content_required", "RunCheck requires a command.")
    blocked = _blocked_command_reason(command, contract)
    if blocked:
        return _blocked_execution(action, contract, before, before, blocked[0], blocked[1])
    args = shlex.split(command, posix=os.name != "nt")
    run_args = [sys.executable, *args[1:]] if args[0] in {"python", "python3"} else args
    try:
        completed = subprocess.run(
            run_args,
            cwd=contract.workspace_root.resolve(),
            shell=False,
            text=True,
            capture_output=True,
            timeout=contract.run_timeout_seconds,
            check=False,
        )
    except FileNotFoundError as error:
        return _blocked_execution(action, contract, before, before, "unsafe_command", str(error))
    except subprocess.TimeoutExpired as error:
        after = workspace_status(contract.workspace_root)
        return _execution(
            action,
            contract,
            _ResolvedTarget(".", contract.workspace_root.resolve()),
            before,
            after,
            status="blocked",
            stdout=_limit_output(error.stdout or "", contract.output_limit_bytes),
            stderr=_limit_output(error.stderr or "", contract.output_limit_bytes),
            error_code="run_check_timeout",
            blocked_reason="RunCheck timed out.",
        )
    after = workspace_status(contract.workspace_root)
    status: ActionExecutionStatus = "completed" if completed.returncode == 0 else "failed"
    return _execution(
        action,
        contract,
        _ResolvedTarget(".", contract.workspace_root.resolve()),
        before,
        after,
        status=status,
        stdout=_limit_output(completed.stdout, contract.output_limit_bytes),
        stderr=_limit_output(completed.stderr, contract.output_limit_bytes),
        error_code="" if completed.returncode == 0 else "run_check_failed",
        blocked_reason="" if completed.returncode == 0 else f"RunCheck exited {completed.returncode}.",
    )


def _resolve_target(
    action: SourceProxyAction,
    contract: ToolActionWorkspaceContract,
    *,
    require_allowed: bool,
) -> _ResolvedTarget:
    repo_path = normalize_repo_path_candidate(action.target or str(action.arguments.get("path") or "."))
    if not repo_path:
        raise _BlockedAction("target_required", "Action target is required.")
    if repo_path != "." and unsafe_target_finding(repo_path, workspace_root=contract.workspace_root) is not None:
        raise _BlockedAction("path_escape", "Action target is unsafe or protected.")
    if _is_protected_repo_path(repo_path, contract):
        raise _BlockedAction("protected_path", "Action target is protected or forbidden.")
    if require_allowed and not _is_allowed_repo_path(repo_path, action, contract):
        raise _BlockedAction("target_not_allowed", "Action target is outside the allowed file snapshot.")
    root = contract.workspace_root.resolve()
    candidate = root / repo_path
    parent = candidate.parent if not candidate.exists() else candidate.parent
    _assert_inside_workspace(parent.resolve(), root)
    resolved_candidate = candidate.resolve() if candidate.exists() else parent.resolve() / candidate.name
    _assert_inside_workspace(resolved_candidate, root)
    if candidate.exists() and candidate.is_symlink():
        raise _BlockedAction("symlink_escape", "Action target cannot be a symlink.")
    return _ResolvedTarget(repo_path=repo_path, path=resolved_candidate)


def _blocked_command_reason(command: str, contract: ToolActionWorkspaceContract) -> tuple[str, str] | None:
    lowered = f" {command.lower()} "
    if not contract.network_allowed and any(marker in lowered for marker in (" curl ", " wget ", " nc ", " netcat ")):
        return "network_blocked", "RunCheck network commands are blocked."
    if any(marker in command for marker in UNSAFE_COMMAND_MARKERS):
        return "unsafe_command", "RunCheck command uses shell, redirection, network, or background syntax."
    try:
        args = shlex.split(command, posix=os.name != "nt")
    except ValueError as error:
        return "unsafe_command", str(error)
    if not args:
        return "content_required", "RunCheck requires a command."
    if not any(tuple(args[: len(prefix)]) == prefix for prefix in SAFE_RUNCHECK_COMMANDS):
        return "unsafe_command", "RunCheck command is not allowlisted."
    return None


def _is_allowed_repo_path(repo_path: str, action: SourceProxyAction, contract: ToolActionWorkspaceContract) -> bool:
    contract_allowed = set(contract.normalized_allowed_files())
    if contract_allowed:
        allowed = contract_allowed
    else:
        allowed = {
            normalize_repo_path_candidate(path)
            for path in action.allowed_files_snapshot
            if normalize_repo_path_candidate(path)
        }
    return bool(allowed) and normalize_repo_path_candidate(repo_path) in allowed


def _is_protected_repo_path(repo_path: str, contract: ToolActionWorkspaceContract) -> bool:
    normalized = normalize_repo_path_candidate(repo_path)
    if normalized == ".":
        return False
    if normalized in contract.normalized_forbidden_files():
        return True
    return unsafe_target_finding(normalized, workspace_root=contract.workspace_root) is not None


def _assert_inside_workspace(candidate: Path, root: Path) -> None:
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise _BlockedAction("path_escape", "Resolved path escapes workspace root.") from exc


def _read_text_if_exists(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _unified_diff(repo_path: str, old: str, new: str) -> str:
    return "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{repo_path}",
            tofile=f"b/{repo_path}",
        )
    )


def _limit_output(text: str, limit: int) -> str:
    encoded = text.encode("utf-8", errors="replace")
    if len(encoded) <= limit:
        return text
    return encoded[:limit].decode("utf-8", errors="replace") + "\n[output truncated]"


def _blocked_execution(
    action: SourceProxyAction,
    contract: ToolActionWorkspaceContract,
    before: WorkspaceStatus,
    after: WorkspaceStatus,
    error_code: str,
    message: str,
) -> ToolActionExecution:
    return _execution(action, contract, _ResolvedTarget(action.target or "", contract.workspace_root.resolve()), before, after, status="blocked", error_code=error_code, blocked_reason=message)


def _failed_execution(
    action: SourceProxyAction,
    contract: ToolActionWorkspaceContract,
    resolved: _ResolvedTarget,
    before: WorkspaceStatus,
    after: WorkspaceStatus,
    error_code: str,
    message: str,
) -> ToolActionExecution:
    return _execution(action, contract, resolved, before, after, status="failed", error_code=error_code, blocked_reason=message)


def _completed_execution(
    action: SourceProxyAction,
    contract: ToolActionWorkspaceContract,
    resolved: _ResolvedTarget,
    before: WorkspaceStatus,
    after: WorkspaceStatus,
    *,
    files_touched: tuple[str, ...] = (),
    diff_summary: str = "",
    stdout: str = "",
    stderr: str = "",
    observation: str = "",
) -> ToolActionExecution:
    return _execution(action, contract, resolved, before, after, status="completed", files_touched=files_touched, diff_summary=diff_summary, stdout=stdout, stderr=stderr, observation=observation)


def _execution(
    action: SourceProxyAction,
    contract: ToolActionWorkspaceContract,
    resolved: _ResolvedTarget,
    before: WorkspaceStatus,
    after: WorkspaceStatus,
    *,
    status: ActionExecutionStatus,
    files_touched: tuple[str, ...] = (),
    diff_summary: str = "",
    stdout: str = "",
    stderr: str = "",
    observation: str = "",
    error_code: str = "",
    blocked_reason: str = "",
) -> ToolActionExecution:
    receipt = ToolActionExecutionReceipt(
        action_id=action.action_id,
        action_type=action.action_type,
        status=status,
        workspace_root=str(contract.workspace_root.resolve()),
        target=resolved.repo_path,
        before_status=before,
        after_status=after,
        files_touched=files_touched,
        diff_summary=diff_summary,
        stdout=stdout,
        stderr=stderr,
        blocked_reason=blocked_reason,
        error_code=error_code,
        adapter_source=action.adapter_source,
    )
    result = SourceProxyActionResult(
        action_id=action.action_id,
        status=status,
        blocked_reason=blocked_reason,
        files_touched=list(files_touched),
        diff_summary=diff_summary,
        stdout=stdout,
        stderr=stderr,
        observation=observation,
        adapter_source=action.adapter_source,
        error_code=error_code,
    )
    return ToolActionExecution(result=result, receipt=receipt)


@dataclass(frozen=True)
class _BlockedAction(Exception):
    code: str
    message: str
