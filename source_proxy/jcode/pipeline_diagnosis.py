"""Isolated Campaign 2-J packet and tool-protocol diagnostics.

This module is intentionally disconnected from the production dispatcher. It
creates fresh detached worktrees and overlays, calls only exact local Ollama
models, and emits complete per-run evidence under the audit branch.
"""

from __future__ import annotations

import ast
import base64
import difflib
import hashlib
import json
import os
import re
import signal
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Literal, Mapping, Sequence

from source_proxy.decision.prompt_packet import PromptPacketInput, build_prompt_packet
from source_proxy.decision.task_spec_intake import (
    build_task_spec_intake,
    intake_as_legacy_task_spec,
)
from source_proxy.decision.tool_action_executor import ToolActionWorkspaceContract
from source_proxy.decision.tool_action_loop import BoundedAgentLoopRequest, run_bounded_agent_loop
from source_proxy.jcode.adapter import REQUIRED_DENIED_TOOLS
from source_proxy.jcode.containment import PreassembledRootConfig, assemble_preassembled_root
from source_proxy.jcode.supervision import JCodeSupervisionConfig


AUTHORIZATION_ID = "OPERATOR_AUTHORIZATION__C2J_PIPELINE_DIAGNOSIS_20260731_V1"
AUTHORIZATION_PROMPT_SHA256 = "f45bde0f3fd1c4c225f4a896577a0778408d449ebee41b3dc4f57c0171ab7afb"
AUTHORIZATION_RECEIPT = (
    "docs/architecture/jcode-qualification/pipeline-diagnosis/"
    "OPERATOR_AUTHORIZATION_RECEIPT.json"
)
DIAGNOSIS_SCHEMA = "source-proxy.campaign-2j-pipeline-diagnosis/v1"
CONTEXT_BUILDER_VERSION = "pipeline-diagnosis-context-builder/v1"
DIAGNOSTIC_BRIDGE_VERSION = "pipeline-diagnosis-bridge/v1"
JCODE_BINARY = Path(
    "/home/source/.codex-audits/jcode-dell-remediation-20260727/approved-binary/jcode"
)
JCODE_BINARY_SHA256 = "2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6"
JCODE_VERSION = "jcode v0.58.51-dev (2444e7b6)"
OLLAMA_API = "http://127.0.0.1:11434"
MODEL_REQUEST_LIMIT = 36
MAX_TURNS_PER_RUN = 3
BridgeMode = Literal["legacy_text_only", "tool_preserving"]
_REQUEST_LEDGER_LOCK = threading.Lock()

MODEL_SPECS: dict[str, dict[str, str]] = {
    "qwen2.5-coder:7b": {
        "digest": "dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364",
        "family": "qwen2",
        "parameter_size": "7.6B",
        "quantization": "Q4_K_M",
    },
    "qwen2.5-coder:14b": {
        "digest": "9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849",
        "family": "qwen2",
        "parameter_size": "14.8B",
        "quantization": "Q4_K_M",
    },
}

TASK_DEFINITIONS: dict[str, dict[str, Any]] = {
    "R": {
        "task_id": "PIPE-R-001",
        "fixture": "task_r",
        "task": (
            "Inspect ledger.py and focused_check.py. Identify the function that builds the "
            "trace receipt, the exact schema version it binds, and the focused test that "
            "checks that binding. Return only those three grounded facts."
        ),
        "writable_files": [],
        "read_only_files": ["ledger.py", "focused_check.py"],
        "acceptance_criteria": [
            "Function name exactly matches the source definition.",
            "Schema version exactly matches the source constant.",
            "Focused test name exactly matches the test definition.",
            "No file mutation occurs.",
        ],
        "expected": {
            "function_name": "build_trace_receipt",
            "schema_version": "pipeline-diagnosis/v3",
            "focused_test": "test_build_trace_receipt_binds_schema",
        },
        "focused_test": None,
    },
    "W": {
        "task_id": "PIPE-W-001",
        "fixture": "task_w",
        "task": (
            "Inspect label.py and focused_check.py. Update only label.py so normalize_label "
            "returns a lowercase, hyphen-separated label for surrounding or repeated "
            "whitespace. Run the focused test and report the result."
        ),
        "writable_files": ["label.py"],
        "read_only_files": ["focused_check.py"],
        "acceptance_criteria": [
            "Only label.py changes.",
            "Surrounding whitespace is removed.",
            "Repeated internal whitespace becomes one hyphen.",
            "Letters are lowercase.",
            "python -m pytest -q focused_check.py passes.",
        ],
        "expected": {},
        "focused_test": "python -m pytest -q focused_check.py",
    },
}


class PipelineDiagnosisError(RuntimeError):
    """A fail-closed diagnostic invariant was violated."""


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def diagnosis_root(root: Path | None = None) -> Path:
    return (root or repository_root()) / "docs/architecture/jcode-qualification/pipeline-diagnosis"


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(value), encoding="utf-8", newline="\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def safe_relative_path(value: str) -> str:
    normalized = value.replace("\\", "/").strip()
    path = PurePosixPath(normalized)
    if normalized in {"", "."} or path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise PipelineDiagnosisError(f"unsafe_diagnostic_path:{value}")
    return path.as_posix()


def task_definition(task_key: str) -> dict[str, Any]:
    try:
        return json.loads(json.dumps(TASK_DEFINITIONS[task_key]))
    except KeyError as error:
        raise PipelineDiagnosisError(f"unknown_task:{task_key}") from error


def tool_schemas(task_key: str) -> list[dict[str, Any]]:
    read_file = {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read one declared fixture file by relative path.",
            "parameters": {
                "type": "object",
                "additionalProperties": False,
                "required": ["path"],
                "properties": {"path": {"type": "string"}},
            },
        },
    }
    if task_key == "R":
        return [read_file]
    return [
        read_file,
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Replace the one writable fixture file with complete UTF-8 text.",
                "parameters": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "content"],
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "apply_patch",
                "description": "Replace one exact old fragment in the writable fixture file.",
                "parameters": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "old", "new"],
                    "properties": {
                        "path": {"type": "string"},
                        "old": {"type": "string"},
                        "new": {"type": "string"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "run_test",
                "description": "Run the one sealed focused test in the fixture overlay.",
                "parameters": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {},
                },
            },
        },
    ]


def ordered_file_manifest(overlay: Path) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    for path in sorted(item for item in overlay.rglob("*") if item.is_file() and not is_runtime_artifact(item, overlay)):
        relative = path.relative_to(overlay).as_posix()
        raw = path.read_bytes()
        manifest.append(
            {
                "path": relative,
                "sha256": sha256_bytes(raw),
                "bytes": len(raw),
                "content": raw.decode("utf-8"),
            }
        )
    return manifest


def build_context_manifest(task_key: str, overlay: Path) -> dict[str, Any]:
    task = task_definition(task_key)
    files = ordered_file_manifest(overlay)
    packet: dict[str, Any] = {
        "schema_version": "source-proxy.pipeline-diagnosis-context/v1",
        "context_builder_version": CONTEXT_BUILDER_VERSION,
        "task_id": task["task_id"],
        "ordered_file_manifest": files,
        "writable_files": task["writable_files"],
        "read_only_files": task["read_only_files"],
        "excluded_paths": [
            "benchmarks/**",
            "qualification_fixture/**",
            "fixture_proxy/**",
            "qualification_write_fixture/**",
            "/home/source/SpiritOS/**",
        ],
        "truncation": {"occurred": False, "omitted_bytes": 0},
        "total_bytes": sum(int(item["bytes"]) for item in files),
    }
    packet["context_packet_sha256"] = sha256_text(canonical_json(packet))
    return packet


def build_task_manifest(task_key: str, context: Mapping[str, Any]) -> dict[str, Any]:
    task = task_definition(task_key)
    visible = {key: value for key, value in task.items() if key != "expected"}
    manifest: dict[str, Any] = {
        "schema_version": "source-proxy.pipeline-diagnosis-task/v1",
        **visible,
        "context_packet_sha256": context["context_packet_sha256"],
        "tool_schema_sha256": sha256_text(canonical_json(tool_schemas(task_key))),
        "authorization_id": AUTHORIZATION_ID,
        "prohibited_actions": [
            "network",
            "Git mutation",
            "files outside the fixture overlay",
            "benchmark access",
            "session or memory reuse",
        ],
    }
    manifest["task_manifest_sha256"] = sha256_text(canonical_json(manifest))
    return manifest


def concise_system_prompt(task_key: str) -> str:
    task = task_definition(task_key)
    mode = "read-only grounding" if task_key == "R" else "one-file repair"
    return (
        f"You are running an isolated {mode} qualification. Use only supplied context or "
        "declared tools. Never invent file contents or test results. Do not use network, Git, "
        "memory, or undeclared paths."
    )


def concise_task_text(task_manifest: Mapping[str, Any]) -> str:
    criteria = "\n".join(f"- {item}" for item in task_manifest["acceptance_criteria"])
    return (
        f"Task ID: {task_manifest['task_id']}\n"
        f"Task: {task_manifest['task']}\n"
        f"Writable files: {json.dumps(task_manifest['writable_files'])}\n"
        f"Read-only files: {json.dumps(task_manifest['read_only_files'])}\n"
        f"Acceptance criteria:\n{criteria}"
    )


def inline_file_text(context: Mapping[str, Any]) -> str:
    chunks: list[str] = []
    for item in context["ordered_file_manifest"]:
        chunks.append(f"FILE: {item['path']}\n---\n{item['content']}\n---")
    return "\n\n".join(chunks)


def build_full_proxy_packet(
    task_key: str,
    task_manifest: Mapping[str, Any],
    context: Mapping[str, Any],
    overlay: Path,
) -> dict[str, Any]:
    relevant_context = (
        "Canonical qualification context follows.\n"
        + canonical_json(context)
    )
    packet = build_prompt_packet(
        PromptPacketInput(
            task=str(task_manifest["task"]),
            relevant_context=relevant_context,
            needs_codebase_context=True,
            wants_implementation=task_key == "W",
            prefer_free=True,
        )
    ).as_payload()
    intake = build_task_spec_intake(
        str(task_manifest["task"]),
        workspace_root=overlay,
        allowed_files=list(task_manifest["writable_files"]),
        forbidden_files=list(task_manifest["read_only_files"]),
        wants_implementation=task_key == "W",
        allow_messy_homepage_helper=False,
    )
    packet["task_spec_intake"] = intake.to_dict()
    packet["legacy_task_spec"] = intake_as_legacy_task_spec(intake)
    packet["diagnostic_binding"] = {
        "task_manifest_sha256": task_manifest["task_manifest_sha256"],
        "context_packet_sha256": context["context_packet_sha256"],
        "note": "Diagnostic binding only; not a production packet field.",
    }
    return packet


def packet_noise_metrics(packet_text: str, task_manifest: Mapping[str, Any]) -> dict[str, Any]:
    total = len(packet_text.encode("utf-8"))
    task_text = str(task_manifest["task"])
    task_pos = packet_text.find(task_text)
    source_positions = {
        name: packet_text.find(name)
        for name in [
            *task_manifest["writable_files"],
            *task_manifest["read_only_files"],
        ]
    }
    relevant_terms = [task_text, *source_positions]
    relevant_bytes = sum(len(term.encode("utf-8")) for term in relevant_terms if term)
    governance_markers = ["campaign", "authorization", "phase", "paste back", "target model"]
    governance_hits = sum(packet_text.lower().count(marker) for marker in governance_markers)
    return {
        "total_bytes": total,
        "estimated_tokens": max(1, round(total / 4)),
        "task_position_bytes": task_pos,
        "source_file_positions": source_positions,
        "relevant_context_ratio_lower_bound": round(relevant_bytes / max(total, 1), 6),
        "governance_marker_hits": governance_hits,
        "effective_output_budget_tokens": 1024,
    }


@dataclass
class ModelCallRecord:
    endpoint: str
    request_body: dict[str, Any]
    request_bytes_b64: str
    request_sha256: str
    response_body: dict[str, Any]
    response_bytes_b64: str
    response_sha256: str
    elapsed_seconds: float
    request_ledger_id: str
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "request_body": self.request_body,
            "request_bytes_base64": self.request_bytes_b64,
            "request_sha256": self.request_sha256,
            "response_body": self.response_body,
            "response_bytes_base64": self.response_bytes_b64,
            "response_sha256": self.response_sha256,
            "elapsed_seconds": self.elapsed_seconds,
            "request_ledger_id": self.request_ledger_id,
            "error": self.error,
        }


