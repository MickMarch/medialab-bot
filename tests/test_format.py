"""Human-readable byte sizes for Discord option descriptions."""

import pytest

from medialab_bot.format import format_size


@pytest.mark.parametrize(
    ("size_bytes", "expected"),
    [
        (0, "0 B"),
        (-5, "0 B"),
        (999, "999 B"),
        (1_000, "1.0 KB"),
        (9_900_000, "9.9 MB"),
        (10_000_000, "10 MB"),
        (847_000_000, "847 MB"),
        (1_000_000_000, "1.0 GB"),
        (4_200_000_000, "4.2 GB"),
        (12_000_000_000, "12 GB"),
        (1_000_000_000_000, "1.0 TB"),
        (2_500_000_000_000_000, "2500 TB"),
    ],
)
def test_format_size(size_bytes: int, expected: str) -> None:
    assert format_size(size_bytes) == expected
