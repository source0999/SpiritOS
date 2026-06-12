from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

from source_proxy.decision.tool_action_executor import (
    ToolActionWorkspaceContract,
    execute_tool_action,
)
from source_proxy.decision.tool_actions import (
    SourceProxyAction,
    parse_model_actions,
    tool_contract,
)


LoopFinalState = Literal[
    "completed",
    "blocked",
    "failed_format",
    "failed_verification",
    "partial",
]

AUTHORITY_ERROR_CODES = {
    "target_not_allowed",
    "path_escape",
    "protected_path",
    "symlink_escape",
    "unsafe_command",
    "network_blocked",
}


@dataclass(frozen=True)
class BoundedAgentLoopRequest:
    task_spec: dict[str, Any]
    context_packet: dict[str, Any]
    workspace_contract: ToolActionWorkspaceContract
    model_id: str = ""
    adapter_source: str = "generic"
    source_message_id: str = "loop"
    recommended_checks: tuple[str, ...] = ()
    run_recommended_checks: bool = False
    verification_skip_reason: str = "verification_policy_not_allowed"
    max_format_retries: int = 1
    max_verification_repairs: int = 1


@dataclass(frozen=True)
class LoopModelCall:
    call_index: int
    packet: dict[str, Any]
    raw_transcript: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_index": self.call_index,
            "packet": self.packet,
            "raw_transcript": self.raw_transcript,
        }


@dataclass(frozen=True)
class LoopSkippedCheck:
    command: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {"command": self.command, "reason": self.reason}


@dataclass(frozen=True)
class BoundedAgentLoopReceipt:
    final_state: LoopFinalState
    raw_model_transcripts: tuple[str, ...]
    model_calls: tuple[LoopModelCall, ...]
    parse_results: tuple[dict[str, Any], ...]
    parsed_actions: tuple[dict[str, Any], ...]
    executions: tuple[dict[str, Any], ...]
    skipped_checks: tuple[LoopSkippedCheck, ...]
    diagnostics_packet: dict[str, Any]
    receipt_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "final_state": self.final_state,
            "raw_model_transcripts": list(self.raw_model_transcripts),
            "model_calls": [call.to_dict() for call in self.model_calls],
            "parse_results": list(self.parse_results),
            "parsed_actions": list(self.parsed_actions),
            "executions": list(self.executions),
            "skipped_checks": [check.to_dict() for check in self.skipped_checks],
            "diagnostics_packet": self.diagnostics_packet,
            "receipt_path": self.receipt_path,
        }


@dataclass(frozen=True)
class BoundedAgentLoopResult:
    final_state: LoopFinalState
    receipt: BoundedAgentLoopReceipt

    def to_dict(self) -> dict[str, Any]:
        return {"final_state": self.final_state, "receipt": self.receipt.to_dict()}


ModelCall = Callable[[dict[str, Any]], str]


