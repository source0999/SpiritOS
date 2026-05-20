from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


DEFAULT_BASE_URL = "http://localhost:8077"


def _blocked_payload(detail: str, requested_by: str, status_code: int | None = None) -> dict:
    return {
        "result": "blocked",
        "detail": detail,
        "status_code": status_code,
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
    parser.add_argument("--requested-by", default="human")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--allow-blocked",
        action="store_true",
        help="Exit 0 when safety preconditions block the dry run.",
    )
    args = parser.parse_args()

    body = json.dumps(
        {
            "promotion_id": args.promotion_id,
            "requested_by": args.requested_by,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{args.base_url.rstrip('/')}/v1/scout/promotions/import-dry-run",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            error_payload = json.loads(exc.read().decode("utf-8"))
            detail = str(error_payload.get("detail") or error_payload)
        except Exception:
            detail = str(exc)
        _print_payload(
            _blocked_payload(detail, args.requested_by, exc.code),
            as_json=args.json,
        )
        return 0 if args.allow_blocked else 2
    except Exception as exc:
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
