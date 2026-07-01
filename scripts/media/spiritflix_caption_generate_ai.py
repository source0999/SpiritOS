#!/usr/bin/env python3
"""Guarded manual AI draft-caption generation for SpiritFlix.

This script is intentionally one-file-at-a-time. It never downloads models,
never calls cloud APIs, and writes only draft WebVTT artifacts under the
SpiritFlix caption admin root.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


MEDIA_ROOT = Path("/mnt/spirit-8tb/media")
CAPTION_ROOT = MEDIA_ROOT / ".spiritflix-admin" / "captions"
GENERATED_DIR = CAPTION_ROOT / "generated"
MANIFEST_DIR = CAPTION_ROOT / "manifests"
EVIDENCE_DIR = CAPTION_ROOT / "evidence"
SOURCE_FORMATS = {"srt", "ass", "ssa", "vtt", "mov_text"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate one manual draft WebVTT caption file with a local backend.")
    parser.add_argument("--media-file", required=True, help="One explicit media file to caption.")
    parser.add_argument("--language", default="auto", help="Language hint for the local backend.")
    parser.add_argument("--audio-stream-index", type=int, default=0, help="Audio stream index hint for receipt metadata.")
    parser.add_argument("--model", help="Local model name/path already installed for the selected backend.")
    parser.add_argument("--backend", choices=["auto", "faster-whisper", "whisper", "whisper.cpp"], default="auto")
    parser.add_argument("--allow-when-source-captions-exist", action="store_true")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing draft VTT for this media file.")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def media_key(media_path: str) -> str:
    return hashlib.sha256(media_path.encode("utf-8")).hexdigest()[:24]


def caption_id(media_path: str) -> str:
    return f"generated-{hashlib.sha1(media_path.encode('utf-8')).hexdigest()[:16]}"


def ensure_under_caption_root(path: Path) -> Path:
    resolved = path.resolve()
    root = CAPTION_ROOT.resolve()
    if resolved != root and root not in resolved.parents:
        raise RuntimeError(f"Refusing caption write outside caption root: {resolved}")
    return resolved


def detect_backends() -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    faster = shutil.which("faster-whisper")
    if faster:
        candidates.append({"name": "faster-whisper", "path": faster})
    whisper = shutil.which("whisper")
    if whisper:
        candidates.append({"name": "whisper", "path": whisper})
    whisper_cpp = shutil.which("whisper-cli") or shutil.which("main")
    if whisper_cpp:
        candidates.append({"name": "whisper.cpp", "path": whisper_cpp})
    return candidates


def choose_backend(requested: str) -> dict[str, str] | None:
    backends = detect_backends()
    if requested == "auto":
        return backends[0] if backends else None
    return next((backend for backend in backends if backend["name"] == requested), None)


def manifest_has_source_captions(media_path: str) -> bool:
    key = media_key(media_path)
    manifest_path = MANIFEST_DIR / f"{key}.json"
    if not manifest_path.exists():
        return False
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    for track in manifest.get("tracks", []):
        if track.get("sourceType") in {"embedded", "external"} and track.get("sourceFormat") in SOURCE_FORMATS:
            return True
    return False


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_under_caption_root(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_command(backend: dict[str, str], args: argparse.Namespace, output_base: Path) -> list[str]:
    if backend["name"] == "whisper":
        command = [backend["path"], args.media_file, "--output_format", "vtt", "--output_dir", str(output_base.parent)]
        if args.language != "auto":
            command.extend(["--language", args.language])
        if args.model:
            command.extend(["--model", args.model])
        return command
    raise RuntimeError(f"AI_BACKEND_COMMAND_NOT_IMPLEMENTED:{backend['name']}")


def main() -> int:
    args = parse_args()
    media_path = str(Path(args.media_file).expanduser())
    if not media_path or any(token in media_path for token in ["*", "\n", "\0"]):
        print(json.dumps({"status": "NO_GO", "code": "EXPLICIT_SINGLE_MEDIA_FILE_REQUIRED"}))
        return 2
    if not Path(media_path).is_file():
        print(json.dumps({"status": "NO_GO", "code": "MEDIA_FILE_UNAVAILABLE", "mediaFile": media_path}))
        return 2

    backends = detect_backends()
    backend = choose_backend(args.backend)
    key = media_key(media_path)
    track_id = caption_id(media_path)
    output_path = ensure_under_caption_root(GENERATED_DIR / key / f"{track_id}.vtt")
    receipt_path = ensure_under_caption_root(EVIDENCE_DIR / f"caption-ai-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d-%H%M%S')}.json")
    receipt: dict[str, Any] = {
        "schema": "spiritflix-caption-ai-draft/v1",
        "generatedAt": utc_now(),
        "mediaFile": media_path,
        "mediaKey": key,
        "trackId": track_id,
        "audioStreamIndex": args.audio_stream_index,
        "languageGuess": args.language,
        "requestedBackend": args.backend,
        "availableBackends": backends,
        "outputPath": str(output_path),
        "reviewStatus": "draft",
        "warnings": [],
    }

    if manifest_has_source_captions(media_path) and not args.allow_when_source_captions_exist:
        receipt["status"] = "NO_GO"
        receipt["code"] = "SOURCE_CAPTIONS_EXIST"
        receipt["warnings"].append("Refused because source embedded/external captions already exist.")
        write_json(receipt_path, receipt)
        print(json.dumps({"status": "NO_GO", "code": "SOURCE_CAPTIONS_EXIST", "receipt": str(receipt_path)}))
        return 2
    if not backend:
        receipt["status"] = "NO_GO"
        receipt["code"] = "AI_BACKEND_UNAVAILABLE"
        write_json(receipt_path, receipt)
        print(json.dumps({"status": "NO_GO", "code": "AI_BACKEND_UNAVAILABLE", "availableBackends": backends, "receipt": str(receipt_path)}))
        return 2
    if output_path.exists() and not args.force:
        receipt["status"] = "NO_GO"
        receipt["code"] = "DRAFT_EXISTS"
        write_json(receipt_path, receipt)
        print(json.dumps({"status": "NO_GO", "code": "DRAFT_EXISTS", "receipt": str(receipt_path)}))
        return 2
    if args.dry_run:
        receipt["status"] = "ok"
        receipt["dryRun"] = True
        write_json(receipt_path, receipt)
        print(json.dumps({"status": "ok", "dryRun": True, "backend": backend, "receipt": str(receipt_path)}))
        return 0

    start = time.time()
    try:
        command = build_command(backend, args, output_path)
    except RuntimeError as error:
        receipt["status"] = "NO_GO"
        receipt["code"] = str(error)
        write_json(receipt_path, receipt)
        print(json.dumps({"status": "NO_GO", "code": str(error), "receipt": str(receipt_path)}))
        return 2

    receipt["backend"] = backend
    receipt["command"] = command
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(command, check=False, capture_output=True, text=True, timeout=3600)
    receipt["durationSeconds"] = round(time.time() - start, 3)
    receipt["returnCode"] = result.returncode
    receipt["stderr"] = result.stderr[-4000:]
    receipt["stdout"] = result.stdout[-4000:]
    if result.returncode != 0:
        receipt["status"] = "NO_GO"
        receipt["code"] = "AI_BACKEND_FAILED"
        write_json(receipt_path, receipt)
        print(json.dumps({"status": "NO_GO", "code": "AI_BACKEND_FAILED", "receipt": str(receipt_path)}))
        return 1

    produced = sorted(output_path.parent.glob("*.vtt"), key=lambda path: path.stat().st_mtime, reverse=True)
    if produced and produced[0] != output_path:
        if output_path.exists() and not args.force:
            receipt["status"] = "NO_GO"
            receipt["code"] = "DRAFT_EXISTS_AFTER_BACKEND"
            write_json(receipt_path, receipt)
            return 1
        produced[0].replace(output_path)
    if not output_path.exists() or output_path.stat().st_size == 0:
        receipt["status"] = "NO_GO"
        receipt["code"] = "AI_OUTPUT_MISSING"
        write_json(receipt_path, receipt)
        print(json.dumps({"status": "NO_GO", "code": "AI_OUTPUT_MISSING", "receipt": str(receipt_path)}))
        return 1

    manifest = {
        "mediaPath": media_path,
        "mediaKey": key,
        "generatedAt": utc_now(),
        "tracks": [
            {
                "id": track_id,
                "sourceType": "generated",
                "sourceFormat": "unknown",
                "outputFormat": "vtt",
                "language": None if args.language == "auto" else args.language,
                "label": "AI Draft Captions",
                "kind": "captions",
                "default": False,
                "forced": False,
                "sdh": False,
                "cachePath": str(output_path),
                "publicUrl": f"/api/spiritflix/captions/file?key={key}&track={track_id}",
                "generatedBy": backend["name"],
                "reviewStatus": "draft",
            }
        ],
    }
    write_json(MANIFEST_DIR / f"{key}.json", manifest)
    receipt["status"] = "ok"
    receipt["manifestPath"] = str(MANIFEST_DIR / f"{key}.json")
    write_json(receipt_path, receipt)
    print(json.dumps({"status": "ok", "output": str(output_path), "manifest": receipt["manifestPath"], "receipt": str(receipt_path)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
