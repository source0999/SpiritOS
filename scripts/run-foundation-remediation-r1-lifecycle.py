#!/usr/bin/env python3
"""Own the clean, production service lifecycle for Foundation R1 proving.

The inner proving client remains an HTTP-only black-box consumer.  This outer
launcher supplies the evidence that an HTTP client cannot: exact clean linked
worktree identity, a fresh Next production build, isolated authority state,
process/CWD/port ownership, and fail-closed teardown.  Its receipt is strictly
subordinate evidence; it never declares the remediation terminal on its own.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import importlib
import json
import os
import re
import secrets
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence


REMEDIATION_ID = "spiritos-foundation-remediation-r1"
RECEIPT_SCHEMA = "spiritos-foundation-remediation-r1-lifecycle-receipt/v1"
INNER_RECEIPT_SCHEMA = "spiritos-foundation-remediation-r1-production-proving-receipt/v1"
LIFECYCLE_CLAIM_CEILING = (
    "subordinate_clean_checkout_build_service_and_trusted_process_"
    "revocation_proof_only"
)
STATE_PREFIX = "spiritos-foundation-r1-state-"
LOOPBACK = "127.0.0.1"
SAFE_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
GIT_EXECUTABLE = Path("/usr/bin/git")
SYSTEMD_RUN_EXECUTABLE = Path("/usr/bin/systemd-run")
SYSTEMCTL_EXECUTABLE = Path("/usr/bin/systemctl")
CGROUP_ROOT = Path("/sys/fs/cgroup")
R1_GATE_INCREMENT = "1.3"
R1_CODER_ALIAS = "coder"
R1_CODER_MODEL = "qwen2.5-coder:14b"
R1_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
R1_PRIMARY_MODEL_ALIAS = "foundation-r1-intentional-primary-failure"
R1_FAILED_PROVIDER = "model-router"
R1_FALLBACK_PROVIDER = "ollama"
R1_FALLBACK_MODEL = f"ollama_chat/{R1_CODER_MODEL}"
R1_REPOSITORY_ID = "SpiritOS"
HEALTH_REQUEST_TIMEOUT_SECONDS = 5
R1_NODE_OPTIONS = "--max-old-space-size=4096 --max-semi-space-size=256"
PROVING_FIXTURE_RELATIVE = Path(
    "tests/ui-agent-trials/fixtures/dummy-product-site"
)
APPROVAL_SECRET_PATH = Path("/home/source/.config/spiritos/secrets/approval-authority.env")
GIT_OID_RE = re.compile(r"^[0-9a-f]{40}$")
WORKTREE_ID_RE = re.compile(r"^[0-9a-f]{24}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
IDENTITY_RE = re.compile(r"^[A-Za-z0-9._/-]{1,240}$")
PROPOSAL_RE = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
INNER_IDENTITY_FLAGS = {
    "--expected-source-head",
    "--expected-repository-id",
    "--expected-worktree-id",
}
FORBIDDEN_KEY_FRAGMENTS = {
    "authorization",
    "cookie",
    "credential",
    "csrf",
    "password",
    "raw_diff",
    "raw_http",
    "request_body",
    "response_body",
    "secret",
    "session_id",
    "session_token",
    "token",
}
TERMINAL_APPROVAL_STATES = {
    "cancelled",
    "consumed",
    "expired",
    "invalidated",
    "rejected",
    "superseded",
}


class LifecycleError(RuntimeError):
    """One fail-closed lifecycle invariant was not met."""

    def __init__(self, reason_code: str):
        self.reason_code = reason_code
        super().__init__(reason_code)


def _fail(reason_code: str) -> None:
    raise LifecycleError(reason_code)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise LifecycleError("lifecycle_noncanonical_json") from error


def _sha256_json(value: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical_json(value)).hexdigest()}"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while chunk := handle.read(1024 * 1024):
                digest.update(chunk)
    except OSError as error:
        raise LifecycleError("lifecycle_file_hash_failed") from error
    return digest.hexdigest()


def _hash_directory(root: Path) -> tuple[str, int]:
    """Hash names, kinds, sizes, and content without following links."""

    if not root.is_dir() or root.is_symlink():
        _fail("lifecycle_hash_directory_invalid")
    digest = hashlib.sha256()
    count = 0
    try:
        entries = sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix())
        for entry in entries:
            relative = entry.relative_to(root).as_posix()
            if entry.is_symlink():
                kind = "link"
                raw_target = os.readlink(entry)
                try:
                    resolved_target = (entry.parent / raw_target).resolve()
                except (OSError, RuntimeError) as error:
                    raise LifecycleError(
                        "lifecycle_directory_symlink_target_invalid"
                    ) from error
                try:
                    resolved_target.relative_to(root.resolve())
                except ValueError:
                    _fail("lifecycle_directory_symlink_escapes_root")
                if not resolved_target.exists():
                    _fail("lifecycle_directory_symlink_target_missing")
                material = raw_target.encode("utf-8")
                size = len(material)
                content_hash = hashlib.sha256(material).hexdigest()
            elif entry.is_file():
                kind = "file"
                size = entry.stat().st_size
                content_hash = _sha256_file(entry)
            elif entry.is_dir():
                kind = "directory"
                size = 0
                content_hash = ""
            else:
                _fail("lifecycle_directory_entry_unsupported")
            digest.update(f"{relative}\0{kind}\0{size}\0{content_hash}\n".encode("utf-8"))
            count += 1
    except OSError as error:
        raise LifecycleError("lifecycle_directory_hash_failed") from error
    return digest.hexdigest(), count


def _mapping(value: Any, reason: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail(reason)
    return dict(value)


def _text(value: Any, reason: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(reason)
    return value


def _new_output_path(raw: Path, *, reason: str) -> Path:
    expanded = raw.expanduser()
    if expanded.is_symlink():
        _fail(reason)
    path = expanded.resolve()
    if path.suffix.lower() != ".json" or path.exists() or path.is_symlink():
        _fail(reason)
    if not path.parent.is_dir():
        _fail(f"{reason}_parent_missing")
    return path


def _outside_worktree(path: Path, worktree: Path, *, reason: str) -> None:
    try:
        path.relative_to(worktree)
    except ValueError:
        return
    _fail(reason)


@dataclasses.dataclass(frozen=True, slots=True)
class LifecycleConfig:
    proof_worktree: Path
    expected_source_head: str
    expected_repository_id: str
    expected_worktree_id: str
    expected_branch: str
    proposal_id: str
    task_file: Path
    inner_receipt: Path
    output: Path
    python_executable: Path
    python_executable_resolved: Path
    expected_python_executable_sha256: str
    expected_python_environment_sha256: str
    node_executable: Path
    node_executable_resolved: Path
    expected_node_executable_sha256: str
    node_modules_root: Path
    expected_node_modules_sha256: str
    tls_certificate: Path
    tls_private_key: Path
    primary_model_alias: str
    fallback_model_alias: str
    expected_failed_provider: str
    expected_failed_model: str
    expected_fallback_provider: str
    expected_fallback_model: str
    source_port: int
    next_port: int
    https_port: int
    startup_timeout_seconds: float
    inner_http_timeout_seconds: float
    inner_process_timeout_seconds: float
    operator_e2e_secret_source: str = "generated"


@dataclasses.dataclass(frozen=True, slots=True)
class WorktreeIdentity:
    root: Path
    repository_id: str
    branch: str
    source_head: str
    source_tree: str
    source_proxy_tree: str
    git_common_dir_sha256: str
    initial_ignored_status_sha256: str


@dataclasses.dataclass(slots=True)
class ServiceProcess:
    name: str
    process: subprocess.Popen[bytes]
    command_sha256: str
    port: int
    stdout_path: Path
    stderr_path: Path
    started_at: str
    scope_unit: str
    cgroup_path: Path
    health_response_sha256: str = ""
    stdout_sha256: str = ""
    stderr_sha256: str = ""
    stopped: bool = False
    port_closed: bool = False
    process_absent: bool = False
    process_group_absent: bool = False
    process_session_absent: bool = False
    descendant_processes_absent: bool = False
    cgroup_empty: bool = False
    loopback_bound: bool = False
    listener_identity_sha256: str = ""


def _command_environment() -> dict[str, str]:
    inherited = os.environ
    environment = {
        key: inherited[key]
        for key in (
            "DBUS_SESSION_BUS_ADDRESS",
            "HOME",
            "LANG",
            "LC_ALL",
            "LOGNAME",
            "SHELL",
            "TZ",
            "USER",
            "XDG_RUNTIME_DIR",
        )
        if inherited.get(key)
    }
    environment["PATH"] = SAFE_PATH
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _run_capture(
    command: Sequence[str],
    *,
    cwd: Path,
    reason: str,
    environment: Mapping[str, str] | None = None,
) -> str:
    try:
        result = subprocess.run(
            list(command),
            cwd=cwd,
            env=dict(environment or _command_environment()),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise LifecycleError(reason) from error
    if result.returncode != 0:
        _fail(reason)
    try:
        return result.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise LifecycleError(reason) from error


def _git(root: Path, *args: str, reason: str = "lifecycle_git_command_failed") -> str:
    environment = _command_environment()
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return _run_capture(
        [
            str(GIT_EXECUTABLE),
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.untrackedCache=false",
            "-c",
            f"core.hooksPath={os.devnull}",
            "-C",
            str(root),
            *args,
        ],
        cwd=root,
        reason=reason,
        environment=environment,
    )


def _derive_repository_id(root: Path) -> tuple[str, Path]:
    raw = Path(_git(root, "rev-parse", "--git-common-dir"))
    common = (raw if raw.is_absolute() else root / raw).resolve()
    repository_id = common.parent.name
    if not repository_id:
        _fail("lifecycle_repository_identity_missing")
    return repository_id, common


def _verify_clean_linked_worktree(config: LifecycleConfig) -> WorktreeIdentity:
    if (
        not GIT_EXECUTABLE.is_file()
        or GIT_EXECUTABLE.is_symlink()
        or not os.access(GIT_EXECUTABLE, os.X_OK)
    ):
        _fail("lifecycle_git_executable_invalid")
    root = config.proof_worktree
    absolute = Path(os.path.abspath(root))
    resolved = Path(os.path.realpath(root))
    if absolute != resolved or not root.is_dir():
        _fail("lifecycle_proof_worktree_not_canonical")
    if not (root / ".git").is_file():
        _fail("lifecycle_linked_worktree_required")
    top = Path(_git(root, "rev-parse", "--show-toplevel")).resolve()
    if top != root:
        _fail("lifecycle_proof_worktree_top_level_mismatch")
    registered_output = _git(root, "worktree", "list", "--porcelain")
    registered = {
        Path(line.removeprefix("worktree ")).resolve()
        for line in registered_output.splitlines()
        if line.startswith("worktree ")
    }
    if root not in registered:
        _fail("lifecycle_proof_worktree_unregistered")
    head = _git(root, "rev-parse", "--verify", "HEAD").lower()
    if head != config.expected_source_head:
        _fail("lifecycle_source_head_mismatch")
    branch = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    if branch != config.expected_branch:
        _fail("lifecycle_branch_mismatch")
    repository_id, common = _derive_repository_id(root)
    if repository_id != config.expected_repository_id:
        _fail("lifecycle_repository_identity_mismatch")
    status = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if status:
        _fail("lifecycle_proof_worktree_not_clean")
    index_flags = _git(root, "ls-files", "-v")
    if any(
        line and (line[0].islower() or line.startswith("S "))
        for line in index_flags.splitlines()
    ):
        _fail("lifecycle_index_visibility_flag_forbidden")
    for relative in (".next", ".spirit-backups", "node_modules"):
        candidate = root / relative
        if candidate.exists() or candidate.is_symlink():
            _fail(f"lifecycle_preexisting_{relative.lstrip('.').replace('-', '_')}_forbidden")
    _git(
        root,
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--check",
        reason="lifecycle_initial_diff_check_failed",
    )
    ignored = _git(
        root,
        "status",
        "--porcelain=v1",
        "--ignored=matching",
        "--untracked-files=all",
    )
    if ignored:
        _fail("lifecycle_proof_worktree_contains_ignored_files")
    return WorktreeIdentity(
        root=root,
        repository_id=repository_id,
        branch=branch,
        source_head=head,
        source_tree=_git(root, "rev-parse", "HEAD^{tree}"),
        source_proxy_tree=_git(root, "rev-parse", "HEAD:source_proxy"),
        git_common_dir_sha256=_sha256_text(str(common)),
        initial_ignored_status_sha256=_sha256_text(ignored),
    )


def _allocate_port(requested: int, *, excluded: set[int]) -> int:
    if requested and requested in excluded:
        _fail("lifecycle_service_ports_not_distinct")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as handle:
            handle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
            handle.bind((LOOPBACK, requested))
            selected = int(handle.getsockname()[1])
    except OSError as error:
        raise LifecycleError("lifecycle_service_port_unavailable") from error
    if selected in excluded:
        _fail("lifecycle_service_ports_not_distinct")
    return selected


def _port_is_closed(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as handle:
            handle.settimeout(0.25)
            return handle.connect_ex((LOOPBACK, port)) != 0
    except OSError:
        return True


def _wait_port_closed(port: int, *, timeout_seconds: float = 15) -> bool:
    deadline = time.monotonic() + timeout_seconds
    consecutive = 0
    while time.monotonic() < deadline:
        if _port_is_closed(port):
            consecutive += 1
            if consecutive >= 3:
                return True
        else:
            consecutive = 0
        time.sleep(0.15)
    return False


def _prepare_dependency_link(config: LifecycleConfig) -> Path:
    target = config.node_modules_root
    if not target.is_dir() or not (target / "next" / "dist" / "bin" / "next").is_file():
        _fail("lifecycle_node_modules_invalid")
    link = config.proof_worktree / "node_modules"
    if link.exists() or link.is_symlink():
        _fail("lifecycle_node_modules_preexisting")
    try:
        link.symlink_to(target, target_is_directory=True)
        if not link.is_symlink() or link.resolve() != target.resolve():
            _fail("lifecycle_node_modules_link_mismatch")
    except (OSError, LifecycleError) as error:
        try:
            if link.is_symlink():
                link.unlink()
        except OSError:
            pass
        if isinstance(error, LifecycleError):
            raise
        raise LifecycleError("lifecycle_node_modules_link_failed") from error
    return link


def _mkdir_private(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path, 0o700)
    if path.stat().st_mode & 0o777 != 0o700:
        _fail("lifecycle_private_directory_mode_invalid")


def _new_state_root() -> Path:
    root = Path(tempfile.mkdtemp(prefix=STATE_PREFIX)).resolve()
    try:
        os.chmod(root, 0o700)
        if root.stat().st_mode & 0o777 != 0o700:
            _fail("lifecycle_state_root_mode_invalid")
        (root / ".foundation-r1-owned").write_text(
            REMEDIATION_ID + "\n",
            encoding="utf-8",
        )
        for relative in (
            "approval",
            "audit",
            "data",
            "fip0-receipts",
        "logs",
        "operator",
        "tmp",
        ):
            _mkdir_private(root / relative)
    except Exception:
        shutil.rmtree(root, ignore_errors=True)
        raise
    return root


def _runtime_environment(
    config: LifecycleConfig,
    *,
    state_root: Path,
    source_port: int,
    next_port: int,
    https_port: int,
    operator_secret: str,
) -> dict[str, str]:
    source_origin = f"http://{LOOPBACK}:{source_port}"
    next_origin = f"https://{LOOPBACK}:{https_port}"
    gate_path = state_root / "gate.json"
    gate_path.write_text(
        json.dumps(
            {
                "status": "APPROVED_INCREMENT",
                "approved_increment": R1_GATE_INCREMENT,
                "approval_token": f"foundation-r1-{secrets.token_hex(16)}",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    os.chmod(gate_path, 0o600)
    inherited = os.environ
    environment = {
        key: inherited[key]
        for key in (
            "DBUS_SESSION_BUS_ADDRESS",
            "HOME",
            "LANG",
            "LC_ALL",
            "LOGNAME",
            "SHELL",
            "TZ",
            "USER",
            "XDG_RUNTIME_DIR",
        )
        if inherited.get(key)
    }
    environment["PATH"] = SAFE_PATH
    # Campaign 3 lane transports are explicitly allow-listed. Credentials are
    # deliberately absent; operator material remains scoped to its real owner.
    for name in (
        "SPIRIT_MACMINI_REPO_PATH", "SPIRIT_MACMINI_TAILSCALE_HOST",
        "SPIRIT_MACMINI_HOSTKEY_ALIAS", "SPIRIT_MACMINI_SSH_ALIAS",
        "SPIRIT_MACMINI_GATEWAY_SSH_ALIAS", "SOURCE_PROXY_SCOUT_RESEARCH_URL",
        "OBSIDIAN_VAULT_PATH", "OBSIDIAN_MAX_NOTE_AGE_SECONDS",
    ):
        if inherited.get(name):
            environment[name] = inherited[name]
    environment.update(
        {
            "HOSTNAME": LOOPBACK,
            "NEXT_TELEMETRY_DISABLED": "1",
            "NODE_ENV": "production",
            "NO_PROXY": f"{LOOPBACK},localhost",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(config.proof_worktree),
            "SOURCE_PROXY_APPROVED_ACTION_AUDIT_LOG": str(state_root / "audit" / "approved.jsonl"),
            "SOURCE_PROXY_BLOCKED_ACTION_AUDIT_LOG": str(state_root / "audit" / "blocked.jsonl"),
            "SOURCE_PROXY_CARTOGRAPHER_GIT_APPROVAL_LOG": str(
                state_root / "audit" / "cartographer-git.jsonl"
            ),
            "SOURCE_PROXY_CODER_MODEL_ALIAS": R1_CODER_ALIAS,
            "SOURCE_PROXY_CODER_OLLAMA_MODEL": R1_CODER_MODEL,
            "SOURCE_PROXY_CODER_SYNC_DEADLINE_SEC": "240",
            "SOURCE_PROXY_CODER_TIMEOUT_SECONDS": "180",
            "SOURCE_PROXY_DATABASE_URL": "disabled",
            "SOURCE_PROXY_DATA_DIR": str(state_root / "data"),
            "SOURCE_PROXY_DUMMY_PRODUCT_SITE_DIRECT_OLLAMA": "0",
            "SOURCE_PROXY_DUMMY_PRODUCT_SITE_MODEL_TIMEOUT_SECONDS": "180",
            "SOURCE_PROXY_FIP0_RECEIPT_DIR": str(state_root / "fip0-receipts"),
            "SOURCE_PROXY_GATE_ALLOWED_ACTIONS": "model_call,apply",
            "SOURCE_PROXY_GATE_INCREMENT": R1_GATE_INCREMENT,
            "SOURCE_PROXY_GATE_STATE_PATH": str(gate_path),
            "SOURCE_PROXY_HOST": LOOPBACK,
            "SOURCE_PROXY_LONG_RUNNING_TASKS_DB": str(state_root / "tasks.sqlite3"),
            "SOURCE_PROXY_OLLAMA_BASE_URL": R1_OLLAMA_BASE_URL,
            "SOURCE_PROXY_ORIGIN": source_origin,
            "SOURCE_PROXY_PORT": str(source_port),
            "SOURCE_PROXY_PROJECT_ROOTS": str(config.proof_worktree),
            "SOURCE_PROXY_REQUEST_TIMEOUT_SECONDS": "180",
            "SOURCE_PROXY_TRIAL_DIRECT_OLLAMA_PROOF": "0",
            "SPIRITOS_FOUNDATION_R1_NEXT_ORIGIN": next_origin,
            "SPIRITOS_FOUNDATION_R1_SOURCE_ORIGIN": source_origin,
            "SPIRIT_CODING_USE_PROXY": "true",
            "SPIRIT_PROJECT_PATH": str(config.proof_worktree),
            "SPIRITOS_APPROVAL_REPOSITORY": config.expected_repository_id,
            "SPIRITOS_APPROVAL_ROOT": str(config.proof_worktree),
            "SPIRITOS_APPROVAL_STATE_DIR": str(state_root / "approval"),
            "SPIRITOS_CODING_FALLBACK_MODEL_ALIAS": config.fallback_model_alias,
            "SPIRITOS_CODING_PRIMARY_MODEL_ALIAS": config.primary_model_alias,
            "SPIRITOS_E2E_FRONTEND_ORIGIN": next_origin,
            "SPIRITOS_OPERATOR_ALLOWED_ORIGINS": next_origin,
            "SPIRITOS_OPERATOR_CREDENTIAL": operator_secret,
            "SPIRITOS_OPERATOR_E2E_MODE": "true",
            "SPIRITOS_OPERATOR_E2E_SECRET": operator_secret,
            "SPIRITOS_OPERATOR_E2E_SECRET_PATH": str(state_root / "operator" / "unused-secret.env"),
            "SPIRITOS_OPERATOR_E2E_STATE_PATH": str(state_root / "operator" / "sessions.json"),
            "SSL_CERT_FILE": str(config.tls_certificate),
            "TMPDIR": str(state_root / "tmp"),
        }
    )
    return environment


def _build_environment(runtime_environment: Mapping[str, str]) -> dict[str, str]:
    """Do not make the short-lived operator credential a build-time input."""

    output = dict(runtime_environment)
    for key in (
        "SPIRITOS_OPERATOR_CREDENTIAL",
        "SPIRITOS_OPERATOR_E2E_SECRET",
    ):
        output.pop(key, None)
    output["NODE_OPTIONS"] = R1_NODE_OPTIONS
    return output


def _scoped_runtime_environment(
    runtime_environment: Mapping[str, str],
    *,
    operator_credential: bool,
    operator_e2e_secret: bool,
) -> dict[str, str]:
    """Give each child only the short-lived operator material it needs."""

    output = dict(runtime_environment)
    if not operator_credential:
        output.pop("SPIRITOS_OPERATOR_CREDENTIAL", None)
    if not operator_e2e_secret:
        output.pop("SPIRITOS_OPERATOR_E2E_SECRET", None)
    return output


def _operator_e2e_secret(config: LifecycleConfig) -> str:
    """Resolve an operator secret only for the explicitly requested isolated run."""
    if config.operator_e2e_secret_source == "generated":
        return secrets.token_urlsafe(48)
    if config.operator_e2e_secret_source != "canonical":
        _fail("lifecycle_operator_secret_source_invalid")
    sys.path.insert(0, str(config.proof_worktree))
    try:
        loader = getattr(importlib.import_module("source_proxy.approval.operator_session"), "_secret")
        value = loader()
    except Exception as error:
        raise LifecycleError("lifecycle_operator_secret_unavailable") from error
    if len(value) < 8 or "\x00" in value:
        _fail("lifecycle_operator_secret_invalid")
    return value


def _approval_secret_baseline() -> tuple[str, tuple[int, int, int, int]]:
    """Require the pre-existing shared signer to remain read-only for this run."""

    path = APPROVAL_SECRET_PATH
    if not path.is_file() or path.is_symlink():
        _fail("lifecycle_approval_signing_key_missing")
    try:
        stat = path.stat()
        if stat.st_mode & 0o777 != 0o600:
            _fail("lifecycle_approval_signing_key_mode_invalid")
        raw = path.read_bytes()
    except OSError as error:
        raise LifecycleError("lifecycle_approval_signing_key_unreadable") from error
    if not raw.startswith(b"SPIRITOS_APPROVAL_HMAC_KEY=") or len(raw) < 48:
        _fail("lifecycle_approval_signing_key_invalid")
    return (
        hashlib.sha256(raw).hexdigest(),
        (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns),
    )


def _verify_approval_secret_unchanged(
    baseline: tuple[str, tuple[int, int, int, int]],
) -> None:
    if _approval_secret_baseline() != baseline:
        _fail("lifecycle_approval_signing_key_changed")


def _verify_external_debug_writer_retired(root: Path) -> None:
    path = root / "source_proxy" / "api" / "decision.py"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise LifecycleError("lifecycle_decision_source_unreadable") from error
    forbidden = (
        "debug-9460b9.log",
        "_DEBUG_LOG_PATH",
        "/home/source/SpiritOS/.cursor",
    )
    if any(value in text for value in forbidden):
        _fail("lifecycle_external_debug_writer_not_retired")


def _verify_loopback_tls_proxy_contract(root: Path) -> None:
    path = root / "scripts" / "spiritflix-prod-https-proxy.mjs"
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise LifecycleError("lifecycle_tls_proxy_source_unreadable") from error
    if (
        "server.listen(port, host" not in text
        or 'args.get("--host")' not in text
        or '"127.0.0.1"' not in text
    ):
        _fail("lifecycle_tls_proxy_loopback_contract_missing")


def _approval_preflight(
    config: LifecycleConfig,
    *,
    environment: Mapping[str, str],
    state_root: Path,
) -> dict[str, Any]:
    _verify_python_executable(config)
    script = config.proof_worktree / "scripts" / "approval-authority.py"
    stdout_path = state_root / "logs" / "approval-preflight.stdout.log"
    execution = _run_logged(
        [str(config.python_executable), str(script), "preflight"],
        cwd=config.proof_worktree,
        environment=environment,
        stdout_path=stdout_path,
        stderr_path=state_root / "logs" / "approval-preflight.stderr.log",
        timeout_seconds=60,
        reason="lifecycle_approval_preflight_failed",
    )
    try:
        payload = json.loads(stdout_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LifecycleError("lifecycle_approval_preflight_unreadable") from error
    preflight = _mapping(payload, "lifecycle_approval_preflight_invalid")
    if (
        preflight.get("schema") != "spiritos-approval-authority-preflight/v3"
        or preflight.get("ready") is not True
        or preflight.get("secretExposed") is not False
        or preflight.get("storeType") != "sqlite"
        or preflight.get("authorityId") != "spiritos-approval-authority"
        or preflight.get("issuerId")
        != "spiritos-approval-authority/foundation-remediation-r1"
        or preflight.get("sourceHead") != config.expected_source_head
        or preflight.get("branch") != config.expected_branch
        or preflight.get("stateNamespace") != config.expected_worktree_id
        or preflight.get("registeredRoots") != [str(config.proof_worktree)]
    ):
        _fail("lifecycle_approval_preflight_identity_mismatch")
    consumers = preflight.get("consumers")
    operations = preflight.get("operations")
    if (
        not isinstance(consumers, list)
        or not {"coding-executor:coder", "cartographer-transfer-consumer"}.issubset(
            set(consumers)
        )
        or not isinstance(operations, list)
        or not {"coding_execution", "cartographer_selection_transfer"}.issubset(
            set(operations)
        )
    ):
        _fail("lifecycle_approval_preflight_capability_mismatch")
    _, common = _derive_repository_id(config.proof_worktree)
    try:
        reported_common = Path(str(preflight.get("commonGitDir") or "")).resolve()
    except OSError as error:
        raise LifecycleError("lifecycle_approval_preflight_identity_invalid") from error
    if reported_common != common:
        _fail("lifecycle_approval_preflight_identity_mismatch")
    return {
        **execution,
        "ready": True,
        "source_head": config.expected_source_head,
        "repository_id": config.expected_repository_id,
        "worktree_id": config.expected_worktree_id,
        "registered_root_exact": True,
        "shared_signing_key_exposed": False,
    }


def _open_private_log(path: Path):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    return os.fdopen(descriptor, "wb")


def _systemd_environment(environment: Mapping[str, str]) -> dict[str, str]:
    output = {
        key: environment[key]
        for key in (
            "DBUS_SESSION_BUS_ADDRESS",
            "HOME",
            "LANG",
            "LC_ALL",
            "LOGNAME",
            "USER",
            "XDG_RUNTIME_DIR",
        )
        if environment.get(key)
    }
    output["PATH"] = SAFE_PATH
    return output


def _verify_cgroup_runtime(environment: Mapping[str, str]) -> dict[str, Any]:
    if (
        not SYSTEMD_RUN_EXECUTABLE.is_file()
        or not SYSTEMCTL_EXECUTABLE.is_file()
        or not (CGROUP_ROOT / "cgroup.controllers").is_file()
    ):
        _fail("lifecycle_cgroup_runtime_unavailable")
    try:
        manager = subprocess.run(
            [
                str(SYSTEMCTL_EXECUTABLE),
                "--user",
                "show",
                "--property=Version",
                "--value",
                "--no-pager",
            ],
            env=_systemd_environment(environment),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise LifecycleError("lifecycle_cgroup_runtime_unavailable") from error
    if manager.returncode != 0 or not manager.stdout.strip():
        _fail("lifecycle_cgroup_runtime_unavailable")
    return {
        "kind": "systemd_user_scope_cgroup_v2",
        "systemd_run_executable_sha256": _sha256_file(SYSTEMD_RUN_EXECUTABLE),
        "systemctl_executable_sha256": _sha256_file(SYSTEMCTL_EXECUTABLE),
        "kernel_membership_enforced": True,
        "threat_model": "trusted_prehashed_executables_and_code",
        "same_uid_cgroup_migration_resistance_claimed": False,
    }


def _new_scope_unit(label: str) -> str:
    safe_label = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")[:28]
    if not safe_label:
        safe_label = "process"
    return f"spiritos-foundation-r1-{safe_label}-{secrets.token_hex(8)}.scope"


def _scope_command(unit: str, command: Sequence[str], *, cwd: Path) -> list[str]:
    del cwd
    return [
        str(SYSTEMD_RUN_EXECUTABLE),
        "--user",
        "--scope",
        "--quiet",
        "--collect",
        f"--unit={unit}",
        "--",
        *command,
    ]


def _scope_control_group(
    unit: str,
    *,
    environment: Mapping[str, str],
) -> Path | None:
    try:
        result = subprocess.run(
            [
                str(SYSTEMCTL_EXECUTABLE),
                "--user",
                "show",
                unit,
                "--property=ControlGroup",
                "--value",
                "--no-pager",
            ],
            env=_systemd_environment(environment),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise LifecycleError("lifecycle_cgroup_identity_unavailable") from error
    if result.returncode != 0:
        return None
    try:
        control_group = result.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise LifecycleError("lifecycle_cgroup_identity_unavailable") from error
    if not control_group:
        return None
    if not control_group.startswith("/") or "\x00" in control_group:
        _fail("lifecycle_cgroup_identity_invalid")
    path = (CGROUP_ROOT / control_group.lstrip("/")).resolve()
    try:
        path.relative_to(CGROUP_ROOT.resolve())
    except ValueError:
        _fail("lifecycle_cgroup_identity_invalid")
    return path


def _wait_scope_control_group(
    unit: str,
    process: subprocess.Popen[bytes],
    *,
    environment: Mapping[str, str],
    timeout_seconds: float = 10,
) -> Path:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        path = _scope_control_group(unit, environment=environment)
        if path is not None and path.is_dir():
            return path
        if process.poll() is not None:
            break
        time.sleep(0.05)
    _fail("lifecycle_cgroup_identity_unavailable")


def _cgroup_process_ids(path: Path) -> set[int]:
    if not path.exists():
        return set()
    try:
        membership_files = [path / "cgroup.procs", *path.rglob("cgroup.procs")]
    except FileNotFoundError:
        membership_files = [path / "cgroup.procs"]
    except (OSError, UnicodeError, ValueError) as error:
        raise LifecycleError("lifecycle_cgroup_membership_unreadable") from error
    process_ids: set[int] = set()
    for membership_file in membership_files:
        try:
            if not membership_file.is_file():
                continue
            raw = membership_file.read_text(encoding="ascii")
            process_ids.update(int(value) for value in raw.split())
        except FileNotFoundError:
            continue
        except (OSError, UnicodeError, ValueError) as error:
            raise LifecycleError("lifecycle_cgroup_membership_unreadable") from error
    return process_ids


def _cgroup_is_populated(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        event_files = [path / "cgroup.events", *path.rglob("cgroup.events")]
    except FileNotFoundError:
        event_files = [path / "cgroup.events"]
    except OSError as error:
        raise LifecycleError("lifecycle_cgroup_events_unreadable") from error
    observed = False
    for event_file in event_files:
        try:
            if not event_file.is_file():
                continue
            values = {
                key: value
                for key, value in (
                    line.split(maxsplit=1)
                    for line in event_file.read_text(encoding="ascii").splitlines()
                    if line.strip()
                )
            }
        except FileNotFoundError:
            continue
        except (OSError, UnicodeError, ValueError) as error:
            raise LifecycleError("lifecycle_cgroup_events_unreadable") from error
        if values.get("populated") not in {"0", "1"}:
            _fail("lifecycle_cgroup_events_invalid")
        observed = True
        if values["populated"] == "1":
            return True
    if path.exists() and not observed:
        _fail("lifecycle_cgroup_events_missing")
    return False


def _wait_cgroup_empty(path: Path, *, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    consecutive_empty = 0
    while time.monotonic() < deadline:
        if _cgroup_process_ids(path) or _cgroup_is_populated(path):
            consecutive_empty = 0
        else:
            consecutive_empty += 1
            if consecutive_empty >= 3:
                return True
        time.sleep(0.1)
    return False


def _systemctl_scope_action(
    unit: str,
    action: str,
    *,
    environment: Mapping[str, str],
) -> None:
    command = [str(SYSTEMCTL_EXECUTABLE), "--user", action]
    if action == "kill":
        command.extend(["--kill-whom=all", "--signal=SIGKILL"])
    command.append(unit)
    try:
        subprocess.run(
            command,
            env=_systemd_environment(environment),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
    except subprocess.TimeoutExpired:
        if action == "kill":
            return
        _systemctl_scope_action(unit, "kill", environment=environment)
    except OSError as error:
        raise LifecycleError("lifecycle_cgroup_control_failed") from error


def _stop_scope(
    unit: str,
    cgroup_path: Path,
    *,
    environment: Mapping[str, str],
) -> bool:
    _systemctl_scope_action(unit, "stop", environment=environment)
    if _wait_cgroup_empty(cgroup_path, timeout_seconds=10):
        return True
    _systemctl_scope_action(unit, "kill", environment=environment)
    return _wait_cgroup_empty(cgroup_path, timeout_seconds=10)


def _process_group_exists(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _session_process_ids(session_id: int) -> set[int]:
    process_ids: set[int] = set()
    try:
        candidates = Path("/proc").iterdir()
    except OSError as error:
        raise LifecycleError("lifecycle_process_session_scan_failed") from error
    for candidate in candidates:
        if not candidate.name.isdigit():
            continue
        try:
            raw = (candidate / "stat").read_text(encoding="ascii")
            fields = raw[raw.rfind(")") + 2 :].split()
            if len(fields) >= 4 and int(fields[3]) == session_id:
                process_ids.add(int(candidate.name))
        except (FileNotFoundError, ProcessLookupError):
            continue
        except (OSError, UnicodeError, ValueError) as error:
            raise LifecycleError("lifecycle_process_session_scan_failed") from error
    return process_ids


def _process_table() -> dict[int, tuple[int, int]]:
    """Return pid -> (parent pid, start time) from one coherent /proc scan."""

    processes: dict[int, tuple[int, int]] = {}
    try:
        candidates = Path("/proc").iterdir()
    except OSError as error:
        raise LifecycleError("lifecycle_process_descendant_scan_failed") from error
    for candidate in candidates:
        if not candidate.name.isdigit():
            continue
        try:
            raw = (candidate / "stat").read_text(encoding="ascii")
            fields = raw[raw.rfind(")") + 2 :].split()
            if len(fields) >= 20:
                processes[int(candidate.name)] = (int(fields[1]), int(fields[19]))
        except (FileNotFoundError, ProcessLookupError):
            continue
        except (OSError, UnicodeError, ValueError) as error:
            raise LifecycleError("lifecycle_process_descendant_scan_failed") from error
    return processes


def _descendant_process_identities(root_pid: int) -> dict[int, int]:
    processes = _process_table()
    tracked: dict[int, int] = {}
    frontier = {root_pid}
    root = processes.get(root_pid)
    if root is not None:
        tracked[root_pid] = root[1]
    while frontier:
        children = {
            process_id
            for process_id, (parent_id, _) in processes.items()
            if parent_id in frontier and process_id not in tracked
        }
        for process_id in children:
            tracked[process_id] = processes[process_id][1]
        frontier = children
    return tracked


def _process_identity_exists(process_id: int, start_time: int) -> bool:
    try:
        raw = Path(f"/proc/{process_id}/stat").read_text(encoding="ascii")
        fields = raw[raw.rfind(")") + 2 :].split()
        return len(fields) >= 20 and int(fields[19]) == start_time
    except (FileNotFoundError, ProcessLookupError):
        return False
    except (OSError, UnicodeError, ValueError) as error:
        raise LifecycleError("lifecycle_process_descendant_scan_failed") from error


def _signal_process_identities(
    identities: Mapping[int, int],
    signal_number: signal.Signals,
) -> None:
    for process_id, start_time in sorted(identities.items(), reverse=True):
        if not _process_identity_exists(process_id, start_time):
            continue
        try:
            os.kill(process_id, signal_number)
        except ProcessLookupError:
            pass


def _wait_process_identities_absent(
    identities: Mapping[int, int],
    *,
    timeout_seconds: float,
) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not any(
            _process_identity_exists(process_id, start_time)
            for process_id, start_time in identities.items()
        ):
            return True
        time.sleep(0.1)
    return not any(
        _process_identity_exists(process_id, start_time)
        for process_id, start_time in identities.items()
    )


def _wait_process_session_absent(session_id: int, *, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while _session_process_ids(session_id) and time.monotonic() < deadline:
        time.sleep(0.1)
    return not _session_process_ids(session_id)


def _signal_process_session(session_id: int, signal_number: signal.Signals) -> None:
    for process_id in sorted(_session_process_ids(session_id), reverse=True):
        try:
            os.kill(process_id, signal_number)
        except ProcessLookupError:
            pass


def _wait_process_group_absent(process_group_id: int, *, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while _process_group_exists(process_group_id) and time.monotonic() < deadline:
        time.sleep(0.1)
    return not _process_group_exists(process_group_id)


def _terminate_process_group(process: subprocess.Popen[bytes]) -> bool:
    tracked = _descendant_process_identities(process.pid)
    if _process_group_exists(process.pid) or _session_process_ids(process.pid):
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    _signal_process_session(process.pid, signal.SIGTERM)
    _signal_process_identities(tracked, signal.SIGTERM)
    # Capture a child created between the first /proc snapshot and the signals.
    tracked.update(_descendant_process_identities(process.pid))
    _signal_process_identities(tracked, signal.SIGTERM)
    if process.poll() is None:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
    if (
        _wait_process_group_absent(process.pid, timeout_seconds=10)
        and _wait_process_session_absent(process.pid, timeout_seconds=10)
        and _wait_process_identities_absent(tracked, timeout_seconds=10)
    ):
        return True
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    _signal_process_session(process.pid, signal.SIGKILL)
    _signal_process_identities(tracked, signal.SIGKILL)
    if process.poll() is None:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            return False
    return (
        _wait_process_group_absent(process.pid, timeout_seconds=10)
        and _wait_process_session_absent(process.pid, timeout_seconds=10)
        and _wait_process_identities_absent(tracked, timeout_seconds=10)
    )


def _run_logged(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: float,
    reason: str,
) -> dict[str, Any]:
    started = time.monotonic()
    process: subprocess.Popen[bytes] | None = None
    cgroup_path: Path | None = None
    scope_unit = _new_scope_unit(reason)
    try:
        with _open_private_log(stdout_path) as stdout, _open_private_log(stderr_path) as stderr:
            process = subprocess.Popen(
                _scope_command(scope_unit, command, cwd=cwd),
                cwd=cwd,
                env=dict(environment),
                # Next's webpack worker crashes under this host's systemd scope
                # when stdin is /dev/null. Keep a private pipe until exit instead.
                stdin=subprocess.PIPE,
                stdout=stdout,
                stderr=stderr,
                # systemd-run owns this short-lived scope. A second session
                # boundary causes Next's webpack worker to segfault on Dell.
            )
            try:
                cgroup_path = _wait_scope_control_group(
                    scope_unit,
                    process,
                    environment=environment,
                )
            except Exception:
                _systemctl_scope_action(
                    scope_unit,
                    "stop",
                    environment=environment,
                )
                _terminate_process_group(process)
                raise
            try:
                return_code = process.wait(timeout=timeout_seconds)
                if process.stdin is not None:
                    process.stdin.close()
            except subprocess.TimeoutExpired as error:
                scope_stopped = _stop_scope(
                    scope_unit,
                    cgroup_path,
                    environment=environment,
                )
                process_stopped = _terminate_process_group(process)
                if not scope_stopped or not process_stopped:
                    raise LifecycleError(f"{reason}_process_boundary_not_stopped") from error
                raise LifecycleError(reason) from error
    except OSError as error:
        raise LifecycleError(reason) from error
    if process is None or cgroup_path is None:
        _fail(reason)
    leaked_processes = bool(_cgroup_process_ids(cgroup_path)) or _cgroup_is_populated(
        cgroup_path
    )
    if not _stop_scope(scope_unit, cgroup_path, environment=environment):
        _fail(f"{reason}_process_boundary_not_stopped")
    if _process_group_exists(process.pid) or _session_process_ids(process.pid):
        if not _terminate_process_group(process):
            _fail(f"{reason}_process_group_not_stopped")
        _fail(f"{reason}_child_process_leak")
    if return_code != 0:
        _fail(reason)
    if leaked_processes:
        _fail(f"{reason}_child_process_leak")
    return {
        "command_sha256": _sha256_json(list(command)),
        "duration_ms": int((time.monotonic() - started) * 1000),
        "stdout_sha256": _sha256_file(stdout_path),
        "stderr_sha256": _sha256_file(stderr_path),
        "cgroup_unit_sha256": _sha256_text(scope_unit),
        "cgroup_path_sha256": _sha256_text(str(cgroup_path)),
        "cgroup_empty_after_command": True,
    }


def _build_next(
    config: LifecycleConfig,
    *,
    environment: Mapping[str, str],
    state_root: Path,
) -> dict[str, Any]:
    _verify_node_executable(config)
    next_root = config.proof_worktree / ".next"
    if next_root.exists() or next_root.is_symlink():
        _fail("lifecycle_next_build_preexisting")
    dependency_sha256, dependency_entry_count = _hash_directory(
        config.node_modules_root
    )
    if dependency_sha256 != config.expected_node_modules_sha256:
        _fail("lifecycle_node_modules_identity_mismatch")
    next_cli = config.node_modules_root / "next" / "dist" / "bin" / "next"
    build = _run_logged(
        [
            str(config.node_executable),
            str(config.node_modules_root / "next" / "dist" / "bin" / "next"),
            "build",
            "--webpack",
        ],
        cwd=config.proof_worktree,
        environment=_build_environment(environment),
        stdout_path=state_root / "logs" / "next-build.stdout.log",
        stderr_path=state_root / "logs" / "next-build.stderr.log",
        timeout_seconds=max(config.startup_timeout_seconds * 4, 600),
        reason="lifecycle_next_build_failed",
    )
    build_id_path = next_root / "BUILD_ID"
    if not build_id_path.is_file() or build_id_path.is_symlink():
        _fail("lifecycle_next_build_id_missing")
    build_id = build_id_path.read_text(encoding="utf-8").strip()
    if not build_id:
        _fail("lifecycle_next_build_id_invalid")
    directory_sha256, entry_count = _hash_directory(next_root)
    package_lock = config.proof_worktree / "package-lock.json"
    next_package = config.node_modules_root / "next" / "package.json"
    if not package_lock.is_file() or not next_package.is_file():
        _fail("lifecycle_next_dependency_identity_missing")
    return {
        **build,
        "build_id_sha256": _sha256_text(build_id),
        "build_directory_sha256": directory_sha256,
        "build_entry_count": entry_count,
        "package_lock_sha256": _sha256_file(package_lock),
        "next_package_sha256": _sha256_file(next_package),
        "next_cli_sha256": _sha256_file(next_cli),
        "node_modules_sha256": dependency_sha256,
        "node_modules_entry_count": dependency_entry_count,
        "node_modules_matched_expected_identity": True,
        "node_executable_sha256": _sha256_file(config.node_executable.resolve()),
        "node_runtime_matched_expected_identity": True,
    }


def _verify_python_executable(config: LifecycleConfig) -> None:
    try:
        resolved = config.python_executable.resolve(strict=True)
    except OSError as error:
        raise LifecycleError("lifecycle_python_executable_identity_mismatch") from error
    if (
        resolved != config.python_executable_resolved
        or _sha256_file(resolved) != config.expected_python_executable_sha256
    ):
        _fail("lifecycle_python_executable_identity_mismatch")


def _verify_node_executable(config: LifecycleConfig) -> None:
    try:
        resolved = config.node_executable.resolve(strict=True)
    except OSError as error:
        raise LifecycleError("lifecycle_node_executable_identity_mismatch") from error
    if (
        resolved != config.node_executable_resolved
        or _sha256_file(resolved) != config.expected_node_executable_sha256
    ):
        _fail("lifecycle_node_executable_identity_mismatch")


def _python_environment_sha256(config: LifecycleConfig) -> str:
    _verify_python_executable(config)
    output = _run_capture(
        [str(config.python_executable), "-m", "pip", "freeze", "--all"],
        cwd=config.proof_worktree,
        reason="lifecycle_python_environment_identity_failed",
    )
    return _sha256_text(output)


def _python_site_packages_identity(config: LifecycleConfig) -> tuple[str, int]:
    _verify_python_executable(config)
    output = _run_capture(
        [
            str(config.python_executable),
            "-I",
            "-c",
            "import sysconfig; print(sysconfig.get_paths()['purelib'])",
        ],
        cwd=config.proof_worktree,
        reason="lifecycle_python_site_packages_identity_failed",
    )
    site_packages = Path(output).resolve()
    venv_root = config.python_executable.parent.parent.resolve()
    try:
        site_packages.relative_to(venv_root)
    except ValueError:
        _fail("lifecycle_python_site_packages_outside_runtime")
    if not site_packages.is_dir() or site_packages.is_symlink():
        _fail("lifecycle_python_site_packages_invalid")
    identity, entry_count = _hash_directory(site_packages)
    if identity != config.expected_python_environment_sha256:
        _fail("lifecycle_python_environment_identity_mismatch")
    return identity, entry_count


def _launch_service(
    *,
    name: str,
    command: Sequence[str],
    config: LifecycleConfig,
    environment: Mapping[str, str],
    port: int,
    state_root: Path,
) -> ServiceProcess:
    _verify_python_executable(config)
    _verify_node_executable(config)
    if not _port_is_closed(port):
        _fail("lifecycle_service_port_not_isolated")
    stdout_path = state_root / "logs" / f"{name}.stdout.log"
    stderr_path = state_root / "logs" / f"{name}.stderr.log"
    scope_unit = _new_scope_unit(name)
    process: subprocess.Popen[bytes] | None = None
    try:
        with _open_private_log(stdout_path) as stdout, _open_private_log(stderr_path) as stderr:
            process = subprocess.Popen(
                _scope_command(
                    scope_unit,
                    command,
                    cwd=config.proof_worktree,
                ),
                cwd=config.proof_worktree,
                env=dict(environment),
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
            )
    except OSError as error:
        raise LifecycleError(f"lifecycle_{name}_start_failed") from error
    try:
        cgroup_path = _wait_scope_control_group(
            scope_unit,
            process,
            environment=environment,
        )
    except Exception:
        _systemctl_scope_action(scope_unit, "stop", environment=environment)
        _terminate_process_group(process)
        raise
    return ServiceProcess(
        name=name,
        process=process,
        command_sha256=_sha256_json(list(command)),
        port=port,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        started_at=_utc_now(),
        scope_unit=scope_unit,
        cgroup_path=cgroup_path,
    )


def _wait_for_json_health(
    service: ServiceProcess,
    *,
    path: str,
    timeout_seconds: float,
    scheme: str = "http",
    ca_file: Path | None = None,
) -> dict[str, Any]:
    handlers: list[Any] = [urllib.request.ProxyHandler({})]
    if scheme == "https":
        import ssl

        if ca_file is None:
            _fail("lifecycle_https_health_ca_missing")
        context = ssl.create_default_context(cafile=str(ca_file))
        # The supplied file is the exact pinned development leaf certificate,
        # not its private mkcert root. Permit that leaf to terminate the trusted
        # chain while retaining normal signature, validity, and hostname checks.
        context.verify_flags |= ssl.VERIFY_X509_PARTIAL_CHAIN
        handlers.append(urllib.request.HTTPSHandler(context=context))
    elif scheme != "http":
        _fail("lifecycle_health_scheme_invalid")
    opener = urllib.request.build_opener(*handlers)
    deadline = time.monotonic() + timeout_seconds
    url = f"{scheme}://{LOOPBACK}:{service.port}{path}"
    last_payload: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        if service.process.poll() is not None:
            _fail(f"lifecycle_{service.name}_exited_before_health")
        try:
            request = urllib.request.Request(
                url,
                headers={"Accept": "application/json", "Cache-Control": "no-store"},
                method="GET",
            )
            with opener.open(request, timeout=HEALTH_REQUEST_TIMEOUT_SECONDS) as response:
                raw = response.read(1024 * 1024 + 1)
                if len(raw) > 1024 * 1024 or not 200 <= int(response.status) < 300:
                    raise ValueError("health_invalid")
                decoded = json.loads(raw.decode("utf-8"))
                if not isinstance(decoded, dict):
                    raise ValueError("health_invalid")
                last_payload = decoded
                service.health_response_sha256 = hashlib.sha256(raw).hexdigest()
                break
        except (OSError, ValueError, UnicodeError, json.JSONDecodeError, urllib.error.URLError):
            time.sleep(0.2)
    if last_payload is None:
        _fail(f"lifecycle_{service.name}_health_timeout")
    return last_payload


def _require_process_cwd(service: ServiceProcess, expected: Path) -> None:
    process_ids = _cgroup_process_ids(service.cgroup_path)
    if not process_ids:
        _fail(f"lifecycle_{service.name}_cwd_unavailable")
    for process_id in process_ids:
        try:
            actual = Path(os.readlink(f"/proc/{process_id}/cwd")).resolve()
        except FileNotFoundError:
            continue
        except OSError as error:
            raise LifecycleError(f"lifecycle_{service.name}_cwd_unavailable") from error
        if actual != expected:
            _fail(f"lifecycle_{service.name}_cwd_mismatch")


def _require_loopback_listener(service: ServiceProcess) -> None:
    port_hex = f"{service.port:04X}"
    listeners: dict[str, str] = {}
    try:
        for table in (Path("/proc/net/tcp"), Path("/proc/net/tcp6")):
            for line in table.read_text(encoding="ascii").splitlines()[1:]:
                fields = line.split()
                if len(fields) < 10 or fields[3] != "0A":
                    continue
                address, raw_port = fields[1].rsplit(":", 1)
                if raw_port == port_hex:
                    listeners[fields[9]] = address
    except (OSError, UnicodeError, ValueError) as error:
        raise LifecycleError(f"lifecycle_{service.name}_listener_identity_unavailable") from error
    if not listeners or set(listeners.values()) != {"0100007F"}:
        _fail(f"lifecycle_{service.name}_not_loopback_only")
    owned_socket_inodes: set[str] = set()
    try:
        for process_id in _cgroup_process_ids(service.cgroup_path):
            fd_root = Path(f"/proc/{process_id}/fd")
            for descriptor in fd_root.iterdir():
                try:
                    target = os.readlink(descriptor)
                except FileNotFoundError:
                    continue
                if target.startswith("socket:[") and target.endswith("]"):
                    owned_socket_inodes.add(target[8:-1])
    except (OSError, UnicodeError) as error:
        raise LifecycleError(
            f"lifecycle_{service.name}_listener_owner_unavailable"
        ) from error
    if not set(listeners).issubset(owned_socket_inodes):
        _fail(f"lifecycle_{service.name}_listener_not_process_owned")
    service.loopback_bound = True
    service.listener_identity_sha256 = _sha256_json(sorted(listeners))


def _stop_service(
    service: ServiceProcess,
    *,
    environment: Mapping[str, str],
) -> None:
    process = service.process
    scope_stopped = _stop_scope(
        service.scope_unit,
        service.cgroup_path,
        environment=environment,
    )
    terminated = _terminate_process_group(process)
    service.stopped = process.poll() is not None
    service.process_absent = not Path(f"/proc/{process.pid}").exists()
    service.process_group_absent = not _process_group_exists(process.pid)
    service.process_session_absent = not _session_process_ids(process.pid)
    service.cgroup_empty = (
        not _cgroup_process_ids(service.cgroup_path)
        and not _cgroup_is_populated(service.cgroup_path)
    )
    service.descendant_processes_absent = scope_stopped and service.cgroup_empty
    service.port_closed = _wait_port_closed(service.port)
    service.stdout_sha256 = _sha256_file(service.stdout_path)
    service.stderr_sha256 = _sha256_file(service.stderr_path)
    if (
        not terminated
        or not scope_stopped
        or not service.stopped
        or not service.process_absent
        or not service.process_group_absent
        or not service.process_session_absent
        or not service.descendant_processes_absent
        or not service.cgroup_empty
        or not service.port_closed
    ):
        _fail(f"lifecycle_{service.name}_teardown_incomplete")


def _inner_supported_flags(config: LifecycleConfig) -> None:
    inner = config.proof_worktree / "scripts" / "run-foundation-remediation-r1-proving.py"
    if not inner.is_file() or inner.is_symlink():
        _fail("lifecycle_inner_client_missing")
    help_text = _run_capture(
        [str(config.python_executable), str(inner), "--help"],
        cwd=config.proof_worktree,
        reason="lifecycle_inner_client_contract_unreadable",
    )
    missing = [flag for flag in INNER_IDENTITY_FLAGS if flag not in help_text]
    if missing:
        _fail("lifecycle_inner_client_identity_contract_incomplete")


def _run_inner_client(
    config: LifecycleConfig,
    *,
    environment: Mapping[str, str],
    source_port: int,
    next_port: int,
    https_port: int,
    state_root: Path,
    receipt_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    _verify_python_executable(config)
    _inner_supported_flags(config)
    inner = config.proof_worktree / "scripts" / "run-foundation-remediation-r1-proving.py"
    command = [
        str(config.python_executable),
        str(inner),
        "--source-origin",
        f"http://{LOOPBACK}:{source_port}",
        "--next-origin",
        f"https://{LOOPBACK}:{https_port}",
        "--proposal-id",
        config.proposal_id,
        "--task-file",
        str(config.task_file),
        "--output",
        str(receipt_path),
        "--timeout-seconds",
        str(config.inner_http_timeout_seconds),
        "--expected-source-head",
        config.expected_source_head,
        "--expected-repository-id",
        config.expected_repository_id,
        "--expected-worktree-id",
        config.expected_worktree_id,
        "--expected-failed-provider",
        config.expected_failed_provider,
        "--expected-failed-model",
        config.expected_failed_model,
        "--expected-fallback-provider",
        config.expected_fallback_provider,
        "--expected-fallback-model",
        config.expected_fallback_model,
    ]
    execution = _run_logged(
        command,
        cwd=config.proof_worktree,
        environment=environment,
        stdout_path=state_root / "logs" / "inner-client.stdout.log",
        stderr_path=state_root / "logs" / "inner-client.stderr.log",
        timeout_seconds=config.inner_process_timeout_seconds,
        reason="lifecycle_inner_client_failed",
    )
    try:
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LifecycleError("lifecycle_inner_receipt_unreadable") from error
    _assert_sensitive_values_absent(
        _canonical_json(receipt),
        forbidden_values=[
            environment.get("SPIRITOS_OPERATOR_CREDENTIAL", ""),
            config.task_file.read_text(encoding="utf-8").strip(),
        ],
    )
    validated = _validate_inner_receipt(
        receipt,
        config,
        source_port=source_port,
        next_port=next_port,
        https_port=https_port,
    )
    execution["client_script_sha256"] = _sha256_file(inner)
    execution["receipt_sha256"] = validated["receipt_sha256"]
    return validated, execution, receipt


def _validate_inner_receipt(
    value: Any,
    config: LifecycleConfig,
    *,
    source_port: int,
    next_port: int,
    https_port: int,
) -> dict[str, Any]:
    receipt = _mapping(value, "lifecycle_inner_receipt_invalid")
    unsigned = dict(receipt)
    recorded = unsigned.pop("receipt_sha256", None)
    if recorded != _sha256_json(unsigned):
        _fail("lifecycle_inner_receipt_hash_mismatch")
    expected = {
        "schema_version": INNER_RECEIPT_SCHEMA,
        "receipt_type": "foundation_r1_black_box_production_proving",
        "remediation_id": REMEDIATION_ID,
        "run_mode": "production_http",
        "source_commit": config.expected_source_head,
        "terminal_proof_eligible": True,
        "claim_ceiling": "recovered_via_declared_fallback_only",
        "failures": [],
    }
    for key, expected_value in expected.items():
        if receipt.get(key) != expected_value:
            _fail(f"lifecycle_inner_receipt_{key}_mismatch")
    repository = _mapping(receipt.get("repository_identity"), "lifecycle_inner_repository_identity_missing")
    if repository.get("repository") != config.expected_repository_id:
        _fail("lifecycle_inner_repository_id_mismatch")
    for key in ("worktree", "root"):
        try:
            actual = Path(str(repository.get(key) or "")).resolve()
        except OSError as error:
            raise LifecycleError("lifecycle_inner_worktree_identity_invalid") from error
        if actual != config.proof_worktree:
            _fail("lifecycle_inner_worktree_identity_mismatch")
    transport = _mapping(receipt.get("transport"), "lifecycle_inner_transport_missing")
    if (
        transport.get("kind") != "production_http"
        or transport.get("source_origin") != f"http://{LOOPBACK}:{source_port}"
        or transport.get("next_origin") != f"https://{LOOPBACK}:{https_port}"
        or transport.get("redirects_allowed") is not False
        or transport.get("services_started_by_harness") is not False
        or transport.get("application_modules_imported") is not False
        or transport.get("test_modules_imported") is not False
    ):
        _fail("lifecycle_inner_transport_mismatch")
    expected_runtime = _mapping(
        receipt.get("expected_runtime_identity"),
        "lifecycle_inner_expected_runtime_identity_missing",
    )
    if expected_runtime != {
        "source_head": config.expected_source_head,
        "repository_id": config.expected_repository_id,
        "worktree_id": config.expected_worktree_id,
        "worktree_id_source": "approval_preflight.stateNamespace",
    }:
        _fail("lifecycle_inner_expected_runtime_identity_mismatch")
    plugin = _mapping(
        receipt.get("target_plugin_identity"),
        "lifecycle_inner_target_plugin_identity_missing",
    )
    if (
        plugin.get("repository_id") != config.expected_repository_id
        or plugin.get("worktree_id") != config.expected_worktree_id
        or plugin.get("state_namespace") != config.expected_worktree_id
        or plugin.get("source_head") != config.expected_source_head
    ):
        _fail("lifecycle_inner_target_plugin_identity_mismatch")
    try:
        plugin_root = Path(str(plugin.get("workspace_root") or "")).resolve()
    except OSError as error:
        raise LifecycleError("lifecycle_inner_target_plugin_identity_invalid") from error
    if plugin_root != config.proof_worktree:
        _fail("lifecycle_inner_target_plugin_identity_mismatch")
    operator = _mapping(receipt.get("operator_session"), "lifecycle_inner_operator_session_missing")
    if operator.get("authenticated") is not True or operator.get("revoked") is not True:
        _fail("lifecycle_inner_operator_session_not_revoked")
    redaction = _mapping(receipt.get("redaction"), "lifecycle_inner_redaction_missing")
    if redaction.get("status") != "passed":
        _fail("lifecycle_inner_redaction_failed")
    runs = receipt.get("runs")
    if (
        not isinstance(runs, list)
        or len(runs) != 2
        or any(not isinstance(item, Mapping) for item in runs)
    ):
        _fail("lifecycle_inner_run_count_invalid")
    task_ids = [str(item.get("task_id") or "") for item in runs]
    run_ids = [str(item.get("orchestrator_run_id") or "") for item in runs]
    if (
        any(not value for value in (*task_ids, *run_ids))
        or len(set(task_ids)) != 2
        or len(set(run_ids)) != 2
    ):
        _fail("lifecycle_inner_run_identity_invalid")
    clean_rerun = _mapping(
        receipt.get("clean_rerun"),
        "lifecycle_inner_clean_rerun_missing",
    )
    for key in (
        "completed",
        "source_commit_unchanged",
        "source_baseline_verified",
        "fixture_absent_before_each_run",
        "reset_was_idempotent_after_undo",
        "repository_identity_unchanged",
        "task_id_distinct",
        "run_id_distinct",
        "approval_id_distinct",
        "artifact_identity_distinct",
    ):
        if clean_rerun.get(key) is not True:
            _fail("lifecycle_inner_clean_rerun_invalid")
    attestation = _mapping(
        receipt.get("run_attestation"),
        "lifecycle_inner_run_attestation_missing",
    )
    if (
        attestation.get("schema_version")
        != "spiritos-production-http-run-attestation/v1"
        or attestation.get("exchange_count") != 27
        or attestation.get("client_verified") is not True
    ):
        _fail("lifecycle_inner_run_attestation_invalid")
    exchanges = receipt.get("http_exchanges")
    if (
        not isinstance(exchanges, list)
        or len(exchanges) != 27
        or [
            item.get("ordinal") if isinstance(item, Mapping) else None
            for item in exchanges
        ]
        != list(range(1, 28))
    ):
        _fail("lifecycle_inner_http_transcript_invalid")
    return {
        "schema_version": receipt["schema_version"],
        "receipt_sha256": recorded,
        "source_commit": receipt["source_commit"],
        "claim_ceiling": _text(receipt.get("claim_ceiling"), "lifecycle_inner_claim_ceiling_missing"),
        "terminal_proof_eligible": True,
        "run_count": 2,
        "http_exchange_count": 27,
        "run_attestation_sha256": _sha256_json(attestation),
        "run_identity_sha256": _sha256_json(
            [
                {
                    "task_id": item.get("task_id"),
                    "orchestrator_run_id": item.get("orchestrator_run_id"),
                }
                for item in runs
            ]
        ),
        "operator_session_revoked": True,
        "redaction_status": "passed",
    }


def _bind_full_inner_proving_receipt(
    raw_inner_receipt: Mapping[str, Any],
    execution: Mapping[str, Any],
) -> dict[str, Any]:
    """Embed the exact separately published receipt, not a derived summary."""

    return {
        **dict(raw_inner_receipt),
        "execution": dict(execution),
        "published_only_after_lifecycle_teardown": True,
    }


def _operator_state_summary(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        _fail("lifecycle_operator_state_invalid")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise LifecycleError("lifecycle_operator_state_unreadable") from error
    sessions = payload.get("sessions") if isinstance(payload, Mapping) else None
    if not isinstance(sessions, Mapping) or not sessions:
        _fail("lifecycle_operator_session_state_missing")
    records = list(sessions.values())
    if any(not isinstance(record, Mapping) or not record.get("revoked_at") for record in records):
        _fail("lifecycle_operator_session_state_not_revoked")
    return {
        "session_count": len(records),
        "all_sessions_revoked": True,
        "state_sha256": _sha256_json(payload),
    }


def _approval_state_summary(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        _fail("lifecycle_approval_state_missing")
    try:
        database = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        record_rows = database.execute(
            "SELECT state, COUNT(*) FROM approval_records_v3 GROUP BY state"
        ).fetchall()
        preview_rows = database.execute(
            "SELECT state, COUNT(*) FROM approval_previews_v3 GROUP BY state"
        ).fetchall()
        database.close()
    except sqlite3.Error as error:
        raise LifecycleError("lifecycle_approval_state_invalid") from error
    record_counts = {str(state): int(count) for state, count in record_rows}
    preview_counts = {str(state): int(count) for state, count in preview_rows}
    record_total = sum(record_counts.values())
    preview_total = sum(preview_counts.values())
    if record_total < 4 or preview_total < 4:
        _fail("lifecycle_approval_state_incomplete")
    active_records = {
        state: count
        for state, count in record_counts.items()
        if state not in TERMINAL_APPROVAL_STATES
    }
    invalid_previews = {
        state: count
        for state, count in preview_counts.items()
        if state not in {"approved", "rejected"}
    }
    if active_records or invalid_previews:
        _fail("lifecycle_temporary_approval_authority_still_active")
    return {
        "approval_record_count": record_total,
        "approval_preview_count": preview_total,
        "active_approval_count": 0,
        "state_counts_sha256": _sha256_json(
            {"records": record_counts, "previews": preview_counts}
        ),
        "database_sha256": _sha256_file(path),
    }


def _remove_owned_top_level(root: Path, relative: str) -> None:
    target = root / relative
    if target.parent != root:
        _fail("lifecycle_cleanup_target_invalid")
    if not target.exists() and not target.is_symlink():
        return
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)
    else:
        _fail("lifecycle_cleanup_target_unsupported")


def _clean_data_source_proxy(root: Path) -> None:
    data_root = root / "data" / "source-proxy"
    if not data_root.exists():
        return
    tracked_raw = _git(root, "ls-files", "-z", "--", "data/source-proxy")
    tracked = {value for value in tracked_raw.split("\0") if value}
    tracked_hashes = {
        relative: _sha256_file(root / relative)
        for relative in tracked
        if (root / relative).is_file() and not (root / relative).is_symlink()
    }
    for entry in sorted(data_root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        relative = entry.relative_to(root).as_posix()
        if relative in tracked:
            continue
        if entry.is_symlink() or entry.is_file():
            entry.unlink()
        elif entry.is_dir():
            try:
                entry.rmdir()
            except OSError:
                pass
    for relative, expected_hash in tracked_hashes.items():
        if _sha256_file(root / relative) != expected_hash:
            _fail("lifecycle_tracked_runtime_baseline_changed")


def _remove_owned_proving_fixture(root: Path) -> bool:
    relative = PROVING_FIXTURE_RELATIVE.as_posix()
    tracked_raw = _git(
        root,
        "ls-files",
        "-z",
        "--",
        f":(literal){relative}",
        f":(glob){relative}/**",
    )
    if any(value for value in tracked_raw.split("\0") if value):
        _fail("lifecycle_proving_fixture_contains_tracked_paths")

    target = root / PROVING_FIXTURE_RELATIVE
    if not target.exists() and not target.is_symlink():
        return False

    ancestor = root
    for component in PROVING_FIXTURE_RELATIVE.parts[:-1]:
        ancestor = ancestor / component
        if ancestor.is_symlink():
            _fail("lifecycle_proving_fixture_ancestor_symlink_forbidden")
        if not ancestor.is_dir():
            _fail("lifecycle_proving_fixture_ancestor_invalid")

    if target.is_symlink():
        target.unlink()
    elif target.is_dir():
        if not getattr(shutil.rmtree, "avoids_symlink_attacks", False):
            _fail("lifecycle_proving_fixture_symlink_safety_unavailable")
        shutil.rmtree(target)
    else:
        _fail("lifecycle_proving_fixture_cleanup_target_unsupported")
    if target.exists() or target.is_symlink():
        _fail("lifecycle_proving_fixture_cleanup_failed")
    return True


def _cleanup_worktree_runtime(
    identity: WorktreeIdentity,
    *,
    config: LifecycleConfig,
    dependency_link: Path | None,
) -> dict[str, Any]:
    root = identity.root
    if dependency_link is not None and (dependency_link.exists() or dependency_link.is_symlink()):
        if not dependency_link.is_symlink():
            _fail("lifecycle_dependency_link_replaced")
        dependency_link.unlink()
    _remove_owned_top_level(root, ".next")
    _remove_owned_top_level(root, ".spirit-backups")
    _clean_data_source_proxy(root)
    proving_fixture_was_present = _remove_owned_proving_fixture(root)
    status = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    if status:
        _fail("lifecycle_worktree_not_clean_after_teardown")
    ignored = _git(
        root,
        "status",
        "--porcelain=v1",
        "--ignored=matching",
        "--untracked-files=all",
    )
    if _sha256_text(ignored) != identity.initial_ignored_status_sha256:
        _fail("lifecycle_ignored_runtime_state_not_restored")
    if _git(root, "rev-parse", "HEAD").lower() != identity.source_head:
        _fail("lifecycle_source_head_changed_during_proving")
    final_identity = _verify_clean_linked_worktree(config)
    if final_identity != identity:
        _fail("lifecycle_worktree_identity_changed_during_proving")
    return {
        "dependency_link_removed": True,
        "next_build_removed": True,
        "backup_state_removed": True,
        "runtime_receipts_removed": True,
        "proving_fixture_removed": True,
        "proving_fixture_was_present": proving_fixture_was_present,
        "proving_fixture_tracked_paths_absent": True,
        "proving_fixture_symlinks_not_followed": True,
        "tracked_status_clean": True,
        "ignored_status_restored": True,
        "source_head_unchanged": True,
        "branch_unchanged": True,
        "repository_identity_unchanged": True,
        "linked_worktree_registration_unchanged": True,
        "index_visibility_unchanged": True,
    }


def _remove_state_root(root: Path) -> None:
    expected_parent = Path(tempfile.gettempdir()).resolve()
    if root.parent != expected_parent or not root.name.startswith(STATE_PREFIX):
        _fail("lifecycle_state_cleanup_target_invalid")
    marker = root / ".foundation-r1-owned"
    if not marker.is_file() or marker.read_text(encoding="utf-8").strip() != REMEDIATION_ID:
        _fail("lifecycle_state_cleanup_marker_missing")
    shutil.rmtree(root)
    if root.exists() or root.is_symlink():
        _fail("lifecycle_state_cleanup_failed")


def _service_receipt(service: ServiceProcess) -> dict[str, Any]:
    if (
        not service.stdout_sha256
        or not service.stderr_sha256
        or not service.loopback_bound
        or not service.listener_identity_sha256
    ):
        _fail("lifecycle_service_log_evidence_missing")
    return {
        "name": service.name,
        "command_sha256": service.command_sha256,
        "pid_sha256": _sha256_text(str(service.process.pid)),
        "port_sha256": _sha256_text(str(service.port)),
        "instance_sha256": _sha256_json(
            {
                "command_sha256": service.command_sha256,
                "pid": service.process.pid,
                "port": service.port,
                "started_at": service.started_at,
            }
        ),
        "health_response_sha256": service.health_response_sha256,
        "stdout_sha256": service.stdout_sha256,
        "stderr_sha256": service.stderr_sha256,
        "cwd_bound_to_proof_worktree": True,
        "loopback_bound": service.loopback_bound,
        "listener_identity_sha256": service.listener_identity_sha256,
        "stopped": service.stopped,
        "process_absent": service.process_absent,
        "process_group_absent": service.process_group_absent,
        "process_session_absent": service.process_session_absent,
        "descendant_processes_absent": service.descendant_processes_absent,
        "cgroup_empty": service.cgroup_empty,
        "cgroup_unit_sha256": _sha256_text(service.scope_unit),
        "cgroup_path_sha256": _sha256_text(str(service.cgroup_path)),
        "port_closed": service.port_closed,
        "raw_pid_recorded": False,
        "raw_port_recorded": False,
    }


def _forbidden_key_paths(value: Any, *, prefix: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            redaction_declaration = (
                child is False
                and normalized.endswith(("_recorded", "_exposed"))
            ) or (
                child is True
                and normalized.endswith("_cleared")
            )
            if (
                any(fragment in normalized for fragment in FORBIDDEN_KEY_FRAGMENTS)
                and not redaction_declaration
            ):
                failures.append(f"{prefix}.{key}")
            failures.extend(_forbidden_key_paths(child, prefix=f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            failures.extend(_forbidden_key_paths(child, prefix=f"{prefix}[{index}]"))
    return failures


def _assert_redacted(receipt: Mapping[str, Any], *, forbidden_values: Sequence[str]) -> None:
    if _forbidden_key_paths(receipt):
        _fail("lifecycle_receipt_forbidden_key_present")
    _assert_sensitive_values_absent(
        _canonical_json(receipt),
        forbidden_values=forbidden_values,
    )


def _assert_sensitive_values_absent(
    serialized: bytes,
    *,
    forbidden_values: Sequence[str],
) -> None:
    for value in forbidden_values:
        if (
            isinstance(value, str)
            and len(value) >= 8
            and value.encode("utf-8") in serialized
        ):
            _fail("lifecycle_receipt_sensitive_value_present")


def _assert_logs_redacted(log_root: Path, *, forbidden_values: Sequence[str]) -> None:
    try:
        logs = sorted(path for path in log_root.iterdir() if path.is_file())
        for path in logs:
            _assert_sensitive_values_absent(
                path.read_bytes(),
                forbidden_values=forbidden_values,
            )
    except OSError as error:
        raise LifecycleError("lifecycle_log_redaction_scan_failed") from error


def _write_new_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        _fail("lifecycle_receipt_output_exists")
    payload = json.dumps(receipt, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = handle.name
            os.chmod(temporary, 0o600)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temporary, path)
    except FileExistsError as error:
        raise LifecycleError("lifecycle_receipt_output_exists") from error
    except OSError as error:
        raise LifecycleError("lifecycle_receipt_atomic_create_failed") from error
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def _run_lifecycle(config: LifecycleConfig) -> dict[str, Any]:
    started_at = _utc_now()
    task_text = config.task_file.read_text(encoding="utf-8").strip()
    task_sha256 = _sha256_text(task_text)
    identity = _verify_clean_linked_worktree(config)
    _verify_external_debug_writer_retired(config.proof_worktree)
    _verify_loopback_tls_proxy_contract(config.proof_worktree)
    approval_secret_baseline = _approval_secret_baseline()
    cgroup_runtime = _verify_cgroup_runtime(_command_environment())
    source_port = _allocate_port(config.source_port, excluded=set())
    next_port = _allocate_port(config.next_port, excluded={source_port})
    https_port = _allocate_port(
        config.https_port,
        excluded={source_port, next_port, 3000},
    )
    if https_port == 3000:
        _fail("lifecycle_https_port_3000_forbidden")
    state_root = _new_state_root()
    operator_secret = ""
    environment: dict[str, str] = {}
    dependency_link: Path | None = None
    source: ServiceProcess | None = None
    next_service: ServiceProcess | None = None
    tls_service: ServiceProcess | None = None
    service_receipts: list[dict[str, Any]] | None = None
    next_build: dict[str, Any] | None = None
    source_build: dict[str, Any] | None = None
    approval_preflight: dict[str, Any] | None = None
    inner_receipt: dict[str, Any] | None = None
    raw_inner_receipt: dict[str, Any] | None = None
    inner_execution: dict[str, Any] | None = None
    operator_state: dict[str, Any] | None = None
    approval_state: dict[str, Any] | None = None
    state_directory_sha256 = ""
    state_entry_count = 0
    cleanup: dict[str, Any] | None = None
    primary_error: LifecycleError | None = None
    teardown_errors: list[str] = []
    try:
        operator_secret = _operator_e2e_secret(config)
        environment = _runtime_environment(
            config,
            state_root=state_root,
            source_port=source_port,
            next_port=next_port,
            https_port=https_port,
            operator_secret=operator_secret,
        )
        python_environment_sha256, python_environment_entry_count = (
            _python_site_packages_identity(config)
        )
        source_build = {
            "source_tree": identity.source_proxy_tree,
            "python_executable_sha256": _sha256_file(
                config.python_executable.resolve()
            ),
            "python_environment_sha256": python_environment_sha256,
            "python_environment_entry_count": python_environment_entry_count,
            "python_package_inventory_sha256": _python_environment_sha256(config),
            "python_runtime_matched_expected_identity": True,
        }
        approval_preflight = _approval_preflight(
            config,
            environment=_scoped_runtime_environment(
                environment,
                operator_credential=False,
                operator_e2e_secret=False,
            ),
            state_root=state_root,
        )
        dependency_link = config.proof_worktree / "node_modules"
        _prepare_dependency_link(config)
        next_build = _build_next(config, environment=environment, state_root=state_root)
        source_command = [
            str(config.python_executable),
            "-m",
            "uvicorn",
            "source_proxy.main:app",
            "--host",
            LOOPBACK,
            "--port",
            str(source_port),
        ]
        next_command = [
            str(config.node_executable),
            str(config.node_modules_root / "next" / "dist" / "bin" / "next"),
            "start",
            "-H",
            LOOPBACK,
            "-p",
            str(next_port),
        ]
        source = _launch_service(
            name="source_proxy",
            command=source_command,
            config=config,
            environment=_scoped_runtime_environment(
                environment,
                operator_credential=False,
                operator_e2e_secret=True,
            ),
            port=source_port,
            state_root=state_root,
        )
        source_health = _wait_for_json_health(
            source,
            path="/v1/self/status",
            timeout_seconds=config.startup_timeout_seconds,
        )
        configured_roots = source_health.get("configured_roots")
        root_paths = {
            item.get("path")
            for item in configured_roots
            if isinstance(item, Mapping)
        } if isinstance(configured_roots, list) else set()
        repo_metadata = source_health.get("repo_metadata")
        if (
            source_health.get("service") != "source-proxy"
            or source_health.get("manifest_version") != "2.7A-1"
            or str(config.proof_worktree) not in root_paths
            or not isinstance(repo_metadata, Mapping)
            or repo_metadata.get("root") != str(config.proof_worktree)
            or repo_metadata.get("git_directory_present") is not True
        ):
            _fail("lifecycle_source_proxy_health_invalid")
        _require_process_cwd(source, config.proof_worktree)
        _require_loopback_listener(source)
        next_service = _launch_service(
            name="next",
            command=next_command,
            config=config,
            environment=_scoped_runtime_environment(
                environment,
                operator_credential=False,
                operator_e2e_secret=True,
            ),
            port=next_port,
            state_root=state_root,
        )
        next_health = _wait_for_json_health(
            next_service,
            path="/v1/operator/session",
            timeout_seconds=config.startup_timeout_seconds,
        )
        if next_health.get("status") != "unauthenticated":
            _fail("lifecycle_next_health_invalid")
        _require_process_cwd(next_service, config.proof_worktree)
        _require_loopback_listener(next_service)
        tls_command = [
            str(config.node_executable),
            str(config.proof_worktree / "scripts" / "spiritflix-prod-https-proxy.mjs"),
            "--host",
            LOOPBACK,
            "--port",
            str(https_port),
            "--target-port",
            str(next_port),
            "--key",
            str(config.tls_private_key),
            "--cert",
            str(config.tls_certificate),
        ]
        tls_service = _launch_service(
            name="next_tls",
            command=tls_command,
            config=config,
            environment=_scoped_runtime_environment(
                environment,
                operator_credential=False,
                operator_e2e_secret=False,
            ),
            port=https_port,
            state_root=state_root,
        )
        tls_health = _wait_for_json_health(
            tls_service,
            path="/v1/operator/session",
            timeout_seconds=config.startup_timeout_seconds,
            scheme="https",
            ca_file=config.tls_certificate,
        )
        if tls_health.get("status") != "unauthenticated":
            _fail("lifecycle_next_tls_health_invalid")
        _require_process_cwd(tls_service, config.proof_worktree)
        _require_loopback_listener(tls_service)
        inner_receipt, inner_execution, raw_inner_receipt = _run_inner_client(
            config,
            environment=_scoped_runtime_environment(
                environment,
                operator_credential=True,
                operator_e2e_secret=False,
            ),
            source_port=source_port,
            next_port=next_port,
            https_port=https_port,
            state_root=state_root,
            receipt_path=state_root / "inner-receipt.json",
        )
    except LifecycleError as error:
        primary_error = error
    except Exception:
        primary_error = LifecycleError("lifecycle_internal_error")
    finally:
        for service in (tls_service, next_service, source):
            if service is None:
                continue
            try:
                _stop_service(service, environment=environment)
            except Exception as error:
                teardown_errors.append(
                    error.reason_code
                    if isinstance(error, LifecycleError)
                    else f"lifecycle_{service.name}_teardown_internal_error"
                )
        try:
            _verify_approval_secret_unchanged(approval_secret_baseline)
        except Exception as error:
            teardown_errors.append(
                error.reason_code
                if isinstance(error, LifecycleError)
                else "lifecycle_approval_signing_key_verification_internal_error"
            )
        if primary_error is None and not teardown_errors:
            try:
                if source is None or next_service is None or tls_service is None:
                    _fail("lifecycle_service_sequence_incomplete")
                service_receipts = [
                    _service_receipt(source),
                    _service_receipt(next_service),
                    _service_receipt(tls_service),
                ]
                if next_build is None:
                    _fail("lifecycle_next_build_evidence_missing")
                final_dependency_sha256, final_dependency_entry_count = (
                    _hash_directory(config.node_modules_root)
                )
                if (
                    final_dependency_sha256
                    != config.expected_node_modules_sha256
                    or final_dependency_entry_count
                    != next_build.get("node_modules_entry_count")
                ):
                    _fail("lifecycle_node_modules_changed_during_proving")
                next_build["node_modules_unchanged_after_run"] = True
                final_python_environment_sha256, final_python_entry_count = (
                    _python_site_packages_identity(config)
                )
                if (
                    source_build is None
                    or final_python_environment_sha256
                    != source_build.get("python_environment_sha256")
                    or final_python_entry_count
                    != source_build.get("python_environment_entry_count")
                ):
                    _fail("lifecycle_runtime_identity_changed_during_proving")
                _verify_node_executable(config)
                source_build["python_runtime_unchanged_after_run"] = True
                next_build["node_runtime_unchanged_after_run"] = True
                try:
                    final_task_text = config.task_file.read_text(
                        encoding="utf-8"
                    ).strip()
                except (OSError, UnicodeError) as error:
                    raise LifecycleError(
                        "lifecycle_task_unreadable_after_proving"
                    ) from error
                if _sha256_text(final_task_text) != task_sha256:
                    _fail("lifecycle_task_changed_during_proving")
                _assert_logs_redacted(
                    state_root / "logs",
                    forbidden_values=[operator_secret, task_text],
                )
            except Exception as error:
                teardown_errors.append(
                    error.reason_code
                    if isinstance(error, LifecycleError)
                    else "lifecycle_service_evidence_internal_error"
                )
        if primary_error is None and not teardown_errors:
            try:
                operator_state = _operator_state_summary(
                    state_root / "operator" / "sessions.json"
                )
                approval_state = _approval_state_summary(
                    state_root / "approval" / "approvals.sqlite3"
                )
                state_directory_sha256, state_entry_count = _hash_directory(state_root)
            except Exception as error:
                teardown_errors.append(
                    error.reason_code
                    if isinstance(error, LifecycleError)
                    else "lifecycle_authority_teardown_internal_error"
                )
        try:
            cleanup = _cleanup_worktree_runtime(
                identity,
                config=config,
                dependency_link=dependency_link,
            )
        except Exception as error:
            teardown_errors.append(
                error.reason_code
                if isinstance(error, LifecycleError)
                else "lifecycle_worktree_cleanup_internal_error"
            )
        try:
            _remove_state_root(state_root)
        except Exception as error:
            teardown_errors.append(
                error.reason_code
                if isinstance(error, LifecycleError)
                else "lifecycle_state_cleanup_internal_error"
            )
    if primary_error is not None:
        if teardown_errors:
            _fail("lifecycle_teardown_failed_after_proving_failure")
        raise primary_error
    if teardown_errors:
        _fail("lifecycle_teardown_failed")
    if any(
        value is None
        for value in (
            source,
            next_service,
            tls_service,
            service_receipts,
            next_build,
            source_build,
            approval_preflight,
            inner_receipt,
            raw_inner_receipt,
            inner_execution,
            operator_state,
            approval_state,
            cleanup,
        )
    ):
        _fail("lifecycle_sequence_incomplete")
    completed_at = _utc_now()
    receipt: dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA,
        "receipt_type": "foundation_r1_clean_production_service_lifecycle",
        "remediation_id": REMEDIATION_ID,
        "status": "passed",
        "terminal_proof_eligible": False,
        "claim_ceiling": LIFECYCLE_CLAIM_CEILING,
        "started_at": started_at,
        "completed_at": completed_at,
        "source": {
            "repository_id": identity.repository_id,
            "worktree_root": str(identity.root),
            "branch": identity.branch,
            "source_head": identity.source_head,
            "worktree_id": config.expected_worktree_id,
            "source_tree": identity.source_tree,
            "source_proxy_tree": identity.source_proxy_tree,
            "git_common_dir_sha256": identity.git_common_dir_sha256,
            "git_executable_sha256": _sha256_file(GIT_EXECUTABLE),
            "initial_ignored_status_sha256": identity.initial_ignored_status_sha256,
            "registered_linked_worktree": True,
            "clean_before_build": True,
        },
        "build": {
            "next": next_build,
            "next_tls": {
                "proxy_script_sha256": _sha256_file(
                    config.proof_worktree
                    / "scripts"
                    / "spiritflix-prod-https-proxy.mjs"
                ),
                "certificate_sha256": _sha256_file(config.tls_certificate),
                "private_key_recorded": False,
            },
            "source_proxy": source_build,
        },
        "services": service_receipts,
        "process_boundary": cgroup_runtime,
        "inner_proving": _bind_full_inner_proving_receipt(
            raw_inner_receipt,
            inner_execution,
        ),
        "temporary_authority": {
            "state_root_sha256": _sha256_text(str(state_root)),
            "state_directory_sha256": state_directory_sha256,
            "state_entry_count": state_entry_count,
            "operator": operator_state,
            "approval": approval_state,
            "approval_preflight": approval_preflight,
            "shared_signing_key_preexisted": True,
            "shared_signing_key_unchanged": True,
            "state_root_removed": True,
        },
        "teardown": {
            **cleanup,
            "all_services_stopped": True,
            "all_service_processes_absent": True,
            "all_service_ports_closed": True,
            "temporary_state_removed": True,
            "operator_session_revoked": True,
            "temporary_approval_authority_inactive": True,
            "failures": [],
        },
        "redaction": {
            "status": "passed",
            "raw_environment_recorded": False,
            "raw_process_ids_recorded": False,
            "raw_ports_recorded": False,
            "raw_logs_recorded": False,
            "raw_task_recorded": False,
            "credentials_recorded": False,
            "forbidden_key_scan": "passed",
            "forbidden_value_scan": "passed",
        },
        "failures": [],
    }
    _assert_redacted(receipt, forbidden_values=[operator_secret, task_text])
    receipt["receipt_sha256"] = _sha256_json(receipt)
    _assert_redacted(receipt, forbidden_values=[operator_secret, task_text])
    _write_new_receipt(config.output, receipt)
    _write_new_receipt(config.inner_receipt, raw_inner_receipt)
    return receipt


def _environment_default(name: str) -> str | None:
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else None


def _parse_config(argv: Sequence[str] | None = None) -> LifecycleConfig:
    parser = argparse.ArgumentParser(
        description="Build and own isolated Source Proxy + Next production proving services."
    )
    parser.add_argument("--proof-worktree", required=True, type=Path)
    parser.add_argument("--expected-source-head", required=True)
    parser.add_argument("--expected-repository-id", required=True)
    parser.add_argument("--expected-worktree-id", required=True)
    parser.add_argument("--expected-branch", required=True)
    parser.add_argument("--proposal-id", required=True)
    parser.add_argument("--task-file", required=True, type=Path)
    parser.add_argument("--inner-receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--python-executable",
        type=Path,
        default=Path(sys.executable),
    )
    parser.add_argument("--expected-python-executable-sha256", required=True)
    parser.add_argument("--expected-python-environment-sha256", required=True)
    parser.add_argument(
        "--node-executable",
        type=Path,
        default=Path(_environment_default("SPIRITOS_FOUNDATION_R1_NODE") or shutil.which("node") or ""),
    )
    parser.add_argument("--expected-node-executable-sha256", required=True)
    parser.add_argument(
        "--node-modules-root",
        required=_environment_default("SPIRITOS_FOUNDATION_R1_NODE_MODULES_ROOT") is None,
        type=Path,
        default=(
            Path(_environment_default("SPIRITOS_FOUNDATION_R1_NODE_MODULES_ROOT"))
            if _environment_default("SPIRITOS_FOUNDATION_R1_NODE_MODULES_ROOT")
            else None
        ),
    )
    parser.add_argument("--expected-node-modules-sha256", required=True)
    parser.add_argument(
        "--tls-certificate",
        required=_environment_default("SPIRITOS_FOUNDATION_R1_TLS_CERTIFICATE") is None,
        type=Path,
        default=(
            Path(_environment_default("SPIRITOS_FOUNDATION_R1_TLS_CERTIFICATE"))
            if _environment_default("SPIRITOS_FOUNDATION_R1_TLS_CERTIFICATE")
            else None
        ),
    )
    parser.add_argument(
        "--tls-private-key",
        required=_environment_default("SPIRITOS_FOUNDATION_R1_TLS_PRIVATE_KEY") is None,
        type=Path,
        default=(
            Path(_environment_default("SPIRITOS_FOUNDATION_R1_TLS_PRIVATE_KEY"))
            if _environment_default("SPIRITOS_FOUNDATION_R1_TLS_PRIVATE_KEY")
            else None
        ),
    )
    parser.add_argument("--primary-model-alias", required=True)
    parser.add_argument("--fallback-model-alias", required=True)
    parser.add_argument("--expected-failed-provider", required=True)
    parser.add_argument("--expected-failed-model", required=True)
    parser.add_argument("--expected-fallback-provider", required=True)
    parser.add_argument("--expected-fallback-model", required=True)
    parser.add_argument("--source-port", type=int, default=0)
    parser.add_argument("--next-port", type=int, default=0)
    parser.add_argument("--https-port", type=int, default=0)
    parser.add_argument("--startup-timeout-seconds", type=float, default=180)
    parser.add_argument("--inner-http-timeout-seconds", type=float, default=900)
    parser.add_argument("--inner-process-timeout-seconds", type=float, default=7200)
    parser.add_argument("--operator-e2e-secret-source", choices=("generated", "canonical"), default="generated")
    args = parser.parse_args(argv)

    proof_raw = args.proof_worktree.expanduser()
    if Path(os.path.abspath(proof_raw)) != Path(os.path.realpath(proof_raw)):
        _fail("lifecycle_proof_worktree_symlink_forbidden")
    proof = proof_raw.resolve()
    if not proof.is_dir():
        _fail("lifecycle_proof_worktree_missing")
    head = str(args.expected_source_head).lower()
    if GIT_OID_RE.fullmatch(head) is None:
        _fail("lifecycle_expected_source_head_invalid")
    for value, reason in (
        (args.expected_repository_id, "lifecycle_expected_repository_id_invalid"),
        (args.expected_branch, "lifecycle_expected_branch_invalid"),
    ):
        if IDENTITY_RE.fullmatch(str(value)) is None:
            _fail(reason)
    if str(args.expected_repository_id) != R1_REPOSITORY_ID:
        _fail("lifecycle_expected_repository_id_invalid")
    if WORKTREE_ID_RE.fullmatch(str(args.expected_worktree_id)) is None:
        _fail("lifecycle_expected_worktree_id_invalid")
    if PROPOSAL_RE.fullmatch(str(args.proposal_id)) is None:
        _fail("lifecycle_proposal_id_invalid")
    task_raw = args.task_file.expanduser()
    if task_raw.is_symlink():
        _fail("lifecycle_task_file_invalid")
    task_file = task_raw.resolve()
    if not task_file.is_file():
        _fail("lifecycle_task_file_invalid")
    task_text = task_file.read_text(encoding="utf-8").strip()
    if not 20 <= len(task_text.encode("utf-8")) <= 4_000 or "\x00" in task_text:
        _fail("lifecycle_task_content_invalid")
    inner_receipt = _new_output_path(
        args.inner_receipt,
        reason="lifecycle_inner_receipt_output_invalid",
    )
    output = _new_output_path(args.output, reason="lifecycle_receipt_output_invalid")
    if inner_receipt == output:
        _fail("lifecycle_receipt_outputs_not_distinct")
    for path, reason in (
        (task_file, "lifecycle_task_file_inside_proof_worktree"),
        (inner_receipt, "lifecycle_inner_receipt_inside_proof_worktree"),
        (output, "lifecycle_receipt_inside_proof_worktree"),
    ):
        _outside_worktree(path, proof, reason=reason)
    python = Path(os.path.abspath(args.python_executable.expanduser()))
    node = Path(os.path.abspath(args.node_executable.expanduser()))
    if any(not path.is_file() or not os.access(path, os.X_OK) for path in (python, node)):
        _fail("lifecycle_runtime_executable_invalid")
    try:
        python_resolved = python.resolve(strict=True)
        node_resolved = node.resolve(strict=True)
    except OSError as error:
        raise LifecycleError("lifecycle_runtime_executable_invalid") from error
    for executable in (python, python_resolved, node, node_resolved):
        _outside_worktree(
            executable,
            proof,
            reason="lifecycle_runtime_executable_inside_proof_worktree",
        )
    expected_python_executable_sha256 = str(
        args.expected_python_executable_sha256
    ).lower()
    expected_python_environment_sha256 = str(
        args.expected_python_environment_sha256
    ).lower()
    expected_node_executable_sha256 = str(args.expected_node_executable_sha256).lower()
    if any(
        SHA256_RE.fullmatch(value) is None
        for value in (
            expected_python_executable_sha256,
            expected_python_environment_sha256,
            expected_node_executable_sha256,
        )
    ):
        _fail("lifecycle_expected_runtime_sha256_invalid")
    if _sha256_file(python_resolved) != expected_python_executable_sha256:
        _fail("lifecycle_python_executable_identity_mismatch")
    if _sha256_file(node_resolved) != expected_node_executable_sha256:
        _fail("lifecycle_node_executable_identity_mismatch")
    if args.node_modules_root is None:
        _fail("lifecycle_node_modules_required")
    node_modules = args.node_modules_root.expanduser().resolve()
    if not node_modules.is_dir():
        _fail("lifecycle_node_modules_invalid")
    _outside_worktree(
        node_modules,
        proof,
        reason="lifecycle_node_modules_inside_proof_worktree",
    )
    expected_node_modules_sha256 = str(args.expected_node_modules_sha256).lower()
    if SHA256_RE.fullmatch(expected_node_modules_sha256) is None:
        _fail("lifecycle_expected_node_modules_sha256_invalid")
    if args.tls_certificate is None or args.tls_private_key is None:
        _fail("lifecycle_tls_material_required")
    tls_certificate_raw = args.tls_certificate.expanduser()
    tls_private_key_raw = args.tls_private_key.expanduser()
    if tls_certificate_raw.is_symlink() or tls_private_key_raw.is_symlink():
        _fail("lifecycle_tls_material_invalid")
    tls_certificate = tls_certificate_raw.resolve()
    tls_private_key = tls_private_key_raw.resolve()
    if (
        not tls_certificate.is_file()
        or not tls_private_key.is_file()
    ):
        _fail("lifecycle_tls_material_invalid")
    try:
        if tls_private_key.stat().st_mode & 0o077:
            _fail("lifecycle_tls_private_key_mode_invalid")
    except OSError as error:
        raise LifecycleError("lifecycle_tls_material_invalid") from error
    for path, reason in (
        (tls_certificate, "lifecycle_tls_certificate_inside_proof_worktree"),
        (tls_private_key, "lifecycle_tls_private_key_inside_proof_worktree"),
    ):
        _outside_worktree(path, proof, reason=reason)
    aliases = (
        args.primary_model_alias,
        args.fallback_model_alias,
        args.expected_failed_provider,
        args.expected_failed_model,
        args.expected_fallback_provider,
        args.expected_fallback_model,
    )
    if any(
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 200
        or any(ord(character) < 32 for character in value)
        for value in aliases
    ):
        _fail("lifecycle_model_identity_invalid")
    if aliases != (
        R1_PRIMARY_MODEL_ALIAS,
        R1_CODER_ALIAS,
        R1_FAILED_PROVIDER,
        R1_PRIMARY_MODEL_ALIAS,
        R1_FALLBACK_PROVIDER,
        R1_FALLBACK_MODEL,
    ):
        _fail("lifecycle_model_identity_profile_mismatch")
    for port in (args.source_port, args.next_port, args.https_port):
        if port != 0 and not 1024 <= port <= 65535:
            _fail("lifecycle_service_port_invalid")
    requested_ports = [
        port for port in (args.source_port, args.next_port, args.https_port) if port
    ]
    if len(requested_ports) != len(set(requested_ports)):
        _fail("lifecycle_service_ports_not_distinct")
    if args.https_port == 3000:
        _fail("lifecycle_https_port_3000_forbidden")
    if not 10 <= args.startup_timeout_seconds <= 1_800:
        _fail("lifecycle_startup_timeout_invalid")
    if not 1 <= args.inner_http_timeout_seconds <= 3_600:
        _fail("lifecycle_inner_http_timeout_invalid")
    if not 60 <= args.inner_process_timeout_seconds <= 14_400:
        _fail("lifecycle_inner_process_timeout_invalid")
    return LifecycleConfig(
        proof_worktree=proof,
        expected_source_head=head,
        expected_repository_id=str(args.expected_repository_id),
        expected_worktree_id=str(args.expected_worktree_id),
        expected_branch=str(args.expected_branch),
        proposal_id=str(args.proposal_id),
        task_file=task_file,
        inner_receipt=inner_receipt,
        output=output,
        python_executable=python,
        python_executable_resolved=python_resolved,
        expected_python_executable_sha256=expected_python_executable_sha256,
        expected_python_environment_sha256=expected_python_environment_sha256,
        node_executable=node,
        node_executable_resolved=node_resolved,
        expected_node_executable_sha256=expected_node_executable_sha256,
        node_modules_root=node_modules,
        expected_node_modules_sha256=expected_node_modules_sha256,
        tls_certificate=tls_certificate,
        tls_private_key=tls_private_key,
        primary_model_alias=str(args.primary_model_alias),
        fallback_model_alias=str(args.fallback_model_alias),
        expected_failed_provider=str(args.expected_failed_provider),
        expected_failed_model=str(args.expected_failed_model),
        expected_fallback_provider=str(args.expected_fallback_provider),
        expected_fallback_model=str(args.expected_fallback_model),
        source_port=int(args.source_port),
        next_port=int(args.next_port),
        https_port=int(args.https_port),
        startup_timeout_seconds=float(args.startup_timeout_seconds),
        inner_http_timeout_seconds=float(args.inner_http_timeout_seconds),
        inner_process_timeout_seconds=float(args.inner_process_timeout_seconds),
        operator_e2e_secret_source=str(args.operator_e2e_secret_source),
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        config = _parse_config(argv)
        receipt = _run_lifecycle(config)
    except LifecycleError as error:
        print(f"FOUNDATION_R1_LIFECYCLE_FAILED:{error.reason_code}", file=sys.stderr)
        return 1
    except (OSError, UnicodeError):
        print("FOUNDATION_R1_LIFECYCLE_FAILED:lifecycle_io_failed", file=sys.stderr)
        return 1
    except Exception:
        print("FOUNDATION_R1_LIFECYCLE_FAILED:lifecycle_internal_error", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "passed",
                "receipt": str(config.output),
                "receipt_sha256": receipt["receipt_sha256"],
                "terminal_proof_eligible": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
