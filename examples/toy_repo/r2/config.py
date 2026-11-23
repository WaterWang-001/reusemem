"""Synthetic repository snapshot r2: explicit None checking preserves zero."""

DEFAULT_TIMEOUT = 30


def parse_timeout(raw_value: str) -> int | None:
    """Return a nonnegative integer or None for an invalid value."""
    try:
        value = int(raw_value.strip())
    except ValueError:
        return None
    return value if value >= 0 else None


def resolve_timeout(raw_value: str) -> int:
    """Use the default only when parsing returns None."""
    value = parse_timeout(raw_value)
    return DEFAULT_TIMEOUT if value is None else value
