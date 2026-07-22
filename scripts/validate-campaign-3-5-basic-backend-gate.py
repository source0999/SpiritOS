#!/usr/bin/env python3
"""Validate the frozen Basic Backend 10 contract and scoring preconditions."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source_proxy.benchmarks.campaign_3_5_basic_gate_runner import (  # noqa: E402
    BasicBackendGateConfig,
    BasicBackendGateError,
    _default_python,
    validate_basic_backend_gate_configuration,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--python", type=Path)
    parser.add_argument("--expected-head")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Development-only structural validation; a scored run still requires clean Git state.",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    source_root = args.source_root.expanduser().resolve()
    config = BasicBackendGateConfig(
        source_root=source_root,
        output_root=source_root.parent / ".basic-backend-10-validation-unused",
        python_executable=args.python or _default_python(source_root),
        expected_head=args.expected_head,
    )
    try:
        report = validate_basic_backend_gate_configuration(
            config,
            require_clean=not args.allow_dirty,
        )
    except BasicBackendGateError as error:
        print(
            json.dumps(
                {
                    "passed": False,
                    "reason_code": error.reason_code,
                    "details": error.details,
                },
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
