from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json


def append_raw_event(
    data_dir: Path,
    source_uri: str,
    event_kind: str,
    payload: dict[str, Any],
) -> tuple[str, str]:
    """Append a single-line JSON record to today's rotated JSONL."""
    now = datetime.now(timezone.utc)
    day = now.strftime("%Y-%m-%d")
    log_dir = data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    rel_path = f"logs/raw_events.{day}.jsonl"
    full_path = data_dir / rel_path
    record = {
        "captured_at": now.isoformat(),
        "source_uri": source_uri,
        "event_kind": event_kind,
        "payload": payload,
    }
    serialized = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    sha = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    with full_path.open("a", encoding="utf-8") as fh:
        fh.write(serialized)
    return rel_path, sha
