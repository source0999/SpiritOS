import pytest

pytest.importorskip("tree_sitter_languages")

from scout.extractors.repomap import build_repomap


def test_build_repomap_writes_symbols(tmp_path):
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    (repo_path / "app.py").write_text(
        """
class App:
    def run(self):
        return helper()

def helper():
    return "ok"
""",
        encoding="utf-8",
    )

    path, metadata = build_repomap(repo_path, "owner", "repo", "abc1234", tmp_path / "data")

    assert path is not None
    content = path.read_text(encoding="utf-8")
    assert "App" in content
    assert "helper" in content
    assert metadata["symbols"] >= 2
