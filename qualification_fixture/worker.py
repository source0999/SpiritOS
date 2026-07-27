def emit_event(kind: str, payload: dict[str, object]) -> dict[str, object]:
    return {"kind": kind, "payload": dict(payload)}
