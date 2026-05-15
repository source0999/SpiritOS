from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from scout.config import get_settings
from scout.packets.promotions import (
    approve_promotion,
    list_queued_promotions,
    load_packet_and_verdict,
    reject_promotion,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Review queued Scout promotions.")
    parser.add_argument("--approved-by", default=os.environ.get("USER", "human"))
    args = parser.parse_args()

    settings = get_settings()
    queued = list_queued_promotions(settings)
    if not queued:
        print("No queued promotions.")
        return 0

    for row in queued:
        packet, verdict = load_packet_and_verdict(settings, row["packet_id"])
        print("\n" + "=" * 72)
        print(f"Promotion: {row['promotion_id']}")
        print(f"Packet: {packet.packet_id}")
        print(f"Source: {packet.source_uri}")
        print(f"Decision: {verdict.decision}")
        print(f"Summary: {packet.summary}")
        print(f"Impact: {packet.impact_analysis}")
        print(f"Reason codes: {', '.join(verdict.reason_codes) or '(none)'}")
        choice = input("[a]pprove, [r]eject, [s]kip: ").strip().lower()
        if choice == "a":
            approve_promotion(settings, row["promotion_id"], approved_by=args.approved_by)
            print("Approved.")
        elif choice == "r":
            reason = input("Rejection reason: ").strip()
            if not reason:
                print("Rejection requires a reason; skipped.")
                continue
            reject_promotion(settings, row["promotion_id"], reason=reason)
            print("Rejected.")
        else:
            print("Skipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
