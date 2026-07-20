"""Seeded Python-family starter repositories for Campaign 3.5.

Each function represents a distinct fixture architecture and includes the
documented baseline defect/state.  Visible tests intentionally cover ordinary
behaviour; private semantic probes cover the task-specific edge conditions.
"""
from __future__ import annotations

import hashlib
from typing import Callable


class Campaign35PythonFixtureError(ValueError):
    pass


def _tag(seed: str) -> str:
    return hashlib.sha256(seed.encode("ascii")).hexdigest()[:10]


def _header(seed: str, fixture_id: str) -> str:
    return f"# Disposable Campaign 3.5 fixture: {fixture_id}\n# harmless-layout-tag: {_tag(seed)}\n"


def _fastapi_small(seed: str) -> dict[str, str]:
    header = _header(seed, "py-fastapi-small")
    return {
        "src/api/items.py": header + """PACKAGE_VERSION = \"0.9.0\"\nITEMS = [{\"id\": index} for index in range(250)]\n\ndef list_items(limit=None):\n    # Baseline defect: ignores the optional bound.\n    return list(ITEMS)\n\ndef health():\n    # Baseline defect: omits canonical package metadata.\n    return {\"status\": \"ok\"}\n""",
        "tests/test_items.py": """from src.api.items import health, list_items\n\ndef test_default_route_returns_records():\n    assert len(list_items()) == 250\n\ndef test_health_is_ok():\n    assert health()[\"status\"] == \"ok\"\n""",
        "src/api/decoy_items.py": "def list_items(limit=None): return []  # test-only decoy\n",
    }


def _library_small(seed: str) -> dict[str, str]:
    header = _header(seed, "py-library-small")
    return {
        "src/identity/email.py": header + """def normalize_email(value):\n    # Baseline: lowercases local-part too and accepts malformed values.\n    return value.strip().lower()\n""",
        "src/net/retry.py": header + """def retry_delay(attempt, base=0.25, cap=8.0, jitter=0.1, rng=None):\n    # Baseline: unbounded and non-deterministic.\n    import random\n    return base * (2 ** attempt) + random.random() * jitter\n""",
        "src/text/slug.py": header + """import re\n\ndef slug(value):\n    return re.sub(r\"[^a-z0-9]+\", \"-\", value.lower())\n""",
        "tests/test_library.py": """from src.identity.email import normalize_email\nfrom src.text.slug import slug\n\ndef test_regular_email(): assert normalize_email(\"A@Example.COM\") == \"a@example.com\"\ndef test_regular_slug(): assert slug(\"Hello world\") == \"hello-world\"\n""",
        "src/identity/legacy_email.py": "def normalize_email(value): return value  # obsolete decoy\n",
    }


def _cli_small(seed: str) -> dict[str, str]:
    header = _header(seed, "py-cli-small")
    return {
        "src/cli/main.py": header + """import os\n\ndef emit_result(result, progress, out, err):\n    out.write(f\"{result}\\n\")\n    out.write(f\"{progress}\\n\")  # Baseline: progress cannot be silenced.\n\ndef save_settings(path, value):\n    with open(path, \"w\", encoding=\"utf-8\") as handle:\n        handle.write(value)  # Baseline: non-atomic replacement.\n""",
        "tests/test_cli.py": """from io import StringIO\nfrom src.cli.main import emit_result\n\ndef test_emits_result_and_progress():\n    out = StringIO(); emit_result(\"ok\", \"working\", out, StringIO())\n    assert \"ok\" in out.getvalue()\n""",
        "docs/cli.md": "Progress is normally written beside result data.\n",
    }


