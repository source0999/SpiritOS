#!/usr/bin/env python3
"""Read-only SpiritFlix caption/subtitle inventory.

Writes JSONL only under /mnt/spirit-8tb/media/.spiritflix-admin/captions/inventory.
Does not create, edit, move, or delete media files.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


MEDIA_ROOT = Path("/mnt/spirit-8tb/media")
DEFAULT_ROOTS = [MEDIA_ROOT / "anime", MEDIA_ROOT / "yes"]
REPORT_DIR = MEDIA_ROOT / ".spiritflix-admin" / "captions" / "inventory"
VIDEO_EXTENSIONS = {".mkv", ".mp4", ".m4v", ".mov", ".avi", ".webm"}
CAPTION_EXTENSIONS = {".srt", ".ass", ".ssa", ".vtt"}
FORMAT_BY_CODEC = {
    "ass": "ass",
    "ssa": "ssa",
    "subrip": "srt",
    "srt": "srt",
    "webvtt": "vtt",
    "mov_text": "mov_text",
    "hdmv_pgs_subtitle": "pgs",
    "pgs": "pgs",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory embedded and external SpiritFlix captions.")
    parser.add_argument("--root", action="append", dest="roots", help="Media root to scan. May be repeated.")
    parser.add_argument("--output", help="Explicit JSONL output path. Must be under the SpiritFlix admin caption inventory directory.")
    parser.add_argument("--limit", type=int, default=0, help="Optional max number of video files to probe.")
    return parser.parse_args()


def assert_under_report_dir(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    report_root = REPORT_DIR.resolve()
    if resolved != report_root and report_root not in resolved.parents:
        raise SystemExit(f"Refusing to write outside caption inventory directory: {resolved}")
    return resolved


def run_json(command: list[str]) -> tuple[dict[str, Any] | None, str | None]:
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=90)
    except Exception as error:  # noqa: BLE001 - serialized into inventory report
        return None, str(error)
    if result.returncode != 0:
        return None, (result.stderr or result.stdout or f"exit {result.returncode}").strip()
    try:
        return json.loads(result.stdout or "{}"), None
    except json.JSONDecodeError as error:
        return None, f"invalid JSON: {error}"


def iter_files(root: Path, extensions: set[str]) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in extensions),
        key=lambda path: str(path).lower(),
    )


def caption_format(value: str | None) -> str:
    if not value:
        return "unknown"
    return FORMAT_BY_CODEC.get(value.lower(), "unknown")


def stream_bool(tags: dict[str, Any], disposition: dict[str, Any], key: str) -> bool:
    value = tags.get(key)
    if isinstance(value, str) and value.lower() in {"1", "true", "yes"}:
        return True
    return bool(disposition.get(key) == 1)


def caption_id(*parts: object) -> str:
    digest = hashlib.sha1("|".join(str(part) for part in parts).encode("utf-8"), usedforsecurity=False).hexdigest()
    return f"caption-{digest[:16]}"


def embedded_tracks(media_path: Path, ffprobe_data: dict[str, Any]) -> list[dict[str, Any]]:
    tracks: list[dict[str, Any]] = []
    for stream in ffprobe_data.get("streams", []):
        if str(stream.get("codec_type", "")).lower() != "subtitle":
            continue
        tags = stream.get("tags") if isinstance(stream.get("tags"), dict) else {}
        disposition = stream.get("disposition") if isinstance(stream.get("disposition"), dict) else {}
        codec = stream.get("codec_name")
        stream_index = stream.get("index")
        language = tags.get("language") or tags.get("LANGUAGE")
        title = tags.get("title") or tags.get("handler_name") or codec or "Subtitle"
        forced = stream_bool(tags, disposition, "forced")
        sdh = "sdh" in str(title).lower() or "hearing" in str(title).lower()
        tracks.append(
            {
                "id": caption_id(media_path, "embedded", stream_index),
                "mediaPath": str(media_path),
                "sourceType": "embedded",
                "format": caption_format(str(codec) if codec else None),
                "language": language,
                "label": str(title),
                "kind": "captions" if sdh else "subtitles",
                "default": bool(disposition.get("default") == 1),
                "forced": forced,
                "sdh": sdh,
                "streamIndex": stream_index if isinstance(stream_index, int) else None,
                "reviewStatus": "source",
            }
        )
    return tracks


def mkvmerge_summary(media_path: Path, mkvmerge_path: str | None) -> dict[str, Any]:
    if not mkvmerge_path or media_path.suffix.lower() != ".mkv":
        return {"available": bool(mkvmerge_path), "used": False}
    data, error = run_json([mkvmerge_path, "-J", str(media_path)])
    if error:
        return {"available": True, "used": True, "error": error}
    subtitle_tracks = [
        {
            "id": track.get("id"),
            "type": track.get("type"),
            "codec": track.get("codec"),
            "properties": track.get("properties", {}),
        }
        for track in data.get("tracks", [])
        if track.get("type") == "subtitles"
    ]
    return {"available": True, "used": True, "subtitleTracks": subtitle_tracks}


def external_record(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower().lstrip(".")
    label = path.stem
    lower_label = label.lower()
    forced = "forced" in lower_label
    sdh = "sdh" in lower_label or "hearing" in lower_label
    return {
        "schema": "spiritflix-caption-inventory/v1",
        "recordType": "external_caption",
        "track": {
            "id": caption_id(path, "external"),
            "mediaPath": str(path.parent),
            "sourceType": "external",
            "format": suffix if f".{suffix}" in CAPTION_EXTENSIONS else "unknown",
            "label": label,
            "kind": "captions" if sdh else "subtitles",
            "default": False,
            "forced": forced,
            "sdh": sdh,
            "sourcePath": str(path),
            "reviewStatus": "source",
        },
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    args = parse_args()
    roots = [Path(root).expanduser() for root in (args.roots or [str(root) for root in DEFAULT_ROOTS])]
    output = assert_under_report_dir(
        Path(args.output).expanduser()
        if args.output
        else REPORT_DIR / f"{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d')}.jsonl"
    )
    ffprobe = shutil.which("ffprobe")
    mkvmerge = shutil.which("mkvmerge")
    if not ffprobe:
        raise SystemExit("ffprobe is required for caption inventory.")

    records: list[dict[str, Any]] = [
        {
            "schema": "spiritflix-caption-inventory/v1",
            "recordType": "run",
            "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
            "roots": [str(root) for root in roots],
            "tools": {"ffprobe": ffprobe, "mkvmerge": mkvmerge},
            "writePolicy": "media-read-only; report-jsonl-only",
        }
    ]

    video_files: list[Path] = []
    external_files: list[Path] = []
    for root in roots:
        video_files.extend(iter_files(root, VIDEO_EXTENSIONS))
        external_files.extend(iter_files(root, CAPTION_EXTENSIONS))
    if args.limit > 0:
        video_files = video_files[: args.limit]

    for index, media_path in enumerate(video_files, start=1):
        ffprobe_data, ffprobe_error = run_json([ffprobe, "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(media_path)])
        tracks = embedded_tracks(media_path, ffprobe_data or {}) if ffprobe_data else []
        records.append(
            {
                "schema": "spiritflix-caption-inventory/v1",
                "recordType": "media",
                "ordinal": index,
                "mediaPath": str(media_path),
                "container": (ffprobe_data or {}).get("format", {}).get("format_name"),
                "embeddedCaptionTrackCount": len(tracks),
                "captionTracks": tracks,
                "ffprobeError": ffprobe_error,
                "mkvmerge": mkvmerge_summary(media_path, mkvmerge),
            }
        )

    for caption_path in external_files:
        records.append(external_record(caption_path))

    records.append(
        {
            "schema": "spiritflix-caption-inventory/v1",
            "recordType": "summary",
            "videoFileCount": len(video_files),
            "externalCaptionFileCount": len(external_files),
            "mediaWithEmbeddedCaptions": sum(1 for record in records if record.get("recordType") == "media" and record.get("embeddedCaptionTrackCount", 0) > 0),
        }
    )
    write_jsonl(output, records)
    print(json.dumps({"output": str(output), "records": len(records), "videos": len(video_files), "externalCaptions": len(external_files)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
