from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

import source_proxy.tasks.long_running as long_running
from source_proxy.benchmarks.campaign_3_5_fixture_authority import (
    ENV_MANIFEST,
    MANIFEST_SCHEMA_V2,
    load_campaign_3_5_fixture_authority,
)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args],
        text=True,
    ).strip()


def _fixture_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, dict[str, object]]:
    root = (tmp_path / "fixture").resolve()
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "config", "user.name", "Fixture")
    (root / "src").mkdir()
    (root / "src" / "example.py").write_text("value = 1\n", encoding="utf-8")
    os.chmod(root / "src" / "example.py", 0o750)
    _git(root, "add", "--", "src/example.py")
    _git(root, "commit", "-qm", "baseline")

    manifest = {
        "schema_version": MANIFEST_SCHEMA_V2,
        "fixture_id": "generic-backup-fixture",
        "workspace_root": str(root),
        "baseline_commit": _git(root, "rev-parse", "HEAD"),
        "baseline_tree": _git(root, "rev-parse", "HEAD^{tree}"),
        "readable_paths": ["src/"],
        "writable_paths": ["src/"],
        "execution_profile": "generic-architect-coder-packet-v1",
    }
    manifest_path = (tmp_path / "fixture-authority.json").resolve()
    manifest_path.write_text(
        json.dumps(manifest, sort_keys=True),
        encoding="utf-8",
    )
    os.chmod(manifest_path, 0o600)
    monkeypatch.setenv(ENV_MANIFEST, str(manifest_path))
    authority = load_campaign_3_5_fixture_authority()
    namespace = authority.manifest_sha256[:24]
    identity: dict[str, object] = {
        "schema_version": "spiritos-target-plugin/v1",
        "plugin_id": "generic-workspace",
        "repository_id": "campaign-3.5-fixture",
        "worktree_id": namespace,
        "workspace_root": str(root),
        "branch": "test-control-branch",
        "state_namespace": namespace,
        "fixture_root": ".",
        "source_head": "control-source-head",
        "target_source_head": authority.baseline_commit,
        "target_workspace_state_sha256": authority.current_state_sha256,
        "target_workspace_state_paths": list(authority.current_state_paths),
        "selected_prompt_id": "generic-architect-coder-packet",
        "selected_context_id": "server-scoped-architect-context",
        "execution_profile": authority.execution_profile,
        "allowed_actions": list(authority.writable_paths),
        "readable_actions": list(authority.readable_paths),
        "result_identity": f"generic-workspace:{authority.manifest_sha256[:12]}",
        "approval_id": None,
        "approval_generation": None,
        "evidence_pointer": None,
        "failure_reason": None,
        "acknowledgement_status": "pending",
    }
    return root, identity


def _diff() -> str:
    return "\n".join(
        [
            "diff --git a/src/example.py b/src/example.py",
            "--- a/src/example.py",
            "+++ b/src/example.py",
            "@@ -1 +1 @@",
            "-value = 1",
            "+value = 2",
            "",
        ]
    )


def _apply_generic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, dict[str, object], dict[str, object], str]:
    root, identity = _fixture_identity(tmp_path, monkeypatch)
    data_dir = (tmp_path / "server-state" / "data").resolve()
    monkeypatch.setenv("SOURCE_PROXY_DATA_DIR", str(data_dir))
    diff = _diff()
    assert long_running._target_plugin_execution_workspace(identity) == root
    result = long_running._apply_verified_diff(
        diff,
        {"changed_files": [{"path": "src/example.py"}]},
        workspace_root=root,
        target_plugin_identity=identity,
        backup_binding="task-generic:approval-generic",
    )
    return root, identity, result, diff


