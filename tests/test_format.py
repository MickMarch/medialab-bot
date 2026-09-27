"""Human-readable byte sizes for Discord option descriptions."""

import pytest

from medialab_bot.format import (
    PROGRESS_BAR_EMPTY,
    PROGRESS_BAR_FILLED,
    PROGRESS_BAR_WIDTH,
    format_eta,
    format_size,
    progress_bar,
)


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


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (None, "-"),
        (0, "<1m"),
        (59, "<1m"),
        (60, "1m"),
        (12 * 60 + 30, "12m"),
        (3599, "59m"),
        (3600, "1h 00m"),
        (3 * 3600 + 5 * 60, "3h 05m"),
        (86_399, "23h 59m"),
        (86_400, "1d 0h"),
        (2 * 86_400 + 4 * 3600 + 59 * 60, "2d 4h"),
    ],
)
def test_format_eta(seconds: int | None, expected: str) -> None:
    assert format_eta(seconds) == expected


@pytest.mark.parametrize(
    ("fraction", "filled"),
    [(0.0, 0), (0.5, PROGRESS_BAR_WIDTH // 2), (1.0, PROGRESS_BAR_WIDTH)],
)
def test_progress_bar_is_fixed_width_and_fills_proportionally(fraction: float, filled: int) -> None:
    bar = progress_bar(fraction)
    assert len(bar) == PROGRESS_BAR_WIDTH
    assert bar == PROGRESS_BAR_FILLED * filled + PROGRESS_BAR_EMPTY * (PROGRESS_BAR_WIDTH - filled)
