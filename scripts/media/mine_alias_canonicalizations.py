#!/usr/bin/env python3
"""Report likely performer alias canonicalizations from SpiritFlix model_index.json.

The script is intentionally read-only. It prints SEED_PERFORMER_ALIASES-style
lines for a human review pass before any alias is added to face_organizer.py.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_MODEL_INDEX = Path(__file__).with_name("model_index.json")
DEFAULT_FACE_ORGANIZER = Path(__file__).with_name("face_organizer.py")
ANCHOR_STATUSES = {"profile-url", "user-confirmed"}
LOCAL_AUTO_STATUSES = {"local-auto"}


def normalize_identity_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def levenshtein(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)
    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, 1):
        current = [left_index]
        for right_index, right_char in enumerate(right, 1):
            cost = 0 if left_char == right_char else 1
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + cost,
                )
            )
        previous = current
    return previous[-1]


def load_models(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    models = payload.get("models") if isinstance(payload, dict) else payload
    if isinstance(models, dict):
        models = list(models.values())
    if not isinstance(models, list):
        raise SystemExit(f"No models array found in {path}")
    return [item for item in models if isinstance(item, dict)]


def existing_seed_aliases(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    start = text.find("SEED_PERFORMER_ALIASES")
    if start < 0:
        return {}
    end = text.find("\n}\n", start)
    block = text[start:end] if end > start else text[start:]
    aliases: dict[str, str] = {}
    for match in re.finditer(r'^\s*"([^"]+)":\s*"([^"]+)",', block, flags=re.MULTILINE):
        aliases[normalize_identity_key(match.group(1))] = match.group(2)
    return aliases


def status_for(row: dict[str, Any]) -> str:
    return str(row.get("status") or row.get("assignment_status") or "").strip().lower()


def row_key(row: dict[str, Any]) -> str:
    return normalize_identity_key(str(row.get("slug") or row.get("name") or ""))


def row_name(row: dict[str, Any]) -> str:
    return str(row.get("name") or row.get("slug") or "").strip()


def is_anchor(row: dict[str, Any]) -> bool:
    return status_for(row) in ANCHOR_STATUSES or bool(row.get("profile_handles"))


def is_local_auto(row: dict[str, Any]) -> bool:
    return status_for(row) in LOCAL_AUTO_STATUSES


def substring_match(left: str, right: str) -> bool:
    return min(len(left), len(right)) >= 5 and (left in right or right in left)


def mine_aliases(
    models: list[dict[str, Any]],
    existing_aliases: dict[str, str],
    *,
    max_distance: int,
) -> list[dict[str, Any]]:
    anchors = [row for row in models if is_anchor(row) and row_key(row)]
    suggestions: dict[str, dict[str, Any]] = {}
    for local in models:
        local_key = row_key(local)
        if not local_key or not is_local_auto(local) or local_key in existing_aliases:
            continue
        for anchor in anchors:
            anchor_key = row_key(anchor)
            if not anchor_key or anchor_key == local_key:
                continue
            distance = levenshtein(local_key, anchor_key)
            matched_by = "levenshtein" if distance <= max_distance else ""
            if not matched_by and substring_match(local_key, anchor_key):
                matched_by = "substring"
            if not matched_by:
                continue
            current = suggestions.get(local_key)
            if current and int(current["distance"]) <= distance:
                continue
            suggestions[local_key] = {
                "alias_key": local_key,
                "alias_name": row_name(local),
                "canonical_name": row_name(anchor),
                "canonical_slug": anchor.get("slug"),
                "distance": distance,
                "matched_by": matched_by,
                "local_video_count": int(local.get("video_count") or 0),
                "canonical_video_count": int(anchor.get("video_count") or 0),
            }
    return sorted(suggestions.values(), key=lambda item: (str(item["canonical_name"]).lower(), str(item["alias_key"])))


def main() -> int:
    parser = argparse.ArgumentParser(description="Print likely SEED_PERFORMER_ALIASES additions from model_index.json.")
    parser.add_argument("--model-index", type=Path, default=DEFAULT_MODEL_INDEX)
    parser.add_argument("--face-organizer", type=Path, default=DEFAULT_FACE_ORGANIZER)
    parser.add_argument("--max-distance", type=int, default=2)
    parser.add_argument("--json", action="store_true", help="print machine-readable suggestions")
    args = parser.parse_args()

    models = load_models(args.model_index)
    aliases = existing_seed_aliases(args.face_organizer)
    suggestions = mine_aliases(models, aliases, max_distance=max(0, int(args.max_distance)))
    if args.json:
        print(json.dumps({"suggestions": suggestions}, indent=2, ensure_ascii=False))
        return 0
    if not suggestions:
        print("No new alias canonicalizations suggested.")
        return 0
    print("Suggested SEED_PERFORMER_ALIASES additions:")
    for item in suggestions:
        print(f'    "{item["alias_key"]}": "{item["canonical_name"]}",')
    print("\nReview detail:")
    print(json.dumps(suggestions, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