class ExactOllamaClient:
    def __init__(
        self,
        model: str,
        *,
        run_id: str,
        evidence_root: Path,
        api_base: str = OLLAMA_API,
        timeout: int = 300,
    ) -> None:
        if model not in MODEL_SPECS:
            raise PipelineDiagnosisError(f"unauthorized_model:{model}")
        self.model = model
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self.run_id = run_id
        self.evidence_root = evidence_root
        self.records: list[ModelCallRecord] = []
        self.registry_receipt = self.verify_registry()

    def verify_registry(self) -> dict[str, Any]:
        with urllib.request.urlopen(f"{self.api_base}/api/tags", timeout=10) as response:
            raw = response.read()
        payload = json.loads(raw.decode("utf-8"))
        matches = [item for item in payload.get("models", []) if item.get("name") == self.model]
        if len(matches) != 1:
            raise PipelineDiagnosisError(f"model_registry_identity_unavailable:{self.model}")
        observed = matches[0]
        expected = MODEL_SPECS[self.model]
        if observed.get("digest") != expected["digest"]:
            raise PipelineDiagnosisError(f"model_digest_mismatch:{self.model}")
        details = observed.get("details") or {}
        if (
            details.get("family") != expected["family"]
            or details.get("parameter_size") != expected["parameter_size"]
            or details.get("quantization_level") != expected["quantization"]
        ):
            raise PipelineDiagnosisError(f"model_detail_mismatch:{self.model}")
        return {
            "endpoint": f"{self.api_base}/api/tags",
            "model": self.model,
            "expected": expected,
            "observed": observed,
            "verified": True,
        }

    def post(self, route: str, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("model") != self.model:
            raise PipelineDiagnosisError("model_request_identity_drift")
        body = canonical_json(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.api_base}{route}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        ledger_id = record_model_request_start(
            self.evidence_root,
            run_id=self.run_id,
            model=self.model,
            endpoint=f"{self.api_base}{route}",
            request_body=payload,
            request_bytes=body,
        )
        started = time.monotonic()
        raw = b""
        parsed: dict[str, Any] = {}
        error_text: str | None = None
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read()
            parsed = json.loads(raw.decode("utf-8"))
            if parsed.get("model") != self.model or parsed.get("done") is not True:
                raise PipelineDiagnosisError("provider_response_identity_invalid")
        except Exception as error:
            error_text = f"{type(error).__name__}:{error}"
            record_model_request_finish(
                self.evidence_root,
                ledger_id=ledger_id,
                response_sha256=sha256_bytes(raw),
                error=error_text,
            )
            self.records.append(
                ModelCallRecord(
                    endpoint=f"{self.api_base}{route}",
                    request_body=payload,
                    request_bytes_b64=base64.b64encode(body).decode("ascii"),
                    request_sha256=sha256_bytes(body),
                    response_body=parsed,
                    response_bytes_b64=base64.b64encode(raw).decode("ascii"),
                    response_sha256=sha256_bytes(raw),
                    elapsed_seconds=round(time.monotonic() - started, 3),
                    request_ledger_id=ledger_id,
                    error=error_text,
                )
            )
            raise
        elapsed = round(time.monotonic() - started, 3)
        record_model_request_finish(
            self.evidence_root,
            ledger_id=ledger_id,
            response_sha256=sha256_bytes(raw),
            error=None,
        )
        self.records.append(
            ModelCallRecord(
                endpoint=f"{self.api_base}{route}",
                request_body=payload,
                request_bytes_b64=base64.b64encode(body).decode("ascii"),
                request_sha256=sha256_bytes(body),
                response_body=parsed,
                response_bytes_b64=base64.b64encode(raw).decode("ascii"),
                response_sha256=sha256_bytes(raw),
                elapsed_seconds=elapsed,
                request_ledger_id=ledger_id,
            )
        )
        return parsed

    def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": "10m",
            "options": {"temperature": 0, "seed": 7, "num_predict": 1024},
        }
        if tools:
            payload["tools"] = tools
        return self.post("/api/chat", payload)

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "10m",
            "options": {"temperature": 0, "seed": 7, "num_predict": 1024},
        }
        return str(self.post("/api/generate", payload).get("response") or "")


@dataclass
class ToolExecution:
    turn: int
    tool_name: str
    arguments: dict[str, Any]
    status: str
    result: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn": self.turn,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "status": self.status,
            "result": self.result,
        }


def execute_diagnostic_tool(
    *,
    call: Mapping[str, Any],
    task_key: str,
    overlay: Path,
    turn: int,
) -> ToolExecution:
    function = call.get("function") if isinstance(call.get("function"), Mapping) else {}
    name = str(function.get("name") or "")
    arguments = function.get("arguments")
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            arguments = {}
    args = dict(arguments) if isinstance(arguments, Mapping) else {}
    task = task_definition(task_key)
    readable = set(task["writable_files"] + task["read_only_files"])
    writable = set(task["writable_files"])
    try:
        if name == "read_file":
            relative = safe_relative_path(str(args.get("path") or ""))
            if relative not in readable:
                raise PipelineDiagnosisError("read_path_denied")
            result = (overlay / relative).read_text(encoding="utf-8")
        elif name == "write_file":
            relative = safe_relative_path(str(args.get("path") or ""))
            if relative not in writable or not isinstance(args.get("content"), str):
                raise PipelineDiagnosisError("write_path_or_content_denied")
            (overlay / relative).write_text(str(args["content"]), encoding="utf-8", newline="\n")
            result = f"wrote:{relative}"
        elif name == "apply_patch":
            relative = safe_relative_path(str(args.get("path") or ""))
            old = args.get("old")
            new = args.get("new")
            if relative not in writable or not isinstance(old, str) or not isinstance(new, str):
                raise PipelineDiagnosisError("patch_path_or_content_denied")
            path = overlay / relative
            content = path.read_text(encoding="utf-8")
            if old not in content:
                raise PipelineDiagnosisError("patch_old_fragment_missing")
            path.write_text(content.replace(old, new, 1), encoding="utf-8", newline="\n")
            result = f"patched:{relative}"
        elif name == "run_test" and task_key == "W":
            completed = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "focused_check.py"],
                cwd=overlay,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            result = canonical_json(
                {
                    "exit_code": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                }
            ).strip()
        else:
            raise PipelineDiagnosisError(f"tool_name_denied:{name}")
        return ToolExecution(turn, name, args, "completed", result)
    except (OSError, subprocess.SubprocessError, PipelineDiagnosisError) as error:
        return ToolExecution(turn, name, args, "failed", str(error))


def run_direct_inline(
    task_key: str,
    model: str,
    task_manifest: Mapping[str, Any],
    context: Mapping[str, Any],
    client: ExactOllamaClient,
) -> dict[str, Any]:
    lane_instruction = (
        "Return exactly one JSON object with keys function_name, schema_version, and focused_test."
        if task_key == "R"
        else "Do not apply changes. Return the complete corrected label.py content only, with no markdown fence."
    )
    messages = [
        {"role": "system", "content": concise_system_prompt(task_key)},
        {
            "role": "user",
            "content": f"{concise_task_text(task_manifest)}\n\n{lane_instruction}\n\n{inline_file_text(context)}",
        },
    ]
    response = client.chat(messages)
    message = response.get("message") if isinstance(response.get("message"), dict) else {}
    return {
        "messages": messages,
        "tools": [],
        "turns": 1,
        "final_text": str(message.get("content") or ""),
        "raw_response": response,
        "tool_ledger": [],
        "tool_parse": {"tool_calls": list(message.get("tool_calls") or []), "parser": "ollama_chat/v1"},
    }


def run_direct_tool_loop(
    task_key: str,
    model: str,
    task_manifest: Mapping[str, Any],
    overlay: Path,
    client: ExactOllamaClient,
) -> dict[str, Any]:
    tools = tool_schemas(task_key)
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                concise_system_prompt(task_key)
                + " You are in a bounded agent loop. Call declared tools for file facts and execution; "
                "after tool results, return the grounded final answer."
            ),
        },
        {"role": "user", "content": concise_task_text(task_manifest)},
    ]
    ledger: list[ToolExecution] = []
    responses: list[dict[str, Any]] = []
    final_text = ""
    for turn in range(1, MAX_TURNS_PER_RUN + 1):
        response = client.chat(messages, tools)
        responses.append(response)
        message = response.get("message") if isinstance(response.get("message"), dict) else {}
        assistant = {key: value for key, value in message.items() if key in {"role", "content", "thinking", "tool_calls"}}
        assistant.setdefault("role", "assistant")
        messages.append(assistant)
        calls = list(message.get("tool_calls") or [])
        if not calls:
            final_text = str(message.get("content") or "")
            break
        for call in calls:
            execution = execute_diagnostic_tool(call=call, task_key=task_key, overlay=overlay, turn=turn)
            ledger.append(execution)
            messages.append(
                {
                    "role": "tool",
                    "tool_name": execution.tool_name,
                    "content": execution.result,
                }
            )
    return {
        "messages": messages,
        "tools": tools,
        "turns": len(responses),
        "final_text": final_text,
        "raw_response": responses,
        "tool_ledger": [item.to_dict() for item in ledger],
        "tool_parse": {
            "parser": "ollama_native_tool_calls/v1",
            "tool_call_count": len(ledger),
            "failed_tool_calls": sum(item.status != "completed" for item in ledger),
        },
    }


def render_baseline_prompt(packet: Mapping[str, Any], *, full_proxy_packet: Mapping[str, Any] | None) -> str:
    action_contract = (
        "Return Source Proxy action JSON only. To read a file, use "
        '{"action_type":"ReadFile","target":"PATH","arguments":{},"reason":"..."}. '
        "To finish, use "
        '{"action_type":"ReturnFinal","target":".","arguments":{"message":"GROUNDED ANSWER"},"reason":"done"}. '
        "Do not combine unsupported prose with actions."
    )
    payload = dict(packet)
    if full_proxy_packet is not None:
        payload["full_proxy_packet"] = full_proxy_packet
    return f"{action_contract}\nMODEL PACKET:\n{canonical_json(payload)}"


def run_baseline_harness(
    task_key: str,
    model: str,
    task_manifest: Mapping[str, Any],
    context: Mapping[str, Any],
    overlay: Path,
    client: ExactOllamaClient,
    *,
    full_proxy_packet: Mapping[str, Any] | None,
) -> dict[str, Any]:
    contract = ToolActionWorkspaceContract(
        workspace_root=overlay,
        allowed_files=tuple(task_manifest["writable_files"] + task_manifest["read_only_files"]),
        forbidden_files=(),
        protected_paths=tuple(task_manifest["read_only_files"] if task_key == "W" else ()),
        workspace_mode="disposable_workspace",
        approval_level="diagnostic_only",
        model_may_choose_paths=False,
        max_file_count=len(context["ordered_file_manifest"]),
        network_allowed=False,
        run_timeout_seconds=30,
    )
    context_packet: dict[str, Any] = {
        "mode": "pipeline_diagnosis_full" if full_proxy_packet is not None else "pipeline_diagnosis_minimal",
        "task_id": task_manifest["task_id"],
        "file_manifest": [
            {key: item[key] for key in ("path", "sha256", "bytes")}
            for item in context["ordered_file_manifest"]
        ],
        "acceptance_criteria": task_manifest["acceptance_criteria"],
        "context_packet_sha256": context["context_packet_sha256"],
    }
    request = BoundedAgentLoopRequest(
        task_spec={
            "task_id": task_manifest["task_id"],
            "task": task_manifest["task"],
            "writable_files": task_manifest["writable_files"],
            "read_only_files": task_manifest["read_only_files"],
        },
        context_packet=context_packet,
        workspace_contract=contract,
        model_id=model,
        adapter_source="pipeline_diagnosis_baseline/v1",
        source_message_id=f"pipeline-{task_key.lower()}",
        recommended_checks=(),
        run_recommended_checks=False,
        max_format_retries=0,
        max_verification_repairs=0,
    )
    prompts: list[str] = []

    def call_model(model_packet: dict[str, Any]) -> str:
        prompt = render_baseline_prompt(model_packet, full_proxy_packet=full_proxy_packet)
        prompts.append(prompt)
        return client.generate(prompt)

    result = run_bounded_agent_loop(request, call_model).to_dict()
    receipt = result["receipt"]
    finals = [
        str((execution.get("result") or {}).get("observation") or "")
        for execution in receipt.get("executions") or []
        if (execution.get("receipt") or {}).get("action_type") == "ReturnFinal"
    ]
    return {
        "messages": [{"role": "user", "content": item} for item in prompts],
        "tools": (receipt.get("model_calls") or [{}])[0].get("packet", {}).get("tool_contract", {}),
        "turns": len(prompts),
        "final_text": finals[-1] if finals else "",
        "raw_response": receipt.get("raw_model_transcripts") or [],
        "tool_ledger": receipt.get("executions") or [],
        "tool_parse": receipt.get("parse_results") or [],
        "baseline_receipt": receipt,
    }


def legacy_bridge_transform(request_body: Mapping[str, Any], model: str) -> dict[str, Any]:
    messages = request_body.get("messages")
    if not isinstance(messages, list):
        raise PipelineDiagnosisError("compatibility_messages_invalid")
    prompt = "\n".join(
        str(item.get("content", "")) for item in messages if isinstance(item, Mapping)
    ).strip()
    return {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "seed": 7, "num_predict": 1024},
    }


