from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass
from typing import Any, Sequence

from source_proxy.diagnostics.status_codes import FailureClass


@dataclass(frozen=True)
class ProcessAdapterRequest:
    adapter_id: str
    command: tuple[str, ...]
    cwd: str | None = None
    timeout_seconds: float | None = None
    attempt: int = 1
    owner: str = "source_proxy"
    evidence_ref: str = ""
    failure_class: FailureClass = FailureClass.TOOL_FAILURE

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["command"] = list(self.command)
        payload["failure_class"] = self.failure_class.value
        return payload


@dataclass(frozen=True)
class ProcessAdapterResult:
    request: ProcessAdapterRequest
    returncode: int
    stdout: str
    stderr: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": self.request.to_dict(),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "status": self.status,
        }


def run_process_adapter(
    *,
    adapter_id: str,
    command: Sequence[str],
    cwd: str | None = None,
    timeout_seconds: float | None = None,
    attempt: int = 1,
    owner: str = "source_proxy",
    evidence_ref: str = "",
    failure_class: FailureClass = FailureClass.TOOL_FAILURE,
) -> ProcessAdapterResult:
    request = ProcessAdapterRequest(
        adapter_id=adapter_id,
        command=tuple(str(part) for part in command),
        cwd=cwd,
        timeout_seconds=timeout_seconds,
        attempt=attempt,
        owner=owner,
        evidence_ref=evidence_ref,
        failure_class=failure_class,
    )
    completed = subprocess.run(
        list(request.command),
        cwd=request.cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=request.timeout_seconds,
    )
    return ProcessAdapterResult(
        request=request,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        status="used" if completed.returncode == 0 else "failed",
    )
