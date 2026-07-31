"""Fail-closed authority checks for the Gate 2-J.9I write smoke."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


class WriteSmokeSafetyError(ValueError):
    """A write-smoke request exceeded its sealed authority."""


@dataclass(frozen=True)
class WriteSmokePolicy:
    allowed_source: str = "qualification_write_fixture/source_file.py"
    focused_validation: str = "python -m pytest -q qualification_write_fixture/test_source_file.py"
    provider_profile_id: str = "spiritos-qualification"
    model: str = "qwen2.5-coder:14b"
    model_digest: str = "9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849"

    def authorize_mutation(self, operation: str, path: str) -> None:
        normalized = path.replace("\\", "/").strip()
        if operation != "modify":
            raise WriteSmokeSafetyError("write_smoke_mutation_operation_denied")
        if not normalized or normalized.startswith("/") or ".." in normalized.split("/"):
            raise WriteSmokeSafetyError("write_smoke_path_escape_denied")
        if normalized != self.allowed_source:
            raise WriteSmokeSafetyError("write_smoke_protected_path_denied")

    def authorize_command(self, command: str) -> None:
        if command != self.focused_validation:
            raise WriteSmokeSafetyError("write_smoke_command_denied")

    def verify_model_binding(self, *, provider_profile_id: str, model: str, digest: str, fallback: bool, direct_ollama: bool) -> None:
        if direct_ollama:
            raise WriteSmokeSafetyError("write_smoke_direct_ollama_denied")
        if fallback:
            raise WriteSmokeSafetyError("write_smoke_fallback_denied")
        if provider_profile_id != self.provider_profile_id:
            raise WriteSmokeSafetyError("write_smoke_provider_denied")
        if model != self.model:
            raise WriteSmokeSafetyError("write_smoke_model_denied")
        if digest != self.model_digest:
            raise WriteSmokeSafetyError("write_smoke_digest_denied")

    def verify_terminal_integrity(self, *, model_timeout: bool = False, tool_timeout: bool = False, cancelled: bool = False, crashed_after_partial_write: bool = False, evidence_written: bool = True, terminal_event: bool = True, filesystem_ledger_complete: bool = True, git_ledger_reconciled: bool = True, cleanup_complete: bool = True) -> None:
        failures = {
            "model_timeout": model_timeout,
            "tool_timeout": tool_timeout,
            "jcode_cancelled": cancelled,
            "jcode_crashed_after_partial_write": crashed_after_partial_write,
            "evidence_destination_failed": not evidence_written,
            "terminal_event_missing": not terminal_event,
            "filesystem_ledger_incomplete": not filesystem_ledger_complete,
            "git_ledger_mismatch": not git_ledger_reconciled,
            "cleanup_failed": not cleanup_complete,
        }
        for reason, failed in failures.items():
            if failed:
                raise WriteSmokeSafetyError(f"write_smoke_{reason}")


@dataclass(frozen=True)
class RequestBudgetBinding:
    request_sha256: str
    input_limit: int
    output_limit: int = 1024
    request_limit: int = 2

    def verify(self, request: dict[str, object], *, input_tokens: int, output_tokens: int, request_number: int) -> None:
        encoded = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
        if hashlib.sha256(encoded).hexdigest() != self.request_sha256:
            raise WriteSmokeSafetyError("write_smoke_request_hash_mismatch")
        if input_tokens > self.input_limit:
            raise WriteSmokeSafetyError("write_smoke_input_budget_exhausted")
        if output_tokens > self.output_limit:
            raise WriteSmokeSafetyError("write_smoke_output_budget_exhausted")
        if request_number > self.request_limit:
            raise WriteSmokeSafetyError("write_smoke_request_count_exhausted")
