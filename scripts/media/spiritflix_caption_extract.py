#!/usr/bin/env python3
"""Extract SpiritFlix source captions into a read-only WebVTT cache.

Reads inventory JSONL produced by spiritflix_caption_inventory.py and writes only
under /mnt/spirit-8tb/media/.spiritflix-admin/captions/.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


MEDIA_ROOT = Path("/mnt/spirit-8tb/media")
CAPTION_ROOT = MEDIA_ROOT / ".spiritflix-admin" / "captions"
INVENTORY_DIR = CAPTION_ROOT / "inventory"
CACHE_DIR = CAPTION_ROOT / "cache"
MANIFEST_DIR = CAPTION_ROOT / "manifests"
EVIDENCE_DIR = CAPTION_ROOT / "evidence"
TEXT_SOURCE_FORMATS = {"srt", "ass", "ssa", "vtt", "mov_text"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract embedded/external SpiritFlix captions to cached WebVTT.")
    parser.add_argument("--inventory", help="Inventory JSONL path. Defaults to the newest inventory report.")
    parser.add_argument("--pilot", help="Case-insensitive media path filter, e.g. S01E01.")
    parser.add_argument("--dry-run", action="store_true", help="Plan extraction without writing cache or manifests.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing cached VTT files.")
    parser.add_argument("--limit", type=int, default=0, help="Optional max number of media records to consider.")
    return parser.parse_args()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def media_key(media_path: str) -> str:
    digest = hashlib.sha256(media_path.encode("utf-8")).hexdigest()
    return digest[:24]


def latest_inventory() -> Path:
    reports = sorted(INVENTORY_DIR.glob("*.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not reports:
        raise SystemExit(f"No inventory reports found under {INVENTORY_DIR}")
    return reports[0]


def read_inventory(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def ensure_under_caption_root(path: Path) -> Path:
    resolved = path.resolve()
    root = CAPTION_ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise RuntimeError(f"Refusing caption write outside caption root: {resolved}")
    return resolved


def output_track(track: dict[str, Any], key: str) -> dict[str, Any]:
    track_id = str(track.get("id") or f"track-{track.get('streamIndex', 'unknown')}")
    cache_path = ensure_under_caption_root(CACHE_DIR / key / f"{track_id}.vtt")
    public_url = f"/api/spiritflix/captions/file?key={key}&track={track_id}"
    label = str(track.get("label") or track.get("language") or "Subtitle")
    if track.get("forced") and "forced" not in label.lower():
        language = str(track.get("language") or "").lower()
        label = f"{'English' if language == 'eng' else label} Forced"
    return {
        "id": track_id,
        "sourceType": track.get("sourceType", "embedded"),
        "sourceFormat": track.get("format", "unknown"),
        "outputFormat": "vtt",
        "language": track.get("language"),
        "label": label,
        "kind": track.get("kind", "subtitles"),
        "default": bool(track.get("default")),
        "forced": bool(track.get("forced")),
        "sdh": bool(track.get("sdh")),
        "streamIndex": track.get("streamIndex"),
        "sourcePath": track.get("sourcePath"),
        "cachePath": str(cache_path),
        "publicUrl": public_url,
        "reviewStatus": track.get("reviewStatus", "source"),
    }


def run_ffmpeg(ffmpeg: str, media_path: str, stream_index: int, output_path: Path, force: bool) -> tuple[bool, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y" if force else "-n",
        "-i",
        media_path,
        "-map",
        f"0:{stream_index}",
        "-c:s",
        "webvtt",
        str(output_path),
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=180)
    if result.returncode == 0:
        return True, "ok"
    return False, (result.stderr or result.stdout or f"ffmpeg exited {result.returncode}").strip()


def sanitize_webvtt(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8", errors="replace")
    blocks = text.replace("\r\n", "\n").replace("\r", "\n").split("\n\n")
    if not blocks:
        return {"removedZeroDurationCues": 0, "keptCues": 0}
    output_blocks = [blocks[0].strip() or "WEBVTT"]
    removed = 0
    kept = 0
    for block in blocks[1:]:
        lines = [line.rstrip() for line in block.split("\n") if line.strip()]
        timing_line = next((line for line in lines if "-->" in line), "")
        if timing_line:
            left, right = [part.strip().split()[0] for part in timing_line.split("-->", 1)]
            if left == right:
                removed += 1
                continue
            kept += 1
        output_blocks.append("\n".join(lines))
    if removed:
        path.write_text("\n\n".join(block for block in output_blocks if block).rstrip() + "\n", encoding="utf-8")
    return {"removedZeroDurationCues": removed, "keptCues": kept}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_under_caption_root(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print(json.dumps({"status": "NO_GO", "code": "FFMPEG_UNAVAILABLE"}))
        return 2

    inventory_path = Path(args.inventory).expanduser() if args.inventory else latest_inventory()
    records = read_inventory(inventory_path)
    media_records = [record for record in records if record.get("recordType") == "media"]
    if args.pilot:
        needle = args.pilot.lower()
        media_records = [record for record in media_records if needle in str(record.get("mediaPath", "")).lower()]
    if args.limit > 0:
        media_records = media_records[: args.limit]

    receipt: dict[str, Any] = {
        "schema": "spiritflix-caption-extraction/v1",
        "generatedAt": utc_now(),
        "inventory": str(inventory_path),
        "dryRun": bool(args.dry_run),
        "force": bool(args.force),
        "pilot": args.pilot,
        "ffmpeg": ffmpeg,
        "mediaConsidered": len(media_records),
        "actions": [],
        "summary": {"extractable": 0, "extracted": 0, "skipped": 0, "failed": 0, "manifestsWritten": 0},
    }

    manifests: dict[str, dict[str, Any]] = {}
    for media_record in media_records:
        media_path = str(media_record.get("mediaPath") or "")
        if not media_path or media_path.endswith(".part.mp4") or media_record.get("ffprobeError"):
            receipt["summary"]["skipped"] += 1
            receipt["actions"].append({"mediaPath": media_path, "status": "skipped", "reason": "unreadable_or_incomplete"})
            continue
        key = media_key(media_path)
        tracks = media_record.get("captionTracks") if isinstance(media_record.get("captionTracks"), list) else []
        manifest_tracks: list[dict[str, Any]] = []
        for track in tracks:
            source_format = str(track.get("format") or "unknown")
            stream_index = track.get("streamIndex")
            out_track = output_track(track, key)
            action = {
                "mediaPath": media_path,
                "mediaKey": key,
                "trackId": out_track["id"],
                "streamIndex": stream_index,
                "sourceFormat": source_format,
                "outputPath": out_track["cachePath"],
            }
            if source_format not in TEXT_SOURCE_FORMATS or not isinstance(stream_index, int):
                receipt["summary"]["skipped"] += 1
                receipt["actions"].append({**action, "status": "skipped", "reason": "unsupported_or_missing_stream_index"})
                continue
            receipt["summary"]["extractable"] += 1
            output_path = Path(out_track["cachePath"])
            if output_path.exists() and not args.force:
                sanitize_result = sanitize_webvtt(output_path)
                receipt["summary"]["skipped"] += 1
                manifest_tracks.append(out_track)
                receipt["actions"].append({**action, "status": "skipped", "reason": "cache_exists", **sanitize_result})
                continue
            if args.dry_run:
                manifest_tracks.append(out_track)
                receipt["actions"].append({**action, "status": "planned"})
                continue
            ok, message = run_ffmpeg(ffmpeg, media_path, stream_index, output_path, args.force)
            if ok and output_path.exists() and output_path.stat().st_size > 0:
                sanitize_result = sanitize_webvtt(output_path)
                receipt["summary"]["extracted"] += 1
                manifest_tracks.append(out_track)
                receipt["actions"].append({**action, "status": "extracted", "size": output_path.stat().st_size, **sanitize_result})
            else:
                receipt["summary"]["failed"] += 1
                receipt["actions"].append({**action, "status": "failed", "error": message})
        if manifest_tracks:
            manifests[key] = {"mediaPath": media_path, "mediaKey": key, "generatedAt": utc_now(), "tracks": manifest_tracks}

    if not args.dry_run:
        for key, manifest in manifests.items():
            write_json(MANIFEST_DIR / f"{key}.json", manifest)
            receipt["summary"]["manifestsWritten"] += 1

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    evidence_path = EVIDENCE_DIR / f"caption-extract-{stamp}.json"
    if not args.dry_run:
        write_json(evidence_path, receipt)
    else:
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "evidence": str(evidence_path), "summary": receipt["summary"]}, sort_keys=True))
    return 0 if receipt["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