def run_bounded_agent_loop(
    request: BoundedAgentLoopRequest,
    model_call: ModelCall,
    *,
    receipt_path: Path | None = None,
) -> BoundedAgentLoopResult:
    raw_transcripts: list[str] = []
    model_calls: list[LoopModelCall] = []
    parse_results: list[dict[str, Any]] = []
    parsed_actions: list[dict[str, Any]] = []
    executions: list[dict[str, Any]] = []
    skipped_checks: list[LoopSkippedCheck] = []
    observations: list[dict[str, Any]] = []
    format_retries = 0
    verification_repairs = 0
    final_state: LoopFinalState = "partial"

    max_calls = 1 + request.max_format_retries + request.max_verification_repairs
    for call_index in range(max_calls):
        packet = _model_packet(request, observations, call_index)
        raw = model_call(packet)
        raw_transcripts.append(raw)
        model_calls.append(LoopModelCall(call_index=call_index, packet=packet, raw_transcript=raw))

        parsed = parse_model_actions(
            raw,
            model_id=request.model_id,
            source_message_id=f"{request.source_message_id}:{call_index}",
            allowed_files_snapshot=request.workspace_contract.allowed_files,
            adapter_source=request.adapter_source,
        )
        parsed_dict = parsed.to_dict()
        parse_results.append(parsed_dict)
        parsed_actions.extend(action.to_dict() for action in parsed.actions)

        if not parsed.ok:
            observations.append({"type": "parse_error", "error_code": parsed.error_code, "repair_prompt": parsed.repair_prompt})
            if parsed.error_code in AUTHORITY_ERROR_CODES:
                final_state = "blocked"
                break
            if format_retries < request.max_format_retries:
                format_retries += 1
                continue
            final_state = "failed_format"
            break

        action_state, should_stop = _execute_actions(parsed.actions, request, executions, observations)
        if should_stop:
            final_state = action_state
            break

        check_state = _run_or_skip_checks(request, executions, observations, skipped_checks)
        if check_state == "completed":
            final_state = "completed"
            break
        if check_state == "skipped":
            final_state = "partial" if _has_productive_execution(executions) else "completed"
            break
        if check_state == "failed_verification":
            if verification_repairs < request.max_verification_repairs:
                verification_repairs += 1
                continue
            final_state = "failed_verification"
            break
        final_state = check_state
        break

    receipt = _build_receipt(
        request=request,
        final_state=final_state,
        raw_transcripts=raw_transcripts,
        model_calls=model_calls,
        parse_results=parse_results,
        parsed_actions=parsed_actions,
        executions=executions,
        skipped_checks=skipped_checks,
        receipt_path=receipt_path,
        format_retries=format_retries,
        verification_repairs=verification_repairs,
    )
    if receipt_path is not None:
        _write_receipt(receipt_path, receipt)
        receipt = _receipt_with_path(receipt, receipt_path)
    return BoundedAgentLoopResult(final_state=final_state, receipt=receipt)


def _execute_actions(
    actions: list[SourceProxyAction],
    request: BoundedAgentLoopRequest,
    executions: list[dict[str, Any]],
    observations: list[dict[str, Any]],
) -> tuple[LoopFinalState, bool]:
    for action in actions:
        execution = execute_tool_action(action, request.workspace_contract).to_dict()
        executions.append(execution)
        result = execution["result"]
        observations.append({"type": "action_result", "action_id": action.action_id, "result": result})
        if result["status"] == "blocked":
            return "blocked", True
        if result["status"] == "failed" and result.get("error_code") in AUTHORITY_ERROR_CODES:
            return "blocked", True
        if action.action_type == "AskClarification":
            return "blocked", True
        if action.action_type == "ReturnFinal":
            return ("completed" if not _has_failed_execution(executions) else "partial"), True
    return "partial", False


def _run_or_skip_checks(
    request: BoundedAgentLoopRequest,
    executions: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    skipped_checks: list[LoopSkippedCheck],
) -> LoopFinalState | Literal["skipped"]:
    if not request.recommended_checks:
        return "completed"
    if not request.run_recommended_checks:
        for command in request.recommended_checks:
            skipped = LoopSkippedCheck(command=command, reason=request.verification_skip_reason)
            skipped_checks.append(skipped)
            observations.append({"type": "check_skipped", **skipped.to_dict()})
        return "skipped"
    for index, command in enumerate(request.recommended_checks, start=1):
        action = SourceProxyAction(
            action_id=f"{request.source_message_id}:check:{index}",
            action_type="RunCheck",
            target=".",
            arguments={"command": command},
            reason="Recommended verification check.",
            requires_approval=True,
            model_id=request.model_id,
            source_message_id=request.source_message_id,
            allowed_files_snapshot=list(request.workspace_contract.allowed_files),
            created_at="",
            adapter_source=request.adapter_source,
        )
        execution = execute_tool_action(action, request.workspace_contract).to_dict()
        executions.append(execution)
        observations.append({"type": "verification_result", "command": command, "result": execution["result"]})
        if execution["result"]["status"] != "completed":
            return "failed_verification"
    return "completed"


