from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from source_proxy.planning.plan import PLAN_SCHEMA_VERSION
from source_proxy.safety.paths import normalize_repo_path_candidate


ACTION_CONTRACT_VERSION = PLAN_SCHEMA_VERSION

ActionType = Literal[
    "ReadFile",
    "ListFiles",
    "SearchRepo",
    "WriteFile",
    "EditFile",
    "MultiEdit",
    "RunCheck",
    "AskClarification",
    "ReturnFinal",
]
ActionCapability = Literal["read", "write", "execute", "respond"]
ActionStatus = Literal["pending", "blocked", "completed", "failed"]

ERROR_CODES = {
    "empty_transcript",
    "invalid_json",
    "invalid_action_schema",
    "unsupported_action_type",
    "target_required",
    "target_not_allowed",
    "content_required",
    "bash_string_args_only_for_bash",
    "free_floating_code_no_path_action",
    "backend_authorship_rejected",
    "execution_blocked_until_plan_3",
}

TOOL_CAPABILITIES: dict[str, ActionCapability] = {
    "ReadFile": "read",
    "ListFiles": "read",
    "SearchRepo": "read",
    "WriteFile": "write",
    "EditFile": "write",
    "MultiEdit": "write",
    "RunCheck": "execute",
    "AskClarification": "respond",
    "ReturnFinal": "respond",
}

WRITE_ACTIONS = {"WriteFile", "EditFile", "MultiEdit"}
EXECUTE_ACTIONS = {"RunCheck"}
PLAN_3_BLOCKED_ACTIONS = WRITE_ACTIONS | EXECUTE_ACTIONS

_ACTION_ALIASES = {
    "read_file": "ReadFile",
    "list_files": "ListFiles",
    "search_repo": "SearchRepo",
    "write_file": "WriteFile",
    "replace_file": "WriteFile",
    "edit_file": "EditFile",
    "multi_edit": "MultiEdit",
    "run_check": "RunCheck",
    "bash": "RunCheck",
    "shell": "RunCheck",
    "ask_clarification": "AskClarification",
    "return_final": "ReturnFinal",
    "final": "ReturnFinal",
}


@dataclass(frozen=True)
class SourceProxyAction:
    action_id: str
    action_type: ActionType
    target: str
    arguments: dict[str, Any]
    reason: str
    requires_approval: bool
    model_id: str
    source_message_id: str
    allowed_files_snapshot: list[str]
    created_at: str
    adapter_source: str = "generic"
    schema_version: int = ACTION_CONTRACT_VERSION
    authorship: str = "model_authored"
    execution_state: str = "parser_only"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceProxyActionResult:
    action_id: str
    status: ActionStatus
    blocked_reason: str = ""
    files_touched: list[str] = field(default_factory=list)
    diff_summary: str = ""
    stdout: str = ""
    stderr: str = ""
    observation: str = ""
    receipt_path: str = ""
    adapter_source: str = "generic"
    schema_version: int = ACTION_CONTRACT_VERSION
    error_code: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActionParseDecision:
    parser: str
    status: Literal["accepted", "rejected", "skipped"]
    error_code: str = ""
    detail: str = ""
    action_id: str = ""
    adapter_source: str = "generic"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActionParseResult:
    raw_transcript: str
    actions: list[SourceProxyAction]
    decisions: list[ActionParseDecision]
    adapter_source: str = "generic"
    error_code: str = ""
    repair_prompt: str = ""

    @property
    def ok(self) -> bool:
        return bool(self.actions) and not self.error_code

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw_transcript": self.raw_transcript,
            "actions": [action.to_dict() for action in self.actions],
            "decisions": [decision.to_dict() for decision in self.decisions],
            "adapter_source": self.adapter_source,
            "error_code": self.error_code,
            "repair_prompt": self.repair_prompt,
            "ok": self.ok,
        }


def tool_contract() -> dict[str, Any]:
    return {
        "schema_version": ACTION_CONTRACT_VERSION,
        "tools": [
            {
                "action_type": action_type,
                "capability": capability,
                "execution_state": "blocked_until_plan_3"
                if action_type in PLAN_3_BLOCKED_ACTIONS
                else "parser_only",
            }
            for action_type, capability in TOOL_CAPABILITIES.items()
        ],
        "stable_error_codes": sorted(ERROR_CODES),
    }


