from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from source_proxy.sandbox.bubblewrap import (
    BubblewrapConfig,
    BubblewrapUnavailable,
    run_bubblewrap,
)
from source_proxy.terminal_presets import terminal_command_presets_payload

router = APIRouter(prefix="/v1/sandbox")


class SandboxTerminalRequest(BaseModel):
    command: list[str] = Field(min_length=1, max_length=32)
    session_id: str | None = Field(default=None, min_length=1, max_length=80)
    session_kind: Literal["test_run", "coding_task", "log_output", "command_history"] = "command_history"
    session_label: str | None = Field(default=None, max_length=120)
    timeout_seconds: int = Field(default=30, ge=1, le=30)
    network_policy: Literal["none", "trusted_command"] = "none"


@dataclass
class TerminalHistoryEntry:
    command: list[str]
    network_policy: str
    returncode: int | None
    stderr_tail: str
    stdout_tail: str
    timeout_seconds: int
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def as_payload(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "network_policy": self.network_policy,
            "returncode": self.returncode,
            "stderr_tail": self.stderr_tail,
            "stdout_tail": self.stdout_tail,
            "timeout_seconds": self.timeout_seconds,
            "timestamp": self.timestamp,
        }


@dataclass
class TerminalSession:
    id: str
    kind: str
    label: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    history: list[TerminalHistoryEntry] = field(default_factory=list)

    def append(self, entry: TerminalHistoryEntry) -> None:
        self.history.append(entry)
        self.history = self.history[-50:]
        self.updated_at = entry.timestamp

    def as_payload(self, *, include_history: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "command_count": len(self.history),
            "last_command": self.history[-1].as_payload() if self.history else None,
            "writes_allowed": False,
            "approval_required_for_apply": True,
        }
        if include_history:
            payload["history"] = [entry.as_payload() for entry in self.history]
        return payload


_terminal_sessions: dict[str, TerminalSession] = {}


def _tail(text: str, limit: int = 4000) -> str:
    return text[-limit:] if len(text) > limit else text


def _session_label(command: list[str], provided: str | None) -> str:
    label = (provided or "").strip()
    if label:
        return label
    return " ".join(command[:4])[:120] or "sandbox command"


def _get_or_create_session(request: SandboxTerminalRequest) -> TerminalSession:
    session_id = (request.session_id or "").strip() or f"term_{uuid4().hex[:12]}"
    existing = _terminal_sessions.get(session_id)
    if existing is not None:
        return existing
    session = TerminalSession(
        id=session_id,
        kind=request.session_kind,
        label=_session_label(request.command, request.session_label),
    )
    _terminal_sessions[session_id] = session
    return session


@router.get("/terminal/sessions")
async def sandbox_terminal_sessions() -> dict[str, Any]:
    sessions = sorted(_terminal_sessions.values(), key=lambda session: session.updated_at, reverse=True)
    return {
        "tool": "sandbox_terminal_sessions",
        "write_actions_enabled": False,
        "sessions": [session.as_payload(include_history=False) for session in sessions],
    }


@router.get("/terminal/sessions/{session_id}")
async def sandbox_terminal_session_detail(session_id: str) -> dict[str, Any]:
    session = _terminal_sessions.get(session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "Terminal session not found.", "reason_code": "terminal_session_not_found"},
        )
    return {
        "tool": "sandbox_terminal_session_detail",
        "write_actions_enabled": False,
        "session": session.as_payload(include_history=True),
    }


@router.get("/terminal/presets")
async def sandbox_terminal_presets() -> dict[str, Any]:
    return {
        "tool": "sandbox_terminal_presets",
        "write_actions_enabled": False,
        "presets": terminal_command_presets_payload(),
    }


@router.post("/terminal/run")
async def sandbox_terminal_run(request: SandboxTerminalRequest) -> dict[str, Any]:
    session = _get_or_create_session(request)
    try:
        result = run_bubblewrap(
            request.command,
            BubblewrapConfig(
                workspace=Path.cwd(),
                network_policy=request.network_policy,
            ),
            timeout_seconds=request.timeout_seconds,
        )
    except BubblewrapUnavailable as error:
        raise HTTPException(
            status_code=503,
            detail={
                "error": str(error),
                "reason_code": "bubblewrap_unavailable",
            },
        ) from error
    except subprocess.TimeoutExpired as error:
        session.append(
            TerminalHistoryEntry(
                command=request.command,
                network_policy=request.network_policy,
                returncode=None,
                stderr_tail="Sandboxed command timed out.",
                stdout_tail="",
                timeout_seconds=request.timeout_seconds,
            )
        )
        raise HTTPException(
            status_code=408,
            detail={
                "error": "Sandboxed command timed out.",
                "reason_code": "sandbox_timeout",
                "timeout_seconds": request.timeout_seconds,
                "command": request.command,
            },
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail={
                "error": str(error),
                "reason_code": "invalid_sandbox_request",
            },
        ) from error

    session.append(
        TerminalHistoryEntry(
            command=request.command,
            network_policy=request.network_policy,
            returncode=result.returncode,
            stderr_tail=_tail(result.stderr),
            stdout_tail=_tail(result.stdout),
            timeout_seconds=request.timeout_seconds,
        )
    )

    return {
        "tool": "sandbox_terminal_run",
        "access_scope": "bubblewrap_sandboxed_terminal",
        "command": request.command,
        "returncode": result.returncode,
        "session": session.as_payload(include_history=True),
        "session_id": session.id,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "sandbox": {
            "workspace_mount": "/workspace",
            "workspace_writable": False,
            "home_hidden": True,
            "network_policy": request.network_policy,
            "timeout_seconds": request.timeout_seconds,
        },
    }
