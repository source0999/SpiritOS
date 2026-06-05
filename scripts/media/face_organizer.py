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
import html
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
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
HIGH_CONFIDENCE = 0.80
POSSIBLE_CONFIDENCE = 0.55
DEFAULT_SOURCE = os.environ.get("FACE_ORGANIZER_SOURCE", "/mnt/spirit-8tb/media/other")
DEFAULT_DB = os.environ.get("FACE_ORGANIZER_DB", "scripts/media/known_performers")
DEFAULT_REPORT = os.environ.get("FACE_ORGANIZER_REPORT", "scripts/media/face_verification_report.html")
DEFAULT_BACKUP_DIR = os.environ.get("FACE_ORGANIZER_BACKUP_DIR", "scripts/media/backups")
DEFAULT_RENAME_MANIFEST = os.environ.get("FACE_ORGANIZER_RENAME_MANIFEST", "scripts/media/rename_plan.json")
DEFAULT_ORGANIZE_MANIFEST = os.environ.get("FACE_ORGANIZER_ORGANIZE_MANIFEST", "scripts/media/organize_manifest.json")
DEFAULT_MODEL = os.environ.get("FACE_ORGANIZER_MODEL", "buffalo_l")
MODEL_VERSION = f"insightface:{DEFAULT_MODEL}"
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
        candidates.append(
            {
                "name": name,
                "source": "filename",
                "confidence": round(min(score, 0.75), 2),
                "raw": raw,
            }
        )
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
        "ambune": "Amburne",
        "amburne": "Amburne",
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
        "brendatril": "Brenda Trindade",
        "brendatri": "Brenda Trindade",
        "brendatrii": "Brenda Trindade",
        "brendatrindadee": "Brenda Trindade",
        "aaliyahyasan": "Aaliyah Yasan",
        "thatbritishgirl": "Aaliyah Yasan",
        "thatbritishgirlxdirtyspringbok": "Aaliyah Yasan",
        "kinkykttn": "Kinkykttn",
        "kinkyktn": "Kinkykttn",
        "alannasworlx": "Alannasworldx",
        "alannasworldx": "Alannasworldx",
        "olenfromalannasworldx": "Alannasworldx",
        "tolenfromalannasworldx": "Alannasworldx",
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


