"""Synthetic repository snapshot r1: zero is mistaken for a missing timeout."""

DEFAULT_TIMEOUT = 30


def parse_timeout(raw_value: str) -> int | None:
    """Return a nonnegative integer or None for an invalid value."""
    try:
        value = int(raw_value.strip())
    except ValueError:
        return None
    return value if value >= 0 else None


def resolve_timeout(raw_value: str) -> int:
    """Resolve a timeout using the original, intentionally buggy fallback."""
    return parse_timeout(raw_value) or DEFAULT_TIMEOUT
