DEFAULTS = {"log_level": "info", "api_url": "http://localhost"}


def current_config() -> dict[str, str]:
    return dict(DEFAULTS)
