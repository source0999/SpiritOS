#!/usr/bin/env python3
"""Authorized anime episode importer for SpiritFlix/Jellyfin.

This tool is intentionally a placement/import wrapper. It does not bypass DRM,
site protections, or copyright restrictions. Use it only with files or URLs you
own, created, or have permission/license to download and process.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DEFAULT_ANIME_ROOT = Path(os.environ.get("SPIRITFLIX_ANIME_ROOT", "/mnt/spirit-8tb/media/anime"))
DEFAULT_ANIME_INBOX_ROOT = Path(
    os.environ.get("SPIRITFLIX_ANIME_INBOX_ROOT", "/mnt/spirit-8tb/media-inbox/anime")
)
DEFAULT_RECEIPT_DIR = ".spiritos-import-receipts"
BLOCKED_SOURCE_HOSTS = {
    "hianime.ad",
    "hianime.ms",
    "hianime.to",
    "aniwatch.to",
    "zoro.to",
}
VIDEO_EXTENSIONS = {".mkv", ".mp4", ".webm", ".mov", ".m4v"}


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sanitize_segment(value: str, fallback: str = "untitled") -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "", value.strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned[:140] or fallback


def ensure_under_root(root: Path, target: Path) -> Path:
    resolved_root = root.resolve()
    resolved_target = target.resolve()
    try:
        resolved_target.relative_to(resolved_root)
    except ValueError as exc:
        raise SystemExit(f"Refusing to write outside anime root: {resolved_target}") from exc
    return resolved_target


def parse_episode_range(value: str | None, fallback_episode: int | None) -> list[int]:
    if value:
        episodes: list[int] = []
        for part in value.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                start_raw, end_raw = part.split("-", 1)
                start = int(start_raw)
                end = int(end_raw)
                if end < start:
                    raise SystemExit(f"Invalid episode range: {part}")
                episodes.extend(range(start, end + 1))
            else:
                episodes.append(int(part))
        return sorted(dict.fromkeys(episodes))

    if fallback_episode is not None:
        return [fallback_episode]

    return [1]


def reject_blocked_url(source_url: str) -> None:
    host = urlparse(source_url).hostname or ""
    host = host.lower().removeprefix("www.")
    if host in BLOCKED_SOURCE_HOSTS:
        raise SystemExit(
            f"Refusing source host {host}. Use only authorized direct media or yt-dlp-supported URLs."
        )


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ffprobe(path: Path) -> dict[str, Any]:
    if not command_exists("ffprobe"):
        return {}
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return {"error": result.stderr.strip()}
    try:
        return json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        return {}


def video_height(probe: dict[str, Any]) -> int | None:
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == "video" and stream.get("height"):
            try:
                return int(stream["height"])
            except (TypeError, ValueError):
                return None
    return None


def audio_languages(probe: dict[str, Any]) -> list[str]:
    languages: list[str] = []
    for stream in probe.get("streams", []):
        if stream.get("codec_type") != "audio":
            continue
        tags = stream.get("tags") or {}
        language = str(tags.get("language") or "und").lower()
        if language not in languages:
            languages.append(language)
    return languages


def make_file_name(
    series: str,
    season: int,
    episode: int,
    episode_title: str | None,
    quality: str | None,
    extension: str,
) -> str:
    stem = f"{sanitize_segment(series)} - S{season:02d}E{episode:02d}"
    if episode_title:
        stem += f" - {sanitize_segment(episode_title)}"
    if quality:
        stem += f" [{sanitize_segment(quality)}]"
    return f"{stem}{extension}"


def find_existing_episode(season_dir: Path, series: str, season: int, episode: int) -> Path | None:
    if not season_dir.exists():
        return None
    safe_series = re.escape(sanitize_segment(series))
    pattern = re.compile(rf"^{safe_series} - S{season:02d}E{episode:02d}(?:\b|[ ._-]).*", re.IGNORECASE)
    matches = sorted(
        path for path in season_dir.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS and pattern.match(path.name)
    )
    return matches[0] if matches else None


def write_receipt(receipt_dir: Path, payload: dict[str, Any]) -> Path:
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_dir / f"{dt.datetime.now(dt.UTC).strftime('%Y%m%d')}.jsonl"
    with receipt_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")
    return receipt_path


def download_with_ytdlp(source_url: str, staging_dir: Path) -> Path:
    if not command_exists("yt-dlp"):
        raise SystemExit("yt-dlp is not installed on this host. Install it before URL imports.")

    output_template = str(staging_dir / "%(title).120B.%(ext)s")
    subprocess.run(
        [
            "yt-dlp",
            "--no-playlist",
            "--continue",
            "--restrict-filenames",
            "--merge-output-format",
            "mkv",
            "-f",
            "bv*+ba/best",
            "-o",
            output_template,
            source_url,
        ],
        check=True,
    )
    candidates = sorted(
        [path for path in staging_dir.iterdir() if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise SystemExit("yt-dlp completed but no video file was found in staging.")
    return candidates[0]


def load_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    if not manifest_path.exists():
        raise SystemExit(f"Manifest does not exist: {manifest_path}")

    if manifest_path.suffix.lower() == ".json":
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise SystemExit("JSON manifest must be an array of episode objects.")
        return [dict(item) for item in data]

    if manifest_path.suffix.lower() == ".jsonl":
        rows: list[dict[str, Any]] = []
        for line_number, line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            try:
                parsed = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSONL manifest line {line_number}: {exc}") from exc
            rows.append(dict(parsed))
        return rows

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def row_value(row: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def args_for_manifest_row(base_args: argparse.Namespace, row: dict[str, Any], row_number: int) -> argparse.Namespace:
    row_args = argparse.Namespace(**vars(base_args))

    row_args.series = row_value(row, "series", "series_title", "show") or base_args.series
    season = row_value(row, "season", "season_number") or (str(base_args.season) if base_args.season else None)
    episode = row_value(row, "episode", "episode_number", "ep")
    row_args.source_url = row_value(row, "source_url", "url", "link")
    row_args.source_file = row_value(row, "source_file", "file", "path")
    row_args.episode_title = row_value(row, "episode_title", "title", "name") or base_args.episode_title
    row_args.audio = row_value(row, "audio") or base_args.audio
    row_args.quality = row_value(row, "quality") or base_args.quality

    if not row_args.series:
        raise SystemExit(f"Manifest row {row_number} is missing series and no --series fallback was provided.")
    if not season:
        raise SystemExit(f"Manifest row {row_number} is missing season and no --season fallback was provided.")
    if not episode:
        raise SystemExit(f"Manifest row {row_number} is missing episode.")
    if not row_args.source_url and not row_args.source_file:
        raise SystemExit(f"Manifest row {row_number} is missing source_url/link or source_file/path.")
    if row_args.source_url and row_args.source_file:
        raise SystemExit(f"Manifest row {row_number} has both source_url and source_file; choose one.")
    if row_args.audio not in {"dub", "sub", "original"}:
        raise SystemExit(f"Manifest row {row_number} has invalid audio value: {row_args.audio}")

    try:
        row_args.season = int(season)
        row_args.episode = int(episode)
    except ValueError as exc:
        raise SystemExit(f"Manifest row {row_number} has non-numeric season/episode.") from exc

    return row_args


def import_episode(args: argparse.Namespace, episode: int) -> dict[str, Any]:
    anime_root = DEFAULT_ANIME_INBOX_ROOT if args.send_to_converter else Path(args.target_root)
    allowed_roots = {str(DEFAULT_ANIME_ROOT)}
    if args.send_to_converter:
        allowed_roots.add(str(DEFAULT_ANIME_INBOX_ROOT))
    if str(anime_root) not in allowed_roots and not args.allow_custom_root:
        raise SystemExit(
            f"Refusing custom target root {anime_root}. Pass --allow-custom-root for an explicit test root."
        )

    anime_root.mkdir(parents=True, exist_ok=True)
    series_dir = ensure_under_root(anime_root, anime_root / sanitize_segment(args.series))
    season_dir = ensure_under_root(series_dir, series_dir / f"Season {args.season:02d}")
    receipt_dir = ensure_under_root(anime_root, anime_root / DEFAULT_RECEIPT_DIR)

    source_path: Path | None = None
    staging_parent: tempfile.TemporaryDirectory[str] | None = None
    source_kind = "source-file" if args.source_file else "source-url"

    if args.source_file:
        source_path = Path(args.source_file)
        if not source_path.exists():
            raise SystemExit(f"Source file does not exist: {source_path}")
    elif args.source_url:
        reject_blocked_url(args.source_url)
        staging_parent = tempfile.TemporaryDirectory(prefix="spiritflix-anime-import-")
        source_path = download_with_ytdlp(args.source_url, Path(staging_parent.name))
    else:
        raise SystemExit("Provide --source-file or --source-url.")

    probe = ffprobe(source_path)
    height = video_height(probe)
    quality = args.quality or (f"{height}p" if args.include_detected_quality and height else None)
    target_name = make_file_name(
        args.series,
        args.season,
        episode,
        args.episode_title,
        quality,
        source_path.suffix.lower() or ".mkv",
    )
    target_path = ensure_under_root(season_dir, season_dir / target_name)

    season_dir.mkdir(parents=True, exist_ok=True)
    existing_episode_path = find_existing_episode(season_dir, args.series, args.season, episode)
    status = "planned"
    if existing_episode_path and not args.force:
        target_path = existing_episode_path
        status = "skipped_existing"
    elif args.dry_run:
        status = "dry_run"
    else:
        if source_path.resolve() == target_path.resolve():
            status = "skipped_existing"
        else:
            temp_path = target_path.with_suffix(target_path.suffix + ".part")
            if temp_path.exists():
                temp_path.unlink()
            shutil.copy2(source_path, temp_path)
            temp_path.replace(target_path)
            status = "imported"

    receipt = {
        "at": utc_now(),
        "status": status,
        "series": args.series,
        "season": args.season,
        "episode": episode,
        "audio": args.audio,
        "sourceKind": source_kind,
        "source": args.source_url or str(source_path),
        "targetPath": str(target_path),
        "targetMode": "converter-inbox" if args.send_to_converter else "final-library",
        "targetExists": target_path.exists(),
        "quality": quality,
        "audioLanguages": audio_languages(probe),
        "sha256": sha256_file(target_path) if target_path.exists() and not args.no_hash else None,
        "authorization": {
            "affirmed": True,
            "note": args.authorization_note,
        },
    }
    receipt["receiptPath"] = str(write_receipt(receipt_dir, receipt))

    if staging_parent:
        staging_parent.cleanup()

    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import authorized anime episodes into SpiritFlix/Jellyfin anime folders.")
    parser.add_argument("--series", help="Series folder/title, for example 'Rurouni Kenshin (1996)'. Required unless every manifest row has series.")
    parser.add_argument("--season", type=int, help="Season number. Required unless every manifest row has season.")
    parser.add_argument("--episode", type=int, help="Single episode number. Defaults to 1.")
    parser.add_argument("--episodes", help="Episode list/range, for example '1' or '1-27'.")
    parser.add_argument("--episode-title", help="Optional episode title for the target filename.")
    parser.add_argument("--audio", default="dub", choices=["dub", "sub", "original"], help="Receipt audio lane.")
    parser.add_argument("--quality", help="Override quality label in the target filename, for example 1080p.")
    parser.add_argument("--include-detected-quality", action="store_true", help="Append detected height such as [1080p] to new filenames.")
    parser.add_argument("--source-file", help="Authorized local media file to place.")
    parser.add_argument("--source-url", help="Authorized URL to download with yt-dlp.")
    parser.add_argument("--manifest", help="CSV, JSON, or JSONL manifest with series, season, episode, and source_url/source_file columns.")
    parser.add_argument("--target-root", default=str(DEFAULT_ANIME_ROOT), help="Anime root. Defaults to SpiritFlix anime root.")
    parser.add_argument(
        "--send-to-converter",
        action="store_true",
        help="Place files in the media-inbox anime tree so media-ingest-worker converts them before final library placement.",
    )
    parser.add_argument("--allow-custom-root", action="store_true", help="Allow target roots other than the default anime root.")
    parser.add_argument("--affirm-authorized", action="store_true", help="Required: affirm you own or have rights to process this media.")
    parser.add_argument("--authorization-note", default="User affirmed authorized media import.", help="Receipt authorization note.")
    parser.add_argument("--stop-after", type=int, default=None, help="Stop after N imported/planned episodes.")
    parser.add_argument("--dry-run", action="store_true", help="Plan and write receipts without copying/downloading final files.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing target file.")
    parser.add_argument("--no-hash", action="store_true", help="Skip SHA-256 hash calculation in receipts.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.affirm_authorized:
        parser.error("--affirm-authorized is required for all imports.")

    if args.manifest:
        rows = load_manifest(Path(args.manifest))
        if args.stop_after is not None:
            rows = rows[: max(args.stop_after, 0)]
        receipts = [
            import_episode(row_args, row_args.episode)
            for row_number, row in enumerate(rows, start=1)
            for row_args in [args_for_manifest_row(args, row, row_number)]
        ]
        print(json.dumps({"ok": True, "count": len(receipts), "receipts": receipts}, indent=2))
        return 0

    if not args.series:
        parser.error("--series is required without --manifest.")
    if args.season is None:
        parser.error("--season is required without --manifest.")
    if not args.source_url and not args.source_file:
        parser.error("--source-url or --source-file is required without --manifest.")

    episodes = parse_episode_range(args.episodes, args.episode)
    if args.stop_after is not None:
        episodes = episodes[: max(args.stop_after, 0)]

    receipts = [import_episode(args, episode) for episode in episodes]
    print(json.dumps({"ok": True, "count": len(receipts), "receipts": receipts}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
