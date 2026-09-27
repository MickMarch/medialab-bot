"""Presentation helpers for Discord text. Formatting only, no contracts."""

_UNIT_STEP = 1000
"""Decimal units, matching what torrent indexers and qBittorrent's UI display."""
_UNITS = ("B", "KB", "MB", "GB", "TB")
_ONE_DECIMAL_BELOW = 10
"""Values under this many of a unit show one decimal (4.2 GB); above, none (12 GB)."""


def format_size(size_bytes: int) -> str:
    """Render a byte count as a short human-readable size."""
    if size_bytes <= 0:
        return f"0 {_UNITS[0]}"
    value = float(size_bytes)
    unit_index = 0
    while value >= _UNIT_STEP and unit_index < len(_UNITS) - 1:
        value /= _UNIT_STEP
        unit_index += 1
    unit = _UNITS[unit_index]
    if unit_index == 0:
        return f"{int(value)} {unit}"
    if value < _ONE_DECIMAL_BELOW:
        return f"{value:.1f} {unit}"
    return f"{value:.0f} {unit}"


_SECONDS_PER_MINUTE = 60
_SECONDS_PER_HOUR = 60 * _SECONDS_PER_MINUTE
_SECONDS_PER_DAY = 24 * _SECONDS_PER_HOUR
ETA_UNKNOWN = "-"
ETA_UNDER_A_MINUTE = "<1m"

PROGRESS_BAR_WIDTH = 10
PROGRESS_BAR_FILLED = "█"
PROGRESS_BAR_EMPTY = "░"
_PERCENT = 100


def format_eta(seconds: int | None) -> str:
    """``12m`` under an hour, ``3h 05m`` under a day, ``2d 4h`` beyond; ``-`` when unknown."""
    if seconds is None:
        return ETA_UNKNOWN
    if seconds < _SECONDS_PER_MINUTE:
        return ETA_UNDER_A_MINUTE
    if seconds < _SECONDS_PER_HOUR:
        return f"{seconds // _SECONDS_PER_MINUTE}m"
    if seconds < _SECONDS_PER_DAY:
        hours, remainder = divmod(seconds, _SECONDS_PER_HOUR)
        return f"{hours}h {remainder // _SECONDS_PER_MINUTE:02d}m"
    days, remainder = divmod(seconds, _SECONDS_PER_DAY)
    return f"{days}d {remainder // _SECONDS_PER_HOUR}h"


def progress_bar(fraction: float) -> str:
    """Fixed-width block bar; partial cells round down so a bar is full only when done."""
    clamped = min(max(fraction, 0.0), 1.0)
    filled = int(clamped * PROGRESS_BAR_WIDTH)
    return PROGRESS_BAR_FILLED * filled + PROGRESS_BAR_EMPTY * (PROGRESS_BAR_WIDTH - filled)


def format_progress(fraction: float, eta_seconds: int | None) -> str:
    """``bar 42% - ETA 12m`` with the bar in a code span so it renders monospaced."""
    percent = int(min(max(fraction, 0.0), 1.0) * _PERCENT)
    return f"`{progress_bar(fraction)}` {percent}% - ETA {format_eta(eta_seconds)}"