def blocked_result_for_plan_2(action: SourceProxyAction) -> SourceProxyActionResult:
    if action.action_type not in PLAN_3_BLOCKED_ACTIONS:
        return SourceProxyActionResult(
            action_id=action.action_id,
            status="pending",
            observation="Action parsed only; no executor is attached in Plan 2.",
            adapter_source=action.adapter_source,
        )
    return SourceProxyActionResult(
        action_id=action.action_id,
        status="blocked",
        blocked_reason="Plan 2 defines parser contracts only. Execution starts in Plan 3.",
        files_touched=[],
        observation=f"{action.action_type} execution is blocked until Plan 3.",
        adapter_source=action.adapter_source,
        error_code="execution_blocked_until_plan_3",
    )


def parse_model_actions(
    raw_transcript: str,
    *,
    model_id: str = "",
    source_message_id: str = "",
    allowed_files_snapshot: list[str] | tuple[str, ...] | None = None,
    created_at: str = "",
    author: str = "model",
    adapter_source: str = "generic",
) -> ActionParseResult:
    raw = raw_transcript or ""
    decisions: list[ActionParseDecision] = []
    if author != "model":
        return _reject(
            raw,
            decisions,
            "backend_authorship_rejected",
            "Only model-authored action content may enter the Plan 2 parser.",
        )
    if not raw.strip():
        return _reject(raw, decisions, "empty_transcript", "Model transcript was empty.")

    context = _ParseContext(
        model_id=model_id,
        source_message_id=source_message_id,
        allowed_files_snapshot=list(allowed_files_snapshot or []),
        created_at=created_at,
        adapter_source=adapter_source or "generic",
    )
    for parser_name, parser in (
        ("strict_json", _parse_strict_json_actions),
        ("line_delimited_json", _parse_line_delimited_json_actions),
        ("aider_path_bound_edit", _parse_aider_path_bound_edits),
        ("path_content_block", _parse_path_content_blocks),
        ("markdown_path_content_block", _parse_markdown_path_content_blocks),
    ):
        actions, parser_decisions = parser(raw, context)
        decisions.extend(parser_decisions)
        if actions:
            return ActionParseResult(
                raw_transcript=raw,
                actions=actions,
                decisions=decisions,
                adapter_source=context.adapter_source,
            )

    if _looks_like_free_floating_code(raw):
        return _reject(
            raw,
            decisions,
            "free_floating_code_no_path_action",
            "Code-like output had no path-bound action or file block.",
        )
    contract_error = _highest_priority_rejection(decisions)
    if contract_error:
        return _reject(
            raw,
            decisions,
            contract_error,
            "Model transcript matched an action-like format but failed the action contract.",
        )
    return _reject(raw, decisions, "invalid_json", "No supported action format parsed.")


@dataclass(frozen=True)
class _ParseContext:
    model_id: str
    source_message_id: str
    allowed_files_snapshot: list[str]
    created_at: str
    adapter_source: str


def _parse_strict_json_actions(
    raw: str,
    context: _ParseContext,
) -> tuple[list[SourceProxyAction], list[ActionParseDecision]]:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        return [], [
            ActionParseDecision(
                parser="strict_json",
                status="rejected",
                error_code="invalid_json",
                detail=str(error),
            )
        ]
    specs = _json_action_specs(parsed)
    if specs is None:
        return [], [
            ActionParseDecision(
                parser="strict_json",
                status="rejected",
                error_code="invalid_action_schema",
                detail="JSON root must be an action object or actions list.",
            )
        ]
    return _actions_from_specs(specs, context, parser="strict_json")


def _parse_line_delimited_json_actions(
    raw: str,
    context: _ParseContext,
) -> tuple[list[SourceProxyAction], list[ActionParseDecision]]:
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(lines) < 2:
        return [], [
            ActionParseDecision(
                parser="line_delimited_json",
                status="skipped",
                detail="Transcript did not contain multiple JSON lines.",
            )
        ]
    specs: list[dict[str, Any]] = []
    decisions: list[ActionParseDecision] = []
    for line in lines:
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError as error:
            return [], [
                *decisions,
                ActionParseDecision(
                    parser="line_delimited_json",
                    status="rejected",
                    error_code="invalid_json",
                    detail=str(error),
                ),
            ]
        if not isinstance(parsed, dict):
            return [], [
                *decisions,
                ActionParseDecision(
                    parser="line_delimited_json",
                    status="rejected",
                    error_code="invalid_action_schema",
                    detail="Each JSON line must be an object.",
                ),
            ]
        specs.append(parsed)
    return _actions_from_specs(specs, context, parser="line_delimited_json")