def tool_preserving_bridge_transform(request_body: Mapping[str, Any], model: str) -> dict[str, Any]:
    messages = request_body.get("messages")
    if not isinstance(messages, list):
        raise PipelineDiagnosisError("compatibility_messages_invalid")
    call_names: dict[str, str] = {}
    converted: list[dict[str, Any]] = []
    for item in messages:
        if not isinstance(item, Mapping):
            continue
        message = dict(item)
        converted_calls: list[dict[str, Any]] = []
        for call in message.get("tool_calls") or []:
            if not isinstance(call, Mapping):
                continue
            function = call.get("function") if isinstance(call.get("function"), Mapping) else {}
            if call.get("id") and function.get("name"):
                call_names[str(call["id"])] = str(function["name"])
            arguments = function.get("arguments")
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}
            converted_calls.append(
                {
                    "function": {
                        "name": str(function.get("name") or ""),
                        "arguments": dict(arguments) if isinstance(arguments, Mapping) else {},
                    }
                }
            )
        if converted_calls:
            message["tool_calls"] = converted_calls
        if message.get("role") == "tool" and not message.get("tool_name"):
            call_id = str(message.get("tool_call_id") or "")
            if call_id in call_names:
                message["tool_name"] = call_names[call_id]
        converted.append(message)
    payload: dict[str, Any] = {
        "model": model,
        "messages": converted,
        "stream": False,
        "options": {"temperature": 0, "seed": 7, "num_predict": 1024},
    }
    tools = request_body.get("tools")
    if isinstance(tools, list) and tools:
        payload["tools"] = tools
    return payload


def openai_sse_response(ollama_response: Mapping[str, Any], model: str) -> bytes:
    message = ollama_response.get("message") if isinstance(ollama_response.get("message"), Mapping) else {}
    tool_calls = list(message.get("tool_calls") or [])
    events: list[dict[str, Any]] = []
    if tool_calls:
        converted_calls: list[dict[str, Any]] = []
        for index, call in enumerate(tool_calls):
            function = call.get("function") if isinstance(call, Mapping) and isinstance(call.get("function"), Mapping) else {}
            arguments = function.get("arguments") if isinstance(function.get("arguments"), Mapping) else {}
            converted_calls.append(
                {
                    "index": index,
                    "id": f"call_diag_{index}",
                    "type": "function",
                    "function": {
                        "name": str(function.get("name") or ""),
                        "arguments": json.dumps(arguments, ensure_ascii=False, separators=(",", ":")),
                    },
                }
            )
        events.append(
            {
                "id": "c2j-diagnostic",
                "object": "chat.completion.chunk",
                "model": model,
                "choices": [{"index": 0, "delta": {"role": "assistant", "tool_calls": converted_calls}, "finish_reason": None}],
            }
        )
        finish_reason = "tool_calls"
    else:
        content = str(message.get("content") or ollama_response.get("response") or "")
        events.append(
            {
                "id": "c2j-diagnostic",
                "object": "chat.completion.chunk",
                "model": model,
                "choices": [{"index": 0, "delta": {"role": "assistant", "content": content}, "finish_reason": None}],
            }
        )
        finish_reason = "stop"
    events.append(
        {
            "id": "c2j-diagnostic",
            "object": "chat.completion.chunk",
            "model": model,
            "choices": [{"index": 0, "delta": {}, "finish_reason": finish_reason}],
        }
    )
    return b"".join(
        b"data: " + json.dumps(event, separators=(",", ":")).encode("utf-8") + b"\n\n"
        for event in events
    ) + b"data: [DONE]\n\n"


def read_http_request(client: socket.socket) -> dict[str, Any]:
    data = bytearray()
    while b"\r\n\r\n" not in data and len(data) <= 2_000_000:
        chunk = client.recv(65_536)
        if not chunk:
            raise PipelineDiagnosisError("http_headers_incomplete")
        data.extend(chunk)
    raw_headers, body = bytes(data).split(b"\r\n\r\n", 1)
    lines = raw_headers.decode("ascii").split("\r\n")
    method, path, version = lines[0].split()
    headers: dict[str, str] = {}
    for line in lines[1:]:
        key, value = line.split(":", 1)
        headers[key.lower()] = value.strip()
    length = int(headers.get("content-length", "-1"))
    if length < 0 or length > 2_000_000:
        raise PipelineDiagnosisError("http_body_size_invalid")
    while len(body) < length:
        chunk = client.recv(min(65_536, length - len(body)))
        if not chunk:
            raise PipelineDiagnosisError("http_body_incomplete")
        body += chunk
    raw_body = body[:length]
    return {
        "method": method,
        "path": path,
        "version": version,
        "headers": {key: ("[redacted]" if "authorization" in key else value) for key, value in headers.items()},
        "raw_body": raw_body,
        "body": json.loads(raw_body.decode("utf-8")),
    }


@dataclass
class DiagnosticBridgeServer:
    socket_path: Path
    model: str
    mode: BridgeMode
    run_id: str
    evidence_root: Path
    max_requests: int = MAX_TURNS_PER_RUN
    capture_only: bool = False
    client: ExactOllamaClient = field(init=False)
    provider_requests: list[dict[str, Any]] = field(default_factory=list, init=False)
    provider_responses: list[dict[str, Any]] = field(default_factory=list, init=False)
    transformations: list[dict[str, Any]] = field(default_factory=list, init=False)
    errors: list[str] = field(default_factory=list, init=False)
    _listener: socket.socket | None = field(default=None, init=False)
    _thread: threading.Thread | None = field(default=None, init=False)
    _connection_threads: list[threading.Thread] = field(default_factory=list, init=False)
    _connected_sockets: list[socket.socket] = field(default_factory=list, init=False)
    _stop: threading.Event = field(default_factory=threading.Event, init=False)

    def __post_init__(self) -> None:
        self.client = ExactOllamaClient(
            self.model,
            run_id=self.run_id,
            evidence_root=self.evidence_root,
        )

    def start(self) -> None:
        if self.socket_path.exists() or not self.socket_path.parent.is_dir():
            raise PipelineDiagnosisError("diagnostic_bridge_socket_invalid")
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(self.socket_path))
        self.socket_path.chmod(0o600)
        listener.listen(self.max_requests)
        listener.settimeout(0.25)
        self._listener = listener
        self._thread = threading.Thread(target=self._serve, name="c2j-diagnostic-bridge", daemon=True)
        self._thread.start()

    def start_connected(self, connections: Sequence[socket.socket]) -> None:
        if self._listener is not None or self._thread is not None or self._connection_threads:
            raise PipelineDiagnosisError("diagnostic_bridge_already_started")
        self._connected_sockets = list(connections)
        for index, connection in enumerate(self._connected_sockets):
            thread = threading.Thread(
                target=self._serve_connection,
                args=(connection,),
                name=f"c2j-diagnostic-channel-{index + 1}",
                daemon=True,
            )
            self._connection_threads.append(thread)
            thread.start()

    def close(self) -> None:
        self._stop.set()
        if self._listener is not None:
            self._listener.close()
        for connection in self._connected_sockets:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        for thread in self._connection_threads:
            thread.join(timeout=2)
        self._listener = None
        self._connected_sockets = []
        self._connection_threads = []
        if self.socket_path.exists() or self.socket_path.is_symlink():
            self.socket_path.unlink()

    def _serve(self) -> None:
        assert self._listener is not None
        while not self._stop.is_set():
            try:
                connection, _ = self._listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self._serve_connection(connection)

    def _serve_connection(self, connection: socket.socket) -> None:
            try:
                request = read_http_request(connection)
                body = request["body"]
                if request["method"] != "POST" or request["path"] != "/v1/chat/completions":
                    raise PipelineDiagnosisError("compatibility_route_denied")
                if body.get("model") != self.model:
                    raise PipelineDiagnosisError("compatibility_model_denied")
                captured_request = {
                    "method": request["method"],
                    "path": request["path"],
                    "headers": request["headers"],
                    "body": body,
                    "body_bytes_base64": base64.b64encode(request["raw_body"]).decode("ascii"),
                    "body_sha256": sha256_bytes(request["raw_body"]),
                    "model_request_authorized": (
                        not self.capture_only and len(self.client.records) < self.max_requests
                    ),
                    "capture_only": self.capture_only,
                }
                self.provider_requests.append(captured_request)
                if not self.capture_only and not captured_request["model_request_authorized"]:
                    rejection = canonical_json(
                        {
                            "error": {
                                "message": "diagnostic model-turn budget exhausted",
                                "type": "rate_limit_error",
                            }
                        }
                    ).encode("utf-8")
                    connection.sendall(
                        b"HTTP/1.1 429 Too Many Requests\r\nContent-Type: application/json\r\n"
                        b"Connection: close\r\nContent-Length: "
                        + str(len(rejection)).encode("ascii")
                        + b"\r\n\r\n"
                        + rejection
                    )
                    return
                if self.capture_only:
                    transformed = {"capture_only": True, "model": self.model}
                    response = {
                        "model": self.model,
                        "done": True,
                        "message": {"role": "assistant", "content": "CAPTURE_ONLY"},
                    }
                elif self.mode == "legacy_text_only":
                    transformed = legacy_bridge_transform(body, self.model)
                    response = self.client.post("/api/generate", transformed)
                else:
                    transformed = tool_preserving_bridge_transform(body, self.model)
                    response = self.client.post("/api/chat", transformed)
                self.transformations.append(
                    {
                        "mode": self.mode,
                        "capture_only": self.capture_only,
                        "input_sha256": sha256_text(canonical_json(body)),
                        "output_sha256": sha256_text(canonical_json(transformed)),
                        "input_roles": [item.get("role") for item in body.get("messages", []) if isinstance(item, Mapping)],
                        "input_tool_names": [
                            str((item.get("function") or {}).get("name") or "")
                            for item in body.get("tools", [])
                            if isinstance(item, Mapping)
                        ],
                        "output_roles": [item.get("role") for item in transformed.get("messages", []) if isinstance(item, Mapping)],
                        "output_tool_names": [
                            str((item.get("function") or {}).get("name") or "")
                            for item in transformed.get("tools", [])
                            if isinstance(item, Mapping)
                        ],
                        "tools_dropped": bool(body.get("tools")) and not bool(transformed.get("tools")),
                        "roles_flattened": "messages" not in transformed,
                        "input_body": body,
                        "output_body": transformed,
                    }
                )
                sse = openai_sse_response(response, self.model)
                self.provider_responses.append(
                    {
                        "content_type": "text/event-stream",
                        "body_bytes_base64": base64.b64encode(sse).decode("ascii"),
                        "body_sha256": sha256_bytes(sse),
                        "body_utf8": sse.decode("utf-8"),
                    }
                )
                connection.sendall(
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: text/event-stream\r\n"
                    b"Cache-Control: no-cache\r\n"
                    b"Connection: close\r\n"
                    b"Content-Length: "
                    + str(len(sse)).encode("ascii")
                    + b"\r\n\r\n"
                    + sse
                )
            except Exception as error:  # preserved as diagnostic evidence
                if str(error) == "http_headers_incomplete":
                    return
                self.errors.append(f"{type(error).__name__}:{error}")
                body = canonical_json({"error": {"message": str(error), "type": "invalid_request_error"}}).encode("utf-8")
                try:
                    connection.sendall(
                        b"HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\nConnection: close\r\nContent-Length: "
                        + str(len(body)).encode("ascii")
                        + b"\r\n\r\n"
                        + body
                    )
                except OSError:
                    pass
            finally:
                connection.close()


