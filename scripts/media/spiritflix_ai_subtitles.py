#!/usr/bin/env python3
"""Generate local AI draft subtitles for SpiritFlix videos.

Writes only caption artifacts under:
  /mnt/spirit-8tb/media/.spiritflix-admin/captions/

The script is intentionally direct: pick media, extract a temporary 16 kHz mono
WAV, run a local ASR backend, write WebVTT, merge a generated draft track into
the existing SpiritFlix caption manifest, and write receipts.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import venv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


MEDIA_ROOT = Path("/mnt/spirit-8tb/media")
CAPTION_ROOT = MEDIA_ROOT / ".spiritflix-admin" / "captions"
GENERATED_DIR = CAPTION_ROOT / "generated"
MANIFEST_DIR = CAPTION_ROOT / "manifests"
TMP_DIR = CAPTION_ROOT / "tmp"
RECEIPT_DIR = CAPTION_ROOT / "evidence" / "ai-subtitles"
QC_DIR = CAPTION_ROOT / "evidence" / "caption-qc"
VENV_DIR = CAPTION_ROOT / "venv"
REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_EVIDENCE_DIR = REPO_ROOT / "docs" / "evidence"

VIDEO_EXTENSIONS = {".mp4", ".m4v", ".mkv", ".mov", ".avi", ".webm", ".wmv"}
LANGUAGE_NAMES = {
    "auto": "Auto",
    "en": "English",
    "eng": "English",
    "ja": "Japanese",
    "jpn": "Japanese",
    "es": "Spanish",
    "spa": "Spanish",
    "fr": "French",
    "fra": "French",
    "fre": "French",
    "de": "German",
    "deu": "German",
    "ger": "German",
}
JUNK_TEXT = {
    "",
    ".",
    "...",
    "♪",
    "[music]",
    "(music)",
    "[silence]",
    "(silence)",
    "[applause]",
}
ASR_INITIAL_PROMPT = (
    "Transcribe the English dub verbatim. Do not translate, summarize, paraphrase, "
    "or describe the scene. Preserve spoken words and punctuation when available."
)
PROVENANCE_EMBEDDED_EXTRACTED = "embedded-extracted"
PROVENANCE_AI_WORD_TIMED = "ai-asr-word-timed"
PROVENANCE_AI_SEGMENT_TIMED = "ai-asr-segment-timed"
PROVENANCE_FALLBACK = "fallback"


@dataclass
class Backend:
    name: str
    runner: str
    python: str | None = None
    path: str | None = None
    installed: bool = False

    @property
    def label(self) -> str:
        return self.name


@dataclass
class Word:
    start: float
    end: float
    text: str
    probability: float | None = None


@dataclass
class Segment:
    start: float
    end: float
    text: str
    words: list[Word] = field(default_factory=list)


@dataclass
class SpeechSpan:
    start: float
    end: float


@dataclass
class TimingConfig:
    timing_mode: str
    max_lead_ms: int
    max_linger_ms: int
    split_silence_ms: int
    min_cue_ms: int
    max_cue_ms: int
    global_offset_ms: int
    silence_noise_db: int
    max_line_chars: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate local AI draft WebVTT subtitles for SpiritFlix.")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--file", help="One explicit media file to caption.")
    scope.add_argument("--root", help="Root folder to scan for videos.")
    parser.add_argument("--limit", type=int, help="Maximum videos to process in --root mode.")
    parser.add_argument("--confirm-large-batch", action="store_true", help="Allow --root without --limit.")
    parser.add_argument("--model", default="base", help="Local ASR model name/path. Defaults to base.")
    parser.add_argument("--language", default="en", help="Language hint, or auto.")
    parser.add_argument("--force", action="store_true", help="Regenerate and replace existing generated AI caption track.")
    parser.add_argument("--skip-existing", action="store_true", help="Skip videos with an existing generated AI caption track.")
    parser.add_argument("--audio-stream", help="Explicit ffmpeg audio stream map, stream index, or 0:a:N selector.")
    parser.add_argument("--dry-run", action="store_true", help="Plan work without extracting audio, generating VTT, or writing manifests.")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary extracted audio.")
    parser.add_argument("--detect-only", action="store_true", help="Only detect/install a local backend and print JSON.")
    parser.add_argument("--no-install", action="store_true", help="Do not create the caption venv or install faster-whisper.")
    parser.add_argument("--backend", choices=["auto", "faster-whisper", "whisper", "whisper-cli", "whisper.cpp"], default="auto")
    parser.add_argument("--verify-vtt", help="Run subtitle QC only against this VTT and --file audio; do not run ASR or write a manifest.")
    parser.set_defaults(prefer_embedded_english=env_bool("AI_SUBTITLE_PREFER_EMBEDDED_ENGLISH", True))
    parser.add_argument(
        "--prefer-embedded-english",
        dest="prefer_embedded_english",
        action="store_true",
        help="Prefer an existing full embedded/external English subtitle track instead of generating AI captions.",
    )
    parser.add_argument(
        "--no-prefer-embedded-english",
        dest="prefer_embedded_english",
        action="store_false",
        help="Explicitly allow AI generation even when a full English source subtitle track exists.",
    )
    parser.add_argument("--timing-mode", default=os.environ.get("AI_SUBTITLE_TIMING_MODE", "word_vad_clamp"))
    parser.add_argument("--max-lead-ms", type=int, default=env_int("AI_SUBTITLE_MAX_LEAD_MS", 150))
    parser.add_argument("--max-linger-ms", type=int, default=env_int("AI_SUBTITLE_MAX_LINGER_MS", 350))
    parser.add_argument("--split-silence-ms", type=int, default=env_int("AI_SUBTITLE_SPLIT_SILENCE_MS", 700))
    parser.add_argument("--min-cue-ms", type=int, default=env_int("AI_SUBTITLE_MIN_CUE_MS", 600))
    parser.add_argument("--max-cue-ms", type=int, default=env_int("AI_SUBTITLE_MAX_CUE_MS", 6000))
    parser.add_argument("--global-offset-ms", type=int, default=env_int("AI_SUBTITLE_GLOBAL_OFFSET_MS", 0))
    parser.add_argument("--silence-noise-db", type=int, default=env_int("AI_SUBTITLE_SILENCE_NOISE_DB", -35))
    parser.add_argument("--max-line-chars", type=int, default=env_int("AI_SUBTITLE_MAX_LINE_CHARS", 42))
    return parser.parse_args()


def env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


def timing_config_from_args(args: argparse.Namespace) -> TimingConfig:
    return TimingConfig(
        timing_mode=str(args.timing_mode or "word_vad_clamp"),
        max_lead_ms=max(0, int(args.max_lead_ms)),
        max_linger_ms=max(0, int(args.max_linger_ms)),
        split_silence_ms=max(100, int(args.split_silence_ms)),
        min_cue_ms=max(100, int(args.min_cue_ms)),
        max_cue_ms=max(500, int(args.max_cue_ms)),
        global_offset_ms=int(args.global_offset_ms),
        silence_noise_db=int(args.silence_noise_db),
        max_line_chars=max(24, int(args.max_line_chars)),
    )


def timing_config_to_dict(config: TimingConfig) -> dict[str, Any]:
    return {
        "timingMode": config.timing_mode,
        "maxLeadMs": config.max_lead_ms,
        "maxLingerMs": config.max_linger_ms,
        "splitSilenceMs": config.split_silence_ms,
        "minCueMs": config.min_cue_ms,
        "maxCueMs": config.max_cue_ms,
        "globalOffsetMs": config.global_offset_ms,
        "silenceNoiseDb": config.silence_noise_db,
        "maxLineChars": config.max_line_chars,
    }


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")


def media_key(media_path: str) -> str:
    return hashlib.sha256(media_path.encode("utf-8")).hexdigest()[:24]


def normalize_media_path(value: str) -> str:
    normalized = value.replace("\\", "/")
    if normalized.startswith("/media/"):
        return f"/mnt/spirit-8tb/media/{normalized.removeprefix('/media/')}"
    return str(Path(normalized).expanduser())


def safe_language(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "-", (value or "auto").strip().lower()).strip("-")
    return cleaned or "auto"


def language_label(value: str) -> str:
    key = safe_language(value)
    return LANGUAGE_NAMES.get(key, key.upper() if len(key) <= 3 else key.title())


def ensure_under_root(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    resolved_root = root.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise RuntimeError(f"Refusing write outside {resolved_root}: {resolved}")
    return resolved


def ensure_under_caption_root(path: Path) -> Path:
    return ensure_under_root(path, CAPTION_ROOT)


def write_json(path: Path, payload: dict[str, Any], *, caption_root_only: bool = True) -> None:
    if caption_root_only:
        ensure_under_caption_root(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_command(command: list[str], *, timeout: int = 3600, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout, env=env)


def module_available(python_exe: str, module: str) -> bool:
    result = run_command([python_exe, "-c", f"import {module}"], timeout=20)
    return result.returncode == 0


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def detect_backends() -> list[Backend]:
    backends: list[Backend] = []
    python_candidates = [sys.executable]
    venv_py = venv_python()
    if venv_py.exists():
        python_candidates.insert(0, str(venv_py))

    seen_python: set[str] = set()
    for python_exe in python_candidates:
        if not python_exe or python_exe in seen_python:
            continue
        seen_python.add(python_exe)
        if module_available(python_exe, "faster_whisper"):
            backends.append(Backend(name="faster-whisper", runner="python-module", python=python_exe))
        if module_available(python_exe, "whisper"):
            backends.append(Backend(name="whisper", runner="python-module", python=python_exe))

    whisper_cli = shutil.which("whisper")
    if whisper_cli:
        backends.append(Backend(name="whisper-cli", runner="cli", path=whisper_cli))
    whisper_cpp = shutil.which("whisper-cli") or shutil.which("main")
    if whisper_cpp and whisper_cpp != whisper_cli:
        backends.append(Backend(name="whisper.cpp", runner="cli", path=whisper_cpp))
    return backends


def install_faster_whisper() -> tuple[Backend | None, dict[str, Any]]:
    install_receipt: dict[str, Any] = {
        "venv": str(VENV_DIR),
        "attempted": True,
        "commands": [],
    }
    try:
        VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
        if not venv_python().exists():
            venv.EnvBuilder(with_pip=True, clear=False).create(VENV_DIR)
        python_exe = str(venv_python())
        pip_command = [python_exe, "-m", "pip", "install", "--upgrade", "faster-whisper"]
        install_receipt["commands"].append(pip_command)
        result = run_command(pip_command, timeout=1800)
        install_receipt["returnCode"] = result.returncode
        install_receipt["stdout"] = result.stdout[-8000:]
        install_receipt["stderr"] = result.stderr[-8000:]
        if result.returncode == 0 and module_available(python_exe, "faster_whisper"):
            return Backend(name="faster-whisper", runner="python-module", python=python_exe, installed=True), install_receipt
        return None, install_receipt
    except Exception as error:  # noqa: BLE001 - receipt should preserve the exact blocker.
        install_receipt["error"] = repr(error)
        return None, install_receipt


def choose_backend(requested: str, allow_install: bool) -> tuple[Backend | None, list[Backend], dict[str, Any] | None]:
    available = detect_backends()
    candidates = available
    if requested != "auto":
        aliases = {"whisper.cpp": {"whisper.cpp"}, "whisper-cli": {"whisper-cli", "whisper"}}
        allowed = aliases.get(requested, {requested})
        candidates = [backend for backend in available if backend.name in allowed]
    if candidates:
        return candidates[0], available, None
    if allow_install and requested in {"auto", "faster-whisper"}:
        installed, install_receipt = install_faster_whisper()
        available_after = detect_backends()
        if installed:
            return installed, available_after, install_receipt
        return None, available_after, install_receipt
    return None, available, None


def backend_to_dict(backend: Backend) -> dict[str, Any]:
    return {
        "name": backend.name,
        "runner": backend.runner,
        "python": backend.python,
        "path": backend.path,
        "installed": backend.installed,
    }


def ffprobe_media(media_path: str) -> dict[str, Any]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("FFPROBE_UNAVAILABLE")
    command = [
        ffprobe,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        media_path,
    ]
    result = run_command(command, timeout=120)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or f"ffprobe exited {result.returncode}").strip())
    return json.loads(result.stdout)


def audio_match_text(stream: dict[str, Any]) -> str:
    tags = stream.get("tags") if isinstance(stream.get("tags"), dict) else {}
    values = [
        stream.get("codec_name"),
        tags.get("language"),
        tags.get("title"),
        tags.get("handler_name"),
    ]
    return " ".join(str(value) for value in values if value).lower()


def select_audio_stream(media_path: str, requested: str | None) -> dict[str, Any]:
    probe = ffprobe_media(media_path)
    streams = [stream for stream in probe.get("streams", []) if stream.get("codec_type") == "audio"]
    if requested:
        requested_text = str(requested)
        if requested_text.isdigit():
            index = int(requested_text)
            matched = next((stream for stream in streams if int(stream.get("index", -1)) == index), None)
            return {
                "map": f"0:{index}",
                "index": index,
                "requested": requested_text,
                "detected": matched,
            }
        return {
            "map": requested_text,
            "index": None,
            "requested": requested_text,
            "detected": None,
        }

    english = next((stream for stream in streams if re.search(r"\b(en|eng|english)\b", audio_match_text(stream))), None)
    selected = english or (streams[0] if streams else None)
    if not selected:
        raise RuntimeError("NO_AUDIO_STREAMS")
    index = int(selected.get("index"))
    return {
        "map": f"0:{index}",
        "index": index,
        "requested": None,
        "detected": selected,
        "reason": "english_audio" if english else "first_audio",
    }


def extract_audio(media_path: str, audio_selection: dict[str, Any], output_path: Path, force: bool) -> dict[str, Any]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("FFMPEG_UNAVAILABLE")
    output_path = ensure_under_caption_root(output_path)
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
        str(audio_selection["map"]),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    result = run_command(command, timeout=1800)
    return {
        "command": command,
        "returnCode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
        "outputPath": str(output_path),
    }


def seconds_to_vtt(value: float) -> str:
    value = max(0.0, float(value))
    total_ms = int(round(value * 1000))
    hours, remainder = divmod(total_ms, 3600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, ms = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{ms:03d}"


def parse_vtt_time(value: str) -> float | None:
    match = re.match(r"(?:(\d+):)?(\d{2}):(\d{2})[.,](\d{3})", value.strip())
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    millis = int(match.group(4))
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def clean_segment_text(value: str) -> str:
    text = re.sub(r"\s+", " ", value.replace("\u200b", " ")).strip()
    text = re.sub(r"^(?:[-\s.])+", "", text).strip()
    return text


def sanitize_segments(raw_segments: Iterable[Segment]) -> list[Segment]:
    clean: list[Segment] = []
    previous_text = ""
    previous_end = 0.0
    repeated_count = 0
    for segment in sorted(raw_segments, key=lambda item: (item.start, item.end)):
        start = max(0.0, float(segment.start))
        end = max(0.0, float(segment.end))
        text = clean_segment_text(segment.text)
        if text.lower() in JUNK_TEXT:
            continue
        if end <= start:
            continue
        if text == previous_text:
            repeated_count += 1
            if repeated_count >= 2:
                continue
        else:
            repeated_count = 0
        if clean and start < previous_end:
            start = previous_end
            if end <= start:
                end = start + 0.2
        words = [
            word
            for word in segment.words
            if word.end > word.start and word.end >= segment.start - 0.25 and word.start <= segment.end + 0.25 and clean_segment_text(word.text)
        ]
        clean.append(Segment(start=start, end=end, text=text, words=words))
        previous_text = text
        previous_end = end
    return clean


def wrap_caption_text(text: str, max_line_chars: int = 42) -> str:
    cleaned = clean_segment_text(text)
    if len(cleaned) <= max_line_chars:
        return cleaned
    words = cleaned.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_line_chars:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    if len(lines) <= 2:
        return "\n".join(lines)
    midpoint = max(1, math.ceil(len(words) / 2))
    return "\n".join([" ".join(words[:midpoint]), " ".join(words[midpoint:])])


def write_vtt(path: Path, segments: list[Segment], config: TimingConfig | None = None) -> None:
    path = ensure_under_caption_root(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["WEBVTT", ""]
    for index, segment in enumerate(segments, start=1):
        lines.append(str(index))
        lines.append(f"{seconds_to_vtt(segment.start)} --> {seconds_to_vtt(segment.end)}")
        text = wrap_caption_text(segment.text, config.max_line_chars if config else 42)
        lines.extend(text.splitlines() or [text])
        lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def read_segments_json(path: Path) -> list[Segment]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    segments = payload.get("segments", payload)
    output: list[Segment] = []
    for segment in segments:
        words: list[Word] = []
        for raw_word in segment.get("words") or []:
            try:
                word_start = float(raw_word.get("start"))
                word_end = float(raw_word.get("end"))
            except (TypeError, ValueError):
                continue
            if word_end <= word_start:
                continue
            probability = raw_word.get("probability")
            words.append(
                Word(
                    start=word_start,
                    end=word_end,
                    text=str(raw_word.get("word") or raw_word.get("text") or ""),
                    probability=float(probability) if isinstance(probability, (int, float)) else None,
                )
            )
        output.append(Segment(start=float(segment["start"]), end=float(segment["end"]), text=str(segment.get("text", "")), words=words))
    return output


def transcribe_faster_whisper(backend: Backend, audio_path: Path, model: str, language: str, output_json: Path) -> dict[str, Any]:
    script = r"""
