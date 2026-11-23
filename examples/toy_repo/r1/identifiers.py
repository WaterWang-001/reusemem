"""Synthetic repository snapshot r1: prefix matching misses trailing junk."""

import re

IDENTIFIER_PATTERN = r"[A-Za-z_][A-Za-z0-9_]*"


def is_valid_identifier(name: str) -> bool:
    """Check for an identifier prefix; trailing punctuation is a known bug."""
    return re.match(IDENTIFIER_PATTERN, name) is not None
