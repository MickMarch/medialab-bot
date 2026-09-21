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