import json
import sys
from faster_whisper import WhisperModel

audio_path, model_name, language, output_json, initial_prompt = sys.argv[1:6]
model = WhisperModel(model_name, device="cpu", compute_type="int8")
segments, info = model.transcribe(
    audio_path,
    language=None if language == "auto" else language,
    vad_filter=True,
    word_timestamps=True,
    condition_on_previous_text=False,
    initial_prompt=initial_prompt,
    temperature=0.0,
)
payload = {
    "language": getattr(info, "language", None),
    "duration": getattr(info, "duration", None),
    "wordTimestamps": True,
    "segments": [
        {
            "start": s.start,
            "end": s.end,
            "text": s.text,
            "words": [
                {
                    "start": getattr(w, "start", None),
                    "end": getattr(w, "end", None),
                    "word": getattr(w, "word", ""),
                    "probability": getattr(w, "probability", None),
                }
                for w in (getattr(s, "words", None) or [])
            ],
        }
        for s in segments
    ],
}
with open(output_json, "w", encoding="utf-8") as handle:
    json.dump(payload, handle)
"""
    command = [backend.python or sys.executable, "-c", script, str(audio_path), model, safe_language(language), str(output_json), ASR_INITIAL_PROMPT]
    result = run_command(command, timeout=7200)
    return {"command": command, "returnCode": result.returncode, "stdout": result.stdout[-4000:], "stderr": result.stderr[-8000:]}


def transcribe_whisper_module(backend: Backend, audio_path: Path, model: str, language: str, output_json: Path) -> dict[str, Any]:
    script = r"""