def _finalized_task(
    root: Path,
    identity: dict[str, object],
    result: dict[str, object],
    diff: str,
) -> tuple[long_running.LongRunningTask, Path]:
    storage = result["backup_storage"]
    assert isinstance(storage, dict)
    audit = {
        "action": "repair generic fixture",
        "approval_id": "approval-generic",
        "approved_at": long_running._now_iso(),
        "approved_by": "test",
        "approved_diff_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest(),
        "changed_files": ["src/example.py"],
        "backup_manifest": result["manifest_path"],
        "backup_root": result["backup_root"],
        "backup_storage": storage,
        "changed_file_snapshots": result["changed_file_snapshots"],
        "approved_diff_path": result["approved_diff_path"],
        "task_id": "task-generic",
        "workspace_root": str(root),
    }
    manifest_sha256 = long_running._finalize_backup_manifest(
        workspace_root=root,
        manifest_path=str(result["manifest_path"]),
        backup_storage=storage,
        audit_record=audit,
    )
    task = long_running.LongRunningTask(
        description="generic backup test",
        id="task-generic",
        status="completed",
        open_diffs=[{"status": "verified", "verified": True}],
        ast_snapshot={
            "campaign_2_approval": {"target_plugin_identity": identity},
            "approved_execution_evidence": {
                "audit": audit,
                "backup_root": result["backup_root"],
                "backup_storage": storage,
                "backup_manifest": result["manifest_path"],
                "backup_manifest_sha256": manifest_sha256,
                "backup_manifest_applied_sha256": manifest_sha256,
                "approved_diff_path": result["approved_diff_path"],
                "approved_diff_sha256": audit["approved_diff_sha256"],
                "workspace_root": str(root),
            },
        },
    )
    manifest_path, _, _ = long_running._load_hash_bound_backup_manifest(
        task,
        reason_prefix="test",
    )
    return task, manifest_path


def test_generic_apply_uses_strict_hash_bound_server_state_storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, identity, result, diff = _apply_generic(tmp_path, monkeypatch)
    task, manifest_path = _finalized_task(root, identity, result, diff)

    storage = result["backup_storage"]
    assert isinstance(storage, dict)
    backup_root = manifest_path.parent
    assert backup_root.parent == (
        tmp_path / "server-state" / "data" / "approved-diff-backups"
    ).resolve()
    assert result["backup_root"] == f"server-state:{storage['namespace']}"
    assert str(result["manifest_path"]).endswith("/manifest.json")
    assert not (root / ".spirit-backups").exists()
    assert _git(root, "status", "--porcelain") == "M src/example.py"
    assert stat.S_IMODE(backup_root.stat().st_mode) == 0o700
    for path in backup_root.rglob("*"):
        expected_mode = 0o700 if path.is_dir() else 0o600
        assert stat.S_IMODE(path.stat().st_mode) == expected_mode
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["backup_storage"] == storage
    assert manifest["approved_diff_path"] == "approved.diff"
    assert manifest["backed_up_files"][0]["backup_path"] == "files/src/example.py"
    loaded_path, loaded, loaded_sha256 = long_running._load_hash_bound_backup_manifest(
        task,
        reason_prefix="test",
    )
    assert loaded_path == manifest_path
    assert loaded["task_id"] == task.id
    assert loaded_sha256 == task.ast_snapshot["approved_execution_evidence"][
        "backup_manifest_sha256"
    ]


def test_generic_workspace_receipt_root_ignores_unrelated_apply_allowlist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, identity, result, diff = _apply_generic(tmp_path, monkeypatch)
    task, _ = _finalized_task(root, identity, result, diff)
    unrelated = (tmp_path / "unrelated-control-root").resolve()
    unrelated.mkdir()
    monkeypatch.setattr(
        long_running,
        "_ordered_workspace_roots_for_apply",
        lambda: [unrelated],
    )

    assert long_running._approved_execution_workspace_root(
        task,
        reason_prefix="test",
    ) == root

    task.ast_snapshot["approved_execution_evidence"]["workspace_root"] = str(
        unrelated
    )
    with pytest.raises(long_running.LongRunningTaskError) as raised:
        long_running._approved_execution_workspace_root(task, reason_prefix="test")
    assert raised.value.reason_code == "test_workspace_root_authority_mismatch"


