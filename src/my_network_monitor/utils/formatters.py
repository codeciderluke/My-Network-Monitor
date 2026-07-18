"""Display-oriented unit and string formatting utilities."""

from __future__ import annotations

_RATE_UNITS = ("B/s", "KB/s", "MB/s", "GB/s", "TB/s")
_SIZE_UNITS = ("B", "KB", "MB", "GB", "TB")


def format_rate(bytes_per_second: float) -> str:
    """Convert bytes per second into a human-readable rate."""
    return _humanize(bytes_per_second, _RATE_UNITS)


def format_size(num_bytes: float) -> str:
    """Convert a byte count into a human-readable size."""
    return _humanize(num_bytes, _SIZE_UNITS)


def _humanize(value: float, units: tuple[str, ...]) -> str:
    value = max(value, 0.0)
    unit_index = 0
    while value >= 1024.0 and unit_index < len(units) - 1:
        value /= 1024.0
        unit_index += 1
    if unit_index == 0:
        return f"{int(value)} {units[unit_index]}"
    return f"{value:.1f} {units[unit_index]}"


def format_port(port: int | None) -> str:
    """Convert a port to a string; empty string if None."""
    return "" if port is None else str(port)
