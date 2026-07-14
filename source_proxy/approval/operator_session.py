"""Verifies short-lived server assertions from the local operator session route."""
import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from pathlib import Path


class OperatorSessionError(ValueError):
    pass


def _secret() -> str:
    value = os.environ.get("SPIRITOS_OPERATOR_E2E_SECRET", "") if os.environ.get("SPIRITOS_OPERATOR_E2E_MODE") == "true" else ""
    if value:
        return value
    location = Path("/home/source/.config/spiritos/secrets/operator-approval.env")
    try:
        if location.stat().st_mode & 0o777 != 0o600:
            raise OperatorSessionError("operator_unsafe_secret_permissions")
        value = location.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise OperatorSessionError("operator_secret_unavailable") from error
    if not value.startswith("SPIRITOS_OPERATOR_CREDENTIAL="):
        raise OperatorSessionError("operator_secret_malformed")
    return value.split("=", 1)[1]


def _state_path() -> Path:
    if os.environ.get("SPIRITOS_OPERATOR_E2E_MODE") == "true" and os.environ.get("SPIRITOS_OPERATOR_E2E_STATE_PATH"):
        return Path(os.environ["SPIRITOS_OPERATOR_E2E_STATE_PATH"])
    return Path("/home/source/.local/state/spiritos/operator-approval-sessions.json")


def _parse_time(value: object, reason: str) -> datetime:
    if not isinstance(value, str):
        raise OperatorSessionError(reason)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise OperatorSessionError(reason) from error
    if parsed.tzinfo is None:
        raise OperatorSessionError(reason)
    return parsed.astimezone(timezone.utc)


def verify_operator_approval_assertion(assertion: str) -> dict[str, object]:
    try:
        encoded, signature = assertion.split(".", 1)
        expected = hmac.new(_secret().encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest()
        supplied = base64.urlsafe_b64decode(signature + "=" * (-len(signature) % 4))
        payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
    except (ValueError, UnicodeError, json.JSONDecodeError) as error:
        raise OperatorSessionError("operator_assertion_invalid") from error
    if not hmac.compare_digest(expected, supplied) or not isinstance(payload, dict):
        raise OperatorSessionError("operator_assertion_invalid")
    required = {"action", "expires_at", "generation", "operator", "preview_id", "role", "session_id", "task_id"}
    if set(payload) != required or payload["operator"] != "spiritos-local-operator" or payload["role"] != "approval-issuer":
        raise OperatorSessionError("operator_assertion_invalid")
    if payload["action"] not in {"approve", "reject"} or not isinstance(payload["generation"], int) or payload["generation"] < 1:
        raise OperatorSessionError("operator_assertion_invalid")
    expires_at = _parse_time(payload["expires_at"], "operator_assertion_invalid")
    now = datetime.now(timezone.utc)
    if expires_at <= now or (expires_at - now).total_seconds() > 90:
        raise OperatorSessionError("operator_assertion_expired")
    try:
        state = json.loads(_state_path().read_text(encoding="utf-8"))
        session = state["sessions"][payload["session_id"]]
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise OperatorSessionError("operator_session_invalid") from error
    if session.get("revoked_at"):
        raise OperatorSessionError("operator_session_revoked")
    if _parse_time(session.get("expires_at"), "operator_session_invalid") <= now:
        raise OperatorSessionError("operator_session_expired")
    return payload
