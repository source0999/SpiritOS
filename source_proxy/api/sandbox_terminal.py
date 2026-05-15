from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from source_proxy.sandbox.bubblewrap import (
    BubblewrapConfig,
    BubblewrapUnavailable,
    run_bubblewrap,
)

router = APIRouter(prefix="/v1/sandbox")


class SandboxTerminalRequest(BaseModel):
    command: list[str] = Field(min_length=1, max_length=32)
    timeout_seconds: int = Field(default=30, ge=1, le=30)
    network_policy: Literal["none", "trusted_command"] = "none"


@router.post("/terminal/run")
async def sandbox_terminal_run(request: SandboxTerminalRequest) -> dict[str, Any]:
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

    return {
        "tool": "sandbox_terminal_run",
        "access_scope": "bubblewrap_sandboxed_terminal",
        "command": request.command,
        "returncode": result.returncode,
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