def compile_relay_launcher(root: Path, output: Path) -> None:
    source = root / "source_proxy/jcode/preassembled_relay_runner.c"
    source_text = source.read_text(encoding="utf-8")
    replacements = {
        "static void serve(int listener, const char *socket_path, int relay_fd) {\n  for (;;) {":
            "static void serve(int listener, const char *socket_path, int *relay_fds, int relay_count) {\n  int relay_index = 0;\n  for (;;) {",
        "    if (relay_fd >= 0) { forward_pair(client, relay_fd); close(client); return; }":
            "    if (relay_count > 0) {\n      if (relay_index >= relay_count) { close(client); return; }\n      forward_pair(client, relay_fds[relay_index]);\n      close(relay_fds[relay_index]);\n      ++relay_index;\n      close(client);\n      if (relay_index >= relay_count) return;\n      continue;\n    }",
        "  int port = 0, command = -1, listener = -1, relay_fd = -1;":
            "  int port = 0, command = -1, listener = -1, relay_count = 0;\n  int relay_fds[3] = {-1, -1, -1};",
        "    else if (!strcmp(argv[index], \"--relay-fd\") && index + 1 < argc) relay_fd = atoi(argv[++index]);":
            "    else if (!strcmp(argv[index], \"--relay-fd\") && index + 1 < argc) {\n      if (relay_count >= 3) return 64;\n      relay_fds[relay_count++] = atoi(argv[++index]);\n    }",
        "  if (socket_path || relay_fd >= 0) {": "  if (socket_path || relay_count > 0) {",
        "if (prctl(PR_SET_PDEATHSIG, SIGTERM) || getppid() == 1) return 67; serve(listener, socket_path, relay_fd); return 0;":
            "if (prctl(PR_SET_PDEATHSIG, SIGTERM) || getppid() == 1) return 67; serve(listener, socket_path, relay_fds, relay_count); return 0;",
    }
    for old, new in replacements.items():
        if source_text.count(old) != 1:
            raise PipelineDiagnosisError("relay_launcher_source_shape_drift")
        source_text = source_text.replace(old, new)
    completed = subprocess.run(
        ["gcc", "-x", "c", "-static", "-O2", "-Wall", "-Werror", "-", "-o", str(output)],
        cwd=root,
        input=source_text,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if completed.returncode != 0:
        raise PipelineDiagnosisError(f"relay_launcher_compile_failed:{completed.stderr}")


def run_supervised_with_socketpairs(
    command: Sequence[str],
    child_sockets: Sequence[socket.socket],
    config: JCodeSupervisionConfig,
) -> dict[str, object]:
    started = time.monotonic()
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            list(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
            pass_fds=tuple(item.fileno() for item in child_sockets),
        )
    finally:
        for item in child_sockets:
            item.close()
    assert process is not None
    disposition = "completed"
    termination_signal: str | None = None
    try:
        stdout, stderr = process.communicate(timeout=config.timeout_seconds)
    except subprocess.TimeoutExpired:
        disposition = "timed_out"
        os.killpg(process.pid, signal.SIGTERM)
        termination_signal = "SIGTERM"
        try:
            stdout, stderr = process.communicate(timeout=config.termination_grace_seconds)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            termination_signal = "SIGKILL"
            stdout, stderr = process.communicate()
    deadline = time.monotonic() + 1
    process_group_reaped = False
    while time.monotonic() < deadline:
        try:
            os.killpg(process.pid, 0)
        except ProcessLookupError:
            process_group_reaped = True
            break
        time.sleep(0.02)
    return {
        "status": disposition,
        "process_exit_code": process.returncode,
        "termination_signal": termination_signal,
        "process_group_reaped": process_group_reaped,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "stdout": stdout,
        "stderr": stderr,
        "supervisor": "pipeline-diagnosis-socketpair-supervisor/v1",
    }


def jcode_runtime_files() -> tuple[Path, ...]:
    return (
        Path("/lib/x86_64-linux-gnu/libgcc_s.so.1"),
        Path("/lib/x86_64-linux-gnu/libm.so.6"),
        Path("/lib/x86_64-linux-gnu/libc.so.6"),
        Path("/lib64/ld-linux-x86-64.so.2"),
    )


def jcode_prompt_message(prompt_sha: str, context_sha: str) -> str:
    return (
        "Read the immutable SpiritOS executor packet at /workspace/DIAGNOSTIC_TASK.txt. "
        f"Verify SHA-256 {prompt_sha} before acting. Read the immutable context packet at "
        f"/workspace/DIAGNOSTIC_CONTEXT.json and verify SHA-256 {context_sha}. Stay inside "
        "the declared file and tool scope. Do not commit, push, deploy, resume a session, "
        "use memory, use MCP, or claim Proxy terminal success."
    )


def parse_jcode_ndjson(value: str) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    parse_errors: list[dict[str, Any]] = []
    for line_number, line in enumerate(value.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            parse_errors.append({"line": line_number, "error": str(error), "raw": line})
            continue
        if isinstance(event, dict):
            events.append(event)
        else:
            parse_errors.append({"line": line_number, "error": "event_not_object", "raw": line})
    tool_events = [event for event in events if str(event.get("type") or "").startswith("tool_")]
    done_events = [event for event in events if event.get("type") == "done"]
    return {
        "events": events,
        "event_types": [str(event.get("type") or "") for event in events],
        "tool_events": tool_events,
        "done_events": done_events,
        "parse_errors": parse_errors,
    }


def run_jcode_harness(
    task_key: str,
    model: str,
    task_manifest: Mapping[str, Any],
    context: Mapping[str, Any],
    overlay: Path,
    runtime_root: Path,
    run_id: str,
    evidence_root: Path,
    *,
    full_proxy_packet: Mapping[str, Any] | None,
    bridge_mode: BridgeMode,
    capture_only: bool = False,
) -> dict[str, Any]:
    if not JCODE_BINARY.is_file() or sha256_file(JCODE_BINARY) != JCODE_BINARY_SHA256:
        raise PipelineDiagnosisError("jcode_binary_identity_invalid")
    prompt_text = (
        canonical_json(full_proxy_packet)
        if full_proxy_packet is not None
        else concise_task_text(task_manifest) + "\n"
    )
    context_text = canonical_json(context)
    prompt_path = runtime_root / "DIAGNOSTIC_TASK.txt"
    context_path = runtime_root / "DIAGNOSTIC_CONTEXT.json"
    write_text(prompt_path, prompt_text)
    write_text(context_path, context_text)
    prompt_sha = sha256_file(prompt_path)
    context_sha = sha256_file(context_path)

    launcher = runtime_root / "relay-runner"
    compile_relay_launcher(repository_root(), launcher)
    preassembled = runtime_root / "preassembled-root"
    assemble_preassembled_root(
        PreassembledRootConfig(
            root=preassembled,
            executable=JCODE_BINARY,
            runtime_files=jcode_runtime_files(),
            additional_executables=((launcher, "relay-runner"),),
        )
    )
    bridge = DiagnosticBridgeServer(
        runtime_root / "unused-mounted-socket",
        model,
        bridge_mode,
        run_id,
        evidence_root,
        capture_only=capture_only,
    )
    socketpairs = [socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM) for _ in range(MAX_TURNS_PER_RUN)]
    host_sockets = [pair[0] for pair in socketpairs]
    child_sockets = [pair[1] for pair in socketpairs]
    bridge.start_connected(host_sockets)
    port = 18080
    allowed_tools = "read" if task_key == "R" else "read,write,apply_patch"
    message = jcode_prompt_message(prompt_sha, context_sha)
    jcode_command = [
        "/usr/bin/jcode",
        "--cwd",
        "/workspace",
        "--no-update",
        "--no-selfdev",
        "--quiet",
        "--trace",
        "--provider-profile",
        "spiritos-qualification",
        "--model",
        model,
        "--disable-base-tools",
        "--tools",
        allowed_tools,
        "--disabled-tools",
        ",".join(REQUIRED_DENIED_TOOLS),
        "run",
        "--ndjson",
        message,
    ]
    command = [
        "bwrap",
        "--clearenv",
        "--unshare-user",
        "--unshare-pid",
        "--unshare-ipc",
        "--unshare-uts",
        "--unshare-cgroup",
        "--unshare-net",
        "--new-session",
        "--die-with-parent",
        "--cap-drop",
        "ALL",
        "--uid",
        "0",
        "--gid",
        "0",
        "--ro-bind",
        str(preassembled),
        "/",
        "--bind",
        str(overlay),
        "/workspace",
        "--ro-bind",
        str(prompt_path),
        "/workspace/DIAGNOSTIC_TASK.txt",
        "--ro-bind",
        str(context_path),
        "/workspace/DIAGNOSTIC_CONTEXT.json",
    ]
    for read_only in task_manifest["read_only_files"]:
        command.extend(["--ro-bind", str(overlay / read_only), f"/workspace/{read_only}"])
    command.extend(
        [
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
            "--dir",
            "/tmp/jcode-home",
            "--chdir",
            "/workspace",
            "--setenv",
            "PATH",
            "/usr/bin:/bin",
            "--setenv",
            "HOME",
            "/tmp/jcode-home",
            "--setenv",
            "JCODE_HOME",
            "/tmp/jcode-home",
            "--setenv",
            "TMPDIR",
            "/tmp",
            "--setenv",
            "LANG",
            "C",
            "--setenv",
            "LC_ALL",
            "C",
            "--setenv",
            "TZ",
            "UTC",
            "--setenv",
            "DO_NOT_TRACK",
            "1",
            "--setenv",
            "JCODE_ALLOW_COMMIT",
            "0",
            "--setenv",
            "JCODE_ALLOW_DEPLOY",
            "0",
            "--setenv",
            "JCODE_ALLOW_PUSH",
            "0",
            "--setenv",
            "JCODE_AUTO_UPDATE_ENABLED",
            "0",
            "--setenv",
            "JCODE_BROWSER_ENABLED",
            "0",
            "--setenv",
            "JCODE_MEMORY_ENABLED",
            "0",
            "--setenv",
            "JCODE_NETWORK_ENABLED",
            "0",
            "--setenv",
            "JCODE_PERSIST_MEMORY_INJECTIONS",
            "0",
            "--setenv",
            "JCODE_RUN_AUTO_POKE",
            "0",
            "--setenv",
            "JCODE_RUN_MCP",
            "0",
            "--setenv",
            "JCODE_SESSION_RESUME_ENABLED",
            "0",
            "--setenv",
            "JCODE_TELEMETRY_ENABLED",
            "0",
            "--",
            "/usr/bin/relay-runner",
            "--socket",
            "/run/jcode-bridge/inference.sock",
            "--listen-port",
            str(port),
            "--config-path",
            "/tmp/jcode-home/config.toml",
            "--base-url",
            f"http://127.0.0.1:{port}/v1",
            "--model",
            model,
            "--",
            *jcode_command,
        ]
    )
    socket_argument_index = command.index("--socket")
    relay_fd_arguments = [
        value
        for child_socket in child_sockets
        for value in ("--relay-fd", str(child_socket.fileno()))
    ]
    command[socket_argument_index : socket_argument_index + 2] = relay_fd_arguments
    try:
        process = run_supervised_with_socketpairs(
            command,
            child_sockets,
            JCodeSupervisionConfig(timeout_seconds=300, termination_grace_seconds=2),
        )
    finally:
        time.sleep(0.2)
        bridge.close()
    raw_responses = [record.response_body for record in bridge.client.records]
    parsed_stream = parse_jcode_ndjson(str(process["stdout"]))
    done_texts = [str(event.get("text") or "") for event in parsed_stream["done_events"]]
    backend_text = "\n".join(
        str((item.get("message") or {}).get("content") or item.get("response") or "")
        for item in raw_responses
    )
    final_text = done_texts[-1] if done_texts else backend_text
    return {
        "messages": [
            {"role": "jcode_cli_user", "content": message},
            {"role": "prompt_file", "content": prompt_text},
            {"role": "context_file", "content": context_text},
        ],
        "tools": [
            item.get("body", {}).get("tools", []) for item in bridge.provider_requests
        ],
        "turns": len(bridge.client.records),
        "final_text": final_text,
        "raw_response": raw_responses,
        "tool_ledger": parsed_stream["tool_events"],
        "tool_parse": {
            "jcode_stdout_ndjson": process["stdout"],
            "jcode_stderr": process["stderr"],
            "provider_request_count": len(bridge.provider_requests),
            "bridge_errors": bridge.errors,
            "parsed_jcode_stream": parsed_stream,
        },
        "jcode_process": process,
        "jcode_command": jcode_command,
        "containment_command": command,
        "jcode_provider_requests": bridge.provider_requests,
        "jcode_provider_responses": bridge.provider_responses,
        "bridge_transformations": bridge.transformations,
        "backend_model_calls": [record.to_dict() for record in bridge.client.records],
        "registry_receipt": bridge.client.registry_receipt,
        "bridge_mode": bridge_mode,
        "capture_only": capture_only,
        "relay_transport": "supervisor-owned-one-use-socketpairs/v1",
        "prompt_sha256": prompt_sha,
        "context_sha256": context_sha,
    }


def is_runtime_artifact(path: Path, overlay: Path) -> bool:
    relative = path.relative_to(overlay)
    return (
        path.suffix == ".pyc"
        or "__pycache__" in relative.parts
        or ".pytest_cache" in relative.parts
        or relative.as_posix() in {"DIAGNOSTIC_CONTEXT.json", "DIAGNOSTIC_TASK.txt"}
    )


def snapshot_overlay(overlay: Path) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    for path in sorted(item for item in overlay.rglob("*") if item.is_file() and not is_runtime_artifact(item, overlay)):
        relative = path.relative_to(overlay).as_posix()
        raw = path.read_bytes()
        snapshot[relative] = {
            "sha256": sha256_bytes(raw),
            "bytes": len(raw),
            "content": raw.decode("utf-8", errors="replace"),
        }
    return snapshot


def diff_snapshots(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    changed = sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))
    chunks: list[str] = []
    for path in changed:
        old = str((before.get(path) or {}).get("content") or "")
        new = str((after.get(path) or {}).get("content") or "")
        chunks.extend(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
            )
        )
    return {"changed_files": changed, "unified_diff": "".join(chunks)}


