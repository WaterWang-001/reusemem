"""Synthetic repository snapshot r2: the complete identifier is validated."""

import re

IDENTIFIER_PATTERN = r"[A-Za-z_][A-Za-z0-9_]*"


def is_valid_identifier(name: str) -> bool:
    """Accept only complete identifiers; empty strings remain invalid."""
    return re.fullmatch(IDENTIFIER_PATTERN, name) is not None
