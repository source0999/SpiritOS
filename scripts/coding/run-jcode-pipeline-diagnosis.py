#!/usr/bin/env python3
"""Repository wrapper for the isolated Campaign 2-J diagnostic CLI."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source_proxy.jcode.pipeline_diagnosis_cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
