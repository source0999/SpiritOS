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
from typing import Callable, Mapping, Sequence
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
        (
            "inclusive_limits",
            valid_one
            == {"status": 200, "body": {"items": [dict(item) for item in before[:1]]}}
            and valid_max
            == {
                "status": 200,
                "body": {"items": [dict(item) for item in before[:maximum]]},
            },
        ),
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
        (
            "focused_test_added",
            _test_function_invoked_by_test(test_source, function.__name__),
        ),
    )


def _bt07(root: Path, values: Mapping[str, str | int]) -> tuple[tuple[str, bool], ...]:
    del values
    users_source = (root / "src/users.py").read_text(encoding="utf-8")
    contacts_source = (root / "src/contacts.py").read_text(encoding="utf-8")
    users = _package_module(root, "src.users")
    contacts = _package_module(root, "src.contacts")
    helper_modules = {
        path.stem
        for path in (root / "src").glob("*.py")
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
        ("behavior_preserved", users.normalize_username(" A.B ") == "a.b" and contacts.normalize_email(" X@Y.TEST ") == "x@y.test"),
        ("shared_helper", bool(helper_modules) and bool(shared_usage)),
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
