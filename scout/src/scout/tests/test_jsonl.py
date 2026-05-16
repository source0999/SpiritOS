import json
from concurrent.futures import ThreadPoolExecutor

from scout.storage.jsonl import append_raw_event


def test_concurrent_appends_produce_valid_json_lines(tmp_path):
    def append_one(index: int) -> None:
        append_raw_event(
            tmp_path,
            "test://source",
            "test.event",
            {"index": index},
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(append_one, [1, 2]))

    [log_file] = (tmp_path / "logs").glob("raw_events.*.jsonl")
    lines = log_file.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 2
    records = [json.loads(line) for line in lines]
    assert {record["payload"]["index"] for record in records} == {1, 2}
    assert all(record["source_uri"] == "test://source" for record in records)

