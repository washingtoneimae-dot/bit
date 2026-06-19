"""Test fixtures for the Bit Protocol."""

from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def sample_txt() -> Path:
    """Path to sample text file."""
    return FIXTURES / "sample.txt"
