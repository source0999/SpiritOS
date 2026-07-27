import re


def slugify(value: str) -> str:
    """Return a simple slug; task JQ-S01 intentionally exposes edge cases."""
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
