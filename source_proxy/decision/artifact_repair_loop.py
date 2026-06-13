from __future__ import annotations

import hashlib
import traceback
from pathlib import Path
from typing import Any, Callable

from source_proxy.decision.artifact_repair_contract import build_repair_prompt_from_failure_packet
from source_proxy.decision.tool_action_executor import ToolActionWorkspaceContract, execute_tool_action
from source_proxy.decision.tool_actions import parse_model_actions


RepairCall = Callable[[dict[str, Any], str, int], str]


def run_limited_artifact_repair_loop(
    *,
    failure_packet: dict[str, Any],
    repair_call: RepairCall,
    max_attempts: int | None = None,
    model_id: str = "local-repair-worker",
) -> dict[str, Any]:
    if failure_packet.get("handoff_required"):
        return _handoff("input_packet_requires_handoff", [], failure_packet)

    allowed_workspace = Path(str(failure_packet.get("allowed_workspace") or "")).resolve()
    if not allowed_workspace:
        return _handoff("allowed_workspace_missing", [], failure_packet)

    allowed_files = _allowed_files_from_packet(failure_packet, allowed_workspace)
    if not allowed_files:
        return _handoff("allowed_artifact_files_missing", [], failure_packet)

    attempts_allowed = max_attempts if max_attempts is not None else int(failure_packet.get("max_attempts_hint") or 1)
    prior_attempts = int(failure_packet.get("attempt_count") or 0)
    if attempts_allowed <= 0 or prior_attempts >= attempts_allowed:
        return _handoff("attempt_limit_reached", [], failure_packet)

    contract = ToolActionWorkspaceContract(
        workspace_root=allowed_workspace,
        allowed_files=tuple(allowed_files),
        allowed_file_extensions=(".html", ".css", ".js"),
        forbidden_files=tuple(failure_packet.get("forbidden_paths") or ()),
        approval_level="disposable_workspace",
        model_may_choose_paths=True,
        max_file_count=max(len(allowed_files) + 4, 4),
        network_allowed=False,
        run_timeout_seconds=10,
    )
    repair_prompt = build_repair_prompt_from_failure_packet(failure_packet)
    attempts: list[dict[str, Any]] = []

    for index in range(prior_attempts, attempts_allowed):
        try:
            raw_transcript = repair_call(failure_packet, repair_prompt, index)
        except Exception as error:  # pragma: no cover - traceback content varies by runtime.
            attempts.append(
                _attempt_record(
                    attempt_index=index,
                    raw_transcript="",
                    parse_result={"ok": False, "error_code": "repair_worker_failed"},
                    executions=[],
                    reason_codes=["repair_worker_failed"],
                    error=str(error),
                    traceback_text=traceback.format_exc(limit=3),
                )
            )
            return _handoff("repair_worker_failed", attempts, failure_packet)

        parse_result = parse_model_actions(
            raw_transcript,
            model_id=model_id,
            source_message_id=f"artifact-repair-attempt-{index + 1}",
            allowed_files_snapshot=[],
            adapter_source="artifact_repair_loop",
        )
        executions = []
        if parse_result.ok:
            for action in parse_result.actions:
                executions.append(execute_tool_action(action, contract).to_dict())

        reason_codes = _attempt_reason_codes(parse_result.to_dict(), executions)
        attempts.append(
            _attempt_record(
                attempt_index=index,
                raw_transcript=raw_transcript,
                parse_result=parse_result.to_dict(),
                executions=executions,
                reason_codes=reason_codes,
            )
        )

        if parse_result.ok and executions and all(item["result"]["status"] == "completed" for item in executions):
            return {
                "status": "READY_FOR_RETEST",
                "handoff_required": False,
                "handoff_reason": "",
                "attempts_used": len(attempts),
                "allowed_workspace": str(allowed_workspace),
                "allowed_files": allowed_files,
                "attempts": attempts,
                "repair_attempts": len(attempts),
                "changed_files": _changed_files(attempts),
                "repaired_files": _changed_files(attempts),
                "repair_model_authored_targets": _model_authored_targets(attempts),
                "repair_model_authored_content_hashes": _model_authored_content_hashes(attempts),
                "file_equals_model_action_content": _file_equals_model_action_content(attempts, allowed_workspace),
                "bytes_written_match_model_authored_content": _file_equals_model_action_content(attempts, allowed_workspace),
                "parse_decisions": _parse_decisions(attempts),
                "rejected_repair_transcripts": _rejected_transcripts(attempts),
                "valid_repaired_targets": _changed_files(attempts),
                "diffs": _diffs(attempts),
                "reason_codes": sorted(set(reason for attempt in attempts for reason in attempt["reason_codes"])),
            }

        if any(item["result"]["status"] == "blocked" for item in executions):
            return _handoff("unsafe_or_blocked_repair_output", attempts, failure_packet)

    return _handoff("repair_attempts_exhausted", attempts, failure_packet)


