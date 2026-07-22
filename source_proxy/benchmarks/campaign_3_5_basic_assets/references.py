"""Private known-good references used only to prove fixture solvability.

Nothing in this module is imported by production dispatch.  The reference
source is never copied into a prompt, public test result, or scored receipt.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping

from source_proxy.benchmarks.campaign_3_5_basic_assets.fixtures import BasicBackendFixture


class BasicBackendReferenceError(ValueError):
    pass


def apply_reference(fixture: BasicBackendFixture) -> None:
    writer = REFERENCE_WRITERS.get(fixture.rendered_task.definition.task_id)
    if writer is None:
        raise BasicBackendReferenceError("basic_backend_reference_missing")
    root = fixture.root.resolve(strict=True)
    result = writer(fixture.rendered_task.values)
    files = {result[0]: result[1]} if isinstance(result, tuple) else dict(result)
    for relative, content in files.items():
        target = (fixture.root / relative).resolve(strict=False)
        if root not in target.parents or target.is_symlink():
            raise BasicBackendReferenceError("basic_backend_reference_target_invalid")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")


def _bt01(values: Mapping[str, str | int]) -> tuple[str, str]:
    parameter = str(values["limit_parameter"])
    maximum = int(values["maximum_limit"])
    resource = str(values["resource_name"])
    items = ",\n    ".join(f'{{"id": {index}, "name": "{resource}-{index}"}}' for index in range(1, maximum + 3))
    return "src/backend.py", f'''from __future__ import annotations

ITEMS = (
    {items},
)
ROUTE = "/{resource}s"


def list_items(query: dict[str, str]) -> dict[str, object]:
    raw_limit = query.get("{parameter}")
    if raw_limit is None:
        selected = ITEMS
    elif not isinstance(raw_limit, str) or not raw_limit.isdigit():
        return {{"status": 400, "body": {{"error": "{parameter} must be a whole number from 1 through {maximum}"}}}}
    else:
        limit = int(raw_limit)
        if limit < 1 or limit > {maximum}:
            return {{"status": 400, "body": {{"error": "{parameter} must be a whole number from 1 through {maximum}"}}}}
        selected = ITEMS[:limit]
    return {{"status": 200, "body": {{"items": [dict(item) for item in selected]}}}}
'''


def _bt02(values: Mapping[str, str | int]) -> tuple[str, str]:
    function_name = str(values["function_name"])
    return "src/backend.py", f'''from __future__ import annotations


def {function_name}(values: list[int]) -> int:
    return sum(values)
'''


def _bt03(values: Mapping[str, str | int]) -> tuple[str, str]:
    field = str(values["response_field"])
    instance = str(values["instance_value"])
    return "src/backend.py", f'''from __future__ import annotations

SERVICE_INSTANCE_ID = "{instance}"


def get_status() -> dict[str, object]:
    return {{"status": "ok", "version": 1, "{field}": SERVICE_INSTANCE_ID}}
'''


def _bt04(values: Mapping[str, str | int]) -> tuple[str, str]:
    field = str(values["field_name"])
    return "src/backend.py", f'''from __future__ import annotations

ACCOUNTS: list[dict[str, object]] = []


def create_account(payload: dict[str, object]) -> dict[str, object]:
    value = payload.get("{field}")
    if not isinstance(value, str) or not value.strip():
        return {{"status": 422, "body": {{"error": "{field} must be a non-blank string"}}}}
    account = {{"id": len(ACCOUNTS) + 1, "{field}": value}}
    ACCOUNTS.append(account)
    return {{"status": 201, "body": account}}
'''


def _bt05(values: Mapping[str, str | int]) -> tuple[str, str]:
    prefix = str(values["record_prefix"])
    count = int(values["record_count"])
    records = ",\n    ".join(f'{{"id": {index}, "name": "{prefix}{index}"}}' for index in range(count))
    return "src/backend.py", f'''from __future__ import annotations

RECORDS = [
    {records},
]


def list_records(offset: int = 0, limit: int | None = None) -> list[dict[str, object]]:
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be a non-negative integer")
    if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit < 1):
        raise ValueError("limit must be a positive integer")
    end = None if limit is None else offset + limit
    return [dict(record) for record in RECORDS[offset:end]]
'''


def _bt06(values: Mapping[str, str | int]) -> Mapping[str, str]:
    status_name = str(values["status_name"])
    status_value = str(values["status_value"])
    function_name = f"count_{status_name}_orders"
    return {
        "src/service.py": f'''from __future__ import annotations

ORDERS = (
    {{"id": 1, "status": "{status_value}"}},
    {{"id": 2, "status": "pending"}},
    {{"id": 3, "status": "{status_value}"}},
)


def find_order(order_id: int) -> dict[str, object] | None:
    return next((dict(order) for order in ORDERS if order["id"] == order_id), None)


def {function_name}() -> int:
    return sum(1 for order in ORDERS if order["status"] == "{status_value}")
''',
        "tests/test_service.py": f'''from src import service


def test_existing_lookup_is_preserved():
    assert service.find_order(1) == {{"id": 1, "status": "{status_value}"}}


def test_{status_name}_order_count():
    assert service.{function_name}() == 2
''',
    }


def _bt07(values: Mapping[str, str | int]) -> Mapping[str, str]:
    del values
    return {
        "src/normalization.py": '''from __future__ import annotations


def normalize_identity(value: str) -> str:
    return value.strip().lower()
''',
        "src/users.py": '''from __future__ import annotations

from src.normalization import normalize_identity


def normalize_username(value: str) -> str:
    return normalize_identity(value)
''',
        "src/contacts.py": '''from __future__ import annotations

from src.normalization import normalize_identity


def normalize_email(value: str) -> str:
    return normalize_identity(value)
''',
    }


def _bt08(values: Mapping[str, str | int]) -> tuple[str, str]:
    environment = str(values["environment_name"])
    default = int(values["default_value"])
    return "src/config.py", f'''from __future__ import annotations

import os

ENVIRONMENT_NAME = "{environment}"
DEFAULT_TIMEOUT = {default}


def load_timeout() -> int:
    raw = os.getenv(ENVIRONMENT_NAME)
    if raw is None or not raw.strip():
        return DEFAULT_TIMEOUT
    try:
        value = int(raw)
    except ValueError as error:
        raise ValueError(f"{{ENVIRONMENT_NAME}} must be a positive integer") from error
    if value <= 0:
        raise ValueError(f"{{ENVIRONMENT_NAME}} must be a positive integer")
    return value
'''


def _bt09(values: Mapping[str, str | int]) -> tuple[str, str]:
    del values
    return "src/backend.py", '''from __future__ import annotations

import logging
from typing import Any

LOGGER = logging.getLogger(__name__)


def deliver_message(client: Any, destination: str, body: str, config: dict[str, str]) -> None:
    try:
        client.send(destination, body, token=config["api_token"])
    except Exception as error:
        LOGGER.error("delivery to %s failed with %s", destination, type(error).__name__)
        raise
'''


def _bt10(values: Mapping[str, str | int]) -> tuple[str, str]:
    dependency = str(values["dependency_name"])
    return "src/backend.py", f'''from __future__ import annotations

from typing import Any

DEPENDENCY_NAME = "{dependency}"


class DependencyUnavailable(RuntimeError):
    pass


def fetch_profile(client: Any, profile_id: int) -> dict[str, object]:
    try:
        return client.fetch(profile_id)
    except (ConnectionError, TimeoutError, OSError) as error:
        raise DependencyUnavailable(f"{{DEPENDENCY_NAME}} is unavailable; retry later") from error
'''


REFERENCE_WRITERS: dict[
    str,
    Callable[[Mapping[str, str | int]], tuple[str, str] | Mapping[str, str]],
] = {
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