def _model_packet(
    request: BoundedAgentLoopRequest,
    observations: list[dict[str, Any]],
    call_index: int,
) -> dict[str, Any]:
    return {
        "call_index": call_index,
        "task_spec": request.task_spec,
        "context_packet": request.context_packet,
        "tool_contract": tool_contract(),
        "observations": list(observations),
        "workspace_contract": {
            "workspace_root": str(request.workspace_contract.workspace_root.resolve()),
            "allowed_files": list(request.workspace_contract.allowed_files),
            "forbidden_files": list(request.workspace_contract.forbidden_files),
            "protected_paths": list(request.workspace_contract.protected_paths),
            "approval_level": request.workspace_contract.approval_level,
            "network_allowed": request.workspace_contract.network_allowed,
        },
        "loop_policy": {
            "max_format_retries": request.max_format_retries,
            "max_verification_repairs": request.max_verification_repairs,
            "run_recommended_checks": request.run_recommended_checks,
            "recommended_checks": list(request.recommended_checks),
        },
    }


def _build_receipt(
    *,
    request: BoundedAgentLoopRequest,
    final_state: LoopFinalState,
    raw_transcripts: list[str],
    model_calls: list[LoopModelCall],
    parse_results: list[dict[str, Any]],
    parsed_actions: list[dict[str, Any]],
    executions: list[dict[str, Any]],
    skipped_checks: list[LoopSkippedCheck],
    receipt_path: Path | None,
    format_retries: int,
    verification_repairs: int,
) -> BoundedAgentLoopReceipt:
    diagnostics_packet = {
        "model_id": request.model_id,
        "adapter_source": request.adapter_source,
        "final_state": final_state,
        "model_call_count": len(model_calls),
        "format_retries_used": format_retries,
        "verification_repairs_used": verification_repairs,
        "parsed_action_count": len(parsed_actions),
        "execution_count": len(executions),
        "blocked_reasons": [
            execution["result"].get("blocked_reason", "")
            for execution in executions
            if execution["result"].get("blocked_reason")
        ],
        "files_touched": sorted(
            {
                touched
                for execution in executions
                for touched in execution["result"].get("files_touched", [])
            }
        ),
        "skipped_checks": [check.to_dict() for check in skipped_checks],
    }
    return BoundedAgentLoopReceipt(
        final_state=final_state,
        raw_model_transcripts=tuple(raw_transcripts),
        model_calls=tuple(model_calls),
        parse_results=tuple(parse_results),
        parsed_actions=tuple(parsed_actions),
        executions=tuple(executions),
        skipped_checks=tuple(skipped_checks),
        diagnostics_packet=diagnostics_packet,
        receipt_path=str(receipt_path or ""),
    )


def _write_receipt(path: Path, receipt: BoundedAgentLoopReceipt) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _receipt_with_path(receipt: BoundedAgentLoopReceipt, path: Path) -> BoundedAgentLoopReceipt:
    return BoundedAgentLoopReceipt(
        final_state=receipt.final_state,
        raw_model_transcripts=receipt.raw_model_transcripts,
        model_calls=receipt.model_calls,
        parse_results=receipt.parse_results,
        parsed_actions=receipt.parsed_actions,
        executions=receipt.executions,
        skipped_checks=receipt.skipped_checks,
        diagnostics_packet=receipt.diagnostics_packet,
        receipt_path=str(path),
    )


def _has_failed_execution(executions: list[dict[str, Any]]) -> bool:
    return any(execution["result"]["status"] in {"failed", "blocked"} for execution in executions)


def _has_productive_execution(executions: list[dict[str, Any]]) -> bool:
    return any(execution["result"].get("files_touched") for execution in executions)