def focused_test_result(task_key: str, overlay: Path) -> dict[str, Any]:
    if task_key != "W":
        return {"applicable": False, "exit_code": None, "stdout": "", "stderr": ""}
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "focused_check.py"],
        cwd=overlay,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return {
        "applicable": True,
        "command": f"{sys.executable} -m pytest -q focused_check.py",
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def safe_inline_candidate_passes(text: str) -> bool:
    code = text.strip()
    fenced = re.search(r"```(?:python)?\s*(.*?)```", code, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        code = fenced.group(1).strip()
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False
    allowed_nodes = (
        ast.Module,
        ast.FunctionDef,
        ast.arguments,
        ast.arg,
        ast.Return,
        ast.Call,
        ast.Attribute,
        ast.Name,
        ast.Load,
        ast.Constant,
        ast.Expr,
    )
    if any(not isinstance(node, allowed_nodes) for node in ast.walk(tree)):
        return False
    function = next((node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "normalize_label"), None)
    if function is None:
        return False
    namespace: dict[str, Any] = {}
    exec(compile(tree, "<diagnostic-candidate>", "exec"), {"__builtins__": {}}, namespace)
    candidate = namespace.get("normalize_label")
    return bool(
        callable(candidate)
        and candidate("  Alpha Beta  ") == "alpha-beta"
        and candidate("Already   Spaced") == "already-spaced"
    )


def evaluate_run(
    task_key: str,
    lane: str,
    result: Mapping[str, Any],
    diff: Mapping[str, Any],
    test: Mapping[str, Any],
) -> dict[str, Any]:
    if task_key == "R":
        expected = task_definition(task_key)["expected"]
        text = str(result.get("final_text") or "")
        checks = {key: str(value) in text for key, value in expected.items()}
        passed = all(checks.values()) and not diff["changed_files"]
        return {
            "passed": passed,
            "checks": checks,
            "no_mutation": not diff["changed_files"],
            "classification": "grounded_answer_pass" if passed else "grounded_answer_fail",
        }
    if lane == "A":
        candidate_pass = safe_inline_candidate_passes(str(result.get("final_text") or ""))
        passed = candidate_pass and not diff["changed_files"]
        return {
            "passed": passed,
            "candidate_behavior_pass": candidate_pass,
            "no_applied_mutation": not diff["changed_files"],
            "classification": "inline_patch_capability_pass" if passed else "inline_patch_capability_fail",
        }
    changed = list(diff["changed_files"])
    write_and_independent_test_pass = changed == ["label.py"] and test.get("exit_code") == 0
    tool_ledger = list(result.get("tool_ledger") or [])
    run_test_executions = [
        item
        for item in tool_ledger
        if isinstance(item, Mapping)
        and (item.get("tool_name") == "run_test" or item.get("name") == "run_test")
        and item.get("status") == "completed"
    ]
    task_contract_complete = write_and_independent_test_pass and bool(run_test_executions)
    if lane in {"D", "F"} and write_and_independent_test_pass:
        classification = "tool_write_pass_test_execution_tool_absent"
    else:
        classification = "tool_write_pass" if task_contract_complete else "tool_write_fail"
    return {
        "passed": task_contract_complete,
        "changed_files": changed,
        "focused_test_pass": test.get("exit_code") == 0,
        "write_and_independent_test_pass": write_and_independent_test_pass,
        "model_invoked_required_test_tool": bool(run_test_executions),
        "task_contract_complete": task_contract_complete,
        "classification": classification,
    }


@dataclass
class FreshRunState:
    source_worktree: Path
    overlay: Path
    runtime_root: Path
    base_head: str


def create_fresh_run_state(root: Path, run_id: str, task_key: str) -> FreshRunState:
    safe_run_id = re.sub(r"[^A-Za-z0-9._-]", "_", run_id)
    runtime_root = Path(tempfile.mkdtemp(prefix=f"spiritos-c2j-{safe_run_id}-", dir="/tmp"))
    source_worktree = runtime_root / "source-worktree"
    base_head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    subprocess.run(
        ["git", "-C", str(root), "worktree", "add", "--detach", str(source_worktree), base_head],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    fixture = source_worktree / "source_proxy/tests/fixtures/jcode_pipeline_diagnosis" / task_definition(task_key)["fixture"]
    overlay = runtime_root / "overlay"
    shutil.copytree(fixture, overlay)
    (runtime_root / "home").mkdir(mode=0o700)
    (runtime_root / "jcode-home").mkdir(mode=0o700)
    return FreshRunState(source_worktree, overlay, runtime_root, base_head)


def cleanup_fresh_run_state(root: Path, state: FreshRunState) -> dict[str, Any]:
    resolved_runtime = state.runtime_root.resolve()
    if resolved_runtime.parent != Path("/tmp") or not resolved_runtime.name.startswith("spiritos-c2j-"):
        raise PipelineDiagnosisError("runtime_cleanup_target_invalid")
    remove = subprocess.run(
        ["git", "-C", str(root), "worktree", "remove", "--force", str(state.source_worktree)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    shutil.rmtree(resolved_runtime)
    return {
        "git_worktree_remove_exit_code": remove.returncode,
        "runtime_root_removed": not resolved_runtime.exists(),
    }


def existing_request_count(evidence_root: Path) -> int:
    ledger = evidence_root / "MODEL_REQUEST_LEDGER.ndjson"
    if ledger.is_file():
        total = 0
        for line_number, line in enumerate(ledger.read_text(encoding="utf-8").splitlines(), start=1):
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise PipelineDiagnosisError(f"request_ledger_unreadable:{line_number}") from error
            if event.get("event") == "request_started":
                total += 1
        return total
    total = 0
    runs = evidence_root / "runs"
    if not runs.is_dir():
        return 0
    for receipt in runs.glob("*/evaluation_receipt.json"):
        try:
            total += int(json.loads(receipt.read_text(encoding="utf-8")).get("model_request_count") or 0)
        except (OSError, ValueError, json.JSONDecodeError):
            raise PipelineDiagnosisError(f"request_counter_unreadable:{receipt}")
    return total


def append_request_ledger_event(evidence_root: Path, event: Mapping[str, Any]) -> None:
    evidence_root.mkdir(parents=True, exist_ok=True)
    ledger = evidence_root / "MODEL_REQUEST_LEDGER.ndjson"
    line = canonical_json(dict(event))
    with ledger.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())


def request_ledger_events(evidence_root: Path, run_id: str) -> list[dict[str, Any]]:
    ledger = evidence_root / "MODEL_REQUEST_LEDGER.ndjson"
    if not ledger.is_file():
        return []
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(ledger.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise PipelineDiagnosisError(f"request_ledger_unreadable:{line_number}") from error
        if event.get("run_id") == run_id:
            events.append(event)
            continue
        ledger_id = event.get("ledger_id")
        if event.get("event") == "request_finished" and any(
            prior.get("ledger_id") == ledger_id for prior in events
        ):
            events.append(event)
    return events


def request_journal_entries(evidence_root: Path, run_id: str) -> list[dict[str, Any]]:
    journal_dir = evidence_root / "request-journal"
    if not journal_dir.is_dir():
        return []
    entries: list[dict[str, Any]] = []
    for path in sorted(journal_dir.glob("model-request-*.json")):
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise PipelineDiagnosisError(f"request_journal_unreadable:{path.name}") from error
        if entry.get("run_id") != run_id:
            continue
        raw = base64.b64decode(str(entry.get("request_bytes_base64") or ""), validate=True)
        if sha256_bytes(raw) != entry.get("request_sha256"):
            raise PipelineDiagnosisError(f"request_journal_hash_mismatch:{path.name}")
        if raw != canonical_json(entry.get("request_body")).encode("utf-8"):
            raise PipelineDiagnosisError(f"request_journal_body_mismatch:{path.name}")
        entries.append({**entry, "journal_file": path.name})
    return entries


def write_request_journal_entry(
    evidence_root: Path,
    *,
    ledger_id: str,
    run_id: str,
    model: str,
    endpoint: str,
    request_body: Mapping[str, Any],
    request_bytes: bytes,
) -> tuple[Path, str]:
    expected_bytes = canonical_json(dict(request_body)).encode("utf-8")
    if request_bytes != expected_bytes:
        raise PipelineDiagnosisError("request_journal_noncanonical_body")
    journal_dir = evidence_root / "request-journal"
    journal_dir.mkdir(parents=True, exist_ok=True)
    path = journal_dir / f"{ledger_id}.json"
    entry = {
        "schema_version": "source-proxy.model-request-journal/v1",
        "ledger_id": ledger_id,
        "run_id": run_id,
        "model": model,
        "model_digest": MODEL_SPECS[model]["digest"],
        "endpoint": endpoint,
        "request_body": dict(request_body),
        "request_bytes_base64": base64.b64encode(request_bytes).decode("ascii"),
        "request_sha256": sha256_bytes(request_bytes),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "write_order": "durably_written_before_request_started_ledger_event_and_network_send",
    }
    encoded = canonical_json(entry)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as error:
        raise PipelineDiagnosisError(f"immutable_request_journal_exists:{ledger_id}") from error
    directory_fd = os.open(journal_dir, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    return path, sha256_text(encoded)


def record_model_request_start(
    evidence_root: Path,
    *,
    run_id: str,
    model: str,
    endpoint: str,
    request_body: Mapping[str, Any],
    request_bytes: bytes,
) -> str:
    with _REQUEST_LEDGER_LOCK:
        count = existing_request_count(evidence_root)
        if count >= MODEL_REQUEST_LIMIT:
            raise PipelineDiagnosisError("model_request_budget_exhausted")
        ledger_id = f"model-request-{count + 1:02d}"
        journal_path, journal_sha256 = write_request_journal_entry(
            evidence_root,
            ledger_id=ledger_id,
            run_id=run_id,
            model=model,
            endpoint=endpoint,
            request_body=request_body,
            request_bytes=request_bytes,
        )
        append_request_ledger_event(
            evidence_root,
            {
                "schema_version": "source-proxy.model-request-ledger/v1",
                "event": "request_started",
                "ledger_id": ledger_id,
                "run_id": run_id,
                "model": model,
                "model_digest": MODEL_SPECS[model]["digest"],
                "endpoint": endpoint,
                "request_sha256": sha256_bytes(request_bytes),
                "request_journal": str(journal_path.relative_to(evidence_root)),
                "request_journal_sha256": journal_sha256,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        return ledger_id


def record_model_request_finish(
    evidence_root: Path,
    *,
    ledger_id: str,
    response_sha256: str,
    error: str | None,
) -> None:
    with _REQUEST_LEDGER_LOCK:
        append_request_ledger_event(
            evidence_root,
            {
                "schema_version": "source-proxy.model-request-ledger/v1",
                "event": "request_finished",
                "ledger_id": ledger_id,
                "response_sha256": response_sha256,
                "error": error,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            },
        )


def model_request_capture_receipt(evidence_root: Path, run_id: str) -> dict[str, Any]:
    events = request_ledger_events(evidence_root, run_id)
    starts = [event for event in events if event.get("event") == "request_started"]
    entries = request_journal_entries(evidence_root, run_id)
    journal_ids = {entry.get("ledger_id") for entry in entries}
    missing = [event.get("ledger_id") for event in starts if event.get("ledger_id") not in journal_ids]
    if not starts and not entries:
        status = "NO_MODEL_REQUEST"
    elif len(entries) == len(starts) and not missing:
        status = "COMPLETE"
    else:
        status = "EVIDENCE_INCOMPLETE"
    return {
        "schema_version": "source-proxy.model-request-capture/v1",
        "run_id": run_id,
        "status": status,
        "request_started_count": len(starts),
        "journal_entry_count": len(entries),
        "missing_request_body_ledger_ids": missing,
        "ledger_events": events,
        "journal_entries": entries,
    }


def seal_run_evidence(evidence_dir: Path, files: Mapping[str, Any]) -> None:
    if evidence_dir.exists():
        raise PipelineDiagnosisError(f"immutable_run_evidence_exists:{evidence_dir.name}")
    evidence_dir.mkdir(parents=True)
    for name, value in files.items():
        path = evidence_dir / name
        if isinstance(value, str):
            write_text(path, value)
        else:
            write_json(path, value)
    hashes = {
        path.name: {"sha256": sha256_file(path), "bytes": path.stat().st_size}
        for path in sorted(evidence_dir.iterdir())
        if path.is_file()
    }
    write_json(evidence_dir / "hashes.json", {"schema_version": DIAGNOSIS_SCHEMA, "files": hashes})


def seal_interrupted_run_from_ledger(
    *,
    run_id: str,
    task_key: str,
    lane: str,
    model: str,
    root: Path | None = None,
) -> dict[str, Any]:
    """Seal a fail-closed receipt for a run interrupted before normal evidence sealing."""
    repo = (root or repository_root()).resolve()
    evidence_root = diagnosis_root(repo)
    if lane not in set("ABCDEF") or model not in MODEL_SPECS:
        raise PipelineDiagnosisError("interrupted_run_identity_invalid")
    capture = model_request_capture_receipt(evidence_root, run_id)
    starts = [event for event in capture["ledger_events"] if event.get("event") == "request_started"]
    finishes = [event for event in capture["ledger_events"] if event.get("event") == "request_finished"]
    if not starts or any(event.get("run_id") != run_id for event in starts):
        raise PipelineDiagnosisError("interrupted_run_start_event_missing")
    if any(event.get("model") != model for event in starts):
        raise PipelineDiagnosisError("interrupted_run_model_mismatch")
    if not finishes or not any(event.get("error") for event in finishes):
        raise PipelineDiagnosisError("interrupted_run_failure_event_missing")
    fixture = repo / "source_proxy/tests/fixtures/jcode_pipeline_diagnosis" / task_definition(task_key)["fixture"]
    context = build_context_manifest(task_key, fixture)
    task_manifest = build_task_manifest(task_key, context)
    registry = ExactOllamaClient(
        model,
        run_id=f"{run_id}-receipt-only",
        evidence_root=evidence_root,
    ).registry_receipt
    base_head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    failure = next(str(event.get("error")) for event in reversed(finishes) if event.get("error"))
    evidence_dir = evidence_root / "runs" / run_id
    evidence = {
        "authorization_receipt.json": {
            "authorization_id": AUTHORIZATION_ID,
            "operator_prompt_sha256": AUTHORIZATION_PROMPT_SHA256,
            "authorization_receipt": AUTHORIZATION_RECEIPT,
            "starting_head": base_head,
            "starting_head_status": "reconstructed_at_receipt_seal; run began on this unchanged audit head",
        },
        "task_manifest.json": task_manifest,
        "context_manifest.json": context,
        "model_registry_receipt.json": registry,
        "model_request_capture_receipt.json": capture,
        "exact_model_visible_packet.json": {
            "schema_version": "source-proxy.model-visible-packet/v1",
            "run_id": run_id,
            "task_id": task_manifest["task_id"],
            "lane": lane,
            "model": model,
            "model_digest": MODEL_SPECS[model]["digest"],
            "capture_status": capture["status"],
            "backend_request_sha256": [event.get("request_sha256") for event in starts],
            "backend_requests": [entry.get("request_body") for entry in capture["journal_entries"]],
            "backend_request_bytes_base64": [
                entry.get("request_bytes_base64") for entry in capture["journal_entries"]
            ],
            "evidence_limit": (
                "Exact request body and bytes were not persisted before the timeout; only the "
                "durable request hash and ledger timing survive. No packet was reconstructed."
                if capture["status"] == "EVIDENCE_INCOMPLETE"
                else None
            ),
        },
        "tool_schema.json": {"proposed_minimal_tools": tool_schemas(task_key), "actual": []},
        "raw_model_response.json": {
            "responses": [],
            "backend_calls": [],
            "capture_status": "NO_RESPONSE_BYTES_CAPTURED",
        },
        "tool_parse_receipt.json": {
            "status": "NOT_REACHED_OR_NOT_CAPTURED",
            "reason": failure,
        },
        "tool_ledger.json": {"executions": []},
        "diff_receipt.json": {
            "capture_status": "EVIDENCE_INCOMPLETE",
            "changed_files": None,
            "unified_diff": None,
            "reason": "The fresh overlay was cleaned by the pre-repair finally block before a snapshot was sealed.",
        },
        "evaluation_receipt.json": {
            "schema_version": DIAGNOSIS_SCHEMA,
            "run_id": run_id,
            "task_key": task_key,
            "task_id": task_manifest["task_id"],
            "lane": lane,
            "model": model,
            "model_digest": MODEL_SPECS[model]["digest"],
            "bridge_mode": None,
            "model_request_count": len(starts),
            "evaluation": {
                "passed": False,
                "classification": "diagnostic_run_timeout_evidence_incomplete",
            },
            "failure": failure,
            "evidence_completeness": capture["status"],
            "reconstructed_packet": False,
            "retry_performed": False,
        },
        "packet_noise_receipt.json": {
            "capture_status": "EVIDENCE_INCOMPLETE",
            "reason": "Exact model-visible packet unavailable; metrics intentionally not reconstructed.",
        },
        "instrumentation_erratum.json": {
            "classification": "EVIDENCE_INCOMPLETE",
            "discovered_after_run": True,
            "repair": "Exact request bodies are now journaled durably before network transmission.",
            "scope": "This receipt documents the gap and does not alter or retry the failed run.",
        },
    }
    seal_run_evidence(evidence_dir, evidence)
    return {
        "run_id": run_id,
        "task_key": task_key,
        "lane": lane,
        "model": model,
        "model_request_count": len(starts),
        "passed": False,
        "classification": "diagnostic_run_timeout_evidence_incomplete",
        "evidence_completeness": capture["status"],
        "evidence_dir": str(evidence_dir.relative_to(repo)),
    }


def verify_diagnostic_evidence(root: Path | None = None) -> dict[str, Any]:
    """Verify run seals, request accounting, exact identities, and declared capture gaps."""
    repo = (root or repository_root()).resolve()
    evidence_root = diagnosis_root(repo)
    errors: list[str] = []
    ledger_path = evidence_root / "MODEL_REQUEST_LEDGER.ndjson"
    events: list[dict[str, Any]] = []
    if not ledger_path.is_file():
        errors.append("model_request_ledger_missing")
    else:
        for line_number, line in enumerate(ledger_path.read_text(encoding="utf-8").splitlines(), start=1):
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                errors.append(f"model_request_ledger_invalid_json:{line_number}")
                continue
            if not isinstance(event, dict):
                errors.append(f"model_request_ledger_event_not_object:{line_number}")
                continue
            events.append(event)
    starts = [event for event in events if event.get("event") == "request_started"]
    finishes = [event for event in events if event.get("event") == "request_finished"]
    start_ids = [str(event.get("ledger_id") or "") for event in starts]
    finish_ids = [str(event.get("ledger_id") or "") for event in finishes]
    if len(start_ids) != len(set(start_ids)):
        errors.append("model_request_started_id_duplicate")
    if len(finish_ids) != len(set(finish_ids)):
        errors.append("model_request_finished_id_duplicate")
    if set(start_ids) != set(finish_ids):
        errors.append("model_request_start_finish_mismatch")
    if len(starts) > MODEL_REQUEST_LIMIT:
        errors.append("model_request_budget_exceeded")
    for event in starts:
        model_name = str(event.get("model") or "")
        if model_name not in MODEL_SPECS:
            errors.append(f"model_request_unauthorized_model:{model_name}")
        elif event.get("model_digest") != MODEL_SPECS[model_name]["digest"]:
            errors.append(f"model_request_digest_mismatch:{event.get('ledger_id')}")

    journal_by_id: dict[str, dict[str, Any]] = {}
    journal_dir = evidence_root / "request-journal"
    if journal_dir.is_dir():
        for path in sorted(journal_dir.glob("model-request-*.json")):
            try:
                entry = json.loads(path.read_text(encoding="utf-8"))
                raw = base64.b64decode(str(entry.get("request_bytes_base64") or ""), validate=True)
            except (json.JSONDecodeError, ValueError):
                errors.append(f"request_journal_unreadable:{path.name}")
                continue
            ledger_id = str(entry.get("ledger_id") or "")
            if ledger_id in journal_by_id:
                errors.append(f"request_journal_duplicate:{ledger_id}")
            if sha256_bytes(raw) != entry.get("request_sha256"):
                errors.append(f"request_journal_hash_mismatch:{ledger_id}")
            if raw != canonical_json(entry.get("request_body")).encode("utf-8"):
                errors.append(f"request_journal_body_mismatch:{ledger_id}")
            journal_by_id[ledger_id] = entry

    run_dirs = sorted(path for path in (evidence_root / "runs").glob("*") if path.is_dir())
    run_request_total = 0
    run_request_counts: dict[str, int] = {}
    accepted_capture_gaps: list[dict[str, Any]] = []
    run_ids: set[str] = set()
    for run_dir in run_dirs:
        run_id = run_dir.name
        run_ids.add(run_id)
        hashes_path = run_dir / "hashes.json"
        if not hashes_path.is_file():
            errors.append(f"run_hash_manifest_missing:{run_id}")
            continue
        try:
            hash_manifest = json.loads(hashes_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append(f"run_hash_manifest_invalid:{run_id}")
            continue
        declared = hash_manifest.get("files") if isinstance(hash_manifest.get("files"), dict) else {}
        actual_names = {path.name for path in run_dir.iterdir() if path.is_file() and path.name != "hashes.json"}
        if set(declared) != actual_names:
            errors.append(f"run_hash_manifest_file_set_mismatch:{run_id}")
        for name, metadata in declared.items():
            path = run_dir / name
            if not path.is_file() or not isinstance(metadata, Mapping):
                errors.append(f"run_hash_target_missing:{run_id}:{name}")
                continue
            if sha256_file(path) != metadata.get("sha256") or path.stat().st_size != metadata.get("bytes"):
                errors.append(f"run_hash_mismatch:{run_id}:{name}")
        evaluation_path = run_dir / "evaluation_receipt.json"
        packet_path = run_dir / "exact_model_visible_packet.json"
        if not evaluation_path.is_file() or not packet_path.is_file():
            errors.append(f"run_core_receipt_missing:{run_id}")
            continue
        try:
            evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append(f"run_core_receipt_invalid:{run_id}")
            continue
        if evaluation.get("run_id") != run_id or packet.get("run_id") != run_id:
            errors.append(f"run_identity_mismatch:{run_id}")
        model_name = str(evaluation.get("model") or "")
        if model_name not in MODEL_SPECS or evaluation.get("model_digest") != MODEL_SPECS.get(model_name, {}).get("digest"):
            errors.append(f"run_model_identity_mismatch:{run_id}")
        request_count = int(evaluation.get("model_request_count") or 0)
        run_request_total += request_count
        run_request_counts[run_id] = request_count
        if request_count > MAX_TURNS_PER_RUN:
            errors.append(f"run_turn_budget_exceeded:{run_id}")

    starts_by_run: dict[str, list[dict[str, Any]]] = {}
    for event in starts:
        starts_by_run.setdefault(str(event.get("run_id") or ""), []).append(event)
    for run_id in run_ids:
        if len(starts_by_run.get(run_id, [])) != run_request_counts.get(run_id, 0):
            errors.append(f"run_request_count_mismatch:{run_id}")
    for ledger_id in journal_by_id:
        if ledger_id not in set(start_ids):
            errors.append(f"request_journal_without_ledger_start:{ledger_id}")
    for run_id, run_starts in starts_by_run.items():
        if run_id not in run_ids:
            errors.append(f"request_run_receipt_missing:{run_id}")
            continue
        packet_path = evidence_root / "runs" / run_id / "exact_model_visible_packet.json"
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        hashes = list(packet.get("backend_request_sha256") or [])
        encoded_requests = list(packet.get("backend_request_bytes_base64") or [])
        for start in run_starts:
            ledger_id = str(start.get("ledger_id") or "")
            request_hash = str(start.get("request_sha256") or "")
            exact_request_available = False
            journal = journal_by_id.get(ledger_id)
            if journal is not None:
                exact_request_available = journal.get("request_sha256") == request_hash
            if not exact_request_available:
                for index, observed_hash in enumerate(hashes):
                    if observed_hash != request_hash or index >= len(encoded_requests) or not encoded_requests[index]:
                        continue
                    try:
                        raw = base64.b64decode(str(encoded_requests[index]), validate=True)
                    except ValueError:
                        continue
                    if sha256_bytes(raw) == request_hash:
                        exact_request_available = True
                        break
            if exact_request_available:
                continue
            evaluation = json.loads(
                (evidence_root / "runs" / run_id / "evaluation_receipt.json").read_text(encoding="utf-8")
            )
            erratum = evidence_root / "runs" / run_id / "instrumentation_erratum.json"
            if evaluation.get("evidence_completeness") == "EVIDENCE_INCOMPLETE" and erratum.is_file():
                accepted_capture_gaps.append(
                    {
                        "run_id": run_id,
                        "ledger_id": ledger_id,
                        "request_sha256": request_hash,
                        "classification": "EVIDENCE_INCOMPLETE",
                    }
                )
            else:
                errors.append(f"exact_request_capture_missing:{run_id}:{ledger_id}")

    if run_request_total != len(starts):
        errors.append("run_and_ledger_request_count_mismatch")
    timeout_ids = [
        str(event.get("ledger_id") or "")
        for event in finishes
        if str(event.get("error") or "").startswith("TimeoutError:")
    ]
    return {
        "schema_version": "source-proxy.pipeline-diagnosis-evidence-validation/v1",
        "passed": not errors,
        "errors": errors,
        "run_count": len(run_dirs),
        "model_request_count": len(starts),
        "request_finish_count": len(finishes),
        "request_budget_limit": MODEL_REQUEST_LIMIT,
        "maximum_observed_turns_per_run": max(
            [
                int(
                    json.loads((run_dir / "evaluation_receipt.json").read_text(encoding="utf-8")).get(
                        "model_request_count"
                    )
                    or 0
                )
                for run_dir in run_dirs
                if (run_dir / "evaluation_receipt.json").is_file()
            ],
            default=0,
        ),
        "request_journal_entry_count": len(journal_by_id),
        "accepted_capture_gaps": accepted_capture_gaps,
        "timeout_ledger_ids": timeout_ids,
        "frozen_benchmark_runs": 0,
    }


def run_diagnostic(
    *,
    run_id: str,
    task_key: str,
    lane: str,
    model: str,
    bridge_mode: BridgeMode = "legacy_text_only",
    root: Path | None = None,
) -> dict[str, Any]:
    repo = (root or repository_root()).resolve()
    evidence_root = diagnosis_root(repo)
    if lane not in set("ABCDEF"):
        raise PipelineDiagnosisError(f"unknown_lane:{lane}")
    potential = MAX_TURNS_PER_RUN if lane in {"B", "D", "F"} else 1
    if existing_request_count(evidence_root) + potential > MODEL_REQUEST_LIMIT:
        raise PipelineDiagnosisError("model_request_budget_would_be_exceeded")
    state = create_fresh_run_state(repo, run_id, task_key)
    cleanup: dict[str, Any] = {"runtime_root_removed": False}
    started = time.monotonic()
    context: dict[str, Any] = {}
    task_manifest: dict[str, Any] = {}
    before: dict[str, Any] = {}
    full_proxy: dict[str, Any] | None = None
    client: ExactOllamaClient | None = None
    result: dict[str, Any] = {}
    backend_calls: list[dict[str, Any]] = []
    registry: dict[str, Any] = {}
    try:
        context = build_context_manifest(task_key, state.overlay)
        task_manifest = build_task_manifest(task_key, context)
        before = snapshot_overlay(state.overlay)
        full_proxy = (
            build_full_proxy_packet(task_key, task_manifest, context, state.overlay)
            if lane in {"E", "F"}
            else None
        )
        if lane == "A":
            client = ExactOllamaClient(model, run_id=run_id, evidence_root=evidence_root)
            result = run_direct_inline(task_key, model, task_manifest, context, client)
            backend_calls = [record.to_dict() for record in client.records]
            registry = client.registry_receipt
        elif lane == "B":
            client = ExactOllamaClient(model, run_id=run_id, evidence_root=evidence_root)
            result = run_direct_tool_loop(task_key, model, task_manifest, state.overlay, client)
            backend_calls = [record.to_dict() for record in client.records]
            registry = client.registry_receipt
        elif lane in {"C", "E"}:
            client = ExactOllamaClient(model, run_id=run_id, evidence_root=evidence_root)
            result = run_baseline_harness(
                task_key,
                model,
                task_manifest,
                context,
                state.overlay,
                client,
                full_proxy_packet=full_proxy,
            )
            backend_calls = [record.to_dict() for record in client.records]
            registry = client.registry_receipt
        else:
            result = run_jcode_harness(
                task_key,
                model,
                task_manifest,
                context,
                state.overlay,
                state.runtime_root,
                run_id,
                evidence_root,
                full_proxy_packet=full_proxy,
                bridge_mode=bridge_mode,
            )
            backend_calls = list(result.get("backend_model_calls") or [])
            registry = result.get("registry_receipt") or {}
        after = snapshot_overlay(state.overlay)
        diff = diff_snapshots(before, after)
        test = focused_test_result(task_key, state.overlay)
        evaluation = evaluate_run(task_key, lane, result, diff, test)
        request_capture = model_request_capture_receipt(evidence_root, run_id)
        model_request_count = int(request_capture["request_started_count"])
        if request_capture["status"] != "COMPLETE":
            raise PipelineDiagnosisError("model_request_capture_incomplete")
        if model_request_count != len(backend_calls):
            raise PipelineDiagnosisError("model_request_record_count_mismatch")
        if model_request_count > MAX_TURNS_PER_RUN:
            raise PipelineDiagnosisError("per_run_model_turn_budget_exceeded")
        backend_request_bodies = [item.get("request_body") for item in backend_calls]
        jcode_provider_requests = list(result.get("jcode_provider_requests") or [])
        provider_input_bodies = [
            item.get("body") for item in jcode_provider_requests if isinstance(item.get("body"), Mapping)
        ]
        executor_version = {
            "A": "pipeline-diagnosis-direct-inline/v1",
            "B": "pipeline-diagnosis-native-tool-loop/v1",
            "C": "source-proxy-bounded-agent-loop/current-head",
            "D": JCODE_VERSION,
            "E": "source-proxy-bounded-agent-loop/current-head",
            "F": JCODE_VERSION,
        }[lane]
        system_prompts = [
            str(message.get("content") or "")
            for request in backend_request_bodies
            if isinstance(request, Mapping)
            for message in request.get("messages", [])
            if isinstance(message, Mapping) and message.get("role") == "system"
        ]
        user_prompts = [
            str(message.get("content") or "")
            for request in backend_request_bodies
            if isinstance(request, Mapping)
            for message in request.get("messages", [])
            if isinstance(message, Mapping) and message.get("role") == "user"
        ]
        generated_prompts = [
            str(request.get("prompt") or "")
            for request in backend_request_bodies
            if isinstance(request, Mapping) and "prompt" in request
        ]
        proposed_tools = tool_schemas(task_key)
        backend_tools = [
            list(request.get("tools") or [])
            for request in backend_request_bodies
            if isinstance(request, Mapping)
        ]
        provider_input_tools = [list(request.get("tools") or []) for request in provider_input_bodies]
        if lane in {"D", "F"}:
            tool_schemas_reached_provider_unchanged = bool(provider_input_tools) and all(
                index < len(backend_tools) and value == backend_tools[index]
                for index, value in enumerate(provider_input_tools)
            )
        elif lane == "B":
            tool_schemas_reached_provider_unchanged = bool(backend_tools) and backend_tools[0] == proposed_tools
        else:
            tool_schemas_reached_provider_unchanged = None
        role_order = [
            message.get("role")
            for request in backend_request_bodies
            if isinstance(request, Mapping)
            for message in request.get("messages", [])
            if isinstance(message, Mapping)
        ]
        model_visible = {
            "schema_version": "source-proxy.model-visible-packet/v1",
            "run_id": run_id,
            "task_id": task_manifest["task_id"],
            "lane": lane,
            "model": model,
            "model_registry_id": model,
            "model_digest": MODEL_SPECS[model]["digest"],
            "provider_reported_models": [
                (item.get("response_body") or {}).get("model") for item in backend_calls
            ],
            "jcode_binary_sha256": JCODE_BINARY_SHA256 if lane in {"D", "F"} else None,
            "executor_version": executor_version,
            "context_builder_version": CONTEXT_BUILDER_VERSION,
            "bridge_version": DIAGNOSTIC_BRIDGE_VERSION if lane in {"D", "F"} else None,
            "registry_attestation": registry,
            "messages_or_prompts": result.get("messages") or [],
            "tool_contract": result.get("tools") or [],
            "backend_requests": backend_request_bodies,
            "backend_request_bytes_base64": [item.get("request_bytes_base64") for item in backend_calls],
            "backend_request_sha256": [item.get("request_sha256") for item in backend_calls],
            "role_order": role_order,
            "system_prompts": system_prompts,
            "user_prompts": user_prompts,
            "flattened_generate_prompts": generated_prompts,
            "task_specification": task_manifest,
            "acceptance_criteria": task_manifest["acceptance_criteria"],
            "project_instruction_receipt": {
                "agents_md_model_visible": False,
                "developer_instructions_model_visible": False,
                "jcode_generated_content_captured_in_provider_messages": lane in {"D", "F"},
                "proxy_generated_content": full_proxy,
            },
            "stop_sequences": [
                request.get("stop")
                for request in backend_request_bodies
                if isinstance(request, Mapping) and request.get("stop") is not None
            ],
            "generation_parameters": [
                {
                    "stream": request.get("stream"),
                    "options": request.get("options") or {},
                    "tool_choice": request.get("tool_choice"),
                }
                for request in backend_request_bodies
                if isinstance(request, Mapping)
            ],
            "context": {
                **context,
                "estimated_tokens": max(1, round(int(context["total_bytes"]) / 4)),
                "omitted_files": [],
            },
            "path_consistency": {
                "paths_shown": [item["path"] for item in context["ordered_file_manifest"]],
                "paths_mounted": [item["path"] for item in context["ordered_file_manifest"]],
                "tool_working_directory": "/workspace" if lane in {"D", "F"} else str(state.overlay),
                "consistent": True,
            },
            "tool_protocol": {
                "proposed_minimal_tools": proposed_tools,
                "executor_input_tools": provider_input_tools if lane in {"D", "F"} else result.get("tools") or [],
                "backend_tools": backend_tools,
                "allowed_paths": task_manifest["writable_files"] + task_manifest["read_only_files"],
                "denied_paths": context["excluded_paths"],
                "command_policy": "no command tool" if lane in {"A", "B", "D", "F"} else "existing bounded action contract",
                "tool_choice": [request.get("tool_choice") for request in provider_input_bodies],
                "tools_reached_provider_unchanged": tool_schemas_reached_provider_unchanged,
                "provider_schema": "OpenAI functions translated to Ollama native tools" if lane in {"B", "D", "F"} else "text action contract or no tools",
                "jcode_expected_dialect": "OpenAI-compatible streamed tool_calls" if lane in {"D", "F"} else None,
                "required_test_tool_available": lane == "B",
            },
            "response": {
                "raw_provider_responses": [item.get("response_body") for item in backend_calls],
                "raw_response_bytes_base64": [item.get("response_bytes_base64") for item in backend_calls],
                "response_sha256": [item.get("response_sha256") for item in backend_calls],
                "streamed_deltas": result.get("jcode_provider_responses") or [],
                "parser_decisions": result.get("tool_parse") or {},
                "tool_executions_and_results": result.get("tool_ledger") or [],
                "rejected_tool_calls": [
                    item
                    for item in result.get("tool_ledger") or []
                    if isinstance(item, Mapping) and item.get("status") in {"failed", "blocked", "rejected"}
                ],
                "retries": max(0, int(result.get("turns") or 0) - 1),
                "final_model_claim": result.get("final_text") or "",
            },
        }
        packet_text = canonical_json(full_proxy) if full_proxy is not None else concise_task_text(task_manifest)
        evidence = {
            "authorization_receipt.json": {
                "authorization_id": AUTHORIZATION_ID,
                "operator_prompt_sha256": AUTHORIZATION_PROMPT_SHA256,
                "authorization_receipt": AUTHORIZATION_RECEIPT,
                "starting_head": state.base_head,
            },
            "task_manifest.json": task_manifest,
            "context_manifest.json": context,
            "model_registry_receipt.json": registry,
            "model_request_capture_receipt.json": request_capture,
            "exact_model_visible_packet.json": model_visible,
            "tool_schema.json": {"proposed_minimal_tools": tool_schemas(task_key), "actual": result.get("tools") or []},
            "raw_model_response.json": {"responses": result.get("raw_response") or [], "backend_calls": backend_calls},
            "tool_parse_receipt.json": result.get("tool_parse") or {},
            "tool_ledger.json": {"executions": result.get("tool_ledger") or []},
            "diff_receipt.json": {**diff, "focused_test": test},
            "evaluation_receipt.json": {
                "schema_version": DIAGNOSIS_SCHEMA,
                "run_id": run_id,
                "task_key": task_key,
                "task_id": task_manifest["task_id"],
                "lane": lane,
                "model": model,
                "model_digest": MODEL_SPECS[model]["digest"],
                "bridge_mode": bridge_mode if lane in {"D", "F"} else None,
                "model_request_count": model_request_count,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "evaluation": evaluation,
                "final_text": result.get("final_text") or "",
            },
            "packet_noise_receipt.json": packet_noise_metrics(packet_text, task_manifest),
        }
        if lane in {"D", "F"}:
            evidence["jcode_provider_request.json"] = {"requests": result.get("jcode_provider_requests") or []}
            evidence["jcode_provider_response.json"] = {"responses": result.get("jcode_provider_responses") or []}
            evidence["bridge_transformation_receipt.json"] = {
                "bridge_mode": bridge_mode,
                "transformations": result.get("bridge_transformations") or [],
                "jcode_command": result.get("jcode_command") or [],
                "containment": {
                    "network_namespace_unshared": True,
                    "direct_jcode_to_ollama": False,
                    "fresh_home": True,
                    "fresh_jcode_home": True,
                },
            }
            evidence["jcode_stdout.ndjson"] = str((result.get("jcode_process") or {}).get("stdout") or "")
            evidence["jcode_stderr.txt"] = str((result.get("jcode_process") or {}).get("stderr") or "")
        evidence_dir = evidence_root / "runs" / run_id
        seal_run_evidence(evidence_dir, evidence)
        summary = {
            "run_id": run_id,
            "task_key": task_key,
            "lane": lane,
            "model": model,
            "model_request_count": model_request_count,
            "passed": evaluation["passed"],
            "classification": evaluation["classification"],
            "evidence_dir": str(evidence_dir.relative_to(repo)),
        }
    except Exception as error:
        failure = f"{type(error).__name__}:{error}"
        if client is not None:
            backend_calls = [record.to_dict() for record in client.records]
            registry = client.registry_receipt
        request_capture = model_request_capture_receipt(evidence_root, run_id)
        model_request_count = int(request_capture["request_started_count"])
        if model_request_count > MAX_TURNS_PER_RUN:
            raise PipelineDiagnosisError("failed_run_turn_budget_exceeded") from error
        if not context:
            context = build_context_manifest(task_key, state.overlay)
        if not task_manifest:
            task_manifest = build_task_manifest(task_key, context)
        if before:
            after = snapshot_overlay(state.overlay)
            diff: dict[str, Any] = diff_snapshots(before, after)
            diff["capture_status"] = "COMPLETE"
        else:
            diff = {
                "capture_status": "EVIDENCE_INCOMPLETE",
                "changed_files": None,
                "unified_diff": None,
                "reason": "Failure occurred before the baseline overlay snapshot completed.",
            }
        test = focused_test_result(task_key, state.overlay)
        capture_status = (
            "COMPLETE"
            if request_capture["status"] in {"COMPLETE", "NO_MODEL_REQUEST"}
            and diff["capture_status"] == "COMPLETE"
            else "EVIDENCE_INCOMPLETE"
        )
        classification = (
            "diagnostic_run_error"
            if capture_status == "COMPLETE"
            else "diagnostic_run_error_evidence_incomplete"
        )
        journal_entries = list(request_capture["journal_entries"])
        backend_request_bodies = [entry.get("request_body") for entry in journal_entries]
        packet_text = canonical_json(full_proxy) if full_proxy is not None else concise_task_text(task_manifest)
        evidence = {
            "authorization_receipt.json": {
                "authorization_id": AUTHORIZATION_ID,
                "operator_prompt_sha256": AUTHORIZATION_PROMPT_SHA256,
                "authorization_receipt": AUTHORIZATION_RECEIPT,
                "starting_head": state.base_head,
            },
            "task_manifest.json": task_manifest,
            "context_manifest.json": context,
            "model_registry_receipt.json": registry,
            "model_request_capture_receipt.json": request_capture,
            "exact_model_visible_packet.json": {
                "schema_version": "source-proxy.model-visible-packet/v1",
                "run_id": run_id,
                "task_id": task_manifest["task_id"],
                "lane": lane,
                "model": model,
                "model_registry_id": model,
                "model_digest": MODEL_SPECS[model]["digest"],
                "jcode_binary_sha256": JCODE_BINARY_SHA256 if lane in {"D", "F"} else None,
                "executor_version": "failed_before_normal_receipt",
                "context_builder_version": CONTEXT_BUILDER_VERSION,
                "bridge_version": DIAGNOSTIC_BRIDGE_VERSION if lane in {"D", "F"} else None,
                "registry_attestation": registry,
                "capture_status": capture_status,
                "backend_requests": backend_request_bodies,
                "backend_request_bytes_base64": [
                    entry.get("request_bytes_base64") for entry in journal_entries
                ],
                "backend_request_sha256": [entry.get("request_sha256") for entry in journal_entries],
                "task_specification": task_manifest,
                "acceptance_criteria": task_manifest["acceptance_criteria"],
                "context": context,
                "failure": failure,
            },
            "tool_schema.json": {
                "proposed_minimal_tools": tool_schemas(task_key),
                "actual": result.get("tools") or [],
            },
            "raw_model_response.json": {
                "responses": result.get("raw_response") or [],
                "backend_calls": backend_calls,
                "capture_status": "COMPLETE" if backend_calls else "NO_RESPONSE_CAPTURED",
            },
            "tool_parse_receipt.json": result.get("tool_parse")
            or {"status": "NOT_REACHED", "reason": failure},
            "tool_ledger.json": {"executions": result.get("tool_ledger") or []},
            "diff_receipt.json": {**diff, "focused_test": test},
            "evaluation_receipt.json": {
                "schema_version": DIAGNOSIS_SCHEMA,
                "run_id": run_id,
                "task_key": task_key,
                "task_id": task_manifest["task_id"],
                "lane": lane,
                "model": model,
                "model_digest": MODEL_SPECS[model]["digest"],
                "bridge_mode": bridge_mode if lane in {"D", "F"} else None,
                "model_request_count": model_request_count,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "evaluation": {"passed": False, "classification": classification},
                "failure": failure,
                "evidence_completeness": capture_status,
                "retry_performed": False,
            },
            "packet_noise_receipt.json": packet_noise_metrics(packet_text, task_manifest),
            "failure_receipt.json": {
                "failure": failure,
                "exception_type": type(error).__name__,
                "capture_status": capture_status,
                "cleanup_pending_at_seal": True,
            },
        }
        if lane in {"D", "F"}:
            evidence["jcode_provider_request.json"] = {
                "requests": result.get("jcode_provider_requests") or []
            }
            evidence["jcode_provider_response.json"] = {
                "responses": result.get("jcode_provider_responses") or []
            }
            evidence["bridge_transformation_receipt.json"] = {
                "bridge_mode": bridge_mode,
                "transformations": result.get("bridge_transformations") or [],
                "capture_status": capture_status,
            }
            evidence["jcode_stdout.ndjson"] = str(
                (result.get("jcode_process") or {}).get("stdout") or ""
            )
            evidence["jcode_stderr.txt"] = str(
                (result.get("jcode_process") or {}).get("stderr") or ""
            )
        evidence_dir = evidence_root / "runs" / run_id
        seal_run_evidence(evidence_dir, evidence)
        summary = {
            "run_id": run_id,
            "task_key": task_key,
            "lane": lane,
            "model": model,
            "model_request_count": model_request_count,
            "passed": False,
            "classification": classification,
            "evidence_completeness": capture_status,
            "failure": failure,
            "evidence_dir": str(evidence_dir.relative_to(repo)),
        }
    finally:
        cleanup = cleanup_fresh_run_state(repo, state)
    if not cleanup["runtime_root_removed"]:
        raise PipelineDiagnosisError("runtime_cleanup_incomplete")
    return summary


def seal_jcode_capture_preflight(root: Path | None = None) -> dict[str, Any]:
    repo = (root or repository_root()).resolve()
    evidence_root = diagnosis_root(repo)
    request_count_before = existing_request_count(evidence_root)
    cells: list[dict[str, Any]] = []
    for model in MODEL_SPECS:
        for task_key in ("R", "W"):
            run_id = f"preflight-{task_key.lower()}-{model.rsplit(':', 1)[-1]}"
            state = create_fresh_run_state(repo, run_id, task_key)
            cleanup: dict[str, Any] = {"runtime_root_removed": False}
            try:
                context = build_context_manifest(task_key, state.overlay)
                task_manifest = build_task_manifest(task_key, context)
                result = run_jcode_harness(
                    task_key,
                    model,
                    task_manifest,
                    context,
                    state.overlay,
                    state.runtime_root,
                    run_id,
                    evidence_root,
                    full_proxy_packet=None,
                    bridge_mode="legacy_text_only",
                    capture_only=True,
                )
                requests = list(result["jcode_provider_requests"])
                if len(requests) != 1 or result["backend_model_calls"]:
                    raise PipelineDiagnosisError(
                        "capture_preflight_request_count_invalid:"
                        + canonical_json(
                            {
                                "run_id": run_id,
                                "provider_request_count": len(requests),
                                "backend_model_call_count": len(result["backend_model_calls"]),
                                "process": result["jcode_process"],
                                "bridge_errors": result["tool_parse"]["bridge_errors"],
                            }
                        ).strip()
                    )
                body = requests[0]["body"]
                observed_tools = [
                    str((item.get("function") or {}).get("name") or "")
                    for item in body.get("tools", [])
                    if isinstance(item, Mapping)
                ]
                expected_tools = ["read"] if task_key == "R" else ["apply_patch", "read", "write"]
                cell = {
                    "run_id": run_id,
                    "task_key": task_key,
                    "model": model,
                    "model_digest": MODEL_SPECS[model]["digest"],
                    "registry_receipt": result["registry_receipt"],
                    "jcode_binary_sha256": JCODE_BINARY_SHA256,
                    "jcode_version": JCODE_VERSION,
                    "process": result["jcode_process"],
                    "provider_request": requests[0],
                    "provider_response": result["jcode_provider_responses"],
                    "roles": [
                        item.get("role") for item in body.get("messages", []) if isinstance(item, Mapping)
                    ],
                    "observed_tools": observed_tools,
                    "expected_tools": expected_tools,
                    "tool_set_matches": sorted(observed_tools) == sorted(expected_tools),
                    "model_binding_matches": body.get("model") == model,
                    "direct_jcode_to_ollama": False,
                    "real_model_requests": 0,
                }
                if (
                    cell["process"]["status"] != "completed"
                    or cell["process"]["process_exit_code"] != 0
                    or not cell["tool_set_matches"]
                    or not cell["model_binding_matches"]
                ):
                    raise PipelineDiagnosisError(f"capture_preflight_failed:{run_id}")
                cells.append(cell)
            finally:
                cleanup = cleanup_fresh_run_state(repo, state)
            if not cleanup["runtime_root_removed"]:
                raise PipelineDiagnosisError("capture_preflight_cleanup_incomplete")
    request_count_after = existing_request_count(evidence_root)
    if request_count_after != request_count_before:
        raise PipelineDiagnosisError("capture_preflight_spent_model_request")
    receipt: dict[str, Any] = {
        "schema_version": "source-proxy.jcode-packet-capture-preflight/v1",
        "authorization_id": AUTHORIZATION_ID,
        "repository_head": subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True
        ).strip(),
        "cells": cells,
        "real_model_requests": 0,
        "model_request_count_before": request_count_before,
        "model_request_count_after": request_count_after,
        "passed": True,
    }
    receipt["receipt_sha256"] = sha256_text(canonical_json(receipt))
    write_json(evidence_root / "JCODE_PACKET_CAPTURE_PREFLIGHT.json", receipt)
    return receipt


def seal_matrix_manifest(root: Path | None = None) -> dict[str, Any]:
    repo = (root or repository_root()).resolve()
    fixture_root = repo / "source_proxy/tests/fixtures/jcode_pipeline_diagnosis"
    fixtures: dict[str, Any] = {}
    for task_key, task in TASK_DEFINITIONS.items():
        directory = fixture_root / task["fixture"]
        files = ordered_file_manifest(directory)
        fixtures[task_key] = {
            "task_id": task["task_id"],
            "task_sha256": sha256_text(str(task["task"])),
            "files": [{key: item[key] for key in ("path", "sha256", "bytes")} for item in files],
            "fixture_tree_sha256": sha256_text(canonical_json(files)),
        }
    run_plan = [
        {
            "stage": 1,
            "task": "R",
            "lane": lane,
            "model": model,
            "bridge_mode": "legacy_text_only" if lane in {"D", "F"} else None,
        }
        for model in MODEL_SPECS
        for lane in "ABCDEF"
    ]
    run_plan.extend(
        {
            "stage": 2,
            "task": "W",
            "lane": lane,
            "model": model,
            "bridge_mode": "legacy_text_only" if lane in {"D", "F"} else None,
        }
        for model in MODEL_SPECS
        for lane in "ABDF"
    )
    manifest: dict[str, Any] = {
        "schema_version": "source-proxy.campaign-2j-diagnostic-matrix/v1",
        "authorization_id": AUTHORIZATION_ID,
        "operator_prompt_sha256": AUTHORIZATION_PROMPT_SHA256,
        "repository_head": subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip(),
        "models": MODEL_SPECS,
        "fixtures": fixtures,
        "run_plan": run_plan,
        "confirmation_plan": {
            "maximum_runs": 4,
            "global_correction_candidate": "Preserve messages and native tool schemas through the compatibility bridge using Ollama /api/chat.",
            "selection_after_stage_2": True,
        },
        "budgets": {
            "maximum_real_model_requests": MODEL_REQUEST_LIMIT,
            "maximum_turns_per_run": MAX_TURNS_PER_RUN,
            "frozen_benchmark_runs": 0,
        },
        "immutable": True,
    }
    manifest["manifest_sha256"] = sha256_text(canonical_json(manifest))
    write_json(diagnosis_root(repo) / "DIAGNOSTIC_MATRIX_MANIFEST.json", manifest)
    return manifest
