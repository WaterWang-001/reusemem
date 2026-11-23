"""Synthetic repository snapshot r1: only single-item processing exists."""


def process_item(value: int) -> int:
    """Double an integer, including zero and negative values."""
    return value * 2