def test_server_state_storage_root_hash_and_non_symlink_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, identity, result, diff = _apply_generic(tmp_path, monkeypatch)
    task, manifest_path = _finalized_task(root, identity, result, diff)
    evidence = task.ast_snapshot["approved_execution_evidence"]
    evidence["backup_storage"] = {
        **evidence["backup_storage"],
        "storage_root_sha256": "0" * 64,
    }
    with pytest.raises(long_running.LongRunningTaskError) as raised:
        long_running._load_hash_bound_backup_manifest(task, reason_prefix="test")
    assert raised.value.reason_code == "test_backup_storage_root_mismatch"

    evidence["backup_storage"] = result["backup_storage"]
    original = manifest_path.read_bytes()
    target = (tmp_path / "manifest-copy.json").resolve()
    target.write_bytes(original)
    os.chmod(target, 0o600)
    manifest_path.unlink()
    manifest_path.symlink_to(target)
    with pytest.raises(long_running.LongRunningTaskError) as raised:
        long_running._load_hash_bound_backup_manifest(task, reason_prefix="test")
    assert raised.value.reason_code == "test_manifest_unavailable"


def test_generic_undo_reads_backups_relative_to_server_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, identity, result, diff = _apply_generic(tmp_path, monkeypatch)
    task, manifest_path = _finalized_task(root, identity, result, diff)
    long_running._finalize_post_apply_backup_manifest(task, {"status": "verified"})
    monkeypatch.setattr(long_running, "_lookup_task", lambda _task_id: task)
    monkeypatch.setattr(long_running, "_save_task", lambda _task: None)
    monkeypatch.setattr(long_running, "central_gate_check", lambda *args, **kwargs: None)

    payload = long_running.undo_last_approved_change(
        task.id,
        confirm_undo=True,
        expected_backup_manifest=str(result["manifest_path"]),
        requested_by="test",
    )

    assert (root / "src" / "example.py").read_text(encoding="utf-8") == "value = 1\n"
    assert stat.S_IMODE((root / "src" / "example.py").stat().st_mode) == 0o750
    receipt = payload["undo"]
    assert receipt["receipt_path"].startswith("server-state:")
    receipt_path = manifest_path.parent / "undo-receipt.json"
    assert receipt_path.is_file()
    assert stat.S_IMODE(receipt_path.stat().st_mode) == 0o600
    assert json.loads(manifest_path.read_text(encoding="utf-8"))["stage"] == "undone"


def test_workspace_relative_backup_receipts_remain_v1_compatible(
    tmp_path: Path,
) -> None:
    root = (tmp_path / "legacy").resolve()
    root.mkdir()
    _git(root, "init", "-q")
    (root / "legacy.txt").write_text("before\n", encoding="utf-8")
    diff = "\n".join(
        [
            "diff --git a/legacy.txt b/legacy.txt",
            "--- a/legacy.txt",
            "+++ b/legacy.txt",
            "@@ -1 +1 @@",
            "-before",
            "+after",
            "",
        ]
    )

    result = long_running._apply_verified_diff(
        diff,
        {"changed_files": [{"path": "legacy.txt"}]},
        workspace_root=root,
    )

    assert result["backup_storage"] is None
    assert str(result["backup_root"]).startswith(".spirit-backups/")
    assert (root / str(result["manifest_path"])).is_file()
    assert (root / str(result["approved_diff_path"])).is_file()


def test_generic_backup_storage_refuses_target_workspace_containment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, identity = _fixture_identity(tmp_path, monkeypatch)
    monkeypatch.setenv("SOURCE_PROXY_DATA_DIR", str(root / "server-state"))

    with pytest.raises(long_running.LongRunningTaskError) as raised:
        long_running._apply_verified_diff(
            _diff(),
            {"changed_files": [{"path": "src/example.py"}]},
            workspace_root=root,
            target_plugin_identity=identity,
            backup_binding="task-generic:approval-generic",
        )

    assert raised.value.reason_code == "backup_storage_scope_invalid"
    assert not (root / "server-state").exists()
    assert (root / "src" / "example.py").read_text(encoding="utf-8") == "value = 1\n"
