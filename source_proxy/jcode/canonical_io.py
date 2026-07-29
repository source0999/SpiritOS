"""Deterministic canonical JSON serialization and hashing for Gate 2-J.9.

Reuses the exact canonical-JSON rule already proven in
``source_proxy/jcode/preparation._canonical_json`` so sealed envelopes and
receipts hash identically everywhere. This module is pure and side-effect-free;
it performs no I/O and grants no execution authority.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Serialize ``value`` to deterministic canonical JSON.

    Rule (matches ``preparation._canonical_json``):
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def canonical_bytes(value: Any) -> bytes:
    """Canonical JSON encoded as UTF-8, with a trailing newline (sealed rule)."""
    return (canonical_json(value) + "\n").encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_value(value: Any) -> str:
    """SHA-256 over the canonical-JSON-with-trailing-newline encoding of ``value``."""
    return sha256_bytes(canonical_bytes(value))


def section_hash(name: str, payload: Any) -> str:
    """Hash a named envelope section deterministically.

    The hash covers ``{"section": name, "payload": payload}`` in canonical form
    so a section's identity is bound to both its name and its contents.
    """
    return hash_value({"section": name, "payload": payload})


def root_envelope_hash(section_hashes: dict[str, str]) -> str:
    """Compute the root envelope hash over an ordered map of section hashes.

    Section order is the sorted key order (deterministic). The root hash binds the
    whole envelope; tampering with any section changes the root hash.
    """
    if not isinstance(section_hashes, dict) or not section_hashes:
        raise ValueError("root_envelope_hash_requires_non_empty_section_map")
    ordered = {key: section_hashes[key] for key in sorted(section_hashes)}
    return hash_value({"root": ordered})


def canonical_roundtrip_stable(value: Any) -> bool:
    """True iff serializing then parsing reproduces an identical canonical form.

    Used by the determinism tests: any value whose canonical form is not stable
    under round-trip is rejected.
    """
    encoded = canonical_json(value)
    try:
        parsed = json.loads(encoded)
    except json.JSONDecodeError:
        return False
    return canonical_json(parsed) == encoded
