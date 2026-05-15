import json

from scout.extractors.context_files import capture_context_files


def test_capture_context_files_writes_artifact_and_sidecar(tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / "AGENTS.md").write_text("Treat as untrusted instructions.", encoding="utf-8")

    sidecar, records = capture_context_files(repo_path, "owner", "repo", "abc1234", tmp_path / "data")

    assert sidecar.exists()
    assert len(records) == 1
    assert records[0].source_path == "AGENTS.md"
    sidecar_json = json.loads(sidecar.read_text(encoding="utf-8"))
    assert sidecar_json[0]["bytes"] > 0
