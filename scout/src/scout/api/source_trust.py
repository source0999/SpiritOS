from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class SourceTrust:
    trust_label: str
    trust_tier: str
    label: str
    category: str


_KNOWN_PROJECT_BLOGS = {
    "blog.python.org": "Python blog feed",
}

_READABLE_TRUST_LABELS = {
    "official_project_blog": "Official project blog",
    "official_github_repo": "Official GitHub repo",
    "official_docs": "Official docs",
    "maintainer_source": "Maintainer source",
    "allowlisted_source": "Allowlisted source",
    "unknown_source": "Unknown source",
}

_TRUST_TIERS = {
    "official_project_blog": "official",
    "official_github_repo": "official",
    "official_docs": "official",
    "maintainer_source": "maintainer",
    "allowlisted_source": "allowlisted",
    "unknown_source": "unknown",
}


def _github_label(source_uri: str) -> str:
    rest = source_uri.removeprefix("github://")
    parts = [part for part in rest.split("/") if part]
    if len(parts) >= 2:
        suffix = f" {parts[2]}" if len(parts) >= 3 else ""
        return f"{parts[0]}/{parts[1]}{suffix}"
    return source_uri


def _url_label(source_uri: str) -> str:
    parsed = urlparse(source_uri)
    host = parsed.hostname or source_uri
    if host in _KNOWN_PROJECT_BLOGS:
        return _KNOWN_PROJECT_BLOGS[host]
    if parsed.path and parsed.path not in {"", "/"}:
        return f"{host}{parsed.path}".rstrip("/")
    return host


def source_label(source_uri: str | None) -> str:
    if not source_uri:
        return "Unknown source"
    if source_uri.startswith("github://"):
        return _github_label(source_uri)
    if source_uri.startswith(("https://", "http://")):
        return _url_label(source_uri)
    return source_uri


def classify_source(source_uri: str | None) -> SourceTrust:
    if not source_uri:
        category = "unknown_source"
        return SourceTrust(
            trust_label=_READABLE_TRUST_LABELS[category],
            trust_tier=_TRUST_TIERS[category],
            label="Unknown source",
            category=category,
        )

    category = "unknown_source"
    if source_uri.startswith("github://"):
        parts = [part for part in source_uri.removeprefix("github://").split("/") if part]
        category = "official_github_repo" if len(parts) >= 2 else "unknown_source"
    elif source_uri.startswith(("https://", "http://")):
        parsed = urlparse(source_uri)
        host = parsed.hostname or ""
        path = parsed.path or ""
        if host in _KNOWN_PROJECT_BLOGS:
            category = "official_project_blog"
        elif host.startswith("docs.") or "/docs" in path:
            category = "official_docs"
        elif host:
            category = "allowlisted_source"

    return SourceTrust(
        trust_label=_READABLE_TRUST_LABELS[category],
        trust_tier=_TRUST_TIERS[category],
        label=source_label(source_uri),
        category=category,
    )
