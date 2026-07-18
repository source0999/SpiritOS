#!/usr/bin/env python3
"""Run the Foundation Remediation R1 black-box production proving sequence.

This program is deliberately an HTTP-only client.  It does not import Source
Proxy, Next, target-adapter, authority, or test modules; it does not start a
service; and it never accepts a caller-provided diff.  The only diff that can
cross the approval boundary is read back from the CodingOrchestrator's
persisted runtime output.

The Source Proxy service must be started separately with an intentionally
failing ``SPIRITOS_CODING_PRIMARY_MODEL_ALIAS`` and a working canonical
``SPIRITOS_CODING_FALLBACK_MODEL_ALIAS``.  The expected failed and replacement
provider/model identities are supplied to this client and checked against the
persisted controlled-recovery record.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import hmac
import http.cookiejar
import json
import os
import re
import ssl
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence


REMEDIATION_ID = "foundation-remediation-r1"
RECEIPT_SCHEMA = "spiritos-foundation-remediation-r1-production-proving-receipt/v1"
PROMPT_ID = "coder-001-init-dummy-product-site"
CONTEXT_ID = "init-storefront"
FIXTURE_ROOT = "tests/ui-agent-trials/fixtures/dummy-product-site/"
TARGET = f"{FIXTURE_ROOT}README.md"
ALLOWED_FILES = [f"{FIXTURE_ROOT}**"]
PROMPT1_FILES = sorted(
    f"{FIXTURE_ROOT}{name}"
    for name in (
        "README.md",
        "package.json",
        "index.html",
        "src/main.js",
        "src/products.js",
        "src/styles.css",
    )
)
ACTION = f"Run selected dummy Coder prompt {PROMPT_ID}"
CONSUMER = "coding-executor:coder"
OPERATOR_COOKIE_NAME = "spiritos_operator_approval"
ORCHESTRATOR_SCHEMA = "coding-orchestrator/v2"
LANE_SEQUENCE = [
    "context-broker",
    "planner",
    "coder",
    "reviewer",
    "verifier",
    "anti-cheat",
    "repair",
    "evidence-recorder",
]
FINAL_LANE_STATES = {
    "context-broker": "completed",
    "planner": "completed",
    "coder": "completed",
    "reviewer": "completed",
    "verifier": "completed",
    "anti-cheat": "completed",
    "repair": "skipped",
    "evidence-recorder": "completed",
}
RUNTIME_LANES = {
    "context-broker",
    "planner",
    "coder",
    "reviewer",
    "verifier",
    "anti-cheat",
    "evidence-recorder",
}
PARTICIPANT_ROLES = {
    "coding-executor",
    "coding-reviewer",
    "coding-verifier",
    "coding-anti-cheat",
    "evidence-recorder",
}
MAX_RESPONSE_BYTES = 32 * 1024 * 1024
MAX_TASK_BYTES = 4_000
PROPOSAL_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
IDENTITY_RE = re.compile(r"^[A-Za-z0-9._:-]{1,200}$")
GIT_OID_RE = re.compile(r"^[0-9a-f]{40,64}$")
SHA256_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")
CARTOGRAPHER_PROPOSAL_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{16}$")
FORBIDDEN_RECEIPT_KEYS = {
    "approved_diff",
    "proposed_diff",
    "prompt_text",
    "task_text",
    "raw_response",
    "response_body",
    "request_body",
    "credential",
    "cookie",
    "set-cookie",
    "csrf",
    "error_message",
}
FORBIDDEN_RECEIPT_KEY_SUBSTRINGS = {"token", "secret", "authorization"}


class ProvingError(RuntimeError):
    """A fail-closed proving invariant was not met."""

    def __init__(self, reason_code: str, *, step: str | None = None):
        self.reason_code = reason_code
        self.step = step
        super().__init__(f"{step}:{reason_code}" if step else reason_code)


def _fail(reason_code: str, *, step: str | None = None) -> None:
    raise ProvingError(reason_code, step=step)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ProvingError("non_canonical_json_value") from error


def _sha256_json(value: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical_json(value)).hexdigest()}"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def _mapping(value: Any, reason: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail(reason)
    return dict(value)


def _list(value: Any, reason: str) -> list[Any]:
    if not isinstance(value, list):
        _fail(reason)
    return value


def _text(value: Any, reason: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(reason)
    return value


def _integer(value: Any, reason: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        _fail(reason)
    return value


def _path(value: Mapping[str, Any], keys: Sequence[str], reason: str) -> Any:
    current: Any = value
    for key in keys:
        if not isinstance(current, Mapping) or key not in current:
            _fail(reason)
        current = current[key]
    return current


def _require_equal(actual: Any, expected: Any, reason: str) -> None:
    if actual != expected:
        _fail(reason)


def _git_oid(value: Any, reason: str) -> str:
    text = _text(value, reason)
    if GIT_OID_RE.fullmatch(text) is None:
        _fail(reason)
    return text


def _normalize_changed_paths(value: Any, reason: str) -> list[str]:
    raw = _list(value, reason)
    paths: list[str] = []
    for item in raw:
        path = item.get("path") if isinstance(item, Mapping) else item
        if not isinstance(path, str):
            _fail(reason)
        normalized = path.replace("\\", "/").strip()
        if (
            not normalized
            or normalized.startswith("/")
            or ".." in normalized.split("/")
            or not normalized.startswith(FIXTURE_ROOT)
        ):
            _fail(reason)
        paths.append(normalized)
    if len(paths) != len(set(paths)):
        _fail(reason)
    return paths


def _target_plugin_packet(config: ProvingConfig | None = None) -> dict[str, Any]:
    packet = {
        "schema_version": "spiritos-target-plugin/v1",
        "id": "lumacart",
        "fixture_root": FIXTURE_ROOT,
        "selected_prompt_id": PROMPT_ID,
        "selected_context_id": CONTEXT_ID,
        "execution_profile": "coder-10",
    }
    if config is not None:
        packet.update(
            {
                "repository_id": config.expected_repository_id,
                "worktree_id": config.expected_worktree_id,
                "source_head": config.expected_source_head,
            }
        )
    return packet


def _normalize_origin(raw: str, *, role: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(raw.strip())
    except ValueError as error:
        raise ProvingError(f"{role}_origin_invalid") from error
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        _fail(f"{role}_origin_invalid")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        _fail(f"{role}_origin_contains_forbidden_components")
    if parsed.path not in {"", "/"}:
        _fail(f"{role}_origin_path_forbidden")
    if parsed.scheme == "http" and parsed.hostname not in {
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        _fail(f"{role}_origin_plain_http_must_be_loopback")
    host = f"[{parsed.hostname}]" if ":" in parsed.hostname else parsed.hostname
    try:
        parsed_port = parsed.port
    except ValueError as error:
        raise ProvingError(f"{role}_origin_invalid") from error
    default_port = 80 if parsed.scheme == "http" else 443
    port = f":{parsed_port}" if parsed_port is not None and parsed_port != default_port else ""
    return f"{parsed.scheme}://{host}{port}"


@dataclasses.dataclass(frozen=True, slots=True)
class RecoveryExpectation:
    failed_provider: str
    failed_model: str
    replacement_provider: str
    replacement_model: str


@dataclasses.dataclass(frozen=True, slots=True)
class ProvingConfig:
    source_origin: str
    next_origin: str
    proposal_id: str
    task_file: Path
    output: Path
    timeout_seconds: float
    recovery: RecoveryExpectation
    expected_source_head: str
    expected_repository_id: str
    expected_worktree_id: str


@dataclasses.dataclass(frozen=True, slots=True)
class HttpExchange:
    ordinal: int
    service: str
    method: str
    path: str
    status: int
    response_bytes: int
    response_sha256: str
    request_sha256: str
    sensitive_request: bool
    _attestation_tag: str = dataclasses.field(repr=False)

    def to_receipt(self) -> dict[str, Any]:
        return {
            "ordinal": self.ordinal,
            "service": self.service,
            "method": self.method,
            "path": self.path,
            "status": self.status,
            "response_bytes": self.response_bytes,
            "response_sha256": self.response_sha256,
            "request_sha256": self.request_sha256,
            "sensitive_request": self.sensitive_request,
        }


@dataclasses.dataclass(frozen=True, slots=True)
class ProductionRunAttestation:
    """Opaque, client-bound proof that the canonical HTTP sequence occurred."""

    schema_version: str
    transcript_sha256: str
    binding_sha256: str
    exchange_count: int
    _attestation_mac: str = dataclasses.field(repr=False)

    def to_receipt(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "transcript_sha256": self.transcript_sha256,
            "binding_sha256": self.binding_sha256,
            "exchange_count": self.exchange_count,
            "client_verified": True,
        }


@dataclasses.dataclass(slots=True)
class RunResult:
    summary: dict[str, Any]
    approved_diff: str = dataclasses.field(repr=False)
    prompt_packet_diff: str = dataclasses.field(repr=False)
    backup_manifest: str
    source_commit: str
    repository_identity: dict[str, Any]
    target_plugin_identity: dict[str, Any]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        del req, fp, code, msg, headers, newurl
        return None


class ProductionHttpClient:
    """Bounded JSON client with a private cookie jar and redirects disabled."""

    production_http = True

    def __init__(self, config: ProvingConfig):
        self._origins = {
            "source": config.source_origin,
            "next": config.next_origin,
        }
        self._timeout = config.timeout_seconds
        self._proposal_id = config.proposal_id
        self._csrf: str | None = None
        self._session_cookie_observed = False
        self._retired_session_cookie: tuple[str, str] | None = None
        self._retired_session_status_verified = False
        self._attestation_key = os.urandom(32)
        self._issued_attestation: ProductionRunAttestation | None = None
        self._cookies = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            _NoRedirect(),
            urllib.request.HTTPCookieProcessor(self._cookies),
            urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        )
        self._production_opener = self._opener
        self.exchanges: list[HttpExchange] = []

    def _exchange_tag(self, public: Mapping[str, Any]) -> str:
        return hmac.new(
            self._attestation_key,
            _canonical_json(public),
            hashlib.sha256,
        ).hexdigest()

    def bind_csrf(self, value: str) -> None:
        if not value or self._csrf is not None:
            _fail("operator_session_csrf_binding_invalid")
        self._csrf = value

    def cookie_values(self) -> list[str]:
        return [cookie.value for cookie in self._cookies if cookie.value]

    def confirm_session_cookie_binding(self) -> list[str]:
        cookies = list(self._cookies)
        if (
            len(cookies) != 1
            or cookies[0].name != OPERATOR_COOKIE_NAME
            or not cookies[0].value
            or self._session_cookie_observed
        ):
            _fail("operator_session_cookie_binding_invalid")
        self._session_cookie_observed = True
        self._retired_session_cookie = (cookies[0].name, cookies[0].value)
        return [cookies[0].value]

    def json(
        self,
        service: str,
        method: str,
        path: str,
        body: Mapping[str, Any] | None = None,
        *,
        sensitive_request: bool = False,
        _retired_cookie: tuple[str, str] | None = None,
    ) -> dict[str, Any]:
        if service not in self._origins or not path.startswith("/") or "//" in path:
            _fail("http_request_target_invalid", step=path)
        url = self._origins[service] + path
        data = _canonical_json(dict(body)) if body is not None else None
        headers = {
            "Accept": "application/json",
            "Cache-Control": "no-store",
            "User-Agent": "SpiritOS-Foundation-R1-Prover/1",
        }
        if service == "next":
            # Next's operator boundary requires a same-origin request on session
            # creation and a cookie-bound CSRF value on every later mutation.
            headers["Origin"] = self._origins["next"]
            if self._csrf is not None and method in {"POST", "PUT", "PATCH", "DELETE"}:
                headers["X-SpiritOS-CSRF"] = self._csrf
        if _retired_cookie is not None:
            if (
                service != "next"
                or method != "GET"
                or path != "/v1/operator/session"
                or _retired_cookie != self._retired_session_cookie
            ):
                _fail("retired_operator_session_probe_invalid")
            headers["Cookie"] = f"{_retired_cookie[0]}={_retired_cookie[1]}"
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        status = 0
        response_headers: Mapping[str, str]
        try:
            response = self._opener.open(request, timeout=self._timeout)
            status = int(response.status)
            response_headers = response.headers
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as error:
            status = int(error.code)
            response_headers = error.headers
            raw = error.read(MAX_RESPONSE_BYTES + 1)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            del error
            _fail("http_transport_failed", step=f"{method} {path}")
        if len(raw) > MAX_RESPONSE_BYTES:
            _fail("http_response_too_large", step=f"{method} {path}")
        exchange_public = {
            "ordinal": len(self.exchanges) + 1,
            "service": service,
            "method": method,
            "path": path,
            "status": status,
            "response_bytes": len(raw),
            "response_sha256": hashlib.sha256(raw).hexdigest(),
            "request_sha256": _sha256_json(
                {
                    "body_sha256": hashlib.sha256(data or b"").hexdigest(),
                    "retired_cookie_sha256": (
                        _sha256_text(_retired_cookie[1])
                        if _retired_cookie is not None
                        else None
                    ),
                }
            ),
            "sensitive_request": sensitive_request,
        }
        self.exchanges.append(
            HttpExchange(
                **exchange_public,
                _attestation_tag=self._exchange_tag(exchange_public),
            )
        )
        content_type = str(response_headers.get("content-type", "")).lower()
        if "application/json" not in content_type:
            _fail("http_response_not_json", step=f"{method} {path}")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            _fail("http_response_json_invalid", step=f"{method} {path}")
        if not isinstance(payload, dict):
            _fail("http_response_object_required", step=f"{method} {path}")
        if not 200 <= status < 300:
            reason = _safe_reason_code(payload) or f"http_status_{status}"
            _fail(reason, step=f"{method} {path}")
        return payload

    def verify_retired_session_status(self) -> str:
        if self._retired_session_cookie is None or self._retired_session_status_verified:
            _fail("retired_operator_session_probe_invalid")
        if list(self._cookies):
            _fail("operator_session_cookie_not_cleared")
        payload = self.json(
            "next",
            "GET",
            "/v1/operator/session",
            _retired_cookie=self._retired_session_cookie,
        )
        if payload != {"status": "revoked"}:
            _fail("retired_operator_session_not_revoked")
        self._retired_session_status_verified = True
        return self.exchanges[-1].response_sha256

    def issue_run_attestation(
        self,
        *,
        first: RunResult,
        second: RunResult,
        undo: Mapping[str, Any],
        reset: Mapping[str, Any],
        operator_hash: str,
        revocation_response_sha256: str,
        retired_session_probe_response_sha256: str,
    ) -> ProductionRunAttestation:
        """Seal exactly one complete production transcript.

        A caller cannot choose a shorter exchange sequence.  The expected
        routes are derived from the two validated runs, and each exchange must
        carry the private tag created only by :meth:`json` after an HTTP
        response was read.
        """

        if type(self) is not ProductionHttpClient or self._opener is not self._production_opener:
            _fail("production_http_client_integrity_invalid")
        if self._issued_attestation is not None:
            _fail("production_run_attestation_already_issued")
        expected = _expected_exchange_sequence(self._proposal_id, first, second)
        if not expected or len(self.exchanges) != len(expected):
            _fail("production_http_transcript_sequence_invalid")
        for exchange, route in zip(self.exchanges, expected, strict=True):
            if (exchange.service, exchange.method, exchange.path) != route:
                _fail("production_http_transcript_sequence_invalid")
            if not 200 <= exchange.status < 300 or exchange.response_bytes <= 0:
                _fail("production_http_transcript_exchange_invalid")
            if exchange._attestation_tag != self._exchange_tag(exchange.to_receipt()):
                _fail("production_http_transcript_attestation_invalid")
        if (
            self._csrf is None
            or not self._session_cookie_observed
            or not self._retired_session_status_verified
            or list(self._cookies)
        ):
            _fail("production_http_session_binding_missing")
        if (
            self.exchanges[-2].response_sha256 != revocation_response_sha256
            or self.exchanges[-1].response_sha256
            != retired_session_probe_response_sha256
        ):
            _fail("production_http_revocation_binding_invalid")
        binding = _run_attestation_binding(
            first=first,
            second=second,
            undo=undo,
            reset=reset,
            operator_hash=operator_hash,
            revocation_response_sha256=revocation_response_sha256,
            retired_session_probe_response_sha256=(
                retired_session_probe_response_sha256
            ),
        )
        transcript_sha256 = _sha256_json(
            [exchange.to_receipt() for exchange in self.exchanges]
        )
        binding_sha256 = _sha256_json(binding)
        mac_material = {
            "schema_version": "spiritos-production-http-run-attestation/v1",
            "transcript_sha256": transcript_sha256,
            "binding_sha256": binding_sha256,
            "exchange_count": len(self.exchanges),
        }
        attestation = ProductionRunAttestation(
            **mac_material,
            _attestation_mac=self._exchange_tag(mac_material),
        )
        self._issued_attestation = attestation
        return attestation

    def verify_run_attestation(
        self,
        attestation: ProductionRunAttestation,
        *,
        binding: Mapping[str, Any],
    ) -> None:
        if (
            type(attestation) is not ProductionRunAttestation
            or attestation is not self._issued_attestation
        ):
            _fail("production_run_attestation_missing")
        public = attestation.to_receipt()
        public.pop("client_verified")
        if (
            attestation.transcript_sha256
            != _sha256_json([exchange.to_receipt() for exchange in self.exchanges])
            or attestation.binding_sha256 != _sha256_json(binding)
            or attestation.exchange_count != len(self.exchanges)
            or attestation._attestation_mac != self._exchange_tag(public)
        ):
            _fail("production_run_attestation_invalid")


def _safe_reason_code(payload: Mapping[str, Any]) -> str | None:
    for candidate in (payload, payload.get("detail")):
        if isinstance(candidate, Mapping):
            value = candidate.get("reason_code") or candidate.get("error_code")
            if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,160}", value):
                return value
    return None


def _validate_plugin_identity(identity: Any, source_head: str | None = None) -> dict[str, Any]:
    value = _mapping(identity, "target_plugin_identity_missing")
    expected = {
        "schema_version": "spiritos-target-plugin/v1",
        "plugin_id": "lumacart",
        "fixture_root": FIXTURE_ROOT,
        "selected_prompt_id": PROMPT_ID,
        "selected_context_id": CONTEXT_ID,
        "execution_profile": "coder-10",
    }
    for key, expected_value in expected.items():
        _require_equal(value.get(key), expected_value, f"target_plugin_identity_{key}_mismatch")
    actual_head = _git_oid(value.get("source_head"), "target_plugin_source_head_invalid")
    if source_head is not None:
        _require_equal(actual_head, source_head, "target_plugin_source_head_mismatch")
    for key in ("repository_id", "worktree_id", "workspace_root", "branch", "state_namespace", "result_identity"):
        _text(value.get(key), f"target_plugin_{key}_missing")
    actions = _list(value.get("allowed_actions"), "target_plugin_allowed_actions_missing")
    if set(actions) != {"propose", "approve", "execute", "verify", "record-evidence"}:
        _fail("target_plugin_allowed_actions_invalid")
    return value


def _validate_prompt_packet(payload: Mapping[str, Any], task_id: str) -> str:
    _require_equal(payload.get("status"), "preview_ready", "prompt_packet_not_preview_ready")
    _require_equal(payload.get("selected_prompt_id"), PROMPT_ID, "prompt_packet_prompt_mismatch")
    if payload.get("coder_blocked") is not False or payload.get("already_satisfied") is not False:
        _fail("prompt_packet_not_model_diff_candidate")
    proposed = _text(payload.get("proposed_diff"), "prompt_packet_diff_missing")
    if payload.get("provider_call_made") is not True or payload.get("provider_call_authorized") is not True:
        _fail("prompt_packet_provider_call_not_proven")
    context = _mapping(payload.get("canonical_context_broker"), "prompt_packet_context_missing")
    if context.get("canonical") is not True or context.get("go_eligible") is not True:
        _fail("prompt_packet_context_not_go_eligible")
    _text(context.get("canonical_report_hash"), "prompt_packet_context_hash_missing")
    diagnostics = _mapping(payload.get("coder_diagnostics"), "prompt_packet_diagnostics_missing")
    expected = {
        "transport_kind": "canonical_litellm_router",
        "provider_call_made": True,
        "provider_call_authorized": True,
        "generation_source": "model",
        "terminal_proof_eligible": True,
    }
    for key, value in expected.items():
        _require_equal(diagnostics.get(key), value, f"prompt_packet_{key}_invalid")
    if sorted(_normalize_changed_paths(payload.get("changed_files"), "prompt_packet_changed_files_invalid")) != PROMPT1_FILES:
        _fail("prompt_packet_prompt1_scope_invalid")
    receipt = _mapping(payload.get("fip0_truth_receipt"), "prompt_packet_truth_receipt_missing")
    _text(receipt.get("run_id"), "prompt_packet_truth_run_id_missing")
    if receipt.get("task_id") not in {None, "", task_id}:
        _fail("prompt_packet_truth_task_mismatch")
    return proposed


def _validate_cartographer_proposal_collection(
    payload: Mapping[str, Any],
    *,
    proposal_id: str,
) -> dict[str, Any]:
    expected_collection = {
        "status": "observing",
        "write_actions_enabled": False,
        "authority_granted": False,
        "apply_allowed": False,
        "commit_allowed": False,
        "push_allowed": False,
        "actions_taken": False,
        "transition_audit_complete": True,
    }
    for key, value in expected_collection.items():
        _require_equal(
            payload.get(key),
            value,
            f"cartographer_proposal_collection_{key}_invalid",
        )
    proposals = _list(payload.get("proposals"), "cartographer_proposal_collection_missing")
    exact = [
        _mapping(item, "cartographer_proposal_invalid")
        for item in proposals
        if isinstance(item, Mapping) and item.get("proposal_id") == proposal_id
    ]
    if len(exact) != 1:
        _fail("cartographer_exact_proposal_identity_invalid")
    proposal = exact[0]
    expected = {
        "proposal_id": proposal_id,
        "persisted": True,
        "generated": False,
        "status": "pending_review",
        "type": "coding_target_selection",
        "component": "coding-foundation",
        "proposed_files": [TARGET],
        "warnings": [],
        "requires_approval": True,
    }
    for key, value in expected.items():
        _require_equal(proposal.get(key), value, f"cartographer_proposal_{key}_invalid")
    fingerprint = _text(
        proposal.get("fingerprint"),
        "cartographer_proposal_fingerprint_missing",
    )
    if CARTOGRAPHER_PROPOSAL_FINGERPRINT_RE.fullmatch(fingerprint) is None:
        _fail("cartographer_proposal_fingerprint_invalid")
    approved_diff = proposal.get("approved_diff") or proposal.get("diff_preview") or ""
    if not isinstance(approved_diff, str):
        _fail("cartographer_proposal_selection_content_invalid")
    selection_content = {
        "approved_diff": approved_diff,
        "proposal_fingerprint": fingerprint,
        "proposal_id": proposal_id,
        "proposed_files": [TARGET],
        "target": TARGET,
    }
    selection_context = json.dumps(
        {"consumer": CONSUMER, "proposal_id": proposal_id},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    selection_content_sha256 = hashlib.sha256(
        json.dumps(
            {"content": selection_content, "context": selection_context},
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    transitions = [
        _mapping(item, "cartographer_proposal_transition_invalid")
        for item in _list(
            proposal.get("transitions"),
            "cartographer_proposal_transitions_missing",
        )
    ]
    state_order = {"detected": 0, "drafted": 1, "pending_review": 2}
    transition_states: list[str] = []
    for transition in transitions:
        status = _text(
            transition.get("status"),
            "cartographer_proposal_transition_status_missing",
        )
        if status not in state_order:
            _fail("cartographer_proposal_transition_status_invalid")
        transition_states.append(status)
        timestamp = _text(
            transition.get("timestamp"),
            "cartographer_proposal_transition_timestamp_missing",
        )
        try:
            parsed_timestamp = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            )
        except ValueError:
            _fail("cartographer_proposal_transition_timestamp_invalid")
        if parsed_timestamp.tzinfo is None:
            _fail("cartographer_proposal_transition_timestamp_invalid")
        _text(
            transition.get("actor"),
            "cartographer_proposal_transition_actor_missing",
        )
    if (
        not transition_states
        or transition_states[-1] != "pending_review"
        or any(
            state_order[current] < state_order[previous]
            for previous, current in zip(transition_states, transition_states[1:])
        )
    ):
        _fail("cartographer_proposal_transition_history_invalid")
    return {
        "proposal_id": proposal_id,
        "persisted": True,
        "generated": False,
        "status": "pending_review",
        "type": "coding_target_selection",
        "component": "coding-foundation",
        "proposed_files": [TARGET],
        "fingerprint": fingerprint,
        "selection_content_sha256": selection_content_sha256,
        "warnings": [],
        "transition_count": len(transitions),
        "last_transition_status": "pending_review",
    }


def _validate_cartographer_selection_binding(
    proposal: Mapping[str, Any],
    consumption: Mapping[str, Any],
) -> None:
    expected = _text(
        proposal.get("selection_content_sha256"),
        "cartographer_proposal_selection_content_hash_missing",
    )
    actual = _text(
        consumption.get("content_hash"),
        "cartographer_selection_content_hash_missing",
    )
    if not _is_sha256(expected) or not _is_sha256(actual):
        _fail("cartographer_selection_content_hash_invalid")
    _require_equal(
        actual,
        expected,
        "cartographer_selection_proposal_binding_mismatch",
    )


def _validate_initial_task(
    payload: Mapping[str, Any],
    *,
    proposal_id: str,
    selection_id: str,
) -> tuple[str, dict[str, Any]]:
    task = _mapping(payload.get("task"), "task_create_task_missing")
    task_id = _text(task.get("id"), "task_create_id_missing")
    state = _mapping(payload.get("coding_orchestrator"), "task_create_orchestrator_missing")
    _require_equal(state.get("schema_version"), ORCHESTRATOR_SCHEMA, "task_create_orchestrator_schema_invalid")
    if state.get("authoritative") is not True or state.get("task_id") != task_id:
        _fail("task_create_orchestrator_not_authoritative")
    transfer = _mapping(state.get("cartographer_transfer"), "task_create_cartographer_transfer_missing")
    expected = {
        "proposal_id": proposal_id,
        "selection_id": selection_id,
        "selection_approval_id": selection_id,
        "consumer": CONSUMER,
        "target": TARGET,
        "task_id": task_id,
        "run_id": state.get("run_id"),
    }
    for key, value in expected.items():
        _require_equal(transfer.get(key), value, f"task_create_cartographer_{key}_mismatch")
    _text(transfer.get("transfer_event_id"), "task_create_transfer_event_missing")
    if transfer.get("downstream_consumer_invocation_id") is not None:
        _fail("task_create_transfer_prematurely_acknowledged")
    return task_id, state


def _validate_runtime_boundary(state: Mapping[str, Any]) -> dict[str, Any]:
    outputs = [_mapping(item, "runtime_output_invalid") for item in _list(state.get("runtime_outputs"), "runtime_outputs_missing")]
    acknowledgements = [
        _mapping(item, "runtime_acknowledgement_invalid")
        for item in _list(state.get("runtime_acknowledgements"), "runtime_acknowledgements_missing")
    ]
    consumptions = [
        _mapping(item, "runtime_consumption_invalid")
        for item in _list(state.get("runtime_consumptions"), "runtime_consumptions_missing")
    ]
    required = _list(state.get("required_output_ids"), "runtime_required_outputs_missing")
    output_by_id: dict[str, dict[str, Any]] = {}
    for output in outputs:
        _require_equal(output.get("schema_version"), "coding.runtime-lane-output/v1", "runtime_output_schema_invalid")
        output_id = _text(output.get("output_id"), "runtime_output_id_missing")
        if output_id in output_by_id:
            _fail("runtime_output_id_duplicate")
        _text(output.get("lane_id"), "runtime_output_lane_missing")
        _text(output.get("contract_version"), "runtime_output_contract_missing")
        _text(output.get("producer_invocation_id"), "runtime_output_producer_missing")
        payload = _mapping(output.get("payload"), "runtime_output_payload_invalid")
        _require_equal(output.get("artifact_hash"), _sha256_json(payload), "runtime_output_artifact_hash_mismatch")
        output_by_id[output_id] = output
    if set(required) != set(output_by_id) or len(required) != len(set(required)):
        _fail("runtime_required_output_set_invalid")
    ack_by_output: dict[str, dict[str, Any]] = {}
    ack_ids: set[str] = set()
    for acknowledgement in acknowledgements:
        _require_equal(
            acknowledgement.get("schema_version"),
            "coding.runtime-lane-acknowledgement/v1",
            "runtime_acknowledgement_schema_invalid",
        )
        output_id = _text(acknowledgement.get("output_id"), "runtime_acknowledgement_output_missing")
        output = output_by_id.get(output_id)
        if output is None or output_id in ack_by_output:
            _fail("runtime_acknowledgement_output_invalid")
        acknowledgement_id = _text(acknowledgement.get("acknowledgement_id"), "runtime_acknowledgement_id_missing")
        if acknowledgement_id in ack_ids:
            _fail("runtime_acknowledgement_id_duplicate")
        ack_ids.add(acknowledgement_id)
        for key in ("lane_id", "contract_version", "producer_invocation_id", "artifact_hash"):
            _require_equal(acknowledgement.get(key), output.get(key), "runtime_acknowledgement_binding_mismatch")
        consumer = _text(acknowledgement.get("consumer_invocation_id"), "runtime_acknowledgement_consumer_missing")
        if consumer == output.get("producer_invocation_id"):
            _fail("runtime_acknowledgement_not_independent")
        _text(acknowledgement.get("consumer_version"), "runtime_consumer_version_missing")
        ack_by_output[output_id] = acknowledgement
    consumed_outputs: set[str] = set()
    consumption_ids: set[str] = set()
    for consumption in consumptions:
        _require_equal(
            consumption.get("schema_version"),
            "coding.runtime-lane-consumption/v1",
            "runtime_consumption_schema_invalid",
        )
        output_id = _text(consumption.get("output_id"), "runtime_consumption_output_missing")
        output = output_by_id.get(output_id)
        acknowledgement = ack_by_output.get(output_id)
        if output is None or acknowledgement is None or output_id in consumed_outputs:
            _fail("runtime_consumption_output_invalid")
        consumed_outputs.add(output_id)
        consumption_id = _text(consumption.get("consumption_id"), "runtime_consumption_id_missing")
        if consumption_id in consumption_ids:
            _fail("runtime_consumption_id_duplicate")
        consumption_ids.add(consumption_id)
        _require_equal(
            consumption.get("acknowledgement_id"),
            acknowledgement.get("acknowledgement_id"),
            "runtime_consumption_acknowledgement_mismatch",
        )
        for key in ("lane_id", "contract_version", "artifact_hash"):
            _require_equal(consumption.get(key), output.get(key), "runtime_consumption_binding_mismatch")
        for key in ("consumer_version", "consumer_invocation_id"):
            _require_equal(consumption.get(key), acknowledgement.get(key), "runtime_consumption_binding_mismatch")
    if set(output_by_id) != set(ack_by_output) or set(output_by_id) != consumed_outputs:
        _fail("runtime_output_consumption_incomplete")
    return {
        "output_ids": sorted(output_by_id),
        "acknowledgement_ids": sorted(ack_ids),
        "consumption_ids": sorted(consumption_ids),
        "lanes": sorted(str(item.get("lane_id")) for item in outputs),
        "all_required_outputs_consumed": True,
    }


def _validate_recovery(
    state: Mapping[str, Any],
    *,
    expectation: RecoveryExpectation,
    selected_model: Mapping[str, Any],
) -> dict[str, Any]:
    records = _list(state.get("recovery_lineage"), "controlled_recovery_missing")
    if len(records) != 1:
        _fail("controlled_recovery_record_count_invalid")
    record = _mapping(records[0], "controlled_recovery_record_invalid")
    unsigned = dict(record)
    recorded_hash = unsigned.pop("record_sha256", None)
    if recorded_hash is not None:
        _require_equal(recorded_hash, _sha256_json(unsigned), "controlled_recovery_hash_mismatch")
    expected_top = {
        "schema_version": "coding.controlled-recovery/v1",
        "state": "completed",
        "run_id": state.get("run_id"),
        "task_id": state.get("task_id"),
        "proof_eligible": True,
        "claim_ceiling_impact": "recovered_via_declared_fallback_only",
    }
    for key, value in expected_top.items():
        _require_equal(record.get(key), value, f"controlled_recovery_{key}_invalid")
    recovery_id = _text(record.get("recovery_id"), "controlled_recovery_id_missing")
    failure = _mapping(record.get("failure"), "controlled_recovery_failure_missing")
    failed = _mapping(failure.get("participant"), "controlled_recovery_failed_participant_missing")
    decision = _mapping(record.get("decision"), "controlled_recovery_decision_missing")
    replacement = _mapping(record.get("replacement"), "controlled_recovery_replacement_missing")
    replacement_participant = _mapping(
        replacement.get("participant"),
        "controlled_recovery_replacement_participant_missing",
    )
    if failed.get("passed") is not False or not _text(
        failed.get("error_code"), "controlled_recovery_failure_code_missing"
    ):
        _fail("controlled_recovery_failure_not_proven")
    expected_failed = {
        "provider": expectation.failed_provider,
        "model": expectation.failed_model,
        "run_id": state.get("run_id"),
        "task_id": state.get("task_id"),
    }
    for key, value in expected_failed.items():
        _require_equal(failed.get(key), value, f"controlled_recovery_failed_{key}_mismatch")
    _require_equal(decision.get("kind"), "fallback", "controlled_recovery_decision_not_fallback")
    policy = _mapping(decision.get("policy"), "controlled_recovery_policy_missing")
    if policy.get("allow_fallback") is not True:
        _fail("controlled_recovery_fallback_not_authorized")
    routes = _list(policy.get("allowed_replacement_routes"), "controlled_recovery_routes_missing")
    expected_route = {
        "provider": expectation.replacement_provider,
        "model": expectation.replacement_model,
    }
    if routes != [expected_route]:
        _fail("controlled_recovery_replacement_route_not_exact")
    for key, value in expected_route.items():
        _require_equal(replacement.get(key), value, f"controlled_recovery_replacement_{key}_mismatch")
        _require_equal(
            replacement_participant.get(key),
            value,
            f"controlled_recovery_participant_{key}_mismatch",
        )
    if replacement.get("outcome") != "succeeded" or replacement_participant.get("passed") is not True:
        _fail("controlled_recovery_replacement_not_successful")
    if dict(replacement_participant) != dict(selected_model):
        _fail("controlled_recovery_selected_model_mismatch")
    if (
        failed.get("attempt_id") == replacement_participant.get("attempt_id")
        or failed.get("invocation_id") == replacement_participant.get("invocation_id")
        or failed.get("output_id") == replacement_participant.get("output_id")
    ):
        _fail("controlled_recovery_replacement_identity_reused")
    events = [
        _mapping(failure.get("event"), "controlled_recovery_failure_event_missing"),
        _mapping(decision.get("event"), "controlled_recovery_decision_event_missing"),
        _mapping(replacement.get("start_event"), "controlled_recovery_start_event_missing"),
        _mapping(replacement.get("outcome_event"), "controlled_recovery_outcome_event_missing"),
    ]
    event_ids = [_text(item.get("event_id"), "controlled_recovery_event_id_missing") for item in events]
    if len(event_ids) != len(set(event_ids)):
        _fail("controlled_recovery_event_identity_reused")
    if any(item.get("run_id") != state.get("run_id") or item.get("task_id") != state.get("task_id") for item in events):
        _fail("controlled_recovery_event_run_mismatch")
    return {
        "recovery_id": recovery_id,
        "decision": "fallback",
        "failure": {
            "provider": failed["provider"],
            "model": failed["model"],
            "invocation_id": failed["invocation_id"],
            "error_code": failed["error_code"],
            "error_message_sha256": _sha256_text(str(failed.get("error_message") or "")),
        },
        "replacement": {
            "provider": replacement_participant["provider"],
            "model": replacement_participant["model"],
            "invocation_id": replacement_participant["invocation_id"],
            "output_id": replacement_participant["output_id"],
        },
        "claim_ceiling_impact": record["claim_ceiling_impact"],
        "proof_eligible": True,
    }


def _validate_cartographer_consumption(
    state: Mapping[str, Any],
    *,
    proposal_id: str,
    selection_id: str,
    source_head: str,
    selected_model: Mapping[str, Any],
) -> dict[str, Any]:
    transfer = _mapping(state.get("cartographer_transfer"), "cartographer_transfer_missing")
    finalization = _mapping(
        state.get("cartographer_finalization"),
        "cartographer_finalization_missing",
    )
    consumer_invocation_id = _text(
        transfer.get("downstream_consumer_invocation_id"),
        "cartographer_downstream_consumer_invocation_missing",
    )
    if consumer_invocation_id != selected_model.get("invocation_id"):
        _fail("cartographer_downstream_consumer_not_real_model_invocation")
    expected = {
        "proposal_id": proposal_id,
        "selection_id": selection_id,
        "selection_approval_id": selection_id,
        "consumer": CONSUMER,
        "target": TARGET,
        "task_id": state.get("task_id"),
        "run_id": state.get("run_id"),
        "downstream_consumer_invocation_id": consumer_invocation_id,
    }
    for key, value in expected.items():
        _require_equal(transfer.get(key), value, f"cartographer_transfer_{key}_mismatch")
    transfer_event = _text(transfer.get("transfer_event_id"), "cartographer_transfer_event_missing")
    provenance = _mapping(transfer.get("provenance"), "cartographer_transfer_provenance_missing")
    _require_equal(provenance.get("source_head"), source_head, "cartographer_transfer_source_head_mismatch")
    content_hash = _text(
        provenance.get("content_hash"),
        "cartographer_transfer_content_hash_missing",
    )
    if not _is_sha256(content_hash):
        _fail("cartographer_transfer_content_hash_invalid")
    for key in ("context", "preview_id"):
        _text(provenance.get(key), f"cartographer_transfer_{key}_missing")
    _require_equal(finalization.get("state"), "consumed", "cartographer_finalization_state_invalid")
    acknowledgement = _mapping(
        finalization.get("downstream_acknowledgement"),
        "cartographer_acknowledgement_missing",
    )
    authority = _mapping(finalization.get("authority_receipt"), "cartographer_authority_receipt_missing")
    if acknowledgement.get("consumed") is not True or authority.get("state") != "consumed":
        _fail("cartographer_consumption_not_finalized")
    expected_ack = {
        "schema_version": "cartographer.downstream-acknowledgement/v2",
        "transfer_event_id": transfer_event,
        "consumer_invocation_id": consumer_invocation_id,
        "consumer_output_id": selected_model.get("output_id"),
        "consumer_output_sha256": selected_model.get("output_sha256"),
        "consumer_artifact_sha256": selected_model.get("artifact_sha256"),
        "consumer_completed_at": selected_model.get("completed_at"),
        "consumer_passed": True,
        "proposal_id": proposal_id,
        "selection_id": selection_id,
        "task_id": state.get("task_id"),
        "run_id": state.get("run_id"),
    }
    for key, value in expected_ack.items():
        _require_equal(acknowledgement.get(key), value, f"cartographer_ack_{key}_mismatch")
    return {
        "proposal_id": proposal_id,
        "selection_id": selection_id,
        "selection_generation": transfer.get("selection_generation"),
        "transfer_event_id": transfer_event,
        "consumer_invocation_id": consumer_invocation_id,
        "acknowledgement_id": _text(
            acknowledgement.get("acknowledgement_id"),
            "cartographer_acknowledgement_id_missing",
        ),
        "content_hash": content_hash,
        "authority_state": authority["state"],
    }


def _extract_persisted_proposal(
    state: Mapping[str, Any],
    *,
    task_id: str,
    proposal_id: str,
    selection_id: str,
    expectation: RecoveryExpectation,
) -> tuple[str, dict[str, Any]]:
    _require_equal(state.get("schema_version"), ORCHESTRATOR_SCHEMA, "proposal_orchestrator_schema_invalid")
    if state.get("authoritative") is not True or state.get("task_id") != task_id:
        _fail("proposal_orchestrator_not_authoritative")
    run_id = _text(state.get("run_id"), "proposal_run_id_missing")
    proposal = _mapping(state.get("target_plugin_proposal"), "target_plugin_proposal_missing")
    if proposal.get("schema_version") != "coding.target-plugin-proposal/v1":
        _fail("target_plugin_proposal_schema_invalid")
    if proposal.get("task_id") != task_id or proposal.get("run_id") != run_id:
        _fail("target_plugin_proposal_run_mismatch")
    _require_equal(proposal.get("status"), "ready_for_approval_preview", "target_plugin_proposal_not_ready")
    _require_equal(proposal.get("selected_prompt_id"), PROMPT_ID, "target_plugin_proposal_prompt_mismatch")
    _require_equal(proposal.get("selected_context_id"), CONTEXT_ID, "target_plugin_proposal_context_mismatch")
    _require_equal(proposal.get("target"), TARGET, "target_plugin_proposal_target_mismatch")
    source_head = _git_oid(proposal.get("source_head"), "target_plugin_proposal_source_head_invalid")
    sealed = dict(proposal)
    recorded_binding = sealed.pop("proposal_binding_sha256", None)
    _require_equal(recorded_binding, _sha256_json(sealed), "target_plugin_proposal_hash_mismatch")
    identity = _validate_plugin_identity(proposal.get("target_plugin_identity"), source_head)
    changed_files = _normalize_changed_paths(proposal.get("changed_files"), "target_plugin_proposal_changed_files_invalid")
    if sorted(changed_files) != PROMPT1_FILES:
        _fail("target_plugin_proposal_prompt1_scope_invalid")
    output_id = _text(proposal.get("runtime_output_id"), "target_plugin_runtime_output_id_missing")
    outputs = [_mapping(item, "target_plugin_runtime_output_invalid") for item in _list(state.get("runtime_outputs"), "target_plugin_runtime_outputs_missing")]
    matches = [item for item in outputs if item.get("output_id") == output_id]
    if len(matches) != 1:
        _fail("target_plugin_persisted_runtime_output_missing")
    output = matches[0]
    _require_equal(output.get("lane_id"), "coder", "target_plugin_runtime_output_lane_invalid")
    output_payload = _mapping(output.get("payload"), "target_plugin_runtime_payload_invalid")
    approved_diff = _text(output_payload.get("approved_diff"), "target_plugin_persisted_diff_missing")
    output_changed = _normalize_changed_paths(output_payload.get("changed_files"), "target_plugin_output_changed_files_invalid")
    if output_changed != changed_files:
        _fail("target_plugin_output_scope_mismatch")
    approved_diff_sha = _sha256_text(approved_diff)
    _require_equal(proposal.get("approved_diff_sha256"), approved_diff_sha, "target_plugin_diff_hash_mismatch")
    _require_equal(output.get("artifact_hash"), proposal.get("runtime_output_artifact_sha256"), "target_plugin_output_artifact_mismatch")
    _require_equal(output.get("artifact_hash"), _sha256_json(output_payload), "target_plugin_output_artifact_hash_invalid")
    invocations = [_mapping(item, "target_plugin_model_invocation_invalid") for item in _list(state.get("model_invocations"), "target_plugin_model_invocations_missing")]
    selected_id = _text(proposal.get("producer_model_invocation_id"), "target_plugin_producer_invocation_missing")
    selected_matches = [item for item in invocations if item.get("invocation_id") == selected_id]
    if len(selected_matches) != 1 or selected_matches[0].get("passed") is not True:
        _fail("target_plugin_selected_model_invocation_invalid")
    selected = selected_matches[0]
    if len(invocations) != 2 or sum(item.get("passed") is False for item in invocations) != 1:
        _fail("target_plugin_controlled_failure_set_invalid")
    for invocation in invocations:
        if invocation.get("run_id") != run_id or invocation.get("task_id") != task_id:
            _fail("target_plugin_model_invocation_run_mismatch")
        for key in ("attempt_id", "invocation_id", "output_id", "provider", "model", "input_sha256", "output_sha256"):
            _text(invocation.get(key), f"target_plugin_model_{key}_missing")
    provenance = _mapping(proposal.get("target_adapter_provenance"), "target_adapter_provenance_missing")
    expected_provenance = {
        "schema_version": "spiritos-target-adapter-provenance/v1",
        "plugin_id": "lumacart",
        "selected_prompt_id": PROMPT_ID,
        "transport_kind": "canonical_litellm_router",
        "configured_transport_kind": "canonical_litellm_router",
        "provider_call_made": True,
        "provider_call_authorized": True,
        "generation_source": "model",
        "terminal_proof_eligible": True,
        "provider": expectation.replacement_provider,
        "model": expectation.replacement_model,
    }
    for key, value in expected_provenance.items():
        _require_equal(provenance.get(key), value, f"target_adapter_{key}_invalid")
    for key in ("rendered_prompt_sha256", "raw_response_sha256"):
        if not _is_sha256(provenance.get(key)):
            _fail(f"target_adapter_{key}_invalid")
    calls = _list(provenance.get("calls"), "target_adapter_calls_missing")
    call_count = _integer(provenance.get("call_count"), "target_adapter_call_count_invalid", minimum=1)
    if len(calls) != call_count or not all(isinstance(item, Mapping) for item in calls):
        _fail("target_adapter_calls_invalid")
    model_output_provenance = _mapping(
        proposal.get("model_output_provenance"),
        "target_plugin_model_output_provenance_missing",
    )
    if (
        model_output_provenance.get("target_adapter_provenance") != provenance
        or model_output_provenance.get("approved_diff_sha256") != approved_diff_sha
        or model_output_provenance.get("changed_files") != changed_files
        or model_output_provenance.get("blocked") is not False
    ):
        _fail("target_plugin_model_output_provenance_invalid")
    _require_equal(selected.get("output_sha256"), _sha256_json(model_output_provenance), "target_plugin_model_output_hash_mismatch")
    _require_equal(
        selected.get("artifact_sha256"),
        _sha256_json({"proposed_diff": approved_diff, "changed_files": changed_files}),
        "target_plugin_model_artifact_hash_mismatch",
    )
    _require_equal(selected.get("output_sha256"), proposal.get("producer_model_output_sha256"), "target_plugin_producer_output_mismatch")
    _require_equal(selected.get("artifact_sha256"), proposal.get("producer_model_artifact_sha256"), "target_plugin_producer_artifact_mismatch")
    context = _mapping(proposal.get("canonical_context_report"), "target_plugin_context_report_missing")
    if context.get("canonical") is not True or context.get("go_eligible") is not True:
        _fail("target_plugin_context_not_go_eligible")
    _require_equal(context.get("canonical_report_hash"), proposal.get("context_hash"), "target_plugin_context_hash_mismatch")
    _require_equal(_sha256_json(context), proposal.get("canonical_context_report_sha256"), "target_plugin_context_report_hash_mismatch")
    recovery = _validate_recovery(state, expectation=expectation, selected_model=selected)
    cartographer = _validate_cartographer_consumption(
        state,
        proposal_id=proposal_id,
        selection_id=selection_id,
        source_head=source_head,
        selected_model=selected,
    )
    material = {
        "task_id": task_id,
        "run_id": run_id,
        "attempt_id": _text(state.get("attempt_id"), "proposal_attempt_id_missing"),
        "source_commit": source_head,
        "runtime_output_id": output_id,
        "producer_model_invocation_id": selected_id,
        "proposal_binding_sha256": recorded_binding,
        "approved_diff_sha256": approved_diff_sha,
        "changed_files": changed_files,
        "context": {
            "context_hash": proposal["context_hash"],
            "runtime_output_id": proposal.get("context_runtime_output_id"),
            "consumer_acknowledgement_id": proposal.get("context_consumer_acknowledgement_id"),
            "consumption_id": proposal.get("context_consumption_id"),
        },
        "adapter": {
            "provider": provenance["provider"],
            "model": provenance["model"],
            "transport_kind": provenance["transport_kind"],
            "rendered_prompt_sha256": provenance["rendered_prompt_sha256"],
            "raw_response_sha256": provenance["raw_response_sha256"],
            "call_count": call_count,
            "terminal_proof_eligible": True,
        },
        "cartographer": cartographer,
        "recovery": recovery,
        "target_plugin_identity": identity,
    }
    return approved_diff, material


def _validate_diff_preview(payload: Mapping[str, Any], changed_files: Sequence[str]) -> dict[str, Any]:
    expected = {
        "tool": "diff_verification_preview",
        "access_scope": "read_only_diff_preview",
        "status": "preview_ready",
        "would_apply_diff": False,
        "would_execute": False,
        "git_apply_check_ok": True,
    }
    for key, value in expected.items():
        _require_equal(payload.get(key), value, f"diff_preview_{key}_invalid")
    if _list(payload.get("blocked_reasons"), "diff_preview_blocked_reasons_missing"):
        _fail("diff_preview_blocked")
    preview_paths = _normalize_changed_paths(payload.get("changed_files"), "diff_preview_changed_files_invalid")
    if preview_paths != list(changed_files):
        _fail("diff_preview_scope_mismatch")
    limits = _mapping(payload.get("limits"), "diff_preview_limits_missing")
    if limits.get("terminal_execution_allowed") is not False:
        _fail("diff_preview_execution_authority_invalid")
    task_spec_check = _mapping(payload.get("task_spec_check"), "diff_preview_task_spec_check_missing")
    if task_spec_check.get("ok") is not True:
        _fail("diff_preview_task_spec_failed")
    checks = _list(payload.get("deterministic_checks"), "diff_preview_deterministic_checks_missing")
    for check in checks:
        item = _mapping(check, "diff_preview_deterministic_check_invalid")
        if item.get("blocking") is True and item.get("status") not in {"passed", "skipped"}:
            _fail("diff_preview_blocking_check_failed")
    return {
        "status": "preview_ready",
        "risk": _text(payload.get("risk"), "diff_preview_risk_missing"),
        "changed_files": preview_paths,
        "git_apply_check_ok": True,
        "would_apply_diff": False,
        "would_execute": False,
    }


def _validate_artifact(
    artifact: Any,
    *,
    task_id: str,
    run_id: str,
    source_head: str,
    approval_id: str,
    approval_generation: int,
    approved_diff_sha256: str,
    proposal_material: Mapping[str, Any],
) -> dict[str, Any]:
    value = _mapping(artifact, "coding_artifact_missing")
    unsigned = dict(value)
    recorded_hash = unsigned.pop("artifact_sha256", None)
    _require_equal(recorded_hash, _sha256_json(unsigned), "coding_artifact_hash_mismatch")
    expected = {
        "schema_version": "coding.immutable-applied-artifact/v2",
        "task_id": task_id,
        "run_id": run_id,
        "approval_id": approval_id,
        "generation": approval_generation,
        "approved_diff_sha256": approved_diff_sha256,
        "source_commit": source_head,
        "target_plugin_identity": proposal_material.get("target_plugin_identity"),
    }
    for key, expected_value in expected.items():
        _require_equal(value.get(key), expected_value, f"coding_artifact_{key}_mismatch")
    repository = _mapping(value.get("repository_identity"), "coding_artifact_repository_identity_missing")
    for key in ("repository", "worktree", "root"):
        _text(repository.get(key), f"coding_artifact_repository_{key}_missing")
    snapshots = _list(value.get("changed_files"), "coding_artifact_changed_files_missing")
    snapshot_paths: list[str] = []
    for snapshot in snapshots:
        item = _mapping(snapshot, "coding_artifact_changed_file_invalid")
        path = _text(item.get("path"), "coding_artifact_changed_path_missing").replace("\\", "/")
        if not path.startswith(FIXTURE_ROOT) or not _is_sha256(item.get("sha256_after")):
            _fail("coding_artifact_changed_file_invalid")
        if item.get("missing_before_apply") is not True or item.get("sha256_before") is not None:
            _fail("coding_artifact_source_baseline_not_absent")
        snapshot_paths.append(path)
    if sorted(snapshot_paths) != PROMPT1_FILES:
        _fail("coding_artifact_prompt1_scope_invalid")
    _require_equal(value.get("result_sha256"), _sha256_json(sorted(snapshots, key=lambda item: item["path"])), "coding_artifact_result_hash_mismatch")
    prompt_identity = _mapping(value.get("prompt_identity"), "coding_artifact_prompt_identity_missing")
    context_identity = _mapping(value.get("context_identity"), "coding_artifact_context_identity_missing")
    output_identity = _mapping(value.get("model_output_identity"), "coding_artifact_model_output_identity_missing")
    _require_equal(prompt_identity.get("selected_prompt_id"), PROMPT_ID, "coding_artifact_prompt_id_mismatch")
    _require_equal(
        prompt_identity.get("proposal_binding_sha256"),
        proposal_material.get("proposal_binding_sha256"),
        "coding_artifact_proposal_binding_mismatch",
    )
    _require_equal(context_identity.get("context_hash"), proposal_material["context"]["context_hash"], "coding_artifact_context_hash_mismatch")
    expected_output_identity = {
        "runtime_output_id": proposal_material.get("runtime_output_id"),
        "producer_model_invocation_id": proposal_material.get("producer_model_invocation_id"),
        "approved_diff_sha256": approved_diff_sha256,
    }
    for key, expected_value in expected_output_identity.items():
        _require_equal(output_identity.get(key), expected_value, f"coding_artifact_output_{key}_mismatch")
    cartographer = _mapping(value.get("cartographer_identity"), "coding_artifact_cartographer_identity_missing")
    expected_cartographer = proposal_material["cartographer"]
    cartographer_mapping = {
        "proposal_id": expected_cartographer["proposal_id"],
        "selection_id": expected_cartographer["selection_id"],
        "selection_generation": expected_cartographer["selection_generation"],
        "transfer_event_id": expected_cartographer["transfer_event_id"],
        "consumer_invocation_id": expected_cartographer["consumer_invocation_id"],
        "acknowledgement_id": expected_cartographer["acknowledgement_id"],
        "authority_state": expected_cartographer["authority_state"],
        "source_head": source_head,
    }
    _require_equal(cartographer, cartographer_mapping, "coding_artifact_cartographer_binding_mismatch")
    return value


def _validate_participants(state: Mapping[str, Any], artifact: Mapping[str, Any]) -> list[dict[str, Any]]:
    records = [_mapping(item, "coding_participant_record_invalid") for item in _list(state.get("participant_records"), "coding_participants_missing")]
    if len(records) != len(PARTICIPANT_ROLES) or {item.get("role") for item in records} != PARTICIPANT_ROLES:
        _fail("coding_participant_set_invalid")
    all_ids: list[str] = []
    summaries: list[dict[str, Any]] = []
    for record in records:
        role = _text(record.get("role"), "coding_participant_role_missing")
        if record.get("passed") is not True:
            _fail("coding_participant_not_passed")
        expected = {
            "schema_version": "coding.participant-invocation/v2",
            "provider": "source-proxy",
            "task_id": artifact.get("task_id"),
            "run_id": artifact.get("run_id"),
            "artifact_sha256": artifact.get("artifact_sha256"),
        }
        for key, expected_value in expected.items():
            _require_equal(record.get(key), expected_value, f"coding_participant_{role}_{key}_mismatch")
        invocation_id = _text(record.get("invocation_id"), "coding_participant_invocation_id_missing")
        output_id = _text(record.get("output_id"), "coding_participant_output_id_missing")
        acknowledgement_id = _text(
            record.get("consumer_acknowledgement_id"),
            "coding_participant_acknowledgement_id_missing",
        )
        all_ids.extend([invocation_id, output_id, acknowledgement_id])
        result = _mapping(record.get("result"), "coding_participant_result_missing")
        if result.get("passed") is not True:
            _fail("coding_participant_result_not_passed")
        output_hash = _sha256_json(result)
        recorded_output_hash = str(record.get("output_sha256") or "")
        if recorded_output_hash not in {output_hash, output_hash.removeprefix("sha256:")}:
            _fail("coding_participant_output_hash_mismatch")
        producer_process = _mapping(
            record.get("producer_process"),
            "coding_participant_process_identity_missing",
        )
        expected_isolation = (
            "source_proxy_executor_transaction"
            if role == "coding-executor"
            else "dedicated_participant_subprocess"
        )
        _require_equal(
            producer_process.get("isolation"),
            expected_isolation,
            "coding_participant_process_isolation_mismatch",
        )
        producer_process_id = int(
            producer_process.get("process_id")
            if isinstance(producer_process.get("process_id"), int)
            else 0
        )
        if producer_process_id <= 0:
            _fail("coding_participant_process_id_invalid")
        _text(
            producer_process.get("executable_sha256"),
            "coding_participant_executable_hash_missing",
        )
        _text(
            producer_process.get("entrypoint_sha256"),
            "coding_participant_entrypoint_hash_missing",
        )
        acknowledgement = _mapping(
            record.get("consumer_acknowledgement"),
            "coding_participant_acknowledgement_missing",
        )
        for key, expected_value in {
            "schema_version": "coding.participant-acknowledgement/v2",
            "acknowledgement_id": acknowledgement_id,
            "approval_id": artifact.get("approval_id"),
            "generation": artifact.get("generation"),
            "invocation_id": invocation_id,
            "output_id": output_id,
            "output_sha256": recorded_output_hash,
            "artifact_sha256": artifact.get("artifact_sha256"),
            "producer_record_sha256": record.get("producer_record_sha256"),
            "consumed": True,
        }.items():
            _require_equal(
                acknowledgement.get(key),
                expected_value,
                f"coding_participant_acknowledgement_{key}_mismatch",
            )
        consumer_process_id = acknowledgement.get("consumer_process_id")
        if not isinstance(consumer_process_id, int) or consumer_process_id <= 0:
            _fail("coding_participant_consumer_process_id_invalid")
        if role != "coding-executor" and consumer_process_id == producer_process_id:
            _fail("coding_participant_process_not_independent")
        producer_unsigned = {
            key: value
            for key, value in record.items()
            if key
            not in {
                "consumer_acknowledgement_id",
                "consumer_acknowledgement",
                "record_sha256",
            }
        }
        producer_unsigned["schema_version"] = "coding.participant-output/v2"
        producer_hash = producer_unsigned.pop("producer_record_sha256", None)
        _require_equal(
            producer_hash,
            _sha256_json(producer_unsigned),
            "coding_participant_producer_record_hash_mismatch",
        )
        unsigned = dict(record)
        recorded = unsigned.pop("record_sha256", None)
        _require_equal(recorded, _sha256_json(unsigned), "coding_participant_record_hash_mismatch")
        summaries.append(
            {
                "role": role,
                "service": _text(record.get("service"), "coding_participant_service_missing"),
                "model": _text(record.get("model"), "coding_participant_model_missing"),
                "invocation_id": invocation_id,
                "output_id": output_id,
                "consumer_acknowledgement_id": acknowledgement_id,
                "output_sha256": recorded_output_hash,
                "producer_process_id": producer_process_id,
                "producer_isolation": expected_isolation,
                "consumer_process_id": consumer_process_id,
                "passed": True,
            }
        )
    if len(all_ids) != len(set(all_ids)):
        _fail("coding_participant_identity_reused")
    return sorted(summaries, key=lambda item: item["role"])


def _validate_applied_execution(
    payload: Mapping[str, Any],
    *,
    task_id: str,
    material: Mapping[str, Any],
    approval_id: str,
    approval_generation: int,
) -> tuple[str, dict[str, Any]]:
    task = _mapping(payload.get("task"), "execute_task_missing")
    if task.get("id") != task_id or task.get("status") != "applied_needs_verification":
        _fail("execute_task_status_invalid")
    execution = _mapping(payload.get("execution"), "execute_receipt_missing")
    if execution.get("ok") is not True or execution.get("status") != "applied_needs_verification":
        _fail("execute_receipt_status_invalid")
    if execution.get("commit_created") is not False or execution.get("push_ran") is not False:
        _fail("execute_unexpected_git_authority")
    audit = _mapping(execution.get("audit"), "execute_audit_missing")
    _require_equal(audit.get("approved_diff_sha256"), material.get("approved_diff_sha256"), "execute_diff_hash_mismatch")
    changed_files = _normalize_changed_paths(audit.get("changed_files"), "execute_changed_files_invalid")
    if sorted(changed_files) != PROMPT1_FILES:
        _fail("execute_prompt1_scope_invalid")
    backup_manifest = _text(audit.get("backup_manifest"), "execute_backup_manifest_missing")
    artifact = _validate_artifact(
        execution.get("artifact"),
        task_id=task_id,
        run_id=str(material["run_id"]),
        source_head=str(material["source_commit"]),
        approval_id=approval_id,
        approval_generation=approval_generation,
        approved_diff_sha256=str(material["approved_diff_sha256"]),
        proposal_material=material,
    )
    state = _mapping(payload.get("coding_orchestrator"), "execute_orchestrator_missing")
    if state.get("task_id") != task_id or state.get("run_id") != material.get("run_id"):
        _fail("execute_orchestrator_run_mismatch")
    lane_states = _mapping(state.get("lane_states"), "execute_lane_states_missing")
    if lane_states.get("coder") != "completed" or lane_states.get("reviewer") != "completed":
        _fail("execute_independent_review_not_complete")
    roles = {item.get("role") for item in _list(state.get("participant_records"), "execute_participants_missing") if isinstance(item, Mapping)}
    if roles != {"coding-executor", "coding-reviewer"}:
        _fail("execute_participant_set_invalid")
    return backup_manifest, artifact


def _validate_production_proof(
    proof: Any,
    *,
    state: Mapping[str, Any],
    artifact: Mapping[str, Any],
    source_head: str,
) -> dict[str, Any]:
    value = _mapping(proof, "coding_production_proof_missing")
    unsigned = dict(value)
    recorded_hash = unsigned.pop("proof_sha256", None)
    _require_equal(recorded_hash, _sha256_json(unsigned), "coding_production_proof_hash_mismatch")
    expected = {
        "schema_version": "coding.production-proof/v1",
        "task_id": state.get("task_id"),
        "run_id": state.get("run_id"),
        "source_head": source_head,
        "artifact_sha256": artifact.get("artifact_sha256"),
        "approval_id": artifact.get("approval_id"),
        "terminal_proof_eligible": True,
        "failures": [],
    }
    for key, expected_value in expected.items():
        _require_equal(value.get(key), expected_value, f"coding_production_proof_{key}_invalid")
    _require_equal(
        value.get("target_plugin_proposal_sha256"),
        state.get("target_plugin_proposal", {}).get("proposal_binding_sha256"),
        "coding_production_proof_proposal_mismatch",
    )
    _require_equal(
        value.get("model_invocation_id"),
        state.get("target_plugin_proposal", {}).get("producer_model_invocation_id"),
        "coding_production_proof_model_mismatch",
    )
    _require_equal(
        value.get("recovery_id"),
        state.get("recovery_lineage", [{}])[0].get("recovery_id"),
        "coding_production_proof_recovery_mismatch",
    )
    claim = _text(value.get("claim_ceiling"), "coding_production_proof_claim_ceiling_missing")
    _require_equal(claim, "recovered_via_declared_fallback_only", "coding_production_proof_claim_ceiling_invalid")
    return {
        "proof_sha256": recorded_hash,
        "terminal_proof_eligible": True,
        "claim_ceiling": claim,
        "failures": [],
    }


def _validate_final_task(
    payload: Mapping[str, Any],
    *,
    task_id: str,
    material: Mapping[str, Any],
    approval_id: str,
    approval_generation: int,
    backup_manifest: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    task = _mapping(payload.get("task"), "final_task_missing")
    if task.get("id") != task_id or task.get("status") != "completed":
        _fail("final_task_not_completed")
    verification = _mapping(task.get("post_apply_verification"), "final_verification_missing")
    expected_verification = {
        "status": "verified",
        "verification_profile": "dummy_product_site",
        "client_browser_evidence_decision_bearing": False,
        "manual_browser_check_done": True,
        "commit_proposal_blocked": False,
    }
    for key, value in expected_verification.items():
        _require_equal(verification.get(key), value, f"final_verification_{key}_invalid")
    browser = _mapping(verification.get("browser_evidence"), "final_browser_evidence_missing")
    if (
        browser.get("real_browser_used") is not True
        or browser.get("storefront_runtime_engine") != "playwright_chromium"
        or browser.get("browser_verification_status") != "passed"
    ):
        _fail("final_real_browser_verification_missing")
    snapshot = _mapping(task.get("ast_snapshot"), "final_task_snapshot_missing")
    state = _mapping(snapshot.get("coding_orchestrator"), "final_orchestrator_state_missing")
    if (
        state.get("schema_version") != ORCHESTRATOR_SCHEMA
        or state.get("authoritative") is not True
        or state.get("task_id") != task_id
        or state.get("run_id") != material.get("run_id")
    ):
        _fail("final_orchestrator_state_invalid")
    _require_equal(state.get("lane_sequence"), LANE_SEQUENCE, "final_lane_sequence_invalid")
    _require_equal(state.get("lane_states"), FINAL_LANE_STATES, "final_lane_states_invalid")
    artifact = _validate_artifact(
        state.get("immutable_artifact"),
        task_id=task_id,
        run_id=str(material["run_id"]),
        source_head=str(material["source_commit"]),
        approval_id=approval_id,
        approval_generation=approval_generation,
        approved_diff_sha256=str(material["approved_diff_sha256"]),
        proposal_material=material,
    )
    if state.get("target_plugin_proposal", {}).get("proposal_binding_sha256") != material.get("proposal_binding_sha256"):
        _fail("final_target_plugin_proposal_changed")
    participants = _validate_participants(state, artifact)
    runtime = _validate_runtime_boundary(state)
    if set(runtime["lanes"]) != RUNTIME_LANES:
        _fail("final_runtime_lane_set_invalid")
    production_proof = _validate_production_proof(
        snapshot.get("coding_production_proof"),
        state=state,
        artifact=artifact,
        source_head=str(material["source_commit"]),
    )
    campaign_approval = _mapping(snapshot.get("campaign_2_approval"), "final_campaign_approval_missing")
    if (
        campaign_approval.get("state") != "consumed"
        or campaign_approval.get("approval_id") != approval_id
        or campaign_approval.get("generation") != approval_generation
    ):
        _fail("final_campaign_approval_not_consumed")
    evidence = _mapping(snapshot.get("approved_execution_evidence"), "final_execution_evidence_missing")
    if (
        evidence.get("final_truth_status") != "GO"
        or evidence.get("commit_safe") is not True
        or evidence.get("terminal_proof_eligible") is not True
        or evidence.get("backup_manifest") != backup_manifest
    ):
        _fail("final_execution_evidence_invalid")
    event_types = [item.get("event_type") for item in _list(state.get("causal_events"), "final_causal_events_missing") if isinstance(item, Mapping)]
    if "post_apply_verification_requested" not in event_types or "final_result" not in event_types:
        _fail("final_causal_finalization_events_missing")
    if event_types.index("post_apply_verification_requested") >= event_types.index("final_result"):
        _fail("finalization_preceded_verification")
    final_summary = {
        "task_status": "completed",
        "verification_status": "verified",
        "real_browser_used": True,
        "browser_engine": browser["storefront_runtime_engine"],
        "artifact": {
            "artifact_sha256": artifact["artifact_sha256"],
            "result_sha256": artifact["result_sha256"],
            "approved_diff_sha256": artifact["approved_diff_sha256"],
            "approval_id": artifact["approval_id"],
            "generation": artifact["generation"],
        },
        "pre_apply_source_baseline": {
            "fixture_absent": True,
            "paths_verified_absent": PROMPT1_FILES,
        },
        "participants": participants,
        "runtime_boundary": runtime,
        "production_proof": production_proof,
        "approval_final_state": "consumed",
        "verification_preceded_final_result": True,
    }
    return final_summary, state


def _exchange_hash(client: ProductionHttpClient) -> str:
    if not client.exchanges:
        _fail("http_exchange_missing")
    return client.exchanges[-1].response_sha256


def _run_one_proving_task(
    client: ProductionHttpClient,
    config: ProvingConfig,
    *,
    task_text: str,
    ordinal: int,
    expected_source_head: str | None,
) -> RunResult:
    exchange_start = len(client.exchanges) + 1
    proposal_path_id = urllib.parse.quote(config.proposal_id, safe="")
    proposal_collection = client.json(
        "source",
        "GET",
        "/v1/cartographer/proposals",
    )
    proposal_collection_response_sha256 = _exchange_hash(client)
    cartographer_proposal = _validate_cartographer_proposal_collection(
        proposal_collection,
        proposal_id=config.proposal_id,
    )
    selection_response = client.json(
        "source",
        "POST",
        f"/v1/cartographer/proposals/{proposal_path_id}/selection-preview",
        {"consumer": CONSUMER, "target": TARGET},
    )
    if (
        selection_response.get("authority") != "spiritos-approval-authority"
        or selection_response.get("cartographer_identity") != "cartographer-proposal-only"
        or selection_response.get("downstream_consumer") != CONSUMER
        or selection_response.get("write_authority") is not False
        or selection_response.get("approval_issuer_authority") is not False
    ):
        _fail("cartographer_selection_preview_authority_invalid")
    selection_preview = _mapping(selection_response.get("preview"), "cartographer_selection_preview_missing")
    selection_preview_id = _text(selection_preview.get("preview_id"), "cartographer_selection_preview_id_missing")
    selection_generation = _integer(
        selection_preview.get("generation"),
        "cartographer_selection_generation_invalid",
        minimum=1,
    )
    if selection_preview.get("state") != "previewed":
        _fail("cartographer_selection_preview_binding_invalid")

    selection_issue = client.json(
        "next",
        "POST",
        "/v1/operator/cartographer-selection",
        {
            "action": "approve",
            "generation": selection_generation,
            "preview_id": selection_preview_id,
            "proposal_id": config.proposal_id,
        },
    )
    selection_approval = _mapping(selection_issue.get("approval"), "cartographer_selection_approval_missing")
    selection_id = _text(selection_approval.get("approval_id"), "cartographer_selection_approval_id_missing")
    if not selection_id.startswith("apr_"):
        _fail("cartographer_selection_approval_id_invalid")
    _require_equal(selection_approval.get("generation"), selection_generation, "cartographer_selection_approval_generation_mismatch")
    _require_equal(selection_approval.get("state"), "approved", "cartographer_selection_approval_state_invalid")

    created = client.json(
        "next",
        "POST",
        "/v1/tasks/long-running",
        {
            "description": task_text,
            "cartographer_selection": {
                "selection_approval_id": selection_id,
                "proposal_id": config.proposal_id,
                "target": TARGET,
            },
        },
        sensitive_request=True,
    )
    task_id, initial_state = _validate_initial_task(
        created,
        proposal_id=config.proposal_id,
        selection_id=selection_id,
    )
    task_path_id = urllib.parse.quote(task_id, safe="")

    prompt_packet = client.json(
        "next",
        "POST",
        "/v1/decisions/prompt-packet",
        {
            "task": task_text,
            "task_id": task_id,
            "active_task_id": task_id,
            "allowed_files": ALLOWED_FILES,
            "selected_prompt_id": PROMPT_ID,
            "trial_prompt_id": PROMPT_ID,
            "selected_prompt_number": 1,
            "selected_target": TARGET,
            "target_file": TARGET,
            "target_files": [TARGET],
            "trial_mode": "live_apply",
            "needs_codebase_context": True,
            "wants_implementation": True,
            "dummy_coder_10_packet": {"target_plugin": _target_plugin_packet(config)},
        },
        sensitive_request=True,
    )
    prompt_packet_response_sha256 = _exchange_hash(client)
    prompt_packet_diff = _validate_prompt_packet(prompt_packet, task_id)
    prompt_receipt = _mapping(prompt_packet.get("fip0_truth_receipt"), "prompt_packet_truth_receipt_missing")
    proposal_state = _mapping(
        prompt_packet.get("coding_orchestrator"),
        "prompt_packet_orchestrator_missing",
    )
    approved_diff, material = _extract_persisted_proposal(
        proposal_state,
        task_id=task_id,
        proposal_id=config.proposal_id,
        selection_id=selection_id,
        expectation=config.recovery,
    )
    _validate_cartographer_selection_binding(
        cartographer_proposal,
        material["cartographer"],
    )
    _require_equal(
        initial_state.get("run_id"),
        material["run_id"],
        "prompt_packet_orchestrator_run_changed",
    )
    _require_equal(
        _sha256_text(prompt_packet_diff),
        material["approved_diff_sha256"],
        "prompt_packet_persisted_diff_mismatch",
    )
    source_head = str(material["source_commit"])
    if source_head != config.expected_source_head:
        _fail("proving_source_head_not_expected")
    if expected_source_head is not None and source_head != expected_source_head:
        _fail("proving_source_head_changed")
    plugin_identity = _mapping(
        material.get("target_plugin_identity"),
        "target_plugin_identity_missing",
    )
    _require_equal(
        plugin_identity.get("repository_id"),
        config.expected_repository_id,
        "target_plugin_repository_id_not_expected",
    )
    _require_equal(
        plugin_identity.get("worktree_id"),
        config.expected_worktree_id,
        "target_plugin_worktree_id_not_expected",
    )

    diff_preview_payload = client.json(
        "source",
        "POST",
        "/v1/verification/diff-preview",
        {
            "unified_diff": approved_diff,
            "active_task_id": task_id,
            "task_text": task_text,
            "task_spec": {
                "allowed_files": ALLOWED_FILES,
                "target": TARGET,
                "task_type": "create_file_bundle",
            },
        },
        sensitive_request=True,
    )
    diff_preview_response_sha256 = _exchange_hash(client)
    diff_preview = _validate_diff_preview(diff_preview_payload, material["changed_files"])

    approval_preview_response = client.json(
        "next",
        "POST",
        f"/v1/tasks/long-running/{task_path_id}/approval-preview",
        {
            "action": ACTION,
            "approved_diff": approved_diff,
            "target": TARGET,
            "selected_prompt_id": PROMPT_ID,
            "context_hash": material["context"]["context_hash"],
            "runtime_output_id": material["runtime_output_id"],
            "target_plugin": _target_plugin_packet(config),
        },
        sensitive_request=True,
    )
    approval_preview_response_sha256 = _exchange_hash(client)
    approval_preview = _mapping(approval_preview_response.get("preview"), "coding_approval_preview_missing")
    approval_preview_id = _text(approval_preview.get("preview_id"), "coding_approval_preview_id_missing")
    approval_generation = _integer(
        approval_preview.get("generation"),
        "coding_approval_preview_generation_invalid",
        minimum=1,
    )
    if (
        approval_preview_response.get("authority") != "spiritos-approval-authority"
        or approval_preview_response.get("consumer") != "coding-executor"
        or approval_preview.get("state") != "previewed"
    ):
        _fail("coding_approval_preview_binding_invalid")

    approval_response = client.json(
        "next",
        "POST",
        "/v1/operator/approval",
        {
            "action": "approve",
            "generation": approval_generation,
            "preview_id": approval_preview_id,
            "task_id": task_id,
        },
    )
    approval = _mapping(approval_response.get("approval"), "coding_operator_approval_missing")
    approval_id = _text(approval.get("approval_id"), "coding_operator_approval_id_missing")
    if not approval_id.startswith("apr_") or approval.get("state") != "approved":
        _fail("coding_operator_approval_invalid")
    _require_equal(approval.get("generation"), approval_generation, "coding_operator_approval_generation_mismatch")

    execute_response = client.json(
        "next",
        "POST",
        "/v1/actions/execute-approved",
        {
            "action": ACTION,
            "target": TARGET,
            "approved_diff": approved_diff,
            "task_id": task_id,
            "approval_id": approval_id,
            "allowed_files": ALLOWED_FILES,
            "trial_prompt_id": PROMPT_ID,
            "trial_prompt_text": task_text,
            "runtime_output_id": material["runtime_output_id"],
            "context_hash": material["context"]["context_hash"],
        },
        sensitive_request=True,
    )
    execute_response_sha256 = _exchange_hash(client)
    backup_manifest, applied_artifact = _validate_applied_execution(
        execute_response,
        task_id=task_id,
        material=material,
        approval_id=approval_id,
        approval_generation=approval_generation,
    )
    _require_equal(
        applied_artifact.get("repository_identity", {}).get("repository"),
        config.expected_repository_id,
        "coding_artifact_repository_id_not_expected",
    )

    verify_response = client.json(
        "next",
        "POST",
        f"/v1/tasks/long-running/{task_path_id}/verify",
        {
            "confirm_backup_audit_present": True,
            "confirm_changed_files_reviewed": True,
            "confirm_expected_change_present": True,
            "confirm_no_unintended_files": True,
            "run_code_verification": True,
            "verification_profile": "dummy_product_site",
            "run_snapshot_verification": True,
            "verification_note": "Foundation R1 server-owned production verification.",
        },
    )
    verify_response_sha256 = _exchange_hash(client)
    verify_task = _mapping(verify_response.get("task"), "verify_task_missing")
    if verify_task.get("id") != task_id or verify_task.get("status") != "completed":
        _fail("verify_did_not_finalize_task")
    verify_state = _mapping(verify_response.get("coding_orchestrator"), "verify_orchestrator_missing")

    final_readback = client.json(
        "next",
        "GET",
        f"/v1/tasks/long-running/{task_path_id}",
    )
    final_readback_response_sha256 = _exchange_hash(client)
    final_summary, final_state = _validate_final_task(
        final_readback,
        task_id=task_id,
        material=material,
        approval_id=approval_id,
        approval_generation=approval_generation,
        backup_manifest=backup_manifest,
    )
    if _sha256_json(verify_state) != _sha256_json(final_state):
        _fail("final_orchestrator_readback_mismatch")
    if final_state.get("immutable_artifact", {}).get("artifact_sha256") != applied_artifact.get("artifact_sha256"):
        _fail("final_artifact_changed_after_apply")

    summary = {
        "ordinal": ordinal,
        "clean_rerun": ordinal == 2,
        "task_id": task_id,
        "orchestrator_run_id": material["run_id"],
        "orchestrator_attempt_id": material["attempt_id"],
        "source_commit": source_head,
        "task_prompt_sha256": _sha256_text(task_text),
        "cartographer_proposal": {
            **cartographer_proposal,
            "collection_response_sha256": proposal_collection_response_sha256,
        },
        "cartographer": material["cartographer"],
        "selection_preview_id": selection_preview_id,
        "selection_generation": selection_generation,
        "prompt_packet": {
            "selected_prompt_id": PROMPT_ID,
            "truth_receipt_run_id": prompt_receipt["run_id"],
            "response_sha256": prompt_packet_response_sha256,
            "diff_observed_but_not_used": True,
            "diff_sha256": _sha256_text(prompt_packet_diff),
        },
        "target_proposal": {
            "authoritative_source": "prompt_packet.coding_orchestrator.runtime_outputs",
            "proposal_binding_sha256": material["proposal_binding_sha256"],
            "runtime_output_id": material["runtime_output_id"],
            "producer_model_invocation_id": material["producer_model_invocation_id"],
            "approved_diff_sha256": material["approved_diff_sha256"],
            "changed_files": material["changed_files"],
            "response_sha256": prompt_packet_response_sha256,
        },
        "context": material["context"],
        "target_adapter": material["adapter"],
        "controlled_recovery": material["recovery"],
        "diff_preview": {
            **diff_preview,
            "response_sha256": diff_preview_response_sha256,
        },
        "approval": {
            "preview_id": approval_preview_id,
            "preview_generation": approval_generation,
            "approval_id": approval_id,
            "approval_generation": approval_generation,
            "preview_response_sha256": approval_preview_response_sha256,
        },
        "execution_response_sha256": execute_response_sha256,
        "verification_response_sha256": verify_response_sha256,
        "final_readback_response_sha256": final_readback_response_sha256,
        **final_summary,
        "http_exchange_ordinals": [exchange_start, len(client.exchanges)],
    }
    return RunResult(
        summary=summary,
        approved_diff=approved_diff,
        prompt_packet_diff=prompt_packet_diff,
        backup_manifest=backup_manifest,
        source_commit=source_head,
        repository_identity=dict(applied_artifact["repository_identity"]),
        target_plugin_identity=dict(material["target_plugin_identity"]),
    )


def _validate_undo(payload: Mapping[str, Any], first: RunResult) -> dict[str, Any]:
    undo = _mapping(payload.get("undo"), "undo_receipt_missing")
    if (
        undo.get("original_task_id") != first.summary["task_id"]
        or undo.get("selected_backup_manifest") != first.backup_manifest
        or undo.get("filesystem_verified") is not True
        or undo.get("untouched_scope_assertion") is not True
        or undo.get("unrelated_paths_touched") != []
        or undo.get("final_truth_status") != "UNDO_FILESYSTEM_VERIFIED"
    ):
        _fail("undo_receipt_invalid")
    restored = _list(undo.get("files_restored"), "undo_files_restored_missing")
    restored_paths = _normalize_changed_paths(restored, "undo_files_restored_invalid")
    if sorted(restored_paths) != PROMPT1_FILES or any(
        not isinstance(item, Mapping)
        or item.get("verified") is not True
        or item.get("absent") is not True
        or item.get("expected_sha256_before") is not None
        or item.get("actual_sha256") is not None
        for item in restored
    ):
        _fail("undo_restoration_not_verified")
    return {
        "original_task_id": first.summary["task_id"],
        "undo_receipt_id": _text(undo.get("undo_receipt_id"), "undo_receipt_id_missing"),
        "selected_backup_manifest": first.backup_manifest,
        "approved_diff_sha256": undo.get("approved_diff_sha256"),
        "files_restored": restored_paths,
        "source_baseline_restored": True,
        "fixture_absent": True,
        "filesystem_verified": True,
        "untouched_scope_assertion": True,
        "final_truth_status": "UNDO_FILESYSTEM_VERIFIED",
    }


def _validate_reset(payload: Mapping[str, Any], source_head: str) -> dict[str, Any]:
    if (
        payload.get("status") != "reset_verified"
        or payload.get("reset_verified") is not True
        or payload.get("clean_verified") is not True
        or payload.get("fixture_root") != FIXTURE_ROOT
    ):
        _fail("target_fixture_reset_not_verified")
    _require_equal(
        _git_oid(payload.get("source_head"), "target_fixture_reset_source_head_invalid"),
        source_head,
        "target_fixture_reset_source_head_mismatch",
    )
    if payload.get("source_baseline_verified") is not True:
        _fail("target_fixture_source_baseline_not_verified")
    baseline_sha256 = _text(
        payload.get("source_baseline_sha256"),
        "target_fixture_source_baseline_hash_missing",
    )
    if not _is_sha256(baseline_sha256):
        _fail("target_fixture_source_baseline_hash_invalid")
    if payload.get("source_baseline_tracked_paths") != []:
        _fail("target_fixture_source_baseline_not_absent")
    identity = _validate_plugin_identity(payload.get("target_plugin_identity"), source_head)
    removed = _list(payload.get("removed_paths"), "target_fixture_reset_paths_missing")
    if removed:
        _fail("target_fixture_reset_was_not_post_undo_idempotent")
    return {
        "status": "reset_verified",
        "reset_receipt_id": _text(payload.get("reset_receipt_id"), "target_fixture_reset_receipt_id_missing"),
        "fixture_root": FIXTURE_ROOT,
        "removed_paths": removed,
        "clean_verified": True,
        "source_head": source_head,
        "source_baseline_verified": True,
        "source_baseline_sha256": baseline_sha256,
        "source_baseline_tracked_paths": [],
        "target_plugin_result_identity": identity["result_identity"],
    }


def _receipt_forbidden_key_paths(value: Any, *, prefix: str = "$") -> list[str]:
    failures: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower()
            if normalized in FORBIDDEN_RECEIPT_KEYS or any(
                fragment in normalized
                for fragment in FORBIDDEN_RECEIPT_KEY_SUBSTRINGS
            ):
                failures.append(f"{prefix}.{key}")
            failures.extend(_receipt_forbidden_key_paths(child, prefix=f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            failures.extend(_receipt_forbidden_key_paths(child, prefix=f"{prefix}[{index}]"))
    return failures


def _assert_receipt_redacted(receipt: Mapping[str, Any], forbidden_values: Sequence[str]) -> None:
    if _receipt_forbidden_key_paths(receipt):
        _fail("proving_receipt_forbidden_key_present")
    serialized = _canonical_json(receipt).decode("utf-8")
    for value in forbidden_values:
        if isinstance(value, str) and len(value) >= 8 and value in serialized:
            _fail("proving_receipt_sensitive_value_present")


def _safe_plugin_receipt_identity(identity: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "schema_version",
        "plugin_id",
        "repository_id",
        "worktree_id",
        "workspace_root",
        "branch",
        "state_namespace",
        "fixture_root",
        "source_head",
        "selected_prompt_id",
        "selected_context_id",
        "execution_profile",
        "allowed_actions",
        "result_identity",
    )
    return {key: identity.get(key) for key in keys}


def _expected_exchange_sequence(
    proposal_id: str,
    first: RunResult,
    second: RunResult,
) -> list[tuple[str, str, str]]:
    proposal_path_id = urllib.parse.quote(proposal_id, safe="")

    def run_sequence(result: RunResult) -> list[tuple[str, str, str]]:
        task_path_id = urllib.parse.quote(str(result.summary.get("task_id") or ""), safe="")
        if not task_path_id:
            _fail("production_http_transcript_task_id_missing")
        return [
            ("source", "GET", "/v1/cartographer/proposals"),
            (
                "source",
                "POST",
                f"/v1/cartographer/proposals/{proposal_path_id}/selection-preview",
            ),
            ("next", "POST", "/v1/operator/cartographer-selection"),
            ("next", "POST", "/v1/tasks/long-running"),
            ("next", "POST", "/v1/decisions/prompt-packet"),
            ("source", "POST", "/v1/verification/diff-preview"),
            (
                "next",
                "POST",
                f"/v1/tasks/long-running/{task_path_id}/approval-preview",
            ),
            ("next", "POST", "/v1/operator/approval"),
            ("next", "POST", "/v1/actions/execute-approved"),
            ("next", "POST", f"/v1/tasks/long-running/{task_path_id}/verify"),
            ("next", "GET", f"/v1/tasks/long-running/{task_path_id}"),
        ]

    first_task_path = urllib.parse.quote(str(first.summary.get("task_id") or ""), safe="")
    if not first_task_path:
        _fail("production_http_transcript_task_id_missing")
    return [
        ("next", "POST", "/v1/operator/session"),
        *run_sequence(first),
        ("next", "POST", f"/v1/tasks/long-running/{first_task_path}/undo"),
        ("next", "POST", "/v1/coding/dummy-product-site-preview/reset"),
        *run_sequence(second),
        ("next", "DELETE", "/v1/operator/session"),
        ("next", "GET", "/v1/operator/session"),
    ]


def _run_attestation_binding(
    *,
    first: RunResult,
    second: RunResult,
    undo: Mapping[str, Any],
    reset: Mapping[str, Any],
    operator_hash: str,
    revocation_response_sha256: str,
    retired_session_probe_response_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": "spiritos-production-http-run-binding/v1",
        "operator_identity_sha256": operator_hash,
        "revocation_response_sha256": revocation_response_sha256,
        "retired_session_probe_response_sha256": (
            retired_session_probe_response_sha256
        ),
        "source_head": first.source_commit,
        "first_run_summary_sha256": _sha256_json(first.summary),
        "second_run_summary_sha256": _sha256_json(second.summary),
        "undo_summary_sha256": _sha256_json(dict(undo)),
        "reset_summary_sha256": _sha256_json(dict(reset)),
    }


def _build_receipt(
    *,
    client: ProductionHttpClient,
    config: ProvingConfig,
    started_at: str,
    completed_at: str,
    task_text: str,
    operator_hash: str,
    first: RunResult,
    second: RunResult,
    undo: Mapping[str, Any],
    reset: Mapping[str, Any],
    attestation: ProductionRunAttestation | None,
    revocation_response_sha256: str,
    retired_session_probe_response_sha256: str,
    forbidden_values: Sequence[str],
) -> dict[str, Any]:
    if type(client) is not ProductionHttpClient or client.production_http is not True:
        _fail("nonproduction_transport_cannot_issue_receipt")
    binding = _run_attestation_binding(
        first=first,
        second=second,
        undo=undo,
        reset=reset,
        operator_hash=operator_hash,
        revocation_response_sha256=revocation_response_sha256,
        retired_session_probe_response_sha256=(
            retired_session_probe_response_sha256
        ),
    )
    if attestation is None:
        _fail("production_run_attestation_missing")
    client.verify_run_attestation(attestation, binding=binding)
    if first.source_commit != second.source_commit:
        _fail("clean_rerun_source_head_changed")
    if first.source_commit != config.expected_source_head:
        _fail("clean_rerun_source_head_not_expected")
    if first.repository_identity != second.repository_identity:
        _fail("clean_rerun_repository_identity_changed")
    for result in (first, second):
        if (
            result.target_plugin_identity.get("repository_id")
            != config.expected_repository_id
            or result.target_plugin_identity.get("worktree_id")
            != config.expected_worktree_id
        ):
            _fail("clean_rerun_repository_identity_not_expected")
    distinct_pairs = (
        ("task_id",),
        ("orchestrator_run_id",),
    )
    for (key,) in distinct_pairs:
        if first.summary.get(key) == second.summary.get(key):
            _fail(f"clean_rerun_{key}_reused")
    if first.summary["approval"]["approval_id"] == second.summary["approval"]["approval_id"]:
        _fail("clean_rerun_approval_reused")
    if first.summary["artifact"]["artifact_sha256"] == second.summary["artifact"]["artifact_sha256"]:
        _fail("clean_rerun_artifact_identity_reused")
    if (
        undo.get("source_baseline_restored") is not True
        or undo.get("fixture_absent") is not True
        or reset.get("source_baseline_verified") is not True
        or reset.get("source_head") != first.source_commit
        or reset.get("source_baseline_tracked_paths") != []
        or reset.get("removed_paths") != []
        or first.summary.get("pre_apply_source_baseline", {}).get("fixture_absent") is not True
        or second.summary.get("pre_apply_source_baseline", {}).get("fixture_absent") is not True
    ):
        _fail("clean_rerun_source_baseline_not_verified")
    receipt: dict[str, Any] = {
        "schema_version": RECEIPT_SCHEMA,
        "receipt_type": "foundation_r1_black_box_production_proving",
        "remediation_id": REMEDIATION_ID,
        "run_mode": "production_http",
        "terminal_proof_eligible": True,
        "claim_ceiling": "recovered_via_declared_fallback_only",
        "started_at": started_at,
        "completed_at": completed_at,
        "source_commit": first.source_commit,
        "expected_runtime_identity": {
            "source_head": config.expected_source_head,
            "repository_id": config.expected_repository_id,
            "worktree_id": config.expected_worktree_id,
            "worktree_id_source": "approval_preflight.stateNamespace",
        },
        "repository_identity": first.repository_identity,
        "transport": {
            "kind": "production_http",
            "source_origin": config.source_origin,
            "next_origin": config.next_origin,
            "origins_distinct": True,
            "redirects_allowed": False,
            "services_started_by_harness": False,
            "application_modules_imported": False,
            "test_modules_imported": False,
            "callback_transport_allowed": False,
        },
        "task_prompt": {
            "sha256": _sha256_text(task_text),
            "byte_count": len(task_text.encode("utf-8")),
            "raw_text_recorded": False,
        },
        "target_plugin_identity": _safe_plugin_receipt_identity(first.target_plugin_identity),
        "operator_session": {
            "operator_identity_sha256": operator_hash,
            "role": "approval-issuer",
            "authenticated": True,
            "revoked": True,
            "revocation_response_sha256": revocation_response_sha256,
            "retired_session_probe_response_sha256": (
                retired_session_probe_response_sha256
            ),
            "retired_session_status": "revoked",
            "cookie_jar_cleared": True,
            "credential_recorded": False,
            "session_identifier_recorded": False,
        },
        "runs": [first.summary, second.summary],
        "run_attestation": attestation.to_receipt(),
        "undo": dict(undo),
        "reset": dict(reset),
        "clean_rerun": {
            "completed": True,
            "source_commit_unchanged": True,
            "source_baseline_sha256": reset["source_baseline_sha256"],
            "source_baseline_verified": True,
            "fixture_absent_before_each_run": True,
            "reset_was_idempotent_after_undo": True,
            "repository_identity_unchanged": True,
            "task_id_distinct": True,
            "run_id_distinct": True,
            "approval_id_distinct": True,
            "artifact_identity_distinct": True,
        },
        "expected_controlled_recovery": dataclasses.asdict(config.recovery),
        "http_exchanges": [exchange.to_receipt() for exchange in client.exchanges],
        "redaction": {
            "status": "passed",
            "raw_task_recorded": False,
            "raw_diffs_recorded": False,
            "raw_http_bodies_recorded": False,
            "credentials_recorded": False,
            "cookies_recorded": False,
            "csrf_values_recorded": False,
            "forbidden_key_scan": "passed",
            "forbidden_value_scan": "passed",
        },
        "failures": [],
    }
    _assert_receipt_redacted(receipt, forbidden_values)
    receipt["receipt_sha256"] = _sha256_json(receipt)
    _assert_receipt_redacted(receipt, forbidden_values)
    return receipt


def _write_new_receipt(path: Path, receipt: Mapping[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        _fail("proving_receipt_output_already_exists")
    parent = path.parent
    if not parent.is_dir():
        _fail("proving_receipt_output_parent_missing")
    payload = json.dumps(receipt, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_name = handle.name
            os.chmod(temporary_name, 0o600)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary_name, path)
        except FileExistsError:
            _fail("proving_receipt_output_already_exists")
        except OSError as error:
            del error
            _fail("proving_receipt_atomic_create_failed")
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def _run_proving(config: ProvingConfig, *, credential: str) -> dict[str, Any]:
    client = ProductionHttpClient(config)
    task_text = config.task_file.read_text(encoding="utf-8").strip()
    started_at = _utc_now()
    session_established = False
    original_error: ProvingError | None = None
    first: RunResult | None = None
    second: RunResult | None = None
    undo_summary: dict[str, Any] | None = None
    reset_summary: dict[str, Any] | None = None
    operator_hash = ""
    csrf_value = ""
    cookie_values: list[str] = []
    revocation_response_sha256 = ""
    retired_session_probe_response_sha256 = ""
    try:
        session = client.json(
            "next",
            "POST",
            "/v1/operator/session",
            {"credential": credential},
            sensitive_request=True,
        )
        # A successful session response may already have created server state;
        # mark it active before validating any response fields so every later
        # fail-closed path still attempts revocation.
        session_established = True
        if session.get("role") != "approval-issuer":
            _fail("operator_session_role_invalid")
        operator = _text(session.get("operator"), "operator_session_identity_missing")
        csrf_value = _text(session.get("csrf"), "operator_session_csrf_missing")
        client.bind_csrf(csrf_value)
        _text(session.get("expires_at"), "operator_session_expiry_missing")
        operator_hash = _sha256_text(operator)
        cookie_values = client.confirm_session_cookie_binding()

        first = _run_one_proving_task(
            client,
            config,
            task_text=task_text,
            ordinal=1,
            expected_source_head=config.expected_source_head,
        )
        first_task_path = urllib.parse.quote(str(first.summary["task_id"]), safe="")
        undo_response = client.json(
            "next",
            "POST",
            f"/v1/tasks/long-running/{first_task_path}/undo",
            {
                "confirm_undo": True,
                "expected_backup_manifest": first.backup_manifest,
                "requested_by": "foundation-remediation-r1-prover",
            },
        )
        undo_response_sha256 = _exchange_hash(client)
        undo_summary = _validate_undo(undo_response, first)
        undo_summary["response_sha256"] = undo_response_sha256

        reset_response = client.json(
            "next",
            "POST",
            "/v1/coding/dummy-product-site-preview/reset",
            {
                "selected_prompt_id": PROMPT_ID,
                "target_plugin": _target_plugin_packet(config),
            },
        )
        reset_response_sha256 = _exchange_hash(client)
        reset_summary = _validate_reset(reset_response, first.source_commit)
        reset_summary["response_sha256"] = reset_response_sha256

        second = _run_one_proving_task(
            client,
            config,
            task_text=task_text,
            ordinal=2,
            expected_source_head=first.source_commit,
        )
    except ProvingError as error:
        original_error = error
    except Exception:
        original_error = ProvingError("proving_internal_validation_error")
    finally:
        if session_established:
            try:
                revoked = client.json("next", "DELETE", "/v1/operator/session")
                if revoked.get("status") != "revoked":
                    _fail("operator_session_revocation_not_confirmed")
                revocation_response_sha256 = _exchange_hash(client)
                retired_session_probe_response_sha256 = (
                    client.verify_retired_session_status()
                )
                session_established = False
            except Exception:
                if original_error is None:
                    original_error = ProvingError("operator_session_revocation_failed")
                else:
                    original_error = ProvingError(
                        "operator_session_revocation_failed_after_proving_failure"
                    )
    if original_error is not None:
        raise original_error
    if session_established or first is None or second is None or undo_summary is None or reset_summary is None:
        _fail("proving_sequence_incomplete")
    completed_at = _utc_now()
    forbidden_values = [
        credential,
        csrf_value,
        task_text,
        first.approved_diff,
        first.prompt_packet_diff,
        second.approved_diff,
        second.prompt_packet_diff,
        *cookie_values,
    ]
    attestation = client.issue_run_attestation(
        first=first,
        second=second,
        undo=undo_summary,
        reset=reset_summary,
        operator_hash=operator_hash,
        revocation_response_sha256=revocation_response_sha256,
        retired_session_probe_response_sha256=(
            retired_session_probe_response_sha256
        ),
    )
    receipt = _build_receipt(
        client=client,
        config=config,
        started_at=started_at,
        completed_at=completed_at,
        task_text=task_text,
        operator_hash=operator_hash,
        first=first,
        second=second,
        undo=undo_summary,
        reset=reset_summary,
        attestation=attestation,
        revocation_response_sha256=revocation_response_sha256,
        retired_session_probe_response_sha256=(
            retired_session_probe_response_sha256
        ),
        forbidden_values=forbidden_values,
    )
    _write_new_receipt(config.output, receipt)
    return receipt


def _environment_default(name: str) -> str | None:
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else None


def _parse_config(argv: Sequence[str] | None = None) -> ProvingConfig:
    parser = argparse.ArgumentParser(
        description=(
            "Run two real Foundation R1 production HTTP proving tasks. Services must "
            "already be running; the operator credential is accepted only through "
            "SPIRITOS_OPERATOR_CREDENTIAL."
        )
    )
    parser.add_argument(
        "--source-origin",
        default=_environment_default("SPIRITOS_FOUNDATION_R1_SOURCE_ORIGIN"),
        help="Source Proxy origin (or SPIRITOS_FOUNDATION_R1_SOURCE_ORIGIN)",
    )
    parser.add_argument(
        "--next-origin",
        default=_environment_default("SPIRITOS_FOUNDATION_R1_NEXT_ORIGIN"),
        help="Next production origin (or SPIRITOS_FOUNDATION_R1_NEXT_ORIGIN)",
    )
    parser.add_argument("--proposal-id", required=True, help="Existing persisted Cartographer proposal id")
    parser.add_argument(
        "--expected-source-head",
        required=True,
        help="Exact immutable source HEAD expected from every server-owned artifact",
    )
    parser.add_argument(
        "--expected-repository-id",
        required=True,
        help="Exact canonical repository identity expected from the target adapter",
    )
    parser.add_argument(
        "--expected-worktree-id",
        required=True,
        help="Exact canonical worktree/state namespace expected from the target adapter",
    )
    parser.add_argument("--task-file", required=True, type=Path, help="UTF-8 proving task text; never copied into the receipt")
    parser.add_argument("--output", required=True, type=Path, help="New receipt path; existing files are never overwritten")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=float(_environment_default("SPIRITOS_FOUNDATION_R1_HTTP_TIMEOUT_SECONDS") or "900"),
    )
    parser.add_argument(
        "--expected-failed-provider",
        default=_environment_default("SPIRITOS_FOUNDATION_R1_EXPECTED_FAILED_PROVIDER"),
        help="Expected primary failure provider (or SPIRITOS_FOUNDATION_R1_EXPECTED_FAILED_PROVIDER)",
    )
    parser.add_argument(
        "--expected-failed-model",
        default=_environment_default("SPIRITOS_FOUNDATION_R1_EXPECTED_FAILED_MODEL"),
        help="Expected primary failure model (or SPIRITOS_FOUNDATION_R1_EXPECTED_FAILED_MODEL)",
    )
    parser.add_argument(
        "--expected-fallback-provider",
        default=_environment_default("SPIRITOS_FOUNDATION_R1_EXPECTED_FALLBACK_PROVIDER"),
        help="Expected canonical fallback provider (or SPIRITOS_FOUNDATION_R1_EXPECTED_FALLBACK_PROVIDER)",
    )
    parser.add_argument(
        "--expected-fallback-model",
        default=_environment_default("SPIRITOS_FOUNDATION_R1_EXPECTED_FALLBACK_MODEL"),
        help="Expected canonical fallback model (or SPIRITOS_FOUNDATION_R1_EXPECTED_FALLBACK_MODEL)",
    )
    args = parser.parse_args(argv)
    if not args.source_origin or not args.next_origin:
        _fail("service_origins_required")
    source_origin = _normalize_origin(args.source_origin, role="source")
    next_origin = _normalize_origin(args.next_origin, role="next")
    if source_origin == next_origin:
        _fail("source_and_next_origins_must_be_distinct")
    if PROPOSAL_ID_RE.fullmatch(args.proposal_id) is None:
        _fail("proposal_id_invalid")
    expected_source_head = _git_oid(
        args.expected_source_head,
        "expected_source_head_invalid",
    )
    if (
        IDENTITY_RE.fullmatch(args.expected_repository_id) is None
        or IDENTITY_RE.fullmatch(args.expected_worktree_id) is None
    ):
        _fail("expected_repository_identity_invalid")
    task_input = args.task_file.expanduser()
    if task_input.is_symlink():
        _fail("task_file_invalid")
    task_file = task_input.resolve()
    if not task_file.is_file():
        _fail("task_file_invalid")
    try:
        task_text = task_file.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError) as error:
        raise ProvingError("task_file_unreadable") from error
    task_bytes = len(task_text.encode("utf-8"))
    if task_bytes < 20 or task_bytes > MAX_TASK_BYTES or "\x00" in task_text:
        _fail("task_file_content_invalid")
    output_input = args.output.expanduser()
    if output_input.is_symlink():
        _fail("proving_receipt_output_already_exists")
    output = output_input.resolve()
    if output.suffix.lower() != ".json" or output == task_file:
        _fail("proving_receipt_output_invalid")
    if output.exists() or output.is_symlink():
        _fail("proving_receipt_output_already_exists")
    if not output.parent.is_dir():
        _fail("proving_receipt_output_parent_missing")
    if not 1 <= args.timeout_seconds <= 3_600:
        _fail("http_timeout_invalid")
    recovery_values = (
        args.expected_failed_provider,
        args.expected_failed_model,
        args.expected_fallback_provider,
        args.expected_fallback_model,
    )
    if any(not isinstance(value, str) or not value.strip() for value in recovery_values):
        _fail("expected_recovery_route_required")
    if any(len(value) > 200 or any(ord(character) < 32 for character in value) for value in recovery_values):
        _fail("expected_recovery_route_invalid")
    return ProvingConfig(
        source_origin=source_origin,
        next_origin=next_origin,
        proposal_id=args.proposal_id,
        task_file=task_file,
        output=output,
        timeout_seconds=args.timeout_seconds,
        recovery=RecoveryExpectation(
            failed_provider=args.expected_failed_provider,
            failed_model=args.expected_failed_model,
            replacement_provider=args.expected_fallback_provider,
            replacement_model=args.expected_fallback_model,
        ),
        expected_source_head=expected_source_head,
        expected_repository_id=args.expected_repository_id,
        expected_worktree_id=args.expected_worktree_id,
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        config = _parse_config(argv)
        credential = os.environ.get("SPIRITOS_OPERATOR_CREDENTIAL", "")
        if len(credential) < 8 or "\x00" in credential:
            _fail("operator_credential_env_required")
        receipt = _run_proving(config, credential=credential)
    except (ProvingError, OSError) as error:
        reason = error.reason_code if isinstance(error, ProvingError) else "proving_io_failed"
        print(f"FOUNDATION_R1_PROVING_FAILED:{reason}", file=sys.stderr)
        return 1
    except Exception:
        print("FOUNDATION_R1_PROVING_FAILED:proving_internal_error", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": "passed",
                "receipt": str(config.output),
                "receipt_sha256": receipt["receipt_sha256"],
                "terminal_proof_eligible": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
