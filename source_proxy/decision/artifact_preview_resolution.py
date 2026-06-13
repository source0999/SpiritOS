from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PREVIEW_RESOLUTION_VERSION = "source-proxy-artifact-preview-resolution-v0.2"


@dataclass(frozen=True)
class ArtifactPreviewResolution:
    status: str
    selected_path: str
    selection_reason: str
    reason_codes: list[str]
    candidate_paths: list[str]
    explicit_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_artifact_preview_path(
    *,
    workspace: Path,
    prompt: str = "",
    evidence_packet: dict[str, Any] | None = None,
    receipt: dict[str, Any] | None = None,
    score: dict[str, Any] | None = None,
) -> ArtifactPreviewResolution:
    """Select a browser-viewable generated artifact without assuming index.html."""

    root = workspace.resolve()
    explicit = _explicit_preview_path(evidence_packet or {}, receipt or {}, score or {})
    html_files = _html_files(root)
    candidates = [_relative(root, path) for path in html_files]
    ignored_explicit = ""

    if explicit:
        explicit_path = _resolve_under_workspace(root, explicit)
        if explicit_path and explicit_path.is_file() and explicit_path.suffix.lower() in {".html", ".htm"}:
            return ArtifactPreviewResolution(
                status="ready",
                selected_path=str(explicit_path),
                selection_reason="explicit_preview_path",
                reason_codes=["explicit_preview_path_selected"],
                candidate_paths=candidates,
                explicit_path=explicit,
            )
        ignored_explicit = explicit

    index = root / "index.html"
    if index.is_file():
        return ArtifactPreviewResolution(
            status="ready",
            selected_path=str(index),
            selection_reason="index_html_present_after_invalid_explicit" if ignored_explicit else "index_html_present",
            reason_codes=["index_html_selected", *(["explicit_preview_path_invalid_fallback_used"] if ignored_explicit else [])],
            candidate_paths=candidates,
            explicit_path=ignored_explicit,
        )

    if len(html_files) == 1:
        return ArtifactPreviewResolution(
            status="ready",
            selected_path=str(html_files[0]),
            selection_reason="single_html_entrypoint_after_invalid_explicit" if ignored_explicit else "single_html_entrypoint",
            reason_codes=["single_html_entrypoint_selected", *(["explicit_preview_path_invalid_fallback_used"] if ignored_explicit else [])],
            candidate_paths=candidates,
            explicit_path=ignored_explicit,
        )

    if len(html_files) > 1:
        matches = _semantic_matches(html_files, prompt)
        if len(matches) == 1:
            return ArtifactPreviewResolution(
                status="ready",
                selected_path=str(matches[0]),
                selection_reason="semantic_prompt_slug_match_after_invalid_explicit" if ignored_explicit else "semantic_prompt_slug_match",
                reason_codes=["semantic_prompt_slug_match_selected", *(["explicit_preview_path_invalid_fallback_used"] if ignored_explicit else [])],
                candidate_paths=candidates,
                explicit_path=ignored_explicit,
            )
        return ArtifactPreviewResolution(
            status="artifact_entrypoint_ambiguous",
            selected_path="",
            selection_reason="multiple_html_entrypoints_no_unique_match_after_invalid_explicit" if ignored_explicit else "multiple_html_entrypoints_no_unique_match",
            reason_codes=["artifact_entrypoint_ambiguous", *(["explicit_preview_path_invalid"] if ignored_explicit else [])],
            candidate_paths=candidates,
            explicit_path=ignored_explicit,
        )

    return ArtifactPreviewResolution(
        status="missing_preview_artifact",
        selected_path="",
        selection_reason="no_browser_viewable_html_artifact_after_invalid_explicit" if ignored_explicit else "no_browser_viewable_html_artifact",
        reason_codes=["missing_preview_artifact", *(["explicit_preview_path_invalid"] if ignored_explicit else [])],
        candidate_paths=candidates,
        explicit_path=ignored_explicit,
    )


def _explicit_preview_path(
    evidence_packet: dict[str, Any],
    receipt: dict[str, Any],
    score: dict[str, Any],
) -> str:
    keys = ("selected_preview_path", "preview_path", "preview_file", "artifact_preview_path")
    for source in (evidence_packet, receipt, score):
        for key in keys:
            value = source.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    paths = score.get("openable_homepage_paths")
    if isinstance(paths, list) and paths and isinstance(paths[0], str):
        return paths[0]
    return ""


def _html_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path.resolve()
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".html", ".htm"} and ".git" not in path.parts
    )


def _semantic_matches(paths: list[Path], prompt: str) -> list[Path]:
    prompt_tokens = set(_tokens(prompt)) - {"make", "create", "build", "simple", "a", "an", "the", "app", "demo"}
    matches = []
    for path in paths:
        path_tokens = set(_tokens(path.stem))
        if prompt_tokens and (prompt_tokens <= path_tokens or len(prompt_tokens & path_tokens) >= min(2, len(prompt_tokens))):
            matches.append(path)
    return matches


def _tokens(value: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", value.lower()) if token]


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _resolve_under_workspace(root: Path, value: str) -> Path | None:
    raw = Path(value)
    path = raw if raw.is_absolute() else root / raw
    try:
        resolved = path.resolve()
        resolved.relative_to(root)
    except (OSError, ValueError):
        return None
    return resolved
