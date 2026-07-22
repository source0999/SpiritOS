"""Private independent behavioral oracles for Basic Backend 10.

Oracle results are retained in the private evaluation store.  Production
dispatch receives neither these checks nor their failure detail.
"""
from __future__ import annotations

import ast
import importlib
import importlib.util
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Callable, Mapping
from uuid import uuid4


class BasicBackendOracleError(ValueError):
    pass


@dataclass(frozen=True)
class PrivateOracleResult:
    task_id: str
    passed: bool
    checks: tuple[tuple[str, bool], ...]

    def private_payload(self) -> dict[str, object]:
        return {
            "schema_version": "source-proxy-basic-backend-10-private-oracle/v1",
            "task_id": self.task_id,
            "passed": self.passed,
            "checks": [{"name": name, "passed": passed} for name, passed in self.checks],
        }


def evaluate_private_oracle(
    task_id: str,
    workspace_root: Path,
    values: Mapping[str, str | int],
) -> PrivateOracleResult:
    evaluator = ORACLES.get(task_id)
    if evaluator is None:
        raise BasicBackendOracleError("basic_backend_oracle_missing")
    root = workspace_root.resolve(strict=True)
    if not (root / ".git").exists():
        raise BasicBackendOracleError("basic_backend_oracle_workspace_invalid")
    try:
        checks = evaluator(root, values)
    except Exception:
        # The private report identifies an oracle execution failure without
        # exposing hidden inputs to the production repair loop.
        checks = (("oracle_execution", False),)
    return PrivateOracleResult(task_id=task_id, passed=all(value for _, value in checks), checks=checks)


def _bt01(root: Path, values: Mapping[str, str | int]) -> tuple[tuple[str, bool], ...]:
    module = _module(root / "src/backend.py")
    parameter = str(values["limit_parameter"])
    maximum = int(values["maximum_limit"])
    before = tuple(dict(item) for item in module.ITEMS)
    omitted = module.list_items({})
    valid_one = module.list_items({parameter: "1"})
    valid_max = module.list_items({parameter: str(maximum)})
    invalid = [module.list_items({parameter: value}) for value in ("", "0", str(maximum + 1), "1.5", "nope")]
    return (
        ("omitted_compatibility", omitted == {"status": 200, "body": {"items": [dict(item) for item in before]}}),
        ("inclusive_limits", len(valid_one["body"]["items"]) == 1 and len(valid_max["body"]["items"]) == maximum),
        ("invalid_values", all(response.get("status") == 400 and response.get("body", {}).get("error") for response in invalid)),
        ("storage_immutable", tuple(module.ITEMS) == before),
    )


def _bt02(root: Path, values: Mapping[str, str | int]) -> tuple[tuple[str, bool], ...]:
    module = _module(root / "src/backend.py")
    function = getattr(module, str(values["function_name"]))
    data = [4, -2, 9, 0]
    before = list(data)
    return (
        ("complete_sum", function(data) == 11 and function([7]) == 7 and function([]) == 0),
        ("input_immutable", data == before),
    )


def _bt03(root: Path, values: Mapping[str, str | int]) -> tuple[tuple[str, bool], ...]:
    module = _module(root / "src/backend.py")
    field = str(values["response_field"])
    response = module.get_status()
    return (
        ("existing_contract", response.get("status") == "ok" and response.get("version") == 1),
        ("new_field", response.get(field) == module.SERVICE_INSTANCE_ID),
        ("json_shape", set(response) == {"status", "version", field}),
    )


def _bt04(root: Path, values: Mapping[str, str | int]) -> tuple[tuple[str, bool], ...]:
    module = _module(root / "src/backend.py")
    field = str(values["field_name"])
    module.ACCOUNTS.clear()
    invalid = [module.create_account(payload) for payload in ({}, {field: None}, {field: 5}, {field: "\t"})]
    no_invalid_writes = module.ACCOUNTS == []
    valid = module.create_account({field: " valid "})
    return (
        ("invalid_status", all(response.get("status") == 422 and response.get("body", {}).get("error") for response in invalid)),
        ("invalid_storage_immutable", no_invalid_writes),
        ("valid_compatibility", valid.get("status") == 201 and valid.get("body", {}).get(field) == " valid "),
    )


def _bt05(root: Path, values: Mapping[str, str | int]) -> tuple[tuple[str, bool], ...]:
    del values
    module = _module(root / "src/backend.py")
    before = [dict(record) for record in module.RECORDS]
    first = module.list_records(offset=2, limit=3)
    second = module.list_records(offset=2, limit=3)
    invalid_raised = True
    for args in ((-1, None), (0, 0), (0, -1), (True, None), (0, False), ("1", None)):
        try:
            module.list_records(offset=args[0], limit=args[1])
        except ValueError:
            continue
        invalid_raised = False
    defaults = module.list_records()
    return (
        ("page_semantics", first == before[2:5] and second == first),
        ("storage_immutable", module.RECORDS == before),
        ("invalid_values", invalid_raised),
        ("independent_default_result", defaults == before and defaults is not module.RECORDS),
    )


def _bt06(root: Path, values: Mapping[str, str | int]) -> tuple[tuple[str, bool], ...]:
    module = _module(root / "src/service.py")
    function = getattr(module, f"count_{values['status_name']}_orders")
    before = tuple(dict(order) for order in module.ORDERS)
    test_source = (root / "tests/test_service.py").read_text(encoding="utf-8")
    return (
        ("exact_status_count", function() == 2),
        ("existing_lookup", module.find_order(2) == {"id": 2, "status": "pending"} and module.find_order(999) is None),
        ("storage_immutable", tuple(module.ORDERS) == before),
        ("focused_test_added", f"{function.__name__}()" in test_source and "def test_" in test_source),
    )