import json
import sys
import whisper

audio_path, model_name, language, output_json, initial_prompt = sys.argv[1:6]
model = whisper.load_model(model_name)
kwargs = {
    "language": None if language == "auto" else language,
    "word_timestamps": True,
    "condition_on_previous_text": False,
    "initial_prompt": initial_prompt,
    "fp16": False,
}
try:
    result = model.transcribe(audio_path, **kwargs)
except TypeError:
    kwargs.pop("word_timestamps", None)
    result = model.transcribe(audio_path, **kwargs)
payload = {
    "language": result.get("language"),
    "wordTimestamps": any(s.get("words") for s in result.get("segments", [])),
    "segments": [
        {
            "start": s.get("start"),
            "end": s.get("end"),
            "text": s.get("text", ""),
            "words": [
                {
                    "start": w.get("start"),
                    "end": w.get("end"),
                    "word": w.get("word", ""),
                    "probability": w.get("probability"),
                }
                for w in (s.get("words") or [])
            ],
        }
        for s in result.get("segments", [])
    ],
}
with open(output_json, "w", encoding="utf-8") as handle:
    json.dump(payload, handle)
"""
    command = [backend.python or sys.executable, "-c", script, str(audio_path), model, safe_language(language), str(output_json), ASR_INITIAL_PROMPT]
    result = run_command(command, timeout=7200)
    return {"command": command, "returnCode": result.returncode, "stdout": result.stdout[-4000:], "stderr": result.stderr[-8000:]}


def transcribe_whisper_cli(backend: Backend, audio_path: Path, model: str, language: str, temp_dir: Path) -> tuple[dict[str, Any], Path | None]:
    command = [
        backend.path or "whisper",
        str(audio_path),
        "--model",
        model,
        "--output_format",
        "vtt",
        "--output_dir",
        str(temp_dir),
    ]
    if safe_language(language) != "auto":
        command.extend(["--language", safe_language(language)])
    result = run_command(command, timeout=7200)
    newest = None
    produced = sorted(temp_dir.glob("*.vtt"), key=lambda item: item.stat().st_mtime, reverse=True)
    if produced:
        newest = produced[0]
    return {"command": command, "returnCode": result.returncode, "stdout": result.stdout[-4000:], "stderr": result.stderr[-8000:]}, newest


def transcribe_whisper_cpp(backend: Backend, audio_path: Path, model: str, language: str, temp_dir: Path) -> tuple[dict[str, Any], Path | None]:
    model_path = Path(model).expanduser()
    if not model_path.exists():
        return {
            "command": [],
            "returnCode": 2,
            "stdout": "",
            "stderr": "whisper.cpp requires --model to be a local model file path.",
        }, None
    output_base = temp_dir / "whisper-cpp"
    command = [
        backend.path or "whisper-cli",
        "-m",
        str(model_path),
        "-f",
        str(audio_path),
        "-ovtt",
        "-of",
        str(output_base),
    ]
    if safe_language(language) != "auto":
        command.extend(["-l", safe_language(language)])
    result = run_command(command, timeout=7200)
    produced = output_base.with_suffix(".vtt")
    return {"command": command, "returnCode": result.returncode, "stdout": result.stdout[-4000:], "stderr": result.stderr[-8000:]}, produced if produced.exists() else None


def parse_vtt_segments(path: Path) -> list[Segment]:
    text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    segments: list[Segment] = []
    for block in text.split("\n\n"):
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        timing_index = next((index for index, line in enumerate(lines) if "-->" in line), -1)
        if timing_index < 0:
            continue
        left, right = [part.strip().split()[0] for part in lines[timing_index].split("-->", 1)]
        start = parse_vtt_time(left)
        end = parse_vtt_time(right)
        if start is None or end is None:
            continue
        text_lines = lines[timing_index + 1 :]
        segments.append(Segment(start=start, end=end, text=" ".join(text_lines)))
    return segments


def ffprobe_duration_seconds(media_path: Path) -> float | None:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None
    result = run_command(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(media_path)],
        timeout=60,
    )
    if result.returncode != 0:
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def detect_speech_spans(audio_path: Path, config: TimingConfig) -> tuple[list[SpeechSpan], dict[str, Any]]:
    ffmpeg = shutil.which("ffmpeg")
    duration = ffprobe_duration_seconds(audio_path)
    receipt: dict[str, Any] = {
        "method": "ffmpeg-silencedetect",
        "noiseDb": config.silence_noise_db,
        "minSilenceMs": config.split_silence_ms,
        "audioPath": str(audio_path),
        "audioDurationSeconds": round(duration, 3) if duration is not None else None,
    }
    if not ffmpeg:
        receipt.update({"status": "unavailable", "error": "FFMPEG_UNAVAILABLE"})
        return [], receipt
    if duration is None or duration <= 0:
        receipt.update({"status": "unavailable", "error": "AUDIO_DURATION_UNAVAILABLE"})
        return [], receipt

    command = [
        ffmpeg,
        "-hide_banner",
        "-nostdin",
        "-i",
        str(audio_path),
        "-af",
        f"silencedetect=noise={config.silence_noise_db}dB:d={config.split_silence_ms / 1000:.3f}",
        "-f",
        "null",
        "-",
    ]
    result = run_command(command, timeout=1800)
    receipt["command"] = command
    receipt["returnCode"] = result.returncode
    receipt["stderrTail"] = result.stderr[-4000:]
    if result.returncode != 0:
        receipt.update({"status": "failed", "error": result.stderr[-1000:] or result.stdout[-1000:]})
        return [], receipt

    silences: list[tuple[float, float]] = []
    current_start: float | None = None
    for line in (result.stderr + "\n" + result.stdout).splitlines():
        start_match = re.search(r"silence_start:\s*([0-9.]+)", line)
        if start_match:
            current_start = float(start_match.group(1))
            continue
        end_match = re.search(r"silence_end:\s*([0-9.]+)", line)
        if end_match and current_start is not None:
            silence_end = float(end_match.group(1))
            if silence_end > current_start:
                silences.append((current_start, silence_end))
            current_start = None
    if current_start is not None and duration > current_start:
        silences.append((current_start, duration))

    spans: list[SpeechSpan] = []
    cursor = 0.0
    for silence_start, silence_end in sorted(silences):
        if silence_start - cursor > 0.05:
            spans.append(SpeechSpan(start=cursor, end=silence_start))
        cursor = max(cursor, silence_end)
    if duration - cursor > 0.05:
        spans.append(SpeechSpan(start=cursor, end=duration))
    if not silences:
        spans = [SpeechSpan(start=0.0, end=duration)]

    speech_duration = sum(max(0.0, span.end - span.start) for span in spans)
    receipt.update(
        {
            "status": "ok",
            "silenceCount": len(silences),
            "speechSpanCount": len(spans),
            "speechDurationSeconds": round(speech_duration, 3),
            "firstSpeechStartSeconds": round(spans[0].start, 3) if spans else None,
            "lastSpeechEndSeconds": round(spans[-1].end, 3) if spans else None,
        }
    )
    return spans, receipt


def segments_have_word_timestamps(segments: Iterable[Segment]) -> bool:
    return any(any(word.end > word.start for word in segment.words) for segment in segments)


def words_to_text(words: list[Word]) -> str:
    joined = "".join(word.text for word in words).strip()
    if joined:
        return clean_segment_text(joined)
    return clean_segment_text(" ".join(word.text for word in words))


def split_words_by_timing(words: list[Word], config: TimingConfig) -> list[list[Word]]:
    valid_words = sorted((word for word in words if word.end > word.start), key=lambda word: (word.start, word.end))
    if not valid_words:
        return []
    chunks: list[list[Word]] = []
    current: list[Word] = []
    max_duration = config.max_cue_ms / 1000
    split_gap = config.split_silence_ms / 1000
    for word in valid_words:
        if current:
            gap = word.start - current[-1].end
            would_be_too_long = word.end - current[0].start > max_duration
            if gap >= split_gap or would_be_too_long:
                chunks.append(current)
                current = []
        current.append(word)
    if current:
        chunks.append(current)
    return chunks


def split_text_by_weights(text: str, weights: list[float]) -> list[str]:
    words = clean_segment_text(text).split()
    if not weights:
        return [clean_segment_text(text)]
    if len(weights) == 1 or len(words) <= 1:
        return [clean_segment_text(text) for _ in weights]
    total = sum(weight for weight in weights if weight > 0) or float(len(weights))
    pieces: list[str] = []
    cursor = 0
    for index, weight in enumerate(weights):
        remaining_words = len(words) - cursor
        remaining_pieces = len(weights) - index
        if remaining_pieces <= 1:
            count = remaining_words
        else:
            count = max(1, round(len(words) * max(weight, 0.0) / total))
            count = min(count, remaining_words - (remaining_pieces - 1))
        pieces.append(" ".join(words[cursor : cursor + count]).strip())
        cursor += count
    return [piece or clean_segment_text(text) for piece in pieces]


def overlapping_speech_spans(spans: list[SpeechSpan], start: float, end: float) -> list[SpeechSpan]:
    return [span for span in spans if span.end > start and span.start < end]


def clamp_interval_to_speech(
    start: float,
    end: float,
    speech_spans: list[SpeechSpan],
    config: TimingConfig,
) -> tuple[float, float, bool, bool]:
    if "vad" not in config.timing_mode:
        return start, end, False, False
    overlaps = overlapping_speech_spans(speech_spans, start, end)
    if not overlaps:
        return start, end, False, False
    max_linger = config.max_linger_ms / 1000
    first_speech = min(span.start for span in overlaps)
    last_speech = max(span.end for span in overlaps)
    clamped_start = max(0.0, max(start, first_speech))
    clamped_end = min(end, last_speech + max(0.0, max_linger - 0.02))
    if clamped_end <= clamped_start:
        clamped_end = max(clamped_start + 0.05, min(end, last_speech))
    return clamped_start, clamped_end, clamped_start != start, clamped_end != end


def split_long_segment(segment: Segment, config: TimingConfig) -> list[Segment]:
    duration = segment.end - segment.start
    max_duration = config.max_cue_ms / 1000
    if duration <= max_duration or max_duration <= 0:
        return [segment]
    count = max(1, math.ceil(duration / max_duration))
    pieces = split_text_by_weights(segment.text, [1.0] * count)
    output: list[Segment] = []
    cursor = segment.start
    for index, piece in enumerate(pieces):
        next_end = segment.end if index == len(pieces) - 1 else min(segment.end, cursor + max_duration)
        output.append(Segment(start=cursor, end=next_end, text=piece))
        cursor = next_end
    return output


def normalize_repaired_segments(
    segments: list[Segment],
    config: TimingConfig,
    report: dict[str, Any],
    speech_spans: list[SpeechSpan] | None = None,
) -> list[Segment]:
    normalized: list[Segment] = []
    for segment in sorted(segments, key=lambda item: (item.start, item.end)):
        for piece in split_long_segment(segment, config):
            text = clean_segment_text(piece.text)
            if text.lower() in JUNK_TEXT:
                report["emptyOrJunkCueRemovedCount"] += 1
                continue
            start = max(0.0, piece.start)
            end = max(0.0, piece.end)
            if normalized and start < normalized[-1].end:
                report["overlapAdjustedCount"] += 1
                start = normalized[-1].end
            if end <= start:
                report["emptyOrJunkCueRemovedCount"] += 1
                continue
            if speech_spans and "vad" in config.timing_mode:
                if not overlapping_speech_spans(speech_spans, start, end):
                    report["noSpeechCueDroppedCount"] += 1
                    continue
                start, end, start_changed, end_changed = clamp_interval_to_speech(start, end, speech_spans, config)
                if start_changed:
                    report["startClampedCount"] += 1
                if end_changed:
                    report["endClampedCount"] += 1
                if end <= start:
                    report["emptyOrJunkCueRemovedCount"] += 1
                    continue
            normalized.append(Segment(start=start, end=end, text=text))
    return normalized


def repair_segments(raw_segments: list[Segment], speech_spans: list[SpeechSpan], config: TimingConfig) -> tuple[list[Segment], dict[str, Any]]:
    report: dict[str, Any] = {
        "timingMode": config.timing_mode,
        "inputCueCount": len(raw_segments),
        "outputCueCount": 0,
        "wordTimedInputCueCount": 0,
        "segmentFallbackInputCueCount": 0,
        "splitCueCount": 0,
        "startClampedCount": 0,
        "endClampedCount": 0,
        "overlapAdjustedCount": 0,
        "emptyOrJunkCueRemovedCount": 0,
        "noSpeechCueDroppedCount": 0,
    }
    repaired: list[Segment] = []
    offset = config.global_offset_ms / 1000
    max_linger = config.max_linger_ms / 1000
    min_duration = config.min_cue_ms / 1000

    def append_clamped(start: float, end: float, text: str) -> None:
        if end - start < min_duration:
            end = min(start + min_duration, end + max_linger)
        clamped_start, clamped_end, start_changed, end_changed = clamp_interval_to_speech(start, end, speech_spans, config)
        if start_changed:
            report["startClampedCount"] += 1
        if end_changed:
            report["endClampedCount"] += 1
        repaired.append(Segment(start=clamped_start, end=clamped_end, text=text))

    def add_candidate(start: float, end: float, text: str) -> None:
        if "vad" in config.timing_mode and speech_spans:
            overlaps = overlapping_speech_spans(speech_spans, start, end)
            if not overlaps:
                report["noSpeechCueDroppedCount"] += 1
                return
            split_gap = config.split_silence_ms / 1000
            has_long_internal_gap = any(max(0.0, right.start - left.end) >= split_gap for left, right in zip(overlaps, overlaps[1:], strict=False))
            if len(overlaps) > 1 and has_long_internal_gap:
                report["splitCueCount"] += len(overlaps) - 1
                text_pieces = split_text_by_weights(text, [span.end - span.start for span in overlaps])
                for span, cue_text in zip(overlaps, text_pieces, strict=False):
                    append_clamped(max(start, span.start), min(end, span.end + max_linger), cue_text)
                return
        append_clamped(start, end, text)

    for segment in raw_segments:
        text = clean_segment_text(segment.text)
        if not text or text.lower() in JUNK_TEXT:
            report["emptyOrJunkCueRemovedCount"] += 1
            continue

        if "word" in config.timing_mode and segment.words:
            word_chunks = split_words_by_timing(segment.words, config)
        else:
            word_chunks = []

        if word_chunks:
            report["wordTimedInputCueCount"] += 1
            if len(word_chunks) > 1:
                report["splitCueCount"] += len(word_chunks) - 1
            for chunk in word_chunks:
                first_word = chunk[0].start + offset
                last_word = chunk[-1].end + offset
                cue_text = text if len(word_chunks) == 1 else words_to_text(chunk)
                add_candidate(max(0.0, first_word), max(first_word + 0.05, last_word + max_linger), cue_text)
            continue

        report["segmentFallbackInputCueCount"] += 1
        start = max(0.0, segment.start + offset)
        end = max(start + 0.05, segment.end + offset)
        overlaps = overlapping_speech_spans(speech_spans, start, end) if "vad" in config.timing_mode else []
        if len(overlaps) > 1:
            report["splitCueCount"] += len(overlaps) - 1
            text_pieces = split_text_by_weights(text, [span.end - span.start for span in overlaps])
            for span, cue_text in zip(overlaps, text_pieces, strict=False):
                add_candidate(max(start, span.start), min(end, span.end + max_linger), cue_text)
        elif len(overlaps) == 1:
            span = overlaps[0]
            add_candidate(max(start, span.start), min(end, span.end + max_linger), text)
        else:
            add_candidate(start, end, text)

    normalized = normalize_repaired_segments(repaired, config, report, speech_spans)
    report["outputCueCount"] = len(normalized)
    return normalized, report


def transcribe_audio(backend: Backend, audio_path: Path, model: str, language: str, temp_dir: Path) -> tuple[list[Segment], dict[str, Any]]:
    segments_json = temp_dir / "segments.json"
    if backend.name == "faster-whisper":
        result = transcribe_faster_whisper(backend, audio_path, model, language, segments_json)
        if result["returnCode"] != 0:
            return [], result
        return read_segments_json(segments_json), result
    if backend.name == "whisper" and backend.runner == "python-module":
        result = transcribe_whisper_module(backend, audio_path, model, language, segments_json)
        if result["returnCode"] != 0:
            return [], result
        return read_segments_json(segments_json), result
    if backend.name == "whisper-cli":
        result, vtt_path = transcribe_whisper_cli(backend, audio_path, model, language, temp_dir)
        if result["returnCode"] != 0 or not vtt_path:
            return [], result
        return parse_vtt_segments(vtt_path), result
    if backend.name == "whisper.cpp":
        result, vtt_path = transcribe_whisper_cpp(backend, audio_path, model, language, temp_dir)
        if result["returnCode"] != 0 or not vtt_path:
            return [], result
        return parse_vtt_segments(vtt_path), result
    return [], {"returnCode": 2, "stderr": f"Unsupported backend: {backend.name}", "stdout": "", "command": []}


def internal_long_silence_count(cue: Segment, speech_spans: list[SpeechSpan], config: TimingConfig) -> int:
    overlaps = overlapping_speech_spans(speech_spans, cue.start, cue.end)
    if len(overlaps) <= 1:
        return 0
    count = 0
    split_gap = config.split_silence_ms / 1000
    for left, right in zip(overlaps, overlaps[1:], strict=False):
        gap = max(0.0, right.start - left.end)
        if gap >= split_gap:
            count += 1
    return count


def qc_segments(
    cues: list[Segment],
    *,
    starts_with_webvtt: bool = True,
    file_size_bytes: int = 0,
    speech_spans: list[SpeechSpan] | None = None,
    config: TimingConfig | None = None,
    provenance: str | None = None,
    word_timestamps_used: bool | None = None,
    english_dub_audio_source: bool | None = None,
) -> dict[str, Any]:
    config = config or TimingConfig(
        timing_mode="word_vad_clamp",
        max_lead_ms=150,
        max_linger_ms=350,
        split_silence_ms=700,
        min_cue_ms=600,
        max_cue_ms=6000,
        global_offset_ms=0,
        silence_noise_db=-35,
        max_line_chars=42,
    )
    empty = 0
    zero_duration = 0
    overlap = 0
    total_duration = 0.0
    previous_end = 0.0
    durations: list[float] = []
    gaps: list[float] = []
    starts_before_speech = 0
    ends_after_speech = 0
    long_silence_linger = 0
    no_speech_overlap = 0
    speech_spans = speech_spans or []
    for cue in cues:
        if not cue.text.strip():
            empty += 1
        if cue.end <= cue.start:
            zero_duration += 1
        if cue.start < previous_end:
            overlap += 1
        elif previous_end > 0:
            gaps.append(cue.start - previous_end)
        previous_end = max(previous_end, cue.end)
        duration = max(0.0, cue.end - cue.start)
        durations.append(duration)
        total_duration += duration
        if speech_spans:
            overlaps = overlapping_speech_spans(speech_spans, cue.start, cue.end)
            if not overlaps:
                no_speech_overlap += 1
            else:
                first_speech = min(span.start for span in overlaps)
                last_speech = max(span.end for span in overlaps)
                if cue.start < first_speech - (config.max_lead_ms / 1000):
                    starts_before_speech += 1
                if cue.end > last_speech + (config.max_linger_ms / 1000):
                    ends_after_speech += 1
                long_silence_linger += internal_long_silence_count(cue, speech_spans, config)
    long_cues = sum(1 for duration in durations if duration > config.max_cue_ms / 1000)
    avg_duration = (sum(durations) / len(durations)) if durations else 0.0
    early_percent = (starts_before_speech / len(cues) * 100) if cues else 0.0
    return {
        "startsWithWebVtt": starts_with_webvtt,
        "cueCount": len(cues),
        "totalCaptionedDurationSeconds": round(total_duration, 3),
        "averageCueDurationSeconds": round(avg_duration, 3),
        "maxCueDurationSeconds": round(max(durations), 3) if durations else 0,
        "longCueCount": long_cues,
        "firstCueTime": seconds_to_vtt(cues[0].start) if cues else None,
        "lastCueTime": seconds_to_vtt(cues[-1].end) if cues else None,
        "emptyCueCount": empty,
        "zeroDurationCueCount": zero_duration,
        "overlapCount": overlap,
        "cueGapCount": len(gaps),
        "averageCueGapSeconds": round(sum(gaps) / len(gaps), 3) if gaps else 0,
        "maxCueGapSeconds": round(max(gaps), 3) if gaps else 0,
        "longCueGapCount": sum(1 for gap in gaps if gap >= config.split_silence_ms / 1000),
        "speechCompared": bool(speech_spans),
        "startsBeforeDetectedSpeechCount": starts_before_speech,
        "endsAfterDetectedSpeechCount": ends_after_speech,
        "longSilenceLingerViolationCount": long_silence_linger,
        "cuesWithoutDetectedSpeechOverlapCount": no_speech_overlap,
        "suspiciouslyEarlyStartPercent": round(early_percent, 2),
        "wordTimestampsUsed": word_timestamps_used,
        "englishDubAudioSource": english_dub_audio_source,
        "provenance": provenance,
        "timingConfig": timing_config_to_dict(config),
        "fileSizeBytes": file_size_bytes,
    }


def qc_vtt(
    path: Path,
    *,
    speech_spans: list[SpeechSpan] | None = None,
    config: TimingConfig | None = None,
    provenance: str | None = None,
    word_timestamps_used: bool | None = None,
    english_dub_audio_source: bool | None = None,
) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    cues = parse_vtt_segments(path)
    return qc_segments(
        cues,
        starts_with_webvtt=text.startswith("WEBVTT"),
        file_size_bytes=path.stat().st_size if path.exists() else 0,
        speech_spans=speech_spans,
        config=config,
        provenance=provenance,
        word_timestamps_used=word_timestamps_used,
        english_dub_audio_source=english_dub_audio_source,
    )


def sample_cues(segments: list[Segment], limit: int = 20) -> list[dict[str, Any]]:
    return [
        {
            "index": index,
            "start": seconds_to_vtt(segment.start),
            "end": seconds_to_vtt(segment.end),
            "durationSeconds": round(segment.end - segment.start, 3),
            "text": clean_segment_text(segment.text),
        }
        for index, segment in enumerate(segments[:limit], start=1)
    ]


def load_manifest(key: str, media_path: str) -> dict[str, Any]:
    manifest_path = MANIFEST_DIR / f"{key}.json"
    if not manifest_path.exists():
        return {"mediaPath": media_path, "mediaKey": key, "generatedAt": utc_now(), "tracks": []}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"mediaPath": media_path, "mediaKey": key, "generatedAt": utc_now(), "tracks": []}
    manifest["mediaPath"] = manifest.get("mediaPath") or media_path
    manifest["mediaKey"] = manifest.get("mediaKey") or key
    manifest["tracks"] = manifest.get("tracks") if isinstance(manifest.get("tracks"), list) else []
    return manifest


def manifest_has_source_tracks(manifest: dict[str, Any]) -> bool:
    return any(track.get("sourceType") in {"embedded", "external"} for track in manifest.get("tracks", []))


def track_looks_english(track: dict[str, Any]) -> bool:
    values = [
        track.get("language"),
        track.get("label"),
        track.get("sourceFormat"),
        track.get("kind"),
    ]
    haystack = " ".join(str(value) for value in values if value).lower()
    return bool(re.search(r"\b(en|eng|english)\b", haystack))


def preferred_english_source_track(manifest: dict[str, Any]) -> dict[str, Any] | None:
    tracks = [track for track in manifest.get("tracks", []) if track.get("sourceType") in {"embedded", "external"}]
    english = [track for track in tracks if track_looks_english(track)]
    full = [track for track in english if not track.get("forced")]
    text = [track for track in full if track.get("outputFormat") == "vtt" and track.get("cachePath")]
    if text:
        return sorted(text, key=lambda track: (not bool(track.get("default")), str(track.get("label") or "")))[0]
    return None


def manifest_has_generated_track(manifest: dict[str, Any], track_id: str) -> bool:
    return any(track.get("sourceType") == "generated" and track.get("id") == track_id for track in manifest.get("tracks", []))


def selected_audio_looks_english(audio_selection: dict[str, Any]) -> bool:
    detected = audio_selection.get("detected")
    return isinstance(detected, dict) and bool(re.search(r"\b(en|eng|english)\b|dub", audio_match_text(detected)))


def generated_label(language: str, has_source_tracks: bool, audio_selection: dict[str, Any]) -> str:
    label_language = language_label(language)
    if label_language == "Auto":
        label_language = "English" if selected_audio_looks_english(audio_selection) else "Auto"
    if has_source_tracks and selected_audio_looks_english(audio_selection):
        return f"{label_language} Dub AI Captions"
    return f"{label_language} AI Captions"


def merge_generated_track(
    manifest: dict[str, Any],
    *,
    media_path: str,
    key: str,
    track_id: str,
    output_path: Path,
    language: str,
    backend: Backend,
    model: str,
    audio_selection: dict[str, Any],
    provenance: str,
    timing_config: TimingConfig,
    word_timestamps_used: bool,
    english_dub_audio_source: bool,
    force: bool,
) -> dict[str, Any]:
    existing_tracks = manifest.get("tracks", [])
    if force:
        existing_tracks = [track for track in existing_tracks if track.get("id") != track_id]
    has_source_tracks = manifest_has_source_tracks(manifest)
    public_url = f"/api/spiritflix/captions/file?key={key}&track={track_id}"
    generated_track = {
        "id": track_id,
        "sourceType": "generated",
        "sourceFormat": "ai",
        "outputFormat": "vtt",
        "language": None if safe_language(language) == "auto" else safe_language(language),
        "label": generated_label(language, has_source_tracks, audio_selection),
        "kind": "captions",
        "default": not any(track.get("default") for track in existing_tracks),
        "forced": False,
        "sdh": False,
        "generatedBy": f"{backend.name}/{model}",
        "provenance": provenance,
        "timingMode": timing_config.timing_mode,
        "wordTimestampsUsed": word_timestamps_used,
        "englishDubAudioSource": english_dub_audio_source,
        "cachePath": str(output_path),
        "publicUrl": public_url,
        "reviewStatus": "draft",
    }
    return {
        **manifest,
        "mediaPath": media_path,
        "mediaKey": key,
        "generatedAt": utc_now(),
        "tracks": [*existing_tracks, generated_track],
    }


def scan_videos(root: str) -> list[str]:
    root_path = Path(normalize_media_path(root)).expanduser()
    videos = [
        str(path)
        for path in root_path.rglob("*")
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS and not path.name.lower().endswith(".part.mp4")
    ]
    return sorted(videos, key=lambda item: (Path(item).stat().st_size, item))


def receipt_base(args: argparse.Namespace, media_path: str, key: str) -> dict[str, Any]:
    return {
        "schema": "spiritflix-ai-subtitle-generation/v1",
        "mediaPath": media_path,
        "mediaKey": key,
        "model": args.model,
        "language": args.language,
        "requestedAudioStream": args.audio_stream,
        "force": bool(args.force),
        "skipExisting": bool(args.skip_existing),
        "dryRun": bool(args.dry_run),
        "startTime": utc_now(),
        "warnings": [],
        "errors": [],
        "commands": [],
    }


def write_receipt(receipt: dict[str, Any]) -> Path:
    key = receipt.get("mediaKey", "unknown")
    receipt_path = RECEIPT_DIR / f"ai-subtitles-{stamp()}-{key}.json"
    write_json(receipt_path, receipt)
    return receipt_path


def process_media(media_path: str, args: argparse.Namespace, backend: Backend | None, available_backends: list[Backend], install_receipt: dict[str, Any] | None) -> dict[str, Any]:
    media_path = normalize_media_path(media_path)
    key = media_key(media_path)
    language_slug = safe_language(args.language)
    track_id = f"ai-{language_slug}"
    output_path = ensure_under_caption_root(GENERATED_DIR / key / f"{track_id}.vtt")
    manifest_path = ensure_under_caption_root(MANIFEST_DIR / f"{key}.json")
    config = timing_config_from_args(args)
    receipt = receipt_base(args, media_path, key)
    receipt["availableBackends"] = [backend_to_dict(item) for item in available_backends]
    receipt["installAttempt"] = install_receipt
    receipt["outputVttPath"] = str(output_path)
    receipt["manifestPath"] = str(manifest_path)
    receipt["timingConfig"] = timing_config_to_dict(config)
    receipt["preferEmbeddedEnglish"] = bool(args.prefer_embedded_english)

    started = time.time()
    try:
        if not Path(media_path).is_file():
            receipt.update({"status": "NO_GO", "skippedReason": "MEDIA_FILE_UNAVAILABLE"})
            return receipt
        manifest = load_manifest(key, media_path)
        preferred_source = preferred_english_source_track(manifest)
        if preferred_source and args.prefer_embedded_english:
            receipt.update(
                {
                    "status": "skipped",
                    "skippedReason": "preferred_embedded_english_source",
                    "provenance": PROVENANCE_EMBEDDED_EXTRACTED,
                    "selectedCaptionTrack": preferred_source,
                }
            )
            cache_path = Path(str(preferred_source.get("cachePath") or ""))
            if cache_path.exists():
                receipt["qc"] = qc_vtt(
                    cache_path,
                    config=config,
                    provenance=PROVENANCE_EMBEDDED_EXTRACTED,
                    word_timestamps_used=False,
                    english_dub_audio_source=True,
                )
                receipt["sampleCues"] = sample_cues(parse_vtt_segments(cache_path), 20)
            return receipt
        receipt["preferredEmbeddedEnglishTrack"] = preferred_source

        if output_path.exists() and not args.force:
            receipt.update({"status": "skipped", "skippedReason": "generated_ai_caption_exists"})
            receipt["qc"] = qc_vtt(output_path, config=config) if output_path.exists() else None
            return receipt
        if manifest_has_generated_track(manifest, track_id) and not args.force:
            receipt.update({"status": "skipped", "skippedReason": "generated_ai_manifest_track_exists"})
            return receipt
        if args.dry_run:
            receipt.update({"status": "planned", "selectedBackend": backend_to_dict(backend) if backend else None})
            return receipt
        if not backend:
            receipt.update({"status": "NO_GO", "skippedReason": "AI_BACKEND_UNAVAILABLE"})
            receipt["errors"].append("No local AI subtitle backend detected or installed.")
            return receipt

        try:
            audio_selection = select_audio_stream(media_path, args.audio_stream)
        except RuntimeError as error:
            receipt.update({"status": "NO_GO", "skippedReason": str(error)})
            receipt["errors"].append(str(error))
            return receipt
        english_audio_source = selected_audio_looks_english(audio_selection)
        receipt["selectedAudioStream"] = audio_selection
        receipt["englishDubAudioSource"] = english_audio_source
        if not english_audio_source:
            receipt["warnings"].append("Selected ASR audio stream is not explicitly tagged as English/dub.")

        tmp_parent = ensure_under_caption_root(TMP_DIR / key)
        tmp_parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="ai-subtitles-", dir=tmp_parent) as temp_name:
            temp_dir = Path(temp_name)
            audio_path = ensure_under_caption_root(temp_dir / "audio-16k-mono.wav")
            extraction = extract_audio(media_path, audio_selection, audio_path, force=True)
            receipt["audioExtraction"] = extraction
            receipt["commands"].append(extraction["command"])
            if extraction["returnCode"] != 0:
                receipt.update({"status": "NO_GO", "skippedReason": "AUDIO_EXTRACTION_FAILED"})
                receipt["errors"].append(extraction["stderr"] or extraction["stdout"] or "ffmpeg audio extraction failed.")
                if args.keep_temp:
                    kept = tmp_parent / f"kept-{stamp()}"
                    temp_dir.rename(kept)
                    receipt["keptTempDir"] = str(kept)
                return receipt

            speech_spans, speech_receipt = detect_speech_spans(audio_path, config)
            receipt["speechActivity"] = speech_receipt
            if speech_receipt.get("command"):
                receipt["commands"].append(speech_receipt["command"])

            if output_path.exists():
                baseline_existing_segments = parse_vtt_segments(output_path)
                receipt["baselineExistingQc"] = qc_segments(
                    baseline_existing_segments,
                    starts_with_webvtt=output_path.read_text(encoding="utf-8", errors="replace").startswith("WEBVTT"),
                    file_size_bytes=output_path.stat().st_size,
                    speech_spans=speech_spans,
                    config=config,
                    provenance=PROVENANCE_AI_SEGMENT_TIMED,
                    word_timestamps_used=False,
                    english_dub_audio_source=english_audio_source,
                )
                receipt["baselineExistingSample"] = sample_cues(baseline_existing_segments, 20)

            segments, transcribe = transcribe_audio(backend, audio_path, args.model, args.language, temp_dir)
            receipt["selectedBackend"] = backend_to_dict(backend)
            receipt["transcription"] = transcribe
            if transcribe.get("command"):
                receipt["commands"].append(transcribe["command"])
            if transcribe["returnCode"] != 0:
                receipt.update({"status": "NO_GO", "skippedReason": "AI_BACKEND_FAILED"})
                receipt["errors"].append(transcribe["stderr"] or transcribe["stdout"] or "AI backend failed.")
                if args.keep_temp:
                    temp_dir.rename(tmp_parent / f"kept-{stamp()}")
                return receipt

            clean_segments = sanitize_segments(segments)
            if not clean_segments:
                receipt.update({"status": "NO_GO", "skippedReason": "NO_CAPTION_SEGMENTS"})
                receipt["errors"].append("AI backend returned no usable subtitle segments.")
                if args.keep_temp:
                    temp_dir.rename(tmp_parent / f"kept-{stamp()}")
                return receipt

            word_timestamps_used = segments_have_word_timestamps(clean_segments)
            provenance = PROVENANCE_AI_WORD_TIMED if word_timestamps_used else PROVENANCE_AI_SEGMENT_TIMED
            repaired_segments, repair_report = repair_segments(clean_segments, speech_spans, config)
            if not repaired_segments:
                receipt.update({"status": "NO_GO", "skippedReason": "NO_REPAIRED_CAPTION_SEGMENTS"})
                receipt["errors"].append("Timing repair removed all subtitle segments.")
                if args.keep_temp:
                    temp_dir.rename(tmp_parent / f"kept-{stamp()}")
                return receipt

            receipt["rawQc"] = qc_segments(
                clean_segments,
                speech_spans=speech_spans,
                config=config,
                provenance=provenance,
                word_timestamps_used=word_timestamps_used,
                english_dub_audio_source=english_audio_source,
            )
            receipt["repair"] = repair_report
            receipt["beforeAfterSample"] = {"before": sample_cues(clean_segments, 20), "after": sample_cues(repaired_segments, 20)}

            write_vtt(output_path, repaired_segments, config)
            qc = qc_vtt(
                output_path,
                speech_spans=speech_spans,
                config=config,
                provenance=provenance,
                word_timestamps_used=word_timestamps_used,
                english_dub_audio_source=english_audio_source,
            )
            receipt["qc"] = qc
            if qc["startsBeforeDetectedSpeechCount"] > 0:
                receipt["warnings"].append("Some cues still start before detected speech beyond the configured lead window.")
            if qc["longSilenceLingerViolationCount"] > 0:
                receipt["warnings"].append("Some cues still cross long detected silences.")
            if not qc["startsWithWebVtt"] or qc["cueCount"] <= 0 or qc["zeroDurationCueCount"] > 0:
                receipt.update({"status": "NO_GO", "skippedReason": "VTT_QC_FAILED"})
                receipt["errors"].append("Generated VTT failed basic QC.")
                return receipt

            merged = merge_generated_track(
                manifest,
                media_path=media_path,
                key=key,
                track_id=track_id,
                output_path=output_path,
                language=args.language,
                backend=backend,
                model=args.model,
                audio_selection=audio_selection,
                provenance=provenance,
                timing_config=config,
                word_timestamps_used=word_timestamps_used,
                english_dub_audio_source=english_audio_source,
                force=args.force,
            )
            write_json(manifest_path, merged)
            receipt["manifestTrackCount"] = len(merged.get("tracks", []))
            receipt["generatedTrack"] = next((track for track in merged["tracks"] if track.get("id") == track_id), None)
            receipt["provenance"] = provenance
            receipt["wordTimestampsUsed"] = word_timestamps_used
            receipt["status"] = "ok"
            if args.keep_temp:
                kept = tmp_parent / f"kept-{stamp()}"
                temp_dir.rename(kept)
                receipt["keptTempDir"] = str(kept)
    except Exception as error:  # noqa: BLE001 - receipts are for exact operational blockers.
        receipt.update({"status": "NO_GO", "skippedReason": "EXCEPTION"})
        receipt["errors"].append(repr(error))
    finally:
        receipt["endTime"] = utc_now()
        receipt["durationSeconds"] = round(time.time() - started, 3)
    return receipt


def verify_vtt_file(args: argparse.Namespace) -> int:
    media_path = normalize_media_path(args.file)
    vtt_path = Path(str(args.verify_vtt)).expanduser()
    config = timing_config_from_args(args)
    key = media_key(media_path)
    receipt: dict[str, Any] = {
        "schema": "spiritflix-caption-qc/v1",
        "generatedAt": utc_now(),
        "mediaPath": media_path,
        "mediaKey": key,
        "vttPath": str(vtt_path),
        "requestedAudioStream": args.audio_stream,
        "timingConfig": timing_config_to_dict(config),
        "warnings": [],
        "errors": [],
        "commands": [],
    }
    started = time.time()
    try:
        if not Path(media_path).is_file():
            receipt.update({"status": "NO_GO", "code": "MEDIA_FILE_UNAVAILABLE"})
            receipt["errors"].append(media_path)
        elif not vtt_path.is_file():
            receipt.update({"status": "NO_GO", "code": "VTT_FILE_UNAVAILABLE"})
            receipt["errors"].append(str(vtt_path))
        else:
            audio_selection = select_audio_stream(media_path, args.audio_stream)
            english_audio_source = selected_audio_looks_english(audio_selection)
            receipt["selectedAudioStream"] = audio_selection
            receipt["englishDubAudioSource"] = english_audio_source
            if not english_audio_source:
                receipt["warnings"].append("Selected verification audio stream is not explicitly tagged as English/dub.")
            tmp_parent = ensure_under_caption_root(TMP_DIR / key)
            tmp_parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="caption-qc-", dir=tmp_parent) as temp_name:
                temp_dir = Path(temp_name)
                audio_path = ensure_under_caption_root(temp_dir / "audio-16k-mono.wav")
                extraction = extract_audio(media_path, audio_selection, audio_path, force=True)
                receipt["audioExtraction"] = extraction
                receipt["commands"].append(extraction["command"])
                if extraction["returnCode"] != 0:
                    receipt.update({"status": "NO_GO", "code": "AUDIO_EXTRACTION_FAILED"})
                    receipt["errors"].append(extraction["stderr"] or extraction["stdout"] or "ffmpeg audio extraction failed.")
                else:
                    speech_spans, speech_receipt = detect_speech_spans(audio_path, config)
                    receipt["speechActivity"] = speech_receipt
                    if speech_receipt.get("command"):
                        receipt["commands"].append(speech_receipt["command"])
                    receipt["qc"] = qc_vtt(
                        vtt_path,
                        speech_spans=speech_spans,
                        config=config,
                        provenance=None,
                        word_timestamps_used=None,
                        english_dub_audio_source=english_audio_source,
                    )
                    receipt["sampleCues"] = sample_cues(parse_vtt_segments(vtt_path), 20)
                    receipt["status"] = "ok"
    except Exception as error:  # noqa: BLE001 - preserve exact verifier blocker.
        receipt.update({"status": "NO_GO", "code": "EXCEPTION"})
        receipt["errors"].append(repr(error))
    finally:
        receipt["durationSeconds"] = round(time.time() - started, 3)
    evidence_path = QC_DIR / f"caption-qc-{stamp()}-{key}.json"
    write_json(evidence_path, receipt)
    print(json.dumps({"status": receipt.get("status"), "evidence": str(evidence_path), "qc": receipt.get("qc"), "errors": receipt.get("errors")}, sort_keys=True))
    return 0 if receipt.get("status") == "ok" else 1


def write_doc_evidence(args: argparse.Namespace, batch: dict[str, Any], receipts: list[dict[str, Any]]) -> Path:
    DOC_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = DOC_EVIDENCE_DIR / f"spiritflix-ai-subtitles-{stamp()}.md"
    ok = [receipt for receipt in receipts if receipt.get("status") == "ok"]
    skipped = [receipt for receipt in receipts if receipt.get("status") == "skipped"]
    failed = [receipt for receipt in receipts if receipt.get("status") == "NO_GO"]
    lines = [
        "# SpiritFlix AI Subtitles Evidence",
        "",
        f"- generatedAt: {utc_now()}",
        f"- scope: {'file ' + args.file if args.file else 'root ' + str(args.root)}",
        f"- model: {args.model}",
        f"- language: {args.language}",
        f"- backend: {batch.get('selectedBackend')}",
        f"- timingConfig: `{json.dumps(batch.get('timingConfig'), sort_keys=True)}`",
        f"- preferEmbeddedEnglish: {batch.get('preferEmbeddedEnglish')}",
        f"- media considered: {len(receipts)}",
        f"- ok: {len(ok)}",
        f"- skipped: {len(skipped)}",
        f"- failed: {len(failed)}",
        "",
        "## Results",
        "",
    ]
    for receipt in receipts:
        lines.extend(
            [
                f"### {Path(str(receipt.get('mediaPath', 'unknown'))).name}",
                "",
                f"- status: {receipt.get('status')}",
                f"- mediaPath: {receipt.get('mediaPath')}",
                f"- mediaKey: {receipt.get('mediaKey')}",
                f"- selectedBackend: {receipt.get('selectedBackend')}",
                f"- selectedAudioStream: {receipt.get('selectedAudioStream')}",
                f"- provenance: {receipt.get('provenance')}",
                f"- wordTimestampsUsed: {receipt.get('wordTimestampsUsed')}",
                f"- englishDubAudioSource: {receipt.get('englishDubAudioSource')}",
                f"- outputVttPath: {receipt.get('outputVttPath')}",
                f"- manifestPath: {receipt.get('manifestPath')}",
                f"- baselineExistingQc: `{json.dumps(receipt.get('baselineExistingQc'), sort_keys=True)}`",
                f"- rawQc: `{json.dumps(receipt.get('rawQc'), sort_keys=True)}`",
                f"- repair: `{json.dumps(receipt.get('repair'), sort_keys=True)}`",
                f"- qc: `{json.dumps(receipt.get('qc'), sort_keys=True)}`",
                f"- selectedCaptionTrack: `{json.dumps(receipt.get('selectedCaptionTrack'), sort_keys=True)}`",
                f"- skippedReason: {receipt.get('skippedReason')}",
                f"- errors: `{json.dumps(receipt.get('errors', []))}`",
                "",
            ]
        )
        sample = receipt.get("beforeAfterSample") or {}
        if sample:
            lines.extend(["#### Before/After Sample", ""])
            for label in ["before", "after"]:
                lines.extend([f"- {label}:"])
                for cue in sample.get(label, [])[:10]:
                    lines.append(f"  - {cue.get('start')} --> {cue.get('end')}: {cue.get('text')}")
            lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def validate_args(args: argparse.Namespace) -> str | None:
    if args.verify_vtt and not args.file:
        return "--verify-vtt requires --file so the VTT can be compared with audio."
    if args.verify_vtt and args.root:
        return "--verify-vtt cannot be combined with --root."
    if not args.detect_only and not args.file and not args.root:
        return "Either --file or --root is required."
    if args.root and not args.limit and not args.confirm_large_batch:
        return "--limit is required for --root mode unless --confirm-large-batch is passed."
    if args.limit is not None and args.limit <= 0:
        return "--limit must be greater than 0."
    return None


def main() -> int:
    args = parse_args()
    validation_error = validate_args(args)
    if validation_error:
        print(json.dumps({"status": "NO_GO", "code": "INVALID_ARGS", "error": validation_error}))
        return 2
    if args.verify_vtt:
        return verify_vtt_file(args)

    allow_install = not args.no_install and not args.dry_run
    backend, available_backends, install_receipt = choose_backend(args.backend, allow_install)
    batch: dict[str, Any] = {
        "schema": "spiritflix-ai-subtitle-batch/v1",
        "startedAt": utc_now(),
        "selectedBackend": backend_to_dict(backend) if backend else None,
        "availableBackends": [backend_to_dict(item) for item in available_backends],
        "installAttempt": install_receipt,
        "model": args.model,
        "language": args.language,
        "dryRun": bool(args.dry_run),
        "timingConfig": timing_config_to_dict(timing_config_from_args(args)),
        "preferEmbeddedEnglish": bool(args.prefer_embedded_english),
        "items": [],
        "summary": {"ok": 0, "skipped": 0, "failed": 0, "planned": 0},
    }

    if args.detect_only:
        print(json.dumps({"status": "ok" if backend else "NO_GO", **batch}, sort_keys=True))
        return 0 if backend else 2

    if args.file:
        media_paths = [normalize_media_path(args.file)]
    else:
        media_paths = scan_videos(str(args.root))
        if args.limit:
            media_paths = media_paths[: args.limit]

    receipts: list[dict[str, Any]] = []
    for media_path in media_paths:
        receipt = process_media(media_path, args, backend, available_backends, install_receipt)
        receipt_path = write_receipt(receipt)
        receipt["receiptPath"] = str(receipt_path)
        receipts.append(receipt)
        status = receipt.get("status")
        if status == "ok":
            batch["summary"]["ok"] += 1
        elif status == "planned":
            batch["summary"]["planned"] += 1
        elif status == "skipped":
            batch["summary"]["skipped"] += 1
        else:
            batch["summary"]["failed"] += 1

    batch["items"] = [
        {
            "mediaPath": receipt.get("mediaPath"),
            "mediaKey": receipt.get("mediaKey"),
            "status": receipt.get("status"),
            "receiptPath": receipt.get("receiptPath"),
            "outputVttPath": receipt.get("outputVttPath"),
            "manifestPath": receipt.get("manifestPath"),
            "qc": receipt.get("qc"),
            "skippedReason": receipt.get("skippedReason"),
        }
        for receipt in receipts
    ]
    batch["finishedAt"] = utc_now()
    batch_path = RECEIPT_DIR / f"ai-subtitles-batch-{stamp()}.json"
    write_json(batch_path, batch)
    doc_path = write_doc_evidence(args, batch, receipts)

    result = {
        "status": "ok" if batch["summary"]["failed"] == 0 else "NO_GO",
        "summary": batch["summary"],
        "batchReceipt": str(batch_path),
        "docEvidence": str(doc_path),
        "items": batch["items"],
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if batch["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
