def validate_repo_path(value: str) -> str:
    """Return a repository path. JQ-S03 hardens this intentionally permissive stub."""
    return value.replace("\\", "/")
