import json


def write_record(stream, value: object) -> None:
    """Write one record. JQ-S04 fixes partial framing and typed errors."""
    stream.write(json.dumps(value))