def _bt07(root: Path, values: Mapping[str, str | int]) -> tuple[tuple[str, bool], ...]:
    del values
    users_source = (root / "src/users.py").read_text(encoding="utf-8")
    contacts_source = (root / "src/contacts.py").read_text(encoding="utf-8")
    users = _package_module(root, "src.users")
    contacts = _package_module(root, "src.contacts")
    users_imports = _imported_names(users_source)
    contacts_imports = _imported_names(contacts_source)
    shared = (users_imports & contacts_imports) - {"annotations"}
    helper_exists = any(
        path.name not in {"users.py", "contacts.py", "__init__.py"}
        and path.is_file()
        for path in (root / "src").glob("*.py")
    )
    return (
        ("behavior_preserved", users.normalize_username(" A.B ") == "a.b" and contacts.normalize_email(" X@Y.TEST ") == "x@y.test"),
        ("shared_helper", helper_exists and bool(shared)),
    )


def _bt08(root: Path, values: Mapping[str, str | int]) -> tuple[tuple[str, bool], ...]:
    module = _module(root / "src/config.py")
    name = str(values["environment_name"])
    original = os.environ.get(name)
    present = name in os.environ
    try:
        os.environ.pop(name, None)
        missing = module.load_timeout()
        blanks = []
        for raw in ("", " ", "\t"):
            os.environ[name] = raw
            blanks.append(module.load_timeout())
        os.environ[name] = "41"
        positive = module.load_timeout()
        invalid_raised = True
        for raw in ("0", "-3", "abc"):
            os.environ[name] = raw
            try:
                module.load_timeout()
            except ValueError:
                continue
            invalid_raised = False
    finally:
        if present:
            os.environ[name] = str(original)
        else:
            os.environ.pop(name, None)
    return (
        ("default_semantics", missing == module.DEFAULT_TIMEOUT and blanks == [module.DEFAULT_TIMEOUT] * 3),
        ("positive_value", positive == 41),
        ("invalid_values", invalid_raised),
    )


def _bt09(root: Path, values: Mapping[str, str | int]) -> tuple[tuple[str, bool], ...]:
    module = _module(root / "src/backend.py")
    destination = str(values["destination"])
    secret = str(values["secret_value"])
    body = "hidden-message-body"
    password = "hidden-password"
    failure = ConnectionError(f"offline:{secret}")

    class BrokenClient:
        def send(self, *args: object, **kwargs: object) -> None:
            raise failure

    class Capture(logging.Handler):
        def __init__(self) -> None:
            super().__init__()
            self.messages: list[str] = []

        def emit(self, record: logging.LogRecord) -> None:
            self.messages.append(record.getMessage())

    capture = Capture()
    module.LOGGER.addHandler(capture)
    module.LOGGER.setLevel(logging.ERROR)
    raised_same = False
    try:
        module.deliver_message(BrokenClient(), destination, body, {"api_token": secret, "password": password})
    except ConnectionError as error:
        raised_same = error is failure
    finally:
        module.LOGGER.removeHandler(capture)
    text = " ".join(capture.messages)
    return (
        ("useful_log", destination in text and "ConnectionError" in text),
        ("secrets_absent", all(value not in text for value in (secret, password, body))),
        ("original_error_reraised", raised_same),
    )


def _bt10(root: Path, values: Mapping[str, str | int]) -> tuple[tuple[str, bool], ...]:
    module = _module(root / "src/backend.py")
    profile_id = int(values["profile_id"])

    class WorkingClient:
        def fetch(self, value: int) -> dict[str, object]:
            return {"id": value, "ok": True}

    failure = ConnectionError("offline")

    class OfflineClient:
        def fetch(self, value: int) -> dict[str, object]:
            del value
            raise failure

    success = module.fetch_profile(WorkingClient(), profile_id)
    wrapped = None
    try:
        module.fetch_profile(OfflineClient(), profile_id)
    except module.DependencyUnavailable as error:
        wrapped = error
    message = str(wrapped or "").lower()
    return (
        ("success_preserved", success == {"id": profile_id, "ok": True}),
        ("truthful_actionable_error", wrapped is not None and module.DEPENDENCY_NAME.lower() in message and "retry" in message),
        ("cause_preserved", wrapped is not None and wrapped.__cause__ is failure),
    )


ORACLES: dict[
    str,
    Callable[[Path, Mapping[str, str | int]], tuple[tuple[str, bool], ...]],
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


def _module(path: Path) -> ModuleType:
    root = path.resolve(strict=True)
    name = f"campaign35_basic_oracle_{uuid4().hex}"
    specification = importlib.util.spec_from_file_location(name, root)
    if specification is None or specification.loader is None:
        raise BasicBackendOracleError("basic_backend_oracle_import_failed")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _package_module(root: Path, qualified_name: str) -> ModuleType:
    workspace = str(root.resolve(strict=True))
    previous = {name: module for name, module in sys.modules.items() if name == "src" or name.startswith("src.")}
    for name in previous:
        sys.modules.pop(name, None)
    sys.path.insert(0, workspace)
    try:
        return importlib.import_module(qualified_name)
    finally:
        sys.path.remove(workspace)
        for name in tuple(sys.modules):
            if name == "src" or name.startswith("src."):
                sys.modules.pop(name, None)
        sys.modules.update(previous)


def _imported_names(source: str) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
    return names
