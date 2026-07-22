"""Private builders for disposable Basic Backend 10 public repositories.

Task-specific branching is confined to this benchmark-only package.  The
resulting repository contains only ordinary source, public tests, and normal
project metadata; raw seeds, oracle logic, and reference implementations are
never materialized into it.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping

from source_proxy.benchmarks.campaign_3_5_basic_assets.catalog import RenderedBasicBackendTask


class BasicBackendFixtureError(ValueError):
    pass


@dataclass(frozen=True)
class BasicBackendFixture:
    root: Path
    rendered_task: RenderedBasicBackendTask
    baseline_commit: str
    baseline_tree: str
    content_sha256: str
    authority_manifest: Mapping[str, object]


def materialize_basic_backend_fixture(
    fixture_parent: Path,
    rendered_task: RenderedBasicBackendTask,
) -> BasicBackendFixture:
    parent = fixture_parent.resolve(strict=True)
    if not parent.is_dir() or (parent / ".git").exists():
        raise BasicBackendFixtureError("basic_backend_fixture_parent_invalid")
    fixture_name = f"basic-{rendered_task.task_seed_commitment[:16]}"
    root = (parent / fixture_name).resolve(strict=False)
    if root.parent != parent or root.exists():
        raise BasicBackendFixtureError("basic_backend_fixture_root_invalid")
    builder = FIXTURE_BUILDERS.get(rendered_task.definition.task_id)
    if builder is None:
        raise BasicBackendFixtureError("basic_backend_fixture_builder_missing")
    files = {**_common_files(), **builder(rendered_task.values)}
    root.mkdir(mode=0o700)
    _write_files(root, files)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "basic-backend-fixture@example.invalid")
    _git(root, "config", "user.name", "Basic Backend Fixture")
    _git(root, "add", "--", *sorted(files))
    _git(root, "commit", "-qm", "frozen basic-backend fixture baseline")
    baseline_commit = _git(root, "rev-parse", "HEAD")
    baseline_tree = _git(root, "rev-parse", "HEAD^{tree}")
    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest = {
        "schema_version": "campaign-3.5-fixture-authority/v2",
        "fixture_id": f"source-proxy-basic-backend-10-{rendered_task.task_seed_commitment[:16]}",
        "workspace_root": str(root),
        "baseline_commit": baseline_commit,
        "baseline_tree": baseline_tree,
        "readable_paths": list(rendered_task.definition.readable_paths),
        "writable_paths": list(rendered_task.definition.writable_paths),
        "execution_profile": "generic-architect-coder-packet-v1",
    }
    return BasicBackendFixture(
        root=root,
        rendered_task=rendered_task,
        baseline_commit=baseline_commit,
        baseline_tree=baseline_tree,
        content_sha256=hashlib.sha256(canonical).hexdigest(),
        authority_manifest=manifest,
    )


def _common_files() -> dict[str, str]:
    return {
        "pyproject.toml": (
            "[tool.pytest.ini_options]\n"
            "testpaths = [\"tests\"]\n"
            "addopts = \"--strict-markers\"\n"
        ),
        "src/__init__.py": "",
        "tests/conftest.py": (
            "from __future__ import annotations\n\n"
            "import sys\n"
            "from pathlib import Path\n\n"
            "sys.path.insert(0, str(Path(__file__).resolve().parents[1]))\n"
        ),
    }


def _bt01(values: Mapping[str, str | int]) -> dict[str, str]:
    parameter = str(values["limit_parameter"])
    maximum = int(values["maximum_limit"])
    resource = str(values["resource_name"])
    items = ",\n    ".join(f'{{"id": {index}, "name": "{resource}-{index}"}}' for index in range(1, maximum + 3))
    return {
        "src/backend.py": f'''from __future__ import annotations

ITEMS = (
    {items},
)
ROUTE = "/{resource}s"


def list_items(query: dict[str, str]) -> dict[str, object]:
    """Return the existing endpoint response."""
    return {{"status": 200, "body": {{"items": [dict(item) for item in ITEMS]}}}}
''',
        "tests/test_backend.py": f'''from src.backend import ITEMS, list_items


def test_omitted_parameter_preserves_existing_response():
    response = list_items({{}})
    assert response == {{"status": 200, "body": {{"items": [dict(item) for item in ITEMS]}}}}


def test_valid_optional_limit_is_applied_without_mutation():
    before = tuple(dict(item) for item in ITEMS)
    response = list_items({{"{parameter}": "2"}})
    assert response["status"] == 200
    assert len(response["body"]["items"]) == 2
    assert tuple(ITEMS) == before
''',
    }


def _bt02(values: Mapping[str, str | int]) -> dict[str, str]:
    function_name = str(values["function_name"])
    sample = int(values["sample_value"])
    return {
        "src/backend.py": f'''from __future__ import annotations


def {function_name}(values: list[int]) -> int:
    return sum(values[:-1])
''',
        "tests/test_backend.py": f'''from src.backend import {function_name}


def test_all_values_are_included():
    values = [3, {sample}, 5]
    assert {function_name}(values) == 3 + {sample} + 5


def test_input_is_not_mutated():
    values = [1, 2, 3]
    before = list(values)
    {function_name}(values)
    assert values == before
''',
    }


def _bt03(values: Mapping[str, str | int]) -> dict[str, str]:
    field = str(values["response_field"])
    instance = str(values["instance_value"])
    return {
        "src/backend.py": f'''from __future__ import annotations

SERVICE_INSTANCE_ID = "{instance}"


def get_status() -> dict[str, object]:
    return {{"status": "ok", "version": 1}}
''',
        "tests/test_backend.py": f'''from src.backend import SERVICE_INSTANCE_ID, get_status


def test_status_keeps_existing_fields_and_adds_instance():
    response = get_status()
    assert response["status"] == "ok"
    assert response["version"] == 1
    assert response["{field}"] == SERVICE_INSTANCE_ID
''',
    }


def _bt04(values: Mapping[str, str | int]) -> dict[str, str]:
    field = str(values["field_name"])
    valid = str(values["valid_value"])
    return {
        "src/backend.py": f'''from __future__ import annotations

ACCOUNTS: list[dict[str, object]] = []


def create_account(payload: dict[str, object]) -> dict[str, object]:
    account = {{"id": len(ACCOUNTS) + 1, "{field}": payload.get("{field}")}}
    ACCOUNTS.append(account)
    return {{"status": 201, "body": account}}
''',
        "tests/test_backend.py": f'''from src.backend import ACCOUNTS, create_account


def setup_function():
    ACCOUNTS.clear()


def test_valid_account_is_created():
    response = create_account({{"{field}": "{valid}"}})
    assert response["status"] == 201
    assert response["body"]["{field}"] == "{valid}"


def test_blank_value_is_rejected_without_storage_mutation():
    response = create_account({{"{field}": "   "}})
    assert response["status"] == 422
    assert "error" in response["body"]
    assert ACCOUNTS == []
''',
    }


def _bt05(values: Mapping[str, str | int]) -> dict[str, str]:
    prefix = str(values["record_prefix"])
    count = int(values["record_count"])
    records = ",\n    ".join(f'{{"id": {index}, "name": "{prefix}{index}"}}' for index in range(count))
    return {
        "src/backend.py": f'''from __future__ import annotations

RECORDS = [
    {records},
]


def list_records(offset: int = 0, limit: int | None = None) -> list[dict[str, object]]:
    del RECORDS[:offset]
    if limit is None:
        return RECORDS
    return RECORDS[:limit]
''',
        "tests/test_backend.py": '''from src.backend import RECORDS, list_records


def test_pagination_does_not_mutate_storage():
    before = [dict(record) for record in RECORDS]
    assert list_records(offset=1, limit=2) == before[1:3]
    assert RECORDS == before


def test_defaults_return_independent_copy_of_all_records():
    before = [dict(record) for record in RECORDS]
    result = list_records()
    assert result == before
    assert result is not RECORDS
''',
    }


def _bt06(values: Mapping[str, str | int]) -> dict[str, str]:
    status_name = str(values["status_name"])
    status_value = str(values["status_value"])
    return {
        "src/service.py": f'''from __future__ import annotations

ORDERS = (
    {{"id": 1, "status": "{status_value}"}},
    {{"id": 2, "status": "pending"}},
    {{"id": 3, "status": "{status_value}"}},
)


def find_order(order_id: int) -> dict[str, object] | None:
    return next((dict(order) for order in ORDERS if order["id"] == order_id), None)
''',
        "tests/test_service.py": f'''from src import service


def test_existing_lookup_is_preserved():
    assert service.find_order(1) == {{"id": 1, "status": "{status_value}"}}
''',
    }


def _bt07(values: Mapping[str, str | int]) -> dict[str, str]:
    user = str(values["sample_user"])
    domain = str(values["sample_domain"])
    return {
        "src/users.py": '''from __future__ import annotations


def normalize_username(value: str) -> str:
    return value.strip().lower()

''',
        "src/contacts.py": '''from __future__ import annotations


def normalize_email(value: str) -> str:
    return value.strip().lower()
''',
        "tests/test_service.py": f'''from src.contacts import normalize_email
from src.users import normalize_username


def test_normalizers_preserve_current_behavior():
    assert normalize_username("  {user.upper()}  ") == "{user}"
    assert normalize_email("  USER@{domain.upper()}.TEST ") == "user@{domain}.test"
''',
    }


def _bt08(values: Mapping[str, str | int]) -> dict[str, str]:
    environment = str(values["environment_name"])
    default = int(values["default_value"])
    return {
        "src/config.py": f'''from __future__ import annotations

import os

ENVIRONMENT_NAME = "{environment}"
DEFAULT_TIMEOUT = {default}


def load_timeout() -> int:
    raw = os.getenv(ENVIRONMENT_NAME)
    if raw is None:
        return DEFAULT_TIMEOUT
    return int(raw)
''',
        "tests/test_config.py": f'''import pytest

from src.config import DEFAULT_TIMEOUT, ENVIRONMENT_NAME, load_timeout


def test_missing_and_blank_values_use_default(monkeypatch):
    monkeypatch.delenv(ENVIRONMENT_NAME, raising=False)
    assert load_timeout() == {default}
    monkeypatch.setenv(ENVIRONMENT_NAME, "   ")
    assert load_timeout() == DEFAULT_TIMEOUT


def test_positive_integer_is_loaded(monkeypatch):
    monkeypatch.setenv(ENVIRONMENT_NAME, "37")
    assert load_timeout() == 37
''',
    }


def _bt09(values: Mapping[str, str | int]) -> dict[str, str]:
    destination = str(values["destination"])
    secret = str(values["secret_value"])
    return {
        "src/backend.py": '''from __future__ import annotations

import logging
from typing import Any

LOGGER = logging.getLogger(__name__)


def deliver_message(client: Any, destination: str, body: str, config: dict[str, str]) -> None:
    try:
        client.send(destination, body, token=config["api_token"])
    except Exception:
        LOGGER.error("delivery failed: config=%r body=%r", config, body)
        raise
''',
        "tests/test_backend.py": f'''import logging

import pytest

from src.backend import deliver_message


class BrokenClient:
    def send(self, *args, **kwargs):
        raise ConnectionError("offline")


def test_failure_log_is_useful_and_safe(caplog):
    caplog.set_level(logging.ERROR)
    with pytest.raises(ConnectionError):
        deliver_message(BrokenClient(), "{destination}", "private body", {{"api_token": "{secret}", "password": "pw"}})
    text = caplog.text
    assert "{destination}" in text
    assert "ConnectionError" in text
    assert "{secret}" not in text
    assert "private body" not in text
''',
    }


def _bt10(values: Mapping[str, str | int]) -> dict[str, str]:
    dependency = str(values["dependency_name"])
    profile_id = int(values["profile_id"])
    return {
        "src/backend.py": f'''from __future__ import annotations

from typing import Any

DEPENDENCY_NAME = "{dependency}"


class DependencyUnavailable(RuntimeError):
    pass


def fetch_profile(client: Any, profile_id: int) -> dict[str, object]:
    return client.fetch(profile_id)
''',
        "tests/test_backend.py": f'''import pytest

from src.backend import DEPENDENCY_NAME, DependencyUnavailable, fetch_profile


class WorkingClient:
    def fetch(self, profile_id):
        return {{"id": profile_id}}


class OfflineClient:
    def fetch(self, profile_id):
        raise ConnectionError("connection refused")


def test_success_is_preserved():
    assert fetch_profile(WorkingClient(), {profile_id}) == {{"id": {profile_id}}}


def test_unavailable_dependency_has_actionable_wrapped_error():
    with pytest.raises(DependencyUnavailable) as caught:
        fetch_profile(OfflineClient(), {profile_id})
    assert DEPENDENCY_NAME in str(caught.value)
    assert "retry" in str(caught.value).lower()
    assert isinstance(caught.value.__cause__, ConnectionError)
''',
    }


FIXTURE_BUILDERS: dict[str, Callable[[Mapping[str, str | int]], dict[str, str]]] = {
    "BT01": _bt01,
    "BT02": _bt02,
    "BT03": _bt03,
    "BT04": _bt04,
    "BT05": _bt05,
    "BT06": _bt06,
    "BT07": _bt07,
    "BT08": _bt08,
    "BT09": _bt09,
    "BT10": _bt10,
}


def _write_files(root: Path, files: Mapping[str, str]) -> None:
    root_resolved = root.resolve(strict=True)
    for relative, content in sorted(files.items()):
        candidate = PurePosixPath(relative)
        if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
            raise BasicBackendFixtureError("basic_backend_fixture_path_invalid")
        path = root.joinpath(*candidate.parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        resolved_parent = path.parent.resolve(strict=True)
        if resolved_parent != root_resolved and root_resolved not in resolved_parent.parents:
            raise BasicBackendFixtureError("basic_backend_fixture_path_invalid")
        path.write_text(content, encoding="utf-8", newline="\n")


def _git(root: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
            env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise BasicBackendFixtureError("basic_backend_fixture_git_failed") from error
    return completed.stdout.strip()
