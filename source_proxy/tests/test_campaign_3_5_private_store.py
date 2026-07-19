from pathlib import Path
import stat

from source_proxy.benchmarks.campaign_3_5_private_store import create_private_store, write_private_task


def test_private_store_is_owner_only_and_refuses_reuse(tmp_path: Path) -> None:
    store = create_private_store(tmp_path / "private")
    task = write_private_task(store, "T01", {"seed": "private", "oracle": {"hidden": True}})
    assert stat.S_IMODE(store.stat().st_mode) == 0o700
    assert stat.S_IMODE(task.stat().st_mode) == 0o600
