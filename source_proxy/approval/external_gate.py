from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from source_proxy.approval.model_call_authority import (
    CAMPAIGN_ID,
    ModelCallAuthorityError,
    validate_campaign_3_5_model_call_authorization,
)


VALID_GATE_STATES = {
    "WAITING_FOR_HUMAN",
    "APPROVED_INCREMENT",
    "RUNNING_INCREMENT",
    "BLOCKED",
}

DEFAULT_INCREMENT_ENV = "SOURCE_PROXY_GATE_INCREMENT"
ALLOWED_ACTIONS_ENV = "SOURCE_PROXY_GATE_ALLOWED_ACTIONS"
GATE_STATE_PATH_ENV = "SOURCE_PROXY_GATE_STATE_PATH"


class ExternalGateError(RuntimeError):
    def __init__(self, message: str, reason_code: str, payload: dict[str, Any] | None = None):
        super().__init__(message)
        self.reason_code = reason_code
        self.payload = payload or {}


@dataclass(frozen=True)
class ExternalGateReceipt:
    action: str
    increment_id: str
    run_id: str
    gate_state_before: str
    approved_increment: str
    approval_token_id: str
    checked_at: str

    def as_payload(self) -> dict[str, str]:
        return {
            "action": self.action,
            "increment_id": self.increment_id,
            "run_id": self.run_id,
            "gate_state_before": self.gate_state_before,
            "approved_increment": self.approved_increment,
            "approval_token_id": self.approval_token_id,
            "checked_at": self.checked_at,
            "central_gate_check_passed": True,
        }


def central_gate_check(
    action: str,
    increment_id: str | None = None,
    run_id: str | None = None,
    model_alias: str | None = None,
) -> ExternalGateReceipt:
    """Single required guard for Source Proxy model-call and apply paths."""
    clean_action = _clean_required(action, "action")
    clean_increment = _clean_required(
        increment_id or os.getenv(DEFAULT_INCREMENT_ENV, "1.3"),
        "increment_id",
    )
    clean_run_id = _clean_optional(run_id) or f"{clean_increment}:{clean_action}"
    if clean_action == "model_call" and clean_increment == CAMPAIGN_ID:
        return _campaign_3_5_model_call_check(
            action=clean_action,
            increment_id=clean_increment,
            run_id=clean_run_id,
            model_alias=_clean_required(model_alias, "model_alias"),
        )
    state = _read_gate_state()

    status = str(state.get("status") or "")
    approved_increment = state.get("approved_increment")
    approval_token = state.get("approval_token")

    if status not in VALID_GATE_STATES:
        raise _gate_error("Gate status is invalid.", "gate_malformed", state)
    if status == "BLOCKED":
        raise _gate_error("Gate is blocked.", "gate_blocked", state)
    if status not in {"APPROVED_INCREMENT", "RUNNING_INCREMENT"}:
        raise _gate_error("Gate is closed.", "gate_closed", state)
    if approved_increment != clean_increment:
        raise _gate_error(
            f"Approved increment {approved_increment!r} does not match {clean_increment!r}.",
            "increment_mismatch",
            state,
        )
    if not isinstance(approval_token, str) or not approval_token.strip():
        raise _gate_error("Approval token is missing.", "approval_token_missing", state)
    if not _action_allowed(clean_action):
        raise _gate_error(
            f"Action {clean_action!r} is not allowed for increment {clean_increment!r}.",
            "action_not_allowed_for_increment",
            state,
            extra={"action": clean_action, "increment_id": clean_increment},
        )

    return ExternalGateReceipt(
        action=clean_action,
        increment_id=clean_increment,
        run_id=clean_run_id,
        gate_state_before=status,
        approved_increment=approved_increment,
        approval_token_id=approval_token,
        checked_at=datetime.now(UTC).isoformat(),
    )


def _campaign_3_5_model_call_check(
    *,
    action: str,
    increment_id: str,
    run_id: str,
    model_alias: str,
) -> ExternalGateReceipt:
    try:
        authorization = validate_campaign_3_5_model_call_authorization(
            action=action,
            model_alias=model_alias,
            run_id=run_id,
        )
    except ModelCallAuthorityError as error:
        raise ExternalGateError(
            "Campaign 3.5 model-call authority denied the request.",
            error.reason_code,
            {
                "campaign_id": CAMPAIGN_ID,
                "central_gate_check_passed": False,
                "blocked_reason": error.reason_code,
                **error.details,
            },
        ) from error
    return ExternalGateReceipt(
        action=action,
        increment_id=increment_id,
        run_id=run_id,
        gate_state_before="DURABLE_CAMPAIGN_3_5_AUTHORITY",
        approved_increment=increment_id,
        approval_token_id=authorization.authorization_id,
        checked_at=authorization.checked_at,
    )


def _action_allowed(action: str) -> bool:
    allowed_raw = os.getenv(ALLOWED_ACTIONS_ENV, "").strip()
    if not allowed_raw:
        return action == "gate_implementation"
    allowed = {item.strip() for item in allowed_raw.split(",") if item.strip()}
    return action in allowed


def _read_gate_state() -> dict[str, Any]:
    path = _gate_state_path()
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as error:
        raise ExternalGateError(
            f"Gate state is missing at {path}: {error}",
            "gate_missing",
            {"gate_state_path": str(path)},
        ) from error
    try:
        state = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ExternalGateError(
            f"Gate state is malformed JSON: {error}",
            "gate_malformed",
            {"gate_state_path": str(path)},
        ) from error
    if not isinstance(state, dict):
        raise ExternalGateError(
            "Gate state must be a JSON object.",
            "gate_malformed",
            {"gate_state_path": str(path)},
        )
    return state


def _gate_state_path() -> Path:
    configured = os.getenv(GATE_STATE_PATH_ENV, "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (_repo_root() / ".gate" / "state.json").resolve()


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "package.json").is_file() and (parent / "source_proxy").is_dir():
            return parent
    return Path.cwd().resolve()


def _clean_required(value: str | None, label: str) -> str:
    clean = str(value or "").strip()
    if not clean:
        raise ExternalGateError(f"{label} is required.", f"{label}_missing")
    return clean


def _clean_optional(value: str | None) -> str:
    return str(value or "").strip()


def _gate_error(
    message: str,
    reason_code: str,
    state: dict[str, Any],
    *,
    extra: dict[str, Any] | None = None,
) -> ExternalGateError:
    payload = {
        "gate_state_before": state.get("status"),
        "approved_increment": state.get("approved_increment"),
        "central_gate_check_passed": False,
        "blocked_reason": reason_code,
    }
    if extra:
        payload.update(extra)
    return ExternalGateError(message, reason_code, payload)
