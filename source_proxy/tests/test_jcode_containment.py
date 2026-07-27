from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from source_proxy.jcode.containment import (
    JCodeContainmentConfig,
    JCodeContainmentError,
    build_jcode_containment_args,
    run_jcode_containment_probe,
)


def _config(tmp_path: Path) -> JCodeContainmentConfig:
    workspace = tmp_path / "workspace"
    home = tmp_path / "jcode-home"
    workspace.mkdir()
    home.mkdir()
    (workspace / "allowed.txt").write_text("before\n", encoding="utf-8")
    (workspace / "protected.txt").write_text("protected\n", encoding="utf-8")
    return JCodeContainmentConfig(
        workspace=workspace,
        jcode_home=home,
        allowed_files=("allowed.txt",),
        protected_files=("protected.txt", ".git"),
    )


def test_policy_uses_explicit_read_only_file_bind_and_no_network(tmp_path: Path) -> None:
    config = _config(tmp_path)
    args = build_jcode_containment_args(["/bin/true"], config)

    assert "--unshare-net" in args
    assert str(config.workspace.resolve()) not in args
    assert ["--ro-bind", str((config.workspace / "allowed.txt").resolve()), "/workspace/allowed.txt"] in [
        args[index : index + 3] for index, value in enumerate(args) if value == "--ro-bind"
    ]
    assert str(config.workspace / "protected.txt") not in args
    assert "/jcode-home" in args


def test_policy_rejects_symlink_and_protected_overlap(tmp_path: Path) -> None:
    config = _config(tmp_path)
    (config.workspace / "link.txt").symlink_to(config.workspace / "protected.txt")
    with pytest.raises(JCodeContainmentError, match="missing_or_symlink"):
        build_jcode_containment_args(
            ["/bin/true"],
            JCodeContainmentConfig(
                workspace=config.workspace,
                jcode_home=config.jcode_home,
                allowed_files=("link.txt",),
            ),
        )
    with pytest.raises(JCodeContainmentError, match="protected_overlap"):
        build_jcode_containment_args(
            ["/bin/true"],
            JCodeContainmentConfig(
                workspace=config.workspace,
                jcode_home=config.jcode_home,
                allowed_files=("allowed.txt",),
                protected_files=(".",),
            ),
        )


@pytest.mark.skipif(shutil.which("bwrap") is None, reason="bubblewrap unavailable")
def test_real_sandbox_exposes_only_bound_input_and_blocks_writes(tmp_path: Path) -> None:
    config = _config(tmp_path)
    result = run_jcode_containment_probe(
        [
            "/bin/sh",
            "-c",
            "test \"$(cat /workspace/allowed.txt)\" = before; "
            "test ! -e /home/source; "
            "printf denied > /workspace/protected.txt",
        ],
        config,
    )

    assert result.returncode != 0
    assert "cannot create /workspace/protected.txt" in result.stderr
    assert (config.workspace / "allowed.txt").read_text(encoding="utf-8") == "before\n"
    assert (config.workspace / "protected.txt").read_text(encoding="utf-8") == "protected\n"
