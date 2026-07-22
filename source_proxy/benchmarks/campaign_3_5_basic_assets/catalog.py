"""Validated catalog for the private Basic Backend 10 asset harness."""
from __future__ import annotations

import json
import hashlib
import string
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from source_proxy.benchmarks.campaign_3_5_basic_assets.seeding import (
    BasicBackendRunSeed,
    derive_task_digest,
    render_randomized_fields,
    task_seed_commitment,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PUBLIC_ROOT = REPOSITORY_ROOT / "benchmarks" / "source-proxy-basic-backend-10" / "v1"
PUBLIC_TASKS_PATH = PUBLIC_ROOT / "tasks.json"
EXPECTED_TASK_IDS = tuple(f"BT{index:02d}" for index in range(1, 11))
_PRIVATE_FIELD_NAMES = {
    "answer",
    "expected_patch",
    "hidden_check",
    "oracle",
    "reference",
    "solution",
}


class BasicBackendCatalogError(ValueError):
    pass


@dataclass(frozen=True)
class BasicBackendTask:
    task_id: str
    category: str
    fixture_family: str
    prompt_template: str
    randomized_fields: tuple[Mapping[str, Any], ...]
    public_test_command: str
    readable_paths: tuple[str, ...]
    writable_paths: tuple[str, ...]
    forbidden_mutations: tuple[str, ...]
    expected_terminal_disposition: str
    trace_requirements: tuple[str, ...]

    def render(self, task_digest: str) -> tuple[str, dict[str, str | int]]:
        values = render_randomized_fields(task_digest, list(self.randomized_fields))
        if "resource_name" in values:
            values["route"] = f"/{values['resource_name']}s"
        try:
            prompt = self.prompt_template.format(**values)
        except (KeyError, ValueError) as error:
            raise BasicBackendCatalogError("basic_backend_prompt_template_invalid") from error
        return prompt, values


@dataclass(frozen=True)
class RenderedBasicBackendTask:
    definition: BasicBackendTask
    prompt: str
    values: Mapping[str, str | int]
    task_seed_commitment: str


def load_basic_backend_tasks(path: Path = PUBLIC_TASKS_PATH) -> tuple[BasicBackendTask, ...]:
    if path.resolve() == PUBLIC_TASKS_PATH.resolve():
        validate_public_contract(PUBLIC_ROOT)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BasicBackendCatalogError("basic_backend_public_catalog_unreadable") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != "source-proxy-basic-backend-10/v1":
        raise BasicBackendCatalogError("basic_backend_public_catalog_schema_invalid")
    records = payload.get("tasks")
    if not isinstance(records, list) or payload.get("task_count") != 10 or len(records) != 10:
        raise BasicBackendCatalogError("basic_backend_public_catalog_count_invalid")
    if _contains_private_key(payload):
        raise BasicBackendCatalogError("basic_backend_public_catalog_private_data")
    tasks = tuple(_parse_task(record) for record in records)
    if tuple(task.task_id for task in tasks) != EXPECTED_TASK_IDS:
        raise BasicBackendCatalogError("basic_backend_public_catalog_ids_invalid")
    return tasks


def validate_public_contract(root: Path = PUBLIC_ROOT) -> dict[str, Any]:
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BasicBackendCatalogError("basic_backend_public_freeze_unreadable") from error
    if (
        not isinstance(manifest, dict)
        or manifest.get("schema_version") != "source-proxy-basic-backend-10-public-freeze/v1"
        or manifest.get("task_count") != 10
        or tuple(manifest.get("required_task_ids") or ()) != EXPECTED_TASK_IDS
    ):
        raise BasicBackendCatalogError("basic_backend_public_freeze_invalid")
    files = manifest.get("files")
    if not isinstance(files, dict) or set(files) != {"README.md", "seed-contract.json", "tasks.json"}:
        raise BasicBackendCatalogError("basic_backend_public_freeze_invalid")
    for relative, expected in files.items():
        target = (root / relative).resolve(strict=True)
        if root.resolve() not in target.parents:
            raise BasicBackendCatalogError("basic_backend_public_freeze_invalid")
        with target.open("rb") as handle:
            actual = hashlib.file_digest(handle, "sha256").hexdigest()
        if actual != expected:
            raise BasicBackendCatalogError("basic_backend_public_freeze_mismatch")
    return manifest


def render_basic_backend_task(
    task_id: str,
    *,
    run_seed: BasicBackendRunSeed,
    run_nonce: str,
    tasks: tuple[BasicBackendTask, ...] | None = None,
) -> RenderedBasicBackendTask:
    catalog = tasks or load_basic_backend_tasks()
    try:
        task = next(item for item in catalog if item.task_id == task_id)
    except StopIteration as error:
        raise BasicBackendCatalogError("basic_backend_task_unknown") from error
    digest = derive_task_digest(run_seed, run_nonce=run_nonce, task_id=task_id)
    prompt, values = task.render(digest)
    return RenderedBasicBackendTask(
        definition=task,
        prompt=prompt,
        values=values,
        task_seed_commitment=task_seed_commitment(digest),
    )


def _parse_task(value: object) -> BasicBackendTask:
    if not isinstance(value, dict):
        raise BasicBackendCatalogError("basic_backend_public_task_invalid")
    required = {
        "task_id",
        "category",
        "fixture_family",
        "prompt_template",
        "randomized_fields",
        "public_test_command",
        "readable_paths",
        "writable_paths",
        "forbidden_mutations",
        "expected_terminal_disposition",
        "trace_requirements",
    }
    if set(value) != required:
        raise BasicBackendCatalogError("basic_backend_public_task_invalid")
    string_fields = ("task_id", "category", "fixture_family", "prompt_template")
    if any(not isinstance(value[field], str) or not value[field] for field in string_fields):
        raise BasicBackendCatalogError("basic_backend_public_task_invalid")
    if value["public_test_command"] != "python -m pytest -q":
        raise BasicBackendCatalogError("basic_backend_public_test_command_invalid")
    if value["expected_terminal_disposition"] != "completed_verified":
        raise BasicBackendCatalogError("basic_backend_terminal_disposition_invalid")
    definitions = value["randomized_fields"]
    if not isinstance(definitions, list) or not definitions or not all(isinstance(item, dict) for item in definitions):
        raise BasicBackendCatalogError("basic_backend_randomization_invalid")
    formatter_names = {
        field_name
        for _, field_name, _, _ in string.Formatter().parse(str(value["prompt_template"]))
        if field_name
    }
    definition_names = {str(item.get("name") or "") for item in definitions}
    allowed_computed = {"route"} if "resource_name" in definition_names else set()
    if formatter_names - definition_names - allowed_computed:
        raise BasicBackendCatalogError("basic_backend_prompt_randomization_missing")
    readable = _string_tuple(value.get("readable_paths"))
    writable = _string_tuple(value.get("writable_paths"))
    if not all(_in_scope(path, readable) for path in writable):
        raise BasicBackendCatalogError("basic_backend_writable_scope_invalid")
    traces = _string_tuple(value.get("trace_requirements"))
    if len(traces) != 8:
        raise BasicBackendCatalogError("basic_backend_trace_contract_invalid")
    return BasicBackendTask(
        task_id=str(value["task_id"]),
        category=str(value["category"]),
        fixture_family=str(value["fixture_family"]),
        prompt_template=str(value["prompt_template"]),
        randomized_fields=tuple(definitions),
        public_test_command=str(value["public_test_command"]),
        readable_paths=readable,
        writable_paths=writable,
        forbidden_mutations=_string_tuple(value.get("forbidden_mutations")),
        expected_terminal_disposition=str(value["expected_terminal_disposition"]),
        trace_requirements=traces,
    )


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise BasicBackendCatalogError("basic_backend_public_task_invalid")
    result = tuple(value)
    if len(result) != len(set(result)):
        raise BasicBackendCatalogError("basic_backend_public_task_invalid")
    return result


def _in_scope(path: str, scopes: tuple[str, ...]) -> bool:
    candidate = path.rstrip("/")
    return any(
        candidate == scope.rstrip("/")
        or candidate.startswith(scope.rstrip("/") + "/")
        for scope in scopes
    )


def _contains_private_key(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).lower() in _PRIVATE_FIELD_NAMES or _contains_private_key(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_private_key(item) for item in value)
    return False
