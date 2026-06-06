#!/usr/bin/env python3
"""Dispatch one media file to the Mac Mini for VideoToolbox encoding.

This is a narrow helper for SpiritFlix media tests. It copies a source file to
the Mac worker scratch area, runs ffmpeg with VideoToolbox, copies the encoded
file back to a requested output path, verifies it with ffprobe, and writes a
JSON receipt beside the output.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path


DEFAULT_MAC_HOST = "spirit-mac-mini"
DEFAULT_MAC_ROOT = "/Users/spiritmac/SpiritMediaWorker"
DEFAULT_FFMPEG = "/usr/local/bin/ffmpeg"
DEFAULT_FFPROBE = "/usr/local/bin/ffprobe"


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(argv: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, check=check, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def shell_join(argv: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in argv)


def ssh(host: str, script: str, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["ssh", "-o", "BatchMode=yes", host, script], check=check)


def ffprobe_local(path: Path) -> dict:
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


def remote_ffprobe(host: str, ffprobe: str, path: str) -> dict:
    command = shell_join(
        [
            ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            path,
        ]
    )
    completed = ssh(host, command)
    return json.loads(completed.stdout or "{}")


def first_stream(probe: dict, codec_type: str) -> dict:
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == codec_type:
            return stream
    return {}


def ensure_source(path: Path) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        raise SystemExit(f"Source file does not exist: {resolved}")
    return resolved


def ensure_output(path: Path, force: bool) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.exists() and not force:
        raise SystemExit(f"Output already exists, pass --force to replace: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Encode one file on the Mac Mini with VideoToolbox.")
    parser.add_argument("--source", required=True, help="Local/Dell source media path.")
    parser.add_argument("--output", required=True, help="Local/Dell output path for encoded file.")
    parser.add_argument("--mac-host", default=DEFAULT_MAC_HOST)
    parser.add_argument("--mac-root", default=DEFAULT_MAC_ROOT)
    parser.add_argument("--ffmpeg", default=DEFAULT_FFMPEG)
    parser.add_argument("--ffprobe", default=DEFAULT_FFPROBE)
    parser.add_argument("--video-bitrate", default="500k")
    parser.add_argument("--maxrate", default="900k")
    parser.add_argument("--bufsize", default="1800k")
    parser.add_argument("--profile", default="main10", choices=["main", "main10"])
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--keep-remote", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = ensure_source(Path(args.source))
    output = ensure_output(Path(args.output), args.force)
    temp_output = output.with_suffix(output.suffix + ".part")
    receipt_path = output.with_suffix(output.suffix + ".receipt.json")
    job_id = f"mac-vt-{int(time.time())}-{os.getpid()}"
    remote_dir = f"{args.mac_root.rstrip('/')}/jobs/{job_id}"
    remote_input = f"{remote_dir}/input{source.suffix.lower() or '.mkv'}"
    remote_output = f"{remote_dir}/output.mkv"

    started = time.time()
    local_probe = ffprobe_local(source)
    ssh(args.mac_host, f"mkdir -p {shlex.quote(remote_dir)}")
    run(["rsync", "-ah", "--info=progress2", str(source), f"{args.mac_host}:{remote_input}"])

    video_filter = "format=p010le" if args.profile == "main10" else "format=yuv420p"
    encode_argv = [
        args.ffmpeg,
        "-nostdin",
        "-hide_banner",
        "-y",
        "-i",
        remote_input,
        "-map",
        "0:v:0",
        "-map",
        "0:a:0",
        "-vf",
        video_filter,
        "-c:v",
        "hevc_videotoolbox",
        "-profile:v",
        args.profile,
        "-b:v",
        args.video_bitrate,
        "-maxrate",
        args.maxrate,
        "-bufsize",
        args.bufsize,
        "-tag:v",
        "hvc1",
        "-c:a",
        "copy",
        remote_output,
    ]
    remote_command = (
        "export PATH=/usr/local/bin:$PATH; "
        f"/usr/bin/time -l {shell_join(encode_argv)}"
    )
    encode = ssh(args.mac_host, remote_command)
    remote_probe = remote_ffprobe(args.mac_host, args.ffprobe, remote_output)

    if temp_output.exists():
        temp_output.unlink()
    run(["rsync", "-ah", "--info=progress2", f"{args.mac_host}:{remote_output}", str(temp_output)])
    ffprobe_local(temp_output)
    temp_output.replace(output)

    if not args.keep_remote:
        ssh(args.mac_host, f"rm -rf {shlex.quote(remote_dir)}", check=False)

    elapsed = time.time() - started
    receipt = {
        "at": utc_now(),
        "jobId": job_id,
        "macHost": args.mac_host,
        "source": str(source),
        "output": str(output),
        "elapsedSeconds": round(elapsed, 3),
        "profile": args.profile,
        "videoBitrate": args.video_bitrate,
        "maxrate": args.maxrate,
        "bufsize": args.bufsize,
        "sourceSize": source.stat().st_size,
        "outputSize": output.stat().st_size,
        "savingsPercent": round((1 - output.stat().st_size / source.stat().st_size) * 100, 2),
        "sourceVideo": first_stream(local_probe, "video"),
        "outputVideo": first_stream(remote_probe, "video"),
        "outputAudio": first_stream(remote_probe, "audio"),
        "encodeStdout": encode.stdout[-4000:],
        "encodeStderr": encode.stderr[-8000:],
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