def _security_small(seed: str) -> dict[str, str]:
    header = _header(seed, "py-security-small")
    return {
        "src/security/tokens.py": header + """def is_valid_token(provided, expected):\n    # Baseline vulnerability: direct equality leaks timing information.\n    return provided == expected\n""",
        "tests/test_tokens.py": """from src.security.tokens import is_valid_token\n\ndef test_valid_and_invalid_tokens():\n    assert is_valid_token(\"secret\", \"secret\")\n    assert not is_valid_token(\"wrong\", \"secret\")\n""",
        "src/security/test_helpers.py": "def compare(a, b): return a == b  # decoy, not production validation\n",
    }


def _config_small(seed: str) -> dict[str, str]:
    header = _header(seed, "py-config-small")
    return {
        "src/config/parse.py": header + """def parse_bool(value):\n    # Baseline: Python truthiness accepts every non-empty value.\n    return bool(value)\n""",
        "tests/test_parse.py": """from src.config.parse import parse_bool\n\ndef test_empty_is_false(): assert parse_bool(\"\") is False\ndef test_true_is_true(): assert parse_bool(\"true\") is True\n""",
        "docs/environment.md": "Boolean values are configured through environment variables.\n",
    }


def _fastapi_multifile(seed: str) -> dict[str, str]:
    header = _header(seed, "py-fastapi-multifile")
    return {
        "src/api/keys.py": header + """def rotate_key(repository, key_id):\n    # Baseline: immediately replaces a key and exposes no grace/audit semantics.\n    return repository.replace(key_id)\n""",
        "src/domain/keys.py": "class Key: pass\n",
        "src/repositories/keys.py": "class KeyRepository:\n    def replace(self, key_id): return {\"id\": key_id, \"secret\": \"visible-once\"}\n",
        "migrations/001_keys.sql": "CREATE TABLE api_keys (id TEXT PRIMARY KEY, secret TEXT NOT NULL);\n",
        "tests/test_key_rotation.py": "def test_existing_rotation_returns_replacement(): assert True\n",
        "src/api/legacy_keys.py": "# Decoy legacy endpoint; do not use for new rotations.\n",
    }


def _service_multifile(seed: str) -> dict[str, str]:
    header = _header(seed, "py-service-multifile")
    return {
        "src/services/signup.py": header + """def create_user(repository, mailer, user):\n    created = repository.insert_user(user)\n    mailer.send_welcome(created)  # Baseline: direct non-transactional delivery.\n    return created\n""",
        "src/services/operations.py": """def destructive_operation(actor, operation):\n    return operation()  # Baseline: no server-side policy evaluation.\n""",
        "src/workers/outbox.py": "def deliver(event, mailer): return mailer.send(event)\n",
        "config/policies.yaml": "version: 1\npolicies: []\n",
        "migrations/001_users.sql": "CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT NOT NULL);\n",
        "tests/test_services.py": "def test_user_creation(): assert True\n",
        "src/services/demo_operations.py": "def destructive_operation(*args): return None  # documentation decoy\n",
    }


def _cli_multifile(seed: str) -> dict[str, str]:
    header = _header(seed, "py-cli-multifile")
    return {
        "src/credentials/store.py": header + """from pathlib import Path\n\ndef put(path, name, value):\n    path.write_text(f\"{name}={value}\\n\")  # Baseline plaintext storage.\n\ndef get(path, name):\n    return dict(line.split(\"=\", 1) for line in path.read_text().splitlines())[name]\n""",
        "src/cli/credentials.py": "from src.credentials.store import get, put\n",
        "src/platform/keyring.py": "class Keyring: pass\n",
        "tests/test_credentials.py": "def test_command_surface_exists(): assert True\n",
        "docs/credentials.md": "Legacy credentials are stored in a local file.\n",
    }


def _service_debug(seed: str) -> dict[str, str]:
    header = _header(seed, "py-service-debug")
    return {
        "src/payments/webhooks.py": header + """def capture(repository, event):\n    # Baseline race: a duplicate delivery can capture twice.\n    repository.capture(event[\"payment_id\"])\n    return {\"ok\": True}\n""",
        "src/payments/repository.py": "class PaymentRepository:\n    def capture(self, payment_id): pass\n",
        "tests/test_webhooks.py": "def test_single_delivery(): assert True\n",
        "docs/incidents.md": "Intermittent capture reports require a concurrency reproduction.\n",
    }


