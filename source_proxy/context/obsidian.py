from __future__ import annotations

import os
import re
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


DEFAULT_INCLUDE_GLOBS = "*.md"
DEFAULT_EXCLUDE_GLOBS = ".obsidian/**, private/**, secrets/**, archive/**"
DEFAULT_MAX_NOTES = 8
DEFAULT_MAX_CHARS_PER_NOTE = 1200


@dataclass(frozen=True)
class ObsidianContextConfig:
    enabled: bool
    vault_path: str
    include_globs: tuple[str, ...]
    exclude_globs: tuple[str, ...]
    max_notes: int
    max_chars_per_note: int


def obsidian_context_config_from_env() -> ObsidianContextConfig:
    return ObsidianContextConfig(
        enabled=_env_true("OBSIDIAN_CONTEXT_ENABLED"),
        vault_path=os.getenv("OBSIDIAN_VAULT_PATH", "").strip(),
        include_globs=_split_globs(os.getenv("OBSIDIAN_INCLUDE_GLOBS", DEFAULT_INCLUDE_GLOBS)),
        exclude_globs=_split_globs(os.getenv("OBSIDIAN_EXCLUDE_GLOBS", DEFAULT_EXCLUDE_GLOBS)),
        max_notes=_bounded_int(os.getenv("OBSIDIAN_MAX_NOTES", ""), DEFAULT_MAX_NOTES, 1, 25),
        max_chars_per_note=_bounded_int(
            os.getenv("OBSIDIAN_MAX_CHARS_PER_NOTE", ""),
            DEFAULT_MAX_CHARS_PER_NOTE,
            200,
            8000,
        ),
    )


def obsidian_context_diagnostics(
    config: ObsidianContextConfig | None = None,
) -> dict[str, Any]:
    cfg = config or obsidian_context_config_from_env()
    return {
        "obsidian_context_enabled": cfg.enabled,
        "obsidian_context_used": False,
        "obsidian_notes_considered": 0,
        "obsidian_notes_selected": 0,
        "obsidian_context_chars": 0,
        "obsidian_context_paths": [],
        "obsidian_status": _status_for_config(cfg),
        "obsidian_vault_path_configured": bool(cfg.vault_path),
        "obsidian_include_globs": list(cfg.include_globs),
        "obsidian_exclude_globs": list(cfg.exclude_globs),
        "obsidian_max_notes": cfg.max_notes,
        "obsidian_max_chars_per_note": cfg.max_chars_per_note,
        "obsidian_read_only": True,
    }


def query_obsidian_context(
    task: str,
    *,
    config: ObsidianContextConfig | None = None,
) -> dict[str, Any]:
    cfg = config or obsidian_context_config_from_env()
    diagnostics = obsidian_context_diagnostics(cfg)
    if not cfg.enabled:
        return {"status": "disabled", "notes": [], "diagnostics": diagnostics}
    if not cfg.vault_path:
        diagnostics["obsidian_status"] = "missing_vault_path"
        return {"status": "missing_vault_path", "notes": [], "diagnostics": diagnostics}

    vault = Path(cfg.vault_path).expanduser()
    try:
        resolved_vault = vault.resolve()
    except OSError:
        diagnostics["obsidian_status"] = "vault_unavailable"
        return {"status": "vault_unavailable", "notes": [], "diagnostics": diagnostics}
    if not resolved_vault.exists() or not resolved_vault.is_dir():
        diagnostics["obsidian_status"] = "vault_unavailable"
        return {"status": "vault_unavailable", "notes": [], "diagnostics": diagnostics}

    candidates = list(_iter_candidate_notes(resolved_vault, cfg))
    diagnostics["obsidian_notes_considered"] = len(candidates)
    scored = [
        _scored_note(path, resolved_vault, task, cfg.max_chars_per_note)
        for path in candidates
    ]
    selected = [
        note
        for note in sorted(scored, key=lambda item: (-item["score"], item["path"]))
        if note["score"] > 0
    ][: cfg.max_notes]

    diagnostics["obsidian_context_used"] = bool(selected)
    diagnostics["obsidian_notes_selected"] = len(selected)
    diagnostics["obsidian_context_chars"] = sum(len(str(note["safe_excerpt"])) for note in selected)
    diagnostics["obsidian_context_paths"] = [str(note["path"]) for note in selected]
    diagnostics["obsidian_status"] = "used" if selected else "no_relevant_notes"

    public_notes = [
        {
            "title": note["title"],
            "path": note["path"],
            "safe_excerpt": note["safe_excerpt"],
            "why_matched": note["why_matched"],
            "char_estimate": len(str(note["safe_excerpt"])),
            "used_in_prompt_context": bool(selected),
        }
        for note in selected
    ]
    return {"status": diagnostics["obsidian_status"], "notes": public_notes, "diagnostics": diagnostics}


