#!/usr/bin/env python3
"""Seal a non-executing Campaign 2-J Gate 2-J.8.5 run packet."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from source_proxy.jcode.preparation import build_run_packet, write_sealed_packet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--fixture-commit", required=True)
    parser.add_argument("--registry-snapshot", type=Path, required=True)
    parser.add_argument("--created-at-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    packet = build_run_packet(
        manifest_path=args.manifest,
        repository_root=args.repository_root,
        fixture_commit=args.fixture_commit,
        registry_snapshot_path=args.registry_snapshot,
        created_at_utc=args.created_at_utc,
    )
    receipt = write_sealed_packet(packet, args.output)
    print(receipt["packet_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
