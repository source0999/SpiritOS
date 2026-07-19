from pathlib import Path
from source_proxy.benchmarks.campaign_3_5_fixture_builder import materialize_fixture

def test_fixture_materialization_is_deterministic(tmp_path: Path) -> None:
    files={"src/app.py":"value = 1\n"}
    assert materialize_fixture(tmp_path / "a", files=files, seed="secret") == materialize_fixture(tmp_path / "b", files=files, seed="secret")
