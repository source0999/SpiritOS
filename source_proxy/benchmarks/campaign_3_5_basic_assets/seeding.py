"""Private, domain-separated seed derivation for Basic Backend 10 fixtures."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Any, Mapping


SEED_DOMAIN = "source-proxy-basic-backend-10/v1"


class BasicBackendSeedError(ValueError):
    pass


@dataclass(frozen=True)
class BasicBackendRunSeed:
    raw: bytes
    commitment: str

    @classmethod
    def generate(cls) -> "BasicBackendRunSeed":
        raw = secrets.token_bytes(32)
        return cls(raw=raw, commitment=hashlib.sha256(raw).hexdigest())

    @classmethod
    def from_private_bytes(cls, raw: bytes) -> "BasicBackendRunSeed":
        if len(raw) != 32:
            raise BasicBackendSeedError("basic_backend_run_seed_invalid")
        return cls(raw=bytes(raw), commitment=hashlib.sha256(raw).hexdigest())


def derive_task_digest(seed: BasicBackendRunSeed, *, run_nonce: str, task_id: str) -> str:
    if len(seed.raw) != 32 or not run_nonce or not task_id:
        raise BasicBackendSeedError("basic_backend_task_seed_scope_invalid")
    context = f"{SEED_DOMAIN}\0{run_nonce}\0{task_id}".encode("utf-8")
    return hmac.new(seed.raw, context, hashlib.sha256).hexdigest()


def task_seed_commitment(task_digest: str) -> str:
    _digest_bytes(task_digest)
    return hashlib.sha256(task_digest.encode("ascii")).hexdigest()


def render_randomized_fields(
    task_digest: str,
    definitions: list[Mapping[str, Any]],
) -> dict[str, str | int]:
    task_key = _digest_bytes(task_digest)
    rendered: dict[str, str | int] = {}
    for definition in definitions:
        name = str(definition.get("name") or "")
        kind = str(definition.get("kind") or "")
        if not name or name in rendered:
            raise BasicBackendSeedError("basic_backend_field_definition_invalid")
        context = f"{SEED_DOMAIN}/field\0{task_digest}\0{name}".encode("utf-8")
        field_digest = hmac.new(task_key, context, hashlib.sha256).digest()
        number = int.from_bytes(field_digest, "big")
        if kind == "identifier":
            prefix = str(definition.get("prefix") or "")
            if not prefix or not prefix.replace("_", "a").isalnum():
                raise BasicBackendSeedError("basic_backend_field_definition_invalid")
            rendered[name] = prefix + field_digest.hex()[:8]
        elif kind in {"integer", "port"}:
            if kind == "port":
                minimum, maximum = 20_000, 49_999
            else:
                try:
                    minimum = int(definition["minimum"])
                    maximum = int(definition["maximum"])
                except (KeyError, TypeError, ValueError) as error:
                    raise BasicBackendSeedError("basic_backend_field_definition_invalid") from error
            if minimum > maximum:
                raise BasicBackendSeedError("basic_backend_field_definition_invalid")
            rendered[name] = minimum + number % (maximum - minimum + 1)
        else:
            raise BasicBackendSeedError("basic_backend_field_kind_unsupported")
    return rendered


def _digest_bytes(value: str) -> bytes:
    if len(value) != 64 or value != value.lower() or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise BasicBackendSeedError("basic_backend_task_digest_invalid")
    return bytes.fromhex(value)
