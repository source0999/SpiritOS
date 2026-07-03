#!/usr/bin/env python3
"""
Media Face Organizer v1.

Install GPU dependencies on the media host:

    pip install insightface "onnxruntime-gpu[cuda,cudnn]" numpy pillow opencv-python-headless tqdm

Optional, for prettier progress bars:

    pip install rich

This tool is dry-run by default. Scans do not write metadata, NFO files, or
review crops unless --apply is passed. The --report mode intentionally writes
the HTML report because report generation is its entire job.
"""

from __future__ import annotations

import argparse
import base64
import dataclasses
import hashlib
import html
import http.server
import json
import logging
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from http import HTTPStatus
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def bootstrap_venv_cuda_paths() -> None:
    """Expose pip-installed NVIDIA shared libraries before ONNX Runtime loads."""
    if os.environ.get("FACE_ORGANIZER_CUDA_BOOTSTRAPPED") == "1":
        return
    venv = os.environ.get("VIRTUAL_ENV")
    if not venv:
        return
    site_root = Path(venv) / "lib"
    candidates = sorted(site_root.glob("python*/site-packages/nvidia/*/lib"))
    existing = [str(path) for path in candidates if path.exists()]
    if not existing:
        return
    current = os.environ.get("LD_LIBRARY_PATH", "")
    current_parts = [part for part in current.split(":") if part]
    missing = [path for path in existing if path not in current_parts]
    if not missing:
        return
    os.environ["LD_LIBRARY_PATH"] = ":".join(missing + current_parts)
    os.environ["FACE_ORGANIZER_CUDA_BOOTSTRAPPED"] = "1"
    os.execvpe(sys.executable, [sys.executable, *sys.argv], os.environ)


bootstrap_venv_cuda_paths()

try:
    import numpy as np
except ImportError as exc:  # pragma: no cover - exercised only on unbootstrapped hosts
    raise SystemExit(
        "Missing required dependency: numpy. Install with: "
        'pip install insightface "onnxruntime-gpu[cuda,cudnn]" numpy pillow opencv-python-headless tqdm'
    ) from exc

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".mov",
    ".avi",
    ".webm",
    ".m4v",
    ".wmv",
    ".flv",
}
EXCLUDED_SCAN_DIRS = {".face-review", "models", "unknown", "backups", "review_exports", "known_performers"}
# Model-folder and unknown-folder uploads still need human verification before trust.
VERIFICATION_QUEUE_EXCLUDED_DIRS = EXCLUDED_SCAN_DIRS - {"unknown", "models"}
GALLERY_DIR_NAME = "model_gallery"
GALLERY_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
GALLERY_SIDECAR_SUFFIX = ".gallery.json"
GALLERY_MAX_UPLOAD_BYTES = 256 * 1024 * 1024
HIGH_CONFIDENCE = 0.80
POSSIBLE_CONFIDENCE = 0.55
ENROLLMENT_MIN_SCREENS_PER_VIDEO = 5
ENROLLMENT_SCAN_FRAMES_PER_VIDEO = 18
ENROLLMENT_SINGLE_VIDEO_DEEP_SCAN_FRAMES = 48
ENROLLMENT_MAX_CROPS_PER_VIDEO = 5
ENROLLMENT_MIN_DET_SCORE = 0.72
ENROLLMENT_FACE_ASPECT_MIN = 0.55
ENROLLMENT_FACE_ASPECT_MAX = 1.75
ENROLLMENT_UNIDENTIFIED_RESCAN_LIMIT = 80
ENROLLMENT_CONFIDENCE_BASELINE_SCREENS = 10
ENROLLMENT_CONFIDENCE_MAX_TARGET_SCREENS = 20
DEFAULT_SOURCE = os.environ.get("FACE_ORGANIZER_SOURCE", "/mnt/spirit-8tb/media/other")
DEFAULT_DB = os.environ.get("FACE_ORGANIZER_DB", "scripts/media/known_performers")
DEFAULT_REPORT = os.environ.get("FACE_ORGANIZER_REPORT", "scripts/media/face_verification_report.html")
DEFAULT_BACKUP_DIR = os.environ.get("FACE_ORGANIZER_BACKUP_DIR", "scripts/media/backups")
DEFAULT_RENAME_MANIFEST = os.environ.get("FACE_ORGANIZER_RENAME_MANIFEST", "scripts/media/rename_plan.json")
DEFAULT_ORGANIZE_MANIFEST = os.environ.get("FACE_ORGANIZER_ORGANIZE_MANIFEST", "scripts/media/organize_manifest.json")
DEFAULT_VERIFICATION_REGISTRY = os.environ.get("FACE_ORGANIZER_VERIFICATION_REGISTRY", "scripts/media/performer_verification.json")
DEFAULT_MODEL = os.environ.get("FACE_ORGANIZER_MODEL", "buffalo_l")
MODEL_VERSION = f"insightface:{DEFAULT_MODEL}"
WEB_TEXT_EVIDENCE_SCHEMA = "media-web-text-evidence/v1"
IDENTITY_TRACE_SCHEMA = "media-identity-trace/v1"
ASSIGNMENT_DECISION_SCHEMA = "media-assignment-decision/v1"
SOURCE_TRUST_LEVELS = {
    "official-profile",
    "creator-profile",
    "configured-corroborator",
    "repost-index",
    "unknown",
}
REPOST_INDEX_DOMAINS = {"coomer.st", "pimpbunny.com"}
CREATOR_PROFILE_DOMAINS = {"onlyfans.com", "fansly.com", "fanvue.com"}
NOISE_TOKENS = {
    "1080p",
    "480p",
    "720p",
    "4k",
    "fhd",
    "hd",
    "hq",
    "leak",
    "leaked",
    "paid",
    "telegram",
    "tg",
    "join",
    "joinus",
    "visit",
    "onlyshare",
    "of4lm",
    "plugleakz",
    "fapptime",
    "pornhub",
    "onlyfans",
    "fans",
    "nsfw365",
    "packby",
    "com",
    "net",
    "www",
    "more",
    "home",
    "yes",
    "other",
    "media",
    "movies",
    "music",
    "anime",
    "tv",
    "optimized",
    "test",
}
HOST_WATERMARK_DOMAINS = {
    "of4lm.com",
    "onlyshare.io",
    "yummycouple.com",
}


@dataclasses.dataclass(frozen=True)
class OrganizerConfig:
    source_dir: Path
    db_dir: Path
    report_path: Path
    backup_dir: Path
    rename_manifest_path: Path
    apply: bool
    write_nfo: bool
    backup_videos: bool
    frame_count: int
    sample_limit: int | None
    force: bool
    skip_existing: bool
    recursive: bool
    model_name: str
    ctx_id: int
    det_size: tuple[int, int]
    review_dir_name: str
    min_face_score: float
    min_face_area_ratio: float
    ocr_watermarks: bool
    organize_manifest_path: Path
    verification_registry_path: Path
    report_all: bool = False


@dataclasses.dataclass
class Match:
    performer_id: str | None
    name: str
    similarity: float
    status: str
    verification_needed: bool
    confidence_label: str


@dataclasses.dataclass
class FaceObservation:
    frame_path: Path
    crop_path: Path | None
    embedding: np.ndarray
    bbox: list[float]
    det_score: float
    match: Match


@dataclasses.dataclass
class RejectedFace:
    frame_path: Path
    bbox: list[float]
    det_score: float
    reason: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or f"performer-{uuid.uuid4().hex[:8]}"


def safe_percent(value: float) -> str:
    return f"{round(value * 100)}%"


def sanitized_filename_part(value: str, fallback: str = "unknown") -> str:
    value = re.sub(r"[<>:\"/\\|?*\x00-\x1f]", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" ._-")
    return value[:120] or fallback


def normalize_candidate_name(value: str) -> str:
    original = value.strip()
    if re.fullmatch(r"[a-fA-F0-9]{16,}", original):
        return ""
    if re.fullmatch(r"[A-Za-z0-9_-]{10,}", original) and any(char.isdigit() for char in original):
        return ""
    if re.search(r"\.(com|fun|net|io|org|co)\b", original, flags=re.IGNORECASE):
        return ""
    value = re.sub(r"[_~]+", " ", value)
    value = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", value)
    value = re.sub(r"[^A-Za-z0-9\s.'-]+", " ", value)
    value = re.sub(r"\b\d{3,}\b", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" ._-")
    words = [word for word in value.split() if word.lower() not in NOISE_TOKENS]
    if not words:
        return ""
    return " ".join(word[:1].upper() + word[1:] for word in words[:5])


def normalized_host_domain(value: str) -> str:
    text = str(value or "").lower()
    text = text.replace("[dot]", ".").replace("(dot)", ".")
    text = text.replace("0", "o")
    for domain in HOST_WATERMARK_DOMAINS:
        if domain in text:
            return domain
    compact = re.sub(r"\s+", "", text)
    for domain in HOST_WATERMARK_DOMAINS:
        if domain in compact:
            return domain
    match = re.search(r"([a-z0-9-]+)\.(com|io|net|org|co)\b", compact, re.I)
    if not match:
        return ""
    return f"{match.group(1)}.{match.group(2)}".lower()


def host_watermark_evidence(text: str, region: str, confidence: float, frame_path: Any = None) -> dict[str, Any] | None:
    domain = normalized_host_domain(text)
    if not domain or domain not in HOST_WATERMARK_DOMAINS:
        return None
    return {
        "name": "site watermark found; model still unknown",
        "source": "site_watermark",
        "confidence": round(float(confidence), 2),
        "raw": text,
        "domain": domain,
        "region": region,
        "frame_path": frame_path,
        "variants": [domain],
        "evidence_role": "site_watermark",
        "not_performer_name": True,
    }


def expand_ocr_text_fragments(text: str) -> list[str]:
    raw = str(text or "")
    fragments = [raw]
    fragments.extend(re.split(r"[/\\|:;@]+", raw))
    fragments.extend(re.findall(r"[A-Z]?[a-z]+|[A-Z]{2,}(?=[A-Z][a-z]|\b)|[A-Za-z]+|\d+", raw))
    compact = re.sub(r"[^A-Za-z0-9]+", "", raw)
    if compact and compact != raw:
        fragments.append(compact)
    expanded: list[str] = []
    seen: set[str] = set()
    for fragment in fragments:
        cleaned = fragment.strip(" ._-")
        if len(cleaned) < 3:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            expanded.append(cleaned)
    return expanded[:8]


def watermark_region_weight(region: str) -> float:
    region = str(region or "full")
    if region in {"bottom_strip", "top_strip", "bottom_left", "bottom_right", "top_left", "top_right"}:
        return 1.16
    return 0.82


def candidate_variants(name: str, raw_text: str = "") -> list[str]:
    variants: list[str] = []
    seen: set[str] = set()

    def add(value: str) -> None:
        cleaned = " ".join(str(value or "").split()).strip(" ._-")
        if not cleaned:
            return
        key = normalize_identity_key(cleaned)
        if not key or key in seen or is_bad_candidate_name(cleaned, raw_text or cleaned):
            return
        seen.add(key)
        variants.append(cleaned)

    add(name)
    add(split_handle_words(name))
    compact = re.sub(r"\s+", "", name)
    if compact != name:
        add(compact)
    without_single_prefix = re.sub(r"^[A-Za-z]\s+(?=[A-Za-z0-9_.-]{4,}$)", "", name).strip()
    if without_single_prefix and without_single_prefix != name:
        add(without_single_prefix)
    missing_space = re.sub(r"(?i)\b([A-Za-z])([A-Za-z]{4,})\b", r"\1 \2", name)
    if missing_space != name:
        add(missing_space)
    compact_raw = re.sub(r"[^A-Za-z0-9]+", "", raw_text or "")
    if 4 <= len(compact_raw) <= 28:
        add(split_handle_words(compact_raw))
    handle_match = re.search(r"\b[A-Za-z][A-Za-z0-9_.-]{3,24}\b", raw_text or "")
    if handle_match:
        add(handle_match.group(0))
    return variants[:5]


def normalized_candidate(
    name: str,
    source: str,
    confidence: float,
    raw: Any,
    *,
    frame_path: Any = None,
    region: str | None = None,
    platform: str | None = None,
    handle: str | None = None,
    profile_url: str | None = None,
    evidence_role: str = "candidate",
) -> dict[str, Any] | None:
    raw_text = raw if isinstance(raw, str) else json.dumps(raw, sort_keys=True, default=str)
    canonical = split_handle_words(name)
    if is_bad_candidate_name(canonical, raw_text):
        return None
    candidate = {
        "name": canonical,
        "source": source,
        "confidence": round(float(confidence), 2),
        "raw": raw,
        "variants": candidate_variants(canonical, raw_text),
        "evidence_role": evidence_role,
    }
    if frame_path:
        candidate["frame_path"] = frame_path
    if region:
        candidate["region"] = region
    if platform:
        candidate["platform"] = platform
    if handle:
        candidate["handle"] = handle
    if profile_url:
        candidate["profile_url"] = profile_url
    return candidate


def dedupe_rank_candidates(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for item in candidates:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "")
        key = normalize_identity_key(name)
        if not key:
            continue
        current = best.get(key)
        if current is None or float(item.get("confidence") or 0) > float(current.get("confidence") or 0):
            merged = dict(item)
            variants: list[str] = []
            for source_item in (current, item):
                if not source_item:
                    continue
                for variant in source_item.get("variants") or []:
                    if variant not in variants:
                        variants.append(str(variant))
            merged["variants"] = variants[:5] or candidate_variants(name, str(item.get("raw") or ""))
            best[key] = merged
    return sorted(best.values(), key=lambda item: float(item.get("confidence") or 0), reverse=True)


def extract_filename_candidates(video_path: Path) -> list[dict[str, Any]]:
    stem = video_path.stem
    raw_candidates = [stem]
    raw_candidates.extend(re.split(r"[-_\[\](){}]+", stem))
    raw_candidates.append(video_path.parent.name)
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in raw_candidates:
        name = normalize_candidate_name(raw)
        if len(name) < 3:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        score = 0.35
        if " " in name:
            score += 0.2
        if any(char.isalpha() for char in name):
            score += 0.1
        candidate = normalized_candidate(name, "filename", min(score, 0.75), raw, evidence_role="filename_hint")
        if candidate:
            candidates.append(candidate)
    return candidates[:6]


def request_json(url: str, headers: dict[str, str], timeout: int = 15) -> Any:
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def lookup_papi_candidates(name: str) -> list[dict[str, Any]]:
    api_key = os.environ.get("PAPI_RAPIDAPI_KEY")
    api_host = os.environ.get("PAPI_RAPIDAPI_HOST", "papi-pornstarsapi.p.rapidapi.com")
    base_url = os.environ.get("PAPI_BASE_URL", f"https://{api_host}/pornstars/")
    if not api_key or not name:
        return []
    query = urllib.parse.urlencode({"q": name, "name": name, "limit": "5"})
    separator = "&" if "?" in base_url else "?"
    try:
        payload = request_json(
            f"{base_url}{separator}{query}",
            {
                "X-RapidAPI-Key": api_key,
                "X-RapidAPI-Host": api_host,
                "Accept": "application/json",
            },
        )
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        logging.warning("pAPI lookup failed for %s: %s", name, exc)
        return []
    rows = payload.get("data") if isinstance(payload, dict) else payload
    if isinstance(rows, dict):
        rows = rows.get("items") or rows.get("results") or rows.get("pornstars") or []
    candidates: list[dict[str, Any]] = []
    for item in rows if isinstance(rows, list) else []:
        if not isinstance(item, dict):
            continue
        candidate_name = item.get("name") or item.get("performer_name") or item.get("title")
        if not candidate_name:
            continue
        candidates.append(
            {
                "name": str(candidate_name),
                "source": "papi",
                "confidence": 0.62,
                "slug": item.get("slug"),
                "aliases": item.get("aliases") or [],
                "raw": {key: item.get(key) for key in ("name", "slug", "nationality", "ethnicity", "hair", "eyes") if key in item},
            }
        )
    return candidates[:5]


def watermark_ocr_images(frame_path: Path) -> list[tuple[str, Path]]:
    try:
        from PIL import Image, ImageEnhance, ImageFilter
    except ImportError:
        return [("full", frame_path)]
    try:
        image = Image.open(frame_path).convert("RGB")
    except OSError:
        return [("full", frame_path)]
    width, height = image.size
    if width <= 0 or height <= 0:
        return [("full", frame_path)]
    regions = {
        "full": (0, 0, width, height),
        "bottom_strip": (0, int(height * 0.68), width, height),
        "top_strip": (0, 0, width, int(height * 0.32)),
        "bottom_left": (0, int(height * 0.58), int(width * 0.52), height),
        "bottom_right": (int(width * 0.48), int(height * 0.58), width, height),
        "top_left": (0, 0, int(width * 0.52), int(height * 0.42)),
        "top_right": (int(width * 0.48), 0, width, int(height * 0.42)),
    }
    ocr_dir = frame_path.parent / ".ocr-regions"
    ocr_dir.mkdir(parents=True, exist_ok=True)
    images: list[tuple[str, Path]] = [("full", frame_path)]
    for region_name, box in regions.items():
        if region_name == "full":
            continue
        crop = image.crop(box)
        if crop.width < 24 or crop.height < 24:
            continue
        scale = 3 if max(crop.size) < 900 else 2
        crop = crop.resize((crop.width * scale, crop.height * scale))
        crop = ImageEnhance.Contrast(crop).enhance(1.8)
        crop = ImageEnhance.Sharpness(crop).enhance(1.7)
        crop = crop.filter(ImageFilter.UnsharpMask(radius=1, percent=140, threshold=3))
        target = ocr_dir / f"{frame_path.stem}-{region_name}.jpg"
        crop.save(target, "JPEG", quality=92)
        images.append((region_name, target))
    return images


def ocr_frame_text(frame_paths: list[Path]) -> list[dict[str, Any]]:
    if not frame_paths:
        return []
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        logging.debug("rapidocr_onnxruntime is not installed; skipping watermark OCR")
        return []
    ocr = RapidOCR()
    results: list[dict[str, Any]] = []
    for frame_path in frame_paths[:8]:
        for region_name, ocr_path in watermark_ocr_images(frame_path):
            try:
                detections, _elapsed = ocr(str(ocr_path))
            except Exception as exc:
                logging.warning("OCR failed for %s: %s", ocr_path, exc)
                continue
            for detection in detections or []:
                if len(detection) < 3:
                    continue
                box, text, score = detection[0], str(detection[1]), float(detection[2])
                cleaned_text = text.strip()
                if score < 0.48 or len(cleaned_text) < 3:
                    continue
                results.append(
                    {
                        "text": cleaned_text,
                        "confidence": round(score, 3),
                        "frame_path": str(frame_path),
                        "ocr_image_path": str(ocr_path),
                        "region": region_name,
                        "box": box,
                    }
                )
    return results


def split_handle_words(value: str) -> str:
    value = re.sub(r"[_\-.]+", " ", value)
    value = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", value)
    # Common creator handles are all lowercase; preserve short known-looking names
    # but split simple firstlast handles into title case words when possible.
    known_splits = {
        "savas": "Sava Schultz",
        "savasch": "Sava Schultz",
        "saavasch": "Sava Schultz",
        "savash": "Sava Schultz",
        "savasehurlt": "Sava Schultz",
        "savascchurlt": "Sava Schultz",
        "savascchultz": "Sava Schultz",
        "savaschiultz": "Sava Schultz",
        "savaschu": "Sava Schultz",
        "savaschult": "Sava Schultz",
        "savaschuiltz": "Sava Schultz",
        "savaschyltz": "Sava Schultz",
        "savaschultz": "Sava Schultz",
        "onlyfanscomysavaschultz": "Sava Schultz",
        "onlyfanscomsavaschultz": "Sava Schultz",
        "cutegeekie": "Cute Geekie",
        "qutegeekie": "Cute Geekie",
        "meekie": "Cute Geekie",
        "cutegeer": "Cute Geekie",
        "cutegeer": "Cute Geekie",
        "cuteyeekie": "Cute Geekie",
        "cutegdekie": "Cute Geekie",
        "cuteggekie": "Cute Geekie",
        "cutegoekie": "Cute Geekie",
        "cuteadekie": "Cute Geekie",
        "cutegeel": "Cute Geekie",
        "utegeekie": "Cute Geekie",
        "ambune": "Amburne",
        "amburne": "Amburne",
        "angetawhite": "Angela White",
        "katianakayfm": "Katianakayfree",
        "katianakayfree": "Katianakayfree",
        "madiitay": "Maditay",
        "maditay": "Maditay",
        "pin": "Pinkychu",
        "pinl": "Pinkychu",
        "pinhy": "Pinkychu",
        "pichyu": "Pinkychu",
        "kchyu": "Pinkychu",
        "pinkchyu": "Pinkychu",
        "pinkychu": "Pinkychu",
        "ruth": "Ruth Lee",
        "ruthlce": "Ruth Lee",
        "ruthlee": "Ruth Lee",
        "sendnueesx": "Sendnudesx",
        "sendnudesx": "Sendnudesx",
        "mackzjones": "Mackzjones",
        "mackzjone": "Mackzjones",
        "ickzjone": "Mackzjones",
        "ackzjone": "Mackzjones",
        "ackzfone": "Mackzjones",
        "iackzfone": "Mackzjones",
        "misslilu": "Miss LiLu",
        "lilu": "Miss LiLu",
        "lilushandjobs": "Miss LiLu",
        "puffypink": "Puffy Pink",
        "bearu": "Bearuby",
        "bearub": "Bearuby",
        "bearua": "Bearuby",
        "bearuby": "Bearuby",
        "beamu": "Bearuby",
        "oearuby": "Bearuby",
        "chkoelamb": "Chloe Lamb",
        "chloelamb": "Chloe Lamb",
        "chloclamb": "Chloe Lamb",
        "lazmenjafr": "Jazmen Jafar",
        "lazmenjafar": "Jazmen Jafar",
        "jazmenjafar": "Jazmen Jafar",
        "azmenjafar": "Jazmen Jafar",
        "jarmenjafar": "Jazmen Jafar",
        "jazme": "Jazmen Jafar",
        "jazmer": "Jazmen Jafar",
        "gemthejewels": "Gem The Jewels",
        "gemejewels": "Gem The Jewels",
        "gemthejewls": "Gem The Jewels",
        "gemthejewls": "Gem The Jewels",
        "gemthejewels": "Gem The Jewels",
        "brendatril": "Brenda Trindade",
        "brendatri": "Brenda Trindade",
        "brendatrii": "Brenda Trindade",
        "brendatrindadee": "Brenda Trindade",
        "aziliahadid": "Azilia Hadid",
        "izzygreen": "Izzy Green",
        "izzygree": "Izzy Green",
        "lzzygreen": "Izzy Green",
        "izzygeen": "Izzy Green",
        "izzyg": "Izzy Green",
        "zygreen": "Izzy Green",
        "siennaababi": "Sienna Ababi",
        "siennaabab": "Sienna Ababi",
        "slennaababi": "Sienna Ababi",
        "sienaabbi": "Sienna Ababi",
        "leighbunbun": "Leighbunbun",
        "eighbunbun": "Leighbunbun",
        "jakara": "Jakara Mitchell",
        "iaarababy": "Jakara Mitchell",
        "iaaraoaby": "Jakara Mitchell",
        "jakarab": "Jakara Mitchell",
        "jakarabap": "Jakara Mitchell",
        "jakarabao": "Jakara Mitchell",
        "jakarababy": "Jakara Mitchell",
        "jakaramitchell": "Jakara Mitchell",
        "karamito": "Jakara Mitchell",
        "karamite": "Jakara Mitchell",
        "karamit": "Jakara Mitchell",
        "sakhovanski": "Sakhovanski",
        "saknovanski": "Sakhovanski",
        "khovansk": "Sakhovanski",
        "hayleelove": "Haylee Love",
        "havleel": "Haylee Love",
        "hayleelov": "Haylee Love",
        "hayleeloy": "Haylee Love",
        "aaliyahyasan": "Aaliyah Yasan",
        "thatbritishgirl": "Aaliyah Yasan",
        "thatbritishgirlxdirtyspringbok": "Aaliyah Yasan",
        "abmy": "Aaliyah Yasan",
        "kinkykttn": "Kinkykttn",
        "kinkyktn": "Kinkykttn",
        "alannasworlx": "Alannasworldx",
        "alannasworldx": "Alannasworldx",
        "olenfromalannasworldx": "Alannasworldx",
        "tolenfromalannasworldx": "Alannasworldx",
        "romalannasworldx": "Alannasworldx",
        "stolentromalannasworldx": "Alannasworldx",
        "omalannasworldx": "Alannasworldx",
    }
    lowered = normalize_identity_key(value)
    if re.search(r"sava(?:sch|sh|se?h|s?c?h?u?l?t?z)", lowered):
        return "Sava Schultz"
    if "sendnudesx" in lowered:
        return "Sendnudesx"
    if "ckzjon" in lowered or "ckzfon" in lowered:
        return "Mackzjones"
    if lowered in known_splits:
        return known_splits[lowered]
    return normalize_candidate_name(value)


def is_bad_candidate_name(name: str, raw_text: str = "") -> bool:
    lowered = name.lower().strip()
    identity_key = normalize_identity_key(name)
    raw_lowered = raw_text.lower()
    if not lowered or lowered in NOISE_TOKENS or lowered == "unknown":
        return True
    if identity_key in {
        "unknown",
        "only",
        "onlyfar",
        "onlyfans",
        "onlyfansc",
        "onlyf",
        "onlyfa",
        "fans",
        "fanscc",
        "fansly",
        "telegram",
        "this",
        "thisvideo",
        "thisvideowas",
        "uploaded",
        "uploadedto",
        "thothub",
        "thothublol",
    }:
        return True
    if identity_key in {"onlyc", "onlyfanscom", "onlyfansco", "fansc", "fansco", "fanscom"}:
        return True
    if any(domain.replace(".", "") in identity_key for domain in HOST_WATERMARK_DOMAINS):
        return True
    if identity_key.startswith(("onlyfan", "onlyfar", "telegram")):
        return identity_key not in {"onlyfanscomysavaschultz", "onlyfanscomsavaschultz"}
    if identity_key.startswith(("virai", "viral", "jirai")) and ("porn" in identity_key or "xxx" in identity_key or "hub" in identity_key):
        return True
    if lowered in {"fansly", "fansly c", "onlyfans", "telegram", "t me", "t.me", "packby"}:
        return True
    if "fansly" in lowered or "onlyfans" in lowered or "only fans" in lowered:
        return True
    if len(lowered) > 36 and " " not in lowered:
        return True
    if re.fullmatch(r"[a-f0-9]{16,}", lowered):
        return True
    if raw_lowered.startswith("t.me/") or raw_lowered.strip() in {"telegram", "t me", "t.me"}:
        return True
    return False


def profile_mentions_from_text(text: str) -> list[dict[str, str]]:
    mentions: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    profile_pattern = re.compile(
        r"\b(onlyfans|fansly|fanvue|lyfans|of)[\s.:;]*c[o0][mnrli]{0,2}[/\\:|]+([A-Za-z0-9_.-]{4,})",
        re.IGNORECASE,
    )
    for match in profile_pattern.finditer(text):
        platform = match.group(1).lower()
        if platform in {"lyfans", "of"}:
            platform = "onlyfans"
        handle = re.sub(r"[^A-Za-z0-9_.-].*$", "", match.group(2)).strip("._-")
        if not handle:
            continue
        key = (platform, handle.lower())
        if key in seen:
            continue
        seen.add(key)
        mentions.append({"platform": platform, "handle": handle, "url": f"https://{platform}.com/{handle}"})
    return mentions


def watermark_candidates(ocr_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    site_seen: set[str] = set()
    patterns = [
        r"(?:^|\b)c[o0][mnrli]{0,2}[/\\:|]+([A-Za-z0-9_.-]{5,})",
        r"(?:stolen\s+from|leaked\s+from|leaked\s+by|from)\s+([A-Za-z0-9_.-]{4,})",
        r"@([A-Za-z0-9_.-]{4,})",
    ]
    for result in ocr_results:
        text = str(result.get("text", ""))
        region = str(result.get("region") or "full")
        score = float(result.get("confidence", 0.6))
        weighted_score = min(0.95, max(0.1, score * watermark_region_weight(region)))
        site_evidence = host_watermark_evidence(text, region, weighted_score, result.get("frame_path"))
        if site_evidence and str(site_evidence.get("domain")) not in site_seen:
            site_seen.add(str(site_evidence.get("domain")))
            candidates.append(site_evidence)
        for mention in profile_mentions_from_text(text):
            name = split_handle_words(mention["handle"])
            key = normalize_identity_key(name)
            if key in seen or is_bad_candidate_name(name, text):
                continue
            seen.add(key)
            candidate = normalized_candidate(
                name,
                "watermark_profile_url",
                min(0.92, weighted_score * 0.95),
                text,
                frame_path=result.get("frame_path"),
                region=region,
                platform=mention["platform"],
                handle=mention["handle"],
                profile_url=mention["url"],
                evidence_role="watermark_profile_url",
            )
            if candidate:
                candidates.append(candidate)
        for pattern in patterns:
            if ("telegram" in text.lower() or "t.me/" in text.lower()) and pattern.startswith("@"):
                continue
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                raw = match.group(1)
                raw = re.sub(r"[^A-Za-z0-9_.-].*$", "", raw).strip("._-")
                name = split_handle_words(raw)
                if is_bad_candidate_name(name, text) or name.lower() in seen:
                    continue
                seen.add(normalize_identity_key(name))
                profile_like = "com" in pattern or "from" in pattern
                confidence_cap = 0.9 if profile_like or region != "full" else 0.78
                candidate = normalized_candidate(
                    name,
                    "watermark_ocr",
                    min(confidence_cap, weighted_score * 0.92),
                    text,
                    frame_path=result.get("frame_path"),
                    region=region,
                    evidence_role="ocr_handle",
                )
                if candidate:
                    candidates.append(candidate)
        for fragment_index, fragment in enumerate(expand_ocr_text_fragments(text)):
            cleaned = normalize_candidate_name(fragment)
            if (
                cleaned
                and normalize_identity_key(cleaned) not in seen
                and len(cleaned.split()) <= 3
                and not is_bad_candidate_name(cleaned, text)
            ):
                seen.add(normalize_identity_key(cleaned))
                raw_text = fragment.strip()
                handle_like = bool(
                    re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{3,24}", raw_text)
                    and (
                        any(char in raw_text for char in "_.-0123456789")
                        or bool(re.search(r"[a-z][A-Z]", raw_text))
                        or not raw_text.islower()
                    )
                )
                confidence_cap = 0.86 if handle_like and region != "full" else 0.68
                multiplier = 0.88 if handle_like and region != "full" else 0.65
                if fragment_index:
                    multiplier *= 0.88
                candidate = normalized_candidate(
                    cleaned,
                    "watermark_ocr_text",
                    min(confidence_cap, weighted_score * multiplier),
                    text,
                    frame_path=result.get("frame_path"),
                    region=region,
                    evidence_role="ocr_text",
                )
                if candidate:
                    candidates.append(candidate)
    return dedupe_rank_candidates(candidates)[:8]


def yandex_search_url(query: str) -> str:
    return f"https://yandex.com/search/?text={urllib.parse.quote(query)}"


def coomer_search_url(query: str) -> str:
    return f"https://coomer.st/search?q={urllib.parse.quote(query)}"


def source_domain(url: str) -> str:
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
    except ValueError:
        return ""
    return host[4:] if host.startswith("www.") else host


def source_trust_level(url: str, configured_domains: set[str] | None = None) -> str:
    domain = source_domain(url)
    configured = {item.lower() for item in (configured_domains or set())}
    if domain in CREATOR_PROFILE_DOMAINS:
        return "creator-profile"
    if domain in REPOST_INDEX_DOMAINS:
        return "repost-index"
    if domain in configured:
        return "configured-corroborator"
    return "unknown"


def normalize_search_result(
    result: dict[str, Any],
    *,
    provider: str,
    query: str,
    configured_domains: set[str] | None = None,
) -> dict[str, Any]:
    url = str(result.get("url") or result.get("link") or "")
    title = str(result.get("title") or result.get("name") or "")
    snippet = str(result.get("snippet") or result.get("content") or result.get("description") or "")
    trust = source_trust_level(url, configured_domains)
    return {
        "schema": WEB_TEXT_EVIDENCE_SCHEMA,
        "provider": provider,
        "query": query,
        "url": url,
        "title": title,
        "snippet": snippet,
        "matched_handle": "",
        "matched_name": "",
        "source_domain": source_domain(url),
        "source_trust_level": trust,
        "collected_at": "",
        "confidence": 0.35 if trust in {"repost-index", "unknown"} else 0.55,
        "review_required": True,
        "evidence_role": "web_text",
        "limitations": ["Text result only; no face or image comparison performed."],
        "unsafe_untrusted_content": True,
    }


@dataclasses.dataclass(frozen=True)
class TextEvidenceProvider:
    name: str

    def collect(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        raise NotImplementedError


@dataclasses.dataclass(frozen=True)
class UrlGenerationProvider(TextEvidenceProvider):
    provider_filter: str | None = None

    def collect(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        for query in text_verification_queries(candidates):
            if self.provider_filter and query.get("provider") != self.provider_filter:
                continue
            rows.append({**query, "provider": self.name, "result_type": "generated_url"})
        return rows


@dataclasses.dataclass(frozen=True)
class ConfiguredDomainProvider(TextEvidenceProvider):
    domains: tuple[str, ...]

    def collect(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for candidate in candidates:
            variants = candidate.get("variants") or candidate_variants(str(candidate.get("name") or ""), str(candidate.get("raw") or ""))
            for variant in variants[:2]:
                exact = f'"{variant}"'
                for domain in self.domains:
                    query = f"{exact} site:{domain}"
                    key = (domain.lower(), query.lower())
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append(
                        {
                            "provider": self.name,
                            "label": f"Yandex {domain}",
                            "query": query,
                            "url": yandex_search_url(query),
                            "candidate_name": candidate.get("name"),
                            "candidate_source": candidate.get("source"),
                            "evidence_role": "configured_domain_text_search",
                            "text_only": True,
                            "result_type": "generated_url",
                            "source_domain": domain,
                            "source_trust_level": source_trust_level(f"https://{domain}/", set(self.domains)),
                        }
                    )
        return rows


@dataclasses.dataclass(frozen=True)
class MockSearchProvider(TextEvidenceProvider):
    results_by_query: dict[str, list[dict[str, Any]]]
    configured_domains: tuple[str, ...] = ()

    def collect(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        evidence: list[dict[str, Any]] = []
        configured = set(self.configured_domains)
        for query in text_verification_queries(candidates):
            for result in self.results_by_query.get(str(query.get("query") or ""), []):
                evidence.append(
                    normalize_search_result(
                        result,
                        provider=self.name,
                        query=str(query.get("query") or ""),
                        configured_domains=configured,
                    )
                )
        return evidence


def provider_dry_run_packet(candidates: list[dict[str, Any]], providers: list[TextEvidenceProvider]) -> dict[str, Any]:
    return {
        "schema": "media-text-evidence-provider-packet/v1",
        "generated_at": utc_now(),
        "providers": [provider.name for provider in providers],
        "results": [item for provider in providers for item in provider.collect(candidates)],
        "text_only": True,
        "network_executed": False,
        "biometric_boundary": "Providers operate on text candidates only; no web image or face comparison is performed.",
    }


def trace_item(
    signal_type: str,
    value: str,
    source: str,
    confidence: float,
    reason: str,
    *,
    review_required: bool = True,
    source_path: str = "",
) -> dict[str, Any]:
    return {
        "schema": IDENTITY_TRACE_SCHEMA,
        "signal_type": signal_type,
        "value": value,
        "source": source,
        "confidence": round(float(confidence), 2),
        "reason": reason,
        "review_required": review_required,
        "source_path": source_path,
    }


def best_performer_signal(record: dict[str, Any]) -> dict[str, Any] | None:
    performers = [item for item in record.get("performers") or [] if isinstance(item, dict)]
    if not performers:
        return None
    return max(performers, key=lambda item: float(item.get("similarity") or item.get("confidence") or 0))


def best_text_candidate(record: dict[str, Any]) -> dict[str, Any] | None:
    candidates = (record.get("metadata_hints") or {}).get("candidate_names") or []
    candidates = [
        item
        for item in candidates
        if isinstance(item, dict)
        and not item.get("not_performer_name")
        and str(item.get("source") or "") != "site_watermark"
        and not is_bad_candidate_name(str(item.get("name") or ""), str(item.get("raw") or ""))
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: float(item.get("confidence") or 0))


def matching_web_evidence(candidate_name: str, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_key = normalize_identity_key(candidate_name)
    matches: list[dict[str, Any]] = []
    for item in normalize_web_text_evidence(evidence):
        haystack = " ".join(
            str(item.get(field) or "")
            for field in ("matched_handle", "matched_name", "title", "snippet", "url")
        )
        if candidate_key and candidate_key in normalize_identity_key(haystack):
            matches.append(item)
    return matches


def score_assignment(record: dict[str, Any]) -> dict[str, Any]:
    trace: list[dict[str, Any]] = []
    blocking: list[str] = []
    suggested_name = ""
    confidence = 0.0
    auto_allowed = False
    primary_reason = "No strong identity signal was available."

    performer = best_performer_signal(record)
    if performer:
        face_name = str(performer.get("name") or "")
        face_confidence = float(performer.get("similarity") or performer.get("confidence") or 0)
        if face_name and face_name != "unknown performer":
            trace.append(
                trace_item(
                    "local_face",
                    face_name,
                    str(performer.get("model_version") or "local_face_db"),
                    face_confidence,
                    "Local known-performer face comparison.",
                    review_required=face_confidence < HIGH_CONFIDENCE,
                    source_path=str(performer.get("crop_path") or ""),
                )
            )
            if face_confidence >= HIGH_CONFIDENCE and performer.get("status") == "auto":
                suggested_name = face_name
                confidence = max(confidence, face_confidence)
                auto_allowed = True
                primary_reason = "Local user-confirmed face match met the auto threshold."
            elif face_confidence >= POSSIBLE_CONFIDENCE:
                blocking.append("local_face_match_below_auto_threshold")

    text_candidate = best_text_candidate(record)
    if text_candidate:
        text_name = str(text_candidate.get("name") or "")
        text_confidence = float(text_candidate.get("confidence") or 0)
        text_source = str(text_candidate.get("source") or "")
        signal_type = "watermark_profile_url" if text_candidate.get("profile_url") or text_source == "watermark_profile_url" else "ocr_handle"
        trace.append(
            trace_item(
                signal_type,
                text_name,
                text_source,
                text_confidence,
                "Visible in-video text/profile signal.",
                review_required=text_confidence < HIGH_CONFIDENCE,
                source_path=str(text_candidate.get("frame_path") or ""),
            )
        )
        if is_bad_candidate_name(text_name, str(text_candidate.get("raw") or "")):
            blocking.append("host_or_noise_candidate")
        elif signal_type == "watermark_profile_url" and text_confidence >= 0.75 and not suggested_name:
            suggested_name = text_name
            confidence = max(confidence, min(0.86, text_confidence))
            auto_allowed = True
            primary_reason = "Full in-video profile URL/watermark signal was parsed cleanly."
        elif not suggested_name and text_confidence >= 0.55:
            suggested_name = text_name
            confidence = max(confidence, min(0.74, text_confidence))
            blocking.append("ocr_text_requires_review")

    web_matches = matching_web_evidence(suggested_name or (text_candidate or {}).get("name", ""), record.get("web_text_evidence") or [])
    for item in web_matches[:3]:
        trace.append(
            trace_item(
                "web_text",
                str(item.get("matched_name") or item.get("matched_handle") or suggested_name),
                str(item.get("provider") or "web_text"),
                float(item.get("confidence") or 0),
                f"Text result from {item.get('source_trust_level') or 'unknown'} source.",
                review_required=True,
                source_path=str(item.get("url") or ""),
            )
        )
    if web_matches and suggested_name and not auto_allowed:
        best_web_conf = max(float(item.get("confidence") or 0) for item in web_matches)
        confidence = max(confidence, min(0.79, 0.55 + best_web_conf / 4))
        blocking.append("web_text_requires_review")

    if performer and text_candidate:
        face_name = str(performer.get("name") or "")
        text_name = str(text_candidate.get("name") or "")
        face_confidence = float(performer.get("similarity") or performer.get("confidence") or 0)
        if (
            face_name
            and text_name
            and face_name != "unknown performer"
            and normalize_identity_key(face_name) != normalize_identity_key(text_name)
            and face_confidence >= POSSIBLE_CONFIDENCE
        ):
            blocking.append("local_face_text_contradiction")
            auto_allowed = False
            confidence = min(confidence, 0.54)
            primary_reason = "Local face and text signals disagree."

    if suggested_name and is_bad_candidate_name(suggested_name):
        blocking.append("host_or_noise_candidate")
        auto_allowed = False
        confidence = 0.0

    if not suggested_name:
        blocking.append("no_assignable_identity_signal")
    if confidence < HIGH_CONFIDENCE:
        auto_allowed = False
    review_required = bool(blocking) or not auto_allowed
    decision = {
        "schema": ASSIGNMENT_DECISION_SCHEMA,
        "suggested_slug": slugify(suggested_name) if suggested_name else None,
        "suggested_name": suggested_name or None,
        "confidence": round(float(confidence), 2),
        "auto_assign_allowed": bool(auto_allowed and not blocking),
        "review_required": review_required,
        "why": primary_reason,
        "blocking_reasons": sorted(set(blocking)),
        "supporting_signal_ids": [f"{item['signal_type']}:{idx}" for idx, item in enumerate(trace)],
    }
    return {"identity_trace": trace, "assignment_decision": decision}


def apply_assignment_scoring(record: dict[str, Any]) -> dict[str, Any]:
    scored = score_assignment(record)
    updated = dict(record)
    updated["identity_trace"] = scored["identity_trace"]
    updated["assignment_decision"] = scored["assignment_decision"]
    return updated


def text_verification_queries(candidates: Iterable[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    queries: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def add(provider: str, label: str, query: str, url: str, candidate: dict[str, Any], role: str) -> None:
        query = " ".join(str(query or "").split())
        if not query:
            return
        key = (provider, label, query.lower())
        if key in seen:
            return
        seen.add(key)
        queries.append(
            {
                "provider": provider,
                "label": label,
                "query": query,
                "url": url,
                "candidate_name": candidate.get("name"),
                "candidate_source": candidate.get("source"),
                "evidence_role": role,
                "text_only": True,
            }
        )

    for candidate in list(candidates)[:limit]:
        if not isinstance(candidate, dict):
            continue
        variants = candidate.get("variants") or candidate_variants(str(candidate.get("name") or ""), str(candidate.get("raw") or ""))
        for variant in variants[:3]:
            if is_bad_candidate_name(str(variant), str(candidate.get("raw") or variant)):
                continue
            exact = f'"{variant}"'
            add("yandex-url", "Yandex", exact, yandex_search_url(exact), candidate, "manual_text_search")
            add(
                "yandex-url",
                "Yandex OnlyFans",
                f'{exact} onlyfans',
                yandex_search_url(f'{exact} onlyfans'),
                candidate,
                "manual_text_search",
            )
            add(
                "yandex-site-url",
                "Yandex PimpBunny",
                f"{exact} site:pimpbunny.com",
                yandex_search_url(f"{exact} site:pimpbunny.com"),
                candidate,
                "site_scoped_text_search",
            )
            add(
                "yandex-site-url",
                "Yandex Coomer",
                f"{exact} site:coomer.st",
                yandex_search_url(f"{exact} site:coomer.st"),
                candidate,
                "site_scoped_text_search",
            )
            add("coomer-url", "Coomer", str(variant), coomer_search_url(str(variant)), candidate, "site_text_search")
    return queries[: limit * 8]


def build_metadata_hints(video_path: Path, enable_online: bool, frame_paths: list[Path] | None = None, ocr_watermarks: bool = False) -> dict[str, Any]:
    filename_candidates = extract_filename_candidates(video_path)
    ocr_results = ocr_frame_text(frame_paths or []) if ocr_watermarks else []
    ocr_candidates = watermark_candidates(ocr_results)
    online_candidates: list[dict[str, Any]] = []
    if enable_online:
        for candidate in (ocr_candidates + filename_candidates)[:3]:
            online_candidates.extend(lookup_papi_candidates(candidate["name"]))
    all_candidates = dedupe_rank_candidates(ocr_candidates + filename_candidates + online_candidates)
    return {
        "generated_at": utc_now(),
        "status": "candidate_hints_only",
        "candidate_names": all_candidates[:10],
        "text_verification_queries": text_verification_queries(all_candidates[:10]),
        "watermark_ocr": ocr_results[:20],
        "providers": {
            "filename": {"enabled": True},
            "watermark_ocr": {"enabled": ocr_watermarks, "configured": bool(ocr_results or frame_paths)},
            "papi": {"enabled": enable_online, "configured": bool(os.environ.get("PAPI_RAPIDAPI_KEY"))},
            "apify": {"enabled": False, "reason": "provider hook reserved; needs explicit token and dataset mapping"},
            "ofauth": {"enabled": False, "reason": "provider hook reserved for authorized account metadata only"},
        },
        "biometric_boundary": "Internet metadata is not imported as face identity. Confirm a local crop before adding embeddings.",
    }


def json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def smart_rescan_status_path() -> Path | None:
    raw_path = os.environ.get("SPIRITFLIX_SMART_RESCAN_STATUS_PATH", "").strip()
    return Path(raw_path) if raw_path else None


def write_smart_rescan_status(update: dict[str, Any]) -> None:
    path = smart_rescan_status_path()
    if not path:
        return
    current = load_json(path, {}) if path.exists() else {}
    payload = {
        "schema": "spiritflix-library-smart-rescan-status/v1",
        "status": "running",
        **current,
        **update,
        "updatedAt": utc_now(),
    }
    json_dump(path, payload)


def np_save_atomic(path: Path, payload: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            np.save(handle, payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


def np_load_with_retry(path: Path, *, attempts: int = 5, delay_seconds: float = 0.08) -> np.ndarray:
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            return np.load(path)
        except (EOFError, ValueError, OSError) as exc:
            last_exc = exc
            if attempt + 1 >= attempts:
                break
            time.sleep(delay_seconds)
    assert last_exc is not None
    raise last_exc


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item).strip()]


def normalize_web_text_evidence(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        trust_level = str(item.get("source_trust_level") or "unknown")
        if trust_level not in SOURCE_TRUST_LEVELS:
            trust_level = "unknown"
        confidence = item.get("confidence")
        normalized.append(
            {
                "schema": str(item.get("schema") or WEB_TEXT_EVIDENCE_SCHEMA),
                "provider": str(item.get("provider") or ""),
                "query": str(item.get("query") or ""),
                "url": str(item.get("url") or ""),
                "title": str(item.get("title") or ""),
                "snippet": str(item.get("snippet") or ""),
                "matched_handle": str(item.get("matched_handle") or ""),
                "matched_name": str(item.get("matched_name") or ""),
                "source_domain": str(item.get("source_domain") or ""),
                "source_trust_level": trust_level,
                "collected_at": str(item.get("collected_at") or ""),
                "confidence": float(confidence) if isinstance(confidence, (int, float)) else None,
                "review_required": bool(item.get("review_required", True)),
                "evidence_role": str(item.get("evidence_role") or "corroboration"),
                "limitations": _string_list(item.get("limitations")),
                "unsafe_untrusted_content": bool(item.get("unsafe_untrusted_content", True)),
            }
        )
    return normalized


def normalize_identity_trace(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        confidence = item.get("confidence")
        normalized.append(
            {
                "schema": str(item.get("schema") or IDENTITY_TRACE_SCHEMA),
                "signal_type": str(item.get("signal_type") or ""),
                "value": str(item.get("value") or ""),
                "source": str(item.get("source") or ""),
                "confidence": float(confidence) if isinstance(confidence, (int, float)) else None,
                "reason": str(item.get("reason") or ""),
                "review_required": bool(item.get("review_required", True)),
                "source_path": str(item.get("source_path") or ""),
            }
        )
    return normalized


def blank_assignment_decision() -> dict[str, Any]:
    return {
        "schema": ASSIGNMENT_DECISION_SCHEMA,
        "suggested_slug": None,
        "suggested_name": None,
        "confidence": 0.0,
        "auto_assign_allowed": False,
        "review_required": True,
        "why": "",
        "blocking_reasons": [],
        "supporting_signal_ids": [],
    }


def normalize_assignment_decision(value: Any) -> dict[str, Any]:
    decision = blank_assignment_decision()
    if not isinstance(value, dict):
        return decision
    decision["schema"] = str(value.get("schema") or ASSIGNMENT_DECISION_SCHEMA)
    for field in ("suggested_slug", "suggested_name", "why"):
        if value.get(field) is not None:
            decision[field] = str(value.get(field))
    confidence = value.get("confidence")
    if isinstance(confidence, (int, float)):
        decision["confidence"] = float(confidence)
    decision["auto_assign_allowed"] = bool(value.get("auto_assign_allowed", False))
    decision["review_required"] = bool(value.get("review_required", True))
    decision["blocking_reasons"] = _string_list(value.get("blocking_reasons"))
    decision["supporting_signal_ids"] = _string_list(value.get("supporting_signal_ids"))
    return decision


def identity_schema_fields(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "web_text_evidence": normalize_web_text_evidence(record.get("web_text_evidence")),
        "identity_trace": normalize_identity_trace(record.get("identity_trace")),
        "assignment_decision": normalize_assignment_decision(record.get("assignment_decision")),
    }


def summarize_web_text_evidence(items: list[dict[str, Any]]) -> dict[str, Any]:
    trust_counts: dict[str, int] = {}
    providers: set[str] = set()
    review_required = False
    for item in normalize_web_text_evidence(items):
        trust_level = str(item.get("source_trust_level") or "unknown")
        trust_counts[trust_level] = trust_counts.get(trust_level, 0) + 1
        if item.get("provider"):
            providers.add(str(item.get("provider")))
        review_required = review_required or bool(item.get("review_required"))
    return {
        "schema": WEB_TEXT_EVIDENCE_SCHEMA,
        "count": sum(trust_counts.values()),
        "providers": sorted(providers),
        "source_trust_counts": dict(sorted(trust_counts.items())),
        "review_required": review_required,
    }


def model_index_entry(slug: str, entry: dict[str, Any]) -> dict[str, Any]:
    decision = normalize_assignment_decision(entry.get("assignment_decision"))
    web_count = int((entry.get("web_text_evidence_summary") or {}).get("count") or 0)
    trace_count = int((entry.get("identity_trace_summary") or {}).get("count") or 0)
    if web_count:
        primary_evidence_role = "web_text"
    elif trace_count:
        primary_evidence_role = "identity_trace"
    else:
        primary_evidence_role = entry.get("status", "needs-review")
    row = {
        "name": entry.get("name"),
        "slug": slug,
        "aliases": entry.get("aliases", []),
        "status": entry.get("status", "needs-review"),
        "video_count": entry.get("video_count", 0),
        "profile_handles": entry.get("profile_handles", []),
        "assignment_status": "auto" if decision.get("auto_assign_allowed") else entry.get("status", "needs-review"),
        "identity_confidence": decision.get("confidence"),
        "primary_evidence_role": primary_evidence_role,
        "review_required": decision.get("review_required"),
        "why": decision.get("why"),
    }
    if entry.get("faceless") or entry.get("face_enrollment_status") == "faceless":
        row["faceless"] = True
        row["face_enrollment_status"] = "faceless"
        row["faceless_confirmed_by"] = entry.get("faceless_confirmed_by")
        row["faceless_confirmed_at"] = entry.get("faceless_confirmed_at")
    return row


def require_ffmpeg() -> None:
    for binary in ("ffmpeg", "ffprobe"):
        if shutil.which(binary) is None:
            raise RuntimeError(f"{binary} is required on PATH for frame extraction")


class KnownPerformersDB:
    def __init__(self, db_dir: Path) -> None:
        self.db_dir = db_dir
        self.index_path = db_dir / "index.json"
        self.embeddings_path = db_dir / "embeddings.npy"
        self.map_path = db_dir / "performer_map.json"
        self.faces_dir = db_dir / "faces"
        self.index: dict[str, Any] = {"performers": []}
        self.performer_map: dict[str, str] = {}
        self.embeddings = np.empty((0, 512), dtype=np.float32)

    def ensure(self) -> None:
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.faces_dir.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            json_dump(self.index_path, {"performers": []})
        if not self.map_path.exists():
            json_dump(self.map_path, {})
        if not self.embeddings_path.exists():
            np_save_atomic(self.embeddings_path, self.embeddings)

    def load(self) -> None:
        self.ensure()
        self.index = load_json(self.index_path, {"performers": []})
        self.performer_map = load_json(self.map_path, {})
        try:
            self.embeddings = np_load_with_retry(self.embeddings_path)
        except Exception as exc:
            raise RuntimeError(f"Could not load embeddings index at {self.embeddings_path}: {exc}") from exc
        if self.embeddings.ndim != 2:
            raise RuntimeError(f"Embeddings index must be 2D, got shape {self.embeddings.shape}")

    def performer_by_id(self) -> dict[str, dict[str, Any]]:
        return {item["id"]: item for item in self.index.get("performers", [])}

    def add_performer(self, name: str, aliases: list[str] | None = None) -> str:
        self.load()
        performers = self.index.setdefault("performers", [])
        existing = {item["id"] for item in performers}
        performer_id = slugify(name)
        if performer_id in existing:
            for item in performers:
                if item.get("id") != performer_id:
                    continue
                alias_set = {str(alias) for alias in item.get("aliases", []) if alias}
                alias_set.update(str(alias) for alias in aliases or [] if alias)
                item["aliases"] = sorted(alias_set, key=str.lower)
                json_dump(self.index_path, self.index)
            return performer_id
        suffix = 2
        base_id = performer_id
        while performer_id in existing:
            performer_id = f"{base_id}-{suffix}"
            suffix += 1
        performers.append(
            {
                "id": performer_id,
                "name": name.strip(),
                "aliases": aliases or [],
                "added_at": utc_now(),
            }
        )
        json_dump(self.index_path, self.index)
        (self.faces_dir / performer_id).mkdir(parents=True, exist_ok=True)
        return performer_id

    def record_enrollment(
        self,
        performer_id: str,
        sample_path: Path,
        *,
        confirmed_by: str,
        aliases: list[str] | None = None,
        profile_handles: list[dict[str, str]] | None = None,
        profile_urls: list[str] | None = None,
        source_crop: str = "",
        source_video: str = "",
        source_timestamp: Any = None,
        embedding_rows: list[int] | None = None,
    ) -> None:
        self.load()
        for item in self.index.setdefault("performers", []):
            if item.get("id") != performer_id:
                continue
            alias_set = {str(alias) for alias in item.get("aliases", []) if alias}
            alias_set.update(str(alias) for alias in aliases or [] if alias)
            item["aliases"] = sorted(alias_set, key=str.lower)
            item["profile_handles"] = profile_handles or item.get("profile_handles", [])
            item["profile_urls"] = profile_urls or item.get("profile_urls", [])
            item["confirmed_by"] = confirmed_by
            item["confirmed_at"] = utc_now()
            item.setdefault("enrolled_face_samples", []).append(str(sample_path))
            sample_records = item.setdefault("enrolled_face_sample_records", [])
            if isinstance(sample_records, list):
                sample_records.append(
                    {
                        "sample_path": str(sample_path),
                        "source_crop": source_crop,
                        "source_video": source_video,
                        "source_timestamp": source_timestamp,
                        "embedding_rows": embedding_rows or [],
                        "confirmed_by": confirmed_by,
                        "confirmed_at": utc_now(),
                    }
                )
            item.setdefault("audit_events", []).append(
                {
                    "event": "confirmed_crop_enrolled",
                    "at": utc_now(),
                    "confirmed_by": confirmed_by,
                    "sample_path": str(sample_path),
                    "source_crop": source_crop,
                    "source_video": source_video,
                    "source_timestamp": source_timestamp,
                    "embedding_rows": embedding_rows or [],
                    "limitations": "Local crop enrollment only; no web image or internet face comparison was used.",
                }
            )
            json_dump(self.index_path, self.index)
            return

    def append_embedding(self, performer_id: str, embedding: np.ndarray) -> int:
        self.load()
        embedding = normalize_embedding(embedding).astype(np.float32)
        if self.embeddings.size == 0:
            self.embeddings = embedding.reshape(1, -1)
        else:
            if self.embeddings.shape[1] != embedding.shape[0]:
                raise RuntimeError(
                    f"Embedding dimension mismatch: index has {self.embeddings.shape[1]}, new face has {embedding.shape[0]}"
                )
            self.embeddings = np.vstack([self.embeddings, embedding.reshape(1, -1)])
        row = str(len(self.embeddings) - 1)
        self.performer_map[row] = performer_id
        np_save_atomic(self.embeddings_path, self.embeddings.astype(np.float32))
        json_dump(self.map_path, self.performer_map)
        return int(row)

    def remove_enrolled_samples(self, performer_id: str, sample_paths: list[str]) -> dict[str, Any]:
        self.load()
        wanted = {str(path) for path in sample_paths if str(path)}
        removed_rows: set[int] = set()
        removed_samples: list[str] = []
        for item in self.index.setdefault("performers", []):
            if item.get("id") != performer_id:
                continue
            item["enrolled_face_samples"] = [
                str(path)
                for path in item.get("enrolled_face_samples", []) or []
                if str(path) not in wanted
            ]
            removed_set = {str(path) for path in item.get("removed_face_samples", []) or []}
            removed_set.update(wanted)
            item["removed_face_samples"] = sorted(removed_set)
            kept_records = []
            for record in item.get("enrolled_face_sample_records", []) or []:
                if not isinstance(record, dict):
                    continue
                sample_path = str(record.get("sample_path") or "")
                if sample_path in wanted:
                    removed_samples.append(sample_path)
                    for row in record.get("embedding_rows") or []:
                        try:
                            removed_rows.add(int(row))
                        except Exception:
                            pass
                    continue
                kept_records.append(record)
            item["enrolled_face_sample_records"] = kept_records
            item.setdefault("audit_events", []).append(
                {
                    "event": "enrolled_sample_removed",
                    "at": utc_now(),
                    "sample_paths": sorted(wanted),
                    "embedding_rows_removed": sorted(removed_rows),
                }
            )
            break
        if removed_rows and self.embeddings.size:
            keep_indexes = [idx for idx in range(int(self.embeddings.shape[0])) if idx not in removed_rows]
            self.embeddings = self.embeddings[keep_indexes, :] if keep_indexes else np.empty((0, self.embeddings.shape[1]), dtype=np.float32)
            row_shift = {}
            for new_idx, old_idx in enumerate(keep_indexes):
                row_shift[str(old_idx)] = str(new_idx)
            self.performer_map = {
                row_shift[str(old_row)]: performer_id_value
                for old_row, performer_id_value in self.performer_map.items()
                if str(old_row) in row_shift
            }
            np_save_atomic(self.embeddings_path, self.embeddings.astype(np.float32))
            json_dump(self.map_path, self.performer_map)
        json_dump(self.index_path, self.index)
        return {
            "removed_samples": removed_samples or sorted(wanted),
            "embedding_rows_removed": sorted(removed_rows),
        }

    def match(self, embedding: np.ndarray) -> Match:
        if self.embeddings.size == 0:
            return build_match(None, "unknown performer", 0.0)
        normalized = normalize_embedding(embedding)
        scores = self.embeddings @ normalized
        best_index = int(np.argmax(scores))
        similarity = float(scores[best_index])
        performer_id = self.performer_map.get(str(best_index))
        performer = self.performer_by_id().get(performer_id or "", {})
        name = performer.get("name") or "unknown performer"
        return build_match(performer_id, name, similarity)


def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    vector = np.asarray(embedding, dtype=np.float32).reshape(-1)
    norm = float(np.linalg.norm(vector))
    if norm == 0:
        return vector
    return vector / norm


def build_match(performer_id: str | None, name: str, similarity: float) -> Match:
    if similarity >= HIGH_CONFIDENCE and performer_id:
        return Match(performer_id, name, similarity, "auto", False, f"{name} ({safe_percent(similarity)} confidence)")
    if similarity >= POSSIBLE_CONFIDENCE and performer_id:
        return Match(
            performer_id,
            name,
            similarity,
            "possible",
            True,
            f"possible: {name} ({safe_percent(similarity)} confidence) - verification needed",
        )
    return Match(None, "unknown performer", similarity, "unknown", True, "unknown performer - verification needed")


def normalize_identity_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


SEED_PERFORMER_ALIASES: dict[str, str] = {
    "siennaababi": "Sienna Ababi",
    "siennaabab": "Sienna Ababi",
    "slennaababi": "Sienna Ababi",
    "sienaabbi": "Sienna Ababi",
    "gemthejewels": "Gem The Jewels",
    "gemthejewls": "Gem The Jewels",
    "gemthejewels": "Gem The Jewels",
    "cutelittlepearl": "Cute Geekie",
    "cutegeekie": "Cute Geekie",
    "cutegeeky": "Cute Geekie",
    "cutegeek": "Cute Geekie",
    "jazmenjafar": "Jazmen Jafar",
    "jazmenjarfar": "Jazmen Jafar",
    "jazmanjafar": "Jazmen Jafar",
    "jakarababy": "Jakara Mitchell",
    "jakaramitchell": "Jakara Mitchell",
    "karamito": "Jakara Mitchell",
    "karamite": "Jakara Mitchell",
    "aaliyahyasan": "Aaliyah Yasan",
    "thatbritishgirl": "Aaliyah Yasan",
    "angetawhite": "Angela White",
    "savaschultz": "Sava Schultz",
    "savasch": "Sava Schultz",
    "savaschu": "Sava Schultz",
    "savaschyltz": "Sava Schultz",
    "savaschuilitz": "Sava Schultz",
    "savaschuiltz": "Sava Schultz",
    "savaschult": "Sava Schultz",
    "savaschulz": "Sava Schultz",
    "savash": "Sava Schultz",
    "ruthlce": "Ruth Lee",
    "ruthlee": "Ruth Lee",
    "pinkychu": "Pinkychu",
    "pinkychi": "Pinkychu",
    "mackzjones": "Mackzjones",
    "misslilu": "Miss LiLu",
    "lilushandjobs": "Miss LiLu",
    "sendnudesx": "Sendnudesx",
    "sendnueesx": "Sendnudesx",
    "whoahannahjo": "Whoahannahjo",
    "kinkykttn": "Kinkykttn",
    "kinkyktn": "Kinkykttn",
    "alannasworldx": "Alannasworldx",
    "alannasworlx": "Alannasworldx",
    "olenfromalannasworldx": "Alannasworldx",
    "tolenfromalannasworldx": "Alannasworldx",
    "stolentromalannasworldx": "Alannasworldx",
    "puffypink": "Puffy Pink",
}


TRUSTED_PROFILE_HANDLES = {
    "aaliyahyasan",
    "alannasworldx",
    "alannasworlx",
    "cutegeekie",
    "cutelittlepearl",
    "gemthejewels",
    "izzygreen",
    "jakaramitchell",
    "jakarababy",
    "jazmenjafar",
    "kinkykttn",
    "mackzjones",
    "misslilu",
    "pinkychu",
    "puffypink",
    "ruthlee",
    "savaschultz",
    "sendnudes",
    "sendnudesx",
    "sienna",
    "siennaababi",
    "whoahannahjo",
}


def blank_performer_registry() -> dict[str, Any]:
    return {
        "schema": "media-performer-verification/v1",
        "generated_at": utc_now(),
        "updated_at": utc_now(),
        "performers": {},
        "aliases": dict(SEED_PERFORMER_ALIASES),
        "rules": {
            "verified_identity_sources": ["user_correction", "profile_url", "local_face_db"],
            "non_identity_sources": ["site_watermark", "telegram_repost", "filename_only"],
            "note": "This registry stores text/profile evidence only; it does not perform internet face identification.",
        },
        "optional_schemas": {
            "web_text_evidence": WEB_TEXT_EVIDENCE_SCHEMA,
            "identity_trace": IDENTITY_TRACE_SCHEMA,
            "assignment_decision": ASSIGNMENT_DECISION_SCHEMA,
        },
    }


def load_performer_registry(path: Path) -> dict[str, Any]:
    registry = load_json(path, blank_performer_registry())
    if not isinstance(registry, dict):
        registry = blank_performer_registry()
    registry.setdefault("schema", "media-performer-verification/v1")
    registry.setdefault("generated_at", utc_now())
    registry.setdefault("performers", {})
    registry.setdefault(
        "optional_schemas",
        {
            "web_text_evidence": WEB_TEXT_EVIDENCE_SCHEMA,
            "identity_trace": IDENTITY_TRACE_SCHEMA,
            "assignment_decision": ASSIGNMENT_DECISION_SCHEMA,
        },
    )
    aliases = registry.setdefault("aliases", {})
    for key, value in SEED_PERFORMER_ALIASES.items():
        aliases.setdefault(key, value)
    return registry


def registry_aliases(registry: dict[str, Any] | None) -> dict[str, str]:
    aliases = dict(SEED_PERFORMER_ALIASES)
    if registry:
        for key, value in (registry.get("aliases") or {}).items():
            if isinstance(key, str) and isinstance(value, str):
                aliases[normalize_identity_key(key)] = value
    return aliases


def canonical_performer_name(name: str, registry: dict[str, Any] | None = None) -> str:
    cleaned = split_handle_words(name)
    aliases = registry_aliases(registry)
    key = normalize_identity_key(cleaned or name)
    if key in aliases:
        return aliases[key]
    for performer in (registry or {}).get("performers", {}).values():
        if not isinstance(performer, dict):
            continue
        canonical = str(performer.get("name") or "")
        if not canonical:
            continue
        keys = {normalize_identity_key(canonical), normalize_identity_key(str(performer.get("slug") or ""))}
        keys.update(normalize_identity_key(str(alias)) for alias in performer.get("aliases", []) if isinstance(alias, str))
        if key in keys:
            return canonical
    return cleaned


def profile_handles_from_hints(metadata_hints: dict[str, Any]) -> list[dict[str, str]]:
    handles: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for item in metadata_hints.get("candidate_names", []):
        if item.get("platform") and item.get("handle"):
            platform = str(item.get("platform")).lower()
            handle = str(item.get("handle")).strip("._-")
            key = (platform, handle.lower())
            if key not in seen:
                seen.add(key)
                handles.append(
                    {
                        "platform": platform,
                        "handle": handle,
                        "url": str(item.get("profile_url") or f"https://{platform}.com/{handle}"),
                        "source": str(item.get("source") or "watermark_ocr"),
                        "raw": str(item.get("raw") or ""),
                    }
                )
        raw = str(item.get("raw") or "")
        for mention in profile_mentions_from_text(raw):
            platform = mention["platform"]
            handle = mention["handle"]
            key = (platform, handle.lower())
            if key in seen:
                continue
            seen.add(key)
            handles.append(
                {
                    "platform": platform,
                    "handle": handle,
                    "url": mention["url"],
                    "source": str(item.get("source") or "watermark_ocr"),
                    "raw": raw,
                }
            )
    return handles


def parse_profile_handle(value: str) -> dict[str, str]:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("profile handle cannot be empty")
    url_match = re.match(r"https?://(?:www\.)?(onlyfans|fansly|fanvue)\.com/([A-Za-z0-9_.-]{4,})", raw, re.I)
    if url_match:
        platform = url_match.group(1).lower()
        handle = url_match.group(2).strip("._-")
        return {"platform": platform, "handle": handle, "url": f"https://{platform}.com/{handle}"}
    if ":" in raw:
        platform, handle = raw.split(":", 1)
    elif "/" in raw:
        platform, handle = raw.split("/", 1)
    else:
        platform, handle = "onlyfans", raw
    platform = platform.strip().lower()
    handle = re.sub(r"[^A-Za-z0-9_.-].*$", "", handle).strip("._-")
    if platform not in {"onlyfans", "fansly", "fanvue"}:
        raise ValueError(f"unsupported profile platform: {platform}")
    if not handle or is_bad_candidate_name(handle, raw):
        raise ValueError(f"unsafe profile handle: {raw}")
    return {"platform": platform, "handle": handle, "url": f"https://{platform}.com/{handle}"}


def parse_profile_handles(values: Iterable[str] | None) -> list[dict[str, str]]:
    handles: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for value in values or []:
        handle = parse_profile_handle(value)
        key = (handle["platform"], handle["handle"].lower())
        if key not in seen:
            seen.add(key)
            handles.append(handle)
    return handles


def update_registry_enrollment(
    registry_path: Path,
    name: str,
    performer_id: str,
    sample_path: Path,
    *,
    confirmed_by: str,
    aliases: list[str],
    profile_handles: list[dict[str, str]],
    profile_urls: list[str],
) -> None:
    registry = load_performer_registry(registry_path)
    slug = slugify(name)
    entry = registry.setdefault("performers", {}).setdefault(
        slug,
        {
            "name": name,
            "slug": slug,
            "aliases": [],
            "profile_handles": [],
            "status": "user-confirmed",
            "evidence": [],
            "video_count": 0,
        },
    )
    entry["name"] = name
    entry["slug"] = slug
    entry["status"] = "user-confirmed"
    entry["confirmed_by"] = confirmed_by
    entry["confirmed_at"] = utc_now()
    alias_set = {str(alias) for alias in entry.get("aliases", []) if alias}
    alias_set.update(alias for alias in aliases if alias)
    entry["aliases"] = sorted(alias_set, key=str.lower)
    for alias in entry["aliases"]:
        registry.setdefault("aliases", {})[normalize_identity_key(alias)] = name
    handle_seen = {(item.get("platform"), str(item.get("handle", "")).lower()) for item in entry.get("profile_handles", [])}
    for handle in profile_handles:
        key = (handle["platform"], handle["handle"].lower())
        if key not in handle_seen:
            entry.setdefault("profile_handles", []).append(handle)
            handle_seen.add(key)
    url_seen = {str(item) for item in entry.get("profile_urls", [])}
    for url in profile_urls:
        if url and url not in url_seen:
            entry.setdefault("profile_urls", []).append(url)
            url_seen.add(url)
    entry.setdefault("enrolled_face_samples", []).append(str(sample_path))
    entry.setdefault("audit_events", []).append(
        {
            "event": "confirmed_crop_enrolled",
            "at": utc_now(),
            "confirmed_by": confirmed_by,
            "performer_id": performer_id,
            "sample_path": str(sample_path),
            "limitations": "Local crop enrollment only; no web image or internet face comparison was used.",
        }
    )
    registry["updated_at"] = utc_now()
    json_dump(registry_path, registry)


def update_registry_entry(
    registry: dict[str, Any],
    canonical_name: str,
    alias_names: Iterable[str],
    record: dict[str, Any],
) -> None:
    if not canonical_name or canonical_name == "unknown performer":
        return
    slug = slugify(canonical_name)
    performers = registry.setdefault("performers", {})
    entry = performers.setdefault(
        slug,
        {
            "name": canonical_name,
            "slug": slug,
            "aliases": [],
            "profile_handles": [],
            "status": "needs-review",
            "evidence": [],
            "web_text_evidence_summary": summarize_web_text_evidence([]),
            "identity_trace_summary": {"schema": IDENTITY_TRACE_SCHEMA, "count": 0, "review_required": True},
            "assignment_decision": blank_assignment_decision(),
            "confirmed_by": None,
            "confirmed_at": None,
            "enrolled_face_samples": [],
            "audit_events": [],
            "video_count": 0,
        },
    )
    entry["name"] = canonical_name
    entry["slug"] = slug
    alias_set = {str(alias) for alias in entry.get("aliases", []) if alias}
    for alias in alias_names:
        if alias and normalize_identity_key(alias) != normalize_identity_key(canonical_name):
            alias_set.add(str(alias))
            registry.setdefault("aliases", {})[normalize_identity_key(alias)] = canonical_name
    entry["aliases"] = sorted(alias_set, key=str.lower)
    if not record.get("_folder_alias_only"):
        entry["video_count"] = int(entry.get("video_count") or 0) + 1

    hints = record.get("metadata_hints") or {}
    handle_set = {(item.get("platform"), str(item.get("handle", "")).lower()) for item in entry.get("profile_handles", [])}
    for handle in profile_handles_from_hints(hints):
        handle_key = normalize_identity_key(handle["handle"])
        canonical_key = normalize_identity_key(canonical_name)
        handle_name = canonical_performer_name(handle["handle"], registry)
        if handle_key != canonical_key and handle_key not in TRUSTED_PROFILE_HANDLES:
            continue
        if normalize_identity_key(handle_name) != canonical_key:
            continue
        key = (handle["platform"], handle["handle"].lower())
        if key not in handle_set:
            entry.setdefault("profile_handles", []).append(handle)
            handle_set.add(key)

    signals: set[str] = set()
    for performer in record.get("performers") or []:
        if isinstance(performer, dict):
            signals.update(str(signal) for signal in performer.get("source_signals", []) if signal)
    if "user_correction" in signals:
        entry["status"] = "user-confirmed"
    elif entry.get("profile_handles"):
        entry["status"] = "profile-url"
    elif any((p.get("status") == "auto" and not p.get("verification_needed")) for p in record.get("performers") or [] if isinstance(p, dict)):
        entry["status"] = "local-auto"

    evidence = entry.setdefault("evidence", [])
    video_path = str(record.get("video_path") or record.get("path") or "")
    schema_fields = identity_schema_fields(record)
    web_summary = summarize_web_text_evidence(schema_fields["web_text_evidence"])
    if web_summary["count"]:
        entry["web_text_evidence_summary"] = web_summary
    entry.setdefault("web_text_evidence_summary", summarize_web_text_evidence([]))
    trace_count = len(schema_fields["identity_trace"])
    if trace_count:
        entry["identity_trace_summary"] = {
            "schema": IDENTITY_TRACE_SCHEMA,
            "count": trace_count,
            "review_required": any(item.get("review_required") for item in schema_fields["identity_trace"]),
        }
    entry.setdefault("identity_trace_summary", {"schema": IDENTITY_TRACE_SCHEMA, "count": 0, "review_required": True})
    if "assignment_decision" in record:
        entry["assignment_decision"] = schema_fields["assignment_decision"]
    else:
        entry.setdefault("assignment_decision", schema_fields["assignment_decision"])
    entry.setdefault("confirmed_by", None)
    entry.setdefault("confirmed_at", None)
    entry.setdefault("enrolled_face_samples", [])
    entry.setdefault("audit_events", [])
    for candidate in (hints.get("candidate_names") or [])[:5]:
        if not isinstance(candidate, dict):
            continue
        source = str(candidate.get("source") or "")
        if not source.startswith("watermark_ocr"):
            continue
        evidence_key = (video_path, source, str(candidate.get("raw") or candidate.get("name") or ""))
        if any((item.get("video_path"), item.get("source"), item.get("raw")) == evidence_key for item in evidence):
            continue
        evidence.append(
            {
                "video_path": video_path,
                "source": source,
                "name": candidate.get("name"),
                "raw": candidate.get("raw"),
                "confidence": candidate.get("confidence"),
                "frame_path": candidate.get("frame_path"),
            }
        )
    entry["evidence"] = evidence[-20:]


def canonicalize_record(record: dict[str, Any], registry: dict[str, Any], source_dir: Path) -> tuple[dict[str, Any], bool]:
    changed = False
    performers = record.get("performers") or []
    new_performers: list[dict[str, Any]] = []
    for performer in performers:
        if not isinstance(performer, dict):
            continue
        original_name = str(performer.get("name") or "")
        if not original_name or original_name == "unknown performer":
            new_performers.append(performer)
            continue
        canonical = canonical_performer_name(original_name, registry)
        new_performer = dict(performer)
        if canonical and canonical != original_name:
            new_performer["name"] = canonical
            new_performer["id"] = slugify(canonical)
            label = str(new_performer.get("label") or "")
            if label:
                new_performer["label"] = re.sub(re.escape(original_name), canonical, label, count=1)
            changed = True
        new_performers.append(new_performer)
        update_registry_entry(registry, canonical or original_name, [original_name], record)
    if new_performers != performers:
        record["performers"] = new_performers
    identity = record.get("identity_resolution")
    if isinstance(identity, dict):
        original_name = str(identity.get("name") or "")
        canonical = canonical_performer_name(original_name, registry)
        if canonical and canonical != original_name:
            identity["name"] = canonical
            changed = True
    if record.get("performers"):
        record["suggested_organization"] = suggested_org(record["performers"], source_dir)
    return record, changed


def best_watermark_hint(metadata_hints: dict[str, Any]) -> dict[str, Any] | None:
    candidates = []
    for item in metadata_hints.get("candidate_names", []):
        if not str(item.get("source", "")).startswith("watermark_ocr"):
            continue
        name = split_handle_words(str(item.get("name") or ""))
        if is_bad_candidate_name(name, str(item.get("raw") or item.get("name") or "")):
            continue
        candidate = dict(item)
        candidate["name"] = name
        candidates.append(candidate)
    if not candidates:
        return None

    def priority(item: dict[str, Any]) -> float:
        raw = str(item.get("raw") or "")
        source = str(item.get("source") or "")
        full_profile = bool(re.search(r"(?:onlyfans|lyfans|fansly|fans|of|fanvue)\.com/", raw, re.I))
        score = float(item.get("confidence", 0))
        if full_profile:
            score += 0.28
        if source == "watermark_ocr":
            score += 0.16
        if source == "watermark_ocr_text":
            score -= 0.18
        return score

    return max(candidates, key=priority)


def apply_combined_identity(meta: dict[str, Any], source_dir: Path) -> dict[str, Any]:
    hints = meta.get("metadata_hints") or {}
    watermark = best_watermark_hint(hints)
    if not watermark:
        return meta
    watermark_name = str(watermark.get("name") or "").strip()
    watermark_conf = float(watermark.get("confidence", 0))
    key = normalize_identity_key(watermark_name)
    performers = meta.get("performers") or []
    face_agreement = None
    for performer in performers:
        if normalize_identity_key(str(performer.get("name", ""))) == key:
            face_agreement = performer
            break
    face_similarity = float(face_agreement.get("similarity", 0)) if face_agreement else 0.0
    full_profile_watermark = bool(re.search(r"(?:onlyfans|lyfans|fansly|fans|of|fanvue)\.com/", str(watermark.get("raw", "")), re.I))
    if not watermark_name or (not full_profile_watermark and not face_agreement):
        return meta
    if watermark_conf < HIGH_CONFIDENCE and not (full_profile_watermark and watermark_conf >= 0.75):
        return meta
    auto_approve = bool(face_agreement and face_similarity >= POSSIBLE_CONFIDENCE) or (full_profile_watermark and watermark_conf >= 0.75)
    combined_confidence = min(0.99, max(watermark_conf, (watermark_conf * 0.72) + (face_similarity * 0.38)))
    meta["identity_resolution"] = {
        "name": watermark_name,
        "status": "auto" if auto_approve else "probable",
        "combined_confidence": round(combined_confidence, 3),
        "verification_needed": not auto_approve,
        "signals": {
            "watermark_ocr": {
                "confidence": round(watermark_conf, 3),
                "raw": watermark.get("raw"),
                "frame_path": watermark.get("frame_path"),
            },
            "face_match": {
                "similarity": round(face_similarity, 3),
                "status": face_agreement.get("status") if face_agreement else "none",
            },
        },
    }
    if auto_approve:
        resolved = {
            "id": slugify(watermark_name),
            "name": watermark_name,
            "confidence": round(combined_confidence, 4),
            "similarity": round(face_similarity, 4),
            "status": "auto",
            "verification_needed": False,
            "label": f"{watermark_name} ({round(combined_confidence * 100)}% combined confidence)",
            "face_crop_path": face_agreement.get("face_crop_path") if face_agreement else None,
            "original_frame_path": face_agreement.get("original_frame_path") if face_agreement else None,
            "model_version": meta.get("model_version"),
            "supporting_faces": face_agreement.get("supporting_faces", 0) if face_agreement else 0,
            "source_signals": ["watermark_ocr", "face_match"] if face_agreement else ["watermark_ocr"],
        }
        meta["performers"] = [resolved] + [
            item
            for item in performers
            if normalize_identity_key(str(item.get("name", ""))) != key and item.get("status") != "unknown"
        ]
        meta["verification_needed"] = any(item.get("verification_needed") for item in meta["performers"])
    meta["suggested_organization"] = suggested_org(meta.get("performers", []), source_dir)
    return meta


class InsightFaceRecognizer:
    def __init__(self, model_name: str, ctx_id: int, det_size: tuple[int, int]) -> None:
        try:
            from insightface.app import FaceAnalysis
            import cv2
            from PIL import Image
        except ImportError as exc:
            raise RuntimeError(
                "Missing face-recognition dependencies. Install with: "
                'pip install insightface "onnxruntime-gpu[cuda,cudnn]" numpy pillow opencv-python-headless tqdm'
            ) from exc
        self.cv2 = cv2
        self.image_cls = Image
        self.model_name = model_name
        providers = ["CPUExecutionProvider"] if ctx_id < 0 else ["CUDAExecutionProvider", "CPUExecutionProvider"]
        self.app = FaceAnalysis(name=model_name, providers=providers)
        try:
            self.app.prepare(ctx_id=ctx_id, det_size=det_size)
        except Exception as exc:
            raise RuntimeError(
                f"InsightFace model '{model_name}' could not initialize. "
                "If this is the first run, check internet/model-cache access and CUDA provider availability. "
                f"Original error: {exc}"
            ) from exc

    def detect(self, frame_path: Path) -> list[Any]:
        image = self.cv2.imread(str(frame_path))
        if image is None:
            logging.warning("Could not read extracted frame: %s", frame_path)
            return []
        return self.app.get(image)

    def save_crop(self, frame_path: Path, face: Any, crop_path: Path) -> None:
        image = self.image_cls.open(frame_path).convert("RGB")
        bbox = [max(0, int(x)) for x in face.bbox.tolist()]
        left, top, right, bottom = bbox
        pad_x = max(8, int((right - left) * 0.18))
        pad_y = max(8, int((bottom - top) * 0.18))
        crop_box = (
            max(0, left - pad_x),
            max(0, top - pad_y),
            min(image.width, right + pad_x),
            min(image.height, bottom + pad_y),
        )
        crop_path.parent.mkdir(parents=True, exist_ok=True)
        image.crop(crop_box).save(crop_path, "JPEG", quality=88)


def progress(items: list[Path], label: str) -> Iterable[Path]:
    try:
        from tqdm import tqdm

        yield from tqdm(items, desc=label, unit="video")
    except ImportError:
        for index, item in enumerate(items, 1):
            logging.info("%s %s/%s %s", label, index, len(items), item.name)
            yield item


def find_videos(source_dir: Path, recursive: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    videos = [
        path
        for path in source_dir.glob(pattern)
        if path.is_file()
        and path.suffix.lower() in VIDEO_EXTENSIONS
        and not any(part in EXCLUDED_SCAN_DIRS for part in path.relative_to(source_dir).parts[:-1])
    ]
    return sorted(videos)


def find_verification_queue_videos(source_dir: Path, recursive: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    videos = [
        path
        for path in source_dir.glob(pattern)
        if path.is_file()
        and path.suffix.lower() in VIDEO_EXTENSIONS
        and not any(part in VERIFICATION_QUEUE_EXCLUDED_DIRS for part in path.relative_to(source_dir).parts[:-1])
    ]
    return sorted(videos)


def meta_path_for(video_path: Path) -> Path:
    return video_path.with_name(f"{video_path.name}.face-meta.json")


def nfo_path_for(video_path: Path) -> Path:
    return video_path.with_name(f"{video_path.name}.nfo")


def needs_scan(video_path: Path, force: bool) -> bool:
    if force:
        return True
    meta_path = meta_path_for(video_path)
    if not meta_path.exists():
        return True
    try:
        meta = load_json(meta_path, {})
    except Exception:
        return True
    if meta.get("verification_needed"):
        return True
    return meta_path.stat().st_mtime < video_path.stat().st_mtime


def has_metadata(video_path: Path) -> bool:
    return meta_path_for(video_path).exists()


def ffprobe_duration(video_path: Path) -> float | None:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return float(result.stdout.strip())
    except Exception:
        return None


def extract_frames(video_path: Path, work_dir: Path, frame_count: int) -> list[Path]:
    require_ffmpeg()
    duration = ffprobe_duration(video_path)
    if duration and duration > 10:
        start = max(2.0, duration * 0.08)
        end = max(start + 1, duration * 0.92)
        timestamps = np.linspace(start, end, num=frame_count)
    else:
        timestamps = np.linspace(1, max(1, frame_count), num=frame_count)
    frame_paths: list[Path] = []
    for index, timestamp in enumerate(timestamps, 1):
        frame_path = work_dir / f"frame-{index:02d}.jpg"
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{float(timestamp):.2f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-q:v",
            "2",
            "-y",
            str(frame_path),
        ]
        subprocess.run(command, check=False, capture_output=True, text=True)
        if frame_path.exists() and frame_path.stat().st_size > 0:
            frame_paths.append(frame_path)
    return frame_paths


def should_keep_face(face: Any, frame_size: tuple[int, int], config: OrganizerConfig) -> tuple[bool, str]:
    det_score = float(getattr(face, "det_score", 0.0))
    if det_score < config.min_face_score:
        return False, f"low detection score {det_score:.3f} < {config.min_face_score:.3f}"
    width, height = frame_size
    left, top, right, bottom = [float(value) for value in face.bbox.tolist()]
    face_area = max(0.0, right - left) * max(0.0, bottom - top)
    frame_area = max(1.0, float(width * height))
    ratio = face_area / frame_area
    if ratio < config.min_face_area_ratio:
        return False, f"small face area {ratio:.4f} < {config.min_face_area_ratio:.4f}"
    return True, "accepted"


def face_bbox_aspect_ratio(face: Any) -> float:
    left, top, right, bottom = [float(value) for value in face.bbox.tolist()]
    width = max(1.0, right - left)
    height = max(1.0, bottom - top)
    return width / height


def should_keep_enrollment_face(face: Any, frame_size: tuple[int, int], config: OrganizerConfig) -> tuple[bool, str]:
    keep, reason = should_keep_face(face, frame_size, config)
    if not keep:
        return keep, reason
    det_score = float(getattr(face, "det_score", 0.0))
    if det_score < ENROLLMENT_MIN_DET_SCORE:
        return False, f"enrollment detection score {det_score:.3f} < {ENROLLMENT_MIN_DET_SCORE:.3f}"
    aspect = face_bbox_aspect_ratio(face)
    if aspect < ENROLLMENT_FACE_ASPECT_MIN or aspect > ENROLLMENT_FACE_ASPECT_MAX:
        return False, f"face bbox aspect ratio {aspect:.2f} outside enrollment range"
    return True, "accepted"


def aggregate_observations(observations: list[FaceObservation], model_version: str) -> list[dict[str, Any]]:
    if not observations:
        return [
            {
                "name": "unknown performer",
                "confidence": 0.0,
                "similarity": 0.0,
                "status": "unknown",
                "verification_needed": True,
                "label": "unknown performer - verification needed",
                "face_crop_path": None,
                "original_frame_path": None,
                "model_version": model_version,
                "supporting_faces": 0,
            }
        ]

    grouped: dict[str, list[FaceObservation]] = {}
    for observation in observations:
        key = observation.match.performer_id or "unknown"
        grouped.setdefault(key, []).append(observation)

    performers: list[dict[str, Any]] = []
    for key, faces in grouped.items():
        best = max(faces, key=lambda item: item.match.similarity)
        performers.append(
            {
                "id": best.match.performer_id,
                "name": best.match.name,
                "confidence": round(best.match.similarity, 4),
                "similarity": round(best.match.similarity, 4),
                "status": best.match.status,
                "verification_needed": best.match.verification_needed,
                "label": best.match.confidence_label,
                "face_crop_path": str(best.crop_path) if best.crop_path else None,
                "original_frame_path": str(best.frame_path),
                "bbox": [round(float(value), 2) for value in best.bbox],
                "detection_score": round(float(best.det_score), 4),
                "model_version": model_version,
                "supporting_faces": len(faces),
            }
        )

    performers.sort(key=lambda item: (item["status"] != "auto", -float(item["similarity"])))
    strong = [item for item in performers if float(item["similarity"]) >= HIGH_CONFIDENCE]
    possibles = [item for item in performers if POSSIBLE_CONFIDENCE <= float(item["similarity"]) < HIGH_CONFIDENCE]
    unknowns = [item for item in performers if item["status"] == "unknown"]
    if strong:
        return strong[:4] + possibles[: max(0, 2 - len(strong))]
    if possibles:
        return possibles[:2]
    return unknowns[:1]


def suggested_org(performers: list[dict[str, Any]], source_dir: Path) -> dict[str, Any]:
    auto = [item for item in performers if item["status"] == "auto"]
    if 1 <= len(auto) <= 2 and all(not item["verification_needed"] for item in auto):
        primary = slugify(auto[0]["name"])
        return {
            "eligible": True,
            "strategy": "symlink-first",
            "target_dir": str(source_dir / "models" / primary),
            "reason": "all detected performers are high-confidence and review-free",
        }
    return {
        "eligible": False,
        "strategy": "none",
        "target_dir": None,
        "reason": "requires verification or has too many/too few high-confidence performers",
    }


def write_nfo(video_path: Path, performers: list[dict[str, Any]]) -> None:
    tags = []
    for performer in performers:
        name = performer["name"]
        if performer["verification_needed"]:
            name = f"{name} verification needed"
        tags.append(f"  <tag>{html.escape(name)}</tag>")
    payload = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<movie>\n" + "\n".join(tags) + "\n</movie>\n"
    nfo_path_for(video_path).write_text(payload, encoding="utf-8")


def scan_video(video_path: Path, config: OrganizerConfig, db: KnownPerformersDB, recognizer: InsightFaceRecognizer) -> dict[str, Any]:
    started = time.perf_counter()
    review_dir = video_path.parent / config.review_dir_name / video_path.stem
    observations: list[FaceObservation] = []
    rejected_faces: list[RejectedFace] = []
    with tempfile.TemporaryDirectory(prefix="face-organizer-") as temp_name:
        temp_dir = Path(temp_name)
        frame_paths = extract_frames(video_path, temp_dir, config.frame_count)
        review_frame_paths: list[Path] = []
        if config.apply:
            frames_dir = review_dir / "frames"
            frames_dir.mkdir(parents=True, exist_ok=True)
            for frame_path in frame_paths:
                target = frames_dir / frame_path.name
                shutil.copy2(frame_path, target)
                review_frame_paths.append(target)
        else:
            review_frame_paths = frame_paths
        for frame_path in frame_paths:
            frame_image = recognizer.image_cls.open(frame_path)
            frame_size = frame_image.size
            frame_image.close()
            faces = recognizer.detect(frame_path)
            for face_index, face in enumerate(faces, 1):
                keep, reason = should_keep_face(face, frame_size, config)
                if not keep:
                    rejected_faces.append(
                        RejectedFace(
                            frame_path=frame_path,
                            bbox=face.bbox.tolist(),
                            det_score=float(getattr(face, "det_score", 0.0)),
                            reason=reason,
                        )
                    )
                    continue
                embedding = normalize_embedding(np.asarray(face.embedding, dtype=np.float32))
                match = db.match(embedding)
                crop_path = review_dir / f"{frame_path.stem}-face-{face_index:02d}.jpg"
                frame_review_path = review_dir / f"{frame_path.stem}.jpg"
                if config.apply:
                    recognizer.save_crop(frame_path, face, crop_path)
                    frame_review_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(frame_path, frame_review_path)
                    stored_frame_path = frame_review_path
                    stored_crop_path: Path | None = crop_path
                else:
                    stored_frame_path = frame_path
                    stored_crop_path = None
                observations.append(
                    FaceObservation(
                        frame_path=stored_frame_path,
                        crop_path=stored_crop_path,
                        embedding=embedding,
                        bbox=face.bbox.tolist(),
                        det_score=float(getattr(face, "det_score", 0.0)),
                        match=match,
                    )
                )
        metadata_hints = build_metadata_hints(
            video_path,
            enable_online=False,
            frame_paths=review_frame_paths,
            ocr_watermarks=config.ocr_watermarks,
        )

    model_version = f"insightface:{config.model_name}"
    performers = aggregate_observations(observations, model_version)
    duration = ffprobe_duration(video_path)
    verification_needed = any(item["verification_needed"] for item in performers)
    meta = {
        "schema": "media-face-organizer/v1",
        "video_path": str(video_path),
        "generated_at": utc_now(),
        "dry_run": not config.apply,
        "verification_needed": verification_needed,
        "performers": performers,
        "metadata_hints": metadata_hints,
        "suggested_organization": suggested_org(performers, config.source_dir),
        "frames_analyzed": config.frame_count,
        "review_frames": [str(path) for path in review_frame_paths],
        "faces_detected": len(observations),
        "faces_rejected": [
            {
                "frame_path": str(item.frame_path),
                "bbox": [round(float(value), 2) for value in item.bbox],
                "detection_score": round(float(item.det_score), 4),
                "reason": item.reason,
            }
            for item in rejected_faces
        ],
        "duration_seconds": round(duration, 3) if duration else None,
        "processing_time_seconds": round(time.perf_counter() - started, 3),
        "model_version": model_version,
        "thresholds": {
            "auto": HIGH_CONFIDENCE,
            "possible": POSSIBLE_CONFIDENCE,
        },
    }
    return apply_combined_identity(meta, config.source_dir)


PRESERVED_SCAN_SIDECAR_FIELDS = (
    "assignment_decision",
    "face_match_decisions",
    "faceless_video",
    "faceless_video_decisions",
    "left_unknown_decision",
    "left_unknown_decisions",
    "manual_correction_pending",
)


def merge_scan_with_existing_sidecar(fresh: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any]:
    """Keep user CRUD decisions when a face-rec scan refreshes generated evidence."""
    if not isinstance(existing, dict) or not existing:
        return fresh
    merged = dict(fresh)
    for field in PRESERVED_SCAN_SIDECAR_FIELDS:
        if field in existing:
            merged[field] = existing[field]

    fresh_performers = [item for item in merged.get("performers") or [] if isinstance(item, dict)]
    seen_keys: set[str] = set()
    for performer in fresh_performers:
        seen_keys.update(performer_match_keys(str(performer.get("name") or ""), str(performer.get("id") or "")))
    for performer in existing.get("performers") or []:
        if not isinstance(performer, dict):
            continue
        status = str(performer.get("status") or "")
        if status not in {"manual-confirmed", "user-confirmed"}:
            continue
        keys = performer_match_keys(str(performer.get("name") or ""), str(performer.get("id") or ""))
        if seen_keys & keys:
            continue
        fresh_performers.append(performer)
        seen_keys.update(keys)
    if fresh_performers:
        merged["performers"] = fresh_performers

    if bool(merged.get("faceless_video")) or bool(merged.get("left_unknown_decision")):
        merged["verification_needed"] = False
    elif any(not bool(item.get("verification_needed")) for item in fresh_performers):
        merged["verification_needed"] = any(bool(item.get("verification_needed")) for item in fresh_performers)
    return merged


def write_scan_sidecar(path: Path, fresh_meta: dict[str, Any]) -> dict[str, Any]:
    existing = load_json(path, {}) if path.exists() else {}
    merged = merge_scan_with_existing_sidecar(fresh_meta, existing)
    json_dump(path, merged)
    return merged


def scan(config: OrganizerConfig, *, status_phase: str = "scanning_videos") -> list[dict[str, Any]]:
    if not config.source_dir.exists():
        raise RuntimeError(f"Source directory does not exist: {config.source_dir}")
    require_ffmpeg()
    db = KnownPerformersDB(config.db_dir)
    db.load()
    recognizer = InsightFaceRecognizer(config.model_name, config.ctx_id, config.det_size)
    if config.skip_existing:
        videos = [video for video in find_videos(config.source_dir, config.recursive) if not has_metadata(video)]
    else:
        videos = [video for video in find_videos(config.source_dir, config.recursive) if needs_scan(video, config.force)]
    if config.sample_limit:
        videos = videos[: config.sample_limit]
    logging.info("Scanning %s video(s) from %s", len(videos), config.source_dir)
    write_smart_rescan_status(
        {
            "phase": status_phase,
            "phaseLabel": "Rescanning videos for high-confidence model matches",
            "progress": {
                "total": len(videos),
                "completed": 0,
                "percent": 0 if videos else 100,
            },
        }
    )
    results: list[dict[str, Any]] = []
    for index, video_path in enumerate(progress(videos, "face scan"), start=1):
        relative_preview = str(video_path)
        try:
            relative_preview = str(video_path.relative_to(config.source_dir))
        except ValueError:
            pass
        write_smart_rescan_status(
            {
                "phase": status_phase,
                "phaseLabel": "Rescanning videos for high-confidence model matches",
                "currentItem": {
                    "kind": "video",
                    "name": video_path.name,
                    "path": str(video_path),
                    "preview": relative_preview,
                },
                "progress": {
                    "total": len(videos),
                    "completed": index - 1,
                    "percent": round(((index - 1) / max(1, len(videos))) * 100, 1),
                },
            }
        )
        try:
            meta = scan_video(video_path, config, db, recognizer)
            results.append(meta)
            labels = ", ".join(item["label"] for item in meta["performers"])
            logging.info("%s -> %s", video_path.name, labels)
            if config.apply:
                meta = write_scan_sidecar(meta_path_for(video_path), meta)
                if config.write_nfo:
                    write_nfo(video_path, meta["performers"])
            else:
                logging.info("dry-run: would write %s", meta_path_for(video_path))
        except Exception as exc:
            logging.exception("Failed to scan %s: %s", video_path, exc)
        finally:
            write_smart_rescan_status(
                {
                    "phase": status_phase,
                    "phaseLabel": "Rescanning videos for high-confidence model matches",
                    "currentItem": {
                        "kind": "video",
                        "name": video_path.name,
                        "path": str(video_path),
                        "preview": relative_preview,
                    },
                    "progress": {
                        "total": len(videos),
                        "completed": index,
                        "percent": round((index / max(1, len(videos))) * 100, 1),
                    },
                }
            )
    if not config.apply:
        logging.info("dry-run complete: no sidecars, crops, NFO files, or organization changes were written")
    return results


def scan_recent_unscanned_videos(config: OrganizerConfig, *, limit: int = 12, max_age_hours: int = 72) -> list[str]:
    """Face-scan freshly uploaded library files that never received a sidecar."""
    if limit <= 0:
        return []
    cutoff = time.time() - max(1, int(max_age_hours)) * 3600
    scanned: list[str] = []
    candidates: list[tuple[float, Path]] = []
    for video_path in find_verification_queue_videos(config.source_dir, config.recursive):
        if meta_path_for(video_path).exists():
            continue
        try:
            mtime = float(video_path.stat().st_mtime)
        except Exception:
            continue
        if mtime < cutoff:
            continue
        candidates.append((mtime, video_path))
    for _, video_path in sorted(candidates, key=lambda item: item[0], reverse=True):
        try:
            scan_single_video(config, video_path, refresh_pages=False)
            scanned.append(str(video_path))
        except Exception as exc:
            logging.warning("Failed auto-scan for recent upload %s: %s", video_path, exc)
        if len(scanned) >= limit:
            break
    if scanned:
        logging.info("Auto-scanned %s recent upload(s) without face sidecars", len(scanned))
        refresh_organizer_pages(config, refresh_stale_enrollment=True, include_verification_report=True, scan_recent_uploads=False)
    return scanned


def scan_single_video(config: OrganizerConfig, video_path: Path, *, refresh_pages: bool = True) -> dict[str, Any]:
    if not video_path.exists() or not video_path.is_file() or video_path.suffix.lower() not in VIDEO_EXTENSIONS:
        raise RuntimeError(f"Video does not exist or is unsupported: {video_path}")
    require_ffmpeg()
    db = KnownPerformersDB(config.db_dir)
    db.load()
    recognizer = InsightFaceRecognizer(config.model_name, config.ctx_id, config.det_size)
    scan_config = dataclasses.replace(config, source_dir=video_path.parent, force=True)
    meta = scan_video(video_path, scan_config, db, recognizer)
    if config.apply:
        meta = write_scan_sidecar(meta_path_for(video_path), meta)
        if config.write_nfo:
            write_nfo(video_path, meta["performers"])
        if refresh_pages:
            refresh_organizer_pages(config, refresh_stale_enrollment=True, scan_recent_uploads=False)
    else:
        logging.info("dry-run: would write %s", meta_path_for(video_path))
    return meta


def image_to_data_uri(path_text: str | None, report_dir: Path) -> str | None:
    if not path_text:
        return None
    path = Path(path_text)
    candidates = [path, report_dir / path_text]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            mime = "image/jpeg"
            encoded = base64.b64encode(candidate.read_bytes()).decode("ascii")
            return f"data:{mime};base64,{encoded}"
    return None


def display_image_src(path_text: str | None) -> str:
    text = str(path_text or "")
    if not text:
        return ""
    normalized = text.replace("\\", "/")
    candidates: list[Path] = []
    if "/home/source/SpiritOS/" in normalized:
        candidates.append(Path.cwd() / normalized.split("/home/source/SpiritOS/", 1)[1])
    if normalized.startswith("/mnt/spirit-8tb/media/yes/"):
        relative = normalized.removeprefix("/mnt/spirit-8tb/media/yes/")
        candidates.extend([Path("/mnt/spirit-8tb/media/yes") / relative, Path("/DATA/yes") / relative, Path("M:/yes") / relative])
    elif normalized.startswith("/DATA/yes/"):
        relative = normalized.removeprefix("/DATA/yes/")
        candidates.extend([Path("/DATA/yes") / relative, Path("/mnt/spirit-8tb/media/yes") / relative, Path("M:/yes") / relative])
    else:
        candidates.append(Path(normalized))
    for path in candidates:
        if not path.is_absolute():
            path = path.resolve()
        if path.exists() and path.is_file():
            suffix = path.suffix.lower()
            mime = "image/png" if suffix == ".png" else "image/webp" if suffix == ".webp" else "image/jpeg"
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            return f"data:{mime};base64,{encoded}"
    return text


def collect_metadata(source_dir: Path, recursive: bool) -> list[dict[str, Any]]:
    pattern = "**/*.face-meta.json" if recursive else "*.face-meta.json"
    records: list[dict[str, Any]] = []
    for path in sorted(source_dir.glob(pattern)):
        try:
            rel_parts = path.relative_to(source_dir).parts[:-1]
        except ValueError:
            rel_parts = ()
        if any(part in {"backups", "review_exports", "known_performers"} for part in rel_parts):
            continue
        try:
            record = load_json(path, {})
            record["_meta_path"] = str(path)
            actual_video_path = resolve_metadata_video_path(path)
            record["_resolved_video_path"] = str(actual_video_path)
            record["_video_exists"] = bool(actual_video_path.exists())
            if actual_video_path.exists():
                record["video_path"] = str(actual_video_path)
                record["path"] = str(actual_video_path)
            records.append(record)
        except Exception as exc:
            logging.warning("Could not read %s: %s", path, exc)
    return dedupe_metadata_records(records)


def metadata_record_face_score(record: dict[str, Any]) -> tuple[int, int, int, int, int, float]:
    performers = [item for item in record.get("performers") or [] if isinstance(item, dict)]
    support = max((int(item.get("supporting_faces") or 0) for item in performers), default=0)
    crop_count = sum(1 for item in performers if item.get("face_crop_path") or item.get("original_frame_path"))
    faces_detected = int(record.get("faces_detected") or 0)
    meta_path = Path(str(record.get("_meta_path") or ""))
    resolved_path = Path(str(record.get("_resolved_video_path") or record.get("video_path") or ""))
    exact_video_path = meta_path.with_name(meta_path.name.removesuffix(".face-meta.json")) if meta_path.name else Path("")
    exact_sidecar_match = int(bool(exact_video_path and path_key(exact_video_path) == path_key(resolved_path)))
    decision_count = len([item for item in record.get("face_match_decisions") or [] if isinstance(item, dict)])
    faceless_state = int(bool(record.get("faceless_video")))
    try:
        mtime = meta_path.stat().st_mtime if meta_path.exists() else 0.0
    except Exception:
        mtime = 0.0
    return (exact_sidecar_match, decision_count + faceless_state, support, crop_count, faces_detected, mtime)


def dedupe_metadata_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_by_video: dict[str, dict[str, Any]] = {}
    passthrough: list[dict[str, Any]] = []
    for record in records:
        raw_key = str(record.get("_resolved_video_path") or record.get("video_path") or record.get("path") or "")
        path = Path(raw_key) if raw_key else None
        if not path or path.suffix.lower() not in VIDEO_EXTENSIONS:
            passthrough.append(record)
            continue
        try:
            key = str(path.resolve()) if path.exists() else str(path)
        except Exception:
            key = str(path)
        current = best_by_video.get(key)
        if current is None or metadata_record_face_score(record) > metadata_record_face_score(current):
            best_by_video[key] = record
    return sorted([*passthrough, *best_by_video.values()], key=lambda item: str(item.get("_meta_path") or ""))


def resolve_metadata_video_path(meta_path: Path) -> Path:
    exact = meta_path.with_name(meta_path.name.removesuffix(".face-meta.json"))
    if exact.exists():
        return exact
    base = exact.with_suffix("")
    preferred_suffixes = [".mp4", ".mkv", ".mov", ".m4v", ".avi", ".webm"]
    for suffix in [suffix for suffix in preferred_suffixes if suffix in VIDEO_EXTENSIONS]:
        candidate = base.with_suffix(suffix)
        if candidate.exists():
            return candidate
    root = metadata_media_root(meta_path)
    if root and root.exists():
        for pattern in [exact.name, f"*/{exact.name}", f"models/*/{exact.name}"]:
            for candidate in sorted(root.glob(pattern)):
                if candidate.is_file() and not metadata_path_is_excluded(root, candidate):
                    return candidate
        for suffix in [suffix for suffix in preferred_suffixes if suffix in VIDEO_EXTENSIONS]:
            for pattern in [f"{base.name}{suffix}", f"*/{base.name}{suffix}", f"models/*/{base.name}{suffix}"]:
                for candidate in sorted(root.glob(pattern)):
                    if candidate.is_file() and not metadata_path_is_excluded(root, candidate):
                        return candidate
    return exact


def metadata_media_root(path: Path) -> Path | None:
    for parent in [path.parent, *path.parents]:
        if parent.name in {"yes", "other"}:
            return parent
    return None


def metadata_path_is_excluded(root: Path, path: Path) -> bool:
    try:
        parts = path.relative_to(root).parts[:-1]
    except ValueError:
        parts = path.parts[:-1]
    return any(part in {"backups", "review_exports", "known_performers", ".face-review"} for part in parts)


def timestamped_backup_root(config: OrganizerConfig) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = config.backup_dir / stamp
    if not root.exists():
        return root
    return config.backup_dir / f"{stamp}-{uuid.uuid4().hex[:6]}"


def backup_state(config: OrganizerConfig, include_videos: bool = False) -> Path:
    backup_root = timestamped_backup_root(config)
    metadata_dir = backup_root / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "schema": "media-face-organizer-backup/v1",
        "created_at": utc_now(),
        "source_dir": str(config.source_dir),
        "db_dir": str(config.db_dir),
        "report_path": str(config.report_path),
        "include_videos": include_videos,
        "files": [],
    }
    for meta_path in sorted(config.source_dir.glob("**/*.face-meta.json" if config.recursive else "*.face-meta.json")):
        target = metadata_dir / meta_path.relative_to(config.source_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(meta_path, target)
        manifest["files"].append({"type": "sidecar", "source": str(meta_path), "backup": str(target)})
    if config.db_dir.exists():
        target_db = backup_root / "known_performers"
        if target_db.exists():
            shutil.rmtree(target_db)
        shutil.copytree(config.db_dir, target_db)
        manifest["files"].append({"type": "known_performers", "source": str(config.db_dir), "backup": str(target_db)})
    if config.verification_registry_path.exists():
        target_registry = backup_root / config.verification_registry_path.name
        shutil.copy2(config.verification_registry_path, target_registry)
        manifest["files"].append(
            {
                "type": "performer_verification",
                "source": str(config.verification_registry_path),
                "backup": str(target_registry),
            }
        )
    if config.report_path.exists():
        target_report = backup_root / config.report_path.name
        target_report.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config.report_path, target_report)
        manifest["files"].append({"type": "report", "source": str(config.report_path), "backup": str(target_report)})
    if include_videos:
        video_dir = backup_root / "videos"
        videos = find_videos(config.source_dir, config.recursive)
        if config.sample_limit:
            videos = videos[: config.sample_limit]
        for video_path in progress(videos, "video backup"):
            target = video_dir / video_path.relative_to(config.source_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(video_path, target)
            manifest["files"].append({"type": "video", "source": str(video_path), "backup": str(target), "bytes": video_path.stat().st_size})
    json_dump(backup_root / "backup_manifest.json", manifest)
    logging.info("Wrote backup manifest: %s", backup_root / "backup_manifest.json")
    return backup_root


def backup_selected_records(config: OrganizerConfig, records: list[dict[str, Any]], include_videos: bool = True) -> Path:
    if include_videos and os.environ.get("SPIRITFLIX_SMART_RESCAN_NO_VIDEO_BACKUPS") == "1":
        logging.info("Smart rescan guard: selected video backups disabled")
        include_videos = False
    backup_root = timestamped_backup_root(config)
    manifest: dict[str, Any] = {
        "schema": "media-face-organizer-selected-backup/v1",
        "created_at": utc_now(),
        "source_dir": str(config.source_dir),
        "include_videos": include_videos,
        "files": [],
    }
    metadata_dir = backup_root / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    for record in records:
        meta_path = Path(record.get("_meta_path", ""))
        if meta_path.exists():
            try:
                target = metadata_dir / meta_path.relative_to(config.source_dir)
            except ValueError:
                target = metadata_dir / meta_path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(meta_path, target)
            manifest["files"].append({"type": "sidecar", "source": str(meta_path), "backup": str(target)})
        if include_videos:
            video_path = Path(record.get("video_path") or "")
            if video_path.exists():
                video_target = backup_root / "videos" / video_path.name
                video_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(video_path, video_target)
                manifest["files"].append(
                    {"type": "video", "source": str(video_path), "backup": str(video_target), "bytes": video_path.stat().st_size}
                )
    if config.db_dir.exists():
        target_db = backup_root / "known_performers"
        shutil.copytree(config.db_dir, target_db)
        manifest["files"].append({"type": "known_performers", "source": str(config.db_dir), "backup": str(target_db)})
    json_dump(backup_root / "backup_manifest.json", manifest)
    logging.info("Wrote selected backup manifest: %s", backup_root / "backup_manifest.json")
    return backup_root


def enrich_metadata(config: OrganizerConfig, enable_online: bool) -> list[dict[str, Any]]:
    records = collect_metadata(config.source_dir, config.recursive)
    if config.sample_limit:
        records = records[: config.sample_limit]
    logging.info("Enriching %s metadata record(s)", len(records))
    enriched: list[dict[str, Any]] = []
    for record in records:
        video_path = Path(record.get("video_path") or "")
        if not video_path.exists():
            meta_path = Path(record.get("_meta_path", ""))
            video_path = meta_path.with_name(meta_path.name.removesuffix(".face-meta.json")) if meta_path.name else video_path
        frame_paths = [
            Path(item.get("original_frame_path"))
            for item in record.get("performers", [])
            if item.get("original_frame_path") and Path(item.get("original_frame_path")).exists()
        ]
        hints = build_metadata_hints(
            video_path,
            enable_online,
            frame_paths=frame_paths,
            ocr_watermarks=config.ocr_watermarks,
        )
        record["metadata_hints"] = hints
        record = apply_combined_identity(record, config.source_dir)
        enriched.append(record)
        best = hints.get("candidate_names", [{}])[0].get("name") if hints.get("candidate_names") else None
        logging.info("%s -> best metadata hint: %s", video_path.name or record.get("_meta_path"), best or "none")
        if config.apply:
            json_dump(Path(record["_meta_path"]), {key: value for key, value in record.items() if key != "_meta_path"})
        else:
            logging.info("dry-run: would update %s", record.get("_meta_path"))
    return enriched


def choose_primary_name(record: dict[str, Any]) -> tuple[str, str, float]:
    performers = record.get("performers") or []
    auto = [item for item in performers if item.get("status") == "auto" and not item.get("verification_needed")]
    if auto:
        best = max(auto, key=lambda item: float(item.get("similarity", 0)))
        return str(best.get("name") or "Unknown"), "face-auto", float(best.get("similarity", 0))
    hints = ((record.get("metadata_hints") or {}).get("candidate_names") or [])
    if hints:
        best_hint = max(hints, key=lambda item: float(item.get("confidence", 0)))
        return str(best_hint.get("name") or "Unknown"), f"metadata-{best_hint.get('source', 'hint')}", float(best_hint.get("confidence", 0))
    return "Unknown Performer", "unknown", 0.0


def build_rename_entry(record: dict[str, Any], source_dir: Path) -> dict[str, Any]:
    video_path = Path(record.get("video_path") or "")
    primary_name, basis, confidence = choose_primary_name(record)
    duration = record.get("duration_seconds")
    year = "unknown-year"
    try:
        if video_path.exists():
            year = str(datetime.fromtimestamp(video_path.stat().st_mtime).year)
    except OSError:
        pass
    descriptor_source = normalize_candidate_name(video_path.stem) or video_path.stem or "video"
    descriptor = sanitized_filename_part(descriptor_source, "video")
    performer_part = sanitized_filename_part(primary_name, "Unknown Performer")
    suffix = video_path.suffix.lower() or ".mp4"
    duration_part = f"{round(float(duration) / 60):02d}m" if isinstance(duration, (int, float)) and duration else "unknown-duration"
    proposed_name = f"{performer_part} - {year} - {descriptor} - {duration_part}{suffix}"
    target_dir = video_path.parent
    if primary_name != "Unknown Performer":
        target_dir = source_dir / "models" / sanitized_filename_part(primary_name, slugify(primary_name))
    return {
        "source_path": str(video_path),
        "proposed_path": str(target_dir / proposed_name),
        "proposed_filename": proposed_name,
        "primary_name": primary_name,
        "basis": basis,
        "confidence": round(confidence, 3),
        "verification_needed": bool(record.get("verification_needed") or basis.startswith("metadata") or basis == "unknown"),
        "safe_to_apply": False,
        "reason": "proposal only; rename requires human review and a future explicit apply-renames mode",
    }


def write_rename_plan(config: OrganizerConfig) -> dict[str, Any]:
    records = collect_metadata(config.source_dir, config.recursive)
    if config.sample_limit:
        records = records[: config.sample_limit]
    entries = [build_rename_entry(record, config.source_dir) for record in records]
    plan = {
        "schema": "media-face-organizer-rename-plan/v1",
        "generated_at": utc_now(),
        "source_dir": str(config.source_dir),
        "entries": entries,
        "safety": {
            "renames_applied": False,
            "videos_copied": False,
            "message": "This manifest is review-only. It does not rename, move, delete, or overwrite media.",
        },
    }
    if config.apply:
        config.rename_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        json_dump(config.rename_manifest_path, plan)
        logging.info("Wrote rename plan: %s", config.rename_manifest_path)
    else:
        logging.info("dry-run: would write rename plan to %s", config.rename_manifest_path)
    for entry in entries[:10]:
        logging.info("rename proposal: %s -> %s", Path(entry["source_path"]).name, entry["proposed_filename"])
    return plan


def unique_destination(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for index in range(2, 1000):
        candidate = path.with_name(f"{stem}-{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not find a free destination for {path}")


def destination_for_record(record: dict[str, Any], source_dir: Path) -> tuple[Path, str]:
    video_path = Path(record.get("video_path") or "")
    performers = record.get("performers") or []
    auto = [item for item in performers if item.get("status") == "auto" and not item.get("verification_needed")]
    if auto and not record.get("verification_needed"):
        primary = auto[0].get("name") or "Unknown Performer"
        return source_dir / "models" / slugify(str(primary)) / video_path.name, "model"
    return source_dir / "unknown" / video_path.name, "unknown"


def move_with_sidecars(video_path: Path, destination: Path) -> dict[str, str]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    final_video = destination if video_path.resolve() == destination.resolve() else unique_destination(destination)
    moved: dict[str, str] = {}
    if video_path.resolve() != final_video.resolve():
        shutil.move(str(video_path), str(final_video))
        moved[str(video_path)] = str(final_video)
    old_meta = meta_path_for(video_path)
    if old_meta.exists():
        new_meta = meta_path_for(final_video)
        if old_meta.resolve() != new_meta.resolve():
            shutil.move(str(old_meta), str(new_meta))
        try:
            metadata = load_json(new_meta, {})
            metadata["video_path"] = str(final_video)
            metadata["path"] = str(final_video)
            metadata["filename"] = final_video.name
            json_dump(new_meta, metadata)
        except Exception as exc:
            logging.warning("Moved %s but could not update embedded video path: %s", new_meta, exc)
        moved[str(old_meta)] = str(new_meta)
    old_nfo = nfo_path_for(video_path)
    if old_nfo.exists():
        new_nfo = nfo_path_for(final_video)
        if old_nfo.resolve() != new_nfo.resolve():
            shutil.move(str(old_nfo), str(new_nfo))
        moved[str(old_nfo)] = str(new_nfo)
    return moved


def existing_video_for_sidecar(record: dict[str, Any], sidecar_path: Path) -> Path:
    candidates = []
    raw_video = str(record.get("video_path") or "")
    if raw_video:
        candidates.append(Path(raw_video))
    sidecar_name = sidecar_path.name
    if sidecar_name.endswith(".face-meta.json"):
        original = sidecar_path.with_name(sidecar_name[: -len(".face-meta.json")])
        candidates.append(original)
        candidates.extend(original.with_suffix(suffix) for suffix in VIDEO_EXTENSIONS)
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return Path(raw_video) if raw_video else sidecar_path


def organize_videos(config: OrganizerConfig) -> dict[str, Any]:
    records = collect_metadata(config.source_dir, config.recursive)
    if config.sample_limit:
        records = records[: config.sample_limit]
    records = [
        record
        for record in records
        if Path(record.get("video_path") or "").exists()
        and Path(record.get("video_path") or "").resolve() != destination_for_record(record, config.source_dir)[0].resolve()
    ]
    if not records:
        logging.info("No metadata records found to organize")
        return {"entries": []}
    if not config.apply:
        logging.info("dry-run: would organize %s video(s)", len(records))
    else:
        backup_selected_records(config, records, include_videos=True)
    manifest = {
        "schema": "media-face-organizer-organize/v1",
        "generated_at": utc_now(),
        "source_dir": str(config.source_dir),
        "entries": [],
    }
    for record in records:
        video_path = Path(record.get("video_path") or "")
        if not video_path.exists():
            manifest["entries"].append({"source_path": str(video_path), "status": "missing"})
            continue
        destination, bucket = destination_for_record(record, config.source_dir)
        entry = {
            "source_path": str(video_path),
            "destination_path": str(destination),
            "bucket": bucket,
            "verification_needed": bool(record.get("verification_needed")),
            "performers": record.get("performers", []),
            "applied": False,
            "moved": {},
        }
        if config.apply:
            moved = move_with_sidecars(video_path, destination)
            final_video = Path(moved[str(video_path)])
            new_meta_path = meta_path_for(final_video)
            if new_meta_path.exists():
                updated = load_json(new_meta_path, {})
                updated["video_path"] = str(final_video)
                updated["organized_at"] = utc_now()
                updated["organization_bucket"] = bucket
                updated["suggested_organization"] = {
                    **(updated.get("suggested_organization") or {}),
                    "applied": True,
                    "final_path": str(final_video),
                }
                json_dump(new_meta_path, updated)
            entry["applied"] = True
            entry["moved"] = moved
            entry["destination_path"] = str(final_video)
            logging.info("organized %s -> %s", video_path.name, final_video)
        else:
            logging.info("dry-run organize: %s -> %s", video_path.name, destination)
        manifest["entries"].append(entry)
    if config.apply:
        config.organize_manifest_path.parent.mkdir(parents=True, exist_ok=True)
        json_dump(config.organize_manifest_path, manifest)
        logging.info("Wrote organize manifest: %s", config.organize_manifest_path)
    return manifest


def verify_performers(config: OrganizerConfig, enable_online: bool = False, organize: bool = True) -> dict[str, Any]:
    records = collect_metadata(config.source_dir, config.recursive)
    if config.sample_limit:
        records = records[: config.sample_limit]
    registry = load_performer_registry(config.verification_registry_path)
    preserved_aliases = dict(registry.get("aliases") or {})
    registry["performers"] = {}
    registry["aliases"] = {**dict(SEED_PERFORMER_ALIASES), **preserved_aliases}
    registry["generated_at"] = registry.get("generated_at") or utc_now()
    registry["updated_at"] = utc_now()
    registry["source_dir"] = str(config.source_dir)
    registry["online_metadata_requested"] = bool(enable_online)

    changed_records = 0
    scanned_records = 0
    for record in records:
        scanned_records += 1
        before = json.dumps(record, sort_keys=True, default=str)
        record, changed = canonicalize_record(record, registry, config.source_dir)
        after = json.dumps(record, sort_keys=True, default=str)
        changed = changed or before != after
        if changed:
            changed_records += 1
            if config.apply:
                meta_path = Path(record.get("_meta_path") or meta_path_for(Path(record.get("video_path") or "")))
                clean_record = {key: value for key, value in record.items() if key != "_meta_path"}
                json_dump(meta_path, clean_record)

    # Add model folders as aliases/evidence so UI fallback names do not split cards.
    models_root = config.source_dir / "models"
    if models_root.exists():
        for folder in sorted(path for path in models_root.iterdir() if path.is_dir()):
            folder_name = folder.name
            canonical = canonical_performer_name(folder_name, registry)
            if canonical and canonical != "unknown performer":
                update_registry_entry(
                    registry,
                    canonical,
                    [folder_name],
                    {
                        "_folder_alias_only": True,
                        "video_path": str(folder),
                        "performers": [{"name": canonical, "status": "folder"}],
                        "metadata_hints": {},
                    },
                )

    # Collapse exact duplicate registry entries after aliases have been learned.
    performers = registry.get("performers") or {}
    merged: dict[str, dict[str, Any]] = {}
    for entry in performers.values():
        if not isinstance(entry, dict):
            continue
        canonical = canonical_performer_name(str(entry.get("name") or ""), registry)
        slug = slugify(canonical)
        target = merged.setdefault(
            slug,
            {
                "name": canonical,
                "slug": slug,
                "aliases": [],
                "profile_handles": [],
                "status": entry.get("status") or "needs-review",
                "evidence": [],
                "web_text_evidence_summary": entry.get("web_text_evidence_summary") or summarize_web_text_evidence([]),
                "identity_trace_summary": entry.get("identity_trace_summary")
                or {"schema": IDENTITY_TRACE_SCHEMA, "count": 0, "review_required": True},
                "assignment_decision": entry.get("assignment_decision") or blank_assignment_decision(),
                "confirmed_by": entry.get("confirmed_by"),
                "confirmed_at": entry.get("confirmed_at"),
                "enrolled_face_samples": entry.get("enrolled_face_samples") or [],
                "audit_events": entry.get("audit_events") or [],
                "video_count": 0,
            },
        )
        target["video_count"] = int(target.get("video_count") or 0) + int(entry.get("video_count") or 0)
        for field in ("aliases", "profile_handles", "evidence"):
            existing = json.dumps(target.get(field, []), sort_keys=True)
            seen = {json.dumps(item, sort_keys=True) for item in target.get(field, [])}
            for item in entry.get(field, []) or []:
                key = json.dumps(item, sort_keys=True)
                if key not in seen:
                    target.setdefault(field, []).append(item)
                    seen.add(key)
            if field == "aliases":
                target[field] = sorted({str(item) for item in target.get(field, []) if item}, key=str.lower)
            elif existing:
                target[field] = target.get(field, [])[-30:]
        for field in ("enrolled_face_samples", "audit_events"):
            seen = {json.dumps(item, sort_keys=True) for item in target.get(field, [])}
            for item in entry.get(field, []) or []:
                key = json.dumps(item, sort_keys=True)
                if key not in seen:
                    target.setdefault(field, []).append(item)
                    seen.add(key)
        entry_web_count = int((entry.get("web_text_evidence_summary") or {}).get("count") or 0)
        target_web_count = int((target.get("web_text_evidence_summary") or {}).get("count") or 0)
        if entry_web_count > target_web_count:
            target["web_text_evidence_summary"] = entry.get("web_text_evidence_summary")
        entry_trace_count = int((entry.get("identity_trace_summary") or {}).get("count") or 0)
        target_trace_count = int((target.get("identity_trace_summary") or {}).get("count") or 0)
        if entry_trace_count > target_trace_count:
            target["identity_trace_summary"] = entry.get("identity_trace_summary")
        entry_decision = normalize_assignment_decision(entry.get("assignment_decision"))
        target_decision = normalize_assignment_decision(target.get("assignment_decision"))
        if float(entry_decision.get("confidence") or 0) > float(target_decision.get("confidence") or 0):
            target["assignment_decision"] = entry_decision
        status_rank = {"user-confirmed": 0, "profile-url": 1, "local-auto": 2, "needs-review": 3}
        if status_rank.get(str(entry.get("status")), 99) < status_rank.get(str(target.get("status")), 99):
            target["status"] = entry.get("status")
    registry["performers"] = dict(sorted(merged.items(), key=lambda item: item[0]))

    model_index = {
        "schema": "spiritflix-model-index/v1",
        "generated_at": utc_now(),
        "source_dir": str(config.source_dir),
        "models": [
            model_index_entry(slug, entry) for slug, entry in registry["performers"].items()
        ],
    }

    if config.apply:
        json_dump(config.verification_registry_path, registry)
        json_dump(config.verification_registry_path.with_name("model_index.json"), model_index)
        logging.info("Wrote performer verification registry: %s", config.verification_registry_path)
        logging.info("Wrote SpiritFlix model index: %s", config.verification_registry_path.with_name("model_index.json"))
        if organize:
            manifest = organize_videos(config)
            remove_empty_model_dirs(config.source_dir)
        else:
            manifest = {"entries": []}
    else:
        logging.info(
            "dry-run: scanned %s metadata record(s), would update %s record(s), registry %s",
            scanned_records,
            changed_records,
            config.verification_registry_path,
        )
        manifest = {"entries": []}
    return {
        "scanned_records": scanned_records,
        "changed_records": changed_records,
        "registry_path": str(config.verification_registry_path),
        "model_index_path": str(config.verification_registry_path.with_name("model_index.json")),
        "model_count": len(registry.get("performers") or {}),
        "organize_entries": len(manifest.get("entries", [])),
    }


def remove_empty_model_dirs(source_dir: Path) -> None:
    models_root = source_dir / "models"
    if not models_root.exists():
        return
    for folder in sorted((path for path in models_root.iterdir() if path.is_dir()), key=lambda path: len(path.parts), reverse=True):
        try:
            visible_files = [path for path in folder.rglob("*") if path.is_file() and ".face-review" not in path.parts]
            if not visible_files:
                shutil.rmtree(folder)
                logging.info("Removed empty model folder: %s", folder)
        except Exception as exc:
            logging.warning("Could not remove empty model folder %s: %s", folder, exc)


def backfill_review_frames(config: OrganizerConfig, enable_online: bool = False) -> list[dict[str, Any]]:
    records = collect_metadata(config.source_dir, config.recursive)
    if config.sample_limit:
        records = records[: config.sample_limit]
    logging.info("Backfilling review frames for %s metadata record(s)", len(records))
    updated: list[dict[str, Any]] = []
    for record in progress(records, "frame backfill"):
        video_path = Path(record.get("video_path") or "")
        if not video_path.exists():
            logging.warning("Skipping missing video for %s", record.get("_meta_path"))
            continue
        with tempfile.TemporaryDirectory(prefix="face-review-frames-") as temp_name:
            temp_dir = Path(temp_name)
            frame_paths = extract_frames(video_path, temp_dir, config.frame_count)
            review_dir = video_path.parent / config.review_dir_name / video_path.stem / "frames"
            review_paths: list[Path] = []
            if config.apply:
                review_dir.mkdir(parents=True, exist_ok=True)
            for frame_path in frame_paths:
                target = review_dir / frame_path.name
                if config.apply:
                    shutil.copy2(frame_path, target)
                    review_paths.append(target)
                else:
                    review_paths.append(frame_path)
            record["review_frames"] = [str(path) for path in review_paths]
            record["metadata_hints"] = build_metadata_hints(
                video_path,
                enable_online=enable_online,
                frame_paths=review_paths,
                ocr_watermarks=config.ocr_watermarks,
            )
            record = apply_combined_identity(record, config.source_dir)
            updated.append(record)
            best = ((record.get("metadata_hints") or {}).get("candidate_names") or [{}])[0].get("name")
            logging.info("%s -> %s review frames, best hint: %s", video_path.name, len(review_paths), best or "none")
            if config.apply:
                json_dump(Path(record["_meta_path"]), {key: value for key, value in record.items() if key != "_meta_path"})
            else:
                logging.info("dry-run: would update %s", record.get("_meta_path"))
    return updated


def render_badge(performer: dict[str, Any]) -> str:
    status = performer.get("status", "unknown")
    classes = {
        "auto": "badge-auto",
        "possible": "badge-possible",
        "unknown": "badge-unknown",
    }.get(status, "badge-unknown")
    label = performer.get("label") or performer.get("name") or "unknown"
    return f'<span class="badge {classes}">{html.escape(label)}</span>'


def lightbox_image(src: str, css_class: str, alt: str) -> str:
    safe_src = html.escape(src, quote=True)
    safe_alt = html.escape(alt, quote=True)
    return f'<button class="image-button" type="button" data-full="{safe_src}"><img src="{safe_src}" class="{css_class}" alt="{safe_alt}" loading="lazy" decoding="async"></button>'


def clean_display_hints(hints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in hints:
        raw_name = str(item.get("name") or "")
        canonical = split_handle_words(raw_name)
        if is_bad_candidate_name(canonical, str(item.get("raw") or raw_name)):
            continue
        key = normalize_identity_key(canonical)
        if key in seen:
            continue
        seen.add(key)
        next_item = dict(item)
        next_item["name"] = canonical
        cleaned.append(next_item)
    return cleaned


def model_verification_links(name: str) -> list[dict[str, str]]:
    query = " ".join(str(name or "").split())
    if not query or query.lower() == "unknown performer":
        return []
    candidate = normalized_candidate(query, "manual", 0.0, query, evidence_role="manual_text_search")
    return [
        {"label": str(item["label"]), "url": str(item["url"])}
        for item in text_verification_queries([candidate] if candidate else [], limit=1)
        if item.get("label") in {"Yandex", "Yandex PimpBunny", "Yandex Coomer", "Coomer"}
    ]


def manual_name_queries(name: str) -> list[dict[str, Any]]:
    candidate = normalized_candidate(name, "manual", 1.0, name, evidence_role="user_entered_candidate")
    return text_verification_queries([candidate] if candidate else [], limit=1)


def sidecar_record_path(value: str | Path) -> Path:
    path = Path(value)
    if path.suffix == ".json" and path.name.endswith(".face-meta.json"):
        return path
    return meta_path_for(path)


def store_manual_correction(
    config: OrganizerConfig,
    sidecar_path: Path,
    name: str,
    *,
    corrected_by: str,
    belongs_to_existing: bool = False,
) -> dict[str, Any]:
    if not name.strip() or is_bad_candidate_name(name):
        raise RuntimeError(f"Unsafe correction name: {name!r}")
    if not corrected_by.strip():
        raise RuntimeError("--corrected-by is required")
    record = load_json(sidecar_path, {})
    if not isinstance(record, dict):
        raise RuntimeError(f"Sidecar is not a JSON object: {sidecar_path}")
    video_path = existing_video_for_sidecar(record, sidecar_path)
    previous = normalize_assignment_decision(record.get("assignment_decision")).get("suggested_name")
    correction = {
        "schema": "media-manual-correction/v1",
        "status": "pending",
        "corrected_by": corrected_by,
        "corrected_at": utc_now(),
        "source_file": str(record.get("video_path") or video_path or sidecar_path),
        "sidecar_path": str(sidecar_path),
        "previous_suggestion": previous,
        "new_canonical_name": split_handle_words(name),
        "evidence_role": "user_confirmed_correction",
        "belongs_to_existing": bool(belongs_to_existing),
        "face_enrollment_performed": False,
        "text_verification_queries": manual_name_queries(name),
        "limitations": "Pending evidence only. Registry/model index and face embeddings are unchanged until confirm-correction is run explicitly.",
    }
    if not config.apply:
        logging.info("dry-run: would store pending manual correction on %s: %s", sidecar_path, correction)
        return correction
    record.setdefault("manual_corrections", []).append(correction)
    record["manual_correction_pending"] = correction
    json_dump(sidecar_path, record)
    logging.info("Stored pending manual correction on %s", sidecar_path)
    return correction


def latest_pending_correction(record: dict[str, Any]) -> dict[str, Any] | None:
    pending = record.get("manual_correction_pending")
    if isinstance(pending, dict) and pending.get("status") == "pending":
        return pending
    for item in reversed(record.get("manual_corrections") or []):
        if isinstance(item, dict) and item.get("status") == "pending":
            return item
    return None


def write_model_index_from_registry(config: OrganizerConfig, registry: dict[str, Any]) -> None:
    model_index = {
        "schema": "spiritflix-model-index/v1",
        "generated_at": utc_now(),
        "source_dir": str(config.source_dir),
        "models": [model_index_entry(slug, entry) for slug, entry in sorted(registry.get("performers", {}).items())],
    }
    json_dump(config.verification_registry_path.with_name("model_index.json"), model_index)


def confirm_manual_correction(
    config: OrganizerConfig,
    sidecar_path: Path,
    *,
    confirmed_by: str,
) -> dict[str, Any]:
    if not confirmed_by.strip():
        raise RuntimeError("--confirmed-by is required")
    record = load_json(sidecar_path, {})
    if not isinstance(record, dict):
        raise RuntimeError(f"Sidecar is not a JSON object: {sidecar_path}")
    correction = latest_pending_correction(record)
    if not correction:
        raise RuntimeError(f"No pending manual correction found in {sidecar_path}")
    name = split_handle_words(str(correction.get("new_canonical_name") or ""))
    if not name or is_bad_candidate_name(name):
        raise RuntimeError(f"Unsafe pending correction name: {name!r}")
    video_path = existing_video_for_sidecar(record, sidecar_path)
    audit_event = {
        "event": "manual_correction_confirmed",
        "corrected_by": correction.get("corrected_by"),
        "confirmed_by": confirmed_by,
        "confirmed_at": utc_now(),
        "corrected_at": correction.get("corrected_at"),
        "source_file": correction.get("source_file") or record.get("video_path") or str(video_path),
        "previous_suggestion": correction.get("previous_suggestion"),
        "new_canonical_name": name,
        "evidence_role": "user_confirmed_correction",
        "face_enrollment_performed": False,
        "limitations": "Registry/model index text identity update only; no face enrollment was performed.",
    }
    if not config.apply:
        logging.info("dry-run: would confirm manual correction: %s", audit_event)
        return audit_event
    registry = load_performer_registry(config.verification_registry_path)
    slug = slugify(name)
    entry = registry.setdefault("performers", {}).setdefault(
        slug,
        {
            "name": name,
            "slug": slug,
            "aliases": [],
            "profile_handles": [],
            "status": "user-confirmed",
            "evidence": [],
            "web_text_evidence_summary": summarize_web_text_evidence([]),
            "identity_trace_summary": {"schema": IDENTITY_TRACE_SCHEMA, "count": 0, "review_required": True},
            "assignment_decision": blank_assignment_decision(),
            "video_count": 0,
        },
    )
    entry["name"] = name
    entry["slug"] = slug
    entry["status"] = "user-confirmed"
    entry["confirmed_by"] = confirmed_by
    entry["confirmed_at"] = audit_event["confirmed_at"]
    entry.setdefault("audit_events", []).append(audit_event)
    entry.setdefault("evidence", []).append(
        {
            "video_path": str(record.get("video_path") or video_path),
            "source": "manual_correction",
            "name": name,
            "confidence": 1.0,
            "evidence_role": "user_confirmed_correction",
            "sidecar_path": str(sidecar_path),
        }
    )
    registry.setdefault("aliases", {})[normalize_identity_key(name)] = name
    registry["updated_at"] = utc_now()
    correction["status"] = "confirmed"
    correction["confirmed_by"] = confirmed_by
    correction["confirmed_at"] = audit_event["confirmed_at"]
    record["manual_correction_pending"] = None
    record.setdefault("manual_corrections", []).append(dict(correction))
    record.setdefault("audit_events", []).append(audit_event)
    record["verification_needed"] = True
    json_dump(sidecar_path, record)
    json_dump(config.verification_registry_path, registry)
    write_model_index_from_registry(config, registry)
    logging.info("Confirmed manual correction for %s as %s", sidecar_path, name)
    return audit_event


def apply_manual_name_correction(
    config: OrganizerConfig,
    sidecar_path: Path,
    name: str,
    *,
    corrected_by: str = "Britton",
    confirmed_by: str = "Britton",
    belongs_to_existing: bool = False,
) -> dict[str, Any]:
    registry = load_performer_registry(config.verification_registry_path)
    model_lookup = model_index_lookup(config.verification_registry_path.with_name("model_index.json"))
    known = known_db_summary(config.db_dir)
    canonical_name = canonical_performer_name(name, registry)
    initial_presence = performer_presence(canonical_name, registry, model_lookup, known)
    if initial_presence.get("registry_entry"):
        canonical_name = str((initial_presence.get("registry_entry") or {}).get("name") or canonical_name)
    elif initial_presence.get("model_index_match"):
        canonical_name = str((model_lookup.get(normalize_identity_key(canonical_name)) or {}).get("name") or canonical_name)
    elif initial_presence.get("known_record"):
        canonical_name = str((initial_presence.get("known_record") or {}).get("name") or canonical_name)
    auto_existing = bool(
        initial_presence.get("registry_match")
        or initial_presence.get("model_index_match")
        or initial_presence.get("known_performers_record")
    )
    correction = store_manual_correction(
        config,
        sidecar_path,
        canonical_name,
        corrected_by=corrected_by,
        belongs_to_existing=bool(belongs_to_existing or auto_existing),
    )
    event = confirm_manual_correction(config, sidecar_path, confirmed_by=confirmed_by)
    confirmed_name = str(event.get("new_canonical_name") or correction.get("new_canonical_name") or canonical_name)
    registry = load_performer_registry(config.verification_registry_path)
    presence = performer_presence(
        confirmed_name,
        registry,
        model_lookup,
        known,
    )
    sidecar_after = sidecar_record_path(sidecar_path)
    record = load_json(sidecar_after, {})
    video_path = existing_video_for_sidecar(record, sidecar_after)
    move_receipt: dict[str, str] = {}
    if config.apply and presence.get("status") == "face-enrolled" and video_path.exists():
        target = config.source_dir / "models" / slugify(confirmed_name) / video_path.name
        move_receipt = move_with_sidecars(video_path, target)
        moved_video = Path(move_receipt.get(str(video_path), str(video_path)))
        expected_meta = meta_path_for(moved_video)
        moved_meta = move_receipt.get(str(sidecar_after))
        if not moved_meta and sidecar_after.exists() and sidecar_after.resolve() != expected_meta.resolve():
            expected_meta.parent.mkdir(parents=True, exist_ok=True)
            final_meta = unique_destination(expected_meta)
            shutil.move(str(sidecar_after), str(final_meta))
            move_receipt[str(sidecar_after)] = str(final_meta)
            moved_meta = str(final_meta)
        if moved_meta:
            sidecar_after = Path(moved_meta)
        record = load_json(sidecar_after, record)
        performers = [
            {
                "id": str(presence.get("known_performer_id") or slugify(confirmed_name)),
                "name": confirmed_name,
                "confidence": 1.0,
                "similarity": 1.0,
                "status": "manual-confirmed",
                "verification_needed": False,
                "label": f"{confirmed_name} - manually confirmed",
            }
        ]
        record["performers"] = performers
        record["verification_needed"] = False
        record["manual_confirmed_model"] = {
            "schema": "media-manual-model-assignment/v1",
            "name": confirmed_name,
            "confirmed_by": confirmed_by,
            "confirmed_at": utc_now(),
            "known_performer_id": str(presence.get("known_performer_id") or ""),
            "face_enrolled": True,
            "move_receipt": move_receipt,
        }
        json_dump(sidecar_after, record)
        next_action = "updated_existing_enrolled_model"
    else:
        if config.apply and video_path.exists():
            expected_meta = meta_path_for(video_path)
            if sidecar_after.exists() and sidecar_after.resolve() != expected_meta.resolve():
                expected_meta.parent.mkdir(parents=True, exist_ok=True)
                final_meta = unique_destination(expected_meta)
                shutil.move(str(sidecar_after), str(final_meta))
                move_receipt[str(sidecar_after)] = str(final_meta)
                sidecar_after = final_meta
                record = load_json(sidecar_after, record)
            record["video_path"] = str(video_path)
            record["path"] = str(video_path)
            record["filename"] = video_path.name
            record["performers"] = [
                {
                    "id": slugify(confirmed_name),
                    "name": confirmed_name,
                    "confidence": 1.0,
                    "similarity": 1.0,
                    "status": "manual-confirmed",
                    "verification_needed": False,
                    "label": f"{confirmed_name} - manually confirmed; needs face enrollment",
                }
            ]
            record["verification_needed"] = False
            record["manual_confirmed_model"] = {
                "schema": "media-manual-model-assignment/v1",
                "name": confirmed_name,
                "confirmed_by": confirmed_by,
                "confirmed_at": utc_now(),
                "known_performer_id": "",
                "face_enrolled": False,
                "move_receipt": move_receipt,
                "next_action": "queued_for_face_enrollment",
            }
            json_dump(sidecar_after, record)
        next_action = "queued_for_face_enrollment"
    return {
        "schema": "media-manual-model-correction-result/v1",
        "name": confirmed_name,
        "sidecar_path": str(sidecar_after),
        "presence": presence,
        "next_action": next_action,
        "move_receipt": move_receipt,
        "correction": correction,
        "confirmation": event,
        "auto_existing_match": auto_existing,
    }


def mark_video_left_unknown(config: OrganizerConfig, sidecar_path: Path, *, confirmed_by: str = "Britton", reason: str = "") -> dict[str, Any]:
    if not confirmed_by.strip():
        raise RuntimeError("confirmed_by is required")
    record = load_json(sidecar_path, {})
    if not isinstance(record, dict):
        raise RuntimeError(f"Sidecar is not a JSON object: {sidecar_path}")
    video_path = existing_video_for_sidecar(record, sidecar_path)
    if video_path.exists() and not record.get("video_path"):
        record["video_path"] = str(video_path)
        record["path"] = str(video_path)
        record["filename"] = video_path.name
    event = {
        "schema": "media-face-organizer-left-unknown/v1",
        "event": "video_left_unknown",
        "confirmed_by": confirmed_by,
        "confirmed_at": utc_now(),
        "sidecar_path": str(sidecar_path),
        "video_path": str(record.get("video_path") or record.get("path") or video_path or ""),
        "reason": reason or "User chose to leave this video as unknown.",
        "preserves_scan_evidence": True,
    }
    if not config.apply:
        logging.info("dry-run: would mark %s as left unknown", sidecar_path)
        return event
    record["left_unknown_decision"] = event
    record.setdefault("left_unknown_decisions", []).append(event)
    record["manual_correction_pending"] = None
    record["verification_needed"] = False
    record.setdefault("audit_events", []).append(event)
    json_dump(sidecar_path, record)
    logging.info("Marked %s as left unknown", sidecar_path)
    return event


def lookup_manual_model_name(config: OrganizerConfig, name: str) -> dict[str, Any]:
    registry = load_performer_registry(config.verification_registry_path)
    canonical_name = canonical_performer_name(name, registry)
    presence = performer_presence(
        canonical_name,
        registry,
        model_index_lookup(config.verification_registry_path.with_name("model_index.json")),
        known_db_summary(config.db_dir),
    )
    existing = bool(
        presence.get("registry_match")
        or presence.get("model_index_match")
        or presence.get("known_performers_record")
    )
    resolved_name = canonical_name
    if presence.get("registry_entry"):
        resolved_name = str((presence.get("registry_entry") or {}).get("name") or resolved_name)
    elif presence.get("known_record"):
        resolved_name = str((presence.get("known_record") or {}).get("name") or resolved_name)
    return {
        "schema": "media-manual-model-name-lookup/v1",
        "input_name": name,
        "canonical_name": resolved_name,
        "existing": existing,
        "face_enrolled": presence.get("status") == "face-enrolled",
        "status": presence.get("status"),
        "known_performer_id": str(presence.get("known_performer_id") or ""),
    }


def model_index_lookup(path: Path) -> dict[str, dict[str, Any]]:
    payload = load_json(path, {"models": []})
    models = payload.get("models") if isinstance(payload, dict) else []
    lookup: dict[str, dict[str, Any]] = {}
    if isinstance(models, dict):
        iterable = models.values()
    elif isinstance(models, list):
        iterable = models
    else:
        iterable = []
    for item in iterable:
        if not isinstance(item, dict):
            continue
        keys = [item.get("slug"), item.get("id"), item.get("name")]
        keys.extend(item.get("aliases") or [])
        for key in keys:
            normalized = normalize_identity_key(str(key or ""))
            if normalized:
                lookup[normalized] = item
    return lookup


def known_db_summary(db_dir: Path) -> dict[str, Any]:
    index = load_json(db_dir / "index.json", {"performers": []})
    performer_map = load_json(db_dir / "performer_map.json", {})
    performers = index.get("performers") if isinstance(index, dict) else []
    by_id = {str(item.get("id")): item for item in performers if isinstance(item, dict) and item.get("id")}
    try:
        embeddings = np_load_with_retry(db_dir / "embeddings.npy")
        shape = tuple(int(value) for value in embeddings.shape)
        rows = int(embeddings.shape[0]) if embeddings.ndim >= 1 else 0
    except Exception as exc:
        shape = None
        rows = 0
        logging.warning("Could not read embeddings metadata from %s: %s", db_dir / "embeddings.npy", exc)
    mapped_ids = {str(value) for value in performer_map.values()} if isinstance(performer_map, dict) else set()
    row_to_id = {str(key): str(value) for key, value in performer_map.items()} if isinstance(performer_map, dict) else {}
    return {
        "performers": performers if isinstance(performers, list) else [],
        "by_id": by_id,
        "performer_map": row_to_id,
        "mapped_ids": mapped_ids,
        "embedding_shape": shape,
        "embedding_rows": rows,
    }


def performer_presence(name: str, registry: dict[str, Any], model_lookup: dict[str, dict[str, Any]], known_summary: dict[str, Any]) -> dict[str, Any]:
    key = normalize_identity_key(name)
    registry_entry = None
    for slug, entry in (registry.get("performers") or {}).items():
        if not isinstance(entry, dict):
            continue
        keys = {normalize_identity_key(str(slug)), normalize_identity_key(str(entry.get("name") or ""))}
        keys.update(normalize_identity_key(str(alias)) for alias in entry.get("aliases", []) if alias)
        if key in keys:
            registry_entry = entry
            break
    model_entry = model_lookup.get(key)
    known_record = None
    for performer in known_summary["performers"]:
        if not isinstance(performer, dict):
            continue
        keys = {normalize_identity_key(str(performer.get("id") or "")), normalize_identity_key(str(performer.get("name") or ""))}
        keys.update(normalize_identity_key(str(alias)) for alias in performer.get("aliases", []) if alias)
        if key in keys:
            known_record = performer
            break
    known_id = str((known_record or {}).get("id") or "")
    embedding_rows = []
    for row, performer_id in known_summary["performer_map"].items():
        if performer_id == known_id:
            if str(row).isdigit():
                embedding_rows.append(int(row))
    is_faceless = bool((registry_entry or {}).get("faceless")) or (registry_entry or {}).get("face_enrollment_status") == "faceless"
    return {
        "name": name,
        "registry_match": bool(registry_entry),
        "registry_entry": registry_entry,
        "model_index_match": bool(model_entry),
        "faceless": is_faceless,
        "known_performers_record": bool(known_record),
        "known_performer_id": known_id,
        "embedding_row": str(sorted(embedding_rows)[0]) if embedding_rows else None,
        "embedding_rows": sorted(embedding_rows),
        "known_record": known_record,
        "status": (
            "faceless performer"
            if is_faceless
            else
            "face-enrolled"
            if known_record and embedding_rows
            else "in registry/model index, not face-enrolled"
            if registry_entry or model_entry
            else "not found in registry/model index/known_performers"
        ),
    }


def explain_detection(record: dict[str, Any], expected: str, presence: dict[str, Any]) -> str:
    faces = int(record.get("faces_detected") or 0)
    rejected = record.get("faces_rejected") or record.get("rejected_faces") or []
    performers = record.get("performers") or []
    if faces <= 0:
        if rejected:
            reasons = ", ".join(str(item.get("reason") or "rejected face") for item in rejected[:3] if isinstance(item, dict))
            return f"no accepted face detected; rejected face reason: {reasons or 'rejected face'}"
        return "no accepted face detected"
    if presence.get("registry_match") or presence.get("model_index_match"):
        if not presence.get("embedding_row"):
            return "in registry/model index, not face-enrolled"
    best = max((float(item.get("similarity") or 0) for item in performers if isinstance(item, dict)), default=0.0)
    if presence.get("embedding_row") and best < POSSIBLE_CONFIDENCE:
        return f"face-enrolled but similarity below threshold ({best:.3f} < {POSSIBLE_CONFIDENCE:.3f})"
    if faces and not performers:
        return "faces detected but no performer records were produced"
    return "unknown performer match; no local face DB similarity reached threshold"


def audit_known_db(config: OrganizerConfig, expected_files: dict[str, str] | None = None) -> dict[str, Any]:
    registry = load_performer_registry(config.verification_registry_path)
    model_lookup = model_index_lookup(config.verification_registry_path.with_name("model_index.json"))
    known = known_db_summary(config.db_dir)
    registry_keys = set(registry.get("performers", {}).keys())
    model_keys = {normalize_identity_key(str(item.get("slug") or item.get("name") or "")) for item in model_lookup.values()}
    known_ids = set(known["by_id"].keys())
    missing_known = []
    for slug, entry in sorted((registry.get("performers") or {}).items()):
        name = str(entry.get("name") or slug) if isinstance(entry, dict) else str(slug)
        presence = performer_presence(name, registry, model_lookup, known)
        if presence.get("faceless"):
            continue
        if not presence["known_performers_record"]:
            missing_known.append({"slug": slug, "name": name, "status": "in registry/model index, not face-enrolled"})
    known_missing_rows = [
        {"id": performer_id, "name": item.get("name"), "status": "known performer record missing embedding row"}
        for performer_id, item in sorted(known["by_id"].items())
        if performer_id not in known["mapped_ids"]
    ]
    orphan_rows = [
        {"row": row, "performer_id": performer_id}
        for row, performer_id in sorted(known["performer_map"].items(), key=lambda pair: int(pair[0]) if pair[0].isdigit() else 999999)
        if performer_id not in known_ids or (row.isdigit() and int(row) >= int(known["embedding_rows"]))
    ]
    alias_collisions: list[dict[str, Any]] = []
    alias_owner: dict[str, str] = {}
    for slug, entry in sorted((registry.get("performers") or {}).items()):
        if not isinstance(entry, dict):
            continue
        for alias in entry.get("aliases", []) or []:
            key = normalize_identity_key(str(alias))
            if key in alias_owner and alias_owner[key] != slug:
                alias_collisions.append({"alias": alias, "performers": sorted({alias_owner[key], slug})})
            else:
                alias_owner[key] = slug
    file_rows: list[dict[str, Any]] = []
    for filename, expected in (expected_files or {}).items():
        sidecar = next(config.source_dir.rglob(f"{filename}.face-meta.json"), None)
        record = load_json(sidecar, {}) if sidecar else {}
        presence = performer_presence(expected, registry, model_lookup, known)
        reason = explain_detection(record, expected, presence) if sidecar else "sidecar missing"
        file_rows.append(
            {
                "file": filename,
                "expected_performer": expected,
                "sidecar_exists": bool(sidecar),
                "faces_detected": record.get("faces_detected") if sidecar else None,
                "face_crops_saved": sum(1 for item in record.get("performers", []) if isinstance(item, dict) and item.get("face_crop_path")) if sidecar else 0,
                "registry_match": presence["registry_match"],
                "model_index_match": presence["model_index_match"],
                "known_performers_record": presence["known_performers_record"],
                "embedding_row": presence["embedding_row"],
                "reason": reason,
            }
        )
    return {
        "schema": "media-known-db-audit/v1",
        "generated_at": utc_now(),
        "read_only": True,
        "registry_count": len(registry.get("performers") or {}),
        "model_index_count": len({id(item) for item in model_lookup.values()}),
        "known_performers_count": len(known["performers"]),
        "embedding_shape": known["embedding_shape"],
        "performers_missing_known_record": missing_known,
        "known_performers_missing_embedding_rows": known_missing_rows,
        "embedding_rows_without_performer_ids": orphan_rows,
        "alias_collisions": alias_collisions,
        "file_expectation_audit": file_rows,
    }


def review_root(config: OrganizerConfig) -> Path:
    return config.source_dir / config.review_dir_name


def enrollment_review_dir(config: OrganizerConfig) -> Path:
    return review_root(config) / "enrollment"


def relative_url(from_path: Path, to_path: Path) -> str:
    try:
        return Path(os.path.relpath(to_path, from_path.parent)).as_posix()
    except ValueError:
        return to_path.as_posix()


def report_nav_html(current: str, base_path: Path) -> str:
    links = [
        ("Verification Queue", "face_verification_report.html"),
        ("Face Enrollment Queue", "face_enrollment_queue.html"),
        ("Enrolled", "face_enrolled_performers.html"),
        ("Gallery Upload", "face_gallery.html"),
        ("Known DB Audit", "known_db_audit.html"),
        ("Report All / Full Audit", "face_verification_full_audit.html"),
    ]
    items = []
    for label, filename in links:
        href = relative_url(base_path, base_path.with_name(filename))
        cls = "active" if current == label else ""
        items.append(f'<a class="{cls}" href="{html.escape(href, quote=True)}">{html.escape(label)}</a>')
    return f'<nav class="report-nav">{"".join(items)}</nav>'


def report_nav_css() -> str:
    return """
    .report-nav { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1rem; }
    .report-nav a { border-radius: .25rem; background: rgba(255,255,255,.07); color: #dbeafe; padding: .45rem .65rem; text-decoration: none; outline: 1px solid rgba(191,219,254,.16); font-size: .82rem; }
    .report-nav a.active { background: rgba(16,185,129,.16); color: #d1fae5; outline-color: rgba(52,211,153,.28); }
    """


def gallery_root(config: OrganizerConfig) -> Path:
    return config.report_path.with_name(GALLERY_DIR_NAME)


def gallery_index_path(config: OrganizerConfig) -> Path:
    return config.report_path.with_name("face_gallery.json")


def gallery_sidecar_path(image_path: Path) -> Path:
    return Path(f"{image_path}{GALLERY_SIDECAR_SUFFIX}")


def is_gallery_image_path(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in GALLERY_IMAGE_EXTENSIONS and not path.name.endswith(GALLERY_SIDECAR_SUFFIX)


def read_gallery_sidecar(image_path: Path) -> dict[str, Any]:
    sidecar = gallery_sidecar_path(image_path)
    if not sidecar.exists():
        return {}
    try:
        payload = json.loads(sidecar.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def gallery_item_payload(config: OrganizerConfig, model_name: str, model_slug: str, image_path: Path) -> dict[str, Any]:
    stat = image_path.stat()
    metadata = read_gallery_sidecar(image_path)
    name = str(metadata.get("model_name") or model_name)
    slug = str(metadata.get("model_slug") or model_slug)
    collection = str(metadata.get("collection") or "").strip()
    uploaded_at = str(metadata.get("uploaded_at") or "")
    return {
        "id": f"{slug}/{image_path.name}",
        "model_name": name,
        "model_key": normalize_identity_key(name),
        "model_slug": slug,
        "file_name": image_path.name,
        "path": str(image_path),
        "url": relative_url(config.report_path.with_name("face_gallery.html"), image_path),
        "collection": collection,
        "uploaded_at": uploaded_at or datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds"),
        "size_bytes": stat.st_size,
        "content_type": mimetypes.guess_type(str(image_path))[0] or "application/octet-stream",
    }


def gallery_items_for_model(config: OrganizerConfig, model_name: str, model_slug: str | None = None) -> list[dict[str, Any]]:
    slug = model_slug or slugify(model_name)
    folder = gallery_root(config) / slug
    if not folder.exists():
        return []
    items = [
        gallery_item_payload(config, model_name, slug, path)
        for path in sorted(folder.iterdir(), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)
        if is_gallery_image_path(path)
    ]
    return items


def build_gallery_payload(config: OrganizerConfig, enrolled_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    enrolled_payload = enrolled_payload or build_enrolled_groups(config)
    groups = []
    all_items = []
    for group in enrolled_payload.get("groups", []):
        if not isinstance(group, dict):
            continue
        model_name = str(group.get("name") or "").strip()
        if not model_name:
            continue
        model_slug = str(group.get("slug") or slugify(model_name))
        items = gallery_items_for_model(config, model_name, model_slug)
        groups.append(
            {
                "name": model_name,
                "model_key": normalize_identity_key(model_name),
                "model_slug": model_slug,
                "known_performer_id": str(group.get("known_performer_id") or ""),
                "item_count": len(items),
                "items": items,
            }
        )
        all_items.extend(items)
    all_items.sort(key=lambda item: str(item.get("uploaded_at") or ""), reverse=True)
    return {
        "schema": "spiritflix-model-gallery/v1",
        "generated_at": utc_now(),
        "gallery_root": str(gallery_root(config)),
        "summary": {
            "enrolled_models": len(groups),
            "models_with_gallery": sum(1 for group in groups if int(group.get("item_count") or 0) > 0),
            "gallery_items": len(all_items),
        },
        "groups": groups,
        "items": all_items,
    }


def write_gallery_index(config: OrganizerConfig, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or build_gallery_payload(config)
    gallery_index_path(config).parent.mkdir(parents=True, exist_ok=True)
    json_dump(gallery_index_path(config), payload)
    return payload


def resolve_gallery_performer(config: OrganizerConfig, performer_name: str) -> tuple[str, str]:
    requested = performer_name.strip()
    if not requested:
        raise RuntimeError("performer_name is required")
    registry = load_performer_registry(config.verification_registry_path)
    known = known_db_summary(config.db_dir)
    target_keys = {normalize_identity_key(requested), normalize_identity_key(slugify(requested))}
    for performer in known.get("performers", []):
        if not isinstance(performer, dict):
            continue
        performer_id = str(performer.get("id") or "")
        name = canonical_performer_name(str(performer.get("name") or performer_id), registry)
        keys = {normalize_identity_key(name), normalize_identity_key(performer_id), normalize_identity_key(slugify(name))}
        keys.update(normalize_identity_key(str(alias)) for alias in performer.get("aliases", []) or [] if alias)
        if not target_keys.intersection(keys):
            continue
        if not known_embedding_rows_for_id(known, performer_id):
            raise RuntimeError(f"{name} exists but is not face-enrolled yet")
        return name, performer_id
    raise RuntimeError(f"enrolled performer not found for gallery upload: {requested}")


def unique_gallery_filename(folder: Path, original_name: str, content_type: str = "") -> str:
    raw_suffix = Path(original_name or "").suffix.lower()
    suffix = raw_suffix if raw_suffix in GALLERY_IMAGE_EXTENSIONS else ""
    if not suffix and content_type.startswith("image/"):
        suffix = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
        }.get(content_type.lower(), "")
    if suffix not in GALLERY_IMAGE_EXTENSIONS:
        raise RuntimeError("gallery uploads must be image files (.jpg, .jpeg, .png, .webp, or .gif)")
    stem = sanitized_filename_part(Path(original_name or "gallery-image").stem, "gallery-image")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    for attempt in range(100):
        token = uuid.uuid4().hex[:8]
        candidate = f"{timestamp}-{token}-{stem}{suffix}"
        if not (folder / candidate).exists():
            return candidate
    raise RuntimeError("could not allocate a unique gallery filename")


def save_gallery_uploads(config: OrganizerConfig, fields: dict[str, str], files: list[dict[str, Any]]) -> dict[str, Any]:
    performer_name, performer_id = resolve_gallery_performer(config, fields.get("performer_name") or "")
    collection = str(fields.get("collection") or "").strip()
    model_slug = slugify(performer_name)
    upload_dir = gallery_root(config) / model_slug
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for file_item in files:
        filename = str(file_item.get("filename") or "")
        content = file_item.get("content") or b""
        content_type = str(file_item.get("content_type") or "")
        if not content:
            continue
        if not content_type.startswith("image/") and Path(filename).suffix.lower() not in GALLERY_IMAGE_EXTENSIONS:
            raise RuntimeError(f"{filename or 'upload'} is not an accepted image file")
        target_name = unique_gallery_filename(upload_dir, filename, content_type)
        target = upload_dir / target_name
        target.write_bytes(content)
        metadata = {
            "schema": "spiritflix-model-gallery-item/v1",
            "model_name": performer_name,
            "model_key": normalize_identity_key(performer_name),
            "model_slug": model_slug,
            "known_performer_id": performer_id,
            "original_name": filename,
            "file_name": target_name,
            "collection": collection,
            "uploaded_at": utc_now(),
            "uploaded_by": str(fields.get("uploaded_by") or "Britton"),
            "content_type": mimetypes.guess_type(str(target))[0] or content_type or "application/octet-stream",
            "size_bytes": len(content),
        }
        json_dump(gallery_sidecar_path(target), metadata)
        saved.append(gallery_item_payload(config, performer_name, model_slug, target))
    if not saved:
        raise RuntimeError("select at least one image to upload")
    payload = write_gallery_index(config)
    return {
        "schema": "spiritflix-model-gallery-upload/v1",
        "event": "gallery_images_uploaded",
        "performer_name": performer_name,
        "model_slug": model_slug,
        "saved_count": len(saved),
        "saved_items": saved,
        "gallery_summary": payload.get("summary") or {},
    }


def multipart_boundary(content_type: str) -> bytes:
    match = re.search(r'boundary=(?:"([^"]+)"|([^;]+))', content_type)
    if not match:
        raise RuntimeError("multipart boundary missing")
    boundary = (match.group(1) or match.group(2) or "").strip()
    if not boundary:
        raise RuntimeError("multipart boundary missing")
    return boundary.encode("utf-8")


def parse_content_disposition(header_value: str) -> dict[str, str]:
    parts = {}
    for key, value in re.findall(r'([A-Za-z0-9_-]+)="([^"]*)"', header_value):
        parts[key.lower()] = value
    return parts


def read_multipart_form(handler: http.server.BaseHTTPRequestHandler) -> tuple[dict[str, str], list[dict[str, Any]]]:
    content_type = handler.headers.get("Content-Type") or ""
    if "multipart/form-data" not in content_type:
        raise RuntimeError("gallery upload must use multipart/form-data")
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        raise RuntimeError("empty upload")
    if length > GALLERY_MAX_UPLOAD_BYTES:
        raise RuntimeError("gallery upload is too large")
    boundary = b"--" + multipart_boundary(content_type)
    raw = handler.rfile.read(length)
    fields: dict[str, str] = {}
    files: list[dict[str, Any]] = []
    for part in raw.split(boundary):
        part = part.strip(b"\r\n")
        if not part or part == b"--":
            continue
        if part.endswith(b"--"):
            part = part[:-2].rstrip(b"\r\n")
        header_blob, separator, body = part.partition(b"\r\n\r\n")
        if not separator:
            continue
        headers: dict[str, str] = {}
        for line in header_blob.decode("utf-8", errors="replace").split("\r\n"):
            name, _, value = line.partition(":")
            if name and value:
                headers[name.lower()] = value.strip()
        disposition = parse_content_disposition(headers.get("content-disposition", ""))
        field_name = disposition.get("name") or ""
        filename = disposition.get("filename")
        body = body.rstrip(b"\r\n")
        if filename is not None:
            files.append(
                {
                    "field": field_name,
                    "filename": filename,
                    "content_type": headers.get("content-type", ""),
                    "content": body,
                }
            )
        elif field_name:
            fields[field_name] = body.decode("utf-8", errors="replace").strip()
    return fields, files


def render_gallery_items(items: list[dict[str, Any]], empty_text: str = "No gallery pictures uploaded yet.") -> str:
    if not items:
        return f'<div class="empty-crop">{html.escape(empty_text)}</div>'
    return "".join(
        f"""
        <a class="gallery-thumb" href="{html.escape(str(item.get("url") or item.get("path") or ""), quote=True)}" target="_blank" rel="noopener noreferrer">
          <img src="{html.escape(str(item.get("url") or item.get("path") or ""), quote=True)}" alt="{html.escape(str(item.get("model_name") or "Gallery image"), quote=True)}" loading="lazy" decoding="async">
          <span>{html.escape(str(item.get("collection") or Path(str(item.get("file_name") or "")).stem))}</span>
        </a>
        """
        for item in items
    )


def render_gallery_upload_form(model_name: str, model_slug: str, *, collection: str = "") -> str:
    return f"""
      <form class="gallery-upload-form" enctype="multipart/form-data" data-performer="{html.escape(model_name, quote=True)}">
        <input type="hidden" name="performer_name" value="{html.escape(model_name, quote=True)}">
        <input type="hidden" name="model_slug" value="{html.escape(model_slug, quote=True)}">
        <label>Collection name<input name="collection" value="{html.escape(collection, quote=True)}" placeholder="optional set name"></label>
        <label>Gallery pictures<input name="images" type="file" accept="image/jpeg,image/png,image/webp,image/gif" multiple></label>
        <div class="button-row"><button type="button" data-action="gallery-upload">Upload pictures</button></div>
      </form>
    """


def render_gallery_upload_panel(group: dict[str, Any]) -> str:
    model_name = str(group.get("name") or "")
    model_slug = str(group.get("slug") or slugify(model_name))
    items = group.get("gallery_items") or []
    return f"""
      <details class="gallery-panel">
        <summary>Gallery pictures ({len(items)})</summary>
        <p class="exists">Upload model pictures here; SpiritFlix reads this gallery on the Library Gallery tab.</p>
        {render_gallery_upload_form(model_name, model_slug)}
        <div class="gallery-grid">{render_gallery_items(items)}</div>
      </details>
    """


def generate_gallery_page(config: OrganizerConfig, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or build_gallery_payload(config)
    out_path = config.report_path.with_name("face_gallery.html")
    summary = payload.get("summary") or {}
    stats = "".join(
        f"<span>{html.escape(str(key).replace('_', ' '))}: {html.escape(str(value))}</span>"
        for key, value in summary.items()
    )
    cards = []
    for group in payload.get("groups", []):
        if not isinstance(group, dict):
            continue
        model_name = str(group.get("name") or "")
        model_slug = str(group.get("model_slug") or slugify(model_name))
        items = group.get("items") if isinstance(group.get("items"), list) else []
        cards.append(
            f"""
            <article class="enroll-card gallery-upload-card" data-performer="{html.escape(model_name, quote=True)}">
              <div class="enroll-head">
                <div>
                  <p>GALLERY UPLOAD</p>
                  <h2>{html.escape(model_name)}</h2>
                  <small>{html.escape(model_slug)}</small>
                </div>
                <div class="mini-metrics"><span>{len(items)} picture(s)</span></div>
              </div>
              <div class="action-status" aria-live="polite"></div>
              {render_gallery_upload_form(model_name, model_slug)}
              <div class="gallery-grid">{render_gallery_items(items)}</div>
            </article>
            """
        )
    html_payload = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Gallery Upload</title>
  <style>{enrollment_page_css()}</style>
</head>
<body>
  <header>
    <p class="muted">Media Face Organizer v1</p>
    <h1>Gallery Upload</h1>
    <p class="muted">Generated {html.escape(utc_now())} for enrolled models. Uploaded pictures appear in SpiritFlix Library / Gallery.</p>
    {report_nav_html("Gallery Upload", out_path)}
    <div class="summary">{stats}</div>
  </header>
  <main class="grid">{''.join(cards) or '<div class="empty-crop">No enrolled performers found.</div>'}</main>
  <script>{enrollment_page_script()}</script>
</body>
</html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_payload, encoding="utf-8")
    write_gallery_index(config, payload)
    logging.info("Wrote gallery upload page: %s", out_path)
    return payload


def iter_model_index_models(path: Path) -> list[dict[str, Any]]:
    payload = load_json(path, {"models": []})
    models = payload.get("models") if isinstance(payload, dict) else []
    if isinstance(models, dict):
        iterable = models.values()
    elif isinstance(models, list):
        iterable = models
    else:
        iterable = []
    return [item for item in iterable if isinstance(item, dict)]


def known_embedding_rows_for_id(known: dict[str, Any], performer_id: str) -> list[int]:
    rows = []
    for row, mapped_id in known.get("performer_map", {}).items():
        if str(mapped_id) == str(performer_id) and str(row).isdigit():
            rows.append(int(row))
    return sorted(rows)


def registry_name_keys(registry: dict[str, Any]) -> dict[str, tuple[str, set[str]]]:
    lookup: dict[str, tuple[str, set[str]]] = {}
    for slug, entry in (registry.get("performers") or {}).items():
        if not isinstance(entry, dict):
            continue
        name = canonical_performer_name(str(entry.get("name") or slug), registry)
        keys = {normalize_identity_key(str(slug)), normalize_identity_key(name)}
        keys.update(normalize_identity_key(str(alias)) for alias in entry.get("aliases", []) or [] if alias)
        keys = {key for key in keys if key}
        if keys:
            lookup[normalize_identity_key(name)] = (name, keys)
    return lookup


def video_matches_known_name(video_path: Path, source_dir: Path, name_keys: set[str]) -> bool:
    try:
        rel_parts = [normalize_identity_key(part) for part in video_path.relative_to(source_dir).parts[:-1]]
    except ValueError:
        rel_parts = []
    filename_key = normalize_identity_key(video_path.stem)
    for key in name_keys:
        if not key:
            continue
        if key in rel_parts:
            return True
        if any(part == key or part.endswith(key) for part in rel_parts):
            return True
        if key in filename_key:
            return True
    return False


def collect_direct_enrollment_video_records(config: OrganizerConfig, registry: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    by_key: dict[str, list[dict[str, Any]]] = {}
    known = registry_name_keys(registry)
    if not known:
        return by_key
    for video_path in find_videos(config.source_dir, config.recursive):
        if any(part in {config.review_dir_name, "backups", "review_exports", "known_performers"} for part in video_path.parts):
            continue
        for key, (name, name_keys) in known.items():
            if not video_matches_known_name(video_path, config.source_dir, name_keys):
                continue
            by_key.setdefault(key, []).append(
                {
                    "video_path": str(video_path),
                    "path": str(video_path),
                    "_meta_path": str(meta_path_for(video_path)),
                    "source_kind": "direct_video_match",
                    "assignment_decision": {
                        "suggested_name": name,
                        "confidence": 0.7,
                        "review_required": False,
                        "why": "Current video path or filename matches a known performer.",
                    },
                }
            )
            break
    return by_key


def collect_enrollment_source_records(config: OrganizerConfig, registry: dict[str, Any] | None = None) -> dict[str, list[dict[str, Any]]]:
    by_key: dict[str, list[dict[str, Any]]] = {}
    for record in collect_metadata(config.source_dir, config.recursive):
        names: list[str] = []
        pending = record.get("manual_correction_pending")
        if isinstance(pending, dict) and pending.get("new_canonical_name"):
            names.append(str(pending.get("new_canonical_name")))
        confirmed_model = record.get("manual_confirmed_model")
        if isinstance(confirmed_model, dict) and confirmed_model.get("name"):
            names.append(str(confirmed_model.get("name")))
        elif not pending:
            for correction in record.get("manual_corrections") or []:
                if isinstance(correction, dict) and correction.get("status") == "confirmed" and correction.get("new_canonical_name"):
                    names.append(str(correction.get("new_canonical_name")))
        decision = normalize_assignment_decision(record.get("assignment_decision"))
        if decision.get("suggested_name"):
            names.append(str(decision.get("suggested_name")))
        for performer in record.get("performers") or []:
            if isinstance(performer, dict) and performer.get("name") and performer.get("name") != "unknown performer":
                names.append(str(performer.get("name")))
        for candidate in ((record.get("metadata_hints") or {}).get("candidate_names") or []):
            if (
                isinstance(candidate, dict)
                and candidate.get("name")
                and not candidate.get("not_performer_name")
                and str(candidate.get("source") or "") != "site_watermark"
            ):
                names.append(str(candidate.get("name")))
        for name in names:
            canonical = canonical_performer_name(name, registry) if registry else name
            key = normalize_identity_key(canonical)
            if key:
                by_key.setdefault(key, []).append(record)
    if registry:
        direct_by_key = collect_direct_enrollment_video_records(config, registry)
        for key, records in direct_by_key.items():
            existing_videos = {str(item.get("video_path") or "") for item in by_key.get(key, [])}
            for record in records:
                if str(record.get("video_path") or "") not in existing_videos:
                    by_key.setdefault(key, []).append(record)
                    existing_videos.add(str(record.get("video_path") or ""))
    return {key: dedupe_enrollment_records(records) for key, records in by_key.items()}


def dedupe_enrollment_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        path = str(record.get("video_path") or record.get("path") or "")
        meta = str(record.get("_meta_path") or "")
        key = path or meta
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(record)
    return deduped


def merge_candidate_groups_by_canonical(candidate_payload: dict[str, Any], registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for group in candidate_payload.get("groups", []):
        if not isinstance(group, dict):
            continue
        raw_name = str(group.get("name") or group.get("slug") or "")
        canonical_name = canonical_performer_name(raw_name, registry)
        canonical_slug = slugify(canonical_name)
        target = merged.setdefault(
            canonical_slug,
            {
                **group,
                "slug": canonical_slug,
                "name": canonical_name,
                "recommended_crops": [],
                "recommended_stills": [],
                "records": [],
            },
        )
        for field in ("recommended_crops", "recommended_stills", "records"):
            target[field] = merge_unique_values(target.get(field, []), group.get(field, []))
        if group.get("blocked_reason") and not target.get("blocked_reason"):
            target["blocked_reason"] = group.get("blocked_reason")
    return merged


def enrollment_group_status(presence: dict[str, Any], records: list[dict[str, Any]]) -> tuple[str, str]:
    registry_entry = presence.get("registry_entry") if isinstance(presence.get("registry_entry"), dict) else {}
    if registry_entry.get("faceless") or registry_entry.get("face_enrollment_status") == "faceless":
        return "faceless performer", "Marked by user as a creator/model whose current content does not show a usable face."
    if presence.get("known_performers_record") and presence.get("embedding_row") is not None:
        return "face-enrolled", "Known performer has at least one embedding row."
    if presence.get("known_performers_record") and presence.get("embedding_row") is None:
        return "known_performers record present but missing embedding rows", "Known DB record exists without mapped embedding rows."
    if any(isinstance(record.get("manual_correction_pending"), dict) for record in records):
        return "unknown/review items with pending manual correction", "A sidecar has a pending manual correction."
    if presence.get("registry_match"):
        return "user-confirmed but not face-enrolled", "Registry contains a confirmed/text performer without a local face embedding."
    if presence.get("model_index_match"):
        return "registry/model_index present but missing known_performers record", "Model index references this performer but the known face DB does not."
    return "profile-url/text-known but not face-enrolled", "Text/profile evidence exists, but no local face enrollment is present."


def build_enrollment_groups(config: OrganizerConfig) -> dict[str, Any]:
    registry = load_performer_registry(config.verification_registry_path)
    model_path = config.verification_registry_path.with_name("model_index.json")
    model_lookup = model_index_lookup(model_path)
    known = known_db_summary(config.db_dir)
    records_by_key = collect_enrollment_source_records(config, registry)
    names_by_key: dict[str, str] = {}
    reasons_by_key: dict[str, list[str]] = {}

    for slug, entry in (registry.get("performers") or {}).items():
        if not isinstance(entry, dict):
            continue
        name = canonical_performer_name(str(entry.get("name") or slug), registry)
        key = normalize_identity_key(name or slug)
        if key:
            names_by_key.setdefault(key, name)
            reasons_by_key.setdefault(key, []).append("registry")
    for model in iter_model_index_models(model_path):
        name = canonical_performer_name(str(model.get("name") or model.get("slug") or model.get("id") or ""), registry)
        key = normalize_identity_key(name)
        if key:
            names_by_key.setdefault(key, name)
            reasons_by_key.setdefault(key, []).append("model_index")
    for performer in known.get("performers", []):
        if not isinstance(performer, dict):
            continue
        name = canonical_performer_name(str(performer.get("name") or performer.get("id") or ""), registry)
        key = normalize_identity_key(name)
        if key:
            names_by_key.setdefault(key, name)
            reasons_by_key.setdefault(key, []).append("known_performers")
    for key, records in records_by_key.items():
        if key in names_by_key:
            continue
        name = ""
        for record in records:
            pending = record.get("manual_correction_pending")
            if isinstance(pending, dict) and pending.get("new_canonical_name"):
                name = canonical_performer_name(str(pending.get("new_canonical_name")), registry)
                break
            decision = normalize_assignment_decision(record.get("assignment_decision"))
            if decision.get("suggested_name"):
                name = canonical_performer_name(str(decision.get("suggested_name")), registry)
                break
        if name:
            names_by_key[key] = name
            reasons_by_key.setdefault(key, []).append("sidecar_evidence")

    candidate_payload = load_json(enrollment_review_dir(config) / "enrollment_candidates.json", {"groups": []})
    candidates_by_slug = merge_candidate_groups_by_canonical(candidate_payload, registry)
    groups = []
    for key, name in sorted(names_by_key.items(), key=lambda pair: pair[1].lower()):
        records = records_by_key.get(key, [])
        presence = performer_presence(name, registry, model_lookup, known)
        status, why = enrollment_group_status(presence, records)
        candidate_group = candidates_by_slug.get(slugify(name), {})
        rejected_paths = rejected_crop_paths(config, name)
        rejected_signatures = rejected_crop_signatures(config, name)
        accepted_paths = accepted_source_crop_paths(presence.get("known_record"))
        crops = [
            crop
            for crop in candidate_group.get("recommended_crops") or []
            if str(crop.get("crop_path") or "") not in rejected_paths
            and crop_recommendation_signature(crop) not in rejected_signatures
            and str(crop.get("crop_path") or "") not in accepted_paths
        ]
        live_video_count = live_candidate_video_count(records)
        crop_limit = max(24, int(live_video_count or 1) * ENROLLMENT_MAX_CROPS_PER_VIDEO)
        crops = balanced_candidate_crops(
            enrollable_candidate_crops(crops, config),
            limit=crop_limit,
            per_video_limit=ENROLLMENT_MAX_CROPS_PER_VIDEO,
        )
        blocked = str(candidate_group.get("blocked_reason") or "")
        if not blocked and not crops:
            blocked = "candidate generation not run yet or no associated videos found"
        full_record_entries = [{"video_path": str(record.get("video_path") or record.get("path") or "")} for record in records]
        groups.append(
            {
                "slug": slugify(name),
                "name": name,
                "status": status,
                "why": why,
                "registry_present": bool(presence.get("registry_match")),
                "model_index_present": bool(presence.get("model_index_match")),
                "known_performers_record": bool(presence.get("known_performers_record")),
                "known_performer_id": str(presence.get("known_performer_id") or ""),
                "embedding_rows": presence.get("embedding_rows") or ([int(presence["embedding_row"])] if presence.get("embedding_row") is not None else []),
                "candidate_videos": live_video_count,
                "candidate_face_crops": len(crops),
                "blocked_reason": blocked,
                "exists_because": sorted(set(reasons_by_key.get(key, []) + (["sidecar_evidence"] if records else []))),
                "source_video_keys": group_source_video_keys({"records": full_record_entries}),
                "records": [
                    {
                        "video_path": str(record.get("video_path") or ""),
                        "meta_path": str(record.get("_meta_path") or ""),
                        "pending_manual_correction": bool(record.get("manual_correction_pending")),
                    }
                    for record in records[:12]
                ],
                "recommended_crops": crops,
                "recommended_stills": review_stills_by_video(candidate_group.get("recommended_stills") or [], ENROLLMENT_MIN_SCREENS_PER_VIDEO),
                "recommendation_source_videos": candidate_group.get("recommendation_source_videos") or [],
                "recommendations_refreshed_at": candidate_group.get("recommendations_refreshed_at"),
                "recommendation_scan_summary": candidate_group.get("recommendation_scan_summary") or [],
                "recommendation_generation_settings": candidate_group.get("recommendation_generation_settings") or {},
            }
        )
    return {
        "schema": "media-face-enrollment-groups/v1",
        "generated_at": utc_now(),
        "source_dir": str(config.source_dir),
        "groups": groups,
        "summary": {
            "groups_found": len(groups),
            "groups_missing_embeddings": sum(1 for group in groups if not group["embedding_rows"]),
            "already_face_enrolled": sum(1 for group in groups if group["embedding_rows"]),
            "candidate_crops": sum(int(group["candidate_face_crops"]) for group in groups),
            "blocked_groups": sum(1 for group in groups if group.get("blocked_reason")),
        },
    }


def enrollment_timestamps(duration: float | None, count: int = 6) -> list[float]:
    count = max(3, int(count))
    if duration and duration > 12:
        return [float(item) for item in np.linspace(max(2.0, duration * 0.08), max(3.0, duration * 0.92), num=count)]
    return [float(item) for item in np.linspace(1.0, float(count), num=count)]


def extract_frame_at(video_path: Path, frame_path: Path, timestamp: float) -> None:
    require_ffmpeg()
    frame_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{float(timestamp):.2f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(frame_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)


def face_quality_score(face: Any, frame_size: tuple[int, int], sharpness: float | None = None) -> float:
    width, height = frame_size
    bbox = [float(value) for value in getattr(face, "bbox", [0, 0, 0, 0]).tolist()]
    face_area = max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1])
    area_ratio = face_area / max(1.0, float(width * height))
    det_score = float(getattr(face, "det_score", 0.0))
    sharp_component = min(1.0, max(0.0, float(sharpness or 0.0) / 150.0))
    return round(det_score * 0.55 + min(1.0, area_ratio * 18.0) * 0.35 + sharp_component * 0.10, 4)


def image_sharpness(path: Path) -> float | None:
    try:
        import cv2

        image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if image is None:
            return None
        return float(cv2.Laplacian(image, cv2.CV_64F).var())
    except Exception:
        return None


def dedupe_candidate_crops(crops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, int]] = set()
    deduped: list[dict[str, Any]] = []
    for crop in sorted(crops, key=lambda item: float(item.get("quality_score") or 0), reverse=True):
        key = (str(crop.get("source_video") or ""), int(round(float(crop.get("timestamp") or 0) / 4.0)))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(crop)
    return deduped


def enrollable_candidate_crops(crops: list[dict[str, Any]], config: OrganizerConfig) -> list[dict[str, Any]]:
    filtered = []
    min_score = max(float(config.min_face_score), ENROLLMENT_MIN_DET_SCORE)
    for crop in crops:
        try:
            detection_score = float(crop.get("enrollment_detection_score") or crop.get("detection_score") or 0)
        except Exception:
            detection_score = 0.0
        if detection_score >= min_score:
            filtered.append(crop)
    return filtered


def balanced_candidate_crops(crops: list[dict[str, Any]], limit: int = 12, per_video_limit: int = 3) -> list[dict[str, Any]]:
    by_video: dict[str, list[dict[str, Any]]] = {}
    for crop in sorted(crops, key=lambda item: float(item.get("quality_score") or 0), reverse=True):
        key = str(crop.get("source_video") or crop.get("source_video_name") or "")
        by_video.setdefault(key, []).append(crop)
    selected: list[dict[str, Any]] = []
    if len(by_video) <= 1:
        return [item for values in by_video.values() for item in values][:limit]
    used_per_video = {key: 0 for key in by_video}
    while len(selected) < limit:
        added = False
        for key in sorted(by_video, key=lambda value: Path(value).name.lower()):
            if used_per_video[key] >= per_video_limit or not by_video[key]:
                continue
            selected.append(by_video[key].pop(0))
            used_per_video[key] += 1
            added = True
            if len(selected) >= limit:
                break
        if not added:
            break
    return selected


def review_stills_by_video(stills: list[dict[str, Any]], per_video_limit: int = ENROLLMENT_MIN_SCREENS_PER_VIDEO) -> list[dict[str, Any]]:
    manual_stills = [still for still in stills if str(still.get("status") or "") == "manual_crop_candidate"]
    failed_stills = [still for still in stills if str(still.get("status") or "") == "still_candidate"]
    by_video: dict[str, list[dict[str, Any]]] = {}
    for still in sorted(manual_stills, key=lambda item: (str(item.get("source_video_name") or ""), float(item.get("timestamp") or 0))):
        key = str(still.get("source_video") or still.get("source_video_name") or "")
        by_video.setdefault(key, []).append(still)
    selected: list[dict[str, Any]] = []
    for key in sorted(by_video, key=lambda value: Path(value).name.lower()):
        selected.extend(by_video[key])
    failed_by_video: dict[str, list[dict[str, Any]]] = {}
    for still in sorted(failed_stills, key=lambda item: (str(item.get("source_video_name") or ""), float(item.get("timestamp") or 0))):
        key = str(still.get("source_video") or still.get("source_video_name") or "")
        failed_by_video.setdefault(key, []).append(still)
    for key in sorted(failed_by_video, key=lambda value: Path(value).name.lower()):
        remaining = max(0, per_video_limit - len([item for item in selected if str(item.get("source_video") or item.get("source_video_name") or "") == key]))
        if remaining:
            selected.extend(failed_by_video[key][:remaining])
    return selected


def crop_recommendation_signature(crop: dict[str, Any] | str) -> str:
    if isinstance(crop, dict):
        source_video = str(crop.get("source_video") or "")
        timestamp = crop.get("timestamp")
        if source_video and timestamp not in (None, ""):
            try:
                return f"{source_video}|t:{int(round(float(timestamp) * 10))}"
            except Exception:
                return f"{source_video}|t:{timestamp}"
        still_path = str(crop.get("still_path") or "")
        if source_video and still_path:
            return f"{source_video}|still:{Path(still_path).stem}"
        crop_path = str(crop.get("crop_path") or "")
    else:
        crop_path = str(crop or "")
    stem = Path(crop_path).stem
    stable_stem = re.sub(r"-face-[0-9a-fA-F]+$", "", stem)
    stable_stem = re.sub(r"-manual-[0-9a-fA-F]+$", "", stable_stem)
    return f"crop-stem:{stable_stem}" if stable_stem else crop_path


def video_path_key(video_path: Path | str) -> str:
    path = Path(video_path)
    if not path.is_absolute() and path.exists():
        path = path.resolve()
    try:
        return f"{path}:{path.stat().st_mtime_ns if path.exists() else 0}"
    except Exception:
        return str(video_path)


def group_source_video_keys(group: dict[str, Any]) -> list[str]:
    keys = []
    seen: set[str] = set()
    for record in group.get("records") or []:
        if not isinstance(record, dict):
            continue
        raw = str(record.get("video_path") or record.get("meta_path") or "")
        if not raw:
            continue
        raw_path = Path(raw)
        if raw_path.suffix.lower() in VIDEO_EXTENSIONS and not raw_path.exists():
            continue
        key = video_path_key(raw_path if raw_path.exists() else raw)
        if key not in seen:
            seen.add(key)
            keys.append(key)
    return sorted(keys)


def scanned_video_keys(video_paths: list[Path]) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for video_path in video_paths:
        key = video_path_key(video_path)
        if key not in seen:
            seen.add(key)
            keys.append(key)
    return sorted(keys)


def missing_enrollment_video_paths(video_paths: list[Path], scanned_keys: set[str]) -> list[Path]:
    missing: list[Path] = []
    seen: set[str] = set()
    for video_path in video_paths:
        key = video_path_key(video_path)
        if key in scanned_keys or key in seen:
            continue
        seen.add(key)
        missing.append(video_path)
    return missing


def prioritize_enrollment_videos(video_paths: list[Path], already_scanned_keys: set[str]) -> list[Path]:
    unscanned: list[Path] = []
    scanned: list[Path] = []
    for path in video_paths:
        if video_path_key(path) in already_scanned_keys:
            scanned.append(path)
        else:
            unscanned.append(path)
    return unscanned + scanned


def live_candidate_video_count(records: list[dict[str, Any]]) -> int:
    videos: set[str] = set()
    for record in records:
        raw_path = str(record.get("video_path") or record.get("path") or "")
        if not raw_path:
            continue
        video_path = Path(raw_path)
        if not video_path.exists() and raw_path.startswith("/DATA/"):
            video_path = Path(raw_path.replace("/DATA/", "/mnt/spirit-8tb/media/", 1))
        if video_path.suffix.lower() in VIDEO_EXTENSIONS:
            videos.add(str(video_path if video_path.exists() else raw_path))
    return len(videos)


def recommendations_are_fresh(group: dict[str, Any], *, require_current_settings: bool = True) -> bool:
    recommendation_meta = group.get("recommendation_source_videos")
    if not isinstance(recommendation_meta, list):
        return False
    settings = group.get("recommendation_generation_settings") or {}
    if require_current_settings:
        if int(settings.get("min_screens_per_video") or 0) < ENROLLMENT_MIN_SCREENS_PER_VIDEO:
            return False
        if int(settings.get("max_crops_per_video") or 0) < ENROLLMENT_MAX_CROPS_PER_VIDEO:
            return False
    required_keys = set(group.get("source_video_keys") or group_source_video_keys(group))
    if not required_keys:
        return bool(recommendation_meta)
    scanned_keys = {str(item) for item in recommendation_meta}
    return required_keys <= scanned_keys


def blocked_reason_for_candidates(records: list[dict[str, Any]], crops: list[dict[str, Any]], failures: list[str]) -> str:
    if not records:
        return "text-known but no associated videos found"
    if not crops:
        return failures[0] if failures else "no face detected"
    if len(crops) < 5:
        parts = [f"only {len(crops)} valid crops found"]
        if len({str(record.get("video_path") or "") for record in records}) <= 1:
            parts.append("only one source video found")
        if failures:
            parts.append(failures[0])
        return "; ".join(parts)
    return ""


def generate_enrollment_candidates(
    config: OrganizerConfig,
    *,
    max_groups: int | None = None,
    frames_per_group: int = 18,
    target_name: str | None = None,
    refresh_pages: bool = True,
    missing_only: bool = False,
) -> dict[str, Any]:
    groups_payload = build_enrollment_groups(config)
    registry = load_performer_registry(config.verification_registry_path)
    records_by_key = collect_enrollment_source_records(config, registry)
    existing_payload = load_json(enrollment_review_dir(config) / "enrollment_candidates.json", {"groups": []})
    existing_by_slug = {
        str(group.get("slug")): group
        for group in existing_payload.get("groups", [])
        if isinstance(group, dict) and group.get("slug")
    }
    recognizer = InsightFaceRecognizer(config.model_name, config.ctx_id, config.det_size)
    out_dir = enrollment_review_dir(config)
    out_dir.mkdir(parents=True, exist_ok=True)
    generated_groups = []
    target_key = normalize_identity_key(target_name or "")
    selected_groups = [
        group
        for group in groups_payload["groups"]
        if not target_key or target_key in {normalize_identity_key(str(group.get("name") or "")), normalize_identity_key(str(group.get("slug") or ""))}
    ]
    limit = max_groups if max_groups is not None else config.sample_limit
    limited_groups = selected_groups[: limit or None]

    def write_candidate_progress(name: str, completed: int) -> None:
        write_smart_rescan_status(
            {
                "phase": "select_face_pictures",
                "phaseLabel": "Refreshing model face candidates",
                "currentItem": {"kind": "model", "name": name},
                "modelProgress": {
                    "total": len(limited_groups),
                    "completed": completed,
                },
            }
        )

    for group_index, group in enumerate(limited_groups, start=1):
        name = str(group["name"])
        write_candidate_progress(name, group_index - 1)
        key = normalize_identity_key(name)
        records = records_by_key.get(key, [])
        video_paths: list[Path] = []
        for record in records:
            video_path = resolve_media_path(str(record.get("_resolved_video_path") or record.get("video_path") or record.get("path") or ""), config)
            if video_path.exists() and video_path.suffix.lower() in VIDEO_EXTENSIONS and video_path not in video_paths:
                video_paths.append(video_path)
        if not video_paths:
            group["recommended_crops"] = []
            group["recommended_stills"] = []
            group["blocked_reason"] = "text-known but no associated videos found"
            generated_groups.append(group)
            write_candidate_progress(name, group_index)
            continue
        slug = str(group.get("slug") or slugify(name))
        existing_group = existing_by_slug.get(slug, {})
        existing_crops = list(existing_group.get("recommended_crops") or [])
        existing_stills = list(existing_group.get("recommended_stills") or [])
        existing_scanned_keys = {str(item) for item in (existing_group.get("recommendation_source_videos") or [])}
        if missing_only:
            video_paths = missing_enrollment_video_paths(video_paths, existing_scanned_keys)
            if not video_paths:
                group["recommended_crops"] = existing_crops
                group["recommended_stills"] = existing_stills
                group["candidate_face_crops"] = len(enrollable_candidate_crops(existing_crops, config))
                group["blocked_reason"] = ""
                group["recommendation_scan_summary"] = list(existing_group.get("recommendation_scan_summary") or [])
                generated_groups.append(group)
                write_candidate_progress(name, group_index)
                continue
        group_dir = out_dir / slugify(name)
        still_dir = group_dir / "stills"
        crop_dir = group_dir / "crops"
        still_dir.mkdir(parents=True, exist_ok=True)
        crop_dir.mkdir(parents=True, exist_ok=True)
        crops: list[dict[str, Any]] = []
        stills: list[dict[str, Any]] = []
        failures: list[str] = []
        scan_summary: list[dict[str, Any]] = []
        video_limit = len(video_paths) if (target_key or missing_only) else min(len(video_paths), 3)
        ordered_video_paths = prioritize_enrollment_videos(video_paths, existing_scanned_keys) if not target_key else video_paths
        scanned_video_paths = ordered_video_paths[:video_limit]
        scanned_path_strings = {str(path) for path in scanned_video_paths}
        per_video = ENROLLMENT_SCAN_FRAMES_PER_VIDEO if target_key else max(ENROLLMENT_MIN_SCREENS_PER_VIDEO, int(np.ceil(frames_per_group / max(1, video_limit))))
        for video_path in scanned_video_paths:
            duration = ffprobe_duration(video_path)
            video_summary = {
                "source_video": str(video_path),
                "source_video_name": video_path.name,
                "frames_sampled": 0,
                "faces_detected": 0,
                "candidate_crops": 0,
                "failures": [],
            }
            for index, timestamp in enumerate(enrollment_timestamps(duration, per_video), 1):
                still_path = still_dir / f"{slugify(video_path.stem)}-{index:02d}-{int(timestamp):06d}.jpg"
                try:
                    video_summary["frames_sampled"] += 1
                    if not still_path.exists():
                        extract_frame_at(video_path, still_path, timestamp)
                    faces = recognizer.detect(still_path)
                    video_summary["faces_detected"] += len(faces)
                    if not faces:
                        failures.append("no face detected")
                        video_summary["failures"].append("no face detected")
                        stills.append(
                            {
                                "id": still_path.stem,
                                "still_path": str(still_path),
                                "source_video": str(video_path),
                                "source_video_name": video_path.name,
                                "timestamp": round(float(timestamp), 2),
                                "status": "still_candidate",
                            }
                        )
                        continue
                    try:
                        frame_image = recognizer.image_cls.open(still_path)
                        frame_size = frame_image.size
                        frame_image.close()
                    except Exception:
                        frame_size = (1, 1)
                    if len(faces) > 1:
                        failures.append("multiple faces detected")
                        video_summary["failures"].append("multiple faces detected")
                    sharpness = image_sharpness(still_path)
                    valid_faces = []
                    for face in faces:
                        keep, reason = should_keep_enrollment_face(face, frame_size, config)
                        if keep:
                            valid_faces.append(face)
                        else:
                            failures.append(reason)
                            video_summary["failures"].append(reason)
                    if not valid_faces:
                        stills.append(
                            {
                                "id": still_path.stem,
                                "still_path": str(still_path),
                                "source_video": str(video_path),
                                "source_video_name": video_path.name,
                                "timestamp": round(float(timestamp), 2),
                                "status": "still_candidate",
                            }
                        )
                        continue
                    face = max(valid_faces, key=lambda item: face_quality_score(item, frame_size, sharpness))
                    crop_path = crop_dir / f"{still_path.stem}-face-{uuid.uuid4().hex[:6]}.jpg"
                    recognizer.save_crop(still_path, face, crop_path)
                    crops.append(
                        {
                            "id": crop_path.stem,
                            "crop_path": str(crop_path),
                            "still_path": str(still_path),
                            "source_video": str(video_path),
                            "source_video_name": video_path.name,
                            "timestamp": round(float(timestamp), 2),
                            "detection_score": round(float(getattr(face, "det_score", 0.0)), 4),
                            "enrollment_detection_score": round(float(getattr(face, "det_score", 0.0)), 4),
                            "quality_score": face_quality_score(face, frame_size, sharpness),
                            "sharpness": round(float(sharpness), 2) if sharpness is not None else None,
                            "status": "candidate",
                        }
                    )
                    video_summary["candidate_crops"] += 1
                except Exception as exc:
                    failures.append(f"missing sidecars or frame extraction failed: {exc}")
                    video_summary["failures"].append(f"frame extraction failed: {exc}")
            video_summary["failures"] = sorted(set(str(item) for item in video_summary["failures"]))[:6]
            scan_summary.append(video_summary)
        if target_key:
            preserved_crops = []
            preserved_stills = []
        else:
            preserved_crops = [
                crop
                for crop in existing_crops
                if isinstance(crop, dict) and str(crop.get("source_video") or "") not in scanned_path_strings
            ]
            preserved_stills = [
                still
                for still in existing_stills
                if isinstance(still, dict) and str(still.get("source_video") or "") not in scanned_path_strings
            ]
        merged_crops = dedupe_candidate_crops([*preserved_crops, *crops])
        merged_stills = [
            still
            for still in preserved_stills + stills
            if isinstance(still, dict) and str(still.get("still_path") or "")
        ]
        crop_limit = max(24, len(video_paths) * ENROLLMENT_MAX_CROPS_PER_VIDEO)
        recommendations = balanced_candidate_crops(
            enrollable_candidate_crops(merged_crops, config),
            limit=crop_limit,
            per_video_limit=ENROLLMENT_MAX_CROPS_PER_VIDEO,
        )
        group["recommended_crops"] = recommendations
        group["recommended_stills"] = review_stills_by_video(merged_stills, ENROLLMENT_MIN_SCREENS_PER_VIDEO)
        group["candidate_face_crops"] = len(recommendations)
        group["blocked_reason"] = blocked_reason_for_candidates(records, recommendations, failures)
        scanned_keys = sorted(set(existing_scanned_keys) | set(scanned_video_keys(scanned_video_paths)))
        group["recommendation_source_videos"] = scanned_keys
        group["source_video_keys"] = group_source_video_keys(
            {"records": [{"video_path": str(record.get("video_path") or record.get("path") or "")} for record in records]}
        )
        group["recommendations_refreshed_at"] = utc_now()
        group["recommendation_scan_summary"] = scan_summary
        group["recommendation_generation_settings"] = {
            "min_screens_per_video": ENROLLMENT_MIN_SCREENS_PER_VIDEO,
            "scan_frames_per_video": per_video,
            "max_crops_per_video": ENROLLMENT_MAX_CROPS_PER_VIDEO,
            "video_limit": len(scanned_video_paths),
            "videos_scanned_total": len(scanned_keys),
            "videos_required_total": len(group["source_video_keys"]),
        }
        generated_groups.append(group)
        write_candidate_progress(name, group_index)
    merged_by_slug = dict(existing_by_slug)
    for group in generated_groups:
        merged_by_slug[str(group.get("slug"))] = group
    payload_groups = list(merged_by_slug.values())
    payload = {
        "schema": "media-face-enrollment-candidates/v1",
        "generated_at": utc_now(),
        "source_dir": str(config.source_dir),
        "review_dir": str(out_dir),
        "groups": payload_groups,
        "summary": {
            "groups_found": len(payload_groups),
            "groups_missing_embeddings": sum(1 for group in payload_groups if not group.get("embedding_rows")),
            "candidate_crops_generated": sum(len(group.get("recommended_crops") or []) for group in payload_groups),
            "blocked_groups": sum(1 for group in payload_groups if group.get("blocked_reason")),
            "groups_generated_this_run": len(generated_groups),
        },
        "safety": {
            "source_media_modified": False,
            "production_enrollment_performed": False,
            "internet_face_recognition": False,
        },
    }
    json_dump(out_dir / "enrollment_candidates.json", payload)
    if refresh_pages:
        generate_enrollment_queue_page(config)
    return payload


def enrollment_missing_video_count(group: dict[str, Any]) -> int:
    required = set(group.get("source_video_keys") or group_source_video_keys(group))
    scanned = {str(item) for item in (group.get("recommendation_source_videos") or [])}
    return len(required - scanned)


def refresh_stale_enrolled_recommendations(
    config: OrganizerConfig,
    *,
    only_unenrolled: bool = False,
    max_groups: int | None = None,
) -> dict[str, Any]:
    payload = build_enrollment_groups(config)
    refreshed: list[str] = []
    checked = 0
    stale_groups: list[dict[str, Any]] = []
    for group in payload.get("groups", []):
        if only_unenrolled and group.get("embedding_rows"):
            continue
        checked += 1
        has_recommendations = bool(group.get("recommended_crops") or group.get("recommended_stills"))
        if has_recommendations and recommendations_are_fresh(group, require_current_settings=False):
            continue
        stale_groups.append(group)
    stale_groups.sort(
        key=lambda item: (
            -enrollment_missing_video_count(item),
            str(item.get("name") or "").lower(),
        )
    )
    if max_groups is not None:
        stale_groups = stale_groups[: max(0, int(max_groups))]
    for group in stale_groups:
        generate_enrollment_candidates(
            config,
            max_groups=None,
            target_name=str(group.get("name") or ""),
            refresh_pages=False,
        )
        refreshed.append(str(group.get("name") or ""))
    return {
        "schema": "media-face-enrolled-recommendation-refresh/v1",
        "checked_groups": checked,
        "checked_enrolled_groups": sum(1 for group in payload.get("groups", []) if group.get("embedding_rows")),
        "refreshed_groups": refreshed,
        "refreshed_count": len(refreshed),
        "only_unenrolled": only_unenrolled,
        "max_groups": max_groups,
    }


def validate_crop_coordinates(coords: dict[str, Any], width: int, height: int) -> tuple[int, int, int, int]:
    try:
        x = int(float(coords.get("x")))
        y = int(float(coords.get("y")))
        w = int(float(coords.get("width")))
        h = int(float(coords.get("height")))
    except Exception as exc:
        raise RuntimeError("invalid crop coordinates") from exc
    if x < 0 or y < 0 or w <= 0 or h <= 0:
        raise RuntimeError("invalid crop coordinates: x/y must be non-negative and width/height must be positive")
    if x + w > width or y + h > height:
        raise RuntimeError("invalid crop coordinates: crop extends outside still frame")
    if w < 16 or h < 16:
        raise RuntimeError("invalid crop coordinates: crop is too small")
    return x, y, x + w, y + h


def save_manual_crop_candidate(config: OrganizerConfig, payload: dict[str, Any]) -> dict[str, Any]:
    from PIL import Image

    performer = str(payload.get("performer") or payload.get("name") or "").strip()
    still_path = Path(str(payload.get("still_path") or ""))
    if not performer:
        raise RuntimeError("performer is required")
    if not still_path.exists() or not still_path.is_file():
        raise RuntimeError(f"still frame does not exist: {still_path}")
    image = Image.open(still_path).convert("RGB")
    box = validate_crop_coordinates(payload.get("crop") or payload, image.width, image.height)
    target_dir = enrollment_review_dir(config) / slugify(performer) / "manual-crops"
    target_dir.mkdir(parents=True, exist_ok=True)
    crop_path = target_dir / f"{slugify(still_path.stem)}-manual-{uuid.uuid4().hex[:8]}.jpg"
    image.crop(box).save(crop_path, "JPEG", quality=90)
    validation = {"usable_face_count": 0, "status": "stored_candidate_evidence", "reason": ""}
    try:
        recognizer = InsightFaceRecognizer(config.model_name, config.ctx_id, config.det_size)
        faces = recognizer.detect(crop_path)
        validation["usable_face_count"] = len(faces)
        if len(faces) == 1:
            validation["status"] = "valid_candidate"
        elif not faces:
            validation["reason"] = "no-face crop stored as candidate evidence only"
        else:
            validation["reason"] = "multi-face crop stored as candidate evidence only"
    except Exception as exc:
        validation["reason"] = f"face validation unavailable: {exc}"
    record = {
        "schema": "media-face-enrollment-manual-crop/v1",
        "created_at": utc_now(),
        "performer": performer,
        "crop_path": str(crop_path),
        "still_path": str(still_path),
        "source_video": str(payload.get("source_video") or ""),
        "timestamp": payload.get("timestamp"),
        "validation": validation,
        "enrolled": False,
    }
    json_dump(crop_path.with_suffix(".json"), record)
    return record


def backup_known_performers_files(config: OrganizerConfig) -> Path:
    backup_root = timestamped_backup_root(config) / "known_performers-enrollment"
    backup_root.mkdir(parents=True, exist_ok=True)
    for filename in ("index.json", "performer_map.json", "embeddings.npy"):
        source = config.db_dir / filename
        if source.exists():
            shutil.copy2(source, backup_root / filename)
    json_dump(
        backup_root / "backup_manifest.json",
        {
            "schema": "media-face-enrollment-known-db-backup/v1",
            "created_at": utc_now(),
            "db_dir": str(config.db_dir),
            "files": [filename for filename in ("index.json", "performer_map.json", "embeddings.npy") if (config.db_dir / filename).exists()],
        },
    )
    return backup_root


def resolve_artifact_path(value: str | Path, config: OrganizerConfig) -> Path:
    text = str(value or "")
    if not text:
        return Path("")
    if text.startswith("/DATA/yes"):
        return config.source_dir / text.removeprefix("/DATA/yes").lstrip("/")
    if text.startswith("/mnt/spirit-8tb/media/yes"):
        return config.source_dir / text.removeprefix("/mnt/spirit-8tb/media/yes").lstrip("/")
    path = Path(text)
    if path.exists() or path.is_absolute():
        return path
    return Path.cwd() / path


def equivalent_artifact_key(value: str | Path, config: OrganizerConfig) -> str:
    resolved = resolve_artifact_path(value, config)
    return path_key(resolved if resolved else value)


def resolve_enrollment_crop_path(value: str | Path, config: OrganizerConfig) -> Path:
    crop_path = resolve_artifact_path(value, config)
    if not crop_path.exists() or not crop_path.is_file():
        raise RuntimeError(f"crop does not exist: {value}")
    review_dir = enrollment_review_dir(config)
    try:
        crop_path.relative_to(review_dir)
    except ValueError as exc:
        raise RuntimeError(f"crop is outside the enrollment review folder: {value}") from exc
    return crop_path


def copy_manifest_file(source: Path, backup_root: Path, file_type: str, manifest: dict[str, Any], *, base: Path | None = None) -> None:
    if not source.exists() or not source.is_file():
        manifest.setdefault("missing_files", []).append({"type": file_type, "source": str(source)})
        return
    try:
        relative = source.relative_to(base) if base else Path(source.name)
    except ValueError:
        relative = Path(source.name)
    target = backup_root / file_type / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    manifest.setdefault("files", []).append({"type": file_type, "source": str(source), "backup": str(target), "bytes": source.stat().st_size})


def load_sava_generated_group(config: OrganizerConfig) -> dict[str, Any]:
    enrolled_path = config.report_path.with_name("face_enrolled_performers.json")
    payload = load_json(enrolled_path, {"groups": []})
    for group in payload.get("groups") or []:
        if isinstance(group, dict) and normalize_identity_key(str(group.get("name") or group.get("slug") or "")) == normalize_identity_key(SAVA_GOLDEN_PERFORMER_NAME):
            return group
    return {}


def phase3_backup_sava_current_state(config: OrganizerConfig) -> dict[str, Any]:
    backup_root = timestamped_backup_root(config) / "phase3-sava-before-reset"
    backup_root.mkdir(parents=True, exist_ok=True)
    known = known_db_summary(config.db_dir)
    known_record = (known.get("by_id") or {}).get(SAVA_GOLDEN_PERFORMER_ID) or {}
    generated_group = load_sava_generated_group(config)
    sample_records = known_face_sample_records(config, SAVA_GOLDEN_PERFORMER_ID, known_record)
    ledger = build_model_video_ledger(config, SAVA_GOLDEN_PERFORMER_NAME, SAVA_GOLDEN_PERFORMER_ID, generated_group=generated_group)
    manifest: dict[str, Any] = {
        "schema": "media-face-organizer-phase3-sava-backup/v1",
        "created_at": utc_now(),
        "performer_name": SAVA_GOLDEN_PERFORMER_NAME,
        "performer_id": SAVA_GOLDEN_PERFORMER_ID,
        "source_dir": str(config.source_dir),
        "db_dir": str(config.db_dir),
        "backup_root": str(backup_root),
        "pre_reset_counts": {
            "known_performers_count": known.get("known_performers_count") or len(known.get("performers", [])),
            "embedding_rows": int(known.get("embedding_rows") or 0),
            "sava_embedding_rows": known_embedding_rows_for_id(known, SAVA_GOLDEN_PERFORMER_ID),
            "sava_accepted_sample_records": len(sample_records),
            "ledger_count_types": ledger.get("count_types") or {},
            "generated_candidate_videos": generated_group.get("candidate_videos"),
            "generated_library_video_matches": len(generated_group.get("library_video_matches") or []),
            "generated_pending_video_matches": len(generated_group.get("pending_video_matches") or []),
        },
        "files": [],
        "missing_files": [],
        "reset_performed": False,
        "stop_before_reset_required": True,
    }

    for path in [
        config.db_dir / "index.json",
        config.db_dir / "performer_map.json",
        config.db_dir / "embeddings.npy",
        config.verification_registry_path,
        config.verification_registry_path.with_name("model_index.json"),
        config.report_path.with_name("known_db_audit.json"),
        config.report_path.with_name("face_enrolled_performers.json"),
        config.report_path.with_name("face_enrollment_queue.json"),
    ]:
        copy_manifest_file(path, backup_root, "state", manifest)

    for row in ledger.get("rows") or []:
        sidecar_path = resolve_artifact_path(str(row.get("sidecar_path") or ""), config)
        if sidecar_path:
            copy_manifest_file(sidecar_path, backup_root, "sidecars", manifest, base=config.source_dir)
        receipt_path = resolve_artifact_path(str(row.get("media_ingest_receipt_path") or ""), config)
        if receipt_path:
            copy_manifest_file(receipt_path, backup_root, "media_ingest_receipts", manifest, base=config.source_dir)

    artifact_values: list[str] = []
    for record in sample_records:
        if not isinstance(record, dict):
            continue
        for key in ("sample_path", "source_crop", "source_video"):
            if record.get(key):
                artifact_values.append(str(record.get(key)))
    for field in ("recommended_crops", "recommended_stills"):
        for item in generated_group.get(field) or []:
            if not isinstance(item, dict):
                continue
            for key in ("crop_path", "still_path", "source_video"):
                if item.get(key):
                    artifact_values.append(str(item.get(key)))
    for value in sorted(set(artifact_values)):
        resolved = resolve_artifact_path(value, config)
        if resolved:
            copy_manifest_file(resolved, backup_root, "artifacts", manifest, base=config.source_dir)

    json_dump(backup_root / "sava_enrolled_group.json", generated_group or {})
    json_dump(backup_root / "sava_known_sample_records.json", {"records": sample_records})
    json_dump(backup_root / "sava_source_of_truth_ledger.json", ledger)
    manifest["files"].extend(
        [
            {"type": "derived", "source": "generated_group", "backup": str(backup_root / "sava_enrolled_group.json")},
            {"type": "derived", "source": "known_sample_records", "backup": str(backup_root / "sava_known_sample_records.json")},
            {"type": "derived", "source": "source_of_truth_ledger", "backup": str(backup_root / "sava_source_of_truth_ledger.json")},
        ]
    )
    json_dump(backup_root / "backup_manifest.json", manifest)
    return manifest


def normalized_sample_identity(value: Any) -> str:
    text = str(value or "")
    if not text:
        return ""
    text = text.replace("\\", "/")
    if "/home/source/SpiritOS/" in text:
        text = str(Path.cwd() / text.split("/home/source/SpiritOS/", 1)[1])
    elif text.startswith("//10.0.0.186/SpiritOS/"):
        text = str(Path.cwd() / text.removeprefix("//10.0.0.186/SpiritOS/"))
    elif text.startswith("/home/source/SpiritOS/"):
        text = str(Path.cwd() / text.removeprefix("/home/source/SpiritOS/"))
    path = Path(text)
    if not path.is_absolute():
        path = path.resolve()
    key = path_key(path)
    if key.startswith("//10.0.0.186/spiritos/"):
        return path_key(Path.cwd() / key.removeprefix("//10.0.0.186/spiritos/"))
    return key


def classify_sava_sample_reset_candidates(config: OrganizerConfig) -> dict[str, Any]:
    known = known_db_summary(config.db_dir)
    known_record = (known.get("by_id") or {}).get(SAVA_GOLDEN_PERFORMER_ID) or {}
    samples = known_face_sample_records(config, SAVA_GOLDEN_PERFORMER_ID, known_record)
    referenced_rows: set[int] = set()
    remove_samples: list[dict[str, Any]] = []
    keep_samples: list[dict[str, Any]] = []
    for record in samples:
        sample_path = str(record.get("sample_path") or "")
        source_crop = str(record.get("source_crop") or "")
        source_video = str(record.get("source_video") or "")
        embedding_rows = [int(row) for row in record.get("embedding_rows") or [] if str(row).isdigit()]
        referenced_rows.update(embedding_rows)
        reasons: list[str] = []
        if not embedding_rows:
            reasons.append("missing_embedding_rows")
        if source_video and not resolve_artifact_path(source_video, config).exists():
            reasons.append("source_video_missing")
        if source_crop and not resolve_artifact_path(source_crop, config).exists():
            reasons.append("source_crop_missing")
        if not source_crop and not source_video:
            reasons.append("missing_source_evidence")
        entry = {
            "sample_path": sample_path,
            "source_crop": source_crop,
            "source_video": source_video,
            "embedding_rows": embedding_rows,
            "reasons": sorted(set(reasons)),
        }
        if reasons:
            remove_samples.append(entry)
        else:
            keep_samples.append(entry)

    sava_rows = set(known_embedding_rows_for_id(known, SAVA_GOLDEN_PERFORMER_ID))
    orphan_rows = sorted(sava_rows - referenced_rows)
    return {
        "remove_samples": remove_samples,
        "keep_samples": keep_samples,
        "orphan_embedding_rows": orphan_rows,
        "before_sample_count": len(samples),
        "before_sava_embedding_rows": sorted(sava_rows),
    }


def phase3_reset_sava_stale_samples(config: OrganizerConfig, *, backup_root: str | Path) -> dict[str, Any]:
    sava_only_guard(SAVA_GOLDEN_PERFORMER_NAME, SAVA_GOLDEN_PERFORMER_ID)
    if not backup_root or not Path(backup_root).exists():
        raise RuntimeError("phase3 Sava reset requires an existing backup_root")
    plan = classify_sava_sample_reset_candidates(config)
    remove_identities = {normalized_sample_identity(item.get("sample_path")) for item in plan["remove_samples"]}
    rows_to_remove = {
        int(row)
        for item in plan["remove_samples"]
        for row in item.get("embedding_rows") or []
    }
    rows_to_remove.update(int(row) for row in plan["orphan_embedding_rows"])
    if not config.apply:
        return {
            "schema": "media-face-organizer-phase3-sava-reset/v1",
            "dry_run": True,
            "backup_root": str(backup_root),
            **plan,
        }

    db = KnownPerformersDB(config.db_dir)
    db.load()
    before_embeddings = int(db.embeddings.shape[0]) if db.embeddings.ndim == 2 else 0
    removed_samples: list[str] = []
    kept_records: list[dict[str, Any]] = []
    performer_found = False
    for item in db.index.setdefault("performers", []):
        if item.get("id") != SAVA_GOLDEN_PERFORMER_ID:
            continue
        performer_found = True
        item["enrolled_face_samples"] = [
            str(path)
            for path in item.get("enrolled_face_samples", []) or []
            if normalized_sample_identity(path) not in remove_identities
        ]
        removed_set = {str(path) for path in item.get("removed_face_samples", []) or []}
        for removal in plan["remove_samples"]:
            sample_path = str(removal.get("sample_path") or "")
            if sample_path:
                removed_samples.append(sample_path)
                removed_set.add(sample_path)
        item["removed_face_samples"] = sorted(removed_set)
        for record in item.get("enrolled_face_sample_records", []) or []:
            if not isinstance(record, dict):
                continue
            if normalized_sample_identity(record.get("sample_path")) in remove_identities:
                continue
            kept_records.append(record)
        item["enrolled_face_sample_records"] = kept_records
        item.setdefault("audit_events", []).append(
            {
                "event": "phase3_sava_stale_samples_reset",
                "at": utc_now(),
                "backup_root": str(backup_root),
                "removed_samples": removed_samples,
                "removed_sample_reasons": plan["remove_samples"],
                "orphan_embedding_rows_removed": sorted(plan["orphan_embedding_rows"]),
                "kept_sample_count": len(kept_records),
            }
        )
        break
    if not performer_found:
        raise RuntimeError("Sava Schultz known performer record not found")

    row_shift: dict[str, str] = {}
    if rows_to_remove and db.embeddings.size:
        keep_indexes = [idx for idx in range(before_embeddings) if idx not in rows_to_remove]
        db.embeddings = db.embeddings[keep_indexes, :] if keep_indexes else np.empty((0, db.embeddings.shape[1]), dtype=np.float32)
        row_shift = {str(old_idx): str(new_idx) for new_idx, old_idx in enumerate(keep_indexes)}
        db.performer_map = {
            row_shift[str(old_row)]: performer_id_value
            for old_row, performer_id_value in db.performer_map.items()
            if str(old_row) in row_shift
        }
        for item in db.index.setdefault("performers", []):
            if item.get("id") != SAVA_GOLDEN_PERFORMER_ID:
                continue
            for record in item.get("enrolled_face_sample_records", []) or []:
                if not isinstance(record, dict):
                    continue
                record["embedding_rows"] = [
                    int(row_shift[str(row)])
                    for row in record.get("embedding_rows") or []
                    if str(row) in row_shift
                ]
        np_save_atomic(db.embeddings_path, db.embeddings.astype(np.float32))
        json_dump(db.map_path, db.performer_map)
    json_dump(db.index_path, db.index)

    after_known = known_db_summary(config.db_dir)
    after_record = (after_known.get("by_id") or {}).get(SAVA_GOLDEN_PERFORMER_ID) or {}
    receipt = {
        "schema": "media-face-organizer-phase3-sava-reset/v1",
        "event": "phase3_sava_stale_samples_reset",
        "reset_at": utc_now(),
        "performer_name": SAVA_GOLDEN_PERFORMER_NAME,
        "performer_id": SAVA_GOLDEN_PERFORMER_ID,
        "backup_root": str(backup_root),
        "removed_samples": removed_samples,
        "removed_sample_reasons": plan["remove_samples"],
        "kept_samples": plan["keep_samples"],
        "orphan_embedding_rows_removed": sorted(plan["orphan_embedding_rows"]),
        "before": {
            "accepted_sample_count": int(plan["before_sample_count"]),
            "sava_embedding_rows": plan["before_sava_embedding_rows"],
            "embedding_rows": before_embeddings,
        },
        "after": {
            "accepted_sample_count": len(known_face_sample_records(config, SAVA_GOLDEN_PERFORMER_ID, after_record)),
            "sava_embedding_rows": known_embedding_rows_for_id(after_known, SAVA_GOLDEN_PERFORMER_ID),
            "embedding_rows": int(after_known.get("embedding_rows") or 0),
        },
        "next_required_step": "Phase 3.3 bounded Sava rescan before adding replacement accepted samples.",
    }
    receipt_path = Path(backup_root) / "phase3_sava_reset_receipt.json"
    json_dump(receipt_path, receipt)
    receipt["receipt_path"] = str(receipt_path)
    return receipt


def phase3_sava_auto_add_candidates(config: OrganizerConfig, *, backup_root: str | Path, confirmed_by: str = "Phase 3.4 auto-add") -> dict[str, Any]:
    sava_only_guard(SAVA_GOLDEN_PERFORMER_NAME, SAVA_GOLDEN_PERFORMER_ID)
    backup_path = Path(backup_root)
    rescan_receipt_path = backup_path / "phase3_sava_bounded_rescan_receipt.json"
    if not backup_path.exists() or not rescan_receipt_path.exists():
        raise RuntimeError("Phase 3.4 requires the Phase 3.1 backup and Phase 3.3 bounded rescan receipt")
    receipt = load_json(rescan_receipt_path, {})
    known_before = known_db_summary(config.db_dir)
    known_record = (known_before.get("by_id") or {}).get(SAVA_GOLDEN_PERFORMER_ID) or {}
    accepted_crops = {path_key(resolve_artifact_path(path, config)) for path in accepted_source_crop_paths(known_record)}
    qualified: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for result in receipt.get("results") or []:
        if not isinstance(result, dict) or result.get("status") != "auto_match":
            continue
        performers = [item for item in result.get("performers") or [] if isinstance(item, dict)]
        match = next(
            (
                item
                for item in performers
                if str(item.get("id") or "") == SAVA_GOLDEN_PERFORMER_ID
                and float(item.get("similarity") or item.get("confidence") or 0) >= HIGH_CONFIDENCE
                and str(item.get("status") or "") == "auto"
                and not item.get("verification_needed")
                and int(item.get("supporting_faces") or 0) > 0
            ),
            None,
        )
        if not match:
            skipped.append({"video_path": result.get("video_path"), "reason": "no thresholded Sava face-rec match"})
            continue
        crop_path = resolve_artifact_path(str(match.get("face_crop_path") or ""), config)
        frame_path = resolve_artifact_path(str(match.get("original_frame_path") or ""), config)
        if not crop_path.exists():
            skipped.append({"video_path": result.get("video_path"), "reason": "face crop missing", "crop_path": str(crop_path)})
            continue
        if path_key(crop_path) in accepted_crops:
            skipped.append({"video_path": result.get("video_path"), "reason": "crop already accepted", "crop_path": str(crop_path)})
            continue
        qualified.append(
            {
                "video_path": str(resolve_artifact_path(str(result.get("video_path") or ""), config)),
                "source_crop": str(crop_path),
                "source_frame": str(frame_path) if frame_path.exists() else "",
                "similarity": round(float(match.get("similarity") or match.get("confidence") or 0), 4),
                "supporting_faces": int(match.get("supporting_faces") or 0),
                "detection_score": round(float(match.get("detection_score") or 0), 4),
                "label": str(match.get("label") or ""),
            }
        )
    if not config.apply:
        return {
            "schema": "media-face-organizer-phase3-sava-auto-add/v1",
            "dry_run": True,
            "qualified": qualified,
            "skipped": skipped,
            "backup_root": str(backup_path),
        }

    db_backup = backup_known_performers_files(config)
    db = KnownPerformersDB(config.db_dir)
    performer_id = db.add_performer(SAVA_GOLDEN_PERFORMER_NAME)
    recognizer = InsightFaceRecognizer(config.model_name, config.ctx_id, config.det_size)
    added: list[dict[str, Any]] = []
    for item in qualified:
        crop_path = Path(item["source_crop"])
        faces = recognizer.detect(crop_path)
        if len(faces) != 1:
            skipped.append({"video_path": item["video_path"], "reason": f"expected one face in crop; detected {len(faces)}", "crop_path": str(crop_path)})
            continue
        face = faces[0]
        if float(getattr(face, "det_score", 0.0)) < config.min_face_score:
            skipped.append({"video_path": item["video_path"], "reason": "crop detection score below threshold", "crop_path": str(crop_path)})
            continue
        row = db.append_embedding(performer_id, np.asarray(face.embedding, dtype=np.float32))
        target_dir = db.faces_dir / performer_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{slugify(crop_path.stem)}-{uuid.uuid4().hex[:8]}{crop_path.suffix.lower() or '.jpg'}"
        shutil.copy2(crop_path, target)
        db.record_enrollment(
            performer_id,
            target,
            confirmed_by=confirmed_by,
            source_crop=str(crop_path),
            source_video=item["video_path"],
            source_timestamp=None,
            embedding_rows=[row],
        )
        added.append({**item, "sample_path": str(target), "embedding_row": row})

    known_after = known_db_summary(config.db_dir)
    after_record = (known_after.get("by_id") or {}).get(SAVA_GOLDEN_PERFORMER_ID) or {}
    out = {
        "schema": "media-face-organizer-phase3-sava-auto-add/v1",
        "event": "phase3_sava_auto_add_thresholded_samples",
        "created_at": utc_now(),
        "performer_name": SAVA_GOLDEN_PERFORMER_NAME,
        "performer_id": SAVA_GOLDEN_PERFORMER_ID,
        "phase3_backup_root": str(backup_path),
        "known_db_backup_root": str(db_backup),
        "phase3_rescan_receipt": str(rescan_receipt_path),
        "thresholds": {"auto_similarity": HIGH_CONFIDENCE, "min_face_score": config.min_face_score},
        "qualified_count": len(qualified),
        "added_count": len(added),
        "skipped": skipped,
        "added_samples": added,
        "before": {
            "accepted_sample_record_count": len(known_record.get("enrolled_face_sample_records") or []),
            "accepted_sample_path_count": len(known_record.get("enrolled_face_samples") or []),
            "sava_embedding_rows": known_embedding_rows_for_id(known_before, SAVA_GOLDEN_PERFORMER_ID),
            "embedding_rows": int(known_before.get("embedding_rows") or 0),
        },
        "after": {
            "accepted_sample_record_count": len(after_record.get("enrolled_face_sample_records") or []),
            "accepted_sample_path_count": len(after_record.get("enrolled_face_samples") or []),
            "sava_embedding_rows": known_embedding_rows_for_id(known_after, SAVA_GOLDEN_PERFORMER_ID),
            "embedding_rows": int(known_after.get("embedding_rows") or 0),
        },
        "generated_ui_surfaces_stale": True,
        "generated_ui_stale_reason": "Phase 3.4 updated known performer DB samples but did not regenerate enrolled JSON/HTML by scope.",
    }
    out_path = backup_path / "phase3_sava_auto_add_receipt.json"
    json_dump(out_path, out)
    out["receipt_path"] = str(out_path)
    return out


def phase3_sava_queue_uncertain_matches(config: OrganizerConfig, *, backup_root: str | Path) -> dict[str, Any]:
    sava_only_guard(SAVA_GOLDEN_PERFORMER_NAME, SAVA_GOLDEN_PERFORMER_ID)
    backup_path = Path(backup_root)
    rescan_receipt_path = backup_path / "phase3_sava_bounded_rescan_receipt.json"
    if not backup_path.exists() or not rescan_receipt_path.exists():
        raise RuntimeError("Phase 3.5 requires the Phase 3.1 backup and Phase 3.3 bounded rescan receipt")
    receipt = load_json(rescan_receipt_path, {})
    queued: list[dict[str, Any]] = []
    hidden_low_confidence: list[dict[str, Any]] = []
    above_queue_band: list[dict[str, Any]] = []
    faceless_no_face: list[dict[str, Any]] = []
    for result in receipt.get("results") or []:
        if not isinstance(result, dict):
            continue
        status = str(result.get("status") or "")
        similarity = float(result.get("best_similarity") or 0)
        item = {
            "video_path": str(resolve_artifact_path(str(result.get("video_path") or ""), config)),
            "sidecar_path": str(resolve_artifact_path(str(result.get("sidecar_path") or ""), config)),
            "similarity": round(similarity, 4),
            "supporting_faces": int(result.get("supporting_faces") or 0),
            "faces_detected": int(result.get("faces_detected") or 0),
        }
        if status == "review_match" and POSSIBLE_CONFIDENCE <= similarity <= 0.75:
            item["queue_bucket"] = "needs_confirmation"
            queued.append(item)
        elif status == "review_match" and similarity > 0.75:
            item["queue_bucket"] = "above_uncertain_band"
            above_queue_band.append(item)
        elif status == "faceless_no_face":
            item["queue_bucket"] = "faceless_or_no_face"
            faceless_no_face.append(item)
        elif similarity < POSSIBLE_CONFIDENCE:
            item["queue_bucket"] = "hidden_low_confidence"
            hidden_low_confidence.append(item)
    out = {
        "schema": "media-face-organizer-phase3-sava-uncertain-queue/v1",
        "event": "phase3_sava_uncertain_review_queue",
        "created_at": utc_now(),
        "performer_name": SAVA_GOLDEN_PERFORMER_NAME,
        "performer_id": SAVA_GOLDEN_PERFORMER_ID,
        "phase3_backup_root": str(backup_path),
        "phase3_rescan_receipt": str(rescan_receipt_path),
        "thresholds": {"review_min": POSSIBLE_CONFIDENCE, "review_max": 0.75, "auto_min": HIGH_CONFIDENCE},
        "queued_needs_confirmation": queued,
        "above_queue_band": above_queue_band,
        "hidden_low_confidence": hidden_low_confidence,
        "faceless_no_face": faceless_no_face,
        "counts": {
            "queued_needs_confirmation": len(queued),
            "above_queue_band": len(above_queue_band),
            "hidden_low_confidence": len(hidden_low_confidence),
            "faceless_no_face": len(faceless_no_face),
        },
        "generated_ui_surfaces_stale": True,
        "generated_ui_stale_reason": "Phase 3.5 wrote a bounded queue receipt only; enrolled JSON/HTML was not regenerated by scope.",
    }
    out_path = backup_path / "phase3_sava_uncertain_queue_receipt.json"
    json_dump(out_path, out)
    out["receipt_path"] = str(out_path)
    return out


def phase3_sava_6513_bucket_closeout(config: OrganizerConfig, *, backup_root: str | Path) -> dict[str, Any]:
    backup_path = Path(backup_root)
    if not backup_path.exists():
        raise RuntimeError("Phase 3.6 requires the Phase 3 backup root")
    generated_group = load_sava_generated_group(config)
    ledger = build_model_video_ledger(config, SAVA_GOLDEN_PERFORMER_NAME, SAVA_GOLDEN_PERFORMER_ID, generated_group=generated_group)
    rows = [row for row in ledger.get("rows") or [] if row.get("basename") == "6513.mp4"]
    if len(rows) != 1:
        raise RuntimeError(f"expected exactly one 6513.mp4 ledger row, found {len(rows)}")
    row = rows[0]
    sidecar = load_json(Path(str(row.get("sidecar_path") or "")), {})
    performers = [item for item in sidecar.get("performers") or [] if isinstance(item, dict)]
    sava_matches = [
        item
        for item in performers
        if str(item.get("id") or "") == SAVA_GOLDEN_PERFORMER_ID
        or normalize_identity_key(str(item.get("name") or "")) == normalize_identity_key(SAVA_GOLDEN_PERFORMER_NAME)
    ]
    best_sava_similarity = max((float(item.get("similarity") or item.get("confidence") or 0) for item in sava_matches), default=0.0)
    receipt = {
        "schema": "media-face-organizer-phase3-sava-6513-bucket-closeout/v1",
        "event": "phase3_sava_6513_bucket_verified",
        "created_at": utc_now(),
        "performer_name": SAVA_GOLDEN_PERFORMER_NAME,
        "performer_id": SAVA_GOLDEN_PERFORMER_ID,
        "backup_root": str(backup_path),
        "ledger_row": row,
        "sidecar_summary": {
            "path": str(row.get("sidecar_path") or ""),
            "generated_at": sidecar.get("generated_at"),
            "frames_analyzed": sidecar.get("frames_analyzed"),
            "faces_detected": sidecar.get("faces_detected"),
            "performers": performers,
        },
        "final_bucket": "unknown",
        "final_state": "unknown",
        "sava_face_rec_confirmed": False,
        "best_sava_similarity": round(best_sava_similarity, 4),
        "reason": "fresh scan detected faces, but no Sava performer match reached review or auto threshold; best saved performer is unknown at 0.4523",
        "thresholds": {"review": POSSIBLE_CONFIDENCE, "auto": HIGH_CONFIDENCE},
    }
    out_path = backup_path / "phase3_sava_6513_bucket_closeout.json"
    json_dump(out_path, receipt)
    receipt["receipt_path"] = str(out_path)
    return receipt


def enroll_selected_crops(config: OrganizerConfig, payload: dict[str, Any]) -> dict[str, Any]:
    performer_name = str(payload.get("performer_name") or "").strip()
    confirmation = str(payload.get("confirmation") or "").strip()
    requested_crop_paths = [str(item) for item in payload.get("crop_paths") or []]
    crop_paths: list[Path] = []
    create_new = bool(payload.get("create_new"))
    add_to_existing = bool(payload.get("add_to_existing"))
    confirmed_by = str(payload.get("confirmed_by") or "Britton").strip()
    if not performer_name:
        raise RuntimeError("performer_name is required")
    if confirmation != performer_name and confirmation != slugify(performer_name):
        raise RuntimeError("confirmation field must match the performer name or slug")
    if not requested_crop_paths:
        raise RuntimeError("at least one crop must be selected")
    if not confirmed_by:
        raise RuntimeError("confirmed_by is required")
    known_before = known_db_summary(config.db_dir)
    existing = None
    key = normalize_identity_key(performer_name)
    for performer in known_before.get("performers", []):
        if not isinstance(performer, dict):
            continue
        keys = {normalize_identity_key(str(performer.get("id") or "")), normalize_identity_key(str(performer.get("name") or ""))}
        keys.update(normalize_identity_key(str(alias)) for alias in performer.get("aliases", []) if alias)
        if key in keys:
            existing = performer
            break
    if existing and create_new:
        raise RuntimeError("name normalization collides with an existing performer; use add_to_existing confirmation")
    if existing and not add_to_existing:
        raise RuntimeError("existing performer found; explicit add_to_existing confirmation is required")
    if not existing and not create_new and not add_to_existing:
        raise RuntimeError("select create_new or add_to_existing before enrollment")
    for crop_path in requested_crop_paths:
        crop_paths.append(resolve_enrollment_crop_path(crop_path, config))
    if not config.apply:
        return {"dry_run": True, "would_enroll": len(crop_paths), "performer_name": performer_name}

    recognizer = InsightFaceRecognizer(config.model_name, config.ctx_id, config.det_size)
    crop_lookup = candidate_crop_lookup(config)
    valid_crops: list[dict[str, Any]] = []
    added_rows: list[int] = []
    rows_by_crop: dict[str, list[int]] = {}
    enrolled_crops: list[str] = []
    skipped_crops: list[dict[str, Any]] = []
    for crop_path in crop_paths:
        source_meta = crop_lookup.get(str(crop_path), {})
        detection_path = Path(str(source_meta.get("still_path") or "")) if source_meta.get("still_path") else crop_path
        faces = recognizer.detect(detection_path)
        if len(faces) != 1:
            if detection_path != crop_path and faces:
                faces = [max(faces, key=lambda item: float(getattr(item, "det_score", 0.0)))]
            else:
                skipped_crops.append(
                    {
                        "crop_path": str(crop_path),
                        "reason": f"expected exactly one usable face; detected {len(faces)}",
                    }
                )
                continue
        face = faces[0]
        if float(getattr(face, "det_score", 0.0)) < config.min_face_score:
            skipped_crops.append(
                {
                    "crop_path": str(crop_path),
                    "reason": f"face detection score below enrollment threshold ({float(getattr(face, 'det_score', 0.0)):.4f} < {config.min_face_score:.4f})",
                }
            )
            continue
        valid_crops.append(
            {
                "crop_path": crop_path,
                "embedding": np.asarray(face.embedding, dtype=np.float32),
                "detection_source": str(detection_path),
                "detection_score": round(float(getattr(face, "det_score", 0.0)), 4),
            }
        )
    if skipped_crops:
        record_rejected_crop(
            config,
            {
                "performer_name": performer_name,
                "crop_paths": [item["crop_path"] for item in skipped_crops],
                "reason": "skipped during enrollment because crop did not meet enrollment quality requirements",
            },
        )
    if not valid_crops:
        return {
            "schema": "media-face-enrollment-audit/v1",
            "event": "no_selected_crops_met_enrollment_quality",
            "performer_name": performer_name,
            "source_crops": [],
            "skipped_crops": skipped_crops,
            "embedding_row_indexes_added": [],
            "no_enrollment_performed": True,
            "status": "SKIPPED_WEAK_CROPS",
            "message": "No selected recommendations met enrollment quality requirements; weak crops were hidden from future recommendations.",
        }

    backup_root = backup_known_performers_files(config)
    db = KnownPerformersDB(config.db_dir)
    performer_id = db.add_performer(performer_name)
    for item in valid_crops:
        crop_path = Path(item["crop_path"])
        row = db.append_embedding(performer_id, item["embedding"])
        added_rows.append(row)
        rows_by_crop[str(crop_path)] = [row]
        enrolled_crops.append(str(crop_path))
    target_dir = db.faces_dir / performer_id
    target_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for crop_path in [Path(item) for item in enrolled_crops]:
        target = target_dir / f"{slugify(crop_path.stem)}-{uuid.uuid4().hex[:8]}{crop_path.suffix.lower() or '.jpg'}"
        shutil.copy2(crop_path, target)
        copied.append(str(target))
        source_meta = crop_lookup.get(str(crop_path), {})
        db.record_enrollment(
            performer_id,
            target,
            confirmed_by=confirmed_by,
            source_crop=str(crop_path),
            source_video=str(source_meta.get("source_video") or ""),
            source_timestamp=source_meta.get("timestamp"),
            embedding_rows=rows_by_crop.get(str(crop_path), []),
        )
    if payload.get("defer_unidentified_rescan"):
        unidentified_rescan = {
            "deferred": True,
            "scanned": 0,
            "matched_new_performer": 0,
            "message": "Deferred so the interactive enrollment action can return immediately.",
        }
    else:
        unidentified_rescan = rescan_unidentified_videos_after_enrollment(
            config,
            performer_name=performer_name,
            recognizer=recognizer,
            limit=ENROLLMENT_UNIDENTIFIED_RESCAN_LIMIT,
        )
    audit = {
        "schema": "media-face-enrollment-audit/v1",
        "event": "confirmed_embedding_enrollment",
        "performer_id": performer_id,
        "performer_name": performer_name,
        "aliases": payload.get("aliases") or [],
        "source_crops": enrolled_crops,
        "skipped_crops": skipped_crops,
        "source_videos": payload.get("source_videos") or [],
        "source_timestamps": payload.get("source_timestamps") or [],
        "enrolled_by": confirmed_by,
        "confirmed_by": confirmed_by,
        "enrolled_at": utc_now(),
        "embedding_row_indexes_added": added_rows,
        "backup_root": str(backup_root),
        "previous_db_counts": {
            "performers": len(known_before.get("performers", [])),
            "embedding_rows": int(known_before.get("embedding_rows") or 0),
        },
        "new_db_counts": {
            "performers": len(known_db_summary(config.db_dir).get("performers", [])),
            "embedding_rows": int(known_db_summary(config.db_dir).get("embedding_rows") or 0),
        },
        "internet_face_recognition": False,
        "unidentified_rescan": unidentified_rescan,
    }
    removed_recommendations = remove_candidate_crops_from_queue(config, performer_name, enrolled_crops)
    audit["removed_recommendations"] = removed_recommendations
    audit_path = enrollment_review_dir(config) / "enrollment_audit.jsonl"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(audit, ensure_ascii=False) + "\n")
    return audit


def record_needs_identity_rescan(record: dict[str, Any]) -> bool:
    performers = [item for item in record.get("performers") or [] if isinstance(item, dict)]
    if not performers:
        return True
    if record.get("verification_needed"):
        return True
    return not any(item.get("status") == "auto" and not item.get("verification_needed") for item in performers)


def rescan_unidentified_videos_after_enrollment(
    config: OrganizerConfig,
    *,
    performer_name: str,
    recognizer: InsightFaceRecognizer,
    limit: int = ENROLLMENT_UNIDENTIFIED_RESCAN_LIMIT,
) -> dict[str, Any]:
    if not config.apply:
        return {"dry_run": True, "scanned": 0, "matched_new_performer": 0}
    db = KnownPerformersDB(config.db_dir)
    db.load()
    target_key = normalize_identity_key(performer_name)
    candidates: list[tuple[Path, Path]] = []
    for record in collect_metadata(config.source_dir, config.recursive):
        if not record_needs_identity_rescan(record):
            continue
        video_path = Path(str(record.get("video_path") or ""))
        meta_path = Path(str(record.get("_meta_path") or meta_path_for(video_path)))
        if video_path.exists() and video_path.suffix.lower() in VIDEO_EXTENSIONS:
            candidates.append((video_path, meta_path))
        if len(candidates) >= limit:
            break
    scanned = 0
    matched = []
    errors = []
    for video_path, meta_path in candidates:
        try:
            meta = scan_video(video_path, config, db, recognizer)
            meta = write_scan_sidecar(meta_path, meta)
            scanned += 1
            performers = [item for item in meta.get("performers") or [] if isinstance(item, dict)]
            if any(normalize_identity_key(str(item.get("name") or "")) == target_key and item.get("status") in {"auto", "possible"} for item in performers):
                matched.append(str(video_path))
        except Exception as exc:
            errors.append({"video_path": str(video_path), "error": str(exc)})
    return {
        "schema": "media-face-enrollment-unidentified-rescan/v1",
        "performer_name": performer_name,
        "scanned": scanned,
        "matched_new_performer": len(matched),
        "matched_videos": matched[:25],
        "candidate_limit": limit,
        "errors": errors[:10],
    }


def performer_match_keys(name: str, performer_id: str = "") -> set[str]:
    keys = {normalize_identity_key(name), normalize_identity_key(slugify(name))}
    if performer_id:
        keys.add(normalize_identity_key(performer_id))
    return {key for key in keys if key}


def record_performer_matches(record: dict[str, Any], *, performer_name: str, performer_id: str = "") -> list[dict[str, Any]]:
    target_keys = performer_match_keys(performer_name, performer_id)
    matches: list[dict[str, Any]] = []
    for performer in record.get("performers") or []:
        if not isinstance(performer, dict):
            continue
        keys = performer_match_keys(str(performer.get("name") or ""), str(performer.get("id") or ""))
        if target_keys & keys:
            matches.append(performer)
    return matches


def video_match_decision_for(record: dict[str, Any], *, performer_name: str, performer_id: str = "") -> str:
    decision = video_match_decision_record_for(record, performer_name=performer_name, performer_id=performer_id)
    return str((decision or {}).get("decision") or "")


def video_match_decision_record_for(record: dict[str, Any], *, performer_name: str, performer_id: str = "") -> dict[str, Any] | None:
    target_keys = performer_match_keys(performer_name, performer_id)
    for decision in reversed(record.get("face_match_decisions") or []):
        if not isinstance(decision, dict):
            continue
        keys = performer_match_keys(str(decision.get("performer_name") or ""), str(decision.get("performer_id") or ""))
        if target_keys & keys:
            return decision
    return None


def video_is_in_model_library(record: dict[str, Any], *, performer_name: str, performer_id: str = "") -> bool:
    candidate_paths = [
        Path(str(record.get("video_path") or record.get("path") or "")),
        Path(str(record.get("_meta_path") or "")),
    ]
    slug_keys = performer_match_keys(performer_name, performer_id)
    for candidate_path in candidate_paths:
        parts = [normalize_identity_key(part) for part in candidate_path.parts]
        if "models" not in parts:
            continue
        try:
            model_index = parts.index("models")
        except ValueError:
            continue
        if any(part in slug_keys for part in parts[model_index + 1 : model_index + 3]):
            return True
    return False


def path_key(value: str | Path) -> str:
    return str(value).replace("\\", "/").lower()


def path_basename(value: str | Path) -> str:
    text = str(value or "").replace("\\", "/").rstrip("/")
    return text.rsplit("/", 1)[-1] if text else ""


def media_root_candidates(config: OrganizerConfig) -> list[Path]:
    roots: list[Path] = []
    seen: set[str] = set()
    for root in (config.source_dir, Path("/DATA/yes"), Path("/mnt/spirit-8tb/media/yes"), Path("M:/yes")):
        key = path_key(root)
        if key in seen:
            continue
        roots.append(root)
        seen.add(key)
    return roots


def media_path_from_known_root(value: str | Path, config: OrganizerConfig) -> Path | None:
    text = str(value or "")
    if not text:
        return None
    normalized = text.replace("\\", "/")
    for prefix in ("M:/yes/", "/mnt/spirit-8tb/media/yes/", "/DATA/yes/"):
        if normalized.startswith(prefix):
            relative = normalized.removeprefix(prefix)
            candidates = [root / relative for root in media_root_candidates(config)]
            for candidate in candidates:
                if candidate.exists():
                    return candidate
            return candidates[0] if candidates else Path(text)
    return None


def ledger_resolved_path(value: str | Path, config: OrganizerConfig) -> Path:
    text = str(value or "")
    if not text:
        return Path("")
    rooted = media_path_from_known_root(text, config)
    if rooted is not None:
        return rooted
    return Path(text)


def resolve_sidecar_path(value: str | Path, config: OrganizerConfig) -> Path:
    text = str(value or "")
    if not text:
        return Path("")
    rooted = media_path_from_known_root(text, config)
    if rooted is not None:
        return rooted
    return Path(text)


def resolve_media_path(value: str | Path, config: OrganizerConfig) -> Path:
    text = str(value or "")
    if not text:
        return Path("")
    direct = Path(text)
    if direct.exists():
        return direct
    rooted = media_path_from_known_root(text, config)
    if rooted is not None:
        return rooted
    return Path(text)


def ledger_path_key(value: str | Path, config: OrganizerConfig) -> str:
    return path_key(ledger_resolved_path(value, config))


def record_has_performer_context(record: dict[str, Any], *, performer_name: str, performer_id: str = "") -> bool:
    target_keys = performer_match_keys(performer_name, performer_id)
    if record_performer_matches(record, performer_name=performer_name, performer_id=performer_id):
        return True
    decision = normalize_assignment_decision(record.get("assignment_decision"))
    if normalize_identity_key(str(decision.get("suggested_name") or "")) in target_keys:
        return True
    pending = record.get("manual_correction_pending")
    if isinstance(pending, dict) and normalize_identity_key(str(pending.get("new_canonical_name") or "")) in target_keys:
        return True
    for candidate in ((record.get("metadata_hints") or {}).get("candidate_names") or []):
        if not isinstance(candidate, dict) or candidate.get("not_performer_name"):
            continue
        candidate_keys = performer_match_keys(str(candidate.get("name") or ""))
        candidate_keys.update(normalize_identity_key(str(item)) for item in candidate.get("variants") or [] if item)
        if target_keys & {key for key in candidate_keys if key}:
            return True
    return video_is_in_model_library(record, performer_name=performer_name, performer_id=performer_id)


def record_best_similarity(record: dict[str, Any], match: dict[str, Any] | None) -> float | None:
    if match:
        return round(float(match.get("similarity") or match.get("confidence") or 0), 4)
    performers = [item for item in record.get("performers") or [] if isinstance(item, dict)]
    if not performers:
        return None
    return round(max(float(item.get("similarity") or item.get("confidence") or 0) for item in performers), 4)


def record_metadata_matches_performer(record: dict[str, Any], *, performer_name: str, performer_id: str = "") -> bool:
    target_keys = performer_match_keys(performer_name, performer_id)
    for candidate in ((record.get("metadata_hints") or {}).get("candidate_names") or []):
        if not isinstance(candidate, dict) or candidate.get("not_performer_name"):
            continue
        keys = performer_match_keys(str(candidate.get("name") or ""))
        keys.update(normalize_identity_key(str(item)) for item in candidate.get("variants") or [] if item)
        if target_keys & {key for key in keys if key}:
            return True
    return False


def video_filename_matches_performer(video_path: Path, *, performer_name: str, performer_id: str = "") -> bool:
    target_keys = performer_match_keys(performer_name, performer_id)
    path_key_text = normalize_identity_key(video_path.stem)
    parent_key_text = normalize_identity_key(video_path.parent.name)
    if target_keys & {path_key_text, parent_key_text}:
        return True
    for candidate in extract_filename_candidates(video_path):
        keys = performer_match_keys(str(candidate.get("name") or ""))
        keys.update(normalize_identity_key(str(item)) for item in candidate.get("variants") or [] if item)
        if target_keys & {key for key in keys if key}:
            return True
    compact_targets = {key.replace(" ", "") for key in target_keys if key}
    compact_text = f"{path_key_text} {parent_key_text}".replace(" ", "")
    return any(key and key in compact_text for key in compact_targets)


def record_ocr_matches_performer(record: dict[str, Any], *, performer_name: str, performer_id: str = "") -> bool:
    target_keys = performer_match_keys(performer_name, performer_id)
    for candidate in ((record.get("metadata_hints") or {}).get("candidate_names") or []):
        if not isinstance(candidate, dict) or candidate.get("not_performer_name"):
            continue
        source = str(candidate.get("source") or "")
        role = str(candidate.get("evidence_role") or "")
        if "ocr" not in source and "ocr" not in role:
            continue
        keys = performer_match_keys(str(candidate.get("name") or ""))
        keys.update(normalize_identity_key(str(item)) for item in candidate.get("variants") or [] if item)
        if target_keys & {key for key in keys if key}:
            return True
    return False


def ledger_sidecar_freshness(record: dict[str, Any] | None, video_path: Path) -> str:
    if not record:
        return "none"
    if not record.get("_video_exists", True):
        return "missing_source"
    resolved = Path(str(record.get("_resolved_video_path") or record.get("video_path") or ""))
    if resolved and path_key(resolved) != path_key(video_path):
        return "path_mismatch"
    return "fresh"


def ledger_match_evidence_type(
    record: dict[str, Any] | None,
    match: dict[str, Any] | None,
    *,
    performer_name: str,
    performer_id: str,
    in_model_library: bool,
) -> str:
    if not record:
        return "unknown"
    if bool(record.get("faceless_video")):
        return "faceless_video"
    decision_record = video_match_decision_record_for(record, performer_name=performer_name, performer_id=performer_id)
    if match:
        similarity = float(match.get("similarity") or match.get("confidence") or 0)
        supporting_faces = int(match.get("supporting_faces") or 0)
        has_face_evidence = bool(supporting_faces > 0 or match.get("face_crop_path") or match.get("original_frame_path"))
        if has_face_evidence and similarity >= HIGH_CONFIDENCE and not match.get("verification_needed"):
            return "face_rec"
    if decision_record and decision_record.get("decision") == "accepted" and decision_record.get("visual_confirmed"):
        return "manual_confirmed"
    if record_ocr_matches_performer(record, performer_name=performer_name, performer_id=performer_id):
        return "ocr_only"
    if record_metadata_matches_performer(record, performer_name=performer_name, performer_id=performer_id):
        return "metadata_only"
    if in_model_library or normalize_assignment_decision(record.get("assignment_decision")).get("suggested_name"):
        return "metadata_only"
    return "unknown"


def ledger_match_state(record: dict[str, Any] | None, match: dict[str, Any] | None, evidence_type: str) -> str:
    if evidence_type in {"face_rec", "manual_confirmed"}:
        return "confirmed"
    if evidence_type in {"faceless_video", "faceless_creator"}:
        return "faceless"
    if match:
        similarity = float(match.get("similarity") or match.get("confidence") or 0)
        if similarity >= POSSIBLE_CONFIDENCE:
            return "needs_review"
    if evidence_type in {"metadata_only", "ocr_only"}:
        return "needs_review"
    if record:
        return "unknown"
    return "unscanned"


def build_model_video_ledger(
    config: OrganizerConfig,
    performer_name: str,
    performer_id: str = "",
    *,
    generated_group: dict[str, Any] | None = None,
    visible_item_paths: Iterable[str] | None = None,
) -> dict[str, Any]:
    performer_id = performer_id or slugify(performer_name)
    visible_keys = {ledger_path_key(item, config) for item in visible_item_paths or [] if item}
    all_records = collect_metadata(config.source_dir, config.recursive)
    records = [
        record
        for record in all_records
        if record_has_performer_context(record, performer_name=performer_name, performer_id=performer_id)
    ]
    records_by_video: dict[str, dict[str, Any]] = {}
    for record in all_records:
        video_text = str(record.get("_resolved_video_path") or record.get("video_path") or record.get("path") or "")
        if video_text:
            records_by_video[ledger_path_key(video_text, config)] = record

    row_paths: dict[str, Path] = {}

    def add_path(value: str | Path) -> None:
        path = ledger_resolved_path(value, config)
        if path.suffix.lower() in VIDEO_EXTENSIONS:
            row_paths.setdefault(path_key(path), path)

    for record in records:
        add_path(record.get("_resolved_video_path") or record.get("video_path") or record.get("path") or "")

    slug_keys = performer_match_keys(performer_name, performer_id)
    models_dir = config.source_dir / "models"
    if models_dir.exists():
        for model_dir in sorted(models_dir.iterdir(), key=lambda item: item.name.lower()):
            if model_dir.is_dir() and normalize_identity_key(model_dir.name) in slug_keys:
                for video_path in find_videos(model_dir, True):
                    add_path(video_path)

    if generated_group:
        generated_paths: list[str] = []
        for field in ("records", "library_video_matches", "missing_video_matches", "auto_video_matches", "pending_video_matches"):
            for item in generated_group.get(field) or []:
                if isinstance(item, dict):
                    generated_paths.append(str(item.get("resolved_video_path") or item.get("video_path") or ""))
        for field in ("recommended_crops", "recommended_stills"):
            for item in generated_group.get(field) or []:
                if isinstance(item, dict):
                    generated_paths.append(str(item.get("source_video") or ""))
        for value in generated_paths:
            add_path(value)

    if performer_id == SAVA_GOLDEN_PERFORMER_ID:
        add_path(config.source_dir / "6513.mp4")

    generated_library_keys = {
        ledger_path_key(item.get("resolved_video_path") or item.get("video_path") or "", config)
        for item in (generated_group or {}).get("library_video_matches") or []
        if isinstance(item, dict)
    }
    generated_candidate_keys = {
        ledger_path_key(item.get("resolved_video_path") or item.get("video_path") or "", config)
        for item in (generated_group or {}).get("records") or []
        if isinstance(item, dict)
    }
    generated_candidate_keys.update(generated_library_keys)
    generated_candidate_keys.update(
        ledger_path_key(item.get("resolved_video_path") or item.get("video_path") or "", config)
        for item in (generated_group or {}).get("pending_video_matches") or []
        if isinstance(item, dict)
    )
    generated_candidate_keys = {key for key in generated_candidate_keys if key}

    rows: list[dict[str, Any]] = []
    physical_model_keys: set[str] = set()
    sidecar_keys: set[str] = set()
    for key, video_path in sorted(row_paths.items(), key=lambda item: Path(item[1]).name.lower()):
        record = records_by_video.get(key)
        meta_path = Path(str(record.get("_meta_path"))) if record and record.get("_meta_path") else meta_path_for(video_path)
        if record:
            sidecar_keys.add(str(meta_path))
        in_model_library = video_is_in_model_library(
            record or {"video_path": str(video_path)},
            performer_name=performer_name,
            performer_id=performer_id,
        )
        if in_model_library and video_path.exists():
            physical_model_keys.add(key)
        matches = record_performer_matches(record or {}, performer_name=performer_name, performer_id=performer_id)
        best = max(matches, key=lambda item: float(item.get("similarity") or item.get("confidence") or 0), default=None)
        evidence_type = ledger_match_evidence_type(
            record,
            best,
            performer_name=performer_name,
            performer_id=performer_id,
            in_model_library=in_model_library,
        )
        sidecar_freshness = ledger_sidecar_freshness(record, video_path)
        source_exists = video_path.exists()
        spiritflix_visible = path_key(video_path) in visible_keys if visible_keys else None
        mismatch_reasons: list[str] = []
        if not source_exists:
            mismatch_reasons.append("missing_source_file")
        if sidecar_freshness == "none":
            mismatch_reasons.append("sidecar_missing")
        elif sidecar_freshness != "fresh":
            mismatch_reasons.append(sidecar_freshness)
        if visible_keys and not spiritflix_visible:
            mismatch_reasons.append("not_jellyfin_visible")
        if in_model_library and generated_group and key not in generated_library_keys:
            mismatch_reasons.append("organizer_library_bucket_missing")
        if evidence_type == "metadata_only":
            mismatch_reasons.append("metadata_only")
        if evidence_type == "ocr_only":
            mismatch_reasons.append("ocr_only")
        if evidence_type == "unknown":
            mismatch_reasons.append("unscanned_or_unknown")
        if in_model_library and evidence_type != "face_rec":
            mismatch_reasons.append("model_folder_not_face_rec_supported")

        rows.append(
            {
                "canonical_video_id": f"path:{path_key(video_path)}",
                "basename": video_path.name,
                "resolved_path": str(video_path) if source_exists else "",
                "source_root_path": str(config.source_dir),
                "model_folder_path": str(video_path) if in_model_library else "",
                "jellyfin_item_id": "",
                "spiritflix_visible": spiritflix_visible,
                "organizer_visible": key in generated_candidate_keys if generated_group else bool(record),
                "sidecar_path": str(meta_path) if meta_path.exists() or record else "",
                "sidecar_freshness": sidecar_freshness,
                "media_ingest_receipt_path": str(video_path.with_name(f"{video_path.name}.media-ingest.json"))
                if video_path.with_name(f"{video_path.name}.media-ingest.json").exists()
                else "",
                "model_label": performer_name,
                "performer_id": performer_id,
                "match_state": ledger_match_state(record, best, evidence_type),
                "match_evidence_type": evidence_type,
                "face_evidence_count": int((best or {}).get("supporting_faces") or 0),
                "supporting_faces": (best or {}).get("supporting_face_records") or [],
                "best_similarity": record_best_similarity(record or {}, best),
                "visual_confirmed": bool((video_match_decision_record_for(record or {}, performer_name=performer_name, performer_id=performer_id) or {}).get("visual_confirmed")),
                "denied": video_match_decision_for(record or {}, performer_name=performer_name, performer_id=performer_id) == "rejected",
                "accepted_sample_count": 0,
                "faceless_video": bool((record or {}).get("faceless_video")),
                "faceless_creator": False,
                "needs_user_decision": ledger_match_state(record, best, evidence_type) == "needs_review",
                "sync_mismatch_reasons": sorted(set(mismatch_reasons)),
                "last_scan_at": str((record or {}).get("generated_at") or ""),
                "last_crud_action_at": str(((video_match_decision_record_for(record or {}, performer_name=performer_name, performer_id=performer_id) or {}).get("decided_at") or "")),
            }
        )

    counts = {
        "source_files_count": sum(1 for row in rows if row.get("resolved_path")),
        "model_folder_files_count": len(physical_model_keys),
        "sidecar_records_count": len(sidecar_keys),
        "jellyfin_visible_item_count": len(visible_keys) if visible_keys else None,
        "spiritflix_visible_model_count": len(visible_keys) if visible_keys else None,
        "enrolled_accepted_screen_count": len((generated_group or {}).get("enrolled_samples") or (generated_group or {}).get("embedding_rows") or []),
        "face_rec_supported_video_count": sum(1 for row in rows if row.get("match_evidence_type") == "face_rec"),
        "metadata_manual_only_video_count": sum(
            1 for row in rows if row.get("match_evidence_type") in {"metadata_only", "ocr_only", "manual_confirmed"}
        ),
        "faceless_video_count": sum(1 for row in rows if row.get("faceless_video")),
    }
    return {
        "schema": "media-model-video-ledger/v1",
        "generated_at": utc_now(),
        "read_only": True,
        "model_label": performer_name,
        "performer_id": performer_id,
        "count_types": counts,
        "rows": rows,
        "consumer_map": {
            "organizer_enrolled_page": "source_of_truth_ledger.rows and count_types",
            "organizer_enrollment_queue": "source_of_truth_ledger rows where needs_user_decision is true",
            "spiritflix_face_metadata_api": "ledger-derived visible-item projection",
            "spiritflix_model_grouping": "visible Jellyfin items plus ledger count labels",
            "crud_action_handlers": "ledger row by canonical_video_id before mutation",
            "media_ingest_closeout": "media_ingest_receipt_path and resolved_path fields",
        },
    }


SAVA_GOLDEN_PERFORMER_ID = "sava-schultz"
SAVA_GOLDEN_PERFORMER_NAME = "Sava Schultz"


def sava_only_guard(performer_name: str, performer_id: str = "") -> dict[str, Any]:
    keys = performer_match_keys(performer_name, performer_id or slugify(performer_name))
    allowed = performer_match_keys(SAVA_GOLDEN_PERFORMER_NAME, SAVA_GOLDEN_PERFORMER_ID)
    return {
        "allowed": bool(keys & allowed),
        "scope": "sava-only",
        "allowed_performer_name": SAVA_GOLDEN_PERFORMER_NAME,
        "allowed_performer_id": SAVA_GOLDEN_PERFORMER_ID,
        "reject_reason": "" if keys & allowed else "Phase 2 is approved only for the Sava Schultz golden case.",
    }


def phase2_sava_crud_sync_contract() -> dict[str, Any]:
    action_layers = {
        "accept_recommended_screen": {
            "handler": "enroll_selected_crops",
            "ledger_row_lookup": "source_video/crop_path -> source_of_truth_ledger.rows[].canonical_video_id",
            "updates_layers": ["known_performers", "enrolled_json_after_regeneration", "queue_json_after_regeneration", "known_db_audit"],
            "does_not_update_layers": ["media_file", "model_folder_path", "3001_code"],
            "required_backup": "backup_known_performers_files before embedding/index/map mutation",
            "required_receipt": "media-face-enrollment-audit/v1 with source_crop, source_video, timestamp, embedding rows, confirmed_by",
            "post_checks": ["ledger enrolled_accepted_screen_count changes only after regeneration", "face_rec_supported_video_count does not increase without thresholded face evidence"],
        },
        "reject_recommended_screen": {
            "handler": "record_rejected_crop",
            "ledger_row_lookup": "crop_path/source_video -> canonical_video_id",
            "updates_layers": ["review_export_rejection_receipt"],
            "does_not_update_layers": ["known_performers", "embeddings", "media_file", "3001_code"],
            "required_backup": "none unless future implementation removes accepted DB rows",
            "required_receipt": "rejection receipt with crop_path, performer_name, reason, timestamp",
            "post_checks": ["rejected crop hidden from primary recommendations after regeneration"],
        },
        "remove_accepted_screen": {
            "handler": "remove_enrolled_samples",
            "ledger_row_lookup": "sample record source_video -> canonical_video_id",
            "updates_layers": ["known_performers", "enrolled_json_after_regeneration", "known_db_audit"],
            "does_not_update_layers": ["sidecar_face_evidence", "media_file", "3001_code"],
            "required_backup": "backup_known_performers_files before index/map/embedding removal",
            "required_receipt": "media-face-enrollment-remove-samples result with backup_root and removed sample paths",
            "post_checks": ["embedding row count decreases only for selected Sava samples", "no source face evidence is deleted"],
        },
        "confirm_video_match": {
            "handler": "set_enrolled_video_match_decision",
            "ledger_row_lookup": "meta_path -> source_of_truth_ledger.rows[].sidecar_path",
            "updates_layers": ["sidecar.face_match_decisions", "enrolled_json_after_regeneration", "queue_json_after_regeneration"],
            "does_not_update_layers": ["known_performers", "embeddings", "media_file", "3001_code"],
            "required_backup": "selected sidecar backup before sidecar mutation",
            "required_receipt": "media-face-enrolled-video-match-decision/v1 appended to sidecar",
            "post_checks": ["manual confirmation does not become face_rec unless saved thresholded support exists"],
        },
        "deny_video_match": {
            "handler": "set_enrolled_video_match_decision",
            "ledger_row_lookup": "meta_path -> source_of_truth_ledger.rows[].sidecar_path",
            "updates_layers": ["sidecar.face_match_decisions", "enrolled_json_after_regeneration", "queue_json_after_regeneration"],
            "does_not_update_layers": ["known_performers", "embeddings", "media_file", "3001_code"],
            "required_backup": "selected sidecar backup before sidecar mutation",
            "required_receipt": "media-face-enrolled-video-match-decision/v1 appended to sidecar with decision=rejected",
            "post_checks": ["denied Sava relationship is excluded from match suggestions"],
        },
        "mark_video_faceless": {
            "handler": "planned_phase2_video_faceless_handler",
            "ledger_row_lookup": "canonical_video_id or sidecar_path",
            "updates_layers": ["sidecar.faceless_video", "faceless receipt", "enrolled_json_after_regeneration", "queue_json_after_regeneration"],
            "does_not_update_layers": ["known_performers", "embeddings", "media_file", "3001_code"],
            "required_backup": "selected sidecar backup before faceless flag mutation",
            "required_receipt": "media-face-faceless-video/v1 with old_state, new_state, actor, reason, source page",
            "post_checks": ["faceless video leaves face-rec recommendation panels", "video can remain model-associated as faceless/manual or faceless/metadata"],
        },
        "mark_creator_faceless": {
            "handler": "mark_performer_faceless",
            "ledger_row_lookup": "performer_id -> all source_of_truth_ledger.rows for Sava",
            "updates_layers": ["registry", "model_index", "known_db_audit", "enrolled_json_after_regeneration", "queue_json_after_regeneration"],
            "does_not_update_layers": ["known_performers embeddings", "media_file", "3001_code"],
            "required_backup": "backup_registry_model_files before registry/model_index mutation",
            "required_receipt": "media-face-enrollment-faceless/v1 with old_state, new_state, actor, reason",
            "post_checks": ["faceless_creator true is represented separately from faceless_video", "face-rec readiness pressure is removed without deleting model association"],
        },
        "rescan_sava_model": {
            "handler": "scan_library_for_enrolled_model",
            "ledger_row_lookup": "performer_id -> bounded Sava ledger rows only",
            "updates_layers": ["sidecars", "review frames/crops", "enrolled_json_after_regeneration", "queue_json_after_regeneration"],
            "does_not_update_layers": ["known_performers", "embeddings", "media_file", "3001_code"],
            "required_backup": "selected Sava sidecar backup before scan output replacement",
            "required_receipt": "scan receipt with command, scope, model_label, sidecar paths, threshold settings",
            "post_checks": ["scope contains only Sava rows", "6513 remains ocr_only unless similarity >= 0.80 with saved support"],
        },
        "sync_3001": {
            "handler": "planned_manual_sync_3001_lane",
            "ledger_row_lookup": "visible Jellyfin item path/id -> ledger canonical_video_id",
            "updates_layers": ["3001 working copy", "3001 build output", "port 3001 process"],
            "does_not_update_layers": ["media_file", "sidecar", "known_performers", "embeddings"],
            "required_backup": "record source commit/status and 3001 working-copy diff before copy/build/restart",
            "required_receipt": "3001 sync receipt with copied files, build command, restart command, live verification URL",
            "post_checks": ["source repo and /tmp/spiritos-spiritflix-stable-3001 contents verified separately", "live 3001 labels visible count vs ledger count separately"],
        },
    }
    return {
        "schema": "media-face-organizer-phase2-sava-crud-sync-contract/v1",
        "scope": "sava-only",
        "performer_name": SAVA_GOLDEN_PERFORMER_NAME,
        "performer_id": SAVA_GOLDEN_PERFORMER_ID,
        "non_goals": [
            "do_not_generalize_to_all_models",
            "do_not_reset_sava_accepted_screens",
            "do_not_mutate_media_sidecars_known_db_embeddings_generated_artifacts_or_3001_from_contract_planning",
        ],
        "action_layers": action_layers,
        "ledger_to_handler_mapping": {
            "canonical_video_id": "stable row key every CRUD action must resolve before mutation",
            "sidecar_path": "set_enrolled_video_match_decision, mark_video_faceless, deny/confirm video match",
            "media_ingest_receipt_path": "upload/update and sync closeout provenance",
            "match_evidence_type": "prevents ocr_only/manual/metadata from being treated as face_rec",
            "faceless_video": "video-level non-face-rec maintenance state",
            "faceless_creator": "creator-level state independent of video-level flags",
            "sync_mismatch_reasons": "UI and closeout explanation for Organizer vs SpiritFlix/Jellyfin differences",
        },
        "refresh_3001_contract": [
            "do not touch /tmp/spiritos-spiritflix-stable-3001 until source changes and approval are explicit",
            "copy only approved source files into /tmp/spiritos-spiritflix-stable-3001",
            "run build inside the 3001 working copy",
            "restart only the 3001 lane",
            "verify http://10.0.0.186:3001/spiritflix separately from source repo state",
            "post-sync UI must label visible Jellyfin count separately from ledger/model/face-rec counts",
        ],
        "6513_honesty_rule": {
            "basename": "6513.mp4",
            "current_bucket": "ocr_only",
            "current_state": "needs_review",
            "current_best_similarity": 0.4608,
            "rule": "do not upgrade to face_rec unless saved face evidence exists, similarity >= 0.80, quality passes, and verification_needed is false or explicitly resolved",
        },
        "faceless_state_contract": {
            "video": {
                "field": "faceless_video",
                "storage": "sidecar or ledger state",
                "effect": "exclude frames from face-rec recommendation panels while preserving manual/metadata association",
                "receipt_schema": "media-face-faceless-video/v1",
            },
            "creator": {
                "field": "faceless_creator",
                "storage": "registry/model index derived ledger state",
                "effect": "remove creator from face-enrollment pressure without deleting organized videos",
                "receipt_schema": "media-face-enrollment-faceless/v1",
            },
        },
        "phase3_preflight_checks": [
            "Sava ledger builds and contains 6513.mp4 row",
            "6513.mp4 row is ocr_only/needs_review with best_similarity 0.4608 unless new approved scan evidence exists",
            "all Sava action contracts name backup and receipt behavior",
            "known_performers backup path is planned before accepted-screen reset",
            "sidecar backup path is planned before any video decision/faceless/rescan action",
            "3001 sync receipt fields are planned before any 3001 copy/build/restart",
            "unit tests pass on Windows/Codex and Dell host",
        ],
    }


def video_match_record(record: dict[str, Any], match: dict[str, Any], *, kind: str) -> dict[str, Any]:
    video_path = str(record.get("video_path") or record.get("path") or "")
    meta_path = str(record.get("_meta_path") or meta_path_for(Path(video_path or "unknown")))
    resolved_video_path = str(record.get("_resolved_video_path") or video_path)
    supporting_faces = int(match.get("supporting_faces") or 0)
    face_crop_path = str(match.get("face_crop_path") or "")
    frame_path = str(match.get("original_frame_path") or "")
    preview_paths = [
        str(path)
        for path in [face_crop_path, frame_path] + [str(item) for item in record.get("review_frames") or []]
        if str(path)
    ]
    similarity = float(match.get("similarity") or 0)
    confidence = similarity if supporting_faces > 0 or face_crop_path or frame_path else 0.0
    return {
        "video_path": video_path,
        "resolved_video_path": resolved_video_path,
        "meta_path": meta_path,
        "video_name": Path(video_path or meta_path).name,
        "performer_name": str(match.get("name") or ""),
        "performer_id": str(match.get("id") or ""),
        "confidence": round(confidence, 4),
        "confidence_percent": round(confidence * 100),
        "status": str(match.get("status") or ""),
        "verification_needed": bool(match.get("verification_needed")),
        "face_crop_path": face_crop_path,
        "frame_path": frame_path,
        "preview_paths": preview_paths[:6],
        "supporting_faces": supporting_faces,
        "has_face_evidence": bool(supporting_faces > 0 or face_crop_path or frame_path),
        "source_video_exists": bool(record.get("_video_exists", True)),
        "in_model_library": video_is_in_model_library(record, performer_name=str(match.get("name") or ""), performer_id=str(match.get("id") or "")),
        "kind": kind,
    }


def latest_sava_uncertain_queue_receipt(config: OrganizerConfig) -> dict[str, Any]:
    candidates = sorted(
        config.backup_dir.glob("*/phase3-sava-before-reset/phase3_sava_uncertain_queue_receipt.json"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    return load_json(candidates[0], {}) if candidates else {}


def queue_video_match_record(item: dict[str, Any], *, kind: str, config: OrganizerConfig | None = None) -> dict[str, Any]:
    video_path = str(item.get("video_path") or "")
    meta_path = str(item.get("sidecar_path") or "")
    resolved_meta_path = resolve_sidecar_path(meta_path, config) if config is not None else Path(meta_path)
    resolved_video_path = resolve_media_path(video_path, config) if config is not None else Path(video_path)
    sidecar = load_json(resolved_meta_path, {})
    performer = next(
        (
            entry
            for entry in sidecar.get("performers") or []
            if isinstance(entry, dict)
            and (
                str(entry.get("id") or "") == SAVA_GOLDEN_PERFORMER_ID
                or normalize_identity_key(str(entry.get("name") or "")) == normalize_identity_key(SAVA_GOLDEN_PERFORMER_NAME)
            )
        ),
        {},
    )
    preview_paths = [
        str(path)
        for path in [
            performer.get("face_crop_path"),
            performer.get("original_frame_path"),
            *((sidecar.get("review_frames") or [])[:4]),
        ]
        if str(path or "")
    ]
    similarity = float(item.get("similarity") or performer.get("similarity") or performer.get("confidence") or 0)
    return {
        "video_path": video_path,
        "resolved_video_path": str(resolved_video_path if resolved_video_path.exists() else video_path),
        "meta_path": str(resolved_meta_path if resolved_meta_path.exists() else meta_path),
        "video_name": path_basename(video_path or meta_path),
        "performer_name": SAVA_GOLDEN_PERFORMER_NAME,
        "performer_id": SAVA_GOLDEN_PERFORMER_ID,
        "confidence": round(similarity, 4),
        "confidence_percent": round(similarity * 100),
        "status": str(performer.get("status") or "possible"),
        "verification_needed": True,
        "face_crop_path": str(performer.get("face_crop_path") or ""),
        "frame_path": str(performer.get("original_frame_path") or ""),
        "preview_paths": preview_paths[:6],
        "supporting_faces": int(item.get("supporting_faces") or performer.get("supporting_faces") or 0),
        "has_face_evidence": bool(int(item.get("supporting_faces") or performer.get("supporting_faces") or 0) > 0 or performer.get("face_crop_path")),
        "source_video_exists": resolved_video_path.exists(),
        "in_model_library": True,
        "kind": kind,
    }


def metadata_video_match_record(record: dict[str, Any], *, performer_name: str, performer_id: str, kind: str = "metadata_review") -> dict[str, Any]:
    video_path = str(record.get("video_path") or record.get("path") or "")
    meta_path = str(record.get("_meta_path") or meta_path_for(Path(video_path or "unknown")))
    resolved_video_path = str(record.get("_resolved_video_path") or video_path)
    candidates = [
        candidate
        for candidate in ((record.get("metadata_hints") or {}).get("candidate_names") or [])
        if isinstance(candidate, dict) and not candidate.get("not_performer_name")
    ]
    target_keys = performer_match_keys(performer_name, performer_id)
    matching = []
    for candidate in candidates:
        keys = performer_match_keys(str(candidate.get("name") or ""))
        keys.update(normalize_identity_key(str(item)) for item in candidate.get("variants") or [] if item)
        if target_keys & {key for key in keys if key}:
            matching.append(candidate)
    best_candidate = max(matching, key=lambda item: float(item.get("confidence") or 0), default={})
    confidence = min(0.74, max(0.55, float(best_candidate.get("confidence") or 0.55))) if matching else 0.0
    return {
        "video_path": video_path,
        "resolved_video_path": resolved_video_path,
        "meta_path": meta_path,
        "video_name": Path(video_path or meta_path).name,
        "performer_name": performer_name,
        "performer_id": performer_id,
        "confidence": round(confidence, 4),
        "confidence_percent": round(confidence * 100),
        "status": "metadata_only",
        "verification_needed": True,
        "face_crop_path": "",
        "frame_path": "",
        "preview_paths": sidecar_preview_paths(meta_path, limit=6),
        "supporting_faces": 0,
        "has_face_evidence": False,
        "source_video_exists": bool(record.get("_video_exists", True)),
        "in_model_library": video_is_in_model_library(record, performer_name=performer_name, performer_id=performer_id),
        "kind": kind,
    }


def dedupe_video_match_rows(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_by_name: dict[str, dict[str, Any]] = {}
    for match in matches:
        key = normalize_identity_key(path_basename(match.get("video_name") or match.get("resolved_video_path") or match.get("video_path") or ""))
        if not key:
            key = path_key(match.get("meta_path") or "")
        current = best_by_name.get(key)
        if current is None:
            best_by_name[key] = match
            continue
        current_score = (
            1 if current.get("has_face_evidence") else 0,
            1 if current.get("kind") != "metadata_review" else 0,
            float(current.get("confidence") or 0),
        )
        match_score = (
            1 if match.get("has_face_evidence") else 0,
            1 if match.get("kind") != "metadata_review" else 0,
            float(match.get("confidence") or 0),
        )
        if match_score > current_score:
            best_by_name[key] = match
    return list(best_by_name.values())


def sidecar_preview_paths(meta_path: str, limit: int = 4) -> list[str]:
    if not str(meta_path or "").strip():
        return []
    sidecar_path = Path(str(meta_path))
    if not sidecar_path.is_file():
        return []
    sidecar = load_json(sidecar_path, {})
    performers = [item for item in sidecar.get("performers") or [] if isinstance(item, dict)]
    paths: list[str] = []
    for performer in performers:
        for key in ("face_crop_path", "original_frame_path"):
            value = str(performer.get(key) or "")
            if value and value not in paths:
                paths.append(value)
    for value in sidecar.get("review_frames") or []:
        text = str(value or "")
        if text and text not in paths:
            paths.append(text)
    return paths[:limit]


def enrolled_video_matches(config: OrganizerConfig, group: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    performer_name = str(group.get("name") or "")
    performer_id = str(group.get("known_performer_id") or slugify(performer_name))
    library_matches: list[dict[str, Any]] = []
    missing_matches: list[dict[str, Any]] = []
    auto_matches: list[dict[str, Any]] = []
    pending_matches: list[dict[str, Any]] = []
    for record in collect_metadata(config.source_dir, config.recursive):
        if bool(record.get("faceless_video")):
            continue
        decision_record = video_match_decision_record_for(record, performer_name=performer_name, performer_id=performer_id)
        decision = str((decision_record or {}).get("decision") or "")
        if decision == "rejected":
            continue
        matches = record_performer_matches(record, performer_name=performer_name, performer_id=performer_id)
        if not matches:
            if record_metadata_matches_performer(record, performer_name=performer_name, performer_id=performer_id):
                pending_matches.append(metadata_video_match_record(record, performer_name=performer_name, performer_id=performer_id))
            continue
        best = max(matches, key=lambda item: float(item.get("similarity") or item.get("confidence") or 0))
        confidence = float(best.get("similarity") or best.get("confidence") or 0)
        supporting_faces = int(best.get("supporting_faces") or 0)
        has_face_evidence = bool(supporting_faces > 0 or best.get("face_crop_path") or best.get("original_frame_path"))
        if not bool(record.get("_video_exists", True)):
            missing_matches.append(video_match_record(record, best, kind="missing_source"))
            continue
        if video_is_in_model_library(record, performer_name=performer_name, performer_id=performer_id):
            library_matches.append(video_match_record(record, best, kind="library"))
            continue
        if decision == "accepted":
            if bool((decision_record or {}).get("visual_confirmed")):
                if has_face_evidence:
                    auto_matches.append(video_match_record(record, best, kind="accepted"))
                else:
                    auto_matches.append(metadata_video_match_record(record, performer_name=performer_name, performer_id=performer_id, kind="accepted_manual"))
            else:
                pending_matches.append(video_match_record(record, best, kind="needs_visual_confirm"))
            continue
        if has_face_evidence and confidence >= HIGH_CONFIDENCE and str(best.get("status") or "") == "auto" and not best.get("verification_needed"):
            auto_matches.append(video_match_record(record, best, kind="auto"))
        elif has_face_evidence and confidence >= POSSIBLE_CONFIDENCE:
            pending_matches.append(video_match_record(record, best, kind="pending"))
        elif not has_face_evidence and record_metadata_matches_performer(record, performer_name=performer_name, performer_id=performer_id):
            pending_matches.append(metadata_video_match_record(record, performer_name=performer_name, performer_id=performer_id))
    if performer_id == SAVA_GOLDEN_PERFORMER_ID:
        queue_receipt = latest_sava_uncertain_queue_receipt(config)
        seen_pending = {path_key(match.get("meta_path") or match.get("video_path") or "") for match in pending_matches}
        seen_current = {
            path_key(match.get(field) or "")
            for match in [*library_matches, *missing_matches, *auto_matches, *pending_matches]
            for field in ("meta_path", "resolved_video_path", "video_path")
            if isinstance(match, dict)
        }
        for item in (queue_receipt.get("queued_needs_confirmation") or []) + (queue_receipt.get("above_queue_band") or []):
            if not isinstance(item, dict):
                continue
            key = path_key(item.get("sidecar_path") or item.get("video_path") or "")
            if key in seen_pending:
                continue
            queued_meta_path = resolve_sidecar_path(str(item.get("sidecar_path") or ""), config)
            queued_record = load_json(queued_meta_path, {}) if queued_meta_path.exists() else {}
            queued_video_path = resolve_media_path(str(item.get("video_path") or queued_record.get("video_path") or ""), config)
            if key in seen_current or path_key(queued_meta_path) in seen_current or path_key(queued_video_path) in seen_current:
                continue
            if bool(queued_record.get("faceless_video")):
                continue
            queued_decision = video_match_decision_record_for(queued_record, performer_name=performer_name, performer_id=performer_id)
            if str((queued_decision or {}).get("decision") or "") in {"accepted", "rejected"}:
                continue
            pending_matches.append(queue_video_match_record(item, kind="phase3_needs_confirmation", config=config))
            seen_pending.add(key)
    pending_matches = dedupe_video_match_rows(pending_matches)
    library_matches.sort(key=lambda item: (str(item.get("video_name") or "").lower()))
    missing_matches.sort(key=lambda item: (str(item.get("video_name") or "").lower()))
    auto_matches.sort(key=lambda item: (-float(item.get("confidence") or 0), str(item.get("video_name") or "").lower()))
    pending_matches.sort(key=lambda item: (-float(item.get("confidence") or 0), str(item.get("video_name") or "").lower()))
    return {"library": library_matches, "missing": missing_matches, "auto": auto_matches, "pending": pending_matches}


def enrolled_model_scan_videos(config: OrganizerConfig, performer_name: str, performer_id: str = "") -> list[Path]:
    videos: list[Path] = []
    seen: set[str] = set()

    def add_video(path: Path) -> None:
        if not path.exists() or not path.is_file() or path.suffix.lower() not in VIDEO_EXTENSIONS:
            return
        key = str(path.resolve())
        if key in seen:
            return
        seen.add(key)
        videos.append(path)

    for record in collect_metadata(config.source_dir, config.recursive):
        if not (
            video_is_in_model_library(record, performer_name=performer_name, performer_id=performer_id)
            or record_performer_matches(record, performer_name=performer_name, performer_id=performer_id)
            or record_metadata_matches_performer(record, performer_name=performer_name, performer_id=performer_id)
        ):
            continue
        add_video(Path(str(record.get("_resolved_video_path") or record.get("video_path") or "")))

    slug_keys = performer_match_keys(performer_name, performer_id)
    models_dir = config.source_dir / "models"
    if models_dir.exists():
        for model_dir in models_dir.iterdir():
            if not model_dir.is_dir() or normalize_identity_key(model_dir.name) not in slug_keys:
                continue
            for video_path in find_videos(model_dir, True):
                add_video(video_path)

    for video_path in find_videos(config.source_dir, False):
        if video_filename_matches_performer(video_path, performer_name=performer_name, performer_id=performer_id):
            add_video(video_path)

    def scan_priority(path: Path) -> tuple[int, float, str]:
        meta_path = meta_path_for(path)
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        return (0 if not meta_path.exists() else 1, -mtime, path.name.lower())

    return sorted(videos, key=scan_priority)


def set_enrolled_video_match_decision(config: OrganizerConfig, payload: dict[str, Any]) -> dict[str, Any]:
    performer_name = str(payload.get("performer_name") or "").strip()
    performer_id = str(payload.get("performer_id") or slugify(performer_name)).strip()
    decision = str(payload.get("decision") or "").strip().lower()
    meta_path = resolve_sidecar_path(str(payload.get("meta_path") or ""), config)
    if decision not in {"accepted", "rejected"}:
        raise RuntimeError("decision must be accepted or rejected")
    if not performer_name:
        raise RuntimeError("performer_name is required")
    if not meta_path.exists() or not meta_path.name.endswith(".face-meta.json"):
        raise RuntimeError(f"sidecar not found: {meta_path}")
    record = load_json(meta_path, {})
    matches = record_performer_matches(record, performer_name=performer_name, performer_id=performer_id)
    target_keys = performer_match_keys(performer_name, performer_id)
    metadata_supported = record_metadata_matches_performer(record, performer_name=performer_name, performer_id=performer_id)
    if not matches and not metadata_supported:
        raise RuntimeError(f"no pending face or metadata match for {performer_name} in {meta_path.name}")
    metadata_record = metadata_video_match_record(record, performer_name=performer_name, performer_id=performer_id)
    best = max(matches, key=lambda item: float(item.get("similarity") or item.get("confidence") or 0), default={})
    if not best:
        best = {
            "name": performer_name,
            "id": performer_id,
            "similarity": float(metadata_record.get("confidence") or 0),
            "confidence": float(metadata_record.get("confidence") or 0),
            "status": "manual-confirmed",
            "verification_needed": False,
            "supporting_faces": 0,
        }
    has_face_evidence = bool(
        int(best.get("supporting_faces") or 0) > 0
        or best.get("face_crop_path")
        or best.get("original_frame_path")
    )
    decision_record = {
        "schema": "media-face-enrolled-video-match-decision/v1",
        "decision": decision,
        "performer_name": performer_name,
        "performer_id": performer_id,
        "confidence": round(float(best.get("similarity") or best.get("confidence") or 0), 4),
        "visual_confirmed": bool(payload.get("visual_confirmed")),
        "match_evidence_type": "face_rec" if has_face_evidence else "metadata_only",
        "decided_by": str(payload.get("confirmed_by") or "Britton"),
        "decided_at": utc_now(),
    }
    record.setdefault("face_match_decisions", []).append(decision_record)
    if decision == "accepted":
        matched_existing = False
        for performer in record.get("performers") or []:
            if not isinstance(performer, dict):
                continue
            if target_keys & performer_match_keys(str(performer.get("name") or ""), str(performer.get("id") or "")):
                matched_existing = True
                performer["status"] = "auto" if has_face_evidence else "manual-confirmed"
                performer["verification_needed"] = False
                performer["label"] = f"{performer_name} ({safe_percent(float(performer.get('similarity') or performer.get('confidence') or 0))} confidence)"
        if not matched_existing:
            record.setdefault("performers", []).append(
                {
                    "name": performer_name,
                    "id": performer_id,
                    "confidence": round(float(best.get("confidence") or best.get("similarity") or 0), 4),
                    "similarity": round(float(best.get("similarity") or best.get("confidence") or 0), 4),
                    "status": "manual-confirmed",
                    "verification_needed": False,
                    "label": f"{performer_name} (manual metadata/title confirmation)",
                }
            )
        record["verification_needed"] = any(bool(item.get("verification_needed")) for item in record.get("performers") or [] if isinstance(item, dict))
        record["suggested_organization"] = suggested_org(record.get("performers") or [], config.source_dir)
        registry = load_performer_registry(config.verification_registry_path)
        update_registry_entry(registry, performer_name, [performer_id], record)
        slug, entry = registry_entry_for_name(registry, performer_name)
        if entry is not None:
            entry["status"] = "local-auto" if has_face_evidence else "user-confirmed"
            entry["confirmed_by"] = str(payload.get("confirmed_by") or "Britton")
            entry["confirmed_at"] = decision_record["decided_at"]
            entry.setdefault("audit_events", []).append(decision_record)
        registry["updated_at"] = utc_now()
    else:
        kept = []
        for performer in record.get("performers") or []:
            if not isinstance(performer, dict):
                continue
            if target_keys & performer_match_keys(str(performer.get("name") or ""), str(performer.get("id") or "")):
                continue
            kept.append(performer)
        record["performers"] = kept or [
            {
                "name": "unknown performer",
                "confidence": 0.0,
                "similarity": 0.0,
                "status": "unknown",
                "verification_needed": True,
                "label": "unknown performer - verification needed",
            }
        ]
        record["verification_needed"] = True
        record["suggested_organization"] = suggested_org(record.get("performers") or [], config.source_dir)
    if config.apply:
        json_dump(meta_path, record)
        if decision == "accepted":
            json_dump(config.verification_registry_path, registry)
            write_model_index_from_registry(config, registry)
    return {
        "schema": "media-face-enrolled-video-match-decision-result/v1",
        "event": f"video_match_{decision}",
        "meta_path": str(meta_path),
        "performer_name": performer_name,
        "decision": decision,
        "applied": bool(config.apply),
    }


def mark_video_faceless(config: OrganizerConfig, payload: dict[str, Any]) -> dict[str, Any]:
    meta_path = resolve_sidecar_path(str(payload.get("meta_path") or ""), config)
    performer_name = str(payload.get("performer_name") or "").strip()
    confirmed_by = str(payload.get("confirmed_by") or "Britton").strip()
    if not meta_path.exists() or not meta_path.name.endswith(".face-meta.json"):
        raise RuntimeError(f"sidecar not found: {meta_path}")
    if not confirmed_by:
        raise RuntimeError("confirmed_by is required")
    record = load_json(meta_path, {})
    event = {
        "schema": "media-face-organizer-video-faceless-decision/v1",
        "event": "video_marked_faceless",
        "performer_name": performer_name,
        "confirmed_by": confirmed_by,
        "confirmed_at": utc_now(),
        "reason": str(payload.get("reason") or "No usable performer face in current scan evidence."),
    }
    record["faceless_video"] = True
    record["verification_needed"] = False
    record.setdefault("faceless_video_decisions", []).append(event)
    if config.apply:
        json_dump(meta_path, record)
    return {
        "schema": "media-face-organizer-video-faceless-decision-result/v1",
        "event": "video_marked_faceless",
        "meta_path": str(meta_path),
        "performer_name": performer_name,
        "applied": bool(config.apply),
        "decision": event,
    }


def deep_scan_enrolled_video(config: OrganizerConfig, payload: dict[str, Any]) -> dict[str, Any]:
    performer_name = str(payload.get("performer_name") or "").strip()
    performer_id = str(payload.get("performer_id") or slugify(performer_name)).strip()
    meta_path = resolve_sidecar_path(str(payload.get("meta_path") or ""), config)
    video_value = str(payload.get("video_path") or "").strip()
    video_path: Path | None = resolve_media_path(video_value, config) if video_value else None
    if video_path is None and meta_path:
        record = load_json(meta_path, {})
        video_path = resolve_media_path(str(record.get("_resolved_video_path") or record.get("video_path") or ""), config)
    if not performer_name:
        raise RuntimeError("performer_name is required")
    if video_path is None or not video_path.exists() or not video_path.is_file() or video_path.suffix.lower() not in VIDEO_EXTENSIONS:
        raise RuntimeError(f"video not found: {video_path}")
    requested_frames = int(payload.get("frame_count") or ENROLLMENT_SINGLE_VIDEO_DEEP_SCAN_FRAMES)
    frame_count = min(96, max(ENROLLMENT_SCAN_FRAMES_PER_VIDEO, requested_frames))
    db = KnownPerformersDB(config.db_dir)
    db.load()
    recognizer = InsightFaceRecognizer(config.model_name, config.ctx_id, config.det_size)
    scan_config = dataclasses.replace(config, frame_count=frame_count, force=True)
    meta = scan_video(video_path, scan_config, db, recognizer)
    out_path = meta_path if meta_path.name.endswith(".face-meta.json") else meta_path_for(video_path)
    if config.apply:
        meta = write_scan_sidecar(out_path, meta)
    target_keys = performer_match_keys(performer_name, performer_id)
    matches = [
        item
        for item in meta.get("performers") or []
        if isinstance(item, dict) and target_keys & performer_match_keys(str(item.get("name") or ""), str(item.get("id") or ""))
    ]
    best = max(matches, key=lambda item: float(item.get("similarity") or item.get("confidence") or 0), default={})
    confidence = float(best.get("similarity") or best.get("confidence") or 0)
    return {
        "schema": "media-face-enrolled-video-deep-scan/v1",
        "event": "enrolled_video_deep_scan",
        "performer_name": performer_name,
        "video_path": str(video_path),
        "meta_path": str(out_path),
        "frames_analyzed": int(meta.get("frames_analyzed") or frame_count),
        "faces_detected": int(meta.get("faces_detected") or 0),
        "supporting_faces": int(best.get("supporting_faces") or 0),
        "similarity": round(confidence, 4),
        "status": str(best.get("status") or "no_target_match"),
        "applied": bool(config.apply),
    }


def scan_library_for_enrolled_model(config: OrganizerConfig, payload: dict[str, Any]) -> dict[str, Any]:
    performer_name = str(payload.get("performer_name") or "").strip()
    performer_id = str(payload.get("performer_id") or slugify(performer_name)).strip()
    limit = int(payload.get("limit") or ENROLLMENT_UNIDENTIFIED_RESCAN_LIMIT)
    if not performer_name:
        raise RuntimeError("performer_name is required")
    db = KnownPerformersDB(config.db_dir)
    db.load()
    recognizer = InsightFaceRecognizer(config.model_name, config.ctx_id, config.det_size)
    target_key = normalize_identity_key(performer_name)
    scan_config = dataclasses.replace(config, frame_count=max(config.frame_count, ENROLLMENT_SCAN_FRAMES_PER_VIDEO), force=True)
    candidate_videos = enrolled_model_scan_videos(config, performer_name, performer_id=performer_id)
    videos = candidate_videos[:limit]
    scanned = 0
    auto_matches = 0
    pending_matches = 0
    unknown_matches = 0
    errors: list[dict[str, str]] = []
    scanned_videos: list[dict[str, Any]] = []
    for video_path in videos:
        try:
            meta = scan_video(video_path, scan_config, db, recognizer)
            if config.apply:
                meta = write_scan_sidecar(meta_path_for(video_path), meta)
            scanned += 1
            matches = [
                item
                for item in meta.get("performers") or []
                if isinstance(item, dict) and normalize_identity_key(str(item.get("name") or "")) == target_key
            ]
            if not matches:
                unknown_matches += 1
                scanned_videos.append(
                    {
                        "video_path": str(video_path),
                        "faces_detected": int(meta.get("faces_detected") or 0),
                        "status": "no_target_match",
                        "best_similarity": max(
                            (float(item.get("similarity") or 0) for item in meta.get("performers") or [] if isinstance(item, dict)),
                            default=0.0,
                        ),
                    }
                )
                continue
            best = max(matches, key=lambda item: float(item.get("similarity") or item.get("confidence") or 0))
            confidence = float(best.get("similarity") or best.get("confidence") or 0)
            has_face_evidence = bool(int(best.get("supporting_faces") or 0) > 0 or best.get("face_crop_path") or best.get("original_frame_path"))
            scanned_videos.append(
                {
                    "video_path": str(video_path),
                    "faces_detected": int(meta.get("faces_detected") or 0),
                    "supporting_faces": int(best.get("supporting_faces") or 0),
                    "status": str(best.get("status") or ""),
                    "similarity": round(confidence, 4),
                    "face_crop_path": str(best.get("face_crop_path") or ""),
                }
            )
            if not has_face_evidence:
                unknown_matches += 1
            elif confidence >= HIGH_CONFIDENCE and str(best.get("status") or "") == "auto" and not best.get("verification_needed"):
                auto_matches += 1
            elif confidence >= POSSIBLE_CONFIDENCE:
                pending_matches += 1
        except Exception as exc:
            errors.append({"video_path": str(video_path), "error": str(exc)})
    return {
        "schema": "media-face-enrolled-library-scan/v1",
        "performer_name": performer_name,
        "scanned": scanned,
        "candidate_videos": len(candidate_videos),
        "scan_limit": limit,
        "remaining_candidates": max(0, len(candidate_videos) - scanned),
        "auto_matches": auto_matches,
        "pending_matches": pending_matches,
        "unknown_matches": unknown_matches,
        "thresholds": {"auto": HIGH_CONFIDENCE, "review": POSSIBLE_CONFIDENCE},
        "scanned_videos": scanned_videos[:50],
        "errors": errors[:10],
        "applied": bool(config.apply),
    }


def registry_entry_for_name(registry: dict[str, Any], name: str) -> tuple[str, dict[str, Any] | None]:
    key = normalize_identity_key(name)
    for slug, entry in (registry.get("performers") or {}).items():
        if not isinstance(entry, dict):
            continue
        keys = {normalize_identity_key(str(slug)), normalize_identity_key(str(entry.get("name") or ""))}
        keys.update(normalize_identity_key(str(alias)) for alias in entry.get("aliases", []) if alias)
        if key in keys:
            return str(slug), entry
    return slugify(name), None


def merge_unique_values(current: list[Any], incoming: list[Any]) -> list[Any]:
    merged = list(current or [])
    seen = {json.dumps(item, sort_keys=True, default=str) for item in merged}
    for item in incoming or []:
        key = json.dumps(item, sort_keys=True, default=str)
        if key not in seen:
            merged.append(item)
            seen.add(key)
    return merged


def backup_registry_model_files(config: OrganizerConfig) -> Path:
    backup_root = timestamped_backup_root(config) / "registry-model-merge"
    backup_root.mkdir(parents=True, exist_ok=True)
    files = []
    for path in (config.verification_registry_path, config.verification_registry_path.with_name("model_index.json")):
        if path.exists():
            shutil.copy2(path, backup_root / path.name)
            files.append(path.name)
    json_dump(
        backup_root / "backup_manifest.json",
        {
            "schema": "media-face-enrollment-registry-merge-backup/v1",
            "created_at": utc_now(),
            "files": files,
        },
    )
    return backup_root


def merge_duplicate_creator(config: OrganizerConfig, payload: dict[str, Any]) -> dict[str, Any]:
    source_name = str(payload.get("source_name") or payload.get("duplicate_name") or "").strip()
    target_name = str(payload.get("target_name") or payload.get("known_creator") or "").strip()
    confirmation = str(payload.get("confirmation") or "").strip()
    confirmed_by = str(payload.get("confirmed_by") or "Britton").strip()
    if not source_name or not target_name:
        raise RuntimeError("source_name and target_name are required")
    if normalize_identity_key(source_name) == normalize_identity_key(target_name):
        raise RuntimeError("source and target are already the same normalized creator")
    if confirmation not in {target_name, slugify(target_name)}:
        raise RuntimeError("confirmation field must match the target creator name or slug")
    if not confirmed_by:
        raise RuntimeError("confirmed_by is required")

    registry = load_performer_registry(config.verification_registry_path)
    source_slug, source_entry = registry_entry_for_name(registry, source_name)
    target_slug, target_entry = registry_entry_for_name(registry, target_name)
    if not target_entry:
        target_slug = slugify(target_name)
        target_entry = {
            "name": target_name,
            "slug": target_slug,
            "aliases": [],
            "profile_handles": [],
            "status": "user-confirmed",
            "evidence": [],
            "video_count": 0,
            "audit_events": [],
        }
        registry.setdefault("performers", {})[target_slug] = target_entry

    alias_set = {str(alias) for alias in target_entry.get("aliases", []) if alias}
    alias_set.update({source_name, source_slug})
    if source_entry:
        alias_set.add(str(source_entry.get("name") or source_name))
        alias_set.update(str(alias) for alias in source_entry.get("aliases", []) if alias)
        for field in ("profile_handles", "evidence", "enrolled_face_samples", "audit_events"):
            target_entry[field] = merge_unique_values(target_entry.get(field, []), source_entry.get(field, []))
        target_entry["video_count"] = int(target_entry.get("video_count") or 0) + int(source_entry.get("video_count") or 0)
        if source_slug != target_slug:
            registry.get("performers", {}).pop(source_slug, None)
    target_entry["aliases"] = sorted(alias_set, key=str.lower)
    target_entry["status"] = "user-confirmed"
    target_entry.setdefault("audit_events", []).append(
        {
            "event": "duplicate_creator_merged",
            "source_name": source_name,
            "target_name": target_name,
            "confirmed_by": confirmed_by,
            "at": utc_now(),
        }
    )
    aliases = registry.setdefault("aliases", {})
    aliases[normalize_identity_key(source_name)] = target_name
    aliases[normalize_identity_key(source_slug)] = target_name
    registry["updated_at"] = utc_now()

    known_before = known_db_summary(config.db_dir)
    source_known = None
    target_known = None
    source_key = normalize_identity_key(source_name)
    target_key = normalize_identity_key(target_name)
    for performer in known_before.get("performers", []):
        if not isinstance(performer, dict):
            continue
        keys = {normalize_identity_key(str(performer.get("id") or "")), normalize_identity_key(str(performer.get("name") or ""))}
        keys.update(normalize_identity_key(str(alias)) for alias in performer.get("aliases", []) if alias)
        if source_key in keys:
            source_known = performer
        if target_key in keys:
            target_known = performer

    if not config.apply:
        return {
            "dry_run": True,
            "source_name": source_name,
            "target_name": target_name,
            "registry_source_found": bool(source_entry),
            "known_source_found": bool(source_known),
            "known_target_found": bool(target_known),
            "message": "Restart --serve-review with --apply to write this merge after confirmation.",
        }

    registry_backup = backup_registry_model_files(config)
    db_backup = backup_known_performers_files(config)
    json_dump(config.verification_registry_path, registry)
    write_model_index_from_registry(config, registry)
    candidate_path = enrollment_review_dir(config) / "enrollment_candidates.json"
    candidate_payload = load_json(candidate_path, {"groups": []})
    if isinstance(candidate_payload, dict) and isinstance(candidate_payload.get("groups"), list):
        source_slug = slugify(source_name)
        target_slug = slugify(target_name)
        merged_groups: list[dict[str, Any]] = []
        target_group: dict[str, Any] | None = None
        for group in candidate_payload.get("groups", []):
            if not isinstance(group, dict):
                continue
            if str(group.get("slug")) == target_slug:
                target_group = dict(group)
            elif str(group.get("slug")) != source_slug:
                merged_groups.append(group)
        for group in candidate_payload.get("groups", []):
            if not isinstance(group, dict) or str(group.get("slug")) != source_slug:
                continue
            if target_group is None:
                target_group = dict(group)
                target_group["slug"] = target_slug
                target_group["name"] = target_name
            else:
                for field in ("recommended_crops", "recommended_stills", "records"):
                    target_group[field] = merge_unique_values(target_group.get(field, []), group.get(field, []))
        if target_group is not None:
            merged_groups = [group for group in merged_groups if str(group.get("slug")) != target_slug]
            merged_groups.append(target_group)
        candidate_payload["groups"] = sorted(merged_groups, key=lambda item: str(item.get("name") or "").lower())
        candidate_payload["updated_at"] = utc_now()
        json_dump(candidate_path, candidate_payload)

    if source_known:
        db = KnownPerformersDB(config.db_dir)
        db.load()
        performers = db.index.setdefault("performers", [])
        if not target_known:
            target_known = source_known
            target_known["id"] = slugify(target_name)
            target_known["name"] = target_name
        target_id = str(target_known.get("id") or slugify(target_name))
        source_id = str(source_known.get("id") or slugify(source_name))
        for row, performer_id in list(db.performer_map.items()):
            if str(performer_id) == source_id:
                db.performer_map[str(row)] = target_id
        kept = []
        for performer in performers:
            if not isinstance(performer, dict):
                continue
            if str(performer.get("id")) == source_id and source_id != target_id:
                continue
            if str(performer.get("id")) == target_id:
                aliases = {str(alias) for alias in performer.get("aliases", []) if alias}
                aliases.update({source_name, source_id})
                performer["aliases"] = sorted(aliases, key=str.lower)
                performer.setdefault("audit_events", []).append(
                    {
                        "event": "duplicate_creator_merged",
                        "source_name": source_name,
                        "target_name": target_name,
                        "confirmed_by": confirmed_by,
                        "at": utc_now(),
                    }
                )
            kept.append(performer)
        db.index["performers"] = kept
        json_dump(db.index_path, db.index)
        json_dump(db.map_path, db.performer_map)

    audit = {
        "schema": "media-face-enrollment-merge-audit/v1",
        "event": "duplicate_creator_merged",
        "source_name": source_name,
        "target_name": target_name,
        "confirmed_by": confirmed_by,
        "merged_at": utc_now(),
        "registry_backup": str(registry_backup),
        "known_db_backup": str(db_backup),
        "previous_db_counts": {
            "performers": len(known_before.get("performers", [])),
            "embedding_rows": int(known_before.get("embedding_rows") or 0),
        },
        "new_db_counts": {
            "performers": len(known_db_summary(config.db_dir).get("performers", [])),
            "embedding_rows": int(known_db_summary(config.db_dir).get("embedding_rows") or 0),
        },
    }
    audit_path = enrollment_review_dir(config) / "creator_merge_audit.jsonl"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(audit, ensure_ascii=False) + "\n")
    return audit


def render_model_verification_links(hints: list[dict[str, Any]]) -> str:
    queries = text_verification_queries(hints[:3], limit=3)
    if not queries:
        return ""
    groups = []
    by_name: dict[str, list[dict[str, Any]]] = {}
    for item in queries:
        name = str(item.get("candidate_name") or "")
        by_name.setdefault(name, []).append(item)
    for name, links_for_name in by_name.items():
        links = " ".join(
            f'<a href="{html.escape(link["url"], quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(link["label"])}</a>'
            for link in links_for_name[:5]
        )
        groups.append(f'<div><span>{html.escape(name)}</span>{links}</div>')
    return f'<div class="verify-links"><p>Text verification links</p>{"".join(groups)}</div>'


def render_assignment_decision(record: dict[str, Any]) -> str:
    decision = normalize_assignment_decision(record.get("assignment_decision"))
    if not record.get("assignment_decision"):
        scored = score_assignment(record)
        decision = scored["assignment_decision"]
        trace = scored["identity_trace"]
    else:
        trace = normalize_identity_trace(record.get("identity_trace"))
    status = "auto" if decision.get("auto_assign_allowed") else "review"
    blockers = "".join(f"<li>{html.escape(reason)}</li>" for reason in decision.get("blocking_reasons") or [])
    confidence = round(float(decision.get("confidence") or 0) * 100)
    trace_html = render_identity_trace(trace)
    return f"""
      <div class="decision-panel">
        <div class="decision-head">
          <span class="decision-pill decision-{html.escape(status)}">{html.escape(status)}</span>
          <strong>{html.escape(str(decision.get("suggested_name") or "No assignment"))}</strong>
          <span>{confidence}%</span>
        </div>
        <p>{html.escape(str(decision.get("why") or "No decision reason recorded."))}</p>
        {f'<ul class="blockers">{blockers}</ul>' if blockers else ''}
        {trace_html}
      </div>
    """


def render_identity_trace(trace: list[dict[str, Any]]) -> str:
    if not trace:
        return '<div class="trace empty-mini">No identity trace recorded.</div>'
    rows = []
    for item in trace[:8]:
        confidence = item.get("confidence")
        confidence_text = f"{round(float(confidence) * 100)}%" if isinstance(confidence, (int, float)) else "n/a"
        source_path = str(item.get("source_path") or "")
        source_link = f' <a href="{html.escape(source_path, quote=True)}" target="_blank" rel="noopener noreferrer">source</a>' if source_path.startswith("http") else ""
        rows.append(
            "<li>"
            f"<strong>{html.escape(str(item.get('signal_type') or 'signal'))}</strong>"
            f"<span>{html.escape(str(item.get('value') or ''))}</span>"
            f"<em>{confidence_text}</em>"
            f"<p>{html.escape(str(item.get('reason') or ''))}{source_link}</p>"
            "</li>"
        )
    return f'<div class="trace"><p>Why this name?</p><ol>{"".join(rows)}</ol></div>'


def render_web_evidence(record: dict[str, Any]) -> str:
    evidence = normalize_web_text_evidence(record.get("web_text_evidence"))
    if not evidence:
        return ""
    cards = []
    for item in evidence[:6]:
        cards.append(
            '<div class="evidence-card">'
            f'<span>{html.escape(str(item.get("source_trust_level") or "unknown"))}</span>'
            f'<a href="{html.escape(str(item.get("url") or ""), quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(str(item.get("title") or item.get("source_domain") or "text result"))}</a>'
            f'<p>{html.escape(str(item.get("snippet") or ""))}</p>'
            '<small>Text result only. Review required.</small>'
            '</div>'
        )
    return f'<div class="web-evidence"><p>Web text evidence</p><div>{ "".join(cards) }</div></div>'


def render_query_cards(record: dict[str, Any]) -> str:
    metadata = record.get("metadata_hints") or {}
    queries = metadata.get("text_verification_queries") or text_verification_queries(metadata.get("candidate_names") or [], limit=3)
    if not queries:
        return ""
    links = []
    for item in queries[:8]:
        links.append(
            f'<a href="{html.escape(str(item.get("url") or ""), quote=True)}" target="_blank" rel="noopener noreferrer">'
            f'{html.escape(str(item.get("label") or item.get("provider") or "Search"))}'
            f'<small>{html.escape(str(item.get("query") or ""))}</small></a>'
        )
    return f'<div class="query-cards"><p>Generated text queries</p><div>{"".join(links)}</div></div>'


def render_action_snippets(record: dict[str, Any], first_name: str) -> str:
    meta_path = str(record.get("_meta_path") or meta_path_for(Path(record.get("video_path") or "unknown")))
    suggested = "" if first_name == "unknown performer" else first_name
    escaped_suggested = html.escape(suggested, quote=True)
    escaped_meta = html.escape(meta_path, quote=True)
    search_query = html.escape(urllib.parse.quote(suggested or "<entered-name>"), quote=True)
    pending = (
        f'python scripts/media/face_organizer.py --source "{Path(record.get("video_path") or ".").parent}" '
        f'--record-correction "{suggested or "<actual-name>"}" --sidecar "{meta_path}" '
        f'--corrected-by Britton --apply'
    )
    confirm = (
        f'python scripts/media/face_organizer.py --source "{Path(record.get("video_path") or ".").parent}" '
        f'--confirm-correction --sidecar "{meta_path}" --confirmed-by Britton --apply'
    )
    existing = (
        f'python scripts/media/face_organizer.py --record-correction "{suggested or "<existing-performer>"}" '
        f'--sidecar "{meta_path}" --belongs-to-existing --corrected-by Britton --apply'
    )
    reject = f'Mark unknown / needs review: edit {meta_path} and keep "verification_needed": true'
    return (
        '<div class="primary-actions">'
        '<label>Actual model/creator name'
        f'<input class="manual-name" placeholder="Enter confirmed name" value="{escaped_suggested}" data-sidecar="{escaped_meta}"></label>'
        '<div class="manual-submit-row">'
        '<button type="button" class="manual-submit" data-action="manual-model-correction">Apply correction</button>'
        f'<button type="button" class="manual-submit unknown-submit" data-action="leave-unknown" data-sidecar="{escaped_meta}">Leave unknown</button>'
        '<label class="inline-check"><input type="checkbox" class="manual-existing"> Belongs to existing enrolled model</label>'
        '<span class="manual-status" aria-live="polite"></span>'
        '</div>'
        '<div class="action-grid">'
        f'<a class="action-link" href="https://yandex.com/search/?text={search_query}" target="_blank" rel="noopener noreferrer">Search this name</a>'
        f'<code class="confirm">Save pending evidence: {html.escape(pending)}</code>'
        f'<code class="confirm">Confirm database update: {html.escape(confirm)}</code>'
        f'<code class="edit">Belongs to existing performer: {html.escape(existing)}</code>'
        f'<code class="unknown">{html.escape(reject)}</code>'
        '</div>'
        '</div>'
    )


def render_plain_reason(record: dict[str, Any]) -> str:
    decision = normalize_assignment_decision(record.get("assignment_decision"))
    if decision.get("why"):
        return str(decision.get("why"))
    faces = int(record.get("faces_detected") or 0)
    if faces <= 0:
        rejected = record.get("faces_rejected") or record.get("rejected_faces") or []
        if rejected:
            return "No accepted face detected; one or more detections were rejected by quality thresholds."
        return "No accepted face detected, so face recognition could not assign a performer."
    performers = record.get("performers") or []
    best = max((float(item.get("similarity") or 0) for item in performers if isinstance(item, dict)), default=0.0)
    if best < POSSIBLE_CONFIDENCE:
        return f"Faces were detected, but local face similarity stayed below review threshold ({best:.3f})."
    return "Review required before any database or organization action."


def record_left_unknown(record: dict[str, Any]) -> bool:
    return bool(record.get("left_unknown_decision"))


def record_has_unknown_model(record: dict[str, Any]) -> bool:
    if record_left_unknown(record) or bool(record.get("faceless_video")):
        return False
    performers = [item for item in record.get("performers") or [] if isinstance(item, dict)]
    if not performers:
        return True
    return all(normalize_identity_key(str(item.get("name") or "")) in {"", "unknownperformer"} for item in performers)


def extract_unscanned_preview_frames(video_path: Path, review_dir: Path, frame_count: int) -> list[Path]:
    require_ffmpeg()
    review_dir.mkdir(parents=True, exist_ok=True)
    timestamps = [2.0, 10.0, 20.0, 35.0][: max(1, frame_count)]
    saved: list[Path] = []
    for index, timestamp in enumerate(timestamps, 1):
        target = review_dir / f"unscanned-preview-{index:02d}.jpg"
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{timestamp:.2f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            "-q:v",
            "3",
            "-y",
            str(target),
        ]
        subprocess.run(command, check=False, capture_output=True, text=True)
        if target.exists() and target.stat().st_size > 0:
            saved.append(target)
    return saved


def ensure_unscanned_preview_frames(video_path: Path, config: OrganizerConfig, frame_count: int = 2) -> list[str]:
    review_dir = video_path.parent / config.review_dir_name / video_path.stem / "frames"
    existing = sorted(review_dir.glob("unscanned-preview-*.jpg"))
    if len(existing) >= frame_count:
        return [str(path) for path in existing[:frame_count]]
    if not config.apply:
        return []
    try:
        saved = extract_unscanned_preview_frames(video_path, review_dir, frame_count)
        return [str(path) for path in saved]
    except Exception as exc:
        logging.warning("Could not create unscanned preview frames for %s: %s", video_path, exc)
        return [str(path) for path in existing[:frame_count]]


def unscanned_unknown_record(video_path: Path, config: OrganizerConfig) -> dict[str, Any]:
    meta_path = meta_path_for(video_path)
    candidates = extract_filename_candidates(video_path)
    review_frames = ensure_unscanned_preview_frames(video_path, config)
    return {
        "schema": "media-face-organizer/unscanned-placeholder/v1",
        "video_path": str(video_path),
        "path": str(video_path),
        "filename": video_path.name,
        "_meta_path": str(meta_path),
        "_resolved_video_path": str(video_path),
        "_video_exists": True,
        "verification_needed": True,
        "unscanned": True,
        "faces_detected": None,
        "performers": [
            {
                "name": "unknown performer",
                "confidence": 0.0,
                "similarity": 0.0,
                "status": "unknown",
                "verification_needed": True,
                "label": "unknown performer - verification needed",
                "supporting_faces": 0,
            }
        ],
        "metadata_hints": {"candidate_names": candidates},
        "review_frames": review_frames,
        "assignment_decision": {
            **blank_assignment_decision(),
            "suggested_name": candidates[0]["name"] if candidates else "",
            "confidence": min(0.5, float((candidates[0] if candidates else {}).get("confidence") or 0.0)),
            "why": "Video has not been face-scanned yet; queued for verification as unknown.",
            "blocking_reasons": ["no face sidecar exists yet"],
        },
    }


def verification_attention_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        record
        for record in records
        if record.get("verification_needed") or record_has_unknown_model(record)
    ]


def verification_queue_fingerprint_from_attention(attention: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for record in sorted(
        attention,
        key=lambda item: str(item.get("_resolved_video_path") or item.get("video_path") or item.get("path") or ""),
    ):
        path = str(record.get("_resolved_video_path") or record.get("video_path") or record.get("path") or "")
        meta_path = str(record.get("_meta_path") or "")
        parts.append(
            "|".join(
                [
                    path,
                    meta_path,
                    f"unscanned={int(bool(record.get('unscanned')))}",
                    f"vn={int(bool(record.get('verification_needed')))}",
                ]
            )
        )
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:20]


def build_verification_queue_status(config: OrganizerConfig) -> dict[str, Any]:
    records = verification_queue_records(config)
    attention = verification_attention_records(records)
    fingerprint = verification_queue_fingerprint_from_attention(attention)
    stored = load_json(config.report_path.with_suffix(".json"), {})
    report_fingerprint = str(stored.get("fingerprint") or "")
    return {
        "schema": "media-face-verification-queue-status/v1",
        "fingerprint": fingerprint,
        "report_fingerprint": report_fingerprint,
        "review_count": len(attention),
        "total_count": len(records),
        "report_stale": fingerprint != report_fingerprint,
        "generated_at": utc_now(),
    }


def verification_queue_records(config: OrganizerConfig) -> list[dict[str, Any]]:
    records = collect_metadata(config.source_dir, config.recursive)
    by_video_key = {
        path_key(record.get("_resolved_video_path") or record.get("video_path") or record.get("path") or "")
        for record in records
    }
    for video_path in find_verification_queue_videos(config.source_dir, config.recursive):
        key = path_key(video_path)
        if key in by_video_key or meta_path_for(video_path).exists():
            continue
        records.append(unscanned_unknown_record(video_path, config))
        by_video_key.add(key)
    return records


def render_preview_section(review_frames: list[str], crops: list[str]) -> str:
    face_html = "".join(crops)
    frame_html = "".join(review_frames[:6])
    if not face_html and not frame_html:
        return '<div class="preview-panel"><div class="empty-crop">No preview images saved yet. Rescan or run frame backfill.</div></div>'
    return (
        '<div class="preview-panel">'
        f'<div class="thumbs preview-faces">{face_html or "<div class=\"empty-crop compact-empty\">No face crop saved.</div>"}</div>'
        f'<div class="frame-strip preview-frames">{frame_html}</div>'
        '</div>'
    )


def render_review_hints(hints: list[dict[str, Any]]) -> str:
    if not hints:
        return '<div class="review-hints"><p>Verification hints</p><div class="empty-mini">No OCR or filename hints recorded.</div></div>'
    chips = []
    for item in hints[:6]:
        source = str(item.get("source") or "")
        confidence = item.get("confidence")
        confidence_text = f"{round(float(confidence) * 100)}%" if isinstance(confidence, (int, float)) else "n/a"
        role = "site clue" if source == "site_watermark" or item.get("not_performer_name") else source.replace("_", " ")
        chips.append(
            '<span class="review-hint">'
            f'<strong>{html.escape(str(item.get("name") or ""))}</strong>'
            f'<small>{html.escape(role)} - {html.escape(confidence_text)}</small>'
            '</span>'
        )
    return f'<div class="review-hints"><p>Verification hints</p><div>{"".join(chips)}</div></div>'


def render_review_details(
    decision_html: str,
    query_html: str,
    web_evidence_html: str,
) -> str:
    return f"""
      <details class="review-details">
        <summary>Show details</summary>
        {decision_html}
        {query_html}
        {web_evidence_html}
      </details>
    """


def render_enrollment_crop(crop: dict[str, Any]) -> str:
    crop_path = str(crop.get("crop_path") or "")
    still_path = str(crop.get("still_path") or "")
    crop_src = display_image_src(crop_path)
    video_name = str(crop.get("source_video_name") or Path(str(crop.get("source_video") or "")).name)
    enroll_score = crop.get("enrollment_detection_score")
    score_text = f"enroll {enroll_score} / " if enroll_score not in (None, "") else ""
    return f"""
      <label class="crop-card">
        <input type="checkbox" name="crop" value="{html.escape(crop_path, quote=True)}" data-still="{html.escape(still_path, quote=True)}" data-video="{html.escape(str(crop.get("source_video") or ""), quote=True)}" data-timestamp="{html.escape(str(crop.get("timestamp") or ""), quote=True)}">
        <img src="{html.escape(crop_src, quote=True)}" alt="Candidate face crop" loading="lazy" decoding="async">
        <strong title="{html.escape(video_name, quote=True)}">{html.escape(video_name)}</strong>
        <span>{html.escape(str(crop.get("timestamp") or "?"))}s</span>
        <small>{html.escape(score_text)}detect {html.escape(str(crop.get("detection_score") or "n/a"))} / quality {html.escape(str(crop.get("quality_score") or "n/a"))}</small>
        <a href="{html.escape(still_path, quote=True)}" target="_blank" rel="noopener noreferrer">Open still frame</a>
        <button type="button" class="small-action" data-action="manual-one" data-performer="" data-still="{html.escape(still_path, quote=True)}" data-video="{html.escape(str(crop.get("source_video") or ""), quote=True)}" data-timestamp="{html.escape(str(crop.get("timestamp") or ""), quote=True)}">Manual crop this still</button>
      </label>
    """


def render_enrollment_still(still: dict[str, Any]) -> str:
    still_path = str(still.get("still_path") or "")
    still_src = display_image_src(still_path)
    video_name = str(still.get("source_video_name") or Path(str(still.get("source_video") or "")).name)
    return f"""
      <div class="crop-card still-card">
        <input type="checkbox" disabled title="Manual crop this still before enrollment">
        <img src="{html.escape(still_src, quote=True)}" alt="Candidate still frame" loading="lazy" decoding="async">
        <strong title="{html.escape(video_name, quote=True)}">{html.escape(video_name)}</strong>
        <span>{html.escape(str(still.get("timestamp") or "?"))}s</span>
        <small>no face found — manual crop</small>
        <a href="{html.escape(still_path, quote=True)}" target="_blank" rel="noopener noreferrer">Open still frame</a>
        <button type="button" class="small-action" data-action="manual-one" data-still="{html.escape(still_path, quote=True)}" data-video="{html.escape(str(still.get("source_video") or ""), quote=True)}" data-timestamp="{html.escape(str(still.get("timestamp") or ""), quote=True)}">Manual crop this still</button>
      </div>
    """


def enrollment_card_should_expand(group: dict[str, Any], *, enrolled: bool = False) -> bool:
    if enrollment_missing_video_count(group) > 0:
        return True
    if str(group.get("blocked_reason") or "").strip():
        return True
    if enrolled:
        confidence = group.get("confidence_estimate") or enrolled_confidence_estimate(group)
        return int(confidence.get("percent") or 0) < 90
    return False


def render_page_collapse_controls() -> str:
    return """
    <div class="page-collapse-controls">
      <button type="button" class="page-expand-all">Expand all models</button>
      <button type="button" class="page-collapse-all">Collapse all models</button>
      <button type="button" class="page-rescan-all-models">Rescan all models</button>
    </div>
    """


def render_enrollment_group(group: dict[str, Any]) -> str:
    crops = group.get("recommended_crops") or []
    stills = group.get("recommended_stills") or []
    recommendation_html = render_recommendations_by_video(crops, stills)
    records = "".join(
        f'<li>{html.escape(Path(str(record.get("video_path") or record.get("meta_path") or "")).name)}</li>'
        for record in group.get("records", [])[:5]
    )
    blocked = str(group.get("blocked_reason") or "")
    missing_videos = enrollment_missing_video_count(group)
    stale_banner = ""
    if missing_videos > 0:
        stale_banner = (
            f'<p class="blocked">'
            f"{missing_videos} linked video(s) not face-scanned yet — use Rescan all model videos."
            f"</p>"
        )
    flags = [
        f"registry: {'yes' if group.get('registry_present') else 'no'}",
        f"model_index: {'yes' if group.get('model_index_present') else 'no'}",
        f"known record: {'yes' if group.get('known_performers_record') else 'no'}",
        f"embedding rows: {len(group.get('embedding_rows') or [])}",
    ]
    open_attr = " open" if enrollment_card_should_expand(group) else ""
    return f"""
      <article class="enroll-card" data-status="{html.escape(str(group.get('status') or ''))}" data-performer="{html.escape(str(group.get("name") or ""), quote=True)}">
        <details class="model-card-collapse"{open_attr}>
          <summary class="enroll-head model-card-summary">
            <div>
              <p>{html.escape(str(group.get("status") or ""))}</p>
              <h2>{html.escape(str(group.get("name") or ""))}</h2>
              <small>{html.escape(str(group.get("why") or ""))}</small>
            </div>
            <div class="mini-metrics">
              <span>{html.escape(str(group.get("candidate_videos") or 0))} videos</span>
              <span>{html.escape(str(group.get("candidate_face_crops") or 0))} crops</span>
              <span class="collapse-chevron" aria-hidden="true">▸</span>
            </div>
          </summary>
          <div class="enroll-card-body">
        <div class="presence">{"".join(f"<span>{html.escape(flag)}</span>" for flag in flags)}</div>
        <p class="exists">Why this candidate exists: {html.escape(", ".join(group.get("exists_because") or []))}</p>
        {stale_banner}
        {f'<p class="blocked">Limited: {html.escape(blocked)}</p>' if blocked else ''}
        {render_recommendation_video_summary(group)}
        {render_scan_coverage(group)}
        <div class="recommendation-groups">{recommendation_html}</div>
        <div class="action-status" aria-live="polite"></div>
        <form class="enroll-form" data-performer="{html.escape(str(group.get("name") or ""), quote=True)}">
          <input type="hidden" name="performer_name" value="{html.escape(str(group.get("name") or ""), quote=True)}">
          <label>Confirmation name or slug<input name="confirmation" placeholder="{html.escape(str(group.get("name") or ""), quote=True)}"></label>
          <details class="merge-panel">
            <summary>Merge duplicate creator / alias</summary>
            <label>Duplicate/source name<input name="merge_source" value="{html.escape(str(group.get("name") or ""), quote=True)}"></label>
            <label>Correct known creator<input name="merge_target" placeholder="Existing/correct creator name"></label>
            <label>Confirm correct creator<input name="merge_confirmation" placeholder="Type exact target name or slug"></label>
            <button type="button" data-action="merge-creator">Merge source into correct creator</button>
          </details>
          <div class="button-row">
            <button type="button" class="primary-action" data-action="more">Rescan all model videos</button>
            <button type="button" {'class="primary-action"' if missing_videos else ''} data-action="missing-videos">Scan missing/new linked videos</button>
            <button type="button" data-action="reject">Reject crop</button>
            <button type="button" data-action="better">Needs better sample</button>
            <button type="button" data-action="faceless">Mark model faceless</button>
            <button type="button" data-action="manual">Manual crop from still</button>
            <button type="button" data-action="smart-accept">Smart accept best 5</button>
            <button type="button" data-action="enroll-existing">Enroll selected crops as existing performer</button>
            <button type="button" data-action="enroll-new">Create new face-enrolled performer from selected crops</button>
          </div>
        </form>
        <details><summary>Source records</summary><ul>{records or '<li>No associated sidecars yet.</li>'}</ul></details>
          </div>
        </details>
      </article>
    """


def enrollment_page_css() -> str:
    return report_nav_css() + """
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: #09090b; color: #f4f4f5; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    header, main { width: min(1180px, calc(100vw - 2rem)); margin: 0 auto; }
    header { padding: 2rem 0 1rem; }
    h1 { margin: .2rem 0; font-size: clamp(1.8rem, 3vw, 3rem); letter-spacing: 0; }
    .muted, .exists, small { color: #a1a1aa; }
    .summary { display: flex; flex-wrap: wrap; gap: .5rem; margin: 1rem 0; }
    .summary span, .presence span, .mini-metrics span { border-radius: .25rem; background: rgba(255,255,255,.07); padding: .35rem .5rem; color: #e4e4e7; }
    .grid { display: grid; gap: 1rem; padding-bottom: 3rem; }
    .enroll-card { border-radius: .45rem; background: rgba(255,255,255,.045); outline: 1px solid rgba(255,255,255,.08); padding: 1rem; }
    .model-card-collapse { display: block; }
    .model-card-collapse > summary.model-card-summary { list-style: none; cursor: pointer; }
    .model-card-collapse > summary.model-card-summary::-webkit-details-marker { display: none; }
    .model-card-collapse > summary.model-card-summary::marker { content: ''; }
    .model-card-collapse[open] > summary .collapse-chevron { transform: rotate(90deg); }
    .collapse-chevron { display: inline-flex; align-items: center; justify-content: center; width: 1.5rem; height: 1.5rem; border-radius: .25rem; background: rgba(103,232,249,.12); color: #67e8f9; font-size: .95rem; line-height: 1; transition: transform .15s ease; }
    .enroll-card-body { padding-top: .15rem; }
    .page-collapse-controls { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .75rem; }
    .page-collapse-controls button { background: rgba(255,255,255,.08); color: #e4e4e7; }
    .enroll-head { display: flex; justify-content: space-between; gap: 1rem; align-items: flex-start; }
    .enroll-head p { margin: 0 0 .25rem; color: #a7f3d0; font-size: .75rem; text-transform: uppercase; }
    .enroll-head h2 { margin: 0; overflow-wrap: anywhere; letter-spacing: 0; }
    .model-title { display: flex; align-items: center; gap: .85rem; min-width: 0; }
    .model-title > div { min-width: 0; }
    .model-avatar { flex: 0 0 4.5rem; width: 4.5rem; height: 5.8rem; display: block; overflow: hidden; border-radius: .35rem; background: rgba(0,0,0,.35); outline: 1px solid rgba(255,255,255,.12); }
    .model-avatar img { width: 100%; height: 100%; display: block; object-fit: cover; }
    .model-avatar-empty { background: linear-gradient(135deg, rgba(20,184,166,.16), rgba(59,130,246,.12)); }
    .mini-metrics, .presence, .button-row { display: flex; flex-wrap: wrap; gap: .45rem; }
    .presence { margin-top: .8rem; }
    .blocked { border-radius: .25rem; background: rgba(251,191,36,.12); color: #fef3c7; padding: .55rem; }
    .crop-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(155px, 1fr)); gap: .75rem; margin-top: .9rem; align-items: stretch; }
    .crop-card { min-width: 0; position: relative; display: grid; grid-template-rows: auto auto auto auto auto 1fr; gap: .35rem; align-content: start; border-radius: .35rem; background: rgba(0,0,0,.22); padding: .55rem; outline: 1px solid rgba(255,255,255,.08); overflow: hidden; cursor: pointer; }
    .crop-card:has(input[type="checkbox"]:checked) { outline: 2px solid #38bdf8; background: rgba(56,189,248,.12); }
    .crop-card input[type="checkbox"] { position: absolute; top: .55rem; right: .55rem; z-index: 2; width: 1.25rem; height: 1.25rem; margin: 0; accent-color: #38bdf8; }
    .crop-card input[type="checkbox"]:disabled { opacity: .45; cursor: not-allowed; }
    .crop-card img { width: 100%; aspect-ratio: 1 / 1; object-fit: cover; border-radius: .25rem; background: #18181b; }
    .crop-card strong { min-width: 0; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .crop-card span, .crop-card small, .crop-card a { min-width: 0; max-width: 100%; overflow-wrap: anywhere; }
    .crop-card a { color: #bfdbfe; }
    .small-action { align-self: end; width: 100%; min-width: 0; padding: .42rem .45rem; font-size: .76rem; line-height: 1.15; white-space: normal; overflow-wrap: anywhere; }
    .enroll-form { display: grid; gap: .65rem; margin-top: .9rem; }
    input { width: 100%; margin-top: .25rem; border: 1px solid rgba(255,255,255,.16); border-radius: .25rem; background: #18181b; color: #fff; padding: .5rem; }
    button { border: 0; border-radius: .25rem; background: rgba(96,165,250,.18); color: #dbeafe; padding: .55rem .7rem; cursor: pointer; }
    button.primary-action { background: rgba(16,185,129,.28); color: #ecfdf5; outline: 1px solid rgba(52,211,153,.35); font-weight: 700; }
    button.primary-action:hover { background: rgba(16,185,129,.4); }
    button:hover { background: rgba(96,165,250,.28); }
    .empty-crop { color: #a1a1aa; border-radius: .35rem; background: rgba(255,255,255,.04); padding: 1rem; }
    .merge-panel { border-radius: .35rem; background: rgba(255,255,255,.035); padding: .65rem; outline: 1px solid rgba(255,255,255,.08); }
    .merge-panel summary { cursor: pointer; color: #bfdbfe; font-weight: 700; }
    .action-status { display: none; border-radius: .35rem; padding: .65rem .75rem; font-size: .9rem; }
    .action-status.is-visible { display: block; }
    .action-status.ok { background: rgba(16,185,129,.14); color: #d1fae5; outline: 1px solid rgba(52,211,153,.25); }
    .action-status.warn { background: rgba(251,191,36,.14); color: #fef3c7; outline: 1px solid rgba(251,191,36,.25); }
    .action-status.err { background: rgba(244,63,94,.14); color: #ffe4e6; outline: 1px solid rgba(244,63,94,.25); }
    .confidence-panel { display: grid; gap: .45rem; margin-top: 1rem; border-radius: .35rem; background: rgba(16,185,129,.08); padding: .75rem; outline: 1px solid rgba(52,211,153,.18); }
    .confidence-panel div { display: flex; align-items: baseline; gap: .55rem; }
    .confidence-panel strong { color: #d1fae5; font-size: 1.65rem; line-height: 1; }
    .confidence-panel span { color: #a7f3d0; font-size: .82rem; text-transform: uppercase; font-weight: 700; }
    .confidence-panel p { margin: 0; color: #d4d4d8; font-size: .85rem; }
    .confidence-panel progress { width: 100%; height: .65rem; accent-color: #34d399; }
    .accepted-panel { margin-top: 1rem; border-radius: .35rem; background: rgba(255,255,255,.035); padding: .75rem; outline: 1px solid rgba(255,255,255,.08); }
    .accepted-panel summary { cursor: pointer; color: #dbeafe; font-weight: 700; }
    .accepted-list { display: grid; gap: .35rem; margin-top: .75rem; }
    .accepted-row { display: grid; grid-template-columns: auto minmax(8rem, 1fr) minmax(6rem, 1fr); gap: .5rem; align-items: center; border-radius: .25rem; background: rgba(0,0,0,.18); padding: .45rem; }
    .accepted-row:has(input[type="checkbox"]:checked) { outline: 2px solid #38bdf8; background: rgba(56,189,248,.12); }
    .accepted-row input { margin: 0; width: auto; }
    .accepted-row a { color: #bfdbfe; overflow-wrap: anywhere; }
    .accepted-row small { overflow-wrap: anywhere; }
    .gallery-panel { margin-top: 1rem; border-radius: .35rem; background: rgba(14,165,233,.055); padding: .75rem; outline: 1px solid rgba(125,211,252,.14); }
    .gallery-panel summary { cursor: pointer; color: #bae6fd; font-weight: 800; }
    .gallery-upload-form { display: grid; grid-template-columns: minmax(11rem, 1fr) minmax(13rem, 1.3fr) auto; gap: .65rem; align-items: end; margin-top: .85rem; }
    .gallery-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(112px, 1fr)); gap: .65rem; margin-top: .85rem; }
    .gallery-thumb { position: relative; display: block; overflow: hidden; border-radius: .35rem; background: rgba(0,0,0,.25); outline: 1px solid rgba(255,255,255,.08); color: #e0f2fe; text-decoration: none; }
    .gallery-thumb img { display: block; width: 100%; aspect-ratio: 3 / 4; object-fit: cover; background: #18181b; }
    .gallery-thumb span { position: absolute; left: 0; right: 0; bottom: 0; overflow: hidden; padding: .55rem .5rem .45rem; background: linear-gradient(0deg, rgba(0,0,0,.82), rgba(0,0,0,0)); color: #fff; font-size: .74rem; font-weight: 800; text-overflow: ellipsis; white-space: nowrap; }
    .recommendation-groups { display: grid; gap: 1rem; margin-top: .9rem; }
    .recommendation-panel { margin-top: 1rem; border-radius: .35rem; background: rgba(255,255,255,.025); padding: .75rem; outline: 1px solid rgba(255,255,255,.08); }
    .recommendation-panel summary { cursor: pointer; color: #dbeafe; font-weight: 800; }
    .video-recommendation-group { display: grid; gap: .55rem; }
    .video-recommendation-group h4 { margin: 0; color: #f4f4f5; font-size: .98rem; overflow-wrap: anywhere; }
    .video-recommendation-group h4 span { color: #a1a1aa; font-size: .78rem; font-weight: 500; }
    .video-summary { display: flex; flex-wrap: wrap; align-items: center; gap: .4rem; margin-top: .65rem; color: #d4d4d8; font-size: .85rem; }
    .video-summary strong { margin-right: .2rem; color: #a7f3d0; }
    .video-summary span { border-radius: .25rem; background: rgba(255,255,255,.06); padding: .25rem .45rem; color: #e4e4e7; }
    .scan-coverage { margin-top: .65rem; border-radius: .35rem; background: rgba(255,255,255,.035); padding: .55rem .65rem; outline: 1px solid rgba(255,255,255,.08); }
    .scan-coverage summary { cursor: pointer; color: #bfdbfe; font-weight: 700; font-size: .85rem; }
    .scan-coverage div { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .55rem; }
    .scan-coverage span { border-radius: .25rem; padding: .28rem .45rem; font-size: .76rem; color: #d4d4d8; background: rgba(255,255,255,.05); }
    .scan-coverage span.has-crops { color: #d1fae5; background: rgba(16,185,129,.1); }
    .scan-coverage span.no-crops { color: #fecaca; background: rgba(244,63,94,.09); }
    .scan-coverage strong { color: #f4f4f5; }
    .video-match-panel { margin-top: 1rem; border-radius: .35rem; background: rgba(255,255,255,.03); padding: .75rem; outline: 1px solid rgba(255,255,255,.08); }
    .video-match-panel summary { cursor: pointer; color: #dbeafe; font-weight: 800; }
    .library-awareness-panel { border-radius: .35rem; background: rgba(255,255,255,.025); padding: .55rem; outline: 1px solid rgba(255,255,255,.06); }
    .library-awareness-panel summary { color: #a7f3d0; }
    .library-awareness-panel .video-match-list { margin-top: .55rem; }
    .video-match-actions { display: flex; flex-wrap: wrap; gap: .45rem; margin: .65rem 0; }
    .video-match-columns { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(28rem, 100%), 1fr)); gap: .85rem; }
    .video-match-columns section { min-width: 0; }
    .video-match-columns h4 { margin: .2rem 0 .5rem; font-size: .95rem; }
    .video-match-list { display: grid; gap: .45rem; }
    .video-match-row { display: grid; grid-template-columns: minmax(7rem, 9rem) minmax(0, 1fr); gap: .6rem; align-items: center; border-radius: .35rem; background: rgba(0,0,0,.2); padding: .5rem; outline: 1px solid rgba(255,255,255,.06); }
    .match-previews { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .25rem; }
    .match-previews a { display: block; min-width: 0; }
    .match-previews img, .video-match-row .empty-mini { width: 100%; aspect-ratio: 1 / 1; border-radius: .25rem; object-fit: cover; background: #18181b; }
    .match-copy { min-width: 0; }
    .video-match-row strong, .video-match-row span, .video-match-row small { display: block; min-width: 0; overflow-wrap: anywhere; }
    .video-match-row span { color: #a7f3d0; font-weight: 700; }
    .match-actions { grid-column: 1 / -1; display: flex; flex-wrap: wrap; gap: .35rem; justify-content: flex-start; }
    @media (max-width: 520px) {
      .enroll-head { flex-direction: column; }
      .model-avatar { flex-basis: 4rem; width: 4rem; height: 5.1rem; }
      .gallery-upload-form { grid-template-columns: 1fr; }
      .video-match-row { grid-template-columns: 1fr; }
      .match-previews { max-width: 12rem; }
    }
    """


def enrollment_page_script() -> str:
    return """
    async function postJson(url, payload) {
      const response = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
      const text = await response.text();
      let data = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch (error) {
        throw new Error(text || response.statusText || error.message);
      }
      if (!response.ok) throw new Error(data.error || response.statusText);
      return data;
    }
    async function postForm(url, form) {
      const response = await fetch(url, {method: 'POST', body: new FormData(form)});
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || response.statusText);
      return data;
    }
    function setCardStatus(card, message, kind = 'ok') {
      const status = card.querySelector('.action-status');
      if (!status) return;
      status.className = 'action-status is-visible ' + kind;
      status.textContent = message;
      status.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    function setBusy(button, buttons, label) {
      button.dataset.originalText = button.dataset.originalText || button.textContent;
      button.textContent = label;
      buttons.forEach(item => item.disabled = true);
    }
    function clearBusy(button, buttons) {
      if (button.dataset.originalText) button.textContent = button.dataset.originalText;
      buttons.forEach(item => item.disabled = false);
    }
    function reloadAfterRefresh(result, delayMs = 2500) {
      const delay = result?.refresh_deferred ? Math.max(delayMs, 12000) : delayMs;
      setTimeout(() => location.reload(), delay);
    }
    function goToEnrolledAfterRefresh(result, delayMs = 2500) {
      const delay = result?.refresh_deferred ? Math.max(delayMs, 12000) : delayMs;
      setTimeout(() => {
        window.location.href = '/enrolled';
      }, delay);
    }
    function persistCardStatus(card, message, kind = 'ok') {
      const performer = card?.dataset.performer || card?.querySelector('[name=performer_name]')?.value || '';
      if (!performer) return;
      sessionStorage.setItem('faceOrganizerStatus:' + performer, JSON.stringify({message, kind}));
    }
    document.querySelectorAll('.enroll-card').forEach((card) => {
      const performer = card.dataset.performer || card.querySelector('[name=performer_name]')?.value || '';
      const saved = performer ? sessionStorage.getItem('faceOrganizerStatus:' + performer) : '';
      if (!saved) return;
      sessionStorage.removeItem('faceOrganizerStatus:' + performer);
      try {
        const status = JSON.parse(saved);
        setCardStatus(card, status.message || '', status.kind || 'ok');
        const collapse = card.querySelector('.model-card-collapse');
        if (collapse) collapse.open = true;
      } catch (_) {}
    });
    document.querySelectorAll('.page-expand-all').forEach((button) => {
      button.addEventListener('click', () => {
        document.querySelectorAll('.model-card-collapse').forEach((collapse) => { collapse.open = true; });
      });
    });
    document.querySelectorAll('.page-collapse-all').forEach((button) => {
      button.addEventListener('click', () => {
        document.querySelectorAll('.model-card-collapse').forEach((collapse) => { collapse.open = false; });
      });
    });
    document.querySelectorAll('.page-rescan-all-models').forEach((button) => {
      button.addEventListener('click', async () => {
        try {
          const buttons = [...document.querySelectorAll('button')];
          setBusy(button, buttons, 'Rescanning all models...');
          const result = await postJson('/api/enrollment/generate-candidates', {all_models: true});
          const summary = result.summary || {};
          button.textContent = 'Rescan complete: ' + (summary.groups_generated_this_run ?? '?') + ' model(s)';
          reloadAfterRefresh(result, 1200);
        } catch (error) {
          button.textContent = 'NEEDS_FIX: ' + error.message;
          button.disabled = false;
        }
      });
    });
    document.addEventListener('click', (event) => {
      const card = event.target.closest('.crop-card');
      if (!card || event.target.closest('a, button, input')) return;
      const input = card.querySelector('input[type="checkbox"]:not(:disabled)');
      if (!input) return;
      event.preventDefault();
      input.checked = !input.checked;
      input.dispatchEvent(new Event('change', {bubbles: true}));
    });
    document.querySelectorAll('button[data-action="merge-creator"]').forEach((button) => {
      button.addEventListener('click', async (event) => {
        event.preventDefault();
        event.stopPropagation();
        const form = button.closest('form');
        const card = button.closest('.enroll-card');
        const buttons = [...(card?.querySelectorAll('button[data-action]') || [])];
        try {
          if (!form || !card) throw new Error('Merge form not found on this card');
          const payload = {
            source_name: form.querySelector('[name=merge_source]')?.value?.trim() || '',
            target_name: form.querySelector('[name=merge_target]')?.value?.trim() || '',
            confirmation: form.querySelector('[name=merge_confirmation]')?.value?.trim() || '',
            confirmed_by: 'Britton'
          };
          if (!payload.source_name || !payload.target_name || !payload.confirmation) {
            throw new Error('Fill duplicate/source, correct creator, and confirmation before merging.');
          }
          setCardStatus(card, 'Merging ' + payload.source_name + ' into ' + payload.target_name + '...', 'warn');
          setBusy(button, buttons, 'Merging...');
          const result = await postJson('/api/enrollment/merge-creator', payload);
          setCardStatus(card, 'Merged ' + payload.source_name + ' into ' + payload.target_name + '. Refreshing the queue...', 'ok');
          card.style.opacity = '0.55';
          card.style.pointerEvents = 'none';
          reloadAfterRefresh(result, 700);
        } catch (error) {
          clearBusy(button, buttons);
          setCardStatus(card, 'NEEDS_FIX: ' + error.message, 'err');
        }
      });
    });
    document.addEventListener('click', async (event) => {
      const button = event.target.closest('button[data-action]');
      if (!button) return;
      if (button.dataset.action === 'merge-creator') return;
      const form = button.closest('form');
      const card = button.closest('.enroll-card');
      const performer = form?.querySelector('[name=performer_name]')?.value || button.dataset.performer || card?.dataset.performer || '';
      const selected = [...(card?.querySelectorAll('input[name=crop]:checked') || [])].map(input => input.value);
      const buttons = [...(card?.querySelectorAll('button[data-action]') || [])];
      try {
        if (button.dataset.action === 'gallery-upload') {
          const uploadForm = button.closest('form');
          const fileInput = uploadForm?.querySelector('input[type=file]');
          if (!uploadForm || !fileInput?.files?.length) {
            setCardStatus(card, 'Select at least one gallery picture first.', 'warn');
            return;
          }
          setCardStatus(card, 'Uploading ' + fileInput.files.length + ' gallery picture(s)...', 'warn');
          setBusy(button, buttons, 'Uploading...');
          const result = await postForm('/api/gallery/upload', uploadForm);
          setCardStatus(card, 'Uploaded ' + result.saved_count + ' picture(s). Refreshing...', 'ok');
          setTimeout(() => location.reload(), 900);
        } else if (button.dataset.action === 'select-recommendations' || button.dataset.action === 'clear-recommendations') {
          const checked = button.dataset.action === 'select-recommendations';
          const boxes = [...(card?.querySelectorAll('input[name=crop]:not(:disabled)') || [])];
          boxes.forEach(input => input.checked = checked);
          setCardStatus(card, (checked ? 'Selected ' : 'Cleared ') + boxes.length + ' recommendation(s).', checked ? 'ok' : 'warn');
          return;
        } else if (button.dataset.action === 'select-accepted' || button.dataset.action === 'clear-accepted') {
          const checked = button.dataset.action === 'select-accepted';
          const boxes = [...(card?.querySelectorAll('input[name=accepted_sample]') || [])];
          boxes.forEach(input => input.checked = checked);
          setCardStatus(card, (checked ? 'Selected ' : 'Cleared ') + boxes.length + ' accepted screen(s).', checked ? 'ok' : 'warn');
          return;
        } else if (button.dataset.action === 'enroll-existing' || button.dataset.action === 'enroll-new' || button.dataset.action === 'enrolled-accept') {
          if (!selected.length) {
            setCardStatus(card, 'Select at least one recommendation first.', 'warn');
            return;
          }
          const payload = {
            performer_name: performer,
            confirmation: form.querySelector('[name=confirmation]').value || performer,
            crop_paths: selected,
            add_to_existing: button.dataset.action === 'enroll-existing' || button.dataset.action === 'enrolled-accept',
            create_new: button.dataset.action === 'enroll-new',
            confirmed_by: 'Britton'
          };
          setCardStatus(card, 'Accepting ' + selected.length + ' selected recommendation(s)...', 'warn');
          setBusy(button, buttons, 'Accepting...');
          const result = await postJson('/api/enrollment/enroll', payload);
          const added = (result.embedding_row_indexes_added || []).length || result.would_enroll || 0;
          const skipped = (result.skipped_crops || []).length || 0;
          const message = added === 0 && skipped
            ? 'Skipped ' + skipped + ' weak recommendation(s); hidden from future recommendations. Refreshing...'
            : skipped
            ? 'Accepted ' + added + ' recommendation(s); skipped ' + skipped + ' weak crop(s). Refreshing...'
            : 'Accepted ' + added + ' recommendation(s). Refreshing...';
          setCardStatus(card, message, skipped ? 'warn' : 'ok');
          selected.forEach((path) => {
            const input = card.querySelector('input[name=crop][value="' + CSS.escape(path) + '"]');
            const cropCard = input?.closest('.crop-card');
            if (cropCard) {
              cropCard.style.opacity = '0.45';
              cropCard.style.pointerEvents = 'none';
            }
          });
          goToEnrolledAfterRefresh(result, 1700);
        } else if (button.dataset.action === 'remove-accepted') {
          const samples = [...card.querySelectorAll('input[name=accepted_sample]:checked')].map(input => input.value);
          if (!samples.length) {
            setCardStatus(card, 'Select at least one accepted screen first.', 'warn');
            return;
          }
          setCardStatus(card, 'Removing ' + samples.length + ' accepted screen(s)...', 'warn');
          setBusy(button, buttons, 'Removing...');
          const result = await postJson('/api/enrolled/remove-sample', {performer_name: performer, sample_paths: samples});
          setCardStatus(card, 'Removed ' + ((result.removed_samples || []).length || 0) + ' accepted screen(s).', 'ok');
          setTimeout(() => location.reload(), 800);
        } else if (button.dataset.action === 'reject') {
          if (!selected.length) {
            setCardStatus(card, 'Select at least one recommendation first.', 'warn');
            return;
          }
          setCardStatus(card, 'Rejecting ' + selected.length + ' selected recommendation(s)...', 'warn');
          setBusy(button, buttons, 'Rejecting...');
          await postJson('/api/enrollment/reject-crop', {performer_name: performer, crop_paths: selected});
          setCardStatus(card, 'Rejected ' + selected.length + ' recommendation(s). Refreshing...', 'ok');
          selected.forEach((path) => {
            const input = card.querySelector('input[name=crop][value="' + CSS.escape(path) + '"]');
            const cropCard = input?.closest('.crop-card');
            if (cropCard) {
              cropCard.style.opacity = '0.35';
              cropCard.style.pointerEvents = 'none';
            }
          });
          setTimeout(() => location.reload(), 1700);
        } else if (button.dataset.action === 'more') {
          setCardStatus(card, 'Rescanning all videos for ' + performer + '. This can take 1-3 minutes...', 'warn');
          setBusy(button, buttons, 'Rescanning...');
          const result = await postJson('/api/enrollment/generate-candidates', {performer_name: performer});
          const summary = result.summary || {};
          setCardStatus(card, 'Rescan complete: ' + (summary.candidate_crops_generated ?? '?') + ' total crops saved across this model.', 'ok');
          location.reload();
        } else if (button.dataset.action === 'missing-videos') {
          setCardStatus(card, 'Scanning only missing/new linked videos for ' + performer + '...', 'warn');
          setBusy(button, buttons, 'Scanning missing/new...');
          const result = await postJson('/api/enrollment/generate-candidates', {performer_name: performer, missing_only: true});
          const summary = result.summary || {};
          setCardStatus(card, 'Missing/new scan complete: ' + (summary.candidate_crops_generated ?? '?') + ' total crops now saved. Refreshing...', 'ok');
          location.reload();
        } else if (button.dataset.action === 'smart-accept') {
          const confirmation = form.querySelector('[name=confirmation]')?.value || performer;
          setCardStatus(card, 'Smart selecting the optimal screens for ' + performer + '...', 'warn');
          setBusy(button, buttons, 'Smart accepting...');
          const result = await postJson('/api/enrollment/smart-accept', {
            performer_name: performer,
            confirmation,
            confirmed_by: 'Britton',
            target_count: 5
          });
          const added = (result.enrollment || {}).embedding_row_indexes_added?.length || 0;
          const picked = (result.selected_crops || []).length || 0;
          const skipped = ((result.enrollment || {}).skipped_crops || []).length || 0;
          const message = 'Smart accept picked ' + picked + ' screen(s), enrolled ' + added + ', skipped ' + skipped + ', removed ' + ((result.enrollment || {}).removed_recommendations || 0) + ' stale recommendation(s). Refreshing...';
          setCardStatus(card, message, skipped ? 'warn' : 'ok');
          persistCardStatus(card, message, skipped ? 'warn' : 'ok');
          goToEnrolledAfterRefresh(result, 2500);
        } else if (button.dataset.action === 'scan-library-matches') {
          setCardStatus(card, 'Running face-rec scan on linked videos for ' + performer + '. This can take a few minutes...', 'warn');
          setBusy(button, buttons, 'Scanning...');
          const result = await postJson('/api/enrolled/scan-library-matches', {performer_name: performer, limit: 15});
          const remaining = Number(result.remaining_candidates || 0);
          const candidateNote = remaining > 0 ? ', ' + remaining + ' queued candidate(s) remain for another bounded pass' : '';
          const message = 'Face-rec scan complete: ' + result.scanned + '/' + (result.candidate_videos || result.scanned) + ' candidate video(s) scanned, ' + result.auto_matches + ' strong match(es), ' + result.pending_matches + ' review match(es), ' + result.unknown_matches + ' not matched' + candidateNote + '. Refreshing...';
          setCardStatus(card, message, 'ok');
          persistCardStatus(card, message, 'ok');
          setTimeout(() => location.reload(), 3000);
        } else if (button.dataset.action === 'video-match-accept' || button.dataset.action === 'video-match-reject') {
          const decision = button.dataset.action === 'video-match-accept' ? 'accepted' : 'rejected';
          setCardStatus(card, (decision === 'accepted' ? 'Confirming' : 'Denying') + ' video match...', 'warn');
          setBusy(button, buttons, decision === 'accepted' ? 'Confirming...' : 'Denying...');
          const result = await postJson('/api/enrolled/video-match-decision', {
            performer_name: button.dataset.performer || performer,
            performer_id: button.dataset.performerId || '',
            meta_path: button.dataset.meta || '',
            decision,
            visual_confirmed: decision === 'accepted',
            confirmed_by: 'Britton'
          });
          setCardStatus(card, 'Video match ' + decision + '. Refreshing...', 'ok');
          reloadAfterRefresh(result, 1200);
        } else if (button.dataset.action === 'video-mark-faceless') {
          setCardStatus(card, 'Marking video as faceless...', 'warn');
          setBusy(button, buttons, 'Marking...');
          await postJson('/api/enrolled/video-faceless', {
            performer_name: button.dataset.performer || performer,
            meta_path: button.dataset.meta || '',
            confirmed_by: 'Britton'
          });
          setCardStatus(card, 'Video marked faceless. Refreshing...', 'ok');
          setTimeout(() => location.reload(), 900);
        } else if (button.dataset.action === 'video-deep-scan') {
          setCardStatus(card, 'Deep rescanning one selected video. This is bounded to one file...', 'warn');
          setBusy(button, buttons, 'Rescanning...');
          const result = await postJson('/api/enrolled/video-deep-scan', {
            performer_name: button.dataset.performer || performer,
            performer_id: button.dataset.performerId || '',
            meta_path: button.dataset.meta || '',
            video_path: button.dataset.video || '',
            frame_count: 48,
            confirmed_by: 'Britton'
          });
          const label = button.dataset.performer || performer || 'selected model';
          const message = 'Deep scan complete for ' + (result.video_path || 'selected video') + ': ' + result.frames_analyzed + ' frames, ' + result.faces_detected + ' faces, ' + result.supporting_faces + ' supporting ' + label + ' face(s), similarity ' + Math.round((result.similarity || 0) * 100) + '%. Refreshing...';
          setCardStatus(card, message, 'ok');
          persistCardStatus(card, message, 'ok');
          setTimeout(() => location.reload(), 4000);
        } else if (button.dataset.action === 'manual') {
          const selectedBox = card.querySelector('input[name=crop]:checked') || card.querySelector('input[name=crop]');
          const params = new URLSearchParams({ performer, still_path: selectedBox?.dataset.still || '' });
          if (selectedBox?.dataset.video) params.set('source_video', selectedBox.dataset.video);
          if (selectedBox?.dataset.timestamp) params.set('timestamp', selectedBox.dataset.timestamp);
          window.open('manual_crop.html?' + params.toString(), '_blank', 'noopener');
        } else if (button.dataset.action === 'manual-one') {
          const sourceCard = button.closest('.enroll-card');
          const name = sourceCard?.querySelector('[name=performer_name]')?.value || performer || '';
          const params = new URLSearchParams({ performer: name, still_path: button.dataset.still || '' });
          if (button.dataset.video) params.set('source_video', button.dataset.video);
          if (button.dataset.timestamp) params.set('timestamp', button.dataset.timestamp);
          window.open('manual_crop.html?' + params.toString(), '_blank', 'noopener');
        } else if (button.dataset.action === 'merge-creator') {
          if (!form || !card) throw new Error('Merge form not found on this card');
          const payload = {
            source_name: form.querySelector('[name=merge_source]')?.value?.trim() || '',
            target_name: form.querySelector('[name=merge_target]')?.value?.trim() || '',
            confirmation: form.querySelector('[name=merge_confirmation]')?.value?.trim() || '',
            confirmed_by: 'Britton'
          };
          if (!payload.source_name || !payload.target_name || !payload.confirmation) {
            throw new Error('Fill duplicate/source, correct creator, and confirmation before merging.');
          }
          setCardStatus(card, 'Merging ' + payload.source_name + ' into ' + payload.target_name + '...', 'warn');
          setBusy(button, buttons, 'Merging...');
          const result = await postJson('/api/enrollment/merge-creator', payload);
          setCardStatus(card, 'Merged ' + payload.source_name + ' into ' + payload.target_name + '. Refreshing the queue...', 'ok');
          card.style.opacity = '0.55';
          card.style.pointerEvents = 'none';
          reloadAfterRefresh(result, 700);
        } else if (button.dataset.action === 'faceless') {
          const confirmation = form.querySelector('[name=confirmation]')?.value || performer;
          setCardStatus(card, 'Marking ' + performer + ' as faceless...', 'warn');
          setBusy(button, buttons, 'Marking...');
          const result = await postJson('/api/enrollment/mark-faceless', {
            performer_name: performer,
            confirmation,
            confirmed_by: 'Britton'
          });
          setCardStatus(card, 'Marked ' + result.performer_name + ' as faceless. Refreshing the queue...', 'ok');
          card.style.opacity = '0.55';
          card.style.pointerEvents = 'none';
          reloadAfterRefresh(result, 800);
        } else {
          alert(button.textContent + ' recorded for review.');
        }
      } catch (error) {
        clearBusy(button, buttons);
        setCardStatus(card, 'NEEDS_FIX: ' + error.message, 'err');
      }
    });
    """


def generate_enrollment_queue_page(
    config: OrganizerConfig,
    payload: dict[str, Any] | None = None,
    *,
    refresh_stale: bool = True,
) -> dict[str, Any]:
    if refresh_stale and payload is None:
        refresh_summary = refresh_stale_enrolled_recommendations(
            config,
            only_unenrolled=True,
            max_groups=6,
        )
        if refresh_summary.get("refreshed_count"):
            logging.info(
                "Auto-refreshed stale enrollment recommendations for: %s",
                ", ".join(refresh_summary.get("refreshed_groups") or []),
            )
    payload = payload or build_enrollment_groups(config)
    visible_groups = [
        group
        for group in payload.get("groups", [])
        if not group.get("embedding_rows") and str(group.get("status") or "") != "faceless performer"
    ]
    payload = {
        **payload,
        "groups": visible_groups,
        "summary": {
            "groups_found": len(visible_groups),
            "groups_missing_embeddings": sum(1 for group in visible_groups if not group.get("embedding_rows")),
            "candidate_crops": sum(int(group.get("candidate_face_crops") or 0) for group in visible_groups),
            "blocked_groups": sum(1 for group in visible_groups if group.get("blocked_reason")),
        },
    }
    out_path = config.report_path.with_name("face_enrollment_queue.html")
    summary = payload.get("summary") or {}
    rows = "".join(render_enrollment_group(group) for group in payload.get("groups", []))
    stats = "".join(
        f"<span>{html.escape(str(key).replace('_', ' '))}: {html.escape(str(value))}</span>"
        for key, value in summary.items()
    )
    html_payload = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Face Enrollment Queue</title>
  <style>{enrollment_page_css()}</style>
</head>
<body>
  <header>
    <p class="muted">Media Face Organizer v1</p>
    <h1>Face Enrollment Queue</h1>
    <p class="muted">Generated {html.escape(utc_now())} from {html.escape(str(config.source_dir))}</p>
    {report_nav_html("Face Enrollment Queue", out_path)}
    <div class="summary">{stats}</div>
    {render_page_collapse_controls()}
  </header>
  <main class="grid">{rows or '<div class="empty-crop">No enrollment groups found.</div>'}</main>
  <script>{enrollment_page_script()}</script>
</body>
</html>
"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_payload, encoding="utf-8")
    json_dump(out_path.with_suffix(".json"), payload)
    generate_manual_crop_page(config)
    logging.info("Wrote face enrollment queue: %s", out_path)
    return payload


def known_face_sample_paths(config: OrganizerConfig, performer_id: str, known_record: dict[str, Any] | None = None) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()

    def normalize_sample_path(value: Any) -> str:
        raw = str(value or "")
        if not raw:
            return ""
        path = Path(raw)
        if not path.is_absolute():
            path = path.resolve()
        return str(path)

    removed = {normalize_sample_path(item) for item in (known_record or {}).get("removed_face_samples", []) or []}
    for event in (known_record or {}).get("audit_events", []) or []:
        if isinstance(event, dict) and event.get("event") == "enrolled_sample_removed":
            removed.update(normalize_sample_path(item) for item in event.get("sample_paths") or [])
    for item in (known_record or {}).get("enrolled_face_samples", []) or []:
        normalized = normalize_sample_path(item)
        identity = normalized_sample_identity(normalized)
        if normalized and normalized not in removed and identity not in seen:
            paths.append(normalized)
            seen.add(identity)
    face_dir = (config.db_dir / "faces" / performer_id).resolve()
    if face_dir.exists():
        for path in sorted(face_dir.glob("*")):
            normalized = str(path.resolve())
            identity = normalized_sample_identity(normalized)
            if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} and normalized not in removed and identity not in seen:
                paths.append(normalized)
                seen.add(identity)
    return paths


def known_face_sample_records(config: OrganizerConfig, performer_id: str, known_record: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in (known_record or {}).get("enrolled_face_sample_records", []) or []:
        if not isinstance(item, dict):
            continue
        sample_path = str(item.get("sample_path") or "")
        if sample_path and not Path(sample_path).is_absolute():
            sample_path = str(Path(sample_path).resolve())
        if not sample_path or sample_path in seen:
            continue
        seen.add(sample_path)
        normalized = dict(item)
        normalized["sample_path"] = sample_path
        records.append(normalized)
    for path_text in known_face_sample_paths(config, performer_id, known_record):
        if path_text in seen:
            continue
        seen.add(path_text)
        records.append({"sample_path": path_text})
    return records


def accepted_source_crop_paths(known_record: dict[str, Any] | None) -> set[str]:
    paths: set[str] = set()
    for item in (known_record or {}).get("enrolled_face_sample_records", []) or []:
        if isinstance(item, dict) and item.get("source_crop"):
            paths.add(str(item.get("source_crop")))
    return paths


def enrolled_confidence_estimate(group: dict[str, Any]) -> dict[str, Any]:
    samples = group.get("enrolled_sample_records") or []
    sample_count = len(samples)
    embedding_count = len(group.get("embedding_rows") or [])
    source_videos = {
        str(item.get("source_video") or "")
        for item in samples
        if isinstance(item, dict) and item.get("source_video")
    }
    current_video_count = int(group.get("candidate_videos") or 0)
    target_samples = min(
        ENROLLMENT_CONFIDENCE_MAX_TARGET_SCREENS,
        max(5, ENROLLMENT_CONFIDENCE_BASELINE_SCREENS, min(12, current_video_count or 1)),
    )
    target_videos = max(1, min(8, current_video_count or target_samples))
    coverage_ratio = min(1.0, len(source_videos) / target_videos)
    sample_ratio = min(1.0, sample_count / float(target_samples))
    embedding_ratio = min(1.0, embedding_count / float(target_samples))
    recommendation_scores = [
        float(crop.get("quality_score") or 0)
        for crop in group.get("recommended_crops") or []
        if isinstance(crop, dict)
    ]
    quality_signal = min(1.0, max(recommendation_scores, default=0.72))
    estimate = 0.18 + sample_ratio * 0.34 + embedding_ratio * 0.24 + coverage_ratio * 0.16 + quality_signal * 0.08
    if sample_count <= 1:
        estimate = min(estimate, 0.68)
    elif sample_count < 5:
        estimate = min(estimate, 0.88)
    elif sample_count < target_samples:
        estimate = min(estimate, 0.93)
    return {
        "percent": int(round(max(0.0, min(0.98, estimate)) * 100)),
        "sample_count": sample_count,
        "embedding_count": embedding_count,
        "source_video_count": len(source_videos),
        "current_video_count": current_video_count,
        "target_samples": target_samples,
        "target_videos": target_videos,
        "label": "ready" if sample_count >= target_samples and embedding_count >= target_samples else "improving",
        "why": (
            f"{sample_count}/{target_samples} accepted screens, {embedding_count}/{target_samples} embedding rows, "
            f"{len(source_videos)}/{target_videos} useful source-video coverage"
        ),
    }


def render_enrolled_sample(path_text: str) -> str:
    image_src = display_image_src(path_text)
    return f"""
      <a class="sample-card" href="{html.escape(path_text, quote=True)}" target="_blank" rel="noopener noreferrer">
        <img src="{html.escape(image_src, quote=True)}" alt="Enrolled face sample" loading="lazy" decoding="async">
      </a>
    """


def render_enrolled_sample_row(record: dict[str, Any]) -> str:
    sample_path = str(record.get("sample_path") or "")
    video_name = Path(str(record.get("source_video") or "")).name if record.get("source_video") else "legacy sample"
    timestamp = record.get("source_timestamp")
    detail = video_name
    if timestamp not in (None, ""):
        detail = f"{detail} @ {timestamp}s"
    return f"""
      <label class="accepted-row">
        <input type="checkbox" name="accepted_sample" value="{html.escape(sample_path, quote=True)}">
        <a href="{html.escape(sample_path, quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(Path(sample_path).name or 'sample')}</a>
        <small>{html.escape(detail)}</small>
      </label>
    """


def enrolled_group_header_image(group: dict[str, Any], samples: list[str]) -> str:
    gallery_items = group.get("gallery_items") or []
    image_src = ""
    image_label = str(group.get("name") or "Model image")
    if gallery_items:
        first_gallery = gallery_items[0] if isinstance(gallery_items[0], dict) else {}
        image_src = str(first_gallery.get("url") or first_gallery.get("path") or "")
    if not image_src and samples:
        image_src = display_image_src(str(samples[0]))
    if not image_src:
        return '<div class="model-avatar model-avatar-empty" aria-hidden="true"></div>'
    return f"""
      <a class="model-avatar" href="{html.escape(image_src, quote=True)}" target="_blank" rel="noopener noreferrer">
        <img src="{html.escape(image_src, quote=True)}" alt="{html.escape(image_label, quote=True)}" loading="lazy" decoding="async">
      </a>
    """


def render_recommendations_by_video(crops: list[dict[str, Any]], stills: list[dict[str, Any]]) -> str:
    groups: dict[str, list[str]] = {}
    counts: dict[str, int] = {}
    crop_stills = {str(crop.get("still_path") or "") for crop in crops if isinstance(crop, dict)}
    for crop in crops:
        video_name = str(crop.get("source_video_name") or Path(str(crop.get("source_video") or "")).name or "Unknown video")
        groups.setdefault(video_name, []).append(render_enrollment_crop(crop))
        counts[video_name] = counts.get(video_name, 0) + 1
    for still in stills:
        if str(still.get("still_path") or "") in crop_stills:
            continue
        video_name = str(still.get("source_video_name") or Path(str(still.get("source_video") or "")).name or "Unknown video")
        groups.setdefault(video_name, []).append(render_enrollment_still(still))
        counts[video_name] = counts.get(video_name, 0) + 1
    if not groups:
        return '<div class="empty-crop">No extra recommendations found yet.</div>'
    sections = []
    for video_name in sorted(groups, key=str.lower):
        sections.append(
            f"""
            <section class="video-recommendation-group">
              <h4>{html.escape(video_name)} <span>{counts.get(video_name, 0)} screen(s)</span></h4>
              <div class="crop-grid">{''.join(groups[video_name])}</div>
            </section>
            """
        )
    return "".join(sections)


def render_recommendation_video_summary(group: dict[str, Any]) -> str:
    names = sorted(
        {
            str(crop.get("source_video_name") or Path(str(crop.get("source_video") or "")).name)
            for crop in list(group.get("recommended_crops") or []) + list(group.get("recommended_stills") or [])
            if isinstance(crop, dict)
        },
        key=str.lower,
    )
    total = int(group.get("candidate_videos") or 0)
    if not names:
        return '<p class="video-summary">No source videos represented in current recommendations.</p>'
    chips = "".join(f"<span>{html.escape(name)}</span>" for name in names)
    return f'<div class="video-summary"><strong>{len(names)} of {total} videos represented</strong>{chips}</div>'


def render_scan_coverage(group: dict[str, Any]) -> str:
    rows = []
    for item in group.get("recommendation_scan_summary") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("source_video_name") or Path(str(item.get("source_video") or "")).name or "Unknown video")
        frames = int(item.get("frames_sampled") or 0)
        faces = int(item.get("faces_detected") or 0)
        crops = int(item.get("candidate_crops") or 0)
        cls = "has-crops" if crops else "no-crops"
        rows.append(
            f'<span class="{cls}" title="{html.escape(name, quote=True)}">'
            f'<strong>{html.escape(name)}</strong> {frames} frames / {faces} faces / {crops} usable'
            '</span>'
        )
    if not rows:
        return ""
    return f'<details class="scan-coverage"><summary>Scan coverage by video</summary><div>{"".join(rows)}</div></details>'


def render_video_match_row(match: dict[str, Any], *, allow_actions: bool) -> str:
    confidence = int(match.get("confidence_percent") or round(float(match.get("confidence") or 0) * 100))
    preview_paths = [str(path) for path in match.get("preview_paths") or [] if str(path)]
    meta_path = str(match.get("meta_path") or "")
    video_path = str(match.get("resolved_video_path") or match.get("video_path") or "")
    performer_name = str(match.get("performer_name") or "")
    performer_id = str(match.get("performer_id") or "")
    actions = ""
    if allow_actions:
        actions = (
            '<div class="match-actions">'
            f'<button type="button" data-action="video-match-accept" data-meta="{html.escape(meta_path, quote=True)}" data-performer="{html.escape(performer_name, quote=True)}" data-performer-id="{html.escape(performer_id, quote=True)}">Confirm video</button>'
            f'<button type="button" data-action="video-match-reject" data-meta="{html.escape(meta_path, quote=True)}" data-performer="{html.escape(performer_name, quote=True)}" data-performer-id="{html.escape(performer_id, quote=True)}">Deny</button>'
            f'<button type="button" data-action="video-deep-scan" data-meta="{html.escape(meta_path, quote=True)}" data-video="{html.escape(video_path, quote=True)}" data-performer="{html.escape(performer_name, quote=True)}" data-performer-id="{html.escape(performer_id, quote=True)}">Deep rescan video</button>'
            f'<button type="button" data-action="video-mark-faceless" data-meta="{html.escape(meta_path, quote=True)}" data-performer="{html.escape(performer_name, quote=True)}">Mark faceless video</button>'
            '</div>'
        )
    thumbs = "".join(
        f'<a href="{html.escape(path, quote=True)}" target="_blank" rel="noopener noreferrer"><img src="{html.escape(display_image_src(path), quote=True)}" alt="Video match preview" loading="lazy" decoding="async"></a>'
        for path in preview_paths[:4]
    )
    thumb = f'<div class="match-previews">{thumbs}</div>' if thumbs else '<div class="empty-mini">No preview saved</div>'
    has_face_evidence = bool(match.get("has_face_evidence"))
    if match.get("kind") == "missing_source":
        confidence_text = "Missing source video; stale sidecar only"
    elif match.get("kind") == "metadata_review":
        confidence_text = f"{confidence}% metadata/title match; needs visual review"
    elif match.get("kind") == "accepted_manual":
        confidence_text = f"{confidence}% manually confirmed metadata/title match"
    elif match.get("kind") == "library":
        confidence_text = (
            f"{confidence}% sidecar face evidence in model folder"
            if has_face_evidence
            else "In model folder; metadata/manual evidence only"
        )
    else:
        confidence_text = f"{confidence}% face match confidence" if has_face_evidence else "Needs visual review; metadata only"
    support_text = (
        f"{html.escape(str(match.get('supporting_faces') or 0))} supporting face(s)"
        if has_face_evidence
        else f"no saved {performer_name or 'target model'} face-rec evidence"
    )
    return f"""
      <article class="video-match-row">
        {thumb}
        <div class="match-copy">
          <strong>{html.escape(str(match.get("video_name") or "Unknown video"))}</strong>
          <span>{html.escape(confidence_text)}</span>
          <small>{support_text}</small>
        </div>
        {actions}
      </article>
    """


def render_preview_paths(paths: list[str], *, empty_text: str = "No preview saved") -> str:
    clean_paths = [str(path) for path in paths if str(path)]
    if not clean_paths:
        return f'<div class="empty-mini">{html.escape(empty_text)}</div>'
    thumbs = "".join(
        f'<a href="{html.escape(path, quote=True)}" target="_blank" rel="noopener noreferrer"><img src="{html.escape(display_image_src(path), quote=True)}" alt="Video preview" loading="lazy" decoding="async"></a>'
        for path in clean_paths[:4]
    )
    return f'<div class="match-previews">{thumbs}</div>'


def render_enrolled_video_matches(group: dict[str, Any]) -> str:
    performer_name = str(group.get("name") or "this model")
    library_matches = group.get("library_video_matches") or []
    ledger_rows = ((group.get("source_of_truth_ledger") or {}).get("rows") or [])
    physical_model_rows = [row for row in ledger_rows if isinstance(row, dict) and row.get("model_folder_path")]
    face_rec_model_rows = [row for row in physical_model_rows if row.get("match_evidence_type") == "face_rec"]
    model_row_by_path = {path_key(row.get("model_folder_path") or ""): row for row in physical_model_rows}
    library_match_keys = {
        path_key(match.get("resolved_video_path") or match.get("video_path") or "")
        for match in library_matches
        if isinstance(match, dict)
    }
    unmatched_model_rows = [
        row for key, row in sorted(model_row_by_path.items(), key=lambda item: str(item[1].get("basename") or "").lower())
        if key not in library_match_keys
    ]
    missing_matches = group.get("missing_video_matches") or []
    all_auto_matches = group.get("auto_video_matches") or []
    confirmed_kinds = {"accepted", "accepted_manual"}
    confirmed_matches = [match for match in all_auto_matches if str(match.get("kind") or "") in confirmed_kinds]
    auto_matches = [match for match in all_auto_matches if str(match.get("kind") or "") not in confirmed_kinds]
    pending_matches = group.get("pending_video_matches") or []
    library_rows = "".join(render_video_match_row(match, allow_actions=False) for match in library_matches[:24])
    unmatched_model_html = "".join(
        f"""
        <article class="video-match-row">
          {render_preview_paths(sidecar_preview_paths(str(row.get("sidecar_path") or "")), empty_text="No scan preview saved")}
          <div class="match-copy">
            <strong>{html.escape(str(row.get("basename") or Path(str(row.get("model_folder_path") or "")).name or "Unknown video"))}</strong>
            <span>{html.escape(str(row.get("match_evidence_type") or "unknown").replace("_", " "))}</span>
            <small>{html.escape(", ".join(row.get("sync_mismatch_reasons") or []) or "physical model-folder file")}</small>
          </div>
          <div class="match-actions">
            <button type="button" data-action="video-deep-scan" data-meta="{html.escape(str(row.get("sidecar_path") or ""), quote=True)}" data-video="{html.escape(str(row.get("model_folder_path") or ""), quote=True)}" data-performer="{html.escape(str(group.get("name") or ""), quote=True)}" data-performer-id="{html.escape(str(group.get("known_performer_id") or ""), quote=True)}">Deep rescan video</button>
            <button type="button" data-action="video-mark-faceless" data-meta="{html.escape(str(row.get("sidecar_path") or ""), quote=True)}" data-performer="{html.escape(str(group.get("name") or ""), quote=True)}">Mark faceless video</button>
          </div>
        </article>
        """
        for row in unmatched_model_rows[:24]
    )
    missing_rows = "".join(render_video_match_row(match, allow_actions=False) for match in missing_matches[:24])
    confirmed_rows = "".join(render_video_match_row(match, allow_actions=False) for match in confirmed_matches[:24])
    auto_rows = "".join(render_video_match_row(match, allow_actions=True) for match in auto_matches[:24])
    pending_rows = "".join(render_video_match_row(match, allow_actions=True) for match in pending_matches[:24])
    actionable = len(auto_matches) + len(pending_matches)
    panel_open = " open" if actionable else ""
    return f"""
      <details class="video-match-panel"{panel_open}>
        <summary>Video match review ({actionable} need action, {len(physical_model_rows) or len(library_matches)} physical model-folder files, {len(face_rec_model_rows)} face-rec-supported, {len(missing_matches)} missing source)</summary>
        <p class="exists">SpiritFlix counts visible Jellyfin library videos. This panel counts organizer sidecars and physical files in the model folder, so it can be higher until Jellyfin exposes the same files.</p>
        <div class="video-match-actions">
          <button type="button" data-action="scan-library-matches">Run face-rec scan for this model</button>
        </div>
        <div class="video-match-columns">
          <section>
            <h4>Needs your decision</h4>
            <div class="video-match-list">{pending_rows or '<div class="empty-crop">No questionable matches waiting right now.</div>'}</div>
          </section>
          <section>
            <h4>Confirmed outside-library matches</h4>
            <p class="exists">These were confirmed from scan metadata. They only appear in SpiritFlix under this model when Jellyfin also exposes that video in the library view.</p>
            <div class="video-match-list">{confirmed_rows or '<div class="empty-crop">No confirmed non-library matches recorded yet.</div>'}</div>
          </section>
          <section>
            <h4>New 80%+ matches</h4>
            <div class="video-match-list">{auto_rows or '<div class="empty-crop">No 80%+ auto video matches recorded yet.</div>'}</div>
          </section>
          <section>
            <details class="library-awareness-panel">
              <summary>Already in model folder ({len(physical_model_rows) or len(library_matches)} physical files, {len(library_matches)} with current {html.escape(performer_name)} scan evidence)</summary>
              <p class="exists">This is the physical model-folder count. Rows without {html.escape(performer_name)} face-rec support stay visible here so Organizer and SpiritFlix do not look like they disagree.</p>
              <div class="video-match-list">{library_rows}{unmatched_model_html or ''}</div>
            </details>
          </section>
          <section>
            <details class="library-awareness-panel" {'open' if missing_matches else ''}>
              <summary>Missing source video sidecars ({len(missing_matches)})</summary>
              <p class="exists">These sidecars still exist, but the actual video file is missing or was renamed outside the organizer. They will not appear in SpiritFlix until the video path exists again.</p>
              <div class="video-match-list">{missing_rows or '<div class="empty-crop">No missing source-video sidecars found.</div>'}</div>
            </details>
          </section>
        </div>
      </details>
    """


def render_enrolled_group(group: dict[str, Any]) -> str:
    samples = group.get("enrolled_samples") or []
    sample_records = group.get("enrolled_sample_records") or []
    recommendations = group.get("recommended_crops") or []
    stills = group.get("recommended_stills") or []
    sample_html = "".join(render_enrolled_sample(path) for path in samples)
    sample_rows = "".join(render_enrolled_sample_row(record) for record in sample_records)
    recommendation_html = render_recommendations_by_video(recommendations, stills)
    confidence = group.get("confidence_estimate") or enrolled_confidence_estimate(group)
    confidence_percent = int(confidence.get("percent") or 0)
    recommendations_open = confidence_percent < 90
    target_samples = int(confidence.get("target_samples") or 5)
    ready = len(samples) >= target_samples
    has_embeddings = bool(group.get("embedding_rows"))
    card_state = (
        "ENROLLED - READY"
        if ready and has_embeddings
        else "READY TO FACE-ENROLL"
        if recommendations and not has_embeddings
        else "ENROLLED - NEEDS MORE SCREENS"
        if has_embeddings
        else "USER-CONFIRMED BUT NOT FACE-ENROLLED"
    )
    library_match_count = len(group.get("library_video_matches") or [])
    missing_match_count = len(group.get("missing_video_matches") or [])
    review_match_count = len(group.get("auto_video_matches") or []) + len(group.get("pending_video_matches") or [])
    gallery_count = len(group.get("gallery_items") or [])
    header_image = enrolled_group_header_image(group, samples)
    open_attr = " open" if enrollment_card_should_expand(group, enrolled=True) else ""
    return f"""
      <article class="enroll-card enrolled-card" data-performer="{html.escape(str(group.get("name") or ""), quote=True)}">
        <details class="model-card-collapse"{open_attr}>
          <summary class="enroll-head model-card-summary">
            <div class="model-title">
              {header_image}
              <div>
                <p>{html.escape(card_state)}</p>
                <h2>{html.escape(str(group.get("name") or ""))}</h2>
                <small>{html.escape(str(group.get("known_performer_id") or ""))}</small>
              </div>
            </div>
            <div class="mini-metrics">
              <span>{len(samples)} enrolled screens</span>
              <span>{len(group.get("embedding_rows") or [])} embedding rows</span>
              <span>{library_match_count} model-folder files</span>
              <span>{gallery_count} gallery pics</span>
              <span>{missing_match_count} missing source</span>
              <span>{review_match_count} scan matches</span>
              <span class="collapse-chevron" aria-hidden="true">▸</span>
            </div>
          </summary>
          <div class="enroll-card-body">
        <div class="presence">
          <span>registry: {'yes' if group.get('registry_present') else 'no'}</span>
          <span>model_index: {'yes' if group.get('model_index_present') else 'no'}</span>
          <span>known record: {'yes' if group.get('known_performers_record') else 'no'}</span>
        </div>
        <div class="confidence-panel">
          <div>
            <strong>{html.escape(str(confidence.get("percent") or 0))}%</strong>
            <span>estimated match confidence</span>
          </div>
          <progress value="{html.escape(str(confidence.get("percent") or 0))}" max="100"></progress>
          <p>{html.escape(str(confidence.get("why") or ""))}</p>
        </div>
        <div class="action-status" aria-live="polite"></div>
        {render_gallery_upload_panel(group)}
        {render_enrolled_video_matches(group)}
        <details class="accepted-panel">
          <summary>Accepted screens ({len(samples)})</summary>
          <div class="sample-grid">{sample_html or '<div class="empty-crop">No enrolled screen paths recorded yet.</div>'}</div>
          <div class="accepted-list">{sample_rows}</div>
          <form class="enroll-form accepted-actions" data-performer="{html.escape(str(group.get("name") or ""), quote=True)}">
            <input type="hidden" name="performer_name" value="{html.escape(str(group.get("name") or ""), quote=True)}">
            <div class="button-row">
              <button type="button" data-action="select-accepted">Select all accepted</button>
              <button type="button" data-action="clear-accepted">Clear accepted selection</button>
              <button type="button" data-action="remove-accepted">Remove selected accepted screens</button>
            </div>
          </form>
        </details>
        <details class="recommendation-panel" {'open' if recommendations_open else ''}>
          <summary>Recommended screens from other current videos ({len(recommendations) + len(stills)})</summary>
          <p class="exists">These are useful screens found from current sidecars/videos that are not automatically enrolled. Review and confirm before adding to the DB.</p>
          {render_recommendation_video_summary(group)}
          {render_scan_coverage(group)}
          <div class="recommendation-groups">{recommendation_html}</div>
          <form class="enroll-form enrolled-actions" data-performer="{html.escape(str(group.get("name") or ""), quote=True)}">
            <input type="hidden" name="performer_name" value="{html.escape(str(group.get("name") or ""), quote=True)}">
            <input type="hidden" name="confirmation" value="{html.escape(str(group.get("name") or ""), quote=True)}">
            <div class="button-row">
              <button type="button" data-action="select-recommendations">Select all recommendations</button>
              <button type="button" data-action="clear-recommendations">Clear recommendation selection</button>
              <button type="button" data-action="enrolled-accept">Accept selected recommendations</button>
              <button type="button" data-action="smart-accept">Smart accept optimal</button>
              <button type="button" data-action="reject">Reject selected recommendations</button>
              <button type="button" data-action="more">Scan current videos again</button>
            </div>
          </form>
        </details>
          </div>
        </details>
      </article>
    """


def build_enrolled_groups(config: OrganizerConfig, *, refresh_recommendations: bool = False) -> dict[str, Any]:
    refresh_summary = None
    if refresh_recommendations:
        refresh_summary = refresh_stale_enrolled_recommendations(config)
    payload = build_enrollment_groups(config)
    known = known_db_summary(config.db_dir)
    known_by_id = known.get("by_id", {})
    groups = []
    candidate_workbench_count = 0
    for group in payload.get("groups", []):
        has_enrollment = bool(group.get("embedding_rows"))
        if not has_enrollment:
            candidate_workbench_count += 1
            continue
        performer_id = str(group.get("known_performer_id") or slugify(str(group.get("name") or "")))
        known_record = known_by_id.get(performer_id) or {}
        group = dict(group)
        group["enrolled_samples"] = known_face_sample_paths(config, performer_id, known_record)
        group["enrolled_sample_records"] = known_face_sample_records(config, performer_id, known_record)
        accepted_videos = {
            str(item.get("source_video") or "")
            for item in group["enrolled_sample_records"]
            if isinstance(item, dict) and item.get("source_video")
        }
        if accepted_videos:
            other_video_crops = [
                crop
                for crop in group.get("recommended_crops") or []
                if str(crop.get("source_video") or "") not in accepted_videos
            ]
            other_video_stills = [
                still
                for still in group.get("recommended_stills") or []
                if str(still.get("source_video") or "") not in accepted_videos
            ]
            group["recommended_crops"] = other_video_crops
            group["recommended_stills"] = other_video_stills
        if has_enrollment:
            matches = enrolled_video_matches(config, group)
            group["library_video_matches"] = matches["library"]
            group["missing_video_matches"] = matches["missing"]
            group["auto_video_matches"] = matches["auto"]
            group["pending_video_matches"] = matches["pending"]
        else:
            group["library_video_matches"] = []
            group["missing_video_matches"] = []
            group["auto_video_matches"] = []
            group["pending_video_matches"] = []
        group["confidence_estimate"] = enrolled_confidence_estimate(group)
        group["gallery_items"] = gallery_items_for_model(config, str(group.get("name") or ""), str(group.get("slug") or slugify(str(group.get("name") or ""))))
        group["gallery_count"] = len(group["gallery_items"])
        group["source_of_truth_ledger"] = (
            build_model_video_ledger(
                config,
                str(group.get("name") or ""),
                performer_id,
                generated_group=group,
            )
            if has_enrollment
            else {
                "schema": "media-model-video-ledger/v1",
                "read_only": True,
                "model_label": str(group.get("name") or ""),
                "performer_id": performer_id,
                "count_types": {},
                "rows": [],
                "deferred_until_face_enrolled": True,
            }
        )
        groups.append(group)
    return {
        "schema": "media-face-enrolled-performers/v1",
        "generated_at": utc_now(),
        "source_dir": str(config.source_dir),
        "groups": groups,
        "summary": {
            "enrolled_performers": len(groups),
            "candidate_workbench_groups": candidate_workbench_count,
            "displayed_groups": len(groups),
            "ready_with_target_screens": sum(
                1
                for group in groups
                if len(group.get("enrolled_samples") or []) >= int((group.get("confidence_estimate") or {}).get("target_samples") or 5)
            ),
            "ready_with_five_screens": sum(1 for group in groups if len(group.get("enrolled_samples") or []) >= 5),
            "enrolled_screens": sum(len(group.get("enrolled_samples") or []) for group in groups),
            "live_recommendations": sum(len(group.get("recommended_crops") or []) for group in groups),
            "library_video_matches": sum(len(group.get("library_video_matches") or []) for group in groups),
            "missing_video_match_sources": sum(len(group.get("missing_video_matches") or []) for group in groups),
            "auto_video_matches": sum(len(group.get("auto_video_matches") or []) for group in groups),
            "pending_video_match_questions": sum(len(group.get("pending_video_matches") or []) for group in groups),
            "average_confidence_percent": round(
                sum(int((group.get("confidence_estimate") or {}).get("percent") or 0) for group in groups) / max(1, len(groups))
            ),
            "recommendation_refreshes": int((refresh_summary or {}).get("refreshed_count") or 0),
        },
    }


def generate_enrolled_page(config: OrganizerConfig, *, refresh_recommendations: bool = False) -> dict[str, Any]:
    payload = build_enrolled_groups(config, refresh_recommendations=refresh_recommendations)
    out_path = config.report_path.with_name("face_enrolled_performers.html")
    summary = payload.get("summary") or {}
    stats = "".join(
        f"<span>{html.escape(str(key).replace('_', ' '))}: {html.escape(str(value))}</span>"
        for key, value in summary.items()
    )
    rows = "".join(render_enrolled_group(group) for group in payload.get("groups", []))
    html_payload = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Enrolled Performers</title>
  <style>{enrollment_page_css()}
    h3 {{ margin: 1rem 0 .5rem; }}
    .sample-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: .65rem; margin-top: .75rem; }}
    .sample-card {{ display: block; border-radius: .35rem; background: rgba(0,0,0,.22); outline: 1px solid rgba(255,255,255,.08); padding: .4rem; }}
    .sample-card img {{ display: block; width: 100%; aspect-ratio: 1 / 1; object-fit: cover; border-radius: .25rem; }}
  </style>
</head>
<body>
  <header>
    <p class="muted">Media Face Organizer v1</p>
    <h1>Enrolled</h1>
    <p class="muted">Generated {html.escape(utc_now())} from live registry, model index, sidecars, and known performer DB.</p>
    {report_nav_html("Enrolled", out_path)}
    <div class="summary">{stats}</div>
    {render_page_collapse_controls()}
  </header>
  <main class="grid">{rows or '<div class="empty-crop">No enrolled performers found.</div>'}</main>
  <script>{enrollment_page_script()}</script>
</body>
</html>
"""
    out_path.write_text(html_payload, encoding="utf-8")
    json_dump(out_path.with_suffix(".json"), payload)
    logging.info("Wrote enrolled performers page: %s", out_path)
    return payload


def generate_manual_crop_page(config: OrganizerConfig) -> None:
    out_path = config.report_path.with_name("manual_crop.html")
    html_payload = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Manual Face Crop</title>
  <style>{enrollment_page_css()}
    .tool {{ display: grid; gap: 1rem; }}
    .canvas-wrap {{ overflow: auto; border-radius: .35rem; background: #050505; outline: 1px solid rgba(255,255,255,.1); }}
    canvas {{ display: block; max-width: 100%; height: auto; cursor: crosshair; }}
    .result {{ white-space: pre-wrap; border-radius: .35rem; background: rgba(255,255,255,.05); padding: .75rem; color: #d4d4d8; }}
  </style>
</head>
<body>
  <header>
    <p class="muted">Media Face Organizer v1</p>
    <h1>Manual Face Crop</h1>
    <p class="muted">Draw a rectangle on a local still frame, preview the crop, then save it as candidate evidence.</p>
    {report_nav_html("Face Enrollment Queue", out_path)}
  </header>
  <main class="tool">
    <label>Performer<input id="performer"></label>
    <label>Still frame path or URL<input id="stillPath"></label>
    <div class="button-row"><button id="loadStill" type="button">Load still</button><button id="saveCrop" type="button">Save crop candidate</button></div>
    <div class="canvas-wrap"><canvas id="canvas"></canvas></div>
    <div class="canvas-wrap"><canvas id="preview"></canvas></div>
    <pre id="result" class="result">No crop saved yet.</pre>
  </main>
  <script>
    const params = new URLSearchParams(location.search);
    const performerInput = document.getElementById('performer');
    const stillInput = document.getElementById('stillPath');
    const canvas = document.getElementById('canvas');
    const preview = document.getElementById('preview');
    const result = document.getElementById('result');
    const saveButton = document.getElementById('saveCrop');
    const ctx = canvas.getContext('2d');
    const pctx = preview.getContext('2d');
    const image = new Image();
    let naturalScale = 1;
    let start = null;
    let crop = null;
    performerInput.value = params.get('performer') || '';
    stillInput.value = params.get('still_path') || '';
    image.onload = () => {{
      const maxWidth = Math.min(1100, Math.max(320, document.body.clientWidth - 40));
      naturalScale = image.naturalWidth / Math.min(image.naturalWidth, maxWidth);
      canvas.width = Math.round(image.naturalWidth / naturalScale);
      canvas.height = Math.round(image.naturalHeight / naturalScale);
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
    }};
    function loadStill() {{
      if (!stillInput.value) return;
      result.textContent = 'Loading still frame...';
      image.src = stillInput.value;
    }}
    image.onerror = () => {{
      result.textContent = 'NEEDS_FIX: still frame could not be loaded: ' + stillInput.value;
    }};
    function drawRect(rect) {{
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
      if (!rect) return;
      ctx.strokeStyle = '#67e8f9';
      ctx.lineWidth = 2;
      ctx.strokeRect(rect.x, rect.y, rect.width, rect.height);
      preview.width = Math.max(1, rect.width);
      preview.height = Math.max(1, rect.height);
      pctx.drawImage(canvas, rect.x, rect.y, rect.width, rect.height, 0, 0, rect.width, rect.height);
    }}
    canvas.addEventListener('pointerdown', event => {{
      const bounds = canvas.getBoundingClientRect();
      start = {{ x: event.clientX - bounds.left, y: event.clientY - bounds.top }};
    }});
    canvas.addEventListener('pointermove', event => {{
      if (!start) return;
      const bounds = canvas.getBoundingClientRect();
      const x = event.clientX - bounds.left;
      const y = event.clientY - bounds.top;
      crop = {{ x: Math.min(start.x, x), y: Math.min(start.y, y), width: Math.abs(x - start.x), height: Math.abs(y - start.y) }};
      drawRect(crop);
    }});
    canvas.addEventListener('pointerup', () => {{ start = null; }});
    document.getElementById('loadStill').addEventListener('click', loadStill);
    document.getElementById('saveCrop').addEventListener('click', async () => {{
      if (!crop) {{ result.textContent = 'NEEDS_FIX: draw a crop first.'; return; }}
      const payload = {{
        performer: performerInput.value,
        still_path: stillInput.value,
        source_video: params.get('source_video') || '',
        timestamp: params.get('timestamp') || '',
        crop: {{
          x: Math.round(crop.x * naturalScale),
          y: Math.round(crop.y * naturalScale),
          width: Math.round(crop.width * naturalScale),
          height: Math.round(crop.height * naturalScale)
        }}
      }};
      saveButton.disabled = true;
      saveButton.textContent = 'Saving...';
      result.textContent = 'Saving crop candidate and validating face...';
      result.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      try {{
        const response = await fetch('/api/enrollment/manual-crop', {{ method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(payload) }});
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || response.statusText);
        result.textContent = 'Saved crop candidate.\\n\\n' + JSON.stringify(data, null, 2);
      }} catch (error) {{
        result.textContent = 'NEEDS_FIX: ' + error.message;
      }} finally {{
        saveButton.disabled = false;
        saveButton.textContent = 'Save crop candidate';
      }}
    }});
    if (stillInput.value) loadStill();
  </script>
</body>
</html>
"""
    out_path.write_text(html_payload, encoding="utf-8")


def generate_known_db_audit_page(config: OrganizerConfig) -> dict[str, Any]:
    audit = audit_known_db(config)
    out_path = config.report_path.with_name("known_db_audit.html")
    missing = "".join(
        f'<li>{html.escape(str(item.get("name") or item.get("id") or ""))}: {html.escape(str(item.get("status") or ""))}</li>'
        for item in (audit.get("performers_missing_known_record") or [])[:200]
    )
    missing_rows = "".join(
        f'<li>{html.escape(str(item.get("name") or item.get("id") or ""))}: {html.escape(str(item.get("status") or ""))}</li>'
        for item in (audit.get("known_performers_missing_embedding_rows") or [])[:200]
    )
    html_payload = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Known DB Audit</title>
  <style>{enrollment_page_css()}</style>
</head>
<body>
  <header>
    <p class="muted">Media Face Organizer v1</p>
    <h1>Known DB Audit</h1>
    <p class="muted">Generated {html.escape(str(audit.get("generated_at") or ""))}</p>
    {report_nav_html("Known DB Audit", out_path)}
    <div class="summary">
      <span>registry: {html.escape(str(audit.get("registry_count")))}</span>
      <span>model index: {html.escape(str(audit.get("model_index_count")))}</span>
      <span>known performers: {html.escape(str(audit.get("known_performers_count")))}</span>
      <span>embedding shape: {html.escape(str(audit.get("embedding_shape")))}</span>
    </div>
  </header>
  <main class="grid">
    <article class="enroll-card"><h2>Missing known performer records</h2><ul>{missing or '<li>None.</li>'}</ul></article>
    <article class="enroll-card"><h2>Known records missing embedding rows</h2><ul>{missing_rows or '<li>None.</li>'}</ul></article>
  </main>
</body>
</html>
"""
    out_path.write_text(html_payload, encoding="utf-8")
    json_dump(out_path.with_suffix(".json"), audit)
    logging.info("Wrote known DB audit page: %s", out_path)
    return audit


def generate_report(config: OrganizerConfig, *, refresh_related_pages: bool = True) -> None:
    records = verification_queue_records(config)
    attention = verification_attention_records(records)
    auto = [record for record in records if not record.get("verification_needed")]
    display_records = records if config.report_all else attention
    rows = []
    report_dir = config.report_path.parent
    for record in display_records:
        if "assignment_decision" not in record:
            record = apply_assignment_scoring(record)
        performers = record.get("performers", [])
        status = "needs-review" if record.get("verification_needed") else "auto"
        badges = " ".join(render_badge(item) for item in performers)
        identity = record.get("identity_resolution") or {}
        identity_html = ""
        if identity:
            identity_status = identity.get("status", "probable")
            identity_class = "badge-auto" if identity_status == "auto" else "badge-possible"
            identity_html = (
                '<div class="resolved">'
                f'<span class="badge {identity_class}">Resolved: {html.escape(str(identity.get("name", "")))} '
                f'({round(float(identity.get("combined_confidence", 0)) * 100)}% combined)</span>'
                "</div>"
            )
        crops = []
        review_frames = []
        for frame_text in record.get("review_frames", [])[:8]:
            frame_uri = image_to_data_uri(frame_text, report_dir)
            if frame_uri:
                review_frames.append(lightbox_image(frame_uri, "thumb-frame", "review frame"))
        for performer in performers[:4]:
            uri = image_to_data_uri(performer.get("face_crop_path"), report_dir)
            if uri:
                crops.append(lightbox_image(uri, "thumb-face", "face crop"))
            frame_uri = image_to_data_uri(performer.get("original_frame_path"), report_dir)
            if frame_uri:
                crops.append(lightbox_image(frame_uri, "thumb-frame", "source frame"))
        names = [item.get("name", "unknown performer") for item in performers]
        first_name = names[0] if names else "unknown performer"
        hints = clean_display_hints(((record.get("metadata_hints") or {}).get("candidate_names") or []))[:5]
        hint_html = ""
        decision_html = render_assignment_decision(record)
        query_html = render_query_cards(record)
        web_evidence_html = render_web_evidence(record)
        if hints:
            hint_badges = " ".join(
                f'<span class="hint">{html.escape(str(item.get("name", "")))} <small>{html.escape(str(item.get("source", "")))}</small></span>'
                for item in hints
            )
            hint_html = f'<div class="hints"><p>Metadata hints</p><div>{hint_badges}</div></div>'
            if first_name == "unknown performer":
                first_name = str(hints[0].get("name") or first_name)
        actions_html = render_action_snippets(record, first_name)
        preview_html = render_preview_section(review_frames, crops)
        review_hints_html = render_review_hints(hints)
        decision = normalize_assignment_decision(record.get("assignment_decision"))
        suggestion = str(decision.get("suggested_name") or ("" if first_name == "unknown performer" else first_name) or "No current suggestion")
        confidence = decision.get("confidence")
        if isinstance(confidence, (int, float)):
            confidence_text = f"{round(float(confidence) * 100)}%"
        else:
            best_conf = max((float(item.get("similarity") or item.get("confidence") or 0) for item in performers if isinstance(item, dict)), default=0.0)
            confidence_text = f"{round(best_conf * 100)}%" if best_conf else "n/a"
        duration = record.get("duration_seconds")
        duration_text = f"{round(float(duration), 1)}s" if isinstance(duration, (int, float)) else "unknown duration"
        details_html = render_review_details(decision_html, query_html, web_evidence_html)
        rows.append(
            f"""
            <article class="video-card" data-status="{status}" data-name="{html.escape(' '.join(names).lower())}">
              <div class="card-head simple-head">
                <div>
                  <h2>{html.escape(Path(record.get('video_path', 'unknown')).name)}</h2>
                  <div class="simple-meta">
                    <span>{html.escape(duration_text)}</span>
                    <span>{html.escape(str(record.get('faces_detected', 0)))} face(s)</span>
                    <span class="status-badge">{html.escape(status.replace('-', ' '))}</span>
                  </div>
                </div>
                <div class="metrics"><div>{html.escape(confidence_text)}</div><div>confidence</div></div>
              </div>
              <div class="suggestion-row">
                <span>Current suggestion</span>
                <strong>{html.escape(suggestion)}</strong>
                <p>{html.escape(render_plain_reason(record))}</p>
              </div>
              {identity_html}
              <div class="badges compact-badges">{badges or '<span class="badge badge-unknown">unknown performer</span>'}</div>
              {preview_html}
              {review_hints_html}
              {actions_html}
              {details_html}
            </article>
            """
        )
    generated = utc_now()
    queue_fingerprint = verification_queue_fingerprint_from_attention(attention)
    report_title = "All Records Audit" if config.report_all else "Verification Queue"
    empty_message = "No records matched this report mode." if config.report_all else "No videos need review. Auto-approved items have left this queue."
    report_css = """
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: #000; color: #f4f4f5; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    """ + report_nav_css() + """
    main { max-width: 80rem; margin: 0 auto; padding: 1.5rem 1rem; }
    header { display: flex; flex-direction: column; gap: 1rem; border-bottom: 1px solid rgba(255,255,255,.1); padding-bottom: 1.25rem; }
    h1 { margin: .5rem 0 0; font-size: 1.875rem; line-height: 2.25rem; color: #fff; }
    h2 { margin: .25rem 0 0; overflow-wrap: anywhere; font-size: 1.125rem; line-height: 1.75rem; color: #fff; }
    p { margin: 0; }
    code { overflow-wrap: anywhere; white-space: normal; }
    input, select { width: 100%; border: 0; border-radius: .25rem; background: #18181b; color: #f4f4f5; padding: .55rem .75rem; font-size: .875rem; outline: 1px solid rgba(255,255,255,.1); }
    input:focus, select:focus { outline-color: #67e8f9; }
    .kicker { font-size: .875rem; text-transform: uppercase; letter-spacing: 0; color: #67e8f9; }
    .muted { margin-top: .5rem; max-width: 42rem; font-size: .875rem; color: #a1a1aa; }
    .stats { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: .5rem; text-align: center; }
    .stat { border-radius: .5rem; background: #18181b; padding: .75rem; }
    .stat strong { display: block; font-size: 1.5rem; line-height: 2rem; }
    .stat span { font-size: .75rem; color: #71717a; }
    .filters { position: sticky; top: 0; z-index: 10; margin: 1rem -1rem 0; border-bottom: 1px solid rgba(255,255,255,.1); background: rgba(0,0,0,.86); padding: .75rem 1rem; backdrop-filter: blur(12px); }
    .filters-inner { display: flex; flex-direction: column; gap: .75rem; }
    #grid { display: grid; gap: 1rem; margin-top: 1.25rem; }
    .video-card { border-radius: .5rem; border: 1px solid rgba(255,255,255,.1); background: rgba(9,9,11,.88); padding: 1rem; box-shadow: 0 25px 50px -12px rgba(0,0,0,.45); }
    .card-head { display: flex; flex-direction: column; gap: .75rem; }
    .status-text { font-size: .75rem; text-transform: uppercase; letter-spacing: 0; color: #71717a; }
    .badges, .thumbs { display: flex; flex-wrap: wrap; gap: .5rem; }
    .badges { margin-top: .75rem; }
    .thumbs { margin-top: 1rem; gap: .75rem; }
    .frame-strip { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: 1rem; }
    .frame-strip img { height: 9rem; width: 9rem; border-radius: .25rem; object-fit: cover; outline: 1px solid rgba(255,255,255,.1); }
    .image-button { appearance: none; border: 0; background: transparent; padding: 0; cursor: zoom-in; }
    .image-button:focus-visible { outline: 2px solid #67e8f9; outline-offset: 3px; border-radius: .25rem; }
    .thumbs img { height: 7rem; border-radius: .25rem; object-fit: cover; outline: 1px solid rgba(255,255,255,.1); }
    .thumb-face { width: 7rem; }
    .thumb-frame { width: 11rem; }
    .empty-crop { border: 1px dashed rgba(255,255,255,.1); border-radius: .25rem; padding: 2rem 1rem; color: #71717a; font-size: .875rem; }
    .badge { display: inline-flex; border-radius: 9999px; padding: .25rem .75rem; font-size: .75rem; font-weight: 700; outline: 1px solid; }
    .badge-auto { background: rgba(16,185,129,.15); color: #d1fae5; outline-color: rgba(110,231,183,.3); }
    .badge-possible { background: rgba(251,191,36,.15); color: #fef3c7; outline-color: rgba(252,211,77,.3); }
    .badge-unknown { background: rgba(244,63,94,.15); color: #ffe4e6; outline-color: rgba(253,164,175,.3); }
    .metrics { color: #a1a1aa; font-size: .75rem; }
    .simple-meta { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .5rem; color: #a1a1aa; font-size: .78rem; }
    .simple-meta span { border-radius: .25rem; background: rgba(255,255,255,.05); padding: .2rem .45rem; }
    .status-badge { color: #fef3c7; }
    .suggestion-row { margin-top: .9rem; border-radius: .35rem; background: rgba(255,255,255,.045); padding: .75rem; }
    .suggestion-row span { display: block; margin-bottom: .2rem; color: #a1a1aa; font-size: .72rem; text-transform: uppercase; }
    .suggestion-row strong { display: block; color: #fff; overflow-wrap: anywhere; }
    .suggestion-row p { margin-top: .35rem; color: #d4d4d8; font-size: .85rem; }
    .compact-badges { margin-top: .75rem; }
    .preview-panel { margin-top: 1rem; border-radius: .35rem; background: rgba(255,255,255,.035); padding: .75rem; }
    .preview-panel .thumbs, .preview-panel .frame-strip { margin-top: 0; }
    .preview-panel .preview-faces { margin-bottom: .75rem; }
    .preview-panel .preview-faces img { height: 9rem; width: 9rem; }
    .preview-panel .preview-frames img { height: 8rem; width: 11rem; }
    .compact-empty { padding: 1rem; }
    .review-hints { margin-top: .75rem; border-radius: .35rem; background: rgba(103,232,249,.055); padding: .65rem .75rem; outline: 1px solid rgba(103,232,249,.12); }
    .review-hints p { margin-bottom: .5rem; color: #a5f3fc; font-size: .75rem; font-weight: 700; text-transform: uppercase; }
    .review-hints > div { display: flex; flex-wrap: wrap; gap: .4rem; }
    .review-hint { display: inline-flex; flex-direction: column; gap: .12rem; border-radius: .3rem; background: rgba(255,255,255,.06); padding: .45rem .55rem; outline: 1px solid rgba(255,255,255,.08); }
    .review-hint strong { color: #f8fafc; font-size: .82rem; overflow-wrap: anywhere; }
    .review-hint small { color: #a1a1aa; font-size: .7rem; }
    .review-details { margin-top: 1rem; border-top: 1px solid rgba(255,255,255,.08); padding-top: .75rem; }
    .review-details summary { cursor: pointer; color: #bfdbfe; font-weight: 700; font-size: .85rem; }
    .hints { margin-top: 1rem; border-top: 1px solid rgba(255,255,255,.08); padding-top: .75rem; }
    .resolved { margin-top: .75rem; }
    .hints p { margin-bottom: .5rem; color: #a1a1aa; font-size: .75rem; text-transform: uppercase; }
    .hint { display: inline-flex; align-items: baseline; gap: .35rem; margin: 0 .35rem .35rem 0; border-radius: 9999px; background: rgba(103,232,249,.1); color: #cffafe; padding: .25rem .6rem; font-size: .75rem; }
    .hint small { color: #67e8f9; }
    .decision-panel, .trace, .query-cards, .web-evidence { margin-top: 1rem; border-top: 1px solid rgba(255,255,255,.08); padding-top: .75rem; }
    .decision-head { display: flex; flex-wrap: wrap; align-items: center; gap: .5rem; }
    .decision-head strong { color: #fff; }
    .decision-head span:last-child { color: #a1a1aa; font-size: .75rem; }
    .decision-panel > p, .trace p, .query-cards p, .web-evidence > p { color: #a1a1aa; font-size: .75rem; }
    .decision-pill { border-radius: 9999px; padding: .2rem .55rem; font-size: .7rem; font-weight: 700; text-transform: uppercase; }
    .decision-auto { background: rgba(16,185,129,.16); color: #d1fae5; }
    .decision-review { background: rgba(251,191,36,.16); color: #fef3c7; }
    .blockers { margin: .5rem 0 0; padding-left: 1.1rem; color: #fecdd3; font-size: .75rem; }
    .trace ol { display: grid; gap: .45rem; margin: .5rem 0 0; padding: 0; list-style: none; }
    .trace li { display: grid; grid-template-columns: minmax(7rem, .8fr) minmax(8rem, 1fr) auto; gap: .5rem; align-items: baseline; border-radius: .25rem; background: rgba(255,255,255,.04); padding: .5rem; }
    .trace li p { grid-column: 1 / -1; }
    .trace strong { color: #bfdbfe; font-size: .75rem; }
    .trace span { color: #f4f4f5; font-size: .8rem; overflow-wrap: anywhere; }
    .trace em { color: #a1a1aa; font-size: .75rem; font-style: normal; }
    .trace a, .web-evidence a, .query-cards a { color: #bfdbfe; }
    .empty-mini { color: #71717a; font-size: .75rem; }
    .verify-links { margin-top: .75rem; display: grid; gap: .4rem; }
    .verify-links p { color: #a1a1aa; font-size: .75rem; text-transform: uppercase; }
    .verify-links div { display: flex; flex-wrap: wrap; align-items: center; gap: .4rem; color: #e4e4e7; font-size: .75rem; }
    .verify-links span { min-width: 7rem; color: #f4f4f5; font-weight: 700; }
    .verify-links a { border-radius: .25rem; background: rgba(244,244,245,.08); color: #bfdbfe; padding: .25rem .5rem; text-decoration: none; outline: 1px solid rgba(191,219,254,.18); }
    .verify-links a:hover { background: rgba(96,165,250,.16); color: #dbeafe; }
    .query-cards div, .web-evidence > div { display: grid; gap: .5rem; margin-top: .5rem; }
    .query-cards a, .evidence-card { border-radius: .25rem; background: rgba(244,244,245,.06); padding: .55rem .65rem; text-decoration: none; outline: 1px solid rgba(255,255,255,.08); }
    .query-cards small { display: block; margin-top: .25rem; color: #a1a1aa; overflow-wrap: anywhere; }
    .evidence-card span { display: inline-block; margin-bottom: .25rem; border-radius: 9999px; background: rgba(251,191,36,.13); color: #fef3c7; padding: .15rem .45rem; font-size: .7rem; font-weight: 700; }
    .evidence-card p { margin-top: .35rem; color: #d4d4d8; font-size: .8rem; }
    .evidence-card small { display: block; margin-top: .35rem; color: #fca5a5; font-size: .72rem; }
    .primary-actions { margin-top: 1rem; border-radius: .35rem; background: rgba(255,255,255,.04); padding: .75rem; }
    .primary-actions label { display: grid; gap: .35rem; color: #d4d4d8; font-size: .8rem; }
    .manual-submit-row { display: flex; flex-wrap: wrap; align-items: center; gap: .5rem; margin-top: .6rem; }
    .manual-submit { border: 0; border-radius: .25rem; background: #67e8f9; color: #082f49; padding: .55rem .75rem; font-weight: 800; cursor: pointer; }
    .manual-submit:disabled { cursor: wait; opacity: .62; }
    .unknown-submit { background: rgba(251,113,133,.2); color: #ffe4e6; outline: 1px solid rgba(251,113,133,.35); }
    .inline-check { display: inline-flex !important; grid-template-columns: auto 1fr; width: auto; align-items: center; gap: .35rem !important; }
    .inline-check input { width: auto; }
    .manual-status { min-height: 1.25rem; color: #a5f3fc; font-size: .78rem; }
    .manual-status.is-error { color: #fecdd3; }
    .manual-status.is-match { color: #bbf7d0; }
    .action-grid { display: grid; gap: .5rem; margin-top: .75rem; }
    .action-grid code, .action-link { border-radius: .25rem; padding: .65rem; font-size: .75rem; }
    .action-link { display: block; background: rgba(96,165,250,.12); color: #dbeafe; text-decoration: none; outline: 1px solid rgba(191,219,254,.18); }
    .confirm { background: rgba(52,211,153,.1); color: #d1fae5; }
    .unknown { background: rgba(251,113,133,.1); color: #ffe4e6; }
    .edit { background: rgba(251,191,36,.1); color: #fef3c7; }
    .empty-report { border: 1px solid rgba(255,255,255,.1); border-radius: .5rem; background: #09090b; padding: 2rem; color: #a1a1aa; }
    .lightbox { position: fixed; inset: 0; display: none; align-items: center; justify-content: center; z-index: 100; background: rgba(0,0,0,.9); padding: 1rem; }
    .lightbox.is-open { display: flex; }
    .live-status { color: #67e8f9; font-size: .8rem; }
    .lightbox img { max-width: min(96vw, 1400px); max-height: 92vh; object-fit: contain; border-radius: .35rem; box-shadow: 0 24px 80px rgba(0,0,0,.8); }
    @media (min-width: 768px) {
      header { flex-direction: row; align-items: flex-end; justify-content: space-between; }
      .filters-inner { flex-direction: row; }
      .filters-inner select { width: 14rem; }
      .card-head { flex-direction: row; align-items: flex-start; justify-content: space-between; }
      .metrics { text-align: right; }
      .action-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    """
    html_payload = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Media Face Verification</title>
  <style>{report_css}</style>
</head>
<body>
  <main>
    <header>
      <div>
        <p class="kicker">Media Face Organizer v1</p>
        <h1>{html.escape(report_title)}</h1>
        <p class="muted">Generated {html.escape(generated)} from {html.escape(str(config.source_dir))}</p>
        {'' if config.report_all else '<p id="queueLiveStatus" class="muted live-status">Live queue — auto-refreshes when new uploads need verification.</p>'}
        {report_nav_html("Report All / Full Audit" if config.report_all else "Verification Queue", config.report_path)}
      </div>
      <div class="stats">
        <div class="stat"><strong>{len(records)}</strong><span>total</span></div>
        <div class="stat"><strong>{len(attention)}</strong><span>review</span></div>
        <div class="stat"><strong>{len(auto)}</strong><span>auto</span></div>
      </div>
    </header>
    <section class="filters">
      <div class="filters-inner">
        <input id="search" placeholder="Search filename or performer">
        <select id="status">
          <option value="all">All statuses</option>
          <option value="needs-review">Needs review</option>
          <option value="auto">Auto</option>
        </select>
      </div>
    </section>
    <section id="grid">{''.join(rows) or f'<div class="empty-report">{html.escape(empty_message)}</div>'}</section>
  </main>
  <div id="lightbox" class="lightbox" role="dialog" aria-modal="true" aria-label="Image preview"><img id="lightboxImage" alt="Expanded preview"></div>
  <script>
    const search = document.getElementById('search');
    const status = document.getElementById('status');
    const cards = [...document.querySelectorAll('.video-card')];
    const lightbox = document.getElementById('lightbox');
    const lightboxImage = document.getElementById('lightboxImage');
    function applyFilters() {{
      const q = search.value.trim().toLowerCase();
      const s = status.value;
      for (const card of cards) {{
        const text = card.innerText.toLowerCase() + ' ' + card.dataset.name;
        const okSearch = !q || text.includes(q);
        const okStatus = s === 'all' || card.dataset.status === s;
        card.style.display = okSearch && okStatus ? '' : 'none';
      }}
    }}
    search.addEventListener('input', applyFilters);
    status.addEventListener('change', applyFilters);
    document.querySelectorAll('.image-button').forEach((button) => {{
      button.addEventListener('click', () => {{
        lightboxImage.src = button.dataset.full;
        lightbox.classList.add('is-open');
      }});
    }});
    lightbox.addEventListener('click', () => {{
      lightbox.classList.remove('is-open');
      lightboxImage.removeAttribute('src');
    }});
    document.addEventListener('keydown', (event) => {{
      if (event.key === 'Escape') {{
        lightbox.classList.remove('is-open');
        lightboxImage.removeAttribute('src');
      }}
    }});
    {'' if config.report_all else f'''
    const queueFingerprint = {json.dumps(queue_fingerprint)};
    let queueRefreshInFlight = false;
    async function pollVerificationQueue() {{
      try {{
        const response = await fetch('/api/verification/queue-status', {{ cache: 'no-store' }});
        const status = await response.json();
        if (!response.ok) return;
        if (status.fingerprint !== queueFingerprint && !queueRefreshInFlight) {{
          queueRefreshInFlight = true;
          const indicator = document.getElementById('queueLiveStatus');
          if (indicator) indicator.textContent = 'New uploads detected — refreshing verification queue...';
          await fetch('/api/verification/refresh-queue', {{ method: 'POST' }});
          let attempts = 0;
          const waitForRefresh = window.setInterval(async () => {{
            attempts += 1;
            try {{
              const next = await (await fetch('/api/verification/queue-status', {{ cache: 'no-store' }})).json();
              if (next.fingerprint === status.fingerprint || attempts >= 24) {{
                window.clearInterval(waitForRefresh);
                window.location.reload();
              }}
            }} catch (_) {{
              if (attempts >= 24) window.location.reload();
            }}
          }}, 1500);
        }}
      }} catch (_) {{}}
    }}
    window.setInterval(pollVerificationQueue, 30000);
    window.setTimeout(pollVerificationQueue, 5000);
    '''}
    const lookupTimers = new WeakMap();
    document.querySelectorAll('.manual-name').forEach((input) => {{
      input.addEventListener('input', () => {{
        const panel = input.closest('.primary-actions');
        const existing = panel ? panel.querySelector('.manual-existing') : null;
        const statusNode = panel ? panel.querySelector('.manual-status') : null;
        const name = input.value.trim();
        if (lookupTimers.has(input)) clearTimeout(lookupTimers.get(input));
        if (!name || !existing || !statusNode) {{
          if (existing) existing.checked = false;
          if (statusNode) {{
            statusNode.textContent = '';
            statusNode.classList.remove('is-error', 'is-match');
          }}
          return;
        }}
        lookupTimers.set(input, setTimeout(async () => {{
          try {{
            const response = await fetch('/api/verification/model-name-lookup', {{
              method: 'POST',
              headers: {{ 'Content-Type': 'application/json' }},
              body: JSON.stringify({{ name }}),
            }});
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Lookup failed');
            statusNode.classList.remove('is-error', 'is-match');
            if (result.existing) {{
              existing.checked = true;
              statusNode.classList.add('is-match');
              statusNode.textContent = result.face_enrolled
                ? `Existing enrolled model: ${{result.canonical_name}}`
                : `Existing model: ${{result.canonical_name}}`;
              if (result.canonical_name && input.value.trim().toLowerCase() !== String(result.canonical_name).toLowerCase()) {{
                input.value = result.canonical_name;
              }}
            }} else {{
              existing.checked = false;
              statusNode.textContent = 'New model name; will go to face enrollment.';
            }}
          }} catch (error) {{
            statusNode.textContent = '';
            statusNode.classList.remove('is-error', 'is-match');
          }}
        }}, 260));
      }});
    }});
    document.querySelectorAll('[data-action="manual-model-correction"]').forEach((button) => {{
      button.addEventListener('click', async () => {{
        const panel = button.closest('.primary-actions');
        const input = panel ? panel.querySelector('.manual-name') : null;
        const existing = panel ? panel.querySelector('.manual-existing') : null;
        const status = panel ? panel.querySelector('.manual-status') : null;
        const name = input ? input.value.trim() : '';
        if (!input || !status || !name) {{
          if (status) {{
            status.textContent = 'Enter the correct model name first.';
            status.classList.add('is-error');
          }}
          return;
        }}
        button.disabled = true;
        status.classList.remove('is-error');
        status.textContent = 'Saving correction...';
        try {{
          const response = await fetch('/api/verification/manual-model-correction', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
              sidecar_path: input.dataset.sidecar,
              name,
              belongs_to_existing: Boolean(existing && existing.checked),
              corrected_by: 'Britton',
              confirmed_by: 'Britton',
            }}),
          }});
          const result = await response.json();
          if (!response.ok) throw new Error(result.error || 'Correction failed');
          status.textContent = result.next_action === 'updated_existing_enrolled_model'
            ? 'Updated under enrolled model.'
            : 'Queued for face enrollment.';
          const card = button.closest('.record-card, article, section');
          if (card) {{
            card.style.opacity = '0.55';
            card.style.pointerEvents = 'none';
          }}
        }} catch (error) {{
          status.textContent = error instanceof Error ? error.message : 'Correction failed';
          status.classList.add('is-error');
          button.disabled = false;
        }}
      }});
    }});
    document.querySelectorAll('[data-action="leave-unknown"]').forEach((button) => {{
      button.addEventListener('click', async () => {{
        const panel = button.closest('.primary-actions');
        const status = panel ? panel.querySelector('.manual-status') : null;
        button.disabled = true;
        if (status) {{
          status.classList.remove('is-error');
          status.textContent = 'Leaving video as unknown...';
        }}
        try {{
          const response = await fetch('/api/verification/leave-unknown', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{
              sidecar_path: button.dataset.sidecar,
              confirmed_by: 'Britton',
            }}),
          }});
          const result = await response.json();
          if (!response.ok) throw new Error(result.error || 'Leave unknown failed');
          if (status) status.textContent = 'Marked unknown. Refreshing...';
          setTimeout(() => window.location.reload(), 900);
        }} catch (error) {{
          if (status) {{
            status.textContent = error instanceof Error ? error.message : 'Leave unknown failed';
            status.classList.add('is-error');
          }}
          button.disabled = false;
        }}
      }});
    }});
  </script>
</body>
</html>
"""
    config.report_path.parent.mkdir(parents=True, exist_ok=True)
    config.report_path.write_text(html_payload, encoding="utf-8")
    if not config.report_all:
        json_dump(
            config.report_path.with_suffix(".json"),
            {
                "schema": "media-face-verification-queue/v1",
                "fingerprint": queue_fingerprint,
                "generated_at": generated,
                "review_count": len(attention),
                "total_count": len(records),
            },
        )
    logging.info("Wrote verification report: %s", config.report_path)
    if refresh_related_pages and config.report_path.name in {"face_verification_report.html", "report.html"}:
        refresh_organizer_pages(config, refresh_stale_enrollment=True, include_verification_report=False)


def refresh_organizer_pages(
    config: OrganizerConfig,
    *,
    refresh_stale_enrollment: bool = True,
    include_verification_report: bool = True,
    scan_recent_uploads: bool = True,
) -> None:
    if scan_recent_uploads:
        scan_recent_unscanned_videos(config)
    if include_verification_report:
        generate_report(config, refresh_related_pages=False)
    generate_enrollment_queue_page(config, refresh_stale=refresh_stale_enrollment)
    generate_enrolled_page(config)
    generate_gallery_page(config)
    generate_known_db_audit_page(config)


def add_performer_from_image(
    config: OrganizerConfig,
    name: str,
    image_path: Path,
    *,
    aliases: list[str] | None = None,
    profile_handles: list[dict[str, str]] | None = None,
    profile_urls: list[str] | None = None,
    confirmed_by: str = "Britton",
) -> None:
    if not name.strip() or is_bad_candidate_name(name):
        raise RuntimeError(f"Unsafe performer name for enrollment: {name!r}")
    if not confirmed_by.strip():
        raise RuntimeError("--confirmed-by is required for performer enrollment")
    if not config.apply:
        logging.info("dry-run: would add performer %r from local crop %s", name, image_path)
        return
    if not image_path.exists():
        raise RuntimeError(f"Face image does not exist: {image_path}")
    if not image_path.is_file():
        raise RuntimeError(f"Face image must be a local file: {image_path}")
    if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise RuntimeError("Face image must be a local image crop (.jpg, .jpeg, .png, or .webp)")
    db = KnownPerformersDB(config.db_dir)
    performer_id = db.add_performer(name, aliases=aliases)
    recognizer = InsightFaceRecognizer(config.model_name, config.ctx_id, config.det_size)
    faces = recognizer.detect(image_path)
    if not faces:
        raise RuntimeError(f"No face detected in {image_path}")
    if len(faces) > 1:
        raise RuntimeError(f"Expected one confirmed face crop, found {len(faces)} faces in {image_path}")
    best = max(faces, key=lambda face: float(getattr(face, "det_score", 0.0)))
    if float(getattr(best, "det_score", 0.0)) < config.min_face_score:
        raise RuntimeError(f"Face detection score below enrollment threshold: {float(getattr(best, 'det_score', 0.0)):.3f}")
    db.append_embedding(performer_id, np.asarray(best.embedding, dtype=np.float32))
    target_dir = db.faces_dir / performer_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{slugify(image_path.stem)}-{uuid.uuid4().hex[:8]}{image_path.suffix.lower() or '.jpg'}"
    shutil.copy2(image_path, target)
    db.record_enrollment(
        performer_id,
        target,
        confirmed_by=confirmed_by,
        aliases=aliases,
        profile_handles=profile_handles,
        profile_urls=profile_urls,
    )
    update_registry_enrollment(
        config.verification_registry_path,
        name.strip(),
        performer_id,
        target,
        confirmed_by=confirmed_by,
        aliases=aliases or [],
        profile_handles=profile_handles or [],
        profile_urls=profile_urls or [],
    )
    logging.info("Added performer %s (%s) with sample %s", name, performer_id, target)


def read_json_body(handler: http.server.BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8"))


def write_response(handler: http.server.BaseHTTPRequestHandler, status: int, payload: bytes, content_type: str) -> None:
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def write_json_response(handler: http.server.BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    write_response(handler, status, json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")


def mark_performer_faceless(config: OrganizerConfig, payload: dict[str, Any]) -> dict[str, Any]:
    performer_name = canonical_performer_name(str(payload.get("performer_name") or "").strip(), load_performer_registry(config.verification_registry_path))
    confirmation = str(payload.get("confirmation") or "").strip()
    confirmed_by = str(payload.get("confirmed_by") or "Britton").strip()
    if not performer_name:
        raise RuntimeError("performer_name is required")
    if confirmation != performer_name and confirmation != slugify(performer_name):
        raise RuntimeError("confirmation field must match the performer name or slug")
    if not confirmed_by:
        raise RuntimeError("confirmed_by is required")
    registry = load_performer_registry(config.verification_registry_path)
    canonical_name = canonical_performer_name(performer_name, registry)
    slug, entry = registry_entry_for_name(registry, canonical_name)
    if entry is None:
        entry = registry.setdefault("performers", {}).setdefault(
            slug,
            {
                "name": canonical_name,
                "slug": slug,
                "aliases": [],
                "profile_handles": [],
                "status": "user-confirmed",
                "evidence": [],
                "web_text_evidence_summary": summarize_web_text_evidence([]),
                "identity_trace_summary": {"schema": IDENTITY_TRACE_SCHEMA, "count": 0, "review_required": True},
                "assignment_decision": blank_assignment_decision(),
                "video_count": 0,
            },
        )
    event = {
        "event": "performer_marked_faceless",
        "performer_name": canonical_name,
        "confirmed_by": confirmed_by,
        "confirmed_at": utc_now(),
        "reason": str(payload.get("reason") or "User confirmed current content does not show a usable face."),
    }
    if config.apply:
        entry["name"] = canonical_name
        entry["slug"] = slug
        entry["status"] = "user-confirmed"
        entry["faceless"] = True
        entry["face_enrollment_status"] = "faceless"
        entry["faceless_confirmed_by"] = confirmed_by
        entry["faceless_confirmed_at"] = event["confirmed_at"]
        entry.setdefault("audit_events", []).append(event)
        registry.setdefault("aliases", {})[normalize_identity_key(canonical_name)] = canonical_name
        registry["updated_at"] = utc_now()
        json_dump(config.verification_registry_path, registry)
        write_model_index_from_registry(config, registry)
    return {
        "schema": "media-face-enrollment-faceless/v1",
        "event": "performer_marked_faceless",
        "performer_name": canonical_name,
        "slug": slug,
        "applied": bool(config.apply),
        "audit_event": event,
    }


def record_rejected_crop(config: OrganizerConfig, payload: dict[str, Any]) -> dict[str, Any]:
    crop_lookup = candidate_crop_lookup(config)
    crop_paths = [str(item) for item in payload.get("crop_paths") or []]
    signatures = []
    for crop_path in crop_paths:
        signatures.append(crop_recommendation_signature(crop_lookup.get(crop_path) or crop_path))
    record = {
        "schema": "media-face-enrollment-rejected-crop/v1",
        "created_at": utc_now(),
        "performer_name": str(payload.get("performer_name") or ""),
        "crop_paths": crop_paths,
        "crop_signatures": sorted(set(signatures)),
        "reason": str(payload.get("reason") or "rejected in enrollment queue"),
    }
    path = enrollment_review_dir(config) / "rejected_crops.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def remove_enrolled_samples(config: OrganizerConfig, payload: dict[str, Any]) -> dict[str, Any]:
    performer_name = str(payload.get("performer_name") or "").strip()
    sample_paths = [str(item) for item in payload.get("sample_paths") or [] if str(item)]
    if not performer_name:
        raise RuntimeError("performer_name is required")
    if not sample_paths:
        raise RuntimeError("select at least one accepted screen to remove")
    registry = load_performer_registry(config.verification_registry_path)
    model_lookup = model_index_lookup(config.verification_registry_path.with_name("model_index.json"))
    known = known_db_summary(config.db_dir)
    presence = performer_presence(canonical_performer_name(performer_name, registry), registry, model_lookup, known)
    performer_id = str(presence.get("known_performer_id") or "")
    if not performer_id:
        raise RuntimeError(f"known performer not found for {performer_name}")
    if not config.apply:
        return {"dry_run": True, "would_remove_samples": sample_paths, "performer_id": performer_id}
    backup_root = backup_known_performers_files(config)
    db = KnownPerformersDB(config.db_dir)
    result = db.remove_enrolled_samples(performer_id, sample_paths)
    result.update(
        {
            "schema": "media-face-enrolled-sample-remove/v1",
            "event": "enrolled_samples_removed",
            "performer_name": performer_name,
            "performer_id": performer_id,
            "backup_root": str(backup_root),
            "removed_at": utc_now(),
        }
    )
    return result


def rejected_crop_paths(config: OrganizerConfig, performer_name: str = "") -> set[str]:
    path = enrollment_review_dir(config) / "rejected_crops.jsonl"
    if not path.exists():
        return set()
    target_key = normalize_identity_key(performer_name)
    rejected: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            item = json.loads(line)
        except Exception:
            continue
        item_key = normalize_identity_key(str(item.get("performer_name") or ""))
        if target_key and item_key and item_key != target_key:
            continue
        for crop_path in item.get("crop_paths") or []:
            rejected.add(str(crop_path))
    return rejected


def rejected_crop_signatures(config: OrganizerConfig, performer_name: str = "") -> set[str]:
    path = enrollment_review_dir(config) / "rejected_crops.jsonl"
    if not path.exists():
        return set()
    target_key = normalize_identity_key(performer_name)
    rejected: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            item = json.loads(line)
        except Exception:
            continue
        item_key = normalize_identity_key(str(item.get("performer_name") or ""))
        if target_key and item_key and item_key != target_key:
            continue
        for signature in item.get("crop_signatures") or []:
            rejected.add(str(signature))
        for crop_path in item.get("crop_paths") or []:
            rejected.add(crop_recommendation_signature(str(crop_path)))
    return rejected


def candidate_crop_lookup(config: OrganizerConfig) -> dict[str, dict[str, Any]]:
    payload = load_json(enrollment_review_dir(config) / "enrollment_candidates.json", {"groups": []})
    lookup: dict[str, dict[str, Any]] = {}
    for group in payload.get("groups", []):
        if not isinstance(group, dict):
            continue
        for crop in group.get("recommended_crops") or []:
            if isinstance(crop, dict) and crop.get("crop_path"):
                crop_path = str(crop.get("crop_path"))
                lookup[crop_path] = crop
                lookup[str(resolve_artifact_path(crop_path, config))] = crop
                lookup[equivalent_artifact_key(crop_path, config)] = crop
    return lookup


def candidate_group_for_name(config: OrganizerConfig, performer_name: str) -> dict[str, Any]:
    registry = load_performer_registry(config.verification_registry_path)
    target_slug = slugify(canonical_performer_name(performer_name, registry))
    payload = load_json(enrollment_review_dir(config) / "enrollment_candidates.json", {"groups": []})
    for group in payload.get("groups", []):
        if not isinstance(group, dict):
            continue
        group_name = canonical_performer_name(str(group.get("name") or group.get("slug") or ""), registry)
        if str(group.get("slug") or "") == target_slug or slugify(group_name) == target_slug:
            return group
    return {}


def remove_candidate_crops_from_queue(config: OrganizerConfig, performer_name: str, crop_paths: list[str]) -> int:
    if not crop_paths:
        return 0
    candidate_path = enrollment_review_dir(config) / "enrollment_candidates.json"
    payload = load_json(candidate_path, {"groups": []})
    target_slug = slugify(canonical_performer_name(performer_name, load_performer_registry(config.verification_registry_path)))
    remove_paths = {str(path) for path in crop_paths if path}
    remove_keys = {equivalent_artifact_key(path, config) for path in crop_paths if path}
    removed = 0
    for group in payload.get("groups") or []:
        if not isinstance(group, dict):
            continue
        group_slug = str(group.get("slug") or slugify(str(group.get("name") or "")))
        if group_slug != target_slug:
            continue
        kept_crops = []
        removed_stills = set()
        for crop in group.get("recommended_crops") or []:
            crop_path = str((crop or {}).get("crop_path") or "")
            if crop_path in remove_paths or equivalent_artifact_key(crop_path, config) in remove_keys:
                removed += 1
                removed_stills.add(str((crop or {}).get("still_path") or ""))
                continue
            kept_crops.append(crop)
        group["recommended_crops"] = kept_crops
        group["recommended_stills"] = [
            still
            for still in group.get("recommended_stills") or []
            if str((still or {}).get("still_path") or "") not in removed_stills
        ]
        group["candidate_face_crops"] = len(kept_crops)
    if removed and config.apply:
        payload["updated_at"] = utc_now()
        json_dump(candidate_path, payload)
    return removed


def smart_candidate_crops(group: dict[str, Any], config: OrganizerConfig, target_count: int = 5) -> list[dict[str, Any]]:
    rejected_paths = rejected_crop_paths(config, str(group.get("name") or ""))
    rejected_signatures = rejected_crop_signatures(config, str(group.get("name") or ""))
    crops = [
        crop
        for crop in group.get("recommended_crops") or []
        if isinstance(crop, dict)
        and crop.get("crop_path")
        and resolve_artifact_path(str(crop.get("crop_path")), config).exists()
        and str(crop.get("crop_path")) not in rejected_paths
        and equivalent_artifact_key(str(crop.get("crop_path")), config) not in rejected_paths
        and crop_recommendation_signature(crop) not in rejected_signatures
    ]
    crops = enrollable_candidate_crops(dedupe_candidate_crops(crops), config)
    by_video: dict[str, list[dict[str, Any]]] = {}
    for crop in sorted(crops, key=lambda item: float(item.get("quality_score") or 0), reverse=True):
        key = str(crop.get("source_video") or crop.get("source_video_name") or "")
        by_video.setdefault(key, []).append(crop)
    selected: list[dict[str, Any]] = []
    used_paths: set[str] = set()
    for key in sorted(by_video, key=lambda value: float(by_video[value][0].get("quality_score") or 0), reverse=True):
        crop = by_video[key][0]
        crop_path = str(crop.get("crop_path") or "")
        if crop_path and crop_path not in used_paths:
            selected.append(crop)
            used_paths.add(crop_path)
        if len(selected) >= target_count:
            return selected
    for crop in sorted(crops, key=lambda item: float(item.get("quality_score") or 0), reverse=True):
        crop_path = str(crop.get("crop_path") or "")
        if crop_path and crop_path not in used_paths:
            selected.append(crop)
            used_paths.add(crop_path)
        if len(selected) >= target_count:
            break
    return selected


def smart_accept_best_crops(config: OrganizerConfig, payload: dict[str, Any]) -> dict[str, Any]:
    performer_name = str(payload.get("performer_name") or "").strip()
    confirmation = str(payload.get("confirmation") or "").strip()
    confirmed_by = str(payload.get("confirmed_by") or "Britton").strip()
    if not performer_name:
        raise RuntimeError("performer_name is required")
    if confirmation != performer_name and confirmation != slugify(performer_name):
        raise RuntimeError("confirmation field must match the performer name or slug")
    known = known_db_summary(config.db_dir)
    key = normalize_identity_key(performer_name)
    existing = False
    existing_sample_count = 0
    for performer in known.get("performers", []):
        if not isinstance(performer, dict):
            continue
        keys = {normalize_identity_key(str(performer.get("id") or "")), normalize_identity_key(str(performer.get("name") or ""))}
        keys.update(normalize_identity_key(str(alias)) for alias in performer.get("aliases", []) if alias)
        if key in keys:
            existing = True
            existing_sample_count = len(performer.get("enrolled_face_sample_records") or performer.get("enrolled_face_samples") or [])
            break
    group = candidate_group_for_name(config, performer_name)
    requested_count = int(payload.get("target_count") or 0)
    target_count = min(requested_count, 5) if requested_count > 0 else max(0, min(5, ENROLLMENT_CONFIDENCE_MAX_TARGET_SCREENS - existing_sample_count))
    if target_count <= 0:
        raise RuntimeError(f"{performer_name} already has {existing_sample_count} accepted screen(s), which meets the current optimal cap.")
    selected = smart_candidate_crops(group, config, target_count=target_count)
    if not selected:
        raise RuntimeError("smart accept could not find existing enrollable candidate crops; run Scan current videos again first")
    enrollment = enroll_selected_crops(
        config,
        {
            "performer_name": performer_name,
            "confirmation": confirmation or performer_name,
            "crop_paths": [str(crop.get("crop_path")) for crop in selected],
            "add_to_existing": existing,
            "create_new": not existing,
            "confirmed_by": confirmed_by,
            "defer_unidentified_rescan": True,
        },
    )
    return {
        "schema": "media-face-enrollment-smart-accept/v1",
        "event": "smart_best_crops_accepted",
        "performer_name": performer_name,
        "selected_crops": selected,
        "selection_count": len(selected),
        "enrollment": enrollment,
        "generated_at": utc_now(),
    }


def make_review_handler(config: OrganizerConfig) -> type[http.server.BaseHTTPRequestHandler]:
    report_dir = config.report_path.parent.resolve()
    source_dir = config.source_dir.resolve()
    db_dir = config.db_dir.resolve()

    def refresh_review_outputs_async(
        reason: str,
        *,
        enrollment_target: str | None = None,
        enrolled_only: bool = False,
    ) -> None:
        def worker() -> None:
            try:
                logging.info("Refreshing face organizer review outputs after %s", reason)
                if enrolled_only:
                    generate_enrolled_page(config)
                    return
                if enrollment_target:
                    generate_enrollment_candidates(
                        config,
                        max_groups=None,
                        target_name=enrollment_target,
                        refresh_pages=False,
                    )
                scan_recent_unscanned_videos(config)
                generate_report(config)
                generate_enrollment_queue_page(config)
                generate_enrolled_page(config)
                generate_known_db_audit_page(config)
            except Exception as exc:
                logging.warning("Deferred face organizer refresh after %s failed: %s", reason, exc)

        threading.Thread(target=worker, name=f"face-organizer-refresh-{reason}", daemon=True).start()

    class ReviewHandler(http.server.BaseHTTPRequestHandler):
        server_version = "FaceOrganizerReview/1.0"

        def log_message(self, format: str, *args: Any) -> None:
            logging.info("review-server: " + format, *args)

        def _serve_file(self, path: Path) -> None:
            try:
                resolved = path.resolve()
                allowed_roots = [report_dir, source_dir, db_dir, enrollment_review_dir(config).resolve(), gallery_root(config).resolve()]
                if not any(resolved == root or root in resolved.parents for root in allowed_roots):
                    write_json_response(self, HTTPStatus.FORBIDDEN, {"error": "file outside allowed review roots"})
                    return
                if not resolved.exists() or not resolved.is_file():
                    write_json_response(self, HTTPStatus.NOT_FOUND, {"error": "not found"})
                    return
                content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
                payload_len = resolved.stat().st_size
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(payload_len))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                with resolved.open("rb") as handle:
                    while True:
                        chunk = handle.read(1024 * 256)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                return
            except Exception as exc:
                write_json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            path = urllib.parse.unquote(parsed.path)
            try:
                if path in {"/", "/face_verification_report.html"}:
                    self._serve_file(config.report_path)
                    return
                if path in {"/enrollment", "/face_enrollment_queue.html"}:
                    self._serve_file(config.report_path.with_name("face_enrollment_queue.html"))
                    return
                if path in {"/enrolled", "/face_enrolled_performers.html"}:
                    self._serve_file(config.report_path.with_name("face_enrolled_performers.html"))
                    return
                if path in {"/gallery", "/face_gallery.html"}:
                    if not config.report_path.with_name("face_gallery.html").exists():
                        generate_gallery_page(config)
                    self._serve_file(config.report_path.with_name("face_gallery.html"))
                    return
                if path in {"/manual-crop", "/manual_crop.html"}:
                    if not config.report_path.with_name("manual_crop.html").exists():
                        generate_manual_crop_page(config)
                    self._serve_file(config.report_path.with_name("manual_crop.html"))
                    return
                if path in {"/known-db-audit", "/known_db_audit.html"}:
                    if not config.report_path.with_name("known_db_audit.html").exists():
                        generate_known_db_audit_page(config)
                    self._serve_file(config.report_path.with_name("known_db_audit.html"))
                    return
                if path == "/api/verification/queue-status":
                    write_json_response(self, HTTPStatus.OK, build_verification_queue_status(config))
                    return
                if path == "/api/enrollment/groups":
                    write_json_response(self, HTTPStatus.OK, build_enrollment_groups(config))
                    return
                if path == "/api/enrolled/groups":
                    write_json_response(self, HTTPStatus.OK, build_enrolled_groups(config, refresh_recommendations=False))
                    return
                if path == "/api/gallery":
                    write_json_response(self, HTTPStatus.OK, build_gallery_payload(config))
                    return
                if path.startswith("/mnt/spirit-8tb/media/yes/"):
                    self._serve_file(config.source_dir / path.removeprefix("/mnt/spirit-8tb/media/yes/").lstrip("/"))
                    return
                if (
                    path.startswith("/DATA/")
                    or path.startswith(str(config.source_dir).replace("\\", "/"))
                    or path.startswith(str(config.db_dir.resolve()).replace("\\", "/"))
                    or path.startswith(str(gallery_root(config).resolve()).replace("\\", "/"))
                ):
                    self._serve_file(Path(path))
                    return
                candidate = report_dir / path.lstrip("/")
                self._serve_file(candidate)
            except (BrokenPipeError, ConnectionResetError):
                return
            except Exception as exc:
                write_json_response(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

        def do_POST(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            payload = {} if parsed.path == "/api/gallery/upload" else read_json_body(self)
            try:
                if parsed.path == "/api/verification/refresh-queue":
                    refresh_review_outputs_async("queue-refresh-api")
                    write_json_response(self, HTTPStatus.ACCEPTED, {"status": "refreshing"})
                    return
                if parsed.path == "/api/gallery/upload":
                    fields, files = read_multipart_form(self)
                    result = save_gallery_uploads(config, fields, files)
                    generate_enrolled_page(config)
                    generate_gallery_page(config)
                    write_json_response(self, HTTPStatus.OK, result)
                    return
                if parsed.path == "/api/enrollment/groups":
                    write_json_response(self, HTTPStatus.OK, build_enrollment_groups(config))
                    return
                if parsed.path == "/api/enrollment/generate-candidates":
                    target_name = "" if payload.get("all_models") else str(payload.get("performer_name") or "")
                    result = generate_enrollment_candidates(
                        config,
                        max_groups=0 if payload.get("all_models") else None,
                        target_name=target_name,
                        missing_only=bool(payload.get("missing_only")),
                    )
                    write_json_response(self, HTTPStatus.OK, result)
                    return
                if parsed.path == "/api/enrollment/manual-crop":
                    result = save_manual_crop_candidate(config, payload)
                    write_json_response(self, HTTPStatus.OK, result)
                    return
                if parsed.path == "/api/verification/model-name-lookup":
                    result = lookup_manual_model_name(config, str(payload.get("name") or ""))
                    write_json_response(self, HTTPStatus.OK, result)
                    return
                if parsed.path == "/api/verification/manual-model-correction":
                    requested_name = str(payload.get("name") or "")
                    result = apply_manual_name_correction(
                        config,
                        sidecar_record_path(str(payload.get("sidecar_path") or "")),
                        requested_name,
                        corrected_by=str(payload.get("corrected_by") or "Britton"),
                        confirmed_by=str(payload.get("confirmed_by") or "Britton"),
                        belongs_to_existing=bool(payload.get("belongs_to_existing")),
                    )
                    result["refresh_deferred"] = True
                    refresh_review_outputs_async(
                        "manual-model-correction",
                        enrollment_target=str(result.get("name") or requested_name or ""),
                    )
                    write_json_response(self, HTTPStatus.OK, result)
                    return
                if parsed.path == "/api/verification/leave-unknown":
                    result = mark_video_left_unknown(
                        config,
                        sidecar_record_path(str(payload.get("sidecar_path") or "")),
                        confirmed_by=str(payload.get("confirmed_by") or "Britton"),
                        reason=str(payload.get("reason") or ""),
                    )
                    generate_report(config)
                    generate_enrollment_queue_page(config)
                    generate_enrolled_page(config)
                    generate_known_db_audit_page(config)
                    write_json_response(self, HTTPStatus.OK, result)
                    return
                if parsed.path == "/api/enrollment/enroll":
                    result = enroll_selected_crops(config, payload)
                    generate_enrollment_queue_page(config, refresh_stale=False)
                    result["refresh_deferred"] = True
                    refresh_review_outputs_async("enrollment-enroll")
                    write_json_response(self, HTTPStatus.OK, result)
                    return
                if parsed.path == "/api/enrollment/smart-accept":
                    result = smart_accept_best_crops(config, payload)
                    generate_enrollment_queue_page(config, refresh_stale=False)
                    result["refresh_deferred"] = True
                    refresh_review_outputs_async("enrollment-smart-accept")
                    write_json_response(self, HTTPStatus.OK, result)
                    return
                if parsed.path == "/api/enrolled/remove-sample":
                    result = remove_enrolled_samples(config, payload)
                    generate_enrolled_page(config)
                    write_json_response(self, HTTPStatus.OK, result)
                    return
                if parsed.path == "/api/enrolled/scan-library-matches":
                    result = scan_library_for_enrolled_model(config, payload)
                    generate_enrolled_page(config)
                    write_json_response(self, HTTPStatus.OK, result)
                    return
                if parsed.path == "/api/enrolled/video-match-decision":
                    result = set_enrolled_video_match_decision(config, payload)
                    result["refresh_deferred"] = True
                    write_json_response(self, HTTPStatus.OK, result)
                    refresh_review_outputs_async(
                        f"video-match-{result.get('decision') or 'decision'}",
                        enrolled_only=True,
                    )
                    return
                if parsed.path == "/api/enrolled/video-faceless":
                    result = mark_video_faceless(config, payload)
                    generate_enrolled_page(config)
                    write_json_response(self, HTTPStatus.OK, result)
                    return
                if parsed.path == "/api/enrolled/video-deep-scan":
                    result = deep_scan_enrolled_video(config, payload)
                    generate_enrolled_page(config)
                    write_json_response(self, HTTPStatus.OK, result)
                    return
                if parsed.path == "/api/enrollment/merge-creator":
                    result = merge_duplicate_creator(config, payload)
                    result["refresh_deferred"] = True
                    refresh_review_outputs_async("enrollment-merge-creator")
                    write_json_response(self, HTTPStatus.OK, result)
                    return
                if parsed.path == "/api/enrollment/mark-faceless":
                    result = mark_performer_faceless(config, payload)
                    result["refresh_deferred"] = True
                    refresh_review_outputs_async("enrollment-mark-faceless")
                    write_json_response(self, HTTPStatus.OK, result)
                    return
                if parsed.path == "/api/enrollment/reject-crop":
                    result = record_rejected_crop(config, payload)
                    write_json_response(self, HTTPStatus.OK, result)
                    return
                write_json_response(self, HTTPStatus.NOT_FOUND, {"error": "unknown endpoint"})
            except Exception as exc:
                write_json_response(self, HTTPStatus.BAD_REQUEST, {"error": str(exc), "status": "NEEDS_FIX"})

    return ReviewHandler


def serve_review(config: OrganizerConfig, host: str, port: int) -> None:
    server = http.server.ThreadingHTTPServer((host, port), make_review_handler(config))
    logging.info("Serving face organizer review at http://%s:%s/face_verification_report.html", host, port)

    def startup_refresh() -> None:
        try:
            logging.info("Background startup refresh for face organizer review pages")
            generate_report(config)
            generate_enrollment_queue_page(config, refresh_stale=False)
            generate_enrolled_page(config)
            generate_gallery_page(config)
            generate_known_db_audit_page(config)
            generate_manual_crop_page(config)
            logging.info("Background startup refresh complete")
        except Exception as exc:
            logging.warning("Background startup refresh failed: %s", exc)

    threading.Thread(target=startup_refresh, name="face-organizer-startup-refresh", daemon=True).start()
    try:
        server.serve_forever()
    finally:
        server.server_close()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local GPU face detection + performer recognition for media libraries.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--scan", action="store_true", help="scan videos; default mode")
    mode.add_argument("--report", action="store_true", help="generate the HTML verification report from existing metadata")
    mode.add_argument("--add-performer", metavar="NAME", help="add a confirmed performer embedding from --face-image")
    mode.add_argument("--init-db", action="store_true", help="create known_performers DB files and exit")
    mode.add_argument("--enrich-metadata", action="store_true", help="add filename/provider candidate-name hints to existing sidecars")
    mode.add_argument("--rename-plan", action="store_true", help="generate a review-only smart rename manifest")
    mode.add_argument("--backup-state", action="store_true", help="copy current sidecars, performer DB, report, and optionally videos to backups")
    mode.add_argument("--backfill-review-frames", action="store_true", help="extract general review frames for existing sidecars")
    mode.add_argument("--verify-performers", action="store_true", help="build/update canonical performer registry and repair duplicate names")
    mode.add_argument("--audit-known-db", action="store_true", help="read-only audit of registry/model index versus known face embeddings")
    mode.add_argument("--spiritflix-library-smart-rescan", action="store_true", help="refresh existing model face crops, then force-rescan videos for high-confidence model matches")
    mode.add_argument("--organizer-quick-refresh", action="store_true", help="regenerate organizer HTML pages without heavy enrollment rescans")
    mode.add_argument("--generate-enrollment-candidates", action="store_true", help="generate local review-only face enrollment candidates")
    mode.add_argument("--enrollment-queue", action="store_true", help="generate the static face enrollment queue page")
    mode.add_argument("--enrolled-page", action="store_true", help="generate the enrolled performers page")
    mode.add_argument("--gallery-page", action="store_true", help="generate the static gallery upload page")
    mode.add_argument("--known-db-audit-page", action="store_true", help="generate the static known DB audit page")
    mode.add_argument("--serve-review", action="store_true", help="serve verification/enrollment review pages and local-only POST actions")
    mode.add_argument("--scan-video", type=Path, metavar="VIDEO", help="scan exactly one video and write its face sidecar when --apply is passed")
    mode.add_argument("--record-correction", metavar="NAME", help="store a pending manual correction on a sidecar; requires --sidecar and --apply to write")
    mode.add_argument("--confirm-correction", action="store_true", help="confirm a pending manual correction into registry/model index; requires --sidecar and --apply to write")
    parser.add_argument("--face-image", type=Path, help="face crop/image to use with --add-performer")
    parser.add_argument("--sidecar", type=Path, help="sidecar JSON path, or video path whose .face-meta.json should be used")
    parser.add_argument("--alias", action="append", default=[], help="alias/public handle to record with --add-performer; repeatable")
    parser.add_argument("--profile-handle", action="append", default=[], help="profile handle such as onlyfans:handle, fansly:handle, or a profile URL; repeatable")
    parser.add_argument("--profile-url", action="append", default=[], help="public/stage profile URL to record with --add-performer; repeatable")
    parser.add_argument("--corrected-by", default="Britton", help="operator/user who entered a pending manual correction")
    parser.add_argument("--confirmed-by", default="Britton", help="operator/user who confirmed the local crop enrollment")
    parser.add_argument("--belongs-to-existing", action="store_true", help="mark pending correction as belonging to an existing performer")
    parser.add_argument("--source", type=Path, default=Path(DEFAULT_SOURCE), help=f"media source directory (default: {DEFAULT_SOURCE})")
    parser.add_argument("--db", type=Path, default=Path(DEFAULT_DB), help=f"known performers DB directory (default: {DEFAULT_DB})")
    parser.add_argument("--report-path", type=Path, default=Path(DEFAULT_REPORT), help=f"HTML report path (default: {DEFAULT_REPORT})")
    parser.add_argument("--report-all", action="store_true", help="include all metadata records in --report instead of only review-needed records")
    parser.add_argument("--backup-dir", type=Path, default=Path(DEFAULT_BACKUP_DIR), help=f"backup directory (default: {DEFAULT_BACKUP_DIR})")
    parser.add_argument(
        "--rename-manifest",
        type=Path,
        default=Path(DEFAULT_RENAME_MANIFEST),
        help=f"smart rename manifest path (default: {DEFAULT_RENAME_MANIFEST})",
    )
    parser.add_argument(
        "--organize-manifest",
        type=Path,
        default=Path(DEFAULT_ORGANIZE_MANIFEST),
        help=f"organization manifest path (default: {DEFAULT_ORGANIZE_MANIFEST})",
    )
    parser.add_argument(
        "--verification-registry",
        type=Path,
        default=Path(DEFAULT_VERIFICATION_REGISTRY),
        help=f"canonical performer verification registry path (default: {DEFAULT_VERIFICATION_REGISTRY})",
    )
    parser.add_argument("--apply", action="store_true", help="write sidecar JSON, review crops, NFO files, or DB changes")
    parser.add_argument("--dry-run", action="store_true", help="explicit dry-run; this is already the default")
    parser.add_argument("--online-metadata", action="store_true", help="allow configured online metadata providers such as pAPI")
    parser.add_argument("--backup-videos", action="store_true", help="with --backup-state --apply, also copy selected videos")
    parser.add_argument("--write-nfo", action="store_true", help="with --apply, also write minimal Jellyfin .nfo files")
    parser.add_argument("--force", action="store_true", help="rescan even when metadata is fresh")
    parser.add_argument("--skip-existing", action="store_true", help="scan only videos that do not already have face metadata")
    parser.add_argument("--recursive", action=argparse.BooleanOptionalAction, default=True, help="scan recursively")
    parser.add_argument("--frame-count", type=int, default=6, help="frames to sample per video")
    parser.add_argument("--sample-limit", type=int, help="limit scan to first N videos; use 2 or 3 for test mode")
    parser.add_argument("--smart-accept-limit", type=int, default=0, help="with --spiritflix-library-smart-rescan, limit existing models to smart-accept before video rescan")
    parser.add_argument("--smart-rescan-model-limit", type=int, default=0, help="with --spiritflix-library-smart-rescan, limit the model candidate groups to refresh")
    parser.add_argument("--smart-rescan-video-limit", type=int, default=0, help="with --spiritflix-library-smart-rescan, limit the model video rescan batch size")
    parser.add_argument("--enrollment-target", metavar="NAME", help="limit --generate-enrollment-candidates to one performer and scan all of their videos")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"InsightFace model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--ctx-id", type=int, default=0, help="InsightFace ctx_id; 0 for first GPU, -1 for CPU")
    parser.add_argument("--det-size", default="640x640", help="detector size WIDTHxHEIGHT")
    parser.add_argument("--min-face-score", type=float, default=0.65, help="ignore weak detections below this score")
    parser.add_argument("--min-face-area-ratio", type=float, default=0.002, help="ignore tiny faces below this frame-area ratio")
    parser.add_argument("--ocr-watermarks", action=argparse.BooleanOptionalAction, default=True, help="read visible watermark/profile text from sampled frames")
    parser.add_argument("--review-dir-name", default=".face-review", help="directory beside videos for persisted crops/frames")
    parser.add_argument("--host", default="127.0.0.1", help="host for --serve-review")
    parser.add_argument("--port", type=int, default=8765, help="port for --serve-review")
    parser.add_argument("--organize", action="store_true", help="move auto-approved videos to models and unresolved videos to unknown; requires --apply")
    parser.add_argument("--verbose", action="store_true", help="debug logging")
    return parser.parse_args(argv)


def make_config(args: argparse.Namespace) -> OrganizerConfig:
    try:
        width_text, height_text = args.det_size.lower().split("x", 1)
        det_size = (int(width_text), int(height_text))
    except Exception as exc:
        raise SystemExit("--det-size must look like 640x640") from exc
    return OrganizerConfig(
        source_dir=args.source,
        db_dir=args.db,
        report_path=args.report_path,
        backup_dir=args.backup_dir,
        rename_manifest_path=args.rename_manifest,
        organize_manifest_path=args.organize_manifest,
        verification_registry_path=args.verification_registry,
        apply=bool(args.apply and not args.dry_run),
        write_nfo=bool(args.write_nfo),
        backup_videos=bool(args.backup_videos),
        frame_count=max(1, int(args.frame_count)),
        sample_limit=args.sample_limit,
        force=bool(args.force),
        skip_existing=bool(args.skip_existing),
        recursive=bool(args.recursive),
        model_name=args.model,
        ctx_id=int(args.ctx_id),
        det_size=det_size,
        review_dir_name=args.review_dir_name,
        min_face_score=max(0.0, min(1.0, float(args.min_face_score))),
        min_face_area_ratio=max(0.0, float(args.min_face_area_ratio)),
        ocr_watermarks=bool(args.ocr_watermarks),
        report_all=bool(args.report_all),
    )


def run_spiritflix_library_smart_rescan(
    config: OrganizerConfig,
    *,
    confirmed_by: str = "Britton",
    smart_accept_limit: int = 0,
    smart_rescan_model_limit: int = 0,
    smart_rescan_video_limit: int = 0,
) -> dict[str, Any]:
    if not config.apply:
        raise RuntimeError("--spiritflix-library-smart-rescan requires --apply")

    started_at = utc_now()
    write_smart_rescan_status(
        {
            "status": "running",
            "phase": "backup",
            "phaseLabel": "Backing up current face metadata",
            "startedAt": started_at,
            "progress": {"total": 4, "completed": 0, "percent": 0},
            "currentItem": {"kind": "system", "name": "Face Organizer backup"},
        }
    )
    backup_root = backup_state(config, include_videos=False)
    write_smart_rescan_status(
        {
            "phase": "verify_models",
            "phaseLabel": "Verifying existing model registry",
            "progress": {"total": 4, "completed": 1, "percent": 25},
            "currentItem": {"kind": "system", "name": "Model registry"},
        }
    )
    verification_summary = verify_performers(config, enable_online=False, organize=False)
    write_smart_rescan_status(
        {
            "phase": "select_face_pictures",
            "phaseLabel": "Selecting best existing model face pictures",
            "progress": {"total": 4, "completed": 2, "percent": 50},
            "currentItem": {"kind": "system", "name": "Enrollment candidates"},
        }
    )
    candidate_group_limit = smart_rescan_model_limit if smart_rescan_model_limit > 0 else None
    candidates_payload = generate_enrollment_candidates(config, max_groups=candidate_group_limit, missing_only=True)
    known = known_db_summary(config.db_dir)
    known_keys: set[str] = set()
    for performer in known.get("performers", []):
        if not isinstance(performer, dict):
            continue
        known_keys.add(normalize_identity_key(str(performer.get("id") or "")))
        known_keys.add(normalize_identity_key(str(performer.get("name") or "")))
        known_keys.update(normalize_identity_key(str(alias)) for alias in performer.get("aliases", []) if alias)

    groups = [
        group
        for group in candidates_payload.get("groups", [])
        if isinstance(group, dict) and normalize_identity_key(str(group.get("name") or "")) in known_keys
    ]
    if smart_accept_limit > 0:
        groups = groups[:smart_accept_limit]

    accepted: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for group in groups:
        performer_name = str(group.get("name") or "").strip()
        if not performer_name:
            continue
        write_smart_rescan_status(
            {
                "phase": "select_face_pictures",
                "phaseLabel": "Selecting best existing model face pictures",
                "currentItem": {"kind": "model", "name": performer_name},
                "modelProgress": {
                    "total": len(groups),
                    "completed": len(accepted) + len(skipped),
                    "accepted": len(accepted),
                    "skipped": len(skipped),
                },
            }
        )
        try:
            result = smart_accept_best_crops(
                config,
                {
                    "performer_name": performer_name,
                    "confirmation": performer_name,
                    "confirmed_by": confirmed_by,
                },
            )
            accepted.append(
                {
                    "performer_name": performer_name,
                    "selection_count": int(result.get("selection_count") or 0),
                }
            )
        except Exception as exc:
            skipped.append({"performer_name": performer_name, "reason": str(exc)})

    model_source_dir = config.source_dir / "models"
    rescan_source_dir = model_source_dir if model_source_dir.exists() else config.source_dir
    video_batch_limit = smart_rescan_video_limit if smart_rescan_video_limit > 0 else config.sample_limit
    rescan_config = dataclasses.replace(
        config,
        source_dir=rescan_source_dir,
        force=True,
        skip_existing=False,
        frame_count=max(config.frame_count, ENROLLMENT_SCAN_FRAMES_PER_VIDEO),
        sample_limit=video_batch_limit,
    )
    scanned_records = scan(rescan_config, status_phase="rescanning_videos")
    write_smart_rescan_status(
        {
            "phase": "refresh_outputs",
            "phaseLabel": "Refreshing model previews and reports",
            "progress": {"total": 4, "completed": 3, "percent": 75},
            "currentItem": {"kind": "system", "name": "SpiritFlix model previews"},
        }
    )
    refresh_config = dataclasses.replace(config, force=True, skip_existing=False)
    generate_report(refresh_config)
    generate_enrollment_queue_page(refresh_config, refresh_stale=False)
    enrolled_payload = generate_enrolled_page(refresh_config, refresh_recommendations=False)
    gallery_payload = generate_gallery_page(refresh_config)
    generate_known_db_audit_page(refresh_config)

    summary = {
        "schema": "spiritflix-library-smart-rescan/v1",
        "started_at": started_at,
        "completed_at": utc_now(),
        "source_dir": str(config.source_dir),
        "video_scan_source_dir": str(rescan_source_dir),
        "video_batch_limit": video_batch_limit,
        "backup_root": str(backup_root),
        "verification_summary": verification_summary,
        "candidate_groups": len(candidates_payload.get("groups", []) or []),
        "candidate_group_limit": candidate_group_limit,
        "existing_model_groups_checked": len(groups),
        "smart_accepts": accepted,
        "smart_accept_skips": skipped[:100],
        "videos_scanned": len(scanned_records),
        "enrolled_summary": enrolled_payload.get("summary", {}),
        "gallery_summary": gallery_payload.get("summary", {}),
        "thresholds": {"auto": HIGH_CONFIDENCE, "review": POSSIBLE_CONFIDENCE},
        "applied": True,
    }
    summary_path = config.report_path.with_name("spiritflix_library_smart_rescan_summary.json")
    json_dump(summary_path, summary)
    write_smart_rescan_status(
        {
            "status": "completed",
            "phase": "completed",
            "phaseLabel": "Smart scan completed",
            "completedAt": summary["completed_at"],
            "progress": {"total": 4, "completed": 4, "percent": 100},
            "currentItem": {"kind": "system", "name": "Complete"},
            "summaryPath": str(summary_path),
            "summary": summary,
        }
    )
    return {**summary, "summary_path": str(summary_path)}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    setup_logging(args.verbose)
    config = make_config(args)
    db = KnownPerformersDB(config.db_dir)
    if args.init_db:
        db.ensure()
        logging.info("Initialized known performers DB at %s", config.db_dir)
        return 0
    if args.backup_state:
        if not config.apply:
            logging.info("dry-run: would back up state under %s", config.backup_dir)
            if args.backup_videos:
                logging.info("dry-run: would also copy selected videos because --backup-videos was passed")
            return 0
        backup_state(config, include_videos=config.backup_videos)
        return 0
    if args.report:
        generate_report(config)
        generate_enrollment_queue_page(config)
        generate_enrolled_page(config)
        generate_gallery_page(config)
        generate_known_db_audit_page(config)
        full_config = dataclasses.replace(config, report_path=config.report_path.with_name("face_verification_full_audit.html"), report_all=True)
        generate_report(full_config)
        return 0
    if args.enrollment_queue:
        generate_enrollment_queue_page(config, refresh_stale=False)
        return 0
    if args.enrolled_page:
        generate_enrolled_page(config)
        generate_gallery_page(config)
        return 0
    if args.gallery_page:
        generate_gallery_page(config)
        return 0
    if args.known_db_audit_page:
        generate_known_db_audit_page(config)
        return 0
    if args.organizer_quick_refresh:
        refresh_organizer_pages(config, refresh_stale_enrollment=False)
        return 0
    if args.generate_enrollment_candidates:
        payload = generate_enrollment_candidates(
            config,
            target_name=str(args.enrollment_target or "") or None,
        )
        print(json.dumps(payload.get("summary", {}), indent=2, ensure_ascii=False))
        return 0
    if args.serve_review:
        serve_review(config, str(args.host), int(args.port))
        return 0
    if args.scan_video:
        meta = scan_single_video(config, args.scan_video)
        print(json.dumps({"video_path": meta.get("video_path"), "performers": meta.get("performers", [])}, indent=2, ensure_ascii=False))
        return 0
    if args.enrich_metadata:
        if config.apply:
            backup_state(config, include_videos=False)
        enrich_metadata(config, enable_online=bool(args.online_metadata))
        return 0
    if args.rename_plan:
        if config.apply:
            backup_state(config, include_videos=False)
        write_rename_plan(config)
        return 0
    if args.backfill_review_frames:
        if config.apply:
            backup_state(config, include_videos=False)
        backfill_review_frames(config, enable_online=bool(args.online_metadata))
        return 0
    if args.verify_performers:
        if config.apply:
            backup_state(config, include_videos=False)
        summary = verify_performers(config, enable_online=bool(args.online_metadata))
        logging.info("Performer verification summary: %s", summary)
        return 0
    if args.audit_known_db:
        summary = audit_known_db(config)
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0
    if args.spiritflix_library_smart_rescan:
        summary = run_spiritflix_library_smart_rescan(
            config,
            confirmed_by=str(args.confirmed_by or "Britton"),
            smart_accept_limit=max(0, int(args.smart_accept_limit or 0)),
            smart_rescan_model_limit=max(0, int(args.smart_rescan_model_limit or 0)),
            smart_rescan_video_limit=max(0, int(args.smart_rescan_video_limit or 0)),
        )
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0
    if args.record_correction:
        if not args.sidecar:
            raise SystemExit("--record-correction requires --sidecar")
        sidecar_path = sidecar_record_path(args.sidecar)
        store_manual_correction(
            config,
            sidecar_path,
            args.record_correction,
            corrected_by=str(args.corrected_by or ""),
            belongs_to_existing=bool(args.belongs_to_existing),
        )
        return 0
    if args.confirm_correction:
        if not args.sidecar:
            raise SystemExit("--confirm-correction requires --sidecar")
        confirm_manual_correction(config, sidecar_record_path(args.sidecar), confirmed_by=str(args.confirmed_by or ""))
        return 0
    if args.organize:
        if not config.apply:
            logging.info("dry-run: --organize requires --apply to move files; showing planned destinations only")
        organize_videos(config)
        return 0
    if args.add_performer:
        if not args.face_image:
            raise SystemExit("--add-performer requires --face-image")
        add_performer_from_image(
            config,
            args.add_performer,
            args.face_image,
            aliases=[str(item) for item in args.alias or []],
            profile_handles=parse_profile_handles(args.profile_handle),
            profile_urls=[str(item) for item in args.profile_url or []],
            confirmed_by=str(args.confirmed_by or ""),
        )
        return 0
    if config.apply:
        backup_state(config, include_videos=False)
    scan(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
