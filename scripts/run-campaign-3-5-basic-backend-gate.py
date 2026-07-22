#!/usr/bin/env python3
"""Run the authenticated first/clean-rerun Basic Backend 10 gate."""
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source_proxy.benchmarks.campaign_3_5_basic_gate_runner import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["--source-root", str(ROOT), *sys.argv[1:]]))