def _parse_path_content_blocks(
    raw: str,
    context: _ParseContext,
) -> tuple[list[SourceProxyAction], list[ActionParseDecision]]:
    actions: list[SourceProxyAction] = []
    decisions: list[ActionParseDecision] = []
    for match in re.finditer(
        r"<file\s+path=[\"']([^\"']+)[\"']\s*>(.*?)</file>",
        raw,
        flags=re.DOTALL | re.IGNORECASE,
    ):
        target = normalize_repo_path_candidate(match.group(1))
        content = _trim_block_content(match.group(2))
        if not target:
            decisions.append(
                ActionParseDecision(
                    parser="path_content_block",
                    status="rejected",
                    error_code="target_required",
                    detail="File block path was empty or invalid.",
                    adapter_source=context.adapter_source,
                )
            )
            continue
        if not _target_allowed(target, context.allowed_files_snapshot):
            decisions.append(
                ActionParseDecision(
                    parser="path_content_block",
                    status="rejected",
                    error_code="target_not_allowed",
                    detail="File block target was outside the allowed file snapshot.",
                    adapter_source=context.adapter_source,
                )
            )
            continue
        if not content:
            decisions.append(
                ActionParseDecision(
                    parser="path_content_block",
                    status="rejected",
                    error_code="content_required",
                    detail="File block content was empty.",
                    adapter_source=context.adapter_source,
                )
            )
            continue
        actions.append(
            _build_action(
                {
                    "action_type": "WriteFile",
                    "target": target,
                    "arguments": {"content": content, "content_source": "path_content_block"},
                    "reason": "Model returned explicit path/content file block.",
                },
                context,
                index=len(actions),
            )
        )
    if actions:
        return actions, [
            *decisions,
            *[
                ActionParseDecision(
                    parser="path_content_block",
                    status="accepted",
                    action_id=action.action_id,
                    adapter_source=context.adapter_source,
                )
                for action in actions
            ],
        ]
    return [], [
        *decisions,
        ActionParseDecision(
            parser="path_content_block",
            status="rejected",
            error_code="invalid_action_schema",
            detail="No explicit <file path=\"...\"> block found.",
            adapter_source=context.adapter_source,
        ),
    ]


