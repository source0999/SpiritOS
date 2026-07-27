def parse_ttl(value: object) -> int:
    """Parse a TTL. JQ-S02 supplies the stricter public contract."""
    if isinstance(value, str) and value.endswith("s"):
        return int(value[:-1])
    return int(value)
