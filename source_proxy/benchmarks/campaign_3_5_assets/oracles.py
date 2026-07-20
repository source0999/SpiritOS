"""Private, fail-closed oracle-profile framework for Campaign 3.5.

Profiles are built from immutable task contracts, stored outside materialized
fixtures, and return generalized failure categories.  A completed-code profile
is not considered semantically validated until its fixture family supplies an
independent probe; this deliberate fail-closed state prevents a skeletal
fixture from becoming executable merely because it has a profile file.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from source_proxy.benchmarks.campaign_3_5_private_store import write_private_task


class Campaign35OracleError(ValueError):
    pass


SemanticProbe = Callable[[Path], tuple[bool, str]]


@dataclass(frozen=True)
class PrivateOracleProfile:
    task_id: str
    expected_disposition: str
    expected_artifacts: tuple[str, ...]
    expected_tests: tuple[str, ...]
    expected_diagnostics: tuple[str, ...]
    oracle_checks: tuple[str, ...]
    forbidden_behavior: tuple[str, ...]
    hard_failures: tuple[str, ...]
    scoring: dict[str, Any]
    semantic_probe_id: str

    def private_payload(self) -> dict[str, Any]:
        return {
            "schema_version": "campaign-3.5-private-oracle-profile/v1",
            "task_id": self.task_id,
            "expected_disposition": self.expected_disposition,
            "expected_artifacts": list(self.expected_artifacts),
            "expected_tests": list(self.expected_tests),
            "expected_diagnostics": list(self.expected_diagnostics),
            "oracle_checks": list(self.oracle_checks),
            "forbidden_behavior": list(self.forbidden_behavior),
            "hard_failures": list(self.hard_failures),
            "scoring": self.scoring,
            "semantic_probe_id": self.semantic_probe_id,
        }


def build_private_oracle_profiles(tasks: list[dict[str, Any]]) -> dict[str, PrivateOracleProfile]:
    profiles: dict[str, PrivateOracleProfile] = {}
    for task in tasks:
        task_id = task["task_id"]
        if task_id in profiles:
            raise Campaign35OracleError("campaign_3_5_oracle_task_duplicate")
        profiles[task_id] = PrivateOracleProfile(
            task_id=task_id,
            expected_disposition=task["expected_disposition"],
            expected_artifacts=tuple(task["expected_artifacts"]),
            expected_tests=tuple(task["expected_tests"]),
            expected_diagnostics=tuple(task["expected_diagnostics"]),
            oracle_checks=tuple(task["oracle_checks"]),
            forbidden_behavior=tuple(task["forbidden_behavior"]),
            hard_failures=tuple(task["hard_failures"]),
            scoring=task["scoring"],
            semantic_probe_id=f"campaign-3.5/{task_id}/semantic-v1",
        )
    return profiles


def stage_private_oracle_profiles(store: Path, tasks: list[dict[str, Any]]) -> dict[str, Path]:
    """Write all profiles to the already-created mode-0700 private store."""
    return {
        task_id: write_private_task(store, task_id, profile.private_payload())
        for task_id, profile in build_private_oracle_profiles(tasks).items()
    }


def _changed_paths(fixture_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(fixture_root), "diff", "--name-only", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _path_scope_ok(paths: list[str], allowed_paths: list[str]) -> bool:
    return all(any(path.startswith(allowed) for allowed in allowed_paths) for path in paths)


def evaluate_profile(
    profile: PrivateOracleProfile,
    *,
    fixture_root: Path,
    allowed_paths: list[str],
    final_disposition: str,
    semantic_probe: SemanticProbe | None,
) -> dict[str, Any]:
    """Evaluate a profile without emitting private expected answers.

    The result is safe for evidence because it contains only category labels and
    booleans.  Probe messages are reduced to a stable category by the caller.
    """
    paths = _changed_paths(fixture_root)
    results: dict[str, bool] = {
        "disposition": final_disposition == profile.expected_disposition,
        "scope": _path_scope_ok(paths, allowed_paths),
    }
    if profile.expected_disposition == "COMPLETED_VERIFIED":
        results["mutation"] = bool(paths)
        if semantic_probe is None:
            results["semantic"] = False
            semantic_category = "semantic_probe_unimplemented"
        else:
            results["semantic"], semantic_category = semantic_probe(fixture_root)
    elif profile.expected_disposition == "BLOCKED_OR_DEGRADED_TRUTHFULLY":
        results["nonmutation"] = not paths
        semantic_category = "blocked_state_checked"
    else:
        # Escalation work may construct only a context pack under its allowed
        # evidence path; the task's terminal code must remain non-mutating.
        results["context_pack"] = bool(paths)
        semantic_category = "context_pack_presence_checked"
    passed = all(results.values())
    return {
        "schema_version": "campaign-3.5-oracle-result/v1",
        "task_id": profile.task_id,
        "passed": passed,
        "checks": results,
        "changed_path_count": len(paths),
        "semantic_category": semantic_category,
        "result_commitment": hashlib.sha256(json.dumps(results, sort_keys=True).encode("utf-8")).hexdigest(),
    }
