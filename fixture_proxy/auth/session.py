def require_authenticated(actor: str | None) -> str:
    if not actor:
        raise PermissionError("authentication required")
    return actor
