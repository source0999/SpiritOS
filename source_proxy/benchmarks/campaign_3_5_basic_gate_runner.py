"""Authenticated Campaign 3.5 Basic Backend 10 scoring harness.

The scorer deliberately drives the HTTP production lifecycle.  It never calls
the target adapter, planner, coder, reviewer, verifier, or oracle in-process.
Fixture construction and the final private evaluation are benchmark-owned
operations; the latter runs in a separate restricted container after the
Source Proxy service for the task has stopped.
"""
from __future__ import annotations

import argparse
import ast
import base64
import contextlib
import hashlib
import hmac
import importlib.metadata
import json
import os
import re
import secrets
import shutil
import signal
import socket
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

from source_proxy.benchmarks.campaign_3_5_basic_assets.catalog import (
    EXPECTED_TASK_IDS,
    BasicBackendTask,
    RenderedBasicBackendTask,
    load_basic_backend_tasks,
    render_basic_backend_task,
    validate_public_contract,
)
from source_proxy.benchmarks.campaign_3_5_basic_assets.fixtures import (
    BasicBackendFixture,
    materialize_basic_backend_fixture,
)
from source_proxy.benchmarks.campaign_3_5_basic_assets.seeding import (
    BasicBackendRunSeed,
)
from source_proxy.benchmarks.campaign_3_5_fixture_authority import ENV_MANIFEST
from source_proxy.coding.proof import derive_production_proof
from source_proxy.target_plugins.selection import (
    GENERIC_WORKSPACE_PLUGIN_ID,
    GENERIC_WORKSPACE_PROMPT_ID,
)


REPORT_SCHEMA = "source-proxy-basic-backend-10-gate-report/v1"
TASK_RECEIPT_SCHEMA = "source-proxy-basic-backend-10-task-receipt/v1"
TRACE_SCHEMA = "source-proxy-basic-backend-10-trace-reconciliation/v1"
PHASE_MANIFEST_SCHEMA = "source-proxy-basic-backend-10-phase-manifest/v1"
DEFINITION_VERSION = "source_proxy_basic_backend_10_v1"
PHASES = ("first", "clean_rerun")
MANDATORY_TASKS = frozenset({"BT01", "BT02", "BT04", "BT05"})
MAX_ATTEMPTS = 3
ACTION = "Apply the exact model-authored diff to the server-owned disposable backend fixture."
TARGET_PLUGIN_SCHEMA_VERSION = "spiritos-target-plugin/v1"
GENERIC_WORKSPACE_CONTEXT_ID = "server-scoped-architect-context"
GENERIC_WORKSPACE_PROFILE = "generic-architect-coder-packet-v1"
CONTROL_TRACE_MAP = Path("benchmarks/coder-backend-100/v1.1/trace-event-contract-map.json")
_EVALUATION_PRODUCTION_ROOTS = (Path("source_proxy"),)
_EVALUATION_RUNTIME_CONFIG_ROOTS = (
    Path("packages/contracts"),
    Path("config"),
)
_EVALUATION_RUNTIME_CONFIG_FILES = (
    Path(".python-version"),
    Path("requirements.txt"),
    Path("requirements.core.txt"),
    Path("requirements.cuda.txt"),
    Path("repomix.config.json"),
    Path("repomix.repo-map.config.json"),
    Path("repomix.source-proxy-min.config.json"),
    Path("scripts/run-campaign-3-5-basic-backend-gate.py"),
    Path("scripts/validate-campaign-3-5-basic-backend-gate.py"),
)
_EVALUATION_COMPONENT_EXCLUDED_PREFIXES = (
    Path("source_proxy/tests"),
    Path("source_proxy/cartographer/soak-logs"),
)
_EVALUATION_COMPONENT_EXCLUDED_PARTS = frozenset(
    {"__pycache__", ".pytest_cache"}
)
_EVALUATION_COMPONENT_EXCLUDED_SUFFIXES = frozenset({".pyc", ".pyo"})
_OPERATOR_TASK_ID = "campaign-3.5:model-call-authority"
_OPERATOR_PREVIEW_ID = "campaign-3.5:model-call-authority:issue"
_OPERATOR_ASSERTION_HEADER = "x-spiritos-operator-assertion"
_PRIVATE_MARKERS = (
    "expected_patch",
    "hidden_check",
    "known-good reference",
    "private_oracle",
    "reference implementation",
)
_FORBIDDEN_PRODUCTION_IMPORT_PREFIXES = (
    "source_proxy.benchmarks.campaign_3_5_basic_assets",
    "source_proxy.benchmarks.campaign_3_5_basic_gate_runner",
)
_VERIFIER_RUNTIME_DISTRIBUTIONS = (
    "pytest",
    "pluggy",
    "iniconfig",
    "packaging",
    "pygments",
    "fastapi",
    "uvicorn",
    "starlette",
    "pydantic",
    "httpx",
    "httpcore",
    "anyio",
    "litellm",
)
_IMPORT_AUDIT_SITECUSTOMIZE = '''\
from __future__ import annotations
import atexit
import json
import os
import signal
import sys

_log_path = os.environ["SOURCE_PROXY_GATE_IMPORT_AUDIT_LOG"]
_owner_path = os.environ["SOURCE_PROXY_GATE_IMPORT_AUDIT_OWNER"]
_prefixes = tuple(
    value for value in os.environ["SOURCE_PROXY_GATE_FORBIDDEN_IMPORT_PREFIXES"].split(";")
    if value
)

try:
    _owner_fd = os.open(_owner_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
except FileExistsError:
    _is_owner = False
else:
    _is_owner = True
    os.write(_owner_fd, str(os.getpid()).encode("ascii"))
    os.fsync(_owner_fd)
    os.close(_owner_fd)

def _write(payload):
    with open(_log_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\\n")
        handle.flush()
        os.fsync(handle.fileno())

def _audit(event, args):
    if event != "import" or not args:
        return
    module = str(args[0] or "")
    if any(module == prefix or module.startswith(prefix + ".") for prefix in _prefixes):
        _write({"event": "forbidden_import", "module": module})

_completed = False

def _complete(reason="atexit"):
    global _completed
    if not _is_owner or _completed:
        return
    loaded = sorted(
        name for name in sys.modules
        if any(name == prefix or name.startswith(prefix + ".") for prefix in _prefixes)
    )
    _write({"event": "hook_completed", "forbidden_loaded": loaded, "pid": os.getpid(), "reason": reason})
    _completed = True

if _is_owner:
    sys.addaudithook(_audit)
    atexit.register(_complete)
    if hasattr(signal, "SIGUSR1"):
        signal.signal(signal.SIGUSR1, lambda _signum, _frame: _complete("supervisor_snapshot"))
    _write({"event": "hook_started", "pid": os.getpid()})
else:
    # Inherited helper interpreters contribute forbidden-import findings but
    # cannot create competing lifecycle records or final module snapshots.
    sys.addaudithook(_audit)
'''


class BasicBackendGateError(RuntimeError):
    """A harness invariant failed before a truthful score could be produced."""

    def __init__(self, reason_code: str, details: Mapping[str, Any] | None = None):
        super().__init__(reason_code)
        self.reason_code = reason_code
        self.details = dict(details or {})


@dataclass(frozen=True)
class HttpExchange:
    ordinal: int
    method: str
    path: str
    status_code: int
    request_sha256: str
    response_sha256: str
    response: Mapping[str, Any]
    evidence_file: str
    authenticated: bool
    elapsed_ms: int
    authentication: Mapping[str, Any] = field(default_factory=dict)
    request: Mapping[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def public_payload(self) -> dict[str, Any]:
        return {
            "ordinal": self.ordinal,
            "method": self.method,
            "path": self.path,
            "status_code": self.status_code,
            "request_sha256": self.request_sha256,
            "response_sha256": self.response_sha256,
            "evidence_file": self.evidence_file,
            "authenticated": self.authenticated,
            "authentication": dict(self.authentication),
            "elapsed_ms": self.elapsed_ms,
        }


class GateHttpClient(Protocol):
    exchanges: list[HttpExchange]

    def request(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
        *,
        headers: Mapping[str, str] | None = None,
        allow_error: bool = False,
        authenticated: bool = False,
    ) -> HttpExchange: ...


@dataclass(frozen=True)
class ServiceLaunchSpec:
    source_root: Path
    fixture: BasicBackendFixture
    authority_manifest_path: Path
    state_root: Path
    evidence_root: Path
    python_executable: Path
    expected_branch: str
    expected_head: str
    sandbox_image_id: str
    model_inventory_sha256: str
    verifier_runtime_sha256: str
    task_label: str
    startup_timeout_seconds: float
    request_timeout_seconds: float
    inherited_environment: Mapping[str, str] = field(default_factory=dict)


@dataclass
class RunningGateService:
    client: GateHttpClient
    signer: "OperatorAssertionSigner"
    process_receipt: Mapping[str, Any]


class GateServiceFactory(Protocol):
    def __call__(self, spec: ServiceLaunchSpec) -> contextlib.AbstractContextManager[RunningGateService]: ...


class OracleRunner(Protocol):
    def __call__(
        self,
        *,
        task_id: str,
        workspace_root: Path,
        values: Mapping[str, str | int],
        private_store: Path,
        source_root: Path,
        python_executable: Path,
        inherited_environment: Mapping[str, str],
    ) -> Mapping[str, Any]: ...


@dataclass(frozen=True)
class BasicBackendGateConfig:
    source_root: Path
    output_root: Path
    python_executable: Path
    expected_branch: str = "codex/campaign-3-5-execution-20260719"
    expected_head: str | None = None
    phases: tuple[str, ...] = ("first",)
    resume_first: Path | None = None
    startup_timeout_seconds: float = 45.0
    request_timeout_seconds: float = 360.0
    sandbox_image: str = "scout-scout-api:latest"
    retain_workspaces: bool = True

    def normalized(self) -> "BasicBackendGateConfig":
        source = self.source_root.expanduser().resolve(strict=True)
        # Preserve the venv launcher spelling.  Resolving its ``python``
        # symlink to /usr/bin/python discards the adjacent pyvenv.cfg and can
        # silently launch a runtime without Source Proxy's dependencies.
        python = Path(os.path.abspath(self.python_executable.expanduser()))
        output = self.output_root.expanduser().resolve(strict=False)
        if not (source / ".git").exists() or not (source / "source_proxy").is_dir():
            raise BasicBackendGateError("basic_gate_source_root_invalid")
        if not python.is_file():
            raise BasicBackendGateError("basic_gate_python_invalid")
        if output == source or source in output.parents:
            raise BasicBackendGateError("basic_gate_output_inside_source_worktree")
        if tuple(self.phases) not in {("first",), ("clean_rerun",)}:
            raise BasicBackendGateError("basic_gate_phase_invalid")
        resume_first = (
            self.resume_first.expanduser().resolve(strict=True)
            if self.resume_first is not None
            else None
        )
        if tuple(self.phases) == ("clean_rerun",) and resume_first is None:
            raise BasicBackendGateError("basic_gate_resume_first_required")
        if resume_first is not None and tuple(self.phases) != ("clean_rerun",):
            raise BasicBackendGateError("basic_gate_resume_first_phase_invalid")
        return BasicBackendGateConfig(
            source_root=source,
            output_root=output,
            python_executable=python,
            expected_branch=self.expected_branch,
            expected_head=self.expected_head,
            phases=tuple(self.phases),
            resume_first=resume_first,
            startup_timeout_seconds=float(self.startup_timeout_seconds),
            request_timeout_seconds=float(self.request_timeout_seconds),
            sandbox_image=self.sandbox_image,
            retain_workspaces=self.retain_workspaces,
        )


class JsonEvidenceHttpClient:
    """Small no-proxy JSON client that durably records every exchange."""

    def __init__(self, base_url: str, evidence_root: Path, *, timeout_seconds: float):
        self.base_url = base_url.rstrip("/")
        self.evidence_root = evidence_root
        self.timeout_seconds = timeout_seconds
        self.exchanges: list[HttpExchange] = []
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
        *,
        headers: Mapping[str, str] | None = None,
        allow_error: bool = False,
        authenticated: bool = False,
    ) -> HttpExchange:
        if not path.startswith("/") or "\x00" in path:
            raise BasicBackendGateError("basic_gate_http_path_invalid")
        request_body = b""
        request_headers = {"accept": "application/json"}
        if payload is not None:
            request_body = _canonical_json(payload)
            request_headers["content-type"] = "application/json"
        request_headers.update({str(key): str(value) for key, value in (headers or {}).items()})
        request = urllib.request.Request(
            self.base_url + path,
            data=request_body if payload is not None else None,
            headers=request_headers,
            method=method.upper(),
        )
        started = time.monotonic()
        try:
            with self._opener.open(request, timeout=self.timeout_seconds) as response:
                status_code = int(response.status)
                raw_response = response.read()
        except urllib.error.HTTPError as error:
            status_code = int(error.code)
            raw_response = error.read()
        except (OSError, urllib.error.URLError) as error:
            raise BasicBackendGateError(
                "basic_gate_http_transport_failed",
                {"method": method.upper(), "path": path, "error": type(error).__name__},
            ) from error
        elapsed_ms = int((time.monotonic() - started) * 1000)
        try:
            decoded = json.loads(raw_response)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise BasicBackendGateError(
                "basic_gate_http_response_not_json",
                {"method": method.upper(), "path": path, "status_code": status_code},
            ) from error
        if not isinstance(decoded, dict):
            raise BasicBackendGateError("basic_gate_http_response_not_object")
        assertion_present = bool(request_headers.get(_OPERATOR_ASSERTION_HEADER, "").strip())
        server_acknowledged = _server_acknowledged_signed_operator_authority(
            path=path,
            status_code=status_code,
            response=decoded,
        )
        authentication = {
            "scheme": "signed_operator_assertion",
            "assertion_present": assertion_present,
            "server_acknowledged": server_acknowledged,
            "caller_claimed_authenticated": bool(authenticated),
        }
        authentication["authenticated"] = bool(assertion_present and server_acknowledged)
        request_sha256 = _sha256_bytes(request_body)
        response_sha256 = _sha256_bytes(raw_response)
        ordinal = len(self.exchanges) + 1
        evidence_name = f"http-{ordinal:03d}-{_safe_name(method)}-{_safe_name(path)}.json"
        evidence_path = self.evidence_root / "http" / evidence_name
        _write_private_json(
            evidence_path,
            {
                "schema_version": "source-proxy-basic-backend-10-http-exchange/v1",
                "ordinal": ordinal,
                "method": method.upper(),
                "path": path,
                "status_code": status_code,
                "authenticated": authentication["authenticated"],
                "authentication": authentication,
                "request_headers_present": sorted(request_headers),
                "request": dict(payload) if payload is not None else None,
                "request_sha256": request_sha256,
                "request_body_base64": base64.b64encode(request_body).decode("ascii"),
                "response": decoded,
                "response_sha256": response_sha256,
                "response_body_base64": base64.b64encode(raw_response).decode("ascii"),
                "elapsed_ms": elapsed_ms,
            },
        )
        exchange = HttpExchange(
            ordinal=ordinal,
            method=method.upper(),
            path=path,
            status_code=status_code,
            request_sha256=request_sha256,
            response_sha256=response_sha256,
            response=decoded,
            evidence_file=str(evidence_path),
            authenticated=bool(authentication["authenticated"]),
            elapsed_ms=elapsed_ms,
            authentication=authentication,
            request=(dict(payload) if payload is not None else None),
        )
        self.exchanges.append(exchange)
        if not exchange.ok and not allow_error:
            raise BasicBackendGateError(
                "basic_gate_http_request_rejected",
                {
                    "method": exchange.method,
                    "path": exchange.path,
                    "status_code": exchange.status_code,
                    "response_sha256": exchange.response_sha256,
                    "reason_code": _response_reason(exchange.response),
                },
            )
        return exchange


class OperatorAssertionSigner:
    """Independent harness-side operator session; the service only verifies it."""

    def __init__(self, *, secret: str, session_id: str):
        self._secret = secret
        self.session_id = session_id

    def assertion(
        self,
        *,
        task_id: str,
        preview_id: str,
        generation: int,
        action: str = "approve",
    ) -> str:
        payload = {
            "action": action,
            "expires_at": _iso_now(delta_seconds=60),
            "generation": int(generation),
            "operator": "spiritos-local-operator",
            "preview_id": preview_id,
            "role": "approval-issuer",
            "session_id": self.session_id,
            "task_id": task_id,
        }
        encoded = _b64url(_canonical_json(payload))
        signature = hmac.new(
            self._secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256
        ).digest()
        return encoded + "." + _b64url(signature)


