"""Private benchmark-store boundary; production code never reads this store."""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any


class Campaign35PrivateStoreError(ValueError):
    pass


def create_private_store(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=False)
    os.chmod(root, 0o700)
    if stat.S_IMODE(root.stat().st_mode) != 0o700:
        raise Campaign35PrivateStoreError("campaign_3_5_private_store_permissions_invalid")
    return root


def write_private_task(store: Path, task_id: str, payload: dict[str, Any]) -> Path:
    if not store.is_dir() or stat.S_IMODE(store.stat().st_mode) != 0o700:
        raise Campaign35PrivateStoreError("campaign_3_5_private_store_permissions_invalid")
    if not task_id or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for ch in task_id):
        raise Campaign35PrivateStoreError("campaign_3_5_private_task_id_invalid")
    path = store / f"{task_id}.json"
    if path.exists():
        raise Campaign35PrivateStoreError("campaign_3_5_private_task_exists")
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    os.chmod(path, 0o600)
    return path
