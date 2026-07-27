try:
    import optional_fast_parser
except ImportError:
    optional_fast_parser = None


def parse(value: str) -> dict[str, str]:
    if optional_fast_parser is None:
        raise RuntimeError("optional parser unavailable")
    return optional_fast_parser.parse(value)
