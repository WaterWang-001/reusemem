"""Synthetic repository snapshot r2: a reusable batch helper was added."""


def process_item(value: int) -> int:
    """Double an integer, including zero and negative values."""
    return value * 2


def batch_process(values: list[int]) -> list[int]:
    """Process every value in order without dropping falsy values."""
    return [process_item(value) for value in values]