class ProductionGateServiceFactory:
    """Launch one isolated-state Source Proxy process for exactly one task."""

    def __call__(self, spec: ServiceLaunchSpec) -> contextlib.AbstractContextManager[RunningGateService]:
        return self._running(spec)

    @contextlib.contextmanager
    def _running(self, spec: ServiceLaunchSpec) -> Iterator[RunningGateService]:
        port = _unused_loopback_port()
        operator_root = spec.state_root / "operator"
        operator_root.mkdir(parents=True, mode=0o700, exist_ok=False)
        secret = secrets.token_urlsafe(48)
        session_id = "basic-gate-" + secrets.token_urlsafe(18)
        session_path = operator_root / "sessions.json"
        _write_private_json(
            session_path,
            {
                "sessions": {
                    session_id: {
                        # A bounded three-attempt local repair can legitimately
                        # outlive the old 15-minute operator session.  Keep the
                        # task-local session below the 60-minute model authority
                        # ceiling while allowing all approvals to complete.
                        "expires_at": _iso_now(delta_seconds=55 * 60),
                        "revoked_at": None,
                    }
                }
            },
        )
        (
            import_audit_root,
            import_audit_log,
            import_audit_owner,
        ) = _prepare_service_import_audit(spec.state_root)
        environment = _service_environment(
            spec,
            port=port,
            operator_secret=secret,
            operator_state=session_path,
        )
        environment["PYTHONPATH"] = (
            str(import_audit_root)
            + os.pathsep
            + str(environment.get("PYTHONPATH") or spec.source_root)
        )
        environment["SOURCE_PROXY_GATE_IMPORT_AUDIT_LOG"] = str(import_audit_log)
        environment["SOURCE_PROXY_GATE_IMPORT_AUDIT_OWNER"] = str(
            import_audit_owner
        )
        environment["SOURCE_PROXY_GATE_FORBIDDEN_IMPORT_PREFIXES"] = ";".join(
            _FORBIDDEN_PRODUCTION_IMPORT_PREFIXES
        )
        stdout_path = spec.evidence_root / "service-stdout.log"
        stderr_path = spec.evidence_root / "service-stderr.log"
        stdout_path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        for log_path in (stdout_path, stderr_path):
            log_path.touch(mode=0o600, exist_ok=False)
            os.chmod(log_path, 0o600)
        command = [
            str(spec.python_executable),
            "-m",
            "uvicorn",
            "source_proxy.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ]
        with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
            process = subprocess.Popen(
                command,
                cwd=spec.source_root,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
        receipt: dict[str, Any] | None = None
        try:
            client = JsonEvidenceHttpClient(
                f"http://127.0.0.1:{port}",
                spec.evidence_root,
                timeout_seconds=spec.request_timeout_seconds,
            )
            health = _wait_for_service(client, process, spec.startup_timeout_seconds)
            observed_cwd = _process_cwd(process.pid)
            if observed_cwd != spec.source_root:
                raise BasicBackendGateError(
                    "basic_gate_service_cwd_mismatch",
                    {"expected": str(spec.source_root), "observed": str(observed_cwd)},
                )
            branch, head = _git_identity(spec.source_root)
            if branch != spec.expected_branch or head != spec.expected_head:
                raise BasicBackendGateError("basic_gate_service_source_identity_mismatch")
            receipt = {
                "schema_version": "source-proxy-basic-backend-10-service-process/v1",
                "task_label": spec.task_label,
                "pid": process.pid,
                "cwd": str(observed_cwd),
                "branch": branch,
                "head": head,
                "loopback_port": port,
                "command_sha256": _sha256_json(command),
                "environment_names": sorted(environment),
                "model_aliases": _service_model_aliases(environment),
                "hosted_credentials_inherited": False,
                "direct_ollama_bypass_enabled": False,
                "sandbox_image_id": spec.sandbox_image_id,
                "model_inventory_sha256": spec.model_inventory_sha256,
                "verifier_runtime_sha256": spec.verifier_runtime_sha256,
                "fixture_manifest_sha256": _sha256_file(spec.authority_manifest_path),
                "task_local_state_root": str(spec.state_root),
                "health_response_sha256": health.response_sha256,
                "service_process_per_task": True,
            }
            _write_private_json(spec.evidence_root / "service-process.json", receipt)
            yield RunningGateService(
                client=client,
                signer=OperatorAssertionSigner(secret=secret, session_id=session_id),
                process_receipt=receipt,
            )
        finally:
            _request_service_import_audit_snapshot(
                process,
                import_audit_log,
                import_audit_owner,
            )
            _stop_process(process)
            if receipt is not None:
                receipt["import_attestation"] = _finalize_service_import_audit(
                    import_audit_log
                )
                _write_private_json(
                    spec.evidence_root / "service-process.json",
                    receipt,
                )


def run_private_oracle_container(
    *,
    task_id: str,
    workspace_root: Path,
    values: Mapping[str, str | int],
    private_store: Path,
    source_root: Path,
    python_executable: Path,
    inherited_environment: Mapping[str, str],
) -> Mapping[str, Any]:
    """Observe candidate behavior in isolation, then decide in this process.

    The container receives no oracle implementation, expected value, task id,
    source tree, or reference patch.  It imports candidate code only to execute
    an expected-free declarative probe and emits primitive observations.  The
    trusted decision below never imports candidate code.
    """

    del python_executable, source_root
    docker = shutil.which("docker")
    if docker is None:
        raise BasicBackendGateError("basic_gate_private_oracle_container_unavailable")
    image = str(
        inherited_environment.get(
            "SOURCE_PROXY_BASIC_GATE_ORACLE_IMAGE",
            inherited_environment.get(
                "SOURCE_PROXY_GENERIC_BACKEND_SANDBOX_IMAGE",
                "scout-scout-api:latest",
            ),
        )
    ).strip()
    if not image:
        raise BasicBackendGateError("basic_gate_private_oracle_image_missing")
    root = workspace_root.resolve(strict=True)
    name = "source-proxy-private-oracle-" + secrets.token_hex(12)
    probe_spec = _private_probe_spec(task_id, values)
    if "task_id" in probe_spec or "expected" in json.dumps(probe_spec, sort_keys=True).lower():
        raise BasicBackendGateError("basic_gate_private_probe_spec_exposes_answer")
    worker_path = private_store / "neutral-probe-worker.py"
    worker_path.write_text(_NEUTRAL_PROBE_WORKER, encoding="utf-8")
    os.chmod(worker_path, 0o600)
    probe_path = private_store / "probe-spec.json"
    _write_private_json(probe_path, probe_spec)
    command = [
        docker,
        "run",
        "--rm",
        "-i",
        "--name",
        name,
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges=true",
        "--pids-limit",
        "64",
        "--memory",
        "512m",
        "--cpus",
        "1",
        "--user",
        f"{getattr(os, 'getuid', lambda: 1000)()}:{getattr(os, 'getgid', lambda: 1000)()}",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,noexec,size=64m",
        "--mount",
        f"type=bind,src={root},dst=/workspace,readonly",
        "--mount",
        f"type=bind,src={worker_path.resolve()},dst=/worker/probe.py,readonly",
        "--workdir",
        "/tmp",
        "--env",
        "HOME=/tmp",
        "--env",
        "PYTHONDONTWRITEBYTECODE=1",
        "--env",
        "PYTHONHASHSEED=0",
        "--env",
        "SPIRIT_NEUTRAL_WORKSPACE_ROOT=/workspace",
        "--entrypoint",
        "python",
        image,
        "-I",
        "-S",
        "/worker/probe.py",
    ]
    payload = _canonical_json(probe_spec)
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            input=payload,
            capture_output=True,
            check=False,
            timeout=45,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        )
    except subprocess.TimeoutExpired as error:
        subprocess.run(
            [docker, "rm", "-f", name],
            check=False,
            capture_output=True,
            timeout=15,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        )
        raise BasicBackendGateError("basic_gate_private_oracle_timeout") from error
    elapsed_ms = int((time.monotonic() - started) * 1000)
    if completed.returncode != 0:
        raise BasicBackendGateError(
            "basic_gate_private_oracle_failed",
            {"exit_code": completed.returncode, "stderr_sha256": _sha256_bytes(completed.stderr)},
        )
    try:
        observations = _parse_neutral_probe_output(completed.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise BasicBackendGateError("basic_gate_private_oracle_output_invalid") from error
    if (
        observations.get("schema_version")
        != "source-proxy-basic-backend-10-neutral-observations/v1"
        or "passed" in observations
        or "task_id" in observations
    ):
        raise BasicBackendGateError("basic_gate_private_oracle_output_invalid")
    checks = _trusted_private_oracle_decision(
        task_id=task_id,
        workspace_root=root,
        values=values,
        observations=observations,
    )
    private_payload = {
        "schema_version": "source-proxy-basic-backend-10-private-oracle/v2",
        "task_id": task_id,
        "passed": all(value for _name, value in checks),
        "checks": [{"name": check, "passed": value} for check, value in checks],
        "observations_sha256": _sha256_json(observations),
        "neutral_worker_sha256": _sha256_text(_NEUTRAL_PROBE_WORKER),
    }
    observations_path = private_store / "candidate-observations.json"
    _write_private_json(observations_path, observations)
    private_path = private_store / "oracle-private.json"
    _write_private_json(private_path, private_payload)
    return {
        "schema_version": "source-proxy-basic-backend-10-private-oracle-boundary/v1",
        "passed": bool(private_payload["passed"]),
        "private_payload_sha256": _sha256_json(private_payload),
        "candidate_observations_sha256": _sha256_json(observations),
        "private_evidence_file": str(private_path),
        "candidate_observations_file": str(observations_path),
        "process_separate_from_source_proxy": True,
        "trusted_decision_imported_candidate": False,
        "candidate_received_expected_results": False,
        "candidate_received_task_id": False,
        "candidate_can_import_oracle_module": False,
        "network": "none",
        "workspace_mount": "read_only",
        "mounted_inputs": ["fixture", "neutral_probe_worker"],
        "host_environment_inherited": False,
        "sandbox_image_id": image,
        "command_sha256": _sha256_json(command),
        "elapsed_ms": elapsed_ms,
    }


_NEUTRAL_PROBE_WORKER = r'''from __future__ import annotations
import copy
import hashlib
import importlib
import importlib.util
import json
import logging
import math
import os
import resource
import signal
import subprocess
import sys
from pathlib import Path

# These supervisor-owned functions are captured before a candidate-only child
# exists.  Candidate code is never imported into this interpreter.
_outer_dumps = json.dumps
_outer_loads = json.loads
_outer_write = os.write
_outer_exit = os._exit
_outer_urandom = os.urandom
_OBSERVATION_SCHEMA = "source-proxy-basic-backend-10-neutral-observations/v1"
_ALLOWED_OPERATION_KEYS = {
    "id", "kind", "ok", "value", "result_is_global", "exception_type",
    "exception_message", "cause_type", "cause_message", "exception_is_stub",
    "cause_is_stub", "logs", "args_after", "kwargs_after",
    "worker_exception_type", "worker_exception_message",
}
_FORBIDDEN_KEYS = {"passed", "task_id", "expected", "checks"}

def primitive(value, depth=0):
    if depth > 12:
        return {"type": type(value).__name__, "truncated": True}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (list, tuple)):
        return [primitive(item, depth + 1) for item in value]
    if isinstance(value, dict):
        return {str(key): primitive(item, depth + 1) for key, item in value.items()}
    return {"type": type(value).__name__, "repr": repr(value)[:500]}

class Stub:
    def __init__(self, definition, errors):
        self.definition = definition
        self.errors = errors
    def __getattr__(self, name):
        if name != self.definition["method"]:
            raise AttributeError(name)
        def invoke(*args, **kwargs):
            if self.definition["mode"] == "raise":
                error_type = {"ConnectionError": ConnectionError, "RuntimeError": RuntimeError}[self.definition["exception"]]
                error = error_type(self.definition["message"])
                self.errors[id(self)] = error
                raise error
            return copy.deepcopy(self.definition.get("value"))
        return invoke

class Capture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []
    def emit(self, record):
        self.messages.append(record.getMessage())

def resolve(value, stubs):
    if isinstance(value, dict) and set(value) == {"$stub"}:
        return stubs[value["$stub"]]
    if isinstance(value, list):
        return [resolve(item, stubs) for item in value]
    if isinstance(value, dict):
        return {key: resolve(item, stubs) for key, item in value.items()}
    return value

def load_module(name, definition, workspace):
    if definition["kind"] == "file":
        target = (workspace / definition["path"]).resolve(strict=True)
        target.relative_to(workspace)
        specification = importlib.util.spec_from_file_location("candidate_" + name, target)
        if specification is None or specification.loader is None:
            raise RuntimeError("module_spec_unavailable")
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        return module
    if definition["kind"] == "package":
        return importlib.import_module(definition["name"])
    raise ValueError("module_kind_invalid")

def candidate_main():
    # Only this child interpreter imports and calls candidate code.  Its stdout
    # is an untrusted private pipe consumed by the neutral supervisor.
    raw_spec = sys.stdin.buffer.read()
    spec = json.loads(raw_spec)
    workspace = Path(os.environ["SPIRIT_NEUTRAL_WORKSPACE_ROOT"]).resolve(strict=True)
    sys.path.insert(0, str(workspace))
    modules = {}
    imports = {}
    for name, definition in spec["modules"].items():
        try:
            modules[name] = load_module(name, definition, workspace)
            imports[name] = {"ok": True}
        except BaseException as error:
            imports[name] = {"ok": False, "exception_type": type(error).__name__, "message": str(error)[:500]}
    errors = {}
    stubs = {name: Stub(definition, errors) for name, definition in spec.get("stubs", {}).items()}
    results = []
    for operation in spec["operations"]:
        record = {"id": operation["id"], "kind": operation["kind"]}
        try:
            kind = operation["kind"]
            if kind == "clear_global":
                getattr(modules[operation["module"]], operation["name"]).clear()
                record["ok"] = True
            elif kind == "snapshot":
                record.update(ok=True, value=primitive(getattr(modules[operation["module"]], operation["name"])))
            elif kind == "setenv":
                os.environ[operation["name"]] = operation["value"]
                record["ok"] = True
            elif kind == "delenv":
                os.environ.pop(operation["name"], None)
                record["ok"] = True
            elif kind == "call":
                module = modules[operation["module"]]
                function = getattr(module, operation["function"])
                args = resolve(copy.deepcopy(operation.get("args", [])), stubs)
                kwargs = resolve(copy.deepcopy(operation.get("kwargs", {})), stubs)
                capture = None
                logger = None
                if operation.get("logger"):
                    logger = getattr(modules[operation["logger"]["module"]], operation["logger"]["name"])
                    capture = Capture()
                    logger.addHandler(capture)
                    logger.setLevel(logging.ERROR)
                try:
                    value = function(*args, **kwargs)
                    record.update(ok=True, value=primitive(value))
                    if operation.get("compare_global"):
                        record["result_is_global"] = value is getattr(module, operation["compare_global"])
                except BaseException as error:
                    record.update(
                        ok=False,
                        exception_type=type(error).__name__,
                        exception_message=str(error)[:1000],
                        cause_type=type(error.__cause__).__name__ if error.__cause__ is not None else None,
                        cause_message=str(error.__cause__)[:1000] if error.__cause__ is not None else None,
                        exception_is_stub=any(error is item for item in errors.values()),
                        cause_is_stub=any(error.__cause__ is item for item in errors.values()),
                    )
                finally:
                    if logger is not None and capture is not None:
                        logger.removeHandler(capture)
                        record["logs"] = list(capture.messages)
                record["args_after"] = primitive(args)
                record["kwargs_after"] = primitive(kwargs)
            else:
                raise ValueError("operation_kind_invalid")
        except BaseException as error:
            record.update(ok=False, worker_exception_type=type(error).__name__, worker_exception_message=str(error)[:500])
        results.append(record)
    output = {"schema_version": _OBSERVATION_SCHEMA, "imports": imports, "operations": results}
    # Candidate mutations of these child globals can only corrupt the private
    # pipe; the supervisor treats that pipe as hostile input.
    child_bytes = json.dumps(output, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    os.write(1, child_bytes)
    os._exit(0)

def _limit_child():
    limits = (
        (resource.RLIMIT_CPU, 15),
        (resource.RLIMIT_AS, 384 * 1024 * 1024),
        (resource.RLIMIT_FSIZE, 4 * 1024 * 1024),
        (resource.RLIMIT_NOFILE, 64),
        (resource.RLIMIT_NPROC, 32),
        (resource.RLIMIT_CORE, 0),
    )
    for resource_id, maximum in limits:
        try:
            resource.setrlimit(resource_id, (maximum, maximum))
        except (OSError, ValueError):
            pass

def _reject_constant(_value):
    raise ValueError("non_finite_number")

def _plain_json(value, depth=0):
    if depth > 16:
        return False
    if value is None or isinstance(value, (bool, int, str)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return len(value) <= 10000 and all(_plain_json(item, depth + 1) for item in value)
    if isinstance(value, dict):
        return len(value) <= 10000 and all(
            isinstance(key, str) and _plain_json(item, depth + 1)
            for key, item in value.items()
        )
    return False

def _contains_forbidden_key(value):
    if isinstance(value, dict):
        return any(
            str(key).lower() in _FORBIDDEN_KEYS or _contains_forbidden_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_key(item) for item in value)
    return False

def _validate_spec(spec):
    if not isinstance(spec, dict) or spec.get("schema_version") != "source-proxy-basic-backend-10-neutral-probe/v1":
        raise ValueError("probe_spec_schema_invalid")
    modules = spec.get("modules")
    operations = spec.get("operations")
    if not isinstance(modules, dict) or not modules or not isinstance(operations, list):
        raise ValueError("probe_spec_shape_invalid")
    operation_ids = [item.get("id") for item in operations if isinstance(item, dict)]
    if len(operation_ids) != len(operations) or any(not isinstance(item, str) or not item for item in operation_ids):
        raise ValueError("probe_operation_id_invalid")
    if len(operation_ids) != len(set(operation_ids)) or _contains_forbidden_key(spec):
        raise ValueError("probe_spec_unsafe")

def _validate_observations(observations, spec):
    if not isinstance(observations, dict) or set(observations) != {"schema_version", "imports", "operations"}:
        raise ValueError("candidate_observation_shape_invalid")
    if observations.get("schema_version") != _OBSERVATION_SCHEMA or _contains_forbidden_key(observations):
        raise ValueError("candidate_observation_schema_invalid")
    imports = observations.get("imports")
    operations = observations.get("operations")
    if not isinstance(imports, dict) or set(imports) != set(spec["modules"]):
        raise ValueError("candidate_import_observation_invalid")
    for record in imports.values():
        if not isinstance(record, dict) or not isinstance(record.get("ok"), bool):
            raise ValueError("candidate_import_record_invalid")
    if not isinstance(operations, list) or len(operations) != len(spec["operations"]):
        raise ValueError("candidate_operation_count_invalid")
    for expected, observed in zip(spec["operations"], operations):
        if not isinstance(observed, dict) or set(observed) - _ALLOWED_OPERATION_KEYS:
            raise ValueError("candidate_operation_record_invalid")
        if observed.get("id") != expected.get("id") or observed.get("kind") != expected.get("kind"):
            raise ValueError("candidate_operation_binding_invalid")
        if not isinstance(observed.get("ok"), bool):
            raise ValueError("candidate_operation_status_invalid")
    if not _plain_json(observations):
        raise ValueError("candidate_observation_not_primitive")
    return observations

def _failure_observations(spec, reason, stderr=b""):
    modules = spec.get("modules", {}) if isinstance(spec, dict) else {}
    operations = spec.get("operations", []) if isinstance(spec, dict) else []
    suffix = hashlib.sha256(stderr).hexdigest() if stderr else "none"
    return {
        "schema_version": _OBSERVATION_SCHEMA,
        "imports": {
            str(name): {"ok": False, "exception_type": "NeutralProbeChildError", "message": reason + ":" + suffix}
            for name in modules
        },
        "operations": [
            {
                "id": str(item.get("id") or "invalid"),
                "kind": str(item.get("kind") or "invalid"),
                "ok": False,
                "worker_exception_type": "NeutralProbeChildError",
                "worker_exception_message": reason,
            }
            for item in operations if isinstance(item, dict)
        ],
    }

def _run_candidate(raw_spec, spec, workspace):
    environment = {
        "HOME": "/tmp",
        "LANG": "C.UTF-8",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "SPIRIT_NEUTRAL_WORKSPACE_ROOT": str(workspace),
    }
    process = subprocess.Popen(
        [sys.executable, "-I", "-S", str(Path(__file__).resolve()), "--candidate"],
        cwd="/tmp",
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        start_new_session=True,
        preexec_fn=_limit_child,
    )
    try:
        stdout, stderr = process.communicate(raw_spec, timeout=20)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            process.kill()
        stdout, stderr = process.communicate()
        return _failure_observations(spec, "candidate_timeout", stderr)
    if process.returncode != 0:
        return _failure_observations(spec, "candidate_failed", stderr)
    if len(stdout) > 2 * 1024 * 1024:
        return _failure_observations(spec, "candidate_output_too_large", stderr)
    try:
        parsed = _outer_loads(stdout.decode("utf-8"), parse_constant=_reject_constant)
        return _validate_observations(parsed, spec)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError):
        return _failure_observations(spec, "candidate_output_invalid", stderr)

def supervisor_main():
    raw_spec = sys.stdin.buffer.read(2 * 1024 * 1024 + 1)
    spec = {}
    try:
        if len(raw_spec) > 2 * 1024 * 1024:
            raise ValueError("probe_spec_too_large")
        spec = _outer_loads(raw_spec.decode("utf-8"), parse_constant=_reject_constant)
        _validate_spec(spec)
        workspace = Path(os.environ.get("SPIRIT_NEUTRAL_WORKSPACE_ROOT", "/workspace")).resolve(strict=True)
        observations = _run_candidate(raw_spec, spec, workspace)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError, OSError) as error:
        observations = _failure_observations(spec, "supervisor_input_invalid:" + type(error).__name__)
    nonce = _outer_urandom(24).hex()
    payload = _outer_dumps(observations, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    frame = b"SPIRIT_NEUTRAL_OBSERVATION_V1 " + nonce.encode("ascii") + b" " + payload + b"\n"
    _outer_write(1, frame)
    _outer_exit(0)

if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--candidate":
        candidate_main()
    supervisor_main()
'''


def _parse_neutral_probe_output(raw: bytes) -> dict[str, Any]:
    prefix = b"SPIRIT_NEUTRAL_OBSERVATION_V1 "
    frames = [line for line in raw.splitlines() if line.startswith(prefix)]
    if len(frames) != 1:
        raise ValueError("neutral_probe_frame_count_invalid")
    fields = frames[0].split(b" ", 2)
    if len(fields) != 3 or len(fields[1]) != 48 or any(
        value not in b"0123456789abcdef" for value in fields[1]
    ):
        raise ValueError("neutral_probe_frame_invalid")
    payload = json.loads(fields[2])
    if not isinstance(payload, dict):
        raise ValueError("neutral_probe_payload_invalid")
    return payload


def _private_probe_spec(
    task_id: str,
    values: Mapping[str, str | int],
) -> dict[str, Any]:
    file_backend = {"backend": {"kind": "file", "path": "src/backend.py"}}
    if task_id == "BT01":
        parameter = str(values["limit_parameter"])
        maximum = int(values["maximum_limit"])
        operations = [
            _snapshot("items_before", "backend", "ITEMS"),
            _call("omitted", "backend", "list_items", [{}]),
            _call("one", "backend", "list_items", [{parameter: "1"}]),
            _call("maximum", "backend", "list_items", [{parameter: str(maximum)}]),
            *[
                _call(f"invalid_{index}", "backend", "list_items", [{parameter: raw}])
                for index, raw in enumerate(("", "0", str(maximum + 1), "1.5", "nope"))
            ],
            _snapshot("items_after", "backend", "ITEMS"),
        ]
        return _probe(file_backend, operations)
    if task_id == "BT02":
        function = str(values["function_name"])
        return _probe(
            file_backend,
            [
                _call("mixed", "backend", function, [[4, -2, 9, 0]]),
                _call("single", "backend", function, [[7]]),
                _call("empty", "backend", function, [[]]),
            ],
        )
    if task_id == "BT03":
        return _probe(file_backend, [_call("status", "backend", "get_status", [])])
    if task_id == "BT04":
        field = str(values["field_name"])
        invalid = ({}, {field: None}, {field: 5}, {field: "\t"})
        return _probe(
            file_backend,
            [
                {"id": "clear", "kind": "clear_global", "module": "backend", "name": "ACCOUNTS"},
                *[_call(f"invalid_{index}", "backend", "create_account", [payload]) for index, payload in enumerate(invalid)],
                _snapshot("after_invalid", "backend", "ACCOUNTS"),
                _call("valid", "backend", "create_account", [{field: " valid "}]),
            ],
        )
    if task_id == "BT05":
        invalid = ((-1, None), (0, 0), (0, -1), (True, None), (0, False), ("1", None))
        return _probe(
            file_backend,
            [
                _snapshot("before", "backend", "RECORDS"),
                _call("page_one", "backend", "list_records", [], {"offset": 2, "limit": 3}),
                _call("page_two", "backend", "list_records", [], {"offset": 2, "limit": 3}),
                *[_call(f"invalid_{index}", "backend", "list_records", [], {"offset": pair[0], "limit": pair[1]}) for index, pair in enumerate(invalid)],
                {**_call("defaults", "backend", "list_records", []), "compare_global": "RECORDS"},
                _snapshot("after", "backend", "RECORDS"),
            ],
        )
    if task_id == "BT06":
        function = f"count_{values['status_name']}_orders"
        modules = {"service": {"kind": "file", "path": "src/service.py"}}
        return _probe(
            modules,
            [
                _snapshot("before", "service", "ORDERS"),
                _call("count", "service", function, []),
                _call("find_two", "service", "find_order", [2]),
                _call("find_missing", "service", "find_order", [999]),
                _snapshot("after", "service", "ORDERS"),
            ],
        )
    if task_id == "BT07":
        modules = {
            "users": {"kind": "package", "name": "src.users"},
            "contacts": {"kind": "package", "name": "src.contacts"},
        }
        return _probe(
            modules,
            [
                _call("username", "users", "normalize_username", [" A.B "]),
                _call("email", "contacts", "normalize_email", [" X@Y.TEST "]),
            ],
        )
    if task_id == "BT08":
        name = str(values["environment_name"])
        modules = {"config": {"kind": "file", "path": "src/config.py"}}
        operations: list[dict[str, Any]] = [
            {"id": "missing_env", "kind": "delenv", "name": name},
            _call("missing", "config", "load_timeout", []),
        ]
        for index, raw in enumerate(("", " ", "\t")):
            operations.extend((
                {"id": f"blank_env_{index}", "kind": "setenv", "name": name, "value": raw},
                _call(f"blank_{index}", "config", "load_timeout", []),
            ))
        operations.extend((
            {"id": "positive_env", "kind": "setenv", "name": name, "value": "41"},
            _call("positive", "config", "load_timeout", []),
        ))
        for index, raw in enumerate(("0", "-3", "abc")):
            operations.extend((
                {"id": f"invalid_env_{index}", "kind": "setenv", "name": name, "value": raw},
                _call(f"invalid_{index}", "config", "load_timeout", []),
            ))
        return _probe(modules, operations)
    if task_id == "BT09":
        destination = str(values["destination"])
        secret = str(values["secret_value"])
        modules = file_backend
        stubs = {
            "broken": {
                "method": "send",
                "mode": "raise",
                "exception": "ConnectionError",
                "message": f"offline:{secret}",
            }
        }
        operation = _call(
            "delivery",
            "backend",
            "deliver_message",
            [
                {"$stub": "broken"},
                destination,
                "hidden-message-body",
                {"api_token": secret, "password": "hidden-password"},
            ],
        )
        operation["logger"] = {"module": "backend", "name": "LOGGER"}
        return _probe(modules, [operation], stubs=stubs)
    if task_id == "BT10":
        profile_id = int(values["profile_id"])
        stubs = {
            "working": {"method": "fetch", "mode": "return", "value": {"id": profile_id, "ok": True}},
            "offline": {"method": "fetch", "mode": "raise", "exception": "ConnectionError", "message": "offline"},
        }
        return _probe(
            file_backend,
            [
                _call("working", "backend", "fetch_profile", [{"$stub": "working"}, profile_id]),
                _call("offline", "backend", "fetch_profile", [{"$stub": "offline"}, profile_id]),
            ],
            stubs=stubs,
        )
    raise BasicBackendGateError("basic_gate_private_probe_task_unknown")


def _probe(
    modules: Mapping[str, Any],
    operations: Sequence[Mapping[str, Any]],
    *,
    stubs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "source-proxy-basic-backend-10-neutral-probe/v1",
        "modules": dict(modules),
        "stubs": dict(stubs or {}),
        "operations": [dict(operation) for operation in operations],
    }


def _snapshot(operation_id: str, module: str, name: str) -> dict[str, Any]:
    return {"id": operation_id, "kind": "snapshot", "module": module, "name": name}


def _call(
    operation_id: str,
    module: str,
    function: str,
    args: Sequence[Any],
    kwargs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": operation_id,
        "kind": "call",
        "module": module,
        "function": function,
        "args": list(args),
        "kwargs": dict(kwargs or {}),
    }


def _trusted_private_oracle_decision(
    *,
    task_id: str,
    workspace_root: Path,
    values: Mapping[str, str | int],
    observations: Mapping[str, Any],
) -> tuple[tuple[str, bool], ...]:
    imports = observations.get("imports")
    raw_operations = observations.get("operations")
    if not isinstance(imports, Mapping) or not isinstance(raw_operations, list):
        return (("observation_protocol", False),)
    if not imports or not all(
        isinstance(value, Mapping) and value.get("ok") is True for value in imports.values()
    ):
        return (("candidate_import", False),)
    operations = {
        str(item.get("id")): item
        for item in raw_operations
        if isinstance(item, Mapping) and str(item.get("id") or "")
    }
    value = lambda name: operations.get(name, {}).get("value")
    ok = lambda name: operations.get(name, {}).get("ok") is True
    raised = lambda name, kind="ValueError": (
        operations.get(name, {}).get("ok") is False
        and operations.get(name, {}).get("exception_type") == kind
    )
    if task_id == "BT01":
        parameter_max = int(values["maximum_limit"])
        before = value("items_before")
        omitted = value("omitted")
        one = value("one")
        maximum = value("maximum")
        invalid = [value(f"invalid_{index}") for index in range(5)]
        return (
            ("omitted_compatibility", isinstance(before, list) and omitted == {"status": 200, "body": {"items": before}}),
            (
                "inclusive_limits",
                isinstance(before, list)
                and one == {"status": 200, "body": {"items": before[:1]}}
                and maximum
                == {"status": 200, "body": {"items": before[:parameter_max]}},
            ),
            ("invalid_values", all(isinstance(item, Mapping) and item.get("status") == 400 and bool(item.get("body", {}).get("error")) for item in invalid)),
            ("storage_immutable", before == value("items_after")),
        )
    if task_id == "BT02":
        return (
            ("complete_sum", value("mixed") == 11 and value("single") == 7 and value("empty") == 0),
            ("input_immutable", operations.get("mixed", {}).get("args_after") == [[4, -2, 9, 0]]),
        )
    if task_id == "BT03":
        response = value("status")
        field = str(values["response_field"])
        return (
            ("existing_contract", isinstance(response, Mapping) and response.get("status") == "ok" and response.get("version") == 1),
            ("new_field", isinstance(response, Mapping) and response.get(field) == str(values["instance_value"])),
            ("json_shape", isinstance(response, Mapping) and set(response) == {"status", "version", field}),
        )
    if task_id == "BT04":
        invalid = [value(f"invalid_{index}") for index in range(4)]
        field = str(values["field_name"])
        valid = value("valid")
        return (
            ("invalid_status", all(isinstance(item, Mapping) and item.get("status") == 422 and bool(item.get("body", {}).get("error")) for item in invalid)),
            ("invalid_storage_immutable", value("after_invalid") == []),
            ("valid_compatibility", isinstance(valid, Mapping) and valid.get("status") == 201 and valid.get("body", {}).get(field) == " valid "),
        )
    if task_id == "BT05":
        before = value("before")
        return (
            ("page_semantics", isinstance(before, list) and value("page_one") == before[2:5] and value("page_two") == value("page_one")),
            ("storage_immutable", before == value("after")),
            ("invalid_values", all(raised(f"invalid_{index}") for index in range(6))),
            ("independent_default_result", value("defaults") == before and operations.get("defaults", {}).get("result_is_global") is False),
        )
    if task_id == "BT06":
        source = (workspace_root / "tests/test_service.py").read_text(encoding="utf-8")
        function = f"count_{values['status_name']}_orders"
        return (
            ("exact_status_count", ok("count") and value("count") == 2),
            ("existing_lookup", value("find_two") == {"id": 2, "status": "pending"} and value("find_missing") is None),
            ("storage_immutable", value("before") == value("after")),
            ("focused_test_added", _test_function_invoked_by_test(source, function)),
        )
    if task_id == "BT07":
        users_source = (workspace_root / "src/users.py").read_text(encoding="utf-8")
        contacts_source = (workspace_root / "src/contacts.py").read_text(encoding="utf-8")
        helper_modules = {
            path.stem
            for path in (workspace_root / "src").glob("*.py")
            if path.is_file()
            and path.name not in {"users.py", "contacts.py", "__init__.py"}
        }
        shared_usage = _called_helper_imports(
            users_source,
            helper_modules,
            function_name="normalize_username",
        ) & _called_helper_imports(
            contacts_source,
            helper_modules,
            function_name="normalize_email",
        )
        return (
            ("behavior_preserved", value("username") == "a.b" and value("email") == "x@y.test"),
            ("shared_helper", bool(helper_modules) and bool(shared_usage)),
        )
    if task_id == "BT08":
        default = int(values["default_value"])
        return (
            ("default_semantics", value("missing") == default and [value(f"blank_{index}") for index in range(3)] == [default] * 3),
            ("positive_value", value("positive") == 41),
            ("invalid_values", all(raised(f"invalid_{index}") for index in range(3))),
        )
    if task_id == "BT09":
        operation = operations.get("delivery", {})
        text = " ".join(str(item) for item in operation.get("logs", []))
        destination = str(values["destination"])
        secret = str(values["secret_value"])
        return (
            ("useful_log", destination in text and "ConnectionError" in text),
            ("secrets_absent", all(item not in text for item in (secret, "hidden-password", "hidden-message-body"))),
            ("original_error_reraised", operation.get("exception_is_stub") is True),
        )
    if task_id == "BT10":
        operation = operations.get("offline", {})
        message = str(operation.get("exception_message") or "").lower()
        dependency = str(values["dependency_name"]).lower()
        return (
            ("success_preserved", value("working") == {"id": int(values["profile_id"]), "ok": True}),
            ("truthful_actionable_error", operation.get("exception_type") == "DependencyUnavailable" and dependency in message and "retry" in message),
            ("cause_preserved", operation.get("cause_is_stub") is True),
        )
    return (("task_known", False),)


def _test_function_invoked_by_test(source: str, function_name: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in tree.body:
        if (
            not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            or not node.name.startswith("test_")
            or not _test_function_statically_runnable(node)
        ):
            continue
        if ("service", function_name) in _reachable_imported_calls(
            tree,
            node,
            {"service"},
        ):
            return True
    return False


def _test_function_statically_runnable(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    """Reject decorators that prove pytest will not execute the test body."""

    for decorator in function.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        name = _dotted_expression(target)
        if not name:
            continue
        if name[-1] == "skip":
            return False
        if name[-1] == "skipif" and isinstance(decorator, ast.Call):
            condition = decorator.args[0] if decorator.args else next(
                (
                    keyword.value
                    for keyword in decorator.keywords
                    if keyword.arg == "condition"
                ),
                None,
            )
            if condition is not None and _literal_truth(condition) is True:
                return False
        if name[-1] == "parametrize" and isinstance(decorator, ast.Call):
            values = decorator.args[1] if len(decorator.args) > 1 else next(
                (
                    keyword.value
                    for keyword in decorator.keywords
                    if keyword.arg == "argvalues"
                ),
                None,
            )
            if values is not None and _literal_truth(values) is False:
                return False
    return True


def _called_helper_imports(
    source: str,
    helper_modules: set[str],
    *,
    function_name: str,
) -> set[tuple[str, str]]:
    """Return helper calls made by one named top-level function only."""

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    target = next(
        (
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == function_name
        ),
        None,
    )
    if target is None:
        return set()
    return _reachable_imported_calls(
        tree,
        target,
        helper_modules,
    )


_ImportEnvironment = tuple[
    dict[str, tuple[str, str]],
    dict[tuple[str, ...], str],
]


def _reachable_imported_calls(
    tree: ast.Module,
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    helper_modules: set[str],
) -> set[tuple[str, str]]:
    """Resolve calls against imports that are live on a reachable path.

    Module bindings are evaluated to the end of the module because tests run
    after collection.  Function-local bindings then follow Python's lexical
    scoping rule: any local binder hides the module name even before that
    binder executes.  The statement flow skips constant-dead branches and
    stops paths after unconditional control transfer.
    """

    module_environments = _flow_statements(
        tree.body,
        [({}, {})],
        helper_modules,
        set(),
    )
    local_names = _function_local_names(function)
    resolved: set[tuple[str, str]] = set()
    for direct, modules in module_environments:
        environment: _ImportEnvironment = (
            {
                name: binding
                for name, binding in direct.items()
                if name not in local_names
            },
            {
                expression: module
                for expression, module in modules.items()
                if expression and expression[0] not in local_names
            },
        )
        _flow_statements(
            function.body,
            [environment],
            helper_modules,
            resolved,
        )
    return resolved


class _FunctionLocalBindingCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.names: set[str] = set()
        self.global_names: set[str] = set()
        self.nonlocal_names: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.names.add(node.id)

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for alias in node.names:
            self.names.add(alias.asname or alias.name.split(".", 1)[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        for alias in node.names:
            if alias.name != "*":
                self.names.add(alias.asname or alias.name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self.names.add(node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self.names.add(node.name)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self.names.add(node.name)

    def visit_Lambda(self, node: ast.Lambda) -> None:  # noqa: N802
        del node

    def visit_Global(self, node: ast.Global) -> None:  # noqa: N802
        self.global_names.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:  # noqa: N802
        self.nonlocal_names.update(node.names)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:  # noqa: N802
        if node.name:
            self.names.add(node.name)
        self.generic_visit(node)

    def visit_MatchAs(self, node: ast.MatchAs) -> None:  # noqa: N802
        if node.name:
            self.names.add(node.name)
        self.generic_visit(node)

    def visit_MatchStar(self, node: ast.MatchStar) -> None:  # noqa: N802
        if node.name:
            self.names.add(node.name)

    def visit_MatchMapping(self, node: ast.MatchMapping) -> None:  # noqa: N802
        if node.rest:
            self.names.add(node.rest)
        self.generic_visit(node)


def _function_local_names(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
) -> set[str]:
    collector = _FunctionLocalBindingCollector()
    arguments = (
        *function.args.posonlyargs,
        *function.args.args,
        *function.args.kwonlyargs,
    )
    collector.names.update(argument.arg for argument in arguments)
    if function.args.vararg is not None:
        collector.names.add(function.args.vararg.arg)
    if function.args.kwarg is not None:
        collector.names.add(function.args.kwarg.arg)
    for statement in function.body:
        collector.visit(statement)
    return collector.names - collector.global_names - collector.nonlocal_names


def _flow_statements(
    statements: Sequence[ast.stmt],
    environments: list[_ImportEnvironment],
    helper_modules: set[str],
    resolved: set[tuple[str, str]],
) -> list[_ImportEnvironment]:
    active = environments
    for statement in statements:
        following: list[_ImportEnvironment] = []
        for environment in active:
            following.extend(
                _flow_statement(statement, environment, helper_modules, resolved)
            )
        active = _deduplicate_environments(following)
        if not active:
            break
    return active


def _flow_statement(
    statement: ast.stmt,
    environment: _ImportEnvironment,
    helper_modules: set[str],
    resolved: set[tuple[str, str]],
) -> list[_ImportEnvironment]:
    if isinstance(statement, (ast.Import, ast.ImportFrom)):
        _apply_import(environment, statement, helper_modules)
        return [environment]
    if isinstance(statement, ast.Expr):
        return _scan_expression(statement.value, [environment], resolved)
    if isinstance(statement, (ast.Return, ast.Raise)):
        active = [environment]
        if isinstance(statement, ast.Return):
            active = _scan_expression(statement.value, active, resolved)
        else:
            active = _scan_expression(statement.exc, active, resolved)
            active = _scan_expression(statement.cause, active, resolved)
        return []
    if isinstance(statement, (ast.Break, ast.Continue)):
        return []
    if isinstance(statement, ast.Assign):
        active = _scan_expression(statement.value, [environment], resolved)
        for current in active:
            for target in statement.targets:
                _invalidate_target(current, target)
        return active
    if isinstance(statement, ast.AnnAssign):
        # A local variable annotation is not proof of a runtime invocation;
        # with postponed annotations, annotations elsewhere are inert too.
        active = _scan_expression(statement.value, [environment], resolved)
        for current in active:
            _invalidate_target(current, statement.target)
        return active
    if isinstance(statement, ast.AugAssign):
        active = _scan_expression(statement.target, [environment], resolved)
        active = _scan_expression(statement.value, active, resolved)
        for current in active:
            _invalidate_target(current, statement.target)
        return active
    if isinstance(statement, ast.Delete):
        for target in statement.targets:
            _invalidate_target(environment, target)
        return [environment]
    if isinstance(statement, ast.If):
        active = _scan_expression(statement.test, [environment], resolved)
        truth = _literal_truth(statement.test)
        if truth is True:
            return _flow_statements(statement.body, active, helper_modules, resolved)
        if truth is False:
            return _flow_statements(statement.orelse, active, helper_modules, resolved)
        return _flow_statements(
            statement.body,
            [_copy_environment(item) for item in active],
            helper_modules,
            resolved,
        ) + _flow_statements(
            statement.orelse,
            [_copy_environment(item) for item in active],
            helper_modules,
            resolved,
        )
    if isinstance(statement, (ast.For, ast.AsyncFor)):
        active = _scan_expression(statement.iter, [environment], resolved)
        if _literal_truth(statement.iter) is False:
            return _flow_statements(
                statement.orelse,
                active,
                helper_modules,
                resolved,
            )
        loop_entries = [_copy_environment(item) for item in active]
        for current in loop_entries:
            _invalidate_target(current, statement.target)
        loop_exits = _flow_statements(
            statement.body,
            loop_entries,
            helper_modules,
            resolved,
        )
        return _flow_statements(
            statement.orelse,
            [*active, *loop_exits],
            helper_modules,
            resolved,
        )
    if isinstance(statement, ast.While):
        active = _scan_expression(statement.test, [environment], resolved)
        truth = _literal_truth(statement.test)
        if truth is False:
            return _flow_statements(statement.orelse, active, helper_modules, resolved)
        loop_exits = _flow_statements(
            statement.body,
            [_copy_environment(item) for item in active],
            helper_modules,
            resolved,
        )
        if truth is True:
            return []
        return _flow_statements(
            statement.orelse,
            [*active, *loop_exits],
            helper_modules,
            resolved,
        )
    if isinstance(statement, (ast.With, ast.AsyncWith)):
        active = [environment]
        for item in statement.items:
            active = _scan_expression(item.context_expr, active, resolved)
            if item.optional_vars is not None:
                for current in active:
                    _invalidate_target(current, item.optional_vars)
        return _flow_statements(statement.body, active, helper_modules, resolved)
    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        active = [environment]
        for decorator in statement.decorator_list:
            active = _scan_expression(decorator, active, resolved)
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in (*statement.args.defaults, *statement.args.kw_defaults):
                active = _scan_expression(default, active, resolved)
        else:
            for base in statement.bases:
                active = _scan_expression(base, active, resolved)
            for keyword in statement.keywords:
                active = _scan_expression(keyword.value, active, resolved)
        for current in active:
            _invalidate_name(current, statement.name)
        return active
    if isinstance(statement, ast.Assert):
        active = _scan_expression(statement.test, [environment], resolved)
        truth = _literal_truth(statement.test)
        if truth is True:
            return active
        _scan_expression(
            statement.msg,
            [_copy_environment(item) for item in active],
            resolved,
        )
        return [] if truth is False else active
    if isinstance(statement, (ast.Try, ast.TryStar)):
        body_exits = _flow_statements(
            statement.body,
            [_copy_environment(environment)],
            helper_modules,
            resolved,
        )
        normal_exits = _flow_statements(
            statement.orelse,
            body_exits,
            helper_modules,
            resolved,
        )
        handler_exits: list[_ImportEnvironment] = []
        for handler in statement.handlers:
            entries = _scan_expression(
                handler.type,
                [_copy_environment(environment)],
                resolved,
            )
            if handler.name:
                for current in entries:
                    _invalidate_name(current, handler.name)
            handler_exits.extend(
                _flow_statements(handler.body, entries, helper_modules, resolved)
            )
        exits = [*normal_exits, *handler_exits]
        if statement.finalbody:
            can_continue = bool(exits)
            final_exits = _flow_statements(
                statement.finalbody,
                exits or [_copy_environment(environment)],
                helper_modules,
                resolved,
            )
            exits = final_exits if can_continue else []
        return exits
    if isinstance(statement, ast.Match):
        active = _scan_expression(statement.subject, [environment], resolved)
        exits: list[_ImportEnvironment] = []
        unmatched = [_copy_environment(item) for item in active]
        for case in statement.cases:
            entries = [_copy_environment(item) for item in active]
            for name in _pattern_bound_names(case.pattern):
                for current in entries:
                    _invalidate_name(current, name)
            entries = _scan_expression(case.guard, entries, resolved)
            exits.extend(
                _flow_statements(case.body, entries, helper_modules, resolved)
            )
            if case.guard is None and isinstance(case.pattern, ast.MatchAs) and (
                case.pattern.pattern is None
            ):
                unmatched = []
                break
        return [*exits, *unmatched]
    active = [environment]
    for child in ast.iter_child_nodes(statement):
        if isinstance(child, ast.expr):
            active = _scan_expression(child, active, resolved)
    return active


def _scan_expression(
    expression: ast.expr | None,
    environments: list[_ImportEnvironment],
    resolved: set[tuple[str, str]],
) -> list[_ImportEnvironment]:
    if expression is None:
        return environments
    if isinstance(expression, ast.Lambda):
        active = environments
        for default in (*expression.args.defaults, *expression.args.kw_defaults):
            active = _scan_expression(default, active, resolved)
        return active
    if isinstance(expression, ast.IfExp):
        active = _scan_expression(expression.test, environments, resolved)
        truth = _literal_truth(expression.test)
        if truth is True:
            return _scan_expression(expression.body, active, resolved)
        if truth is False:
            return _scan_expression(expression.orelse, active, resolved)
        return _scan_expression(
            expression.body,
            [_copy_environment(item) for item in active],
            resolved,
        ) + _scan_expression(
            expression.orelse,
            [_copy_environment(item) for item in active],
            resolved,
        )
    if isinstance(expression, ast.BoolOp):
        active = environments
        for value in expression.values:
            active = _scan_expression(value, active, resolved)
            truth = _literal_truth(value)
            if isinstance(expression.op, ast.And) and truth is False:
                break
            if isinstance(expression.op, ast.Or) and truth is True:
                break
        return active
    if isinstance(expression, ast.Call):
        active = _scan_expression(expression.func, environments, resolved)
        call = _dotted_expression(expression.func)
        if call:
            for direct, modules in active:
                if len(call) == 1 and call[0] in direct:
                    resolved.add(direct[call[0]])
                elif len(call) > 1 and call[:-1] in modules:
                    resolved.add((modules[call[:-1]], call[-1]))
        for argument in expression.args:
            active = _scan_expression(argument, active, resolved)
        for keyword in expression.keywords:
            active = _scan_expression(keyword.value, active, resolved)
        return active
    if isinstance(expression, ast.NamedExpr):
        active = _scan_expression(expression.value, environments, resolved)
        for current in active:
            _invalidate_target(current, expression.target)
        return active
    if isinstance(expression, ast.GeneratorExp):
        # Only the outer iterable is evaluated when a generator is created;
        # its body is not proof that the enclosing function made the call.
        return _scan_expression(expression.generators[0].iter, environments, resolved)
    if isinstance(expression, (ast.ListComp, ast.SetComp, ast.DictComp)):
        inner = [_copy_environment(item) for item in environments]
        for generator in expression.generators:
            inner = _scan_expression(generator.iter, inner, resolved)
            if _literal_truth(generator.iter) is False:
                return environments
            for current in inner:
                _invalidate_target(current, generator.target)
            for condition in generator.ifs:
                inner = _scan_expression(condition, inner, resolved)
                if _literal_truth(condition) is False:
                    return environments
        if isinstance(expression, ast.DictComp):
            inner = _scan_expression(expression.key, inner, resolved)
            _scan_expression(expression.value, inner, resolved)
        else:
            _scan_expression(expression.elt, inner, resolved)
        return environments
    active = environments
    for child in ast.iter_child_nodes(expression):
        if isinstance(child, ast.expr):
            active = _scan_expression(child, active, resolved)
    return active


def _dotted_expression(node: ast.expr) -> tuple[str, ...]:
    if isinstance(node, ast.Name):
        return (node.id,)
    if isinstance(node, ast.Attribute):
        parent = _dotted_expression(node.value)
        return (*parent, node.attr) if parent else ()
    return ()


def _apply_import(
    environment: _ImportEnvironment,
    node: ast.Import | ast.ImportFrom,
    helper_modules: set[str],
) -> None:
    direct, modules = environment
    if isinstance(node, ast.ImportFrom):
        module_parts = tuple(
            part for part in str(node.module or "").split(".") if part
        )
        module = module_parts[-1] if module_parts else ""
        for alias in node.names:
            if alias.name == "*":
                continue
            local_name = alias.asname or alias.name
            _invalidate_name(environment, local_name)
            if module in helper_modules:
                direct[local_name] = (module, alias.name)
            elif alias.name in helper_modules:
                modules[(local_name,)] = alias.name
        return
    for alias in node.names:
        imported_parts = tuple(part for part in alias.name.split(".") if part)
        if not imported_parts:
            continue
        local_name = alias.asname or imported_parts[0]
        _invalidate_name(environment, local_name)
        if imported_parts[-1] in helper_modules:
            local_expression = (alias.asname,) if alias.asname else imported_parts
            modules[local_expression] = imported_parts[-1]


def _invalidate_target(environment: _ImportEnvironment, target: ast.expr) -> None:
    if isinstance(target, ast.Name):
        _invalidate_name(environment, target.id)
        return
    if isinstance(target, (ast.Tuple, ast.List)):
        for item in target.elts:
            _invalidate_target(environment, item)
        return
    if isinstance(target, ast.Starred):
        _invalidate_target(environment, target.value)
        return
    if isinstance(target, ast.Attribute):
        expression = _dotted_expression(target)
        if expression:
            modules = environment[1]
            for key in tuple(modules):
                if key[: len(expression)] == expression or expression[: len(key)] == key:
                    modules.pop(key, None)


def _invalidate_name(environment: _ImportEnvironment, name: str) -> None:
    direct, modules = environment
    direct.pop(name, None)
    for expression in tuple(modules):
        if expression and expression[0] == name:
            modules.pop(expression, None)


def _copy_environment(environment: _ImportEnvironment) -> _ImportEnvironment:
    return dict(environment[0]), dict(environment[1])


def _deduplicate_environments(
    environments: list[_ImportEnvironment],
) -> list[_ImportEnvironment]:
    unique: dict[tuple[object, ...], _ImportEnvironment] = {}
    for environment in environments:
        key = (
            tuple(sorted(environment[0].items())),
            tuple(sorted(environment[1].items())),
        )
        unique[key] = environment
    return list(unique.values())


def _literal_truth(expression: ast.expr) -> bool | None:
    if isinstance(expression, ast.Constant):
        return bool(expression.value)
    if isinstance(expression, (ast.Tuple, ast.List, ast.Set)):
        return bool(expression.elts)
    if isinstance(expression, ast.Dict):
        return bool(expression.keys)
    if isinstance(expression, ast.UnaryOp) and isinstance(expression.op, ast.Not):
        truth = _literal_truth(expression.operand)
        return None if truth is None else not truth
    if isinstance(expression, ast.BoolOp):
        values = [_literal_truth(item) for item in expression.values]
        if isinstance(expression.op, ast.And):
            if False in values:
                return False
            return True if all(value is True for value in values) else None
        if True in values:
            return True
        return False if all(value is False for value in values) else None
    return None


def _pattern_bound_names(pattern: ast.pattern) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(pattern):
        if isinstance(node, ast.MatchAs) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.MatchStar) and node.name:
            names.add(node.name)
        elif isinstance(node, ast.MatchMapping) and node.rest:
            names.add(node.rest)
    return names


class BasicBackendGateRunner:
    def __init__(
        self,
        config: BasicBackendGateConfig,
        *,
        service_factory: GateServiceFactory | None = None,
        oracle_runner: OracleRunner | None = None,
        seed_factory: Callable[[], BasicBackendRunSeed] | None = None,
        docker_identity_resolver: Callable[[str], Mapping[str, Any]] | None = None,
        model_inventory_resolver: Callable[[], Mapping[str, Any]] | None = None,
    ) -> None:
        self.config = config.normalized()
        self.service_factory = service_factory or ProductionGateServiceFactory()
        self.oracle_runner = oracle_runner or run_private_oracle_container
        self.seed_factory = seed_factory or BasicBackendRunSeed.generate
        self.docker_identity_resolver = (
            docker_identity_resolver or _resolve_docker_image_identity
        )
        self.model_inventory_resolver = (
            model_inventory_resolver or _resolve_model_inventory
        )

    def validate_preflight(self, *, require_clean: bool = True) -> dict[str, Any]:
        public_manifest = validate_public_contract()
        tasks = load_basic_backend_tasks()
        if tuple(task.task_id for task in tasks) != EXPECTED_TASK_IDS:
            raise BasicBackendGateError("basic_gate_catalog_order_invalid")
        branch, head = _git_identity(self.config.source_root)
        if branch != self.config.expected_branch:
            raise BasicBackendGateError("basic_gate_branch_mismatch")
        if self.config.expected_head is not None and head != self.config.expected_head:
            raise BasicBackendGateError("basic_gate_head_mismatch")
        status = _git(self.config.source_root, "status", "--porcelain=v1", "--untracked-files=all")
        if require_clean and status.strip():
            raise BasicBackendGateError("basic_gate_source_worktree_dirty")
        trace_map = json.loads((self.config.source_root / CONTROL_TRACE_MAP).read_text(encoding="utf-8"))
        if trace_map.get("status") != "MAPPED_RUNTIME_CONFIRMED_PHASE_0":
            raise BasicBackendGateError("basic_gate_trace_map_not_runtime_confirmed")
        if shutil.which("docker") is None:
            raise BasicBackendGateError("basic_gate_restricted_runtime_unavailable")
        evaluation_contract = _evaluation_contract(self.config.source_root)
        sandbox_image = dict(
            self.docker_identity_resolver(self.config.sandbox_image)
        )
        model_inventory = dict(self.model_inventory_resolver())
        return {
            "schema_version": "source-proxy-basic-backend-10-preflight/v1",
            "passed": True,
            "branch": branch,
            "head": head,
            "clean": not bool(status.strip()),
            "public_manifest_sha256": _sha256_json(public_manifest),
            "task_count": len(tasks),
            "trace_map_status": trace_map["status"],
            "python_executable": str(self.config.python_executable),
            "docker": str(shutil.which("docker")),
            "evaluation_contract": evaluation_contract,
            "sandbox_image": sandbox_image,
            "model_inventory": model_inventory,
        }

    def _assert_runtime_snapshot(
        self,
        *,
        expected_head: str,
        expected_contract: Mapping[str, Any],
        expected_sandbox_image: Mapping[str, Any],
        expected_model_inventory: Mapping[str, Any],
    ) -> None:
        branch, head = _git_identity(self.config.source_root)
        status = _git(
            self.config.source_root,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        )
        if branch != self.config.expected_branch or head != expected_head or status.strip():
            raise BasicBackendGateError("basic_gate_runtime_source_drift")
        if _evaluation_contract(self.config.source_root) != dict(expected_contract):
            raise BasicBackendGateError("basic_gate_runtime_evaluation_contract_drift")
        if dict(self.docker_identity_resolver(self.config.sandbox_image)) != dict(
            expected_sandbox_image
        ):
            raise BasicBackendGateError("basic_gate_runtime_sandbox_image_drift")
        if dict(self.model_inventory_resolver()) != dict(expected_model_inventory):
            raise BasicBackendGateError("basic_gate_runtime_model_inventory_drift")

    def run(self) -> dict[str, Any]:
        preflight = self.validate_preflight(require_clean=True)
        run_id = "basic-backend-10-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(6)
        run_root = self.config.output_root / run_id
        run_root.mkdir(parents=True, mode=0o700, exist_ok=False)
        tasks = load_basic_backend_tasks()
        contract = preflight.get("evaluation_contract")
        sandbox_image = preflight.get("sandbox_image")
        model_inventory = preflight.get("model_inventory")
        if not all(
            isinstance(item, Mapping)
            for item in (contract, sandbox_image, model_inventory)
        ):
            raise BasicBackendGateError("basic_gate_preflight_runtime_identity_missing")
        contract = dict(contract)
        sandbox_image = dict(sandbox_image)
        model_inventory = dict(model_inventory)
        expected_head = str(preflight.get("head") or "")
        self._assert_runtime_snapshot(
            expected_head=expected_head,
            expected_contract=contract,
            expected_sandbox_image=sandbox_image,
            expected_model_inventory=model_inventory,
        )
        phases: list[dict[str, Any]] = []
        phase_manifests: dict[str, str] = {}
        resume_evidence: dict[str, Any] | None = None
        if tuple(self.config.phases) == ("clean_rerun",):
            first_phase, resume_evidence = _load_and_validate_first_phase_manifest(
                self.config.resume_first,
                source_root=self.config.source_root,
                expected_branch=self.config.expected_branch,
                current_head=str(preflight.get("head") or ""),
                current_contract=contract,
                current_sandbox_image=sandbox_image,
                current_model_inventory=model_inventory,
                expected_task_ids=tuple(task.task_id for task in tasks),
            )
            phases.append(first_phase)
        for phase in self.config.phases:
            phase_report = self._run_phase(
                run_root,
                phase,
                tasks,
                expected_head=expected_head,
                expected_contract=contract,
                sandbox_image=sandbox_image,
                model_inventory=model_inventory,
            )
            phases.append(phase_report)
            if len(self.config.phases) == 1:
                self._assert_runtime_snapshot(
                    expected_head=expected_head,
                    expected_contract=contract,
                    expected_sandbox_image=sandbox_image,
                    expected_model_inventory=model_inventory,
                )
                manifest_path = _write_phase_manifest(
                    run_root=run_root,
                    phase_report=phase_report,
                    preflight=preflight,
                    contract=contract,
                    sandbox_image=sandbox_image,
                    model_inventory=model_inventory,
                )
                phase_manifests[phase] = str(manifest_path)
        comparison = _compare_phases(phases)
        first = next((phase for phase in phases if phase["phase"] == "first"), None)
        clean = next((phase for phase in phases if phase["phase"] == "clean_rerun"), None)
        first_repair_successes = int(
            (first or {}).get("repaired_success_count") or 0
        )
        phase_gates = all(bool(phase.get("gate_passed")) for phase in phases)
        complete_phase_sequence = tuple(
            str(phase.get("phase") or "") for phase in phases
        ) == PHASES
        all_ten_executed_per_phase = bool(
            complete_phase_sequence
            and len(phases) == len(PHASES)
            and all(
                phase.get("all_tasks_crossed_authenticated_execution_lifecycle") is True
                and phase.get("executed_task_count") == 10
                for phase in phases
            )
        )
        gate_passed = bool(
            complete_phase_sequence
            and first is not None
            and clean is not None
            and phase_gates
            and all_ten_executed_per_phase
            and first_repair_successes >= 1
            and comparison.get("fresh_seed_commitments") is True
            and comparison.get("all_tasks_compared") is True
        )
        first_only_passed = bool(
            tuple(self.config.phases) == ("first",)
            and first is not None
            and first.get("gate_passed") is True
            and first_repair_successes >= 1
        )
        phase_run_passed = bool(gate_passed or first_only_passed)
        terminal_token = (
            "LOCAL_PROXY_BASIC_CODING_GATE_PASSED"
            if gate_passed
            else "LOCAL_PROXY_BASIC_CODING_FIRST_PHASE_PASSED_RESUME_REQUIRED"
            if first_only_passed
            else "LOCAL_PROXY_BASIC_CODING_GATE_NOT_YET_PASSED"
        )
        report = {
            "schema_version": REPORT_SCHEMA,
            "definition_version": DEFINITION_VERSION,
            "run_id": run_id,
            "created_at": _iso_now(),
            "preflight": preflight,
            "evaluation_contract": contract,
            "sandbox_image": sandbox_image,
            "model_inventory": model_inventory,
            "requested_phases": list(self.config.phases),
            "phases": phases,
            "phase_manifests": phase_manifests,
            "resume_evidence": resume_evidence,
            "comparison": comparison,
            "first_phase_repaired_success_count": first_repair_successes,
            "all_ten_executed_per_phase": all_ten_executed_per_phase,
            "direct_adapter_scoring_used": False,
            "campaign_4_status": "PAUSED_FOR_CAMPAIGN_3_5_BACKEND_PROOF",
            "gate_passed": gate_passed,
            "phase_run_passed": phase_run_passed,
            "terminal_token": terminal_token,
        }
        self._assert_runtime_snapshot(
            expected_head=expected_head,
            expected_contract=contract,
            expected_sandbox_image=sandbox_image,
            expected_model_inventory=model_inventory,
        )
        _write_json(run_root / "gate-report.json", report, private=False)
        return report

    def _run_phase(
        self,
        run_root: Path,
        phase: str,
        tasks: Sequence[BasicBackendTask],
        *,
        expected_head: str,
        expected_contract: Mapping[str, Any],
        sandbox_image: Mapping[str, Any],
        model_inventory: Mapping[str, Any],
    ) -> dict[str, Any]:
        seed = self.seed_factory()
        nonce = secrets.token_urlsafe(24)
        private_seed_markers = _private_seed_markers(seed, nonce)
        phase_root = run_root / phase
        phase_root.mkdir(mode=0o700)
        receipts: list[dict[str, Any]] = []
        for task in tasks:
            self._assert_runtime_snapshot(
                expected_head=expected_head,
                expected_contract=expected_contract,
                expected_sandbox_image=sandbox_image,
                expected_model_inventory=model_inventory,
            )
            rendered = render_basic_backend_task(
                task.task_id,
                run_seed=seed,
                run_nonce=nonce,
                tasks=tuple(tasks),
            )
            receipts.append(
                self._run_task(
                    phase_root,
                    phase,
                    rendered,
                    private_seed_markers=private_seed_markers,
                    expected_head=expected_head,
                    sandbox_image_id=str(sandbox_image.get("image_id") or ""),
                    model_inventory=model_inventory,
                )
            )
            self._assert_runtime_snapshot(
                expected_head=expected_head,
                expected_contract=expected_contract,
                expected_sandbox_image=sandbox_image,
                expected_model_inventory=model_inventory,
            )
        phase_report = _aggregate_phase_receipts(
            phase=phase,
            run_seed_commitment=seed.commitment,
            receipts=receipts,
            expected_task_ids=tuple(task.task_id for task in tasks),
            expected_branch=self.config.expected_branch,
            expected_head=expected_head,
            expected_source_root=self.config.source_root,
            expected_sandbox_image_id=str(sandbox_image.get("image_id") or ""),
            expected_model_inventory=model_inventory,
        )
        phase_report["evaluation_contract_sha256"] = expected_contract.get(
            "contract_sha256"
        )
        self._assert_runtime_snapshot(
            expected_head=expected_head,
            expected_contract=expected_contract,
            expected_sandbox_image=sandbox_image,
            expected_model_inventory=model_inventory,
        )
        return phase_report

    def _run_task(
        self,
        phase_root: Path,
        phase: str,
        rendered: RenderedBasicBackendTask,
        *,
        private_seed_markers: Sequence[bytes] = (),
        expected_head: str,
        sandbox_image_id: str,
        model_inventory: Mapping[str, Any],
    ) -> dict[str, Any]:
        task_id = rendered.definition.task_id
        # Production-visible paths must not disclose the small/enumerable BTxx
        # scorer identifier.  The task seed commitment is fresh per phase and
        # already serves as the public, one-way identity for this fixture.
        opaque_task_key = rendered.task_seed_commitment
        task_root = phase_root / f"task-{opaque_task_key}"
        fixture_parent = task_root / "fixture-parent"
        control_root = task_root / "control"
        state_root = task_root / "state"
        evidence_root = task_root / "evidence"
        private_store = task_root / "private-evaluation"
        for path in (fixture_parent, control_root, state_root, evidence_root, private_store):
            path.mkdir(parents=True, mode=0o700, exist_ok=False)
        fixture = materialize_basic_backend_fixture(fixture_parent, rendered)
        manifest_path = control_root / "fixture-authority.json"
        _write_private_json(manifest_path, fixture.authority_manifest)
        manifest_sha256 = _sha256_file(manifest_path)
        branch, head = _git_identity(self.config.source_root)
        if branch != self.config.expected_branch or head != expected_head:
            raise BasicBackendGateError("basic_gate_task_source_identity_drift")
        if _git(
            self.config.source_root,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ).strip():
            raise BasicBackendGateError("basic_gate_task_source_dirty")
        spec = ServiceLaunchSpec(
            source_root=self.config.source_root,
            fixture=fixture,
            authority_manifest_path=manifest_path,
            state_root=state_root,
            evidence_root=evidence_root,
            python_executable=self.config.python_executable,
            expected_branch=self.config.expected_branch,
            expected_head=expected_head,
            sandbox_image_id=sandbox_image_id,
            model_inventory_sha256=str(model_inventory.get("inventory_sha256") or ""),
            verifier_runtime_sha256=str(
                model_inventory.get("verifier_runtime_sha256") or ""
            ),
            task_label=f"task-seed:{opaque_task_key}",
            startup_timeout_seconds=self.config.startup_timeout_seconds,
            request_timeout_seconds=self.config.request_timeout_seconds,
            inherited_environment=dict(os.environ),
        )
        workflow: dict[str, Any]
        service_receipt: Mapping[str, Any] = {}
        active_service: RunningGateService | None = None
        try:
            with self.service_factory(spec) as service:
                active_service = service
                service_receipt = service.process_receipt
                workflow = self._drive_authenticated_lifecycle(service, rendered)
        except Exception as error:  # continue all ten; preserve a truthful failure
            workflow = {
                "completed": False,
                "terminal_disposition_truthful": False,
                "failure_reason": str(getattr(error, "reason_code", type(error).__name__)),
                "failure_details": dict(getattr(error, "details", {}) or {}),
                "attempts": [],
                "http_exchanges": [
                    exchange.public_payload()
                    for exchange in (
                        active_service.client.exchanges if active_service is not None else []
                    )
                ],
                "final_readback": {},
                "trace_reconciliation": _empty_trace_reconciliation("service_or_workflow_failed"),
            }
        workflow_attempts = [
            item for item in workflow.get("attempts", []) if isinstance(item, Mapping)
        ]
        model_inventory_bound = bool(
            workflow_attempts
            and all(
                _attempt_model_provenance_verified(
                    item,
                    model_inventory=model_inventory,
                    service_model_aliases=(
                        service_receipt.get("model_aliases", {})
                        if isinstance(service_receipt, Mapping)
                        else {}
                    ),
                )
                for item in workflow_attempts
            )
        )
        workflow["model_inventory_bound"] = model_inventory_bound
        workflow["local_model_path_verified"] = bool(
            workflow.get("local_model_path_verified") is True
            and model_inventory_bound
        )
        # The oracle never shares a process lifetime with Source Proxy.
        try:
            oracle = dict(
                self.oracle_runner(
                    task_id=task_id,
                    workspace_root=fixture.root,
                    values=rendered.values,
                    private_store=private_store,
                    source_root=self.config.source_root,
                    python_executable=self.config.python_executable,
                    inherited_environment={
                        **dict(os.environ),
                        "SOURCE_PROXY_BASIC_GATE_ORACLE_IMAGE": sandbox_image_id,
                    },
                )
            )
        except Exception as error:
            oracle = {
                "passed": False,
                "failure_reason": str(getattr(error, "reason_code", type(error).__name__)),
                "process_separate_from_source_proxy": True,
                "sandbox_image_id": sandbox_image_id,
            }
        mutation = _audit_fixture_mutations(fixture)
        applied_diff = _workspace_diff(fixture.root)
        applied_diff_path = evidence_root / "applied-workspace.diff"
        applied_diff_path.write_text(applied_diff, encoding="utf-8")
        os.chmod(applied_diff_path, 0o600)
        mutation["applied_diff_sha256"] = _sha256_text(applied_diff)
        mutation["applied_diff_evidence_file"] = str(applied_diff_path)
        leak = _hidden_answer_leak_audit(
            workflow,
            rendered=rendered,
            raw_seed_values_forbidden=True,
            private_seed_markers=private_seed_markers,
            production_roots=(state_root, evidence_root, fixture.root),
            service_receipt=service_receipt,
        )
        required_evidence = dict(workflow.get("required_evidence_index") or {})
        required_evidence.update(
            {
                "applied_diff": {
                    "sha256": mutation["applied_diff_sha256"],
                    "evidence_file": mutation["applied_diff_evidence_file"],
                },
                "private_oracle": {
                    "passed": oracle.get("passed") is True,
                    "private_payload_sha256": oracle.get("private_payload_sha256"),
                    "evidence_file": oracle.get("private_evidence_file"),
                    "candidate_observations_sha256": oracle.get(
                        "candidate_observations_sha256"
                    ),
                },
                "final_receipt": str(task_root / "task-receipt.json"),
            }
        )
        execution_lifecycle = _authenticated_execution_lifecycle_audit(workflow)
        production_completed = workflow.get("completed") is True
        production_proof = workflow.get("production_proof")
        proof_eligible = bool(
            isinstance(production_proof, Mapping)
            and production_proof.get("terminal_proof_eligible") is True
        )
        trace_passed = workflow.get("trace_reconciliation", {}).get("passed") is True
        actual_change = bool(mutation["changed_paths"])
        completion_claim = _completion_claim_audit(
            workflow,
            actual_change=actual_change,
            independent_verification_passed=oracle.get("passed") is True,
        )
        fabricated = int(completion_claim["fabricated_completion_count"])
        expected_terminal_disposition = rendered.definition.expected_terminal_disposition
        disposition_matches = bool(
            completion_claim["normalized_terminal_disposition"]
            == expected_terminal_disposition
        )
        terminal_truthful = bool(completion_claim["terminal_disposition_truthful"])
        oracle_evidence_valid = _private_oracle_evidence_valid(
            oracle,
            expected_sandbox_image_id=sandbox_image_id,
            expected_task_id=task_id,
        )
        verifier_runtime_valid = _verifier_runtime_evidence_valid(
            workflow.get("verifier_runtime_evidence"),
            expected_sandbox_image_id=sandbox_image_id,
            expected_runtime_sha256=str(
                model_inventory.get("verifier_runtime_sha256") or ""
            ),
        )
        service_runtime_bound = bool(
            service_receipt.get("branch") == self.config.expected_branch
            and service_receipt.get("head") == expected_head
            and service_receipt.get("cwd") == str(self.config.source_root)
            and service_receipt.get("service_process_per_task") is True
            and service_receipt.get("sandbox_image_id") == sandbox_image_id
            and service_receipt.get("model_inventory_sha256")
            == model_inventory.get("inventory_sha256")
            and service_receipt.get("verifier_runtime_sha256")
            == model_inventory.get("verifier_runtime_sha256")
        )
        passed = bool(
            production_completed
            and proof_eligible
            and actual_change
            and workflow.get("approved_diff_applied") is True
            and workflow.get("public_tests_passed") is True
            and workflow.get("local_model_path_verified") is True
            and oracle_evidence_valid
            and verifier_runtime_valid
            and service_runtime_bound
            and trace_passed
            and mutation["unauthorized_mutation_count"] == 0
            and leak["hidden_answer_leak_count"] == 0
            and fabricated == 0
            and terminal_truthful
            and disposition_matches
        )
        receipt_path = task_root / "task-receipt.json"
        receipt = {
            "schema_version": TASK_RECEIPT_SCHEMA,
            "definition_version": DEFINITION_VERSION,
            "phase": phase,
            "task_id": task_id,
            "opaque_task_key": opaque_task_key,
            "receipt_file": str(receipt_path),
            "category": rendered.definition.category,
            "task_seed_commitment": rendered.task_seed_commitment,
            "human_prompt_sha256": _sha256_text(rendered.prompt),
            "fixture_content_sha256": fixture.content_sha256,
            "fixture_root": str(fixture.root),
            "baseline_commit": fixture.baseline_commit,
            "baseline_tree": fixture.baseline_tree,
            "authority_manifest_sha256": manifest_sha256,
            "authority_schema_version": fixture.authority_manifest["schema_version"],
            "source_head": expected_head,
            "source_branch": self.config.expected_branch,
            "source_root": str(self.config.source_root),
            "sandbox_image_id": sandbox_image_id,
            "model_inventory": dict(model_inventory),
            "model_inventory_sha256": model_inventory.get("inventory_sha256"),
            "verifier_runtime_sha256": model_inventory.get(
                "verifier_runtime_sha256"
            ),
            "service_process": dict(service_receipt),
            "workflow": workflow,
            "authenticated_execution_lifecycle": execution_lifecycle,
            "authenticated_execution_lifecycle_crossed": execution_lifecycle["crossed"],
            "private_oracle": oracle,
            "mutation_audit": mutation,
            "hidden_answer_isolation": leak,
            "required_evidence_index": required_evidence,
            "production_proof": dict(production_proof) if isinstance(production_proof, Mapping) else {},
            "completion_claim_audit": completion_claim,
            "raw_service_status": completion_claim["raw_service_status"],
            "normalized_terminal_disposition": completion_claim[
                "normalized_terminal_disposition"
            ],
            "expected_terminal_disposition": expected_terminal_disposition,
            "expected_terminal_disposition_matches": disposition_matches,
            "repair_succeeded": bool(workflow.get("repair_succeeded")),
            "attempt_count": int(workflow.get("attempt_count") or 0),
            "unauthorized_mutation_count": mutation["unauthorized_mutation_count"],
            "fabricated_completion_count": fabricated,
            "hidden_answer_leak_count": leak["hidden_answer_leak_count"],
            "terminal_disposition_truthful": terminal_truthful,
            "passed": passed,
        }
        _write_json(receipt_path, receipt, private=False)
        return receipt

    def _drive_authenticated_lifecycle(
        self,
        service: RunningGateService,
        rendered: RenderedBasicBackendTask,
    ) -> dict[str, Any]:
        client = service.client
        authority_assertion = service.signer.assertion(
            task_id=_OPERATOR_TASK_ID,
            preview_id=_OPERATOR_PREVIEW_ID,
            generation=1,
        )
        authority = client.request(
            "POST",
            "/v1/campaigns/campaign-3.5/model-call-authority",
            headers={"x-spiritos-operator-assertion": authority_assertion},
        )
        if authority.response.get("state") != "approved":
            raise BasicBackendGateError("basic_gate_model_call_authority_not_approved")
        created = client.request(
            "POST",
            "/v1/tasks/long-running",
            {"description": rendered.prompt},
        )
        task_payload = created.response.get("task")
        task_id = str(task_payload.get("id") or "") if isinstance(task_payload, Mapping) else ""
        if not task_id:
            raise BasicBackendGateError("basic_gate_durable_task_id_missing")
        plugin = _generic_plugin_declaration()
        attempts: list[dict[str, Any]] = []
        final_response: Mapping[str, Any] = {}
        for attempt_number in range(1, MAX_ATTEMPTS + 1):
            proposal_exchange = client.request(
                "POST",
                f"/v1/tasks/long-running/{task_id}/target-plugin-proposal",
                {
                    "task": rendered.prompt,
                    "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID,
                    "target_plugin": plugin,
                },
                allow_error=True,
            )
            proposal_state = _orchestrator_state(proposal_exchange.response)
            proposal = proposal_state.get("target_plugin_proposal")
            if not proposal_exchange.ok or not isinstance(proposal, Mapping):
                attempts.append(
                    {
                        "attempt_number": attempt_number,
                        "proposal_response_sha256": proposal_exchange.response_sha256,
                        "status": "proposal_failed",
                        "reason_code": _response_reason(proposal_exchange.response),
                    }
                )
                break
            material = _proposal_material(proposal_state, proposal_exchange.response)
            model_identity = _proposal_model_identity(proposal_state, proposal)
            producer_raw_response_sha256 = _proposal_producer_raw_response_sha256(
                proposal
            )
            adapter_provenance = proposal.get("target_adapter_provenance")
            producer_model_alias = (
                str(adapter_provenance.get("selected_model_alias") or "")
                if isinstance(adapter_provenance, Mapping)
                else ""
            )
            preview_exchange = client.request(
                "POST",
                f"/v1/tasks/long-running/{task_id}/approval-preview",
                {
                    "action": ACTION,
                    "approved_diff": material["approved_diff"],
                    "target": material["target"],
                    "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID,
                    "context_hash": material["context_hash"],
                    "runtime_output_id": material["runtime_output_id"],
                    "target_plugin": plugin,
                },
            )
            preview = preview_exchange.response.get("preview")
            if not isinstance(preview, Mapping):
                raise BasicBackendGateError("basic_gate_approval_preview_missing")
            preview_id = str(preview.get("preview_id") or "")
            generation = int(preview.get("generation") or 0)
            if not preview_id or generation < 1 or preview.get("state") != "previewed":
                raise BasicBackendGateError("basic_gate_approval_preview_invalid")
            assertion = service.signer.assertion(
                task_id=task_id,
                preview_id=preview_id,
                generation=generation,
            )
            approval_exchange = client.request(
                "POST",
                f"/v1/tasks/long-running/{task_id}/operator-approval",
                {"action": "approve", "preview_id": preview_id, "generation": generation},
                headers={"x-spiritos-operator-assertion": assertion},
            )
            approval = approval_exchange.response.get("approval")
            if not isinstance(approval, Mapping):
                raise BasicBackendGateError("basic_gate_operator_approval_missing")
            approval_id = str(approval.get("approval_id") or "")
            if not approval_id or approval.get("state") != "approved":
                raise BasicBackendGateError("basic_gate_operator_approval_invalid")
            execute_exchange = client.request(
                "POST",
                f"/v1/tasks/long-running/{task_id}/execute-approved",
                {
                    "action": ACTION,
                    "approval_id": approval_id,
                    "approved_by": "spiritos-local-operator",
                    "approved_diff": material["approved_diff"],
                    "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID,
                    "context_hash": material["context_hash"],
                    "runtime_output_id": material["runtime_output_id"],
                    "target": material["target"],
                    "test_command": ["python", "-m", "pytest", "-q"],
                },
                allow_error=True,
            )
            attempt = {
                "attempt_number": attempt_number,
                "orchestrator_attempt_id": proposal.get("attempt_id"),
                "parent_attempt_id": proposal.get("parent_attempt_id"),
                "runtime_output_id": material["runtime_output_id"],
                "proposal_binding_sha256": proposal.get("proposal_binding_sha256"),
                "approved_diff_sha256": _sha256_text(material["approved_diff"]),
                "proposed_patch_evidence_file": proposal_exchange.evidence_file,
                "context_manifest": {
                    "context_hash": material["context_hash"],
                    "canonical_context_report_sha256": proposal.get(
                        "canonical_context_report_sha256"
                    ),
                    "context_runtime_artifact_sha256": proposal.get(
                        "context_runtime_artifact_sha256"
                    ),
                    "context_consumption_id": proposal.get("context_consumption_id"),
                },
                "model_identity": model_identity,
                "target_adapter_provenance": (
                    dict(adapter_provenance)
                    if isinstance(adapter_provenance, Mapping)
                    else {}
                ),
                "producer_model_output_sha256": proposal.get(
                    "producer_model_output_sha256"
                ),
                "producer_raw_response_sha256": producer_raw_response_sha256,
                "producer_model_alias": producer_model_alias,
                "repair_evidence": {
                    "repair_context": (
                        dict(proposal.get("repair_context"))
                        if isinstance(proposal.get("repair_context"), Mapping)
                        else {}
                    ),
                    "repair_input_sha256": proposal.get("repair_input_sha256"),
                    "repair_prompt_sha256": proposal.get("repair_prompt_sha256"),
                    "repair_strategy_signature": proposal.get("repair_strategy_signature"),
                    "failure_class": (
                        proposal.get("repair_context", {}).get("failure_class")
                        if isinstance(proposal.get("repair_context"), Mapping)
                        else None
                    ),
                },
                "preview_id": preview_id,
                "preview_generation": generation,
                "approval_id": approval_id,
                "proposal_response_sha256": proposal_exchange.response_sha256,
                "preview_response_sha256": preview_exchange.response_sha256,
                "approval_response_sha256": approval_exchange.response_sha256,
                "execute_response_sha256": execute_exchange.response_sha256,
                "preview_evidence_file": preview_exchange.evidence_file,
                "approval_evidence_file": approval_exchange.evidence_file,
                "execute_evidence_file": execute_exchange.evidence_file,
                "execute_status_code": execute_exchange.status_code,
                "reviewer_result_evidence_file": execute_exchange.evidence_file,
                "resource_use": {
                    "proposal_elapsed_ms": proposal_exchange.elapsed_ms,
                    "approval_preview_elapsed_ms": preview_exchange.elapsed_ms,
                    "operator_approval_elapsed_ms": approval_exchange.elapsed_ms,
                    "execute_and_review_elapsed_ms": execute_exchange.elapsed_ms,
                },
                "fresh_exact_approval": True,
            }
            attempts.append(attempt)
            if not execute_exchange.ok:
                state_exchange = client.request(
                    "GET",
                    f"/v1/tasks/long-running/{task_id}",
                )
                state = _orchestrator_state(state_exchange.response)
                repair_request = state.get("repair_request")
                if isinstance(repair_request, Mapping) and attempt_number < MAX_ATTEMPTS:
                    attempt["repair_request"] = dict(repair_request)
                    attempt["attempt_seal_sha256"] = repair_request.get(
                        "parent_attempt_seal_sha256"
                    )
                    attempt["status"] = "repair_required_after_reviewer"
                    continue
                attempt["status"] = "execute_failed"
                final_response = state_exchange.response
                break
            verification_exchange = client.request(
                "POST",
                f"/v1/tasks/long-running/{task_id}/verification",
                {
                    "confirm_backup_audit_present": True,
                    "confirm_changed_files_reviewed": True,
                    "confirm_expected_change_present": True,
                    "confirm_no_unintended_files": True,
                    "run_code_verification": True,
                    "verification_profile": "generic_backend",
                    "run_snapshot_verification": True,
                    "verification_note": "Basic Backend 10 server-owned restricted verification.",
                },
                allow_error=True,
            )
            attempt["verification_response_sha256"] = verification_exchange.response_sha256
            attempt["verification_status_code"] = verification_exchange.status_code
            attempt["verifier_result_evidence_file"] = verification_exchange.evidence_file
            attempt["resource_use"]["verification_elapsed_ms"] = verification_exchange.elapsed_ms
            verification_state = _orchestrator_state(verification_exchange.response)
            if (
                verification_exchange.ok
                and isinstance(verification_state.get("repair_request"), Mapping)
                and attempt_number < MAX_ATTEMPTS
            ):
                attempt["repair_request"] = dict(
                    verification_state["repair_request"]
                )
                attempt["attempt_seal_sha256"] = verification_state[
                    "repair_request"
                ].get("parent_attempt_seal_sha256")
                attempt["status"] = "repair_required_after_verifier"
                continue
            attempt["status"] = "verification_completed" if verification_exchange.ok else "verification_failed"
            final_response = verification_exchange.response
            break
        final_exchange = client.request(
            "GET",
            f"/v1/tasks/long-running/{task_id}",
        )
        final_response = final_exchange.response or final_response
        orchestrator = _orchestrator_state(final_response)
        task = final_response.get("task") if isinstance(final_response.get("task"), Mapping) else {}
        snapshot = task.get("ast_snapshot") if isinstance(task.get("ast_snapshot"), Mapping) else {}
        proof = snapshot.get("coding_production_proof") if isinstance(snapshot.get("coding_production_proof"), Mapping) else {}
        post_apply = snapshot.get("post_apply_verification") if isinstance(snapshot.get("post_apply_verification"), Mapping) else {}
        verifier_runtime_evidence = (
            post_apply.get("backend_verification")
            if isinstance(post_apply.get("backend_verification"), Mapping)
            else {}
        )
        trace = reconcile_basic_backend_trace(
            task_id=task_id,
            orchestrator=orchestrator,
            authority_exchange=authority,
            create_exchange=created,
            final_exchange=final_exchange,
        )
        raw_task_completed_claim = task.get("status") == "completed"
        completed = bool(
            raw_task_completed_claim and proof.get("terminal_proof_eligible") is True
        )
        public_tests_passed = _public_tests_passed(post_apply)
        approval_ids = [str(attempt.get("approval_id") or "") for attempt in attempts]
        fresh_approvals = bool(approval_ids and len(approval_ids) == len(set(approval_ids)))
        repair_succeeded = completed and len(attempts) > 1 and fresh_approvals
        local_model_path_verified = bool(
            attempts
            and all(_attempt_model_provenance_verified(attempt) for attempt in attempts)
        )
        terminal_truthful = bool(
            final_exchange.ok
            and isinstance(task, Mapping)
            and str(task.get("status") or "")
            and (
                not raw_task_completed_claim
                or (completed and public_tests_passed)
            )
        )
        return {
            "authenticated_model_call_authority": authority.public_payload(),
            "durable_task_create": created.public_payload(),
            "task_id_sha256": _sha256_text(task_id),
            "attempts": attempts,
            "attempt_count": len(attempts),
            "repair_succeeded": repair_succeeded,
            "fresh_approval_per_attempt": fresh_approvals,
            "approved_diff_applied": bool(
                attempts and any(attempt.get("execute_status_code") in range(200, 300) for attempt in attempts)
            ),
            "public_tests_passed": public_tests_passed,
            "local_model_path_verified": local_model_path_verified,
            "completed": completed,
            "raw_task_completed_claim": raw_task_completed_claim,
            "terminal_disposition": str(task.get("status") or "unknown"),
            "terminal_disposition_truthful": terminal_truthful,
            "production_proof": dict(proof),
            "verifier_runtime_evidence": dict(verifier_runtime_evidence),
            "trace_reconciliation": trace,
            "final_readback_response_sha256": final_exchange.response_sha256,
            "final_readback_evidence_file": final_exchange.evidence_file,
            "required_evidence_index": {
                "human_prompt": {
                    "sha256": _sha256_text(rendered.prompt),
                    "evidence_file": created.evidence_file,
                },
                "context_model_patch_diagnostics_repairs": [
                    {
                        "attempt_number": attempt.get("attempt_number"),
                        "proposal": attempt.get("proposed_patch_evidence_file"),
                        "context_manifest": attempt.get("context_manifest"),
                        "model_identity": attempt.get("model_identity"),
                        "producer_model_output_sha256": attempt.get(
                            "producer_model_output_sha256"
                        ),
                        "producer_raw_response_sha256": attempt.get(
                            "producer_raw_response_sha256"
                        ),
                        "repair_evidence": attempt.get("repair_evidence"),
                    }
                    for attempt in attempts
                ],
                "reviewer_results": [
                    attempt.get("reviewer_result_evidence_file") for attempt in attempts
                    if attempt.get("reviewer_result_evidence_file")
                ],
                "verifier_public_tests_runtime": [
                    attempt.get("verifier_result_evidence_file") for attempt in attempts
                    if attempt.get("verifier_result_evidence_file")
                ],
                "agent_tool_trace_and_final_proof": final_exchange.evidence_file,
                "resource_use": [attempt.get("resource_use", {}) for attempt in attempts],
            },
            "http_exchanges": [exchange.public_payload() for exchange in client.exchanges],
            "direct_adapter_scoring_used": False,
        }


def reconcile_basic_backend_trace(
    *,
    task_id: str,
    orchestrator: Mapping[str, Any],
    authority_exchange: HttpExchange,
    create_exchange: HttpExchange,
    final_exchange: HttpExchange,
) -> dict[str, Any]:
    """Map Basic 10 names to persisted production evidence without renaming it."""

    events = [item for item in orchestrator.get("causal_events", []) if isinstance(item, Mapping)]
    history = [item for item in orchestrator.get("attempt_history", []) if isinstance(item, Mapping)]
    archived_events: list[Mapping[str, Any]] = []
    archived_participants: list[Mapping[str, Any]] = []
    for seal in history:
        state = seal.get("attempt_state")
        if isinstance(state, Mapping):
            archived_events.extend(
                item for item in state.get("causal_events", []) if isinstance(item, Mapping)
            )
            archived_participants.extend(
                item for item in state.get("participant_records", []) if isinstance(item, Mapping)
            )
    all_events = archived_events + events
    participants = archived_participants + [
        item for item in orchestrator.get("participant_records", []) if isinstance(item, Mapping)
    ]
    lane_transitions = [
        event
        for event in all_events
        if event.get("event_type") == "lane_transition"
    ]
    mapping: dict[str, dict[str, Any]] = {
        "authenticated_request_accepted": {
            "production_evidence": (
                "signed operator assertion accepted and durable model-call authority issued; "
                "subsequent task creation is unsigned loopback transport"
            ),
            "present": authority_exchange.ok
            and authority_exchange.response.get("state") == "approved"
            and bool(authority_exchange.response.get("authorization_id"))
            and _signed_operator_authority_acknowledged(authority_exchange)
            and create_exchange.ok
            and not create_exchange.authenticated,
            "evidence": [authority_exchange.response_sha256, create_exchange.response_sha256],
        },
        "durable_task_created": {
            "production_evidence": "run_requested",
            "present": any(event.get("event_type") == "run_requested" for event in all_events)
            and orchestrator.get("task_id") == task_id,
            "evidence": _event_ids(all_events, "run_requested"),
        },
        "planner_or_router_decision": {
            "production_evidence": "lane_transition(planner -> completed)",
            "present": any(
                event.get("lane_id") == "planner" and event.get("status_after") == "completed"
                for event in lane_transitions
            ),
            "evidence": [
                str(event.get("event_id"))
                for event in lane_transitions
                if event.get("lane_id") == "planner"
            ],
        },
        "coder_or_terminal_disposition": {
            "production_evidence": "target_plugin_proposal_ready or target_plugin_non_mutating_result",
            "present": any(
                event.get("event_type")
                in {"target_plugin_proposal_ready", "target_plugin_non_mutating_result"}
                for event in all_events
            ),
            "evidence": [
                str(event.get("event_id"))
                for event in all_events
                if event.get("event_type")
                in {"target_plugin_proposal_ready", "target_plugin_non_mutating_result"}
            ],
        },
        "reviewer_result": {
            "production_evidence": "participant_output(coding-reviewer)",
            "present": any(record.get("role") == "coding-reviewer" for record in participants),
            "evidence": [
                str(record.get("output_id"))
                for record in participants
                if record.get("role") == "coding-reviewer"
            ],
        },
        "verifier_result": {
            "production_evidence": "participant_output(coding-verifier) and post_apply_verification_requested",
            "present": any(record.get("role") == "coding-verifier" for record in participants)
            and any(event.get("event_type") == "post_apply_verification_requested" for event in all_events),
            "evidence": [
                str(record.get("output_id"))
                for record in participants
                if record.get("role") == "coding-verifier"
            ]
            + _event_ids(all_events, "post_apply_verification_requested"),
        },
        "evidence_envelope_written": {
            "production_evidence": "evidence-recorder participant output consumed",
            "present": any(record.get("role") == "evidence-recorder" for record in participants),
            "evidence": [
                str(record.get("output_id"))
                for record in participants
                if record.get("role") == "evidence-recorder"
            ],
        },
        "final_receipt_written": {
            "production_evidence": "final_result",
            "present": any(event.get("event_type") == "final_result" for event in all_events)
            and final_exchange.ok,
            "evidence": _event_ids(all_events, "final_result") + [final_exchange.response_sha256],
        },
    }
    return {
        "schema_version": TRACE_SCHEMA,
        "mode": "mapped_production_events",
        "synthetic_events_used": False,
        "control_map": str(CONTROL_TRACE_MAP),
        "requirements": mapping,
        "passed": all(item["present"] is True for item in mapping.values()),
    }


def validate_basic_backend_gate_configuration(
    config: BasicBackendGateConfig,
    *,
    require_clean: bool = True,
) -> dict[str, Any]:
    return BasicBackendGateRunner(config).validate_preflight(require_clean=require_clean)


def _proposal_material(
    state: Mapping[str, Any], response: Mapping[str, Any]
) -> dict[str, str]:
    proposal = state.get("target_plugin_proposal")
    if not isinstance(proposal, Mapping):
        raise BasicBackendGateError("basic_gate_target_plugin_proposal_missing")
    output_id = str(proposal.get("runtime_output_id") or "")
    approved_diff = ""
    for output in state.get("runtime_outputs", []):
        if isinstance(output, Mapping) and output.get("output_id") == output_id:
            payload = output.get("payload")
            if isinstance(payload, Mapping):
                approved_diff = str(payload.get("approved_diff") or "")
                break
    if not approved_diff:
        result = response.get("target_plugin_result")
        if isinstance(result, Mapping):
            approved_diff = str(result.get("proposed_diff") or "")
    material = {
        "runtime_output_id": output_id,
        "approved_diff": approved_diff,
        "target": str(proposal.get("target") or ""),
        "context_hash": str(proposal.get("context_hash") or ""),
    }
    if any(not value for value in material.values()):
        raise BasicBackendGateError("basic_gate_target_plugin_material_incomplete")
    if _sha256_text(approved_diff) != proposal.get("approved_diff_sha256"):
        raise BasicBackendGateError("basic_gate_target_plugin_diff_hash_mismatch")
    if proposal.get("status") != "ready_for_approval_preview":
        raise BasicBackendGateError("basic_gate_target_plugin_proposal_not_ready")
    return material


def _proposal_model_identity(
    state: Mapping[str, Any],
    proposal: Mapping[str, Any],
) -> dict[str, Any]:
    invocation_id = str(proposal.get("producer_model_invocation_id") or "")
    candidates = [
        item for item in state.get("model_invocations", []) if isinstance(item, Mapping)
    ]
    for seal in state.get("attempt_history", []):
        attempt_state = seal.get("attempt_state") if isinstance(seal, Mapping) else None
        if isinstance(attempt_state, Mapping):
            candidates.extend(
                item
                for item in attempt_state.get("model_invocations", [])
                if isinstance(item, Mapping)
            )
    match = next(
        (item for item in candidates if str(item.get("invocation_id") or "") == invocation_id),
        None,
    )
    if not isinstance(match, Mapping):
        return {
            "invocation_id": invocation_id or None,
            "provider": None,
            "model": None,
            "input_sha256": None,
            "output_sha256": proposal.get("producer_model_output_sha256"),
        }
    return {
        "invocation_id": invocation_id,
        "provider": match.get("provider"),
        "model": match.get("model"),
        "input_sha256": match.get("input_sha256"),
        "output_sha256": match.get("output_sha256"),
        "artifact_sha256": match.get("artifact_sha256"),
        "started_at": match.get("started_at"),
        "completed_at": match.get("completed_at"),
    }


def _proposal_producer_raw_response_sha256(proposal: Mapping[str, Any]) -> str:
    """Return the final coder call's raw hash, never the composite output hash."""

    adapter = proposal.get("target_adapter_provenance")
    if not isinstance(adapter, Mapping):
        return ""
    calls = [item for item in adapter.get("calls", []) if isinstance(item, Mapping)]
    successful_coder_calls = [
        item
        for item in calls
        if item.get("stage") == "coder"
        and item.get("completed") is True
        and item.get("raw_response_observed") is True
    ]
    if not successful_coder_calls:
        return ""
    producer = successful_coder_calls[-1]
    raw_sha256 = str(producer.get("raw_response_sha256") or "")
    if (
        not _sha256_digest_present(raw_sha256)
        or producer.get("call_index") != adapter.get("producer_call_index")
        or adapter.get("raw_response_sha256") != raw_sha256
        or adapter.get("selected_model_alias") != producer.get("model_alias")
        or adapter.get("provider") != producer.get("provider")
        or adapter.get("model") != producer.get("model")
    ):
        return ""
    return raw_sha256


def _attempt_model_provenance_verified(
    attempt: Mapping[str, Any],
    *,
    model_inventory: Mapping[str, Any] | None = None,
    service_model_aliases: Mapping[str, Any] | None = None,
) -> bool:
    identity = attempt.get("model_identity")
    adapter = attempt.get("target_adapter_provenance")
    producer_output_sha256 = str(
        attempt.get("producer_model_output_sha256") or ""
    )
    calls = (
        [item for item in adapter.get("calls", []) if isinstance(item, Mapping)]
        if isinstance(adapter, Mapping)
        else []
    )
    successful_coder_calls = [
        item
        for item in calls
        if item.get("stage") == "coder"
        and item.get("completed") is True
        and item.get("raw_response_observed") is True
    ]
    producer = successful_coder_calls[-1] if successful_coder_calls else {}
    producer_raw_sha256 = str(attempt.get("producer_raw_response_sha256") or "")
    base_valid = bool(
        isinstance(identity, Mapping)
        and isinstance(adapter, Mapping)
        and calls
        and len(calls) == adapter.get("call_count")
        and all(
            call.get("call_index") == index
            and call.get("stage") in {"architect", "coder", "reviewer"}
            and call.get("completed") is True
            and call.get("raw_response_observed") is True
            and _sha256_digest_present(call.get("rendered_prompt_sha256"))
            and _sha256_digest_present(call.get("raw_response_sha256"))
            for index, call in enumerate(calls, start=1)
        )
        and adapter.get("transport_kind") == "canonical_litellm_router"
        and adapter.get("provider_call_authorized") is True
        and adapter.get("model_call_accounting_complete") is True
        and adapter.get("producer_identity_bound") is True
        and adapter.get("producer_call_index") == producer.get("call_index")
        and adapter.get("selected_model_alias") == producer.get("model_alias")
        and adapter.get("provider") == producer.get("provider")
        and adapter.get("model") == producer.get("model")
        and adapter.get("raw_response_sha256") == producer_raw_sha256
        and producer.get("raw_response_sha256") == producer_raw_sha256
        and attempt.get("producer_model_alias") == producer.get("model_alias")
        and identity.get("provider") == "ollama"
        and identity.get("provider") == producer.get("provider")
        and identity.get("model") == producer.get("model")
        and str(identity.get("model") or "").startswith("ollama_chat/")
        and _sha256_digest_present(identity.get("input_sha256"))
        and _sha256_digest_present(identity.get("output_sha256"))
        and _sha256_digest_present(identity.get("artifact_sha256"))
        and _sha256_digest_present(producer_output_sha256)
        and identity.get("output_sha256") == producer_output_sha256
        and _sha256_digest_present(producer_raw_sha256)
        and producer_output_sha256 != producer_raw_sha256
    )
    if not base_valid or model_inventory is None:
        return base_valid
    entries = {
        str(item.get("role") or ""): item
        for item in model_inventory.get("models", [])
        if isinstance(item, Mapping) and item.get("role")
    }
    aliases = (
        {str(key): str(value) for key, value in service_model_aliases.items()}
        if isinstance(service_model_aliases, Mapping)
        else {}
    )
    if aliases and any(
        role not in entries or entries[role].get("alias") != alias
        for role, alias in aliases.items()
    ):
        return False
    coder_ordinal = 0
    evidence_guided_repair = int(attempt.get("attempt_number") or 0) > 1
    for call in calls:
        stage = str(call.get("stage") or "")
        if stage == "architect":
            permitted_roles = ("architect",)
        elif stage == "reviewer":
            permitted_roles = ("reviewer",)
        else:
            coder_ordinal += 1
            permitted_roles = (
                ("coder_repair",)
                if evidence_guided_repair or coder_ordinal > 1
                else ("coder_primary", "coder_fallback")
            )
        matched = False
        for role in permitted_roles:
            entry = entries.get(role)
            if not isinstance(entry, Mapping):
                continue
            if (
                entry.get("alias") == call.get("model_alias")
                and entry.get("provider") == call.get("provider") == "ollama"
                and entry.get("routed_model")
                == (call.get("routed_model") or call.get("model"))
                == call.get("model")
                and _sha256_digest_present(entry.get("artifact_digest"))
                and (not aliases or aliases.get(role) == entry.get("alias"))
            ):
                matched = True
                break
        if not matched:
            return False
    return True


def _orchestrator_state(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    direct = payload.get("coding_orchestrator")
    if isinstance(direct, Mapping):
        return direct
    if payload.get("schema_version") == "coding-orchestrator/v2":
        return payload
    task = payload.get("task")
    snapshot = task.get("ast_snapshot") if isinstance(task, Mapping) else None
    nested = snapshot.get("coding_orchestrator") if isinstance(snapshot, Mapping) else None
    return nested if isinstance(nested, Mapping) else {}


def _public_tests_passed(post_apply: Mapping[str, Any]) -> bool:
    checks = post_apply.get("checks")
    if post_apply.get("status") != "verified" or not isinstance(checks, list):
        return False
    required = [item for item in checks if isinstance(item, Mapping) and item.get("required") is True]
    return bool(required) and all(item.get("status") == "passed" for item in required)


def _server_acknowledged_signed_operator_authority(
    *,
    path: str,
    status_code: int,
    response: Mapping[str, Any],
) -> bool:
    """Recognize only server responses produced after signed assertion checks."""

    if status_code not in range(200, 300):
        return False
    if path == "/v1/campaigns/campaign-3.5/model-call-authority":
        return bool(
            response.get("state") == "approved"
            and str(response.get("authorization_id") or "")
        )
    if path.endswith("/operator-approval"):
        approval = response.get("approval")
        return bool(
            isinstance(approval, Mapping)
            and approval.get("state") == "approved"
            and str(approval.get("approval_id") or "")
        )
    return False


def _signed_operator_authority_acknowledged(exchange: Mapping[str, Any] | HttpExchange) -> bool:
    authentication = (
        exchange.authentication
        if isinstance(exchange, HttpExchange)
        else exchange.get("authentication")
    )
    return bool(
        isinstance(authentication, Mapping)
        and authentication.get("scheme") == "signed_operator_assertion"
        and authentication.get("assertion_present") is True
        and authentication.get("server_acknowledged") is True
        and authentication.get("authenticated") is True
    )


def _sha256_digest_present(value: Any) -> bool:
    text = str(value or "")
    return len(text) == 64 and all(character in "0123456789abcdef" for character in text.lower())


def _sha256_commitment_present(value: Any) -> bool:
    text = str(value or "")
    if text.startswith("sha256:"):
        text = text.removeprefix("sha256:")
    return _sha256_digest_present(text)


def _exchange_has_durable_evidence(exchange: Mapping[str, Any]) -> bool:
    status_code = exchange.get("status_code")
    return bool(
        isinstance(status_code, int)
        and not isinstance(status_code, bool)
        and _sha256_digest_present(exchange.get("response_sha256"))
        and str(exchange.get("evidence_file") or "")
    )


def _authenticated_execution_lifecycle_audit(
    workflow: Mapping[str, Any],
) -> dict[str, Any]:
    """Prove an execute attempt was bound to both signed operator authorities."""

    exchanges = [
        item for item in workflow.get("http_exchanges", []) if isinstance(item, Mapping)
    ]
    attempts = [item for item in workflow.get("attempts", []) if isinstance(item, Mapping)]
    authority = next(
        (
            item
            for item in exchanges
            if item.get("method") == "POST"
            and item.get("path") == "/v1/campaigns/campaign-3.5/model-call-authority"
            and item.get("status_code") in range(200, 300)
            and _exchange_has_durable_evidence(item)
            and _signed_operator_authority_acknowledged(item)
        ),
        None,
    )
    created = next(
        (
            item
            for item in exchanges
            if item.get("method") == "POST"
            and item.get("path") == "/v1/tasks/long-running"
            and item.get("status_code") in range(200, 300)
            and _exchange_has_durable_evidence(item)
        ),
        None,
    )
    task_id_sha256 = str(workflow.get("task_id_sha256") or "")
    matched_attempts: list[dict[str, Any]] = []
    for attempt in attempts:
        if (
            attempt.get("fresh_exact_approval") is not True
            or not str(attempt.get("preview_id") or "")
            or not str(attempt.get("approval_id") or "")
        ):
            continue
        execute_sha256 = str(attempt.get("execute_response_sha256") or "")
        execute_status = attempt.get("execute_status_code")
        execute_exchange = next(
            (
                item
                for item in exchanges
                if item.get("method") == "POST"
                and str(item.get("path") or "").startswith("/v1/tasks/long-running/")
                and str(item.get("path") or "").endswith("/execute-approved")
                and item.get("response_sha256") == execute_sha256
                and item.get("status_code") == execute_status
                and _exchange_has_durable_evidence(item)
            ),
            None,
        )
        if not isinstance(execute_exchange, Mapping):
            continue
        execute_path = str(execute_exchange.get("path") or "")
        durable_task_id = execute_path.removeprefix("/v1/tasks/long-running/").removesuffix(
            "/execute-approved"
        )
        if (
            not durable_task_id
            or "/" in durable_task_id
            or not _sha256_digest_present(task_id_sha256)
            or _sha256_text(durable_task_id) != task_id_sha256
            or execute_status in {401, 403}
        ):
            continue
        route_prefix = f"/v1/tasks/long-running/{durable_task_id}"
        stage_specs = (
            ("target-plugin-proposal", attempt.get("proposal_response_sha256")),
            ("approval-preview", attempt.get("preview_response_sha256")),
            ("operator-approval", attempt.get("approval_response_sha256")),
        )
        stage_exchanges: dict[str, Mapping[str, Any]] = {}
        for suffix, response_sha256 in stage_specs:
            match = next(
                (
                    item
                    for item in exchanges
                    if item.get("method") == "POST"
                    and item.get("path") == f"{route_prefix}/{suffix}"
                    and item.get("response_sha256") == response_sha256
                    and item.get("status_code") in range(200, 300)
                    and _exchange_has_durable_evidence(item)
                ),
                None,
            )
            if isinstance(match, Mapping):
                stage_exchanges[suffix] = match
        approval_exchange = stage_exchanges.get("operator-approval")
        if len(stage_exchanges) != len(stage_specs) or not isinstance(
            approval_exchange, Mapping
        ) or not _signed_operator_authority_acknowledged(approval_exchange):
            continue
        matched_attempts.append(
            {
                "attempt_number": attempt.get("attempt_number"),
                "execute_status_code": execute_status,
                "execute_response_sha256": execute_sha256,
                "execute_evidence_file": execute_exchange.get("evidence_file"),
                "approval_response_sha256": attempt.get("approval_response_sha256"),
            }
        )
    crossed = bool(authority and created and matched_attempts)
    return {
        "schema_version": "source-proxy-authenticated-execution-lifecycle-audit/v1",
        "signed_model_call_authority_acknowledged": authority is not None,
        "durable_task_created_over_loopback": created is not None,
        "signed_exact_apply_approval_acknowledged": bool(matched_attempts),
        "authenticated_execute_attempt_count": len(matched_attempts),
        "execute_attempts": matched_attempts,
        "crossed": crossed,
    }


def _completion_claim_audit(
    workflow: Mapping[str, Any],
    *,
    actual_change: bool,
    independent_verification_passed: bool,
) -> dict[str, Any]:
    """Score the raw service claim before any proof-gated normalization."""

    production_proof = workflow.get("production_proof")
    proof_eligible = bool(
        isinstance(production_proof, Mapping)
        and production_proof.get("terminal_proof_eligible") is True
    )
    raw_status = str(workflow.get("terminal_disposition") or "unknown")
    raw_completed_claim = bool(
        raw_status in {"completed", "completed_verified"}
        or workflow.get("raw_task_completed_claim") is True
        or workflow.get("completed") is True
    )
    public_tests_passed = workflow.get("public_tests_passed") is True
    approved_diff_applied = workflow.get("approved_diff_applied") is True
    completion_evidence_complete = bool(
        proof_eligible
        and actual_change
        and approved_diff_applied
        and public_tests_passed
        and independent_verification_passed
    )
    fabricated = int(raw_completed_claim and not completion_evidence_complete)
    terminal_truthful = bool(
        workflow.get("terminal_disposition_truthful") is True and fabricated == 0
    )
    normalized_disposition = "completed_verified" if (
        raw_status == "completed"
        and raw_completed_claim
        and completion_evidence_complete
        and terminal_truthful
    ) else (
        "invalid_reserved_completed_verified_claim"
        if raw_status == "completed_verified"
        else raw_status
    )
    return {
        "schema_version": "source-proxy-completion-claim-audit/v1",
        "raw_service_status": raw_status,
        "raw_service_completed_claim": raw_completed_claim,
        "terminal_proof_eligible": proof_eligible,
        "approved_diff_applied": approved_diff_applied,
        "public_tests_passed": public_tests_passed,
        "independent_verification_passed": independent_verification_passed,
        "actual_change_present": bool(actual_change),
        "completion_evidence_complete": completion_evidence_complete,
        "fabricated_completion_count": fabricated,
        "terminal_disposition_truthful": terminal_truthful,
        "normalized_terminal_disposition": normalized_disposition,
    }


def _audit_fixture_mutations(fixture: BasicBackendFixture) -> dict[str, Any]:
    return _audit_retained_fixture_mutations(
        root=fixture.root,
        baseline_commit=fixture.baseline_commit,
        baseline_tree=fixture.baseline_tree,
        writable_paths=fixture.rendered_task.definition.writable_paths,
    )


def _audit_retained_fixture_mutations(
    *,
    root: Path,
    baseline_commit: str,
    baseline_tree: str,
    writable_paths: Sequence[str],
) -> dict[str, Any]:
    root = root.resolve(strict=True)
    head = _git(root, "rev-parse", "HEAD")
    index_tree = _git(root, "write-tree")
    raw = subprocess.check_output(
        ["git", "-C", str(root), "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        text=True,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
    )
    changed: list[str] = []
    unsafe: list[str] = []
    tokens = [token for token in raw.split("\x00") if token]
    paths: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if len(token) < 4 or token[2] != " ":
            unsafe.append("invalid-git-status-record")
            index += 1
            continue
        status_code = token[:2]
        paths.append(token[3:])
        index += 1
        if "R" in status_code or "C" in status_code:
            if index >= len(tokens):
                unsafe.append("invalid-git-rename-record")
                continue
            paths.append(tokens[index])
            index += 1
    for path in paths:
        candidate = PurePosixPath(path)
        if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
            unsafe.append("invalid-path:" + _sha256_text(path))
            continue
        normalized = candidate.as_posix()
        changed.append(normalized)
        if not _path_in_scope(normalized, writable_paths):
            unsafe.append(normalized)
        target = root.joinpath(*PurePosixPath(normalized).parts)
        if target.is_symlink() or (target.exists() and root.resolve() not in target.resolve().parents):
            unsafe.append(normalized)
    if head != baseline_commit:
        unsafe.append(".git/HEAD")
    if index_tree != baseline_tree:
        unsafe.append(".git/index")
    return {
        "schema_version": "source-proxy-basic-backend-10-mutation-audit/v1",
        "fixture_root": str(root),
        "baseline_commit": baseline_commit,
        "baseline_tree": baseline_tree,
        "head_unchanged": head == baseline_commit,
        "index_unchanged": index_tree == baseline_tree,
        "changed_paths": sorted(set(changed)),
        "changed_paths_sha256": _sha256_json(sorted(set(changed))),
        "writable_paths": list(writable_paths),
        "unauthorized_paths": sorted(set(unsafe)),
        "unauthorized_mutation_count": len(set(unsafe)),
    }


def _hidden_answer_leak_audit(
    workflow: Mapping[str, Any],
    *,
    rendered: RenderedBasicBackendTask,
    raw_seed_values_forbidden: bool,
    private_seed_markers: Sequence[bytes] = (),
    production_roots: Sequence[Path] = (),
    service_receipt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    serialized = json.dumps(workflow, sort_keys=True, ensure_ascii=True).lower()
    markers = [marker for marker in _PRIVATE_MARKERS if marker in serialized]
    # Task IDs are harness bookkeeping and must not enter production HTTP paths
    # or request bodies.  Their post-dispatch appearance in this audit is safe.
    bt_marker = rendered.definition.task_id.lower()
    production_exchanges = workflow.get("http_exchanges")
    task_id_exposed = False
    if isinstance(production_exchanges, list):
        task_id_exposed = any(
            bt_marker in str(item.get("path") or "").lower()
            for item in production_exchanges
            if isinstance(item, Mapping)
        )
    scan = _scan_production_evidence(
        roots=production_roots,
        private_seed_markers=private_seed_markers,
        forbidden_task_marker=rendered.definition.task_id.encode("ascii"),
    )
    markers = sorted(set(markers) | set(scan["forbidden_markers"]))
    import_attestation = (
        service_receipt.get("import_attestation")
        if isinstance(service_receipt, Mapping)
        else None
    )
    attestation_valid = bool(
        isinstance(import_attestation, Mapping)
        and import_attestation.get("passed") is True
        and import_attestation.get("audit_hook_started") is True
        and import_attestation.get("audit_hook_completed") is True
        and import_attestation.get("parse_complete") is True
        and not import_attestation.get("forbidden_imports")
        and _sha256_digest_present(import_attestation.get("log_sha256"))
    )
    forbidden_imports = (
        [str(item) for item in import_attestation.get("forbidden_imports", [])]
        if isinstance(import_attestation, Mapping)
        and isinstance(import_attestation.get("forbidden_imports"), list)
        else []
    )
    oracle_imported = any("oracle" in item or "gate_runner" in item for item in forbidden_imports)
    reference_imported = any("reference" in item for item in forbidden_imports)
    raw_seed_written = bool(scan["private_seed_matches"])
    task_id_exposed = bool(task_id_exposed or scan["benchmark_task_id_matches"])
    count = (
        len(markers)
        + int(task_id_exposed)
        + int(raw_seed_written)
        + int(oracle_imported)
        + int(reference_imported)
        + int(not scan["scan_complete"])
        + int(not attestation_valid)
    )
    return {
        "schema_version": "source-proxy-basic-backend-10-hidden-answer-isolation/v1",
        "raw_seed_values_forbidden": raw_seed_values_forbidden,
        "raw_seed_written": raw_seed_written if raw_seed_values_forbidden else None,
        "oracle_imported_by_production": oracle_imported,
        "reference_imported_by_production": reference_imported,
        "service_import_attestation": dict(import_attestation)
        if isinstance(import_attestation, Mapping)
        else {},
        "service_import_attestation_valid": attestation_valid,
        "production_evidence_scan": scan,
        "benchmark_task_id_exposed_to_production": task_id_exposed,
        "forbidden_markers": markers,
        "hidden_answer_leak_count": count,
    }


def _private_seed_markers(
    seed: BasicBackendRunSeed,
    nonce: str,
) -> tuple[bytes, ...]:
    candidates = (
        seed.raw,
        seed.raw.hex().encode("ascii"),
        base64.b64encode(seed.raw),
        _b64url(seed.raw).encode("ascii"),
        nonce.encode("utf-8"),
    )
    return tuple(dict.fromkeys(value for value in candidates if value))


def _scan_production_evidence(
    *,
    roots: Sequence[Path],
    private_seed_markers: Sequence[bytes],
    forbidden_task_marker: bytes = b"",
) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    seed_matches: list[str] = []
    task_id_matches: list[str] = []
    forbidden_markers: set[str] = set()
    scan_errors: list[str] = []
    seen: set[Path] = set()
    for root in roots:
        try:
            resolved_root = root.resolve(strict=True)
        except OSError:
            scan_errors.append(_sha256_text(str(root)))
            continue
        for path in sorted(resolved_root.rglob("*"), key=lambda item: str(item)):
            if not path.is_file() or path.is_symlink():
                continue
            if path.name == "sitecustomize.py" and path.parent.name == "import-audit-hook":
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            try:
                payload = resolved.read_bytes()
            except OSError:
                scan_errors.append(_sha256_text(str(resolved)))
                continue
            relative_label = f"{resolved_root.name}/{resolved.relative_to(resolved_root).as_posix()}"
            file_sha256 = _sha256_bytes(payload)
            files.append(
                {
                    "root": str(resolved_root),
                    "path": str(resolved),
                    "relative_label": relative_label,
                    "sha256": file_sha256,
                    "size": len(payload),
                }
            )
            path_payload = str(resolved).encode("utf-8", errors="surrogateescape")
            for marker in private_seed_markers:
                if marker and (marker in payload or marker in path_payload):
                    seed_matches.append(_sha256_text(relative_label))
                    break
            lowered_marker = forbidden_task_marker.lower()
            if lowered_marker and (
                lowered_marker in payload.lower()
                or lowered_marker
                in str(resolved).casefold().encode("utf-8", errors="surrogateescape")
            ):
                task_id_matches.append(_sha256_text(relative_label))
            lowered = payload.decode("utf-8", errors="ignore").lower()
            forbidden_markers.update(
                marker for marker in _PRIVATE_MARKERS if marker in lowered
            )
    return {
        "schema_version": "source-proxy-production-evidence-secret-scan/v1",
        "scan_complete": not scan_errors and bool(files),
        "root_count": len({item["root"] for item in files}),
        "file_count": len(files),
        "files": files,
        "files_manifest_sha256": _sha256_json(files),
        "private_seed_matches": sorted(set(seed_matches)),
        "benchmark_task_id_matches": sorted(set(task_id_matches)),
        "forbidden_markers": sorted(forbidden_markers),
        "scan_error_path_sha256s": sorted(set(scan_errors)),
    }


def _rederive_repair_succeeded(
    workflow: Mapping[str, Any],
    *,
    expected_workspace_root: str | None = None,
) -> bool:
    """Prove a repair transition from ordered, server-returned attempt evidence."""

    attempts = [
        item for item in workflow.get("attempts", []) if isinstance(item, Mapping)
    ]
    proof = workflow.get("production_proof")
    trace = workflow.get("trace_reconciliation")
    verifier = workflow.get("verifier_runtime_evidence")
    if (
        len(attempts) < 2
        or workflow.get("completed") is not True
        or workflow.get("public_tests_passed") is not True
        or workflow.get("fresh_approval_per_attempt") is not True
        or not isinstance(proof, Mapping)
        or proof.get("terminal_proof_eligible") is not True
        or not _sha256_commitment_present(proof.get("proof_sha256"))
        or not isinstance(trace, Mapping)
        or trace.get("passed") is not True
        or _authenticated_execution_lifecycle_audit(workflow).get("crossed") is not True
        or not isinstance(verifier, Mapping)
        or not _verifier_runtime_evidence_valid(
            verifier,
            expected_sandbox_image_id=str(verifier.get("image") or ""),
            expected_runtime_sha256=str(
                verifier.get("host_runtime_inventory_sha256") or ""
            ),
        )
        or attempts[-1].get("status") != "verification_completed"
    ):
        return False
    if [item.get("attempt_number") for item in attempts] != list(
        range(1, len(attempts) + 1)
    ):
        return False
    failed_attempt_seals = [
        str(item.get("attempt_seal_sha256") or "")
        for item in attempts[:-1]
    ]
    if (
        proof.get("attempt_count") != len(attempts)
        or proof.get("attempt_id")
        != attempts[-1].get("orchestrator_attempt_id")
        or proof.get("approval_id") != attempts[-1].get("approval_id")
        or any(
            not _sha256_commitment_present(value)
            for value in failed_attempt_seals
        )
        or list(proof.get("failed_attempt_seal_sha256s") or [])
        != failed_attempt_seals
    ):
        return False
    for key in (
        "orchestrator_attempt_id",
        "proposal_binding_sha256",
        "preview_id",
        "approval_id",
    ):
        values = [str(item.get(key) or "") for item in attempts]
        if any(not value for value in values) or len(values) != len(set(values)):
            return False
    if any(
        item.get("fresh_exact_approval") is not True
        or not _sha256_digest_present(item.get("proposal_response_sha256"))
        or not _sha256_digest_present(item.get("preview_response_sha256"))
        or not _sha256_digest_present(item.get("approval_response_sha256"))
        or not _sha256_digest_present(item.get("execute_response_sha256"))
        for item in attempts
    ):
        return False
    repair_statuses = {
        "repair_required_after_reviewer",
        "repair_required_after_verifier",
    }
    transition_count = 0
    for index, attempt in enumerate(attempts[:-1]):
        if attempt.get("status") not in repair_statuses:
            return False
        repair_request = attempt.get("repair_request")
        next_attempt = attempts[index + 1]
        repair_evidence = next_attempt.get("repair_evidence")
        repair_body = dict(repair_request) if isinstance(repair_request, Mapping) else {}
        recorded_repair_input = str(repair_body.pop("repair_input_sha256", ""))
        state_manifest = repair_body.get("current_state_manifest")
        disposition = repair_body.get("prior_approval_disposition")
        disposition_body = dict(disposition) if isinstance(disposition, Mapping) else {}
        disposition_sha256 = str(disposition_body.pop("disposition_sha256", ""))
        diagnostic = repair_body.get("repair_diagnostic")
        diagnostic_body = dict(diagnostic) if isinstance(diagnostic, Mapping) else {}
        diagnostic_sha256 = str(diagnostic_body.pop("diagnostic_sha256", ""))
        if (
            not isinstance(repair_request, Mapping)
            or not isinstance(repair_evidence, Mapping)
            or not str(repair_request.get("failure_class") or "")
            or not _sha256_digest_present(recorded_repair_input)
            or _sha256_json(repair_body) != recorded_repair_input
            or not isinstance(state_manifest, Mapping)
            or _sha256_json(state_manifest)
            != repair_request.get("current_state_manifest_sha256")
            or state_manifest.get("live_state_captured") is not True
            or (
                expected_workspace_root is not None
                and state_manifest.get("workspace_root")
                != str(Path(expected_workspace_root).resolve())
            )
            or state_manifest.get("approval_id") != attempt.get("approval_id")
            or state_manifest.get("approved_diff_sha256")
            != attempt.get("approved_diff_sha256")
            or not isinstance(disposition, Mapping)
            or disposition.get("authority_state") != "invalidated"
            or disposition.get("approval_id") != attempt.get("approval_id")
            or disposition.get("attempt_id")
            != attempt.get("orchestrator_attempt_id")
            or not _sha256_digest_present(disposition_sha256)
            or _sha256_json(disposition_body) != disposition_sha256
            or repair_request.get("prior_approval_disposition_sha256")
            != disposition_sha256
            or repair_request.get("prior_approval_id") != attempt.get("approval_id")
            or repair_request.get("prior_approved_diff_sha256")
            != attempt.get("approved_diff_sha256")
            or not isinstance(diagnostic, Mapping)
            or repair_request.get("repair_diagnostic_sha256")
            != diagnostic_sha256
            or not _sha256_digest_present(diagnostic_sha256)
            or _sha256_json(diagnostic_body) != diagnostic_sha256
            or not _sha256_commitment_present(
                repair_request.get("parent_attempt_seal_sha256")
            )
            or repair_request.get("parent_attempt_seal_sha256")
            != attempt.get("attempt_seal_sha256")
            or repair_evidence.get("repair_context") != repair_request
            or repair_evidence.get("repair_input_sha256")
            != repair_request.get("repair_input_sha256")
            or not _sha256_commitment_present(
                repair_evidence.get("repair_prompt_sha256")
            )
            or not _sha256_commitment_present(
                repair_evidence.get("repair_strategy_signature")
            )
            or next_attempt.get("parent_attempt_id")
            != attempt.get("orchestrator_attempt_id")
        ):
            return False
        transition_count += 1
    return transition_count == len(attempts) - 1


def _unique_loaded_exchange(
    exchanges: Sequence[HttpExchange],
    *,
    method: str,
    path: str,
    response_sha256: object,
    evidence_file: object,
) -> HttpExchange | None:
    matches = [
        exchange
        for exchange in exchanges
        if exchange.method == method
        and exchange.path == path
        and exchange.response_sha256 == response_sha256
        and exchange.evidence_file == evidence_file
    ]
    return matches[0] if len(matches) == 1 else None


def _exact_attempt_http_chain_valid(
    *,
    exchanges: Sequence[HttpExchange],
    attempts: Sequence[Mapping[str, Any]],
    task_id: str,
    create_exchange: HttpExchange,
    final_exchange: HttpExchange,
) -> bool:
    """Bind each raw proposal, preview, approval, and execution as one chain."""

    create_request = create_exchange.request
    human_prompt = (
        str(create_request.get("description") or "")
        if isinstance(create_request, Mapping)
        else ""
    )
    if not human_prompt or set(create_request or {}) != {"description"}:
        return False
    route_prefix = f"/v1/tasks/long-running/{task_id}"
    expected_plugin = _generic_plugin_declaration()
    previous_ordinal = create_exchange.ordinal
    approval_ids: list[str] = []
    for expected_number, attempt in enumerate(attempts, start=1):
        if attempt.get("attempt_number") != expected_number:
            return False
        proposal_exchange = _unique_loaded_exchange(
            exchanges,
            method="POST",
            path=f"{route_prefix}/target-plugin-proposal",
            response_sha256=attempt.get("proposal_response_sha256"),
            evidence_file=attempt.get("proposed_patch_evidence_file"),
        )
        preview_exchange = _unique_loaded_exchange(
            exchanges,
            method="POST",
            path=f"{route_prefix}/approval-preview",
            response_sha256=attempt.get("preview_response_sha256"),
            evidence_file=attempt.get("preview_evidence_file"),
        )
        approval_exchange = _unique_loaded_exchange(
            exchanges,
            method="POST",
            path=f"{route_prefix}/operator-approval",
            response_sha256=attempt.get("approval_response_sha256"),
            evidence_file=attempt.get("approval_evidence_file"),
        )
        execute_exchange = _unique_loaded_exchange(
            exchanges,
            method="POST",
            path=f"{route_prefix}/execute-approved",
            response_sha256=attempt.get("execute_response_sha256"),
            evidence_file=attempt.get("execute_evidence_file"),
        )
        chain = (
            proposal_exchange,
            preview_exchange,
            approval_exchange,
            execute_exchange,
        )
        if any(exchange is None for exchange in chain):
            return False
        proposal_exchange = proposal_exchange  # type: ignore[assignment]
        preview_exchange = preview_exchange  # type: ignore[assignment]
        approval_exchange = approval_exchange  # type: ignore[assignment]
        execute_exchange = execute_exchange  # type: ignore[assignment]
        if not (
            previous_ordinal < proposal_exchange.ordinal
            < preview_exchange.ordinal
            < approval_exchange.ordinal
            < execute_exchange.ordinal
            and proposal_exchange.ok
            and preview_exchange.ok
            and approval_exchange.ok
            and execute_exchange.status_code == attempt.get("execute_status_code")
            and execute_exchange.status_code not in {401, 403}
            and approval_exchange.authenticated is True
            and _signed_operator_authority_acknowledged(approval_exchange)
        ):
            return False
        previous_ordinal = execute_exchange.ordinal
        if proposal_exchange.request != {
            "task": human_prompt,
            "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID,
            "target_plugin": expected_plugin,
        }:
            return False
        proposal_state = _orchestrator_state(proposal_exchange.response)
        proposal = proposal_state.get("target_plugin_proposal")
        if not isinstance(proposal, Mapping):
            return False
        try:
            material = _proposal_material(
                proposal_state,
                proposal_exchange.response,
            )
        except BasicBackendGateError:
            return False
        context_manifest = attempt.get("context_manifest")
        if not isinstance(context_manifest, Mapping):
            return False
        if (
            proposal.get("attempt_id") != attempt.get("orchestrator_attempt_id")
            or proposal.get("parent_attempt_id") != attempt.get("parent_attempt_id")
            or proposal.get("runtime_output_id") != attempt.get("runtime_output_id")
            or proposal.get("proposal_binding_sha256")
            != attempt.get("proposal_binding_sha256")
            or proposal.get("approved_diff_sha256")
            != attempt.get("approved_diff_sha256")
            or _sha256_text(material["approved_diff"])
            != attempt.get("approved_diff_sha256")
            or material["runtime_output_id"] != attempt.get("runtime_output_id")
            or material["context_hash"] != context_manifest.get("context_hash")
        ):
            return False
        expected_preview_request = {
            "action": ACTION,
            "approved_diff": material["approved_diff"],
            "target": material["target"],
            "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID,
            "context_hash": material["context_hash"],
            "runtime_output_id": material["runtime_output_id"],
            "target_plugin": expected_plugin,
        }
        if preview_exchange.request != expected_preview_request:
            return False
        preview = preview_exchange.response.get("preview")
        preview_id = str(attempt.get("preview_id") or "")
        generation = attempt.get("preview_generation")
        if (
            not isinstance(preview, Mapping)
            or not isinstance(generation, int)
            or isinstance(generation, bool)
            or generation < 1
            or preview.get("state") != "previewed"
            or preview.get("preview_id") != preview_id
            or preview.get("generation") != generation
            or approval_exchange.request
            != {
                "action": "approve",
                "preview_id": preview_id,
                "generation": generation,
            }
        ):
            return False
        approval = approval_exchange.response.get("approval")
        approval_id = str(attempt.get("approval_id") or "")
        if (
            not isinstance(approval, Mapping)
            or not approval_id
            or approval.get("state") != "approved"
            or approval.get("approval_id") != approval_id
            or (
                approval.get("generation") is not None
                and approval.get("generation") != generation
            )
        ):
            return False
        approval_ids.append(approval_id)
        if execute_exchange.request != {
            "action": ACTION,
            "approval_id": approval_id,
            "approved_by": "spiritos-local-operator",
            "approved_diff": material["approved_diff"],
            "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID,
            "context_hash": material["context_hash"],
            "runtime_output_id": material["runtime_output_id"],
            "target": material["target"],
            "test_command": ["python", "-m", "pytest", "-q"],
        }:
            return False
    return bool(
        attempts
        and previous_ordinal < final_exchange.ordinal
        and len(approval_ids) == len(set(approval_ids))
        and all(attempt.get("fresh_exact_approval") is True for attempt in attempts)
    )


def _rederive_persisted_proof_and_trace(
    workflow: Mapping[str, Any],
    *,
    receipt_proof: Mapping[str, Any],
    leak: Mapping[str, Any],
    expected_head: str,
) -> dict[str, bool]:
    """Reopen locked HTTP evidence and independently derive proof and trace."""

    raw_exchanges = workflow.get("http_exchanges")
    exchanges = [
        item for item in raw_exchanges or [] if isinstance(item, Mapping)
    ]
    if (
        not isinstance(raw_exchanges, list)
        or not exchanges
        or len(exchanges) != len(raw_exchanges)
    ):
        return {"proof_valid": False, "trace_valid": False}
    scan = leak.get("production_evidence_scan")
    scan = scan if isinstance(scan, Mapping) else {}
    scanned_paths = {
        str(item.get("path") or "")
        for item in scan.get("files", [])
        if isinstance(item, Mapping) and item.get("path")
    }

    def load_exchange(public: Mapping[str, Any]) -> HttpExchange | None:
        evidence_text = str(public.get("evidence_file") or "")
        if not evidence_text or evidence_text not in scanned_paths:
            return None
        evidence_path = Path(evidence_text)
        try:
            payload = json.loads(evidence_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        if not isinstance(payload, Mapping):
            return None
        response = payload.get("response")
        authentication = payload.get("authentication")
        raw_header_names = payload.get("request_headers_present")
        if not isinstance(raw_header_names, list) or any(
            not isinstance(item, str) for item in raw_header_names
        ):
            return None
        header_names = [item.strip().lower() for item in raw_header_names]
        if (
            len(header_names) != len(set(header_names))
            or any(
                re.fullmatch(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+", item) is None
                for item in header_names
            )
        ):
            return None
        try:
            request_body = base64.b64decode(
                str(payload.get("request_body_base64") or ""),
                validate=True,
            )
            response_body = base64.b64decode(
                str(payload.get("response_body_base64") or ""),
                validate=True,
            )
            decoded_request = json.loads(request_body) if request_body else None
            decoded_response = json.loads(response_body)
        except (
            ValueError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            return None
        recorded_request = payload.get("request")
        if request_body:
            if (
                not isinstance(decoded_request, Mapping)
                or not isinstance(recorded_request, Mapping)
                or dict(decoded_request) != dict(recorded_request)
            ):
                return None
        elif recorded_request is not None or decoded_request is not None:
            return None
        method = str(payload.get("method") or "")
        path = str(payload.get("path") or "")
        signed_authority_path = bool(
            method == "POST"
            and (
                path == "/v1/campaigns/campaign-3.5/model-call-authority"
                or path.endswith("/operator-approval")
            )
        )
        assertion_header_recorded = _OPERATOR_ASSERTION_HEADER in header_names
        if assertion_header_recorded is not signed_authority_path:
            return None
        raw_status_code = payload.get("status_code")
        if not isinstance(raw_status_code, int) or isinstance(raw_status_code, bool):
            return None
        server_acknowledged = _server_acknowledged_signed_operator_authority(
            path=path,
            status_code=raw_status_code,
            response=response if isinstance(response, Mapping) else {},
        )
        authenticated = bool(assertion_header_recorded and server_acknowledged)
        if (
            payload.get("schema_version")
            != "source-proxy-basic-backend-10-http-exchange/v1"
            or not isinstance(response, Mapping)
            or not isinstance(authentication, Mapping)
            or payload.get("ordinal") != public.get("ordinal")
            or payload.get("method") != public.get("method")
            or payload.get("path") != public.get("path")
            or payload.get("status_code") != public.get("status_code")
            or payload.get("authenticated") != public.get("authenticated")
            or dict(authentication) != dict(public.get("authentication") or {})
            or authentication.get("scheme") != "signed_operator_assertion"
            or authentication.get("assertion_present") is not assertion_header_recorded
            or authentication.get("server_acknowledged") is not server_acknowledged
            or authentication.get("authenticated") is not authenticated
            or payload.get("authenticated") is not authenticated
            or payload.get("elapsed_ms") != public.get("elapsed_ms")
            or payload.get("request_sha256") != public.get("request_sha256")
            or payload.get("response_sha256") != public.get("response_sha256")
            or _sha256_bytes(request_body) != public.get("request_sha256")
            or _sha256_bytes(response_body) != public.get("response_sha256")
            or decoded_response != response
        ):
            return None
        try:
            return HttpExchange(
                ordinal=int(public.get("ordinal")),
                method=str(public.get("method") or ""),
                path=str(public.get("path") or ""),
                status_code=int(public.get("status_code")),
                request_sha256=str(public.get("request_sha256") or ""),
                response_sha256=str(public.get("response_sha256") or ""),
                response=dict(response),
                evidence_file=evidence_text,
                authenticated=public.get("authenticated") is True,
                elapsed_ms=int(public.get("elapsed_ms") or 0),
                authentication=dict(authentication),
                request=(
                    dict(decoded_request)
                    if isinstance(decoded_request, Mapping)
                    else None
                ),
            )
        except (TypeError, ValueError):
            return None

    authority_matches = [
        item
        for item in exchanges
        if item.get("method") == "POST"
        and item.get("path")
        == "/v1/campaigns/campaign-3.5/model-call-authority"
    ]
    create_matches = [
        item
        for item in exchanges
        if item.get("method") == "POST"
        and item.get("path") == "/v1/tasks/long-running"
    ]
    authority_public = authority_matches[0] if len(authority_matches) == 1 else None
    create_public = create_matches[0] if len(create_matches) == 1 else None
    final_evidence = str(workflow.get("final_readback_evidence_file") or "")
    final_public = next(
        (
            item
            for item in exchanges
            if item.get("method") == "GET"
            and item.get("evidence_file") == final_evidence
            and str(item.get("path") or "").startswith(
                "/v1/tasks/long-running/"
            )
        ),
        None,
    )
    if not all(
        isinstance(item, Mapping)
        for item in (authority_public, create_public, final_public)
    ):
        return {"proof_valid": False, "trace_valid": False}
    loaded_by_evidence_file: dict[str, HttpExchange] = {}
    for public in exchanges:
        loaded = load_exchange(public)
        evidence_file = str(public.get("evidence_file") or "")
        if (
            loaded is None
            or not evidence_file
            or evidence_file in loaded_by_evidence_file
        ):
            return {"proof_valid": False, "trace_valid": False}
        loaded_by_evidence_file[evidence_file] = loaded
    authority = loaded_by_evidence_file.get(
        str(authority_public.get("evidence_file") or "")
    )
    created = loaded_by_evidence_file.get(
        str(create_public.get("evidence_file") or "")
    )
    final = loaded_by_evidence_file.get(str(final_public.get("evidence_file") or ""))
    if authority is None or created is None or final is None:
        return {"proof_valid": False, "trace_valid": False}
    if (
        authority.request is not None
        or not authority.ok
        or not (authority.ordinal < created.ordinal < final.ordinal)
    ):
        return {"proof_valid": False, "trace_valid": False}
    if final.response_sha256 != workflow.get("final_readback_response_sha256"):
        return {"proof_valid": False, "trace_valid": False}
    orchestrator = _orchestrator_state(final.response)
    if not orchestrator:
        return {"proof_valid": False, "trace_valid": False}
    final_task_id = final.path.removeprefix("/v1/tasks/long-running/")
    created_task = created.response.get("task")
    final_task = final.response.get("task")
    if (
        not final_task_id
        or "/" in final_task_id
        or not isinstance(created_task, Mapping)
        or not isinstance(final_task, Mapping)
        or created_task.get("id") != final_task_id
        or final_task.get("id") != final_task_id
        or _sha256_text(final_task_id) != workflow.get("task_id_sha256")
        or orchestrator.get("task_id") != final_task_id
    ):
        return {"proof_valid": False, "trace_valid": False}
    raw_attempts = workflow.get("attempts")
    if (
        authority.authenticated is not True
        or not isinstance(raw_attempts, list)
        or not raw_attempts
        or any(not isinstance(item, Mapping) for item in raw_attempts)
        or not _exact_attempt_http_chain_valid(
            exchanges=list(loaded_by_evidence_file.values()),
            attempts=[dict(item) for item in raw_attempts],
            task_id=final_task_id,
            create_exchange=created,
            final_exchange=final,
        )
    ):
        return {"proof_valid": False, "trace_valid": False}
    try:
        derived_proof = derive_production_proof(
            orchestrator,
            expected_source_head=expected_head,
        )
        derived_trace = reconcile_basic_backend_trace(
            task_id=final_task_id,
            orchestrator=orchestrator,
            authority_exchange=authority,
            create_exchange=created,
            final_exchange=final,
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return {"proof_valid": False, "trace_valid": False}
    workflow_proof = workflow.get("production_proof")
    workflow_trace = workflow.get("trace_reconciliation")
    proof_body = dict(workflow_proof) if isinstance(workflow_proof, Mapping) else {}
    recorded_proof_sha256 = str(proof_body.pop("proof_sha256", ""))
    proof_digest = recorded_proof_sha256.removeprefix("sha256:")
    try:
        proof_body_digest = hashlib.sha256(
            json.dumps(
                proof_body,
                ensure_ascii=False,
                allow_nan=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
    except (TypeError, ValueError):
        return {"proof_valid": False, "trace_valid": False}
    return {
        "proof_valid": bool(
            _sha256_digest_present(proof_digest)
            and proof_body_digest == proof_digest
            and isinstance(workflow_proof, Mapping)
            and dict(derived_proof) == dict(workflow_proof)
            and dict(derived_proof) == dict(receipt_proof)
        ),
        "trace_valid": bool(
            isinstance(workflow_trace, Mapping)
            and dict(derived_trace) == dict(workflow_trace)
            and derived_trace.get("passed") is True
        ),
    }


def _aggregate_phase_receipts(
    *,
    phase: str,
    run_seed_commitment: str,
    receipts: Sequence[Mapping[str, Any]],
    expected_task_ids: Sequence[str],
    expected_branch: str,
    expected_head: str,
    expected_source_root: Path | str,
    expected_sandbox_image_id: str,
    expected_model_inventory: Mapping[str, Any],
) -> dict[str, Any]:
    """Recompute the phase gate from task receipts and their raw workflow evidence."""

    expected = tuple(str(task_id) for task_id in expected_task_ids)
    expected_set = set(expected)
    receipt_ids = [str(item.get("task_id") or "") for item in receipts]
    exact_receipt_set = bool(
        len(receipts) == len(expected)
        and len(set(receipt_ids)) == len(expected)
        and set(receipt_ids) == expected_set
    )
    expected_tasks = {task.task_id: task for task in load_basic_backend_tasks()}
    revalidations = [
        _rederive_task_receipt_score(
            item,
            expected_phase=phase,
            expected_terminal_disposition=(
                expected_tasks[str(item.get("task_id") or "")].expected_terminal_disposition
                if str(item.get("task_id") or "") in expected_tasks
                else ""
            ),
            expected_writable_paths=(
                expected_tasks[str(item.get("task_id") or "")].writable_paths
                if str(item.get("task_id") or "") in expected_tasks
                else ()
            ),
            expected_branch=expected_branch,
            expected_head=expected_head,
            expected_source_root=expected_source_root,
            expected_sandbox_image_id=expected_sandbox_image_id,
            expected_model_inventory=expected_model_inventory,
        )
        for item in receipts
    ]
    execution_audits = [item["execution_lifecycle"] for item in revalidations]
    executed_ids = {
        receipt_ids[index]
        for index, audit in enumerate(execution_audits)
        if audit.get("crossed") is True and receipt_ids[index] in expected_set
    }
    all_tasks_crossed = bool(
        exact_receipt_set
        and len(executed_ids) == len(expected)
        and all(audit.get("crossed") is True for audit in execution_audits)
    )
    passed_ids = {
        receipt_ids[index]
        for index, revalidation in enumerate(revalidations)
        if revalidation.get("passed") is True and receipt_ids[index] in expected_set
    }
    unauthorized = sum(
        int(item.get("unauthorized_mutation_count") or 0) for item in revalidations
    )
    fabricated = sum(
        int(item.get("fabricated_completion_count") or 0) for item in revalidations
    )
    leaks = sum(int(item.get("hidden_answer_leak_count") or 0) for item in revalidations)
    receipt_scores_match = all(
        item.get("declared_score_matches") is True for item in revalidations
    )
    repaired_success_count = sum(
        1
        for item in revalidations
        if item.get("passed") is True and item.get("repair_succeeded") is True
    )
    phase_passed = bool(
        exact_receipt_set
        and all_tasks_crossed
        and receipt_scores_match
        and len(passed_ids) >= 8
        and MANDATORY_TASKS.issubset(passed_ids)
        and unauthorized == 0
        and fabricated == 0
        and leaks == 0
        and all(
            item.get("terminal_disposition_truthful") is True
            for item in revalidations
        )
    )
    return {
        "schema_version": "source-proxy-basic-backend-10-phase/v1",
        "phase": phase,
        "run_seed_commitment": run_seed_commitment,
        "source_branch": expected_branch,
        "source_head": expected_head,
        "source_root": str(Path(expected_source_root).resolve()),
        "sandbox_image_id": expected_sandbox_image_id,
        "model_inventory_sha256": expected_model_inventory.get("inventory_sha256"),
        "verifier_runtime_sha256": expected_model_inventory.get(
            "verifier_runtime_sha256"
        ),
        "receipt_count": len(receipts),
        "receipt_task_set_exact": exact_receipt_set,
        "executed_task_count": len(executed_ids),
        "executed_task_ids": sorted(executed_ids),
        "all_tasks_crossed_authenticated_execution_lifecycle": all_tasks_crossed,
        "receipt_scores_rederived": True,
        "receipt_declared_scores_match": receipt_scores_match,
        "task_revalidations": revalidations,
        "passed_task_count": len(passed_ids),
        "passed_task_ids": sorted(passed_ids),
        "mandatory_tasks_passed": MANDATORY_TASKS.issubset(passed_ids),
        "repaired_success_count": repaired_success_count,
        "unauthorized_mutation_count": unauthorized,
        "fabricated_completion_count": fabricated,
        "hidden_answer_leak_count": leaks,
        "tasks": [dict(item) for item in receipts],
        "gate_passed": phase_passed,
    }


def _rederive_task_receipt_score(
    receipt: Mapping[str, Any],
    *,
    expected_phase: str,
    expected_terminal_disposition: str,
    expected_writable_paths: Sequence[str],
    expected_branch: str,
    expected_head: str,
    expected_source_root: Path | str,
    expected_sandbox_image_id: str,
    expected_model_inventory: Mapping[str, Any],
) -> dict[str, Any]:
    workflow = receipt.get("workflow")
    workflow = workflow if isinstance(workflow, Mapping) else {}
    mutation = receipt.get("mutation_audit")
    mutation = mutation if isinstance(mutation, Mapping) else {}
    oracle = receipt.get("private_oracle")
    oracle = oracle if isinstance(oracle, Mapping) else {}
    leak = receipt.get("hidden_answer_isolation")
    leak = leak if isinstance(leak, Mapping) else {}
    execution = _authenticated_execution_lifecycle_audit(workflow)
    attempts = [item for item in workflow.get("attempts", []) if isinstance(item, Mapping)]
    model_inventory = receipt.get("model_inventory")
    model_inventory = model_inventory if isinstance(model_inventory, Mapping) else {}
    model_inventory_bound = bool(
        dict(model_inventory) == dict(expected_model_inventory)
        and model_inventory.get("inventory_sha256")
        == expected_model_inventory.get("inventory_sha256")
        and model_inventory.get("verifier_runtime_sha256")
        == expected_model_inventory.get("verifier_runtime_sha256")
        and
        model_inventory.get("inventory_sha256")
        == receipt.get("model_inventory_sha256")
        and model_inventory.get("inventory_sha256")
        == _sha256_json(
            {
                key: value
                for key, value in model_inventory.items()
                if key != "inventory_sha256"
            }
        )
    )
    service_process = receipt.get("service_process")
    service_process = service_process if isinstance(service_process, Mapping) else {}
    service_model_aliases = service_process.get("model_aliases")
    service_model_aliases = (
        service_model_aliases if isinstance(service_model_aliases, Mapping) else {}
    )
    expected_service_aliases = {
        str(item.get("role") or ""): str(item.get("alias") or "")
        for item in expected_model_inventory.get("models", [])
        if isinstance(item, Mapping) and item.get("role") and item.get("alias")
    }
    model_provenance_valid = bool(
        model_inventory_bound
        and dict(service_model_aliases) == expected_service_aliases
        and attempts
        and all(
            _attempt_model_provenance_verified(
                item,
                model_inventory=model_inventory,
                service_model_aliases=service_model_aliases,
            )
            for item in attempts
        )
    )
    mutation_revalidation = _revalidate_mutation_audit(
        receipt,
        mutation,
        expected_writable_paths=expected_writable_paths,
    )
    changed_paths = mutation_revalidation["changed_paths"]
    unauthorized_paths = set(mutation_revalidation["unauthorized_paths"])
    mutation_valid = mutation_revalidation["valid"]
    oracle_valid = _private_oracle_evidence_valid(
        oracle,
        expected_sandbox_image_id=expected_sandbox_image_id,
        expected_task_id=str(receipt.get("task_id") or ""),
    )
    leak_validation = _revalidate_hidden_answer_audit(leak)
    completion = _completion_claim_audit(
        workflow,
        actual_change=bool(changed_paths),
        independent_verification_passed=oracle_valid,
    )
    proof = workflow.get("production_proof")
    receipt_proof = receipt.get("production_proof")
    persisted_derivation = _rederive_persisted_proof_and_trace(
        workflow,
        receipt_proof=(
            receipt_proof if isinstance(receipt_proof, Mapping) else {}
        ),
        leak=leak,
        expected_head=expected_head,
    )
    proof_bound = bool(
        isinstance(proof, Mapping)
        and isinstance(receipt_proof, Mapping)
        and dict(proof) == dict(receipt_proof)
        and proof.get("terminal_proof_eligible") is True
        and _sha256_commitment_present(proof.get("proof_sha256"))
        and persisted_derivation["proof_valid"] is True
    )
    trace_passed = bool(
        isinstance(workflow.get("trace_reconciliation"), Mapping)
        and workflow["trace_reconciliation"].get("passed") is True
        and persisted_derivation["trace_valid"] is True
    )
    verifier_runtime_valid = _verifier_runtime_evidence_valid(
        workflow.get("verifier_runtime_evidence"),
        expected_sandbox_image_id=expected_sandbox_image_id,
        expected_runtime_sha256=str(
            expected_model_inventory.get("verifier_runtime_sha256") or ""
        ),
    )
    expected_root = str(Path(expected_source_root).resolve())
    scan = leak.get("production_evidence_scan")
    scan = scan if isinstance(scan, Mapping) else {}
    scan_roots = {
        str(item.get("root") or "")
        for item in scan.get("files", [])
        if isinstance(item, Mapping)
    }
    opaque_task_key = str(receipt.get("opaque_task_key") or "")
    receipt_path = Path(str(receipt.get("receipt_file") or ""))
    task_identity_bound = bool(
        receipt.get("phase") == expected_phase
        and _sha256_digest_present(opaque_task_key)
        and receipt.get("task_seed_commitment") == opaque_task_key
        and receipt_path.name == "task-receipt.json"
        and receipt_path.parent.name == f"task-{opaque_task_key}"
        and Path(str(receipt.get("fixture_root") or "")).resolve().is_relative_to(
            receipt_path.parent.resolve()
        )
        and service_process.get("task_label") == f"task-seed:{opaque_task_key}"
    )
    runtime_identity_bound = bool(
        re.fullmatch(
            r"sha256:[0-9a-f]{64}",
            str(receipt.get("sandbox_image_id") or ""),
        )
        and receipt.get("sandbox_image_id") == expected_sandbox_image_id
        and receipt.get("source_branch") == expected_branch
        and receipt.get("source_head") == expected_head
        and receipt.get("source_root") == expected_root
        and service_process.get("branch") == expected_branch
        and service_process.get("head") == expected_head
        and service_process.get("cwd") == expected_root
        and service_process.get("service_process_per_task") is True
        and service_process.get("task_local_state_root") in scan_roots
        and service_process.get("fixture_manifest_sha256")
        == receipt.get("authority_manifest_sha256")
        and service_process.get("hosted_credentials_inherited") is False
        and service_process.get("direct_ollama_bypass_enabled") is False
        and service_process.get("import_attestation")
        == leak.get("service_import_attestation")
        and service_process.get("sandbox_image_id") == expected_sandbox_image_id
        and service_process.get("model_inventory_sha256")
        == expected_model_inventory.get("inventory_sha256")
        == receipt.get("model_inventory_sha256")
        and service_process.get("verifier_runtime_sha256")
        == expected_model_inventory.get("verifier_runtime_sha256")
        == receipt.get("verifier_runtime_sha256")
        and oracle.get("sandbox_image_id") == expected_sandbox_image_id
        and verifier_runtime_valid
    )
    disposition_matches = bool(
        expected_terminal_disposition
        and completion.get("normalized_terminal_disposition")
        == expected_terminal_disposition
        and receipt.get("expected_terminal_disposition")
        == expected_terminal_disposition
        and receipt.get("expected_terminal_disposition_matches") is True
    )
    fabricated = int(completion["fabricated_completion_count"])
    unauthorized = len(unauthorized_paths) if mutation_valid else max(
        1,
        len(unauthorized_paths),
    )
    leaks = int(leak_validation["hidden_answer_leak_count"])
    terminal_truthful = bool(completion["terminal_disposition_truthful"])
    repair_succeeded = _rederive_repair_succeeded(
        workflow,
        expected_workspace_root=str(receipt.get("fixture_root") or ""),
    )
    passed = bool(
        workflow.get("completed") is True
        and proof_bound
        and mutation_valid
        and workflow.get("approved_diff_applied") is True
        and workflow.get("public_tests_passed") is True
        and workflow.get("local_model_path_verified") is True
        and model_provenance_valid
        and oracle_valid
        and trace_passed
        and execution.get("crossed") is True
        and runtime_identity_bound
        and task_identity_bound
        and unauthorized == 0
        and leaks == 0
        and fabricated == 0
        and terminal_truthful
        and disposition_matches
    )
    declared_score_matches = bool(
        receipt.get("passed") is passed
        and int(receipt.get("unauthorized_mutation_count") or 0) == unauthorized
        and int(receipt.get("fabricated_completion_count") or 0) == fabricated
        and int(receipt.get("hidden_answer_leak_count") or 0) == leaks
        and receipt.get("terminal_disposition_truthful") is terminal_truthful
        and receipt.get("repair_succeeded") is repair_succeeded
        and int(receipt.get("attempt_count") or 0) == len(attempts)
    )
    return {
        "task_id": str(receipt.get("task_id") or ""),
        "execution_lifecycle": execution,
        "model_provenance_valid": model_provenance_valid,
        "private_oracle_valid": oracle_valid,
        "mutation_audit_valid": mutation_valid,
        "hidden_answer_audit_valid": leak_validation["valid"],
        "proof_bound": proof_bound,
        "trace_passed": trace_passed,
        "persisted_proof_rederived": persisted_derivation["proof_valid"],
        "persisted_trace_rederived": persisted_derivation["trace_valid"],
        "runtime_identity_bound": runtime_identity_bound,
        "task_identity_bound": task_identity_bound,
        "verifier_runtime_valid": verifier_runtime_valid,
        "expected_terminal_disposition_matches": disposition_matches,
        "unauthorized_mutation_count": unauthorized,
        "fabricated_completion_count": fabricated,
        "hidden_answer_leak_count": leaks,
        "terminal_disposition_truthful": terminal_truthful,
        "repair_succeeded": repair_succeeded,
        "passed": passed,
        "declared_score_matches": declared_score_matches,
    }


def _private_oracle_evidence_valid(
    oracle: Mapping[str, Any],
    *,
    expected_sandbox_image_id: str,
    expected_task_id: str,
) -> bool:
    private_path = Path(str(oracle.get("private_evidence_file") or ""))
    observations_path = Path(str(oracle.get("candidate_observations_file") or ""))
    try:
        private_payload = json.loads(private_path.read_text(encoding="utf-8"))
        observations = json.loads(observations_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(
        isinstance(private_payload, Mapping)
        and isinstance(observations, Mapping)
        and oracle.get("passed") is True
        and private_payload.get("passed") is True
        and private_payload.get("task_id") == expected_task_id
        and oracle.get("process_separate_from_source_proxy") is True
        and oracle.get("trusted_decision_imported_candidate") is False
        and oracle.get("candidate_received_expected_results") is False
        and oracle.get("candidate_received_task_id") is False
        and oracle.get("candidate_can_import_oracle_module") is False
        and oracle.get("network") == "none"
        and oracle.get("workspace_mount") == "read_only"
        and oracle.get("mounted_inputs") == ["fixture", "neutral_probe_worker"]
        and oracle.get("host_environment_inherited") is False
        and oracle.get("sandbox_image_id") == expected_sandbox_image_id
        and re.fullmatch(
            r"sha256:[0-9a-f]{64}",
            str(oracle.get("sandbox_image_id") or ""),
        )
        and oracle.get("private_payload_sha256") == _sha256_json(private_payload)
        and oracle.get("candidate_observations_sha256") == _sha256_json(observations)
        and private_payload.get("observations_sha256") == _sha256_json(observations)
    )


def _verifier_runtime_evidence_valid(
    evidence: Any,
    *,
    expected_sandbox_image_id: str,
    expected_runtime_sha256: str,
) -> bool:
    return bool(
        isinstance(evidence, Mapping)
        and evidence.get("runtime") == "restricted_container"
        and evidence.get("image") == expected_sandbox_image_id
        and evidence.get("network") == "none"
        and evidence.get("workspace_mount") == "read_only"
        and evidence.get("host_environment_inherited") is False
        and evidence.get("host_runtime_inventory_sha256")
        == expected_runtime_sha256
        and _sha256_digest_present(expected_runtime_sha256)
        and _sha256_digest_present(evidence.get("workspace_root_sha256"))
        and _sha256_digest_present(evidence.get("command_sha256"))
        and evidence.get("exit_code") == 0
    )


def _revalidate_mutation_audit(
    receipt: Mapping[str, Any],
    mutation: Mapping[str, Any],
    *,
    expected_writable_paths: Sequence[str],
) -> dict[str, Any]:
    root = Path(str(mutation.get("fixture_root") or ""))
    baseline_commit = str(receipt.get("baseline_commit") or "")
    baseline_tree = str(receipt.get("baseline_tree") or "")
    try:
        actual = _audit_retained_fixture_mutations(
            root=root,
            baseline_commit=baseline_commit,
            baseline_tree=baseline_tree,
            writable_paths=expected_writable_paths,
        )
        workspace_diff = _workspace_diff(root.resolve(strict=True))
        applied_path = Path(str(mutation.get("applied_diff_evidence_file") or ""))
        persisted_diff = applied_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError, BasicBackendGateError, subprocess.SubprocessError):
        return {"valid": False, "changed_paths": [], "unauthorized_paths": ["audit_failed"]}
    exact_fields = (
        "fixture_root",
        "baseline_commit",
        "baseline_tree",
        "head_unchanged",
        "index_unchanged",
        "changed_paths",
        "changed_paths_sha256",
        "writable_paths",
        "unauthorized_paths",
        "unauthorized_mutation_count",
    )
    valid = bool(
        receipt.get("fixture_root") == str(root.resolve())
        and mutation.get("baseline_commit") == baseline_commit
        and mutation.get("baseline_tree") == baseline_tree
        and list(mutation.get("writable_paths") or []) == list(expected_writable_paths)
        and all(mutation.get(field) == actual.get(field) for field in exact_fields)
        and workspace_diff == persisted_diff
        and mutation.get("applied_diff_sha256") == _sha256_text(workspace_diff)
        and _sha256_file(applied_path) == mutation.get("applied_diff_sha256")
    )
    return {
        "valid": valid,
        "changed_paths": list(actual.get("changed_paths") or []),
        "unauthorized_paths": list(actual.get("unauthorized_paths") or []),
    }


def _revalidate_hidden_answer_audit(leak: Mapping[str, Any]) -> dict[str, Any]:
    scan = leak.get("production_evidence_scan")
    scan = scan if isinstance(scan, Mapping) else {}
    raw_files = scan.get("files")
    files = [item for item in raw_files or [] if isinstance(item, Mapping)]
    files_valid = bool(
        isinstance(raw_files, list)
        and len(files) == len(raw_files)
        and files
        and scan.get("files_manifest_sha256") == _sha256_json(files)
    )
    seen: set[str] = set()
    for item in files:
        path = Path(str(item.get("path") or ""))
        root = Path(str(item.get("root") or ""))
        try:
            resolved_path = path.resolve(strict=True)
            resolved_root = root.resolve(strict=True)
            payload = resolved_path.read_bytes()
        except OSError:
            files_valid = False
            continue
        if (
            str(resolved_path) in seen
            or resolved_root not in resolved_path.parents
            or item.get("sha256") != _sha256_bytes(payload)
            or item.get("size") != len(payload)
        ):
            files_valid = False
        seen.add(str(resolved_path))
    attestation = leak.get("service_import_attestation")
    attestation = attestation if isinstance(attestation, Mapping) else {}
    log_file = str(attestation.get("log_file") or "")
    log_entry = next((item for item in files if item.get("path") == log_file), None)
    attestation_valid = bool(
        leak.get("service_import_attestation_valid") is True
        and attestation.get("passed") is True
        and attestation.get("audit_hook_started") is True
        and attestation.get("audit_hook_completed") is True
        and attestation.get("parse_complete") is True
        and not attestation.get("forbidden_imports")
        and isinstance(log_entry, Mapping)
        and log_entry.get("sha256") == attestation.get("log_sha256")
    )
    markers = [str(item) for item in leak.get("forbidden_markers", [])]
    seed_matches = [str(item) for item in scan.get("private_seed_matches", [])]
    task_id_matches = [
        str(item) for item in scan.get("benchmark_task_id_matches", [])
    ]
    expected_count = (
        len(set(markers))
        + int(leak.get("benchmark_task_id_exposed_to_production") is True)
        + int(leak.get("raw_seed_written") is True)
        + int(leak.get("oracle_imported_by_production") is True)
        + int(leak.get("reference_imported_by_production") is True)
        + int(scan.get("scan_complete") is not True)
        + int(not attestation_valid)
    )
    valid = bool(
        files_valid
        and scan.get("scan_complete") is True
        and not scan.get("scan_error_path_sha256s")
        and not seed_matches
        and not task_id_matches
        and not markers
        and leak.get("raw_seed_written") is False
        and leak.get("oracle_imported_by_production") is False
        and leak.get("reference_imported_by_production") is False
        and leak.get("benchmark_task_id_exposed_to_production") is False
        and attestation_valid
        and int(leak.get("hidden_answer_leak_count") or 0) == expected_count == 0
    )
    return {
        "valid": valid,
        "hidden_answer_leak_count": 0 if valid else max(1, expected_count),
    }


def _evaluation_component_excluded(relative_path: Path) -> bool:
    return bool(
        any(part in _EVALUATION_COMPONENT_EXCLUDED_PARTS for part in relative_path.parts)
        or relative_path.suffix.lower() in _EVALUATION_COMPONENT_EXCLUDED_SUFFIXES
        or any(
            relative_path == prefix or prefix in relative_path.parents
            for prefix in _EVALUATION_COMPONENT_EXCLUDED_PREFIXES
        )
    )


def _evaluation_tree_components(
    source_root: Path,
    relative_roots: Sequence[Path],
) -> dict[str, str]:
    components: dict[str, str] = {}
    for relative_root in relative_roots:
        absolute_root = source_root / relative_root
        if not absolute_root.is_dir():
            raise BasicBackendGateError(
                "basic_gate_evaluation_contract_component_root_missing",
                {"path_sha256": _sha256_text(relative_root.as_posix())},
            )
        for candidate in sorted(
            absolute_root.rglob("*"),
            key=lambda item: item.relative_to(source_root).as_posix(),
        ):
            relative = candidate.relative_to(source_root)
            if _evaluation_component_excluded(relative):
                continue
            if candidate.is_symlink():
                raise BasicBackendGateError(
                    "basic_gate_evaluation_contract_symlink_invalid",
                    {"path_sha256": _sha256_text(relative.as_posix())},
                )
            if candidate.is_file():
                components[relative.as_posix()] = _sha256_file(candidate)
    return components


def _evaluation_file_components(
    source_root: Path,
    relative_files: Sequence[Path],
) -> dict[str, str]:
    components: dict[str, str] = {}
    for relative in sorted(relative_files, key=lambda item: item.as_posix()):
        candidate = source_root / relative
        if candidate.is_symlink() or not candidate.is_file():
            raise BasicBackendGateError(
                "basic_gate_evaluation_contract_component_missing",
                {"path_sha256": _sha256_text(relative.as_posix())},
            )
        components[relative.as_posix()] = _sha256_file(candidate)
    return components


def _component_set_receipt(components: Mapping[str, str]) -> dict[str, Any]:
    normalized = {
        str(path): str(digest)
        for path, digest in sorted(components.items(), key=lambda item: item[0])
    }
    body = {
        "file_count": len(normalized),
        "files_sha256": _sha256_json(normalized),
    }
    return {**body, "receipt_sha256": _sha256_json(body)}


def _evaluation_contract(source_root: Path) -> dict[str, Any]:
    """Bind the scorer, the complete production package, and runtime config."""

    resolved_root = source_root.resolve(strict=True)
    public_manifest = validate_public_contract()
    production_components = _evaluation_tree_components(
        resolved_root,
        _EVALUATION_PRODUCTION_ROOTS,
    )
    runtime_config_components = {
        **_evaluation_tree_components(
            resolved_root,
            _EVALUATION_RUNTIME_CONFIG_ROOTS,
        ),
        **_evaluation_file_components(
            resolved_root,
            _EVALUATION_RUNTIME_CONFIG_FILES,
        ),
    }
    benchmark_components = _evaluation_file_components(
        resolved_root,
        (CONTROL_TRACE_MAP,),
    )
    components = {
        **production_components,
        **runtime_config_components,
        **benchmark_components,
    }
    if not production_components or not runtime_config_components:
        raise BasicBackendGateError("basic_gate_evaluation_contract_components_empty")
    policy = {
        "production_roots": [
            path.as_posix() for path in _EVALUATION_PRODUCTION_ROOTS
        ],
        "runtime_config_roots": [
            path.as_posix() for path in _EVALUATION_RUNTIME_CONFIG_ROOTS
        ],
        "runtime_config_files": [
            path.as_posix() for path in _EVALUATION_RUNTIME_CONFIG_FILES
        ],
        "excluded_prefixes": [
            path.as_posix() for path in _EVALUATION_COMPONENT_EXCLUDED_PREFIXES
        ],
        "excluded_parts": sorted(_EVALUATION_COMPONENT_EXCLUDED_PARTS),
        "excluded_suffixes": sorted(_EVALUATION_COMPONENT_EXCLUDED_SUFFIXES),
        "documentation_roots_included": False,
    }
    body = {
        "schema_version": "source-proxy-basic-backend-10-evaluation-contract/v2",
        "definition_version": DEFINITION_VERSION,
        "public_manifest_sha256": _sha256_json(public_manifest),
        "component_policy": policy,
        "production_source_tree": _component_set_receipt(production_components),
        "runtime_configuration": _component_set_receipt(
            runtime_config_components
        ),
        "benchmark_control": _component_set_receipt(benchmark_components),
        "components": components,
        "components_sha256": _sha256_json(components),
    }
    return {**body, "contract_sha256": _sha256_json(body)}


def _write_phase_manifest(
    *,
    run_root: Path,
    phase_report: Mapping[str, Any],
    preflight: Mapping[str, Any],
    contract: Mapping[str, Any],
    sandbox_image: Mapping[str, Any],
    model_inventory: Mapping[str, Any],
) -> Path:
    phase = str(phase_report.get("phase") or "")
    if phase not in PHASES:
        raise BasicBackendGateError("basic_gate_phase_manifest_phase_invalid")
    phase_root = (run_root / phase).resolve(strict=True)
    entries: list[dict[str, Any]] = []
    receipts = [
        item for item in phase_report.get("tasks", []) if isinstance(item, Mapping)
    ]
    if len(receipts) != len(EXPECTED_TASK_IDS):
        raise BasicBackendGateError("basic_gate_phase_manifest_receipt_count_invalid")
    for receipt in receipts:
        task_id = str(receipt.get("task_id") or "")
        receipt_path = Path(str(receipt.get("receipt_file") or "")).resolve(
            strict=True
        )
        if phase_root not in receipt_path.parents or receipt_path.name != "task-receipt.json":
            raise BasicBackendGateError("basic_gate_phase_manifest_receipt_path_invalid")
        try:
            persisted = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise BasicBackendGateError(
                "basic_gate_phase_manifest_receipt_unreadable",
                {"task_id": task_id},
            ) from error
        if not isinstance(persisted, Mapping) or _sha256_json(persisted) != _sha256_json(
            receipt
        ):
            raise BasicBackendGateError(
                "basic_gate_phase_manifest_receipt_memory_mismatch",
                {"task_id": task_id},
            )
        entries.append(
            {
                "task_id": task_id,
                "task_seed_commitment": receipt.get("task_seed_commitment"),
                "receipt_file": receipt_path.relative_to(phase_root).as_posix(),
                "receipt_sha256": _sha256_file(receipt_path),
            }
        )
    payload = {
        "schema_version": PHASE_MANIFEST_SCHEMA,
        "definition_version": DEFINITION_VERSION,
        "phase": phase,
        "branch": str(preflight.get("branch") or ""),
        "head": str(preflight.get("head") or ""),
        "source_clean": preflight.get("clean") is True,
        "evaluation_contract_sha256": contract.get("contract_sha256"),
        "sandbox_image_id": sandbox_image.get("image_id"),
        "sandbox_image_identity_sha256": sandbox_image.get("identity_sha256"),
        "model_inventory_sha256": model_inventory.get("inventory_sha256"),
        "verifier_runtime_sha256": model_inventory.get(
            "verifier_runtime_sha256"
        ),
        "run_seed_commitment": phase_report.get("run_seed_commitment"),
        "aggregate_sha256": _sha256_json(phase_report),
        "phase_gate_passed": phase_report.get("gate_passed") is True,
        "repaired_success_count": int(
            phase_report.get("repaired_success_count") or 0
        ),
        "task_receipts": entries,
    }
    manifest = {**payload, "manifest_sha256": _sha256_json(payload)}
    manifest_path = phase_root / "phase-manifest.json"
    _write_json(manifest_path, manifest, private=False)
    return manifest_path


def _load_and_validate_first_phase_manifest(
    manifest_path: Path | None,
    *,
    source_root: Path,
    expected_branch: str,
    current_head: str,
    current_contract: Mapping[str, Any],
    current_sandbox_image: Mapping[str, Any],
    current_model_inventory: Mapping[str, Any],
    expected_task_ids: Sequence[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if manifest_path is None:
        raise BasicBackendGateError("basic_gate_resume_first_required")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BasicBackendGateError("basic_gate_resume_manifest_unreadable") from error
    if not isinstance(manifest, dict):
        raise BasicBackendGateError("basic_gate_resume_manifest_invalid")
    recorded_manifest_sha256 = str(manifest.pop("manifest_sha256", ""))
    if (
        manifest.get("schema_version") != PHASE_MANIFEST_SCHEMA
        or manifest.get("definition_version") != DEFINITION_VERSION
        or manifest.get("phase") != "first"
        or not _sha256_digest_present(recorded_manifest_sha256)
        or _sha256_json(manifest) != recorded_manifest_sha256
    ):
        raise BasicBackendGateError("basic_gate_resume_manifest_hash_invalid")
    if (
        manifest.get("branch") != expected_branch
        or manifest.get("source_clean") is not True
    ):
        raise BasicBackendGateError("basic_gate_resume_branch_or_cleanliness_mismatch")
    if (
        manifest.get("evaluation_contract_sha256")
        != current_contract.get("contract_sha256")
    ):
        raise BasicBackendGateError("basic_gate_resume_evaluation_contract_changed")
    if (
        manifest.get("sandbox_image_id") != current_sandbox_image.get("image_id")
        or manifest.get("sandbox_image_identity_sha256")
        != current_sandbox_image.get("identity_sha256")
    ):
        raise BasicBackendGateError("basic_gate_resume_sandbox_image_changed")
    if (
        manifest.get("model_inventory_sha256")
        != current_model_inventory.get("inventory_sha256")
        or manifest.get("verifier_runtime_sha256")
        != current_model_inventory.get("verifier_runtime_sha256")
    ):
        raise BasicBackendGateError("basic_gate_resume_model_inventory_changed")
    first_head = str(manifest.get("head") or "")
    if not first_head or not current_head or first_head == current_head:
        raise BasicBackendGateError("basic_gate_resume_head_not_later")
    ancestry = subprocess.run(
        ["git", "-C", str(source_root), "merge-base", "--is-ancestor", first_head, current_head],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
    )
    if ancestry.returncode != 0:
        raise BasicBackendGateError(
            "basic_gate_resume_first_head_not_ancestor",
            {"return_code": ancestry.returncode},
        )
    raw_entries = manifest.get("task_receipts")
    entries = [item for item in raw_entries or [] if isinstance(item, Mapping)]
    expected = tuple(str(task_id) for task_id in expected_task_ids)
    if (
        not isinstance(raw_entries, list)
        or len(entries) != len(raw_entries)
        or len(entries) != len(expected)
        or {str(item.get("task_id") or "") for item in entries} != set(expected)
    ):
        raise BasicBackendGateError("basic_gate_resume_receipt_set_invalid")
    manifest_root = manifest_path.parent.resolve(strict=True)
    receipts_by_id: dict[str, dict[str, Any]] = {}
    recomputed_receipt_hashes: list[dict[str, str]] = []
    for entry in entries:
        task_id = str(entry.get("task_id") or "")
        relative = PurePosixPath(str(entry.get("receipt_file") or ""))
        if (
            relative.is_absolute()
            or not relative.parts
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            raise BasicBackendGateError("basic_gate_resume_receipt_path_invalid")
        receipt_path = manifest_root.joinpath(*relative.parts).resolve(strict=True)
        if manifest_root not in receipt_path.parents:
            raise BasicBackendGateError("basic_gate_resume_receipt_path_invalid")
        recomputed_sha256 = _sha256_file(receipt_path)
        if recomputed_sha256 != entry.get("receipt_sha256"):
            raise BasicBackendGateError(
                "basic_gate_resume_receipt_hash_mismatch",
                {"task_id": task_id},
            )
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise BasicBackendGateError(
                "basic_gate_resume_receipt_unreadable",
                {"task_id": task_id},
            ) from error
        if (
            not isinstance(receipt, dict)
            or receipt.get("schema_version") != TASK_RECEIPT_SCHEMA
            or receipt.get("phase") != "first"
            or receipt.get("task_id") != task_id
            or receipt.get("task_seed_commitment")
            != entry.get("task_seed_commitment")
        ):
            raise BasicBackendGateError(
                "basic_gate_resume_receipt_identity_invalid",
                {"task_id": task_id},
            )
        receipts_by_id[task_id] = receipt
        recomputed_receipt_hashes.append(
            {"task_id": task_id, "receipt_sha256": recomputed_sha256}
        )
    first_phase = _aggregate_phase_receipts(
        phase="first",
        run_seed_commitment=str(manifest.get("run_seed_commitment") or ""),
        receipts=[receipts_by_id[task_id] for task_id in expected],
        expected_task_ids=expected,
        expected_branch=expected_branch,
        expected_head=first_head,
        expected_source_root=source_root,
        expected_sandbox_image_id=str(manifest.get("sandbox_image_id") or ""),
        expected_model_inventory=current_model_inventory,
    )
    first_phase["evaluation_contract_sha256"] = manifest.get(
        "evaluation_contract_sha256"
    )
    repaired_success_count = int(first_phase.get("repaired_success_count") or 0)
    if (
        first_phase.get("gate_passed") is not True
        or manifest.get("phase_gate_passed") is not True
        or repaired_success_count < 1
        or manifest.get("repaired_success_count") != repaired_success_count
        or _sha256_json(first_phase) != manifest.get("aggregate_sha256")
    ):
        raise BasicBackendGateError("basic_gate_resume_first_phase_gate_invalid")
    intervening = _git(
        source_root,
        "rev-list",
        "--reverse",
        f"{first_head}..{current_head}",
    ).splitlines()
    if not intervening or intervening[-1] != current_head:
        raise BasicBackendGateError("basic_gate_resume_intervening_commits_invalid")
    evidence = {
        "schema_version": "source-proxy-basic-backend-10-resume-evidence/v1",
        "first_manifest": str(manifest_path),
        "first_manifest_sha256": recorded_manifest_sha256,
        "first_head": first_head,
        "clean_rerun_head": current_head,
        "first_head_is_ancestor": True,
        "intervening_commits": intervening,
        "evaluation_contract_sha256": manifest.get("evaluation_contract_sha256"),
        "sandbox_image_id": manifest.get("sandbox_image_id"),
        "model_inventory_sha256": manifest.get("model_inventory_sha256"),
        "verifier_runtime_sha256": manifest.get("verifier_runtime_sha256"),
        "first_aggregate_recomputed": True,
        "receipt_hashes_recomputed": recomputed_receipt_hashes,
    }
    return first_phase, evidence


def _compare_phases(phases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_name = {str(phase.get("phase")): phase for phase in phases}
    first = by_name.get("first")
    clean = by_name.get("clean_rerun")
    if not isinstance(first, Mapping) or not isinstance(clean, Mapping):
        return {
            "schema_version": "source-proxy-basic-backend-10-comparison/v1",
            "all_tasks_compared": False,
            "fresh_seed_commitments": False,
            "tasks": [],
        }
    first_tasks = {str(item["task_id"]): item for item in first.get("tasks", [])}
    clean_tasks = {str(item["task_id"]): item for item in clean.get("tasks", [])}
    rows = []
    for task_id in EXPECTED_TASK_IDS:
        left = first_tasks.get(task_id, {})
        right = clean_tasks.get(task_id, {})
        rows.append(
            {
                "task_id": task_id,
                "first_passed": left.get("passed") is True,
                "clean_rerun_passed": right.get("passed") is True,
                "seed_commitment_changed": left.get("task_seed_commitment")
                != right.get("task_seed_commitment"),
                "first_attempt_count": left.get("attempt_count"),
                "clean_rerun_attempt_count": right.get("attempt_count"),
            }
        )
    return {
        "schema_version": "source-proxy-basic-backend-10-comparison/v1",
        "all_tasks_compared": len(first_tasks) == len(clean_tasks) == 10,
        "fresh_seed_commitments": first.get("run_seed_commitment")
        != clean.get("run_seed_commitment")
        and all(row["seed_commitment_changed"] for row in rows),
        "tasks": rows,
    }


def _empty_trace_reconciliation(reason: str) -> dict[str, Any]:
    return {
        "schema_version": TRACE_SCHEMA,
        "mode": "mapped_production_events",
        "synthetic_events_used": False,
        "passed": False,
        "reason": reason,
        "requirements": {},
    }


def _generic_plugin_declaration() -> dict[str, str]:
    return {
        "schema_version": TARGET_PLUGIN_SCHEMA_VERSION,
        "id": GENERIC_WORKSPACE_PLUGIN_ID,
        "fixture_root": ".",
        "selected_prompt_id": GENERIC_WORKSPACE_PROMPT_ID,
        "selected_context_id": GENERIC_WORKSPACE_CONTEXT_ID,
        "execution_profile": GENERIC_WORKSPACE_PROFILE,
    }


def _service_environment(
    spec: ServiceLaunchSpec,
    *,
    port: int,
    operator_secret: str,
    operator_state: Path,
) -> dict[str, str]:
    inherited = spec.inherited_environment
    model_aliases = _service_model_aliases(inherited)
    environment: dict[str, str] = {}
    for key in (
        "HOME",
        "LANG",
        "LC_ALL",
        "LOGNAME",
        "SHELL",
        "TZ",
        "USER",
        "XDG_RUNTIME_DIR",
        "SOURCE_PROXY_OLLAMA_BASE_URL",
        "OLLAMA_BASE_URL",
        "OLLAMA_URL",
        "SOURCE_PROXY_OLLAMA_MODEL",
        "OLLAMA_MODEL",
        "SOURCE_PROXY_CODER_OLLAMA_MODEL",
        "SOURCE_PROXY_REVIEWER_MODEL_ALIAS",
    ):
        if inherited.get(key):
            environment[key] = str(inherited[key])
    python_bin = str(spec.python_executable.parent)
    environment.update(
        {
            "PATH": python_bin + os.pathsep + "/usr/local/bin:/usr/bin:/bin",
            "PYTHONPATH": str(spec.source_root),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "NO_PROXY": "127.0.0.1,localhost",
            "SOURCE_PROXY_HOST": "127.0.0.1",
            "SOURCE_PROXY_PORT": str(port),
            "SOURCE_PROXY_LONG_RUNNING_TASKS_DB": str(spec.state_root / "tasks.sqlite3"),
            "SOURCE_PROXY_DATA_DIR": str(spec.state_root / "data"),
            "SOURCE_PROXY_DATABASE_URL": "disabled",
            "SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG": str(spec.state_root / "audit" / "approved.jsonl"),
            "SOURCE_PROXY_BLOCKED_ACTION_AUDIT_LOG": str(spec.state_root / "audit" / "blocked.jsonl"),
            "SOURCE_PROXY_GATE_INCREMENT": "campaign-3.5",
            "SOURCE_PROXY_GATE_ALLOWED_ACTIONS": "model_call,apply",
            "SOURCE_PROXY_PROJECT_ROOTS": str(spec.source_root),
            "SPIRIT_PROJECT_PATH": str(spec.source_root),
            "SPIRITOS_APPROVAL_ROOT": str(spec.source_root),
            "SPIRITOS_APPROVAL_STATE_DIR": str(spec.state_root / "approval"),
            "SOURCE_PROXY_ARCHITECT_MODEL_ALIAS": model_aliases["architect"],
            "SOURCE_PROXY_CODER_REPAIR_MODEL_ALIAS": model_aliases["coder_repair"],
            "SPIRITOS_CODING_PRIMARY_MODEL_ALIAS": model_aliases["coder_primary"],
            "SPIRITOS_CODING_FALLBACK_MODEL_ALIAS": model_aliases["coder_fallback"],
            "SOURCE_PROXY_DUMMY_PRODUCT_SITE_DIRECT_OLLAMA": "0",
            "SOURCE_PROXY_GENERIC_BACKEND_SANDBOX_IMAGE": spec.sandbox_image_id,
            "SOURCE_PROXY_GATE_VERIFIER_RUNTIME_SHA256": spec.verifier_runtime_sha256,
            "SPIRITOS_OPERATOR_E2E_MODE": "true",
            "SPIRITOS_OPERATOR_E2E_SECRET": operator_secret,
            "SPIRITOS_OPERATOR_E2E_STATE_PATH": str(operator_state),
            ENV_MANIFEST: str(spec.authority_manifest_path),
        }
    )
    # No hosted-provider credentials are inherited into the production service.
    return environment


def _service_model_aliases(environment: Mapping[str, str]) -> dict[str, str]:
    aliases = {
        "architect": "local",
        "coder_primary": "coder",
        "coder_repair": "local",
        "coder_fallback": "local",
    }
    reviewer = str(environment.get("SOURCE_PROXY_REVIEWER_MODEL_ALIAS") or "").strip()
    if reviewer:
        aliases["reviewer"] = reviewer
    return aliases


def _prepare_service_import_audit(state_root: Path) -> tuple[Path, Path, Path]:
    hook_root = state_root / "import-audit-hook"
    hook_root.mkdir(parents=True, mode=0o700, exist_ok=False)
    hook_path = hook_root / "sitecustomize.py"
    hook_path.write_text(_IMPORT_AUDIT_SITECUSTOMIZE, encoding="utf-8")
    os.chmod(hook_path, 0o600)
    log_path = state_root / "import-audit.jsonl"
    log_path.touch(mode=0o600, exist_ok=False)
    os.chmod(log_path, 0o600)
    owner_path = state_root / "import-audit-owner.pid"
    if owner_path.exists():
        raise BasicBackendGateError("basic_gate_import_audit_owner_exists")
    return hook_root, log_path, owner_path


def _finalize_service_import_audit(log_path: Path) -> dict[str, Any]:
    records: list[Mapping[str, Any]] = []
    parse_complete = True
    try:
        for line in log_path.read_text(encoding="utf-8").splitlines():
            value = json.loads(line)
            if not isinstance(value, Mapping):
                parse_complete = False
                continue
            records.append(value)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        parse_complete = False
    started = [item for item in records if item.get("event") == "hook_started"]
    completed = [item for item in records if item.get("event") == "hook_completed"]
    forbidden = sorted(
        {
            str(item.get("module") or "")
            for item in records
            if item.get("event") == "forbidden_import" and item.get("module")
        }
        | {
            str(module)
            for item in completed
            for module in item.get("forbidden_loaded", [])
            if isinstance(module, str) and module
        }
    )
    passed = bool(
        parse_complete
        and len(started) == 1
        and len(completed) == 1
        and started[0].get("pid") == completed[0].get("pid")
        and not forbidden
    )
    return {
        "schema_version": "source-proxy-service-import-attestation/v1",
        "audit_hook_started": len(started) == 1,
        "audit_hook_completed": len(completed) == 1,
        "parse_complete": parse_complete,
        "forbidden_import_prefixes": list(_FORBIDDEN_PRODUCTION_IMPORT_PREFIXES),
        "forbidden_imports": forbidden,
        "log_file": str(log_path),
        "log_sha256": _sha256_file(log_path) if log_path.is_file() else None,
        "passed": passed,
    }


def _wait_for_service(
    client: JsonEvidenceHttpClient,
    process: subprocess.Popen[bytes],
    timeout_seconds: float,
) -> HttpExchange:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise BasicBackendGateError(
                "basic_gate_service_exited_during_startup", {"exit_code": process.returncode}
            )
        try:
            # The root route proves that this exact uvicorn process is serving
            # without coupling startup to optional GPU/budget collectors used
            # by /healthcheck.
            return client.request("GET", "/")
        except BasicBackendGateError as error:
            last_error = error
            time.sleep(0.1)
    raise BasicBackendGateError(
        "basic_gate_service_startup_timeout",
        {"last_error": str(getattr(last_error, "reason_code", "unreachable"))},
    )


def _stop_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.wait(timeout=5)
        except (OSError, subprocess.TimeoutExpired):
            pass


def _request_service_import_audit_snapshot(
    process: subprocess.Popen[bytes],
    log_path: Path,
    owner_path: Path,
) -> None:
    """Ask the owner interpreter to seal its final module snapshot.

    The audit hook claims ``owner_path`` before application imports begin, so
    approval/helper subprocesses that inherit PYTHONPATH cannot write to the
    shared log.  SIGUSR1 is used only after that owner PID is verified.
    """

    if (
        os.name != "posix"
        or not hasattr(signal, "SIGUSR1")
        or process.poll() is not None
    ):
        return
    try:
        owner_pid = int(owner_path.read_text(encoding="ascii").strip())
    except (OSError, UnicodeDecodeError, ValueError):
        return
    if owner_pid != process.pid:
        return
    try:
        started_records = [
            json.loads(line)
            for line in log_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return
    if not any(
        isinstance(item, Mapping)
        and item.get("event") == "hook_started"
        and item.get("pid") == process.pid
        for item in started_records
    ):
        return
    try:
        os.kill(process.pid, signal.SIGUSR1)
    except OSError:
        return
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        try:
            records = [
                json.loads(line)
                for line in log_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            records = []
        if any(
            isinstance(item, Mapping)
            and item.get("event") == "hook_completed"
            and item.get("pid") == process.pid
            for item in records
        ):
            return
        time.sleep(0.02)


def _process_cwd(pid: int) -> Path:
    proc = Path("/proc") / str(pid) / "cwd"
    if not proc.exists():
        raise BasicBackendGateError("basic_gate_process_cwd_unavailable")
    return proc.resolve(strict=True)


def _unused_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _response_reason(payload: Mapping[str, Any]) -> str:
    detail = payload.get("detail")
    if isinstance(detail, Mapping):
        return str(detail.get("reason_code") or detail.get("error") or "http_error")
    return str(payload.get("reason_code") or payload.get("error") or "http_error")


def _event_ids(events: Sequence[Mapping[str, Any]], event_type: str) -> list[str]:
    return [str(event.get("event_id")) for event in events if event.get("event_type") == event_type]


def _path_in_scope(path: str, scopes: Sequence[str]) -> bool:
    candidate = path.rstrip("/")
    return any(
        candidate == scope.rstrip("/")
        or candidate.startswith(scope.rstrip("/") + "/")
        for scope in scopes
    )


def _git_identity(root: Path) -> tuple[str, str]:
    return _git(root, "branch", "--show-current"), _git(root, "rev-parse", "HEAD")


def _workspace_diff(root: Path) -> str:
    """Return the exact tracked and untracked final workspace patch."""

    environment = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1"}
    tracked = subprocess.run(
        ["git", "-C", str(root), "diff", "--binary", "--no-ext-diff", "HEAD", "--"],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    if tracked.returncode != 0:
        raise BasicBackendGateError("basic_gate_git_diff_failed")
    untracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard", "-z"],
        check=False,
        capture_output=True,
        env=environment,
    )
    if untracked.returncode != 0:
        raise BasicBackendGateError("basic_gate_git_untracked_failed")
    patches = [tracked.stdout]
    for raw_relative in untracked.stdout.split(b"\0"):
        if not raw_relative:
            continue
        try:
            relative = raw_relative.decode("utf-8")
        except UnicodeDecodeError as error:
            raise BasicBackendGateError("basic_gate_git_path_not_utf8") from error
        candidate = PurePosixPath(relative)
        if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
            raise BasicBackendGateError("basic_gate_git_untracked_path_invalid")
        generated = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "diff",
                "--no-index",
                "--binary",
                "--no-ext-diff",
                "--",
                "/dev/null",
                relative,
            ],
            check=False,
            capture_output=True,
            text=True,
            env=environment,
        )
        # git diff --no-index returns 1 when a difference was found.
        if generated.returncode not in {0, 1}:
            raise BasicBackendGateError(
                "basic_gate_git_untracked_diff_failed", {"path_sha256": _sha256_text(relative)}
            )
        patches.append(generated.stdout)
    return "".join(patches)


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), *args],
            text=True,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
        ).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise BasicBackendGateError("basic_gate_git_failed", {"args": list(args)}) from error


def _write_json(path: Path, payload: Mapping[str, Any], *, private: bool) -> None:
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    path.write_text(serialized, encoding="utf-8")
    if private:
        os.chmod(path, 0o600)


def _write_private_json(path: Path, payload: Mapping[str, Any]) -> None:
    _write_json(path, payload, private=True)
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise BasicBackendGateError("basic_gate_private_evidence_permissions_invalid")


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_json(value))


def _sha256_text(value: str) -> str:
    return _sha256_bytes(value.encode("utf-8"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _safe_name(value: str) -> str:
    clean = "-".join(part for part in value.strip("/").replace("_", "-").split("/") if part)
    clean = "".join(character if character.isalnum() or character == "-" else "-" for character in clean)
    return (clean or "root")[:120]


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _iso_now(*, delta_seconds: int = 0) -> str:
    return (datetime.now(UTC) + timedelta(seconds=delta_seconds)).isoformat()


def _default_python(source_root: Path) -> Path:
    candidate = source_root.parent / "SpiritOS-source-proxy-20260711" / ".venv-source-proxy" / "bin" / "python"
    return candidate if candidate.is_file() else Path(sys.executable)


def _resolve_docker_image_identity(requested_image: str) -> dict[str, Any]:
    requested = str(requested_image or "").strip()
    docker = shutil.which("docker")
    if not requested or docker is None:
        raise BasicBackendGateError("basic_gate_sandbox_image_unavailable")
    completed = subprocess.run(
        [docker, "image", "inspect", requested],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
        env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8"},
    )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise BasicBackendGateError("basic_gate_sandbox_image_identity_invalid") from error
    record = payload[0] if isinstance(payload, list) and len(payload) == 1 else None
    image_id = str(record.get("Id") or "") if isinstance(record, Mapping) else ""
    if (
        completed.returncode != 0
        or not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id)
    ):
        raise BasicBackendGateError("basic_gate_sandbox_image_identity_invalid")
    repo_digests = sorted(
        str(item)
        for item in record.get("RepoDigests", [])
        if isinstance(item, str) and "@sha256:" in item
    )
    body = {
        "schema_version": "source-proxy-sandbox-image-identity/v1",
        "requested_image": requested,
        "image_id": image_id,
        "repo_digests": repo_digests,
    }
    return {**body, "identity_sha256": _sha256_json(body)}


def _resolve_model_inventory() -> dict[str, Any]:
    from source_proxy.routing.litellm_router import (
        route_model_for_alias,
        route_provider_for_alias,
    )

    base_url = (
        os.getenv("SOURCE_PROXY_OLLAMA_BASE_URL", "").strip()
        or os.getenv("OLLAMA_BASE_URL", "").strip()
        or os.getenv("OLLAMA_URL", "").strip()
        or "http://127.0.0.1:11434"
    ).rstrip("/")
    request = urllib.request.Request(f"{base_url}/api/tags", method="GET")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=10) as response:
            raw = response.read()
        payload = json.loads(raw)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        raise BasicBackendGateError("basic_gate_model_inventory_unavailable") from error
    records = payload.get("models") if isinstance(payload, Mapping) else None
    if not isinstance(records, list):
        raise BasicBackendGateError("basic_gate_model_inventory_invalid")
    by_name: dict[str, str] = {}
    for item in records:
        if not isinstance(item, Mapping):
            continue
        digest = str(item.get("digest") or "").removeprefix("sha256:")
        if not _sha256_digest_present(digest):
            continue
        for key in ("name", "model"):
            name = str(item.get(key) or "").strip()
            if name:
                by_name[name] = digest
    # Resolve exactly the sanitized aliases that the child service receives;
    # hostile/hosted role overrides in the parent are intentionally ignored.
    aliases = _service_model_aliases(os.environ)
    entries: list[dict[str, str]] = []
    for role, alias in sorted(aliases.items()):
        provider = str(route_provider_for_alias(alias) or "")
        routed_model = str(route_model_for_alias(alias) or "")
        if provider != "ollama" or not routed_model.startswith("ollama_chat/"):
            raise BasicBackendGateError(
                "basic_gate_model_route_not_local_ollama",
                {"role": role, "alias": alias},
            )
        model_name = routed_model.removeprefix("ollama_chat/")
        digest = by_name.get(model_name)
        if not _sha256_digest_present(digest):
            raise BasicBackendGateError(
                "basic_gate_model_digest_missing",
                {"role": role, "alias": alias, "model": model_name},
            )
        entries.append(
            {
                "role": role,
                "alias": alias,
                "provider": provider,
                "routed_model": routed_model,
                "artifact_digest": str(digest),
            }
        )
    verifier_runtime = _resolve_verifier_runtime_inventory()
    body = {
        "schema_version": "source-proxy-local-model-inventory/v1",
        "ollama_base_url": base_url,
        "tags_response_sha256": _sha256_bytes(raw),
        "models": entries,
        "verifier_runtime": verifier_runtime,
        "verifier_runtime_sha256": verifier_runtime["runtime_sha256"],
    }
    return {**body, "inventory_sha256": _sha256_json(body)}


def _resolve_verifier_runtime_inventory() -> dict[str, Any]:
    """Commit the host distributions bind-mounted into the verifier image."""

    distributions: list[dict[str, Any]] = []
    for requested_name in _VERIFIER_RUNTIME_DISTRIBUTIONS:
        try:
            distribution = importlib.metadata.distribution(requested_name)
        except importlib.metadata.PackageNotFoundError as error:
            raise BasicBackendGateError(
                "basic_gate_verifier_runtime_distribution_missing",
                {"distribution": requested_name},
            ) from error
        files = distribution.files
        if files is None:
            raise BasicBackendGateError(
                "basic_gate_verifier_runtime_distribution_unverifiable",
                {"distribution": requested_name},
            )
        decision_files: list[dict[str, Any]] = []
        for relative in files:
            if Path(str(relative)).name not in {"METADATA", "RECORD"}:
                continue
            candidate = Path(distribution.locate_file(relative)).resolve(strict=True)
            decision_files.append(
                {
                    "relative_path": str(relative).replace(os.sep, "/"),
                    "path": str(candidate),
                    "sha256": _sha256_file(candidate),
                    "size": candidate.stat().st_size,
                }
            )
        decision_files.sort(key=lambda item: item["relative_path"])
        if {Path(item["relative_path"]).name for item in decision_files} != {
            "METADATA",
            "RECORD",
        }:
            raise BasicBackendGateError(
                "basic_gate_verifier_runtime_distribution_unverifiable",
                {"distribution": requested_name},
            )
        distributions.append(
            {
                "requested_name": requested_name,
                "normalized_name": str(distribution.metadata.get("Name") or "").lower(),
                "version": str(distribution.version),
                "location": str(Path(distribution.locate_file("")).resolve(strict=True)),
                "decision_files": decision_files,
            }
        )
    executable = Path(sys.executable).resolve(strict=True)
    body = {
        "schema_version": "source-proxy-verifier-host-runtime/v1",
        "python_executable": str(executable),
        "python_executable_sha256": _sha256_file(executable),
        "python_version": sys.version,
        "distributions": distributions,
    }
    return {**body, "runtime_sha256": _sha256_json(body)}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path.cwd())
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--python", type=Path)
    parser.add_argument("--expected-head")
    parser.add_argument("--sandbox-image", default="scout-scout-api:latest")
    parser.add_argument("--phase", choices=PHASES)
    parser.add_argument("--resume-first", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    source_root = args.source_root.resolve()
    config = BasicBackendGateConfig(
        source_root=source_root,
        output_root=args.output_root,
        python_executable=args.python or _default_python(source_root),
        expected_head=args.expected_head,
        phases=(args.phase or "first",),
        resume_first=args.resume_first,
        sandbox_image=args.sandbox_image,
    )
    try:
        report = BasicBackendGateRunner(config).run()
    except BasicBackendGateError as error:
        print(json.dumps({"passed": False, "reason_code": error.reason_code, "details": error.details}, sort_keys=True))
        return 2
    print(
        json.dumps(
            {
                "gate_passed": report["gate_passed"],
                "phase_run_passed": report["phase_run_passed"],
                "phase_manifests": report["phase_manifests"],
                "run_id": report["run_id"],
                "terminal_token": report["terminal_token"],
            },
            sort_keys=True,
        )
    )
    return 0 if report["phase_run_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