def _allowed_files_from_packet(packet: dict[str, Any], allowed_workspace: Path) -> list[str]:
    allowed: list[str] = []
    workspace = allowed_workspace.resolve()
    raw_paths = [
        *list(packet.get("artifact_paths") or []),
        *list(packet.get("generated_files") or []),
        *list(packet.get("model_authored_targets") or []),
    ]
    for raw_path in raw_paths:
        raw = Path(str(raw_path))
        path = raw if raw.is_absolute() else workspace / raw
        try:
            repo_path = path.resolve().relative_to(workspace).as_posix()
        except (OSError, ValueError):
            continue
        if repo_path and repo_path not in allowed and Path(repo_path).suffix.lower() in {".html", ".htm", ".css", ".js"}:
            allowed.append(repo_path)
    return allowed


def _attempt_reason_codes(parse_result: dict[str, Any], executions: list[dict[str, Any]]) -> list[str]:
    reasons: list[str] = []
    if not parse_result.get("ok"):
        reasons.append(str(parse_result.get("error_code") or "malformed_repair_output"))
    for execution in executions:
        result = execution.get("result") or {}
        if result.get("error_code"):
            reasons.append(str(result["error_code"]))
        if result.get("status") == "blocked":
            reasons.append("repair_action_blocked")
        if result.get("status") == "failed":
            reasons.append("repair_action_failed")
    return sorted(set(reason for reason in reasons if reason))


def _attempt_record(
    *,
    attempt_index: int,
    raw_transcript: str,
    parse_result: dict[str, Any],
    executions: list[dict[str, Any]],
    reason_codes: list[str],
    error: str = "",
    traceback_text: str = "",
) -> dict[str, Any]:
    return {
        "attempt_index": attempt_index,
        "raw_transcript": raw_transcript,
        "parse_result": parse_result,
        "executions": executions,
        "reason_codes": reason_codes,
        "error": error,
        "traceback": traceback_text,
        "changed_files": [
            path
            for execution in executions
            for path in ((execution.get("result") or {}).get("files_touched") or [])
        ],
        "diffs": [
            str((execution.get("result") or {}).get("diff_summary") or "")
            for execution in executions
            if (execution.get("result") or {}).get("diff_summary")
        ],
    }


def _handoff(reason: str, attempts: list[dict[str, Any]], packet: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "HANDOFF",
        "handoff_required": True,
        "handoff_reason": reason,
        "attempts_used": len(attempts),
        "allowed_workspace": str(packet.get("allowed_workspace") or ""),
        "allowed_files": [],
        "attempts": attempts,
        "repair_attempts": len(attempts),
        "changed_files": _changed_files(attempts),
        "repaired_files": _changed_files(attempts),
        "repair_model_authored_targets": _model_authored_targets(attempts),
        "repair_model_authored_content_hashes": _model_authored_content_hashes(attempts),
        "file_equals_model_action_content": False if attempts else None,
        "bytes_written_match_model_authored_content": False if attempts else None,
        "parse_decisions": _parse_decisions(attempts),
        "rejected_repair_transcripts": _rejected_transcripts(attempts),
        "valid_repaired_targets": _changed_files(attempts),
        "diffs": _diffs(attempts),
        "reason_codes": sorted(set([reason, *[item for attempt in attempts for item in attempt["reason_codes"]]])),
    }


def _changed_files(attempts: list[dict[str, Any]]) -> list[str]:
    return sorted(set(path for attempt in attempts for path in attempt["changed_files"]))


def _diffs(attempts: list[dict[str, Any]]) -> list[str]:
    return [diff for attempt in attempts for diff in attempt["diffs"]]


def _parse_decisions(attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        decision
        for attempt in attempts
        for decision in ((attempt.get("parse_result") or {}).get("decisions") or [])
    ]


def _rejected_transcripts(attempts: list[dict[str, Any]]) -> list[str]:
    return [
        str(attempt.get("raw_transcript") or "")
        for attempt in attempts
        if not (attempt.get("parse_result") or {}).get("ok")
    ]


def _model_authored_targets(attempts: list[dict[str, Any]]) -> list[str]:
    targets: set[str] = set()
    for attempt in attempts:
        parse_result = attempt.get("parse_result") or {}
        for action in parse_result.get("actions") or []:
            if action.get("action_type") == "WriteFile" and action.get("target"):
                targets.add(str(action["target"]))
    return sorted(targets)


def _model_authored_content_hashes(attempts: list[dict[str, Any]]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for attempt in attempts:
        parse_result = attempt.get("parse_result") or {}
        for action in parse_result.get("actions") or []:
            arguments = action.get("arguments") or {}
            target = str(action.get("target") or "")
            content = arguments.get("content") if isinstance(arguments, dict) else None
            if action.get("action_type") == "WriteFile" and target and isinstance(content, str):
                hashes[target] = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return hashes


def _file_equals_model_action_content(attempts: list[dict[str, Any]], workspace: Path) -> bool:
    model_content: dict[str, str] = {}
    for attempt in attempts:
        parse_result = attempt.get("parse_result") or {}
        for action in parse_result.get("actions") or []:
            arguments = action.get("arguments") or {}
            target = str(action.get("target") or "")
            content = arguments.get("content") if isinstance(arguments, dict) else None
            if action.get("action_type") == "WriteFile" and target and isinstance(content, str):
                model_content[target] = content
    changed = _changed_files(attempts)
    if not changed:
        return False
    for repo_path in changed:
        path = workspace / repo_path
        if not path.is_file() or model_content.get(repo_path) != path.read_text(encoding="utf-8", errors="replace"):
            return False
    return True
