"""Deterministic injection heuristics over untrusted *content*, not model taxonomies.

The literal entity tag `injection_signal` is a reserved Scout marker. LLMs hallucinate it
on benign RSS; we strip it at synthesis unless the underlying source text matches these
patterns. Tier-1 uses the same patterns on packet narrative + optional artifact text.
"""

from __future__ import annotations

import re

CONTENT_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore (all )?(previous|prior) (instructions|prompts)", re.I),
    re.compile(r"you are now", re.I),
    re.compile(r"<\s*/?\s*(system|assistant|user)\s*>", re.I),
    re.compile(r"\bsystem:\s", re.I),
    re.compile(r"[\u200b\u200c\u200d\ufeff]"),
    re.compile(r"[A-Za-z0-9+/]{200,}={0,2}"),
]

RESERVED_ENTITY_TAG_INJECTION_SIGNAL = "injection_signal"


def untrusted_text_matches_content_injection(text: str) -> bool:
    if not text:
        return False
    return any(pattern.search(text) for pattern in CONTENT_INJECTION_PATTERNS)


def filter_entity_tags_reserved_injection_signal(
    entity_tags: list[str] | list[object] | None,
    *,
    source_text: str,
) -> list[str]:
    """Drop hallucinated `injection_signal` tags unless source text matches heuristics."""
    if entity_tags is None:
        return []
    coerced = [str(t) for t in entity_tags]
    if untrusted_text_matches_content_injection(source_text):
        return coerced
    return [
        t
        for t in coerced
        if t.strip().lower() != RESERVED_ENTITY_TAG_INJECTION_SIGNAL
    ]
