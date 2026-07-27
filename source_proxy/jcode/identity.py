"""Fail-closed binary and provider/model identity reconciliation."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class JCodeIdentityExpectation:
    source_commit: str
    binary_sha256: str
    provider_profile: str
    model: str


def verify_jcode_binary_identity(
    binary: Path,
    expectation: JCodeIdentityExpectation,
    *,
    observed_source_commit: str,
    observed_version: str,
) -> dict[str, object]:
    """Verify an exact executable hash, source commit, and embedded revision."""
    actual_hash = hashlib.sha256(binary.read_bytes()).hexdigest() if binary.is_file() else None
    version_commit_match = expectation.source_commit[:8] in observed_version
    reasons: list[str] = []
    if actual_hash != expectation.binary_sha256:
        reasons.append("jcode_binary_sha256_mismatch")
    if observed_source_commit != expectation.source_commit:
        reasons.append("jcode_source_commit_mismatch")
    if not version_commit_match:
        reasons.append("jcode_version_commit_mismatch")
    return {
        "ok": not reasons,
        "binary_sha256": actual_hash,
        "source_commit": observed_source_commit,
        "version": observed_version,
        "blocked_reasons": reasons,
    }


def reconcile_jcode_model_identity(
    expectation: JCodeIdentityExpectation,
    observed: Mapping[str, object],
) -> dict[str, object]:
    """Accept a provider receipt only when profile and actual model are exact."""
    profile = str(observed.get("provider_profile") or "")
    model = str(observed.get("actual_model") or "")
    reasons: list[str] = []
    if profile != expectation.provider_profile:
        reasons.append("jcode_provider_profile_mismatch")
    if model != expectation.model:
        reasons.append("jcode_actual_model_mismatch")
    if not bool(observed.get("identity_observed")):
        reasons.append("jcode_actual_model_unobserved")
    return {
        "ok": not reasons,
        "requested_provider_profile": expectation.provider_profile,
        "requested_model": expectation.model,
        "observed_provider_profile": profile or None,
        "observed_actual_model": model or None,
        "blocked_reasons": reasons,
    }
