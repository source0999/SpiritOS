"""Private seed derivation for reproducible, non-leaking benchmark fixtures."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass


class Campaign35SeedError(ValueError):
    pass


@dataclass(frozen=True)
class Campaign35RunSeed:
    """Private raw seed plus a public audit commitment.

    Callers must keep `raw` in the private store.  It is intentionally not
    serializable by this module.
    """

    raw: bytes
    commitment: str


def generate_run_seed() -> Campaign35RunSeed:
    raw = secrets.token_bytes(32)
    return Campaign35RunSeed(raw=raw, commitment=hashlib.sha256(raw).hexdigest())


def derive_task_seed(seed: Campaign35RunSeed, task_id: str, fixture_id: str) -> str:
    if not task_id or not fixture_id:
        raise Campaign35SeedError("campaign_3_5_seed_scope_invalid")
    context = f"campaign-3.5/v1.1/{task_id}/{fixture_id}".encode("utf-8")
    return hmac.new(seed.raw, context, hashlib.sha256).hexdigest()


def task_seed_commitment(task_seed: str) -> str:
    if len(task_seed) != 64 or any(character not in "0123456789abcdef" for character in task_seed):
        raise Campaign35SeedError("campaign_3_5_task_seed_invalid")
    return hashlib.sha256(task_seed.encode("ascii")).hexdigest()
