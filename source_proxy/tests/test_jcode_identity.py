from __future__ import annotations

import hashlib
from pathlib import Path

from source_proxy.jcode.identity import (
    JCodeIdentityExpectation,
    reconcile_jcode_model_identity,
    verify_jcode_binary_identity,
)


def _expectation(binary: Path) -> JCodeIdentityExpectation:
    return JCodeIdentityExpectation(
        source_commit="2444e7b6bc80d421ae3ee404081bdb41150a1830",
        binary_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        provider_profile="spiritos_qualification",
        model="qwen2.5-coder:7b",
    )


def test_binary_identity_requires_exact_hash_source_and_version_commit(tmp_path: Path) -> None:
    binary = tmp_path / "jcode"
    binary.write_bytes(b"pinned-artifact")
    expectation = _expectation(binary)

    verified = verify_jcode_binary_identity(
        binary,
        expectation,
        observed_source_commit=expectation.source_commit,
        observed_version="jcode v0.58.51-dev (2444e7b6)",
    )
    mismatched = verify_jcode_binary_identity(
        binary,
        expectation,
        observed_source_commit="0" * 40,
        observed_version="jcode v0.58.0",
    )

    assert verified["ok"] is True
    assert set(mismatched["blocked_reasons"]) == {
        "jcode_source_commit_mismatch",
        "jcode_version_commit_mismatch",
    }


def test_model_identity_requires_observed_exact_profile_and_model(tmp_path: Path) -> None:
    binary = tmp_path / "jcode"
    binary.write_bytes(b"pinned-artifact")
    expectation = _expectation(binary)

    verified = reconcile_jcode_model_identity(
        expectation,
        {"identity_observed": True, "provider_profile": expectation.provider_profile, "actual_model": expectation.model},
    )
    blocked = reconcile_jcode_model_identity(expectation, {"provider_profile": expectation.provider_profile})

    assert verified["ok"] is True
    assert "jcode_actual_model_unobserved" in blocked["blocked_reasons"]
    assert "jcode_actual_model_mismatch" in blocked["blocked_reasons"]
