#!/usr/bin/env python3
"""Download, dual-audio remux, and Mac-optimize authorized anime episodes.

Run this from the Dell/SpiritOS host. It dispatches the network download and
VideoToolbox encode to the Mac, then copies the verified MP4 into the
SpiritFlix/Jellyfin anime library.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DEFAULT_ANIME_ROOT = Path(os.environ.get("SPIRITFLIX_ANIME_ROOT", "/mnt/spirit-8tb/media/anime"))
DEFAULT_MAC_HOST = os.environ.get("SPIRITFLIX_MAC_HOST", "spirit-mac-mini")
DEFAULT_MAC_ROOT = os.environ.get("SPIRITFLIX_MAC_ROOT", "~/SpiritMediaWorker")
DEFAULT_MAC_CLOUD_ROOT = os.environ.get("SPIRITFLIX_MAC_CLOUD_ANIME_ROOT", "~/yes/anime")
DEFAULT_FFMPEG = os.environ.get("SPIRITFLIX_MAC_FFMPEG", "ffmpeg")
DEFAULT_FFPROBE = os.environ.get("SPIRITFLIX_MAC_FFPROBE", "ffprobe")
DEFAULT_YTDLP = os.environ.get("SPIRITFLIX_MAC_YTDLP", "yt-dlp")
DEFAULT_RECEIPT_DIR = ".spiritos-import-receipts"
BLOCKED_SOURCE_HOSTS = {
    "hianime.ad",
    "hianime.ms",
    "hianime.to",
    "aniwatch.to",
    "zoro.to",
}
VIDEO_EXTENSIONS = {".mp4", ".m4v", ".mkv", ".mov", ".webm"}

REMOTE_WORKER = r'''
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(argv):
    completed = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        raise SystemExit(
            json.dumps(
                {
                    "ok": False,
                    "command": argv,
                    "returncode": completed.returncode,
                    "stdout": completed.stdout[-4000:],
                    "stderr": completed.stderr[-8000:],
                }
            )
        )
    return completed


def which(binary):
    if os.path.isabs(binary) and os.access(binary, os.X_OK):
        return binary
    found = shutil.which(binary)
    if found:
        return found
    for prefix in (
        "/opt/homebrew/bin",
        "/usr/local/bin",
        str(Path.home() / "Library/Python/3.9/bin"),
        str(Path.home() / ".local/bin"),
    ):
        candidate = Path(prefix) / binary
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise SystemExit(json.dumps({"ok": False, "error": f"Missing executable on Mac: {binary}"}))


def newest_file(directory, prefix):
    candidates = [
        path for path in Path(directory).iterdir()
        if path.is_file()
        and path.name.startswith(prefix)
        and not path.name.endswith((".part", ".ytdl", ".temp"))
    ]
    if not candidates:
        raise SystemExit(json.dumps({"ok": False, "error": f"No downloaded file found for prefix {prefix}"}))
    return max(candidates, key=lambda path: path.stat().st_mtime)


def ffprobe(ffprobe_bin, path):
    completed = run(
        [
            ffprobe_bin,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
    )
    return json.loads(completed.stdout or "{}")


def ensure_nonempty(path):
    path = Path(path)
    if not path.exists() or not path.is_file() or path.stat().st_size <= 0:
        raise SystemExit(json.dumps({"ok": False, "error": f"Expected non-empty file: {path}"}))


def main():
    payload = json.loads(Path(sys.argv[1]).read_text())
    yt_dlp = which(payload.get("yt_dlp", "yt-dlp"))
    ffmpeg = which(payload.get("ffmpeg", "ffmpeg"))
    ffprobe_bin = which(payload.get("ffprobe", "ffprobe"))
    job_dir = Path(payload["job_dir"]).expanduser()
    cloud_output = Path(payload["cloud_output"]).expanduser()
    job_dir.mkdir(parents=True, exist_ok=True)
    cloud_output.parent.mkdir(parents=True, exist_ok=True)
    staging_output = cloud_output.with_name("." + cloud_output.name + ".part.mp4")

    with tempfile.TemporaryDirectory(prefix="dual-audio-", dir=str(job_dir)) as tmp:
        tmpdir = Path(tmp)
        sub_template = str(tmpdir / "sub.%(ext)s")
        dub_template = str(tmpdir / "dub.%(ext)s")

        run(
            [
                yt_dlp,
                "--no-playlist",
                "--continue",
                "--merge-output-format",
                "mp4",
                "-f",
                "bv*+ba/best",
                "-o",
                sub_template,
                payload["sub_url"],
            ]
        )
        sub_file = newest_file(tmpdir, "sub.")
        ensure_nonempty(sub_file)

        run(
            [
                yt_dlp,
                "--no-playlist",
                "--continue",
                "-f",
                "ba/best",
                "-o",
                dub_template,
                payload["dub_url"],
            ]
        )
        dub_file = newest_file(tmpdir, "dub.")
        ensure_nonempty(dub_file)

        remuxed = tmpdir / "dual-source.mp4"
        run(
            [
                ffmpeg,
                "-nostdin",
                "-hide_banner",
                "-y",
                "-i",
                str(sub_file),
                "-i",
                str(dub_file),
                "-map",
                "0:v:0",
                "-map",
                "0:a:0",
                "-map",
                "1:a:0",
                "-c",
                "copy",
                "-metadata:s:a:0",
                "language=jpn",
                "-metadata:s:a:0",
                "title=Japanese",
                "-metadata:s:a:1",
                "language=eng",
                "-metadata:s:a:1",
                "title=English",
                "-disposition:a:0",
                "default",
                "-disposition:a:1",
                "0",
                "-movflags",
                "+faststart",
                str(remuxed),
            ]
        )
        ensure_nonempty(remuxed)

        run(
            [
                ffmpeg,
                "-nostdin",
                "-hide_banner",
                "-y",
                "-i",
                str(remuxed),
                "-map",
                "0:v:0",
                "-map",
                "0:a:0",
                "-map",
                "0:a:1",
                "-vf",
                payload.get("video_filter", "format=p010le"),
                "-c:v",
                "hevc_videotoolbox",
                "-profile:v",
                payload.get("profile", "main10"),
                "-b:v",
                payload.get("video_bitrate", "900k"),
                "-maxrate",
                payload.get("maxrate", "1600k"),
                "-bufsize",
                payload.get("bufsize", "3200k"),
                "-tag:v",
                "hvc1",
                "-c:a",
                "aac",
                "-b:a",
                payload.get("audio_bitrate", "128k"),
                "-metadata:s:a:0",
                "language=jpn",
                "-metadata:s:a:0",
                "title=Japanese",
                "-metadata:s:a:1",
                "language=eng",
                "-metadata:s:a:1",
                "title=English",
                "-disposition:a:0",
                "default",
                "-disposition:a:1",
                "0",
                "-movflags",
                "+faststart",
                str(staging_output),
            ]
        )
        ensure_nonempty(staging_output)
        probe = ffprobe(ffprobe_bin, staging_output)
        audio_count = len([stream for stream in probe.get("streams", []) if stream.get("codec_type") == "audio"])
        video_count = len([stream for stream in probe.get("streams", []) if stream.get("codec_type") == "video"])
        if video_count < 1 or audio_count < 2:
            raise SystemExit(
                json.dumps(
                    {
                        "ok": False,
                        "error": "Encoded output is missing expected video or dual audio tracks.",
                        "videoStreams": video_count,
                        "audioStreams": audio_count,
                    }
                )
            )
        staging_output.replace(cloud_output)
        transfer_output = job_dir / "final-output.mp4"
        if transfer_output.exists():
            transfer_output.unlink()
        try:
            os.link(cloud_output, transfer_output)
        except OSError:
            shutil.copy2(cloud_output, transfer_output)

    result = {
        "ok": True,
        "cloudOutput": str(cloud_output),
        "transferOutput": str(transfer_output),
        "size": cloud_output.stat().st_size,
        "probe": ffprobe(ffprobe_bin, cloud_output),
    }
    print(json.dumps(result))


main()
'''


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sanitize_segment(value: str, fallback: str = "untitled") -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "", value.strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned[:140] or fallback


def ensure_under_root(root: Path, target: Path) -> Path:
    resolved_root = root.expanduser().resolve()
    resolved_target = target.expanduser().resolve()
    try:
        resolved_target.relative_to(resolved_root)
    except ValueError as exc:
        raise SystemExit(f"Refusing to write outside root: {resolved_target}") from exc
    return resolved_target


def reject_blocked_url(source_url: str) -> None:
    host = urlparse(source_url).hostname or ""
    host = host.lower().removeprefix("www.")
    if host in BLOCKED_SOURCE_HOSTS:
        raise SystemExit(f"Refusing source host {host}. Use only authorized direct media/HLS URLs.")


def run(argv: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(argv, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and completed.returncode != 0:
        raise SystemExit(
            "Command failed "
            f"({completed.returncode}): {' '.join(shlex.quote(part) for part in argv)}\n"
            f"stdout:\n{completed.stdout[-4000:]}\n"
            f"stderr:\n{completed.stderr[-8000:]}"
        )
    return completed


def remote_shell(host: str, script: str, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["ssh", "-o", "BatchMode=yes", host, script], check=check)


def remote_expand(host: str, path: str) -> str:
    completed = remote_shell(
        host,
        "python3 -c "
        + shlex.quote(
            "import os,sys; print(os.path.abspath(os.path.expanduser(sys.argv[1])))"
        )
        + " "
        + shlex.quote(path),
    )
    return completed.stdout.strip()


def rsync_from_remote(host: str, remote_path: str, local_path: Path) -> None:
    local_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = local_path.with_suffix(local_path.suffix + ".part")
    if temp_path.exists():
        temp_path.unlink()
    run(["rsync", "-ah", "--info=progress2", f"{host}:{remote_path}", str(temp_path)])
    if not temp_path.exists() or temp_path.stat().st_size <= 0:
        raise SystemExit(f"Copied output is missing or empty: {temp_path}")
    temp_path.replace(local_path)


def ffprobe_local(path: Path) -> dict[str, Any]:
    completed = run(
        [
            "ffprobe",
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(path),
        ]
    )
    return json.loads(completed.stdout or "{}")


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


def make_file_name(series: str, season: int, episode: int, episode_title: str | None, quality: str | None) -> str:
    stem = f"{sanitize_segment(series)} - S{season:02d}E{episode:02d}"
    if episode_title:
        stem += f" - {sanitize_segment(episode_title)}"
    if quality:
        stem += f" [{sanitize_segment(quality)}]"
    return f"{stem}.mp4"


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


def load_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    if not manifest_path.exists():
        raise SystemExit(f"Manifest does not exist: {manifest_path}")
    if manifest_path.suffix.lower() == ".json":
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise SystemExit("JSON manifest must be an array of episode objects.")
        return [dict(item) for item in data]
    if manifest_path.suffix.lower() == ".jsonl":
        rows = []
        for line_number, line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            try:
                rows.append(dict(json.loads(stripped)))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSONL manifest line {line_number}: {exc}") from exc
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
    row_args.season = int(row_value(row, "season", "season_number") or base_args.season or 0)
    row_args.episode = int(row_value(row, "episode", "episode_number", "ep") or 0)
    row_args.episode_title = row_value(row, "episode_title", "title", "name") or base_args.episode_title
    row_args.sub_url = row_value(row, "sub_m3u8_url", "sub_url", "jpn_url", "japanese_url")
    row_args.dub_url = row_value(row, "dub_m3u8_url", "dub_url", "eng_url", "english_url")
    row_args.quality = row_value(row, "quality") or base_args.quality
    if not row_args.series:
        raise SystemExit(f"Manifest row {row_number} is missing series.")
    if row_args.season < 1 or row_args.episode < 1:
        raise SystemExit(f"Manifest row {row_number} needs numeric season and episode.")
    if not row_args.sub_url or not row_args.dub_url:
        raise SystemExit(f"Manifest row {row_number} needs sub_m3u8_url and dub_m3u8_url.")
    return row_args


def run_episode(args: argparse.Namespace) -> dict[str, Any]:
    reject_blocked_url(args.sub_url)
    reject_blocked_url(args.dub_url)

    anime_root = Path(args.target_root)
    allowed_root = DEFAULT_ANIME_ROOT.resolve()
    if anime_root.resolve() != allowed_root and not args.allow_custom_root:
        raise SystemExit(f"Refusing custom target root {anime_root}. Pass --allow-custom-root for a test root.")

    series_dir = ensure_under_root(anime_root, anime_root / sanitize_segment(args.series))
    season_dir = ensure_under_root(series_dir, series_dir / f"Season {args.season:02d}")
    receipt_dir = ensure_under_root(anime_root, anime_root / DEFAULT_RECEIPT_DIR)
    target_name = make_file_name(args.series, args.season, args.episode, args.episode_title, args.quality)
    target_path = ensure_under_root(season_dir, season_dir / target_name)
    season_dir.mkdir(parents=True, exist_ok=True)

    existing = find_existing_episode(season_dir, args.series, args.season, args.episode)
    if existing and not args.force:
        receipt = {
            "at": utc_now(),
            "status": "skipped_existing",
            "series": args.series,
            "season": args.season,
            "episode": args.episode,
            "targetPath": str(existing),
            "targetExists": True,
            "authorization": {"affirmed": True, "note": args.authorization_note},
        }
        receipt["receiptPath"] = str(write_receipt(receipt_dir, receipt))
        return receipt

    if args.dry_run:
        receipt = {
            "at": utc_now(),
            "status": "dry_run",
            "series": args.series,
            "season": args.season,
            "episode": args.episode,
            "targetPath": str(target_path),
            "targetExists": target_path.exists(),
            "authorization": {"affirmed": True, "note": args.authorization_note},
        }
        receipt["receiptPath"] = str(write_receipt(receipt_dir, receipt))
        return receipt

    job_id = f"dual-audio-{dt.datetime.now(dt.UTC).strftime('%Y%m%dT%H%M%SZ')}-{os.getpid()}"
    mac_root = remote_expand(args.mac_host, args.mac_root).rstrip("/")
    mac_job_dir = f"{mac_root}/jobs/{job_id}"
    mac_payload_path = f"{mac_job_dir}/payload.json"
    mac_worker_path = f"{mac_job_dir}/worker.py"
    cloud_root = remote_expand(args.mac_host, args.mac_cloud_root).rstrip("/")
    cloud_output = f"{cloud_root}/{sanitize_segment(args.series)}/Season {args.season:02d}/{target_name}"

    payload = {
        "job_id": job_id,
        "job_dir": mac_job_dir,
        "sub_url": args.sub_url,
        "dub_url": args.dub_url,
        "cloud_output": cloud_output,
        "yt_dlp": args.yt_dlp,
        "ffmpeg": args.ffmpeg,
        "ffprobe": args.ffprobe,
        "video_bitrate": args.video_bitrate,
        "maxrate": args.maxrate,
        "bufsize": args.bufsize,
        "audio_bitrate": args.audio_bitrate,
        "profile": args.profile,
        "video_filter": "format=p010le" if args.profile == "main10" else "format=yuv420p",
    }

    with tempfile.TemporaryDirectory(prefix="spiritflix-dual-audio-") as tmp:
        local_payload = Path(tmp) / "payload.json"
        local_worker = Path(tmp) / "worker.py"
        local_payload.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        local_worker.write_text(REMOTE_WORKER, encoding="utf-8")
        remote_shell(args.mac_host, f"mkdir -p {shlex.quote(mac_job_dir)}")
        run(["scp", str(local_payload), f"{args.mac_host}:{mac_payload_path}"])
        run(["scp", str(local_worker), f"{args.mac_host}:{mac_worker_path}"])

    started = dt.datetime.now(dt.UTC)
    completed = remote_shell(
        args.mac_host,
        "export PATH=/opt/homebrew/bin:/usr/local/bin:$HOME/Library/Python/3.9/bin:$PATH; "
        f"python3 {shlex.quote(mac_worker_path)} {shlex.quote(mac_payload_path)}",
    )
    try:
        mac_result = json.loads(completed.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Mac worker returned non-JSON output:\n{completed.stdout}\n{completed.stderr}") from exc
    if not mac_result.get("ok"):
        raise SystemExit(f"Mac worker failed: {json.dumps(mac_result, indent=2)}")

    rsync_from_remote(
        args.mac_host,
        str(mac_result.get("transferOutput") or mac_result.get("cloudOutput") or cloud_output),
        target_path,
    )
    probe = ffprobe_local(target_path)
    audio_count = len([stream for stream in probe.get("streams", []) if stream.get("codec_type") == "audio"])
    if audio_count < 2:
        raise SystemExit(f"Final SpiritFlix output does not have two audio tracks: {target_path}")

    if not args.keep_remote_job:
        remote_shell(args.mac_host, f"rm -rf {shlex.quote(mac_job_dir)}", check=False)

    elapsed = (dt.datetime.now(dt.UTC) - started).total_seconds()
    receipt = {
        "at": utc_now(),
        "status": "imported",
        "series": args.series,
        "season": args.season,
        "episode": args.episode,
        "audio": "dual",
        "sourceKind": "dual-hls",
        "targetPath": str(target_path),
        "targetMode": "final-library",
        "targetExists": target_path.exists(),
        "macHost": args.mac_host,
        "macCloudOutput": cloud_output,
        "elapsedSeconds": round(elapsed, 3),
        "quality": args.quality,
        "audioLanguages": audio_languages(probe),
        "outputSize": target_path.stat().st_size,
        "macOutputSize": mac_result.get("size"),
        "authorization": {"affirmed": True, "note": args.authorization_note},
    }
    receipt["receiptPath"] = str(write_receipt(receipt_dir, receipt))
    return receipt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mac-optimize authorized dual-audio anime HLS into SpiritFlix.")
    parser.add_argument("--series", help="Series folder/title.")
    parser.add_argument("--season", type=int, help="Season number.")
    parser.add_argument("--episode", type=int, default=1, help="Episode number.")
    parser.add_argument("--episode-title", help="Optional episode title.")
    parser.add_argument("--sub-url", "--sub-m3u8-url", dest="sub_url", help="Japanese/sub HLS .m3u8 URL.")
    parser.add_argument("--dub-url", "--dub-m3u8-url", dest="dub_url", help="English/dub HLS .m3u8 URL.")
    parser.add_argument("--manifest", help="CSV, JSON, or JSONL with series, season, episode, sub_m3u8_url, dub_m3u8_url.")
    parser.add_argument("--stop-after", type=int, default=None, help="Stop after N manifest rows.")
    parser.add_argument("--target-root", default=str(DEFAULT_ANIME_ROOT), help="SpiritFlix anime root.")
    parser.add_argument("--mac-host", default=DEFAULT_MAC_HOST)
    parser.add_argument("--mac-root", default=DEFAULT_MAC_ROOT)
    parser.add_argument("--mac-cloud-root", default=DEFAULT_MAC_CLOUD_ROOT, help="Mac cloud-monitored anime root.")
    parser.add_argument("--yt-dlp", default=DEFAULT_YTDLP)
    parser.add_argument("--ffmpeg", default=DEFAULT_FFMPEG)
    parser.add_argument("--ffprobe", default=DEFAULT_FFPROBE)
    parser.add_argument("--quality", default="1080p")
    parser.add_argument("--video-bitrate", default="900k")
    parser.add_argument("--maxrate", default="1600k")
    parser.add_argument("--bufsize", default="3200k")
    parser.add_argument("--audio-bitrate", default="128k")
    parser.add_argument("--profile", default="main10", choices=["main", "main10"])
    parser.add_argument("--allow-custom-root", action="store_true")
    parser.add_argument("--affirm-authorized", action="store_true", help="Required: affirm you can process this media.")
    parser.add_argument("--authorization-note", default="User affirmed authorized dual-audio anime import.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--keep-remote-job", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.affirm_authorized:
        parser.error("--affirm-authorized is required.")

    if args.manifest:
        rows = load_manifest(Path(args.manifest))
        if args.stop_after is not None:
            rows = rows[: max(args.stop_after, 0)]
        receipts = [
            run_episode(row_args)
            for row_number, row in enumerate(rows, start=1)
            for row_args in [args_for_manifest_row(args, row, row_number)]
        ]
        print(json.dumps({"ok": True, "count": len(receipts), "receipts": receipts}, indent=2))
        return 0

    if not args.series:
        parser.error("--series is required without --manifest.")
    if args.season is None:
        parser.error("--season is required without --manifest.")
    if not args.sub_url or not args.dub_url:
        parser.error("--sub-url and --dub-url are required without --manifest.")

    receipt = run_episode(args)
    print(json.dumps({"ok": True, "count": 1, "receipts": [receipt]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
