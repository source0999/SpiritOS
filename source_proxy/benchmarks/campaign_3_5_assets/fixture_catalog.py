"""Private fixture-builder catalog.

The catalog intentionally exposes only generated fixture files and a public
manifest.  Its inputs and outputs contain seed commitments, never the raw run
seed or a private oracle/reference transformation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from source_proxy.benchmarks.campaign_3_5_assets.python_fixtures import PYTHON_FIXTURE_BUILDERS, build_python_fixture
from source_proxy.benchmarks.campaign_3_5_assets.typescript_fixtures import TYPESCRIPT_FIXTURE_BUILDERS, build_typescript_fixture
from source_proxy.benchmarks.campaign_3_5_assets.systems_fixtures import SYSTEM_FIXTURE_BUILDERS, build_system_fixture
from source_proxy.benchmarks.campaign_3_5_assets.control_fixtures import CONTROL_FIXTURE_BUILDERS, build_control_fixture
from source_proxy.benchmarks.campaign_3_5_fixture_builder import FixtureMaterialization, materialize_git_fixture


IMPLEMENTED_FIXTURE_IDS = frozenset(PYTHON_FIXTURE_BUILDERS) | frozenset(TYPESCRIPT_FIXTURE_BUILDERS) | frozenset(SYSTEM_FIXTURE_BUILDERS) | frozenset(CONTROL_FIXTURE_BUILDERS)


def materialize_implemented_fixture(
    fixture_parent: Path,
    task: dict[str, Any],
    *,
    task_seed: str,
    task_seed_commitment: str,
) -> FixtureMaterialization:
    """Build one currently implemented fixture family in a disposable root."""
    fixture_id = task["fixture"]
    if fixture_id not in IMPLEMENTED_FIXTURE_IDS:
        raise ValueError("campaign_3_5_fixture_builder_not_implemented")
    if fixture_id in PYTHON_FIXTURE_BUILDERS:
        files = build_python_fixture(fixture_id, task_seed)
    elif fixture_id in TYPESCRIPT_FIXTURE_BUILDERS:
        files = build_typescript_fixture(fixture_id, task_seed)
    elif fixture_id in SYSTEM_FIXTURE_BUILDERS:
        files = build_system_fixture(fixture_id, task_seed)
    else:
        files = build_control_fixture(fixture_id, task_seed)
    fixture_name = f"fixture-{task_seed_commitment[:16]}"
    return materialize_git_fixture(
        fixture_parent,
        fixture_name,
        fixture_id=fixture_id,
        files=files,
        seed_commitment=task_seed_commitment,
        allowed_paths=["src/", "tests/", "migrations/", "config/", "docs/", "pyproject.toml"],
    )