def _calendar_debug(seed: str) -> dict[str, str]:
    header = _header(seed, "py-calendar-debug")
    return {
        "src/calendar/recurrence.py": header + """from datetime import timedelta\n\ndef weekly(start, count):\n    # Baseline defect: elapsed 7-day arithmetic loses local wall-time across DST.\n    return [start + timedelta(days=7 * index) for index in range(count)]\n""",
        "tests/test_recurrence.py": "def test_weekly_count(): assert True\n",
        "src/calendar/utc_recurrence.py": "def weekly(start, count): return []  # unrelated UTC-only decoy\n",
    }


def _cli_debug(seed: str) -> dict[str, str]:
    header = _header(seed, "py-cli-debug")
    return {
        "src/cli/confirm.py": header + """def confirm(stream):\n    while True:\n        value = stream.readline()\n        if value.strip().lower() in {\"y\", \"yes\"}: return True\n        if value.strip().lower() in {\"n\", \"no\"}: return False\n        # Baseline: EOF repeatedly produces an empty line and loops forever.\n""",
        "tests/test_confirm.py": "from io import StringIO\nfrom src.cli.confirm import confirm\ndef test_no(): assert confirm(StringIO('no\\n')) is False\n",
        "docs/interactive.md": "Confirmation reads standard input.\n",
    }


def _security_debug(seed: str) -> dict[str, str]:
    header = _header(seed, "py-security-debug")
    return {
        "src/authz/cache.py": header + """class PermissionCache:\n    def __init__(self): self.values = {}\n    def allowed(self, tenant_id, user_id, action, resolver):\n        key = (user_id, action)  # Baseline defect: tenant omitted.\n        if key not in self.values: self.values[key] = resolver(tenant_id, user_id, action)\n        return self.values[key]\n""",
        "tests/test_cache.py": "from src.authz.cache import PermissionCache\ndef test_same_tenant_cached():\n c=PermissionCache(); assert c.allowed('a','u','read',lambda *_:True)\n",
        "src/authz/ui_cache.py": "# Browser-only cache; not the authorization decision cache.\n",
    }


def _style_ambiguous(seed: str) -> dict[str, str]:
    header = _header(seed, "py-style-ambiguous")
    return {
        "src/reporting/formatting.py": header + """def render_report(values):\n  return  { 'count':len(values),'values':values }\n""",
        "pyproject.toml": "[tool.black]\nline-length = 88\n",
        "tests/test_formatting.py": "from src.reporting.formatting import render_report\ndef test_result(): assert render_report([1])[\"count\"] == 1\n",
        "src/reporting/legacy_formatting.py": "# Historical file intentionally retains its original style.\n",
    }


PYTHON_FIXTURE_BUILDERS: dict[str, Callable[[str], dict[str, str]]] = {
    "py-fastapi-small": _fastapi_small,
    "py-library-small": _library_small,
    "py-cli-small": _cli_small,
    "py-security-small": _security_small,
    "py-config-small": _config_small,
    "py-fastapi-multifile": _fastapi_multifile,
    "py-service-multifile": _service_multifile,
    "py-cli-multifile": _cli_multifile,
    "py-service-debug": _service_debug,
    "py-calendar-debug": _calendar_debug,
    "py-cli-debug": _cli_debug,
    "py-security-debug": _security_debug,
    "py-style-ambiguous": _style_ambiguous,
}


def build_python_fixture(fixture_id: str, seed: str) -> dict[str, str]:
    try:
        return PYTHON_FIXTURE_BUILDERS[fixture_id](seed)
    except KeyError as exc:
        raise Campaign35PythonFixtureError("campaign_3_5_python_fixture_unknown") from exc