def _parse_markdown_path_content_blocks(
    raw: str,
    context: _ParseContext,
) -> tuple[list[SourceProxyAction], list[ActionParseDecision]]:
    actions: list[SourceProxyAction] = []
    decisions: list[ActionParseDecision] = []
    pattern = re.compile(
        r"(?P<prefix>(?:^|\n)[^\n]{0,240}?(?P<path>[A-Za-z0-9._/@()[\]-]+\.(?:html|htm|css|js|md|txt))[^\n]{0,240}?)"
        r"\n\s*```(?:[A-Za-z0-9_-]+)?\r?\n(?P<content>.*?)\r?\n```",
        flags=re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(raw):
        target = normalize_repo_path_candidate(match.group("path"))
        content = _trim_block_content(match.group("content"))
        if not target:
            decisions.append(
                ActionParseDecision(
                    parser="markdown_path_content_block",
                    status="rejected",
                    error_code="target_required",
                    detail="Markdown file block path was empty or invalid.",
                    adapter_source=context.adapter_source,
                )
            )
            continue
        if not _target_allowed(target, context.allowed_files_snapshot):
            decisions.append(
                ActionParseDecision(
                    parser="markdown_path_content_block",
                    status="rejected",
                    error_code="target_not_allowed",
                    detail="Markdown file block target was outside the allowed file snapshot.",
                    adapter_source=context.adapter_source,
                )
            )
            continue
        if not content:
            decisions.append(
                ActionParseDecision(
                    parser="markdown_path_content_block",
                    status="rejected",
                    error_code="content_required",
                    detail="Markdown file block content was empty.",
                    adapter_source=context.adapter_source,
                )
            )
            continue
        actions.append(
            _build_action(
                {
                    "action_type": "WriteFile",
                    "target": target,
                    "arguments": {
                        "content": content,
                        "content_source": "markdown_path_content_block",
                    },
                    "reason": "Model returned a markdown code block tied to an explicit file path.",
                },
                context,
                index=len(actions),
            )
        )
    if actions:
        return actions, [
            *decisions,
            *[
                ActionParseDecision(
                    parser="markdown_path_content_block",
                    status="accepted",
                    action_id=action.action_id,
                    adapter_source=context.adapter_source,
                )
                for action in actions
            ],
        ]
    return [], [
        *decisions,
        ActionParseDecision(
            parser="markdown_path_content_block",
            status="skipped",
            detail="No markdown code block was tied to an explicit file path.",
            adapter_source=context.adapter_source,
        ),
    ]


def _parse_aider_path_bound_edits(
    raw: str,
    context: _ParseContext,
) -> tuple[list[SourceProxyAction], list[ActionParseDecision]]:
    actions: list[SourceProxyAction] = []
    decisions: list[ActionParseDecision] = []
    pattern = re.compile(
        r"(?:^|\n)\s*(?:path|file)\s*:\s*(?P<path>[^\r\n]+)\s*"
        r"(?:\r?\n)+<<<<<<< SEARCH\r?\n"
        r"(?P<old>.*?)\r?\n=======\r?\n"
        r"(?P<new>.*?)\r?\n>>>>>>> REPLACE",
        flags=re.DOTALL | re.IGNORECASE,
    )
    for match in pattern.finditer(raw):
        target = normalize_repo_path_candidate(match.group("path"))
        old = _trim_block_content(match.group("old"))
        new = _trim_block_content(match.group("new"))
        if not target:
            decisions.append(
                ActionParseDecision(
                    parser="aider_path_bound_edit",
                    status="rejected",
                    error_code="target_required",
                    detail="Aider-like edit chunk did not include a usable path.",
                    adapter_source=context.adapter_source,
                )
            )
            continue
        if not _target_allowed(target, context.allowed_files_snapshot):
            decisions.append(
                ActionParseDecision(
                    parser="aider_path_bound_edit",
                    status="rejected",
                    error_code="target_not_allowed",
                    detail="Aider-like edit target was outside the allowed file snapshot.",
                    adapter_source=context.adapter_source,
                )
            )
            continue
        actions.append(
            _build_action(
                {
                    "action_type": "EditFile",
                    "target": target,
                    "arguments": {
                        "old": old,
                        "new": new,
                        "content_source": "aider_path_bound_edit",
                    },
                    "reason": "Model returned a path-bound Aider-like search/replace chunk.",
                },
                context,
                index=len(actions),
            )
        )
    if actions:
        return actions, [
            *decisions,
            *[
                ActionParseDecision(
                    parser="aider_path_bound_edit",
                    status="accepted",
                    action_id=action.action_id,
                    adapter_source=context.adapter_source,
                )
                for action in actions
            ],
        ]
    return [], [
        *decisions,
        ActionParseDecision(
            parser="aider_path_bound_edit",
            status="skipped",
            detail="No path-bound Aider-like edit chunk found.",
            adapter_source=context.adapter_source,
        ),
    ]


def _json_action_specs(parsed: Any) -> list[dict[str, Any]] | None:
    if isinstance(parsed, dict) and isinstance(parsed.get("actions"), list):
        return [item for item in parsed["actions"] if isinstance(item, dict)]
    if isinstance(parsed, dict) and (
        "action_type" in parsed
        or "tool" in parsed
        or "action" in parsed
        or "name" in parsed
    ):
        return [parsed]
    return None


def _actions_from_specs(
    specs: list[dict[str, Any]],
    context: _ParseContext,
    *,
    parser: str,
) -> tuple[list[SourceProxyAction], list[ActionParseDecision]]:
    actions: list[SourceProxyAction] = []
    decisions: list[ActionParseDecision] = []
    if not specs:
        return [], [
            ActionParseDecision(
                parser=parser,
                status="rejected",
                error_code="invalid_action_schema",
                detail="No action objects were supplied.",
                adapter_source=context.adapter_source,
            )
        ]
    for index, spec in enumerate(specs):
        raw_action_type = _raw_action_type(spec)
        action_type = _normalize_action_type(spec)
        if action_type not in TOOL_CAPABILITIES:
            decisions.append(
                ActionParseDecision(
                    parser=parser,
                    status="rejected",
                    error_code="unsupported_action_type",
                    detail=f"Unsupported action type: {action_type or '<missing>'}.",
                    adapter_source=context.adapter_source,
                )
            )
            return [], decisions
        normalized = _normalize_spec(spec, action_type, raw_action_type=raw_action_type)
        schema_error = _schema_error(normalized, action_type)
        if schema_error:
            decisions.append(
                ActionParseDecision(
                    parser=parser,
                    status="rejected",
                    error_code=schema_error,
                    detail=f"{action_type} did not satisfy the action contract.",
                    adapter_source=context.adapter_source,
                )
            )
            return [], decisions
        target_error = _target_policy_error(normalized, action_type, context.allowed_files_snapshot)
        if target_error:
            decisions.append(
                ActionParseDecision(
                    parser=parser,
                    status="rejected",
                    error_code=target_error,
                    detail=f"{action_type} target was outside the allowed action contract.",
                    adapter_source=context.adapter_source,
                )
            )
            return [], decisions
        action = _build_action(normalized, context, index=index)
        actions.append(action)
        decisions.append(
            ActionParseDecision(
                parser=parser,
                status="accepted",
                action_id=action.action_id,
                adapter_source=context.adapter_source,
            )
        )
    return actions, decisions


def _raw_action_type(spec: dict[str, Any]) -> str:
    raw_type = spec.get("action_type") or spec.get("tool") or spec.get("name") or spec.get("action")
    return str(raw_type or "").strip()


def _normalize_action_type(spec: dict[str, Any]) -> str:
    raw = _raw_action_type(spec)
    if raw in TOOL_CAPABILITIES:
        return raw
    return _ACTION_ALIASES.get(raw.lower(), raw)


def _normalize_spec(spec: dict[str, Any], action_type: str, *, raw_action_type: str) -> dict[str, Any]:
    arguments = spec.get("arguments", spec.get("args", {}))
    raw_is_bash = raw_action_type.lower() == "bash"
    string_args_were_rejected = False
    if action_type == "RunCheck" and isinstance(arguments, str) and raw_is_bash:
        arguments = {"command": arguments}
    elif isinstance(arguments, str):
        string_args_were_rejected = True
    if not isinstance(arguments, dict):
        arguments = {"value": arguments}
    target = str(spec.get("target") or arguments.get("path") or arguments.get("file") or "").strip()
    if action_type in {"ReadFile", "WriteFile", "EditFile"}:
        target = normalize_repo_path_candidate(target)
    if action_type == "ListFiles":
        target = normalize_repo_path_candidate(target or str(arguments.get("directory") or "."))
    if action_type == "SearchRepo":
        target = normalize_repo_path_candidate(target or ".")
    if action_type == "RunCheck":
        target = normalize_repo_path_candidate(target or ".")
    if action_type == "WriteFile" and "content" not in arguments and "content_lines" in spec:
        content_lines = spec.get("content_lines")
        if isinstance(content_lines, list) and all(isinstance(item, str) for item in content_lines):
            arguments = {**arguments, "content": "\n".join(content_lines)}
    if action_type == "WriteFile" and "content" not in arguments and isinstance(spec.get("content"), str):
        arguments = {**arguments, "content": spec["content"]}
    return {
        **spec,
        "action_type": action_type,
        "target": target,
        "arguments": arguments,
        "reason": str(spec.get("reason") or ""),
        "adapter_source": str(spec.get("adapter_source") or ""),
        "_string_args_were_rejected": string_args_were_rejected,
    }


def _schema_error(spec: dict[str, Any], action_type: str) -> str:
    target = str(spec.get("target") or "").strip()
    arguments = spec.get("arguments")
    if spec.get("_string_args_were_rejected"):
        return "bash_string_args_only_for_bash"
    if action_type in {"ReadFile", "ListFiles", "SearchRepo", "WriteFile", "EditFile", "MultiEdit"}:
        if not target:
            return "target_required"
    if action_type == "WriteFile" and not isinstance(arguments.get("content"), str):
        return "content_required"
    if action_type == "EditFile" and not (
        isinstance(arguments.get("old"), str) and isinstance(arguments.get("new"), str)
    ):
        return "content_required"
    if action_type == "MultiEdit" and not isinstance(arguments.get("edits"), list):
        return "content_required"
    if action_type == "RunCheck" and not str(arguments.get("command") or "").strip():
        return "content_required"
    if action_type == "AskClarification" and not str(
        arguments.get("question") or spec.get("reason") or ""
    ).strip():
        return "content_required"
    if action_type == "ReturnFinal" and not str(
        arguments.get("message") or arguments.get("summary") or spec.get("reason") or ""
    ).strip():
        return "content_required"
    return ""


def _target_policy_error(
    spec: dict[str, Any],
    action_type: str,
    allowed_files_snapshot: list[str],
) -> str:
    target = str(spec.get("target") or "").strip()
    if action_type in {"WriteFile", "EditFile", "MultiEdit"} and not _target_allowed(
        target,
        allowed_files_snapshot,
    ):
        return "target_not_allowed"
    return ""


def _target_allowed(target: str, allowed_files_snapshot: list[str]) -> bool:
    if not allowed_files_snapshot:
        return True
    normalized_target = normalize_repo_path_candidate(target)
    allowed = {normalize_repo_path_candidate(path) for path in allowed_files_snapshot}
    return normalized_target in allowed


def _build_action(
    spec: dict[str, Any],
    context: _ParseContext,
    *,
    index: int,
) -> SourceProxyAction:
    action_type = spec["action_type"]
    action_id = str(
        spec.get("action_id")
        or f"{context.source_message_id or 'model-message'}:{index + 1}:{action_type}"
    )
    execution_state = (
        "blocked_until_plan_3" if action_type in PLAN_3_BLOCKED_ACTIONS else "parser_only"
    )
    return SourceProxyAction(
        action_id=action_id,
        action_type=action_type,
        target=str(spec.get("target") or ""),
        arguments=dict(spec.get("arguments") or {}),
        reason=str(spec.get("reason") or ""),
        requires_approval=bool(spec.get("requires_approval", action_type in PLAN_3_BLOCKED_ACTIONS)),
        model_id=str(spec.get("model_id") or context.model_id),
        source_message_id=str(spec.get("source_message_id") or context.source_message_id),
        allowed_files_snapshot=list(
            spec.get("allowed_files_snapshot") or context.allowed_files_snapshot
        ),
        created_at=str(spec.get("created_at") or context.created_at),
        adapter_source=str(spec.get("adapter_source") or context.adapter_source),
        execution_state=execution_state,
    )


def _reject(
    raw: str,
    decisions: list[ActionParseDecision],
    error_code: str,
    detail: str,
) -> ActionParseResult:
    decision = ActionParseDecision(
        parser="contract",
        status="rejected",
        error_code=error_code,
        detail=detail,
    )
    return ActionParseResult(
        raw_transcript=raw,
        actions=[],
        decisions=[*decisions, decision],
        adapter_source=decisions[-1].adapter_source if decisions else "generic",
        error_code=error_code,
        repair_prompt=_repair_prompt(error_code),
    )


def _repair_prompt(error_code: str) -> str:
    if error_code == "free_floating_code_no_path_action":
        return (
            "Return an explicit Source Proxy action with action_type and target, "
            "or a <file path=\"repo/path\">...</file> block. Do not send free-floating code."
        )
    return (
        "Return valid Source Proxy action JSON using one of: "
        + ", ".join(TOOL_CAPABILITIES.keys())
        + "."
    )


def _highest_priority_rejection(decisions: list[ActionParseDecision]) -> str:
    priority = (
        "target_not_allowed",
        "bash_string_args_only_for_bash",
        "target_required",
        "content_required",
        "unsupported_action_type",
        "invalid_action_schema",
    )
    rejected = {
        decision.error_code
        for decision in decisions
        if decision.status == "rejected" and decision.error_code
    }
    for code in priority:
        if code in rejected:
            return code
    return ""


def _looks_like_free_floating_code(raw: str) -> bool:
    text = raw.strip()
    return bool(
        re.search(r"```|^\s*(export\s+default|function\s+\w+|class\s+\w+|def\s+\w+|<html)", text, re.M)
    )


def _trim_block_content(content: str) -> str:
    value = content.replace("\r\n", "\n").replace("\r", "\n")
    if value.startswith("\n"):
        value = value[1:]
    if value.endswith("\n"):
        value = value[:-1]
    return value
