def parse_frames(raw: bytes) -> list[bytes]:
    """JQ-T01 repairs this splitter for partial and concatenated frames."""
    return raw.split(b"\n\n")
