"""Deterministic fixture materialization for the independent harness."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def materialize_fixture(root: Path, *, files: dict[str, str], seed: str) -> str:
    if not seed or not files:
        raise ValueError("campaign_3_5_fixture_input_invalid")
    root.mkdir(parents=True, exist_ok=False)
    for relative, content in sorted(files.items()):
        path = root / relative
        if path.resolve().parent != root.resolve() and root.resolve() not in path.resolve().parents:
            raise ValueError("campaign_3_5_fixture_path_invalid")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return hashlib.sha256(json.dumps({"seed": seed, "files": files}, sort_keys=True).encode()).hexdigest()