def watermark_candidates(ocr_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    patterns = [
        r"(?:onlyfans|lyfans|fansly|fans|of)[\s.:;]*c[o0][mnrli]{0,2}[/\\:|]+([A-Za-z0-9_.-]{5,})",
        r"(?:^|\b)c[o0][mnrli]{0,2}[/\\:|]+([A-Za-z0-9_.-]{5,})",
        r"(?:stolen\s+from|leaked\s+from|leaked\s+by|from)\s+([A-Za-z0-9_.-]{4,})",
        r"@([A-Za-z0-9_.-]{4,})",
    ]
    for result in ocr_results:
        text = str(result.get("text", ""))
        region = str(result.get("region") or "full")
        score = float(result.get("confidence", 0.6))
        for pattern in patterns:
            if ("telegram" in text.lower() or "t.me/" in text.lower()) and pattern.startswith("@"):
                continue
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                raw = match.group(1)
                raw = re.sub(r"[^A-Za-z0-9_.-].*$", "", raw).strip("._-")
                name = split_handle_words(raw)
                if is_bad_candidate_name(name, text) or name.lower() in seen:
                    continue
                seen.add(name.lower())
                profile_like = "com" in pattern or "from" in pattern
                confidence_cap = 0.9 if profile_like or region != "full" else 0.78
                candidates.append(
                    {
                        "name": name,
                        "source": "watermark_ocr",
                        "confidence": round(min(confidence_cap, score * 0.92), 2),
                        "raw": text,
                        "frame_path": result.get("frame_path"),
                        "region": region,
                    }
                )
        cleaned = normalize_candidate_name(text)
        if cleaned and cleaned.lower() not in seen and len(cleaned.split()) <= 3 and not is_bad_candidate_name(cleaned, text):
            seen.add(cleaned.lower())
            raw_text = text.strip()
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
            candidates.append(
                {
                    "name": cleaned,
                    "source": "watermark_ocr_text",
                    "confidence": round(min(confidence_cap, score * multiplier), 2),
                    "raw": text,
                    "frame_path": result.get("frame_path"),
                    "region": region,
                }
            )
    return candidates[:8]


def build_metadata_hints(video_path: Path, enable_online: bool, frame_paths: list[Path] | None = None, ocr_watermarks: bool = False) -> dict[str, Any]:
    filename_candidates = extract_filename_candidates(video_path)
    ocr_results = ocr_frame_text(frame_paths or []) if ocr_watermarks else []
    ocr_candidates = watermark_candidates(ocr_results)
    online_candidates: list[dict[str, Any]] = []
    if enable_online:
        for candidate in (ocr_candidates + filename_candidates)[:3]:
            online_candidates.extend(lookup_papi_candidates(candidate["name"]))
    all_candidates = ocr_candidates + filename_candidates + online_candidates
    all_candidates.sort(key=lambda item: float(item.get("confidence", 0)), reverse=True)
    return {
        "generated_at": utc_now(),
        "status": "candidate_hints_only",
        "candidate_names": all_candidates[:10],
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


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


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
            np.save(self.embeddings_path, self.embeddings)

    def load(self) -> None:
        self.ensure()
        self.index = load_json(self.index_path, {"performers": []})
        self.performer_map = load_json(self.map_path, {})
        try:
            self.embeddings = np.load(self.embeddings_path)
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

    def append_embedding(self, performer_id: str, embedding: np.ndarray) -> None:
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
        np.save(self.embeddings_path, self.embeddings.astype(np.float32))
        json_dump(self.map_path, self.performer_map)

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


def scan(config: OrganizerConfig) -> list[dict[str, Any]]:
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
    results: list[dict[str, Any]] = []
    for video_path in progress(videos, "face scan"):
        try:
            meta = scan_video(video_path, config, db, recognizer)
            results.append(meta)
            labels = ", ".join(item["label"] for item in meta["performers"])
            logging.info("%s -> %s", video_path.name, labels)
            if config.apply:
                json_dump(meta_path_for(video_path), meta)
                if config.write_nfo:
                    write_nfo(video_path, meta["performers"])
            else:
                logging.info("dry-run: would write %s", meta_path_for(video_path))
        except Exception as exc:
            logging.exception("Failed to scan %s: %s", video_path, exc)
    if not config.apply:
        logging.info("dry-run complete: no sidecars, crops, NFO files, or organization changes were written")
    return results


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
            actual_video_path = path.with_name(path.name.removesuffix(".face-meta.json"))
            if actual_video_path.exists():
                record["video_path"] = str(actual_video_path)
                record["path"] = str(actual_video_path)
            records.append(record)
        except Exception as exc:
            logging.warning("Could not read %s: %s", path, exc)
    return records


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
    return f'<button class="image-button" type="button" data-full="{safe_src}"><img src="{safe_src}" class="{css_class}" alt="{safe_alt}"></button>'


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


def generate_report(config: OrganizerConfig) -> None:
    records = collect_metadata(config.source_dir, config.recursive)
    attention = [record for record in records if record.get("verification_needed")]
    auto = [record for record in records if not record.get("verification_needed")]
    display_records = attention
    rows = []
    report_dir = config.report_path.parent
    for record in display_records:
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
        if hints:
            hint_badges = " ".join(
                f'<span class="hint">{html.escape(str(item.get("name", "")))} <small>{html.escape(str(item.get("source", "")))}</small></span>'
                for item in hints
            )
            hint_html = f'<div class="hints"><p>Metadata hints</p><div>{hint_badges}</div></div>'
            if first_name == "unknown performer":
                first_name = str(hints[0].get("name") or first_name)
        command = (
            f'python scripts/media/face_organizer.py --add-performer "{first_name}" '
            f'--face-image "<crop-path>" --apply'
        )
        rows.append(
            f"""
            <article class="video-card" data-status="{status}" data-name="{html.escape(' '.join(names).lower())}">
              <div class="card-head">
                <div>
                  <p class="status-text">{html.escape(status.replace('-', ' '))}</p>
                  <h2>{html.escape(Path(record.get('video_path', 'unknown')).name)}</h2>
                  <div class="badges">{badges}</div>
                  {identity_html}
                </div>
                <div class="metrics">
                  <div>{html.escape(str(record.get('faces_detected', 0)))} faces</div>
                  <div>{html.escape(str(record.get('processing_time_seconds', '?')))}s</div>
                </div>
              </div>
              {hint_html}
              <div class="frame-strip">{''.join(review_frames) or '<div class="empty-crop">No review frames saved yet. Rescan or run frame backfill.</div>'}</div>
              <div class="thumbs">{''.join(crops) or '<div class="empty-crop">No face crops saved for this video.</div>'}</div>
              <div class="actions">
                <code class="confirm">Confirm: {html.escape(command)}</code>
                <code class="unknown">Mark unknown: edit {html.escape(record.get('_meta_path', 'metadata'))}</code>
                <code class="edit">Edit name: update known_performers/index.json then rebuild</code>
              </div>
            </article>
            """
        )
    generated = utc_now()
    report_css = """
    * { box-sizing: border-box; }
    body { margin: 0; min-height: 100vh; background: #000; color: #f4f4f5; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
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
    .hints { margin-top: 1rem; border-top: 1px solid rgba(255,255,255,.08); padding-top: .75rem; }
    .resolved { margin-top: .75rem; }
    .hints p { margin-bottom: .5rem; color: #a1a1aa; font-size: .75rem; text-transform: uppercase; }
    .hint { display: inline-flex; align-items: baseline; gap: .35rem; margin: 0 .35rem .35rem 0; border-radius: 9999px; background: rgba(103,232,249,.1); color: #cffafe; padding: .25rem .6rem; font-size: .75rem; }
    .hint small { color: #67e8f9; }
    .actions { display: grid; gap: .5rem; margin-top: 1rem; }
    .actions code { border-radius: .25rem; padding: .75rem; font-size: .75rem; }
    .confirm { background: rgba(52,211,153,.1); color: #d1fae5; }
    .unknown { background: rgba(251,113,133,.1); color: #ffe4e6; }
    .edit { background: rgba(251,191,36,.1); color: #fef3c7; }
    .empty-report { border: 1px solid rgba(255,255,255,.1); border-radius: .5rem; background: #09090b; padding: 2rem; color: #a1a1aa; }
    .lightbox { position: fixed; inset: 0; display: none; align-items: center; justify-content: center; z-index: 100; background: rgba(0,0,0,.9); padding: 1rem; }
    .lightbox.is-open { display: flex; }
    .lightbox img { max-width: min(96vw, 1400px); max-height: 92vh; object-fit: contain; border-radius: .35rem; box-shadow: 0 24px 80px rgba(0,0,0,.8); }
    @media (min-width: 768px) {
      header { flex-direction: row; align-items: flex-end; justify-content: space-between; }
      .filters-inner { flex-direction: row; }
      .filters-inner select { width: 14rem; }
      .card-head { flex-direction: row; align-items: flex-start; justify-content: space-between; }
      .metrics { text-align: right; }
      .actions { grid-template-columns: repeat(3, minmax(0, 1fr)); }
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
        <h1>Verification Queue</h1>
        <p class="muted">Generated {html.escape(generated)} from {html.escape(str(config.source_dir))}</p>
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
    <section id="grid">{''.join(rows) or '<div class="empty-report">No videos need review. Auto-approved items have left this queue.</div>'}</section>
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
  </script>
</body>
</html>
"""
    config.report_path.parent.mkdir(parents=True, exist_ok=True)
    config.report_path.write_text(html_payload, encoding="utf-8")
    logging.info("Wrote verification report: %s", config.report_path)


def add_performer_from_image(config: OrganizerConfig, name: str, image_path: Path) -> None:
    if not config.apply:
        logging.info("dry-run: would add performer %r from %s", name, image_path)
        return
    if not image_path.exists():
        raise RuntimeError(f"Face image does not exist: {image_path}")
    db = KnownPerformersDB(config.db_dir)
    performer_id = db.add_performer(name)
    recognizer = InsightFaceRecognizer(config.model_name, config.ctx_id, config.det_size)
    faces = recognizer.detect(image_path)
    if not faces:
        raise RuntimeError(f"No face detected in {image_path}")
    best = max(faces, key=lambda face: float(getattr(face, "det_score", 0.0)))
    db.append_embedding(performer_id, np.asarray(best.embedding, dtype=np.float32))
    target_dir = db.faces_dir / performer_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{slugify(image_path.stem)}-{uuid.uuid4().hex[:8]}{image_path.suffix.lower() or '.jpg'}"
    shutil.copy2(image_path, target)
    logging.info("Added performer %s (%s) with sample %s", name, performer_id, target)


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
    parser.add_argument("--face-image", type=Path, help="face crop/image to use with --add-performer")
    parser.add_argument("--source", type=Path, default=Path(DEFAULT_SOURCE), help=f"media source directory (default: {DEFAULT_SOURCE})")
    parser.add_argument("--db", type=Path, default=Path(DEFAULT_DB), help=f"known performers DB directory (default: {DEFAULT_DB})")
    parser.add_argument("--report-path", type=Path, default=Path(DEFAULT_REPORT), help=f"HTML report path (default: {DEFAULT_REPORT})")
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
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"InsightFace model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--ctx-id", type=int, default=0, help="InsightFace ctx_id; 0 for first GPU, -1 for CPU")
    parser.add_argument("--det-size", default="640x640", help="detector size WIDTHxHEIGHT")
    parser.add_argument("--min-face-score", type=float, default=0.65, help="ignore weak detections below this score")
    parser.add_argument("--min-face-area-ratio", type=float, default=0.002, help="ignore tiny faces below this frame-area ratio")
    parser.add_argument("--ocr-watermarks", action=argparse.BooleanOptionalAction, default=True, help="read visible watermark/profile text from sampled frames")
    parser.add_argument("--review-dir-name", default=".face-review", help="directory beside videos for persisted crops/frames")
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
    )


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
    if args.organize:
        if not config.apply:
            logging.info("dry-run: --organize requires --apply to move files; showing planned destinations only")
        organize_videos(config)
        return 0
    if args.add_performer:
        if not args.face_image:
            raise SystemExit("--add-performer requires --face-image")
        add_performer_from_image(config, args.add_performer, args.face_image)
        return 0
    if config.apply:
        backup_state(config, include_videos=False)
    scan(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
