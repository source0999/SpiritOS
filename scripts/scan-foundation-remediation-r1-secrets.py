#!/usr/bin/env python3
"""Fail on high-confidence secret material in tracked repository files."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path


PATTERNS = {
    "private_key": re.compile(b"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(b"AKIA[0-9A-Z]{16}"),
    "github_token": re.compile(b"(?<![A-Za-z0-9])gh[pousr]_[A-Za-z0-9]{36,255}"),
    "openai_token": re.compile(b"(?<![A-Za-z0-9])sk-(?:proj-)?[A-Za-z0-9_-]{40,}"),
    "slack_token": re.compile(b"(?<![A-Za-z0-9])xox[baprs]-[A-Za-z0-9-]{20,}"),
}
CHUNK_SIZE = 1024 * 1024
PATTERN_OVERLAP = 512


def tracked_files(root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("tracked_file_inventory_unreadable")
    return [item.decode("utf-8", "surrogateescape") for item in completed.stdout.split(b"\0") if item]


def scan_tracked_files(root: Path) -> list[str]:
    findings: list[str] = []
    for relative in tracked_files(root):
        path = root / relative
        if path.is_symlink() or not path.is_file():
            continue
        try:
            matched: set[str] = set()
            overlap = b""
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
                    data = overlap + chunk
                    for name, pattern in PATTERNS.items():
                        if name not in matched and pattern.search(data):
                            matched.add(name)
                    overlap = data[-PATTERN_OVERLAP:]
        except OSError as error:
            findings.append(f"tracked_file_unreadable:{relative}:{error}")
            continue
        findings.extend(f"high_confidence_secret:{name}:{relative}" for name in sorted(matched))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(os.environ.get("SPIRITOS_FOUNDATION_R1_ROOT", Path(__file__).resolve().parents[1])),
    )
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        findings = scan_tracked_files(root)
    except RuntimeError as error:
        findings = [str(error)]
    if findings:
        print("FOUNDATION_REMEDIATION_R1_SECRET_SCAN_INVALID")
        print("\n".join(sorted(findings)))
        return 1
    print("FOUNDATION_REMEDIATION_R1_SECRET_SCAN_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
