from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scout.config import get_settings
from scout.packets.promotions import PromotionError, dry_run_proxy_import


def _blocked_payload(detail: str, requested_by: str) -> dict:
    return {
        "result": "blocked",
        "detail": detail,
        "requested_by": requested_by,
        "dry_run": True,
        "read_only": True,
        "mutated": False,
        "mutation_allowed": False,
        "would_call_proxy_intake": False,
        "would_write_proxy_memory": False,
        "would_write_coding_context": False,
        "would_finalize_promotion": False,
    }


def _print_payload(payload: dict, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    for key, value in payload.items():
        print(f"{key}: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Dry-run one approved Scout promotion import without proxy writes.",
    )
    parser.add_argument("--promotion-id", required=True)
    parser.add_argument("--requested-by", default=os.environ.get("USER", "human"))
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--allow-blocked",
        action="store_true",
        help="Exit 0 when safety preconditions block the dry run.",
    )
    args = parser.parse_args()

    try:
        payload = dry_run_proxy_import(get_settings(), args.promotion_id)
    except PromotionError as exc:
        _print_payload(
            _blocked_payload(str(exc), args.requested_by),
            as_json=args.json,
        )
        return 0 if args.allow_blocked else 2

    payload["result"] = "pass"
    payload["requested_by"] = args.requested_by
    payload["mutated"] = False
    _print_payload(payload, as_json=args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
