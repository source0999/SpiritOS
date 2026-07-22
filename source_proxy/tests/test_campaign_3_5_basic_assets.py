from __future__ import annotations

import json
import os
from pathlib import Path

from source_proxy.benchmarks.campaign_3_5_basic_assets.catalog import (
    EXPECTED_TASK_IDS,
    PUBLIC_ROOT,
    load_basic_backend_tasks,
    render_basic_backend_task,
)
from source_proxy.benchmarks.campaign_3_5_basic_assets.fixtures import materialize_basic_backend_fixture
from source_proxy.benchmarks.campaign_3_5_basic_assets.freeze import validate_freeze
from source_proxy.benchmarks.campaign_3_5_basic_assets.reference_validation import validate_references
from source_proxy.benchmarks.campaign_3_5_basic_assets.seeding import (
    BasicBackendRunSeed,
    derive_task_digest,
)
from source_proxy.benchmarks.campaign_3_5_fixture_authority import (
    ENV_MANIFEST,
    MANIFEST_SCHEMA_V2,
    load_campaign_3_5_fixture_authority,
)


def test_public_catalog_is_exactly_the_ten_ordinary_backend_prompts() -> None:
    tasks = load_basic_backend_tasks()

    assert tuple(task.task_id for task in tasks) == EXPECTED_TASK_IDS
    assert len({task.category for task in tasks}) == 10
    assert all(task.expected_terminal_disposition == "completed_verified" for task in tasks)
    assert all(task.public_test_command == "python -m pytest -q" for task in tasks)
    assert all("task_id" not in task.prompt_template.lower() for task in tasks)
    assert all(len(task.trace_requirements) == 8 for task in tasks)


def test_hmac_seed_scopes_change_across_tasks_runs_and_fields() -> None:
    seed = BasicBackendRunSeed.from_private_bytes(b"a" * 32)
    other_seed = BasicBackendRunSeed.from_private_bytes(b"b" * 32)

    first = derive_task_digest(seed, run_nonce="run-one", task_id="BT01")

    assert first == derive_task_digest(seed, run_nonce="run-one", task_id="BT01")
    assert first != derive_task_digest(seed, run_nonce="run-one", task_id="BT02")
    assert first != derive_task_digest(seed, run_nonce="run-two", task_id="BT01")
    assert first != derive_task_digest(other_seed, run_nonce="run-one", task_id="BT01")


def test_materialized_fixture_exposes_only_v2_authority_and_public_inputs(
    tmp_path: Path, monkeypatch
) -> None:
    seed = BasicBackendRunSeed.from_private_bytes(b"c" * 32)
    rendered = render_basic_backend_task("BT01", run_seed=seed, run_nonce="fixture-run")
    fixture_parent = tmp_path / "fixtures"
    fixture_parent.mkdir()
    fixture = materialize_basic_backend_fixture(fixture_parent, rendered)
    authority_path = tmp_path / "authority.json"
    authority_path.write_text(json.dumps(fixture.authority_manifest, sort_keys=True), encoding="utf-8")
    os.chmod(authority_path, 0o600)
    monkeypatch.setenv(ENV_MANIFEST, str(authority_path.resolve()))

    authority = load_campaign_3_5_fixture_authority()
    all_public_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in fixture.root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    )

    assert fixture.authority_manifest["schema_version"] == MANIFEST_SCHEMA_V2
    assert authority.baseline_commit == fixture.baseline_commit
    assert authority.baseline_tree == fixture.baseline_tree
    assert authority.current_state_paths == ()
    assert seed.raw.hex() not in all_public_text
    assert "campaign_3_5_basic_assets" not in all_public_text
    assert "private_oracle" not in all_public_text


def test_fresh_seed_changes_rendered_names_without_changing_task_contract() -> None:
    first = render_basic_backend_task(
        "BT04",
        run_seed=BasicBackendRunSeed.from_private_bytes(b"d" * 32),
        run_nonce="clean-run-one",
    )
    second = render_basic_backend_task(
        "BT04",
        run_seed=BasicBackendRunSeed.from_private_bytes(b"e" * 32),
        run_nonce="clean-run-two",
    )

    assert first.definition.task_id == second.definition.task_id == "BT04"
    assert first.prompt != second.prompt
    assert first.values != second.values
    assert first.task_seed_commitment != second.task_seed_commitment


def test_all_private_references_pass_public_tests_authority_and_oracles() -> None:
    report = validate_references()

    assert report["task_count"] == 10
    assert report["passed"] is True
    assert [record["task_id"] for record in report["tasks"]] == list(EXPECTED_TASK_IDS)
    assert all(record["public_tests_passed"] for record in report["tasks"])
    assert all(record["private_oracle_passed"] for record in report["tasks"])
    assert all(record["authority_passed"] for record in report["tasks"])
    assert all(record["writable_scope_passed"] for record in report["tasks"])


def test_public_and_private_asset_freeze_is_current_and_import_isolated() -> None:
    manifest = validate_freeze()
    public_manifest = json.loads((PUBLIC_ROOT / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["task_ids"] == list(EXPECTED_TASK_IDS)
    assert manifest["task_count"] == 10
    assert manifest["production_import_boundary_passed"] is True
    assert public_manifest["required_task_ids"] == list(EXPECTED_TASK_IDS)
