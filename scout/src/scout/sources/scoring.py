from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from urllib.parse import urlparse

from scout.api.source_trust import classify_source
from scout.storage.db import open_connection


SPAM_PATTERNS = (
    "casino",
    "crypto-airdrop",
    "free-money",
    "loan",
    "porn",
    "seo",
    "viagra",
)
KNOWN_ECOSYSTEM_DOMAINS = {
    "blog.python.org",
    "docs.python.org",
    "fastapi.tiangolo.com",
    "github.com",
    "pypi.org",
    "www.typescriptlang.org",
}
OFFICIAL_SOURCE_DOMAINS = {
    "blog.python.org",
    "docs.python.org",
    "fastapi.tiangolo.com",
    "github.com",
    "pypi.org",
    "www.python.org",
    "www.typescriptlang.org",
}
KNOWN_GITHUB_ORGS = {
    "anthropics",
    "fastapi",
    "microsoft",
    "openai",
    "pallets",
    "python",
    "tiangolo",
}
TOPIC_ANCHORS = {
    "agent",
    "agents",
    "docker",
    "embeddings",
    "fastapi",
    "llm",
    "python",
    "sqlite",
    "typescript",
}


@dataclass(frozen=True)
class SourceScore:
    confidence_score: float
    status: str
    trust_label: str
    trust_tier: str
    recommendation: str
    reason_codes: list[str]
    explanation: str


def score_candidate(
    db_path: Path,
    *,
    canonical_uri: str,
    source_kind: str,
    discovered_from_uri: str | None = None,
    title: str | None = None,
    snippet: str | None = None,
    published_at: str | None = None,
) -> SourceScore:
    trust = classify_source(canonical_uri)
    reason_codes: list[str] = []
    score = 0.5

    if _is_blocked(db_path, canonical_uri):
        return SourceScore(
            confidence_score=0.0,
            status="blocked",
            trust_label=trust.trust_label,
            trust_tier=trust.trust_tier,
            recommendation="Blocked source. Do not review for activation.",
            reason_codes=["blocked_source"],
            explanation="This source matches a manual block entry.",
        )

    if _is_active(db_path, canonical_uri):
        return SourceScore(
            confidence_score=1.0,
            status="approved",
            trust_label=trust.trust_label,
            trust_tier=trust.trust_tier,
            recommendation="Already active in the source registry.",
            reason_codes=["already_active"],
            explanation="This source is already approved and active.",
        )

    if _canonical_valid(canonical_uri):
        score += 0.08
        reason_codes.append("canonical_uri_valid")
    else:
        score -= 0.2
        reason_codes.append("canonical_uri_invalid")

    if canonical_uri.startswith("https://") or canonical_uri.startswith("github://"):
        score += 0.08
        reason_codes.append("https_or_internal_scheme")
    else:
        score -= 0.2
        reason_codes.append("https_required")

    if _has_spam_pattern(canonical_uri):
        score -= 0.45
        reason_codes.append("spam_pattern_detected")

    if canonical_uri.startswith("github://"):
        score += 0.12
        reason_codes.append("github_repo_detected")
        owner = canonical_uri.removeprefix("github://").split("/", 1)[0]
        if owner in KNOWN_GITHUB_ORGS:
            score += 0.18
            reason_codes.append("official_repo_pattern")

    parsed = urlparse(canonical_uri)
    host = parsed.hostname or ""
    path = parsed.path.lower()
    evidence_text = " ".join(
        part for part in [canonical_uri, title or "", snippet or ""] if part
    ).lower()
    if host.startswith("docs.") or "/docs" in path:
        score += 0.1
        reason_codes.append("official_docs_pattern")
    if "changelog" in path or "release" in path:
        score += 0.1
        reason_codes.append("release_notes_pattern")
    if host in KNOWN_ECOSYSTEM_DOMAINS:
        score += 0.1
        reason_codes.append("known_ecosystem_match")
    if host in OFFICIAL_SOURCE_DOMAINS:
        score += 0.08
        reason_codes.append("official_domain_match")
    topic_hits = _topic_anchor_hits(evidence_text)
    if topic_hits:
        score += 0.08
        reason_codes.append("matches_topic_anchor")
    if topic_hits >= 2:
        score += 0.06
        reason_codes.append("topic_anchor_density")
    if discovered_from_uri and _is_active_discovery_source(discovered_from_uri):
        score += 0.08
        reason_codes.append("linked_from_active_source")
    if source_kind in {"docs_page", "github_repo", "changelog", "release_feed"}:
        score += 0.05
        reason_codes.append("metadata_sufficient")
    if title or snippet:
        score += 0.04
        reason_codes.append("source_metadata_quality")
    if published_at and _is_fresh_source(published_at):
        score += 0.04
        reason_codes.append("fresh_source")

    if not reason_codes:
        reason_codes.append("low_evidence")

    confidence = max(0.0, min(1.0, round(score, 3)))
    status = _status_for_score(confidence)
    return SourceScore(
        confidence_score=confidence,
        status=status,
        trust_label=trust.trust_label,
        trust_tier=trust.trust_tier,
        recommendation=_recommendation_for_status(status),
        reason_codes=list(dict.fromkeys(reason_codes)),
        explanation=_explanation_for_status(status),
    )


def _status_for_score(score: float) -> str:
    if score >= 0.9:
        return "recommended"
    if score >= 0.7:
        return "needs_review"
    return "stored"


def _recommendation_for_status(status: str) -> str:
    if status == "recommended":
        return "Recommended for manual review before activation."
    if status == "needs_review":
        return "Needs human review before activation."
    if status == "stored":
        return "Stored as low-priority evidence. Do not promote aggressively."
    return "Review source before activation."


def _explanation_for_status(status: str) -> str:
    if status == "recommended":
        return "Deterministic source checks found strong relevance and trust signals."
    if status == "needs_review":
        return "Deterministic source checks found useful but incomplete evidence."
    if status == "stored":
        return "Deterministic source checks found limited evidence for this source."
    return "Deterministic source checks require manual review."


def _canonical_valid(canonical_uri: str) -> bool:
    if canonical_uri.startswith("github://"):
        return bool(re.match(r"^github://[^/\s]+/[^/\s]+$", canonical_uri))
    parsed = urlparse(canonical_uri)
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname)


def _has_spam_pattern(canonical_uri: str) -> bool:
    lowered = canonical_uri.lower()
    return any(pattern in lowered for pattern in SPAM_PATTERNS)


def _topic_anchor_hits(text: str) -> int:
    return sum(1 for anchor in TOPIC_ANCHORS if anchor in text)


def _is_active_discovery_source(discovered_from_uri: str) -> bool:
    return not discovered_from_uri.startswith("search://")


def _is_fresh_source(published_at: str) -> bool:
    try:
        parsed = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).days
    return 0 <= age_days <= 730


def _is_blocked(db_path: Path, canonical_uri: str) -> bool:
    conn = open_connection(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM blocked_sources WHERE canonical_uri = ?",
            (canonical_uri,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def _is_active(db_path: Path, canonical_uri: str) -> bool:
    conn = open_connection(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM source_registry WHERE canonical_uri = ? AND status = 'active'",
            (canonical_uri,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()