def _env_true(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _split_globs(value: str) -> tuple[str, ...]:
    globs = tuple(item.strip().replace("\\", "/") for item in value.split(",") if item.strip())
    return globs or (DEFAULT_INCLUDE_GLOBS,)


def _bounded_int(value: str, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(parsed, maximum))


def _status_for_config(config: ObsidianContextConfig) -> str:
    if not config.enabled:
        return "disabled"
    if not config.vault_path:
        return "missing_vault_path"
    return "configured_not_scanned"


def _iter_candidate_notes(vault: Path, config: ObsidianContextConfig):
    for path in vault.rglob("*.md"):
        if not path.is_file():
            continue
        rel = path.relative_to(vault).as_posix()
        if _matches_any(rel, config.exclude_globs):
            continue
        if not _matches_any(rel, config.include_globs):
            continue
        yield path


def _matches_any(rel_path: str, patterns: tuple[str, ...]) -> bool:
    normalized = rel_path.replace("\\", "/")
    name = normalized.rsplit("/", 1)[-1]
    for pattern in patterns:
        if fnmatch(normalized, pattern) or fnmatch(name, pattern):
            return True
        if pattern.endswith("/**"):
            prefix = pattern[:-3].strip("/")
            if normalized == prefix or normalized.startswith(f"{prefix}/"):
                return True
    return False


def _scored_note(
    path: Path,
    vault: Path,
    task: str,
    max_chars_per_note: int,
) -> dict[str, Any]:
    rel = path.relative_to(vault).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    terms = _query_terms(task)
    haystack = f"{rel}\n{text}".lower()
    matches = [term for term in terms if term in haystack]
    return {
        "title": _note_title(path, text),
        "path": rel,
        "safe_excerpt": _safe_excerpt(text, terms, max_chars_per_note),
        "score": len(matches),
        "why_matched": f"Matched: {', '.join(matches[:8])}" if matches else "No query term match.",
    }


def _query_terms(task: str) -> list[str]:
    stop = {
        "about",
        "after",
        "context",
        "from",
        "given",
        "into",
        "note",
        "notes",
        "obsidian",
        "please",
        "read",
        "task",
        "that",
        "this",
        "with",
    }
    terms = []
    for term in re.findall(r"[A-Za-z0-9_-]{3,}", task.lower()):
        if term not in stop and term not in terms:
            terms.append(term)
    return terms


def _note_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or path.stem
    return path.stem


def _safe_excerpt(text: str, terms: list[str], max_chars: int) -> str:
    cleaned = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[redacted-email]", text)
    cleaned = re.sub(r"sk-[A-Za-z0-9_-]{12,}", "[redacted-token]", cleaned)
    cleaned = re.sub(r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*\S+", r"\1=[redacted]", cleaned)
    lower = cleaned.lower()
    start = 0
    for term in terms:
        index = lower.find(term)
        if index >= 0:
            start = max(0, index - 160)
            break
    excerpt = cleaned[start : start + max_chars].strip()
    return " ".join(excerpt.split())
