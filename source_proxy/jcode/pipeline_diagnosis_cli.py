"""Command line entry point for the isolated Campaign 2-J diagnostics."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from source_proxy.jcode.pipeline_diagnosis import (
    MODEL_SPECS,
    canonical_json,
    run_diagnostic,
    seal_interrupted_run_from_ledger,
    seal_jcode_capture_preflight,
    seal_matrix_manifest,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run isolated Campaign 2-J packet diagnostics.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("seal-manifest", help="Seal the immutable task and matrix manifest.")
    subparsers.add_parser("preflight", help="Capture JCode packets without a real model request.")

    run = subparsers.add_parser("run", help="Execute one fresh, bounded diagnostic cell.")
    run.add_argument("--run-id", required=True)
    run.add_argument("--task", required=True, choices=("R", "W"))
    run.add_argument("--lane", required=True, choices=tuple("ABCDEF"))
    run.add_argument("--model", required=True, choices=tuple(MODEL_SPECS))
    run.add_argument(
        "--bridge-mode",
        choices=("legacy_text_only", "tool_preserving"),
        default="legacy_text_only",
    )

    interrupted = subparsers.add_parser(
        "seal-interrupted",
        help="Seal an explicit incomplete receipt for a pre-repair interrupted run.",
    )
    interrupted.add_argument("--run-id", required=True)
    interrupted.add_argument("--task", required=True, choices=("R", "W"))
    interrupted.add_argument("--lane", required=True, choices=tuple("ABCDEF"))
    interrupted.add_argument("--model", required=True, choices=tuple(MODEL_SPECS))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "seal-manifest":
        result = seal_matrix_manifest()
    elif args.command == "preflight":
        result = seal_jcode_capture_preflight()
    elif args.command == "seal-interrupted":
        result = seal_interrupted_run_from_ledger(
            run_id=args.run_id,
            task_key=args.task,
            lane=args.lane,
            model=args.model,
        )
    else:
        result = run_diagnostic(
            run_id=args.run_id,
            task_key=args.task,
            lane=args.lane,
            model=args.model,
            bridge_mode=args.bridge_mode,
        )
    print(canonical_json(result), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
