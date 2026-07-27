from __future__ import annotations

import json
from pathlib import Path

import pytest

from source_proxy.jcode.preparation import (
    CHALLENGER_MODEL,
    PRIMARY_MODEL,
    PreparationPacketError,
    build_run_packet,
    write_sealed_packet,
)


def _manifest(path: Path) -> Path:
    value = {
        "schema_version": "source-proxy.jcode-diagnostic-manifest/v1",
        "manifest_id": "fixture-manifest",
        "frozen_benchmark_dependency": False,
        "tasks": [
            {
                "id": f"JQ-{index:02d}",
                "category": "repair",
                "prompt": f"Task {index}",
                "allowed_paths": ["qualification_fixture/value.py"],
                "protected_paths": [".git"],
                "expected_terminal": "COMPLETED_VERIFIED",
            }
            for index in range(1, 21)
        ],
    }
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _registry(path: Path) -> Path:
    value = {
        "models": [
            {"name": PRIMARY_MODEL, "digest": "dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364", "details": {"family": "qwen2", "parameter_size": "7.6B", "quantization_level": "Q4_K_M"}},
            {"name": CHALLENGER_MODEL, "digest": "9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849", "details": {"family": "qwen2", "parameter_size": "14.8B", "quantization_level": "Q4_K_M"}},
        ]
    }
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _fixture(root: Path) -> None:
    for name in ("qualification_fixture", "fixture_proxy"):
        directory = root / name
        directory.mkdir()
        (directory / "value.py").write_text("VALUE = 1\n", encoding="utf-8")


def test_builds_sealed_matrix_without_executor_activity(tmp_path: Path) -> None:
    _fixture(tmp_path)
    packet = build_run_packet(
        manifest_path=_manifest(tmp_path / "manifest.json"),
        repository_root=tmp_path,
        fixture_commit="a" * 40,
        registry_snapshot_path=_registry(tmp_path / "registry.json"),
        created_at_utc="2026-07-27T00:00:00Z",
    )

    assert packet["status"] == "SEALED_PRE_EXECUTION_NO_TASKS_RUN"
    assert packet["fixture"]["file_count"] == 2
    assert len(packet["task_packets"]) == 20
    assert len(packet["run_order"]) == 80
    assert packet["run_order"][0]["lane"] == "A"
    assert packet["run_order"][1]["lane"] == "B"
    assert packet["run_order"][40]["lane"] == "C"
    assert packet["execution_prohibited_by_preparation_stage"] is True

    receipt = write_sealed_packet(packet, tmp_path / "packet.json")
    assert len(receipt["packet_sha256"]) == 64
    assert (tmp_path / "packet.json.sha256").is_file()


def test_rejects_registry_identity_drift(tmp_path: Path) -> None:
    _fixture(tmp_path)
    registry = _registry(tmp_path / "registry.json")
    value = json.loads(registry.read_text(encoding="utf-8"))
    value["models"][0]["digest"] = "0" * 64
    registry.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(PreparationPacketError, match="registry_digest_mismatch"):
        build_run_packet(
            manifest_path=_manifest(tmp_path / "manifest.json"),
            repository_root=tmp_path,
            fixture_commit="a" * 40,
            registry_snapshot_path=registry,
            created_at_utc="2026-07-27T00:00:00Z",
        )
