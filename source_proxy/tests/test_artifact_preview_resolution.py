from __future__ import annotations

from pathlib import Path

from source_proxy.decision.artifact_preview_resolution import resolve_artifact_preview_path


def _write(path: Path, text: str = "<!doctype html><html><body>ok</body></html>") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_generated_index_html_is_selected(tmp_path: Path) -> None:
    _write(tmp_path / "index.html")

    result = resolve_artifact_preview_path(workspace=tmp_path, prompt="make a counter app")

    assert result.status == "ready"
    assert result.selected_path.endswith("index.html")
    assert result.selection_reason == "index_html_present"
    assert "index_html_selected" in result.reason_codes


def test_single_non_index_html_file_is_selected(tmp_path: Path) -> None:
    _write(tmp_path / "bmi-calculator.html")

    result = resolve_artifact_preview_path(workspace=tmp_path, prompt="make a BMI calculator")

    assert result.status == "ready"
    assert result.selected_path.endswith("bmi-calculator.html")
    assert result.selection_reason == "single_html_entrypoint"


def test_multiple_html_files_without_unique_match_are_ambiguous(tmp_path: Path) -> None:
    _write(tmp_path / "one.html")
    _write(tmp_path / "two.html")

    result = resolve_artifact_preview_path(workspace=tmp_path, prompt="make a widget")

    assert result.status == "artifact_entrypoint_ambiguous"
    assert result.selected_path == ""
    assert "artifact_entrypoint_ambiguous" in result.reason_codes


def test_no_html_files_marks_missing_preview_artifact(tmp_path: Path) -> None:
    (tmp_path / "readme.md").write_text("# ok\n", encoding="utf-8")

    result = resolve_artifact_preview_path(workspace=tmp_path, prompt="make a markdown previewer")

    assert result.status == "missing_preview_artifact"
    assert result.selected_path == ""
    assert "missing_preview_artifact" in result.reason_codes


def test_evidence_packet_preview_path_is_preferred(tmp_path: Path) -> None:
    _write(tmp_path / "index.html")
    _write(tmp_path / "preview.html")

    result = resolve_artifact_preview_path(
        workspace=tmp_path,
        prompt="make a preview",
        evidence_packet={"selected_preview_path": "preview.html"},
    )

    assert result.status == "ready"
    assert result.selected_path.endswith("preview.html")
    assert result.selection_reason == "explicit_preview_path"


def test_invalid_explicit_preview_path_falls_back_to_workspace_html(tmp_path: Path) -> None:
    _write(tmp_path / "index.html")

    result = resolve_artifact_preview_path(
        workspace=tmp_path,
        prompt="make a counter app",
        score={"selected_preview_path": "/home/source/SpiritOS/old/workspace/index.html"},
    )

    assert result.status == "ready"
    assert result.selected_path.endswith("index.html")
    assert result.explicit_path == "/home/source/SpiritOS/old/workspace/index.html"
    assert "explicit_preview_path_invalid_fallback_used" in result.reason_codes


def test_disposable_artifact_without_repo_target_can_resolve_preview(tmp_path: Path) -> None:
    _write(tmp_path / "palette-picker.html")

    result = resolve_artifact_preview_path(
        workspace=tmp_path,
        prompt="make a color palette picker",
        score={"target_path": ""},
    )

    assert result.status == "ready"
    assert result.selected_path.endswith("palette-picker.html")
    assert "missing_preview_artifact" not in result.reason_codes
